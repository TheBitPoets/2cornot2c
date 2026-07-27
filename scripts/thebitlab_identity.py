from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal


UserRole = Literal["admin", "teacher", "student", "pending"]
MembershipRole = Literal["teacher", "student"]
PairingStatus = Literal["pending", "authorized", "consumed", "expired", "revoked"]

USER_ROLES = frozenset({"admin", "teacher", "student", "pending"})
MEMBERSHIP_ROLES = frozenset({"teacher", "student"})
PAIRING_STATUSES = frozenset({"pending", "authorized", "consumed", "expired", "revoked"})
DIGEST_HEX_LENGTHS = {
    "sha256": 64,
    "sha512": 128,
    "hmac-sha256": 64,
    "hmac-sha512": 128,
}
SESSION_DIGEST_ALGORITHMS = frozenset({"sha256", "sha512"})
PAIRING_DIGEST_ALGORITHMS = frozenset({"hmac-sha256", "hmac-sha512"})
MAX_IDENTITY_TEXT_CHARS = 512


class IdentityDomainError(ValueError):
    """Base error for invalid identity and authorization domain data."""


class InvalidIdentityDataError(IdentityDomainError):
    """Raised when identity domain data violates a contract invariant."""


class InvalidRoleError(IdentityDomainError):
    """Raised when a user or class membership role is unsupported."""


class DuplicateExternalIdentityError(IdentityDomainError):
    """Raised when one provider subject is already linked to another user."""


class IdentityLinkConflictError(IdentityDomainError):
    """Raised when an identity linking request conflicts with existing data."""


class AccountDisabledError(IdentityDomainError):
    """Raised when a disabled account attempts an authorized operation."""


class InvalidPairingTransitionError(IdentityDomainError):
    """Raised when a one-time pairing attempts an invalid state transition."""


def _required_text(value: str, field_name: str, *, lowercase: bool = False) -> str:
    if not isinstance(value, str):
        raise InvalidIdentityDataError(f"{field_name} deve essere una stringa.")
    normalized = value.strip()
    if lowercase:
        normalized = normalized.lower()
    if not normalized:
        raise InvalidIdentityDataError(f"{field_name} obbligatorio.")
    if len(normalized) > MAX_IDENTITY_TEXT_CHARS:
        raise InvalidIdentityDataError(f"{field_name} troppo lungo.")
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise InvalidIdentityDataError(f"{field_name} contiene caratteri di controllo.")
    return normalized


def _optional_text(value: str | None, field_name: str, *, lowercase: bool = False) -> str | None:
    if value is None:
        return None
    return _required_text(value, field_name, lowercase=lowercase)


def _aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise InvalidIdentityDataError(f"{field_name} deve includere il timezone.")
    return value


def _digest(
    value: str,
    field_name: str,
    *,
    allowed_algorithms: frozenset[str],
) -> str:
    normalized = _required_text(value, field_name, lowercase=True)
    algorithm, separator, hexadecimal = normalized.partition(":")
    expected_length = DIGEST_HEX_LENGTHS.get(algorithm)
    valid_hex = hexadecimal and all(character in "0123456789abcdef" for character in hexadecimal)
    if (
        separator != ":"
        or algorithm not in allowed_algorithms
        or expected_length is None
        or len(hexadecimal) != expected_length
        or not valid_hex
    ):
        allowed = ", ".join(sorted(allowed_algorithms))
        raise InvalidIdentityDataError(
            f"{field_name} deve essere un digest valido con algoritmo {allowed}."
        )
    return normalized


@dataclass(frozen=True)
class UserAccount:
    """Provider-independent TheBitLab user account."""

    user_id: str
    display_name: str
    role: UserRole
    active: bool
    created_at: datetime
    updated_at: datetime
    primary_email: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_id", _required_text(self.user_id, "user_id"))
        object.__setattr__(self, "display_name", _required_text(self.display_name, "display_name"))
        role = _required_text(self.role, "role", lowercase=True)
        if role not in USER_ROLES:
            raise InvalidRoleError(f"Ruolo utente non supportato: {role}")
        object.__setattr__(self, "role", role)
        if not isinstance(self.active, bool):
            raise InvalidIdentityDataError("active deve essere booleano.")
        object.__setattr__(self, "created_at", _aware_datetime(self.created_at, "created_at"))
        updated_at = _aware_datetime(self.updated_at, "updated_at")
        if updated_at < self.created_at:
            raise InvalidIdentityDataError("updated_at non puo precedere created_at.")
        object.__setattr__(self, "updated_at", updated_at)
        object.__setattr__(
            self,
            "primary_email",
            _optional_text(self.primary_email, "primary_email", lowercase=True),
        )


