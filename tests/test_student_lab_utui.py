from __future__ import annotations

import copy
import os
from pathlib import Path

import pytest

from scripts import student_lab_layout, student_lab_utui


SNAPSHOT_ROOT = Path(__file__).with_name("snapshots") / "student_lab_utui"

ASSIGNMENT = {
    "title": "Somma in Python",
    "activity_id": "python-demo-somma-001",
    "assignment_id": "assignment-demo-001",
    "class_id": "3A",
    "class_label": "3A Informatica",
    "assigned_at": "2026-07-20T08:30:00+02:00",
    "due_at": "2026-07-25T23:59:00+02:00",
    "status": "submitted",
    "student_support_mode": "debug",
    "workspace": {
        "path": "tmp/demo/rossi-mario/python-demo-somma-001",
        "exists": True,
    },
    "activity": {
        "path": "activities/python-demo-somma-001.json",
        "kind": "laboratorio",
        "language": "python",
        "source_name": "main.py",
        "topics": ["funzioni", "somma", "input"],
    },
    "support_policy": {
        "label": "Debug guidato",
        "summary": "Spiegazioni e indizi senza soluzione completa.",
        "allowed": ["errori", "concetti"],
        "not_allowed": ["soluzione completa"],
    },
    "help": {
        "status": "",
        "error": None,
        "total": 2,
        "allowed": 2,
        "denied": 0,
        "ai_budget": {"limit": 5, "used": 2, "remaining": 3, "exhausted": False},
        "last_requested_at": "2026-07-23T18:05:00+02:00",
        "last_decision": "consentita",
    },
    "report": {
        "path": "teacher-reports/demo/python-demo-somma-001.json",
        "exists": True,
        "submitted_at": "2026-07-23T18:10:00+02:00",
        "commit": "abc1234",
        "tests": [
            {"name": "test_somma_positivi", "passed": True},
            {
                "name": "test_somma_negativi",
                "passed": False,
                "detail": "atteso -3, ottenuto 3",
            },
        ],
    },
    "grading": {
        "status": "draft",
        "tests_passed": 1,
        "tests_total": 2,
        "score": 7,
    },
    "runner": {"status": "passed", "backend": "docker"},
}


def assert_snapshot(name: str, value: str) -> None:
    expected = (SNAPSHOT_ROOT / name).read_text(encoding="utf-8")
    normalized = "\n".join(line.rstrip() for line in value.splitlines()).rstrip() + "\n"
    assert normalized == expected


def test_project_assignment_contains_all_stable_sections_without_mutation() -> None:
    original = copy.deepcopy(ASSIGNMENT)

    sections = student_lab_utui.project_assignment_sections(ASSIGNMENT)

    assert tuple(section["id"] for section in sections) == student_lab_utui.SECTION_IDS
    assert ASSIGNMENT == original
    by_id = {section["id"]: section for section in sections}
    assert by_id["assignment"]["rows"][0] == "Titolo: Somma in Python"
    assert by_id["assignment"]["rows"][-1] == "Stato: Consegnata"
    assert by_id["assignment"]["row_styles"][-1] == "success"
    assert by_id["tests"]["rows"] == (
        "[ok] test_somma_positivi",
        "[ko] test_somma_negativi",
        "  atteso -3, ottenuto 3",
    )
    assert by_id["tests"]["row_styles"] == ("success", "error", None)
    assert by_id["help"]["row_styles"][5] == "warning"
    assert by_id["help"]["row_styles"][-1] == "success"
    assert by_id["grading"]["row_styles"][-1] == "success"
    assert by_id["runner"]["row_styles"][0] == "success"
    assert by_id["guide"]["rows"][4:9] == (
        "",
        "Flusso consigliato",
        "1. Apri il workspace.",
        "2. Modifica i file.",
        "3. Esegui i test e salva il report.",
    )
    assert "l  Modifica layout pannelli" in by_id["guide"]["rows"]
    assert "invio  Torna alla lista" in by_id["guide"]["rows"]


def test_project_assignment_keeps_missing_sections_visible() -> None:
    sections = student_lab_utui.project_assignment_sections({})

    assert len(sections) == 10
    assert all(section["rows"] for section in sections)


