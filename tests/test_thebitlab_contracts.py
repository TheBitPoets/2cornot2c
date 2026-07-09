from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts import thebitlab_contracts


FIXTURES = Path("tests/fixtures/contracts")


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_normalize_activity_preserves_contract_fixture() -> None:
    payload = load_fixture("activity.json")

    normalized = thebitlab_contracts.normalize_activity(payload)

    assert normalized["id"] == "python-base-somma-001"
    assert normalized["title"] == "Somma in Python"
    assert normalized["kind"] == "compito-casa"
    assert normalized["language"] == "python"
    assert normalized["difficulty"] == "B"
    assert normalized["topics"] == ["variabili", "input-output"]
    assert normalized["instructions"] == "Scrivi un programma che legge due numeri e stampa la somma."
    assert normalized["grading_policy"] == payload["correzione"]
    assert normalized["class_id"] == "3A-TPSI"
    assert normalized["github_team"] == "team-3a-tpsi"


def test_normalize_activity_reads_legacy_aliases() -> None:
    payload = {
        "id": "c-base-contatore-001",
        "titolo": "Contatore in C",
        "tipo": "laboratorio",
        "linguaggio": "c",
        "difficolta": "C",
        "argomenti": ["cicli"],
        "consegna": "Scrivi un contatore.",
        "support_mode": "feedback-tecnico",
        "correzione": {"compila": True},
        "contesto": {"classe": "4A-INF", "team_github": "team-4a-inf"},
    }

    normalized = thebitlab_contracts.normalize_activity(payload)

    assert normalized["schema_version"] == "1.0"
    assert normalized["title"] == "Contatore in C"
    assert normalized["kind"] == "laboratorio"
    assert normalized["language"] == "c"
    assert normalized["difficulty"] == "C"
    assert normalized["topics"] == ["cicli"]
    assert normalized["instructions"] == "Scrivi un contatore."
    assert normalized["student_support_mode"] == "feedback-tecnico"
    assert normalized["grading_policy"] == {"compila": True}
    assert normalized["class_id"] == "4A-INF"
    assert normalized["github_team"] == "team-4a-inf"


def test_normalize_assignment_register_preserves_contract_fixture() -> None:
    payload = load_fixture("assignment_register.json")

    normalized = thebitlab_contracts.normalize_assignment_register(payload)

    assert normalized["id"] == "register-3a-tpsi-python-base-somma-001"
    assert normalized["assignment_id"] == "assignment-3a-tpsi-python-base-somma-001"
    assert normalized["activity_id"] == "python-base-somma-001"
    assert normalized["class_id"] == "3a-tpsi-2026"
    assert normalized["students"][0]["student_id"] == "rossi-mario"
    assert normalized["students"][0]["submission"]["files"][0]["role"] == "solution"
    assert normalized["students"][0]["grading"]["passed"] is True
    assert normalized["students"][0]["ai_feedback"]["status"] == "not_generated"


def test_normalize_assignment_register_adds_nested_defaults() -> None:
    payload = {
        "activity_id": "activity",
        "kind": "compito-casa",
        "class_id": "3A-TPSI",
        "students": [
            {
                "student": "rossi-mario",
                "repo": "TheBitPoets/rossi-mario",
                "submitted": True,
                "submission": {"commit": "abc1234"},
                "grading": {"status": "graded_passed"},
            }
        ],
    }

    normalized = thebitlab_contracts.normalize_assignment_register(payload)
    student = normalized["students"][0]

    assert normalized["schema_version"] == "1.0"
    assert normalized["class_label"] == "3A-TPSI"
    assert student["student_id"] == "rossi-mario"
    assert student["submission"]["commit"] == "abc1234"
    assert student["submission"]["files"] == []
    assert student["grading"]["failed_tests"] == []
    assert student["grading"]["teacher_grade"] is None
    assert student["ai_feedback"]["status"] == "not_generated"


def test_normalize_register_student_parses_boolean_strings_conservatively() -> None:
    student = thebitlab_contracts.normalize_register_student(
        {
            "student": "rossi-mario",
            "submitted": "false",
            "late": "0",
        }
    )
    other_student = thebitlab_contracts.normalize_register_student(
        {
            "student": "bianchi-luca",
            "submitted": "yes",
            "late": "si",
        }
    )

    assert student["submitted"] is False
    assert student["late"] is False
    assert other_student["submitted"] is True
    assert other_student["late"] is True
