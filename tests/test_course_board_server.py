from __future__ import annotations

import json

from scripts import assignment_records, course_board_server


def test_assignment_overview_lists_students_across_saved_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "python-base-somma-001.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "class_id": "3A-TPSI",
                "class_label": "3A TPSI",
                "github_team": "team-3a-tpsi",
                "kind": "compito-casa",
                "student_support_mode": "guidato",
                "assigned_at": "2026-10-12T09:00:00+02:00",
                "due_at": "2026-10-19T23:59:00+02:00",
                "students": [
                    {
                        "student": "rossi-mario",
                        "repo": "TheBitPoets/rossi-mario",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "submission": {
                            "submitted_at": "2026-10-18T18:22:10+02:00",
                            "commit": "abc1234",
                            "source_path": "assignments/python-base-somma-001/main.py",
                        },
                        "grading": {
                            "status": "graded_passed",
                            "tests_passed": 2,
                            "tests_total": 2,
                            "teacher_grade": 9,
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "status": "submitted_late",
                        "submitted": True,
                        "late": True,
                        "grading": {
                            "status": "graded_failed",
                            "tests_passed": 1,
                            "tests_total": 2,
                            "failed_tests": ["somma numeri negativi"],
                            "score": 5,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = course_board_server.assignment_overview()

    assert len(rows) == 2
    assert rows[0]["report_name"] == "demo/python-base-somma-001.json"
    assert rows[0]["activity_id"] == "python-base-somma-001"
    assert rows[0]["class_id"] == "3A-TPSI"
    assert rows[0]["class_label"] == "3A TPSI"
    assert rows[0]["github_team"] == "team-3a-tpsi"
    assert rows[0]["kind"] == "compito-casa"
    assert rows[0]["student_support_mode"] == "guidato"
    assert rows[0]["student"] == "rossi-mario"
    assert rows[0]["tests_passed"] == 2
    assert rows[0]["teacher_grade"] == 9
    assert rows[1]["student"] == "bianchi-luca"
    assert rows[1]["late"] is True
    assert rows[1]["failed_tests"] == ["somma numeri negativi"]
    assert rows[1]["score"] == 5


def test_list_assignment_reports_counts_late_only_for_submitted_students(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "class_id": "4A-INF",
                "class_label": "4A INF",
                "github_team": "team-4a-inf",
                "students": [
                    {"student": "rossi-mario", "status": "submitted_late", "submitted": True, "late": True},
                    {"student": "bianchi-luca", "status": "missing", "submitted": False, "late": True},
                    {"student": "verdi-anna", "status": "submitted_on_time", "submitted": True, "late": False},
                ],
            }
        ),
        encoding="utf-8",
    )

    reports = course_board_server.list_assignment_reports()

    assert reports[0]["class_id"] == "4A-INF"
    assert reports[0]["class_label"] == "4A INF"
    assert reports[0]["github_team"] == "team-4a-inf"
    assert reports[0]["students"] == 3
    assert reports[0]["submitted"] == 2
    assert reports[0]["not_submitted"] == 1
    assert reports[0]["late"] == 1


def test_list_assignment_records_marks_due_without_register(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {"student_id": "rossi-mario", "path": "studenti/rossi-mario"},
                {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
            ],
        ),
    )

    payload = course_board_server.list_assignment_records("2026-10-20T08:00:00+02:00")

    assert payload["assignments"][0]["id"] == assignment["id"]
    assert payload["due_without_register"][0]["assignment"]["id"] == assignment["id"]
    assert payload["due_without_register"][0]["needs_register"] is True


def test_delete_assignment_record_removes_saved_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        ),
    )

    payload = course_board_server.delete_assignment_record({
        "assignment_id": assignment["id"],
        "now": "2026-10-20T08:00:00+02:00",
    })

    assert payload["ok"] is True
    assert payload["deleted"]["id"] == assignment["id"]
    assert payload["assignments"] == []
    assert payload["due_without_register"] == []
    assert not (tmp_path / assignment["path"]).exists()


