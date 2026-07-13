"""Helpers for explicit MVP activity assignment records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import create_activity


ASSIGNMENT_SCHEMA_VERSION = "1.0"
DEFAULT_ASSIGNMENTS_DIR = Path("teacher-assignments")


@dataclass(frozen=True)
class AssignmentStatus:
    """Computed status for one assignment record."""

    assignment: dict[str, Any]
    due: bool
    has_register: bool

    @property
    def needs_register(self) -> bool:
        """Return whether the assignment is due and lacks a register."""

        return self.due and not self.has_register

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable status summary."""

        return {
            "assignment": self.assignment,
            "due": self.due,
            "has_register": self.has_register,
            "needs_register": self.needs_register,
        }


def parse_iso_datetime(value: str, field_name: str) -> datetime:
    """Parse an ISO datetime, accepting a trailing Z for UTC."""

    clean = str(value or "").strip()
    if not clean:
        raise ValueError(f"{field_name} obbligatorio.")
    try:
        return datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field_name} non valido: {clean}") from error


def normalize_target(target: dict[str, Any] | str) -> dict[str, str]:
    """Normalize a target entry into the assignment target shape."""

    if isinstance(target, str):
        clean = target.strip()
        if not clean:
            raise ValueError("Target vuoto.")
        return {"target": clean}
    if not isinstance(target, dict):
        raise ValueError("Target non valido.")
    normalized = {
        key: str(target.get(key, "")).strip()
        for key in ("student_id", "display_name", "repo_ref", "path", "target")
        if str(target.get(key, "")).strip()
    }
    if not normalized:
        raise ValueError("Target vuoto.")
    return normalized


def assignment_target_ref(
    *,
    target_type: str,
    class_id: str = "",
    github_team: str = "",
    targets: list[dict[str, str]] | None = None,
) -> str:
    """Return the human/stable target reference used in generated ids."""

    if target_type == "class" and class_id:
        return class_id
    if target_type == "team" and github_team:
        return github_team
    targets = targets or []
    if target_type == "student" and len(targets) == 1:
        return targets[0].get("student_id") or targets[0].get("target") or targets[0].get("path") or "student"
    if target_type == "group" and targets:
        return f"group-{len(targets)}"
    return target_type or "target"


def build_assignment_id(activity_id: str, target_ref: str, assigned_at: str) -> str:
    """Build a stable filesystem-friendly assignment id."""

    date_part = parse_iso_datetime(assigned_at, "assigned_at").date().isoformat()
    slug = create_activity.slugify(f"{activity_id}-{target_ref}-{date_part}")
    return f"assignment-{slug}"


def build_assignment_record(
    *,
    activity_id: str,
    activity_path: str,
    target_type: str,
    assigned_at: str,
    due_at: str,
    targets: list[dict[str, Any] | str],
    class_id: str = "",
    class_label: str = "",
    github_team: str = "",
    assignment_id: str = "",
) -> dict[str, Any]:
    """Build and validate an explicit assignment record."""

    clean_activity_id = str(activity_id or "").strip()
    clean_activity_path = str(activity_path or "").strip().replace("\\", "/")
    clean_target_type = str(target_type or "").strip() or "group"
    if not clean_activity_id:
        raise ValueError("activity_id obbligatorio.")
    if not clean_activity_path:
        raise ValueError("activity_path obbligatorio.")
    if clean_target_type not in {"class", "team", "group", "student"}:
        raise ValueError("target_type deve essere class, team, group o student.")
    normalized_targets = [normalize_target(target) for target in targets]
    if not normalized_targets:
        raise ValueError("targets obbligatorio.")
    parse_iso_datetime(assigned_at, "assigned_at")
    parse_iso_datetime(due_at, "due_at")
    target_ref = assignment_target_ref(
        target_type=clean_target_type,
        class_id=str(class_id or "").strip(),
        github_team=str(github_team or "").strip(),
        targets=normalized_targets,
    )
    clean_assignment_id = str(assignment_id or "").strip() or build_assignment_id(
        clean_activity_id,
        target_ref,
        assigned_at,
    )
    return {
        "schema_version": ASSIGNMENT_SCHEMA_VERSION,
        "id": clean_assignment_id,
        "activity_id": clean_activity_id,
        "activity_path": clean_activity_path,
        "target_type": clean_target_type,
        "class_id": str(class_id or "").strip(),
        "class_label": str(class_label or "").strip(),
        "github_team": str(github_team or "").strip(),
        "assigned_at": str(assigned_at).strip(),
        "due_at": str(due_at).strip(),
        "targets": normalized_targets,
    }


