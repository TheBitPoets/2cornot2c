from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts import student_virtual_lab, student_virtual_lab_ui


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_SOURCE = SOURCE_ROOT / "activities/examples/hardware_pcie_lane_sharing.json"
SCENARIO_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/scenarios/pcie-lane-sharing-001.json"
STARTER_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/starters/pcie-lane-sharing-001.json"
ACTIVITY_ID = "hw-pcie-lane-sharing-001"
SCENARIO_ID = "pcie-lane-sharing-001"


def prepare_assignment(tmp_path: Path) -> tuple[Path, dict]:
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
        "activity": {
            "path": "activities/hardware.json",
            "language": "virtual-lab",
            "source_name": "build.json",
        },
        "workspace": {
            "path": workspace.relative_to(root).as_posix(),
            "exists": True,
        },
    }
    return root, assignment


def test_virtual_lab_assignment_detection() -> None:
    assert student_virtual_lab_ui.is_virtual_lab_assignment(
        {"activity": {"language": "virtual-lab"}}
    )
    assert not student_virtual_lab_ui.is_virtual_lab_assignment(
        {"activity": {"language": "python"}}
    )
    assert not student_virtual_lab_ui.is_virtual_lab_assignment({})


def test_session_for_assignment_resolves_thebitlab_paths(tmp_path: Path) -> None:
    root, assignment = prepare_assignment(tmp_path)

    session = student_virtual_lab_ui.session_for_assignment(assignment, root=root)

    assert session.activity["id"] == ACTIVITY_ID
    assert session.extension["runtime"] == "efesto"
    assert session.extension["scenario_id"] == SCENARIO_ID
    assert session.submission_path.name == "build.json"
    assert session.submission_path.parent == (root / assignment["workspace"]["path"]).resolve()


def test_session_for_assignment_rejects_non_virtual_lab(tmp_path: Path) -> None:
    root, assignment = prepare_assignment(tmp_path)
    assignment["activity"]["language"] = "python"

    with pytest.raises(ValueError, match="non e un virtual-lab"):
        student_virtual_lab_ui.session_for_assignment(assignment, root=root)


def test_registry_reuses_server_for_same_assignment_and_closes_it(tmp_path: Path) -> None:
    root, assignment = prepare_assignment(tmp_path)
    registry = student_virtual_lab_ui.StudentVirtualLabUiRegistry()
    opened_urls: list[str] = []

    try:
        first, reused_first, browser_first = registry.open(
            assignment,
            root=root,
            open_browser_fn=lambda url: opened_urls.append(url) or True,
        )
        second, reused_second, browser_second = registry.open(
            assignment,
            root=root,
            open_browser_fn=lambda url: opened_urls.append(url) or True,
        )

        assert reused_first is False
        assert reused_second is True
        assert browser_first is True
        assert browser_second is True
        assert first is second
        assert first.url == second.url
        assert len(registry) == 1
        assert opened_urls == [first.url, first.url]
    finally:
        registry.close_all()

    assert len(registry) == 0
    assert registry._closed is True


def test_registry_keeps_server_when_browser_open_fails(tmp_path: Path) -> None:
    root, assignment = prepare_assignment(tmp_path)
    registry = student_virtual_lab_ui.StudentVirtualLabUiRegistry()

    try:
        running, reused, opened = registry.open(
            assignment,
            root=root,
            open_browser_fn=lambda _url: False,
        )
        assert reused is False
        assert opened is False
        assert running.url.startswith("http://127.0.0.1:")
        assert len(registry) == 1
    finally:
        registry.close_all()
