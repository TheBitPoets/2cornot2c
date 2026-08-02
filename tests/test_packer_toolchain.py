from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "packer" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plugin_archive(member: str = "packer-plugin-vagrant_v1.1.5_x5.0.exe") -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(member, b"verified plugin")
    return output.getvalue()


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def geturl(self) -> str:
        return "https://objects.githubusercontent.com/locked-plugin.zip"


def write_lock(path: Path, archive: bytes) -> None:
    path.write_text(
        json.dumps(
            {
                "plugins": {
                    "github.com/hashicorp/vagrant": {
                        "version": "1.1.5",
                        "archives": {
                            "windows_amd64": hashlib.sha256(archive).hexdigest(),
                            "darwin_arm64": "0" * 64,
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_locked_plugin_installer_verifies_archive_before_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_script("install_locked_plugin", "install-locked-plugin.py")
    archive = plugin_archive()
    lock = tmp_path / "toolchain.lock.json"
    write_lock(lock, archive)
    calls = []
    monkeypatch.setattr(module, "LOCK", lock)
    monkeypatch.setattr(module, "urlopen", lambda url, timeout: Response(archive))
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command) or SimpleNamespace(returncode=0),
    )

    module.install("windows_amd64")

    assert len(calls) == 1
    assert calls[0][:5] == (
        "packer",
        "plugins",
        "install",
        "--force",
        "--path",
    )
    assert calls[0][-1] == "github.com/hashicorp/vagrant"


def test_locked_plugin_installer_rejects_archive_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_script("install_locked_plugin_unsafe", "install-locked-plugin.py")
    archive = plugin_archive("../packer-plugin-vagrant_v1.1.5_x5.0")
    lock = tmp_path / "toolchain.lock.json"
    write_lock(lock, archive)
    monkeypatch.setattr(module, "LOCK", lock)
    monkeypatch.setattr(module, "urlopen", lambda url, timeout: Response(archive))

    with pytest.raises(RuntimeError, match="non sicuro"):
        module.install("windows_amd64")


def test_toolchain_lock_schema_is_accepted() -> None:
    module = load_script("verify_toolchain", "verify-toolchain.py")

    assert module.load_lock() == (
        "1.16.0",
        "github.com/hashicorp/vagrant",
        "1.1.5",
    )
