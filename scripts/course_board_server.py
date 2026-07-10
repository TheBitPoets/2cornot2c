#!/usr/bin/env python3
"""Serve the local course design board and save course_design.json.

Usage:

    python scripts/course_board_server.py

Then open:

    http://localhost:8765/tools/course_board.html

The server uses only the Python standard library.  It exposes a tiny local API
for reading Markdown headings, loading/saving doc/course_design.json, and
serving static files from the repository.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import manual_ai_feedback, thebitlab_services, thebitlab_storage, track_assignments

DESIGN_PATH = ROOT / "doc" / "course_design.json"
COURSE_DESIGNS_DIR = ROOT / "doc" / "course_designs"
SCHOOL_CALENDARS_DIR = ROOT / "doc" / "calendars"
TEACHER_REPORTS_DIR = ROOT / "teacher-reports"
ACTIVITY_DIRS = [ROOT / "activities", ROOT / "examples" / "assignment_tracking"]
COURSE_PLAN_MD_PATH = ROOT / "doc" / "PERCORSO_DIDATTICO.md"
README_PATH = ROOT / "README.md"
AI_PROVIDERS_PATH = ROOT / "config" / "ai_providers.yaml"
AI_SECRET_PATH = ROOT / ".secrets" / "ai.secret"
LEGACY_AI_SECRET_PATH = ROOT / "scripts" / ".secrets" / "ai.secret"
DEFAULT_SOURCES = ["README.md", "LINUX_PROGRAMMING.md"]
ACTIVE_AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai").strip().lower()
ACTIVE_AI_MODEL = os.environ.get("AI_MODEL", "").strip()
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TAG_RE = re.compile(r"<[^>]+>")
PUNCT_RE = re.compile(r"[^\w\s-]", re.UNICODE)
SPACE_RE = re.compile(r"[\s_]+")
DESIGN_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+\.json$")
AI_FRAME_FIELDS = [
    "context",
    "prerequisites",
    "objectives",
    "recall",
    "preview",
    "next_step",
    "references",
]
COURSE_PLAN_REQUIRED_FIELDS = ["year_id", "title", "description", "udas", "unplaced_topics", "notes"]
MAX_SECTION_CHARS = 6000
MAX_CHILDREN_WITH_TEXT = 8
MAX_CATALOG_EXCERPT_CHARS = 400
AI_FRAME_TIMEOUT_SECONDS = 120
AI_COURSE_PLAN_TIMEOUT_SECONDS = 240
COMPACT_TEXT_CHARS = 1200
MAX_SUBMISSION_FILE_BYTES = 512 * 1024


def course_storage() -> thebitlab_storage.JsonCourseStorage:
    """Return the JSON storage adapter for course designs and calendars."""

    return thebitlab_storage.JsonCourseStorage(ROOT, DEFAULT_SOURCES)


def course_service() -> thebitlab_services.CourseService:
    """Return the application service for course designs and calendars."""

    return thebitlab_services.CourseService(course_storage())


def assignment_storage() -> thebitlab_storage.JsonAssignmentStorage:
    """Return the JSON storage adapter for activities and assignment reports."""

    return thebitlab_storage.JsonAssignmentStorage(ROOT, TEACHER_REPORTS_DIR, ACTIVITY_DIRS)


def assignment_service() -> thebitlab_services.AssignmentService:
    """Return the application service for assignment dashboard data."""

    return thebitlab_services.AssignmentService(assignment_storage())


def github_anchor(title: str, seen: dict[str, int]) -> str:
    """Return a GitHub-like Markdown anchor for a heading title."""

    plain = TAG_RE.sub("", title).strip().lower()
    plain = plain.replace("`", "")
    plain = PUNCT_RE.sub("", plain)
    base = SPACE_RE.sub("-", plain).strip("-") or "section"
    count = seen.get(base, 0)
    seen[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count}"


def read_design() -> dict:
    """Load the course design JSON file, creating a minimal shape if missing."""

    return course_service().read_design()


def write_design(payload: dict) -> None:
    """Persist the course design JSON with stable formatting."""

    course_service().write_design(payload)


def generate_course_plan_md(payload: dict) -> dict:
    """Persist the current design and regenerate doc/PERCORSO_DIDATTICO.md."""

    write_design(payload)
    command = [sys.executable, str(ROOT / "scripts" / "generate_course_plan.py")]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "Errore sconosciuto durante la generazione del percorso MD.").strip()
        raise RuntimeError(detail)
    return {
        "ok": True,
        "design_path": str(DESIGN_PATH.relative_to(ROOT)),
        "markdown_path": str(COURSE_PLAN_MD_PATH.relative_to(ROOT)),
        "message": (completed.stdout or "").strip(),
    }


def update_readme_frames(payload: dict) -> dict:
    """Persist the current design and update README.md didactic-frame blocks."""

    write_design(payload)
    command = [sys.executable, str(ROOT / "scripts" / "update_course_frames.py"), "--target", str(README_PATH)]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "Errore sconosciuto durante l'aggiornamento del README.").strip()
        raise RuntimeError(detail)
    return {
        "ok": True,
        "design_path": str(DESIGN_PATH.relative_to(ROOT)),
        "readme_path": str(README_PATH.relative_to(ROOT)),
        "message": (completed.stdout or "").strip(),
    }


def safe_design_name(name: str) -> str:
    """Validate a saved course-design filename."""

    return course_service().safe_design_name(name)


def saved_design_path(name: str) -> Path:
    """Return the safe path for a saved course design."""

    return course_service().saved_design_path(name)


def school_calendar_path(name: str) -> Path:
    """Return the safe path for a saved school calendar."""

    return course_service().school_calendar_path(name)


def safe_teacher_report_path(name: str) -> Path:
    """Return a safe teacher-report path below teacher-reports."""

    return assignment_service().safe_teacher_report_path(name)


def list_saved_designs() -> list[dict]:
    """List saved course designs stored in doc/course_designs."""

    return course_service().list_saved_designs()


def read_saved_design(name: str) -> dict:
    """Read a saved course design by filename."""

    return course_service().read_saved_design(name)


def write_saved_design(name: str, payload: dict) -> dict:
    """Persist a named course design in the archive folder."""

    return course_service().write_saved_design(name, payload)


def delete_saved_design(name: str, delete_calendars: bool = False, calendars: list[str] | None = None) -> dict:
    """Delete an archived course design and, optionally, its linked calendars."""

    return course_service().delete_saved_design(name, delete_calendars, calendars)


def list_school_calendars() -> list[dict]:
    """List saved school calendars stored in doc/calendars."""

    return course_service().list_school_calendars()


def list_assignment_reports() -> list[dict]:
    """List assignment tracking reports stored in teacher-reports."""

    return assignment_service().list_assignment_reports()


def read_assignment_report(name: str) -> dict:
    """Read one assignment tracking report from teacher-reports."""

    return assignment_service().read_assignment_report(name)


def review_assignment_ai_feedback(name: str, student_id: str, decision: str) -> dict:
    """Apply a teacher review decision to draft AI feedback in a report."""

    storage = assignment_storage()
    register = storage.read_assignment_report(name)
    updated = manual_ai_feedback.review_feedback_in_register(register, student_id, decision)
    return storage.write_assignment_report(name, updated)


def assignment_overview() -> list[dict]:
    """Return one row per student/activity across all saved teacher reports."""

    return assignment_service().assignment_overview()


def list_activities() -> list[dict]:
    """List available activity JSON files for the assignment dashboard."""

    return assignment_service().list_activities()


def resolve_submission_file_path(student: dict, file_path: str) -> Path:
    """Resolve a submitted file path while keeping reads inside the student repo."""

    repo = Path(str(student.get("repo", "")).strip())
    if not str(repo):
        raise ValueError("Repository studente mancante nel registro.")
    repo_path = repo if repo.is_absolute() else (ROOT / repo).resolve()
    raw_path = Path(str(file_path).strip())
    if not str(raw_path):
        raise ValueError("File consegna non indicato.")
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path.resolve())
    else:
        candidates.append((ROOT / raw_path).resolve())
        candidates.append((repo_path / raw_path).resolve())
    for candidate in candidates:
        try:
            candidate.relative_to(repo_path)
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"File consegna non trovato o non consentito: {file_path}")


def read_submission_file(payload: dict) -> dict:
    """Read one file from a submitted assignment for the teacher dashboard."""

    report = read_assignment_report(payload.get("report_name", ""))
    student_name = str(payload.get("student", "")).strip()
    student = next((entry for entry in report.get("students", []) if entry.get("student") == student_name), None)
    if student is None:
        raise FileNotFoundError(f"Studente non trovato nel registro: {student_name}")
    path = resolve_submission_file_path(student, payload.get("path", ""))
    size = path.stat().st_size
    if size > MAX_SUBMISSION_FILE_BYTES:
        raise ValueError("File troppo grande per l'anteprima nella dashboard.")
    text = path.read_text(encoding="utf-8-sig")
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path),
        "name": path.name,
        "size": size,
        "content": text,
    }


def resolve_local_path(path_value: str, field_name: str) -> Path:
    """Resolve a user-provided local path from the repository root."""

    raw_path = Path(str(path_value).strip())
    if not str(raw_path):
        raise ValueError(f"{field_name} obbligatorio.")
    return raw_path if raw_path.is_absolute() else (ROOT / raw_path).resolve()


def read_targets_from_text(targets_text: str) -> list[track_assignments.TrackingTarget]:
    """Build tracking targets from one path per line."""

    targets = []
    for raw_line in targets_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        target_path = resolve_local_path(line, "target")
        targets.append(track_assignments.TrackingTarget(student=target_path.name, repo=str(target_path), path=target_path))
    if not targets:
        raise ValueError("Inserisci almeno un repository studente nei target.")
    return targets


def generate_assignment_report(payload: dict) -> dict:
    """Generate and persist an assignment tracking report from the local GUI."""

    activity_path = resolve_local_path(payload.get("activity_path", ""), "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    targets = read_targets_from_text(str(payload.get("targets_text", "")))
    output_path = safe_teacher_report_path(payload.get("output_name", ""))
    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=targets,
        assigned_at=payload.get("assigned_at") or None,
        due_at=payload.get("due_at") or None,
        now=payload.get("now") or None,
        class_id=payload.get("class_id") or None,
        class_label=payload.get("class_label") or None,
        github_team=payload.get("github_team") or None,
    )
    track_assignments.write_tracking_index(index, output_path)
    return {
        "ok": True,
        "report": index,
        "saved": {
            "name": str(output_path.relative_to(TEACHER_REPORTS_DIR)).replace("\\", "/"),
            "path": str(output_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "reports": list_assignment_reports(),
    }


def read_school_calendar(name: str) -> dict:
    """Read a saved school calendar by filename."""

    return course_service().read_school_calendar(name)


def write_school_calendar(name: str, payload: dict) -> dict:
    """Persist a named school calendar in the calendars folder."""

    return course_service().write_school_calendar(name, payload)


def read_secret_env() -> dict[str, str]:
    """Read local secret values from .secrets/ai.secret."""

    values: dict[str, str] = {}
    if not AI_SECRET_PATH.is_file():
        return values
    for line in AI_SECRET_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def secret_value(key: str) -> str:
    """Return a secret from environment first, then local secret file."""

    return os.environ.get(key, "") or read_secret_env().get(key, "")


def secret_int_value(key: str, default: int) -> int:
    """Return an integer setting from environment or local secret file."""

    raw_value = secret_value(key)
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def parse_ai_providers_yaml() -> dict:
    """Parse the small YAML subset used by config/ai_providers.yaml."""

    if not AI_PROVIDERS_PATH.is_file():
        return default_ai_provider_config()
    providers: dict[str, dict] = {}
    current_provider: str | None = None
    current_model: dict | None = None
    in_models = False
    for raw in AI_PROVIDERS_PATH.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.strip().startswith("#") or raw.strip() == "providers:":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 2 and line.endswith(":"):
            current_provider = line[:-1]
            providers[current_provider] = {"id": current_provider, "models": []}
            in_models = False
            current_model = None
            continue
        if not current_provider:
            continue
        if indent == 4 and line == "models:":
            in_models = True
            continue
        if in_models and indent == 6 and line.startswith("- "):
            current_model = {}
            providers[current_provider]["models"].append(current_model)
            key, value = line[2:].split(":", 1)
            current_model[key.strip()] = value.strip()
            continue
        if in_models and indent == 8 and current_model and ":" in line:
            key, value = line.split(":", 1)
            current_model[key.strip()] = value.strip()
            continue
        if indent == 4 and ":" in line:
            key, value = line.split(":", 1)
            providers[current_provider][key.strip()] = value.strip()
    return {"providers": providers}


def default_ai_provider_config() -> dict:
    """Return built-in AI provider config when YAML is missing."""

    return {
        "providers": {
            "openai": {
                "id": "openai",
                "label": "OpenAI",
                "secret_key": "OPENAI_API_KEY",
                "default_model": "gpt-5.5",
                "billing_note": "OpenAI API usa quota/billing API separati da ChatGPT Free/Plus.",
                "models": [{"id": "gpt-5.5", "label": "GPT-5.5", "tier": "paid"}],
            },
            "gemini": {
                "id": "gemini",
                "label": "Gemini",
                "secret_key": "GEMINI_API_KEY",
                "default_model": "gemini-2.5-flash",
                "billing_note": "Gemini puo avere free tier su Google AI Studio, ma quota e limiti dipendono dall'account.",
                "models": [{"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash", "tier": "free-or-low-cost"}],
            },
        }
    }


def extract_headings() -> list[dict]:
    """Extract headings from configured Markdown sources."""

    design = read_design()
    sources = design.get("source_files") or DEFAULT_SOURCES
    headings: list[dict] = []
    for source in sources:
        path = (ROOT / source).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            continue
        if not path.is_file():
            continue
        seen: dict[str, int] = {}
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            match = HEADING_RE.match(line)
            if not match:
                continue
            title = match.group(2).strip()
            if not title or title.startswith("0 \""):
                continue
            anchor = github_anchor(title, seen)
            headings.append(
                {
                    "id": f"{source}#{anchor}",
                    "source": source,
                    "level": len(match.group(1)),
                    "title": TAG_RE.sub("", title).strip(),
                    "anchor": anchor,
                    "href": f"../{source}#{anchor}",
                    "line": lineno,
                }
            )
    return headings


def github_blob_url(source: str, anchor: str = "") -> str:
    """Return a GitHub URL for a source file and optional anchor."""

    base = f"https://github.com/TheBitPoets/2cornot2c/blob/main/{source}"
    return f"{base}#{anchor}" if anchor else base


def section_text(source: str, line: int | str, level: int | str) -> str:
    """Extract local Markdown text for one heading section."""

    try:
        start_line = int(line)
        start_level = int(level)
    except (TypeError, ValueError):
        return ""
    path = (ROOT / source).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return ""
    if not path.is_file():
        return ""

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if start_line < 1 or start_line > len(lines):
        return ""

    section: list[str] = []
    for current in lines[start_line:]:
        match = HEADING_RE.match(current)
        if match and len(match.group(1)) <= start_level:
            break
        section.append(current)
    text = "\n".join(section).strip()
    if len(text) > MAX_SECTION_CHARS:
        return text[:MAX_SECTION_CHARS].rstrip() + "\n\n[contenuto tagliato per limite di contesto]"
    return text


def section_excerpt(heading: dict) -> str:
    """Return a short local excerpt for course-plan generation."""

    text = section_text(heading.get("source", ""), heading.get("line", ""), heading.get("level", ""))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_CATALOG_EXCERPT_CHARS:
        return text[:MAX_CATALOG_EXCERPT_CHARS].rstrip() + "..."
    return text


def heading_catalog_tree() -> list[dict]:
    """Return all available headings as a tree with compact excerpts."""

    roots: list[dict] = []
    stack: list[dict] = []
    for heading in extract_headings():
        node = {
            "id": heading["id"],
            "title": heading["title"],
            "source": heading["source"],
            "level": heading["level"],
            "href": heading["href"],
            "excerpt": section_excerpt(heading),
            "children": [],
        }
        while stack and heading["level"] <= stack[-1]["level"]:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            roots.append(node)
        stack.append(node)
    prune_empty_children(roots)
    return roots


def prune_empty_children(items: list[dict]) -> None:
    """Remove empty children arrays recursively."""

    for item in items:
        prune_empty_children(item.get("children", []))
        if not item.get("children"):
            item.pop("children", None)


def topic_summary(item: dict, include_text: bool = False, child_text_budget: int = 0) -> dict:
    """Return a compact recursive topic summary for the AI prompt."""

    anchor = str(item.get("href", "")).split("#", 1)[-1] if "#" in str(item.get("href", "")) else ""
    summary = {
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "level": item.get("level", ""),
        "href": item.get("href", ""),
        "github_url": github_blob_url(item.get("source", ""), anchor),
        "children": [
            topic_summary(child, include_text=include_text and index < child_text_budget)
            for index, child in enumerate(item.get("children", []))
        ],
    }
    if include_text:
        summary["text"] = section_text(item.get("source", ""), item.get("line", ""), item.get("level", ""))
    return summary


def heading_by_id() -> dict[str, dict]:
    """Return available headings indexed by stable id."""

    return {heading["id"]: heading for heading in extract_headings()}


def item_from_heading_id(heading_id: str, headings: list[dict]) -> dict | None:
    """Build a board item from a heading id, preserving its subtree."""

    index = next((i for i, heading in enumerate(headings) if heading["id"] == heading_id), None)
    if index is None:
        return None
    heading = headings[index]
    item = board_item_from_heading(heading)
    roots: list[dict] = []
    stack: list[dict] = [{"level": heading["level"], "children": roots}]
    for child in headings[index + 1:]:
        if child["source"] != heading["source"] or child["level"] <= heading["level"]:
            break
        child_item = board_item_from_heading(child)
        child_item["children"] = []
        while stack and child["level"] <= stack[-1]["level"]:
            stack.pop()
        stack[-1]["children"].append(child_item)
        stack.append({"level": child["level"], "children": child_item["children"]})
    prune_empty_children(roots)
    if roots:
        item["children"] = roots
    return item


def board_item_from_heading(heading: dict) -> dict:
    """Return the JSON item shape consumed by the course board."""

    return {
        "id": heading["id"],
        "title": heading["title"],
        "source": heading["source"],
        "href": heading["href"],
        "level": heading["level"],
        "line": heading["line"],
        "frame": {"status": "todo"},
    }


def compact_design(design: dict) -> dict:
    """Return the full course structure without verbose frame text."""

    return {
        "years": [
            {
                "id": year.get("id", ""),
                "title": year.get("title", ""),
                "description": year.get("description", ""),
                "udas": [
                    {
                        "id": uda.get("id", ""),
                        "title": uda.get("title", ""),
                        "path": uda.get("path", ""),
                        "weeks": uda.get("weeks", ""),
                        "items": [topic_summary(item) for item in uda.get("items", [])],
                    }
                    for uda in year.get("udas", [])
                ],
            }
            for year in design.get("years", [])
        ]
    }


def target_context(design: dict, year_id: str, uda_id: str, item_id: str) -> dict:
    """Collect the target item plus local before/after context inside its UDA."""

    for year in design.get("years", []):
        if year.get("id") != year_id:
            continue
        for uda in year.get("udas", []):
            if uda.get("id") != uda_id:
                continue
            found = find_item_context(uda.get("items", []), item_id)
            if found:
                index, siblings, item = found
                previous_topics = siblings[max(0, index - 2):index]
                next_topics = siblings[index + 1:index + 3]
                return {
                    "year": {key: year.get(key, "") for key in ["id", "title", "description"]},
                    "uda": {key: uda.get(key, "") for key in ["id", "title", "path", "weeks"]},
                    "position": topic_position(index, siblings, item),
                    "previous_topics": [
                        topic_summary(candidate, include_text=True)
                        for candidate in previous_topics
                    ],
                    "target_topic": topic_summary(
                        item,
                        include_text=True,
                        child_text_budget=MAX_CHILDREN_WITH_TEXT,
                    ),
                    "next_topics": [
                        topic_summary(candidate, include_text=True)
                        for candidate in next_topics
                    ],
                }
    raise ValueError("Argomento non trovato nel percorso didattico corrente.")


def find_item_context(items: list[dict], item_id: str) -> tuple[int, list[dict], dict] | None:
    """Find an item at any nesting level, returning its index and siblings."""

    for index, item in enumerate(items):
        if item.get("id") == item_id:
            return index, items, item
        found = find_item_context(item.get("children", []), item_id)
        if found:
            return found
    return None


def topic_position(index: int, items: list[dict], item: dict) -> dict:
    """Describe how much local didactic context surrounds a topic."""

    previous_count = index
    next_count = max(0, len(items) - index - 1)
    has_children = bool(item.get("children"))
    if previous_count and next_count:
        quality = "good"
    elif previous_count or next_count or has_children:
        quality = "medium"
    else:
        quality = "weak"
    return {
        "index_in_uda": index + 1,
        "total_items_in_uda": len(items),
        "previous_topics_available": previous_count,
        "next_topics_available": next_count,
        "has_subtopics": has_children,
        "context_quality": quality,
    }


def didactic_frame_schema_openai() -> dict:
    """Return the JSON Schema shape expected from OpenAI."""

    return {
        "type": "object",
        "additionalProperties": False,
        "required": AI_FRAME_FIELDS,
        "properties": {field: {"type": "string"} for field in AI_FRAME_FIELDS},
    }


def didactic_frame_schema_gemini() -> dict:
    """Return the JSON Schema shape expected from Gemini generateContent."""

    return {
        "type": "OBJECT",
        "required": AI_FRAME_FIELDS,
        "properties": {field: {"type": "STRING"} for field in AI_FRAME_FIELDS},
    }


def proofread_schema_openai() -> dict:
    """Return the JSON schema for AI proofreading responses."""

    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "corrected_text": {"type": "string"},
            "changes": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
        },
        "required": ["corrected_text", "changes", "notes"],
    }


def course_plan_schema_openai() -> dict:
    """Return the JSON Schema expected from OpenAI for a course proposal."""

    return {
        "type": "object",
        "additionalProperties": False,
        "required": COURSE_PLAN_REQUIRED_FIELDS,
        "properties": {
            "year_id": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "udas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "title", "path", "weeks", "items"],
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "path": {"type": "string"},
                        "weeks": {"type": "string"},
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "unplaced_topics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "reason"],
                    "properties": {
                        "id": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                },
            },
            "notes": {"type": "string"},
        },
    }


def course_plan_schema_gemini() -> dict:
    """Return the JSON Schema expected from Gemini for a course proposal."""

    return {
        "type": "OBJECT",
        "required": COURSE_PLAN_REQUIRED_FIELDS,
        "properties": {
            "year_id": {"type": "STRING"},
            "title": {"type": "STRING"},
            "description": {"type": "STRING"},
            "udas": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "required": ["id", "title", "path", "weeks", "items"],
                    "properties": {
                        "id": {"type": "STRING"},
                        "title": {"type": "STRING"},
                        "path": {"type": "STRING"},
                        "weeks": {"type": "STRING"},
                        "items": {"type": "ARRAY", "items": {"type": "STRING"}},
                    },
                },
            },
            "unplaced_topics": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "required": ["id", "reason"],
                    "properties": {
                        "id": {"type": "STRING"},
                        "reason": {"type": "STRING"},
                    },
                },
            },
            "notes": {"type": "STRING"},
        },
    }


def didactic_frame_system_prompt() -> str:
    """Return the shared provider-independent instruction."""

    return (
        "Sei un docente di TPSI e programmazione C. "
        "Compila una cornice didattica in italiano per un argomento del corso. "
        "Usa prima di tutto il testo locale dei paragrafi forniti nel payload. "
        "Sii concreto, fluido e didattico; non inventare link; non perdere il contenuto tecnico. "
        "Se la qualita del contesto e weak, resta prudente e non inventare una progressione didattica. "
        "Se la qualita del contesto e medium o good, collega l'argomento ai paragrafi precedenti e successivi."
    )


def proofread_system_prompt() -> str:
    """Return the provider-independent instruction for grammar proofreading."""

    return (
        "Sei un revisore grammaticale italiano per materiali didattici di programmazione C. "
        "Correggi solo ortografia, grammatica, accenti, punteggiatura minima e refusi. "
        "Devi capire dal contesto se serve 'e' oppure 'è'. "
        "Non cambiare il contenuto tecnico, non semplificare concetti, non aggiungere esempi e non rimuovere termini tecnici. "
        "Preserva la formattazione leggera: **grassetto**, _corsivo_, `inline code`, elenchi puntati e numerati. "
        "Restituisci solo JSON con corrected_text, changes e notes."
    )


def course_plan_system_prompt() -> str:
    """Return the provider-independent instruction for course-plan generation."""

    return (
        "Sei un docente esperto di progettazione didattica per discipline tecniche e informatiche. "
        "Devi costruire una proposta di percorso annuale usando solo gli id degli argomenti disponibili. "
        "Rispetta il brief del docente, la progressione didattica, il numero di settimane, le ore disponibili e gli obiettivi. "
        "Il campo brief.description rappresenta gli obiettivi e i criteri principali di selezione: usalo per decidere quali paragrafi e sottoparagrafi includere, escludere o lasciare non assegnati. "
        "Non inventare id. Non duplicare argomenti nello stesso anno. "
        "Se un argomento non e coerente con il brief, lascialo tra gli unplaced_topics spiegando il motivo. "
        "Restituisci solo JSON valido secondo lo schema richiesto."
    )


def normalize_frame(result: dict) -> dict:
    """Keep only the expected didactic-frame fields as stripped strings."""

    if isinstance(result.get("frame"), dict):
        result = result["frame"]
    frame = {field: str(result.get(field, "")).strip() for field in AI_FRAME_FIELDS}
    if not any(frame.values()):
        raise RuntimeError(
            "Il provider AI ha risposto correttamente, ma non ha compilato nessun campo della cornice didattica. "
            "Prova un modello diverso o un provider diverso."
        )
    return frame


def normalize_proofread(result: dict, original_text: str) -> dict:
    """Keep only expected proofreading fields."""

    corrected_text = str(result.get("corrected_text", "")).strip() or original_text
    changes = result.get("changes", [])
    if not isinstance(changes, list):
        changes = [changes]
    return {
        "corrected_text": corrected_text,
        "changes": [str(change).strip() for change in changes if str(change).strip()],
        "notes": str(result.get("notes", "")).strip(),
    }


def normalize_course_plan(raw: dict, design: dict, year_id: str) -> dict:
    """Validate a raw AI proposal and hydrate item ids into board items."""

    headings = extract_headings()
    valid_ids = {heading["id"] for heading in headings}
    year = next((candidate for candidate in design.get("years", []) if candidate.get("id") == year_id), {})
    used: set[str] = set()
    hydrated_udas: list[dict] = []

    for index, uda in enumerate(raw.get("udas", []), start=1):
        hydrated_items: list[dict] = []
        for heading_id in uda.get("items", []):
            if heading_id not in valid_ids or heading_id in used:
                continue
            item = item_from_heading_id(heading_id, headings)
            if item:
                hydrated_items.append(item)
                used.update(collect_item_ids(item))
        hydrated_udas.append(
            {
                "id": str(uda.get("id") or f"uda-{index}"),
                "title": str(uda.get("title") or f"UDA {index}"),
                "path": str(uda.get("path") or "Da definire"),
                "weeks": str(uda.get("weeks") or "?"),
                "items": hydrated_items,
            }
        )

    unplaced = []
    for topic in raw.get("unplaced_topics", []):
        heading_id = str(topic.get("id", ""))
        if heading_id in valid_ids:
            unplaced.append({"id": heading_id, "reason": str(topic.get("reason", ""))})

    return {
        "year_id": year_id,
        "title": str(raw.get("title") or year.get("title", "")),
        "description": str(raw.get("description") or year.get("description", "")),
        "udas": hydrated_udas,
        "unplaced_topics": unplaced,
        "notes": str(raw.get("notes", "")),
        "stats": {
            "assigned_topics": sum(count_item_tree(item) for uda in hydrated_udas for item in uda["items"]),
            "root_topics": sum(len(uda["items"]) for uda in hydrated_udas),
        },
    }


def collect_item_ids(item: dict) -> set[str]:
    """Collect ids from a board item subtree."""

    ids = {item.get("id", "")}
    for child in item.get("children", []):
        ids.update(collect_item_ids(child))
    return {item_id for item_id in ids if item_id}


def count_item_tree(item: dict) -> int:
    """Count a board item subtree."""

    return 1 + sum(count_item_tree(child) for child in item.get("children", []))


def call_openai_didactic_frame(payload: dict) -> dict:
    """Ask OpenAI to draft didactic-frame fields for one course topic."""

    api_key = secret_value("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENAI_API_KEY prima di usare AI assisted.")

    model = active_ai_model()
    body = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": didactic_frame_system_prompt(),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(payload, ensure_ascii=False, indent=2),
                    }
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "didactic_frame",
                "schema": didactic_frame_schema_openai(),
                "strict": True,
            }
        },
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_FRAME_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore OpenAI API {error.code}: {detail}") from error

    output_text = data.get("output_text")
    if not output_text:
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    output_text = content.get("text")
                    break
            if output_text:
                break
    if not output_text:
        raise RuntimeError("La risposta AI non contiene testo utilizzabile.")

    result = json.loads(output_text)
    return normalize_frame(result)


def call_gemini_didactic_frame(payload: dict) -> dict:
    """Ask Gemini to draft didactic-frame fields for one course topic."""

    api_key = secret_value("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GEMINI_API_KEY prima di usare AI assisted con Gemini.")

    model = active_ai_model()
    body = {
        "systemInstruction": {
            "parts": [{"text": didactic_frame_system_prompt()}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(gemini_frame_payload(payload), ensure_ascii=False, indent=2)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": didactic_frame_schema_gemini(),
        },
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_FRAME_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore Gemini API {error.code}: {detail}") from error

    try:
        output_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise RuntimeError("La risposta Gemini non contiene testo utilizzabile.") from error

    return normalize_frame(json.loads(output_text))


def gemini_frame_payload(payload: dict) -> dict:
    """Use compact Gemini context only when explicitly configured."""

    if secret_value("GEMINI_COMPACT_TEXT_CHARS"):
        return compact_frame_payload(payload)
    return payload


def call_chat_completions_json(provider_name: str, url: str, api_key: str, model: str, system_prompt: str, payload: dict) -> dict:
    """Call an OpenAI-compatible chat completions endpoint and parse JSON content."""

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "2cornot2c-course-board/1.0",
        "Connection": "close",
    }
    if provider_name == "OpenRouter":
        headers["HTTP-Referer"] = "https://github.com/TheBitPoets/2cornot2c"
        headers["X-Title"] = "2cornot2c Course Design Board"
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_COURSE_PLAN_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore {provider_name} API {error.code}: {detail}") from error
    try:
        return parse_json_object(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, json.JSONDecodeError) as error:
        raise RuntimeError(f"La risposta {provider_name} non contiene JSON utilizzabile.") from error


def parse_json_object(text: str) -> dict:
    """Parse a JSON object, tolerating markdown fences around it."""

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def compact_frame_payload(payload: dict) -> dict:
    """Reduce frame-generation context for providers with strict token limits."""

    target = payload.get("target", {})
    return {
        "course": {
            "years": [
                {
                    "title": year.get("title", ""),
                    "description": year.get("description", ""),
                    "udas": [
                        {
                            "title": uda.get("title", ""),
                            "path": uda.get("path", ""),
                            "weeks": uda.get("weeks", ""),
                        }
                        for uda in year.get("udas", [])
                    ],
                }
                for year in payload.get("course", {}).get("years", [])
            ]
        },
        "target": {
            "year": target.get("year", {}),
            "uda": target.get("uda", {}),
            "position": target.get("position", {}),
            "previous_topics": [compact_topic(topic, include_text=False) for topic in target.get("previous_topics", [])],
            "target_topic": compact_topic(target.get("target_topic", {}), include_text=True),
            "next_topics": [compact_topic(topic, include_text=False) for topic in target.get("next_topics", [])],
        },
        "context_mode": "compact",
    }


def compact_topic(topic: dict, include_text: bool) -> dict:
    """Return a compact topic with optional truncated text and child titles."""

    text_limit = secret_int_value(f"{ACTIVE_AI_PROVIDER.upper()}_COMPACT_TEXT_CHARS", COMPACT_TEXT_CHARS)
    compact = {
        "title": topic.get("title", ""),
        "source": topic.get("source", ""),
        "level": topic.get("level", ""),
        "href": topic.get("href", ""),
        "children": [
            {
                "title": child.get("title", ""),
                "source": child.get("source", ""),
                "level": child.get("level", ""),
            }
            for child in topic.get("children", [])
        ],
    }
    if include_text:
        text = str(topic.get("text", ""))
        compact["text"] = text[:text_limit].rstrip()
        if len(text) > text_limit:
            compact["text"] += "\n[contenuto tagliato per provider con limite token]"
    return compact


def call_groq_didactic_frame(payload: dict) -> dict:
    """Ask Groq to draft didactic-frame fields."""

    api_key = secret_value("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GROQ_API_KEY prima di usare AI assisted con Groq.")
    result = call_chat_completions_json(
        "Groq",
        "https://api.groq.com/openai/v1/chat/completions",
        api_key,
        active_ai_model(),
        didactic_frame_system_prompt() + " Restituisci solo JSON con questi campi top-level: context, prerequisites, objectives, recall, preview, next_step, references.",
        compact_frame_payload(payload),
    )
    return normalize_frame(result)


def call_openrouter_didactic_frame(payload: dict) -> dict:
    """Ask OpenRouter to draft didactic-frame fields."""

    api_key = secret_value("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENROUTER_API_KEY prima di usare AI assisted con OpenRouter.")
    result = call_chat_completions_json(
        "OpenRouter",
        "https://openrouter.ai/api/v1/chat/completions",
        api_key,
        active_ai_model(),
        didactic_frame_system_prompt() + " Restituisci solo JSON con questi campi top-level: context, prerequisites, objectives, recall, preview, next_step, references.",
        compact_frame_payload(payload),
    )
    return normalize_frame(result)


def call_ai_didactic_frame(payload: dict) -> dict:
    """Route didactic-frame generation to the configured AI provider."""

    provider = ACTIVE_AI_PROVIDER
    if provider == "openai":
        return call_openai_didactic_frame(payload)
    if provider == "gemini":
        return call_gemini_didactic_frame(payload)
    if provider == "groq":
        return call_groq_didactic_frame(payload)
    if provider == "openrouter":
        return call_openrouter_didactic_frame(payload)
    raise RuntimeError(f"Provider AI non supportato: {provider}. Usa un provider dichiarato in config/ai_providers.yaml.")


def call_openai_proofread(text: str) -> dict:
    """Ask OpenAI to proofread one didactic-frame field."""

    api_key = secret_value("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENAI_API_KEY prima di usare AI grammatica.")
    body = {
        "model": active_ai_model(),
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": proofread_system_prompt()}]},
            {"role": "user", "content": [{"type": "input_text", "text": json.dumps({"text": text}, ensure_ascii=False)}]},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "proofread",
                "schema": proofread_schema_openai(),
                "strict": True,
            }
        },
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_FRAME_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore OpenAI API {error.code}: {detail}") from error
    output_text = data.get("output_text")
    if not output_text:
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    output_text = content.get("text")
                    break
            if output_text:
                break
    if not output_text:
        raise RuntimeError("La risposta OpenAI non contiene testo utilizzabile.")
    return normalize_proofread(json.loads(output_text), text)


def call_gemini_proofread(text: str) -> dict:
    """Ask Gemini to proofread one didactic-frame field."""

    api_key = secret_value("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GEMINI_API_KEY prima di usare AI grammatica con Gemini.")
    body = {
        "systemInstruction": {"parts": [{"text": proofread_system_prompt()}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps({"text": text}, ensure_ascii=False)}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{active_ai_model()}:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_FRAME_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore Gemini API {error.code}: {detail}") from error
    try:
        output_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise RuntimeError("La risposta Gemini non contiene testo utilizzabile.") from error
    return normalize_proofread(parse_json_object(output_text), text)


def call_groq_proofread(text: str) -> dict:
    """Ask Groq to proofread one didactic-frame field."""

    api_key = secret_value("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GROQ_API_KEY prima di usare AI grammatica con Groq.")
    result = call_chat_completions_json(
        "Groq",
        "https://api.groq.com/openai/v1/chat/completions",
        api_key,
        active_ai_model(),
        proofread_system_prompt(),
        {"text": text},
    )
    return normalize_proofread(result, text)


def call_openrouter_proofread(text: str) -> dict:
    """Ask OpenRouter to proofread one didactic-frame field."""

    api_key = secret_value("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENROUTER_API_KEY prima di usare AI grammatica con OpenRouter.")
    result = call_chat_completions_json(
        "OpenRouter",
        "https://openrouter.ai/api/v1/chat/completions",
        api_key,
        active_ai_model(),
        proofread_system_prompt(),
        {"text": text},
    )
    return normalize_proofread(result, text)


def call_ai_proofread(text: str) -> dict:
    """Route proofreading to the configured AI provider."""

    provider = ACTIVE_AI_PROVIDER
    if provider == "openai":
        return call_openai_proofread(text)
    if provider == "gemini":
        return call_gemini_proofread(text)
    if provider == "groq":
        return call_groq_proofread(text)
    if provider == "openrouter":
        return call_openrouter_proofread(text)
    raise RuntimeError(f"Provider AI non supportato: {provider}.")


def call_openai_course_plan(payload: dict) -> dict:
    """Ask OpenAI to draft an annual course plan."""

    api_key = secret_value("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENAI_API_KEY prima di usare AI assisted percorso.")
    model = active_ai_model()
    body = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": course_plan_system_prompt()}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "course_plan_proposal",
                "schema": course_plan_schema_openai(),
                "strict": True,
            }
        },
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_COURSE_PLAN_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore OpenAI API {error.code}: {detail}") from error
    output_text = data.get("output_text")
    if not output_text:
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    output_text = content.get("text")
                    break
            if output_text:
                break
    if not output_text:
        raise RuntimeError("La risposta AI non contiene una proposta utilizzabile.")
    return json.loads(output_text)


def call_gemini_course_plan(payload: dict) -> dict:
    """Ask Gemini to draft an annual course plan."""

    api_key = secret_value("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GEMINI_API_KEY prima di usare AI assisted percorso con Gemini.")
    model = active_ai_model()
    body = {
        "systemInstruction": {"parts": [{"text": course_plan_system_prompt()}]},
        "contents": [{"role": "user", "parts": [{"text": json.dumps(payload, ensure_ascii=False, indent=2)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": course_plan_schema_gemini(),
        },
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AI_COURSE_PLAN_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore Gemini API {error.code}: {detail}") from error
    try:
        output_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise RuntimeError("La risposta Gemini non contiene una proposta utilizzabile.") from error
    return json.loads(output_text)


def call_groq_course_plan(payload: dict) -> dict:
    """Ask Groq to draft an annual course plan."""

    api_key = secret_value("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GROQ_API_KEY prima di usare AI assisted percorso con Groq.")
    return call_chat_completions_json(
        "Groq",
        "https://api.groq.com/openai/v1/chat/completions",
        api_key,
        active_ai_model(),
        course_plan_system_prompt(),
        payload,
    )


def call_openrouter_course_plan(payload: dict) -> dict:
    """Ask OpenRouter to draft an annual course plan."""

    api_key = secret_value("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENROUTER_API_KEY prima di usare AI assisted percorso con OpenRouter.")
    return call_chat_completions_json(
        "OpenRouter",
        "https://openrouter.ai/api/v1/chat/completions",
        api_key,
        active_ai_model(),
        course_plan_system_prompt(),
        payload,
    )


def call_ai_course_plan(payload: dict) -> dict:
    """Route annual course-plan generation to the configured AI provider."""

    provider = ACTIVE_AI_PROVIDER
    if provider == "openai":
        return call_openai_course_plan(payload)
    if provider == "gemini":
        return call_gemini_course_plan(payload)
    if provider == "groq":
        return call_groq_course_plan(payload)
    if provider == "openrouter":
        return call_openrouter_course_plan(payload)
    raise RuntimeError(f"Provider AI non supportato: {provider}. Usa un provider dichiarato in config/ai_providers.yaml.")


def ai_config() -> dict:
    """Return safe AI provider configuration for the board UI."""

    providers = ai_providers()
    active = providers.get(ACTIVE_AI_PROVIDER) or providers["openai"]
    return {
        "provider": active["id"],
        "model": active_ai_model(),
        "api_key_configured": active["api_key_configured"],
        "billing_note": active["billing_note"],
        "providers": list(providers.values()),
        "secret_status": ai_secret_status(providers),
    }


def diagnostic_path(path: Path) -> str:
    """Return a stable diagnostic path without exposing host-specific separators."""

    display_path = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    return str(display_path).replace("\\", "/")


def ai_secret_status(providers: dict | None = None) -> dict:
    """Return safe diagnostics about AI secrets without exposing values."""

    safe_providers = providers or ai_providers()
    secret_keys = sorted(
        {
            provider.get("secret_key", "")
            for provider in parse_ai_providers_yaml()["providers"].values()
            if provider.get("secret_key", "")
        }
    )
    return {
        "path": diagnostic_path(AI_SECRET_PATH),
        "exists": AI_SECRET_PATH.is_file(),
        "legacy_path": diagnostic_path(LEGACY_AI_SECRET_PATH),
        "legacy_exists": LEGACY_AI_SECRET_PATH.is_file(),
        "configured_keys": {
            key: bool(secret_value(key))
            for key in secret_keys
        },
        "configured_providers": {
            provider_id: bool(provider.get("api_key_configured"))
            for provider_id, provider in safe_providers.items()
        },
    }


def ai_providers() -> dict:
    """Return all server-supported providers with safe configuration status."""

    config = parse_ai_providers_yaml()["providers"]
    providers: dict[str, dict] = {}
    for provider_id, provider in config.items():
        secret_key = provider.get("secret_key", "")
        default_model = provider.get("default_model", "")
        env_model = os.environ.get(f"{provider_id.upper()}_MODEL", "")
        model = env_model or (ACTIVE_AI_MODEL if ACTIVE_AI_PROVIDER == provider_id else "") or default_model
        models = provider.get("models", [])
        providers[provider_id] = {
            "id": provider_id,
            "label": provider.get("label", provider_id),
            "model": model,
            "default_model": default_model,
            "api_key_configured": bool(secret_value(secret_key)),
            "billing_note": provider.get("billing_note", ""),
            "models": models,
        }
    return providers


def active_ai_model() -> str:
    """Return the currently selected model for the active provider."""

    providers = ai_providers()
    active = providers.get(ACTIVE_AI_PROVIDER) or providers["openai"]
    return ACTIVE_AI_MODEL or active.get("model") or active.get("default_model", "")


def set_ai_provider(provider: str, model: str = "") -> dict:
    """Set the active provider/model only when the server has its API key."""

    global ACTIVE_AI_PROVIDER, ACTIVE_AI_MODEL
    provider = provider.strip().lower()
    providers = ai_providers()
    if provider not in providers:
        raise RuntimeError(f"Provider AI non supportato: {provider}.")
    if not providers[provider]["api_key_configured"]:
        raise RuntimeError(f"Provider {providers[provider]['label']} non configurato: API key mancante.")
    model_ids = {candidate.get("id") for candidate in providers[provider].get("models", [])}
    selected_model = model.strip() or providers[provider].get("model") or providers[provider].get("default_model", "")
    if model_ids and selected_model not in model_ids:
        raise RuntimeError(f"Modello non supportato per {providers[provider]['label']}: {selected_model}.")
    ACTIVE_AI_PROVIDER = provider
    ACTIVE_AI_MODEL = selected_model
    return ai_config()


class CourseBoardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the local board and its JSON API."""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/headings":
            self.write_json({"headings": extract_headings()})
            return
        if parsed.path == "/api/course-design":
            self.write_json(read_design())
            return
        if parsed.path == "/api/saved-designs":
            self.write_json({"designs": list_saved_designs()})
            return
        if parsed.path == "/api/school-calendars":
            self.write_json({"calendars": list_school_calendars()})
            return
        if parsed.path == "/api/assignment-reports":
            self.write_json({"reports": list_assignment_reports()})
            return
        if parsed.path == "/api/assignment-overview":
            self.write_json({"rows": assignment_overview()})
            return
        if parsed.path == "/api/activities":
            self.write_json({"activities": list_activities()})
            return
        if parsed.path == "/api/ai-config":
            self.write_json(ai_config())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if parsed.path == "/api/course-design":
            write_design(payload)
            self.write_json({"ok": True, "path": str(DESIGN_PATH.relative_to(ROOT))})
            return
        if parsed.path == "/api/course-plan-md":
            try:
                self.write_json(generate_course_plan_md(payload.get("design", payload)))
            except Exception as error:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/readme-frames":
            try:
                self.write_json(update_readme_frames(payload.get("design", payload)))
            except Exception as error:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/saved-designs/load":
            try:
                self.write_json({"design": read_saved_design(payload.get("name", ""))})
            except Exception as error:  # noqa: BLE001
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/saved-designs/save":
            try:
                saved = write_saved_design(payload.get("name", ""), payload.get("design", {}))
                self.write_json({"ok": True, "saved": saved, "designs": list_saved_designs()})
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/saved-designs/delete":
            try:
                self.write_json(delete_saved_design(
                    payload.get("name", ""),
                    bool(payload.get("delete_calendars", False)),
                    payload.get("calendars", []),
                ))
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/school-calendars/load":
            try:
                self.write_json({"calendar": read_school_calendar(payload.get("name", ""))})
            except Exception as error:  # noqa: BLE001
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/assignment-reports/load":
            try:
                self.write_json({"report": read_assignment_report(payload.get("name", ""))})
            except Exception as error:  # noqa: BLE001
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/assignment-reports/ai-feedback/review":
            try:
                report = review_assignment_ai_feedback(
                    payload.get("name", ""),
                    payload.get("student_id", ""),
                    payload.get("decision", ""),
                )
                self.write_json({"ok": True, "report": report})
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/assignment-reports/generate":
            try:
                self.write_json(generate_assignment_report(payload))
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/assignment-submissions/read":
            try:
                self.write_json({"file": read_submission_file(payload)})
            except FileNotFoundError as error:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/school-calendars/save":
            try:
                saved = write_school_calendar(payload.get("name", ""), payload.get("calendar", {}))
                self.write_json({"ok": True, "saved": saved, "calendars": list_school_calendars()})
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/ai-config":
            try:
                self.write_json(set_ai_provider(payload.get("provider", ""), payload.get("model", "")))
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/ai-frame":
            try:
                context = {
                    "course": compact_design(payload.get("design", {})),
                    "target": target_context(
                        payload.get("design", {}),
                        payload.get("year_id", ""),
                        payload.get("uda_id", ""),
                        payload.get("item_id", ""),
                    ),
                }
                self.write_json({"frame": call_ai_didactic_frame(context)})
            except Exception as error:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/ai-proofread":
            try:
                text = str(payload.get("text", ""))
                if not text.strip():
                    raise RuntimeError("Testo vuoto: niente da correggere.")
                self.write_json(call_ai_proofread(text))
            except Exception as error:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        if parsed.path == "/api/ai-course-plan":
            try:
                design = payload.get("design", {})
                year_id = payload.get("year_id", "")
                brief = payload.get("brief", {})
                ai_payload = {
                    "brief": brief,
                    "selection_objectives": brief.get("description", ""),
                    "selection_rule": "Usa selection_objectives come criterio principale per scegliere quali paragrafi e sottoparagrafi inserire nelle UDA.",
                    "target_year_id": year_id,
                    "current_course": compact_design(design),
                    "available_topics": heading_catalog_tree(),
                    "constraints": {
                        "use_only_available_topic_ids": True,
                        "do_not_duplicate_topics": True,
                        "return_items_as_topic_ids": True,
                        "teacher_must_review_before_apply": True,
                    },
                }
                raw = call_ai_course_plan(ai_payload)
                self.write_json({"proposal": normalize_course_plan(raw, design, year_id)})
            except Exception as error:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        self.send_error(404)

    def write_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, request_path: str) -> None:
        relative = unquote(request_path.lstrip("/")) or "tools/course_board.html"
        target = (ROOT / relative).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self.send_error(403)
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix in {".html", ".css", ".js"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CourseBoardHandler)
    print(f"Course board: http://{args.host}:{args.port}/tools/course_board.html")
    print("Premi Ctrl+C per fermare il server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer fermato.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

