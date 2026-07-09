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
