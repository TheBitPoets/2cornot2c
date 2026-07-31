"""Google OpenID Connect authorization-code adapter with state, nonce, and PKCE."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import re
import secrets
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping, Protocol, Sequence

from scripts.thebitlab_auth_services import (
    AuthApplicationError,
    FederatedIdentityAssertion,
    FederatedIdentityService,
    OnboardingNotAllowedError,
)
from scripts.thebitlab_http_auth import (
    EstablishedHttpSession,
    HttpAuthenticationRequiredError,
    HttpSessionAuthBoundary,
)
from scripts.thebitlab_identity import AccountDisabledError, IdentityDomainError

_GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})
_GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_AUTHORIZATION_RESPONSE_ISSUER = "https://accounts.google.com"
_MISSING_CALLBACK_VALUE = object()
_GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_UNRESERVED_RE = re.compile(r"^[A-Za-z0-9._~-]+$")
_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{10,512}$")
_INVALID_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_MAX_CALLBACK_VALUE_CHARS = 8192
_TRANSACTION_COOKIE_PREFIX = "__Host-thebitlab_oidc_txn-"
_MAX_COOKIE_HEADER_BYTES = 4096
_GOOGLE_CERT_ENDPOINTS = frozenset(
    {
        "https://www.googleapis.com/oauth2/v1/certs",
        "https://www.googleapis.com/oauth2/v3/certs",
    }
)


class GoogleOidcError(RuntimeError):
    """Base credential-free Google OIDC adapter error."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.clear_transaction_cookie: str | None = None


class GoogleOidcConfigurationError(GoogleOidcError):
    """Raised for invalid server-side OIDC configuration."""


class GoogleOidcCallbackError(GoogleOidcError):
    """Raised for malformed or provider-declined callbacks."""


class GoogleOidcStateError(GoogleOidcError):
    """Raised for unknown, expired, duplicate, or replayed state."""


class GoogleOidcConsumedStateError(GoogleOidcStateError):
    """Raised after a terminal state was removed from the flow store."""


class GoogleOidcStateConflictError(GoogleOidcStateError):
    """Raised before insert when a generated state collides."""


class GoogleOidcFlowCapacityError(GoogleOidcStateConflictError):
    """Raised before insert when the bounded flow store is full."""


class GoogleOidcProviderUnavailableError(GoogleOidcError):
    """Raised when Google token or verification infrastructure is unavailable."""


class GoogleOidcTokenRejectedError(GoogleOidcError):
    """Raised when an ID token does not satisfy the OIDC contract."""


class GoogleOidcIdentityRejectedError(GoogleOidcError):
    """Raised when the authenticated Google identity cannot use an account."""


