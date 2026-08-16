from __future__ import annotations

from copy import deepcopy

from scripts import efesto_contracts, efesto_headless


SCENARIO = {
    "schema_version": "efesto.scenario.v1",
    "id": "quantitative-test-001",
    "title": "Scenario quantitativo di test",
    "slots": [
        {"id": "cpu", "kind": "cpu-socket", "label": "CPU"},
        {"id": "gpu", "kind": "pcie", "label": "GPU"},
        {"id": "ram1", "kind": "dimm", "label": "RAM 1"},
        {"id": "ram2", "kind": "dimm", "label": "RAM 2"},
        {"id": "psu", "kind": "psu", "label": "PSU"},
    ],
    "components": [
        {
            "id": "cpu-120w",
            "kind": "cpu",
            "label": "CPU 120 W",
            "allowed_slots": ["cpu"],
            "attributes": {"power_w": 120, "socket_family": "am5"},
        },
        {
            "id": "gpu-12gb",
            "kind": "gpu",
            "label": "GPU 12 GB",
            "allowed_slots": ["gpu"],
            "attributes": {"vram_gb": 12, "power_w": 350},
        },
        {
            "id": "gpu-24gb",
            "kind": "gpu",
            "label": "GPU 24 GB",
            "allowed_slots": ["gpu"],
            "attributes": {"vram_gb": 24, "power_w": 350},
        },
        {
            "id": "ram16-a",
            "kind": "ram",
            "label": "RAM 16 GB A",
            "allowed_slots": ["ram1", "ram2"],
            "attributes": {"capacity_gb": 16},
        },
        {
            "id": "ram16-b",
            "kind": "ram",
            "label": "RAM 16 GB B",
            "allowed_slots": ["ram1", "ram2"],
            "attributes": {"capacity_gb": 16},
        },
        {
            "id": "ram32-a",
            "kind": "ram",
            "label": "RAM 32 GB A",
            "allowed_slots": ["ram1", "ram2"],
            "attributes": {"capacity_gb": 32},
        },
        {
            "id": "ram32-b",
            "kind": "ram",
            "label": "RAM 32 GB B",
            "allowed_slots": ["ram1", "ram2"],
            "attributes": {"capacity_gb": 32},
        },
        {
            "id": "psu650",
            "kind": "psu",
            "label": "PSU 650 W",
            "allowed_slots": ["psu"],
            "attributes": {"capacity_w": 650},
        },
        {
            "id": "psu750",
            "kind": "psu",
            "label": "PSU 750 W",
            "allowed_slots": ["psu"],
            "attributes": {"capacity_w": 750},
        },
    ],
    "checks": [
        {
            "id": "compatible",
            "name": "Posizionamenti compatibili",
            "type": "all-placements-compatible",
            "visibility": "student",
        },
        {
            "id": "gpu-vram",
            "name": "VRAM almeno 24 GB",
            "type": "slot-component-attribute-min",
            "slot": "gpu",
            "attribute": "vram_gb",
            "min_value": 24,
            "unit": "GB",
            "visibility": "student",
        },
        {
            "id": "cpu-power",
            "name": "CPU entro 150 W",
            "type": "slot-component-attribute-max",
            "slot": "cpu",
            "attribute": "power_w",
            "max_value": 150,
            "unit": "W",
            "visibility": "student",
        },
        {
            "id": "cpu-socket",
            "name": "CPU AM5",
            "type": "slot-component-attribute-equals",
            "slot": "cpu",
            "attribute": "socket_family",
            "expected": "am5",
            "visibility": "student",
        },
        {
            "id": "ram-total",
            "name": "RAM totale almeno 64 GB",
            "type": "installed-attribute-sum-min",
            "attribute": "capacity_gb",
            "kind": "ram",
            "min_value": 64,
            "unit": "GB",
            "visibility": "student",
        },
        {
            "id": "power-total",
            "name": "Carico componenti entro 500 W",
            "type": "installed-attribute-sum-max",
            "attribute": "power_w",
            "max_value": 500,
            "unit": "W",
            "visibility": "student",
        },
        {
            "id": "ram-count",
            "name": "Esattamente due moduli RAM",
            "type": "installed-kind-count",
            "kind": "ram",
            "min_count": 2,
            "max_count": 2,
            "visibility": "student",
        },
        {
            "id": "psu-headroom",
            "name": "PSU con margine del 20 percento",
            "type": "slot-capacity-covers-installed-sum",
            "capacity_slot": "psu",
            "capacity_attribute": "capacity_w",
            "demand_attribute": "power_w",
            "fixed_demand": 100,
            "factor": 1.2,
            "unit": "W",
            "visibility": "student",
        },
    ],
}


