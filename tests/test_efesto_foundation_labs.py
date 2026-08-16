from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import efesto_headless, efesto_ui_server, student_virtual_lab
from scripts.thebitlab_virtual_lab_contracts import (
    normalize_virtual_lab_extension,
    validate_virtual_lab_extension,
)
from scripts.thebitlab_virtual_lab_scaffold import starter_content_for_activity


ROOT = Path(__file__).resolve().parents[1]


LABS = [
    {
        "activity": "activities/examples/hardware_component_placement.json",
        "activity_id": "hw-component-placement-001",
        "scenario_id": "component-placement-001",
        "starter_score": 5.0,
        "corrected": [
            {"slot": "cpu_socket", "component_id": "cpu-basic-001"},
            {"slot": "dimm_a2", "component_id": "ram-ddr5-001"},
            {"slot": "pcie1", "component_id": "gpu-basic-001"},
            {"slot": "m2_1", "component_id": "nvme-basic-001"},
            {"slot": "sata1", "component_id": "sata-ssd-basic-001"},
        ],
    },
    {
        "activity": "activities/examples/hardware_cpu_socket_matching.json",
        "activity_id": "hw-cpu-socket-matching-001",
        "scenario_id": "cpu-socket-matching-001",
        "starter_score": 0.0,
        "corrected": [
            {"slot": "socket_am5", "component_id": "cpu-ryzen-am5-001"},
            {"slot": "socket_lga1700", "component_id": "cpu-core-lga1700-001"},
        ],
    },
    {
        "activity": "activities/examples/hardware_ddr5_dual_channel.json",
        "activity_id": "hw-ddr5-dual-channel-001",
        "scenario_id": "ddr5-dual-channel-001",
        "starter_score": 3.33,
        "corrected": [
            {"slot": "dimm_a2", "component_id": "ddr5-module-a-001"},
            {"slot": "dimm_b2", "component_id": "ddr5-module-b-001"},
        ],
    },
    {
        "activity": "activities/examples/hardware_psu_selection.json",
        "activity_id": "hw-psu-selection-001",
        "scenario_id": "psu-selection-001",
        "starter_score": 6.67,
        "corrected": [
            {"slot": "pcie1", "component_id": "gpu-350w-001"},
            {"slot": "psu_bay", "component_id": "psu-850-gold-001"},
        ],
    },
]


@pytest.mark.parametrize("lab", LABS, ids=[item["scenario_id"] for item in LABS])
def test_foundation_activity_and_starter_contract(lab: dict) -> None:
    activity_path = ROOT / lab["activity"]
    activity = json.loads(activity_path.read_text(encoding="utf-8"))

    assert activity["id"] == lab["activity_id"]
    assert activity["language"] == "virtual-lab"
    assert activity["source_name"] == "build.json"
    assert validate_virtual_lab_extension(activity, str(activity_path)) == []

    extension = normalize_virtual_lab_extension(activity)
    assert extension is not None
    assert extension["runtime"] == "efesto"
    assert extension["scenario_id"] == lab["scenario_id"]
    assert extension["submission"]["path"] == "build.json"
    assert set(extension["capabilities"]) == {
        "interactive-ui",
        "deterministic-grade",
        "headless-run",
    }

    provider_extension, starter_text = starter_content_for_activity(
        activity,
        project_root=ROOT,
    )
    starter = json.loads(starter_text)
    assert provider_extension == extension
    assert starter["schema_version"] == "efesto.build.v1"
    assert starter["scenario_id"] == lab["scenario_id"]


@pytest.mark.parametrize("lab", LABS, ids=[item["scenario_id"] for item in LABS])
def test_foundation_starter_fails_and_corrected_build_passes(lab: dict) -> None:
    scenario = efesto_headless.load_scenario(ROOT, lab["scenario_id"])
    starter = json.loads(
        (ROOT / "virtual-labs/efesto/starters" / f"{lab['scenario_id']}.json").read_text(
            encoding="utf-8"
        )
    )

    initial = efesto_headless.grade_build(
        scenario,
        starter,
        activity_id=lab["activity_id"],
    )
    corrected = {
        "schema_version": "efesto.build.v1",
        "scenario_id": lab["scenario_id"],
        "components": lab["corrected"],
    }
    final = efesto_headless.grade_build(
        scenario,
        corrected,
        activity_id=lab["activity_id"],
    )

    assert initial["passed"] is False
    assert initial["score"] == lab["starter_score"]
    assert any(test["passed"] is False for test in initial["tests"])
    assert final["passed"] is True
    assert final["score"] == 10.0
    assert final["summary"]["passed"] == final["summary"]["total"]


@pytest.mark.parametrize("lab", LABS, ids=[item["scenario_id"] for item in LABS])
def test_foundation_lab_uses_same_generic_2d_ui(tmp_path: Path, lab: dict) -> None:
    activity_path = ROOT / lab["activity"]
    student_repo = tmp_path / lab["activity_id"]
    workspace = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=ROOT,
    )

    session = efesto_ui_server.EfestoUiSession.load(
        project_root=ROOT,
        activity_path=activity_path,
        workspace_path=workspace,
    )
    state = session.state()

    assert state["activity"]["id"] == lab["activity_id"]
    assert state["activity"]["scenario_id"] == lab["scenario_id"]
    assert state["build"]["scenario_id"] == lab["scenario_id"]
    assert state["grading"]["passed"] is False
    assert state["grading"]["score"] == lab["starter_score"]
    assert state["scenario"]["slots"]
    assert state["scenario"]["components"]
