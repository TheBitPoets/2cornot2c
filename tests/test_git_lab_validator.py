from __future__ import annotations

import hashlib
import os
from pathlib import Path
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


def write(repo: Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def init_fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "assignment"
    repo.mkdir()
    run(repo, "init")
    run(repo, "branch", "-M", "main")
    write(repo, "README.md", "# Git Lab\n")
    write(repo, "programma.py", 'print("v1")\n')
    write(repo, "note.txt", "iniziale\n")
    run(repo, "add", "README.md", "programma.py", "note.txt")
    run(repo, "commit", "-m", "fixture iniziale")
    return repo


def target_spec() -> dict:
    return {
        "schema_version": validator.SPEC_SCHEMA,
        "expectations": {
            "clean": True,
            "branch": "main",
            "commit_count": 3,
            "staged_paths": [],
            "unstaged_paths": [],
            "untracked_paths": [],
            "commits": [
                {
                    "position": 0,
                    "subject_contains": "note",
                    "changed_paths": ["note.txt"],
                    "files": {"note.txt": sha256("seconda versione\n")},
                },
                {
                    "position": 1,
                    "subject_contains": "programma",
                    "changed_paths": ["programma.py"],
                    "files": {"programma.py": sha256('print("v2")\n')},
                },
            ],
        },
    }


def create_correct_student_history(repo: Path) -> None:
    # The student may edit both files before staging. What matters is that the
    # two commits contain the requested independent changes.
    write(repo, "programma.py", 'print("v2")\n')
    write(repo, "note.txt", "seconda versione\n")

    run(repo, "add", "programma.py")
    run(repo, "commit", "-m", "Aggiorna programma")

    run(repo, "add", "note.txt")
    run(repo, "commit", "-m", "Aggiorna note")


def test_correct_two_commit_history_passes(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)
    create_correct_student_history(repo)

    result = validator.evaluate_repository(repo, target_spec())

    assert result["passed"] is True
    assert result["evidence"]["working_tree"]["clean"] is True
    assert result["evidence"]["repository"]["branch"] == "main"
    assert [commit["changed_paths"] for commit in result["evidence"]["commits"][:2]] == [
        ["note.txt"],
        ["programma.py"],
    ]


def test_one_big_commit_fails_even_if_final_files_are_correct(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)
    write(repo, "programma.py", 'print("v2")\n')
    write(repo, "note.txt", "seconda versione\n")
    run(repo, "add", "programma.py", "note.txt")
    run(repo, "commit", "-m", "Aggiorna tutto")

    result = validator.evaluate_repository(repo, target_spec())

    assert result["passed"] is False
    failures = {item["name"] for item in result["checks"] if not item["passed"]}
    assert "history.commit_count" in failures
    assert "commit[0].changed_paths" in failures


def test_dirty_or_staged_repository_is_reported(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)
    write(repo, "programma.py", 'print("working")\n')
    write(repo, "note.txt", "staged\n")
    write(repo, "nuovo.txt", "untracked\n")
    run(repo, "add", "note.txt")

    report = validator.inspect_repository(repo)

    assert report["working_tree"] == {
        "staged": ["note.txt"],
        "unstaged": ["programma.py"],
        "untracked": ["nuovo.txt"],
        "clean": False,
    }


def test_file_evidence_is_read_from_commit_not_current_worktree(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)
    create_correct_student_history(repo)
    # Change the working copy after commits; commit evidence must stay stable.
    write(repo, "note.txt", "working copy diversa\n")

    spec = target_spec()
    spec["expectations"]["clean"] = False
    spec["expectations"]["unstaged_paths"] = ["note.txt"]
    result = validator.evaluate_repository(repo, spec)

    note_check = next(item for item in result["checks"] if item["name"] == "commit[0].file:note.txt")
    assert note_check["passed"] is True


def test_exact_repo_root_is_required(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)
    nested = repo / "nested"
    nested.mkdir()

    with pytest.raises(validator.GitLabValidationError, match="esattamente la root"):
        validator.inspect_repository(nested)


def test_symlink_repository_root_is_rejected(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation may require elevated privileges on Windows")
    repo = init_fixture(tmp_path)
    link = tmp_path / "repo-link"
    link.symlink_to(repo, target_is_directory=True)

    with pytest.raises(validator.GitLabValidationError, match="symlink"):
        validator.inspect_repository(link)


def test_invalid_specs_fail_closed(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)

    with pytest.raises(validator.GitLabValidationError, match="schema_version"):
        validator.evaluate_repository(repo, {"schema_version": "wrong", "expectations": {"clean": True}})

    with pytest.raises(validator.GitLabValidationError, match="path"):
        validator.evaluate_repository(
            repo,
            {
                "schema_version": validator.SPEC_SCHEMA,
                "expectations": {"staged_paths": ["../teacher/solution.txt"]},
            },
        )


def test_detached_head_is_visible_in_normalized_report(tmp_path: Path) -> None:
    repo = init_fixture(tmp_path)
    head = run(repo, "rev-parse", "HEAD")
    run(repo, "checkout", "--detach", head)

    report = validator.inspect_repository(repo)

    assert report["repository"]["detached"] is True
    assert report["repository"]["branch"] is None


def test_empty_repository_is_supported_as_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    run(repo, "init")
    run(repo, "branch", "-M", "main")

    report = validator.inspect_repository(repo)

    assert report["repository"]["head"] is None
    assert report["commits"] == []
    assert report["working_tree"]["clean"] is True