@dataclass(frozen=True)
class ExternalIdentity:
    """External provider subject linked to one internal user."""

    user_id: str
    provider: str
    subject: str
    linked_at: datetime
    email: str | None = None
    username: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_id", _required_text(self.user_id, "user_id"))
        object.__setattr__(self, "provider", _required_text(self.provider, "provider", lowercase=True))
        object.__setattr__(self, "subject", _required_text(self.subject, "subject"))
        object.__setattr__(self, "linked_at", _aware_datetime(self.linked_at, "linked_at"))
        object.__setattr__(self, "email", _optional_text(self.email, "email", lowercase=True))
        object.__setattr__(self, "username", _optional_text(self.username, "username"))

    @property
    def provider_key(self) -> tuple[str, str]:
        """Return the stable provider identity key."""

        return (self.provider, self.subject)


@dataclass(frozen=True)
class ClassGroup:
    """Internal class independent from repository provider groups."""

    class_id: str
    label: str
    school_year: str
    active: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "class_id", _required_text(self.class_id, "class_id"))
        object.__setattr__(self, "label", _required_text(self.label, "label"))
        object.__setattr__(self, "school_year", _required_text(self.school_year, "school_year"))
        if not isinstance(self.active, bool):
            raise InvalidIdentityDataError("active deve essere booleano.")
        object.__setattr__(self, "created_at", _aware_datetime(self.created_at, "created_at"))
        updated_at = _aware_datetime(self.updated_at, "updated_at")
        if updated_at < self.created_at:
            raise InvalidIdentityDataError("updated_at non puo precedere created_at.")
        object.__setattr__(self, "updated_at", updated_at)


@dataclass(frozen=True)
class ClassMembership:
    """Internal user membership in a TheBitLab class."""

    user_id: str
    class_id: str
    role: MembershipRole
    joined_at: datetime
    source_provider: str | None = None
    source_group_subject: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_id", _required_text(self.user_id, "user_id"))
        object.__setattr__(self, "class_id", _required_text(self.class_id, "class_id"))
        role = _required_text(self.role, "role", lowercase=True)
        if role not in MEMBERSHIP_ROLES:
            raise InvalidRoleError(f"Ruolo membership non supportato: {role}")
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "joined_at", _aware_datetime(self.joined_at, "joined_at"))
        source_provider = _optional_text(self.source_provider, "source_provider", lowercase=True)
        source_group = _optional_text(self.source_group_subject, "source_group_subject")
        if (source_provider is None) != (source_group is None):
            raise InvalidIdentityDataError(
                "source_provider e source_group_subject devono essere entrambi presenti o assenti."
            )
        object.__setattr__(self, "source_provider", source_provider)
        object.__setattr__(self, "source_group_subject", source_group)


@dataclass(frozen=True)
class ExternalGroupMapping:
    """Mapping from a stable provider group/team to one internal class."""

    provider: str
    organization_subject: str
    group_subject: str
    class_id: str
    created_at: datetime
    display_name: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _required_text(self.provider, "provider", lowercase=True))
        object.__setattr__(
            self,
            "organization_subject",
            _required_text(self.organization_subject, "organization_subject"),
        )
        object.__setattr__(self, "group_subject", _required_text(self.group_subject, "group_subject"))
        object.__setattr__(self, "class_id", _required_text(self.class_id, "class_id"))
        object.__setattr__(self, "created_at", _aware_datetime(self.created_at, "created_at"))
        object.__setattr__(self, "display_name", _optional_text(self.display_name, "display_name"))

    @property
    def provider_key(self) -> tuple[str, str, str]:
        """Return the stable external group key."""

        return (self.provider, self.organization_subject, self.group_subject)


