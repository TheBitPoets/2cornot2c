from __future__ import annotations

import json

import pytest

from scripts import flowchart_lab_service as service


def artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "read", "type": "input", "target": "n", "data_type": "int"},
            {"id": "out", "type": "output", "expression": "n * 2"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "read", "label": "next"},
            {"from": "read", "to": "out", "label": "next"},
            {"from": "out", "to": "end", "label": "next"},
        ],
    }


def decode(result: tuple[int, bytes]) -> tuple[int, dict]:
    status, body = result
    return status, json.loads(body.decode("utf-8"))


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_loopback_hosts_are_allowed(host: str) -> None:
    service.validate_bind_host(host)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.2", "flowchart.example"])
def test_non_loopback_hosts_are_rejected(host: str) -> None:
    with pytest.raises(ValueError, match="solo su loopback"):
        service.validate_bind_host(host)


def test_validate_api_reports_valid_artifact() -> None:
    status, payload = decode(
        service.handle_api_request(
            "POST", "/api/validate", json.dumps({"artifact": artifact()}).encode()
        )
    )
    assert status == 200
    assert payload == {"valid": True, "errors": []}


def test_validate_api_reports_structural_errors_without_executing() -> None:
    broken = artifact()
    broken["edges"] = []
    status, payload = decode(
        service.handle_api_request(
            "POST", "/api/validate", json.dumps({"artifact": broken}).encode()
        )
    )
    assert status == 200
    assert payload["valid"] is False
    assert payload["errors"]


def test_run_api_returns_trace_from_core() -> None:
    status, payload = decode(
        service.handle_api_request(
            "POST", "/api/run", json.dumps({"artifact": artifact(), "inputs": [7]}).encode()
        )
    )
    assert status == 200
    assert payload["schema_version"] == "thebitlab.flowtrace.v1"
    assert payload["status"] == "completed"
    assert payload["outputs"] == [14]
    assert payload["final_variables"] == {"n": 7}


def test_run_api_rejects_unsafe_artifact() -> None:
    broken = artifact()
    output = next(node for node in broken["nodes"] if node["id"] == "out")
    output["expression"] = "__import__('os')"
    status, payload = decode(
        service.handle_api_request(
            "POST", "/api/run", json.dumps({"artifact": broken, "inputs": [7]}).encode()
        )
    )
    assert status == 422
    assert payload["error"] == "invalid-artifact"


def test_api_rejects_oversized_request_before_json_parse() -> None:
    status, payload = decode(
        service.handle_api_request("POST", "/api/run", b"x" * (service.MAX_REQUEST_BYTES + 1))
    )
    assert status == 413
    assert payload == {"error": "request-too-large"}


def test_api_rejects_invalid_json_and_wrong_shapes() -> None:
    status, payload = decode(service.handle_api_request("POST", "/api/run", b"not-json"))
    assert status == 400
    assert payload["error"] == "invalid-json"

    status, payload = decode(
        service.handle_api_request(
            "POST", "/api/run", json.dumps({"artifact": artifact(), "inputs": "7"}).encode()
        )
    )
    assert status == 400
    assert payload["error"] == "inputs-must-be-list"


def test_api_is_post_only_and_has_small_surface() -> None:
    status, payload = decode(service.handle_api_request("GET", "/api/run", b""))
    assert status == 405
    assert payload["error"] == "method-not-allowed"

    status, payload = decode(service.handle_api_request("POST", "/api/unknown", b"{}"))
    assert status == 404
    assert payload["error"] == "not-found"


def test_limits_are_bounded_by_core_contract() -> None:
    status, payload = decode(
        service.handle_api_request(
            "POST",
            "/api/run",
            json.dumps(
                {
                    "artifact": artifact(),
                    "inputs": [7],
                    "limits": {"max_steps": service.flowchart_lab_core.HARD_MAX_STEPS + 1},
                }
            ).encode(),
        )
    )
    assert status == 400
    assert payload["error"] == "invalid-limits"


def test_static_routes_are_fixed_and_packaged() -> None:
    html = service.static_asset("/")
    css = service.static_asset("/app.css")
    js = service.static_asset("/app.js")

    assert html is not None and html[0] == 200 and html[1].startswith("text/html")
    assert css is not None and css[0] == 200 and css[1].startswith("text/css")
    assert js is not None and js[0] == 200 and "javascript" in js[1]
    assert b"TheBitLab Flowchart Lab" in html[2]
    assert b"/api/validate" in js[2]
    assert b"/api/run" in js[2]


def test_static_service_rejects_arbitrary_paths_and_traversal() -> None:
    assert service.static_asset("/../README.md") is None
    assert service.static_asset("/scripts/flowchart_lab_core.py") is None
    assert service.static_asset("/unknown") is None


def test_browser_shell_has_no_remote_runtime_dependency() -> None:
    html = service.static_asset("/")[2].decode("utf-8").lower()
    js = service.static_asset("/app.js")[2].decode("utf-8")
    css = service.static_asset("/app.css")[2].decode("utf-8").lower()

    assert '<script src="http' not in html
    assert '<link rel="stylesheet" href="http' not in html
    assert "@import url(http" not in css
    assert 'fetch("http' not in js.lower()
    assert "fetch('http" not in js.lower()
    assert "eval(" not in js
    assert "new function" not in js.lower()


def test_browser_shell_exposes_visual_authoring_trace_and_accessibility_surface() -> None:
    html = service.static_asset("/")[2].decode("utf-8")

    for marker in (
        "newBtn",
        "addNodeBtn",
        "deleteNodeBtn",
        "saveNodeBtn",
        "addEdgeBtn",
        "deleteEdgeBtn",
        "validateBtn",
        "runBtn",
        "stepBtn",
        "resetBtn",
        "variables",
        "outputs",
        "graph",
    ):
        assert marker in html
    assert 'aria-live="polite"' in html
    assert 'aria-label="Editor visuale del flow chart"' in html


def test_browser_js_keeps_layout_separate_and_supports_drag_selection() -> None:
    js = service.static_asset("/app.js")[2].decode("utf-8")

    assert "artifact.layout" in js
    assert "pointermove" in js
    assert "selectNode" in js
    assert "applyNodeProperties" in js
    assert "addEdge" in js
    assert "deleteEdge" in js
