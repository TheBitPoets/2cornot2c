from __future__ import annotations

from argparse import ArgumentTypeError, Namespace
from pathlib import Path

import pytest

from scripts import student_lab_service, student_runtime_cli


def test_browser_endpoint_accepts_only_http_or_https() -> None:
    assert student_runtime_cli.safe_browser_endpoint("http://127.0.0.1:9999/session") is True
    assert student_runtime_cli.safe_browser_endpoint("https://lab.example.test/session") is True
    assert student_runtime_cli.safe_browser_endpoint("file:///tmp/answer") is False
    assert student_runtime_cli.safe_browser_endpoint("javascript:alert(1)") is False
    assert student_runtime_cli.safe_browser_endpoint("matlab:open") is False
    assert student_runtime_cli.safe_browser_endpoint("") is False


def test_keep_interactive_runtime_alive_waits_until_operator_interrupt(monkeypatch) -> None:
    calls: list[float] = []

    def interrupt(seconds: float) -> None:
        calls.append(seconds)
        raise KeyboardInterrupt

    monkeypatch.setattr(student_runtime_cli.time, "sleep", interrupt)

    student_runtime_cli.keep_interactive_runtime_alive(poll_seconds=0.125)

    assert calls == [0.125]


def test_positive_int_is_local_and_strict() -> None:
    assert student_runtime_cli.positive_int("7") == 7
    with pytest.raises(ArgumentTypeError):
        student_runtime_cli.positive_int("0")
    with pytest.raises(ArgumentTypeError):
        student_runtime_cli.positive_int("x")


def test_select_assignment_matches_runner_semantics() -> None:
    assignments = [
        {"assignment_id": "a1", "activity_id": "flow-a"},
        {"assignment_id": "a2", "activity_id": "flow-b"},
    ]

    assert student_runtime_cli.select_assignment(assignments, assignment_id="a2") == assignments[1]
    assert student_runtime_cli.select_assignment(assignments, activity_id="flow-a") == assignments[0]

    duplicated = assignments + [{"assignment_id": "a3", "activity_id": "flow-a"}]
    with pytest.raises(ValueError, match="presente in piu consegne"):
        student_runtime_cli.select_assignment(duplicated, activity_id="flow-a")


def test_load_assignment_uses_student_lab_service_payload(monkeypatch, tmp_path: Path) -> None:
    expected = {"assignment_id": "a1", "activity_id": "flow-a"}
    calls: list[dict] = []

    def fake_payload(**kwargs):
        calls.append(kwargs)
        return {"assignments": [expected]}

    monkeypatch.setattr(student_lab_service, "student_lab_payload", fake_payload)
    args = Namespace(
        root=tmp_path,
        student_id="student-1",
        assignment_id=None,
        activity_id="flow-a",
        now="2026-08-30T12:00:00+00:00",
    )

    assert student_runtime_cli.load_assignment(args) == expected
    assert calls == [
        {
            "root": tmp_path.resolve(strict=False),
            "student_id": "student-1",
            "now": "2026-08-30T12:00:00+00:00",
            "expose_external_paths": True,
        }
    ]
