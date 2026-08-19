from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

SCHEMA_V0 = "thebitlab.content-pack.v0"
SCHEMA_V1 = "thebitlab.content-pack.v1"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SOURCE_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,63})$")
LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")

EDITORIAL_STATUSES = frozenset(
    {"draft", "reviewed", "approved", "superseded", "retired"}
)
REFERENCE_ROLES = frozenset(
    {
        "coverage-reference",
        "technical-reference",
        "teacher-reference",
        "specification",
    }
)
INDEXABLE_PROVIDERS = frozenset({"local", "github", "gitlab"})
INDEXABLE_TYPES = frozenset({"markdown"})
INDEXING_STATUSES = frozenset({"ready", "pending", "error", "disabled"})
REQUIRED_POLICIES = frozenset(
    {
        "provenance_required",
        "teacher_review_required_before_publish",
        "student_teacher_asset_separation_required",
        "ai_is_not_primary_source",
        "restricted_source_copying_forbidden",
    }
)
REQUIRED_OWNERSHIP_FIELDS = frozenset(
    {"content_origin", "redistribution_status", "editorial_copying_allowed"}
)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _portable_id(value: Any, *, source_id: bool = False) -> bool:
    text = _text(value)
    return bool((SOURCE_ID_RE if source_id else TOKEN_RE).fullmatch(text))


def _safe_relative_path(value: Any, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, str) or value != value.strip():
        return False
    if not value:
        return allow_empty
    if "\\" in value or ":" in value or value.startswith("/"):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
        and path.as_posix() == value
    )


