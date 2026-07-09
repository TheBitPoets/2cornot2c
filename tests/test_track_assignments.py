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


def write_report_with_activity_id(root, activity_id: str) -> None:
    """Write a local grading report with a configurable activity id."""
    report_path = root / "reports" / "python-base-somma-001" / "latest.json"
    source_path = root / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "passed": True,
                "status": "passed",
                "activity_id": activity_id,
                "source": str(source_path),
                "submitted_at": "2026-10-18T18:22:10+02:00",
                "commit": "abc1234",
            }
        ),
        encoding="utf-8",
    )


def write_report_without_activity_id(root) -> None:
    """Write a local grading report without activity id."""
    report_path = root / "reports" / "python-base-somma-001" / "latest.json"
    source_path = root / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "passed": True,
                "status": "passed",
                "source": str(source_path),
                "submitted_at": "2026-10-18T18:22:10+02:00",
                "commit": "abc1234",
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
    assert row["submission"]["files"][0]["path"].endswith("assignments/python-base-somma-001/main.py")
    assert row["submission"]["files"][0]["role"] == "solution"


def test_track_assignments_records_explicit_class_metadata(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        class_id="3A-TPSI",
        class_label="3A TPSI",
        github_team="team-3a-tpsi",
    )

    assert index["class_id"] == "3A-TPSI"
    assert index["class_label"] == "3A TPSI"
    assert index["github_team"] == "team-3a-tpsi"


def test_track_assignments_uses_activity_context_class_metadata(tmp_path) -> None:
    payload = activity()
    payload["contesto"] = {
        "classe": "4A-INF",
        "team_github": "team-4a-inf",
    }
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")
    student = target(tmp_path, "rossi-mario")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
    )

    assert index["class_id"] == "4A-INF"
    assert index["class_label"] == "4A-INF"
    assert index["github_team"] == "team-4a-inf"


def test_track_assignments_uses_canonical_activity_metadata(tmp_path) -> None:
    payload = {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "title": "Somma canonica",
        "kind": "verifica-pratica",
        "difficulty": "B",
        "topics": ["variabili", "input-output"],
        "language": "python",
        "instructions": "Scrivi un programma Python che stampa una somma.",
        "grading_policy": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "student_support_mode": "senza-aiuto",
        "class_id": "5A-INF",
        "github_team": "team-5a-inf",
    }
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")
    student = target(tmp_path, "rossi-mario")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
    )

    assert index["title"] == "Somma canonica"
    assert index["kind"] == "verifica-pratica"
    assert index["student_support_mode"] == "senza-aiuto"
    assert index["class_id"] == "5A-INF"
    assert index["class_label"] == "5A-INF"
    assert index["github_team"] == "team-5a-inf"


def test_track_assignments_rejects_invalid_canonical_kind(tmp_path) -> None:
    payload = activity()
    payload["tipo"] = "compito-casa"
    payload["kind"] = "compito-classe"
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[],
        )
    except ValueError as error:
        assert "kind non ammesso: compito-classe" in str(error)
    else:
        raise AssertionError("track_assignments should reject invalid canonical kind")


def test_track_assignments_lists_multiple_submission_files(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")
    assignment_dir = student.path / "assignments" / "python-base-somma-001"
    (assignment_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (assignment_dir / "README.md").write_text("# Note\n", encoding="utf-8")
    (assignment_dir / "__pycache__").mkdir()
    (assignment_dir / "__pycache__" / "utils.cpython-310.pyc").write_bytes(b"cache")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    files = index["students"][0]["submission"]["files"]
    paths = [file_entry["path"] for file_entry in files]
    assert any(path.endswith("assignments/python-base-somma-001/main.py") for path in paths)
    assert any(path.endswith("assignments/python-base-somma-001/utils.py") for path in paths)
    assert any(path.endswith("assignments/python-base-somma-001/README.md") for path in paths)
    assert not any("__pycache__" in path for path in paths)


def test_track_assignments_resolves_relative_report_source_from_student_repo(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")
    report_path = student.path / "reports" / "python-base-somma-001" / "latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["source"] = "assignments/python-base-somma-001/main.py"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    files = index["students"][0]["submission"]["files"]
    source_files = [
        file_entry for file_entry in files
        if file_entry["path"].endswith("assignments/python-base-somma-001/main.py")
    ]
    assert len(source_files) == 1
    assert source_files[0]["role"] == "solution"


def test_track_assignments_uses_report_file_manifest_when_available(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")
    report_path = student.path / "reports" / "python-base-somma-001" / "latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["files"] = [
        {"path": "assignments/python-base-somma-001/main.py", "role": "solution"},
        {"path": "assignments/python-base-somma-001/utils.py", "role": "support"},
    ]
    report_path.write_text(json.dumps(report), encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    files = index["students"][0]["submission"]["files"]
    assert [(file_entry["path"], file_entry["role"]) for file_entry in files] == [
        ("assignments/python-base-somma-001/main.py", "solution"),
        ("assignments/python-base-somma-001/utils.py", "support"),
    ]


def test_track_assignments_marks_pending_before_due_date(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
        now="2026-10-18T12:00:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "pending"
    assert row["submitted"] is False
    assert row["late"] is False


def test_track_assignments_does_not_count_scaffold_as_submission(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")
    assignment_dir = student.path / "assignments" / "python-base-somma-001"
    assignment_dir.mkdir(parents=True)
    (assignment_dir / "main.py").write_text("# starter\n", encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
        now="2026-10-18T12:00:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "pending"
    assert row["submitted"] is False
    assert row["submission"]["source_path"] is None


def test_track_assignments_marks_missing_after_due_date(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
        now="2026-10-20T12:00:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "missing"
    assert row["submitted"] is False
    assert row["grading"]["status"] == "not_graded"


def test_track_assignments_rejects_naive_now_when_due_has_timezone(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
            now="2026-10-18T12:00:00",
        )
    except ValueError as error:
        assert "now deve includere il timezone" in str(error)
    else:
        raise AssertionError("track_assignments should reject now without timezone")


def test_track_assignments_rejects_naive_submitted_at_when_due_has_timezone(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report(student.path, "2026-10-20T08:00:00", passed=False)

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
        )
    except ValueError as error:
        assert "submitted_at deve includere il timezone" in str(error)
    else:
        raise AssertionError("track_assignments should reject submitted_at without timezone")


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


def test_track_assignments_rejects_report_for_different_activity(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report_with_activity_id(student.path, "altra-activity")

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
        )
    except ValueError as error:
        assert "Report non coerente" in str(error)
        assert "python-base-somma-001" in str(error)
        assert "altra-activity" in str(error)
    else:
        raise AssertionError("track_assignments should reject reports for a different activity")


def test_track_assignments_rejects_report_without_activity_id(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report_without_activity_id(student.path)

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
        )
    except ValueError as error:
        assert "Report non coerente" in str(error)
        assert "manca activity_id" in str(error)
    else:
        raise AssertionError("track_assignments should reject reports without activity_id")


def test_write_tracking_index_creates_parent_directories(tmp_path) -> None:
    output = tmp_path / "teacher-reports" / "3A" / "index.json"
    index = {"activity_id": "python-base-somma-001", "students": []}

    track_assignments.write_tracking_index(index, output)

    assert json.loads(output.read_text(encoding="utf-8")) == index
