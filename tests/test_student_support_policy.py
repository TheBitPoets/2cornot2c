from __future__ import annotations

from scripts import student_support_policy


def test_support_policy_exposes_known_ai_assisted_mode() -> None:
    policy = student_support_policy.support_policy("ai-assisted")

    assert policy["mode"] == "ai-assisted"
    assert policy["label"] == "AI assisted"
    assert policy["ai_allowed"] is True
    assert policy["theory_allowed"] is True
    assert policy["debug_allowed"] is True
    assert policy["ai_request_limit"] == 5
    assert "suggerimenti AI controllati" in policy["allowed"]


def test_support_policy_defaults_unknown_mode_to_technical_feedback() -> None:
    policy = student_support_policy.support_policy("modalita-sconosciuta")

    assert policy["mode"] == "feedback-tecnico"
    assert policy["source_mode"] == "modalita-sconosciuta"
    assert policy["is_defaulted"] is True
    assert policy["ai_allowed"] is False
    assert policy["ai_request_limit"] == 0
    assert policy["debug_allowed"] is True
