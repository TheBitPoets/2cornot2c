from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator, TypeVar

from scripts.thebitlab_identity import (
    ClassGroup,
    ClassMembership,
    ExternalGroupMapping,
    ExternalIdentity,
    InvalidIdentityDataError,
    TuiPairing,
    UserAccount,
    UserSession,
)
from scripts.thebitlab_dashboard_auth_ports import DashboardAuthorizationSnapshot
from scripts.thebitlab_identity_ports import (
    IdentityStorageConflictError,
    IdentityStorageCorruptionError,
    IdentityStorageError,
    IdentityStorageGenerationConflictError,
    IdentityStorageMappingGenerationConflictError,
    IdentityStorageNotFoundError,
    IdentityStoragePairingExpiredError,
    IdentityStorageSessionExpiredError,
)


SCHEMA_VERSION = 11
_T = TypeVar("_T")


_MIGRATION_1 = (
    """
    CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'teacher', 'student', 'pending')),
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        primary_email TEXT,
        CHECK (updated_at >= created_at)
    )
    """,
    """
    CREATE TABLE external_identities (
        provider TEXT NOT NULL,
        subject TEXT NOT NULL,
        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        linked_at TEXT NOT NULL,
        email TEXT,
        username TEXT,
        PRIMARY KEY (provider, subject)
    )
    """,
    "CREATE INDEX idx_external_identities_user ON external_identities(user_id)",
    """
    CREATE TABLE classes (
        class_id TEXT PRIMARY KEY,
        label TEXT NOT NULL,
        school_year TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (updated_at >= created_at)
    )
    """,
    "CREATE INDEX idx_classes_active ON classes(active)",
    """
    CREATE TABLE class_memberships (
        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
        role TEXT NOT NULL CHECK (role IN ('teacher', 'student')),
        joined_at TEXT NOT NULL,
        source_provider TEXT,
        source_group_subject TEXT,
        PRIMARY KEY (user_id, class_id, role),
        CHECK ((source_provider IS NULL) = (source_group_subject IS NULL))
    )
    """,
    "CREATE INDEX idx_class_memberships_class ON class_memberships(class_id)",
    """
    CREATE TABLE external_group_mappings (
        provider TEXT NOT NULL,
        organization_subject TEXT NOT NULL,
        group_subject TEXT NOT NULL,
        class_id TEXT NOT NULL REFERENCES classes(class_id) ON DELETE CASCADE,
        created_at TEXT NOT NULL,
        display_name TEXT,
        PRIMARY KEY (provider, organization_subject, group_subject)
    )
    """,
    "CREATE INDEX idx_external_group_mappings_class ON external_group_mappings(class_id)",
    """
    CREATE TABLE sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        token_digest TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        revoked_at TEXT,
        CHECK (expires_at > created_at),
        CHECK (last_seen_at >= created_at AND last_seen_at < expires_at),
        CHECK (revoked_at IS NULL OR (
            revoked_at >= created_at AND revoked_at < expires_at AND last_seen_at <= revoked_at
        ))
    )
    """,
    "CREATE INDEX idx_sessions_user ON sessions(user_id)",
    "CREATE INDEX idx_sessions_expires ON sessions(expires_at)",
    """
    CREATE TABLE tui_pairings (
        pairing_id TEXT PRIMARY KEY,
        code_digest TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL CHECK (status IN ('pending', 'authorized', 'consumed', 'expired', 'revoked')),
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
        authorized_at TEXT,
        consumed_at TEXT,
        expired_at TEXT,
        revoked_at TEXT,
        CHECK (expires_at > created_at),
        CHECK ((user_id IS NULL) = (authorized_at IS NULL)),
        CHECK (authorized_at IS NULL OR (authorized_at >= created_at AND authorized_at < expires_at)),
        CHECK (consumed_at IS NULL OR (
            authorized_at IS NOT NULL AND consumed_at >= authorized_at AND consumed_at < expires_at
        )),
        CHECK (expired_at IS NULL OR expired_at >= expires_at),
        CHECK (revoked_at IS NULL OR (
            revoked_at >= created_at AND revoked_at < expires_at
            AND (authorized_at IS NULL OR revoked_at >= authorized_at)
        )),
        CHECK (
            (status = 'pending' AND user_id IS NULL
                AND consumed_at IS NULL AND expired_at IS NULL AND revoked_at IS NULL)
            OR (status = 'authorized' AND user_id IS NOT NULL
                AND consumed_at IS NULL AND expired_at IS NULL AND revoked_at IS NULL)
            OR (status = 'consumed' AND user_id IS NOT NULL
                AND consumed_at IS NOT NULL AND expired_at IS NULL AND revoked_at IS NULL)
            OR (status = 'expired' AND consumed_at IS NULL AND expired_at IS NOT NULL AND revoked_at IS NULL)
            OR (status = 'revoked' AND consumed_at IS NULL AND expired_at IS NULL AND revoked_at IS NOT NULL)
        )
    )
    """,
    "CREATE INDEX idx_tui_pairings_user ON tui_pairings(user_id)",
    "CREATE INDEX idx_tui_pairings_expires ON tui_pairings(expires_at)",
)

_MIGRATION_3 = (
    """
    CREATE TABLE external_identity_link_conflicts (
        provider TEXT NOT NULL,
        subject TEXT NOT NULL,
        user_id TEXT NOT NULL,
        linked_at TEXT NOT NULL,
        email TEXT,
        username TEXT,
        PRIMARY KEY (provider, subject)
    )
    """,
    """
    INSERT INTO external_identity_link_conflicts
        (provider, subject, user_id, linked_at, email, username)
    SELECT provider, subject, user_id, linked_at, email, username
    FROM external_identities
    WHERE (user_id, provider) IN (
        SELECT user_id, provider FROM external_identities
        GROUP BY user_id, provider HAVING COUNT(*) > 1
    )
    """,
    """
    INSERT OR IGNORE INTO external_identity_generations
        (provider, subject, linked_at)
    SELECT provider, subject, linked_at
    FROM external_identity_link_conflicts
    """,
    """
    DELETE FROM external_identities
    WHERE (user_id, provider) IN (
        SELECT user_id, provider FROM external_identity_link_conflicts
        GROUP BY user_id, provider
    )
    """,
    """
    CREATE UNIQUE INDEX uq_external_identities_user_provider
    ON external_identities(user_id, provider)
    """,
)

_MIGRATION_5 = (
    "ALTER TABLE external_group_mappings ADD COLUMN updated_at TEXT",
    "UPDATE external_group_mappings SET updated_at = created_at",
)

_MIGRATION_6 = (
    "ALTER TABLE sessions ADD COLUMN audience TEXT NOT NULL DEFAULT 'web' "
    "CHECK (audience IN ('web', 'tui'))",
)

_MIGRATION_7 = (
    "ALTER TABLE sessions ADD COLUMN source_pairing_id TEXT "
    "REFERENCES tui_pairings(pairing_id)",
    "DELETE FROM sessions WHERE audience = 'tui' AND source_pairing_id IS NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_sessions_source_pairing "
    "ON sessions(source_pairing_id) WHERE source_pairing_id IS NOT NULL",
)

_MIGRATION_8 = (
    """
    DELETE FROM sessions
    WHERE (audience = 'web' AND source_pairing_id IS NOT NULL)
        OR (audience = 'tui' AND NOT EXISTS (
            SELECT 1 FROM tui_pairings
            WHERE tui_pairings.pairing_id = sessions.source_pairing_id
                AND tui_pairings.status = 'consumed'
                AND tui_pairings.user_id = sessions.user_id
                AND tui_pairings.consumed_at = sessions.created_at
        ))
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_sessions_validate_pairing_insert
    BEFORE INSERT ON sessions
    WHEN (NEW.audience = 'web' AND NEW.source_pairing_id IS NOT NULL)
        OR (NEW.audience = 'tui' AND (
            NEW.source_pairing_id IS NULL OR NOT EXISTS (
                SELECT 1 FROM tui_pairings
                WHERE pairing_id = NEW.source_pairing_id
                    AND status = 'consumed'
                    AND user_id = NEW.user_id
                    AND consumed_at = NEW.created_at
            )
        ))
    BEGIN
        SELECT RAISE(ABORT, 'invalid session pairing correlation');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_sessions_immutable_audience_update
    BEFORE UPDATE OF session_id, user_id, token_digest, created_at, expires_at,
        audience, source_pairing_id ON sessions
    WHEN NEW.audience != OLD.audience
        OR NEW.source_pairing_id IS NOT OLD.source_pairing_id
        OR (OLD.audience = 'tui' AND (
            NEW.session_id != OLD.session_id
            OR NEW.user_id != OLD.user_id
            OR NEW.token_digest != OLD.token_digest
            OR NEW.created_at != OLD.created_at
            OR NEW.expires_at != OLD.expires_at
        ))
    BEGIN
        SELECT RAISE(ABORT, 'immutable session audience');
    END
    """,
)

_MIGRATION_9 = (
    "DROP TRIGGER IF EXISTS trg_sessions_immutable_audience_update",
    _MIGRATION_8[2],
)

_MIGRATION_10 = (
    _MIGRATION_8[0],
    """
    CREATE TRIGGER IF NOT EXISTS trg_consumed_pairing_session_immutable
    BEFORE UPDATE ON tui_pairings
    WHEN EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.source_pairing_id = OLD.pairing_id
    ) AND (
        NEW.pairing_id != OLD.pairing_id
        OR NEW.code_digest != OLD.code_digest
        OR NEW.status != OLD.status
        OR NEW.created_at != OLD.created_at
        OR NEW.expires_at != OLD.expires_at
        OR NEW.user_id IS NOT OLD.user_id
        OR NEW.authorized_at IS NOT OLD.authorized_at
        OR NEW.consumed_at IS NOT OLD.consumed_at
        OR NEW.expired_at IS NOT OLD.expired_at
        OR NEW.revoked_at IS NOT OLD.revoked_at
    )
    BEGIN
        SELECT RAISE(ABORT, 'immutable consumed pairing correlation');
    END
    """,
)

_MIGRATION_11 = (
    _MIGRATION_8[0],
    "DROP TRIGGER IF EXISTS trg_consumed_pairing_session_immutable",
    _MIGRATION_10[1],
)

