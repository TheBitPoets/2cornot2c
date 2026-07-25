from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from scripts.build_assignment_runner import IMAGE_REPOSITORY, VERSION_RE


LOCK_SCHEMA_VERSION = "thebitlab.grading-toolchain-lock.v1"
SUPPORTED_PLATFORMS = {"linux/amd64"}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_KEYS = {
    "schema_version",
    "version",
    "platform",
    "image_repository",
    "source_revision",
    "immutable_reference",
}


class ToolchainLockError(RuntimeError):
    """Raised when the toolchain lock is missing, malformed, or unauthorized."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ToolchainLockError(f"Lock toolchain non leggibile: {path}.") from error


def _split_reference(reference: str) -> tuple[str, str]:
    if "@" not in reference:
        raise ToolchainLockError("Riferimento immutabile mancante di digest.")
    repository, digest = reference.rsplit("@", 1)
    if not repository:
        raise ToolchainLockError("Repository nel riferimento immutabile vuota.")
    if not DIGEST_RE.fullmatch(digest):
        raise ToolchainLockError("Digest nel riferimento immutabile non valido.")
    return repository, digest


def load_lock(path: Path) -> dict[str, Any]:
    """Load and strictly validate the authoritative toolchain lock file."""

    payload = _load_json(path)
    if not isinstance(payload, dict) or set(payload) != EXPECTED_KEYS:
        raise ToolchainLockError("Campi del lock toolchain non validi.")
    if payload["schema_version"] != LOCK_SCHEMA_VERSION:
        raise ToolchainLockError("Schema lock toolchain non supportato.")
    if not isinstance(payload["version"], str) or not VERSION_RE.fullmatch(
        payload["version"]
    ):
        raise ToolchainLockError("Versione nel lock toolchain non valida.")
    if payload["platform"] not in SUPPORTED_PLATFORMS:
        raise ToolchainLockError("Piattaforma nel lock toolchain non supportata.")
    if payload["image_repository"] != IMAGE_REPOSITORY:
        raise ToolchainLockError("Repository nel lock toolchain non autorizzato.")
    if not isinstance(payload["source_revision"], str) or not SHA_RE.fullmatch(
        payload["source_revision"]
    ):
        raise ToolchainLockError("Revisione sorgente nel lock non valida.")
    repository, digest = _split_reference(payload["immutable_reference"])
    if repository != payload["image_repository"]:
        raise ToolchainLockError("Repository e riferimento immutabile non coerenti.")
    return {
        **payload,
        "digest": digest,
    }


def immutable_reference(lock: dict[str, Any]) -> str:
    """Return the fully qualified immutable reference from a validated lock."""

    return str(lock["immutable_reference"])
