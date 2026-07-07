from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from scripts import create_submission_scaffold


@dataclass(frozen=True)
class AssignmentResult:
    """Result of assigning one activity to one target repository."""

    target: Path
    assignment_dir: Path


def load_targets_file(path: Path) -> list[Path]:
    """Load target repository roots from a plain text file."""
    targets: list[Path] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if clean_line and not clean_line.startswith("#"):
            target = Path(clean_line)
            if not target.is_absolute():
                target = path.parent / target
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
    activity = create_submission_scaffold.load_activity(activity_path)
    identifier = create_submission_scaffold.activity_id(activity)
    blocked_targets = [
        target
        for target in targets
        if create_submission_scaffold.scaffold_dir(target, identifier).exists()
        and any(create_submission_scaffold.scaffold_dir(target, identifier).iterdir())
        and not overwrite
    ]
    if blocked_targets:
        blocked = "\n".join(str(target) for target in blocked_targets)
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
    return parser.parse_args()


def main() -> int:
    """Run the assignment CLI."""
    args = parse_args()
    try:
        targets = collect_targets(args.target, args.targets_file)
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
