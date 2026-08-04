from __future__ import annotations

import argparse
import base64
import ipaddress
import json
import os
import shlex
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import uuid
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import (
    student_help_auth,
    student_help_service,
    student_lab_layout,
    student_lab_runner,
    student_lab_service,
    student_lab_utui,
    thebitlab_tui_pairing_client,
)


InputFn = Callable[[str], str]
PrintFn = Callable[[str], None]
DEFAULT_SERVER_URL = "http://127.0.0.1:8765"
_USER_AGENT = "TheBitLab-TUI/1.0"
HELP_REQUEST_TIMEOUT_SECONDS = 150
MAX_STUDENT_API_RESPONSE_BYTES = 2 * 1024 * 1024
TUI_RENDERERS = {"auto", "legacy", "utui"}


class StudentHelpRequestPendingError(ValueError):
    """Report that an idempotent help request is still being processed."""


class _MemoryBearer:
    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = str(value or "")

    def __repr__(self) -> str:
        return "_MemoryBearer(present=%s)" % bool(self.value)


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
HELP_REQUEST_COLOR = "\033[36m"
HELP_PROMPT_COLOR = "\033[33m"
HELP_REASON_COLOR = "\033[35m"
HELP_RESPONSE_COLOR = "\033[32m"
HELP_ERROR_COLOR = "\033[31m"
GUIDE_TERM_COLORS = {
    "consegna": "\033[35m",
    "workspace": WORKSPACE_COLOR,
    "test": "\033[33m",
    "report": "\033[32m",
}
GUIDE_TERM_BOLD_COLOR = "\033[1;37m"
GUIDE_DESCRIPTION_COLOR = "\033[3;90m"
MAX_ATTEMPTS_DISPLAYED = 20
RESET_COLOR = "\033[0m"


def clean_text(value: Any, fallback: str = "-") -> str:
    """Return a compact label for terminal output."""

    text = "".join(
        " " if character in "\r\n\t" else ""
        if unicodedata.category(character).startswith("C")
        else character
        for character in str(value or "")
    ).strip()
    return text or fallback


def validated_server_url(server_url: str, allow_insecure_http: bool = False) -> str:
    """Require HTTPS when a bearer token leaves the local machine."""

    clean_url = str(server_url or "").strip().rstrip("/")
    parsed = urllib.parse.urlparse(clean_url)
    if parsed.scheme == "https" and parsed.hostname:
        return clean_url
    if parsed.scheme == "http" and parsed.hostname:
        is_loopback = parsed.hostname.lower() == "localhost"
        try:
            is_loopback = is_loopback or ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            pass
        if is_loopback or allow_insecure_http:
            return clean_url
    raise ValueError(
        "Il token studente richiede HTTPS per un server remoto. "
        "Usa un tunnel HTTPS oppure --allow-insecure-http solo per un collaudo controllato."
    )


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


