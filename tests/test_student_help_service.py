from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts import student_help_service, student_support_policy
from scripts.student_help_provider import StudentHelpResponse


class RecordingHelpProvider:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.requests = []

    def respond(self, request):
        self.requests.append(request)
        if self.fail:
            raise RuntimeError("Provider non raggiungibile: token=segreto-di-prova")
        return StudentHelpResponse(
            status="ready",
            provider="test-provider",
            provider_label="Provider test",
            message="Prova un caso minimo e confronta il risultato.",
            usage={"input_tokens": 3, "output_tokens": 7, "total_tokens": 10},
        )


def test_server_help_log_path_encodes_non_portable_identifiers(tmp_path) -> None:
    path = student_help_service.server_help_log_path(
        tmp_path,
        "Rossi Mario",
        "Compito è 1/../segreto",
    )

    assert path.is_relative_to(tmp_path / "teacher-help-events")
    assert path.name == "events.json"
    assert ".." not in path.relative_to(tmp_path).parts
    assert "Rossi Mario" not in str(path)


def test_server_help_log_path_separates_portable_id_from_encoded_lookalike(tmp_path) -> None:
    first = student_help_service.server_help_log_path(tmp_path, "A", "assignment-001")
    second = student_help_service.server_help_log_path(
        tmp_path,
        "a-559aead08264d579",
        "assignment-001",
    )

    assert first != second
    assert first.parent.name == second.parent.name
    assert first.parent.parent != second.parent.parent


def test_read_help_log_rejects_file_above_size_limit(tmp_path) -> None:
    log_path = tmp_path / "events.json"
    with log_path.open("wb") as stream:
        stream.truncate(student_help_service.MAX_HELP_LOG_BYTES + 1)

    events, error = student_help_service.read_help_log(log_path)

    assert events == []
    assert "troppo grande" in error


def test_read_help_log_reports_invalid_utf8_without_raising(tmp_path) -> None:
    log_path = tmp_path / "events.json"
    log_path.write_bytes(b"\xff\xfe{")

    events, error = student_help_service.read_help_log(log_path)

    assert events == []
    assert error == "Encoding del log aiuti non valido: atteso UTF-8."


def test_write_help_events_rejects_payload_above_read_limit(tmp_path) -> None:
    log_path = tmp_path / "events.json"

    with pytest.raises(student_help_service.StudentHelpRateLimitError, match="Limite spazio"):
        student_help_service.write_help_events(
            log_path,
            [{"prompt": "x" * (student_help_service.MAX_HELP_LOG_BYTES + 1)}],
        )

    assert not log_path.exists()


