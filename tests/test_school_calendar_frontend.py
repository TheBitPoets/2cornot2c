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


def test_activity_events_are_derived_from_visible_course_year_without_calendar_copies() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    start = source.index("function activityEventsByDate")
    end = source.index("\nfunction renderCalendarView", start)
    function_source = source[start:end]
    script = f"""
    const state = {{
      activityEvents: [
        {{
          year_id: "third", year_title: "Terzo", uda_id: "uda-1", uda_title: "Funzioni",
          activity_id: "functions-001", activity_path: "activities/functions.json",
          title: "Funzioni", role: "verification",
          scheduled_on: "2026-11-10", due_on: "2026-11-17",
        }},
        {{
          year_id: "fourth", year_title: "Quarto", uda_id: "uda-2", uda_title: "Reti",
          activity_id: "networks-001", activity_path: "activities/networks.json",
          title: "Reti", role: "practice", scheduled_on: "2026-11-10",
        }},
      ],
    }};
    function visibleTracks() {{ return [{{ id: "track-third", course_year_id: "third" }}]; }}
    {function_source}
    const events = activityEventsByDate();
    process.stdout.write(JSON.stringify({{
      scheduled: events.get("2026-11-10"),
      due: events.get("2026-11-17"),
      dates: [...events.keys()],
    }}));
    """
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout)

    assert payload["dates"] == ["2026-11-10", "2026-11-17"]
    assert payload["scheduled"][0]["activity_id"] == "functions-001"
    assert payload["scheduled"][0]["uda_title"] == "Funzioni"
    assert payload["scheduled"][0]["event_type"] == "scheduled"
    assert payload["due"][0]["event_type"] == "due"


def test_calendar_load_renders_new_calendar_when_course_context_fails() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    start = source.index("async function loadCalendarByName")
    end = source.index("\nasync function saveCalendar", start)
    function_source = source[start:end]
    script = f"""
    const assert = require("node:assert/strict");
    const state = {{ calendar: {{ school_year: "old" }}, visibleTrackIds: new Set() }};
    const els = {{ fileName: {{ value: "" }} }};
    const localStorage = {{ setItem() {{}}, removeItem() {{}} }};
    const sessionStorage = {{ setItem() {{}}, removeItem() {{}} }};
    const ACTIVE_SCHOOL_CALENDAR_KEY = "calendar";
    const ACTIVE_COURSE_DESIGN_KEY = "design";
    const ACTIVE_COURSE_SESSION_KEY = "session";
    async function api() {{ return {{ calendar: {{ school_year: "new", course_design_name: "missing.json" }} }}; }}
    async function loadCourseDesign() {{ return false; }}
    let renders = 0;
    function renderAll() {{ renders += 1; }}
    function setStatus() {{}}
    {function_source}
    (async () => {{
      await loadCalendarByName("new-calendar.json");
      assert.equal(state.calendar.school_year, "new");
      assert.equal(els.fileName.value, "new-calendar.json");
      assert.equal(renders, 1);
    }})().catch((error) => {{ console.error(error); process.exit(1); }});
    """
    subprocess.run(["node", "-e", script], check=True)


def test_course_design_loader_ignores_stale_out_of_order_response() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    start = source.index("async function loadCourseDesign")
    end = source.index("\nasync function loadCalendarForActiveCourseDesign", start)
    function_source = source[start:end]
    script = f"""
    const assert = require("node:assert/strict");
    const state = {{
      calendar: {{ course_design_name: "a.json" }},
      courseDesign: null,
      activityEvents: [],
      courseDesignRequestId: 0,
    }};
    const pending = new Map();
    function api(path) {{
      return new Promise((resolve) => pending.set(path, resolve));
    }}
    function setStatus() {{}}
    {function_source}
    (async () => {{
      const first = loadCourseDesign();
      state.calendar.course_design_name = "b.json";
      const second = loadCourseDesign();
      pending.get("/api/course-calendar-context?design=b.json")({{
        design: {{ id: "b" }}, activity_events: [{{ activity_id: "b" }}],
      }});
      assert.equal(await second, true);
      pending.get("/api/course-calendar-context?design=a.json")({{
        design: {{ id: "a" }}, activity_events: [{{ activity_id: "a" }}],
      }});
      assert.equal(await first, null);
      assert.equal(state.courseDesign.id, "b");
      assert.equal(state.activityEvents[0].activity_id, "b");
    }})().catch((error) => {{ console.error(error); process.exit(1); }});
    """
    subprocess.run(["node", "-e", script], check=True)


def test_calendar_declares_activity_event_rendering_without_persisted_event_field() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")

    assert "activityEventsByDate()" in source
    assert "dayActivityButton" in source
    assert "/api/course-calendar-context" in source
    assert "state.calendar.activity" not in source


def test_calendar_view_selection_resets_when_period_is_not_available() -> None:
    source = Path("tools/school_calendar.js").read_text(encoding="utf-8")
    start = source.index("function firstAvailableCalendarViewValue")
    end = source.index("\nfunction updateCalendarNavButtons", start)
    function_source = source[start:end]
    script = f"{function_source}\nprocess.stdout.write(JSON.stringify([firstAvailableCalendarViewValue(['2026-06'], '2026-03'), firstAvailableCalendarViewValue(['2026-06'], '2026-06'), firstAvailableCalendarViewValue([], '2026-03')]))"
    result = subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == ["2026-06", "2026-06", ""]
