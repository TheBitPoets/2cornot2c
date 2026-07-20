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
import base64
import hashlib
import ipaddress
import json
import mimetypes
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
import uuid
from copy import deepcopy
from contextlib import ExitStack, contextmanager, nullcontext
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

APP_ROOT = Path(__file__).resolve().parents[1]
ROOT = APP_ROOT
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from scripts import (
    activity_ai_package,
    assignment_records,
    assign_activity,
    codex_activity_adapter,
    create_activity,
    create_submission_scaffold,
    manual_ai_feedback,
    student_help_auth,
    student_help_codex_adapter,
    student_help_service,
    student_lab_service,
    thebitlab_services,
    thebitlab_storage,
    track_assignments,
)
from scripts.thebitlab_contracts import normalize_activity
from scripts.student_help_provider import DeterministicStudentHelpProvider, StudentHelpProvider

DESIGN_PATH = ROOT / "doc" / "course_design.json"
COURSE_DESIGNS_DIR = ROOT / "doc" / "course_designs"
SCHOOL_CALENDARS_DIR = ROOT / "doc" / "calendars"
TEACHER_REPORTS_DIR = ROOT / "teacher-reports"
TEACHER_ASSIGNMENTS_DIR = ROOT / "teacher-assignments"
ACTIVITY_DIRS = [ROOT / "activities", ROOT / "examples" / "assignment_tracking"]
COURSE_PLAN_MD_PATH = ROOT / "doc" / "PERCORSO_DIDATTICO.md"
README_PATH = ROOT / "README.md"
AI_PROVIDERS_PATH = ROOT / "config" / "ai_providers.yaml"
AI_SECRET_PATH = ROOT / ".secrets" / "ai.secret"
LEGACY_AI_SECRET_PATH = ROOT / "scripts" / ".secrets" / "ai.secret"
DEFAULT_SOURCES = ["README.md", "LINUX_PROGRAMMING.md"]
ACTIVE_AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai").strip().lower()
ACTIVE_AI_MODEL = os.environ.get("AI_MODEL", "").strip()
MAX_HTTP_WORKERS = 64
MAX_HTTP_WORKERS_PER_CLIENT = 8
HTTP_CLIENT_TIMEOUT_SECONDS = 15
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
MAX_STUDENT_HELP_REQUEST_BYTES = 16 * 1024
MAX_TEACHER_REQUEST_BYTES = 32 * 1024 * 1024
MIN_TEACHER_TOKEN_CHARS = 32
MAX_HELP_LOG_ROLLBACK_BYTES = 256 * 1024 * 1024
HELP_DELETION_SCHEMA_VERSION = "student_help_deletion.v2"
ASSIGNMENT_TARGET_BINDINGS_OPERATION_ID = "assignment-target-bindings-global"
STUDENT_HELP_SERVER_ERROR = "Servizio aiuto temporaneamente non disponibile."
TEACHER_AUTH_REALM = "TheBitLab docente"
PRIVATE_STATIC_ROOTS = {"teacher-assignments", "teacher-help-events", "teacher-reports"}
REMOTE_STUDENT_API_ROUTES = frozenset(
    {
        ("GET", "/api/student-lab/assignments"),
        ("GET", "/api/student-lab/help-history"),
        ("POST", "/api/student-lab/help"),
    }
)
_ASSIGNMENT_OPERATION_LOCKS: dict[str, dict[str, Any]] = {}
_ASSIGNMENT_OPERATION_LOCKS_GUARD = threading.Lock()


class StudentHelpConfigurationError(RuntimeError):
    """Raised when the teacher server has an invalid help-provider setup."""


class StudentHelpBusyError(RuntimeError):
    """Raised when another help request already owns the assignment slot."""


def normalized_assignment_operation_id(operation_id: str) -> str:
    """Return the canonical key shared by equivalent operation identifiers."""

    original = str(operation_id or "").strip()
    readable = create_activity.slugify(original)[:48] or "operation"
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
    return f"{readable}-{digest}"


def data_root_process_lock_dir() -> Path:
    """Return a private, stable directory for cross-process data-root locks."""

    configured = os.environ.get("THEBITLAB_LOCK_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve(strict=False)
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())
        return base / "TheBitLab" / "locks"
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    if runtime_dir:
        return Path(runtime_dir).expanduser().resolve(strict=False) / "thebitlab" / "locks"
    cache_dir = os.environ.get("XDG_CACHE_HOME", "").strip()
    base = Path(cache_dir).expanduser() if cache_dir else Path.home() / ".cache"
    return base.resolve(strict=False) / "thebitlab" / "locks"


class DataRootProcessLock:
    """Hold an operating-system lock for one server data root."""

    def __init__(self, root: Path, *, hold_legacy_lock: bool = True) -> None:
        self.root = root.resolve(strict=False)
        readable = create_activity.slugify(self.root.name)[:32] or "root"
        root_key = os.path.normcase(str(self.root))
        digest = hashlib.sha256(root_key.encode("utf-8")).hexdigest()
        self.path = data_root_process_lock_dir() / f"{readable}-{digest}.lock"
        self.legacy_path = self.root / ".thebitlab-server.lock"
        self.hold_legacy_lock = hold_legacy_lock
        self._handle = None
        self._legacy_handle = None

    @staticmethod
    def _acquire_handle(path: Path):
        handle = path.open("a+b")
        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError):
            handle.close()
            raise
        return handle

    @staticmethod
    def _release_handle(handle) -> None:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()

    def acquire(self) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name != "nt":
            self.path.parent.chmod(0o700)
        self.legacy_path.parent.mkdir(parents=True, exist_ok=True)
        private_handle = None
        legacy_handle = None
        try:
            private_handle = self._acquire_handle(self.path)
            legacy_handle = self._acquire_handle(self.legacy_path)
        except (OSError, BlockingIOError) as error:
            if legacy_handle is not None:
                self._release_handle(legacy_handle)
            if private_handle is not None:
                self._release_handle(private_handle)
            raise RuntimeError(
                f"Un altro server sta gia usando il root dati: {self.root}"
            ) from error
        self._handle = private_handle
        if self.hold_legacy_lock:
            self._legacy_handle = legacy_handle
        else:
            self._release_handle(legacy_handle)

    def release(self) -> None:
        if self._legacy_handle is not None:
            self._release_handle(self._legacy_handle)
            self._legacy_handle = None
        if self._handle is not None:
            self._release_handle(self._handle)
            self._handle = None


@contextmanager
def assignment_operation_lock(assignment_id: str, *, blocking: bool = True):
    """Serialize one assignment operation and release its cache entry afterward."""

    normalized_assignment_id = normalized_assignment_operation_id(assignment_id)
    key = f"{ROOT.resolve(strict=False)}::{normalized_assignment_id}"
    with _ASSIGNMENT_OPERATION_LOCKS_GUARD:
        entry = _ASSIGNMENT_OPERATION_LOCKS.setdefault(
            key,
            {"lock": threading.Lock(), "users": 0},
        )
        entry["users"] += 1
    lock = entry["lock"]
    acquired = lock.acquire(blocking=blocking)
    if not acquired:
        with _ASSIGNMENT_OPERATION_LOCKS_GUARD:
            entry["users"] -= 1
            if entry["users"] == 0 and _ASSIGNMENT_OPERATION_LOCKS.get(key) is entry:
                _ASSIGNMENT_OPERATION_LOCKS.pop(key, None)
        raise StudentHelpBusyError("Una richiesta di aiuto per questa consegna e gia in elaborazione.")
    try:
        yield
    finally:
        lock.release()
        with _ASSIGNMENT_OPERATION_LOCKS_GUARD:
            entry["users"] -= 1
            if entry["users"] == 0 and _ASSIGNMENT_OPERATION_LOCKS.get(key) is entry:
                _ASSIGNMENT_OPERATION_LOCKS.pop(key, None)


def student_help_provider() -> StudentHelpProvider:
    """Return the server-side provider selected for student help."""

    local_provider = DeterministicStudentHelpProvider()
    provider_name = os.environ.get("THEBITLAB_STUDENT_HELP_PROVIDER", "codex").strip().lower()
    if provider_name in {"local", "deterministic-local"}:
        return local_provider
    if provider_name != "codex":
        raise StudentHelpConfigurationError("Provider aiuto studente non supportato.")
    codex_provider = student_help_codex_adapter.CodexStudentHelpProvider(
        codex_command=os.environ.get("CODEX_COMMAND", "codex"),
        model=os.environ.get("THEBITLAB_STUDENT_HELP_CODEX_MODEL", ""),
    )
    ai_provider = student_help_codex_adapter.FallbackStudentHelpProvider(codex_provider, local_provider)
    return student_help_codex_adapter.StudentHelpProviderRouter(ai_provider, local_provider)


