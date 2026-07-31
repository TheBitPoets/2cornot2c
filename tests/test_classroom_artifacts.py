from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path

import pytest

from installer.artifacts import (
    ArtifactError,
    MAX_BOX_BYTES,
    download_box,
    load_release,
    select_artifact,
    verify_box,
)
from installer.model import Host, Provider


BOX_CONTENT = b"verified classroom box"


def manifest_payload() -> dict:
    return {
        "schema_version": "2cornot2c.classroom-images.v1",
        "release": "0.1.0",
        "artifacts": [
            {
                "name": "VMware ARM64",
                "host": "macos-arm64",
                "provider": "vmware_desktop",
                "architecture": "arm64",
                "box_name": "2cornot2c/test-vmware-0.1.0",
                "url": "https://downloads.example.test/vmware.box",
                "sha256": hashlib.sha256(BOX_CONTENT).hexdigest(),
                "size_bytes": len(BOX_CONTENT),
            }
        ],
    }


def write_manifest(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "release.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_manifest_selects_exact_host_provider(tmp_path: Path) -> None:
    release = load_release(write_manifest(tmp_path, manifest_payload()))

    artifact = select_artifact(release, Host.MACOS_ARM64, Provider.VMWARE)

    assert artifact.architecture == "arm64"
    assert artifact.size_bytes == len(BOX_CONTENT)


def test_manifest_rejects_http_and_wrong_architecture(tmp_path: Path) -> None:
    payload = manifest_payload()
    payload["artifacts"][0]["url"] = "http://downloads.example.test/vmware.box"
    with pytest.raises(ArtifactError, match="HTTPS"):
        load_release(write_manifest(tmp_path, payload))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("box_name", "../outside", "Nome box Vagrant"),
        ("box_name", "--force", "Nome box Vagrant"),
        (
            "url",
            "https://downloads.example.test/not-a-box.txt",
            "Nome file box",
        ),
        (
            "url",
            "https://downloads.example.test/%2e%2e%2foutside.box",
            "Nome file box",
        ),
    ],
)
def test_manifest_rejects_unsafe_box_identifiers(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    payload = manifest_payload()
    payload["artifacts"][0][field] = value

    with pytest.raises(ArtifactError, match=message):
        load_release(write_manifest(tmp_path, payload))


def test_manifest_rejects_box_too_large_for_github_release(tmp_path: Path) -> None:
    payload = manifest_payload()
    payload["artifacts"][0]["size_bytes"] = MAX_BOX_BYTES + 1

    with pytest.raises(ArtifactError, match="Dimensione"):
        load_release(write_manifest(tmp_path, payload))

    payload = manifest_payload()
    payload["artifacts"][0]["architecture"] = "amd64"
    with pytest.raises(ArtifactError, match="Architettura"):
        load_release(write_manifest(tmp_path, payload))


def test_verify_box_rejects_changed_content(tmp_path: Path) -> None:
    release = load_release(write_manifest(tmp_path, manifest_payload()))
    artifact = release.artifacts[0]
    box = tmp_path / "classroom.box"
    box.write_bytes(b"tampered classroom box")

    with pytest.raises(ArtifactError):
        verify_box(box, artifact)


class FakeResponse(BytesIO):
    def geturl(self) -> str:
        return "https://cdn.example.test/classroom.box"


def test_download_is_verified_and_atomically_published(tmp_path: Path) -> None:
    release = load_release(write_manifest(tmp_path, manifest_payload()))
    destination = tmp_path / "cache" / "classroom.box"

    result = download_box(
        release.artifacts[0],
        destination,
        opener=lambda url: FakeResponse(BOX_CONTENT),
    )

    assert result == destination
    assert destination.read_bytes() == BOX_CONTENT
    assert list(destination.parent.glob("*.part")) == []


def test_download_does_not_publish_invalid_file(tmp_path: Path) -> None:
    release = load_release(write_manifest(tmp_path, manifest_payload()))
    destination = tmp_path / "classroom.box"

    with pytest.raises(ArtifactError):
        download_box(
            release.artifacts[0],
            destination,
            opener=lambda url: FakeResponse(b"invalid"),
        )

    assert not destination.exists()
