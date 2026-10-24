#!/usr/bin/env python3
"""Shared, stdlib-only contract for the external pilot environment file."""

from __future__ import annotations

import base64
import binascii
import os
import re
import stat
from pathlib import Path
from typing import Mapping


REQUIRED_EXTERNAL_NAMES = frozenset(
    {
        "THEBITLAB_TEACHER_TOKEN",
        "THEBITLAB_GOOGLE_CLIENT_ID",
        "THEBITLAB_GOOGLE_CLIENT_SECRET",
        "THEBITLAB_AUTH_CSRF_SECRET_B64",
        "THEBITLAB_RATE_LIMIT_PEPPER_B64",
        "THEBITLAB_TUI_PAIRING_PEPPER_B64",
    }
)
GITHUB_EXTERNAL_NAMES = frozenset(
    {
        "THEBITLAB_GITHUB_CLIENT_ID",
        "THEBITLAB_GITHUB_CLIENT_SECRET",
    }
)
ALLOWED_EXTERNAL_NAMES = REQUIRED_EXTERNAL_NAMES | GITHUB_EXTERNAL_NAMES
OPAQUE_SECRET_NAMES = frozenset(
    {
        "THEBITLAB_TEACHER_TOKEN",
        "THEBITLAB_GOOGLE_CLIENT_SECRET",
        "THEBITLAB_GITHUB_CLIENT_SECRET",
    }
)
BASE64URL_SECRET_NAMES = (
    "THEBITLAB_AUTH_CSRF_SECRET_B64",
    "THEBITLAB_RATE_LIMIT_PEPPER_B64",
    "THEBITLAB_TUI_PAIRING_PEPPER_B64",
)
_IDENTIFIER_VALUE_RE = re.compile(r"^[A-Za-z0-9._~+/=-]+$")
_BASE64URL_VALUE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class DeploymentValidationError(ValueError):
    """A safe configuration error that never needs to include secret values."""


def check_environment_file(path: Path) -> None:
    """Require a regular, non-symlink environment file with private permissions."""

    try:
        metadata = path.lstat()
    except OSError as exc:
        raise DeploymentValidationError(
            f"Riferimento esterno assente o non accessibile: {path}"
        ) from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise DeploymentValidationError(f"Riferimento esterno non regolare: {path}")
    if os.name != "nt" and metadata.st_mode & 0o027:
        raise DeploymentValidationError(
            f"Permessi troppo ampi sul riferimento esterno: {path}"
        )


def parse_environment_file(path: Path) -> dict[str, str]:
    """Parse the deliberately small, unquoted external-file contract."""

    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise DeploymentValidationError("EnvironmentFile non leggibile.") from exc
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export ") or "=" not in line:
            raise DeploymentValidationError(
                f"EnvironmentFile: sintassi non valida alla riga {line_number}."
            )
        key, value = line.split("=", 1)
        if (
            not key
            or key != key.strip()
            or not key.replace("_", "A").isalnum()
            or not key[0].isalpha()
        ):
            raise DeploymentValidationError(
                f"EnvironmentFile: nome non valido alla riga {line_number}."
            )
        if key in values:
            raise DeploymentValidationError(
                f"EnvironmentFile: variabile duplicata alla riga {line_number}."
            )
        if (
            not value
            or value != value.strip()
            or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value)
        ):
            raise DeploymentValidationError(
                f"EnvironmentFile: valore non valido alla riga {line_number}."
            )
        values[key] = value
    return values


def validate_environment_names(
    values: Mapping[str, str], *, github_oauth: bool
) -> None:
    """Fail closed unless the external file has exactly the enabled name contract."""

    errors: list[str] = []
    missing = REQUIRED_EXTERNAL_NAMES.difference(values)
    unexpected = set(values).difference(ALLOWED_EXTERNAL_NAMES)
    present_github = GITHUB_EXTERNAL_NAMES.intersection(values)
    if missing:
        errors.append("variabili obbligatorie omesse: " + ", ".join(sorted(missing)))
    if unexpected:
        errors.append("variabili non ammesse: " + ", ".join(sorted(unexpected)))
    if github_oauth and present_github != GITHUB_EXTERNAL_NAMES:
        errors.append("GitHub OAuth: client ID e client secret esterni sono entrambi obbligatori")
    if not github_oauth and present_github:
        errors.append("GitHub OAuth: credenziali presenti ma feature disabilitata")
    if errors:
        raise DeploymentValidationError(
            "EnvironmentFile non valido (valori omessi):\n- " + "\n- ".join(errors)
        )


def validate_external_environment(
    values: Mapping[str, str], *, github_oauth: bool
) -> None:
    """Validate the complete runtime contract without deployment-only dependencies."""

    validate_environment_names(values, github_oauth=github_oauth)
    errors: list[str] = []
    for name in OPAQUE_SECRET_NAMES.intersection(values):
        value = values[name]
        if not 32 <= len(value) <= 4096 or _IDENTIFIER_VALUE_RE.fullmatch(value) is None:
            errors.append(f"{name}: forma non valida")

    client_id_lengths = {
        "THEBITLAB_GOOGLE_CLIENT_ID": (6, 255),
        "THEBITLAB_GITHUB_CLIENT_ID": (1, 255),
    }
    for name, (minimum, maximum) in client_id_lengths.items():
        value = values.get(name)
        if value is not None and (
            not minimum <= len(value) <= maximum
            or _IDENTIFIER_VALUE_RE.fullmatch(value) is None
        ):
            errors.append(f"{name}: forma non valida")

    decoded_secrets: list[bytes] = []
    for name in BASE64URL_SECRET_NAMES:
        value = values[name]
        if not 43 <= len(value) <= 86 or _BASE64URL_VALUE_RE.fullmatch(value) is None:
            errors.append(f"{name}: forma non valida")
            continue
        try:
            decoded = base64.b64decode(
                value + "=" * (-len(value) % 4),
                altchars=b"-_",
                validate=True,
            )
        except (binascii.Error, ValueError):
            errors.append(f"{name}: base64url non valida")
            continue
        if not 32 <= len(decoded) <= 64:
            errors.append(f"{name}: deve rappresentare 32-64 byte")
        decoded_secrets.append(decoded)
    if len(decoded_secrets) != len(set(decoded_secrets)):
        errors.append("I segreti CSRF, rate limit e pairing devono essere indipendenti")

    if errors:
        raise DeploymentValidationError(
            "EnvironmentFile non valido (valori omessi):\n- " + "\n- ".join(errors)
        )
