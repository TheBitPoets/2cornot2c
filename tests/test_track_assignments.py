from __future__ import annotations

import json
import sys

from scripts import assignment_records, student_help_service, student_identity, student_support_policy, track_assignments
from scripts.thebitlab_repository_providers import LocalRepositoryProvider, StudentRepository


def test_parse_args_exposes_server_help_storage_options(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "track_assignments.py",
            "--activity",
            "activity.json",
            "--output",
            "report.json",
            "--assignment-id",
            "assignment-001",
            "--server-root",
            str(tmp_path),
        ],
    )

    args = track_assignments.parse_args()

    assert args.assignment_id == "assignment-001"
    assert args.server_root == tmp_path


def activity() -> dict:
    """Return a minimal valid activity for tracking tests."""
    return {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "titolo": "Somma in Python",
        "tipo": "compito-casa",
        "difficolta": "B",
        "argomenti": ["variabili", "input-output"],
        "linguaggio": "python",
        "consegna": "Scrivi un programma Python che stampa una somma.",
        "correzione": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 20,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
    }


def write_activity(tmp_path):
    """Write a valid activity JSON and return its path."""
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(activity()), encoding="utf-8")
    return path


def target(tmp_path, name: str) -> track_assignments.TrackingTarget:
    """Return a tracking target rooted in tmp_path."""
    root = tmp_path / name
    return track_assignments.TrackingTarget(student=name, repo=f"TheBitPoets/{name}", path=root)


def test_github_file_path_uses_project_root_for_repo_relative_paths(tmp_path, monkeypatch) -> None:
    project_root = tmp_path / "project"
    source_path = (
        project_root
        / "examples"
        / "assignment_tracking"
        / "student_repos"
        / "bianchi-luca"
        / "assignments"
        / "python-base-somma-001"
        / "main.py"
    )
    scripts_dir = project_root / "scripts"
    source_path.parent.mkdir(parents=True)
    scripts_dir.mkdir()
    source_path.write_text("print(3)\n", encoding="utf-8")
    student = track_assignments.TrackingTarget(
        student="bianchi-luca",
        repo="TheBitPoets/2cornot2c",
        path=project_root / "examples" / "assignment_tracking" / "student_repos" / "bianchi-luca",
    )
    monkeypatch.setattr(track_assignments, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(track_assignments, "git_root", lambda path: project_root)
    monkeypatch.chdir(scripts_dir)

    path = track_assignments.github_file_path(
        student,
        "examples/assignment_tracking/student_repos/bianchi-luca/assignments/python-base-somma-001/main.py",
    )

    assert path == "examples/assignment_tracking/student_repos/bianchi-luca/assignments/python-base-somma-001/main.py"


class MissingPathProvider:
    provider_name = "missing-path"

    def list_student_repositories(self, class_ref: str | None = None) -> list[StudentRepository]:
        return [StudentRepository(student_id="rossi-mario", repo_ref="TheBitPoets/rossi-mario", provider=self.provider_name)]

    def resolve_student_repository(self, student_id: str) -> StudentRepository:
        return self.list_student_repositories()[0]


def write_report(root, submitted_at: str, passed: bool = True) -> None:
    """Write a local grading report in the default report location."""
    report_path = root / "reports" / "python-base-somma-001" / "latest.json"
    source_path = root / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "activity_id": "python-base-somma-001",
                "source": str(source_path),
                "submitted_at": submitted_at,
                "commit": "abc1234",
                "summary": {
                    "passed": 2 if passed else 1,
                    "total": 2,
                },
                "tests": [
                    {"name": "somma positiva", "passed": True, "status": "passed"},
                    {"name": "somma con negativo", "passed": passed, "status": "passed" if passed else "failed"},
                ],
            }
        ),
        encoding="utf-8",
    )


def write_report_with_activity_id(root, activity_id: str) -> None:
    """Write a local grading report with a configurable activity id."""
    report_path = root / "reports" / "python-base-somma-001" / "latest.json"
    source_path = root / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "passed": True,
                "status": "passed",
                "activity_id": activity_id,
                "source": str(source_path),
                "submitted_at": "2026-10-18T18:22:10+02:00",
                "commit": "abc1234",
            }
        ),
        encoding="utf-8",
    )


