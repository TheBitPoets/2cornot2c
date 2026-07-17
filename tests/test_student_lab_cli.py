from __future__ import annotations

import json
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
        "student_support_mode": "studio-guidato",
        "support_policy": {
            "mode": "studio-guidato",
            "label": "Studio guidato",
            "summary": "Puoi consultare materiali e domande guida.",
            "allowed": ["riferimenti alla teoria", "feedback tecnico"],
            "not_allowed": ["soluzioni complete"],
        },
        "help": {
            "path": "examples/assignment_tracking/student_repos/rossi-mario/help/python-base-somma-001/events.json",
            "exists": True,
            "total": 2,
            "allowed": 1,
            "denied": 1,
            "last_requested_at": "2026-10-18T17:20:00+02:00",
            "last_decision": "bloccata",
            "counts": {"teoria": 1, "ai": 1},
            "ai_budget": {"limit": 5, "used": 1, "remaining": 4, "exhausted": False},
        },
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
    assert "2026-10-19 23:59" in rendered
    assert "2026-10-19T23:59:00+02:00" not in rendered
    assert "Legenda:" in rendered
    assert "Mancante: scadenza superata" in rendered
    assert "no workspace: cartella locale" in rendered


def test_render_assignment_list_handles_empty_payload() -> None:
    rendered = student_lab_cli.render_assignment_list(sample_payload([]))

    assert "Nessuna consegna disponibile" in rendered


def test_render_assignment_detail_shows_workspace_report_and_runner() -> None:
    rendered = student_lab_cli.render_assignment_detail(sample_assignment())

    assert "Dettaglio consegna" in rendered
    assert "Somma in Python" in rendered
    assert "Classe demo 3A" in rendered
    assert "2026-10-12 09:00" in rendered
    assert "2026-10-19 23:59" in rendered
    assert "Path:" in rendered
    assert "examples/assignment_tracking/student_repos/rossi-mario/assignments/python-base-somma-001" in rendered
    assert "Linguaggio:" in rendered
    assert "python" in rendered
    assert "Aiuto consentito" in rendered
    assert "Studio guidato" in rendered
    assert "riferimenti alla teoria, feedback tecnico" in rendered
    assert "soluzioni complete" in rendered
    assert "Richieste aiuto" in rendered
    assert "Bloccate:" in rendered
    assert "1/5 usate, 4 rimanenti" in rendered
    assert "2026-10-18 17:20" in rendered
    assert "bloccata" in rendered
    assert "not_graded" in rendered
    assert "not_run" in rendered
    assert "e = esegui e salva report" in rendered
    assert "h = storico aiuti" in rendered
    assert "invio = lista" in rendered
    assert "o = apri workspace" in rendered


def test_render_assignment_list_can_color_statuses() -> None:
    rendered = student_lab_cli.render_assignment_list(sample_payload(), use_color=True)

    assert "\033[33mDa fare\033[0m" in rendered
    assert "\033[36mworkspace\033[0m" in rendered


def test_render_assignment_detail_can_color_status() -> None:
    rendered = student_lab_cli.render_assignment_detail(sample_assignment(status="missing"), use_color=True)

    assert "\033[31mMancante\033[0m" in rendered


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


def test_runner_result_message_shows_status_tests_and_report_path(tmp_path) -> None:
    message = student_lab_cli.runner_result_message(
        {"status": "passed", "summary": {"passed": 2, "total": 3}},
        tmp_path / "reports" / "latest.json",
    )

    assert "Runner completato: passed (2/3 test)" in message
    assert "Report salvato:" in message


def test_assignment_repo_path_uses_help_or_workspace_path(tmp_path) -> None:
    assignment = sample_assignment(
        help={"path": "student/help/python-base-somma-001/events.json"},
        workspace={"path": "student/assignments/python-base-somma-001", "exists": True},
    )

    assert student_lab_cli.assignment_repo_path(assignment, root=tmp_path) == tmp_path / "student"

    assignment_without_help = sample_assignment(help={}, workspace={"path": "student/assignments/python-base-somma-001", "exists": True})

    assert student_lab_cli.assignment_repo_path(assignment_without_help, root=tmp_path) == tmp_path / "student"


def test_assignment_help_log_path_uses_payload_or_repo_path(tmp_path) -> None:
    assignment = sample_assignment(help={"path": "student/help/python-base-somma-001/events.json"})

    assert student_lab_cli.assignment_help_log_path(assignment, root=tmp_path) == tmp_path / "student" / "help" / "python-base-somma-001" / "events.json"

    assignment_without_help_path = sample_assignment(help={}, workspace={"path": "student/assignments/python-base-somma-001", "exists": True})

    assert (
        student_lab_cli.assignment_help_log_path(assignment_without_help_path, root=tmp_path)
        == tmp_path / "student" / "help" / "python-base-somma-001" / "events.json"
    )


def test_render_help_history_shows_events(tmp_path) -> None:
    log_path = tmp_path / "student" / "help" / "python-base-somma-001" / "events.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "requested_at": "2026-10-18T17:20:00+02:00",
                        "label": "Aiuto AI",
                        "allowed": False,
                        "reason": "La modalita scelta dal docente non consente aiuto AI.",
                        "prompt": "Mi scrivi la soluzione completa?",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assignment = sample_assignment(help={"path": "student/help/python-base-somma-001/events.json"})

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Storico richieste aiuto" in rendered
    assert "2026-10-18 17:20 | Aiuto AI | bloccata" in rendered
    assert "non consente aiuto AI" in rendered
    assert "Mi scrivi la soluzione completa?" in rendered