def test_generate_assignment_report_preserves_assignment_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    activity_path = tmp_path / "activity.json"
    activity_path.write_text(
        json.dumps({
            "schema_version": "1.0",
            "id": "python-base-somma-001",
            "titolo": "Somma in Python",
            "linguaggio": "python",
            "tipo": "compito-casa",
            "difficolta": "B",
            "argomenti": ["variabili"],
            "consegna": "Somma due numeri.",
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
            "student_support_mode": "senza-aiuto",
        }),
        encoding="utf-8",
    )
    student_repo = tmp_path / "studenti" / "rossi-mario"
    (student_repo / "assignments" / "python-base-somma-001").mkdir(parents=True)
    (student_repo / "assignments" / "python-base-somma-001" / "main.py").write_text("print(3)\n", encoding="utf-8")

    result = course_board_server.generate_assignment_report({
        "activity_path": str(activity_path),
        "output_name": "demo/report.json",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "github_team": "team-3a-tpsi",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "now": "2026-10-20T08:00:00+02:00",
        "targets_text": str(student_repo),
        "assignment_id": "assignment-python-base-somma-001-3a",
    })

    assert result["report"]["assignment_id"] == "assignment-python-base-somma-001-3a"
    saved_payload = json.loads((tmp_path / "teacher-reports" / "demo" / "report.json").read_text(encoding="utf-8"))
    assert saved_payload["assignment_id"] == "assignment-python-base-somma-001-3a"


def test_preview_activity_assignment_returns_plan_without_writing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "assets": [{"type": "starter", "path": "starter/main.py", "target_path": "main.py"}],
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
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.preview_activity_assignment(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
        }
    )

    assert response["ok"] is True
    assert response["plan"]["activity_id"] == "python-base-somma-001"
    assert response["plan"]["student_assets"][0]["target_path"] == "main.py"
    assert response["plan"]["targets"][0]["target"] == str(target.resolve())
    assert not (target / "assignments").exists()


def test_preview_activity_ai_package_returns_context_files_and_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "tests").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    (activities_dir / "tests" / "hidden.py").write_text("assert True\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili", "operatori"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "contesto": {"percorso": "terzo-anno", "uda": "uda-input"},
                "assets": [
                    {"type": "starter", "path": "starter/main.py", "target_path": "main.py", "visibility": "student"},
                    {"type": "hidden_test", "path": "tests/hidden.py", "visibility": "teacher"},
                ],
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
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.preview_activity_ai_package(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Aggiungi test sui negativi",
            "provider": "codex",
            "student_budget": 5,
            "integrity_mode": "controlled",
        }
    )

    package = response["package"]
    assert response["ok"] is True
    assert package["schema_version"] == "activity_ai_package.v1"
    assert package["provider"] == "codex"
    assert package["prompt"] == "Aggiungi test sui negativi"
    assert package["activity"]["id"] == "python-base-somma-001"
    assert package["course_context"]["uda"] == "uda-input"
    target_entry = package["assignment"]["targets"][0]
    assert target_entry == {
        "target_id": "target-001",
        "display_name": "rossi-mario",
        "exists": False,
    }
    assert "target" not in target_entry
    assert "assignment_dir" not in target_entry
    assert str(tmp_path) not in json.dumps(package["assignment"]["targets"])
    assert package["files"][0]["path"] == "starter/main.py"
    assert package["files"][0]["included"] is True
    assert "starter" in package["files"][0]["content"]
    assert package["files"][1]["visibility"] == "teacher"
    assert package["policy"]["student_budget"] == 5
    assert package["policy"]["integrity_mode"] == "controlled"
    assert package["policy"]["no_provider_call"] is True
    assert not (target / "assignments").exists()


def test_preview_activity_ai_package_tolerates_empty_draft_language(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "activity-senza-linguaggio",
                "titolo": "Bozza senza linguaggio",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "",
                "consegna": "Completa la bozza.",
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
        ),
        encoding="utf-8",
    )

    response = course_board_server.preview_activity_ai_package(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Genera starter file",
            "provider": "codex",
        }
    )

    assert response["ok"] is True
    assert response["package"]["assignment"]["language"] == "c"


