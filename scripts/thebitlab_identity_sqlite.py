from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
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
from scripts.thebitlab_identity_ports import (
    IdentityStorageConflictError,
    IdentityStorageCorruptionError,
    IdentityStorageError,
    IdentityStorageNotFoundError,
)


SCHEMA_VERSION = 1
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

    def __init__(self, database_path: Path | str) -> None:
        if str(database_path) == ":memory:":
            raise IdentityStorageError(
                "Usare un file temporaneo: connessioni isolate non supportano SQLite :memory:."
            )
        self.database_path = Path(database_path)
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
            if 1 not in versions:
                for statement in _MIGRATION_1:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (1, _encode_datetime(datetime.now(timezone.utc), "applied_at")),
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
            connection.execute(
                "INSERT INTO external_identities VALUES (?, ?, ?, ?, ?, ?)",
                (
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    _encode_datetime(identity.linked_at, "linked_at"),
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

    def link_external_identity(self, identity: ExternalIdentity) -> None:
        with self._transaction("link_external_identity") as connection:
            cursor = connection.execute(
                """
                INSERT INTO external_identities VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, subject) DO UPDATE SET
                    email = excluded.email,
                    username = excluded.username
                WHERE external_identities.user_id = excluded.user_id
                """,
                (
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    _encode_datetime(identity.linked_at, "linked_at"),
                    identity.email,
                    identity.username,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageConflictError(
                    "L'identita provider e gia collegata a un utente diverso."
                )

    def refresh_external_identity(
        self, identity: ExternalIdentity, *, expected_linked_at: datetime
    ) -> None:
        expected_revision = _encode_datetime(expected_linked_at, "expected_linked_at")
        with self._transaction("refresh_external_identity") as connection:
            cursor = connection.execute(
                """
                UPDATE external_identities SET email = ?, username = ?
                WHERE provider = ? AND subject = ? AND user_id = ? AND linked_at = ?
                """,
                (
                    identity.email,
                    identity.username,
                    identity.provider,
                    identity.subject,
                    identity.user_id,
                    expected_revision,
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

    def read_external_identity(self, provider: str, subject: str) -> ExternalIdentity | None:
        row = self._query_one(
            "SELECT * FROM external_identities WHERE provider = ? AND subject = ?",
            (provider.lower(), subject),
        )
        return None if row is None else self._external_identity(row)

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

    def save_class(self, class_group: ClassGroup) -> None:
        with self._transaction("save_class") as connection:
            cursor = connection.execute(
                """
                UPDATE classes SET label = ?, school_year = ?, active = ?, created_at = ?,
                    updated_at = ? WHERE class_id = ?
                """,
                (
                    class_group.label,
                    class_group.school_year,
                    int(class_group.active),
                    _encode_datetime(class_group.created_at, "created_at"),
                    _encode_datetime(class_group.updated_at, "updated_at"),
                    class_group.class_id,
                ),
            )
            if cursor.rowcount != 1:
                raise IdentityStorageNotFoundError("Classe da aggiornare non trovata.")

    def list_classes(self, *, active_only: bool = False) -> list[ClassGroup]:
        where = " WHERE active = 1" if active_only else ""
        rows = self._query_all(f"SELECT * FROM classes{where} ORDER BY class_id")
        return [self._class_group(row) for row in rows]

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

    def save_external_group_mapping(self, mapping: ExternalGroupMapping) -> None:
        with self._transaction("save_external_group_mapping") as connection:
            cursor = connection.execute(
                """
                INSERT INTO external_group_mappings VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, organization_subject, group_subject) DO UPDATE SET
                    display_name = excluded.display_name
                WHERE external_group_mappings.class_id = excluded.class_id
                """,
                (
                    mapping.provider,
                    mapping.organization_subject,
                    mapping.group_subject,
                    mapping.class_id,
                    _encode_datetime(mapping.created_at, "created_at"),
                    mapping.display_name,
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
    ) -> bool:
        with self._transaction("delete_external_group_mapping") as connection:
            cursor = connection.execute(
                """
                DELETE FROM external_group_mappings
                WHERE provider = ? AND organization_subject = ? AND group_subject = ?
                """,
                (provider.lower(), organization_subject, group_subject),
            )
            return cursor.rowcount == 1

    def create_session(self, session: UserSession) -> None:
        with self._transaction("create_session") as connection:
            connection.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)",
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
                ),
            )

    def create_session_for_active_user(self, session: UserSession) -> None:
        with self._transaction("create_session_for_active_user") as connection:
            cursor = connection.execute(
                """
                INSERT INTO sessions
                SELECT ?, ?, ?, ?, ?, ?, ?
                FROM users WHERE user_id = ? AND active = 1
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
                    session.user_id,
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
        )
        with self._transaction("save_session") as connection:
            if session.revoked_at is None:
                cursor = connection.execute(
                    """
                    UPDATE sessions SET last_seen_at = ?
                    WHERE session_id = ? AND user_id = ? AND token_digest = ?
                        AND created_at = ? AND expires_at = ?
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
                        AND created_at = ? AND expires_at = ?
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

    def list_user_sessions(self, user_id: str) -> list[UserSession]:
        rows = self._query_all(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY created_at, session_id",
            (user_id,),
        )
        return [self._session(row) for row in rows]

    def revoke_user_sessions(self, user_id: str, revoked_at: datetime) -> int:
        encoded = _encode_datetime(revoked_at, "revoked_at")
        with self._transaction("revoke_user_sessions") as connection:
            stale = connection.execute(
                """
                SELECT COUNT(*) FROM sessions
                WHERE user_id = ? AND revoked_at IS NULL AND expires_at > ?
                    AND (created_at > ? OR last_seen_at > ?)
                """,
                (user_id, encoded, encoded, encoded),
            ).fetchone()[0]
            if stale:
                raise IdentityStorageConflictError(
                    "revoked_at precede la creazione o l'ultimo utilizzo di una sessione attiva."
                )
            cursor = connection.execute(
                """
                UPDATE sessions SET revoked_at = ?
                WHERE user_id = ? AND revoked_at IS NULL
                    AND created_at <= ? AND expires_at > ?
                """,
                (encoded, user_id, encoded, encoded),
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

    def save_pairing_for_active_user(self, pairing: TuiPairing) -> None:
        if pairing.user_id is None:
            raise IdentityStorageConflictError(
                "La transizione pairing richiede un utente attivo."
            )
        self._save_pairing_transition(pairing, require_active_user=True)

    def _save_pairing_transition(
        self, pairing: TuiPairing, *, require_active_user: bool
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
            active_user_sql = (
                " AND EXISTS (SELECT 1 FROM users"
                " WHERE users.user_id = ? AND users.active = 1)"
            )
            active_user_values = (pairing.user_id,)
        else:
            active_user_sql = ""
            active_user_values = ()
        placeholders = ", ".join("?" for _ in predecessors)
        with self._transaction("save_pairing") as connection:
            cursor = connection.execute(
                f"""
                UPDATE tui_pairings SET status = ?, user_id = ?, authorized_at = ?,
                    consumed_at = ?, expired_at = ?, revoked_at = ?
                WHERE pairing_id = ? AND code_digest = ? AND created_at = ? AND expires_at = ?
                    AND status IN ({placeholders}){prior_identity_sql}{active_user_sql}
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
                + active_user_values,
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM tui_pairings WHERE pairing_id = ?", (pairing.pairing_id,)
                ).fetchone()
                if exists is None:
                    raise IdentityStorageNotFoundError("Pairing da aggiornare non trovato.")
                raise IdentityStorageConflictError(
                    "Pairing modificato, transitato o associato a un utente non attivo."
                )

    def delete_expired_pairings(self, expired_before: datetime) -> int:
        encoded = _encode_datetime(expired_before, "expired_before")
        with self._transaction("delete_expired_pairings") as connection:
            cursor = connection.execute("DELETE FROM tui_pairings WHERE expires_at <= ?", (encoded,))
            return cursor.rowcount
