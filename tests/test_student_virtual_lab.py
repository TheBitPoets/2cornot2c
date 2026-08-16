from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import student_virtual_lab
from scripts.thebitlab_virtual_lab_scaffold import (
    EfestoStarterProvider,
    starter_content_for_activity,
)


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_SOURCE = SOURCE_ROOT / "activities/examples/hardware_pcie_lane_sharing.json"
SCENARIO_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/scenarios/pcie-lane-sharing-001.json"
STARTER_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/starters/pcie-lane-sharing-001.json"
ACTIVITY_ID = "hw-pcie-lane-sharing-001"
SCENARIO_ID = "pcie-lane-sharing-001"


def prepare_root(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "thebitlab"
    activity_path = root / "activities/hardware.json"
    scenario_path = root / "virtual-labs/efesto/scenarios" / f"{SCENARIO_ID}.json"
    starter_path = root / "virtual-labs/efesto/starters" / f"{SCENARIO_ID}.json"
    activity_path.parent.mkdir(parents=True)
    scenario_path.parent.mkdir(parents=True)
    starter_path.parent.mkdir(parents=True)
    shutil.copyfile(ACTIVITY_SOURCE, activity_path)
    shutil.copyfile(SCENARIO_SOURCE, scenario_path)
    shutil.copyfile(STARTER_SOURCE, starter_path)
    return root, activity_path


def assignment_for(root: Path, workspace: Path) -> dict:
    return {
        "assignment_id": "assignment-hw-pcie-001",
        "activity_id": ACTIVITY_ID,
        "student_id": "rossi-mario",
        "activity": {"path": "activities/hardware.json"},
        "workspace": {"path": workspace.relative_to(root).as_posix()},
    }


def test_efesto_starter_provider_returns_valid_json(tmp_path) -> None:
    root, activity_path = prepare_root(tmp_path)
    activity = json.loads(activity_path.read_text(encoding="utf-8"))

    extension, content = starter_content_for_activity(activity, project_root=root)
    starter = json.loads(content)

    assert extension["runtime"] == "efesto"
    assert starter["schema_version"] == "efesto.build.v1"
    assert starter["scenario_id"] == SCENARIO_ID
    assert {item["slot"] for item in starter["components"]} == {"pcie1", "pcie2", "m2_2"}


def test_starter_provider_rejects_missing_scenario(tmp_path) -> None:
    provider = EfestoStarterProvider(project_root=tmp_path)

    with pytest.raises(ValueError, match="Starter Efesto"):
        provider.starter_content("missing-scenario")


def test_scaffold_creates_virtual_submission_without_fake_source_file(tmp_path) -> None:
    root, activity_path = prepare_root(tmp_path)
    student_repo = root / "students/rossi-mario"

    destination = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
    )

    assert destination == student_repo / "assignments" / ACTIVITY_ID
    assert (destination / "build.json").is_file()
    assert not (destination / "main.c").exists()
    snapshot = json.loads((destination / "activity.json").read_text(encoding="utf-8"))
    extension = snapshot["extensions"]["thebitlab.virtual_lab"]
    assert snapshot["language"] == "virtual-lab"
    assert snapshot["source_name"] == "build.json"
    assert extension["runtime"] == "efesto"
    assert extension["scenario_id"] == SCENARIO_ID
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "Runtime virtuale: `efesto`" in readme
    assert "`build.json`" in readme


def test_force_scaffold_preserves_student_build(tmp_path) -> None:
    root, activity_path = prepare_root(tmp_path)
    student_repo = root / "students/rossi-mario"
    destination = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
    )
    build_path = destination / "build.json"
    student_build = {
        "schema_version": "efesto.build.v1",
        "scenario_id": SCENARIO_ID,
        "components": [{"slot": "m2_1", "component_id": "nvme-2tb-001"}],
    }
    build_path.write_text(json.dumps(student_build), encoding="utf-8")

    student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
        overwrite=True,
    )

    assert json.loads(build_path.read_text(encoding="utf-8")) == student_build


def test_end_to_end_attempt_history_keeps_failure_then_final_success(tmp_path) -> None:
    root, activity_path = prepare_root(tmp_path)
    student_repo = root / "students/rossi-mario"
    workspace = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
    )
    assignment = assignment_for(root, workspace)

    first_report = student_virtual_lab.run_virtual_lab_assignment(
        assignment,
        root=root,
    )
    first_path = student_virtual_lab.persist_virtual_lab_attempt(
        assignment,
        first_report,
        root=root,
    )

    assert first_report["passed"] is False
    assert first_report["score"] == 8.0
    assert first_report["attempt_id"]
    first_attempt_id = first_report["attempt_id"]
    assert first_path == student_repo / "reports" / ACTIVITY_ID / "latest.json"

    build_path = workspace / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    for item in build["components"]:
        if item["component_id"] == "nvme-2tb-001":
            item["slot"] = "m2_1"
    build_path.write_text(json.dumps(build, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    second_report = student_virtual_lab.run_virtual_lab_assignment(
        assignment,
        root=root,
    )
    second_path = student_virtual_lab.persist_virtual_lab_attempt(
        assignment,
        second_report,
        root=root,
        final=True,
    )

    assert second_path == first_path
    assert second_report["passed"] is True
    assert second_report["score"] == 10.0
    assert second_report["attempt_id"]
    assert second_report["attempt_id"] != first_attempt_id

    assignment_history = (
        student_repo
        / "reports"
        / ACTIVITY_ID
        / "assignments"
        / assignment["assignment_id"]
    )
    attempts = sorted((assignment_history / "attempts").glob("attempt-*.json"))
    assert len(attempts) == 2
    final_payload = json.loads((assignment_history / "final.json").read_text(encoding="utf-8"))
    assert final_payload["attempt_id"] == second_report["attempt_id"]


def test_scaffold_rejects_symlink_submission_on_refresh(tmp_path) -> None:
    root, activity_path = prepare_root(tmp_path)
    student_repo = root / "students/rossi-mario"
    destination = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
    )
    build_path = destination / "build.json"
    target = destination / "student-build-target.json"
    build_path.replace(target)
    try:
        build_path.symlink_to(target.name)
    except OSError:
        pytest.skip("Symlink non disponibile su questa piattaforma")

    with pytest.raises(ValueError, match="link simbolico"):
        student_virtual_lab.create_virtual_lab_scaffold(
            activity_path=activity_path,
            target_dir=student_repo,
            project_root=root,
            overwrite=True,
        )
