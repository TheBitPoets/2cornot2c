from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from scripts import course_source_catalog
from scripts.content_pack_contract import (
    SCHEMA_V1,
    project_course_design_sources,
    upgrade_v0_to_v1,
    validate_content_pack,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
V1_FIXTURE = FIXTURES / "content_pack_v1.json"
V0_FIXTURE = FIXTURES / "content_pack_v0.json"


def load(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_canonical_v1_fixture_is_valid() -> None:
    pack = load(V1_FIXTURE)

    assert validate_content_pack(pack, str(V1_FIXTURE)) == []


def test_sources_project_to_current_course_source_catalog() -> None:
    pack = load(V1_FIXTURE)
    projected = project_course_design_sources(pack)

    normalized = course_source_catalog.normalize_course_sources(
        {"sources": projected}
    )

    assert len(normalized) == 1
    assert normalized[0].source_id == "tpsi5-source-originali"
    assert normalized[0].provider == "local"
    assert normalized[0].files == (
        "README.md",
        "COVERAGE.md",
        "01_WEB_FOUNDATIONS.md",
    )


def test_coverage_is_required_when_pack_has_coverage_reference() -> None:
    pack = load(V1_FIXTURE)
    pack.pop("coverage")

    errors = validate_content_pack(pack)

    assert any("coverage richiesto" in error for error in errors)


def test_provenance_must_reference_known_source_or_reference() -> None:
    pack = load(V1_FIXTURE)
    pack["content_items"][0]["source_refs"][0]["id"] = "unknown-source"

    errors = validate_content_pack(pack)

    assert any("source_refs[0].id sconosciuto" in error for error in errors)


def test_source_and_reference_ids_share_one_namespace() -> None:
    pack = load(V1_FIXTURE)
    pack["references"][0]["id"] = "tpsi5-source-originali"

    errors = validate_content_pack(pack)

    assert any("ID condivisi fra sources e references" in error for error in errors)


def test_paths_cannot_escape_pack_root() -> None:
    pack = load(V1_FIXTURE)
    pack["content_items"][0]["path"] = "../secret.md"
    pack["activity_roots"] = ["activities/tpsi5", "../other"]

    errors = validate_content_pack(pack)

    assert any("content_items[0].path" in error for error in errors)
    assert any("activity_roots[1]" in error for error in errors)


def test_indexable_source_requires_at_least_one_file() -> None:
    pack = load(V1_FIXTURE)
    pack["sources"][0]["files"] = []

    errors = validate_content_pack(pack)

    assert any("sources[0].files" in error for error in errors)


def test_approved_pack_requires_approved_content_design_and_coverage() -> None:
    pack = load(V1_FIXTURE)
    pack["status"] = "approved"

    errors = validate_content_pack(pack)

    assert any("content item non approved" in error for error in errors)
    assert any("course design non approved" in error for error in errors)
    assert any("coverage approved" in error for error in errors)

    pack["content_items"][0]["status"] = "approved"
    pack["course_designs"][0]["status"] = "approved"
    pack["coverage"]["status"] = "approved"
    assert validate_content_pack(pack) == []


def test_v0_upgrade_is_deterministic_and_valid() -> None:
    old = load(V0_FIXTURE)

    upgraded = upgrade_v0_to_v1(old)

    assert upgraded["schema_version"] == SCHEMA_V1
    assert upgraded["references"][0]["id"] == "tpsi4-curriculum-example"
    assert upgraded["sources"][0]["label"] == "tpsi4-source-originali"
    assert upgraded["coverage"] == {
        "path": "content/tpsi_quarto/COVERAGE.md",
        "status": "draft",
    }
    assert upgraded["content_items"][0]["source_refs"] == [
        {
            "id": "tpsi4-source-originali",
            "role": "content-origin",
            "locator": "content/tpsi_quarto/01_PROCESSI.md",
        }
    ]
    assert upgraded["policies"]["restricted_source_copying_forbidden"] is True
    assert upgraded["extensions"]["v0_compatibility"] == old["compatibility"]
    assert "compatibility" not in upgraded
    assert validate_content_pack(upgraded) == []


def test_v0_upgrade_does_not_invent_missing_provenance() -> None:
    old = load(V0_FIXTURE)
    old["content_items"][0]["path"] = "content/tpsi_quarto/NOT_DECLARED.md"

    upgraded = upgrade_v0_to_v1(old)
    errors = validate_content_pack(upgraded)

    assert upgraded["content_items"][0]["source_refs"] == []
    assert any("source_refs deve essere una lista non vuota" in error for error in errors)


def test_root_validation_checks_declared_files_and_activity_roots(
    tmp_path: Path,
) -> None:
    pack = load(V1_FIXTURE)

    content = tmp_path / "content" / "tpsi5"
    content.mkdir(parents=True)
    for filename in ("README.md", "COVERAGE.md", "01_WEB_FOUNDATIONS.md"):
        (content / filename).write_text(f"# {filename}\n", encoding="utf-8")

    design = tmp_path / "doc" / "course_designs"
    design.mkdir(parents=True)
    (design / "tpsi_quinto_2026_2027.json").write_text("{}\n", encoding="utf-8")

    (tmp_path / "activities" / "tpsi5").mkdir(parents=True)

    assert validate_content_pack(pack, root=tmp_path) == []

    (content / "01_WEB_FOUNDATIONS.md").unlink()
    errors = validate_content_pack(pack, root=tmp_path)
    assert any("01_WEB_FOUNDATIONS.md" in error for error in errors)


def test_references_can_model_public_and_licensed_material_without_ingestion() -> None:
    pack = load(V1_FIXTURE)
    providers = {item["provider"]: item for item in pack["references"]}

    assert providers["mdn"]["role"] == "technical-reference"
    assert providers["mdn"]["access"] == "public"
    assert providers["manning"]["role"] == "teacher-reference"
    assert providers["manning"]["access"] == "licensed"
    assert all(source["provider"] != "manning" for source in pack["sources"])
