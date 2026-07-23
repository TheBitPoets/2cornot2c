"""Pure uTUI rendering adapter for the student lab assignment detail."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import sys
from typing import Any

from scripts import student_lab_layout


BREAKPOINT = 90
MISSING_VALUE = "-"
PANEL_BODY_ROWS = 6
SECTION_IDS = tuple(student_lab_layout.PANEL_NAMES)
SECTION_TITLES = dict(student_lab_layout.PANEL_TITLES)
MINIMUM_PYTHON = (3, 11)

try:
    from utui import (
        Canvas,
        Column,
        Divider,
        Label,
        Modal,
        Panel,
        Rect,
        Row,
        ScrollView,
        Size,
        Widget,
        render_lines,
    )
except ImportError as error:  # pragma: no cover - depends on the optional extra
    Canvas = Column = Divider = Label = Modal = Panel = Rect = Row = ScrollView = None
    Size = Widget = render_lines = None
    UTUI_IMPORT_ERROR: ImportError | None = error
else:
    UTUI_IMPORT_ERROR = None


class UtuiUnavailableError(RuntimeError):
    """Raised when the optional uTUI renderer cannot be loaded."""


@dataclass(slots=True)
class _DashboardFrame:
    """Draw the dashboard first and the optional modal above it."""

    dashboard: Any
    modal: Any

    def draw(self, canvas: Any, rect: Any) -> None:
        self.dashboard.draw(canvas, rect)
        self.modal.draw(canvas, rect)


def is_available() -> bool:
    """Return whether the optional renderer can be used."""

    return UTUI_IMPORT_ERROR is None


def _require_utui() -> None:
    if sys.version_info < MINIMUM_PYTHON:
        raise UtuiUnavailableError(
            "Renderer utui richiede Python 3.11 o successivo."
        )
    if UTUI_IMPORT_ERROR is not None:
        raise UtuiUnavailableError(
            "Renderer utui non disponibile. Installa requirements-utui.txt "
            "con Python 3.11 o successivo."
        ) from UTUI_IMPORT_ERROR


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _text(value: Any, fallback: str = MISSING_VALUE) -> str:
    if value is None:
        return fallback
    rendered = str(value).strip()
    return rendered or fallback


def _datetime_text(value: Any) -> str:
    raw = _text(value, "")
    if not raw:
        return MISSING_VALUE
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return parsed.strftime("%d/%m/%Y %H:%M")


def _list_text(value: Any) -> str:
    items = [_text(item, "") for item in _sequence(value)]
    return ", ".join(item for item in items if item) or MISSING_VALUE


def _yes_no(value: Any) -> str:
    if value is True:
        return "si"
    if value is False:
        return "no"
    return MISSING_VALUE


def _ai_budget_text(value: Any) -> str:
    budget = _mapping(value)
    limit = budget.get("limit")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        return "non disponibile"
    used = budget.get("used")
    remaining = budget.get("remaining")
    used_value = used if isinstance(used, int) and not isinstance(used, bool) else 0
    remaining_value = (
        remaining if isinstance(remaining, int) and not isinstance(remaining, bool) else 0
    )
    label = f"{used_value}/{limit} usate, {remaining_value} rimanenti"
    return f"{label} (esaurito)" if budget.get("exhausted") is True else label


def _grading_status(grading: Mapping[str, Any]) -> str:
    status = _text(grading.get("status"), "non valutata")
    passed = grading.get("tests_passed")
    total = grading.get("tests_total")
    if passed is not None and total is not None:
        return f"{status} ({passed}/{total} test)"
    return status


def _rows(*values: tuple[str, Any]) -> tuple[str, ...]:
    return tuple(f"{label}: {_text(value)}" for label, value in values)


def _test_rows(report: Mapping[str, Any]) -> tuple[str, ...]:
    tests = _sequence(report.get("tests"))
    if not tests:
        return ("Dettaglio non disponibile nel report.",)
    rows: list[str] = []
    for index, raw_test in enumerate(tests, start=1):
        test = _mapping(raw_test)
        result = "ok" if test.get("passed") is True else "ko" if test.get("passed") is False else "?"
        name = _text(test.get("name"), f"test {index}")
        rows.append(f"[{result}] {name}")
        if test.get("passed") is not True:
            detail = next(
                (
                    _text(test.get(key), "")
                    for key in ("detail", "message", "error", "stderr", "stdout")
                    if _text(test.get(key), "")
                ),
                "",
            )
            if detail:
                rows.append(f"  {' '.join(detail.split())}")
    return tuple(rows) or ("Dettaglio non disponibile nel report.",)


def project_assignment_sections(assignment: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Project one application assignment into the ten stable presentation sections."""

    workspace = _mapping(assignment.get("workspace"))
    activity = _mapping(assignment.get("activity"))
    support = _mapping(assignment.get("support_policy"))
    help_summary = _mapping(assignment.get("help"))
    report = _mapping(assignment.get("report"))
    grading = _mapping(assignment.get("grading"))
    runner = _mapping(assignment.get("runner"))
    grade = grading.get("teacher_grade")
    if grade is None:
        grade = grading.get("score")
    sections = (
        {
            "id": "assignment",
            "title": SECTION_TITLES["assignment"],
            "rows": _rows(
                ("Titolo", assignment.get("title") or assignment.get("activity_id")),
                ("Activity", assignment.get("activity_id")),
                ("Assegnazione", assignment.get("assignment_id")),
                ("Classe", assignment.get("class_label") or assignment.get("class_id")),
                ("Assegnata", _datetime_text(assignment.get("assigned_at"))),
                ("Scadenza", _datetime_text(assignment.get("due_at"))),
                ("Stato", assignment.get("status")),
            ),
        },
        {
            "id": "workspace",
            "title": SECTION_TITLES["workspace"],
            "rows": _rows(
                ("Path", workspace.get("path")),
                ("Esiste", _yes_no(workspace.get("exists"))),
            ),
        },
        {
            "id": "activity",
            "title": SECTION_TITLES["activity"],
            "rows": _rows(
                ("Path", activity.get("path")),
                ("Tipo", activity.get("kind")),
                ("Linguaggio", activity.get("language")),
                ("Sorgente", activity.get("source_name")),
                ("Argomenti", _list_text(activity.get("topics"))),
            ),
        },
        {
            "id": "support",
            "title": SECTION_TITLES["support"],
            "rows": _rows(
                ("Modalita", support.get("label") or assignment.get("student_support_mode")),
                ("Sintesi", support.get("summary")),
                ("Permesso", _list_text(support.get("allowed"))),
                ("Non permesso", _list_text(support.get("not_allowed"))),
            ),
        },
        {
            "id": "help",
            "title": SECTION_TITLES["help"],
            "rows": _rows(
                ("Stato log", help_summary.get("status")),
                ("Errore log", help_summary.get("error")),
                ("Eventi", help_summary.get("total")),
                ("Consentite", help_summary.get("allowed")),
                ("Bloccate", help_summary.get("denied")),
                ("AI budget", _ai_budget_text(help_summary.get("ai_budget"))),
                ("Ultima", _datetime_text(help_summary.get("last_requested_at"))),
                ("Esito ultima", help_summary.get("last_decision")),
            ),
        },
        {
            "id": "report",
            "title": SECTION_TITLES["report"],
            "rows": _rows(
                ("Path", report.get("path")),
                ("Esiste", _yes_no(report.get("exists"))),
                ("Consegnata", _datetime_text(report.get("submitted_at"))),
                ("Commit", report.get("commit")),
            ),
        },
        {
            "id": "tests",
            "title": SECTION_TITLES["tests"],
            "rows": _test_rows(report),
        },
        {
            "id": "grading",
            "title": SECTION_TITLES["grading"],
            "rows": _rows(
                ("Stato", _grading_status(grading)),
                ("Voto", grade),
            ),
        },
        {
            "id": "runner",
            "title": SECTION_TITLES["runner"],
            "rows": _rows(
                ("Stato", runner.get("status")),
                ("Backend", runner.get("backend")),
            ),
        },
        {
            "id": "guide",
            "title": SECTION_TITLES["guide"],
            "rows": (
                "Consegna: lavoro assegnato dal docente.",
                "Workspace: cartella locale dove modifichi i file.",
                "Test: controlli automatici sul tuo lavoro.",
                "Report: risultato letto da dashboard e registro.",
                "Flusso: apri, modifica, esegui test, controlla.",
                "Comandi: e test, a aiuto, o workspace, v editor.",
                "Altri: h storico, b indietro, q esci.",
            ),
        },
    )
    return sections


