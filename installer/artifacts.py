"""Manifest e download verificato delle box didattiche pubblicate."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, BinaryIO
from urllib.parse import urlparse
from urllib.request import urlopen

from installer.model import Host, Provider


SCHEMA_VERSION = "2cornot2c.classroom-images.v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
BOX_NAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$"
)
BOX_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+\.box$")
# GitHub Releases richiede che ogni singolo asset sia strettamente sotto 2 GiB.
MAX_BOX_BYTES = 2 * 1024 * 1024 * 1024 - 1
MANIFEST_KEYS = {"schema_version", "release", "artifacts"}
ARTIFACT_KEYS = {
    "name",
    "host",
    "provider",
    "architecture",
    "box_name",
    "url",
    "sha256",
    "size_bytes",
}


class ArtifactError(RuntimeError):
    """Manifest, download o checksum non valido."""


@dataclass(frozen=True, slots=True)
class BoxArtifact:
    """Una box provider-specifica descritta dal manifest autorevole."""

    name: str
    host: Host
    provider: Provider
    architecture: str
    box_name: str
    url: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ImageRelease:
    """Release immutabile contenente le box supportate."""

    version: str
    artifacts: tuple[BoxArtifact, ...]


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactError(f"Chiave duplicata nel manifest: {key}")
        result[key] = value
    return result


def load_release(path: Path) -> ImageRelease:
    """Carica e valida completamente un manifest locale affidabile."""

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicates,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArtifactError(f"Manifest non leggibile: {path}") from error
    if not isinstance(payload, dict) or set(payload) != MANIFEST_KEYS:
        raise ArtifactError("Campi del manifest non validi.")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ArtifactError("Schema manifest non supportato.")
    version = payload["release"]
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ArtifactError("Versione release non valida.")
    raw_artifacts = payload["artifacts"]
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ArtifactError("Il manifest non contiene artefatti.")

    artifacts = tuple(_parse_artifact(item) for item in raw_artifacts)
    identities = {(item.host, item.provider) for item in artifacts}
    if len(identities) != len(artifacts):
        raise ArtifactError("Combinazione host/provider duplicata.")
    return ImageRelease(version, artifacts)


def _parse_artifact(payload: Any) -> BoxArtifact:
    if not isinstance(payload, dict) or set(payload) != ARTIFACT_KEYS:
        raise ArtifactError("Campi artefatto non validi.")
    try:
        host = Host(payload["host"])
        provider = Provider(payload["provider"])
    except (TypeError, ValueError) as error:
        raise ArtifactError("Host o provider artefatto non valido.") from error

    expected = {
        (Host.MACOS_ARM64, Provider.VMWARE): "arm64",
        (Host.WINDOWS_AMD64, Provider.VIRTUALBOX): "amd64",
    }
    architecture = payload["architecture"]
    if expected.get((host, provider)) != architecture:
        raise ArtifactError("Architettura non coerente con host e provider.")
    name = payload["name"]
    if not isinstance(name, str) or not name.strip():
        raise ArtifactError("Campo artefatto vuoto: name")
    box_name = payload["box_name"]
    if not isinstance(box_name, str) or not BOX_NAME_RE.fullmatch(box_name):
        raise ArtifactError("Nome box Vagrant non valido.")
    url = payload["url"]
    if not isinstance(url, str) or urlparse(url).scheme != "https":
        raise ArtifactError("La box deve usare un URL HTTPS.")
    filename = Path(urlparse(url).path).name
    if not BOX_FILENAME_RE.fullmatch(filename):
        raise ArtifactError("Nome file box non valido.")
    digest = payload["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise ArtifactError("Checksum SHA-256 non valido.")
    size = payload["size_bytes"]
    if not isinstance(size, int) or isinstance(size, bool) or not 0 < size <= MAX_BOX_BYTES:
        raise ArtifactError("Dimensione artefatto non valida.")
    return BoxArtifact(
        name,
        host,
        provider,
        architecture,
        box_name,
        url,
        digest,
        size,
    )


def select_artifact(
    release: ImageRelease, host: Host, provider: Provider
) -> BoxArtifact:
    """Seleziona una sola box per la combinazione richiesta."""

    matches = [
        artifact
        for artifact in release.artifacts
        if artifact.host is host and artifact.provider is provider
    ]
    if len(matches) != 1:
        raise ArtifactError(f"Box non disponibile per {host.value}/{provider.value}.")
    return matches[0]


def sha256_file(path: Path) -> tuple[str, int]:
    """Calcola digest e dimensione leggendo il file a blocchi."""

    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def verify_box(path: Path, artifact: BoxArtifact) -> None:
    """Rifiuta file incompleti o diversi dal manifest."""

    digest, size = sha256_file(path)
    if size != artifact.size_bytes:
        raise ArtifactError(
            f"Dimensione box errata: attesi {artifact.size_bytes}, trovati {size} byte."
        )
    if digest != artifact.sha256:
        raise ArtifactError("Checksum SHA-256 della box non corrispondente.")


ResponseOpener = Callable[[str], BinaryIO]


def download_box(
    artifact: BoxArtifact,
    destination: Path,
    *,
    opener: ResponseOpener = urlopen,
) -> Path:
    """Scarica in streaming e pubblica atomicamente solo una box verificata."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        verify_box(destination, artifact)
        return destination

    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{destination.name}.",
            suffix=".part",
            dir=destination.parent,
            delete=False,
        ) as output:
            temporary_name = output.name
            with opener(artifact.url) as response:
                final_url = getattr(response, "geturl", lambda: artifact.url)()
                if urlparse(final_url).scheme != "https":
                    raise ArtifactError("Il download è stato reindirizzato fuori da HTTPS.")
                written = 0
                while chunk := response.read(1024 * 1024):
                    written += len(chunk)
                    if written > artifact.size_bytes:
                        raise ArtifactError("Il download supera la dimensione dichiarata.")
                    output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        temporary = Path(temporary_name)
        verify_box(temporary, artifact)
        temporary.replace(destination)
        return destination
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
