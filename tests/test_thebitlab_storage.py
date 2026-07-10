from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.thebitlab_storage import JsonAssignmentStorage, JsonCourseStorage


def test_read_design_returns_minimal_default_when_missing(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path, ["README.md"])

    assert storage.read_design() == {"version": 1, "source_files": ["README.md"], "years": []}


def test_write_and_read_current_design(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    payload = {"schema_version": "1.0", "years": [{"id": "terzo"}]}

    storage.write_design(payload)

    assert storage.read_design() == payload
    assert (tmp_path / "doc" / "course_design.json").read_text(encoding="utf-8").endswith("\n")


def test_saved_designs_are_validated_and_listed(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)

    saved = storage.write_saved_design("as_2026_2027.json", {"title": "AS 2026/2027"})

    assert saved == {
        "name": "as_2026_2027.json",
        "path": "doc/course_designs/as_2026_2027.json",
    }
    assert storage.list_saved_designs() == [saved]
    assert storage.read_saved_design("as_2026_2027.json") == {"title": "AS 2026/2027"}


def test_saved_design_rejects_unsafe_name(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.write_saved_design("../unsafe.json", {})


def test_school_calendar_metadata_tolerates_invalid_json(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    calendars_dir = tmp_path / "doc" / "calendars"
    calendars_dir.mkdir(parents=True)
    (calendars_dir / "broken.json").write_text("{", encoding="utf-8")
    (calendars_dir / "empty-link.json").write_text(json.dumps({"course_design_name": None}), encoding="utf-8")
    storage.write_school_calendar("valid.json", {"course_design_name": "as_2026_2027.json"})

    assert storage.list_school_calendars() == [
        {
            "name": "broken.json",
            "path": "doc/calendars/broken.json",
            "course_design_name": "",
        },
        {
            "name": "empty-link.json",
            "path": "doc/calendars/empty-link.json",
            "course_design_name": "",
        },
        {
            "name": "valid.json",
            "path": "doc/calendars/valid.json",
            "course_design_name": "as_2026_2027.json",
        },
    ]


def test_delete_saved_design_deletes_only_linked_calendars(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("as_2026_2027.json", {"title": "AS 2026/2027"})
    storage.write_school_calendar("linked.json", {"course_design_name": "as_2026_2027.json"})
    storage.write_school_calendar("other.json", {"course_design_name": "other.json"})

    result = storage.delete_saved_design(
        "as_2026_2027.json",
        delete_calendars=True,
        calendars=["linked.json", "other.json", "missing.json"],
    )

    assert result["name"] == "as_2026_2027.json"
    assert result["deleted_calendars"] == ["linked.json"]
    assert result["designs"] == []
    assert result["calendars"] == [
        {
            "name": "other.json",
            "path": "doc/calendars/other.json",
            "course_design_name": "other.json",
        }
    ]
    assert not (tmp_path / "doc" / "calendars" / "linked.json").exists()
    assert (tmp_path / "doc" / "calendars" / "other.json").exists()


def test_read_json_rejects_non_object_payload(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    path = tmp_path / "list.json"
    path.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(ValueError):
        storage.read_json(path)


def test_assignment_reports_are_listed_with_counts(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "title": "Activity demo",
                "class_id": "4A-INF",
                "class_label": "4A INF",
                "github_team": "team-4a-inf",
                "students": [
                    {"student": "rossi-mario", "submitted": True, "late": True},
                    {"student": "bianchi-luca", "submitted": "false", "late": "true"},
                    {"student": "verdi-anna", "submitted": "yes", "late": "false"},
                ],
            }
        ),
        encoding="utf-8",
    )

    reports = storage.list_assignment_reports()

    assert reports[0]["name"] == "demo/activity.json"
    assert reports[0]["path"] == "teacher-reports/demo/activity.json"
    assert reports[0]["class_id"] == "4A-INF"
    assert reports[0]["students"] == 3
    assert reports[0]["submitted"] == 2
    assert reports[0]["not_submitted"] == 1
    assert reports[0]["late"] == 1
    assert reports[0]["updated_at"]


def test_read_assignment_report_normalizes_student_booleans(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "submitted": "false",
                        "late": "0",
                        "submission": {"late": "yes"},
                        "grading": {"passed": "false"},
                        "ai_feedback": {"approved_by_teacher": "si"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    student = storage.read_assignment_report("activity.json")["students"][0]

    assert student["submitted"] is False
    assert student["late"] is False
    assert student["submission"]["late"] is True
    assert student["grading"]["passed"] is False
    assert student["ai_feedback"]["approved_by_teacher"] is True


def test_ai_feedback_demo_report_exposes_teacher_review_states() -> None:
    root = Path(__file__).resolve().parents[1]
    storage = JsonAssignmentStorage(root, root / "teacher-reports", [])

    report = storage.read_assignment_report("demo/ai-feedback-states.json")
    statuses = {student["student"]: student["ai_feedback"]["status"] for student in report["students"]}
    approvals = {student["student"]: student["ai_feedback"]["approved_by_teacher"] for student in report["students"]}

    assert report["activity_id"] == "demo-ai-feedback-states"
    assert statuses == {
        "rossi-mario": "draft",
        "bianchi-luca": "approved",
        "verdi-anna": "rejected",
        "neri-giulia": "not_generated",
    }
    assert approvals == {
        "rossi-mario": False,
        "bianchi-luca": True,
        "verdi-anna": False,
        "neri-giulia": False,
    }


def test_assignment_report_rejects_unsafe_or_invalid_reports(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "invalid.json").write_text(json.dumps({"students": {}}), encoding="utf-8")

    with pytest.raises(ValueError):
        storage.safe_teacher_report_path("../unsafe.json")

    with pytest.raises(ValueError, match="students"):
        storage.read_assignment_report("invalid.json")


def test_list_activities_skips_invalid_json_and_deduplicates_paths(tmp_path) -> None:
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    valid = activities_dir / "activity.json"
    valid.write_text(
        json.dumps(
            {
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "linguaggio": "python",
                "contesto": {"classe": "3A-TPSI", "team_github": "team-3a-tpsi"},
            }
        ),
        encoding="utf-8",
    )
    (activities_dir / "broken.json").write_text("{", encoding="utf-8")
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [activities_dir, activities_dir])

    assert storage.list_activities() == [
        {
            "id": "python-base-somma-001",
            "title": "Somma in Python",
            "kind": "compito-casa",
            "student_support_mode": "",
            "class_id": "3A-TPSI",
            "class_label": "3A-TPSI",
            "github_team": "team-3a-tpsi",
            "language": "python",
            "path": "activities/activity.json",
        }
    ]