def validate_assignment_record(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize an assignment record payload."""

    if not isinstance(payload, dict):
        raise ValueError("Assegnazione non valida.")
    return build_assignment_record(
        assignment_id=str(payload.get("id", "")).strip(),
        activity_id=str(payload.get("activity_id", "")).strip(),
        activity_path=str(payload.get("activity_path", "")).strip(),
        target_type=str(payload.get("target_type", "")).strip(),
        class_id=str(payload.get("class_id", "")).strip(),
        class_label=str(payload.get("class_label", "")).strip(),
        github_team=str(payload.get("github_team", "")).strip(),
        assigned_at=str(payload.get("assigned_at", "")).strip(),
        due_at=str(payload.get("due_at", "")).strip(),
        targets=payload.get("targets") if isinstance(payload.get("targets"), list) else [],
    )


def assignment_matches_register(assignment: dict[str, Any], register: dict[str, Any]) -> bool:
    """Return whether a register already covers an assignment."""

    if not isinstance(register, dict):
        return False
    assignment_id = str(assignment.get("id", "")).strip()
    register_assignment_id = str(register.get("assignment_id", "")).strip()
    if assignment_id and register_assignment_id:
        return assignment_id == register_assignment_id
    return (
        str(assignment.get("activity_id", "")).strip() == str(register.get("activity_id", "")).strip()
        and str(assignment.get("class_id", "")).strip() == str(register.get("class_id", "")).strip()
        and str(assignment.get("due_at", "")).strip() == str(register.get("due_at", "")).strip()
    )


def assignment_status(
    assignment: dict[str, Any],
    registers: list[dict[str, Any]],
    now: str | datetime,
) -> AssignmentStatus:
    """Return due/register status for one assignment."""

    normalized = validate_assignment_record(assignment)
    current_time = now if isinstance(now, datetime) else parse_iso_datetime(str(now), "now")
    due_at = parse_iso_datetime(normalized["due_at"], "due_at")
    has_register = any(assignment_matches_register(normalized, register) for register in registers)
    return AssignmentStatus(assignment=normalized, due=current_time >= due_at, has_register=has_register)


class JsonAssignmentRecordStorage:
    """JSON storage adapter for explicit assignment records."""

    def __init__(self, root: Path, assignments_dir: Path | None = None) -> None:
        self.root = root
        self.assignments_dir = assignments_dir or root / DEFAULT_ASSIGNMENTS_DIR

    def relative_path(self, path: Path) -> str:
        """Return a repository-relative path with URL-style separators."""

        return str(path.relative_to(self.root)).replace("\\", "/")

    def safe_assignment_path(self, assignment_id: str) -> Path:
        """Return a safe assignment JSON path below teacher-assignments."""

        filename = f"{create_activity.slugify(assignment_id)}.json"
        path = (self.assignments_dir / filename).resolve()
        path.relative_to(self.assignments_dir.resolve())
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

    def write_assignment(self, payload: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        """Persist one assignment record."""

        assignment = validate_assignment_record(payload)
        path = self.safe_assignment_path(assignment["id"])
        if path.exists() and not overwrite:
            raise ValueError(f"Assegnazione gia esistente: {self.relative_path(path)}")
        self.write_json(path, assignment)
        return {**assignment, "name": path.name, "path": self.relative_path(path)}

    def read_assignment(self, assignment_id: str) -> dict[str, Any]:
        """Read one assignment record by id."""

        path = self.safe_assignment_path(assignment_id)
        if not path.is_file():
            raise FileNotFoundError(f"Assegnazione non trovata: {assignment_id}")
        return validate_assignment_record(self.read_json(path))

    def list_assignments(self) -> list[dict[str, Any]]:
        """List assignment records stored in teacher-assignments."""

        self.assignments_dir.mkdir(parents=True, exist_ok=True)
        assignments = []
        for path in sorted(self.assignments_dir.glob("*.json")):
            try:
                assignment = validate_assignment_record(self.read_json(path))
            except Exception:  # noqa: BLE001
                continue
            assignments.append({**assignment, "name": path.name, "path": self.relative_path(path)})
        return assignments

    def assignments_due_without_register(
        self,
        registers: list[dict[str, Any]],
        now: str | datetime,
    ) -> list[dict[str, Any]]:
        """Return stored assignments that are due and not covered by a register."""

        return [
            status.to_dict()
            for status in (assignment_status(assignment, registers, now) for assignment in self.list_assignments())
            if status.needs_register
        ]
