from __future__ import annotations

import json
import os

import pytest

from scripts import assignment_records, student_lab_runner, student_lab_service


pytestmark = pytest.mark.skipif(
    os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1",
    reason="test Docker reale abilitato solo con THEBITLAB_RUN_DOCKER_TESTS=1",
)


@pytest.mark.parametrize(
    ("language", "source_name", "source", "test_case"),
    [
        (
            "nodejs",
            "main.js",
            (
                "let value = '';\n"
                "process.stdin.on('data', chunk => value += chunk)\n"
                "  .on('end', () => console.log(Number(value) + 1));\n"
            ),
            {
                "name": "incremento",
                "stdin": "4\n",
                "expected_stdout": "5\n",
            },
        ),
        (
            "sql",
            "main.sql",
            "SELECT 2 + 3;\n",
            {
                "name": "somma",
                "expected_stdout": "5\n",
            },
        ),
    ],
)
def test_docker_assignment_flows_through_report_and_service(
    tmp_path,
    language,
    source_name,
    source,
    test_case,
) -> None:
    activity_id = f"{language}-docker-e2e-001"
    activity_path = tmp_path / "activities" / f"{activity_id}.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": activity_id,
                "title": f"Demo Docker {language}",
                "kind": "laboratorio",
                "difficulty": "B",
                "topics": ["runner"],
                "language": language,
                "source_name": source_name,
                "instructions": "Completa la consegna.",
                "grading_policy": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "test_cases": [test_case],
            }
        ),
        encoding="utf-8",
    )
    assignment = assignment_records.build_assignment_record(
        activity_id=activity_id,
        activity_path=f"activities/{activity_id}.json",
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
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(assignment)
    workspace = (
        tmp_path
        / "examples"
        / "assignment_tracking"
        / "student_repos"
        / "rossi-mario"
        / "assignments"
        / activity_id
    )
    workspace.mkdir(parents=True)
    (workspace / source_name).write_text(source, encoding="utf-8")

    loaded_assignment = student_lab_runner.load_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
        now="2026-10-18T12:00:00+02:00",
    )
    report = student_lab_runner.run_docker_assignment(
        loaded_assignment,
        root=tmp_path,
    )
    report_path = student_lab_runner.write_student_report(
        tmp_path,
        loaded_assignment,
        report,
    )

    assert report_path.is_file()
    assert report["backend"] == "docker"
    assert report["language"] == language
    assert report["passed"] is True
    assert report["status"] == "passed"
    assert report["summary"] == {"passed": 1, "total": 1}

    payload = student_lab_service.student_lab_payload(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-18T12:00:00+02:00",
    )
    assignment_payload = next(
        item for item in payload["assignments"] if item["activity_id"] == activity_id
    )
    assert assignment_payload["report"]["exists"] is True
    assert assignment_payload["grading"]["status"] == "graded_passed"
    assert assignment_payload["grading"]["tests_passed"] == 1
    assert assignment_payload["grading"]["tests_total"] == 1
