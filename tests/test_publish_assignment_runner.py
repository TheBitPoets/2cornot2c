from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from scripts import build_assignment_runner as builder
from scripts import publish_assignment_runner as publisher


SOURCE_REVISION = "a" * 40
IMAGE_ID = "sha256:" + "b" * 64
MANIFEST_DIGEST = "sha256:" + "c" * 64


def metadata() -> dict:
    return {
        "schema_version": builder.SCHEMA_VERSION,
        "version": "2026.07.1",
        "platform": "linux/amd64",
        "image_repository": builder.IMAGE_REPOSITORY,
        "local_tag": builder.DEFAULT_TAG,
        "local_image_id": IMAGE_ID,
        "source_revision": SOURCE_REVISION,
        "worker_schema_version": builder.WORKER_SCHEMA_VERSION,
        "base_image": "debian:bookworm-slim@sha256:" + "d" * 64,
        "debian_snapshot": "20260713T000000Z",
        "packages": {},
    }


def write_metadata(tmp_path: Path, payload: dict | None = None) -> Path:
    path = tmp_path / "build.json"
    path.write_text(json.dumps(payload or metadata()), encoding="utf-8")
    return path


def completed(
    command: list[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def test_manifest_lookup_fails_closed_on_registry_error(monkeypatch) -> None:
    monkeypatch.setattr(
        publisher,
        "_run",
        lambda command, check=False: completed(
            command, returncode=1, stderr="unauthorized: authentication required"
        ),
    )

    with pytest.raises(publisher.ToolchainPublishError, match="Impossibile verificare"):
        publisher.manifest_exists(f"{builder.IMAGE_REPOSITORY}:2026.07.1")


def test_manifest_lookup_recognizes_only_missing_manifest(monkeypatch) -> None:
    monkeypatch.setattr(
        publisher,
        "_run",
        lambda command, check=False: completed(
            command, returncode=1, stderr="manifest unknown"
        ),
    )

    assert not publisher.manifest_exists(
        f"{builder.IMAGE_REPOSITORY}:2026.07.1"
    )


def test_existing_reference_must_match_local_image(monkeypatch) -> None:
    monkeypatch.setattr(publisher, "manifest_exists", lambda reference: True)
    monkeypatch.setattr(
        publisher, "remote_image_id", lambda reference: "sha256:" + "e" * 64
    )

    with pytest.raises(publisher.ToolchainPublishError, match="contenuto diverso"):
        publisher.ensure_reference(
            reference=f"{builder.IMAGE_REPOSITORY}:2026.07.1",
            local_tag=builder.DEFAULT_TAG,
            local_image_id=IMAGE_ID,
        )


def test_publish_is_idempotent_after_partial_release(
    tmp_path: Path, monkeypatch
) -> None:
    references: set[str] = {
        f"{builder.IMAGE_REPOSITORY}:sha-{SOURCE_REVISION}"
    }
    commands: list[list[str]] = []

    monkeypatch.setattr(
        publisher, "manifest_exists", lambda reference: reference in references
    )
    monkeypatch.setattr(
        publisher, "remote_image_id", lambda reference: IMAGE_ID
    )
    monkeypatch.setattr(
        publisher, "remote_manifest_digest", lambda reference: MANIFEST_DIGEST
    )

    def fake_run(command: list[str], *, check: bool = True):
        commands.append(command)
        if command[:2] == ["docker", "push"]:
            references.add(command[2])
        return completed(command)

    monkeypatch.setattr(publisher, "_run", fake_run)
    release_path = tmp_path / "release.json"
    output_path = tmp_path / "github-output.txt"

    release = publisher.publish(
        metadata_path=write_metadata(tmp_path),
        release_path=release_path,
        github_output_path=output_path,
    )

    version_ref = f"{builder.IMAGE_REPOSITORY}:2026.07.1"
    assert ["docker", "push", version_ref] in commands
    assert not any(
        command == [
            "docker",
            "push",
            f"{builder.IMAGE_REPOSITORY}:sha-{SOURCE_REVISION}",
        ]
        for command in commands
    )
    assert release["published_digest"] == MANIFEST_DIGEST
    assert json.loads(release_path.read_text(encoding="utf-8")) == release
    assert f"digest={MANIFEST_DIGEST}" in output_path.read_text(encoding="utf-8")


def test_existing_matching_reference_is_reused_without_push(monkeypatch) -> None:
    monkeypatch.setattr(publisher, "manifest_exists", lambda reference: True)
    monkeypatch.setattr(publisher, "remote_image_id", lambda reference: IMAGE_ID)
    monkeypatch.setattr(
        publisher, "remote_manifest_digest", lambda reference: MANIFEST_DIGEST
    )

    def fail_on_write(command: list[str], *, check: bool = True):
        raise AssertionError(f"Scrittura registry inattesa: {command}")

    monkeypatch.setattr(publisher, "_run", fail_on_write)

    digest = publisher.ensure_reference(
        reference=f"{builder.IMAGE_REPOSITORY}:2026.07.1",
        local_tag=builder.DEFAULT_TAG,
        local_image_id=IMAGE_ID,
    )

    assert digest == MANIFEST_DIGEST


def test_publish_creates_both_tags_on_first_release(
    tmp_path: Path, monkeypatch
) -> None:
    references: set[str] = set()
    commands: list[list[str]] = []

    monkeypatch.setattr(
        publisher, "manifest_exists", lambda reference: reference in references
    )
    monkeypatch.setattr(publisher, "remote_image_id", lambda reference: IMAGE_ID)
    monkeypatch.setattr(
        publisher, "remote_manifest_digest", lambda reference: MANIFEST_DIGEST
    )

    def fake_run(command: list[str], *, check: bool = True):
        commands.append(command)
        if command[:2] == ["docker", "push"]:
            references.add(command[2])
        return completed(command)

    monkeypatch.setattr(publisher, "_run", fake_run)

    release = publisher.publish(
        metadata_path=write_metadata(tmp_path),
        release_path=tmp_path / "release.json",
        github_output_path=None,
    )

    version_ref = f"{builder.IMAGE_REPOSITORY}:2026.07.1"
    commit_ref = f"{builder.IMAGE_REPOSITORY}:sha-{SOURCE_REVISION}"
    assert ["docker", "push", version_ref] in commands
    assert ["docker", "push", commit_ref] in commands
    assert release["immutable_reference"] == (
        f"{builder.IMAGE_REPOSITORY}@{MANIFEST_DIGEST}"
    )


def test_publish_is_fully_idempotent_when_both_tags_exist(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(publisher, "manifest_exists", lambda reference: True)
    monkeypatch.setattr(publisher, "remote_image_id", lambda reference: IMAGE_ID)
    monkeypatch.setattr(
        publisher, "remote_manifest_digest", lambda reference: MANIFEST_DIGEST
    )

    def fail_on_write(command: list[str], *, check: bool = True):
        raise AssertionError(f"Scrittura registry inattesa: {command}")

    monkeypatch.setattr(publisher, "_run", fail_on_write)
    release_path = tmp_path / "release.json"

    release = publisher.publish(
        metadata_path=write_metadata(tmp_path),
        release_path=release_path,
        github_output_path=None,
    )

    assert release["published_digest"] == MANIFEST_DIGEST
    assert json.loads(release_path.read_text(encoding="utf-8")) == release


def test_publish_rejects_different_version_and_commit_digests(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        publisher,
        "ensure_reference",
        lambda **kwargs: (
            MANIFEST_DIGEST
            if ":sha-" in kwargs["reference"]
            else "sha256:" + "f" * 64
        ),
    )

    with pytest.raises(publisher.ToolchainPublishError, match="stesso manifest"):
        publisher.publish(
            metadata_path=write_metadata(tmp_path),
            release_path=tmp_path / "release.json",
            github_output_path=None,
        )


def test_metadata_cannot_redirect_publication(tmp_path: Path) -> None:
    payload = metadata()
    payload["image_repository"] = "ghcr.io/thebitpoets/other-runner"

    with pytest.raises(publisher.ToolchainPublishError, match="non autorizzate"):
        publisher.load_build_metadata(write_metadata(tmp_path, payload))
