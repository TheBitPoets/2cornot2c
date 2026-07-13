from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


CODEX_DRAFT_TIMEOUT_SECONDS = 240

CODEX_ACTIVITY_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "teacher_notes": {"type": "string"},
        "activity_patch": {"type": "object"},
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "role": {"type": "string"},
                    "content": {"type": "string"},
                    "visibility": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["path", "role", "content"],
                "additionalProperties": True,
            },
        },
        "questions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["summary", "activity_patch", "files", "teacher_notes"],
    "additionalProperties": True,
}


def codex_activity_prompt() -> str:
    """Return the prompt used by the local Codex adapter."""

    return (
        "Sei un assistente per un docente che sta creando o rifinendo una activity didattica. "
        "Riceverai su stdin un JSON `activity_ai_package.v1` con prompt docente, contesto, policy e file. "
        "Non modificare file sul filesystem. Restituisci solo una bozza JSON conforme allo schema richiesto. "
        "La bozza deve essere modificabile dal docente e non deve dare per approvata nessuna decisione. "
        "Quando proponi file, includi path relativo, ruolo, visibilita, descrizione e contenuto."
    )


def validate_codex_activity_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized Codex activity draft or raise ValueError."""

    if not isinstance(payload, dict):
        raise ValueError("La risposta Codex non e un oggetto JSON.")
    if not isinstance(payload.get("activity_patch"), dict):
        raise ValueError("La risposta Codex non contiene `activity_patch` valido.")
    files = payload.get("files", [])
    if files is None:
        files = []
    if not isinstance(files, list):
        raise ValueError("La risposta Codex contiene `files` non valido.")
    for file in files:
        if not isinstance(file, dict) or not str(file.get("path", "")).strip():
            raise ValueError("La risposta Codex contiene un file senza path.")
        if not str(file.get("content", "")).strip():
            raise ValueError(f"La risposta Codex contiene il file `{file.get('path')}` senza contenuto.")
    return {
        "summary": str(payload.get("summary", "")).strip(),
        "teacher_notes": str(payload.get("teacher_notes", "")).strip(),
        "activity_patch": payload["activity_patch"],
        "files": files,
        "questions": payload.get("questions", []) if isinstance(payload.get("questions", []), list) else [],
        "warnings": payload.get("warnings", []) if isinstance(payload.get("warnings", []), list) else [],
    }


def run_codex_activity_draft(
    package: dict[str, Any],
    *,
    cwd: Path,
    codex_command: str = "codex",
    timeout_seconds: int = CODEX_DRAFT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Ask local Codex CLI for an editable activity draft."""

    codex_path = shutil.which(codex_command)
    if codex_path is None:
        raise RuntimeError("Codex CLI non trovato nel PATH della macchina docente.")

    with tempfile.TemporaryDirectory(prefix="thebitlab-codex-") as temp_dir:
        schema_path = Path(temp_dir) / "activity_draft_schema.json"
        schema_path.write_text(json.dumps(CODEX_ACTIVITY_DRAFT_SCHEMA, ensure_ascii=False, indent=2), encoding="utf-8")
        completed = subprocess.run(
            [
                codex_path,
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--output-schema",
                str(schema_path),
                codex_activity_prompt(),
            ],
            cwd=cwd,
            input=json.dumps(package, ensure_ascii=False, indent=2),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "Codex non ha restituito dettagli.").strip()
        raise RuntimeError(f"Codex exec non riuscito: {detail}")
    try:
        raw_payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"Codex non ha restituito JSON valido: {error}") from error
    draft = validate_codex_activity_draft(raw_payload)
    return {
        "adapter": "codex_exec",
        "draft": draft,
        "raw": raw_payload,
    }
