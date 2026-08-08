"""Structural and cross-document validation for TheBitLab course bundles."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
COLLECTION_TYPES = (
    ("activities", "activity"),
    ("materials", "material"),
    ("media", "media"),
    ("handouts", "handout"),
)
_WINDOWS_RESERVED = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE
)
_WINDOWS_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')


def load_json(path: Path) -> dict[str, Any]:
    """Load a UTF-8 JSON object from *path*."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _load_schema(name: str) -> dict[str, Any]:
    return load_json(SCHEMA_DIR / name)


def _json_path(error: Any) -> str:
    return ".".join(str(part) for part in error.absolute_path) or "$"


def validate_schema(instance: Mapping[str, Any], schema_name: str) -> list[str]:
    """Return deterministic Draft 2020-12 schema errors for *instance*."""

    schema = _load_schema(schema_name)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{_json_path(error)}: {error.message}"
        for error in sorted(
            validator.iter_errors(instance),
            key=lambda item: (list(item.absolute_path), item.message),
        )
    ]


def portable_path_key(path: str) -> tuple[str, ...]:
    """Return the NFC, case-folded Windows-portable collision key."""

    return tuple(
        unicodedata.normalize("NFC", part).casefold().rstrip(". ")
        for part in path.split("/")
    )


def validate_portable_path(path: str) -> list[str]:
    """Validate path rules that JSON Schema cannot express portably."""

    errors: list[str] = []
    parts = path.split("/")
    if unicodedata.normalize("NFC", path) != path:
        errors.append("path is not Unicode NFC")
    if any(part in ("", ".", "..") for part in parts):
        errors.append("path contains an empty, '.' or '..' component")
    if any(part.endswith((".", " ")) for part in parts):
        errors.append("path component ends with a dot or space")
    if any(_WINDOWS_INVALID.search(part) for part in parts):
        errors.append("path contains a character forbidden on Windows")
    if any(part.casefold() == ".git" for part in parts):
        errors.append("path contains reserved .git metadata")
    if any(_WINDOWS_RESERVED.fullmatch(part) for part in parts):
        errors.append("path contains a reserved Windows name")
    return errors


def _manifest_paths(bundle: Mapping[str, Any]) -> list[tuple[str, str]]:
    paths: list[tuple[str, str]] = []
    for unit_index, unit in enumerate(bundle.get("content", {}).get("units", [])):
        for collection, _ in COLLECTION_TYPES:
            for item_index, path in enumerate(unit.get(collection, [])):
                paths.append(
                    (f"content.units.{unit_index}.{collection}.{item_index}", path)
                )
    for import_index, imported in enumerate(bundle.get("imports", [])):
        for item_index, item in enumerate(imported.get("items", [])):
            prefix = f"imports.{import_index}.items.{item_index}"
            paths.extend(((f"{prefix}.path", item["path"]), (f"{prefix}.target_path", item["target_path"])))
            for dependency_index, dependency in enumerate(item.get("dependencies", [])):
                dep_prefix = f"{prefix}.dependencies.{dependency_index}"
                paths.extend(
                    (
                        (f"{dep_prefix}.path", dependency["path"]),
                        (f"{dep_prefix}.target_path", dependency["target_path"]),
                    )
                )
    for extension_index, extension in enumerate(bundle.get("local_extensions", [])):
        paths.append(
            (f"local_extensions.{extension_index}.override_path", extension["override_path"])
        )
        ref_path = extension.get("ref", "").partition("::")[2]
        if ref_path:
            paths.append((f"local_extensions.{extension_index}.ref", ref_path))
    return paths


def _content_paths(bundle: Mapping[str, Any]) -> list[str]:
    return [
        path
        for unit in bundle.get("content", {}).get("units", [])
        for collection, _ in COLLECTION_TYPES
        for path in unit.get(collection, [])
    ]


def _source_item_paths(bundle: Mapping[str, Any]) -> set[str]:
    return set(_content_paths(bundle))


