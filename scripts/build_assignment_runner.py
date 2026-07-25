from __future__ import annotations

import argparse
from datetime import datetime
from datetime import timezone
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docker" / "assignment-runner" / "toolchain.json"
DOCKERFILE = ROOT / "docker" / "assignment-runner" / "Dockerfile"
DEFAULT_TAG = "thebitlab-assignment-runner"
SCHEMA_VERSION = "thebitlab.grading-toolchain-build.v1"
WORKER_SCHEMA_VERSION = "thebitlab.grading-worker.v1"
IMAGE_REPOSITORY = "ghcr.io/thebitpoets/2cornot2c-assignment-runner"
EXPECTED_KEYS = {
    "schema_version",
    "version",
    "platform",
    "image_repository",
    "worker_schema_version",
    "base_image",
    "debian_snapshot",
    "packages",
}
EXPECTED_PACKAGES = {"gcc", "libc6-dev", "nodejs", "python3", "sqlite3"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
BASE_IMAGE_RE = re.compile(r"^debian:bookworm-slim@(sha256:[0-9a-f]{64})$")
VERSION_RE = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[1-9][0-9]*$")
SNAPSHOT_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z$")
PACKAGE_VERSION_RE = re.compile(r"^[A-Za-z0-9.+:~_-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ToolchainBuildError(RuntimeError):
    """Raised when the reproducible runner configuration is invalid."""


def snapshot_epoch(snapshot: str) -> int:
    """Return the deterministic SOURCE_DATE_EPOCH for one Debian snapshot."""

    moment = datetime.strptime(snapshot, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return int(moment.timestamp())


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ToolchainBuildError(f"Chiave duplicata nel manifest toolchain: {key}.")
        result[key] = value
    return result


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load and strictly validate the reproducible toolchain build manifest."""

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ToolchainBuildError(f"Costante JSON non valida: {value}.")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ToolchainBuildError(f"Manifest toolchain non leggibile: {path}.") from error
    if not isinstance(payload, dict) or set(payload) != EXPECTED_KEYS:
        raise ToolchainBuildError("Campi del manifest toolchain non validi.")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ToolchainBuildError("Schema manifest toolchain non supportato.")
    if not isinstance(payload["version"], str) or not VERSION_RE.fullmatch(payload["version"]):
        raise ToolchainBuildError("Versione toolchain non valida.")
    if payload["platform"] != "linux/amd64":
        raise ToolchainBuildError("La prima toolchain supporta esclusivamente linux/amd64.")
    if payload["image_repository"] != IMAGE_REPOSITORY:
        raise ToolchainBuildError("Repository immagine toolchain non autorizzato.")
    if payload["worker_schema_version"] != WORKER_SCHEMA_VERSION:
        raise ToolchainBuildError("Schema worker toolchain non compatibile.")
    if not isinstance(payload["base_image"], str) or not BASE_IMAGE_RE.fullmatch(
        payload["base_image"]
    ):
        raise ToolchainBuildError("Immagine base non fissata a un digest Debian valido.")
    if (
        not isinstance(payload["debian_snapshot"], str)
        or not SNAPSHOT_RE.fullmatch(payload["debian_snapshot"])
    ):
        raise ToolchainBuildError("Snapshot Debian non valido.")
    packages = payload["packages"]
    if not isinstance(packages, dict) or set(packages) != EXPECTED_PACKAGES:
        raise ToolchainBuildError("Pacchetti toolchain mancanti o inattesi.")
    for package, version in packages.items():
        if not isinstance(version, str) or not PACKAGE_VERSION_RE.fullmatch(version):
            raise ToolchainBuildError(f"Versione non valida per il pacchetto {package}.")
    return payload


def docker_build_command(
    manifest: dict[str, Any],
    *,
    tag: str,
    source_revision: str,
) -> list[str]:
    """Return the deterministic Docker build command for one validated manifest."""

    if not tag.strip():
        raise ToolchainBuildError("Tag Docker locale mancante.")
    if not SHA_RE.fullmatch(source_revision):
        raise ToolchainBuildError("Revisione sorgente non valida.")
    packages = manifest["packages"]
    build_args = {
        "DEBIAN_BASE_IMAGE": manifest["base_image"],
        "DEBIAN_SNAPSHOT": manifest["debian_snapshot"],
        "GCC_VERSION": packages["gcc"],
        "LIBC6_DEV_VERSION": packages["libc6-dev"],
        "NODEJS_VERSION": packages["nodejs"],
        "PYTHON3_VERSION": packages["python3"],
        "SQLITE3_VERSION": packages["sqlite3"],
        "THEBITLAB_TOOLCHAIN_VERSION": manifest["version"],
        "THEBITLAB_WORKER_SCHEMA_VERSION": manifest["worker_schema_version"],
        "SOURCE_REVISION": source_revision,
        "SOURCE_DATE_EPOCH": str(snapshot_epoch(manifest["debian_snapshot"])),
    }
    command = [
        "docker",
        "build",
        "--pull=false",
        "--platform",
        manifest["platform"],
        "--tag",
        tag,
        "--file",
        str(DOCKERFILE),
    ]
    for name, value in build_args.items():
        command.extend(["--build-arg", f"{name}={value}"])
    command.append(str(ROOT))
    return command


def image_metadata(
    manifest: dict[str, Any],
    *,
    tag: str,
    source_revision: str,
    inspect_payload: Any,
) -> dict[str, Any]:
    """Validate Docker inspect output and return release metadata."""

    if (
        not isinstance(inspect_payload, list)
        or len(inspect_payload) != 1
        or not isinstance(inspect_payload[0], dict)
    ):
        raise ToolchainBuildError("docker image inspect non ha restituito una sola immagine.")
    image = inspect_payload[0]
    image_id = image.get("Id")
    config = image.get("Config")
    labels = config.get("Labels") if isinstance(config, dict) else None
    if not isinstance(image_id, str) or not DIGEST_RE.fullmatch(image_id):
        raise ToolchainBuildError("Docker image ID non valido.")
    expected_labels = {
        "org.opencontainers.image.version": manifest["version"],
        "org.opencontainers.image.revision": source_revision,
        "io.thebitlab.grading.base-image": manifest["base_image"],
        "io.thebitlab.grading.debian-snapshot": manifest["debian_snapshot"],
        "io.thebitlab.grading.worker-schema": manifest["worker_schema_version"],
    }
    if not isinstance(labels, dict) or any(
        labels.get(name) != value for name, value in expected_labels.items()
    ):
        raise ToolchainBuildError("Le label dell'immagine non corrispondono al manifest.")
    return {
        "schema_version": SCHEMA_VERSION,
        "version": manifest["version"],
        "platform": manifest["platform"],
        "image_repository": manifest["image_repository"],
        "local_tag": tag,
        "local_image_id": image_id,
        "source_revision": source_revision,
        "worker_schema_version": manifest["worker_schema_version"],
        "base_image": manifest["base_image"],
        "debian_snapshot": manifest["debian_snapshot"],
        "packages": dict(manifest["packages"]),
    }


def _git_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip().lower()


def build_runner(
    *,
    manifest_path: Path,
    tag: str,
    source_revision: str | None,
    metadata_path: Path | None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    revision = (source_revision or _git_revision()).strip().lower()
    command = docker_build_command(manifest, tag=tag, source_revision=revision)
    subprocess.run(command, cwd=ROOT, check=True)
    inspected = subprocess.run(
        ["docker", "image", "inspect", tag],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        inspect_payload = json.loads(inspected.stdout)
    except json.JSONDecodeError as error:
        raise ToolchainBuildError("Output di docker image inspect non valido.") from error
    metadata = image_metadata(
        manifest,
        tag=tag,
        source_revision=revision,
        inspect_payload=inspect_payload,
    )
    if metadata_path is not None:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Costruisce il runner grading dalla toolchain riproducibile."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--source-revision")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida soltanto il manifest senza avviare Docker.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.check:
            print(
                f"Toolchain {manifest['version']} valida per {manifest['platform']}."
            )
            return 0
        metadata = build_runner(
            manifest_path=args.manifest,
            tag=args.tag,
            source_revision=args.source_revision,
            metadata_path=args.metadata,
        )
    except (OSError, subprocess.CalledProcessError, ToolchainBuildError) as error:
        print(f"Build runner non riuscita: {error}")
        return 1
    print(
        f"Runner {metadata['version']} costruito come "
        f"{metadata['local_tag']} ({metadata['local_image_id']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
