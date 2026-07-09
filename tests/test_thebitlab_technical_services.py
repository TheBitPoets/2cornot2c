from __future__ import annotations

import pytest

from scripts.thebitlab_technical_services import (
    DeterministicGradingService,
    ExecutionResult,
    GradingRequest,
    InvalidServicePayloadError,
    RunnerTestResult,
    execution_result_from_payload,
    grading_dict_from_grade_activity_report,
)


def grade(execution: ExecutionResult):
    service = DeterministicGradingService()
    return service.grade(
        GradingRequest(
            activity_id="python-base-somma-001",
            student_id="rossi-mario",
            execution=execution,
        )
    )


def test_deterministic_grading_summarizes_passed_tests_for_dashboard() -> None:
    result = grade(
        ExecutionResult(
            status="passed",
            tests=[
                RunnerTestResult("somma_positivi", True),
                RunnerTestResult("somma_negativi", True),
            ],
        )
    )

    assert result.status == "graded_passed"
    assert result.passed is True
    assert result.tests_passed == 2
    assert result.tests_total == 2
    assert result.failed_tests == []
    assert result.score == 10
    assert result.to_dashboard_dict()["status"] == "graded_passed"


def test_deterministic_grading_keeps_failed_test_names_visible() -> None:
    result = grade(
        ExecutionResult(
            status="failed",
            tests=[
                RunnerTestResult("somma_positivi", True),
                RunnerTestResult("somma_negativi", False, "Output errato"),
            ],
            detail="Test deterministici falliti.",
        )
    )

    assert result.status == "graded_failed"
    assert result.passed is False
    assert result.tests_passed == 1
    assert result.tests_total == 2
    assert result.failed_tests == ["somma_negativi"]
    assert result.score == 5
    assert result.detail == "Test deterministici falliti."


def test_deterministic_grading_reports_timeout_as_error() -> None:
    result = grade(ExecutionResult(status="timeout", detail="Limite di 10 secondi superato."))

    assert result.status == "error"
    assert result.passed is False
    assert result.tests_passed == 0
    assert result.tests_total is None
    assert result.detail == "Limite di 10 secondi superato."


def test_deterministic_grading_does_not_run_when_runner_is_missing() -> None:
    result = grade(ExecutionResult(status="runner_unavailable", detail="Docker non disponibile."))

    assert result.status == "not_run"
    assert result.passed is None
    assert result.tests_passed is None
    assert result.tests_total is None
    assert result.detail == "Docker non disponibile."


def test_deterministic_grading_rejects_conclusive_execution_without_tests() -> None:
    result = grade(ExecutionResult(status="passed"))

    assert result.status == "error"
    assert result.passed is False
    assert result.tests_passed is None
    assert result.tests_total == 0
    assert result.detail == "Runner concluso senza test eseguiti."


def test_execution_result_from_payload_accepts_runner_json() -> None:
    result = execution_result_from_payload(
        """
        {
          "status": "failed",
          "tests": [
            {"name": "somma_positivi", "passed": true},
            {"name": "somma_negativi", "passed": false, "detail": "Output errato"}
          ],
          "stdout": "1",
          "stderr": "",
          "duration_ms": 42
        }
        """
    )

    assert result.status == "failed"
    assert result.tests[1] == RunnerTestResult("somma_negativi", False, "Output errato")
    assert result.duration_ms == 42


def test_grading_dict_from_grade_activity_report_keeps_failed_tests_visible() -> None:
    result = grading_dict_from_grade_activity_report(
        {
            "activity_id": "c-base-somma-001",
            "passed": False,
            "status": "failed",
            "teacher_grade": 5.5,
            "tests": [
                {"name": "somma_positivi", "passed": True, "status": "passed"},
                {"name": "somma_negativi", "passed": False, "status": "failed", "stderr": "Output errato"},
            ],
        }
    )

    assert result["status"] == "graded_failed"
    assert result["passed"] is False
    assert result["tests_passed"] == 1
    assert result["tests_total"] == 2
    assert result["failed_tests"] == ["somma_negativi"]
    assert result["score"] == 5
    assert result["teacher_grade"] == 5.5
    assert result["report_status"] == "failed"


def test_grading_dict_from_grade_activity_report_marks_infrastructure_errors_not_run() -> None:
    result = grading_dict_from_grade_activity_report(
        {
            "activity_id": "python-001",
            "passed": False,
            "status": "unsupported-language",
            "tests": [],
            "error": "Runner non ancora implementato per il linguaggio: python",
        }
    )

    assert result["status"] == "not_run"
    assert result["passed"] is None
    assert result["tests_passed"] is None
    assert result["tests_total"] is None
    assert result["detail"] == "Runner non ancora implementato per il linguaggio: python"
    assert result["report_status"] == "unsupported-language"


@pytest.mark.parametrize(
    "payload",
    [
        "{not-json",
        "[]",
        {"status": "unknown"},
        {"status": "passed"},
        {"status": "failed", "tests": []},
        {"status": "passed", "tests": {}},
        {"status": "passed", "tests": [{"name": "senza_esito"}]},
    ],
)
def test_execution_result_from_payload_rejects_invalid_payloads(payload) -> None:
    with pytest.raises(InvalidServicePayloadError):
        execution_result_from_payload(payload)
