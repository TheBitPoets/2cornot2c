from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path

import pytest

from installer import classroom_images
from installer.artifacts import BoxArtifact
from installer.model import Host, Provider
from installer.vagrant_box import VagrantResult


CONTENT = b"verified packer box"


def artifact() -> BoxArtifact:
    return BoxArtifact(
        "2cornot2c-windows-amd64-virtualbox.box",
        Host.WINDOWS_AMD64,
        Provider.VIRTUALBOX,
        "amd64",
        "2cornot2c/ubuntu-24.04-virtualbox-amd64-1.0.0",
        "https://downloads.example.test/classroom.box",
        hashlib.sha256(CONTENT).hexdigest(),
        len(CONTENT),
    )


def manifest_payload() -> dict:
    selected = artifact()
    return {
        "schema_version": "2cornot2c.classroom-images.v1",
        "release": "1.0.0",
        "artifacts": [
            {
                "name": selected.name,
                "host": selected.host.value,
                "provider": selected.provider.value,
                "architecture": selected.architecture,
                "box_name": selected.box_name,
                "url": selected.url,
                "sha256": selected.sha256,
                "size_bytes": selected.size_bytes,
            }
        ],
    }


def project(tmp_path: Path) -> Path:
    (tmp_path / "Vagrantfile").write_text("", encoding="utf-8")
    return tmp_path


def test_install_image_downloads_imports_and_configures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    selected = artifact()
    monkeypatch.setattr(
        classroom_images,
        "resolve_artifact",
        lambda host, provider, cache: selected,
    )

    downloaded: list[Path] = []

    def fake_download(
        item: BoxArtifact, destination: Path, *, opener=None
    ) -> Path:
        downloaded.append(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(CONTENT)
        return destination

    monkeypatch.setattr(classroom_images, "download_box", fake_download)
    monkeypatch.setattr(
        classroom_images,
        "import_box",
        lambda item, path: VagrantResult("succeeded", "importata"),
    )

    detail = classroom_images.install_image(
        root, Host.WINDOWS_AMD64, Provider.VIRTUALBOX
    )

    assert "importata" in detail
    assert downloaded[0].name == (
        "2cornot2c--ubuntu-24.04-virtualbox-amd64-1.0.0.box"
    )
    assert (root / ".classroom-box").read_text(encoding="utf-8").strip() == (
        selected.box_name
    )
    assert (root / ".classroom-provider").read_text(encoding="utf-8").strip() == (
        "virtualbox"
    )


def test_install_image_refuses_implicit_legacy_vm_migration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    machine = root / ".vagrant" / "machines" / "default" / "virtualbox"
    machine.mkdir(parents=True)
    (machine / "id").write_text("vm-id", encoding="utf-8")
    monkeypatch.setattr(
        classroom_images,
        "resolve_artifact",
        lambda host, provider, cache: artifact(),
    )

    with pytest.raises(classroom_images.ClassroomImageError, match="migration"):
        classroom_images.install_image(
            root, Host.WINDOWS_AMD64, Provider.VIRTUALBOX
        )


def test_check_ready_requires_matching_config_and_installed_box(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    selected = artifact()
    (root / ".classroom-box").write_text(selected.box_name, encoding="utf-8")
    (root / ".classroom-provider").write_text("virtualbox", encoding="utf-8")
    monkeypatch.setattr(
        classroom_images,
        "resolve_artifact",
        lambda host, provider, cache: selected,
    )
    monkeypatch.setattr(
        classroom_images,
        "_installed_boxes",
        lambda: {(selected.box_name, "virtualbox")},
    )

    assert "pronta" in classroom_images.check_ready(
        root, Host.WINDOWS_AMD64, Provider.VIRTUALBOX
    )


def test_vagrantfile_disables_implicit_bento_fallback() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "Vagrantfile"
    ).read_text(encoding="utf-8")

    assert "CLASSROOM_ALLOW_LEGACY_PROVISIONING" in source
    assert "Box Packer 2cornot2c non configurata" in source


def test_latest_manifest_ignores_unrelated_releases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = [
        {
            "tag_name": "application-v9.0.0",
            "draft": False,
            "prerelease": False,
            "assets": [],
        },
        {
            "tag_name": "classroom-v1.9.0",
            "draft": False,
            "prerelease": False,
            "assets": [
                {
                    "name": "release-manifest.json",
                    "browser_download_url": (
                        "https://github.com/TheBitPoets/2cornot2c/releases/"
                        "download/classroom-v1.9.0/release-manifest.json"
                    ),
                }
            ],
        },
        {
            "tag_name": "classroom-v1.10.0",
            "draft": False,
            "prerelease": False,
            "assets": [
                {
                    "name": "release-manifest.json",
                    "browser_download_url": (
                        "https://github.com/TheBitPoets/2cornot2c/releases/"
                        "download/classroom-v1.10.0/release-manifest.json"
                    ),
                }
            ],
        },
    ]

    class Response(io.BytesIO):
        headers: dict[str, str] = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(
        classroom_images,
        "urlopen",
        lambda url, timeout: Response(json.dumps(payload).encode()),
    )

    assert "classroom-v1.10.0" in classroom_images.latest_manifest_url()


def test_acquire_manifest_reuses_fresh_valid_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "images"
    cache.mkdir()
    manifest = cache / "release-manifest.json"
    manifest.write_text(json.dumps(manifest_payload()), encoding="utf-8")
    monkeypatch.setattr(
        classroom_images,
        "latest_manifest_url",
        lambda: pytest.fail("la cache fresca non deve interrogare GitHub"),
    )

    assert classroom_images.acquire_manifest(cache) == manifest


def test_acquire_manifest_falls_back_to_stale_valid_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "images"
    cache.mkdir()
    manifest = cache / "release-manifest.json"
    manifest.write_text(json.dumps(manifest_payload()), encoding="utf-8")
    os.utime(manifest, (1, 1))
    monkeypatch.setattr(
        classroom_images,
        "latest_manifest_url",
        lambda: (_ for _ in ()).throw(
            classroom_images.ClassroomImageError("GitHub API rate limit")
        ),
    )

    assert classroom_images.acquire_manifest(cache) == manifest


def test_acquire_manifest_rejects_invalid_cache_during_api_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "images"
    cache.mkdir()
    (cache / "release-manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        classroom_images,
        "latest_manifest_url",
        lambda: (_ for _ in ()).throw(
            classroom_images.ClassroomImageError("GitHub API rate limit")
        ),
    )

    with pytest.raises(classroom_images.ClassroomImageError, match="rate limit"):
        classroom_images.acquire_manifest(cache)


def test_acquire_manifest_preserves_valid_cache_on_invalid_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "images"
    cache.mkdir()
    manifest = cache / "release-manifest.json"
    original = json.dumps(manifest_payload())
    manifest.write_text(original, encoding="utf-8")
    os.utime(manifest, (1, 1))
    monkeypatch.setattr(
        classroom_images,
        "latest_manifest_url",
        lambda: "https://downloads.example.test/release-manifest.json",
    )

    class Response(io.BytesIO):
        headers: dict[str, str] = {}

        def geturl(self) -> str:
            return "https://downloads.example.test/release-manifest.json"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(
        classroom_images,
        "urlopen",
        lambda url, timeout: Response(b"{}"),
    )

    assert classroom_images.acquire_manifest(cache) == manifest
    assert manifest.read_text(encoding="utf-8") == original
