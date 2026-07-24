from __future__ import annotations

import json
import os

import pytest

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


def test_create_scaffold_excludes_teacher_grading_data(tmp_path) -> None:
    payload = activity()
    payload["test_cases"] = [
        {"name": "riservato", "stdin": "2 3\n", "expected_stdout": "5\n"},
        {
            "name": "pubblico",
            "stdin": "1 1\n",
            "expected_stdout": "2\n",
            "visibility": "student",
        },
    ]
    payload["rubrica"] = [{"criterio": "Correttezza", "punti": 100}]
    payload["soluzione_attesa"] = {
        "tipo": "programma-c",
        "output_atteso": "Differenza: 3",
    }
    payload["support_mode"] = "feedback-tecnico"
    payload["source_refs"] = [
        {
            "path": "doc/dispensa.md",
            "heading": "Array",
            "expected_stdout": "SEGRETO_ANNIDATO",
        }
    ]
    payload["contesto"] = {
        "classe": {"expected_stdout": "SEGRETO_TIPO"},
        "percorso": "terzo-anno",
    }
    payload["source_refs"].append(
        {"description": {"expected_stdout": "SEGRETO_TIPO"}}
    )
    payload["vincoli"] = ["usa scanf", {"expected_stdout": "SEGRETO_TIPO"}]
    payload["correzione"]["expected_stdout"] = "SEGRETO_ANNIDATO"
    payload["metriche"]["teacher_notes"] = "SEGRETO_ANNIDATO"
    payload["assets"] = [
        {"type": "hidden_test", "path": "tests/hidden.py", "visibility": "teacher"},
    ]
    activity_path = write_activity(tmp_path, payload)

    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )

    distributed = json.loads((destination / "activity.json").read_text(encoding="utf-8"))
    assert distributed["test_cases"] == [
        {
            "name": "pubblico",
            "stdin": "1 1\n",
            "expected_stdout": "2\n",
            "visibility": "student",
        }
    ]
    assert "rubrica" not in distributed
    assert "soluzione_attesa" not in distributed
    assert distributed["assets"] == []
    assert distributed["support_mode"] == "feedback-tecnico"
    assert distributed["source_refs"] == [
        {"path": "doc/dispensa.md", "heading": "Array"},
    ]
    assert distributed["vincoli"] == ["usa scanf"]
    assert distributed["contesto"] == {"percorso": "terzo-anno"}
    serialized = json.dumps(distributed)
    assert "riservato" not in serialized
    assert "2 3" not in serialized
    assert "Differenza: 3" not in serialized
    assert "SEGRETO_ANNIDATO" not in serialized
    assert "SEGRETO_TIPO" not in serialized


def test_create_scaffold_supports_canonical_activity_metadata(tmp_path) -> None:
    activity_path = write_activity(tmp_path, canonical_activity())

    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)

    assert destination == tmp_path / "assignments" / "python-base-somma-001"
    assert (destination / "main.py").exists()
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "# Somma canonica" in readme
    assert "Scrivi un programma Python che stampa una somma." in readme
    assert "language`: `python`" in readme


def test_create_scaffold_copies_student_assets_only(tmp_path) -> None:
    (tmp_path / "starter").mkdir()
    (tmp_path / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_public.py").write_text("def test_public():\n    assert True\n", encoding="utf-8")
    (tmp_path / "tests" / "test_hidden.py").write_text("def test_hidden():\n    assert True\n", encoding="utf-8")
    (tmp_path / "solution").mkdir()
    (tmp_path / "solution" / "main.py").write_text("print('solution')\n", encoding="utf-8")
    activity_path = write_activity(
        tmp_path,
        {
            **activity(),
            "id": "python-assets-001",
            "linguaggio": "python",
            "assets": [
                {"type": "starter", "path": "starter/main.py", "target_path": "main.py"},
                {"type": "visible_test", "path": "tests/test_public.py", "target_path": "tests/test_public.py"},
                {"type": "hidden_test", "path": "tests/test_hidden.py"},
                {"type": "teacher_only", "path": "solution/main.py", "visibility": "teacher"},
            ],
        },
    )

    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)

    assert (destination / "main.py").read_text(encoding="utf-8") == "print('starter')\n"
    assert (destination / "tests" / "test_public.py").exists()
    assert not (destination / "tests" / "test_hidden.py").exists()
    assert not (destination / "solution" / "main.py").exists()
    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "`main.py` (starter)" in readme
    assert "`tests/test_public.py` (visible_test)" in readme


