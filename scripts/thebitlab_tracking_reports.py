"""Application adapter for authoritative remote grading reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any, Iterable, Protocol

from scripts.thebitlab_grading_artifacts import (
    GradingArtifactError,
    GradingArtifactSource,
)
from scripts.thebitlab_repository_providers import normalize_github_repo_ref


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
    if report.get("activity_id") != binding.activity_id:
        raise ValueError("Report remoto riferito a una activity diversa.")
    if report.get("assignment_id") != binding.assignment_id:
        raise ValueError("Report remoto riferito a un'assegnazione diversa.")
    report_student_id = str(report.get("student_id", "") or "").strip()
    if not report_student_id:
        raise ValueError("Report remoto privo dell'identificativo studente.")
    if report_student_id != binding.student_id:
        raise ValueError("Report remoto riferito a uno studente diverso.")
    commit = str(report.get("commit", "")).strip().lower()
    if commit != binding.expected_student_head_sha:
        raise ValueError("Commit del report remoto diverso dallo SHA autorizzato.")
    if str(report.get("submitted_at", "") or "").strip() != binding.expected_submitted_at:
        raise ValueError("Timestamp di consegna del report remoto diverso da quello autorizzato.")
    if provenance.repository.lower() != binding.workflow_repo_ref.lower():
        raise ValueError("Provenienza remota riferita a un repository diverso.")
    if provenance.head_sha.lower() != binding.expected_workflow_head_sha:
        raise ValueError("Provenienza remota riferita a uno SHA diverso.")
    if provenance.workflow_run_id != binding.expected_workflow_run_id:
        raise ValueError("Provenienza remota riferita a una workflow run diversa.")
    if provenance.artifact_name != binding.artifact_name:
        raise ValueError("Provenienza remota riferita a un artifact diverso.")


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
