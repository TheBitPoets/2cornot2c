from __future__ import annotations

import base64
import http.client
import json
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts import (
    assignment_records,
    course_board_server,
    student_help_auth,
    student_help_service,
    student_lab_demo_setup,
)
from scripts.student_help_provider import StudentHelpResponse


def test_server_bind_rejects_clear_text_network_exposure_by_default() -> None:
    assert course_board_server.is_loopback_bind_host("127.0.0.1") is True
    assert course_board_server.is_loopback_bind_host("::1") is True
    assert course_board_server.is_loopback_bind_host("localhost") is True
    assert course_board_server.is_loopback_bind_host("0.0.0.0") is False

    with pytest.raises(ValueError, match="--allow-insecure-network-http"):
        course_board_server.validate_server_bind("0.0.0.0")

    course_board_server.validate_server_bind("0.0.0.0", allow_insecure_network_http=True)


def test_teacher_dashboard_token_rejects_weak_configured_value(monkeypatch) -> None:
    monkeypatch.setenv("THEBITLAB_TEACHER_TOKEN", "troppo-corto")

    with pytest.raises(ValueError, match="almeno 32 caratteri"):
        course_board_server.teacher_dashboard_token()


def test_teacher_dashboard_token_uses_valid_configured_value(monkeypatch) -> None:
    configured = "teacher-dashboard-token-with-32-chars"
    monkeypatch.setenv("THEBITLAB_TEACHER_TOKEN", configured)

    assert course_board_server.teacher_dashboard_token() == configured


def test_teacher_dashboard_token_generates_robust_value(monkeypatch) -> None:
    monkeypatch.delenv("THEBITLAB_TEACHER_TOKEN", raising=False)

    generated = course_board_server.teacher_dashboard_token()

    assert len(generated) >= course_board_server.MIN_TEACHER_TOKEN_CHARS


def test_teacher_dashboard_token_console_line_hides_configured_value() -> None:
    configured = "teacher-dashboard-token-with-32-chars"

    line = course_board_server.teacher_dashboard_token_console_line(configured, configured=True)

    assert configured not in line
    assert "THEBITLAB_TEACHER_TOKEN" in line


def test_teacher_dashboard_token_console_line_shows_generated_value() -> None:
    generated = "generated-teacher-dashboard-token"

    line = course_board_server.teacher_dashboard_token_console_line(generated, configured=False)

    assert generated in line
    assert "temporaneo" in line


def test_data_root_process_lock_rejects_a_second_server(tmp_path) -> None:
    first_lock = course_board_server.DataRootProcessLock(tmp_path)
    second_lock = course_board_server.DataRootProcessLock(tmp_path)
    first_lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="Un altro server"):
            second_lock.acquire()
    finally:
        first_lock.release()

    second_lock.acquire()
    second_lock.release()


def test_bounded_http_server_limits_workers_and_sets_client_timeout(monkeypatch) -> None:
    class FakeRequest:
        timeout = None

        def settimeout(self, timeout) -> None:
            self.timeout = timeout

    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=1,
        max_workers_per_client=1,
    )
    request = FakeRequest()
    try:
        assert server._request_slots.acquire(blocking=False) is True
        assert server._request_slots.acquire(blocking=False) is False
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request_thread",
            lambda self, current_request, client_address: None,
        )

        server.process_request_thread(request, ("127.0.0.1", 12345))

        assert request.timeout == course_board_server.HTTP_CLIENT_TIMEOUT_SECONDS
        assert server._request_slots.acquire(blocking=False) is True
        server._request_slots.release()
    finally:
        server.server_close()


def test_bounded_http_server_rejects_overload_without_blocking(monkeypatch) -> None:
    class FakeRequest:
        def __init__(self) -> None:
            self.timeout = None
            self.response = b""

        def settimeout(self, timeout) -> None:
            self.timeout = timeout

        def sendall(self, content) -> None:
            self.response += content

    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=1,
        max_workers_per_client=1,
    )
    request = FakeRequest()
    closed = []
    try:
        assert server._request_slots.acquire(blocking=False) is True
        monkeypatch.setattr(server, "shutdown_request", lambda current_request: closed.append(current_request))
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request",
            lambda self, current_request, client_address: pytest.fail("La richiesta satura non va accodata."),
        )

        server.process_request(request, ("127.0.0.1", 12345))

        assert request.timeout == 1
        assert request.response.startswith(b"HTTP/1.1 503 Service Unavailable")
        assert b"Content-Length: 34\r\n" in request.response
        assert closed == [request]
    finally:
        server._request_slots.release()
        server.server_close()


def test_bounded_http_server_limits_and_releases_slots_per_client(monkeypatch) -> None:
    class FakeRequest:
        def __init__(self) -> None:
            self.response = b""

        def settimeout(self, timeout) -> None:
            pass

        def sendall(self, content) -> None:
            self.response += content

    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=4,
        max_workers_per_client=1,
    )
    first = FakeRequest()
    same_client = FakeRequest()
    other_client = FakeRequest()
    retry = FakeRequest()
    accepted = []
    try:
        monkeypatch.setattr(server, "shutdown_request", lambda request: None)
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request",
            lambda self, request, address: accepted.append((request, address)),
        )
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request_thread",
            lambda self, request, address: None,
        )

        server.process_request(first, ("192.0.2.10", 1001))
        server.process_request(same_client, ("192.0.2.10", 1002))
        server.process_request(other_client, ("192.0.2.11", 1003))

        assert [item[0] for item in accepted] == [first, other_client]
        assert same_client.response.startswith(b"HTTP/1.1 503 Service Unavailable")

        server.process_request_thread(first, ("192.0.2.10", 1001))
        server.process_request(retry, ("192.0.2.10", 1004))
        assert accepted[-1][0] is retry

        server.process_request_thread(retry, ("192.0.2.10", 1004))
        server.process_request_thread(other_client, ("192.0.2.11", 1003))
        assert server._client_workers == {}
    finally:
        server.server_close()


def patch_assignment_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])


def write_demo_activity(path, activity_id: str = "python-base-somma-001") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": activity_id,
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Somma due numeri.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )


def test_assignment_overview_lists_students_across_saved_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "python-base-somma-001.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "class_id": "3A-TPSI",
                "class_label": "3A TPSI",
                "github_team": "team-3a-tpsi",
                "kind": "compito-casa",
                "student_support_mode": "guidato",
                "assigned_at": "2026-10-12T09:00:00+02:00",
                "due_at": "2026-10-19T23:59:00+02:00",
                "students": [
                    {
                        "student": "rossi-mario",
                        "repo": "TheBitPoets/rossi-mario",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "submission": {
                            "submitted_at": "2026-10-18T18:22:10+02:00",
                            "commit": "abc1234",
                            "source_path": "assignments/python-base-somma-001/main.py",
                        },
                        "grading": {
                            "status": "graded_passed",
                            "tests_passed": 2,
                            "tests_total": 2,
                            "teacher_grade": 9,
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "status": "submitted_late",
                        "submitted": True,
                        "late": True,
                        "grading": {
                            "status": "graded_failed",
                            "tests_passed": 1,
                            "tests_total": 2,
                            "failed_tests": ["somma numeri negativi"],
                            "failed_test_details": [
                                {
                                    "name": "somma numeri negativi",
                                    "message": "Output atteso diverso",
                                    "expected_stdout": "0",
                                    "actual_stdout": "1",
                                }
                            ],
                            "score": 5,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = course_board_server.assignment_overview()

    assert len(rows) == 2
    assert rows[0]["report_name"] == "demo/python-base-somma-001.json"
    assert rows[0]["activity_id"] == "python-base-somma-001"
    assert rows[0]["class_id"] == "3A-TPSI"
    assert rows[0]["class_label"] == "3A TPSI"
    assert rows[0]["github_team"] == "team-3a-tpsi"
    assert rows[0]["kind"] == "compito-casa"
    assert rows[0]["student_support_mode"] == "guidato"
    assert rows[0]["student"] == "rossi-mario"
    assert rows[0]["tests_passed"] == 2
    assert rows[0]["teacher_grade"] == 9
    assert rows[1]["student"] == "bianchi-luca"
    assert rows[1]["late"] is True
    assert rows[1]["failed_tests"] == ["somma numeri negativi"]
    assert rows[1]["failed_test_details"][0]["message"] == "Output atteso diverso"
    assert rows[1]["score"] == 5


def test_list_assignment_reports_counts_late_only_for_submitted_students(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "class_id": "4A-INF",
                "class_label": "4A INF",
                "github_team": "team-4a-inf",
                "students": [
                    {"student": "rossi-mario", "status": "submitted_late", "submitted": True, "late": True},
                    {"student": "bianchi-luca", "status": "missing", "submitted": False, "late": True},
                    {"student": "verdi-anna", "status": "submitted_on_time", "submitted": True, "late": False},
                ],
            }
        ),
        encoding="utf-8",
    )

    reports = course_board_server.list_assignment_reports()

    assert reports[0]["class_id"] == "4A-INF"
    assert reports[0]["class_label"] == "4A INF"
    assert reports[0]["github_team"] == "team-4a-inf"
    assert reports[0]["students"] == 3
    assert reports[0]["submitted"] == 2
    assert reports[0]["not_submitted"] == 1
    assert reports[0]["late"] == 1


def test_list_assignment_records_marks_due_without_register(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {"student_id": "rossi-mario", "path": "studenti/rossi-mario"},
                {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
            ],
        ),
    )

    payload = course_board_server.list_assignment_records("2026-10-20T08:00:00+02:00")

    assert payload["assignments"][0]["id"] == assignment["id"]
    assert payload["assignment_statuses"][0]["assignment"]["id"] == assignment["id"]
    assert payload["assignment_statuses"][0]["due"] is True
    assert payload["assignment_statuses"][0]["has_register"] is False
    assert payload["due_without_register"][0]["assignment"]["id"] == assignment["id"]
    assert payload["due_without_register"][0]["needs_register"] is True


def test_delete_assignment_record_removes_saved_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        ),
    )

    payload = course_board_server.delete_assignment_record({
        "assignment_id": assignment["id"],
        "now": "2026-10-20T08:00:00+02:00",
    })

    assert payload["ok"] is True
    assert payload["deleted"]["id"] == assignment["id"]
    assert payload["assignments"] == []
    assert payload["due_without_register"] == []
    assert not (tmp_path / assignment["path"]).exists()


