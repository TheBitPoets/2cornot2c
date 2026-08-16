from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import student_virtual_lab


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold ed esecuzione dei laboratori virtuali TheBitLab."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Crea l'artifact iniziale di una Activity virtual-lab.",
    )
    scaffold_parser.add_argument("--activity", type=Path, required=True)
    scaffold_parser.add_argument("--target", type=Path, required=True)
    scaffold_parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    scaffold_parser.add_argument("--force", action="store_true")

    run_parser = subparsers.add_parser(
        "run",
        help="Esegue e salva un tentativo virtual-lab per uno studente.",
    )
    run_parser.add_argument("--student-id", required=True)
    selection = run_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--assignment-id")
    selection.add_argument("--activity-id")
    run_parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    run_parser.add_argument("--runtime-root", type=Path)
    run_parser.add_argument("--now")
    run_parser.add_argument("--final", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "scaffold":
            destination = student_virtual_lab.create_virtual_lab_scaffold(
                activity_path=args.activity,
                target_dir=args.target,
                project_root=args.project_root,
                overwrite=args.force,
            )
            print(f"Scaffold virtual-lab creato: {destination}")
            return 0

        report, report_path = student_virtual_lab.run_student_virtual_lab(
            student_id=args.student_id,
            assignment_id=args.assignment_id,
            activity_id=args.activity_id,
            root=args.root,
            runtime_root=args.runtime_root,
            now=args.now,
            final=args.final,
        )
    except ValueError as error:
        print(f"Virtual lab non eseguito:\n{error}")
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report salvato: {report_path}")
    return 0 if report.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
