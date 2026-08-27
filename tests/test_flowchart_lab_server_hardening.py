from __future__ import annotations

from contextlib import contextmanager
import http.client
import json
import threading

from scripts import flowchart_lab_server as api


def sum_artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "a", "type": "input", "target": "a", "data_type": "int"},
            {"id": "b", "type": "input", "target": "b", "data_type": "int"},
            {"id": "sum", "type": "assign", "target": "totale", "expression": "a + b"},
            {"id": "out", "type": "output", "expression": "totale"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "a", "label": "next"},
            {"from": "a", "to": "b", "label": "next"},
            {"from": "b", "to": "sum", "label": "next"},
            {"from": "sum", "to": "out", "label": "next"},
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


def raw_json_request(port: int, body: bytes) -> tuple[int, dict]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request(
        "POST",
        "/api/run",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    status = response.status
    payload = json.loads(response.read().decode("utf-8"))
    connection.close()
    return status, payload


def test_duplicate_json_keys_are_rejected() -> None:
    with live_server() as port:
        status, payload = raw_json_request(
            port,
            b'{"artifact":{},"artifact":{},"inputs":[]}',
        )

    assert status == 400
    assert payload["error"] == "invalid_json"


def test_non_standard_nan_json_constant_is_rejected() -> None:
    with live_server() as port:
        status, payload = raw_json_request(
            port,
            b'{"artifact":{},"inputs":[NaN]}',
        )

    assert status == 400
    assert payload["error"] == "invalid_json"


def test_interactive_api_cannot_raise_step_limit_above_default_bound() -> None:
    body = json.dumps(
        {
            "artifact": sum_artifact(),
            "inputs": [2, 3],
            "limits": {"max_steps": api.MAX_API_STEPS + 1},
        }
    ).encode("utf-8")

    with live_server() as port:
        status, payload = raw_json_request(port, body)

    assert status == 400
    assert payload["error"] == "invalid_request"
    assert str(api.MAX_API_STEPS) in payload["message"]
