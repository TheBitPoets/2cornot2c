from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import toolchain_lock


PUBLISHED_VERSION = "2026.08.3"
PUBLISHED_SOURCE = "23bc1d36c7eb8c1b10a11cbde5f226ce7554f85e"
PUBLISHED_DIGEST = "sha256:c0594df833925044831463a9ee631aba2688929951a7dbcb53612b86d221ed51"
IMAGE_REPOSITORY = "ghcr.io/thebitpoets/2cornot2c-assignment-runner"


def lock_payload() -> dict:
    return {
        "schema_version": "thebitlab.grading-toolchain-lock.v1",
        "version": PUBLISHED_VERSION,
        "platform": "linux/amd64",
        "image_repository": IMAGE_REPOSITORY,
        "source_revision": PUBLISHED_SOURCE,
        "immutable_reference": f"{IMAGE_REPOSITORY}@{PUBLISHED_DIGEST}",
    }


def write_lock(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "toolchain.lock.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_lock_accepts_checked_in_published_reference(tmp_path: Path) -> None:
    lock = toolchain_lock.load_lock(write_lock(tmp_path, lock_payload()))

    assert lock["version"] == PUBLISHED_VERSION
    assert lock["platform"] == "linux/amd64"
    assert lock["image_repository"] == IMAGE_REPOSITORY
    assert lock["source_revision"] == PUBLISHED_SOURCE
    assert lock["digest"] == PUBLISHED_DIGEST
    assert toolchain_lock.immutable_reference(lock) == lock_payload()["immutable_reference"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"schema_version": "other"}, "Schema"),
        ({"version": "latest"}, "Versione"),
        ({"platform": "linux/arm64"}, "Piattaforma"),
        ({"image_repository": "ghcr.io/thebitpoets/other-runner"}, "Repository"),
        ({"source_revision": "short"}, "Revisione"),
        ({"immutable_reference": "missing-digest"}, "digest"),
        (
            {
                "immutable_reference": (
                    "ghcr.io/thebitpoets/other-runner"
                    "@sha256:c0594df833925044831463a9ee631aba2688929951a7dbcb53612b86d221ed51"
                )
            },
            "coerenti",
        ),
        ({"immutable_reference": "repo@sha256:notadigest"}, "Digest"),
    ],
)
def test_load_lock_rejects_malformed_or_unauthorized_configuration(
    tmp_path: Path, change: dict, message: str
) -> None:
    payload = lock_payload()
    payload.update(change)

    with pytest.raises(toolchain_lock.ToolchainLockError, match=message):
        toolchain_lock.load_lock(write_lock(tmp_path, payload))


def test_load_lock_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(toolchain_lock.ToolchainLockError, match="non leggibile"):
        toolchain_lock.load_lock(tmp_path / "missing.lock.json")


def test_load_lock_rejects_extra_or_missing_fields(tmp_path: Path) -> None:
    payload = lock_payload()
    payload["extra"] = "value"

    with pytest.raises(toolchain_lock.ToolchainLockError, match="Campi"):
        toolchain_lock.load_lock(write_lock(tmp_path, payload))

    payload.pop("extra")
    payload.pop("source_revision")

    with pytest.raises(toolchain_lock.ToolchainLockError, match="Campi"):
        toolchain_lock.load_lock(write_lock(tmp_path, payload))
