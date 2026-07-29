"""Concrete authenticated HTTP routes for GitHub account linking."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from scripts.thebitlab_edge_rate_limit import (
    EdgeClientAttributionError,
    EdgeRequestMetadata,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_github_oauth import (
    GitHubAccountLinkService,
    GitHubLinkAuthorizationRequest,
    GitHubLinkCallbackError,
    GitHubLinkCapacityError,
    GitHubLinkConfigurationError,
    GitHubLinkConsumedStateError,
    GitHubLinkError,
    GitHubLinkIdentityConflictError,
    GitHubLinkProviderRejectedError,
    GitHubLinkProviderUnavailableError,
    GitHubLinkResult,
    GitHubLinkStateError,
)
from scripts.thebitlab_http_auth import (
    HttpAuthError,
    HttpAuthRequest,
    HttpSessionAuthBoundary,
)
from scripts.thebitlab_identity import ExternalIdentity

_LINK_PATH = "/auth/github/link"
_CALLBACK_PATH = "/auth/github/callback"
_UNLINK_PATH = "/auth/github/unlink"
_MAX_QUERY_BYTES = 8192
_MAX_QUERY_FIELDS = 16
_MAX_COOKIE_HEADER_BYTES = 16_384
_MAX_RESPONSE_HEADER_BYTES = 16_384
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_TRANSACTION_COOKIE_RE = re.compile(r"^__Host-thebitlab_github_link-[0-9a-f]{24}$")
_COOKIE_VALUE_RE = re.compile(r"^[A-Za-z0-9_-]{32,256}$")


@dataclass(frozen=True)
class GitHubOAuthHttpRequest:
    method: str
    path: str
    query: str = field(repr=False, compare=False)
    edge: EdgeRequestMetadata
    is_tls: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.method) is not str
            or not self.method
            or len(self.method) > 65_535
            or _HEADER_NAME_RE.fullmatch(self.method) is None
            or type(self.path) is not str
            or not self.path.startswith("/")
            or len(self.path) > 256
            or type(self.query) is not str
            or len(self.query.encode("utf-8", errors="surrogatepass")) > _MAX_QUERY_BYTES
            or type(self.edge) is not EdgeRequestMetadata
            or type(self.is_tls) is not bool
        ):
            raise ValueError("Richiesta GitHub HTTP non valida.")


@dataclass(frozen=True)
class GitHubOAuthHttpResponse:
    status_code: int
    headers: tuple[tuple[str, str], ...] = field(repr=False, compare=False)
    body: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.status_code) is not int or not 100 <= self.status_code <= 599:
            raise ValueError("Risposta GitHub HTTP non valida.")
        if type(self.headers) is not tuple or len(self.headers) > 32:
            raise ValueError("Risposta GitHub HTTP non valida.")
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
                raise ValueError("Risposta GitHub HTTP non valida.")
            try:
                encoded = item[1].encode("latin-1")
            except UnicodeEncodeError:
                raise ValueError("Risposta GitHub HTTP non serializzabile.") from None
            total += len(item[0]) + len(encoded) + 4
        if total > _MAX_RESPONSE_HEADER_BYTES or type(self.body) is not bytes or len(self.body) > 4096:
            raise ValueError("Risposta GitHub HTTP non valida.")


class GitHubOAuthHttpRoutes:
    """Link, callback, and unlink routes bound to an authenticated web session."""

    def __init__(
        self,
        service: GitHubAccountLinkService,
        http_sessions: HttpSessionAuthBoundary,
        proxy_resolver: TrustedProxyClientResolver,
    ) -> None:
        if (
            type(service) is not GitHubAccountLinkService
            or type(http_sessions) is not HttpSessionAuthBoundary
            or type(proxy_resolver) is not TrustedProxyClientResolver
        ):
            raise ValueError("Router GitHub non valido.")
        self.service = service
        self.http_sessions = http_sessions
        self.proxy_resolver = proxy_resolver

    def handles(self, path: str) -> bool:
        return path in {_LINK_PATH, _CALLBACK_PATH, _UNLINK_PATH}

    def dispatch(self, request: GitHubOAuthHttpRequest) -> GitHubOAuthHttpResponse | None:
        if type(request) is not GitHubOAuthHttpRequest:
            return self._error(400, "bad_auth_request", "Richiesta non valida.")
        if not self.handles(request.path):
            return None
        cleanup_cookie = None
        try:
            self._require_https(request)
            self._require_empty_body(request.edge)
            expected_method = "POST" if request.path == _UNLINK_PATH else "GET"
            if request.method != expected_method:
                return self._error(
                    405,
                    "auth_method_not_allowed",
                    "Metodo non consentito.",
                    (("Allow", expected_method),),
                )
            if request.path == _LINK_PATH:
                return self._begin(request)
            if request.path == _CALLBACK_PATH:
                return self._callback(request)
            return self._unlink(request)
        except HttpAuthError as error:
            return self._error(error.status_code, error.error_code, error.public_message)
        except _GitHubHttpRequestError as error:
            return self._error(error.status_code, error.error_code, error.public_message)
        except GitHubLinkError as error:
            cleanup_cookie = getattr(error, "clear_transaction_cookie", None)
            extra = ()
            if cleanup_cookie is not None:
                extra = (("Set-Cookie", _validated_transaction_cookie(cleanup_cookie, clear=True)),)
            if isinstance(error, (GitHubLinkStateError, GitHubLinkCallbackError, GitHubLinkConsumedStateError)):
                return self._error(400, "invalid_oauth_callback", "Callback GitHub non valida.", extra)
            if isinstance(error, GitHubLinkIdentityConflictError):
                return self._error(409, "github_identity_conflict", "Account GitHub non collegabile.", extra)
            if isinstance(error, GitHubLinkProviderRejectedError):
                return self._error(400, "github_provider_rejected", "Risposta GitHub non valida.", extra)
            if isinstance(error, GitHubLinkCapacityError):
                return self._error(503, "github_link_capacity", "Servizio GitHub temporaneamente non disponibile.", extra)
            if isinstance(error, (GitHubLinkProviderUnavailableError, GitHubLinkConfigurationError)):
                return self._error(503, "github_link_unavailable", "Servizio GitHub temporaneamente non disponibile.", extra)
            return self._error(503, "github_link_unavailable", "Servizio GitHub temporaneamente non disponibile.", extra)
        except EdgeClientAttributionError:
            return self._error(400, "invalid_client_address", "Indirizzo client non valido.")
        except Exception:
            return self._error(503, "github_link_unavailable", "Servizio GitHub temporaneamente non disponibile.")
        finally:
            request = None
            cleanup_cookie = None

    def _context(self, request: GitHubOAuthHttpRequest, *, csrf: bool = False):
        cookie = _combined_cookie_header(request.edge.headers)
        csrf_token = _single_header(request.edge.headers, "x-csrf-token") if csrf else None
        try:
            return self.http_sessions.authenticate(
                HttpAuthRequest(request.method, cookie_header=cookie, csrf_token=csrf_token)
            )
        finally:
            cookie = None
            csrf_token = None

    def _begin(self, request: GitHubOAuthHttpRequest) -> GitHubOAuthHttpResponse:
        if request.query:
            raise _GitHubHttpRequestError(400, "bad_auth_request", "Query non consentita.")
        started = self.service.begin_link(self._context(request))
        if type(started) is not GitHubLinkAuthorizationRequest:
            raise GitHubLinkProviderUnavailableError("Avvio linking non valido.")
        location = _github_authorization_location(started.authorization_url)
        cookie = _validated_transaction_cookie(started.set_cookie)
        return GitHubOAuthHttpResponse(
            302,
            (
                ("Location", location),
                ("Set-Cookie", cookie),
                ("Cache-Control", "no-store"),
                ("Pragma", "no-cache"),
                ("Referrer-Policy", "no-referrer"),
                ("Content-Length", "0"),
            ),
            b"",
        )

    def _callback(self, request: GitHubOAuthHttpRequest) -> GitHubOAuthHttpResponse:
        parameters = _callback_query(request.query)
        cookie = _combined_cookie_header(request.edge.headers)
        context = self._context(request)
        expected_user_id = context.user.user_id
        try:
            result = self.service.complete_link(parameters, cookie_header=cookie, context=context)
        finally:
            parameters = None
            cookie = None
            context = None
        if (
            type(result) is not GitHubLinkResult
            or type(result.identity) is not ExternalIdentity
            or result.identity.provider != "github"
            or result.identity.user_id != expected_user_id
        ):
            raise GitHubLinkProviderUnavailableError("Risultato linking non valido.")
        location = _local_redirect(result.redirect_path)
        clear_cookie = _validated_transaction_cookie(result.clear_transaction_cookie, clear=True)
        return GitHubOAuthHttpResponse(
            303,
            (
                ("Location", location),
                ("Set-Cookie", clear_cookie),
                ("Cache-Control", "no-store"),
                ("Pragma", "no-cache"),
                ("Referrer-Policy", "no-referrer"),
                ("Content-Length", "0"),
            ),
            b"",
        )

    def _unlink(self, request: GitHubOAuthHttpRequest) -> GitHubOAuthHttpResponse:
        if request.query:
            raise _GitHubHttpRequestError(400, "bad_auth_request", "Query non consentita.")
        context = self._context(request, csrf=True)
        identity = self.service.links.unlink(
            context.user.user_id,
            expected_session=context.session,
        )
        if (
            type(identity) is not ExternalIdentity
            or identity.provider != "github"
            or identity.user_id != context.user.user_id
        ):
            raise GitHubLinkProviderUnavailableError("Risultato unlink non valido.")
        return GitHubOAuthHttpResponse(
            204,
            (
                ("Cache-Control", "no-store"),
                ("Pragma", "no-cache"),
                ("Referrer-Policy", "no-referrer"),
                ("Content-Length", "0"),
            ),
            b"",
        )

    def _require_https(self, request: GitHubOAuthHttpRequest) -> None:
        if request.is_tls:
            return
        if not self.proxy_resolver.is_trusted_peer(request.edge):
            raise _GitHubHttpRequestError(400, "https_required", "HTTPS obbligatorio.")
        forwarded = [
            value.strip().lower()
            for name, value in request.edge.headers
            if name.lower() == "x-forwarded-proto"
        ]
        if forwarded != ["https"]:
            raise _GitHubHttpRequestError(400, "https_required", "HTTPS obbligatorio.")

    @staticmethod
    def _require_empty_body(edge: EdgeRequestMetadata) -> None:
        lengths = [value.strip() for name, value in edge.headers if name.lower() == "content-length"]
        transfers = [value for name, value in edge.headers if name.lower() == "transfer-encoding"]
        if transfers or len(lengths) > 1 or (lengths and lengths != ["0"]):
            raise _GitHubHttpRequestError(400, "bad_auth_request", "Body non consentito.")

    @staticmethod
    def _error(
        status_code: int,
        error_code: str,
        message: str,
        extra_headers: tuple[tuple[str, str], ...] = (),
    ) -> GitHubOAuthHttpResponse:
        body = json.dumps(
            {"error": error_code, "message": message},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return GitHubOAuthHttpResponse(
            status_code,
            extra_headers
            + (
                ("Content-Type", "application/json; charset=utf-8"),
                ("Cache-Control", "no-store"),
                ("Referrer-Policy", "no-referrer"),
                ("Content-Length", str(len(body))),
            ),
            body,
        )


class _GitHubHttpRequestError(RuntimeError):
    def __init__(self, status_code: int, error_code: str, public_message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.public_message = public_message
        super().__init__(public_message)


def _single_header(headers: tuple[tuple[str, str], ...], name: str) -> str | None:
    values = [value for key, value in headers if key.lower() == name]
    if len(values) != 1:
        return None
    value = values[0]
    if not value or len(value) > 4096 or any(ord(character) < 0x21 or ord(character) == 0x7F for character in value):
        raise _GitHubHttpRequestError(400, "bad_auth_request", "Header non valido.")
    return value


def _combined_cookie_header(headers: tuple[tuple[str, str], ...]) -> str | None:
    values = [value for name, value in headers if name.lower() == "cookie"]
    if not values:
        return None
    combined = "; ".join(values)
    if (
        len(combined.encode("utf-8", errors="surrogatepass")) > _MAX_COOKIE_HEADER_BYTES
        or any(ord(character) < 32 or ord(character) == 127 for character in combined)
    ):
        raise _GitHubHttpRequestError(400, "bad_auth_request", "Cookie non valido.")
    return combined


def _callback_query(raw_query: str) -> dict[str, tuple[str, ...]]:
    if (
        type(raw_query) is not str
        or not raw_query
        or len(raw_query.encode("utf-8", errors="surrogatepass")) > _MAX_QUERY_BYTES
        or "#" in raw_query
        or _PERCENT_ESCAPE_RE.search(raw_query) is not None
    ):
        raise _GitHubHttpRequestError(400, "bad_auth_request", "Query callback non valida.")
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
        raise _GitHubHttpRequestError(400, "bad_auth_request", "Query callback non valida.") from None
    return {key: tuple(values) for key, values in parsed.items()}


def _github_authorization_location(value: object) -> str:
    if type(value) is not str or not value or len(value) > 8192:
        raise ValueError("Redirect GitHub non valido.")
    parsed = urllib.parse.urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise ValueError("Redirect GitHub non valido.") from None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or parsed.path != "/login/oauth/authorize"
        or not parsed.query
        or parsed.fragment
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("Redirect GitHub non valido.")
    value.encode("ascii")
    return value


def _local_redirect(value: object) -> str:
    if type(value) is not str or not value or len(value) > 2048:
        raise ValueError("Redirect locale non valido.")
    parsed = urllib.parse.urlsplit(value)
    if (
        not value.startswith("/")
        or value.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or _PERCENT_ESCAPE_RE.search(value) is not None
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("Redirect locale non valido.")
    return urllib.parse.quote(value, safe="/-._~!$&'()*+,;=:@%")


def _validated_transaction_cookie(value: object, *, clear: bool = False) -> str:
    if (
        type(value) is not str
        or not value
        or len(value.encode("utf-8", errors="surrogatepass")) > 4096
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("Cookie GitHub non valido.")
    parts = [part.strip() for part in value.split(";")]
    if not parts or "=" not in parts[0] or any(not part for part in parts):
        raise ValueError("Cookie GitHub non valido.")
    name, cookie_value = parts[0].split("=", 1)
    flags: set[str] = set()
    attributes: dict[str, str] = {}
    for part in parts[1:]:
        if "=" in part:
            key, attribute = part.split("=", 1)
            lowered = key.lower()
            if lowered in attributes or lowered in flags:
                raise ValueError("Cookie GitHub non valido.")
            attributes[lowered] = attribute
        else:
            lowered = part.lower()
            if lowered in attributes or lowered in flags:
                raise ValueError("Cookie GitHub non valido.")
            flags.add(lowered)
    if (
        _TRANSACTION_COOKIE_RE.fullmatch(name) is None
        or flags != {"secure", "httponly"}
        or attributes.get("path") != "/"
        or attributes.get("samesite", "").lower() != "lax"
        or set(attributes) - {"path", "samesite", "max-age", "expires"}
    ):
        raise ValueError("Cookie GitHub non valido.")
    if clear:
        valid = cookie_value == "" and attributes.get("max-age") == "0" and "expires" in attributes
    else:
        max_age = attributes.get("max-age", "")
        valid = _COOKIE_VALUE_RE.fullmatch(cookie_value) is not None and max_age.isdigit() and 1 <= int(max_age) <= 1800
    if not valid:
        raise ValueError("Cookie GitHub non valido.")
    return value