def test_create_scaffold_readme_keeps_default_source_when_assets_are_support_files(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_public.py").write_text("def test_public():\n    assert True\n", encoding="utf-8")
    activity_path = write_activity(
        tmp_path,
        {
            **activity(),
            "id": "python-public-test-001",
            "linguaggio": "python",
            "assets": [
                {"type": "visible_test", "path": "tests/test_public.py", "target_path": "tests/test_public.py"},
            ],
        },
    )

    destination = create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)

    readme = (destination / "README.md").read_text(encoding="utf-8")
    assert "- `main.py`" in readme
    assert "- `tests/test_public.py` (visible_test)" in readme


def test_create_scaffold_rejects_missing_student_asset(tmp_path) -> None:
    activity_path = write_activity(
        tmp_path,
        {
            **activity(),
            "assets": [{"type": "starter", "path": "starter/missing.c", "target_path": "main.c"}],
        },
    )

    try:
        create_submission_scaffold.create_scaffold(activity_path=activity_path, target_dir=tmp_path)
    except ValueError as error:
        assert "Asset non trovato" in str(error)
    else:
        raise AssertionError("create_scaffold should reject missing student assets")

    assert not (tmp_path / "assignments").exists()


@pytest.mark.parametrize(
    "reserved_target",
    ["activity.json", "ACTIVITY.JSON", "README.md", "readme.md", "README.md."],
)
def test_create_scaffold_rejects_asset_target_reserved_for_scaffold(
    tmp_path,
    reserved_target,
) -> None:
    (tmp_path / "asset.txt").write_text("contenuto\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "example",
                "path": "asset.txt",
                "target_path": reserved_target,
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"

    with pytest.raises(ValueError, match="riservato allo scaffold"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=target_dir,
        )

    assert not (target_dir / "assignments").exists()


@pytest.mark.parametrize(
    "targets",
    [
        ("data", "data/input.txt"),
        ("data/input.txt", "data"),
    ],
)
def test_create_scaffold_rejects_parent_child_asset_targets(tmp_path, targets) -> None:
    (tmp_path / "first.txt").write_text("primo\n", encoding="utf-8")
    (tmp_path / "second.txt").write_text("secondo\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {"type": "example", "path": "first.txt", "target_path": targets[0]},
            {"type": "example", "path": "second.txt", "target_path": targets[1]},
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"

    with pytest.raises(ValueError, match="sovrapposto"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=target_dir,
        )

    assert not (target_dir / "assignments").exists()


def test_create_scaffold_rejects_linked_asset_outside_activity_bundle(tmp_path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "starter").mkdir()
    external = tmp_path / "external.py"
    external.write_text("SECRET = 'locale docente'\n", encoding="utf-8")
    linked_asset = bundle / "starter" / "main.py"
    try:
        linked_asset.symlink_to(external)
    except OSError:
        pytest.skip("Creazione symlink non consentita su questa piattaforma.")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "starter",
                "path": "starter/main.py",
                "target_path": "main.py",
            }
        ],
    }
    activity_path = bundle / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")
    target_dir = tmp_path / "student"

    with pytest.raises(ValueError, match="link simbolici"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=target_dir,
        )

    assert not (target_dir / "assignments").exists()


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


