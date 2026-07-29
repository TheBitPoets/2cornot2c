"""Concrete HTTPS transport for browser-mediated TUI pairing."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from scripts.thebitlab_edge_rate_limit import (
    AtomicRateLimitStore,
    EdgeClientAttributionError,
    EdgeRateLimitStoreError,
    EdgeRequestMetadata,
    RateLimitBucket,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_http_auth import (
    HttpAuthError,
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpCsrfRejectedError,
)
from scripts.thebitlab_tui_pairing import (
    IssuedTuiCredential,
    TuiBrowserPairingBoundary,
    TuiPairingBadRequestError,
)

_BEGIN_PATH = "/auth/tui/pairings"
_AUTHORIZE_PATH = "/auth/tui/pair"
_LOGOUT_PATH = "/auth/tui/logout"
_TOKEN_RE = re.compile(r"^/auth/tui/pairings/([A-Za-z0-9_-]{1,128})/token$")
_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
_MAX_BODY_BYTES = 2048


@dataclass(frozen=True)
class TuiPairingHttpRequest:
    method: str
    path: str
    raw_query: str = field(default="", repr=False)
    body: bytes = field(default=b"", repr=False, compare=False)
    edge: EdgeRequestMetadata = field(default=None, repr=False)
    is_tls: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.method) is not str
            or type(self.path) is not str
            or type(self.raw_query) is not str
            or type(self.body) is not bytes
            or len(self.body) > _MAX_BODY_BYTES
            or type(self.edge) is not EdgeRequestMetadata
            or type(self.is_tls) is not bool
        ):
            raise ValueError("Richiesta pairing HTTP non valida.")


class TuiCredentialDeliveryGuard:
    __slots__ = ("_boundary", "_credential", "_completed")

    def __init__(self, boundary: TuiBrowserPairingBoundary, credential: IssuedTuiCredential):
        self._boundary = boundary
        self._credential = credential
        self._completed = False

    def delivered(self) -> None:
        self._completed = True
        self._credential = None

    def failed(self) -> None:
        if self._completed:
            return
        credential = self._credential
        self._credential = None
        self._completed = True
        if credential is not None:
            self._boundary.discard_issued_credential(credential)
        credential = None

    def __repr__(self) -> str:
        return "TuiCredentialDeliveryGuard(pending=%s)" % (not self._completed)


@dataclass(frozen=True)
class TuiPairingHttpResponse:
    status_code: int
    headers: tuple[tuple[str, str], ...]
    body: bytes = field(default=b"", repr=False, compare=False)
    delivery_guard: TuiCredentialDeliveryGuard | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if (
            type(self.status_code) is not int
            or not 100 <= self.status_code <= 599
            or type(self.headers) is not tuple
            or type(self.body) is not bytes
            or len(self.body) > 16 * 1024
            or (
                self.delivery_guard is not None
                and type(self.delivery_guard) is not TuiCredentialDeliveryGuard
            )
        ):
            raise ValueError("Risposta pairing HTTP non valida.")


class TuiPairingHttpRateLimiter:
    def __init__(
        self,
        store: AtomicRateLimitStore,
        resolver: TrustedProxyClientResolver,
        *,
        pepper: bytes,
        clock=lambda: datetime.now(timezone.utc),
    ) -> None:
        if type(pepper) is not bytes or len(pepper) < 32:
            raise ValueError("Pepper rate limit pairing non valido.")
        self.store = store
        self.resolver = resolver
        self._pepper = pepper
        self.clock = clock

    def admit(self, route_id: str, edge: EdgeRequestMetadata, correlation: str | None = None) -> None:
        client = self.resolver.resolve(edge)
        now = self.clock()
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
            raise EdgeRateLimitStoreError("Clock pairing non valido.")
        limits = {
            "begin": (120, 8),
            "authorize": (300, 20),
            "consume": (600, 30),
            "logout": (600, 30),
        }
        if route_id not in limits:
            raise EdgeRateLimitStoreError("Route pairing non valida.")
        global_limit, client_limit = limits[route_id]
        client_key = self._key(route_id, client)
        buckets = [
            RateLimitBucket(f"global:auth.tui.{route_id}", global_limit, 60),
            RateLimitBucket(client_key, client_limit, 60),
        ]
        if correlation is not None:
            buckets.append(RateLimitBucket(self._key(route_id, correlation), 20, 60))
        retry_after = self.store.admit(tuple(buckets), now=now.astimezone(timezone.utc))
        if retry_after is not None:
            if type(retry_after) is not int or retry_after < 1:
                raise EdgeRateLimitStoreError("Retry rate limit pairing non valido.")
            raise _PairingRateLimitError(retry_after)

    def _key(self, route_id: str, value: str) -> str:
        return "hmac-sha256:" + hmac.new(
            self._pepper,
            ("auth.tui." + route_id + "\0" + value).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


class TuiPairingHttpRoutes:
    def __init__(
        self,
        boundary: TuiBrowserPairingBoundary,
        proxy_resolver: TrustedProxyClientResolver,
        rate_limiter: TuiPairingHttpRateLimiter,
    ) -> None:
        if (
            type(boundary) is not TuiBrowserPairingBoundary
            or type(proxy_resolver) is not TrustedProxyClientResolver
            or type(rate_limiter) is not TuiPairingHttpRateLimiter
            or rate_limiter.resolver is not proxy_resolver
        ):
            raise ValueError("Grafo route pairing non valido.")
        self.boundary = boundary
        self.proxy_resolver = proxy_resolver
        self.rate_limiter = rate_limiter

    def handles(self, path: str) -> bool:
        return path in {_BEGIN_PATH, _AUTHORIZE_PATH, _LOGOUT_PATH} or _TOKEN_RE.fullmatch(path or "") is not None

    def dispatch(self, request: TuiPairingHttpRequest) -> TuiPairingHttpResponse | None:
        if type(request) is not TuiPairingHttpRequest:
            return self._error(400, "tui_pairing_invalid", "Richiesta pairing non valida.")
        if not self.handles(request.path):
            return None
        code = None
        pairing_id = None
        credential = None
        payload = None
        cookie_header = None
        csrf_token = None
        authorization_header = None
        started = None
        try:
            self._require_https_and_query(request)
            if request.path == _AUTHORIZE_PATH and request.method == "GET":
                self._require_safe_method_framing(request)
                return self._browser_page()
            if request.method != "POST":
                allow = "GET, POST" if request.path == _AUTHORIZE_PATH else "POST"
                return self._error(405, "auth_method_not_allowed", "Metodo non consentito.", (("Allow", allow),))
            self._require_framing(request)
            if request.path == _BEGIN_PATH:
                self._require_empty_body(request)
                self.rate_limiter.admit("begin", request.edge)
                self._cleanup_expired_pairings()
                started = self.boundary.begin()
                return self._json(201, {
                    "pairing_id": started.pairing_id,
                    "user_code": started.user_code,
                    "verification_path": started.verification_path,
                    "expires_at": _utc_z(started.expires_at),
                })
            if request.path == _LOGOUT_PATH:
                self._require_empty_body(request)
                authorization_header = _authorization_header(request.edge)
                self.rate_limiter.admit("logout", request.edge)
                self.boundary.revoke_bearer(authorization_header)
                return TuiPairingHttpResponse(
                    204,
                    self._base_headers() + (("Content-Length", "0"),),
                )
            payload = _json_object(request)
            code = payload.get("code")
            if set(payload) != {"code"} or type(code) is not str or _CODE_RE.fullmatch(code) is None:
                raise TuiPairingBadRequestError()
            if request.path == _AUTHORIZE_PATH:
                self.rate_limiter.admit("authorize", request.edge)
                cookie_header = _combined_cookie(request.edge)
                csrf_token = _csrf_header(request.edge)
                self.boundary.authorize_browser(
                    HttpAuthRequest("POST", cookie_header, csrf_token), code
                )
                return TuiPairingHttpResponse(204, self._base_headers() + (("Content-Length", "0"),))
            match = _TOKEN_RE.fullmatch(request.path)
            pairing_id = match.group(1) if match is not None else None
            if pairing_id is None:
                raise TuiPairingBadRequestError()
            self.rate_limiter.admit("consume", request.edge, pairing_id)
            credential = self.boundary.consume(pairing_id, code)
            response = self._json(200, {
                "token_type": "Bearer",
                "bearer_token": credential.bearer_token,
                "expires_at": _utc_z(credential.expires_at),
            }, guard=TuiCredentialDeliveryGuard(self.boundary, credential))
            credential = None
            return response
        except _PairingRateLimitError as error:
            return self._error(429, "rate_limit_exceeded", "Troppe richieste.", (("Retry-After", str(error.retry_after)),))
        except EdgeClientAttributionError:
            return self._error(400, "invalid_client_address", "Indirizzo client non valido.")
        except HttpAuthError as error:
            return self._error(error.status_code, error.error_code, error.public_message)
        except Exception:
            if credential is not None:
                self.boundary.discard_issued_credential(credential)
            return self._error(503, "tui_pairing_unavailable", "Servizio pairing temporaneamente non disponibile.")
        finally:
            request = None
            code = None
            pairing_id = None
            credential = None
            payload = None
            cookie_header = None
            csrf_token = None
            authorization_header = None
            started = None

    def _require_https_and_query(self, request: TuiPairingHttpRequest) -> None:
        if request.raw_query:
            raise TuiPairingBadRequestError()
        require_tui_https_transport(
            self.proxy_resolver,
            request.edge,
            is_tls=request.is_tls,
        )

    @staticmethod
    def _require_safe_method_framing(request: TuiPairingHttpRequest) -> None:
        transfers = _header_values(request.edge, "transfer-encoding")
        lengths = _header_values(request.edge, "content-length")
        if transfers or request.body or lengths not in ([], ["0"]):
            raise TuiPairingBadRequestError()

    @staticmethod
    def _require_framing(request: TuiPairingHttpRequest) -> None:
        transfers = _header_values(request.edge, "transfer-encoding")
        lengths = _header_values(request.edge, "content-length")
        if (
            transfers
            or len(lengths) != 1
            or not lengths[0].isdigit()
            or int(lengths[0]) != len(request.body)
        ):
            raise TuiPairingBadRequestError()

    def _cleanup_expired_pairings(self) -> None:
        pairing_service = self.boundary.pairings.pairings
        now = pairing_service.clock()
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
            raise EdgeRateLimitStoreError("Clock cleanup pairing non valido.")
        cutoff = now.astimezone(timezone.utc)
        removed_sessions = pairing_service.storage.delete_expired_sessions(cutoff)
        if type(removed_sessions) is not int or removed_sessions < 0:
            raise EdgeRateLimitStoreError("Cleanup sessioni non valido.")
        removed_pairings = pairing_service.storage.delete_expired_pairings(cutoff)
        if type(removed_pairings) is not int or removed_pairings < 0:
            raise EdgeRateLimitStoreError("Cleanup pairing non valido.")

    @staticmethod
    def _require_empty_body(request: TuiPairingHttpRequest) -> None:
        if request.body:
            raise TuiPairingBadRequestError()

    @staticmethod
    def _base_headers() -> tuple[tuple[str, str], ...]:
        return (("Cache-Control", "no-store"), ("Pragma", "no-cache"), ("Referrer-Policy", "no-referrer"))

    def _browser_page(self) -> TuiPairingHttpResponse:
        nonce = secrets.token_urlsafe(24)
        html = _PAIRING_PAGE.replace("__CSP_NONCE__", nonce).encode("utf-8")
        headers = self._base_headers() + (
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Security-Policy", f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Content-Length", str(len(html))),
        )
        return TuiPairingHttpResponse(200, headers, html)

    def _json(self, status: int, payload: dict, *, guard=None) -> TuiPairingHttpResponse:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return TuiPairingHttpResponse(status, self._base_headers() + (("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))), body, guard)

    def _error(self, status: int, code: str, message: str, extra=()) -> TuiPairingHttpResponse:
        body = json.dumps({"error": code, "message": message}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return TuiPairingHttpResponse(status, tuple(extra) + self._base_headers() + (("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))), body)


class _PairingRateLimitError(RuntimeError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Troppe richieste.")


def require_tui_https_transport(
    resolver: TrustedProxyClientResolver,
    edge: EdgeRequestMetadata,
    *,
    is_tls: bool,
) -> None:
    """Require direct TLS or one unambiguous trusted proxy assertion."""

    if (
        type(resolver) is not TrustedProxyClientResolver
        or type(edge) is not EdgeRequestMetadata
        or type(is_tls) is not bool
    ):
        raise EdgeClientAttributionError("Trasporto pairing non valido.")
    if is_tls:
        return
    if not resolver.is_trusted_peer(edge):
        raise _HttpsRequiredError()
    forwarded = [value.lower() for value in _header_values(edge, "x-forwarded-proto")]
    if forwarded != ["https"]:
        raise _HttpsRequiredError()


class _HttpsRequiredError(HttpAuthError):
    status_code = 400
    error_code = "https_required"
    public_message = "HTTPS obbligatorio."


def _header_values(edge: EdgeRequestMetadata, name: str) -> list[str]:
    return [value.strip() for key, value in edge.headers if key.lower() == name]


def _combined_cookie(edge: EdgeRequestMetadata) -> str:
    values = _header_values(edge, "cookie")
    if not values:
        raise HttpAuthenticationRequiredError()
    combined = "; ".join(values)
    if len(combined.encode("utf-8", errors="surrogatepass")) > 16384:
        raise TuiPairingBadRequestError()
    return combined


def _csrf_header(edge: EdgeRequestMetadata) -> str:
    values = _header_values(edge, "x-csrf-token")
    if len(values) != 1 or not values[0] or len(values[0]) > 512:
        raise HttpCsrfRejectedError()
    return values[0]


def _authorization_header(edge: EdgeRequestMetadata) -> str:
    values = _header_values(edge, "authorization")
    if len(values) > 1 or (
        values
        and len(values[0].encode("utf-8", errors="surrogatepass")) > 2048
    ):
        raise TuiPairingBadRequestError()
    return values[0] if values else ""


def _json_object(request: TuiPairingHttpRequest) -> dict:
    content_types = _header_values(request.edge, "content-type")
    if content_types != ["application/json"] or not 2 <= len(request.body) <= _MAX_BODY_BYTES:
        raise TuiPairingBadRequestError()
    try:
        payload = json.loads(request.body.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise TuiPairingBadRequestError() from None
    if type(payload) is not dict:
        raise TuiPairingBadRequestError()
    return payload


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


_PAIRING_PAGE = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Collega terminale · TheBitLab</title>
<style nonce="__CSP_NONCE__">body{font-family:system-ui,sans-serif;max-width:34rem;margin:4rem auto;padding:0 1rem;color:#172033}label,input,button{display:block;width:100%;box-sizing:border-box}input,button{font:inherit;padding:.75rem;margin:.5rem 0 1rem}button{cursor:pointer}#status{min-height:1.5rem}.error{color:#a00}.ok{color:#075}</style>
</head><body><main><h1>Collega il terminale</h1><p>Accedi come studente, poi inserisci il codice mostrato nel terminale. Il browser non riceverà la credenziale TUI.</p>
<label for="code">Codice terminale</label><input id="code" name="code" autocomplete="one-time-code" autocapitalize="characters" spellcheck="false" maxlength="128" pattern="[A-Za-z0-9_-]{8,128}">
<button id="pair" type="button">Autorizza terminale</button><p id="status" role="status" aria-live="polite"></p><p><a id="login" href="/auth/google/login" target="_blank" rel="noopener noreferrer" hidden>Accedi con Google in una nuova scheda</a></p></main>
<script nonce="__CSP_NONCE__">(()=>{'use strict';const code=document.getElementById('code'),button=document.getElementById('pair'),status=document.getElementById('status'),login=document.getElementById('login');const message=(text,kind)=>{status.textContent=text;status.className=kind||''};button.addEventListener('click',async()=>{button.disabled=true;login.hidden=true;message('Verifica in corso…','');try{const session=await fetch('/auth/session',{credentials:'same-origin',cache:'no-store',redirect:'error'});if(session.status===401){login.hidden=false;throw new Error('Accedi prima di autorizzare il terminale.')}if(!session.ok)throw new Error('Sessione non disponibile. Riprova.');const snapshot=await session.json();if(typeof snapshot.csrf_token!=='string')throw new Error('Sessione non valida.');const response=await fetch('/auth/tui/pair',{method:'POST',credentials:'same-origin',cache:'no-store',redirect:'error',headers:{'Content-Type':'application/json','X-CSRF-Token':snapshot.csrf_token},body:JSON.stringify({code:code.value.trim()})});if(!response.ok)throw new Error(response.status===403?'Accesso studente richiesto.':'Codice non valido, scaduto o già usato.');code.value='';message('Terminale autorizzato. Puoi tornare alla TUI.','ok')}catch(error){message(error instanceof Error?error.message:'Autorizzazione non disponibile.','error')}finally{button.disabled=false}})})();</script></body></html>"""


def _utc_z(value: datetime) -> str:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
