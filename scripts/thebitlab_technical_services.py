from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


ExecutionStatus = Literal["passed", "failed", "timeout", "runner_unavailable", "invalid_payload"]
GradingStatus = Literal["graded_passed", "graded_failed", "not_run", "error"]
AiFeedbackStatus = Literal["not_generated", "draft", "error"]


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
    approved_by_teacher: bool = False
    detail: str = ""


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


def execution_result_from_payload(payload: str | dict[str, Any]) -> ExecutionResult:
    """Parse a runner payload into an ExecutionResult."""

    raw = _decode_payload(payload)
    status = raw.get("status")
    if status not in {"passed", "failed", "timeout", "runner_unavailable", "invalid_payload"}:
        raise InvalidServicePayloadError("Payload runner senza status valido.")

    tests_raw = raw.get("tests", [])
    if not isinstance(tests_raw, list):
        raise InvalidServicePayloadError("Payload runner con tests non validi.")

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
