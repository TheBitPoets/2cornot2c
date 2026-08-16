from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import efesto_headless, efesto_ui_server, student_virtual_lab
from scripts.thebitlab_virtual_lab_contracts import normalize_virtual_lab_extension


ROOT = Path(__file__).resolve().parents[1]


DESIGN_LABS = [
    {
        "activity": "activities/examples/hardware_ai_gpu_vram.json",
        "activity_id": "hw-ai-gpu-vram-001",
        "scenario_id": "ai-gpu-vram-001",
        "starter_score": 5.0,
        "solutions": [
            [{"slot": "pcie1", "component_id": "gpu-ai-24gb"}],
            [{"slot": "pcie1", "component_id": "gpu-ai-48gb"}],
        ],
    },
    {
        "activity": "activities/examples/hardware_ram_upgrade_headroom.json",
        "activity_id": "hw-ram-upgrade-headroom-001",
        "scenario_id": "ram-upgrade-headroom-001",
        "starter_score": 6.67,
        "solutions": [
            [
                {"slot": "dimm_a2", "component_id": "ram32-a"},
                {"slot": "dimm_b2", "component_id": "ram32-b"},
            ]
        ],
    },
    {
        "activity": "activities/examples/hardware_storage_tiering.json",
        "activity_id": "hw-storage-tiering-001",
        "scenario_id": "storage-tiering-001",
        "starter_score": 3.33,
        "solutions": [
            [
                {"slot": "m2_system", "component_id": "nvme-1024"},
                {"slot": "sata_archive", "component_id": "sata-2048"},
            ],
            [
                {"slot": "m2_system", "component_id": "nvme-2048"},
                {"slot": "sata_archive", "component_id": "sata-4096"},
            ],
        ],
    },
    {
        "activity": "activities/examples/hardware_psu_headroom_design.json",
        "activity_id": "hw-psu-headroom-design-001",
        "scenario_id": "psu-headroom-design-001",
        "starter_score": 8.0,
        "solutions": [
            [
                {"slot": "cpu_socket", "component_id": "cpu-workstation-120w"},
                {"slot": "pcie1", "component_id": "gpu-workstation-350w"},
                {"slot": "m2_1", "component_id": "nvme-workstation-15w"},
                {"slot": "psu_bay", "component_id": "psu-design-750"},
            ],
            [
                {"slot": "cpu_socket", "component_id": "cpu-workstation-120w"},
                {"slot": "pcie1", "component_id": "gpu-workstation-350w"},
                {"slot": "m2_1", "component_id": "nvme-workstation-15w"},
                {"slot": "psu_bay", "component_id": "psu-design-850"},
            ],
        ],
    },
]


def build_for(scenario_id: str, placements: list[dict]) -> dict:
    return {
        "schema_version": "efesto.build.v1",
        "scenario_id": scenario_id,
        "components": placements,
    }


@pytest.mark.parametrize(
    "lab",
    DESIGN_LABS,
    ids=[item["scenario_id"] for item in DESIGN_LABS],
)
def test_design_lab_starter_fails_and_all_declared_solutions_pass(lab: dict) -> None:
    scenario = efesto_headless.load_scenario(ROOT, lab["scenario_id"])
    starter_path = ROOT / "virtual-labs/efesto/starters" / f"{lab['scenario_id']}.json"
    starter = json.loads(starter_path.read_text(encoding="utf-8"))

    initial = efesto_headless.grade_build(
        scenario,
        starter,
        activity_id=lab["activity_id"],
    )

    assert initial["passed"] is False
    assert initial["score"] == lab["starter_score"]

    for placements in lab["solutions"]:
        report = efesto_headless.grade_build(
            scenario,
            build_for(lab["scenario_id"], placements),
            activity_id=lab["activity_id"],
        )
        assert report["passed"] is True
        assert report["score"] == 10.0


@pytest.mark.parametrize(
    "lab",
    DESIGN_LABS,
    ids=[item["scenario_id"] for item in DESIGN_LABS],
)
def test_design_activity_points_to_quantitative_scenario(lab: dict) -> None:
    activity = json.loads((ROOT / lab["activity"]).read_text(encoding="utf-8"))
    extension = normalize_virtual_lab_extension(activity)

    assert activity["id"] == lab["activity_id"]
    assert activity["language"] == "virtual-lab"
    assert activity["source_name"] == "build.json"
    assert extension is not None
    assert extension["runtime"] == "efesto"
    assert extension["scenario_id"] == lab["scenario_id"]


@pytest.mark.parametrize(
    "lab",
    DESIGN_LABS,
    ids=[item["scenario_id"] for item in DESIGN_LABS],
)
def test_design_lab_loads_in_generic_ui_and_exposes_trusted_attributes(
    tmp_path: Path,
    lab: dict,
) -> None:
    activity_path = ROOT / lab["activity"]
    workspace = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / lab["activity_id"],
        project_root=ROOT,
    )
    session = efesto_ui_server.EfestoUiSession.load(
        project_root=ROOT,
        activity_path=activity_path,
        workspace_path=workspace,
    )

    state = session.state()

    assert state["activity"]["scenario_id"] == lab["scenario_id"]
    assert state["grading"]["score"] == lab["starter_score"]
    assert any(
        isinstance(component.get("attributes"), dict) and component["attributes"]
        for component in state["scenario"]["components"]
    )


def test_psu_lab_cannot_pass_by_removing_the_gpu_to_reduce_demand() -> None:
    scenario = efesto_headless.load_scenario(ROOT, "psu-headroom-design-001")
    cheating_build = build_for(
        "psu-headroom-design-001",
        [
            {"slot": "cpu_socket", "component_id": "cpu-workstation-120w"},
            {"slot": "m2_1", "component_id": "nvme-workstation-15w"},
            {"slot": "psu_bay", "component_id": "psu-design-650"},
        ],
    )

    report = efesto_headless.grade_build(scenario, cheating_build)
    tests = {test["name"]: test for test in report["tests"]}

    assert report["passed"] is False
    assert tests["GPU del brief presente"]["passed"] is False
    assert tests["PSU sufficiente con 80 W fissi e margine del 20 percento"]["passed"] is True


def test_psu_lab_calculates_678_w_required_from_the_brief() -> None:
    scenario = efesto_headless.load_scenario(ROOT, "psu-headroom-design-001")
    starter = json.loads(
        (ROOT / "virtual-labs/efesto/starters/psu-headroom-design-001.json").read_text(
            encoding="utf-8"
        )
    )

    report = efesto_headless.grade_build(scenario, starter)
    capacity = next(
        test
        for test in report["tests"]
        if test["name"] == "PSU sufficiente con 80 W fissi e margine del 20 percento"
    )

    assert capacity["passed"] is False
    assert "richiesti 678 W" in capacity["message"]
