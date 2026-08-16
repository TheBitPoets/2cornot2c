from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import create_submission_scaffold as scaffold
from scripts import student_lab_runner, student_lab_service
from scripts.thebitlab_technical_services import ExecutionRequest, ExecutionResult
from scripts.thebitlab_virtual_lab_contracts import (
    VIRTUAL_LAB_EXTENSION_KEY,
    normalize_virtual_lab_extension,
    validate_virtual_lab_extension,
)
from scripts.thebitlab_virtual_lab_runtime import VirtualLabExecutionService
from scripts.thebitlab_virtual_lab_scaffold import starter_content_for_activity


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _virtual_lab_contract(activity: dict[str, Any], source: str) -> dict[str, Any]:
    errors = validate_virtual_lab_extension(activity, source)
    if errors:
        raise ValueError("; ".join(errors))
    extension = normalize_virtual_lab_extension(activity)
    if extension is None:
        raise ValueError(f"Activity senza extensions.{VIRTUAL_LAB_EXTENSION_KEY}")
    return extension


def student_activity_snapshot(
    activity: dict[str, Any],
    extension: dict[str, Any],
) -> dict[str, Any]:
    """Return a student-safe Activity snapshot including only the normalized lab extension."""

    payload = scaffold.student_activity_payload(activity)
    payload["language"] = "virtual-lab"
    payload["source_name"] = str(extension["submission"]["path"])
    payload["extensions"] = {VIRTUAL_LAB_EXTENSION_KEY: extension}
    if "linguaggio" in payload:
        payload["linguaggio"] = "virtual-lab"
    return payload


def virtual_lab_readme(
    activity: dict[str, Any],
    *,
    identifier: str,
    extension: dict[str, Any],
) -> str:
    normalized = scaffold.normalize_activity(activity)
    title = str(normalized.get("title") or identifier)
    instructions = str(normalized.get("instructions") or "Segui le indicazioni del docente.")
    runtime = str(extension["runtime"])
    scenario_id = str(extension["scenario_id"])
    submission_path = str(extension["submission"]["path"])
    return (
        f"# {title}\n\n"
        f"Activity ID: `{identifier}`\n\n"
        f"Runtime virtuale: `{runtime}`\n\n"
        f"Scenario: `{scenario_id}`\n\n"
        "## Consegna\n\n"
        f"{instructions}\n\n"
        "## Artifact da modificare\n\n"
        f"- `{submission_path}`\n\n"
        "TheBitLab considera questo file lo stato della tua soluzione. "
        "Il voto non viene preso dall'interfaccia del simulatore: il file viene "
        "ricontrollato dal grader deterministico.\n\n"
        "## Controllo locale\n\n"
        "Usa il comando virtual-lab di TheBitLab oppure il pulsante equivalente "
        "quando disponibile nella TUI/UI studente.\n"
    )


def create_virtual_lab_scaffold(
    *,
    activity_path: Path,
    target_dir: Path,
    project_root: Path = PROJECT_ROOT,
    overwrite: bool = False,
) -> Path:
    """Create a student scaffold whose editable artifact is supplied by the registered runtime."""

    activity = scaffold.load_activity(activity_path)
    identifier = scaffold.activity_id(activity)
    scaffold.validate_activity_contract_or_raise(activity, identifier)
    extension, starter = starter_content_for_activity(
        activity,
        project_root=project_root,
    )
    submission_rel = scaffold.validate_relative_path(
        extension["submission"]["path"],
        f"extensions.{VIRTUAL_LAB_EXTENSION_KEY}.submission.path",
    )
    if scaffold.is_reserved_scaffold_target(submission_rel):
        raise ValueError(f"Artifact virtual-lab riservato allo scaffold: {submission_rel}")

    destination = scaffold.scaffold_dir(target_dir, identifier)
    scaffold.prepare_scaffold_destination(target_dir, destination)
    has_existing = any(destination.iterdir())
    if has_existing and not overwrite:
        raise ValueError(f"Consegna gia esistente: {destination}. Usa --force per aggiornare.")

    activity_output = scaffold.confined_output_path(
        destination, Path("activity.json"), create_parents=True
    )
    readme_output = scaffold.confined_output_path(
        destination, Path("README.md"), create_parents=True
    )
    for owned in (activity_output, readme_output):
        if owned.exists() and not owned.is_file():
            raise ValueError(f"File di scaffold non aggiornabile: {owned.name}")

    submission_output = scaffold.confined_output_path(
        destination, submission_rel, create_parents=True
    )
    if submission_output.exists() and not submission_output.is_file():
        raise ValueError(f"Artifact virtual-lab non e un file regolare: {submission_rel}")

    snapshot = student_activity_snapshot(activity, extension)
    scaffold.atomic_write_text(
        destination,
        Path("activity.json"),
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
    )
    if not submission_output.exists():
        scaffold.atomic_write_text(destination, submission_rel, starter)
    scaffold.atomic_write_text(
        destination,
        Path("README.md"),
        virtual_lab_readme(activity, identifier=identifier, extension=extension),
    )
    return destination


