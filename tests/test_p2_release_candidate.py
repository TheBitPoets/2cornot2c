from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docker" / "assignment-runner" / "toolchain.json"
LOCK = ROOT / "docker" / "assignment-runner" / "toolchain.lock.json"
DOCKERFILE = ROOT / "docker" / "assignment-runner" / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"

PUBLISHED_VERSION = "2026.08.3"
PUBLISHED_SOURCE = "23bc1d36c7eb8c1b10a11cbde5f226ce7554f85e"
PUBLISHED_DIGEST = "sha256:c0594df833925044831463a9ee631aba2688929951a7dbcb53612b86d221ed51"
IMAGE_REPOSITORY = "ghcr.io/thebitpoets/2cornot2c-assignment-runner"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_combined_p2_p3_p4_release_is_locked_to_published_2026_08_3() -> None:
    manifest = load(MANIFEST)
    lock = load(LOCK)

    assert manifest["version"] == PUBLISHED_VERSION
    assert lock["version"] == PUBLISHED_VERSION
    assert manifest["platform"] == lock["platform"] == "linux/amd64"
    assert manifest["image_repository"] == lock["image_repository"] == IMAGE_REPOSITORY
    assert lock["source_revision"] == PUBLISHED_SOURCE
    assert lock["immutable_reference"] == f"{IMAGE_REPOSITORY}@{PUBLISHED_DIGEST}"


def test_manifest_and_stable_lock_share_the_reviewed_release_identity() -> None:
    manifest = load(MANIFEST)
    lock = load(LOCK)

    assert manifest["version"] == lock["version"] == PUBLISHED_VERSION
    assert manifest["image_repository"] == lock["image_repository"]
    assert "@sha256:" in lock["immutable_reference"]


def test_combined_runner_packages_all_three_python_profile_workers() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    dockerignore = DOCKERIGNORE.read_text(encoding="utf-8")

    for path in (
        "scripts/python_function_profile.py",
        "scripts/python_function_worker.py",
        "scripts/python_object_profile.py",
        "scripts/python_object_worker.py",
        "scripts/python_filesystem_profile.py",
        "scripts/python_filesystem_worker.py",
    ):
        assert f"COPY {path} /opt/thebitlab/{Path(path).name}" in dockerfile
        assert f"!{path}" in dockerignore

    assert 'ENTRYPOINT ["python3", "/opt/thebitlab/grade_activity.py"]' in dockerfile