def teacher_dashboard_token() -> str:
    """Return a robust configured or generated teacher credential."""

    configured = os.environ.get("THEBITLAB_TEACHER_TOKEN", "").strip()
    if configured:
        if len(configured) < MIN_TEACHER_TOKEN_CHARS:
            raise ValueError(
                f"THEBITLAB_TEACHER_TOKEN deve contenere almeno {MIN_TEACHER_TOKEN_CHARS} caratteri."
            )
        return configured
    return secrets.token_urlsafe(24)


def teacher_dashboard_token_console_line(token: str, configured: bool) -> str:
    """Return a startup line without disclosing a persistent credential."""

    if configured:
        return "Token dashboard: configurato tramite THEBITLAB_TEACHER_TOKEN (valore non mostrato)"
    return f"Token dashboard temporaneo: {token}"


def student_help_operation_id(assignment_id: str, student_id: str) -> str:
    """Return the per-student admission key for one assignment help request."""

    return f"help::{assignment_id}::{student_id}"


def unique_student_help_operation_ids(assignment_id: str, student_ids: set[str]) -> list[str]:
    """Return one operation id for each effective lock key."""

    operations: dict[str, str] = {}
    for student_id in sorted(student_ids):
        operation_id = student_help_operation_id(assignment_id, student_id)
        operations.setdefault(normalized_assignment_operation_id(operation_id), operation_id)
    return list(operations.values())


def record_student_help(payload: dict[str, Any], *, student_id: str) -> dict[str, Any]:
    """Record one TUI request using server-owned assignment context and policy."""

    assignment_id = str(payload.get("assignment_id", "")).strip()
    request_kwargs = {
        "root": ROOT,
        "assignments_dir": TEACHER_ASSIGNMENTS_DIR,
        "student_id": student_id,
        "assignment_id": assignment_id,
        "help_type": payload.get("help_type", ""),
        "prompt": payload.get("prompt", ""),
        "request_id": payload.get("request_id", ""),
    }
    try:
        with assignment_operation_lock(
            student_help_operation_id(assignment_id, student_id),
            blocking=False,
        ):
            event = student_lab_service.record_student_help_request(
                **request_kwargs,
                provider=DeterministicStudentHelpProvider(),
                provider_factory=student_help_provider,
            )
    except StudentHelpBusyError:
        try:
            event = student_lab_service.record_student_help_request(
                **request_kwargs,
                provider=DeterministicStudentHelpProvider(),
                existing_only=True,
            )
        except student_help_service.StudentHelpRequestNotFoundError:
            raise StudentHelpBusyError("Richiesta di aiuto gia in elaborazione per questa consegna.") from None
    return {"ok": True, "event": event}


def configure_data_root(root: Path) -> Path:
    """Configure the repository data root used by API endpoints."""

    global ROOT
    global DESIGN_PATH
    global COURSE_DESIGNS_DIR
    global SCHOOL_CALENDARS_DIR
    global TEACHER_REPORTS_DIR
    global TEACHER_ASSIGNMENTS_DIR
    global ACTIVITY_DIRS
    global COURSE_PLAN_MD_PATH
    global README_PATH
    global AI_PROVIDERS_PATH
    global AI_SECRET_PATH
    global LEGACY_AI_SECRET_PATH

    ROOT = root.resolve(strict=False)
    DESIGN_PATH = ROOT / "doc" / "course_design.json"
    COURSE_DESIGNS_DIR = ROOT / "doc" / "course_designs"
    SCHOOL_CALENDARS_DIR = ROOT / "doc" / "calendars"
    TEACHER_REPORTS_DIR = ROOT / "teacher-reports"
    TEACHER_ASSIGNMENTS_DIR = ROOT / "teacher-assignments"
    ACTIVITY_DIRS = [ROOT / "activities", ROOT / "examples" / "assignment_tracking"]
    COURSE_PLAN_MD_PATH = ROOT / "doc" / "PERCORSO_DIDATTICO.md"
    README_PATH = ROOT / "README.md"
    AI_PROVIDERS_PATH = ROOT / "config" / "ai_providers.yaml"
    AI_SECRET_PATH = ROOT / ".secrets" / "ai.secret"
    LEGACY_AI_SECRET_PATH = ROOT / "scripts" / ".secrets" / "ai.secret"
    recover_interrupted_assignment_deletions()
    return ROOT


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


def assignment_record_storage() -> assignment_records.JsonAssignmentRecordStorage:
    """Return the JSON storage adapter for explicit assignment records."""

    return assignment_records.JsonAssignmentRecordStorage(ROOT, TEACHER_ASSIGNMENTS_DIR)


def assignment_record_operation_id(
    storage: assignment_records.JsonAssignmentRecordStorage,
    assignment_id: str,
) -> str:
    """Return the lock identity shared by every alias of one record path."""

    return f"assignment-record:{storage.safe_assignment_path(assignment_id)}"


def class_roster_storage() -> thebitlab_storage.JsonClassRosterStorage:
    """Return the JSON storage adapter for local class rosters."""

    return thebitlab_storage.JsonClassRosterStorage(ROOT)


