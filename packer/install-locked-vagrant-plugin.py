"""Install the checksum-pinned VMware Vagrant plugin in isolated VAGRANT_HOME."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
LOCK = ROOT / "toolchain.lock.json"
MAX_GEM_BYTES = 50 * 1024 * 1024


def install() -> None:
    if not os.environ.get("VAGRANT_HOME"):
        raise RuntimeError("VAGRANT_HOME isolato non configurato.")
    payload = json.loads(LOCK.read_text(encoding="utf-8"))
    plugin = payload["vagrant_plugins"]["vagrant-vmware-desktop"]
    version = str(plugin["version"])
    expected = str(plugin["sha256"])
    filename = f"vagrant-vmware-desktop-{version}.gem"
    url = f"https://rubygems.org/downloads/{filename}"

    with tempfile.TemporaryDirectory(prefix="2cornot2c-vagrant-plugin-") as directory:
        gem = Path(directory) / filename
        digest = hashlib.sha256()
        size = 0
        with urlopen(url, timeout=30) as response, gem.open("wb") as output:
            if urlparse(response.geturl()).scheme != "https":
                raise RuntimeError("Redirect plugin Vagrant fuori da HTTPS.")
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_GEM_BYTES:
                    raise RuntimeError("Plugin Vagrant troppo grande.")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if size <= 0 or digest.hexdigest() != expected:
            raise RuntimeError("Checksum plugin Vagrant non corrispondente al lock.")

        completed = subprocess.run(
            ("vagrant", "plugin", "install", str(gem)),
            check=False,
            timeout=120,
        )
        if completed.returncode != 0:
            raise RuntimeError("Installazione plugin Vagrant VMware non riuscita.")


if __name__ == "__main__":
    install()
    print("Plugin Vagrant VMware verificato e installato.")
