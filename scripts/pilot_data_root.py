#!/usr/bin/env python3
"""Bootstrap, validate, back up, and restore one canonical pilot data root."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import (  # noqa: E402
    course_board_server,
    student_lab_demo_check,
    student_lab_demo_smoke,
    validate_pilot_deployment,
)
from scripts.thebitlab_identity import (  # noqa: E402
    ClassGroup,
    ClassMembership,
    UserAccount,
)
from scripts.thebitlab_identity_binding import (  # noqa: E402
    LegacySubjectAlias,
    StudentBindingResolutionError,
    StudentSubjectBinding,
    resolve_assignment_target,
)
from scripts.thebitlab_identity_ports import IdentityStorageError  # noqa: E402
from scripts.thebitlab_identity_sqlite import (  # noqa: E402
    SCHEMA_VERSION,
    SqliteIdentityStorage,
)

ROOT_SCHEMA = "thebitlab.pilot-root.v1"
BACKUP_SCHEMA = "thebitlab.pilot-backup.v1"
ROOT_MARKER = ".thebitlab-root.json"
BACKUP_MANIFEST = "manifest.json"
BACKUP_MANIFEST_CHECKSUM = "manifest.sha256"
BACKUP_PAYLOAD = "payload"
DEFAULT_AUTH_DB_PATH = ".thebitlab-auth/auth.sqlite3"
DEMO_CLASS_ID = "3A-TPSI"
DEMO_TIMESTAMP = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
DEMO_IDENTITIES = (
    {
        "user_id": "demo-student-rossi-mario",
        "student_id": student_lab_demo_smoke.STUDENT_ID,
        "display_name": "Rossi Mario",
        "subject_id": "subject:11111111111111111111111111111111",
    },
    {
        "user_id": "demo-student-bianchi-luca",
        "student_id": student_lab_demo_smoke.FAILING_STUDENT_ID,
        "display_name": "Bianchi Luca",
        "subject_id": "subject:22222222222222222222222222222222",
    },
)
REQUIRED_EXACT_PATHS = (
    "activities/python-demo-somma-001.json",
    "doc/calendars/as_2026_2027.json",
    "doc/classes/demo-3a.json",
    "doc/course_design.json",
    "teacher-reports/demo/python-demo-somma-001.json",
)
REQUIRED_GLOBS = (
    "teacher-assignments/*.json",
    "teacher-help-events/*/*/events.json",
    "examples/assignment_tracking/student_repos/rossi-mario/reports/python-demo-somma-001/latest.json",
    "examples/assignment_tracking/student_repos/rossi-mario/reports/"
    "python-demo-somma-001/assignments/*/attempts/*.json",
    "examples/assignment_tracking/student_repos/bianchi-luca/reports/python-demo-somma-001/latest.json",
    "examples/assignment_tracking/student_repos/bianchi-luca/reports/"
    "python-demo-somma-001/assignments/*/attempts/*.json",
)
TRANSIENT_NAMES = {".thebitlab-server.lock"}
SECRET_COMPONENTS = {".secrets", "secrets"}
SECRET_SUFFIXES = {".env", ".key", ".pem", ".p12", ".pfx"}
DEPLOYMENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,62}$")


class PilotRootError(RuntimeError):
    """Raised when the supported single-root pilot contract is not satisfied."""


@dataclass(frozen=True)
class PilotTopology:
    root: Path
    auth_db_relative: str
    deployment_id: str

    @property
    def auth_db_path(self) -> Path:
        return self.root.joinpath(*PurePosixPath(self.auth_db_relative).parts)


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json(payload))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value or "\x00" in value:
        raise PilotRootError("Il path auth deve essere relativo POSIX canonico.")
    raw_parts = value.split("/")
    path = PurePosixPath(value)
    if path.is_absolute() or path == PurePosixPath(".") or any(part in {"", ".", ".."} for part in raw_parts):
        raise PilotRootError("Il path auth deve restare nella root canonica.")
    if path.suffix not in {".db", ".sqlite", ".sqlite3"}:
        raise PilotRootError("Il path auth deve identificare un database SQLite.")
    return path.as_posix()


def topology_from_paths(
    root: Path,
    auth_db_path: str = DEFAULT_AUTH_DB_PATH,
    *,
    deployment_id: str = "pilot-demo-local",
) -> PilotTopology:
    expanded = root.expanduser()
    if not expanded.is_absolute():
        raise PilotRootError("La data root deve essere espressa come path assoluto.")
    if expanded.is_symlink():
        raise PilotRootError("La data root non puo essere un symlink.")
    resolved = expanded.resolve(strict=False)
    if resolved == resolved.parent:
        raise PilotRootError("La data root deve essere una directory assoluta dedicata.")
    if not isinstance(deployment_id, str) or DEPLOYMENT_ID_PATTERN.fullmatch(deployment_id) is None:
        raise PilotRootError("deployment_id non valido.")
    return PilotTopology(resolved, _relative_path(auth_db_path), deployment_id)


def topology_from_manifest(path: Path) -> PilotTopology:
    manifest = validate_pilot_deployment.load_json(path)
    validate_pilot_deployment.validate_manifest(manifest)
    return topology_from_paths(
        Path(manifest["data"]["root"]),
        manifest["data"]["auth_db_path"],
        deployment_id=manifest["deployment_id"],
    )


def _root_marker(topology: PilotTopology) -> dict[str, Any]:
    return {
        "schema_version": ROOT_SCHEMA,
        "profile": "pilot-demo",
        "deployment_id": topology.deployment_id,
        "auth_db_path": topology.auth_db_relative,
        "identity_schema_version": SCHEMA_VERSION,
        "class_id": DEMO_CLASS_ID,
        "students": [
            {
                "user_id": item["user_id"],
                "student_id": item["student_id"],
                "subject_id": item["subject_id"],
            }
            for item in DEMO_IDENTITIES
        ],
    }


def _load_object(path: Path, label: str) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PilotRootError(f"{label} contiene chiavi duplicate.")
            result[key] = value
        return result

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicates,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise PilotRootError(f"{label} assente o non valido.") from error
    if not isinstance(payload, dict):
        raise PilotRootError(f"{label} deve essere un oggetto JSON.")
    return payload


@contextmanager
def _stopped_root_lock(root: Path) -> Iterator[None]:
    lock = course_board_server.DataRootProcessLock(root)
    try:
        lock.acquire()
    except RuntimeError as error:
        raise PilotRootError("Root in uso: la topologia a doppia istanza non e supportata.") from error
    try:
        yield
    finally:
        lock.release()


def _copy_demo_documents(root: Path) -> None:
    calendar_source = PROJECT_ROOT / "doc" / "calendars" / "as_2026_2027.json"
    calendar_destination = root / "doc" / "calendars" / "as_2026_2027.json"
    calendar_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(calendar_source, calendar_destination)

    design = _load_object(PROJECT_ROOT / "doc" / "course_design.json", "Design demo")
    years = design.get("years")
    if not isinstance(years, list) or not years or not isinstance(years[0], dict):
        raise PilotRootError("Design demo senza anno scolastico.")
    years[0]["audience"] = {"class_ids": [DEMO_CLASS_ID]}
    _write_json(root / "doc" / "course_design.json", design)

    roster = _load_object(PROJECT_ROOT / "doc" / "classes" / "demo-3a.json", "Roster demo")
    expected_student_ids = {item["student_id"] for item in DEMO_IDENTITIES}
    students = roster.get("students")
    if not isinstance(students, list):
        raise PilotRootError("Roster demo senza studenti.")
    roster["id"] = DEMO_CLASS_ID
    roster["label"] = "3A TPSI"
    roster["students"] = [
        student
        for student in students
        if isinstance(student, dict) and student.get("id") in expected_student_ids
    ]
    if {student.get("id") for student in roster["students"]} != expected_student_ids:
        raise PilotRootError("Roster demo incompleto.")
    _write_json(root / "doc" / "classes" / "demo-3a.json", roster)


def _provision_identity(topology: PilotTopology) -> None:
    storage = SqliteIdentityStorage(topology.auth_db_path)
    storage.create_user(
        UserAccount(
            "demo-teacher",
            "Docente Demo",
            "teacher",
            True,
            DEMO_TIMESTAMP,
            DEMO_TIMESTAMP,
        )
    )
    storage.create_class(
        ClassGroup(
            DEMO_CLASS_ID,
            "3A TPSI",
            "2026-2027",
            True,
            DEMO_TIMESTAMP,
            DEMO_TIMESTAMP,
        )
    )
    storage.save_membership(
        ClassMembership("demo-teacher", DEMO_CLASS_ID, "teacher", DEMO_TIMESTAMP)
    )
    for identity in DEMO_IDENTITIES:
        storage.create_user(
            UserAccount(
                identity["user_id"],
                identity["display_name"],
                "student",
                True,
                DEMO_TIMESTAMP,
                DEMO_TIMESTAMP,
            )
        )
        storage.save_membership(
            ClassMembership(identity["user_id"], DEMO_CLASS_ID, "student", DEMO_TIMESTAMP)
        )
        storage.create_student_subject_binding(
            StudentSubjectBinding(
                identity["subject_id"],
                identity["user_id"],
                True,
                1,
                DEMO_TIMESTAMP,
                DEMO_TIMESTAMP,
            ),
            (
                LegacySubjectAlias(
                    DEMO_CLASS_ID,
                    identity["student_id"],
                    identity["subject_id"],
                    DEMO_TIMESTAMP,
                ),
            ),
        )


def _add_assignment_subjects(root: Path) -> None:
    paths = sorted((root / "teacher-assignments").glob("*.json"))
    if len(paths) != 1:
        raise PilotRootError("Il bootstrap demo deve produrre una sola consegna autorevole.")
    assignment = _load_object(paths[0], "Consegna demo")
    subjects = {item["student_id"]: item["subject_id"] for item in DEMO_IDENTITIES}
    targets = assignment.get("targets")
    if not isinstance(targets, list):
        raise PilotRootError("Target della consegna demo non validi.")
    for target in targets:
        if not isinstance(target, dict) or target.get("student_id") not in subjects:
            raise PilotRootError("Target della consegna demo inatteso.")
        target["subject_id"] = subjects[target["student_id"]]
    _write_json(paths[0], assignment)


def _remove_runtime_caches(root: Path) -> None:
    for directory in sorted(root.rglob("__pycache__"), reverse=True):
        if directory.is_dir() and not directory.is_symlink():
            shutil.rmtree(directory)
    for path in root.rglob("*.pyc"):
        path.unlink()


def _harden_tree_permissions(root: Path) -> None:
    """Apply private baseline modes on POSIX; Windows ACLs remain deployment-owned."""

    if os.name == "nt":
        return
    root.chmod(0o700)
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PilotRootError("Symlink non supportato nello stato applicativo.")
        path.chmod(0o700 if path.is_dir() else 0o600)


def bootstrap(topology: PilotTopology) -> dict[str, Any]:
    """Create a complete demo installation, or validate the existing one unchanged."""

    root = topology.root
    existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    cleanup_on_failure = not existed
    try:
        with _stopped_root_lock(root):
            entries = [item for item in root.iterdir() if item.name not in TRANSIENT_NAMES]
            if entries:
                if not (root / ROOT_MARKER).is_file():
                    raise PilotRootError("Root parziale o non gestita: bootstrap rifiutato.")
                result = validate_root(topology, run_demo_check=True, lock=False)
                return {**result, "created": False, "idempotent": True}
            cleanup_on_failure = True
            student_lab_demo_smoke.run_smoke(root)
            _remove_runtime_caches(root)
            _copy_demo_documents(root)
            _provision_identity(topology)
            _add_assignment_subjects(root)
            _write_json(root / ROOT_MARKER, _root_marker(topology))
            _harden_tree_permissions(root)
            result = validate_root(topology, run_demo_check=True, lock=False)
            return {**result, "created": True, "idempotent": True}
    except Exception:
        if cleanup_on_failure:
            shutil.rmtree(root, ignore_errors=True)
        raise


def _sqlite_integrity(database_path: Path) -> None:
    if not database_path.is_file() or database_path.is_symlink():
        raise PilotRootError("Database auth canonico assente o non regolare.")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True)
        result = connection.execute("PRAGMA integrity_check").fetchone()
        versions = [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
    except sqlite3.DatabaseError as error:
        raise PilotRootError("Integrity/schema check SQLite non riuscito.") from error
    finally:
        if connection is not None:
            connection.close()
    if result != ("ok",):
        raise PilotRootError("SQLite integrity_check non riuscito.")
    if versions != list(range(1, SCHEMA_VERSION + 1)):
        raise PilotRootError("Migrazioni auth incomplete o non supportate.")


def _verify_identity(topology: PilotTopology) -> None:
    storage = SqliteIdentityStorage(topology.auth_db_path)
    users = storage.list_users()
    expected_users = {"demo-teacher", *(item["user_id"] for item in DEMO_IDENTITIES)}
    if {user.user_id for user in users} != expected_users or any(not user.active for user in users):
        raise PilotRootError("Matrice account demo incoerente.")
    classes = storage.list_classes()
    if len(classes) != 1 or classes[0].class_id != DEMO_CLASS_ID or not classes[0].active:
        raise PilotRootError("Classe demo auth incoerente.")
    roster = _load_object(topology.root / "doc/classes/demo-3a.json", "Roster demo")
    roster_students = roster.get("students")
    expected_student_ids = {item["student_id"] for item in DEMO_IDENTITIES}
    if (
        roster.get("id") != DEMO_CLASS_ID
        or not isinstance(roster_students, list)
        or {
            student.get("id")
            for student in roster_students
            if isinstance(student, dict) and student.get("active") is True
        }
        != expected_student_ids
    ):
        raise PilotRootError("Roster demo incoerente con classe e account auth.")
    expected_memberships = {
        ("demo-teacher", "teacher"),
        *((item["user_id"], "student") for item in DEMO_IDENTITIES),
    }
    memberships = {
        (membership.user_id, membership.role)
        for membership in storage.list_class_memberships(DEMO_CLASS_ID)
    }
    if memberships != expected_memberships:
        raise PilotRootError("Membership demo auth incoerenti.")
    assignment_paths = sorted((topology.root / "teacher-assignments").glob("*.json"))
    if len(assignment_paths) != 1:
        raise PilotRootError("Consegna demo autorevole mancante o ambigua.")
    assignment = _load_object(assignment_paths[0], "Consegna demo")
    for identity in DEMO_IDENTITIES:
        snapshot = storage.read_student_binding_snapshot(identity["user_id"])
        resolution = resolve_assignment_target(identity["user_id"], snapshot, assignment)
        if resolution.subject_id != identity["subject_id"] or resolution.used_legacy_alias:
            raise PilotRootError("Binding #702 o target subject_id demo incoerente.")


def _check_required_state(root: Path, auth_relative: str) -> None:
    if any(path.is_symlink() for path in root.rglob("*")):
        raise PilotRootError("Symlink non supportato nella root applicativa.")
    required = (*REQUIRED_EXACT_PATHS, auth_relative)
    missing = [relative for relative in required if not root.joinpath(*PurePosixPath(relative).parts).is_file()]
    missing.extend(pattern for pattern in REQUIRED_GLOBS if not any(root.glob(pattern)))
    if missing:
        raise PilotRootError("Root parziale: stato richiesto mancante.")
    sqlite_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}
    }
    if sqlite_files != {auth_relative}:
        raise PilotRootError("Topologia auth ambigua: database SQLite inatteso o mancante.")


def validate_root(
    topology: PilotTopology,
    *,
    run_demo_check: bool = True,
    lock: bool = True,
) -> dict[str, Any]:
    """Fail closed unless the root, auth database, demo state, and binding agree."""

    def perform() -> dict[str, Any]:
        root = topology.root
        if not root.is_dir() or root.is_symlink():
            raise PilotRootError("Data root canonica assente, non-directory o symlink.")
        marker = _load_object(root / ROOT_MARKER, "Marker root canonica")
        if marker != _root_marker(topology):
            raise PilotRootError("Marker root incoerente con deployment/auth configurati.")
        _check_required_state(root, topology.auth_db_relative)
        _sqlite_integrity(topology.auth_db_path)
        try:
            _verify_identity(topology)
        except (IdentityStorageError, StudentBindingResolutionError) as error:
            raise PilotRootError("Account, membership o binding #702 incoerenti.") from error
        if run_demo_check:
            try:
                result = student_lab_demo_check.run_guided_check(root, prepare=False)
            except RuntimeError as error:
                raise PilotRootError("student_lab_demo_check --existing non riuscito.") from error
            if result.get("ok") is not True:
                raise PilotRootError("student_lab_demo_check --existing non riuscito.")
        return {
            "ok": True,
            "root": str(root),
            "auth_db_path": topology.auth_db_relative,
            "deployment_id": topology.deployment_id,
            "identity_schema_version": SCHEMA_VERSION,
            "demo_check": run_demo_check,
        }

    if lock:
        if not topology.root.is_dir() or topology.root.is_symlink():
            raise PilotRootError("Data root canonica assente, non-directory o symlink.")
        with _stopped_root_lock(topology.root):
            return perform()
    return perform()


def _paths_overlap(first: Path, second: Path) -> bool:
    first_resolved = first.resolve(strict=False)
    second_resolved = second.resolve(strict=False)
    return (
        first_resolved == second_resolved
        or first_resolved in second_resolved.parents
        or second_resolved in first_resolved.parents
    )


def _secret_path(relative: PurePosixPath) -> bool:
    lowered = [part.lower() for part in relative.parts]
    name = lowered[-1]
    return (
        any(part in SECRET_COMPONENTS for part in lowered)
        or Path(name).suffix in SECRET_SUFFIXES
        or "secret" in name
        or ("token" in name and name != "auth.sqlite3")
    )


def _root_files(
    root: Path, auth_db_relative: str
) -> list[tuple[Path, PurePosixPath]]:
    files: list[tuple[Path, PurePosixPath]] = []
    auth_sidecars = {
        f"{auth_db_relative}-journal",
        f"{auth_db_relative}-shm",
        f"{auth_db_relative}-wal",
    }
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if (
            relative.name in TRANSIENT_NAMES
            or relative.as_posix() in auth_sidecars
            or relative.suffix in {".lock", ".pyc"}
            or "__pycache__" in relative.parts
        ):
            continue
        if path.is_symlink():
            raise PilotRootError("Symlink non supportato nella root applicativa.")
        if path.is_dir():
            continue
        if not path.is_file():
            raise PilotRootError("Entry non regolare nella root applicativa.")
        if _secret_path(relative):
            raise PilotRootError("Secret o credenziale rilevata nella root: backup rifiutato.")
        files.append((path, relative))
    return files


def _copy_sqlite_snapshot(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_connection: sqlite3.Connection | None = None
    destination_connection: sqlite3.Connection | None = None
    try:
        source_connection = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        if source_connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise PilotRootError("SQLite sorgente non integro: backup rifiutato.")
        destination_connection = sqlite3.connect(destination)
        source_connection.backup(destination_connection)
    except sqlite3.DatabaseError as error:
        raise PilotRootError("Snapshot SQLite coerente non riuscito.") from error
    finally:
        if destination_connection is not None:
            destination_connection.close()
        if source_connection is not None:
            source_connection.close()


def create_backup(topology: PilotTopology, output: Path) -> dict[str, Any]:
    """Create a deterministic manifest and a stopped-process coherent snapshot."""

    started = time.perf_counter()
    if not topology.root.is_dir() or topology.root.is_symlink():
        raise PilotRootError("Data root canonica assente, non-directory o symlink.")
    output = output.expanduser().resolve(strict=False)
    if _paths_overlap(topology.root, output):
        raise PilotRootError("Il backup deve essere esterno e isolato dalla root sorgente.")
    if output.exists():
        raise PilotRootError("La directory backup deve essere nuova.")
    staging = output.with_name(f".{output.name}.partial-{os.getpid()}")
    if staging.exists():
        raise PilotRootError("Directory staging backup gia presente.")
    try:
        with _stopped_root_lock(topology.root):
            validate_root(topology, run_demo_check=True, lock=False)
            files = _root_files(topology.root, topology.auth_db_relative)
            payload_root = staging / BACKUP_PAYLOAD
            for source, relative in files:
                destination = payload_root.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if relative.as_posix() == topology.auth_db_relative:
                    _copy_sqlite_snapshot(source, destination)
                else:
                    shutil.copyfile(source, destination)
            manifest_files = [
                {
                    "path": relative.as_posix(),
                    "size": payload_root.joinpath(*relative.parts).stat().st_size,
                    "sha256": _sha256(payload_root.joinpath(*relative.parts)),
                }
                for _, relative in files
            ]
            manifest = {
                "schema_version": BACKUP_SCHEMA,
                "root_schema_version": ROOT_SCHEMA,
                "deployment_id": topology.deployment_id,
                "auth_db_path": topology.auth_db_relative,
                "consistency": "application-stopped-exclusive-root-lock+sqlite-backup-api",
                "files": manifest_files,
            }
            manifest_bytes = _canonical_json(manifest)
            (staging / BACKUP_MANIFEST).write_bytes(manifest_bytes)
            checksum = hashlib.sha256(manifest_bytes).hexdigest()
            (staging / BACKUP_MANIFEST_CHECKSUM).write_text(
                f"{checksum}  {BACKUP_MANIFEST}\n", encoding="ascii"
            )
            _harden_tree_permissions(staging)
            staging.rename(output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    duration = time.perf_counter() - started
    return {
        "ok": True,
        "backup": str(output),
        "files": len(manifest_files),
        "manifest_sha256": checksum,
        "duration_seconds": round(duration, 6),
        "rpo_target_hours": 24,
        "rto_target_business_hours": 8,
        "target_assessment": "local measurement only; not an SLA or compliance claim",
    }


def _validated_backup(backup: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not backup.is_dir() or backup.is_symlink():
        raise PilotRootError("Directory backup assente o non regolare.")
    manifest_path = backup / BACKUP_MANIFEST
    checksum_path = backup / BACKUP_MANIFEST_CHECKSUM
    try:
        checksum_line = checksum_path.read_text(encoding="ascii")
    except (OSError, UnicodeError) as error:
        raise PilotRootError("Checksum manifest assente o non valido.") from error
    expected_line = f"{_sha256(manifest_path)}  {BACKUP_MANIFEST}\n"
    if checksum_line != expected_line:
        raise PilotRootError("Checksum del manifest non valido.")
    manifest = _load_object(manifest_path, "Manifest backup")
    required_keys = {
        "schema_version",
        "root_schema_version",
        "deployment_id",
        "auth_db_path",
        "consistency",
        "files",
    }
    if (
        set(manifest) != required_keys
        or manifest.get("schema_version") != BACKUP_SCHEMA
        or manifest.get("root_schema_version") != ROOT_SCHEMA
        or manifest.get("consistency")
        != "application-stopped-exclusive-root-lock+sqlite-backup-api"
        or not isinstance(manifest.get("deployment_id"), str)
        or DEPLOYMENT_ID_PATTERN.fullmatch(manifest["deployment_id"]) is None
    ):
        raise PilotRootError("Contratto manifest backup non supportato.")
    auth_relative = _relative_path(manifest.get("auth_db_path"))
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise PilotRootError("Elenco file del backup assente.")
    paths: list[str] = []
    files: list[dict[str, Any]] = []
    for item in raw_files:
        if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
            raise PilotRootError("Entry manifest backup non valida.")
        relative_text = item.get("path")
        try:
            relative = PurePosixPath(relative_text)
        except TypeError as error:
            raise PilotRootError("Path manifest backup non valido.") from error
        if (
            relative.is_absolute()
            or relative == PurePosixPath(".")
            or any(part in {"", ".", ".."} for part in relative.parts)
            or "\\" in relative_text
        ):
            raise PilotRootError("Path manifest backup non portabile.")
        if _secret_path(relative):
            raise PilotRootError("Manifest backup contiene un path secret vietato.")
        source = backup / BACKUP_PAYLOAD / Path(*relative.parts)
        if source.is_symlink() or not source.is_file():
            raise PilotRootError("Payload backup incompleto o non regolare.")
        if type(item.get("size")) is not int or item["size"] < 0 or source.stat().st_size != item["size"]:
            raise PilotRootError("Dimensione payload backup non valida.")
        digest = item.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or _sha256(source) != digest:
            raise PilotRootError("Checksum payload backup non valido.")
        paths.append(relative.as_posix())
        files.append(item)
    if paths != sorted(paths) or len(paths) != len(set(paths)) or auth_relative not in paths:
        raise PilotRootError("Ordine, unicita o database auth del manifest non validi.")
    payload_entries = list((backup / BACKUP_PAYLOAD).rglob("*"))
    if any(
        path.is_symlink() or (not path.is_file() and not path.is_dir())
        for path in payload_entries
    ):
        raise PilotRootError("Payload backup contiene entry non regolari.")
    actual = {
        path.relative_to(backup / BACKUP_PAYLOAD).as_posix()
        for path in payload_entries
        if path.is_file()
    }
    if actual != set(paths):
        raise PilotRootError("Payload backup contiene file non dichiarati.")
    return manifest, files


def _controlled_startup_smoke(root: Path) -> None:
    original_root = course_board_server.ROOT
    lock = course_board_server.DataRootProcessLock(root)
    server = None
    try:
        lock.acquire()
        course_board_server.configure_data_root(root)
        server = course_board_server.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0), course_board_server.CourseBoardHandler
        )
        server.teacher_token = "controlled-restore-smoke-only"
    except (OSError, RuntimeError) as error:
        raise PilotRootError("Startup smoke controllato del restore non riuscito.") from error
    finally:
        try:
            if server is not None:
                server.server_close()
        finally:
            try:
                course_board_server.configure_data_root(original_root)
            finally:
                lock.release()


def restore_backup(backup: Path, target: Path) -> dict[str, Any]:
    """Verify and restore a backup into a new isolated root, never into its source."""

    started = time.perf_counter()
    backup = backup.expanduser().resolve(strict=True)
    target = target.expanduser().resolve(strict=False)
    if target.exists():
        raise PilotRootError("La root restore deve essere nuova e isolata.")
    if _paths_overlap(backup, target):
        raise PilotRootError("La root restore non puo sovrapporsi al backup.")
    manifest, files = _validated_backup(backup)
    topology = topology_from_paths(
        target,
        manifest["auth_db_path"],
        deployment_id=manifest["deployment_id"],
    )
    staging = target.with_name(f".{target.name}.partial-{os.getpid()}")
    if staging.exists():
        raise PilotRootError("Directory staging restore gia presente.")
    try:
        for item in files:
            relative = PurePosixPath(item["path"])
            source = backup / BACKUP_PAYLOAD / Path(*relative.parts)
            destination = staging / Path(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        _harden_tree_permissions(staging)
        staging.rename(target)
        try:
            SqliteIdentityStorage(topology.auth_db_path)
        except IdentityStorageError as error:
            raise PilotRootError("Migrazione schema identity del restore non riuscita.") from error
        result = validate_root(topology, run_demo_check=True)
        _controlled_startup_smoke(target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(target, ignore_errors=True)
        raise
    duration = time.perf_counter() - started
    return {
        **result,
        "restore": str(target),
        "source_backup": str(backup),
        "files": len(files),
        "sqlite_integrity": True,
        "migrations": SCHEMA_VERSION,
        "binding_702": True,
        "startup_smoke": True,
        "duration_seconds": round(duration, 6),
        "rpo_target_hours": 24,
        "rto_target_business_hours": 8,
        "target_assessment": "local measurement only; not an SLA or compliance claim",
    }


def _topology_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", type=Path, help="Manifest deployment pilot autorevole.")
    group.add_argument("--root", type=Path, help="Root assoluta per smoke locali/demo.")
    parser.add_argument("--auth-db-path", default=DEFAULT_AUTH_DB_PATH)
    parser.add_argument("--deployment-id", default="pilot-demo-local")


def _args_topology(args: argparse.Namespace) -> PilotTopology:
    if args.config is not None:
        if args.auth_db_path != DEFAULT_AUTH_DB_PATH or args.deployment_id != "pilot-demo-local":
            raise PilotRootError("Con --config root, auth e deployment_id derivano soltanto dal manifest.")
        return topology_from_manifest(args.config)
    return topology_from_paths(
        args.root,
        args.auth_db_path,
        deployment_id=args.deployment_id,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    bootstrap_parser = subparsers.add_parser("bootstrap", help="Bootstrap idempotente della root vuota.")
    _topology_arguments(bootstrap_parser)
    validate_parser = subparsers.add_parser("validate", help="Validazione fail-closed della root.")
    _topology_arguments(validate_parser)
    backup_parser = subparsers.add_parser("backup", help="Snapshot coerente a processo fermo.")
    _topology_arguments(backup_parser)
    backup_parser.add_argument("--output", type=Path, required=True)
    restore_parser = subparsers.add_parser("restore", help="Restore verificato in root nuova isolata.")
    restore_parser.add_argument("--backup", type=Path, required=True)
    restore_parser.add_argument("--target", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "restore":
            result = restore_backup(args.backup, args.target)
        else:
            topology = _args_topology(args)
            if args.command == "bootstrap":
                result = bootstrap(topology)
            elif args.command == "validate":
                result = validate_root(topology)
            else:
                result = create_backup(topology, args.output)
    except (RuntimeError, OSError, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