def test_help_operation_ids_keep_distinct_student_identities() -> None:
    operation_ids = course_board_server.unique_student_help_operation_ids(
        "assignment-001",
        {"mario.rossi", "mario-rossi"},
    )

    assert len(operation_ids) == 2
    with course_board_server.assignment_operation_lock(operation_ids[0], blocking=False):
        with course_board_server.assignment_operation_lock(operation_ids[1], blocking=False):
            pass


def test_assignment_record_aliases_share_the_same_operation_lock(tmp_path) -> None:
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    canonical = course_board_server.assignment_record_operation_id(storage, "assignment-demo")
    alias = course_board_server.assignment_record_operation_id(storage, "Assignment Demo")

    assert canonical == alias
    with course_board_server.assignment_operation_lock(canonical):
        with pytest.raises(course_board_server.StudentHelpBusyError):
            with course_board_server.assignment_operation_lock(alias, blocking=False):
                pass


def test_delete_assignment_record_resets_server_help_history_and_budget(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment_payload = assignment_records.build_assignment_record(
        assignment_id="assignment-riutilizzabile",
        activity_id="python-base-somma-001",
        activity_path="activities/python-base-somma-001.json",
        target_type="student",
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[{"student_id": "studente-stabile-001", "path": "studenti/cartella-repository"}],
    )
    assignment = storage.write_assignment(assignment_payload)
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "studente-stabile-001",
        assignment["id"],
    )
    student_help_service.record_help_request(
        activity_id="python-base-somma-001",
        support_policy={"mode": "studio-guidato", "ai": {"enabled": True, "max_requests": 1}},
        help_type="ai",
        prompt="Aiutami con la somma.",
        now="2026-10-20T08:10:00+02:00",
        log_path=log_path,
    )
    assert student_help_service.teacher_help_summary(log_path)["total"] == 1

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
    storage.write_assignment(assignment_payload)

    summary = student_help_service.teacher_help_summary(log_path)
    assert not log_path.parent.exists()
    assert summary["total"] == 0
    assert summary["ai_total"] == 0


def test_delete_assignment_record_is_idempotent_after_response_loss(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-delete-retry",
            activity_id="activity-demo",
            activity_path="activities/activity-demo.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )

    first = course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
    retry = course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert first["already_deleted"] is False
    assert retry["already_deleted"] is True
    assert retry["deleted"]["id"] == assignment["id"]
    assert retry["assignments"] == []


def test_recovery_restores_staged_logs_when_assignment_record_still_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-crash-prima-record",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": [{"prompt": "prima del crash"}]}\n', encoding="utf-8")

    trash_root, _ = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent],
    )
    assert not log_path.exists()

    course_board_server.recover_interrupted_assignment_deletions()

    assert log_path.is_file()
    assert "prima del crash" in log_path.read_text(encoding="utf-8")
    assert not trash_root.exists()


def test_recovery_syncs_restored_logs_before_purging_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-recovery-sync",
            activity_id="activity-demo",
            activity_path="activities/activity-demo.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, _ = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent],
    )
    events = []
    original_purge = course_board_server.purge_help_deletion_trash
    monkeypatch.setattr(
        course_board_server,
        "sync_file_tree",
        lambda root: events.append(("sync", root)),
    )

    def capture_purge(current_trash_root, **kwargs):
        events.append(("purge", current_trash_root))
        return original_purge(current_trash_root, **kwargs)

    monkeypatch.setattr(course_board_server, "purge_help_deletion_trash", capture_purge)

    course_board_server.recover_interrupted_assignment_deletions()

    assert events.index(("sync", log_path.parent)) < events.index(("purge", trash_root))
    assert log_path.is_file()


def test_recovery_purges_staged_logs_when_assignment_record_is_already_deleted(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-crash-dopo-record",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": [{"prompt": "da eliminare"}]}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent],
    )
    course_board_server.persist_help_log_rollback(
        trash_root,
        assignment,
        course_board_server.snapshot_staged_help_logs(staged_logs),
    )
    assert assignment_records.JsonAssignmentRecordStorage(tmp_path).read_json(
        course_board_server.help_deletion_manifest_path(trash_root)
    )["state"] == "prepared"
    storage.delete_assignment(assignment["id"])

    course_board_server.recover_interrupted_assignment_deletions()

    assert not log_path.exists()
    assert not trash_root.exists()


def test_help_log_staging_syncs_transaction_and_rename_directories(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "rossi-mario",
        "assignment-demo",
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    synced_directories = []
    monkeypatch.setattr(
        assignment_records,
        "sync_directory",
        lambda path: synced_directories.append(path),
    )

    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        "assignment-demo",
        [log_path.parent],
    )

    assert trash_root.parent in synced_directories
    assert log_path.parent.parent in synced_directories
    assert trash_root in synced_directories

    synced_directories.clear()
    course_board_server.restore_staged_help_logs(staged_logs)

    assert trash_root in synced_directories
    assert log_path.parent.parent in synced_directories
    assert log_path.is_file()


def test_sync_file_tree_flushes_regular_files_on_windows(tmp_path, monkeypatch) -> None:
    root = tmp_path / "rollback"
    first = root / "student-a" / "events.json"
    second = root / "student-b" / "events.json"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")
    flushed = []
    monkeypatch.setattr(course_board_server.os, "name", "nt")
    monkeypatch.setattr(course_board_server.os, "fsync", lambda descriptor: flushed.append(descriptor))

    course_board_server.sync_file_tree(root)

    assert len(flushed) == 2


def test_delete_assignment_uses_canonical_record_id_for_help_logs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="Assignment Demo 2026",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "rossi-mario",
        assignment["id"],
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")

    deleted = course_board_server.delete_assignment_record(
        {"assignment_id": "assignment-demo-2026"}
    )

    assert deleted["deleted"]["id"] == "Assignment Demo 2026"
    assert not storage.safe_assignment_path(assignment["id"]).exists()
    assert not log_path.parent.exists()


def test_delete_legacy_assignment_removes_logs_for_derived_aliases(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment_payload = assignment_records.build_assignment_record(
        assignment_id="assignment-legacy-riutilizzabile",
        activity_id="python-base-somma-001",
        activity_path="activities/python-base-somma-001.json",
        target_type="student",
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[{"target": "studenti/rossi-mario"}],
    )
    assignment = storage.write_assignment(assignment_payload)
    alias_paths = [student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])]
    for log_path in alias_paths:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text('{"events": [{"help_type": "ai", "allowed": true}]}\n', encoding="utf-8")

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
    storage.write_assignment(assignment_payload)

    assert all(not log_path.exists() for log_path in alias_paths)


def test_delete_legacy_assignment_normalizes_windows_path_aliases(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-legacy-windows",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"target": r"studenti\rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert not log_path.parent.exists()


def test_delete_modern_assignment_also_removes_historical_alias_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-con-alias-storico",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {
                    "student_id": "studente-stabile-001",
                    "repo_ref": "TheBitPoets/vecchia-cartella",
                    "path": "studenti/vecchia-cartella",
                }
            ],
        )
    )
    canonical_log = student_help_service.server_help_log_path(tmp_path, "studente-stabile-001", assignment["id"])
    historical_log = student_help_service.server_help_log_path(tmp_path, "vecchia-cartella", assignment["id"])
    for log_path in (canonical_log, historical_log):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text('{"events": []}\n', encoding="utf-8")

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert not canonical_log.exists()
    assert not historical_log.exists()


def test_delete_assignment_keeps_record_when_help_log_removal_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-log-bloccato",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    monkeypatch.setattr(Path, "replace", lambda self, target: (_ for _ in ()).throw(PermissionError()))

    with pytest.raises(PermissionError):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert log_path.is_file()


