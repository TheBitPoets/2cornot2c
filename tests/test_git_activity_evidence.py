from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import git_activity_evidence as evidence


GIT = shutil.which("git")
pytestmark = pytest.mark.skipif(GIT is None, reason="Git executable required")


def trusted_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Test Student",
            "GIT_AUTHOR_EMAIL": "student@example.invalid",
            "GIT_COMMITTER_NAME": "Test Student",
            "GIT_COMMITTER_EMAIL": "student@example.invalid",
        }
    )
    return subprocess.run(
        [GIT, *args],
        cwd=repo,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=10,
    )


def baseline(repo: Path) -> dict:
    return evidence.build_linear_scenario(
        repo,
        [
            {
                "message": "baseline",
                "files": {
                    "programma.py": 'print("ciao")\n',
                    ".gitignore": "*.tmp\n",
                },
            }
        ],
    )


def test_inspector_reports_g1_worktree_index_state(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    baseline(repo)

    (repo / "programma.py").write_text('print("ciao")\nprint("staged")\n', encoding="utf-8")
    trusted_git(repo, "add", "programma.py")
    (repo / "programma.py").write_text(
        'print("ciao")\nprint("staged")\nprint("working")\n', encoding="utf-8"
    )
    (repo / "note.txt").write_text("untracked\n", encoding="utf-8")
    (repo / "build.tmp").write_text("ignored\n", encoding="utf-8")

    state = evidence.inspect_repository(repo)

    assert state["schema_version"] == "thebitlab.git-evidence.v1"
    assert state["repository"]["current_branch"] == "main"
    assert state["repository"]["unborn"] is False
    assert state["repository"]["clean"] is False
    assert state["worktree_index"]["staged_paths"] == ["programma.py"]
    assert state["worktree_index"]["modified_paths"] == ["programma.py"]
    assert state["worktree_index"]["untracked_paths"] == ["note.txt"]
    assert state["worktree_index"]["ignored_paths"] == ["build.tmp"]
    assert set(state["worktree_index"]["tracked_paths"]) == {".gitignore", "programma.py"}


def test_builder_produces_deterministic_commit_objects(tmp_path: Path) -> None:
    commits = [
        {"message": "one", "files": {"a.txt": "A\n"}},
        {"message": "two", "files": {"a.txt": "AA\n", "b.txt": "B\n"}},
    ]
    first = evidence.build_linear_scenario(tmp_path / "one", commits)
    second = evidence.build_linear_scenario(tmp_path / "two", commits)

    assert first["repository"]["head_oid"] == second["repository"]["head_oid"]
    assert [(item["oid"], item["parents"], item["tree_oid"]) for item in first["commits"]] == [
        (item["oid"], item["parents"], item["tree_oid"]) for item in second["commits"]
    ]
    assert first["commits"][0]["changed_paths"] == ["a.txt", "b.txt"]
    assert first["commits"][1]["changed_paths"] == ["a.txt"]
    assert first["repository"]["clean"] is True


def test_unborn_repository_is_supported_without_inventing_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    trusted_git(repo, "init", "-b", "main")

    state = evidence.inspect_repository(repo)

    assert state["repository"] == {
        "bare": False,
        "current_branch": "main",
        "head_oid": None,
        "unborn": True,
        "clean": True,
    }
    assert state["commits"] == []
    assert state["head_tree"] == []


def test_local_dangerous_diff_and_fsmonitor_config_are_neutralized(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    baseline(repo)
    trusted_git(repo, "config", "diff.external", "definitely-do-not-execute")
    trusted_git(repo, "config", "core.fsmonitor", "definitely-do-not-execute")
    trusted_git(repo, "config", "diff.evil.command", "definitely-do-not-execute")
    (repo / ".gitattributes").write_text("*.txt diff=evil\n", encoding="utf-8")
    (repo / "new.txt").write_text("hello\n", encoding="utf-8")

    state = evidence.inspect_repository(repo)

    assert "new.txt" in state["worktree_index"]["untracked_paths"]
    assert state["repository"]["head_oid"]


def test_local_config_include_is_rejected_before_git_inspection(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    baseline(repo)
    config = repo / ".git" / "config"
    config.write_text(
        config.read_text(encoding="utf-8") + "\n[include]\n\tpath = /outside/thebitlab\n",
        encoding="utf-8",
    )

    with pytest.raises(evidence.GitEvidenceError, match="include/includeIf"):
        evidence.inspect_repository(repo)


def test_object_alternates_are_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    baseline(repo)
    alternates = repo / ".git" / "objects" / "info" / "alternates"
    alternates.write_text(str(tmp_path / "outside-objects") + "\n", encoding="utf-8")

    with pytest.raises(evidence.GitEvidenceError, match="external/common Git storage"):
        evidence.inspect_repository(repo)


def test_git_directory_redirect_file_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: ../outside.git\n", encoding="utf-8")

    with pytest.raises(evidence.GitEvidenceError, match="real directory"):
        evidence.inspect_repository(repo)


def test_git_directory_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    target = tmp_path / "outside-git"
    target.mkdir()
    repo = tmp_path / "repo"
    repo.mkdir()
    link = repo / ".git"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this runner")

    with pytest.raises(evidence.GitEvidenceError, match="real directory"):
        evidence.inspect_repository(repo)


def test_symlink_inside_git_directory_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    baseline(repo)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = repo / ".git" / "evil-link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this runner")

    with pytest.raises(evidence.GitEvidenceError, match="symlink inside .git"):
        evidence.inspect_repository(repo)


def test_hooks_are_not_executed_by_inspector(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    baseline(repo)
    marker = tmp_path / "hook-ran"
    hook = repo / ".git" / "hooks" / "pre-commit"
    if os.name == "nt":
        hook.write_text(f"@echo ran>{marker}\r\n", encoding="utf-8")
    else:
        hook.write_text(f"#!/bin/sh\necho ran > '{marker}'\n", encoding="utf-8")
        hook.chmod(0o755)

    evidence.inspect_repository(repo)

    assert not marker.exists()


def test_local_bare_remote_builder_needs_no_network(tmp_path: Path) -> None:
    remote = evidence.create_local_bare_remote(tmp_path / "remote.git")

    assert remote.is_dir()
    assert (remote / "HEAD").is_file()
    assert (remote / "objects").is_dir()
    head = (remote / "HEAD").read_text(encoding="utf-8").strip()
    assert head == "ref: refs/heads/main"


def test_workspace_escape_paths_are_rejected_by_scenario_builder(tmp_path: Path) -> None:
    with pytest.raises(evidence.GitEvidenceError, match="unsafe relative path"):
        evidence.build_linear_scenario(
            tmp_path / "repo",
            [{"message": "bad", "files": {"../escape.txt": "no"}}],
        )


def test_commit_graph_is_bounded(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    evidence.build_linear_scenario(
        repo,
        [
            {"message": "one", "files": {"a.txt": "1\n"}},
            {"message": "two", "files": {"a.txt": "2\n"}},
            {"message": "three", "files": {"a.txt": "3\n"}},
        ],
    )

    state = evidence.inspect_repository(repo, max_commits=2)

    assert len(state["commits"]) == 2
    assert state["truncation"]["commits"] is True
