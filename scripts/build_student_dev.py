from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docker" / "student-dev" / "toolchain.json"
DOCKERFILE = ROOT / "docker" / "student-dev" / "Dockerfile"
DEFAULT_TAG = "2cornot2c-student-dev"
SCHEMA_VERSION = "2cornot2c.student-dev-build.v1"
IMAGE_REPOSITORY = "ghcr.io/thebitpoets/2cornot2c-student-dev"
EXPECTED_PLATFORMS = ["linux/amd64", "linux/arm64"]
EXPECTED_PACKAGES = {
    "build-essential",
    "ca-certificates",
    "gcc",
    "gdb",
    "git",
    "make",
    "nodejs",
    "python3",
    "sqlite3",
    "vim-tiny",
}
EXPECTED_KEYS = {
    "schema_version",
    "version",
    "platforms",
    "image_repository",
    "base_image",
    "ubuntu_snapshot",
    "packages",
}
VERSION_RE = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[1-9][0-9]*$")
SNAPSHOT_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
BASE_RE = re.compile(r"^ubuntu:24\.04@sha256:[0-9a-f]{64}$")
PACKAGE_RE = re.compile(r"^[A-Za-z0-9.+:~_-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class StudentDevBuildError(RuntimeError):
    """Configurazione student-dev non valida."""


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Carica e valida senza tollerare campi o piattaforme implicite."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StudentDevBuildError(f"Manifest non leggibile: {path}") from error
    if not isinstance(payload, dict) or set(payload) != EXPECTED_KEYS:
        raise StudentDevBuildError("Campi manifest student-dev non validi.")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise StudentDevBuildError("Schema student-dev non supportato.")
    if not isinstance(payload["version"], str) or not VERSION_RE.fullmatch(
        payload["version"]
    ):
        raise StudentDevBuildError("Versione student-dev non valida.")
    if payload["platforms"] != EXPECTED_PLATFORMS:
        raise StudentDevBuildError("Piattaforme student-dev non valide.")
    if payload["image_repository"] != IMAGE_REPOSITORY:
        raise StudentDevBuildError("Repository student-dev non autorizzato.")
    if not isinstance(payload["base_image"], str) or not BASE_RE.fullmatch(
        payload["base_image"]
    ):
        raise StudentDevBuildError("Base Ubuntu 24.04 non fissata a digest.")
    if not isinstance(payload["ubuntu_snapshot"], str) or not SNAPSHOT_RE.fullmatch(
        payload["ubuntu_snapshot"]
    ):
        raise StudentDevBuildError("Snapshot Ubuntu non valido.")
    packages = payload["packages"]
    if not isinstance(packages, dict) or set(packages) != EXPECTED_PACKAGES:
        raise StudentDevBuildError("Pacchetti student-dev mancanti o inattesi.")
    if any(
        not isinstance(version, str) or not PACKAGE_RE.fullmatch(version)
        for version in packages.values()
    ):
        raise StudentDevBuildError("Versione pacchetto student-dev non valida.")
    return payload


def build_command(
    manifest: dict[str, Any],
    *,
    platform: str,
    tag: str,
    source_revision: str,
) -> list[str]:
    """Costruisce il comando per una singola architettura collaudabile."""

    if platform not in manifest["platforms"]:
        raise StudentDevBuildError(f"Piattaforma non supportata: {platform}")
    if not tag.strip():
        raise StudentDevBuildError("Tag locale mancante.")
    if not SHA_RE.fullmatch(source_revision):
        raise StudentDevBuildError("Revisione sorgente non valida.")
    packages = manifest["packages"]
    arguments = {
        "UBUNTU_BASE_IMAGE": manifest["base_image"],
        "UBUNTU_SNAPSHOT": manifest["ubuntu_snapshot"],
        "BUILD_ESSENTIAL_VERSION": packages["build-essential"],
        "CA_CERTIFICATES_VERSION": packages["ca-certificates"],
        "GCC_VERSION": packages["gcc"],
        "GDB_VERSION": packages["gdb"],
        "GIT_VERSION": packages["git"],
        "MAKE_VERSION": packages["make"],
        "NODEJS_VERSION": packages["nodejs"],
        "PYTHON3_VERSION": packages["python3"],
        "SQLITE3_VERSION": packages["sqlite3"],
        "VIM_TINY_VERSION": packages["vim-tiny"],
        "STUDENT_DEV_VERSION": manifest["version"],
        "SOURCE_REVISION": source_revision,
    }
    command = [
        "docker",
        "build",
        "--pull=false",
        "--platform",
        platform,
        "--tag",
        tag,
        "--file",
        str(DOCKERFILE),
    ]
    for name, value in arguments.items():
        command.extend(["--build-arg", f"{name}={value}"])
    command.append(str(ROOT))
    return command


def publish_command(
    manifest: dict[str, Any],
    *,
    source_revision: str,
) -> list[str]:
    """Costruisce e pubblica un unico manifest nativo multiarch."""

    packages = manifest["packages"]
    arguments = {
        "UBUNTU_BASE_IMAGE": manifest["base_image"],
        "UBUNTU_SNAPSHOT": manifest["ubuntu_snapshot"],
        "BUILD_ESSENTIAL_VERSION": packages["build-essential"],
        "CA_CERTIFICATES_VERSION": packages["ca-certificates"],
        "GCC_VERSION": packages["gcc"],
        "GDB_VERSION": packages["gdb"],
        "GIT_VERSION": packages["git"],
        "MAKE_VERSION": packages["make"],
        "NODEJS_VERSION": packages["nodejs"],
        "PYTHON3_VERSION": packages["python3"],
        "SQLITE3_VERSION": packages["sqlite3"],
        "VIM_TINY_VERSION": packages["vim-tiny"],
        "STUDENT_DEV_VERSION": manifest["version"],
        "SOURCE_REVISION": source_revision,
    }
    if not SHA_RE.fullmatch(source_revision):
        raise StudentDevBuildError("Revisione sorgente non valida.")
    repository = manifest["image_repository"]
    command = [
        "docker",
        "buildx",
        "build",
        "--pull=false",
        "--platform",
        ",".join(manifest["platforms"]),
        "--tag",
        f"{repository}:{manifest['version']}",
        "--tag",
        f"{repository}:latest",
        "--file",
        str(DOCKERFILE),
    ]
    for name, value in arguments.items():
        command.extend(["--build-arg", f"{name}={value}"])
    command.extend(["--push", str(ROOT)])
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Costruisce student-dev Ubuntu.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--platform", choices=EXPECTED_PLATFORMS)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.check:
            print(
                f"student-dev {manifest['version']} valido per "
                f"{', '.join(manifest['platforms'])}."
            )
            return 0
        if args.publish and args.platform is not None:
            raise StudentDevBuildError("--publish e --platform sono alternativi.")
        platform = args.platform
        if not args.publish and platform is None:
            raise StudentDevBuildError("--platform è richiesto per una build locale.")
        revision = args.source_revision
        if revision is None:
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        if args.publish:
            subprocess.run(
                publish_command(manifest, source_revision=revision),
                cwd=ROOT,
                check=True,
            )
        else:
            subprocess.run(
                build_command(
                    manifest,
                    platform=platform,
                    tag=args.tag,
                    source_revision=revision,
                ),
                cwd=ROOT,
                check=True,
            )
    except (OSError, subprocess.CalledProcessError, StudentDevBuildError) as error:
        print(f"Build student-dev non riuscita: {error}")
        return 1
    if args.publish:
        print(
            f"student-dev {manifest['version']} pubblicato per "
            f"{', '.join(manifest['platforms'])}."
        )
    else:
        print(f"student-dev costruito come {args.tag} per {platform}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
