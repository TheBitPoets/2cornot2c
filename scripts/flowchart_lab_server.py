#!/usr/bin/env python3
"""Loopback-only HTTP service for TheBitLab Flowchart Lab v1.

Flowchart semantics live exclusively in ``scripts.flowchart_lab_core``. Run
executes the canonical core once; Step and Reset only navigate that trace. The
browser UI is served from an exact whitelist. Optional workspace persistence is
confined to one launcher-selected root and one fixed artifact filename.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import secrets
import threading
import time
from typing import Any, Callable
from urllib.parse import urlparse

from scripts import flowchart_lab_core as flow
from scripts import flowchart_lab_svg as flow_svg
from scripts import flowchart_lab_workspace as flow_workspace


SERVICE_SCHEMA_VERSION = "thebitlab.flowchart-lab-service.v1"
SESSION_SCHEMA_VERSION = "thebitlab.flowchart-session.v1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8771
MAX_REQUEST_BYTES = 1024 * 1024
MAX_INPUT_VALUES = 512
MAX_API_STEPS = flow.DEFAULT_MAX_STEPS
MAX_SESSIONS = 64
SESSION_TTL_SECONDS = 30 * 60
REQUEST_SOCKET_TIMEOUT_SECONDS = 5
APP_ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = APP_ROOT / "tools" / "flowchart_lab"
UI_STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/flowchart-lab": ("index.html", "text/html; charset=utf-8"),
    "/flowchart-lab/": ("index.html", "text/html; charset=utf-8"),
    "/flowchart-lab/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/flowchart-lab/style.css": ("app.css", "text/css; charset=utf-8"),
}
UI_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
    "base-uri 'none'; frame-ancestors 'none'"
)


class FlowchartLabAPIError(ValueError):
    """Expected client-facing API error with an HTTP status/code."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


@dataclass
class TraceSession:
    session_id: str
    result: dict[str, Any]
    cursor: int
    created_at: float
    touched_at: float


def _require_object(value: Any, label: str = "payload") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FlowchartLabAPIError(400, "invalid_request", f"{label} deve essere un oggetto JSON")
    return value


def _reject_unknown_fields(payload: dict[str, Any], allowed: set[str]) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise FlowchartLabAPIError(
            400,
            "invalid_request",
            "campi non supportati: " + ", ".join(unknown),
        )


def _inputs(payload: dict[str, Any]) -> list[Any]:
    values = payload.get("inputs", [])
    if not isinstance(values, list):
        raise FlowchartLabAPIError(400, "invalid_request", "inputs deve essere una lista")
    if len(values) > MAX_INPUT_VALUES:
        raise FlowchartLabAPIError(413, "too_many_inputs", "troppi valori input")
    return values


