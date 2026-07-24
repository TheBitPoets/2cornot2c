from __future__ import annotations

import hashlib
import heapq
import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from scripts import track_assignments
from scripts.student_identity import confined_regular_file


ATTEMPT_SELECTION_SCHEMA = "student_lab_attempt_selection.v1"
SAFE_KEY_PATTERN = re.compile(r"[^a-z0-9]+")
MAX_ATTEMPTS_LOADED = 500
MAX_ATTEMPT_FILES_SCANNED = 5000
MAX_ATTEMPT_HISTORY_BYTES = 20 * 1024 * 1024


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


def confined_destination(base_dir: Path, candidate: Path) -> Path:
    """Validate a write destination without following symlinked parents."""

    lexical_base = base_dir.absolute()
    lexical_candidate = candidate.absolute()
    try:
        relative = lexical_candidate.relative_to(lexical_base)
    except ValueError as error:
        raise ValueError("Destinazione report fuori dal repository studente.") from error
    current = lexical_base
    for part in relative.parts:
        current /= part
        if current.exists() and current.is_symlink():
            raise ValueError("Destinazione report attraversa un collegamento simbolico.")
    return lexical_candidate


def json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize a JSON object using the repository text contract."""

    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sync_directory(path: Path) -> None:
    """Sync directory metadata where the platform exposes POSIX fsync."""

    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_bytes_atomic(path: Path, content: bytes, *, base_dir: Path | None = None) -> None:
    """Write bytes atomically in the destination directory."""

    output = confined_destination(base_dir, path) if base_dir is not None else path
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, output)
        sync_directory(output.parent)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, payload: dict[str, Any], *, base_dir: Path | None = None) -> None:
    """Write one JSON object atomically in the destination directory."""

    write_bytes_atomic(path, json_bytes(payload), base_dir=base_dir)


def write_json_exclusive(path: Path, payload: dict[str, Any], *, base_dir: Path) -> None:
    """Publish an immutable JSON file without replacing an existing attempt."""

    output = confined_destination(base_dir, path)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    published = False
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json_bytes(payload))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary_path, output)
        published = True
        sync_directory(output.parent)
    except BaseException:
        if published:
            output.unlink(missing_ok=True)
        raise
    finally:
        temporary_path.unlink(missing_ok=True)


@contextmanager
def report_history_lock(report_path: Path, *, base_dir: Path) -> Iterator[None]:
    """Serialize report-history updates using only the Python standard library."""

    lock_path = confined_destination(base_dir, report_path.parent / ".attempt-history.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def persist_attempt(
    report_path: Path,
    assignment_id: str,
    report: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Persist an immutable attempt and the assignment-specific latest report."""

    history_dir = assignment_history_dir(report_path, assignment_id)
    attempt_id = new_attempt_id()
    stored = dict(report)
    stored["attempt_id"] = attempt_id
    stored["assignment_id"] = assignment_id
    attempt_path = history_dir / "attempts" / f"{attempt_id}.json"
    write_base = base_dir or report_path.parents[2]
    try:
        write_json_exclusive(attempt_path, stored, base_dir=write_base)
    except FileExistsError as error:
        raise ValueError(f"ID tentativo già esistente: {attempt_id}") from error
    assignment_latest_path = history_dir / "latest.json"
    try:
        current_latest = (
            track_assignments.load_report(assignment_latest_path)
            if confined_regular_file(write_base, assignment_latest_path)
            else None
        )
        if current_latest is None or attempt_sort_key(stored) >= attempt_sort_key(current_latest):
            write_json_atomic(assignment_latest_path, stored, base_dir=write_base)
    except BaseException:
        attempt_path.unlink(missing_ok=True)
        raise
    return attempt_path, assignment_latest_path


def persist_standard_report(
    report_path: Path,
    assignment_id: str,
    report: dict[str, Any],
    *,
    base_dir: Path,
) -> tuple[Path, Path]:
    """Persist one attempt and both latest projections under a process lock."""

    history_latest = assignment_history_dir(report_path, assignment_id) / "latest.json"
    attempt_path: Path | None = None
    with report_history_lock(report_path, base_dir=base_dir):
        previous_history = history_latest.read_bytes() if confined_regular_file(base_dir, history_latest) else None
        previous_legacy = report_path.read_bytes() if confined_regular_file(base_dir, report_path) else None
        try:
            attempt_path, history_latest = persist_attempt(
                report_path,
                assignment_id,
                report,
                base_dir=base_dir,
            )
            stored = json.loads(history_latest.read_text(encoding="utf-8"))
            write_json_atomic(report_path, stored, base_dir=base_dir)
        except BaseException:
            if attempt_path is not None:
                attempt_path.unlink(missing_ok=True)
            if previous_history is None:
                history_latest.unlink(missing_ok=True)
            else:
                write_bytes_atomic(history_latest, previous_history, base_dir=base_dir)
            if previous_legacy is None:
                report_path.unlink(missing_ok=True)
            else:
                write_bytes_atomic(report_path, previous_legacy, base_dir=base_dir)
            raise
    return attempt_path, history_latest


