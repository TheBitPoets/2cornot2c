from __future__ import annotations

import json

from scripts import student_lab_runner


def test_teacher_p2_results_are_redacted_for_student_report() -> None:
    teacher_report = {
        "passed": False,
        "status": "failed",
        "profile": "python-function-v1",
        "summary": {"passed": 1, "total": 2},
        "tests": [
            {
                "name": "area hidden oracle",
                "profile": "python-function-v1",
                "function": "area",
                "visibility": "teacher",
                "passed": True,
                "status": "passed",
                "worker_status": "returned",
                "stdout": "debug segreto",
                "stderr": "",
                "actual_return": 12,
                "actual_exception": None,
            },
            {
                "name": "exception hidden oracle",
                "profile": "python-function-v1",
                "function": "reciproco",
                "visibility": "teacher",
                "passed": False,
                "status": "failed",
                "worker_status": "raised",
                "stdout": "",
                "stderr": "",
                "actual_return": None,
                "actual_exception": {
                    "type": "ValueError",
                    "message": "teacher-only diagnostic",
                },
            },
        ],
    }

    student = student_lab_runner.redact_student_grading_report(teacher_report)

    assert student["tests"] == [
        {"name": "Test 1", "passed": True, "status": "passed"},
        {"name": "Test 2", "passed": False, "status": "failed"},
    ]
    serialized = json.dumps(student, ensure_ascii=False)
    for forbidden in (
        "area hidden oracle",
        "exception hidden oracle",
        "actual_return",
        "actual_exception",
        "teacher-only diagnostic",
        "debug segreto",
        "reciproco",
    ):
        assert forbidden not in serialized


def test_explicit_public_p2_result_can_preserve_public_observation() -> None:
    report = {
        "tests": [
            {
                "name": "esempio pubblico",
                "visibility": "public",
                "passed": True,
                "status": "passed",
                "worker_status": "returned",
                "actual_return": 6,
            }
        ]
    }
    student = student_lab_runner.redact_student_grading_report(report)
    assert student["tests"][0]["name"] == "esempio pubblico"
    assert student["tests"][0]["actual_return"] == 6
