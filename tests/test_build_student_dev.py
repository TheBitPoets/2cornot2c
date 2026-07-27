from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import build_student_dev


def manifest_payload() -> dict:
    return json.loads(build_student_dev.DEFAULT_MANIFEST.read_text(encoding="utf-8"))


def write_manifest(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "toolchain.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_manifest_is_ubuntu_2404_multiarch() -> None:
    manifest = build_student_dev.load_manifest()

    assert manifest["platforms"] == ["linux/amd64", "linux/arm64"]
    assert manifest["base_image"].startswith("ubuntu:24.04@sha256:")
    assert {"gcc", "gdb", "make", "git", "vim-tiny"} <= set(manifest["packages"])


def test_manifest_rejects_missing_architecture(tmp_path: Path) -> None:
    payload = manifest_payload()
    payload["platforms"] = ["linux/amd64"]

    with pytest.raises(build_student_dev.StudentDevBuildError, match="Piattaforme"):
        build_student_dev.load_manifest(write_manifest(tmp_path, payload))


def test_build_command_pins_snapshot_packages_and_platform() -> None:
    manifest = build_student_dev.load_manifest()

    command = build_student_dev.build_command(
        manifest,
        platform="linux/arm64",
        tag="student-dev:test",
        source_revision="a" * 40,
    )

    assert command[:5] == [
        "docker",
        "build",
        "--pull=false",
        "--platform",
        "linux/arm64",
    ]
    joined = "\n".join(command)
    assert "UBUNTU_SNAPSHOT=20260713T000000Z" in joined
    assert "GCC_VERSION=4:13.2.0-7ubuntu1" in joined
    assert manifest["base_image"] in joined


def test_build_rejects_unlisted_platform() -> None:
    with pytest.raises(build_student_dev.StudentDevBuildError, match="Piattaforma"):
        build_student_dev.build_command(
            build_student_dev.load_manifest(),
            platform="linux/ppc64le",
            tag="test",
            source_revision="b" * 40,
        )


def test_publish_command_uses_versioned_and_latest_multiarch_tags() -> None:
    manifest = build_student_dev.load_manifest()

    command = build_student_dev.publish_command(
        manifest,
        source_revision="c" * 40,
    )

    assert command[:6] == [
        "docker",
        "buildx",
        "build",
        "--pull=false",
        "--platform",
        "linux/amd64,linux/arm64",
    ]
    assert f"{manifest['image_repository']}:{manifest['version']}" in command
    assert f"{manifest['image_repository']}:latest" in command
    assert command[-2:] == ["--push", str(build_student_dev.ROOT)]
