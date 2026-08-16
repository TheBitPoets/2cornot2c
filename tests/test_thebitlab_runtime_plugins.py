from __future__ import annotations

from pathlib import Path

import pytest

from scripts import thebitlab_runtime_plugins as plugins


class FakeEntryPoint:
    def __init__(self, name: str, factory) -> None:
        self.name = name
        self._factory = factory

    def load(self):
        return self._factory


class FakePlugin:
    def __init__(
        self,
        runtime_id: str = "example-runtime",
        *,
        api_version: str = plugins.RUNTIME_PLUGIN_API_VERSION,
        capabilities: tuple[str, ...] = ("headless-run", "deterministic-grade"),
    ) -> None:
        self.runtime_id = runtime_id
        self.api_version = api_version
        self.capabilities = capabilities
        self.closed: list[str] = []
        self.last_request = None

    def describe(self):
        return {
            "schema_version": plugins.RUNTIME_DESCRIPTOR_SCHEMA_VERSION,
            "runtime_id": self.runtime_id,
            "display_name": "Example Runtime",
            "plugin_version": "1.2.3",
            "api_version": self.api_version,
            "capabilities": list(self.capabilities),
        }

    def probe(self):
        return {
            "schema_version": plugins.RUNTIME_PROBE_SCHEMA_VERSION,
            "available": True,
            "version": "1.2.3",
            "detail": "ready",
        }

    def launch(self, request):
        self.last_request = request
        return {
            "schema_version": plugins.RUNTIME_LAUNCH_SCHEMA_VERSION,
            "status": "unsupported",
            "detail": "no interactive UI",
        }

    def run(self, request):
        self.last_request = request
        return {
            "schema_version": plugins.RUNTIME_EXECUTION_SCHEMA_VERSION,
            "status": "passed",
            "tests": [
                {"name": "runtime smoke", "passed": True, "detail": "ok"}
            ],
            "duration_ms": 5,
            "detail": "completed",
        }

    def close(self, session_id: str) -> None:
        self.closed.append(session_id)


def activity(
    runtime_id: str = "example-runtime",
    capabilities: list[str] | None = None,
) -> dict:
    return {
        "extensions": {
            "thebitlab.runtime": {
                "schema_version": "runtime_activity.v1",
                "runtime_id": runtime_id,
                "config": {
                    "path": "runtime/config.json",
                    "media_type": "application/json",
                },
                "required_capabilities": capabilities or ["headless-run"],
                "submission": {
                    "artifacts": [
                        {
                            "id": "primary",
                            "path": "answer.bin",
                            "media_type": "application/octet-stream",
                            "required": True,
                        }
                    ]
                },
            }
        }
    }


def registry(*entry_points: FakeEntryPoint) -> plugins.RuntimePluginRegistry:
    return plugins.RuntimePluginRegistry(lambda: tuple(entry_points))


def request(tmp_path: Path, runtime_id: str = "example-runtime") -> plugins.RuntimeRequest:
    activity_dir = tmp_path / "activity"
    workspace = tmp_path / "workspace"
    activity_dir.mkdir()
    workspace.mkdir()
    activity_path = activity_dir / "activity.json"
    activity_path.write_text("{}", encoding="utf-8")
    return plugins.runtime_request_from_activity(
        activity(runtime_id),
        activity_id="a1",
        assignment_id="assign-1",
        student_id="student-1",
        activity_path=activity_path,
        workspace_path=workspace,
    )


def test_registry_discovers_runtime_by_entry_point_without_hardcoded_ids() -> None:
    fake_plugin = FakePlugin("ns3")
    runtime_registry = registry(FakeEntryPoint("ns3", lambda: fake_plugin))

    loaded = runtime_registry.get("ns3")

    assert runtime_registry.installed_ids() == ("ns3",)
    assert loaded.descriptor.runtime_id == "ns3"
    assert plugins.probe_runtime(loaded).available is True


def test_registry_enforces_installation_allowlist() -> None:
    runtime_registry = registry(FakeEntryPoint("matlab", lambda: FakePlugin("matlab")))

    with pytest.raises(plugins.RuntimePluginNotFoundError, match="non autorizzato"):
        runtime_registry.get("matlab", allowlist={"efesto", "ns3"})


def test_registry_rejects_duplicate_runtime_entry_points() -> None:
    runtime_registry = registry(
        FakeEntryPoint("efesto", lambda: FakePlugin("efesto")),
        FakeEntryPoint("efesto", lambda: FakePlugin("efesto")),
    )

    with pytest.raises(plugins.RuntimePluginConflictError, match="Piu plugin"):
        runtime_registry.get("efesto")


def test_registry_rejects_plugin_api_version_mismatch() -> None:
    runtime_registry = registry(
        FakeEntryPoint(
            "simulink",
            lambda: FakePlugin("simulink", api_version="runtime_plugin.v99"),
        )
    )

    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="runtime_plugin.v99"):
        runtime_registry.get("simulink")