def _collision_errors(bundle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    target_entries: list[tuple[str, str]] = []
    for imported in bundle.get("imports", []):
        for item in imported.get("items", []):
            target_entries.append(("import target", item["target_path"]))
            target_entries.extend(
                ("dependency target", dependency["target_path"])
                for dependency in item.get("dependencies", [])
            )
    target_entries.extend(
        ("local extension", extension["override_path"])
        for extension in bundle.get("local_extensions", [])
    )

    generated_keys = {portable_path_key(path) for _, path in target_entries}
    local_paths: list[str] = []
    seen_local_paths: set[str] = set()
    for path in _content_paths(bundle):
        key = portable_path_key(path)
        if key not in generated_keys and path not in seen_local_paths:
            local_paths.append(path)
            seen_local_paths.add(path)

    seen: dict[tuple[str, ...], tuple[str, str]] = {}
    for kind, path in [*target_entries, *(("local content", value) for value in local_paths)]:
        key = portable_path_key(path)
        previous = seen.get(key)
        if previous is not None:
            errors.append(
                f"portable path collision: {previous[0]} {previous[1]!r} and {kind} {path!r}"
            )
        else:
            seen[key] = (kind, path)
    return errors


def _reference_errors(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    imports: dict[str, Mapping[str, Any]] = {}
    for imported in bundle.get("imports", []):
        bundle_id = imported["bundle_id"]
        if bundle_id in imports:
            errors.append(f"duplicate import bundle_id: {bundle_id}")
        imports[bundle_id] = imported
        source_bundle = imported_bundles.get(bundle_id)
        if source_bundle is not None:
            if source_bundle.get("id") != bundle_id:
                errors.append(
                    f"import {bundle_id} does not match source bundle id: "
                    f"{source_bundle.get('id')!r}"
                )
            if source_bundle.get("version") != imported["version"]:
                errors.append(
                    f"import {bundle_id} version {imported['version']!r} does not "
                    f"match source bundle version: {source_bundle.get('version')!r}"
                )

    content_keys = {portable_path_key(path) for path in _content_paths(bundle)}
    seen_overrides: set[tuple[str, ...]] = set()
    for extension in bundle.get("local_extensions", []):
        bundle_id, separator, source_path = extension["ref"].partition("::")
        imported = imports.get(bundle_id)
        if not separator or imported is None:
            errors.append(f"local extension references an undeclared import: {extension['ref']}")
            continue
        if "items" in imported:
            imported_paths = {item["path"] for item in imported["items"]}
            if source_path not in imported_paths:
                errors.append(f"local extension references an unimported item: {extension['ref']}")
        elif bundle_id in imported_bundles:
            if source_path not in _source_item_paths(imported_bundles[bundle_id]):
                errors.append(f"local extension references a missing item: {extension['ref']}")

        override_key = portable_path_key(extension["override_path"])
        if override_key in seen_overrides:
            errors.append(f"duplicate local extension override: {extension['override_path']}")
        seen_overrides.add(override_key)
        if override_key not in content_keys:
            errors.append(
                f"local extension override is not referenced by content.units: {extension['override_path']}"
            )
    return errors


def _cycle_errors(
    root: Mapping[str, Any], imported_bundles: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    manifests = {root.get("id", "<root>"): root, **imported_bundles}
    graph = {
        bundle_id: [
            imported["bundle_id"]
            for imported in manifest.get("imports", [])
            if imported["bundle_id"] in manifests
        ]
        for bundle_id, manifest in manifests.items()
    }
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(bundle_id: str) -> list[str] | None:
        if bundle_id in visiting:
            start = visiting.index(bundle_id)
            return [*visiting[start:], bundle_id]
        if bundle_id in visited:
            return None
        visiting.append(bundle_id)
        for dependency in graph[bundle_id]:
            cycle = visit(dependency)
            if cycle:
                return cycle
        visiting.pop()
        visited.add(bundle_id)
        return None

    for bundle_id in graph:
        cycle = visit(bundle_id)
        if cycle:
            return [f"import cycle: {' -> '.join(cycle)}"]
    return []


def generate_index(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Generate the canonical flat index for the local manifest units."""

    units: list[dict[str, Any]] = []
    for position, unit in enumerate(bundle["content"]["units"], start=1):
        items = [
            {"type": item_type, "path": path}
            for collection, item_type in COLLECTION_TYPES
            for path in unit.get(collection, [])
        ]
        units.append(
            {
                "id": unit["id"],
                "title": unit["title"],
                "order": unit.get("order", position),
                "items": items,
            }
        )
    units.sort(key=lambda unit: (unit["order"], unit["id"]))
    return {"units": units}


def validate_bundle(
    bundle: Mapping[str, Any],
    *,
    index: Mapping[str, Any] | None = None,
    imported_bundles: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    """Validate one manifest and optional cross-document context."""

    errors = validate_schema(bundle, "course-bundle.schema.json")
    if errors:
        return errors

    imports = imported_bundles or {}
    for location, path in _manifest_paths(bundle):
        errors.extend(f"{location}: {message}" for message in validate_portable_path(path))

    unit_ids = [unit["id"] for unit in bundle["content"]["units"]]
    if len(unit_ids) != len(set(unit_ids)):
        errors.append("content.units ids must be unique")

    errors.extend(_collision_errors(bundle))
    errors.extend(_reference_errors(bundle, imports))
    errors.extend(_cycle_errors(bundle, imports))
    if index is not None and index != generate_index(bundle):
        errors.append("index.json is not the canonical index derived from bundle.json")
    return errors


def validate_bundle_reference(reference: Mapping[str, Any]) -> list[str]:
    """Validate an external BundleReference document."""

    return validate_schema(reference, "bundle-reference.schema.json")
