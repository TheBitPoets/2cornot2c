from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import build_assignment_runner as builder


SOURCE_REVISION = "a" * 40
IMAGE_ID = "sha256:" + "b" * 64


def manifest() -> dict:
    return builder.load_manifest()


def test_checked_in_toolchain_manifest_is_strict_and_immutable() -> None:
    payload = manifest()

    assert payload["version"] == "2026.07.1"
    assert payload["platform"] == "linux/amd64"
    assert payload["image_repository"] == builder.IMAGE_REPOSITORY
    assert payload["base_image"].startswith("debian:bookworm-slim@sha256:")
    assert set(payload["packages"]) == builder.EXPECTED_PACKAGES
    assert all(payload["packages"].values())


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"schema_version": "other"}, "Schema"),
        ({"version": "latest"}, "Versione"),
        ({"platform": "linux/arm64"}, "linux/amd64"),
        (
            {"image_repository": "ghcr.io/thebitpoets/other-runner"},
            "Repository",
        ),
        ({"worker_schema_version": "other"}, "Schema worker"),
        ({"base_image": "debian:bookworm-slim"}, "digest"),
        ({"debian_snapshot": "latest"}, "Snapshot"),
        ({"debian_snapshot": "20261340T000000Z"}, "Snapshot"),
        ({"packages": {"gcc": "12"}}, "Pacchetti"),
    ],
)
def test_manifest_rejects_mutable_or_incomplete_configuration(
    tmp_path: Path,
    change: dict,
    message: str,
) -> None:
    payload = manifest()
    payload.update(change)
    path = tmp_path / "toolchain.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(builder.ToolchainBuildError, match=message):
        builder.load_manifest(path)


def test_manifest_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "toolchain.json"
    path.write_text('{"schema_version":"one","schema_version":"two"}', encoding="utf-8")

    with pytest.raises(builder.ToolchainBuildError, match="duplicata"):
        builder.load_manifest(path)


def test_docker_build_command_uses_only_manifest_pins() -> None:
    payload = manifest()

    command = builder.docker_build_command(
        payload,
        tag="runner-test",
        source_revision=SOURCE_REVISION,
    )

    joined = " ".join(command)
    assert command[:3] == ["docker", "build", "--pull=false"]
    assert payload["base_image"] in joined
    assert payload["debian_snapshot"] in joined
    assert f"SOURCE_REVISION={SOURCE_REVISION}" in command
    assert (
        f"SOURCE_DATE_EPOCH={builder.snapshot_epoch(payload['debian_snapshot'])}"
        in command
    )
    for package_version in payload["packages"].values():
        assert package_version in joined
    assert ":latest" not in joined


def test_snapshot_epoch_is_deterministic() -> None:
    assert builder.snapshot_epoch("20260713T000000Z") == 1783900800


def test_image_metadata_requires_labels_matching_manifest() -> None:
    payload = manifest()
    labels = {
        "org.opencontainers.image.version": payload["version"],
        "org.opencontainers.image.revision": SOURCE_REVISION,
        "io.thebitlab.grading.base-image": payload["base_image"],
        "io.thebitlab.grading.debian-snapshot": payload["debian_snapshot"],
        "io.thebitlab.grading.worker-schema": payload["worker_schema_version"],
    }

    metadata = builder.image_metadata(
        payload,
        tag="runner-test",
        source_revision=SOURCE_REVISION,
        inspect_payload=[{"Id": IMAGE_ID, "Config": {"Labels": labels}}],
    )

    assert metadata["local_image_id"] == IMAGE_ID
    assert metadata["source_revision"] == SOURCE_REVISION
    assert metadata["packages"] == payload["packages"]

    labels["org.opencontainers.image.version"] = "other"
    with pytest.raises(builder.ToolchainBuildError, match="label"):
        builder.image_metadata(
            payload,
            tag="runner-test",
            source_revision=SOURCE_REVISION,
            inspect_payload=[{"Id": IMAGE_ID, "Config": {"Labels": labels}}],
        )


def test_dockerfile_uses_snapshot_and_requires_build_arguments() -> None:
    source = builder.DOCKERFILE.read_text(encoding="utf-8")
    payload = manifest()

    assert source.startswith(
        f"ARG DEBIAN_BASE_IMAGE={payload['base_image']}\n"
        "FROM ${DEBIAN_BASE_IMAGE}\n\n"
        "ARG DEBIAN_BASE_IMAGE\n"
    )
    assert "snapshot.debian.org/archive/debian/%s/" in source
    assert '"${DEBIAN_SNAPSHOT}"' in source
    assert '"gcc=${GCC_VERSION}"' in source
    assert '"python3=${PYTHON3_VERSION}"' in source
    assert "FROM debian:bookworm-slim" not in source
    assert "apt-get upgrade" not in source
