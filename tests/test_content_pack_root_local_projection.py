from __future__ import annotations

import json
from pathlib import Path

from scripts import course_source_catalog
from scripts.content_pack_contract import (
    project_course_design_sources,
    validate_content_pack,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "content_pack_v1.json"


def load_fixture() -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_local_source_at_repository_root_omits_empty_path_in_projection() -> None:
    pack = load_fixture()
    pack["sources"] = [
        {
            "id": "tpsi5-source-root",
            "kind": "source-package",
            "label": "Root Markdown source",
            "type": "markdown",
            "provider": "local",
            "role": "technical-reference",
            "path": "",
            "files": ["README.md"],
            "license_status": "review-required",
            "indexing_status": "ready",
        }
    ]
    # Keep required provenance valid without claiming that the fixture content
    # originated from the root source used only to exercise the projection edge case.
    pack["content_items"][0]["source_refs"] = [
        {
            "id": "tpsi5-ref-mdn-html",
            "role": "technical-reference",
            "locator": "HTML reference",
        }
    ]

    assert validate_content_pack(pack) == []

    projected = project_course_design_sources(pack)
    assert len(projected) == 1
    assert projected[0]["provider"] == "local"
    assert projected[0]["files"] == ["README.md"]
    assert "path" not in projected[0]

    normalized = course_source_catalog.normalize_course_sources(
        {"sources": projected}
    )
    assert len(normalized) == 1
    assert normalized[0].provider == "local"
    assert normalized[0].path == ""
    assert normalized[0].files == ("README.md",)
