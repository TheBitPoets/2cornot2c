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

    assert validate_bundle(minimal, index=index) == []
    assert generate_index(minimal) == index
    assert validate_bundle(partial_import) == []


def test_valid_bundle_reference_fixture_conforms() -> None:
    reference = load_json(VALID / "bundle-reference.json")
    assert validate_bundle_reference(reference) == []


def test_nfc_unicode_paths_conform() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    bundle["content"]["units"][0]["materials"][0] = "materials/caffè.md"

    assert validate_bundle(bundle) == []


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


def test_semver_numeric_prerelease_identifiers_reject_leading_zeroes() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    reference = load_json(VALID / "bundle-reference.json")
    bundle["version"] = "1.0.0-01"
    reference["version"] = "1.0.0-01"

    assert validate_bundle(bundle)
    assert validate_bundle_reference(reference)


def test_source_url_must_be_a_valid_uri() -> None:
    bundle = load_json(VALID / "partial-import-bundle.json")
    reference = load_json(VALID / "bundle-reference.json")
    bundle["imports"][0]["source_url"] = "https://git hub.example/org/repo"
    reference["source_url"] = "https://git hub.example/org/repo"

    assert validate_bundle(bundle)
    assert validate_bundle_reference(reference)


def test_stale_index_is_rejected() -> None:
    bundle = load_json(VALID / "minimal-bundle.json")
    stale_index = load_json(INVALID / "stale-index.json")

    errors = validate_bundle(bundle, index=stale_index)

    assert "index.json is not the canonical index derived from bundle.json" in errors


def test_portable_key_normalizes_nfc_case_and_windows_suffixes() -> None:
    assert portable_path_key("Materials/Café.md") == portable_path_key(
        "materials/Cafe\u0301.md"
    )
    assert portable_path_key("materials/lesson. ") == portable_path_key(
        "materials/lesson"
    )
