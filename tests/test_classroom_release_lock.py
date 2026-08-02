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
                "candidate_version": "1.0.0",
                "active_release": None,
            },
            "macos-arm64-vmware": {
                "host": "macos-arm64",
                "provider": "vmware_desktop",
                "candidate_version": "1.0.0",
                "active_release": None,
            },
        },
    }


def active_release(target: str, version: str = "1.0.0") -> dict:
    return {
        "version": version,
        "manifest_url": (
            "https://github.com/TheBitPoets/2cornot2c/releases/download/"
            f"classroom-{target}-v{version}/release-manifest.json"
        ),
        "manifest_sha256": "a" * 64,
    }


def write_lock(tmp_path: Path, value: dict) -> Path:
    path = tmp_path / "lock.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_targets_have_independent_candidates(tmp_path: Path) -> None:
    path = write_lock(tmp_path, payload())
    windows = target_release(Host.WINDOWS_AMD64, Provider.VIRTUALBOX, path)
    macos = target_release(Host.MACOS_ARM64, Provider.VMWARE, path)

    assert not windows.active
    assert windows.candidate_version == "1.0.0"
    assert not macos.active
    assert windows.target_id != macos.target_id


def test_one_target_can_be_activated_without_the_other(tmp_path: Path) -> None:
    value = payload()
    windows = value["targets"]["windows-amd64-virtualbox"]
    windows["candidate_version"] = None
    windows["active_release"] = active_release("windows-amd64-virtualbox")
    releases = load_target_releases(write_lock(tmp_path, value))

    assert releases["windows-amd64-virtualbox"].active
    assert not releases["macos-arm64-vmware"].active


def test_candidate_does_not_disable_existing_active_release(tmp_path: Path) -> None:
    value = payload()
    windows = value["targets"]["windows-amd64-virtualbox"]
    windows["active_release"] = active_release("windows-amd64-virtualbox")
    windows["candidate_version"] = "1.1.0"
    release = target_release(
        Host.WINDOWS_AMD64, Provider.VIRTUALBOX, write_lock(tmp_path, value)
    )

    assert release.active
    assert release.version == "1.0.0"
    assert release.candidate_version == "1.1.0"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            candidate_version=None, active_release=None
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            active_release={"version": "1.0.0"}
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            active_release={
                **active_release("windows-amd64-virtualbox"),
                "manifest_url": "https://example.test/manifest.json",
            }
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            candidate_version="latest"
        ),
        lambda value: value["targets"]["windows-amd64-virtualbox"].update(
            active_release=active_release("windows-amd64-virtualbox")
        ),
    ),
)
def test_invalid_target_lock_fails_closed(tmp_path: Path, mutation) -> None:
    value = payload()
    mutation(value)
    with pytest.raises(ClassroomReleaseLockError):
        load_target_releases(write_lock(tmp_path, value))
