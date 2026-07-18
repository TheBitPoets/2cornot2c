from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

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


def test_main_reads_student_token_only_from_environment(monkeypatch, tmp_path) -> None:
    captured = {}
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_TOKEN", "token-da-ambiente")
    monkeypatch.setattr(
        sys,
        "argv",
        ["student_lab_cli.py", "--student-id", "rossi-mario", "--root", str(tmp_path)],
    )
    monkeypatch.setattr(student_lab_cli, "run_tui", lambda **kwargs: captured.update(kwargs) or 0)

    assert student_lab_cli.main() == 0
    assert captured["server_token"] == "token-da-ambiente"

    monkeypatch.setattr(
        sys,
        "argv",
        ["student_lab_cli.py", "--student-id", "rossi-mario", "--server-token", "token-cli"],
    )
    with pytest.raises(SystemExit):
        student_lab_cli.parse_args()


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
    assert rendered.count(student_lab_cli.section_separator()) >= 8
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
    assert "Guida rapida" in rendered
    assert "Consegna  lavoro assegnato dal docente." in rendered
    assert "Workspace cartella locale dove modifichi i file." in rendered
    assert "Test      controlli automatici sul tuo lavoro." in rendered
    assert "Report    risultato salvato e letto da dashboard/registro." in rendered
    assert "Flusso consigliato" in rendered
    assert "1. Apri workspace" in rendered
    assert "2. Modifica i file" in rendered
    assert "3. Esegui test e salva report" in rendered
    assert "4. Controlla esito e, se serve, chiedi aiuto sulla consegna" in rendered
    assert "Azioni principali" in rendered
    assert "  e  Esegui test e salva report" in rendered
    assert "  a  Chiedi aiuto" in rendered
    assert "  o  Apri workspace" in rendered
    assert "Altri comandi" in rendered
    assert "  h  Storico aiuti" in rendered
    assert "  b  Torna alla lista" in rendered
    assert "  invio  Torna alla lista" in rendered
    assert "  q  Esci" in rendered
    assert "Comandi:" not in rendered


def test_render_assignment_list_can_color_statuses() -> None:
    rendered = student_lab_cli.render_assignment_list(sample_payload(), use_color=True)

    assert "\033[33mDa fare\033[0m" in rendered
    assert "\033[36mworkspace\033[0m" in rendered


def test_render_assignment_detail_can_color_status() -> None:
    rendered = student_lab_cli.render_assignment_detail(sample_assignment(status="missing"), use_color=True)

    assert "\033[31mMancante\033[0m" in rendered
    assert "\033[35mConsegna \033[0m" in rendered
    assert "\033[36mWorkspace\033[0m" in rendered
    assert "\033[33mTest     \033[0m" in rendered
    assert "\033[32mReport   \033[0m" in rendered


def test_render_assignment_detail_summarizes_grading_tests() -> None:
    assignment = sample_assignment(
        status="submitted",
        submitted=True,
        grading={"status": "graded_passed", "tests_passed": 2, "tests_total": 3, "teacher_grade": 8, "score": None},
        report={
            "path": "reports/latest.json",
            "exists": True,
            "submitted_at": "2026-10-18T18:00:00+02:00",
            "commit": "abc1234",
            "tests": [
                {"name": "input_base", "passed": True, "status": "passed"},
                {"name": "caso_zero", "passed": False, "status": "failed", "message": "Output atteso: 10; output ottenuto: 8"},
            ],
        },
    )

    rendered = student_lab_cli.render_assignment_detail(assignment)

    assert "graded_passed (2/3 test)" in rendered
    assert "abc1234" in rendered
    assert "8" in rendered
    assert "Ultimo dettaglio test" in rendered
    assert "[ok] input_base" in rendered
    assert "[ko] caso_zero" in rendered
    assert "Output atteso: 10; output ottenuto: 8" in rendered


