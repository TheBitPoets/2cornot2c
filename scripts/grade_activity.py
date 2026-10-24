"""Deterministically grade one activity using its locked language runner contract."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

try:
    from scripts.thebitlab_sandbox_boundary import docker_boundary_command
except ModuleNotFoundError:  # direct ``python scripts/grade_activity.py`` execution
    from thebitlab_sandbox_boundary import docker_boundary_command

DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_NODE_STARTUP_GRACE_SECONDS = 10
DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS = 10
DEFAULT_DOCKER_IMAGE = "thebitlab-assignment-runner"
MAX_DOCKER_OUTPUT_BYTES = 1024 * 1024
WINDOWS_CREATE_SUSPENDED = 0x00000004
DOCKER_WORKER_SCHEMA = "thebitlab.grading-worker.v1"
SUPPORTED_LANGUAGES = {
    "c": "implemented",
    "python": "implemented",
    "javascript": "implemented",
    "nodejs": "implemented",
    "html": "planned",
    "java": "planned",
    "sql": "implemented",
    "golang": "planned",
    "assembly": "planned",
    "cpp": "planned",
    "php": "planned",
}


class DockerCleanupError(ValueError):
    """Raised when a grading container cannot be confirmed absent."""


def load_activity(path: Path) -> dict[str, Any]:
    """Load an activity JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def compile_c_source(source: Path, output: Path, *, timeout_seconds: int) -> dict[str, Any]:
    """Compile a C source file with gcc and return a deterministic result."""
    command = ["gcc", str(source), "-o", str(output)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as error:
        return {
            "passed": False,
            "status": "compile-timeout",
            "command": command,
            "stdout": error.stdout or "",
            "stderr": error.stderr or "",
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "status": "compiler-not-found",
            "command": command,
            "stdout": "",
            "stderr": "gcc non trovato",
        }

    return {
        "passed": result.returncode == 0,
        "status": "compiled" if result.returncode == 0 else "compile-error",
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def normalize_output(value: str) -> str:
    """Normalize output for deterministic stdout comparisons."""
    return value.replace("\r\n", "\n").strip()


def run_test_case(binary: Path, test_case: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """Run a compiled binary against one test case."""
    stdin = str(test_case.get("stdin", ""))
    expected_stdout = str(test_case.get("expected_stdout", ""))
    name = str(test_case.get("name", "test"))

    try:
        result = subprocess.run(
            [str(binary)],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "name": name,
            "passed": False,
            "status": "timeout",
            "returncode": None,
            "stdin": stdin,
            "expected_stdout": expected_stdout,
            "stdout": error.stdout or "",
            "stderr": error.stderr or "",
        }
    except OSError as error:
        return {
            "name": name,
            "passed": False,
            "status": "execution-error",
            "returncode": None,
            "stdin": stdin,
            "expected_stdout": expected_stdout,
            "stdout": "",
            "stderr": str(error),
        }

    actual_stdout = result.stdout
    passed = result.returncode == 0 and normalize_output(actual_stdout) == normalize_output(expected_stdout)
    return {
        "name": name,
        "passed": passed,
        "status": "passed" if passed else "failed",
        "returncode": result.returncode,
        "stdin": stdin,
        "expected_stdout": expected_stdout,
        "stdout": actual_stdout,
        "stderr": result.stderr,
    }


def run_command_test_case(command: list[str], test_case: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """Run one command against a deterministic stdin/stdout case."""

    stdin = str(test_case.get("stdin", ""))
    expected_stdout = str(test_case.get("expected_stdout", ""))
    name = str(test_case.get("name", "test"))
    try:
        result = subprocess.run(
            command,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "name": name,
            "passed": False,
            "status": "timeout",
            "command": command,
            "returncode": None,
            "stdout": error.stdout or "",
            "stderr": error.stderr or "",
            "expected_stdout": expected_stdout,
        }
    except OSError as error:
        return {
            "name": name,
            "passed": False,
            "status": "execution-error",
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
            "expected_stdout": expected_stdout,
        }

    passed = result.returncode == 0 and normalize_output(result.stdout) == normalize_output(expected_stdout)
    return {
        "name": name,
        "passed": passed,
        "status": "passed" if passed else "failed",
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "expected_stdout": expected_stdout,
    }


def run_python_test_case(source: Path, test_case: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """Run one Python source file against a deterministic stdin/stdout case."""

    return run_command_test_case([sys.executable, str(source)], test_case, timeout_seconds=timeout_seconds)


def run_node_test_case(source: Path, test_case: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """Run one JavaScript source file through Node.js."""

    name = str(test_case.get("name", "test"))
    expected_stdout = str(test_case.get("expected_stdout", ""))
    startup_command = ["node", "--check", str(source)]
    try:
        subprocess.run(
            startup_command,
            capture_output=True,
            text=True,
            timeout=DEFAULT_NODE_STARTUP_GRACE_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "name": name,
            "passed": False,
            "status": "runtime-startup-timeout",
            "command": startup_command,
            "returncode": None,
            "stdout": error.stdout or "",
            "stderr": error.stderr or "",
            "expected_stdout": expected_stdout,
        }
    except OSError as error:
        return {
            "name": name,
            "passed": False,
            "status": "execution-error",
            "command": startup_command,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
            "expected_stdout": expected_stdout,
        }
    return run_command_test_case(
        ["node", str(source)],
        test_case,
        timeout_seconds=timeout_seconds,
    )


def sqlite_output_value(value: Any) -> str:
    """Serialize one SQLite value like the previous text-mode CLI runner."""

    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_sql_test_case(source: Path, test_case: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """Run one SQL script against an isolated in-memory SQLite database."""

    sql = source.read_text(encoding="utf-8") + "\n" + str(test_case.get("stdin", ""))
    expected_stdout = str(test_case.get("expected_stdout", ""))
    name = str(test_case.get("name", "test"))
    command = ["python-stdlib", "sqlite3", ":memory:"]
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    output_lines: list[str] = []

    def ensure_before_deadline() -> None:
        nonlocal timed_out
        if time.monotonic() >= deadline:
            timed_out = True
            raise TimeoutError

    def stop_after_deadline() -> int:
        nonlocal timed_out
        timed_out = time.monotonic() >= deadline
        return 1 if timed_out else 0

    try:
        with sqlite3.connect(":memory:") as connection:
            connection.set_progress_handler(stop_after_deadline, 1000)
            statement_buffer: list[str] = []
            for index, character in enumerate(sql):
                if index % 1024 == 0:
                    ensure_before_deadline()
                statement_buffer.append(character)
                if character != ";":
                    continue
                statement = "".join(statement_buffer)
                if not sqlite3.complete_statement(statement):
                    continue
                ensure_before_deadline()
                cursor = connection.execute(statement)
                if cursor.description:
                    output_lines.extend(
                        "|".join(sqlite_output_value(value) for value in row)
                        for row in cursor.fetchall()
                    )
                statement_buffer.clear()
            trailing_statement = "".join(statement_buffer)
            if trailing_statement.strip():
                ensure_before_deadline()
                cursor = connection.execute(trailing_statement)
                if cursor.description:
                    output_lines.extend(
                        "|".join(sqlite_output_value(value) for value in row)
                        for row in cursor.fetchall()
                    )
    except (sqlite3.Error, TimeoutError) as error:
        return {
            "name": name,
            "passed": False,
            "status": "timeout" if timed_out else "execution-error",
            "command": command,
            "returncode": None if timed_out else 1,
            "stdout": "\n".join(output_lines) + ("\n" if output_lines else ""),
            "stderr": f"Timeout dopo {timeout_seconds} secondi." if timed_out else str(error),
            "expected_stdout": expected_stdout,
        }

    actual_stdout = "\n".join(output_lines) + ("\n" if output_lines else "")
    passed = normalize_output(actual_stdout) == normalize_output(expected_stdout)
    return {
        "name": name,
        "passed": passed,
        "status": "passed" if passed else "failed",
        "command": command,
        "returncode": 0,
        "stdout": actual_stdout,
        "stderr": "",
        "expected_stdout": expected_stdout,
    }


def validate_test_cases(test_cases: Any) -> list[str]:
    """Validate minimal deterministic test case structure."""
    if not isinstance(test_cases, list) or not test_cases:
        return ["L'attivita deve contenere una lista non vuota test_cases."]

    errors: list[str] = []
    for index, test_case in enumerate(test_cases):
        prefix = f"test_cases[{index}]"
        if not isinstance(test_case, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        if "expected_stdout" not in test_case:
            errors.append(f"{prefix}.expected_stdout mancante")
        elif not isinstance(test_case["expected_stdout"], str):
            errors.append(f"{prefix}.expected_stdout deve essere una stringa")
        if "stdin" in test_case and not isinstance(test_case["stdin"], str):
            errors.append(f"{prefix}.stdin deve essere una stringa")
    return errors


def activity_language(activity: dict[str, Any], explicit_language: str | None = None) -> str:
    """Return the language requested by CLI or activity metadata."""
    return str(explicit_language or activity.get("linguaggio") or activity.get("language") or "c").strip().lower()


def unsupported_language_report(activity: dict[str, Any], source: Path, language: str) -> dict[str, Any]:
    """Return a deterministic report for planned but not implemented languages."""
    return {
        "passed": False,
        "status": "unsupported-language",
        "activity_id": activity.get("id"),
        "source": str(source),
        "language": language,
        "supported_languages": SUPPORTED_LANGUAGES,
        "error": f"Runner non ancora implementato per il linguaggio: {language}",
    }


def unknown_language_report(activity: dict[str, Any], source: Path, language: str) -> dict[str, Any]:
    """Return a deterministic report for languages outside the supported model."""
    return {
        "passed": False,
        "status": "unknown-language",
        "activity_id": activity.get("id"),
        "source": str(source),
        "language": language,
        "supported_languages": SUPPORTED_LANGUAGES,
        "error": f"Linguaggio non riconosciuto: {language}",
    }


def grade_activity(
    activity: dict[str, Any],
    source: Path,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    language: str | None = None,
) -> dict[str, Any]:
    """Grade a source file using the language runner requested by the activity."""
    selected_language = activity_language(activity, language)
    if selected_language not in SUPPORTED_LANGUAGES:
        return unknown_language_report(activity, source, selected_language)

    if SUPPORTED_LANGUAGES.get(selected_language) != "implemented":
        return unsupported_language_report(activity, source, selected_language)

    if selected_language == "c":
        return grade_c_activity(activity, source, timeout_seconds=timeout_seconds)

    if selected_language == "python":
        return grade_python_activity(activity, source, timeout_seconds=timeout_seconds)

    if selected_language in {"javascript", "nodejs"}:
        return grade_node_activity(
            activity,
            source,
            timeout_seconds=timeout_seconds,
            language=selected_language,
        )

    if selected_language == "sql":
        return grade_sql_activity(activity, source, timeout_seconds=timeout_seconds)

    return unsupported_language_report(activity, source, selected_language)


def grade_c_activity(activity: dict[str, Any], source: Path, *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Compile and grade a C source file using test cases from an activity."""
    if not source.exists():
        return {
            "passed": False,
            "status": "source-not-found",
            "activity_id": activity.get("id"),
            "language": "c",
            "source": str(source),
            "tests": [],
            "error": f"Sorgente non trovato: {source}",
        }

    test_cases = activity.get("test_cases", [])
    test_case_errors = validate_test_cases(test_cases)
    if test_case_errors:
        return {
            "passed": False,
            "status": "invalid-activity",
            "activity_id": activity.get("id"),
            "language": "c",
            "source": str(source),
            "tests": [],
            "errors": test_case_errors,
        }

    with tempfile.TemporaryDirectory() as temp_dir:
        suffix = ".exe" if os.name == "nt" else ""
        binary = Path(temp_dir) / f"submission{suffix}"
        compile_result = compile_c_source(source, binary, timeout_seconds=timeout_seconds)
        if not compile_result["passed"]:
            return {
                "passed": False,
                "status": compile_result["status"],
                "activity_id": activity.get("id"),
                "language": "c",
                "source": str(source),
                "compile": compile_result,
                "tests": [],
            }

        tests = [run_test_case(binary, test_case, timeout_seconds=timeout_seconds) for test_case in test_cases]
        for test, test_case in zip(tests, test_cases):
            test["visibility"] = str(test_case.get("visibility", "teacher"))
        passed = all(test["passed"] for test in tests)
        return {
            "passed": passed,
            "status": "passed" if passed else "failed",
            "activity_id": activity.get("id"),
            "language": "c",
            "source": str(source),
            "compile": compile_result,
            "tests": tests,
            "summary": {
                "passed": sum(1 for test in tests if test["passed"]),
                "total": len(tests),
            },
        }


def grade_script_activity(
    activity: dict[str, Any],
    source: Path,
    *,
    language: str,
    test_runner: Any,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Execute and grade a script source file using activity test cases."""

    if not source.exists():
        return {
            "passed": False,
            "status": "source-not-found",
            "activity_id": activity.get("id"),
            "language": language,
            "source": str(source),
            "tests": [],
            "error": f"Sorgente non trovato: {source}",
        }

    test_cases = activity.get("test_cases", [])
    test_case_errors = validate_test_cases(test_cases)
    if test_case_errors:
        return {
            "passed": False,
            "status": "invalid-activity",
            "activity_id": activity.get("id"),
            "language": language,
            "source": str(source),
            "tests": [],
            "errors": test_case_errors,
        }

    tests = [test_runner(source, test_case, timeout_seconds=timeout_seconds) for test_case in test_cases]
    for test, test_case in zip(tests, test_cases):
        test["visibility"] = str(test_case.get("visibility", "teacher"))
    passed = all(test["passed"] for test in tests)
    return {
        "passed": passed,
        "status": "passed" if passed else "failed",
        "activity_id": activity.get("id"),
        "language": language,
        "source": str(source),
        "tests": tests,
        "summary": {
            "passed": sum(1 for test in tests if test["passed"]),
            "total": len(tests),
        },
    }


def grade_python_activity(activity: dict[str, Any], source: Path, *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Execute and grade a Python source file using activity test cases."""

    return grade_script_activity(
        activity,
        source,
        language="python",
        test_runner=run_python_test_case,
        timeout_seconds=timeout_seconds,
    )


def grade_node_activity(
    activity: dict[str, Any],
    source: Path,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    language: str = "javascript",
) -> dict[str, Any]:
    """Execute and grade a Node.js source file using activity test cases."""

    return grade_script_activity(
        activity,
        source,
        language=language,
        test_runner=run_node_test_case,
        timeout_seconds=timeout_seconds,
    )


def grade_sql_activity(activity: dict[str, Any], source: Path, *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Execute and grade a SQL script in an isolated SQLite database."""

    return grade_script_activity(
        activity,
        source,
        language="sql",
        test_runner=run_sql_test_case,
        timeout_seconds=timeout_seconds,
    )


def write_report(report: dict[str, Any], path: Path) -> None:
    """Write a grading report as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def has_minimal_report_shape(value: Any) -> bool:
    """Return whether a value looks like a grading report."""
    return isinstance(value, dict) and isinstance(value.get("passed"), bool) and isinstance(value.get("status"), str)


def build_worker_request(
    activity: dict[str, Any],
    test_case: dict[str, Any],
    language: str | None = None,
) -> dict[str, Any]:
    """Build one untrusted worker request with only the current test input."""
    selected_language = activity_language(activity, language)
    return {
        "schema_version": DOCKER_WORKER_SCHEMA,
        "language": selected_language,
        "stdin": str(test_case.get("stdin", "")),
    }


def load_worker_request(stream: Any) -> dict[str, Any]:
    """Read and validate the restricted request accepted inside the container."""
    try:
        request = json.load(stream)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Richiesta worker non valida.") from error
    if not isinstance(request, dict) or request.get("schema_version") != DOCKER_WORKER_SCHEMA:
        raise ValueError("Schema richiesta worker non supportato.")
    allowed_keys = {"schema_version", "language", "stdin"}
    if set(request) - allowed_keys:
        raise ValueError("La richiesta worker contiene campi non consentiti.")
    language = request.get("language")
    if not isinstance(language, str) or language not in SUPPORTED_LANGUAGES:
        raise ValueError("Linguaggio worker non valido.")
    if not isinstance(request.get("stdin"), str):
        raise ValueError("Lo stdin del test worker deve essere una stringa.")
    return request


def worker_execution_report(request: dict[str, Any], source: Path, *, timeout_seconds: int) -> dict[str, Any]:
    """Execute tests without receiving or returning their expected output."""
    activity = {
        "language": request["language"],
        "test_cases": [{"name": "test", "stdin": request["stdin"], "expected_stdout": ""}],
    }
    report = grade_activity(
        activity,
        source,
        timeout_seconds=timeout_seconds,
        language=request["language"],
    )
    sanitized = dict(report)
    sanitized["worker_schema_version"] = DOCKER_WORKER_SCHEMA
    sanitized["tests"] = [
        {
            key: value
            for key, value in test.items()
            if key not in {"expected_stdout", "stdin", "passed"}
        }
        for test in report.get("tests", [])
        if isinstance(test, dict)
    ]
    sanitized.pop("summary", None)
    return sanitized


def finalize_worker_report(
    activity: dict[str, Any],
    worker_reports: list[dict[str, Any]],
    source: Path,
    *,
    language: str | None = None,
) -> dict[str, Any]:
    """Compare worker output with teacher-only expectations on the trusted host."""
    selected_language = activity_language(activity, language)
    expected_tests = activity.get("test_cases", [])
    if len(worker_reports) > len(expected_tests):
        raise ValueError("Il numero di report worker supera i test richiesti.")
    tests: list[dict[str, Any]] = []
    terminal_report: dict[str, Any] | None = None
    for index, worker_report in enumerate(worker_reports):
        if worker_report.get("worker_schema_version") != DOCKER_WORKER_SCHEMA:
            raise ValueError("Report worker con schema non supportato.")
        if worker_report.get("language") != selected_language:
            raise ValueError("Il linguaggio del report worker non corrisponde alla richiesta.")
        worker_tests = worker_report.get("tests")
        if not isinstance(worker_tests, list) or len(worker_tests) > 1:
            raise ValueError("Il report worker non contiene un singolo risultato valido.")
        if not worker_tests:
            terminal_report = worker_report
            break
        raw_test = worker_tests[0]
        if not isinstance(raw_test, dict):
            raise ValueError("Il report worker contiene un test non valido.")
        expected_test = expected_tests[index]
        actual_stdout = raw_test.get("stdout")
        returncode = raw_test.get("returncode")
        raw_status = raw_test.get("status")
        if not isinstance(actual_stdout, str) or not isinstance(raw_status, str):
            raise ValueError("Il report worker contiene campi test non validi.")
        execution_ok = returncode == 0 and raw_status not in {
            "timeout",
            "execution-error",
            "runtime-startup-timeout",
        }
        expected_stdout = str(expected_test["expected_stdout"])
        passed = execution_ok and normalize_output(actual_stdout) == normalize_output(expected_stdout)
        test = dict(raw_test)
        test.update(
            {
                "name": str(expected_test.get("name", "test")),
                "visibility": str(expected_test.get("visibility", "teacher")),
                "passed": passed,
                "status": "passed" if passed else ("failed" if execution_ok else raw_status),
                "stdin": str(expected_test.get("stdin", "")),
                "expected_stdout": expected_stdout,
            }
        )
        tests.append(test)

    if terminal_report is None and len(worker_reports) != len(expected_tests):
        raise ValueError("Il numero di report worker non corrisponde ai test richiesti.")
    template_report = terminal_report or (worker_reports[0] if worker_reports else {})
    report = {
        key: value
        for key, value in template_report.items()
        if key not in {"worker_schema_version", "tests", "summary", "passed", "status"}
    }
    report["activity_id"] = activity.get("id")
    report["language"] = selected_language
    report["source"] = str(source)
    report["tests"] = tests
    if tests:
        report["passed"] = all(test["passed"] for test in tests)
        report["status"] = "passed" if report["passed"] else "failed"
        report["summary"] = {
            "passed": sum(1 for test in tests if test["passed"]),
            "total": len(tests),
        }
    else:
        report["passed"] = False
        report["status"] = str(template_report.get("status", "worker-error"))
    return report


def docker_timeout_seconds(
    activity: dict[str, Any],
    timeout_seconds: int,
    language: str | None = None,
) -> int:
    """Return the outer Docker timeout for compile plus all declared test cases."""
    test_cases = activity.get("test_cases", [])
    test_count = len(test_cases) if isinstance(test_cases, list) else 0
    test_timeout = timeout_seconds
    if activity_language(activity, language) in {"javascript", "nodejs"}:
        test_timeout += DEFAULT_NODE_STARTUP_GRACE_SECONDS
    return (test_count * test_timeout) + timeout_seconds + DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS


def path_inside_workspace(path: Path, workspace: Path, label: str) -> str:
    """Return a workspace-relative path or raise a teacher-friendly error."""
    try:
        # Docker runs a Linux container even when the teacher host is Windows.
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"{label} deve trovarsi dentro il workspace montato: {workspace}") from error


def confined_regular_input(path: Path, root: Path, label: str) -> Path:
    """Resolve one input without following links outside its authorized root."""

    resolved_root = root.resolve(strict=True)
    lexical = Path(os.path.abspath(path))
    try:
        relative = lexical.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"{label} deve trovarsi dentro {resolved_root}.") from error
    candidate = resolved_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"{label} non puo essere un collegamento simbolico.")
    resolved = lexical.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ValueError(f"{label} deve trovarsi dentro {resolved_root}.") from error
    if not resolved.is_file():
        raise ValueError(f"{label} deve essere un file regolare.")
    return resolved


def prepare_docker_workspace(
    activity: Path,
    source: Path,
    root: Path,
    *,
    activity_root: Path | None = None,
    source_root: Path | None = None,
) -> tuple[Path, Path]:
    """Create a Docker workspace that excludes teacher-only grading data."""
    confined_regular_input(activity, activity_root or activity.parent, "activity")
    safe_source = confined_regular_input(source, source_root or source.parent, "source")
    workspace = root / "workspace"
    source_dir = workspace / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    source_copy = source_dir / source.name

    shutil.copy2(safe_source, source_copy)

    return workspace, source_copy


def docker_command(
    *,
    source: Path,
    timeout_seconds: int,
    image: str = DEFAULT_DOCKER_IMAGE,
    workspace: Path | None = None,
    cidfile: Path | None = None,
    container_name: str | None = None,
) -> list[str]:
    """Build the docker command used to run grading in a container."""
    workspace = (workspace or Path.cwd()).resolve()
    source_path = source.resolve()
    command = docker_boundary_command(
        image=image,
        workspace=workspace,
        cidfile=cidfile,
        container_name=container_name,
    )
    command.extend(
        [
        "--worker",
        "--source",
        path_inside_workspace(source_path, workspace, "source"),
        "--timeout",
        str(timeout_seconds),
        ]
    )
    return command


def remove_docker_container(cidfile: Path, container_name: str) -> None:
    """Force-remove a named container and confirm that the daemon released it."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", container_name):
        raise DockerCleanupError("Nome container Docker di cleanup non valido.")
    try:
        container_id = cidfile.read_text(encoding="ascii").strip()
    except OSError:
        container_id = ""
    if container_id and not re.fullmatch(r"[0-9a-fA-F]{12,64}", container_id):
        container_id = ""
    last_error = ""
    for attempt in range(2):
        try:
            remove_result = subprocess.run(
                ["docker", "rm", "-f", container_name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
            if remove_result.returncode != 0:
                last_error = f"docker rm ha restituito {remove_result.returncode}"
        except (OSError, subprocess.TimeoutExpired) as error:
            last_error = str(error)
        try:
            inspect_result = subprocess.run(
                ["docker", "inspect", container_name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            last_error = str(error)
        else:
            if inspect_result.returncode != 0:
                inspect_error = (inspect_result.stderr or "").strip()
                normalized_error = inspect_error.casefold()
                if (
                    "no such object" in normalized_error
                    or "no such container" in normalized_error
                ):
                    cidfile.unlink(missing_ok=True)
                    return
                last_error = (
                    f"docker inspect ha restituito {inspect_result.returncode}: "
                    f"{inspect_error or 'errore non specificato'}"
                )
                continue
            last_error = "docker inspect conferma che il container esiste ancora"
        if attempt == 0:
            time.sleep(0.1)
    cid_detail = f" CID: {container_id}." if container_id else ""
    raise DockerCleanupError(
        f"Container Docker non rimosso; esegui `docker rm -f {container_name}`."
        f"{cid_detail} "
        f"Dettaglio: {last_error or 'cleanup non riuscito'}."
    )


def run_bounded_process(
    command: list[str],
    *,
    input_text: str,
    timeout: float,
    max_output_bytes: int = MAX_DOCKER_OUTPUT_BYTES,
) -> subprocess.CompletedProcess[str]:
    """Run a process while bounding captured stdout and discarding stderr."""
    deadline = time.monotonic() + timeout
    popen_options: dict[str, Any] = {}
    if os.name == "nt":
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
        )
    else:
        popen_options["start_new_session"] = True
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        **popen_options,
    )
    windows_job: Any = None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class JobObjectBasicLimitInformation(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_ulonglong),
                ("WriteOperationCount", ctypes.c_ulonglong),
                ("OtherOperationCount", ctypes.c_ulonglong),
                ("ReadTransferCount", ctypes.c_ulonglong),
                ("WriteTransferCount", ctypes.c_ulonglong),
                ("OtherTransferCount", ctypes.c_ulonglong),
            ]

        class JobObjectExtendedLimitInformation(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JobObjectBasicLimitInformation),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        ntdll = ctypes.WinDLL("ntdll")
        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        ntdll.NtResumeProcess.restype = ctypes.c_long

        windows_job = kernel32.CreateJobObjectW(None, None)
        if not windows_job:
            process.kill()
            process.wait()
            raise ctypes.WinError(ctypes.get_last_error())
        job_limits = JobObjectExtendedLimitInformation()
        job_limits.BasicLimitInformation.LimitFlags = 0x00002000
        if not kernel32.SetInformationJobObject(
            windows_job,
            9,
            ctypes.byref(job_limits),
            ctypes.sizeof(job_limits),
        ) or not kernel32.AssignProcessToJobObject(
            windows_job,
            wintypes.HANDLE(int(process._handle)),
        ):
            error_code = ctypes.get_last_error()
            kernel32.CloseHandle(windows_job)
            windows_job = None
            process.kill()
            process.wait()
            raise ctypes.WinError(error_code)
        resume_status = ntdll.NtResumeProcess(wintypes.HANDLE(int(process._handle)))
        if resume_status != 0:
            kernel32.CloseHandle(windows_job)
            windows_job = None
            if process.poll() is None:
                process.kill()
                process.wait()
            raise OSError(
                f"Impossibile riprendere il processo Windows sospeso: "
                f"NTSTATUS 0x{resume_status & 0xFFFFFFFF:08X}."
            )
    output = bytearray()
    output_exceeded = threading.Event()

    def write_stdin() -> None:
        assert process.stdin is not None
        try:
            process.stdin.write(input_text.encode("utf-8"))
        except (BrokenPipeError, OSError, ValueError):
            pass
        finally:
            try:
                process.stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                pass

    def read_stdout() -> None:
        assert process.stdout is not None
        read_chunk = getattr(process.stdout, "read1", process.stdout.read)
        try:
            while chunk := read_chunk(65536):
                remaining = max_output_bytes + 1 - len(output)
                if remaining > 0:
                    output.extend(chunk[:remaining])
                if len(output) > max_output_bytes:
                    output_exceeded.set()
                    process.kill()
                    break
        except (OSError, ValueError):
            pass

    def terminate_process_group() -> None:
        nonlocal windows_job
        if os.name == "nt":
            if windows_job is not None:
                kernel32.CloseHandle(windows_job)
                windows_job = None
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def close_pipe(pipe: Any) -> None:
        try:
            raw_pipe = getattr(pipe, "raw", None)
            if raw_pipe is not None:
                raw_pipe.close()
            else:
                pipe.close()
        except (OSError, ValueError):
            pass

    writer = threading.Thread(target=write_stdin, daemon=True)
    reader = threading.Thread(target=read_stdout, daemon=True)
    writer.start()
    reader.start()
    try:
        try:
            returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as error:
            terminate_process_group()
            raise subprocess.TimeoutExpired(
                command,
                timeout,
                output=bytes(output),
            ) from error
        writer.join(timeout=max(0, deadline - time.monotonic()))
        reader.join(timeout=max(0, deadline - time.monotonic()))
        if writer.is_alive() or reader.is_alive():
            raise subprocess.TimeoutExpired(
                command,
                timeout,
                output=bytes(output),
            )
    finally:
        terminate_process_group()
        close_pipe(process.stdin)
        close_pipe(process.stdout)
        writer.join(timeout=0.2)
        reader.join(timeout=0.2)

    if output_exceeded.is_set():
        raise ValueError(
            f"Sandbox Docker ha superato il limite output di {max_output_bytes} byte."
        )
    return subprocess.CompletedProcess(
        command,
        returncode,
        bytes(output).decode("utf-8", errors="replace"),
        "",
    )


def grade_activity_in_docker(
    activity_path: Path,
    source_path: Path,
    *,
    timeout_seconds: int,
    language: str | None = None,
    image: str = DEFAULT_DOCKER_IMAGE,
    activity_root: Path | None = None,
    source_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Run isolated workers and compare their output on the trusted host."""
    with tempfile.TemporaryDirectory(prefix="thebitlab-docker-") as temp_dir:
        temp_root = Path(temp_dir)
        activity = load_activity(
            confined_regular_input(
                activity_path,
                activity_root or activity_path.parent,
                "activity",
            )
        )
        test_case_errors = validate_test_cases(activity.get("test_cases", []))
        if test_case_errors:
            raise ValueError("; ".join(test_case_errors))
        workspace, source = prepare_docker_workspace(
            activity_path,
            source_path,
            temp_root,
            activity_root=activity_root,
            source_root=source_root,
        )
        docker_timeout = docker_timeout_seconds(
            {"test_cases": [{}], "language": activity_language(activity, language)},
            timeout_seconds,
            language,
        )
        worker_reports: list[dict[str, Any]] = []
        for test_index, test_case in enumerate(activity["test_cases"]):
            cidfile = temp_root / f"container-{test_index}.cid"
            container_name = f"thebitlab-grade-{uuid.uuid4().hex}"
            command = docker_command(
                source=source,
                timeout_seconds=timeout_seconds,
                image=image,
                workspace=workspace,
                cidfile=cidfile,
                container_name=container_name,
            )
            worker_request = build_worker_request(activity, test_case, language)
            try:
                result = run_bounded_process(
                    command,
                    input_text=json.dumps(worker_request, ensure_ascii=False),
                    timeout=docker_timeout,
                )
            except FileNotFoundError:
                cidfile.unlink(missing_ok=True)
                raise
            except BaseException as grading_error:
                try:
                    remove_docker_container(cidfile, container_name)
                except DockerCleanupError as cleanup_error:
                    raise cleanup_error from grading_error
                raise
            else:
                remove_docker_container(cidfile, container_name)

            try:
                worker_report = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                raise ValueError("Sandbox Docker non ha prodotto un report JSON valido.") from error
            if not has_minimal_report_shape(worker_report):
                raise ValueError("Sandbox Docker non ha prodotto un report di grading valido.")
            if result.returncode != 0:
                raise ValueError("Sandbox Docker worker terminata con un errore infrastrutturale.")
            worker_reports.append(worker_report)
            if not worker_report.get("tests"):
                break
        report = finalize_worker_report(
            activity,
            worker_reports,
            source_path,
            language=language,
        )
        return report, ""


def run_docker_grading(args: argparse.Namespace) -> int:
    """Run authoritative grading through isolated Docker workers."""
    try:
        report, _worker_stderr = grade_activity_in_docker(
            args.activity,
            args.source,
            timeout_seconds=args.timeout,
            language=args.language,
            image=args.docker_image,
            activity_root=getattr(args, "activity_root", None),
            source_root=getattr(args, "source_root", None),
        )
    except subprocess.TimeoutExpired as error:
        print(f"Sandbox Docker interrotta dopo {error.timeout} secondi.")
        return 1
    except FileNotFoundError:
        print("Docker non trovato. Installa Docker oppure esegui senza --docker.")
        return 1
    except (OSError, ValueError) as error:
        print(f"Sandbox Docker non avviata: {error}")
        return 1

    report = with_report_metadata(
        report,
        assignment_id=getattr(args, "assignment_id", None),
        student_id=getattr(args, "student_id", None),
        commit=getattr(args, "commit", None),
        submitted_at=getattr(args, "submitted_at", None),
        source_repo_path=getattr(args, "source_repo_path", None),
        toolchain_version=getattr(args, "toolchain_version", None),
        toolchain_reference=getattr(args, "toolchain_reference", None),
    )
    if args.report:
        write_report(report, args.report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


def positive_int(value: str) -> int:
    """Parse a positive integer CLI argument."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("deve essere un numero intero") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("deve essere un numero positivo")
    return number


def with_report_metadata(
    report: dict[str, Any],
    *,
    assignment_id: str | None = None,
    student_id: str | None = None,
    commit: str | None = None,
    submitted_at: str | None = None,
    source_repo_path: str | None = None,
    toolchain_version: str | None = None,
    toolchain_reference: str | None = None,
) -> dict[str, Any]:
    """Return a report enriched with explicit remote-tracking identities."""

    enriched = dict(report)
    for key, value in (
        ("assignment_id", assignment_id),
        ("student_id", student_id),
        ("commit", commit),
        ("submitted_at", submitted_at),
        ("source", source_repo_path),
        ("toolchain_version", toolchain_version),
        ("toolchain_reference", toolchain_reference),
    ):
        clean = str(value or "").strip()
        if clean:
            enriched[key] = clean
    return enriched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corregge in modo deterministico una consegna TheBitLab.")
    parser.add_argument("--activity", type=Path, help="Scheda attivita JSON con test_cases.")
    parser.add_argument("--source", type=Path, required=True, help="File sorgente da correggere.")
    parser.add_argument("--language", choices=sorted(SUPPORTED_LANGUAGES), help="Linguaggio da usare, se diverso dalla scheda.")
    parser.add_argument("--report", type=Path, help="Percorso report JSON da scrivere.")
    parser.add_argument("--assignment-id", help="Identificativo assegnazione da includere nel report.")
    parser.add_argument("--student-id", help="Identificativo studente da includere nel report.")
    parser.add_argument("--commit", help="SHA del commit studente da includere nel report.")
    parser.add_argument("--submitted-at", help="Timestamp ISO-8601 di ricezione della consegna.")
    parser.add_argument("--source-repo-path", help="Path del sorgente nel repository studente.")
    parser.add_argument("--activity-root", type=Path, help="Root autorizzata per la activity.")
    parser.add_argument("--source-root", type=Path, help="Root autorizzata per il sorgente.")
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout compilazione/esecuzione.")
    parser.add_argument("--docker", action="store_true", help="Esegue il grading dentro la sandbox Docker.")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE, help="Immagine Docker da usare con --docker.")
    parser.add_argument("--toolchain-version", help="Versione della toolchain usata per il grading.")
    parser.add_argument("--toolchain-reference", help="Riferimento immutabile della toolchain usata per il grading.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if getattr(args, "worker", False):
        try:
            request = load_worker_request(sys.stdin)
            report = worker_execution_report(request, args.source, timeout_seconds=args.timeout)
        except (OSError, ValueError) as error:
            print(json.dumps({"passed": False, "status": "worker-error", "error": str(error)}))
            return 2
        print(json.dumps(report, ensure_ascii=False))
        return 0
    if args.activity is None:
        raise SystemExit("--activity e obbligatorio fuori dalla modalita worker.")
    if args.docker:
        return run_docker_grading(args)

    activity_path = (
        confined_regular_input(args.activity, args.activity_root, "activity")
        if args.activity_root
        else args.activity
    )
    source_path = (
        confined_regular_input(args.source, args.source_root, "source")
        if args.source_root
        else args.source
    )
    activity = load_activity(activity_path)
    report = with_report_metadata(
        grade_activity(activity, source_path, timeout_seconds=args.timeout, language=args.language),
        assignment_id=args.assignment_id,
        student_id=args.student_id,
        commit=args.commit,
        submitted_at=args.submitted_at,
        source_repo_path=args.source_repo_path,
    )

    if args.report:
        write_report(report, args.report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