def write_report_without_activity_id(root) -> None:
    """Write a local grading report without activity id."""
    report_path = root / "reports" / "python-base-somma-001" / "latest.json"
    source_path = root / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "passed": True,
                "status": "passed",
                "source": str(source_path),
                "submitted_at": "2026-10-18T18:22:10+02:00",
                "commit": "abc1234",
            }
        ),
        encoding="utf-8",
    )


def test_load_targets_from_local_repository_provider(tmp_path) -> None:
    (tmp_path / "rossi-mario").mkdir()
    (tmp_path / "bianchi-luca").mkdir()
    provider = LocalRepositoryProvider(tmp_path)

    targets = track_assignments.load_targets_from_provider(provider)

    assert targets == [
        track_assignments.TrackingTarget(
            student="bianchi-luca",
            repo="bianchi-luca",
            path=(tmp_path / "bianchi-luca").resolve(),
        ),
        track_assignments.TrackingTarget(
            student="rossi-mario",
            repo="rossi-mario",
            path=(tmp_path / "rossi-mario").resolve(),
        ),
    ]


def test_load_targets_from_provider_requires_local_path() -> None:
    try:
        track_assignments.load_targets_from_provider(MissingPathProvider())
    except ValueError as error:
        assert "Repository senza path locale" in str(error)
    else:
        raise AssertionError("load_targets_from_provider should reject repositories without a local path")


def test_track_assignments_marks_submitted_on_time(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "submitted_on_time"
    assert row["submitted"] is True
    assert row["late"] is False
    assert row["grading"]["status"] == "graded_passed"
    assert row["grading"]["tests_passed"] == 2
    assert row["ai_feedback"]["status"] == "not_generated"
    assert row["submission"]["files"][0]["path"].endswith("assignments/python-base-somma-001/main.py")
    assert row["submission"]["files"][0]["role"] == "solution"


def test_track_assignments_records_explicit_class_metadata(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        class_id="3A-TPSI",
        class_label="3A TPSI",
        github_team="team-3a-tpsi",
    )

    assert index["class_id"] == "3A-TPSI"
    assert index["class_label"] == "3A TPSI"
    assert index["github_team"] == "team-3a-tpsi"


def test_track_assignments_uses_activity_context_class_metadata(tmp_path) -> None:
    payload = activity()
    payload["contesto"] = {
        "classe": "4A-INF",
        "team_github": "team-4a-inf",
    }
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")
    student = target(tmp_path, "rossi-mario")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
    )

    assert index["class_id"] == "4A-INF"
    assert index["class_label"] == "4A-INF"
    assert index["github_team"] == "team-4a-inf"


def test_track_assignments_uses_canonical_activity_metadata(tmp_path) -> None:
    payload = {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "title": "Somma canonica",
        "kind": "verifica-pratica",
        "difficulty": "B",
        "topics": ["variabili", "input-output"],
        "language": "python",
        "instructions": "Scrivi un programma Python che stampa una somma.",
        "grading_policy": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "student_support_mode": "senza-aiuto",
        "class_id": "5A-INF",
        "github_team": "team-5a-inf",
    }
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")
    student = target(tmp_path, "rossi-mario")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
    )

    assert index["title"] == "Somma canonica"
    assert index["kind"] == "verifica-pratica"
    assert index["student_support_mode"] == "senza-aiuto"
    assert index["class_id"] == "5A-INF"
    assert index["class_label"] == "5A-INF"
    assert index["github_team"] == "team-5a-inf"


def test_track_assignments_rejects_invalid_canonical_kind(tmp_path) -> None:
    payload = activity()
    payload["tipo"] = "compito-casa"
    payload["kind"] = "compito-classe"
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[],
        )
    except ValueError as error:
        assert "kind non ammesso: compito-classe" in str(error)
    else:
        raise AssertionError("track_assignments should reject invalid canonical kind")


