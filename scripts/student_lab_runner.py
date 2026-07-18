from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import grade_activity, student_lab_service
from scripts.thebitlab_contracts import normalize_activity


DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_DOCKER_IMAGE = grade_activity.DEFAULT_DOCKER_IMAGE
RUNNER_BACKENDS = {"local", "docker"}
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


PYTEST_RESULT_RE = re.compile(
    r"^(?P<node>\S+::\S+)\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b",
    re.MULTILINE,
)


def parse_pytest_test_results(output: str) -> list[dict[str, Any]]:
    """Return per-test results from pytest verbose output."""

    results: list[dict[str, Any]] = []
    for match in PYTEST_RESULT_RE.finditer(output):
        node = match.group("node").replace("\\", "/")
        status = match.group("status").lower()
        passed = status in {"passed", "xpass"}
        item: dict[str, Any] = {
            "name": node,
            "passed": passed,
            "status": status,
        }
        if not passed:
            item["message"] = output.strip()
        results.append(item)
    return results


def pytest_report_tests(*, passed: bool, status: str, stdout: str, stderr: str) -> list[dict[str, Any]]:
    """Return an aggregate pytest test entry for dashboard grading."""

    return [
        {
            "name": "pytest",
            "passed": passed,
            "status": status,
            "message": stderr or stdout,
        }
    ]


def c_test_message(test: dict[str, Any]) -> str:
    """Return a compact student-facing message for a C test result."""

    for key in ("message", "detail", "error", "stderr"):
        value = clean_text(test.get(key))
        if value:
            return " ".join(value.split())
    expected = clean_text(test.get("expected_stdout"))
    actual = clean_text(test.get("stdout"))
    if expected or actual:
        return f"Output atteso: {expected or '-'}; output ottenuto: {actual or '-'}"
    status = clean_text(test.get("status"))
    return f"Test non superato: {status}" if status else ""


