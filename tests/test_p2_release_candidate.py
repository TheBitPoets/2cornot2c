from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docker" / "assignment-runner" / "toolchain.json"
LOCK = ROOT / "docker" / "assignment-runner" / "toolchain.lock.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_p2_build_candidate_has_new_version_without_faking_published_lock() -> None:
    manifest = load(MANIFEST)
    lock = load(LOCK)

    assert manifest["version"] == "2026.08.1"
    assert manifest["platform"] == "linux/amd64"
    assert manifest["image_repository"] == lock["image_repository"]

    # Until the release is actually published and its remote digest is known,
    # the checked-in immutable lock must remain the previously published release.
    assert lock["version"] == "2026.07.1"
    assert lock["source_revision"] == "bd102146a684a9b06835204ec1b7f668f7655a03"
    assert lock["immutable_reference"].endswith(
        "@sha256:62f0f7b7bc1d48d01b7f8e5fa765e0b43be3622e70a614033b1bb4a4e522e159"
    )


def test_candidate_and_stable_lock_are_deliberately_different_release_identities() -> None:
    manifest = load(MANIFEST)
    lock = load(LOCK)

    assert manifest["version"] != lock["version"]
