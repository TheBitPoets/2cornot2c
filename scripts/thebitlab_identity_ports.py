from __future__ import annotations

from datetime import datetime
from typing import Protocol

from scripts.thebitlab_identity import (
    ClassGroup,
    ClassMembership,
    ExternalGroupMapping,
    ExternalIdentity,
    TuiPairing,
    UserAccount,
    UserSession,
)


class IdentityStorageError(RuntimeError):
    """Base error shared by identity persistence adapters."""


class IdentityStorageConflictError(IdentityStorageError):
    """Raised when a persistence invariant or compare-and-swap fails."""


class IdentityStorageNotFoundError(IdentityStorageError):
    """Raised when an update targets a missing identity record."""


class IdentityStorageCorruptionError(IdentityStorageError):
    """Raised when persisted data cannot satisfy the domain contracts."""


class UserDirectoryStorage(Protocol):
    """Persistence port for internal users and linked external identities."""

    def create_user(self, user: UserAccount) -> None: ...

    def provision_user_with_identity(
        self, user: UserAccount, identity: ExternalIdentity
    ) -> None:
        """Atomically create one user and its first provider identity."""
        ...

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def save_user(self, user: UserAccount, *, expected_updated_at: datetime) -> None:
        """Update a user only when the persisted revision matches the expected instant."""
        ...

    def list_users(self) -> list[UserAccount]: ...

    def link_external_identity(self, identity: ExternalIdentity) -> None: ...

    def refresh_external_identity(
        self,
        identity: ExternalIdentity,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> None:
        """Refresh a link only while its active owner revision remains unchanged."""
        ...

    def read_external_identity(self, provider: str, subject: str) -> ExternalIdentity | None: ...

    def list_external_identities(self, user_id: str) -> list[ExternalIdentity]: ...

    def unlink_external_identity(self, provider: str, subject: str) -> bool: ...


class ClassDirectoryStorage(Protocol):
    """Persistence port for classes, memberships, and provider group mappings."""

    def create_class(self, class_group: ClassGroup) -> None: ...

    def read_class(self, class_id: str) -> ClassGroup | None: ...

    def save_class(self, class_group: ClassGroup) -> None: ...

    def list_classes(self, *, active_only: bool = False) -> list[ClassGroup]: ...

    def save_membership(self, membership: ClassMembership) -> None: ...

    def list_user_memberships(self, user_id: str) -> list[ClassMembership]: ...

    def list_class_memberships(self, class_id: str) -> list[ClassMembership]: ...

    def delete_membership(self, user_id: str, class_id: str, role: str) -> bool: ...

    def save_external_group_mapping(self, mapping: ExternalGroupMapping) -> None: ...

    def read_external_group_mapping(
        self,
        provider: str,
        organization_subject: str,
        group_subject: str,
    ) -> ExternalGroupMapping | None: ...

    def list_external_group_mappings(self, class_id: str | None = None) -> list[ExternalGroupMapping]: ...

    def delete_external_group_mapping(
        self,
        provider: str,
        organization_subject: str,
        group_subject: str,
    ) -> bool: ...


class SessionStorage(Protocol):
    """Persistence port for hashed web sessions."""

    def create_session(self, session: UserSession) -> None: ...

    def create_session_for_active_user(self, session: UserSession) -> None:
        """Atomically create a session only while its owner is active."""
        ...

    def read_session(self, session_id: str) -> UserSession | None: ...

    def read_session_by_token_digest(self, token_digest: str) -> UserSession | None: ...

    def save_session(self, session: UserSession) -> None: ...

    def save_session_for_active_user(
        self, session: UserSession, *, expected_user_updated_at: datetime
    ) -> None:
        """Touch an active session only while its owner revision remains unchanged."""
        ...

    def list_user_sessions(self, user_id: str) -> list[UserSession]: ...

    def revoke_user_sessions(self, user_id: str, revoked_at: datetime) -> int:
        """Atomically revoke active sessions, rejecting a stale revocation instant."""
        ...

    def delete_expired_sessions(self, expired_before: datetime) -> int:
        """Delete sessions expiring at or before an explicit retention cutoff."""
        ...


class TuiPairingStorage(Protocol):
    """Persistence port for hashed one-time TUI pairing records."""

    def create_pairing(self, pairing: TuiPairing) -> None: ...

    def read_pairing(self, pairing_id: str) -> TuiPairing | None: ...

    def read_pairing_by_code_digest(self, code_digest: str) -> TuiPairing | None: ...

    def save_pairing(self, pairing: TuiPairing) -> None: ...

    def save_pairing_for_active_user(self, pairing: TuiPairing) -> None:
        """Atomically transition a pairing only while its linked user is active."""
        ...

    def delete_expired_pairings(self, expired_before: datetime) -> int:
        """Delete pairings expiring at or before an explicit retention cutoff."""
        ...