def _limits(payload: dict[str, Any]) -> flow.ExecutionLimits:
    raw = payload.get("limits")
    if raw is None:
        return flow.ExecutionLimits()
    if not isinstance(raw, dict):
        raise FlowchartLabAPIError(400, "invalid_request", "limits deve essere un oggetto")
    _reject_unknown_fields(raw, {"max_steps", "max_output_events"})
    kwargs: dict[str, int] = {}
    for name in ("max_steps", "max_output_events"):
        if name not in raw:
            continue
        value = raw[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise FlowchartLabAPIError(400, "invalid_request", f"limits.{name} deve essere intero")
        kwargs[name] = value
    if kwargs.get("max_steps", MAX_API_STEPS) > MAX_API_STEPS:
        raise FlowchartLabAPIError(
            400,
            "invalid_request",
            f"limits.max_steps non può superare {MAX_API_STEPS} nel servizio interattivo",
        )
    try:
        return flow.ExecutionLimits(**kwargs)
    except ValueError as error:
        raise FlowchartLabAPIError(400, "invalid_request", str(error)) from error


class FlowchartLabService:
    """Bounded in-memory facade over the canonical deterministic core."""

    def __init__(
        self,
        *,
        max_sessions: int = MAX_SESSIONS,
        session_ttl_seconds: int = SESSION_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        workspace_store: flow_workspace.FlowchartWorkspaceStore | None = None,
    ) -> None:
        if max_sessions < 1:
            raise ValueError("max_sessions deve essere positivo")
        if session_ttl_seconds < 1:
            raise ValueError("session_ttl_seconds deve essere positivo")
        self.max_sessions = max_sessions
        self.session_ttl_seconds = session_ttl_seconds
        self._clock = clock
        self._lock = threading.RLock()
        self._sessions: OrderedDict[str, TraceSession] = OrderedDict()
        self._workspace_store = workspace_store

    def health(self) -> dict[str, Any]:
        with self._lock:
            self._purge_expired()
            active_sessions = len(self._sessions)
        return {
            "schema_version": SERVICE_SCHEMA_VERSION,
            "status": "ok",
            "flowchart_schema_version": flow.SCHEMA_VERSION,
            "trace_schema_version": flow.TRACE_SCHEMA_VERSION,
            "svg_schema_version": flow_svg.SVG_SCHEMA_VERSION,
            "active_sessions": active_sessions,
            "max_sessions": self.max_sessions,
            "workspace_configured": self._workspace_store is not None,
        }

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"artifact"})
        artifact = _require_object(payload.get("artifact"), "artifact")
        errors = flow.validate_flowchart_artifact(artifact)
        return {
            "schema_version": SERVICE_SCHEMA_VERSION,
            "valid": not errors,
            "errors": errors,
        }

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"artifact", "inputs", "limits"})
        artifact = _require_object(payload.get("artifact"), "artifact")
        return flow.execute_flowchart(artifact, _inputs(payload), limits=_limits(payload))

    def render_svg(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"artifact"})
        artifact = _require_object(payload.get("artifact"), "artifact")
        rendered = flow_svg.render_flowchart_svg(artifact)
        return {
            "schema_version": flow_svg.SVG_SCHEMA_VERSION,
            "media_type": "image/svg+xml",
            "filename": "algorithm.flow.svg",
            "svg": rendered,
        }

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"artifact", "inputs", "limits"})
        result = self.run(payload)
        now = self._clock()
        session = TraceSession(
            session_id=secrets.token_urlsafe(24),
            result=result,
            cursor=0,
            created_at=now,
            touched_at=now,
        )
        with self._lock:
            self._purge_expired(now)
            while len(self._sessions) >= self.max_sessions:
                self._sessions.popitem(last=False)
            self._sessions[session.session_id] = session
        return self._session_state(session, event=None)

    def step(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"session_id"})
        session_id = self._session_id(payload.get("session_id"))
        with self._lock:
            session = self._get_session_locked(session_id)
            trace = session.result["trace"]
            event = trace[session.cursor] if session.cursor < len(trace) else None
            if event is not None:
                session.cursor += 1
            session.touched_at = self._clock()
            self._sessions.move_to_end(session.session_id)
            return self._session_state(session, event=event)

    def reset(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"session_id"})
        session_id = self._session_id(payload.get("session_id"))
        with self._lock:
            session = self._get_session_locked(session_id)
            session.cursor = 0
            session.touched_at = self._clock()
            self._sessions.move_to_end(session.session_id)
            return self._session_state(session, event=None)

    def delete_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"session_id"})
        session_id = self._session_id(payload.get("session_id"))
        with self._lock:
            self._purge_expired()
            if self._sessions.pop(session_id, None) is None:
                raise FlowchartLabAPIError(404, "session_not_found", "sessione non trovata")
        return {
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_id": session_id,
            "deleted": True,
        }

    def workspace_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, set())
        store = self._require_workspace()
        try:
            return store.status()
        except flow_workspace.FlowchartWorkspaceError as error:
            raise FlowchartLabAPIError(409, "workspace_error", str(error)) from error

    def workspace_load(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, set())
        store = self._require_workspace()
        try:
            return store.load_response()
        except flow_workspace.FlowchartWorkspaceError as error:
            raise FlowchartLabAPIError(409, "workspace_error", str(error)) from error

    def workspace_save(self, payload: dict[str, Any]) -> dict[str, Any]:
        _reject_unknown_fields(payload, {"artifact"})
        artifact = _require_object(payload.get("artifact"), "artifact")
        store = self._require_workspace()
        try:
            return store.save_response(artifact)
        except flow.FlowchartValidationError as error:
            raise FlowchartLabAPIError(422, "flowchart_validation_error", str(error)) from error
        except flow_workspace.FlowchartWorkspaceError as error:
            raise FlowchartLabAPIError(409, "workspace_error", str(error)) from error

    def _require_workspace(self) -> flow_workspace.FlowchartWorkspaceStore:
        if self._workspace_store is None:
            raise FlowchartLabAPIError(
                409,
                "workspace_unavailable",
                "Flowchart Lab non è stato avviato con una workspace gestita",
            )
        return self._workspace_store

    def _session_id(self, value: Any) -> str:
        if not isinstance(value, str) or not value or len(value) > 128:
            raise FlowchartLabAPIError(400, "invalid_request", "session_id non valido")
        return value

    def _get_session_locked(self, session_id: str) -> TraceSession:
        self._purge_expired()
        session = self._sessions.get(session_id)
        if session is None:
            raise FlowchartLabAPIError(404, "session_not_found", "sessione non trovata")
        return session

    def _purge_expired(self, now: float | None = None) -> None:
        current = self._clock() if now is None else now
        expired = [
            session_id
            for session_id, session in self._sessions.items()
            if current - session.touched_at > self.session_ttl_seconds
        ]
        for session_id in expired:
            self._sessions.pop(session_id, None)

    def _session_state(
        self,
        session: TraceSession,
        *,
        event: dict[str, Any] | None,
    ) -> dict[str, Any]:
        trace = session.result["trace"]
        cursor = session.cursor
        emitted = trace[:cursor]
        outputs = [item["output"] for item in emitted if "output" in item]
        variables = emitted[-1]["variables_after"] if emitted else {}
        return {
            "schema_version": SESSION_SCHEMA_VERSION,
            "session_id": session.session_id,
            "cursor": cursor,
            "total_steps": len(trace),
            "done": cursor >= len(trace),
            "event": event,
            "outputs": outputs,
            "variables": dict(variables),
            "run_status": session.result["status"],
            "termination_reason": session.result["termination_reason"],
        }


