from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_identity import (
    ClassGroup,
    ClassMembership,
    ExternalGroupMapping,
    ExternalIdentity,
    TuiPairing,
    UserAccount,
    UserSession,
    authorize_pairing,
    consume_pairing,
)
from scripts.thebitlab_identity_sqlite import (
    IdentityStorageConflictError,
    IdentityStorageCorruptionError,
    IdentityStorageError,
    IdentityStorageGenerationConflictError,
    IdentityStorageNotFoundError,
    SCHEMA_VERSION,
    SqliteIdentityStorage,
)


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)
SESSION_DIGEST = "sha256:" + "a" * 64
PAIRING_DIGEST = "hmac-sha256:" + "b" * 64


def account(user_id: str = "user-01", **overrides) -> UserAccount:
    values = {
        "user_id": user_id,
        "display_name": f"Utente {user_id}",
        "role": "student",
        "active": True,
        "created_at": NOW,
        "updated_at": NOW,
        "primary_email": f"{user_id}@example.test",
    }
    values.update(overrides)
    return UserAccount(**values)


def class_group(class_id: str = "class-01", **overrides) -> ClassGroup:
    values = {
        "class_id": class_id,
        "label": f"Classe {class_id}",
        "school_year": "2026/2027",
        "active": True,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return ClassGroup(**values)


def session(
    session_id: str = "session-01",
    digest: str = SESSION_DIGEST,
    **overrides,
) -> UserSession:
    values = {
        "session_id": session_id,
        "user_id": "user-01",
        "token_digest": digest,
        "created_at": NOW,
        "expires_at": LATER,
        "last_seen_at": NOW,
    }
    values.update(overrides)
    return UserSession(**values)


def pairing(
    pairing_id: str = "pairing-01",
    digest: str = PAIRING_DIGEST,
    **overrides,
) -> TuiPairing:
    values = {
        "pairing_id": pairing_id,
        "code_digest": digest,
        "status": "pending",
        "created_at": NOW,
        "expires_at": LATER,
    }
    values.update(overrides)
    return TuiPairing(**values)


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "identity.sqlite3"


@pytest.fixture
def storage(database_path):
    return SqliteIdentityStorage(database_path)


def test_in_memory_database_is_rejected_instead_of_losing_schema_between_connections() -> None:
    with pytest.raises(IdentityStorageError, match="file temporaneo"):
        SqliteIdentityStorage(":memory:")


def test_connection_open_error_is_translated(database_path) -> None:
    database_path.mkdir()

    with pytest.raises(IdentityStorageError, match="aprire o configurare") as captured:
        SqliteIdentityStorage(database_path)

    assert isinstance(captured.value.__cause__, sqlite3.OperationalError)


def test_migration_is_idempotent_and_rejects_newer_schema(database_path) -> None:
    SqliteIdentityStorage(database_path)
    SqliteIdentityStorage(database_path)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall() == [
            (version,) for version in range(1, SCHEMA_VERSION + 1)
        ]
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION + 1, "2026-09-01T08:00:00.000000Z"),
        )

    with pytest.raises(IdentityStorageError, match="piu recente"):
        SqliteIdentityStorage(database_path)


def test_migration_v2_upgrades_and_backfills_existing_v1_identity(database_path) -> None:
    storage = SqliteIdentityStorage(database_path)
    user = account()
    identity = ExternalIdentity("user-01", "google", "subject-01", NOW)
    storage.provision_user_with_identity(user, identity)

    with sqlite3.connect(database_path) as connection:
        connection.execute("DROP TABLE external_identity_generations")
        connection.execute("DELETE FROM schema_migrations WHERE version = 2")

    upgraded = SqliteIdentityStorage(database_path)
    with sqlite3.connect(database_path) as connection:
        assert connection.execute(
            "SELECT provider, subject, linked_at FROM external_identity_generations"
        ).fetchall() == [
            ("google", "subject-01", "2026-09-01T08:00:00.000000Z")
        ]
        assert connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall() == [(1,), (2,)]

    assert upgraded.unlink_external_identity("google", "subject-01") is True
    with pytest.raises(IdentityStorageConflictError):
        upgraded.link_external_identity(identity)