def test_preview_activity_ai_codex_draft_uses_local_adapter(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setenv("CODEX_COMMAND", "codex-test")
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
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
        ),
        encoding="utf-8",
    )
    captured = {}

    def fake_run_codex_activity_draft(package, *, cwd, codex_command="codex"):
        captured["package"] = package
        captured["cwd"] = cwd
        captured["codex_command"] = codex_command
        return {
            "adapter": "codex_exec",
            "draft": {
                "summary": "Bozza pronta",
                "teacher_notes": "Controllare i test.",
                "activity_patch": {"titolo": "Somma con negativi"},
                "files": [{"path": "main.py", "role": "starter", "content": "print(0)\n"}],
                "questions": [],
                "warnings": [],
            },
        }

    monkeypatch.setattr(course_board_server.codex_activity_adapter, "run_codex_activity_draft", fake_run_codex_activity_draft)

    response = course_board_server.preview_activity_ai_codex_draft(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Aggiungi test sui negativi",
            "provider": "codex",
            "current_draft": {
                "summary": "Prima bozza",
                "activity_patch": {"titolo": "Somma guidata"},
                "files": [],
            },
        }
    )

    assert response["ok"] is True
    assert response["adapter"] == "codex_exec"
    assert response["draft"]["activity_patch"]["titolo"] == "Somma con negativi"
    assert "raw" not in response
    assert captured["package"]["current_draft"]["summary"] == "Prima bozza"
    assert captured["package"]["prompt"] == "Aggiungi test sui negativi"
    assert captured["cwd"] == tmp_path
    assert captured["codex_command"] == "codex-test"


def test_save_assignment_record_persists_dashboard_assignment(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
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
        ),
        encoding="utf-8",
    )
    (tmp_path / "students" / "rossi-mario").mkdir(parents=True)
    (tmp_path / "students" / "bianchi-luca").mkdir(parents=True)

    response = course_board_server.save_assignment_record({
        "activity_path": "activities/activity.json",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "now": "2026-10-20T08:00:00+02:00",
        "targets_text": "students/rossi-mario\nstudents/bianchi-luca",
    })

    assert response["ok"] is True
    assert response["assignment"]["activity_id"] == "python-base-somma-001"
    assert response["assignment"]["target_type"] == "class"
    assert response["assignment"]["targets"][0]["path"] == "students/rossi-mario"
    assert response["due_without_register"][0]["assignment"]["id"] == response["assignment"]["id"]
    saved_path = tmp_path / response["assignment"]["path"]
    assert saved_path.is_file()


def test_distribute_activity_assignment_writes_scaffolds(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)

    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "assets": [{"type": "starter", "path": "starter/main.py", "target_path": "main.py"}],
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
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.distribute_activity_assignment({
        "activity_path": "activities/activity.json",
        "targets_text": "students/rossi-mario",
    })

    assignment_dir = target / "assignments" / "python-base-somma-001"
    assert response["ok"] is True
    assert response["results"][0]["assignment_dir"] == str(assignment_dir.resolve())
    assert response["plan"]["targets"][0]["exists"] is True
    assert (assignment_dir / "activity.json").is_file()
    assert (assignment_dir / "main.py").read_text(encoding="utf-8") == "print('starter')\n"