def class_roster_service() -> thebitlab_services.ClassRosterService:
    """Return the application service for class/student rosters."""

    return thebitlab_services.ClassRosterService(class_roster_storage())


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
    """Generate doc/PERCORSO_DIDATTICO.md without promoting the edited design."""

    temporary_root = ROOT / "tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="course-plan-", dir=temporary_root) as directory:
        workdir = Path(directory)
        input_path = workdir / "course_design.json"
        output_path = workdir / COURSE_PLAN_MD_PATH.name
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        command = [
            sys.executable,
            str(ROOT / "scripts" / "generate_course_plan.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode:
            detail = (
                completed.stderr
                or completed.stdout
                or "Errore sconosciuto durante la generazione del percorso MD."
            ).strip()
            raise RuntimeError(detail)
        COURSE_PLAN_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        os.replace(output_path, COURSE_PLAN_MD_PATH)
    return {
        "ok": True,
        "markdown_path": str(COURSE_PLAN_MD_PATH.relative_to(ROOT)),
        "message": (completed.stdout or "").strip(),
    }


def update_readme_frames(payload: dict) -> dict:
    """Update README didactic frames without promoting the edited design."""

    temporary_root = ROOT / "tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="readme-frames-", dir=temporary_root) as directory:
        workdir = Path(directory)
        input_path = workdir / "course_design.json"
        target_path = workdir / README_PATH.name
        input_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copy2(README_PATH, target_path)
        command = [
            sys.executable,
            str(ROOT / "scripts" / "update_course_frames.py"),
            "--input",
            str(input_path),
            "--target",
            str(target_path),
        ]
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if completed.returncode:
            detail = (
                completed.stderr
                or completed.stdout
                or "Errore sconosciuto durante l'aggiornamento del README."
            ).strip()
            raise RuntimeError(detail)
        os.replace(target_path, README_PATH)
    return {
        "ok": True,
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


def datetime_now_iso() -> str:
    """Return the current local datetime with timezone for assignment status checks."""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def safe_teacher_report_path(name: str) -> Path:
    """Return a safe teacher-report path below teacher-reports."""

    return assignment_service().safe_teacher_report_path(name)


def list_saved_designs() -> list[dict]:
    """List saved course designs stored in doc/course_designs."""

    return course_service().list_saved_designs()


def read_saved_design(name: str) -> dict:
    """Read a saved course design by filename."""

    return course_service().read_saved_design(name)


def write_saved_design(name: str, payload: dict, overwrite: bool = True) -> dict:
    """Persist a named course design in the archive folder."""

    return course_service().write_saved_design(name, payload, overwrite=overwrite)


def delete_saved_design(name: str, delete_calendars: bool = False, calendars: list[str] | None = None) -> dict:
    """Delete an archived course design and, optionally, its linked calendars."""

    return course_service().delete_saved_design(name, delete_calendars, calendars)


def list_school_calendars() -> list[dict]:
    """List saved school calendars stored in doc/calendars."""

    return course_service().list_school_calendars()


def list_assignment_reports() -> list[dict]:
    """List assignment tracking reports stored in teacher-reports."""

    return assignment_service().list_assignment_reports()


def list_assignment_records(now: str | None = None) -> dict:
    """Return explicit assignment records and those due without register."""

    storage = assignment_storage()
    record_storage = assignment_record_storage()
    registers = []
    for report in storage.list_assignment_reports():
        try:
            registers.append(storage.read_assignment_report(str(report.get("name", ""))))
        except Exception:  # noqa: BLE001
            continue
    current_time = now or datetime_now_iso()
    assignments = record_storage.list_assignments()
    assignment_statuses = [
        assignment_records.assignment_status(assignment, registers, current_time).to_dict()
        for assignment in assignments
    ]
    due_without_register = [status for status in assignment_statuses if status["needs_register"]]
    return {
        "assignments": assignments,
        "assignment_statuses": assignment_statuses,
        "due_without_register": due_without_register,
        "now": current_time,
    }


def locked_student_lab_payload(*, student_id: str, now: str | None = None) -> dict[str, Any]:
    """Build the network-safe student payload without blocking provider calls."""

    return student_lab_service.student_lab_payload(
        root=ROOT,
        assignments_dir=TEACHER_ASSIGNMENTS_DIR,
        student_id=student_id,
        now=now,
    )


def restore_staged_help_logs(staged_logs: list[tuple[Path, Path]]) -> None:
    """Restore quarantined help-log directories in reverse order."""

    for original, staged in reversed(staged_logs):
        if staged.exists():
            original.parent.mkdir(parents=True, exist_ok=True)
            staged.replace(original)
            assignment_records.sync_directory(staged.parent)
            assignment_records.sync_directory(original.parent)


def snapshot_staged_help_logs(
    staged_logs: list[tuple[Path, Path]],
) -> list[tuple[Path, dict[Path, bytes]]]:
    """Read a bounded rollback snapshot before deleting quarantined logs."""

    snapshots: list[tuple[Path, dict[Path, bytes]]] = []
    total_bytes = 0
    for original, staged in staged_logs:
        files: dict[Path, bytes] = {}
        for candidate in staged.rglob("*"):
            if candidate.is_symlink():
                raise ValueError("La quarantena dei log contiene un collegamento simbolico non supportato.")
            if not candidate.is_file():
                continue
            content = candidate.read_bytes()
            total_bytes += len(content)
            if total_bytes > MAX_HELP_LOG_ROLLBACK_BYTES:
                raise ValueError("I log di aiuto superano il limite di rollback per una singola assegnazione.")
            files[candidate.relative_to(staged)] = content
        snapshots.append((original, files))
    return snapshots


def restore_help_log_snapshots(snapshots: list[tuple[Path, dict[Path, bytes]]]) -> None:
    """Recreate complete help-log directories from an in-memory snapshot."""

    for original, files in snapshots:
        original.mkdir(parents=True, exist_ok=True)
        for relative_path, content in files.items():
            destination = original / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        sync_file_tree(original)


def sync_file_tree(root: Path) -> None:
    """Persist a completed file tree before advancing its recovery journal."""

    if not root.is_dir():
        return
    directories = {root}
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"Collegamento simbolico non supportato: {candidate}")
        if candidate.is_dir():
            directories.add(candidate)
            continue
        if candidate.is_file():
            with candidate.open("r+b") as stream:
                os.fsync(stream.fileno())
            directories.add(candidate.parent)
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        assignment_records.sync_directory(directory)
    assignment_records.sync_directory(root.parent)


def update_help_deletion_manifest(trash_root: Path, **updates: Any) -> dict[str, Any]:
    """Atomically update one deletion recovery journal."""

    storage = assignment_records.JsonAssignmentRecordStorage(ROOT)
    manifest_path = help_deletion_manifest_path(trash_root)
    manifest = storage.read_json(manifest_path)
    manifest.update(updates)
    storage.write_json(manifest_path, manifest)
    return manifest


def persist_help_log_rollback(
    trash_root: Path,
    assignment: dict[str, Any],
    snapshots: list[tuple[Path, dict[Path, bytes]]],
) -> None:
    """Persist a complete rollback copy before the assignment record is removed."""

    manifest = assignment_records.JsonAssignmentRecordStorage(ROOT).read_json(
        help_deletion_manifest_path(trash_root)
    )
    logs = manifest.get("logs")
    if not isinstance(logs, list):
        raise RuntimeError("Journal cancellazione incoerente con i log in quarantena.")
    rollback_root = trash_root / "rollback"
    for original, files in snapshots:
        original_relative = str(original.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
        item = next(
            (
                candidate
                for candidate in logs
                if isinstance(candidate, dict) and candidate.get("original") == original_relative
            ),
            None,
        )
        if item is None:
            raise RuntimeError("Journal cancellazione incoerente con i log in quarantena.")
        staged_name = str(item.get("staged", "")).strip()
        if not staged_name.isdigit():
            raise RuntimeError("Path non valido nel journal cancellazione.")
        backup_relative = Path("rollback") / staged_name
        backup_dir = trash_root / backup_relative
        backup_dir.mkdir(parents=True, exist_ok=True)
        for relative_path, content in files.items():
            destination = backup_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        item["rollback"] = str(backup_relative).replace("\\", "/")
    sync_file_tree(rollback_root)
    update_help_deletion_manifest(
        trash_root,
        state="prepared",
        assignment=assignment,
        logs=logs,
    )


def restore_persistent_help_deletion(trash_root: Path, manifest: dict[str, Any]) -> None:
    """Idempotently restore assignment and logs from a rollback journal."""

    assignment = manifest.get("assignment")
    logs = manifest.get("logs")
    if not isinstance(assignment, dict) or not isinstance(logs, list):
        raise RuntimeError(f"Journal rollback non valido: {help_deletion_manifest_path(trash_root)}")
    help_root = (ROOT / "teacher-help-events").resolve(strict=False)
    for item in logs:
        if not isinstance(item, dict):
            raise RuntimeError(f"Journal rollback non valido: {help_deletion_manifest_path(trash_root)}")
        rollback_path = str(item.get("rollback", "")).strip()
        if not rollback_path:
            continue
        original = (ROOT / str(item.get("original", ""))).resolve(strict=False)
        backup = (trash_root / rollback_path).resolve(strict=False)
        try:
            original_relative = original.relative_to(help_root)
            backup_relative = backup.relative_to(trash_root.resolve(strict=False))
        except ValueError as error:
            raise RuntimeError(f"Path non valido nel journal: {help_deletion_manifest_path(trash_root)}") from error
        if not original_relative.parts or len(backup_relative.parts) < 2 or backup_relative.parts[0] != "rollback":
            raise RuntimeError(f"Path non valido nel journal: {help_deletion_manifest_path(trash_root)}")
        if not backup.is_dir():
            raise RuntimeError(f"Copia di rollback mancante: {backup}")
        if original.exists():
            shutil.rmtree(original)
        shutil.copytree(backup, original)
        sync_file_tree(original)
    assignment_record_storage().write_assignment(assignment, overwrite=True)
    update_help_deletion_manifest(trash_root, state="restored")


def help_deletion_manifest_path(trash_root: Path) -> Path:
    """Return the persistent recovery journal for one deletion."""

    return trash_root / "deletion.json"


def purge_help_deletion_trash(trash_root: Path, *, ignore_errors: bool = False) -> None:
    """Remove transaction data while keeping the recovery journal until last."""

    try:
        manifest_path = help_deletion_manifest_path(trash_root)
        if trash_root.is_dir():
            for child in list(trash_root.iterdir()):
                if child == manifest_path:
                    continue
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
            assignment_records.sync_directory(trash_root)
            trash_root.rmdir()
            assignment_records.sync_directory(trash_root.parent)
    except OSError:
        if not ignore_errors:
            raise


def stage_help_logs_for_deletion(
    assignment_id: str,
    log_dirs: list[Path],
) -> tuple[Path, list[tuple[Path, Path]]]:
    """Move help logs to a private same-volume quarantine before record deletion."""

    help_events_root = ROOT / "teacher-help-events"
    help_events_root.mkdir(parents=True, exist_ok=True)
    assignment_records.sync_directory(help_events_root.parent)
    trash_base = help_events_root / ".trash"
    trash_base.mkdir(parents=True, exist_ok=True)
    assignment_records.sync_directory(trash_base.parent)
    trash_root = trash_base / uuid.uuid4().hex
    staged_logs: list[tuple[Path, Path]] = []
    planned_logs = []
    for index, log_dir in enumerate(log_dirs):
        try:
            original = log_dir.resolve(strict=False).relative_to(ROOT.resolve(strict=False))
        except ValueError as error:
            raise ValueError("Il log da cancellare deve trovarsi nella root dati.") from error
        planned_logs.append({"original": str(original).replace("\\", "/"), "staged": str(index)})
    assignment_records.JsonAssignmentRecordStorage(ROOT).write_json(
        help_deletion_manifest_path(trash_root),
        {
            "schema_version": HELP_DELETION_SCHEMA_VERSION,
            "state": "staging",
            "assignment_id": assignment_id,
            "logs": planned_logs,
        },
    )
    assignment_records.sync_directory(trash_base)
    try:
        for index, log_dir in enumerate(log_dirs):
            if not log_dir.is_dir():
                continue
            staged = trash_root / str(index)
            staged.parent.mkdir(parents=True, exist_ok=True)
            log_dir.replace(staged)
            assignment_records.sync_directory(log_dir.parent)
            assignment_records.sync_directory(staged.parent)
            staged_logs.append((log_dir, staged))
    except Exception:
        restore_staged_help_logs(staged_logs)
        purge_help_deletion_trash(trash_root, ignore_errors=True)
        raise
    return trash_root, staged_logs


def recover_interrupted_assignment_deletions() -> None:
    """Recover or complete journaled help-log deletions after a server restart."""

    trash_base = ROOT / "teacher-help-events" / ".trash"
    if not trash_base.is_dir():
        return
    storage = assignment_record_storage()
    help_root = (ROOT / "teacher-help-events").resolve(strict=False)
    for trash_root in sorted(path for path in trash_base.iterdir() if path.is_dir()):
        manifest_path = help_deletion_manifest_path(trash_root)
        if not manifest_path.is_file():
            if not any(trash_root.iterdir()):
                trash_root.rmdir()
                assignment_records.sync_directory(trash_root.parent)
                continue
            raise RuntimeError(f"Quarantena senza journal: {trash_root}")
        manifest = storage.read_json(manifest_path)
        schema_version = manifest.get("schema_version")
        if schema_version not in {"student_help_deletion.v1", HELP_DELETION_SCHEMA_VERSION}:
            raise RuntimeError(f"Journal cancellazione non supportato: {manifest_path}")
        assignment_id = str(manifest.get("assignment_id", "")).strip()
        logs = manifest.get("logs")
        if not assignment_id or not isinstance(logs, list):
            raise RuntimeError(f"Journal cancellazione non valido: {manifest_path}")
        state = "staging" if schema_version == "student_help_deletion.v1" else str(manifest.get("state", ""))
        if state == "rolling_back":
            restore_persistent_help_deletion(trash_root, manifest)
            purge_help_deletion_trash(trash_root)
            continue
        if state in {"restored", "committed"}:
            purge_help_deletion_trash(trash_root)
            continue
        if state not in {"staging", "prepared"}:
            raise RuntimeError(f"Stato journal cancellazione non supportato: {manifest_path}")
        assignment_exists = storage.safe_assignment_path(assignment_id).is_file()
        if assignment_exists:
            for item in logs:
                if not isinstance(item, dict):
                    raise RuntimeError(f"Journal cancellazione non valido: {manifest_path}")
                original = (ROOT / str(item.get("original", ""))).resolve(strict=False)
                staged = (trash_root / str(item.get("staged", ""))).resolve(strict=False)
                try:
                    original_relative = original.relative_to(help_root)
                    staged_relative = staged.relative_to(trash_root.resolve(strict=False))
                except ValueError as error:
                    raise RuntimeError(f"Path non valido nel journal: {manifest_path}") from error
                if (
                    not original_relative.parts
                    or len(staged_relative.parts) != 1
                    or not staged_relative.parts[0].isdigit()
                ):
                    raise RuntimeError(f"Path non valido nel journal: {manifest_path}")
                if staged.is_dir():
                    if original.exists():
                        shutil.copytree(staged, original, dirs_exist_ok=True)
                        shutil.rmtree(staged)
                    else:
                        original.parent.mkdir(parents=True, exist_ok=True)
                        staged.replace(original)
                    sync_file_tree(original)
        purge_help_deletion_trash(trash_root)
    try:
        trash_base.rmdir()
    except OSError:
        pass


def rollback_help_deletion(
    trash_root: Path,
    assignment: dict[str, Any],
    snapshots: list[tuple[Path, dict[Path, bytes]]],
) -> None:
    """Restore one failed deletion while leaving a recoverable journal on interruption."""

    update_help_deletion_manifest(trash_root, state="rolling_back")
    restore_help_log_snapshots(snapshots)
    assignment_record_storage().write_assignment(assignment, overwrite=True)
    update_help_deletion_manifest(trash_root, state="restored")
    purge_help_deletion_trash(trash_root, ignore_errors=True)


def delete_assignment_record(payload: dict) -> dict:
    """Delete one assignment, including its authoritative student help logs."""

    requested_assignment_id = str(payload.get("assignment_id", "")).strip()
    if not requested_assignment_id:
        raise ValueError("assignment_id obbligatorio.")
    record_storage = assignment_record_storage()
    with ExitStack() as assignment_locks:
        assignment_locks.enter_context(assignment_operation_lock(ASSIGNMENT_TARGET_BINDINGS_OPERATION_ID))
        assignment_locks.enter_context(
            assignment_operation_lock(assignment_record_operation_id(record_storage, requested_assignment_id))
        )
        try:
            assignment = record_storage.read_assignment(requested_assignment_id)
        except FileNotFoundError:
            updated = list_assignment_records(str(payload.get("now", "")).strip() or None)
            return {
                "ok": True,
                "deleted": {"id": requested_assignment_id},
                "already_deleted": True,
                "cleanup_pending": False,
                **updated,
            }
        assignment_id = str(assignment["id"])
        student_ids = set()
        for target in assignment.get("targets", []):
            if isinstance(target, dict):
                student_ids.update(student_lab_service.target_cleanup_student_ids(target))
        log_paths = sorted(
            {
                student_help_service.server_help_log_path(ROOT, student_id, assignment_id)
                for student_id in student_ids
            },
            key=str,
        )
        with ExitStack() as help_operations:
            for operation_id in unique_student_help_operation_ids(assignment_id, student_ids):
                help_operations.enter_context(
                    assignment_operation_lock(operation_id)
                )
            with ExitStack() as log_locks:
                for log_path in log_paths:
                    log_locks.enter_context(student_help_service.help_log_lock(log_path))
                trash_root, staged_logs = stage_help_logs_for_deletion(
                    assignment_id,
                    [log_path.parent for log_path in log_paths]
                )
                try:
                    rollback_snapshots = snapshot_staged_help_logs(staged_logs)
                    persist_help_log_rollback(trash_root, assignment, rollback_snapshots)
                except Exception:
                    restore_staged_help_logs(staged_logs)
                    purge_help_deletion_trash(trash_root, ignore_errors=True)
                    raise
                try:
                    deleted = record_storage.delete_assignment(assignment_id)
                except Exception:
                    rollback_help_deletion(trash_root, assignment, rollback_snapshots)
                    raise
                try:
                    for _, staged in staged_logs:
                        if staged.exists():
                            shutil.rmtree(staged)
                    update_help_deletion_manifest(trash_root, state="committed")
                except Exception:
                    rollback_help_deletion(trash_root, assignment, rollback_snapshots)
                    raise
                cleanup_pending = False
                try:
                    purge_help_deletion_trash(trash_root)
                except OSError:
                    cleanup_pending = True
    updated = list_assignment_records(str(payload.get("now", "")).strip() or None)
    return {
        "ok": True,
        "deleted": deleted,
        "already_deleted": False,
        "cleanup_pending": cleanup_pending,
        **updated,
    }


def repository_relative_path(path: Path) -> str:
    """Return a repository-relative path where possible."""

    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def ensure_activity_draft_path(path: Path) -> None:
    """Reject deletion targets outside activities/drafts."""

    drafts_dir = (ROOT / "activities" / "drafts").resolve()
    try:
        path.resolve().relative_to(drafts_dir)
    except ValueError as error:
        raise ValueError("Puoi cancellare solo bozze activity dentro activities/drafts.") from error


def activity_delete_dependencies(activity_path: Path, activity: dict) -> dict:
    """Return assignments and registers that still reference an activity."""

    activity_id = str(activity.get("id", "")).strip()
    relative_activity_path = repository_relative_path(activity_path.resolve())
    assignments = []
    for assignment in assignment_record_storage().list_assignments():
        assignment_activity_id = str(assignment.get("activity_id", "")).strip()
        assignment_activity_path = str(assignment.get("activity_path", "")).strip().replace("\\", "/")
        if (activity_id and assignment_activity_id == activity_id) or assignment_activity_path == relative_activity_path:
            assignments.append(
                {
                    "id": assignment.get("id", ""),
                    "activity_id": assignment_activity_id,
                    "activity_path": assignment_activity_path,
                    "target_type": assignment.get("target_type", ""),
                    "class_id": assignment.get("class_id", ""),
                    "github_team": assignment.get("github_team", ""),
                    "due_at": assignment.get("due_at", ""),
                }
            )

    storage = assignment_storage()
    reports = []
    for report_summary in storage.list_assignment_reports():
        name = str(report_summary.get("name", "")).strip()
        if not name:
            continue
        try:
            report = storage.read_assignment_report(name)
        except Exception:  # noqa: BLE001
            continue
        report_activity_id = str(report.get("activity_id", "")).strip()
        report_activity_path = str(report.get("activity_path", "")).strip().replace("\\", "/")
        if (activity_id and report_activity_id == activity_id) or report_activity_path == relative_activity_path:
            reports.append(
                {
                    "name": name,
                    "activity_id": report_activity_id,
                    "assignment_id": report.get("assignment_id", ""),
                    "class_id": report.get("class_id", ""),
                    "github_team": report.get("github_team", ""),
                    "due_at": report.get("due_at", ""),
                }
            )
    return {"assignments": assignments, "reports": reports}


def delete_activity_record(payload: dict) -> dict:
    """Delete one unlinked teacher-authored activity draft."""

    activity_path = resolve_local_path(str(payload.get("activity_path", "")), "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    ensure_activity_draft_path(activity_path)
    storage = assignment_storage()
    activity = normalize_activity(storage.read_json(activity_path))
    dependencies = activity_delete_dependencies(activity_path, activity)
    if dependencies["assignments"] or dependencies["reports"]:
        assignment_count = len(dependencies["assignments"])
        report_count = len(dependencies["reports"])
        raise ValueError(
            "Activity collegata a "
            f"{assignment_count} assegnazioni e {report_count} registri: cancellazione bloccata. "
            "Cancella prima le assegnazioni o i registri collegati."
        )
    deleted = {
        "id": activity.get("id", ""),
        "title": activity.get("title", ""),
        "path": repository_relative_path(activity_path),
    }
    activity_path.unlink()
    return {"ok": True, "deleted": deleted, "dependencies": dependencies, "activities": list_activities()}


def list_class_rosters() -> list[dict]:
    """List local class rosters stored in doc/classes."""

    return class_roster_service().list_class_rosters()


def read_class_roster(name: str) -> dict:
    """Read one local class roster from doc/classes."""

    return class_roster_service().read_class_roster(name)


def enrich_assignment_report_help(report: dict) -> dict:
    """Attach current authoritative help summaries to one assignment report."""

    assignment_id = str(report.get("assignment_id", "")).strip()
    students = report.get("students") if isinstance(report.get("students"), list) else []
    if not assignment_id:
        return report
    for student in students:
        if not isinstance(student, dict):
            continue
        student_id = str(student.get("student_id", "") or student.get("student", "")).strip()
        if not student_id:
            continue
        previous_help = student.get("help") if isinstance(student.get("help"), dict) else {}
        log_path = student_help_service.server_help_log_path(ROOT, student_id, assignment_id)
        current_help = student_help_service.teacher_help_summary(log_path)
        current_help["path"] = str(log_path.relative_to(ROOT)).replace("\\", "/")
        current_help["activity_id"] = str(report.get("activity_id", "")).strip()
        for key in ("legacy_unverified", "legacy_path", "legacy"):
            if key in previous_help:
                current_help[key] = previous_help[key]
        student["help"] = current_help
    return report


def read_assignment_report(name: str) -> dict:
    """Read one assignment tracking report from teacher-reports."""

    return enrich_assignment_report_help(assignment_service().read_assignment_report(name))


def assignment_report_operation_id(
    storage: thebitlab_storage.JsonAssignmentStorage,
    name: str,
) -> str:
    """Return the canonical lock identity shared by mutations of one report."""

    report_path = storage.safe_teacher_report_path(name)
    return f"assignment-report::{os.path.normcase(str(report_path))}"


def preserve_assignment_ai_feedback(previous: dict, generated: dict) -> dict:
    """Keep meaningful AI feedback when regenerating the same assignment report."""

    previous_activity = str(previous.get("activity_id", "")).strip()
    generated_activity = str(generated.get("activity_id", "")).strip()
    if not previous_activity or previous_activity != generated_activity:
        return generated
    previous_assignment = str(previous.get("assignment_id", "")).strip()
    generated_assignment = str(generated.get("assignment_id", "")).strip()
    if previous_assignment != generated_assignment:
        return generated

    previous_students = previous.get("students") if isinstance(previous.get("students"), list) else []
    by_student_id = {}
    by_student_name = {}
    for student in previous_students:
        if not isinstance(student, dict):
            continue
        student_id = str(student.get("student_id", "")).strip()
        student_name = str(student.get("student", "")).strip()
        if student_id:
            by_student_id.setdefault(student_id, student)
        if student_name:
            by_student_name.setdefault(student_name, student)

    generated_students = generated.get("students") if isinstance(generated.get("students"), list) else []
    for student in generated_students:
        if not isinstance(student, dict):
            continue
        student_id = str(student.get("student_id", "")).strip()
        student_name = str(student.get("student", "")).strip()
        previous_student = by_student_id.get(student_id) if student_id else None
        if previous_student is None and student_name:
            previous_student = by_student_name.get(student_name)
        if previous_student is None:
            continue
        feedback = previous_student.get("ai_feedback")
        if not isinstance(feedback, dict):
            continue
        status = str(feedback.get("status", "")).strip()
        if not status or status == "not_generated":
            continue
        student["ai_feedback"] = deepcopy(feedback)
    return generated


def review_assignment_ai_feedback(name: str, student_id: str, decision: str) -> dict:
    """Apply a teacher review decision to draft AI feedback in a report."""

    storage = assignment_storage()
    with assignment_operation_lock(assignment_report_operation_id(storage, name)):
        register = storage.read_assignment_report(name)
        updated = manual_ai_feedback.review_feedback_in_register(register, student_id, decision)
        saved = storage.write_assignment_report(name, updated)
        return enrich_assignment_report_help(saved)


def assignment_overview() -> list[dict]:
    """Return one row per student/activity across all saved teacher reports."""

    return assignment_service().assignment_overview()


def student_dashboard(student_id: str) -> dict:
    """Return the minimal student-facing assignment dashboard."""

    dashboard = assignment_service().student_dashboard(student_id)
    try:
        dashboard["lab"] = locked_student_lab_payload(student_id=student_id)
    except Exception as error:  # noqa: BLE001
        dashboard["lab"] = {
            "schema_version": "student_lab.v1",
            "student_id": str(student_id or "").strip(),
            "assignments": [],
            "error": str(error),
        }
    return dashboard


def list_activities() -> list[dict]:
    """List available activity JSON files for the assignment dashboard."""

    return assignment_service().list_activities()


def save_activity(payload: dict) -> dict:
    """Create and persist a teacher-authored activity draft."""

    title = str(payload.get("title", "")).strip()
    activity_id = str(payload.get("id", "")).strip() or create_activity.slugify(title)
    topics = create_activity.parse_topics(str(payload.get("topics", "")))
    activity = create_activity.build_activity(
        activity_id=activity_id,
        title=title,
        activity_type=str(payload.get("kind", "")).strip(),
        difficulty=str(payload.get("difficulty", "")).strip(),
        topics=topics,
        prompt=str(payload.get("prompt", "")).strip(),
        estimated_minutes=create_activity.positive_int(str(payload.get("estimated_minutes", "30"))),
        language=create_submission_scaffold.validate_language(str(payload.get("language", "c") or "c")),
        source_name=create_submission_scaffold.validate_source_name(str(payload.get("source_name", "main.c") or "main.c")),
        context={
            "classe": str(payload.get("class_id", "")).strip(),
            "team_github": str(payload.get("github_team", "")).strip(),
            "percorso": str(payload.get("path_id", "")).strip(),
            "uda": str(payload.get("uda_id", "")).strip(),
        },
    )
    saved = assignment_service().save_activity(activity, bool(payload.get("overwrite", False)))
    return {"ok": True, "activity": saved, "activities": list_activities()}


def legacy_submission_repo_path(student: dict) -> Path | None:
    """Infer an old local repo root from its recorded grading report path."""

    trusted_root = ROOT.resolve(strict=False)
    repo_ref = str(student.get("repo", "")).strip().replace("\\", "/").rstrip("/")
    repo_name = repo_ref.rsplit("/", 1)[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    if not repo_name:
        return None
    submission = student.get("submission") if isinstance(student.get("submission"), dict) else {}
    report_references = {
        normalized_submission_file_reference(student.get("report_path")),
        normalized_submission_file_reference(submission.get("report_path")),
    }
    report_references.discard("")
    for reference in report_references:
        raw_path = Path(reference)
        candidates = [raw_path.resolve()] if raw_path.is_absolute() else [
            (ROOT / raw_path).resolve(),
            (APP_ROOT / raw_path).resolve(),
            (ROOT / repo_name / raw_path).resolve(),
        ]
        for candidate in candidates:
            if candidate != trusted_root and not candidate.is_relative_to(trusted_root):
                continue
            if not candidate.is_file():
                continue
            for parent in candidate.parents:
                if parent.name.casefold() != "reports":
                    continue
                inferred_repo = parent.parent
                if inferred_repo.name.casefold() == repo_name.casefold():
                    return inferred_repo
    return None


def normalized_submission_file_reference(value: Any) -> str:
    """Return a comparable register reference for one submitted file."""

    normalized = str(value or "").strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def registered_submission_file_references(student: dict) -> set[str]:
    """Return the file references explicitly recorded for one submission."""

    submission = student.get("submission") if isinstance(student.get("submission"), dict) else {}
    references = {
        normalized_submission_file_reference(submission.get("source_path")),
    }
    files = submission.get("files") if isinstance(submission.get("files"), list) else []
    for entry in files:
        value = entry.get("path") or entry.get("source_path") if isinstance(entry, dict) else entry
        references.add(normalized_submission_file_reference(value))
    references.discard("")
    return references


def resolve_submission_file_path(student: dict, file_path: str) -> Path:
    """Resolve a submitted file path while keeping reads inside the student repo."""

    requested_reference = normalized_submission_file_reference(file_path)
    if requested_reference not in registered_submission_file_references(student):
        raise FileNotFoundError(f"File consegna non trovato o non consentito: {file_path}")
    explicit_repo_path = str(student.get("repo_path", "")).strip()
    repo_value = explicit_repo_path or str(student.get("repo", "")).strip()
    repo = Path(repo_value)
    if not str(repo):
        raise ValueError("Repository studente mancante nel registro.")
    repo_path = repo if repo.is_absolute() else (ROOT / repo).resolve()
    legacy_repo_path = None if explicit_repo_path or repo_path.is_dir() else legacy_submission_repo_path(student)
    raw_path = Path(str(file_path).strip())
    if not str(raw_path):
        raise ValueError("File consegna non indicato.")
    candidates = []
    if raw_path.is_absolute():
        candidates.append(raw_path.resolve())
    else:
        candidates.append((ROOT / raw_path).resolve())
        candidates.append((APP_ROOT / raw_path).resolve())
        candidates.append((repo_path / raw_path).resolve())
    for candidate in candidates:
        allowed_repo_paths = [repo_path]
        if legacy_repo_path is not None:
            allowed_repo_paths.append(legacy_repo_path)
        if not any(candidate == allowed or candidate.is_relative_to(allowed) for allowed in allowed_repo_paths):
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


def read_assignment_target_paths_from_text(targets_text: str) -> list[Path]:
    """Build assignment target repository paths from one path per line."""

    targets = []
    for raw_line in targets_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        targets.append(resolve_local_path(line, "target"))
    if not targets:
        raise ValueError("Inserisci almeno un repository studente nei target.")
    return targets


def assignment_record_targets_from_text(targets_text: str) -> list[dict]:
    """Build explicit assignment targets from one local repository path per line."""

    targets = []
    for target_path in read_assignment_target_paths_from_text(targets_text):
        try:
            clean_path = str(target_path.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            clean_path = str(target_path)
        targets.append({
            "student_id": target_path.name,
            "display_name": target_path.name,
            "path": clean_path,
        })
    return targets


def infer_assignment_target_type(class_id: str, github_team: str, targets: list[dict]) -> str:
    """Infer the assignment target type from the current dashboard fields."""

    if class_id:
        return "class"
    if github_team:
        return "team"
    if len(targets) == 1:
        return "student"
    return "group"


def assignment_target_student_ids(assignment: dict[str, Any]) -> set[str]:
    """Return canonical student identities referenced by one assignment."""

    return {
        student_id
        for target in assignment.get("targets", [])
        if isinstance(target, dict)
        for student_id in [student_lab_service.target_student_id(target)]
        if student_id
    }


def assignment_target_bindings(assignment: dict[str, Any]) -> dict[str, str]:
    """Return one unambiguous repository binding for every student identity."""

    bindings: dict[str, str] = {}
    for target in assignment.get("targets", []):
        if not isinstance(target, dict):
            continue
        student_id = student_lab_service.target_student_id(target)
        repo_path = student_lab_service.target_repo_path(ROOT, target, student_id)
        if not student_id or repo_path is None:
            raise ValueError("Destinatario senza identita o repository valido.")
        binding = os.path.normcase(str(repo_path.resolve(strict=False)))
        previous = bindings.setdefault(student_id, binding)
        if previous != binding:
            raise ValueError(
                f"Identificativo studente ambiguo: {student_id} e associato a repository diversi."
            )
    return bindings


def validate_global_assignment_target_bindings(
    storage: assignment_records.JsonAssignmentRecordStorage,
    assignment: dict[str, Any],
) -> dict[str, str]:
    """Reject reuse of one student identity for a different repository."""

    new_bindings = assignment_target_bindings(assignment)
    for existing in storage.list_assignments():
        if existing.get("id") == assignment.get("id"):
            continue
        for student_id, binding in assignment_target_bindings(existing).items():
            if student_id in new_bindings and new_bindings[student_id] != binding:
                raise ValueError(
                    f"Identificativo studente gia associato a un altro repository: {student_id}."
                )
    return new_bindings


def save_assignment_record(payload: dict) -> dict:
    """Persist an explicit assignment record from the teacher dashboard."""

    activity_path_value = str(payload.get("activity_path", "")).strip()
    activity_path = resolve_local_path(activity_path_value, "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    activity = normalize_activity(assignment_storage().read_json(activity_path))
    activity_id = str(activity.get("id", "")).strip()
    if not activity_id:
        raise ValueError("Activity senza id.")
    targets = assignment_record_targets_from_text(str(payload.get("targets_text", "")))
    class_id = str(payload.get("class_id", "")).strip()
    github_team = str(payload.get("github_team", "")).strip()
    assignment = assignment_records.build_assignment_record(
        activity_id=activity_id,
        activity_path=activity_path_value.replace("\\", "/"),
        target_type=str(payload.get("target_type", "")).strip() or infer_assignment_target_type(class_id, github_team, targets),
        class_id=class_id,
        class_label=str(payload.get("class_label", "")).strip(),
        github_team=github_team,
        assigned_at=str(payload.get("assigned_at", "")).strip(),
        due_at=str(payload.get("due_at", "")).strip(),
        targets=targets,
    )
    overwrite = bool(payload.get("overwrite", False))
    storage = assignment_record_storage()
    with assignment_operation_lock(ASSIGNMENT_TARGET_BINDINGS_OPERATION_ID):
        with assignment_operation_lock(assignment_record_operation_id(storage, assignment["id"])):
            new_bindings = validate_global_assignment_target_bindings(storage, assignment)
            if overwrite:
                try:
                    existing = storage.read_assignment(assignment["id"])
                except FileNotFoundError:
                    existing = None
                if existing is not None and assignment_target_bindings(existing) != new_bindings:
                    raise ValueError(
                        "I destinatari o i repository di un'assegnazione esistente non sono modificabili: "
                        "cancella l'assegnazione e creane una nuova."
                    )
            saved = storage.write_assignment(assignment, overwrite)
    records = list_assignment_records(str(payload.get("now", "")).strip() or None)
    return {
        "ok": True,
        "assignment": saved,
        **records,
    }


def preview_activity_assignment(payload: dict) -> dict:
    """Return a write-free assignment plan for the local GUI."""

    activity_path = resolve_local_path(payload.get("activity_path", ""), "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    targets = read_assignment_target_paths_from_text(str(payload.get("targets_text", "")))
    plan = assign_activity.build_assignment_plan(
        activity_path=activity_path,
        targets=targets,
        source_name=payload.get("source_name") or None,
        language=payload.get("language") or None,
        thebitlab_ref=payload.get("thebitlab_ref") or create_submission_scaffold.DEFAULT_THEBITLAB_REF,
        overwrite=bool(payload.get("overwrite", False)),
    )
    return {"ok": True, "plan": plan.to_dict()}


def preview_activity_ai_package(payload: dict) -> dict:
    """Return the write-free AI package for the selected activity and targets."""

    activity_path = resolve_local_path(payload.get("activity_path", ""), "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    targets = read_assignment_target_paths_from_text(str(payload.get("targets_text", "")))
    package = activity_ai_package.build_activity_ai_package(
        activity_path=activity_path,
        targets=targets,
        prompt=str(payload.get("prompt", "")),
        provider=str(payload.get("provider", "codex")),
        student_budget=int(payload.get("student_budget", 0) or 0),
        integrity_mode=str(payload.get("integrity_mode", "normal")),
        source_name=payload.get("source_name") or None,
        language=payload.get("language") or None,
        thebitlab_ref=payload.get("thebitlab_ref") or create_submission_scaffold.DEFAULT_THEBITLAB_REF,
    )
    current_draft = payload.get("current_draft")
    if isinstance(current_draft, dict):
        package["current_draft"] = current_draft
    return {"ok": True, "package": package}


def preview_activity_ai_codex_draft(payload: dict) -> dict:
    """Return a teacher-editable activity draft generated by local Codex."""

    package = preview_activity_ai_package(payload)["package"]
    result = codex_activity_adapter.run_codex_activity_draft(
        package,
        cwd=ROOT,
        codex_command=os.environ.get("CODEX_COMMAND", "codex").strip() or "codex",
    )
    return {"ok": True, "package": package, **result}


def distribute_activity_assignment(payload: dict) -> dict:
    """Create activity scaffolds in the selected local target repositories."""

    activity_path = resolve_local_path(payload.get("activity_path", ""), "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    targets = read_assignment_target_paths_from_text(str(payload.get("targets_text", "")))
    results = assign_activity.assign_activity_to_targets(
        activity_path=activity_path,
        targets=targets,
        source_name=payload.get("source_name") or None,
        language=payload.get("language") or None,
        thebitlab_ref=payload.get("thebitlab_ref") or create_submission_scaffold.DEFAULT_THEBITLAB_REF,
        overwrite=bool(payload.get("overwrite", False)),
        overwrite_source=bool(payload.get("overwrite_source", False)),
    )
    plan = assign_activity.build_assignment_plan(
        activity_path=activity_path,
        targets=targets,
        source_name=payload.get("source_name") or None,
        language=payload.get("language") or None,
        thebitlab_ref=payload.get("thebitlab_ref") or create_submission_scaffold.DEFAULT_THEBITLAB_REF,
        overwrite=bool(payload.get("overwrite", False)),
    )
    return {
        "ok": True,
        "results": [
            {
                "target": str(result.target),
                "assignment_dir": str(result.assignment_dir),
            }
            for result in results
        ],
        "plan": plan.to_dict(),
    }


def generate_assignment_report(payload: dict) -> dict:
    """Generate and persist an assignment tracking report from the local GUI."""

    activity_path = resolve_local_path(payload.get("activity_path", ""), "activity_path")
    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    targets = read_targets_from_text(str(payload.get("targets_text", "")))
    output_name = str(payload.get("output_name", ""))
    storage = assignment_storage()
    output_path = storage.safe_teacher_report_path(output_name)
    assignment_id = str(payload.get("assignment_id", "")).strip()
    record_storage = assignment_record_storage()
    operation_lock = (
        assignment_operation_lock(assignment_record_operation_id(record_storage, assignment_id))
        if assignment_id
        else nullcontext()
    )
    with operation_lock:
        canonical_assignment_id = assignment_id
        if assignment_id:
            canonical_assignment_id = str(record_storage.read_assignment(assignment_id)["id"])
        index = track_assignments.track_assignments(
            activity_path=activity_path,
            targets=targets,
            assigned_at=payload.get("assigned_at") or None,
            due_at=payload.get("due_at") or None,
            now=payload.get("now") or None,
            class_id=payload.get("class_id") or None,
            class_label=payload.get("class_label") or None,
            github_team=payload.get("github_team") or None,
            assignment_id=canonical_assignment_id or None,
            server_root=ROOT if canonical_assignment_id else None,
        )
        with assignment_operation_lock(assignment_report_operation_id(storage, output_name)):
            if output_path.is_file():
                previous = storage.read_assignment_report(output_name)
                preserve_assignment_ai_feedback(previous, index)
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


class BoundedThreadingHTTPServer(ThreadingHTTPServer):
    """Serve requests with a fixed upper bound on concurrent client threads."""

    daemon_threads = False
    block_on_close = True

    def __init__(
        self,
        *args,
        max_workers: int = MAX_HTTP_WORKERS,
        max_workers_per_client: int | None = None,
        **kwargs,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers deve essere almeno 1")
        if max_workers_per_client is None:
            max_workers_per_client = min(MAX_HTTP_WORKERS_PER_CLIENT, max_workers)
        if max_workers_per_client < 1 or max_workers_per_client > max_workers:
            raise ValueError("max_workers_per_client deve essere tra 1 e max_workers")
        self._request_slots = threading.BoundedSemaphore(max_workers)
        self._max_workers_per_client = max_workers_per_client
        self._client_workers: dict[str, int] = {}
        self._client_workers_guard = threading.Lock()
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address) -> None:
        if not self.acquire_client_slot(client_address):
            self.reject_overloaded_request(request)
            return
        if not self._request_slots.acquire(blocking=False):
            self.release_client_slot(client_address)
            self.reject_overloaded_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._request_slots.release()
            self.release_client_slot(client_address)
            raise

    def acquire_client_slot(self, client_address) -> bool:
        client_key = str(client_address[0])
        with self._client_workers_guard:
            current = self._client_workers.get(client_key, 0)
            if current >= self._max_workers_per_client:
                return False
            self._client_workers[client_key] = current + 1
            return True

    def release_client_slot(self, client_address) -> None:
        client_key = str(client_address[0])
        with self._client_workers_guard:
            current = self._client_workers.get(client_key, 0)
            if current <= 1:
                self._client_workers.pop(client_key, None)
            else:
                self._client_workers[client_key] = current - 1

    def reject_overloaded_request(self, request) -> None:
        """Reject a connection without occupying the server accept loop."""

        response = (
            b"HTTP/1.1 503 Service Unavailable\r\n"
            b"Connection: close\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"Content-Length: 34\r\n"
            b"Retry-After: 1\r\n\r\n"
            b"Servizio temporaneamente occupato."
        )
        try:
            request.settimeout(1)
            request.sendall(response)
        except OSError:
            pass
        finally:
            self.shutdown_request(request)

    def process_request_thread(self, request, client_address) -> None:
        try:
            request.settimeout(HTTP_CLIENT_TIMEOUT_SECONDS)
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()
            self.release_client_slot(client_address)


class CourseBoardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the local board and its JSON API."""

    def end_headers(self) -> None:
        """Add browser hardening headers to every server response."""

        self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def is_loopback_client(self) -> bool:
        """Return whether this request originates from the teacher machine."""

        try:
            return ipaddress.ip_address(self.client_address[0]).is_loopback
        except ValueError:
            return False

    def is_teacher_authenticated(self) -> bool:
        """Authenticate the teacher independently from the network source."""

        expected_token = str(getattr(self.server, "teacher_token", ""))
        scheme, separator, credentials = self.headers.get("Authorization", "").partition(" ")
        if not expected_token or not separator or scheme.lower() != "basic":
            return False
        try:
            decoded = base64.b64decode(credentials, validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False
        username, separator, password = decoded.partition(":")
        return bool(
            separator
            and secrets.compare_digest(username, "teacher")
            and secrets.compare_digest(password, expected_token)
        )

    def write_teacher_auth_required(self) -> None:
        """Request browser-compatible teacher credentials."""

        body = json.dumps(
            {"error": "Autenticazione docente richiesta."},
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", f'Basic realm="{TEACHER_AUTH_REALM}", charset="UTF-8"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def reject_unauthenticated_teacher_api(self, method: str, path: str) -> bool:
        is_teacher_api = path.startswith("/api/") and (method, path) not in REMOTE_STUDENT_API_ROUTES
        if is_teacher_api and not self.is_teacher_authenticated():
            self.write_teacher_auth_required()
            return True
        return False

    def reject_unsafe_teacher_post(self, path: str) -> bool:
        """Reject browser cross-site writes and non-JSON teacher API requests."""

        if not path.startswith("/api/") or ("POST", path) in REMOTE_STUDENT_API_ROUTES:
            return False
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self.write_error_json(415, "Le API docente accettano soltanto application/json.")
            return True
        if self.headers.get("Sec-Fetch-Site", "").strip().lower() == "cross-site":
            self.write_error_json(403, "Richiesta cross-site rifiutata.")
            return True
        origin = self.headers.get("Origin", "").strip()
        if origin:
            parsed_origin = urlparse(origin)
            request_host = self.headers.get("Host", "").strip().lower()
            if parsed_origin.scheme not in {"http", "https"} or parsed_origin.netloc.lower() != request_host:
                self.write_error_json(403, "Origine della richiesta non autorizzata.")
                return True
        return False

    def authenticated_student_id(self) -> str | None:
        """Authenticate one student request and write the HTTP error on failure."""

        try:
            secret = student_help_auth.student_help_secret()
        except ValueError:
            self.write_error_json(500, STUDENT_HELP_SERVER_ERROR)
            return None
        try:
            return student_help_auth.student_id_from_authorization(
                self.headers.get("Authorization", ""),
                secret,
            )
        except ValueError as error:
            self.write_error_json(401, str(error))
            return None

    def read_teacher_json(self) -> dict[str, Any] | None:
        """Read one bounded JSON object from an authenticated teacher request."""

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            self.write_error_json(400, "Content-Length non valido.")
            return None
        if length < 1:
            self.write_error_json(400, "Body JSON obbligatorio.")
            return None
        if length > MAX_TEACHER_REQUEST_BYTES:
            self.write_error_json(413, "Richiesta docente troppo grande.")
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            self.write_error_json(400, f"JSON non valido: {error}")
            return None
        if not isinstance(payload, dict):
            self.write_error_json(400, "Il payload JSON deve essere un oggetto.")
            return None
        return payload

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if self.reject_unauthenticated_teacher_api("GET", parsed.path):
            return
        if parsed.path in {"/api/student-lab/assignments", "/api/student-lab/help-history"}:
            student_id = self.authenticated_student_id()
            if student_id is None:
                return
            try:
                query = parse_qs(parsed.query)
                if parsed.path == "/api/student-lab/assignments":
                    requested_now = query.get("now", [""])[0] or None
                    self.write_json(
                        locked_student_lab_payload(
                            student_id=student_id,
                            now=requested_now if self.is_loopback_client() else None,
                        )
                    )
                    return
                assignment_id = query.get("assignment_id", [""])[0]
                self.write_json(
                    student_lab_service.student_help_history(
                        root=ROOT,
                        assignments_dir=TEACHER_ASSIGNMENTS_DIR,
                        student_id=student_id,
                        assignment_id=assignment_id,
                    )
                )
            except ValueError as error:
                self.write_error_json(400, str(error))
            except Exception:  # noqa: BLE001
                self.write_error_json(500, STUDENT_HELP_SERVER_ERROR)
            return
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
        if parsed.path == "/api/assignments":
            query = parse_qs(parsed.query)
            self.write_json(list_assignment_records(query.get("now", [""])[0] or None))
            return
        if parsed.path == "/api/assignment-overview":
            self.write_json({"rows": assignment_overview()})
            return
        if parsed.path == "/api/class-rosters":
            self.write_json({"rosters": list_class_rosters()})
            return
        if parsed.path == "/api/student-dashboard":
            try:
                query = parse_qs(parsed.query)
                self.write_json(student_dashboard(query.get("student_id", [""])[0]))
            except Exception as error:  # noqa: BLE001
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
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
        if self.reject_unauthenticated_teacher_api("POST", parsed.path):
            return
        if self.reject_unsafe_teacher_post(parsed.path):
            return
        if parsed.path == "/api/student-lab/help":
            student_id = self.authenticated_student_id()
            if student_id is None:
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except (TypeError, ValueError):
                self.write_error_json(400, "Content-Length non valido.")
                return
            if length < 1 or length > MAX_STUDENT_HELP_REQUEST_BYTES:
                self.write_error_json(413, "Richiesta aiuto troppo grande o vuota.")
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("Il payload della richiesta deve essere un oggetto JSON.")
                self.write_json(record_student_help(payload, student_id=student_id))
            except student_help_service.StudentHelpRateLimitError as error:
                self.write_error_json(429, str(error))
            except student_help_service.StudentHelpPendingError as error:
                self.write_error_json(409, str(error))
            except StudentHelpBusyError as error:
                self.write_error_json(429, str(error))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
                self.write_error_json(400, str(error))
            except Exception:  # noqa: BLE001
                self.write_error_json(500, STUDENT_HELP_SERVER_ERROR)
            return
        payload = self.read_teacher_json()
        if payload is None:
            return
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
                saved = write_saved_design(
                    payload.get("name", ""),
                    payload.get("design", {}),
                    overwrite=payload.get("overwrite") is True,
                )
                self.write_json({"ok": True, "saved": saved, "designs": list_saved_designs()})
            except FileExistsError:
                self.write_error_json(409, "Esiste già un progetto con questo nome.")
            except Exception as error:  # noqa: BLE001
                self.write_error_json(400, str(error))
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
        if parsed.path == "/api/class-rosters/load":
            try:
                self.write_json({"roster": read_class_roster(payload.get("name", ""))})
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
        if parsed.path == "/api/activities/assignment-plan":
            try:
                self.write_json(preview_activity_assignment(payload))
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
        if parsed.path == "/api/activities/ai-package":
            try:
                self.write_json(preview_activity_ai_package(payload))
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
        if parsed.path == "/api/activities/ai-codex-draft":
            try:
                self.write_json(preview_activity_ai_codex_draft(payload))
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
        if parsed.path == "/api/assignments/save":
            try:
                self.write_json(save_assignment_record(payload))
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
        if parsed.path == "/api/assignments/delete":
            try:
                self.write_json(delete_assignment_record(payload))
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
        if parsed.path == "/api/activities/delete":
            try:
                self.write_json(delete_activity_record(payload))
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
        if parsed.path == "/api/assignments/distribute":
            try:
                self.write_json(distribute_activity_assignment(payload))
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
        if parsed.path == "/api/activities/save":
            try:
                self.write_json(save_activity(payload))
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

    def write_error_json(self, status: int, message: str) -> None:
        body = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, request_path: str) -> None:
        if not self.is_teacher_authenticated():
            self.write_teacher_auth_required()
            return
        relative = unquote(request_path.lstrip("/")) or "tools/course_board.html"
        target = (APP_ROOT / relative).resolve()
        try:
            relative_target = target.relative_to(APP_ROOT)
        except ValueError:
            self.send_error(403)
            return
        lowered_parts = {part.lower() for part in relative_target.parts}
        if lowered_parts & PRIVATE_STATIC_ROOTS or any(part.startswith(".") for part in relative_target.parts):
            self.send_error(403)
            return
        if "student_repos" in lowered_parts and "help" in lowered_parts:
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
    parser.add_argument("--root", type=Path, default=APP_ROOT, help="Root dati da usare per API e dashboard.")
    parser.add_argument(
        "--allow-insecure-network-http",
        action="store_true",
        help="Consente esplicitamente HTTP su un indirizzo non loopback; usare solo dietro protezioni di rete.",
    )
    args = parser.parse_args()
    teacher_token_is_configured = bool(os.environ.get("THEBITLAB_TEACHER_TOKEN", "").strip())
    try:
        validate_server_bind(args.host, args.allow_insecure_network_http)
        configured_teacher_token = teacher_dashboard_token()
    except ValueError as error:
        parser.error(str(error))
    data_root_lock = DataRootProcessLock(args.root)
    try:
        data_root_lock.acquire()
    except RuntimeError as error:
        parser.error(str(error))
    server = None
    try:
        data_root = configure_data_root(args.root)
        server = BoundedThreadingHTTPServer((args.host, args.port), CourseBoardHandler)
        server.teacher_token = configured_teacher_token
        if not is_loopback_bind_host(args.host):
            print("ATTENZIONE: dashboard e credenziali Basic sono esposte su HTTP non cifrato.")
            print("Preferisci loopback con tunnel SSH oppure un reverse proxy HTTPS.")
        print(f"Course board: http://{args.host}:{args.port}/tools/course_board.html")
        print(f"Root dati: {data_root}")
        print("Credenziali dashboard: utente teacher")
        print(teacher_dashboard_token_console_line(server.teacher_token, teacher_token_is_configured))
        print("Premi Ctrl+C per fermare il server.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer fermato.")
    finally:
        if server is not None:
            server.server_close()
        data_root_lock.release()
    return 0


def is_loopback_bind_host(host: str) -> bool:
    """Return whether a server bind host is explicitly limited to loopback."""

    normalized = host.strip().removeprefix("[").removesuffix("]")
    if normalized.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def validate_server_bind(host: str, allow_insecure_network_http: bool = False) -> None:
    """Reject accidental clear-text exposure of teacher Basic credentials."""

    if is_loopback_bind_host(host) or allow_insecure_network_http:
        return
    raise ValueError(
        "il bind HTTP su un indirizzo non loopback richiede "
        "--allow-insecure-network-http. Preferisci un tunnel SSH o un reverse proxy HTTPS."
    )


if __name__ == "__main__":
    raise SystemExit(main())
