"""Concrete HTTPS routes for current web session status and logout."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scripts.thebitlab_admin_provisioning import (
    AdminProvisioningConflictError,
    AdminProvisioningService,
)
from scripts.thebitlab_edge_rate_limit import (
    EdgeClientAttributionError,
    EdgeRequestMetadata,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_http_auth import (
    HttpAuthError,
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpBadRequestError,
    HttpCsrfRejectedError,
    HttpMethodNotAllowedError,
    HttpSessionAuthBoundary,
)

_SESSION_PATH = "/auth/session"
_ACCOUNT_PATH = "/auth/account"
_ADMIN_PATH = "/auth/admin"
_LOGOUT_PATH = "/auth/logout"
_MAX_COOKIE_HEADER_BYTES = 16 * 1024
_CSRF_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")


@dataclass(frozen=True)
class SessionHttpRequest:
    method: str
    path: str
    raw_query: str = field(default="", repr=False)
    edge: EdgeRequestMetadata = field(default=None, repr=False)
    is_tls: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.method) is not str
            or type(self.path) is not str
            or type(self.raw_query) is not str
            or type(self.edge) is not EdgeRequestMetadata
            or type(self.is_tls) is not bool
        ):
            raise ValueError("Richiesta sessione HTTP non valida.")


@dataclass(frozen=True)
class SessionHttpResponse:
    status_code: int
    headers: tuple[tuple[str, str], ...]
    body: bytes = field(default=b"", repr=False, compare=False)

    def __post_init__(self) -> None:
        if (
            type(self.status_code) is not int
            or not 100 <= self.status_code <= 599
            or type(self.headers) is not tuple
            or type(self.body) is not bytes
            or len(self.body) > 16 * 1024
        ):
            raise ValueError("Risposta sessione HTTP non valida.")
        for header in self.headers:
            if (
                type(header) is not tuple
                or len(header) != 2
                or type(header[0]) is not str
                or type(header[1]) is not str
                or not header[0]
                or any(ord(character) < 32 or ord(character) == 127 for character in header[0] + header[1])
            ):
                raise ValueError("Header sessione HTTP non valido.")


class SessionHttpRoutes:
    """Expose a minimal authenticated session snapshot and CSRF logout."""

    def __init__(
        self,
        sessions: HttpSessionAuthBoundary,
        proxy_resolver: TrustedProxyClientResolver,
        admin_provisioning: AdminProvisioningService | None = None,
    ) -> None:
        if type(sessions) is not HttpSessionAuthBoundary:
            raise ValueError("Boundary sessione HTTP non valido.")
        if type(proxy_resolver) is not TrustedProxyClientResolver:
            raise ValueError("Resolver proxy sessione non valido.")
        if not sessions.cookie_policy.secure:
            raise ValueError("Le route sessione richiedono cookie Secure.")
        if admin_provisioning is not None and type(admin_provisioning) is not AdminProvisioningService:
            raise ValueError("Service provisioning amministrativo non valido.")
        self.sessions = sessions
        self.proxy_resolver = proxy_resolver
        self.admin_provisioning = admin_provisioning

    def handles(self, path: str) -> bool:
        return path in {_SESSION_PATH, _ACCOUNT_PATH, _LOGOUT_PATH} or (
            path == _ADMIN_PATH and self.admin_provisioning is not None
        )

    def dispatch(self, request: SessionHttpRequest) -> SessionHttpResponse | None:
        if type(request) is not SessionHttpRequest:
            return self._error(400, "bad_auth_request", "Richiesta non valida.")
        if not self.handles(request.path):
            return None
        cookie_header = None
        csrf_token = None
        context = None
        result = None
        try:
            self._require_https(request)
            self._require_empty_request(request)
            if (
                request.path in {_SESSION_PATH, _ACCOUNT_PATH, _ADMIN_PATH}
                and request.method != "GET"
            ):
                return self._method_error("GET")
            if request.path == _LOGOUT_PATH and request.method != "POST":
                return self._method_error("POST")
            cookie_header = _combined_header(
                request.edge, "cookie", maximum_bytes=_MAX_COOKIE_HEADER_BYTES,
                separator="; ", required=True
            )
            if request.path in {_SESSION_PATH, _ACCOUNT_PATH, _ADMIN_PATH}:
                csrf_headers = _header_values(request.edge, "x-csrf-token")
                if csrf_headers:
                    _csrf_header(csrf_headers)
                context = self.sessions.authenticate(
                    HttpAuthRequest("GET", cookie_header=cookie_header)
                )
                if request.path == _ACCOUNT_PATH:
                    return self._account_response(context)
                if request.path == _ADMIN_PATH:
                    return self._admin_response(context)
                return self._session_response(context)
            csrf_token = _csrf_header(
                _header_values(request.edge, "x-csrf-token")
            )
            result = self.sessions.logout(
                HttpAuthRequest(
                    "POST",
                    cookie_header=cookie_header,
                    csrf_token=csrf_token,
                )
            )
            return SessionHttpResponse(
                204,
                self._base_headers() + (
                    ("Set-Cookie", result.set_cookie),
                    ("Content-Length", "0"),
                ),
            )
        except _SessionRequestError as error:
            return self._error(error.status_code, error.error_code, error.public_message)
        except AdminProvisioningConflictError:
            return self._error(403, "admin_forbidden", "Accesso amministrativo non consentito.")
        except HttpAuthError as error:
            extra = (("Allow", "POST"),) if isinstance(error, HttpMethodNotAllowedError) else ()
            return self._error(error.status_code, error.error_code, error.public_message, extra)
        except EdgeClientAttributionError:
            return self._error(400, "invalid_client_address", "Indirizzo client non valido.")
        except Exception:
            return self._error(
                503,
                "authentication_unavailable",
                "Servizio di autenticazione temporaneamente non disponibile.",
            )
        finally:
            request = None
            cookie_header = None
            csrf_token = None
            context = None
            result = None

    def _require_https(self, request: SessionHttpRequest) -> None:
        if request.is_tls:
            return
        if not self.proxy_resolver.is_trusted_peer(request.edge):
            raise _SessionRequestError(400, "https_required", "HTTPS obbligatorio.")
        forwarded = [
            value.strip().lower()
            for name, value in request.edge.headers
            if name.lower() == "x-forwarded-proto"
        ]
        if forwarded != ["https"]:
            raise _SessionRequestError(400, "https_required", "HTTPS obbligatorio.")

    @staticmethod
    def _require_empty_request(request: SessionHttpRequest) -> None:
        if request.raw_query:
            raise _SessionRequestError(400, "bad_auth_request", "Query non consentita.")
        lengths = _header_values(request.edge, "content-length")
        transfers = _header_values(request.edge, "transfer-encoding")
        if transfers or len(lengths) > 1 or (lengths and lengths != ["0"]):
            raise _SessionRequestError(400, "bad_auth_request", "Body non consentito.")

    @staticmethod
    def _base_headers() -> tuple[tuple[str, str], ...]:
        return (
            ("Cache-Control", "no-store"),
            ("Pragma", "no-cache"),
            ("Referrer-Policy", "no-referrer"),
        )

    def _session_response(self, context) -> SessionHttpResponse:
        user = context.user
        session = context.session
        expires_at = _utc_z(session.expires_at)
        payload = {
            "authenticated": True,
            "user": {
                "user_id": user.user_id,
                "display_name": user.display_name,
                "role": user.role,
            },
            "session": {"expires_at": expires_at},
            "csrf_token": context.csrf_token,
        }
        body = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        return SessionHttpResponse(
            200,
            self._base_headers() + (
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ),
            body,
        )

    def _account_response(self, context) -> SessionHttpResponse:
        role = context.user.role
        if role == "pending":
            title = "Account in attesa"
            message = (
                "L'account è autenticato, ma ruolo e classe devono ancora essere approvati."
            )
            action = ""
        elif role == "student":
            title = "Area studente"
            message = (
                "L'account studente è autorizzato. Puoi associare la TUI da questo browser."
            )
            action = '<p><a href="/auth/tui/pair">Associa la TUI</a></p>'
        elif role == "teacher":
            title = "Area docente"
            message = (
                "L'account docente è autorizzato. "
                "La Board mantiene una protezione docente separata."
            )
            action = '<p><a href="/tools/course_board.html">Apri la Course Design Board</a></p>'
        else:
            title = "Area amministratore"
            message = "L'account amministratore è autorizzato."
            action = '<p><a href="/auth/admin">Gestisci utenti e classi</a></p>'
        body = (
            "<!doctype html><html lang=\"it\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{title} - TheBitLab</title></head><body><main><h1>{title}</h1>"
            f"<p>{message}</p>{action}</main></body></html>"
        ).encode("utf-8")
        return SessionHttpResponse(
            200,
            self._base_headers() + (
                (
                    "Content-Security-Policy",
                    "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
                    "form-action 'none'",
                ),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ),
            body,
        )

    def _admin_response(self, context) -> SessionHttpResponse:
        snapshot = self.admin_provisioning.snapshot(context.user)
        pending = "".join(
            f"<li><code>{html.escape(user.user_id)}</code> — {html.escape(user.display_name)}</li>"
            for user in snapshot.pending_users
        ) or "<li>Nessun account pending</li>"
        classes = "".join(
            f"<li><code>{html.escape(item.class_id)}</code> — {html.escape(item.label)}</li>"
            for item in snapshot.classes
        ) or "<li>Nessuna classe</li>"
        body = (
            "<!doctype html><html lang=\"it\"><head><meta charset=\"utf-8\">"
            "<title>Amministrazione - TheBitLab</title></head><body><main>"
            f"<h1>Amministrazione</h1><h2>Account pending</h2><ul>{pending}</ul>"
            f"<h2>Classi</h2><ul>{classes}</ul></main></body></html>"
        ).encode("utf-8")
        return SessionHttpResponse(200, self._base_headers() + (
            ("Content-Security-Policy", "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"),
            ("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "DENY"),
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ), body)

    def _method_error(self, allowed: str) -> SessionHttpResponse:
        return self._error(
            405,
            "auth_method_not_allowed",
            "Metodo non consentito.",
            (("Allow", allowed),),
        )

    def _error(
        self,
        status_code: int,
        error_code: str,
        message: str,
        extra_headers: tuple[tuple[str, str], ...] = (),
    ) -> SessionHttpResponse:
        body = json.dumps(
            {"error": error_code, "message": message},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return SessionHttpResponse(
            status_code,
            extra_headers + self._base_headers() + (
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ),
            body,
        )


class _SessionRequestError(RuntimeError):
    def __init__(self, status_code: int, error_code: str, public_message: str) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.public_message = public_message
        super().__init__(public_message)


def _header_values(edge: EdgeRequestMetadata, lowered_name: str) -> list[str]:
    return [value.strip() for name, value in edge.headers if name.lower() == lowered_name]


def _combined_header(
    edge: EdgeRequestMetadata,
    lowered_name: str,
    *,
    maximum_bytes: int,
    separator: str,
    required: bool,
) -> str | None:
    values = _header_values(edge, lowered_name)
    if not values:
        if required:
            raise HttpAuthenticationRequiredError()
        return None
    combined = separator.join(values)
    if (
        len(combined.encode("utf-8", errors="surrogatepass")) > maximum_bytes
        or any(ord(character) < 32 or ord(character) == 127 for character in combined)
    ):
        combined = None
        raise HttpBadRequestError()
    return combined


def _csrf_header(values: list[str]) -> str:
    if len(values) != 1 or _CSRF_RE.fullmatch(values[0]) is None:
        values = []
        raise HttpCsrfRejectedError()
    return values[0]


def _utc_z(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Scadenza sessione non valida.")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
