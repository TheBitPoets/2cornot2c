#!/usr/bin/env python3
"""Composable assignment/run lifecycle for TheBitLab Git Lab G1.

Git Lab uses a repository-submission scaffold rather than pretending Git is a
code language. Final Course Board / Student Lab routing can call these same
functions without duplicating Git-specific semantics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import git_lab_assignment, git_lab_student


def assign_git_lab(
    *,
    activity_path: Path,
    target: Path,
    thebitlab_ref: str = "main",
) -> dict[str, Any]:
    """Create the safe Git Lab scaffold and its nested repository."""
    del thebitlab_ref  # repository submissions do not expose code-runner workflow refs.
    return git_lab_assignment.create_git_lab_assignment(
        activity_path=activity_path,
        target_dir=target,
    )


def run_git_lab(
    *,
    root: Path,
    assignment: dict[str, Any],
) -> dict[str, Any]:
    """Grade one already-prepared Git Lab assignment using student-safe output."""
    return git_lab_student.run_git_lab_assignment(assignment, root=root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Assign or grade one TheBitLab Git Lab Activity")
    sub = parser.add_subparsers(dest="command", required=True)

    assign_cmd = sub.add_parser("assign")
    assign_cmd.add_argument("--activity", type=Path, required=True)
    assign_cmd.add_argument("--target", type=Path, required=True)
    assign_cmd.add_argument("--thebitlab-ref", default="main")

    grade_cmd = sub.add_parser("grade")
    grade_cmd.add_argument("--root", type=Path, required=True)
    grade_cmd.add_argument("--assignment-json", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "assign":
        payload = assign_git_lab(
            activity_path=args.activity,
            target=args.target,
            thebitlab_ref=args.thebitlab_ref,
        )
    else:
        assignment = json.loads(args.assignment_json.read_text(encoding="utf-8"))
        if not isinstance(assignment, dict):
            raise SystemExit("assignment JSON deve essere un oggetto")
        payload = run_git_lab(root=args.root, assignment=assignment)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("passed", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
