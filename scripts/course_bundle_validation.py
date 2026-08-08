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

    errors: list[str] = []
    if any(ord(character) <= 0x20 or ord(character) == 0x7F for character in url):
        errors.append("source URL must not contain whitespace or control characters")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        errors.append("source URL has an invalid port")
        return errors

    host = parsed.hostname
    if parsed.scheme != "https" or host is None:
        errors.append("source URL must use HTTPS and include a host")
        return errors
    if parsed.username is not None or parsed.password is not None:
        errors.append("source URL must not contain userinfo")
    if parsed.query or parsed.fragment:
        errors.append("source URL must not contain a query or fragment")
    authority = parsed.netloc.rsplit("@", 1)[-1]
    if ":" in authority and authority.rsplit(":", 1)[1] != "443":
        errors.append("source URL port must be omitted or written exactly as 443")
    elif port not in (None, 443):
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


def _content_items(bundle: Mapping[str, Any]) -> list[tuple[str, str]]:
    return [
        (item_type, path)
        for unit in bundle.get("content", {}).get("units", [])
        for collection, item_type in COLLECTION_TYPES
        for path in unit.get(collection, [])
    ]


def _content_paths(bundle: Mapping[str, Any]) -> list[str]:
    return [path for _, path in _content_items(bundle)]


def _content_path_types(bundle: Mapping[str, Any]) -> dict[str, set[str]]:
    path_types: dict[str, set[str]] = {}
    for item_type, path in _content_items(bundle):
        path_types.setdefault(path, set()).add(item_type)
    return path_types


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
    descendant_by_prefix: dict[tuple[str, ...], tuple[str, str]] = {}
    entries = [*target_entries, *(("local content", path) for path in local_paths)]
    for kind, path in entries:
        key = portable_path_key(path)
        previous = seen.get(key)
        if previous is None:
            previous = next(
                (
                    seen[prefix]
                    for length in range(1, len(key))
                    if (prefix := key[:length]) in seen
                ),
                None,
            )
        if previous is None:
            previous = descendant_by_prefix.get(key)
        if previous is not None:
            errors.append(
                f"portable path collision: {previous[0]} {previous[1]!r} and "
                f"{kind} {path!r}"
            )
        seen.setdefault(key, (kind, path))
        for length in range(1, len(key)):
            descendant_by_prefix.setdefault(key[:length], (kind, path))
    return errors


