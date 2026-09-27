from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import assignment_records, pilot_data_root, rehearse_legacy_root as rehearsal
from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_binding import StudentBindingResolutionError, resolve_assignment_target
from scripts.thebitlab_identity_ports import IdentityStorageError
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage


NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)
AUTH = pilot_data_root.DEFAULT_AUTH_DB_PATH


def hashes(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


@pytest.fixture
def legacy(tmp_path):
    root = tmp_path / "s"
    root.mkdir()
    storage = SqliteIdentityStorage(root / AUTH)
    for user, role in (("internal-student", "student"), ("internal-teacher", "teacher")):
        storage.create_user(UserAccount(user, "Synthetic " + role, role, True, NOW, NOW))
    for index in range(4):
        storage.create_class(ClassGroup(f"class-{index}", f"Class {index}", "2026-2027", True, NOW, NOW))
    storage.save_membership(ClassMembership("internal-student", "class-0", "student", NOW))
    with closing(sqlite3.connect(root / AUTH)) as connection:
        connection.execute("DROP TABLE legacy_student_subject_aliases")
        connection.execute("DROP TABLE student_subject_bindings")
        connection.execute("DELETE FROM schema_migrations WHERE version=12")
        connection.commit()
    assignment = assignment_records.build_assignment_record(
        activity_id="activity-1", activity_path="activities/activity-1.json",
        target_type="class", class_id="class-0", assigned_at=NOW.isoformat(),
        due_at=NOW.isoformat(), targets=[{"student_id": "legacy-student"}],
    )
    pilot_data_root._write_json(root / "teacher-assignments/a.json", assignment)
    for relative in ("activities/activity-1.json", "activities/activity-2.json",
                     "activities/imported/registry.txt", "activities/imported/revisions/r.json",
                     "teacher-reports/r.json", "doc/classes/roster.json",
                     "teacher-deliveries/source/main.py", "teacher-deliveries/receipt.json",
                     "teacher-deliveries/final.json", "custom/data.bin", "custom/keep.lock"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic preserved bytes\x00\xff")
    (root / "empty").mkdir()
    mapping = tmp_path / "mapping.json"
    pilot_data_root._write_json(mapping, {
        "schema_version": "thebitlab.legacy-adoption-map.v1",
        "bindings": [{"user_id": "internal-student", "aliases": [
            {"class_id": "class-0", "legacy_student_id": "legacy-student"}]}],
    })
    return root, mapping, tmp_path / "out"


def run(legacy):
    source, mapping, output = legacy
    return rehearsal.rehearse(source, output, mapping, offline_copy=True)


def test_complete_copy_preserves_legacy_and_resolves_targets_and_rollback(legacy, tmp_path):
    source, mapping, output = legacy
    original = hashes(source)
    assert run(legacy) == {"ok": True, "deployable": False, "source_schema": 11,
                           "candidate_schema": 12, "bindings": 1, "aliases": 1, "assignments": 1}
    assert hashes(source) == original
    before, candidate = output / "preupgrade", output / "candidate"
    report = json.loads((output / "report.json").read_text())
    assert report["legacy_tables_preserved"] and report["other_files_preserved"]
    assert report["preupgrade_identity"]["tables"]["users"]["rows"] == 2
    assert report["candidate_identity"]["tables"]["classes"]["rows"] == 4
    assert report["candidate_identity"]["tables"]["class_memberships"]["rows"] == 1
    for root in (before, candidate):
        assert not (root / pilot_data_root.ROOT_MARKER).exists()
        assert (root / "empty").is_dir()
    for name, digest in original.items():
        if name not in {AUTH, "teacher-assignments/a.json"}:
            assert hashes(candidate)[name] == digest
        if name != AUTH:
            assert hashes(before)[name] == digest
    old_record = json.loads((source / "teacher-assignments/a.json").read_text())
    new_record = json.loads((candidate / "teacher-assignments/a.json").read_text())
    storage = SqliteIdentityStorage(candidate / AUTH)
    snapshot = storage.read_student_binding_snapshot("internal-student")
    assert resolve_assignment_target("internal-student", snapshot, old_record).used_legacy_alias
    assert not resolve_assignment_target("internal-student", snapshot, new_record).used_legacy_alias
    without_subject = json.loads(json.dumps(new_record))
    del without_subject["targets"][0]["subject_id"]
    assert without_subject == old_record
    frozen = hashes(before)
    shutil.copytree(before, tmp_path / "rollback")
    assert rehearsal.database_state(tmp_path / "rollback" / AUTH)["versions"] == list(range(1, 12))
    assert hashes(before) == frozen
    assert rehearsal.inventory(before) == report["preupgrade_inventory"]


def test_wal_is_absorbed_from_private_copy_without_changing_source(legacy, tmp_path):
    source, mapping, output = legacy
    with closing(sqlite3.connect(source / AUTH)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("UPDATE users SET display_name='Only in WAL' WHERE user_id='internal-student'")
        connection.commit()
        offline = tmp_path / "offline"
        shutil.copytree(source, offline)
        assert (offline / (AUTH + "-wal")).stat().st_size > 0
    original = hashes(offline)
    run((offline, mapping, output))
    assert hashes(offline) == original
    assert not (output / "preupgrade" / (AUTH + "-wal")).exists()
    with closing(sqlite3.connect(output / "preupgrade" / AUTH)) as connection:
        assert connection.execute("SELECT display_name FROM users WHERE user_id='internal-student'").fetchone() == ("Only in WAL",)


@pytest.mark.parametrize("fault", ["missing-user", "wrong-user", "duplicate-user", "duplicate-alias",
                                  "wrong-class", "missing-alias", "unknown-field", "duplicate-key"])
def test_bad_admin_mapping_never_publishes_or_changes_source(legacy, fault):
    source, mapping, output = legacy
    data = json.loads(mapping.read_text())
    item = data["bindings"][0]
    if fault == "missing-user":
        data["bindings"] = []
    elif fault == "wrong-user":
        item["user_id"] = "internal-teacher"
    elif fault == "duplicate-user":
        data["bindings"].append(item)
    elif fault == "duplicate-alias":
        item["aliases"].append(item["aliases"][0])
    elif fault == "wrong-class":
        item["aliases"][0]["class_id"] = "class-1"
    elif fault == "missing-alias":
        item["aliases"] = []
    elif fault == "unknown-field":
        item["email"] = "must-not-be-used"
    pilot_data_root._write_json(mapping, data)
    if fault == "duplicate-key":
        mapping.write_text('{"schema_version":"x","schema_version":"y","bindings":[]}')
    original = hashes(source)
    with pytest.raises((rehearsal.RehearsalError, pilot_data_root.PilotRootError,
                        StudentBindingResolutionError, IdentityStorageError)):
        run(legacy)
    assert not output.exists()
    assert hashes(source) == original
    assert not list(output.parent.glob(".legacy-*"))


@pytest.mark.parametrize("fault", ["missing-target", "duplicate-target", "late-invalid", "duplicate-id"])
def test_assignment_errors_abort_whole_dry_run(legacy, fault):
    source, mapping, output = legacy
    path = source / "teacher-assignments/a.json"
    record = json.loads(path.read_text())
    if fault == "missing-target":
        record["targets"][0]["student_id"] = "unmapped"
    elif fault == "duplicate-target":
        record["targets"].append(record["targets"][0])
    elif fault == "late-invalid":
        pilot_data_root._write_json(source / "teacher-assignments/z.json", {"invalid": True})
    elif fault == "duplicate-id":
        pilot_data_root._write_json(source / "teacher-assignments/z.json", record)
    pilot_data_root._write_json(path, record)
    original = hashes(source)
    with pytest.raises((ValueError, rehearsal.RehearsalError, StudentBindingResolutionError)):
        run(legacy)
    assert hashes(source) == original
    assert not output.exists()


@pytest.mark.parametrize("fault", ["marker", "second-db", "secret", "schema12", "corrupt-db"])
def test_unsupported_root_is_rejected(legacy, fault):
    source, mapping, output = legacy
    if fault == "marker":
        (source / pilot_data_root.ROOT_MARKER).write_text("{}")
    elif fault == "second-db":
        (source / "other.sqlite3").write_bytes(b"unexpected")
    elif fault == "secret":
        (source / "runtime.env").write_text("SYNTHETIC=value")
    elif fault == "schema12":
        SqliteIdentityStorage(source / AUTH)
    else:
        (source / AUTH).write_bytes(b"invalid SQLite")
    original = hashes(source)
    with pytest.raises((rehearsal.RehearsalError, pilot_data_root.PilotRootError)):
        run(legacy)
    assert hashes(source) == original
    assert not output.exists()


def test_destination_safety_and_explicit_offline_attestation(legacy):
    source, mapping, output = legacy
    with pytest.raises(rehearsal.RehearsalError, match="attestazione"):
        rehearsal.rehearse(source, output, mapping)
    for target in (source, source / "nested", source.parent):
        with pytest.raises(rehearsal.RehearsalError):
            rehearsal.rehearse(source, target, mapping, offline_copy=True)
    output.mkdir()
    (output / "keep").write_text("keep")
    with pytest.raises(rehearsal.RehearsalError):
        run(legacy)
    assert (output / "keep").read_text() == "keep"


def test_source_mutation_is_detected_and_no_output_is_published(legacy, monkeypatch):
    source, mapping, output = legacy
    real_copytree = shutil.copytree

    def mutate_after_copy(src, dst, *args, **kwargs):
        result = real_copytree(src, dst, *args, **kwargs)
        if Path(src) == source:
            (source / "concurrent.txt").write_text("writer must be stopped")
        return result

    monkeypatch.setattr(shutil, "copytree", mutate_after_copy)
    with pytest.raises(rehearsal.RehearsalError, match="cambiata"):
        run(legacy)
    assert not output.exists()


def test_symlink_is_rejected(legacy, tmp_path):
    source, mapping, output = legacy
    outside = tmp_path / "outside"
    outside.write_text("private")
    try:
        (source / "link").symlink_to(outside)
    except OSError:
        pytest.skip("Symlink non disponibile per questo utente Windows")
    with pytest.raises(rehearsal.RehearsalError, match="Link"):
        run(legacy)
    assert outside.read_text() == "private"
    assert not output.exists()


def test_inventory_does_not_silently_skip_unreadable_directories(legacy, monkeypatch):
    source, mapping, output = legacy

    def unreadable_walk(root, *, followlinks, onerror):
        onerror(PermissionError("private path must not reach the CLI"))
        return iter(())

    monkeypatch.setattr(rehearsal.os, "walk", unreadable_walk)
    with pytest.raises(rehearsal.RehearsalError, match="non leggibile"):
        run(legacy)
    assert not output.exists()


@pytest.mark.parametrize("offline", [True, False])
def test_cli_result_and_offline_guard(legacy, offline):
    source, mapping, output = legacy
    command = [sys.executable, str(Path(rehearsal.__file__)), "--source", str(source),
               "--output", str(output), "--mapping", str(mapping)]
    if offline:
        command.append("--offline-copy")
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    payload = json.loads(result.stdout)
    assert payload["ok"] is offline
    assert result.returncode == (0 if offline else 1)
    assert result.stderr == ""
    assert output.exists() is offline
    assert str(source) not in result.stdout