def test_create_scaffold_force_removes_asset_that_became_teacher_only(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    asset_source = tmp_path / "tests" / "test_secret.py"
    asset_source.write_text("SECRET = 'teacher-only'\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "visible_test",
                "path": "tests/test_secret.py",
                "target_path": "tests/test_secret.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )
    (destination / "notes.txt").write_text("file studente\n", encoding="utf-8")
    (destination / "main.py").write_text("codice studente\n", encoding="utf-8")

    payload["assets"][0]["type"] = "hidden_test"
    payload["assets"][0]["visibility"] = "teacher"
    write_activity(tmp_path, payload)
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
        overwrite=True,
    )

    assert not (destination / "tests" / "test_secret.py").exists()
    assert (destination / "main.py").read_text(encoding="utf-8") == "codice studente\n"
    assert (destination / "notes.txt").read_text(encoding="utf-8") == "file studente\n"


def test_create_scaffold_requires_clean_regeneration_for_legacy_assets(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_secret.py").write_text("SECRET = 'old-public'\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "visible_test",
                "path": "tests/test_secret.py",
                "target_path": "tests/test_secret.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    manifest_path = create_submission_scaffold.managed_assets_path(
        target_dir,
        "python-base-somma-001",
    )
    manifest_path.unlink()

    payload["assets"][0]["type"] = "hidden_test"
    payload["assets"][0]["visibility"] = "teacher"
    write_activity(tmp_path, payload)

    for overwrite_source in (False, True):
        try:
            create_submission_scaffold.create_scaffold(
                activity_path=activity_path,
                target_dir=target_dir,
                overwrite=True,
                overwrite_source=overwrite_source,
            )
        except ValueError as error:
            assert "archivia o rinomina" in str(error)
        else:
            raise AssertionError("legacy scaffold should require a clean regeneration")

    assert (destination / "tests" / "test_secret.py").exists()
    backup = destination.with_name(f"{destination.name}-backup")
    destination.rename(backup)
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
    )
    assert not (destination / "tests" / "test_secret.py").exists()
    assert (backup / "tests" / "test_secret.py").exists()
    assert manifest_path.exists()


def test_create_scaffold_force_removes_public_asset_deleted_from_activity(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_old.py").write_text("def test_old(): pass\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "visible_test",
                "path": "tests/test_old.py",
                "target_path": "tests/test_old.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )

    payload["assets"] = []
    write_activity(tmp_path, payload)
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
        overwrite=True,
    )

    assert not (destination / "tests" / "test_old.py").exists()


def test_create_scaffold_force_preserves_unmanaged_private_target(tmp_path) -> None:
    payload = canonical_activity()
    activity_path = write_activity(tmp_path, payload)
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )
    (destination / "notes.txt").write_text("file studente\n", encoding="utf-8")

    payload["assets"] = [
        {
            "type": "hidden_test",
            "path": "teacher/hidden.py",
            "target_path": "notes.txt",
            "visibility": "teacher",
        }
    ]
    write_activity(tmp_path, payload)
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
        overwrite=True,
    )

    assert (destination / "notes.txt").read_text(encoding="utf-8") == "file studente\n"


def test_create_scaffold_ignores_student_repository_manifest(tmp_path) -> None:
    payload = canonical_activity()
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    notes = destination / "notes.txt"
    notes.write_text("file studente\n", encoding="utf-8")
    forged_manifest = destination / ".thebitlab-managed-assets.json"
    forged_manifest.write_text(
        json.dumps(
            {
                "assets": {
                    "notes.txt": create_submission_scaffold.file_sha256(notes),
                }
            }
        ),
        encoding="utf-8",
    )

    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
    )

    assert notes.read_text(encoding="utf-8") == "file studente\n"
    assert forged_manifest.exists()


