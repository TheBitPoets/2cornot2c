from __future__ import annotations

from datetime import datetime, timedelta
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


class IdentityStorageGenerationConflictError(IdentityStorageConflictError):
    """Raised when an immutable external-identity generation was already used."""


class IdentityStorageMappingGenerationConflictError(IdentityStorageConflictError):
    """Raised when an immutable external-group mapping generation was already used."""


class IdentityStoragePairingExpiredError(IdentityStorageConflictError):
    """Raised after atomically expiring a pairing at transaction time."""


class IdentityStorageSessionExpiredError(IdentityStorageConflictError):
    """Raised when a candidate session expires before atomic insertion."""


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

    def link_external_identity_for_active_user(
        self,
        identity: ExternalIdentity,
        *,
        expected_user_updated_at: datetime,
    ) -> None:
        """Atomically link while the active owner revision still matches."""
        ...

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
        """Atomically link while both active user and session still match."""
        ...

    def refresh_external_identity(
        self,
        identity: ExternalIdentity,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> None:
        """Refresh a link only while its active owner revision remains unchanged."""
        ...

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
        """Refresh a link while active user and session still match."""
        ...

    def read_external_identity(self, provider: str, subject: str) -> ExternalIdentity | None: ...

    def read_latest_external_identity_generation(
        self, provider: str, subject: str
    ) -> datetime | None: ...

    def list_external_identities(self, user_id: str) -> list[ExternalIdentity]: ...

    def unlink_external_identity(self, provider: str, subject: str) -> bool: ...

    def unlink_external_identity_for_active_user(
        self,
        provider: str,
        subject: str,
        user_id: str,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> bool:
        """Atomically unlink only the expected identity generation and active owner revision."""
        ...

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
        """Atomically unlink while identity, active owner, and live session match."""
        ...


class ClassDirectoryStorage(Protocol):
    """Persistence port for classes, memberships, and provider group mappings."""

    def create_class(self, class_group: ClassGroup) -> None: ...

    def read_class(self, class_id: str) -> ClassGroup | None: ...

    def save_class(
        self, class_group: ClassGroup, *, expected_updated_at: datetime
    ) -> None: ...

    def list_classes(self, *, active_only: bool = False) -> list[ClassGroup]: ...

    def save_membership(self, membership: ClassMembership) -> None: ...

    def list_user_memberships(self, user_id: str) -> list[ClassMembership]: ...

    def list_class_memberships(self, class_id: str) -> list[ClassMembership]: ...

    def delete_membership(self, user_id: str, class_id: str, role: str) -> bool: ...

    def save_external_group_mapping(
        self,
        mapping: ExternalGroupMapping,
        *,
        expected_updated_at: datetime | None,
    ) -> None: ...

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
        *,
        expected_created_at: datetime,
        expected_updated_at: datetime,
    ) -> bool: ...

    def read_latest_external_group_mapping_generation(
        self,
        provider: str,
        organization_subject: str,
        group_subject: str,
    ) -> datetime | None: ...

    def save_external_group_mapping_for_admin(
        self,
        mapping: ExternalGroupMapping,
        *,
        admin_user_id: str,
        expected_admin_updated_at: datetime,
        expected_class_updated_at: datetime,
        expected_mapping_created_at: datetime | None,
        expected_mapping_updated_at: datetime | None,
    ) -> None: ...

    def delete_external_group_mapping_for_admin(
        self,
        mapping: ExternalGroupMapping,
        *,
        admin_user_id: str,
        expected_admin_updated_at: datetime,
        expected_class_updated_at: datetime,
    ) -> bool: ...

    def revoke_github_memberships_without_identity(
        self,
        user_id: str,
        *,
        expected_user_updated_at: datetime,
        expected_memberships: tuple[ClassMembership, ...],
    ) -> None:
        """Revoke provider-owned memberships only while no GitHub link exists."""
        ...

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
        """Replace only GitHub-governed student memberships after atomic CAS validation."""
        ...

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
    ) -> None: ...


class SessionStorage(Protocol):
    """Persistence port for hashed web sessions."""

    def create_session(self, session: UserSession) -> None: ...

    def create_session_for_active_user(
        self, session: UserSession, *, expected_user_updated_at: datetime
    ) -> None:
        """Create a session only while its active owner revision remains unchanged."""
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

    def revoke_user_sessions(
        self,
        user_id: str,
        revoked_at: datetime,
        *,
        audience: str | None = None,
    ) -> int:
        """Atomically revoke active sessions, optionally limited to one audience."""
        ...

    def delete_expired_sessions(self, expired_before: datetime) -> int:
        """Delete sessions expiring at or before an explicit retention cutoff."""
        ...


class TuiPairingStorage(Protocol):
    """Persistence port for hashed one-time TUI pairing records."""

    def create_pairing(self, pairing: TuiPairing) -> None: ...

    def read_pairing(self, pairing_id: str) -> TuiPairing | None: ...

    def read_pairing_by_code_digest(self, code_digest: str) -> TuiPairing | None: ...

    def read_tui_authentication_snapshot(
        self, token_digest: str, pairing_id: str
    ) -> tuple[UserSession | None, UserAccount | None, TuiPairing | None]:
        """Read correlated TUI session, owner, and pairing in one snapshot."""
        ...

    def save_pairing(self, pairing: TuiPairing) -> None: ...

    def save_pairing_for_active_user(
        self, pairing: TuiPairing, *, expected_user_updated_at: datetime
    ) -> None:
        """Transition a pairing only while its active user revision remains unchanged."""
        ...

    def consume_pairing_and_create_session(
        self,
        pairing: TuiPairing,
        session: UserSession,
        *,
        expected_user_updated_at: datetime,
        expected_user_role: str,
    ) -> None:
        """Atomically consume an authorized pairing and create its user session."""
        ...

    def delete_expired_pairings(self, expired_before: datetime) -> int:
        """Delete pairings expiring at or before an explicit retention cutoff."""
        ...