def test_user_and_external_identity_round_trip_and_uniqueness(storage) -> None:
    first = account()
    second = account("user-02")
    storage.create_user(first)
    storage.create_user(second)

    updated = replace(first, display_name="Mario Rossi", role="teacher", updated_at=NOW + timedelta(minutes=1))
    storage.save_user(updated, expected_updated_at=first.updated_at)
    assert storage.read_user("user-01") == updated
    assert storage.list_users() == [updated, second]

    identity = ExternalIdentity(
        "user-01",
        "github",
        "4242",
        NOW,
        email="Mario@Example.Test",
        username="mrossi",
    )
    storage.link_external_identity(identity)
    assert storage.read_external_identity("GITHUB", "4242") == identity
    assert storage.list_external_identities("user-01") == [identity]

    refreshed = replace(identity, linked_at=LATER, email="new@example.test", username="new-name")
    storage.refresh_external_identity(
        refreshed,
        expected_linked_at=identity.linked_at,
        expected_user_updated_at=updated.updated_at,
    )
    expected_refresh = replace(refreshed, linked_at=identity.linked_at)
    assert storage.read_external_identity("github", "4242") == expected_refresh

    with pytest.raises(IdentityStorageConflictError):
        storage.link_external_identity(ExternalIdentity("user-02", "github", "4242", NOW))
    assert storage.read_external_identity("github", "4242") == expected_refresh
    assert storage.unlink_external_identity("github", "4242") is True
    assert storage.unlink_external_identity("github", "4242") is False


def test_external_identity_generation_tombstone_prevents_aba_refresh(storage) -> None:
    storage.create_user(account())
    original = ExternalIdentity("user-01", "google", "subject-01", NOW, email="old@test")
    storage.link_external_identity(original)
    assert storage.unlink_external_identity("google", "subject-01") is True

    with pytest.raises(IdentityStorageGenerationConflictError):
        storage.link_external_identity(replace(original, email="recreated@test"))

    replacement = replace(
        original,
        linked_at=NOW + timedelta(microseconds=1),
        email="replacement@test",
    )
    storage.link_external_identity(replacement)
    with pytest.raises(IdentityStorageConflictError, match="ricollegata"):
        storage.refresh_external_identity(
            replace(original, email="stale@test"),
            expected_linked_at=original.linked_at,
            expected_user_updated_at=NOW,
        )
    assert storage.read_external_identity("google", "subject-01") == replacement


def test_user_updates_are_monotonic_and_stale_snapshot_cannot_reactivate(storage) -> None:
    original = account()
    storage.create_user(original)
    stale_active = replace(original, updated_at=NOW + timedelta(minutes=20))
    disabled = replace(original, active=False, updated_at=NOW + timedelta(minutes=10))
    storage.save_user(disabled, expected_updated_at=original.updated_at)

    with pytest.raises(IdentityStorageConflictError, match="timestamp non monotono"):
        storage.save_user(stale_active, expected_updated_at=original.updated_at)
    with pytest.raises(IdentityStorageConflictError, match="timestamp non monotono"):
        storage.save_user(
            replace(disabled, created_at=NOW - timedelta(days=1), updated_at=LATER),
            expected_updated_at=disabled.updated_at,
        )

    assert storage.read_user("user-01") == disabled


def test_missing_foreign_key_rolls_back_without_partial_state(storage) -> None:
    identity = ExternalIdentity("missing-user", "google", "subject-01", NOW)

    with pytest.raises(IdentityStorageConflictError):
        storage.link_external_identity(identity)

    assert storage.read_external_identity("google", "subject-01") is None


def test_classes_memberships_and_group_mapping_crud(storage) -> None:
    user = account()
    first_class = class_group()
    second_class = class_group("class-02", active=False)
    storage.create_user(user)
    storage.create_class(first_class)
    storage.create_class(second_class)

    membership = ClassMembership(
        "user-01",
        "class-01",
        "student",
        NOW,
        source_provider="github",
        source_group_subject="team-42",
    )
    storage.save_membership(membership)
    storage.save_membership(replace(membership, joined_at=NOW + timedelta(minutes=1)))
    assert storage.list_user_memberships("user-01") == [replace(membership, joined_at=NOW + timedelta(minutes=1))]
    assert storage.list_class_memberships("class-01") == storage.list_user_memberships("user-01")
    assert storage.list_classes(active_only=True) == [first_class]

    mapping = ExternalGroupMapping("github", "org-7", "team-42", "class-01", NOW, "3A")
    storage.save_external_group_mapping(mapping)
    renamed = replace(mapping, created_at=LATER, display_name="3A Informatica")
    storage.save_external_group_mapping(renamed)
    expected_mapping = replace(renamed, created_at=mapping.created_at)
    assert storage.read_external_group_mapping("GITHUB", "org-7", "team-42") == expected_mapping
    assert storage.list_external_group_mappings("class-01") == [expected_mapping]

    with pytest.raises(IdentityStorageConflictError, match="classe diversa"):
        storage.save_external_group_mapping(replace(mapping, class_id="class-02"))
    assert storage.read_external_group_mapping("github", "org-7", "team-42") == expected_mapping
    assert storage.delete_external_group_mapping("github", "org-7", "team-42") is True
    assert storage.delete_membership("user-01", "class-01", "STUDENT") is True


