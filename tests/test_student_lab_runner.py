from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from scripts import assignment_records, student_lab_runner, student_lab_service


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


def run_store_and_reload_script_assignment(
    root,
    *,
    activity_id: str,
    language: str,
    source_name: str,
    source: str,
    test_cases: list[dict],
) -> tuple[dict, dict]:
    """Run a script assignment and reload its grading through the lab service."""

    activity_path = write_activity(
        root,
        activity_id=activity_id,
        language=language,
        source_name=source_name,
        test_cases=test_cases,
    )
    activity_file = root / activity_path
    activity_payload = json.loads(activity_file.read_text(encoding="utf-8"))
    activity_payload.pop("source_name")
    activity_file.write_text(json.dumps(activity_payload), encoding="utf-8")
    write_assignment(root, activity_path, activity_id=activity_id)
    workspace = (
        root
        / "examples"
        / "assignment_tracking"
        / "student_repos"
        / "rossi-mario"
        / "assignments"
        / activity_id
    )
    workspace.mkdir(parents=True)
    (workspace / source_name).write_text(source, encoding="utf-8")

    assignment = student_lab_runner.load_student_assignment(
        root=root,
        student_id="rossi-mario",
        activity_id=activity_id,
        now="2026-10-18T12:00:00+02:00",
    )
    report = student_lab_runner.run_local_assignment(assignment, root=root)
    student_lab_runner.write_student_report(root, assignment, report)
    payload = student_lab_service.student_lab_payload(
        root=root,
        student_id="rossi-mario",
        now="2026-10-20T12:00:00+02:00",
    )
    assignment_payload = next(
        item for item in payload["assignments"] if item["activity_id"] == activity_id
    )
    return report, assignment_payload


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
    assert report["tests"] == [
        {
            "name": "tests/test_main.py::test_somma",
            "passed": True,
            "status": "passed",
        }
    ]


def test_write_student_report_persists_latest_json_and_service_reads_it(tmp_path) -> None:
    write_assignment(tmp_path, write_activity(tmp_path))
    write_python_workspace(
        tmp_path,
        source="def somma(a, b):\n    return a + b\n",
        test_source="from main import somma\n\ndef test_somma():\n    assert somma(2, 3) == 5\n",
    )

    assignment = student_lab_runner.load_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
        now="2026-10-18T12:00:00+02:00",
    )
    report = student_lab_runner.run_local_assignment(assignment, root=tmp_path)
    report_path = student_lab_runner.write_student_report(tmp_path, assignment, report)

    stored = json.loads(report_path.read_text(encoding="utf-8"))
    assert stored["activity_id"] == "python-base-somma-001"
    assert stored["submitted_at"] == report["generated_at"]
    assert stored["source"] == "assignments/python-base-somma-001/main.py"

    payload = student_lab_service.student_lab_payload(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-20T12:00:00+02:00",
    )

    assignment_payload = payload["assignments"][0]
    assert assignment_payload["status"] == "submitted"
    assert assignment_payload["submitted"] is True
    assert assignment_payload["report"]["exists"] is True
    assert assignment_payload["report"]["submitted_at"] == report["generated_at"]
    assert assignment_payload["grading"]["status"] == "graded_passed"
    assert assignment_payload["grading"]["tests_passed"] == 1
    assert assignment_payload["grading"]["tests_total"] == 1


@pytest.mark.skipif(shutil.which("node") is None, reason="node non disponibile nell'ambiente di test")
def test_node_assignment_flows_from_runner_to_service_grading(tmp_path) -> None:
    report, assignment_payload = run_store_and_reload_script_assignment(
        tmp_path,
        activity_id="javascript-incremento-001",
        language="javascript",
        source_name="main.js",
        source=(
            "let value = '';\n"
            "process.stdin.on('data', chunk => value += chunk)\n"
            "  .on('end', () => console.log(Number(value) + 1));\n"
        ),
        test_cases=[
            {
                "name": "incremento",
                "stdin": "4\n",
                "expected_stdout": "5\n",
            }
        ],
    )

    assert report["backend"] == "local"
    assert report["language"] == "javascript"
    assert report["status"] == "passed"
    assert report["summary"] == {"passed": 1, "total": 1}
    assert assignment_payload["report"]["exists"] is True
    assert assignment_payload["grading"]["status"] == "graded_passed"
    assert assignment_payload["grading"]["tests_passed"] == 1
    assert assignment_payload["grading"]["tests_total"] == 1


