from __future__ import annotations

from pathlib import Path

import pytest

from scripts import thebitlab_runtime_plugins as plugins
from scripts.thebitlab_technical_services import ExecutionResult


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
        capabilities: frozenset[str] = frozenset({"headless-run", "deterministic-grade"}),
    ) -> None:
        self._descriptor = plugins.RuntimeDescriptor(
            runtime_id=runtime_id,
            display_name="Example Runtime",
            plugin_version="1.2.3",
            api_version=api_version,
            capabilities=capabilities,
        )

    def describe(self) -> plugins.RuntimeDescriptor:
        return self._descriptor

    def probe(self) -> plugins.RuntimeProbeResult:
        return plugins.RuntimeProbeResult(available=True, version="1.2.3")

    def launch(self, request: plugins.RuntimeRequest) -> plugins.RuntimeLaunchResult:
        return plugins.RuntimeLaunchResult(status="unsupported")

    def run(self, request: plugins.RuntimeRequest) -> ExecutionResult:
        return ExecutionResult(status="passed")

    def close(self, session_id: str) -> None:
        return None


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


def test_registry_discovers_runtime_by_entry_point_without_hardcoded_ids() -> None:
    fake = FakeEntryPoint("ns3", lambda: FakePlugin("ns3"))
    runtime_registry = registry(fake)

    loaded = runtime_registry.get("ns3")

    assert runtime_registry.installed_ids() == ("ns3",)
    assert loaded.descriptor.runtime_id == "ns3"
    assert loaded.plugin.probe().available is True


def test_registry_enforces_installation_allowlist() -> None:
    fake = FakeEntryPoint("matlab", lambda: FakePlugin("matlab"))
    runtime_registry = registry(fake)

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


def test_capability_matching_is_activity_driven() -> None:
    descriptor = FakePlugin(
        "packet-tracer",
        capabilities=frozenset({"interactive-launch", "artifact-collect"}),
    ).describe()
    requested = activity(
        "packet-tracer",
        ["interactive-launch", "artifact-collect"],
    )

    plugins.assert_runtime_supports_activity(requested, descriptor)
    assert plugins.missing_capabilities(requested, descriptor) == frozenset()


def test_capability_matching_reports_missing_headless_grading() -> None:
    descriptor = FakePlugin(
        "packet-tracer",
        capabilities=frozenset({"interactive-launch", "artifact-collect"}),
    ).describe()
    requested = activity(
        "packet-tracer",
        ["interactive-launch", "deterministic-grade"],
    )

    with pytest.raises(plugins.RuntimePluginIncompatibleError, match="deterministic-grade"):
        plugins.assert_runtime_supports_activity(requested, descriptor)


def test_runtime_request_passes_paths_and_artifacts_without_parsing_runtime_config(tmp_path: Path) -> None:
    activity_dir = tmp_path / "activity"
    workspace = tmp_path / "workspace"
    activity_dir.mkdir()
    workspace.mkdir()
    activity_path = activity_dir / "activity.json"
    activity_path.write_text("{}", encoding="utf-8")

    request = plugins.runtime_request_from_activity(
        activity(),
        activity_id="a1",
        assignment_id="assign-1",
        student_id="student-1",
        activity_path=activity_path,
        workspace_path=workspace,
    )

    assert request.activity_id == "a1"
    assert request.assignment_id == "assign-1"
    assert request.config_path == activity_dir / "runtime/config.json"
    assert request.submission_artifacts == (
        plugins.RuntimeArtifactSpec(
            id="primary",
            path="answer.bin",
            media_type="application/octet-stream",
            required=True,
        ),
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
        descriptor = FakePlugin(runtime_id, capabilities=frozenset(required)).describe()
        plugins.assert_runtime_supports_activity(activity(runtime_id, required), descriptor)
