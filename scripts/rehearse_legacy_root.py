#!/usr/bin/env python3
"""Rehearse schema-11 identity adoption on an explicitly offline root copy.

Never writes a canonical root marker or starts a server. Output is evidence,
not a deployment root; see doc/PILOT_LEGACY_ROOT_ADOPTION.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import assignment_records, pilot_data_root
from scripts.thebitlab_identity_binding import (
    LegacySubjectAlias,
    StudentSubjectBinding,
    generate_subject_id,
    migrate_legacy_assignment_targets,
    resolve_assignment_target,
    resolve_student_identity,
)
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage


class RehearsalError(RuntimeError):
    """Offline rehearsal failed; nothing has been published."""


def inventory(root: Path) -> dict[str, Any]:
    """Inventory all entries, including empty directories; never follow links."""
    entries: dict[str, Any] = {}
    def unreadable(error: OSError) -> None:
        raise RehearsalError("Inventario incompleto: directory non leggibile.") from error

    for directory, directories, files in os.walk(root, followlinks=False, onerror=unreadable):
        for name in sorted(directories + files):
            path = Path(directory) / name
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise RehearsalError("Link/reparse point nella copia offline.")
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise RehearsalError("Entry non regolare nella copia offline.")
            if pilot_data_root._secret_path(PurePosixPath(relative)):
                raise RehearsalError("Configurazione segreta nella root: separarla prima del rehearsal.")
            if stat.S_ISDIR(info.st_mode):
                entries[relative] = {"directory": True}
            elif relative != ".thebitlab-server.lock":
                entries[relative] = {"size": info.st_size, "sha256": pilot_data_root._sha256(path)}
    return dict(sorted(entries.items()))


def database_state(path: Path) -> dict[str, Any]:
    """Logical fingerprints only: never put account/session data in reports."""
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise RehearsalError("SQLite non integro.")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise RehearsalError("Foreign key SQLite incoerenti.")
        versions = [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
        tables = {}
        for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted = '"' + name.replace('"', '""') + '"'
            rows = connection.execute(f"SELECT * FROM {quoted}").fetchall()
            digest = hashlib.sha256()
            for row in sorted(repr(row) for row in rows):
                digest.update((row + "\n").encode("utf-8"))
            tables[name] = {"rows": len(rows), "sha256": digest.hexdigest()}
        return {"versions": versions, "tables": tables}


def read_mapping(path: Path) -> list[dict[str, Any]]:
    payload = pilot_data_root._load_object(path, "Mapping amministrativo")
    if set(payload) != {"schema_version", "bindings"} or payload["schema_version"] != "thebitlab.legacy-adoption-map.v1":
        raise RehearsalError("Contratto mapping non valido.")
    bindings = payload["bindings"]
    if not isinstance(bindings, list):
        raise RehearsalError("bindings deve essere una lista.")
    users: set[str] = set()
    aliases: set[tuple[str, str]] = set()
    for item in bindings:
        if not isinstance(item, dict) or set(item) != {"user_id", "aliases"}:
            raise RehearsalError("Binding mapping non valido.")
        user = item["user_id"]
        if not isinstance(user, str) or not user or user != user.strip() or user in users:
            raise RehearsalError("Account mapping vuoto, non canonico o duplicato.")
        users.add(user)
        if not isinstance(item["aliases"], list):
            raise RehearsalError("aliases deve essere una lista.")
        for alias in item["aliases"]:
            if not isinstance(alias, dict) or set(alias) != {"class_id", "legacy_student_id"}:
                raise RehearsalError("Alias mapping non valido.")
            if any(not isinstance(value, str) or not value or value != value.strip() for value in alias.values()):
                raise RehearsalError("Alias mapping non canonico.")
            key = (alias["class_id"], alias["legacy_student_id"])
            if key in aliases:
                raise RehearsalError("Alias mapping duplicato o ambiguo.")
            aliases.add(key)
    return bindings


def rehearse(source: Path, output: Path, mapping: Path, *, offline_copy: bool = False) -> dict[str, Any]:
    if not offline_copy:
        raise RehearsalError("Richiesta attestazione esplicita di copia offline; non usare la root live.")
    # Resolve only after checking all existing ancestors for symlinks/junctions.
    for path in (source, output):
        if not path.is_absolute():
            raise RehearsalError("Usare path assoluti.")
        for ancestor in (path, *path.parents):
            if ancestor.is_symlink() or (ancestor.exists() and getattr(ancestor.stat(), "st_file_attributes", 0) & 0x400):
                raise RehearsalError("Path con link/reparse point non supportato.")
    source, output = source.resolve(), output.resolve()
    if not source.is_dir() or output.exists() or pilot_data_root._paths_overlap(source, output):
        raise RehearsalError("Sorgente non valida o destinazione esistente/sovrapposta.")
    if not output.parent.is_dir():
        raise RehearsalError("La directory privata di output deve gia esistere.")
    auth = pilot_data_root.DEFAULT_AUTH_DB_PATH
    original = inventory(source)
    databases = {name for name, entry in original.items() if "sha256" in entry and Path(name).suffix.lower() in {".db", ".sqlite", ".sqlite3"}}
    if databases != {auth} or pilot_data_root.ROOT_MARKER in original:
        raise RehearsalError("Richiesta root storica senza marker con un solo auth DB canonico.")
    bindings = read_mapping(mapping)
    with tempfile.TemporaryDirectory(prefix=".legacy-", dir=output.parent) as temporary:
        stage = Path(temporary)
        raw = stage / "raw"
        shutil.copytree(source, raw, copy_function=shutil.copyfile,
                        ignore=lambda directory, names: [".thebitlab-server.lock"] if Path(directory) == source else [])
        if inventory(raw) != original or inventory(source) != original:
            raise RehearsalError("La sorgente e cambiata durante la copia.")
        bundle = stage / "bundle"
        before = bundle / "preupgrade"
        shutil.copytree(raw, before, copy_function=shutil.copyfile)
        # Consume WAL only on a disposable copy, never by opening source SQLite.
        sidecars = {auth + suffix for suffix in ("-wal", "-shm", "-journal")}
        for relative in (auth, *sorted(sidecars)):
            before.joinpath(*PurePosixPath(relative).parts).unlink(missing_ok=True)
        pilot_data_root._copy_sqlite_snapshot(raw / auth, before / auth)
        # backup() can retain the source WAL journal mode. Make the offline
        # snapshot self-contained before any read-only verification opens it.
        with closing(sqlite3.connect(before / auth)) as connection:
            if connection.execute("PRAGMA journal_mode=DELETE").fetchone() != ("delete",):
                raise RehearsalError("Impossibile consolidare lo snapshot SQLite.")
        baseline = database_state(before / auth)
        if baseline["versions"] != list(range(1, 12)):
            raise RehearsalError("Questo rehearsal supporta soltanto lo schema sorgente 11 completo.")
        before_files = inventory(before)
        unchanged = {name: entry for name, entry in original.items() if name not in {auth, *sidecars}}
        if {name: entry for name, entry in before_files.items() if name != auth} != unchanged:
            raise RehearsalError("Snapshot incompleto.")
        candidate = bundle / "candidate"
        shutil.copytree(before, candidate, copy_function=shutil.copyfile)
        storage = SqliteIdentityStorage(candidate / auth)
        active_students = {user.user_id for user in storage.list_users() if user.active and user.role == "student"}
        if {item["user_id"] for item in bindings} != active_students:
            raise RehearsalError("Il mapping deve coprire esattamente gli account studenti attivi.")
        now = datetime.now(timezone.utc)
        for item in bindings:
            subject = generate_subject_id()
            aliases = tuple(LegacySubjectAlias(alias["class_id"], alias["legacy_student_id"], subject, now) for alias in item["aliases"])
            storage.create_student_subject_binding(StudentSubjectBinding(subject, item["user_id"], True, 1, now, now), aliases)
            resolve_student_identity(item["user_id"], storage.read_student_binding_snapshot(item["user_id"]))
        aliases = storage.list_legacy_subject_aliases()
        owners = {storage.list_user_subject_bindings(user)[0].subject_id: user for user in active_students}
        migrated: dict[Path, dict[str, Any]] = {}
        assignment_ids: set[str] = set()
        for path in sorted((candidate / "teacher-assignments").rglob("*.json")):
            legacy = pilot_data_root._load_object(path, "Assignment legacy")
            assignment_records.validate_assignment_record(legacy)
            record = migrate_legacy_assignment_targets(legacy, aliases)
            round_trip = assignment_records.validate_assignment_record(record)
            if round_trip["id"] in assignment_ids:
                raise RehearsalError("ID assignment duplicato.")
            assignment_ids.add(round_trip["id"])
            for target in record["targets"]:
                user = owners.get(target["subject_id"])
                if user is None:
                    raise RehearsalError("Target senza account autorevole.")
                snapshot = storage.read_student_binding_snapshot(user)
                resolve_assignment_target(user, snapshot, legacy)
                resolution = resolve_assignment_target(user, snapshot, round_trip)
                if resolution.used_legacy_alias or resolution.subject_id != target["subject_id"]:
                    raise RehearsalError("Round-trip assignment non coerente.")
            migrated[path] = record
        # All records pass dry-run before writing any assignment in candidate.
        for path, record in migrated.items():
            pilot_data_root._write_json(path, record)
        after = database_state(candidate / auth)
        pilot_data_root._sqlite_integrity(candidate / auth)
        if any(after["tables"].get(table) != state for table, state in baseline["tables"].items() if table != "schema_migrations"):
            raise RehearsalError("Dati identity storici modificati dalla migrazione.")
        changed = {auth, *(path.relative_to(candidate).as_posix() for path in migrated)}
        candidate_files = inventory(candidate)
        if ({name: entry for name, entry in candidate_files.items() if name not in changed | sidecars}
                != {name: entry for name, entry in before_files.items() if name not in changed}):
            raise RehearsalError("File estranei alla migrazione modificati.")
        if inventory(source) != original or inventory(before) != before_files:
            raise RehearsalError("Sorgente o snapshot pre-upgrade modificato.")
        report = {
            "schema_version": "thebitlab.legacy-rehearsal.v1", "ok": True,
            "deployable": False, "source_schema": 11, "candidate_schema": 12,
            "bindings": len(bindings), "aliases": len(aliases), "assignments": len(migrated),
            "source_unchanged": True, "preupgrade_unchanged": True,
            "legacy_tables_preserved": True, "other_files_preserved": True,
            "source_inventory": original, "preupgrade_inventory": before_files,
            "candidate_inventory": candidate_files,
            "preupgrade_identity": baseline, "candidate_identity": after,
        }
        pilot_data_root._write_json(bundle / "report.json", report)
        pilot_data_root._harden_tree_permissions(bundle)
        if output.exists():
            raise RehearsalError("La destinazione e stata creata durante il rehearsal.")
        bundle.rename(output)
    return {key: report[key] for key in ("ok", "deployable", "source_schema", "candidate_schema", "bindings", "aliases", "assignments")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--offline-copy", action="store_true", help="Attesta copia offline isolata; mai root live")
    args = parser.parse_args()
    try:
        result = rehearse(args.source, args.output, args.mapping, offline_copy=args.offline_copy)
    except Exception as error:
        # Underlying SQLite/OS errors may contain private IDs or paths.
        message = str(error) if isinstance(error, RehearsalError) else "Rehearsal rifiutato; nessuna root pubblicata."
        print(json.dumps({"ok": False, "error": message, "error_type": type(error).__name__}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
