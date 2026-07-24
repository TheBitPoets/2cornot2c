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


def test_latest_attempt_compares_timezone_offsets_in_utc() -> None:
    earlier = report(
        attempt_id="attempt-earlier",
        passed=True,
        tests_passed=1,
        tests_total=1,
        submitted_at="2026-10-18T12:00:00+02:00",
    )
    later = report(
        attempt_id="attempt-later",
        passed=True,
        tests_passed=1,
        tests_total=1,
        submitted_at="2026-10-18T11:30:00+00:00",
    )

    assert student_lab_attempts.select_latest_attempt([later, earlier]) == later


def test_persist_attempt_never_replaces_an_existing_attempt(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    monkeypatch.setattr(student_lab_attempts, "new_attempt_id", lambda: "attempt-fixed")
    original = report(
        attempt_id="ignored",
        passed=False,
        tests_passed=0,
        tests_total=1,
        submitted_at="2026-10-18T10:00:00+02:00",
    )
    student_lab_attempts.persist_attempt(report_path, ASSIGNMENT_ID, original)
    attempt_path = (
        student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
        / "attempts"
        / "attempt-fixed.json"
    )
    original_bytes = attempt_path.read_bytes()

    with pytest.raises(ValueError, match="ID tentativo già esistente"):
        student_lab_attempts.persist_attempt(report_path, ASSIGNMENT_ID, {**original, "passed": True})

    assert attempt_path.read_bytes() == original_bytes


def test_exclusive_write_falls_back_when_hard_links_are_unsupported(tmp_path, monkeypatch) -> None:
    output = tmp_path / "attempt.json"
    payload = {"attempt_id": "attempt-exfat", "passed": True}

    def unsupported_link(source, destination):
        error = OSError("hard links unsupported")
        error.winerror = 1
        raise error

    monkeypatch.setattr(student_lab_attempts.os, "link", unsupported_link)

    student_lab_attempts.write_json_exclusive(output, payload, base_dir=tmp_path)

    assert json.loads(output.read_text(encoding="utf-8")) == payload
    with pytest.raises(FileExistsError):
        student_lab_attempts.write_json_exclusive(output, {**payload, "passed": False}, base_dir=tmp_path)
    assert json.loads(output.read_text(encoding="utf-8")) == payload


def test_exclusive_write_does_not_mask_unrelated_link_errors(tmp_path, monkeypatch) -> None:
    output = tmp_path / "attempt.json"

    def denied_link(source, destination):
        raise PermissionError("link denied")

    monkeypatch.setattr(student_lab_attempts.os, "link", denied_link)

    with pytest.raises(PermissionError, match="link denied"):
        student_lab_attempts.write_json_exclusive(
            output,
            {"attempt_id": "attempt-denied"},
            base_dir=tmp_path,
        )

    assert not output.exists()


def test_exclusive_attempt_is_removed_when_directory_sync_fails(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    monkeypatch.setattr(student_lab_attempts, "new_attempt_id", lambda: "attempt-sync-failure")
    monkeypatch.setattr(
        student_lab_attempts,
        "sync_directory",
        lambda path: (_ for _ in ()).throw(OSError("sync failed")),
    )

    with pytest.raises(OSError, match="sync failed"):
        student_lab_attempts.persist_attempt(
            report_path,
            ASSIGNMENT_ID,
            report(
                attempt_id="ignored",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at="2026-10-18T10:00:00+02:00",
            ),
        )

    history_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
    assert not (history_dir / "attempts" / "attempt-sync-failure.json").exists()


def test_persist_standard_report_rolls_back_when_legacy_latest_fails(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    original_write = student_lab_attempts.write_json_atomic
    failed = False

    def fail_legacy_once(path, payload, **kwargs):
        nonlocal failed
        if path == report_path and not failed:
            failed = True
            raise OSError("legacy write failed")
        return original_write(path, payload, **kwargs)

    monkeypatch.setattr(student_lab_attempts, "write_json_atomic", fail_legacy_once)

    with pytest.raises(OSError, match="legacy write failed"):
        student_lab_attempts.persist_standard_report(
            report_path,
            ASSIGNMENT_ID,
            report(
                attempt_id="ignored",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at="2026-10-18T10:00:00+02:00",
            ),
            base_dir=tmp_path,
        )

    history_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
    assert list((history_dir / "attempts").glob("attempt-*.json")) == []
    assert not (history_dir / "latest.json").exists()
    assert not report_path.exists()


def test_persist_attempt_rolls_back_when_assignment_latest_fails(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    history_latest = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID) / "latest.json"
    original_write = student_lab_attempts.write_json_atomic

    def fail_assignment_latest(path, payload, **kwargs):
        if path == history_latest:
            raise OSError("assignment latest failed")
        return original_write(path, payload, **kwargs)

    monkeypatch.setattr(student_lab_attempts, "write_json_atomic", fail_assignment_latest)

    with pytest.raises(OSError, match="assignment latest failed"):
        student_lab_attempts.persist_standard_report(
            report_path,
            ASSIGNMENT_ID,
            report(
                attempt_id="ignored",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at="2026-10-18T10:00:00+02:00",
            ),
            base_dir=tmp_path,
        )

    history_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
    assert list((history_dir / "attempts").glob("attempt-*.json")) == []
    assert not history_latest.exists()
    assert not report_path.exists()


def test_persist_attempt_rolls_back_when_existing_latest_is_corrupt(tmp_path) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    history_latest = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID) / "latest.json"
    history_latest.parent.mkdir(parents=True)
    history_latest.write_text("{", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        student_lab_attempts.persist_standard_report(
            report_path,
            ASSIGNMENT_ID,
            report(
                attempt_id="ignored",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at="2026-10-18T10:00:00+02:00",
            ),
            base_dir=tmp_path,
        )

    history_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
    assert list((history_dir / "attempts").glob("attempt-*.json")) == []
    assert history_latest.read_text(encoding="utf-8") == "{"
    assert not report_path.exists()


def test_persist_standard_report_rejects_symlinked_history_parent(tmp_path) -> None:
    report_path = tmp_path / "repo" / "reports" / ACTIVITY_ID / "latest.json"
    external = tmp_path / "external"
    external.mkdir()
    external_history = (
        external
        / student_lab_attempts.assignment_storage_key(ASSIGNMENT_ID)
        / "latest.json"
    )
    external_history.parent.mkdir()
    external_history.write_text("external-data", encoding="utf-8")
    report_path.parent.mkdir(parents=True)
    assignments_link = report_path.parent / "assignments"
    try:
        assignments_link.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("Creazione symlink non disponibile su questa piattaforma.")

    with pytest.raises(ValueError, match="collegamento simbolico"):
        student_lab_attempts.persist_standard_report(
            report_path,
            ASSIGNMENT_ID,
            report(
                attempt_id="ignored",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at="2026-10-18T10:00:00+02:00",
            ),
            base_dir=tmp_path / "repo",
        )

    assert external_history.read_text(encoding="utf-8") == "external-data"


def test_load_attempt_history_rejects_symlinked_attempts_directory(tmp_path) -> None:
    report_path = tmp_path / "repo" / "reports" / ACTIVITY_ID / "latest.json"
    external = tmp_path / "external"
    external.mkdir()
    external_attempt = external / "attempt-external.json"
    external_attempt.write_text("not-json", encoding="utf-8")
    history_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID)
    history_dir.mkdir(parents=True)
    attempts_link = history_dir / "attempts"
    try:
        attempts_link.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("Creazione symlink non disponibile su questa piattaforma.")

    history = student_lab_attempts.load_attempt_history(
        report_path,
        ASSIGNMENT_ID,
        ACTIVITY_ID,
        base_dir=tmp_path / "repo",
    )

    assert history == {"attempts": [], "count": 0, "truncated": False}
    assert external_attempt.read_text(encoding="utf-8") == "not-json"


def test_load_attempts_caps_number_of_reports(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    for index in range(3):
        write_attempt(
            report_path,
            report(
                attempt_id=f"attempt-{index}",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at=f"2026-10-18T1{index}:00:00+02:00",
            ),
        )
    monkeypatch.setattr(student_lab_attempts, "MAX_ATTEMPTS_LOADED", 2)

    attempts = student_lab_attempts.load_attempts(report_path, ASSIGNMENT_ID, ACTIVITY_ID)

    assert [item["attempt_id"] for item in attempts] == ["attempt-2", "attempt-1"]


def test_load_attempts_caps_directory_scan(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    for index in range(4):
        write_attempt(
            report_path,
            report(
                attempt_id=f"attempt-{index}",
                passed=True,
                tests_passed=1,
                tests_total=1,
                submitted_at=f"2026-10-18T1{index}:00:00+02:00",
            ),
        )
    monkeypatch.setattr(student_lab_attempts, "MAX_ATTEMPT_FILES_SCANNED", 2)

    history = student_lab_attempts.load_attempt_history(report_path, ASSIGNMENT_ID, ACTIVITY_ID)

    assert history["count"] == 2
    assert history["truncated"] is True
    assert len(history["attempts"]) == 2


def test_load_attempts_counts_unrelated_entries_toward_scan_limit(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    attempts_dir = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID) / "attempts"
    attempts_dir.mkdir(parents=True)
    for index in range(4):
        (attempts_dir / f"noise-{index}.txt").write_text("noise", encoding="utf-8")
    monkeypatch.setattr(student_lab_attempts, "MAX_ATTEMPT_FILES_SCANNED", 2)

    history = student_lab_attempts.load_attempt_history(report_path, ASSIGNMENT_ID, ACTIVITY_ID)

    assert history == {"attempts": [], "count": 0, "truncated": True}


def test_assignment_latest_remains_available_when_history_scan_is_truncated(tmp_path, monkeypatch) -> None:
    report_path = tmp_path / "reports" / ACTIVITY_ID / "latest.json"
    older = report(
        attempt_id="attempt-2",
        passed=False,
        tests_passed=0,
        tests_total=1,
        submitted_at="2026-10-18T10:00:00+02:00",
    )
    latest = report(
        attempt_id="attempt-9",
        passed=True,
        tests_passed=1,
        tests_total=1,
        submitted_at="2026-10-18T12:00:00+02:00",
    )
    write_attempt(report_path, older)
    write_attempt(report_path, latest)
    history_latest = student_lab_attempts.assignment_history_dir(report_path, ASSIGNMENT_ID) / "latest.json"
    student_lab_attempts.write_json_atomic(history_latest, latest)
    monkeypatch.setattr(student_lab_attempts, "MAX_ATTEMPT_FILES_SCANNED", 1)

    history = student_lab_attempts.load_attempt_history(report_path, ASSIGNMENT_ID, ACTIVITY_ID)
    canonical = student_lab_attempts.load_assignment_latest(
        report_path,
        ASSIGNMENT_ID,
        ACTIVITY_ID,
        base_dir=tmp_path,
    )

    assert history["truncated"] is True
    assert canonical == latest


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
