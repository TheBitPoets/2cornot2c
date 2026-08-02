from __future__ import annotations

import json
from pathlib import Path

import pytest

from installer.classroom_release_lock import (
    ClassroomReleaseLockError,
    load_target_releases,
    target_release,
)
from installer.model import Host, Provider


def payload() -> dict:
    return {
        "schema_version": "2cornot2c.classroom-release-lock.v1",
        "targets": {
            "windows-amd64-virtualbox": {
                "host": "windows-amd64",
                "provider": "virtualbox",
                "state": "pending",
                "version": "1.0.0",
                "manifest_url": (
                    "https://github.com/TheBitPoets/2cornot2c/releases/download/"
                    "classroom-windows-amd64-virtualbox-v1.0.0/"
                    "release-manifest.json"
                ),
                "manifest_sha256": None,
            },
            "macos-arm64-vmware": {
                "host": "macos-arm64",
                "provider": "vmware_desktop",
                "state": "pending",
                "version": "1.0.0",
                "manifest_url": (
                    "https://github.com/TheBitPoets/2cornot2c/releases/download/"
                    "classroom-macos-arm64-vmware-v1.0.0/"
                    "release-manifest.json"
                ),
                "manifest_sha256": None,
            },
        },
    }


def write_lock(tmp_path: Path, value: dict) -> Path:
    path = tmp_path / "lock.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_targets_are_independently_pending(tmp_path: Path) -> None:
    path = write_lock(tmp_path, payload())
    windows = target_release(Host.WINDOWS_AMD64, Provider.VIRTUALBOX, path)
    macos = target_release(Host.MACOS_ARM64, Provider.VMWARE, path)

    assert not windows.active
    assert not macos.active
    assert windows.target_id != macos.target_id


def test_one_target_can_be_activated_without_the_other(tmp_path: Path) -> None:
    value = payload()
    windows = value["targets"]["windows-amd64-virtualbox"]
    windows["state"] = "active"
    windows["manifest_sha256"] = "a" * 64
    releases = load_target_releases(write_lock(tmp_path, value))

    assert releases["windows-amd64-virtualbox"].active
    assert not releases["macos-arm64-vmware"].active


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            state="active", manifest_sha256=None
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            state="pending", manifest_sha256="a" * 64
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            manifest_url="https://example.test/manifest.json"
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            version="latest"
        ),
    ),
)
def test_invalid_target_lock_fails_closed(tmp_path: Path, mutation) -> None:
    value = payload()
    mutation(value)
    with pytest.raises(ClassroomReleaseLockError):
        load_target_releases(write_lock(tmp_path, value))
