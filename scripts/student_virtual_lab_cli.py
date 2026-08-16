from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import (
    efesto_ui_server,
    student_lab_runner,
    student_virtual_lab,
    student_virtual_lab_ui,
)


def add_assignment_selection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--student-id", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--assignment-id")
    selection.add_argument("--activity-id")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--now")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold, esecuzione e UI dei laboratori virtuali TheBitLab."
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
    add_assignment_selection(run_parser)
    run_parser.add_argument("--final", action="store_true")

    ui_parser = subparsers.add_parser(
        "ui",
        help="Apre la UI 2D locale della consegna virtual-lab selezionata.",
    )
    add_assignment_selection(ui_parser)
    ui_parser.add_argument("--port", type=efesto_ui_server.positive_port, default=0)
    ui_parser.add_argument(
        "--no-open-browser",
        action="store_true",
        help="Avvia il server senza aprire automaticamente il browser.",
    )
    return parser.parse_args()


def load_selected_assignment(args: argparse.Namespace) -> dict:
    root = args.root.resolve(strict=False)
    return student_lab_runner.load_student_assignment(
        root=root,
        student_id=args.student_id,
        assignment_id=args.assignment_id,
        activity_id=args.activity_id,
        now=args.now,
    )


def assignment_ui_session(args: argparse.Namespace) -> efesto_ui_server.EfestoUiSession:
    return student_virtual_lab_ui.session_for_assignment(
        load_selected_assignment(args),
        root=args.root,
        runtime_root=args.runtime_root,
    )


def run_ui_command(args: argparse.Namespace) -> int:
    assignment = load_selected_assignment(args)
    session = student_virtual_lab_ui.session_for_assignment(
        assignment,
        root=args.root,
        runtime_root=args.runtime_root,
    )
    server = efesto_ui_server.create_server(session, port=args.port)
    url = efesto_ui_server.session_url(server, session)
    print(f"Efesto UI: {url}")
    print("Server solo locale; Ctrl+C per terminare.")
    if not args.no_open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


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

        if args.command == "ui":
            return run_ui_command(args)

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
