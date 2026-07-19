from __future__ import annotations

import json

from scripts import student_lab_demo_smoke


def test_student_lab_demo_smoke_builds_complete_flow(tmp_path) -> None:
    summary = student_lab_demo_smoke.run_smoke(tmp_path)

    assert summary["ok"] is True
    assert summary["student_id"] == "rossi-mario"
    assert summary["activity_id"] == "python-demo-somma-001"
    assert summary["workspace"].endswith("assignments/python-demo-somma-001")
    assert summary["report"].endswith("reports/python-demo-somma-001/latest.json")
    assert summary["teacher_register"].endswith("teacher-reports/demo/python-demo-somma-001.json")
    assert summary["tests"] == {"passed": 2, "total": 2}
    assert summary["help"] == {
        "total": 1,
        "ai_total": 1,
        "ai_budget_remaining": 4,
        "response_provider": "deterministic-local",
    }
    assert summary["backend"] == "local"

    register = json.loads((tmp_path / summary["teacher_register"]).read_text(encoding="utf-8"))
    student = register["students"][0]
    assert student["submitted"] is True
    assert student["repo"] == "TheBitPoets/rossi-mario"
    assert student["repo_path"] == "examples/assignment_tracking/student_repos/rossi-mario"
    assert student["grading"]["status"] == "graded_passed"
    assert student["submission"]["report_backend"] == "local"
    assert student["help"]["total"] == 1
    assert student["help"]["ai_total"] == 1
    assert student["help"]["events"][0]["prompt"] == "Puoi darmi un suggerimento senza scrivere la soluzione?"
    assert student["help"]["events"][0]["response"]["status"] == "ready"
    assert student["help"]["events"][0]["response"]["provider"] == "deterministic-local"
