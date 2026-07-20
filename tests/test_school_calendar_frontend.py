from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_associated_course_update_declares_overwrite_intent() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    function_source = source.split("async function saveAssociatedCourseDesign()", 1)[1].split(
        "async function saveActualProgress", 1
    )[0]

    assert "overwrite: true" in function_source


def test_calendar_view_selection_resets_when_period_is_not_available() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    start = source.index("function firstAvailableCalendarViewValue")
    end = source.index("\nfunction updateCalendarNavButtons", start)
    function_source = source[start:end]
    script = f"{function_source}\nprocess.stdout.write(JSON.stringify([firstAvailableCalendarViewValue(['2026-06'], '2026-03'), firstAvailableCalendarViewValue(['2026-06'], '2026-06'), firstAvailableCalendarViewValue([], '2026-03')]))"
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == ["2026-06", "2026-06", ""]
