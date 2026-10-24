"""Genera il manifest immutabile di una box Packer collaudata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
MAX_RELEASE_ASSET_BYTES = 2 * 1024 * 1024 * 1024 - 1
TARGETS = {
    "windows-amd64-virtualbox": {
        "name": "VirtualBox AMD64",
        "host": "windows-amd64",
        "provider": "virtualbox",
        "architecture": "amd64",
        "filename": "2cornot2c-windows-amd64-virtualbox.box",
    },
    "macos-arm64-vmware": {
        "name": "VMware ARM64",
        "host": "macos-arm64",
        "provider": "vmware_desktop",
        "architecture": "arm64",
        "filename": "2cornot2c-macos-arm64-vmware.box",
    },
}


def digest(path: Path) -> tuple[str, int]:
    checksum = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            checksum.update(chunk)
            size += len(chunk)
    return checksum.hexdigest(), size


def artifact(
    *, path: Path, version: str, repository: str, target: str
) -> dict[str, object]:
    config = TARGETS[target]
    checksum, size = digest(path)
    if size > MAX_RELEASE_ASSET_BYTES:
        raise SystemExit(f"La box supera il limite GitHub Releases di 2 GiB: {path}")
    tag = f"classroom-{target}-v{version}"
    provider = config["provider"]
    architecture = config["architecture"]
    return {
        "name": config["name"],
        "host": config["host"],
        "provider": provider,
        "architecture": architecture,
        "box_name": f"2cornot2c/ubuntu-24.04-{provider}-{architecture}-{version}",
        "url": (
            f"https://github.com/{repository}/releases/download/"
            f"{tag}/{config['filename']}"
        ),
        "sha256": checksum,
        "size_bytes": size,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--version", required=True)
    result.add_argument("--repository", default="TheBitPoets/2cornot2c")
    result.add_argument("--target", choices=tuple(TARGETS), required=True)
    result.add_argument("--box", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if not VERSION_RE.fullmatch(args.version):
        raise SystemExit("La versione deve essere SemVer numerica, per esempio 1.0.0.")
    if not args.box.is_file():
        raise SystemExit(f"Box non trovata: {args.box}")
    payload = {
        "schema_version": "2cornot2c.classroom-images.v1",
        "release": args.version,
        "artifacts": [
            artifact(
                path=args.box,
                version=args.version,
                repository=args.repository,
                target=args.target,
            )
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
