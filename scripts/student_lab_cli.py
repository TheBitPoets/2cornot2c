from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import student_lab_runner, student_lab_service


InputFn = Callable[[str], str]
PrintFn = Callable[[str], None]


STATUS_LABELS = {
    "pending": "Da fare",
    "missing": "Mancante",
    "submitted": "Consegnata",
    "submitted_late": "Consegnata in ritardo",
}
STATUS_COLORS = {
    "pending": "\033[33m",
    "missing": "\033[31m",
    "submitted": "\033[32m",
    "submitted_late": "\033[35m",
}
WORKSPACE_COLOR = "\033[36m"
RESET_COLOR = "\033[0m"


def clean_text(value: Any, fallback: str = "-") -> str:
    """Return a compact label for terminal output."""

    text = str(value or "").strip()
    return text or fallback


def status_label(status: str) -> str:
    """Return the human label for a lab assignment status."""

    return STATUS_LABELS.get(status, clean_text(status))


def colorize(text: str, color: str, use_color: bool) -> str:
    """Wrap text in ANSI color codes when color output is enabled."""

    return f"{color}{text}{RESET_COLOR}" if use_color and color else text


def colored_status(status: str, use_color: bool) -> str:
    """Return the status label, optionally colorized for terminal output."""

    clean_status = clean_text(status, "")
    return colorize(status_label(clean_status), STATUS_COLORS.get(clean_status, ""), use_color)


def grading_label(grading: dict[str, Any]) -> str:
    """Return a short grading summary for list and detail views."""

    status = clean_text(grading.get("status"), "non valutata")
    passed = grading.get("tests_passed")
    total = grading.get("tests_total")
    if passed is not None and total is not None:
        return f"{status} ({passed}/{total} test)"
    return status


def policy_list(values: Any) -> str:
    """Return a compact comma-separated list for support policy details."""

    if not isinstance(values, list) or not values:
        return "-"
    return ", ".join(clean_text(value) for value in values)


def truncate(text: str, width: int) -> str:
    """Return text clipped to width with a suffix."""

    clean = clean_text(text)
    if width <= 3:
        return clean[:width]
    if len(clean) <= width:
        return clean
    return clean[: width - 3] + "..."


def compact_datetime(value: Any) -> str:
    """Return a compact date/time label for the terminal."""

    text = clean_text(value, "")
    if not text:
        return "-"
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text


def render_header(student_id: str, assignments: list[dict[str, Any]]) -> str:
    """Render the static header for the student lab TUI."""

    submitted = sum(1 for item in assignments if item.get("submitted"))
    missing = sum(1 for item in assignments if item.get("status") == "missing")
    pending = sum(1 for item in assignments if item.get("status") == "pending")
    return "\n".join(
        [
            "TheBitLab - lab studente",
            f"Studente: {clean_text(student_id)}",
            f"Consegne: {len(assignments)} | Da fare: {pending} | Mancanti: {missing} | Consegnate: {submitted}",
        ]
    )


def render_legend(use_color: bool = False) -> str:
    """Render a compact legend for status and workspace labels."""

    return "\n".join(
        [
            "Legenda:",
            f"- {colored_status('pending', use_color)}: consegna assegnata, scadenza futura, nessun report ancora salvato.",
            f"- {colored_status('missing', use_color)}: scadenza superata senza report/consegna.",
            f"- {colored_status('submitted', use_color)}: esiste un report coerente con la consegna.",
            f"- {colored_status('submitted_late', use_color)}: report presente ma consegnato dopo la scadenza.",
            f"- {colorize('workspace', WORKSPACE_COLOR, use_color)}: cartella locale della consegna presente.",
            "- no workspace: cartella locale non ancora presente o non trovata.",
        ]
    )


def render_assignment_row(index: int, assignment: dict[str, Any], use_color: bool = False) -> str:
    """Render one compact assignment row."""

    title = truncate(clean_text(assignment.get("title") or assignment.get("activity_id")), 34)
    status = truncate(colored_status(clean_text(assignment.get("status")), use_color), 31 if use_color else 22)
    due_at = truncate(compact_datetime(assignment.get("due_at")), 16)
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_mark = colorize("workspace", WORKSPACE_COLOR, use_color) if workspace.get("exists") else "no workspace"
    status_width = 31 if use_color else 22
    return f"{index:>2}. {title:<34} | {status:<{status_width}} | {due_at:<16} | {workspace_mark}"


