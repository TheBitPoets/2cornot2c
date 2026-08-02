"""Lock revisionato delle release classroom indipendenti per piattaforma."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

from installer.model import Host, Provider


SCHEMA_VERSION = "2cornot2c.classroom-release-lock.v1"
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROOT_KEYS = {"schema_version", "targets"}
TARGET_KEYS = {
    "host",
    "provider",
    "state",
    "version",
    "manifest_url",
    "manifest_sha256",
}
TARGET_IDS = {
    (Host.WINDOWS_AMD64, Provider.VIRTUALBOX): "windows-amd64-virtualbox",
    (Host.MACOS_ARM64, Provider.VMWARE): "macos-arm64-vmware",
}
DEFAULT_LOCK_PATH = (
    Path(__file__).resolve().parents[1] / "packer" / "classroom-releases.lock.json"
)


class ClassroomReleaseLockError(RuntimeError):
    """Lock mancante, ambiguo o non valido."""


@dataclass(frozen=True, slots=True)
class TargetRelease:
    target_id: str
    host: Host
    provider: Provider
    state: str
    version: str
    manifest_url: str
    manifest_sha256: str | None

    @property
    def active(self) -> bool:
        return self.state == "active"


def _without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ClassroomReleaseLockError(f"Chiave duplicata nel lock: {key}")
        result[key] = value
    return result


def load_target_releases(path: Path = DEFAULT_LOCK_PATH) -> dict[str, TargetRelease]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_without_duplicates,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ClassroomReleaseLockError("Lock release classroom non leggibile.") from error
    if not isinstance(payload, dict) or set(payload) != ROOT_KEYS:
        raise ClassroomReleaseLockError("Campi root del lock non validi.")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ClassroomReleaseLockError("Schema lock release non supportato.")
    raw_targets = payload["targets"]
    if not isinstance(raw_targets, dict) or not raw_targets:
        raise ClassroomReleaseLockError("Il lock non contiene target.")

    releases: dict[str, TargetRelease] = {}
    identities: set[tuple[Host, Provider]] = set()
    for target_id, raw in raw_targets.items():
        if not isinstance(target_id, str) or not isinstance(raw, dict):
            raise ClassroomReleaseLockError("Target release non valido.")
        if set(raw) != TARGET_KEYS:
            raise ClassroomReleaseLockError(f"Campi non validi per {target_id}.")
        try:
            host = Host(raw["host"])
            provider = Provider(raw["provider"])
        except (TypeError, ValueError) as error:
            raise ClassroomReleaseLockError(
                f"Host/provider non validi per {target_id}."
            ) from error
        identity = (host, provider)
        if TARGET_IDS.get(identity) != target_id or identity in identities:
            raise ClassroomReleaseLockError(f"Identità target non valida: {target_id}.")
        identities.add(identity)
        state = raw["state"]
        version = raw["version"]
        url = raw["manifest_url"]
        digest = raw["manifest_sha256"]
        if state not in {"pending", "active"}:
            raise ClassroomReleaseLockError(f"Stato non valido per {target_id}.")
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            raise ClassroomReleaseLockError(f"Versione non valida per {target_id}.")
        expected_url = (
            "https://github.com/TheBitPoets/2cornot2c/releases/download/"
            f"classroom-{target_id}-v{version}/release-manifest.json"
        )
        if (
            not isinstance(url, str)
            or url != expected_url
            or urlparse(url).scheme != "https"
        ):
            raise ClassroomReleaseLockError(f"URL manifest non valido per {target_id}.")
        if state == "active":
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise ClassroomReleaseLockError(
                    f"Digest attivo non valido per {target_id}."
                )
        elif digest is not None:
            raise ClassroomReleaseLockError(
                f"Un target pending non deve avere un digest: {target_id}."
            )
        releases[target_id] = TargetRelease(
            target_id, host, provider, state, version, url, digest
        )
    return releases


def target_release(
    host: Host,
    provider: Provider,
    path: Path = DEFAULT_LOCK_PATH,
) -> TargetRelease:
    target_id = TARGET_IDS.get((host, provider))
    if target_id is None:
        raise ClassroomReleaseLockError(
            f"Target classroom non supportato: {host.value}/{provider.value}."
        )
    try:
        return load_target_releases(path)[target_id]
    except KeyError as error:
        raise ClassroomReleaseLockError(
            f"Target classroom mancante nel lock: {target_id}."
        ) from error