@dataclass(frozen=True)
class UserSession:
    """Persistable web session metadata without the raw bearer token."""

    session_id: str
    user_id: str
    token_digest: str
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", _required_text(self.session_id, "session_id"))
        object.__setattr__(self, "user_id", _required_text(self.user_id, "user_id"))
        object.__setattr__(
            self,
            "token_digest",
            _digest(
                self.token_digest,
                "token_digest",
                allowed_algorithms=SESSION_DIGEST_ALGORITHMS,
            ),
        )
        object.__setattr__(self, "created_at", _aware_datetime(self.created_at, "created_at"))
        expires_at = _aware_datetime(self.expires_at, "expires_at")
        last_seen_at = _aware_datetime(self.last_seen_at, "last_seen_at")
        if expires_at <= self.created_at:
            raise InvalidIdentityDataError("expires_at deve essere successivo a created_at.")
        if not self.created_at <= last_seen_at <= expires_at:
            raise InvalidIdentityDataError("last_seen_at deve essere compreso nella durata della sessione.")
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "last_seen_at", last_seen_at)
        if self.revoked_at is not None:
            revoked_at = _aware_datetime(self.revoked_at, "revoked_at")
            if not self.created_at <= revoked_at <= expires_at:
                raise InvalidIdentityDataError(
                    "revoked_at deve essere compreso nella durata della sessione."
                )
            if last_seen_at > revoked_at:
                raise InvalidIdentityDataError("last_seen_at non puo essere successivo a revoked_at.")
            object.__setattr__(self, "revoked_at", revoked_at)


@dataclass(frozen=True)
class TuiPairing:
    """Persistable TUI pairing state without the raw one-time code."""

    pairing_id: str
    code_digest: str
    status: PairingStatus
    created_at: datetime
    expires_at: datetime
    user_id: str | None = None
    authorized_at: datetime | None = None
    consumed_at: datetime | None = None
    expired_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "pairing_id", _required_text(self.pairing_id, "pairing_id"))
        object.__setattr__(
            self,
            "code_digest",
            _digest(
                self.code_digest,
                "code_digest",
                allowed_algorithms=PAIRING_DIGEST_ALGORITHMS,
            ),
        )
        status = _required_text(self.status, "status", lowercase=True)
        if status not in PAIRING_STATUSES:
            raise InvalidIdentityDataError(f"Stato pairing non supportato: {status}")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "created_at", _aware_datetime(self.created_at, "created_at"))
        expires_at = _aware_datetime(self.expires_at, "expires_at")
        if expires_at <= self.created_at:
            raise InvalidIdentityDataError("expires_at deve essere successivo a created_at.")
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "user_id", _optional_text(self.user_id, "user_id"))

        for field_name in ("authorized_at", "consumed_at", "revoked_at"):
            value = getattr(self, field_name)
            if value is None:
                continue
            normalized = _aware_datetime(value, field_name)
            if not self.created_at <= normalized <= expires_at:
                raise InvalidIdentityDataError(
                    f"{field_name} deve essere compreso nella durata del pairing."
                )
            if normalized == expires_at:
                raise InvalidIdentityDataError(
                    f"{field_name} deve precedere expires_at; alla scadenza usare expired."
                )
            object.__setattr__(self, field_name, normalized)
        if self.expired_at is not None:
            expired_at = _aware_datetime(self.expired_at, "expired_at")
            if expired_at < expires_at:
                raise InvalidIdentityDataError("expired_at non puo precedere expires_at.")
            object.__setattr__(self, "expired_at", expired_at)

        if status == "pending" and any(
            value is not None
            for value in (
                self.user_id,
                self.authorized_at,
                self.consumed_at,
                self.expired_at,
                self.revoked_at,
            )
        ):
            raise InvalidIdentityDataError(
                "Un pairing pending non puo essere associato o terminale."
            )
        if (self.user_id is None) != (self.authorized_at is None):
            raise InvalidIdentityDataError(
                "user_id e authorized_at devono essere entrambi presenti o assenti."
            )
        if self.authorized_at is not None and self.consumed_at is not None:
            if self.consumed_at < self.authorized_at:
                raise InvalidIdentityDataError("consumed_at non puo precedere authorized_at.")
        if self.authorized_at is not None and self.revoked_at is not None:
            if self.revoked_at < self.authorized_at:
                raise InvalidIdentityDataError("revoked_at non puo precedere authorized_at.")

        if status == "authorized":
            if (
                self.user_id is None
                or self.consumed_at is not None
                or self.expired_at is not None
                or self.revoked_at is not None
            ):
                raise InvalidIdentityDataError(
                    "Un pairing authorized richiede user_id/authorized_at e nessuno stato terminale."
                )
        elif status == "consumed":
            if (
                self.user_id is None
                or self.consumed_at is None
                or self.expired_at is not None
                or self.revoked_at is not None
            ):
                raise InvalidIdentityDataError(
                    "Un pairing consumed richiede autorizzazione e consumed_at soltanto."
                )
        elif status == "expired":
            if self.expired_at is None or self.consumed_at is not None or self.revoked_at is not None:
                raise InvalidIdentityDataError(
                    "Un pairing expired richiede expired_at e non puo essere consumato o revocato."
                )
        elif status == "revoked":
            if self.revoked_at is None or self.consumed_at is not None or self.expired_at is not None:
                raise InvalidIdentityDataError(
                    "Un pairing revoked richiede revoked_at e non puo essere consumato o scaduto."
                )


