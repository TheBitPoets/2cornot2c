#!/usr/bin/env python3
"""Validate TheBitLab course environment manifests.

The contract is intentionally capability-based: courses declare what they need,
while TheBitLab maps capabilities to concrete classroom profiles.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "thebitlab.course-environment.v1"
PORTABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
PYTHON_RANGE_RE = re.compile(r"^>=([0-9]+)\.([0-9]+),<([0-9]+)\.([0-9]+)$")

KNOWN_PROFILES = frozenset({"docker-light", "vm-gui"})

# Registry state is deliberately different from availability. Planned capabilities
# are known to the contract but must not be accepted as required until a profile
# implementation has been certified.
KNOWN_CAPABILITIES = frozenset(
    {
        "workspace.v1",
        "shell.v1",
        "python.v1",
        "git.basic.v1",
        "node.v1",
        "sqlite.v1",
        "compiler.c.v1",
        "browser.local.v1",
        "editor.vscode.v1",
        "flowchart.lab.v1",
        "runtime.romeo-sim.v1",
    }
)

PROFILE_CAPABILITIES = {
    "docker-light": frozenset(
        {
            "workspace.v1",
            "shell.v1",
            "python.v1",
            "git.basic.v1",
            "node.v1",
            "sqlite.v1",
            "compiler.c.v1",
        }
    ),
    "vm-gui": frozenset(
        {
            "workspace.v1",
            "shell.v1",
            "python.v1",
            "git.basic.v1",
            "compiler.c.v1",
            "browser.local.v1",
        }
    ),
}

KNOWN_FALLBACKS = frozenset({"flowchart.manual-evidence.v1"})


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _portable_id(value: Any) -> bool:
    text = _text(value)
    return bool(text and PORTABLE_ID_RE.fullmatch(text))


def _unique_portable_strings(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    if any(not _portable_id(item) for item in value):
        return False
    return len(value) == len(set(value))


def _safe_relative_path(value: Any) -> bool:
    text = _text(value)
    if not text or "\\" in text or text.startswith("/"):
        return False
    path = PurePosixPath(text)
    return not path.is_absolute() and ".." not in path.parts


def _validate_baseline(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("baseline deve essere un oggetto")
        return
    if _text(value.get("os_family")) != "linux":
        errors.append("baseline.os_family deve essere linux per i profili classroom v1")
    python_range = _text(value.get("python"))
    match = PYTHON_RANGE_RE.fullmatch(python_range)
    if not match:
        errors.append("baseline.python deve usare il formato >=X.Y,<A.B")
        return
    lower = (int(match.group(1)), int(match.group(2)))
    upper = (int(match.group(3)), int(match.group(4)))
    if lower >= upper:
        errors.append("baseline.python deve avere un limite superiore maggiore del minimo")


def _validate_profiles(value: Any, errors: list[str]) -> list[str]:
    if not _unique_portable_strings(value):
        errors.append("supported_profiles deve essere una lista non vuota di ID unici")
        return []
    profiles = list(value)
    unknown = sorted(set(profiles) - KNOWN_PROFILES)
    if unknown:
        errors.append(f"supported_profiles contiene profili sconosciuti: {', '.join(unknown)}")
    return [profile for profile in profiles if profile in KNOWN_PROFILES]


def _validate_capability_list(
    value: Any,
    *,
    field: str,
    allow_empty: bool,
    errors: list[str],
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"capabilities.{field} deve essere una lista")
        return []
    if not allow_empty and not value:
        errors.append(f"capabilities.{field} non può essere vuota")
    if any(not _portable_id(item) for item in value):
        errors.append(f"capabilities.{field} contiene ID non portabili")
        return []
    if len(value) != len(set(value)):
        errors.append(f"capabilities.{field} contiene duplicati")
    unknown = sorted(set(value) - KNOWN_CAPABILITIES)
    if unknown:
        errors.append(f"capabilities.{field} contiene capability sconosciute: {', '.join(unknown)}")
    return [item for item in value if item in KNOWN_CAPABILITIES]


def _validate_fallbacks(value: Any, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append("capabilities.fallback deve essere una lista")
        return []
    capabilities: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        prefix = f"capabilities.fallback[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        capability = _text(item.get("capability"))
        if capability not in KNOWN_CAPABILITIES:
            errors.append(f"{prefix}.capability sconosciuta: {capability or '<mancante>'}")
        elif capability in seen:
            errors.append(f"capabilities.fallback contiene capability duplicata: {capability}")
        else:
            seen.add(capability)
            capabilities.append(capability)
        fallback_id = _text(item.get("fallback_id"))
        if fallback_id not in KNOWN_FALLBACKS:
            errors.append(f"{prefix}.fallback_id sconosciuto: {fallback_id or '<mancante>'}")
        outcomes = item.get("preserves_outcomes")
        if not _unique_portable_strings(outcomes):
            errors.append(f"{prefix}.preserves_outcomes deve essere una lista non vuota di ID unici")
        if not _text(item.get("student_path")):
            errors.append(f"{prefix}.student_path deve descrivere il percorso equivalente")
    return capabilities


def _validate_capabilities(value: Any, profiles: list[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("capabilities deve essere un oggetto")
        return
    required = _validate_capability_list(
        value.get("required"), field="required", allow_empty=False, errors=errors
    )
    optional = _validate_capability_list(
        value.get("optional", []), field="optional", allow_empty=True, errors=errors
    )
    fallback = _validate_fallbacks(value.get("fallback", []), errors)

    buckets = {
        "required": set(required),
        "optional": set(optional),
        "fallback": set(fallback),
    }
    names = list(buckets)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            overlap = sorted(buckets[first] & buckets[second])
            if overlap:
                errors.append(
                    f"capability presente sia in {first} sia in {second}: {', '.join(overlap)}"
                )

    for profile in profiles:
        available = PROFILE_CAPABILITIES[profile]
        missing = sorted(set(required) - available)
        if missing:
            errors.append(
                f"profilo {profile} non fornisce capability required certificate: {', '.join(missing)}"
            )


def _validate_workspace(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("workspace deve essere un oggetto")
        return
    if not _safe_relative_path(value.get("course_root")):
        errors.append("workspace.course_root deve essere un path relativo sicuro")
    for field in ("student_writable", "teacher_assets_exposed"):
        if not isinstance(value.get(field), bool):
            errors.append(f"workspace.{field} deve essere boolean")
    if value.get("teacher_assets_exposed") is True:
        errors.append("workspace.teacher_assets_exposed deve essere false nel contratto studente")


def _validate_network(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("network deve essere un oggetto")
        return
    for field in ("interactive_required", "grading_required"):
        if not isinstance(value.get(field), bool):
            errors.append(f"network.{field} deve essere boolean")


def validate_course_environment_manifest(manifest: Any) -> list[str]:
    """Return deterministic validation errors for one course environment manifest."""

    if not isinstance(manifest, dict):
        return ["course environment manifest deve essere un oggetto JSON"]

    errors: list[str] = []
    if _text(manifest.get("schema_version")) != SCHEMA_VERSION:
        errors.append(f"schema_version deve essere {SCHEMA_VERSION}")
    if not _portable_id(manifest.get("course_id")):
        errors.append("course_id deve essere un ID portabile")

    profiles = _validate_profiles(manifest.get("supported_profiles"), errors)
    _validate_baseline(manifest.get("baseline"), errors)
    _validate_capabilities(manifest.get("capabilities"), profiles, errors)
    _validate_workspace(manifest.get("workspace"), errors)
    _validate_network(manifest.get("network"), errors)

    notes = manifest.get("notes", {})
    if notes is not None and not isinstance(notes, dict):
        errors.append("notes deve essere un oggetto se presente")

    return errors


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest root non è un oggetto")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TheBitLab course environment v1 manifest")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        manifest = load_manifest(args.manifest)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}")
        return 2

    errors = validate_course_environment_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"PASS: {args.manifest} conforms to {SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
