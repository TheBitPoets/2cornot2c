from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import create_activity, validate_activity
from scripts.thebitlab_contracts import normalize_activity, normalize_assignment_register


DESIGN_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+\.json$")


class JsonCourseStorage:
    """JSON storage adapter for course designs and school calendars."""

    def __init__(self, root: Path, default_sources: list[str] | None = None) -> None:
        self.root = root
        self.default_sources = default_sources or []
        self.design_path = root / "doc" / "course_design.json"
        self.course_designs_dir = root / "doc" / "course_designs"
        self.school_calendars_dir = root / "doc" / "calendars"

    def safe_design_name(self, name: str) -> str:
        """Validate a JSON filename used by saved designs and calendars."""

        clean_name = name.strip()
        if not DESIGN_NAME_RE.match(clean_name):
            raise ValueError("Nome non valido. Usa solo lettere, numeri, trattino, underscore, punto e suffisso .json.")
        return clean_name

    def saved_design_path(self, name: str) -> Path:
        """Return the safe path for a saved course design."""

        return self.course_designs_dir / self.safe_design_name(name)

    def school_calendar_path(self, name: str) -> Path:
        """Return the safe path for a saved school calendar."""

        return self.school_calendars_dir / self.safe_design_name(name)

    def read_json(self, path: Path) -> dict[str, Any]:
        """Read a JSON object from path."""

        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"JSON non valido: {path}")
        return payload

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        """Write a JSON object with stable formatting."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def relative_path(self, path: Path) -> str:
        """Return a repository-relative path with URL-style separators."""

        return str(path.relative_to(self.root)).replace("\\", "/")

    def read_design(self) -> dict[str, Any]:
        """Load the current course design, returning a minimal shape if missing."""

        if self.design_path.exists():
            return self.read_json(self.design_path)
        return {"version": 1, "source_files": self.default_sources, "years": []}

    def write_design(self, payload: dict[str, Any]) -> None:
        """Persist the current course design."""

        self.write_json(self.design_path, payload)

    def list_saved_designs(self) -> list[dict[str, str]]:
        """List saved course designs stored in doc/course_designs."""

        self.course_designs_dir.mkdir(parents=True, exist_ok=True)
        return [
            {"name": path.name, "path": self.relative_path(path)}
            for path in sorted(self.course_designs_dir.glob("*.json"))
        ]

    def read_saved_design(self, name: str) -> dict[str, Any]:
        """Read a saved course design by filename."""

        path = self.saved_design_path(name)
        if not path.is_file():
            raise FileNotFoundError(f"Percorso salvato non trovato: {name}")
        return self.read_json(path)

    def write_saved_design(self, name: str, payload: dict[str, Any]) -> dict[str, str]:
        """Persist a named course design in the archive folder."""

        path = self.saved_design_path(name)
        self.write_json(path, payload)
        return {"name": path.name, "path": self.relative_path(path)}

    def list_school_calendars(self) -> list[dict[str, str]]:
        """List saved school calendars stored in doc/calendars."""

        self.school_calendars_dir.mkdir(parents=True, exist_ok=True)
        calendars = []
        for path in sorted(self.school_calendars_dir.glob("*.json")):
            metadata = {"name": path.name, "path": self.relative_path(path), "course_design_name": ""}
            try:
                payload = self.read_json(path)
                course_design_name = payload.get("course_design_name", "")
                metadata["course_design_name"] = course_design_name if isinstance(course_design_name, str) else ""
            except Exception:  # noqa: BLE001
                metadata["course_design_name"] = ""
            calendars.append(metadata)
        return calendars

    def read_school_calendar(self, name: str) -> dict[str, Any]:
        """Read a saved school calendar by filename."""

        path = self.school_calendar_path(name)
        if not path.is_file():
            raise FileNotFoundError(f"Calendario scolastico non trovato: {name}")
        return self.read_json(path)

    def write_school_calendar(self, name: str, payload: dict[str, Any]) -> dict[str, str]:
        """Persist a named school calendar in the calendars folder."""

        path = self.school_calendar_path(name)
        self.write_json(path, payload)
        return {"name": path.name, "path": self.relative_path(path)}

    def delete_saved_design(
        self,
        name: str,
        delete_calendars: bool = False,
        calendars: list[str] | None = None,
    ) -> dict[str, Any]:
        """Delete an archived course design and, optionally, its linked calendars."""

        safe_name = self.safe_design_name(name)
        path = self.saved_design_path(safe_name)
        if not path.is_file():
            raise FileNotFoundError(f"Percorso salvato non trovato: {safe_name}")
        path.unlink()
        deleted_calendars = []
        if delete_calendars:
            for calendar_name in calendars or []:
                safe_calendar_name = self.safe_design_name(calendar_name)
                calendar_path = self.school_calendar_path(safe_calendar_name)
                if not calendar_path.is_file():
                    continue
                payload = self.read_json(calendar_path)
                if payload.get("course_design_name", "") != safe_name:
                    continue
                calendar_path.unlink()
                deleted_calendars.append(safe_calendar_name)
        return {
            "name": safe_name,
            "deleted_calendars": deleted_calendars,
            "designs": self.list_saved_designs(),
            "calendars": self.list_school_calendars(),
        }


class JsonAssignmentStorage:
    """JSON storage adapter for activities and assignment tracking reports."""

    def __init__(self, root: Path, teacher_reports_dir: Path, activity_dirs: list[Path]) -> None:
        self.root = root
        self.teacher_reports_dir = teacher_reports_dir
        self.activity_dirs = activity_dirs

    def relative_path(self, path: Path) -> str:
        """Return a repository-relative path with URL-style separators."""

        return str(path.relative_to(self.root)).replace("\\", "/")

    def safe_teacher_report_path(self, name: str) -> Path:
        """Return a safe teacher-report path below teacher-reports."""

        clean_name = name.strip().replace("\\", "/")
        if not clean_name or clean_name.startswith("/") or ".." in Path(clean_name).parts or not clean_name.endswith(".json"):
            raise ValueError("Nome registro non valido. Usa un path relativo .json dentro teacher-reports.")
        path = (self.teacher_reports_dir / clean_name).resolve()
        path.relative_to(self.teacher_reports_dir.resolve())
        return path

    def activity_drafts_dir(self) -> Path:
        """Return the folder used for teacher-authored draft activities."""

        return self.root / "activities" / "drafts"

    def safe_activity_draft_path(self, activity_id: str) -> Path:
        """Return a safe draft activity path below activities/drafts."""

        filename = f"{create_activity.slugify(activity_id)}.json"
        path = (self.activity_drafts_dir() / filename).resolve()
        path.relative_to(self.activity_drafts_dir().resolve())
        return path

    def read_json(self, path: Path) -> dict[str, Any]:
        """Read a JSON object from path."""

        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"JSON non valido: {path}")
        return payload

    def write_json(self, path: Path, payload: dict[str, Any]) -> None:
        """Write a JSON object with stable formatting."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def save_activity(self, payload: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        """Validate and persist a teacher-authored activity draft."""

        activity_id = str(payload.get("id", "")).strip()
        errors = validate_activity.validate_activity(payload, activity_id or "<activity>")
        if errors:
            raise ValueError("\n".join(errors))
        path = self.safe_activity_draft_path(activity_id)
        if path.exists() and not overwrite:
            raise ValueError(f"Activity gia esistente: {self.relative_path(path)}")
        self.write_json(path, payload)
        activity = normalize_activity(payload)
        return {
            "id": activity.get("id", ""),
            "title": activity.get("title", ""),
            "kind": activity.get("kind", ""),
            "student_support_mode": activity.get("student_support_mode", ""),
            "class_id": activity.get("class_id", ""),
            "class_label": activity.get("class_id", ""),
            "github_team": activity.get("github_team", ""),
            "language": activity.get("language", ""),
            "path": self.relative_path(path),
        }

    def list_assignment_reports(self) -> list[dict[str, Any]]:
        """List assignment tracking reports stored in teacher-reports."""

        self.teacher_reports_dir.mkdir(parents=True, exist_ok=True)
        reports = []
        for path in sorted(self.teacher_reports_dir.rglob("*.json")):
            try:
                payload = self.read_json(path)
            except Exception:  # noqa: BLE001
                payload = {}
            payload = normalize_assignment_register(payload)
            students = payload.get("students", []) if isinstance(payload.get("students"), list) else []
            submitted = sum(1 for student in students if isinstance(student, dict) and student.get("submitted"))
            late = sum(1 for student in students if isinstance(student, dict) and student.get("submitted") and student.get("late"))
            not_submitted = sum(1 for student in students if isinstance(student, dict) and not student.get("submitted"))
            reports.append(
                {
                    "name": str(path.relative_to(self.teacher_reports_dir)).replace("\\", "/"),
                    "path": self.relative_path(path),
                    "activity_id": payload.get("activity_id", ""),
                    "title": payload.get("title", ""),
                    "class_id": payload.get("class_id", ""),
                    "class_label": payload.get("class_label", ""),
                    "github_team": payload.get("github_team", ""),
                    "due_at": payload.get("due_at") or "",
                    "students": len(students),
                    "submitted": submitted,
                    "late": late,
                    "not_submitted": not_submitted,
                    "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )
        return reports

    def read_assignment_report(self, name: str) -> dict[str, Any]:
        """Read one assignment tracking report from teacher-reports."""

        path = self.safe_teacher_report_path(name)
        if not path.is_file():
            raise FileNotFoundError(f"Registro consegne non trovato: {name}")
        payload = self.read_json(path)
        if not isinstance(payload.get("students"), list):
            raise ValueError("Registro consegne non valido: students deve essere una lista.")
        return normalize_assignment_register(payload)

    def write_assignment_report(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist one assignment tracking report below teacher-reports."""

        path = self.safe_teacher_report_path(name)
        self.write_json(path, payload)
        return normalize_assignment_register(payload)

    def list_activities(self) -> list[dict[str, Any]]:
        """List available activity JSON files for the assignment dashboard."""

        activities = []
        seen_paths = set()
        for directory in self.activity_dirs:
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*.json")):
                resolved = path.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                try:
                    payload = self.read_json(path)
                except Exception:  # noqa: BLE001
                    continue
                activity = normalize_activity(payload)
                if not activity.get("id"):
                    continue
                activities.append(
                    {
                        "id": activity.get("id", ""),
                        "title": activity.get("title", ""),
                        "kind": activity.get("kind", ""),
                        "student_support_mode": activity.get("student_support_mode", ""),
                        "class_id": activity.get("class_id", ""),
                        "class_label": activity.get("class_id", ""),
                        "github_team": activity.get("github_team", ""),
                        "language": activity.get("language", ""),
                        "path": self.relative_path(path),
                    }
                )
        return activities


