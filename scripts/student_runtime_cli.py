from __future__ import annotations

import argparse
import json
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from scripts import student_lab_runner, student_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def add_assignment_selection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--student-id", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--assignment-id")
    selection.add_argument("--activity-id")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--now")
    parser.add_argument(
        "--timeout",
        type=student_lab_runner.positive_int,
        default=30,
        help="Timeout operativo passato al runtime, in secondi.",
    )


def safe_browser_endpoint(endpoint: str) -> bool:
    """Allow automatic browser opening only for ordinary HTTP(S) endpoints."""

    parsed = urlparse(str(endpoint or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def keep_interactive_runtime_alive(*, poll_seconds: float = 0.25) -> None:
    """Keep the CLI process alive while an in-process interactive runtime is serving.

    Built-in interactive runtimes such as Flowchart Lab host their loopback HTTP
    service in daemon threads owned by this process. Returning from the CLI would
    immediately destroy that service and leave the printed endpoint unusable.
    The launcher therefore remains attached until the operator interrupts it.
    """

    try:
        while True:
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Esegue o apre una consegna TheBitLab gestita da un runtime esterno."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch = subparsers.add_parser("launch", help="Apre l'interfaccia interattiva del runtime.")
    add_assignment_selection(launch)
    launch.add_argument("--no-open-browser", action="store_true")

    run = subparsers.add_parser("run", help="Esegue il grading headless tramite il normale runner TheBitLab.")
    add_assignment_selection(run)
    run.add_argument("--write-report", action="store_true")
    run.add_argument("--final", action="store_true")
    return parser.parse_args()


def load_assignment(args: argparse.Namespace) -> dict:
    return student_lab_runner.load_student_assignment(
        root=args.root.resolve(strict=False),
        student_id=args.student_id,
        assignment_id=args.assignment_id,
        activity_id=args.activity_id,
        now=args.now,
    )


def main() -> int:
    args = parse_args()
    root = args.root.resolve(strict=False)
    try:
        assignment = load_assignment(args)
        if args.command == "launch":
            result = student_runtime.launch_runtime_assignment(
                assignment,
                root=root,
                timeout_seconds=args.timeout,
            )
            payload = {
                "status": result.status,
                "session_id": result.session_id,
                "endpoint": result.endpoint,
                "detail": result.detail,
                "metadata": result.metadata,
            }
            # Flush is required because the managed launcher stays alive after
            # emitting its endpoint and may be consumed by a parent launcher.
            print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
            if result.endpoint and not args.no_open_browser:
                if not safe_browser_endpoint(result.endpoint):
                    raise ValueError(
                        "Il runtime ha restituito un endpoint non HTTP(S); "
                        "l'apertura automatica e stata bloccata."
                    )
                webbrowser.open(result.endpoint)
            if result.status in {"started", "already_running"} and result.endpoint:
                keep_interactive_runtime_alive()
            return 0 if result.status in {"started", "already_running"} else 1

        if args.final and not args.write_report:
            raise ValueError("--final richiede --write-report")
        report = student_lab_runner.run_assignment(
            assignment,
            root=root,
            timeout_seconds=args.timeout,
        )
        if args.write_report:
            report_path = student_lab_runner.write_student_report(root, assignment, report)
            if args.final:
                student_lab_runner.finalize_report_attempt(
                    root,
                    assignment,
                    report_path,
                    student_lab_runner.clean_text(report.get("attempt_id")),
                )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("passed") is True else 1
    except ValueError as error:
        print(f"Runtime non disponibile: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