def test_project_assignment_removes_terminal_control_characters() -> None:
    assignment = {
        "title": "Titolo\niniettato\x1b]52;c;SGVsbG8=\x07",
        "activity_id": "demo\x1b[2J",
    }

    sections = student_lab_utui.project_assignment_sections(assignment)
    rows = [row for section in sections for row in section["rows"]]
    rendered = "\n".join(rows)

    assert "Titolo iniettato]52;c;SGVsbG8=" in rendered
    assert all("\n" not in row for row in rows)
    assert "\x1b" not in rendered
    assert "\x07" not in rendered


def test_required_utui_dependency_is_importable() -> None:
    if os.environ.get("THEBITLAB_REQUIRE_UTUI") == "1":
        assert student_lab_utui.is_available(), repr(student_lab_utui.UTUI_IMPORT_ERROR)


@pytest.mark.skipif(not student_lab_utui.is_available(), reason="utui non installato")
def test_wide_no_color_snapshot() -> None:
    frame = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=120,
        height=34,
        color=False,
    )

    assert_snapshot("wide-no-color.txt", "\n".join(frame))


@pytest.mark.skipif(not student_lab_utui.is_available(), reason="utui non installato")
def test_narrow_no_color_snapshot() -> None:
    frame = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=72,
        height=72,
        color=False,
    )

    assert_snapshot("narrow-no-color.txt", "\n".join(frame))


@pytest.mark.skipif(not student_lab_utui.is_available(), reason="utui non installato")
def test_color_and_no_color_have_identical_visible_geometry() -> None:
    plain = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=100,
        height=30,
        color=False,
    )
    colored = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=100,
        height=30,
        color=True,
    )

    assert [student_lab_layout.visible_text(line) for line in colored] == plain
    rendered = "\n".join(colored)
    assert "\x1b[92m" in rendered
    assert "\x1b[91m" in rendered
    help_scrolled = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=100,
        height=30,
        color=True,
        interaction={"section_offsets": {"help": 5}},
    )
    assert "\x1b[93m" in "\n".join(help_scrolled)


@pytest.mark.skipif(not student_lab_utui.is_available(), reason="utui non installato")
def test_breakpoint_switches_from_ordered_stack_to_two_columns() -> None:
    at_89 = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=89,
        height=12,
        color=False,
    )
    at_90 = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=90,
        height=12,
        color=False,
    )

    assert " | " not in at_89[0]
    assert " | " in at_90[0]


@pytest.mark.skipif(not student_lab_utui.is_available(), reason="utui non installato")
def test_panel_and_dashboard_offsets_reveal_later_rows_without_mutation() -> None:
    interaction = {
        "section_offsets": {"help": 2},
        "dashboard_offset": 1,
    }
    original = copy.deepcopy(interaction)

    panel_scrolled = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=120,
        height=34,
        color=False,
        interaction={"section_offsets": {"help": 2}},
    )
    dashboard_scrolled = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        {**student_lab_layout.DEFAULT_LAYOUT, "orientation": "vertical"},
        width=72,
        height=12,
        color=False,
        interaction=interaction,
    )

    assert any("Ultima: 23/07/2026 18:05" in line for line in panel_scrolled)
    assert dashboard_scrolled[0].startswith("|Titolo:")
    assert interaction == original


@pytest.mark.skipif(not student_lab_utui.is_available(), reason="utui non installato")
def test_reordered_collapsed_focus_snapshot_without_layout_mutation() -> None:
    layout = {
        **student_lab_layout.DEFAULT_LAYOUT,
        "order": list(reversed(student_lab_layout.DEFAULT_PANEL_ORDER)),
        "collapsed": ["help", "report"],
        "focus": "runner",
    }
    original = copy.deepcopy(layout)

    frame = student_lab_utui.render_assignment_frame(
        ASSIGNMENT,
        layout,
        width=120,
        height=30,
        color=False,
    )

    assert layout == original
    assert_snapshot("reordered-collapsed.txt", "\n".join(frame))


def test_render_falls_back_after_adapter_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> list[str]:
        raise RuntimeError("render failure")

    monkeypatch.setattr(student_lab_utui, "render_assignment_frame", fail)

    rendered = student_lab_utui.render_assignment_or_fallback(
        ASSIGNMENT,
        student_lab_layout.DEFAULT_LAYOUT,
        width=120,
        height=30,
        color=False,
        fallback=lambda: "legacy renderer",
    )

    assert rendered == "legacy renderer"