def render_assignment_list(payload: dict[str, Any], use_color: bool = False) -> str:
    """Render the main assignment list."""

    assignments = payload.get("assignments") if isinstance(payload.get("assignments"), list) else []
    lines = [
        render_header(clean_text(payload.get("student_id")), assignments),
        "",
        "Comandi: numero = dettaglio | r = ricarica | q = esci",
        "",
        render_legend(use_color),
        "",
    ]
    if not assignments:
        lines.append("Nessuna consegna disponibile per questo studente.")
        return "\n".join(lines)
    lines.append(" #  Titolo                             | Stato                  | Scadenza         | Workspace")
    lines.append("-" * 95)
    for index, assignment in enumerate(assignments, start=1):
        lines.append(render_assignment_row(index, assignment, use_color))
    return "\n".join(lines)


def detail_line(label: str, value: Any) -> str:
    """Render one label/value line for the detail view."""

    return f"{label:<18} {clean_text(value)}"


def render_assignment_detail(assignment: dict[str, Any], use_color: bool = False) -> str:
    """Render the detail page for one lab assignment."""

    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    report = assignment.get("report") if isinstance(assignment.get("report"), dict) else {}
    grading = assignment.get("grading") if isinstance(assignment.get("grading"), dict) else {}
    runner = assignment.get("runner") if isinstance(assignment.get("runner"), dict) else {}
    support_policy = assignment.get("support_policy") if isinstance(assignment.get("support_policy"), dict) else {}
    help_summary = assignment.get("help") if isinstance(assignment.get("help"), dict) else {}
    topics = activity.get("topics") if isinstance(activity.get("topics"), list) else []
    lines = [
        "Dettaglio consegna",
        "",
        detail_line("Titolo:", assignment.get("title") or assignment.get("activity_id")),
        detail_line("Activity:", assignment.get("activity_id")),
        detail_line("Assegnazione:", assignment.get("assignment_id")),
        detail_line("Classe:", assignment.get("class_label") or assignment.get("class_id")),
        detail_line("Assegnata:", compact_datetime(assignment.get("assigned_at"))),
        detail_line("Scadenza:", compact_datetime(assignment.get("due_at"))),
        detail_line("Stato:", colored_status(clean_text(assignment.get("status")), use_color)),
        "",
        "Workspace",
        detail_line("Path:", workspace.get("path")),
        detail_line("Esiste:", "si" if workspace.get("exists") else "no"),
        "",
        "Activity",
        detail_line("Path:", activity.get("path")),
        detail_line("Tipo:", activity.get("kind")),
        detail_line("Linguaggio:", activity.get("language")),
        detail_line("Sorgente:", activity.get("source_name")),
        detail_line("Argomenti:", ", ".join(str(topic) for topic in topics) if topics else "-"),
        "",
        "Aiuto consentito",
        detail_line("Modalita:", support_policy.get("label") or assignment.get("student_support_mode")),
        detail_line("Sintesi:", support_policy.get("summary")),
        detail_line("Permesso:", policy_list(support_policy.get("allowed"))),
        detail_line("Non permesso:", policy_list(support_policy.get("not_allowed"))),
        "",
        "Richieste aiuto",
        detail_line("Eventi:", help_summary.get("total")),
        detail_line("Consentite:", help_summary.get("allowed")),
        detail_line("Bloccate:", help_summary.get("denied")),
        detail_line("Ultima:", compact_datetime(help_summary.get("last_requested_at"))),
        detail_line("Esito ultima:", help_summary.get("last_decision")),
        "",
        "Report",
        detail_line("Path:", report.get("path")),
        detail_line("Esiste:", "si" if report.get("exists") else "no"),
        detail_line("Consegnata:", compact_datetime(report.get("submitted_at"))),
        detail_line("Commit:", report.get("commit")),
        "",
        "Grading",
        detail_line("Stato:", grading_label(grading)),
        detail_line("Voto:", grading.get("teacher_grade") if grading.get("teacher_grade") is not None else grading.get("score")),
        "",
        "Runner",
        detail_line("Stato:", runner.get("status")),
        detail_line("Backend:", runner.get("backend")),
        "",
        "Comandi: e = esegui e salva report | o = apri workspace | invio = torna all'elenco",
    ]
    return "\n".join(lines)


