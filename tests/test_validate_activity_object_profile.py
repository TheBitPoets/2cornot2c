from __future__ import annotations

from scripts import create_submission_scaffold, validate_activity


def p3_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-p3-object-001",
        "titolo": "Conto con stato",
        "tipo": "laboratorio",
        "difficolta": "B",
        "argomenti": ["classi", "oggetti", "stato"],
        "consegna": "Implementa la classe Conto con saldo e metodo deposita.",
        "language": "python",
        "linguaggio": "python",
        "correzione": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 20,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
        "object_tests": [
            {
                "profile": "python-object-v1",
                "name": "saldo dopo deposito",
                "class": "Conto",
                "construct": {"args": ["Anna", 100]},
                "steps": [
                    {
                        "call": "deposita",
                        "args": [20],
                        "expected_return": None,
                    },
                    {"observe": "saldo", "expected": 120},
                ],
            }
        ],
    }


def test_activity_validator_accepts_p3_object_contract() -> None:
    assert validate_activity.validate_activity(p3_activity(), "activity.json") == []


def test_activity_validator_rejects_p3_on_non_python_activity() -> None:
    activity = p3_activity()
    activity["language"] = "c"
    activity["linguaggio"] = "c"
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("object_tests" in error and "Python" in error for error in errors)


def test_activity_validator_rejects_multiple_python_profiles() -> None:
    activity = p3_activity()
    activity["function_tests"] = [
        {
            "profile": "python-function-v1",
            "function": "f",
            "expected_return": 1,
        }
    ]
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("profili Python incompatibili" in error for error in errors)


def test_student_activity_payload_redacts_object_scenarios() -> None:
    public = create_submission_scaffold.student_activity_payload(p3_activity())
    assert "object_tests" not in public
    serialized = repr(public).casefold()
    for forbidden in (
        "saldo dopo deposito",
        "expected_return",
        "expected_exception",
        "expected_constructor_exception",
        "'expected': 120",
    ):
        assert forbidden not in serialized
