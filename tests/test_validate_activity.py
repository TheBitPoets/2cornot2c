from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_activity


EXAMPLES = Path("activities/examples")


def valid_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "c-base-test-001",
        "titolo": "Esercizio di test",
        "tipo": "compito-casa",
        "difficolta": "B",
        "argomenti": ["variabili"],
        "consegna": "Scrivi un programma C minimale.",
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
    }


def test_examples_are_valid() -> None:
    errors = validate_activity.validate_files([EXAMPLES])

    assert errors == []


def test_missing_required_field_is_reported() -> None:
    activity = valid_activity()
    del activity["consegna"]

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: campo obbligatorio mancante: consegna" in errors


def test_invalid_type_is_reported() -> None:
    activity = valid_activity()
    activity["tipo"] = "gara-di-cucina"

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: tipo non ammesso: gara-di-cucina" in errors


def test_correction_flags_must_be_boolean() -> None:
    activity = valid_activity()
    activity["correzione"]["sandbox"] = "si"

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: correzione.sandbox deve essere boolean" in errors


def test_cli_validation_fails_on_invalid_file(tmp_path, monkeypatch) -> None:
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text(json.dumps({"id": "troppo-poco"}), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["validate_activity.py", str(invalid_file)])

    assert validate_activity.main() == 1


def test_cli_validation_passes_on_valid_file(tmp_path, monkeypatch) -> None:
    valid_file = tmp_path / "valid.json"
    valid_file.write_text(json.dumps(valid_activity()), encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["validate_activity.py", str(valid_file)])

    assert validate_activity.main() == 0


def test_missing_path_is_reported(tmp_path) -> None:
    missing_path = tmp_path / "missing"

    errors = validate_activity.validate_files([missing_path])

    assert f"{missing_path}: path non trovato" in errors


def test_empty_directory_is_reported(tmp_path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    errors = validate_activity.validate_files([empty_dir])

    assert f"{empty_dir}: nessun file JSON trovato" in errors
