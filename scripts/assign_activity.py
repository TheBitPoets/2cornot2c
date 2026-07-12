from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts import create_submission_scaffold
from scripts.thebitlab_repository_providers import RepositoryProvider


@dataclass(frozen=True)
class AssignmentResult:
    """Result of assigning one activity to one target repository."""

    target: Path
    assignment_dir: Path


@dataclass(frozen=True)
class AssignmentPlan:
    """Preview of assigning one activity to a set of target repositories."""

    activity_id: str
    title: str
    language: str
    source_name: str
    student_assets: list[dict[str, Any]]
    teacher_assets: list[dict[str, Any]]
    targets: list[dict[str, Any]]
    blocked_targets: list[str]
    overwrite: bool

    @property
    def can_assign(self) -> bool:
        """Return whether the plan can be executed without force."""

        return self.overwrite or not self.blocked_targets

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable plan for CLI/API consumers."""

        return {
            "activity_id": self.activity_id,
            "title": self.title,
            "language": self.language,
            "source_name": self.source_name,
            "student_assets": self.student_assets,
            "teacher_assets": self.teacher_assets,
            "targets": self.targets,
            "blocked_targets": self.blocked_targets,
            "overwrite": self.overwrite,
            "can_assign": self.can_assign,
        }


def load_targets_file(path: Path) -> list[Path]:
    """Load target repository roots from a plain text file."""
    targets: list[Path] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if clean_line and not clean_line.startswith("#"):
            target = Path(clean_line)
            if not target.is_absolute():
                target = (path.parent / target).resolve(strict=False)
            targets.append(target)
    return targets


def collect_targets(targets: list[Path] | None = None, targets_file: Path | None = None) -> list[Path]:
    """Return the ordered target list provided directly or through a file."""
    collected = list(targets or [])
    if targets_file is not None:
        collected.extend(load_targets_file(targets_file))
    if not collected:
        raise ValueError("Indica almeno un repository studente con --target o --targets-file.")
    return collected


def collect_targets_from_provider(provider: RepositoryProvider, class_ref: str | None = None) -> list[Path]:
    """Return local target paths exposed by a repository provider."""

    repositories = provider.list_student_repositories(class_ref=class_ref)
    paths = []
    for repository in repositories:
        if repository.path is None:
            raise ValueError(f"Repository senza path locale: {repository.repo_ref}")
        paths.append(repository.path)
    if not paths:
        raise ValueError("Il provider non ha restituito repository studenti.")
    return paths


def assignment_asset_summary(activity: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return student-visible and teacher/grader assets for an activity preview."""

    student_assets = []
    teacher_assets = []
    assets = activity.get("assets")
    if not isinstance(assets, list):
        return student_assets, teacher_assets
    student_asset_ids = {id(asset) for asset in create_submission_scaffold.student_assets(activity)}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_type = str(asset.get("type", ""))
        path = str(asset.get("path", ""))
        target_path = str(asset.get("target_path", path))
        visibility = create_submission_scaffold.asset_visibility(asset)
        summary = {
            "type": asset_type,
            "path": path,
            "target_path": target_path,
            "visibility": visibility,
            "description": str(asset.get("description", "")),
        }
        if id(asset) in student_asset_ids:
            student_assets.append(summary)
        else:
            teacher_assets.append(summary)
    return student_assets, teacher_assets


def build_assignment_plan(
    *,
    activity_path: Path,
    targets: list[Path],
    source_name: str | None = None,
    language: str | None = None,
    thebitlab_ref: str = create_submission_scaffold.DEFAULT_THEBITLAB_REF,
    overwrite: bool = False,
) -> AssignmentPlan:
    """Validate an assignment request and return a write-free execution preview."""

    if not targets:
        raise ValueError("Indica almeno un repository studente.")
    activity = create_submission_scaffold.load_activity(activity_path)
    identifier = create_submission_scaffold.activity_id(activity)
    normalized_activity = create_submission_scaffold.validate_activity_contract_or_raise(activity, identifier)
    selected_language = create_submission_scaffold.language_for(normalized_activity, language)
    selected_source_name = create_submission_scaffold.validate_source_name(
        source_name
        if source_name is not None
        else create_submission_scaffold.default_source_name_for(selected_language)
    )
    create_submission_scaffold.validate_thebitlab_ref(thebitlab_ref)
    create_submission_scaffold.student_asset_copy_plan(activity_path, activity)
    blocked_targets = [
        str(target)
        for target in targets
        if create_submission_scaffold.scaffold_dir(target, identifier).exists()
        and any(create_submission_scaffold.scaffold_dir(target, identifier).iterdir())
    ]
    student_assets, teacher_assets = assignment_asset_summary(activity)
    return AssignmentPlan(
        activity_id=identifier,
        title=str(normalized_activity.get("title") or identifier),
        language=selected_language,
        source_name=selected_source_name,
        student_assets=student_assets,
        teacher_assets=teacher_assets,
        targets=[
            {
                "target": str(target),
                "assignment_dir": str(create_submission_scaffold.scaffold_dir(target, identifier)),
                "exists": str(target) in blocked_targets,
            }
            for target in targets
        ],
        blocked_targets=blocked_targets,
        overwrite=overwrite,
    )