def test_runner_result_message_shows_status_tests_and_report_path(tmp_path) -> None:
    message = student_lab_cli.runner_result_message(
        {
            "status": "failed",
            "passed": False,
            "summary": {"passed": 2, "total": 3},
            "tests": [
                {"name": "input_base", "passed": True, "status": "passed"},
                {"name": "caso_zero", "passed": False, "status": "failed", "message": "Output atteso: 10, ottenuto: 8"},
            ],
        },
        tmp_path / "reports" / "latest.json",
    )

    assert "Esecuzione completata" in message
    assert "Stato runner:" in message
    assert "failed" in message
    assert "consegna da ricontrollare" in message
    assert "2/3 test" in message
    assert "Report salvato:" in message
    assert "Dettaglio test" in message
    assert "[ok] input_base" in message
    assert "[ko] caso_zero" in message
    assert "Output atteso: 10, ottenuto: 8" in message
    assert "Questo report è quello letto da dashboard e registro docente." in message
    assert "Questo report e quello" not in message


def test_runner_result_message_handles_missing_test_details(tmp_path) -> None:
    message = student_lab_cli.runner_result_message(
        {"status": "passed", "passed": True, "summary": {"passed": 2, "total": 2}},
        tmp_path / "reports" / "latest.json",
    )

    assert "consegna superata" in message
    assert "Dettaglio test" in message
    assert "non disponibile nel report" in message


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
                        "reason": "La modalità scelta dal docente non consente aiuto AI.",
                        "prompt": "Mi scrivi la soluzione completa?",
                        "response": {
                            "status": "ready",
                            "provider_label": "Guida locale (nessuna AI esterna)",
                            "message": "Prova prima un caso minimo.",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assignment = sample_assignment(help={"path": "student/help/python-base-somma-001/events.json"})

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Storico richieste aiuto" in rendered
    assert "Richiesta 1" in rendered
    assert "Data:              2026-10-18 17:20" in rendered
    assert "Tipo:              Aiuto AI" in rendered
    assert "Esito:             bloccata" in rendered
    assert rendered.count(student_lab_cli.section_separator()) == 2
    assert "Prompt studente" in rendered
    assert "Motivo della decisione" in rendered
    assert "non consente aiuto AI" in rendered
    assert "Mi scrivi la soluzione completa?" in rendered
    assert "Risposta - Guida locale (nessuna AI esterna)" in rendered
    assert "Prova prima un caso minimo" in rendered


def test_render_help_history_uses_events_from_server_payload(tmp_path) -> None:
    assignment = sample_assignment(
        help={
            "path": "teacher-help-events/rossi-mario/assignment-001/events.json",
            "events": [
                {
                    "requested_at": "2026-10-18T17:20:00+02:00",
                    "label": "Richiamo teorico",
                    "allowed": True,
                    "reason": "Consentito.",
                    "prompt": "Quale concetto devo ripassare?",
                    "response": {
                        "status": "ready",
                        "provider_label": "Guida locale",
                        "message": "Ripassa il ciclo for.",
                    },
                }
            ],
        }
    )

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Quale concetto devo ripassare?" in rendered
    assert "Ripassa il ciclo for." in rendered


def test_render_help_history_marks_a_saved_provider_request_as_pending(tmp_path) -> None:
    assignment = sample_assignment(
        help={
            "events": [
                {
                    "requested_at": "2026-10-20T08:00:00+02:00",
                    "help_type": "ai",
                    "label": "Aiuto AI",
                    "allowed": True,
                    "prompt": "Come procedo?",
                    "provider_status": "pending",
                }
            ]
        }
    )

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Risposta in elaborazione" in rendered
    assert "La richiesta e stata salvata" in rendered
    assert "Risposta non disponibile" not in rendered


def test_render_help_history_keeps_legacy_events_visible(tmp_path) -> None:
    legacy_path = tmp_path / "student" / "help" / "activity" / "events.json"
    student_lab_cli.student_help_service.write_help_events(
        legacy_path,
        [
            {
                "requested_at": "2026-10-17T17:20:00+02:00",
                "label": "Aiuto AI",
                "allowed": True,
                "reason": "Consentito.",
                "prompt": "Richiesta precedente.",
            }
        ],
    )
    assignment = sample_assignment(
        help={
            "path": "teacher-help-events/rossi/assignment/events.json",
            "legacy_path": "student/help/activity/events.json",
        }
    )

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Richiesta precedente." in rendered


def test_render_help_history_does_not_duplicate_server_legacy_events(tmp_path) -> None:
    legacy_path = tmp_path / "student" / "help" / "activity" / "events.json"
    student_lab_cli.student_help_service.write_help_events(
        legacy_path,
        [{"prompt": "Evento legacy unico.", "allowed": True, "label": "Aiuto AI"}],
    )
    assignment = sample_assignment(
        help={
            "legacy_path": "student/help/activity/events.json",
            "events": [
                {
                    "prompt": "Evento legacy unico.",
                    "allowed": True,
                    "label": "Aiuto AI",
                    "source": "legacy-unverified",
                }
            ],
        }
    )

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert rendered.count("Evento legacy unico.") == 1
    assert "Legacy non verificati" in rendered
    assert "non incidono sul budget" in rendered


def test_render_help_history_uses_colors_and_wraps_long_text(tmp_path) -> None:
    log_path = tmp_path / "student" / "help" / "python-base-somma-001" / "events.json"
    log_path.parent.mkdir(parents=True)
    long_prompt = "Vorrei capire come analizzare il primo test fallito senza ricevere la soluzione completa e senza saltare i passaggi di debug."
    log_path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "requested_at": "2026-10-18T17:20:00+02:00",
                        "label": "Aiuto AI",
                        "allowed": True,
                        "reason": "La modalità consente aiuto AI.",
                        "prompt": long_prompt,
                        "response": {
                            "status": "ready",
                            "provider_label": "Guida locale (nessuna AI esterna)",
                            "message": "Parti dal primo test fallito e verifica una sola ipotesi alla volta.",
                        },
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assignment = sample_assignment(help={"path": "student/help/python-base-somma-001/events.json"})

    rendered = student_lab_cli.render_help_history(assignment, root=tmp_path, use_color=True)

    assert "\033[36mRichiesta 1\033[0m" in rendered
    assert "\033[33mPrompt studente\033[0m" in rendered
    assert "\033[32mRisposta - Guida locale (nessuna AI esterna)\033[0m" in rendered
    assert "\033[35mMotivo della decisione\033[0m" in rendered
    assert "\033[32mconsentita\033[0m" in rendered
    assert "\n  la soluzione completa e senza saltare i passaggi di debug." in rendered
    assert long_prompt not in rendered


def test_render_help_history_handles_empty_or_invalid_log(tmp_path) -> None:
    assignment = sample_assignment(help={"path": "student/help/python-base-somma-001/events.json"})

    empty_rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Nessuna richiesta di aiuto registrata" in empty_rendered

    log_path = tmp_path / "student" / "help" / "python-base-somma-001" / "events.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text("{non-json", encoding="utf-8")

    invalid_rendered = student_lab_cli.render_help_history(assignment, root=tmp_path)

    assert "Log aiuti non leggibile" in invalid_rendered


def test_find_assignment_uses_index_only_without_stable_assignment_id() -> None:
    first = sample_assignment(assignment_id="assignment-a", title="Prima")
    second = sample_assignment(assignment_id="assignment-b", title="Seconda")
    payload = sample_payload([first, second])

    assert student_lab_cli.find_assignment(payload, "assignment-b", 0) == second
    assert student_lab_cli.find_assignment(payload, "missing", 1) is None
    assert student_lab_cli.find_assignment(payload, "", 1) == second
    assert student_lab_cli.find_assignment(sample_payload([]), "missing", 0) is None


def test_run_tui_keeps_current_payload_when_manual_refresh_fails(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["r", "", "q"])
    fetch_count = 0

    def fake_fetch_payload(**kwargs):
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count == 2:
            raise ValueError("server temporaneamente non disponibile")
        return payload

    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", fake_fetch_payload)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
        server_url="https://server.test",
        server_token="signed-token",
    )

    assert result == 0
    assert fetch_count == 2
    assert any("Aggiornamento dati non disponibile" in output for output in outputs)
    assert sum(1 for output in outputs if "TheBitLab - lab studente" in output) == 2


def test_help_result_message_shows_policy_decision() -> None:
    message = student_lab_cli.help_result_message(
        {
            "allowed": False,
            "label": "Aiuto AI",
            "reason": "La modalità scelta dal docente non consente aiuto AI.",
        }
    )

    assert "Esito richiesta aiuto" in message
    assert "Tipo:              Aiuto AI" in message
    assert "Esito:             bloccata" in message
    assert "Motivo" in message
    assert "non consente aiuto AI" in message
    assert message.count(student_lab_cli.section_separator()) == 2
    assert "Richiesta salvata. Usa h per rileggerla nello storico." in message


def test_help_result_message_shows_local_provider_response() -> None:
    message = student_lab_cli.help_result_message(
        {
            "allowed": True,
            "label": "Aiuto AI",
            "reason": "La modalità consente aiuto AI.",
            "response": {
                "status": "ready",
                "provider_label": "Guida locale (nessuna AI esterna)",
                "message": "Parti dal primo test fallito.",
            },
        }
    )

    assert "Esito richiesta aiuto" in message
    assert "Esito:             consentita" in message
    assert "Risposta - Guida locale (nessuna AI esterna)" in message
    assert "Parti dal primo test fallito" in message
    assert "La modalità consente aiuto AI" not in message


def test_help_result_message_uses_colors_and_wraps_long_response() -> None:
    long_response = (
        "Inizia dal primo test fallito e ricostruisci i valori delle variabili "
        "passaggio per passaggio, poi confronta il risultato atteso con quello ottenuto."
    )

    message = student_lab_cli.help_result_message(
        {
            "allowed": True,
            "label": "Aiuto AI",
            "response": {
                "status": "ready",
                "provider_label": "Guida locale",
                "message": long_response,
            },
        },
        use_color=True,
    )

    assert "\033[36mEsito richiesta aiuto\033[0m" in message
    assert "\033[32mconsentita\033[0m" in message
    assert "\033[32mRisposta - Guida locale\033[0m" in message
    assert "Usa \033[36mh\033[0m per rileggerla" in message
    assert "\n  variabili passaggio per passaggio" in message
    assert long_response not in message


def test_help_history_block_wraps_long_urls_without_horizontal_overflow() -> None:
    long_url = "https://example.test/" + ("percorso" * 24)

    lines = student_lab_cli.help_history_block("Prompt studente", long_url, "", use_color=False)

    assert len(lines) > 2
    assert all(len(line) <= 70 for line in lines[1:])
    assert "".join(line.removeprefix("  ") for line in lines[1:]) == long_url


def test_ai_budget_label_handles_missing_and_exhausted_budget() -> None:
    assert student_lab_cli.ai_budget_label({}) == "non disponibile"
    assert student_lab_cli.ai_budget_label({"limit": 2, "used": 2, "remaining": 0, "exhausted": True}) == "2/2 usate, 0 rimanenti (esaurito)"


def test_record_help_from_tui_posts_only_identifiers_and_prompt(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"ok": True, "event": {"allowed": True, "label": "Aiuto AI"}}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(student_lab_cli, "student_api_urlopen", fake_urlopen)

    event = student_lab_cli.record_help_from_tui(
        assignment=sample_assignment(),
        server_url="https://teacher.test:8765/",
        server_token="signed-token",
        help_type="ai",
        prompt="Come procedo?",
        request_id="request-tui-0001",
    )

    assert event == {"allowed": True, "label": "Aiuto AI"}
    assert captured["url"] == "https://teacher.test:8765/api/student-lab/help"
    assert captured["payload"] == {
        "assignment_id": "assignment-python-base-somma-001-demo",
        "help_type": "ai",
        "prompt": "Come procedo?",
        "request_id": "request-tui-0001",
    }
    assert captured["headers"]["Content-type"] == "application/json; charset=utf-8"
    assert captured["headers"]["Authorization"] == "Bearer signed-token"
    assert captured["timeout"] == student_lab_cli.HELP_REQUEST_TIMEOUT_SECONDS


def test_record_help_from_tui_distinguishes_pending_idempotent_retry(monkeypatch) -> None:
    response_body = io.BytesIO(
        json.dumps({"error": "Richiesta di aiuto ancora in elaborazione. Riprova tra poco."}).encode("utf-8")
    )

    def fake_urlopen(*args, **kwargs):
        raise urllib.error.HTTPError(
            "https://teacher.test/api/student-lab/help",
            409,
            "Conflict",
            {},
            response_body,
        )

    monkeypatch.setattr(student_lab_cli, "student_api_urlopen", fake_urlopen)

    with pytest.raises(student_lab_cli.StudentHelpRequestPendingError, match="ancora in elaborazione"):
        student_lab_cli.record_help_from_tui(
            assignment=sample_assignment(),
            server_url="https://teacher.test",
            server_token="signed-token",
            help_type="ai",
            prompt="Come procedo?",
            request_id="request-pending-0001",
        )


def test_fetch_help_history_uses_authenticated_server_endpoint(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"assignment_id": "assignment-python-base-somma-001-demo", "events": []}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr(student_lab_cli, "student_api_urlopen", fake_urlopen)

    history = student_lab_cli.fetch_help_history_from_server(
        assignment=sample_assignment(),
        server_url="https://teacher.test:8765/",
        server_token="signed-token",
    )

    assert history["events"] == []
    assert captured["url"].endswith(
        "/api/student-lab/help-history?assignment_id=assignment-python-base-somma-001-demo"
    )
    assert captured["headers"]["Authorization"] == "Bearer signed-token"


def test_fetch_student_lab_payload_uses_authenticated_server_endpoint(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"schema_version": "student_lab.v1", "assignments": []}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr(student_lab_cli, "student_api_urlopen", fake_urlopen)

    payload = student_lab_cli.fetch_student_lab_payload(
        server_url="https://teacher.test:8765",
        server_token="signed-token",
        now="2026-10-18T12:00:00+02:00",
    )

    assert payload["assignments"] == []
    assert "/api/student-lab/assignments?now=" in captured["url"]
    assert captured["headers"]["Authorization"] == "Bearer signed-token"


def test_load_current_payload_enriches_remote_assignment_with_matching_local_paths(monkeypatch, tmp_path) -> None:
    remote_assignment = sample_assignment(
        status="missing",
        workspace={"path": "", "exists": False},
        activity={"path": "", "exists": True, "title": "Titolo autorevole"},
        report={"path": "", "exists": False, "tests": []},
    )
    local_assignment = sample_assignment(
        status="pending",
        workspace={"path": "D:/studenti/rossi/assignments/somma", "exists": True},
        activity={"path": "D:/attivita/somma.json", "exists": True, "title": "Titolo locale"},
        report={"path": "D:/studenti/rossi/reports/somma/latest.json", "exists": True},
    )
    monkeypatch.setattr(
        student_lab_cli,
        "fetch_student_lab_payload",
        lambda **kwargs: sample_payload([remote_assignment]),
    )
    monkeypatch.setattr(
        student_lab_cli,
        "load_payload",
        lambda root, student_id, now=None: sample_payload([local_assignment]),
    )

    payload = student_lab_cli.load_current_payload(
        root=tmp_path,
        student_id="rossi-mario",
        now=None,
        server_url="https://teacher.test",
        server_token="signed-token",
        allow_insecure_http=False,
    )

    assignment = payload["assignments"][0]
    assert assignment["status"] == "missing"
    assert assignment["activity"]["title"] == "Titolo autorevole"
    assert assignment["workspace"] == {"path": "D:/studenti/rossi/assignments/somma", "exists": True}
    assert assignment["activity"]["path"] == "D:/attivita/somma.json"
    assert assignment["report"]["path"] == "D:/studenti/rossi/reports/somma/latest.json"
    assert assignment["report"]["exists"] is True


def test_load_current_payload_keeps_remote_paths_hidden_without_local_match(monkeypatch, tmp_path) -> None:
    remote_assignment = sample_assignment(
        workspace={"path": "", "exists": True},
        activity={"path": "", "exists": True},
        report={"path": "", "exists": False},
    )
    monkeypatch.setattr(
        student_lab_cli,
        "fetch_student_lab_payload",
        lambda **kwargs: sample_payload([remote_assignment]),
    )
    monkeypatch.setattr(
        student_lab_cli,
        "load_payload",
        lambda root, student_id, now=None: sample_payload([sample_assignment(assignment_id="assignment-diversa")]),
    )

    payload = student_lab_cli.load_current_payload(
        root=tmp_path,
        student_id="rossi-mario",
        now=None,
        server_url="https://teacher.test",
        server_token="signed-token",
        allow_insecure_http=False,
    )

    assignment = payload["assignments"][0]
    assert assignment["workspace"]["path"] == ""
    assert assignment["activity"]["path"] == ""
    assert assignment["report"]["path"] == ""


def test_load_current_payload_rejects_local_paths_for_a_different_student(monkeypatch, tmp_path) -> None:
    remote_payload = sample_payload(
        [
            sample_assignment(
                workspace={"path": "", "exists": True},
                activity={"path": "", "exists": True},
                report={"path": "", "exists": False},
            )
        ]
    )
    local_payload = sample_payload(
        [sample_assignment(workspace={"path": "D:/studenti/bianchi/assignments/somma", "exists": True})]
    )
    local_payload["student_id"] = "bianchi-luca"
    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", lambda **kwargs: remote_payload)
    monkeypatch.setattr(
        student_lab_cli,
        "load_payload",
        lambda root, student_id, now=None: local_payload,
    )

    payload = student_lab_cli.load_current_payload(
        root=tmp_path,
        student_id="bianchi-luca",
        now=None,
        server_url="https://teacher.test",
        server_token="token-di-rossi",
        allow_insecure_http=False,
    )

    assert payload["student_id"] == "rossi-mario"
    assert payload["assignments"][0]["workspace"]["path"] == ""


def test_record_help_from_tui_reports_server_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        student_lab_cli,
        "student_api_urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError()),
    )

    try:
        student_lab_cli.record_help_from_tui(
            assignment=sample_assignment(),
            server_url="https://teacher.test:8765",
            server_token="signed-token",
            help_type="ai",
            prompt="Come procedo?",
        )
    except ValueError as error:
        assert "non ha risposto entro il tempo previsto" in str(error)
    else:
        raise AssertionError("Il timeout del server deve essere mostrato come errore TUI")