def test_track_assignments_lists_multiple_submission_files(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")
    assignment_dir = student.path / "assignments" / "python-base-somma-001"
    (assignment_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (assignment_dir / "README.md").write_text("# Note\n", encoding="utf-8")
    (assignment_dir / "__pycache__").mkdir()
    (assignment_dir / "__pycache__" / "utils.cpython-310.pyc").write_bytes(b"cache")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    files = index["students"][0]["submission"]["files"]
    paths = [file_entry["path"] for file_entry in files]
    assert any(path.endswith("assignments/python-base-somma-001/main.py") for path in paths)
    assert any(path.endswith("assignments/python-base-somma-001/utils.py") for path in paths)
    assert any(path.endswith("assignments/python-base-somma-001/README.md") for path in paths)
    assert not any("__pycache__" in path for path in paths)


def test_track_assignments_resolves_relative_report_source_from_student_repo(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")
    report_path = student.path / "reports" / "python-base-somma-001" / "latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["source"] = "assignments/python-base-somma-001/main.py"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    files = index["students"][0]["submission"]["files"]
    source_files = [
        file_entry for file_entry in files
        if file_entry["path"].endswith("assignments/python-base-somma-001/main.py")
    ]
    assert len(source_files) == 1
    assert source_files[0]["role"] == "solution"


def test_track_assignments_uses_report_file_manifest_when_available(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-18T18:22:10+02:00")
    report_path = student.path / "reports" / "python-base-somma-001" / "latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["files"] = [
        {"path": "assignments/python-base-somma-001/main.py", "role": "solution"},
        {"path": "assignments/python-base-somma-001/utils.py", "role": "support"},
    ]
    report_path.write_text(json.dumps(report), encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    files = index["students"][0]["submission"]["files"]
    assert [(file_entry["path"], file_entry["role"]) for file_entry in files] == [
        ("assignments/python-base-somma-001/main.py", "solution"),
        ("assignments/python-base-somma-001/utils.py", "support"),
    ]


def test_track_assignments_marks_pending_before_due_date(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
        now="2026-10-18T12:00:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "pending"
    assert row["submitted"] is False
    assert row["late"] is False


def test_track_assignments_does_not_count_scaffold_as_submission(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")
    assignment_dir = student.path / "assignments" / "python-base-somma-001"
    assignment_dir.mkdir(parents=True)
    (assignment_dir / "main.py").write_text("# starter\n", encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
        now="2026-10-18T12:00:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "pending"
    assert row["submitted"] is False
    assert row["submission"]["source_path"] is None


def test_track_assignments_marks_missing_after_due_date(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
        now="2026-10-20T12:00:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "missing"
    assert row["submitted"] is False
    assert row["grading"]["status"] == "not_graded"


def test_track_assignments_rejects_naive_now_when_due_has_timezone(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "bianchi-luca")

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
            now="2026-10-18T12:00:00",
        )
    except ValueError as error:
        assert "now deve includere il timezone" in str(error)
    else:
        raise AssertionError("track_assignments should reject now without timezone")


def test_track_assignments_rejects_naive_submitted_at_when_due_has_timezone(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report(student.path, "2026-10-20T08:00:00", passed=False)

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
        )
    except ValueError as error:
        assert "submitted_at deve includere il timezone" in str(error)
    else:
        raise AssertionError("track_assignments should reject submitted_at without timezone")


def test_track_assignments_marks_submitted_late(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report(student.path, "2026-10-20T08:00:00+02:00", passed=False)

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-19T23:59:00+02:00",
    )

    row = index["students"][0]
    assert row["status"] == "submitted_late"
    assert row["late"] is True
    assert row["grading"]["status"] == "graded_failed"


def test_track_assignments_uses_technical_grading_adapter_for_infrastructure_errors(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    report_path = student.path / "reports" / "python-base-somma-001" / "latest.json"
    source_path = student.path / "assignments" / "python-base-somma-001" / "main.py"
    report_path.parent.mkdir(parents=True)
    source_path.parent.mkdir(parents=True)
    source_path.write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "passed": False,
                "status": "unsupported-language",
                "language": "python",
                "source": str(source_path),
                "submitted_at": "2026-10-20T08:00:00+02:00",
                "error": "Runner non ancora implementato per il linguaggio: python",
                "tests": [],
            }
        ),
        encoding="utf-8",
    )

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-21T08:00:00+02:00",
        now="2026-10-20T08:00:00+02:00",
    )

    grading = index["students"][0]["grading"]

    assert grading["status"] == "not_run"
    assert grading["passed"] is None
    assert grading["report_status"] == "unsupported-language"


def test_track_assignments_exposes_student_lab_report_metadata(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    write_report(student.path, "2026-10-20T08:00:00+02:00", passed=True)
    report_path = student.path / "reports" / "python-base-somma-001" / "latest.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["schema_version"] = "student_lab_run.v1"
    report["backend"] = "docker"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-21T08:00:00+02:00",
        now="2026-10-20T09:00:00+02:00",
    )

    row = index["students"][0]

    assert row["report_path"] == "reports/python-base-somma-001/latest.json"
    assert row["submission"]["report_path"] == "reports/python-base-somma-001/latest.json"
    assert row["submission"]["report_backend"] == "docker"
    assert row["submission"]["report_schema_version"] == "student_lab_run.v1"
    assert row["submission"]["report_status"] == "passed"
    assert row["grading"]["status"] == "graded_passed"


def test_track_assignments_exposes_student_help_requests(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "rossi-mario")
    policy = student_support_policy.support_policy("studio-guidato")
    student_help_service.record_help_request(
        repo_path=student.path,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="teoria",
        prompt="Puoi ricordarmi come funziona input()?",
        now="2026-10-20T08:10:00+02:00",
    )
    student_help_service.record_help_request(
        repo_path=student.path,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Scrivimi la soluzione completa.",
        now="2026-10-20T08:15:00+02:00",
    )

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        due_at="2026-10-21T08:00:00+02:00",
        now="2026-10-20T09:00:00+02:00",
    )

    help_summary = index["students"][0]["help"]

    assert help_summary["path"] == "help/python-base-somma-001/events.json"
    assert help_summary["activity_id"] == "python-base-somma-001"
    assert help_summary["total"] == 2
    assert help_summary["ai_total"] == 1
    assert help_summary["allowed"] == 1
    assert help_summary["denied"] == 1
    assert help_summary["events"][0]["prompt"] == "Puoi ricordarmi come funziona input()?"
    assert help_summary["events"][1]["prompt"] == "Scrivimi la soluzione completa."
    assert help_summary["events"][1]["allowed"] is False


def test_track_assignments_uses_stable_assignment_student_id_for_server_help(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "cartella-repository")
    assignment_id = "assignment-stable-student"
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id=assignment_id,
            activity_id="python-base-somma-001",
            activity_path=str(activity_path.relative_to(tmp_path)),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-21T08:00:00+02:00",
            targets=[
                {
                    "student_id": "studente-stabile-001",
                    "repo_ref": student.repo,
                    "path": str(student.path.relative_to(tmp_path)),
                }
            ],
        )
    )
    policy = student_support_policy.support_policy("studio-guidato")
    student_help_service.record_help_request(
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="teoria",
        prompt="Come funziona input()?",
        now="2026-10-20T08:10:00+02:00",
        log_path=student_help_service.server_help_log_path(
            tmp_path,
            "studente-stabile-001",
            assignment_id,
        ),
    )

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        assignment_id=assignment_id,
        server_root=tmp_path,
        due_at="2026-10-21T08:00:00+02:00",
        now="2026-10-20T09:00:00+02:00",
    )

    help_summary = index["students"][0]["help"]
    assert help_summary["total"] == 1
    assert help_summary["events"][0]["prompt"] == "Come funziona input()?"
    assert "studente-stabile-001" in help_summary["path"]