@dataclass(frozen=True, init=False)
class GoogleOidcConfig:
    client_id: str
    client_secret: str = field(repr=False, compare=False)
    redirect_uri: str
    authorization_endpoint: str = _GOOGLE_AUTHORIZATION_ENDPOINT
    token_endpoint: str = _GOOGLE_TOKEN_ENDPOINT
    post_login_path: str = "/"
    flow_ttl: timedelta = timedelta(minutes=10)
    id_token_max_age: timedelta = timedelta(minutes=15)
    clock_skew: timedelta = timedelta(seconds=30)
    timeout_seconds: float = 10.0
    max_token_response_bytes: int = 64 * 1024
    max_cert_response_bytes: int = 256 * 1024

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorization_endpoint: str = _GOOGLE_AUTHORIZATION_ENDPOINT,
        token_endpoint: str = _GOOGLE_TOKEN_ENDPOINT,
        post_login_path: str = "/",
        flow_ttl: timedelta = timedelta(minutes=10),
        id_token_max_age: timedelta = timedelta(minutes=15),
        clock_skew: timedelta = timedelta(seconds=30),
        timeout_seconds: float = 10.0,
        max_token_response_bytes: int = 64 * 1024,
        max_cert_response_bytes: int = 256 * 1024,
    ) -> None:
        candidate_secret = client_secret
        client_secret = None
        object.__setattr__(self, "client_id", client_id)
        object.__setattr__(self, "client_secret", candidate_secret)
        object.__setattr__(self, "redirect_uri", redirect_uri)
        object.__setattr__(self, "authorization_endpoint", authorization_endpoint)
        object.__setattr__(self, "token_endpoint", token_endpoint)
        object.__setattr__(self, "post_login_path", post_login_path)
        object.__setattr__(self, "flow_ttl", flow_ttl)
        object.__setattr__(self, "id_token_max_age", id_token_max_age)
        object.__setattr__(self, "clock_skew", clock_skew)
        object.__setattr__(self, "timeout_seconds", timeout_seconds)
        object.__setattr__(self, "max_token_response_bytes", max_token_response_bytes)
        object.__setattr__(self, "max_cert_response_bytes", max_cert_response_bytes)
        validation_error = None
        unexpected = False
        try:
            self._validate()
        except GoogleOidcConfigurationError as error:
            validation_error = error
        except Exception:
            unexpected = True
        if validation_error is not None or unexpected:
            object.__setattr__(self, "client_secret", "")
            candidate_secret = None
            if validation_error is not None:
                raise validation_error
            raise GoogleOidcConfigurationError("Configurazione Google OIDC non valida.")
        candidate_secret = None

    def _validate(self) -> None:
        if type(self.client_id) is not str or not _CLIENT_ID_RE.fullmatch(self.client_id):
            raise GoogleOidcConfigurationError("Google client ID non valido.")
        if (
            type(self.client_secret) is not str
            or not 1 <= len(self.client_secret) <= 2048
            or not self.client_secret.strip()
            or any(ord(character) < 0x20 for character in self.client_secret)
        ):
            raise GoogleOidcConfigurationError("Google client secret non valido.")
        for field_name in ("redirect_uri", "authorization_endpoint", "token_endpoint"):
            value = getattr(self, field_name)
            parsed = urllib.parse.urlsplit(value) if type(value) is str else None
            invalid_port = False
            try:
                port = parsed.port if parsed is not None else None
            except ValueError:
                invalid_port = True
                port = None
            if (
                parsed is None
                or invalid_port
                or (port is not None and port < 1)
                or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in value)
                or "\\" in value
                or _INVALID_PERCENT_ESCAPE_RE.search(value) is not None
                or parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.fragment
                or (field_name != "redirect_uri" and parsed.query)
            ):
                raise GoogleOidcConfigurationError(
                    f"{field_name} deve essere un URL HTTPS assoluto."
                )
        if (
            self.authorization_endpoint != _GOOGLE_AUTHORIZATION_ENDPOINT
            or self.token_endpoint != _GOOGLE_TOKEN_ENDPOINT
        ):
            raise GoogleOidcConfigurationError(
                "Endpoint Google OIDC non consentito."
            )
        encoded_post_login = (
            urllib.parse.unquote_to_bytes(self.post_login_path)
            if type(self.post_login_path) is str
            else b""
        )
        if (
            type(self.post_login_path) is not str
            or not self.post_login_path.startswith("/")
            or self.post_login_path.startswith("//")
            or "\\" in self.post_login_path
            or _INVALID_PERCENT_ESCAPE_RE.search(self.post_login_path) is not None
            or any(
                ord(character) <= 0x20 or ord(character) == 0x7F
                for character in self.post_login_path
            )
            or any(byte < 0x20 or byte == 0x7F for byte in encoded_post_login)
        ):
            raise GoogleOidcConfigurationError("Path post-login non valido.")
        for value, name, maximum in (
            (self.flow_ttl, "flow_ttl", timedelta(minutes=30)),
            (self.id_token_max_age, "id_token_max_age", timedelta(hours=1)),
            (self.clock_skew, "clock_skew", timedelta(minutes=5)),
        ):
            if (
                type(value) is not timedelta
                or value < timedelta(0)
                or (name != "clock_skew" and value == timedelta(0))
                or value > maximum
            ):
                raise GoogleOidcConfigurationError(f"{name} non valido.")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not 0 < self.timeout_seconds <= 60
        ):
            raise GoogleOidcConfigurationError("Timeout OIDC non valido.")
        for value, name, minimum in (
            (self.max_token_response_bytes, "token", 1024),
            (self.max_cert_response_bytes, "certificati", 4096),
        ):
            if type(value) is not int or not minimum <= value <= 1024 * 1024:
                raise GoogleOidcConfigurationError(
                    f"Limite risposta {name} non valido."
                )


@dataclass(frozen=True)
class PendingGoogleOidcFlow:
    state_digest: str
    nonce_digest: str
    browser_digest: str
    code_verifier: str = field(repr=False, compare=False)
    creation_marker: object = field(repr=False, compare=False)
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class GoogleAuthorizationRequest:
    authorization_url: str = field(repr=False, compare=False)
    set_cookie: str = field(repr=False, compare=False)


@dataclass(frozen=True)
class GoogleOidcLoginResult:
    user_id: str
    role: str
    session: EstablishedHttpSession
    redirect_path: str
    clear_transaction_cookie: str = field(repr=False, compare=False)