def test_remote_help_server_requires_https_unless_explicitly_allowed(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(student_lab_cli, "student_api_urlopen", lambda *args, **kwargs: calls.append(args))

    with pytest.raises(ValueError, match="richiede HTTPS"):
        student_lab_cli.record_help_from_tui(
            assignment=sample_assignment(),
            server_url="http://teacher.test:8765",
            server_token="signed-token",
            help_type="ai",
            prompt="Come procedo?",
        )

    assert calls == []
    assert student_lab_cli.validated_server_url("http://127.0.0.1:8765") == "http://127.0.0.1:8765"
    assert student_lab_cli.validated_server_url(
        "http://teacher.test:8765",
        allow_insecure_http=True,
    ) == "http://teacher.test:8765"


def test_student_api_opener_rejects_redirects() -> None:
    handler = next(
        handler
        for handler in student_lab_cli._STUDENT_API_OPENER.handlers
        if isinstance(handler, student_lab_cli._NoRedirectHandler)
    )
    request = student_lab_cli.urllib.request.Request(
        "https://teacher.test/api/student-lab/assignments",
        headers={"Authorization": "Bearer signed-token"},
    )

    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://attacker.test/collect",
    )

    assert redirected is None


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

    def fake_fetch_payload(**kwargs):
        load_calls.append(kwargs)
        return payload

    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", fake_fetch_payload)
    requests = []

    def fake_record_help(**kwargs):
        requests.append(kwargs)
        return {
            "allowed": True,
            "label": "Aiuto AI",
            "response": {
                "status": "ready",
                "provider_label": "Codex locale (macchina docente)",
                "message": "Parti dal primo test fallito.",
            },
        }

    monkeypatch.setattr(student_lab_cli, "record_help_from_tui", fake_record_help)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
        server_url="http://server.test:8765",
        server_token="signed-token",
    )

    assert result == 0
    assert len(load_calls) == 2
    assert all(call["server_token"] == "signed-token" for call in load_calls)
    assert len(requests) == 1
    request = requests[0]
    assert request["assignment"] == payload["assignments"][0]
    assert request["server_url"] == "http://server.test:8765"
    assert request["server_token"] == "signed-token"
    assert request["help_type"] == "ai"
    assert request["prompt"] == "Mi scrivi la soluzione?"
    assert request["allow_insecure_http"] is False
    assert len(request["request_id"]) == 32
    assert request["request_id"].isalnum()
    assert any("Esito richiesta aiuto" in output and "Codex locale" in output for output in outputs)
    assert sum(1 for output in outputs if "Dettaglio consegna" in output) == 2


