from __future__ import annotations

from pathlib import Path

from scripts import student_lab_cli


def sample_assignment(**overrides):
    """Return a lab assignment payload for TUI rendering tests."""

    payload = {
        "assignment_id": "assignment-python-base-somma-001-demo",
        "activity_id": "python-base-somma-001",
        "title": "Somma in Python",
        "student_id": "rossi-mario",
        "target_type": "class",
        "class_id": "demo-3a",
        "class_label": "Classe demo 3A",
        "github_team": "demo-3a",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "status": "pending",
        "submitted": False,
        "workspace": {
            "path": "examples/assignment_tracking/student_repos/rossi-mario/assignments/python-base-somma-001",
            "exists": True,
        },
        "activity": {
            "path": "activities/python-base-somma-001.json",
            "exists": True,
            "title": "Somma in Python",
            "kind": "laboratorio",
            "language": "python",
            "source_name": "main.py",
            "topics": ["variabili", "input-output"],
        },
        "report": {
            "path": "examples/assignment_tracking/student_repos/rossi-mario/reports/python-base-somma-001/latest.json",
            "exists": False,
            "submitted_at": "",
            "commit": None,
        },
        "grading": {
            "status": "not_graded",
            "tests_passed": None,
            "tests_total": None,
            "teacher_grade": None,
            "score": None,
        },
        "runner": {
            "status": "not_run",
            "backend": "student_lab_service",
        },
    }
    payload.update(overrides)
    return payload


def sample_payload(assignments=None):
    """Return a full student lab payload."""

    return {
        "schema_version": "student_lab.v1",
        "student_id": "rossi-mario",
        "generated_at": "2026-10-20T12:00:00+02:00",
        "assignments": assignments if assignments is not None else [sample_assignment()],
    }


def test_render_assignment_list_summarizes_statuses() -> None:
    payload = sample_payload(
        [
            sample_assignment(status="pending", submitted=False),
            sample_assignment(title="Debug puntatori", status="missing", submitted=False),
            sample_assignment(title="Array in C", status="submitted", submitted=True),
        ]
    )

    rendered = student_lab_cli.render_assignment_list(payload)

    assert "TheBitLab - lab studente" in rendered
    assert "Studente: rossi-mario" in rendered
    assert "Consegne: 3 | Da fare: 1 | Mancanti: 1 | Consegnate: 1" in rendered
    assert "Somma in Python" in rendered
    assert "Debug puntatori" in rendered
    assert "Array in C" in rendered
    assert "workspace" in rendered
    assert "numero = dettaglio" in rendered


def test_render_assignment_list_handles_empty_payload() -> None:
    rendered = student_lab_cli.render_assignment_list(sample_payload([]))

    assert "Nessuna consegna disponibile" in rendered


def test_render_assignment_detail_shows_workspace_report_and_runner() -> None:
    rendered = student_lab_cli.render_assignment_detail(sample_assignment())

    assert "Dettaglio consegna" in rendered
    assert "Somma in Python" in rendered
    assert "Classe demo 3A" in rendered
    assert "Path:" in rendered
    assert "examples/assignment_tracking/student_repos/rossi-mario/assignments/python-base-somma-001" in rendered
    assert "Linguaggio:" in rendered
    assert "python" in rendered
    assert "not_graded" in rendered
    assert "not_run" in rendered
    assert "o = apri workspace" in rendered


def test_render_assignment_detail_summarizes_grading_tests() -> None:
    assignment = sample_assignment(
        status="submitted",
        submitted=True,
        grading={"status": "graded_passed", "tests_passed": 2, "tests_total": 3, "teacher_grade": 8, "score": None},
        report={"path": "reports/latest.json", "exists": True, "submitted_at": "2026-10-18T18:00:00+02:00", "commit": "abc1234"},
    )

    rendered = student_lab_cli.render_assignment_detail(assignment)

    assert "graded_passed (2/3 test)" in rendered
    assert "abc1234" in rendered
    assert "8" in rendered


def test_run_tui_can_show_detail_and_exit(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "", "q"])

    monkeypatch.setattr(student_lab_cli, "load_payload", lambda root, student_id, now=None: payload)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
    )

    assert result == 0
    assert any("TheBitLab - lab studente" in output for output in outputs)
    assert any("Dettaglio consegna" in output for output in outputs)


def test_open_workspace_rejects_missing_path(tmp_path) -> None:
    assert student_lab_cli.open_workspace(str(tmp_path / "missing")) is False


def test_open_workspace_resolves_relative_path_from_root(monkeypatch, tmp_path) -> None:
    workspace = tmp_path / "student" / "assignments" / "python-base-somma-001"
    workspace.mkdir(parents=True)
    opened = []

    monkeypatch.setattr(student_lab_cli.os, "startfile", opened.append, raising=False)
    monkeypatch.setattr(student_lab_cli.os, "name", "nt")

    assert student_lab_cli.open_workspace("student/assignments/python-base-somma-001", root=tmp_path) is True
    assert opened == [workspace.resolve()]


def test_truncate_keeps_short_text_and_clips_long_text() -> None:
    assert student_lab_cli.truncate("abc", 5) == "abc"
    assert student_lab_cli.truncate("abcdef", 5) == "ab..."


def test_status_label_uses_human_labels() -> None:
    assert student_lab_cli.status_label("missing") == "Mancante"
    assert student_lab_cli.status_label("custom") == "custom"
