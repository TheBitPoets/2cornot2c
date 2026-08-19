#!/usr/bin/env python3
"""Activate or roll back the dedicated Ubuntu nginx pilot topology fail-closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_pilot_deployment as deployment  # noqa: E402


NGINX_CONFIG = Path("/etc/nginx/nginx.conf")
CURRENT_LINK = Path("/etc/thebitlab/current")
STATE_FILE = Path("/etc/thebitlab/activation-state.json")
DISTRO_DEFAULT = Path("/etc/nginx/sites-enabled/default")
INTEGRATION_LINKS = {
    Path("/etc/nginx/modules-enabled/90-thebitlab-process-error-log.conf"):
        "/etc/thebitlab/current/nginx/thebitlab-process-error-log.conf",
    Path("/etc/nginx/conf.d/thebitlab-log-format.conf"):
        "/etc/thebitlab/current/nginx/thebitlab-log-format.conf",
    Path("/etc/nginx/sites-enabled/thebitlab.conf"):
        "/etc/thebitlab/current/nginx/thebitlab.conf",
    Path("/etc/logrotate.d/thebitlab"):
        "/etc/thebitlab/current/logrotate/thebitlab",
    Path("/etc/systemd/system/thebitlab.service"):
        "/etc/thebitlab/current/systemd/thebitlab.service",
}
_REQUIRED_NGINX_INCLUDES = (
    re.compile(r"(?m)^\s*include\s+/etc/nginx/modules-enabled/\*\.conf\s*;"),
    re.compile(r"(?m)^\s*include\s+/etc/nginx/conf\.d/\*\.conf\s*;"),
    re.compile(r"(?m)^\s*include\s+/etc/nginx/sites-enabled/\*\s*;"),
)
_SOURCE_MARKER = re.compile(r"^# configuration file (/.+):$")


class ActivationError(RuntimeError):
    """The host cannot safely activate or restore the candidate."""


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


def _restore_symlink(path: Path, saved: Mapping[str, Any]) -> None:
    if saved.get("present") is True:
        target = saved.get("target")
        if not isinstance(target, str) or not target:
            raise ActivationError(f"Stato rollback non valido per {path}")
        _replace_symlink(path, target)
    else:
        current = _symlink_state(path)
        if current["present"]:
            path.unlink()


def _directory_entries(path: Path) -> set[str]:
    try:
        return {entry.name for entry in path.iterdir()}
    except OSError as exc:
        raise ActivationError(f"Layout Ubuntu assente o non accessibile: {path}") from exc


def verify_ubuntu_layout() -> None:
    try:
        nginx_config = NGINX_CONFIG.read_text(encoding="utf-8")
    except OSError as exc:
        raise ActivationError(f"nginx.conf Ubuntu assente o non accessibile: {NGINX_CONFIG}") from exc
    if any(pattern.search(nginx_config) is None for pattern in _REQUIRED_NGINX_INCLUDES):
        raise ActivationError(
            "Layout nginx Ubuntu non supportato: include modules-enabled/conf.d/sites-enabled richiesti"
        )
    for directory in (
        Path("/etc/nginx/modules-enabled"),
        Path("/etc/nginx/conf.d"),
        Path("/etc/nginx/sites-enabled"),
        Path("/etc/logrotate.d"),
    ):
        if not directory.is_dir() or directory.is_symlink():
            raise ActivationError(f"Directory Ubuntu non supportata: {directory}")


def _check_managed_link(path: Path, expected: str, *, allow_absent: bool) -> None:
    state = _symlink_state(path)
    if not state["present"]:
        if allow_absent:
            return
        raise ActivationError(f"Symlink pilot atteso assente: {path}")
    if state["target"] != expected:
        raise ActivationError(f"Symlink pilot inatteso: {path}")


def _server_blocks(effective: str) -> list[tuple[str, str]]:
    source = ""
    blocks: list[tuple[str, str]] = []
    lines = effective.splitlines()
    index = 0
    while index < len(lines):
        marker = _SOURCE_MARKER.match(lines[index])
        if marker:
            source = marker.group(1)
            index += 1
            continue
        if re.match(r"^\s*server\s*\{", lines[index]):
            depth = lines[index].count("{") - lines[index].count("}")
            body = [lines[index]]
            index += 1
            while index < len(lines) and depth > 0:
                body.append(lines[index])
                depth += lines[index].count("{") - lines[index].count("}")
                index += 1
            if depth != 0:
                raise ActivationError("Output nginx -T con blocco server incompleto")
            blocks.append((source, "\n".join(body)))
            continue
        index += 1
    return blocks


def validate_effective_nginx(effective: str, manifest: Mapping[str, Any], *, activated: bool) -> None:
    blocks = _server_blocks(effective)
    pilot_site = "/etc/nginx/sites-enabled/thebitlab.conf"
    distro_site = "/etc/nginx/sites-enabled/default"
    allowed_sources = {pilot_site} if activated else {pilot_site, distro_site}
    unexpected = sorted({source or "<nginx.conf>" for source, _ in blocks if source not in allowed_sources})
    if unexpected:
        raise ActivationError("Vhost nginx unmanaged rilevato: " + ", ".join(unexpected))

    if not activated:
        if any(source == pilot_site for source, _ in blocks):
            pilot_blocks = [body for source, body in blocks if source == pilot_site]
            _validate_pilot_blocks(pilot_blocks)
        return

    if any(source != pilot_site for source, _ in blocks):
        raise ActivationError("La topologia dedicata attiva contiene vhost non pilot")
    pilot_blocks = [body for _, body in blocks]
    _validate_pilot_blocks(pilot_blocks)

    process_path = re.escape(manifest["origin"]["error_log"])
    process_directives = re.findall(
        rf"(?m)^\s*error_log\s+{process_path}\s+notice\s*;", effective
    )
    if len(process_directives) != 1:
        raise ActivationError("Error log process-level main-context assente o duplicato")


def _validate_pilot_blocks(blocks: list[str]) -> None:
    if len(blocks) != 4:
        raise ActivationError(f"Numero vhost pilot inatteso: {len(blocks)}")
    for block in blocks:
        directives = re.findall(r"(?m)^\s*error_log\s+([^;]+);", block)
        if directives != ["/dev/null"]:
            raise ActivationError("Vhost pilot capace di persistere errori request-context")
    combined = "\n".join(blocks)
    required_default_listens = (
        "listen 80 default_server;",
        "listen [::]:80 default_server;",
        "listen 443 ssl default_server;",
        "listen [::]:443 ssl default_server;",
    )
    if any(combined.count(directive) != 1 for directive in required_default_listens):
        raise ActivationError("Default server pilot IPv4/IPv6 assente, duplicato o ambiguo")
    if len(re.findall(r"(?m)^\s*listen\s+[^;]*default_server\s*;", combined)) != 4:
        raise ActivationError("Collisione o direttiva default_server inattesa")


def verify_host_preflight(bundle: Path) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise ActivationError("Il preflight host Ubuntu richiede root")
    verify_ubuntu_layout()
    manifest = verify_bundle(bundle)

    site_entries = _directory_entries(Path("/etc/nginx/sites-enabled"))
    if site_entries - {"default", "thebitlab.conf"}:
        raise ActivationError("sites-enabled contiene elementi unmanaged")
    conf_entries = _directory_entries(Path("/etc/nginx/conf.d"))
    if conf_entries - {"thebitlab-log-format.conf"}:
        raise ActivationError("conf.d contiene elementi unmanaged")

    default_state = _symlink_state(DISTRO_DEFAULT)
    distro_available = Path("/etc/nginx/sites-available/default")
    if default_state["present"]:
        try:
            target_is_distro_default = (
                DISTRO_DEFAULT.resolve(strict=True) == distro_available.resolve(strict=True)
                and distro_available.is_file()
            )
        except OSError:
            target_is_distro_default = False
        if not target_is_distro_default:
            raise ActivationError("Symlink default non punta a sites-available/default distro")
    for path, target in INTEGRATION_LINKS.items():
        _check_managed_link(path, target, allow_absent=True)

    effective = _run(["nginx", "-T", "-c", str(NGINX_CONFIG)])
    validate_effective_nginx(effective, manifest, activated=False)
    return manifest


def verify_bundle(bundle: Path) -> dict[str, Any]:
    bundle = bundle.resolve(strict=True)
    manifest_path = bundle / "manifest.normalized.json"
    lock_path = bundle / "deployment.lock.json"
    manifest = deployment.load_json(manifest_path)
    deployment.validate_manifest(manifest)
    deployment.validate_versioned_logging(manifest)
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        files = lock["files"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ActivationError("Lock deployment assente o non valido") from exc
    if not isinstance(files, dict) or set(files) != set(deployment.GENERATED_FILES):
        raise ActivationError("Lock deployment con inventario inatteso")
    for name, expected in files.items():
        path = bundle / name
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise ActivationError(f"Artifact bundle assente: {name}") from exc
        if not isinstance(expected, str) or actual != expected:
            raise ActivationError(f"Digest bundle non valido: {name}")
    return manifest


def prepare_log_directory(manifest: Mapping[str, Any]) -> None:
    import grp
    import pwd

    logging = manifest["logging"]
    directory = Path(logging["directory"])
    owner_id = pwd.getpwnam("root").pw_uid
    group_id = grp.getgrnam(logging["group"]).gr_gid
    file_owner_id = pwd.getpwnam(logging["owner"]).pw_uid
    directory.mkdir(mode=int(logging["directory_mode"], 8), parents=False, exist_ok=True)
    metadata = directory.lstat()
    if directory.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ActivationError(f"Directory log non regolare: {directory}")
    os.chown(directory, owner_id, group_id)
    os.chmod(directory, int(logging["directory_mode"], 8))

    for raw_path in (manifest["origin"]["access_log"], manifest["origin"]["error_log"]):
        path = Path(raw_path)
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, int(logging["file_mode"], 8))
        except OSError as exc:
            raise ActivationError(f"Log non creabile in sicurezza: {path}") from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise ActivationError(f"Log non regolare: {path}")
            os.fchown(descriptor, file_owner_id, group_id)
            os.fchmod(descriptor, int(logging["file_mode"], 8))
        finally:
            os.close(descriptor)


def _capture_state() -> dict[str, Any]:
    return {
        "schema_version": "thebitlab.pilot-activation-state.v1",
        "current": _symlink_state(CURRENT_LINK),
        "distro_default": _symlink_state(DISTRO_DEFAULT),
        "integration_links": {
            str(path): _symlink_state(path) for path in INTEGRATION_LINKS
        },
    }


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, indent=2, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _restore(state: Mapping[str, Any]) -> None:
    links = state.get("integration_links")
    if not isinstance(links, dict) or set(links) != {str(path) for path in INTEGRATION_LINKS}:
        raise ActivationError("Inventario rollback integration link non valido")
    for path in reversed(tuple(INTEGRATION_LINKS)):
        saved = links[str(path)]
        if not isinstance(saved, dict):
            raise ActivationError("Stato rollback integration link non valido")
        _restore_symlink(path, saved)
    current = state.get("current")
    distro_default = state.get("distro_default")
    if not isinstance(current, dict) or not isinstance(distro_default, dict):
        raise ActivationError("Stato rollback symlink non valido")
    _restore_symlink(CURRENT_LINK, current)
    _restore_symlink(DISTRO_DEFAULT, distro_default)


def _validate_activated(manifest: Mapping[str, Any]) -> None:
    _run(["nginx", "-t", "-c", str(NGINX_CONFIG)])
    effective = _run(["nginx", "-T", "-c", str(NGINX_CONFIG)])
    validate_effective_nginx(effective, manifest, activated=True)
    _run(["logrotate", "--debug", "/etc/logrotate.conf"])
    _run(["systemd-analyze", "verify", "/etc/systemd/system/thebitlab.service"])


def activate(bundle: Path, state_path: Path = STATE_FILE) -> None:
    bundle = bundle.resolve(strict=True)
    manifest = verify_host_preflight(bundle)
    previous = _capture_state()
    try:
        prepare_log_directory(manifest)
        if previous["distro_default"]["present"]:
            DISTRO_DEFAULT.unlink()
        _replace_symlink(CURRENT_LINK, str(bundle))
        for path, target in INTEGRATION_LINKS.items():
            _replace_symlink(path, target)
        _validate_activated(manifest)
        _write_state(state_path, previous)
    except Exception as exc:
        try:
            _restore(previous)
            _run(["nginx", "-t", "-c", str(NGINX_CONFIG)])
        except Exception as rollback_exc:
            raise ActivationError(
                f"Attivazione fallita e rollback non verificato: {rollback_exc}"
            ) from exc
        raise


def rollback(state_path: Path = STATE_FILE) -> None:
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError(f"Stato rollback assente o non valido: {state_path}") from exc
    if state.get("schema_version") != "thebitlab.pilot-activation-state.v1":
        raise ActivationError("Versione stato rollback non supportata")
    _restore(state)
    _run(["nginx", "-t", "-c", str(NGINX_CONFIG)])
    state_path.unlink()


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
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            verify_host_preflight(args.bundle)
        elif args.command == "activate":
            activate(args.bundle, args.state_file)
        else:
            rollback(args.state_file)
    except (ActivationError, deployment.DeploymentValidationError, KeyError, OSError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: pilot Ubuntu {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
