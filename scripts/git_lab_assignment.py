"""Prepare Git Lab repository workspaces after normal Activity scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts import git_lab_activity, git_lab_student


def prepare_assignment_repository(activity_path: Path, assignment_dir: Path) -> dict[str, Any] | None:
    """Prepare repository/ for a Git Lab Activity; return None for other Activities."""
    activity = git_lab_activity.load_activity(activity_path)
    if not git_lab_student.activity_uses_git_lab(activity):
        return None
    if assignment_dir.is_symlink() or not assignment_dir.is_dir():
        raise git_lab_activity.GitLabActivityError("assignment_dir deve essere una directory reale già creata dallo scaffold")
    repository = assignment_dir / git_lab_student.REPOSITORY_DIRNAME
    return git_lab_activity.prepare_repository(activity_path, repository)


def repository_path(assignment_dir: Path) -> Path:
    """Return the fixed Git Lab repository location inside an assignment scaffold."""
    return assignment_dir / git_lab_student.REPOSITORY_DIRNAME
