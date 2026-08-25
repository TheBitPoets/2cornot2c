#!/usr/bin/env python3
"""Loopback-only HTTP service for TheBitLab Flowchart Lab.

The service is intentionally thin: all artifact semantics live in
``flowchart_lab_core``. V1 API accepts artifacts in request bodies and does not
read arbitrary filesystem paths.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from scripts import flowchart_lab_core


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8776
MAX_REQUEST_BYTES = 1024 * 1024


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

    def _send_json(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._send_json(*_response(404, {"error": "not-found"}))

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
        # Avoid noisy/default request logging in classroom terminals. The future
        # managed launcher can add bounded structured logs when needed.
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve TheBitLab Flowchart Lab core on loopback")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    validate_bind_host(args.host)
    if not 1 <= args.port <= 65535:
        raise SystemExit("porta non valida")
    server = ThreadingHTTPServer((args.host, args.port), FlowchartLabHandler)
    print(f"Flowchart Lab core API: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