def test_run_tui_distinguishes_saved_help_from_failed_refresh(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "a", "3", "Come procedo?", "", "", "q"])
    fetch_count = 0

    def fake_fetch_payload(**kwargs):
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count == 2:
            raise ValueError("server temporaneamente non raggiungibile")
        return payload

    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", fake_fetch_payload)
    monkeypatch.setattr(
        student_lab_cli,
        "record_help_from_tui",
        lambda **kwargs: {"allowed": True, "label": "Aiuto AI"},
    )

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
        server_url="https://server.test",
        server_token="signed-token",
    )

    assert result == 0
    assert fetch_count == 2
    assert any("Richiesta salvata, ma aggiornamento dati non disponibile" in output for output in outputs)
    assert not any("Richiesta aiuto non salvata" in output for output in outputs)


def test_run_tui_reuses_request_id_while_help_is_pending(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(
        [
            "1",
            "a",
            "3",
            "Come procedo?",
            "",
            "a",
            "3",
            "Come procedo?",
            "",
            "q",
        ]
    )
    request_ids = []

    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", lambda **kwargs: payload)

    def fake_record_help(**kwargs):
        request_ids.append(kwargs["request_id"])
        raise student_lab_cli.StudentHelpRequestPendingError("ancora in elaborazione")

    monkeypatch.setattr(student_lab_cli, "record_help_from_tui", fake_record_help)

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
        server_url="https://server.test",
        server_token="signed-token",
    )

    assert result == 0
    assert len(request_ids) == 2
    assert request_ids[0] == request_ids[1]
    assert sum("gia salvata e ancora in elaborazione" in output for output in outputs) == 2
    assert not any("Richiesta aiuto non salvata" in output for output in outputs)


