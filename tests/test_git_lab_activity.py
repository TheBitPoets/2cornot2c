from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts import git_lab_activity


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(repo: Path, *args: str) -> None:
    env = os.environ.copy()
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_activity(tmp_path: Path) -> Path:
    activity_dir = tmp_path / "activity"
    base = activity_dir / "fixture" / "base"
    working = activity_dir / "fixture" / "working"
    grading = activity_dir / "grading"
    base.mkdir(parents=True)
    working.mkdir(parents=True)
    grading.mkdir(parents=True)
    (base / "README.md").write_text("# fixture\n", encoding="utf-8")
    (base / "programma.py").write_text('print("versione iniziale")\n', encoding="utf-8")
    (base / "note.txt").write_text("appunti iniziali\n", encoding="utf-8")
    (working / "programma.py").write_text('print("versione laboratorio")\n', encoding="utf-8")
    (working / "note.txt").write_text("appunti aggiornati\n", encoding="utf-8")
    expectations = {
        "schema_version": "thebitlab.git-lab.v1",
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
    (grading / "expectations.json").write_text(json.dumps(expectations), encoding="utf-8")
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


def test_prepare_then_stage_then_grade(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    repo = tmp_path / "student-repo"
    report = git_lab_activity.prepare_repository(activity_json, repo)
    assert report["repository"]["commit_count"] == 1
    assert report["repository"]["staged"] == []
    assert report["repository"]["unstaged"] == ["note.txt", "programma.py"]
    assert not (repo / "grading").exists()
    run(repo, "add", "programma.py")
    evidence = git_lab_activity.grade_repository(activity_json, repo)
    assert evidence["passed"] is True


def test_prepare_fails_closed_on_nonempty_destination(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    repo = tmp_path / "student-repo"
    repo.mkdir()
    (repo / "keep.txt").write_text("keep\n", encoding="utf-8")
    with pytest.raises(git_lab_activity.GitLabActivityError, match="directory reale vuota"):
        git_lab_activity.prepare_repository(activity_json, repo)
    assert (repo / "keep.txt").read_text(encoding="utf-8") == "keep\n"


def test_fixture_cannot_smuggle_dot_git(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    bad = activity_json.parent / "fixture" / "base" / ".git"
    bad.mkdir()
    (bad / "config").write_text("bad\n", encoding="utf-8")
    with pytest.raises(git_lab_activity.GitLabActivityError, match=".git"):
        git_lab_activity.prepare_repository(activity_json, tmp_path / "repo")


def test_expectations_path_cannot_escape_activity(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    activity = json.loads(activity_json.read_text(encoding="utf-8"))
    activity["extensions"]["thebitlab.git-lab"]["expectations"]["path"] = "../teacher/answer.json"
    activity_json.write_text(json.dumps(activity), encoding="utf-8")
    with pytest.raises(git_lab_activity.GitLabActivityError, match="sicuro"):
        git_lab_activity.load_expectations(activity_json)
