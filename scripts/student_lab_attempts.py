from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts import track_assignments
from scripts.student_identity import confined_regular_file


ATTEMPT_SELECTION_SCHEMA = "student_lab_attempt_selection.v1"
SAFE_KEY_PATTERN = re.compile(r"[^a-z0-9]+")


def clean_text(value: Any) -> str:
    """Return a stripped string value."""

    return str(value or "").strip()


def assignment_storage_key(assignment_id: str) -> str:
    """Return a readable collision-resistant directory name."""

    normalized = clean_text(assignment_id)
    if not normalized:
        raise ValueError("assignment_id mancante per lo storico tentativi.")
    slug = SAFE_KEY_PATTERN.sub("-", normalized.lower()).strip("-")[:48] or "assignment"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}"


def assignment_history_dir(report_path: Path, assignment_id: str) -> Path:
    """Return the canonical history directory for one assignment."""

    return report_path.parent / "assignments" / assignment_storage_key(assignment_id)


def new_attempt_id() -> str:
    """Return a sortable identifier that remains unique within one second."""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"attempt-{timestamp}-{uuid.uuid4().hex[:8]}"


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Write one JSON object atomically in the destination directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def persist_attempt(report_path: Path, assignment_id: str, report: dict[str, Any]) -> tuple[Path, Path]:
    """Persist an immutable attempt and the assignment-specific latest report."""

    history_dir = assignment_history_dir(report_path, assignment_id)
    attempt_id = new_attempt_id()
    stored = dict(report)
    stored["attempt_id"] = attempt_id
    stored["assignment_id"] = assignment_id
    attempt_path = history_dir / "attempts" / f"{attempt_id}.json"
    if attempt_path.exists():
        raise ValueError(f"ID tentativo già esistente: {attempt_id}")
    write_json_atomic(attempt_path, stored)
    assignment_latest_path = history_dir / "latest.json"
    write_json_atomic(assignment_latest_path, stored)
    return attempt_path, assignment_latest_path


def load_attempts(
    report_path: Path,
    assignment_id: str,
    activity_id: str,
    *,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load valid immutable attempts for one assignment."""

    attempts_dir = assignment_history_dir(report_path, assignment_id) / "attempts"
    if not attempts_dir.is_dir():
        return []
    attempts: list[dict[str, Any]] = []
    for path in sorted(attempts_dir.glob("attempt-*.json")):
        safe_path = confined_regular_file(base_dir, path) if base_dir is not None else path
        if safe_path is None:
            continue
        try:
            report = track_assignments.load_report(safe_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if report is None:
            continue
        if clean_text(report.get("assignment_id")) != assignment_id:
            continue
        if clean_text(report.get("activity_id")) != activity_id:
            continue
        attempt_id = clean_text(report.get("attempt_id"))
        if not attempt_id or path.name != f"{attempt_id}.json":
            continue
        attempts.append(report)
    return attempts


def attempt_sort_key(report: dict[str, Any]) -> tuple[str, str]:
    """Return the stable chronological key used for latest selection."""

    created_at = clean_text(report.get("submitted_at")) or clean_text(report.get("generated_at"))
    return created_at, clean_text(report.get("attempt_id"))


def best_attempt_sort_key(report: dict[str, Any]) -> tuple[int, float, int, int, str, str]:
    """Return a deterministic technical quality key for best selection."""

    grading = track_assignments.grading_summary(report)
    passed_count = grading.get("tests_passed")
    total_count = grading.get("tests_total")
    passed_tests = passed_count if isinstance(passed_count, int) and passed_count >= 0 else 0
    total_tests = total_count if isinstance(total_count, int) and total_count > 0 else 0
    ratio = passed_tests / total_tests if total_tests else -1.0
    valid = int(total_tests > 0 or isinstance(report.get("passed"), bool))
    passed = int(report.get("passed") is True)
    created_at, attempt_id = attempt_sort_key(report)
    return valid, ratio, passed, passed_tests, created_at, attempt_id


def select_latest_attempt(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the most recent valid attempt."""

    return max(attempts, key=attempt_sort_key, default=None)


def select_best_attempt(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the technically strongest valid attempt."""

    return max(attempts, key=best_attempt_sort_key, default=None)


def attempt_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return compact metadata for a service payload."""

    if report is None:
        return None
    grading = track_assignments.grading_summary(report)
    return {
        "id": clean_text(report.get("attempt_id")),
        "submitted_at": clean_text(report.get("submitted_at")) or clean_text(report.get("generated_at")),
        "status": clean_text(report.get("status")),
        "passed": report.get("passed") if isinstance(report.get("passed"), bool) else None,
        "tests_passed": grading.get("tests_passed"),
        "tests_total": grading.get("tests_total"),
    }


def set_final_attempt(report_path: Path, assignment_id: str, activity_id: str, attempt_id: str) -> Path:
    """Select an existing attempt as the final submission."""

    clean_attempt_id = clean_text(attempt_id)
    attempts = load_attempts(report_path, assignment_id, activity_id)
    selected = next((item for item in attempts if clean_text(item.get("attempt_id")) == clean_attempt_id), None)
    if selected is None:
        raise ValueError(f"Tentativo non trovato per la consegna: {clean_attempt_id}")
    output = assignment_history_dir(report_path, assignment_id) / "final.json"
    write_json_atomic(
        output,
        {
            "schema_version": ATTEMPT_SELECTION_SCHEMA,
            "assignment_id": assignment_id,
            "activity_id": activity_id,
            "attempt_id": clean_attempt_id,
            "selected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
    )
    return output


def load_final_attempt(
    report_path: Path,
    assignment_id: str,
    activity_id: str,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Return the explicitly selected final attempt, if valid."""

    final_path = assignment_history_dir(report_path, assignment_id) / "final.json"
    safe_final_path = confined_regular_file(base_dir, final_path) if base_dir is not None else final_path
    if safe_final_path is None:
        return None
    try:
        selection = track_assignments.load_report(safe_final_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if selection is None:
        return None
    if selection.get("schema_version") != ATTEMPT_SELECTION_SCHEMA:
        return None
    if clean_text(selection.get("assignment_id")) != assignment_id:
        return None
    if clean_text(selection.get("activity_id")) != activity_id:
        return None
    attempt_id = clean_text(selection.get("attempt_id"))
    return next(
        (
            attempt
            for attempt in load_attempts(report_path, assignment_id, activity_id, base_dir=base_dir)
            if clean_text(attempt.get("attempt_id")) == attempt_id
        ),
        None,
    )