def test_managed_asset_state_for_dot_target_is_outside_repository(tmp_path, monkeypatch) -> None:
    repository = tmp_path / "student"
    repository.mkdir()
    monkeypatch.chdir(repository)

    manifest_path = create_submission_scaffold.managed_assets_path(
        create_submission_scaffold.DEFAULT_TARGET_DIR,
        "python-base-somma-001",
    )

    assert manifest_path.parents[1] == repository.parent / create_submission_scaffold.MANAGED_ASSETS_STATE_DIR


def test_managed_asset_state_rejects_directory_inside_repository(tmp_path) -> None:
    repository = tmp_path / "student"

    with pytest.raises(ValueError, match="esterna al repository"):
        create_submission_scaffold.managed_assets_path(
            repository,
            "python-base-somma-001",
            repository / ".state",
        )


def test_create_scaffold_does_not_follow_student_manifest_symlink(tmp_path) -> None:
    activity_path = write_activity(tmp_path, canonical_activity())
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    external = tmp_path / "external.txt"
    external.write_text("non modificare\n", encoding="utf-8")
    forged_manifest = destination / ".thebitlab-managed-assets.json"
    try:
        forged_manifest.symlink_to(external)
    except OSError:
        pytest.skip("Creazione symlink non consentita su questa piattaforma.")

    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
    )

    assert external.read_text(encoding="utf-8") == "non modificare\n"
    assert forged_manifest.is_symlink()


def test_create_scaffold_rejects_metadata_symlink_on_force(tmp_path) -> None:
    activity_path = write_activity(tmp_path, canonical_activity())
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    external = tmp_path / "external.json"
    external.write_text("non modificare\n", encoding="utf-8")
    scaffold_activity = destination / "activity.json"
    scaffold_activity.unlink()
    try:
        scaffold_activity.symlink_to(external)
    except OSError:
        pytest.skip("Creazione symlink non consentita su questa piattaforma.")

    with pytest.raises(ValueError, match="link simbolico"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=target_dir,
            overwrite=True,
        )

    assert external.read_text(encoding="utf-8") == "non modificare\n"


def test_create_scaffold_rejects_asset_parent_symlink_on_force(tmp_path) -> None:
    activity_path = write_activity(tmp_path, canonical_activity())
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    teacher_tests = tmp_path / "tests"
    teacher_tests.mkdir()
    (teacher_tests / "test_public.py").write_text("def test_public(): pass\n", encoding="utf-8")
    external = tmp_path / "external"
    external.mkdir()
    try:
        (destination / "tests").symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("Creazione symlink non consentita su questa piattaforma.")
    payload = canonical_activity()
    payload["assets"] = [
        {
            "type": "visible_test",
            "path": "tests/test_public.py",
            "target_path": "tests/test_public.py",
        }
    ]
    write_activity(tmp_path, payload)

    with pytest.raises(ValueError, match="link simbolico"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=target_dir,
            overwrite=True,
        )

    assert not (external / "test_public.py").exists()


def test_create_scaffold_force_preserves_modified_stale_asset(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_old.py").write_text("def test_old(): pass\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "visible_test",
                "path": "tests/test_old.py",
                "target_path": "tests/test_old.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )
    stale_asset = destination / "tests" / "test_old.py"
    stale_asset.write_text("modifica studente\n", encoding="utf-8")

    payload["assets"] = []
    write_activity(tmp_path, payload)
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
        overwrite=True,
    )

    assert stale_asset.read_text(encoding="utf-8") == "modifica studente\n"


