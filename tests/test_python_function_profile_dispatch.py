from __future__ import annotations

import json
from pathlib import Path

from scripts.thebitlab_technical_services import (
    DockerGradeActivityExecutionService,
    ExecutionRequest,
    RunnerTestResult,
)


def _request(activity_path: Path, source_path: Path, *, language: str = "python") -> ExecutionRequest:
    return ExecutionRequest(
        activity_id="python-p2-dispatch",
        student_id="rossi-mario",
        files={source_path.name: str(source_path)},
        language=language,
        timeout_seconds=7,
        metadata={
            "activity_path": activity_path,
            "source_path": source_path,
            "docker_image": "p2-candidate:test",
        },
    )


def test_docker_service_dispatches_function_tests_to_p2_only(monkeypatch, tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(
        json.dumps(
            {
                "id": "python-p2-dispatch",
                "language": "python",
                "function_tests": [
                    {
                        "profile": "python-function-v1",
                        "function": "doppio",
                        "args": [3],
                        "expected_return": 6,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text("def doppio(x):\n    return x * 2\n", encoding="utf-8")

    from scripts import grade_activity, grade_python_function_activity

    def legacy_must_not_run(*args, **kwargs):
        raise AssertionError("legacy Docker grader must not run for P2")

    def fake_p2(*, activity_path, source_path, image, timeout_seconds, activity_root=None, source_root=None):
        assert activity_path == tmp_path / "activity.json"
        assert source_path == tmp_path / "main.py"
        assert image == "p2-candidate:test"
        assert timeout_seconds == 7
        assert activity_root is None
        assert source_root is None
        return {
            "passed": True,
            "status": "passed",
            "activity_id": "python-p2-dispatch",
            "language": "python",
            "profile": "python-function-v1",
            "source": str(source_path),
            "tests": [
                {
                    "name": "doppio",
                    "passed": True,
                    "status": "passed",
                    "worker_status": "returned",
                }
            ],
            "summary": {"passed": 1, "total": 1},
        }

    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", legacy_must_not_run)
    monkeypatch.setattr(grade_python_function_activity, "grade_in_docker", fake_p2)

    result = DockerGradeActivityExecutionService().run(_request(activity_path, source_path))

    assert result.status == "passed"
    assert result.tests == [RunnerTestResult("doppio", True)]
    assert result.metadata["backend"] == "docker"
    assert result.metadata["docker_image"] == "p2-candidate:test"
    assert result.metadata["grading_profile"] == "python-function-v1"
    assert result.metadata["runner_report"]["profile"] == "python-function-v1"


def test_docker_service_keeps_legacy_path_without_function_tests(monkeypatch, tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(
        json.dumps(
            {
                "id": "python-p1-dispatch",
                "language": "python",
                "test_cases": [{"stdin": "2\n", "expected_stdout": "4\n"}],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text("print(int(input()) * 2)\n", encoding="utf-8")

    from scripts import grade_activity, grade_python_function_activity

    def p2_must_not_run(*args, **kwargs):
        raise AssertionError("P2 grader must not run for legacy Activity")

    def fake_legacy(activity, source, *, timeout_seconds, language, image):
        assert activity == activity_path
        assert source == source_path
        assert timeout_seconds == 7
        assert language == "python"
        assert image == "p2-candidate:test"
        return (
            {
                "passed": True,
                "status": "passed",
                "activity_id": "python-p1-dispatch",
                "language": "python",
                "source": str(source_path),
                "tests": [{"name": "base", "passed": True, "status": "passed"}],
                "summary": {"passed": 1, "total": 1},
            },
            "",
        )

    monkeypatch.setattr(grade_python_function_activity, "grade_in_docker", p2_must_not_run)
    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", fake_legacy)

    result = DockerGradeActivityExecutionService().run(_request(activity_path, source_path))

    assert result.status == "passed"
    assert result.tests == [RunnerTestResult("base", True)]
    assert result.metadata["grading_profile"] == "legacy"


def test_docker_service_rejects_function_profile_for_non_python_request(monkeypatch, tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.c"
    activity_path.write_text(
        json.dumps(
            {
                "id": "invalid-p2-language",
                "language": "c",
                "function_tests": [
                    {
                        "profile": "python-function-v1",
                        "function": "f",
                        "expected_return": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text("int main(void){return 0;}\n", encoding="utf-8")

    from scripts import grade_activity, grade_python_function_activity

    monkeypatch.setattr(
        grade_activity,
        "grade_activity_in_docker",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("legacy must not run")),
    )
    monkeypatch.setattr(
        grade_python_function_activity,
        "grade_in_docker",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("P2 must not run")),
    )

    result = DockerGradeActivityExecutionService().run(
        _request(activity_path, source_path, language="c")
    )

    assert result.status == "invalid_payload"
    assert "function_tests" in result.detail
    assert "Python" in result.detail
