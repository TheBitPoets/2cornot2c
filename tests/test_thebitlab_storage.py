from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from scripts.thebitlab_storage import JsonAssignmentStorage, JsonClassRosterStorage, JsonCourseStorage


def test_read_design_returns_minimal_default_when_missing(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path, ["README.md"])

    assert storage.read_design() == {"version": 1, "source_files": ["README.md"], "years": []}


def test_write_and_read_current_design(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    payload = {"schema_version": "1.0", "years": [{"id": "terzo"}]}

    storage.write_design(payload)

    assert storage.read_design() == payload
    assert (tmp_path / "doc" / "course_design.json").read_text(encoding="utf-8").endswith("\n")


def test_json_overwrite_keeps_previous_content_when_publication_fails(tmp_path, monkeypatch) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_design({"title": "Versione precedente"})
    target = storage.design_path

    monkeypatch.setattr(
        "scripts.thebitlab_storage.os.replace",
        lambda _source, _destination: (_ for _ in ()).throw(OSError("pubblicazione interrotta")),
    )

    with pytest.raises(OSError, match="pubblicazione interrotta"):
        storage.write_design({"title": "Versione nuova"})

    assert storage.read_design() == {"title": "Versione precedente"}
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []


def test_json_publication_syncs_destination_directory(tmp_path, monkeypatch) -> None:
    synced: list[Path] = []
    monkeypatch.setattr("scripts.thebitlab_storage.sync_directory", lambda path: synced.append(path))
    storage = JsonCourseStorage(tmp_path)

    storage.write_design({"title": "Versione durevole"})

    assert storage.design_path.parent in synced


def test_saved_designs_are_validated_and_listed(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)

    saved = storage.write_saved_design("as_2026_2027.json", {"title": "AS 2026/2027"})

    assert saved == {
        "name": "as_2026_2027.json",
        "path": "doc/course_designs/as_2026_2027.json",
    }
    assert storage.list_saved_designs() == [saved]
    assert storage.read_saved_design("as_2026_2027.json") == {"title": "AS 2026/2027"}


def test_saved_design_rejects_unsafe_name(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)

    with pytest.raises(ValueError):
        storage.write_saved_design("../unsafe.json", {})


def test_saved_design_create_does_not_overwrite_existing_file(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("existing.json", {"title": "Originale"}, overwrite=False)

    with pytest.raises(FileExistsError):
        storage.write_saved_design("existing.json", {"title": "Nuovo"}, overwrite=False)

    assert storage.read_saved_design("existing.json") == {"title": "Originale"}


def test_saved_design_create_does_not_publish_partial_file_when_sync_fails(tmp_path, monkeypatch) -> None:
    storage = JsonCourseStorage(tmp_path)
    target = storage.saved_design_path("retry.json")
    monkeypatch.setattr("scripts.thebitlab_storage.os.fsync", lambda _descriptor: (_ for _ in ()).throw(OSError("sync")))

    with pytest.raises(OSError, match="sync"):
        storage.write_saved_design("retry.json", {"title": "Incompleto"}, overwrite=False)

    assert not target.exists()
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []

    monkeypatch.undo()
    storage.write_saved_design("retry.json", {"title": "Completo"}, overwrite=False)
    assert storage.read_saved_design("retry.json") == {"title": "Completo"}


def test_school_calendar_metadata_tolerates_invalid_json(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    calendars_dir = tmp_path / "doc" / "calendars"
    calendars_dir.mkdir(parents=True)
    (calendars_dir / "broken.json").write_text("{", encoding="utf-8")
    (calendars_dir / "empty-link.json").write_text(json.dumps({"course_design_name": None}), encoding="utf-8")
    storage.write_school_calendar("valid.json", {"course_design_name": "as_2026_2027.json"})

    assert storage.list_school_calendars() == [
        {
            "name": "broken.json",
            "path": "doc/calendars/broken.json",
            "course_design_name": "",
        },
        {
            "name": "empty-link.json",
            "path": "doc/calendars/empty-link.json",
            "course_design_name": "",
        },
        {
            "name": "valid.json",
            "path": "doc/calendars/valid.json",
            "course_design_name": "as_2026_2027.json",
        },
    ]


def test_delete_saved_design_deletes_only_linked_calendars(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("as_2026_2027.json", {"title": "AS 2026/2027"})
    storage.write_school_calendar("linked.json", {"course_design_name": "as_2026_2027.json"})
    storage.write_school_calendar("other.json", {"course_design_name": "other.json"})

    result = storage.delete_saved_design(
        "as_2026_2027.json",
        delete_calendars=True,
        calendars=["linked.json", "other.json", "missing.json"],
    )

    assert result["name"] == "as_2026_2027.json"
    assert result["deleted_calendars"] == ["linked.json"]
    assert result["designs"] == []
    assert result["calendars"] == [
        {
            "name": "other.json",
            "path": "doc/calendars/other.json",
            "course_design_name": "other.json",
        }
    ]
    assert not (tmp_path / "doc" / "calendars" / "linked.json").exists()
    assert (tmp_path / "doc" / "calendars" / "other.json").exists()


def test_delete_saved_design_rescans_linked_calendars_under_lock(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da eliminare"})
    storage.write_school_calendar("known.json", {"course_design_name": "victim.json"})
    storage.write_school_calendar("created-later.json", {"course_design_name": "victim.json"})

    result = storage.delete_saved_design(
        "victim.json",
        delete_calendars=True,
        calendars=["known.json"],
    )

    assert result["deleted_calendars"] == ["created-later.json", "known.json"]
    assert storage.list_school_calendars() == []


def test_delete_saved_design_validates_all_calendar_names_before_deleting(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da conservare"})

    with pytest.raises(ValueError):
        storage.delete_saved_design(
            "victim.json",
            delete_calendars=True,
            calendars=["../unsafe.json"],
        )

    assert storage.read_saved_design("victim.json") == {"title": "Da conservare"}


def test_delete_saved_design_rolls_back_when_staging_fails(tmp_path, monkeypatch) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da conservare"})
    storage.write_school_calendar("linked.json", {"course_design_name": "victim.json"})
    real_replace = os.replace
    calls = 0

    def fail_second_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("staging non disponibile")
        real_replace(source, destination)

    monkeypatch.setattr("scripts.thebitlab_storage.os.replace", fail_second_replace)

    with pytest.raises(OSError, match="staging non disponibile"):
        storage.delete_saved_design(
            "victim.json",
            delete_calendars=True,
            calendars=["linked.json"],
        )

    assert storage.read_saved_design("victim.json") == {"title": "Da conservare"}
    assert storage.read_school_calendar("linked.json") == {"course_design_name": "victim.json"}


def test_save_waits_for_delete_rollback_before_updating_design(tmp_path, monkeypatch) -> None:
    deleting_storage = JsonCourseStorage(tmp_path)
    saving_storage = JsonCourseStorage(tmp_path)
    deleting_storage.write_saved_design("victim.json", {"title": "Originale"})
    deleting_storage.write_school_calendar("linked.json", {"course_design_name": "victim.json"})
    first_move_done = threading.Event()
    continue_delete = threading.Event()
    save_done = threading.Event()
    real_replace = os.replace
    calls = 0

    def controlled_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 1:
            real_replace(source, destination)
            first_move_done.set()
            assert continue_delete.wait(timeout=5)
            return
        if calls == 2:
            raise OSError("staging non disponibile")
        real_replace(source, destination)

    monkeypatch.setattr("scripts.thebitlab_storage.os.replace", controlled_replace)

    def delete_design() -> None:
        with pytest.raises(OSError, match="staging non disponibile"):
            deleting_storage.delete_saved_design(
                "victim.json",
                delete_calendars=True,
                calendars=["linked.json"],
            )

    def save_design() -> None:
        saving_storage.write_saved_design("victim.json", {"title": "Aggiornato"})
        save_done.set()

    delete_thread = threading.Thread(target=delete_design)
    save_thread = threading.Thread(target=save_design)
    delete_thread.start()
    assert first_move_done.wait(timeout=5)
    save_thread.start()
    assert save_done.wait(timeout=0.1) is False
    continue_delete.set()
    delete_thread.join(timeout=5)
    save_thread.join(timeout=5)

    assert save_done.is_set()
    assert saving_storage.read_saved_design("victim.json") == {"title": "Aggiornato"}


def test_calendar_save_waits_for_course_storage_operation(tmp_path) -> None:
    locking_storage = JsonCourseStorage(tmp_path)
    saving_storage = JsonCourseStorage(tmp_path)
    save_started = threading.Event()
    save_done = threading.Event()

    def save_calendar() -> None:
        save_started.set()
        saving_storage.write_school_calendar("linked.json", {"course_design_name": "victim.json"})
        save_done.set()

    save_thread = threading.Thread(target=save_calendar)
    with locking_storage.operation_lock:
        save_thread.start()
        assert save_started.wait(timeout=5)
        assert save_done.wait(timeout=0.1) is False

    save_thread.join(timeout=5)
    assert save_done.is_set()
    assert saving_storage.read_school_calendar("linked.json") == {"course_design_name": "victim.json"}


def test_course_storage_lock_serializes_different_processes(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    command = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; "
            "from scripts.thebitlab_storage import JsonCourseStorage; "
            f"storage = JsonCourseStorage(Path({str(tmp_path)!r})); "
            "storage.write_design({'title': 'child'}); "
            "print('completed', flush=True)"
        ),
    ]

    with storage.operation_lock:
        process = subprocess.Popen(command, cwd=Path.cwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(0.3)
        assert process.poll() is None

    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, stderr
    assert stdout.strip() == "completed"
    assert storage.read_design() == {"title": "child"}


def test_uncommitted_delete_transaction_is_restored_on_next_adapter(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da ripristinare"})
    original = storage.saved_design_path("victim.json")
    transaction_dir = storage.delete_staging_dir / "interrupted"
    transaction_dir.mkdir(parents=True)
    staged = transaction_dir / "0-victim.json"
    os.replace(original, staged)
    (transaction_dir / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [{"original": storage.relative_path(original), "staged": staged.name}],
            }
        ),
        encoding="utf-8",
    )

    recovered = JsonCourseStorage(tmp_path)

    assert recovered.read_saved_design("victim.json") == {"title": "Da ripristinare"}
    assert not transaction_dir.exists()


def test_committed_delete_transaction_is_completed_on_next_adapter(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da eliminare"})
    original = storage.saved_design_path("victim.json")
    transaction_dir = storage.delete_staging_dir / "committed"
    transaction_dir.mkdir(parents=True)
    staged = transaction_dir / "0-victim.json"
    os.replace(original, staged)
    (transaction_dir / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [{"original": storage.relative_path(original), "staged": staged.name}],
            }
        ),
        encoding="utf-8",
    )
    (transaction_dir / "COMMITTED").write_text("committed\n", encoding="utf-8")

    recovered = JsonCourseStorage(tmp_path)

    assert recovered.list_saved_designs() == []
    assert not transaction_dir.exists()


def test_delete_reports_pending_cleanup_and_next_adapter_retries(tmp_path, monkeypatch) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da eliminare"})
    real_rmtree = shutil.rmtree
    failed_once = False

    def fail_first_cleanup(path, *args, **kwargs):
        nonlocal failed_once
        if not failed_once and Path(path).parent == storage.delete_staging_dir:
            failed_once = True
            raise PermissionError("cleanup bloccato")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr("scripts.thebitlab_storage.shutil.rmtree", fail_first_cleanup)
    result = storage.delete_saved_design("victim.json")

    assert result["cleanup_pending"] is True
    assert any(storage.delete_staging_dir.iterdir())

    monkeypatch.setattr("scripts.thebitlab_storage.shutil.rmtree", real_rmtree)
    recovered = JsonCourseStorage(tmp_path)
    assert recovered.list_saved_designs() == []
    assert list(recovered.delete_staging_dir.iterdir()) == []


def test_partial_committed_cleanup_never_restores_deleted_design(tmp_path, monkeypatch) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da eliminare"})
    real_rmtree = shutil.rmtree
    failed_once = False

    def partially_clean_then_fail(path, *args, **kwargs):
        nonlocal failed_once
        transaction_dir = Path(path)
        if not failed_once and transaction_dir.name.endswith(".committed"):
            failed_once = True
            (transaction_dir / "manifest.json").unlink()
            raise PermissionError("cleanup interrotto")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr("scripts.thebitlab_storage.shutil.rmtree", partially_clean_then_fail)
    result = storage.delete_saved_design("victim.json")

    assert result["cleanup_pending"] is True
    assert storage.list_saved_designs() == []
    assert any(path.name.endswith(".committed") for path in storage.delete_staging_dir.iterdir())

    monkeypatch.setattr("scripts.thebitlab_storage.shutil.rmtree", real_rmtree)
    recovered = JsonCourseStorage(tmp_path)
    assert recovered.list_saved_designs() == []
    assert list(recovered.delete_staging_dir.iterdir()) == []


def test_delete_syncs_staged_entry_before_source_removal(tmp_path, monkeypatch) -> None:
    storage = JsonCourseStorage(tmp_path)
    storage.write_saved_design("victim.json", {"title": "Da eliminare"})
    synced: list[Path] = []
    monkeypatch.setattr("scripts.thebitlab_storage.sync_directory", lambda path: synced.append(path))

    storage.delete_saved_design("victim.json")

    source_sync_index = synced.index(storage.course_designs_dir)
    staged_directory = synced[source_sync_index - 1]
    assert staged_directory.parent == storage.delete_staging_dir
    assert staged_directory.name.endswith(".pending")


def test_read_json_rejects_non_object_payload(tmp_path) -> None:
    storage = JsonCourseStorage(tmp_path)
    path = tmp_path / "list.json"
    path.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(ValueError):
        storage.read_json(path)


def test_assignment_reports_are_listed_with_counts(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "title": "Activity demo",
                "class_id": "4A-INF",
                "class_label": "4A INF",
                "github_team": "team-4a-inf",
                "students": [
                    {"student": "rossi-mario", "submitted": True, "late": True},
                    {"student": "bianchi-luca", "submitted": "false", "late": "true"},
                    {"student": "verdi-anna", "submitted": "yes", "late": "false"},
                ],
            }
        ),
        encoding="utf-8",
    )

    reports = storage.list_assignment_reports()

    assert reports[0]["name"] == "demo/activity.json"
    assert reports[0]["path"] == "teacher-reports/demo/activity.json"
    assert reports[0]["class_id"] == "4A-INF"
    assert reports[0]["students"] == 3
    assert reports[0]["submitted"] == 2
    assert reports[0]["not_submitted"] == 1
    assert reports[0]["late"] == 1
    assert reports[0]["updated_at"]


def test_read_assignment_report_normalizes_student_booleans(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "submitted": "false",
                        "late": "0",
                        "submission": {"late": "yes"},
                        "grading": {"passed": "false"},
                        "ai_feedback": {"approved_by_teacher": "si"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    student = storage.read_assignment_report("activity.json")["students"][0]

    assert student["submitted"] is False
    assert student["late"] is False
    assert student["submission"]["late"] is True
    assert student["grading"]["passed"] is False
    assert student["ai_feedback"]["approved_by_teacher"] is True


def test_ai_feedback_demo_report_exposes_teacher_review_states() -> None:
    root = Path(__file__).resolve().parents[1]
    storage = JsonAssignmentStorage(root, root / "teacher-reports", [])

    report = storage.read_assignment_report("demo/ai-feedback-states.json")
    statuses = {student["student"]: student["ai_feedback"]["status"] for student in report["students"]}
    approvals = {student["student"]: student["ai_feedback"]["approved_by_teacher"] for student in report["students"]}

    assert report["activity_id"] == "demo-ai-feedback-states"
    assert statuses == {
        "rossi-mario": "draft",
        "bianchi-luca": "approved",
        "verdi-anna": "rejected",
        "neri-giulia": "not_generated",
    }
    assert approvals == {
        "rossi-mario": False,
        "bianchi-luca": True,
        "verdi-anna": False,
        "neri-giulia": False,
    }


def test_assignment_report_rejects_unsafe_or_invalid_reports(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [])
    reports_dir = tmp_path / "teacher-reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "invalid.json").write_text(json.dumps({"students": {}}), encoding="utf-8")

    with pytest.raises(ValueError):
        storage.safe_teacher_report_path("../unsafe.json")

    with pytest.raises(ValueError, match="students"):
        storage.read_assignment_report("invalid.json")


def test_list_activities_skips_invalid_json_and_deduplicates_paths(tmp_path) -> None:
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    valid = activities_dir / "activity.json"
    valid.write_text(
        json.dumps(
            {
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "linguaggio": "python",
                "contesto": {"classe": "3A-TPSI", "team_github": "team-3a-tpsi", "source_name": "main.py"},
            }
        ),
        encoding="utf-8",
    )
    (activities_dir / "broken.json").write_text("{", encoding="utf-8")
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [activities_dir, activities_dir])

    assert storage.list_activities() == [
        {
            "id": "python-base-somma-001",
            "title": "Somma in Python",
            "kind": "compito-casa",
            "student_support_mode": "",
            "class_id": "3A-TPSI",
            "class_label": "3A-TPSI",
            "github_team": "team-3a-tpsi",
            "language": "python",
            "source_name": "main.py",
            "topics": [],
            "path": "activities/activity.json",
        }
    ]


def test_save_activity_persists_valid_draft_and_lists_it(tmp_path) -> None:
    storage = JsonAssignmentStorage(tmp_path, tmp_path / "teacher-reports", [tmp_path / "activities"])
    activity = {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "titolo": "Somma in Python",
        "tipo": "compito-casa",
        "difficolta": "B",
        "argomenti": ["variabili", "operatori"],
        "consegna": "Scrivi un programma che somma due numeri.",
        "correzione": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": True,
        },
        "metriche": {
            "tempo_stimato_minuti": 30,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
        "contesto": {"classe": "3A-TPSI", "team_github": "team-3a"},
    }

    saved = storage.save_activity(activity)

    assert saved["path"] == "activities/drafts/python-base-somma-001.json"
    assert saved["topics"] == ["variabili", "operatori"]
    assert saved["source_name"] == ""
    assert (tmp_path / "activities" / "drafts" / "python-base-somma-001.json").is_file()
    assert storage.list_activities() == [saved]
    with pytest.raises(ValueError, match="gia esistente"):
        storage.save_activity(activity)


def test_class_rosters_are_normalized_and_listed(tmp_path) -> None:
    storage = JsonClassRosterStorage(tmp_path)
    classes_dir = tmp_path / "doc" / "classes"
    classes_dir.mkdir(parents=True)
    (classes_dir / "3a.json").write_text(
        json.dumps(
            {
                "class_id": "3A-TPSI",
                "class_label": "3A TPSI",
                "year": "2026-2027",
                "github_team": "team-3a-tpsi",
                "students": [
                    {
                        "student_id": "rossi-mario",
                        "student": "Rossi Mario",
                        "repo": "TheBitPoets/rossi-mario",
                        "local_path": r"studenti\rossi-mario",
                    },
                    {"id": "bianchi-luca", "display_name": "Bianchi Luca", "active": "false", "repo_path": "studenti/bianchi-luca"},
                ],
            }
        ),
        encoding="utf-8",
    )

    rosters = storage.list_class_rosters()
    roster = storage.read_class_roster("3a.json")

    assert rosters[0]["name"] == "3a.json"
    assert rosters[0]["path"] == "doc/classes/3a.json"
    assert rosters[0]["id"] == "3A-TPSI"
    assert rosters[0]["label"] == "3A TPSI"
    assert rosters[0]["students"] == 2
    assert roster == {
        "schema_version": "1.0",
        "id": "3A-TPSI",
        "label": "3A TPSI",
        "school_year": "2026-2027",
        "provider": "local",
        "provider_ref": "",
        "github_team": "team-3a-tpsi",
        "students": [
            {
                "id": "bianchi-luca",
                "display_name": "Bianchi Luca",
                "email": "",
                "github_username": "",
                "repo_ref": "",
                "local_path": "",
                "repo_path": "studenti/bianchi-luca",
                "path": "",
                "active": False,
                "provider_accounts": [],
            },
            {
                "id": "rossi-mario",
                "display_name": "Rossi Mario",
                "email": "",
                "github_username": "",
                "repo_ref": "TheBitPoets/rossi-mario",
                "local_path": "studenti/rossi-mario",
                "repo_path": "",
                "path": "",
                "active": True,
                "provider_accounts": [],
            },
        ],
    }


def test_class_roster_rejects_unsafe_name_and_invalid_shape(tmp_path) -> None:
    storage = JsonClassRosterStorage(tmp_path)
    classes_dir = tmp_path / "doc" / "classes"
    classes_dir.mkdir(parents=True)
    (classes_dir / "invalid.json").write_text(json.dumps({"id": "3A", "students": {}}), encoding="utf-8")
    (classes_dir / "invalid-student.json").write_text(
        json.dumps({"id": "3A", "students": ["rossi-mario"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        storage.safe_roster_name("../3a.json")

    with pytest.raises(ValueError, match="students"):
        storage.read_class_roster("invalid.json")
    with pytest.raises(ValueError, match="ogni studente"):
        storage.read_class_roster("invalid-student.json")
