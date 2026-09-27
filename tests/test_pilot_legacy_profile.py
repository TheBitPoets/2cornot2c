from __future__ import annotations

import json
import hashlib
import shlex
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import assignment_records, pilot_data_root as roots, pilot_legacy_profile as profile
from scripts import pilot_service_launcher as launcher, rehearse_legacy_root as rehearsal
from scripts import course_board_server
from scripts import validate_pilot_deployment as deployment
from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

ROOT = Path(__file__).resolve().parents[1]
AUTH = roots.DEFAULT_AUTH_DB_PATH
NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)


@pytest.fixture
def bundle(tmp_path):
    source = tmp_path / "s"
    storage = SqliteIdentityStorage(source / AUTH)
    for user, role in (("s1", "student"), ("t1", "teacher")):
        storage.create_user(UserAccount(user, user, role, True, NOW, NOW))
    storage.create_class(ClassGroup("c1", "Class", "2026-2027", True, NOW, NOW))
    for user, role in (("s1", "student"), ("t1", "teacher")):
        storage.save_membership(ClassMembership(user, "c1", role, NOW))
    with closing(sqlite3.connect(source / AUTH)) as connection:
        connection.execute("DROP TABLE legacy_student_subject_aliases")
        connection.execute("DROP TABLE student_subject_bindings")
        connection.execute("DELETE FROM schema_migrations WHERE version=12")
        connection.commit()
    activity = json.loads((ROOT / "activities/examples/homework_variables.json").read_text(encoding="utf-8"))
    roots._write_json(source / "activities/a.json", activity)
    roots._write_json(source / "teacher-assignments/a.json", assignment_records.build_assignment_record(
        activity_id=activity["id"], activity_path="activities/a.json", target_type="class",
        class_id="c1", assigned_at=NOW.isoformat(), due_at=NOW.isoformat(),
        targets=[{"student_id": "legacy-1"}],
    ))
    roots._write_json(source / "doc/classes/c.json", {"id": "c1", "students": [{"id": "legacy-1", "active": True}]})
    roots._write_json(source / "doc/course_design.json", {"years": []})
    (source / "empty").mkdir()
    (source / "custom.lock").write_bytes(b"application state")
    (source / "teacher-deliveries").mkdir()
    (source / "teacher-deliveries/final.bin").write_bytes(b"submission")
    mapping = tmp_path / "map.json"
    roots._write_json(mapping, {"schema_version": "thebitlab.legacy-adoption-map.v1", "bindings": [
        {"user_id": "s1", "aliases": [{"class_id": "c1", "legacy_student_id": "legacy-1"}]}]})
    output = tmp_path / "b"
    rehearsal.rehearse(source, output, mapping, offline_copy=True)
    return output


def topology(path):
    return roots.topology_from_paths(path, deployment_id="historical-test", profile=profile.PROFILE)


def test_adoption_backup_restore_and_preupgrade_are_isolated(bundle, tmp_path):
    baseline = profile.inventory(bundle)
    target = topology(tmp_path / "a")
    result = profile.adopt(target, bundle, offline_copy=True)
    assert result["ok"] and result["startup_smoke"] and not result["demo_check"]
    assert profile.inventory(bundle) == baseline
    marker = roots._load_object(target.root / roots.ROOT_MARKER, "marker")
    Draft202012Validator(json.loads((ROOT / "schemas/pilot-legacy-root.schema.json").read_text())).validate(marker)
    before = profile.inventory(target.root)
    roots.validate_root(target, run_demo_check=False)
    assert profile.inventory(target.root) == before
    backup = tmp_path / "backup"
    roots.create_backup(target, backup)
    manifest = roots._load_object(backup / "manifest.json", "manifest")
    Draft202012Validator(json.loads((ROOT / "schemas/pilot-backup-manifest-v2.schema.json").read_text())).validate(manifest)
    assert "empty" in manifest["directories"]
    assert "custom.lock" in {item["path"] for item in manifest["files"]}
    restored = tmp_path / "r"
    restored_result = roots.restore_backup(backup, restored)
    assert restored_result["startup_smoke"] and restored_result["profile"] == profile.PROFILE
    restored_inventory = profile.inventory(restored)
    assert {k: v for k, v in restored_inventory.items() if k != AUTH} == {k: v for k, v in before.items() if k != AUTH}
    assert rehearsal.database_state(restored / AUTH) == rehearsal.database_state(target.auth_db_path)
    assert profile.inventory(target.root) == before
    assert profile.inventory(bundle) == baseline
    assert rehearsal.database_state(bundle / "preupgrade" / AUTH)["versions"] == list(range(1, 12))
    with pytest.raises(roots.PilotRootError):
        roots.validate_root(roots.topology_from_paths(target.root, deployment_id="historical-test"))
    with pytest.raises(roots.PilotRootError):
        roots.bootstrap(target)


