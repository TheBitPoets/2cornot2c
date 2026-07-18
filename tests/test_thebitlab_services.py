from __future__ import annotations

import json
from pathlib import Path

from scripts.thebitlab_services import AssignmentOverviewService, AssignmentService, ClassRosterService, CourseService
from scripts.thebitlab_storage import JsonAssignmentStorage, JsonClassRosterStorage, JsonCourseStorage


def course_service(tmp_path) -> CourseService:
    storage = JsonCourseStorage(tmp_path, ["README.md"])
    return CourseService(storage)


def assignment_service(tmp_path) -> AssignmentService:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    return AssignmentService(storage)


def assignment_overview_service(tmp_path) -> AssignmentOverviewService:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    return AssignmentOverviewService(storage)


def class_roster_service(tmp_path) -> ClassRosterService:
    storage = JsonClassRosterStorage(tmp_path)
    return ClassRosterService(storage)


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


def test_course_service_accepts_protocol_compatible_storage(tmp_path) -> None:
    class FakeCourseStorage:
        def safe_design_name(self, name: str) -> str:
            return name

        def saved_design_path(self, name: str) -> Path:
            return tmp_path / "designs" / name

        def school_calendar_path(self, name: str) -> Path:
            return tmp_path / "calendars" / name

        def read_design(self) -> dict[str, object]:
            return {"years": []}

        def write_design(self, payload: dict[str, object]) -> None:
            self.design = payload

        def list_saved_designs(self) -> list[dict[str, str]]:
            return [{"name": "demo.json", "path": "doc/course_designs/demo.json"}]

        def read_saved_design(self, name: str) -> dict[str, object]:
            return {"name": name}

        def write_saved_design(self, name: str, payload: dict[str, object]) -> dict[str, str]:
            return {"name": name, "path": f"doc/course_designs/{name}"}

        def delete_saved_design(
            self,
            name: str,
            delete_calendars: bool = False,
            calendars: list[str] | None = None,
        ) -> dict[str, object]:
            return {"name": name, "deleted_calendars": calendars or []}

        def list_school_calendars(self) -> list[dict[str, str]]:
            return []

        def read_school_calendar(self, name: str) -> dict[str, object]:
            return {"name": name}

        def write_school_calendar(self, name: str, payload: dict[str, object]) -> dict[str, str]:
            return {"name": name, "path": f"doc/calendars/{name}"}

    service = CourseService(FakeCourseStorage())

    assert service.read_design() == {"years": []}
    assert service.write_saved_design("demo.json", {}) == {
        "name": "demo.json",
        "path": "doc/course_designs/demo.json",
    }


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
    service = assignment_overview_service(tmp_path)
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
            "failed_test_details": [],
            "teacher_grade": 9,
            "score": None,
            "ai_status": "not_generated",
        }
    ]


def test_assignment_service_accepts_protocol_compatible_storage(tmp_path) -> None:
    class FakeAssignmentStorage:
        def safe_teacher_report_path(self, name: str) -> Path:
            return tmp_path / "teacher-reports" / name

        def list_assignment_reports(self) -> list[dict[str, object]]:
            return [{"name": "demo.json", "path": "teacher-reports/demo.json"}]

        def read_assignment_report(self, name: str) -> dict[str, object]:
            return {"activity_id": "demo", "students": [{"student": "rossi-mario"}]}

        def list_activities(self) -> list[dict[str, object]]:
            return [{"id": "demo"}]

    service = AssignmentService(FakeAssignmentStorage())

    assert service.list_activities() == [{"id": "demo"}]
    assert service.assignment_overview()[0]["student"] == "rossi-mario"


