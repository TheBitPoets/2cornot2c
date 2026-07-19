from __future__ import annotations

from pathlib import Path


def test_associated_course_update_declares_overwrite_intent() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    function_source = source.split("async function saveAssociatedCourseDesign()", 1)[1].split(
        "async function saveActualProgress", 1
    )[0]

    assert "overwrite: true" in function_source
