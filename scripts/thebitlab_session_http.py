"""Concrete HTTPS routes for current web session status and logout."""

from __future__ import annotations

import base64
import hashlib
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
from scripts.thebitlab_auth_styles import AUTH_PAGE_CSS
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
_ADMIN_CLASSES_PATH = "/auth/admin/classes"
_ADMIN_APPROVALS_PATH = "/auth/admin/approvals"
_ADMIN_MUTATION_PATHS = frozenset({_ADMIN_CLASSES_PATH, _ADMIN_APPROVALS_PATH})
_LOGOUT_PATH = "/auth/logout"
_MAX_COOKIE_HEADER_BYTES = 16 * 1024
_MAX_ADMIN_BODY_BYTES = 4096
_CSRF_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_ADMIN_SCRIPT = """const session=()=>fetch('/auth/session').then(r=>{if(!r.ok)throw Error();return r.json()});document.querySelectorAll('form[data-endpoint]').forEach(form=>form.addEventListener('submit',async event=>{event.preventDefault();if(!confirm('Confermare l’operazione amministrativa?'))return;const data=new FormData(form);let payload;if(form.dataset.endpoint.endsWith('/classes')){payload={class_id:data.get('class_id'),label:data.get('label'),school_year:data.get('school_year')}}else{const role=data.get('role');payload={target_user_id:form.dataset.user,expected_target_updated_at:form.dataset.revision,role:role,class_id:role==='student'?data.get('class_id'):null}}try{const auth=await session();const response=await fetch(form.dataset.endpoint,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':auth.csrf_token},body:JSON.stringify(payload)});if(!response.ok)throw Error();location.reload()}catch(error){alert('Operazione non completata. Ricaricare e riprovare.')}}));"""
_ADMIN_SCRIPT_HASH = base64.b64encode(
    hashlib.sha256(_ADMIN_SCRIPT.encode("utf-8")).digest()
).decode("ascii")


