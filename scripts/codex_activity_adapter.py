from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


CODEX_DRAFT_TIMEOUT_SECONDS = 240

CODEX_ACTIVITY_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "teacher_notes": {"type": "string"},
        "activity_patch_json": {"type": "string"},
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
                "required": ["path", "role", "content", "visibility", "description"],
                "additionalProperties": False,
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
    "required": ["summary", "activity_patch_json", "files", "teacher_notes", "questions", "warnings"],
    "additionalProperties": False,
}


def codex_activity_prompt() -> str:
    """Return the prompt used by the local Codex adapter."""

    return (
        "Sei un assistente per un docente che sta creando o rifinendo una activity didattica. "
        "Riceverai su stdin un JSON `activity_ai_package.v1` con prompt docente, contesto, policy e file. "
        "Non modificare file sul filesystem. Restituisci solo una bozza JSON conforme allo schema richiesto. "
        "La bozza deve essere modificabile dal docente e non deve dare per approvata nessuna decisione. "
        "Se il pacchetto contiene current_draft, usalo come bozza corrente da rifinire: applica la nuova richiesta "
        "del docente e conserva metadati e file non coinvolti dalla modifica. "
        "Quando proponi file, includi path relativo, ruolo, visibilita, descrizione e contenuto. "
        "Il campo activity_patch_json deve contenere una stringa JSON valida con le modifiche proposte alla activity."
    )


def safe_draft_file_path(path: str) -> str:
    """Return a normalized relative draft file path or raise ValueError."""

    raw_path = str(path).strip()
    if not raw_path:
        raise ValueError("La risposta Codex contiene un file senza path.")
    windows_path = PureWindowsPath(raw_path)
    posix_path = PurePosixPath(raw_path.replace("\\", "/"))
    if windows_path.is_absolute() or windows_path.drive or posix_path.is_absolute() or ".." in posix_path.parts:
        raise ValueError(f"La risposta Codex contiene un path file non consentito: {path}")
    return posix_path.as_posix()


def normalize_activity_patch(activity_patch: dict[str, Any]) -> dict[str, Any]:
    """Return an activity patch with safe asset paths when present."""

    patch = dict(activity_patch)
    assets = patch.get("assets")
    if assets is None:
        return patch
    if not isinstance(assets, list):
        raise ValueError("La risposta Codex contiene `activity_patch.assets` non valido.")
    normalized_assets = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("La risposta Codex contiene un asset non valido.")
        normalized_asset = dict(asset)
        if "path" in normalized_asset:
            normalized_asset["path"] = safe_draft_file_path(str(normalized_asset.get("path", "")))
        if "target_path" in normalized_asset:
            normalized_asset["target_path"] = safe_draft_file_path(str(normalized_asset.get("target_path", "")))
        normalized_assets.append(normalized_asset)
    patch["assets"] = normalized_assets
    return patch


def activity_patch_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the activity patch from structured Codex output."""

    if isinstance(payload.get("activity_patch"), dict):
        return payload["activity_patch"]
    patch_json = payload.get("activity_patch_json")
    if not isinstance(patch_json, str) or not patch_json.strip():
        raise ValueError("La risposta Codex non contiene `activity_patch_json` valido.")
    patch = load_activity_patch_json(patch_json)
    if not isinstance(patch, dict):
        raise ValueError("`activity_patch_json` deve contenere un oggetto JSON.")
    return patch


def load_activity_patch_json(patch_json: str) -> Any:
    """Decode Codex activity patch JSON, repairing invalid backslash escapes when safe."""

    try:
        return json.loads(patch_json)
    except json.JSONDecodeError as original_error:
        repaired = escape_invalid_json_backslashes(patch_json)
        if repaired == patch_json:
            raise ValueError(f"`activity_patch_json` non e JSON valido: {original_error}") from original_error
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as repaired_error:
            raise ValueError(f"`activity_patch_json` non e JSON valido: {repaired_error}") from repaired_error


def escape_invalid_json_backslashes(text: str) -> str:
    """Return text with JSON-invalid backslashes escaped as literal backslashes."""

    result: list[str] = []
    index = 0
    valid_escapes = {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}
    while index < len(text):
        char = text[index]
        if char != "\\":
            result.append(char)
            index += 1
            continue
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if next_char in valid_escapes:
            result.append(char)
        else:
            result.append("\\\\")
        index += 1
    return "".join(result)


def validate_codex_activity_draft(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized Codex activity draft or raise ValueError."""

    if not isinstance(payload, dict):
        raise ValueError("La risposta Codex non e un oggetto JSON.")
    activity_patch = normalize_activity_patch(activity_patch_from_payload(payload))
    files = payload.get("files", [])
    if files is None:
        files = []
    if not isinstance(files, list):
        raise ValueError("La risposta Codex contiene `files` non valido.")
    for file in files:
        if not isinstance(file, dict):
            raise ValueError("La risposta Codex contiene un file senza path.")
        file["path"] = safe_draft_file_path(str(file.get("path", "")))
        if not str(file.get("content", "")).strip():
            raise ValueError(f"La risposta Codex contiene il file `{file.get('path')}` senza contenuto.")
    return {
        "summary": str(payload.get("summary", "")).strip(),
        "teacher_notes": str(payload.get("teacher_notes", "")).strip(),
        "activity_patch": activity_patch,
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
            encoding="utf-8",
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
    }
