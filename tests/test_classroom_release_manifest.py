from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from installer.artifacts import load_release
from installer.model import Host, Provider


def test_release_manifest_generator_emits_installable_contract(tmp_path: Path) -> None:
    vmware = tmp_path / "vmware.box"
    virtualbox = tmp_path / "virtualbox.box"
    output = tmp_path / "release-manifest.json"
    vmware.write_bytes(b"vmware")
    virtualbox.write_bytes(b"virtualbox")
    script = (
        Path(__file__).resolve().parents[1]
        / "packer"
        / "create-release-manifest.py"
    )

    completed = subprocess.run(
        (
            sys.executable,
            str(script),
            "--version",
            "1.2.3",
            "--repository",
            "TheBitPoets/2cornot2c",
            "--vmware",
            str(vmware),
            "--virtualbox",
            str(virtualbox),
            "--output",
            str(output),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    release = load_release(output)
    assert release.version == "1.2.3"
    assert {(item.host, item.provider) for item in release.artifacts} == {
        (Host.MACOS_ARM64, Provider.VMWARE),
        (Host.WINDOWS_AMD64, Provider.VIRTUALBOX),
    }
    assert all(
        item.url.startswith(
            "https://github.com/TheBitPoets/2cornot2c/releases/download/"
        )
        for item in release.artifacts
    )