def normalize_c_tests(tests: Any) -> list[dict[str, Any]]:
    """Return C test results with fields useful for the TUI."""

    if not isinstance(tests, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(tests, start=1):
        if not isinstance(item, dict):
            continue
        test = dict(item)
        test.setdefault("name", f"test {index}")
        if "status" not in test:
            test["status"] = "passed" if test.get("passed") is True else "failed" if test.get("passed") is False else "unknown"
        if test.get("passed") is not True and not clean_text(test.get("message")):
            message = c_test_message(test)
            if message:
                test["message"] = message
        normalized.append(test)
    return normalized


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
    command = [sys.executable, "-m", "pytest", "-vv", *targets]
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
    test_results = parse_pytest_test_results(output) or pytest_report_tests(
        passed=result.returncode == 0,
        status=status,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    return {
        **report_base(assignment, language="python", source=source),
        "passed": result.returncode == 0,
        "status": status,
        "command": command,
        "returncode": result.returncode,
        "summary": parse_pytest_summary(output),
        "tests": test_results,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def wrap_c_report(assignment: dict[str, Any], source: Path, report: dict[str, Any]) -> dict[str, Any]:
    """Wrap the existing C grader output in the student lab runner contract."""

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {"passed": 0, "total": 0}
    tests = normalize_c_tests(report.get("tests"))
    return {
        **report_base(assignment, language="c", source=source),
        **report,
        "schema_version": "student_lab_run.v1",
        "backend": "local",
        "assignment_id": clean_text(assignment.get("assignment_id")),
        "student_id": clean_text(assignment.get("student_id")),
        "summary": summary,
        "tests": tests,
    }


def run_c_docker(
    assignment: dict[str, Any],
    *,
    activity_path: Path,
    source: Path,
    timeout_seconds: int,
    docker_image: str = DEFAULT_DOCKER_IMAGE,
) -> dict[str, Any]:
    """Run a C assignment through the existing Docker grading sandbox."""

    if not source.is_file():
        return error_report(
            assignment,
            language="c",
            source=source,
            status="source-not-found",
            error=f"Sorgente non trovato: {source}",
            backend="docker",
        )
    with tempfile.TemporaryDirectory(prefix="thebitlab-student-docker-") as temp_dir:
        temp_root = Path(temp_dir)
        try:
            workspace, copied_activity, copied_source = grade_activity.prepare_docker_workspace(activity_path, source, temp_root)
            docker_timeout = grade_activity.docker_timeout_seconds(grade_activity.load_activity(copied_activity), timeout_seconds)
            command = grade_activity.docker_command(
                activity=copied_activity,
                source=copied_source,
                language="c",
                timeout_seconds=timeout_seconds,
                image=docker_image,
                workspace=workspace,
            )
        except (OSError, ValueError) as error:
            return error_report(
                assignment,
                language="c",
                source=source,
                status="docker-setup-error",
                error=str(error),
                backend="docker",
            )
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=docker_timeout, check=False)
        except subprocess.TimeoutExpired:
            return error_report(
                assignment,
                language="c",
                source=source,
                status="docker-timeout",
                error=f"Timeout Docker dopo {docker_timeout} secondi.",
                backend="docker",
            )
        except FileNotFoundError:
            return error_report(
                assignment,
                language="c",
                source=source,
                status="docker-not-found",
                error="Docker non trovato. Installa Docker oppure usa --backend local.",
                backend="docker",
            )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        return error_report(
            assignment,
            language="c",
            source=source,
            status="docker-invalid-output",
            error=result.stderr or result.stdout or "Il container non ha prodotto JSON valido.",
            backend="docker",
        )
    if not grade_activity.has_minimal_report_shape(report):
        return error_report(
            assignment,
            language="c",
            source=source,
            status="docker-invalid-report",
            error=result.stderr or "Il container non ha prodotto un report di grading valido.",
            backend="docker",
        )
    if result.returncode != 0 and report.get("passed") is True:
        return error_report(
            assignment,
            language="c",
            source=source,
            status="docker-inconsistent-report",
            error=result.stderr or "Il container ha fallito ma ha prodotto un report di successo.",
            backend="docker",
        )
    wrapped = wrap_c_report(assignment, source, report)
    wrapped["backend"] = "docker"
    return wrapped


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


def run_docker_assignment(
    assignment: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    docker_image: str = DEFAULT_DOCKER_IMAGE,
) -> dict[str, Any]:
    """Run one student lab assignment with Docker when supported."""

    activity_summary = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    activity_path_value = clean_text(activity_summary.get("path"))
    activity_path = student_lab_service.resolve_local_path(root, activity_path_value) if activity_path_value else root
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
            backend="docker",
        )
    if not workspace_path.is_dir():
        return error_report(
            assignment,
            language=language,
            source=source,
            status="workspace-not-found",
            error=f"Workspace non trovato: {workspace_path_value}",
            backend="docker",
        )
    if language == "c":
        return run_c_docker(
            assignment,
            activity_path=activity_path,
            source=source,
            timeout_seconds=timeout_seconds,
            docker_image=docker_image,
        )
    return error_report(
        assignment,
        language=language,
        source=source,
        status="unsupported-docker-language",
        error=f"Runner Docker non supportato per il linguaggio: {language or '-'}",
        backend="docker",
    )


def run_assignment(
    assignment: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    backend: str = "local",
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    docker_image: str = DEFAULT_DOCKER_IMAGE,
) -> dict[str, Any]:
    """Run one assignment with the requested backend."""

    if backend == "local":
        return run_local_assignment(assignment, root=root, timeout_seconds=timeout_seconds)
    if backend == "docker":
        return run_docker_assignment(
            assignment,
            root=root,
            timeout_seconds=timeout_seconds,
            docker_image=docker_image,
        )
    raise ValueError(f"Backend runner non supportato: {backend}")


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
    backend: str = "local",
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    docker_image: str = DEFAULT_DOCKER_IMAGE,
) -> dict[str, Any]:
    """Load and run one assignment for a student."""

    payload = student_lab_service.student_lab_payload(root=root, student_id=student_id, now=now)
    assignments = payload.get("assignments") if isinstance(payload.get("assignments"), list) else []
    assignment = select_assignment(assignments, assignment_id=assignment_id, activity_id=activity_id)
    return run_assignment(
        assignment,
        root=root,
        backend=backend,
        timeout_seconds=timeout_seconds,
        docker_image=docker_image,
    )