def test_sql_assignment_flows_from_runner_to_service_grading(tmp_path) -> None:
    report, assignment_payload = run_store_and_reload_script_assignment(
        tmp_path,
        activity_id="sql-studenti-001",
        language="sql",
        source_name="main.sql",
        source=(
            "CREATE TABLE studenti (nome TEXT, voto INTEGER);\n"
            "INSERT INTO studenti VALUES ('Ada', 9), ('Linus', 8);\n"
            "SELECT nome, voto FROM studenti ORDER BY nome;\n"
        ),
        test_cases=[
            {
                "name": "elenco studenti",
                "expected_stdout": "Ada|9\nLinus|8\n",
            }
        ],
    )

    assert report["backend"] == "local"
    assert report["language"] == "sql"
    assert report["status"] == "passed"
    assert report["summary"] == {"passed": 1, "total": 1}
    assert report["tests"][0]["command"][0] == "python-stdlib"
    assert assignment_payload["report"]["exists"] is True
    assert assignment_payload["grading"]["status"] == "graded_passed"
    assert assignment_payload["grading"]["tests_passed"] == 1
    assert assignment_payload["grading"]["tests_total"] == 1


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
    assert report["tests"][0]["name"] == "tests/test_main.py::test_somma"
    assert report["tests"][0]["passed"] is False
    assert report["tests"][0]["status"] == "failed"
    assert "assert -1 == 5" in report["tests"][0]["message"]
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
    activity_path = write_activity(tmp_path, language="html", source_name="index.html")
    write_assignment(tmp_path, activity_path)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    workspace.mkdir(parents=True)
    (workspace / "index.html").write_text("<p>demo</p>", encoding="utf-8")

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
    )

    assert report["status"] == "unsupported-language"
    assert report["language"] == "html"


def test_run_local_assignment_rejects_source_name_outside_workspace(tmp_path) -> None:
    activity_path = write_activity(tmp_path, source_name="../main.py")
    write_assignment(tmp_path, activity_path)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    workspace.mkdir(parents=True)

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
    )

    assert report["status"] == "invalid-source-name"
    assert report["passed"] is False


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


def test_run_local_assignment_adds_c_failure_message(monkeypatch, tmp_path) -> None:
    activity_id = "c-base-somma-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, language="c", source_name="main.c")
    write_assignment(tmp_path, activity_path, activity_id=activity_id)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / activity_id
    workspace.mkdir(parents=True)
    (workspace / "main.c").write_text("int main(void){ return 0; }\n", encoding="utf-8")

    def failed_test(activity, source, **kwargs):
        return {
            "passed": False,
            "status": "failed",
            "activity_id": activity["id"],
            "language": "c",
            "source": str(source),
            "tests": [
                {
                    "name": "somma_positivi",
                    "passed": False,
                    "status": "failed",
                    "expected_stdout": "5\n",
                    "stdout": "4\n",
                    "stderr": "",
                }
            ],
            "summary": {"passed": 0, "total": 1},
        }

    monkeypatch.setattr(student_lab_runner.grade_activity, "grade_activity", failed_test)

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
    )

    assert report["status"] == "failed"
    assert report["tests"][0]["message"] == "Output atteso: 5; output ottenuto: 4"


def test_run_docker_assignment_wraps_container_report(monkeypatch, tmp_path) -> None:
    activity_id = "c-base-somma-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, language="c", source_name="main.c")
    write_assignment(tmp_path, activity_path, activity_id=activity_id)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / activity_id
    workspace.mkdir(parents=True)
    (workspace / "main.c").write_text("int main(void){ return 0; }\n", encoding="utf-8")

    class Result:
        returncode = 0
        stdout = json.dumps(
            {
                "passed": True,
                "status": "passed",
                "activity_id": activity_id,
                "language": "c",
                "source": "/workspace/source/main.c",
                "tests": [{"name": "smoke", "passed": True, "status": "passed"}],
                "summary": {"passed": 1, "total": 1},
            }
        )
        stderr = ""

    monkeypatch.setattr(student_lab_runner.subprocess, "run", lambda *args, **kwargs: Result())

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
        backend="docker",
    )

    assert report["backend"] == "docker"
    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["summary"] == {"passed": 1, "total": 1}