def test_delete_assignment_restores_all_logs_when_staging_fails_midway(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-due-log",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="group",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}, {"student_id": "bianchi-luca"}],
        )
    )
    log_paths = [
        student_help_service.server_help_log_path(tmp_path, student_id, assignment["id"])
        for student_id in ("rossi-mario", "bianchi-luca")
    ]
    for log_path in log_paths:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text('{"events": []}\n', encoding="utf-8")
    original_replace = Path.replace
    replace_calls = 0

    def fail_second_stage(source, target):
        nonlocal replace_calls
        if ".trash" not in source.parts:
            replace_calls += 1
            if replace_calls == 2:
                raise PermissionError("secondo log bloccato")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_second_stage)

    with pytest.raises(PermissionError, match="secondo log bloccato"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert all(log_path.is_file() for log_path in log_paths)


def test_delete_assignment_restores_logs_when_record_delete_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-record-bloccato",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    monkeypatch.setattr(
        assignment_records.JsonAssignmentRecordStorage,
        "delete_assignment",
        lambda self, assignment_id: (_ for _ in ()).throw(PermissionError("record bloccato")),
    )

    with pytest.raises(PermissionError, match="record bloccato"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert log_path.is_file()


def test_delete_assignment_restores_record_and_logs_when_quarantine_cleanup_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-quarantena-bloccata",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    original_rmtree = course_board_server.shutil.rmtree

    def fail_strict_quarantine_cleanup(path, ignore_errors=False):
        if ".trash" in Path(path).parts and not ignore_errors:
            raise PermissionError("quarantena bloccata")
        return original_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(course_board_server.shutil, "rmtree", fail_strict_quarantine_cleanup)

    with pytest.raises(PermissionError, match="quarantena bloccata"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert log_path.is_file()


def test_delete_assignment_restores_every_log_after_partial_quarantine_cleanup(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-quarantena-parziale",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="group",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}, {"student_id": "bianchi-luca"}],
        )
    )
    log_paths = [
        student_help_service.server_help_log_path(tmp_path, student_id, assignment["id"])
        for student_id in ("rossi-mario", "bianchi-luca")
    ]
    expected_contents = {}
    for index, log_path in enumerate(log_paths):
        content = json.dumps({"events": [{"prompt": f"richiesta {index}"}]}) + "\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(content, encoding="utf-8")
        expected_contents[log_path] = content
    original_rmtree = course_board_server.shutil.rmtree
    cleanup_attempts = 0

    def fail_after_removing_first_staged_log(path, ignore_errors=False):
        nonlocal cleanup_attempts
        candidate = Path(path)
        if (
            candidate.name.isdigit()
            and candidate.parent.parent.name == ".trash"
            and not ignore_errors
        ):
            cleanup_attempts += 1
            if cleanup_attempts == 2:
                raise PermissionError("pulizia parziale della quarantena")
        return original_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(course_board_server.shutil, "rmtree", fail_after_removing_first_staged_log)

    with pytest.raises(PermissionError, match="pulizia parziale"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert cleanup_attempts >= 2
    assert all(log_path.read_text(encoding="utf-8") == content for log_path, content in expected_contents.items())


def test_recovery_is_idempotent_after_crash_during_partial_rollback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-crash-rollback-parziale",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="group",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}, {"student_id": "bianchi-luca"}],
        )
    )
    log_paths = [
        student_help_service.server_help_log_path(tmp_path, student_id, assignment["id"])
        for student_id in ("rossi-mario", "bianchi-luca")
    ]
    expected_contents = {}
    for index, log_path in enumerate(log_paths):
        content = json.dumps({"events": [{"prompt": f"richiesta {index}"}]}) + "\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(content, encoding="utf-8")
        expected_contents[log_path] = content
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent for log_path in log_paths],
    )
    snapshots = course_board_server.snapshot_staged_help_logs(staged_logs)
    course_board_server.persist_help_log_rollback(trash_root, assignment, snapshots)
    storage.delete_assignment(assignment["id"])
    course_board_server.update_help_deletion_manifest(trash_root, state="rolling_back")
    course_board_server.shutil.rmtree(staged_logs[0][1])
    first_log = log_paths[0]
    first_log.parent.mkdir(parents=True)
    first_log.write_text("ripristino interrotto", encoding="utf-8")

    course_board_server.recover_interrupted_assignment_deletions()

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert not trash_root.exists()
    assert all(log_path.read_text(encoding="utf-8") == content for log_path, content in expected_contents.items())


def test_recovery_purges_committed_deletion_without_restoring_assignment(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-cancellazione-committed",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"], [log_path.parent]
    )
    snapshots = course_board_server.snapshot_staged_help_logs(staged_logs)
    course_board_server.persist_help_log_rollback(trash_root, assignment, snapshots)
    storage.delete_assignment(assignment["id"])
    for _, staged in staged_logs:
        course_board_server.shutil.rmtree(staged)
    course_board_server.update_help_deletion_manifest(trash_root, state="committed")

    course_board_server.recover_interrupted_assignment_deletions()

    with pytest.raises(FileNotFoundError):
        storage.read_assignment(assignment["id"])
    assert not log_path.exists()
    assert not trash_root.exists()


def test_recovery_removes_empty_quarantine_left_after_manifest_purge(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    trash_base = tmp_path / "teacher-help-events" / ".trash"
    trash_root = trash_base / "purge-interrotto"
    trash_root.mkdir(parents=True)
    synced = []
    monkeypatch.setattr(
        course_board_server.assignment_records,
        "sync_directory",
        lambda path: synced.append(path),
    )

    course_board_server.recover_interrupted_assignment_deletions()

    assert not trash_root.exists()
    assert synced == [trash_base]


def test_recovery_rejects_nonempty_quarantine_without_manifest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    trash_root = tmp_path / "teacher-help-events" / ".trash" / "journal-mancante"
    trash_root.mkdir(parents=True)
    (trash_root / "dati-residui.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Quarantena senza journal"):
        course_board_server.recover_interrupted_assignment_deletions()

    assert trash_root.exists()


def test_persistent_rollback_rejects_staged_path_outside_transaction(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-journal-path-corrotto",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"], [log_path.parent]
    )
    manifest_path = course_board_server.help_deletion_manifest_path(trash_root)
    manifest = storage.read_json(manifest_path)
    manifest["logs"][0]["staged"] = "../fuori-transazione"
    storage.write_json(manifest_path, manifest)

    with pytest.raises(RuntimeError, match="Path non valido"):
        course_board_server.persist_help_log_rollback(
            trash_root,
            assignment,
            course_board_server.snapshot_staged_help_logs(staged_logs),
        )

    assert not (trash_root.parent / "fuori-transazione").exists()


def test_persistent_rollback_syncs_tree_before_advancing_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-journal-durevole",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"], [log_path.parent]
    )
    events = []
    original_update = course_board_server.update_help_deletion_manifest
    monkeypatch.setattr(
        course_board_server,
        "sync_file_tree",
        lambda root: events.append(("sync", root)),
    )

    def capture_update(current_trash_root, **updates):
        events.append(("state", updates.get("state")))
        return original_update(current_trash_root, **updates)

    monkeypatch.setattr(course_board_server, "update_help_deletion_manifest", capture_update)

    course_board_server.persist_help_log_rollback(
        trash_root,
        assignment,
        course_board_server.snapshot_staged_help_logs(staged_logs),
    )

    assert events == [
        ("sync", trash_root / "rollback"),
        ("state", "prepared"),
    ]