def load_student_assignment(
    *,
    root: Path = PROJECT_ROOT,
    student_id: str,
    assignment_id: str | None = None,
    activity_id: str | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Load one normalized assignment for a student."""

    payload = student_lab_service.student_lab_payload(root=root, student_id=student_id, now=now)
    assignments = payload.get("assignments") if isinstance(payload.get("assignments"), list) else []
    return select_assignment(assignments, assignment_id=assignment_id, activity_id=activity_id)


def assignment_report_path(root: Path, assignment: dict[str, Any]) -> Path:
    """Return the default report path for an assignment."""

    report = assignment.get("report") if isinstance(assignment.get("report"), dict) else {}
    report_path_value = clean_text(report.get("path"))
    if not report_path_value:
        raise ValueError("report.path mancante nella consegna.")
    return student_lab_service.resolve_local_path(root, report_path_value)


def student_repo_path(root: Path, assignment: dict[str, Any]) -> Path | None:
    """Infer the student repository path from the assignment workspace."""

    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_path_value = clean_text(workspace.get("path"))
    if not workspace_path_value:
        return None
    workspace_path = student_lab_service.resolve_local_path(root, workspace_path_value)
    if workspace_path.parent.name != "assignments":
        return None
    return workspace_path.parent.parent


def storage_report(root: Path, assignment: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Return a report normalized for storage in the student repository."""

    stored = dict(report)
    stored.setdefault("submitted_at", clean_text(report.get("generated_at")) or datetime.now().astimezone().isoformat(timespec="seconds"))
    repo_path = student_repo_path(root, assignment)
    source_value = clean_text(stored.get("source"))
    if repo_path is not None and source_value:
        source_path = Path(source_value)
        resolved_source = source_path.resolve(strict=False) if source_path.is_absolute() else (root / source_path).resolve(strict=False)
        try:
            stored["source"] = str(resolved_source.relative_to(repo_path.resolve())).replace("\\", "/")
        except ValueError:
            stored["source"] = source_value
    return stored


def write_student_report(root: Path, assignment: dict[str, Any], report: dict[str, Any], report_path: Path | None = None) -> Path:
    """Persist a student lab report as JSON."""

    output = report_path or assignment_report_path(root, assignment)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(storage_report(root, assignment, report), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output


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
    parser.add_argument("--backend", choices=sorted(RUNNER_BACKENDS), default="local", help="Backend runner da usare.")
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE, help="Immagine Docker da usare con --backend docker.")
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout del runner locale.")
    parser.add_argument("--write-report", action="store_true", help="Scrive il report nel path standard dello studente.")
    parser.add_argument("--report", type=Path, help="Path alternativo del report JSON da scrivere.")
    return parser.parse_args()


def main() -> int:
    """Run the local student lab runner from the command line."""

    args = parse_args()
    try:
        root = args.root.resolve(strict=False)
        assignment = load_student_assignment(
            root=root,
            student_id=args.student_id,
            assignment_id=args.assignment_id,
            activity_id=args.activity_id,
            now=args.now,
        )
        report = run_assignment(
            assignment,
            root=root,
            backend=args.backend,
            timeout_seconds=args.timeout,
            docker_image=args.docker_image,
        )
        if args.write_report or args.report:
            write_student_report(root, assignment, report, args.report.resolve(strict=False) if args.report else None)
    except ValueError as error:
        print(f"Runner lab non disponibile:\n{error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