def _execution_report(
    assignment: dict[str, Any],
    *,
    source: Path,
    extension: dict[str, Any],
    result: ExecutionResult,
) -> dict[str, Any]:
    """Convert the common execution port to the existing student attempt report shape."""

    raw_report = result.metadata.get("runner_report")
    if isinstance(raw_report, dict):
        grading = student_lab_runner.redact_student_grading_report(raw_report)
    else:
        tests = [
            {
                "name": test.name,
                "passed": test.passed,
                "status": "passed" if test.passed else "failed",
                "visibility": "student",
                "message": test.detail,
            }
            for test in result.tests
        ]
        passed_count = sum(1 for test in tests if test["passed"])
        grading = {
            "passed": result.status == "passed" and bool(tests) and passed_count == len(tests),
            "status": result.status if result.status in {"passed", "failed"} else "execution-error",
            "tests": tests,
            "summary": {"passed": passed_count, "total": len(tests)},
            "score": round((passed_count / len(tests)) * 10, 2) if tests else 0.0,
            "detail": result.detail,
        }

    base = student_lab_runner.report_base(
        assignment,
        language="virtual-lab",
        source=source,
        backend="virtual-lab",
    )
    report = {**base, **grading}
    report["schema_version"] = "student_lab_run.v1"
    report["backend"] = "virtual-lab"
    report["runtime"] = str(extension["runtime"])
    report["scenario_id"] = str(extension["scenario_id"])
    report["assignment_id"] = str(assignment.get("assignment_id") or "")
    report["student_id"] = str(assignment.get("student_id") or "")
    report["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    report.setdefault("tests", [])
    report.setdefault("summary", {"passed": 0, "total": len(report["tests"])})
    return report


def run_virtual_lab_assignment(
    assignment: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    """Run one already-resolved TheBitLab assignment through its registered virtual runtime."""

    activity = student_lab_runner.load_activity(root, assignment)
    extension = _virtual_lab_contract(activity, "activity")
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_path_value = str(workspace.get("path") or "").strip()
    if not workspace_path_value:
        raise ValueError("workspace.path mancante nella consegna virtual-lab")
    workspace_path = student_lab_service.resolve_local_path(root, workspace_path_value)
    if workspace_path.is_symlink() or not workspace_path.is_dir():
        raise ValueError(f"Workspace virtual-lab non trovato o non regolare: {workspace_path_value}")

    submission_rel = scaffold.validate_relative_path(
        extension["submission"]["path"],
        f"extensions.{VIRTUAL_LAB_EXTENSION_KEY}.submission.path",
    )
    submission_path = scaffold.confined_output_path(
        workspace_path,
        submission_rel,
        create_parents=False,
    )
    service = VirtualLabExecutionService(project_root=runtime_root or root)
    result = service.run(
        ExecutionRequest(
            activity_id=str(assignment.get("activity_id") or activity.get("id") or ""),
            student_id=str(assignment.get("student_id") or ""),
            files={str(extension["submission"]["path"]): str(submission_path)},
            language="virtual-lab",
            metadata={
                "virtual_lab": extension,
                "workspace_path": str(workspace_path),
            },
        )
    )
    return _execution_report(
        assignment,
        source=submission_path,
        extension=extension,
        result=result,
    )


def persist_virtual_lab_attempt(
    assignment: dict[str, Any],
    report: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    final: bool = False,
) -> Path:
    """Persist a virtual-lab report using the same immutable Attempt history as code labs."""

    report_path = student_lab_runner.write_student_report(root, assignment, report)
    if final:
        student_lab_runner.finalize_report_attempt(
            root,
            assignment,
            report_path,
            attempt_id=str(report.get("attempt_id") or ""),
        )
    return report_path


def run_student_virtual_lab(
    *,
    student_id: str,
    assignment_id: str | None = None,
    activity_id: str | None = None,
    root: Path = PROJECT_ROOT,
    runtime_root: Path | None = None,
    now: str | None = None,
    final: bool = False,
) -> tuple[dict[str, Any], Path]:
    """Resolve, execute and persist one virtual-lab assignment for a student."""

    assignment = student_lab_runner.load_student_assignment(
        root=root,
        student_id=student_id,
        assignment_id=assignment_id,
        activity_id=activity_id,
        now=now,
    )
    report = run_virtual_lab_assignment(
        assignment,
        root=root,
        runtime_root=runtime_root,
    )
    report_path = persist_virtual_lab_attempt(
        assignment,
        report,
        root=root,
        final=final,
    )
    return report, report_path
