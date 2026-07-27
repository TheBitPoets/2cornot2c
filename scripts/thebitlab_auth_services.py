from __future__ import annotations

import hashlib
import hmac
import secrets
import string
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
    IdentityStorageNotFoundError,
)


_MAX_ATTEMPTS = 5
_PAIRING_ALPHABET = string.ascii_uppercase + string.digits


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
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise ProviderProtocolError(f"{field_name} contiene caratteri di controllo.")
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


def session_token_digest(raw_token: str) -> str:
    """Digest one high-entropy bearer token without retaining the raw value."""

    token = _required_text(raw_token, "raw_token")
    if token != raw_token or len(token) < 32:
        raise CredentialGenerationError("Il token di sessione generato non e valido.")
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


def pairing_code_digest(raw_code: str, pepper: bytes) -> str:
    """Key one low-entropy pairing code with a server-side pepper."""

    code = _required_text(raw_code, "raw_code")
    if code != raw_code:
        raise CredentialGenerationError("Il codice pairing generato non e valido.")
    if type(pepper) is not bytes or len(pepper) < 32:
        raise AuthApplicationError("Il pepper pairing deve contenere almeno 32 byte.")
    return "hmac-sha256:" + hmac.new(pepper, code.encode("utf-8"), hashlib.sha256).hexdigest()


def _session_digest_for_verification(raw_token: str) -> str:
    try:
        return session_token_digest(raw_token)
    except AuthApplicationError as error:
        raise InvalidCredentialError("Sessione non valida.") from error


def _pairing_digest_for_verification(raw_code: str, pepper: bytes) -> str:
    try:
        return pairing_code_digest(raw_code, pepper)
    except AuthApplicationError as error:
        raise InvalidCredentialError("Pairing non valido.") from error


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
        try:
            assertion = self._assertions[credential]
        except (KeyError, TypeError):
            # Do not retain the opaque credential in a chained KeyError.
            raise ProviderAuthenticationError("Credenziale provider non valida.") from None
        if assertion.provider != self.provider_name:
            raise ProviderProtocolError("Il provider ha restituito un'assertion con issuer diverso.")
        return assertion


class FederatedIdentityApplicationStorage(Protocol):
    """Minimum persistence capabilities required by FederatedIdentityService."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def read_external_identity(
        self, provider: str, subject: str
    ) -> ExternalIdentity | None: ...

    def link_external_identity(self, identity: ExternalIdentity) -> None: ...

    def provision_user_with_identity(
        self, user: UserAccount, identity: ExternalIdentity
    ) -> None: ...


class SessionApplicationStorage(Protocol):
    """Minimum persistence capabilities required by SessionService."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def create_session_for_active_user(self, session: UserSession) -> None: ...

    def read_session_by_token_digest(self, token_digest: str) -> UserSession | None: ...

    def save_session(self, session: UserSession) -> None: ...

    def revoke_user_sessions(self, user_id: str, revoked_at: datetime) -> int: ...


