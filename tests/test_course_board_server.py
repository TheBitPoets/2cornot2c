from __future__ import annotations

import http.client
import json
import threading
import urllib.error
import urllib.request

import pytest

from scripts import (
    assignment_records,
    course_board_server,
    student_help_auth,
    student_help_service,
    student_lab_demo_setup,
)
from scripts.student_help_provider import StudentHelpResponse


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
    monkeypatch.setattr(course_board_server.shutil, "rmtree", lambda path: (_ for _ in ()).throw(PermissionError()))

    with pytest.raises(PermissionError):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]


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

    monkeypatch.setattr(course_board_server, "student_help_provider", lambda: BlockingProvider())
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
            "support_policy": {"ai_allowed": True},
            "context": {"secret": "client-controlled"},
        },
        student_id="rossi-mario",
    )

    assert response == {"ok": True, "event": {"allowed": True, "label": "Aiuto AI"}}
    assert captured == {
        "root": tmp_path,
        "assignments_dir": tmp_path / "teacher-assignments",
        "student_id": "rossi-mario",
        "assignment_id": "assignment-001",
        "help_type": "ai",
        "prompt": "Dammi una domanda guida.",
        "provider": provider,
    }


def test_student_help_http_endpoint_records_request_on_server_root(tmp_path, monkeypatch) -> None:
    original_root = course_board_server.ROOT
    student_lab_demo_setup.prepare_demo(tmp_path)
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "local")
    secret = "demo-student-help-secret-for-tests-2026"
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_SECRET", secret)
    token = student_help_auth.create_student_token("rossi-mario", secret)
    server = None
    thread = None

    try:
        course_board_server.configure_data_root(tmp_path)
        server = course_board_server.ThreadingHTTPServer(("127.0.0.1", 0), course_board_server.CourseBoardHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(
            f"{base_url}/api/student-dashboard?student_id=rossi-mario",
            timeout=5,
        ) as response:
            dashboard = json.loads(response.read().decode("utf-8"))
        assignment = dashboard["lab"]["assignments"][0]
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
        unauthenticated_history = urllib.request.Request(
            f"{base_url}/api/student-lab/help-history?assignment_id={assignment['assignment_id']}"
        )
        with pytest.raises(urllib.error.HTTPError) as history_unauthorized:
            urllib.request.urlopen(unauthenticated_history, timeout=5)
        assert history_unauthorized.value.code == 401

        original_loopback_check = course_board_server.CourseBoardHandler.is_loopback_client
        monkeypatch.setattr(course_board_server.CourseBoardHandler, "is_loopback_client", lambda self: False)
        for teacher_path in ("api/assignment-reports", "api/assignments", "api/student-dashboard"):
            with pytest.raises(urllib.error.HTTPError) as remote_teacher_api:
                urllib.request.urlopen(f"{base_url}/{teacher_path}", timeout=5)
            assert remote_teacher_api.value.code == 403
        remote_delete = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as remote_teacher_write:
            urllib.request.urlopen(remote_delete, timeout=5)
        assert remote_teacher_write.value.code == 403
        with urllib.request.urlopen(history_request, timeout=5) as remote_student_history:
            assert remote_student_history.status == 200
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
        with urllib.request.urlopen(f"{base_url}/tools/student-public.js", timeout=5) as public_response:
            assert public_response.status == 200
        for private_path in (".secrets/ai.secret", ".git/config"):
            with pytest.raises(urllib.error.HTTPError) as private_file:
                urllib.request.urlopen(f"{base_url}/{private_path}", timeout=5)
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
        with pytest.raises(urllib.error.HTTPError) as invalid_provider:
            urllib.request.urlopen(request, timeout=5)
        invalid_provider_payload = json.loads(invalid_provider.value.read().decode("utf-8"))
        assert invalid_provider.value.code == 500
        assert invalid_provider_payload["error"] == course_board_server.STUDENT_HELP_SERVER_ERROR
        monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "local")

        monkeypatch.setattr(course_board_server, "APP_ROOT", tmp_path.parent)
        with pytest.raises(urllib.error.HTTPError) as private_log:
            urllib.request.urlopen(
                f"{base_url}/{tmp_path.name}/teacher-help-events/rossi-mario/"
                f"{assignment['assignment_id']}/events.json",
                timeout=5,
            )
        assert private_log.value.code == 403

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
    assert events[-1]["prompt"] == "Quale concetto devo ripassare?"


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
