"""Browser-mediated TUI pairing and bearer authentication boundary."""

from __future__ import annotations

import hmac
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scripts.thebitlab_auth_services import (
    AuthenticatedSession,
    AuthApplicationError,
    ConcurrentStateChangeError,
    CredentialGenerationError,
    InvalidCredentialError,
    IssuedPairing,
    IssuedSession,
    PairingExpiredError,
    PairingStateError,
    SessionService,
    TuiPairingSessionService,
    session_token_digest,
    valid_session_bearer,
)
from scripts.thebitlab_http_auth import (
    HttpAuthError,
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpAuthorizationDeniedError,
    HttpSessionAuthBoundary,
)
from scripts.thebitlab_identity import TuiPairing, UserAccount, UserSession

class TuiPairingBadRequestError(HttpAuthError):
    status_code = 400
    error_code = "tui_pairing_invalid"
    public_message = "Richiesta pairing TUI non valida."


class TuiPairingConflictError(HttpAuthError):
    status_code = 409
    error_code = "tui_pairing_conflict"
    public_message = "Pairing TUI non disponibile."


class TuiPairingExpiredHttpError(HttpAuthError):
    status_code = 410
    error_code = "tui_pairing_expired"
    public_message = "Pairing TUI scaduto."


class TuiPairingUnavailableError(HttpAuthError):
    status_code = 503
    error_code = "tui_pairing_unavailable"
    public_message = "Servizio pairing TUI temporaneamente non disponibile."


def _utc(value: datetime, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} deve includere il timezone.")
    return value.astimezone(timezone.utc)


def _identifier(value: str, field_name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} non valido.")
    normalized = value.strip()
    if (
        not normalized
        or normalized != value
        or len(normalized) > 512
        or any(
            ord(character) < 32
            or ord(character) == 127
            or 0xD800 <= ord(character) <= 0xDFFF
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} non valido.")
    return normalized


def _verification_path(value: str) -> str:
    path = _identifier(value, "verification_path")
    if (
        not path.startswith("/")
        or path.startswith("//")
        or "?" in path
        or "#" in path
        or "\\" in path
    ):
        raise ValueError("verification_path non valido.")
    return path


@dataclass(frozen=True)
class TuiPairingStart:
    pairing_id: str
    expires_at: datetime
    verification_path: str
    user_code: str = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "pairing_id", _identifier(self.pairing_id, "pairing_id"))
        object.__setattr__(self, "expires_at", _utc(self.expires_at, "expires_at"))
        object.__setattr__(
            self, "verification_path", _verification_path(self.verification_path)
        )
        object.__setattr__(self, "user_code", _identifier(self.user_code, "user_code"))


@dataclass(frozen=True)
class IssuedTuiCredential:
    session_id: str
    user_id: str
    expires_at: datetime
    bearer_token: str = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "session_id", _identifier(self.session_id, "session_id"))
        object.__setattr__(self, "user_id", _identifier(self.user_id, "user_id"))
        object.__setattr__(self, "expires_at", _utc(self.expires_at, "expires_at"))
        if not valid_session_bearer(self.bearer_token):
            raise ValueError("bearer_token non valido.")


@dataclass(frozen=True)
class TuiAuthenticatedContext:
    authenticated: AuthenticatedSession

    @property
    def user(self) -> UserAccount:
        return self.authenticated.user

    @property
    def session(self) -> UserSession:
        return self.authenticated.session


