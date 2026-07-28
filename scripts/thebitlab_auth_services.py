from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import string
import unicodedata
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping, Protocol

from scripts.thebitlab_identity import (
    ExternalIdentity,
    TuiPairing,
    UserAccount,
    UserSession,
    authorize_pairing,
    consume_pairing,
    expire_pairing,
    require_active_account,
    revoke_pairing,
)
from scripts.thebitlab_identity_ports import (
    IdentityStorageConflictError,
    IdentityStorageGenerationConflictError,
    IdentityStorageNotFoundError,
    IdentityStoragePairingExpiredError,
    IdentityStorageSessionExpiredError,
)


_MAX_ATTEMPTS = 5
_PAIRING_ALPHABET = string.ascii_uppercase + string.digits
_SESSION_BEARER_RE = re.compile(r"^[A-Za-z0-9_-]{32,1024}$")


class AuthApplicationError(RuntimeError):
    """Base error for provider-independent authentication workflows."""


class ProviderAuthenticationError(AuthApplicationError):
    """Raised when a provider cannot authenticate an opaque credential."""


class ProviderProtocolError(AuthApplicationError):
    """Raised when a provider adapter returns an invalid assertion."""


class OnboardingNotAllowedError(AuthApplicationError):
    """Raised when an unknown provider identity cannot create an internal user."""


class InvalidCredentialError(AuthApplicationError):
    """Raised for an unknown, expired or revoked application credential."""


class ConcurrentStateChangeError(AuthApplicationError):
    """Raised when a security state changes during an application operation."""


class CredentialGenerationError(AuthApplicationError):
    """Raised when generators repeatedly produce colliding credentials."""


class ExternalIdentityLinkConflictError(AuthApplicationError):
    """Raised when an external account is linked to an incompatible owner."""


class ExternalIdentityNotLinkedError(AuthApplicationError):
    """Raised when an expected external account link does not exist."""


class PairingStateError(AuthApplicationError):
    """Raised when a pairing is not in the state required by an operation."""


class PairingExpiredError(PairingStateError):
    """Raised when a pairing has reached its exclusive expiration instant."""


def _required_text(value: str, field_name: str, *, lowercase: bool = False) -> str:
    if type(value) is not str:
        raise ProviderProtocolError(f"{field_name} deve essere una stringa primitiva.")
    normalized = value.strip()
    if lowercase:
        normalized = normalized.lower()
    if not normalized or len(normalized) > 512:
        raise ProviderProtocolError(f"{field_name} non valido.")
    if any(
        unicodedata.category(character).startswith("C")
        for character in normalized
    ):
        raise ProviderProtocolError(
            f"{field_name} contiene caratteri Unicode non sicuri."
        )
    return normalized


def _optional_text(value: str | None, field_name: str, *, lowercase: bool = False) -> str | None:
    if value is None:
        return None
    return _required_text(value, field_name, lowercase=lowercase)


def _utc(value: datetime, field_name: str = "now") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise AuthApplicationError(f"{field_name} deve includere il timezone.")
    return value.astimezone(timezone.utc)


def _positive_ttl(value: timedelta, field_name: str) -> timedelta:
    if not isinstance(value, timedelta) or value <= timedelta(0):
        raise AuthApplicationError(f"{field_name} deve essere positivo.")
    return value


def _generated_text(value: str, field_name: str, *, minimum_length: int = 1) -> str:
    try:
        normalized = _required_text(value, field_name)
    except ProviderProtocolError as error:
        raise CredentialGenerationError(f"{field_name} generato non valido.") from error
    if normalized != value or len(normalized) < minimum_length:
        raise CredentialGenerationError(f"{field_name} generato non valido.")
    return normalized


def valid_session_bearer(raw_token: object) -> bool:
    """Return whether a generated bearer is safe for HTTP cookie/header transport."""
    return type(raw_token) is str and _SESSION_BEARER_RE.fullmatch(raw_token) is not None


def session_token_digest(raw_token: str) -> str:
    """Digest one high-entropy bearer token without retaining the raw value."""

    token = None
    encoded = None
    try:
        if (
            type(raw_token) is not str
            or not raw_token
            or len(raw_token) > 512
            or raw_token != raw_token.strip()
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in raw_token
            )
        ):
            raise CredentialGenerationError(
                "Il token di sessione generato non e valido."
            )
        token = raw_token
        if len(token) < 32:
            raise CredentialGenerationError(
                "Il token di sessione generato non e valido."
            )
        try:
            encoded = token.encode("utf-8")
        except UnicodeError:
            raise CredentialGenerationError(
                "Il token di sessione generato non e valido."
            ) from None
        return "sha256:" + hashlib.sha256(encoded).hexdigest()
    finally:
        raw_token = None
        token = None
        encoded = None


def pairing_code_digest(raw_code: str, pepper: bytes) -> str:
    """Key one low-entropy pairing code with a server-side pepper."""

    code = None
    encoded = None
    try:
        if (
            type(raw_code) is not str
            or not raw_code
            or len(raw_code) > 512
            or raw_code != raw_code.strip()
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in raw_code
            )
        ):
            raise CredentialGenerationError(
                "Il codice pairing generato non e valido."
            )
        code = raw_code
        if type(pepper) is not bytes or len(pepper) < 32:
            raise AuthApplicationError(
                "Il pepper pairing deve contenere almeno 32 byte."
            )
        try:
            encoded = code.encode("utf-8")
        except UnicodeError:
            raise CredentialGenerationError(
                "Il codice pairing generato non e valido."
            ) from None
        return "hmac-sha256:" + hmac.new(
            pepper, encoded, hashlib.sha256
        ).hexdigest()
    finally:
        raw_code = None
        code = None
        encoded = None
        pepper = None


