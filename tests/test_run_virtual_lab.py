from __future__ import annotations

import json
from pathlib import Path

from scripts import run_virtual_lab


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = PROJECT_ROOT / "activities/examples/hardware_pcie_lane_sharing.json"


def build(*, nvme_slot: str) -> dict:
    return {
        "schema_version": "efesto.build.v1",
        "scenario_id": "pcie-lane-sharing-001",
        "components": [
            {"slot": "pcie1", "component_id": "gpu-3090-001"},
            {"slot": nvme_slot, "component_id": "nvme-2tb-001"},
            {"slot": "pcie2", "component_id": "nic-10gbe-001"},
        ],
    }


def test_headless_cli_function_returns_normal_report(tmp_path) -> None:
    submission = tmp_path / "build.json"
    submission.write_text(json.dumps(build(nvme_slot="m2_1")), encoding="utf-8")

    report = run_virtual_lab.run_virtual_lab(
        activity_path=ACTIVITY,
        submission_path=submission,
        project_root=PROJECT_ROOT,
    )

    assert report["activity_id"] == "hw-pcie-lane-sharing-001"
    assert report["runtime"] == "efesto"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["summary"] == {"passed": 5, "total": 5}
    assert report["score"] == 10.0


def test_headless_cli_function_reports_lane_conflict(tmp_path) -> None:
    submission = tmp_path / "build.json"
    submission.write_text(json.dumps(build(nvme_slot="m2_2")), encoding="utf-8")

    report = run_virtual_lab.run_virtual_lab(
        activity_path=ACTIVITY,
        submission_path=submission,
        project_root=PROJECT_ROOT,
    )

    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["summary"] == {"passed": 4, "total": 5}


def test_main_writes_report_and_returns_zero_for_passing_build(tmp_path, monkeypatch) -> None:
    submission = tmp_path / "build.json"
    output = tmp_path / "report.json"
    submission.write_text(json.dumps(build(nvme_slot="m2_1")), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_virtual_lab.py",
            "--activity",
            str(ACTIVITY),
            "--submission",
            str(submission),
            "--report",
            str(output),
            "--project-root",
            str(PROJECT_ROOT),
        ],
    )

    exit_code = run_virtual_lab.main()

    assert exit_code == 0
    stored = json.loads(output.read_text(encoding="utf-8"))
    assert stored["passed"] is True
