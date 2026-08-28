from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import uuid
from typing import Any

from scripts import grade_activity
from scripts import python_function_profile as p2
from scripts import validate_activity
from scripts.thebitlab_sandbox_boundary import docker_boundary_command


DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_DOCKER_IMAGE = grade_activity.DEFAULT_DOCKER_IMAGE


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root deve essere un oggetto")
    return value


def p2_docker_command(
    *,
    image: str,
    workspace: Path,
    source: Path,
    timeout_seconds: int,
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
            "/opt/thebitlab/python_function_worker.py",
            "--source",
            grade_activity.path_inside_workspace(source, workspace, "source"),
        ]
    )
    return command


def run_function_test_in_docker(
    *,
    image: str,
    workspace: Path,
    source: Path,
    teacher_test: dict[str, Any],
    timeout_seconds: int,
    temp_root: Path,
    test_index: int,
) -> dict[str, Any]:
    cidfile = temp_root / f"p2-container-{test_index}.cid"
    container_name = f"thebitlab-p2-{uuid.uuid4().hex}"
    command = p2_docker_command(
        image=image,
        workspace=workspace,
        source=source,
        timeout_seconds=timeout_seconds,
        cidfile=cidfile,
        container_name=container_name,
    )
    request = p2.worker_request(teacher_test)
    try:
        try:
            completed = grade_activity.run_bounded_process(
                command,
                input_text=json.dumps(request, ensure_ascii=False, allow_nan=False),
                timeout=timeout_seconds + grade_activity.DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {
                "schema_version": p2.WORKER_SCHEMA,
                "status": "timeout",
                "stdout": "",
                "stderr": "",
            }
        if completed.returncode != 0:
            raise ValueError(
                f"P2 worker terminato con errore infrastrutturale: exit={completed.returncode}"
            )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise ValueError("P2 worker non ha prodotto JSON valido") from error
        return p2.validate_worker_result(result)
    finally:
        try:
            grade_activity.remove_docker_container(cidfile, container_name)
        except grade_activity.DockerCleanupError:
            raise


def grade_in_docker(
    *,
    activity_path: Path,
    source_path: Path,
    image: str,
    timeout_seconds: int,
    activity_root: Path | None = None,
    source_root: Path | None = None,
) -> dict[str, Any]:
    safe_activity = grade_activity.confined_regular_input(
        activity_path,
        activity_root or activity_path.parent,
        "activity",
    )
    safe_source = grade_activity.confined_regular_input(
        source_path,
        source_root or source_path.parent,
        "source",
    )
    activity = load_object(safe_activity)
    errors = validate_activity.validate_activity(activity, str(safe_activity))
    if errors:
        raise ValueError("Activity non valida: " + "; ".join(errors))
    if (activity.get("language") or activity.get("linguaggio")) not in {"python", "py", None}:
        raise ValueError("P2 supporta solo Activity Python")
    teacher_tests = p2.validate_function_tests(activity.get("function_tests"))

    with tempfile.TemporaryDirectory(prefix="thebitlab-p2-") as raw_temp:
        temp_root = Path(raw_temp)
        workspace, source = grade_activity.prepare_docker_workspace(
            safe_activity,
            safe_source,
            temp_root,
            activity_root=activity_root or safe_activity.parent,
            source_root=source_root or safe_source.parent,
        )
        tests: list[dict[str, Any]] = []
        for index, teacher_test in enumerate(teacher_tests):
            worker_result = run_function_test_in_docker(
                image=image,
                workspace=workspace,
                source=source,
                teacher_test=teacher_test,
                timeout_seconds=timeout_seconds,
                temp_root=temp_root,
                test_index=index,
            )
            tests.append(p2.compare_worker_result(teacher_test, worker_result))

    passed = all(test["passed"] for test in tests)
    return {
        "passed": passed,
        "status": "passed" if passed else "failed",
        "activity_id": activity.get("id"),
        "language": "python",
        "profile": p2.PROFILE_ID,
        "source": str(source_path),
        "tests": tests,
        "summary": {
            "passed": sum(1 for test in tests if test["passed"]),
            "total": len(tests),
        },
    }


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("deve essere positivo")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grade Python function-behavior Activity in Docker")
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
    except (OSError, ValueError, grade_activity.DockerCleanupError) as error:
        print(f"P2 Docker grading non avviato: {error}")
        return 2
    if args.report:
        grade_activity.write_report(report, args.report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
