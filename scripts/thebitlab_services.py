from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.thebitlab_storage_ports import AssignmentStorage, ClassRosterStorage, CourseStorage


class CourseService:
    """Application service for course designs and school calendars."""

    def __init__(self, storage: CourseStorage) -> None:
        self.storage = storage

    def safe_design_name(self, name: str) -> str:
        """Validate a JSON filename used by saved designs and calendars."""

        return self.storage.safe_design_name(name)

    def saved_design_path(self, name: str) -> Path:
        """Return the safe path for a saved course design."""

        return self.storage.saved_design_path(name)

    def school_calendar_path(self, name: str) -> Path:
        """Return the safe path for a saved school calendar."""

        return self.storage.school_calendar_path(name)

    def read_design(self) -> dict[str, Any]:
        """Load the current course design."""

        return self.storage.read_design()

    def write_design(self, payload: dict[str, Any]) -> None:
        """Persist the current course design."""

        self.storage.write_design(payload)

    def list_saved_designs(self) -> list[dict[str, str]]:
        """List saved course designs."""

        return self.storage.list_saved_designs()

    def read_saved_design(self, name: str) -> dict[str, Any]:
        """Read a saved course design by filename."""

        return self.storage.read_saved_design(name)

    def write_saved_design(
        self,
        name: str,
        payload: dict[str, Any],
        overwrite: bool = True,
    ) -> dict[str, str]:
        """Persist a named course design."""

        return self.storage.write_saved_design(name, payload, overwrite=overwrite)

    def delete_saved_design(
        self,
        name: str,
        delete_calendars: bool = False,
        calendars: list[str] | None = None,
    ) -> dict[str, Any]:
        """Delete an archived course design and, optionally, its linked calendars."""

        return self.storage.delete_saved_design(name, delete_calendars, calendars)

    def list_school_calendars(self) -> list[dict[str, str]]:
        """List saved school calendars."""

        return self.storage.list_school_calendars()

    def read_school_calendar(self, name: str) -> dict[str, Any]:
        """Read a saved school calendar by filename."""

        return self.storage.read_school_calendar(name)

    def write_school_calendar(self, name: str, payload: dict[str, Any]) -> dict[str, str]:
        """Persist a named school calendar."""

        return self.storage.write_school_calendar(name, payload)


class AssignmentService:
    """Application service for assignment dashboard data."""

    def __init__(self, storage: AssignmentStorage) -> None:
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

    def save_activity(self, payload: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        """Persist one teacher-authored activity draft."""

        return self.storage.save_activity(payload, overwrite)

    def assignment_overview(self) -> list[dict[str, Any]]:
        """Return one row per student/activity across all saved teacher reports."""

        return AssignmentOverviewService(self.storage).assignment_overview()

    def student_dashboard(self, student_id: str) -> dict[str, Any]:
        """Return the minimal student-facing assignment dashboard."""

        return AssignmentOverviewService(self.storage).student_dashboard(student_id)


class AssignmentOverviewService:
    """Query service for derived assignment dashboard rows."""

    def __init__(self, storage: AssignmentStorage) -> None:
        self.storage = storage

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
                        "assigned_at": payload.get("assigned_at") or "",
                        "due_at": payload.get("due_at") or "",
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
                        "failed_test_details": grading.get("failed_test_details", []),
                        "teacher_grade": grading.get("teacher_grade"),
                        "score": grading.get("score"),
                        "ai_status": ai_feedback.get("status", ""),
                    }
                )
        return rows

    def student_dashboard(self, student_id: str) -> dict[str, Any]:
        """Return assignment rows visible to one student."""

        clean_student_id = student_id.strip()
        if not clean_student_id:
            raise ValueError("student_id mancante.")
        assignments = []
        for report in self.storage.list_assignment_reports():
            try:
                payload = self.storage.read_assignment_report(report["name"])
            except Exception:  # noqa: BLE001
                continue
            for student in payload.get("students", []):
                if not isinstance(student, dict) or not _matches_student(student, clean_student_id):
                    continue
                submission = student.get("submission") if isinstance(student.get("submission"), dict) else {}
                grading = student.get("grading") if isinstance(student.get("grading"), dict) else {}
                ai_feedback = student.get("ai_feedback") if isinstance(student.get("ai_feedback"), dict) else {}
                assignments.append(
                    {
                        "report_name": report["name"],
                        "activity_id": payload.get("activity_id", ""),
                        "title": payload.get("title", "") or payload.get("activity_id", ""),
                        "kind": payload.get("kind", ""),
                        "student_support_mode": payload.get("student_support_mode", ""),
                        "class_id": payload.get("class_id", ""),
                        "class_label": payload.get("class_label", ""),
                        "assigned_at": payload.get("assigned_at") or "",
                        "due_at": payload.get("due_at") or "",
                        "status": student.get("status", ""),
                        "submitted": bool(student.get("submitted", False)),
                        "late": bool(student.get("late", False)),
                        "repo": student.get("repo", ""),
                        "repo_github_url": student.get("repo_github_url", ""),
                        "submitted_at": submission.get("submitted_at"),
                        "commit": submission.get("commit"),
                        "source_path": submission.get("source_path"),
                        "source_github_url": _submission_source_github_url(submission),
                        "grading": {
                            "status": grading.get("status", ""),
                            "passed": grading.get("passed"),
                            "tests_passed": grading.get("tests_passed"),
                            "tests_total": grading.get("tests_total"),
                            "failed_tests": grading.get("failed_tests", []),
                            "failed_test_details": grading.get("failed_test_details", []),
                            "teacher_grade": grading.get("teacher_grade"),
                            "score": grading.get("score"),
                            "detail": grading.get("detail", ""),
                        },
                        "approved_feedback": _approved_student_feedback(ai_feedback),
                    }
                )
        assignments.sort(key=lambda row: (row.get("due_at") or "", row.get("activity_id") or ""))
        return {"student_id": clean_student_id, "assignments": assignments}


