from __future__ import annotations

import json
import subprocess

from scripts import assignment_records, student_lab_runner


def write_activity(root, activity_id: str = "python-base-somma-001", **overrides) -> str:
    """Write a minimal activity used by runner tests."""

    payload = {
        "schema_version": "1.0",
        "id": activity_id,
        "title": "Somma in Python",
        "kind": "laboratorio",
        "difficulty": "B",
        "topics": ["variabili", "input-output"],
        "language": "python",
        "source_name": "main.py",
        "instructions": "Scrivi una funzione somma.",
        "grading_policy": {
            "compila": True,
            "test": True,
            "sandbox": False,
            "ai_feedback": False,
        },
    }
    payload.update(overrides)
    path = root / "activities" / f"{activity_id}.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return f"activities/{activity_id}.json"


def write_assignment(root, activity_path: str, activity_id: str = "python-base-somma-001") -> dict:
    """Write an assignment visible to rossi-mario."""

    assignment = assignment_records.build_assignment_record(
        activity_id=activity_id,
        activity_path=activity_path,
        target_type="student",
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[
            {
                "student_id": "rossi-mario",
                "display_name": "Rossi Mario",
                "path": "examples/assignment_tracking/student_repos/rossi-mario",
            }
        ],
    )
    storage = assignment_records.JsonAssignmentRecordStorage(root)
    storage.write_assignment(assignment)
    return assignment


def write_python_workspace(root, *, source: str, test_source: str) -> None:
    """Write a Python student workspace with pytest tests."""

    workspace = root / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    tests = workspace / "tests"
    tests.mkdir(parents=True)
    (workspace / "main.py").write_text(source, encoding="utf-8")
    (tests / "test_main.py").write_text(test_source, encoding="utf-8")


def test_run_student_assignment_passes_python_pytest(tmp_path) -> None:
    write_assignment(tmp_path, write_activity(tmp_path))
    write_python_workspace(
        tmp_path,
        source="def somma(a, b):\n    return a + b\n",
        test_source="from main import somma\n\ndef test_somma():\n    assert somma(2, 3) == 5\n",
    )

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
        now="2026-10-18T12:00:00+02:00",
    )

    assert report["schema_version"] == "student_lab_run.v1"
    assert report["backend"] == "local"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["summary"] == {"passed": 1, "total": 1}


def test_run_student_assignment_reports_python_pytest_failure(tmp_path) -> None:
    write_assignment(tmp_path, write_activity(tmp_path))
    write_python_workspace(
        tmp_path,
        source="def somma(a, b):\n    return a - b\n",
        test_source="from main import somma\n\ndef test_somma():\n    assert somma(2, 3) == 5\n",
    )

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
        now="2026-10-18T12:00:00+02:00",
    )

    assert report["status"] == "failed"
    assert report["passed"] is False
    assert report["summary"]["total"] == 1
    assert "FAILED" in report["stdout"]


def test_run_student_assignment_reports_timeout(monkeypatch, tmp_path) -> None:
    write_assignment(tmp_path, write_activity(tmp_path))
    write_python_workspace(
        tmp_path,
        source="def somma(a, b):\n    return a + b\n",
        test_source="from main import somma\n\ndef test_somma():\n    assert somma(2, 3) == 5\n",
    )

    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(student_lab_runner.subprocess, "run", timeout_run)

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
        timeout_seconds=1,
    )

    assert report["status"] == "timeout"
    assert report["passed"] is False
    assert report["returncode"] is None


def test_run_local_assignment_reports_missing_source(tmp_path) -> None:
    write_assignment(tmp_path, write_activity(tmp_path))
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    (workspace / "tests").mkdir(parents=True)

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
    )

    assert report["status"] == "source-not-found"
    assert report["passed"] is False


def test_run_local_assignment_reports_unsupported_language(tmp_path) -> None:
    activity_path = write_activity(tmp_path, language="sql", source_name="query.sql")
    write_assignment(tmp_path, activity_path)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    workspace.mkdir(parents=True)
    (workspace / "query.sql").write_text("select 1;", encoding="utf-8")

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
    )

    assert report["status"] == "unsupported-language"
    assert report["language"] == "sql"


def test_run_local_assignment_wraps_c_compile_error(monkeypatch, tmp_path) -> None:
    activity_id = "c-base-somma-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, language="c", source_name="main.c")
    write_assignment(tmp_path, activity_path, activity_id=activity_id)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / activity_id
    workspace.mkdir(parents=True)
    (workspace / "main.c").write_text("int main(void){ return }\n", encoding="utf-8")

    def compile_error(activity, source, **kwargs):
        return {
            "passed": False,
            "status": "compile-error",
            "activity_id": activity["id"],
            "language": "c",
            "source": str(source),
            "compile": {"stderr": "errore compilazione"},
            "tests": [],
        }

    monkeypatch.setattr(student_lab_runner.grade_activity, "grade_activity", compile_error)

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
    )

    assert report["schema_version"] == "student_lab_run.v1"
    assert report["status"] == "compile-error"
    assert report["passed"] is False
    assert report["summary"] == {"passed": 0, "total": 0}


def test_select_assignment_requires_disambiguation() -> None:
    try:
        student_lab_runner.select_assignment(
            [
                {"assignment_id": "a", "activity_id": "x"},
                {"assignment_id": "b", "activity_id": "y"},
            ]
        )
    except ValueError as error:
        assert "--assignment-id" in str(error)
    else:
        raise AssertionError("select_assignment should require explicit selection")


def test_select_assignment_requires_assignment_id_for_duplicate_activity() -> None:
    try:
        student_lab_runner.select_assignment(
            [
                {"assignment_id": "a", "activity_id": "x"},
                {"assignment_id": "b", "activity_id": "x"},
            ],
            activity_id="x",
        )
    except ValueError as error:
        assert "piu consegne" in str(error)
        assert "--assignment-id" in str(error)
    else:
        raise AssertionError("select_assignment should reject ambiguous activity_id")
