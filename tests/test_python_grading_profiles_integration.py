from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_activity
from scripts.thebitlab_technical_services import (
    DockerGradeActivityExecutionService,
    ExecutionRequest,
)


def base_activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-profiles-ambiguous-001",
        "titolo": "Contratto ambiguo",
        "tipo": "laboratorio",
        "difficolta": "B",
        "argomenti": ["funzioni", "file"],
        "consegna": "Activity usata soltanto per il gate di integrazione.",
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
        "function_tests": [
            {
                "profile": "python-function-v1",
                "function": "f",
                "expected_return": 1,
            }
        ],
        "filesystem_tests": [
            {
                "profile": "python-filesystem-v1",
                "expected_artifacts": [
                    {"path": "out.txt", "text": "1\n", "encoding": "utf-8"}
                ],
            }
        ],
    }


def test_validator_rejects_activity_with_both_p2_and_p4_contracts() -> None:
    errors = validate_activity.validate_activity(base_activity(), "activity.json")

    assert any(
        "function_tests e filesystem_tests non possono coesistere" in error
        for error in errors
    )


def test_validator_rejects_python_profiles_on_non_python_activity() -> None:
    activity = base_activity()
    activity.pop("filesystem_tests")
    activity["language"] = "c"
    activity["linguaggio"] = "c"
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("function_tests" in error and "Python" in error for error in errors)

    activity = base_activity()
    activity.pop("function_tests")
    activity["language"] = "c"
    activity["linguaggio"] = "c"
    errors = validate_activity.validate_activity(activity, "activity.json")
    assert any("filesystem_tests" in error and "Python" in error for error in errors)


def test_docker_dispatcher_rejects_ambiguous_activity_before_running_any_grader(
    monkeypatch,
    tmp_path: Path,
) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.py"
    activity_path.write_text(json.dumps(base_activity()), encoding="utf-8")
    source_path.write_text("def f():\n    return 1\n", encoding="utf-8")

    from scripts import grade_activity

    def forbidden(*args, **kwargs):
        raise AssertionError("nessun grader deve partire per Activity ambigua")

    monkeypatch.setattr(grade_activity, "grade_activity_in_docker", forbidden)
    result = DockerGradeActivityExecutionService().run(
        ExecutionRequest(
            activity_id="python-profiles-ambiguous-001",
            student_id="student",
            files={"main.py": str(source_path)},
            language="python",
            metadata={
                "activity_path": activity_path,
                "source_path": source_path,
                "docker_image": "runner:test",
            },
        )
    )

    assert result.status == "invalid_payload"
    assert "ambigua" in result.detail
    assert "function_tests" in result.detail
    assert "filesystem_tests" in result.detail
