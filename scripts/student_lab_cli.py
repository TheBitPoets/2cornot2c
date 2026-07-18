from __future__ import annotations

import argparse
import ipaddress
import json
import os
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import student_help_service, student_lab_runner, student_lab_service


InputFn = Callable[[str], str]
PrintFn = Callable[[str], None]
DEFAULT_SERVER_URL = "http://127.0.0.1:8765"
HELP_REQUEST_TIMEOUT_SECONDS = 150


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
RESET_COLOR = "\033[0m"


def clean_text(value: Any, fallback: str = "-") -> str:
    """Return a compact label for terminal output."""

    text = str(value or "").strip()
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


def ai_budget_label(value: Any) -> str:
    """Return a compact AI budget summary."""

    if not isinstance(value, dict):
        return "-"
    limit = value.get("limit")
    used = value.get("used")
    remaining = value.get("remaining")
    if not limit:
        return "non disponibile"
    label = f"{used or 0}/{limit} usate, {remaining or 0} rimanenti"
    return f"{label} (esaurito)" if value.get("exhausted") else label


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


def section_separator(width: int = 72) -> str:
    """Return a subtle separator for detail sections."""

    return "-" * width


def guide_term(text: str, use_color: bool = False) -> str:
    """Return a highlighted guide term for the detail view."""

    return colorize(text, GUIDE_TERM_COLORS.get(text.lower(), ""), use_color)


def guide_label(text: str, use_color: bool = False) -> str:
    """Return a padded guide term with optional coloring."""

    return colorize(f"{text:<9}", GUIDE_TERM_COLORS.get(text.lower(), ""), use_color)


def test_result_label(test: dict[str, Any]) -> str:
    """Return a compact label for one test result."""

    if test.get("passed") is True:
        return "[ok]"
    if test.get("passed") is False:
        return "[ko]"
    status = clean_text(test.get("status"), "")
    return f"[{status}]" if status else "[?]"


def test_result_detail(test: dict[str, Any]) -> str:
    """Return the first useful detail for one test result."""

    for key in ("detail", "message", "error", "stderr", "stdout"):
        value = clean_text(test.get(key), "")
        if value:
            return " ".join(value.split())
    return ""


def render_test_details(report: dict[str, Any]) -> list[str]:
    """Render test details from a runner report."""

    tests = report.get("tests")
    if not isinstance(tests, list) or not tests:
        return ["Dettaglio test", "  non disponibile nel report"]
    lines = ["Dettaglio test"]
    for index, item in enumerate(tests, start=1):
        if not isinstance(item, dict):
            continue
        name = clean_text(item.get("name"), f"test {index}")
        lines.append(f"  {test_result_label(item)} {name}")
        detail = test_result_detail(item)
        if detail and item.get("passed") is not True:
            lines.append(f"      {truncate(detail, 96)}")
    if len(lines) == 1:
        lines.append("  non disponibile nel report")
    return lines


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
        section_separator(),
        detail_line("Titolo:", assignment.get("title") or assignment.get("activity_id")),
        detail_line("Activity:", assignment.get("activity_id")),
        detail_line("Assegnazione:", assignment.get("assignment_id")),
        detail_line("Classe:", assignment.get("class_label") or assignment.get("class_id")),
        detail_line("Assegnata:", compact_datetime(assignment.get("assigned_at"))),
        detail_line("Scadenza:", compact_datetime(assignment.get("due_at"))),
        detail_line("Stato:", colored_status(clean_text(assignment.get("status")), use_color)),
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
        detail_line("AI budget:", ai_budget_label(help_summary.get("ai_budget"))),
        detail_line("Ultima:", compact_datetime(help_summary.get("last_requested_at"))),
        detail_line("Esito ultima:", help_summary.get("last_decision")),
        section_separator(),
        "Report",
        detail_line("Path:", report.get("path")),
        detail_line("Esiste:", "si" if report.get("exists") else "no"),
        detail_line("Consegnata:", compact_datetime(report.get("submitted_at"))),
        detail_line("Commit:", report.get("commit")),
        *(
            [
                section_separator(),
                "Ultimo dettaglio test",
                *render_test_details({"tests": report.get("tests")})[1:],
            ]
            if report.get("exists")
            else []
        ),
        section_separator(),
        "Grading",
        detail_line("Stato:", grading_label(grading)),
        detail_line("Voto:", grading.get("teacher_grade") if grading.get("teacher_grade") is not None else grading.get("score")),
        section_separator(),
        "Runner",
        detail_line("Stato:", runner.get("status")),
        detail_line("Backend:", runner.get("backend")),
        section_separator(),
        "Guida rapida",
        f"  {guide_label('Consegna', use_color)} lavoro assegnato dal docente.",
        f"  {guide_label('Workspace', use_color)} cartella locale dove modifichi i file.",
        f"  {guide_label('Test', use_color)} controlli automatici sul tuo lavoro.",
        f"  {guide_label('Report', use_color)} risultato salvato e letto da dashboard/registro.",
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
        "  o  Apri workspace",
        "",
        "Altri comandi",
        "  h  Storico aiuti",
        "  b  Torna alla lista",
        "  invio  Torna alla lista",
        "  q  Esci",
    ]
    return "\n".join(lines)


