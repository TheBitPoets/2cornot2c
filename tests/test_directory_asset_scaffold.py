from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts import create_submission_scaffold


def base_activity(identifier: str = "python-directory-asset-001") -> dict:
    return {
        "schema_version": "1.0",
        "id": identifier,
        "titolo": "Directory asset",
        "tipo": "laboratorio",
        "difficolta": "C",
        "argomenti": ["runtime"],
        "linguaggio": "python",
        "consegna": "Completa lo starter multi-file.",
        "correzione": {
            "compila": False,
            "test": False,
            "sandbox": False,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 30,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
    }


def write_activity(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def directory_activity(tmp_path: Path, *, target_path: str = "app") -> Path:
    payload = base_activity()
    payload["assets"] = [
        {
            "type": "starter",
            "path": "starter/app",
            "target_path": target_path,
            "visibility": "student",
        }
    ]
    return write_activity(tmp_path, payload)


def test_create_scaffold_copies_directory_asset_to_subdirectory(tmp_path: Path) -> None:
    starter = tmp_path / "starter" / "app"
    (starter / "routes").mkdir(parents=True)
    (starter / "__init__.py").write_text("APP = 'starter'\n", encoding="utf-8")
    (starter / "routes" / "health.py").write_text("READY = True\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path)

    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )

    assert (destination / "app" / "__init__.py").read_text(encoding="utf-8") == "APP = 'starter'\n"
    assert (destination / "app" / "routes" / "health.py").read_text(encoding="utf-8") == "READY = True\n"
    distributed = json.loads((destination / "activity.json").read_text(encoding="utf-8"))
    assert distributed["assets"][0]["path"] == "starter/app"
    assert distributed["assets"][0]["target_path"] == "app"


def test_create_scaffold_copies_directory_contents_to_root(tmp_path: Path) -> None:
    starter = tmp_path / "starter" / "app"
    (starter / "lib").mkdir(parents=True)
    (starter / "main.py").write_text("print('from directory')\n", encoding="utf-8")
    (starter / "lib" / "helper.py").write_text("VALUE = 42\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path, target_path=".")

    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=tmp_path / "student",
    )

    assert (destination / "main.py").read_text(encoding="utf-8") == "print('from directory')\n"
    assert (destination / "lib" / "helper.py").read_text(encoding="utf-8") == "VALUE = 42\n"


def test_directory_asset_overwrite_removes_unchanged_stale_file(tmp_path: Path) -> None:
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    current_source = starter / "current.py"
    stale_source = starter / "old.py"
    current_source.write_text("VALUE = 1\n", encoding="utf-8")
    stale_source.write_text("OLD = True\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )

    stale_source.unlink()
    current_source.write_text("VALUE = 2\n", encoding="utf-8")
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
    )

    assert not (destination / "app" / "old.py").exists()
    assert (destination / "app" / "current.py").read_text(encoding="utf-8") == "VALUE = 2\n"


def test_directory_asset_overwrite_preserves_student_modified_stale_file(tmp_path: Path) -> None:
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    stale_source = starter / "old.py"
    stale_source.write_text("OLD = True\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path)
    target_dir = tmp_path / "student"
    destination = create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
    )
    stale_target = destination / "app" / "old.py"
    stale_target.write_text("# modifica studente\n", encoding="utf-8")

    stale_source.unlink()
    # Keep the directory non-empty because empty directory assets are rejected.
    (starter / "current.py").write_text("VALUE = 1\n", encoding="utf-8")
    create_submission_scaffold.create_scaffold(
        activity_path=activity_path,
        target_dir=target_dir,
        overwrite=True,
    )

    assert stale_target.read_text(encoding="utf-8") == "# modifica studente\n"
    assert (destination / "app" / "current.py").exists()


def test_directory_asset_rejects_overlap_with_separate_asset(tmp_path: Path) -> None:
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    (starter / "main.py").write_text("print('app')\n", encoding="utf-8")
    (tmp_path / "extra.py").write_text("EXTRA = True\n", encoding="utf-8")
    payload = base_activity()
    payload["assets"] = [
        {"type": "starter", "path": "starter/app", "target_path": "app"},
        {"type": "example", "path": "extra.py", "target_path": "app/main.py"},
    ]
    activity_path = write_activity(tmp_path, payload)

    with pytest.raises(ValueError, match="duplicato, equivalente o sovrapposto"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )


def test_create_scaffold_rejects_file_asset_targeting_root(tmp_path: Path) -> None:
    (tmp_path / "starter.py").write_text("print('starter')\n", encoding="utf-8")
    payload = base_activity()
    payload["assets"] = [{"type": "starter", "path": "starter.py", "target_path": "."}]
    activity_path = write_activity(tmp_path, payload)

    with pytest.raises(ValueError, match="non portabile"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )


def test_create_scaffold_rejects_empty_directory_asset(tmp_path: Path) -> None:
    (tmp_path / "starter" / "app").mkdir(parents=True)
    activity_path = directory_activity(tmp_path)

    with pytest.raises(ValueError, match="Directory asset vuota"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )


def test_create_scaffold_rejects_reserved_file_inside_root_directory_asset(tmp_path: Path) -> None:
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    (starter / "README.md").write_text("reserved\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path, target_path=".")

    with pytest.raises(ValueError, match="riservato allo scaffold"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )


def test_create_scaffold_rejects_symlink_inside_directory_asset(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symlink non disponibile")
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    outside = tmp_path / "outside.py"
    outside.write_text("SECRET = True\n", encoding="utf-8")
    try:
        os.symlink(outside, starter / "linked.py")
    except OSError:
        pytest.skip("creazione symlink non consentita su questo host")
    activity_path = directory_activity(tmp_path)

    with pytest.raises(ValueError, match="link simbolici"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )


def test_create_scaffold_rejects_portable_aliases_inside_directory_asset(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("filesystem Windows non permette questa fixture")
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    (starter / "Foo.py").write_text("A = 1\n", encoding="utf-8")
    (starter / "foo.py").write_text("A = 2\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path)

    with pytest.raises(ValueError, match="portabilmente equivalenti"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )


def test_create_scaffold_rejects_nonportable_descendant_inside_directory_asset(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("fixture con nome riservato Windows")
    starter = tmp_path / "starter" / "app"
    starter.mkdir(parents=True)
    (starter / "CON.txt").write_text("bad\n", encoding="utf-8")
    activity_path = directory_activity(tmp_path)

    with pytest.raises(ValueError, match="non portabile"):
        create_submission_scaffold.create_scaffold(
            activity_path=activity_path,
            target_dir=tmp_path / "student",
        )
