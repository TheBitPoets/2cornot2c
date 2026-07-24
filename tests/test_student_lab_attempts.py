from __future__ import annotations

import json

import pytest

from scripts import student_lab_attempts


ASSIGNMENT_ID = "assignment-python-somma-rossi-2026"
ACTIVITY_ID = "python-somma"


def report(*, attempt_id: str, passed: bool, tests_passed: int, tests_total: int, submitted_at: str) -> dict:
    """Return one persisted runner report used by history tests."""

    return {
        "schema_version": "student_lab_run.v1",
        "attempt_id": attempt_id,
        "assignment_id": ASSIGNMENT_ID,
        "activity_id": ACTIVITY_ID,
        "student_id": "rossi-mario",
        "status": "passed" if passed else "failed",
        "passed": passed,
        "submitted_at": submitted_at,
        "summary": {"passed": tests_passed, "total": tests_total},
        "tests": [],
    }


def write_attempt(report_path, payload: dict) -> None:
    """Write one attempt in the canonical test directory."""

    history_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
    path = history_dir / "attempts" / f"{payload['attempt_id']}.json"
    student_lab_attempts.write_json_atomic(path, payload)


def test_assignment_storage_key_is_stable_and_filesystem_safe() -> None:
    first = student_lab_attempts.assignment_storage_key("Consegna / ../ Rossi")
    second = student_lab_attempts.assignment_storage_key("Consegna / ../ Rossi")

    assert first == second
    assert "/" not in first
    assert "\\" not in first
    assert ".." not in first
    assert first.endswith("-1e7d85554a1f")


def test_load_attempts_isolates_assignment_and_activity(tmp_path) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    valid = report(
        attempt_id="attempt-valid",
        passed=True,
        tests_passed=2,
        tests_total=2,
        submitted_at="2026-10-18T12:00:00+02:00",
    )
    write_attempt(report_path, valid)
    wrong_assignment = {**valid, "attempt_id": "attempt-wrong-assignment", "assignment_id": "other"}
    write_attempt(report_path, wrong_assignment)
    wrong_activity = {**valid, "attempt_id": "attempt-wrong-activity", "activity_id": "other"}
    write_attempt(report_path, wrong_activity)

    attempts = student_lab_attempts.load_attempts(report_path, ASSIGNMENT_ID, ACTIVITY_ID)

    assert attempts == [valid]


def test_load_attempts_skips_corrupt_and_oversized_reports(tmp_path) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    attempts_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID) / "attempts"
    attempts_dir.mkdir(parents=True)
    (attempts_dir / "attempt-corrupt.json").write_text("{", encoding="utf-8")
    (attempts_dir / "attempt-large.json").write_text("x" * (2 * 1024 * 1024 + 1), encoding="utf-8")

    assert student_lab_attempts.load_attempts(report_path, ASSIGNMENT_ID, ACTIVITY_ID) == []


def test_best_attempt_prefers_complete_result_and_latest_breaks_ties() -> None:
    partial = report(
        attempt_id="attempt-1",
        passed=False,
        tests_passed=3,
        tests_total=4,
        submitted_at="2026-10-18T10:00:00+02:00",
    )
    complete_old = report(
        attempt_id="attempt-2",
        passed=True,
        tests_passed=2,
        tests_total=2,
        submitted_at="2026-10-18T11:00:00+02:00",
    )
    complete_new = report(
        attempt_id="attempt-3",
        passed=True,
        tests_passed=2,
        tests_total=2,
        submitted_at="2026-10-18T12:00:00+02:00",
    )

    assert student_lab_attempts.select_best_attempt([partial, complete_new, complete_old]) == complete_new
    assert student_lab_attempts.select_latest_attempt([partial, complete_new, complete_old]) == complete_new


def test_final_attempt_remains_selected_after_a_new_attempt(tmp_path) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    selected = report(
        attempt_id="attempt-selected",
        passed=True,
        tests_passed=2,
        tests_total=2,
        submitted_at="2026-10-18T11:00:00+02:00",
    )
    newer = report(
        attempt_id="attempt-newer",
        passed=False,
        tests_passed=1,
        tests_total=2,
        submitted_at="2026-10-18T12:00:00+02:00",
    )
    write_attempt(report_path, selected)
    student_lab_attempts.set_final_attempt(report_path, ASSIGNMENT_ID, ACTIVITY_ID, "attempt-selected")
    write_attempt(report_path, newer)

    assert student_lab_attempts.load_final_attempt(report_path, ASSIGNMENT_ID, ACTIVITY_ID) == selected
    assert student_lab_attempts.select_latest_attempt(
        student_lab_attempts.load_attempts(report_path, ASSIGNMENT_ID, ACTIVITY_ID)
    ) == newer


def test_set_final_attempt_rejects_unknown_id_without_changing_selection(tmp_path) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    selected = report(
        attempt_id="attempt-selected",
        passed=True,
        tests_passed=2,
        tests_total=2,
        submitted_at="2026-10-18T11:00:00+02:00",
    )
    write_attempt(report_path, selected)
    final_path = student_lab_attempts.set_final_attempt(
        report_path,
        ASSIGNMENT_ID,
        ACTIVITY_ID,
        "attempt-selected",
    )
    original = json.loads(final_path.read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="Tentativo non trovato"):
        student_lab_attempts.set_final_attempt(report_path, ASSIGNMENT_ID, ACTIVITY_ID, "../unknown")

    assert json.loads(final_path.read_text(encoding="utf-8")) == original