def test_track_assignments_uses_canonical_legacy_identity_for_server_help(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "Mario Rossi")
    assignment_id = "assignment-legacy-student"
    relative_student_path = str(student.path.relative_to(tmp_path))
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id=assignment_id,
            activity_id="python-base-somma-001",
            activity_path=str(activity_path.relative_to(tmp_path)),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-21T08:00:00+02:00",
            targets=[{"path": relative_student_path}],
        )
    )
    canonical_student_id = student_identity.legacy_display_student_id("Mario Rossi")
    policy = student_support_policy.support_policy("studio-guidato")
    student_help_service.record_help_request(
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="teoria",
        prompt="Come funziona input()?",
        now="2026-10-20T08:10:00+02:00",
        log_path=student_help_service.server_help_log_path(
            tmp_path,
            canonical_student_id,
            assignment_id,
        ),
    )

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        assignment_id=assignment_id,
        server_root=tmp_path,
        due_at="2026-10-21T08:00:00+02:00",
        now="2026-10-20T09:00:00+02:00",
    )

    help_summary = index["students"][0]["help"]
    assert help_summary["total"] == 1
    assert help_summary["events"][0]["prompt"] == "Come funziona input()?"
    assert canonical_student_id in help_summary["path"]


def test_track_assignments_matches_legacy_target_field_for_server_help(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "Mario Rossi")
    assignment_id = "assignment-legacy-target-field"
    relative_student_path = str(student.path.relative_to(tmp_path))
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id=assignment_id,
            activity_id="python-base-somma-001",
            activity_path=str(activity_path.relative_to(tmp_path)),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-21T08:00:00+02:00",
            targets=[{"target": relative_student_path}],
        )
    )
    canonical_student_id = student_identity.legacy_display_student_id("Mario Rossi")
    student_help_service.record_help_request(
        activity_id="python-base-somma-001",
        support_policy=student_support_policy.support_policy("studio-guidato"),
        help_type="teoria",
        prompt="Richiesta dal target legacy.",
        now="2026-10-20T08:10:00+02:00",
        log_path=student_help_service.server_help_log_path(tmp_path, canonical_student_id, assignment_id),
    )

    index = track_assignments.track_assignments(
        activity_path=activity_path,
        targets=[student],
        assignment_id=assignment_id,
        server_root=tmp_path,
        due_at="2026-10-21T08:00:00+02:00",
        now="2026-10-20T09:00:00+02:00",
    )

    assert index["students"][0]["help"]["total"] == 1
    assert index["students"][0]["help"]["events"][0]["prompt"] == "Richiesta dal target legacy."


