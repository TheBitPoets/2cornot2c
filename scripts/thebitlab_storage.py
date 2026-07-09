from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


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
                metadata["course_design_name"] = str(payload.get("course_design_name", ""))
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
