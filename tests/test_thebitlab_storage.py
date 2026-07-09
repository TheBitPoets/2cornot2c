from __future__ import annotations

import json

import pytest

from scripts.thebitlab_storage import JsonCourseStorage


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
    storage.write_school_calendar("valid.json", {"course_design_name": "as_2026_2027.json"})

    assert storage.list_school_calendars() == [
        {
            "name": "broken.json",
            "path": "doc/calendars/broken.json",
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