@pytest.mark.parametrize("change", ["roster", "activity", "assignment", "membership", "binding", "duplicate", "design", "second-db", "secret"])
def test_current_state_fails_closed_after_adoption(bundle, tmp_path, change):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    if change == "roster":
        roots._write_json(target.root / "doc/classes/c.json", {"id": "c1", "students": []})
    elif change == "activity":
        (target.root / "activities/a.json").unlink()
    elif change == "assignment":
        path = target.root / "teacher-assignments/a.json"
        record = roots._load_object(path, "assignment")
        record["targets"][0].pop("subject_id")
        roots._write_json(path, record)
    elif change in {"membership", "binding"}:
        with closing(sqlite3.connect(target.auth_db_path)) as connection:
            connection.execute("DELETE FROM class_memberships WHERE user_id='s1'" if change == "membership"
                               else "UPDATE users SET active=0 WHERE user_id='s1'")
            connection.commit()
    elif change == "duplicate":
        (target.root / "teacher-assignments/b.json").write_bytes((target.root / "teacher-assignments/a.json").read_bytes())
    elif change == "design":
        (target.root / "doc/course_design.json").unlink()
    else:
        (target.root / ("other.db" if change == "second-db" else "password.env")).write_text("invalid")
    with pytest.raises(RuntimeError):
        roots.validate_root(target, run_demo_check=False)
    with pytest.raises(RuntimeError):
        roots.create_backup(target, tmp_path / "backup")
    assert not (tmp_path / "backup").exists()


def test_adoption_refuses_changed_evidence_and_no_attestation(bundle, tmp_path):
    target = topology(tmp_path / "a")
    with pytest.raises(roots.PilotRootError):
        profile.adopt(target, bundle)
    (bundle / "candidate/custom.lock").write_bytes(b"changed")
    with pytest.raises(roots.PilotRootError, match="modificato"):
        profile.adopt(target, bundle, offline_copy=True)
    assert not target.root.exists()
    assert not list(tmp_path.glob(".adopt-*"))


def test_startup_smoke_preserves_pending_recovery_files(bundle, tmp_path):
    source = tmp_path / "s"
    roots._write_json(source / "teacher-reports/report.json", {"state": "current"})
    roots._write_json(source / "teacher-reports/.report.json.interrupted.rollback", {"state": "previous"})
    second = tmp_path / "b2"
    rehearsal.rehearse(source, second, tmp_path / "map.json", offline_copy=True)
    candidate = profile.inventory(second / "candidate")
    target = topology(tmp_path / "a")
    profile.adopt(target, second, offline_copy=True)
    actual = profile.inventory(target.root)
    actual.pop(roots.ROOT_MARKER)
    assert actual == candidate
    backup = tmp_path / "backup"
    roots.create_backup(target, backup)
    restored = tmp_path / "r"
    roots.restore_backup(backup, restored)
    restored_entries = profile.inventory(restored)
    target_entries = profile.inventory(target.root)
    restored_entries.pop(AUTH)
    target_entries.pop(AUTH)
    assert restored_entries == target_entries
    assert rehearsal.database_state(restored / AUTH) == rehearsal.database_state(target.auth_db_path)


def test_startup_smoke_does_not_recover_callers_root(bundle, tmp_path, monkeypatch):
    other = tmp_path / "other"
    roots._write_json(other / "teacher-reports/report.json", {"state": "current"})
    roots._write_json(other / "teacher-reports/.report.json.interrupted.rollback", {"state": "previous"})
    before = profile.inventory(other)
    monkeypatch.setattr(course_board_server, "ROOT", other)
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    assert course_board_server.ROOT == other
    assert profile.inventory(other) == before


def test_invalid_candidate_never_publishes_marker(bundle, tmp_path):
    path = bundle / "candidate/doc/classes/c.json"
    roots._write_json(path, {"id": "unknown", "students": []})
    report = roots._load_object(bundle / "report.json", "report")
    report["candidate_inventory"] = profile.inventory(bundle / "candidate")
    roots._write_json(bundle / "report.json", report)
    with pytest.raises(roots.PilotRootError):
        profile.adopt(topology(tmp_path / "a"), bundle, offline_copy=True)
    assert not (tmp_path / "a").exists()
    assert not (bundle / "candidate" / roots.ROOT_MARKER).exists()


def test_restore_rejects_lost_empty_directory(bundle, tmp_path):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    backup = tmp_path / "backup"
    roots.create_backup(target, backup)
    (backup / "payload/empty").rmdir()
    with pytest.raises(roots.PilotRootError, match="Directory"):
        roots.restore_backup(backup, tmp_path / "r")
    assert not (tmp_path / "r").exists()


def test_backup_consumes_pending_wal(bundle, tmp_path):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    with closing(sqlite3.connect(target.auth_db_path)) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("UPDATE users SET display_name='Changed' WHERE user_id='t1'")
        writer.commit()
        backup = tmp_path / "backup"
        roots.create_backup(target, backup)
        assert (target.root / (AUTH + "-wal")).stat().st_size > 0
        assert not (backup / "payload" / (AUTH + "-wal")).exists()
        assert rehearsal.database_state(backup / "payload" / AUTH) == rehearsal.database_state(target.auth_db_path)


def test_root_lock_blocks_historical_backup(bundle, tmp_path):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    lock = course_board_server.DataRootProcessLock(target.root)
    lock.acquire()
    try:
        with pytest.raises(roots.PilotRootError, match="in uso"):
            roots.create_backup(target, tmp_path / "backup")
    finally:
        lock.release()
    assert not (tmp_path / "backup").exists()