def _session_digest_for_verification(raw_token: str) -> str:
    failed = False
    try:
        digest = session_token_digest(raw_token)
    except AuthApplicationError:
        failed = True
        digest = ""
    raw_token = None
    if failed:
        raise InvalidCredentialError("Sessione non valida.")
    return digest


def _pairing_digest_for_verification(raw_code: str, pepper: bytes) -> str:
    failed = False
    try:
        digest = pairing_code_digest(raw_code, pepper)
    except AuthApplicationError:
        failed = True
        digest = ""
    raw_code = None
    pepper = None
    if failed:
        raise InvalidCredentialError("Pairing non valido.")
    return digest


@dataclass(frozen=True)
class FederatedIdentityAssertion:
    """Normalized result produced only after a provider authenticates its subject."""

    provider: str
    subject: str
    display_name: str
    email: str | None = None
    email_verified: bool = False
    username: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", _required_text(self.provider, "provider", lowercase=True))
        object.__setattr__(self, "subject", _required_text(self.subject, "subject"))
        object.__setattr__(self, "display_name", _required_text(self.display_name, "display_name"))
        object.__setattr__(self, "email", _optional_text(self.email, "email", lowercase=True))
        object.__setattr__(self, "username", _optional_text(self.username, "username"))
        if not isinstance(self.email_verified, bool):
            raise ProviderProtocolError("email_verified deve essere booleano.")
        if self.email is None and self.email_verified:
            raise ProviderProtocolError("email_verified richiede email.")


class FederatedIdentityProvider(Protocol):
    """Adapter port that turns an opaque provider credential into an assertion."""

    provider_name: str

    def authenticate(self, credential: str) -> FederatedIdentityAssertion: ...


class FakeFederatedIdentityProvider:
    """Deterministic provider adapter for application tests and local demos."""

    def __init__(
        self,
        provider_name: str,
        assertions: Mapping[str, FederatedIdentityAssertion],
    ) -> None:
        self.provider_name = _required_text(provider_name, "provider_name", lowercase=True)
        self._assertions = dict(assertions)

    def authenticate(self, credential: str) -> FederatedIdentityAssertion:
        if type(credential) is not str:
            raise ProviderAuthenticationError("Credenziale provider non valida.")
        missing = object()
        assertion = self._assertions.get(credential, missing)
        if assertion is missing:
            raise ProviderAuthenticationError("Credenziale provider non valida.")
        if assertion.provider != self.provider_name:
            raise ProviderProtocolError("Il provider ha restituito un'assertion con issuer diverso.")
        return assertion


class FederatedIdentityApplicationStorage(Protocol):
    """Minimum persistence capabilities required by FederatedIdentityService."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def read_external_identity(
        self, provider: str, subject: str
    ) -> ExternalIdentity | None: ...

    def refresh_external_identity(
        self,
        identity: ExternalIdentity,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> None: ...

    def provision_user_with_identity(
        self, user: UserAccount, identity: ExternalIdentity
    ) -> None: ...


class ExternalIdentityLinkApplicationStorage(Protocol):
    """Transactional persistence required by authenticated account linking."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def read_external_identity(
        self, provider: str, subject: str
    ) -> ExternalIdentity | None: ...

    def read_latest_external_identity_generation(
        self, provider: str, subject: str
    ) -> datetime | None: ...

    def list_external_identities(self, user_id: str) -> list[ExternalIdentity]: ...

    def link_external_identity_for_active_user(
        self,
        identity: ExternalIdentity,
        *,
        expected_user_updated_at: datetime,
    ) -> None: ...

    def link_external_identity_for_active_session(
        self,
        identity: ExternalIdentity,
        *,
        expected_user_updated_at: datetime,
        expected_session_id: str,
        expected_session_token_digest: str,
        expected_session_created_at: datetime,
        expected_session_valid_at: datetime,
    ) -> None: ...

    def refresh_external_identity(
        self,
        identity: ExternalIdentity,
        *,
        expected_linked_at: datetime,
        expected_user_updated_at: datetime,
    ) -> None: ...

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
    ) -> None: ...

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
    ) -> bool: ...


