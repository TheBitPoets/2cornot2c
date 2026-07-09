from __future__ import annotations

import json

from scripts.thebitlab_services import AssignmentService, CourseService
from scripts.thebitlab_storage import JsonAssignmentStorage, JsonCourseStorage


def course_service(tmp_path) -> CourseService:
    storage = JsonCourseStorage(tmp_path, ["README.md"])
    return CourseService(storage)


def assignment_service(tmp_path) -> AssignmentService:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    return AssignmentService(storage)


def test_course_service_delegates_design_and_calendar_storage(tmp_path) -> None:
    service = course_service(tmp_path)
    design = {"version": 1, "years": [{"id": "terzo"}]}

    assert service.read_design() == {"version": 1, "source_files": ["README.md"], "years": []}

    service.write_design(design)
    saved_design = service.write_saved_design("as_2026_2027.json", design)
    saved_calendar = service.write_school_calendar(
        "as_2026_2027.json",
        {"course_design_name": "as_2026_2027.json"},
    )

    assert service.read_design() == design
    assert service.list_saved_designs() == [saved_design]
    assert service.read_saved_design("as_2026_2027.json") == design
    assert saved_calendar == {"name": "as_2026_2027.json", "path": "doc/calendars/as_2026_2027.json"}
    assert service.read_school_calendar("as_2026_2027.json") == {"course_design_name": "as_2026_2027.json"}
    assert service.list_school_calendars() == [
        {
            "name": "as_2026_2027.json",
            "path": "doc/calendars/as_2026_2027.json",
            "course_design_name": "as_2026_2027.json",
        }
    ]


def test_course_service_deletes_linked_calendars(tmp_path) -> None:
    service = course_service(tmp_path)
    service.write_saved_design("as_2026_2027.json", {"title": "AS 2026/2027"})
    service.write_school_calendar("linked.json", {"course_design_name": "as_2026_2027.json"})
    service.write_school_calendar("other.json", {"course_design_name": "other.json"})

    result = service.delete_saved_design(
        "as_2026_2027.json",
        delete_calendars=True,
        calendars=["linked.json", "other.json"],
    )

    assert result["deleted_calendars"] == ["linked.json"]
    assert service.list_saved_designs() == []
    assert service.list_school_calendars() == [
        {
            "name": "other.json",
            "path": "doc/calendars/other.json",
            "course_design_name": "other.json",
        }
    ]


def test_assignment_overview_lists_student_rows(tmp_path) -> None:
    service = assignment_service(tmp_path)
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "kind": "compito-casa",
                "student_support_mode": "guidato",
                "students": [
                    {
                        "student": "rossi-mario",
                        "repo": "TheBitPoets/rossi-mario",
                        "status": "submitted_on_time",
                        "submitted": "true",
                        "late": "false",
                        "submission": {"submitted_at": "2026-10-18T18:22:10+02:00", "commit": "abc1234"},
                        "grading": {"status": "graded_passed", "tests_passed": 2, "tests_total": 2, "teacher_grade": 9},
                        "ai_feedback": {"status": "not_generated"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = service.assignment_overview()

    assert rows == [
        {
            "report_name": "activity.json",
            "report_path": "teacher-reports/activity.json",
            "activity_id": "python-base-somma-001",
            "title": "Somma in Python",
            "class_id": "",
            "class_label": "",
            "github_team": "",
            "kind": "compito-casa",
            "student_support_mode": "guidato",
            "assigned_at": "",
            "due_at": "",
            "student": "rossi-mario",
            "repo": "TheBitPoets/rossi-mario",
            "status": "submitted_on_time",
            "submitted": True,
            "late": False,
            "submitted_at": "2026-10-18T18:22:10+02:00",
            "commit": "abc1234",
            "source_path": None,
            "grading_status": "graded_passed",
            "tests_passed": 2,
            "tests_total": 2,
            "failed_tests": [],
            "teacher_grade": 9,
            "score": None,
            "ai_status": "not_generated",
        }
    ]


def test_assignment_overview_skips_invalid_reports(tmp_path) -> None:
    service = assignment_service(tmp_path)
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "invalid.json").write_text(json.dumps({"students": {}}), encoding="utf-8")
    (reports_dir / "valid.json").write_text(
        json.dumps({"activity_id": "activity", "students": [{"student": "rossi-mario"}]}),
        encoding="utf-8",
    )

    rows = service.assignment_overview()

    assert len(rows) == 1
    assert rows[0]["report_name"] == "valid.json"
    assert rows[0]["student"] == "rossi-mario"


def test_assignment_service_delegates_storage_lists(tmp_path) -> None:
    service = assignment_service(tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "activity.json").write_text(json.dumps({"id": "activity"}), encoding="utf-8")
    service.storage.activity_dirs = [activities_dir]

    assert service.list_activities()[0]["id"] == "activity"
    assert service.list_assignment_reports() == []
