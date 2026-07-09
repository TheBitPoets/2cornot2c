from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.thebitlab_storage_ports import AssignmentStorage


SCHEMA_VERSION = "0001_assignment_index"


def connect_assignment_index(db_path: Path) -> sqlite3.Connection:
    """Open an assignment index database with stable row access."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_assignment_index(connection: sqlite3.Connection) -> None:
    """Create the minimal SQLite schema for the assignment overview spike."""

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version TEXT PRIMARY KEY,
          applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assignments (
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

        CREATE INDEX IF NOT EXISTS idx_assignments_activity_id ON assignments(activity_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_class_id ON assignments(class_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_due_at ON assignments(due_at);
        CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status);

        CREATE TABLE IF NOT EXISTS registers (
          id TEXT PRIMARY KEY,
          assignment_id TEXT REFERENCES assignments(id),
          class_id TEXT DEFAULT '',
          report_path TEXT NOT NULL,
          generated_at TEXT,
          updated_at TEXT NOT NULL,
          source_hash TEXT,
          payload_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_registers_assignment_id ON registers(assignment_id);
        CREATE INDEX IF NOT EXISTS idx_registers_class_id ON registers(class_id);
        CREATE INDEX IF NOT EXISTS idx_registers_report_path ON registers(report_path);

        CREATE TABLE IF NOT EXISTS submissions (
          id TEXT PRIMARY KEY,
          assignment_id TEXT NOT NULL REFERENCES assignments(id),
          student_id TEXT NOT NULL,
          register_id TEXT REFERENCES registers(id),
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

        CREATE INDEX IF NOT EXISTS idx_submissions_assignment_id ON submissions(assignment_id);
        CREATE INDEX IF NOT EXISTS idx_submissions_student_id ON submissions(student_id);
        CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
        CREATE INDEX IF NOT EXISTS idx_submissions_submitted ON submissions(submitted);
        CREATE INDEX IF NOT EXISTS idx_submissions_late ON submissions(late);
        CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at);

        CREATE TABLE IF NOT EXISTS grading_results (
          id TEXT PRIMARY KEY,
          submission_id TEXT NOT NULL REFERENCES submissions(id),
          status TEXT NOT NULL DEFAULT '',
          tests_passed INTEGER,
          tests_total INTEGER,
          score REAL,
          teacher_grade REAL,
          graded_at TEXT,
          payload_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_grading_results_submission_id ON grading_results(submission_id);
        CREATE INDEX IF NOT EXISTS idx_grading_results_status ON grading_results(status);
        """
    )
    connection.execute(
        "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    connection.commit()


def rebuild_assignment_index_from_storage(storage: AssignmentStorage, db_path: Path) -> dict[str, int]:
    """Rebuild an isolated SQLite assignment index from assignment reports."""

    with connect_assignment_index(db_path) as connection:
        initialize_assignment_index(connection)
        _clear_assignment_index(connection)
        reports_read = 0
        for report in storage.list_assignment_reports():
            try:
                payload = storage.read_assignment_report(str(report["name"]))
            except Exception:  # noqa: BLE001
                continue
            reports_read += 1
            assignment_id = _assignment_id(payload)
            register_id = _stable_id("register", str(report["name"]))
            connection.execute(
                """
                INSERT OR REPLACE INTO assignments(
                  id, activity_id, class_id, assigned_at, due_at, status, source_path, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment_id,
                    str(payload.get("activity_id", "")),
                    str(payload.get("class_id", "")),
                    payload.get("assigned_at") or None,
                    payload.get("due_at") or None,
                    str(payload.get("status", "")),
                    report.get("path"),
                    _json_payload(payload),
                ),
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO registers(
                  id, assignment_id, class_id, report_path, generated_at, updated_at, source_hash, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    register_id,
                    assignment_id,
                    str(payload.get("class_id", "")),
                    str(report.get("path", "")),
                    payload.get("generated_at") or None,
                    str(report.get("updated_at") or ""),
                    _stable_hash(payload),
                    _json_payload(payload),
                ),
            )
            for student in payload.get("students", []):
                if not isinstance(student, dict):
                    continue
                submission_id = _stable_id("submission", assignment_id, str(student.get("student", "")))
                submission = student.get("submission") if isinstance(student.get("submission"), dict) else {}
                grading = student.get("grading") if isinstance(student.get("grading"), dict) else {}
                connection.execute(
                    """
                    INSERT INTO submissions(
                      id, assignment_id, student_id, register_id, status, submitted, submitted_at, late,
                      repo_ref, commit_sha, source_path, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(assignment_id, student_id) DO UPDATE SET
                      register_id=excluded.register_id,
                      status=excluded.status,
                      submitted=excluded.submitted,
                      submitted_at=excluded.submitted_at,
                      late=excluded.late,
                      repo_ref=excluded.repo_ref,
                      commit_sha=excluded.commit_sha,
                      source_path=excluded.source_path,
                      payload_json=excluded.payload_json
                    """,
                    (
                        submission_id,
                        assignment_id,
                        str(student.get("student", "")),
                        register_id,
                        str(student.get("status", "")),
                        _to_int_bool(student.get("submitted", False)),
                        submission.get("submitted_at"),
                        _to_int_bool(student.get("late", False)),
                        student.get("repo"),
                        submission.get("commit"),
                        submission.get("source_path"),
                        _json_payload(student),
                    ),
                )
                grading_id = _stable_id("grading", submission_id)
                connection.execute(
                    """
                    INSERT OR REPLACE INTO grading_results(
                      id, submission_id, status, tests_passed, tests_total, score, teacher_grade, graded_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        grading_id,
                        submission_id,
                        str(grading.get("status", "")),
                        grading.get("tests_passed"),
                        grading.get("tests_total"),
                        grading.get("score"),
                        grading.get("teacher_grade"),
                        grading.get("graded_at"),
                        _json_payload(grading),
                    ),
                )
        connection.commit()
        return {
            "reports": reports_read,
            "assignments": _table_count(connection, "assignments"),
            "submissions": _table_count(connection, "submissions"),
            "grading_results": _table_count(connection, "grading_results"),
        }


def list_assignment_index_rows(db_path: Path) -> list[dict[str, Any]]:
    """Return denormalized assignment rows from the SQLite index."""

    with connect_assignment_index(db_path) as connection:
        initialize_assignment_index(connection)
        rows = connection.execute(
            """
            SELECT
              r.report_path,
              a.activity_id,
              a.class_id,
              a.assigned_at,
              a.due_at,
              s.student_id AS student,
              s.repo_ref AS repo,
              s.status,
              s.submitted,
              s.late,
              s.submitted_at,
              s.commit_sha,
              s.source_path,
              g.status AS grading_status,
              g.tests_passed,
              g.tests_total,
              g.score,
              g.teacher_grade
            FROM submissions s
            JOIN assignments a ON a.id = s.assignment_id
            LEFT JOIN registers r ON r.id = s.register_id
            LEFT JOIN grading_results g ON g.submission_id = s.id
            ORDER BY a.activity_id, s.student_id
            """
        ).fetchall()
    return [
        {
            **{key: row[key] for key in row.keys() if key != "commit_sha"},
            "commit": row["commit_sha"],
            "submitted": bool(row["submitted"]),
            "late": bool(row["late"]),
        }
        for row in rows
    ]


def _clear_assignment_index(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM grading_results")
    connection.execute("DELETE FROM submissions")
    connection.execute("DELETE FROM registers")
    connection.execute("DELETE FROM assignments")


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _assignment_id(payload: dict[str, Any]) -> str:
    explicit_id = payload.get("assignment_id")
    if explicit_id:
        return str(explicit_id)
    return _stable_id(
        "assignment",
        str(payload.get("activity_id", "")),
        str(payload.get("class_id", "")),
        str(payload.get("assigned_at") or ""),
        str(payload.get("due_at") or ""),
    )


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _stable_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha1(_json_payload(payload).encode("utf-8")).hexdigest()


def _json_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _to_int_bool(value: Any) -> int:
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"1", "true", "yes", "si"} else 0
    return 1 if bool(value) else 0
