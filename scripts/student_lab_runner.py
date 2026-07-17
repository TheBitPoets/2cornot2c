from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import grade_activity, student_lab_service
from scripts.thebitlab_contracts import normalize_activity


DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_SOURCE_NAMES = {
    "c": "main.c",
    "python": "main.py",
}


def clean_text(value: Any) -> str:
    """Return a stripped string value."""

    return str(value or "").strip()


def load_activity(root: Path, assignment: dict[str, Any]) -> dict[str, Any]:
    """Load the full activity JSON for a lab assignment."""

    activity_summary = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    activity_path_value = clean_text(activity_summary.get("path"))
    if not activity_path_value:
        raise ValueError("activity.path mancante nella consegna.")
    activity_path = student_lab_service.resolve_local_path(root, activity_path_value)
    if not activity_path.is_file():
        raise ValueError(f"Activity non trovata: {activity_path_value}")
    payload = json.loads(activity_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Activity non valida: {activity_path_value}")
    return payload


def source_name_for(activity: dict[str, Any], language: str) -> str:
    """Return the source filename expected in the student workspace."""

    normalized = normalize_activity(activity)
    return clean_text(normalized.get("source_name")) or DEFAULT_SOURCE_NAMES.get(language, "")


def is_safe_source_name(source_name: str) -> bool:
    """Return whether source_name is a simple file name inside the workspace."""

    path = Path(source_name)
    return bool(source_name) and not path.is_absolute() and len(path.parts) == 1 and ".." not in path.parts


def report_base(assignment: dict[str, Any], *, language: str, source: Path, backend: str = "local") -> dict[str, Any]:
    """Return common fields for local runner reports."""

    return {
        "schema_version": "student_lab_run.v1",
        "backend": backend,
        "assignment_id": clean_text(assignment.get("assignment_id")),
        "activity_id": clean_text(assignment.get("activity_id")),
        "student_id": clean_text(assignment.get("student_id")),
        "language": language,
        "source": str(source),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def error_report(
    assignment: dict[str, Any],
    *,
    language: str,
    source: Path,
    status: str,
    error: str,
    backend: str = "local",
) -> dict[str, Any]:
    """Return a deterministic error report."""

    return {
        **report_base(assignment, language=language, source=source, backend=backend),
        "passed": False,
        "status": status,
        "summary": {"passed": 0, "total": 0},
        "tests": [],
        "stdout": "",
        "stderr": error,
        "error": error,
    }


def pytest_targets(workspace: Path) -> list[str]:
    """Return pytest targets discoverable in a student workspace."""

    tests_dir = workspace / "tests"
    if tests_dir.is_dir():
        return ["tests"]
    root_tests = sorted(path.name for path in workspace.glob("test_*.py") if path.is_file())
    return root_tests


def parse_pytest_summary(output: str) -> dict[str, int | None]:
    """Extract a small test count summary from pytest output."""

    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for key in counts:
        match = re.search(rf"(\d+)\s+{key}", output)
        if match:
            counts[key] = int(match.group(1))
    total = sum(counts.values())
    if total == 0:
        return {"passed": None, "total": None}
    return {"passed": counts["passed"], "total": total}


def run_python_pytest(
    assignment: dict[str, Any],
    *,
    workspace: Path,
    source: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run pytest in the student workspace and return a report."""

    if not source.is_file():
        return error_report(
            assignment,
            language="python",
            source=source,
            status="source-not-found",
            error=f"Sorgente non trovato: {source}",
        )
    targets = pytest_targets(workspace)
    if not targets:
        return error_report(
            assignment,
            language="python",
            source=source,
            status="no-tests",
            error="Nessun test pytest rilevato nel workspace.",
        )
    command = [sys.executable, "-m", "pytest", "-q", *targets]
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        return {
            **report_base(assignment, language="python", source=source),
            "passed": False,
            "status": "timeout",
            "command": command,
            "returncode": None,
            "summary": parse_pytest_summary(f"{stdout}\n{stderr}"),
            "tests": [],
            "stdout": stdout,
            "stderr": stderr,
            "error": f"Timeout dopo {timeout_seconds} secondi.",
        }
    status = "passed" if result.returncode == 0 else "failed"
    output = f"{result.stdout}\n{result.stderr}"
    return {
        **report_base(assignment, language="python", source=source),
        "passed": result.returncode == 0,
        "status": status,
        "command": command,
        "returncode": result.returncode,
        "summary": parse_pytest_summary(output),
        "tests": [],
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def wrap_c_report(assignment: dict[str, Any], source: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Wrap the existing C grader output in the student lab runner contract."""

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {"passed": 0, "total": 0}
    return {
        **report_base(assignment, language="c", source=source),
        **report,
        "schema_version": "student_lab_run.v1",
        "backend": "local",
        "assignment_id": clean_text(assignment.get("assignment_id")),
        "student_id": clean_text(assignment.get("student_id")),
        "summary": summary,
    }


def run_local_assignment(
    assignment: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run one student lab assignment locally without Docker."""

    activity = load_activity(root, assignment)
    normalized = normalize_activity(activity)
    language = clean_text(normalized.get("language")).lower()
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_path_value = clean_text(workspace.get("path"))
    workspace_path = student_lab_service.resolve_local_path(root, workspace_path_value) if workspace_path_value else root
    source_name = source_name_for(activity, language)
    source = workspace_path / source_name if source_name else workspace_path
    if not is_safe_source_name(source_name):
        return error_report(
            assignment,
            language=language,
            source=source,
            status="invalid-source-name",
            error="source_name deve essere un nome file semplice dentro il workspace.",
        )
    if not workspace_path.is_dir():
        return error_report(
            assignment,
            language=language,
            source=source,
            status="workspace-not-found",
            error=f"Workspace non trovato: {workspace_path_value}",
        )
    if language == "python":
        return run_python_pytest(assignment, workspace=workspace_path, source=source, timeout_seconds=timeout_seconds)
    if language == "c":
        return wrap_c_report(
            assignment,
            source,
            grade_activity.grade_activity(activity, source, timeout_seconds=timeout_seconds, language="c"),
        )
    return error_report(
        assignment,
        language=language,
        source=source,
        status="unsupported-language",
        error=f"Runner locale non supportato per il linguaggio: {language or '-'}",
    )


def select_assignment(
    assignments: list[dict[str, Any]],
    *,
    assignment_id: str | None = None,
    activity_id: str | None = None,
) -> dict[str, Any]:
    """Return the requested assignment from a student lab payload."""

    if assignment_id:
        for assignment in assignments:
            if assignment.get("assignment_id") == assignment_id:
                return assignment
        raise ValueError(f"Consegna non trovata: {assignment_id}")
    if activity_id:
        matches = [assignment for assignment in assignments if assignment.get("activity_id") == activity_id]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"Activity {activity_id} presente in piu consegne. Usa --assignment-id per scegliere quella corretta."
            )
        raise ValueError(f"Activity non trovata: {activity_id}")
    if not assignment_id and not activity_id and len(assignments) == 1:
        return assignments[0]
    raise ValueError("Nessuna consegna selezionata. Usa --assignment-id o --activity-id.")


def run_student_assignment(
    *,
    root: Path = PROJECT_ROOT,
    student_id: str,
    assignment_id: str | None = None,
    activity_id: str | None = None,
    now: str | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Load and run one assignment for a student."""

    payload = student_lab_service.student_lab_payload(root=root, student_id=student_id, now=now)
    assignments = payload.get("assignments") if isinstance(payload.get("assignments"), list) else []
    assignment = select_assignment(assignments, assignment_id=assignment_id, activity_id=activity_id)
    return run_local_assignment(assignment, root=root, timeout_seconds=timeout_seconds)


def positive_int(value: str) -> int:
    """Parse a positive integer CLI argument."""

    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("deve essere un numero intero") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("deve essere un numero positivo")
    return number


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the local student lab runner."""

    parser = argparse.ArgumentParser(description="Esegue localmente una consegna del lab studente.")
    parser.add_argument("--student-id", required=True, help="Identificativo studente, per esempio rossi-mario.")
    parser.add_argument("--assignment-id", help="ID della consegna da eseguire.")
    parser.add_argument("--activity-id", help="ID activity da eseguire se l'assegnazione e univoca.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Root del repository TheBitLab.")
    parser.add_argument("--now", help="Data ISO da usare per calcolare lo stato della consegna.")
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout del runner locale.")
    return parser.parse_args()


def main() -> int:
    """Run the local student lab runner from the command line."""

    args = parse_args()
    try:
        report = run_student_assignment(
            root=args.root.resolve(strict=False),
            student_id=args.student_id,
            assignment_id=args.assignment_id,
            activity_id=args.activity_id,
            now=args.now,
            timeout_seconds=args.timeout,
        )
    except ValueError as error:
        print(f"Runner lab non disponibile:\n{error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
