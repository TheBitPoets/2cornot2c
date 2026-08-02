"""Install the exact checksum-pinned Packer plugin for a classroom runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile


ROOT = Path(__file__).resolve().parent
LOCK = ROOT / "toolchain.lock.json"
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_BINARY_BYTES = 200 * 1024 * 1024
SOURCE = "github.com/hashicorp/vagrant"
PLATFORMS = {"darwin_arm64", "windows_amd64"}


def install(platform: str) -> None:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    plugin = payload["plugins"][SOURCE]
    version = str(plugin["version"])
    expected = str(plugin["archives"][platform])
    filename = f"packer-plugin-vagrant_v{version}_x5.0_{platform}.zip"
    url = (
        "https://github.com/hashicorp/packer-plugin-vagrant/releases/download/"
        f"v{version}/{filename}"
    )
    with tempfile.TemporaryDirectory(prefix="2cornot2c-packer-plugin-") as directory:
        archive = Path(directory) / filename
        digest = hashlib.sha256()
        size = 0
        with urlopen(url, timeout=30) as response, archive.open("wb") as output:
            if urlparse(response.geturl()).scheme != "https":
                raise RuntimeError("Redirect plugin Packer fuori da HTTPS.")
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("Archivio plugin Packer troppo grande.")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != expected:
            raise RuntimeError("Checksum plugin Packer non corrispondente al lock.")

        with zipfile.ZipFile(archive) as package:
            candidates = []
            for member in package.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise RuntimeError("Percorso non sicuro nell'archivio plugin.")
                if path.name.startswith("packer-plugin-vagrant_v") and not member.is_dir():
                    candidates.append(member)
            if len(candidates) != 1:
                raise RuntimeError("Binario plugin Packer non univoco.")
            member = candidates[0]
            if member.file_size <= 0 or member.file_size > MAX_BINARY_BYTES:
                raise RuntimeError("Dimensione binario plugin Packer non valida.")
            binary = Path(directory) / PurePosixPath(member.filename).name
            written = 0
            with package.open(member) as source, binary.open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    written += len(chunk)
                    if written > member.file_size:
                        raise RuntimeError("Binario plugin Packer oltre la dimensione dichiarata.")
                    output.write(chunk)
            if written != member.file_size:
                raise RuntimeError("Binario plugin Packer incompleto.")
            binary.chmod(0o700)

        completed = subprocess.run(
            (
                "packer",
                "plugins",
                "install",
                "--force",
                "--path",
                str(binary),
                SOURCE,
            ),
            check=False,
            timeout=60,
        )
        if completed.returncode != 0:
            raise RuntimeError("Installazione plugin Packer bloccato non riuscita.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    args = parser.parse_args()
    install(args.platform)


if __name__ == "__main__":
    main()
