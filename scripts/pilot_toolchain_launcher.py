#!/usr/bin/python3 -IB
"""Verify the externally pinned pilot toolchain and enter it with isolated Python."""

from __future__ import annotations

import sys

# Reject explicit non-isolated interpreter invocation before any shadowable import.
if __name__ == "__main__" and not (
    sys.flags.isolated
    and sys.flags.ignore_environment
    and sys.flags.no_user_site
    and getattr(sys.flags, "safe_path", False)
    and getattr(sys.flags, "dont_write_bytecode", False)
):
    print("ERRORE: il launcher richiede il proprio entrypoint Python -I -B", file=sys.stderr)
    raise SystemExit(2)

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


CANONICAL_LAUNCHER = Path("/usr/sbin/thebitlab-pilot-activate")
TOOLS_ROOT = Path("/usr/lib/thebitlab/pilot-tools")
TRUST_PIN = Path("/etc/thebitlab/trust/pilot-toolchain.json")
PYTHON = Path("/usr/bin/python3")
MANIFEST_NAME = "pilot-toolchain-manifest.json"
ACTIVATOR = "scripts/pilot_ubuntu_activation.py"
EXPECTED_FILES = frozenset(
    {
        "scripts/__init__.py",
        "scripts/nginx_config_ast.py",
        "scripts/pilot_environment.py",
        ACTIVATOR,
        "scripts/pilot_trusted_activation_fence.py",
        "scripts/pilot_native_execution_closure.py",
        "scripts/pilot_ubuntu_reviewed_executables.py",
        "scripts/pilot_ubuntu_reviewed_native_code.py",
        "scripts/validate_pilot_deployment.py",
        "schemas/pilot-deployment.schema.json",
        "schemas/pilot-deployment-v1-legacy.schema.json",
        "schemas/pilot-environment.schema.json",
        "deploy/pilot/templates/thebitlab-process-error-log.conf.template",
        "deploy/pilot/templates/thebitlab-log-format.conf.template",
        "deploy/pilot/templates/thebitlab-nginx.conf.template",
        "deploy/pilot/templates/thebitlab-logrotate.conf.template",
        "deploy/pilot/templates/thebitlab.service.template",
        "deploy/pilot/legacy-v1/thebitlab-log-format.conf.template",
        "deploy/pilot/legacy-v1/thebitlab-nginx.conf.template",
        "deploy/pilot/legacy-v1/thebitlab.service.template",
    }
)
_ID_RE = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")


class ToolchainError(RuntimeError):
    """The production activation trust chain is absent or invalid."""


def _metadata(path: Path, *, directory: bool, require_root_owner: bool) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ToolchainError(f"trusted path assente: {path}") from exc
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if path.is_symlink() or not expected(metadata.st_mode):
        raise ToolchainError(f"trusted path non regolare: {path}")
    if os.name != "nt" and require_root_owner and metadata.st_uid != 0:
        raise ToolchainError(f"trusted path non root-owned: {path}")
    if os.name != "nt" and metadata.st_mode & 0o022:
        raise ToolchainError(f"trusted path scrivibile da group/other: {path}")
    if not directory and getattr(metadata, "st_nlink", 1) != 1:
        raise ToolchainError(f"trusted file con hardlink inatteso: {path}")
    return metadata


def _trusted_ancestry(path: Path, *, directory: bool, require_root_owner: bool) -> None:
    if not path.is_absolute() or path != Path(os.path.abspath(path)):
        raise ToolchainError(f"trusted path non assoluto/canonico: {path}")
    if require_root_owner:
        current = Path(path.anchor)
        _metadata(current, directory=True, require_root_owner=True)
        for part in path.parts[1:-1]:
            current /= part
            _metadata(current, directory=True, require_root_owner=True)
    _metadata(path, directory=directory, require_root_owner=require_root_owner)
    if path.resolve(strict=True) != path:
        raise ToolchainError(f"trusted path risolto tramite symlink: {path}")


def _load_strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ToolchainError(f"chiave JSON duplicata: {path}")
            result[key] = value
        return result

    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ToolchainError(f"JSON trusted non valido: {path}") from exc
    if not isinstance(payload, dict):
        raise ToolchainError(f"oggetto JSON trusted richiesto: {path}")
    return payload, raw


