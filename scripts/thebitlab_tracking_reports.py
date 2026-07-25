"""Application adapter for authoritative remote grading reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable, Protocol

from scripts.thebitlab_grading_artifacts import (
    GradingArtifactError,
    GradingArtifactSource,
)
from scripts.thebitlab_repository_providers import normalize_github_repo_ref


REMOTE_TEST_OUTCOME_STATUSES = frozenset({"passed", "failed"})
REMOTE_TEST_RESULT_STATUSES = frozenset(
    {
        "execution-error",
        "failed",
        "passed",
        "runtime-startup-timeout",
        "timeout",
    }
)
REMOTE_TERMINAL_STATUSES = frozenset(
    {
        "compile-error",
        "compile-timeout",
        "compiler-not-found",
        "execution-error",
        "invalid-activity",
        "runtime-startup-timeout",
        "source-not-found",
        "timeout",
        "unknown-language",
        "unsupported-language",
        "worker-error",
    }
)


GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class TrackingReportRequest:
    """Identity of one student report requested by assignment tracking."""

    activity_id: str
    assignment_id: str
    student_id: str
    repo_ref: str


@dataclass(frozen=True)
class TrustedGradingBinding:
    """Teacher-controlled binding to one trusted GitHub Actions run."""

    activity_id: str
    assignment_id: str
    student_id: str
    student_repo_ref: str
    workflow_repo_ref: str
    artifact_name: str
    expected_student_head_sha: str
    expected_workflow_head_sha: str
    expected_submitted_at: str
    expected_workflow_run_id: int
    final: bool = False


@dataclass(frozen=True)
class TrackingReportResult:
    """Remote report resolution without transport-specific exceptions."""

    configured: bool
    report: dict[str, Any] | None = None
    selection: str | None = None
    authority: str | None = None
    provisional: bool = False
    provenance: dict[str, Any] | None = None
    error: str | None = None


def load_trusted_grading_bindings(path: Path) -> list[TrustedGradingBinding]:
    """Load teacher-controlled remote grading bindings from JSON."""

    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Binding grading non leggibili: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError("Il file dei binding grading deve contenere un oggetto JSON.")
    if payload.get("schema_version") != "thebitlab_grading_bindings.v1":
        raise ValueError("Versione schema binding grading non supportata.")
    entries = payload.get("bindings")
    if not isinstance(entries, list):
        raise ValueError("bindings deve essere una lista.")
    bindings: list[TrustedGradingBinding] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Binding grading {index + 1} non valido.")
        try:
            binding = TrustedGradingBinding(**entry)
        except TypeError as error:
            raise ValueError(f"Campi binding grading {index + 1} non validi.") from error
        bindings.append(_validated_binding(binding))
    return bindings


class TrackingReportSource(Protocol):
    """Port consumed by assignment tracking for optional remote reports."""

    def resolve(self, request: TrackingReportRequest) -> TrackingReportResult:
        """Resolve a report or state that no remote binding is configured."""


def canonical_tracking_report_result(result: TrackingReportResult) -> TrackingReportResult:
    """Normalize untrusted adapter output into a fail-closed tracking state."""

    if not result.configured:
        return TrackingReportResult(configured=False)
    if result.report is None:
        return TrackingReportResult(
            configured=True,
            selection="remote_error",
            authority="remote_configured",
            provisional=False,
            error=result.error or "Risultato sorgente remota non valido.",
        )
    if (
        result.selection != "github_actions_artifact"
        or result.authority != "verified_remote"
        or not isinstance(result.provenance, dict)
        or not result.provenance
    ):
        return TrackingReportResult(
            configured=True,
            selection="remote_error",
            authority="remote_configured",
            provisional=False,
            error=result.error or "Provenienza del report remoto non verificabile.",
        )
    try:
        owner, repo = normalize_github_repo_ref(
            str(result.provenance.get("repository", "") or "")
        )
    except ValueError:
        return TrackingReportResult(
            configured=True,
            selection="remote_error",
            authority="remote_configured",
            provisional=False,
            error=result.error or "Repository del report remoto non verificabile.",
        )
    provenance = dict(result.provenance)
    provenance["repository"] = f"{owner}/{repo}"
    return TrackingReportResult(
        configured=True,
        report=result.report,
        selection="github_actions_artifact",
        authority="verified_remote",
        provisional=bool(result.provisional),
        provenance=provenance,
    )


class ArtifactTrackingReportSource:
    """Resolve teacher-bound reports through a grading artifact source."""

    def __init__(
        self,
        artifact_source: GradingArtifactSource,
        bindings: Iterable[TrustedGradingBinding],
    ) -> None:
        self.artifact_source = artifact_source
        self._bindings: dict[tuple[str, str], TrustedGradingBinding] = {}
        for binding in bindings:
            clean = _validated_binding(binding)
            key = (clean.assignment_id, clean.student_id)
            if key in self._bindings:
                raise ValueError(
                    f"Binding grading duplicato per assignment {key[0]} e studente {key[1]}."
                )
            self._bindings[key] = clean

    def resolve(self, request: TrackingReportRequest) -> TrackingReportResult:
        binding = self._bindings.get((request.assignment_id, request.student_id))
        if binding is None:
            return TrackingReportResult(configured=False)
        try:
            _validate_request(request, binding)
            acquired = self.artifact_source.acquire_latest_report(
                binding.workflow_repo_ref,
                binding.artifact_name,
                binding.expected_workflow_head_sha,
                binding.expected_workflow_run_id,
            )
            _validate_acquired_report(acquired.report, acquired.provenance, binding)
        except (GradingArtifactError, ValueError) as error:
            return TrackingReportResult(
                configured=True,
                selection="remote_error",
                authority="remote_configured",
                provisional=not binding.final,
                error=str(error),
            )
        return TrackingReportResult(
            configured=True,
            report=acquired.report,
            selection="github_actions_artifact",
            authority="verified_remote",
            provisional=not binding.final,
            provenance=_tracking_provenance(acquired.provenance, binding),
        )


def _required_text(value: str, field_name: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise ValueError(f"{field_name} obbligatorio nel binding grading.")
    return clean


def _validated_binding(binding: TrustedGradingBinding) -> TrustedGradingBinding:
    activity_id = _required_text(binding.activity_id, "activity_id")
    assignment_id = _required_text(binding.assignment_id, "assignment_id")
    student_id = _required_text(binding.student_id, "student_id")
    student_owner, student_repo = normalize_github_repo_ref(
        _required_text(binding.student_repo_ref, "student_repo_ref")
    )
    workflow_owner, workflow_repo = normalize_github_repo_ref(
        _required_text(binding.workflow_repo_ref, "workflow_repo_ref")
    )
    artifact_name = _required_text(binding.artifact_name, "artifact_name")
    student_head_sha = _required_text(
        binding.expected_student_head_sha,
        "expected_student_head_sha",
    ).lower()
    workflow_head_sha = _required_text(
        binding.expected_workflow_head_sha,
        "expected_workflow_head_sha",
    ).lower()
    if not GIT_SHA_RE.fullmatch(student_head_sha):
        raise ValueError("expected_student_head_sha deve contenere 40 caratteri esadecimali.")
    if not GIT_SHA_RE.fullmatch(workflow_head_sha):
        raise ValueError("expected_workflow_head_sha deve contenere 40 caratteri esadecimali.")
    submitted_at = _required_timestamp(
        binding.expected_submitted_at,
        "expected_submitted_at",
    )
    run_id = binding.expected_workflow_run_id
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise ValueError("expected_workflow_run_id non valido.")
    if not isinstance(binding.final, bool):
        raise ValueError("final deve essere booleano.")
    if not isinstance(binding.final, bool):
        raise ValueError("final deve essere booleano.")
    return TrustedGradingBinding(
        activity_id=activity_id,
        assignment_id=assignment_id,
        student_id=student_id,
        student_repo_ref=f"{student_owner}/{student_repo}",
        workflow_repo_ref=f"{workflow_owner}/{workflow_repo}",
        artifact_name=artifact_name,
        expected_student_head_sha=student_head_sha,
        expected_workflow_head_sha=workflow_head_sha,
        expected_submitted_at=submitted_at,
        expected_workflow_run_id=run_id,
        final=binding.final,
    )


def _validate_request(
    request: TrackingReportRequest,
    binding: TrustedGradingBinding,
) -> None:
    expected = (
        binding.activity_id,
        binding.assignment_id,
        binding.student_id,
    )
    actual = (
        request.activity_id,
        request.assignment_id,
        request.student_id,
    )
    if actual != expected:
        raise ValueError("Binding grading non coerente con assignment o studente.")
    request_repo = str(request.repo_ref or "").strip()
    if request_repo:
        owner, repo = normalize_github_repo_ref(request_repo)
        if f"{owner}/{repo}".lower() != binding.student_repo_ref.lower():
            raise ValueError("Binding grading non coerente con il repository.")


def _validate_acquired_report(report, provenance, binding: TrustedGradingBinding) -> None:  # noqa: ANN001
    test_outcomes = _validate_remote_outcome(report)
    if "teacher_grade" in report:
        raise ValueError(
            "Il report remoto non puo impostare il voto definitivo del docente."
        )
    if "score" in report:
        score = report["score"]
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError("Report remoto con punteggio non valido.")
        if isinstance(score, float) and not math.isfinite(score):
            raise ValueError("Report remoto con punteggio non valido.")
        if not 0 <= score <= 10:
            raise ValueError("Report remoto con punteggio non valido.")
        if not test_outcomes:
            raise ValueError("Report remoto con punteggio senza risultati di test.")
        expected_score = round((sum(test_outcomes) / len(test_outcomes)) * 10, 2)
        if score != expected_score:
            raise ValueError("Report remoto con punteggio non coerente con i test.")
    if report.get("activity_id") != binding.activity_id:
        raise ValueError("Report remoto riferito a una activity diversa.")
    if report.get("assignment_id") != binding.assignment_id:
        raise ValueError("Report remoto riferito a un'assegnazione diversa.")
    raw_student_id = report.get("student_id")
    if not isinstance(raw_student_id, str) or not raw_student_id.strip():
        raise ValueError("Report remoto privo dell'identificativo studente.")
    report_student_id = raw_student_id.strip()
    if report_student_id != binding.student_id:
        raise ValueError("Report remoto riferito a uno studente diverso.")
    raw_commit = report.get("commit")
    if not isinstance(raw_commit, str):
        raise ValueError("Commit del report remoto non valido.")
    commit = raw_commit.strip().lower()
    if commit != binding.expected_student_head_sha:
        raise ValueError("Commit del report remoto diverso dallo SHA autorizzato.")
    raw_submitted_at = report.get("submitted_at")
    if not isinstance(raw_submitted_at, str):
        raise ValueError("Timestamp di consegna del report remoto non valido.")
    if raw_submitted_at.strip() != binding.expected_submitted_at:
        raise ValueError("Timestamp di consegna del report remoto diverso da quello autorizzato.")
    if provenance.repository.lower() != binding.workflow_repo_ref.lower():
        raise ValueError("Provenienza remota riferita a un repository diverso.")
    if provenance.head_sha.lower() != binding.expected_workflow_head_sha:
        raise ValueError("Provenienza remota riferita a uno SHA diverso.")
    if provenance.workflow_run_id != binding.expected_workflow_run_id:
        raise ValueError("Provenienza remota riferita a una workflow run diversa.")
    if provenance.artifact_name != binding.artifact_name:
        raise ValueError("Provenienza remota riferita a un artifact diverso.")


def _validate_remote_outcome(report: dict[str, Any]) -> list[bool]:
    passed = report.get("passed")
    status = report.get("status")
    if (
        not isinstance(passed, bool)
        or not isinstance(status, str)
        or not status.strip()
    ):
        raise ValueError("Report remoto privo dello stato di grading minimo.")
    if passed != (status == "passed"):
        raise ValueError("Report remoto con stato ed esito non coerenti.")

    tests = report.get("tests")
    if status in REMOTE_TERMINAL_STATUSES:
        if passed or ("tests" in report and tests != []) or "summary" in report:
            raise ValueError("Report remoto terminale con risultati di test non coerenti.")
        return []
    if status not in REMOTE_TEST_OUTCOME_STATUSES:
        raise ValueError("Report remoto con stato di grading non riconosciuto.")
    if not isinstance(tests, list) or not tests:
        raise ValueError("Report remoto con elenco test non valido.")
    test_outcomes: list[bool] = []
    for test in tests:
        if not isinstance(test, dict):
            raise ValueError("Report remoto con risultato test non valido.")
        test_passed = test.get("passed")
        test_status = test.get("status")
        if (
            not isinstance(test_passed, bool)
            or not isinstance(test_status, str)
            or test_status not in REMOTE_TEST_RESULT_STATUSES
            or test_passed != (test_status == "passed")
        ):
            raise ValueError("Report remoto con risultato test non valido.")
        test_outcomes.append(test_passed)

    if test_outcomes and passed != all(test_outcomes):
        raise ValueError("Report remoto con test ed esito aggregato non coerenti.")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("Report remoto con riepilogo test non coerente.")
    summary_passed = summary.get("passed")
    summary_total = summary.get("total")
    if (
        not isinstance(summary_passed, int)
        or isinstance(summary_passed, bool)
        or summary_passed < 0
        or not isinstance(summary_total, int)
        or isinstance(summary_total, bool)
        or summary_total < 0
        or summary_passed != sum(test_outcomes)
        or summary_total != len(test_outcomes)
    ):
        raise ValueError("Report remoto con riepilogo test non coerente.")
    return test_outcomes


def _tracking_provenance(provenance, binding: TrustedGradingBinding) -> dict[str, Any]:  # noqa: ANN001
    artifact_provenance = asdict(provenance)
    artifact_repository = artifact_provenance.pop("repository")
    return {
        "source": "github_actions",
        "repository": binding.student_repo_ref,
        "artifact_repository": artifact_repository,
        **artifact_provenance,
    }


def _required_timestamp(value: str, field_name: str) -> str:
    clean = _required_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field_name} deve essere un timestamp ISO-8601 valido.") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} deve includere il fuso orario.")
    return clean
