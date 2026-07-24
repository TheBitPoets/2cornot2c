from __future__ import annotations

from dataclasses import replace

import pytest

from scripts import thebitlab_tracking_reports as tracking_reports
from scripts import grade_activity
from scripts.thebitlab_grading_artifacts import (
    AcquiredGradingReport,
    GradingArtifactError,
    GradingArtifactProvenance,
)


HEAD_SHA = "a" * 40
WORKFLOW_SHA = "b" * 40


class FakeArtifactSource:
    def __init__(self, acquired=None, error: Exception | None = None) -> None:
        self.acquired = acquired
        self.error = error
        self.calls: list[tuple[object, ...]] = []

    def acquire_latest_report(
        self,
        repo_ref,
        artifact_name,
        expected_head_sha,
        expected_workflow_run_id,
    ):  # noqa: ANN001
        self.calls.append(
            (
                repo_ref,
                artifact_name,
                expected_head_sha,
                expected_workflow_run_id,
            )
        )
        if self.error is not None:
            raise self.error
        return self.acquired


def binding(**overrides) -> tracking_reports.TrustedGradingBinding:
    values = {
        "activity_id": "python-base-somma-001",
        "assignment_id": "assignment-001",
        "student_id": "rossi-mario",
        "student_repo_ref": "TheBitPoets/rossi-mario",
        "workflow_repo_ref": "TheBitPoets/2cornot2c",
        "artifact_name": "grading-assignment-001",
        "expected_student_head_sha": HEAD_SHA,
        "expected_workflow_head_sha": WORKFLOW_SHA,
        "expected_workflow_run_id": 900,
        "final": False,
    }
    values.update(overrides)
    return tracking_reports.TrustedGradingBinding(**values)


def report(**overrides) -> dict:
    values = {
        "activity_id": "python-base-somma-001",
        "assignment_id": "assignment-001",
        "student_id": "rossi-mario",
        "commit": HEAD_SHA,
        "status": "passed",
        "passed": True,
        "submitted_at": "2026-10-20T08:00:00+02:00",
        "tests": [{"name": "somma", "status": "passed", "passed": True}],
    }
    values.update(overrides)
    return values


def provenance(**overrides) -> GradingArtifactProvenance:
    values = {
        "repository": "TheBitPoets/2cornot2c",
        "artifact_id": 12,
        "artifact_name": "grading-assignment-001",
        "workflow_run_id": 900,
        "head_sha": WORKFLOW_SHA,
        "created_at": "2026-10-20T08:05:00Z",
        "archive_download_url": (
            "https://api.github.com/repos/TheBitPoets/2cornot2c/actions/artifacts/12/zip"
        ),
        "digest": "sha256:abc",
    }
    values.update(overrides)
    return GradingArtifactProvenance(**values)


def request(**overrides) -> tracking_reports.TrackingReportRequest:
    values = {
        "activity_id": "python-base-somma-001",
        "assignment_id": "assignment-001",
        "student_id": "rossi-mario",
        "repo_ref": "TheBitPoets/rossi-mario",
    }
    values.update(overrides)
    return tracking_reports.TrackingReportRequest(**values)


def test_canonical_tracking_result_rejects_contradictory_remote_states() -> None:
    missing_report = tracking_reports.canonical_tracking_report_result(
        tracking_reports.TrackingReportResult(
            configured=True,
            selection="github_actions_artifact",
            authority="verified_remote",
        )
    )
    missing_provenance = tracking_reports.canonical_tracking_report_result(
        tracking_reports.TrackingReportResult(
            configured=True,
            report={"status": "passed"},
            selection="github_actions_artifact",
            authority="verified_remote",
        )
    )
    invalid_repository = tracking_reports.canonical_tracking_report_result(
        tracking_reports.TrackingReportResult(
            configured=True,
            report={"status": "passed"},
            selection="github_actions_artifact",
            authority="verified_remote",
            provenance={"repository": "not a repository"},
        )
    )

    assert missing_report.selection == "remote_error"
    assert missing_report.authority == "remote_configured"
    assert missing_report.report is None
    assert missing_provenance.selection == "remote_error"
    assert missing_provenance.report is None
    assert "Provenienza" in missing_provenance.error
    assert invalid_repository.selection == "remote_error"
    assert "Repository" in invalid_repository.error