def test_run_tui_can_cancel_help_request_type_choice(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "a", "b", "", "", "q"])
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
    assert len(load_calls) == 1
    assert not log_path.exists()
    assert any("Richiesta aiuto annullata." in output for output in outputs)


def test_run_tui_can_cancel_help_request_with_empty_prompt(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "a", "3", "", "", "", "q"])
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
    assert len(load_calls) == 1
    assert not log_path.exists()
    assert any("Richiesta aiuto annullata: prompt vuoto." in output for output in outputs)


def test_run_tui_rejects_invalid_help_type_without_saving(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "a", "x", "", "", "q"])
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
    assert len(load_calls) == 1
    assert not log_path.exists()
    assert any("Tipo aiuto non valido" in output for output in outputs)


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
                        "reason": "La modalità consente richiami teorici e materiali guida.",
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
        lambda assignment, root: {"status": "passed", "passed": True, "summary": {"passed": 1, "total": 1}},
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
    assert any("Esecuzione completata" in output for output in outputs)
    assert any("consegna superata" in output for output in outputs)
    assert any("1/1 test" in output for output in outputs)
    assert any("Report salvato:" in output for output in outputs)
    assert any("Questo report è quello letto da dashboard e registro docente." in output for output in outputs)
    assert not any("Questo report e quello" in output for output in outputs)
    assert sum(1 for output in outputs if "Dettaglio consegna" in output) == 2