def test_run_docker_assignment_adds_c_failure_message(monkeypatch, tmp_path) -> None:
    activity_id = "c-base-somma-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, language="c", source_name="main.c")
    write_assignment(tmp_path, activity_path, activity_id=activity_id)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / activity_id
    workspace.mkdir(parents=True)
    (workspace / "main.c").write_text("int main(void){ return 0; }\n", encoding="utf-8")

    class Result:
        returncode = 0
        stdout = json.dumps(
            {
                "passed": False,
                "status": "failed",
                "activity_id": activity_id,
                "language": "c",
                "source": "/workspace/source/main.c",
                "tests": [
                    {
                        "name": "somma_negativi",
                        "passed": False,
                        "status": "failed",
                        "expected_stdout": "-5\n",
                        "stdout": "5\n",
                    }
                ],
                "summary": {"passed": 0, "total": 1},
            }
        )
        stderr = ""

    monkeypatch.setattr(student_lab_runner.subprocess, "run", lambda *args, **kwargs: Result())

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
        backend="docker",
    )

    assert report["backend"] == "docker"
    assert report["status"] == "failed"
    assert report["tests"][0]["message"] == "Output atteso: -5; output ottenuto: 5"


def test_run_docker_assignment_reports_missing_docker(monkeypatch, tmp_path) -> None:
    activity_id = "c-base-somma-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, language="c", source_name="main.c")
    write_assignment(tmp_path, activity_path, activity_id=activity_id)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / activity_id
    workspace.mkdir(parents=True)
    (workspace / "main.c").write_text("int main(void){ return 0; }\n", encoding="utf-8")

    def missing_docker(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(student_lab_runner.subprocess, "run", missing_docker)

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
        backend="docker",
    )

    assert report["backend"] == "docker"
    assert report["status"] == "docker-not-found"
    assert "Docker non trovato" in report["error"]


def test_run_docker_assignment_rejects_success_report_on_container_error(monkeypatch, tmp_path) -> None:
    activity_id = "c-base-somma-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, language="c", source_name="main.c")
    write_assignment(tmp_path, activity_path, activity_id=activity_id)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / activity_id
    workspace.mkdir(parents=True)
    (workspace / "main.c").write_text("int main(void){ return 0; }\n", encoding="utf-8")

    class Result:
        returncode = 1
        stdout = json.dumps({"passed": True, "status": "passed"})
        stderr = "errore container"

    monkeypatch.setattr(student_lab_runner.subprocess, "run", lambda *args, **kwargs: Result())

    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
        backend="docker",
    )

    assert report["backend"] == "docker"
    assert report["status"] == "docker-inconsistent-report"
    assert report["passed"] is False


def test_run_docker_assignment_supports_python(monkeypatch, tmp_path) -> None:
    activity_path = write_activity(tmp_path, language="python", source_name="main.py")
    write_assignment(tmp_path, activity_path)
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    workspace.mkdir(parents=True)
    (workspace / "main.py").write_text("print(1)\n", encoding="utf-8")

    class Result:
        returncode = 0
        stdout = json.dumps({
            "passed": True,
            "status": "passed",
            "language": "python",
            "tests": [{"name": "output", "passed": True, "status": "passed"}],
            "summary": {"passed": 1, "total": 1},
        })
        stderr = ""

    monkeypatch.setattr(student_lab_runner.subprocess, "run", lambda *args, **kwargs: Result())
    report = student_lab_runner.run_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id="python-base-somma-001",
        backend="docker",
    )

    assert report["backend"] == "docker"
    assert report["status"] == "passed"
    assert report["language"] == "python"


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
