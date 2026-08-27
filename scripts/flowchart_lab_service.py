#!/usr/bin/env python3
"""Compatibility facade for the original Flowchart Lab service API.

The production HTTP implementation is ``scripts.flowchart_lab_server``.
This module keeps the earlier pure-function test/API surface available while
routing execution semantics and actual server startup through the canonical
implementation. It must not grow a second HTTP/runtime implementation.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from scripts import (
    flowchart_lab_core,
    flowchart_lab_server,
    flowchart_lab_workspace,
)


ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = ROOT / "tools" / "flowchart_lab"
# Legacy aliases retained only for deterministic compatibility tests/callers.
STATIC_ROUTES = {
    "/": (STATIC_ROOT / "index.html", "text/html; charset=utf-8"),
    "/app.css": (STATIC_ROOT / "app.css", "text/css; charset=utf-8"),
    "/app.js": (STATIC_ROOT / "app.js", "text/javascript; charset=utf-8"),
}
DEFAULT_HOST = flowchart_lab_server.DEFAULT_HOST
DEFAULT_PORT = 8776
MAX_REQUEST_BYTES = flowchart_lab_server.MAX_REQUEST_BYTES
MAX_STATIC_BYTES = 512 * 1024


def is_loopback_host(host: str) -> bool:
    value = str(host or "").strip().lower()
    if value == "localhost":
        return True
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def validate_bind_host(host: str) -> None:
    if not is_loopback_host(host):
        raise ValueError("Flowchart Lab può essere esposto solo su loopback")


def valid_host_header(value: str) -> bool:
    """Accept only loopback Host headers, with an optional numeric port."""
    text = str(value or "").strip()
    if not text or any(character in text for character in ("/", "\\", "@", " ", "\t", "\r", "\n")):
        return False
    try:
        parsed = urlsplit(f"//{text}")
        hostname = parsed.hostname or ""
        port = parsed.port
    except ValueError:
        return False
    if port is not None and not 1 <= port <= 65535:
        return False
    return is_loopback_host(hostname)


def _response(status: int, payload: dict[str, Any]) -> tuple[int, bytes]:
    return status, (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def static_asset(path: str) -> tuple[int, str, bytes] | None:
    """Return one fixed packaged asset; never resolve request-controlled paths."""
    descriptor = STATIC_ROUTES.get(path)
    if descriptor is None:
        return None
    file_path, content_type = descriptor
    try:
        resolved_root = STATIC_ROOT.resolve(strict=True)
        resolved = file_path.resolve(strict=True)
        if resolved.parent != resolved_root or resolved.is_symlink():
            return 500, "application/json; charset=utf-8", _response(500, {"error": "static-asset-unavailable"})[1]
        data = resolved.read_bytes()
    except OSError:
        return 500, "application/json; charset=utf-8", _response(500, {"error": "static-asset-unavailable"})[1]
    if len(data) > MAX_STATIC_BYTES:
        return 500, "application/json; charset=utf-8", _response(500, {"error": "static-asset-too-large"})[1]
    return 200, content_type, data


def load_workspace_artifact(
    store: flowchart_lab_workspace.FlowchartWorkspaceStore | None,
) -> tuple[int, bytes]:
    if store is None:
        return _response(503, {"error": "workspace-unavailable"})
    try:
        artifact = store.load()
    except flowchart_lab_workspace.FlowchartWorkspaceError as error:
        return _response(422, {"error": "workspace-error", "detail": str(error)})
    if artifact is None:
        return _response(404, {"error": "artifact-not-found"})
    return _response(200, {"artifact": artifact})


def _parse_legacy_payload(body: bytes) -> tuple[dict[str, Any] | None, tuple[int, bytes] | None]:
    if len(body) > MAX_REQUEST_BYTES:
        return None, _response(413, {"error": "request-too-large"})
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, _response(400, {"error": "invalid-json"})
    if not isinstance(payload, dict):
        return None, _response(400, {"error": "body-must-be-object"})
    return payload, None


def handle_api_request(
    method: str,
    path: str,
    body: bytes,
    *,
    store: flowchart_lab_workspace.FlowchartWorkspaceStore | None = None,
) -> tuple[int, bytes]:
    """Keep the original deterministic helper while using the canonical service."""
    if method != "POST":
        return _response(405, {"error": "method-not-allowed"})
    payload, error = _parse_legacy_payload(body)
    if error is not None:
        return error
    assert payload is not None

    canonical = flowchart_lab_server.FlowchartLabService(workspace_store=store)
    try:
        if path == "/api/validate":
            result = canonical.validate(payload)
            return _response(200, {"valid": result["valid"], "errors": result["errors"]})
        if path == "/api/run":
            if not isinstance(payload.get("inputs", []), list):
                return _response(400, {"error": "inputs-must-be-list"})
            if not isinstance(payload.get("limits", {}), dict):
                return _response(400, {"error": "limits-must-be-object"})
            try:
                result = canonical.run(payload)
            except flowchart_lab_core.FlowchartValidationError as exc:
                return _response(422, {"error": "invalid-artifact", "detail": str(exc)})
            except flowchart_lab_core.FlowchartExecutionError as exc:
                return _response(422, {"error": "execution-error", "detail": str(exc)})
            except flowchart_lab_server.FlowchartLabAPIError as exc:
                return _response(400, {"error": "invalid-limits", "detail": exc.message})
            return _response(200, result)
        if path == "/api/artifact":
            if store is None:
                return _response(503, {"error": "workspace-unavailable"})
            try:
                result = canonical.workspace_save(payload)
            except flowchart_lab_core.FlowchartValidationError as exc:
                return _response(422, {"error": "invalid-artifact", "detail": str(exc)})
            except flowchart_lab_server.FlowchartLabAPIError as exc:
                if exc.code == "flowchart_validation_error":
                    legacy_error = "invalid-artifact"
                elif exc.code == "workspace_error":
                    legacy_error = "workspace-error"
                else:
                    legacy_error = exc.code
                return _response(exc.status, {"error": legacy_error, "detail": exc.message})
            return _response(200, {"saved": result["saved"], "artifact_name": result["artifact_name"]})
    except flowchart_lab_server.FlowchartLabAPIError as exc:
        return _response(exc.status, {"error": exc.code, "detail": exc.message})
    return _response(404, {"error": "not-found"})


def main() -> int:
    """Legacy CLI that delegates all networking to flowchart_lab_server."""
    parser = argparse.ArgumentParser(description="Serve TheBitLab Flowchart Lab on loopback")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Managed assignment workspace. Enables algorithm.flow.json save/load.",
    )
    args = parser.parse_args()
    validate_bind_host(args.host)
    try:
        server = flowchart_lab_server.create_http_server(
            host=args.host,
            port=args.port,
            workspace_root=args.workspace,
        )
    except (OSError, ValueError, RuntimeError, FileNotFoundError) as error:
        print(f"Flowchart Lab non avviato: {error}")
        return 1
    host, port = server.server_address[:2]
    print(f"Flowchart Lab: http://{host}:{port}/ (canonical server)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
