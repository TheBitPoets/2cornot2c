from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS = 10
DEFAULT_DOCKER_IMAGE = "thebitlab-assignment-runner"
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

    return run_command_test_case(["node", str(source)], test_case, timeout_seconds=timeout_seconds)


def run_sql_test_case(source: Path, test_case: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    """Run one SQL script against an isolated in-memory SQLite database."""

    sql = source.read_text(encoding="utf-8") + "\n" + str(test_case.get("stdin", ""))
    return run_command_test_case(["sqlite3", ":memory:"], {**test_case, "stdin": sql}, timeout_seconds=timeout_seconds)


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
        return grade_node_activity(activity, source, timeout_seconds=timeout_seconds)

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


def grade_node_activity(activity: dict[str, Any], source: Path, *, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Execute and grade a Node.js source file using activity test cases."""

    return grade_script_activity(
        activity,
        source,
        language="javascript",
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


def docker_timeout_seconds(activity: dict[str, Any], timeout_seconds: int) -> int:
    """Return the outer Docker timeout for compile plus all declared test cases."""
    test_cases = activity.get("test_cases", [])
    test_count = len(test_cases) if isinstance(test_cases, list) else 0
    return ((test_count + 1) * timeout_seconds) + DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS


def path_inside_workspace(path: Path, workspace: Path, label: str) -> str:
    """Return a workspace-relative path or raise a teacher-friendly error."""
    try:
        # Docker runs a Linux container even when the teacher host is Windows.
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"{label} deve trovarsi dentro il workspace montato: {workspace}") from error


def prepare_docker_workspace(activity: Path, source: Path, root: Path) -> tuple[Path, Path, Path]:
    """Create a minimal Docker workspace with only grading inputs."""
    workspace = root / "workspace"
    scripts_dir = workspace / "scripts"
    activity_dir = workspace / "activity"
    source_dir = workspace / "source"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    activity_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    script_copy = scripts_dir / Path(__file__).name
    activity_copy = activity_dir / activity.name
    source_copy = source_dir / source.name

    shutil.copy2(Path(__file__).resolve(), script_copy)
    shutil.copy2(activity.resolve(), activity_copy)
    shutil.copy2(source.resolve(), source_copy)

    return workspace, activity_copy, source_copy


def docker_command(
    *,
    activity: Path,
    source: Path,
    language: str | None,
    timeout_seconds: int,
    image: str = DEFAULT_DOCKER_IMAGE,
    workspace: Path | None = None,
) -> list[str]:
    """Build the docker command used to run grading in a container."""
    workspace = (workspace or Path.cwd()).resolve()
    activity_path = activity.resolve()
    source_path = source.resolve()
    command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--user",
        "runner",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "128",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "-v",
        f"{workspace}:/workspace:ro",
        "--tmpfs",
        "/thebitlab-work:rw,exec,nosuid,nodev,mode=1777,size=64m",
        "-e",
        "TMPDIR=/thebitlab-work",
        "-w",
        "/workspace",
    ]
    command.extend(
        [
        image,
        "--activity",
        path_inside_workspace(activity_path, workspace, "activity"),
        "--source",
        path_inside_workspace(source_path, workspace, "source"),
        "--timeout",
        str(timeout_seconds),
        ]
    )
    if language:
        command.extend(["--language", language])
    return command


def run_docker_grading(args: argparse.Namespace) -> int:
    """Run grading through Docker using the same CLI inside the container."""
    with tempfile.TemporaryDirectory(prefix="thebitlab-docker-") as temp_dir:
        temp_root = Path(temp_dir)
        try:
            workspace, activity, source = prepare_docker_workspace(args.activity, args.source, temp_root)
            docker_timeout = docker_timeout_seconds(load_activity(activity), args.timeout)
            command = docker_command(
                activity=activity,
                source=source,
                language=args.language,
                timeout_seconds=args.timeout,
                image=args.docker_image,
                workspace=workspace,
            )
        except (OSError, ValueError) as error:
            print(f"Sandbox Docker non avviata: {error}")
            return 1

        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=docker_timeout, check=False)
        except subprocess.TimeoutExpired:
            print(f"Sandbox Docker interrotta dopo {docker_timeout} secondi.")
            return 1
        except FileNotFoundError:
            print("Docker non trovato. Installa Docker oppure esegui senza --docker.")
            return 1

        if args.report:
            try:
                report = json.loads(result.stdout)
            except json.JSONDecodeError:
                print("Sandbox Docker non ha prodotto un report JSON valido.")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return 1
            if not has_minimal_report_shape(report):
                print("Sandbox Docker non ha prodotto un report di grading valido.")
                if result.stderr:
                    print(result.stderr)
                return 1
            if result.returncode != 0 and report.get("passed") is True:
                print("Sandbox Docker ha prodotto un report incoerente con l'esito del container.")
                if result.stderr:
                    print(result.stderr)
                return 1
            write_report(report, args.report)
            if result.stderr:
                print(result.stderr)
        else:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
        return result.returncode


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
    parser = argparse.ArgumentParser(description="Corregge in modo deterministico una consegna TheBitLab.")
    parser.add_argument("--activity", type=Path, required=True, help="Scheda attivita JSON con test_cases.")
    parser.add_argument("--source", type=Path, required=True, help="File sorgente da correggere.")
    parser.add_argument("--language", choices=sorted(SUPPORTED_LANGUAGES), help="Linguaggio da usare, se diverso dalla scheda.")
    parser.add_argument("--report", type=Path, help="Percorso report JSON da scrivere.")
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout compilazione/esecuzione.")
    parser.add_argument("--docker", action="store_true", help="Esegue il grading dentro la sandbox Docker.")
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE, help="Immagine Docker da usare con --docker.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.docker:
        return run_docker_grading(args)

    activity = load_activity(args.activity)
    report = grade_activity(activity, args.source, timeout_seconds=args.timeout, language=args.language)

    if args.report:
        write_report(report, args.report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