def runner_result_message(report: dict[str, Any], report_path: Path) -> str:
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
            detail_line("Stato runner:", status),
            detail_line("Esito:", outcome),
            detail_line("Test:", tests),
            detail_line("Report salvato:", report_path),
            "",
            *render_test_details(report),
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
            lines.extend(
                [
                    section_separator(),
                    colorize(f"Richiesta {request_index}", HELP_REQUEST_COLOR, use_color),
                    detail_line("Data:", compact_datetime(event.get("requested_at"))),
                    detail_line("Tipo:", event.get("label")),
                    detail_line("Esito:", colorize(decision, decision_color, use_color)),
                    *help_history_block("Prompt studente", event.get("prompt"), HELP_PROMPT_COLOR, use_color),
                ]
            )
            if response:
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
    allow_insecure_http: bool = False,
) -> dict[str, Any]:
    """Send one student help request to the teacher-side server."""

    assignment_id = clean_text(assignment.get("assignment_id"), "")
    if not assignment_id:
        raise ValueError("Identificativo consegna non disponibile.")
    if not server_token.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    body = json.dumps(
        {
            "assignment_id": assignment_id,
            "help_type": help_type,
            "prompt": prompt,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/help",
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {server_token.strip()}",
        },
        method="POST",
    )
    try:
        with student_api_urlopen(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = _server_error_detail(error.read())
        raise ValueError(f"Server aiuti: {detail or error.reason}") from error
    except urllib.error.URLError as error:
        raise ValueError(
            f"Server non raggiungibile su {server_url}. Avvialo con scripts/course_board_server.py."
        ) from error
    except TimeoutError as error:
        raise ValueError("Il server aiuti non ha risposto entro il tempo previsto.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Il server aiuti ha restituito una risposta non valida.") from error
    event = payload.get("event") if isinstance(payload, dict) else None
    if not isinstance(event, dict):
        raise ValueError("Il server aiuti non ha restituito l'evento salvato.")
    return event


def fetch_help_history_from_server(
    *,
    assignment: dict[str, Any],
    server_url: str,
    server_token: str,
    allow_insecure_http: bool = False,
) -> dict[str, Any]:
    """Load one student's assignment history through the authenticated server API."""

    assignment_id = clean_text(assignment.get("assignment_id"), "")
    if not assignment_id:
        raise ValueError("Identificativo consegna non disponibile.")
    if not server_token.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    query = urllib.parse.urlencode({"assignment_id": assignment_id})
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/help-history?{query}",
        headers={"Authorization": f"Bearer {server_token.strip()}"},
        method="GET",
    )
    try:
        with student_api_urlopen(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = _server_error_detail(error.read())
        raise ValueError(f"Server aiuti: {detail or error.reason}") from error
    except urllib.error.URLError as error:
        raise ValueError(f"Server non raggiungibile su {server_url}.") from error
    except TimeoutError as error:
        raise ValueError("Il server aiuti non ha risposto entro il tempo previsto.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Il server aiuti ha restituito uno storico non valido.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
        raise ValueError("Il server aiuti ha restituito uno storico non valido.")
    return payload


def _server_error_detail(body: bytes) -> str:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "richiesta rifiutata"
    return clean_text(payload.get("error"), "richiesta rifiutata") if isinstance(payload, dict) else "richiesta rifiutata"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep bearer credentials confined to the original student API URL."""

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


_STUDENT_API_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def student_api_urlopen(request: urllib.request.Request, *, timeout: float):
    """Open an authenticated student API request without following redirects."""

    return _STUDENT_API_OPENER.open(request, timeout=timeout)


def help_result_message(event: dict[str, Any], use_color: bool = False) -> str:
    """Return a structured result after recording a help request."""

    allowed = event.get("allowed") is True
    status = "consentita" if allowed else "bloccata"
    status_color = HELP_RESPONSE_COLOR if allowed else HELP_ERROR_COLOR
    lines = [
        colorize("Esito richiesta aiuto", HELP_REQUEST_COLOR, use_color),
        section_separator(),
        detail_line("Tipo:", event.get("label")),
        detail_line("Esito:", colorize(status, status_color, use_color)),
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

    if not server_token.strip():
        raise ValueError("Token studente mancante. Imposta THEBITLAB_STUDENT_HELP_TOKEN.")
    safe_server_url = validated_server_url(server_url, allow_insecure_http)
    query = urllib.parse.urlencode({"now": now}) if now else ""
    suffix = f"?{query}" if query else ""
    request = urllib.request.Request(
        f"{safe_server_url}/api/student-lab/assignments{suffix}",
        headers={"Authorization": f"Bearer {server_token.strip()}"},
    )
    try:
        with student_api_urlopen(request, timeout=HELP_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = _server_error_detail(error.read())
        raise ValueError(f"Server consegne: {detail or error.reason}") from error
    except urllib.error.URLError as error:
        raise ValueError(f"Server non raggiungibile su {server_url}.") from error
    except TimeoutError as error:
        raise ValueError("Il server consegne non ha risposto entro il tempo previsto.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Il server consegne ha restituito una risposta non valida.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("assignments"), list):
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

    if server_token.strip():
        remote_payload = fetch_student_lab_payload(
            server_url=server_url,
            server_token=server_token,
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
) -> int:
    """Run the interactive student lab loop."""

    payload = load_current_payload(
        root=root,
        student_id=student_id,
        now=now,
        server_url=server_url,
        server_token=server_token,
        allow_insecure_http=allow_insecure_http,
    )
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
                    server_token=server_token,
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
        while True:
            assignment = find_assignment(payload, selected_assignment_id, index)
            if assignment is None:
                print_fn("Consegna non più disponibile.")
                input_fn("Premi invio per tornare alla lista...")
                break
            if clear:
                clear_screen()
            print_fn(render_assignment_detail(assignment, use_color=use_color))
            action = input_fn("\nDettaglio: ").strip().lower()
            if action in {"", "b", "back", "indietro"}:
                break
            if action in {"q", "quit", "esci"}:
                return 0
            if action == "o":
                workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
                if not open_workspace(clean_text(workspace.get("path"), ""), root=root):
                    print_fn("Workspace non disponibile.")
                input_fn("Premi invio per continuare...")
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
                        try:
                            event = record_help_from_tui(
                                assignment=assignment,
                                server_url=server_url,
                                server_token=server_token,
                                help_type=help_type,
                                prompt=prompt,
                                allow_insecure_http=allow_insecure_http,
                            )
                        except ValueError as error:
                            print_fn(f"Richiesta aiuto non salvata:\n{error}")
                        else:
                            print_fn(help_result_message(event, use_color=use_color))
                            try:
                                payload = load_current_payload(
                                    root=root,
                                    student_id=student_id,
                                    now=now,
                                    server_url=server_url,
                                    server_token=server_token,
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
                    if server_token.strip():
                        history = fetch_help_history_from_server(
                            assignment=assignment,
                            server_url=server_url,
                            server_token=server_token,
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
            if action == "e":
                try:
                    report = student_lab_runner.run_local_assignment(assignment, root=root)
                    report_path = student_lab_runner.write_student_report(root, assignment, report)
                except ValueError as error:
                    print_fn(f"Runner non disponibile:\n{error}")
                else:
                    print_fn(runner_result_message(report, report_path))
                    try:
                        payload = load_current_payload(
                            root=root,
                            student_id=student_id,
                            now=now,
                            server_url=server_url,
                            server_token=server_token,
                            allow_insecure_http=allow_insecure_http,
                        )
                    except ValueError as error:
                        print_fn(
                            "Report salvato, ma aggiornamento dati non disponibile:\n"
                            f"{error}"
                        )
                input_fn("Premi invio per continuare...")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the student lab TUI."""

    parser = argparse.ArgumentParser(description="Apri la TUI minima del lab studente.")
    parser.add_argument("--student-id", required=True, help="Identificativo studente, per esempio rossi-mario.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Root del repository TheBitLab.")
    parser.add_argument("--now", help="Data ISO da usare per calcolare scadenze e mancanti.")
    parser.add_argument("--no-clear", action="store_true", help="Non pulire lo schermo tra una vista e l'altra.")
    parser.add_argument("--no-color", action="store_true", help="Disabilita colori ANSI.")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("THEBITLAB_SERVER_URL", DEFAULT_SERVER_URL),
        help="URL del server locale che gestisce richieste di aiuto e provider Codex.",
    )
    parser.add_argument(
        "--server-token",
        default=os.environ.get("THEBITLAB_STUDENT_HELP_TOKEN", ""),
        help="Token personale firmato usato per autenticare le richieste di aiuto.",
    )
    parser.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help="Consenti HTTP remoto solo per un collaudo su rete controllata; il default richiede HTTPS.",
    )
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
            server_url=args.server_url,
            server_token=args.server_token,
            allow_insecure_http=args.allow_insecure_http,
        )
    except ValueError as error:
        print(f"Lab studente non disponibile:\n{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
