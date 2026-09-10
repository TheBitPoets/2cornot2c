#!/usr/bin/env python3
"""Prepare and grade Activity 1.0 bundles using the TheBitLab Git Lab extension."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from typing import Any

from scripts import git_lab_validator


EXTENSION_KEY = "thebitlab.git-lab"
ACTIVITY_SCHEMA = "git_activity.v1"
MAX_FIXTURE_FILES = 128
MAX_FIXTURE_BYTES = 2 * 1024 * 1024
COMMAND_TIMEOUT_SECONDS = 5


class GitLabActivityError(ValueError):
    """The Activity Git Lab extension or fixture is invalid."""


def _safe_relative_path(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise GitLabActivityError(f"{field} deve essere un path relativo non vuoto")
    if "\\" in value or value.startswith("/") or ":" in value:
        raise GitLabActivityError(f"{field} non è un path portabile")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise GitLabActivityError(f"{field} non è un path relativo sicuro")
    return value


def load_activity(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GitLabActivityError("activity.json non leggibile/valido") from error
    if not isinstance(value, dict):
        raise GitLabActivityError("activity.json deve contenere un oggetto")
    return value


def validate_extension(activity: dict[str, Any]) -> dict[str, Any]:
    extensions = activity.get("extensions")
    if not isinstance(extensions, dict):
        raise GitLabActivityError("Activity senza extensions")
    extension = extensions.get(EXTENSION_KEY)
    if not isinstance(extension, dict):
        raise GitLabActivityError(f"Activity senza extensions.{EXTENSION_KEY}")
    if extension.get("schema_version") != ACTIVITY_SCHEMA:
        raise GitLabActivityError(f"Git Lab extension schema deve essere {ACTIVITY_SCHEMA}")

    fixture = extension.get("fixture")
    if not isinstance(fixture, dict):
        raise GitLabActivityError("Git Lab fixture deve essere un oggetto")
    _safe_relative_path(fixture.get("base_dir"), field="fixture.base_dir")
    _safe_relative_path(fixture.get("working_overlay_dir"), field="fixture.working_overlay_dir")
    branch = fixture.get("initial_branch")
    if not isinstance(branch, str) or not branch or len(branch) > 120 or any(
        char.isspace() for char in branch
    ):
        raise GitLabActivityError("fixture.initial_branch non valido")
    message = fixture.get("initial_commit_message")
    if not isinstance(message, str) or not message.strip() or len(message) > 240:
        raise GitLabActivityError("fixture.initial_commit_message non valido")

    expectations = extension.get("expectations")
    if not isinstance(expectations, dict):
        raise GitLabActivityError("Git Lab expectations deve essere un oggetto")
    _safe_relative_path(expectations.get("path"), field="expectations.path")
    if expectations.get("media_type") not in {None, "application/json"}:
        raise GitLabActivityError("expectations.media_type non supportato")

    submission = extension.get("submission")
    if not isinstance(submission, dict) or submission.get("kind") != "git-repository":
        raise GitLabActivityError("submission.kind deve essere git-repository")
    return extension


def _resolve_activity_path(activity_dir: Path, relative: str, *, expect_dir: bool) -> Path:
    root = activity_dir.resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise GitLabActivityError(f"asset fuori activity root o mancante: {relative}") from error
    if candidate.is_symlink() or resolved.is_symlink():
        raise GitLabActivityError(f"asset Git Lab non può essere symlink: {relative}")
    if expect_dir and not resolved.is_dir():
        raise GitLabActivityError(f"asset deve essere directory: {relative}")
    if not expect_dir and not resolved.is_file():
        raise GitLabActivityError(f"asset deve essere file: {relative}")
    return resolved


def _copy_fixture_tree(source: Path, destination: Path) -> None:
    file_count = 0
    total_bytes = 0
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source)
        if ".git" in relative.parts:
            raise GitLabActivityError("fixture non può contenere .git")
        if item.is_symlink():
            raise GitLabActivityError(f"fixture symlink non ammesso: {relative.as_posix()}")
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not item.is_file():
            raise GitLabActivityError(f"fixture contiene tipo file non supportato: {relative.as_posix()}")
        file_count += 1
        total_bytes += item.stat().st_size
        if file_count > MAX_FIXTURE_FILES or total_bytes > MAX_FIXTURE_BYTES:
            raise GitLabActivityError("fixture oltre i limiti G1")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)


def _git_env(hooks_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "TheBitLab Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@thebitlab.invalid",
            "GIT_COMMITTER_NAME": "TheBitLab Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@thebitlab.invalid",
            "GIT_CONFIG_COUNT": "3",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": str(hooks_dir),
            "GIT_CONFIG_KEY_1": "core.fsmonitor",
            "GIT_CONFIG_VALUE_1": "false",
            "GIT_CONFIG_KEY_2": "core.untrackedCache",
            "GIT_CONFIG_VALUE_2": "false",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    return env


def _run_git(repo: Path, hooks_dir: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "--no-pager", *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=_git_env(hooks_dir),
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitLabActivityError(f"Git fixture command non eseguibile: {' '.join(args)}") from error
    if result.returncode != 0:
        raise GitLabActivityError(
            f"git {' '.join(args)} fallito ({result.returncode}): {result.stderr.strip()[:500]}"
        )
    return result.stdout.strip()


def prepare_repository(activity_json: Path, destination: Path) -> dict[str, Any]:
    """Create a deterministic student Git repository from one Activity fixture."""
    activity_json = activity_json.resolve(strict=True)
    activity_dir = activity_json.parent
    activity = load_activity(activity_json)
    extension = validate_extension(activity)
    fixture = extension["fixture"]

    if destination.exists():
        if destination.is_symlink() or not destination.is_dir():
            raise GitLabActivityError("destination deve essere una directory reale")
        if any(destination.iterdir()):
            raise GitLabActivityError("destination Git Lab deve essere vuota")
    else:
        destination.mkdir(parents=True)
    destination = destination.resolve(strict=True)

    base_dir = _resolve_activity_path(activity_dir, fixture["base_dir"], expect_dir=True)
    overlay_dir = _resolve_activity_path(
        activity_dir, fixture["working_overlay_dir"], expect_dir=True
    )

    _copy_fixture_tree(base_dir, destination)

    with tempfile.TemporaryDirectory(prefix="thebitlab-git-hooks-") as hooks:
        hooks_dir = Path(hooks)
        _run_git(destination, hooks_dir, "init")
        _run_git(
            destination,
            hooks_dir,
            "symbolic-ref",
            "HEAD",
            f"refs/heads/{fixture['initial_branch']}",
        )
        _run_git(destination, hooks_dir, "add", "--all")
        _run_git(
            destination,
            hooks_dir,
            "commit",
            "-m",
            fixture["initial_commit_message"],
        )

    _copy_fixture_tree(overlay_dir, destination)
    report = git_lab_validator.inspect_repository(destination)
    return {
        "schema_version": "thebitlab.git-fixture-report.v1",
        "activity_id": activity.get("id"),
        "repository": report,
    }


def load_expectations(activity_json: Path) -> dict[str, Any]:
    activity_json = activity_json.resolve(strict=True)
    activity_dir = activity_json.parent
    activity = load_activity(activity_json)
    extension = validate_extension(activity)
    path = _resolve_activity_path(
        activity_dir, extension["expectations"]["path"], expect_dir=False
    )
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise GitLabActivityError("expectations JSON non valido") from error
    git_lab_validator.validate_spec(spec)
    return spec


def grade_repository(activity_json: Path, repository: Path) -> dict[str, Any]:
    spec = load_expectations(activity_json)
    return git_lab_validator.evaluate_repository(repository, spec)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare/grade a TheBitLab Git Lab Activity")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("activity_json", type=Path)
    prepare.add_argument("destination", type=Path)

    grade = sub.add_parser("grade")
    grade.add_argument("activity_json", type=Path)
    grade.add_argument("repository", type=Path)

    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare_repository(args.activity_json, args.destination)
    else:
        result = grade_repository(args.activity_json, args.repository)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.command == "grade" and not result["passed"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
