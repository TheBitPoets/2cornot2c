#!/usr/bin/env python3
"""Prepare a stable local demo root for the student lab flow."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import student_lab_demo_smoke


DEFAULT_DEMO_ROOT = PROJECT_ROOT / "tmp" / "student-lab-demo"


def reset_root(root: Path) -> None:
    """Remove an existing demo root after a minimal safety check."""

    resolved = root.resolve(strict=False)
    if resolved == resolved.parent or len(resolved.parts) < 3:
        raise ValueError(f"Root demo non sicura da resettare: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


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
    reset_root(root)
    summary = student_lab_demo_smoke.run_smoke(root)
    return {
        **summary,
        "reset": True,
        "commands": demo_commands(root),
    }


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
