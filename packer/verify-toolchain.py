"""Fail closed unless the Packer executable and required plugin match the lock."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent
LOCK = ROOT / "toolchain.lock.json"
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_lock(path: Path = LOCK) -> tuple[str, str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {
        "schema_version",
        "packer_version",
        "plugins",
        "vagrant_plugins",
    }:
        raise RuntimeError("Schema lock Packer non valido.")
    if payload["schema_version"] != "2cornot2c.packer-toolchain.v1":
        raise RuntimeError("Versione lock Packer non supportata.")
    packer_version = payload["packer_version"]
    plugins = payload["plugins"]
    if not isinstance(plugins, dict) or set(plugins) != {
        "github.com/hashicorp/vagrant"
    }:
        raise RuntimeError("Plugin Packer non validi.")
    plugin = plugins["github.com/hashicorp/vagrant"]
    if set(plugin) != {"version", "archives"}:
        raise RuntimeError("Campi plugin Packer non validi.")
    plugin_version = plugin["version"]
    archives = plugin["archives"]
    if not isinstance(archives, dict) or set(archives) != {
        "darwin_arm64",
        "windows_amd64",
    }:
        raise RuntimeError("Archivi plugin Packer non validi.")
    if not VERSION_RE.fullmatch(str(packer_version)):
        raise RuntimeError("Versione Packer non valida.")
    if not VERSION_RE.fullmatch(str(plugin_version)):
        raise RuntimeError("Versione plugin Packer non valida.")
    if any(not SHA256_RE.fullmatch(str(value)) for value in archives.values()):
        raise RuntimeError("Checksum plugin Packer non valido.")
    vagrant_plugins = payload["vagrant_plugins"]
    if not isinstance(vagrant_plugins, dict) or set(vagrant_plugins) != {
        "vagrant-vmware-desktop"
    }:
        raise RuntimeError("Plugin Vagrant non validi.")
    vmware = vagrant_plugins["vagrant-vmware-desktop"]
    if set(vmware) != {"version", "sha256"}:
        raise RuntimeError("Campi plugin Vagrant non validi.")
    if not VERSION_RE.fullmatch(str(vmware["version"])):
        raise RuntimeError("Versione plugin Vagrant non valida.")
    if not SHA256_RE.fullmatch(str(vmware["sha256"])):
        raise RuntimeError("Checksum plugin Vagrant non valido.")
    return str(packer_version), "github.com/hashicorp/vagrant", str(plugin_version)


def _run(command: tuple[str, ...]) -> str:
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Comando toolchain fallito: {' '.join(command)}: "
            f"{(completed.stderr or completed.stdout)[-1000:]}"
        )
    return f"{completed.stdout}\n{completed.stderr}"


def verify(*, require_vagrant_vmware: bool = False) -> None:
    packer_version, source, plugin_version = load_lock()
    version_output = _run(("packer", "version"))
    if not re.search(rf"v{re.escape(packer_version)}(?:\s|$)", version_output):
        raise RuntimeError(f"Packer {packer_version} richiesto.")
    installed = _run(("packer", "plugins", "installed")).replace("\\", "/")
    expected = rf"{re.escape(source)}.*packer-plugin-vagrant_v{re.escape(plugin_version)}_"
    if not re.search(expected, installed):
        raise RuntimeError(f"Plugin {source} {plugin_version} richiesto.")
    if require_vagrant_vmware:
        payload = json.loads(LOCK.read_text(encoding="utf-8"))
        version = payload["vagrant_plugins"]["vagrant-vmware-desktop"]["version"]
        vagrant_plugins = _run(("vagrant", "plugin", "list"))
        if not re.search(
            rf"(?m)^vagrant-vmware-desktop \({re.escape(version)},", vagrant_plugins
        ):
            raise RuntimeError(
                f"Plugin Vagrant VMware {version} richiesto nell'home isolato."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-vagrant-vmware", action="store_true")
    arguments = parser.parse_args()
    verify(require_vagrant_vmware=arguments.require_vagrant_vmware)
    print("Toolchain Packer verificata.")
