from __future__ import annotations

import json

from scripts import student_help_service, student_support_policy


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