def test_write_help_events_syncs_created_tree_and_parent_after_replace(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "help" / "student" / "events.json"
    synced = []
    monkeypatch.setattr(
        student_help_service.assignment_records,
        "sync_directory",
        lambda path: synced.append(path),
    )

    student_help_service.write_help_events(log_path, [{"request_id": "request-000000000001"}])

    assert synced == [tmp_path, tmp_path / "help", log_path.parent]


def test_maximum_help_history_remains_readable_with_utf8_content(tmp_path) -> None:
    log_path = tmp_path / "events.json"
    events = [
        {
            "request_id": f"request-{index:016d}",
            "prompt": "\U0001f4a1" * 2_000,
            "response": {"message": "\U0001f4a1" * student_help_service.MAX_PROVIDER_MESSAGE_CHARS},
        }
        for index in range(student_help_service.MAX_HELP_EVENTS_PER_ASSIGNMENT)
    ]

    student_help_service.write_help_events(log_path, events)
    loaded, error = student_help_service.read_help_log(log_path)

    assert error == ""
    assert len(loaded) == student_help_service.MAX_HELP_EVENTS_PER_ASSIGNMENT
    assert log_path.stat().st_size <= student_help_service.MAX_HELP_LOG_BYTES


class NonSerializableHelpProvider:
    def respond(self, request):
        return StudentHelpResponse(
            status="ready",
            provider="malformed-provider",
            provider_label="Provider malformato",
            message="Risposta apparentemente valida.",
            usage={"input_tokens": object(), "output_tokens": 0, "total_tokens": 0},
        )


class StructuredErrorHelpProvider:
    def respond(self, request):
        return StudentHelpResponse(
            status="error",
            provider="structured-error-provider",
            provider_label="Provider con errore strutturato",
            message="Stack trace remoto: api_key=segreto-nel-messaggio",
            usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            detail="Errore remoto: token=segreto-strutturato",
        )


def test_evaluate_help_request_denies_ai_when_policy_does_not_allow_it() -> None:
    policy = student_support_policy.support_policy("feedback-tecnico")

    decision = student_help_service.evaluate_help_request(policy, "ai")

    assert decision["help_type"] == "ai"
    assert decision["label"] == "Aiuto AI"
    assert decision["allowed"] is False
    assert "non consente aiuto AI" in decision["reason"]


def test_evaluate_help_request_allows_theory_for_guided_study() -> None:
    policy = student_support_policy.support_policy("studio-guidato")

    decision = student_help_service.evaluate_help_request(policy, "teoria")

    assert decision["help_type"] == "teoria"
    assert decision["allowed"] is True
    assert "richiami teorici" in decision["reason"]


def test_record_help_request_appends_event_and_summary(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    policy = student_support_policy.support_policy("ai-assisted")

    event = student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Dammi un suggerimento, non la soluzione.",
        now="2026-10-18T10:30:00+02:00",
    )

    log_path = repo / "help" / "python-base-somma-001" / "events.json"
    payload = json.loads(log_path.read_text(encoding="utf-8"))
    summary = student_help_service.help_summary(log_path)

    assert event["allowed"] is True
    assert payload["schema_version"] == "student_help_log.v1"
    assert payload["events"][0]["prompt"] == "Dammi un suggerimento, non la soluzione."
    assert summary["total"] == 1
    assert summary["allowed"] == 1
    assert summary["denied"] == 0
    assert summary["last_decision"] == "consentita"


def test_record_help_request_persists_provider_response_for_allowed_request(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    policy = student_support_policy.support_policy("ai-assisted")
    provider = RecordingHelpProvider()

    event = student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Come posso trovare il caso che fallisce?",
        provider=provider,
        context={"failed_tests": ["test_negativi"]},
    )

    assert len(provider.requests) == 1
    assert provider.requests[0].context == {"failed_tests": ["test_negativi"]}
    assert event["response"]["status"] == "ready"
    assert event["response"]["message"].startswith("Prova un caso minimo")
    assert event["response"]["usage"]["total_tokens"] == 10
    log_path = repo / "help" / "python-base-somma-001" / "events.json"
    summary = student_help_service.help_summary(log_path)
    teacher_summary = student_help_service.teacher_help_summary(log_path)
    assert summary["last_response_status"] == "ready"
    assert summary["last_response_provider"] == "Provider test"
    assert teacher_summary["events"][0]["response"]["message"].startswith("Prova un caso minimo")
    assert teacher_summary["events"][0]["response"]["usage"]["total_tokens"] == 10
    assert teacher_summary["events"][0]["provider_status"] == "completed"


def test_teacher_help_summary_exposes_only_known_provider_states(tmp_path) -> None:
    log_path = tmp_path / "teacher-help-events" / "student" / "assignment" / "events.json"
    student_help_service.write_help_events(
        log_path,
        [
            {
                "schema_version": student_help_service.HELP_EVENT_SCHEMA_VERSION,
                "request_id": "request-provider-pending-0001",
                "requested_at": "2026-10-20T08:00:00+02:00",
                "activity_id": "activity-demo",
                "help_type": "ai",
                "label": "Aiuto AI",
                "allowed": True,
                "reason": "Consentita.",
                "prompt": "Come procedo?",
                "provider_status": "pending",
            },
            {
                "schema_version": student_help_service.HELP_EVENT_SCHEMA_VERSION,
                "request_id": "request-provider-unknown-0002",
                "requested_at": "2026-10-20T08:01:00+02:00",
                "activity_id": "activity-demo",
                "help_type": "ai",
                "label": "Aiuto AI",
                "allowed": True,
                "reason": "Consentita.",
                "prompt": "E ora?",
                "provider_status": "dettaglio-interno-non-previsto",
            },
        ],
    )

    summary = student_help_service.teacher_help_summary(log_path)

    assert summary["events"][0]["provider_status"] == "pending"
    assert "provider_status" not in summary["events"][1]


def test_record_help_request_deduplicates_retried_request_id(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    policy = student_support_policy.support_policy("ai-assisted")
    provider = RecordingHelpProvider()
    request = {
        "repo_path": repo,
        "activity_id": "python-base-somma-001",
        "support_policy": policy,
        "help_type": "ai",
        "prompt": "Come posso trovare il caso che fallisce?",
        "provider": provider,
        "request_id": "retry-request-0001",
    }

    first = student_help_service.record_help_request(**request)
    second = student_help_service.record_help_request(**request)

    log_path = repo / "help" / "python-base-somma-001" / "events.json"
    assert second == first
    assert len(provider.requests) == 1
    assert student_help_service.help_summary(log_path)["total"] == 1


def test_record_help_request_rejects_retry_while_provider_is_pending(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    activity_id = "python-base-somma-001"
    log_path = student_help_service.help_log_path(repo, activity_id)
    student_help_service.write_help_events(
        log_path,
        [
            {
                "schema_version": student_help_service.HELP_EVENT_SCHEMA_VERSION,
                "request_id": "pending-request-0001",
                "requested_at": "2026-10-18T10:00:00+02:00",
                "activity_id": activity_id,
                "help_type": "ai",
                "prompt": "Come trovo il caso limite?",
                "provider_status": "pending",
                "budget_charged": True,
            }
        ],
    )

    with pytest.raises(student_help_service.StudentHelpPendingError, match="ancora in elaborazione"):
        student_help_service.record_help_request(
            repo_path=repo,
            activity_id=activity_id,
            support_policy=student_support_policy.support_policy("ai-assisted"),
            help_type="ai",
            prompt="Come trovo il caso limite?",
            request_id="pending-request-0001",
            now="2026-10-18T10:01:00+02:00",
        )


def test_record_help_request_rejects_reused_id_with_different_prompt(tmp_path) -> None:
    request = {
        "repo_path": tmp_path / "student-repo",
        "activity_id": "python-base-somma-001",
        "support_policy": student_support_policy.support_policy("ai-assisted"),
        "help_type": "teoria",
        "prompt": "Prima richiesta",
        "request_id": "conflict-request-01",
    }
    student_help_service.record_help_request(**request)

    with pytest.raises(ValueError, match="gia usato"):
        student_help_service.record_help_request(**{**request, "prompt": "Seconda richiesta"})


def test_record_help_request_does_not_call_provider_when_policy_blocks_request(tmp_path) -> None:
    provider = RecordingHelpProvider()

    event = student_help_service.record_help_request(
        repo_path=tmp_path / "student-repo",
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("feedback-tecnico"),
        help_type="ai",
        prompt="Dammi un suggerimento.",
        provider=provider,
    )

    assert provider.requests == []
    assert "response" not in event


def test_record_help_request_audits_ai_when_provider_factory_fails(tmp_path) -> None:
    def failing_provider_factory():
        raise ValueError("Configurazione provider non valida.")

    event = student_help_service.record_help_request(
        repo_path=tmp_path / "student-repo",
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("ai-assisted"),
        help_type="ai",
        prompt="Dammi un suggerimento.",
        provider_factory=failing_provider_factory,
    )

    log_path = tmp_path / "student-repo" / "help" / "python-base-somma-001" / "events.json"
    assert event["provider_status"] == "completed"
    assert event["response"]["status"] == "error"
    assert event["response"]["provider"] == "unavailable"
    assert student_help_service.help_summary(log_path)["total"] == 1


def test_record_help_request_skips_ai_factory_for_local_help(tmp_path) -> None:
    provider = RecordingHelpProvider()

    event = student_help_service.record_help_request(
        repo_path=tmp_path / "student-repo",
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("studio-guidato"),
        help_type="teoria",
        prompt="Ricordami il concetto.",
        provider=provider,
        provider_factory=lambda: pytest.fail("La factory AI non va risolta per un aiuto locale."),
    )

    assert event["response"]["status"] == "ready"
    assert len(provider.requests) == 1


def test_record_help_request_persists_provider_error_without_losing_request(tmp_path) -> None:
    provider = RecordingHelpProvider(fail=True)

    event = student_help_service.record_help_request(
        repo_path=tmp_path / "student-repo",
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("ai-assisted"),
        help_type="ai",
        prompt="Dammi un suggerimento.",
        provider=provider,
    )

    log_path = tmp_path / "student-repo" / "help" / "python-base-somma-001" / "events.json"
    persisted_text = log_path.read_text(encoding="utf-8")

    assert event["allowed"] is True
    assert event["response"]["status"] == "error"
    assert event["response"]["detail"] == student_help_service.PROVIDER_ERROR_DETAIL
    assert "segreto-di-prova" not in persisted_text
    assert "non raggiungibile" not in persisted_text


def test_record_help_request_persists_request_when_provider_response_is_not_json_safe(tmp_path) -> None:
    repo = tmp_path / "student-repo"

    event = student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("ai-assisted"),
        help_type="ai",
        prompt="Conserva questa richiesta.",
        provider=NonSerializableHelpProvider(),
    )

    log_path = repo / "help" / "python-base-somma-001" / "events.json"
    persisted = json.loads(log_path.read_text(encoding="utf-8"))["events"][0]

    assert event["response"]["status"] == "error"
    assert persisted["prompt"] == "Conserva questa richiesta."
    assert persisted["response"]["status"] == "error"
    assert persisted["response"]["usage"] == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def test_record_help_request_sanitizes_structured_provider_errors(tmp_path) -> None:
    repo = tmp_path / "student-repo"

    event = student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("ai-assisted"),
        help_type="ai",
        prompt="Conserva la richiesta senza il segreto.",
        provider=StructuredErrorHelpProvider(),
    )

    log_path = repo / "help" / "python-base-somma-001" / "events.json"
    persisted_text = log_path.read_text(encoding="utf-8")

    assert event["response"]["status"] == "error"
    assert event["response"]["message"] == ""
    assert event["response"]["detail"] == student_help_service.PROVIDER_ERROR_DETAIL
    assert "segreto-nel-messaggio" not in persisted_text
    assert "Stack trace remoto" not in persisted_text
    assert "segreto-strutturato" not in persisted_text
    assert "Errore remoto" not in persisted_text


def test_record_help_request_blocks_ai_when_budget_is_exhausted(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    policy = dict(student_support_policy.support_policy("ai-assisted"))
    policy["ai_request_limit"] = 1

    first = student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Dammi un suggerimento.",
        now="2026-10-18T10:30:00+02:00",
    )
    second = student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Altro suggerimento.",
        now="2026-10-18T10:35:00+02:00",
    )

    log_path = repo / "help" / "python-base-somma-001" / "events.json"
    budget = student_help_service.help_budget_summary(log_path, policy)
    summary = student_help_service.help_summary(log_path)

    assert first["allowed"] is True
    assert second["allowed"] is False
    assert second["reason"] == "Budget richieste AI esaurito per questa consegna."
    assert second["budget"]["exhausted"] is True
    assert budget == {"limit": 1, "used": 1, "remaining": 0, "exhausted": True}
    assert summary["allowed"] == 1
    assert summary["denied"] == 1