def _matches_student(student: dict[str, Any], student_id: str) -> bool:
    return student.get("student_id") == student_id or student.get("student") == student_id


def _submission_source_github_url(submission: dict[str, Any]) -> str | None:
    source_url = _clean_optional_string(submission.get("source_github_url"))
    file_urls = _submission_file_github_urls(submission)
    if source_url and not _looks_like_broken_demo_url(source_url):
        return source_url
    for file_url in file_urls:
        if not _looks_like_broken_demo_url(file_url):
            return file_url
    return source_url


def _submission_file_github_urls(submission: dict[str, Any]) -> list[str]:
    files = submission.get("files")
    if not isinstance(files, list):
        return []
    source_path = _normalized_path(submission.get("source_path"))
    urls = []
    for file_entry in files:
        if not isinstance(file_entry, dict):
            continue
        file_url = _clean_optional_string(file_entry.get("github_url"))
        if not file_url:
            continue
        file_path = _normalized_path(file_entry.get("path"))
        if (
            not source_path
            or file_path == source_path
            or file_path.endswith(f"/{source_path}")
            or source_path.endswith(f"/{file_path}")
        ):
            urls.append(file_url)
    return urls


def _normalized_path(value: Any) -> str:
    return str(value or "").replace("\\", "/").lstrip("./")


def _clean_optional_string(value: Any) -> str | None:
    clean_value = str(value or "").strip()
    return clean_value or None


def _looks_like_broken_demo_url(url: str) -> bool:
    return "/blob/" in url and "/scripts/examples/assignment_tracking/" in url


def _approved_student_feedback(ai_feedback: dict[str, Any]) -> dict[str, Any] | None:
    if ai_feedback.get("status") != "approved" or ai_feedback.get("approved_by_teacher") is not True:
        return None
    return {
        "summary": ai_feedback.get("summary"),
        "student_feedback": ai_feedback.get("student_feedback"),
        "suggested_grade": ai_feedback.get("suggested_grade"),
        "confidence": ai_feedback.get("confidence"),
    }


class ClassRosterService:
    """Application service for local class/student rosters."""

    def __init__(self, storage: ClassRosterStorage) -> None:
        self.storage = storage

    def safe_roster_name(self, name: str) -> str:
        """Validate a local roster filename."""

        return self.storage.safe_roster_name(name)

    def list_class_rosters(self) -> list[dict[str, Any]]:
        """List available class rosters."""

        return self.storage.list_class_rosters()

    def read_class_roster(self, name: str) -> dict[str, Any]:
        """Read one class roster."""

        return self.storage.read_class_roster(name)
