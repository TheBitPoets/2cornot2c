"""Genera il manifest immutabile delle box Packer collaudate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def digest(path: Path) -> tuple[str, int]:
    checksum = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            checksum.update(chunk)
            size += len(chunk)
    return checksum.hexdigest(), size


def artifact(
    *,
    path: Path,
    version: str,
    repository: str,
    name: str,
    host: str,
    provider: str,
    architecture: str,
    filename: str,
) -> dict[str, object]:
    checksum, size = digest(path)
    tag = f"classroom-v{version}"
    return {
        "name": filename,
        "host": host,
        "provider": provider,
        "architecture": architecture,
        "box_name": f"2cornot2c/ubuntu-24.04-{provider}-{architecture}-{version}",
        "url": (
            f"https://github.com/{repository}/releases/download/{tag}/{filename}"
        ),
        "sha256": checksum,
        "size_bytes": size,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--version", required=True)
    result.add_argument("--repository", default="TheBitPoets/2cornot2c")
    result.add_argument("--vmware", type=Path, required=True)
    result.add_argument("--virtualbox", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    return result


def main() -> int:
    args = parser().parse_args()
    if not VERSION_RE.fullmatch(args.version):
        raise SystemExit("La versione deve essere SemVer numerica, per esempio 1.0.0.")
    for path in (args.vmware, args.virtualbox):
        if not path.is_file():
            raise SystemExit(f"Box non trovata: {path}")
    payload = {
        "schema_version": "2cornot2c.classroom-images.v1",
        "release": args.version,
        "artifacts": [
            artifact(
                path=args.vmware,
                version=args.version,
                repository=args.repository,
                name="VMware ARM64",
                host="macos-arm64",
                provider="vmware_desktop",
                architecture="arm64",
                filename="2cornot2c-macos-arm64-vmware.box",
            ),
            artifact(
                path=args.virtualbox,
                version=args.version,
                repository=args.repository,
                name="VirtualBox AMD64",
                host="windows-amd64",
                provider="virtualbox",
                architecture="amd64",
                filename="2cornot2c-windows-amd64-virtualbox.box",
            ),
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
