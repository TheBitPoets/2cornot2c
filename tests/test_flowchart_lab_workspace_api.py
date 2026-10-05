from __future__ import annotations

from contextlib import contextmanager
import http.client
import json
from pathlib import Path
import threading

import pytest

from scripts import flowchart_lab_server as api
from scripts import flowchart_lab_workspace as workspace


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
        "layout": {"start": {"x": 1, "y": 2}},
    }


@contextmanager
def live_server(*, workspace_root: Path | None = None):
    server = api.create_http_server(port=0, workspace_root=workspace_root)
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
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    connection.request(
        "POST",
        path,
        body=body,
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    status = response.status
    value = json.loads(response.read().decode("utf-8"))
    connection.close()
    return status, value


def test_workspace_api_is_explicitly_unavailable_without_launcher_root() -> None:
    with live_server() as port:
        status, body = post(port, "/api/workspace/status", {})
        save_status, save_body = post(
            port,
            "/api/workspace/save",
            {"artifact": artifact()},
        )

    assert status == save_status == 409
    assert body["error"] == "workspace_unavailable"
    assert save_body["error"] == "workspace_unavailable"


def test_workspace_round_trip_uses_only_fixed_algorithm_flow_file(tmp_path: Path) -> None:
    with live_server(workspace_root=tmp_path) as port:
        before_status, before = post(port, "/api/workspace/status", {})
        save_status, saved = post(
            port,
            "/api/workspace/save",
            {"artifact": artifact()},
        )
        after_status, after = post(port, "/api/workspace/status", {})
        load_status, loaded = post(port, "/api/workspace/load", {})

    assert before_status == save_status == after_status == load_status == 200
    assert before["exists"] is False
    assert saved["saved"] is True
    assert saved["artifact_name"] == workspace.ARTIFACT_NAME
    assert after["exists"] is True
    assert after["sha256"] == saved["sha256"]
    assert loaded["exists"] is True
    assert loaded["artifact_name"] == workspace.ARTIFACT_NAME
    assert loaded["artifact"] == artifact()
    assert loaded["sha256"] == saved["sha256"]
    assert [path.name for path in tmp_path.iterdir()] == [workspace.ARTIFACT_NAME]


def test_workspace_api_never_accepts_a_browser_supplied_path(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.flow.json"

    with live_server(workspace_root=tmp_path) as port:
        status, body = post(
            port,
            "/api/workspace/save",
            {
                "artifact": artifact(),
                "path": str(outside),
            },
        )
        load_status, load_body = post(
            port,
            "/api/workspace/load",
            {"path": "../../outside.flow.json"},
        )

    assert status == load_status == 400
    assert body["error"] == "invalid_request"
    assert load_body["error"] == "invalid_request"
    assert not outside.exists()
    assert not (tmp_path / workspace.ARTIFACT_NAME).exists()


def test_invalid_flowchart_is_not_written(tmp_path: Path) -> None:
    broken = artifact()
    broken["edges"] = []

    with live_server(workspace_root=tmp_path) as port:
        status, body = post(
            port,
            "/api/workspace/save",
            {"artifact": broken},
        )

    assert status == 422
    assert body["error"] == "flowchart_validation_error"
    assert not (tmp_path / workspace.ARTIFACT_NAME).exists()


def test_corrupt_workspace_file_fails_closed_without_file_contents_in_response(tmp_path: Path) -> None:
    marker = "TOP-SECRET-MARKER"
    (tmp_path / workspace.ARTIFACT_NAME).write_text(marker, encoding="utf-8")

    with live_server(workspace_root=tmp_path) as port:
        status, body = post(port, "/api/workspace/load", {})

    assert status == 409
    assert body["error"] == "workspace_error"
    assert marker not in json.dumps(body)


def test_workspace_loader_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    raw = (
        '{"schema_version":"thebitlab.flowchart.v1",'
        '"schema_version":"thebitlab.flowchart.v1",'
        '"entry":"start","nodes":[],"edges":[]}'
    )
    (tmp_path / workspace.ARTIFACT_NAME).write_text(raw, encoding="utf-8")
    store = workspace.FlowchartWorkspaceStore(tmp_path)

    with pytest.raises(workspace.FlowchartWorkspaceError, match="duplicata"):
        store.load()


def test_workspace_root_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "linked"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted")

    with pytest.raises(workspace.FlowchartWorkspaceError, match="symlink"):
        workspace.FlowchartWorkspaceStore(link)