_MIGRATION_4 = (
    """
    CREATE TABLE external_group_mapping_generations (
        provider TEXT NOT NULL,
        organization_subject TEXT NOT NULL,
        group_subject TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (provider, organization_subject, group_subject, created_at)
    )
    """,
    """
    INSERT INTO external_group_mapping_generations
        (provider, organization_subject, group_subject, created_at)
    SELECT provider, organization_subject, group_subject, created_at
    FROM external_group_mappings
    """,
)

_MIGRATION_2 = (
    """
    CREATE TABLE external_identity_generations (
        provider TEXT NOT NULL,
        subject TEXT NOT NULL,
        linked_at TEXT NOT NULL,
        PRIMARY KEY (provider, subject, linked_at)
    )
    """,
    """
    INSERT INTO external_identity_generations(provider, subject, linked_at)
    SELECT provider, subject, linked_at FROM external_identities
    """,
)


def _encode_datetime(value: datetime, field_name: str) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise IdentityStorageError(f"{field_name} deve includere il timezone.")
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _decode_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise IdentityStorageCorruptionError("Timestamp persistito non valido.") from error


class SqliteIdentityStorage:
    """SQLite source-of-truth adapter for identity, class, session and pairing ports."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if str(database_path) == ":memory:":
            raise IdentityStorageError(
                "Usare un file temporaneo: connessioni isolate non supportano SQLite :memory:."
            )
        self.database_path = Path(database_path)
        self._clock = clock
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise IdentityStorageError("Impossibile preparare la directory del database identity.") from error
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self.database_path, timeout=30, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 30000")
            return connection
        except sqlite3.DatabaseError as error:
            if connection is not None:
                connection.close()
            raise IdentityStorageError(
                "Impossibile aprire o configurare il database identity."
            ) from error

    def _migrate(self) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            versions = {
                int(row["version"])
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            unsupported = [version for version in versions if version > SCHEMA_VERSION]
            if unsupported:
                raise IdentityStorageError(
                    f"Schema identity piu recente del codice: versione {max(unsupported)}."
                )
            if versions and versions != set(range(1, max(versions) + 1)):
                raise IdentityStorageError("Sequenza migrazioni identity non valida.")
            migrations = (
                (1, _MIGRATION_1),
                (2, _MIGRATION_2),
                (3, _MIGRATION_3),
                (4, _MIGRATION_4),
                (5, _MIGRATION_5),
                (6, _MIGRATION_6),
                (7, _MIGRATION_7),
                (8, _MIGRATION_8),
                (9, _MIGRATION_9),
                (10, _MIGRATION_10),
                (11, _MIGRATION_11),
            )
            for version, statements in migrations:
                if version in versions:
                    continue
                for statement in statements:
                    if version in {5, 6, 7} and statement.startswith("ALTER TABLE"):
                        table = (
                            "external_group_mappings" if version == 5 else "sessions"
                        )
                        expected_column = {
                            5: "updated_at",
                            6: "audience",
                            7: "source_pairing_id",
                        }[version]
                        columns = {
                            row["name"]
                            for row in connection.execute(f"PRAGMA table_info({table})")
                        }
                        if expected_column in columns:
                            continue
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (
                        version,
                        _encode_datetime(datetime.now(timezone.utc), "applied_at"),
                    ),
                )
            connection.commit()
        except IdentityStorageError:
            connection.rollback()
            raise
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise IdentityStorageError("Migrazione schema identity non riuscita.") from error
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def _transaction(self, operation: str) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise IdentityStorageConflictError(
                f"Vincolo storage violato durante {operation}."
            ) from error
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise IdentityStorageError(f"Errore SQLite durante {operation}.") from error
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _query_one(self, sql: str, parameters: tuple[object, ...]) -> sqlite3.Row | None:
        connection = self._connect()
        try:
            return connection.execute(sql, parameters).fetchone()
        except sqlite3.DatabaseError as error:
            raise IdentityStorageError("Errore SQLite durante la lettura.") from error
        finally:
            connection.close()

    def _query_all(self, sql: str, parameters: tuple[object, ...] = ()) -> list[sqlite3.Row]:
        connection = self._connect()
        try:
            return list(connection.execute(sql, parameters).fetchall())
        except sqlite3.DatabaseError as error:
            raise IdentityStorageError("Errore SQLite durante la lettura.") from error
        finally:
            connection.close()

    @staticmethod
    def _hydrate(factory: Callable[..., _T], row: sqlite3.Row, **values: object) -> _T:
        try:
            return factory(**values)
        except (InvalidIdentityDataError, TypeError, ValueError) as error:
            raise IdentityStorageCorruptionError(
                f"Record {factory.__name__} persistito non valido."
            ) from error

    @classmethod
    def _user(cls, row: sqlite3.Row) -> UserAccount:
        return cls._hydrate(
            UserAccount,
            row,
            user_id=row["user_id"],
            display_name=row["display_name"],
            role=row["role"],
            active=bool(row["active"]),
            created_at=_decode_datetime(row["created_at"]),
            updated_at=_decode_datetime(row["updated_at"]),
            primary_email=row["primary_email"],
        )

    @classmethod
    def _external_identity(cls, row: sqlite3.Row) -> ExternalIdentity:
        return cls._hydrate(
            ExternalIdentity,
            row,
            user_id=row["user_id"],
            provider=row["provider"],
            subject=row["subject"],
            linked_at=_decode_datetime(row["linked_at"]),
            email=row["email"],
            username=row["username"],
        )

    @classmethod
    def _class_group(cls, row: sqlite3.Row) -> ClassGroup:
        return cls._hydrate(
            ClassGroup,
            row,
            class_id=row["class_id"],
            label=row["label"],
            school_year=row["school_year"],
            active=bool(row["active"]),
            created_at=_decode_datetime(row["created_at"]),
            updated_at=_decode_datetime(row["updated_at"]),
        )

    @classmethod
    def _membership(cls, row: sqlite3.Row) -> ClassMembership:
        return cls._hydrate(
            ClassMembership,
            row,
            user_id=row["user_id"],
            class_id=row["class_id"],
            role=row["role"],
            joined_at=_decode_datetime(row["joined_at"]),
            source_provider=row["source_provider"],
            source_group_subject=row["source_group_subject"],
        )

    @classmethod
    def _mapping(cls, row: sqlite3.Row) -> ExternalGroupMapping:
        return cls._hydrate(
            ExternalGroupMapping,
            row,
            provider=row["provider"],
            organization_subject=row["organization_subject"],
            group_subject=row["group_subject"],
            class_id=row["class_id"],
            created_at=_decode_datetime(row["created_at"]),
            display_name=row["display_name"],
            updated_at=_decode_datetime(row["updated_at"]),
        )

    @classmethod
    def _session(cls, row: sqlite3.Row) -> UserSession:
        return cls._hydrate(
            UserSession,
            row,
            session_id=row["session_id"],
            user_id=row["user_id"],
            token_digest=row["token_digest"],
            created_at=_decode_datetime(row["created_at"]),
            expires_at=_decode_datetime(row["expires_at"]),
            last_seen_at=_decode_datetime(row["last_seen_at"]),
            revoked_at=_decode_datetime(row["revoked_at"]),
            audience=row["audience"],
            source_pairing_id=row["source_pairing_id"],
        )

    @classmethod
    def _pairing(cls, row: sqlite3.Row) -> TuiPairing:
        return cls._hydrate(
            TuiPairing,
            row,
            pairing_id=row["pairing_id"],
            code_digest=row["code_digest"],
            status=row["status"],
            created_at=_decode_datetime(row["created_at"]),
            expires_at=_decode_datetime(row["expires_at"]),
            user_id=row["user_id"],
            authorized_at=_decode_datetime(row["authorized_at"]),
            consumed_at=_decode_datetime(row["consumed_at"]),
            expired_at=_decode_datetime(row["expired_at"]),
            revoked_at=_decode_datetime(row["revoked_at"]),
        )

    def create_user(self, user: UserAccount) -> None:
        with self._transaction("create_user") as connection:
            connection.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user.user_id,
                    user.display_name,
                    user.role,
                    int(user.active),
                    _encode_datetime(user.created_at, "created_at"),
                    _encode_datetime(user.updated_at, "updated_at"),
                    user.primary_email,
                ),
            )

    def provision_user_with_identity(
        self, user: UserAccount, identity: ExternalIdentity
    ) -> None:
        if identity.user_id != user.user_id:
            raise IdentityStorageConflictError(
                "Utente e identita del provisioning hanno proprietari diversi."
            )
        with self._transaction("provision_user_with_identity") as connection:
            connection.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user.user_id,
                    user.display_name,
                    user.role,
                    int(user.active),
                    _encode_datetime(user.created_at, "created_at"),
                    _encode_datetime(user.updated_at, "updated_at"),
                    user.primary_email,
                ),
            )
            linked_at = _encode_datetime(identity.linked_at, "linked_at")
            self._reserve_external_identity_generation(
                connection, identity.provider, identity.subject, linked_at
            )
            connection.execute(
                "INSERT INTO external_identities VALUES (?, ?, ?, ?, ?, ?)",
                (
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    linked_at,
                    identity.email,
                    identity.username,
                ),
            )

    def read_user(self, user_id: str) -> UserAccount | None:
        row = self._query_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return None if row is None else self._user(row)

    def save_user(self, user: UserAccount, *, expected_updated_at: datetime) -> None:
        created_at = _encode_datetime(user.created_at, "created_at")
        updated_at = _encode_datetime(user.updated_at, "updated_at")
        expected_revision = _encode_datetime(expected_updated_at, "expected_updated_at")
        if updated_at <= expected_revision:
            raise IdentityStorageConflictError(
                "Il nuovo updated_at deve essere successivo alla revisione attesa."
            )
        with self._transaction("save_user") as connection:
            cursor = connection.execute(
                """
                UPDATE users SET display_name = ?, role = ?, active = ?,
                    updated_at = ?, primary_email = ?
                WHERE user_id = ? AND created_at = ? AND updated_at = ?
                """,
                (
                    user.display_name,
                    user.role,
                    int(user.active),
                    updated_at,
                    user.primary_email,
                    user.user_id,
                    created_at,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM users WHERE user_id = ?", (user.user_id,)
                ).fetchone()
                if exists is None:
                    raise IdentityStorageNotFoundError("Utente da aggiornare non trovato.")
                raise IdentityStorageConflictError(
                    "Utente modificato da un'altra operazione o timestamp non monotono."
                )
            if not user.active:
                disabled_at = updated_at
                connection.execute(
                    """
                    UPDATE sessions SET revoked_at = CASE
                        WHEN ? >= last_seen_at AND ? < expires_at THEN ?
                        ELSE last_seen_at
                    END
                    WHERE user_id = ? AND revoked_at IS NULL
                    """,
                    (disabled_at, disabled_at, disabled_at, user.user_id),
                )
                connection.execute(
                    "DELETE FROM tui_pairings WHERE user_id = ? AND status = 'authorized'",
                    (user.user_id,),
                )

    def list_users(self) -> list[UserAccount]:
        return [self._user(row) for row in self._query_all("SELECT * FROM users ORDER BY user_id")]

    @staticmethod
    def _reserve_external_identity_generation(
        connection: sqlite3.Connection,
        provider: str,
        subject: str,
        linked_at: str,
    ) -> None:
        exists = connection.execute(
            """
            SELECT 1 FROM external_identity_generations
            WHERE provider = ? AND subject = ? AND linked_at = ?
            """,
            (provider, subject, linked_at),
        ).fetchone()
        if exists is not None:
            raise IdentityStorageGenerationConflictError(
                "Generazione identita esterna gia utilizzata."
            )
        connection.execute(
            "INSERT INTO external_identity_generations VALUES (?, ?, ?)",
            (provider, subject, linked_at),
        )

    def link_external_identity(self, identity: ExternalIdentity) -> None:
        linked_at = _encode_datetime(identity.linked_at, "linked_at")
        with self._transaction("link_external_identity") as connection:
            self._reserve_external_identity_generation(
                connection, identity.provider, identity.subject, linked_at
            )
            connection.execute(
                "INSERT INTO external_identities VALUES (?, ?, ?, ?, ?, ?)",
                (
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    linked_at,
                    identity.email,
                    identity.username,
                ),
            )

    def link_external_identity_for_active_user(
        self,
        identity: ExternalIdentity,
        *,
        expected_user_updated_at: datetime,
    ) -> None:
        linked_at = _encode_datetime(identity.linked_at, "linked_at")
        expected_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        with self._transaction("link_external_identity_for_active_user") as connection:
            self._reserve_external_identity_generation(
                connection, identity.provider, identity.subject, linked_at
            )
            cursor = connection.execute(
                """
                INSERT INTO external_identities
                    (provider, subject, user_id, linked_at, email, username)
                SELECT ?, ?, user_id, ?, ?, ? FROM users
                WHERE user_id = ? AND active = 1 AND updated_at = ?
                """,
                (
                    identity.provider,
                    identity.subject,
                    linked_at,
                    identity.email,
                    identity.username,
                    identity.user_id,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Utente modificato o disabilitato durante il collegamento."
                )

    def link_external_identity_for_active_session(
        self,
        identity: ExternalIdentity,
        *,
        expected_user_updated_at: datetime,
        expected_session_id: str,
        expected_session_token_digest: str,
        expected_session_created_at: datetime,
        expected_session_valid_at: datetime,
    ) -> None:
        linked_at = _encode_datetime(identity.linked_at, "linked_at")
        expected_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        expected_created_at = _encode_datetime(
            expected_session_created_at, "expected_session_created_at"
        )
        expected_valid_at = _encode_datetime(
            expected_session_valid_at, "expected_session_valid_at"
        )
        with self._transaction(
            "link_external_identity_for_active_session"
        ) as connection:
            transaction_valid_at = max(
                expected_valid_at,
                _encode_datetime(self._clock(), "storage_clock"),
            )
            self._reserve_external_identity_generation(
                connection, identity.provider, identity.subject, linked_at
            )
            cursor = connection.execute(
                """
                INSERT INTO external_identities
                    (provider, subject, user_id, linked_at, email, username)
                SELECT ?, ?, users.user_id, ?, ?, ? FROM users
                WHERE users.user_id = ? AND users.active = 1
                    AND users.updated_at = ?
                    AND EXISTS (
                        SELECT 1 FROM sessions
                        WHERE sessions.session_id = ?
                            AND sessions.token_digest = ?
                            AND sessions.created_at = ?
                            AND sessions.user_id = users.user_id
                            AND sessions.revoked_at IS NULL
                            AND sessions.created_at <= ?
                            AND sessions.last_seen_at <= ?
                            AND sessions.expires_at > ?
                    )
                """,
                (
                    identity.provider,
                    identity.subject,
                    linked_at,
                    identity.email,
                    identity.username,
                    identity.user_id,
                    expected_revision,
                    expected_session_id,
                    expected_session_token_digest,
                    expected_created_at,
                    transaction_valid_at,
                    transaction_valid_at,
                    transaction_valid_at,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Utente o sessione modificati durante il collegamento."
                )

    def refresh_external_identity(
        self,
        identity: ExternalIdentity,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> None:
        expected_revision = _encode_datetime(expected_linked_at, "expected_linked_at")
        expected_user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        with self._transaction("refresh_external_identity") as connection:
            cursor = connection.execute(
                """
                UPDATE external_identities SET email = ?, username = ?
                WHERE provider = ? AND subject = ? AND user_id = ? AND linked_at = ?
                    AND EXISTS (
                        SELECT 1 FROM users
                        WHERE users.user_id = external_identities.user_id
                            AND users.active = 1 AND users.updated_at = ?
                    )
                """,
                (
                    identity.email,
                    identity.username,
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    expected_revision,
                    expected_user_revision,
                ),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    """
                    SELECT 1 FROM external_identities
                    WHERE provider = ? AND subject = ?
                    """,
                    (identity.provider, identity.subject),
                ).fetchone()
                if exists is None:
                    raise IdentityStorageNotFoundError(
                        "Identita provider da aggiornare non trovata."
                    )
                raise IdentityStorageConflictError(
                    "Identita provider ricollegata da un'altra operazione."
                )

    def refresh_external_identity_for_active_session(
        self,
        identity: ExternalIdentity,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
        expected_session_id: str,
        expected_session_token_digest: str,
        expected_session_created_at: datetime,
        expected_session_valid_at: datetime,
    ) -> None:
        expected_generation = _encode_datetime(
            expected_linked_at, "expected_linked_at"
        )
        expected_user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        expected_created_at = _encode_datetime(
            expected_session_created_at, "expected_session_created_at"
        )
        expected_valid_at = _encode_datetime(
            expected_session_valid_at, "expected_session_valid_at"
        )
        with self._transaction(
            "refresh_external_identity_for_active_session"
        ) as connection:
            transaction_valid_at = max(
                expected_valid_at,
                _encode_datetime(self._clock(), "storage_clock"),
            )
            cursor = connection.execute(
                """
                UPDATE external_identities SET email = ?, username = ?
                WHERE provider = ? AND subject = ? AND user_id = ? AND linked_at = ?
                    AND EXISTS (
                        SELECT 1 FROM users
                        WHERE users.user_id = external_identities.user_id
                            AND users.active = 1 AND users.updated_at = ?
                    )
                    AND EXISTS (
                        SELECT 1 FROM sessions
                        WHERE sessions.session_id = ?
                            AND sessions.token_digest = ?
                            AND sessions.created_at = ?
                            AND sessions.user_id = external_identities.user_id
                            AND sessions.revoked_at IS NULL
                            AND sessions.created_at <= ?
                            AND sessions.last_seen_at <= ?
                            AND sessions.expires_at > ?
                    )
                """,
                (
                    identity.email,
                    identity.username,
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    expected_generation,
                    expected_user_revision,
                    expected_session_id,
                    expected_session_token_digest,
                    expected_created_at,
                    transaction_valid_at,
                    transaction_valid_at,
                    transaction_valid_at,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Identita, utente o sessione modificati durante il refresh."
                )

    def read_external_identity(self, provider: str, subject: str) -> ExternalIdentity | None:
        row = self._query_one(
            "SELECT * FROM external_identities WHERE provider = ? AND subject = ?",
            (provider.lower(), subject),
        )
        return None if row is None else self._external_identity(row)

    def read_latest_external_identity_generation(
        self, provider: str, subject: str
    ) -> datetime | None:
        row = self._query_one(
            """
            SELECT MAX(linked_at) AS linked_at
            FROM external_identity_generations
            WHERE provider = ? AND subject = ?
            """,
            (provider.lower(), subject),
        )
        if row is None or row["linked_at"] is None:
            return None
        return _decode_datetime(row["linked_at"])

    def list_external_identities(self, user_id: str) -> list[ExternalIdentity]:
        rows = self._query_all(
            "SELECT * FROM external_identities WHERE user_id = ? ORDER BY provider, subject",
            (user_id,),
        )
        return [self._external_identity(row) for row in rows]

    def unlink_external_identity(self, provider: str, subject: str) -> bool:
        with self._transaction("unlink_external_identity") as connection:
            cursor = connection.execute(
                "DELETE FROM external_identities WHERE provider = ? AND subject = ?",
                (provider.lower(), subject),
            )
            return cursor.rowcount == 1

    def unlink_external_identity_for_active_user(
        self,
        provider: str,
        subject: str,
        user_id: str,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> bool:
        expected_generation = _encode_datetime(
            expected_linked_at, "expected_linked_at"
        )
        expected_user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        with self._transaction(
            "unlink_external_identity_for_active_user"
        ) as connection:
            cursor = connection.execute(
                """
                DELETE FROM external_identities
                WHERE provider = ? AND subject = ? AND user_id = ? AND linked_at = ?
                    AND EXISTS (
                        SELECT 1 FROM users
                        WHERE users.user_id = external_identities.user_id
                            AND users.active = 1 AND users.updated_at = ?
                    )
                """,
                (
                    provider.lower(),
                    subject,
                    user_id,
                    expected_generation,
                    expected_user_revision,
                ),
            )
            if cursor.rowcount == 1:
                return True
            exists = connection.execute(
                """
                SELECT 1 FROM external_identities
                WHERE provider = ? AND subject = ?
                """,
                (provider.lower(), subject),
            ).fetchone()
            if exists is None:
                return False
            raise IdentityStorageConflictError(
                "Identita o utente modificati durante lo scollegamento."
            )

    def unlink_external_identity_for_active_session(
        self,
        provider: str,
        subject: str,
        user_id: str,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
        expected_session_id: str,
        expected_session_token_digest: str,
        expected_session_created_at: datetime,
        expected_session_valid_at: datetime,
    ) -> bool:
        expected_generation = _encode_datetime(
            expected_linked_at, "expected_linked_at"
        )
        expected_user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        expected_created_at = _encode_datetime(
            expected_session_created_at, "expected_session_created_at"
        )
        expected_valid_at = _encode_datetime(
            expected_session_valid_at, "expected_session_valid_at"
        )
        with self._transaction(
            "unlink_external_identity_for_active_session"
        ) as connection:
            transaction_valid_at = max(
                expected_valid_at,
                _encode_datetime(self._clock(), "storage_clock"),
            )
            cursor = connection.execute(
                """
                DELETE FROM external_identities
                WHERE provider = ? AND subject = ? AND user_id = ? AND linked_at = ?
                    AND EXISTS (
                        SELECT 1 FROM users
                        WHERE users.user_id = external_identities.user_id
                            AND users.active = 1 AND users.updated_at = ?
                    )
                    AND EXISTS (
                        SELECT 1 FROM sessions
                        WHERE sessions.session_id = ?
                            AND sessions.token_digest = ?
                            AND sessions.created_at = ?
                            AND sessions.user_id = external_identities.user_id
                            AND sessions.revoked_at IS NULL
                            AND sessions.created_at <= ?
                            AND sessions.last_seen_at <= ?
                            AND sessions.expires_at > ?
                    )
                """,
                (
                    provider.lower(),
                    subject,
                    user_id,
                    expected_generation,
                    expected_user_revision,
                    expected_session_id,
                    expected_session_token_digest,
                    expected_created_at,
                    transaction_valid_at,
                    transaction_valid_at,
                    transaction_valid_at,
                ),
            )
            if cursor.rowcount == 1:
                return True
            exists = connection.execute(
                """
                SELECT 1 FROM external_identities
                WHERE provider = ? AND subject = ?
                """,
                (provider.lower(), subject),
            ).fetchone()
            if exists is None:
                return False
            raise IdentityStorageConflictError(
                "Identita, utente o sessione modificati durante lo scollegamento."
            )

    def create_class(self, class_group: ClassGroup) -> None:
        with self._transaction("create_class") as connection:
            connection.execute(
                "INSERT INTO classes VALUES (?, ?, ?, ?, ?, ?)",
                (
                    class_group.class_id,
                    class_group.label,
                    class_group.school_year,
                    int(class_group.active),
                    _encode_datetime(class_group.created_at, "created_at"),
                    _encode_datetime(class_group.updated_at, "updated_at"),
                ),
            )

    def read_class(self, class_id: str) -> ClassGroup | None:
        row = self._query_one("SELECT * FROM classes WHERE class_id = ?", (class_id,))
        return None if row is None else self._class_group(row)

    def save_class(
        self, class_group: ClassGroup, *, expected_updated_at: datetime
    ) -> None:
        created_at = _encode_datetime(class_group.created_at, "created_at")
        updated_at = _encode_datetime(class_group.updated_at, "updated_at")
        expected_revision = _encode_datetime(
            expected_updated_at, "expected_updated_at"
        )
        if updated_at <= expected_revision:
            raise IdentityStorageConflictError(
                "Il nuovo updated_at classe deve essere successivo alla revisione attesa."
            )
        with self._transaction("save_class") as connection:
            cursor = connection.execute(
                """
                UPDATE classes SET label = ?, school_year = ?, active = ?, updated_at = ?
                WHERE class_id = ? AND created_at = ? AND updated_at = ?
                """,
                (
                    class_group.label,
                    class_group.school_year,
                    int(class_group.active),
                    updated_at,
                    class_group.class_id,
                    created_at,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM classes WHERE class_id = ?",
                    (class_group.class_id,),
                ).fetchone()
                if exists is None:
                    raise IdentityStorageNotFoundError(
                        "Classe da aggiornare non trovata."
                    )
                raise IdentityStorageConflictError(
                    "Classe modificata da un'altra operazione."
                )

    def list_classes(self, *, active_only: bool = False) -> list[ClassGroup]:
        where = " WHERE active = 1" if active_only else ""
        rows = self._query_all(f"SELECT * FROM classes{where} ORDER BY class_id")
        return [self._class_group(row) for row in rows]

    def read_dashboard_authorization_snapshot(
        self,
        actor_user_id: str,
        *,
        expected_actor_updated_at: datetime,
        target_user_id: str | None = None,
    ) -> DashboardAuthorizationSnapshot | None:
        expected_revision = _encode_datetime(
            expected_actor_updated_at, "expected_actor_updated_at"
        )
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            actor = connection.execute(
                """
                SELECT user_id, role, updated_at FROM users
                WHERE user_id = ? AND active = 1 AND updated_at = ?
                """,
                (actor_user_id, expected_revision),
            ).fetchone()
            if actor is None:
                connection.commit()
                return None
            actor_classes = tuple(
                row["class_id"]
                for row in connection.execute(
                    """
                    SELECT memberships.class_id
                    FROM class_memberships AS memberships
                    JOIN classes ON classes.class_id = memberships.class_id
                    WHERE memberships.user_id = ? AND memberships.role = ?
                        AND classes.active = 1
                    ORDER BY memberships.class_id
                    """,
                    (actor["user_id"], actor["role"]),
                )
            )
            target = None
            target_classes: tuple[str, ...] = ()
            if target_user_id is not None:
                target = connection.execute(
                    """
                    SELECT user_id, role FROM users
                    WHERE user_id = ? AND active = 1
                    """,
                    (target_user_id,),
                ).fetchone()
                if target is not None:
                    target_classes = tuple(
                        row["class_id"]
                        for row in connection.execute(
                            """
                            SELECT memberships.class_id
                            FROM class_memberships AS memberships
                            JOIN classes ON classes.class_id = memberships.class_id
                            WHERE memberships.user_id = ?
                                AND memberships.role = 'student'
                                AND classes.active = 1
                            ORDER BY memberships.class_id
                            """,
                            (target["user_id"],),
                        )
                    )
            snapshot = DashboardAuthorizationSnapshot(
                actor_user_id=actor["user_id"],
                actor_role=actor["role"],
                actor_updated_at=_decode_datetime(actor["updated_at"]),
                actor_class_ids=actor_classes,
                target_user_id=None if target is None else target["user_id"],
                target_role=None if target is None else target["role"],
                target_class_ids=target_classes,
            )
            connection.commit()
            return snapshot
        except (ValueError, TypeError) as error:
            connection.rollback()
            raise IdentityStorageCorruptionError(
                "Snapshot autorizzazione dashboard persistito non valido."
            ) from error
        except sqlite3.DatabaseError as error:
            connection.rollback()
            raise IdentityStorageError(
                "Errore SQLite durante autorizzazione dashboard."
            ) from error
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save_membership(self, membership: ClassMembership) -> None:
        with self._transaction("save_membership") as connection:
            connection.execute(
                """
                INSERT INTO class_memberships VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, class_id, role) DO UPDATE SET
                    joined_at = excluded.joined_at,
                    source_provider = excluded.source_provider,
                    source_group_subject = excluded.source_group_subject
                """,
                (
                    membership.user_id,
                    membership.class_id,
                    membership.role,
                    _encode_datetime(membership.joined_at, "joined_at"),
                    membership.source_provider,
                    membership.source_group_subject,
                ),
            )

    def list_user_memberships(self, user_id: str) -> list[ClassMembership]:
        rows = self._query_all(
            "SELECT * FROM class_memberships WHERE user_id = ? ORDER BY class_id, role",
            (user_id,),
        )
        return [self._membership(row) for row in rows]

    def list_class_memberships(self, class_id: str) -> list[ClassMembership]:
        rows = self._query_all(
            "SELECT * FROM class_memberships WHERE class_id = ? ORDER BY user_id, role",
            (class_id,),
        )
        return [self._membership(row) for row in rows]

    def delete_membership(self, user_id: str, class_id: str, role: str) -> bool:
        with self._transaction("delete_membership") as connection:
            cursor = connection.execute(
                "DELETE FROM class_memberships WHERE user_id = ? AND class_id = ? AND role = ?",
                (user_id, class_id, role.lower()),
            )
            return cursor.rowcount == 1

    def save_external_group_mapping(
        self,
        mapping: ExternalGroupMapping,
        *,
        expected_updated_at: datetime | None,
    ) -> None:
        created_at = _encode_datetime(mapping.created_at, "created_at")
        updated_at = _encode_datetime(mapping.updated_at, "updated_at")
        expected_revision = (
            None
            if expected_updated_at is None
            else _encode_datetime(expected_updated_at, "expected_updated_at")
        )
        if expected_revision is None:
            if updated_at != created_at:
                raise IdentityStorageConflictError(
                    "Un nuovo mapping deve iniziare dalla revisione di creazione."
                )
        elif updated_at <= expected_revision:
            raise IdentityStorageConflictError(
                "La revisione mapping deve avanzare monotonicamente."
            )
        with self._transaction("save_external_group_mapping") as connection:
            existing = connection.execute(
                """
                SELECT class_id, created_at, updated_at FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                """,
                mapping.provider_key,
            ).fetchone()
            if expected_revision is None:
                if existing is not None:
                    raise IdentityStorageMappingGenerationConflictError(
                        "Mapping creato da un'altra operazione."
                    )
                self._reserve_external_group_mapping_generation(
                    connection, mapping, created_at
                )
                cursor = connection.execute(
                    """
                    INSERT INTO external_group_mappings
                        (provider, organization_subject, group_subject, class_id,
                         created_at, display_name, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        *mapping.provider_key,
                        mapping.class_id,
                        created_at,
                        mapping.display_name,
                        updated_at,
                    ),
                )
            else:
                if (
                    existing is None
                    or existing["created_at"] != created_at
                    or existing["updated_at"] != expected_revision
                ):
                    raise IdentityStorageMappingGenerationConflictError(
                        "Mapping modificato, rimosso o ricreato da un'altra operazione."
                    )
                cursor = connection.execute(
                    """
                    UPDATE external_group_mappings
                    SET display_name = ?, updated_at = ?
                    WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                        AND class_id = ? AND created_at = ? AND updated_at = ?
                    """,
                    (
                        mapping.display_name,
                        updated_at,
                        *mapping.provider_key,
                        mapping.class_id,
                        created_at,
                        expected_revision,
                    ),
                )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Il gruppo provider e gia associato a una classe diversa."
                )

    def read_external_group_mapping(
        self,
        provider: str,
        organization_subject: str,
        group_subject: str,
    ) -> ExternalGroupMapping | None:
        row = self._query_one(
            """
            SELECT * FROM external_group_mappings
            WHERE provider = ? AND organization_subject = ? AND group_subject = ?
            """,
            (provider.lower(), organization_subject, group_subject),
        )
        return None if row is None else self._mapping(row)

    def list_external_group_mappings(
        self, class_id: str | None = None
    ) -> list[ExternalGroupMapping]:
        if class_id is None:
            rows = self._query_all(
                "SELECT * FROM external_group_mappings ORDER BY provider, organization_subject, group_subject"
            )
        else:
            rows = self._query_all(
                """
                SELECT * FROM external_group_mappings WHERE class_id = ?
                ORDER BY provider, organization_subject, group_subject
                """,
                (class_id,),
            )
        return [self._mapping(row) for row in rows]

    def delete_external_group_mapping(
        self,
        provider: str,
        organization_subject: str,
        group_subject: str,
        *,
        expected_created_at: datetime,
        expected_updated_at: datetime,
    ) -> bool:
        expected_generation = _encode_datetime(
            expected_created_at, "expected_created_at"
        )
        expected_revision = _encode_datetime(
            expected_updated_at, "expected_updated_at"
        )
        with self._transaction("delete_external_group_mapping") as connection:
            cursor = connection.execute(
                """
                DELETE FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                    AND created_at = ? AND updated_at = ?
                """,
                (
                    provider.lower(),
                    organization_subject,
                    group_subject,
                    expected_generation,
                    expected_revision,
                ),
            )
            if cursor.rowcount == 1:
                return True
            exists = connection.execute(
                """
                SELECT 1 FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                """,
                (provider.lower(), organization_subject, group_subject),
            ).fetchone()
            if exists is None:
                return False
            raise IdentityStorageMappingGenerationConflictError(
                "Mapping rimosso o ricreato da un'altra operazione."
            )

    def read_latest_external_group_mapping_generation(
        self,
        provider: str,
        organization_subject: str,
        group_subject: str,
    ) -> datetime | None:
        row = self._query_one(
            """
            SELECT MAX(created_at) AS created_at
            FROM external_group_mapping_generations
            WHERE provider = ? AND organization_subject = ? AND group_subject = ?
            """,
            (provider.lower(), organization_subject, group_subject),
        )
        if row is None or row["created_at"] is None:
            return None
        return _decode_datetime(row["created_at"])

    @staticmethod
    def _reserve_external_group_mapping_generation(
        connection: sqlite3.Connection,
        mapping: ExternalGroupMapping,
        created_at: str,
    ) -> None:
        latest = connection.execute(
            """
            SELECT MAX(created_at) AS created_at
            FROM external_group_mapping_generations
            WHERE provider = ? AND organization_subject = ? AND group_subject = ?
            """,
            mapping.provider_key,
        ).fetchone()
        if latest is not None and latest["created_at"] is not None:
            if created_at <= latest["created_at"]:
                raise IdentityStorageMappingGenerationConflictError(
                    "Generazione mapping non monotona."
                )
        try:
            connection.execute(
                """
                INSERT INTO external_group_mapping_generations
                    (provider, organization_subject, group_subject, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (*mapping.provider_key, created_at),
            )
        except sqlite3.IntegrityError as error:
            raise IdentityStorageMappingGenerationConflictError(
                "Generazione mapping gruppo esterno gia utilizzata."
            ) from error

    def save_external_group_mapping_for_admin(
        self,
        mapping: ExternalGroupMapping,
        *,
        admin_user_id: str,
        expected_admin_updated_at: datetime,
        expected_class_updated_at: datetime,
        expected_mapping_created_at: datetime | None,
        expected_mapping_updated_at: datetime | None,
    ) -> None:
        created_at = _encode_datetime(mapping.created_at, "created_at")
        updated_at = _encode_datetime(mapping.updated_at, "updated_at")
        expected_mapping_generation = (
            None
            if expected_mapping_created_at is None
            else _encode_datetime(
                expected_mapping_created_at, "expected_mapping_created_at"
            )
        )
        expected_mapping_revision = (
            None
            if expected_mapping_updated_at is None
            else _encode_datetime(
                expected_mapping_updated_at, "expected_mapping_updated_at"
            )
        )
        if expected_mapping_generation is None:
            if expected_mapping_revision is not None or updated_at != created_at:
                raise IdentityStorageConflictError("Intent create mapping non valido.")
        elif expected_mapping_revision is None or updated_at <= expected_mapping_revision:
            raise IdentityStorageConflictError("Revisione mapping non monotona.")
        admin_revision = _encode_datetime(
            expected_admin_updated_at, "expected_admin_updated_at"
        )
        class_revision = _encode_datetime(
            expected_class_updated_at, "expected_class_updated_at"
        )
        with self._transaction(
            "save_external_group_mapping_for_admin"
        ) as connection:
            existing = connection.execute(
                """
                SELECT class_id, created_at, updated_at FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                """,
                mapping.provider_key,
            ).fetchone()
            if expected_mapping_generation is None:
                if existing is not None:
                    raise IdentityStorageMappingGenerationConflictError(
                        "Mapping creato da un'altra operazione."
                    )
                self._reserve_external_group_mapping_generation(
                    connection, mapping, created_at
                )
                cursor = connection.execute(
                    """
                    INSERT INTO external_group_mappings
                        (provider, organization_subject, group_subject, class_id,
                         created_at, display_name, updated_at)
                    SELECT ?, ?, ?, ?, ?, ?, ?
                    WHERE EXISTS (
                        SELECT 1 FROM users
                        WHERE user_id = ? AND active = 1 AND role = 'admin'
                            AND updated_at = ?
                    ) AND EXISTS (
                        SELECT 1 FROM classes
                        WHERE class_id = ? AND active = 1 AND updated_at = ?
                    )
                    """,
                    (
                        *mapping.provider_key,
                        mapping.class_id,
                        created_at,
                        mapping.display_name,
                        updated_at,
                        admin_user_id,
                        admin_revision,
                        mapping.class_id,
                        class_revision,
                    ),
                )
            else:
                if (
                    existing is None
                    or existing["created_at"] != expected_mapping_generation
                    or existing["updated_at"] != expected_mapping_revision
                ):
                    raise IdentityStorageMappingGenerationConflictError(
                        "Mapping rimosso o ricreato da un'altra operazione."
                    )
                cursor = connection.execute(
                    """
                    UPDATE external_group_mappings
                    SET display_name = ?, updated_at = ?
                    WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                        AND class_id = ? AND created_at = ? AND updated_at = ?
                        AND EXISTS (
                            SELECT 1 FROM users
                            WHERE user_id = ? AND active = 1 AND role = 'admin'
                                AND updated_at = ?
                        )
                        AND EXISTS (
                            SELECT 1 FROM classes
                            WHERE class_id = ? AND active = 1 AND updated_at = ?
                        )
                    """,
                    (
                        mapping.display_name,
                        updated_at,
                        *mapping.provider_key,
                        mapping.class_id,
                        created_at,
                        expected_mapping_revision,
                        admin_user_id,
                        admin_revision,
                        mapping.class_id,
                        class_revision,
                    ),
                )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Admin, classe o mapping modificati durante il salvataggio."
                )

    def delete_external_group_mapping_for_admin(
        self,
        mapping: ExternalGroupMapping,
        *,
        admin_user_id: str,
        expected_admin_updated_at: datetime,
        expected_class_updated_at: datetime,
    ) -> bool:
        created_at = _encode_datetime(mapping.created_at, "created_at")
        mapping_revision = _encode_datetime(mapping.updated_at, "updated_at")
        admin_revision = _encode_datetime(
            expected_admin_updated_at, "expected_admin_updated_at"
        )
        class_revision = _encode_datetime(
            expected_class_updated_at, "expected_class_updated_at"
        )
        with self._transaction(
            "delete_external_group_mapping_for_admin"
        ) as connection:
            cursor = connection.execute(
                """
                DELETE FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                    AND class_id = ? AND created_at = ? AND updated_at = ?
                    AND EXISTS (
                        SELECT 1 FROM users
                        WHERE user_id = ? AND active = 1 AND role = 'admin'
                            AND updated_at = ?
                    )
                    AND EXISTS (
                        SELECT 1 FROM classes
                        WHERE class_id = ? AND active = 1 AND updated_at = ?
                    )
                """,
                (
                    *mapping.provider_key,
                    mapping.class_id,
                    created_at,
                    mapping_revision,
                    admin_user_id,
                    admin_revision,
                    mapping.class_id,
                    class_revision,
                ),
            )
            if cursor.rowcount == 1:
                return True
            exists = connection.execute(
                """
                SELECT 1 FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                """,
                mapping.provider_key,
            ).fetchone()
            if exists is None:
                return False
            raise IdentityStorageConflictError(
                "Admin, classe o mapping modificati durante la rimozione."
            )

    def synchronize_github_memberships(
        self,
        user_id: str,
        desired_memberships: tuple[ClassMembership, ...],
        *,
        expected_user_updated_at: datetime,
        expected_identity_subject: str,
        expected_identity_linked_at: datetime,
        expected_memberships: tuple[ClassMembership, ...],
        expected_mappings: tuple[ExternalGroupMapping, ...],
        expected_snapshot_group_keys: tuple[tuple[str, str], ...],
        expected_snapshot_captured_at: datetime,
        max_snapshot_age: timedelta,
        future_skew: timedelta,
        expected_classes: tuple[ClassGroup, ...],
    ) -> None:
        if (
            type(user_id) is not str
            or not user_id
            or type(desired_memberships) is not tuple
            or type(expected_memberships) is not tuple
            or type(expected_mappings) is not tuple
            or type(expected_snapshot_group_keys) is not tuple
            or type(expected_classes) is not tuple
            or len(expected_snapshot_group_keys) != len(set(expected_snapshot_group_keys))
            or len({item.class_id for item in desired_memberships}) != len(desired_memberships)
            or any(
                type(item) is not ClassMembership
                or item.user_id != user_id
                or item.role != "student"
                or item.source_provider != "github"
                for item in desired_memberships
            )
            or any(type(item) is not ClassMembership or item.user_id != user_id for item in expected_memberships)
            or any(type(item) is not ExternalGroupMapping or item.provider != "github" for item in expected_mappings)
            or any(
                type(key) is not tuple
                or len(key) != 2
                or any(type(value) is not str or not value for value in key)
                for key in expected_snapshot_group_keys
            )
            or any(type(item) is not ClassGroup for item in expected_classes)
            or len({item.class_id for item in expected_classes}) != len(expected_classes)
            or type(max_snapshot_age) is not timedelta
            or max_snapshot_age <= timedelta(0)
            or type(future_skew) is not timedelta
            or future_skew < timedelta(0)
        ):
            raise IdentityStorageError("Snapshot sincronizzazione GitHub non valido.")
        snapshot_captured_at = _decode_datetime(
            _encode_datetime(expected_snapshot_captured_at, "expected_snapshot_captured_at")
        )
        user_revision = _encode_datetime(expected_user_updated_at, "expected_user_updated_at")
        identity_generation = _encode_datetime(expected_identity_linked_at, "expected_identity_linked_at")

        def membership_row(item: ClassMembership) -> tuple[object, ...]:
            return (
                item.user_id,
                item.class_id,
                item.role,
                _encode_datetime(item.joined_at, "joined_at"),
                item.source_provider,
                item.source_group_subject,
            )

        expected_membership_rows = sorted(membership_row(item) for item in expected_memberships)
        desired_rows = [membership_row(item) for item in desired_memberships]
        expected_mapping_rows = sorted(
            (
                item.organization_subject,
                item.group_subject,
                item.class_id,
                _encode_datetime(item.created_at, "mapping_created_at"),
                _encode_datetime(item.updated_at, "mapping_updated_at"),
            )
            for item in expected_mappings
        )
        if any(
            not any(
                mapping.class_id == membership.class_id
                and mapping.group_subject == membership.source_group_subject
                for mapping in expected_mappings
            )
            for membership in desired_memberships
        ):
            raise IdentityStorageError("Membership desiderata senza mapping GitHub correlato.")
        if snapshot_captured_at < _decode_datetime(identity_generation):
            raise IdentityStorageError("Snapshot GitHub precedente al collegamento identita.")
        with self._transaction("synchronize_github_memberships") as connection:
            transaction_now = self._clock()
            if (
                not isinstance(transaction_now, datetime)
                or transaction_now.tzinfo is None
                or transaction_now.utcoffset() is None
            ):
                raise IdentityStorageError("Clock storage sincronizzazione non valido.")
            transaction_now = transaction_now.astimezone(timezone.utc)
            if (
                snapshot_captured_at <= transaction_now - max_snapshot_age
                or snapshot_captured_at > transaction_now + future_skew
            ):
                raise IdentityStorageConflictError("Snapshot GitHub scaduto durante sincronizzazione.")
            user_row = connection.execute(
                "SELECT active, role, updated_at FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if user_row is None or tuple(user_row) != (1, "student", user_revision):
                raise IdentityStorageConflictError("Utente modificato durante sincronizzazione.")
            identity_row = connection.execute(
                """
                SELECT user_id, linked_at FROM external_identities
                WHERE provider = 'github' AND subject = ?
                """,
                (expected_identity_subject,),
            ).fetchone()
            if identity_row is None or tuple(identity_row) != (user_id, identity_generation):
                raise IdentityStorageConflictError("Identita GitHub modificata durante sincronizzazione.")
            membership_rows = [
                tuple(row)
                for row in connection.execute(
                    "SELECT * FROM class_memberships WHERE user_id = ? ORDER BY class_id, role",
                    (user_id,),
                ).fetchall()
            ]
            if membership_rows != expected_membership_rows:
                raise IdentityStorageConflictError("Membership modificate durante sincronizzazione.")
            connection.execute(
                """
                CREATE TEMP TABLE sync_expected_groups (
                    organization_subject TEXT NOT NULL,
                    group_subject TEXT NOT NULL,
                    PRIMARY KEY (organization_subject, group_subject)
                )
                """
            )
            connection.executemany(
                "INSERT INTO sync_expected_groups VALUES (?, ?)",
                expected_snapshot_group_keys,
            )
            mapping_rows = sorted(
                tuple(row)
                for row in connection.execute(
                    """
                    SELECT mappings.organization_subject, mappings.group_subject,
                           mappings.class_id, mappings.created_at, mappings.updated_at
                    FROM external_group_mappings AS mappings
                    INNER JOIN sync_expected_groups AS expected
                        ON expected.organization_subject = mappings.organization_subject
                        AND expected.group_subject = mappings.group_subject
                    WHERE mappings.provider = 'github'
                    """
                ).fetchall()
            )
            if mapping_rows != expected_mapping_rows:
                raise IdentityStorageConflictError("Mapping GitHub modificati durante sincronizzazione.")
            expected_class_ids = {item.class_id for item in expected_classes}
            if expected_class_ids != {item.class_id for item in expected_mappings}:
                raise IdentityStorageError("Classi snapshot sincronizzazione incoerenti.")
            for class_group in expected_classes:
                class_row = connection.execute(
                    "SELECT active, updated_at FROM classes WHERE class_id = ?",
                    (class_group.class_id,),
                ).fetchone()
                if class_row is None or tuple(class_row) != (
                    int(class_group.active),
                    _encode_datetime(class_group.updated_at, "class_updated_at"),
                ):
                    raise IdentityStorageConflictError("Classe modificata durante sincronizzazione.")
            if any(item.class_id not in expected_class_ids for item in desired_memberships):
                raise IdentityStorageError("Membership desiderata senza mapping GitHub.")
            connection.execute(
                """
                DELETE FROM class_memberships
                WHERE user_id = ? AND role = 'student' AND source_provider = 'github'
                """,
                (user_id,),
            )
            connection.executemany(
                "INSERT INTO class_memberships VALUES (?, ?, ?, ?, ?, ?)",
                desired_rows,
            )

    def onboard_pending_user_from_external_group(
        self,
        membership: ClassMembership,
        *,
        expected_user_updated_at: datetime,
        expected_identity_subject: str,
        expected_identity_linked_at: datetime,
        expected_mapping: ExternalGroupMapping,
        expected_snapshot_group_keys: tuple[tuple[str, str], ...],
        expected_snapshot_captured_at: datetime,
        max_snapshot_age: timedelta,
        future_skew: timedelta,
        expected_class_updated_at: datetime,
    ) -> None:
        if (
            type(expected_snapshot_group_keys) is not tuple
            or not expected_snapshot_group_keys
            or any(
                type(key) is not tuple
                or len(key) != 2
                or any(type(value) is not str or not value for value in key)
                for key in expected_snapshot_group_keys
            )
            or len(expected_snapshot_group_keys) != len(set(expected_snapshot_group_keys))
            or expected_mapping.provider != "github"
            or membership.source_provider != "github"
            or membership.class_id != expected_mapping.class_id
            or membership.source_group_subject != expected_mapping.group_subject
            or type(max_snapshot_age) is not timedelta
            or max_snapshot_age <= timedelta(0)
            or type(future_skew) is not timedelta
            or future_skew < timedelta(0)
        ):
            raise IdentityStorageError("Snapshot gruppi onboarding non valido.")
        snapshot_captured_at = _decode_datetime(
            _encode_datetime(
                expected_snapshot_captured_at, "expected_snapshot_captured_at"
            )
        )
        joined_at = _encode_datetime(membership.joined_at, "joined_at")
        user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        identity_generation = _encode_datetime(
            expected_identity_linked_at, "expected_identity_linked_at"
        )
        mapping_generation = _encode_datetime(
            expected_mapping.created_at, "expected_mapping_created_at"
        )
        class_revision = _encode_datetime(
            expected_class_updated_at, "expected_class_updated_at"
        )
        with self._transaction(
            "onboard_pending_user_from_external_group"
        ) as connection:
            transaction_now = self._clock()
            if (
                not isinstance(transaction_now, datetime)
                or transaction_now.tzinfo is None
                or transaction_now.utcoffset() is None
            ):
                raise IdentityStorageError("Clock storage onboarding non valido.")
            transaction_now = transaction_now.astimezone(timezone.utc)
            if (
                snapshot_captured_at <= transaction_now - max_snapshot_age
                or snapshot_captured_at > transaction_now + future_skew
            ):
                raise IdentityStorageConflictError(
                    "Snapshot GitHub scaduto durante onboarding."
                )
            connection.execute(
                """
                CREATE TEMP TABLE onboarding_expected_groups (
                    organization_subject TEXT NOT NULL,
                    group_subject TEXT NOT NULL,
                    PRIMARY KEY (organization_subject, group_subject)
                )
                """
            )
            connection.executemany(
                "INSERT INTO onboarding_expected_groups VALUES (?, ?)",
                expected_snapshot_group_keys,
            )
            mapped_rows = connection.execute(
                """
                SELECT mappings.organization_subject, mappings.group_subject,
                       mappings.class_id, mappings.created_at, mappings.updated_at
                FROM external_group_mappings AS mappings
                INNER JOIN onboarding_expected_groups AS expected
                    ON expected.organization_subject = mappings.organization_subject
                    AND expected.group_subject = mappings.group_subject
                WHERE mappings.provider = 'github'
                """
            ).fetchall()
            expected_row = (
                expected_mapping.organization_subject,
                expected_mapping.group_subject,
                expected_mapping.class_id,
                mapping_generation,
                _encode_datetime(expected_mapping.updated_at, "expected_mapping_updated_at"),
            )
            if len(mapped_rows) != 1 or tuple(mapped_rows[0]) != expected_row:
                raise IdentityStorageConflictError(
                    "Insieme mapping GitHub modificato durante onboarding."
                )
            cursor = connection.execute(
                """
                UPDATE users SET role = 'student', updated_at = ?
                WHERE user_id = ? AND active = 1 AND role = 'pending'
                    AND updated_at = ?
                    AND EXISTS (
                        SELECT 1 FROM external_identities
                        WHERE provider = 'github' AND subject = ?
                            AND user_id = users.user_id AND linked_at = ?
                    )
                    AND EXISTS (
                        SELECT 1 FROM external_group_mappings
                        WHERE provider = ? AND organization_subject = ?
                            AND group_subject = ? AND class_id = ? AND created_at = ?
                            AND updated_at = ?
                    )
                    AND EXISTS (
                        SELECT 1 FROM classes
                        WHERE class_id = ? AND active = 1 AND updated_at = ?
                    )
                """,
                (
                    joined_at,
                    membership.user_id,
                    user_revision,
                    expected_identity_subject,
                    identity_generation,
                    *expected_mapping.provider_key,
                    expected_mapping.class_id,
                    mapping_generation,
                    _encode_datetime(expected_mapping.updated_at, "expected_mapping_updated_at"),
                    membership.class_id,
                    class_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Utente, identita, mapping o classe modificati durante onboarding."
                )
            connection.execute(
                """
                INSERT INTO class_memberships
                    (user_id, class_id, role, joined_at, source_provider,
                     source_group_subject)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    membership.user_id,
                    membership.class_id,
                    membership.role,
                    joined_at,
                    membership.source_provider,
                    membership.source_group_subject,
                ),
            )

    def create_session(self, session: UserSession) -> None:
        if session.audience != "web" or session.source_pairing_id is not None:
            raise IdentityStorageConflictError(
                "Le sessioni TUI richiedono il consumo pairing atomico."
            )
        with self._transaction("create_session") as connection:
            connection.execute(
                """
                INSERT INTO sessions
                    (session_id, user_id, token_digest, created_at, expires_at,
                     last_seen_at, revoked_at, audience, source_pairing_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session.session_id,
                    session.user_id,
                    session.token_digest,
                    _encode_datetime(session.created_at, "created_at"),
                    _encode_datetime(session.expires_at, "expires_at"),
                    _encode_datetime(session.last_seen_at, "last_seen_at"),
                    None
                    if session.revoked_at is None
                    else _encode_datetime(session.revoked_at, "revoked_at"),
                    session.audience,
                    session.source_pairing_id,
                ),
            )

    def create_session_for_active_user(
        self, session: UserSession, *, expected_user_updated_at: datetime
    ) -> None:
        if session.audience != "web" or session.source_pairing_id is not None:
            raise IdentityStorageConflictError(
                "Le sessioni TUI richiedono il consumo pairing atomico."
            )
        expected_user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        with self._transaction("create_session_for_active_user") as connection:
            cursor = connection.execute(
                """
                INSERT INTO sessions
                    (session_id, user_id, token_digest, created_at, expires_at,
                     last_seen_at, revoked_at, audience, source_pairing_id)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?
                FROM users
                WHERE user_id = ? AND active = 1 AND updated_at = ?
                """,
                (
                    session.session_id,
                    session.user_id,
                    session.token_digest,
                    _encode_datetime(session.created_at, "created_at"),
                    _encode_datetime(session.expires_at, "expires_at"),
                    _encode_datetime(session.last_seen_at, "last_seen_at"),
                    None
                    if session.revoked_at is None
                    else _encode_datetime(session.revoked_at, "revoked_at"),
                    session.audience,
                    session.source_pairing_id,
                    session.user_id,
                    expected_user_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "Impossibile creare la sessione per un utente non attivo."
                )

    def read_session(self, session_id: str) -> UserSession | None:
        row = self._query_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        return None if row is None else self._session(row)

    def read_session_by_token_digest(self, token_digest: str) -> UserSession | None:
        row = self._query_one("SELECT * FROM sessions WHERE token_digest = ?", (token_digest.lower(),))
        return None if row is None else self._session(row)

    def read_tui_authentication_snapshot(
        self, token_digest: str, pairing_id: str
    ) -> tuple[UserSession | None, UserAccount | None, TuiPairing | None]:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            session_row = connection.execute(
                "SELECT * FROM sessions WHERE token_digest = ?",
                (token_digest.lower(),),
            ).fetchone()
            session = None if session_row is None else self._session(session_row)
            user_row = (
                None
                if session is None
                else connection.execute(
                    "SELECT * FROM users WHERE user_id = ?", (session.user_id,)
                ).fetchone()
            )
            pairing_row = connection.execute(
                "SELECT * FROM tui_pairings WHERE pairing_id = ?", (pairing_id,)
            ).fetchone()
            connection.commit()
            return (
                session,
                None if user_row is None else self._user(user_row),
                None if pairing_row is None else self._pairing(pairing_row),
            )
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save_session(self, session: UserSession) -> None:
        created_at = _encode_datetime(session.created_at, "created_at")
        expires_at = _encode_datetime(session.expires_at, "expires_at")
        last_seen_at = _encode_datetime(session.last_seen_at, "last_seen_at")
        immutable = (
            session.session_id,
            session.user_id,
            session.token_digest,
            created_at,
            expires_at,
            session.audience,
            session.source_pairing_id,
        )
        with self._transaction("save_session") as connection:
            if session.revoked_at is None:
                cursor = connection.execute(
                    """
                    UPDATE sessions SET last_seen_at = ?
                    WHERE session_id = ? AND user_id = ? AND token_digest = ?
                        AND created_at = ? AND expires_at = ? AND audience = ?
                        AND source_pairing_id IS ?
                        AND revoked_at IS NULL AND last_seen_at <= ?
                    """,
                    (last_seen_at,) + immutable + (last_seen_at,),
                )
            else:
                revoked_at = _encode_datetime(session.revoked_at, "revoked_at")
                cursor = connection.execute(
                    """
                    UPDATE sessions SET
                        last_seen_at = CASE
                            WHEN last_seen_at > ? THEN last_seen_at ELSE ?
                        END,
                        revoked_at = ?
                    WHERE session_id = ? AND user_id = ? AND token_digest = ?
                        AND created_at = ? AND expires_at = ? AND audience = ?
                        AND source_pairing_id IS ?
                        AND revoked_at IS NULL AND last_seen_at <= ?
                    """,
                    (last_seen_at, last_seen_at, revoked_at)
                    + immutable
                    + (revoked_at,),
                )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM sessions WHERE session_id = ?", (session.session_id,)
                ).fetchone()
                if exists is None:
                    raise IdentityStorageNotFoundError("Sessione da aggiornare non trovata.")
                raise IdentityStorageConflictError(
                    "Sessione modificata o revocata da un'altra operazione."
                )

    def save_session_for_active_user(
        self, session: UserSession, *, expected_user_updated_at: datetime
    ) -> None:
        if session.revoked_at is not None:
            raise IdentityStorageConflictError(
                "Una sessione revocata non puo essere usata come touch attivo."
            )
        created_at = _encode_datetime(session.created_at, "created_at")
        expires_at = _encode_datetime(session.expires_at, "expires_at")
        last_seen_at = _encode_datetime(session.last_seen_at, "last_seen_at")
        expected_user_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        with self._transaction("save_session_for_active_user") as connection:
            cursor = connection.execute(
                """
                UPDATE sessions SET last_seen_at = ?
                WHERE session_id = ? AND user_id = ? AND token_digest = ?
                    AND created_at = ? AND expires_at = ? AND audience = ?
                    AND source_pairing_id IS ?
                    AND revoked_at IS NULL AND last_seen_at <= ?
                    AND EXISTS (
                        SELECT 1 FROM users
                        WHERE users.user_id = sessions.user_id
                            AND users.active = 1 AND users.updated_at = ?
                    )
                """,
                (
                    last_seen_at,
                    session.session_id,
                    session.user_id,
                    session.token_digest,
                    created_at,
                    expires_at,
                    session.audience,
                    session.source_pairing_id,
                    last_seen_at,
                    expected_user_revision,
                ),
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM sessions WHERE session_id = ?", (session.session_id,)
                ).fetchone()
                if exists is None:
                    raise IdentityStorageNotFoundError(
                        "Sessione da aggiornare non trovata."
                    )
                raise IdentityStorageConflictError(
                    "Sessione o utente modificati durante l'autenticazione."
                )

    def list_user_sessions(self, user_id: str) -> list[UserSession]:
        rows = self._query_all(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at, session_id",
            (user_id,),
        )
        return [self._session(row) for row in rows]

    def revoke_user_sessions(
        self,
        user_id: str,
        revoked_at: datetime,
        *,
        audience: str | None = None,
    ) -> int:
        encoded = _encode_datetime(revoked_at, "revoked_at")
        if audience is not None and audience not in {"web", "tui"}:
            raise IdentityStorageConflictError("Audience revoca non valida.")
        audience_sql = "" if audience is None else " AND audience = ?"
        audience_values: tuple[object, ...] = () if audience is None else (audience,)
        with self._transaction("revoke_user_sessions") as connection:
            stale = connection.execute(
                f"""
                SELECT COUNT(*) FROM sessions
                WHERE user_id = ? AND revoked_at IS NULL AND expires_at > ?
                    AND (created_at > ? OR last_seen_at > ?){audience_sql}
                """,
                (user_id, encoded, encoded, encoded) + audience_values,
            ).fetchone()[0]
            if stale:
                raise IdentityStorageConflictError(
                    "revoked_at precede la creazione o l'ultimo utilizzo di una sessione attiva."
                )
            cursor = connection.execute(
                f"""
                UPDATE sessions SET revoked_at = ?
                WHERE user_id = ? AND revoked_at IS NULL
                    AND created_at <= ? AND expires_at > ?{audience_sql}
                """,
                (encoded, user_id, encoded, encoded) + audience_values,
            )
            return cursor.rowcount

    def delete_expired_sessions(self, expired_before: datetime) -> int:
        encoded = _encode_datetime(expired_before, "expired_before")
        with self._transaction("delete_expired_sessions") as connection:
            cursor = connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (encoded,))
            return cursor.rowcount

    def create_pairing(self, pairing: TuiPairing) -> None:
        with self._transaction("create_pairing") as connection:
            connection.execute(
                "INSERT INTO tui_pairings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                self._pairing_values(pairing),
            )

    def read_pairing(self, pairing_id: str) -> TuiPairing | None:
        row = self._query_one("SELECT * FROM tui_pairings WHERE pairing_id = ?", (pairing_id,))
        return None if row is None else self._pairing(row)

    def read_pairing_by_code_digest(self, code_digest: str) -> TuiPairing | None:
        row = self._query_one(
            "SELECT * FROM tui_pairings WHERE code_digest = ?", (code_digest.lower(),)
        )
        return None if row is None else self._pairing(row)

    @staticmethod
    def _pairing_values(pairing: TuiPairing) -> tuple[object, ...]:
        def optional(value: datetime | None, field_name: str) -> str | None:
            return None if value is None else _encode_datetime(value, field_name)

        return (
            pairing.pairing_id,
            pairing.code_digest,
            pairing.status,
            _encode_datetime(pairing.created_at, "created_at"),
            _encode_datetime(pairing.expires_at, "expires_at"),
            pairing.user_id,
            optional(pairing.authorized_at, "authorized_at"),
            optional(pairing.consumed_at, "consumed_at"),
            optional(pairing.expired_at, "expired_at"),
            optional(pairing.revoked_at, "revoked_at"),
        )

    def save_pairing(self, pairing: TuiPairing) -> None:
        self._save_pairing_transition(pairing, require_active_user=False)

    def save_pairing_for_active_user(
        self, pairing: TuiPairing, *, expected_user_updated_at: datetime
    ) -> None:
        if pairing.user_id is None:
            raise IdentityStorageConflictError(
                "La transizione pairing richiede un utente attivo."
            )
        self._save_pairing_transition(
            pairing,
            require_active_user=True,
            expected_user_updated_at=expected_user_updated_at,
        )

    def consume_pairing_and_create_session(
        self,
        pairing: TuiPairing,
        session: UserSession,
        *,
        expected_user_updated_at: datetime,
        expected_user_role: str,
    ) -> None:
        if (
            pairing.status != "consumed"
            or pairing.user_id is None
            or pairing.authorized_at is None
            or pairing.consumed_at is None
            or session.user_id != pairing.user_id
            or session.created_at != pairing.consumed_at
            or session.last_seen_at != session.created_at
            or session.revoked_at is not None
            or session.audience != "tui"
            or session.source_pairing_id != pairing.pairing_id
            or expected_user_role != "student"
        ):
            raise IdentityStorageConflictError(
                "Contratto emissione sessione pairing non valido."
            )
        expected_revision = _encode_datetime(
            expected_user_updated_at, "expected_user_updated_at"
        )
        created_at = _encode_datetime(pairing.created_at, "pairing_created_at")
        expires_at = _encode_datetime(pairing.expires_at, "pairing_expires_at")
        authorized_at = _encode_datetime(
            pairing.authorized_at, "pairing_authorized_at"
        )
        consumed_at = _encode_datetime(pairing.consumed_at, "pairing_consumed_at")
        expired = False
        with self._transaction(
            "consume_pairing_and_create_session"
        ) as connection:
            transaction_instant = max(pairing.consumed_at, self._clock())
            transaction_time = _encode_datetime(transaction_instant, "storage_clock")
            if transaction_instant >= pairing.expires_at:
                cursor = connection.execute(
                    """
                    UPDATE tui_pairings
                    SET status = 'expired', expired_at = ?
                    WHERE pairing_id = ? AND code_digest = ? AND status = 'authorized'
                        AND created_at = ? AND expires_at = ? AND user_id = ?
                        AND authorized_at = ? AND consumed_at IS NULL
                        AND expired_at IS NULL AND revoked_at IS NULL
                    """,
                    (
                        transaction_time,
                        pairing.pairing_id,
                        pairing.code_digest,
                        created_at,
                        expires_at,
                        pairing.user_id,
                        authorized_at,
                    ),
                )
                if cursor.rowcount != 1:
                    raise IdentityStorageConflictError(
                        "Pairing modificato durante la scadenza."
                    )
                expired = True
            else:
                if transaction_instant >= session.expires_at:
                    raise IdentityStorageSessionExpiredError(
                        "Sessione TUI scaduta prima dell'inserimento atomico."
                    )
                cursor = connection.execute(
                    """
                    UPDATE tui_pairings
                    SET status = 'consumed', consumed_at = ?
                    WHERE pairing_id = ? AND code_digest = ? AND status = 'authorized'
                        AND created_at = ? AND expires_at = ? AND user_id = ?
                        AND authorized_at = ? AND consumed_at IS NULL
                        AND expired_at IS NULL AND revoked_at IS NULL
                        AND created_at <= ? AND authorized_at <= ? AND expires_at > ?
                        AND EXISTS (
                            SELECT 1 FROM users
                            WHERE users.user_id = tui_pairings.user_id
                                AND users.active = 1 AND users.role = ?
                                AND users.updated_at = ?
                        )
                    """,
                    (
                        consumed_at,
                        pairing.pairing_id,
                        pairing.code_digest,
                        created_at,
                        expires_at,
                        pairing.user_id,
                        authorized_at,
                        transaction_time,
                        transaction_time,
                        transaction_time,
                        expected_user_role,
                        expected_revision,
                    ),
                )
                if cursor.rowcount != 1:
                    raise IdentityStorageConflictError(
                        "Pairing o utente modificati durante il consumo."
                    )
                connection.execute(
                    """
                    INSERT INTO sessions
                        (session_id, user_id, token_digest, created_at, expires_at,
                         last_seen_at, revoked_at, audience, source_pairing_id)
                    VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    """,
                    (
                        session.session_id,
                        session.user_id,
                        session.token_digest,
                        _encode_datetime(session.created_at, "session_created_at"),
                        _encode_datetime(session.expires_at, "session_expires_at"),
                        _encode_datetime(session.last_seen_at, "session_last_seen_at"),
                        session.audience,
                        session.source_pairing_id,
                    ),
                )
        if expired:
            raise IdentityStoragePairingExpiredError(
                "Pairing scaduto durante il consumo."
            )

    def _save_pairing_transition(
        self,
        pairing: TuiPairing,
        *,
        require_active_user: bool,
        expected_user_updated_at: datetime | None = None,
    ) -> None:
        values = self._pairing_values(pairing)
        if pairing.status in {"consumed", "expired", "revoked"} and pairing.user_id is not None:
            predecessors = ("authorized",)
            prior_identity_sql = " AND user_id = ? AND authorized_at = ?"
            prior_identity_values = (values[5], values[6])
        elif pairing.status in {"expired", "revoked"}:
            predecessors = ("pending",)
            prior_identity_sql = ""
            prior_identity_values = ()
        else:
            predecessors = {
                "pending": ("pending",),
                "authorized": ("pending",),
                "consumed": ("authorized",),
            }[pairing.status]
            prior_identity_sql = ""
            prior_identity_values = ()
        if require_active_user:
            expected_user_revision = _encode_datetime(
                expected_user_updated_at, "expected_user_updated_at"
            )
            active_user_sql = (
                " AND EXISTS (SELECT 1 FROM users"
                " WHERE users.user_id = ? AND users.active = 1"
                " AND users.updated_at = ?)"
            )
            active_user_values = (pairing.user_id, expected_user_revision)
        else:
            active_user_sql = ""
            active_user_values = ()
        placeholders = ", ".join("?" for _ in predecessors)
        expiry_sql = " AND expires_at > ?" if pairing.status == "authorized" else ""
        expired_during_authorization = False
        with self._transaction("save_pairing") as connection:
            expiry_values = (
                (
                    _encode_datetime(self._clock(), "pairing_transition_clock"),
                )
                if pairing.status == "authorized"
                else ()
            )
            cursor = connection.execute(
                f"""
                UPDATE tui_pairings SET status = ?, user_id = ?, authorized_at = ?,
                    consumed_at = ?, expired_at = ?, revoked_at = ?
                WHERE pairing_id = ? AND code_digest = ? AND created_at = ? AND expires_at = ?
                    AND status IN ({placeholders}){prior_identity_sql}{active_user_sql}{expiry_sql}
                """,
                (
                    values[2],
                    values[5],
                    values[6],
                    values[7],
                    values[8],
                    values[9],
                    values[0],
                    values[1],
                    values[3],
                    values[4],
                )
                + predecessors
                + prior_identity_values
                + active_user_values
                + expiry_values,
            )
            if cursor.rowcount != 1:
                current = connection.execute(
                    "SELECT status, expires_at FROM tui_pairings WHERE pairing_id = ?",
                    (pairing.pairing_id,),
                ).fetchone()
                if current is None:
                    raise IdentityStorageNotFoundError("Pairing da aggiornare non trovato.")
                if (
                    pairing.status == "authorized"
                    and current["status"] == "pending"
                    and current["expires_at"] <= expiry_values[0]
                ):
                    expired_cursor = connection.execute(
                        """
                        UPDATE tui_pairings SET status = 'expired', expired_at = ?
                        WHERE pairing_id = ? AND status = 'pending' AND expires_at <= ?
                        """,
                        (expiry_values[0], pairing.pairing_id, expiry_values[0]),
                    )
                    if expired_cursor.rowcount != 1:
                        raise IdentityStorageConflictError(
                            "Pairing modificato durante la scadenza."
                        )
                    expired_during_authorization = True
                else:
                    raise IdentityStorageConflictError(
                        "Pairing modificato, transitato o associato a un utente non attivo."
                    )
        if expired_during_authorization:
            raise IdentityStoragePairingExpiredError(
                "Pairing scaduto durante l'autorizzazione."
            )

    def delete_expired_pairings(self, expired_before: datetime) -> int:
        encoded = _encode_datetime(expired_before, "expired_before")
        with self._transaction("delete_expired_pairings") as connection:
            cursor = connection.execute(
                """
                DELETE FROM tui_pairings
                WHERE expires_at <= ?
                    AND NOT EXISTS (
                        SELECT 1 FROM sessions
                        WHERE sessions.source_pairing_id = tui_pairings.pairing_id
                    )
                """,
                (encoded,),
            )
            return cursor.rowcount
