#!/usr/bin/env python3
"""Prepare a stable local demo root for the student lab flow."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import course_board_server, student_lab_demo_smoke


DEFAULT_DEMO_ROOT = PROJECT_ROOT / "tmp" / "student-lab-demo"


def ensure_demo_root_available(root: Path) -> course_board_server.DataRootProcessLock:
    """Acquire and return the lock that protects the complete demo reset."""

    lock = course_board_server.DataRootProcessLock(root)
    try:
        lock.acquire()
    except RuntimeError as error:
        raise RuntimeError(
            f"Root demo in uso da un server attivo: {root.resolve(strict=False)}. "
            "Ferma il server prima di rigenerare la demo."
        ) from error
    return lock


def remove_tree_with_retry(path: Path, *, attempts: int = 5) -> None:
    """Remove a directory tree, retrying transient Windows cleanup failures."""

    for attempt in range(attempts):
        if not path.exists():
            return
        try:
            shutil.rmtree(path)
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def remove_path_with_retry(path: Path, *, attempts: int = 5) -> None:
    """Remove one file, symlink or directory after transient Windows failures."""

    for attempt in range(attempts):
        if not path.exists() and not path.is_symlink():
            return
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.2 * (attempt + 1))


def cleanup_stale_trash(root: Path) -> None:
    """Best-effort cleanup for old demo roots already moved aside."""

    for candidate in root.parent.glob(f"{root.name}.delete-*"):
        try:
            remove_tree_with_retry(candidate)
        except OSError:
            continue


def reset_root(root: Path) -> None:
    """Clear a demo root while preserving its actively held legacy lock file."""

    resolved = root.resolve(strict=False)
    if resolved == resolved.parent or len(resolved.parts) < 3:
        raise ValueError(f"Root demo non sicura da resettare: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    cleanup_stale_trash(resolved)
    resolved.mkdir(parents=True, exist_ok=True)
    for candidate in resolved.iterdir():
        if candidate.name == ".thebitlab-server.lock":
            continue
        remove_path_with_retry(candidate)


def demo_commands(root: Path) -> dict[str, str]:
    """Return useful commands for inspecting the prepared demo root."""

    root_arg = str(root)
    return {
        "payload": f"python scripts/student_lab_service.py --root {root_arg} --student-id {student_lab_demo_smoke.STUDENT_ID}",
        "tui": f"python scripts/student_lab_cli.py --root {root_arg} --student-id {student_lab_demo_smoke.STUDENT_ID}",
        "runner": (
            "python scripts/student_lab_runner.py "
            f"--root {root_arg} "
            f"--student-id {student_lab_demo_smoke.STUDENT_ID} "
            f"--activity-id {student_lab_demo_smoke.ACTIVITY_ID} "
            "--write-report"
        ),
    }


def prepare_demo(root: Path) -> dict[str, Any]:
    """Create a stable, inspectable demo root and return its summary."""

    root = root.resolve(strict=False)
    lock = ensure_demo_root_available(root)
    try:
        reset_root(root)
        summary = student_lab_demo_smoke.run_smoke(root)
        return {
            **summary,
            "reset": True,
            "commands": demo_commands(root),
        }
    finally:
        lock.release()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Prepara una root demo stabile per il lab studente.")
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_DEMO_ROOT,
        help="Root demo da preparare. Default: tmp/student-lab-demo.",
    )
    return parser.parse_args()


def main() -> int:
    """Prepare the demo root and print a JSON summary."""

    args = parse_args()
    try:
        summary = prepare_demo(args.root)
    except Exception as error:  # noqa: BLE001
        print(f"Setup demo non riuscito: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
