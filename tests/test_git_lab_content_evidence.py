from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess

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


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fixture(tmp_path: Path) -> Path:
    repo = tmp_path / "assignment"
    repo.mkdir()
    run(repo, "init")
    run(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    (repo / "programma.py").write_text('print("versione iniziale")\n', encoding="utf-8")
    (repo / "note.txt").write_text("appunti iniziali\n", encoding="utf-8")
    run(repo, "add", "programma.py", "note.txt")
    run(repo, "commit", "-m", "fixture iniziale")

    (repo / "programma.py").write_text('print("versione laboratorio")\n', encoding="utf-8")
    (repo / "note.txt").write_text("appunti aggiornati\n", encoding="utf-8")
    return repo


def stage_spec() -> dict:
    return {
        "schema_version": validator.SPEC_SCHEMA,
        "expectations": {
            "clean": False,
            "branch": "main",
            "commit_count": 1,
            "staged_paths": ["programma.py"],
            "unstaged_paths": ["note.txt"],
            "untracked_paths": [],
            "working_files": {
                "programma.py": sha256('print("versione laboratorio")\n'),
                "note.txt": sha256("appunti aggiornati\n"),
            },
            "index_files": {
                "programma.py": sha256('print("versione laboratorio")\n'),
                "note.txt": sha256("appunti iniziali\n"),
            },
        },
    }


def test_selective_stage_checks_both_state_and_content(tmp_path: Path) -> None:
    repo = fixture(tmp_path)
    run(repo, "add", "programma.py")

    result = validator.evaluate_repository(repo, stage_spec())

    assert result["passed"] is True
    names = {check["name"] for check in result["checks"]}
    assert "working_tree.file:programma.py" in names
    assert "working_tree.file:note.txt" in names
    assert "index.file:programma.py" in names
    assert "index.file:note.txt" in names


def test_wrong_staged_content_fails_even_with_correct_path_state(tmp_path: Path) -> None:
    repo = fixture(tmp_path)
    run(repo, "add", "programma.py")
    # Modify programma.py again after staging. The status still contains the
    # requested staged path, but the working-tree content is now wrong.
    (repo / "programma.py").write_text('print("alterato dopo lo stage")\n', encoding="utf-8")

    result = validator.evaluate_repository(repo, stage_spec())

    assert result["passed"] is False
    failure_names = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "working_tree.file:programma.py" in failure_names


def test_staging_wrong_snapshot_fails_index_hash(tmp_path: Path) -> None:
    repo = fixture(tmp_path)
    # Stage a different snapshot, then restore the desired working-tree content.
    (repo / "programma.py").write_text('print("snapshot sbagliato")\n', encoding="utf-8")
    run(repo, "add", "programma.py")
    (repo / "programma.py").write_text('print("versione laboratorio")\n', encoding="utf-8")

    spec = stage_spec()
    # State now has both staged and unstaged changes on programma.py; ignore
    # the exact unstaged set here so the content-specific failure is visible.
    spec["expectations"].pop("unstaged_paths")
    result = validator.evaluate_repository(repo, spec)

    assert result["passed"] is False
    failure_names = {check["name"] for check in result["checks"] if not check["passed"]}
    assert "index.file:programma.py" in failure_names


def test_unrequested_index_file_can_be_checked_against_baseline(tmp_path: Path) -> None:
    repo = fixture(tmp_path)
    run(repo, "add", "programma.py")

    result = validator.evaluate_repository(repo, stage_spec())
    note_check = next(check for check in result["checks"] if check["name"] == "index.file:note.txt")

    assert note_check["passed"] is True
    assert note_check["actual"] == sha256("appunti iniziali\n")
