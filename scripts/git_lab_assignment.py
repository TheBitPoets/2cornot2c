"""Prepare safe assignment scaffolds and nested repositories for Git Lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts import create_submission_scaffold, git_lab_activity, git_lab_student


def repository_path(assignment_dir: Path) -> Path:
    """Return the fixed Git Lab repository location inside an assignment scaffold."""
    return assignment_dir / git_lab_student.REPOSITORY_DIRNAME


def git_assignment_readme(activity: dict[str, Any], identifier: str) -> str:
    """Return a repository-submission README without code-runner instructions."""
    normalized = create_submission_scaffold.normalize_activity(activity)
    title = str(normalized.get("title") or identifier)
    prompt = str(normalized.get("instructions") or "Segui le indicazioni del docente.")
    assets = create_submission_scaffold.student_assets(activity)
    asset_lines = [
        f"- `{str(asset.get('target_path', asset.get('path', ''))).strip()}`"
        for asset in assets
        if str(asset.get("target_path", asset.get("path", ""))).strip()
    ]
    files = "\n".join(asset_lines) if asset_lines else "- nessun file guida aggiuntivo"
    return (
        f"# {title}\n\n"
        f"Activity ID: `{identifier}`\n\n"
        "## Consegna\n\n"
        f"{prompt}\n\n"
        "## Workspace Git\n\n"
        "Lavora esclusivamente nella sottocartella `repository/`.\n\n"
        "Prima di agire, osserva sempre lo stato del repository. Il grading valuta "
        "lo stato e la storia Git risultanti, non una sequenza obbligatoria di comandi.\n\n"
        "## Materiale studente\n\n"
        f"{files}\n\n"
        "Le aspettative di grading, gli hash attesi e gli asset docente non sono presenti "
        "nel repository dello studente.\n"
    )


def create_assignment_scaffold(
    *,
    activity_path: Path,
    target_dir: Path,
    state_dir: Path | None = None,
) -> Path:
    """Create the outer Git Lab scaffold using shared safe scaffold primitives.

    Git is a repository submission kind, not a fake code language. Therefore this
    path deliberately skips code-language/source-name selection while reusing the
    shared Activity validation, asset redaction, confinement and atomic writes.
    """
    activity_path = activity_path.resolve(strict=True)
    activity = git_lab_activity.load_activity(activity_path)
    if not git_lab_student.activity_uses_git_lab(activity):
        raise git_lab_activity.GitLabActivityError("L'Activity non dichiara Git Lab.")
    identifier = create_submission_scaffold.activity_id(activity)
    create_submission_scaffold.validate_activity_contract_or_raise(activity, identifier)
    git_lab_activity.validate_extension(activity)
    asset_plan = create_submission_scaffold.student_asset_copy_plan(activity_path, activity)
    destination = create_submission_scaffold.scaffold_dir(target_dir, identifier)
    create_submission_scaffold.prepare_scaffold_destination(target_dir, destination)
    if any(destination.iterdir()):
        raise git_lab_activity.GitLabActivityError(
            "Consegna Git Lab già esistente; reset/reprepare deve essere esplicito."
        )

    current_targets = {target_rel for _, target_rel in asset_plan}
    for target_rel in current_targets:
        if create_submission_scaffold.is_reserved_scaffold_target(target_rel):
            raise git_lab_activity.GitLabActivityError(
                f"Target asset sovrapposto a file riservato: {target_rel}"
            )
        if create_submission_scaffold.portable_paths_overlap(
            target_rel, Path(git_lab_student.REPOSITORY_DIRNAME)
        ):
            raise git_lab_activity.GitLabActivityError(
                f"Target asset non può occupare il repository Git Lab: {target_rel}"
            )

    manifest_path = create_submission_scaffold.managed_assets_path(
        target_dir, identifier, state_dir
    )
    distributed = create_submission_scaffold.student_activity_payload(activity)
    create_submission_scaffold.atomic_write_text(
        destination,
        Path("activity.json"),
        json.dumps(distributed, ensure_ascii=False, indent=2) + "\n",
    )

    copied = create_submission_scaffold.copy_student_assets(
        destination=destination,
        asset_plan=asset_plan,
        managed_assets={},
        source_name=git_lab_student.REPOSITORY_DIRNAME,
        overwrite_source=False,
    )
    managed = {
        path.relative_to(destination): create_submission_scaffold.file_sha256(path)
        for path in copied
    }
    create_submission_scaffold.write_managed_assets(manifest_path, managed)
    create_submission_scaffold.atomic_write_text(
        destination,
        Path("README.md"),
        git_assignment_readme(activity, identifier),
    )
    return destination


def prepare_assignment_repository(activity_path: Path, assignment_dir: Path) -> dict[str, Any] | None:
    """Prepare repository/ for a Git Lab Activity; return None for other Activities."""
    activity = git_lab_activity.load_activity(activity_path)
    if not git_lab_student.activity_uses_git_lab(activity):
        return None
    if assignment_dir.is_symlink() or not assignment_dir.is_dir():
        raise git_lab_activity.GitLabActivityError(
            "assignment_dir deve essere una directory reale già creata dallo scaffold"
        )
    repository = repository_path(assignment_dir)
    return git_lab_activity.prepare_repository(activity_path, repository)


def create_git_lab_assignment(
    *,
    activity_path: Path,
    target_dir: Path,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    """Create outer scaffold plus the nested deterministic Git exercise repo."""
    assignment_dir = create_assignment_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        state_dir=state_dir,
    )
    fixture = prepare_assignment_repository(activity_path, assignment_dir)
    assert fixture is not None
    activity = git_lab_activity.load_activity(activity_path)
    return {
        "schema_version": "thebitlab.git-assignment-result.v1",
        "activity_id": create_submission_scaffold.activity_id(activity),
        "target": str(target_dir.resolve(strict=False)),
        "assignment_dir": str(assignment_dir),
        "repository": str(repository_path(assignment_dir)),
        "fixture": fixture,
    }