def _section_map(
    sections: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    mapped: dict[str, Mapping[str, Any]] = {}
    for section in sections:
        identifier = section.get("id")
        if identifier not in SECTION_IDS:
            raise ValueError(f"Identificatore pannello sconosciuto: {identifier!r}")
        if identifier in mapped:
            raise ValueError(f"Identificatore pannello duplicato: {identifier}")
        mapped[str(identifier)] = section
    return mapped


def _build_panel(
    identifier: str,
    section: Mapping[str, Any] | None,
    *,
    focused: bool,
    collapsed: bool,
    scroll_offset: int,
) -> tuple[Any, int]:
    title = SECTION_TITLES[identifier]
    rows: Sequence[Any] = ()
    if section is not None:
        title = _text(section.get("title"), title)
        rows = _sequence(section.get("rows"))
    normalized_rows = tuple(_text(row) for row in rows) or ("non disponibile",)
    body_height = min(PANEL_BODY_ROWS, len(normalized_rows))
    height = 3 if collapsed else max(3, body_height + 2)
    return (
        Panel(
            ScrollView(
                Label("\n".join(normalized_rows)),
                content_height=len(normalized_rows),
                scroll_offset=scroll_offset,
            ),
            title=title,
            focused=focused,
            collapsed=collapsed,
        ),
        height,
    )


def _build_column(entries: Sequence[tuple[Any, int]]) -> tuple[Any, int]:
    return (
        Column(
            [panel for panel, _height in entries],
            sizes=[Size.fixed_size(height) for _panel, height in entries],
        ),
        sum(height for _panel, height in entries),
    )


def build_dashboard(
    sections: Sequence[Mapping[str, Any]],
    presentation: Mapping[str, Any],
    *,
    width: int,
    interaction: Mapping[str, Any] | None = None,
) -> Any:
    """Build the responsive widget tree from normalized consumer-owned state."""

    _require_utui()
    normalized = student_lab_layout.normalize_layout(dict(presentation))
    mapped = _section_map(sections)
    order = tuple(normalized["order"])
    transient = interaction or {}
    raw_offsets = transient.get("section_offsets", {})
    if not isinstance(raw_offsets, Mapping):
        raise ValueError("section_offsets deve essere una mappa")
    section_offsets: dict[str, int] = {}
    for identifier, value in raw_offsets.items():
        if identifier not in SECTION_IDS:
            raise ValueError(f"Offset per pannello sconosciuto: {identifier!r}")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("Gli offset dei pannelli devono essere interi non negativi")
        section_offsets[str(identifier)] = value
    dashboard_offset = transient.get("dashboard_offset", 0)
    if (
        not isinstance(dashboard_offset, int)
        or isinstance(dashboard_offset, bool)
        or dashboard_offset < 0
    ):
        raise ValueError("dashboard_offset deve essere un intero non negativo")
    entries = [
        _build_panel(
            identifier,
            mapped.get(identifier),
            focused=normalized["focus"] == identifier,
            collapsed=identifier in normalized["collapsed"],
            scroll_offset=section_offsets.get(identifier, 0),
        )
        for identifier in order
    ]
    if normalized["orientation"] != "horizontal" or width < BREAKPOINT:
        dashboard, content_height = _build_column(entries)
    else:
        effective_left = min(normalized["left_width"], max(36, width - 39))
        right_width = max(30, width - effective_left - 3)
        left, left_height = _build_column(entries[:5])
        right, right_height = _build_column(entries[5:])
        content_height = max(left_height, right_height)
        dashboard = Row(
            [left, Divider("vertical"), right],
            sizes=[
                Size.fixed_size(effective_left),
                Size.fixed_size(3),
                Size.fixed_size(right_width),
            ],
            gap=0,
            stack_when_narrow=False,
        )
    modal = Modal("", title="", open=False)
    return _DashboardFrame(
        ScrollView(
            dashboard,
            content_height=content_height,
            scroll_offset=dashboard_offset,
        ),
        modal,
    )


def render_assignment_frame(
    assignment: Mapping[str, Any],
    presentation: Mapping[str, Any],
    *,
    width: int,
    height: int,
    color: bool = False,
    interaction: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render a deterministic frame without printing or mutating caller data."""

    _require_utui()
    return render_lines(
        build_dashboard(
            project_assignment_sections(assignment),
            presentation,
            width=width,
            interaction=interaction,
        ),
        width,
        height,
        color=color,
    )


def render_assignment_or_fallback(
    assignment: Mapping[str, Any],
    presentation: Mapping[str, Any],
    *,
    width: int,
    height: int,
    color: bool,
    fallback: Callable[[], str],
    interaction: Mapping[str, Any] | None = None,
) -> str:
    """Render with uTUI and use the existing renderer after any adapter failure."""

    try:
        return "\n".join(
            render_assignment_frame(
                assignment,
                presentation,
                width=width,
                height=height,
                color=color,
                interaction=interaction,
            )
        )
    except Exception:
        return fallback()
