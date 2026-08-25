from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts import git_lab_validator as lab


def git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Student",
        "GIT_AUTHOR_EMAIL": "student@example.invalid",
        "GIT_COMMITTER_NAME": "Student",
        "GIT_COMMITTER_EMAIL": "student@example.invalid",
        "LC_ALL": "C",
    })
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "assignment"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    (repo / "app.py").write_text("print('v1')\n", encoding="utf-8")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    git(repo, "add", "app.py", "README.md")
    git(repo, "commit", "-m", "Initial project")
    return repo


def test_inspect_repository_distinguishes_worktree_index_and_untracked(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    (repo / "README.md").write_text("# Demo\n\nUpdated\n", encoding="utf-8")
    (repo / "notes.txt").write_text("draft\n", encoding="utf-8")
    git(repo, "add", "README.md")

    state = lab.inspect_repository(repo)

    assert state["branch"] == "main"
    assert state["clean"] is False
    assert state["staged"] == ["README.md"]
    assert state["unstaged"] == ["app.py"]
    assert state["untracked"] == ["notes.txt"]
    assert state["commit_count"] == 1
    assert state["commits"][0]["subject"] == "Initial project"


def test_ignore_and_clean_state_are_observed(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (repo / "debug.log").write_text("ignore me\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "Ignore log files")

    state = lab.inspect_repository(repo)

    assert state["clean"] is True
    assert state["ignored"] == ["debug.log"]
    assert ".gitignore" in state["tracked"]
    assert state["commit_count"] == 2


def test_evidence_checks_history_and_file_content(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    first = git(repo, "rev-parse", "HEAD").strip()
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "Update application")

    evidence = lab.evaluate_expectations(
        repo,
        {
            "clean": True,
            "branch": "main",
            "commit_count": 2,
            "staged": [],
            "unstaged": [],
            "untracked": [],
            "files_at_revision": [
                {"revision": first, "path": "app.py", "content": "print('v1')\n"},
                {"revision": "HEAD", "path": "app.py", "content": "print('v2')\n"},
            ],
        },
    )

    assert evidence["passed"] is True
    assert all(check["passed"] for check in evidence["checks"])


def test_evidence_fails_without_prescribing_commands(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")

    evidence = lab.evaluate_expectations(repo, {"clean": True, "commit_count": 2})

    assert evidence["passed"] is False
    failures = {check["name"] for check in evidence["checks"] if not check["passed"]}
    assert failures == {"clean", "commit_count"}


def test_nested_parent_repository_is_rejected(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    nested = repo / "subdir"
    nested.mkdir()

    with pytest.raises(lab.GitLabError, match="repository toplevel"):
        lab.inspect_repository(nested)


def test_linked_worktree_is_rejected(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    worktree = tmp_path / "linked"
    git(repo, "worktree", "add", "-b", "other", str(worktree))

    with pytest.raises(lab.GitLabError, match="linked worktrees"):
        lab.inspect_repository(worktree)


def test_unsafe_revision_and_path_are_rejected(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    with pytest.raises(lab.GitLabError, match="unsupported revision"):
        lab.evaluate_expectations(
            repo,
            {"files_at_revision": [{"revision": "HEAD~1", "path": "app.py", "content": "x"}]},
        )
    with pytest.raises(lab.GitLabError, match="unsafe repository path"):
        lab.evaluate_expectations(
            repo,
            {"files_at_revision": [{"revision": "HEAD", "path": "../secret", "content": "x"}]},
        )


def test_cli_expectation_format_is_json_serializable(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    evidence = lab.evaluate_expectations(repo, {"clean": True, "commit_count": 1})
    json.dumps(evidence)
    assert evidence["schema_version"] == "thebitlab.git-evidence.v1"