def test_delete_assignment_does_not_restore_record_when_log_snapshot_restore_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-rollback-log-bloccato",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    original_rmtree = course_board_server.shutil.rmtree

    def fail_strict_cleanup(path, ignore_errors=False):
        if ".trash" in Path(path).parts and not ignore_errors:
            raise PermissionError("quarantena bloccata")
        return original_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(course_board_server.shutil, "rmtree", fail_strict_cleanup)
    monkeypatch.setattr(
        course_board_server,
        "restore_help_log_snapshots",
        lambda snapshots: (_ for _ in ()).throw(OSError("ripristino log bloccato")),
    )

    with pytest.raises(OSError, match="ripristino log bloccato"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    with pytest.raises(FileNotFoundError):
        storage.read_assignment(assignment["id"])


def test_delete_assignment_waits_for_inflight_help_request(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-in-corso",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()

    class BlockingProvider:
        def respond(self, request):
            provider_started.set()
            assert provider_release.wait(timeout=5)
            return StudentHelpResponse(
                status="ready",
                provider="blocking-test",
                provider_label="Provider bloccante test",
                message="Controlla il primo passaggio.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: BlockingProvider())
    request_errors = []
    delete_errors = []

    def request_help():
        try:
            course_board_server.record_student_help(
                {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Aiutami."},
                student_id="rossi-mario",
            )
        except Exception as error:  # noqa: BLE001
            request_errors.append(error)

    def delete_assignment():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    request_thread = threading.Thread(target=request_help)
    delete_thread = threading.Thread(target=delete_assignment)
    request_thread.start()
    assert provider_started.wait(timeout=5)
    delete_thread.start()
    assert delete_thread.is_alive()
    provider_release.set()
    request_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert request_errors == []
    assert delete_errors == []
    assert not storage.safe_assignment_path(assignment["id"]).exists()
    assert not student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"]).exists()


def test_concurrent_help_request_is_rejected_without_waiting(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    assignment = assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-concorrente",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()
    provider_calls = 0

    class BlockingProvider:
        def respond(self, request):
            nonlocal provider_calls
            provider_calls += 1
            provider_started.set()
            assert provider_release.wait(timeout=5)
            return StudentHelpResponse(
                status="ready",
                provider="blocking-test",
                provider_label="Provider bloccante test",
                message="Controlla il primo passaggio.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: BlockingProvider())
    first_errors = []

    def first_request():
        try:
            course_board_server.record_student_help(
                {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Prima richiesta."},
                student_id="rossi-mario",
            )
        except Exception as error:  # noqa: BLE001
            first_errors.append(error)

    first_thread = threading.Thread(target=first_request)
    first_thread.start()
    assert provider_started.wait(timeout=5)

    with pytest.raises(course_board_server.StudentHelpBusyError, match="gia in elaborazione"):
        course_board_server.record_student_help(
            {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Seconda richiesta."},
            student_id="rossi-mario",
        )

    assert first_thread.is_alive()
    assert provider_calls == 1
    provider_release.set()
    first_thread.join(timeout=5)
    assert first_errors == []


def test_concurrent_idempotent_help_retry_reports_pending(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    assignment = assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-retry-pending",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()

    class BlockingProvider:
        def respond(self, request):
            provider_started.set()
            assert provider_release.wait(timeout=5)
            return StudentHelpResponse(
                status="ready",
                provider="blocking-test",
                provider_label="Provider bloccante test",
                message="Controlla il primo passaggio.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: BlockingProvider())
    payload = {
        "assignment_id": assignment["id"],
        "help_type": "debug",
        "prompt": "Prima richiesta.",
        "request_id": "request-retry-pending-0001",
    }
    first_errors = []

    def first_request():
        try:
            course_board_server.record_student_help(payload, student_id="rossi-mario")
        except Exception as error:  # noqa: BLE001
            first_errors.append(error)

    first_thread = threading.Thread(target=first_request)
    first_thread.start()
    assert provider_started.wait(timeout=5)

    with pytest.raises(student_help_service.StudentHelpPendingError, match="ancora in elaborazione"):
        course_board_server.record_student_help(payload, student_id="rossi-mario")

    provider_release.set()
    first_thread.join(timeout=5)
    assert first_errors == []


def test_classmates_can_request_help_on_the_same_assignment_concurrently(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    for student_id in ("rossi-mario", "bianchi-luca"):
        (tmp_path / "studenti" / student_id).mkdir(parents=True)
    assignment = assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-classe",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {"student_id": "rossi-mario", "path": "studenti/rossi-mario"},
                {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
            ],
        )
    )
    first_started = threading.Event()
    release_first = threading.Event()

    class PerStudentProvider:
        def respond(self, request):
            if request.prompt == "Aiuto Rossi.":
                first_started.set()
                assert release_first.wait(timeout=5)
            student_label = "rossi-mario" if request.prompt == "Aiuto Rossi." else "bianchi-luca"
            return StudentHelpResponse(
                status="ready",
                provider="parallel-test",
                provider_label="Provider parallelo test",
                message=f"Risposta per {student_label}.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: PerStudentProvider())
    first_errors = []

    def first_request():
        try:
            course_board_server.record_student_help(
                {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Aiuto Rossi."},
                student_id="rossi-mario",
            )
        except Exception as error:  # noqa: BLE001
            first_errors.append(error)

    first_thread = threading.Thread(target=first_request)
    first_thread.start()
    assert first_started.wait(timeout=5)

    second = course_board_server.record_student_help(
        {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Aiuto Bianchi."},
        student_id="bianchi-luca",
    )

    assert second["event"]["response"]["message"] == "Risposta per bianchi-luca."
    assert first_thread.is_alive()
    release_first.set()
    first_thread.join(timeout=5)
    assert first_errors == []


def test_save_and_delete_assignment_are_serialized(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    save_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "student",
        "targets_text": "studenti/rossi-mario",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "overwrite": True,
    }
    initial = course_board_server.save_assignment_record(save_payload)["assignment"]
    original_write = assignment_records.JsonAssignmentRecordStorage.write_assignment
    save_started = threading.Event()
    release_save = threading.Event()
    save_errors = []
    delete_errors = []

    def blocking_write(storage, assignment, overwrite=False):
        save_started.set()
        assert release_save.wait(timeout=5)
        return original_write(storage, assignment, overwrite)

    monkeypatch.setattr(assignment_records.JsonAssignmentRecordStorage, "write_assignment", blocking_write)

    def save_worker():
        try:
            course_board_server.save_assignment_record(save_payload)
        except Exception as error:  # noqa: BLE001
            save_errors.append(error)

    def delete_worker():
        try:
            course_board_server.delete_assignment_record({"assignment_id": initial["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    save_thread = threading.Thread(target=save_worker)
    delete_thread = threading.Thread(target=delete_worker)
    save_thread.start()
    assert save_started.wait(timeout=5)
    delete_thread.start()
    delete_thread.join(timeout=0.1)
    assert delete_thread.is_alive()
    release_save.set()
    save_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert save_errors == []
    assert delete_errors == []
    with pytest.raises(FileNotFoundError):
        assignment_records.JsonAssignmentRecordStorage(tmp_path).read_assignment(initial["id"])


def test_save_assignment_rejects_overwrite_with_different_students(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    for student_id in ("rossi-mario", "bianchi-luca", "verdi-anna"):
        (tmp_path / "studenti" / student_id).mkdir(parents=True)
    base_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "class_id": "3A-TPSI",
        "targets_text": "studenti/rossi-mario\nstudenti/bianchi-luca",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
    }
    saved = course_board_server.save_assignment_record(base_payload)["assignment"]

    with pytest.raises(ValueError, match="destinatari.*non sono modificabili"):
        course_board_server.save_assignment_record(
            {
                **base_payload,
                "targets_text": "studenti/rossi-mario\nstudenti/verdi-anna",
                "overwrite": True,
            }
        )

    persisted = assignment_records.JsonAssignmentRecordStorage(tmp_path).read_assignment(saved["id"])
    assert course_board_server.assignment_target_student_ids(persisted) == {
        "rossi-mario",
        "bianchi-luca",
    }


def test_save_assignment_rejects_student_id_bound_to_different_repository(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    (tmp_path / "classe-a" / "mario").mkdir(parents=True)
    (tmp_path / "classe-b" / "mario").mkdir(parents=True)
    base_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "class_id": "classe-a",
        "targets_text": "classe-a/mario",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
    }
    course_board_server.save_assignment_record(base_payload)

    with pytest.raises(ValueError, match="gia associato a un altro repository: mario"):
        course_board_server.save_assignment_record(
            {
                **base_payload,
                "class_id": "classe-b",
                "targets_text": "classe-b/mario",
            }
        )


def test_concurrent_saves_cannot_bind_one_student_to_two_repositories(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    (tmp_path / "classe-a" / "mario").mkdir(parents=True)
    (tmp_path / "classe-b" / "mario").mkdir(parents=True)
    first_validation_started = threading.Event()
    release_first_validation = threading.Event()
    original_validate = course_board_server.validate_global_assignment_target_bindings
    validation_calls = 0

    def blocking_validate(storage, assignment):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 1:
            first_validation_started.set()
            assert release_first_validation.wait(timeout=5)
        return original_validate(storage, assignment)

    monkeypatch.setattr(course_board_server, "validate_global_assignment_target_bindings", blocking_validate)
    base_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
    }
    saved = []
    errors = []

    def save_worker(class_id):
        try:
            saved.append(
                course_board_server.save_assignment_record(
                    {
                        **base_payload,
                        "class_id": class_id,
                        "targets_text": f"{class_id}/mario",
                    }
                )["assignment"]
            )
        except Exception as error:  # noqa: BLE001
            errors.append(error)

    first_thread = threading.Thread(target=save_worker, args=("classe-a",))
    second_thread = threading.Thread(target=save_worker, args=("classe-b",))
    first_thread.start()
    assert first_validation_started.wait(timeout=5)
    second_thread.start()
    second_thread.join(timeout=0.1)
    assert second_thread.is_alive()
    release_first_validation.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert len(saved) == 1
    assert len(errors) == 1
    assert "gia associato a un altro repository: mario" in str(errors[0])
    assert len(assignment_records.JsonAssignmentRecordStorage(tmp_path).list_assignments()) == 1


def test_delete_rollback_blocks_an_incompatible_concurrent_binding(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    (tmp_path / "classe-a" / "mario").mkdir(parents=True)
    (tmp_path / "classe-b" / "mario").mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-binding-rollback",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "mario", "path": "classe-a/mario"}],
        )
    )
    commit_started = threading.Event()
    release_commit = threading.Event()
    original_update = course_board_server.update_help_deletion_manifest

    def fail_committed_update(trash_root, **updates):
        if updates.get("state") == "committed":
            commit_started.set()
            assert release_commit.wait(timeout=5)
            raise OSError("journal non aggiornabile")
        return original_update(trash_root, **updates)

    monkeypatch.setattr(course_board_server, "update_help_deletion_manifest", fail_committed_update)
    delete_errors = []
    save_errors = []

    def delete_worker():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    def save_worker():
        try:
            course_board_server.save_assignment_record(
                {
                    "activity_path": "activities/python-base-somma-001.json",
                    "target_type": "student",
                    "class_id": "classe-b",
                    "targets_text": "classe-b/mario",
                    "assigned_at": "2026-10-13T09:00:00+02:00",
                    "due_at": "2026-10-20T23:59:00+02:00",
                }
            )
        except Exception as error:  # noqa: BLE001
            save_errors.append(error)

    delete_thread = threading.Thread(target=delete_worker)
    save_thread = threading.Thread(target=save_worker)
    delete_thread.start()
    assert commit_started.wait(timeout=5)
    save_thread.start()
    save_thread.join(timeout=0.1)
    assert save_thread.is_alive()
    release_commit.set()
    delete_thread.join(timeout=5)
    save_thread.join(timeout=5)

    assert len(delete_errors) == 1
    assert len(save_errors) == 1
    assert "gia associato a un altro repository: mario" in str(save_errors[0])
    persisted = storage.list_assignments()
    assert [item["id"] for item in persisted] == [assignment["id"]]
    assert course_board_server.assignment_target_bindings(persisted[0])["mario"] == os.path.normcase(
        str((tmp_path / "classe-a" / "mario").resolve(strict=False))
    )


def test_student_payload_does_not_wait_for_assignment_provider_lock(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-lettura-in-corso",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()

    def hold_assignment_lock():
        with course_board_server.assignment_operation_lock(assignment["id"]):
            provider_started.set()
            assert provider_release.wait(timeout=5)

    provider_thread = threading.Thread(target=hold_assignment_lock)
    provider_thread.start()
    assert provider_started.wait(timeout=5)

    payload = course_board_server.locked_student_lab_payload(student_id="rossi-mario")

    provider_release.set()
    provider_thread.join(timeout=5)
    assert payload["assignments"][0]["assignment_id"] == assignment["id"]


def test_delete_assignment_waits_for_help_log_read(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-log-in-lettura",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    read_started = threading.Event()
    read_release = threading.Event()
    original_read_help_log = student_help_service.read_help_log

    def blocking_read_help_log(path):
        if path == log_path:
            read_started.set()
            assert read_release.wait(timeout=5)
        return original_read_help_log(path)

    monkeypatch.setattr(student_help_service, "read_help_log", blocking_read_help_log)
    delete_errors = []
    read_thread = threading.Thread(target=lambda: student_help_service.help_summary(log_path))

    def delete_assignment():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    delete_thread = threading.Thread(target=delete_assignment)
    read_thread.start()
    assert read_started.wait(timeout=5)
    delete_thread.start()
    assert delete_thread.is_alive()
    read_release.set()
    read_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert delete_errors == []
    assert not storage.safe_assignment_path(assignment["id"]).exists()
    assert not log_path.parent.exists()


def test_assignment_operation_locks_are_released_after_use(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    course_board_server._ASSIGNMENT_OPERATION_LOCKS.clear()

    for index in range(50):
        with course_board_server.assignment_operation_lock(f"assignment-inesistente-{index}"):
            assert course_board_server._ASSIGNMENT_OPERATION_LOCKS

    assert course_board_server._ASSIGNMENT_OPERATION_LOCKS == {}


def test_delete_activity_record_removes_unlinked_draft(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)

    payload = course_board_server.delete_activity_record({
        "activity_path": "activities/drafts/python-base-somma-001.json",
    })

    assert payload["ok"] is True
    assert payload["deleted"]["id"] == "python-base-somma-001"
    assert payload["dependencies"] == {"assignments": [], "reports": []}
    assert payload["activities"] == []
    assert not activity_path.exists()


def test_delete_activity_record_blocks_when_assignment_exists(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/drafts/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        ),
    )

    with pytest.raises(ValueError, match="assegnazioni"):
        course_board_server.delete_activity_record({
            "activity_path": "activities/drafts/python-base-somma-001.json",
        })

    assert activity_path.exists()


def test_delete_activity_record_blocks_when_register_exists(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    report_path = tmp_path / "teacher-reports" / "demo" / "python-base-somma-001.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "students": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="registri"):
        course_board_server.delete_activity_record({
            "activity_path": "activities/drafts/python-base-somma-001.json",
        })

    assert activity_path.exists()


def test_delete_activity_record_rejects_non_draft_activity(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)

    with pytest.raises(ValueError, match="activities/drafts"):
        course_board_server.delete_activity_record({
            "activity_path": "activities/python-base-somma-001.json",
        })

    assert activity_path.exists()


def test_generate_assignment_report_preserves_assignment_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    activity_path = tmp_path / "activity.json"
    activity_path.write_text(
        json.dumps({
            "schema_version": "1.0",
            "id": "python-base-somma-001",
            "titolo": "Somma in Python",
            "linguaggio": "python",
            "tipo": "compito-casa",
            "difficolta": "B",
            "argomenti": ["variabili"],
            "consegna": "Somma due numeri.",
            "correzione": {
                "compila": True,
                "test": True,
                "sandbox": True,
                "ai_feedback": False,
            },
            "metriche": {
                "tempo_stimato_minuti": 20,
                "traccia_tempo_dichiarato": True,
                "traccia_sessioni_thebitlab": True,
                "traccia_eventi_didattici": True,
                "traccia_errori_compilazione": True,
            },
            "student_support_mode": "senza-aiuto",
        }),
        encoding="utf-8",
    )
    student_repo = tmp_path / "studenti" / "rossi-mario"
    (student_repo / "assignments" / "python-base-somma-001").mkdir(parents=True)
    (student_repo / "assignments" / "python-base-somma-001" / "main.py").write_text("print(3)\n", encoding="utf-8")
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-python-base-somma-001-3a",
            activity_id="python-base-somma-001",
            activity_path=str(activity_path),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": str(student_repo)}],
        )
    )

    result = course_board_server.generate_assignment_report({
        "activity_path": str(activity_path),
        "output_name": "demo/report.json",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "github_team": "team-3a-tpsi",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "now": "2026-10-20T08:00:00+02:00",
        "targets_text": str(student_repo),
        "assignment_id": "assignment-python-base-somma-001-3a",
    })

    assert result["report"]["assignment_id"] == "assignment-python-base-somma-001-3a"
    saved_payload = json.loads((tmp_path / "teacher-reports" / "demo" / "report.json").read_text(encoding="utf-8"))
    assert saved_payload["assignment_id"] == "assignment-python-base-somma-001-3a"


def test_read_assignment_report_refreshes_authoritative_help_without_rewriting_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    storage = course_board_server.assignment_storage()
    saved_report = {
        "schema_version": "1.0",
        "assignment_id": "assignment-help-refresh",
        "activity_id": "activity-demo",
        "title": "Activity demo",
        "students": [
            {
                "student": "cartella-repository",
                "student_id": "studente-stabile-001",
                "help": {
                    "total": 0,
                    "events": [],
                    "legacy_unverified": True,
                    "legacy": {"total": 1, "events": [{"prompt": "Evento legacy"}]},
                },
            }
        ],
    }
    storage.write_assignment_report("demo/help-refresh.json", saved_report)
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "studente-stabile-001",
        "assignment-help-refresh",
    )
    student_help_service.write_help_events(
        log_path,
        [
            {
                "schema_version": student_help_service.HELP_EVENT_SCHEMA_VERSION,
                "request_id": "request-help-refresh-0001",
                "requested_at": "2026-10-20T08:00:00+02:00",
                "activity_id": "activity-demo",
                "help_type": "teoria",
                "label": "Richiamo teorico",
                "allowed": True,
                "reason": "Consentita.",
                "prompt": "Quale concetto ripasso?",
            }
        ],
    )

    refreshed = course_board_server.read_assignment_report("demo/help-refresh.json")
    persisted = storage.read_assignment_report("demo/help-refresh.json")

    assert refreshed["students"][0]["help"]["total"] == 1
    assert refreshed["students"][0]["help"]["events"][0]["prompt"] == "Quale concetto ripasso?"
    assert refreshed["students"][0]["help"]["legacy"]["events"][0]["prompt"] == "Evento legacy"
    assert persisted["students"][0]["help"]["total"] == 0


def test_generate_assignment_report_blocks_concurrent_assignment_deletion(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    assignment_id = "assignment-report-in-corso"
    activity_path = tmp_path / "activity.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id=assignment_id,
            activity_id="python-base-somma-001",
            activity_path=str(activity_path),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": str(student_repo)}],
        )
    )
    tracking_started = threading.Event()
    tracking_release = threading.Event()
    report_errors = []
    delete_errors = []

    def blocking_tracking(**kwargs):
        tracking_started.set()
        assert tracking_release.wait(timeout=5)
        return {"schema_version": "1.0", "assignment_id": assignment_id, "students": []}

    monkeypatch.setattr(course_board_server.track_assignments, "track_assignments", blocking_tracking)
    monkeypatch.setattr(course_board_server.track_assignments, "write_tracking_index", lambda index, path: None)
    monkeypatch.setattr(course_board_server, "list_assignment_reports", lambda: [])

    def generate_report():
        try:
            course_board_server.generate_assignment_report(
                {
                    "activity_path": str(activity_path),
                    "output_name": "demo/report.json",
                    "targets_text": str(student_repo),
                    "assignment_id": assignment_id,
                }
            )
        except Exception as error:  # noqa: BLE001
            report_errors.append(error)

    def delete_assignment():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment_id})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    report_thread = threading.Thread(target=generate_report)
    delete_thread = threading.Thread(target=delete_assignment)
    report_thread.start()
    assert tracking_started.wait(timeout=5)
    delete_thread.start()
    assert delete_thread.is_alive()
    tracking_release.set()
    report_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert report_errors == []
    assert delete_errors == []
    assert not storage.safe_assignment_path(assignment_id).exists()


def test_generate_assignment_report_uses_canonical_record_lock_for_alias(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activity.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-report-alias",
            activity_id="python-base-somma-001",
            activity_path=str(activity_path),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": str(student_repo)}],
        )
    )

    tracking_started = threading.Event()
    report_errors = []

    def fake_tracking(**kwargs):
        tracking_started.set()
        return {"schema_version": "1.0", "assignment_id": kwargs["assignment_id"], "students": []}

    monkeypatch.setattr(course_board_server.track_assignments, "track_assignments", fake_tracking)
    monkeypatch.setattr(course_board_server.track_assignments, "write_tracking_index", lambda index, path: None)
    monkeypatch.setattr(course_board_server, "list_assignment_reports", lambda: [])

    def generate_report():
        try:
            course_board_server.generate_assignment_report(
                {
                    "activity_path": str(activity_path),
                    "output_name": "demo/report.json",
                    "targets_text": str(student_repo),
                    "assignment_id": "Assignment Report Alias",
                }
            )
        except Exception as error:  # noqa: BLE001
            report_errors.append(error)

    with course_board_server.assignment_operation_lock(
        course_board_server.assignment_record_operation_id(storage, assignment["id"])
    ):
        report_thread = threading.Thread(target=generate_report)
        report_thread.start()
        assert not tracking_started.wait(timeout=0.1)

    report_thread.join(timeout=5)
    assert report_errors == []
    assert tracking_started.is_set()


def test_preview_activity_assignment_returns_plan_without_writing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "assets": [{"type": "starter", "path": "starter/main.py", "target_path": "main.py"}],
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.preview_activity_assignment(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
        }
    )

    assert response["ok"] is True
    assert response["plan"]["activity_id"] == "python-base-somma-001"
    assert response["plan"]["student_assets"][0]["target_path"] == "main.py"
    assert response["plan"]["targets"][0]["target"] == str(target.resolve())
    assert not (target / "assignments").exists()


def test_preview_activity_ai_package_returns_context_files_and_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "tests").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    (activities_dir / "tests" / "hidden.py").write_text("assert True\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili", "operatori"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "contesto": {"percorso": "terzo-anno", "uda": "uda-input"},
                "assets": [
                    {"type": "starter", "path": "starter/main.py", "target_path": "main.py", "visibility": "student"},
                    {"type": "hidden_test", "path": "tests/hidden.py", "visibility": "teacher"},
                ],
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.preview_activity_ai_package(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Aggiungi test sui negativi",
            "provider": "codex",
            "student_budget": 5,
            "integrity_mode": "controlled",
        }
    )

    package = response["package"]
    assert response["ok"] is True
    assert package["schema_version"] == "activity_ai_package.v1"
    assert package["provider"] == "codex"
    assert package["prompt"] == "Aggiungi test sui negativi"
    assert package["activity"]["id"] == "python-base-somma-001"
    assert package["course_context"]["uda"] == "uda-input"
    target_entry = package["assignment"]["targets"][0]
    assert target_entry == {
        "target_id": "target-001",
        "display_name": "rossi-mario",
        "exists": False,
    }
    assert "target" not in target_entry
    assert "assignment_dir" not in target_entry
    assert str(tmp_path) not in json.dumps(package["assignment"]["targets"])
    assert package["files"][0]["path"] == "starter/main.py"
    assert package["files"][0]["included"] is True
    assert "starter" in package["files"][0]["content"]
    assert package["files"][1]["visibility"] == "teacher"
    assert package["policy"]["student_budget"] == 5
    assert package["policy"]["integrity_mode"] == "controlled"
    assert package["policy"]["no_provider_call"] is True
    assert not (target / "assignments").exists()


def test_preview_activity_ai_package_tolerates_empty_draft_language(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "activity-senza-linguaggio",
                "titolo": "Bozza senza linguaggio",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "",
                "consegna": "Completa la bozza.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )

    response = course_board_server.preview_activity_ai_package(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Genera starter file",
            "provider": "codex",
        }
    )

    assert response["ok"] is True
    assert response["package"]["assignment"]["language"] == "c"


def test_preview_activity_ai_codex_draft_uses_local_adapter(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setenv("CODEX_COMMAND", "codex-test")
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    captured = {}

    def fake_run_codex_activity_draft(package, *, cwd, codex_command="codex"):
        captured["package"] = package
        captured["cwd"] = cwd
        captured["codex_command"] = codex_command
        return {
            "adapter": "codex_exec",
            "draft": {
                "summary": "Bozza pronta",
                "teacher_notes": "Controllare i test.",
                "activity_patch": {"titolo": "Somma con negativi"},
                "files": [{"path": "main.py", "role": "starter", "content": "print(0)\n"}],
                "questions": [],
                "warnings": [],
            },
        }

    monkeypatch.setattr(course_board_server.codex_activity_adapter, "run_codex_activity_draft", fake_run_codex_activity_draft)

    response = course_board_server.preview_activity_ai_codex_draft(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Aggiungi test sui negativi",
            "provider": "codex",
            "current_draft": {
                "summary": "Prima bozza",
                "activity_patch": {"titolo": "Somma guidata"},
                "files": [],
            },
        }
    )

    assert response["ok"] is True
    assert response["adapter"] == "codex_exec"
    assert response["draft"]["activity_patch"]["titolo"] == "Somma con negativi"
    assert "raw" not in response
    assert captured["package"]["current_draft"]["summary"] == "Prima bozza"
    assert captured["package"]["prompt"] == "Aggiungi test sui negativi"
    assert captured["cwd"] == tmp_path
    assert captured["codex_command"] == "codex-test"


def test_save_assignment_record_persists_dashboard_assignment(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "students" / "rossi-mario").mkdir(parents=True)
    (tmp_path / "students" / "bianchi-luca").mkdir(parents=True)

    response = course_board_server.save_assignment_record({
        "activity_path": "activities/activity.json",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "now": "2026-10-20T08:00:00+02:00",
        "targets_text": "students/rossi-mario\nstudents/bianchi-luca",
    })

    assert response["ok"] is True
    assert response["assignment"]["activity_id"] == "python-base-somma-001"
    assert response["assignment"]["target_type"] == "class"
    assert response["assignment"]["targets"][0]["path"] == "students/rossi-mario"
    assert response["due_without_register"][0]["assignment"]["id"] == response["assignment"]["id"]
    saved_path = tmp_path / response["assignment"]["path"]
    assert saved_path.is_file()


def test_distribute_activity_assignment_writes_scaffolds(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)

    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "assets": [{"type": "starter", "path": "starter/main.py", "target_path": "main.py"}],
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.distribute_activity_assignment({
        "activity_path": "activities/activity.json",
        "targets_text": "students/rossi-mario",
    })

    assignment_dir = target / "assignments" / "python-base-somma-001"
    assert response["ok"] is True
    assert response["results"][0]["assignment_dir"] == str(assignment_dir.resolve())
    assert response["plan"]["targets"][0]["exists"] is True
    assert (assignment_dir / "activity.json").is_file()
    assert (assignment_dir / "main.py").read_text(encoding="utf-8") == "print('starter')\n"


def test_review_assignment_ai_feedback_persists_teacher_decision(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    report_path = report_dir / "activity.json"
    report_path.write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "draft",
                            "summary": "Bozza",
                            "approved_by_teacher": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = course_board_server.review_assignment_ai_feedback("demo/activity.json", "rossi-mario", "approve")
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["students"][0]["ai_feedback"]["status"] == "approved"
    assert report["students"][0]["ai_feedback"]["approved_by_teacher"] is True
    assert saved["students"][0]["ai_feedback"]["status"] == "approved"
    assert saved["students"][0]["ai_feedback"]["approved_by_teacher"] is True


def test_review_assignment_ai_feedback_reopens_reviewed_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = course_board_server.review_assignment_ai_feedback("activity.json", "rossi-mario", "reopen")

    assert report["students"][0]["ai_feedback"]["status"] == "draft"
    assert report["students"][0]["ai_feedback"]["approved_by_teacher"] is False


def test_review_assignment_ai_feedback_rejects_approve_on_non_draft_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        course_board_server.review_assignment_ai_feedback("activity.json", "rossi-mario", "approve")
    except ValueError as error:
        assert "non e una bozza" in str(error)
    else:
        raise AssertionError("La review deve rifiutare approve su feedback AI non in bozza")


def test_student_dashboard_endpoint_filters_to_requested_student(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "approved",
                            "approved_by_teacher": True,
                            "student_feedback": "Feedback visibile.",
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "student_id": "bianchi-luca",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    dashboard = course_board_server.student_dashboard("rossi-mario")

    assert dashboard["student_id"] == "rossi-mario"
    assert len(dashboard["assignments"]) == 1
    assert dashboard["assignments"][0]["approved_feedback"]["student_feedback"] == "Feedback visibile."


def test_student_dashboard_endpoint_includes_student_lab_results(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    write_demo_activity(tmp_path / "activities" / "python-base-somma-001.json")
    assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments").write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {
                    "student_id": "rossi-mario",
                    "path": "examples/assignment_tracking/student_repos/rossi-mario",
                }
            ],
        ),
    )
    repo = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario"
    workspace = repo / "assignments" / "python-base-somma-001"
    report_path = repo / "reports" / "python-base-somma-001" / "latest.json"
    workspace.mkdir(parents=True)
    report_path.parent.mkdir(parents=True)
    (workspace / "main.py").write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "student_lab_run.v1",
                "activity_id": "python-base-somma-001",
                "student_id": "rossi-mario",
                "status": "passed",
                "passed": True,
                "source": "assignments/python-base-somma-001/main.py",
                "submitted_at": "2026-10-18T18:00:00+02:00",
                "summary": {"passed": 2, "total": 2},
                "tests": [
                    {"name": "somma positiva", "status": "passed", "passed": True},
                    {"name": "somma negativa", "status": "passed", "passed": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    dashboard = course_board_server.student_dashboard("rossi-mario")

    assert dashboard["lab"]["schema_version"] == "student_lab.v1"
    assert len(dashboard["lab"]["assignments"]) == 1
    lab_assignment = dashboard["lab"]["assignments"][0]
    assert lab_assignment["workspace"]["exists"] is True
    assert lab_assignment["report"]["exists"] is True
    assert lab_assignment["grading"]["status"] == "graded_passed"
    assert lab_assignment["grading"]["tests_passed"] == 2


def test_record_student_help_delegates_only_client_identifiers_to_service(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    provider = object()
    captured = {}
    monkeypatch.setattr(course_board_server, "student_help_provider", lambda: provider)

    def fake_record(**kwargs):
        captured.update(kwargs)
        return {"allowed": True, "label": "Aiuto AI"}

    monkeypatch.setattr(course_board_server.student_lab_service, "record_student_help_request", fake_record)

    response = course_board_server.record_student_help(
        {
            "student_id": "rossi-mario",
            "assignment_id": "assignment-001",
            "help_type": "ai",
            "prompt": "Dammi una domanda guida.",
            "request_id": "request-server-0001",
            "support_policy": {"ai_allowed": True},
            "context": {"secret": "client-controlled"},
        },
        student_id="rossi-mario",
    )

    assert response == {"ok": True, "event": {"allowed": True, "label": "Aiuto AI"}}
    local_provider = captured.pop("provider")
    provider_factory = captured.pop("provider_factory")
    assert isinstance(local_provider, course_board_server.DeterministicStudentHelpProvider)
    assert provider_factory() is provider
    assert captured == {
        "root": tmp_path,
        "assignments_dir": tmp_path / "teacher-assignments",
        "student_id": "rossi-mario",
        "assignment_id": "assignment-001",
        "help_type": "ai",
        "prompt": "Dammi una domanda guida.",
        "request_id": "request-server-0001",
    }


def test_student_help_http_endpoint_records_request_on_server_root(tmp_path, monkeypatch) -> None:
    original_root = course_board_server.ROOT
    student_lab_demo_setup.prepare_demo(tmp_path)
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "local")
    secret = "demo-student-help-secret-for-tests-2026"
    teacher_token = "teacher-dashboard-token-for-tests"
    teacher_authorization = "Basic " + base64.b64encode(
        f"teacher:{teacher_token}".encode("utf-8")
    ).decode("ascii")
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_SECRET", secret)
    token = student_help_auth.create_student_token("rossi-mario", secret)
    server = None
    thread = None

    try:
        course_board_server.configure_data_root(tmp_path)
        server = course_board_server.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0), course_board_server.CourseBoardHandler
        )
        server.teacher_token = teacher_token
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        with pytest.raises(urllib.error.HTTPError) as local_teacher_unauthorized:
            urllib.request.urlopen(
                f"{base_url}/api/student-dashboard?student_id=rossi-mario",
                timeout=5,
            )
        assert local_teacher_unauthorized.value.code == 401
        assert local_teacher_unauthorized.value.headers["WWW-Authenticate"].startswith("Basic ")
        teacher_dashboard_request = urllib.request.Request(
            f"{base_url}/api/student-dashboard?student_id=rossi-mario",
            headers={"Authorization": teacher_authorization},
        )
        with urllib.request.urlopen(teacher_dashboard_request, timeout=5) as response:
            dashboard = json.loads(response.read().decode("utf-8"))
        assignment = dashboard["lab"]["assignments"][0]
        initial_help_total = assignment["help"]["total"]
        assert "events" not in assignment["help"]
        assert "path" not in assignment["help"]
        unauthenticated_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as unauthorized:
            urllib.request.urlopen(unauthenticated_request, timeout=5)
        assert unauthorized.value.code == 401

        connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        connection.putrequest("POST", "/api/student-lab/help")
        connection.putheader("Authorization", f"Bearer {token}")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", "non-numerico")
        connection.endheaders()
        malformed_length = connection.getresponse()
        malformed_payload = json.loads(malformed_length.read().decode("utf-8"))
        connection.close()
        assert malformed_length.status == 400
        assert malformed_payload["error"] == "Content-Length non valido."

        oversized_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=b"x" * (course_board_server.MAX_STUDENT_HELP_REQUEST_BYTES + 1),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as oversized:
            urllib.request.urlopen(oversized_request, timeout=5)
        assert oversized.value.code == 413

        non_object_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=b"[]",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as non_object:
            urllib.request.urlopen(non_object_request, timeout=5)
        assert non_object.value.code == 400

        request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=json.dumps(
                {
                    "assignment_id": assignment["assignment_id"],
                    "help_type": "teoria",
                    "prompt": "Quale concetto devo ripassare?",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))

        history_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help-history?assignment_id={assignment['assignment_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(history_request, timeout=5) as response:
            history = json.loads(response.read().decode("utf-8"))
        assert any(event["prompt"] == "Quale concetto devo ripassare?" for event in history["events"])
        assignments_request = urllib.request.Request(
            f"{base_url}/api/student-lab/assignments",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(assignments_request, timeout=5) as response:
            remote_assignments = json.loads(response.read().decode("utf-8"))
        assert remote_assignments["student_id"] == "rossi-mario"
        assert remote_assignments["assignments"][0]["help"]["total"] == initial_help_total + 1

        original_locked_payload = course_board_server.locked_student_lab_payload

        def fail_student_payload_without_exposing_path(**kwargs):
            try:
                raise ValueError(r"Report non valido: C:\dati-docente\privato\report.json")
            except ValueError as error:
                raise student_lab_service.StudentLabDataError(
                    "Dati delle consegne non disponibili. Avvisa il docente."
                ) from error

        monkeypatch.setattr(
            course_board_server,
            "locked_student_lab_payload",
            fail_student_payload_without_exposing_path,
        )
        with pytest.raises(urllib.error.HTTPError) as invalid_student_data:
            urllib.request.urlopen(assignments_request, timeout=5)
        invalid_student_payload = json.loads(invalid_student_data.value.read().decode("utf-8"))
        assert invalid_student_data.value.code == 500
        assert invalid_student_payload["error"] == course_board_server.STUDENT_HELP_SERVER_ERROR
        assert "dati-docente" not in json.dumps(invalid_student_payload)
        monkeypatch.setattr(
            course_board_server,
            "locked_student_lab_payload",
            original_locked_payload,
        )

        unauthenticated_history = urllib.request.Request(
            f"{base_url}/api/student-lab/help-history?assignment_id={assignment['assignment_id']}"
        )
        with pytest.raises(urllib.error.HTTPError) as history_unauthorized:
            urllib.request.urlopen(unauthenticated_history, timeout=5)
        assert history_unauthorized.value.code == 401

        original_loopback_check = course_board_server.CourseBoardHandler.is_loopback_client
        monkeypatch.setattr(course_board_server.CourseBoardHandler, "is_loopback_client", lambda self: False)
        original_student_lab_payload = course_board_server.student_lab_service.student_lab_payload
        received_now = []

        def capture_student_lab_now(**kwargs):
            received_now.append(kwargs.get("now"))
            return original_student_lab_payload(**kwargs)

        monkeypatch.setattr(
            course_board_server.student_lab_service,
            "student_lab_payload",
            capture_student_lab_now,
        )
        remote_assignments_with_future_time = urllib.request.Request(
            f"{base_url}/api/student-lab/assignments?now=9999-01-01T00:00:00%2B00:00",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(remote_assignments_with_future_time, timeout=5) as response:
            assert response.status == 200
        assert received_now[-1] is None
        monkeypatch.setattr(
            course_board_server.student_lab_service,
            "student_lab_payload",
            original_student_lab_payload,
        )
        for teacher_path in ("api/assignment-reports", "api/assignments", "api/student-dashboard"):
            with pytest.raises(urllib.error.HTTPError) as remote_teacher_api:
                urllib.request.urlopen(f"{base_url}/{teacher_path}", timeout=5)
            assert remote_teacher_api.value.code == 401
        authenticated_teacher_request = urllib.request.Request(
            f"{base_url}/api/assignments",
            headers={"Authorization": teacher_authorization},
        )
        with urllib.request.urlopen(authenticated_teacher_request, timeout=5) as teacher_response:
            assert teacher_response.status == 200
        remote_delete = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as remote_teacher_write:
            urllib.request.urlopen(remote_delete, timeout=5)
        assert remote_teacher_write.value.code == 401
        cross_site_teacher_write = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={
                "Authorization": teacher_authorization,
                "Content-Type": "application/json",
                "Origin": "https://pagina-malevola.test",
                "Sec-Fetch-Site": "cross-site",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as cross_site_rejected:
            urllib.request.urlopen(cross_site_teacher_write, timeout=5)
        assert cross_site_rejected.value.code == 403
        plain_text_teacher_write = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={
                "Authorization": teacher_authorization,
                "Content-Type": "text/plain",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as plain_text_rejected:
            urllib.request.urlopen(plain_text_teacher_write, timeout=5)
        assert plain_text_rejected.value.code == 415
        with urllib.request.urlopen(history_request, timeout=5) as remote_student_history:
            assert remote_student_history.status == 200
        unknown_student_request = urllib.request.Request(
            f"{base_url}/api/student-lab/unknown",
            data=b"body-che-non-deve-essere-letto",
            headers={"Content-Length": str(10**9)},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as remote_unknown_student_api:
            urllib.request.urlopen(unknown_student_request, timeout=5)
        assert remote_unknown_student_api.value.code == 401
        for read_only_path in ("assignments", "help-history"):
            wrong_method_request = urllib.request.Request(
                f"{base_url}/api/student-lab/{read_only_path}",
                data=b"x",
                headers={"Content-Length": str(10**9)},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as remote_wrong_method:
                urllib.request.urlopen(wrong_method_request, timeout=5)
            assert remote_wrong_method.value.code == 401
        public_asset = tmp_path / "tools" / "student-public.js"
        public_asset.parent.mkdir(parents=True, exist_ok=True)
        public_asset.write_text("console.log('pubblico');\n", encoding="utf-8")
        secret_file = tmp_path / ".secrets" / "ai.secret"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text("OPENAI_API_KEY=non-esporre\n", encoding="utf-8")
        git_config = tmp_path / ".git" / "config"
        git_config.parent.mkdir(parents=True, exist_ok=True)
        git_config.write_text("[remote]\n", encoding="utf-8")
        monkeypatch.setattr(course_board_server, "APP_ROOT", tmp_path)
        with pytest.raises(urllib.error.HTTPError) as public_unauthorized:
            urllib.request.urlopen(f"{base_url}/tools/student-public.js", timeout=5)
        assert public_unauthorized.value.code == 401
        public_request = urllib.request.Request(
            f"{base_url}/tools/student-public.js",
            headers={"Authorization": teacher_authorization},
        )
        with urllib.request.urlopen(public_request, timeout=5) as public_response:
            assert public_response.status == 200
            assert public_response.headers["Content-Security-Policy"] == "frame-ancestors 'none'"
            assert public_response.headers["X-Frame-Options"] == "DENY"
            assert public_response.headers["X-Content-Type-Options"] == "nosniff"
        for private_path in (".secrets/ai.secret", ".git/config"):
            private_request = urllib.request.Request(
                f"{base_url}/{private_path}",
                headers={"Authorization": teacher_authorization},
            )
            with pytest.raises(urllib.error.HTTPError) as private_file:
                urllib.request.urlopen(private_request, timeout=5)
            assert private_file.value.code == 403
        monkeypatch.setattr(
            course_board_server.CourseBoardHandler,
            "is_loopback_client",
            original_loopback_check,
        )

        monkeypatch.setattr(student_help_service, "MAX_HELP_EVENTS_PER_ASSIGNMENT", 2)
        with pytest.raises(urllib.error.HTTPError) as rate_limited:
            urllib.request.urlopen(request, timeout=5)
        assert rate_limited.value.code == 429

        monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "provider-non-valido")
        monkeypatch.setattr(student_help_service, "MAX_HELP_EVENTS_PER_ASSIGNMENT", 500)
        with urllib.request.urlopen(request, timeout=5) as invalid_provider_response:
            invalid_provider_payload = json.loads(invalid_provider_response.read().decode("utf-8"))
        assert invalid_provider_response.status == 200
        assert invalid_provider_payload["event"]["response"]["status"] == "ready"

        ai_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=json.dumps(
                {
                    "assignment_id": assignment["assignment_id"],
                    "help_type": "ai",
                    "prompt": "Dammi una domanda guida.",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(ai_request, timeout=5) as invalid_ai_provider_response:
            invalid_ai_provider_payload = json.loads(
                invalid_ai_provider_response.read().decode("utf-8")
            )
        assert invalid_ai_provider_response.status == 200
        assert invalid_ai_provider_payload["event"]["response"]["status"] == "error"
        assert invalid_ai_provider_payload["event"]["provider_status"] == "completed"
        monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "local")

        monkeypatch.setattr(course_board_server, "APP_ROOT", tmp_path.parent)
        private_log_request = urllib.request.Request(
            f"{base_url}/{tmp_path.name}/teacher-help-events/rossi-mario/"
            f"{assignment['assignment_id']}/events.json",
            headers={"Authorization": teacher_authorization},
        )
        with pytest.raises(urllib.error.HTTPError) as private_log:
            urllib.request.urlopen(private_log_request, timeout=5)
        assert private_log.value.code == 403

        def fail_with_pending_request(payload, *, student_id):
            raise student_help_service.StudentHelpPendingError("Richiesta ancora in elaborazione.")

        monkeypatch.setattr(course_board_server, "record_student_help", fail_with_pending_request)
        with pytest.raises(urllib.error.HTTPError) as pending_request:
            urllib.request.urlopen(request, timeout=5)
        assert pending_request.value.code == 409

        def fail_with_internal_path(payload, *, student_id):
            raise OSError(r"C:\dati-docente\segreto\events.json")

        monkeypatch.setattr(course_board_server, "record_student_help", fail_with_internal_path)
        with pytest.raises(urllib.error.HTTPError) as internal_error:
            urllib.request.urlopen(request, timeout=5)
        internal_payload = json.loads(internal_error.value.read().decode("utf-8"))
        assert internal_error.value.code == 500
        assert internal_payload["error"] == course_board_server.STUDENT_HELP_SERVER_ERROR
        assert "dati-docente" not in json.dumps(internal_payload)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        course_board_server.configure_data_root(original_root)

    assert result["ok"] is True
    assert result["event"]["allowed"] is True
    assert result["event"]["response"]["provider"] == "deterministic-local"
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "rossi-mario",
        assignment["assignment_id"],
    )
    events = json.loads(log_path.read_text(encoding="utf-8"))["events"]
    assert any(event["prompt"] == "Quale concetto devo ripassare?" for event in events)
    assert any(event["prompt"] == "Dammi una domanda guida." for event in events)


def test_student_dashboard_uses_configured_demo_data_root(tmp_path) -> None:
    original_root = course_board_server.ROOT
    student_lab_demo_setup.prepare_demo(tmp_path)

    try:
        configured = course_board_server.configure_data_root(tmp_path)
        dashboard = course_board_server.student_dashboard("rossi-mario")
    finally:
        course_board_server.configure_data_root(original_root)

    assert configured == tmp_path.resolve(strict=False)
    assert dashboard["student_id"] == "rossi-mario"
    assert dashboard["lab"]["schema_version"] == "student_lab.v1"
    assert len(dashboard["lab"]["assignments"]) == 1
    lab_assignment = dashboard["lab"]["assignments"][0]
    assert lab_assignment["activity_id"] == "python-demo-somma-001"
    assert lab_assignment["report"]["exists"] is True
    assert lab_assignment["help"]["total"] == 1
    assert lab_assignment["help"]["ai_budget"]["remaining"] == 4


def test_class_roster_helpers_use_local_roster_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    classes_dir = tmp_path / "doc" / "classes"
    classes_dir.mkdir(parents=True)
    (classes_dir / "3a.json").write_text(
        json.dumps(
            {
                "id": "3A",
                "label": "3A TPSI",
                "students": [
                    {
                        "id": "rossi-mario",
                        "display_name": "Rossi Mario",
                        "github_username": "rossi-mario-gh",
                        "local_path": r"studenti\rossi-mario",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rosters = course_board_server.list_class_rosters()
    roster = course_board_server.read_class_roster("3a.json")

    assert rosters[0]["name"] == "3a.json"
    assert rosters[0]["id"] == "3A"
    assert roster["students"][0]["id"] == "rossi-mario"
    assert roster["students"][0]["github_username"] == "rossi-mario-gh"
    assert roster["students"][0]["local_path"] == "studenti/rossi-mario"


def test_save_activity_builds_valid_draft_from_gui_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    result = course_board_server.save_activity({
        "title": "Somma in Python",
        "kind": "compito-casa",
        "difficulty": "B",
        "topics": "variabili, operatori",
        "prompt": "Scrivi un programma che somma due numeri.",
        "estimated_minutes": "25",
        "language": "python",
        "source_name": "main.py",
        "class_id": "3A-TPSI",
        "github_team": "team-3a",
        "uda_id": "uda-1",
    })

    activity_path = tmp_path / "activities" / "drafts" / "somma-in-python.json"
    saved_payload = json.loads(activity_path.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["activity"]["path"] == "activities/drafts/somma-in-python.json"
    assert result["activities"] == [result["activity"]]
    assert saved_payload["id"] == "somma-in-python"
    assert saved_payload["titolo"] == "Somma in Python"
    assert saved_payload["tipo"] == "compito-casa"
    assert saved_payload["linguaggio"] == "python"
    assert saved_payload["language"] == "python"
    assert saved_payload["argomenti"] == ["variabili", "operatori"]
    assert saved_payload["metriche"]["tempo_stimato_minuti"] == 25
    assert saved_payload["contesto"] == {
        "classe": "3A-TPSI",
        "team_github": "team-3a",
        "uda": "uda-1",
        "source_name": "main.py",
    }


def test_ai_secret_status_reports_paths_and_configured_keys_without_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "AI_SECRET_PATH", tmp_path / ".secrets" / "ai.secret")
    monkeypatch.setattr(course_board_server, "LEGACY_AI_SECRET_PATH", tmp_path / "scripts" / ".secrets" / "ai.secret")
    monkeypatch.setattr(course_board_server, "AI_PROVIDERS_PATH", tmp_path / "config" / "ai_providers.yaml")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".secrets").mkdir()
    (tmp_path / ".secrets" / "ai.secret").write_text("OPENAI_API_KEY=secret-value\n", encoding="utf-8")
    (tmp_path / "scripts" / ".secrets").mkdir(parents=True)
    (tmp_path / "scripts" / ".secrets" / "ai.secret").write_text("GEMINI_API_KEY=legacy-secret\n", encoding="utf-8")

    status = course_board_server.ai_secret_status()

    assert status["path"] == ".secrets/ai.secret"
    assert status["exists"] is True
    assert status["legacy_path"] == "scripts/.secrets/ai.secret"
    assert status["legacy_exists"] is True
    assert status["configured_keys"]["OPENAI_API_KEY"] is True
    assert status["configured_keys"]["GEMINI_API_KEY"] is False
    assert "secret-value" not in json.dumps(status)
    assert "legacy-secret" not in json.dumps(status)
