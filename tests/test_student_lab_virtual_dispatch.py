from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts import student_lab_runner, student_lab_service, student_virtual_lab


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_SOURCE = SOURCE_ROOT / "activities/examples/hardware_pcie_lane_sharing.json"
SCENARIO_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/scenarios/pcie-lane-sharing-001.json"
STARTER_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/starters/pcie-lane-sharing-001.json"
ACTIVITY_ID = "hw-pcie-lane-sharing-001"
SCENARIO_ID = "pcie-lane-sharing-001"


def prepare_root(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
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

    student_repo = root / "students/rossi-mario"
    workspace = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
    )
    assignment = {
        "assignment_id": "assignment-hw-pcie-001",
        "activity_id": ACTIVITY_ID,
        "student_id": "rossi-mario",
        "activity": {"path": "activities/hardware.json"},
        "workspace": {"path": workspace.relative_to(root).as_posix()},
    }
    return root, activity_path, workspace, assignment


def test_activity_summary_exposes_virtual_lab_artifact(tmp_path: Path) -> None:
    root, _, _, _ = prepare_root(tmp_path)

    summary = student_lab_service.load_activity_summary(root, "activities/hardware.json")

    assert summary["language"] == "virtual-lab"
    assert summary["source_name"] == "build.json"


def test_generic_runner_dispatches_virtual_lab_without_docker(tmp_path: Path) -> None:
    root, _, workspace, assignment = prepare_root(tmp_path)

    report = student_lab_runner.run_assignment(
        assignment,
        root=root,
        backend="docker",
    )

    assert report["backend"] == "virtual-lab"
    assert report["language"] == "virtual-lab"
    assert report["runtime"] == "efesto"
    assert report["scenario_id"] == SCENARIO_ID
    assert report["source"] == str(workspace / "build.json")
    assert report["passed"] is False
    assert report["score"] == 8.0
    assert report["summary"] == {"passed": 4, "total": 5}


def test_generic_runner_can_persist_corrected_virtual_lab_attempt(tmp_path: Path) -> None:
    root, _, workspace, assignment = prepare_root(tmp_path)
    build_path = workspace / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    for placement in build["components"]:
        if placement["component_id"] == "nvme-2tb-001":
            placement["slot"] = "m2_1"
    build_path.write_text(
        json.dumps(build, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = student_lab_runner.run_assignment(assignment, root=root)
    report_path = student_lab_runner.write_student_report(root, assignment, report)

    assert report["passed"] is True
    assert report["score"] == 10.0
    assert report["attempt_id"].startswith("attempt-")
    stored = json.loads(report_path.read_text(encoding="utf-8"))
    assert stored["backend"] == "virtual-lab"
    assert stored["source"] == f"assignments/{ACTIVITY_ID}/build.json"
    assert stored["passed"] is True