def test_record_help_request_stops_when_assignment_log_limit_is_reached(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "student-repo"
    policy = student_support_policy.support_policy("studio-guidato")
    monkeypatch.setattr(student_help_service, "MAX_HELP_EVENTS_PER_ASSIGNMENT", 1)
    student_help_service.record_help_request(
        repo_path=repo,
        activity_id="activity",
        support_policy=policy,
        help_type="teoria",
        prompt="Prima richiesta.",
    )

    with pytest.raises(student_help_service.StudentHelpRateLimitError, match="Limite richieste"):
        student_help_service.record_help_request(
            repo_path=repo,
            activity_id="activity",
            support_policy=policy,
            help_type="teoria",
            prompt="Richiesta oltre il limite.",
        )

    assert len(student_help_service.load_help_events(student_help_service.help_log_path(repo, "activity"))) == 1


def test_concurrent_ai_requests_share_budget_and_preserve_both_events(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    policy = dict(student_support_policy.support_policy("ai-assisted"))
    policy["ai_request_limit"] = 1
    entered = threading.Event()
    release = threading.Event()

    class BlockingProvider(RecordingHelpProvider):
        def respond(self, request):
            entered.set()
            assert release.wait(timeout=2)
            return super().respond(request)

    provider = BlockingProvider()

    def record(prompt):
        return student_help_service.record_help_request(
            repo_path=repo,
            activity_id="python-base-somma-001",
            support_policy=policy,
            help_type="ai",
            prompt=prompt,
            provider=provider,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(record, "Prima richiesta")
        assert entered.wait(timeout=2)
        second_future = executor.submit(record, "Seconda richiesta")
        time.sleep(0.05)
        assert len(provider.requests) == 0
        release.set()
        first = first_future.result(timeout=2)
        second = second_future.result(timeout=2)

    events = student_help_service.load_help_events(
        repo / "help" / "python-base-somma-001" / "events.json"
    )
    assert first["allowed"] is True
    assert second["allowed"] is False
    assert second["reason"] == "Budget richieste AI esaurito per questa consegna."
    assert len(provider.requests) == 1
    assert [event["prompt"] for event in events] == ["Prima richiesta", "Seconda richiesta"]


def test_concurrent_allowed_requests_do_not_hold_log_lock_during_provider_call(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    policy = dict(student_support_policy.support_policy("ai-assisted"))
    policy["ai_request_limit"] = 2
    first_entered = threading.Event()
    second_entered = threading.Event()
    release_first = threading.Event()
    call_lock = threading.Lock()
    call_count = 0

    class ConcurrentProvider(RecordingHelpProvider):
        def respond(self, request):
            nonlocal call_count
            with call_lock:
                call_count += 1
                current = call_count
            if current == 1:
                first_entered.set()
                assert release_first.wait(timeout=2)
            else:
                second_entered.set()
            return super().respond(request)

    provider = ConcurrentProvider()

    def record(prompt):
        return student_help_service.record_help_request(
            repo_path=repo,
            activity_id="python-base-somma-001",
            support_policy=policy,
            help_type="ai",
            prompt=prompt,
            provider=provider,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(record, "Prima richiesta")
        assert first_entered.wait(timeout=2)
        second_future = executor.submit(record, "Seconda richiesta")
        assert second_entered.wait(timeout=2)
        second = second_future.result(timeout=2)
        release_first.set()
        first = first_future.result(timeout=2)

    events = student_help_service.load_help_events(
        repo / "help" / "python-base-somma-001" / "events.json"
    )
    assert first["response"]["status"] == "ready"
    assert second["response"]["status"] == "ready"
    assert len(events) == 2
    assert all(event.get("response", {}).get("status") == "ready" for event in events)


def test_stale_provider_reservation_is_released_after_server_restart(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    activity_id = "python-base-somma-001"
    log_path = student_help_service.help_log_path(repo, activity_id)
    policy = dict(student_support_policy.support_policy("ai-assisted"))
    policy["ai_request_limit"] = 1
    student_help_service.write_help_events(
        log_path,
        [
            {
                "schema_version": student_help_service.HELP_EVENT_SCHEMA_VERSION,
                "request_id": "orphaned-request",
                "requested_at": "2026-10-18T10:00:00+02:00",
                "activity_id": activity_id,
                "help_type": "ai",
                "label": "Aiuto AI",
                "allowed": True,
                "reason": "Richiesta avviata.",
                "prompt": "Richiesta rimasta senza risposta.",
                "budget_charged": True,
                "provider_status": "pending",
            }
        ],
    )

    event = student_help_service.record_help_request(
        repo_path=repo,
        activity_id=activity_id,
        support_policy=policy,
        help_type="ai",
        prompt="Nuova richiesta dopo il riavvio.",
        now="2026-10-18T10:06:00+02:00",
    )

    events = student_help_service.load_help_events(log_path)
    assert event["allowed"] is True
    assert events[0]["provider_status"] == "interrupted"
    assert events[0]["budget_charged"] is False
    assert events[0]["response"]["status"] == "error"
    assert student_help_service.ai_budget_status(policy, events)["used"] == 1


def test_reading_summary_releases_stale_provider_reservation(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "events.json"
    policy = dict(student_support_policy.support_policy("ai-assisted"))
    student_help_service.write_help_events(
        log_path,
        [
            {
                "requested_at": "2026-10-18T10:00:00+02:00",
                "help_type": "ai",
                "allowed": True,
                "budget_charged": True,
                "provider_status": "pending",
            }
        ],
    )

    monkeypatch.setattr(
        student_help_service,
        "reconciliation_now",
        lambda: "2026-10-18T10:06:00+02:00",
    )
    summary = student_help_service.help_summary(log_path, "9999-01-01T00:00:00+00:00")
    budget = student_help_service.help_budget_summary(log_path, policy, "9999-01-01T00:00:00+00:00")

    persisted = student_help_service.load_help_events(log_path)[0]
    assert summary["last_response_status"] == "error"
    assert budget["used"] == 0
    assert persisted["provider_status"] == "interrupted"
    assert persisted["budget_charged"] is False


def test_simulated_view_time_cannot_release_active_provider_reservation(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "events.json"
    student_help_service.write_help_events(
        log_path,
        [
            {
                "requested_at": "2026-10-18T10:00:00+02:00",
                "help_type": "ai",
                "allowed": True,
                "budget_charged": True,
                "provider_status": "pending",
            }
        ],
    )
    monkeypatch.setattr(
        student_help_service,
        "reconciliation_now",
        lambda: "2026-10-18T10:01:00+02:00",
    )

    student_help_service.help_summary(log_path, "9999-01-01T00:00:00+00:00")

    persisted = student_help_service.load_help_events(log_path)[0]
    assert persisted["provider_status"] == "pending"
    assert persisted["budget_charged"] is True


def test_record_help_request_does_not_overwrite_corrupt_log(tmp_path) -> None:
    repo = tmp_path / "student-repo"
    log_path = student_help_service.help_log_path(repo, "activity")
    log_path.parent.mkdir(parents=True)
    log_path.write_text("{json-troncato", encoding="utf-8")

    with pytest.raises(RuntimeError, match="intervento docente necessario"):
        student_help_service.record_help_request(
            repo_path=repo,
            activity_id="activity",
            support_policy=student_support_policy.support_policy("ai-assisted"),
            help_type="ai",
            prompt="Nuova richiesta.",
        )

    assert log_path.read_text(encoding="utf-8") == "{json-troncato"
    assert student_help_service.help_budget_summary(
        log_path,
        student_support_policy.support_policy("ai-assisted"),
    ) == {"limit": 5, "used": 5, "remaining": 0, "exhausted": True}


def test_atomic_log_write_preserves_previous_file_when_replace_fails(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "events.json"
    original_events = [{"request_id": "existing"}]
    student_help_service.write_help_events(log_path, original_events)

    def fail_replace(source, destination):
        raise OSError("replace non riuscito")

    monkeypatch.setattr(student_help_service.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace non riuscito"):
        student_help_service.write_help_events(log_path, [{"request_id": "new"}])

    assert student_help_service.load_help_events(log_path) == original_events
    assert list(tmp_path.glob(".*.tmp")) == []


def test_help_summary_marks_invalid_json_without_raising(tmp_path) -> None:
    log_path = tmp_path / "student-repo" / "help" / "activity" / "events.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text("{non-json", encoding="utf-8")

    summary = student_help_service.help_summary(log_path)

    assert summary["status"] == "invalid"
    assert summary["error"].startswith("JSON non valido")
    assert summary["total"] == 0
    assert summary["allowed"] == 0