def test_registry_rejects_descriptor_id_different_from_entry_point() -> None:
    runtime_registry = registry(
        FakeEntryPoint("packet-tracer", lambda: FakePlugin("different-runtime"))
    )

    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="descriptor"):
        runtime_registry.get("packet-tracer")


def test_registry_rejects_invalid_plugin_capability() -> None:
    runtime_registry = registry(
        FakeEntryPoint(
            "bad-runtime",
            lambda: FakePlugin("bad-runtime", capabilities=("headless-run", "non valida")),
        )
    )

    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="capabilities"):
        runtime_registry.get("bad-runtime")


def test_capability_matching_is_activity_driven() -> None:
    descriptor = plugins.descriptor_from_payload(
        "packet-tracer",
        FakePlugin(
            "packet-tracer",
            capabilities=("interactive-launch", "artifact-collect"),
        ).describe(),
    )
    requested = activity(
        "packet-tracer",
        ["interactive-launch", "artifact-collect"],
    )

    plugins.assert_runtime_supports_activity(requested, descriptor)
    assert plugins.missing_capabilities(requested, descriptor) == frozenset()


def test_capability_matching_reports_missing_headless_grading() -> None:
    descriptor = plugins.descriptor_from_payload(
        "packet-tracer",
        FakePlugin(
            "packet-tracer",
            capabilities=("interactive-launch", "artifact-collect"),
        ).describe(),
    )
    requested = activity(
        "packet-tracer",
        ["interactive-launch", "deterministic-grade"],
    )

    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="deterministic-grade"):
        plugins.assert_runtime_supports_activity(requested, descriptor)


def test_runtime_request_serializes_paths_and_artifacts_without_parsing_config(tmp_path: Path) -> None:
    runtime_request = request(tmp_path)
    payload = runtime_request.to_payload()

    assert runtime_request.runtime_id == "example-runtime"
    assert runtime_request.config_path == tmp_path / "activity/runtime/config.json"
    assert payload["schema_version"] == plugins.RUNTIME_REQUEST_SCHEMA_VERSION
    assert payload["paths"]["workspace"] == str(tmp_path / "workspace")
    assert payload["submission_artifacts"] == [
        {
            "id": "primary",
            "path": "answer.bin",
            "media_type": "application/octet-stream",
            "required": True,
        }
    ]


def test_runtime_request_rejects_invalid_activity_contract(tmp_path: Path) -> None:
    invalid = activity()
    invalid["extensions"]["thebitlab.runtime"]["submission"]["artifacts"][0]["path"] = "../escape.bin"
    activity_dir = tmp_path / "activity"
    activity_dir.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    activity_path = activity_dir / "activity.json"
    activity_path.write_text("{}", encoding="utf-8")

    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="path relativo sicuro"):
        plugins.runtime_request_from_activity(
            invalid,
            activity_id="a1",
            assignment_id="assign-1",
            student_id="student-1",
            activity_path=activity_path,
            workspace_path=workspace,
        )


def test_runtime_lifecycle_uses_plain_payloads_and_normalizes_execution(tmp_path: Path) -> None:
    fake_plugin = FakePlugin("ns3", capabilities=("headless-run",))
    loaded = registry(FakeEntryPoint("ns3", lambda: fake_plugin)).get("ns3")
    runtime_request = request(tmp_path, "ns3")

    probe = plugins.probe_runtime(loaded)
    launch = plugins.launch_runtime(loaded, runtime_request)
    execution = plugins.run_runtime(loaded, runtime_request)
    plugins.close_runtime(loaded, "session-1")

    assert probe.available is True
    assert launch.status == "unsupported"
    assert execution.status == "passed"
    assert execution.tests[0].name == "runtime smoke"
    assert execution.metadata["runtime_id"] == "ns3"
    assert fake_plugin.last_request["schema_version"] == plugins.RUNTIME_REQUEST_SCHEMA_VERSION
    assert fake_plugin.closed == ["session-1"]


def test_execution_payload_validation_rejects_malformed_test() -> None:
    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="passed deve essere boolean"):
        plugins.execution_result_from_payload(
            {
                "schema_version": plugins.RUNTIME_EXECUTION_SCHEMA_VERSION,
                "status": "failed",
                "tests": [{"name": "broken", "passed": "yes"}],
            }
        )


def test_examples_can_represent_different_runtime_operating_models() -> None:
    cases = {
        "efesto": ["interactive-launch", "headless-run", "deterministic-grade"],
        "ns3": ["headless-run", "deterministic-grade"],
        "packet-tracer": ["interactive-launch", "artifact-collect"],
        "matlab": ["headless-run", "artifact-collect"],
        "simulink": ["interactive-launch", "headless-run", "artifact-collect"],
    }

    for runtime_id, required in cases.items():
        descriptor = plugins.descriptor_from_payload(
            runtime_id,
            FakePlugin(runtime_id, capabilities=tuple(required)).describe(),
        )
        plugins.assert_runtime_supports_activity(activity(runtime_id, required), descriptor)
