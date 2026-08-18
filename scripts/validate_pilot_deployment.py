#!/usr/bin/env python3
"""Validate and render the secret-safe TheBitLab pilot deployment baseline."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(ROOT))

from scripts.pilot_environment import (  # noqa: E402
    DeploymentValidationError,
    check_environment_file,
    parse_environment_file,
    validate_external_environment,
)


DEPLOYMENT_SCHEMA = ROOT / "schemas" / "pilot-deployment.schema.json"
ENVIRONMENT_SCHEMA = ROOT / "schemas" / "pilot-environment.schema.json"
TEMPLATE_ROOT = ROOT / "deploy" / "pilot" / "templates"
_ORIGIN_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?[.])+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
GENERATED_FILES = (
    "nginx/thebitlab-log-format.conf",
    "nginx/thebitlab.conf",
    "logrotate/thebitlab",
    "systemd/thebitlab.service",
    "firewall/origin-exposure.json",
    "manifest.normalized.json",
)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DeploymentValidationError(f"Chiave JSON duplicata: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8-sig"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except DeploymentValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeploymentValidationError(f"JSON non valido: {path}") from exc
    if not isinstance(payload, dict):
        raise DeploymentValidationError(f"Oggetto JSON richiesto: {path}")
    return payload


def _schema_errors(instance: Mapping[str, Any], schema_path: Path, *, redact: bool) -> list[str]:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    messages = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        detail = "vincolo non soddisfatto" if redact else error.message
        messages.append(f"{location}: {detail}")
    return messages


def _posix_path(value: str) -> PurePosixPath:
    return PurePosixPath(value)


def _is_within(candidate: PurePosixPath, parent: PurePosixPath) -> bool:
    return candidate == parent or parent in candidate.parents


def _semantic_manifest_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    release = manifest["release"]
    service = manifest["service"]
    data = manifest["data"]
    origin = manifest["origin"]

    repository_root = _posix_path(release["repository_root"])
    python_executable = _posix_path(release["python_executable"])
    data_root = _posix_path(data["root"])
    environment_file = _posix_path(service["environment_file"])
    home_directory = _posix_path(service["home_directory"])
    tls_certificate = _posix_path(origin["tls_certificate_file"])
    tls_private_key = _posix_path(origin["tls_private_key_file"])
    access_log = _posix_path(origin["access_log"])
    error_log = _posix_path(origin["error_log"])

    if service["user"] in {"root", "nobody"} or service["group"] in {"root", "nogroup"}:
        errors.append("service: usare un account dedicato non privilegiato")
    if home_directory != PurePosixPath("/home") / service["user"]:
        errors.append("service.home_directory: deve essere /home/<service.user>")
    if _is_within(data_root, repository_root) or _is_within(repository_root, data_root):
        errors.append("data.root: deve essere separata dalla release applicativa")
    if not _is_within(python_executable, repository_root):
        errors.append("release.python_executable: deve appartenere alla release applicativa")

    auth_relative = _posix_path(data["auth_db_path"])
    auth_resolved = data_root / auth_relative
    if auth_relative.is_absolute() or auth_relative == PurePosixPath("."):
        errors.append("data.auth_db_path: deve essere un file relativo alla data root")
    if auth_relative.suffix not in {".db", ".sqlite", ".sqlite3"}:
        errors.append("data.auth_db_path: estensione SQLite richiesta")
    if not _is_within(auth_resolved, data_root) or auth_resolved == data_root:
        errors.append("data.auth_db_path: risoluzione fuori dalla data root")

    external_paths = {
        "service.environment_file": environment_file,
        "origin.tls_certificate_file": tls_certificate,
        "origin.tls_private_key_file": tls_private_key,
    }
    for name, path in external_paths.items():
        if _is_within(path, repository_root) or _is_within(path, data_root):
            errors.append(f"{name}: il riferimento esterno non può stare nella release o nella data root")
    if len(set(external_paths.values())) != len(external_paths):
        errors.append("secret references: environment, certificato e chiave devono avere path distinti")
    if access_log == error_log:
        errors.append("origin: access_log e error_log devono avere path distinti")
    for name, path in (("origin.access_log", access_log), ("origin.error_log", error_log)):
        if _is_within(path, repository_root) or _is_within(path, data_root):
            errors.append(f"{name}: il log deve stare fuori da release e data root")

    try:
        parsed_origin = urlsplit(origin["url"])
        parsed_hostname = parsed_origin.hostname
        parsed_port = parsed_origin.port
    except ValueError:
        parsed_origin = None
        parsed_hostname = None
        parsed_port = -1
    canonical_origin = f"https://{parsed_hostname}" if parsed_hostname is not None else None
    if (
        parsed_origin is None
        or parsed_origin.scheme != "https"
        or not parsed_hostname
        or _ORIGIN_HOST_RE.fullmatch(parsed_hostname) is None
        or parsed_hostname.rsplit(".", 1)[-1].isdigit()
        or parsed_origin.username is not None
        or parsed_origin.password is not None
        or parsed_port is not None
        or parsed_origin.path
        or parsed_origin.query
        or parsed_origin.fragment
        or origin["url"] != canonical_origin
    ):
        errors.append("origin.url: deve essere una origin HTTPS canonica senza porta, path, query o credenziali")

    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for index, raw_network in enumerate(origin["allowed_proxy_cidrs"]):
        try:
            network = ipaddress.ip_network(raw_network, strict=True)
        except ValueError:
            errors.append(f"origin.allowed_proxy_cidrs.{index}: CIDR canonica richiesta")
            continue
        if network.prefixlen == 0 or network.is_loopback or network.is_unspecified or network.is_multicast:
            errors.append(f"origin.allowed_proxy_cidrs.{index}: rete non ammessa")
        networks.append(network)
    for index, network in enumerate(networks):
        if any(
            index != other
            and network.version == candidate.version
            and network.subnet_of(candidate)
            for other, candidate in enumerate(networks)
        ):
            errors.append(f"origin.allowed_proxy_cidrs.{index}: rete ridondante o sovrapposta")

    return errors


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    errors = _schema_errors(manifest, DEPLOYMENT_SCHEMA, redact=False)
    if not errors:
        errors.extend(_semantic_manifest_errors(manifest))
    if errors:
        raise DeploymentValidationError("Manifest deployment non valido:\n- " + "\n- ".join(errors))


def validate_environment(values: Mapping[str, str], *, github_oauth: bool) -> None:
    errors = _schema_errors(values, ENVIRONMENT_SCHEMA, redact=True)
    if errors:
        raise DeploymentValidationError(
            "EnvironmentFile non valido (valori omessi):\n- " + "\n- ".join(errors)
        )
    validate_external_environment(values, github_oauth=github_oauth)


def _check_external_file(
    path: Path, *, private: bool, allow_group_read: bool = False
) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise DeploymentValidationError(f"Riferimento esterno assente o non accessibile: {path}") from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise DeploymentValidationError(f"Riferimento esterno non regolare: {path}")
    forbidden_mode = 0o027 if allow_group_read else 0o077
    if private and os.name != "nt" and metadata.st_mode & forbidden_mode:
        raise DeploymentValidationError(f"Permessi troppo ampi sul riferimento esterno: {path}")


def check_external_references(manifest: Mapping[str, Any]) -> None:
    """Check metadata only; this function never opens or reads referenced files."""

    service = manifest["service"]
    origin = manifest["origin"]
    check_environment_file(Path(service["environment_file"]))
    _check_external_file(Path(origin["tls_certificate_file"]), private=False)
    _check_external_file(Path(origin["tls_private_key_file"]), private=True)


def _render_template(name: str, replacements: Mapping[str, str]) -> str:
    template = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(f"@@{token}@@", value)
    if "@@" in rendered:
        raise DeploymentValidationError(f"Template incompleto: {name}")
    return rendered


_ALLOWED_ACCESS_LOG_VARIABLES = frozenset(
    {
        "$remote_addr",
        "$time_local",
        "$request_method",
        "$uri",
        "$server_protocol",
        "$status",
        "$body_bytes_sent",
        "$request_time",
        "$request_id",
    }
)
_LOG_VARIABLE_RE = re.compile(r"(?<!\\)[$][A-Za-z0-9_]+")


def validate_rendered_logging(
    log_format: str,
    nginx_site: str,
    logrotate_config: str,
    manifest: Mapping[str, Any],
) -> None:
    """Fail closed if a rendered proxy log can persist query/header credentials."""

    variables = frozenset(_LOG_VARIABLE_RE.findall(log_format))
    if variables != _ALLOWED_ACCESS_LOG_VARIABLES:
        raise DeploymentValidationError("Formato access log fuori dalla allowlist secret-safe")
    if log_format.count("log_format thebitlab ") != 1:
        raise DeploymentValidationError("Formato access log thebitlab assente o duplicato")

    directives = re.findall(r"(?m)^\s*access_log\s+([^;]+);", nginx_site)
    expected = f'{manifest["origin"]["access_log"]} thebitlab'
    active = [directive.strip() for directive in directives if directive.strip() != "off"]
    if len(active) != 2 or any(directive != expected for directive in active):
        raise DeploymentValidationError("Direttiva access_log non vincolata al formato secret-safe")
    error_directives = [
        directive.strip()
        for directive in re.findall(r"(?m)^\s*error_log\s+([^;]+);", nginx_site)
    ]
    expected_error = f'{manifest["origin"]["error_log"]} crit'
    if len(error_directives) != 2 or any(
        directive != expected_error for directive in error_directives
    ):
        raise DeploymentValidationError("Direttiva error_log non vincolata al livello crit secret-safe")

    logging = manifest["logging"]
    required_lines = {
        logging["rotation"],
        f'rotate {logging["retention_days"]}',
        f'maxage {logging["retention_days"]}',
        "missingok",
        "notifempty",
        "compress",
        "delaycompress",
        f'create {logging["file_mode"]} {logging["owner"]} {logging["group"]}',
        "sharedscripts",
    }
    normalized_lines = {line.strip() for line in logrotate_config.splitlines() if line.strip()}
    expected_header = f'{manifest["origin"]["access_log"]} {manifest["origin"]["error_log"]} {{'
    if (
        expected_header not in normalized_lines
        or not required_lines.issubset(normalized_lines)
        or "copytruncate" in normalized_lines
    ):
        raise DeploymentValidationError("Policy logrotate incompleta o non sicura")


def validate_versioned_logging(manifest: Mapping[str, Any]) -> None:
    """Lint the versioned nginx/logrotate templates even without bundle output."""

    origin = manifest["origin"]
    origin_host = urlsplit(origin["url"]).hostname
    assert origin_host is not None
    replacements = {
        "ORIGIN_HOST": origin_host,
        "ORIGIN_ACCESS_RULES": _origin_access_rules(manifest),
        "TLS_CERTIFICATE_FILE": origin["tls_certificate_file"],
        "TLS_PRIVATE_KEY_FILE": origin["tls_private_key_file"],
        "ACCESS_LOG": origin["access_log"],
        "ERROR_LOG": origin["error_log"],
        "APP_PORT": str(manifest["service"]["port"]),
        "LOG_FILE_MODE": manifest["logging"]["file_mode"],
        "LOG_OWNER": manifest["logging"]["owner"],
        "LOG_GROUP": manifest["logging"]["group"],
    }
    validate_rendered_logging(
        _render_template("thebitlab-log-format.conf.template", replacements),
        _render_template("thebitlab-nginx.conf.template", replacements),
        _render_template("thebitlab-logrotate.conf.template", replacements),
        manifest,
    )


def _origin_access_rules(manifest: Mapping[str, Any]) -> str:
    if manifest["origin"]["exposure"] == "public":
        return "    # Public origin exposure explicitly selected by the manifest."
    rules = ["    # Local diagnostics remain possible; Internet traffic must come from the edge."]
    rules.extend(("    allow 127.0.0.1;", "    allow ::1;"))
    rules.extend(f"    allow {network};" for network in manifest["origin"]["allowed_proxy_cidrs"])
    rules.append("    deny all;")
    return "\n".join(rules)


def normalized_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def render_bundle(manifest: Mapping[str, Any], output: Path) -> None:
    validate_manifest(manifest)
    if output.exists():
        raise DeploymentValidationError(f"La directory output esiste già: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    origin = manifest["origin"]
    service = manifest["service"]
    release = manifest["release"]
    features = manifest["features"]
    origin_host = urlsplit(origin["url"]).hostname
    assert origin_host is not None
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
        "GOOGLE_REDIRECT_URI": f"{origin['url'].rstrip('/')}/auth/google/callback",
        "GITHUB_OAUTH_ARGUMENTS": (
            f" --enable-github-oauth --github-redirect-uri {origin['url'].rstrip('/')}/auth/github/callback"
            if features["github_oauth"]
            else ""
        ),
        "GITHUB_APP_FLAG": " --enable-github-app-token-runtime" if features["github_app_token_runtime"] else "",
        "GITHUB_APP_WRITE_PATH": f" -{github_app_directory}" if features["github_app_token_runtime"] else "",
        "ORIGIN_HOST": origin_host,
        "ORIGIN_ACCESS_RULES": _origin_access_rules(manifest),
        "TLS_CERTIFICATE_FILE": origin["tls_certificate_file"],
        "TLS_PRIVATE_KEY_FILE": origin["tls_private_key_file"],
        "ACCESS_LOG": origin["access_log"],
        "ERROR_LOG": origin["error_log"],
        "LOG_FILE_MODE": manifest["logging"]["file_mode"],
        "LOG_OWNER": manifest["logging"]["owner"],
        "LOG_GROUP": manifest["logging"]["group"],
    }
    firewall_contract = {
        "schema_version": "thebitlab.origin-exposure.v1",
        "mode": origin["exposure"],
        "default_for_tcp_ports": "deny" if origin["exposure"] == "edge_only" else "allow",
        "tcp_ports": [80, 443],
        "allowed_source_cidrs": origin["allowed_proxy_cidrs"],
        "backend_bind": f"{service['bind_host']}:{service['port']}",
    }
    contents = {
        "nginx/thebitlab-log-format.conf": _render_template("thebitlab-log-format.conf.template", replacements),
        "nginx/thebitlab.conf": _render_template("thebitlab-nginx.conf.template", replacements),
        "logrotate/thebitlab": _render_template("thebitlab-logrotate.conf.template", replacements),
        "systemd/thebitlab.service": _render_template("thebitlab.service.template", replacements),
        "firewall/origin-exposure.json": json.dumps(firewall_contract, indent=2, sort_keys=True) + "\n",
        "manifest.normalized.json": normalized_manifest_bytes(manifest).decode("utf-8"),
    }
    validate_rendered_logging(
        contents["nginx/thebitlab-log-format.conf"],
        contents["nginx/thebitlab.conf"],
        contents["logrotate/thebitlab"],
        manifest,
    )

    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for relative_name in GENERATED_FILES:
            target = temporary / relative_name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents[relative_name], encoding="utf-8", newline="\n")
        hashes = {
            name: hashlib.sha256((temporary / name).read_bytes()).hexdigest()
            for name in GENERATED_FILES
        }
        lock = {
            "schema_version": "thebitlab.pilot-deployment-lock.v1",
            "deployment_id": manifest["deployment_id"],
            "release_commit": release["commit"],
            "files": hashes,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Manifest JSON versionato.")
    parser.add_argument("--output", type=Path, help="Directory nuova in cui renderizzare gli artifact.")
    parser.add_argument(
        "--environment-file",
        type=Path,
        help="Valida esplicitamente un EnvironmentFile esterno senza stamparne i valori.",
    )
    parser.add_argument(
        "--check-external-references",
        action="store_true",
        help="Controlla esistenza/tipo/permessi dei riferimenti esterni senza leggerli.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = load_json(args.config)
        validate_manifest(manifest)
        validate_versioned_logging(manifest)
        if args.environment_file is not None:
            expected = Path(manifest["service"]["environment_file"])
            if args.environment_file.absolute() != expected.absolute():
                raise DeploymentValidationError("EnvironmentFile diverso dal riferimento nel manifest.")
            check_environment_file(args.environment_file)
            values = parse_environment_file(args.environment_file)
            validate_environment(values, github_oauth=manifest["features"]["github_oauth"])
        if args.check_external_references:
            check_external_references(manifest)
        if args.output is not None:
            render_bundle(manifest, args.output)
    except DeploymentValidationError as exc:
        print(f"ERRORE: {exc}", file=os.sys.stderr)
        return 2
    print("PASS: baseline deployment valida" + (" e renderizzata" if args.output else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
