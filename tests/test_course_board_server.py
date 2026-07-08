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
    assert rows[0]["kind"] == "compito-casa"
    assert rows[0]["student_support_mode"] == "guidato"
    assert rows[0]["student"] == "rossi-mario"
    assert rows[0]["tests_passed"] == 2
    assert rows[0]["teacher_grade"] == 9
    assert rows[1]["student"] == "bianchi-luca"
    assert rows[1]["late"] is True
    assert rows[1]["failed_tests"] == ["somma numeri negativi"]
    assert rows[1]["score"] == 5
