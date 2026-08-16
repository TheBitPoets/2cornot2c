from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Protocol

from scripts.thebitlab_runtime_contracts import (
    normalize_runtime_extension,
    validate_runtime_extension,
)
from scripts.thebitlab_technical_services import ExecutionResult


RUNTIME_PLUGIN_API_VERSION = "runtime_plugin.v1"
RUNTIME_ENTRY_POINT_GROUP = "thebitlab.runtimes"
_RUNTIME_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

RuntimeLaunchStatus = Literal[
    "started",
    "already_running",
    "unsupported",
    "unavailable",
    "invalid_payload",
    "error",
]


class RuntimePluginError(RuntimeError):
    """Base error raised by runtime discovery and compatibility checks."""


class RuntimePluginNotFoundError(RuntimePluginError):
    """Raised when an Activity requests a runtime that is not installed."""


class RuntimePluginConflictError(RuntimePluginError):
    """Raised when multiple installed entry points claim the same runtime id."""


class RuntimePluginIncompatibleError(RuntimePluginError):
    """Raised when the installed plugin does not satisfy the platform contract."""


@dataclass(frozen=True)
class RuntimeArtifactSpec:
    id: str
    path: str
    media_type: str
    required: bool = True


@dataclass(frozen=True)
class RuntimeDescriptor:
    """Stable metadata advertised by one installed runtime plugin."""

    runtime_id: str
    display_name: str
    plugin_version: str
    api_version: str = RUNTIME_PLUGIN_API_VERSION
    capabilities: frozenset[str] = frozenset()
    vendor: str = ""
    homepage: str = ""


@dataclass(frozen=True)
class RuntimeProbeResult:
    """Availability of the simulator/tool behind an installed plugin."""

    available: bool
    version: str = ""
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeRequest:
    """Trusted paths and metadata passed by TheBitLab to a runtime plugin."""

    activity_id: str
    assignment_id: str
    student_id: str
    activity_path: Path
    workspace_path: Path
    config_path: Path | None
    submission_artifacts: tuple[RuntimeArtifactSpec, ...]
    timeout_seconds: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeLaunchResult:
    """Result of asking an interactive runtime to open one assignment."""

    status: RuntimeLaunchStatus
    session_id: str = ""
    endpoint: str = ""
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class RuntimePlugin(Protocol):
    """Duck-typed plugin API implemented by external runtime packages.

    Implementations may wrap native executables, local web applications,
    containers or remote services. Unsupported operations return an explicit
    status/result; Activities never supply executable commands or endpoints.
    """

    def describe(self) -> RuntimeDescriptor: ...

    def probe(self) -> RuntimeProbeResult: ...

    def launch(self, request: RuntimeRequest) -> RuntimeLaunchResult: ...

    def run(self, request: RuntimeRequest) -> ExecutionResult: ...

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


def _validate_descriptor(runtime_id: str, descriptor: Any) -> RuntimeDescriptor:
    if not isinstance(descriptor, RuntimeDescriptor):
        raise RuntimePluginIncompatibleError(
            f"Runtime {runtime_id} ha restituito un descriptor non valido"
        )
    if not _RUNTIME_TOKEN_RE.fullmatch(runtime_id):
        raise RuntimePluginIncompatibleError(
            f"Runtime entry point non usa un identificativo portabile: {runtime_id}"
        )
    if descriptor.runtime_id != runtime_id:
        raise RuntimePluginIncompatibleError(
            f"Runtime entry point {runtime_id} dichiara descriptor {descriptor.runtime_id or '<mancante>'}"
        )
    if descriptor.api_version != RUNTIME_PLUGIN_API_VERSION:
        raise RuntimePluginIncompatibleError(
            f"Runtime {runtime_id} usa API {descriptor.api_version}; richiesta {RUNTIME_PLUGIN_API_VERSION}"
        )
    if not descriptor.display_name.strip() or not descriptor.plugin_version.strip():
        raise RuntimePluginIncompatibleError(
            f"Runtime {runtime_id} deve dichiarare display_name e plugin_version"
        )
    invalid_capabilities = sorted(
        capability
        for capability in descriptor.capabilities
        if not isinstance(capability, str) or not _RUNTIME_TOKEN_RE.fullmatch(capability)
    )
    if invalid_capabilities:
        raise RuntimePluginIncompatibleError(
            f"Runtime {runtime_id} dichiara capability non valide: {', '.join(map(str, invalid_capabilities))}"
        )
    return descriptor


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
        descriptor = _validate_descriptor(runtime_id, describe())
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
