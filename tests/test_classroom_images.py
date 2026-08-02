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


def test_install_image_blocks_virtualbox_legacy_state_before_selecting_vmware(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    machine = root / ".vagrant" / "machines" / "default" / "virtualbox"
    machine.mkdir(parents=True)
    (machine / "id").write_text("legacy-vbox-id", encoding="utf-8")
    selected = BoxArtifact(
        "VMware ARM64",
        Host.MACOS_ARM64,
        Provider.VMWARE,
        "arm64",
        "2cornot2c/ubuntu-24.04-vmware-arm64-1.0.0",
        "https://downloads.example.test/classroom.box",
        hashlib.sha256(CONTENT).hexdigest(),
        len(CONTENT),
    )
    monkeypatch.setattr(
        classroom_images,
        "resolve_artifact",
        lambda host, provider, cache: selected,
    )

    with pytest.raises(
        classroom_images.ClassroomImageError,
        match="migration.*virtualbox",
    ):
        classroom_images.install_image(
            root, Host.MACOS_ARM64, Provider.VMWARE
        )

    assert not (root / ".classroom-box").exists()
    assert not (root / ".classroom-provider").exists()


def test_repair_blocks_incompatible_legacy_state_with_existing_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    machine = root / ".vagrant" / "machines" / "default" / "virtualbox"
    machine.mkdir(parents=True)
    (machine / "id").write_text("legacy-vbox-id", encoding="utf-8")
    selected = BoxArtifact(
        "VMware ARM64",
        Host.MACOS_ARM64,
        Provider.VMWARE,
        "arm64",
        "2cornot2c/ubuntu-24.04-vmware-arm64-1.0.0",
        "https://downloads.example.test/classroom.box",
        hashlib.sha256(CONTENT).hexdigest(),
        len(CONTENT),
    )
    (root / ".classroom-box").write_text(selected.box_name, encoding="utf-8")
    (root / ".classroom-provider").write_text(
        selected.provider.value, encoding="utf-8"
    )
    monkeypatch.setattr(
        classroom_images,
        "resolve_artifact",
        lambda host, provider, cache: selected,
    )

    with pytest.raises(
        classroom_images.ClassroomImageError,
        match="migration.*virtualbox",
    ):
        classroom_images.install_image(
            root, Host.MACOS_ARM64, Provider.VMWARE
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


def test_official_manifest_is_pinned_without_github_api_discovery() -> None:
    assert classroom_images.latest_manifest_url() == (
        "https://github.com/TheBitPoets/2cornot2c/releases/download/"
        "classroom-v1.0.0/release-manifest.json"
    )
    assert "api.github.com" not in classroom_images.latest_manifest_url()


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


def test_acquire_manifest_rejects_cached_release_different_from_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "images"
    cache.mkdir()
    payload = manifest_payload()
    payload["release"] = "0.9.0"
    (cache / "release-manifest.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    monkeypatch.setattr(
        classroom_images,
        "latest_manifest_url",
        lambda: (_ for _ in ()).throw(
            classroom_images.ClassroomImageError("manifest fissato non disponibile")
        ),
    )

    with pytest.raises(
        classroom_images.ClassroomImageError,
        match="manifest fissato non disponibile",
    ):
        classroom_images.acquire_manifest(cache)


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


def test_remote_override_does_not_replace_official_manifest_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "images"
    override_url = "https://staging.example.test/release-manifest.json"
    official_url = "https://downloads.example.test/release-manifest.json"
    override_payload = manifest_payload()
    override_payload["release"] = "9.9.9"
    requested: list[str] = []

    class Response(io.BytesIO):
        headers: dict[str, str] = {}

        def __init__(self, url: str, payload: dict) -> None:
            super().__init__(json.dumps(payload).encode())
            self.url = url

        def geturl(self) -> str:
            return self.url

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def fake_urlopen(url: str, timeout: int) -> Response:
        requested.append(url)
        payload = override_payload if url == override_url else manifest_payload()
        return Response(url, payload)

    monkeypatch.setattr(classroom_images, "urlopen", fake_urlopen)
    monkeypatch.setenv("CLASSROOM_RELEASE_MANIFEST", override_url)

    override = classroom_images.acquire_manifest(cache)

    assert override == cache / "override-release-manifest.json"
    assert classroom_images.load_release(override).version == "9.9.9"
    assert not (cache / "release-manifest.json").exists()

    monkeypatch.delenv("CLASSROOM_RELEASE_MANIFEST")
    monkeypatch.setattr(classroom_images, "latest_manifest_url", lambda: official_url)

    official = classroom_images.acquire_manifest(cache)

    assert official == cache / "release-manifest.json"
    assert classroom_images.load_release(official).version == "1.0.0"
    assert requested == [override_url, official_url]