def runner_result_message(report: dict[str, Any], report_path: Path) -> str:
    """Return a compact message after a runner execution."""

    status = clean_text(report.get("status"))
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    passed = summary.get("passed")
    total = summary.get("total")
    tests = f" ({passed}/{total} test)" if passed is not None and total is not None else ""
    return "\n".join(
        [
            f"Runner completato: {status}{tests}",
            f"Report salvato: {report_path}",
        ]
    )


def clear_screen() -> None:
    """Clear the terminal screen when possible."""

    os.system("cls" if os.name == "nt" else "clear")


def supports_color(no_color: bool = False) -> bool:
    """Return whether ANSI colors should be emitted."""

    if no_color:
        return False
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def open_workspace(path_value: str, root: Path = PROJECT_ROOT) -> bool:
    """Open a workspace folder with the platform file manager."""

    raw_path = Path(path_value)
    path = raw_path if raw_path.is_absolute() else (root / raw_path).resolve(strict=False)
    if not path.is_dir():
        return False
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return True
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])
    return True


def load_payload(root: Path, student_id: str, now: str | None = None) -> dict[str, Any]:
    """Load the current student lab payload."""

    return student_lab_service.student_lab_payload(root=root, student_id=student_id, now=now)


def run_tui(
    *,
    student_id: str,
    root: Path = PROJECT_ROOT,
    now: str | None = None,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
    clear: bool = True,
    use_color: bool = False,
) -> int:
    """Run the interactive student lab loop."""

    payload = load_payload(root, student_id, now)
    while True:
        if clear:
            clear_screen()
        print_fn(render_assignment_list(payload, use_color=use_color))
        choice = input_fn("\nScelta: ").strip().lower()
        if choice in {"q", "quit", "esci"}:
            return 0
        if choice in {"r", "reload", "ricarica"}:
            payload = load_payload(root, student_id, now)
            continue
        if not choice.isdigit():
            continue
        index = int(choice) - 1
        assignments = payload.get("assignments") if isinstance(payload.get("assignments"), list) else []
        if index < 0 or index >= len(assignments):
            continue
        assignment = assignments[index]
        if clear:
            clear_screen()
        print_fn(render_assignment_detail(assignment, use_color=use_color))
        action = input_fn("\nDettaglio: ").strip().lower()
        if action == "o":
            workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
            if not open_workspace(clean_text(workspace.get("path"), ""), root=root):
                print_fn("Workspace non disponibile.")
                input_fn("Premi invio per continuare...")
        if action == "e":
            try:
                report = student_lab_runner.run_local_assignment(assignment, root=root)
                report_path = student_lab_runner.write_student_report(root, assignment, report)
                print_fn(runner_result_message(report, report_path))
                payload = load_payload(root, student_id, now)
            except ValueError as error:
                print_fn(f"Runner non disponibile:\n{error}")
            input_fn("Premi invio per continuare...")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the student lab TUI."""

    parser = argparse.ArgumentParser(description="Apri la TUI minima del lab studente.")
    parser.add_argument("--student-id", required=True, help="Identificativo studente, per esempio rossi-mario.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Root del repository TheBitLab.")
    parser.add_argument("--now", help="Data ISO da usare per calcolare scadenze e mancanti.")
    parser.add_argument("--no-clear", action="store_true", help="Non pulire lo schermo tra una vista e l'altra.")
    parser.add_argument("--no-color", action="store_true", help="Disabilita colori ANSI.")
    return parser.parse_args()


def main() -> int:
    """Run the student lab TUI from the command line."""

    args = parse_args()
    try:
        return run_tui(
            student_id=args.student_id,
            root=args.root.resolve(strict=False),
            now=args.now,
            clear=not args.no_clear,
            use_color=supports_color(args.no_color),
        )
    except ValueError as error:
        print(f"Lab studente non disponibile:\n{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
