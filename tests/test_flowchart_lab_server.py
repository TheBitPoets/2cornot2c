from __future__ import annotations

from contextlib import contextmanager
import http.client
import json
import threading
from typing import Any

import pytest

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
def live_server(service: api.FlowchartLabService | None = None):
    server = api.create_http_server(port=0, service=service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(
    port: int,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    selected_headers = dict(headers or {})
    if body is not None:
        selected_headers.setdefault("Content-Type", "application/json")
    connection.request(method, path, body=body, headers=selected_headers)
    response = connection.getresponse()
    raw = response.read()
    status = response.status
    connection.close()
    value = json.loads(raw.decode("utf-8")) if raw else {}
    return status, value


def test_server_rejects_non_loopback_bind() -> None:
    with pytest.raises(ValueError, match="loopback"):
        api.create_http_server(host="0.0.0.0", port=0)


def test_health_exposes_only_service_contract() -> None:
    with live_server() as port:
        status, body = request(port, "GET", "/api/health")

    assert status == 200
    assert body["schema_version"] == api.SERVICE_SCHEMA_VERSION
    assert body["status"] == "ok"
    assert body["flowchart_schema_version"] == "thebitlab.flowchart.v1"
    assert body["trace_schema_version"] == "thebitlab.flowtrace.v1"


def test_validate_reports_structural_errors_without_executing() -> None:
    artifact = sum_artifact()
    artifact["edges"] = artifact["edges"][:-1]

    with live_server() as port:
        status, body = request(port, "POST", "/api/validate", {"artifact": artifact})

    assert status == 200
    assert body["valid"] is False
    assert body["errors"]
    assert any("arco next" in message for message in body["errors"])


def test_run_returns_canonical_deterministic_trace() -> None:
    with live_server() as port:
        status, body = request(
            port,
            "POST",
            "/api/run",
            {"artifact": sum_artifact(), "inputs": [2, 3]},
        )

    assert status == 200
    assert body["schema_version"] == "thebitlab.flowtrace.v1"
    assert body["status"] == "completed"
    assert body["outputs"] == [5]
    assert body["final_variables"] == {"a": 2, "b": 3, "totale": 5}
    assert body["executed_node_ids"] == ["start", "a", "b", "sum", "out", "end"]


def test_session_step_and_reset_are_views_over_the_run_trace() -> None:
    artifact = sum_artifact()
    with live_server() as port:
        run_status, run = request(
            port,
            "POST",
            "/api/run",
            {"artifact": artifact, "inputs": [4, 7]},
        )
        session_status, created = request(
            port,
            "POST",
            "/api/session",
            {"artifact": artifact, "inputs": [4, 7]},
        )
        session_id = created["session_id"]

        events = []
        states = []
        while True:
            status, stepped = request(
                port,
                "POST",
                "/api/step",
                {"session_id": session_id},
            )
            assert status == 200
            states.append(stepped)
            if stepped["event"] is not None:
                events.append(stepped["event"])
            if stepped["done"]:
                break

        reset_status, reset = request(
            port,
            "POST",
            "/api/reset",
            {"session_id": session_id},
        )
        next_status, first_again = request(
            port,
            "POST",
            "/api/step",
            {"session_id": session_id},
        )

    assert run_status == session_status == 200
    assert events == run["trace"]
    assert states[-1]["outputs"] == run["outputs"]
    assert states[-1]["variables"] == run["final_variables"]
    assert reset_status == 200
    assert reset["cursor"] == 0
    assert reset["done"] is False
    assert reset["outputs"] == []
    assert reset["variables"] == {}
    assert next_status == 200
    assert first_again["event"] == run["trace"][0]


def test_unknown_and_deleted_sessions_are_404() -> None:
    with live_server() as port:
        status, body = request(
            port,
            "POST",
            "/api/step",
            {"session_id": "missing"},
        )
        _, created = request(
            port,
            "POST",
            "/api/session",
            {"artifact": sum_artifact(), "inputs": [1, 2]},
        )
        deleted_status, deleted = request(
            port,
            "POST",
            "/api/session/delete",
            {"session_id": created["session_id"]},
        )
        after_status, _ = request(
            port,
            "POST",
            "/api/step",
            {"session_id": created["session_id"]},
        )

    assert status == 404
    assert body["error"] == "session_not_found"
    assert deleted_status == 200
    assert deleted["deleted"] is True
    assert after_status == 404


def test_session_store_is_bounded_and_evicts_lru() -> None:
    service = api.FlowchartLabService(max_sessions=2)
    payload = {"artifact": sum_artifact(), "inputs": [1, 2]}

    first = service.create_session(payload)["session_id"]
    second = service.create_session(payload)["session_id"]
    service.step({"session_id": first})
    third = service.create_session(payload)["session_id"]

    assert len({first, second, third}) == 3
    assert service.step({"session_id": first})["session_id"] == first
    assert service.step({"session_id": third})["session_id"] == third
    with pytest.raises(api.FlowchartLabAPIError) as error:
        service.step({"session_id": second})
    assert error.value.status == 404


def test_session_ttl_expires_without_background_thread() -> None:
    now = [100.0]
    service = api.FlowchartLabService(
        max_sessions=2,
        session_ttl_seconds=10,
        clock=lambda: now[0],
    )
    session_id = service.create_session(
        {"artifact": sum_artifact(), "inputs": [1, 2]}
    )["session_id"]
    now[0] += 11

    with pytest.raises(api.FlowchartLabAPIError) as error:
        service.step({"session_id": session_id})
    assert error.value.status == 404
    assert service.health()["active_sessions"] == 0


def test_invalid_json_media_type_and_payload_limits_fail_closed() -> None:
    with live_server() as port:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.request(
            "POST",
            "/api/run",
            body=b"{",
            headers={"Content-Type": "application/json"},
        )
        invalid_json = connection.getresponse()
        invalid_status = invalid_json.status
        invalid_body = json.loads(invalid_json.read().decode("utf-8"))
        connection.close()

        status_media, body_media = request(
            port,
            "POST",
            "/api/run",
            {"artifact": sum_artifact()},
            headers={"Content-Type": "text/plain"},
        )

        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.putrequest("POST", "/api/run")
        connection.putheader("Host", f"127.0.0.1:{port}")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(api.MAX_REQUEST_BYTES + 1))
        connection.endheaders()
        too_large = connection.getresponse()
        too_large_status = too_large.status
        too_large_body = json.loads(too_large.read().decode("utf-8"))
        connection.close()

    assert invalid_status == 400
    assert invalid_body["error"] == "invalid_json"
    assert status_media == 415
    assert body_media["error"] == "unsupported_media_type"
    assert too_large_status == 413
    assert too_large_body["error"] == "payload_too_large"


def test_dns_rebinding_style_host_and_remote_origin_are_rejected() -> None:
    with live_server() as port:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        connection.putrequest("GET", "/api/health", skip_host=True)
        connection.putheader("Host", "evil.example")
        connection.endheaders()
        host_response = connection.getresponse()
        host_status = host_response.status
        host_body = json.loads(host_response.read().decode("utf-8"))
        connection.close()

        status_origin, body_origin = request(
            port,
            "GET",
            "/api/health",
            headers={"Origin": "https://evil.example"},
        )

    assert host_status == 403
    assert host_body["error"] == "loopback_only"
    assert status_origin == 403
    assert body_origin["error"] == "loopback_only"


def test_no_filesystem_or_static_file_surface_is_exposed() -> None:
    with live_server() as port:
        get_status, get_body = request(port, "GET", "/etc/passwd")
        post_status, post_body = request(
            port,
            "POST",
            "/api/file",
            {"path": "../../etc/passwd"},
        )

    assert get_status == 404
    assert get_body["error"] == "not_found"
    assert post_status == 404
    assert post_body["error"] == "not_found"


def test_flowchart_errors_are_sanitized_and_no_traceback_leaks() -> None:
    invalid = sum_artifact()
    invalid["nodes"][3]["expression"] = "__import__('os')"

    with live_server() as port:
        validation_status, validation = request(
            port,
            "POST",
            "/api/run",
            {"artifact": invalid, "inputs": [1, 2]},
        )
        execution_status, execution = request(
            port,
            "POST",
            "/api/run",
            {"artifact": sum_artifact(), "inputs": [1]},
        )

    assert validation_status == 422
    assert validation["error"] == "flowchart_validation_error"
    assert execution_status == 422
    assert execution["error"] == "flowchart_execution_error"
    assert "Traceback" not in json.dumps(validation)
    assert "Traceback" not in json.dumps(execution)


def test_limits_are_explicit_and_unknown_fields_are_rejected() -> None:
    with live_server() as port:
        status, body = request(
            port,
            "POST",
            "/api/run",
            {
                "artifact": sum_artifact(),
                "inputs": [2, 3],
                "limits": {"max_steps": 3},
            },
        )
        unknown_status, unknown = request(
            port,
            "POST",
            "/api/run",
            {"artifact": sum_artifact(), "inputs": [2, 3], "path": "/tmp"},
        )

    assert status == 200
    assert body["status"] == "limit-exceeded"
    assert body["steps"] == 3
    assert unknown_status == 400
    assert unknown["error"] == "invalid_request"
