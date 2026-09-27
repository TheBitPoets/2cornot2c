"""Explicit adoption and validation of an offline, non-demo pilot root."""

from __future__ import annotations

import re
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path, PurePosixPath

from scripts import (
    activity_revision_registry, assignment_records, course_activity_links, create_submission_scaffold,
    pilot_data_root as roots, rehearse_legacy_root as rehearsal,
    thebitlab_storage,
)
from scripts.thebitlab_identity_binding import resolve_assignment_target, resolve_student_identity
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

PROFILE = "legacy-adopted"
ROOT_SCHEMA = "thebitlab.pilot-root.v2"
BACKUP_SCHEMA = "thebitlab.pilot-backup.v2"


def relative_path(value: str) -> PurePosixPath:
    """Reject paths that alias, escape, or change meaning across supported hosts."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise roots.PilotRootError("Path storico non portabile.")
    for part in value.split("/"):
        if (part in {"", ".", ".."} or part.endswith((" ", "."))
                or re.search(r'[\x00-\x1f<>:"|?*]', part)
                or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)):
            raise roots.PilotRootError("Path storico non portabile.")
    return PurePosixPath(value)


def check_path(path: Path) -> None:
    if not path.is_absolute():
        raise roots.PilotRootError("Usare path assoluti.")
    for entry in (path, *path.parents):
        if entry.is_symlink() or (entry.exists() and getattr(entry.stat(), "st_file_attributes", 0) & 0x400):
            raise roots.PilotRootError("Link/reparse point non supportato.")


def inventory(root: Path) -> dict:
    check_path(root)
    if not root.is_dir():
        raise roots.PilotRootError("Root storica assente.")
    entries = rehearsal.inventory(root)
    folded = set()
    for name in entries:
        relative_path(name)
        if name.casefold() in folded:
            raise roots.PilotRootError("Path duplicato senza distinzione maiuscole.")
        folded.add(name.casefold())
    return entries


def marker(topology: roots.PilotTopology) -> dict:
    return {
        "schema_version": ROOT_SCHEMA, "profile": PROFILE,
        "deployment_id": topology.deployment_id,
        "auth_db_path": topology.auth_db_relative,
        "identity_schema_version": roots.SCHEMA_VERSION,
    }


class ReadOnlyIdentity(SqliteIdentityStorage):
    """Reuse identity readers without migrations or writable SQLite connections."""

    def __init__(self, path: Path):
        self.database_path = path

    def _connect(self):
        connection = sqlite3.connect(self.database_path.as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection


def validate_state(topology: roots.PilotTopology) -> dict:
    """Validate current authority and teaching references, never demo identities."""
    root = topology.root
    entries = inventory(root)
    databases = {name for name, item in entries.items() if "sha256" in item
                 and Path(name).suffix.lower() in {".db", ".sqlite", ".sqlite3"}}
    if databases != {topology.auth_db_relative}:
        raise roots.PilotRootError("Topologia auth storica ambigua o incompleta.")
    roots._sqlite_integrity(topology.auth_db_path)
    try:
        with closing(sqlite3.connect(topology.auth_db_path.as_uri() + "?mode=ro", uri=True)) as connection:
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("Foreign key incoerenti")
        storage = ReadOnlyIdentity(topology.auth_db_path)
        users = {user.user_id: user for user in storage.list_users()}
        classes = {group.class_id: group for group in storage.list_classes()}
        if not any(user.active and user.role in {"teacher", "admin"} for user in users.values()):
            raise ValueError("Account docente/amministratore attivo mancante")
        owners, snapshots = {}, {}
        memberships = set()
        for group in classes.values():
            for membership in storage.list_class_memberships(group.class_id):
                user = users.get(membership.user_id)
                if user is None or user.role != membership.role:
                    raise ValueError("Membership incoerente")
                if user.active and group.active and membership.role == "student":
                    memberships.add((group.class_id, user.user_id))
        for user in users.values():
            if user.active and user.role == "student":
                snapshot = storage.read_student_binding_snapshot(user.user_id)
                identity = resolve_student_identity(user.user_id, snapshot)
                owners[identity.subject_id] = user.user_id
                snapshots[user.user_id] = snapshot
        aliases = {(alias.class_id, alias.legacy_student_id): alias.subject_id
                   for alias in storage.list_legacy_subject_aliases()}
        rosters, represented = {}, set()
        for path in sorted((root / "doc/classes").rglob("*.json")):
            roster = thebitlab_storage.normalize_class_roster(roots._load_object(path, "Roster storico"))
            class_id = roster["id"]
            if class_id in rosters or class_id not in classes:
                raise ValueError("Classe roster mancante o duplicata")
            seen = set()
            for student in roster["students"]:
                if student["id"] in seen:
                    raise ValueError("Studente roster duplicato")
                seen.add(student["id"])
                if student["active"]:
                    owner = owners.get(aliases.get((class_id, student["id"])))
                    if (class_id, owner) not in memberships:
                        raise ValueError("Roster senza alias/membership autorevole")
                    if (class_id, owner) in represented:
                        raise ValueError("Persona duplicata nel roster attivo")
                    represented.add((class_id, owner))
            rosters[class_id] = roster
        if represented != memberships:
            raise ValueError("Roster incompleto per membership attive")

        registry = activity_revision_registry.read(root)
        activities = {}
        for revision in registry["history"].values():
            activity_revision_registry.verify(root, revision)
        records = [assignment_records.validate_assignment_record(roots._load_object(path, "Assignment storico"))
                   for path in sorted((root / "teacher-assignments").rglob("*.json"))]
        # Reuse catalog discovery; validate every discovered and referenced
        # descriptor, including historical revisions no longer visible there.
        paths = set((root / "activities").glob("*.json"))
        paths.update(root / name for name in registry["history"])
        catalog = thebitlab_storage.JsonAssignmentStorage(root, root / "teacher-reports",
                                                         [root / "activities", root / "examples/assignment_tracking"])
        paths.update(root / item["path"] for item in catalog.list_activities())
        for record in records:
            path = relative_path(record["activity_path"])
            if not (path.parts[0] == "activities" or path.parts[:2] == ("examples", "assignment_tracking")):
                raise ValueError("Activity fuori catalogo")
            paths.add(root / Path(*path.parts))
        for path in sorted(paths):
            activity = roots._load_object(path, "Activity storica")
            identifier = create_submission_scaffold.activity_id(activity)
            create_submission_scaffold.validate_activity_contract_or_raise(activity, identifier)
            for asset in activity.get("assets", []):
                asset_path = path.parent / Path(*relative_path(asset["path"]).parts)
                if not asset_path.is_file():
                    raise ValueError("Asset activity mancante")
            activities[path.relative_to(root).as_posix()] = activity["id"]
        ids = set()
        for record in records:
            if record["id"] in ids or record.get("class_id") not in rosters:
                raise ValueError("Assignment duplicato o senza roster")
            ids.add(record["id"])
            relative_path(record["activity_path"])
            if activities.get(record["activity_path"]) != record["activity_id"]:
                raise ValueError("Riferimento activity non risolvibile")
            for target in record["targets"]:
                owner = owners.get(target.get("subject_id"))
                if owner is None:
                    raise ValueError("Target senza soggetto canonico attivo")
                resolution = resolve_assignment_target(owner, snapshots[owner], record)
                if resolution.used_legacy_alias:
                    raise ValueError("Target non migrato")
        design_paths = [root / "doc/course_design.json"]
        design_paths.extend((root / "doc/course_designs").glob("*.json"))
        for path in design_paths:
            design = roots._load_object(path, "Design storico")
            if not isinstance(design.get("years"), list):
                raise ValueError("Design senza years")
            course_activity_links.validate_course_activity_targets(design, root)
        for path in (root / "doc/calendars").glob("*.json"):
            roots._load_object(path, "Calendario storico")
    except (ValueError, RuntimeError, sqlite3.DatabaseError, KeyError, TypeError) as error:
        raise roots.PilotRootError("Stato storico incoerente: identity/roster/assignment/activity/design.") from error
    return {"users": len(users), "classes": len(classes), "assignments": len(ids), "activities": len(activities)}


def startup_smoke(root: Path) -> None:
    """Exercise startup recovery on a disposable copy, preserving verified bytes."""
    with tempfile.TemporaryDirectory(prefix=".smoke-", dir=root.parent) as temporary:
        copy = Path(temporary) / "root"
        shutil.copytree(root, copy)
        roots._controlled_startup_smoke(copy)


def adopt(topology: roots.PilotTopology, bundle: Path, *, offline_copy: bool = False) -> dict:
    """Publish a new canonical root only from an unchanged rehearsal bundle."""
    if topology.profile != PROFILE or not offline_copy:
        raise roots.PilotRootError("Adozione richiede profilo storico e attestazione copia offline.")
    for path in (topology.root, bundle):
        check_path(path)
    target = topology.root
    if target.exists() or roots._paths_overlap(target, bundle) or not target.parent.is_dir():
        raise roots.PilotRootError("Destinazione adozione non nuova, isolata o privata.")
    report = roots._load_object(bundle / "report.json", "Report rehearsal")
    expected = {"schema_version": "thebitlab.legacy-rehearsal.v1", "ok": True,
                "deployable": False, "source_schema": 11, "candidate_schema": 12,
                "source_unchanged": True, "preupgrade_unchanged": True,
                "legacy_tables_preserved": True, "other_files_preserved": True}
    if any(type(report.get(key)) is not type(value) or report[key] != value for key, value in expected.items()):
        raise roots.PilotRootError("Report rehearsal non supportato o incompleto.")
    baseline = inventory(bundle)
    for name in ("candidate", "preupgrade"):
        if inventory(bundle / name) != report.get(name + "_inventory"):
            raise roots.PilotRootError("Rehearsal modificato dopo la verifica.")
        actual = rehearsal.database_state(bundle / name / topology.auth_db_relative)
        if actual != report.get(name + "_identity"):
            raise roots.PilotRootError("Stato identity del rehearsal non coerente.")
    if report["preupgrade_identity"]["versions"] != list(range(1, 12)):
        raise roots.PilotRootError("Snapshot rollback schema 11 incompleto.")
    if roots.ROOT_MARKER in report["candidate_inventory"]:
        raise roots.PilotRootError("Candidate gia adottata.")
    with tempfile.TemporaryDirectory(prefix=".adopt-", dir=target.parent) as temporary:
        stage = Path(temporary) / "root"
        shutil.copytree(bundle / "candidate", stage)
        if inventory(stage) != report["candidate_inventory"]:
            raise roots.PilotRootError("Copia candidate incompleta.")
        staged = roots.topology_from_paths(stage, topology.auth_db_relative,
                                          deployment_id=topology.deployment_id, profile=PROFILE)
        validate_state(staged)
        roots._write_json(stage / roots.ROOT_MARKER, marker(staged))
        result = roots.validate_root(staged)
        startup_smoke(stage)
        roots._harden_tree_permissions(stage)
        if inventory(bundle) != baseline or target.exists():
            raise roots.PilotRootError("Sorgente o destinazione cambiate durante adozione.")
        stage.rename(target)
    return {**result, "root": str(target), "adopted": True, "startup_smoke": True}
