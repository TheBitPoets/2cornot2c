"""Provider-independent HTTP session, cookie, CSRF, and role boundary."""

from __future__ import annotations

import base64
import hmac
import re
from dataclasses import dataclass, field
from datetime import timezone
from email.utils import format_datetime
from typing import Collection

from scripts.thebitlab_auth_services import (
    AuthApplicationError,
    AuthenticatedSession,
    IssuedSession,
    SessionService,
)

_COOKIE_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_COOKIE_VALUE_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_OTHER_COOKIE_VALUE_RE = re.compile(r'^[\x21\x23-\x2B\x2D-\x3A\x3C-\x5B\x5D-\x7E]*$')
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_APPLICATION_ROLES = frozenset({"admin", "teacher", "student"})
_MAX_SESSION_TOKEN_CHARS = 1024


class HttpAuthError(RuntimeError):
    """Stable, credential-free error suitable for mapping to an HTTP response."""

    status_code = 500
    error_code = "http_auth_error"
    public_message = "Errore autenticazione HTTP."

    def __init__(self) -> None:
        super().__init__(self.public_message)


class HttpBadRequestError(HttpAuthError):
    status_code = 400
    error_code = "bad_auth_request"
    public_message = "Richiesta di autenticazione non valida."


class HttpAuthenticationRequiredError(HttpAuthError):
    status_code = 401
    error_code = "authentication_required"
    public_message = "Autenticazione richiesta."


class HttpAuthorizationDeniedError(HttpAuthError):
    status_code = 403
    error_code = "authorization_denied"
    public_message = "Accesso non autorizzato."


class HttpCsrfRejectedError(HttpAuthError):
    status_code = 403
    error_code = "csrf_rejected"
    public_message = "Protezione CSRF non valida."


class HttpMethodNotAllowedError(HttpAuthError):
    status_code = 405
    error_code = "auth_method_not_allowed"
    public_message = "Metodo HTTP non supportato."


@dataclass(frozen=True)
class SessionCookiePolicy:
    """Cookie policy; insecure HTTP requires an explicit loopback-only opt-in."""

    name: str = "__Host-thebitlab_session"
    secure: bool = True
    same_site: str = "Lax"
    allow_insecure_loopback: bool = False
    max_cookie_header_bytes: int = 4096

    def __post_init__(self) -> None:
        if type(self.name) is not str or not _COOKIE_NAME_RE.fullmatch(self.name):
            raise ValueError("Nome cookie sessione non valido.")
        if type(self.secure) is not bool or type(self.allow_insecure_loopback) is not bool:
            raise ValueError("Flag sicurezza cookie non validi.")
        if type(self.same_site) is not str or self.same_site not in {"Strict", "Lax", "None"}:
            raise ValueError("SameSite non valido.")
        if self.same_site == "None" and not self.secure:
            raise ValueError("SameSite=None richiede Secure.")
        if self.name.startswith(("__Host-", "__Secure-")) and not self.secure:
            raise ValueError("Un cookie con prefisso sicuro richiede Secure.")
        if not self.secure and not self.allow_insecure_loopback:
            raise ValueError("HTTP senza Secure richiede opt-in loopback esplicito.")
        if (
            type(self.max_cookie_header_bytes) is not int
            or not 256 <= self.max_cookie_header_bytes <= 65536
        ):
            raise ValueError("Limite header Cookie non valido.")

    @classmethod
    def loopback_development(cls) -> "SessionCookiePolicy":
        return cls(
            name="thebitlab_session",
            secure=False,
            allow_insecure_loopback=True,
        )


@dataclass(frozen=True)
class HttpAuthRequest:
    method: str
    cookie_header: str | None = field(default=None, repr=False, compare=False)
    csrf_token: str | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class HttpAuthContext:
    authenticated: AuthenticatedSession
    csrf_token: str = field(repr=False, compare=False)

    @property
    def user(self):
        return self.authenticated.user

    @property
    def session(self):
        return self.authenticated.session


@dataclass(frozen=True)
class EstablishedHttpSession:
    context: HttpAuthContext
    set_cookie: str = field(repr=False, compare=False)


@dataclass(frozen=True)
class LogoutHttpResult:
    revoked: bool
    set_cookie: str = field(repr=False, compare=False)


