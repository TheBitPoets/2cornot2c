"""Concrete HTTP semantics for Google OIDC login and callback routes."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence

from scripts.thebitlab_edge_rate_limit import (
    EdgeClientAttributionError,
    EdgeRateLimitExceededError,
    EdgeRateLimitUnavailableError,
    EdgeRequestMetadata,
    GoogleOidcLoginAdmissionBoundary,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_http_auth import SessionCookiePolicy
from scripts.thebitlab_google_oidc import (
    GoogleAuthorizationRequest,
    GoogleOidcCallbackError,
    GoogleOidcConfigurationError,
    GoogleOidcError,
    GoogleOidcIdentityRejectedError,
    GoogleOidcLoginResult,
    GoogleOidcProviderUnavailableError,
    GoogleOidcStateError,
    GoogleOidcTokenRejectedError,
)


_LOGIN_PATH = "/auth/google/login"
_CALLBACK_PATH = "/auth/google/callback"
_MAX_QUERY_BYTES = 8192
_MAX_QUERY_FIELDS = 16
_MAX_COOKIE_HEADER_BYTES = 16_384
_MAX_RESPONSE_HEADER_BYTES = 16_384
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_COOKIE_VALUE_RE = re.compile(r"^[A-Za-z0-9_-]{32,1024}$")
_TRANSACTION_COOKIE_NAME_RE = re.compile(
    r"^__Host-thebitlab_oidc_txn-[0-9a-f]{24}$"
)


@dataclass(frozen=True)
class GoogleOidcHttpRequest:
    method: str
    path: str
    query: str = field(repr=False, compare=False)
    edge: EdgeRequestMetadata
    is_tls: bool = False

    def __post_init__(self) -> None:
        if type(self.method) is not str or not self.method or len(self.method) > 16:
            raise ValueError("Metodo HTTP non valido.")
        if type(self.path) is not str or not self.path.startswith("/") or len(self.path) > 256:
            raise ValueError("Path HTTP non valido.")
        if type(self.query) is not str or len(
            self.query.encode("utf-8", errors="surrogatepass")
        ) > _MAX_QUERY_BYTES:
            raise ValueError("Query HTTP non valida.")
        if type(self.edge) is not EdgeRequestMetadata or type(self.is_tls) is not bool:
            raise ValueError("Metadati HTTP non validi.")


class GoogleOidcDeliveryGuard:
    """Discard one issued session unless the HTTP response is delivered."""

    def __init__(
        self, discarder: EstablishedSessionDiscarder, established: object
    ) -> None:
        self._discarder = discarder
        self._established = established

    def delivered(self) -> None:
        self._established = None
        self._discarder = None

    def failed(self) -> None:
        established = self._established
        discarder = self._discarder
        self._established = None
        self._discarder = None
        if established is None or discarder is None:
            return
        try:
            discarder.discard_established_session(established)
        except Exception:
            pass


@dataclass(frozen=True)
class GoogleOidcHttpResponse:
    status_code: int
    headers: tuple[tuple[str, str], ...] = field(repr=False, compare=False)
    body: bytes = field(repr=False, compare=False)
    delivery_guard: GoogleOidcDeliveryGuard | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if type(self.status_code) is not int or not 100 <= self.status_code <= 599:
            raise ValueError("Status HTTP non valido.")
        if type(self.headers) is not tuple or len(self.headers) > 32:
            raise ValueError("Header risposta non validi.")
        total = 0
        for item in self.headers:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
                or _HEADER_NAME_RE.fullmatch(item[0]) is None
                or any(ord(character) < 32 or ord(character) == 127 for character in item[1])
            ):
                raise ValueError("Header risposta non validi.")
            try:
                encoded_value = item[1].encode("latin-1")
            except UnicodeEncodeError:
                raise ValueError("Header risposta non serializzabile.") from None
            total += len(item[0].encode("ascii")) + len(encoded_value) + 4
        if (
            total > _MAX_RESPONSE_HEADER_BYTES
            or type(self.body) is not bytes
            or len(self.body) > 4096
            or (
                self.delivery_guard is not None
                and type(self.delivery_guard) is not GoogleOidcDeliveryGuard
            )
        ):
            raise ValueError("Risposta HTTP non valida.")


class EstablishedSessionDiscarder(Protocol):
    def discard_established_session(self, established: object) -> bool: ...


class GoogleCallbackCompleter(Protocol):
    def complete_callback(
        self,
        parameters: Mapping[str, Sequence[str]],
        *,
        existing_cookie_header: str | None = None,
    ) -> GoogleOidcLoginResult: ...


class GoogleOidcHttpRoutes:
    """Dispatch the two public Google OIDC routes with strict HTTP policy."""

    def __init__(
        self,
        admission: GoogleOidcLoginAdmissionBoundary,
        callback: GoogleCallbackCompleter,
        proxy_resolver: TrustedProxyClientResolver,
        session_discarder: EstablishedSessionDiscarder,
        *,
        session_cookie_policy: SessionCookiePolicy = SessionCookiePolicy(),
    ) -> None:
        if (
            type(session_cookie_policy) is not SessionCookiePolicy
            or not session_cookie_policy.secure
            or session_cookie_policy.allow_insecure_loopback
            or not session_cookie_policy.name.startswith("__Host-")
        ):
            raise ValueError("Policy cookie sessione non valida per route HTTPS.")
        callback_http = getattr(callback, "http_sessions", None)
        callback_policy = getattr(callback_http, "cookie_policy", None)
        if callback_policy is not None and callback_policy != session_cookie_policy:
            raise ValueError("Policy cookie callback non coerente.")
        if callback_http is not None and session_discarder is not callback_http:
            raise ValueError("Discarder sessione callback non coerente.")
        self.admission = admission
        self.callback = callback
        self.proxy_resolver = proxy_resolver
        self.session_discarder = session_discarder
        self.session_cookie_policy = session_cookie_policy

    def handles(self, path: str) -> bool:
        return path in {_LOGIN_PATH, _CALLBACK_PATH}

    def dispatch(self, request: GoogleOidcHttpRequest) -> GoogleOidcHttpResponse | None:
        if type(request) is not GoogleOidcHttpRequest:
            return self._error(400, "bad_auth_request", "Richiesta non valida.")
        if not self.handles(request.path):
            return None
        try:
            self._require_https(request)
            self._require_empty_body(request.edge)
            if request.method != "GET":
                return self._error(
                    405,
                    "auth_method_not_allowed",
                    "Metodo non consentito.",
                    (("Allow", "GET"),),
                )
            if request.path == _LOGIN_PATH:
                return self._login(request)
            return self._callback(request)
        except EdgeClientAttributionError:
            return self._error(400, "invalid_client_address", "Indirizzo client non valido.")
        except EdgeRateLimitExceededError as error:
            return self._error(
                429,
                error.error_code,
                error.public_message,
                (("Retry-After", str(error.retry_after_seconds)),),
            )
        except EdgeRateLimitUnavailableError:
            return self._error(
                503,
                "auth_admission_unavailable",
                "Servizio di autenticazione temporaneamente non disponibile.",
            )
        except _HttpRequestError as error:
            return self._error(error.status_code, error.error_code, error.public_message)
        except Exception:
            return self._error(
                503,
                "authentication_unavailable",
                "Servizio di autenticazione temporaneamente non disponibile.",
            )
        finally:
            request = None

    def _login(self, request: GoogleOidcHttpRequest) -> GoogleOidcHttpResponse:
        if request.query:
            raise _HttpRequestError(400, "bad_auth_request", "Query non consentita.")
        started = None
        try:
            started = self.admission.begin_login(request.edge)
            if type(started) is not GoogleAuthorizationRequest:
                raise EdgeRateLimitUnavailableError()
            location = _redirect_location(started.authorization_url, absolute_https=True)
            transaction_cookie = _validated_cookie(
                started.set_cookie, kind="transaction"
            )
            response = GoogleOidcHttpResponse(
                302,
                (
                    ("Location", location),
                    ("Set-Cookie", transaction_cookie),
                    ("Cache-Control", "no-store"),
                    ("Pragma", "no-cache"),
                    ("Referrer-Policy", "no-referrer"),
                    ("Content-Length", "0"),
                ),
                b"",
            )
        finally:
            started = None
        return response

    def _callback(self, request: GoogleOidcHttpRequest) -> GoogleOidcHttpResponse:
        parameters = None
        cookie_header = None
        result = None
        try:
            parameters = _callback_query(request.query)
            cookie_header = _combined_cookie_header(request.edge.headers)
            try:
                result = self.callback.complete_callback(
                    parameters,
                    existing_cookie_header=cookie_header,
                )
            except GoogleOidcError as error:
                clear_cookie = getattr(error, "clear_transaction_cookie", None)
                return self._oidc_error(error, clear_cookie)
            if type(result) is not GoogleOidcLoginResult:
                raise GoogleOidcProviderUnavailableError(
                    "Risultato callback non valido."
                )
            try:
                location = _redirect_location(
                    result.redirect_path, absolute_https=False
                )
                session_cookie = _validated_cookie(
                    result.session.set_cookie,
                    kind="session",
                    session_policy=self.session_cookie_policy,
                )
                clear_cookie = _validated_cookie(
                    result.clear_transaction_cookie,
                    kind="clear_transaction",
                )
                response = GoogleOidcHttpResponse(
                    303,
                    (
                        ("Location", location),
                        ("Set-Cookie", session_cookie),
                        ("Set-Cookie", clear_cookie),
                        ("Cache-Control", "no-store"),
                        ("Pragma", "no-cache"),
                        ("Referrer-Policy", "no-referrer"),
                        ("Content-Length", "0"),
                    ),
                    b"",
                    GoogleOidcDeliveryGuard(
                        self.session_discarder, result.session
                    ),
                )
            except Exception:
                cleanup_header: tuple[tuple[str, str], ...] = ()
                try:
                    cleanup_header = ((
                        "Set-Cookie",
                        _validated_cookie(
                            result.clear_transaction_cookie,
                            kind="clear_transaction",
                        ),
                    ),)
                except Exception:
                    cleanup_header = ()
                try:
                    self.session_discarder.discard_established_session(
                        result.session
                    )
                except Exception:
                    pass
                return self._error(
                    503,
                    "authentication_unavailable",
                    "Servizio di autenticazione temporaneamente non disponibile.",
                    cleanup_header,
                )
        finally:
            request = None
            parameters = None
            cookie_header = None
            result = None
        return response

    def _oidc_error(
        self, error: GoogleOidcError, clear_cookie: object
    ) -> GoogleOidcHttpResponse:
        extra_headers: tuple[tuple[str, str], ...] = ()
        if clear_cookie is not None:
            try:
                extra_headers = ((
                    "Set-Cookie",
                    _validated_cookie(clear_cookie, kind="clear_transaction"),
                ),)
            except Exception:
                return self._error(
                    503,
                    "authentication_unavailable",
                    "Servizio di autenticazione temporaneamente non disponibile.",
                )
        if isinstance(error, GoogleOidcIdentityRejectedError):
            return self._error(403, "identity_rejected", "Identità non autorizzata.", extra_headers)
        if isinstance(error, GoogleOidcProviderUnavailableError) or isinstance(
            error, GoogleOidcConfigurationError
        ):
            return self._error(
                503,
                "authentication_unavailable",
                "Servizio di autenticazione temporaneamente non disponibile.",
                extra_headers,
            )
        if isinstance(error, GoogleOidcStateError):
            return self._error(400, "invalid_oauth_state", "Sessione login non valida.", extra_headers)
        if isinstance(error, (GoogleOidcCallbackError, GoogleOidcTokenRejectedError)):
            return self._error(400, "invalid_oauth_callback", "Callback login non valida.", extra_headers)
        return self._error(
            503,
            "authentication_unavailable",
            "Servizio di autenticazione temporaneamente non disponibile.",
            extra_headers,
        )

    def _require_https(self, request: GoogleOidcHttpRequest) -> None:
        if request.is_tls:
            return
        if not self.proxy_resolver.is_trusted_peer(request.edge):
            raise _HttpRequestError(400, "https_required", "HTTPS obbligatorio.")
        values = [
            value.strip().lower()
            for name, value in request.edge.headers
            if name.lower() == "x-forwarded-proto"
        ]
        if values != ["https"]:
            raise _HttpRequestError(400, "https_required", "HTTPS obbligatorio.")

    @staticmethod
    def _require_empty_body(edge: EdgeRequestMetadata) -> None:
        lengths = [value.strip() for name, value in edge.headers if name.lower() == "content-length"]
        transfers = [value for name, value in edge.headers if name.lower() == "transfer-encoding"]
        if transfers or len(lengths) > 1 or (lengths and lengths != ["0"]):
            raise _HttpRequestError(400, "bad_auth_request", "Body non consentito.")

    @staticmethod
    def _error(
        status_code: int,
        error_code: str,
        public_message: str,
        extra_headers: tuple[tuple[str, str], ...] = (),
    ) -> GoogleOidcHttpResponse:
        body = json.dumps(
            {"error": error_code, "message": public_message},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        headers = extra_headers + (
            ("Content-Type", "application/json; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("Referrer-Policy", "no-referrer"),
            ("Content-Length", str(len(body))),
        )
        return GoogleOidcHttpResponse(status_code, headers, body)


class _HttpRequestError(RuntimeError):
    def __init__(self, status_code: int, error_code: str, public_message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.public_message = public_message
        super().__init__(public_message)


def _callback_query(raw_query: str) -> dict[str, tuple[str, ...]]:
    parsed: dict[str, list[str]] | None = None
    result = None
    try:
        if (
            type(raw_query) is not str
            or not raw_query
            or len(raw_query.encode("utf-8", errors="surrogatepass")) > _MAX_QUERY_BYTES
            or "#" in raw_query
            or _PERCENT_ESCAPE_RE.search(raw_query) is not None
        ):
            raise _HttpRequestError(400, "bad_auth_request", "Query callback non valida.")
        try:
            parsed = urllib.parse.parse_qs(
                raw_query,
                keep_blank_values=True,
                strict_parsing=True,
                max_num_fields=_MAX_QUERY_FIELDS,
                encoding="utf-8",
                errors="strict",
            )
        except (UnicodeError, ValueError):
            raise _HttpRequestError(
                400, "bad_auth_request", "Query callback non valida."
            ) from None
        result = {key: tuple(values) for key, values in parsed.items()}
        return result
    finally:
        raw_query = None
        parsed = None
        result = None


def _combined_cookie_header(headers: tuple[tuple[str, str], ...]) -> str | None:
    values = None
    combined = None
    try:
        values = [value for name, value in headers if name.lower() == "cookie"]
        if not values:
            return None
        combined = "; ".join(values)
        if (
            len(combined.encode("utf-8", errors="surrogatepass")) > _MAX_COOKIE_HEADER_BYTES
            or any(ord(character) < 32 or ord(character) == 127 for character in combined)
        ):
            raise _HttpRequestError(400, "bad_auth_request", "Cookie non valido.")
        return combined
    finally:
        headers = ()
        values = None
        combined = None


def _redirect_location(value: object, *, absolute_https: bool) -> str:
    if type(value) is not str or not value or len(value) > 8192:
        raise ValueError("Redirect non valido.")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("Redirect non valido.")
    parsed = urllib.parse.urlsplit(value)
    if absolute_https:
        try:
            port = parsed.port
        except ValueError:
            raise ValueError("Redirect non valido.") from None
        if (
            parsed.scheme != "https"
            or parsed.hostname != "accounts.google.com"
            or parsed.username is not None
            or parsed.password is not None
            or port not in {None, 443}
            or parsed.path != "/o/oauth2/v2/auth"
            or not parsed.query
            or parsed.fragment
        ):
            raise ValueError("Redirect non valido.")
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("Redirect non valido.") from None
        return value
    if (
        not value.startswith("/")
        or value.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Redirect non valido.")
    if _PERCENT_ESCAPE_RE.search(value) is not None:
        raise ValueError("Redirect non valido.")
    return urllib.parse.quote(value, safe="/-._~!$&'()*+,;=:@%")


def _validated_cookie(
    value: object,
    *,
    kind: str,
    session_policy: SessionCookiePolicy | None = None,
) -> str:
    if (
        type(value) is not str
        or not value
        or len(value.encode("utf-8", errors="surrogatepass")) > 4096
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("Cookie risposta non valido.")
    parts = [part.strip() for part in value.split(";")]
    if not parts or "=" not in parts[0] or any(not part for part in parts):
        raise ValueError("Cookie risposta non valido.")
    name, cookie_value = parts[0].split("=", 1)
    expected_name = (
        session_policy.name
        if kind == "session" and type(session_policy) is SessionCookiePolicy
        else None
    )
    if kind in {"transaction", "clear_transaction"}:
        valid_name = _TRANSACTION_COOKIE_NAME_RE.fullmatch(name) is not None
    else:
        valid_name = kind == "session" and name == expected_name
    flags: set[str] = set()
    attributes: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, attribute_value = part.split("=", 1)
            lowered = key.lower()
            if lowered in attributes or lowered in flags:
                raise ValueError("Cookie risposta non valido.")
            attributes[lowered] = attribute_value
        else:
            lowered = part.lower()
            if lowered in flags or lowered in attributes:
                raise ValueError("Cookie risposta non valido.")
            flags.add(lowered)
    if (
        not valid_name
        or flags != {"secure", "httponly"}
        or attributes.get("path") != "/"
        or set(attributes) - {"path", "samesite", "max-age", "expires"}
    ):
        raise ValueError("Cookie risposta non valido.")
    expected_same_site = (
        session_policy.same_site.lower()
        if kind == "session" and type(session_policy) is SessionCookiePolicy
        else "lax"
    )
    if attributes.get("samesite", "").lower() != expected_same_site:
        raise ValueError("Cookie risposta non valido.")
    max_age = attributes.get("max-age")
    if kind == "clear_transaction":
        valid_value = cookie_value == "" and max_age == "0" and "expires" in attributes
    else:
        valid_value = (
            _COOKIE_VALUE_RE.fullmatch(cookie_value) is not None
            and max_age is not None
            and max_age.isdigit()
            and 1 <= int(max_age) <= 2_678_400
        )
    if not valid_value:
        raise ValueError("Cookie risposta non valido.")
    return value