def load_attempt_history(
    report_path: Path,
    assignment_id: str,
    activity_id: str,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Load a bounded attempt window and disclose when it is truncated."""

    attempts_dir = assignment_history_dir(report_path, assignment_id) / "attempts"
    if not attempts_dir.is_dir():
        return {"attempts": [], "count": 0, "truncated": False}
    attempts: list[dict[str, Any]] = []
    total_bytes = 0
    newest_names: list[str] = []
    scanned_count = 0
    candidate_count = 0
    scan_truncated = False
    with os.scandir(attempts_dir) as entries:
        for entry in entries:
            scanned_count += 1
            if scanned_count > MAX_ATTEMPT_FILES_SCANNED:
                scan_truncated = True
                break
            if not entry.name.startswith("attempt-") or not entry.name.endswith(".json"):
                continue
            if not entry.is_file(follow_symlinks=False):
                continue
            candidate_count += 1
            if len(newest_names) < MAX_ATTEMPTS_LOADED:
                heapq.heappush(newest_names, entry.name)
            elif entry.name > newest_names[0]:
                heapq.heapreplace(newest_names, entry.name)
    paths = [attempts_dir / name for name in sorted(newest_names, reverse=True)]
    for path in paths:
        safe_path = confined_regular_file(base_dir, path) if base_dir is not None else path
        if safe_path is None:
            continue
        try:
            total_bytes += safe_path.stat().st_size
        except OSError:
            continue
        if total_bytes > MAX_ATTEMPT_HISTORY_BYTES:
            break
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
    return {
        "attempts": attempts,
        "count": candidate_count,
        "truncated": scan_truncated or candidate_count > len(attempts),
    }


def load_attempts(
    report_path: Path,
    assignment_id: str,
    activity_id: str,
    *,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load the bounded valid attempt window for one assignment."""

    return load_attempt_history(
        report_path,
        assignment_id,
        activity_id,
        base_dir=base_dir,
    )["attempts"]


def load_attempt_by_id(
    report_path: Path,
    assignment_id: str,
    activity_id: str,
    attempt_id: str,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Load one immutable attempt directly without scanning the history."""

    clean_attempt_id = clean_text(attempt_id)
    if not clean_attempt_id.startswith("attempt-") or Path(clean_attempt_id).name != clean_attempt_id:
        return None
    path = assignment_history_dir(report_path, assignment_id) / "attempts" / f"{clean_attempt_id}.json"
    safe_path = confined_regular_file(base_dir, path) if base_dir is not None else path
    if safe_path is None:
        return None
    try:
        report = track_assignments.load_report(safe_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if report is None:
        return None
    if clean_text(report.get("attempt_id")) != clean_attempt_id:
        return None
    if clean_text(report.get("assignment_id")) != assignment_id:
        return None
    if clean_text(report.get("activity_id")) != activity_id:
        return None
    return report


def load_assignment_latest(
    report_path: Path,
    assignment_id: str,
    activity_id: str,
    *,
    base_dir: Path,
) -> dict[str, Any] | None:
    """Load and validate the assignment-specific latest projection."""

    path = assignment_history_dir(report_path, assignment_id) / "latest.json"
    safe_path = confined_regular_file(base_dir, path)
    if safe_path is None:
        return None
    try:
        report = track_assignments.load_report(safe_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if report is None:
        return None
    if clean_text(report.get("assignment_id")) != assignment_id:
        return None
    if clean_text(report.get("activity_id")) != activity_id:
        return None
    attempt_id = clean_text(report.get("attempt_id"))
    if not attempt_id:
        return None
    return report


def attempt_sort_key(report: dict[str, Any]) -> tuple[float, str]:
    """Return the stable chronological key used for latest selection."""

    created_at = clean_text(report.get("submitted_at")) or clean_text(report.get("generated_at"))
    try:
        timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
    except ValueError:
        timestamp = float("-inf")
    return timestamp, clean_text(report.get("attempt_id"))


def best_attempt_sort_key(report: dict[str, Any]) -> tuple[int, float, int, int, float, str]:
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
    base_dir = report_path.parents[2]
    selected = load_attempt_by_id(
        report_path,
        assignment_id,
        activity_id,
        clean_attempt_id,
        base_dir=base_dir,
    )
    if selected is None:
        raise ValueError(f"Tentativo non trovato per la consegna: {clean_attempt_id}")
    output = assignment_history_dir(report_path, assignment_id) / "final.json"
    with report_history_lock(report_path, base_dir=base_dir):
        write_json_atomic(
            output,
            {
                "schema_version": ATTEMPT_SELECTION_SCHEMA,
                "assignment_id": assignment_id,
                "activity_id": activity_id,
                "attempt_id": clean_attempt_id,
                "selected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            },
            base_dir=base_dir,
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
    return load_attempt_by_id(
        report_path,
        assignment_id,
        activity_id,
        attempt_id,
        base_dir=base_dir,
    )
