from __future__ import annotations

import json
from pathlib import Path

from scripts.efesto_headless import EfestoRuntimeAdapter
from scripts.thebitlab_technical_services import ExecutionRequest, ExecutionResult
from scripts.thebitlab_virtual_lab_runtime import VirtualLabExecutionService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ID = "pcie-lane-sharing-001"


def extension(runtime: str = "efesto") -> dict:
    return {
        "schema_version": "virtual_lab.v1",
        "runtime": runtime,
        "scenario_id": SCENARIO_ID,
        "submission": {
            "path": "build.json",
            "media_type": "application/json",
        },
        "capabilities": ["deterministic-grade"],
    }


def build() -> dict:
    return {
        "schema_version": "efesto.build.v1",
        "scenario_id": SCENARIO_ID,
        "components": [
            {"slot": "pcie1", "component_id": "gpu-3090-001"},
            {"slot": "m2_1", "component_id": "nvme-2tb-001"},
            {"slot": "pcie2", "component_id": "nic-10gbe-001"},
        ],
    }


def request(tmp_path, *, runtime: str = "efesto") -> ExecutionRequest:
    build_path = tmp_path / "build.json"
    build_path.write_text(json.dumps(build()), encoding="utf-8")
    return ExecutionRequest(
        activity_id="hw-pcie-lane-sharing-001",
        student_id="rossi-mario",
        files={"build.json": str(build_path)},
        language="virtual-lab",
        metadata={
            "virtual_lab": extension(runtime),
            "workspace_path": str(tmp_path),
        },
    )


def test_service_dispatches_registered_efesto_runtime(tmp_path) -> None:
    service = VirtualLabExecutionService(project_root=PROJECT_ROOT)

    result = service.run(request(tmp_path))

    assert result.status == "passed"
    assert result.metadata["runtime"] == "efesto"
    assert result.metadata["scenario_id"] == SCENARIO_ID
    assert len(result.tests) == 5


def test_service_rejects_unregistered_runtime(tmp_path) -> None:
    service = VirtualLabExecutionService(project_root=PROJECT_ROOT, registry={})

    result = service.run(request(tmp_path, runtime="unknown-runtime"))

    assert result.status == "runner_unavailable"
    assert "unknown-runtime" in result.detail


def test_service_rejects_submission_outside_workspace(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "build.json"
    outside.write_text(json.dumps(build()), encoding="utf-8")
    service = VirtualLabExecutionService(project_root=PROJECT_ROOT)
    run_request = ExecutionRequest(
        activity_id="hw-pcie-lane-sharing-001",
        student_id="rossi-mario",
        files={"build.json": str(outside)},
        language="virtual-lab",
        metadata={
            "virtual_lab": extension(),
            "workspace_path": str(workspace),
        },
    )

    result = service.run(run_request)

    assert result.status == "invalid_payload"
    assert "workspace" in result.detail


def test_service_returns_failed_test_when_submission_is_missing(tmp_path) -> None:
    service = VirtualLabExecutionService(project_root=PROJECT_ROOT)
    run_request = ExecutionRequest(
        activity_id="hw-pcie-lane-sharing-001",
        student_id="rossi-mario",
        files={},
        language="virtual-lab",
        metadata={
            "virtual_lab": extension(),
            "workspace_path": str(tmp_path),
        },
    )

    result = service.run(run_request)

    assert result.status == "failed"
    assert result.tests[0].passed is False
    assert result.tests[0].name == "Artifact di consegna presente"


def test_registry_can_be_replaced_without_changing_service_contract(tmp_path) -> None:
    class FakeRuntime:
        runtime_id = "fake"

        def run(self, *, scenario_id: str, submission_path: Path, activity_id: str) -> ExecutionResult:
            return ExecutionResult(status="passed", detail=f"{scenario_id}:{activity_id}")

    service = VirtualLabExecutionService(
        project_root=PROJECT_ROOT,
        registry={"fake": FakeRuntime()},
    )

    result = service.run(request(tmp_path, runtime="fake"))

    assert result.status == "passed"
    assert result.detail == f"{SCENARIO_ID}:hw-pcie-lane-sharing-001"
