from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import student_lab_service


InputFn = Callable[[str], str]
PrintFn = Callable[[str], None]


STATUS_LABELS = {
    "pending": "Da fare",
    "missing": "Mancante",
    "submitted": "Consegnata",
    "submitted_late": "Consegnata in ritardo",
}


def clean_text(value: Any, fallback: str = "-") -> str:
    """Return a compact label for terminal output."""

    text = str(value or "").strip()
    return text or fallback


def status_label(status: str) -> str:
    """Return the human label for a lab assignment status."""

    return STATUS_LABELS.get(status, clean_text(status))


def grading_label(grading: dict[str, Any]) -> str:
    """Return a short grading summary for list and detail views."""

    status = clean_text(grading.get("status"), "non valutata")
    passed = grading.get("tests_passed")
    total = grading.get("tests_total")
    if passed is not None and total is not None:
        return f"{status} ({passed}/{total} test)"
    return status


def truncate(text: str, width: int) -> str:
    """Return text clipped to width with a suffix."""

    clean = clean_text(text)
    if width <= 3:
        return clean[:width]
    if len(clean) <= width:
        return clean
    return clean[: width - 3] + "..."


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


def render_assignment_row(index: int, assignment: dict[str, Any]) -> str:
    """Render one compact assignment row."""

    title = truncate(clean_text(assignment.get("title") or assignment.get("activity_id")), 34)
    status = truncate(status_label(clean_text(assignment.get("status"))), 22)
    due_at = truncate(clean_text(assignment.get("due_at")), 25)
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_mark = "workspace" if workspace.get("exists") else "no workspace"
    return f"{index:>2}. {title:<34} | {status:<22} | {due_at:<25} | {workspace_mark}"


def render_assignment_list(payload: dict[str, Any]) -> str:
    """Render the main assignment list."""

    assignments = payload.get("assignments") if isinstance(payload.get("assignments"), list) else []
    lines = [
        render_header(clean_text(payload.get("student_id")), assignments),
        "",
        "Comandi: numero = dettaglio | r = ricarica | q = esci",
        "",
    ]
    if not assignments:
        lines.append("Nessuna consegna disponibile per questo studente.")
        return "\n".join(lines)
    lines.append(" #  Titolo                             | Stato                  | Scadenza                  | Workspace")
    lines.append("-" * 104)
    for index, assignment in enumerate(assignments, start=1):
        lines.append(render_assignment_row(index, assignment))
    return "\n".join(lines)


def detail_line(label: str, value: Any) -> str:
    """Render one label/value line for the detail view."""

    return f"{label:<18} {clean_text(value)}"


def render_assignment_detail(assignment: dict[str, Any]) -> str:
    """Render the detail page for one lab assignment."""

    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    report = assignment.get("report") if isinstance(assignment.get("report"), dict) else {}
    grading = assignment.get("grading") if isinstance(assignment.get("grading"), dict) else {}
    runner = assignment.get("runner") if isinstance(assignment.get("runner"), dict) else {}
    topics = activity.get("topics") if isinstance(activity.get("topics"), list) else []
    lines = [
        "Dettaglio consegna",
        "",
        detail_line("Titolo:", assignment.get("title") or assignment.get("activity_id")),
        detail_line("Activity:", assignment.get("activity_id")),
        detail_line("Assegnazione:", assignment.get("assignment_id")),
        detail_line("Classe:", assignment.get("class_label") or assignment.get("class_id")),
        detail_line("Assegnata:", assignment.get("assigned_at")),
        detail_line("Scadenza:", assignment.get("due_at")),
        detail_line("Stato:", status_label(clean_text(assignment.get("status")))),
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
        "Report",
        detail_line("Path:", report.get("path")),
        detail_line("Esiste:", "si" if report.get("exists") else "no"),
        detail_line("Consegnata:", report.get("submitted_at")),
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
        "Comandi: o = apri workspace | invio = torna all'elenco",
    ]
    return "\n".join(lines)


def clear_screen() -> None:
    """Clear the terminal screen when possible."""

    os.system("cls" if os.name == "nt" else "clear")


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
) -> int:
    """Run the interactive student lab loop."""

    payload = load_payload(root, student_id, now)
    while True:
        if clear:
            clear_screen()
        print_fn(render_assignment_list(payload))
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
        print_fn(render_assignment_detail(assignment))
        action = input_fn("\nDettaglio: ").strip().lower()
        if action == "o":
            workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
            if not open_workspace(clean_text(workspace.get("path"), ""), root=root):
                print_fn("Workspace non disponibile.")
                input_fn("Premi invio per continuare...")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the student lab TUI."""

    parser = argparse.ArgumentParser(description="Apri la TUI minima del lab studente.")
    parser.add_argument("--student-id", required=True, help="Identificativo studente, per esempio rossi-mario.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Root del repository TheBitLab.")
    parser.add_argument("--now", help="Data ISO da usare per calcolare scadenze e mancanti.")
    parser.add_argument("--no-clear", action="store_true", help="Non pulire lo schermo tra una vista e l'altra.")
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
        )
    except ValueError as error:
        print(f"Lab studente non disponibile:\n{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
