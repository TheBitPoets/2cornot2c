"""Resolve AI credentials outside the checkout, with local-file compatibility."""

from __future__ import annotations

import os
from pathlib import Path


def user_secret_path() -> Path:
    return Path.home() / ".thebitlab-secrets" / "ai.secret"


def resolve_path(local_path: Path) -> Path:
    """An explicit path never falls back to another credentials file."""
    configured = os.environ.get("THEBITLAB_AI_SECRET_FILE", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            raise ValueError("THEBITLAB_AI_SECRET_FILE deve essere un percorso assoluto.")
        return path
    external = user_secret_path()
    return external if external.exists() else local_path


def read_env(local_path: Path) -> dict[str, str]:
    path = resolve_path(local_path)
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values