def test_run_tui_refreshes_from_server_after_runner_in_remote_mode(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "e", "", "", "q"])
    fetch_calls = []

    def fake_fetch_payload(**kwargs):
        fetch_calls.append(kwargs)
        return payload

    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", fake_fetch_payload)
    local_loads = []

    def fake_load_payload(root, student_id, now=None):
        local_loads.append((root, student_id, now))
        return payload

    monkeypatch.setattr(student_lab_cli, "load_payload", fake_load_payload)
    monkeypatch.setattr(
        student_lab_cli.student_lab_runner,
        "run_local_assignment",
        lambda assignment, root: {"status": "passed", "passed": True, "summary": {"passed": 1, "total": 1}},
    )
    monkeypatch.setattr(
        student_lab_cli.student_lab_runner,
        "write_student_report",
        lambda root, assignment, report: tmp_path / "reports" / "latest.json",
    )

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
        server_url="https://server.test",
        server_token="signed-token",
    )

    assert result == 0
    assert len(fetch_calls) == 2
    assert len(local_loads) == 2
    assert all(call["server_token"] == "signed-token" for call in fetch_calls)
    assert any("Esecuzione completata" in output for output in outputs)


def test_run_tui_keeps_saved_runner_result_when_remote_refresh_fails(monkeypatch, tmp_path) -> None:
    payload = sample_payload()
    outputs = []
    inputs = iter(["1", "e", "", "", "q"])
    fetch_count = 0

    def fake_fetch_payload(**kwargs):
        nonlocal fetch_count
        fetch_count += 1
        if fetch_count == 2:
            raise ValueError("server temporaneamente non disponibile")
        return payload

    monkeypatch.setattr(student_lab_cli, "fetch_student_lab_payload", fake_fetch_payload)
    monkeypatch.setattr(
        student_lab_cli.student_lab_runner,
        "run_local_assignment",
        lambda assignment, root: {"status": "passed", "passed": True, "summary": {"passed": 1, "total": 1}},
    )
    monkeypatch.setattr(
        student_lab_cli.student_lab_runner,
        "write_student_report",
        lambda root, assignment, report: tmp_path / "reports" / "latest.json",
    )

    result = student_lab_cli.run_tui(
        student_id="rossi-mario",
        root=tmp_path,
        input_fn=lambda prompt: next(inputs),
        print_fn=outputs.append,
        clear=False,
        server_url="https://server.test",
        server_token="signed-token",
    )

    assert result == 0
    assert fetch_count == 2
    assert any("Report salvato, ma aggiornamento dati non disponibile" in output for output in outputs)
    assert not any("Runner non disponibile" in output for output in outputs)


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