def test_session_digest_lookup_revocation_and_cleanup(storage) -> None:
    storage.create_user(account())
    active = session()
    expired = session(
        "session-expired",
        "sha256:" + "c" * 64,
        created_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
        last_seen_at=NOW - timedelta(hours=2),
    )
    future_activity = session(
        "session-future-activity",
        "sha256:" + "d" * 64,
        last_seen_at=NOW + timedelta(minutes=30),
    )
    for value in (active, expired, future_activity):
        storage.create_session(value)

    assert storage.read_session_by_token_digest(SESSION_DIGEST.upper()) == active
    stale_revocation = NOW + timedelta(minutes=10)
    with pytest.raises(IdentityStorageConflictError, match="ultimo utilizzo"):
        storage.revoke_user_sessions("user-01", stale_revocation)
    assert storage.read_session("session-01") == active

    revoked_at = NOW + timedelta(minutes=40)
    assert storage.revoke_user_sessions("user-01", revoked_at) == 2
    assert storage.read_session("session-01") == replace(active, revoked_at=revoked_at)
    assert storage.read_session("session-future-activity") == replace(
        future_activity, revoked_at=revoked_at
    )
    with pytest.raises(IdentityStorageConflictError, match="revocata"):
        storage.save_session(active)
    assert storage.read_session("session-01") == replace(active, revoked_at=revoked_at)

    assert storage.delete_expired_sessions(NOW) == 1
    assert storage.read_session("session-expired") is None
    assert len(storage.list_user_sessions("user-01")) == 2


def test_session_expiring_at_revocation_cutoff_is_not_counted_active(storage) -> None:
    storage.create_user(account())
    boundary = session(
        created_at=NOW - timedelta(hours=1),
        expires_at=NOW,
        last_seen_at=NOW - timedelta(minutes=1),
    )
    storage.create_session(boundary)

    assert storage.revoke_user_sessions("user-01", NOW) == 0
    assert storage.read_session("session-01") == boundary
    assert storage.delete_expired_sessions(NOW) == 1


def test_session_sql_checks_reject_activity_or_revocation_at_expiration(
    storage, database_path
) -> None:
    storage.create_user(account())
    created_at = "2026-09-01T08:00:00.000000Z"
    expires_at = "2026-09-01T09:00:00.000000Z"
    before_expiration = "2026-09-01T08:59:59.000000Z"

    with sqlite3.connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "session-last-seen-boundary",
                    "user-01",
                    "sha256:" + "e" * 64,
                    created_at,
                    expires_at,
                    expires_at,
                    None,
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    "session-revocation-boundary",
                    "user-01",
                    "sha256:" + "f" * 64,
                    created_at,
                    expires_at,
                    before_expiration,
                    expires_at,
                ),
            )


def test_session_last_seen_update_rejects_stale_snapshot(storage) -> None:
    storage.create_user(account())
    original = session()
    storage.create_session(original)
    newer = replace(original, last_seen_at=NOW + timedelta(minutes=10))
    storage.save_session(newer)

    with pytest.raises(IdentityStorageConflictError, match="modificata"):
        storage.save_session(original)

    assert storage.read_session("session-01") == newer


def test_active_session_creation_requires_matching_user_revision(storage) -> None:
    original = account()
    storage.create_user(original)
    storage.save_user(
        replace(original, updated_at=NOW + timedelta(seconds=1)),
        expected_updated_at=original.updated_at,
    )

    with pytest.raises(IdentityStorageConflictError, match="utente non attivo"):
        storage.create_session_for_active_user(
            session(), expected_user_updated_at=original.updated_at
        )
    assert storage.list_user_sessions("user-01") == []


def test_session_digest_is_unique_under_concurrent_writes(storage) -> None:
    storage.create_user(account())
    contenders = [session(f"session-{index}") for index in range(2)]

    def create(value):
        try:
            storage.create_session(value)
            return "created"
        except IdentityStorageConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(create, contenders))

    assert sorted(outcomes) == ["conflict", "created"]
    assert len(storage.list_user_sessions("user-01")) == 1


