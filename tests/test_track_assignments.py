from __future__ import annotations

import json

from scripts import track_assignments


def activity() -> dict:
    """Return a minimal valid activity for tracking tests."""
    return {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "titolo": "Somma in Python",
        "tipo": "compito-casa",
        "difficolta": "B",
        "argomenti": ["variabili", "input-output"],
        "linguaggio": "python",
        "consegna": "Scrivi un programma Python che stampa una somma.",
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


def write_activity(tmp_path):
    """Write a valid activity JSON and return its path."""
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(activity()), encoding="utf-8")
    return path


def target(tmp_path, name: str) -> track_assignments.TrackingTarget:
    """Return a tracking target rooted in tmp_path."""
    root = tmp_path / name
    return track_assignments.TrackingTarget(student=name, repo=f"TheBitPoets/{name}", path=root)


def write_report(root, submitted_at: str, passed: bool = True) -> None:
    """Write a local grading report in the default report location."""
    report_path = root / "reports" / "python-base-somma-001" / "latest.json"
    source_path = root / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "activity_id": "python-base-somma-001",
                "source": str(source_path),
                "submitted_at": submitted_at,
                "commit": "abc1234",
                "summary": {
                    "passed": 2 if passed else 1,
                    "total": 2,
                },
            }
        ),
        encoding="utf-8",
    )


def test_track_assignments_marks_submitted_on_time(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "submitted_on_time"
    assert row["submitted"] is True
    assert row["late"] is False
    assert row["grading"]["status"] == "graded_passed"
    assert row["grading"]["tests_passed"] == 2
    assert row["ai_feedback"]["status"] == "not_generated"


def test_track_assignments_marks_missing_after_due_date(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "missing"
    assert row["submitted"] is False
    assert row["grading"]["status"] == "not_graded"


def test_track_assignments_marks_submitted_late(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report(student.path, "2026-10-20T08:00:00+02:00", passed=False)

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "submitted_late"
    assert row["late"] is True
    assert row["grading"]["status"] == "graded_failed"


def test_write_tracking_index_creates_parent_directories(tmp_path) -> None:
    output = tmp_path / "teacher-reports" / "3A" / "index.json"
    index = {"activity_id": "python-base-somma-001", "students": []}

    track_assignments.write_tracking_index(index, output)

    assert json.loads(output.read_text(encoding="utf-8")) == index
