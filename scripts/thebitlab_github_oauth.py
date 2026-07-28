"""Authenticated GitHub OAuth account-linking adapter."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import queue
import re
import secrets
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping, Protocol, Sequence

from scripts.thebitlab_auth_services import (
    AuthApplicationError,
    ExternalIdentityLinkService,
    FederatedIdentityAssertion,
)
from scripts.thebitlab_http_auth import HttpAuthContext
from scripts.thebitlab_identity import ExternalIdentity, UserAccount, UserSession

_GITHUB_AUTH_ENDPOINT = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_ENDPOINT = "https://github.com/login/oauth/access_token"
_GITHUB_USER_ENDPOINT = "https://api.github.com/user"
_COOKIE_PREFIX = "__Host-thebitlab_github_link-"
_UNRESERVED_RE = re.compile(r"^[A-Za-z0-9._~-]+$")
_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{10,256}$")
_MAX_COOKIE_HEADER_BYTES = 4096


class GitHubLinkError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.clear_transaction_cookie: str | None = None


class GitHubLinkConfigurationError(GitHubLinkError):
    pass


class GitHubLinkStateError(GitHubLinkError):
    pass


class GitHubLinkConsumedStateError(GitHubLinkStateError):
    pass


class GitHubLinkCapacityError(GitHubLinkStateError):
    pass


class GitHubLinkCallbackError(GitHubLinkError):
    pass


class GitHubLinkProviderUnavailableError(GitHubLinkError):
    pass


class GitHubLinkProviderRejectedError(GitHubLinkError):
    pass


class GitHubLinkIdentityConflictError(GitHubLinkError):
    pass


@dataclass(frozen=True, init=False)
class GitHubOAuthConfig:
    client_id: str
    client_secret: str = field(repr=False, compare=False)
    redirect_uri: str
    authorization_endpoint: str = _GITHUB_AUTH_ENDPOINT
    token_endpoint: str = _GITHUB_TOKEN_ENDPOINT
    user_endpoint: str = _GITHUB_USER_ENDPOINT
    post_link_path: str = "/settings/accounts"
    flow_ttl: timedelta = timedelta(minutes=10)
    timeout_seconds: float = 10.0
    max_response_bytes: int = 64 * 1024

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorization_endpoint: str = _GITHUB_AUTH_ENDPOINT,
        token_endpoint: str = _GITHUB_TOKEN_ENDPOINT,
        user_endpoint: str = _GITHUB_USER_ENDPOINT,
        post_link_path: str = "/settings/accounts",
        flow_ttl: timedelta = timedelta(minutes=10),
        timeout_seconds: float = 10.0,
        max_response_bytes: int = 64 * 1024,
    ) -> None:
        candidate_secret = client_secret
        client_secret = None
        for name, value in (
            ("client_id", client_id),
            ("client_secret", candidate_secret),
            ("redirect_uri", redirect_uri),
            ("authorization_endpoint", authorization_endpoint),
            ("token_endpoint", token_endpoint),
            ("user_endpoint", user_endpoint),
            ("post_link_path", post_link_path),
            ("flow_ttl", flow_ttl),
            ("timeout_seconds", timeout_seconds),
            ("max_response_bytes", max_response_bytes),
        ):
            object.__setattr__(self, name, value)
        try:
            self._validate()
        except Exception:
            object.__setattr__(self, "client_secret", "")
            candidate_secret = None
            raise GitHubLinkConfigurationError("Configurazione GitHub OAuth non valida.")
        candidate_secret = None

    def _validate(self) -> None:
        if type(self.client_id) is not str or _CLIENT_ID_RE.fullmatch(self.client_id) is None:
            raise ValueError
        if (
            type(self.client_secret) is not str
            or not 1 <= len(self.client_secret) <= 2048
            or any(ord(character) < 0x20 for character in self.client_secret)
        ):
            raise ValueError
        parsed = urllib.parse.urlsplit(self.redirect_uri) if type(self.redirect_uri) is str else None
        if (
            parsed is None
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or "\\" in self.redirect_uri
            or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in self.redirect_uri)
        ):
            raise ValueError
        try:
            port = parsed.port
        except ValueError:
            raise ValueError from None
        if port is not None and port < 1:
            raise ValueError
        if (
            self.authorization_endpoint != _GITHUB_AUTH_ENDPOINT
            or self.token_endpoint != _GITHUB_TOKEN_ENDPOINT
            or self.user_endpoint != _GITHUB_USER_ENDPOINT
        ):
            raise ValueError
        if (
            type(self.post_link_path) is not str
            or not self.post_link_path.startswith("/")
            or self.post_link_path.startswith("//")
            or "\\" in self.post_link_path
            or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in self.post_link_path)
        ):
            raise ValueError
        if type(self.flow_ttl) is not timedelta or not timedelta(seconds=1) <= self.flow_ttl <= timedelta(minutes=30):
            raise ValueError
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or not 0 < self.timeout_seconds <= 60
        ):
            raise ValueError
        if type(self.max_response_bytes) is not int or not 1024 <= self.max_response_bytes <= 1024 * 1024:
            raise ValueError


@dataclass(frozen=True)
class PendingGitHubLinkFlow:
    state_digest: str
    browser_digest: str
    code_verifier: str = field(repr=False, compare=False)
    creation_marker: object = field(repr=False, compare=False)
    user_id: str
    session_id: str
    session_token_digest: str
    session_created_at: datetime
    user_updated_at: datetime
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class GitHubLinkAuthorizationRequest:
    authorization_url: str = field(repr=False, compare=False)
    set_cookie: str = field(repr=False, compare=False)


@dataclass(frozen=True)
class GitHubLinkResult:
    identity: ExternalIdentity
    redirect_path: str
    clear_transaction_cookie: str = field(repr=False, compare=False)


class GitHubOAuthTransport(Protocol):
    def exchange_code(self, *, form: Mapping[str, str], timeout_seconds: float, max_response_bytes: int) -> Mapping[str, object]: ...

    def read_user(self, *, access_token: str, timeout_seconds: float, max_response_bytes: int) -> Mapping[str, object]: ...


def _strict_json_object(data: bytes) -> dict[str, object]:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    decoded = json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicates)
    if type(decoded) is not dict:
        raise ValueError
    return decoded


_URLLIB_WORKER = r'''
import base64
import json
import sys
import urllib.error
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

try:
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    data = base64.b64decode(payload["data"]) if payload["data"] is not None else None
    request = urllib.request.Request(
        payload["url"],
        data=data,
        headers=payload["headers"],
        method=payload["method"],
    )
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=payload["timeout"]) as response:
        if response.status != 200:
            raise RuntimeError
        body = response.read(payload["maximum"] + 1)
    if len(body) > payload["maximum"]:
        raise RuntimeError
    sys.stdout.buffer.write(body)
except urllib.error.HTTPError as error:
    retryable = error.code in {408, 425, 429}
    if error.code == 403:
        retryable = (
            error.headers.get("Retry-After") is not None
            or error.headers.get("X-RateLimit-Remaining") == "0"
        )
    raise SystemExit(10 if 400 <= error.code < 500 and not retryable else 11)
except Exception:
    raise SystemExit(11)
'''


class UrllibGitHubOAuthTransport:
    _network_slots = threading.BoundedSemaphore(8)
    _process_start_slots = threading.BoundedSemaphore(8)
    _termination_slots = threading.BoundedSemaphore(8)

    def __init__(self) -> None:
        self._process_factory = subprocess.Popen

    def _request(self, request: urllib.request.Request, timeout_seconds: float, max_response_bytes: int) -> Mapping[str, object]:
        serialized = None
        output = None
        process = None
        release_network_slot = False
        release_termination_slot = False
        deadline = time.monotonic() + timeout_seconds
        if not self._network_slots.acquire(blocking=False):
            request = None
            raise GitHubLinkProviderUnavailableError("GitHub non disponibile.")
        release_network_slot = True
        if not self._termination_slots.acquire(blocking=False):
            self._network_slots.release()
            request = None
            raise GitHubLinkProviderUnavailableError("GitHub non disponibile.")
        release_termination_slot = True
        try:
            if not self._process_start_slots.acquire(blocking=False):
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                )
            started: queue.Queue[object] = queue.Queue(maxsize=1)
            abandoned = threading.Event()
            handoff = threading.Lock()

            def terminate_and_reap(candidate) -> None:
                try:
                    candidate.kill()
                    candidate.communicate()
                except Exception:
                    pass
                finally:
                    self._termination_slots.release()
                    self._network_slots.release()

            def start_reaper(candidate) -> None:
                nonlocal release_network_slot, release_termination_slot
                release_network_slot = False
                release_termination_slot = False
                try:
                    threading.Thread(
                        target=terminate_and_reap,
                        args=(candidate,),
                        name="thebitlab-github-oauth-reap",
                        daemon=True,
                    ).start()
                except Exception:
                    cleaned = False
                    try:
                        candidate.kill()
                        candidate.communicate(
                            timeout=max(0.01, min(timeout_seconds, 0.25))
                        )
                        cleaned = True
                    except Exception:
                        pass
                    if cleaned:
                        self._termination_slots.release()
                        self._network_slots.release()
                    # If cleanup cannot be proven, both slots stay reserved fail-closed.

            def start_process() -> None:
                candidate = None
                try:
                    candidate = self._process_factory(
                        [sys.executable, "-I", "-c", _URLLIB_WORKER],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    candidate = False
                finally:
                    self._process_start_slots.release()
                with handoff:
                    if abandoned.is_set():
                        if candidate is not None and candidate is not False:
                            terminate_and_reap(candidate)
                        else:
                            self._termination_slots.release()
                            self._network_slots.release()
                        return
                    started.put(candidate)

            try:
                threading.Thread(
                    target=start_process,
                    name="thebitlab-github-oauth-start",
                    daemon=True,
                ).start()
            except Exception:
                self._process_start_slots.release()
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                ) from None
            remaining = max(0.0, deadline - time.monotonic())
            try:
                process = started.get(timeout=remaining)
            except queue.Empty:
                with handoff:
                    abandoned.set()
                    release_network_slot = False
                    release_termination_slot = False
                    try:
                        late_process = started.get_nowait()
                    except queue.Empty:
                        late_process = None
                if late_process is not None and late_process is not False:
                    start_reaper(late_process)
                elif late_process is False:
                    self._termination_slots.release()
                    self._network_slots.release()
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                ) from None
            if process is False or process is None:
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                )
            serialized = json.dumps(
                {
                    "url": request.full_url,
                    "method": request.get_method(),
                    "headers": dict(request.header_items()),
                    "data": (
                        base64.b64encode(request.data).decode("ascii")
                        if request.data is not None
                        else None
                    ),
                    "timeout": timeout_seconds,
                    "maximum": max_response_bytes,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            request = None
            remaining = deadline - time.monotonic()
            timed_out = remaining <= 0
            if not timed_out:
                try:
                    output, _stderr = process.communicate(
                        input=serialized, timeout=remaining
                    )
                except subprocess.TimeoutExpired:
                    timed_out = True
            serialized = None
            if timed_out:
                start_reaper(process)
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                )
            if process.returncode not in {0, 10}:
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                )
            if process.returncode == 10:
                raise GitHubLinkProviderRejectedError(
                    "Richiesta OAuth GitHub rifiutata."
                )
            if output is None or len(output) > max_response_bytes:
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                )
            try:
                return _strict_json_object(output)
            except Exception:
                raise GitHubLinkProviderUnavailableError(
                    "GitHub non disponibile."
                ) from None
        except GitHubLinkError:
            raise
        except Exception:
            raise GitHubLinkProviderUnavailableError(
                "GitHub non disponibile."
            ) from None
        finally:
            serialized = None
            output = None
            request = None
            process = None
            deadline = 0.0
            if release_termination_slot:
                self._termination_slots.release()
            if release_network_slot:
                self._network_slots.release()

    def exchange_code(self, *, form: Mapping[str, str], timeout_seconds: float, max_response_bytes: int) -> Mapping[str, object]:
        payload = None
        request = None
        try:
            payload = urllib.parse.urlencode(form).encode("ascii")
            form = None
            request = urllib.request.Request(
                _GITHUB_TOKEN_ENDPOINT,
                data=payload,
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            return self._request(request, timeout_seconds, max_response_bytes)
        finally:
            payload = None
            request = None
            form = None

    def read_user(self, *, access_token: str, timeout_seconds: float, max_response_bytes: int) -> Mapping[str, object]:
        request = None
        try:
            request = urllib.request.Request(
                _GITHUB_USER_ENDPOINT,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {access_token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                method="GET",
            )
            return self._request(request, timeout_seconds, max_response_bytes)
        finally:
            access_token = None
            request = None


class InMemoryGitHubLinkFlowStore:
    def __init__(self, *, max_pending_flows: int = 4096) -> None:
        if type(max_pending_flows) is not int or not 1 <= max_pending_flows <= 65536:
            raise GitHubLinkConfigurationError("Cap flow GitHub non valido.")
        self.max_pending_flows = max_pending_flows
        self._flows: dict[str, PendingGitHubLinkFlow] = {}
        self._lock = threading.Lock()

    @staticmethod
    def digest(value: str) -> str:
        return "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()

    def create(self, flow: PendingGitHubLinkFlow) -> None:
        capacity = False
        collision = False
        with self._lock:
            for key in [key for key, current in self._flows.items() if current.expires_at <= flow.created_at]:
                del self._flows[key]
            if len(self._flows) >= self.max_pending_flows:
                capacity = True
            elif flow.state_digest in self._flows:
                collision = True
            else:
                self._flows[flow.state_digest] = flow
        flow = None
        if capacity:
            raise GitHubLinkCapacityError("Capacita flow GitHub esaurita.")
        if collision:
            raise GitHubLinkStateError("Collisione state GitHub.")

    def discard_created(self, state_digest: str, creation_marker: object) -> bool:
        with self._lock:
            flow = self._flows.get(state_digest)
            if flow is None or flow.creation_marker is not creation_marker:
                return False
            del self._flows[state_digest]
            return True

    def consume(self, state: str, browser_binding: str, context: HttpAuthContext, now: datetime) -> PendingGitHubLinkFlow:
        state_digest = self.digest(state)
        browser_digest = self.digest(browser_binding)
        with self._lock:
            flow = self._flows.get(state_digest)
            matches = (
                flow is not None
                and hmac.compare_digest(flow.browser_digest, browser_digest)
                and type(context) is HttpAuthContext
                and type(context.user) is UserAccount
                and type(context.session) is UserSession
                and context.user.active
                and context.user.user_id == flow.user_id
                and context.user.updated_at == flow.user_updated_at
                and context.session.session_id == flow.session_id
                and hmac.compare_digest(context.session.token_digest, flow.session_token_digest)
                and context.session.created_at == flow.session_created_at
                and context.session.user_id == flow.user_id
                and context.session.revoked_at is None
                and context.session.created_at <= now
                and context.session.last_seen_at <= now
                and now < context.session.expires_at
            )
            if matches:
                del self._flows[state_digest]
        state = None
        browser_binding = None
        context = None
        if flow is None or not matches:
            raise GitHubLinkStateError("Flow GitHub non valido o gia usato.")
        if now < flow.created_at or now >= flow.expires_at:
            flow = None
            raise GitHubLinkConsumedStateError("Flow GitHub scaduto.")
        return flow

    def pending_count(self) -> int:
        with self._lock:
            return len(self._flows)


def _credential(value: object, name: str, minimum: int, maximum: int) -> str:
    if type(value) is not str or not minimum <= len(value) <= maximum or _UNRESERVED_RE.fullmatch(value) is None:
        value = None
        raise GitHubLinkConfigurationError(f"Generatore {name} non valido.")
    return value


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise GitHubLinkProviderUnavailableError("Clock GitHub non valido.")
    return value.astimezone(timezone.utc)


class GitHubAccountLinkService:
    def __init__(
        self,
        config: GitHubOAuthConfig,
        flows: InMemoryGitHubLinkFlowStore,
        transport: GitHubOAuthTransport,
        links: ExternalIdentityLinkService,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        state_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        verifier_factory: Callable[[], str] = lambda: secrets.token_urlsafe(64),
        browser_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    ) -> None:
        self.config = config
        self.flows = flows
        self.transport = transport
        self.links = links
        self.clock = clock
        self.state_factory = state_factory
        self.verifier_factory = verifier_factory
        self.browser_factory = browser_factory

    @staticmethod
    def _cookie_name(state: str) -> str:
        return _COOKIE_PREFIX + hashlib.sha256(state.encode("ascii")).hexdigest()[:24]

    def begin_link(self, context: HttpAuthContext) -> GitHubLinkAuthorizationRequest:
        now = _utc(self.clock())
        if (
            type(context) is not HttpAuthContext
            or type(context.user) is not UserAccount
            or type(context.session) is not UserSession
            or not context.user.active
            or context.user.user_id != context.session.user_id
            or context.session.revoked_at is not None
            or now < context.session.created_at
            or now < context.session.last_seen_at
            or now >= context.session.expires_at
        ):
            context = None
            raise GitHubLinkStateError("Sessione TheBitLab non valida.")
        state = _credential(self.state_factory(), "state", 32, 256)
        verifier = _credential(self.verifier_factory(), "PKCE", 43, 128)
        browser = _credential(self.browser_factory(), "browser binding", 32, 256)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        marker = object()
        flow = PendingGitHubLinkFlow(
            state_digest=self.flows.digest(state),
            browser_digest=self.flows.digest(browser),
            code_verifier=verifier,
            creation_marker=marker,
            user_id=context.user.user_id,
            session_id=context.session.session_id,
            session_token_digest=context.session.token_digest,
            session_created_at=context.session.created_at,
            user_updated_at=context.user.updated_at,
            created_at=now,
            expires_at=now + self.config.flow_ttl,
        )
        try:
            self.flows.create(flow)
            query = urllib.parse.urlencode(
                {
                    "client_id": self.config.client_id,
                    "redirect_uri": self.config.redirect_uri,
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                }
            )
            cookie_name = self._cookie_name(state)
            cookie = (
                f"{cookie_name}={browser}; Path=/; Max-Age={math.ceil(self.config.flow_ttl.total_seconds())}; "
                "Secure; HttpOnly; SameSite=Lax"
            )
            return GitHubLinkAuthorizationRequest(
                f"{self.config.authorization_endpoint}?{query}", cookie
            )
        except GitHubLinkError:
            self.flows.discard_created(flow.state_digest, marker)
            raise
        except Exception:
            self.flows.discard_created(flow.state_digest, marker)
            raise GitHubLinkProviderUnavailableError("Avvio linking GitHub non disponibile.")
        finally:
            context = None
            state = None
            verifier = None
            browser = None
            challenge = None
            marker = None
            flow = None

    @staticmethod
    def _callback_values(parameters: Mapping[str, Sequence[str]]) -> tuple[str, str, bool]:
        if not isinstance(parameters, Mapping) or any(key not in {"code", "state", "error", "error_description"} for key in parameters):
            raise GitHubLinkCallbackError("Callback GitHub non valido.")
        normalized = {}
        for key, values in parameters.items():
            if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) != 1 or type(values[0]) is not str or len(values[0]) > 8192:
                raise GitHubLinkCallbackError("Callback GitHub non valido.")
            normalized[key] = values[0]
        state = normalized.get("state")
        provider_error = "error" in normalized
        code = normalized.get("code")
        if (
            type(state) is not str
            or not 32 <= len(state) <= 256
            or _UNRESERVED_RE.fullmatch(state) is None
            or (not provider_error and (type(code) is not str or not code))
        ):
            raise GitHubLinkCallbackError("Callback GitHub non valido.")
        return code or "", state, provider_error

    @classmethod
    def _browser_binding(cls, cookie_header: str | None, state: str) -> tuple[str, str]:
        cookie_name = cls._cookie_name(state)
        try:
            header_size = len(cookie_header.encode("utf-8")) if type(cookie_header) is str else 0
        except UnicodeEncodeError:
            raise GitHubLinkStateError("Cookie linking GitHub non valido.") from None
        invalid = type(cookie_header) is not str or not cookie_header or header_size > _MAX_COOKIE_HEADER_BYTES
        matches = []
        if not invalid:
            for part in cookie_header.split(";"):
                name, separator, value = part.strip().partition("=")
                if separator and name == cookie_name:
                    matches.append(value)
        if len(matches) != 1 or not 32 <= len(matches[0]) <= 256 or _UNRESERVED_RE.fullmatch(matches[0]) is None:
            raise GitHubLinkStateError("Cookie linking GitHub non valido.")
        return matches[0], cookie_name

    @staticmethod
    def _clear_cookie(cookie_name: str) -> str:
        return f"{cookie_name}=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure; HttpOnly; SameSite=Lax"

    def complete_link(
        self,
        parameters: Mapping[str, Sequence[str]],
        *,
        cookie_header: str | None,
        context: HttpAuthContext,
    ) -> GitHubLinkResult:
        flow_consumed = False
        cookie_name = None
        try:
            code, state, provider_error = self._callback_values(parameters)
            browser, cookie_name = self._browser_binding(cookie_header, state)
            try:
                flow = self.flows.consume(state, browser, context, _utc(self.clock()))
            except GitHubLinkConsumedStateError:
                flow_consumed = True
                raise
            flow_consumed = True
            if provider_error:
                raise GitHubLinkCallbackError("Autorizzazione GitHub annullata.")
            token_form = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "code_verifier": flow.code_verifier,
            }
            exchange_rejected = False
            exchange_failed = False
            try:
                token_response = self.transport.exchange_code(
                    form=token_form,
                    timeout_seconds=float(self.config.timeout_seconds),
                    max_response_bytes=self.config.max_response_bytes,
                )
            except GitHubLinkProviderRejectedError:
                exchange_rejected = True
            except Exception:
                exchange_failed = True
            finally:
                token_form = None
                code = None
            if exchange_rejected:
                raise GitHubLinkProviderRejectedError(
                    "Authorization code GitHub rifiutato."
                )
            if exchange_failed:
                raise GitHubLinkProviderUnavailableError(
                    "Token exchange GitHub non disponibile."
                )
            access_token = token_response.get("access_token") if isinstance(token_response, Mapping) else None
            token_type = token_response.get("token_type") if isinstance(token_response, Mapping) else None
            if (
                type(access_token) is not str
                or not 20 <= len(access_token) <= 2048
                or any(ord(character) < 0x21 for character in access_token)
                or type(token_type) is not str
                or token_type.lower() != "bearer"
            ):
                raise GitHubLinkProviderRejectedError("Token GitHub non valido.")
            profile_rejected = False
            profile_failed = False
            try:
                profile = self.transport.read_user(
                    access_token=access_token,
                    timeout_seconds=float(self.config.timeout_seconds),
                    max_response_bytes=self.config.max_response_bytes,
                )
            except GitHubLinkProviderRejectedError:
                profile_rejected = True
            except Exception:
                profile_failed = True
            if profile_rejected or profile_failed:
                access_token = None
                if profile_rejected:
                    raise GitHubLinkProviderRejectedError(
                        "Profilo GitHub rifiutato."
                    )
                raise GitHubLinkProviderUnavailableError(
                    "Profilo GitHub non disponibile."
                )
            github_id = profile.get("id") if isinstance(profile, Mapping) else None
            login = profile.get("login") if isinstance(profile, Mapping) else None
            email = profile.get("email") if isinstance(profile, Mapping) else None
            name = profile.get("name") if isinstance(profile, Mapping) else None
            if (
                type(github_id) is not int
                or isinstance(github_id, bool)
                or github_id <= 0
                or github_id > 9223372036854775807
                or type(login) is not str
                or not login.strip()
                or len(login) > 255
                or any(ord(character) < 0x21 or ord(character) == 0x7F for character in login)
                or (
                    email is not None
                    and (
                        type(email) is not str
                        or not email.strip()
                        or len(email) > 512
                        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in email)
                    )
                )
                or (
                    name is not None
                    and (
                        type(name) is not str
                        or len(name.strip()) > 512
                        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in name)
                    )
                )
                or any(
                    type(value) is str and access_token in value
                    for value in (login, email, name)
                )
            ):
                raise GitHubLinkProviderRejectedError("Profilo GitHub non valido.")
            access_token = None
            assertion_failed = False
            try:
                assertion = FederatedIdentityAssertion(
                    provider="github",
                    subject=str(github_id),
                    display_name=name.strip() if type(name) is str and name.strip() else login.strip(),
                    email=email,
                    email_verified=False,
                    username=login.strip(),
                )
            except Exception:
                assertion_failed = True
            if assertion_failed or assertion is None:
                raise GitHubLinkProviderRejectedError(
                    "Profilo GitHub non valido."
                )
            identity_failed = False
            identity_unavailable = False
            try:
                identity = self.links.link(
                    flow.user_id,
                    assertion,
                    expected_session=context.session,
                    expected_user_updated_at=flow.user_updated_at,
                )
            except AuthApplicationError:
                identity_failed = True
            except Exception:
                identity_unavailable = True
            if identity_unavailable:
                raise GitHubLinkProviderUnavailableError(
                    "Storage linking GitHub non disponibile."
                )
            if identity_failed or identity is None:
                raise GitHubLinkIdentityConflictError(
                    "Account GitHub non collegabile."
                )
            return GitHubLinkResult(identity, self.config.post_link_path, self._clear_cookie(cookie_name))
        except GitHubLinkError as error:
            if flow_consumed and cookie_name is not None:
                error.clear_transaction_cookie = self._clear_cookie(cookie_name)
            raise
        except Exception:
            error = GitHubLinkProviderUnavailableError("Linking GitHub non disponibile.")
            if flow_consumed and cookie_name is not None:
                error.clear_transaction_cookie = self._clear_cookie(cookie_name)
            raise error
        finally:
            parameters = None
            cookie_header = None
            context = None
            code = None
            state = None
            browser = None
            flow = None
            token_response = None
            access_token = None
            token_type = None
            profile = None
            assertion = None
            token_form = None
            exchange_rejected = False
            exchange_failed = False
            profile_rejected = False
            profile_failed = False
            assertion_failed = False
            identity_failed = False
            identity_unavailable = False