def test_student_dashboard_filters_student_and_only_approved_feedback(tmp_path) -> None:
    service = assignment_overview_service(tmp_path)
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "kind": "compito-casa",
                "student_support_mode": "guidato",
                "due_at": "2026-10-19T23:59:00+02:00",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "submission": {"submitted_at": "2026-10-18T18:22:10+02:00", "commit": "abc1234"},
                        "grading": {"status": "graded_passed", "tests_passed": 2, "tests_total": 2, "teacher_grade": 9},
                        "ai_feedback": {
                            "status": "approved",
                            "approved_by_teacher": True,
                            "summary": "Buon lavoro.",
                            "student_feedback": "Hai gestito correttamente i casi base.",
                            "suggested_grade": 9,
                            "confidence": "high",
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "student_id": "bianchi-luca",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "ai_feedback": {
                            "status": "draft",
                            "approved_by_teacher": False,
                            "summary": "Bozza non visibile.",
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    dashboard = service.student_dashboard("rossi-mario")

    assert dashboard["student_id"] == "rossi-mario"
    assert len(dashboard["assignments"]) == 1
    assignment = dashboard["assignments"][0]
    assert assignment["activity_id"] == "python-base-somma-001"
    assert assignment["grading"]["teacher_grade"] == 9
    assert assignment["approved_feedback"] == {
        "summary": "Buon lavoro.",
        "student_feedback": "Hai gestito correttamente i casi base.",
        "suggested_grade": 9,
        "confidence": "high",
    }


def test_student_dashboard_prefers_file_manifest_url_when_source_url_is_broken_demo_path(tmp_path) -> None:
    service = assignment_overview_service(tmp_path)
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    good_url = (
        "https://github.com/TheBitPoets/2cornot2c/blob/main/"
        "examples/assignment_tracking/student_repos/bianchi-luca/assignments/python-base-somma-001/main.py"
    )
    (reports_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "students": [
                    {
                        "student": "bianchi-luca",
                        "student_id": "bianchi-luca",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "submission": {
                            "source_path": (
                                "examples/assignment_tracking/student_repos/bianchi-luca/"
                                "assignments/python-base-somma-001/main.py"
                            ),
                            "source_github_url": (
                                "https://github.com/TheBitPoets/2cornot2c/blob/abc1234/scripts/"
                                "examples/assignment_tracking/student_repos/bianchi-luca/"
                                "assignments/python-base-somma-001/main.py"
                            ),
                            "files": [
                                {
                                    "path": "assignments/python-base-somma-001/main.py",
                                    "role": "solution",
                                    "github_url": good_url,
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dashboard = service.student_dashboard("bianchi-luca")

    assert dashboard["assignments"][0]["source_github_url"] == good_url


def test_assignment_overview_service_accepts_protocol_compatible_storage(tmp_path) -> None:
    class FakeAssignmentStorage:
        def safe_teacher_report_path(self, name: str) -> Path:
            return tmp_path / "teacher-reports" / name

        def list_assignment_reports(self) -> list[dict[str, object]]:
            return [{"name": "demo.json", "path": "teacher-reports/demo.json"}]

        def read_assignment_report(self, name: str) -> dict[str, object]:
            return {"activity_id": "demo", "students": [{"student": "rossi-mario"}]}

        def list_activities(self) -> list[dict[str, object]]:
            return []

    service = AssignmentOverviewService(FakeAssignmentStorage())

    assert service.assignment_overview()[0]["student"] == "rossi-mario"


def test_assignment_overview_skips_invalid_reports(tmp_path) -> None:
    service = assignment_overview_service(tmp_path)
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


def test_class_roster_service_delegates_local_roster_storage(tmp_path) -> None:
    service = class_roster_service(tmp_path)
    classes_dir = tmp_path / "doc" / "classes"
    classes_dir.mkdir(parents=True)
    (classes_dir / "3a.json").write_text(
        json.dumps({"id": "3A", "label": "3A", "students": [{"id": "rossi-mario"}]}),
        encoding="utf-8",
    )

    assert service.safe_roster_name("3a.json") == "3a.json"
    assert service.list_class_rosters()[0]["id"] == "3A"
    assert service.read_class_roster("3a.json")["students"][0]["id"] == "rossi-mario"


def test_class_roster_service_accepts_protocol_compatible_storage() -> None:
    class FakeClassRosterStorage:
        def safe_roster_name(self, name: str) -> str:
            return name

        def list_class_rosters(self) -> list[dict[str, object]]:
            return [{"name": "3a.json", "id": "3A"}]

        def read_class_roster(self, name: str) -> dict[str, object]:
            return {"id": "3A", "name": name, "students": []}

    service = ClassRosterService(FakeClassRosterStorage())

    assert service.list_class_rosters() == [{"name": "3a.json", "id": "3A"}]
    assert service.read_class_roster("3a.json")["name"] == "3a.json"