def authorize_pairing(pairing: TuiPairing, user_id: str, authorized_at: datetime) -> TuiPairing:
    """Move a pending pairing to authorized before its expiration."""

    if pairing.status != "pending":
        raise InvalidPairingTransitionError("Solo un pairing pending puo essere autorizzato.")
    return replace(
        pairing,
        status="authorized",
        user_id=_required_text(user_id, "user_id"),
        authorized_at=_aware_datetime(authorized_at, "authorized_at"),
    )


def consume_pairing(pairing: TuiPairing, consumed_at: datetime) -> TuiPairing:
    """Consume an authorized pairing exactly once."""

    if pairing.status != "authorized":
        raise InvalidPairingTransitionError("Solo un pairing authorized puo essere consumato.")
    return replace(
        pairing,
        status="consumed",
        consumed_at=_aware_datetime(consumed_at, "consumed_at"),
    )


def expire_pairing(pairing: TuiPairing, expired_at: datetime) -> TuiPairing:
    """Expire a pending or authorized pairing after its deadline."""

    if pairing.status not in {"pending", "authorized"}:
        raise InvalidPairingTransitionError(
            "Solo un pairing pending o authorized puo diventare expired."
        )
    return replace(
        pairing,
        status="expired",
        expired_at=_aware_datetime(expired_at, "expired_at"),
    )


def revoke_pairing(pairing: TuiPairing, revoked_at: datetime) -> TuiPairing:
    """Revoke a pending or authorized pairing before its deadline."""

    if pairing.status not in {"pending", "authorized"}:
        raise InvalidPairingTransitionError(
            "Solo un pairing pending o authorized puo diventare revoked."
        )
    return replace(
        pairing,
        status="revoked",
        revoked_at=_aware_datetime(revoked_at, "revoked_at"),
    )


def require_active_account(account: UserAccount) -> None:
    """Reject authorization for a disabled internal account."""

    if not account.active:
        raise AccountDisabledError(f"Account disabilitato: {account.user_id}")


def validate_external_identity_link(
    existing: ExternalIdentity | None,
    requested: ExternalIdentity,
) -> None:
    """Enforce unique ownership of one provider subject."""

    if existing is None:
        return
    if existing.provider_key != requested.provider_key:
        raise IdentityLinkConflictError("La verifica del linking usa un'identita provider diversa.")
    if existing.user_id != requested.user_id:
        raise DuplicateExternalIdentityError(
            f"Identita {requested.provider}:{requested.subject} gia collegata a un altro utente."
        )


def validate_external_group_mapping(
    existing: ExternalGroupMapping | None,
    requested: ExternalGroupMapping,
) -> None:
    """Reject reassignment of one provider group to a different internal class."""

    if existing is None:
        return
    if existing.provider_key != requested.provider_key:
        raise IdentityLinkConflictError("La verifica del mapping usa un gruppo provider diverso.")
    if existing.class_id != requested.class_id:
        raise IdentityLinkConflictError(
            "Il gruppo provider e gia associato a una classe TheBitLab diversa."
        )
