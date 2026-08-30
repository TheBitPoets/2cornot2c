#!/usr/bin/env python3
"""Build an unprivileged staging tree for separately approved pilot tools."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path


TOOLCHAIN_FILES = (
    "scripts/__init__.py",
    "scripts/nginx_config_ast.py",
    "scripts/pilot_environment.py",
    "scripts/pilot_ubuntu_activation.py",
    "scripts/pilot_systemd_generator_orchestrator.py",
    "scripts/pilot_trusted_activation_fence.py",
    "scripts/pilot_native_execution_closure.py",
    "scripts/pilot_ubuntu_reviewed_executables.py",
    "scripts/pilot_ubuntu_reviewed_native_code.py",
    "scripts/pilot_ubuntu_loader_lookup_policy.py",
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
)
MANIFEST_NAME = "pilot-toolchain-manifest.json"
_ID_RE = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?")
_SHA_RE = re.compile(r"[0-9a-f]{40}")


def canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_toolchain(source_root: Path, output: Path, toolchain_id: str, release_commit: str) -> dict[str, object]:
    """Create staging only; the result is not trusted until separately installed and pinned."""

    source_root = source_root.resolve(strict=True)
    if _ID_RE.fullmatch(toolchain_id) is None:
        raise ValueError("toolchain id non canonico")
    if _SHA_RE.fullmatch(release_commit) is None:
        raise ValueError("release commit non canonico")
    if output.exists() or output.is_symlink():
        raise ValueError("output toolchain deve essere nuovo")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        hashes: dict[str, str] = {}
        for relative_name in TOOLCHAIN_FILES:
            source = source_root / relative_name
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"source toolchain non regolare: {relative_name}")
            target = temporary / relative_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            hashes[relative_name] = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest: dict[str, object] = {
            "schema_version": "thebitlab.pilot-toolchain.v1",
            "toolchain_id": toolchain_id,
            "release_commit": release_commit,
            "files": hashes,
        }
        (temporary / MANIFEST_NAME).write_bytes(canonical_json(manifest))
        temporary.replace(output)
        return manifest
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--toolchain-id", required=True)
    parser.add_argument("--release-commit", required=True)
    args = parser.parse_args(argv)
    try:
        manifest = build_toolchain(
            args.source_root, args.output, args.toolchain_id, args.release_commit
        )
        digest = hashlib.sha256((args.output / MANIFEST_NAME).read_bytes()).hexdigest()
    except (OSError, ValueError) as exc:
        print(f"ERRORE: {exc}")
        return 2
    print(
        json.dumps(
            {
                "staging_only": True,
                "toolchain_id": manifest["toolchain_id"],
                "toolchain_manifest_sha256": digest,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