def build(*, gpu: str, ram_a: str, ram_b: str, psu: str) -> dict:
    return {
        "schema_version": "efesto.build.v1",
        "scenario_id": "quantitative-test-001",
        "components": [
            {"slot": "cpu", "component_id": "cpu-120w"},
            {"slot": "gpu", "component_id": gpu},
            {"slot": "ram1", "component_id": ram_a},
            {"slot": "ram2", "component_id": ram_b},
            {"slot": "psu", "component_id": psu},
        ],
    }


def result_by_name(report: dict) -> dict[str, dict]:
    return {test["name"]: test for test in report["tests"]}


def test_quantitative_scenario_contract_is_valid() -> None:
    assert efesto_contracts.validate_scenario(SCENARIO, "scenario") == []


def test_quantitative_checks_reject_under_spec_build_and_accept_target() -> None:
    starter = build(gpu="gpu-12gb", ram_a="ram16-a", ram_b="ram16-b", psu="psu650")
    target = build(gpu="gpu-24gb", ram_a="ram32-a", ram_b="ram32-b", psu="psu750")

    initial = efesto_headless.grade_build(SCENARIO, starter)
    final = efesto_headless.grade_build(SCENARIO, target)
    tests = result_by_name(initial)

    assert initial["passed"] is False
    assert tests["VRAM almeno 24 GB"]["passed"] is False
    assert tests["RAM totale almeno 64 GB"]["passed"] is False
    assert tests["PSU con margine del 20 percento"]["passed"] is False
    assert tests["CPU entro 150 W"]["passed"] is True
    assert tests["CPU AM5"]["passed"] is True
    assert tests["Carico componenti entro 500 W"]["passed"] is True
    assert tests["Esattamente due moduli RAM"]["passed"] is True

    assert final["passed"] is True
    assert final["score"] == 10.0
    assert final["summary"] == {"passed": 8, "total": 8}


def test_student_build_cannot_override_trusted_component_attributes() -> None:
    malicious = build(gpu="gpu-12gb", ram_a="ram32-a", ram_b="ram32-b", psu="psu750")
    gpu_placement = next(item for item in malicious["components"] if item["slot"] == "gpu")
    gpu_placement["attributes"] = {"vram_gb": 999, "power_w": 1}

    report = efesto_headless.grade_build(SCENARIO, malicious)
    tests = result_by_name(report)

    assert tests["VRAM almeno 24 GB"]["passed"] is False
    assert "12 GB" in tests["VRAM almeno 24 GB"]["message"]


def test_invalid_quantitative_contract_values_are_rejected() -> None:
    invalid = deepcopy(SCENARIO)
    invalid["components"][0]["attributes"]["power_w"] = float("nan")
    invalid["checks"][1]["min_value"] = "24"
    invalid["checks"][6]["min_count"] = 3
    invalid["checks"][6]["max_count"] = 2
    invalid["checks"][7]["factor"] = 0

    errors = efesto_contracts.validate_scenario(invalid, "scenario")

    assert any("attributes.power_w" in error for error in errors)
    assert any("min_value deve essere un numero finito" in error for error in errors)
    assert any("min_count non puo superare max_count" in error for error in errors)
    assert any("factor deve essere maggiore di zero" in error for error in errors)


def test_missing_numeric_attribute_fails_filtered_sum_instead_of_undercounting() -> None:
    scenario = deepcopy(SCENARIO)
    del scenario["components"][3]["attributes"]["capacity_gb"]
    starter = build(gpu="gpu-24gb", ram_a="ram16-a", ram_b="ram32-b", psu="psu750")

    report = efesto_headless.grade_build(scenario, starter)
    tests = result_by_name(report)

    assert tests["RAM totale almeno 64 GB"]["passed"] is False
    assert "Attributo capacity_gb mancante" in tests["RAM totale almeno 64 GB"]["message"]
