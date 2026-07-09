from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.thebitlab_storage import JsonAssignmentStorage


class AssignmentService:
    """Application service for assignment dashboard data."""

    def __init__(self, storage: JsonAssignmentStorage) -> None:
        self.storage = storage

    def safe_teacher_report_path(self, name: str) -> Path:
        """Return a safe teacher-report path below the configured reports folder."""

        return self.storage.safe_teacher_report_path(name)

    def list_assignment_reports(self) -> list[dict[str, Any]]:
        """List saved assignment tracking reports."""

        return self.storage.list_assignment_reports()

    def read_assignment_report(self, name: str) -> dict[str, Any]:
        """Read one saved assignment tracking report."""

        return self.storage.read_assignment_report(name)

    def list_activities(self) -> list[dict[str, Any]]:
        """List available activities for the assignment dashboard."""

        return self.storage.list_activities()

    def assignment_overview(self) -> list[dict[str, Any]]:
        """Return one row per student/activity across all saved teacher reports."""

        rows = []
        for report in self.storage.list_assignment_reports():
            try:
                payload = self.storage.read_assignment_report(report["name"])
            except Exception:  # noqa: BLE001
                continue
            for student in payload.get("students", []):
                if not isinstance(student, dict):
                    continue
                submission = student.get("submission") if isinstance(student.get("submission"), dict) else {}
                grading = student.get("grading") if isinstance(student.get("grading"), dict) else {}
                ai_feedback = student.get("ai_feedback") if isinstance(student.get("ai_feedback"), dict) else {}
                rows.append(
                    {
                        "report_name": report["name"],
                        "report_path": report["path"],
                        "activity_id": payload.get("activity_id", ""),
                        "title": payload.get("title", ""),
                        "class_id": payload.get("class_id", ""),
                        "class_label": payload.get("class_label", ""),
                        "github_team": payload.get("github_team", ""),
                        "kind": payload.get("kind", ""),
                        "student_support_mode": payload.get("student_support_mode", ""),
                        "assigned_at": payload.get("assigned_at", ""),
                        "due_at": payload.get("due_at", ""),
                        "student": student.get("student", ""),
                        "repo": student.get("repo", ""),
                        "status": student.get("status", ""),
                        "submitted": bool(student.get("submitted", False)),
                        "late": bool(student.get("late", False)),
                        "submitted_at": submission.get("submitted_at"),
                        "commit": submission.get("commit"),
                        "source_path": submission.get("source_path"),
                        "grading_status": grading.get("status", ""),
                        "tests_passed": grading.get("tests_passed"),
                        "tests_total": grading.get("tests_total"),
                        "failed_tests": grading.get("failed_tests", []),
                        "teacher_grade": grading.get("teacher_grade"),
                        "score": grading.get("score"),
                        "ai_status": ai_feedback.get("status", ""),
                    }
                )
        return rows