class HttpSessionAuthBoundary:
    """Translate HTTP cookie/CSRF inputs to the provider-independent session service."""

    def __init__(
        self,
        sessions: SessionService,
        *,
        csrf_secret: bytes,
        cookie_policy: SessionCookiePolicy = SessionCookiePolicy(),
    ) -> None:
        candidate_secret = csrf_secret
        csrf_secret = None
        invalid_secret = type(candidate_secret) is not bytes or len(candidate_secret) < 32
        if invalid_secret:
            candidate_secret = None
            raise ValueError("Il secret CSRF deve contenere almeno 32 byte.")
        self.sessions = sessions
        self.cookie_policy = cookie_policy
        self._csrf_secret = candidate_secret
        candidate_secret = None

    def establish_session(
        self, user_id: str, *, existing_cookie_header: str | None = None
    ) -> EstablishedHttpSession:
        """Rotate any browser session, then issue one for an already-resolved user."""
        if existing_cookie_header:
            try:
                existing = self._extract_bearer(existing_cookie_header)
            finally:
                existing_cookie_header = None
            try:
                self.sessions.revoke(existing)
            except AuthApplicationError:
                pass
            finally:
                existing = None
        issued = self.sessions.issue(user_id)
        try:
            return self._established_result(issued)
        finally:
            issued = None

    def authenticate(self, request: HttpAuthRequest) -> HttpAuthContext:
        try:
            method, cookie_header, supplied_csrf = self._request_values(request)
        finally:
            request = None
        bearer = None
        auth_failed = False
        authenticated = None
        csrf_token = None
        context = None
        try:
            bearer = self._extract_bearer(cookie_header)
            cookie_header = None
            try:
                authenticated = self.sessions.authenticate(bearer)
            except AuthApplicationError:
                auth_failed = True
            if not auth_failed and authenticated is not None:
                csrf_token = self._csrf_token(bearer)
                if method in _UNSAFE_METHODS:
                    self._validate_csrf(bearer, supplied_csrf)
                context = HttpAuthContext(authenticated, csrf_token)
        finally:
            bearer = None
            cookie_header = None
            supplied_csrf = None
            csrf_token = None
        if auth_failed or context is None:
            raise HttpAuthenticationRequiredError()
        return context

    def authorize_application(
        self, request: HttpAuthRequest, *, allowed_roles: Collection[str]
    ) -> HttpAuthContext:
        normalized_roles = self._application_roles(allowed_roles)
        try:
            context = self.authenticate(request)
        finally:
            request = None
        if context.user.role not in normalized_roles:
            context = None
            raise HttpAuthorizationDeniedError()
        return context

    def logout(self, request: HttpAuthRequest) -> LogoutHttpResult:
        try:
            method, cookie_header, supplied_csrf = self._request_values(request)
        finally:
            request = None
        if method != "POST":
            cookie_header = None
            supplied_csrf = None
            raise HttpMethodNotAllowedError()
        bearer = None
        authenticated = None
        auth_failed = False
        try:
            bearer = self._extract_bearer(cookie_header)
            cookie_header = None
            try:
                authenticated = self.sessions.authenticate(bearer)
            except AuthApplicationError:
                auth_failed = True
            if auth_failed:
                return LogoutHttpResult(False, self._clear_cookie())
            self._validate_csrf(bearer, supplied_csrf)
            return LogoutHttpResult(self.sessions.revoke(bearer), self._clear_cookie())
        finally:
            bearer = None
            authenticated = None
            cookie_header = None
            supplied_csrf = None

    def _established_result(self, issued: IssuedSession) -> EstablishedHttpSession:
        bearer = issued.bearer_token
        authenticated = None
        failed = False
        try:
            try:
                authenticated = self.sessions.authenticate(bearer)
            except AuthApplicationError:
                failed = True
            if failed or authenticated is None:
                try:
                    self.sessions.revoke(bearer)
                except AuthApplicationError:
                    pass
                raise HttpAuthenticationRequiredError()
            csrf_token = self._csrf_token(bearer)
            set_cookie = self._session_cookie(bearer, issued)
            return EstablishedHttpSession(
                HttpAuthContext(authenticated, csrf_token),
                set_cookie,
            )
        finally:
            bearer = None
            issued = None

    @staticmethod
    def _request_values(request: HttpAuthRequest) -> tuple[str, str | None, str | None]:
        if type(request) is not HttpAuthRequest:
            request = None
            raise HttpBadRequestError()
        method = request.method
        cookie_header = request.cookie_header
        csrf_token = request.csrf_token
        request = None
        if type(method) is not str:
            cookie_header = None
            csrf_token = None
            raise HttpBadRequestError()
        method = method.strip().upper()
        if method not in _SAFE_METHODS | _UNSAFE_METHODS:
            cookie_header = None
            csrf_token = None
            raise HttpMethodNotAllowedError()
        return method, cookie_header, csrf_token

    def _extract_bearer(self, cookie_header: str | None) -> str:
        parse_failed = False
        bearer = None
        matches = None
        segment = None
        name = None
        value = None
        try:
            if type(cookie_header) is not str:
                parse_failed = True
            elif len(cookie_header.encode("utf-8")) > self.cookie_policy.max_cookie_header_bytes:
                parse_failed = True
            elif any(ord(character) < 0x20 or ord(character) == 0x7F for character in cookie_header):
                parse_failed = True
            else:
                matches: list[str] = []
                for segment in cookie_header.split(";"):
                    segment = segment.strip()
                    if not segment or "=" not in segment:
                        parse_failed = True
                        break
                    name, value = (part.strip() for part in segment.split("=", 1))
                    if not _COOKIE_NAME_RE.fullmatch(name):
                        parse_failed = True
                        break
                    if name == self.cookie_policy.name:
                        matches.append(value)
                    elif not _OTHER_COOKIE_VALUE_RE.fullmatch(value):
                        parse_failed = True
                        break
                if len(matches) != 1:
                    parse_failed = True
                else:
                    bearer = matches[0]
                    if (
                        not bearer
                        or len(bearer) > _MAX_SESSION_TOKEN_CHARS
                        or not _COOKIE_VALUE_RE.fullmatch(bearer)
                    ):
                        parse_failed = True
        except (UnicodeError, ValueError):
            parse_failed = True
        finally:
            cookie_header = None
            matches = None
            segment = None
            name = None
            value = None
        if parse_failed or bearer is None:
            bearer = None
            raise HttpAuthenticationRequiredError()
        return bearer

    def _validate_csrf(self, bearer: str, supplied_token: str | None) -> None:
        invalid = False
        try:
            expected = self._csrf_token(bearer)
            invalid = (
                type(supplied_token) is not str
                or len(supplied_token) != len(expected)
                or not hmac.compare_digest(supplied_token, expected)
            )
        finally:
            bearer = None
            supplied_token = None
            expected = None
        if invalid:
            raise HttpCsrfRejectedError()

    def _csrf_token(self, bearer: str) -> str:
        digest = hmac.digest(self._csrf_secret, b"thebitlab-csrf-v1\0" + bearer.encode(), "sha256")
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def _session_cookie(self, bearer: str, issued: IssuedSession) -> str:
        expires = format_datetime(issued.session.expires_at.astimezone(timezone.utc), usegmt=True)
        max_age = max(
            0,
            int((issued.session.expires_at - issued.session.created_at).total_seconds()),
        )
        attributes = [
            f"{self.cookie_policy.name}={bearer}",
            "Path=/",
            "HttpOnly",
            f"SameSite={self.cookie_policy.same_site}",
            f"Max-Age={max_age}",
            f"Expires={expires}",
        ]
        if self.cookie_policy.secure:
            attributes.insert(3, "Secure")
        return "; ".join(attributes)

    def _clear_cookie(self) -> str:
        attributes = [
            f"{self.cookie_policy.name}=",
            "Path=/",
            "HttpOnly",
            f"SameSite={self.cookie_policy.same_site}",
            "Max-Age=0",
            "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
        ]
        if self.cookie_policy.secure:
            attributes.insert(3, "Secure")
        return "; ".join(attributes)

    @staticmethod
    def _application_roles(allowed_roles: Collection[str]) -> frozenset[str]:
        if isinstance(allowed_roles, (str, bytes)):
            raise ValueError("I ruoli autorizzati devono essere una collezione.")
        roles = frozenset(allowed_roles)
        if not roles or not roles <= _APPLICATION_ROLES:
            raise ValueError("Policy ruoli applicativi non valida.")
        return roles
