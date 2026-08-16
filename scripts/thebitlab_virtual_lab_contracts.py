from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any


VIRTUAL_LAB_EXTENSION_KEY = "thebitlab.virtual_lab"
VIRTUAL_LAB_SCHEMA_VERSION = "virtual_lab.v1"
DEFAULT_SUBMISSION_MEDIA_TYPE = "application/json"

_RUNTIME_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _clean_text(value: Any) -> str:
    """Return a stripped string value or an empty string."""

    return value.strip() if isinstance(value, str) else ""


def _safe_relative_path(value: Any) -> bool:
    """Return whether value is a portable relative path inside an activity workspace."""

    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def virtual_lab_extension(activity: dict[str, Any]) -> dict[str, Any] | None:
    """Return the namespaced virtual-lab extension when it is an object."""

    extensions = activity.get("extensions")
    if not isinstance(extensions, dict):
        return None
    extension = extensions.get(VIRTUAL_LAB_EXTENSION_KEY)
    return extension if isinstance(extension, dict) else None


def normalize_virtual_lab_extension(activity: dict[str, Any]) -> dict[str, Any] | None:
    """Return the stable virtual-lab contract consumed by runtime adapters."""

    extension = virtual_lab_extension(activity)
    if extension is None:
        return None

    submission = extension.get("submission") if isinstance(extension.get("submission"), dict) else {}
    capabilities = extension.get("capabilities") if isinstance(extension.get("capabilities"), list) else []
    return {
        "schema_version": _clean_text(extension.get("schema_version")),
        "runtime": _clean_text(extension.get("runtime")),
        "scenario_id": _clean_text(extension.get("scenario_id")),
        "submission": {
            "path": _clean_text(submission.get("path")),
            "media_type": _clean_text(submission.get("media_type")) or DEFAULT_SUBMISSION_MEDIA_TYPE,
        },
        "capabilities": [item.strip() for item in capabilities if isinstance(item, str) and item.strip()],
    }


def validate_virtual_lab_extension(activity: dict[str, Any], source: str = "<activity>") -> list[str]:
    """Validate the optional namespaced virtual-lab extension without rejecting other extensions."""

    extensions = activity.get("extensions")
    if extensions is None:
        return []
    if not isinstance(extensions, dict):
        return [f"{source}: extensions deve essere un oggetto"]
    if VIRTUAL_LAB_EXTENSION_KEY not in extensions:
        return []

    prefix = f"{source}: extensions.{VIRTUAL_LAB_EXTENSION_KEY}"
    extension = extensions.get(VIRTUAL_LAB_EXTENSION_KEY)
    if not isinstance(extension, dict):
        return [f"{prefix} deve essere un oggetto"]

    errors: list[str] = []

    schema_version = _clean_text(extension.get("schema_version"))
    if not schema_version:
        errors.append(f"{prefix}.schema_version mancante")
    elif schema_version != VIRTUAL_LAB_SCHEMA_VERSION:
        errors.append(f"{prefix}.schema_version non supportata: {schema_version}")

    runtime = _clean_text(extension.get("runtime"))
    if not runtime:
        errors.append(f"{prefix}.runtime mancante")
    elif not _RUNTIME_ID_RE.fullmatch(runtime):
        errors.append(f"{prefix}.runtime deve essere un identificativo portabile")

    scenario_id = _clean_text(extension.get("scenario_id"))
    if not scenario_id:
        errors.append(f"{prefix}.scenario_id mancante")
    elif len(scenario_id) > 128 or any(character.isspace() for character in scenario_id):
        errors.append(f"{prefix}.scenario_id deve essere un identificativo non vuoto senza spazi")

    submission = extension.get("submission")
    if not isinstance(submission, dict):
        errors.append(f"{prefix}.submission deve essere un oggetto")
    else:
        submission_path = submission.get("path")
        if not _safe_relative_path(submission_path):
            errors.append(f"{prefix}.submission.path deve essere un path relativo sicuro")
        media_type = _clean_text(submission.get("media_type")) or DEFAULT_SUBMISSION_MEDIA_TYPE
        if media_type != DEFAULT_SUBMISSION_MEDIA_TYPE:
            errors.append(
                f"{prefix}.submission.media_type non supportato: {media_type}; "
                f"per virtual_lab.v1 e ammesso solo {DEFAULT_SUBMISSION_MEDIA_TYPE}"
            )

    capabilities = extension.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list):
            errors.append(f"{prefix}.capabilities deve essere una lista")
        else:
            normalized_capabilities: list[str] = []
            for index, capability in enumerate(capabilities):
                value = _clean_text(capability)
                if not value or not _CAPABILITY_RE.fullmatch(value):
                    errors.append(f"{prefix}.capabilities[{index}] deve essere un identificativo portabile")
                    continue
                normalized_capabilities.append(value)
            if len(normalized_capabilities) != len(set(normalized_capabilities)):
                errors.append(f"{prefix}.capabilities non deve contenere duplicati")

    return errors