def _hostname_from_authority(authority: str) -> str | None:
    if not authority:
        return None
    try:
        return urlparse("//" + authority).hostname
    except ValueError:
        return None


def _is_loopback_host(value: str | None) -> bool:
    if value is None:
        return False
    if value.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def _origin_is_local(origin: str | None) -> bool:
    if origin is None:
        return True
    try:
        parsed = urlparse(origin)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and _is_loopback_host(parsed.hostname)


class _StrictJSONError(ValueError):
    pass


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _StrictJSONError(f"chiave JSON duplicata: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise _StrictJSONError(f"costante JSON non valida: {value}")


def _ui_asset(route: str) -> tuple[Path, str] | None:
    configured = UI_STATIC_ROUTES.get(route)
    if configured is None:
        return None
    filename, content_type = configured
    root = UI_ROOT.resolve(strict=True)
    path = (UI_ROOT / filename).resolve(strict=True)
    if path.parent != root or path.is_symlink() or not path.is_file():
        raise RuntimeError(f"asset UI Flowchart Lab non sicuro: {filename}")
    return path, content_type


def make_handler(service: FlowchartLabService) -> type[BaseHTTPRequestHandler]:
    class FlowchartLabHandler(BaseHTTPRequestHandler):
        server_version = "TheBitLab-FlowchartLab/1"
        sys_version = ""

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(REQUEST_SOCKET_TIMEOUT_SECONDS)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if not self._authorized_request():
                return
            parsed = urlparse(self.path)
            if parsed.query or parsed.fragment:
                self._send_error(404, "not_found", "endpoint non trovato")
                return
            if parsed.path == "/api/health":
                self._send_json(200, service.health())
                return
            try:
                asset = _ui_asset(parsed.path)
            except (OSError, RuntimeError):
                self._send_error(500, "internal_error", "asset Flowchart Lab non disponibile")
                return
            if asset is not None:
                path, content_type = asset
                self._send_static(path, content_type)
                return
            self._send_error(404, "not_found", "endpoint non trovato")

        def do_POST(self) -> None:
            if not self._authorized_request():
                return
            parsed = urlparse(self.path)
            if parsed.query or parsed.fragment:
                self._send_error(404, "not_found", "endpoint non trovato")
                return
            routes = {
                "/api/validate": service.validate,
                "/api/run": service.run,
                "/api/svg": service.render_svg,
                "/api/session": service.create_session,
                "/api/step": service.step,
                "/api/reset": service.reset,
                "/api/session/delete": service.delete_session,
                "/api/workspace/status": service.workspace_status,
                "/api/workspace/load": service.workspace_load,
                "/api/workspace/save": service.workspace_save,
            }
            action = routes.get(parsed.path)
            if action is None:
                self._send_error(404, "not_found", "endpoint non trovato")
                return
            try:
                payload = self._read_json()
                result = action(payload)
            except FlowchartLabAPIError as error:
                self._send_error(error.status, error.code, error.message)
                return
            except flow.FlowchartValidationError as error:
                self._send_error(422, "flowchart_validation_error", str(error))
                return
            except flow.FlowchartExecutionError as error:
                self._send_error(422, "flowchart_execution_error", str(error))
                return
            except Exception:
                self._send_error(500, "internal_error", "errore interno del Flowchart Lab")
                return
            self._send_json(200, result)

        def do_OPTIONS(self) -> None:
            if not self._authorized_request():
                return
            self.send_response(204)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _authorized_request(self) -> bool:
            try:
                client_ip = ipaddress.ip_address(self.client_address[0])
            except ValueError:
                client_ip = None
            host = _hostname_from_authority(self.headers.get("Host", ""))
            origin = self.headers.get("Origin")
            if (
                client_ip is None
                or not client_ip.is_loopback
                or not _is_loopback_host(host)
                or not _origin_is_local(origin)
            ):
                self._send_error(403, "loopback_only", "servizio disponibile solo da loopback locale")
                return False
            return True

        def _read_json(self) -> dict[str, Any]:
            content_type = self.headers.get_content_type()
            if content_type != "application/json":
                raise FlowchartLabAPIError(
                    415,
                    "unsupported_media_type",
                    "Content-Type deve essere application/json",
                )
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise FlowchartLabAPIError(411, "length_required", "Content-Length richiesto")
            try:
                length = int(raw_length)
            except ValueError as error:
                raise FlowchartLabAPIError(400, "invalid_request", "Content-Length non valido") from error
            if length < 0:
                raise FlowchartLabAPIError(400, "invalid_request", "Content-Length non valido")
            if length > MAX_REQUEST_BYTES:
                raise FlowchartLabAPIError(413, "payload_too_large", "payload troppo grande")
            try:
                body = self.rfile.read(length)
            except TimeoutError as error:
                raise FlowchartLabAPIError(408, "request_timeout", "lettura richiesta scaduta") from error
            try:
                value = json.loads(
                    body.decode("utf-8"),
                    object_pairs_hook=_unique_json_object,
                    parse_constant=_reject_json_constant,
                )
            except (UnicodeDecodeError, json.JSONDecodeError, _StrictJSONError) as error:
                raise FlowchartLabAPIError(400, "invalid_json", "JSON non valido") from error
            return _require_object(value)

        def _send_error(self, status: int, code: str, message: str) -> None:
            self._send_json(
                status,
                {
                    "schema_version": SERVICE_SCHEMA_VERSION,
                    "error": code,
                    "message": message,
                },
            )

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_static(self, path: Path, content_type: str) -> None:
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", UI_CONTENT_SECURITY_POLICY)
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return FlowchartLabHandler


def create_http_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    service: FlowchartLabService | None = None,
    workspace_root: Path | None = None,
) -> ThreadingHTTPServer:
    if not _is_loopback_host(host):
        raise ValueError("Flowchart Lab deve usare un indirizzo IP loopback")
    if host != DEFAULT_HOST:
        raise ValueError(f"host supportato in v1: {DEFAULT_HOST}")
    if not 0 <= port <= 65535:
        raise ValueError("porta non valida")
    if service is not None and workspace_root is not None:
        raise ValueError("workspace_root non può essere combinata con un service già costruito")
    for route in UI_STATIC_ROUTES:
        _ui_asset(route)
    if service is None:
        store = (
            flow_workspace.FlowchartWorkspaceStore(workspace_root)
            if workspace_root is not None
            else None
        )
        service = FlowchartLabService(workspace_store=store)
    server = ThreadingHTTPServer((host, port), make_handler(service))
    server.daemon_threads = True
    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avvia il Flowchart Lab gestito su loopback locale.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        help="Workspace studente già risolta dal runtime; abilita save/load del solo algorithm.flow.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        server = create_http_server(
            host=args.host,
            port=args.port,
            workspace_root=args.workspace_root,
        )
    except (OSError, ValueError, RuntimeError, FileNotFoundError) as error:
        print(f"Flowchart Lab non avviato: {error}")
        return 1
    host, port = server.server_address[:2]
    print(f"Flowchart Lab: http://{host}:{port}/")
    print(f"Health: http://{host}:{port}/api/health")
    if args.workspace_root is not None:
        print(f"Workspace artifact: {flow_workspace.ARTIFACT_NAME}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
