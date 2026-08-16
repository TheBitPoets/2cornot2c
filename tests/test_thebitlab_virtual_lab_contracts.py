from __future__ import annotations

from scripts import thebitlab_virtual_lab_contracts as virtual_lab
from scripts import validate_activity


def valid_virtual_lab_activity() -> dict:
    return {
        "extensions": {
            virtual_lab.VIRTUAL_LAB_EXTENSION_KEY: {
                "schema_version": virtual_lab.VIRTUAL_LAB_SCHEMA_VERSION,
                "runtime": "efesto",
                "scenario_id": "pcie-lane-sharing-001",
                "submission": {
                    "path": "build.json",
                    "media_type": "application/json",
                },
                "capabilities": ["interactive-ui", "event-log", "deterministic-grade"],
            }
        }
    }


def valid_thebitlab_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "hw-pcie-lane-sharing-001",
        "titolo": "Lane sharing PCIe",
        "tipo": "laboratorio",
        "difficolta": "B",
        "argomenti": ["pcie", "lane", "nvme"],
        "consegna": "Configura la macchina senza disabilitare la scheda di rete.",
        "correzione": {
            "compila": False,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 30,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": False,
        },
        **valid_virtual_lab_activity(),
    }


def test_virtual_lab_extension_is_optional() -> None:
    assert virtual_lab.validate_virtual_lab_extension({}) == []
    assert virtual_lab.normalize_virtual_lab_extension({}) is None


def test_virtual_lab_extension_normalizes_runtime_contract() -> None:
    activity = valid_virtual_lab_activity()

    normalized = virtual_lab.normalize_virtual_lab_extension(activity)

    assert normalized == {
        "schema_version": "virtual_lab.v1",
        "runtime": "efesto",
        "scenario_id": "pcie-lane-sharing-001",
        "submission": {
            "path": "build.json",
            "media_type": "application/json",
        },
        "capabilities": ["interactive-ui", "event-log", "deterministic-grade"],
    }
    assert virtual_lab.validate_virtual_lab_extension(activity, "activity.json") == []


def test_virtual_lab_extension_does_not_reject_other_namespaced_extensions() -> None:
    activity = {
        "extensions": {
            "example.other_extension": {
                "schema_version": "other.v1",
            }
        }
    }

    assert virtual_lab.validate_virtual_lab_extension(activity, "activity.json") == []


def test_virtual_lab_extension_requires_stable_runtime_scenario_and_submission() -> None:
    activity = {
        "extensions": {
            virtual_lab.VIRTUAL_LAB_EXTENSION_KEY: {
                "schema_version": "future.v2",
                "runtime": "Efesto con spazi",
                "scenario_id": "scenario con spazi",
                "submission": {
                    "path": "../teacher/solution.json",
                    "media_type": "application/yaml",
                },
            }
        }
    }

    errors = virtual_lab.validate_virtual_lab_extension(activity, "activity.json")

    assert (
        "activity.json: extensions.thebitlab.virtual_lab.schema_version non supportata: future.v2"
        in errors
    )
    assert "activity.json: extensions.thebitlab.virtual_lab.runtime deve essere un identificativo portabile" in errors
    assert (
        "activity.json: extensions.thebitlab.virtual_lab.scenario_id deve essere un identificativo non vuoto senza spazi"
        in errors
    )
    assert (
        "activity.json: extensions.thebitlab.virtual_lab.submission.path deve essere un path relativo sicuro"
        in errors
    )
    assert any("submission.media_type non supportato: application/yaml" in error for error in errors)


def test_virtual_lab_extension_rejects_duplicate_or_invalid_capabilities() -> None:
    activity = valid_virtual_lab_activity()
    extension = activity["extensions"][virtual_lab.VIRTUAL_LAB_EXTENSION_KEY]
    extension["capabilities"] = ["event-log", "event-log", "non valida"]

    errors = virtual_lab.validate_virtual_lab_extension(activity, "activity.json")

    assert "activity.json: extensions.thebitlab.virtual_lab.capabilities[2] deve essere un identificativo portabile" in errors
    assert "activity.json: extensions.thebitlab.virtual_lab.capabilities non deve contenere duplicati" in errors


def test_virtual_lab_extension_defaults_json_media_type() -> None:
    activity = valid_virtual_lab_activity()
    del activity["extensions"][virtual_lab.VIRTUAL_LAB_EXTENSION_KEY]["submission"]["media_type"]

    normalized = virtual_lab.normalize_virtual_lab_extension(activity)

    assert normalized is not None
    assert normalized["submission"]["media_type"] == "application/json"
    assert virtual_lab.validate_virtual_lab_extension(activity, "activity.json") == []


def test_activity_validator_accepts_virtual_lab_extension() -> None:
    assert validate_activity.validate_activity(valid_thebitlab_activity(), "activity.json") == []


def test_activity_validator_reports_virtual_lab_contract_errors() -> None:
    activity = valid_thebitlab_activity()
    activity["extensions"][virtual_lab.VIRTUAL_LAB_EXTENSION_KEY]["submission"]["path"] = "../escape.json"

    errors = validate_activity.validate_activity(activity, "activity.json")

    assert (
        "activity.json: extensions.thebitlab.virtual_lab.submission.path deve essere un path relativo sicuro"
        in errors
    )