def test_pairing_digest_lookup_lifecycle_and_cleanup(storage) -> None:
    storage.create_user(account())
    pending = pairing()
    storage.create_pairing(pending)
    assert storage.read_pairing_by_code_digest(PAIRING_DIGEST.upper()) == pending

    authorized = authorize_pairing(pending, "user-01", NOW + timedelta(minutes=5))
    storage.save_pairing(authorized)
    consumed = consume_pairing(authorized, NOW + timedelta(minutes=6))
    storage.save_pairing(consumed)
    assert storage.read_pairing("pairing-01") == consumed

    old = pairing(
        "pairing-old",
        "hmac-sha256:" + "c" * 64,
        created_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
    )
    storage.create_pairing(old)
    assert storage.delete_expired_pairings(NOW) == 1
    assert storage.read_pairing("pairing-old") is None

    with pytest.raises(IdentityStorageConflictError):
        storage.create_pairing(pairing("pairing-duplicate"))


def test_active_pairing_transition_requires_matching_user_revision(storage) -> None:
    original = account()
    storage.create_user(original)
    pending = pairing()
    storage.create_pairing(pending)
    storage.save_user(
        replace(original, updated_at=NOW + timedelta(seconds=1)),
        expected_updated_at=original.updated_at,
    )
    authorized = authorize_pairing(pending, "user-01", NOW + timedelta(minutes=1))

    with pytest.raises(IdentityStorageConflictError, match="non attivo"):
        storage.save_pairing_for_active_user(
            authorized, expected_user_updated_at=original.updated_at
        )
    assert storage.read_pairing("pairing-01") == pending


def test_pairing_consumption_is_atomic_and_terminal(storage) -> None:
    storage.create_user(account())
    storage.create_user(account("user-02"))
    pending = pairing()
    storage.create_pairing(pending)
    authorized = authorize_pairing(pending, "user-01", NOW + timedelta(minutes=5))
    storage.save_pairing(authorized)
    consumed = consume_pairing(authorized, NOW + timedelta(minutes=6))
    with pytest.raises(IdentityStorageConflictError, match="transitato"):
        storage.save_pairing(replace(consumed, user_id="user-02"))
    assert storage.read_pairing("pairing-01") == authorized

    def save_consumed():
        try:
            storage.save_pairing(consumed)
            return "consumed"
        except IdentityStorageConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: save_consumed(), range(2)))

    assert sorted(outcomes) == ["conflict", "consumed"]
    with pytest.raises(IdentityStorageConflictError, match="transitato"):
        storage.save_pairing(authorized)
    assert storage.read_pairing("pairing-01") == consumed


def test_reopen_preserves_utc_records_and_schema_contains_no_raw_secrets(database_path) -> None:
    storage = SqliteIdentityStorage(database_path)
    offset = timezone(timedelta(hours=5, minutes=30))
    created = NOW.astimezone(offset)
    user = account(created_at=created, updated_at=created)
    storage.create_user(user)
    storage.create_session(session())
    storage.create_pairing(pairing())

    reopened = SqliteIdentityStorage(database_path)
    assert reopened.read_user("user-01") == user
    assert reopened.read_user("user-01").created_at.tzinfo == timezone.utc

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        columns = {
            row[1]
            for table in tables
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
        assert "token_digest" in columns
        assert "code_digest" in columns
        assert not {"token", "raw_token", "code", "raw_code", "password", "oauth_token"} & columns
        def unique_index_columns(table):
            indexes = connection.execute(f"PRAGMA index_list({table})").fetchall()
            return {
                tuple(
                    column[2]
                    for column in connection.execute(f"PRAGMA index_info({index[1]})")
                )
                for index in indexes
                if index[2]
            }

        assert ("token_digest",) in unique_index_columns("sessions")
        assert ("code_digest",) in unique_index_columns("tui_pairings")


def test_corrupt_timestamp_is_reported_as_stable_storage_error(storage, database_path) -> None:
    storage.create_user(account())
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE users SET created_at = ?, updated_at = ? WHERE user_id = ?",
            ("not-a-timestamp", "not-a-timestamp", "user-01"),
        )

    with pytest.raises(IdentityStorageCorruptionError, match="Timestamp"):
        storage.read_user("user-01")


def test_save_requires_existing_primary_record(storage) -> None:
    with pytest.raises(IdentityStorageNotFoundError):
        storage.save_user(account(), expected_updated_at=NOW - timedelta(seconds=1))
    with pytest.raises(IdentityStorageNotFoundError):
        storage.save_class(class_group())
    with pytest.raises(IdentityStorageNotFoundError):
        storage.save_session(session())
    with pytest.raises(IdentityStorageNotFoundError):
        storage.save_pairing(pairing())