def assign_activity_to_targets(
    *,
    activity_path: Path,
    targets: list[Path],
    source_name: str | None = None,
    language: str | None = None,
    thebitlab_ref: str = create_submission_scaffold.DEFAULT_THEBITLAB_REF,
    overwrite: bool = False,
    overwrite_source: bool = False,
) -> list[AssignmentResult]:
    """Create the activity scaffold in each target student repository."""
    plan = build_assignment_plan(
        activity_path=activity_path,
        targets=targets,
        source_name=source_name,
        language=language,
        thebitlab_ref=thebitlab_ref,
        overwrite=overwrite,
    )
    if not plan.can_assign:
        blocked = "\n".join(plan.blocked_targets)
        raise ValueError(f"Consegna gia esistente in questi repository:\n{blocked}\nUsa --force per aggiornare.")

    results: list[AssignmentResult] = []
    for target in targets:
        assignment_dir = create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=target,
            source_name=source_name,
            language=language,
            thebitlab_ref=thebitlab_ref,
            overwrite=overwrite,
            overwrite_source=overwrite_source,
        )
        results.append(AssignmentResult(target=target, assignment_dir=assignment_dir))
    return results


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for assigning an activity to repositories."""
    parser = argparse.ArgumentParser(description="Assegna una activity TheBitLab a uno o piu repository studente.")
    parser.add_argument("--activity", type=Path, required=True, help="Path della activity JSON da assegnare.")
    parser.add_argument(
        "--target",
        type=Path,
        action="append",
        help="Root di un repository studente. Ripeti il flag per piu studenti.",
    )
    parser.add_argument(
        "--targets-file",
        type=Path,
        help="File di testo con un repository studente per riga. Le righe vuote o che iniziano con # sono ignorate.",
    )
    parser.add_argument("--source-name", help="Nome del file sorgente da creare. Se omesso, dipende dal linguaggio.")
    parser.add_argument("--language", help="Linguaggio da usare, se diverso dalla activity.")
    parser.add_argument(
        "--thebitlab-ref",
        default=create_submission_scaffold.DEFAULT_THEBITLAB_REF,
        help="Branch, tag o commit TheBitLab da indicare nel README della consegna.",
    )
    parser.add_argument("--force", action="store_true", help="Aggiorna una consegna gia esistente.")
    parser.add_argument("--overwrite-source", action="store_true", help="Sovrascrive anche il sorgente se esiste.")
    parser.add_argument("--dry-run", action="store_true", help="Mostra il piano di assegnazione senza scrivere nei repository.")
    return parser.parse_args()


def main() -> int:
    """Run the assignment CLI."""
    args = parse_args()
    try:
        targets = collect_targets(args.target, args.targets_file)
        if args.dry_run:
            plan = build_assignment_plan(
                activity_path=args.activity,
                targets=targets,
                source_name=args.source_name,
                language=args.language,
                thebitlab_ref=args.thebitlab_ref,
                overwrite=args.force,
            )
            print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
            return 0
        results = assign_activity_to_targets(
            activity_path=args.activity,
            targets=targets,
            source_name=args.source_name,
            language=args.language,
            thebitlab_ref=args.thebitlab_ref,
            overwrite=args.force,
            overwrite_source=args.overwrite_source,
        )
    except ValueError as error:
        print(f"Activity non assegnata:\n{error}")
        return 1

    for result in results:
        print(f"Consegna creata per {result.target}: {result.assignment_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
