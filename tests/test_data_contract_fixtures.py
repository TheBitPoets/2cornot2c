from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts import validate_activity


CONTRACT_FIXTURES = Path("tests/fixtures/contracts")


def load_fixture(name: str) -> dict[str, Any]:
    payload = json.loads((CONTRACT_FIXTURES / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def assert_required(payload: dict[str, Any], fields: set[str]) -> None:
    missing = fields - set(payload)
    assert not missing, f"Campi mancanti in fixture: {sorted(missing)}"


def test_course_design_contract_fixture() -> None:
    payload = load_fixture("course_design.json")

    assert_required(payload, {"schema_version", "id", "title", "source_ids", "years"})
    assert payload["years"][0]["udas"][0]["items"][0]["activity_ids"] == ["python-base-somma-001"]


def test_class_group_contract_fixture() -> None:
    payload = load_fixture("class_group.json")

    assert_required(payload, {"schema_version", "id", "label", "school_year", "provider", "provider_ref", "students"})
    student = payload["students"][0]
    assert_required(student, {"schema_version", "id", "display_name", "class_ids", "provider_accounts", "repo_refs"})
    assert student["id"] == "rossi-mario"
    assert student["class_ids"] == ["3a-tpsi-2026"]
    assert student["provider_accounts"]["github"] == "rossi-mario"


def test_activity_contract_fixture_keeps_canonical_and_legacy_fields() -> None:
    payload = load_fixture("activity.json")

    assert_required(
        payload,
        {
            "schema_version",
            "id",
            "title",
            "kind",
            "language",
            "difficulty",
            "topics",
            "instructions",
            "student_support_mode",
            "grading_policy",
            "test_cases",
            "source_refs",
        },
    )
    assert payload["title"] == payload["titolo"]
    assert payload["kind"] == payload["tipo"]
    assert payload["language"] == payload["linguaggio"]
    assert payload["difficulty"] == payload["difficolta"]
    assert payload["topics"] == payload["argomenti"]
    assert payload["instructions"] == payload["consegna"]
    assert payload["grading_policy"] == payload["correzione"]
    assert validate_activity.validate_activity(payload, "activity.json") == []


def test_assignment_register_contract_fixture() -> None:
    payload = load_fixture("assignment_register.json")

    assert_required(
        payload,
        {
            "schema_version",
            "id",
            "assignment_id",
            "activity_id",
            "class_id",
            "class_label",
            "assigned_at",
            "due_at",
            "students",
        },
    )
    student = payload["students"][0]
    assert_required(student, {"student", "student_id", "repo", "submitted", "status", "late", "submission", "grading", "ai_feedback"})
    assert student["submission"]["files"][0]["path"] == "assignments/python-base-somma-001/main.py"
    assert student["grading"]["failed_tests"] == []
    assert student["ai_feedback"]["status"] == "not_generated"


def test_assignment_contract_fixture() -> None:
    payload = load_fixture("assignment.json")

    assert_required(
        payload,
        {
            "schema_version",
            "id",
            "activity_id",
            "activity_path",
            "target_type",
            "assigned_at",
            "due_at",
            "targets",
        },
    )
    assert payload["target_type"] == "class"
    assert payload["targets"][0]["student_id"] == "rossi-mario"
    assert payload["targets"][0]["repo_ref"] == "TheBitPoets/rossi-mario"