class JsonClassRosterStorage:
    """JSON storage adapter for local class/student rosters."""

    def __init__(self, root: Path, classes_dir: Path | None = None) -> None:
        self.root = root
        self.classes_dir = classes_dir or root / "doc" / "classes"

    def relative_path(self, path: Path) -> str:
        """Return a repository-relative path with URL-style separators."""

        return str(path.relative_to(self.root)).replace("\\", "/")

    def safe_roster_name(self, name: str) -> str:
        """Validate a class roster JSON filename."""

        clean_name = name.strip().replace("\\", "/")
        if "/" in clean_name or not DESIGN_NAME_RE.match(clean_name):
            raise ValueError("Nome roster non valido. Usa un file .json dentro doc/classes.")
        return clean_name

    def roster_path(self, name: str) -> Path:
        """Return the safe path for one class roster."""

        return self.classes_dir / self.safe_roster_name(name)

    def read_json(self, path: Path) -> dict[str, Any]:
        """Read a JSON object from path."""

        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError(f"JSON non valido: {path}")
        return payload

    def list_class_rosters(self) -> list[dict[str, Any]]:
        """List local class rosters stored in doc/classes."""

        self.classes_dir.mkdir(parents=True, exist_ok=True)
        rosters = []
        for path in sorted(self.classes_dir.glob("*.json")):
            try:
                payload = self.read_json(path)
                roster = normalize_class_roster(payload)
            except Exception:  # noqa: BLE001
                continue
            rosters.append(
                {
                    "name": path.name,
                    "path": self.relative_path(path),
                    "id": roster.get("id", ""),
                    "label": roster.get("label", ""),
                    "school_year": roster.get("school_year", ""),
                    "provider": roster.get("provider", "local"),
                    "provider_ref": roster.get("provider_ref", ""),
                    "github_team": roster.get("github_team", ""),
                    "students": len(roster.get("students", [])),
                    "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )
        return rosters

    def read_class_roster(self, name: str) -> dict[str, Any]:
        """Read and normalize one local class roster."""

        path = self.roster_path(name)
        if not path.is_file():
            raise FileNotFoundError(f"Roster classe non trovato: {name}")
        return normalize_class_roster(self.read_json(path))


def normalize_class_roster(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical MVP shape for a class roster."""

    roster_id = _first_text(payload, "id", "class_id")
    label = _first_text(payload, "label", "class_label", "name")
    students = payload.get("students")
    if not roster_id:
        raise ValueError("Roster classe non valido: id mancante.")
    if not isinstance(students, list):
        raise ValueError("Roster classe non valido: students deve essere una lista.")
    if any(not isinstance(student, dict) for student in students):
        raise ValueError("Roster classe non valido: ogni studente deve essere un oggetto.")
    normalized_students = [_normalize_roster_student(student) for student in students]
    return {
        "schema_version": _first_text(payload, "schema_version") or "1.0",
        "id": roster_id,
        "label": label or roster_id,
        "school_year": _first_text(payload, "school_year", "year"),
        "provider": _first_text(payload, "provider") or "local",
        "provider_ref": _first_text(payload, "provider_ref"),
        "github_team": _first_text(payload, "github_team"),
        "students": sorted(normalized_students, key=lambda student: student["id"]),
    }


def _normalize_roster_student(payload: dict[str, Any]) -> dict[str, Any]:
    student_id = _first_text(payload, "id", "student_id", "student")
    if not student_id:
        raise ValueError("Roster classe non valido: studente senza id.")
    github_username = _first_text(payload, "github_username", "github")
    repo_ref = _first_text(payload, "repo_ref", "repo")
    return {
        "id": student_id,
        "display_name": _first_text(payload, "display_name", "name", "student") or student_id,
        "email": _first_text(payload, "email"),
        "github_username": github_username,
        "repo_ref": repo_ref,
        "local_path": _path_text(payload, "local_path"),
        "repo_path": _path_text(payload, "repo_path"),
        "path": _path_text(payload, "path"),
        "active": _bool_value(payload.get("active", True)),
        "provider_accounts": _list_of_dicts(payload.get("provider_accounts")),
    }


def _first_text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _path_text(payload: dict[str, Any], key: str) -> str:
    return _first_text(payload, key).replace("\\", "/")


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "n", "off", ""}
    return bool(value)


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]
