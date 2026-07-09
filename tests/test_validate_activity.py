from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_activity
from scripts.thebitlab_contracts import ALLOWED_ACTIVITY_KINDS


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


def test_allowed_types_come_from_activity_contracts() -> None:
    assert validate_activity.ALLOWED_TYPES is ALLOWED_ACTIVITY_KINDS


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


def test_required_text_fields_must_be_non_empty_strings() -> None:
    activity = valid_activity()
    activity["id"] = ""
    activity["titolo"] = 123

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: id deve essere una stringa non vuota" in errors
    assert "activity.json: titolo deve essere una stringa non vuota" in errors


def test_unsupported_schema_version_is_reported() -> None:
    activity = valid_activity()
    activity["schema_version"] = "2.0"

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: schema_version non supportata: 2.0" in errors


def test_correction_flags_must_be_boolean() -> None:
    activity = valid_activity()
    activity["correzione"]["sandbox"] = "si"

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: correzione.sandbox deve essere boolean" in errors


def test_metrics_base_fields_are_required() -> None:
    activity = valid_activity()
    activity["metriche"] = {}

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: metriche.tempo_stimato_minuti mancante" in errors
    assert "activity.json: metriche.traccia_eventi_didattici mancante" in errors


def test_metric_flags_must_be_boolean() -> None:
    activity = valid_activity()
    activity["metriche"]["traccia_sessioni_thebitlab"] = "si"

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: metriche.traccia_sessioni_thebitlab deve essere boolean" in errors


def test_rubric_points_must_not_be_boolean() -> None:
    activity = valid_activity()
    activity["rubrica"] = [{"criterio": "Compilazione", "punti": True}]

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert "activity.json: rubrica[0].punti deve essere un numero non negativo" in errors


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
