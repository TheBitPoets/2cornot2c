from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any


RUNTIME_EXTENSION_KEY = "thebitlab.runtime"
RUNTIME_ACTIVITY_SCHEMA_VERSION = "runtime_activity.v1"
DEFAULT_ARTIFACT_MEDIA_TYPE = "application/octet-stream"

_RUNTIME_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_ARTIFACT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_MEDIA_TYPE_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}$"
)
MAX_SUBMISSION_ARTIFACTS = 32


def _clean_text(value: Any) -> str:
    """Return a stripped string value or an empty string."""

    return value.strip() if isinstance(value, str) else ""


def _safe_relative_path(value: Any) -> bool:
    """Return whether value is a portable relative path inside an activity workspace."""

    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _valid_media_type(value: Any) -> bool:
    return bool(_MEDIA_TYPE_RE.fullmatch(_clean_text(value)))


def runtime_extension(activity: dict[str, Any]) -> dict[str, Any] | None:
    """Return the namespaced runtime extension when it is an object."""

    extensions = activity.get("extensions")
    if not isinstance(extensions, dict):
        return None
    extension = extensions.get(RUNTIME_EXTENSION_KEY)
    return extension if isinstance(extension, dict) else None


def normalize_runtime_extension(activity: dict[str, Any]) -> dict[str, Any] | None:
    """Return the stable runtime contract consumed by installed runtime plugins."""

    extension = runtime_extension(activity)
    if extension is None:
        return None

    config = extension.get("config") if isinstance(extension.get("config"), dict) else None
    submission = extension.get("submission") if isinstance(extension.get("submission"), dict) else {}
    artifacts = submission.get("artifacts") if isinstance(submission.get("artifacts"), list) else []
    required_capabilities = (
        extension.get("required_capabilities")
        if isinstance(extension.get("required_capabilities"), list)
        else []
    )
    normalized_artifacts: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        normalized_artifacts.append(
            {
                "id": _clean_text(artifact.get("id")),
                "path": _clean_text(artifact.get("path")),
                "media_type": _clean_text(artifact.get("media_type")) or DEFAULT_ARTIFACT_MEDIA_TYPE,
                "required": artifact.get("required") is not False,
            }
        )

    normalized: dict[str, Any] = {
        "schema_version": _clean_text(extension.get("schema_version")),
        "runtime_id": _clean_text(extension.get("runtime_id")),
        "required_capabilities": [
            item.strip()
            for item in required_capabilities
            if isinstance(item, str) and item.strip()
        ],
        "submission": {"artifacts": normalized_artifacts},
    }
    if config is not None:
        normalized["config"] = {
            "path": _clean_text(config.get("path")),
            "media_type": _clean_text(config.get("media_type")) or DEFAULT_ARTIFACT_MEDIA_TYPE,
        }
    else:
        normalized["config"] = None
    return normalized


def validate_runtime_extension(activity: dict[str, Any], source: str = "<activity>") -> list[str]:
    """Validate the optional runtime extension without interpreting runtime-specific data."""

    extensions = activity.get("extensions")
    if extensions is None:
        return []
    if not isinstance(extensions, dict):
        return [f"{source}: extensions deve essere un oggetto"]
    if RUNTIME_EXTENSION_KEY not in extensions:
        return []

    prefix = f"{source}: extensions.{RUNTIME_EXTENSION_KEY}"
    extension = extensions.get(RUNTIME_EXTENSION_KEY)
    if not isinstance(extension, dict):
        return [f"{prefix} deve essere un oggetto"]

    errors: list[str] = []

    schema_version = _clean_text(extension.get("schema_version"))
    if not schema_version:
        errors.append(f"{prefix}.schema_version mancante")
    elif schema_version != RUNTIME_ACTIVITY_SCHEMA_VERSION:
        errors.append(f"{prefix}.schema_version non supportata: {schema_version}")

    runtime_id = _clean_text(extension.get("runtime_id"))
    if not runtime_id:
        errors.append(f"{prefix}.runtime_id mancante")
    elif not _RUNTIME_ID_RE.fullmatch(runtime_id):
        errors.append(f"{prefix}.runtime_id deve essere un identificativo portabile")

    config = extension.get("config")
    if config is not None:
        if not isinstance(config, dict):
            errors.append(f"{prefix}.config deve essere un oggetto")
        else:
            if not _safe_relative_path(config.get("path")):
                errors.append(f"{prefix}.config.path deve essere un path relativo sicuro")
            media_type = _clean_text(config.get("media_type")) or DEFAULT_ARTIFACT_MEDIA_TYPE
            if not _valid_media_type(media_type):
                errors.append(f"{prefix}.config.media_type non valido: {media_type}")

    capabilities = extension.get("required_capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list):
            errors.append(f"{prefix}.required_capabilities deve essere una lista")
        else:
            normalized_capabilities: list[str] = []
            for index, capability in enumerate(capabilities):
                value = _clean_text(capability)
                if not value or not _CAPABILITY_RE.fullmatch(value):
                    errors.append(
                        f"{prefix}.required_capabilities[{index}] deve essere un identificativo portabile"
                    )
                    continue
                normalized_capabilities.append(value)
            if len(normalized_capabilities) != len(set(normalized_capabilities)):
                errors.append(f"{prefix}.required_capabilities non deve contenere duplicati")

    submission = extension.get("submission")
    if not isinstance(submission, dict):
        errors.append(f"{prefix}.submission deve essere un oggetto")
        return errors

    artifacts = submission.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(f"{prefix}.submission.artifacts deve essere una lista non vuota")
        return errors
    if len(artifacts) > MAX_SUBMISSION_ARTIFACTS:
        errors.append(
            f"{prefix}.submission.artifacts supera il limite di {MAX_SUBMISSION_ARTIFACTS} elementi"
        )

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, artifact in enumerate(artifacts[:MAX_SUBMISSION_ARTIFACTS]):
        artifact_prefix = f"{prefix}.submission.artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{artifact_prefix} deve essere un oggetto")
            continue
        artifact_id = _clean_text(artifact.get("id"))
        if not _ARTIFACT_ID_RE.fullmatch(artifact_id):
            errors.append(f"{artifact_prefix}.id deve essere un identificativo portabile")
        elif artifact_id in seen_ids:
            errors.append(f"{prefix}.submission.artifacts contiene id duplicato: {artifact_id}")
        else:
            seen_ids.add(artifact_id)

        path = _clean_text(artifact.get("path"))
        if not _safe_relative_path(path):
            errors.append(f"{artifact_prefix}.path deve essere un path relativo sicuro")
        elif path in seen_paths:
            errors.append(f"{prefix}.submission.artifacts contiene path duplicato: {path}")
        else:
            seen_paths.add(path)

        media_type = _clean_text(artifact.get("media_type")) or DEFAULT_ARTIFACT_MEDIA_TYPE
        if not _valid_media_type(media_type):
            errors.append(f"{artifact_prefix}.media_type non valido: {media_type}")

        required = artifact.get("required")
        if required is not None and not isinstance(required, bool):
            errors.append(f"{artifact_prefix}.required deve essere boolean")

    return errors