def ai_budget_label(value: Any, use_color: bool = False) -> str:
    """Return a compact AI budget summary."""

    if not isinstance(value, dict):
        return "-"
    limit = value.get("limit")
    used = value.get("used")
    remaining = value.get("remaining")
    if not limit:
        return colorize("non disponibile", HELP_ERROR_COLOR, use_color)
    label = f"{used or 0}/{limit} usate, {remaining or 0} rimanenti"
    if value.get("exhausted") or not remaining:
        color = HELP_ERROR_COLOR
    elif remaining <= max(1, (limit + 1) // 2):
        color = HELP_PROMPT_COLOR
    else:
        color = HELP_RESPONSE_COLOR
    return colorize(f"{label} (esaurito)" if value.get("exhausted") else label, color, use_color)


def help_decision_label(value: Any, use_color: bool = False) -> str:
    """Return the latest help decision with an actionable status color."""

    decision = clean_text(value, "")
    if decision == "consentita":
        return colorize(decision, HELP_RESPONSE_COLOR, use_color)
    if decision == "bloccata":
        return colorize(decision, HELP_ERROR_COLOR, use_color)
    return colorize("nessuna richiesta", HELP_PROMPT_COLOR, use_color) if use_color else "nessuna richiesta"


def runner_status_label(value: Any, use_color: bool = False) -> str:
    """Return runner state with red pending/error and green completed status."""

    status = clean_text(value, "not_run")
    if status == "not_run":
        return colorize(status, HELP_ERROR_COLOR, use_color)
    if status == "passed":
        return colorize(status, HELP_RESPONSE_COLOR, use_color)
    return colorize(status, HELP_ERROR_COLOR, use_color)


def grade_label(value: Any, use_color: bool = False) -> str:
    """Return a grade with a quick visual indication of its range."""

    if value is None or isinstance(value, bool):
        return "-"
    try:
        grade = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return clean_text(value, "-")
    if 7 <= grade <= 10:
        color = HELP_RESPONSE_COLOR
    elif 5 <= grade < 7:
        color = HELP_PROMPT_COLOR
    else:
        color = HELP_ERROR_COLOR
    return colorize(str(value), color, use_color)


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
    clean_status = clean_text(assignment.get("status"), "")
    status = truncate(status_label(clean_status), 22)
    status = colorize(status, STATUS_COLORS.get(clean_status, ""), use_color)
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


def detail_line(label: str, value: Any, *, formatted: bool = False) -> str:
    """Render one label/value line for the detail view."""

    rendered = str(value) if formatted else clean_text(value)
    return f"{label:<18} {rendered}"


def section_separator(width: int = 72) -> str:
    """Return a subtle separator for detail sections."""

    return "-" * width


def guide_term(text: str, use_color: bool = False) -> str:
    """Return a highlighted guide term for the detail view."""

    return colorize(text, GUIDE_TERM_COLORS.get(text.lower(), ""), use_color)


def guide_label(text: str, use_color: bool = False) -> str:
    """Return a padded guide term with optional coloring."""

    return colorize(f"{text:<9}", GUIDE_TERM_COLORS.get(text.lower(), ""), use_color)


def guide_definition(term: str, description: str, use_color: bool = False) -> str:
    """Render one compact glossary definition for the assignment detail view."""

    styled_term = colorize(term, GUIDE_TERM_BOLD_COLOR, use_color)
    styled_description = colorize(description, GUIDE_DESCRIPTION_COLOR, use_color)
    padding = " " * max(1, 10 - len(term))
    return f"  {styled_term}{padding}{styled_description}"


def test_result_label(test: dict[str, Any], use_color: bool = False) -> str:
    """Return a compact label for one test result."""

    if test.get("passed") is True:
        return colorize("[ok]", HELP_RESPONSE_COLOR, use_color)
    if test.get("passed") is False:
        return colorize("[ko]", HELP_ERROR_COLOR, use_color)
    status = clean_text(test.get("status"), "")
    return colorize(f"[{status}]" if status else "[?]", HELP_PROMPT_COLOR, use_color)


def test_result_detail(test: dict[str, Any]) -> str:
    """Return the first useful detail for one test result."""

    for key in ("detail", "message", "error", "stderr", "stdout"):
        value = clean_text(test.get(key), "")
        if value:
            return " ".join(value.split())
    return ""


def render_test_details(report: dict[str, Any], use_color: bool = False) -> list[str]:
    """Render test details from a runner report."""

    tests = report.get("tests")
    if not isinstance(tests, list) or not tests:
        return ["Dettaglio test", "  non disponibile nel report"]
    lines = ["Dettaglio test"]
    for index, item in enumerate(tests, start=1):
        if not isinstance(item, dict):
            continue
        name = clean_text(item.get("name"), f"test {index}")
        lines.append(f"  {test_result_label(item, use_color=use_color)} {name}")
        detail = test_result_detail(item)
        if detail and item.get("passed") is not True:
            lines.append(f"      {truncate(detail, 96)}")
    if len(lines) == 1:
        lines.append("  non disponibile nel report")
    return lines


def attempt_result_label(attempt: dict[str, Any] | None, use_color: bool = False) -> str:
    """Return one compact attempt result for summaries and history."""

    if not isinstance(attempt, dict):
        return "-"
    passed = attempt.get("tests_passed")
    total = attempt.get("tests_total")
    tests = f"{passed}/{total} test" if isinstance(passed, int) and isinstance(total, int) else "test n/d"
    status = clean_text(attempt.get("status"), "esito n/d")
    color = (
        HELP_RESPONSE_COLOR
        if attempt.get("passed") is True
        else HELP_ERROR_COLOR
        if attempt.get("passed") is False
        else HELP_PROMPT_COLOR
    )
    return colorize(
        f"{status}, {tests}, {compact_datetime(attempt.get('submitted_at'))}",
        color,
        use_color,
    )


def selectable_attempts(assignment: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the recent valid attempts exposed by the interactive TUI."""

    attempts = assignment.get("attempts") if isinstance(assignment.get("attempts"), dict) else {}
    items = attempts.get("items") if isinstance(attempts.get("items"), list) else []
    return [
        item
        for item in items
        if isinstance(item, dict) and clean_text(item.get("id"), "")
    ][:MAX_ATTEMPTS_DISPLAYED]


def render_attempt_history(assignment: dict[str, Any], use_color: bool = False) -> str:
    """Render the bounded immutable attempt history for one assignment."""

    attempts = assignment.get("attempts") if isinstance(assignment.get("attempts"), dict) else {}
    all_items = attempts.get("items") if isinstance(attempts.get("items"), list) else []
    items = selectable_attempts(assignment)
    final = attempts.get("final") if isinstance(attempts.get("final"), dict) else {}
    final_id = clean_text(final.get("id"), "")
    lines = ["Storico tentativi", section_separator()]
    if not items:
        lines.append("Nessun tentativo selezionabile.")
    for index, raw_attempt in enumerate(items, start=1):
        attempt = raw_attempt if isinstance(raw_attempt, dict) else {}
        marker = " [definitivo]" if clean_text(attempt.get("id"), "") == final_id else ""
        lines.append(
            f"{index:>2}. {attempt_result_label(attempt, use_color=use_color)}{marker}"
        )
        lines.append(f"    ID: {clean_text(attempt.get('id'), '-')}")
    if attempts.get("truncated") is True:
        lines.extend(
            [
                section_separator(),
                "Avviso: lo storico mostrato e parziale; i tentativi piu vecchi non sono elencati.",
            ]
        )
    if len(all_items) > len(items):
        lines.append(
            f"Sono mostrati solo i {len(items)} tentativi piu recenti su {attempts.get('count') or len(all_items)}."
        )
    lines.extend(
        [
            section_separator(),
            "Scegli un numero per indicare il tentativo definitivo; invio o b annulla.",
        ]
    )
    return "\n".join(lines)


def render_assignment_detail(
    assignment: dict[str, Any],
    use_color: bool = False,
    layout: dict[str, Any] | None = None,
    terminal_width: int | None = None,
) -> str:
    """Render the detail page for one lab assignment."""

    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    report = assignment.get("report") if isinstance(assignment.get("report"), dict) else {}
    attempts = assignment.get("attempts") if isinstance(assignment.get("attempts"), dict) else {}
    grading = assignment.get("grading") if isinstance(assignment.get("grading"), dict) else {}
    runner = assignment.get("runner") if isinstance(assignment.get("runner"), dict) else {}
    support_policy = assignment.get("support_policy") if isinstance(assignment.get("support_policy"), dict) else {}
    help_summary = assignment.get("help") if isinstance(assignment.get("help"), dict) else {}
    topics = activity.get("topics") if isinstance(activity.get("topics"), list) else []
    lines = [
        "Dettaglio consegna",
        section_separator(),
        detail_line("Titolo:", assignment.get("title") or assignment.get("activity_id")),
        detail_line("Activity:", assignment.get("activity_id")),
        detail_line("Assegnazione:", assignment.get("assignment_id")),
        detail_line("Classe:", assignment.get("class_label") or assignment.get("class_id")),
        detail_line("Assegnata:", compact_datetime(assignment.get("assigned_at"))),
        detail_line("Scadenza:", compact_datetime(assignment.get("due_at"))),
        detail_line("Stato:", colored_status(clean_text(assignment.get("status")), use_color), formatted=True),
        section_separator(),
        "Workspace",
        detail_line("Path:", workspace.get("path")),
        detail_line("Esiste:", "si" if workspace.get("exists") else "no"),
        section_separator(),
        "Activity",
        detail_line("Path:", activity.get("path")),
        detail_line("Tipo:", activity.get("kind")),
        detail_line("Linguaggio:", activity.get("language")),
        detail_line("Sorgente:", activity.get("source_name")),
        detail_line("Argomenti:", ", ".join(str(topic) for topic in topics) if topics else "-"),
        section_separator(),
        "Aiuto consentito",
        detail_line("Modalità:", support_policy.get("label") or assignment.get("student_support_mode")),
        detail_line("Sintesi:", support_policy.get("summary")),
        detail_line("Permesso:", policy_list(support_policy.get("allowed"))),
        detail_line("Non permesso:", policy_list(support_policy.get("not_allowed"))),
        section_separator(),
        "Richieste aiuto",
        detail_line("Stato log:", help_summary.get("status")),
        detail_line("Errore log:", help_summary.get("error")),
        detail_line("Eventi:", help_summary.get("total")),
        detail_line("Consentite:", help_summary.get("allowed")),
        detail_line("Bloccate:", help_summary.get("denied")),
        detail_line("AI budget:", ai_budget_label(help_summary.get("ai_budget"), use_color), formatted=True),
        detail_line("Ultima:", compact_datetime(help_summary.get("last_requested_at"))),
        detail_line("Esito ultima:", help_decision_label(help_summary.get("last_decision"), use_color), formatted=True),
        section_separator(),
        "Report",
        detail_line("Path:", report.get("path")),
        detail_line("Esiste:", "si" if report.get("exists") else "no"),
        detail_line("Consegnata:", compact_datetime(report.get("submitted_at"))),
        detail_line("Commit:", report.get("commit")),
        section_separator(),
        "Tentativi",
        detail_line("Totale:", attempts.get("count")),
        detail_line(
            "Ultimo:",
            attempt_result_label(
                attempts.get("latest") if isinstance(attempts.get("latest"), dict) else None,
                use_color,
            ),
            formatted=True,
        ),
        detail_line(
            "Migliore:",
            attempt_result_label(
                attempts.get("best") if isinstance(attempts.get("best"), dict) else None,
                use_color,
            ),
            formatted=True,
        ),
        detail_line(
            "Definitivo:",
            attempt_result_label(
                attempts.get("final") if isinstance(attempts.get("final"), dict) else None,
                use_color,
            ),
            formatted=True,
        ),
        *(
            [
                section_separator(),
                "Ultimo dettaglio test",
                *render_test_details({"tests": report.get("tests")}, use_color=use_color)[1:],
            ]
            if report.get("exists")
            else []
        ),
        section_separator(),
        "Grading",
        detail_line("Stato:", grading_label(grading)),
        detail_line(
            "Voto:",
            grade_label(
                grading.get("teacher_grade")
                if grading.get("teacher_grade") is not None
                else grading.get("score"),
                use_color,
            ),
            formatted=True,
        ),
        section_separator(),
        "Runner",
        detail_line("Stato:", runner_status_label(runner.get("status"), use_color), formatted=True),
        detail_line("Backend:", runner.get("backend")),
        section_separator(),
        "Guida rapida",
        guide_definition("Consegna", "lavoro assegnato dal docente.", use_color),
        guide_definition("Workspace", "cartella locale dove modifichi i file.", use_color),
        guide_definition("Test", "controlli automatici sul tuo lavoro.", use_color),
        guide_definition("Report", "risultato salvato e letto da dashboard/registro.", use_color),
        "",
        "Flusso consigliato",
        f"  1. Apri {guide_term('workspace', use_color)}",
        "  2. Modifica i file",
        f"  3. Esegui {guide_term('test', use_color)} e salva {guide_term('report', use_color)}",
        f"  4. Controlla esito e, se serve, chiedi aiuto sulla {guide_term('consegna', use_color)}",
        section_separator(),
        "Azioni principali",
        "  e  Esegui test e salva report",
        "  a  Chiedi aiuto",
        "  t  Storico e tentativo definitivo",
        "  o  Apri workspace",
        "  v  Apri editor",
        "  c  Apri terminale",
        "  l  Modifica layout pannelli",
        "",
        "Altri comandi",
        "  h  Storico aiuti",
        "  b  Torna alla lista",
        "  invio  Torna alla lista",
        "  q  Esci",
    ]
    if layout is not None:
        return student_lab_layout.render_layout(
            lines,
            layout,
            terminal_width=terminal_width,
            use_color=use_color,
        )
    return "\n".join(lines)


def resolve_tui_renderer(
    requested: str,
    *,
    interactive: bool | None = None,
) -> str:
    """Resolve the requested renderer without changing non-interactive output."""

    renderer = clean_text(requested, "auto").lower()
    if renderer not in TUI_RENDERERS:
        choices = ", ".join(sorted(TUI_RENDERERS))
        raise ValueError(f"Renderer TUI non supportato: {renderer}. Valori: {choices}.")
    if renderer == "legacy":
        return "legacy"
    if renderer == "utui":
        if not student_lab_utui.is_available():
            raise ValueError(
                "Renderer utui non disponibile. Usa Python 3.11 o successivo e "
                "installa requirements-utui.txt, oppure scegli --renderer legacy."
            )
        return "utui"
    terminal_interactive = sys.stdout.isatty() if interactive is None else interactive
    return "auto" if terminal_interactive and student_lab_utui.is_available() else "legacy"


def render_assignment_view(
    assignment: dict[str, Any],
    *,
    use_color: bool,
    layout: dict[str, Any],
    renderer: str,
    terminal_width: int | None = None,
    terminal_height: int | None = None,
    interaction: dict[str, Any] | None = None,
    renderer_observer: Callable[[str], None] | None = None,
) -> str:
    """Render one assignment through the selected CLI presentation backend."""

    terminal_size = shutil.get_terminal_size((120, 40))
    width = terminal_width or terminal_size.columns
    height = terminal_height or max(8, terminal_size.lines - 5)

    def legacy() -> str:
        return render_assignment_detail(
            assignment,
            use_color=use_color,
            layout=layout,
            terminal_width=width,
        )

    if renderer == "legacy":
        if renderer_observer is not None:
            renderer_observer("legacy")
        return legacy()
    if renderer == "auto":
        fallback_used = False

        def mark_fallback() -> None:
            nonlocal fallback_used
            fallback_used = True

        rendered = student_lab_utui.render_assignment_or_fallback(
            assignment,
            layout,
            width=width,
            height=height,
            color=use_color,
            fallback=legacy,
            interaction=interaction,
            on_fallback=mark_fallback,
        )
        if renderer_observer is not None:
            renderer_observer("legacy" if fallback_used else "utui")
        return rendered
    try:
        rendered = "\n".join(
            student_lab_utui.render_assignment_frame(
                assignment,
                layout,
                width=width,
                height=height,
                color=use_color,
                interaction=interaction,
            )
        )
        if renderer_observer is not None:
            renderer_observer("utui")
        return rendered
    except Exception as error:
        raise ValueError(f"Renderer utui non riuscito: {error}") from error


def render_utui_detail_commands() -> str:
    """Keep navigation and assignment actions visible below the clipped frame."""

    return "\n".join(
        (
            "Navigazione: j = scorri giu | k = scorri su | l = modifica layout",
            "Azioni: e = test/report | t = tentativi | a = aiuto | o = workspace | v = editor | c = terminale",
            "Altri: h = storico aiuti | b/invio = lista | q = esci",
        )
    )


def runner_result_message(report: dict[str, Any], report_path: Path, use_color: bool = False) -> str:
    """Return a clear message after a runner execution."""

    status = clean_text(report.get("status"))
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    passed = summary.get("passed")
    total = summary.get("total")
    tests = f"{passed}/{total} test" if passed is not None and total is not None else "non disponibili"
    outcome = "consegna superata" if report.get("passed") is True else "consegna da ricontrollare"
    if report.get("passed") is None:
        outcome = "esito non disponibile"
    return "\n".join(
        [
            "Esecuzione completata",
            detail_line("Stato runner:", runner_status_label(status, use_color), formatted=True),
            detail_line(
                "Esito:",
                colorize(
                    outcome,
                    HELP_RESPONSE_COLOR
                    if report.get("passed") is True
                    else HELP_ERROR_COLOR
                    if report.get("passed") is False
                    else HELP_PROMPT_COLOR,
                    use_color,
                ),
                formatted=True,
            ),
            detail_line("Test:", tests),
            detail_line("Report salvato:", report_path),
            "",
            *render_test_details(report, use_color=use_color),
            "",
            "Questo report è quello letto da dashboard e registro docente.",
        ]
    )


HELP_MENU = {
    "1": "feedback-tecnico",
    "2": "teoria",
    "3": "ai",
}

def help_choice_label() -> str:
    """Return a compact help-type menu label."""

    return "1 feedback tecnico | 2 teoria | 3 AI"


def assignment_repo_path(assignment: dict[str, Any], root: Path = PROJECT_ROOT) -> Path | None:
    """Infer the local student repo path from assignment paths."""

    help_data = assignment.get("help") if isinstance(assignment.get("help"), dict) else {}
    help_path = clean_text(help_data.get("path"), "")
    normalized_help_path = help_path.replace("\\", "/")
    if help_path and "/help/" in normalized_help_path:
        raw_path = Path(help_path)
        resolved = raw_path if raw_path.is_absolute() else (root / raw_path).resolve(strict=False)
        return resolved.parents[2] if len(resolved.parents) >= 3 else None
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_path = clean_text(workspace.get("path"), "")
    normalized_workspace_path = workspace_path.replace("\\", "/")
    if workspace_path and "/assignments/" in normalized_workspace_path:
        raw_path = Path(workspace_path)
        resolved = raw_path if raw_path.is_absolute() else (root / raw_path).resolve(strict=False)
        return resolved.parents[1] if len(resolved.parents) >= 2 else None
    return None


def assignment_help_log_path(assignment: dict[str, Any], root: Path = PROJECT_ROOT) -> Path | None:
    """Return the local help log path for one assignment, when available."""

    help_data = assignment.get("help") if isinstance(assignment.get("help"), dict) else {}
    help_path = clean_text(help_data.get("path"), "")
    if help_path:
        raw_path = Path(help_path)
        return raw_path if raw_path.is_absolute() else (root / raw_path).resolve(strict=False)
    repo_path = assignment_repo_path(assignment, root=root)
    activity_id = clean_text(assignment.get("activity_id"), "")
    if repo_path is None or not activity_id:
        return None
    return student_help_service.help_log_path(repo_path, activity_id)


def help_history_block(label: str, value: Any, color: str, use_color: bool = False) -> list[str]:
    """Render one labelled, wrapped text block in the help history."""

    text = clean_text(value)
    wrapped = textwrap.wrap(text, width=68, break_long_words=True, break_on_hyphens=False) or ["-"]
    return [colorize(label, color, use_color), *(f"  {line}" for line in wrapped)]


def render_help_history(
    assignment: dict[str, Any],
    root: Path = PROJECT_ROOT,
    use_color: bool = False,
) -> str:
    """Render the help request history for one assignment."""

    lines = ["Storico richieste aiuto"]
    help_data = assignment.get("help") if isinstance(assignment.get("help"), dict) else {}
    payload_events = help_data.get("events")
    log_path = assignment_help_log_path(assignment, root=root)
    loaded_from_payload = isinstance(payload_events, list)
    if loaded_from_payload:
        events = [event for event in payload_events if isinstance(event, dict)]
        error = ""
    elif log_path is not None:
        events, error = student_help_service.read_help_log(log_path)
        if help_data.get("legacy_unverified") is True:
            events = [{**event, "source": "legacy-unverified"} for event in events]
    else:
        lines.append("Log aiuti non disponibile per questa consegna.")
        return "\n".join(lines)
    legacy_path_value = clean_text(help_data.get("legacy_path"), "")
    if legacy_path_value and not loaded_from_payload:
        raw_legacy_path = Path(legacy_path_value)
        legacy_path = raw_legacy_path if raw_legacy_path.is_absolute() else (root / raw_legacy_path).resolve(strict=False)
        if log_path is None or legacy_path.resolve(strict=False) != log_path.resolve(strict=False):
            legacy_events, legacy_error = student_help_service.read_help_log(legacy_path)
            if not legacy_error:
                events = [
                    *({**event, "source": "legacy-unverified"} for event in legacy_events),
                    *events,
                ]
    if error:
        lines.append(f"Log aiuti non leggibile: {error}")
        lines.append(f"Path: {log_path}")
        return "\n".join(lines)
    if not events:
        lines.append("Nessuna richiesta di aiuto registrata.")
        lines.append(f"Path: {log_path}")
        return "\n".join(lines)
    authoritative_events = [event for event in events if event.get("source") != "legacy-unverified"]
    legacy_events = [event for event in events if event.get("source") == "legacy-unverified"]
    groups = [("", authoritative_events)]
    if legacy_events:
        groups.append(("Legacy non verificati", legacy_events))
    request_index = 0
    for group_label, group_events in groups:
        if not group_events:
            continue
        if group_label:
            lines.extend(
                [
                    section_separator(),
                    colorize(group_label, HELP_REASON_COLOR, use_color),
                    "Questi eventi storici non incidono sul budget e sulle metriche del server.",
                ]
            )
        for event in group_events:
            request_index += 1
            decision = "consentita" if event.get("allowed") is True else "bloccata"
            decision_color = HELP_RESPONSE_COLOR if event.get("allowed") is True else HELP_ERROR_COLOR
            response = event.get("response") if isinstance(event.get("response"), dict) else {}
            provider_status = clean_text(event.get("provider_status"), "")
            lines.extend(
                [
                    section_separator(),
                    colorize(f"Richiesta {request_index}", HELP_REQUEST_COLOR, use_color),
                    detail_line("Data:", compact_datetime(event.get("requested_at"))),
                    detail_line("Tipo:", event.get("label")),
                    detail_line("Esito:", colorize(decision, decision_color, use_color), formatted=True),
                    *help_history_block("Prompt studente", event.get("prompt"), HELP_PROMPT_COLOR, use_color),
                ]
            )
            if provider_status == "pending":
                lines.extend(
                    help_history_block(
                        "Risposta in elaborazione",
                        "La richiesta e stata salvata. Il provider sta preparando la risposta.",
                        HELP_PROMPT_COLOR,
                        use_color,
                    )
                )
            elif response:
                provider_label = clean_text(response.get("provider_label")) or "Provider aiuto"
                if response.get("status") == "ready":
                    lines.extend(
                        help_history_block(
                            f"Risposta - {provider_label}",
                            response.get("message"),
                            HELP_RESPONSE_COLOR,
                            use_color,
                        )
                    )
                else:
                    lines.extend(
                        help_history_block(
                            f"Risposta non disponibile - {provider_label}",
                            response.get("detail"),
                            HELP_ERROR_COLOR,
                            use_color,
                        )
                    )
            lines.extend(help_history_block("Motivo della decisione", event.get("reason"), HELP_REASON_COLOR, use_color))
    lines.append(section_separator())
    return "\n".join(lines)


def record_help_from_tui(
    *,
    assignment: dict[str, Any],
    server_url: str,
    server_token: str,
    help_type: str,
    prompt: str,
    request_id: str = "",
    allow_insecure_http: bool = False,
) -> dict[str, Any]:
    """Send one student help request to the teacher-side server."""

    credential = _MemoryBearer(server_token)
    server_token = ""
    assignment_id = clean_text(assignment.get("assignment_id"), "")
    if not assignment_id:
        raise ValueError("Identificativo consegna non disponibile.")
    if not credential.value.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    clean_request_id = str(request_id or "").strip() or uuid.uuid4().hex
    body = json.dumps(
        {
            "assignment_id": assignment_id,
            "help_type": help_type,
            "prompt": prompt,
            "request_id": clean_request_id,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/help",
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {credential.value.strip()}",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )
    payload = None
    failure = None
    pending_failure = False
    try:
        payload = _student_api_json(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS)
    except (urllib.error.HTTPError, _StudentApiHttpStatusError) as error:
        pending_failure = error.code == 409
        failure = (
            "Server aiuti: richiesta gia salvata e ancora in elaborazione"
            if pending_failure
            else f"Server aiuti: richiesta rifiutata (HTTP {error.code})."
        )
    except urllib.error.URLError:
        failure = (
            f"Server non raggiungibile su {server_url}. "
            "Avvialo con scripts/course_board_server.py."
        )
    except TimeoutError:
        failure = "Il server aiuti non ha risposto entro il tempo previsto."
    except (json.JSONDecodeError, UnicodeDecodeError):
        failure = "Il server aiuti ha restituito una risposta non valida."
    else:
        if _contains_credential(payload, credential.value):
            payload = None
            failure = "Il server aiuti ha restituito una risposta non valida."
    finally:
        request = None
        response = None
        credential = None
    if failure is not None:
        if pending_failure:
            raise StudentHelpRequestPendingError(failure)
        raise ValueError(failure)
    event = payload.get("event") if isinstance(payload, dict) else None
    if not isinstance(event, dict):
        payload = None
        raise ValueError("Il server aiuti non ha restituito l'evento salvato.")
    payload = None
    return event


def fetch_help_history_from_server(
    *,
    assignment: dict[str, Any],
    server_url: str,
    server_token: str,
    allow_insecure_http: bool = False,
) -> dict[str, Any]:
    """Load one student's assignment history through the authenticated server API."""

    credential = _MemoryBearer(server_token)
    server_token = ""
    assignment_id = clean_text(assignment.get("assignment_id"), "")
    if not assignment_id:
        raise ValueError("Identificativo consegna non disponibile.")
    if not credential.value.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    query = urllib.parse.urlencode({"assignment_id": assignment_id})
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/help-history?{query}",
        headers={
            "Authorization": f"Bearer {credential.value.strip()}",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    payload = None
    failure = None
    try:
        payload = _student_api_json(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS)
    except (urllib.error.HTTPError, _StudentApiHttpStatusError) as error:
        failure = f"Server aiuti: richiesta rifiutata (HTTP {error.code})."
    except urllib.error.URLError:
        failure = f"Server non raggiungibile su {server_url}."
    except TimeoutError:
        failure = "Il server aiuti non ha risposto entro il tempo previsto."
    except (json.JSONDecodeError, UnicodeDecodeError):
        failure = "Il server aiuti ha restituito uno storico non valido."
    else:
        if _contains_credential(payload, credential.value):
            payload = None
            failure = "Il server aiuti ha restituito uno storico non valido."
    finally:
        request = None
        response = None
        credential = None
    if failure is not None:
        raise ValueError(failure)
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        payload = None
        raise ValueError("Il server aiuti ha restituito uno storico non valido.")
    return payload


def select_final_attempt_from_server(
    *,
    assignment: dict[str, Any],
    attempt_id: str,
    server_url: str,
    server_token: str,
    allow_insecure_http: bool = False,
) -> dict[str, Any]:
    """Select one final attempt through the authenticated student API."""

    credential = _MemoryBearer(server_token)
    server_token = ""
    assignment_id = clean_text(assignment.get("assignment_id"), "")
    if not assignment_id:
        raise ValueError("Identificativo consegna non disponibile.")
    if not credential.value.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    body = json.dumps(
        {
            "assignment_id": assignment_id,
            "attempt_id": clean_text(attempt_id, ""),
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/final-attempt",
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {credential.value.strip()}",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )
    payload = None
    failure = None
    try:
        payload = _student_api_json(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS)
    except (urllib.error.HTTPError, _StudentApiHttpStatusError) as error:
        failure = f"Server tentativi: richiesta rifiutata (HTTP {error.code})."
    except urllib.error.URLError:
        failure = f"Server non raggiungibile su {server_url}."
    except TimeoutError:
        failure = "Il server tentativi non ha risposto entro il tempo previsto."
    except (json.JSONDecodeError, UnicodeDecodeError):
        failure = "Il server tentativi ha restituito una risposta non valida."
    else:
        if _contains_credential(payload, credential.value):
            payload = None
            failure = "Il server tentativi ha restituito una risposta non valida."
    finally:
        request = None
        response = None
        credential = None
    if failure is not None:
        raise ValueError(failure)
    selected = payload.get("assignment") if isinstance(payload, dict) else None
    if not isinstance(selected, dict):
        payload = None
        raise ValueError("Il server tentativi non ha restituito la consegna aggiornata.")
    payload = None
    return selected


def _contains_credential(value: Any, credential: str, depth: int = 0) -> bool:
    try:
        if depth > 32:
            return True
        if isinstance(value, str):
            return bool(credential) and credential in value
        if isinstance(value, dict):
            return any(
                _contains_credential(key, credential, depth + 1)
                or _contains_credential(item, credential, depth + 1)
                for key, item in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(_contains_credential(item, credential, depth + 1) for item in value)
        return False
    finally:
        value = None
        credential = ""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep bearer credentials confined to the original student API URL."""

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


_STUDENT_API_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def student_api_urlopen(request: urllib.request.Request, *, timeout: float):
    """Open an authenticated student API request without following redirects."""

    return _STUDENT_API_OPENER.open(request, timeout=timeout)


_DEFAULT_STUDENT_API_URLOPEN = student_api_urlopen


class _StudentApiHttpStatusError(RuntimeError):
    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__("Student API HTTP error.")


def _student_api_json(request: urllib.request.Request, *, timeout: float):
    if student_api_urlopen is not _DEFAULT_STUDENT_API_URLOPEN:
        with student_api_urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    return _student_api_json_subprocess(request, timeout=timeout)


def _student_api_json_subprocess(request: urllib.request.Request, *, timeout: float):
    specification = json.dumps(
        {
            "url": request.full_url,
            "data": base64.b64encode(request.data or b"").decode("ascii"),
            "headers": list(request.header_items()),
            "method": request.get_method(),
            "timeout": timeout,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    stdout = None
    failure = False
    try:
        returncode, stdout = thebitlab_tui_pairing_client._run_killable_subprocess(
            [sys.executable, str(Path(__file__).resolve()), "--student-api-worker"],
            specification,
            environment=thebitlab_tui_pairing_client._transport_environment(),
            timeout=timeout,
        )
        if (
            returncode != 0
            or type(stdout) is not bytes
            or len(stdout) > MAX_STUDENT_API_RESPONSE_BYTES * 2 + 4096
        ):
            failure = True
    except Exception:
        failure = True
    finally:
        request = None
        specification = None
    if failure:
        stdout = None
        raise urllib.error.URLError("student API unavailable")
    try:
        outcome = json.loads(stdout.decode("utf-8"), object_pairs_hook=_unique_json_object)
    finally:
        stdout = None
    if type(outcome) is not list or len(outcome) != 2:
        outcome = None
        raise urllib.error.URLError("student API unavailable")
    kind, value = outcome
    outcome = None
    if kind == "http" and type(value) is int and not isinstance(value, bool):
        raise _StudentApiHttpStatusError(value)
    if kind != "ok":
        value = None
        raise urllib.error.URLError("student API unavailable")
    return value


def _run_student_api_worker() -> int:
    request = None
    raw = None
    outcome = ["error", None]
    try:
        raw = sys.stdin.buffer.read(65537)
        if len(raw) > 65536:
            raise ValueError("specification")
        specification = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
        if type(specification) is not dict or set(specification) != {
            "url", "data", "headers", "method", "timeout"
        }:
            raise ValueError("specification")
        data = base64.b64decode(specification["data"], validate=True)
        headers = specification["headers"]
        if type(headers) is not list or any(
            type(item) is not list
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
            for item in headers
        ):
            raise ValueError("headers")
        request = urllib.request.Request(
            specification["url"],
            data=data,
            headers=dict(headers),
            method=specification["method"],
        )
        try:
            with _STUDENT_API_OPENER.open(
                request,
                timeout=float(specification["timeout"]),
            ) as response:
                body = response.read(MAX_STUDENT_API_RESPONSE_BYTES + 1)
            if len(body) > MAX_STUDENT_API_RESPONSE_BYTES:
                raise ValueError("response")
            payload = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_json_object)
            outcome = ["ok", payload]
        except urllib.error.HTTPError as error:
            outcome = ["http", error.code]
            error.close()
    except Exception:
        pass
    finally:
        request = None
        raw = None
    encoded = json.dumps(outcome, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_STUDENT_API_RESPONSE_BYTES * 2 + 4096:
        return 1
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
    outcome = None
    encoded = None
    return 0


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def help_result_message(event: dict[str, Any], use_color: bool = False) -> str:
    """Return a structured result after recording a help request."""

    allowed = event.get("allowed") is True
    status = "consentita" if allowed else "bloccata"
    status_color = HELP_RESPONSE_COLOR if allowed else HELP_ERROR_COLOR
    lines = [
        colorize("Esito richiesta aiuto", HELP_REQUEST_COLOR, use_color),
        section_separator(),
        detail_line("Tipo:", event.get("label")),
        detail_line("Esito:", colorize(status, status_color, use_color), formatted=True),
    ]
    response = event.get("response") if isinstance(event.get("response"), dict) else {}
    if response.get("status") == "ready":
        provider_label = clean_text(response.get("provider_label"), "Provider aiuto")
        lines.extend(
            help_history_block(
                f"Risposta - {provider_label}",
                response.get("message"),
                HELP_RESPONSE_COLOR,
                use_color,
            )
        )
    elif response:
        provider_label = clean_text(response.get("provider_label"), "Provider aiuto")
        lines.extend(
            help_history_block(
                f"Risposta non disponibile - {provider_label}",
                response.get("detail"),
                HELP_ERROR_COLOR,
                use_color,
            )
        )
    if not allowed or not response:
        lines.extend(help_history_block("Motivo", event.get("reason"), HELP_REASON_COLOR, use_color))
    lines.extend(
        [
            section_separator(),
            f"Richiesta salvata. Usa {colorize('h', HELP_REQUEST_COLOR, use_color)} per rileggerla nello storico.",
        ]
    )
    return "\n".join(lines)


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


_FOLDER_CAPABLE_EDITORS = frozenset(
    {
        "code",
        "code-insiders",
        "code-oss",
        "codium",
        "vscodium",
        "cursor",
        "zed",
        "fleet",
        "subl",
        "atom",
        "gedit",
        "kate",
        "mousepad",
        "notepadqq",
        "geany",
        "brackets",
    }
)


def _is_folder_capable_editor(command: list[str]) -> bool:
    if not command:
        return False
    basename = Path(command[0]).stem.lower()
    return basename in _FOLDER_CAPABLE_EDITORS


def _open_file_manager(path: Path) -> None:
    """Open a folder with the platform file manager."""

    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, str(path)])


def open_workspace(
    path_value: str,
    root: Path = PROJECT_ROOT,
    workspace_editor: str | None = None,
) -> tuple[bool, str]:
    """Open a workspace folder with the configured editor or the file manager."""

    raw_path = Path(path_value)
    path = raw_path if raw_path.is_absolute() else (root / raw_path).resolve(strict=False)
    if not path.is_dir():
        return False, "Workspace non disponibile."

    explicit_workspace_editor = str(
        workspace_editor or os.environ.get("THEBITLAB_WORKSPACE_EDITOR", "")
    ).strip()
    explicit_editor = str(os.environ.get("THEBITLAB_EDITOR", "")).strip()

    for candidate in (explicit_workspace_editor, explicit_editor):
        if not candidate:
            continue
        command = editor_command(candidate)
        if command is None:
            continue
        if _is_folder_capable_editor(command):
            try:
                subprocess.run([*command, str(path)], cwd=str(path), check=False)
                return True, f"Aperto in {command[0]}."
            except OSError as error:
                return False, f"Editor non avviabile: {error}"

    _open_file_manager(path)
    return True, "Cartella aperta."


EDITOR_CANDIDATES = ("micro", "nvim", "vim", "hx", "nano")
WINDOWS_EDITOR_CANDIDATES = EDITOR_CANDIDATES + ("notepad",)


def editor_command(editor: str | None = None) -> list[str] | None:
    """Resolve the configured editor without adding a Python dependency."""

    configured = str(editor or os.environ.get("THEBITLAB_EDITOR", "")).strip()
    if configured:
        try:
            command = shlex.split(configured, posix=os.name != "nt")
        except ValueError:
            return None
        if not command or shutil.which(command[0]) is None:
            return None
        return command
    candidates = WINDOWS_EDITOR_CANDIDATES if os.name == "nt" else EDITOR_CANDIDATES
    for candidate in candidates:
        if shutil.which(candidate):
            return [candidate]
    return None


def _first_openable_source(workspace: Path) -> Path | None:
    """Return a reasonable source file to open when no explicit source is given."""

    if not workspace.is_dir():
        return None
    preferred = ("README.md", "readme.md", "main.c", "main.py")
    for name in preferred:
        candidate = workspace / name
        if candidate.is_file():
            return candidate
    for candidate in sorted(workspace.iterdir()):
        if candidate.is_file() and not candidate.name.startswith("."):
            return candidate
    return None


def _windows_terminal_command(path: Path) -> tuple[list[str], dict[str, str], str]:
    wt = shutil.which("wt") or shutil.which("wt.exe")
    if wt:
        return [wt, "-d", str(path)], {}, "Terminale Windows aperto."
    return ["cmd"], {"cwd": str(path)}, "Prompt dei comandi aperto."


def _macos_terminal_command(path: Path) -> tuple[list[str], dict[str, str], str]:
    return ["open", "-a", "Terminal", "."], {"cwd": str(path)}, "Terminale aperto."


def _linux_terminal_commands(path: Path) -> list[tuple[list[str], dict[str, str], str]]:
    return [
        (["gnome-terminal", "--working-directory", str(path)], {"cwd": str(path)}, "gnome-terminal"),
        (["konsole", "--workdir", str(path)], {"cwd": str(path)}, "konsole"),
        (["xfce4-terminal", "--working-directory", str(path)], {"cwd": str(path)}, "xfce4-terminal"),
        (["kitty", "--directory", str(path)], {"cwd": str(path)}, "kitty"),
        (["alacritty", "--working-directory", str(path)], {"cwd": str(path)}, "alacritty"),
        (["xterm", "-cd", str(path)], {"cwd": str(path)}, "xterm"),
    ]


def open_terminal(path_value: str, root: Path = PROJECT_ROOT) -> tuple[bool, str]:
    """Open a terminal in the workspace directory.

    On Windows prefer Windows Terminal (`wt -d <dir>`); fall back to cmd.
    On macOS open Terminal.app; on Linux try common terminal emulators.
    """

    raw_path = Path(path_value)
    path = raw_path if raw_path.is_absolute() else (root / raw_path).resolve(strict=False)
    if not path.is_dir():
        return False, "Workspace non disponibile."

    if os.name == "nt":
        command, kwargs, message = _windows_terminal_command(path)
    elif sys.platform == "darwin":
        command, kwargs, message = _macos_terminal_command(path)
    else:
        for command, kwargs, message in _linux_terminal_commands(path):
            if shutil.which(command[0]):
                try:
                    subprocess.Popen(command, **kwargs)
                    return True, f"Terminale aperto ({message})."
                except OSError:
                    continue
        return False, "Nessun terminale disponibile."

    try:
        subprocess.Popen(command, **kwargs)
        return True, message
    except OSError as error:
        return False, f"Terminale non avviabile: {error}"


def open_editor(
    workspace_path: str,
    source_name: str = "",
    root: Path = PROJECT_ROOT,
    editor: str | None = None,
) -> tuple[bool, str]:
    """Open the activity source with a user-selected terminal editor."""

    raw_workspace = Path(workspace_path)
    workspace = raw_workspace if raw_workspace.is_absolute() else (root / raw_workspace).resolve(strict=False)
    if not workspace.is_dir():
        return False, "Workspace non disponibile."
    command = editor_command(editor)
    if command is None:
        return False, "Nessun editor disponibile. Imposta THEBITLAB_EDITOR o installa micro."
    source = clean_text(source_name, "")
    target = workspace / source if source else None
    if target is None or not target.is_file():
        target = _first_openable_source(workspace)
    if target is None:
        return False, "Nessun file sorgente apribile nel workspace."
    try:
        subprocess.run([*command, str(target)], cwd=str(workspace), check=False)
    except OSError as error:
        return False, f"Editor non avviabile: {error}"
    return True, f"Editor chiuso: {command[0]}"


def load_payload(root: Path, student_id: str, now: str | None = None) -> dict[str, Any]:
    """Load the current student lab payload."""

    return student_lab_service.student_lab_payload(
        root=root,
        student_id=student_id,
        now=now,
        expose_external_paths=True,
    )


def fetch_student_lab_payload(
    *,
    server_url: str,
    server_token: str,
    now: str | None = None,
    allow_insecure_http: bool = False,
) -> dict[str, Any]:
    """Load the authenticated student-lab payload from the teacher server."""

    credential = _MemoryBearer(server_token)
    server_token = ""
    if not credential.value.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    query = urllib.parse.urlencode({"now": now}) if now else ""
    suffix = f"?{query}" if query else ""
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/assignments{suffix}",
        headers={
            "Authorization": f"Bearer {credential.value.strip()}",
            "User-Agent": _USER_AGENT,
        },
    )
    payload = None
    failure = None
    try:
        payload = _student_api_json(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS)
    except (urllib.error.HTTPError, _StudentApiHttpStatusError) as error:
        failure = f"Server consegne: richiesta rifiutata (HTTP {error.code})."
    except urllib.error.URLError:
        failure = f"Server non raggiungibile su {server_url}."
    except TimeoutError:
        failure = "Il server consegne non ha risposto entro il tempo previsto."
    except (json.JSONDecodeError, UnicodeDecodeError):
        failure = "Il server consegne ha restituito una risposta non valida."
    else:
        if _contains_credential(payload, credential.value):
            payload = None
            failure = "Il server consegne ha restituito una risposta non valida."
    finally:
        request = None
        response = None
        credential = None
    if failure is not None:
        raise ValueError(failure)
    if not isinstance(payload, dict) or not isinstance(payload.get("assignments"), list):
        payload = None
        raise ValueError("Il server consegne ha restituito un payload non valido.")
    return payload


def load_current_payload(
    *,
    root: Path,
    student_id: str,
    now: str | None,
    server_url: str,
    server_token: str,
    allow_insecure_http: bool,
) -> dict[str, Any]:
    """Load authoritative server data when authenticated, otherwise local data."""

    credential = _MemoryBearer(server_token)
    server_token = ""
    if credential.value.strip():
        remote_payload = fetch_student_lab_payload(
            server_url=server_url,
            server_token=credential.value,
            now=now,
            allow_insecure_http=allow_insecure_http,
        )
        try:
            local_payload = load_payload(root, student_id, now)
        except Exception:  # Local paths are an optional operational enhancement.
            return remote_payload
        return merge_local_operational_paths(remote_payload, local_payload)
    return load_payload(root, student_id, now)


def merge_local_operational_paths(
    remote_payload: dict[str, Any],
    local_payload: dict[str, Any],
) -> dict[str, Any]:
    """Enrich authoritative remote assignments with matching trusted local paths."""

    remote_student_id = clean_text(remote_payload.get("student_id"), "")
    local_student_id = clean_text(local_payload.get("student_id"), "")
    if not remote_student_id or remote_student_id != local_student_id:
        return remote_payload
    local_by_id = {
        clean_text(item.get("assignment_id"), ""): item
        for item in payload_assignments(local_payload)
        if isinstance(item, dict) and clean_text(item.get("assignment_id"), "")
    }
    merged_payload = dict(remote_payload)
    merged_assignments: list[Any] = []
    for remote_assignment in payload_assignments(remote_payload):
        if not isinstance(remote_assignment, dict):
            merged_assignments.append(remote_assignment)
            continue
        merged_assignment = dict(remote_assignment)
        assignment_id = clean_text(remote_assignment.get("assignment_id"), "")
        local_assignment = local_by_id.get(assignment_id)
        if isinstance(local_assignment, dict):
            for section_name in ("workspace", "activity", "report"):
                remote_section = remote_assignment.get(section_name)
                local_section = local_assignment.get(section_name)
                if not isinstance(remote_section, dict) or not isinstance(local_section, dict):
                    continue
                local_path = clean_text(local_section.get("path"), "")
                if not local_path:
                    continue
                merged_section = dict(remote_section)
                merged_section["path"] = local_path
                merged_section["exists"] = local_section.get("exists") is True
                merged_assignment[section_name] = merged_section
        merged_assignments.append(merged_assignment)
    merged_payload["assignments"] = merged_assignments
    return merged_payload


def payload_assignments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return assignment items from a student lab payload."""

    assignments = payload.get("assignments")
    return assignments if isinstance(assignments, list) else []


def find_assignment(payload: dict[str, Any], assignment_id: str, fallback_index: int) -> dict[str, Any] | None:
    """Return the selected assignment after a payload reload."""

    assignments = payload_assignments(payload)
    clean_assignment_id = clean_text(assignment_id, "")
    if clean_assignment_id:
        for assignment in assignments:
            if isinstance(assignment, dict) and clean_text(assignment.get("assignment_id"), "") == clean_assignment_id:
                return assignment
        return None
    if 0 <= fallback_index < len(assignments):
        assignment = assignments[fallback_index]
        return assignment if isinstance(assignment, dict) else None
    return None


def run_tui(
    *,
    student_id: str,
    root: Path = PROJECT_ROOT,
    now: str | None = None,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
    clear: bool = True,
    use_color: bool = False,
    server_url: str = DEFAULT_SERVER_URL,
    server_token: str = "",
    allow_insecure_http: bool = False,
    backend: str = "local",
    timeout_seconds: int = student_lab_runner.DEFAULT_TIMEOUT_SECONDS,
    docker_image: str = student_lab_runner.DEFAULT_DOCKER_IMAGE,
    renderer: str = "auto",
    interactive: bool | None = None,
) -> int:
    """Run the interactive student lab loop."""

    memory_bearer = _MemoryBearer(server_token)
    server_token = ""
    selected_renderer = resolve_tui_renderer(renderer, interactive=interactive)
    payload = load_current_payload(
        root=root,
        student_id=student_id,
        now=now,
        server_url=server_url,
        server_token=memory_bearer.value,
        allow_insecure_http=allow_insecure_http,
    )
    pending_help_request_ids: dict[tuple[str, str, str], str] = {}
    while True:
        if clear:
            clear_screen()
        print_fn(render_assignment_list(payload, use_color=use_color))
        choice = input_fn("\nScelta: ").strip().lower()
        if choice in {"q", "quit", "esci"}:
            return 0
        if choice in {"r", "reload", "ricarica"}:
            try:
                payload = load_current_payload(
                    root=root,
                    student_id=student_id,
                    now=now,
                    server_url=server_url,
                    server_token=memory_bearer.value,
                    allow_insecure_http=allow_insecure_http,
                )
            except ValueError as error:
                print_fn(f"Aggiornamento dati non disponibile:\n{error}")
                input_fn("Premi invio per continuare...")
            continue
        if not choice.isdigit():
            continue
        index = int(choice) - 1
        assignments = payload_assignments(payload)
        if index < 0 or index >= len(assignments):
            continue
        selected_assignment_id = clean_text(assignments[index].get("assignment_id"), "")
        dashboard_offset = 0
        while True:
            assignment = find_assignment(payload, selected_assignment_id, index)
            if assignment is None:
                print_fn("Consegna non più disponibile.")
                input_fn("Premi invio per tornare alla lista...")
                break
            if clear:
                clear_screen()
            rendered_with = ["utui" if selected_renderer == "auto" else selected_renderer]
            print_fn(
                render_assignment_view(
                    assignment,
                    use_color=use_color,
                    layout=student_lab_layout.load_layout(root),
                    renderer=selected_renderer,
                    interaction={
                        "dashboard_offset": dashboard_offset,
                        "expand_sections": True,
                    },
                    renderer_observer=lambda actual: rendered_with.__setitem__(0, actual),
                )
            )
            actual_renderer = rendered_with[0]
            if selected_renderer == "auto" and actual_renderer == "legacy":
                selected_renderer = "legacy"
            if actual_renderer == "utui":
                print_fn(render_utui_detail_commands())
            action = input_fn("\nDettaglio: ").strip().lower()
            if action in {"", "b", "back", "indietro"}:
                break
            if action in {"q", "quit", "esci"}:
                return 0
            if actual_renderer == "utui" and action in {"j", "down", "giu"}:
                dashboard_offset += 5
                continue
            if actual_renderer == "utui" and action in {"k", "up", "su"}:
                dashboard_offset = max(0, dashboard_offset - 5)
                continue
            if action == "o":
                workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
                ok, message = open_workspace(clean_text(workspace.get("path"), ""), root=root)
                if not ok:
                    print_fn(message or "Workspace non disponibile.")
                else:
                    print_fn(message)
                input_fn("Premi invio per continuare...")
                continue
            if action == "v":
                workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
                activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
                _, message = open_editor(
                    clean_text(workspace.get("path"), ""),
                    clean_text(activity.get("source_name"), ""),
                    root=root,
                )
                print_fn(message)
                input_fn("Premi invio per continuare...")
                continue
            if action == "c":
                workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
                ok, message = open_terminal(clean_text(workspace.get("path"), ""), root=root)
                if not ok:
                    print_fn(message or "Terminale non disponibile.")
                else:
                    print_fn(message)
                input_fn("Premi invio per continuare...")
                continue
            if action in {"l", "layout"}:
                layout_renderer = None
                if selected_renderer != "legacy":
                    layout_renderer = lambda current, width, height: render_assignment_view(
                        assignment,
                        use_color=use_color,
                        layout=current,
                        renderer=selected_renderer,
                        terminal_width=width,
                        terminal_height=height,
                    )
                student_lab_layout.run_layout_editor(
                    render_assignment_detail(assignment, use_color=use_color).splitlines(),
                    root=root,
                    use_color=use_color,
                    clear=clear,
                    print_fn=print_fn,
                    layout_renderer=layout_renderer,
                )
                continue
            if action == "a":
                print_fn(f"Tipo aiuto: {help_choice_label()} | invio/b annulla")
                help_choice = input_fn("Tipo: ").strip().lower()
                if help_choice in {"", "b", "back", "indietro"}:
                    print_fn("Richiesta aiuto annullata.")
                elif help_choice not in HELP_MENU:
                    print_fn("Tipo aiuto non valido. Usa 1, 2, 3, invio o b.")
                else:
                    help_type = HELP_MENU.get(help_choice, help_choice)
                    prompt = input_fn("Scrivi la richiesta: ").strip()
                    if not prompt:
                        print_fn("Richiesta aiuto annullata: prompt vuoto.")
                    else:
                        request_key = (selected_assignment_id, help_type, prompt)
                        request_id = pending_help_request_ids.setdefault(request_key, uuid.uuid4().hex)
                        try:
                            event = record_help_from_tui(
                                assignment=assignment,
                                server_url=server_url,
                                server_token=memory_bearer.value,
                                help_type=help_type,
                                prompt=prompt,
                                request_id=request_id,
                                allow_insecure_http=allow_insecure_http,
                            )
                        except StudentHelpRequestPendingError as error:
                            print_fn(f"Richiesta aiuto gia salvata e ancora in elaborazione:\n{error}")
                        except ValueError as error:
                            print_fn(f"Richiesta aiuto non salvata:\n{error}")
                        else:
                            pending_help_request_ids.pop(request_key, None)
                            print_fn(help_result_message(event, use_color=use_color))
                            try:
                                payload = load_current_payload(
                                    root=root,
                                    student_id=student_id,
                                    now=now,
                                    server_url=server_url,
                                    server_token=memory_bearer.value,
                                    allow_insecure_http=allow_insecure_http,
                                )
                            except ValueError as error:
                                print_fn(
                                    "Richiesta salvata, ma aggiornamento dati non disponibile:\n"
                                    f"{error}"
                                )
                input_fn("Premi invio per continuare...")
                continue
            if action == "h":
                try:
                    if memory_bearer.value.strip():
                        history = fetch_help_history_from_server(
                            assignment=assignment,
                            server_url=server_url,
                            server_token=memory_bearer.value,
                            allow_insecure_http=allow_insecure_http,
                        )
                        history_assignment = {**assignment, "help": {"events": history["events"]}}
                        print_fn(render_help_history(history_assignment, root=root, use_color=use_color))
                    else:
                        print_fn(render_help_history(assignment, root=root, use_color=use_color))
                except ValueError as error:
                    print_fn(f"Storico aiuti non disponibile:\n{error}")
                input_fn("Premi invio per continuare...")
                continue
            if action == "t":
                print_fn(render_attempt_history(assignment, use_color=use_color))
                items = selectable_attempts(assignment)
                choice = input_fn("Tentativo definitivo: ").strip().lower()
                if choice in {"", "b", "back", "indietro"}:
                    print_fn("Selezione tentativo annullata.")
                elif not choice.isdigit() or not 1 <= int(choice) <= len(items):
                    print_fn("Tentativo non valido. Usa uno dei numeri mostrati, invio o b.")
                else:
                    selected_attempt = items[int(choice) - 1]
                    attempt_id = (
                        clean_text(selected_attempt.get("id"), "")
                        if isinstance(selected_attempt, dict)
                        else ""
                    )
                    try:
                        if memory_bearer.value.strip():
                            select_final_attempt_from_server(
                                assignment=assignment,
                                attempt_id=attempt_id,
                                server_url=server_url,
                                server_token=memory_bearer.value,
                                allow_insecure_http=allow_insecure_http,
                            )
                        else:
                            student_lab_service.select_student_final_attempt(
                                root=root,
                                student_id=student_id,
                                assignment_id=selected_assignment_id,
                                attempt_id=attempt_id,
                                now=now,
                            )
                        payload = load_current_payload(
                            root=root,
                            student_id=student_id,
                            now=now,
                            server_url=server_url,
                            server_token=memory_bearer.value,
                            allow_insecure_http=allow_insecure_http,
                        )
                    except ValueError as error:
                        print_fn(f"Tentativo definitivo non salvato:\n{error}")
                    else:
                        print_fn("Tentativo definitivo salvato.")
                input_fn("Premi invio per continuare...")
                continue
            if action == "e":
                try:
                    report = student_lab_runner.run_assignment(
                        assignment,
                        root=root,
                        backend=backend,
                        timeout_seconds=timeout_seconds,
                        docker_image=docker_image,
                    )
                    report_path = student_lab_runner.write_student_report(root, assignment, report)
                except ValueError as error:
                    print_fn(f"Runner non disponibile:\n{error}")
                else:
                    print_fn(runner_result_message(report, report_path, use_color=use_color))
                    try:
                        payload = load_current_payload(
                            root=root,
                            student_id=student_id,
                            now=now,
                            server_url=server_url,
                            server_token=memory_bearer.value,
                            allow_insecure_http=allow_insecure_http,
                        )
                    except ValueError as error:
                        print_fn(
                            "Report salvato, ma aggiornamento dati non disponibile:\n"
                            f"{error}"
                        )
                input_fn("Premi invio per continuare...")


def _fetch_student_id(server_url: str, server_token: str) -> str:
    """Ask the server for the authenticated student's identifier."""

    url = validated_server_url(server_url) + "/api/student-lab/me"
    request = urllib.request.Request(
        url,
        headers={"Authorization": "Bearer " + server_token, "User-Agent": _USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    student_id = payload.get("student_id") if isinstance(payload, dict) else None
    if not isinstance(student_id, str):
        raise ValueError("Il server non ha restituito l'identificativo studente.")
    return student_help_auth.validate_student_id(student_id)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the student lab TUI."""

    parser = argparse.ArgumentParser(description="Apri la TUI minima del lab studente.")
    parser.add_argument(
        "--student-id",
        help=(
            "Identificativo studente, per esempio rossi-mario. "
            "Se omesso, viene recuperato automaticamente dal server dopo il pairing."
        ),
    )
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Root del repository TheBitLab.")
    parser.add_argument("--now", help="Data ISO da usare per calcolare scadenze e mancanti.")
    parser.add_argument("--no-clear", action="store_true", help="Non pulire lo schermo tra una vista e l'altra.")
    parser.add_argument("--no-color", action="store_true", help="Disabilita colori ANSI.")
    parser.add_argument(
        "--renderer",
        choices=sorted(TUI_RENDERERS),
        default=os.environ.get("THEBITLAB_TUI_RENDERER", "auto"),
        help="Renderer dettaglio: auto usa utui se disponibile, legacy conserva quello storico.",
    )
    parser.add_argument(
        "--backend",
        choices=sorted(student_lab_runner.RUNNER_BACKENDS),
        default="local",
        help="Backend del runner da usare per il comando esegui test.",
    )
    parser.add_argument(
        "--docker-image",
        default=student_lab_runner.DEFAULT_DOCKER_IMAGE,
        help="Immagine Docker da usare quando il backend e docker.",
    )
    parser.add_argument(
        "--timeout",
        type=student_lab_runner.positive_int,
        default=student_lab_runner.DEFAULT_TIMEOUT_SECONDS,
        help="Timeout del runner in secondi.",
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("THEBITLAB_SERVER_URL", DEFAULT_SERVER_URL),
        help="URL del server locale che gestisce richieste di aiuto e provider Codex.",
    )
    parser.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help="Consenti HTTP remoto solo per un collaudo legacy controllato; il pairing richiede sempre HTTPS.",
    )
    parser.add_argument(
        "--pair-browser",
        action="store_true",
        help="Autentica questa esecuzione nel browser e conserva il bearer TUI soltanto in memoria.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the student lab TUI from the command line."""

    args = parse_args()
    server_token = os.environ.get("THEBITLAB_STUDENT_HELP_TOKEN", "")
    credential = None
    exit_code = 1
    try:
        if args.pair_browser:
            if server_token.strip():
                raise ValueError(
                    "Rimuovi THEBITLAB_STUDENT_HELP_TOKEN quando usi --pair-browser."
                )
            credential = thebitlab_tui_pairing_client.acquire_tui_bearer(args.server_url)
            server_token = credential.bearer_token
        student_id = args.student_id
        if student_id is None:
            if not server_token.strip():
                raise ValueError(
                    "Specifica --student-id oppure autentica la TUI con --pair-browser o THEBITLAB_STUDENT_HELP_TOKEN."
                )
            student_id = _fetch_student_id(args.server_url, server_token)
        exit_code = run_tui(
            student_id=student_id,
            root=args.root.resolve(strict=False),
            now=args.now,
            clear=not args.no_clear,
            use_color=supports_color(args.no_color),
            server_url=args.server_url,
            server_token=server_token,
            allow_insecure_http=args.allow_insecure_http,
            backend=args.backend,
            timeout_seconds=args.timeout,
            docker_image=args.docker_image,
            renderer=args.renderer,
        )
    except ValueError as error:
        print(f"Lab studente non disponibile:\n{error}", file=sys.stderr)
        exit_code = 1
    finally:
        server_token = ""
        if credential is not None:
            try:
                thebitlab_tui_pairing_client.revoke_tui_bearer(
                    args.server_url,
                    credential,
                )
            except ValueError as error:
                print(
                    "Attenzione: sessione TUI remota non revocata:\n"
                    f"{error}",
                    file=sys.stderr,
                )
                exit_code = 1
            finally:
                credential = None
    return exit_code


if __name__ == "__main__":
    raise SystemExit(
        _run_student_api_worker()
        if sys.argv[1:] == ["--student-api-worker"]
        else main()
    )
