from __future__ import annotations

import json
import sqlite3

from scripts.thebitlab_services import AssignmentOverviewService
from scripts.thebitlab_sqlite_index import (
    list_assignment_index_rows,
    rebuild_assignment_index_from_storage,
)
from scripts.thebitlab_storage import JsonAssignmentStorage


def test_rebuild_assignment_index_from_storage_matches_assignment_overview(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "activity.json").write_text(
        json.dumps(
            {
                "assignment_id": "assignment-python-somma-3a",
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "class_id": "3A-INF",
                "assigned_at": "2026-10-10T08:00:00+02:00",
                "due_at": "2026-10-18T23:59:00+02:00",
                "students": [
                    {
                        "student": "rossi-mario",
                        "repo": "TheBitPoets/rossi-mario",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "late": False,
                        "submission": {
                            "submitted_at": "2026-10-18T18:22:10+02:00",
                            "commit": "abc1234",
                            "source_path": "main.py",
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
                        "repo": "TheBitPoets/bianchi-luca",
                        "status": "missing",
                        "submitted": False,
                        "late": False,
                        "grading": {"status": "not_run"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    db_path = tmp_path / "assignment-index.sqlite"
    counts = rebuild_assignment_index_from_storage(storage, db_path)
    indexed_rows = list_assignment_index_rows(db_path)
    overview_rows = AssignmentOverviewService(storage).assignment_overview()

    assert counts == {"reports": 1, "assignments": 1, "submissions": 2, "grading_results": 2}
    assert len(indexed_rows) == len(overview_rows)
    assert indexed_rows[0] == {
        "report_path": "teacher-reports/activity.json",
        "activity_id": "python-base-somma-001",
        "class_id": "3A-INF",
        "assigned_at": "2026-10-10T08:00:00+02:00",
        "due_at": "2026-10-18T23:59:00+02:00",
        "student": "bianchi-luca",
        "repo": "TheBitPoets/bianchi-luca",
        "status": "missing",
        "submitted": False,
        "late": False,
        "submitted_at": None,
        "commit": None,
        "source_path": None,
        "grading_status": "not_run",
        "tests_passed": None,
        "tests_total": None,
        "score": None,
        "teacher_grade": None,
    }
    assert indexed_rows[1]["student"] == "rossi-mario"
    assert indexed_rows[1]["submitted"] is True
    assert indexed_rows[1]["grading_status"] == "graded_passed"


def test_rebuild_assignment_index_keeps_one_submission_per_student_assignment(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    report_payload = {
        "assignment_id": "assignment-python-somma-3a",
        "activity_id": "python-base-somma-001",
        "class_id": "3A-INF",
        "students": [{"student": "rossi-mario", "submitted": True}],
    }
    (reports_dir / "first.json").write_text(json.dumps(report_payload), encoding="utf-8")
    (reports_dir / "second.json").write_text(json.dumps(report_payload), encoding="utf-8")

    db_path = tmp_path / "assignment-index.sqlite"
    rebuild_assignment_index_from_storage(storage, db_path)

    with sqlite3.connect(db_path) as connection:
        submission_count = connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0]
        assignment_count = connection.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]

    assert assignment_count == 1
    assert submission_count == 1
