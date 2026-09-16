"""Student-lab adapter and safe feedback for TheBitLab Git Lab Activities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import git_lab_activity, student_lab_service


REPOSITORY_DIRNAME = "repository"


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def activity_uses_git_lab(activity: dict[str, Any]) -> bool:
    extensions = activity.get("extensions")
    if not isinstance(extensions, dict):
        return False
    extension = extensions.get(git_lab_activity.EXTENSION_KEY)
    return isinstance(extension, dict) and extension.get("schema_version") == git_lab_activity.ACTIVITY_SCHEMA


def assignment_activity_path(root: Path, assignment: dict[str, Any]) -> Path:
    summary = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    value = clean_text(summary.get("path"))
    if not value:
        raise ValueError("activity.path mancante nella consegna Git Lab.")
    path = student_lab_service.resolve_local_path(root, value)
    if not path.is_file():
        raise ValueError(f"Activity Git Lab non trovata: {value}")
    return path


def assignment_repository_path(root: Path, assignment: dict[str, Any]) -> Path:
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    value = clean_text(workspace.get("path"))
    if not value:
        raise ValueError("workspace.path mancante nella consegna Git Lab.")
    workspace_path = student_lab_service.resolve_local_path(root, value)
    repository = workspace_path / REPOSITORY_DIRNAME
    if repository.is_symlink() or not repository.is_dir():
        raise ValueError("Repository Git Lab non preparato nella workspace della consegna.")
    return repository


def _check_feedback(name: str, passed: bool) -> str:
    if name == "working_tree.clean":
        return (
            "Il working tree ha lo stato finale richiesto."
            if passed
            else "Controlla con git status se il working tree deve essere pulito o avere modifiche residue."
        )
    if name == "repository.branch":
        return (
            "Sei sul branch richiesto."
            if passed
            else "Controlla il branch corrente prima di consegnare."
        )
    if name == "history.commit_count":
        return (
            "La storia contiene il numero di commit richiesto."
            if passed
            else "La storia non ha ancora la decomposizione in commit richiesta: controlla git log."
        )
    if name == "working_tree.staged":
        return (
            "Nell'index ci sono i path richiesti."
            if passed
            else "Controlla con git status e git diff --staged quali path sono nell'index."
        )
    if name == "working_tree.unstaged":
        return (
            "Le modifiche non staged corrispondono alla consegna."
            if passed
            else "Controlla con git status e git diff quali modifiche devono restare nel working tree senza essere staged."
        )
    if name == "working_tree.untracked":
        return (
            "I file untracked corrispondono alla consegna."
            if passed
            else "Controlla i file untracked mostrati da git status prima di consegnare."
        )
    if name.startswith("working_tree.file:"):
        path = name.split(":", 1)[1]
        return (
            f"Il contenuto corrente di {path} è quello richiesto."
            if passed
            else f"Il contenuto corrente di {path} non corrisponde allo stato richiesto."
        )
    if name.startswith("index.file:"):
        path = name.split(":", 1)[1]
        return (
            f"Lo snapshot staged di {path} è corretto."
            if passed
            else f"Controlla con git diff --staged quale versione di {path} hai preparato nell'index."
        )
    if name.startswith("commit["):
        return (
            "Il commit controllato rispetta il requisito."
            if passed
            else "Controlla git log/git show e la struttura dei commit richiesta dalla consegna."
        )
    return (
        "Requisito Git verificato."
        if passed
        else "Un requisito Git della consegna non è ancora soddisfatto."
    )


def student_safe_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Remove hashes, exact expected state and teacher-only details."""
    checks = evidence.get("checks") if isinstance(evidence.get("checks"), list) else []
    public_checks: list[dict[str, Any]] = []
    for index, item in enumerate(checks, start=1):
        if not isinstance(item, dict):
            continue
        name = clean_text(item.get("name")) or f"check-{index}"
        passed = item.get("passed") is True
        public_checks.append(
            {
                "name": name,
                "passed": passed,
                "status": "passed" if passed else "failed",
                "message": _check_feedback(name, passed),
                "visibility": "student",
            }
        )

    state = evidence.get("evidence") if isinstance(evidence.get("evidence"), dict) else {}
    repository = state.get("repository") if isinstance(state.get("repository"), dict) else {}
    working_tree = state.get("working_tree") if isinstance(state.get("working_tree"), dict) else {}
    commits = state.get("commits") if isinstance(state.get("commits"), list) else []
    return {
        "passed": evidence.get("passed") is True,
        "checks": public_checks,
        "state_summary": {
            "branch": repository.get("branch"),
            "clean": working_tree.get("clean"),
            "commit_count": len(commits),
        },
    }


def run_git_lab_assignment(
    assignment: dict[str, Any],
    *,
    root: Path,
    timeout_seconds: int = 5,
    backend: str = "local",
) -> dict[str, Any]:
    """Grade the prepared Git Lab repository and return student_lab_run.v1."""
    del timeout_seconds  # Git Lab commands have their own bounded platform timeout.
    del backend
    activity_path = assignment_activity_path(root, assignment)
    activity = json.loads(activity_path.read_text(encoding="utf-8"))
    if not activity_uses_git_lab(activity):
        raise ValueError("Activity non dichiara extensions.thebitlab.git-lab.")
    repository = assignment_repository_path(root, assignment)
    evidence = git_lab_activity.grade_repository(activity_path, repository)
    public = student_safe_evidence(evidence)
    checks = public["checks"]
    passed_count = sum(1 for item in checks if item.get("passed") is True)
    return {
        "schema_version": "student_lab_run.v1",
        "backend": "git-lab",
        "assignment_id": clean_text(assignment.get("assignment_id")),
        "activity_id": clean_text(assignment.get("activity_id")),
        "student_id": clean_text(assignment.get("student_id")),
        "language": "git",
        "source": str(repository),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "passed": public["passed"],
        "status": "passed" if public["passed"] else "failed",
        "summary": {"passed": passed_count, "total": len(checks)},
        "tests": checks,
        "stdout": "",
        "stderr": "",
        "git": public["state_summary"],
    }
