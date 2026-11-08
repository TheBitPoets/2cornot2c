from __future__ import annotations

from contextlib import contextmanager
import http.client
import json
import threading

from scripts import flowchart_lab_server as api
from scripts import flowchart_lab_svg as svg


def artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "out", "type": "output", "expression": "1 + 2"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "out", "label": "next"},
            {"from": "out", "to": "end", "label": "next"},
        ],
    }


@contextmanager
def live_server():
    server = api.create_http_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def post(port: int, path: str, payload: dict) -> tuple[int, dict]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    raw = json.dumps(payload).encode("utf-8")
    connection.request(
        "POST",
        path,
        body=raw,
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    status = response.status
    body = json.loads(response.read().decode("utf-8"))
    connection.close()
    return status, body


def test_svg_endpoint_returns_deterministic_standalone_evidence() -> None:
    with live_server() as port:
        first_status, first = post(port, "/api/svg", {"artifact": artifact()})
        second_status, second = post(port, "/api/svg", {"artifact": artifact()})

    assert first_status == second_status == 200
    assert first == second
    assert first["schema_version"] == svg.SVG_SCHEMA_VERSION
    assert first["media_type"] == "image/svg+xml"
    assert first["filename"] == "algorithm.flow.svg"
    assert first["svg"].startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<script" not in first["svg"].casefold()


def test_svg_endpoint_rejects_invalid_artifact_and_unknown_fields() -> None:
    broken = artifact()
    broken["edges"] = []

    with live_server() as port:
        invalid_status, invalid = post(port, "/api/svg", {"artifact": broken})
        unknown_status, unknown = post(
            port,
            "/api/svg",
            {"artifact": artifact(), "path": "/tmp/output.svg"},
        )

    assert invalid_status == 422
    assert invalid["error"] == "flowchart_validation_error"
    assert unknown_status == 400
    assert unknown["error"] == "invalid_request"
