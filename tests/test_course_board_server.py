from __future__ import annotations

import json

from scripts import course_board_server


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