class GoogleTokenTransport(Protocol):
    def exchange_code(
        self,
        *,
        endpoint: str,
        form: Mapping[str, str],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> Mapping[str, object]: ...


class GoogleIdTokenVerifier(Protocol):
    def verify(self, id_token: str, *, audience: str) -> Mapping[str, object]: ...


class InMemoryGoogleOidcFlowStore:
    """Thread-safe one-time flow store; raw verifier exists only in memory."""

    def __init__(self, *, max_pending_flows: int = 4096) -> None:
        if type(max_pending_flows) is not int or not 1 <= max_pending_flows <= 100000:
            raise GoogleOidcConfigurationError("Limite flow OIDC non valido.")
        self.max_pending_flows = max_pending_flows
        self._flows: dict[str, PendingGoogleOidcFlow] = {}
        self._lock = threading.Lock()

    @staticmethod
    def state_digest(state: str) -> str:
        return "sha256:" + hashlib.sha256(state.encode("ascii")).hexdigest()

    @staticmethod
    def nonce_digest(nonce: str) -> str:
        return "sha256:" + hashlib.sha256(nonce.encode("ascii")).hexdigest()

    @staticmethod
    def browser_digest(browser_binding: str) -> str:
        return "sha256:" + hashlib.sha256(browser_binding.encode("ascii")).hexdigest()

    def create(
        self,
        state: str,
        nonce: str,
        code_verifier: str,
        browser_binding: str,
        creation_marker: object,
        now: datetime,
        ttl: timedelta,
    ) -> None:
        flow = None
        conflict_message = None
        capacity_exhausted = False
        try:
            flow = PendingGoogleOidcFlow(
                state_digest=self.state_digest(state),
                nonce_digest=self.nonce_digest(nonce),
                browser_digest=self.browser_digest(browser_binding),
                code_verifier=code_verifier,
                creation_marker=creation_marker,
                created_at=now,
                expires_at=now + ttl,
            )
            with self._lock:
                expired = [
                    key for key, current in self._flows.items()
                    if current.expires_at <= now
                ]
                for key in expired:
                    del self._flows[key]
                if len(self._flows) >= self.max_pending_flows:
                    conflict_message = "Capacita flow OIDC esaurita."
                    capacity_exhausted = True
                elif flow.state_digest in self._flows:
                    conflict_message = "Collisione state OIDC."
                else:
                    self._flows[flow.state_digest] = flow
        finally:
            state = None
            nonce = None
            code_verifier = None
            browser_binding = None
            creation_marker = None
            flow = None
        if conflict_message is not None:
            if capacity_exhausted:
                raise GoogleOidcFlowCapacityError(conflict_message)
            raise GoogleOidcStateConflictError(conflict_message)

    def consume(
        self, state: str, browser_binding: str, now: datetime
    ) -> PendingGoogleOidcFlow:
        digest_failed = False
        try:
            digest = self.state_digest(state)
            supplied_browser_digest = self.browser_digest(browser_binding)
        except Exception:
            digest_failed = True
            digest = ""
            supplied_browser_digest = ""
        finally:
            state = None
            browser_binding = None
        if digest_failed:
            raise GoogleOidcStateError("State OIDC non valido.")
        with self._lock:
            flow = self._flows.get(digest)
            binding_matches = flow is not None and hmac.compare_digest(
                flow.browser_digest, supplied_browser_digest
            )
            if binding_matches:
                del self._flows[digest]
        supplied_browser_digest = None
        if flow is None or not binding_matches:
            flow = None
            raise GoogleOidcStateError("State OIDC sconosciuto o gia usato.")
        if now < flow.created_at or now >= flow.expires_at:
            flow = None
            raise GoogleOidcConsumedStateError("State OIDC scaduto.")
        return flow

    def discard_created_flow(self, state: str, creation_marker: object) -> bool:
        digest_failed = False
        try:
            state_digest = self.state_digest(state)
        except Exception:
            digest_failed = True
            state_digest = ""
        finally:
            state = None
        if digest_failed:
            creation_marker = None
            return False
        with self._lock:
            flow = self._flows.get(state_digest)
            matches = flow is not None and flow.creation_marker is creation_marker
            if matches:
                del self._flows[state_digest]
        flow = None
        creation_marker = None
        return matches

    def delete_expired(self, cutoff: datetime) -> int:
        with self._lock:
            expired = [key for key, flow in self._flows.items() if flow.expires_at <= cutoff]
            for key in expired:
                del self._flows[key]
            return len(expired)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._flows)


