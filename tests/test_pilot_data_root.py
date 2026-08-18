"""Integrated contract tests for the canonical pilot root and backup/restore."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import course_board_server, pilot_data_root, pilot_service_launcher
from scripts.thebitlab_identity_sqlite import SCHEMA_VERSION, SqliteIdentityStorage


def tree_digest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def prepared_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("pilot-root") / "data"
    topology = pilot_data_root.topology_from_paths(root)
    result = pilot_data_root.bootstrap(topology)
    assert result["ok"] is True
    return root


@pytest.fixture
def canonical_root(prepared_root: Path, tmp_path: Path) -> Path:
    root = tmp_path / "data"
    shutil.copytree(prepared_root, root)
    return root


def test_bootstrap_from_empty_root_is_complete_and_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "canonical"
    topology = pilot_data_root.topology_from_paths(root)

    first = pilot_data_root.bootstrap(topology)
    before = tree_digest(root)
    second = pilot_data_root.bootstrap(topology)

    assert first["created"] is True
    assert second["created"] is False
    assert second["idempotent"] is True
    assert second["demo_check"] is True
    assert tree_digest(root) == before
    assert (root / "doc/course_design.json").is_file()
    assert (root / "doc/calendars/as_2026_2027.json").is_file()
    roster = json.loads((root / "doc/classes/demo-3a.json").read_text(encoding="utf-8"))
    assert roster["id"] == pilot_data_root.DEMO_CLASS_ID
    assert {student["id"] for student in roster["students"]} == {
        "rossi-mario",
        "bianchi-luca",
    }
    assert list(root.glob("teacher-help-events/*/*/events.json"))
    assert list(root.glob("examples/**/attempts/*.json"))


def test_partial_or_incoherent_root_fails_closed_without_reset(tmp_path: Path) -> None:
    root = tmp_path / "partial"
    root.mkdir()
    sentinel = root / "do-not-delete.txt"
    sentinel.write_text("preserve", encoding="utf-8")

    with pytest.raises(pilot_data_root.PilotRootError, match="parziale"):
        pilot_data_root.bootstrap(pilot_data_root.topology_from_paths(root))

    assert sentinel.read_text(encoding="utf-8") == "preserve"


def test_missing_required_state_and_ambiguous_auth_database_fail_closed(canonical_root: Path) -> None:
    topology = pilot_data_root.topology_from_paths(canonical_root)
    report = canonical_root / "teacher-reports/demo/python-demo-somma-001.json"
    report_bytes = report.read_bytes()
    report.unlink()
    with pytest.raises(pilot_data_root.PilotRootError, match="parziale"):
        pilot_data_root.validate_root(topology)
    report.write_bytes(report_bytes)

    shutil.copyfile(
        canonical_root / pilot_data_root.DEFAULT_AUTH_DB_PATH,
        canonical_root / "second.sqlite3",
    )
    with pytest.raises(pilot_data_root.PilotRootError, match="ambigua"):
        pilot_data_root.validate_root(topology)


def test_same_root_double_instance_is_rejected(canonical_root: Path, tmp_path: Path) -> None:
    topology = pilot_data_root.topology_from_paths(canonical_root)
    lock = course_board_server.DataRootProcessLock(canonical_root)
    lock.acquire()
    try:
        with pytest.raises(pilot_data_root.PilotRootError, match="doppia istanza"):
            pilot_data_root.validate_root(topology)
        with pytest.raises(pilot_data_root.PilotRootError, match="doppia istanza"):
            pilot_data_root.create_backup(topology, tmp_path / "backup")
    finally:
        lock.release()


def test_auth_path_is_root_relative_portable_and_unambiguous(tmp_path: Path) -> None:
    nested = pilot_data_root.topology_from_paths(
        tmp_path / "root", "state/auth/identity.sqlite3"
    )

    assert nested.auth_db_path == (tmp_path / "root/state/auth/identity.sqlite3").resolve()
    with pytest.raises(pilot_data_root.PilotRootError, match="assoluto"):
        pilot_data_root.topology_from_paths(Path("relative-root"))
    for invalid in (
        "../identity.sqlite3",
        "/var/lib/identity.sqlite3",
        r"state\auth\identity.sqlite3",
        "state/./identity.sqlite3",
        "state/auth.txt",
    ):
        with pytest.raises(pilot_data_root.PilotRootError):
            pilot_data_root.topology_from_paths(tmp_path / "root", invalid)


def test_backup_manifest_and_payload_are_deterministic_and_secret_free(
    canonical_root: Path, tmp_path: Path
) -> None:
    topology = pilot_data_root.topology_from_paths(canonical_root)
    first = tmp_path / "backup-first"
    second = tmp_path / "backup-second"

    first_result = pilot_data_root.create_backup(topology, first)
    second_result = pilot_data_root.create_backup(topology, second)

    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    assert (first / "manifest.sha256").read_bytes() == (second / "manifest.sha256").read_bytes()
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas/pilot-backup-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(manifest)
    assert manifest["consistency"].endswith("sqlite-backup-api")
    assert manifest["files"] == sorted(manifest["files"], key=lambda item: item["path"])
    assert not any(item["path"].endswith(".lock") for item in manifest["files"])
    assert not any(
        item["path"].endswith(("-journal", "-shm", "-wal"))
        for item in manifest["files"]
    )
    serialized = (first / "manifest.json").read_text(encoding="utf-8").lower()
    assert "client_secret" not in serialized
    assert "teacher_token" not in serialized
    assert first_result["duration_seconds"] >= 0
    assert first_result["target_assessment"].startswith("local measurement only")


def test_secret_inside_root_causes_backup_to_fail_instead_of_leaking(
    canonical_root: Path, tmp_path: Path
) -> None:
    secret = canonical_root / ".secrets/oauth-token.txt"
    secret.parent.mkdir()
    secret.write_text("DO-NOT-BACK-UP", encoding="utf-8")
    output = tmp_path / "backup"

    with pytest.raises(pilot_data_root.PilotRootError, match="Secret"):
        pilot_data_root.create_backup(
            pilot_data_root.topology_from_paths(canonical_root), output
        )

    assert not output.exists()


def test_restore_is_isolated_checks_integrity_binding_demo_and_startup(
    canonical_root: Path, tmp_path: Path
) -> None:
    topology = pilot_data_root.topology_from_paths(canonical_root)
    backup = tmp_path / "backup"
    target = tmp_path / "restored"
    pilot_data_root.create_backup(topology, backup)
    source_before = tree_digest(canonical_root)
    backup_before = tree_digest(backup)

    result = pilot_data_root.restore_backup(backup, target)

    assert result["ok"] is True
    assert result["sqlite_integrity"] is True
    assert result["migrations"] == SCHEMA_VERSION
    assert result["binding_702"] is True
    assert result["demo_check"] is True
    assert result["startup_smoke"] is True
    assert result["duration_seconds"] >= 0
    assert tree_digest(canonical_root) == source_before
    assert tree_digest(backup) == backup_before
    storage = SqliteIdentityStorage(target / pilot_data_root.DEFAULT_AUTH_DB_PATH)
    assert len(storage.list_users()) == 3
    assert len(storage.list_class_memberships(pilot_data_root.DEMO_CLASS_ID)) == 3


def test_restore_rejects_checksum_tampering_and_existing_target(
    canonical_root: Path, tmp_path: Path
) -> None:
    backup = tmp_path / "backup"
    pilot_data_root.create_backup(
        pilot_data_root.topology_from_paths(canonical_root), backup
    )
    target = tmp_path / "target"
    target.mkdir()
    with pytest.raises(pilot_data_root.PilotRootError, match="nuova"):
        pilot_data_root.restore_backup(backup, target)

    target.rmdir()
    payload_file = next(
        path
        for path in (backup / "payload").rglob("*")
        if path.is_file() and path.suffix == ".json"
    )
    payload_file.write_bytes(payload_file.read_bytes() + b"tampered")
    with pytest.raises(pilot_data_root.PilotRootError, match="Dimensione|Checksum"):
        pilot_data_root.restore_backup(backup, target)
    assert not target.exists()


def test_restore_rejects_partial_identity_migration_artifact(
    canonical_root: Path, tmp_path: Path
) -> None:
    backup = tmp_path / "backup"
    pilot_data_root.create_backup(
        pilot_data_root.topology_from_paths(canonical_root), backup
    )
    database = backup / "payload" / pilot_data_root.DEFAULT_AUTH_DB_PATH
    with sqlite3.connect(database) as connection:
        connection.execute(
            "DELETE FROM schema_migrations WHERE version = ?", (SCHEMA_VERSION,)
        )
    manifest_path = backup / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative = pilot_data_root.DEFAULT_AUTH_DB_PATH
    entry = next(item for item in manifest["files"] if item["path"] == relative)
    entry["size"] = database.stat().st_size
    entry["sha256"] = hashlib.sha256(database.read_bytes()).hexdigest()
    manifest_path.write_bytes(pilot_data_root._canonical_json(manifest))
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    (backup / "manifest.sha256").write_text(
        f"{digest}  manifest.json\n", encoding="ascii"
    )

    target = tmp_path / "restored"
    with pytest.raises(pilot_data_root.PilotRootError, match="Migrazione"):
        pilot_data_root.restore_backup(backup, target)

    assert not target.exists()


def test_launcher_validates_canonical_root_before_reading_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def reject_root(*_args, **_kwargs) -> None:
        calls.append("root")
        raise pilot_data_root.PilotRootError("root incompleta")

    def unexpected_secret_read(_path: Path) -> None:
        calls.append("secret")

    monkeypatch.setattr(pilot_service_launcher.pilot_data_root, "validate_root", reject_root)
    monkeypatch.setattr(pilot_service_launcher, "check_environment_file", unexpected_secret_read)
    result = pilot_service_launcher.main(
        [
            "--environment-file",
            str(tmp_path / "missing.env"),
            "--deployment-id",
            "pilot-test",
            "--deployment-revision",
            "a" * 40,
            "--lock-directory",
            str(tmp_path / "locks"),
            "--auth-db-path",
            pilot_data_root.DEFAULT_AUTH_DB_PATH,
            "--trusted-proxy-cidrs",
            "127.0.0.1/32",
            "--google-redirect-uri",
            "https://candidate.example.edu/auth/google/callback",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--root",
            str(tmp_path / "data"),
            "--enable-google-auth",
        ]
    )

    assert result == 2
    assert calls == ["root"]
