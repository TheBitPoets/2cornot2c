from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import flowchart_lab_service as service
from scripts import flowchart_lab_workspace as workspace


def artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "out", "type": "output", "expression": "42"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "out", "label": "next"},
            {"from": "out", "to": "end", "label": "next"},
        ],
    }


def decode(result: tuple[int, bytes]) -> tuple[int, dict]:
    status, body = result
    return status, json.loads(body.decode("utf-8"))


@pytest.mark.parametrize(
    "host_header",
    ["127.0.0.1", "127.0.0.1:8776", "localhost", "localhost:8776", "[::1]", "[::1]:8776"],
)
def test_loopback_host_headers_are_accepted(host_header: str) -> None:
    assert service.valid_host_header(host_header) is True


@pytest.mark.parametrize(
    "host_header",
    [
        "",
        "evil.example",
        "evil.example:8776",
        "127.0.0.1.evil.example",
        "evil@127.0.0.1",
        "127.0.0.1/path",
        "0.0.0.0:8776",
        "192.168.1.2:8776",
    ],
)
def test_non_loopback_or_suspicious_host_headers_are_rejected(host_header: str) -> None:
    assert service.valid_host_header(host_header) is False


def test_workspace_api_is_unavailable_when_launcher_did_not_supply_root() -> None:
    status, payload = decode(service.load_workspace_artifact(None))
    assert status == 503
    assert payload == {"error": "workspace-unavailable"}

    status, payload = decode(
        service.handle_api_request(
            "POST", "/api/artifact", json.dumps({"artifact": artifact()}).encode(), store=None
        )
    )
    assert status == 503
    assert payload == {"error": "workspace-unavailable"}


def test_workspace_api_saves_and_loads_fixed_artifact(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)

    status, payload = decode(
        service.handle_api_request(
            "POST",
            "/api/artifact",
            json.dumps({"artifact": artifact()}).encode(),
            store=store,
        )
    )
    assert status == 200
    assert payload == {"saved": True, "artifact_name": "algorithm.flow.json"}
    assert (tmp_path / "algorithm.flow.json").is_file()

    status, payload = decode(service.load_workspace_artifact(store))
    assert status == 200
    assert payload["artifact"] == artifact()


def test_workspace_load_returns_not_found_before_first_save(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    status, payload = decode(service.load_workspace_artifact(store))

    assert status == 404
    assert payload == {"error": "artifact-not-found"}


def test_workspace_save_rejects_invalid_flow_without_writing(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    broken = artifact()
    broken["edges"] = []

    status, payload = decode(
        service.handle_api_request(
            "POST",
            "/api/artifact",
            json.dumps({"artifact": broken}).encode(),
            store=store,
        )
    )

    assert status == 422
    assert payload["error"] == "invalid-artifact"
    assert not (tmp_path / "algorithm.flow.json").exists()


def test_browser_never_supplies_a_workspace_path() -> None:
    js = service.static_asset("/app.js")[2].decode("utf-8").lower()

    assert "workspace=" not in js
    assert "filesystem" not in js
    assert "file://" not in js
