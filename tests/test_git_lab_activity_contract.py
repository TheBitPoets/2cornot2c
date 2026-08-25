from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

import pytest

from scripts import git_lab_activity_contract as contract
from scripts import git_lab_validator as core


def git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
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


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "assignment"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    (repo / "programma.py").write_text("print('base')\n", encoding="utf-8")
    (repo / "note.txt").write_text("base notes\n", encoding="utf-8")
    git(repo, "add", "programma.py", "note.txt")
    git(repo, "commit", "-m", "Fixture iniziale")

    (repo / "programma.py").write_text("print('student change')\n", encoding="utf-8")
    (repo / "note.txt").write_text("working notes\n", encoding="utf-8")
    git(repo, "add", "programma.py")
    return repo


def activity_expectations() -> dict:
    return {
        "schema_version": "thebitlab.git-lab.v1",
        "expectations": {
            "clean": False,
            "branch": "main",
            "commit_count": 1,
            "staged_paths": ["programma.py"],
            "unstaged_paths": ["note.txt"],
            "untracked_paths": [],
            "working_files": {
                "programma.py": digest("print('student change')\n"),
                "note.txt": digest("working notes\n"),
            },
            "index_files": {
                "programma.py": digest("print('student change')\n"),
                "note.txt": digest("base notes\n"),
            },
        },
    }


def test_activity_contract_passes_selective_stage_fixture(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)

    evidence = contract.evaluate_activity_expectations(repo, activity_expectations())

    assert evidence["passed"] is True
    assert all(item["passed"] for item in evidence["checks"])
    assert evidence["state"]["staged"] == ["programma.py"]
    assert evidence["state"]["unstaged"] == ["note.txt"]


def test_activity_contract_detects_wrong_file_staged(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    git(repo, "add", "note.txt")

    evidence = contract.evaluate_activity_expectations(repo, activity_expectations())

    assert evidence["passed"] is False
    failures = {item["name"] for item in evidence["checks"] if not item["passed"]}
    assert "staged_paths" in failures
    assert "unstaged_paths" in failures
    assert "index_files.note.txt" in failures


def test_activity_contract_detects_working_content_tampering(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    (repo / "note.txt").write_text("different\n", encoding="utf-8")

    evidence = contract.evaluate_activity_expectations(repo, activity_expectations())

    assert evidence["passed"] is False
    failures = {item["name"] for item in evidence["checks"] if not item["passed"]}
    assert "working_files.note.txt" in failures


def test_contract_rejects_unknown_expectations_and_unsafe_paths() -> None:
    with pytest.raises(core.GitLabError, match="unknown Git Lab expectations"):
        contract.validate_expectation_document({
            "schema_version": "thebitlab.git-lab.v1",
            "expectations": {"run_this_command": "git reset --hard"},
        })

    with pytest.raises(core.GitLabError, match="unsafe repository path"):
        contract.validate_expectation_document({
            "schema_version": "thebitlab.git-lab.v1",
            "expectations": {"working_files": {"../secret": "0" * 64}},
        })


def test_contract_rejects_wrong_schema() -> None:
    with pytest.raises(core.GitLabError, match="schema_version"):
        contract.validate_expectation_document({"schema_version": "wrong", "expectations": {}})
