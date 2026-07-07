from __future__ import annotations

import json
import argparse

from scripts import create_activity, validate_activity


def test_slugify_creates_filesystem_friendly_names() -> None:
    assert create_activity.slugify("Somma di due numeri!") == "somma-di-due-numeri"


def test_build_activity_generates_valid_activity() -> None:
    activity = create_activity.build_activity(
        activity_id="c-base-test-001",
        title="Esercizio test",
        activity_type="compito-casa",
        difficulty="B",
        topics=["variabili", "input-output"],
        prompt="Scrivi un programma minimale.",
        estimated_minutes=25,
        context={"classe": "3A-TPSI", "team_github": "3A-TPSI", "percorso": "", "uda": "uda-1"},
    )

    assert activity["schema_version"] == "1.0"
    assert activity["contesto"] == {"classe": "3A-TPSI", "team_github": "3A-TPSI", "uda": "uda-1"}
    assert validate_activity.validate_activity(activity) == []


def test_write_activity_uses_slugged_id_and_valid_json(tmp_path) -> None:
    activity = create_activity.build_activity(
        activity_id="Esercizio Variabili 01",
        title="Esercizio variabili",
        activity_type="compito-casa",
        difficulty="B",
        topics=["variabili"],
        prompt="Scrivi un programma minimale.",
        estimated_minutes=20,
    )

    output_path = create_activity.write_activity(activity, tmp_path)
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.name == "esercizio-variabili-01.json"
    assert written["id"] == "Esercizio Variabili 01"
    assert validate_activity.validate_activity(written) == []


def test_write_activity_refuses_to_overwrite_existing_file(tmp_path) -> None:
    activity = create_activity.build_activity(
        activity_id="attivita-duplicata",
        title="Attivita duplicata",
        activity_type="compito-casa",
        difficulty="B",
        topics=["variabili"],
        prompt="Scrivi un programma minimale.",
        estimated_minutes=20,
    )
    create_activity.write_activity(activity, tmp_path)

    try:
        create_activity.write_activity(activity, tmp_path)
    except ValueError as error:
        assert "File gia esistente" in str(error)
    else:
        raise AssertionError("write_activity should reject overwrite without force")


def test_write_activity_can_overwrite_with_force(tmp_path) -> None:
    activity = create_activity.build_activity(
        activity_id="attivita-force",
        title="Attivita force",
        activity_type="compito-casa",
        difficulty="B",
        topics=["variabili"],
        prompt="Scrivi un programma minimale.",
        estimated_minutes=20,
    )
    create_activity.write_activity(activity, tmp_path)

    output_path = create_activity.write_activity(activity, tmp_path, overwrite=True)

    assert output_path.exists()


def test_activity_from_args_requires_required_fields() -> None:
    class Args:
        titolo = "Titolo"
        tipo = None
        difficolta = "B"
        argomenti = "variabili"
        consegna = "Consegna"
        activity_id = None
        tempo_stimato = 30
        classe = ""
        team_github = ""
        percorso = ""
        uda = ""

    try:
        create_activity.activity_from_args(Args())
    except ValueError as error:
        assert "--tipo" in str(error)
    else:
        raise AssertionError("activity_from_args should reject missing required fields")


def test_activity_from_args_rejects_blank_text_fields() -> None:
    class Args:
        titolo = "   "
        tipo = "compito-casa"
        difficolta = "B"
        argomenti = "variabili"
        consegna = "Consegna"
        activity_id = None
        tempo_stimato = 30
        classe = ""
        team_github = ""
        percorso = ""
        uda = ""

    try:
        create_activity.activity_from_args(Args())
    except ValueError as error:
        assert "--titolo" in str(error)
    else:
        raise AssertionError("activity_from_args should reject blank titles")


def test_activity_from_args_rejects_empty_topics() -> None:
    class Args:
        titolo = "Titolo"
        tipo = "compito-casa"
        difficolta = "B"
        argomenti = " , , "
        consegna = "Consegna"
        activity_id = None
        tempo_stimato = 30
        classe = ""
        team_github = ""
        percorso = ""
        uda = ""

    try:
        create_activity.activity_from_args(Args())
    except ValueError as error:
        assert "almeno un argomento" in str(error)
    else:
        raise AssertionError("activity_from_args should reject empty topics")


def test_positive_int_rejects_zero() -> None:
    try:
        create_activity.positive_int("0")
    except argparse.ArgumentTypeError as error:
        assert "positivo" in str(error)
    else:
        raise AssertionError("positive_int should reject zero")


def test_create_interactive_uses_defaults() -> None:
    answers = iter(
        [
            "Somma due interi",
            "",
            "",
            "",
            "variabili, operatori",
            "Scrivi un programma C.",
            "",
            "3A-TPSI",
            "3A-TPSI",
            "terzo-anno",
            "uda-2",
        ]
    )

    activity = create_activity.create_interactive(input_fn=lambda _: next(answers))

    assert activity["id"] == "somma-due-interi"
    assert activity["tipo"] == "compito-casa"
    assert activity["difficolta"] == "B"
    assert activity["argomenti"] == ["variabili", "operatori"]
    assert activity["metriche"]["tempo_stimato_minuti"] == 30
    assert validate_activity.validate_activity(activity) == []


def test_create_interactive_repeats_empty_topics() -> None:
    answers = iter(
        [
            "Somma due interi",
            "",
            "",
            "",
            ", ,",
            "variabili",
            "Scrivi un programma C.",
            "",
            "",
            "",
            "",
            "",
        ]
    )

    activity = create_activity.create_interactive(input_fn=lambda _: next(answers))

    assert activity["argomenti"] == ["variabili"]
