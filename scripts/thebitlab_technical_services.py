from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol


ExecutionStatus = Literal["passed", "failed", "timeout", "runner_unavailable", "invalid_payload"]
GradingStatus = Literal["graded_passed", "graded_failed", "not_run", "error"]
AiFeedbackStatus = Literal["not_generated", "draft", "error"]
AI_FEEDBACK_REQUEST_SCHEMA_VERSION = "ai_feedback_request.v1"
AI_FEEDBACK_RESPONSE_SCHEMA_VERSION = "ai_feedback_response.v1"


class TechnicalServiceError(RuntimeError):
    """Base error for isolated technical services."""


class RunnerUnavailableError(TechnicalServiceError):
    """Raised when Docker or another configured execution runner is not available."""


class ExecutionTimeoutError(TechnicalServiceError):
    """Raised when student code execution exceeds the configured timeout."""


class InvalidServicePayloadError(TechnicalServiceError):
    """Raised when a technical service returns malformed or incomplete data."""


@dataclass(frozen=True)
class ExecutionRequest:
    """Input for a sandboxed execution service."""

    activity_id: str
    student_id: str
    files: dict[str, str]
    language: str
    timeout_seconds: int = 10
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunnerTestResult:
    """Result of one deterministic test case."""

    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class ExecutionResult:
    """Output produced by a runner before didactic grading policy is applied."""

    status: ExecutionStatus
    tests: list[RunnerTestResult] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_ms: int | None = None
    detail: str = ""


