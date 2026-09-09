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
        "id": "python-p3-student-lab-001",
        "title": "Oggetti nel percorso Student Lab",
        "titolo": "Oggetti nel percorso Student Lab",
        "kind": "laboratorio",
        "tipo": "laboratorio",
        "language": "python",
        "linguaggio": "python",
        "source_name": "main.py",
        "difficulty": "B",
        "difficolta": "B",
        "topics": ["classi", "stato", "invarianti"],
        "argomenti": ["classi", "stato", "invarianti"],
        "instructions": "Implementa Conto con stato e invarianti.",
        "consegna": "Implementa Conto con stato e invarianti.",
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
            "tempo_stimato_minuti": 20,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
        "object_tests": [
            {
                "profile": "python-object-v1",
                "name": "deposito modifica lo stato",
                "class": "Conto",
                "construct": {"args": ["Anna", 100]},
                "steps": [
                    {"call": "deposita", "args": [20], "expected_return": None},
                    {"observe": "saldo", "expected": 120},
                    {"call": "saldo_corrente", "expected_return": 120},
                ],
            },
            {
                "profile": "python-object-v1",
                "name": "deposito invalido preserva lo stato",
                "class": "Conto",
                "construct": {"args": ["Anna", 100]},
                "steps": [
                    {
                        "call": "deposita",
                        "args": [-5],
                        "expected_exception": "ValueError",
                    },
                    {"observe": "saldo", "expected": 100},
                ],
            },
            {
                "profile": "python-object-v1",
                "name": "istanze indipendenti",
                "class": "Conto",
                "construct": {"args": ["Anna", 100]},
                "additional_instances": [
                    {"id": "other", "construct": {"args": ["Luca", 50]}}
                ],
                "steps": [
                    {"call": "deposita", "args": [20], "expected_return": None},
                    {"observe": "saldo", "expected": 120},
                    {"instance": "other", "observe": "saldo", "expected": 50},
                ],
            },
            {
                "profile": "python-object-v1",
                "name": "costruttore protegge invariante",
                "class": "Conto",
                "construct": {"args": ["Anna", -1]},
                "expected_constructor_exception": "ValueError",
            },
        ],
    }


def _assignment() -> dict:
    return {
        "assignment_id": "assignment-python-p3-student-lab",
        "activity_id": "python-p3-student-lab-001",
        "student_id": "rossi-mario",
        "activity": {"path": "activities/python-p3-student-lab-001.json"},
        "workspace": {
            "path": "students/rossi-mario/assignments/python-p3-student-lab-001"
        },
    }


def test_p3_runs_through_normal_student_lab_and_redacts_teacher_oracles(
    tmp_path: Path,
) -> None:
    activity_path = tmp_path / "activities" / "python-p3-student-lab-001.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text(json.dumps(_activity()), encoding="utf-8")

    workspace = (
        tmp_path
        / "students"
        / "rossi-mario"
        / "assignments"
        / "python-p3-student-lab-001"
    )
    workspace.mkdir(parents=True)
    (workspace / "main.py").write_text(
        "class Conto:\n"
        "    def __init__(self, titolare, saldo):\n"
        "        if saldo < 0:\n"
        "            raise ValueError('saldo iniziale negativo')\n"
        "        self.titolare = titolare\n"
        "        self.saldo = saldo\n\n"
        "    def deposita(self, importo):\n"
        "        if importo <= 0:\n"
        "            raise ValueError('importo non valido')\n"
        "        self.saldo += importo\n\n"
        "    def saldo_corrente(self):\n"
        "        return self.saldo\n",
        encoding="utf-8",
    )

    docker_image = os.environ.get("THEBITLAB_P3_DOCKER_IMAGE", "thebitlab-p3-candidate")
    report = student_lab_runner.run_docker_assignment(
        _assignment(),
        root=tmp_path,
        timeout_seconds=3,
        docker_image=docker_image,
    )

    assert report["backend"] == "docker"
    assert report["passed"] is True
    assert report["status"] == "passed"
    assert report["profile"] == "python-object-v1"
    assert report["summary"] == {"passed": 4, "total": 4}
    assert report["tests"] == [
        {"name": "Test 1", "passed": True, "status": "passed"},
        {"name": "Test 2", "passed": True, "status": "passed"},
        {"name": "Test 3", "passed": True, "status": "passed"},
        {"name": "Test 4", "passed": True, "status": "passed"},
    ]

    serialized = json.dumps(report, ensure_ascii=False).casefold()
    for forbidden in (
        "object_tests",
        "expected_return",
        "expected_exception",
        "expected_constructor_exception",
        "observations",
        "worker_status",
        "deposito modifica lo stato",
        "deposito invalido preserva lo stato",
        "istanze indipendenti",
        "costruttore protegge invariante",
        "saldo iniziale negativo",
        "importo non valido",
    ):
        assert forbidden not in serialized
