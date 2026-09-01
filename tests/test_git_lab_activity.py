from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from scripts import git_lab_activity


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
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
    (grading / "expectations.json").write_text(
        json.dumps(expectations), encoding="utf-8"
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
                "expectations": {
                    "path": "grading/expectations.json",
                    "media_type": "application/json",
                },
                "submission": {"kind": "git-repository"},
            }
        },
    }
    activity_json = activity_dir / "activity.json"
    activity_json.write_text(json.dumps(activity), encoding="utf-8")
    return activity_json


def test_prepare_then_student_stage_then_grade_passes(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    repo = tmp_path / "student-repo"

    fixture_report = git_lab_activity.prepare_repository(activity_json, repo)

    evidence = fixture_report["repository"]
    assert evidence["repository"]["branch"] == "main"
    assert len(evidence["commits"]) == 1
    assert evidence["working_tree"]["staged"] == []
    assert evidence["working_tree"]["unstaged"] == ["note.txt", "programma.py"]
    assert (repo / "grading").exists() is False
    assert (repo / "expectations.json").exists() is False

    run(repo, "add", "programma.py")
    grade = git_lab_activity.grade_repository(activity_json, repo)

    assert grade["passed"] is True


def test_prepare_is_deterministic_at_semantic_level(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"

    one = git_lab_activity.prepare_repository(activity_json, first)["repository"]
    two = git_lab_activity.prepare_repository(activity_json, second)["repository"]

    assert one["repository"]["branch"] == two["repository"]["branch"] == "main"
    assert one["working_tree"] == two["working_tree"]
    assert one["commits"][0]["subject"] == two["commits"][0]["subject"] == "Fixture iniziale"
    assert one["commits"][0]["changed_paths"] == two["commits"][0]["changed_paths"]


def test_nonempty_destination_fails_closed(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    repo = tmp_path / "student-repo"
    repo.mkdir()
    (repo / "existing.txt").write_text("do not overwrite\n", encoding="utf-8")

    with pytest.raises(git_lab_activity.GitLabActivityError, match="vuota"):
        git_lab_activity.prepare_repository(activity_json, repo)

    assert (repo / "existing.txt").read_text(encoding="utf-8") == "do not overwrite\n"


def test_fixture_cannot_smuggle_dot_git(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    dot_git = activity_json.parent / "fixture" / "base" / ".git"
    dot_git.mkdir()
    (dot_git / "config").write_text("malicious\n", encoding="utf-8")

    with pytest.raises(git_lab_activity.GitLabActivityError, match=".git"):
        git_lab_activity.prepare_repository(activity_json, tmp_path / "repo")


@pytest.mark.skipif(os.name == "nt", reason="symlink creation may require privileges")
def test_fixture_symlink_is_rejected(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = activity_json.parent / "fixture" / "base" / "link.txt"
    link.symlink_to(outside)

    with pytest.raises(git_lab_activity.GitLabActivityError, match="symlink"):
        git_lab_activity.prepare_repository(activity_json, tmp_path / "repo")


def test_invalid_extension_or_expectation_path_fails(tmp_path: Path) -> None:
    activity_json = build_activity(tmp_path)
    activity = json.loads(activity_json.read_text(encoding="utf-8"))
    activity["extensions"]["thebitlab.git-lab"]["schema_version"] = "wrong"
    activity_json.write_text(json.dumps(activity), encoding="utf-8")

    with pytest.raises(git_lab_activity.GitLabActivityError, match="schema"):
        git_lab_activity.prepare_repository(activity_json, tmp_path / "repo")

    activity_json = build_activity(tmp_path / "second")
    activity = json.loads(activity_json.read_text(encoding="utf-8"))
    activity["extensions"]["thebitlab.git-lab"]["expectations"]["path"] = "../teacher/answer.json"
    activity_json.write_text(json.dumps(activity), encoding="utf-8")

    with pytest.raises(git_lab_activity.GitLabActivityError, match="sicuro"):
        git_lab_activity.load_expectations(activity_json)
