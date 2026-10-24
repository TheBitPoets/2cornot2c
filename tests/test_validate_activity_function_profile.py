from __future__ import annotations

from scripts import create_submission_scaffold, validate_activity


def base_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-function-test-001",
        "titolo": "Area rettangolo",
        "tipo": "laboratorio",
        "difficolta": "B",
        "argomenti": ["funzioni", "return"],
        "consegna": "Completa la funzione area(base, altezza).",
        "correzione": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 15,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
        "function_tests": [
            {
                "profile": "python-function-v1",
                "name": "rettangolo 3x4",
                "function": "area",
                "args": [3, 4],
                "expected_return": 12,
            }
        ],
    }


def test_activity_accepts_valid_function_profile_tests() -> None:
    assert validate_activity.validate_activity(base_activity(), "activity.json") == []


def test_activity_rejects_unknown_function_profile_version() -> None:
    activity = base_activity()
    activity["function_tests"][0]["profile"] = "python-function-v2"
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("profile deve essere python-function-v1" in error for error in errors)


def test_activity_rejects_unknown_function_test_fields() -> None:
    activity = base_activity()
    activity["function_tests"][0]["expected_magic"] = 12
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("campi non supportati" in error for error in errors)


def test_student_activity_payload_redacts_teacher_function_tests() -> None:
    public = create_submission_scaffold.student_activity_payload(base_activity())
    assert "function_tests" not in public
    serialized = str(public)
    assert "expected_return" not in serialized
    assert "rettangolo 3x4" not in serialized