class TuiBrowserPairingBoundary:
    """Expose pairing operations without handing web/provider credentials to the TUI."""

    def __init__(
        self,
        pairings: TuiPairingSessionService,
        http_sessions: HttpSessionAuthBoundary,
        tui_sessions: SessionService,
        *,
        verification_path: str = "/auth/tui/pair",
    ) -> None:
        if (
            type(tui_sessions) is not SessionService
            or tui_sessions.audience != "tui"
            or getattr(http_sessions.sessions, "audience", None) != "web"
        ):
            raise ValueError("Audience sessioni pairing non configurate correttamente.")
        self.pairings = pairings
        self.http_sessions = http_sessions
        self.tui_sessions = tui_sessions
        self.verification_path = _verification_path(verification_path)

    def begin(self) -> TuiPairingStart:
        issued = None
        unavailable = False
        try:
            issued = self.pairings.issue()
        except Exception:
            unavailable = True
        if unavailable or type(issued) is not IssuedPairing:
            raise TuiPairingUnavailableError()
        malformed = False
        result = None
        try:
            result = TuiPairingStart(
                issued.pairing.pairing_id,
                issued.pairing.expires_at,
                self.verification_path,
                issued.code,
            )
        except Exception:
            malformed = True
        finally:
            issued = None
        if malformed or result is None:
            raise TuiPairingUnavailableError()
        return result

    def authorize_browser(self, request: HttpAuthRequest, code: str) -> None:
        context = None
        try:
            context = self.http_sessions.authorize_application(
                request, allowed_roles={"student"}
            )
            invalid = False
            expired = False
            conflict = False
            unavailable = False
            result = None
            try:
                result = self.pairings.authorize(code, context.user.user_id)
            except InvalidCredentialError:
                invalid = True
            except PairingExpiredError:
                expired = True
            except (PairingStateError, ConcurrentStateChangeError):
                conflict = True
            except Exception:
                unavailable = True
            if invalid:
                raise TuiPairingBadRequestError()
            if expired:
                raise TuiPairingExpiredHttpError()
            if conflict:
                raise TuiPairingConflictError()
            if (
                unavailable
                or type(result) is not TuiPairing
                or result.status != "authorized"
            ):
                raise TuiPairingUnavailableError()
        finally:
            request = None
            code = None
            context = None

    def consume(self, pairing_id: str, code: str) -> IssuedTuiCredential:
        issued = None
        invalid = False
        expired = False
        conflict = False
        unavailable = False
        try:
            issued = self.pairings.consume(pairing_id, code)
        except InvalidCredentialError:
            invalid = True
        except PairingExpiredError:
            expired = True
        except (PairingStateError, ConcurrentStateChangeError):
            conflict = True
        except (CredentialGenerationError, AuthApplicationError):
            unavailable = True
        except Exception:
            unavailable = True
        finally:
            pairing_id = None
            code = None
        if invalid:
            raise TuiPairingBadRequestError()
        if expired:
            raise TuiPairingExpiredHttpError()
        if conflict:
            raise TuiPairingConflictError()
        if unavailable or type(issued) is not IssuedSession:
            issued = None
            raise TuiPairingUnavailableError()
        if not self._issued_is_valid(issued):
            revoke_bearer = None
            try:
                if (
                    type(issued.session) is UserSession
                    and issued.session.audience == "tui"
                    and valid_session_bearer(issued.bearer_token)
                ):
                    revoke_bearer = issued.bearer_token
            except Exception:
                revoke_bearer = None
            issued = None
            if revoke_bearer is not None:
                self._best_effort_revoke(revoke_bearer)
            revoke_bearer = None
            raise TuiPairingUnavailableError()
        malformed = False
        credential = None
        revoke_bearer = None
        try:
            credential = IssuedTuiCredential(
                issued.session.session_id,
                issued.session.user_id,
                issued.session.expires_at,
                issued.bearer_token,
            )
        except Exception:
            malformed = True
            try:
                revoke_bearer = issued.bearer_token
            except Exception:
                revoke_bearer = None
        finally:
            issued = None
        if malformed or credential is None:
            if revoke_bearer is not None:
                self._best_effort_revoke(revoke_bearer)
            revoke_bearer = None
            raise TuiPairingUnavailableError()
        return credential

    def authenticate_bearer(self, authorization_header: str) -> TuiAuthenticatedContext:
        bearer = None
        invalid = False
        unavailable = False
        authenticated = None
        try:
            bearer = self._bearer(authorization_header)
            authorization_header = None
            try:
                authenticated = self.tui_sessions.authenticate(bearer)
            except InvalidCredentialError:
                invalid = True
            except Exception:
                unavailable = True
            if not invalid and not unavailable:
                try:
                    structurally_valid = self._valid_authenticated(
                        authenticated, bearer
                    )
                except Exception:
                    structurally_valid = False
                if not structurally_valid:
                    unavailable = True
        finally:
            bearer = None
            authorization_header = None
        if invalid:
            raise HttpAuthenticationRequiredError()
        if unavailable or authenticated is None:
            raise TuiPairingUnavailableError()
        if authenticated.user.role != "student":
            raise HttpAuthorizationDeniedError()
        return TuiAuthenticatedContext(authenticated)

    @staticmethod
    def _bearer(value: str) -> str:
        invalid = type(value) is not str or (
            type(value) is str and len(value) > 2048
        )
        scheme = None
        separator = None
        bearer = None
        if not invalid:
            scheme, separator, bearer = value.strip().partition(" ")
            invalid = (
                separator != " "
                or scheme.lower() != "bearer"
                or not valid_session_bearer(bearer)
            )
        value = None
        if invalid:
            scheme = None
            separator = None
            bearer = None
            raise HttpAuthenticationRequiredError()
        return bearer

    def _issued_is_valid(self, issued: IssuedSession) -> bool:
        bearer = None
        authenticated = None
        try:
            if (
                type(issued.session) is not UserSession
                or issued.session.audience != "tui"
                or not valid_session_bearer(issued.bearer_token)
            ):
                return False
            bearer = issued.bearer_token
            if not hmac.compare_digest(
                issued.session.token_digest, session_token_digest(bearer)
            ):
                return False
            authenticated = self.tui_sessions.authenticate(bearer)
            return (
                type(authenticated) is AuthenticatedSession
                and type(authenticated.session) is UserSession
                and type(authenticated.user) is UserAccount
                and authenticated.user.active
                and authenticated.user.role == "student"
                and authenticated.user.user_id == issued.session.user_id
                and authenticated.session.session_id == issued.session.session_id
                and authenticated.session.user_id == issued.session.user_id
                and authenticated.session.token_digest == issued.session.token_digest
                and authenticated.session.created_at == issued.session.created_at
                and authenticated.session.expires_at == issued.session.expires_at
                and authenticated.session.audience == "tui"
                and authenticated.session.revoked_at is None
            )
        except Exception:
            return False
        finally:
            bearer = None
            authenticated = None

    @staticmethod
    def _valid_authenticated(
        authenticated: AuthenticatedSession | None, bearer: str
    ) -> bool:
        if type(authenticated) is not AuthenticatedSession:
            return False
        if (
            type(authenticated.session) is not UserSession
            or type(authenticated.user) is not UserAccount
            or authenticated.session.user_id != authenticated.user.user_id
            or not authenticated.user.active
        ):
            return False
        try:
            digest = session_token_digest(bearer)
        except Exception:
            return False
        return hmac.compare_digest(authenticated.session.token_digest, digest)

    def _best_effort_revoke(self, bearer: str) -> None:
        try:
            self.tui_sessions.revoke(bearer)
        except Exception:
            pass
