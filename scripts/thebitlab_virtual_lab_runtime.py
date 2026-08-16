from __future__ import annotations

from pathlib import Path
from typing import Protocol

from scripts.efesto_headless import EfestoRuntimeAdapter
from scripts.thebitlab_technical_services import ExecutionRequest, ExecutionResult, RunnerTestResult
from scripts.thebitlab_virtual_lab_contracts import (
    VIRTUAL_LAB_EXTENSION_KEY,
    normalize_virtual_lab_extension,
    validate_virtual_lab_extension,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VirtualLabRuntimeAdapter(Protocol):
    """Runtime-specific adapter hidden behind TheBitLab's ExecutionService port."""

    runtime_id: str

    def run(
        self,
        *,
        scenario_id: str,
        submission_path: Path,
        activity_id: str,
    ) -> ExecutionResult: ...


def default_runtime_registry(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, VirtualLabRuntimeAdapter]:
    """Return the installation-controlled virtual-lab runtime registry."""

    efesto = EfestoRuntimeAdapter(project_root=project_root)
    return {efesto.runtime_id: efesto}


def _extension_activity(extension: object) -> dict:
    return {"extensions": {VIRTUAL_LAB_EXTENSION_KEY: extension}}


def _submission_failure(detail: str) -> ExecutionResult:
    return ExecutionResult(
        status="failed",
        tests=[
            RunnerTestResult(
                name="Artifact di consegna presente",
                passed=False,
                detail=detail,
            )
        ],
        detail=detail,
    )


class VirtualLabExecutionService:
    """Dispatch a virtual-lab Activity to an explicitly registered runtime adapter."""

    def __init__(
        self,
        *,
        project_root: Path = PROJECT_ROOT,
        registry: dict[str, VirtualLabRuntimeAdapter] | None = None,
    ) -> None:
        self.project_root = project_root
        self.registry = registry if registry is not None else default_runtime_registry(project_root)

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        extension = request.metadata.get("virtual_lab")
        activity = _extension_activity(extension)
        errors = validate_virtual_lab_extension(activity, "ExecutionRequest.virtual_lab")
        if errors:
            return ExecutionResult(status="invalid_payload", detail="; ".join(errors))

        normalized = normalize_virtual_lab_extension(activity)
        if normalized is None:
            return ExecutionResult(
                status="invalid_payload",
                detail="ExecutionRequest.virtual_lab mancante.",
            )

        runtime_id = str(normalized["runtime"])
        adapter = self.registry.get(runtime_id)
        if adapter is None:
            return ExecutionResult(
                status="runner_unavailable",
                detail=f"Runtime virtual-lab non registrato: {runtime_id}.",
            )

        submission = normalized["submission"]
        submission_key = str(submission["path"])
        submission_value = request.files.get(submission_key)
        if not submission_value:
            return _submission_failure(
                f"Artifact richiesto non presente nella consegna: {submission_key}."
            )

        submission_path = Path(submission_value).resolve(strict=False)
        workspace_value = request.metadata.get("workspace_path")
        if workspace_value:
            workspace = Path(str(workspace_value)).resolve(strict=False)
            try:
                submission_path.relative_to(workspace)
            except ValueError:
                return ExecutionResult(
                    status="invalid_payload",
                    detail="L'artifact virtual-lab deve restare dentro il workspace studente.",
                )
        if submission_path.is_symlink() or not submission_path.is_file():
            return _submission_failure(
                f"Artifact richiesto non trovato o non regolare: {submission_key}."
            )

        return adapter.run(
            scenario_id=str(normalized["scenario_id"]),
            submission_path=submission_path,
            activity_id=request.activity_id,
        )