class SessionApplicationStorage(Protocol):
    """Minimum persistence capabilities required by SessionService."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def create_session_for_active_user(
        self, session: UserSession, *, expected_user_updated_at: datetime
    ) -> None: ...

    def read_session_by_token_digest(self, token_digest: str) -> UserSession | None: ...

    def read_tui_authentication_snapshot(
        self, token_digest: str, pairing_id: str
    ) -> tuple[UserSession | None, UserAccount | None, TuiPairing | None]: ...

    def save_session(self, session: UserSession) -> None: ...

    def save_session_for_active_user(
        self, session: UserSession, *, expected_user_updated_at: datetime
    ) -> None: ...

    def revoke_user_sessions(
        self, user_id: str, revoked_at: datetime, *, audience: str | None = None
    ) -> int: ...


class PairingApplicationStorage(Protocol):
    """Minimum persistence capabilities required by PairingService."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def create_pairing(self, pairing: TuiPairing) -> None: ...

    def read_pairing(self, pairing_id: str) -> TuiPairing | None: ...

    def read_pairing_by_code_digest(self, code_digest: str) -> TuiPairing | None: ...

    def read_tui_authentication_snapshot(
        self, token_digest: str, pairing_id: str
    ) -> tuple[UserSession | None, UserAccount | None, TuiPairing | None]: ...

    def save_pairing(self, pairing: TuiPairing) -> None: ...

    def save_pairing_for_active_user(
        self, pairing: TuiPairing, *, expected_user_updated_at: datetime
    ) -> None: ...

    def consume_pairing_and_create_session(
        self,
        pairing: TuiPairing,
        session: UserSession,
        *,
        expected_user_updated_at: datetime,
        expected_user_role: str,
    ) -> None: ...


@dataclass(frozen=True)
class IssuedSession:
    session: UserSession
    bearer_token: str = field(repr=False, compare=False)


@dataclass(frozen=True)
class AuthenticatedSession:
    session: UserSession
    user: UserAccount


@dataclass(frozen=True)
class IssuedPairing:
    pairing: TuiPairing
    code: str = field(repr=False, compare=False)


class FederatedIdentityService:
    """Resolve authenticated provider subjects to stable internal users."""

    def __init__(
        self,
        storage: FederatedIdentityApplicationStorage,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        user_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
        onboarding_providers: frozenset[str] = frozenset({"google"}),
    ) -> None:
        self.storage = storage
        self.clock = clock
        self.user_id_factory = user_id_factory
        self.onboarding_providers = frozenset(value.strip().lower() for value in onboarding_providers)

    def authenticate(
        self,
        provider: FederatedIdentityProvider,
        credential: str,
    ) -> UserAccount:
        provider_failed = False
        assertion_echoed_credential = False
        try:
            expected_provider = _required_text(
                provider.provider_name, "provider_name", lowercase=True
            )
            assertion = provider.authenticate(credential)
            if type(assertion) is FederatedIdentityAssertion and type(credential) is str:
                claims = (
                    assertion.provider,
                    assertion.subject,
                    assertion.display_name,
                    assertion.email,
                    assertion.username,
                )
                assertion_echoed_credential = any(
                    type(claim) is str and hmac.compare_digest(claim, credential)
                    for claim in claims
                )
                claims = None
        except Exception:
            # Raise only after leaving except, so __context__ cannot retain credentials.
            provider_failed = True
            expected_provider = ""
            assertion = None
        # Traceback collectors may capture frame locals even without cause/context.
        credential = None
        provider = None
        if provider_failed:
            raise ProviderAuthenticationError("Autenticazione provider non riuscita.")
        if assertion_echoed_credential:
            assertion = None
            expected_provider = None
            raise ProviderProtocolError(
                "Il provider ha restituito una credenziale dentro l'assertion."
            )
        try:
            normalized_assertion = self._normalize_assertion(assertion)
        finally:
            assertion = None
        if normalized_assertion.provider != expected_provider:
            normalized_assertion = None
            expected_provider = None
            raise ProviderProtocolError("Assertion e provider adapter non coincidono.")
        return self._resolve_normalized(normalized_assertion)

    def resolve(self, assertion: FederatedIdentityAssertion) -> UserAccount:
        try:
            normalized = self._normalize_assertion(assertion)
        finally:
            assertion = None
        return self._resolve_normalized(normalized)

    @staticmethod
    def _normalize_assertion(assertion: object) -> FederatedIdentityAssertion:
        if type(assertion) is not FederatedIdentityAssertion:
            assertion = None
            raise ProviderProtocolError("Il provider non ha restituito un'assertion valida.")
        assertion_failed = False
        try:
            normalized = FederatedIdentityAssertion(
                provider=assertion.provider,
                subject=assertion.subject,
                display_name=assertion.display_name,
                email=assertion.email,
                email_verified=assertion.email_verified,
                username=assertion.username,
            )
        except Exception:
            assertion_failed = True
            normalized = None
        if assertion_failed or normalized is None:
            assertion = None
            raise ProviderProtocolError(
                "Il provider non ha restituito un'assertion valida."
            )
        return normalized

    def _resolve_normalized(self, assertion: FederatedIdentityAssertion) -> UserAccount:
        now = _utc(self.clock())
        existing = self.storage.read_external_identity(assertion.provider, assertion.subject)
        if existing is not None:
            return self._resolve_existing(assertion, existing)

        if (
            assertion.provider not in self.onboarding_providers
            or assertion.email is None
            or not assertion.email_verified
        ):
            raise OnboardingNotAllowedError(
                "L'identita sconosciuta non soddisfa la policy di onboarding."
            )

        linked_at = now
        for _user_attempt in range(_MAX_ATTEMPTS):
            user_id = _generated_text(self.user_id_factory(), "user_id")
            account = UserAccount(
                user_id=user_id,
                display_name=assertion.display_name,
                role="pending",
                active=True,
                created_at=now,
                updated_at=now,
                primary_email=assertion.email,
            )
            for _generation_attempt in range(_MAX_ATTEMPTS):
                identity = ExternalIdentity(
                    user_id=user_id,
                    provider=assertion.provider,
                    subject=assertion.subject,
                    linked_at=linked_at,
                    email=assertion.email,
                    username=assertion.username,
                )
                try:
                    self.storage.provision_user_with_identity(account, identity)
                    return account
                except IdentityStorageGenerationConflictError as error:
                    winner = self.storage.read_external_identity(
                        assertion.provider, assertion.subject
                    )
                    if winner is not None:
                        return self._resolve_existing(assertion, winner)
                    try:
                        linked_at += timedelta(microseconds=1)
                    except OverflowError:
                        raise ConcurrentStateChangeError(
                            "Generazione identita esterna esaurita."
                        ) from error
                except IdentityStorageConflictError:
                    winner = self.storage.read_external_identity(
                        assertion.provider, assertion.subject
                    )
                    if winner is not None:
                        return self._resolve_existing(assertion, winner)
                    break
            else:
                raise ConcurrentStateChangeError(
                    "Generazione identita esterna modificata ripetutamente."
                )
        raise CredentialGenerationError("Impossibile generare un user_id interno univoco.")

    def _resolve_existing(
        self,
        assertion: FederatedIdentityAssertion,
        existing: ExternalIdentity,
    ) -> UserAccount:
        account = self.storage.read_user(existing.user_id)
        if account is None:
            raise ConcurrentStateChangeError("Identita collegata a un utente inesistente.")
        require_active_account(account)
        try:
            self.storage.refresh_external_identity(
                ExternalIdentity(
                    user_id=account.user_id,
                    provider=assertion.provider,
                    subject=assertion.subject,
                    linked_at=existing.linked_at,
                    email=assertion.email,
                    username=assertion.username,
                ),
                expected_linked_at=existing.linked_at,
                expected_user_updated_at=account.updated_at,
            )
        except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
            current_account = self.storage.read_user(account.user_id)
            if current_account is None:
                raise ConcurrentStateChangeError(
                    "Utente rimosso durante l'autenticazione."
                ) from error
            require_active_account(current_account)
            if current_account.updated_at != account.updated_at:
                raise ConcurrentStateChangeError(
                    "Utente modificato durante l'autenticazione."
                ) from error
            current = self.storage.read_external_identity(
                assertion.provider, assertion.subject
            )
            if current is None or current.user_id != account.user_id:
                raise ConcurrentStateChangeError(
                    "Identita ricollegata durante l'autenticazione."
                ) from error
            raise ConcurrentStateChangeError(
                "Identita modificata durante l'autenticazione."
            ) from error
        return account


