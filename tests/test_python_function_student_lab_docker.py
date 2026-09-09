from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts import student_lab_runner


pytestmark = pytest.mark.skipif(
    os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1",
    reason="set THEBITLAB_RUN_DOCKER_TESTS=1 to exercise the Docker sandbox",
)


def _activity() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-p2-student-lab-001",
        "title": "Return nel percorso Student Lab",
        "titolo": "Return nel percorso Student Lab",
        "kind": "laboratorio",
        "tipo": "laboratorio",
        "language": "python",
        "linguaggio": "python",
        "source_name": "main.py",
        "difficulty": "B",
        "difficolta": "B",
        "topics": ["funzioni", "return"],
        "argomenti": ["funzioni", "return"],
        "instructions": "Implementa le funzioni richieste.",
        "consegna": "Implementa le funzioni richieste.",
        "grading_policy": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
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
                "name": "doppio positivo",
                "function": "doppio",
                "args": [3],
                "expected_return": 6,
            },
            {
                "profile": "python-function-v1",
                "name": "doppio zero",
                "function": "doppio",
                "args": [0],
                "expected_return": 0,
            },
            {
                "profile": "python-function-v1",
                "name": "predicate pari",
                "function": "pari",
                "args": [8],
                "expected_return": True,
            },
        ],
    }


def _assignment() -> dict:
    return {
        "assignment_id": "assignment-python-p2-student-lab",
        "activity_id": "python-p2-student-lab-001",
        "student_id": "rossi-mario",
        "activity": {"path": "activities/python-p2-student-lab-001.json"},
        "workspace": {
            "path": "students/rossi-mario/assignments/python-p2-student-lab-001"
        },
    }


def test_p2_runs_through_normal_student_lab_and_redacts_teacher_oracles(tmp_path: Path) -> None:
    activity_path = tmp_path / "activities" / "python-p2-student-lab-001.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text(json.dumps(_activity()), encoding="utf-8")

    workspace = (
        tmp_path
        / "students"
        / "rossi-mario"
        / "assignments"
        / "python-p2-student-lab-001"
    )
    workspace.mkdir(parents=True)
    (workspace / "main.py").write_text(
        "def doppio(x):\n"
        "    return x * 2\n\n"
        "def pari(n):\n"
        "    return n % 2 == 0\n",
        encoding="utf-8",
    )

    docker_image = os.environ.get("THEBITLAB_P2_DOCKER_IMAGE", "thebitlab-p2-candidate")
    report = student_lab_runner.run_docker_assignment(
        _assignment(),
        root=tmp_path,
        timeout_seconds=3,
        docker_image=docker_image,
    )

    assert report["backend"] == "docker"
    assert report["passed"] is True
    assert report["status"] == "passed"
    assert report["profile"] == "python-function-v1"
    assert report["summary"] == {"passed": 3, "total": 3}
    assert report["tests"] == [
        {"name": "Test 1", "passed": True, "status": "passed"},
        {"name": "Test 2", "passed": True, "status": "passed"},
        {"name": "Test 3", "passed": True, "status": "passed"},
    ]

    serialized = json.dumps(report, ensure_ascii=False).casefold()
    for forbidden in (
        "expected_return",
        "actual_return",
        "worker_status",
        "doppio positivo",
        "doppio zero",
        "predicate pari",
    ):
        assert forbidden not in serialized
