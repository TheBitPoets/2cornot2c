"""Contratto immutabile dell'immagine student-dev pubblicata."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docker" / "student-dev" / "toolchain.lock.json"
SCHEMA_VERSION = "2cornot2c.student-dev-lock.v1"
EXPECTED_KEYS = {
    "schema_version",
    "version",
    "image_repository",
    "digest",
    "platforms",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class StudentDevLockError(ValueError):
    """Lock student-dev mancante o alterato."""


def load_lock(path: Path = DEFAULT_LOCK) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StudentDevLockError(f"Lock student-dev non leggibile: {path}") from error
    if not isinstance(payload, dict) or set(payload) != EXPECTED_KEYS:
        raise StudentDevLockError("Campi lock student-dev non validi.")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise StudentDevLockError("Schema lock student-dev non supportato.")
    if payload["image_repository"] != "ghcr.io/thebitpoets/2cornot2c-student-dev":
        raise StudentDevLockError("Repository student-dev non autorizzato.")
    if not isinstance(payload["digest"], str) or not DIGEST_RE.fullmatch(
        payload["digest"]
    ):
        raise StudentDevLockError("Digest student-dev non valido.")
    if payload["platforms"] != ["linux/amd64", "linux/arm64"]:
        raise StudentDevLockError("Piattaforme student-dev non valide.")
    if not isinstance(payload["version"], str) or not payload["version"]:
        raise StudentDevLockError("Versione student-dev non valida.")
    return payload


def immutable_reference(path: Path = DEFAULT_LOCK) -> str:
    lock = load_lock(path)
    return f"{lock['image_repository']}@{lock['digest']}"