@dataclass(frozen=True)
class GradingRequest:
    """Input for deterministic grading."""

    activity_id: str
    student_id: str
    execution: ExecutionResult
    grading_policy: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GradingResult:
    """Dashboard-ready deterministic grading result."""

    status: GradingStatus
    passed: bool | None
    tests_passed: int | None
    tests_total: int | None
    failed_tests: list[str] = field(default_factory=list)
    score: float | None = None
    teacher_grade: float | None = None
    detail: str = ""

    def to_dashboard_dict(self) -> dict[str, Any]:
        """Return the shape already used by assignment registers."""

        return {
            "status": self.status,
            "passed": self.passed,
            "tests_passed": self.tests_passed,
            "tests_total": self.tests_total,
            "failed_tests": self.failed_tests,
            "score": self.score,
            "teacher_grade": self.teacher_grade,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AiFeedbackRequest:
    """Input for AI feedback generation, after deterministic grading exists."""

    activity_id: str
    student_id: str
    grading: GradingResult
    allowed_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AiFeedbackResult:
    """Teacher-approvable AI feedback draft."""

    status: AiFeedbackStatus
    summary: str | None = None
    suggested_grade: float | None = None
    student_feedback: str | None = None
    teacher_notes: str | None = None
    confidence: str | None = None
    approved_by_teacher: bool = False
    detail: str = ""


@dataclass(frozen=True)
class ManualAiFeedbackPackage:
    """Prompt and JSON payload prepared for manual AI provider workflows."""

    prompt: str
    request_json: str


class ExecutionService(Protocol):
    """Port for Docker/local execution of untrusted student code."""

    def run(self, request: ExecutionRequest) -> ExecutionResult: ...


class GradingService(Protocol):
    """Port for deterministic grading based on runner output and policy."""

    def grade(self, request: GradingRequest) -> GradingResult: ...


class AiFeedbackService(Protocol):
    """Port for provider-backed feedback drafts separated from grading."""

    def generate_feedback(self, request: AiFeedbackRequest) -> AiFeedbackResult: ...


class DeterministicGradingService:
    """Small grading service that summarizes runner tests without calling AI."""

    def grade(self, request: GradingRequest) -> GradingResult:
        execution = request.execution
        if execution.status == "timeout":
            return GradingResult(
                status="error",
                passed=False,
                tests_passed=0,
                tests_total=len(execution.tests) if execution.tests else None,
                failed_tests=[test.name for test in execution.tests if not test.passed],
                detail=execution.detail or "Esecuzione interrotta per timeout.",
            )
        if execution.status in {"runner_unavailable", "invalid_payload"}:
            return GradingResult(
                status="not_run",
                passed=None,
                tests_passed=None,
                tests_total=None,
                detail=execution.detail or "Runner non disponibile o payload non valido.",
            )
        if execution.status not in {"passed", "failed"}:
            return GradingResult(status="error", passed=False, tests_passed=None, tests_total=None, detail=execution.detail)

        if not execution.tests:
            return GradingResult(
                status="error",
                passed=False,
                tests_passed=None,
                tests_total=0,
                detail=execution.detail or "Runner concluso senza test eseguiti.",
            )

        total = len(execution.tests)
        passed = sum(1 for test in execution.tests if test.passed)
        failed_tests = [test.name for test in execution.tests if not test.passed]
        all_passed = execution.status == "passed" and not failed_tests
        score = round((passed / total) * 10, 2) if total else None
        return GradingResult(
            status="graded_passed" if all_passed else "graded_failed",
            passed=all_passed,
            tests_passed=passed,
            tests_total=total,
            failed_tests=failed_tests,
            score=score,
            detail=execution.detail,
        )


class GradeActivityExecutionService:
    """ExecutionService adapter backed by scripts.grade_activity."""

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        """Run the existing grade_activity runner and return an ExecutionResult."""

        from scripts import grade_activity

        activity_path = request.metadata.get("activity_path")
        source_path = request.metadata.get("source_path")
        if not activity_path or not source_path:
            return ExecutionResult(
                status="invalid_payload",
                detail="ExecutionRequest.metadata deve includere activity_path e source_path.",
            )

        try:
            activity = grade_activity.load_activity(Path(str(activity_path)))
        except (OSError, json.JSONDecodeError) as error:
            return ExecutionResult(status="invalid_payload", detail=f"Activity non caricata: {error}")

        report = grade_activity.grade_activity(
            activity,
            Path(str(source_path)),
            timeout_seconds=request.timeout_seconds,
            language=request.language,
        )
        return execution_result_from_grade_activity_report(report)


class DeterministicAiFeedbackService:
    """Mockable AI feedback service that never calls external providers."""

    def generate_feedback(self, request: AiFeedbackRequest) -> AiFeedbackResult:
        """Generate a deterministic teacher-reviewable feedback draft."""

        grading = request.grading
        if grading.status == "not_run":
            return AiFeedbackResult(
                status="draft",
                summary="Correzione automatica non eseguita: serve verificare il runner o i dati della consegna.",
                suggested_grade=None,
                detail=grading.detail,
            )
        if grading.status == "error":
            return AiFeedbackResult(
                status="draft",
                summary="La correzione ha incontrato un errore tecnico: controlla il dettaglio prima di dare feedback allo studente.",
                suggested_grade=None,
                detail=grading.detail,
            )
        if grading.status == "graded_passed":
            return AiFeedbackResult(
                status="draft",
                summary=f"Tutti i test deterministici risultano superati ({grading.tests_passed}/{grading.tests_total}).",
                suggested_grade=grading.score,
            )

        failed = ", ".join(grading.failed_tests) if grading.failed_tests else "nessun nome test disponibile"
        return AiFeedbackResult(
            status="draft",
            summary=(
                f"La consegna non supera tutti i test deterministici "
                f"({grading.tests_passed}/{grading.tests_total}). Test da rivedere: {failed}."
            ),
            suggested_grade=grading.score,
            detail=grading.detail,
        )


def ai_feedback_dict_from_grading(grading: GradingResult) -> dict[str, Any]:
    """Return register-compatible AI feedback fields from deterministic feedback."""

    feedback = DeterministicAiFeedbackService().generate_feedback(
        AiFeedbackRequest(activity_id="", student_id="", grading=grading)
    )
    return {
        "status": feedback.status,
        "suggested_grade": feedback.suggested_grade,
        "summary": feedback.summary,
        "approved_by_teacher": feedback.approved_by_teacher,
        "detail": feedback.detail,
    }


def ai_feedback_request_payload(
    request: AiFeedbackRequest,
    *,
    activity: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the JSON exchange payload for manual or provider-backed feedback."""

    return {
        "schema_version": AI_FEEDBACK_REQUEST_SCHEMA_VERSION,
        "activity": {**(activity or {}), "id": request.activity_id},
        "student": {"id": request.student_id},
        "grading": request.grading.to_dashboard_dict(),
        "context": request.allowed_context,
        "policy": {
            "mode": "bozza_docente",
            "allow_grade_suggestion": True,
            "allowed_context": sorted(request.allowed_context.keys()),
            **(policy or {}),
        },
    }


def ai_feedback_request_json(
    request: AiFeedbackRequest,
    *,
    activity: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> str:
    """Serialize the AI feedback request payload with stable formatting."""

    return json.dumps(
        ai_feedback_request_payload(request, activity=activity, policy=policy),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def manual_ai_feedback_package(
    request: AiFeedbackRequest,
    *,
    activity: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> ManualAiFeedbackPackage:
    """Prepare copy/paste material for ChatGPT, Codex, or another manual provider."""

    request_json = ai_feedback_request_json(request, activity=activity, policy=policy)
    prompt = (
        "Sei un assistente didattico per la correzione di esercizi di programmazione. "
        "Leggi il JSON seguente e rispondi solo con JSON valido nello schema "
        f"{AI_FEEDBACK_RESPONSE_SCHEMA_VERSION}. "
        "Non approvare il feedback al posto del docente. "
        "Per status draft includi almeno summary; per status error includi summary o detail.\n\n"
        f"{request_json}"
    )
    return ManualAiFeedbackPackage(prompt=prompt, request_json=request_json)


def manual_ai_feedback_result_from_response(payload: str | dict[str, Any]) -> AiFeedbackResult:
    """Normalize a pasted manual-provider JSON response to AiFeedbackResult."""

    return ai_feedback_result_from_payload(payload)


def ai_feedback_result_from_payload(payload: str | dict[str, Any]) -> AiFeedbackResult:
    """Validate a provider/manual JSON response and normalize it to AiFeedbackResult."""

    raw = _decode_ai_feedback_payload(payload)
    schema_version = raw.get("schema_version")
    if schema_version != AI_FEEDBACK_RESPONSE_SCHEMA_VERSION:
        raise InvalidServicePayloadError("Payload feedback AI con schema_version non valido.")

    status = raw.get("status")
    if status not in {"draft", "error"}:
        raise InvalidServicePayloadError("Payload feedback AI senza status valido.")

    summary = _optional_text(raw, "summary")
    detail = _optional_text(raw, "detail") or ""
    if status == "draft" and not summary:
        raise InvalidServicePayloadError("Payload feedback AI draft senza summary.")
    if status == "error" and not (summary or detail):
        raise InvalidServicePayloadError("Payload feedback AI error senza dettaglio.")

    suggested_grade = raw.get("suggested_grade")
    if suggested_grade is not None and (
        isinstance(suggested_grade, bool) or not isinstance(suggested_grade, (int, float))
    ):
        raise InvalidServicePayloadError("Payload feedback AI con suggested_grade non valido.")

    return AiFeedbackResult(
        status=status,
        summary=summary,
        suggested_grade=None if suggested_grade is None else float(suggested_grade),
        student_feedback=_optional_text(raw, "student_feedback"),
        teacher_notes=_optional_text(raw, "teacher_notes"),
        confidence=_optional_text(raw, "confidence"),
        approved_by_teacher=False,
        detail=detail,
    )


def execution_result_from_payload(payload: str | dict[str, Any]) -> ExecutionResult:
    """Parse a runner payload into an ExecutionResult."""

    raw = _decode_payload(payload)
    status = raw.get("status")
    if status not in {"passed", "failed", "timeout", "runner_unavailable", "invalid_payload"}:
        raise InvalidServicePayloadError("Payload runner senza status valido.")

    tests_raw = raw.get("tests", [])
    if not isinstance(tests_raw, list):
        raise InvalidServicePayloadError("Payload runner con tests non validi.")
    if status in {"passed", "failed"} and not tests_raw:
        raise InvalidServicePayloadError("Payload runner conclusivo senza test eseguiti.")

    tests = []
    for item in tests_raw:
        if not isinstance(item, dict) or not item.get("name") or not isinstance(item.get("passed"), bool):
            raise InvalidServicePayloadError("Payload runner con test case incompleto.")
        tests.append(RunnerTestResult(name=str(item["name"]), passed=item["passed"], detail=str(item.get("detail", ""))))

    return ExecutionResult(
        status=status,
        tests=tests,
        stdout=str(raw.get("stdout", "")),
        stderr=str(raw.get("stderr", "")),
        duration_ms=raw.get("duration_ms") if isinstance(raw.get("duration_ms"), int) else None,
        detail=str(raw.get("detail", "")),
    )


def execution_result_from_grade_activity_report(report: dict[str, Any]) -> ExecutionResult:
    """Convert the legacy grade_activity.py report into an ExecutionResult."""

    status = str(report.get("status", ""))
    tests = [
        RunnerTestResult(
            name=str(test.get("name") or test.get("id") or f"test {index + 1}"),
            passed=bool(test.get("passed")),
            detail=str(test.get("message") or test.get("error") or test.get("stderr") or ""),
        )
        for index, test in enumerate(report.get("tests", []) if isinstance(report.get("tests"), list) else [])
        if isinstance(test, dict) and isinstance(test.get("passed"), bool)
    ]
    if status in {"compile-error", "compile-timeout"} and not tests:
        tests.append(RunnerTestResult(name="compilazione", passed=False, detail=_grade_activity_report_detail(report)))
    if status == "source-not-found" and not tests:
        tests.append(RunnerTestResult(name="sorgente", passed=False, detail=_grade_activity_report_detail(report)))

    if report.get("passed") is True:
        execution_status: ExecutionStatus = "passed"
    elif status == "timeout":
        execution_status = "timeout"
    elif status in {"invalid-activity"}:
        execution_status = "invalid_payload"
    elif status in {"compiler-not-found", "unsupported-language", "unknown-language"}:
        execution_status = "runner_unavailable"
    else:
        execution_status = "failed"

    detail = _grade_activity_report_detail(report)
    return ExecutionResult(status=execution_status, tests=tests, detail=detail)


def grading_dict_from_grade_activity_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return dashboard-ready grading fields from a legacy grade_activity.py report."""

    execution = execution_result_from_grade_activity_report(report)
    grading = DeterministicGradingService().grade(
        GradingRequest(
            activity_id=str(report.get("activity_id") or ""),
            student_id=str(report.get("student_id") or ""),
            execution=execution,
        )
    )
    result = grading.to_dashboard_dict()
    result["score"] = report.get("score", result["score"])
    result["teacher_grade"] = report.get("teacher_grade", result["teacher_grade"])
    result["tests"] = _grade_activity_report_tests(report)
    result["report_status"] = report.get("status")
    return result


def _grade_activity_report_tests(report: dict[str, Any]) -> list[dict[str, Any]]:
    tests = []
    for index, test in enumerate(report.get("tests", []) if isinstance(report.get("tests"), list) else []):
        if not isinstance(test, dict):
            continue
        tests.append(
            {
                "name": str(test.get("name") or test.get("id") or f"test {index + 1}"),
                "passed": test.get("passed"),
                "status": test.get("status"),
                "message": test.get("message") or test.get("error") or "",
                "expected_stdout": test.get("expected_stdout"),
                "actual_stdout": test.get("actual_stdout"),
            }
        )
    return tests


def _grade_activity_report_detail(report: dict[str, Any]) -> str:
    if isinstance(report.get("errors"), list):
        return "; ".join(str(error) for error in report["errors"])
    compile_result = report.get("compile") if isinstance(report.get("compile"), dict) else {}
    return str(report.get("error") or compile_result.get("stderr") or report.get("status") or "")


def _decode_payload(payload: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise InvalidServicePayloadError("Payload runner non e JSON valido.") from exc
    if not isinstance(decoded, dict):
        raise InvalidServicePayloadError("Payload runner JSON non e un oggetto.")
    return decoded


def _decode_ai_feedback_payload(payload: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if not isinstance(payload, str):
        raise InvalidServicePayloadError("Payload feedback AI JSON non e un oggetto.")
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise InvalidServicePayloadError("Payload feedback AI non e JSON valido.") from exc
    if not isinstance(decoded, dict):
        raise InvalidServicePayloadError("Payload feedback AI JSON non e un oggetto.")
    return decoded


def _optional_text(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidServicePayloadError(f"Payload feedback AI con {key} non valido.")
    return value
