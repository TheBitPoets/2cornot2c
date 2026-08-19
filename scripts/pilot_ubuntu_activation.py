#!/usr/bin/env python3
"""Activate, migrate, or roll back the dedicated Ubuntu pilot topology fail-closed."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_pilot_deployment as deployment  # noqa: E402


NGINX_CONFIG = Path("/etc/nginx/nginx.conf")
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


def _source_path(path: Path) -> str:
    """Return the POSIX spelling emitted by nginx -T, including in portable tests."""

    return path.as_posix()


@dataclass(frozen=True)
class Token:
    value: str
    line: int
    structural: bool = False


@dataclass(frozen=True)
class Directive:
    source: str
    name: str
    args: tuple[str, ...]
    children: tuple["Directive", ...] | None
    line: int


@dataclass(frozen=True)
class BundleInfo:
    path: Path
    manifest: dict[str, Any]
    lock_digest: str
    sources: Mapping[str, str]
    current_renderer: bool = True


@dataclass(frozen=True)
class Preflight:
    candidate: BundleInfo
    source_kind: str
    previous_v2: BundleInfo | None
    unsafe_provenance: Mapping[str, Any]


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
    """Fault-injection hook used by tests; production deliberately does nothing."""


def _symlink_state(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {"present": False}
    if not stat.S_ISLNK(metadata.st_mode):
        raise ActivationError(f"Elemento gestito non-symlink: {path}")
    return {"present": True, "target": os.readlink(path)}


def _replace_symlink(path: Path, target: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.thebitlab-{os.getpid()}")
    try:
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(target)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _remove_symlink(path: Path) -> None:
    state = _symlink_state(path)
    if state["present"]:
        path.unlink()


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
    tokens: list[Token] = []
    value: list[str] = []
    token_line = 1
    line = 1
    quote: str | None = None
    escaped = False
    index = 0

    def flush() -> None:
        nonlocal value
        if value:
            tokens.append(Token("".join(value), token_line))
            value = []

    while index < len(text):
        char = text[index]
        if escaped:
            value.append(char)
            escaped = False
            if char == "\n":
                line += 1
            index += 1
            continue
        if char == "\\":
            if not value:
                token_line = line
            escaped = True
            index += 1
            continue
        if quote is not None:
            if char == quote:
                quote = None
            else:
                value.append(char)
                if char == "\n":
                    line += 1
            index += 1
            continue
        if char in {"'", '"'}:
            if not value:
                token_line = line
            quote = char
            index += 1
            continue
        if char == "#":
            flush()
            newline = text.find("\n", index)
            if newline < 0:
                index = len(text)
            else:
                index = newline
            continue
        if char in "{};":
            flush()
            tokens.append(Token(char, line, structural=True))
            index += 1
            continue
        if char.isspace():
            flush()
            if char == "\n":
                line += 1
            index += 1
            continue
        if not value:
            token_line = line
        value.append(char)
        index += 1
    if escaped or quote is not None:
        raise ActivationError(f"Configurazione nginx ambigua in {source}: quote/escape incompleto")
    flush()
    return tuple(tokens)


def _parse_nginx_source(source: str, text: str) -> tuple[Directive, ...]:
    tokens = _tokenize_nginx(source, text)

    def parse_sequence(index: int, *, nested: bool) -> tuple[tuple[Directive, ...], int]:
        directives: list[Directive] = []
        words: list[Token] = []
        while index < len(tokens):
            token = tokens[index]
            if token.structural and token.value == "}":
                if words or not nested:
                    raise ActivationError(
                        f"Configurazione nginx malformata in {source}:{token.line}"
                    )
                return tuple(directives), index + 1
            if token.structural and token.value == ";":
                if not words:
                    raise ActivationError(
                        f"Direttiva nginx vuota in {source}:{token.line}"
                    )
                directives.append(
                    Directive(source, words[0].value, tuple(item.value for item in words[1:]), None, words[0].line)
                )
                words = []
                index += 1
                continue
            if token.structural and token.value == "{":
                if not words:
                    raise ActivationError(
                        f"Blocco nginx senza direttiva in {source}:{token.line}"
                    )
                children, index = parse_sequence(index + 1, nested=True)
                directives.append(
                    Directive(
                        source,
                        words[0].value,
                        tuple(item.value for item in words[1:]),
                        children,
                        words[0].line,
                    )
                )
                words = []
                continue
            words.append(token)
            index += 1
        if words or nested:
            line_number = words[0].line if words else (tokens[-1].line if tokens else 1)
            raise ActivationError(
                f"Configurazione nginx incompleta in {source}:{line_number}"
            )
        return tuple(directives), index

    parsed, end = parse_sequence(0, nested=False)
    if end != len(tokens):
        raise ActivationError(f"Configurazione nginx non consumata in {source}")
    return parsed


def _walk_directives(
    directives: Sequence[Directive], context: tuple[str, ...] = ()
) -> Iterable[tuple[Directive, tuple[str, ...]]]:
    for directive in directives:
        yield directive, context
        if directive.children is not None:
            yield from _walk_directives(directive.children, context + (directive.name,))


def _direct(directives: Sequence[Directive], name: str) -> list[Directive]:
    return [directive for directive in directives if directive.name == name]


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
        process_source = parsed.get(_source_path(PROCESS_LINK), ())
        process = _direct(process_source, "error_log")
        expected_process = (manifest["origin"]["error_log"], "notice")
        if len(process) != 1 or process[0].args != expected_process:
            raise ActivationError("Error log process-level main-context assente o duplicato")
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
    require_current_renderer: bool = True,
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
    if require_current_renderer:
        with tempfile.TemporaryDirectory(prefix="thebitlab-verify-bundle-") as temporary_name:
            expected = Path(temporary_name) / "bundle"
            deployment.render_bundle(manifest, expected)
            _compare_expected_bundle(trusted, expected, deployment.GENERATED_FILES)
    sources = {
        _source_path(PROCESS_LINK): process_text,
        _source_path(FORMAT_LINK): format_text,
        _source_path(SITE_LINK): site_text,
    }
    return BundleInfo(trusted, manifest, lock_digest, sources, require_current_renderer)


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


def _verify_modules_enabled_entries() -> None:
    directory = Path("/etc/nginx/modules-enabled")
    for entry in directory.iterdir():
        if entry == PROCESS_LINK:
            _check_managed_link(entry, INTEGRATION_LINKS[PROCESS_LINK], allow_absent=True)
            continue
        if not entry.name.endswith(".conf") or not entry.is_symlink():
            raise ActivationError(f"modules-enabled contiene artifact unmanaged: {entry}")
        try:
            target = entry.resolve(strict=True)
            target.relative_to(Path("/usr/share/nginx/modules-available"))
        except (OSError, ValueError) as exc:
            raise ActivationError(f"Modulo nginx non attribuibile al package Ubuntu: {entry}") from exc
        _assert_trusted_metadata(target, directory=False, require_root_owner=True)
        directives = _parse_nginx_source(entry.as_posix(), target.read_text(encoding="utf-8"))
        _validate_module_source(entry.as_posix(), directives)


def verify_ubuntu_layout() -> None:
    for directory in (
        Path("/etc/nginx/modules-enabled"),
        Path("/etc/nginx/conf.d"),
        Path("/etc/nginx/sites-enabled"),
        Path("/etc/logrotate.d"),
    ):
        if not directory.is_dir() or directory.is_symlink():
            raise ActivationError(f"Directory Ubuntu non supportata: {directory}")
    _verify_modules_enabled_entries()
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


def _classify_existing_topology(effective: str) -> tuple[str, BundleInfo | None]:
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
        validate_effective_nginx(effective, None, topology=topology, expected_sources=expected)
        return topology, None

    if default_state["present"]:
        raise ActivationError("Default distro e site pilot attivi simultaneamente")
    current = _current_bundle_path()
    try:
        previous_v2 = verify_bundle(current, require_current_renderer=False)
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
    )
    return "legacy-v1", None


def verify_host_preflight(bundle: Path) -> Preflight:
    if os.geteuid() != 0:
        raise ActivationError("Il preflight host Ubuntu richiede root")
    verify_ubuntu_layout()
    candidate = verify_bundle(bundle)

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

    effective = _nginx_effective()
    source_kind, previous_v2 = _classify_existing_topology(effective)
    if previous_v2 is not None and previous_v2.path == candidate.path:
        raise ActivationError("Candidate già attiva senza activation state autorevole")
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
    group_id = grp.getgrnam("adm").gr_gid
    file_owner_id = pwd.getpwnam("www-data").pw_uid
    directory.mkdir(mode=0o750, parents=False, exist_ok=True)
    metadata = directory.lstat()
    if directory.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ActivationError(f"Directory log non regolare: {directory}")
    _verify_no_extended_acl(directory)
    os.chown(directory, owner_id, group_id)
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
            os.fchown(descriptor, file_owner_id, group_id)
            os.fchmod(descriptor, 0o640)
        finally:
            os.close(descriptor)
        _verify_no_extended_acl(path)
        metadata = path.stat()
        if (
            stat.S_IMODE(metadata.st_mode) != 0o640
            or metadata.st_uid != file_owner_id
            or metadata.st_gid != group_id
        ):
            raise ActivationError(f"Metadata log non canonici: {path}")
    metadata = directory.stat()
    if (
        stat.S_IMODE(metadata.st_mode) != 0o750
        or metadata.st_uid != owner_id
        or metadata.st_gid != group_id
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
    if state["schema_version"] != "thebitlab.pilot-activation-state.v2":
        raise ActivationError("Versione activation state non supportata")
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
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
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
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)


def _state_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _nginx_may_be_running() -> bool:
    pid_path = Path("/run/nginx.pid")
    if not pid_path.exists() and not pid_path.is_symlink():
        return False
    try:
        metadata = pid_path.lstat()
        raw = pid_path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise ActivationError("PID nginx non verificabile") from exc
    if pid_path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ActivationError("PID nginx non canonico")
    # nginx -t on Ubuntu may leave an empty regular pid file; it denotes no process.
    if not raw:
        return False
    if not raw.isdecimal():
        raise ActivationError("PID nginx non canonico")
    return Path(f"/proc/{raw}").exists()


def _apply_bundle_links(bundle: Path) -> None:
    _remove_symlink(DISTRO_DEFAULT)
    _replace_symlink(CURRENT_LINK, str(bundle))
    for path, target in INTEGRATION_LINKS.items():
        _replace_symlink(path, target)


def _validate_activated(info: BundleInfo) -> None:
    verified = verify_bundle(
        info.path, require_current_renderer=info.current_renderer
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
    )
    _fault("after_effective_validation")
    _run(["logrotate", "--debug", "/etc/logrotate.conf"])
    _fault("after_logrotate_validation")
    _run(["systemd-analyze", "verify", str(SYSTEMD_LINK)])
    _fault("after_systemd_validation")


def _ensure_candidate_or_no_server(info: BundleInfo) -> str:
    """Never restore unsafe links; retain candidate v2 or disable the pilot site."""

    try:
        _apply_bundle_links(info.path)
        prepare_log_directory(info.manifest)
        _validate_activated(info)
        return "failed_candidate_retained"
    except Exception:
        _remove_symlink(DISTRO_DEFAULT)
        _remove_symlink(SITE_LINK)
        try:
            _run(["nginx", "-t", "-c", str(NGINX_CONFIG)])
        except Exception as exc:
            raise ActivationError("Failure non recuperabile: nginx non è fail-closed") from exc
        return "failed_no_server"


def _state_for(preflight: Preflight) -> dict[str, Any]:
    return {
        "schema_version": "thebitlab.pilot-activation-state.v2",
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


def _idempotent_activation(bundle: Path, state_path: Path) -> bool:
    if not _state_exists(state_path):
        return False
    state = _read_state(state_path)
    if state["status"] != "active":
        raise ActivationError("Activation state esistente non completato; archiviazione esplicita richiesta")
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
    _validate_activated(candidate)
    return True


def activate(bundle: Path, state_path: Path = STATE_FILE) -> None:
    if _idempotent_activation(bundle, state_path):
        return
    preflight = verify_host_preflight(bundle)
    unsafe_source = preflight.source_kind != "v2"
    if unsafe_source and _nginx_may_be_running():
        raise ActivationError("Prima migrazione richiede nginx fermo per non mantenere logging v1 in memoria")
    state = _state_for(preflight)
    _write_state(state_path, state, exclusive=True)
    try:
        _fault("after_state_write")
        prepare_log_directory(preflight.candidate.manifest)
        _remove_symlink(DISTRO_DEFAULT)
        _fault("after_distro_default_disable")
        _replace_symlink(CURRENT_LINK, str(preflight.candidate.path))
        _fault("after_current_switch")
        for path, target in INTEGRATION_LINKS.items():
            _replace_symlink(path, target)
        verified = verify_bundle(preflight.candidate.path)
        if verified.lock_digest != preflight.candidate.lock_digest:
            raise ActivationError("Bundle mutato prima dello switch")
        _fault("before_validation")
        _validate_activated(verified)
        state["status"] = "active"
        _write_state(state_path, state, exclusive=False)
    except Exception as exc:
        if preflight.previous_v2 is not None:
            try:
                _apply_bundle_links(preflight.previous_v2.path)
                _validate_activated(preflight.previous_v2)
                state["status"] = "failed_rolled_back_v2"
            except Exception as rollback_exc:
                state["status"] = _ensure_candidate_or_no_server(preflight.candidate)
                _write_state(state_path, state, exclusive=False)
                raise ActivationError(
                    f"Activation fallita; previous v2 non ripristinabile, host fail-closed: {rollback_exc}"
                ) from exc
        else:
            state["status"] = _ensure_candidate_or_no_server(preflight.candidate)
        _write_state(state_path, state, exclusive=False)
        raise


def rollback(state_path: Path = STATE_FILE) -> None:
    if os.geteuid() != 0:
        raise ActivationError("Rollback Ubuntu richiede root")
    state = _read_state(state_path)
    if state["status"] != "active":
        raise ActivationError("Activation state non è in stato active")
    candidate = verify_bundle(Path(state["candidate_bundle"]))
    if candidate.lock_digest != state["candidate_lock_digest"]:
        raise ActivationError("Candidate dello state non verificabile")
    previous_raw = state["previous_v2_bundle"]
    if previous_raw is None:
        _apply_bundle_links(candidate.path)
        _validate_activated(candidate)
        state["status"] = "rollback_unavailable_candidate_retained"
        _write_state(state_path, state, exclusive=False)
        raise ActivationError("Nessuna previous v2 sicura: candidate v2 mantenuta, rollback app separato richiesto")
    previous = verify_bundle(Path(previous_raw), require_current_renderer=False)
    if previous.lock_digest != state["previous_v2_lock_digest"]:
        raise ActivationError("Previous v2 dello state mutata o sostituita")
    try:
        _apply_bundle_links(previous.path)
        _validate_activated(previous)
        state["status"] = "rolled_back_v2"
        _write_state(state_path, state, exclusive=False)
    except Exception as exc:
        try:
            _apply_bundle_links(candidate.path)
            _validate_activated(candidate)
            state["status"] = "rollback_failed_candidate_retained"
        except Exception:
            state["status"] = _ensure_candidate_or_no_server(candidate)
        _write_state(state_path, state, exclusive=False)
        raise ActivationError("Rollback previous v2 fallito; host mantenuto fail-closed") from exc


def complete(state_path: Path, archive_path: Path) -> None:
    if os.geteuid() != 0:
        raise ActivationError("Complete Ubuntu richiede root")
    _read_state(state_path)
    if archive_path.exists() or archive_path.is_symlink():
        raise ActivationError("Archive activation state già esistente")
    if not archive_path.is_absolute() or archive_path.parent != state_path.parent:
        raise ActivationError("Archive activation state deve essere un nuovo file sibling")
    os.replace(state_path, archive_path)
    os.chmod(archive_path, 0o600)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--bundle", type=Path, required=True)
    activate_parser = subparsers.add_parser("activate")
    activate_parser.add_argument("--bundle", type=Path, required=True)
    activate_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("--state-file", type=Path, default=STATE_FILE)
    complete_parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            verify_host_preflight(args.bundle)
        elif args.command == "activate":
            activate(args.bundle, args.state_file)
        elif args.command == "rollback":
            rollback(args.state_file)
        else:
            complete(args.state_file, args.archive)
    except (ActivationError, deployment.DeploymentValidationError, KeyError, OSError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: pilot Ubuntu {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
