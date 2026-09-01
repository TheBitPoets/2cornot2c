from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from scripts import git_lab_activity, git_lab_student


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(repo: Path, *args: str) -> None:
    env = os.environ.copy()
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_activity(root: Path) -> Path:
    activity_dir = root / "activities" / "git-canary"
    base = activity_dir / "fixture" / "base"
    working = activity_dir / "fixture" / "working"
    grading = activity_dir / "grading"
    base.mkdir(parents=True)
    working.mkdir(parents=True)
    grading.mkdir(parents=True)
    (base / "programma.py").write_text('print("base")\n', encoding="utf-8")
    (base / "note.txt").write_text("base\n", encoding="utf-8")
    (working / "programma.py").write_text('print("changed")\n', encoding="utf-8")
    (working / "note.txt").write_text("changed\n", encoding="utf-8")
    spec = {
        "schema_version": "thebitlab.git-lab.v1",
        "expectations": {
            "clean": False,
            "branch": "main",
            "commit_count": 1,
            "staged_paths": ["programma.py"],
            "unstaged_paths": ["note.txt"],
            "untracked_paths": [],
            "working_files": {
                "programma.py": sha256('print("changed")\n'),
                "note.txt": sha256("changed\n"),
            },
            "index_files": {
                "programma.py": sha256('print("changed")\n'),
                "note.txt": sha256("base\n"),
            },
        },
    }
    (grading / "expectations.json").write_text(json.dumps(spec), encoding="utf-8")
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


def assignment(root: Path, activity_path: Path) -> tuple[dict, Path]:
    workspace = root / "students" / "s1" / "assignments" / "git-canary"
    workspace.mkdir(parents=True)
    relative_activity = activity_path.relative_to(root).as_posix()
    relative_workspace = workspace.relative_to(root).as_posix()
    item = {
        "assignment_id": "a1",
        "activity_id": "git-canary",
        "student_id": "s1",
        "activity": {"path": relative_activity},
        "workspace": {"path": relative_workspace},
    }
    return item, workspace


def test_student_adapter_grades_prepared_repository_without_leaking_hashes(tmp_path: Path) -> None:
    activity_path = build_activity(tmp_path)
    item, workspace = assignment(tmp_path, activity_path)
    repo = workspace / git_lab_student.REPOSITORY_DIRNAME
    git_lab_activity.prepare_repository(activity_path, repo)
    run(repo, "add", "programma.py")

    report = git_lab_student.run_git_lab_assignment(item, root=tmp_path)

    assert report["backend"] == "git-lab"
    assert report["passed"] is True
    assert report["summary"]["passed"] == report["summary"]["total"]
    serialized = json.dumps(report)
    assert sha256('print("changed")\n') not in serialized
    assert "expected" not in serialized
    assert "index_files" not in serialized
    assert any("diff --staged" in test["message"] or test["passed"] for test in report["tests"])


def test_student_adapter_failure_is_actionable_not_teacher_revealing(tmp_path: Path) -> None:
    activity_path = build_activity(tmp_path)
    item, workspace = assignment(tmp_path, activity_path)
    repo = workspace / git_lab_student.REPOSITORY_DIRNAME
    git_lab_activity.prepare_repository(activity_path, repo)
    run(repo, "add", "note.txt")

    report = git_lab_student.run_git_lab_assignment(item, root=tmp_path)

    assert report["passed"] is False
    messages = " ".join(test["message"] for test in report["tests"] if not test["passed"])
    assert "index" in messages.lower() or "staged" in messages.lower()
    assert "sha" not in messages.lower()


def test_activity_detection_is_strict() -> None:
    assert git_lab_student.activity_uses_git_lab({}) is False
    assert git_lab_student.activity_uses_git_lab({"extensions": {"thebitlab.git-lab": {"schema_version": "wrong"}}}) is False
    assert git_lab_student.activity_uses_git_lab({"extensions": {"thebitlab.git-lab": {"schema_version": "git_activity.v1"}}}) is True
