from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_binding import (
    LegacySubjectAlias,
    StudentSubjectBinding,
    resolve_assignment_target,
)
from scripts.thebitlab_identity_ports import (
    IdentityStorageConflictError,
    IdentityStorageCorruptionError,
)
from scripts.thebitlab_identity_sqlite import SCHEMA_VERSION, SqliteIdentityStorage


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
SUBJECT_ID = "subject:11111111111111111111111111111111"
CLASS_ID = "class:3a-tpsi:2026-2027"


def provision(storage: SqliteIdentityStorage) -> StudentSubjectBinding:
    storage.create_user(
        UserAccount("auth-user-001", "Mario Rossi", "student", True, NOW, NOW)
    )
    storage.create_class(
        ClassGroup(CLASS_ID, "3A TPSI", "2026-2027", True, NOW, NOW)
    )
    storage.save_membership(
        ClassMembership("auth-user-001", CLASS_ID, "student", NOW)
    )
    binding = StudentSubjectBinding(
        SUBJECT_ID, "auth-user-001", True, 1, NOW, NOW
    )
    storage.create_student_subject_binding(
        binding,
        (LegacySubjectAlias(CLASS_ID, "rossi-mario", SUBJECT_ID, NOW),),
    )
    return binding


def test_sqlite_binding_alias_and_coherent_snapshot_round_trip(tmp_path) -> None:
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3")
    binding = provision(storage)

    assert storage.read_student_subject_binding(SUBJECT_ID) == binding
    assert storage.list_user_subject_bindings("auth-user-001") == [binding]
    assert storage.list_legacy_subject_aliases(CLASS_ID) == [
        LegacySubjectAlias(CLASS_ID, "rossi-mario", SUBJECT_ID, NOW)
    ]

    snapshot = storage.read_student_binding_snapshot("auth-user-001")
    resolution = resolve_assignment_target(
        "auth-user-001",
        snapshot,
        {
            "id": "assignment:legacy:001",
            "class_id": CLASS_ID,
            "targets": [{"student_id": "rossi-mario"}],
        },
    )
    assert resolution.subject_id == SUBJECT_ID
    assert resolution.used_legacy_alias is True


def test_sqlite_binding_uniqueness_and_alias_ambiguity_are_atomic(tmp_path) -> None:
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3")
    original = provision(storage)
    duplicate_for_user = StudentSubjectBinding(
        "subject:22222222222222222222222222222222",
        original.user_id,
        True,
        1,
        NOW,
        NOW,
    )

    with pytest.raises(IdentityStorageConflictError):
        storage.create_student_subject_binding(duplicate_for_user)

    storage.create_user(
        UserAccount("auth-user-002", "Luca Bianchi", "student", True, NOW, NOW)
    )
    other = StudentSubjectBinding(
        "subject:22222222222222222222222222222222",
        "auth-user-002",
        True,
        1,
        NOW,
        NOW,
    )
    with pytest.raises(IdentityStorageConflictError):
        storage.create_student_subject_binding(
            other,
            (LegacySubjectAlias(CLASS_ID, "rossi-mario", other.subject_id, NOW),),
        )

    assert storage.read_student_subject_binding(other.subject_id) is None
    assert storage.read_student_subject_binding(original.subject_id) == original


def test_alias_can_be_appended_only_for_current_binding_and_membership(tmp_path) -> None:
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3")
    provision(storage)
    before = storage.read_student_binding_snapshot("auth-user-001")
    alias = LegacySubjectAlias(CLASS_ID, "m.rossi", SUBJECT_ID, NOW)

    storage.save_legacy_subject_alias(alias, expected_binding_revision=1)
    after = storage.read_student_binding_snapshot("auth-user-001")

    assert alias in storage.list_legacy_subject_aliases(CLASS_ID)
    assert before.authority_revision != after.authority_revision
    with pytest.raises(IdentityStorageConflictError):
        storage.save_legacy_subject_alias(
            LegacySubjectAlias(CLASS_ID, "stale", SUBJECT_ID, NOW),
            expected_binding_revision=2,
        )
    storage.delete_membership("auth-user-001", CLASS_ID, "student")
    with pytest.raises(IdentityStorageConflictError):
        storage.save_legacy_subject_alias(
            LegacySubjectAlias(CLASS_ID, "removed", SUBJECT_ID, NOW),
            expected_binding_revision=1,
        )


def test_binding_lifecycle_uses_monotonic_compare_and_swap(tmp_path) -> None:
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3")
    original = provision(storage)
    disabled = replace(
        original,
        active=False,
        revision=2,
        updated_at=NOW + timedelta(seconds=1),
    )

    storage.save_student_subject_binding(disabled, expected_revision=1)
    with pytest.raises(IdentityStorageConflictError):
        storage.save_student_subject_binding(
            replace(disabled, active=True, revision=3, updated_at=NOW + timedelta(seconds=2)),
            expected_revision=1,
        )

    assert storage.read_student_subject_binding(SUBJECT_ID) == disabled
    with sqlite3.connect(storage.database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "DELETE FROM student_subject_bindings WHERE subject_id = ?",
                (SUBJECT_ID,),
            )
    assert storage.read_student_subject_binding(SUBJECT_ID) == disabled


def test_migration_v12_upgrades_existing_identity_database(tmp_path) -> None:
    database_path = tmp_path / "identity.sqlite3"
    SqliteIdentityStorage(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute("DROP TABLE legacy_student_subject_aliases")
        connection.execute("DROP TABLE student_subject_bindings")
        connection.execute("DELETE FROM schema_migrations WHERE version = 12")

    upgraded = SqliteIdentityStorage(database_path)
    with sqlite3.connect(database_path) as connection:
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert versions == [(version,) for version in range(1, SCHEMA_VERSION + 1)]
    assert "student_subject_bindings" in tables
    assert "legacy_student_subject_aliases" in tables
    assert upgraded.list_user_subject_bindings("missing") == []


def test_incoherent_storage_failure_is_sanitized(tmp_path) -> None:
    database_path = tmp_path / "identity.sqlite3"
    storage = SqliteIdentityStorage(database_path)
    provision(storage)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE classes SET updated_at = 'secret-malformed-value' WHERE class_id = ?",
            (CLASS_ID,),
        )

    with pytest.raises(IdentityStorageCorruptionError) as captured:
        storage.read_student_binding_snapshot("auth-user-001")

    assert str(captured.value) == "Timestamp persistito non valido."
    assert "secret-malformed-value" not in str(captured.value)
    assert "auth-user-001" not in str(captured.value)
