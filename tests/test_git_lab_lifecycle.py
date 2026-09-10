from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts import git_lab_lifecycle


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_git(repo: Path, *args: str) -> None:
    env = os.environ.copy()
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_activity(root: Path) -> Path:
    activity_dir = root / "activities" / "git-canary"
    base = activity_dir / "fixture" / "base"
    working = activity_dir / "fixture" / "working"
    grading = activity_dir / "grading"
    student = activity_dir / "student"
    for path in (base, working, grading, student):
        path.mkdir(parents=True, exist_ok=True)
    (base / "programma.py").write_text('print("base")\n', encoding="utf-8")
    (base / "note.txt").write_text("base notes\n", encoding="utf-8")
    (working / "programma.py").write_text('print("changed")\n', encoding="utf-8")
    (working / "note.txt").write_text("changed notes\n", encoding="utf-8")
    (student / "GUIDA.md").write_text("Stage only programma.py\n", encoding="utf-8")
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
                "note.txt": sha256("changed notes\n"),
            },
            "index_files": {
                "programma.py": sha256('print("changed")\n'),
                "note.txt": sha256("base notes\n"),
            },
        },
    }
    (grading / "expectations.json").write_text(json.dumps(spec), encoding="utf-8")
    activity = {
        "schema_version": "1.0",
        "id": "git-canary",
        "title": "Selective stage",
        "titolo": "Selective stage",
        "kind": "laboratorio",
        "tipo": "laboratorio",
        "difficulty": "B",
        "difficolta": "B",
        "language": "git",
        "linguaggio": "git",
        "source_name": "repository",
        "instructions": "Stage only programma.py",
        "consegna": "Stage only programma.py",
        "topics": ["git-status", "staging"],
        "argomenti": ["git-status", "staging"],
        "student_support_mode": "feedback-tecnico",
        "grading_policy": {"compila": False, "test": True, "sandbox": True, "ai_feedback": False},
        "correzione": {"compila": False, "test": True, "sandbox": True, "ai_feedback": False},
        "metriche": {
            "tempo_stimato_minuti": 20,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": False,
        },
        "assets": [
            {
                "type": "fixture",
                "path": "student/GUIDA.md",
                "target_path": "GUIDA.md",
                "visibility": "student",
                "description": "Student guide",
            }
        ],
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


def assignment_from_result(root: Path, result: dict, activity_path: Path) -> dict:
    assignment_dir = Path(result["assignment_dir"])
    return {
        "assignment_id": "a1",
        "activity_id": "git-canary",
        "student_id": "s1",
        "activity": {"path": activity_path.relative_to(root).as_posix()},
        "workspace": {"path": assignment_dir.relative_to(root).as_posix()},
    }


def test_composed_assign_then_grade_passes_without_grading_leak(tmp_path: Path) -> None:
    activity = build_activity(tmp_path)
    student_repo_root = tmp_path / "students" / "s1"
    student_repo_root.mkdir(parents=True)

    result = git_lab_lifecycle.assign_git_lab(activity_path=activity, target=student_repo_root)
    repository = Path(result["repository"])

    assert (repository / ".git").is_dir()
    assert (Path(result["assignment_dir"]) / "GUIDA.md").is_file()
    assert not (repository / "grading").exists()
    assert not (repository / "expectations.json").exists()

    run_git(repository, "add", "programma.py")
    report = git_lab_lifecycle.run_git_lab(
        root=tmp_path,
        assignment=assignment_from_result(tmp_path, result, activity),
    )

    assert report["backend"] == "git-lab"
    assert report["passed"] is True
    serialized = json.dumps(report)
    assert "working_files" not in serialized
    assert "index_files" not in serialized
    assert sha256('print("changed")\n') not in serialized


def test_second_assignment_does_not_destroy_existing_repository(tmp_path: Path) -> None:
    activity = build_activity(tmp_path)
    target = tmp_path / "students" / "s1"
    target.mkdir(parents=True)
    first = git_lab_lifecycle.assign_git_lab(activity_path=activity, target=target)
    repository = Path(first["repository"])
    (repository / "student-note.txt").write_text("keep me\n", encoding="utf-8")

    with pytest.raises(ValueError, match="già esistente"):
        git_lab_lifecycle.assign_git_lab(activity_path=activity, target=target)

    assert (repository / "student-note.txt").read_text(encoding="utf-8") == "keep me\n"
