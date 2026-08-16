from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Mapping, Protocol

from scripts.thebitlab_runtime_contracts import (
    normalize_runtime_extension,
    validate_runtime_extension,
)
from scripts.thebitlab_technical_services import ExecutionResult, RunnerTestResult


RUNTIME_PLUGIN_API_VERSION = "runtime_plugin.v1"
RUNTIME_ENTRY_POINT_GROUP = "thebitlab.runtimes"
RUNTIME_DESCRIPTOR_SCHEMA_VERSION = "runtime_descriptor.v1"
RUNTIME_REQUEST_SCHEMA_VERSION = "runtime_request.v1"
RUNTIME_PROBE_SCHEMA_VERSION = "runtime_probe.v1"
RUNTIME_LAUNCH_SCHEMA_VERSION = "runtime_launch.v1"
RUNTIME_EXECUTION_SCHEMA_VERSION = "runtime_execution.v1"
_RUNTIME_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

RuntimeLaunchStatus = Literal[
    "started",
    "already_running",
    "unsupported",
    "unavailable",
    "invalid_payload",
    "error",
]
_ALLOWED_LAUNCH_STATUSES = {
    "started",
    "already_running",
    "unsupported",
    "unavailable",
    "invalid_payload",
    "error",
}
_ALLOWED_EXECUTION_STATUSES = {
    "passed",
    "failed",
    "timeout",
    "runner_unavailable",
    "invalid_payload",
}


class RuntimePluginError(RuntimeError):
    """Base error raised by runtime discovery and protocol validation."""


class RuntimePluginNotFoundError(RuntimePluginError):
    """Raised when an Activity requests a runtime that is not installed."""


class RuntimePluginConflictError(RuntimePluginError):
    """Raised when multiple installed entry points claim the same runtime id."""


class RuntimePluginIncompatibleError(RuntimePluginError):
    """Raised when an installed plugin violates the public runtime protocol."""


