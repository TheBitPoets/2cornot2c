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


def activity_payload() -> dict:
    return {
        "schema_version": "1.0",
        "id": "python-p4-student-lab-001",
        "title": "Persistenza nel percorso Student Lab",
        "titolo": "Persistenza nel percorso Student Lab",
        "kind": "laboratorio",
        "tipo": "laboratorio",
        "language": "python",
        "linguaggio": "python",
        "source_name": "main.py",
        "difficulty": "B",
        "difficolta": "B",
        "topics": ["file", "pathlib"],
        "argomenti": ["file", "pathlib"],
        "instructions": "Leggi misure.txt e crea risultato.txt.",
        "consegna": "Leggi misure.txt e crea risultato.txt.",
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
        "filesystem_tests": [
            {
                "profile": "python-filesystem-v1",
                "name": "oracle docente totale 36",
                "fixtures": [
                    {
                        "id": "misure",
                        "source": "fixtures/misure.txt",
                        "target": "misure.txt",
                        "mode": "read-only",
                    }
                ],
                "expected_artifacts": [
                    {
                        "path": "risultato.txt",
                        "text": "36\n",
                        "encoding": "utf-8",
                    }
                ],
                "visibility": "teacher",
            }
        ],
    }


def assignment_payload() -> dict:
    return {
        "assignment_id": "assignment-python-p4-student-lab",
        "activity_id": "python-p4-student-lab-001",
        "student_id": "rossi-mario",
        "activity": {"path": "activities/python-p4-student-lab-001/activity.json"},
        "workspace": {
            "path": "students/rossi-mario/assignments/python-p4-student-lab-001"
        },
    }


def test_p4_runs_through_normal_student_lab_and_redacts_teacher_oracles(tmp_path: Path) -> None:
    activity_root = tmp_path / "activities" / "python-p4-student-lab-001"
    fixtures = activity_root / "fixtures"
    fixtures.mkdir(parents=True)
    (fixtures / "misure.txt").write_text("12\n15\n9\n", encoding="utf-8")
    (activity_root / "activity.json").write_text(
        json.dumps(activity_payload()),
        encoding="utf-8",
    )

    workspace = (
        tmp_path
        / "students"
        / "rossi-mario"
        / "assignments"
        / "python-p4-student-lab-001"
    )
    workspace.mkdir(parents=True)
    (workspace / "main.py").write_text(
        "from pathlib import Path\n"
        "values = [int(x) for x in Path('misure.txt').read_text(encoding='utf-8').splitlines()]\n"
        "Path('risultato.txt').write_text(f'{sum(values)}\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    image = os.environ.get("THEBITLAB_P4_DOCKER_IMAGE", "thebitlab-p4-candidate")
    report = student_lab_runner.run_docker_assignment(
        assignment_payload(),
        root=tmp_path,
        timeout_seconds=3,
        docker_image=image,
    )

    assert report["backend"] == "docker"
    assert report["passed"] is True
    assert report["status"] == "passed"
    assert report["profile"] == "python-filesystem-v1"
    assert report["summary"] == {"passed": 1, "total": 1}
    assert report["tests"] == [
        {"name": "Test 1", "passed": True, "status": "passed"}
    ]

    serialized = json.dumps(report, ensure_ascii=False).casefold()
    for forbidden in (
        "oracle docente totale 36",
        "worker_status",
        "observed_artifacts",
        "checks",
        "fixtures/misure.txt",
        "expected_artifacts",
        '"36\\n"',
    ):
        assert forbidden not in serialized