def test_assignment_student_id_does_not_match_a_different_path_by_basename(tmp_path) -> None:
    tracked_path = tmp_path / "classe-b" / "rossi"
    tracked_path.mkdir(parents=True)
    tracked = track_assignments.TrackingTarget(
        student="rossi",
        repo="TheBitPoets/classe-b-rossi",
        path=tracked_path,
    )
    assignment = {
        "targets": [
            {"student_id": "rossi-classe-a", "target": "classe-a/rossi"},
            {"student_id": "rossi-classe-b", "target": "classe-b/rossi"},
        ]
    }

    student_id = track_assignments.assignment_student_id(tracked, assignment, tmp_path)

    assert student_id == "rossi-classe-b"


def test_track_assignments_rejects_report_for_different_activity(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report_with_activity_id(student.path, "altra-activity")

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
        )
    except ValueError as error:
        assert "Report non coerente" in str(error)
        assert "python-base-somma-001" in str(error)
        assert "altra-activity" in str(error)
    else:
        raise AssertionError("track_assignments should reject reports for a different activity")


def test_track_assignments_rejects_report_without_activity_id(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    student = target(tmp_path, "verdi-anna")
    write_report_without_activity_id(student.path)

    try:
        track_assignments.track_assignments(
            activity_path=activity_path,
            targets=[student],
            due_at="2026-10-19T23:59:00+02:00",
        )
    except ValueError as error:
        assert "Report non coerente" in str(error)
        assert "manca activity_id" in str(error)
    else:
        raise AssertionError("track_assignments should reject reports without activity_id")


def test_write_tracking_index_creates_parent_directories(tmp_path) -> None:
    output = tmp_path / "teacher-reports" / "3A" / "index.json"
    index = {"activity_id": "python-base-somma-001", "students": []}

    track_assignments.write_tracking_index(index, output)

    assert json.loads(output.read_text(encoding="utf-8")) == index
