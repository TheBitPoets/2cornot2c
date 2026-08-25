#!/usr/bin/env python3
"""Loopback-only HTTP service for TheBitLab Flowchart Lab.

All artifact semantics live in ``flowchart_lab_core``. Static UI serving is
restricted to three fixed packaged assets; no arbitrary filesystem path is
accepted from HTTP requests.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from scripts import flowchart_lab_core


ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = ROOT / "tools" / "flowchart_lab"
STATIC_ROUTES = {
    "/": (STATIC_ROOT / "index.html", "text/html; charset=utf-8"),
    "/app.css": (STATIC_ROOT / "app.css", "text/css; charset=utf-8"),
    "/app.js": (STATIC_ROOT / "app.js", "text/javascript; charset=utf-8"),
}
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8776
MAX_REQUEST_BYTES = 1024 * 1024
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


def _response(status: int, payload: dict[str, Any]) -> tuple[int, bytes]:
    return status, (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def static_asset(path: str) -> tuple[int, str, bytes] | None:
    """Return one fixed packaged asset; never resolve request-controlled paths."""
    descriptor = STATIC_ROUTES.get(path)
    if descriptor is None:
        return None
    file_path, content_type = descriptor
    try:
        data = file_path.read_bytes()
    except OSError:
        return 500, "application/json; charset=utf-8", _response(500, {"error": "static-asset-unavailable"})[1]
    if len(data) > MAX_STATIC_BYTES:
        return 500, "application/json; charset=utf-8", _response(500, {"error": "static-asset-too-large"})[1]
    return 200, content_type, data


def handle_api_request(method: str, path: str, body: bytes) -> tuple[int, bytes]:
    """Handle one API request without HTTP/server state, for deterministic tests."""
    if method != "POST":
        return _response(405, {"error": "method-not-allowed"})
    if len(body) > MAX_REQUEST_BYTES:
        return _response(413, {"error": "request-too-large"})
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _response(400, {"error": "invalid-json"})
    if not isinstance(payload, dict):
        return _response(400, {"error": "body-must-be-object"})

    artifact = payload.get("artifact")
    if path == "/api/validate":
        errors = flowchart_lab_core.validate_flowchart_artifact(artifact)
        return _response(200, {"valid": not errors, "errors": errors})

    if path == "/api/run":
        inputs = payload.get("inputs", [])
        if not isinstance(inputs, list):
            return _response(400, {"error": "inputs-must-be-list"})
        limits_payload = payload.get("limits", {})
        if not isinstance(limits_payload, dict):
            return _response(400, {"error": "limits-must-be-object"})
        try:
            limits = flowchart_lab_core.ExecutionLimits(
                max_steps=int(limits_payload.get("max_steps", flowchart_lab_core.DEFAULT_MAX_STEPS)),
                max_output_events=int(
                    limits_payload.get("max_output_events", flowchart_lab_core.MAX_OUTPUT_EVENTS)
                ),
            )
            result = flowchart_lab_core.execute_flowchart(artifact, inputs, limits=limits)
        except flowchart_lab_core.FlowchartValidationError as error:
            return _response(422, {"error": "invalid-artifact", "detail": str(error)})
        except flowchart_lab_core.FlowchartExecutionError as error:
            return _response(422, {"error": "execution-error", "detail": str(error)})
        except (TypeError, ValueError) as error:
            return _response(400, {"error": "invalid-limits", "detail": str(error)})
        return _response(200, result)

    return _response(404, {"error": "not-found"})


class FlowchartLabHandler(BaseHTTPRequestHandler):
    server_version = "TheBitLabFlowchartLab/0.1"

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, body: bytes) -> None:
        self._send(status, "application/json; charset=utf-8", body)

    def do_GET(self) -> None:  # noqa: N802
        asset = static_asset(self.path)
        if asset is None:
            self._send_json(*_response(404, {"error": "not-found"}))
            return
        self._send(*asset)

    def do_POST(self) -> None:  # noqa: N802
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except ValueError:
            self._send_json(*_response(400, {"error": "invalid-content-length"}))
            return
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._send_json(*_response(413, {"error": "request-too-large"}))
            return
        body = self.rfile.read(length)
        self._send_json(*handle_api_request("POST", self.path, body))

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve TheBitLab Flowchart Lab on loopback")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    validate_bind_host(args.host)
    if not 1 <= args.port <= 65535:
        raise SystemExit("porta non valida")
    server = ThreadingHTTPServer((args.host, args.port), FlowchartLabHandler)
    print(f"Flowchart Lab: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