class PairingApplicationStorage(Protocol):
    """Minimum persistence capabilities required by PairingService."""

    def read_user(self, user_id: str) -> UserAccount | None: ...

    def create_pairing(self, pairing: TuiPairing) -> None: ...

    def read_pairing(self, pairing_id: str) -> TuiPairing | None: ...

    def read_pairing_by_code_digest(self, code_digest: str) -> TuiPairing | None: ...

    def save_pairing(self, pairing: TuiPairing) -> None: ...

    def save_pairing_for_active_user(self, pairing: TuiPairing) -> None: ...


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
        try:
            expected_provider = _required_text(
                provider.provider_name, "provider_name", lowercase=True
            )
            assertion = provider.authenticate(credential)
        except Exception:
            # Provider exceptions and their causes may contain the opaque credential.
            raise ProviderAuthenticationError("Autenticazione provider non riuscita.") from None
        normalized_assertion = self._normalize_assertion(assertion)
        if normalized_assertion.provider != expected_provider:
            raise ProviderProtocolError("Assertion e provider adapter non coincidono.")
        return self._resolve_normalized(normalized_assertion)

    def resolve(self, assertion: FederatedIdentityAssertion) -> UserAccount:
        return self._resolve_normalized(self._normalize_assertion(assertion))

    @staticmethod
    def _normalize_assertion(assertion: object) -> FederatedIdentityAssertion:
        if type(assertion) is not FederatedIdentityAssertion:
            raise ProviderProtocolError("Il provider non ha restituito un'assertion valida.")
        try:
            return FederatedIdentityAssertion(
                provider=assertion.provider,
                subject=assertion.subject,
                display_name=assertion.display_name,
                email=assertion.email,
                email_verified=assertion.email_verified,
                username=assertion.username,
            )
        except Exception:
            raise ProviderProtocolError(
                "Il provider non ha restituito un'assertion valida."
            ) from None

    def _resolve_normalized(self, assertion: FederatedIdentityAssertion) -> UserAccount:
        now = _utc(self.clock())
        existing = self.storage.read_external_identity(assertion.provider, assertion.subject)
        if existing is not None:
            account = self.storage.read_user(existing.user_id)
            if account is None:
                raise ConcurrentStateChangeError("Identita collegata a un utente inesistente.")
            require_active_account(account)
            try:
                self.storage.link_external_identity(
                    ExternalIdentity(
                        user_id=account.user_id,
                        provider=assertion.provider,
                        subject=assertion.subject,
                        linked_at=existing.linked_at,
                        email=assertion.email,
                        username=assertion.username,
                    )
                )
            except IdentityStorageConflictError as error:
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

        if (
            assertion.provider not in self.onboarding_providers
            or assertion.email is None
            or not assertion.email_verified
        ):
            raise OnboardingNotAllowedError(
                "L'identita sconosciuta non soddisfa la policy di onboarding."
            )

        for _attempt in range(_MAX_ATTEMPTS):
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
            identity = ExternalIdentity(
                user_id=user_id,
                provider=assertion.provider,
                subject=assertion.subject,
                linked_at=now,
                email=assertion.email,
                username=assertion.username,
            )
            try:
                self.storage.provision_user_with_identity(account, identity)
                return account
            except IdentityStorageConflictError:
                winner = self.storage.read_external_identity(
                    assertion.provider, assertion.subject
                )
                if winner is not None:
                    winner_account = self.storage.read_user(winner.user_id)
                    if winner_account is None:
                        raise ConcurrentStateChangeError(
                            "Provisioning concorrente incompleto."
                        )
                    require_active_account(winner_account)
                    return winner_account
        raise CredentialGenerationError("Impossibile generare un user_id interno univoco.")


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
    ) -> None:
        self.storage = storage
        self.clock = clock
        self.ttl = _positive_ttl(ttl, "ttl sessione")
        self.token_factory = token_factory
        self.session_id_factory = session_id_factory

    def issue(self, user_id: str) -> IssuedSession:
        account = self.storage.read_user(user_id)
        if account is None:
            raise InvalidCredentialError("Utente non disponibile.")
        require_active_account(account)
        now = _utc(self.clock())
        for _attempt in range(_MAX_ATTEMPTS):
            raw_token = self.token_factory()
            try:
                digest = session_token_digest(raw_token)
            except AuthApplicationError as error:
                raise CredentialGenerationError("Token di sessione generato non valido.") from error
            session = UserSession(
                session_id=_generated_text(self.session_id_factory(), "session_id"),
                user_id=account.user_id,
                token_digest=digest,
                created_at=now,
                expires_at=now + self.ttl,
                last_seen_at=now,
            )
            try:
                self.storage.create_session_for_active_user(session)
                return IssuedSession(session, raw_token)
            except IdentityStorageConflictError:
                current_account = self.storage.read_user(account.user_id)
                if current_account is None:
                    raise InvalidCredentialError("Utente non disponibile.")
                require_active_account(current_account)
                continue
        raise CredentialGenerationError("Impossibile generare una sessione univoca.")

    def authenticate(self, bearer_token: str) -> AuthenticatedSession:
        digest = _session_digest_for_verification(bearer_token)
        session = self.storage.read_session_by_token_digest(digest)
        now = _utc(self.clock())
        session, account = self._require_valid(session, digest, now)
        if now > session.last_seen_at:
            try:
                self.storage.save_session(replace(session, last_seen_at=now))
            except (IdentityStorageConflictError, IdentityStorageNotFoundError):
                current = self.storage.read_session_by_token_digest(digest)
                session, account = self._require_valid(current, digest, now)
                if session.last_seen_at < now:
                    raise ConcurrentStateChangeError(
                        "Sessione modificata durante l'autenticazione."
                    )
            else:
                session = replace(session, last_seen_at=now)
        return AuthenticatedSession(session, account)

    def _require_valid(
        self,
        session: UserSession | None,
        digest: str,
        now: datetime,
    ) -> tuple[UserSession, UserAccount]:
        if session is None or not hmac.compare_digest(session.token_digest, digest):
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
        digest = _session_digest_for_verification(bearer_token)
        session = self.storage.read_session_by_token_digest(digest)
        now = _utc(self.clock())
        if session is None or session.revoked_at is not None or not hmac.compare_digest(
            session.token_digest, digest
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
            return self.storage.revoke_user_sessions(user_id, _utc(self.clock()))
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
        pairing_code_digest("VALIDATION", pepper)
        self.storage = storage
        self.pepper = pepper
        self.clock = clock
        self.ttl = _positive_ttl(ttl, "ttl pairing")
        self.code_factory = code_factory
        self.pairing_id_factory = pairing_id_factory

    def issue(self) -> IssuedPairing:
        now = _utc(self.clock())
        for _attempt in range(_MAX_ATTEMPTS):
            raw_code = self.code_factory()
            code = _generated_text(raw_code, "pairing code", minimum_length=8)
            pairing = TuiPairing(
                pairing_id=_generated_text(self.pairing_id_factory(), "pairing_id"),
                code_digest=pairing_code_digest(code, self.pepper),
                status="pending",
                created_at=now,
                expires_at=now + self.ttl,
            )
            try:
                self.storage.create_pairing(pairing)
                return IssuedPairing(pairing, code)
            except IdentityStorageConflictError:
                continue
        raise CredentialGenerationError("Impossibile generare un pairing univoco.")

    def authorize(self, code: str, user_id: str) -> TuiPairing:
        digest = _pairing_digest_for_verification(code, self.pepper)
        pairing = self.storage.read_pairing_by_code_digest(digest)
        now = _utc(self.clock())
        pairing = self._require_secret(pairing, digest)
        if pairing.status != "pending":
            raise PairingStateError("Pairing non disponibile per l'autorizzazione.")
        self._require_current(pairing, now)
        account = self.storage.read_user(user_id)
        if account is None:
            raise InvalidCredentialError("Utente non disponibile.")
        require_active_account(account)
        authorized = authorize_pairing(pairing, account.user_id, now)
        self._save_transition(authorized, require_active_user=True)
        return authorized

    def consume(self, pairing_id: str, code: str) -> TuiPairing:
        digest = _pairing_digest_for_verification(code, self.pepper)
        pairing = self.storage.read_pairing(pairing_id)
        now = _utc(self.clock())
        pairing = self._require_secret(pairing, digest)
        if pairing.status != "authorized":
            raise PairingStateError("Pairing non disponibile per il consumo.")
        self._require_current(pairing, now)
        account = self.storage.read_user(pairing.user_id or "")
        if account is None:
            raise InvalidCredentialError("Utente pairing non disponibile.")
        require_active_account(account)
        consumed = consume_pairing(pairing, now)
        self._save_transition(consumed, require_active_user=True)
        return consumed

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
        self, pairing: TuiPairing, *, require_active_user: bool = False
    ) -> None:
        try:
            if require_active_user:
                self.storage.save_pairing_for_active_user(pairing)
            else:
                self.storage.save_pairing(pairing)
        except (IdentityStorageConflictError, IdentityStorageNotFoundError) as error:
            if require_active_user and pairing.user_id is not None:
                account = self.storage.read_user(pairing.user_id)
                if account is None:
                    raise InvalidCredentialError("Utente pairing non disponibile.")
                require_active_account(account)
            raise ConcurrentStateChangeError(
                "Pairing modificato da un'altra operazione."
            ) from error
