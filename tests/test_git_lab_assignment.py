from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import git_lab_activity, git_lab_assignment


def build_git_activity(tmp_path: Path) -> Path:
    activity_dir = tmp_path / "activity"
    base = activity_dir / "fixture" / "base"
    overlay = activity_dir / "fixture" / "working"
    grading = activity_dir / "grading"
    base.mkdir(parents=True)
    overlay.mkdir(parents=True)
    grading.mkdir(parents=True)
    (base / "programma.py").write_text("print('base')\n", encoding="utf-8")
    (overlay / "programma.py").write_text("print('changed')\n", encoding="utf-8")
    (grading / "expectations.json").write_text(
        json.dumps({
            "schema_version": "thebitlab.git-lab.v1",
            "expectations": {"clean": False, "branch": "main", "commit_count": 1},
        }),
        encoding="utf-8",
    )
    activity = {
        "schema_version": "1.0",
        "id": "git-canary",
        "extensions": {
            "thebitlab.git-lab": {
                "schema_version": "git_activity.v1",
                "fixture": {
                    "base_dir": "fixture/base",
                    "working_overlay_dir": "fixture/working",
                    "initial_branch": "main",
                    "initial_commit_message": "Fixture iniziale",
                },
                "expectations": {"path": "grading/expectations.json", "media_type": "application/json"},
                "submission": {"kind": "git-repository"},
            }
        },
    }
    path = activity_dir / "activity.json"
    path.write_text(json.dumps(activity), encoding="utf-8")
    return path


def test_prepare_assignment_creates_fixed_nested_git_repository(tmp_path: Path) -> None:
    activity = build_git_activity(tmp_path)
    assignment_dir = tmp_path / "student" / "assignments" / "git-canary"
    assignment_dir.mkdir(parents=True)
    (assignment_dir / "GUIDA.md").write_text("student guide\n", encoding="utf-8")

    report = git_lab_assignment.prepare_assignment_repository(activity, assignment_dir)
    repo = git_lab_assignment.repository_path(assignment_dir)

    assert report is not None
    assert repo.is_dir()
    assert (repo / ".git").is_dir()
    assert (repo / "programma.py").read_text(encoding="utf-8") == "print('changed')\n"
    assert (assignment_dir / "GUIDA.md").read_text(encoding="utf-8") == "student guide\n"
    assert not (repo / "grading").exists()
    assert not (repo / "expectations.json").exists()


def test_non_git_activity_is_noop(tmp_path: Path) -> None:
    activity = tmp_path / "activity.json"
    activity.write_text(json.dumps({"schema_version": "1.0", "id": "plain"}), encoding="utf-8")
    assignment_dir = tmp_path / "assignment"
    assignment_dir.mkdir()

    result = git_lab_assignment.prepare_assignment_repository(activity, assignment_dir)

    assert result is None
    assert not git_lab_assignment.repository_path(assignment_dir).exists()


def test_existing_student_repository_fails_closed_without_reset(tmp_path: Path) -> None:
    activity = build_git_activity(tmp_path)
    assignment_dir = tmp_path / "assignment"
    assignment_dir.mkdir()
    repo = git_lab_assignment.repository_path(assignment_dir)
    repo.mkdir()
    (repo / "student-work.txt").write_text("do not delete\n", encoding="utf-8")

    with pytest.raises(git_lab_activity.GitLabActivityError, match="vuota"):
        git_lab_assignment.prepare_assignment_repository(activity, assignment_dir)

    assert (repo / "student-work.txt").read_text(encoding="utf-8") == "do not delete\n"


def test_assignment_dir_symlink_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "assignment"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    activity = build_git_activity(tmp_path / "source")

    with pytest.raises(git_lab_activity.GitLabActivityError, match="directory reale"):
        git_lab_assignment.prepare_assignment_repository(activity, link)
