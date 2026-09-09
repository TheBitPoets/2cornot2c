from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import grade_activity
from scripts import python_object_profile as p3
from scripts import validate_activity
from scripts.thebitlab_sandbox_boundary import docker_boundary_command


DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_DOCKER_IMAGE = grade_activity.DEFAULT_DOCKER_IMAGE


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root deve essere un oggetto")
    return value


def p3_docker_command(
    *,
    image: str,
    workspace: Path,
    source: Path,
    cidfile: Path,
    container_name: str,
) -> list[str]:
    command = docker_boundary_command(
        image=image,
        workspace=workspace,
        cidfile=cidfile,
        container_name=container_name,
    )
    image_ref = command.pop()
    command.extend(["--entrypoint", "python3", image_ref])
    command.extend(
        [
            "/opt/thebitlab/python_object_worker.py",
            "--source",
            grade_activity.path_inside_workspace(source, workspace, "source"),
        ]
    )
    return command


def timeout_worker_result() -> dict[str, Any]:
    return {
        "schema_version": p3.WORKER_SCHEMA,
        "status": "timeout",
        "stdout": "",
        "stderr": "",
        "steps": [],
    }


def run_object_test_in_docker(
    *,
    image: str,
    workspace: Path,
    source: Path,
    teacher_test: dict[str, Any],
    timeout_seconds: int,
    temp_root: Path,
    test_index: int,
) -> dict[str, Any]:
    """Run one P3 scenario in a fresh hardened container."""
    cidfile = temp_root / f"p3-container-{test_index}.cid"
    container_name = f"thebitlab-p3-{uuid.uuid4().hex}"
    command = p3_docker_command(
        image=image,
        workspace=workspace,
        source=source,
        cidfile=cidfile,
        container_name=container_name,
    )
    request = p3.worker_request(teacher_test)
    try:
        try:
            completed = grade_activity.run_bounded_process(
                command,
                input_text=json.dumps(request, ensure_ascii=False, allow_nan=False),
                timeout=timeout_seconds
                + grade_activity.DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return timeout_worker_result()
        if completed.returncode != 0:
            raise ValueError(
                f"P3 worker terminato con errore infrastrutturale: exit={completed.returncode}"
            )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise ValueError("P3 worker non ha prodotto JSON valido") from error
        return p3.validate_worker_result(result)
    finally:
        grade_activity.remove_docker_container(cidfile, container_name)


def grade_in_docker(
    *,
    activity_path: Path,
    source_path: Path,
    image: str = DEFAULT_DOCKER_IMAGE,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    activity_root: Path | None = None,
    source_root: Path | None = None,
) -> dict[str, Any]:
    """Grade Python object behavior with one isolated container per scenario."""
    resolved_activity_root = (activity_root or activity_path.parent).resolve(strict=True)
    resolved_source_root = (source_root or source_path.parent).resolve(strict=True)
    safe_activity = grade_activity.confined_regular_input(
        activity_path,
        resolved_activity_root,
        "activity",
    )
    safe_source = grade_activity.confined_regular_input(
        source_path,
        resolved_source_root,
        "source",
    )
    activity = load_object(safe_activity)
    errors = validate_activity.validate_activity(activity, str(safe_activity))
    if errors:
        raise ValueError("Activity P3 non valida: " + "; ".join(errors))
    language = str(activity.get("language") or activity.get("linguaggio") or "python").lower()
    if language not in {"python", "py"}:
        raise ValueError("P3 supporta solo Activity Python")

    # Keep the teacher contract in its canonical raw Activity form. The worker
    # request builder and host-side comparator each validate/normalize that raw
    # scenario at their own trust boundary. Replacing it here with the normalized
    # representation would make those boundaries parse an internal shape twice.
    teacher_tests = activity.get("object_tests")
    p3.validate_object_tests(teacher_tests)
    if not isinstance(teacher_tests, list):
        raise ValueError("Activity P3 senza object_tests validi")

    with tempfile.TemporaryDirectory(prefix="thebitlab-p3-") as raw_temp:
        temp_root = Path(raw_temp)
        workspace, source = grade_activity.prepare_docker_workspace(
            safe_activity,
            safe_source,
            temp_root,
            activity_root=resolved_activity_root,
            source_root=resolved_source_root,
        )
        tests: list[dict[str, Any]] = []
        for index, teacher_test in enumerate(teacher_tests):
            worker_result = run_object_test_in_docker(
                image=image,
                workspace=workspace,
                source=source,
                teacher_test=teacher_test,
                timeout_seconds=timeout_seconds,
                temp_root=temp_root,
                test_index=index,
            )
            tests.append(p3.compare_worker_result(teacher_test, worker_result))

    passed = all(test["passed"] for test in tests)
    return {
        "passed": passed,
        "status": "passed" if passed else "failed",
        "activity_id": activity.get("id"),
        "language": "python",
        "profile": p3.PROFILE_ID,
        "source": str(source_path),
        "tests": tests,
        "summary": {
            "passed": sum(1 for test in tests if test["passed"]),
            "total": len(tests),
        },
    }


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("deve essere un intero") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("deve essere positivo")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grade Python object-behavior Activity in Docker"
    )
    parser.add_argument("--activity", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--activity-root", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument("--timeout", type=positive_int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = grade_in_docker(
            activity_path=args.activity,
            source_path=args.source,
            image=args.docker_image,
            timeout_seconds=args.timeout,
            activity_root=args.activity_root,
            source_root=args.source_root,
        )
    except subprocess.TimeoutExpired as error:
        print(f"P3 Docker grading interrotto dopo {error.timeout} secondi")
        return 2
    except FileNotFoundError:
        print("Docker non trovato. Installa Docker per il grading P3 autorevole.")
        return 2
    except (OSError, ValueError, grade_activity.DockerCleanupError) as error:
        print(f"P3 Docker grading non avviato: {error}")
        return 2
    if args.report:
        grade_activity.write_report(report, args.report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
