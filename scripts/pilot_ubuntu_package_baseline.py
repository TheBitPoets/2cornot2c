"""Deterministic Ubuntu package universe for the canonical pilot fixture."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Final


ROOT: Final = Path(__file__).resolve().parents[1]
BASELINE_PATH: Final = ROOT / "deploy/pilot/ci/ubuntu-systemd-package-baseline.json"
IMAGE_BASELINE_PATH: Final = Path(
    "/usr/local/share/thebitlab/ubuntu-systemd-package-baseline.json"
)
SNAPSHOT_CA_PATH: Final = Path("/usr/local/share/thebitlab/isrg-root-x1.pem")
APT_SOURCES_PATH: Final = Path("/etc/apt/sources.list.d/ubuntu.sources")
SCHEMA_VERSION: Final = "thebitlab.pilot-ubuntu-package-baseline.v1"
SNAPSHOT_RE: Final = re.compile(r"[0-9]{8}T[0-9]{6}Z")
SHA256_RE: Final = re.compile(r"[0-9a-f]{64}")
OCI_RE: Final = re.compile(r"ubuntu@sha256:[0-9a-f]{64}")
STAGES: Final = frozenset(
    {"runtime", "static-bootstrap-builder", "reviewer-payload-builder"}
)
TOP_LEVEL_KEYS: Final = frozenset(
    {
        "architecture",
        "apt_signed_by",
        "base_oci",
        "reviewed_artifacts",
        "schema_version",
        "snapshot_tls_ca",
        "stages",
        "ubuntu_snapshot",
        "ubuntu_snapshot_uri",
    }
)
STAGE_KEYS: Final = frozenset(
    {
        "installed_package_count",
        "installed_package_inventory_sha256",
        "requested_packages",
    }
)
ARTIFACT_KEYS: Final = frozenset(
    {
        "execution_class",
        "package",
        "package_version",
        "sha256",
        "source_package",
    }
)


class PackageBaselineError(RuntimeError):
    """The declared snapshot/package/artifact universe is inconsistent."""


def _read_manifest(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageBaselineError(f"Package baseline non leggibile: {path}") from exc
    if not isinstance(value, dict) or set(value) != TOP_LEVEL_KEYS:
        raise PackageBaselineError("Schema package baseline inatteso")
    return value, raw


def load_baseline(path: Path = BASELINE_PATH) -> tuple[dict[str, Any], str]:
    value, raw = _read_manifest(path)
    snapshot = value.get("ubuntu_snapshot")
    if (
        value.get("schema_version") != SCHEMA_VERSION
        or value.get("architecture") != "amd64"
        or not isinstance(snapshot, str)
        or SNAPSHOT_RE.fullmatch(snapshot) is None
        or value.get("ubuntu_snapshot_uri")
        != f"https://snapshot.ubuntu.com/ubuntu/{snapshot}"
        or value.get("apt_signed_by")
        != "/usr/share/keyrings/ubuntu-archive-keyring.gpg"
        or not isinstance(value.get("base_oci"), str)
        or OCI_RE.fullmatch(value["base_oci"]) is None
    ):
        raise PackageBaselineError("Identity package baseline non canonica")
    tls = value.get("snapshot_tls_ca")
    if (
        not isinstance(tls, dict)
        or set(tls)
        != {"certificate_sha256", "subject_key", "x509_fingerprint_sha256"}
        or tls.get("subject_key") != "ISRG Root X1"
        or SHA256_RE.fullmatch(str(tls.get("certificate_sha256"))) is None
        or SHA256_RE.fullmatch(str(tls.get("x509_fingerprint_sha256"))) is None
    ):
        raise PackageBaselineError("Trust anchor snapshot non canonica")
    stages = value.get("stages")
    if not isinstance(stages, dict) or set(stages) != STAGES:
        raise PackageBaselineError("Stage package baseline mancanti")
    for name, stage in stages.items():
        if (
            not isinstance(stage, dict)
            or set(stage) != STAGE_KEYS
            or not isinstance(stage["installed_package_count"], int)
            or stage["installed_package_count"] <= 0
            or SHA256_RE.fullmatch(
                str(stage["installed_package_inventory_sha256"])
            )
            is None
            or not isinstance(stage["requested_packages"], dict)
            or not stage["requested_packages"]
            or any(
                not isinstance(package, str)
                or not package
                or not isinstance(version, str)
                or not version
                for package, version in stage["requested_packages"].items()
            )
        ):
            raise PackageBaselineError(f"Stage package non canonico: {name}")
    artifacts = value.get("reviewed_artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise PackageBaselineError("Artifact package baseline assenti")
    for path_name, artifact in artifacts.items():
        if (
            not isinstance(path_name, str)
            or not path_name.startswith("/")
            or not isinstance(artifact, dict)
            or set(artifact) != ARTIFACT_KEYS
            or SHA256_RE.fullmatch(str(artifact["sha256"])) is None
            or any(
                not isinstance(artifact[key], str) or not artifact[key]
                for key in ARTIFACT_KEYS - {"sha256"}
            )
        ):
            raise PackageBaselineError(f"Artifact package non canonico: {path_name}")
    return value, hashlib.sha256(raw).hexdigest()


def _run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise PackageBaselineError(
            f"Comando package baseline fallito: {command[0]}: {result.stderr.strip()}"
        )
    return result.stdout


def installed_package_inventory() -> tuple[bytes, int, str]:
    output = _run(
        ["dpkg-query", "-W", "-f=${binary:Package}=${Version}\\n"]
    )
    lines = sorted(output.splitlines())
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    return payload, len(lines), hashlib.sha256(payload).hexdigest()


def attest_runtime_baseline() -> dict[str, str]:
    baseline, baseline_digest = load_baseline()
    image_baseline, image_raw = _read_manifest(IMAGE_BASELINE_PATH)
    repository_raw = BASELINE_PATH.read_bytes()
    if image_baseline != baseline or image_raw != repository_raw:
        raise PackageBaselineError("Baseline package image/candidate divergente")
    snapshot = str(baseline["ubuntu_snapshot"])
    if os.environ.get("THEBITLAB_UBUNTU_SNAPSHOT") != snapshot:
        raise PackageBaselineError("Snapshot package environment divergente")
    expected_sources = (
        "Types: deb\n"
        f"URIs: https://snapshot.ubuntu.com/ubuntu/{snapshot}\n"
        "Suites: noble noble-updates noble-backports noble-security\n"
        "Components: main universe restricted multiverse\n"
        "Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n"
    )
    if APT_SOURCES_PATH.read_text(encoding="utf-8") != expected_sources:
        raise PackageBaselineError("Sorgente APT snapshot divergente")
    ca_digest = hashlib.sha256(SNAPSHOT_CA_PATH.read_bytes()).hexdigest()
    if ca_digest != baseline["snapshot_tls_ca"]["certificate_sha256"]:
        raise PackageBaselineError("Trust anchor TLS snapshot divergente")
    architecture = _run(["dpkg", "--print-architecture"]).strip()
    if architecture != baseline["architecture"]:
        raise PackageBaselineError("Architettura package baseline divergente")
    _payload, count, inventory_digest = installed_package_inventory()
    runtime = baseline["stages"]["runtime"]
    if (
        count != runtime["installed_package_count"]
        or inventory_digest != runtime["installed_package_inventory_sha256"]
    ):
        raise PackageBaselineError("Inventario package runtime divergente")
    for package, expected_version in runtime["requested_packages"].items():
        observed = _run(
            ["dpkg-query", "-W", "-f=${Version}", package]
        ).strip()
        if observed != expected_version:
            raise PackageBaselineError(f"Versione package divergente: {package}")
    for path_name, policy in baseline["reviewed_artifacts"].items():
        path = Path(path_name)
        canonical = path.resolve(strict=True)
        if canonical != path:
            raise PackageBaselineError(f"Realpath artifact divergente: {path}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != policy["sha256"]:
            raise PackageBaselineError(f"Digest artifact divergente: {path}")
        owner = _run(["dpkg-query", "-S", path.as_posix()]).split(": ", 1)[0]
        if owner != policy["package"]:
            raise PackageBaselineError(f"Owner artifact divergente: {path}")
        md5sums = Path(f"/var/lib/dpkg/info/{policy['package']}.md5sums")
        relative = path.as_posix().removeprefix("/")
        manifest_entries = {
            item.split(None, 1)[1]: item.split(None, 1)[0]
            for item in md5sums.read_text(encoding="utf-8").splitlines()
            if len(item.split(None, 1)) == 2
        }
        actual_md5 = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
        if manifest_entries.get(relative) != actual_md5:
            raise PackageBaselineError(f"Manifest dpkg artifact divergente: {path}")
        package_identity = _run(
            [
                "dpkg-query",
                "-W",
                "-f=${Version}\\n${source:Package}\\n${db:Status-Abbrev}",
                policy["package"],
            ]
        ).splitlines()
        if package_identity != [
            policy["package_version"],
            policy["source_package"],
            "ii ",
        ]:
            raise PackageBaselineError(f"Identity artifact package divergente: {path}")
    return {
        "ubuntu_snapshot": snapshot,
        "package_baseline_sha256": baseline_digest,
        "package_inventory_sha256": inventory_digest,
    }