@dataclass(frozen=True)
class SessionHttpRequest:
    method: str
    path: str
    raw_query: str = field(default="", repr=False)
    edge: EdgeRequestMetadata = field(default=None, repr=False)
    is_tls: bool = False
    body: bytes = field(default=b"", repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.method) is not str
            or type(self.path) is not str
            or type(self.raw_query) is not str
            or type(self.edge) is not EdgeRequestMetadata
            or type(self.is_tls) is not bool
            or type(self.body) is not bytes
            or len(self.body) > _MAX_ADMIN_BODY_BYTES
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
            path in {_ADMIN_PATH, *_ADMIN_MUTATION_PATHS}
            and self.admin_provisioning is not None
        )

    def expects_body(self, path: str) -> bool:
        return path in _ADMIN_MUTATION_PATHS and self.admin_provisioning is not None

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
            if request.path in _ADMIN_MUTATION_PATHS:
                if request.method != "POST":
                    return self._method_error("POST")
                self._require_admin_json_request(request)
            else:
                self._require_empty_request(request)
                if request.path in {_SESSION_PATH, _ACCOUNT_PATH, _ADMIN_PATH}:
                    if request.method != "GET":
                        return self._method_error("GET")
                elif request.method != "POST":
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
            if request.path in _ADMIN_MUTATION_PATHS:
                context = self.sessions.authenticate(
                    HttpAuthRequest(
                        "POST",
                        cookie_header=cookie_header,
                        csrf_token=csrf_token,
                    )
                )
                if context.user.role != "admin":
                    return self._error(
                        403,
                        "admin_forbidden",
                        "Accesso amministrativo non consentito.",
                    )
                payload = _json_object(request.body)
                if request.path == _ADMIN_CLASSES_PATH:
                    self._create_admin_class(context, payload)
                else:
                    self._approve_admin_user(context, payload)
                return SessionHttpResponse(
                    204,
                    self._base_headers() + (("Content-Length", "0"),),
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
            if request.path in _ADMIN_MUTATION_PATHS:
                return self._error(
                    409,
                    "admin_conflict",
                    "Dati amministrativi non più correnti.",
                )
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
    def _require_admin_json_request(request: SessionHttpRequest) -> None:
        if request.raw_query:
            raise _SessionRequestError(400, "bad_auth_request", "Query non consentita.")
        transfers = _header_values(request.edge, "transfer-encoding")
        lengths = _header_values(request.edge, "content-length")
        content_types = _header_values(request.edge, "content-type")
        content_encodings = _header_values(request.edge, "content-encoding")
        expected = str(len(request.body))
        if (
            transfers
            or lengths != [expected]
            or expected == "0"
            or len(request.body) > _MAX_ADMIN_BODY_BYTES
            or content_types != ["application/json"]
            or content_encodings
        ):
            raise _SessionRequestError(
                400, "bad_auth_request", "Richiesta JSON amministrativa non valida."
            )

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
            action = '<p><a class="btn" href="/auth/tui/pair">Associa la TUI</a></p>'
        elif role == "teacher":
            title = "Area docente"
            message = (
                "L'account docente è autorizzato. "
                "La Board mantiene una protezione docente separata."
            )
            action = '<p><a class="btn" href="/tools/course_board.html">Apri la Course Design Board</a></p>'
        else:
            title = "Area amministratore"
            message = "L'account amministratore è autorizzato."
            action = '<p><a class="btn" href="/auth/admin">Gestisci utenti e classi</a></p>'
        logo_url = "https://www.thebitpoets.com/assets/logo-400.png"
        logo_srcset = (
            "https://www.thebitpoets.com/assets/logo-400.png 400w, "
            "https://www.thebitpoets.com/assets/logo-521.png 521w"
        )
        body = (
            "<!doctype html>"
            "<html lang='it'><head>"
            "<meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{title} - TheBitLab</title>"
            f"<style>{AUTH_PAGE_CSS}</style>"
            "</head><body>"
            "<nav class='topNav'>"
            f"<a class='topNavBrand' href='/'><img src='{logo_url}' "
            f"srcset='{logo_srcset}' sizes='40px' width='40' height='40' alt='TheBitLab'></a>"
            "<div class='topNavTitle'>TheBitLab</div>"
            "</nav>"
            "<main><div class='account-card card'>"
            f"<h1>{title}</h1>"
            f"<p>{message}</p>{action}"
            "</div></main>"
            "</body></html>"
        ).encode("utf-8")
        return SessionHttpResponse(
            200,
            self._base_headers() + (
                (
                    "Content-Security-Policy",
                    "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
                    "form-action 'none'; style-src 'unsafe-inline'; "
                    "img-src https://www.thebitpoets.com",
                ),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ),
            body,
        )

    def _create_admin_class(self, context, payload: dict[str, object]) -> None:
        if set(payload) != {"class_id", "label", "school_year"} or any(
            type(payload[name]) is not str
            for name in ("class_id", "label", "school_year")
        ):
            raise _SessionRequestError(
                400, "invalid_admin_payload", "Payload classe non valido."
            )
        try:
            self.admin_provisioning.create_class(
                context.user,
                class_id=payload["class_id"],
                label=payload["label"],
                school_year=payload["school_year"],
            )
        except ValueError as error:
            raise _SessionRequestError(
                400, "invalid_admin_payload", "Payload classe non valido."
            ) from error

    def _approve_admin_user(self, context, payload: dict[str, object]) -> None:
        if set(payload) != {
            "target_user_id",
            "expected_target_updated_at",
            "role",
            "class_id",
        }:
            raise _SessionRequestError(
                400, "invalid_admin_payload", "Payload approvazione non valido."
            )
        target_user_id = payload["target_user_id"]
        revision = payload["expected_target_updated_at"]
        role = payload["role"]
        class_id = payload["class_id"]
        if (
            type(target_user_id) is not str
            or type(revision) is not str
            or type(role) is not str
            or (class_id is not None and type(class_id) is not str)
        ):
            raise _SessionRequestError(
                400, "invalid_admin_payload", "Payload approvazione non valido."
            )
        expected_revision = _parse_utc_revision(revision)
        try:
            self.admin_provisioning.approve(
                context.user,
                target_user_id=target_user_id,
                expected_target_updated_at=expected_revision,
                role=role,
                class_id=class_id,
            )
        except ValueError as error:
            raise _SessionRequestError(
                400, "invalid_admin_payload", "Payload approvazione non valido."
            ) from error

    def _admin_response(self, context) -> SessionHttpResponse:
        snapshot = self.admin_provisioning.snapshot(context.user)
        budget = 10_000

        def bounded_rows(items, render, empty):
            nonlocal budget
            rows = []
            for item in items:
                row = render(item)
                size = len(row.encode("utf-8"))
                if size > budget:
                    rows.append('<p class="hint">Elenco troncato</p>')
                    break
                rows.append(row)
                budget -= size
            return "".join(rows) or empty

        def pending_row(user):
            user_id = html.escape(user.user_id, quote=True)
            revision = html.escape(_utc_z(user.updated_at), quote=True)
            name = html.escape(user.display_name)
            return (
                '<div class="pending-item">'
                f'<div class="email">{name}</div>'
                f'<div class="meta">Google • ID <span class="mono">{user_id}</span></div>'
                f'<form class="row" data-endpoint="{_ADMIN_APPROVALS_PATH}" data-user="{user_id}" '
                f'data-revision="{revision}">'
                '<select name="role">'
                '<option value="student">Studente</option>'
                '<option value="teacher">Docente</option>'
                '<option value="admin">Amministratore</option>'
                '</select>'
                '<input name="class_id" maxlength="512" placeholder="ID classe per studente">'
                '<button class="ok" type="submit">Approva</button></form></div>'
            )

        pending_users = list(snapshot.pending_users)
        class_list = list(snapshot.classes)
        pending = bounded_rows(
            pending_users,
            pending_row,
            '<p class="hint">Nessun account pending</p>',
        )
        classes = bounded_rows(
            class_list,
            lambda item: (
                "<tr>"
                f'<td class="mono">{html.escape(item.class_id)}</td>'
                f'<td>{html.escape(item.label)}</td>'
                f'<td>{html.escape(getattr(item, "school_year", ""))}</td>'
                "</tr>"
            ),
            '<tr><td colspan="3" class="hint">Nessuna classe</td></tr>',
        )
        logo_url = "https://www.thebitpoets.com/assets/logo-400.png"
        logo_srcset = (
            "https://www.thebitpoets.com/assets/logo-400.png 400w, "
            "https://www.thebitpoets.com/assets/logo-521.png 521w"
        )
        body = (
            "<!doctype html><html lang='it'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Amministrazione - TheBitLab</title>"
            f"<style>{AUTH_PAGE_CSS}</style></head><body>"
            "<nav class='topNav'>"
            f"<a class='topNavBrand' href='/'><img src='{logo_url}' "
            f"srcset='{logo_srcset}' sizes='40px' width='40' height='40' alt='TheBitLab'></a>"
            "<div class='topNavTitle'>TheBitLab<span>Gestione utenti e classi</span></div>"
            "</nav>"
            "<main><h1>Amministrazione</h1><div class='grid'>"
            f'<section class="card"><h2>Classi <span class="badge">{len(class_list)}</span></h2>'
            "<table><thead><tr><th>ID</th><th>Nome</th><th>Anno</th></tr></thead>"
            f"<tbody>{classes}</tbody></table>"
            f'<form class="row" data-endpoint="{_ADMIN_CLASSES_PATH}">'
            '<input class="small" name="class_id" maxlength="512" placeholder="ID classe" required>'
            '<input name="label" maxlength="512" placeholder="Nome classe" required>'
            '<input class="small" name="school_year" maxlength="512" placeholder="Anno scolastico" required>'
            '<button type="submit">Crea classe</button></form></section>'
            f'<section class="card"><h2>Utenti in attesa <span class="badge">{len(pending_users)}</span></h2>'
            f"{pending}"
            '<p class="hint">Gli utenti approvati ricevono il ruolo e la classe selezionati.</p></section>'
            "</div></main>"
            f"<script>{_ADMIN_SCRIPT}</script></body></html>"
        ).encode("utf-8")
        return SessionHttpResponse(
            200,
            self._base_headers()
            + (
                (
                    "Content-Security-Policy",
                    "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
                    f"script-src 'sha256-{_ADMIN_SCRIPT_HASH}'; connect-src 'self'; "
                    "form-action 'none'; style-src 'unsafe-inline'; "
                    "img-src https://www.thebitpoets.com",
                ),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ),
            body,
        )

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


def _json_object(body: bytes) -> dict[str, object]:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if type(key) is not str or key in result:
                raise ValueError("JSON duplicato")
            result[key] = value
        return result

    try:
        payload = json.loads(body.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise _SessionRequestError(
            400, "invalid_admin_payload", "Payload amministrativo non valido."
        ) from error
    if type(payload) is not dict:
        raise _SessionRequestError(
            400, "invalid_admin_payload", "Payload amministrativo non valido."
        )
    return payload


def _parse_utc_revision(value: str) -> datetime:
    if not value.endswith("Z"):
        raise _SessionRequestError(
            400, "invalid_admin_payload", "Revisione target non valida."
        )
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise _SessionRequestError(
            400, "invalid_admin_payload", "Revisione target non valida."
        ) from error
    if parsed.tzinfo != timezone.utc or _utc_z(parsed) != value:
        raise _SessionRequestError(
            400, "invalid_admin_payload", "Revisione target non valida."
        )
    return parsed


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
