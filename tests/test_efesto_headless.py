from __future__ import annotations

import json
from pathlib import Path

from scripts import efesto_contracts, efesto_headless


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ID = "pcie-lane-sharing-001"


def valid_build(*, nvme_slot: str = "m2_1") -> dict:
    return {
        "schema_version": efesto_contracts.EFESTO_BUILD_SCHEMA_VERSION,
        "scenario_id": SCENARIO_ID,
        "components": [
            {"slot": "pcie1", "component_id": "gpu-3090-001"},
            {"slot": nvme_slot, "component_id": "nvme-2tb-001"},
            {"slot": "pcie2", "component_id": "nic-10gbe-001"},
        ],
    }


def test_scenario_catalog_entry_is_valid() -> None:
    scenario = efesto_headless.load_scenario(PROJECT_ROOT, SCENARIO_ID)

    assert scenario["schema_version"] == "efesto.scenario.v1"
    assert scenario["id"] == SCENARIO_ID
    assert efesto_contracts.validate_scenario(scenario) == []


def test_build_contract_rejects_duplicate_slots() -> None:
    build = valid_build()
    build["components"].append(
        {"slot": "pcie1", "component_id": "nic-10gbe-001"}
    )

    errors = efesto_contracts.validate_build(build, "build.json")

    assert "build.json: slot duplicato nella build: pcie1" in errors


def test_headless_grade_passes_when_nvme_avoids_shared_slot() -> None:
    scenario = efesto_headless.load_scenario(PROJECT_ROOT, SCENARIO_ID)

    report = efesto_headless.grade_build(
        scenario,
        valid_build(nvme_slot="m2_1"),
        activity_id="hw-pcie-lane-sharing-001",
    )

    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["summary"] == {"passed": 5, "total": 5}
    assert report["score"] == 10.0
    assert all(test["passed"] for test in report["tests"])


def test_headless_grade_detects_lane_sharing_conflict() -> None:
    scenario = efesto_headless.load_scenario(PROJECT_ROOT, SCENARIO_ID)

    report = efesto_headless.grade_build(
        scenario,
        valid_build(nvme_slot="m2_2"),
        activity_id="hw-pcie-lane-sharing-001",
    )

    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["summary"] == {"passed": 4, "total": 5}
    assert report["score"] == 8.0
    lane_test = next(
        test for test in report["tests"] if test["name"] == "Nessun conflitto tra M2_2 e PCIe2"
    )
    assert lane_test["passed"] is False
    assert "occupati contemporaneamente" in lane_test["message"]


def test_headless_grade_rejects_wrong_scenario_id() -> None:
    scenario = efesto_headless.load_scenario(PROJECT_ROOT, SCENARIO_ID)
    build = valid_build()
    build["scenario_id"] = "different-scenario"

    report = efesto_headless.grade_build(scenario, build)

    assert report["passed"] is False
    assert report["summary"] == {"passed": 0, "total": 1}
    assert report["tests"][0]["name"] == "Scenario della build corretto"


def test_grade_submission_treats_invalid_json_as_student_failure(tmp_path) -> None:
    build_path = tmp_path / "build.json"
    build_path.write_text("{not-json", encoding="utf-8")

    report = efesto_headless.grade_submission(
        project_root=PROJECT_ROOT,
        scenario_id=SCENARIO_ID,
        submission_path=build_path,
        activity_id="hw-pcie-lane-sharing-001",
    )

    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["tests"][0]["visibility"] == "student"


def test_runtime_adapter_returns_common_execution_result(tmp_path) -> None:
    build_path = tmp_path / "build.json"
    build_path.write_text(json.dumps(valid_build()), encoding="utf-8")
    adapter = efesto_headless.EfestoRuntimeAdapter(project_root=PROJECT_ROOT)

    result = adapter.run(
        scenario_id=SCENARIO_ID,
        submission_path=build_path,
        activity_id="hw-pcie-lane-sharing-001",
    )

    assert result.status == "passed"
    assert len(result.tests) == 5
    assert result.metadata["runtime"] == "efesto"
    assert result.metadata["runner_report"]["score"] == 10.0
