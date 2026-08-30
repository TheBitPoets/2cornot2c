from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.thebitlab_technical_services import (
    DockerGradeActivityExecutionService,
    ExecutionRequest,
    RunnerTestResult,
)


def p3_activity() -> dict:
    return {
        "id": "python-p3-dispatch-001",
        "language": "python",
        "object_tests": [
            {
                "profile": "python-object-v1",
                "name": "saldo dopo deposito",
                "class": "Conto",
                "construct": {"args": ["Anna", 100]},
                "steps": [
                    {"call": "deposita", "args": [20], "expected_return": None},
                    {"observe": "saldo", "expected": 120},
                ],
            }
        ],
    }


def request(
    activity_path: Path,
    source_path: Path,
    *,
    language: str = "python",
) -> ExecutionRequest:
    return ExecutionRequest(
        activity_id="python-p3-dispatch-001",
        student_id="student",
        files={"main.py": str(source_path)},
        language=language,
        timeout_seconds=6,
        metadata={
            "activity_path": activity_path,
            "source_path": source_path,
            "docker_image": "p3-candidate:test",
        },
    )


def test_docker_service_dispatches_object_tests_to_p3_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(json.dumps(p3_activity()), encoding="utf-8")
    source_path.write_text(
        "class Conto:\n"
        "    def __init__(self, titolare, saldo):\n"
        "        self.titolare = titolare\n"
        "        self.saldo = saldo\n",
        encoding="utf-8",
    )

    from scripts import (
        grade_activity,
        grade_python_filesystem_activity,
        grade_python_function_activity,
        grade_python_object_activity,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("solo il grader P3 deve essere eseguito")

    def fake_p3(**kwargs):
        assert kwargs["activity_path"] == activity_path
        assert kwargs["source_path"] == source_path
        assert kwargs["image"] == "p3-candidate:test"
        assert kwargs["timeout_seconds"] == 6
        assert kwargs["activity_root"] == tmp_path
        assert kwargs["source_root"] == tmp_path
        return {
            "activity_id": "python-p3-dispatch-001",
            "language": "python",
            "profile": "python-object-v1",
            "passed": True,
            "status": "passed",
            "tests": [
                {
                    "name": "saldo dopo deposito",
                    "passed": True,
                    "status": "passed",
                    "worker_status": "completed",
                }
            ],
            "summary": {"passed": 1, "total": 1},
        }

    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", forbidden)
    monkeypatch.setattr(grade_python_function_activity, "grade_in_docker", forbidden)
    monkeypatch.setattr(grade_python_filesystem_activity, "grade_in_docker", forbidden)
    monkeypatch.setattr(grade_python_object_activity, "grade_in_docker", fake_p3)

    result = DockerGradeActivityExecutionService().run(
        request(activity_path, source_path)
    )

    assert result.status == "passed"
    assert result.tests == [RunnerTestResult("saldo dopo deposito", True)]
    assert result.metadata["backend"] == "docker"
    assert result.metadata["docker_image"] == "p3-candidate:test"
    assert result.metadata["grading_profile"] == "python-object-v1"
    assert result.metadata["runner_report"]["profile"] == "python-object-v1"


def test_docker_service_rejects_object_profile_for_non_python_request(
    tmp_path: Path,
) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.c"
    activity_path.write_text(json.dumps(p3_activity()), encoding="utf-8")
    source_path.write_text("int main(void){return 0;}\n", encoding="utf-8")

    result = DockerGradeActivityExecutionService().run(
        request(activity_path, source_path, language="c")
    )

    assert result.status == "invalid_payload"
    assert "object_tests" in result.detail
    assert "Python" in result.detail


@pytest.mark.parametrize("other_field", ["function_tests", "filesystem_tests"])
def test_docker_service_rejects_p3_mixed_with_another_python_profile(
    monkeypatch,
    tmp_path: Path,
    other_field: str,
) -> None:
    activity = p3_activity()
    if other_field == "function_tests":
        activity[other_field] = [
            {
                "profile": "python-function-v1",
                "function": "f",
                "expected_return": 1,
            }
        ]
    else:
        activity[other_field] = [
            {
                "profile": "python-filesystem-v1",
                "expected_artifacts": [
                    {"path": "out.txt", "text": "ok\n", "encoding": "utf-8"}
                ],
            }
        ]

    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(json.dumps(activity), encoding="utf-8")
    source_path.write_text("pass\n", encoding="utf-8")

    from scripts import (
        grade_activity,
        grade_python_filesystem_activity,
        grade_python_function_activity,
        grade_python_object_activity,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("nessun grader deve partire per Activity ambigua")

    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", forbidden)
    monkeypatch.setattr(grade_python_function_activity, "grade_in_docker", forbidden)
    monkeypatch.setattr(grade_python_filesystem_activity, "grade_in_docker", forbidden)
    monkeypatch.setattr(grade_python_object_activity, "grade_in_docker", forbidden)

    result = DockerGradeActivityExecutionService().run(
        request(activity_path, source_path)
    )

    assert result.status == "invalid_payload"
    assert "profili Python incompatibili" in result.detail
    assert "object_tests" in result.detail
    assert other_field in result.detail


def test_docker_service_rejects_all_three_python_profiles_before_execution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    activity = p3_activity()
    activity["function_tests"] = [
        {
            "profile": "python-function-v1",
            "function": "f",
            "expected_return": 1,
        }
    ]
    activity["filesystem_tests"] = [
        {
            "profile": "python-filesystem-v1",
            "expected_artifacts": [
                {"path": "out.txt", "text": "ok\n", "encoding": "utf-8"}
            ],
        }
    ]
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(json.dumps(activity), encoding="utf-8")
    source_path.write_text("pass\n", encoding="utf-8")

    from scripts import grade_activity

    monkeypatch.setattr(
        grade_activity,
        "grade_activity_in_docker",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("legacy non deve partire")
        ),
    )

    result = DockerGradeActivityExecutionService().run(
        request(activity_path, source_path)
    )

    assert result.status == "invalid_payload"
    for field in ("function_tests", "filesystem_tests", "object_tests"):
        assert field in result.detail
