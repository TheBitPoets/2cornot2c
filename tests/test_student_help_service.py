from __future__ import annotations

import json

from scripts import student_help_service, student_support_policy
from scripts.student_help_provider import StudentHelpResponse


class RecordingHelpProvider:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.requests = []

    def respond(self, request):
        self.requests.append(request)
        if self.fail:
            raise RuntimeError("Provider di prova non raggiungibile")
        return StudentHelpResponse(
            status="ready",
            provider="test-provider",
            provider_label="Provider test",
            message="Prova un caso minimo e confronta il risultato.",
            usage={"input_tokens": 3, "output_tokens": 7, "total_tokens": 10},
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

    assert event["allowed"] is True
    assert event["response"]["status"] == "error"
    assert "non raggiungibile" in event["response"]["detail"]


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


def test_help_summary_marks_invalid_json_without_raising(tmp_path) -> None:
    log_path = tmp_path / "student-repo" / "help" / "activity" / "events.json"
    log_path.parent.mkdir(parents=True)
    log_path.write_text("{non-json", encoding="utf-8")

    summary = student_help_service.help_summary(log_path)

    assert summary["status"] == "invalid"
    assert summary["error"].startswith("JSON non valido")
    assert summary["total"] == 0
    assert summary["allowed"] == 0
