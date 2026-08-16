from __future__ import annotations

import json
from pathlib import Path

from scripts import student_runtime, thebitlab_runtime_plugins


class FakeEntryPoint:
    def __init__(self, name: str, factory) -> None:
        self.name = name
        self._factory = factory

    def load(self):
        return self._factory


class FakeRuntime:
    def describe(self):
        return {
            "schema_version": "runtime_descriptor.v1",
            "runtime_id": "example-runtime",
            "display_name": "Example Runtime",
            "plugin_version": "1.0.0",
            "api_version": "runtime_plugin.v1",
            "capabilities": ["interactive-launch", "headless-run", "deterministic-grade"],
        }

    def probe(self):
        return {
            "schema_version": "runtime_probe.v1",
            "available": True,
            "version": "1.0.0",
            "detail": "ready",
            "metadata": {},
        }

    def run(self, request):
        assert request["schema_version"] == "runtime_request.v1"
        assert request["runtime_id"] == "example-runtime"
        return {
            "schema_version": "runtime_execution.v1",
            "status": "failed",
            "tests": [
                {"name": "first", "passed": True, "detail": "ok"},
                {"name": "second", "passed": False, "detail": "fix me"},
            ],
            "detail": "not complete",
            "metadata": {"score": 5.0},
        }

    def launch(self, request):
        return {
            "schema_version": "runtime_launch.v1",
            "status": "started",
            "session_id": "session-1",
            "endpoint": "http://127.0.0.1:9999/",
            "detail": "opened",
            "metadata": {},
        }

    def close(self, session_id):
        return None


def fixture(tmp_path: Path) -> tuple[dict, thebitlab_runtime_plugins.RuntimePluginRegistry]:
    activity_dir = tmp_path / "activity"
    workspace = tmp_path / "workspace"
    runtime_dir = activity_dir / "runtime"
    runtime_dir.mkdir(parents=True)
    workspace.mkdir()
    (runtime_dir / "config.json").write_text("{}", encoding="utf-8")
    (workspace / "answer.bin").write_bytes(b"answer")

    activity = {
        "schema_version": "1.0",
        "id": "runtime-activity",
        "extensions": {
            "thebitlab.runtime": {
                "schema_version": "runtime_activity.v1",
                "runtime_id": "example-runtime",
                "config": {"path": "runtime/config.json", "media_type": "application/json"},
                "required_capabilities": ["headless-run", "deterministic-grade"],
                "submission": {
                    "artifacts": [
                        {"id": "answer", "path": "answer.bin", "media_type": "application/octet-stream", "required": True}
                    ]
                },
            }
        },
    }
    activity_path = activity_dir / "activity.json"
    activity_path.write_text(json.dumps(activity), encoding="utf-8")
    assignment = {
        "assignment_id": "assignment-1",
        "activity_id": "runtime-activity",
        "student_id": "student-1",
        "activity": {"path": "activity/activity.json"},
        "workspace": {"path": "workspace"},
    }
    registry = thebitlab_runtime_plugins.RuntimePluginRegistry(
        lambda: (FakeEntryPoint("example-runtime", FakeRuntime),)
    )
    return assignment, registry


def test_runtime_assignment_generates_normal_student_report(tmp_path: Path) -> None:
    assignment, registry = fixture(tmp_path)
    report = student_runtime.run_runtime_assignment(
        assignment,
        root=tmp_path,
        timeout_seconds=10,
        registry=registry,
    )
    assert report["backend"] == "runtime"
    assert report["runtime_id"] == "example-runtime"
    assert report["language"] == "runtime:example-runtime"
    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["summary"] == {"passed": 1, "total": 2}
    assert report["score"] == 5.0
    assert report["tests"][1]["message"] == "fix me"


def test_runtime_launch_is_generic(tmp_path: Path) -> None:
    assignment, registry = fixture(tmp_path)
    result = student_runtime.launch_runtime_assignment(
        assignment,
        root=tmp_path,
        registry=registry,
    )
    assert result.status == "started"
    assert result.session_id == "session-1"
    assert result.endpoint == "http://127.0.0.1:9999/"


def test_missing_plugin_becomes_stable_student_report(tmp_path: Path) -> None:
    assignment, _ = fixture(tmp_path)
    empty_registry = thebitlab_runtime_plugins.RuntimePluginRegistry(lambda: ())
    report = student_runtime.run_runtime_assignment(
        assignment,
        root=tmp_path,
        timeout_seconds=10,
        registry=empty_registry,
    )
    assert report["status"] == "runtime-unavailable"
    assert report["passed"] is False
    assert "non installato" in report["error"]


def test_activity_runtime_detection_is_generic() -> None:
    activity = {
        "extensions": {
            "thebitlab.runtime": {
                "schema_version": "runtime_activity.v1",
                "runtime_id": "ns3",
                "submission": {"artifacts": [{"id": "result", "path": "result.json"}]},
            }
        }
    }
    assert student_runtime.activity_uses_runtime(activity) is True
    assert student_runtime.activity_uses_runtime({}) is False