def _list_of_unique_strings(value: Any, *, portable: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    seen: set[str] = set()
    for item in value:
        text = _text(item)
        if not text or text in seen:
            return False
        if portable and not _portable_id(text):
            return False
        seen.add(text)
    return True


def _validate_identity(pack: dict[str, Any], source: str, errors: list[str]) -> None:
    if pack.get("schema_version") != SCHEMA_V1:
        errors.append(f"{source}: schema_version deve essere {SCHEMA_V1}")
    if not _portable_id(pack.get("id")):
        errors.append(f"{source}: id deve essere un identificativo portabile")
    if not _text(pack.get("title")):
        errors.append(f"{source}: title deve essere una stringa non vuota")
    version = _text(pack.get("version"))
    if not SEMVER_RE.fullmatch(version):
        errors.append(f"{source}: version deve essere SemVer")
    status = _text(pack.get("status"))
    if status not in EDITORIAL_STATUSES:
        errors.append(
            f"{source}: status non supportato: {status or '<mancante>'}"
        )
    language = _text(pack.get("language"))
    if not LANGUAGE_RE.fullmatch(language):
        errors.append(
            f"{source}: language deve essere un tag lingua semplice "
            "(es. it, en, it-IT)"
        )


def _validate_audience(value: Any, source: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or not value:
        errors.append(f"{source}: audience deve essere un oggetto non vuoto")
        return
    for key, item in value.items():
        if not _portable_id(key):
            errors.append(f"{source}: audience contiene chiave non portabile: {key}")
        if isinstance(item, dict):
            errors.append(
                f"{source}: audience.{key} deve essere uno scalare o una lista di scalari"
            )
        elif isinstance(item, list) and any(
            isinstance(child, (dict, list)) for child in item
        ):
            errors.append(
                f"{source}: audience.{key} deve contenere solo scalari"
            )


def _validate_ownership(value: Any, source: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{source}: ownership deve essere un oggetto")
        return
    for field in sorted(REQUIRED_OWNERSHIP_FIELDS - value.keys()):
        errors.append(f"{source}: ownership.{field} mancante")
    for field in ("content_origin", "redistribution_status"):
        if field in value and not _text(value.get(field)):
            errors.append(
                f"{source}: ownership.{field} deve essere una stringa non vuota"
            )
    if "editorial_copying_allowed" in value and not isinstance(
        value.get("editorial_copying_allowed"), bool
    ):
        errors.append(
            f"{source}: ownership.editorial_copying_allowed deve essere boolean"
        )


def _validate_references(
    value: Any, source: str, errors: list[str]
) -> tuple[set[str], bool]:
    if not isinstance(value, list):
        errors.append(f"{source}: references deve essere una lista")
        return set(), False
    ids: set[str] = set()
    has_coverage_reference = False
    for index, item in enumerate(value):
        prefix = f"{source}: references[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        reference_id = _text(item.get("id"))
        if not _portable_id(reference_id):
            errors.append(f"{prefix}.id deve essere un identificativo portabile")
        elif reference_id in ids:
            errors.append(f"{source}: reference id duplicato: {reference_id}")
        else:
            ids.add(reference_id)
        for field in ("kind", "provider"):
            if not _portable_id(item.get(field)):
                errors.append(
                    f"{prefix}.{field} deve essere un identificativo portabile"
                )
        role = _text(item.get("role"))
        if role not in REFERENCE_ROLES:
            errors.append(
                f"{prefix}.role non supportato: {role or '<mancante>'}"
            )
        has_coverage_reference = (
            has_coverage_reference or role == "coverage-reference"
        )
        if not _text(item.get("title")):
            errors.append(f"{prefix}.title deve essere una stringa non vuota")
        if not _text(item.get("license_status")):
            errors.append(
                f"{prefix}.license_status deve essere una stringa non vuota"
            )
        for optional in ("uri", "access", "notes"):
            if optional in item and not isinstance(item.get(optional), str):
                errors.append(f"{prefix}.{optional} deve essere una stringa")
    return ids, has_coverage_reference


def _validate_sources(value: Any, source: str, errors: list[str]) -> set[str]:
    if not isinstance(value, list):
        errors.append(f"{source}: sources deve essere una lista")
        return set()
    ids: set[str] = set()
    for index, item in enumerate(value):
        prefix = f"{source}: sources[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        source_id = _text(item.get("id"))
        if not _portable_id(source_id, source_id=True):
            errors.append(
                f"{prefix}.id deve essere compatibile col Course Source Catalog"
            )
        elif source_id in ids:
            errors.append(f"{source}: source id duplicato: {source_id}")
        else:
            ids.add(source_id)
        if item.get("kind") != "source-package":
            errors.append(f"{prefix}.kind deve essere source-package")
        if not _text(item.get("label")):
            errors.append(f"{prefix}.label deve essere una stringa non vuota")
        source_type = _text(item.get("type"))
        if source_type not in INDEXABLE_TYPES:
            errors.append(
                f"{prefix}.type non indicizzabile: {source_type or '<mancante>'}"
            )
        provider = _text(item.get("provider"))
        if provider not in INDEXABLE_PROVIDERS:
            errors.append(
                f"{prefix}.provider non supportato dal catalogo corrente: "
                f"{provider or '<mancante>'}"
            )
        if not _portable_id(item.get("role")):
            errors.append(f"{prefix}.role deve essere un identificativo portabile")
        if not _text(item.get("license_status")):
            errors.append(
                f"{prefix}.license_status deve essere una stringa non vuota"
            )
        indexing_status = _text(item.get("indexing_status"))
        if indexing_status not in INDEXING_STATUSES:
            errors.append(
                f"{prefix}.indexing_status non supportato: "
                f"{indexing_status or '<mancante>'}"
            )
        if not _safe_relative_path(item.get("path", ""), allow_empty=True):
            errors.append(f"{prefix}.path deve essere un path relativo sicuro")
        files = item.get("files")
        if not isinstance(files, list) or not files or not _list_of_unique_strings(files):
            errors.append(
                f"{prefix}.files deve essere una lista non vuota di path unici"
            )
        elif any(not _safe_relative_path(file) for file in files):
            errors.append(f"{prefix}.files contiene path non sicuri")
        if provider == "local":
            if item.get("repository") is not None or item.get("ref") is not None:
                errors.append(
                    f"{prefix}: una fonte locale non accetta repository o ref"
                )
        elif provider in {"github", "gitlab"}:
            if _text(item.get("path")):
                errors.append(f"{prefix}: una fonte remota non accetta path locale")
            if not _text(item.get("repository")):
                errors.append(f"{prefix}.repository richiesto per fonte remota")
            if not _text(item.get("ref")):
                errors.append(f"{prefix}.ref richiesto per fonte remota")
    return ids


def _validate_coverage(
    value: Any,
    *,
    required: bool,
    source: str,
    errors: list[str],
) -> None:
    if value is None:
        if required:
            errors.append(
                f"{source}: coverage richiesto quando esiste una coverage-reference"
            )
        return
    if not isinstance(value, dict):
        errors.append(f"{source}: coverage deve essere un oggetto")
        return
    if not _safe_relative_path(value.get("path")):
        errors.append(f"{source}: coverage.path deve essere un path relativo sicuro")
    status = _text(value.get("status"))
    if status not in EDITORIAL_STATUSES:
        errors.append(f"{source}: coverage.status non supportato")


def _validate_source_refs(
    value: Any,
    *,
    known_ids: set[str],
    prefix: str,
    errors: list[str],
) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{prefix}.source_refs deve essere una lista non vuota")
        return
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        item_prefix = f"{prefix}.source_refs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_prefix} deve essere un oggetto")
            continue
        ref_id = _text(item.get("id"))
        if ref_id not in known_ids:
            errors.append(
                f"{item_prefix}.id sconosciuto: {ref_id or '<mancante>'}"
            )
        role = _text(item.get("role"))
        if not _portable_id(role):
            errors.append(
                f"{item_prefix}.role deve essere un identificativo portabile"
            )
        locator = item.get("locator", "")
        if locator is not None and not isinstance(locator, str):
            errors.append(f"{item_prefix}.locator deve essere una stringa")
        key = (ref_id, str(locator or ""))
        if key in seen:
            errors.append(
                f"{prefix}.source_refs contiene riferimento duplicato: {ref_id}"
            )
        seen.add(key)


def _validate_content_items(
    value: Any,
    *,
    known_source_ids: set[str],
    provenance_required: bool,
    source: str,
    errors: list[str],
) -> tuple[set[str], list[str]]:
    if not isinstance(value, list):
        errors.append(f"{source}: content_items deve essere una lista")
        return set(), []
    ids: set[str] = set()
    statuses: list[str] = []
    for index, item in enumerate(value):
        prefix = f"{source}: content_items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        item_id = _text(item.get("id"))
        if not _portable_id(item_id):
            errors.append(f"{prefix}.id deve essere un identificativo portabile")
        elif item_id in ids:
            errors.append(f"{source}: content item id duplicato: {item_id}")
        else:
            ids.add(item_id)
        if not _portable_id(item.get("kind")):
            errors.append(f"{prefix}.kind deve essere un identificativo portabile")
        if not _safe_relative_path(item.get("path")):
            errors.append(f"{prefix}.path deve essere un path relativo sicuro")
        order = item.get("order")
        if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
            errors.append(f"{prefix}.order deve essere un intero positivo")
        status = _text(item.get("status"))
        if status not in EDITORIAL_STATUSES:
            errors.append(f"{prefix}.status non supportato")
        else:
            statuses.append(status)
        for field in ("curriculum_topics", "activity_ids"):
            if field in item and not _list_of_unique_strings(
                item.get(field), portable=True
            ):
                errors.append(
                    f"{prefix}.{field} deve essere una lista di ID portabili unici"
                )
        if provenance_required:
            _validate_source_refs(
                item.get("source_refs"),
                known_ids=known_source_ids,
                prefix=prefix,
                errors=errors,
            )
        elif "source_refs" in item:
            _validate_source_refs(
                item.get("source_refs"),
                known_ids=known_source_ids,
                prefix=prefix,
                errors=errors,
            )
    return ids, statuses


def _validate_course_designs(value: Any, source: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{source}: course_designs deve essere una lista")
        return []
    ids: set[str] = set()
    statuses: list[str] = []
    for index, item in enumerate(value):
        prefix = f"{source}: course_designs[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        item_id = _text(item.get("id"))
        if not _portable_id(item_id):
            errors.append(f"{prefix}.id deve essere un identificativo portabile")
        elif item_id in ids:
            errors.append(f"{source}: course design id duplicato: {item_id}")
        else:
            ids.add(item_id)
        if not _safe_relative_path(item.get("path")):
            errors.append(f"{prefix}.path deve essere un path relativo sicuro")
        status = _text(item.get("status"))
        if status not in EDITORIAL_STATUSES:
            errors.append(f"{prefix}.status non supportato")
        else:
            statuses.append(status)
    return statuses


def _validate_activity_roots(value: Any, source: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{source}: activity_roots deve essere una lista")
        return
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not _safe_relative_path(item):
            errors.append(
                f"{source}: activity_roots[{index}] deve essere un path relativo sicuro"
            )
            continue
        if item in seen:
            errors.append(f"{source}: activity_roots contiene path duplicato: {item}")
        seen.add(item)


def _validate_policies(value: Any, source: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{source}: policies deve essere un oggetto")
        return {}
    for field in sorted(REQUIRED_POLICIES - value.keys()):
        errors.append(f"{source}: policies.{field} mancante")
    for field in REQUIRED_POLICIES & value.keys():
        if not isinstance(value.get(field), bool):
            errors.append(f"{source}: policies.{field} deve essere boolean")
    return value


def validate_content_pack(
    pack: Any,
    source: str = "<content-pack>",
    *,
    root: Path | None = None,
) -> list[str]:
    if not isinstance(pack, dict):
        return [f"{source}: content pack deve essere un oggetto JSON"]

    errors: list[str] = []
    _validate_identity(pack, source, errors)
    _validate_audience(pack.get("audience"), source, errors)
    _validate_ownership(pack.get("ownership"), source, errors)
    policies = _validate_policies(pack.get("policies"), source, errors)

    reference_ids, has_coverage_reference = _validate_references(
        pack.get("references"), source, errors
    )
    source_ids = _validate_sources(pack.get("sources"), source, errors)
    collisions = reference_ids & source_ids
    if collisions:
        errors.append(
            f"{source}: ID condivisi fra sources e references: "
            f"{', '.join(sorted(collisions))}"
        )
    known_ids = reference_ids | source_ids

    if isinstance(pack.get("sources"), list):
        try:
            from scripts import course_source_catalog

            course_source_catalog.normalize_course_sources(
                {"sources": project_course_design_sources(pack)}
            )
        except (TypeError, ValueError) as error:
            errors.append(
                f"{source}: sources non compatibili col Course Source Catalog: {error}"
            )

    _validate_coverage(
        pack.get("coverage"),
        required=has_coverage_reference,
        source=source,
        errors=errors,
    )
    _, content_statuses = _validate_content_items(
        pack.get("content_items"),
        known_source_ids=known_ids,
        provenance_required=policies.get("provenance_required") is True,
        source=source,
        errors=errors,
    )
    design_statuses = _validate_course_designs(
        pack.get("course_designs"), source, errors
    )
    _validate_activity_roots(pack.get("activity_roots"), source, errors)

    if (
        _text(pack.get("status")) == "approved"
        and policies.get("teacher_review_required_before_publish") is True
    ):
        if any(status != "approved" for status in content_statuses):
            errors.append(
                f"{source}: pack approved contiene content item non approved"
            )
        if any(status != "approved" for status in design_statuses):
            errors.append(
                f"{source}: pack approved contiene course design non approved"
            )
        coverage = pack.get("coverage")
        if isinstance(coverage, dict) and _text(coverage.get("status")) != "approved":
            errors.append(f"{source}: pack approved richiede coverage approved")

    if root is not None:
        errors.extend(validate_content_pack_paths(pack, root, source=source))
    return errors


def validate_content_pack_paths(
    pack: dict[str, Any], root: Path, *, source: str = "<content-pack>"
) -> list[str]:
    errors: list[str] = []
    root = root.resolve()

    def check_file(path_value: Any, label: str) -> None:
        if not _safe_relative_path(path_value):
            return
        path = (root / str(path_value)).resolve(strict=False)
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"{source}: {label} esce dalla root")
            return
        if not path.is_file():
            errors.append(f"{source}: file mancante per {label}: {path_value}")

    coverage = pack.get("coverage")
    if isinstance(coverage, dict):
        check_file(coverage.get("path"), "coverage")
    for item in pack.get("content_items", []):
        if isinstance(item, dict):
            check_file(item.get("path"), f"content item {item.get('id')}")
    for item in pack.get("course_designs", []):
        if isinstance(item, dict):
            check_file(item.get("path"), f"course design {item.get('id')}")
    for source_item in pack.get("sources", []):
        if not isinstance(source_item, dict) or source_item.get("provider") != "local":
            continue
        base = _text(source_item.get("path"))
        files = source_item.get("files", [])
        if not isinstance(files, list):
            continue
        for filename in files:
            if not isinstance(filename, str):
                continue
            relative = str(PurePosixPath(base) / filename) if base else filename
            check_file(relative, f"source {source_item.get('id')}")
    for index, value in enumerate(pack.get("activity_roots", [])):
        if not _safe_relative_path(value):
            continue
        path = (root / value).resolve(strict=False)
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"{source}: activity_roots[{index}] esce dalla root")
            continue
        if not path.is_dir():
            errors.append(f"{source}: activity root mancante: {value}")
    return errors


def project_course_design_sources(pack: dict[str, Any]) -> list[dict[str, Any]]:
    """Project v1 sources into the current CourseDesign.sources contract."""
    projected: list[dict[str, Any]] = []
    for source in pack.get("sources", []):
        if not isinstance(source, dict):
            continue
        item = {
            "id": source.get("id"),
            "label": source.get("label"),
            "type": source.get("type"),
            "provider": source.get("provider"),
            "files": deepcopy(source.get("files", [])),
            "indexing_status": source.get("indexing_status"),
        }
        provider = source.get("provider")
        if provider == "local":
            item["path"] = source.get("path", "")
        elif provider in {"github", "gitlab"}:
            item["repository"] = source.get("repository")
            item["ref"] = source.get("ref")
        if "updated_at" in source:
            item["updated_at"] = source.get("updated_at")
        projected.append(item)
    return projected


def _joined_source_file(source: dict[str, Any], filename: str) -> str:
    base = _text(source.get("path"))
    return str(PurePosixPath(base) / filename) if base else filename


def _infer_content_source_refs(
    item: dict[str, Any], sources: list[dict[str, Any]]
) -> list[dict[str, str]]:
    path = _text(item.get("path"))
    if not path:
        return []
    for source in sources:
        for filename in source.get("files", []):
            if (
                isinstance(filename, str)
                and _joined_source_file(source, filename) == path
            ):
                return [
                    {
                        "id": str(source.get("id")),
                        "role": "content-origin",
                        "locator": path,
                    }
                ]
    return []


def _infer_coverage(sources: list[dict[str, Any]]) -> dict[str, str] | None:
    for source in sources:
        for filename in source.get("files", []):
            if (
                isinstance(filename, str)
                and PurePosixPath(filename).name.lower() == "coverage.md"
            ):
                return {
                    "path": _joined_source_file(source, filename),
                    "status": "draft",
                }
    return None


def upgrade_v0_to_v1(pack: Any) -> dict[str, Any]:
    """Upgrade a v0 authoring manifest without fetching or inventing sources."""
    if not isinstance(pack, dict):
        raise ValueError("content pack v0 deve essere un oggetto")
    if pack.get("schema_version") != SCHEMA_V0:
        raise ValueError(f"schema_version deve essere {SCHEMA_V0}")

    result = deepcopy(pack)
    result["schema_version"] = SCHEMA_V1

    references: list[dict[str, Any]] = []
    for raw in result.pop("curriculum_references", []):
        if not isinstance(raw, dict):
            continue
        reference = deepcopy(raw)
        reference.setdefault("kind", "reference")
        reference.setdefault("role", "coverage-reference")
        reference.setdefault("provider", "unknown")
        reference.setdefault("title", reference.get("id", "reference"))
        reference.setdefault("license_status", "review-required")
        references.append(reference)
    result["references"] = references

    sources: list[dict[str, Any]] = []
    for raw in result.get("sources", []):
        if not isinstance(raw, dict):
            continue
        source = deepcopy(raw)
        source.setdefault("kind", "source-package")
        source.setdefault("label", source.get("id", "source"))
        source.setdefault("role", "approved-course-content")
        source.setdefault("license_status", "review-required")
        source.setdefault("indexing_status", "ready")
        source.setdefault("path", "")
        sources.append(source)
    result["sources"] = sources

    for item in result.get("content_items", []):
        if not isinstance(item, dict):
            continue
        item.setdefault("source_refs", _infer_content_source_refs(item, sources))

    if "coverage" not in result:
        coverage = _infer_coverage(sources)
        if coverage is not None:
            result["coverage"] = coverage

    policies = (
        deepcopy(result.get("policies", {}))
        if isinstance(result.get("policies"), dict)
        else {}
    )
    if "restricted_source_copying_forbidden" not in policies:
        policies["restricted_source_copying_forbidden"] = bool(
            policies.get("book_text_reproduction_forbidden", True)
        )
    result["policies"] = policies

    compatibility = result.pop("compatibility", None)
    if compatibility is not None:
        extensions = (
            deepcopy(result.get("extensions", {}))
            if isinstance(result.get("extensions"), dict)
            else {}
        )
        extensions["v0_compatibility"] = compatibility
        result["extensions"] = extensions
    return result


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: atteso oggetto JSON")
    return payload


def _cmd_validate(args: argparse.Namespace) -> int:
    pack = load_json(args.path)
    errors = validate_content_pack(pack, str(args.path), root=args.root)
    if errors:
        print("Content Pack validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Content Pack validation passed.")
    return 0


def _cmd_upgrade(args: argparse.Namespace) -> int:
    source = load_json(args.input)
    upgraded = upgrade_v0_to_v1(source)
    errors = validate_content_pack(upgraded, str(args.input))
    if errors:
        print("Content Pack v0 -> v1 upgrade produced invalid output:")
        for error in errors:
            print(f"- {error}")
        return 1
    args.output.write_text(
        json.dumps(upgraded, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Content Pack v1 scritto in {args.output}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida e migra TheBitLab Content Pack."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("path", type=Path)
    validate.add_argument("--root", type=Path)
    validate.set_defaults(handler=_cmd_validate)

    upgrade = sub.add_parser("upgrade-v0")
    upgrade.add_argument("input", type=Path)
    upgrade.add_argument("output", type=Path)
    upgrade.set_defaults(handler=_cmd_upgrade)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