def test_restore_failure_preserves_concurrently_created_destination(bundle, tmp_path, monkeypatch):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    backup = tmp_path / "backup"
    roots.create_backup(target, backup)
    restored = tmp_path / "r"
    def race(_root):
        restored.mkdir()
        (restored / "owned-by-other").write_text("preserve")
    monkeypatch.setattr(roots, "_controlled_startup_smoke", race)
    with pytest.raises(roots.PilotRootError, match="Destinazione"):
        roots.restore_backup(backup, restored)
    assert (restored / "owned-by-other").read_text() == "preserve"


def test_nested_catalog_and_json_asset(bundle, tmp_path):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    activity = roots._load_object(target.root / "activities/a.json", "activity")
    activity["id"] = "another-activity"
    roots._write_json(target.root / "activities/examples/nested.json", activity)
    asset = target.root / "activities/examples/assets/data.json"
    asset.parent.mkdir()
    asset.write_text('["opaque asset"]')
    assert roots.validate_root(target)["activities"] == 2


def test_unsupported_marker_fails_closed(bundle, tmp_path):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    path = target.root / roots.ROOT_MARKER
    marker = roots._load_object(path, "marker")
    marker["schema_version"] = "thebitlab.pilot-root.v99"
    roots._write_json(path, marker)
    with pytest.raises(roots.PilotRootError, match="Marker"):
        roots.validate_root(target)


@pytest.mark.parametrize("change", ["version", "profile", "extra", "traversal", "extra-file"])
def test_invalid_backup_contract_refused_before_restore(bundle, tmp_path, change):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    backup = tmp_path / "backup"
    roots.create_backup(target, backup)
    path = backup / "manifest.json"
    manifest = roots._load_object(path, "manifest")
    if change == "version":
        manifest["schema_version"] = "thebitlab.pilot-backup.v99"
    elif change == "profile":
        manifest["profile"] = "pilot-demo"
    elif change == "extra":
        manifest["unexpected"] = True
    elif change == "traversal":
        manifest["files"][0]["path"] = "../outside"
    else:
        (backup / "payload/extra").write_text("undeclared")
    roots._write_json(path, manifest)
    (backup / "manifest.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "  manifest.json\n")
    with pytest.raises(roots.PilotRootError):
        roots.restore_backup(backup, tmp_path / "r")
    assert not (tmp_path / "r").exists()


def test_adoption_cli_requires_profile_and_offline_flag(bundle, tmp_path, capsys):
    argv = ["adopt-legacy", "--root", str(tmp_path / "a"), "--rehearsal", str(bundle),
            "--deployment-id", "historical-test", "--profile", profile.PROFILE]
    assert roots.main(argv) == 2
    assert not (tmp_path / "a").exists()
    capsys.readouterr()
    assert roots.main([*argv, "--offline-copy"]) == 0
    assert json.loads(capsys.readouterr().out)["adopted"] is True
    assert roots.main(["validate", "--root", str(tmp_path / "a"), "--deployment-id", "historical-test",
                       "--profile", profile.PROFILE]) == 0


def test_manifest_renderer_launcher_select_explicit_profile(bundle, tmp_path, monkeypatch):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    manifest = deployment.load_json(ROOT / "deploy/pilot/candidate.example.json")
    manifest["data"]["profile"] = profile.PROFILE
    rendered = tmp_path / "rendered"
    deployment.render_bundle(manifest, rendered)
    unit = (rendered / "systemd/thebitlab.service").read_text()
    start = next(line.removeprefix("ExecStart=") for line in unit.splitlines() if line.startswith("ExecStart="))
    argv = shlex.split(start)[2:]
    argv[argv.index("--root") + 1] = str(target.root)
    argv[argv.index("--deployment-id") + 1] = target.deployment_id
    calls = []
    def after_validation(_path):
        calls.append("validated-before-secrets")
        raise OSError("stop before secrets")
    monkeypatch.setattr(launcher, "check_environment_file", after_validation)
    assert launcher.main(argv) == 2
    assert calls == ["validated-before-secrets"]
    argv[argv.index("--root-profile") + 1] = "pilot-demo"
    calls.clear()
    assert launcher.main(argv) == 2
    assert calls == []


@pytest.mark.parametrize("profile_name,auth", [("unknown", AUTH), (profile.PROFILE, "other.sqlite3")])
def test_deployment_rejects_incompatible_historical_topology(profile_name, auth):
    manifest = deployment.load_json(ROOT / "deploy/pilot/candidate.example.json")
    manifest["data"].update(profile=profile_name, auth_db_path=auth)
    with pytest.raises(deployment.DeploymentValidationError):
        deployment.validate_manifest(manifest)


@pytest.mark.parametrize("path", ["../outside", "a//b", "C:/absolute", "a/CON", "a/trailing.", "a\\b", "/absolute"])
def test_nonportable_paths_rejected(path):
    with pytest.raises(roots.PilotRootError):
        profile.relative_path(path)
