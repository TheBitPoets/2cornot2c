#!/usr/bin/env python3
"""Activate, migrate, or roll back the dedicated Ubuntu pilot topology fail-closed."""

from __future__ import annotations

import argparse
import errno
import hashlib
import ipaddress
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit

import jsonschema
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_pilot_deployment as deployment  # noqa: E402
from scripts.nginx_config_ast import (  # noqa: E402
    Directive,
    NginxConfigError,
    Token,
    direct as _shared_direct,
    parse_nginx_source as _shared_parse_nginx_source,
    tokenize_nginx as _shared_tokenize_nginx,
    walk_directives as _shared_walk_directives,
)


NGINX_CONFIG = Path("/etc/nginx/nginx.conf")
NGINX_MODULES_ENABLED_ROOT = Path("/etc/nginx/modules-enabled")
NGINX_PREFIX = Path("/usr/share/nginx")
NGINX_MODULES_LINK = NGINX_PREFIX / "modules"
NGINX_MODULES_ROOT = Path("/usr/lib/nginx/modules")
NGINX_MODULES_AVAILABLE_ROOT = NGINX_PREFIX / "modules-available"
DEPLOYMENTS_ROOT = Path("/etc/thebitlab/deployments")
CURRENT_LINK = Path("/etc/thebitlab/current")
STATE_FILE = Path("/etc/thebitlab/activation-state.json")
DISTRO_DEFAULT = Path("/etc/nginx/sites-enabled/default")
DISTRO_AVAILABLE = Path("/etc/nginx/sites-available/default")
PROCESS_LINK = Path("/etc/nginx/modules-enabled/90-thebitlab-process-error-log.conf")
FORMAT_LINK = Path("/etc/nginx/conf.d/thebitlab-log-format.conf")
SITE_LINK = Path("/etc/nginx/sites-enabled/thebitlab.conf")
LOGROTATE_LINK = Path("/etc/logrotate.d/thebitlab")
SYSTEMD_LINK = Path("/etc/systemd/system/thebitlab.service")
NGINX_MIGRATION_GUARD = Path("/etc/systemd/system/nginx.service")
NGINX_PACKAGE_UNIT = Path("/usr/lib/systemd/system/nginx.service")
NGINX_BINARY = Path("/usr/sbin/nginx")
PROC_ROOT = Path("/proc")
NGINX_CONTROL_GROUP = "/system.slice/nginx.service"
NGINX_WANTS_LINK = Path("/etc/systemd/system/multi-user.target.wants/nginx.service")
THEBITLAB_WANTS_LINK = Path(
    "/etc/systemd/system/multi-user.target.wants/thebitlab.service"
)
SYSTEMD_UNIT_SEARCH_PATH_NAME = "systemd-search-system-unit"
SYSTEMD_GENERATOR_SEARCH_PATH_NAME = "systemd-search-system-generator"
SYSTEMD_GENERATED_DIRECTORY_NAMES = frozenset(
    {"generator", "generator.early", "generator.late"}
)
SYSV_INIT_ROOT = Path("/etc/init.d")
RC_LOCAL_PATH = Path("/etc/rc.local")
# Closed, input-independent outputs observed from package generators in the supported
# Ubuntu 24.04 isolated container. Any other package-unit link needs an explicit
# provenance policy instead of inheriting trust from /run/systemd/generator*.
GENERATED_PACKAGE_UNIT_LINKS = {
    ("generator", "getty.target.wants", "console-getty.service"):
        Path("/usr/lib/systemd/system/console-getty.service"),
    ("generator", "local-fs.target.wants", "systemd-remount-fs.service"):
        Path("/usr/lib/systemd/system/systemd-remount-fs.service"),
}
SYSTEMD_ENABLEMENT_DIRECTORY_SUFFIXES = (".wants", ".requires", ".upholds")
SYSTEMD_ENABLED_STATES = frozenset(
    {"enabled", "enabled-runtime", "linked", "linked-runtime"}
)
SYSTEMD_UNIT_SUFFIXES = frozenset(
    {
        ".automount",
        ".device",
        ".mount",
        ".path",
        ".scope",
        ".service",
        ".slice",
        ".socket",
        ".swap",
        ".target",
        ".timer",
    }
)
LOGROTATE_RUNTIME_ROOT = Path("/run/thebitlab")
LOGROTATE_RUNTIME_DIRECTORY = LOGROTATE_RUNTIME_ROOT / "logrotate"
LOGROTATE_SNAPSHOT = LOGROTATE_RUNTIME_DIRECTORY / "reopen.json"
LOGROTATE_SNAPSHOT_MAX_AGE_SECONDS = 300
LOGROTATE_REOPEN_TIMEOUT_SECONDS = 10.0
LOGROTATE_REOPEN_POLL_SECONDS = 0.1
BOOT_ID_PATH = Path("/proc/sys/kernel/random/boot_id")
CANONICAL_NGINX_PORTS = frozenset({80, 443})
ENABLED_NGINX_UNIT_FILE_STATES = frozenset({"enabled"})
DISABLED_NGINX_UNIT_FILE_STATES = frozenset({"disabled"})
PREFLIGHT_NGINX_UNIT_FILE_STATES = frozenset({"enabled", "disabled"})
INTEGRATION_LINKS = {
    PROCESS_LINK: "/etc/thebitlab/current/nginx/thebitlab-process-error-log.conf",
    FORMAT_LINK: "/etc/thebitlab/current/nginx/thebitlab-log-format.conf",
    SITE_LINK: "/etc/thebitlab/current/nginx/thebitlab.conf",
    LOGROTATE_LINK: "/etc/thebitlab/current/logrotate/thebitlab",
    SYSTEMD_LINK: "/etc/thebitlab/current/systemd/thebitlab.service",
}
LEGACY_LINKS = {
    FORMAT_LINK: INTEGRATION_LINKS[FORMAT_LINK],
    SITE_LINK: INTEGRATION_LINKS[SITE_LINK],
    SYSTEMD_LINK: INTEGRATION_LINKS[SYSTEMD_LINK],
}
LEGACY_GENERATED_FILES = (
    "nginx/thebitlab-log-format.conf",
    "nginx/thebitlab.conf",
    "systemd/thebitlab.service",
    "firewall/origin-exposure.json",
    "manifest.normalized.json",
)
LEGACY_SCHEMA = ROOT / "schemas" / "pilot-deployment-v1-legacy.schema.json"
LEGACY_TEMPLATE_ROOT = ROOT / "deploy" / "pilot" / "legacy-v1"
_SOURCE_MARKER = re.compile(r"^# configuration file (/.+):$")
_ORIGIN_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?[.])+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


class ActivationError(RuntimeError):
    """The host cannot safely activate, migrate, or restore the candidate."""


def _assert_os_runtime_path(path: Path, *, allow_missing_leaf: bool = False) -> None:
    candidate = path if path.exists() else path.parent if allow_missing_leaf else path
    try:
        candidate = candidate.absolute()
        current = Path(candidate.anchor)
        for part in candidate.parts[1:]:
            current /= part
            metadata = current.lstat()
            if current.is_symlink() or metadata.st_uid != 0 or metadata.st_mode & 0o022:
                raise ActivationError(f"Python runtime path non trusted: {path}")
        if not candidate.exists():
            raise ActivationError(f"Python runtime path assente: {path}")
    except OSError as exc:
        raise ActivationError(f"Python runtime path non verificabile: {path}") from exc


def _require_trusted_runtime() -> None:
    """Reject checkout execution and non-isolated Python before host inspection/mutation."""

    expected_root = os.environ.get("THEBITLAB_TRUSTED_TOOLCHAIN_ROOT")
    toolchain_id = os.environ.get("THEBITLAB_TRUSTED_TOOLCHAIN_ID")
    canonical_parent = Path("/usr/lib/thebitlab/pilot-tools")
    if (
        not expected_root
        or not toolchain_id
        or ROOT != Path(expected_root)
        or ROOT.parent != canonical_parent
        or ROOT.name != toolchain_id
        or Path.cwd() != Path("/")
    ):
        raise ActivationError("Production activation richiede il trusted launcher installato")
    flags = sys.flags
    if not (
        flags.isolated
        and flags.ignore_environment
        and flags.no_user_site
        and getattr(flags, "safe_path", False)
        and getattr(flags, "dont_write_bytecode", False)
    ):
        raise ActivationError("Python production non è isolato (-I -B richiesti)")
    if not sys.path or Path(sys.path[0]) != ROOT:
        raise ActivationError("Trusted toolchain assente dalla posizione iniziale di sys.path")
    forbidden = {"", ".", str(Path.cwd()), str(Path.home())}
    if any(entry in forbidden or not Path(entry).is_absolute() for entry in sys.path):
        raise ActivationError("sys.path production contiene una search root non trusted")
    for entry in sys.path[1:]:
        _assert_os_runtime_path(Path(entry), allow_missing_leaf=True)
    local_modules = (Path(__file__), Path(deployment.__file__), Path(sys.modules[Directive.__module__].__file__))
    if any(ROOT not in module.resolve(strict=True).parents for module in local_modules):
        raise ActivationError("Modulo security-critical caricato fuori dalla trusted toolchain")
    jsonschema_path = Path(jsonschema.__file__).resolve(strict=True)
    if ROOT in jsonschema_path.parents:
        raise ActivationError("jsonschema shadowed dalla toolchain")
    _assert_os_runtime_path(jsonschema_path)


def _runtime_information() -> dict[str, Any]:
    return {
        "isolated": bool(sys.flags.isolated),
        "ignore_environment": bool(sys.flags.ignore_environment),
        "no_user_site": bool(sys.flags.no_user_site),
        "safe_path": bool(getattr(sys.flags, "safe_path", False)),
        "dont_write_bytecode": bool(getattr(sys.flags, "dont_write_bytecode", False)),
        "cwd": str(Path.cwd()),
        "sys_path": list(sys.path),
        "toolchain_root": str(ROOT),
        "activator": str(Path(__file__).resolve()),
        "renderer": str(Path(deployment.__file__).resolve()),
        "jsonschema": str(Path(jsonschema.__file__).resolve()),
    }


def _source_path(path: Path) -> str:
    """Return the POSIX spelling emitted by nginx -T, including in portable tests."""

    return path.as_posix()


@dataclass(frozen=True)
class BundleInfo:
    path: Path
    manifest: dict[str, Any]
    lock_digest: str
    sources: Mapping[str, str]


@dataclass(frozen=True)
class Preflight:
    candidate: BundleInfo
    source_kind: str
    previous_v2: BundleInfo | None
    unsafe_provenance: Mapping[str, Any]


@dataclass(frozen=True)
class EffectiveNginxUnit:
    main_pid: int
    control_group: str


@dataclass(frozen=True)
class NginxProcess:
    pid: int
    control_groups: frozenset[str]


@dataclass(frozen=True)
class LogInode:
    path: Path
    device: int
    inode: int


def _run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    if result.returncode:
        detail = "\n".join(output.splitlines()[-20:])
        raise ActivationError(f"Comando fallito ({' '.join(command)}):\n{detail}")
    return output


def _nginx_effective() -> str:
    command = ["nginx", "-T", "-c", str(NGINX_CONFIG)]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        detail = "\n".join((result.stdout + result.stderr).splitlines()[-20:])
        raise ActivationError(f"Comando fallito ({' '.join(command)}):\n{detail}")
    if not result.stdout.strip():
        raise ActivationError("nginx -T non ha prodotto la configurazione effettiva")
    return result.stdout


def _fault(point: str) -> None:
    """Terminate non-catchably only when the ephemeral crash-test interlock is set."""

    if (
        os.environ.get("THEBITLAB_EPHEMERAL_CRASH_TEST") == "1"
        and os.environ.get("THEBITLAB_ACTIVATION_CRASH_POINT") == point
    ):
        os._exit(97)


