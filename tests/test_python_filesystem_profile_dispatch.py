from __future__ import annotations

import json
from pathlib import Path

from scripts.thebitlab_technical_services import (
    DockerGradeActivityExecutionService,
    ExecutionRequest,
)


def p4_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-p4-dispatch-001",
        "titolo": "P4 dispatch",
        "tipo": "laboratorio",
        "difficolta": "B",
        "argomenti": ["file"],
        "consegna": "Crea risultato.txt.",
        "language": "python",
        "linguaggio": "python",
        "correzione": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 10,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
        "filesystem_tests": [
            {
                "profile": "python-filesystem-v1",
                "name": "output",
                "expected_artifacts": [
                    {"path": "risultato.txt", "text": "ok\n", "encoding": "utf-8"}
                ],
            }
        ],
    }


def request(activity_path: Path, source_path: Path, *, language: str = "python") -> ExecutionRequest:
    return ExecutionRequest(
        activity_id="python-p4-dispatch-001",
        student_id="student",
        files={"main.py": str(source_path)},
        language=language,
        timeout_seconds=4,
        metadata={
            "activity_path": activity_path,
            "source_path": source_path,
            "docker_image": "runner:test",
        },
    )


def test_docker_service_dispatches_filesystem_tests_to_p4(monkeypatch, tmp_path: Path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(json.dumps(p4_activity()), encoding="utf-8")
    source_path.write_text("pass\n", encoding="utf-8")

    from scripts import grade_activity, grade_python_filesystem_activity

    legacy_called = False

    def fake_legacy(*args, **kwargs):
        nonlocal legacy_called
        legacy_called = True
        raise AssertionError("legacy grader must not run for filesystem_tests")

    def fake_p4(**kwargs):
        assert kwargs["activity_path"] == activity_path
        assert kwargs["source_path"] == source_path
        assert kwargs["image"] == "runner:test"
        assert kwargs["timeout_seconds"] == 4
        assert kwargs["activity_root"] == tmp_path
        assert kwargs["source_root"] == tmp_path
        return {
            "activity_id": "python-p4-dispatch-001",
            "language": "python",
            "profile": "python-filesystem-v1",
            "passed": True,
            "status": "passed",
            "tests": [
                {
                    "name": "output",
                    "profile": "python-filesystem-v1",
                    "visibility": "teacher",
                    "passed": True,
                    "status": "passed",
                    "worker_status": "completed",
                    "checks": [],
                }
            ],
            "summary": {"passed": 1, "total": 1},
        }

    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", fake_legacy)
    monkeypatch.setattr(grade_python_filesystem_activity, "grade_in_docker", fake_p4)

    result = DockerGradeActivityExecutionService().run(request(activity_path, source_path))

    assert legacy_called is False
    assert result.status == "passed"
    assert result.metadata["grading_profile"] == "python-filesystem-v1"
    assert result.metadata["docker_image"] == "runner:test"
    assert result.metadata["runner_report"]["profile"] == "python-filesystem-v1"


def test_docker_service_rejects_filesystem_profile_for_non_python_request(tmp_path: Path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(json.dumps(p4_activity()), encoding="utf-8")
    source_path.write_text("pass\n", encoding="utf-8")

    result = DockerGradeActivityExecutionService().run(
        request(activity_path, source_path, language="c")
    )

    assert result.status == "invalid_payload"
    assert "filesystem_tests" in result.detail
    assert "Python" in result.detail


def test_docker_service_keeps_legacy_path_without_filesystem_tests(monkeypatch, tmp_path: Path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    legacy_activity = p4_activity()
    legacy_activity.pop("filesystem_tests")
    activity_path.write_text(json.dumps(legacy_activity), encoding="utf-8")
    source_path.write_text("print('ok')\n", encoding="utf-8")

    from scripts import grade_activity

    def fake_legacy(activity, source, *, timeout_seconds, language, image):
        assert activity == activity_path
        assert source == source_path
        assert timeout_seconds == 4
        assert language == "python"
        assert image == "runner:test"
        return (
            {
                "activity_id": "python-p4-dispatch-001",
                "language": "python",
                "passed": True,
                "status": "passed",
                "tests": [{"name": "legacy", "passed": True, "status": "passed"}],
                "summary": {"passed": 1, "total": 1},
            },
            "",
        )

    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", fake_legacy)
    result = DockerGradeActivityExecutionService().run(request(activity_path, source_path))

    assert result.status == "passed"
    assert result.metadata["grading_profile"] == "legacy"
