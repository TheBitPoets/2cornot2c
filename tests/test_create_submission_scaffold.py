from __future__ import annotations

import json

from scripts import create_submission_scaffold


def activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "c-base-somma-001",
        "titolo": "Somma di due interi",
        "tipo": "compito-casa",
        "difficolta": "B",
        "argomenti": ["variabili", "operatori"],
        "linguaggio": "c",
        "consegna": "Scrivi un programma C che legge due interi e stampa la somma.",
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


def write_activity(tmp_path, payload: dict | None = None):
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(activity() if payload is None else payload), encoding="utf-8")
    return path


def canonical_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "title": "Somma canonica",
        "kind": "compito-casa",
        "difficulty": "B",
        "topics": ["variabili", "operatori"],
        "language": "python",
        "instructions": "Scrivi un programma Python che stampa una somma.",
        "student_support_mode": "senza-aiuto",
        "grading_policy": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
    }


def test_create_scaffold_writes_assignment_files(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)

    assert destination == tmp_path / "assignments" / "c-base-somma-001"
    assert json.loads((destination / "activity.json").read_text(encoding="utf-8"))["id"] == "c-base-somma-001"
    assert (destination / "main.c").read_text(encoding="utf-8").startswith("#include <stdio.h>")
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "activity_id`: `c-base-somma-001`" in readme
    assert "source_path`: `assignments/c-base-somma-001/main.c`" in readme
    assert "thebitlab_ref`: `main`" in readme


def test_create_scaffold_supports_canonical_activity_metadata(tmp_path) -> None:
    activity_path = write_activity(tmp_path, canonical_activity())

    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)

    assert destination == tmp_path / "assignments" / "python-base-somma-001"
    assert (destination / "main.py").exists()
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "# Somma canonica" in readme
    assert "Scrivi un programma Python che stampa una somma." in readme
    assert "language`: `python`" in readme


def test_create_scaffold_rejects_invalid_canonical_kind(tmp_path) -> None:
    activity_path = write_activity(
        tmp_path,
        {
            **activity(),
            "tipo": "compito-casa",
            "kind": "compito-classe",
        },
    )

    try:
        create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    except ValueError as error:
        assert "kind non ammesso: compito-classe" in str(error)
    else:
        raise AssertionError("create_scaffold should reject invalid canonical kind")

    assert not (tmp_path / "assignments").exists()


def test_create_scaffold_rejects_unsafe_activity_id(tmp_path) -> None:
    activity_path = write_activity(tmp_path, {**activity(), "id": "Somma 001"})

    try:
        create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    except ValueError as error:
        assert "slug sicuro" in str(error)
    else:
        raise AssertionError("create_scaffold should reject unsafe activity ids")


def test_create_scaffold_rejects_invalid_activity_before_writing(tmp_path) -> None:
    activity_path = write_activity(tmp_path, {"id": "c-base-somma-001"})

    try:
        create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    except ValueError as error:
        assert "schema_version" in str(error)
    else:
        raise AssertionError("create_scaffold should reject invalid activities")

    assert not (tmp_path / "assignments").exists()


def test_create_scaffold_rejects_non_object_activity_json(tmp_path) -> None:
    activity_path = write_activity(tmp_path, [])

    try:
        create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    except ValueError as error:
        assert "oggetto JSON" in str(error)
    else:
        raise AssertionError("create_scaffold should reject non-object activity JSON")


def test_create_scaffold_refuses_existing_assignment_without_force(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)

    try:
        create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    except ValueError as error:
        assert "Consegna gia esistente" in str(error)
    else:
        raise AssertionError("create_scaffold should reject existing assignments")


def test_create_scaffold_force_preserves_existing_source(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    (destination / "main.c").write_text("custom\n", encoding="utf-8")

    create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path, overwrite=True)

    assert (destination / "main.c").read_text(encoding="utf-8") == "custom\n"


def test_create_scaffold_can_overwrite_source_explicitly(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    (destination / "main.c").write_text("custom\n", encoding="utf-8")

    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path,
        overwrite=True,
        overwrite_source=True,
    )

    assert "Scrivi qui" in (destination / "main.c").read_text(encoding="utf-8")


def test_create_scaffold_supports_custom_source_name_and_language(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path,
        source_name="solution.py",
        language="python",
    )

    assert (destination / "solution.py").exists()
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "language`: `python`" in readme
    assert "source_path`: `assignments/c-base-somma-001/solution.py`" in readme


def test_create_scaffold_normalizes_language_aliases(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path,
        language="c++",
    )

    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "language`: `cpp`" in readme


def test_create_scaffold_writes_non_empty_starter_for_supported_languages(tmp_path) -> None:
    for language in create_submission_scaffold.SUPPORTED_LANGUAGES:
        activity_id = f"{language}-exercise"
        activity_path = write_activity(tmp_path, {**activity(), "id": activity_id, "linguaggio": language})
        source_name = create_submission_scaffold.default_source_name_for(language)

        destination = create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / language,
        )

        assert (destination / source_name).read_text(encoding="utf-8").strip()


def test_create_scaffold_rejects_unsupported_language(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
            language="brainfuck",
        )
    except ValueError as error:
        assert "Linguaggio non supportato" in str(error)
    else:
        raise AssertionError("create_scaffold should reject unsupported languages")


def test_create_scaffold_rejects_empty_language(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
            language="",
        )
    except ValueError as error:
        assert "Linguaggio non supportato" in str(error)
    else:
        raise AssertionError("create_scaffold should reject empty languages")


def test_create_scaffold_rejects_empty_activity_language(tmp_path) -> None:
    activity_path = write_activity(tmp_path, {**activity(), "linguaggio": ""})

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
        )
    except ValueError as error:
        assert "Linguaggio non supportato" in str(error)
    else:
        raise AssertionError("create_scaffold should reject empty activity languages")


def test_create_scaffold_rejects_conflicting_activity_languages(tmp_path) -> None:
    activity_path = write_activity(tmp_path, {**activity(), "linguaggio": "python", "language": "c"})

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
        )
    except ValueError as error:
        assert "linguaggio e language" in str(error)
    else:
        raise AssertionError("create_scaffold should reject conflicting activity languages")


def test_create_scaffold_supports_custom_thebitlab_ref(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path,
        thebitlab_ref="v1.0.0",
    )

    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "thebitlab_ref`: `v1.0.0`" in readme


def test_create_scaffold_rejects_multiline_thebitlab_ref(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
            thebitlab_ref="main\naltro",
        )
    except ValueError as error:
        assert "thebitlab_ref" in str(error)
    else:
        raise AssertionError("create_scaffold should reject multiline refs")


def test_create_scaffold_rejects_source_name_with_path_segments(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
            source_name="../main.c",
        )
    except ValueError as error:
        assert "nome file semplice" in str(error)
    else:
        raise AssertionError("create_scaffold should reject path traversal in source_name")


def test_create_scaffold_rejects_source_name_with_unsafe_characters(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
            source_name="`main`.c",
        )
    except ValueError as error:
        assert "nome file semplice" in str(error)
    else:
        raise AssertionError("create_scaffold should reject unsafe characters in source_name")


def test_create_scaffold_rejects_empty_source_name(tmp_path) -> None:
    activity_path = write_activity(tmp_path)

    try:
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path,
            source_name="",
        )
    except ValueError as error:
        assert "nome file semplice" in str(error)
    else:
        raise AssertionError("create_scaffold should reject empty source_name")
