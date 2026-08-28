from __future__ import annotations

from scripts import create_submission_scaffold, validate_activity


def p4_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-p4-files-001",
        "titolo": "Somma misure da file",
        "tipo": "laboratorio",
        "difficolta": "B",
        "argomenti": ["file", "pathlib"],
        "consegna": "Leggi misure.txt e crea risultato.txt.",
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
        "filesystem_tests": [
            {
                "profile": "python-filesystem-v1",
                "name": "somma base",
                "fixtures": [
                    {
                        "id": "input",
                        "source": "fixtures/misure.txt",
                        "target": "misure.txt",
                        "mode": "read-only",
                    }
                ],
                "expected_artifacts": [
                    {
                        "path": "risultato.txt",
                        "text": "36\n",
                        "encoding": "utf-8",
                    }
                ],
            }
        ],
    }


def test_activity_validator_accepts_p4_contract() -> None:
    assert validate_activity.validate_activity(p4_activity(), "activity.json") == []


def test_activity_validator_rejects_p4_on_non_python_activity() -> None:
    activity = p4_activity()
    activity["language"] = "c"
    activity["linguaggio"] = "c"
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("filesystem_tests" in error and "Python" in error for error in errors)


def test_activity_validator_rejects_teacher_contract_errors() -> None:
    activity = p4_activity()
    activity["filesystem_tests"][0]["expected_artifacts"][0]["path"] = "../out.txt"
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("expected_artifacts" in error for error in errors)


def test_student_activity_payload_redacts_filesystem_tests_and_fixture_source() -> None:
    public = create_submission_scaffold.student_activity_payload(p4_activity())
    assert "filesystem_tests" not in public
    serialized = repr(public).casefold()
    assert "fixtures/misure.txt" not in serialized
    assert "risultato.txt" not in serialized
    assert "36" not in serialized
