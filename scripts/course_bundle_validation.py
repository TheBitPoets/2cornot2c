"""Structural and cross-document validation for TheBitLab course bundles."""

from __future__ import annotations

from collections.abc import Mapping
import ipaddress
import json
from pathlib import Path
import re
import unicodedata
from typing import Any
from urllib.parse import urlsplit

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
_SAFE_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
_SOURCE_URL_PATH_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


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
    if not _SAFE_PATH.fullmatch(path):
        errors.append("path contains a character outside the safe manifest alphabet")
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


def validate_source_url(url: str) -> list[str]:
    """Validate the provider-independent HTTPS repository URL baseline."""

    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return ["source URL has an invalid port"]

    errors: list[str] = []
    host = parsed.hostname
    if parsed.scheme != "https" or host is None:
        errors.append("source URL must use HTTPS and include a host")
        return errors
    if parsed.username is not None or parsed.password is not None:
        errors.append("source URL must not contain userinfo")
    if parsed.query or parsed.fragment:
        errors.append("source URL must not contain a query or fragment")
    if port not in (None, 443):
        errors.append("source URL port requires provider-specific policy; only 443 is allowed")

    path_parts = parsed.path.split("/")
    if (
        len(path_parts) < 3
        or path_parts[0] != ""
        or any(
            part in ("", ".", "..") or not _SOURCE_URL_PATH_SEGMENT.fullmatch(part)
            for part in path_parts[1:]
        )
    ):
        errors.append(
            "source URL path must contain owner and repository slug segments "
            "without empty, '.' or '..' components"
        )

    try:
        ipaddress.ip_address(host)
    except ValueError:
        labels = host.split(".")
        if set(host) <= set("0123456789."):
            errors.append("source URL host is an invalid or ambiguous IP address")
        elif (
            len(host) > 253
            or len(labels) < 2
            or any(not _HOST_LABEL.fullmatch(label) for label in labels)
        ):
            errors.append("source URL host is not a valid public DNS name")
    else:
        errors.append("source URL must use a DNS hostname, not an IP address")
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


def _final_destination_paths(bundle: Mapping[str, Any]) -> list[tuple[str, str]]:
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
            paths.append((f"{prefix}.target_path", item["target_path"]))
            paths.extend(
                (
                    f"{prefix}.dependencies.{dependency_index}.target_path",
                    dependency["target_path"],
                )
                for dependency_index, dependency in enumerate(
                    item.get("dependencies", [])
                )
            )
    paths.extend(
        (f"local_extensions.{index}.override_path", extension["override_path"])
        for index, extension in enumerate(bundle.get("local_extensions", []))
    )
    return paths


def _reserved_namespace_errors(bundle: Mapping[str, Any]) -> list[str]:
    return [
        f"{location}: path uses reserved .imports namespace"
        for location, path in _final_destination_paths(bundle)
        if path.split("/", 1)[0].casefold() == ".imports"
    ]


def _materialized_paths(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
    lineage: tuple[str, ...],
) -> list[str]:
    paths = [path for _, path in _final_destination_paths(bundle)]
    for imported in bundle.get("imports", []):
        if imported.get("all") is not True:
            continue
        bundle_id = imported["bundle_id"]
        source = imported_bundles.get(bundle_id)
        if source is None or bundle_id in lineage:
            continue
        paths.extend(
            f".imports/{bundle_id}/{path}"
            for path in _materialized_paths(
                source, imported_bundles, (*lineage, bundle_id)
            )
        )
    return list(dict.fromkeys(paths))


