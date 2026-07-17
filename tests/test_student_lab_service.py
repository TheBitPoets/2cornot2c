from __future__ import annotations

import json

from scripts import assignment_records, student_help_service, student_lab_service, student_support_policy


def write_activity(root, activity_id: str = "python-base-somma-001", student_support_mode: str = "") -> str:
    """Write a minimal activity and return its repository-relative path."""

    path = root / "activities" / f"{activity_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": activity_id,
                "title": "Somma in Python",
                "kind": "laboratorio",
                "difficulty": "B",
                "topics": ["variabili", "input-output"],
                "language": "python",
                "source_name": "main.py",
                "instructions": "Scrivi un programma che stampa una somma.",
                "student_support_mode": student_support_mode,
                "grading_policy": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return f"activities/{activity_id}.json"


def sample_assignment(root, **overrides):
    """Return a valid assignment record for lab tests."""

    activity_path = overrides.get("activity_path") or write_activity(root)
    payload = {
        "activity_id": "python-base-somma-001",
        "activity_path": activity_path,
        "target_type": "group",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "targets": [
            {
                "student_id": "rossi-mario",
                "display_name": "Rossi Mario",
                "repo_ref": "TheBitPoets/rossi-mario",
                "path": "examples/assignment_tracking/student_repos/rossi-mario",
            },
            {
                "student_id": "bianchi-luca",
                "display_name": "Bianchi Luca",
                "repo_ref": "TheBitPoets/bianchi-luca",
                "path": "examples/assignment_tracking/student_repos/bianchi-luca",
            },
        ],
    }
    payload.update(overrides)
    return assignment_records.build_assignment_record(**payload)


def write_assignment(root, assignment):
    """Persist one assignment record in the temporary root."""

    storage = assignment_records.JsonAssignmentRecordStorage(root)
    return storage.write_assignment(assignment)


def test_student_lab_lists_only_requested_student_assignments(tmp_path) -> None:
    write_assignment(tmp_path, sample_assignment(tmp_path))
    workspace = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario" / "assignments" / "python-base-somma-001"
    workspace.mkdir(parents=True)

    payload = student_lab_service.student_lab_payload(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-18T12:00:00+02:00",
    )

    assert payload["schema_version"] == "student_lab.v1"
    assert payload["student_id"] == "rossi-mario"
    assert len(payload["assignments"]) == 1
    assignment = payload["assignments"][0]
    assert assignment["assignment_id"].startswith("assignment-python-base-somma-001-group-")
    assert assignment["activity_id"] == "python-base-somma-001"
    assert assignment["title"] == "Somma in Python"
    assert assignment["status"] == "pending"
    assert assignment["submitted"] is False
    assert assignment["workspace"] == {
        "path": "examples/assignment_tracking/student_repos/rossi-mario/assignments/python-base-somma-001",
        "exists": True,
    }
    assert assignment["activity"]["exists"] is True
    assert assignment["activity"]["language"] == "python"
    assert assignment["support_policy"]["label"] == "Feedback tecnico"
    assert assignment["support_policy"]["debug_allowed"] is True
    assert assignment["report"]["exists"] is False
    assert assignment["runner"]["status"] == "not_run"


def test_student_lab_exposes_explicit_support_policy(tmp_path) -> None:
    activity_id = "python-ai-assisted-001"
    activity_path = write_activity(tmp_path, activity_id=activity_id, student_support_mode="ai-assisted")
    write_assignment(tmp_path, sample_assignment(tmp_path, activity_id=activity_id, activity_path=activity_path))

    assignment = student_lab_service.list_student_lab_assignments(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-18T12:00:00+02:00",
    )[0]

    assert assignment["activity_id"] == activity_id
    assert assignment["student_support_mode"] == "ai-assisted"
    assert assignment["support_policy"]["label"] == "AI assisted"
    assert assignment["support_policy"]["ai_allowed"] is True
    assert assignment["support_policy"]["ai_request_limit"] == 5
    assert "suggerimenti AI controllati" in assignment["support_policy"]["allowed"]


def test_student_lab_marks_missing_after_due_date_without_report(tmp_path) -> None:
    write_assignment(tmp_path, sample_assignment(tmp_path))

    assignments = student_lab_service.list_student_lab_assignments(
        root=tmp_path,
        student_id="bianchi-luca",
        now="2026-10-20T12:00:00+02:00",
    )

    assert len(assignments) == 1
    assert assignments[0]["status"] == "missing"
    assert assignments[0]["workspace"]["exists"] is False
    assert assignments[0]["grading"]["status"] == "not_graded"


