from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess

import pytest

from scripts import git_lab_validator as validator


def run(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "TheBitLab Student",
            "GIT_AUTHOR_EMAIL": "student@example.invalid",
            "GIT_COMMITTER_NAME": "TheBitLab Student",
            "GIT_COMMITTER_EMAIL": "student@example.invalid",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        }
    )
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        timeout=5,
    )
    return result.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "assignment"
    repo.mkdir()
    run(repo, "init")
    run(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "file.txt").write_text("baseline\n", encoding="utf-8")
    run(repo, "add", "file.txt")
    run(repo, "commit", "-m", "fixture")
    return repo


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable fixture")
def test_student_controlled_fsmonitor_is_not_executed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    marker = tmp_path / "fsmonitor-ran"
    hook = tmp_path / "malicious-fsmonitor.sh"
    hook.write_text(
        "#!/bin/sh\n"
        f"printf ran > '{marker}'\n"
        "printf '0\\n'\n",
        encoding="utf-8",
    )
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    run(repo, "config", "core.fsmonitor", str(hook))

    report = validator.inspect_repository(repo)

    assert report["working_tree"]["clean"] is True
    assert marker.exists() is False


def test_validator_process_environment_disables_interactive_git() -> None:
    env = validator._git_environment()

    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_OPTIONAL_LOCKS"] == "0"
    assert env["GIT_CONFIG_KEY_0"] == "core.fsmonitor"
    assert env["GIT_CONFIG_VALUE_0"] == "false"


def test_repository_parent_is_not_accepted_as_assignment_repo(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    with pytest.raises(validator.GitLabValidationError):
        validator.inspect_repository(tmp_path)