class ExternalIdentityLinkService:
    """Link or unlink one provider account for an already-authenticated user."""

    def __init__(
        self,
        storage: ExternalIdentityLinkApplicationStorage,
        *,
        expected_provider: str,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.storage = storage
        self.expected_provider = _required_text(
            expected_provider, "expected_provider", lowercase=True
        )
        self.clock = clock

    def link(
        self,
        user_id: str,
        assertion: FederatedIdentityAssertion,
        *,
        expected_session: UserSession | None = None,
        expected_user_updated_at: datetime | None = None,
    ) -> ExternalIdentity:
        normalized_user_id = _required_text(user_id, "user_id")
        try:
            normalized = FederatedIdentityService._normalize_assertion(assertion)
        finally:
            assertion = None
        if normalized.provider != self.expected_provider:
            normalized = None
            raise ProviderProtocolError("Provider account linking non valido.")
        account = self.storage.read_user(normalized_user_id)
        if account is None:
            normalized = None
            raise InvalidCredentialError("Utente autenticato non valido.")
        require_active_account(account)
        if (
            expected_session is not None
            and (
                type(expected_session) is not UserSession
                or expected_session.user_id != account.user_id
            )
        ):
            normalized = None
            expected_session = None
            raise InvalidCredentialError("Sessione autenticata non valida.")
        operation_now = _utc(self.clock())
        if expected_user_updated_at is not None:
            expected_revision = _utc(expected_user_updated_at)
            if account.updated_at != expected_revision:
                normalized = None
                raise ConcurrentStateChangeError(
                    "Utente modificato durante il collegamento."
                )
        else:
            expected_revision = account.updated_at
        provider_links = [
            identity
            for identity in self.storage.list_external_identities(account.user_id)
            if identity.provider == self.expected_provider
        ]
        if len(provider_links) > 1:
            normalized = None
            raise ConcurrentStateChangeError(
                "Piu account dello stesso provider risultano collegati."
            )
        winner = self.storage.read_external_identity(
            self.expected_provider, normalized.subject
        )
        if winner is not None and winner.user_id != account.user_id:
            normalized = None
            raise ExternalIdentityLinkConflictError(
                "Account provider gia collegato a un altro utente."
            )
        if provider_links and provider_links[0].subject != normalized.subject:
            normalized = None
            raise ExternalIdentityLinkConflictError(
                "Un altro account dello stesso provider e gia collegato."
            )
        if winner is not None:
            refreshed = ExternalIdentity(
                user_id=account.user_id,
                provider=self.expected_provider,
                subject=normalized.subject,
                linked_at=winner.linked_at,
                email=normalized.email,
                username=normalized.username,
            )
            try:
                if expected_session is None:
                    self.storage.refresh_external_identity(
                        refreshed,
                        expected_linked_at=winner.linked_at,
                        expected_user_updated_at=expected_revision,
                    )
                else:
                    self.storage.refresh_external_identity_for_active_session(
                        refreshed,
                        expected_linked_at=winner.linked_at,
                        expected_user_updated_at=expected_revision,
                        expected_session_id=expected_session.session_id,
                        expected_session_token_digest=expected_session.token_digest,
                        expected_session_created_at=expected_session.created_at,
                        expected_session_valid_at=operation_now,
                    )
            except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
                raise ConcurrentStateChangeError(
                    "Account provider modificato durante il collegamento."
                ) from error
            return refreshed

        linked_at = operation_now
        latest_generation = self.storage.read_latest_external_identity_generation(
            self.expected_provider, normalized.subject
        )
        try:
            if latest_generation is not None and latest_generation >= linked_at:
                linked_at = latest_generation + timedelta(microseconds=1)
        except OverflowError as error:
            raise ConcurrentStateChangeError(
                "Generazione link provider esaurita."
            ) from error
        for _attempt in range(_MAX_ATTEMPTS):
            identity = ExternalIdentity(
                user_id=account.user_id,
                provider=self.expected_provider,
                subject=normalized.subject,
                linked_at=linked_at,
                email=normalized.email,
                username=normalized.username,
            )
            try:
                if expected_session is None:
                    self.storage.link_external_identity_for_active_user(
                        identity,
                        expected_user_updated_at=expected_revision,
                    )
                else:
                    self.storage.link_external_identity_for_active_session(
                        identity,
                        expected_user_updated_at=expected_revision,
                        expected_session_id=expected_session.session_id,
                        expected_session_token_digest=expected_session.token_digest,
                        expected_session_created_at=expected_session.created_at,
                        expected_session_valid_at=operation_now,
                    )
                return identity
            except IdentityStorageGenerationConflictError:
                current = self.storage.read_external_identity(
                    self.expected_provider, normalized.subject
                )
                if current is not None:
                    if current.user_id == account.user_id:
                        return self.link(
                            account.user_id,
                            normalized,
                            expected_session=expected_session,
                            expected_user_updated_at=expected_revision,
                        )
                    raise ExternalIdentityLinkConflictError(
                        "Account provider gia collegato a un altro utente."
                    )
                latest_generation = self.storage.read_latest_external_identity_generation(
                    self.expected_provider, normalized.subject
                )
                try:
                    if latest_generation is not None and latest_generation >= linked_at:
                        linked_at = latest_generation + timedelta(microseconds=1)
                    else:
                        linked_at += timedelta(microseconds=1)
                except OverflowError as error:
                    raise ConcurrentStateChangeError(
                        "Generazione link provider esaurita."
                    ) from error
            except IdentityStorageConflictError as error:
                current = self.storage.read_external_identity(
                    self.expected_provider, normalized.subject
                )
                if current is not None and current.user_id != account.user_id:
                    raise ExternalIdentityLinkConflictError(
                        "Account provider gia collegato a un altro utente."
                    ) from error
                raise ConcurrentStateChangeError(
                    "Utente o account modificato durante il collegamento."
                ) from error
        raise ConcurrentStateChangeError(
            "Impossibile riservare una generazione link provider."
        )

    def unlink(
        self,
        user_id: str,
        *,
        expected_session: UserSession,
    ) -> ExternalIdentity:
        normalized_user_id = _required_text(user_id, "user_id")
        account = self.storage.read_user(normalized_user_id)
        if account is None:
            raise InvalidCredentialError("Utente autenticato non valido.")
        require_active_account(account)
        if (
            type(expected_session) is not UserSession
            or expected_session.user_id != account.user_id
        ):
            expected_session = None
            raise InvalidCredentialError("Sessione autenticata non valida.")
        operation_now = _utc(self.clock())
        provider_links = [
            identity
            for identity in self.storage.list_external_identities(account.user_id)
            if identity.provider == self.expected_provider
        ]
        if not provider_links:
            raise ExternalIdentityNotLinkedError(
                "Nessun account provider collegato."
            )
        if len(provider_links) != 1:
            raise ConcurrentStateChangeError(
                "Stato account provider ambiguo."
            )
        identity = provider_links[0]
        try:
            removed = self.storage.unlink_external_identity_for_active_session(
                identity.provider,
                identity.subject,
                identity.user_id,
                expected_linked_at=identity.linked_at,
                expected_user_updated_at=account.updated_at,
                expected_session_id=expected_session.session_id,
                expected_session_token_digest=expected_session.token_digest,
                expected_session_created_at=expected_session.created_at,
                expected_session_valid_at=operation_now,
            )
        except IdentityStorageConflictError as error:
            raise ConcurrentStateChangeError(
                "Account provider modificato durante lo scollegamento."
            ) from error
        if removed is not True:
            raise ConcurrentStateChangeError(
                "Account provider rimosso durante lo scollegamento."
            )
        return identity


class SessionService:
    """Issue and validate high-entropy application sessions."""

    def __init__(
        self,
        storage: SessionApplicationStorage,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        ttl: timedelta = timedelta(hours=8),
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
        audience: str = "web",
    ) -> None:
        self._storage = storage
        self.clock = clock
        self.ttl = _positive_ttl(ttl, "ttl sessione")
        normalized_audience = _required_text(audience, "audience", lowercase=True)
        if normalized_audience not in {"web", "tui"}:
            raise AuthApplicationError("Audience sessione non valida.")
        self._audience = normalized_audience
        self.token_factory = token_factory
        self.session_id_factory = session_id_factory

    @property
    def storage(self) -> SessionApplicationStorage:
        return self._storage

    @property
    def audience(self) -> str:
        return self._audience

    def issue(self, user_id: str) -> IssuedSession:
        if self.audience != "web":
            raise AuthApplicationError(
                "Le sessioni TUI possono essere emesse soltanto dal pairing atomico."
            )
        account = self.storage.read_user(user_id)
        if account is None:
            raise InvalidCredentialError("Utente non disponibile.")
        require_active_account(account)
        now = _utc(self.clock())
        for _attempt in range(_MAX_ATTEMPTS):
            raw_token = self.token_factory()
            try:
                digest_failed = False
                try:
                    digest = session_token_digest(raw_token)
                except AuthApplicationError:
                    digest_failed = True
                    digest = ""
                if digest_failed:
                    raise CredentialGenerationError(
                        "Token di sessione generato non valido."
                    )
                session = UserSession(
                    session_id=_generated_text(self.session_id_factory(), "session_id"),
                    user_id=account.user_id,
                    token_digest=digest,
                    created_at=now,
                    expires_at=now + self.ttl,
                    last_seen_at=now,
                    audience=self.audience,
                )
                try:
                    self.storage.create_session_for_active_user(
                        session, expected_user_updated_at=account.updated_at
                    )
                except IdentityStorageConflictError as error:
                    current_account = self.storage.read_user(account.user_id)
                    if current_account is None:
                        raise InvalidCredentialError("Utente non disponibile.")
                    require_active_account(current_account)
                    if current_account.updated_at != account.updated_at:
                        raise ConcurrentStateChangeError(
                            "Utente modificato durante l'emissione della sessione."
                        ) from error
                    continue
                return IssuedSession(session, raw_token)
            finally:
                raw_token = None
        raise CredentialGenerationError("Impossibile generare una sessione univoca.")

    def authenticate(self, bearer_token: str) -> AuthenticatedSession:
        try:
            digest = _session_digest_for_verification(bearer_token)
        finally:
            bearer_token = None
        session = self.storage.read_session_by_token_digest(digest)
        now = _utc(self.clock())
        for _attempt in range(_MAX_ATTEMPTS):
            session, account = self._require_valid(session, digest, now)
            touched = replace(session, last_seen_at=max(session.last_seen_at, now))
            try:
                self.storage.save_session_for_active_user(
                    touched, expected_user_updated_at=account.updated_at
                )
            except (IdentityStorageConflictError, IdentityStorageNotFoundError):
                session = self.storage.read_session_by_token_digest(digest)
                continue
            return AuthenticatedSession(touched, account)
        raise ConcurrentStateChangeError(
            "Sessione o utente modificati ripetutamente durante l'autenticazione."
        )

    def _require_valid(
        self,
        session: UserSession | None,
        digest: str,
        now: datetime,
    ) -> tuple[UserSession, UserAccount]:
        if (
            session is None
            or session.audience != self.audience
            or not hmac.compare_digest(session.token_digest, digest)
        ):
            raise InvalidCredentialError("Sessione non valida.")
        if now < session.last_seen_at:
            raise ConcurrentStateChangeError("Clock anteriore all'ultimo utilizzo della sessione.")
        if now < session.created_at or now >= session.expires_at or session.revoked_at is not None:
            raise InvalidCredentialError("Sessione non valida.")
        account = self.storage.read_user(session.user_id)
        if account is None:
            raise InvalidCredentialError("Sessione non valida.")
        require_active_account(account)
        return session, account

    def revoke(self, bearer_token: str) -> bool:
        try:
            digest = _session_digest_for_verification(bearer_token)
        finally:
            bearer_token = None
        session = self.storage.read_session_by_token_digest(digest)
        now = _utc(self.clock())
        if (
            session is None
            or session.audience != self.audience
            or session.revoked_at is not None
            or not hmac.compare_digest(session.token_digest, digest)
        ):
            return False
        if now < session.created_at or now >= session.expires_at:
            return False
        if now < session.last_seen_at:
            raise ConcurrentStateChangeError("Clock anteriore all'ultimo utilizzo della sessione.")
        try:
            self.storage.save_session(replace(session, revoked_at=now))
        except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
            current = self.storage.read_session_by_token_digest(digest)
            if current is None or current.revoked_at is not None:
                return False
            raise ConcurrentStateChangeError(
                "Sessione modificata durante la revoca."
            ) from error
        return True

    def revoke_all(self, user_id: str) -> int:
        try:
            return self.storage.revoke_user_sessions(
                user_id, _utc(self.clock()), audience=self.audience
            )
        except IdentityStorageConflictError as error:
            raise ConcurrentStateChangeError(
                "Clock anteriore allo stato delle sessioni attive."
            ) from error


class PairingService:
    """Manage one-time browser/TUI pairing without persisting raw codes."""

    def __init__(
        self,
        storage: PairingApplicationStorage,
        *,
        pepper: bytes,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        ttl: timedelta = timedelta(minutes=10),
        code_factory: Callable[[], str] = lambda: "".join(
            secrets.choice(_PAIRING_ALPHABET) for _index in range(10)
        ),
        pairing_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        pepper_box = [pepper]
        pepper = None
        configuration_failed = False
        try:
            validated_ttl = _positive_ttl(ttl, "ttl pairing")
        except AuthApplicationError:
            configuration_failed = True
            validated_ttl = timedelta(0)
        candidate_pepper = pepper_box[0]
        pepper_invalid = type(candidate_pepper) is not bytes or len(candidate_pepper) < 32
        if configuration_failed or pepper_invalid:
            pepper_box[0] = None
            candidate_pepper = None
            raise AuthApplicationError("Configurazione pairing non valida.")
        self._storage = storage
        self.clock = clock
        self.ttl = validated_ttl
        self.code_factory = code_factory
        self.pairing_id_factory = pairing_id_factory
        self.pepper = candidate_pepper
        candidate_pepper = None
        pepper_box[0] = None

    @property
    def storage(self) -> PairingApplicationStorage:
        return self._storage

    def issue(self) -> IssuedPairing:
        now = _utc(self.clock())
        for _attempt in range(_MAX_ATTEMPTS):
            raw_code = self.code_factory()
            code = None
            try:
                code_failed = False
                try:
                    code = _generated_text(raw_code, "pairing code", minimum_length=8)
                except AuthApplicationError:
                    code_failed = True
                    code = ""
                if code_failed:
                    raise CredentialGenerationError("Codice pairing generato non valido.")
                pairing = TuiPairing(
                    pairing_id=_generated_text(self.pairing_id_factory(), "pairing_id"),
                    code_digest=pairing_code_digest(code, self.pepper),
                    status="pending",
                    created_at=now,
                    expires_at=now + self.ttl,
                )
                try:
                    self.storage.create_pairing(pairing)
                except IdentityStorageConflictError:
                    continue
                return IssuedPairing(pairing, code)
            finally:
                raw_code = None
                code = None
        raise CredentialGenerationError("Impossibile generare un pairing univoco.")

    def authorize(
        self, code: str, user_id: str, *, required_role: str | None = None
    ) -> TuiPairing:
        try:
            digest = _pairing_digest_for_verification(code, self.pepper)
        finally:
            code = None
        pairing = self.storage.read_pairing_by_code_digest(digest)
        now = _utc(self.clock())
        pairing = self._require_secret(pairing, digest)
        if pairing.status == "expired":
            raise PairingExpiredError("Pairing scaduto.")
        if pairing.status != "pending":
            raise PairingStateError("Pairing non disponibile per l'autorizzazione.")
        self._require_current(pairing, now)
        account = self.storage.read_user(user_id)
        if account is None:
            raise InvalidCredentialError("Utente non disponibile.")
        require_active_account(account)
        if required_role is not None and account.role != required_role:
            raise InvalidCredentialError("Utente pairing non disponibile.")
        authorized = authorize_pairing(pairing, account.user_id, now)
        self._save_transition(
            authorized,
            require_active_user=True,
            expected_user_updated_at=account.updated_at,
        )
        return authorized

    def consume(self, pairing_id: str, code: str) -> TuiPairing:
        try:
            _pairing, account, consumed = self._prepare_consumption(
                pairing_id, code
            )
            self._save_transition(
                consumed,
                require_active_user=True,
                expected_user_updated_at=account.updated_at,
            )
            return consumed
        finally:
            code = None

    def _prepare_consumption(
        self, pairing_id: str, code: str
    ) -> tuple[TuiPairing, UserAccount, TuiPairing]:
        try:
            digest = _pairing_digest_for_verification(code, self.pepper)
        finally:
            code = None
        pairing = self.storage.read_pairing(pairing_id)
        now = _utc(self.clock())
        pairing = self._require_secret(pairing, digest)
        if pairing.status == "expired":
            raise PairingExpiredError("Pairing scaduto.")
        if pairing.status != "authorized":
            raise PairingStateError("Pairing non disponibile per il consumo.")
        self._require_current(pairing, now)
        account = self.storage.read_user(pairing.user_id or "")
        if account is None:
            raise InvalidCredentialError("Utente pairing non disponibile.")
        require_active_account(account)
        return pairing, account, consume_pairing(pairing, now)

    def revoke(self, pairing_id: str) -> TuiPairing:
        pairing = self.storage.read_pairing(pairing_id)
        if pairing is None:
            raise PairingStateError("Pairing non disponibile.")
        now = _utc(self.clock())
        if pairing.status not in {"pending", "authorized"}:
            raise PairingStateError("Pairing non revocabile.")
        self._require_current(pairing, now)
        revoked = revoke_pairing(pairing, now)
        self._save_transition(revoked)
        return revoked

    def _require_secret(self, pairing: TuiPairing | None, digest: str) -> TuiPairing:
        if pairing is None or not hmac.compare_digest(pairing.code_digest, digest):
            raise InvalidCredentialError("Pairing non valido.")
        return pairing

    def _require_current(self, pairing: TuiPairing, now: datetime) -> None:
        if now < pairing.created_at:
            raise PairingStateError("Pairing non ancora valido.")
        if pairing.authorized_at is not None and now < pairing.authorized_at:
            raise ConcurrentStateChangeError(
                "Clock anteriore all'autorizzazione del pairing."
            )
        if now >= pairing.expires_at:
            expired = expire_pairing(pairing, now)
            try:
                self.storage.save_pairing(expired)
            except (IdentityStorageConflictError, IdentityStorageNotFoundError):
                pass
            raise PairingExpiredError("Pairing scaduto.")

    def _save_transition(
        self,
        pairing: TuiPairing,
        *,
        require_active_user: bool = False,
        expected_user_updated_at: datetime | None = None,
    ) -> None:
        try:
            if require_active_user:
                if expected_user_updated_at is None:
                    raise AuthApplicationError("Revisione utente pairing mancante.")
                self.storage.save_pairing_for_active_user(
                    pairing, expected_user_updated_at=expected_user_updated_at
                )
            else:
                self.storage.save_pairing(pairing)
        except IdentityStoragePairingExpiredError:
            raise PairingExpiredError("Pairing scaduto.") from None
        except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
            current_pairing = self.storage.read_pairing(pairing.pairing_id)
            if (
                type(current_pairing) is TuiPairing
                and current_pairing.status == "expired"
            ):
                raise PairingExpiredError("Pairing scaduto.") from None
            if require_active_user and pairing.user_id is not None:
                account = self.storage.read_user(pairing.user_id)
                if account is None:
                    raise InvalidCredentialError("Utente pairing non disponibile.")
                require_active_account(account)
            raise ConcurrentStateChangeError(
                "Pairing modificato da un'altra operazione."
            ) from error


class TuiPairingSessionService:
    """Issue a student bearer atomically with one authorized pairing consumption."""

    def __init__(
        self,
        pairings: PairingService,
        *,
        session_ttl: timedelta = timedelta(hours=8),
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        session_id_factory: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        if type(pairings) is not PairingService:
            raise AuthApplicationError("Servizio pairing non valido.")
        self._pairings = pairings
        self.session_ttl = _positive_ttl(session_ttl, "ttl sessione TUI")
        self.token_factory = token_factory
        self.session_id_factory = session_id_factory

    @property
    def pairings(self) -> PairingService:
        return self._pairings

    @property
    def storage(self) -> PairingApplicationStorage:
        return self.pairings.storage

    def issue(self) -> IssuedPairing:
        return self.pairings.issue()

    def authorize(self, code: str, user_id: str) -> TuiPairing:
        try:
            return self.pairings.authorize(
                code, user_id, required_role="student"
            )
        finally:
            code = None

    def revoke(self, pairing_id: str) -> TuiPairing:
        return self.pairings.revoke(pairing_id)

    def consume(self, pairing_id: str, code: str) -> IssuedSession:
        try:
            pairing, account, consumed = self.pairings._prepare_consumption(
                pairing_id, code
            )
        finally:
            code = None
        if account.role != "student":
            pairing = None
            consumed = None
            account = None
            raise InvalidCredentialError("Utente pairing non disponibile.")
        for _attempt in range(_MAX_ATTEMPTS):
            raw_token = self.token_factory()
            try:
                if not valid_session_bearer(raw_token):
                    raise CredentialGenerationError(
                        "Token di sessione TUI generato non valido."
                    )
                digest_failed = False
                try:
                    digest = session_token_digest(raw_token)
                except AuthApplicationError:
                    digest_failed = True
                    digest = ""
                if digest_failed:
                    raise CredentialGenerationError(
                        "Token di sessione TUI generato non valido."
                    )
                session = UserSession(
                    session_id=_generated_text(
                        self.session_id_factory(), "session_id TUI"
                    ),
                    user_id=account.user_id,
                    token_digest=digest,
                    created_at=consumed.consumed_at,
                    expires_at=consumed.consumed_at + self.session_ttl,
                    last_seen_at=consumed.consumed_at,
                    audience="tui",
                    source_pairing_id=pairing.pairing_id,
                )
                try:
                    self.storage.consume_pairing_and_create_session(
                        consumed,
                        session,
                        expected_user_updated_at=account.updated_at,
                        expected_user_role="student",
                    )
                except IdentityStoragePairingExpiredError:
                    raise PairingExpiredError("Pairing scaduto.") from None
                except IdentityStorageSessionExpiredError:
                    raise ConcurrentStateChangeError(
                        "Sessione TUI scaduta durante il consumo."
                    ) from None
                except IdentityStorageConflictError:
                    current_pairing = self.storage.read_pairing(pairing.pairing_id)
                    current_account = self.storage.read_user(account.user_id)
                    if (
                        type(current_pairing) is TuiPairing
                        and current_pairing.status == "expired"
                    ):
                        raise PairingExpiredError("Pairing scaduto.") from None
                    if current_pairing != pairing:
                        raise ConcurrentStateChangeError(
                            "Pairing modificato durante il consumo."
                        ) from None
                    if current_account is None:
                        raise InvalidCredentialError(
                            "Utente pairing non disponibile."
                        ) from None
                    require_active_account(current_account)
                    if current_account.role != "student":
                        raise InvalidCredentialError(
                            "Utente pairing non disponibile."
                        ) from None
                    if current_account.updated_at != account.updated_at:
                        raise ConcurrentStateChangeError(
                            "Utente modificato durante il consumo pairing."
                        ) from None
                    continue
                return IssuedSession(session, raw_token)
            finally:
                raw_token = None
        raise CredentialGenerationError(
            "Impossibile generare una sessione TUI univoca."
        )