def test_student_lab_uses_existing_report_and_grading_summary(tmp_path) -> None:
    write_assignment(tmp_path, sample_assignment(tmp_path))
    repo = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario"
    workspace = repo / "assignments" / "python-base-somma-001"
    report_path = repo / "reports" / "python-base-somma-001" / "latest.json"
    workspace.mkdir(parents=True)
    report_path.parent.mkdir(parents=True)
    (workspace / "main.py").write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "status": "passed",
                "passed": True,
                "source": "assignments/python-base-somma-001/main.py",
                "submitted_at": "2026-10-18T18:00:00+02:00",
                "commit": "abc1234",
                "summary": {"passed": 2, "total": 2},
                "tests": [
                    {"name": "somma positiva", "status": "passed", "passed": True},
                    {"name": "somma negativa", "status": "passed", "passed": True},
                ],
            }
        ),
        encoding="utf-8",
    )

    assignments = student_lab_service.list_student_lab_assignments(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-20T12:00:00+02:00",
    )

    assignment = assignments[0]
    assert assignment["status"] == "submitted"
    assert assignment["submitted"] is True
    assert assignment["report"]["path"] == "examples/assignment_tracking/student_repos/rossi-mario/reports/python-base-somma-001/latest.json"
    assert assignment["report"]["submitted_at"] == "2026-10-18T18:00:00+02:00"
    assert assignment["report"]["commit"] == "abc1234"
    assert assignment["grading"]["status"] == "graded_passed"
    assert assignment["grading"]["tests_passed"] == 2
    assert assignment["grading"]["tests_total"] == 2


def test_student_lab_exposes_help_summary(tmp_path) -> None:
    activity_path = write_activity(tmp_path, student_support_mode="studio-guidato")
    write_assignment(tmp_path, sample_assignment(tmp_path, activity_path=activity_path))
    repo = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario"
    policy = student_support_policy.support_policy("studio-guidato")
    student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="teoria",
        prompt="Ripassami gli array.",
        now="2026-10-18T17:15:00+02:00",
    )
    student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Scrivi la soluzione.",
        now="2026-10-18T17:20:00+02:00",
    )

    assignment = student_lab_service.list_student_lab_assignments(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-18T18:00:00+02:00",
    )[0]

    assert assignment["help"]["path"] == "examples/assignment_tracking/student_repos/rossi-mario/help/python-base-somma-001/events.json"
    assert assignment["help"]["total"] == 2
    assert assignment["help"]["allowed"] == 1
    assert assignment["help"]["denied"] == 1
    assert assignment["help"]["last_decision"] == "bloccata"
    assert assignment["help"]["counts"] == {"teoria": 1, "ai": 1}
    assert assignment["help"]["ai_budget"] == {"limit": 0, "used": 0, "remaining": 0, "exhausted": False}


def test_student_lab_exposes_ai_budget_summary(tmp_path) -> None:
    activity_path = write_activity(tmp_path, student_support_mode="ai-assisted")
    write_assignment(tmp_path, sample_assignment(tmp_path, activity_path=activity_path))
    repo = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario"
    policy = student_support_policy.support_policy("ai-assisted")
    student_help_service.record_help_request(
        repo_path=repo,
        activity_id="python-base-somma-001",
        support_policy=policy,
        help_type="ai",
        prompt="Dammi un suggerimento.",
        now="2026-10-18T17:15:00+02:00",
    )

    assignment = student_lab_service.list_student_lab_assignments(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-18T18:00:00+02:00",
    )[0]

    assert assignment["help"]["ai_budget"] == {"limit": 5, "used": 1, "remaining": 4, "exhausted": False}


def test_student_lab_keeps_assignment_when_local_repo_path_is_only_inferred(tmp_path) -> None:
    write_assignment(
        tmp_path,
        sample_assignment(
            tmp_path,
            target_type="student",
            targets=[{"student_id": "neri-giulia", "repo_ref": "TheBitPoets/neri-giulia"}],
        ),
    )

    assignments = student_lab_service.list_student_lab_assignments(
        root=tmp_path,
        student_id="neri-giulia",
        now="2026-10-18T12:00:00+02:00",
    )

    assert len(assignments) == 1
    assert assignments[0]["workspace"]["path"] == "examples/assignment_tracking/student_repos/neri-giulia/assignments/python-base-somma-001"
    assert assignments[0]["workspace"]["exists"] is False


def test_student_lab_rejects_missing_student_id(tmp_path) -> None:
    try:
        student_lab_service.list_student_lab_assignments(root=tmp_path, student_id="")
    except ValueError as error:
        assert "student_id obbligatorio" in str(error)
    else:
        raise AssertionError("student lab should require a student id")
