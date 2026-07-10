from __future__ import annotations

import pytest

from scripts.thebitlab_technical_services import (
    AiFeedbackRequest,
    DeterministicGradingService,
    DeterministicAiFeedbackService,
    ExecutionResult,
    ExecutionRequest,
    GradeActivityExecutionService,
    GradingResult,
    GradingRequest,
    InvalidServicePayloadError,
    ManualAiFeedbackPackage,
    RunnerTestResult,
    ai_feedback_dict_from_grading,
    ai_feedback_request_payload,
    ai_feedback_result_from_payload,
    execution_result_from_payload,
    grading_dict_from_grade_activity_report,
    manual_ai_feedback_package,
    manual_ai_feedback_result_from_response,
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


def test_grading_dict_from_grade_activity_report_marks_compile_error_as_failed_grading() -> None:
    result = grading_dict_from_grade_activity_report(
        {
            "activity_id": "c-base-somma-001",
            "passed": False,
            "status": "compile-error",
            "compile": {"stderr": "main.c: errore di sintassi"},
            "tests": [],
        }
    )

    assert result["status"] == "graded_failed"
    assert result["passed"] is False
    assert result["tests_passed"] == 0
    assert result["tests_total"] == 1
    assert result["failed_tests"] == ["compilazione"]
    assert result["detail"] == "main.c: errore di sintassi"
    assert result["report_status"] == "compile-error"


def test_grading_dict_from_grade_activity_report_marks_compile_timeout_as_failed_grading() -> None:
    result = grading_dict_from_grade_activity_report(
        {
            "activity_id": "c-base-somma-001",
            "passed": False,
            "status": "compile-timeout",
            "compile": {"stderr": "Compilazione interrotta per timeout"},
            "tests": [],
        }
    )

    assert result["status"] == "graded_failed"
    assert result["passed"] is False
    assert result["tests_passed"] == 0
    assert result["tests_total"] == 1
    assert result["failed_tests"] == ["compilazione"]
    assert result["detail"] == "Compilazione interrotta per timeout"
    assert result["report_status"] == "compile-timeout"


def test_grading_dict_from_grade_activity_report_marks_missing_source_as_failed_grading() -> None:
    result = grading_dict_from_grade_activity_report(
        {
            "activity_id": "c-base-somma-001",
            "passed": False,
            "status": "source-not-found",
            "source": "assignments/c-base-somma-001/main.c",
            "error": "Sorgente non trovato: assignments/c-base-somma-001/main.c",
            "tests": [],
        }
    )

    assert result["status"] == "graded_failed"
    assert result["passed"] is False
    assert result["tests_passed"] == 0
    assert result["tests_total"] == 1
    assert result["failed_tests"] == ["sorgente"]
    assert result["detail"] == "Sorgente non trovato: assignments/c-base-somma-001/main.c"
    assert result["report_status"] == "source-not-found"


def test_grade_activity_execution_service_runs_existing_runner(monkeypatch, tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.c"
    activity_path.write_text('{"id": "c-base-somma-001"}', encoding="utf-8")
    source_path.write_text("int main(void){return 0;}", encoding="utf-8")

    from scripts import grade_activity

    def fake_grade_activity(activity, source, *, timeout_seconds, language):
        assert activity == {"id": "c-base-somma-001"}
        assert source == source_path
        assert timeout_seconds == 7
        assert language == "c"
        return {
            "activity_id": activity["id"],
            "passed": True,
            "status": "passed",
            "tests": [{"name": "base", "passed": True, "status": "passed"}],
        }

    monkeypatch.setattr(grade_activity, "grade_activity", fake_grade_activity)

    result = GradeActivityExecutionService().run(
        ExecutionRequest(
            activity_id="c-base-somma-001",
            student_id="rossi-mario",
            files={"main.c": str(source_path)},
            language="c",
            timeout_seconds=7,
            metadata={"activity_path": activity_path, "source_path": source_path},
        )
    )

    assert result.status == "passed"
    assert result.tests == [RunnerTestResult("base", True)]


def test_grade_activity_execution_service_rejects_missing_paths() -> None:
    result = GradeActivityExecutionService().run(
        ExecutionRequest(
            activity_id="c-base-somma-001",
            student_id="rossi-mario",
            files={},
            language="c",
            metadata={},
        )
    )

    assert result.status == "invalid_payload"
    assert "activity_path" in result.detail


def test_grade_activity_execution_service_returns_invalid_payload_for_missing_activity(tmp_path) -> None:
    result = GradeActivityExecutionService().run(
        ExecutionRequest(
            activity_id="c-base-somma-001",
            student_id="rossi-mario",
            files={},
            language="c",
            metadata={"activity_path": tmp_path / "missing.json", "source_path": tmp_path / "main.c"},
        )
    )

    assert result.status == "invalid_payload"
    assert "Activity non caricata" in result.detail


def test_grade_activity_execution_service_returns_invalid_payload_for_bad_activity_json(tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    activity_path.write_text("{not-json", encoding="utf-8")

    result = GradeActivityExecutionService().run(
        ExecutionRequest(
            activity_id="c-base-somma-001",
            student_id="rossi-mario",
            files={},
            language="c",
            metadata={"activity_path": activity_path, "source_path": tmp_path / "main.c"},
        )
    )

    assert result.status == "invalid_payload"
    assert "Activity non caricata" in result.detail


def test_deterministic_ai_feedback_summarizes_passed_grading() -> None:
    grading = GradingResult(
        status="graded_passed",
        passed=True,
        tests_passed=2,
        tests_total=2,
        failed_tests=[],
        score=10,
    )

    feedback = DeterministicAiFeedbackService().generate_feedback(
        AiFeedbackRequest(activity_id="activity", student_id="rossi-mario", grading=grading)
    )

    assert feedback.status == "draft"
    assert feedback.summary == "Tutti i test deterministici risultano superati (2/2)."
    assert feedback.suggested_grade == 10
    assert feedback.approved_by_teacher is False


def test_deterministic_ai_feedback_names_failed_tests() -> None:
    grading = GradingResult(
        status="graded_failed",
        passed=False,
        tests_passed=1,
        tests_total=2,
        failed_tests=["somma_negativi"],
        score=5,
        detail="Output errato",
    )

    feedback = DeterministicAiFeedbackService().generate_feedback(
        AiFeedbackRequest(activity_id="activity", student_id="rossi-mario", grading=grading)
    )

    assert feedback.status == "draft"
    assert "somma_negativi" in feedback.summary
    assert feedback.suggested_grade == 5
    assert feedback.detail == "Output errato"


def test_ai_feedback_dict_from_grading_is_register_compatible() -> None:
    grading = GradingResult(
        status="not_run",
        passed=None,
        tests_passed=None,
        tests_total=None,
        failed_tests=[],
        detail="Runner non disponibile",
    )

    feedback = ai_feedback_dict_from_grading(grading)

    assert feedback == {
        "status": "draft",
        "suggested_grade": None,
        "summary": "Correzione automatica non eseguita: serve verificare il runner o i dati della consegna.",
        "approved_by_teacher": False,
        "detail": "Runner non disponibile",
    }


def test_ai_feedback_request_payload_uses_stable_manual_contract() -> None:
    grading = GradingResult(
        status="graded_failed",
        passed=False,
        tests_passed=1,
        tests_total=2,
        failed_tests=["somma_negativi"],
        score=5,
        detail="Output errato",
    )

    payload = ai_feedback_request_payload(
        AiFeedbackRequest(
            activity_id="c-base-somma-001",
            student_id="rossi-mario",
            grading=grading,
            allowed_context={"teacher_notes": "Controllare il caso con negativi."},
        ),
        activity={"id": "activity-sbagliata", "title": "Somma in C"},
    )

    assert payload["schema_version"] == "ai_feedback_request.v1"
    assert payload["activity"] == {"id": "c-base-somma-001", "title": "Somma in C"}
    assert payload["student"] == {"id": "rossi-mario"}
    assert payload["grading"]["failed_tests"] == ["somma_negativi"]
    assert payload["policy"]["mode"] == "bozza_docente"
    assert payload["policy"]["allowed_context"] == ["teacher_notes"]


def test_ai_feedback_result_from_payload_normalizes_manual_response() -> None:
    feedback = ai_feedback_result_from_payload(
        {
            "schema_version": "ai_feedback_response.v1",
            "status": "draft",
            "summary": "La soluzione fallisce con numeri negativi.",
            "suggested_grade": 5,
            "student_feedback": "Rivedi il caso con addendi negativi.",
            "teacher_notes": "Errore probabilmente nel parsing del segno.",
            "confidence": "medium",
        }
    )

    assert feedback.status == "draft"
    assert feedback.summary == "La soluzione fallisce con numeri negativi."
    assert feedback.suggested_grade == 5.0
    assert feedback.student_feedback == "Rivedi il caso con addendi negativi."
    assert feedback.teacher_notes == "Errore probabilmente nel parsing del segno."
    assert feedback.confidence == "medium"
    assert feedback.approved_by_teacher is False


@pytest.mark.parametrize(
    "payload",
    [
        "{not-json",
        [],
        {"schema_version": "wrong", "status": "draft"},
        {"schema_version": "ai_feedback_response.v1", "status": "draft"},
        {"schema_version": "ai_feedback_response.v1", "status": "error"},
        {"schema_version": "ai_feedback_response.v1", "status": "approved"},
        {
            "schema_version": "ai_feedback_response.v1",
            "status": "draft",
            "suggested_grade": "cinque",
        },
        {
            "schema_version": "ai_feedback_response.v1",
            "status": "draft",
            "suggested_grade": True,
        },
        {
            "schema_version": "ai_feedback_response.v1",
            "status": "draft",
            "student_feedback": ["non", "testo"],
        },
        {
            "schema_version": "ai_feedback_response.v1",
            "status": "error",
            "detail": {"message": "errore"},
        },
    ],
)
def test_ai_feedback_result_from_payload_rejects_invalid_manual_responses(payload) -> None:
    with pytest.raises(InvalidServicePayloadError):
        ai_feedback_result_from_payload(payload)


def test_manual_ai_feedback_package_prepares_prompt_and_json() -> None:
    grading = GradingResult(
        status="graded_failed",
        passed=False,
        tests_passed=1,
        tests_total=2,
        failed_tests=["somma_negativi"],
        score=5,
    )

    package = manual_ai_feedback_package(
        AiFeedbackRequest(
            activity_id="c-base-somma-001",
            student_id="rossi-mario",
            grading=grading,
            allowed_context={"teacher_notes": "Controllare il caso con negativi."},
        ),
        activity={"title": "Somma in C"},
    )

    assert isinstance(package, ManualAiFeedbackPackage)
    assert "ai_feedback_response.v1" in package.prompt
    assert "Non approvare il feedback al posto del docente" in package.prompt
    assert package.request_json in package.prompt
    assert '"schema_version": "ai_feedback_request.v1"' in package.request_json
    assert '"id": "c-base-somma-001"' in package.request_json


def test_manual_ai_feedback_result_from_response_uses_validated_contract() -> None:
    feedback = manual_ai_feedback_result_from_response(
        {
            "schema_version": "ai_feedback_response.v1",
            "status": "draft",
            "summary": "La consegna fallisce un caso limite.",
        }
    )

    assert feedback.status == "draft"
    assert feedback.summary == "La consegna fallisce un caso limite."
    assert feedback.approved_by_teacher is False


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
