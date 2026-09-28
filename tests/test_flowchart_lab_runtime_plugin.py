from __future__ import annotations

import http.client
import json
from pathlib import Path

from scripts import (
    flowchart_lab_runtime_plugin,
    student_runtime,
    thebitlab_runtime_cli,
    thebitlab_runtime_plugins,
)


def fixture(tmp_path: Path) -> dict:
    activity_dir = tmp_path / "activity"
    workspace = tmp_path / "workspace"
    activity_dir.mkdir()
    workspace.mkdir()

    activity = {
        "schema_version": "1.0",
        "id": "py2-flowchart-canary",
        "extensions": {
            "thebitlab.runtime": {
                "schema_version": "runtime_activity.v1",
                "runtime_id": "flowchart-lab",
                "required_capabilities": ["interactive-launch", "artifact-collect"],
                "submission": {
                    "artifacts": [
                        {
                            "id": "flowchart",
                            "path": "algorithm.flow.json",
                            "media_type": "application/json",
                            "required": True,
                        }
                    ]
                },
            }
        },
    }
    (activity_dir / "activity.json").write_text(json.dumps(activity), encoding="utf-8")
    return {
        "assignment_id": "assignment-flow-1",
        "activity_id": "py2-flowchart-canary",
        "student_id": "student-1",
        "activity": {"path": "activity/activity.json"},
        "workspace": {"path": "workspace"},
    }


def post(endpoint: str, path: str, payload: dict) -> tuple[int, dict]:
    host_port = endpoint.removeprefix("http://").rstrip("/")
    host, raw_port = host_port.split(":", 1)
    connection = http.client.HTTPConnection(host, int(raw_port), timeout=3)
    body = json.dumps(payload).encode("utf-8")
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


def test_builtin_registry_exposes_flowchart_lab_without_hardcoding_generic_registry() -> None:
    assert "flowchart-lab" in student_runtime.DEFAULT_REGISTRY.installed_ids()

    loaded = student_runtime.DEFAULT_REGISTRY.get("flowchart-lab")
    assert loaded.descriptor.runtime_id == "flowchart-lab"
    assert loaded.descriptor.capabilities == frozenset({"interactive-launch", "artifact-collect"})
    assert thebitlab_runtime_plugins.RUNTIME_SANDBOX_CAPABILITY not in loaded.descriptor.capabilities

    probe = thebitlab_runtime_plugins.probe_runtime(loaded)
    assert probe.available is True
    assert probe.metadata["offline"] is True
    assert probe.metadata["loopback_only"] is True


def test_runtime_cli_inventory_contains_available_builtin_flowchart_lab() -> None:
    record = thebitlab_runtime_cli.runtime_record("flowchart-lab")

    assert record["installed"] is True
    assert record["available"] is True
    assert record["status"] == "available"
    assert record["capabilities"] == ["artifact-collect", "interactive-launch"]


def test_student_runtime_launches_loopback_flowchart_service_on_assignment_workspace(tmp_path: Path) -> None:
    assignment = fixture(tmp_path)
    loaded = student_runtime.DEFAULT_REGISTRY.get("flowchart-lab")
    launch = student_runtime.launch_runtime_assignment(assignment, root=tmp_path)

    try:
        assert launch.status == "started"
        assert launch.session_id
        assert launch.endpoint.startswith("http://127.0.0.1:")
        assert launch.metadata["artifact_name"] == "algorithm.flow.json"

        status, saved = post(
            launch.endpoint,
            "/api/workspace/save",
            {
                "artifact": {
                    "schema_version": "thebitlab.flowchart.v1",
                    "entry": "start",
                    "nodes": [
                        {"id": "start", "type": "start"},
                        {"id": "end", "type": "end"},
                    ],
                    "edges": [
                        {"from": "start", "to": "end", "label": "next"}
                    ],
                }
            },
        )
        assert status == 200
        assert saved["saved"] is True
        assert (tmp_path / "workspace" / "algorithm.flow.json").is_file()
    finally:
        thebitlab_runtime_plugins.close_runtime(loaded, launch.session_id)


def test_second_launch_reuses_same_workspace_session_until_closed(tmp_path: Path) -> None:
    assignment = fixture(tmp_path)
    loaded = student_runtime.DEFAULT_REGISTRY.get("flowchart-lab")
    first = student_runtime.launch_runtime_assignment(assignment, root=tmp_path)
    second = student_runtime.launch_runtime_assignment(assignment, root=tmp_path)

    try:
        assert first.status == "started"
        assert second.status == "already_running"
        assert second.session_id == first.session_id
        assert second.endpoint == first.endpoint
    finally:
        thebitlab_runtime_plugins.close_runtime(loaded, first.session_id)


def test_flowchart_runtime_run_does_not_claim_automatic_grading(tmp_path: Path) -> None:
    assignment = fixture(tmp_path)

    report = student_runtime.run_runtime_assignment(
        assignment,
        root=tmp_path,
        timeout_seconds=10,
    )

    assert report["runtime_id"] == "flowchart-lab"
    assert report["passed"] is False
    assert report["status"] == "runner_unavailable"
    assert report["summary"] == {"passed": 0, "total": 0}
    assert "runtime interattivo" in report["detail"]
    assert report["runtime"]["metadata"]["authoritative_grading"] is False


def test_plugin_rejects_untrusted_workspace_shape_without_starting_service(tmp_path: Path) -> None:
    plugin = flowchart_lab_runtime_plugin.FlowchartLabRuntimePlugin()
    result = plugin.launch(
        {
            "schema_version": "runtime_request.v1",
            "runtime_id": "flowchart-lab",
            "paths": {"workspace": str(tmp_path / "missing")},
        }
    )

    assert result["status"] == "invalid_payload"
    assert result["session_id"] == ""
    assert result["endpoint"] == ""
