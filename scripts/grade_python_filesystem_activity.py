from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import grade_activity
from scripts import python_filesystem_profile as p4
from scripts import validate_activity
from scripts.thebitlab_sandbox_boundary import docker_boundary_command


DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_DOCKER_IMAGE = grade_activity.DEFAULT_DOCKER_IMAGE
P4_TMPFS_SPEC = "/thebitlab-work:rw,exec,nosuid,nodev,mode=1777,size=1m"


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root deve essere un oggetto")
    return value


def prepare_fixture_mounts(
    *,
    activity_root: Path,
    teacher_test: dict[str, Any],
    temp_root: Path,
) -> list[tuple[Path, str]]:
    """Copy declared teacher fixtures into bounded temporary read-only mount sources."""

    normalized = p4.validate_filesystem_test(teacher_test)
    fixture_root = temp_root / "fixture-mounts"
    fixture_root.mkdir(parents=True, exist_ok=True)
    mounts: list[tuple[Path, str]] = []
    total = 0
    for index, fixture in enumerate(normalized["fixtures"]):
        source = activity_root / fixture["source"]
        safe_source = grade_activity.confined_regular_input(
            source,
            activity_root,
            f"filesystem fixture {fixture['id']}",
        )
        size = safe_source.stat().st_size
        if size > p4.MAX_FIXTURE_FILE_BYTES:
            raise ValueError(
                f"Fixture {fixture['id']} supera {p4.MAX_FIXTURE_FILE_BYTES} byte"
            )
        total += size
        if total > p4.MAX_FIXTURE_TOTAL_BYTES:
            raise ValueError("Fixture P4 superano il limite totale")
        raw = safe_source.read_bytes()
        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ValueError(f"Fixture {fixture['id']} non e UTF-8 valida") from error
        copied = fixture_root / f"{index:02d}-{fixture['target']}"
        copied.write_bytes(raw)
        try:
            copied.chmod(0o444)
        except OSError:
            pass
        mounts.append((copied, fixture["target"]))
    return mounts


def p4_docker_command(
    *,
    image: str,
    workspace: Path,
    source: Path,
    fixture_mounts: list[tuple[Path, str]],
    cidfile: Path,
    container_name: str,
) -> list[str]:
    """Return the hardened P4 Docker command with read-only fixture mounts."""

    command = docker_boundary_command(
        image=image,
        workspace=workspace,
        cidfile=cidfile,
        container_name=container_name,
    )
    for index, item in enumerate(command):
        if isinstance(item, str) and item.startswith("/thebitlab-work:"):
            command[index] = P4_TMPFS_SPEC
    image_ref = command.pop()
    for host_path, target in fixture_mounts:
        host = str(host_path.resolve())
        if "," in host:
            raise ValueError("Fixture host path contiene una virgola non supportata da Docker --mount")
        command.extend(
            [
                "--mount",
                f"type=bind,src={host},dst=/thebitlab-work/{target},readonly",
            ]
        )
    command.extend(["--entrypoint", "python3", image_ref])
    command.extend(
        [
            "/opt/thebitlab/python_filesystem_worker.py",
            "--source",
            grade_activity.path_inside_workspace(source, workspace, "source"),
            "--workdir",
            "/thebitlab-work",
        ]
    )
    return command


def timeout_test_result(teacher_test: dict[str, Any]) -> dict[str, Any]:
    normalized = p4.validate_filesystem_test(teacher_test)
    return {
        "name": normalized.get("name", "filesystem"),
        "profile": p4.PROFILE_ID,
        "visibility": normalized.get("visibility", "teacher"),
        "passed": False,
        "status": "failed",
        "worker_status": "timeout",
        "checks": [],
        "stdout": "",
        "stderr": "",
        "exception": None,
    }


def run_filesystem_test_in_docker(
    *,
    image: str,
    activity_root: Path,
    activity_path: Path,
    source_path: Path,
    teacher_test: dict[str, Any],
    timeout_seconds: int,
    temp_root: Path,
    test_index: int,
) -> dict[str, Any]:
    """Run one P4 test in a fresh container and compare only on the trusted host."""

    test_root = temp_root / f"test-{test_index:02d}"
    test_root.mkdir(parents=True)
    workspace, source = grade_activity.prepare_docker_workspace(
        activity_path,
        source_path,
        test_root,
        activity_root=activity_root,
        source_root=source_path.parent,
    )
    fixture_mounts = prepare_fixture_mounts(
        activity_root=activity_root,
        teacher_test=teacher_test,
        temp_root=test_root,
    )
    cidfile = test_root / "container.cid"
    container_name = f"thebitlab-p4-{uuid.uuid4().hex}"
    command = p4_docker_command(
        image=image,
        workspace=workspace,
        source=source,
        fixture_mounts=fixture_mounts,
        cidfile=cidfile,
        container_name=container_name,
    )
    request = p4.worker_request(teacher_test)
    try:
        try:
            completed = grade_activity.run_bounded_process(
                command,
                input_text=json.dumps(request, ensure_ascii=False, allow_nan=False),
                timeout=timeout_seconds + grade_activity.DEFAULT_DOCKER_TIMEOUT_GRACE_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return timeout_test_result(teacher_test)
        if completed.returncode != 0:
            raise ValueError(
                f"P4 worker terminato con errore infrastrutturale: exit={completed.returncode}"
            )
        try:
            worker_result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise ValueError("P4 worker non ha prodotto JSON valido") from error
        validated = p4.validate_worker_result(worker_result)
        return p4.compare_worker_result(teacher_test, validated)
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
    """Grade a Python P4 Activity with clean filesystem state per test."""

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
        raise ValueError("Activity P4 non valida: " + "; ".join(errors))
    language = str(activity.get("language") or activity.get("linguaggio") or "python").lower()
    if language not in {"python", "py"}:
        raise ValueError("P4 supporta solo Activity Python")
    teacher_tests = p4.validate_filesystem_tests(activity.get("filesystem_tests"))

    with tempfile.TemporaryDirectory(prefix="thebitlab-p4-") as raw_temp:
        temp_root = Path(raw_temp)
        tests: list[dict[str, Any]] = []
        for index, teacher_test in enumerate(teacher_tests):
            tests.append(
                run_filesystem_test_in_docker(
                    image=image,
                    activity_root=resolved_activity_root,
                    activity_path=safe_activity,
                    source_path=safe_source,
                    teacher_test=teacher_test,
                    timeout_seconds=timeout_seconds,
                    temp_root=temp_root,
                    test_index=index,
                )
            )

    passed = all(test["passed"] for test in tests)
    return {
        "passed": passed,
        "status": "passed" if passed else "failed",
        "activity_id": activity.get("id"),
        "language": "python",
        "profile": p4.PROFILE_ID,
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
        raise argparse.ArgumentTypeError("deve essere intero") from error
    if number <= 0:
        raise argparse.ArgumentTypeError("deve essere positivo")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grade Python filesystem-behavior Activity in Docker")
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
        print(f"P4 Docker grading interrotto dopo {error.timeout} secondi")
        return 2
    except FileNotFoundError:
        print("Docker non trovato. Installa Docker per il grading P4 autorevole.")
        return 2
    except (OSError, ValueError, grade_activity.DockerCleanupError) as error:
        print(f"P4 Docker grading non avviato: {error}")
        return 2
    if args.report:
        grade_activity.write_report(report, args.report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