def test_create_scaffold_force_updates_unchanged_managed_asset(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    teacher_asset = tmp_path / "tests" / "test_public.py"
    teacher_asset.write_text("VERSION = 1\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "visible_test",
                "path": "tests/test_public.py",
                "target_path": "tests/test_public.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )

    teacher_asset.write_text("VERSION = 2\n", encoding="utf-8")
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
        overwrite=True,
    )

    assert (destination / "tests" / "test_public.py").read_text(encoding="utf-8") == "VERSION = 2\n"


def test_create_scaffold_force_preserves_modified_current_asset(tmp_path) -> None:
    (tmp_path / "tests").mkdir()
    teacher_asset = tmp_path / "tests" / "test_public.py"
    teacher_asset.write_text("VERSION = 1\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "visible_test",
                "path": "tests/test_public.py",
                "target_path": "tests/test_public.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )
    student_asset = destination / "tests" / "test_public.py"
    student_asset.write_text("MODIFICA = 'studente'\n", encoding="utf-8")

    teacher_asset.write_text("VERSION = 2\n", encoding="utf-8")
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
        overwrite=True,
    )

    assert student_asset.read_text(encoding="utf-8") == "MODIFICA = 'studente'\n"


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


def test_create_scaffold_overwrite_keeps_teacher_starter_asset(tmp_path) -> None:
    (tmp_path / "starter").mkdir()
    teacher_starter = tmp_path / "starter" / "main.py"
    teacher_starter.write_text("print('starter docente')\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "starter",
                "path": "starter/main.py",
                "target_path": "main.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    (destination / "main.py").write_text("modifica studente\n", encoding="utf-8")

    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
        overwrite_source=True,
    )

    assert (destination / "main.py").read_text(encoding="utf-8") == "print('starter docente')\n"


def test_create_scaffold_overwrite_source_preserves_modified_non_source_asset(tmp_path) -> None:
    (tmp_path / "examples").mkdir()
    teacher_example = tmp_path / "examples" / "example.txt"
    teacher_example.write_text("esempio docente v1\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "example",
                "path": "examples/example.txt",
                "target_path": "example.txt",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    student_example = destination / "example.txt"
    student_example.write_text("annotazioni studente\n", encoding="utf-8")
    teacher_example.write_text("esempio docente v2\n", encoding="utf-8")

    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
        overwrite_source=True,
    )

    assert student_example.read_text(encoding="utf-8") == "annotazioni studente\n"
    assert "Scrivi qui" in (destination / "main.py").read_text(encoding="utf-8")


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


@pytest.mark.parametrize(
    "source_name",
    ["activity.json", "ACTIVITY.JSON", "README.md", "readme.md", "README.md."],
)
def test_create_scaffold_rejects_reserved_source_name(tmp_path, source_name) -> None:
    activity_path = write_activity(tmp_path)

    with pytest.raises(ValueError, match="riservato allo scaffold"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
            source_name=source_name,
        )


def test_create_scaffold_rejects_source_asset_case_alias(tmp_path) -> None:
    (tmp_path / "starter").mkdir()
    (tmp_path / "starter" / "main.py").write_text("print('docente')\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "starter",
                "path": "starter/main.py",
                "target_path": "MAIN.PY",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)

    with pytest.raises(ValueError, match="nome canonico main.py"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )

    assert not (tmp_path / "student" / "assignments").exists()


def test_create_scaffold_reconciles_trusted_source_alias_on_case_sensitive_fs(tmp_path) -> None:
    if os.name == "nt":
        pytest.skip("Scenario di trasferimento da Windows a filesystem case-sensitive.")
    (tmp_path / "starter").mkdir()
    (tmp_path / "starter" / "main.py").write_text("print('docente')\n", encoding="utf-8")
    payload = {
        **canonical_activity(),
        "assets": [
            {
                "type": "starter",
                "path": "starter/main.py",
                "target_path": "main.py",
            }
        ],
    }
    activity_path = write_activity(tmp_path, payload)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    source = destination / "main.py"
    source.write_text("print('studente')\n", encoding="utf-8")
    source.rename(destination / "MAIN.PY")
    manifest_path = create_submission_scaffold.managed_assets_path(
        target_dir,
        "python-base-somma-001",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"]["MAIN.PY"] = manifest["assets"].pop("main.py")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
    )

    assert (destination / "main.py").read_text(encoding="utf-8") == "print('studente')\n"
    assert not (destination / "MAIN.PY").exists()
