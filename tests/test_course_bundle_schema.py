"""Conformance tests for course bundle schemas and semantic invariants."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.course_bundle_validation import (
    generate_index,
    load_json,
    portable_path_key,
    validate_bundle,
    validate_bundle_reference,
    validate_source_url,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "tests" / "fixtures" / "course_bundles"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"


def _apply_case(document: dict[str, Any], case: dict[str, Any]) -> None:
    target: Any = document
    for component in case["path"][:-1]:
        target = target[component]
    leaf = case["path"][-1]
    if case["operation"] == "set":
        target[leaf] = case["value"]
    elif case["operation"] == "append":
        target[leaf].append(case["value"])
    elif case["operation"] == "delete":
        del target[leaf]
    else:  # pragma: no cover - fixture authoring guard
        raise AssertionError(f"unknown fixture operation: {case['operation']}")


def _invalid_cases() -> list[dict[str, Any]]:
    return json.loads((INVALID / "manifest-cases.json").read_text(encoding="utf-8"))


def _adr_json_after_heading(text: str, heading: str) -> dict[str, Any]:
    start = text.index(heading)
    match = re.search(r"```json\s*\n(.*?)\n```", text[start:], re.DOTALL)
    assert match is not None, f"missing JSON example after {heading}"
    return json.loads(match.group(1))


def test_schemas_are_valid_draft_2020_12_documents() -> None:
    for name in ("course-bundle.schema.json", "bundle-reference.schema.json"):
        schema = load_json(SCHEMAS / name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        Draft202012Validator.check_schema(schema)


def test_valid_bundle_fixtures_conform() -> None:
    minimal = load_json(VALID / "minimal-bundle.json")
    index = load_json(VALID / "minimal-index.json")
    partial_import = load_json(VALID / "partial-import-bundle.json")
    full_import = load_json(VALID / "full-import-bundle.json")
    full_index = load_json(VALID / "full-import-index.json")
    imported_bundles = {minimal["id"]: minimal}

    assert validate_bundle(minimal, index=index) == []
    assert generate_index(minimal) == index
    assert validate_bundle(partial_import) == []
    assert (
        validate_bundle(
            full_import, index=full_index, imported_bundles=imported_bundles
        )
        == []
    )
    assert generate_index(full_import, imported_bundles=imported_bundles) == full_index


def test_valid_bundle_reference_fixture_conforms() -> None:
    reference = load_json(VALID / "bundle-reference.json")
    assert validate_bundle_reference(reference) == []


@pytest.mark.parametrize(
    "path",
    [
        "materials/name with space.md",
        "materials/~draft.md",
        "materials/caffè.md",
        "materials/百分比.md",
    ],
)
def test_paths_outside_safe_manifest_alphabet_are_rejected(path: str) -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    bundle["content"]["units"][0]["materials"][0] = path
    schema = load_json(SCHEMAS / "course-bundle.schema.json")

    assert not Draft202012Validator(schema).is_valid(bundle)
    assert validate_bundle(bundle)


@pytest.mark.parametrize(
    ("base", "path"),
    [
        ("minimal-bundle.json", ["id"]),
        ("minimal-bundle.json", ["version"]),
        ("minimal-bundle.json", ["school_year"]),
        ("minimal-bundle.json", ["language"]),
        ("minimal-bundle.json", ["platform_min_version"]),
        ("minimal-bundle.json", ["content", "units", 0, "id"]),
        ("partial-import-bundle.json", ["imports", 0, "bundle_id"]),
        ("partial-import-bundle.json", ["imports", 0, "source_url"]),
        ("partial-import-bundle.json", ["imports", 0, "tag"]),
        ("partial-import-bundle.json", ["imports", 0, "commit_sha"]),
    ],
)
def test_constrained_manifest_strings_reject_terminal_newlines(
    base: str, path: list[Any]
) -> None:
    bundle = load_json(VALID / base)
    target: Any = bundle
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] += "\n"

    assert validate_bundle(bundle)


@pytest.mark.parametrize(
    "field",
    ["bundle_id", "version", "source_url", "tag", "expected_commit_sha"],
)
def test_constrained_bundle_reference_strings_reject_terminal_newlines(
    field: str,
) -> None:
    reference = load_json(VALID / "bundle-reference.json")
    reference[field] += "\n"

    assert validate_bundle_reference(reference)


def test_source_url_semantics_reject_terminal_newline() -> None:
    assert validate_source_url("https://github.com/TheBitPoets/course\n")


def test_invalid_bundle_reference_fixture_is_rejected() -> None:
    reference = load_json(INVALID / "bundle-reference-short-sha.json")
    errors = validate_bundle_reference(reference)
    assert errors
    assert "does not match" in "\n".join(errors)


def test_adr_examples_conform_to_the_formal_contracts() -> None:
    adr = (ROOT / "doc" / "architecture" / "adr-course-bundle-format.md").read_text(
        encoding="utf-8"
    )
    bundle = _adr_json_after_heading(adr, "### `bundle.json` (esempio)")
    reference = _adr_json_after_heading(adr, "### Riferimento esterno al bundle")
    index = _adr_json_after_heading(adr, "### `index.json`")

    assert validate_bundle(bundle, index=index) == []
    assert validate_bundle_reference(reference) == []


@pytest.mark.parametrize("case", _invalid_cases(), ids=lambda case: case["name"])
def test_invalid_manifest_fixtures_fail_closed(case: dict[str, Any]) -> None:
    bundle = deepcopy(load_json(VALID / case["base"]))
    _apply_case(bundle, case)

    errors = validate_bundle(bundle)

    assert errors
    assert case["expected"] in "\n".join(errors)


def test_import_cycles_are_rejected() -> None:
    bundle_a = load_json(INVALID / "cycle-a.json")
    bundle_b = load_json(INVALID / "cycle-b.json")

    errors = validate_bundle(bundle_a, imported_bundles={"bundle-b": bundle_b})

    assert errors == ["import cycle: bundle-a -> bundle-b -> bundle-a"]


def test_import_metadata_must_match_source_manifest() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    source = load_json(VALID / "minimal-bundle.json")

    errors = validate_bundle(bundle, imported_bundles={"fondamenti-c": source})

    assert errors == [
        "import fondamenti-c does not match source bundle id: 'tpsi-quarto-2026'",
        "import fondamenti-c version '1.2.0' does not match source bundle version: '1.0.0'",
    ]


def test_partial_import_items_must_match_supplied_source_manifest() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    source = load_json(VALID / "minimal-bundle.json")
    source["id"] = "fondamenti-c"
    source["version"] = "1.2.0"
    imported_bundles = {source["id"]: source}

    missing_errors = validate_bundle(bundle, imported_bundles=imported_bundles)
    assert any("references a missing source item" in error for error in missing_errors)

    first_item = bundle["imports"][0]["items"][0]
    first_item["path"] = source["content"]["units"][0]["materials"][0]
    type_errors = validate_bundle(bundle, imported_bundles=imported_bundles)
    assert any(
        "is declared as activity, but source manifest has type material" in error
        for error in type_errors
    )


def test_semver_numeric_prerelease_identifiers_reject_leading_zeroes() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    reference = load_json(VALID / "bundle-reference.json")
    bundle["version"] = "1.0.0-01"
    reference["version"] = "1.0.0-01"

    assert validate_bundle(bundle)
    assert validate_bundle_reference(reference)


@pytest.mark.parametrize(
    "source_url",
    [
        "https://git hub.example/org/repo",
        "https://localhost/org/repo",
        "https://a..b/org/repo",
        "https://127.0.0.1/org/repo",
        "https://8.8.8.8/org/repo",
        "https://10.0.0.1/org/repo",
        "https://169.254.169.254/org/repo",
        "https://127.1/org/repo",
        "https://010.0.0.1/org/repo",
        "https://0x7f.0.0.1/org/repo",
        "https://0x7f.1/org/repo",
        "https://127.0.0x1/org/repo",
        "https://[v1.localhost]/org/repo",
        "https://example.com:99999/org/repo",
        "https://example.com:8443/org/repo",
        "https://github.com:/foo/repo",
        "https://github.com:0443/foo/repo",
        "https://github.com:+443/foo/repo",
        "https://github.com/foo/..",
        "https://github.com/../repo",
        "https://github.com/./repo",
        "https://github.com/foo/repo?",
        "https://github.com/foo/repo#",
    ],
)
def test_source_url_baseline_rejects_unsafe_targets(source_url: str) -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    reference = load_json(VALID / "bundle-reference.json")
    bundle["imports"][0]["source_url"] = source_url
    reference["source_url"] = source_url
    bundle_schema = load_json(SCHEMAS / "course-bundle.schema.json")
    reference_schema = load_json(SCHEMAS / "bundle-reference.schema.json")

    assert not Draft202012Validator(bundle_schema).is_valid(bundle)
    assert not Draft202012Validator(reference_schema).is_valid(reference)
    assert validate_source_url(source_url)
    assert validate_bundle(bundle)
    assert validate_bundle_reference(reference)


def test_source_url_explicit_https_port_conforms() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    reference = load_json(VALID / "bundle-reference.json")
    bundle["imports"][0]["source_url"] = (
        "https://github.com:443/TheBitPoets/fondamenti-c"
    )
    reference["source_url"] = (
        "https://github.com:443/TheBitPoets/tpsi-quarto-docente"
    )

    assert validate_bundle(bundle) == []
    assert validate_bundle_reference(reference) == []


def test_stale_index_is_rejected() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    stale_index = load_json(INVALID / "stale-index.json")

    errors = validate_bundle(bundle, index=stale_index)

    assert "index.json is not the canonical index derived from bundle.json" in errors


def test_boolean_order_is_not_equal_to_canonical_integer_order() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    index = load_json(VALID / "minimal-index.json")
    index["units"][0]["order"] = True

    errors = validate_bundle(bundle, index=index)

    assert "index.json is not the canonical index derived from bundle.json" in errors


def test_recursive_full_imports_are_composed_before_local_units() -> None:
    leaf = load_json(VALID / "minimal-bundle.json")
    middle = load_json(VALID / "full-import-bundle.json")
    middle["id"] = "middle-course"
    root = load_json(VALID / "full-import-bundle.json")
    root["imports"][0].update(
        {
            "bundle_id": "middle-course",
            "source_url": "https://github.com/TheBitPoets/middle-course",
        }
    )
    imported_bundles = {leaf["id"]: leaf, middle["id"]: middle}

    index = generate_index(root, imported_bundles=imported_bundles)

    assert [unit["id"] for unit in index["units"]] == [
        "middle-course-tpsi-quarto-2026-u01-intro-c",
        "middle-course-tpsi-quarto-2026-u02-funzioni",
        "middle-course-u-local",
        "u-local",
    ]
    assert index["units"][0]["items"][0]["path"].startswith(
        ".imports/middle-course/.imports/tpsi-quarto-2026/"
    )
    assert validate_bundle(root, index=index, imported_bundles=imported_bundles) == []


def test_full_import_requires_source_for_validation_and_index_generation() -> None:
    root = load_json(VALID / "full-import-bundle.json")
    truncated_index = {
        "units": [
            {
                "id": "u-local",
                "title": "Unità locale",
                "order": 1,
                "items": [{"type": "material", "path": "materials/local.md"}],
            }
        ]
    }

    errors = validate_bundle(root, index=truncated_index)

    assert any(
        "full import source manifest is unavailable" in error for error in errors
    )
    with pytest.raises(ValueError, match="full import source manifest is unavailable"):
        generate_index(root)


def test_generate_index_rejects_composed_unit_id_collisions() -> None:
    root = load_json(VALID / "full-import-bundle.json")
    source = load_json(VALID / "minimal-bundle.json")
    root["content"]["units"][0]["id"] = "tpsi-quarto-2026-u01-intro-c"

    errors = validate_bundle(root, imported_bundles={source["id"]: source})

    assert "composed content.units ids must be globally unique" in errors
    with pytest.raises(
        ValueError, match="composed content.units ids must be globally unique"
    ):
        generate_index(root, imported_bundles={source["id"]: source})


def test_full_import_rejects_unsafe_source_paths_before_index_generation() -> None:
    source = load_json(VALID / "minimal-bundle.json")
    source["content"]["units"][0]["materials"][0] = "../escape.md"
    root = load_json(VALID / "full-import-bundle.json")
    imported_bundles = {source["id"]: source}

    errors = validate_bundle(root, imported_bundles=imported_bundles)

    assert any(
        "import closure composite-course -> tpsi-quarto-2026" in error
        and "'..' component" in error
        for error in errors
    )
    with pytest.raises(ValueError, match="cannot generate index"):
        generate_index(root, imported_bundles=imported_bundles)


def test_nested_full_import_manifest_is_validated_before_composition() -> None:
    leaf = load_json(VALID / "minimal-bundle.json")
    del leaf["content"]
    middle = load_json(VALID / "full-import-bundle.json")
    middle["id"] = "middle-course"
    root = load_json(VALID / "full-import-bundle.json")
    root["imports"][0].update(
        {
            "bundle_id": "middle-course",
            "source_url": "https://github.com/TheBitPoets/middle-course",
        }
    )

    errors = validate_bundle(
        root,
        imported_bundles={"middle-course": middle, "tpsi-quarto-2026": leaf},
    )

    assert any(
        "import closure composite-course -> middle-course -> tpsi-quarto-2026"
        in error
        and "content" in error
        for error in errors
    )


def test_full_import_materialization_collisions_are_rejected() -> None:
    bundle = load_json(INVALID / "full-import-collision-bundle.json")
    source = load_json(VALID / "minimal-bundle.json")

    errors = validate_bundle(bundle, imported_bundles={source["id"]: source})

    assert any("portable path collision" in error for error in errors)
    assert any("reserved .imports namespace" in error for error in errors)

    del bundle["imports"][1]
    local_errors = validate_bundle(bundle, imported_bundles={source["id"]: source})
    assert any("portable path collision" in error for error in local_errors)
    assert any("reserved .imports namespace" in error for error in local_errors)


def test_local_file_directory_path_overlap_is_a_collision() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    bundle["content"]["units"][0]["materials"].append(
        "Materials/01-INTRO.md/child.txt"
    )

    errors = validate_bundle(bundle)

    assert any("portable path collision" in error for error in errors)


def test_import_target_file_directory_path_overlap_is_a_collision() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    bundle["content"]["units"][0]["materials"].append(
        "activities/funzioni-base/activity.json/child.txt"
    )

    errors = validate_bundle(bundle)

    assert any("portable path collision" in error for error in errors)


def test_case_only_alias_of_import_target_is_a_collision() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    bundle["imports"][0]["items"][0]["target_path"] = (
        "activities/FUNZIONI-base/activity.json"
    )

    errors = validate_bundle(bundle)

    assert any("portable path collision" in error for error in errors)


def test_case_only_alias_of_local_override_is_not_an_explicit_reference() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    bundle["local_extensions"][0]["override_path"] = (
        "materials/FUNZIONI-personalizzate.md"
    )

    errors = validate_bundle(bundle)

    assert any("portable path collision" in error for error in errors)
    assert any("override is not referenced by content.units" in error for error in errors)


def test_import_target_must_keep_its_declared_item_type() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    unit = bundle["content"]["units"][0]
    target_path = unit["activities"].pop()
    unit["materials"].append(target_path)

    errors = validate_bundle(bundle)

    assert any(
        "import target 'activities/funzioni-base/activity.json' declared as "
        "activity is referenced by content.units as material" in error
        for error in errors
    )


def test_local_content_path_cannot_have_conflicting_types() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    unit = bundle["content"]["units"][0]
    unit["materials"].append(unit["activities"][0])

    errors = validate_bundle(bundle)

    assert any(
        "is referenced with conflicting types: activity, material" in error
        for error in errors
    )


def test_local_extension_must_keep_its_source_item_type() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    unit = bundle["content"]["units"][0]
    override_path = unit["materials"].pop()
    unit["activities"].append(override_path)

    errors = validate_bundle(bundle)

    assert any(
        "local extension override 'materials/funzioni-personalizzate.md' is "
        "referenced as activity" in error
        and "has type material" in error
        for error in errors
    )


def test_portable_key_normalizes_nfc_case_and_windows_suffixes() -> None:
    assert portable_path_key("Materials/Café.md") == portable_path_key(
        "materials/Cafe\u0301.md"
    )
    assert portable_path_key("materials/lesson. ") == portable_path_key(
        "materials/lesson"
    )