def _full_import_entries(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    lineage = (str(bundle.get("id", "<root>")),)
    for imported in bundle.get("imports", []):
        if imported.get("all") is not True:
            continue
        bundle_id = imported["bundle_id"]
        source = imported_bundles.get(bundle_id)
        if source is None or bundle_id in lineage:
            continue
        entries.extend(
            (f"full import {bundle_id!r}", f".imports/{bundle_id}/{path}")
            for path in _materialized_paths(
                source, imported_bundles, (*lineage, bundle_id)
            )
        )
    return entries


def _collision_errors(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
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
    referenceable_paths = {path for _, path in target_entries}
    target_entries.extend(_full_import_entries(bundle, imported_bundles))

    local_paths: list[str] = []
    seen_local_paths: set[str] = set()
    for path in _content_paths(bundle):
        if path not in referenceable_paths and path not in seen_local_paths:
            local_paths.append(path)
            seen_local_paths.add(path)

    seen: dict[tuple[str, ...], tuple[str, str]] = {}
    entries = [*target_entries, *(("local content", path) for path in local_paths)]
    for kind, path in entries:
        key = portable_path_key(path)
        previous = seen.get(key)
        if previous is not None:
            errors.append(
                f"portable path collision: {previous[0]} {previous[1]!r} and "
                f"{kind} {path!r}"
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

    content_paths = set(_content_paths(bundle))
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
        if extension["override_path"] not in content_paths:
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


def generate_index(
    bundle: Mapping[str, Any],
    *,
    imported_bundles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate the canonical flat index, including recursive full imports."""

    imports = imported_bundles or {}

    def compose(
        manifest: Mapping[str, Any], lineage: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        units: list[dict[str, Any]] = []
        for imported in manifest.get("imports", []):
            if imported.get("all") is not True:
                continue
            bundle_id = imported["bundle_id"]
            source = imports.get(bundle_id)
            if source is None or bundle_id in lineage:
                continue
            for unit in compose(source, (*lineage, bundle_id)):
                units.append(
                    {
                        **unit,
                        "id": f"{bundle_id}-{unit['id']}",
                        "items": [
                            {
                                **item,
                                "path": f".imports/{bundle_id}/{item['path']}",
                            }
                            for item in unit["items"]
                        ],
                    }
                )

        local_units: list[dict[str, Any]] = []
        for position, unit in enumerate(manifest["content"]["units"], start=1):
            items = [
                {"type": item_type, "path": path}
                for collection, item_type in COLLECTION_TYPES
                for path in unit.get(collection, [])
            ]
            local_units.append(
                {
                    "id": unit["id"],
                    "title": unit["title"],
                    "order": unit.get("order", position),
                    "items": items,
                }
            )
        local_units.sort(key=lambda unit: (unit["order"], unit["id"]))
        return [*units, *local_units]

    root_id = str(bundle.get("id", "<root>"))
    return {"units": compose(bundle, (root_id,))}


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
        errors.extend(
            f"{location}: {message}" for message in validate_portable_path(path)
        )
    for import_index, imported in enumerate(bundle.get("imports", [])):
        errors.extend(
            f"imports.{import_index}.source_url: {message}"
            for message in validate_source_url(imported["source_url"])
        )

    unit_ids = [unit["id"] for unit in bundle["content"]["units"]]
    if len(unit_ids) != len(set(unit_ids)):
        errors.append("content.units ids must be unique")

    errors.extend(_reserved_namespace_errors(bundle))
    errors.extend(_collision_errors(bundle, imports))
    errors.extend(_reference_errors(bundle, imports))
    errors.extend(_cycle_errors(bundle, imports))

    canonical_index = generate_index(bundle, imported_bundles=imports)
    composed_ids = [unit["id"] for unit in canonical_index["units"]]
    if len(composed_ids) != len(set(composed_ids)):
        errors.append("composed content.units ids must be globally unique")
    if index is not None and index != canonical_index:
        errors.append("index.json is not the canonical index derived from bundle.json")
    return errors


def validate_bundle_reference(reference: Mapping[str, Any]) -> list[str]:
    """Validate an external BundleReference document."""

    errors = validate_schema(reference, "bundle-reference.schema.json")
    if errors:
        return errors
    errors.extend(
        f"source_url: {message}"
        for message in validate_source_url(reference["source_url"])
    )
    return errors