def test_artifact_tracking_source_resolves_verified_remote_report() -> None:
    artifact_source = FakeArtifactSource(
        AcquiredGradingReport(report=report(), provenance=provenance())
    )
    source = tracking_reports.ArtifactTrackingReportSource(
        artifact_source,
        [binding()],
    )

    result = source.resolve(request())

    assert result.configured is True
    assert result.report == report()
    assert result.selection == "github_actions_artifact"
    assert result.authority == "verified_remote"
    assert result.provisional is True
    assert result.error is None
    assert result.provenance["source"] == "github_actions"
    assert result.provenance["repository"] == "TheBitPoets/rossi-mario"
    assert result.provenance["artifact_repository"] == "TheBitPoets/2cornot2c"
    assert result.provenance["artifact_id"] == 12
    assert artifact_source.calls == [
        (
            "TheBitPoets/2cornot2c",
            "grading-assignment-001",
            WORKFLOW_SHA,
            900,
        )
    ]


def test_grader_report_is_accepted_after_workflow_metadata_enrichment(tmp_path) -> None:
    source_path = tmp_path / "main.py"
    source_path.write_text("print(5)\n", encoding="utf-8")
    produced = grade_activity.grade_activity(
        {
            "id": "python-base-somma-001",
            "linguaggio": "python",
            "test_cases": [{"name": "output", "expected_stdout": "5\n"}],
        },
        source_path,
    )
    produced = grade_activity.with_report_metadata(
        produced,
        assignment_id="assignment-001",
        student_id="rossi-mario",
        commit=HEAD_SHA,
    )
    source = tracking_reports.ArtifactTrackingReportSource(
        FakeArtifactSource(
            AcquiredGradingReport(report=produced, provenance=provenance())
        ),
        [binding()],
    )

    result = source.resolve(request())

    assert result.selection == "github_actions_artifact"
    assert result.authority == "verified_remote"
    assert result.report["passed"] is True


def test_artifact_tracking_source_skips_students_without_binding() -> None:
    artifact_source = FakeArtifactSource()
    source = tracking_reports.ArtifactTrackingReportSource(
        artifact_source,
        [binding()],
    )

    result = source.resolve(request(student_id="bianchi-luca"))

    assert result == tracking_reports.TrackingReportResult(configured=False)
    assert artifact_source.calls == []


@pytest.mark.parametrize(
    ("changed_report", "changed_provenance", "message"),
    [
        ({"activity_id": "other"}, {}, "activity diversa"),
        ({"assignment_id": "other"}, {}, "assegnazione diversa"),
        ({"student_id": ""}, {}, "privo dell'identificativo studente"),
        ({"student_id": "bianchi-luca"}, {}, "studente diverso"),
        ({"commit": "b" * 40}, {}, "Commit"),
        ({}, {"repository": "TheBitPoets/altro"}, "repository diverso"),
        ({}, {"head_sha": "c" * 40}, "SHA diverso"),
        ({}, {"workflow_run_id": 901}, "workflow run diversa"),
        ({}, {"artifact_name": "altro"}, "artifact diverso"),
    ],
)
def test_artifact_tracking_source_fails_closed_on_mismatched_report_or_provenance(
    changed_report: dict,
    changed_provenance: dict,
    message: str,
) -> None:
    acquired = AcquiredGradingReport(
        report=report(**changed_report),
        provenance=provenance(**changed_provenance),
    )
    source = tracking_reports.ArtifactTrackingReportSource(
        FakeArtifactSource(acquired),
        [binding(final=True)],
    )

    result = source.resolve(request())

    assert result.configured is True
    assert result.report is None
    assert result.selection == "remote_error"
    assert result.authority == "remote_configured"
    assert result.provisional is False
    assert message in result.error


def test_artifact_tracking_source_normalizes_expected_acquisition_error() -> None:
    source = tracking_reports.ArtifactTrackingReportSource(
        FakeArtifactSource(error=GradingArtifactError("artifact non disponibile")),
        [binding()],
    )

    result = source.resolve(request())

    assert result.configured is True
    assert result.report is None
    assert result.selection == "remote_error"
    assert result.authority == "remote_configured"
    assert result.error == "artifact non disponibile"


def test_artifact_tracking_source_accepts_missing_runtime_repo_when_binding_is_trusted() -> None:
    artifact_source = FakeArtifactSource(
        AcquiredGradingReport(report=report(), provenance=provenance())
    )
    source = tracking_reports.ArtifactTrackingReportSource(
        artifact_source,
        [binding()],
    )

    result = source.resolve(request(repo_ref=""))

    assert result.configured is True
    assert result.authority == "verified_remote"


def test_artifact_tracking_source_rejects_duplicate_or_invalid_bindings() -> None:
    artifact_source = FakeArtifactSource()
    with pytest.raises(ValueError, match="duplicato"):
        tracking_reports.ArtifactTrackingReportSource(
            artifact_source,
            [binding(), replace(binding(), final=True)],
        )
    with pytest.raises(ValueError, match="40 caratteri"):
        tracking_reports.ArtifactTrackingReportSource(
            artifact_source,
            [binding(expected_student_head_sha="abc")],
        )
