"""Install the exact checksum-pinned Packer binary in an isolated directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import zipfile


ROOT = Path(__file__).resolve().parent
LOCK = ROOT / "toolchain.lock.json"
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_BINARY_BYTES = 200 * 1024 * 1024
PLATFORMS = {"darwin_arm64", "windows_amd64"}


def install(platform: str, destination: Path) -> Path:
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    version = str(payload["packer_version"])
    expected = str(payload["packer_archives"][platform])
    filename = f"packer_{version}_{platform}.zip"
    url = f"https://releases.hashicorp.com/packer/{version}/{filename}"
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)

    with tempfile.TemporaryDirectory(prefix="2cornot2c-packer-") as directory:
        archive_path = Path(directory) / filename
        digest = hashlib.sha256()
        size = 0
        with urlopen(url, timeout=30) as response, archive_path.open("wb") as output:
            if urlparse(response.geturl()).scheme != "https":
                raise RuntimeError("Redirect Packer fuori da HTTPS.")
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("Archivio Packer troppo grande.")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != expected:
            raise RuntimeError("Checksum Packer non corrispondente al lock.")

        with zipfile.ZipFile(archive_path) as package:
            candidates = []
            for member in package.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise RuntimeError("Percorso non sicuro nell'archivio Packer.")
                if path.name in {"packer", "packer.exe"} and not member.is_dir():
                    candidates.append(member)
            if len(candidates) != 1:
                raise RuntimeError("Binario Packer non univoco.")
            member = candidates[0]
            if member.file_size <= 0 or member.file_size > MAX_BINARY_BYTES:
                raise RuntimeError("Dimensione binario Packer non valida.")
            binary = destination / PurePosixPath(member.filename).name
            written = 0
            with package.open(member) as source, binary.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    written += len(chunk)
                    if written > member.file_size:
                        raise RuntimeError("Binario Packer oltre la dimensione dichiarata.")
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())
            if written != member.file_size:
                raise RuntimeError("Binario Packer incompleto.")
            binary.chmod(0o700)
    return binary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=sorted(PLATFORMS))
    parser.add_argument("--destination", required=True, type=Path)
    arguments = parser.parse_args()
    print(install(arguments.platform, arguments.destination))


if __name__ == "__main__":
    main()