class UrllibGoogleTokenTransport:
    """Bounded HTTPS form transport that never follows redirects."""

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None

    def __init__(self) -> None:
        self._opener = urllib.request.build_opener(self._NoRedirect())

    def exchange_code(
        self,
        *,
        endpoint: str,
        form: Mapping[str, str],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> Mapping[str, object]:
        failed = False
        rejected = False
        configuration_failed = False
        payload = None
        request = None
        response = None
        response_bytes = None
        try:
            payload = urllib.parse.urlencode(form).encode("ascii")
            form = None
            request = urllib.request.Request(
                endpoint,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            with self._opener.open(request, timeout=timeout_seconds) as response:
                if response.status != 200:
                    failed = True
                else:
                    response_bytes = response.read(max_response_bytes + 1)
                    if len(response_bytes) > max_response_bytes:
                        failed = True
        except urllib.error.HTTPError as error:
            status = error.code
            error_bytes = None
            if 400 <= status < 500:
                try:
                    error_bytes = error.read(max_response_bytes + 1)
                    if len(error_bytes) > max_response_bytes:
                        raise ValueError("Risposta OAuth 4xx oltre il limite.")
                    decoded_error = json.loads(
                        error_bytes.decode("utf-8"),
                        object_pairs_hook=_reject_duplicate_json_keys,
                    )
                    oauth_error = (
                        decoded_error.get("error")
                        if type(decoded_error) is dict
                        else None
                    )
                    if oauth_error in {
                        "invalid_client",
                        "invalid_request",
                        "unauthorized_client",
                        "unsupported_grant_type",
                        "invalid_scope",
                    }:
                        configuration_failed = True
                    elif oauth_error == "invalid_grant":
                        rejected = True
                    else:
                        failed = True
                except Exception:
                    failed = True
                finally:
                    error_bytes = None
                    decoded_error = None
                    oauth_error = None
            else:
                failed = True
            error = None
        except Exception:
            failed = True
        finally:
            payload = None
            request = None
            response = None
            form = None
        if configuration_failed:
            response_bytes = None
            raise GoogleOidcConfigurationError(
                "Credenziali client Google rifiutate."
            )
        if rejected:
            response_bytes = None
            raise GoogleOidcTokenRejectedError(
                "Authorization code Google rifiutato."
            )
        if failed or response_bytes is None:
            response_bytes = None
            raise GoogleOidcProviderUnavailableError("Token endpoint Google non disponibile.")
        try:
            decoded = json.loads(
                response_bytes.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_json_keys,
            )
        except (UnicodeError, ValueError, TypeError):
            decoded = None
        finally:
            response_bytes = None
        if type(decoded) is not dict:
            decoded = None
            raise GoogleOidcProviderUnavailableError("Risposta token Google non valida.")
        return decoded


class _GoogleAuthCertResponse:
    def __init__(self, status: int, data: bytes, headers: Mapping[str, str]) -> None:
        self.status = status
        self.data = data
        self.headers = headers


class BoundedGoogleCertRequest:
    """google-auth request adapter with fixed endpoints, bounds, and no redirects."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
        max_response_bytes: int = 256 * 1024,
    ) -> None:
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or not 0 < timeout_seconds <= 60
        ):
            raise GoogleOidcConfigurationError(
                "Timeout certificati non valido."
            )
        if (
            type(max_response_bytes) is not int
            or not 4096 <= max_response_bytes <= 1024 * 1024
        ):
            raise GoogleOidcConfigurationError(
                "Limite certificati non valido."
            )
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self._opener = urllib.request.build_opener(UrllibGoogleTokenTransport._NoRedirect())

    def __call__(
        self,
        url: str,
        method: str = "GET",
        body: bytes | None = None,
        headers: Mapping[str, str] | None = None,
        **_kwargs,
    ) -> _GoogleAuthCertResponse:
        failed = False
        request = None
        response = None
        data = None
        status = 0
        response_headers: Mapping[str, str] = {}
        try:
            if url not in _GOOGLE_CERT_ENDPOINTS or method != "GET" or body is not None:
                failed = True
            else:
                request = urllib.request.Request(
                    url,
                    headers={"Accept": "application/json", **dict(headers or {})},
                    method="GET",
                )
                with self._opener.open(request, timeout=self.timeout_seconds) as response:
                    status = response.status
                    data = response.read(self.max_response_bytes + 1)
                    response_headers = dict(response.headers.items())
                    if status != 200 or len(data) > self.max_response_bytes:
                        failed = True
        except Exception:
            failed = True
        finally:
            request = None
            response = None
            body = None
            headers = None
        if failed or data is None:
            data = None
            raise GoogleOidcProviderUnavailableError(
                "Certificati Google non disponibili."
            )
        return _GoogleAuthCertResponse(status, data, response_headers)


class _X509OnlyGoogleCertRequest:
    """Reject JWKS so google-auth cannot start an independent PyJWT fetch."""

    def __init__(self, delegate, *, max_response_bytes: int) -> None:
        self.delegate = delegate
        self.max_response_bytes = max_response_bytes

    def __call__(self, url: str, **kwargs):
        response = self.delegate(url, **kwargs)
        data = getattr(response, "data", None)
        valid = (
            url == "https://www.googleapis.com/oauth2/v1/certs"
            and type(data) is bytes
            and len(data) <= self.max_response_bytes
        )
        decoded = None
        if valid:
            try:
                decoded = json.loads(
                    data.decode("utf-8"),
                    object_pairs_hook=_reject_duplicate_json_keys,
                )
            except (UnicodeError, ValueError, TypeError):
                valid = False
        valid = (
            valid
            and type(decoded) is dict
            and "keys" not in decoded
            and 1 <= len(decoded) <= 32
            and all(
                type(key) is str
                and 1 <= len(key) <= 512
                and type(value) is str
                and 1 <= len(value) <= 16384
                and value.startswith("-----BEGIN CERTIFICATE-----")
                and value.rstrip().endswith("-----END CERTIFICATE-----")
                for key, value in decoded.items()
            )
        )
        if valid:
            try:
                from cryptography import x509

                for certificate_pem in decoded.values():
                    x509.load_pem_x509_certificate(certificate_pem.encode("ascii"))
            except Exception:
                valid = False
            finally:
                certificate_pem = None
        decoded = None
        data = None
        if not valid:
            response = None
            raise GoogleOidcProviderUnavailableError(
                "Formato certificati Google non valido."
            )
        return response


class GoogleOfficialIdTokenVerifier:
    """Production verifier backed by google-auth and a bounded cert transport."""

    def __init__(
        self,
        request_adapter=None,
        *,
        clock_skew_seconds: int = 30,
        max_cert_response_bytes: int = 256 * 1024,
    ) -> None:
        if (
            type(clock_skew_seconds) is not int
            or not 0 <= clock_skew_seconds <= 300
        ):
            raise GoogleOidcConfigurationError("Clock skew verifier non valido.")
        if (
            type(max_cert_response_bytes) is not int
            or not 4096 <= max_cert_response_bytes <= 1048576
        ):
            raise GoogleOidcConfigurationError("Limite certificati non valido.")
        self._request_adapter = request_adapter or BoundedGoogleCertRequest(
            max_response_bytes=max_cert_response_bytes
        )
        self.max_cert_response_bytes = max_cert_response_bytes
        self.clock_skew_seconds = clock_skew_seconds

    @classmethod
    def from_config(cls, config: GoogleOidcConfig) -> "GoogleOfficialIdTokenVerifier":
        return cls(
            BoundedGoogleCertRequest(
                timeout_seconds=float(config.timeout_seconds),
                max_response_bytes=config.max_cert_response_bytes,
            ),
            clock_skew_seconds=int(config.clock_skew.total_seconds()),
            max_cert_response_bytes=config.max_cert_response_bytes,
        )

    def verify(self, id_token: str, *, audience: str) -> Mapping[str, object]:
        failed = False
        unavailable = False
        claims = None
        try:
            from google.oauth2 import id_token as google_id_token

            request_adapter = _X509OnlyGoogleCertRequest(
                self._request_adapter,
                max_response_bytes=self.max_cert_response_bytes,
            )
            claims = google_id_token.verify_oauth2_token(
                id_token,
                request_adapter,
                audience,
                clock_skew_in_seconds=self.clock_skew_seconds,
            )
        except GoogleOidcProviderUnavailableError:
            unavailable = True
        except Exception:
            failed = True
        finally:
            id_token = None
            audience = None
            request_adapter = None
        if unavailable:
            claims = None
            raise GoogleOidcProviderUnavailableError(
                "Verifica certificati Google non disponibile."
            )
        if failed or type(claims) is not dict:
            claims = None
            raise GoogleOidcTokenRejectedError("ID token Google rifiutato.")
        return claims


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Chiave JSON duplicata.")
        result[key] = value
    return result


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise GoogleOidcConfigurationError("Clock OIDC senza timezone.")
    return value.astimezone(timezone.utc)


def _generated_credential(value: object, name: str, minimum: int, maximum: int) -> str:
    invalid = (
        type(value) is not str
        or not minimum <= len(value) <= maximum
        or not _UNRESERVED_RE.fullmatch(value)
    )
    if invalid:
        value = None
        raise GoogleOidcConfigurationError(f"Generatore {name} non valido.")
    return value


class GoogleOidcLoginService:
    """Coordinate Google OIDC callback, identity resolution, and HTTP session issue."""

    def __init__(
        self,
        config: GoogleOidcConfig,
        flows: InMemoryGoogleOidcFlowStore,
        token_transport: GoogleTokenTransport,
        token_verifier: GoogleIdTokenVerifier,
        identities: FederatedIdentityService,
        http_sessions: HttpSessionAuthBoundary,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        state_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        nonce_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        verifier_factory: Callable[[], str] = lambda: secrets.token_urlsafe(64),
        browser_binding_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    ) -> None:
        self.config = config
        self.flows = flows
        self.token_transport = token_transport
        self.token_verifier = token_verifier
        self.identities = identities
        self.http_sessions = http_sessions
        self.clock = clock
        self.state_factory = state_factory
        self.nonce_factory = nonce_factory
        self.verifier_factory = verifier_factory
        self.browser_binding_factory = browser_binding_factory

    def begin_login(self) -> GoogleAuthorizationRequest:
        now = None
        clock_failed = False
        try:
            now = _utc(self.clock())
        except Exception:
            clock_failed = True
        if clock_failed or now is None:
            now = None
            raise GoogleOidcProviderUnavailableError(
                "Clock flow OIDC non disponibile."
            )
        for _attempt in range(5):
            state = None
            nonce = None
            verifier = None
            browser_binding = None
            generation_error = None
            generation_unavailable = False
            try:
                state = _generated_credential(self.state_factory(), "state", 32, 256)
                nonce = _generated_credential(self.nonce_factory(), "nonce", 32, 256)
                verifier = _generated_credential(
                    self.verifier_factory(), "PKCE verifier", 43, 128
                )
                browser_binding = _generated_credential(
                    self.browser_binding_factory(), "browser binding", 32, 256
                )
            except GoogleOidcConfigurationError as error:
                generation_error = error
            except Exception:
                generation_unavailable = True
            if generation_error is not None or generation_unavailable:
                state = None
                nonce = None
                verifier = None
                browser_binding = None
                if generation_error is not None:
                    raise generation_error
                raise GoogleOidcProviderUnavailableError(
                    "Generatori flow OIDC non disponibili."
                )
            collision = False
            store_failed = False
            creation_marker = object()
            try:
                self.flows.create(
                    state,
                    nonce,
                    verifier,
                    browser_binding,
                    creation_marker,
                    now,
                    self.config.flow_ttl,
                )
            except GoogleOidcFlowCapacityError:
                store_failed = True
            except GoogleOidcStateConflictError:
                collision = True
            except Exception:
                store_failed = True
            if collision:
                inserted_then_failed = False
                try:
                    inserted_then_failed = self.flows.discard_created_flow(
                        state, creation_marker
                    )
                except Exception:
                    pass
                if inserted_then_failed:
                    collision = False
                    store_failed = True
                else:
                    state = None
                    nonce = None
                    verifier = None
                    browser_binding = None
                    creation_marker = None
                    continue
            if store_failed:
                try:
                    self.flows.discard_created_flow(state, creation_marker)
                except Exception:
                    pass
                state = None
                nonce = None
                verifier = None
                browser_binding = None
                creation_marker = None
                raise GoogleOidcProviderUnavailableError(
                    "Store flow OIDC non disponibile."
                )
            build_failed = False
            authorization_url = None
            authorization_request = None
            challenge = None
            query = None
            transaction_cookie = None
            try:
                challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(verifier.encode("ascii")).digest()
                ).rstrip(b"=").decode("ascii")
                query = urllib.parse.urlencode(
                    {
                        "client_id": self.config.client_id,
                        "redirect_uri": self.config.redirect_uri,
                        "response_type": "code",
                        "scope": "openid email profile",
                        "state": state,
                        "nonce": nonce,
                        "code_challenge": challenge,
                        "code_challenge_method": "S256",
                    }
                )
                authorization_url = f"{self.config.authorization_endpoint}?{query}"
                transaction_cookie = self._transaction_cookie(
                    state, browser_binding
                )
                authorization_request = GoogleAuthorizationRequest(
                    authorization_url, transaction_cookie
                )
            except Exception:
                build_failed = True
            if build_failed or authorization_request is None:
                try:
                    self.flows.discard_created_flow(state, creation_marker)
                except Exception:
                    pass
                state = None
                nonce = None
                verifier = None
                browser_binding = None
                creation_marker = None
                authorization_url = None
                authorization_request = None
                challenge = None
                query = None
                transaction_cookie = None
                raise GoogleOidcProviderUnavailableError(
                    "Authorization request Google non disponibile."
                )
            state = None
            nonce = None
            verifier = None
            browser_binding = None
            creation_marker = None
            authorization_url = None
            challenge = None
            query = None
            transaction_cookie = None
            return authorization_request
        raise GoogleOidcConfigurationError("Impossibile generare state OIDC univoco.")

    @staticmethod
    def _transaction_cookie_name(state: str) -> str:
        suffix = hashlib.sha256(state.encode("utf-8")).hexdigest()[:24]
        return _TRANSACTION_COOKIE_PREFIX + suffix

    def _transaction_cookie(self, state: str, browser_binding: str) -> str:
        max_age = math.ceil(self.config.flow_ttl.total_seconds())
        cookie_name = self._transaction_cookie_name(state)
        return (
            f"{cookie_name}={browser_binding}; Path=/; "
            f"Max-Age={max_age}; Secure; HttpOnly; SameSite=Lax"
        )

    @staticmethod
    def _clear_transaction_cookie(cookie_name: str) -> str:
        return (
            f"{cookie_name}=; Path=/; Max-Age=0; "
            "Expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure; HttpOnly; SameSite=Lax"
        )

    @classmethod
    def _transaction_binding(
        cls, cookie_header: str | None, state: str
    ) -> tuple[str, str]:
        cookie_name = cls._transaction_cookie_name(state)
        invalid = (
            type(cookie_header) is not str
            or not cookie_header
            or len(cookie_header.encode("utf-8")) > _MAX_COOKIE_HEADER_BYTES
            or any(
                ord(character) < 0x20 or ord(character) == 0x7F
                for character in cookie_header
            )
        )
        matches: list[str] = []
        if not invalid:
            for part in cookie_header.split(";"):
                name, separator, value = part.strip().partition("=")
                if separator and name == cookie_name:
                    matches.append(value)
        if (
            invalid
            or len(matches) != 1
            or not 32 <= len(matches[0]) <= 256
            or _UNRESERVED_RE.fullmatch(matches[0]) is None
        ):
            matches = []
            cookie_header = None
            part = None
            name = None
            value = None
            raise GoogleOidcStateError("Cookie transazione OIDC non valido.")
        binding = matches[0]
        matches = []
        cookie_header = None
        return binding, cookie_name

    def complete_callback(
        self,
        parameters: Mapping[str, Sequence[str]],
        *,
        existing_cookie_header: str | None = None,
    ) -> GoogleOidcLoginResult:
        flow = None
        token_response = None
        id_token = None
        claims = None
        code = None
        state = None
        browser_binding = None
        transaction_cookie_name = None
        provider_error = False
        assertion = None
        user = None
        session = None
        result = None
        expected_error = None
        unexpected_failed = False
        flow_consumed = False
        clear_cookie_name = None
        try:
            try:
                code, state, provider_error = self._callback_values(parameters)
            finally:
                parameters = None
            state_failed = False
            state_unavailable = False
            try:
                browser_binding, transaction_cookie_name = (
                    self._transaction_binding(existing_cookie_header, state)
                )
                clear_cookie_name = transaction_cookie_name
                flow = self.flows.consume(
                    state, browser_binding, _utc(self.clock())
                )
            except GoogleOidcConsumedStateError:
                flow_consumed = True
                state_failed = True
            except GoogleOidcStateError:
                state_failed = True
            except Exception:
                state_unavailable = True
            state = None
            browser_binding = None
            if state_failed:
                raise GoogleOidcStateError("State OIDC non valido o gia usato.")
            if state_unavailable or flow is None:
                raise GoogleOidcProviderUnavailableError(
                    "Store flow OIDC non disponibile."
                )
            flow_consumed = True
            if provider_error:
                provider_error = False
                raise GoogleOidcCallbackError("Login Google annullato o rifiutato.")
            token_response = self._exchange(code, flow.code_verifier)
            code = None
            id_token = token_response.get("id_token")
            token_response = None
            if type(id_token) is not str or not 32 <= len(id_token) <= 32768:
                raise GoogleOidcTokenRejectedError("ID token Google mancante.")
            verification_failed = False
            verification_unavailable = False
            try:
                claims = self.token_verifier.verify(
                    id_token, audience=self.config.client_id
                )
            except GoogleOidcProviderUnavailableError:
                verification_unavailable = True
            except Exception:
                verification_failed = True
            if verification_failed or verification_unavailable:
                id_token = None
                claims = None
                flow = None
                if verification_unavailable:
                    raise GoogleOidcProviderUnavailableError(
                        "Verifica ID token Google non disponibile."
                    )
                raise GoogleOidcTokenRejectedError(
                    "ID token Google rifiutato."
                )
            assertion = self._assertion_from_claims(claims, flow, id_token)
            claims = None
            id_token = None
            flow = None
            identity_rejected = False
            identity_unavailable = False
            try:
                user = self.identities.resolve(assertion)
            except (OnboardingNotAllowedError, AccountDisabledError):
                identity_rejected = True
            except (AuthApplicationError, IdentityDomainError):
                identity_unavailable = True
            except Exception:
                identity_unavailable = True
            assertion = None
            if identity_rejected:
                raise GoogleOidcIdentityRejectedError(
                    "Identita Google non autorizzata."
                )
            if identity_unavailable or user is None:
                raise GoogleOidcProviderUnavailableError(
                    "Servizio identita non disponibile."
                )
            session_rejected = False
            session_unavailable = False
            try:
                session = self.http_sessions.establish_session(
                    user.user_id,
                    existing_cookie_header=existing_cookie_header,
                )
            except HttpAuthenticationRequiredError:
                session_rejected = True
            except Exception:
                session_unavailable = True
            existing_cookie_header = None
            if session_rejected:
                raise GoogleOidcIdentityRejectedError(
                    "Identita Google non autorizzata."
                )
            if session_unavailable or session is None:
                raise GoogleOidcProviderUnavailableError(
                    "Servizio sessioni non disponibile."
                )
            result_failed = False
            try:
                result = GoogleOidcLoginResult(
                    user_id=session.context.user.user_id,
                    role=session.context.user.role,
                    session=session,
                    redirect_path=self.config.post_login_path,
                    clear_transaction_cookie=self._clear_transaction_cookie(
                        transaction_cookie_name
                    ),
                )
            except Exception:
                result_failed = True
            if result_failed or result is None:
                try:
                    self.http_sessions.discard_established_session(session)
                except Exception:
                    pass
                session = None
                raise GoogleOidcProviderUnavailableError(
                    "Completamento login Google non disponibile."
                )
        except GoogleOidcError as error:
            expected_error = error
        except Exception:
            unexpected_failed = True
        finally:
            parameters = None
            flow = None
            token_response = None
            id_token = None
            claims = None
            code = None
            state = None
            browser_binding = None
            transaction_cookie_name = None
            provider_error = False
            state_failed = False
            state_unavailable = False
            identity_rejected = False
            identity_unavailable = False
            session_rejected = False
            session_unavailable = False
            verification_failed = False
            verification_unavailable = False
            result_failed = False
            assertion = None
            user = None
            session = None
            existing_cookie_header = None
        if expected_error is not None:
            if flow_consumed:
                expected_error.clear_transaction_cookie = (
                    self._clear_transaction_cookie(clear_cookie_name)
                )
            raise expected_error
        if unexpected_failed or result is None:
            unavailable_error = GoogleOidcProviderUnavailableError(
                "Completamento login Google non disponibile."
            )
            if flow_consumed:
                unavailable_error.clear_transaction_cookie = (
                    self._clear_transaction_cookie(clear_cookie_name)
                )
            raise unavailable_error
        return result

    @staticmethod
    def _callback_values(
        parameters: Mapping[str, Sequence[str]],
    ) -> tuple[str, str, bool]:
        invalid = False
        code = None
        state = None
        provider_error = False
        try:
            if not isinstance(parameters, Mapping):
                invalid = True
            else:
                allowed = {
                    "code",
                    "state",
                    "error",
                    "error_description",
                    "scope",
                    "authuser",
                    "prompt",
                    "hd",
                    "iss",
                }
                if any(type(key) is not str or key not in allowed for key in parameters):
                    invalid = True
                for callback_values in parameters.values():
                    if (
                        not isinstance(callback_values, Sequence)
                        or isinstance(callback_values, (str, bytes))
                        or len(callback_values) != 1
                        or type(callback_values[0]) is not str
                        or len(callback_values[0]) > _MAX_CALLBACK_VALUE_CHARS
                        or any(ord(character) < 0x20 for character in callback_values[0])
                    ):
                        invalid = True
                issuer_values = parameters.get("iss", _MISSING_CALLBACK_VALUE)
                if issuer_values is not _MISSING_CALLBACK_VALUE and (
                    not isinstance(issuer_values, Sequence)
                    or isinstance(issuer_values, (str, bytes))
                    or len(issuer_values) != 1
                    or issuer_values[0] != _GOOGLE_AUTHORIZATION_RESPONSE_ISSUER
                ):
                    invalid = True
                values = parameters.get("state", ())
                if (
                    not isinstance(values, Sequence)
                    or isinstance(values, (str, bytes))
                    or len(values) != 1
                    or type(values[0]) is not str
                ):
                    invalid = True
                else:
                    state = values[0]
                error_values = parameters.get("error", ())
                if error_values:
                    provider_error = True
                    if "code" in parameters or not error_values[0]:
                        invalid = True
                    if (
                        not isinstance(error_values, Sequence)
                        or isinstance(error_values, (str, bytes))
                        or len(error_values) != 1
                    ):
                        invalid = True
                    code = "provider-error-placeholder"
                else:
                    code_values = parameters.get("code", ())
                    if (
                        not isinstance(code_values, Sequence)
                        or isinstance(code_values, (str, bytes))
                        or len(code_values) != 1
                        or type(code_values[0]) is not str
                    ):
                        invalid = True
                    else:
                        code = code_values[0]
                if (
                    type(state) is not str
                    or not 32 <= len(state) <= _MAX_CALLBACK_VALUE_CHARS
                    or not _UNRESERVED_RE.fullmatch(state)
                    or type(code) is not str
                    or not 1 <= len(code) <= _MAX_CALLBACK_VALUE_CHARS
                    or any(ord(character) < 0x20 for character in code)
                ):
                    invalid = True
        except Exception:
            invalid = True
        finally:
            parameters = None
            values = None
            error_values = None
            code_values = None
            callback_values = None
            issuer_values = None
        if invalid:
            code = None
            state = None
            raise GoogleOidcCallbackError("Callback Google non valida.")
        return code, state, provider_error

    def _exchange(self, code: str, verifier: str) -> Mapping[str, object]:
        failed = False
        rejected = False
        configuration_failed = False
        response = None
        form = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "redirect_uri": self.config.redirect_uri,
            "code_verifier": verifier,
        }
        try:
            response = self.token_transport.exchange_code(
                endpoint=self.config.token_endpoint,
                form=form,
                timeout_seconds=float(self.config.timeout_seconds),
                max_response_bytes=self.config.max_token_response_bytes,
            )
        except GoogleOidcTokenRejectedError:
            rejected = True
        except GoogleOidcConfigurationError:
            configuration_failed = True
        except Exception:
            failed = True
        finally:
            code = None
            verifier = None
            form = None
        if configuration_failed:
            response = None
            raise GoogleOidcConfigurationError(
                "Configurazione token Google rifiutata."
            )
        if rejected:
            response = None
            raise GoogleOidcTokenRejectedError(
                "Authorization code Google rifiutato."
            )
        if failed or not isinstance(response, Mapping):
            response = None
            raise GoogleOidcProviderUnavailableError("Token exchange Google fallito.")
        return response

    def _assertion_from_claims(
        self,
        claims: Mapping[str, object],
        flow: PendingGoogleOidcFlow,
        id_token: str,
    ) -> FederatedIdentityAssertion:
        invalid = False
        unavailable = False
        assertion = None
        try:
            if not isinstance(claims, Mapping):
                invalid = True
                known = {}
            else:
                known = {
                    key: claims.get(key)
                    for key in (
                        "iss", "aud", "azp", "sub", "email", "email_verified",
                        "name", "nonce", "exp", "iat",
                    )
                }
            try:
                now = _utc(self.clock())
            except Exception:
                unavailable = True
                now = None
            issuer = known.get("iss")
            audience = known.get("aud")
            authorized_party = known.get("azp")
            subject = known.get("sub")
            email = known.get("email")
            email_verified = known.get("email_verified")
            display_name = known.get("name")
            nonce = known.get("nonce")
            expires_at = known.get("exp")
            issued_at = known.get("iat")
            if issuer not in _GOOGLE_ISSUERS:
                invalid = True
            if type(audience) is str:
                audience_valid = hmac.compare_digest(audience, self.config.client_id)
            elif type(audience) is list and all(type(item) is str for item in audience):
                audience_valid = self.config.client_id in audience
                if len(audience) > 1 and authorized_party != self.config.client_id:
                    audience_valid = False
            else:
                audience_valid = False
            if (
                not audience_valid
                or (
                    authorized_party is not None
                    and authorized_party != self.config.client_id
                )
            ):
                invalid = True
            if (
                type(subject) is not str or not subject.strip()
                or len(subject) > 255
                or any(ord(character) < 0x21 or ord(character) > 0x7E for character in subject)
                or type(email) is not str or not email.strip()
                or any(ord(character) < 0x20 for character in email)
                or email_verified is not True
                or type(nonce) is not str
                or not hmac.compare_digest(
                    InMemoryGoogleOidcFlowStore.nonce_digest(nonce), flow.nonce_digest
                )
            ):
                invalid = True
            if (
                unavailable
                or type(expires_at) not in {int, float}
                or type(issued_at) not in {int, float}
            ):
                invalid = True
            else:
                expires_value = float(expires_at)
                issued_value = float(issued_at)
                now_timestamp = now.timestamp()
                skew = self.config.clock_skew.total_seconds()
                if (
                    not math.isfinite(expires_value)
                    or not math.isfinite(issued_value)
                    or expires_value <= issued_value
                    or now_timestamp >= expires_value + skew
                    or issued_value > now_timestamp + skew
                    or now_timestamp - issued_value
                    > self.config.id_token_max_age.total_seconds() + skew
                ):
                    invalid = True
            secret_echoes = (
                issuer,
                authorized_party,
                subject,
                email,
                email_verified,
                display_name,
                nonce,
                expires_at,
                issued_at,
            )
            if (
                any(
                    type(value) is str and id_token in value
                    for value in secret_echoes
                )
                or (
                    type(audience) is list
                    and any(
                        type(value) is str and id_token in value
                        for value in audience
                    )
                )
                or (type(audience) is str and id_token in audience)
            ):
                invalid = True
            if not invalid:
                normalized_name = display_name.strip() if type(display_name) is str and display_name.strip() else email.strip()
                assertion = FederatedIdentityAssertion(
                    provider="google",
                    subject=subject.strip(),
                    display_name=normalized_name,
                    email=email.strip().lower(),
                    email_verified=True,
                )
        except Exception:
            invalid = True
        finally:
            claims = None
            flow = None
            id_token = None
            known = None
            now = None
            issuer = None
            audience = None
            audience_valid = None
            authorized_party = None
            nonce = None
            subject = None
            email = None
            email_verified = None
            display_name = None
            expires_at = None
            issued_at = None
            expires_value = None
            issued_value = None
            now_timestamp = None
            skew = None
            normalized_name = None
            secret_echoes = None
        if unavailable:
            assertion = None
            raise GoogleOidcProviderUnavailableError(
                "Clock verifica claim non disponibile."
            )
        if invalid or assertion is None:
            assertion = None
            raise GoogleOidcTokenRejectedError("Claim ID token Google non validi.")
        return assertion
