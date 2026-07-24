from __future__ import annotations

import json
import sqlite3

from scripts.thebitlab_services import AssignmentOverviewService
from scripts.thebitlab_sqlite_index import (
    initialize_assignment_index,
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
                    {
                        "student": "verdi-anna",
                        "repo": "TheBitPoets/verdi-anna",
                        "status": "submission_unknown",
                        "submitted": None,
                        "late": False,
                        "grading": {"status": "not_graded"},
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

    assert counts == {"reports": 1, "assignments": 1, "submissions": 3, "grading_results": 3}
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
    assert indexed_rows[2]["student"] == "verdi-anna"
    assert indexed_rows[2]["status"] == "submission_unknown"
    assert indexed_rows[2]["submitted"] is None


def test_initialize_assignment_index_migrates_legacy_submitted_constraint(tmp_path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE assignments (
              id TEXT PRIMARY KEY,
              activity_id TEXT NOT NULL,
              class_id TEXT NOT NULL DEFAULT '',
              assigned_at TEXT,
              due_at TEXT,
              status TEXT NOT NULL DEFAULT '',
              source_path TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              payload_json TEXT
            );
            CREATE TABLE registers (
              id TEXT PRIMARY KEY,
              assignment_id TEXT,
              class_id TEXT DEFAULT '',
              report_path TEXT NOT NULL,
              generated_at TEXT,
              updated_at TEXT NOT NULL,
              source_hash TEXT,
              payload_json TEXT
            );
            CREATE TABLE submissions (
              id TEXT PRIMARY KEY,
              assignment_id TEXT NOT NULL,
              student_id TEXT NOT NULL,
              register_id TEXT,
              status TEXT NOT NULL DEFAULT '',
              submitted INTEGER NOT NULL DEFAULT 0,
              submitted_at TEXT,
              late INTEGER NOT NULL DEFAULT 0,
              repo_ref TEXT,
              commit_sha TEXT,
              source_path TEXT,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              payload_json TEXT,
              UNIQUE (assignment_id, student_id)
            );
            CREATE TABLE grading_results (
              id TEXT PRIMARY KEY,
              submission_id TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT '',
              tests_passed INTEGER,
              tests_total INTEGER,
              score REAL,
              teacher_grade REAL,
              graded_at TEXT,
              payload_json TEXT
            );
            INSERT INTO assignments(id, activity_id) VALUES ('assignment-1', 'activity-1');
            INSERT INTO submissions(
              id, assignment_id, student_id, status, submitted, late
            ) VALUES ('submission-1', 'assignment-1', 'rossi-mario', 'missing', 0, 0);
            INSERT INTO grading_results(id, submission_id, status)
            VALUES ('grading-1', 'submission-1', 'not_run');
            """
        )
        initialize_assignment_index(connection)

        submitted_column = next(
            row for row in connection.execute("PRAGMA table_info(submissions)")
            if row[1] == "submitted"
        )
        submission = connection.execute(
            "SELECT student_id, submitted FROM submissions"
        ).fetchone()
        grading = connection.execute(
            "SELECT submission_id, status FROM grading_results"
        ).fetchone()

    assert submitted_column[3] == 0
    assert tuple(submission) == ("rossi-mario", 0)
    assert tuple(grading) == ("submission-1", "not_run")


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


def test_rebuild_assignment_index_derives_assignment_id_for_legacy_register_ids(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    base_payload = {
        "activity_id": "python-base-somma-001",
        "class_id": "3A-INF",
        "assigned_at": "2026-10-10T08:00:00+02:00",
        "due_at": "2026-10-18T23:59:00+02:00",
        "students": [{"student": "rossi-mario", "submitted": True}],
    }
    first_payload = {**base_payload, "id": "legacy-register-first"}
    second_payload = {**base_payload, "id": "legacy-register-second"}
    (reports_dir / "first.json").write_text(json.dumps(first_payload), encoding="utf-8")
    (reports_dir / "second.json").write_text(json.dumps(second_payload), encoding="utf-8")

    db_path = tmp_path / "assignment-index.sqlite"
    rebuild_assignment_index_from_storage(storage, db_path)

    with sqlite3.connect(db_path) as connection:
        assignment_count = connection.execute("SELECT COUNT(*) FROM assignments").fetchone()[0]
        register_count = connection.execute("SELECT COUNT(*) FROM registers").fetchone()[0]

    assert assignment_count == 1
    assert register_count == 2
