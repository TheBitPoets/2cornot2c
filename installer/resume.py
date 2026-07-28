"""Stato minimo e validato per riprendere un'installazione Windows."""

from __future__ import annotations

import json
from pathlib import Path

from installer.model import Provider


SCHEMA = "2cornot2c.install-resume.v1"
VALID_STATUSES = {"installing", "awaiting_restart"}


def resume_path() -> Path:
    return Path.home() / ".2cornot2c" / "resume-state.json"


def save_intent(provider: Provider, status: str) -> None:
    """Salva atomicamente soltanto stati conosciuti."""

    if status not in VALID_STATUSES:
        raise ValueError(f"Stato di ripresa non valido: {status}")
    destination = resume_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA,
                "provider": provider.value,
                "status": status,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)


def load_intent() -> tuple[Provider, str] | None:
    """Ignora in sicurezza file assenti, corrotti o di versioni sconosciute."""

    try:
        payload = json.loads(resume_path().read_text(encoding="utf-8"))
        if payload.get("schema_version") != SCHEMA:
            return None
        provider = Provider(payload["provider"])
        status = str(payload["status"])
        if status not in VALID_STATUSES:
            return None
        return provider, status
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def clear_intent() -> None:
    """Rimuove lo stato senza fallire quando è già assente."""

    try:
        resume_path().unlink()
    except FileNotFoundError:
        pass