def _fsync_directory(path: Path) -> None:
    """Persist directory-entry changes on POSIX; fsync failure is fatal."""

    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _symlink_state(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {"present": False}
    if not stat.S_ISLNK(metadata.st_mode):
        raise ActivationError(f"Elemento gestito non-symlink: {path}")
    return {"present": True, "target": os.readlink(path)}


def _replace_symlink(path: Path, target: str) -> None:
    parent_existed = path.parent.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not parent_existed:
        _fsync_directory(path.parent.parent)
    temporary = path.with_name(f".{path.name}.thebitlab-{os.getpid()}")
    try:
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(target)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _remove_symlink(path: Path) -> None:
    state = _symlink_state(path)
    if state["present"]:
        path.unlink()
        _fsync_directory(path.parent)


def _directory_entries(path: Path) -> set[str]:
    try:
        return {entry.name for entry in path.iterdir()}
    except OSError as exc:
        raise ActivationError(f"Layout Ubuntu assente o non accessibile: {path}") from exc


def _check_managed_link(path: Path, expected: str, *, allow_absent: bool) -> None:
    state = _symlink_state(path)
    if not state["present"]:
        if allow_absent:
            return
        raise ActivationError(f"Symlink pilot atteso assente: {path}")
    if state["target"] != expected:
        raise ActivationError(f"Symlink pilot inatteso: {path}")


def _split_effective_sources(effective: str) -> dict[str, str]:
    sources: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    preamble: list[str] = []
    for raw_line in effective.splitlines(keepends=True):
        marker = _SOURCE_MARKER.fullmatch(raw_line.rstrip("\r\n"))
        if marker is not None:
            if current is not None:
                if current in sources:
                    raise ActivationError(f"Sorgente nginx -T duplicata: {current}")
                sources[current] = "".join(buffer).replace("\r\n", "\n")
            elif any(line.strip() for line in preamble):
                raise ActivationError("Output nginx -T ambiguo prima del primo source marker")
            source = marker.group(1)
            pure = PurePosixPath(source)
            if not pure.is_absolute() or ".." in pure.parts or str(pure) != source:
                raise ActivationError(f"Source marker nginx non canonico: {source}")
            current = source
            buffer = []
            continue
        if raw_line.lstrip().startswith("# configuration file ") and current is not None:
            raise ActivationError("Source marker nginx -T malformato o ambiguo")
        if current is None:
            preamble.append(raw_line)
        else:
            buffer.append(raw_line)
    if current is None:
        raise ActivationError("Output nginx -T privo di source marker")
    if current in sources:
        raise ActivationError(f"Sorgente nginx -T duplicata: {current}")
    sources[current] = "".join(buffer).replace("\r\n", "\n")
    return sources


def _tokenize_nginx(source: str, text: str) -> tuple[Token, ...]:
    try:
        return _shared_tokenize_nginx(source, text)
    except NginxConfigError as exc:
        raise ActivationError(str(exc)) from exc


def _parse_nginx_source(source: str, text: str) -> tuple[Directive, ...]:
    try:
        return _shared_parse_nginx_source(source, text)
    except NginxConfigError as exc:
        raise ActivationError(str(exc)) from exc


def _walk_directives(
    directives: Sequence[Directive], context: tuple[str, ...] = ()
) -> Iterable[tuple[Directive, tuple[str, ...]]]:
    return _shared_walk_directives(directives, context)


def _direct(directives: Sequence[Directive], name: str) -> list[Directive]:
    return _shared_direct(directives, name)


def _assert_source_exact(sources: Mapping[str, str], path: str, expected: str) -> None:
    actual = sources.get(path)
    if actual is None:
        raise ActivationError(f"Artifact nginx effettivo assente: {path}")
    # nginx -T inserts a separator newline between dumped source files.
    # Ignore only the count of trailing newlines; every semantic/content byte remains exact.
    if actual.rstrip("\n") != expected.replace("\r\n", "\n").rstrip("\n"):
        raise ActivationError(f"Artifact nginx effettivo divergente dal bundle locked: {path}")


def _validate_ubuntu_include_chain(parsed: Mapping[str, tuple[Directive, ...]]) -> None:
    root_source = _source_path(NGINX_CONFIG)
    root = parsed.get(root_source)
    if root is None:
        raise ActivationError("nginx -T non attribuisce la configurazione a nginx.conf")
    http_blocks = [item for item in root if item.name == "http" and item.children is not None]
    if len(http_blocks) != 1:
        raise ActivationError("nginx.conf deve contenere un solo contesto http")
    expected = {
        ((), "/etc/nginx/modules-enabled/*.conf"),
        (("http",), "/etc/nginx/mime.types"),
        (("http",), "/etc/nginx/conf.d/*.conf"),
        (("http",), "/etc/nginx/sites-enabled/*"),
    }
    actual: set[tuple[tuple[str, ...], str]] = set()
    for source, directives in parsed.items():
        for directive, context in _walk_directives(directives):
            if directive.name != "include":
                continue
            if len(directive.args) != 1:
                raise ActivationError(f"Include nginx ambiguo in {source}:{directive.line}")
            actual.add((context, directive.args[0]))
    if actual != expected:
        raise ActivationError("Include chain nginx Ubuntu divergente o non gestita")


def _validate_module_source(source: str, directives: Sequence[Directive]) -> None:
    for directive, _ in _walk_directives(directives):
        if directive.children is not None or directive.name != "load_module" or len(directive.args) != 1:
            raise ActivationError(f"Configurazione modules-enabled unmanaged: {source}")


def _validate_pilot_servers(servers: Sequence[Directive], *, request_sink: str | None) -> None:
    if len(servers) != 4:
        raise ActivationError(f"Numero vhost pilot inatteso: {len(servers)}")
    if request_sink is not None:
        for server in servers:
            assert server.children is not None
            errors = _direct(server.children, "error_log")
            values = [" ".join(item.args) for item in errors]
            if values != [request_sink]:
                raise ActivationError("Vhost pilot capace di persistere errori request-context")
            for directive, context in _walk_directives(server.children):
                if context and directive.name in {"access_log", "error_log"}:
                    raise ActivationError("Logging request-context annidato non ammesso")
    defaults: list[str] = []
    for server in servers:
        assert server.children is not None
        for listen in _direct(server.children, "listen"):
            if "default_server" in listen.args:
                defaults.append(" ".join(listen.args))
    expected = {
        "80 default_server",
        "[::]:80 default_server",
        "443 ssl default_server",
        "[::]:443 ssl default_server",
    }
    if set(defaults) != expected or len(defaults) != 4:
        raise ActivationError("Default server pilot IPv4/IPv6 assente, duplicato o ambiguo")


def _validate_distro_default(servers: Sequence[Directive]) -> None:
    if len(servers) != 1 or servers[0].children is None:
        raise ActivationError("Default distro Ubuntu modificato o ambiguo")
    server = servers[0]
    listens = {" ".join(item.args) for item in _direct(server.children, "listen")}
    names = [item.args for item in _direct(server.children, "server_name")]
    if not {"80 default_server", "[::]:80 default_server"}.issubset(listens) or names != [("_",)]:
        raise ActivationError("Default distro Ubuntu non riconosciuto")
    if _direct(server.children, "access_log") or _direct(server.children, "error_log"):
        raise ActivationError("Default distro Ubuntu con logging locale inatteso")
    if any(item.name == "include" for item, _ in _walk_directives(server.children)):
        raise ActivationError("Default distro Ubuntu include configurazione non gestita")


def validate_effective_nginx(
    effective: str,
    manifest: Mapping[str, Any] | None,
    *,
    topology: str,
    expected_sources: Mapping[str, str],
    trusted_module_sources: frozenset[str] = frozenset(),
) -> None:
    """Validate source attribution and active server topology from real nginx -T output."""

    sources = _split_effective_sources(effective)
    parsed = {path: _parse_nginx_source(path, text) for path, text in sources.items()}
    _validate_ubuntu_include_chain(parsed)

    base_sources = {_source_path(NGINX_CONFIG), "/etc/nginx/mime.types"}
    allowed = base_sources | set(expected_sources)
    module_prefix = "/etc/nginx/modules-enabled/"
    module_sources = {
        source
        for source in sources
        if source.startswith(module_prefix) and source.endswith(".conf")
    }
    expected_pilot_modules = {
        source for source in expected_sources if source.startswith(module_prefix)
    }
    if module_sources != expected_pilot_modules | set(trusted_module_sources):
        raise ActivationError("Source module nginx effettive non attestate dall'inventario")
    allowed |= module_sources
    if topology == "preinstall-default":
        allowed.add(_source_path(DISTRO_DEFAULT))
    unexpected = sorted(set(sources) - allowed)
    missing = sorted(base_sources - set(sources))
    if unexpected or missing:
        detail = unexpected or missing
        raise ActivationError("Source nginx effettive unmanaged o mancanti: " + ", ".join(detail))

    for path, expected in expected_sources.items():
        _assert_source_exact(sources, path, expected)
    for source in module_sources - set(expected_sources):
        _validate_module_source(source, parsed[source])

    servers = [
        directive
        for directives in parsed.values()
        for directive, _ in _walk_directives(directives)
        if directive.name == "server" and directive.children is not None
    ]
    pilot_servers = [server for server in servers if server.source == _source_path(SITE_LINK)]
    unmanaged = [server for server in servers if server.source != _source_path(SITE_LINK)]

    if topology == "v2":
        if manifest is None:
            raise ActivationError("Manifest v2 richiesto per la topologia attiva")
        if unmanaged:
            raise ActivationError(
                "Vhost nginx unmanaged rilevato: " + ", ".join(sorted({item.source for item in unmanaged}))
            )
        _validate_pilot_servers(pilot_servers, request_sink="/dev/null")
        origin_host = urlsplit(manifest["origin"]["url"]).hostname
        expected_access = (manifest["origin"]["access_log"], "thebitlab")
        for server in pilot_servers:
            assert server.children is not None
            names = [item.args for item in _direct(server.children, "server_name")]
            default_server = names == [("_",)]
            if names not in [[("_",)], [(origin_host,)]]:
                raise ActivationError("Identità vhost pilot inattesa")
            accesses = [item.args for item in _direct(server.children, "access_log")]
            if accesses != ([("off",)] if default_server else [expected_access]):
                raise ActivationError("Access log pilot fuori dalla policy path-only")
        process_source = parsed.get(_source_path(PROCESS_LINK), ())
        process = _direct(process_source, "error_log")
        expected_process = (manifest["origin"]["error_log"], "notice")
        if len(process) != 1 or process[0].args != expected_process:
            raise ActivationError("Error log process-level main-context assente o duplicato")
        try:
            deployment._validate_nginx_logging_tree(
                sources[_source_path(PROCESS_LINK)],
                sources[_source_path(SITE_LINK)],
                manifest,
            )
        except deployment.DeploymentValidationError as exc:
            raise ActivationError("Logging nginx effettivo fuori policy") from exc
    elif topology == "legacy-v1":
        if unmanaged:
            raise ActivationError("Legacy v1 contiene vhost unmanaged")
        _validate_pilot_servers(pilot_servers, request_sink=None)
        for server in pilot_servers[:2]:
            assert server.children is not None
            if _direct(server.children, "error_log"):
                raise ActivationError("Legacy v1 default modificato")
        for server in pilot_servers[2:]:
            assert server.children is not None
            errors = _direct(server.children, "error_log")
            if [item.args for item in errors] != [
                ("/var/log/nginx/thebitlab-error.log", "warn")
            ]:
                raise ActivationError("Legacy v1 logging non corrisponde al fingerprint supportato")
    elif topology == "preinstall-default":
        if pilot_servers:
            raise ActivationError("Pilot site inatteso nella topologia preinstall")
        default_servers = [item for item in unmanaged if item.source == _source_path(DISTRO_DEFAULT)]
        if len(default_servers) != len(unmanaged):
            raise ActivationError("Vhost unmanaged nella topologia preinstall")
        _validate_distro_default(default_servers)
    elif topology == "preinstall-empty":
        if servers:
            raise ActivationError("Vhost inatteso nella topologia preinstall vuota")
    else:
        raise ActivationError(f"Topologia nginx sconosciuta: {topology}")


def _assert_trusted_metadata(path: Path, *, directory: bool, require_root_owner: bool) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ActivationError(f"Path trusted assente o non accessibile: {path}") from exc
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if path.is_symlink() or not expected_type(metadata.st_mode):
        raise ActivationError(f"Path trusted non regolare: {path}")
    if os.name != "nt" and require_root_owner and metadata.st_uid != 0:
        raise ActivationError(f"Path trusted non root-owned: {path}")
    if os.name != "nt" and metadata.st_mode & 0o022:
        raise ActivationError(f"Path trusted scrivibile da group/other: {path}")
    if not directory and getattr(metadata, "st_nlink", 1) != 1:
        raise ActivationError(f"Artifact trusted con hardlink inatteso: {path}")


def _verify_trusted_tree(
    bundle: Path,
    expected_files: set[str],
    *,
    deployments_root: Path,
    require_root_owner: bool,
) -> Path:
    if not bundle.is_absolute():
        raise ActivationError("Bundle deployment deve essere assoluto")
    lexical_bundle = Path(os.path.abspath(bundle))
    lexical_root = Path(os.path.abspath(deployments_root))
    try:
        relative = lexical_bundle.relative_to(lexical_root)
    except ValueError as exc:
        raise ActivationError(f"Bundle fuori dalla deployment root trusted: {bundle}") from exc
    if relative == Path("."):
        raise ActivationError("La deployment root non è un bundle")

    if require_root_owner:
        current = Path(lexical_bundle.anchor)
        parts = lexical_bundle.parts[1:]
    else:
        # Portable/unit tests establish their supplied deployment root as the trust boundary.
        current = lexical_root.parent
        parts = (lexical_root.name, *relative.parts)
    for part in parts:
        current /= part
        _assert_trusted_metadata(current, directory=True, require_root_owner=require_root_owner)
    if lexical_bundle.resolve(strict=True) != lexical_bundle:
        raise ActivationError("Bundle o ancestor risolto tramite symlink/path alternativo")

    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for root_name, directory_names, file_names in os.walk(lexical_bundle, followlinks=False):
        root_path = Path(root_name)
        for name in directory_names:
            path = root_path / name
            _assert_trusted_metadata(path, directory=True, require_root_owner=require_root_owner)
            actual_directories.add(path.relative_to(lexical_bundle).as_posix())
        for name in file_names:
            path = root_path / name
            _assert_trusted_metadata(path, directory=False, require_root_owner=require_root_owner)
            actual_files.add(path.relative_to(lexical_bundle).as_posix())
    if actual_files != expected_files:
        raise ActivationError("Inventario artifact trusted inatteso")
    expected_directories = {
        str(parent)
        for name in expected_files
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    if actual_directories != expected_directories:
        raise ActivationError("Inventario directory trusted inatteso")
    return lexical_bundle


def _read_lock(bundle: Path, expected_files: Sequence[str]) -> tuple[dict[str, Any], str]:
    lock_path = bundle / "deployment.lock.json"
    try:
        raw = lock_path.read_bytes()
        lock = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError("Lock deployment assente o non valido") from exc
    required_keys = {"schema_version", "deployment_id", "release_commit", "files"}
    if not isinstance(lock, dict) or set(lock) != required_keys:
        raise ActivationError("Lock deployment con struttura inattesa")
    files = lock.get("files")
    if not isinstance(files, dict) or set(files) != set(expected_files):
        raise ActivationError("Lock deployment con inventario inatteso")
    for name, expected in files.items():
        try:
            actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
        except OSError as exc:
            raise ActivationError(f"Artifact bundle assente: {name}") from exc
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or actual != expected:
            raise ActivationError(f"Digest bundle non valido: {name}")
    return lock, hashlib.sha256(raw).hexdigest()


def _compare_expected_bundle(bundle: Path, expected: Path, files: Sequence[str]) -> None:
    for name in (*files, "deployment.lock.json"):
        if (bundle / name).read_bytes() != (expected / name).read_bytes():
            raise ActivationError(f"Artifact bundle non riproducibile dal renderer trusted: {name}")


def verify_bundle(
    bundle: Path,
    *,
    deployments_root: Path = DEPLOYMENTS_ROOT,
    require_root_owner: bool = True,
) -> BundleInfo:
    expected_files = set(deployment.GENERATED_FILES) | {"deployment.lock.json"}
    trusted = _verify_trusted_tree(
        bundle,
        expected_files,
        deployments_root=deployments_root,
        require_root_owner=require_root_owner,
    )
    manifest = deployment.load_json(trusted / "manifest.normalized.json")
    deployment.validate_manifest(manifest)
    deployment.validate_versioned_logging(manifest)
    lock, lock_digest = _read_lock(trusted, deployment.GENERATED_FILES)
    if (
        lock["schema_version"] != "thebitlab.pilot-deployment-lock.v1"
        or lock["deployment_id"] != manifest["deployment_id"]
        or lock["release_commit"] != manifest["release"]["commit"]
    ):
        raise ActivationError("Lock deployment non coerente con il manifest")
    if (trusted / "manifest.normalized.json").read_bytes() != deployment.normalized_manifest_bytes(manifest):
        raise ActivationError("Manifest normalizzato non canonico")
    process_text = (trusted / "nginx/thebitlab-process-error-log.conf").read_text(encoding="utf-8")
    format_text = (trusted / "nginx/thebitlab-log-format.conf").read_text(encoding="utf-8")
    site_text = (trusted / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    logrotate_text = (trusted / "logrotate/thebitlab").read_text(encoding="utf-8")
    deployment.validate_rendered_logging(
        process_text, format_text, site_text, logrotate_text, manifest
    )
    with tempfile.TemporaryDirectory(prefix="thebitlab-verify-bundle-") as temporary_name:
        expected = Path(temporary_name) / "bundle"
        deployment.render_bundle(manifest, expected)
        _compare_expected_bundle(trusted, expected, deployment.GENERATED_FILES)
    sources = {
        _source_path(PROCESS_LINK): process_text,
        _source_path(FORMAT_LINK): format_text,
        _source_path(SITE_LINK): site_text,
    }
    return BundleInfo(trusted, manifest, lock_digest, sources)


def _legacy_manifest_errors(manifest: Mapping[str, Any]) -> list[str]:
    schema = deployment.load_json(LEGACY_SCHEMA)
    Draft202012Validator.check_schema(schema)
    errors = [item.message for item in Draft202012Validator(schema).iter_errors(manifest)]
    if errors:
        return errors
    origin = manifest["origin"]
    try:
        parsed = urlsplit(origin["url"])
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return ["origin legacy non valida"]
    if (
        parsed.scheme != "https"
        or hostname is None
        or _ORIGIN_HOST_RE.fullmatch(hostname) is None
        or origin["url"] != f"https://{hostname}"
        or port is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username is not None
    ):
        errors.append("origin legacy non canonica")
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for raw in origin["allowed_proxy_cidrs"]:
        try:
            network = ipaddress.ip_network(raw, strict=True)
        except ValueError:
            errors.append("CIDR legacy non canonica")
            continue
        if network.prefixlen == 0 or network.is_loopback or network.is_unspecified or network.is_multicast:
            errors.append("CIDR legacy non ammessa")
        networks.append(network)
    for index, network in enumerate(networks):
        if any(
            index != other and network.version == candidate.version and network.subnet_of(candidate)
            for other, candidate in enumerate(networks)
        ):
            errors.append("CIDR legacy sovrapposta")
    return errors


def _render_text(template: Path, replacements: Mapping[str, str]) -> str:
    rendered = template.read_text(encoding="utf-8")
    for name, value in replacements.items():
        rendered = rendered.replace(f"@@{name}@@", value)
    if "@@" in rendered:
        raise ActivationError(f"Template legacy incompleto: {template.name}")
    return rendered


def _legacy_contents(manifest: Mapping[str, Any]) -> dict[str, str]:
    origin = manifest["origin"]
    service = manifest["service"]
    release = manifest["release"]
    features = manifest["features"]
    hostname = urlsplit(origin["url"]).hostname
    assert hostname is not None
    github_app_directory = PurePosixPath(service["home_directory"]) / ".thebitlab-secrets/github-app"
    replacements = {
        "DEPLOYMENT_ID": manifest["deployment_id"],
        "REPOSITORY_ROOT": release["repository_root"],
        "PYTHON_EXECUTABLE": release["python_executable"],
        "RELEASE_COMMIT": release["commit"],
        "SERVICE_USER": service["user"],
        "SERVICE_GROUP": service["group"],
        "HOME_DIRECTORY": service["home_directory"],
        "BIND_HOST": service["bind_host"],
        "APP_PORT": str(service["port"]),
        "ENVIRONMENT_FILE": service["environment_file"],
        "LOCK_DIRECTORY": service["lock_directory"],
        "DATA_ROOT": manifest["data"]["root"],
        "AUTH_DB_PATH": manifest["data"]["auth_db_path"],
        "GOOGLE_REDIRECT_URI": f"{origin['url']}/auth/google/callback",
        "GITHUB_OAUTH_ARGUMENTS": (
            f" --enable-github-oauth --github-redirect-uri {origin['url']}/auth/github/callback"
            if features["github_oauth"] else ""
        ),
        "GITHUB_APP_FLAG": " --enable-github-app-token-runtime" if features["github_app_token_runtime"] else "",
        "GITHUB_APP_WRITE_PATH": f" -{github_app_directory}" if features["github_app_token_runtime"] else "",
        "ORIGIN_HOST": hostname,
        "ORIGIN_ACCESS_RULES": deployment._origin_access_rules(manifest),
        "TLS_CERTIFICATE_FILE": origin["tls_certificate_file"],
        "TLS_PRIVATE_KEY_FILE": origin["tls_private_key_file"],
        "ACCESS_LOG": origin["access_log"],
        "ERROR_LOG": origin["error_log"],
    }
    firewall = {
        "schema_version": "thebitlab.origin-exposure.v1",
        "mode": origin["exposure"],
        "default_for_tcp_ports": "deny" if origin["exposure"] == "edge_only" else "allow",
        "tcp_ports": [80, 443],
        "allowed_source_cidrs": origin["allowed_proxy_cidrs"],
        "backend_bind": f"{service['bind_host']}:{service['port']}",
    }
    return {
        "nginx/thebitlab-log-format.conf": _render_text(
            LEGACY_TEMPLATE_ROOT / "thebitlab-log-format.conf.template", replacements
        ),
        "nginx/thebitlab.conf": _render_text(
            LEGACY_TEMPLATE_ROOT / "thebitlab-nginx.conf.template", replacements
        ),
        "systemd/thebitlab.service": _render_text(
            LEGACY_TEMPLATE_ROOT / "thebitlab.service.template", replacements
        ),
        "firewall/origin-exposure.json": json.dumps(firewall, indent=2, sort_keys=True) + "\n",
        "manifest.normalized.json": deployment.normalized_manifest_bytes(manifest).decode("utf-8"),
    }


def render_legacy_v1_bundle(manifest: Mapping[str, Any], output: Path) -> None:
    """Render only the exact historical v1 fingerprint accepted for migration."""

    errors = _legacy_manifest_errors(manifest)
    if errors:
        raise ActivationError("Legacy v1 manifest non supportato: " + "; ".join(errors))
    if output.exists():
        raise ActivationError(f"Directory legacy output già esistente: {output}")
    contents = _legacy_contents(manifest)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for name in LEGACY_GENERATED_FILES:
            path = temporary / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents[name], encoding="utf-8", newline="\n")
        lock = {
            "schema_version": "thebitlab.pilot-deployment-lock.v1",
            "deployment_id": manifest["deployment_id"],
            "release_commit": manifest["release"]["commit"],
            "files": {
                name: hashlib.sha256((temporary / name).read_bytes()).hexdigest()
                for name in LEGACY_GENERATED_FILES
            },
        }
        (temporary / "deployment.lock.json").write_text(
            json.dumps(lock, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify_legacy_v1_bundle(
    bundle: Path,
    *,
    deployments_root: Path = DEPLOYMENTS_ROOT,
    require_root_owner: bool = True,
) -> BundleInfo:
    expected_files = set(LEGACY_GENERATED_FILES) | {"deployment.lock.json"}
    trusted = _verify_trusted_tree(
        bundle,
        expected_files,
        deployments_root=deployments_root,
        require_root_owner=require_root_owner,
    )
    manifest = deployment.load_json(trusted / "manifest.normalized.json")
    errors = _legacy_manifest_errors(manifest)
    if errors:
        raise ActivationError("Legacy v1 manifest non supportato: " + "; ".join(errors))
    lock, lock_digest = _read_lock(trusted, LEGACY_GENERATED_FILES)
    if (
        lock["schema_version"] != "thebitlab.pilot-deployment-lock.v1"
        or lock["deployment_id"] != manifest["deployment_id"]
        or lock["release_commit"] != manifest["release"]["commit"]
    ):
        raise ActivationError("Legacy v1 lock non coerente")
    expected = _legacy_contents(manifest)
    for name, content in expected.items():
        if (trusted / name).read_text(encoding="utf-8") != content:
            raise ActivationError(f"Legacy v1 artifact modificato: {name}")
    sources = {
        _source_path(FORMAT_LINK): expected["nginx/thebitlab-log-format.conf"],
        _source_path(SITE_LINK): expected["nginx/thebitlab.conf"],
    }
    return BundleInfo(trusted, manifest, lock_digest, sources)


def _assert_root_symlink(path: Path, expected_target: str) -> None:
    state = _symlink_state(path)
    if not state["present"] or state["target"] != expected_target:
        raise ActivationError(f"Symlink trusted inatteso: {path}")
    metadata = path.lstat()
    if os.name != "nt" and metadata.st_uid != 0:
        raise ActivationError(f"Symlink trusted non root-owned: {path}")


def _verify_trusted_ancestry(path: Path, boundary: Path) -> None:
    lexical = Path(os.path.abspath(path))
    root = Path(os.path.abspath(boundary))
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise ActivationError(f"Target fuori dal trust boundary: {path}") from exc
    current = root
    _assert_trusted_metadata(current, directory=True, require_root_owner=True)
    for part in relative.parts[:-1]:
        current /= part
        _assert_trusted_metadata(current, directory=True, require_root_owner=True)
    _assert_trusted_metadata(lexical, directory=False, require_root_owner=True)


def _verify_modules_enabled_entries() -> frozenset[str]:
    """Return only module sources whose config and native code are package-attributed."""

    directory = NGINX_MODULES_ENABLED_ROOT
    trusted_sources: set[str] = set()
    package_configs: list[Path] = []
    module_binaries: list[Path] = []
    _assert_systemd_directory_ancestry(NGINX_MODULES_AVAILABLE_ROOT)
    for entry in directory.iterdir():
        source = _source_path(entry)
        if entry == PROCESS_LINK:
            _check_managed_link(entry, INTEGRATION_LINKS[PROCESS_LINK], allow_absent=True)
            if entry.is_symlink():
                trusted_sources.add(source)
            continue
        if not entry.name.endswith(".conf") or not entry.is_symlink():
            raise ActivationError(f"modules-enabled contiene artifact unmanaged: {entry}")
        try:
            link_target = os.readlink(entry)
            if not link_target.startswith("/") or Path(link_target) != Path(os.path.abspath(link_target)):
                raise OSError("target symlink non assoluto/canonico")
            _assert_root_symlink(entry, link_target)
            target = entry.resolve(strict=True)
            if (
                link_target != target.as_posix()
                or target != NGINX_MODULES_AVAILABLE_ROOT / target.name
            ):
                raise OSError("target config fuori dalla root distro/non canonico")
        except OSError as exc:
            raise ActivationError(f"Modulo nginx non attribuibile al package Ubuntu: {entry}") from exc
        _verify_trusted_ancestry(target, NGINX_MODULES_AVAILABLE_ROOT)
        try:
            directives = _parse_nginx_source(source, target.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ActivationError(f"Config modulo nginx non leggibile: {target}") from exc
        _validate_module_source(source, directives)
        package_configs.append(target)
        for directive in directives:
            raw_module = directive.args[0]
            relative = PurePosixPath(raw_module)
            if (
                relative.is_absolute()
                or raw_module != relative.as_posix()
                or len(relative.parts) != 2
                or relative.parts[0] != "modules"
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*[.]so", relative.parts[1]) is None
            ):
                raise ActivationError(f"Path load_module Ubuntu non canonico: {source}")
            semantic_path = NGINX_PREFIX / Path(*relative.parts)
            try:
                binary_metadata = semantic_path.lstat()
                binary = semantic_path.resolve(strict=True)
            except OSError as exc:
                raise ActivationError(f"Binary modulo nginx non risolvibile: {source}") from exc
            if stat.S_ISLNK(binary_metadata.st_mode):
                raise ActivationError(f"Binary modulo nginx symlink non ammesso: {semantic_path}")
            if binary != NGINX_MODULES_ROOT / relative.parts[1]:
                raise ActivationError(f"Binary modulo nginx fuori dalla root distro: {semantic_path}")
            _verify_trusted_ancestry(binary, NGINX_MODULES_ROOT)
            module_binaries.append(binary)
        trusted_sources.add(source)

    if package_configs:
        try:
            link_metadata = NGINX_MODULES_LINK.lstat()
            link_target = os.readlink(NGINX_MODULES_LINK)
            resolved_link = NGINX_MODULES_LINK.resolve(strict=True)
        except OSError as exc:
            raise ActivationError("Bridge modules nginx Ubuntu non verificabile") from exc
        if (
            not stat.S_ISLNK(link_metadata.st_mode)
            or (os.name != "nt" and link_metadata.st_uid != 0)
            or link_target != "../../lib/nginx/modules"
            or resolved_link != NGINX_MODULES_ROOT
        ):
            raise ActivationError("Bridge modules nginx Ubuntu non canonico")
        _assert_systemd_directory_ancestry(NGINX_MODULES_ROOT)
        package_owned = _dpkg_owned_paths(
            (*package_configs, NGINX_MODULES_LINK, *module_binaries)
        )
        for config in package_configs:
            if config not in package_owned:
                raise ActivationError(f"Config modulo nginx non attribuita a package installato: {config}")
        if NGINX_MODULES_LINK not in package_owned:
            raise ActivationError("Bridge modules nginx non attribuito a package installato")
        for binary in module_binaries:
            if binary not in package_owned:
                raise ActivationError(f"Binary modulo nginx non attribuito a package installato: {binary}")
    return frozenset(trusted_sources)


def verify_host_configuration_trust(
    info: BundleInfo | None = None,
    *,
    guard_required: bool | None = None,
    require_complete_links: bool = False,
    allowed_unit_file_states: frozenset[str] = ENABLED_NGINX_UNIT_FILE_STATES,
) -> frozenset[str]:
    """Validate the root-owned host configuration chain and its allowed symlinks."""

    directories = (
        Path("/etc"),
        Path("/etc/nginx"),
        Path("/etc/nginx/conf.d"),
        Path("/etc/nginx/sites-enabled"),
        Path("/etc/nginx/sites-available"),
        Path("/etc/nginx/modules-enabled"),
        Path("/etc/logrotate.d"),
        Path("/etc/thebitlab"),
        DEPLOYMENTS_ROOT,
        Path("/etc/systemd/system"),
    )
    for directory in directories:
        _assert_trusted_metadata(directory, directory=True, require_root_owner=True)
    for config in (
        NGINX_CONFIG,
        Path("/etc/nginx/mime.types"),
        Path("/etc/logrotate.conf"),
        NGINX_PACKAGE_UNIT,
        NGINX_BINARY,
    ):
        _assert_trusted_metadata(config, directory=False, require_root_owner=True)

    guard_present = _symlink_state(NGINX_MIGRATION_GUARD)["present"]
    if guard_required is True and not guard_present:
        raise ActivationError("Migration guard persistente assente")
    if guard_required is False and guard_present:
        raise ActivationError("Migration guard orphan presente: recovery esplicita richiesta")
    if guard_present:
        _verify_migration_guard()
    else:
        _attest_effective_nginx_unit(
            expect_running=None,
            allowed_unit_file_states=allowed_unit_file_states,
        )

    if DISTRO_AVAILABLE.exists() or DISTRO_AVAILABLE.is_symlink():
        _assert_trusted_metadata(DISTRO_AVAILABLE, directory=False, require_root_owner=True)
    if _symlink_state(DISTRO_DEFAULT)["present"]:
        _assert_root_symlink(DISTRO_DEFAULT, os.readlink(DISTRO_DEFAULT))
        if DISTRO_DEFAULT.resolve(strict=True) != DISTRO_AVAILABLE.resolve(strict=True):
            raise ActivationError("Default distro fuori dal trust boundary atteso")

    current_state = _symlink_state(CURRENT_LINK)
    if current_state["present"]:
        target = current_state["target"]
        if not isinstance(target, str) or not target.startswith("/"):
            raise ActivationError("Symlink current non canonico")
        _assert_root_symlink(CURRENT_LINK, target)
        current_target = Path(target)
        lexical_target = Path(os.path.abspath(current_target))
        if current_target != lexical_target or ".." in PurePosixPath(target).parts:
            raise ActivationError("Current target non canonico")
        try:
            current_target.relative_to(DEPLOYMENTS_ROOT)
        except ValueError as exc:
            raise ActivationError("Current fuori dalla deployment root trusted") from exc
        _assert_trusted_metadata(current_target, directory=True, require_root_owner=True)

    for path, expected in INTEGRATION_LINKS.items():
        if not _symlink_state(path)["present"]:
            continue
        _assert_root_symlink(path, expected)
        target = path.resolve(strict=True)
        _verify_trusted_ancestry(target, DEPLOYMENTS_ROOT)

    trusted_module_sources = _verify_modules_enabled_entries()
    if info is not None:
        verified = verify_bundle(info.path)
        if verified.lock_digest != info.lock_digest:
            raise ActivationError("Bundle target mutato durante host trust validation")
        if (
            require_complete_links
            and current_state["present"]
            and Path(current_state["target"]) == info.path
        ):
            for path, expected in INTEGRATION_LINKS.items():
                _assert_root_symlink(path, expected)
    return trusted_module_sources


def verify_ubuntu_layout() -> frozenset[str]:
    for directory in (
        Path("/etc/nginx/modules-enabled"),
        Path("/etc/nginx/conf.d"),
        Path("/etc/nginx/sites-enabled"),
        Path("/etc/logrotate.d"),
    ):
        if not directory.is_dir() or directory.is_symlink():
            raise ActivationError(f"Directory Ubuntu non supportata: {directory}")
    trusted_module_sources = _verify_modules_enabled_entries()
    try:
        text = NGINX_CONFIG.read_text(encoding="utf-8")
    except OSError as exc:
        raise ActivationError(f"nginx.conf Ubuntu assente o non accessibile: {NGINX_CONFIG}") from exc
    nginx_source = _source_path(NGINX_CONFIG)
    parsed = {nginx_source: _parse_nginx_source(nginx_source, text)}
    # Add empty placeholders so this structural check uses the same include contract.
    includes = {
        (context, directive.args[0])
        for directive, context in _walk_directives(parsed[nginx_source])
        if directive.name == "include" and len(directive.args) == 1
    }
    required = {
        ((), "/etc/nginx/modules-enabled/*.conf"),
        (("http",), "/etc/nginx/mime.types"),
        (("http",), "/etc/nginx/conf.d/*.conf"),
        (("http",), "/etc/nginx/sites-enabled/*"),
    }
    if includes != required:
        raise ActivationError("Layout nginx Ubuntu con include non gestite")
    return trusted_module_sources


def _current_bundle_path() -> Path:
    state = _symlink_state(CURRENT_LINK)
    if not state["present"]:
        raise ActivationError("Symlink current assente")
    target = state["target"]
    if not isinstance(target, str) or not target.startswith("/"):
        raise ActivationError("Symlink current non canonico")
    return Path(target)


def _validate_default_link() -> dict[str, Any]:
    state = _symlink_state(DISTRO_DEFAULT)
    if not state["present"]:
        return state
    try:
        valid = (
            DISTRO_DEFAULT.resolve(strict=True) == DISTRO_AVAILABLE.resolve(strict=True)
            and DISTRO_AVAILABLE.is_file()
            and not DISTRO_AVAILABLE.is_symlink()
        )
    except OSError:
        valid = False
    if not valid:
        raise ActivationError("Symlink default non punta al file distro regolare atteso")
    return state


def _classify_existing_topology(
    effective: str, trusted_module_sources: frozenset[str]
) -> tuple[str, BundleInfo | None]:
    site_state = _symlink_state(SITE_LINK)
    default_state = _validate_default_link()
    if not site_state["present"]:
        if _symlink_state(CURRENT_LINK)["present"]:
            raise ActivationError("current presente senza site pilot: topologia ambigua")
        for path in INTEGRATION_LINKS:
            if _symlink_state(path)["present"]:
                raise ActivationError(f"Integration link parziale inatteso: {path}")
        topology = "preinstall-default" if default_state["present"] else "preinstall-empty"
        expected = {}
        if default_state["present"]:
            expected[_source_path(DISTRO_DEFAULT)] = DISTRO_DEFAULT.read_text(encoding="utf-8")
        validate_effective_nginx(
            effective,
            None,
            topology=topology,
            expected_sources=expected,
            trusted_module_sources=trusted_module_sources,
        )
        return topology, None

    if default_state["present"]:
        raise ActivationError("Default distro e site pilot attivi simultaneamente")
    current = _current_bundle_path()
    try:
        previous_v2 = verify_bundle(current)
    except (ActivationError, deployment.DeploymentValidationError):
        previous_v2 = None
    if previous_v2 is not None:
        for path, target in INTEGRATION_LINKS.items():
            _check_managed_link(path, target, allow_absent=False)
        validate_effective_nginx(
            effective,
            previous_v2.manifest,
            topology="v2",
            expected_sources=previous_v2.sources,
            trusted_module_sources=trusted_module_sources,
        )
        return "v2", previous_v2

    legacy = verify_legacy_v1_bundle(current)
    for path, target in LEGACY_LINKS.items():
        _check_managed_link(path, target, allow_absent=False)
    for path in set(INTEGRATION_LINKS) - set(LEGACY_LINKS):
        _check_managed_link(path, INTEGRATION_LINKS[path], allow_absent=True)
        if _symlink_state(path)["present"]:
            raise ActivationError(f"Legacy v1 con link v2 parziale: {path}")
    validate_effective_nginx(
        effective,
        legacy.manifest,
        topology="legacy-v1",
        expected_sources=legacy.sources,
        trusted_module_sources=trusted_module_sources,
    )
    return "legacy-v1", None


def verify_host_preflight(bundle: Path, *, guard_required: bool | None = False) -> Preflight:
    if os.geteuid() != 0:
        raise ActivationError("Il preflight host Ubuntu richiede root")
    _attest_systemd_boot_surface()
    layout_module_sources = verify_ubuntu_layout()
    candidate = verify_bundle(bundle)
    trusted_module_sources = verify_host_configuration_trust(
        candidate,
        guard_required=guard_required,
        allowed_unit_file_states=(
            PREFLIGHT_NGINX_UNIT_FILE_STATES
            if guard_required is not True
            else ENABLED_NGINX_UNIT_FILE_STATES
        ),
    )

    site_entries = _directory_entries(Path("/etc/nginx/sites-enabled"))
    if site_entries - {"default", "thebitlab.conf"}:
        raise ActivationError("sites-enabled contiene elementi unmanaged")
    conf_entries = _directory_entries(Path("/etc/nginx/conf.d"))
    if conf_entries - {"thebitlab-log-format.conf"}:
        raise ActivationError("conf.d contiene elementi unmanaged")
    module_entries = _directory_entries(Path("/etc/nginx/modules-enabled"))
    if any(not name.endswith(".conf") for name in module_entries):
        raise ActivationError("modules-enabled contiene filename inatteso")
    for path, target in INTEGRATION_LINKS.items():
        _check_managed_link(path, target, allow_absent=True)

    if trusted_module_sources != layout_module_sources:
        raise ActivationError("Inventario moduli nginx mutato durante il preflight")
    effective = _nginx_effective()
    source_kind, previous_v2 = _classify_existing_topology(
        effective, trusted_module_sources
    )
    if previous_v2 is not None and previous_v2.path == candidate.path:
        raise ActivationError("Candidate già attiva senza activation state autorevole")
    if guard_required is True:
        _verify_migration_guard()
    else:
        _attest_preflight_nginx_runtime()
    provenance = {
        "current": _symlink_state(CURRENT_LINK),
        "distro_default": _symlink_state(DISTRO_DEFAULT),
        "source_kind": source_kind,
    }
    return Preflight(candidate, source_kind, previous_v2, provenance)


def _verify_no_extended_acl(path: Path) -> None:
    output = _run(["getfacl", "-cp", "--", str(path)])
    allowed_prefixes = ("user::", "group::", "other::")
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("default:") or stripped.startswith("mask:"):
            raise ActivationError(f"ACL estesa/default non ammessa: {path}")
        if not stripped.startswith(allowed_prefixes):
            raise ActivationError(f"ACL nominativa o output getfacl inatteso: {path}")


def prepare_log_directory(manifest: Mapping[str, Any]) -> None:
    import grp
    import pwd

    logging = manifest["logging"]
    if (
        logging["directory"] != "/var/log/thebitlab"
        or logging["directory_mode"] != "0750"
        or logging["file_mode"] != "0640"
        or logging["owner"] != "www-data"
        or logging["group"] != "adm"
    ):
        raise ActivationError("Contratto ownership/mode Ubuntu logging non canonico")
    directory = Path(logging["directory"])
    owner_id = pwd.getpwnam("root").pw_uid
    directory_group_id = grp.getgrnam("www-data").gr_gid
    file_group_id = grp.getgrnam("adm").gr_gid
    file_owner_id = pwd.getpwnam("www-data").pw_uid
    directory.mkdir(mode=0o750, parents=False, exist_ok=True)
    metadata = directory.lstat()
    if directory.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ActivationError(f"Directory log non regolare: {directory}")
    _verify_no_extended_acl(directory)
    os.chown(directory, owner_id, directory_group_id)
    os.chmod(directory, 0o750)
    _verify_no_extended_acl(directory)

    for raw_path in (manifest["origin"]["access_log"], manifest["origin"]["error_log"]):
        path = Path(raw_path)
        if path.exists() or path.is_symlink():
            metadata = path.lstat()
            if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
                raise ActivationError(f"Log non regolare: {path}")
            _verify_no_extended_acl(path)
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o640)
        except OSError as exc:
            raise ActivationError(f"Log non creabile in sicurezza: {path}") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise ActivationError(f"Log non regolare: {path}")
            os.fchown(descriptor, file_owner_id, file_group_id)
            os.fchmod(descriptor, 0o640)
        finally:
            os.close(descriptor)
        _verify_no_extended_acl(path)
        metadata = path.stat()
        if (
            stat.S_IMODE(metadata.st_mode) != 0o640
            or metadata.st_uid != file_owner_id
            or metadata.st_gid != file_group_id
        ):
            raise ActivationError(f"Metadata log non canonici: {path}")
    metadata = directory.stat()
    if (
        stat.S_IMODE(metadata.st_mode) != 0o750
        or metadata.st_uid != owner_id
        or metadata.st_gid != directory_group_id
    ):
        raise ActivationError("Metadata directory log non canonici")


def _state_security(path: Path, *, require_root_owner: bool) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ActivationError(f"Activation state assente o non accessibile: {path}") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or getattr(metadata, "st_nlink", 1) != 1
    ):
        raise ActivationError("Activation state deve essere un file regolare non-symlink/non-hardlink")
    if os.name != "nt" and stat.S_IMODE(metadata.st_mode) != 0o600:
        raise ActivationError("Activation state deve avere mode 0600")
    if os.name != "nt" and require_root_owner and metadata.st_uid != 0:
        raise ActivationError("Activation state deve essere root-owned")
    return metadata


def _read_state(path: Path, *, require_root_owner: bool = True) -> dict[str, Any]:
    _state_security(path, require_root_owner=require_root_owner)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError("Activation state non valido") from exc
    required = {
        "schema_version",
        "status",
        "candidate_bundle",
        "candidate_lock_digest",
        "previous_v2_bundle",
        "previous_v2_lock_digest",
        "unsafe_provenance",
    }
    if not isinstance(state, dict) or set(state) != required:
        raise ActivationError("Activation state con struttura inattesa")
    if state["schema_version"] != "thebitlab.pilot-activation-state.v3":
        raise ActivationError("Versione activation state non supportata")
    allowed_statuses = {
        "prepared", "switched", "validated", "active",
        "rollback_prepared", "rollback_switched", "rollback_validated", "rolled_back_v2",
    }
    if not isinstance(state["status"], str) or state["status"] not in allowed_statuses:
        raise ActivationError("Activation state status non supportato")
    if (
        not isinstance(state["candidate_bundle"], str)
        or not isinstance(state["candidate_lock_digest"], str)
        or re.fullmatch(r"[0-9a-f]{64}", state["candidate_lock_digest"]) is None
    ):
        raise ActivationError("Activation state candidate non valido")
    if state["previous_v2_bundle"] is not None and not isinstance(state["previous_v2_bundle"], str):
        raise ActivationError("Activation state previous v2 non valido")
    if state["previous_v2_lock_digest"] is not None and (
        not isinstance(state["previous_v2_lock_digest"], str)
        or re.fullmatch(r"[0-9a-f]{64}", state["previous_v2_lock_digest"]) is None
    ):
        raise ActivationError("Activation state digest previous v2 non valido")
    if (state["previous_v2_bundle"] is None) != (state["previous_v2_lock_digest"] is None):
        raise ActivationError("Activation state previous v2 incompleto")
    if not isinstance(state["unsafe_provenance"], dict):
        raise ActivationError("Activation state provenance non valida")
    return state


def _write_state(
    path: Path,
    state: Mapping[str, Any],
    *,
    exclusive: bool,
    require_root_owner: bool = True,
) -> None:
    if path.exists() or path.is_symlink():
        if exclusive:
            raise ActivationError("Activation state già esistente")
        _state_security(path, require_root_owner=require_root_owner)
    parent_existed = path.parent.exists()
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    if not parent_existed:
        _fsync_directory(path.parent.parent)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ActivationError("Directory activation state non sicura")
    parent_meta = path.parent.stat()
    if os.name != "nt" and require_root_owner and parent_meta.st_uid != 0:
        raise ActivationError("Directory activation state non root-owned")
    if os.name != "nt" and parent_meta.st_mode & 0o022:
        raise ActivationError("Directory activation state scrivibile da group/other")
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _state_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _systemctl_result(arguments: Sequence[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["systemctl", *arguments], check=False, capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ActivationError("systemctl non disponibile o non responsivo") from exc
    return result.returncode, result.stdout.strip()


def _systemd_path(name: str) -> tuple[Path, ...]:
    try:
        result = subprocess.run(
            ["systemd-path", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ActivationError(f"Search path systemd non disponibile: {name}") from exc
    value = result.stdout.strip()
    if result.returncode != 0 or not value or "\n" in value:
        raise ActivationError(f"Search path systemd non verificabile: {name}")
    paths: list[Path] = []
    for raw in value.split(":"):
        path = Path(raw)
        if not raw or not path.is_absolute() or path != Path(os.path.abspath(path)):
            raise ActivationError(f"Search path systemd non canonica: {name}")
        if path in paths:
            raise ActivationError(f"Search path systemd duplicata: {path}")
        paths.append(path)
    return tuple(paths)


def _dpkg_path_spellings(path: Path) -> tuple[str, ...]:
    value = path.as_posix()
    spellings = [value]
    if value == "/usr/lib" or value.startswith("/usr/lib/"):
        spellings.append(value.removeprefix("/usr"))
    elif value == "/lib" or value.startswith("/lib/"):
        spellings.append("/usr" + value)
    return tuple(spellings)


def _dpkg_owned_paths(paths: Iterable[Path]) -> frozenset[Path]:
    """Attribute exact filesystem artifacts to currently installed Ubuntu packages."""

    candidates: dict[str, set[Path]] = {}
    for path in paths:
        for spelling in _dpkg_path_spellings(path):
            candidates.setdefault(spelling, set()).add(path)
    owners_by_spelling: dict[str, set[str]] = {}
    search_patterns = {
        "".join("\\" + character if character in "\\*?[" else character for character in spelling)
        for spelling in candidates
    }
    names = sorted(search_patterns)
    for offset in range(0, len(names), 100):
        chunk = names[offset : offset + 100]
        try:
            result = subprocess.run(
                ["dpkg-query", "--search", "--", *chunk],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ActivationError("Attribuzione package systemd non disponibile") from exc
        if result.returncode not in {0, 1}:
            raise ActivationError("Attribuzione package systemd fallita")
        for line in result.stdout.splitlines():
            try:
                packages, spelling = line.rsplit(": ", 1)
            except ValueError as exc:
                raise ActivationError("Output dpkg-query ambiguo") from exc
            if spelling not in candidates:
                continue
            parsed = {item.strip() for item in packages.split(",") if item.strip()}
            if not parsed:
                raise ActivationError("Owner dpkg-query vuoto")
            owners_by_spelling.setdefault(spelling, set()).update(parsed)

    owner_names = sorted(
        {package for packages in owners_by_spelling.values() for package in packages}
    )
    installed: set[str] = set()
    for offset in range(0, len(owner_names), 100):
        chunk = owner_names[offset : offset + 100]
        if not chunk:
            continue
        try:
            result = subprocess.run(
                [
                    "dpkg-query",
                    "--show",
                    "--showformat=${binary:Package}\\t${Status}\\n",
                    *chunk,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ActivationError("Stato package systemd non disponibile") from exc
        if result.returncode != 0:
            raise ActivationError("Stato package systemd non verificabile")
        for line in result.stdout.splitlines():
            fields = line.split("\t")
            if len(fields) != 2:
                raise ActivationError("Output stato package systemd ambiguo")
            package, package_status = fields
            if package_status == "install ok installed":
                installed.add(package)
                installed.add(package.split(":", 1)[0])

    owned: set[Path] = set()
    for spelling, packages in owners_by_spelling.items():
        if any(
            package in installed or package.split(":", 1)[0] in installed
            for package in packages
        ):
            owned.update(candidates[spelling])
    return frozenset(owned)


def _assert_systemd_directory_ancestry(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        _assert_trusted_metadata(current, directory=True, require_root_owner=True)


def _collect_systemd_tree(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    if not root.exists() and not root.is_symlink():
        return (), ()
    _assert_systemd_directory_ancestry(root)
    directories: list[Path] = []
    artifacts: list[Path] = []
    try:
        for current_name, directory_names, file_names in os.walk(root, followlinks=False):
            current = Path(current_name)
            for name in sorted(directory_names):
                path = current / name
                metadata = path.lstat()
                if stat.S_ISLNK(metadata.st_mode):
                    artifacts.append(path)
                    directory_names.remove(name)
                else:
                    _assert_trusted_metadata(
                        path, directory=True, require_root_owner=True
                    )
                    directories.append(path)
            for name in sorted(file_names):
                artifacts.append(current / name)
    except OSError as exc:
        raise ActivationError(f"Inventario systemd non enumerabile: {root}") from exc
    return tuple(sorted(directories)), tuple(sorted(artifacts))


def _systemd_unit_identity(path: Path) -> str | None:
    candidates = (path.name, path.parent.name.removesuffix(".d"))
    for candidate in candidates:
        if any(candidate.endswith(suffix) for suffix in SYSTEMD_UNIT_SUFFIXES):
            return candidate
    return None


def _systemd_enablement_name_matches(link_name: str, target_name: str) -> bool:
    if link_name == target_name:
        return True
    if "@." not in target_name:
        return False
    prefix, suffix = target_name.split("@.", 1)
    return (
        link_name.startswith(prefix + "@")
        and link_name.endswith("." + suffix)
        and len(link_name) > len(prefix) + len(suffix) + 2
    )


def _assert_systemd_symlink_metadata(path: Path) -> str:
    try:
        metadata = path.lstat()
        target = os.readlink(path)
    except OSError as exc:
        raise ActivationError(f"Symlink systemd non verificabile: {path}") from exc
    if (
        not stat.S_ISLNK(metadata.st_mode)
        or (os.name != "nt" and metadata.st_uid != 0)
        or not target
    ):
        raise ActivationError(f"Symlink systemd non root-owned/canonico: {path}")
    return target


def _is_generated_systemd_root(path: Path) -> bool:
    return path.parent == Path("/run/systemd") and path.name in SYSTEMD_GENERATED_DIRECTORY_NAMES


def _attest_systemd_generators() -> None:
    roots = _systemd_path(SYSTEMD_GENERATOR_SEARCH_PATH_NAME)
    directories: list[Path] = []
    artifacts: list[Path] = []
    for root in roots:
        tree_directories, tree_artifacts = _collect_systemd_tree(root)
        directories.extend(tree_directories)
        artifacts.extend(tree_artifacts)
    resolved_targets: dict[Path, Path] = {}
    for path in artifacts:
        if path.is_symlink():
            _assert_systemd_symlink_metadata(path)
            try:
                resolved_targets[path] = path.resolve(strict=True)
            except OSError as exc:
                raise ActivationError(f"Symlink generator systemd broken: {path}") from exc
    package_owned = _dpkg_owned_paths(
        (*directories, *artifacts, *resolved_targets.values())
    )
    unmanaged = [path for path in (*directories, *artifacts) if path not in package_owned]
    if unmanaged:
        raise ActivationError(
            f"Generator systemd locale/unmanaged: {unmanaged[0]}"
        )
    for path in artifacts:
        metadata = path.lstat()
        if path.is_symlink():
            target = resolved_targets[path]
            if target != Path("/dev/null") and target not in package_owned:
                raise ActivationError(
                    f"Symlink generator package con target non attribuito: {path}"
                )
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ActivationError(f"Generator systemd package non regolare: {path}")
        if os.name != "nt" and (metadata.st_uid != 0 or metadata.st_mode & 0o022):
            raise ActivationError(f"Generator systemd package con metadata unsafe: {path}")


def _systemd_command_output(arguments: Sequence[str], *, label: str) -> str:
    code, output = _systemctl_result(arguments)
    if code != 0 or not output:
        raise ActivationError(f"{label} systemd non verificabile")
    return output


def _attest_package_owned_generator_input(path: Path, boundary: Path) -> None:
    _assert_systemd_directory_ancestry(boundary)
    if path.parent != boundary:
        raise ActivationError(f"Input generator fuori dal boundary atteso: {path}")
    _verify_trusted_ancestry(path, boundary)
    if path not in _dpkg_owned_paths((path,)):
        raise ActivationError(f"Input generator non attribuito a package installato: {path}")


def _attest_generated_systemd_artifacts(
    artifacts: Sequence[Path],
    generated_roots: set[Path],
    resolved_targets: Mapping[Path, Path | None],
    package_owned: frozenset[Path],
) -> tuple[frozenset[Path], frozenset[str]]:
    """Trust generated artifacts only from a closed, attested input provenance."""

    generated = tuple(
        path
        for path in artifacts
        if any(path == root or root in path.parents for root in generated_roots)
    )
    trusted_artifacts: set[Path] = set()
    trusted_units: set[str] = set()
    sysv_units: dict[str, Path] = {}

    # systemd-sysv-generator regular units authoritatively expose SourcePath. Attest
    # the exact input before considering the generated identity trusted.
    for path in generated:
        if path in resolved_targets:
            continue
        identity = _systemd_unit_identity(path)
        if identity is None or not identity.endswith(".service"):
            raise ActivationError(f"Output generator regolare senza provenance supportata: {path}")
        fragment_value = _systemd_property("FragmentPath", identity)
        fragment = _canonical_path(
            fragment_value, label=f"{identity} FragmentPath"
        )
        if fragment_value != path.as_posix() or fragment != path:
            raise ActivationError(f"Fragment generated ambiguo per {identity}")
        source_value = _systemd_property("SourcePath", identity)
        source = _canonical_path(source_value, label=f"{identity} SourcePath")
        if source_value != source.as_posix() or source.parent != SYSV_INIT_ROOT:
            raise ActivationError(f"SourcePath SysV non canonico per {identity}")
        _attest_package_owned_generator_input(source, SYSV_INIT_ROOT)
        if identity in sysv_units:
            raise ActivationError(f"Output SysV generated duplicato: {identity}")
        sysv_units[identity] = path
        trusted_artifacts.add(path)
        trusted_units.add(identity)

    for path in generated:
        if path not in resolved_targets:
            continue
        target = resolved_targets[path]
        identity = _systemd_unit_identity(path)
        if target is None or identity is None:
            raise ActivationError(f"Symlink generator senza identity/provenance: {path}")
        containing_roots = [
            root for root in generated_roots if path == root or root in path.parents
        ]
        if len(containing_roots) != 1:
            raise ActivationError(f"Output generator con root ambigua: {path}")
        root = containing_roots[0]
        relative_key = (root.name, *path.relative_to(root).parts)

        generated_target = sysv_units.get(identity)
        if (
            generated_target is not None
            and target == generated_target
            and path.parent.name.endswith(SYSTEMD_ENABLEMENT_DIRECTORY_SUFFIXES)
            and _systemd_enablement_name_matches(path.name, generated_target.name)
        ):
            trusted_artifacts.add(path)
            continue

        if relative_key == ("generator", "multi-user.target.wants", "rc-local.service"):
            expected = Path("/usr/lib/systemd/system/rc-local.service").resolve(strict=True)
            if target != expected or target not in package_owned:
                raise ActivationError("Output rc-local generator non canonico")
            _attest_package_owned_generator_input(RC_LOCAL_PATH, Path("/etc"))
            trusted_artifacts.add(path)
            trusted_units.add(identity)
            continue

        expected_target = GENERATED_PACKAGE_UNIT_LINKS.get(relative_key)
        if expected_target is None:
            raise ActivationError(f"Output generator senza provenance chiusa: {path}")
        expected = expected_target.resolve(strict=True)
        if target != expected or target not in package_owned:
            raise ActivationError(f"Output generator package target divergente: {path}")
        trusted_artifacts.add(path)
        trusted_units.add(identity)

    return frozenset(trusted_artifacts), frozenset(trusted_units)


def _attest_systemd_boot_surface() -> None:
    """Fail closed on every non-package/local artifact in the boot unit surface."""

    code, _ = _systemctl_result(["daemon-reload"])
    if code != 0:
        raise ActivationError("systemd daemon-reload fallita durante boot attestation")
    _attest_systemd_generators()
    roots = _systemd_path(SYSTEMD_UNIT_SEARCH_PATH_NAME)
    directories: list[Path] = []
    artifacts: list[Path] = []
    generated_roots = {root for root in roots if _is_generated_systemd_root(root)}
    for root in roots:
        tree_directories, tree_artifacts = _collect_systemd_tree(root)
        directories.extend(tree_directories)
        artifacts.extend(tree_artifacts)

    resolved_targets: dict[Path, Path | None] = {}
    for path in artifacts:
        metadata = path.lstat()
        if os.name != "nt" and metadata.st_uid != 0:
            raise ActivationError(f"Artifact systemd non root-owned: {path}")
        if stat.S_ISLNK(metadata.st_mode):
            _assert_systemd_symlink_metadata(path)
            try:
                resolved_targets[path] = path.resolve(strict=True)
            except OSError as exc:
                raise ActivationError(f"Symlink systemd broken/non risolvibile: {path}") from exc
        elif stat.S_ISREG(metadata.st_mode):
            if (
                (os.name != "nt" and metadata.st_mode & 0o022)
                or getattr(metadata, "st_nlink", 1) != 1
            ):
                raise ActivationError(f"Artifact systemd con metadata unsafe: {path}")
        else:
            raise ActivationError(f"Tipo artifact systemd non ammesso: {path}")

    package_candidates = [*directories, *artifacts]
    package_candidates.extend(
        target for target in resolved_targets.values() if target is not None
    )
    package_owned = _dpkg_owned_paths(package_candidates)
    trusted_generated_artifacts, trusted_generated_units = (
        _attest_generated_systemd_artifacts(
            artifacts, generated_roots, resolved_targets, package_owned
        )
    )
    unit_files = _systemd_command_output(
        ["list-unit-files", "--all", "--no-legend", "--no-pager", "--plain"],
        label="Inventario unit-file",
    )
    unit_file_states: dict[str, str] = {}
    for line in unit_files.splitlines():
        fields = line.split()
        if len(fields) not in {2, 3}:
            raise ActivationError("Output list-unit-files ambiguo")
        unit_name, unit_state = fields[:2]
        if unit_name in unit_file_states:
            raise ActivationError(f"Unit file duplicata nell'inventario: {unit_name}")
        unit_file_states[unit_name] = unit_state
    trusted_units: set[str] = set(trusted_generated_units)

    for directory in directories:
        if any(directory == root or root in directory.parents for root in generated_roots):
            continue
        if directory in package_owned:
            continue
        if directory.name.endswith(SYSTEMD_ENABLEMENT_DIRECTORY_SUFFIXES):
            continue
        raise ActivationError(f"Directory systemd locale/unmanaged: {directory}")

    for path in artifacts:
        identity = _systemd_unit_identity(path)
        generated = any(path == root or root in path.parents for root in generated_roots)
        if generated:
            if path not in trusted_generated_artifacts:
                raise ActivationError(f"Output generator non attestato: {path}")
            continue
        if path in package_owned:
            target = resolved_targets.get(path)
            if target is not None and target != Path("/dev/null") and target not in package_owned:
                raise ActivationError(f"Symlink package systemd con target non attribuito: {path}")
            if identity is not None:
                trusted_units.add(identity)
            continue
        if path == SYSTEMD_LINK:
            target = _assert_systemd_symlink_metadata(path)
            if target != INTEGRATION_LINKS[SYSTEMD_LINK]:
                raise ActivationError("Unit locale TheBitLab con target inatteso")
            try:
                resolved = path.resolve(strict=True)
            except OSError as exc:
                raise ActivationError("Unit locale TheBitLab non risolvibile") from exc
            _verify_trusted_ancestry(resolved, DEPLOYMENTS_ROOT)
            bundle_root = resolved.parent.parent
            try:
                verify_bundle(bundle_root)
            except (ActivationError, deployment.DeploymentValidationError):
                verify_legacy_v1_bundle(bundle_root)
            trusted_units.add("thebitlab.service")
            continue
        if path == NGINX_MIGRATION_GUARD:
            if _assert_systemd_symlink_metadata(path) != "/dev/null":
                raise ActivationError("Migration guard systemd inatteso")
            trusted_units.add("nginx.service")
            continue
        if path not in resolved_targets:
            raise ActivationError(f"Artifact systemd locale/unmanaged: {path}")
        target = resolved_targets[path]
        if target is None:
            raise ActivationError(f"Enablement/link systemd broken: {path}")
        if path == THEBITLAB_WANTS_LINK:
            try:
                expected = SYSTEMD_LINK.resolve(strict=True)
            except OSError as exc:
                raise ActivationError("Enablement TheBitLab senza unit canonica") from exc
            if target != expected or path.name != "thebitlab.service":
                raise ActivationError("Enablement TheBitLab non canonico")
            trusted_units.add(path.name)
            continue
        package_enablement = (
            target in package_owned
            and _systemd_enablement_name_matches(path.name, target.name)
            and (
                path.parent.name.endswith(SYSTEMD_ENABLEMENT_DIRECTORY_SUFFIXES)
                or path.parent in roots
            )
        )
        package_default = (
            target in package_owned
            and path.name == "default.target"
            and path.parent in roots
        )
        package_alias = (
            target in package_owned
            and path.parent in roots
            and unit_file_states.get(path.name) == "alias"
        )
        if not (package_enablement or package_default or package_alias):
            raise ActivationError(f"Enablement systemd verso target non package: {path}")
        trusted_units.add(path.name)

    enabled_units = {
        unit_name
        for unit_name, unit_state in unit_file_states.items()
        if unit_state in SYSTEMD_ENABLED_STATES
    }
    untrusted_enabled = sorted(enabled_units - trusted_units)
    if untrusted_enabled:
        raise ActivationError(
            f"Unit enabled/linked non attribuita: {untrusted_enabled[0]}"
        )

    default_target = _systemd_command_output(["get-default"], label="Default target")
    if "\n" in default_target or default_target not in trusted_units:
        raise ActivationError("Default target systemd non attribuito")
    dependencies = _systemd_command_output(
        [
            "list-dependencies",
            "--all",
            "--plain",
            "--no-pager",
            default_target,
        ],
        label="Boot dependency graph",
    )
    for line in dependencies.splitlines():
        fields = line.split()
        if not fields:
            continue
        unit_name = fields[-1]
        if unit_name in trusted_units or any(
            _systemd_enablement_name_matches(unit_name, trusted)
            for trusted in trusted_units
        ):
            continue
        if unit_name.endswith((".automount", ".device", ".mount", ".scope", ".slice", ".swap")):
            continue
        if _systemd_property("LoadState", unit_name) == "not-found":
            # A package target may name an optional unit (for example display-manager.service).
            # With no artifact in the closed inventory it cannot activate local code.
            continue
        raise ActivationError(f"Unit boot-reachable non attribuita: {unit_name}")


def _nginx_service_state() -> tuple[str, int]:
    code, output = _systemctl_result(["is-active", "nginx.service"])
    if "\n" in output or not output:
        raise ActivationError("Stato systemd nginx ambiguo")
    return output, code


def _require_nginx_not_running() -> None:
    state, code = _nginx_service_state()
    if code != 3 or state not in {"inactive", "failed"}:
        raise ActivationError(f"nginx.service attiva o in transizione: {state}")


def _stop_nginx_service() -> None:
    code, _ = _systemctl_result(["stop", "nginx.service"])
    if code != 0:
        raise ActivationError("Arresto nginx.service fallito")
    _require_nginx_not_running()


def _systemd_property(
    name: str, unit: str = "nginx.service", *, allow_empty: bool = False
) -> str:
    code, value = _systemctl_result(["show", f"--property={name}", "--value", unit])
    if code != 0 or "\n" in value or (not allow_empty and not value):
        raise ActivationError(f"Proprietà systemd non verificabile: {unit} {name}")
    return value


def _canonical_path(value: str, *, label: str) -> Path:
    try:
        path = Path(value)
        if not path.is_absolute():
            raise OSError("path non assoluto")
        return path.resolve(strict=True)
    except OSError as exc:
        raise ActivationError(f"Path systemd {label} non canonico: {value}") from exc


def _parse_systemd_exec(value: str, *, name: str) -> tuple[tuple[Path, tuple[str, ...], bool], ...]:
    """Parse systemd's normalized Exec* records and preserve their security semantics."""

    record = re.compile(
        r"\{\s*path=(?P<path>\S+)\s*;\s*argv\[\]=(?P<argv>.*?)"
        r"\s*;\s*ignore_errors=(?P<ignore>yes|no)\s*;.*?\}"
    )
    parsed: list[tuple[Path, tuple[str, ...], bool]] = []
    cursor = 0
    for match in record.finditer(value):
        if value[cursor : match.start()].strip():
            raise ActivationError(f"{name} systemd non interpretabile")
        try:
            arguments = tuple(shlex.split(match.group("argv"), posix=True))
        except ValueError as exc:
            raise ActivationError(f"{name} systemd non interpretabile") from exc
        if not arguments:
            raise ActivationError(f"{name} systemd senza argv")
        executable = _canonical_path(match.group("path"), label=name)
        argv0 = _canonical_path(arguments[0], label=f"{name} argv[0]")
        if executable != argv0:
            raise ActivationError(f"{name} systemd con executable/argv[0] divergenti")
        parsed.append((executable, arguments[1:], match.group("ignore") == "yes"))
        cursor = match.end()
    if not parsed or value[cursor:].strip():
        raise ActivationError(f"{name} systemd non interpretabile")
    return tuple(parsed)


def _expected_exec(
    executable: str, arguments: str, *, ignore_errors: bool = False
) -> tuple[Path, tuple[str, ...], bool]:
    return (
        _canonical_path(executable, label="contratto Exec"),
        tuple(shlex.split(arguments, posix=True)),
        ignore_errors,
    )


def _attest_effective_nginx_unit(
    *,
    expect_running: bool | None,
    allowed_unit_file_states: frozenset[str] = ENABLED_NGINX_UNIT_FILE_STATES,
) -> EffectiveNginxUnit:
    """Attest the effective Ubuntu 24.04 package unit loaded by systemd."""

    if (
        not allowed_unit_file_states
        or not allowed_unit_file_states <= PREFLIGHT_NGINX_UNIT_FILE_STATES
    ):
        raise ActivationError("Allowlist UnitFileState nginx attesa non supportata")
    scalar_contract = {
        "Id": "nginx.service",
        "LoadState": "loaded",
        "Type": "forking",
        "PIDFile": "/run/nginx.pid",
        "User": "",
        "Group": "",
        "SourcePath": "",
        "DropInPaths": "",
        "KillMode": "mixed",
    }
    for name, expected in scalar_contract.items():
        actual = _systemd_property(name, allow_empty=expected == "")
        if actual != expected:
            raise ActivationError(
                f"Contratto systemd nginx divergente: {name}={actual!r}, atteso {expected!r}"
            )
    unit_file_state = _systemd_property("UnitFileState")
    if unit_file_state not in allowed_unit_file_states:
        raise ActivationError(
            "Contratto systemd nginx divergente: "
            f"UnitFileState={unit_file_state!r}, atteso uno di "
            f"{sorted(allowed_unit_file_states)!r}"
        )
    names = set(_systemd_property("Names").split())
    if names != {"nginx.service"}:
        raise ActivationError(f"Alias systemd nginx inatteso: {sorted(names)}")
    fragment = _canonical_path(_systemd_property("FragmentPath"), label="FragmentPath")
    try:
        expected_fragment = NGINX_PACKAGE_UNIT.resolve(strict=True)
    except OSError as exc:
        raise ActivationError("Unit package nginx non risolvibile") from exc
    if fragment != expected_fragment:
        raise ActivationError(
            f"FragmentPath nginx non package: {fragment} (atteso {expected_fragment})"
        )

    expected_commands = {
        "ExecStartPre": (
            _expected_exec(
                "/usr/sbin/nginx", "-t -q -g daemon 'on;' master_process 'on;'"
            ),
        ),
        "ExecStart": (
            _expected_exec("/usr/sbin/nginx", "-g daemon 'on;' master_process 'on;'"),
        ),
        "ExecReload": (
            _expected_exec(
                "/usr/sbin/nginx", "-g daemon 'on;' master_process 'on;' -s reload"
            ),
        ),
        "ExecStop": (
            _expected_exec(
                "/sbin/start-stop-daemon",
                "--quiet --stop --retry QUIT/5 --pidfile /run/nginx.pid",
                ignore_errors=True,
            ),
        ),
    }
    for name, expected in expected_commands.items():
        actual = _parse_systemd_exec(_systemd_property(name), name=name)
        if actual != expected:
            raise ActivationError(f"Contratto systemd nginx divergente: {name}")

    raw_main_pid = _systemd_property("MainPID")
    control_group = _systemd_property("ControlGroup", allow_empty=True)
    if not raw_main_pid.isdecimal():
        raise ActivationError("MainPID nginx.service non canonico")
    main_pid = int(raw_main_pid)
    if expect_running is True:
        if main_pid <= 0 or control_group != NGINX_CONTROL_GROUP:
            raise ActivationError("MainPID/ControlGroup nginx.service non attestati dopo start")
    elif expect_running is False:
        if main_pid != 0 or control_group:
            raise ActivationError("nginx.service conserva MainPID/ControlGroup inattesi")
    elif (main_pid == 0) != (control_group == ""):
        raise ActivationError("MainPID/ControlGroup nginx.service incoerenti")
    return EffectiveNginxUnit(main_pid, control_group)


def _read_process_control_groups(pid: int) -> frozenset[str]:
    try:
        lines = (PROC_ROOT / str(pid) / "cgroup").read_text(encoding="ascii").splitlines()
    except OSError as exc:
        if exc.errno in {errno.ENOENT, errno.ESRCH}:
            return frozenset()
        raise ActivationError(f"Cgroup processo {pid} non verificabile") from exc
    groups: set[str] = set()
    for line in lines:
        fields = line.split(":", 2)
        if len(fields) != 3 or not fields[2].startswith("/"):
            raise ActivationError(f"Cgroup processo {pid} non canonico")
        groups.add(fields[2])
    if not groups:
        raise ActivationError(f"Cgroup processo {pid} assente")
    return frozenset(groups)


def _process_in_control_group(process: NginxProcess, control_group: str) -> bool:
    prefix = control_group.rstrip("/") + "/"
    return any(group == control_group or group.startswith(prefix) for group in process.control_groups)


def _nginx_processes() -> tuple[NginxProcess, ...]:
    """Find package nginx processes by /proc executable inode, never PID file/name/argv."""

    try:
        binary = NGINX_BINARY.stat()
        canonical_binary = NGINX_BINARY.resolve(strict=True)
        entries = tuple(PROC_ROOT.iterdir())
    except OSError as exc:
        raise ActivationError("Enumerazione processi nginx non disponibile") from exc
    identity = (binary.st_dev, binary.st_ino)
    canonical_spellings = {str(NGINX_BINARY), str(canonical_binary)}
    found: list[NginxProcess] = []
    for entry in entries:
        if not entry.name.isdecimal():
            continue
        pid = int(entry.name)
        try:
            executable_link = entry / "exe"
            executable = executable_link.stat()
            executable_name = os.readlink(executable_link)
        except OSError as exc:
            if exc.errno in {errno.ENOENT, errno.ESRCH}:
                continue
            raise ActivationError(f"Executable processo {pid} non verificabile") from exc
        lexical_name = executable_name.removesuffix(" (deleted)")
        if (
            (executable.st_dev, executable.st_ino) != identity
            and lexical_name not in canonical_spellings
        ):
            continue
        groups = _read_process_control_groups(pid)
        if groups:
            found.append(NginxProcess(pid, groups))
    return tuple(sorted(found, key=lambda process: process.pid))


def _listener_inodes() -> dict[int, set[str]]:
    listeners = {port: set() for port in CANONICAL_NGINX_PORTS}
    for name in ("tcp", "tcp6"):
        try:
            lines = (PROC_ROOT / "net" / name).read_text(encoding="ascii").splitlines()[1:]
        except OSError as exc:
            raise ActivationError(f"Socket table {name} non verificabile") from exc
        for line in lines:
            fields = line.split()
            if len(fields) < 10:
                raise ActivationError(f"Socket table {name} non canonica")
            try:
                port = int(fields[1].rsplit(":", 1)[1], 16)
            except (IndexError, ValueError) as exc:
                raise ActivationError(f"Socket table {name} non canonica") from exc
            if fields[3] == "0A" and port in listeners:
                inode = fields[9]
                if not inode.isdecimal():
                    raise ActivationError(f"Socket inode {name} non canonico")
                listeners[port].add(inode)
    return listeners


def _canonical_listener_owners() -> dict[int, frozenset[int]]:
    """Attribute canonical listeners through proc socket inodes; fail on unattributed sockets."""

    for _attempt in range(2):
        listeners = _listener_inodes()
        targets = set().union(*listeners.values())
        if not targets:
            return {port: frozenset() for port in listeners}
        owners = {inode: set() for inode in targets}
        try:
            processes = tuple(PROC_ROOT.iterdir())
        except OSError as exc:
            raise ActivationError("Enumerazione owner socket non disponibile") from exc
        for process in processes:
            if not process.name.isdecimal():
                continue
            try:
                descriptors = tuple((process / "fd").iterdir())
            except OSError as exc:
                if exc.errno in {errno.ENOENT, errno.ESRCH}:
                    continue
                raise ActivationError(f"FD processo {process.name} non verificabili") from exc
            for descriptor in descriptors:
                try:
                    target = os.readlink(descriptor)
                except OSError as exc:
                    if exc.errno in {errno.ENOENT, errno.ESRCH}:
                        continue
                    raise ActivationError(f"FD processo {process.name} non verificabile") from exc
                if target.startswith("socket:[") and target.endswith("]"):
                    inode = target[8:-1]
                    if inode in owners:
                        owners[inode].add(int(process.name))
        missing = {inode for inode, pids in owners.items() if not pids}
        if not missing:
            return {
                port: frozenset(pid for inode in inodes for pid in owners[inode])
                for port, inodes in listeners.items()
            }
        current = set().union(*_listener_inodes().values())
        if not (missing & current):
            continue
        if _attempt == 1:
            raise ActivationError("Listener canonico senza owner process-level attestabile")
    raise ActivationError("Listener canonici instabili durante attestazione")


def _assert_zero_nginx_processes() -> None:
    processes = _nginx_processes()
    if processes:
        raise ActivationError(
            "Processo nginx unmanaged presente durante guard: "
            + ",".join(str(process.pid) for process in processes)
        )


def _assert_no_canonical_listeners() -> None:
    owners = _canonical_listener_owners()
    occupied = {port: sorted(pids) for port, pids in owners.items() if pids}
    if occupied:
        raise ActivationError(f"Listener 80/443 estraneo presente: {occupied}")


def _attest_nginx_service_runtime(
    unit: EffectiveNginxUnit | None = None,
) -> None:
    if _nginx_service_state() != ("active", 0):
        raise ActivationError("nginx.service non attiva durante runtime attestation")
    effective = unit or _attest_effective_nginx_unit(expect_running=True)
    processes = _nginx_processes()
    if not processes or effective.main_pid not in {process.pid for process in processes}:
        raise ActivationError("MainPID nginx.service non identifica il master nginx package")
    if any(
        not _process_in_control_group(process, effective.control_group)
        for process in processes
    ):
        raise ActivationError("Processo nginx fuori dal ControlGroup nginx.service")
    listeners = _canonical_listener_owners()
    if set(listeners) != CANONICAL_NGINX_PORTS or any(not pids for pids in listeners.values()):
        raise ActivationError("Listener nginx canonici 80/443 incompleti")
    for pids in listeners.values():
        for pid in pids:
            process = NginxProcess(pid, _read_process_control_groups(pid))
            if not process.control_groups or not _process_in_control_group(
                process, effective.control_group
            ):
                raise ActivationError("Listener canonico fuori dal ControlGroup nginx.service")


def _logrotate_paths() -> tuple[Path, Path]:
    import grp
    import pwd

    info = verify_bundle(_current_bundle_path())
    log_directory = Path("/var/log/thebitlab")
    try:
        directory_metadata = log_directory.lstat()
    except OSError as exc:
        raise ActivationError("Directory logrotate non verificabile") from exc
    if (
        log_directory.is_symlink()
        or not stat.S_ISDIR(directory_metadata.st_mode)
        or directory_metadata.st_uid != pwd.getpwnam("root").pw_uid
        or directory_metadata.st_gid != grp.getgrnam("www-data").gr_gid
        or stat.S_IMODE(directory_metadata.st_mode) != 0o750
    ):
        raise ActivationError("Directory logrotate con metadata non canonici")
    _verify_no_extended_acl(log_directory)
    paths = tuple(
        Path(info.manifest["origin"][name]) for name in ("access_log", "error_log")
    )
    if (
        len(set(paths)) != 2
        or any(
            not path.is_absolute()
            or path.parent != Path("/var/log/thebitlab")
            or path.suffix != ".log"
            for path in paths
        )
    ):
        raise ActivationError("Path logrotate fuori dal contratto pilot")
    return paths[0], paths[1]


def _log_inode(path: Path) -> LogInode:
    import grp
    import pwd

    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ActivationError(f"Log rotation path non verificabile: {path}") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or getattr(metadata, "st_nlink", 1) != 1
        or stat.S_IMODE(metadata.st_mode) != 0o640
        or metadata.st_uid != pwd.getpwnam("www-data").pw_uid
        or metadata.st_gid != grp.getgrnam("adm").gr_gid
    ):
        raise ActivationError(f"Log rotation path non regolare/canonico: {path}")
    return LogInode(path, metadata.st_dev, metadata.st_ino)


def _boot_id() -> str:
    try:
        value = BOOT_ID_PATH.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise ActivationError("Boot ID non verificabile per logrotate") from exc
    if re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", value) is None:
        raise ActivationError("Boot ID non canonico per logrotate")
    return value


def _ensure_logrotate_runtime_directory() -> None:
    if not LOGROTATE_RUNTIME_ROOT.exists():
        LOGROTATE_RUNTIME_ROOT.mkdir(mode=0o755, parents=False)
        _fsync_directory(LOGROTATE_RUNTIME_ROOT.parent)
    _assert_trusted_metadata(
        LOGROTATE_RUNTIME_ROOT, directory=True, require_root_owner=True
    )
    root_metadata = LOGROTATE_RUNTIME_ROOT.stat()
    if stat.S_IMODE(root_metadata.st_mode) != 0o755:
        raise ActivationError("Runtime root logrotate deve avere mode 0755")
    if not LOGROTATE_RUNTIME_DIRECTORY.exists():
        LOGROTATE_RUNTIME_DIRECTORY.mkdir(mode=0o700, parents=False)
        _fsync_directory(LOGROTATE_RUNTIME_ROOT)
    _assert_trusted_metadata(
        LOGROTATE_RUNTIME_DIRECTORY, directory=True, require_root_owner=True
    )
    if stat.S_IMODE(LOGROTATE_RUNTIME_DIRECTORY.stat().st_mode) != 0o700:
        raise ActivationError("Directory snapshot logrotate deve avere mode 0700")


def _logrotate_snapshot_security(path: Path = LOGROTATE_SNAPSHOT) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ActivationError("Snapshot logrotate assente o non accessibile") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != 0
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or getattr(metadata, "st_nlink", 1) != 1
        or metadata.st_size > 4096
    ):
        raise ActivationError("Snapshot logrotate con metadata unsafe")
    return metadata


def _write_logrotate_snapshot(payload: Mapping[str, Any]) -> None:
    _ensure_logrotate_runtime_directory()
    if LOGROTATE_SNAPSHOT.exists() or LOGROTATE_SNAPSHOT.is_symlink():
        _logrotate_snapshot_security()
    temporary = LOGROTATE_RUNTIME_DIRECTORY / f".reopen.{os.getpid()}"
    descriptor = -1
    try:
        temporary.unlink(missing_ok=True)
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, LOGROTATE_SNAPSHOT)
        _fsync_directory(LOGROTATE_RUNTIME_DIRECTORY)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def logrotate_snapshot() -> None:
    """Persist only pre-rotation inode identity in a root-owned transient record."""

    logs = tuple(_log_inode(path) for path in _logrotate_paths())
    payload = {
        "schema_version": "thebitlab.logrotate-reopen.v1",
        "boot_id": _boot_id(),
        "created_unix_ns": time.time_ns(),
        "logs": [
            {"path": str(item.path), "st_dev": item.device, "st_ino": item.inode}
            for item in logs
        ],
    }
    _write_logrotate_snapshot(payload)


def _read_logrotate_snapshot() -> tuple[LogInode, ...]:
    _ensure_logrotate_runtime_directory()
    _logrotate_snapshot_security()
    try:
        payload = json.loads(LOGROTATE_SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError("Snapshot logrotate corrotto") from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "boot_id", "created_unix_ns", "logs"
    }:
        raise ActivationError("Schema snapshot logrotate inatteso")
    if (
        payload["schema_version"] != "thebitlab.logrotate-reopen.v1"
        or payload["boot_id"] != _boot_id()
        or not isinstance(payload["created_unix_ns"], int)
    ):
        raise ActivationError("Snapshot logrotate stale o non supportato")
    age_ns = time.time_ns() - payload["created_unix_ns"]
    if age_ns < 0 or age_ns > LOGROTATE_SNAPSHOT_MAX_AGE_SECONDS * 1_000_000_000:
        raise ActivationError("Snapshot logrotate stale")
    raw_logs = payload["logs"]
    expected_paths = _logrotate_paths()
    if not isinstance(raw_logs, list) or len(raw_logs) != 2:
        raise ActivationError("Snapshot logrotate senza due log canonici")
    logs: list[LogInode] = []
    for index, raw in enumerate(raw_logs):
        if not isinstance(raw, dict) or set(raw) != {"path", "st_dev", "st_ino"}:
            raise ActivationError("Record inode logrotate inatteso")
        if (
            raw["path"] != str(expected_paths[index])
            or not isinstance(raw["st_dev"], int)
            or not isinstance(raw["st_ino"], int)
            or raw["st_dev"] < 0
            or raw["st_ino"] <= 0
        ):
            raise ActivationError("Record inode logrotate non canonico")
        logs.append(LogInode(expected_paths[index], raw["st_dev"], raw["st_ino"]))
    return tuple(logs)


def _nginx_open_log_inodes(
    processes: Sequence[NginxProcess], watched: frozenset[tuple[int, int]]
) -> dict[tuple[int, int], int]:
    counts = {identity: 0 for identity in watched}
    for process in processes:
        directory = PROC_ROOT / str(process.pid) / "fd"
        try:
            descriptors = tuple(directory.iterdir())
        except OSError as exc:
            raise ActivationError(f"FD nginx {process.pid} non enumerabili") from exc
        for descriptor in descriptors:
            try:
                metadata = descriptor.stat()
            except OSError as exc:
                raise ActivationError(
                    f"FD nginx {process.pid} instabile/non verificabile"
                ) from exc
            identity = (metadata.st_dev, metadata.st_ino)
            if identity in counts:
                counts[identity] += 1
    return counts


def _attest_logrotate_active_unit(
    expected: EffectiveNginxUnit | None = None,
) -> tuple[EffectiveNginxUnit, tuple[NginxProcess, ...]]:
    if _nginx_service_state() != ("active", 0):
        raise ActivationError("nginx.service ha cambiato stato durante reopen")
    unit = _attest_effective_nginx_unit(expect_running=True)
    if expected is not None and unit != expected:
        raise ActivationError("MainPID/cgroup nginx cambiati durante reopen")
    _attest_nginx_service_runtime(unit)
    processes = _nginx_processes()
    if not processes or any(
        not _process_in_control_group(process, unit.control_group)
        for process in processes
    ):
        raise ActivationError("Process topology nginx ambigua durante reopen")
    return unit, processes


def logrotate_reopen() -> None:
    """Signal canonical nginx and prove old-to-current FD/inode transition."""

    previous = _read_logrotate_snapshot()
    current = tuple(_log_inode(item.path) for item in previous)
    rotated = tuple(
        (old, new)
        for old, new in zip(previous, current, strict=True)
        if (old.device, old.inode) != (new.device, new.inode)
    )
    if not rotated:
        raise ActivationError("Postrotate invocato senza inode ruotati")

    state, code = _nginx_service_state()
    if (state, code) == ("inactive", 3):
        _attest_effective_nginx_unit(expect_running=False)
        _assert_zero_nginx_processes()
        LOGROTATE_SNAPSHOT.unlink()
        _fsync_directory(LOGROTATE_RUNTIME_DIRECTORY)
        return
    if (state, code) != ("active", 0):
        raise ActivationError(f"Stato nginx ambiguo durante logrotate: {state}")

    unit, _ = _attest_logrotate_active_unit()
    kill_code, _ = _systemctl_result(
        ["kill", "--kill-whom=main", "--signal=USR1", "nginx.service"]
    )
    if kill_code != 0:
        raise ActivationError("USR1 nginx tramite systemd fallita")
    watched = frozenset(
        (item.device, item.inode) for pair in rotated for item in pair
    )
    deadline = time.monotonic() + LOGROTATE_REOPEN_TIMEOUT_SECONDS
    while True:
        _observed_unit, processes = _attest_logrotate_active_unit(unit)
        if any(_log_inode(item.path) != item for item in current):
            raise ActivationError("Current log path sostituito durante reopen")
        counts = _nginx_open_log_inodes(processes, watched)
        _confirmed_unit, confirmed_processes = _attest_logrotate_active_unit(unit)
        if tuple(process.pid for process in processes) != tuple(
            process.pid for process in confirmed_processes
        ):
            raise ActivationError("Process set nginx cambiato durante scansione FD")
        confirmed_counts = _nginx_open_log_inodes(confirmed_processes, watched)
        _final_unit, final_processes = _attest_logrotate_active_unit(unit)
        if tuple(process.pid for process in confirmed_processes) != tuple(
            process.pid for process in final_processes
        ):
            raise ActivationError("Process set nginx cambiato dopo scansione FD")
        if all(
            counts[(old.device, old.inode)] == 0
            and counts[(new.device, new.inode)] >= 1
            and confirmed_counts[(old.device, old.inode)] == 0
            and confirmed_counts[(new.device, new.inode)] >= 1
            for old, new in rotated
        ):
            LOGROTATE_SNAPSHOT.unlink()
            _fsync_directory(LOGROTATE_RUNTIME_DIRECTORY)
            return
        if time.monotonic() >= deadline:
            raise ActivationError("Timeout reopen nginx: transizione FD/inode non provata")
        time.sleep(LOGROTATE_REOPEN_POLL_SECONDS)


def _attest_preflight_nginx_runtime() -> None:
    state, code = _nginx_service_state()
    if (state, code) == ("active", 0):
        _attest_nginx_service_runtime(
            _attest_effective_nginx_unit(
                expect_running=True,
                allowed_unit_file_states=PREFLIGHT_NGINX_UNIT_FILE_STATES,
            )
        )
        return
    if code == 3 and state in {"inactive", "failed"}:
        _attest_effective_nginx_unit(
            expect_running=False,
            allowed_unit_file_states=PREFLIGHT_NGINX_UNIT_FILE_STATES,
        )
        _assert_zero_nginx_processes()
        _assert_no_canonical_listeners()
        return
    raise ActivationError(f"nginx.service in stato preflight ambiguo: {state}")


def _disable_nginx_autostart_link() -> None:
    """Remove only the canonical package wants link while a manager mask is effective."""

    state = _symlink_state(NGINX_WANTS_LINK)
    if state["present"]:
        target = state["target"]
        if not isinstance(target, str) or not target.startswith("/"):
            raise ActivationError("Enablement nginx.service non canonico")
        _assert_root_symlink(NGINX_WANTS_LINK, target)
        try:
            if Path(target).resolve(strict=True) != NGINX_PACKAGE_UNIT.resolve(strict=True):
                raise ActivationError("Enablement nginx.service fuori dal package unit")
        except OSError as exc:
            raise ActivationError("Enablement nginx.service non risolvibile") from exc
        NGINX_WANTS_LINK.unlink()
        _fsync_directory(NGINX_WANTS_LINK.parent)
    elif NGINX_WANTS_LINK.exists():
        raise ActivationError("Enablement nginx.service non-symlink")


def _verify_migration_guard() -> None:
    """Prove the effective manager mask, zero nginx, and negative starts."""

    _assert_root_symlink(NGINX_MIGRATION_GUARD, "/dev/null")
    if _systemd_property("Id") != "nginx.service":
        raise ActivationError("Id systemd nginx inatteso durante guard")
    if _systemd_property("LoadState") != "masked":
        raise ActivationError("nginx.service non risulta masked al service manager")
    if _systemd_property("UnitFileState") != "masked":
        raise ActivationError("Mask persistente nginx.service non verificata")
    names = set(_systemd_property("Names").split())
    if names != {"nginx.service"}:
        raise ActivationError(f"Alias systemd nginx inatteso: {sorted(names)}")
    _require_nginx_not_running()
    for unit_name in ("nginx.service", "nginx"):
        code, _ = _systemctl_result(["start", unit_name])
        if code == 0:
            _stop_nginx_service()
            raise ActivationError(f"Migration guard bypassabile tramite start {unit_name}")
        _require_nginx_not_running()
    _assert_zero_nginx_processes()
    _assert_no_canonical_listeners()


def _install_migration_guard() -> None:
    """Acquire the guard through systemd; return only after its process-level proof."""

    existing = _symlink_state(NGINX_MIGRATION_GUARD)
    if existing["present"]:
        _assert_root_symlink(NGINX_MIGRATION_GUARD, "/dev/null")
        # Recovery may see a durable mask that the rebooted/cached manager has not loaded.
        code, _ = _systemctl_result(["daemon-reload"])
        if code != 0:
            raise ActivationError("systemd non ha ricaricato il guard persistente")
    else:
        # Disable before masking, while systemd can still read the package [Install] section.
        code, _ = _systemctl_result(["disable", "nginx.service"])
        if code != 0:
            raise ActivationError("Disabilitazione preventiva nginx.service fallita")
        code, unit_state = _systemctl_result(["is-enabled", "nginx.service"])
        if code == 0 or unit_state != "disabled":
            raise ActivationError("nginx.service non risulta disabled prima del guard")
        if NGINX_WANTS_LINK.parent.is_dir() and not NGINX_WANTS_LINK.parent.is_symlink():
            _fsync_directory(NGINX_WANTS_LINK.parent)
        _fault("after_pre_guard_disable")
    # Closed local-unit inventory immediately precedes the manager-mediated boundary.
    _attest_systemd_boot_surface()
    code, _ = _systemctl_result(["mask", "--now", "nginx.service"])
    if code != 0:
        raise ActivationError("Mask manager-mediated nginx.service fallita")
    _fsync_directory(NGINX_MIGRATION_GUARD.parent)
    _verify_migration_guard()


def _remove_migration_guard() -> None:
    # Recovery of a legacy guard may still have the canonical wants link underneath the mask.
    _disable_nginx_autostart_link()
    _fault("after_nginx_disable")

    # Final guarded linearization point: no process/listener or local boot unit may survive.
    _verify_migration_guard()
    _attest_systemd_boot_surface()
    _verify_migration_guard()
    code, _ = _systemctl_result(["unmask", "nginx.service"])
    if code != 0:
        raise ActivationError("Unmask manager-mediated nginx.service fallita")
    _fsync_directory(NGINX_MIGRATION_GUARD.parent)
    _fault("after_guard_unmask")
    code, _ = _systemctl_result(["daemon-reload"])
    if code != 0:
        raise ActivationError("systemd daemon-reload fallito durante rimozione guard")
    _attest_effective_nginx_unit(
        expect_running=False,
        allowed_unit_file_states=DISABLED_NGINX_UNIT_FILE_STATES,
    )
    _require_nginx_not_running()
    _assert_zero_nginx_processes()
    _assert_no_canonical_listeners()
    _fault("after_unit_reload_attestation")


def _start_nginx_service() -> None:
    # Start while disabled: no crash/reboot can autostart before runtime attestation.
    _attest_effective_nginx_unit(
        expect_running=False,
        allowed_unit_file_states=DISABLED_NGINX_UNIT_FILE_STATES,
    )
    _require_nginx_not_running()
    _assert_zero_nginx_processes()
    _assert_no_canonical_listeners()
    code, _ = _systemctl_result(["start", "nginx.service"])
    if code != 0:
        raise ActivationError("Avvio nginx.service fallito")
    disabled_unit = _attest_effective_nginx_unit(
        expect_running=True,
        allowed_unit_file_states=DISABLED_NGINX_UNIT_FILE_STATES,
    )
    _attest_nginx_service_runtime(disabled_unit)
    _fault("after_nginx_runtime_attestation")

    # Keep the last boot-surface check adjacent to final persistent enablement.
    _attest_systemd_boot_surface()
    _attest_nginx_service_runtime(disabled_unit)
    code, _ = _systemctl_result(["enable", "nginx.service"])
    if code != 0:
        raise ActivationError("Riabilitazione persistente nginx.service fallita")
    if NGINX_WANTS_LINK.parent.is_dir() and not NGINX_WANTS_LINK.parent.is_symlink():
        _fsync_directory(NGINX_WANTS_LINK.parent)
    _fault("after_nginx_enable")
    code, unit_state = _systemctl_result(["is-enabled", "nginx.service"])
    if code != 0 or unit_state != "enabled":
        raise ActivationError("nginx.service non risulta enabled dopo start attestato")
    enabled_unit = _attest_effective_nginx_unit(expect_running=True)
    _attest_nginx_service_runtime(enabled_unit)


def _apply_bundle_links(bundle: Path) -> None:
    _remove_symlink(DISTRO_DEFAULT)
    _replace_symlink(CURRENT_LINK, str(bundle))
    for path, target in INTEGRATION_LINKS.items():
        _replace_symlink(path, target)


def _validate_activated(info: BundleInfo, *, guard_required: bool = True) -> None:
    _attest_systemd_boot_surface()
    verified = verify_bundle(info.path)
    trusted_module_sources = verify_host_configuration_trust(
        verified, guard_required=guard_required, require_complete_links=True
    )
    if verified.lock_digest != info.lock_digest:
        raise ActivationError("Bundle mutato durante activation")
    _fault("before_nginx_test")
    _run(["nginx", "-t", "-c", str(NGINX_CONFIG)])
    _fault("after_nginx_test")
    validate_effective_nginx(
        _nginx_effective(),
        verified.manifest,
        topology="v2",
        expected_sources=verified.sources,
        trusted_module_sources=trusted_module_sources,
    )
    _fault("after_effective_validation")
    _run(["logrotate", "--debug", "/etc/logrotate.conf"])
    _fault("after_logrotate_validation")
    _run(["systemd-analyze", "verify", str(SYSTEMD_LINK)])
    _fault("after_systemd_validation")
    final_module_sources = verify_host_configuration_trust(
        verified, guard_required=guard_required, require_complete_links=True
    )
    if final_module_sources != trusted_module_sources:
        raise ActivationError("Inventario moduli nginx mutato durante la validazione")


def _state_for(preflight: Preflight) -> dict[str, Any]:
    return {
        "schema_version": "thebitlab.pilot-activation-state.v3",
        "status": "prepared",
        "candidate_bundle": str(preflight.candidate.path),
        "candidate_lock_digest": preflight.candidate.lock_digest,
        "previous_v2_bundle": (
            str(preflight.previous_v2.path) if preflight.previous_v2 is not None else None
        ),
        "previous_v2_lock_digest": (
            preflight.previous_v2.lock_digest if preflight.previous_v2 is not None else None
        ),
        "unsafe_provenance": dict(preflight.unsafe_provenance),
    }


def _state_bundle(state: Mapping[str, Any], *, previous: bool = False) -> BundleInfo:
    path_key = "previous_v2_bundle" if previous else "candidate_bundle"
    digest_key = "previous_v2_lock_digest" if previous else "candidate_lock_digest"
    raw = state[path_key]
    if raw is None:
        raise ActivationError("Previous v2 assente nello state")
    info = verify_bundle(Path(raw))
    if info.lock_digest != state[digest_key]:
        raise ActivationError("Bundle reale dello state mutato o sostituito")
    return info


def _write_status(path: Path, state: dict[str, Any], status: str) -> None:
    state["status"] = status
    _write_state(path, state, exclusive=False)


def _finish_transition(
    state_path: Path,
    state: dict[str, Any],
    target: BundleInfo,
    *,
    rollback_transition: bool,
) -> None:
    prepared = "rollback_prepared" if rollback_transition else "prepared"
    switched = "rollback_switched" if rollback_transition else "switched"
    validated = "rollback_validated" if rollback_transition else "validated"
    final = "rolled_back_v2" if rollback_transition else "active"
    status = state["status"]

    if status == prepared:
        verify_host_configuration_trust(target, guard_required=True)
        prepare_log_directory(target.manifest)
        verify_host_configuration_trust(target, guard_required=True)
        _remove_symlink(DISTRO_DEFAULT)
        _fault("after_distro_default_disable")
        _replace_symlink(CURRENT_LINK, str(target.path))
        _fault("after_current_switch")
        for path, link_target in INTEGRATION_LINKS.items():
            _replace_symlink(path, link_target)
        verify_host_configuration_trust(
            target, guard_required=True, require_complete_links=True
        )
        _write_status(state_path, state, switched)
        _fault("after_switched_state")
        status = switched

    if status == switched:
        # Reapply idempotently: a crash may have persisted only a prefix of the symlink set.
        _apply_bundle_links(target.path)
        verify_host_configuration_trust(
            target, guard_required=True, require_complete_links=True
        )
        _fault("before_validation")
        _validate_activated(target, guard_required=True)
        _write_status(state_path, state, validated)
        _fault("after_validated_state")
        status = validated

    if status != validated:
        raise ActivationError(f"Stato transition non recuperabile automaticamente: {status}")

    guard_present = _symlink_state(NGINX_MIGRATION_GUARD)["present"]
    _validate_activated(target, guard_required=guard_present)
    if guard_present:
        try:
            _remove_migration_guard()
        except Exception:
            if not _symlink_state(NGINX_MIGRATION_GUARD)["present"]:
                _install_migration_guard()
            raise
    _fault("after_guard_remove")
    try:
        _start_nginx_service()
    except Exception:
        # A catchable start failure returns to the durable offline boundary.
        _install_migration_guard()
        raise
    _fault("after_nginx_start")
    # Catch a foreign nginx introduced after systemctl start but before durable active state.
    _attest_nginx_service_runtime()
    _write_status(state_path, state, final)


def _idempotent_activation(bundle: Path, state_path: Path) -> bool:
    if not _state_exists(state_path):
        return False
    state = _read_state(state_path)
    if state["status"] != "active":
        raise ActivationError("Activation incompleta: usare il comando recover, non archiviare lo state")
    candidate = verify_bundle(bundle)
    if (
        state["candidate_bundle"] != str(candidate.path)
        or state["candidate_lock_digest"] != candidate.lock_digest
    ):
        raise ActivationError("Activation state appartiene a una candidate diversa")
    if _symlink_state(DISTRO_DEFAULT)["present"] or _current_bundle_path() != candidate.path:
        raise ActivationError("Topologia attiva divergente dall'activation state")
    for path, target in INTEGRATION_LINKS.items():
        _check_managed_link(path, target, allow_absent=False)
    _validate_activated(candidate, guard_required=False)
    _attest_nginx_service_runtime()
    return True


def activate(bundle: Path, state_path: Path = STATE_FILE) -> None:
    if _state_exists(state_path):
        if _idempotent_activation(bundle, state_path):
            return
    if _symlink_state(NGINX_MIGRATION_GUARD)["present"]:
        raise ActivationError("Migration guard orphan: usare recover; rimozione automatica vietata")
    preflight = verify_host_preflight(bundle, guard_required=False)
    _fault("after_preflight")
    _install_migration_guard()
    _fault("after_guard_install")
    verify_host_configuration_trust(preflight.candidate, guard_required=True)
    state = _state_for(preflight)
    _write_state(state_path, state, exclusive=True)
    _fault("after_state_write")
    _finish_transition(
        state_path, state, preflight.candidate, rollback_transition=False
    )


def recover(bundle: Path | None = None, state_path: Path = STATE_FILE) -> None:
    """Resume solely from durable guard/state/filesystem evidence; never force through failure."""

    if os.geteuid() != 0:
        raise ActivationError("Recovery Ubuntu richiede root")
    _attest_systemd_boot_surface()
    if not _state_exists(state_path):
        if not _symlink_state(NGINX_MIGRATION_GUARD)["present"]:
            raise ActivationError("Nessuna transition persistente da recuperare")
        if bundle is None:
            raise ActivationError("Guard orphan: --bundle trusted richiesto per recovery")
        _install_migration_guard()
        preflight = verify_host_preflight(bundle, guard_required=True)
        state = _state_for(preflight)
        _write_state(state_path, state, exclusive=True)
        _finish_transition(state_path, state, preflight.candidate, rollback_transition=False)
        return

    state = _read_state(state_path)
    if state["status"] == "active":
        selected = Path(state["candidate_bundle"]) if bundle is None else bundle
        _idempotent_activation(selected, state_path)
        return
    if state["status"] == "rolled_back_v2":
        target = _state_bundle(state, previous=True)
        _validate_activated(target, guard_required=False)
        _attest_nginx_service_runtime()
        return

    # Re-acquire through systemd for every intermediate state, including a cached manager
    # that has not observed a durable filesystem mask after crash/reboot.
    _install_migration_guard()

    if state["status"].startswith("rollback_"):
        target = _state_bundle(state, previous=True)
        _finish_transition(state_path, state, target, rollback_transition=True)
    else:
        target = _state_bundle(state)
        if bundle is not None and target.path != verify_bundle(bundle).path:
            raise ActivationError("Recovery bundle diversa dalla candidate dello state")
        _finish_transition(state_path, state, target, rollback_transition=False)


def rollback(state_path: Path = STATE_FILE) -> None:
    if os.geteuid() != 0:
        raise ActivationError("Rollback Ubuntu richiede root")
    state = _read_state(state_path)
    if state["status"] != "active":
        raise ActivationError("Activation state non è in stato active")
    candidate = _state_bundle(state)
    previous_raw = state["previous_v2_bundle"]
    if previous_raw is None:
        _validate_activated(candidate, guard_required=False)
        _attest_nginx_service_runtime()
        raise ActivationError(
            "Nessuna previous v2 riproducibile: candidate mantenuta, rollback app separato richiesto"
        )
    previous = _state_bundle(state, previous=True)
    verify_host_configuration_trust(candidate, guard_required=False)
    _install_migration_guard()
    _fault("after_guard_install")
    _write_status(state_path, state, "rollback_prepared")
    _fault("after_state_write")
    _finish_transition(state_path, state, previous, rollback_transition=True)


def complete(state_path: Path, archive_path: Path) -> None:
    if os.geteuid() != 0:
        raise ActivationError("Complete Ubuntu richiede root")
    state = _read_state(state_path)
    if state["status"] not in {"active", "rolled_back_v2"}:
        raise ActivationError("State incompleto non archiviabile: eseguire recover")
    if archive_path.exists() or archive_path.is_symlink():
        raise ActivationError("Archive activation state già esistente")
    if not archive_path.is_absolute() or archive_path.parent != state_path.parent:
        raise ActivationError("Archive activation state deve essere un nuovo file sibling")
    os.replace(state_path, archive_path)
    _fsync_directory(archive_path.parent)


def main(argv: list[str] | None = None) -> int:
    try:
        _require_trusted_runtime()
    except ActivationError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--bundle", type=Path, required=True)
    activate_parser = subparsers.add_parser("activate")
    activate_parser.add_argument("--bundle", type=Path, required=True)
    activate_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    recover_parser = subparsers.add_parser("recover")
    recover_parser.add_argument("--bundle", type=Path)
    recover_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    complete_parser.add_argument("--archive", type=Path, required=True)
    subparsers.add_parser("logrotate-snapshot")
    subparsers.add_parser("logrotate-reopen")
    subparsers.add_parser("runtime-info")
    args = parser.parse_args(argv)
    try:
        if args.command == "runtime-info":
            print(json.dumps(_runtime_information(), indent=2, sort_keys=True))
            return 0
        if args.command == "preflight":
            verify_host_preflight(args.bundle)
        elif args.command == "activate":
            activate(args.bundle, args.state_file)
        elif args.command == "rollback":
            rollback(args.state_file)
        elif args.command == "recover":
            recover(args.bundle, args.state_file)
        elif args.command == "complete":
            complete(args.state_file, args.archive)
        elif args.command == "logrotate-snapshot":
            logrotate_snapshot()
        else:
            logrotate_reopen()
    except (ActivationError, deployment.DeploymentValidationError, KeyError, OSError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: pilot Ubuntu {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