def test_review_assignment_ai_feedback_persists_teacher_decision(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    report_path = report_dir / "activity.json"
    report_path.write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "draft",
                            "summary": "Bozza",
                            "approved_by_teacher": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = course_board_server.review_assignment_ai_feedback("demo/activity.json", "rossi-mario", "approve")
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["students"][0]["ai_feedback"]["status"] == "approved"
    assert report["students"][0]["ai_feedback"]["approved_by_teacher"] is True
    assert saved["students"][0]["ai_feedback"]["status"] == "approved"
    assert saved["students"][0]["ai_feedback"]["approved_by_teacher"] is True


def test_review_assignment_ai_feedback_reopens_reviewed_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = course_board_server.review_assignment_ai_feedback("activity.json", "rossi-mario", "reopen")

    assert report["students"][0]["ai_feedback"]["status"] == "draft"
    assert report["students"][0]["ai_feedback"]["approved_by_teacher"] is False


def test_review_assignment_ai_feedback_rejects_approve_on_non_draft_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        course_board_server.review_assignment_ai_feedback("activity.json", "rossi-mario", "approve")
    except ValueError as error:
        assert "non e una bozza" in str(error)
    else:
        raise AssertionError("La review deve rifiutare approve su feedback AI non in bozza")


def test_student_dashboard_endpoint_filters_to_requested_student(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "approved",
                            "approved_by_teacher": True,
                            "student_feedback": "Feedback visibile.",
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "student_id": "bianchi-luca",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    dashboard = course_board_server.student_dashboard("rossi-mario")

    assert dashboard["student_id"] == "rossi-mario"
    assert len(dashboard["assignments"]) == 1
    assert dashboard["assignments"][0]["approved_feedback"]["student_feedback"] == "Feedback visibile."


def test_class_roster_helpers_use_local_roster_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    classes_dir = tmp_path / "doc" / "classes"
    classes_dir.mkdir(parents=True)
    (classes_dir / "3a.json").write_text(
        json.dumps(
            {
                "id": "3A",
                "label": "3A TPSI",
                "students": [
                    {
                        "id": "rossi-mario",
                        "display_name": "Rossi Mario",
                        "github_username": "rossi-mario-gh",
                        "local_path": r"studenti\rossi-mario",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rosters = course_board_server.list_class_rosters()
    roster = course_board_server.read_class_roster("3a.json")

    assert rosters[0]["name"] == "3a.json"
    assert rosters[0]["id"] == "3A"
    assert roster["students"][0]["id"] == "rossi-mario"
    assert roster["students"][0]["github_username"] == "rossi-mario-gh"
    assert roster["students"][0]["local_path"] == "studenti/rossi-mario"


def test_save_activity_builds_valid_draft_from_gui_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    result = course_board_server.save_activity({
        "title": "Somma in Python",
        "kind": "compito-casa",
        "difficulty": "B",
        "topics": "variabili, operatori",
        "prompt": "Scrivi un programma che somma due numeri.",
        "estimated_minutes": "25",
        "language": "python",
        "source_name": "main.py",
        "class_id": "3A-TPSI",
        "github_team": "team-3a",
        "uda_id": "uda-1",
    })

    activity_path = tmp_path / "activities" / "drafts" / "somma-in-python.json"
    saved_payload = json.loads(activity_path.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["activity"]["path"] == "activities/drafts/somma-in-python.json"
    assert result["activities"] == [result["activity"]]
    assert saved_payload["id"] == "somma-in-python"
    assert saved_payload["titolo"] == "Somma in Python"
    assert saved_payload["tipo"] == "compito-casa"
    assert saved_payload["linguaggio"] == "python"
    assert saved_payload["language"] == "python"
    assert saved_payload["argomenti"] == ["variabili", "operatori"]
    assert saved_payload["metriche"]["tempo_stimato_minuti"] == 25
    assert saved_payload["contesto"] == {
        "classe": "3A-TPSI",
        "team_github": "team-3a",
        "uda": "uda-1",
        "source_name": "main.py",
    }


def test_ai_secret_status_reports_paths_and_configured_keys_without_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "AI_SECRET_PATH", tmp_path / ".secrets" / "ai.secret")
    monkeypatch.setattr(course_board_server, "LEGACY_AI_SECRET_PATH", tmp_path / "scripts" / ".secrets" / "ai.secret")
    monkeypatch.setattr(course_board_server, "AI_PROVIDERS_PATH", tmp_path / "config" / "ai_providers.yaml")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".secrets").mkdir()
    (tmp_path / ".secrets" / "ai.secret").write_text("OPENAI_API_KEY=secret-value\n", encoding="utf-8")
    (tmp_path / "scripts" / ".secrets").mkdir(parents=True)
    (tmp_path / "scripts" / ".secrets" / "ai.secret").write_text("GEMINI_API_KEY=legacy-secret\n", encoding="utf-8")

    status = course_board_server.ai_secret_status()

    assert status["path"] == ".secrets/ai.secret"
    assert status["exists"] is True
    assert status["legacy_path"] == "scripts/.secrets/ai.secret"
    assert status["legacy_exists"] is True
    assert status["configured_keys"]["OPENAI_API_KEY"] is True
    assert status["configured_keys"]["GEMINI_API_KEY"] is False
    assert "secret-value" not in json.dumps(status)
    assert "legacy-secret" not in json.dumps(status)
