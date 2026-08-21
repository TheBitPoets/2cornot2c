from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import (
    student_lab_service,
    thebitlab_runtime_contracts,
    thebitlab_runtime_plugins,
    thebitlab_runtime_sandbox,
)

DEFAULT_REGISTRY = thebitlab_runtime_plugins.RuntimePluginRegistry()


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def activity_uses_runtime(activity: dict[str, Any]) -> bool:
    return thebitlab_runtime_contracts.normalize_runtime_extension(activity) is not None


def _activity_path(root: Path, assignment: dict[str, Any]) -> Path:
    summary = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    value = clean_text(summary.get("path"))
    if not value:
        raise ValueError("activity.path mancante nella consegna.")
    path = student_lab_service.resolve_local_path(root, value)
    if not path.is_file():
        raise ValueError(f"Activity non trovata: {value}")
    return path


def _workspace_path(root: Path, assignment: dict[str, Any]) -> Path:
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    value = clean_text(workspace.get("path"))
    if not value:
        raise ValueError("workspace.path mancante nella consegna.")
    path = student_lab_service.resolve_local_path(root, value)
    if not path.is_dir():
        raise ValueError(f"Workspace non trovato: {value}")
    return path


def _load_activity(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Activity non leggibile: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Activity non valida: atteso oggetto JSON")
    return payload


def _runtime_context(
    assignment: dict[str, Any],
    *,
    root: Path,
    timeout_seconds: int,
    registry: thebitlab_runtime_plugins.RuntimePluginRegistry,
) -> tuple[
    dict[str, Any],
    thebitlab_runtime_plugins.LoadedRuntimePlugin,
    thebitlab_runtime_plugins.RuntimeRequest,
]:
    activity_path = _activity_path(root, assignment)
    workspace_path = _workspace_path(root, assignment)
    activity = _load_activity(activity_path)
    extension = thebitlab_runtime_contracts.normalize_runtime_extension(activity)
    if extension is None:
        raise ValueError("Activity senza extensions.thebitlab.runtime")
    runtime_id = clean_text(extension.get("runtime_id"))
    try:
        loaded = registry.get(runtime_id)
        thebitlab_runtime_plugins.assert_runtime_supports_activity(activity, loaded.descriptor)
        probe = thebitlab_runtime_plugins.probe_runtime(loaded)
    except thebitlab_runtime_plugins.RuntimePluginError as error:
        raise ValueError(str(error)) from error
    if not probe.available:
        raise ValueError(probe.detail or f"Runtime {runtime_id} non disponibile")
    request = thebitlab_runtime_plugins.runtime_request_from_activity(
        activity,
        activity_id=clean_text(assignment.get("activity_id")),
        assignment_id=clean_text(assignment.get("assignment_id")),
        student_id=clean_text(assignment.get("student_id")),
        activity_path=activity_path,
        workspace_path=workspace_path,
        timeout_seconds=timeout_seconds,
        metadata={"source": "student_lab_runner"},
    )
    return activity, loaded, request


def _source_from_request(request: thebitlab_runtime_plugins.RuntimeRequest) -> Path:
    if request.submission_artifacts:
        return request.workspace_path / request.submission_artifacts[0].path
    return request.workspace_path


def _report_base(
    assignment: dict[str, Any],
    *,
    runtime_id: str,
    source: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "student_lab_run.v1",
        "backend": "runtime",
        "runtime_id": runtime_id,
        "assignment_id": clean_text(assignment.get("assignment_id")),
        "activity_id": clean_text(assignment.get("activity_id")),
        "student_id": clean_text(assignment.get("student_id")),
        "language": f"runtime:{runtime_id}",
        "source": str(source),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def runtime_error_report(
    assignment: dict[str, Any],
    *,
    runtime_id: str,
    source: Path,
    error: str,
    status: str = "runtime-unavailable",
) -> dict[str, Any]:
    return {
        **_report_base(assignment, runtime_id=runtime_id or "unknown", source=source),
        "passed": False,
        "status": status,
        "summary": {"passed": 0, "total": 0},
        "tests": [],
        "stdout": "",
        "stderr": error,
        "error": error,
    }


def _student_runtime_backend(
    requested_backend: str,
    loaded: thebitlab_runtime_plugins.LoadedRuntimePlugin,
) -> str:
    """Prefer the authoritative sandbox for student-facing sandbox-capable runtimes.

    Historical student callers default to ``local``. Once an administrator-installed
    runtime advertises ``sandbox-plan.v1``, treating that implicit local value as
    process-only grading would silently downgrade the security boundary. Promote it
    to Docker instead. Legacy v1 runtimes that do not offer the sandbox capability
    keep their existing local behavior.
    """

    if (
        requested_backend == "local"
        and thebitlab_runtime_plugins.RUNTIME_SANDBOX_CAPABILITY
        in loaded.descriptor.capabilities
    ):
        return "docker"
    return requested_backend


def run_runtime_assignment(
    assignment: dict[str, Any],
    *,
    root: Path,
    timeout_seconds: int,
    backend: str = "local",
    registry: thebitlab_runtime_plugins.RuntimePluginRegistry = DEFAULT_REGISTRY,
    sandbox_service: thebitlab_runtime_sandbox.RuntimeSandboxExecutionService | None = None,
) -> dict[str, Any]:
    runtime_id = "unknown"
    source = root
    effective_backend = backend
    try:
        activity_path = _activity_path(root, assignment)
        activity = _load_activity(activity_path)
        extension = thebitlab_runtime_contracts.normalize_runtime_extension(activity)
        runtime_id = clean_text(extension.get("runtime_id")) if extension else "unknown"
        workspace = _workspace_path(root, assignment)
        source = workspace
        _, loaded, request = _runtime_context(
            assignment,
            root=root,
            timeout_seconds=timeout_seconds,
            registry=registry,
        )
        source = _source_from_request(request)
        effective_backend = _student_runtime_backend(backend, loaded)
        if effective_backend == "local":
            execution = thebitlab_runtime_plugins.run_runtime(loaded, request)
        elif effective_backend == "docker":
            plan = thebitlab_runtime_plugins.prepare_sandbox_runtime(loaded, request)
            service = (
                sandbox_service
                or thebitlab_runtime_sandbox.DockerRuntimeSandboxExecutionService()
            )
            try:
                sandbox_result = service.run(plan, request)
            except subprocess.TimeoutExpired as error:
                return runtime_error_report(
                    assignment,
                    runtime_id=runtime_id,
                    source=source,
                    error=f"Sandbox runtime interrotta dopo {error.timeout} secondi.",
                    status="timeout",
                )
            except FileNotFoundError:
                return runtime_error_report(
                    assignment,
                    runtime_id=runtime_id,
                    source=source,
                    error=(
                        "Docker non trovato; il grading runtime autorevole "
                        "non e disponibile."
                    ),
                )
            if sandbox_result.get("worker_schema") != plan.profile.worker_schema:
                raise thebitlab_runtime_plugins.RuntimePluginIncompatibleError(
                    "Il worker schema restituito dalla sandbox non coincide con il piano"
                )
            execution = thebitlab_runtime_plugins.finalize_sandbox_runtime(
                loaded, request, sandbox_result
            )
        else:
            raise ValueError(f"Backend runtime non supportato: {effective_backend}")
    except FileNotFoundError as error:
        missing = error.filename or str(error)
        return runtime_error_report(
            assignment,
            runtime_id=runtime_id,
            source=source,
            error=f"File runtime non trovato: {missing}",
        )
    except (ValueError, thebitlab_runtime_plugins.RuntimePluginError) as error:
        return runtime_error_report(
            assignment,
            runtime_id=runtime_id,
            source=source,
            error=str(error),
        )

    tests = [
        {
            "name": test.name,
            "passed": test.passed,
            "status": "passed" if test.passed else "failed",
            "message": test.detail,
            "visibility": "student",
        }
        for test in execution.tests
    ]
    passed_count = sum(1 for test in execution.tests if test.passed)
    total = len(execution.tests)
    passed = execution.status == "passed" and (not execution.tests or passed_count == total)
    score = execution.metadata.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        score = round((passed_count / total) * 10, 2) if total else None
    report = {
        **_report_base(assignment, runtime_id=loaded.descriptor.runtime_id, source=source),
        "passed": passed,
        "status": execution.status,
        "summary": {"passed": passed_count, "total": total},
        "tests": tests,
        "stdout": execution.stdout,
        "stderr": execution.stderr,
        "detail": execution.detail,
        "runtime": {
            "plugin_version": loaded.descriptor.plugin_version,
            "backend": effective_backend,
            "requested_backend": backend,
            "metadata": execution.metadata,
        },
    }
    if score is not None:
        report["score"] = float(score)
    return report


def launch_runtime_assignment(
    assignment: dict[str, Any],
    *,
    root: Path,
    timeout_seconds: int = 30,
    registry: thebitlab_runtime_plugins.RuntimePluginRegistry = DEFAULT_REGISTRY,
) -> thebitlab_runtime_plugins.RuntimeLaunchResult:
    try:
        _, loaded, request = _runtime_context(
            assignment,
            root=root,
            timeout_seconds=timeout_seconds,
            registry=registry,
        )
        return thebitlab_runtime_plugins.launch_runtime(loaded, request)
    except thebitlab_runtime_plugins.RuntimePluginError as error:
        raise ValueError(str(error)) from error