def verify_installation(
    *,
    pin_path: Path = TRUST_PIN,
    tools_root: Path = TOOLS_ROOT,
    launcher_path: Path = CANONICAL_LAUNCHER,
    require_root_owner: bool = True,
) -> tuple[Path, Mapping[str, Any]]:
    """Verify external pin, launcher, exact toolchain inventory, metadata and digests."""

    _trusted_ancestry(pin_path, directory=False, require_root_owner=require_root_owner)
    _trusted_ancestry(launcher_path, directory=False, require_root_owner=require_root_owner)
    pin, _ = _load_strict_json(pin_path)
    required_pin = {
        "schema_version",
        "toolchain_id",
        "toolchain_manifest_sha256",
        "launcher_sha256",
        "release_commit",
    }
    if set(pin) != required_pin or pin.get("schema_version") != "thebitlab.pilot-toolchain-pin.v1":
        raise ToolchainError("external trust pin con struttura inattesa")
    toolchain_id = pin.get("toolchain_id")
    if not isinstance(toolchain_id, str) or _ID_RE.fullmatch(toolchain_id) is None:
        raise ToolchainError("toolchain id esterno non canonico")
    for key in ("toolchain_manifest_sha256", "launcher_sha256"):
        if not isinstance(pin.get(key), str) or _SHA256_RE.fullmatch(pin[key]) is None:
            raise ToolchainError(f"digest esterno non canonico: {key}")
    if not isinstance(pin.get("release_commit"), str) or _COMMIT_RE.fullmatch(pin["release_commit"]) is None:
        raise ToolchainError("release commit esterno non canonico")
    if hashlib.sha256(launcher_path.read_bytes()).hexdigest() != pin["launcher_sha256"]:
        raise ToolchainError("launcher digest diverso dal pin esterno")

    toolchain = tools_root / toolchain_id
    _trusted_ancestry(toolchain, directory=True, require_root_owner=require_root_owner)
    manifest_path = toolchain / MANIFEST_NAME
    _metadata(manifest_path, directory=False, require_root_owner=require_root_owner)
    manifest, manifest_raw = _load_strict_json(manifest_path)
    if hashlib.sha256(manifest_raw).hexdigest() != pin["toolchain_manifest_sha256"]:
        raise ToolchainError("toolchain manifest digest diverso dal pin esterno")
    required_manifest = {"schema_version", "toolchain_id", "release_commit", "files"}
    if (
        set(manifest) != required_manifest
        or manifest.get("schema_version") != "thebitlab.pilot-toolchain.v1"
        or manifest.get("toolchain_id") != toolchain_id
        or manifest.get("release_commit") != pin["release_commit"]
    ):
        raise ToolchainError("toolchain manifest non coerente con il pin esterno")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != EXPECTED_FILES:
        raise ToolchainError("inventario toolchain dichiarato inatteso")

    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for root_name, directory_names, file_names in os.walk(toolchain, followlinks=False):
        root_path = Path(root_name)
        for name in directory_names:
            path = root_path / name
            _metadata(path, directory=True, require_root_owner=require_root_owner)
            actual_directories.add(path.relative_to(toolchain).as_posix())
        for name in file_names:
            path = root_path / name
            _metadata(path, directory=False, require_root_owner=require_root_owner)
            actual_files.add(path.relative_to(toolchain).as_posix())
    if actual_files != EXPECTED_FILES | {MANIFEST_NAME}:
        raise ToolchainError("file set installato inatteso")
    expected_directories = {
        str(parent)
        for name in EXPECTED_FILES
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    if actual_directories != expected_directories:
        raise ToolchainError("directory set installato inatteso")
    for relative_name, expected_digest in files.items():
        if not isinstance(expected_digest, str) or _SHA256_RE.fullmatch(expected_digest) is None:
            raise ToolchainError(f"digest manifest non canonico: {relative_name}")
        actual_digest = hashlib.sha256((toolchain / relative_name).read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            raise ToolchainError(f"toolchain file modificato: {relative_name}")
    return toolchain, pin


def isolated_command(toolchain: Path, arguments: Sequence[str], *, python: Path = PYTHON) -> list[str]:
    bootstrap = (
        "import runpy,sys;"
        "root=sys.argv.pop(1);"
        "sys.path.insert(0,root);"
        "runpy.run_module('scripts.pilot_ubuntu_activation',run_name='__main__')"
    )
    return [str(python), "-I", "-B", "-c", bootstrap, str(toolchain), *arguments]


def sanitized_environment(toolchain: Path, pin: Mapping[str, Any]) -> dict[str, str]:
    environment = {
        "HOME": "/root",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "THEBITLAB_TRUSTED_TOOLCHAIN_ID": str(pin["toolchain_id"]),
        "THEBITLAB_TRUSTED_TOOLCHAIN_ROOT": str(toolchain),
    }
    # Test-only crash injection requires an explicit root-owned ephemeral-host interlock.
    interlock = Path("/run/thebitlab-ephemeral-activation-test")
    if os.environ.get("THEBITLAB_EPHEMERAL_CRASH_TEST") == "1" and interlock.exists():
        metadata = interlock.lstat()
        if (
            not interlock.is_symlink()
            and stat.S_ISREG(metadata.st_mode)
            and metadata.st_uid == 0
            and stat.S_IMODE(metadata.st_mode) == 0o600
            and interlock.read_text(encoding="ascii") == "ephemeral-only\n"
        ):
            environment["THEBITLAB_EPHEMERAL_CRASH_TEST"] = "1"
            environment["THEBITLAB_ACTIVATION_CRASH_POINT"] = os.environ.get(
                "THEBITLAB_ACTIVATION_CRASH_POINT", ""
            )
            environment["THEBITLAB_ACTIVATION_CRASH_FENCE_NAME"] = os.environ.get(
                "THEBITLAB_ACTIVATION_CRASH_FENCE_NAME", ""
            )
    return environment


def main(argv: list[str] | None = None) -> int:
    actual_launcher = Path(__file__).absolute()
    if actual_launcher != CANONICAL_LAUNCHER:
        print("ERRORE: production activation consentita solo dal launcher installato", file=sys.stderr)
        return 2
    try:
        toolchain, pin = verify_installation(launcher_path=actual_launcher)
        if os.geteuid() != 0:
            raise ToolchainError("production activation richiede root")
        result = subprocess.run(
            isolated_command(toolchain, sys.argv[1:] if argv is None else argv),
            cwd="/",
            env=sanitized_environment(toolchain, pin),
            check=False,
        )
        return result.returncode
    except (OSError, subprocess.SubprocessError, ToolchainError) as exc:
        print(f"ERRORE: trusted activation toolchain: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