def test_render_help_history_handles_empty_or_invalid_log(tmp_path) -> None:
    assignment = sample_assignment(help={"path": "student/help/python-base-somma-001/events.json"})

    empty_rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Nessuna richiesta di aiuto registrata" in empty_rendered

    log_path = tmp_path / "student" / "help" / "python-base-somma-001" / "events.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text("{non-json", encoding="utf-8")

    invalid_rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Log aiuti non leggibile" in invalid_rendered


def test_find_assignment_prefers_assignment_id_and_falls_back_to_index() -> None:
    first = sample_assignment(assignment_id="assignment-a", title="Prima")
    second = sample_assignment(assignment_id="assignment-b", title="Seconda")
    payload = sample_payload([first, second])

    assert student_lab_cli.find_assignment(payload, "assignment-b", 0) == second
    assert student_lab_cli.find_assignment(payload, "missing", 1) == second
    assert student_lab_cli.find_assignment(sample_payload([]), "missing", 0) is None


def test_help_result_message_shows_policy_decision() -> None:
    message = student_lab_cli.help_result_message(
        {
            "allowed": False,
            "label": "Aiuto AI",
            "reason": "La modalita scelta dal docente non consente aiuto AI.",
        }
    )

    assert "Richiesta aiuto bloccata: Aiuto AI" in message
    assert "non consente aiuto AI" in message


def test_ai_budget_label_handles_missing_and_exhausted_budget() -> None:
    assert student_lab_cli.ai_budget_label({}) == "non disponibile"
    assert student_lab_cli.ai_budget_label({"limit": 2, "used": 2, "remaining": 0, "exhausted": True}) == "2/2 usate, 0 rimanenti (esaurito)"


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


def test_run_tui_can_record_help_request_and_reload(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "a", "3", "Mi scrivi la soluzione?", "", "", "q"])
    load_calls = []

    def fake_load_payload(root, student_id, now=None):
        load_calls.append((root, student_id, now))
        return payload

    monkeypatch.setattr(student_lab_cli, "load_payload", fake_load_payload)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
    )

    log_path = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "help" / "python-base-somma-001" / "events.json"

    assert result == 0
    assert len(load_calls) == 2
    assert log_path.exists()
    assert "Mi scrivi la soluzione?" in log_path.read_text(encoding="utf-8")
    assert any("Richiesta aiuto bloccata: Aiuto AI" in output for output in outputs)
    assert sum(1 for output in outputs if "Dettaglio consegna" in output) == 2


def test_run_tui_can_show_help_history(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "help" / "python-base-somma-001" / "events.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "requested_at": "2026-10-18T17:20:00+02:00",
                        "label": "Richiamo teorico",
                        "allowed": True,
                        "reason": "La modalita consente richiami teorici e materiali guida.",
                        "prompt": "Mi ricordi la differenza tra input e output?",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "h", "", "", "q"])

    monkeypatch.setattr(student_lab_cli, "load_payload", lambda root, student_id, now=None: payload)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
    )

    assert result == 0
    assert any("Storico richieste aiuto" in output for output in outputs)
    assert any("Mi ricordi la differenza" in output for output in outputs)
    assert sum(1 for output in outputs if "Dettaglio consegna" in output) == 2


def test_run_tui_can_execute_runner_save_report_and_reload(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "e", "", "", "q"])
    load_calls = []
    saved_reports = []

    def fake_load_payload(root, student_id, now=None):
        load_calls.append((root, student_id, now))
        return payload

    monkeypatch.setattr(student_lab_cli, "load_payload", fake_load_payload)
    monkeypatch.setattr(
        student_lab_cli.student_lab_runner,
        "run_local_assignment",
        lambda assignment, root: {"status": "passed", "summary": {"passed": 1, "total": 1}},
    )

    def fake_write_report(root, assignment, report):
        saved_reports.append((root, assignment, report))
        return tmp_path / "reports" / "latest.json"

    monkeypatch.setattr(student_lab_cli.student_lab_runner, "write_student_report", fake_write_report)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
    )

    assert result == 0
    assert len(load_calls) == 2
    assert saved_reports
    assert any("Runner completato: passed (1/1 test)" in output for output in outputs)
    assert any("Report salvato:" in output for output in outputs)
    assert sum(1 for output in outputs if "Dettaglio consegna" in output) == 2


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


def test_compact_datetime_hides_seconds_and_timezone() -> None:
    assert student_lab_cli.compact_datetime("2026-10-19T23:59:00+02:00") == "2026-10-19 23:59"
    assert student_lab_cli.compact_datetime("") == "-"
    assert student_lab_cli.compact_datetime("non-data") == "non-data"


def test_status_label_uses_human_labels() -> None:
    assert student_lab_cli.status_label("missing") == "Mancante"
    assert student_lab_cli.status_label("custom") == "custom"


def test_supports_color_respects_no_color(monkeypatch) -> None:
    assert student_lab_cli.supports_color(no_color=True) is False
    monkeypatch.setenv("NO_COLOR", "1")
    assert student_lab_cli.supports_color() is False