def _reference_errors(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors: list[str] = []
    imports: dict[str, Mapping[str, Any]] = {}
    content_types = _content_path_types(bundle)
    for path, item_types in content_types.items():
        if len(item_types) > 1:
            errors.append(
                f"content path {path!r} is referenced with conflicting types: "
                f"{', '.join(sorted(item_types))}"
            )

    for imported in bundle.get("imports", []):
        bundle_id = imported["bundle_id"]
        if bundle_id in imports:
            errors.append(f"duplicate import bundle_id: {bundle_id}")
        imports[bundle_id] = imported
        source_bundle = imported_bundles.get(bundle_id)
        source_matches = source_bundle is not None
        if source_bundle is not None:
            if source_bundle.get("id") != bundle_id:
                source_matches = False
                errors.append(
                    f"import {bundle_id} does not match source bundle id: "
                    f"{source_bundle.get('id')!r}"
                )
            if source_bundle.get("version") != imported["version"]:
                source_matches = False
                errors.append(
                    f"import {bundle_id} version {imported['version']!r} does not "
                    f"match source bundle version: {source_bundle.get('version')!r}"
                )
        source_content_types = (
            _content_path_types(source_bundle) if source_matches else {}
        )

        imported_source_types: dict[str, set[str]] = {}
        for item in imported.get("items", []):
            imported_source_types.setdefault(item["path"], set()).add(item["type"])
            if source_matches:
                actual_types = source_content_types.get(item["path"], set())
                if not actual_types:
                    errors.append(
                        f"import {bundle_id} references a missing source item: "
                        f"{item['path']!r}"
                    )
                elif item["type"] not in actual_types:
                    errors.append(
                        f"import {bundle_id} source item {item['path']!r} is declared "
                        f"as {item['type']}, but source manifest has type "
                        f"{', '.join(sorted(actual_types))}"
                    )
            referenced_types = content_types.get(item["target_path"], set())
            if referenced_types and item["type"] not in referenced_types:
                errors.append(
                    f"import target {item['target_path']!r} declared as "
                    f"{item['type']} is referenced by content.units as "
                    f"{', '.join(sorted(referenced_types))}"
                )
        for source_path, item_types in imported_source_types.items():
            if len(item_types) > 1:
                errors.append(
                    f"import {bundle_id} source path {source_path!r} has "
                    f"conflicting declared types: {', '.join(sorted(item_types))}"
                )

    seen_overrides: set[tuple[str, ...]] = set()
    for extension in bundle.get("local_extensions", []):
        bundle_id, separator, source_path = extension["ref"].partition("::")
        imported = imports.get(bundle_id)
        if not separator or imported is None:
            errors.append(f"local extension references an undeclared import: {extension['ref']}")
            continue

        source_types: set[str] = set()
        if "items" in imported:
            source_types = {
                item["type"]
                for item in imported["items"]
                if item["path"] == source_path
            }
            if not source_types:
                errors.append(f"local extension references an unimported item: {extension['ref']}")
        elif bundle_id in imported_bundles:
            source_types = _content_path_types(imported_bundles[bundle_id]).get(
                source_path, set()
            )
            if not source_types:
                errors.append(f"local extension references a missing item: {extension['ref']}")

        override_key = portable_path_key(extension["override_path"])
        if override_key in seen_overrides:
            errors.append(f"duplicate local extension override: {extension['override_path']}")
        seen_overrides.add(override_key)
        override_types = content_types.get(extension["override_path"], set())
        if not override_types:
            errors.append(
                f"local extension override is not referenced by content.units: {extension['override_path']}"
            )
        elif source_types and source_types.isdisjoint(override_types):
            errors.append(
                f"local extension override {extension['override_path']!r} is "
                f"referenced as {', '.join(sorted(override_types))}, but source "
                f"{extension['ref']!r} has type {', '.join(sorted(source_types))}"
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


def _reachable_manifest_closure(
    root: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> tuple[
    list[tuple[tuple[str, ...], Mapping[str, Any]]],
    dict[str, Mapping[str, Any]],
    list[str],
]:
    root_id = str(root.get("id", "<root>"))
    available = dict(imported_bundles)
    available.setdefault(root_id, root)
    manifests: list[tuple[tuple[str, ...], Mapping[str, Any]]] = [
        ((root_id,), root)
    ]
    valid_imports: dict[str, Mapping[str, Any]] = {}
    errors: list[str] = []
    discovered = {root_id}

    for lineage, manifest in manifests:
        for imported in manifest.get("imports", []):
            bundle_id = imported["bundle_id"]
            source = available.get(bundle_id)
            if source is None:
                if imported.get("all") is True:
                    context = " -> ".join((*lineage, bundle_id))
                    errors.append(
                        f"import closure {context}: full import source manifest "
                        "is unavailable"
                    )
                continue
            if bundle_id in discovered:
                continue
            discovered.add(bundle_id)
            source_lineage = (*lineage, bundle_id)
            schema_errors = validate_schema(source, "course-bundle.schema.json")
            if schema_errors:
                context = " -> ".join(source_lineage)
                errors.extend(
                    f"import closure {context}: {message}"
                    for message in schema_errors
                )
                continue
            valid_imports[bundle_id] = source
            manifests.append((source_lineage, source))
    return manifests, valid_imports, errors


def _local_manifest_errors(bundle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
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
    return errors


def _contextualize_errors(
    lineage: tuple[str, ...], errors: list[str]
) -> list[str]:
    if len(lineage) == 1:
        return errors
    context = " -> ".join(lineage)
    return [f"import closure {context}: {message}" for message in errors]


def _bundle_errors(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    errors = validate_schema(bundle, "course-bundle.schema.json")
    if errors:
        return errors

    manifests, valid_imports, closure_errors = _reachable_manifest_closure(
        bundle, imported_bundles
    )
    if closure_errors:
        return closure_errors

    imported_local_errors: list[str] = []
    for lineage, manifest in manifests:
        manifest_errors = _contextualize_errors(
            lineage, _local_manifest_errors(manifest)
        )
        if len(lineage) == 1:
            errors.extend(manifest_errors)
        else:
            imported_local_errors.extend(manifest_errors)
    if imported_local_errors:
        return [*errors, *imported_local_errors]

    for lineage, manifest in manifests:
        manifest_errors = [
            *_reference_errors(manifest, valid_imports),
            *_collision_errors(manifest, valid_imports),
        ]
        errors.extend(_contextualize_errors(lineage, manifest_errors))
    errors.extend(_cycle_errors(bundle, valid_imports))
    if not errors:
        canonical_index = _generate_index(bundle, valid_imports)
        composed_ids = [unit["id"] for unit in canonical_index["units"]]
        if len(composed_ids) != len(set(composed_ids)):
            errors.append("composed content.units ids must be globally unique")
    return errors


def _generate_index(
    bundle: Mapping[str, Any],
    imported_bundles: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    imports = imported_bundles

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


def generate_index(
    bundle: Mapping[str, Any],
    *,
    imported_bundles: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Generate the canonical flat index after validating the import closure."""

    imports = imported_bundles or {}
    errors = _bundle_errors(bundle, imports)
    if errors:
        raise ValueError(f"cannot generate index: {'; '.join(errors)}")
    return _generate_index(bundle, imports)


def _json_values_equal(left: Any, right: Any) -> bool:
    """Compare JSON-like values without Python's bool/integer aliasing."""

    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return left.keys() == right.keys() and all(
            _json_values_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return type(left) is type(right) and left == right


def validate_bundle(
    bundle: Mapping[str, Any],
    *,
    index: Mapping[str, Any] | None = None,
    imported_bundles: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    """Validate one manifest and optional cross-document context."""

    imports = imported_bundles or {}
    errors = _bundle_errors(bundle, imports)
    if errors:
        return errors

    canonical_index = _generate_index(bundle, imports)
    if index is not None and not _json_values_equal(index, canonical_index):
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
