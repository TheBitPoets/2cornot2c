from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docker" / "assignment-runner" / "toolchain.json"
LOCK = ROOT / "docker" / "assignment-runner" / "toolchain.lock.json"
DOCKERFILE = ROOT / "docker" / "assignment-runner" / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_combined_p2_p3_p4_candidate_has_distinct_version_without_faking_published_lock() -> None:
    manifest = load(MANIFEST)
    lock = load(LOCK)

    assert manifest["version"] == "2026.08.3"
    assert manifest["platform"] == "linux/amd64"
    assert manifest["image_repository"] == lock["image_repository"]

    # Until the combined P2/P3/P4 release is actually reviewed, merged and
    # published, the checked-in immutable lock remains the previous stable release.
    assert lock["version"] == "2026.07.1"
    assert lock["source_revision"] == "bd102146a684a9b06835204ec1b7f668f7655a03"
    assert lock["immutable_reference"].endswith(
        "@sha256:62f0f7b7bc1d48d01b7f8e5fa765e0b43be3622e70a614033b1bb4a4e522e159"
    )


def test_candidate_and_stable_lock_are_deliberately_different_release_identities() -> None:
    manifest = load(MANIFEST)
    lock = load(LOCK)

    assert manifest["version"] != lock["version"]


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