@dataclass(frozen=True)
class RuntimeArtifactSpec:
    id: str
    path: str
    media_type: str
    required: bool = True

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "media_type": self.media_type,
            "required": self.required,
        }


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Validated metadata advertised by one installed runtime plugin."""

    runtime_id: str
    display_name: str
    plugin_version: str
    api_version: str = RUNTIME_PLUGIN_API_VERSION
    capabilities: frozenset[str] = frozenset()
    vendor: str = ""
    homepage: str = ""


@dataclass(frozen=True)
class RuntimeProbeResult:
    """Validated availability of the simulator/tool behind a plugin."""

    available: bool
    version: str = ""
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeRequest:
    """Trusted request created by TheBitLab and serialized for an external plugin."""

    runtime_id: str
    activity_id: str
    assignment_id: str
    student_id: str
    activity_path: Path
    workspace_path: Path
    config_path: Path | None
    submission_artifacts: tuple[RuntimeArtifactSpec, ...]
    timeout_seconds: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": RUNTIME_REQUEST_SCHEMA_VERSION,
            "runtime_id": self.runtime_id,
            "activity_id": self.activity_id,
            "assignment_id": self.assignment_id,
            "student_id": self.student_id,
            "paths": {
                "activity": str(self.activity_path),
                "workspace": str(self.workspace_path),
                "config": str(self.config_path) if self.config_path is not None else None,
            },
            "submission_artifacts": [item.to_payload() for item in self.submission_artifacts],
            "timeout_seconds": self.timeout_seconds,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeLaunchResult:
    """Validated result of asking an interactive runtime to open one assignment."""

    status: RuntimeLaunchStatus
    session_id: str = ""
    endpoint: str = ""
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimePlugin(Protocol):
    """Dependency-free duck-typed interface implemented by external packages.

    Plugins receive and return plain mappings. They do not need to import any
    Python module from TheBitLab. TheBitLab validates every returned payload
    before translating it to internal dataclasses such as ExecutionResult.
    """

    def describe(self) -> Mapping[str, Any]: ...

    def probe(self) -> Mapping[str, Any]: ...

    def launch(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def run(self, request: Mapping[str, Any]) -> Mapping[str, Any]: ...

    def close(self, session_id: str) -> None: ...


@dataclass(frozen=True)
class LoadedRuntimePlugin:
    descriptor: RuntimeDescriptor
    plugin: RuntimePlugin


EntryPointsProvider = Callable[[], Iterable[Any]]


def _default_entry_points() -> Iterable[Any]:
    """Return entry points in a way compatible with supported Python versions."""

    discovered = metadata.entry_points()
    select = getattr(discovered, "select", None)
    if callable(select):
        return select(group=RUNTIME_ENTRY_POINT_GROUP)
    return discovered.get(RUNTIME_ENTRY_POINT_GROUP, ())  # type: ignore[union-attr]


def _entry_point_name(entry_point: Any) -> str:
    return str(getattr(entry_point, "name", "") or "").strip()


def _text(value: Any, *, field_name: str, required: bool = False) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise RuntimePluginIncompatibleError(f"{field_name} deve essere una stringa")
    result = value.strip()
    if required and not result:
        raise RuntimePluginIncompatibleError(f"{field_name} non puo essere vuoto")
    return result


def _mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimePluginIncompatibleError(f"{field_name} deve essere un oggetto")
    return value


def _metadata_dict(value: Any, *, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    mapping = _mapping(value, field_name=field_name)
    return dict(mapping)


def _load_plugin_factory(entry_point: Any) -> RuntimePlugin:
    try:
        factory = entry_point.load()
    except Exception as error:  # plugin import failures need a stable platform error
        raise RuntimePluginIncompatibleError(
            f"Runtime plugin {_entry_point_name(entry_point) or '<senza nome>'} non caricabile: {error}"
        ) from error
    if not callable(factory):
        raise RuntimePluginIncompatibleError(
            f"Runtime plugin {_entry_point_name(entry_point)} deve esporre una factory senza argomenti"
        )
    try:
        plugin = factory()
    except Exception as error:
        raise RuntimePluginIncompatibleError(
            f"Factory runtime {_entry_point_name(entry_point)} non inizializzabile: {error}"
        ) from error
    return plugin


def descriptor_from_payload(runtime_id: str, payload: Any) -> RuntimeDescriptor:
    """Validate a dependency-free plugin descriptor payload."""

    raw = _mapping(payload, field_name=f"descriptor runtime {runtime_id}")
    schema_version = _text(
        raw.get("schema_version"),
        field_name="descriptor.schema_version",
        required=True,
    )
    if schema_version != RUNTIME_DESCRIPTOR_SCHEMA_VERSION:
        raise RuntimePluginIncompatibleError(
            f"Runtime {runtime_id} usa descriptor {schema_version}; richiesto {RUNTIME_DESCRIPTOR_SCHEMA_VERSION}"
        )
    if not _RUNTIME_TOKEN_RE.fullmatch(runtime_id):
        raise RuntimePluginIncompatibleError(
            f"Runtime entry point non usa un identificativo portabile: {runtime_id}"
        )
    declared_id = _text(raw.get("runtime_id"), field_name="descriptor.runtime_id", required=True)
    if declared_id != runtime_id:
        raise RuntimePluginIncompatibleError(
            f"Runtime entry point {runtime_id} dichiara descriptor {declared_id}"
        )
    api_version = _text(raw.get("api_version"), field_name="descriptor.api_version", required=True)
    if api_version != RUNTIME_PLUGIN_API_VERSION:
        raise RuntimePluginIncompatibleError(
            f"Runtime {runtime_id} usa API {api_version}; richiesta {RUNTIME_PLUGIN_API_VERSION}"
        )
    display_name = _text(raw.get("display_name"), field_name="descriptor.display_name", required=True)
    plugin_version = _text(raw.get("plugin_version"), field_name="descriptor.plugin_version", required=True)

    capabilities_raw = raw.get("capabilities", [])
    if not isinstance(capabilities_raw, (list, tuple, set, frozenset)):
        raise RuntimePluginIncompatibleError("descriptor.capabilities deve essere una lista")
    capabilities: set[str] = set()
    for index, capability in enumerate(capabilities_raw):
        value = _text(
            capability,
            field_name=f"descriptor.capabilities[{index}]",
            required=True,
        )
        if not _RUNTIME_TOKEN_RE.fullmatch(value):
            raise RuntimePluginIncompatibleError(
                f"descriptor.capabilities[{index}] non e un identificativo portabile: {value}"
            )
        capabilities.add(value)

    return RuntimeDescriptor(
        runtime_id=runtime_id,
        display_name=display_name,
        plugin_version=plugin_version,
        api_version=api_version,
        capabilities=frozenset(capabilities),
        vendor=_text(raw.get("vendor"), field_name="descriptor.vendor"),
        homepage=_text(raw.get("homepage"), field_name="descriptor.homepage"),
    )


def probe_result_from_payload(payload: Any) -> RuntimeProbeResult:
    raw = _mapping(payload, field_name="runtime probe result")
    schema_version = _text(raw.get("schema_version"), field_name="probe.schema_version", required=True)
    if schema_version != RUNTIME_PROBE_SCHEMA_VERSION:
        raise RuntimePluginIncompatibleError(
            f"Probe runtime con schema {schema_version}; richiesto {RUNTIME_PROBE_SCHEMA_VERSION}"
        )
    available = raw.get("available")
    if not isinstance(available, bool):
        raise RuntimePluginIncompatibleError("probe.available deve essere boolean")
    return RuntimeProbeResult(
        available=available,
        version=_text(raw.get("version"), field_name="probe.version"),
        detail=_text(raw.get("detail"), field_name="probe.detail"),
        metadata=_metadata_dict(raw.get("metadata"), field_name="probe.metadata"),
    )


def launch_result_from_payload(payload: Any) -> RuntimeLaunchResult:
    raw = _mapping(payload, field_name="runtime launch result")
    schema_version = _text(raw.get("schema_version"), field_name="launch.schema_version", required=True)
    if schema_version != RUNTIME_LAUNCH_SCHEMA_VERSION:
        raise RuntimePluginIncompatibleError(
            f"Launch runtime con schema {schema_version}; richiesto {RUNTIME_LAUNCH_SCHEMA_VERSION}"
        )
    status = _text(raw.get("status"), field_name="launch.status", required=True)
    if status not in _ALLOWED_LAUNCH_STATUSES:
        raise RuntimePluginIncompatibleError(f"launch.status non supportato: {status}")
    return RuntimeLaunchResult(
        status=status,  # type: ignore[arg-type]
        session_id=_text(raw.get("session_id"), field_name="launch.session_id"),
        endpoint=_text(raw.get("endpoint"), field_name="launch.endpoint"),
        detail=_text(raw.get("detail"), field_name="launch.detail"),
        metadata=_metadata_dict(raw.get("metadata"), field_name="launch.metadata"),
    )


def execution_result_from_payload(payload: Any) -> ExecutionResult:
    """Validate a plugin payload and translate it to the internal execution port."""

    raw = _mapping(payload, field_name="runtime execution result")
    schema_version = _text(
        raw.get("schema_version"),
        field_name="execution.schema_version",
        required=True,
    )
    if schema_version != RUNTIME_EXECUTION_SCHEMA_VERSION:
        raise RuntimePluginIncompatibleError(
            f"Execution runtime con schema {schema_version}; richiesto {RUNTIME_EXECUTION_SCHEMA_VERSION}"
        )
    status = _text(raw.get("status"), field_name="execution.status", required=True)
    if status not in _ALLOWED_EXECUTION_STATUSES:
        raise RuntimePluginIncompatibleError(f"execution.status non supportato: {status}")

    tests_raw = raw.get("tests", [])
    if not isinstance(tests_raw, list):
        raise RuntimePluginIncompatibleError("execution.tests deve essere una lista")
    tests: list[RunnerTestResult] = []
    for index, item in enumerate(tests_raw):
        test = _mapping(item, field_name=f"execution.tests[{index}]")
        name = _text(test.get("name"), field_name=f"execution.tests[{index}].name", required=True)
        passed = test.get("passed")
        if not isinstance(passed, bool):
            raise RuntimePluginIncompatibleError(
                f"execution.tests[{index}].passed deve essere boolean"
            )
        tests.append(
            RunnerTestResult(
                name=name,
                passed=passed,
                detail=_text(test.get("detail"), field_name=f"execution.tests[{index}].detail"),
            )
        )

    duration_ms = raw.get("duration_ms")
    if duration_ms is not None and (
        isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms < 0
    ):
        raise RuntimePluginIncompatibleError("execution.duration_ms deve essere un intero non negativo")

    return ExecutionResult(
        status=status,  # type: ignore[arg-type]
        tests=tests,
        stdout=_text(raw.get("stdout"), field_name="execution.stdout"),
        stderr=_text(raw.get("stderr"), field_name="execution.stderr"),
        duration_ms=duration_ms,
        detail=_text(raw.get("detail"), field_name="execution.detail"),
        metadata=_metadata_dict(raw.get("metadata"), field_name="execution.metadata"),
    )


class RuntimePluginRegistry:
    """Resolve administrator-installed runtime plugins through Python entry points."""

    def __init__(self, entry_points_provider: EntryPointsProvider = _default_entry_points) -> None:
        self._entry_points_provider = entry_points_provider
        self._cache: dict[str, LoadedRuntimePlugin] = {}

    def installed_ids(self) -> tuple[str, ...]:
        names = sorted(
            {
                _entry_point_name(entry_point)
                for entry_point in self._entry_points_provider()
                if _entry_point_name(entry_point)
            }
        )
        return tuple(names)

    def get(
        self,
        runtime_id: str,
        *,
        allowlist: set[str] | frozenset[str] | None = None,
    ) -> LoadedRuntimePlugin:
        runtime_id = str(runtime_id or "").strip()
        if not runtime_id:
            raise RuntimePluginNotFoundError("runtime_id mancante")
        if not _RUNTIME_TOKEN_RE.fullmatch(runtime_id):
            raise RuntimePluginNotFoundError(f"runtime_id non valido: {runtime_id}")
        if allowlist is not None and runtime_id not in allowlist:
            raise RuntimePluginNotFoundError(
                f"Runtime {runtime_id} non autorizzato da questa installazione TheBitLab"
            )
        if runtime_id in self._cache:
            return self._cache[runtime_id]

        matches = [
            entry_point
            for entry_point in self._entry_points_provider()
            if _entry_point_name(entry_point) == runtime_id
        ]
        if not matches:
            raise RuntimePluginNotFoundError(f"Runtime plugin non installato: {runtime_id}")
        if len(matches) != 1:
            raise RuntimePluginConflictError(
                f"Piu plugin dichiarano il runtime {runtime_id}: {len(matches)} entry point"
            )

        plugin = _load_plugin_factory(matches[0])
        describe = getattr(plugin, "describe", None)
        if not callable(describe):
            raise RuntimePluginIncompatibleError(
                f"Runtime {runtime_id} non implementa describe()"
            )
        try:
            descriptor_payload = describe()
        except Exception as error:
            raise RuntimePluginIncompatibleError(
                f"Runtime {runtime_id} ha fallito describe(): {error}"
            ) from error
        descriptor = descriptor_from_payload(runtime_id, descriptor_payload)
        loaded = LoadedRuntimePlugin(descriptor=descriptor, plugin=plugin)
        self._cache[runtime_id] = loaded
        return loaded


def required_capabilities(activity: dict[str, Any]) -> frozenset[str]:
    extension = normalize_runtime_extension(activity)
    if extension is None:
        return frozenset()
    return frozenset(str(value) for value in extension["required_capabilities"])


def missing_capabilities(
    activity: dict[str, Any],
    descriptor: RuntimeDescriptor,
) -> frozenset[str]:
    return required_capabilities(activity) - descriptor.capabilities


def assert_runtime_supports_activity(
    activity: dict[str, Any],
    descriptor: RuntimeDescriptor,
) -> None:
    """Reject an installed runtime that cannot satisfy the Activity requirements."""

    errors = validate_runtime_extension(activity, "activity")
    if errors:
        raise RuntimePluginIncompatibleError("; ".join(errors))
    extension = normalize_runtime_extension(activity)
    if extension is None:
        raise RuntimePluginIncompatibleError("Activity senza extensions.thebitlab.runtime")
    if extension["runtime_id"] != descriptor.runtime_id:
        raise RuntimePluginIncompatibleError(
            f"Activity richiede {extension['runtime_id']}, descriptor ricevuto {descriptor.runtime_id}"
        )
    missing = sorted(missing_capabilities(activity, descriptor))
    if missing:
        raise RuntimePluginIncompatibleError(
            f"Runtime {descriptor.runtime_id} non offre capability richieste: {', '.join(missing)}"
        )


def runtime_request_from_activity(
    activity: dict[str, Any],
    *,
    activity_id: str,
    assignment_id: str,
    student_id: str,
    activity_path: Path,
    workspace_path: Path,
    timeout_seconds: int = 30,
    metadata: dict[str, Any] | None = None,
) -> RuntimeRequest:
    """Build the generic request without parsing runtime-specific configuration."""

    errors = validate_runtime_extension(activity, "activity")
    if errors:
        raise RuntimePluginIncompatibleError("; ".join(errors))
    extension = normalize_runtime_extension(activity)
    if extension is None:
        raise RuntimePluginIncompatibleError("Activity senza extensions.thebitlab.runtime")
    activity_dir = activity_path.parent.resolve(strict=False)
    config = extension.get("config")
    config_path = None
    if isinstance(config, dict):
        config_path = (activity_dir / str(config["path"])).resolve(strict=False)
        try:
            config_path.relative_to(activity_dir)
        except ValueError as error:
            raise RuntimePluginIncompatibleError("Runtime config fuori dal package Activity") from error

    artifacts = tuple(
        RuntimeArtifactSpec(
            id=str(item["id"]),
            path=str(item["path"]),
            media_type=str(item["media_type"]),
            required=item.get("required") is not False,
        )
        for item in extension["submission"]["artifacts"]
    )
    return RuntimeRequest(
        runtime_id=str(extension["runtime_id"]),
        activity_id=activity_id,
        assignment_id=assignment_id,
        student_id=student_id,
        activity_path=activity_path.resolve(strict=False),
        workspace_path=workspace_path.resolve(strict=False),
        config_path=config_path,
        submission_artifacts=artifacts,
        timeout_seconds=timeout_seconds,
        metadata=dict(metadata or {}),
    )


def probe_runtime(loaded: LoadedRuntimePlugin) -> RuntimeProbeResult:
    probe = getattr(loaded.plugin, "probe", None)
    if not callable(probe):
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} non implementa probe()"
        )
    try:
        payload = probe()
    except Exception as error:
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} ha fallito probe(): {error}"
        ) from error
    return probe_result_from_payload(payload)


def launch_runtime(
    loaded: LoadedRuntimePlugin,
    request: RuntimeRequest,
) -> RuntimeLaunchResult:
    launch = getattr(loaded.plugin, "launch", None)
    if not callable(launch):
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} non implementa launch()"
        )
    try:
        payload = launch(request.to_payload())
    except Exception as error:
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} ha fallito launch(): {error}"
        ) from error
    return launch_result_from_payload(payload)


def run_runtime(
    loaded: LoadedRuntimePlugin,
    request: RuntimeRequest,
) -> ExecutionResult:
    run = getattr(loaded.plugin, "run", None)
    if not callable(run):
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} non implementa run()"
        )
    try:
        payload = run(request.to_payload())
    except Exception as error:
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} ha fallito run(): {error}"
        ) from error
    result = execution_result_from_payload(payload)
    return ExecutionResult(
        status=result.status,
        tests=result.tests,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_ms=result.duration_ms,
        detail=result.detail,
        metadata={
            **result.metadata,
            "runtime_id": loaded.descriptor.runtime_id,
            "runtime_plugin_version": loaded.descriptor.plugin_version,
        },
    )


def close_runtime(loaded: LoadedRuntimePlugin, session_id: str) -> None:
    close = getattr(loaded.plugin, "close", None)
    if not callable(close):
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} non implementa close()"
        )
    try:
        close(session_id)
    except Exception as error:
        raise RuntimePluginIncompatibleError(
            f"Runtime {loaded.descriptor.runtime_id} ha fallito close(): {error}"
        ) from error
