"""GitHub team-to-class mapping and deterministic pending-user onboarding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping, Protocol, Sequence

from scripts.thebitlab_identity import (
    ClassGroup,
    ClassMembership,
    ExternalGroupMapping,
    ExternalIdentity,
    UserAccount,
)
from scripts.thebitlab_identity_ports import (
    IdentityStorageConflictError,
    IdentityStorageMappingGenerationConflictError,
    IdentityStorageNotFoundError,
)

_MAX_GITHUB_SUBJECT = 9223372036854775807
_MAX_TEAMS = 200
_MAX_ATTEMPTS = 5


class GitHubTeamMappingError(RuntimeError):
    """Base error for team mapping and onboarding."""


class GitHubTeamDirectoryUnavailableError(GitHubTeamMappingError):
    """The external directory could not return an authoritative snapshot."""


class GitHubTeamDirectoryRejectedError(GitHubTeamMappingError):
    """The external directory returned a malformed or mismatched snapshot."""


class GitHubTeamMappingDeniedError(GitHubTeamMappingError):
    """The actor is not an active persisted administrator."""


class GitHubTeamMappingConflictError(GitHubTeamMappingError):
    """A mapping or onboarding CAS conflicted with concurrent state."""


class GitHubTeamMappingNotFoundError(GitHubTeamMappingError):
    """A required user, class, identity, or mapping does not exist."""


def _text(value: object, name: str, *, maximum: int = 512) -> str:
    if type(value) is not str:
        raise GitHubTeamDirectoryRejectedError(f"{name} non valido.")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > maximum
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in normalized)
    ):
        raise GitHubTeamDirectoryRejectedError(f"{name} non valido.")
    return normalized


def _numeric_subject(value: object, name: str) -> str:
    normalized = _text(value, name, maximum=19)
    if (
        not normalized.isascii()
        or not normalized.isdecimal()
        or normalized.startswith("0")
    ):
        raise GitHubTeamDirectoryRejectedError(f"{name} deve essere un ID numerico canonico.")
    number = int(normalized)
    if number <= 0 or number > _MAX_GITHUB_SUBJECT or str(number) != normalized:
        raise GitHubTeamDirectoryRejectedError(f"{name} fuori intervallo.")
    return normalized


def _utc(value: datetime, name: str = "clock") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise GitHubTeamDirectoryUnavailableError(f"{name} non valido.")
    return value.astimezone(timezone.utc)


def _next_generation(candidate: datetime, previous: datetime | None) -> datetime:
    try:
        if previous is not None and previous >= candidate:
            return previous + timedelta(microseconds=1)
        return candidate
    except OverflowError as error:
        raise GitHubTeamMappingConflictError("Generazioni mapping esaurite.") from error


@dataclass(frozen=True)
class GitHubTeamMembership:
    organization_subject: str
    team_subject: str
    display_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "organization_subject",
            _numeric_subject(self.organization_subject, "organization_subject"),
        )
        object.__setattr__(
            self,
            "team_subject",
            _numeric_subject(self.team_subject, "team_subject"),
        )
        if self.display_name is not None:
            object.__setattr__(self, "display_name", _text(self.display_name, "display_name"))

    @property
    def provider_key(self) -> tuple[str, str, str]:
        return ("github", self.organization_subject, self.team_subject)


@dataclass(frozen=True)
class GitHubTeamMembershipSnapshot:
    user_subject: str
    teams: tuple[GitHubTeamMembership, ...]
    captured_at: datetime
    complete: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_subject", _numeric_subject(self.user_subject, "user_subject"))
        if type(self.teams) is not tuple or len(self.teams) > _MAX_TEAMS:
            raise GitHubTeamDirectoryRejectedError("Snapshot team GitHub non valido.")
        keys = []
        for team in self.teams:
            if type(team) is not GitHubTeamMembership:
                raise GitHubTeamDirectoryRejectedError("Snapshot team GitHub non valido.")
            keys.append(team.provider_key)
        if len(keys) != len(set(keys)):
            raise GitHubTeamDirectoryRejectedError("Snapshot team GitHub contiene duplicati.")
        if self.complete is not True:
            raise GitHubTeamDirectoryRejectedError("Snapshot team GitHub non completo.")
        object.__setattr__(self, "captured_at", _utc(self.captured_at, "captured_at"))


class GitHubTeamDirectory(Protocol):
    def read_complete_memberships(self, user_subject: str) -> GitHubTeamMembershipSnapshot: ...


class FakeGitHubTeamDirectory:
    """Deterministic complete-snapshot directory for tests and local demos."""

    def __init__(
        self,
        snapshots: Mapping[str, GitHubTeamMembershipSnapshot],
        *,
        unavailable_subjects: Sequence[str] = (),
    ) -> None:
        self._snapshots = dict(snapshots)
        self._unavailable = frozenset(unavailable_subjects)

    def read_complete_memberships(self, user_subject: str) -> GitHubTeamMembershipSnapshot:
        subject = _numeric_subject(user_subject, "user_subject")
        if subject in self._unavailable:
            raise GitHubTeamDirectoryUnavailableError("Directory team GitHub non disponibile.")
        snapshot = self._snapshots.get(subject)
        if snapshot is None:
            return GitHubTeamMembershipSnapshot(subject, (), datetime.now(timezone.utc))
        return snapshot


class GitHubTeamMappingStorage(Protocol):
    def read_user(self, user_id: str) -> UserAccount | None: ...
    def read_class(self, class_id: str) -> ClassGroup | None: ...
    def list_external_identities(self, user_id: str) -> list[ExternalIdentity]: ...
    def read_external_group_mapping(
        self, provider: str, organization_subject: str, group_subject: str
    ) -> ExternalGroupMapping | None: ...
    def read_latest_external_group_mapping_generation(
        self, provider: str, organization_subject: str, group_subject: str
    ) -> datetime | None: ...
    def save_external_group_mapping_for_admin(
        self,
        mapping: ExternalGroupMapping,
        *,
        admin_user_id: str,
        expected_admin_updated_at: datetime,
        expected_class_updated_at: datetime,
        expected_mapping_created_at: datetime | None,
    ) -> None: ...
    def delete_external_group_mapping_for_admin(
        self,
        mapping: ExternalGroupMapping,
        *,
        admin_user_id: str,
        expected_admin_updated_at: datetime,
        expected_class_updated_at: datetime,
    ) -> bool: ...
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


class GitHubTeamClassMappingService:
    """Admin-only mapping management with persisted actor/class CAS."""

    def __init__(
        self,
        storage: GitHubTeamMappingStorage,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.storage = storage
        self.clock = clock

    def _admin_and_class(self, admin_user_id: str, class_id: str) -> tuple[UserAccount, ClassGroup]:
        actor = self.storage.read_user(_text(admin_user_id, "admin_user_id"))
        if actor is None or not actor.active or actor.role != "admin":
            raise GitHubTeamMappingDeniedError("Admin TheBitLab non autorizzato.")
        class_group = self.storage.read_class(_text(class_id, "class_id"))
        if class_group is None:
            raise GitHubTeamMappingNotFoundError("Classe TheBitLab non trovata.")
        if not class_group.active:
            raise GitHubTeamMappingConflictError("Classe TheBitLab non attiva.")
        return actor, class_group

    def save_mapping(
        self,
        admin_user_id: str,
        class_id: str,
        organization_subject: str,
        team_subject: str,
        *,
        display_name: str | None = None,
    ) -> ExternalGroupMapping:
        team = GitHubTeamMembership(organization_subject, team_subject, display_name)
        actor, class_group = self._admin_and_class(admin_user_id, class_id)
        existing = self.storage.read_external_group_mapping(*team.provider_key)
        if existing is not None:
            if existing.class_id != class_group.class_id:
                raise GitHubTeamMappingConflictError(
                    "Team GitHub gia associato a un'altra classe."
                )
            mapping = ExternalGroupMapping(
                *team.provider_key,
                class_group.class_id,
                existing.created_at,
                team.display_name,
            )
            try:
                self.storage.save_external_group_mapping_for_admin(
                    mapping,
                    admin_user_id=actor.user_id,
                    expected_admin_updated_at=actor.updated_at,
                    expected_class_updated_at=class_group.updated_at,
                    expected_mapping_created_at=existing.created_at,
                )
            except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
                raise GitHubTeamMappingConflictError(
                    "Mapping modificato durante il salvataggio."
                ) from error
            return mapping

        candidate = _utc(self.clock())
        for _attempt in range(_MAX_ATTEMPTS):
            previous = self.storage.read_latest_external_group_mapping_generation(
                *team.provider_key
            )
            created_at = _next_generation(candidate, previous)
            mapping = ExternalGroupMapping(
                *team.provider_key,
                class_group.class_id,
                created_at,
                team.display_name,
            )
            try:
                self.storage.save_external_group_mapping_for_admin(
                    mapping,
                    admin_user_id=actor.user_id,
                    expected_admin_updated_at=actor.updated_at,
                    expected_class_updated_at=class_group.updated_at,
                    expected_mapping_created_at=None,
                )
                return mapping
            except IdentityStorageMappingGenerationConflictError as error:
                current = self.storage.read_external_group_mapping(*team.provider_key)
                if current is not None:
                    raise GitHubTeamMappingConflictError(
                        "Mapping creato da un'altra operazione."
                    ) from error
                candidate = _next_generation(created_at, created_at)
            except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
                raise GitHubTeamMappingConflictError(
                    "Admin, classe o mapping modificati durante il salvataggio."
                ) from error
        raise GitHubTeamMappingConflictError("Impossibile riservare il mapping GitHub.")

    def delete_mapping(
        self,
        admin_user_id: str,
        organization_subject: str,
        team_subject: str,
    ) -> ExternalGroupMapping:
        team = GitHubTeamMembership(organization_subject, team_subject)
        mapping = self.storage.read_external_group_mapping(*team.provider_key)
        if mapping is None:
            raise GitHubTeamMappingNotFoundError("Mapping GitHub non trovato.")
        actor, class_group = self._admin_and_class(admin_user_id, mapping.class_id)
        try:
            removed = self.storage.delete_external_group_mapping_for_admin(
                mapping,
                admin_user_id=actor.user_id,
                expected_admin_updated_at=actor.updated_at,
                expected_class_updated_at=class_group.updated_at,
            )
        except IdentityStorageConflictError as error:
            raise GitHubTeamMappingConflictError(
                "Mapping modificato durante la rimozione."
            ) from error
        if removed is not True:
            raise GitHubTeamMappingConflictError("Mapping gia rimosso.")
        return mapping


@dataclass(frozen=True)
class GitHubPendingOnboardingResult:
    status: str
    reason: str
    membership: ClassMembership | None = None


class GitHubPendingOnboardingService:
    """Promote only one pending user with exactly one mapped GitHub team."""

    def __init__(
        self,
        storage: GitHubTeamMappingStorage,
        directory: GitHubTeamDirectory,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        max_snapshot_age: timedelta = timedelta(minutes=2),
        future_skew: timedelta = timedelta(seconds=30),
    ) -> None:
        if (
            type(max_snapshot_age) is not timedelta
            or not timedelta(seconds=1) <= max_snapshot_age <= timedelta(minutes=10)
            or type(future_skew) is not timedelta
            or not timedelta(0) <= future_skew <= timedelta(minutes=2)
        ):
            raise GitHubTeamDirectoryRejectedError("Policy freschezza snapshot non valida.")
        self.storage = storage
        self.directory = directory
        self.clock = clock
        self.max_snapshot_age = max_snapshot_age
        self.future_skew = future_skew

    def reconcile(self, user_id: str) -> GitHubPendingOnboardingResult:
        account = self.storage.read_user(_text(user_id, "user_id"))
        if account is None:
            raise GitHubTeamMappingNotFoundError("Utente TheBitLab non trovato.")
        if not account.active or account.role != "pending":
            return GitHubPendingOnboardingResult("pending", "not-eligible")
        github_identities = [
            identity
            for identity in self.storage.list_external_identities(account.user_id)
            if identity.provider == "github"
        ]
        if len(github_identities) != 1:
            return GitHubPendingOnboardingResult("pending", "github-not-linked")
        identity = github_identities[0]
        try:
            snapshot = self.directory.read_complete_memberships(identity.subject)
        except (GitHubTeamDirectoryUnavailableError, GitHubTeamDirectoryRejectedError):
            raise
        except Exception as error:
            raise GitHubTeamDirectoryUnavailableError(
                "Directory team GitHub non disponibile."
            ) from error
        if type(snapshot) is not GitHubTeamMembershipSnapshot or snapshot.user_subject != identity.subject:
            raise GitHubTeamDirectoryRejectedError("Snapshot GitHub non correlato all'utente.")
        validation_now = _utc(self.clock())
        if (
            snapshot.captured_at < identity.linked_at
            or snapshot.captured_at <= validation_now - self.max_snapshot_age
            or snapshot.captured_at > validation_now + self.future_skew
        ):
            raise GitHubTeamDirectoryRejectedError("Snapshot GitHub non fresco.")

        mapped: list[ExternalGroupMapping] = []
        for team in snapshot.teams:
            mapping = self.storage.read_external_group_mapping(*team.provider_key)
            if mapping is not None:
                mapped.append(mapping)
        if not mapped:
            return GitHubPendingOnboardingResult("pending", "no-mapped-team")
        if len(mapped) != 1:
            return GitHubPendingOnboardingResult("pending", "ambiguous-mapped-teams")
        mapping = mapped[0]
        class_group = self.storage.read_class(mapping.class_id)
        if class_group is None or not class_group.active:
            return GitHubPendingOnboardingResult("pending", "class-unavailable")
        joined_at = _next_generation(_utc(self.clock()), account.updated_at)
        membership = ClassMembership(
            account.user_id,
            class_group.class_id,
            "student",
            joined_at,
            "github",
            mapping.group_subject,
        )
        try:
            self.storage.onboard_pending_user_from_external_group(
                membership,
                expected_user_updated_at=account.updated_at,
                expected_identity_subject=identity.subject,
                expected_identity_linked_at=identity.linked_at,
                expected_mapping=mapping,
                expected_snapshot_group_keys=tuple(
                    (team.organization_subject, team.team_subject)
                    for team in snapshot.teams
                ),
                expected_snapshot_captured_at=snapshot.captured_at,
                max_snapshot_age=self.max_snapshot_age,
                future_skew=self.future_skew,
                expected_class_updated_at=class_group.updated_at,
            )
        except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
            raise GitHubTeamMappingConflictError(
                "Stato modificato durante onboarding GitHub."
            ) from error
        return GitHubPendingOnboardingResult("onboarded", "single-mapped-team", membership)
