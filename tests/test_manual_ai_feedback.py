from __future__ import annotations

import json
from pathlib import Path

from scripts import manual_ai_feedback

REGISTER_FIXTURE = Path("tests/fixtures/contracts/assignment_register.json")


def request_payload() -> dict:
    return {
        "activity_id": "c-base-somma-001",
        "student_id": "rossi-mario",
        "activity": {"title": "Somma in C"},
        "allowed_context": {"teacher_notes": "Controllare il caso con negativi."},
        "grading": {
            "status": "graded_failed",
            "passed": False,
            "tests_passed": 1,
            "tests_total": 2,
            "failed_tests": ["somma_negativi"],
            "score": 5,
            "detail": "Output errato",
        },
    }


def test_package_command_prints_prompt_and_request_json(tmp_path, capsys) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request_payload()), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package", str(request_path)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert "Non aggiungere testo fuori dal JSON" in output["prompt"]
    assert "ai_feedback_response.v1" in output["prompt"]
    request_json = json.loads(output["request_json"])
    assert request_json["schema_version"] == "ai_feedback_request.v1"
    assert request_json["activity"]["id"] == "c-base-somma-001"
    assert request_json["student"] == {"id": "rossi-mario"}


def test_package_from_register_command_prints_prompt_for_student(tmp_path, capsys) -> None:
    register_path = tmp_path / "register.json"
    register_path.write_text(REGISTER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package-from-register", str(register_path), "rossi-mario"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    request_json = json.loads(output["request_json"])
    assert request_json["activity"]["id"] == "python-base-somma-001"
    assert request_json["activity"]["class_id"] == "3a-tpsi-2026"
    assert request_json["student"] == {"id": "rossi-mario"}
    assert request_json["grading"]["status"] == "graded_passed"
    assert request_json["context"]["student_status"] == "submitted_on_time"


def test_package_from_register_command_reports_missing_student(tmp_path, capsys) -> None:
    register_path = tmp_path / "register.json"
    register_path.write_text(REGISTER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package-from-register", str(register_path), "missing-student"])

    assert exit_code == 1
    assert "studente non trovato" in capsys.readouterr().err


def test_package_from_register_command_accepts_legacy_student_field(tmp_path, capsys) -> None:
    register = json.loads(REGISTER_FIXTURE.read_text(encoding="utf-8"))
    del register["students"][0]["student_id"]
    register_path = tmp_path / "register.json"
    register_path.write_text(json.dumps(register), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package-from-register", str(register_path), "rossi-mario"])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    request_json = json.loads(output["request_json"])
    assert request_json["student"] == {"id": "rossi-mario"}


def test_apply_response_command_writes_updated_register(tmp_path, capsys) -> None:
    register_path = tmp_path / "register.json"
    response_path = tmp_path / "response.json"
    output_path = tmp_path / "updated-register.json"
    register_path.write_text(REGISTER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    response_path.write_text(
        json.dumps(
            {
                "schema_version": "ai_feedback_response.v1",
                "status": "draft",
                "summary": "La consegna e corretta.",
                "suggested_grade": 9,
                "student_feedback": "Buon lavoro.",
            }
        ),
        encoding="utf-8",
    )

    exit_code = manual_ai_feedback.main(
        ["apply-response", str(register_path), "rossi-mario", str(response_path), "--output", str(output_path)]
    )

    assert exit_code == 0
    assert str(output_path) in capsys.readouterr().out
    updated = json.loads(output_path.read_text(encoding="utf-8"))
    feedback = updated["students"][0]["ai_feedback"]
    assert feedback["status"] == "draft"
    assert feedback["summary"] == "La consegna e corretta."
    assert feedback["suggested_grade"] == 9.0
    assert feedback["student_feedback"] == "Buon lavoro."
    assert feedback["approved_by_teacher"] is False


def test_apply_response_command_refuses_existing_output_without_force(tmp_path, capsys) -> None:
    register_path = tmp_path / "register.json"
    response_path = tmp_path / "response.json"
    output_path = tmp_path / "updated-register.json"
    register_path.write_text(REGISTER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    response_path.write_text(
        json.dumps(
            {
                "schema_version": "ai_feedback_response.v1",
                "status": "draft",
                "summary": "Feedback valido.",
            }
        ),
        encoding="utf-8",
    )
    output_path.write_text("{}", encoding="utf-8")

    exit_code = manual_ai_feedback.main(
        ["apply-response", str(register_path), "rossi-mario", str(response_path), "--output", str(output_path)]
    )

    assert exit_code == 1
    assert "file gia esistente" in capsys.readouterr().err


def test_apply_response_command_accepts_utf8_bom_response(tmp_path) -> None:
    register_path = tmp_path / "register.json"
    response_path = tmp_path / "response.json"
    output_path = tmp_path / "updated-register.json"
    register_path.write_text(REGISTER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    response_path.write_text(
        json.dumps(
            {
                "schema_version": "ai_feedback_response.v1",
                "status": "draft",
                "summary": "Feedback salvato da editor Windows.",
            }
        ),
        encoding="utf-8-sig",
    )

    exit_code = manual_ai_feedback.main(
        ["apply-response", str(register_path), "rossi-mario", str(response_path), "--output", str(output_path)]
    )

    assert exit_code == 0
    updated = json.loads(output_path.read_text(encoding="utf-8"))
    assert updated["students"][0]["ai_feedback"]["summary"] == "Feedback salvato da editor Windows."


def test_review_feedback_command_approves_draft_feedback(tmp_path) -> None:
    register = json.loads(REGISTER_FIXTURE.read_text(encoding="utf-8"))
    register["students"][0]["ai_feedback"] = {
        "status": "draft",
        "summary": "Feedback da approvare.",
        "approved_by_teacher": False,
    }
    register_path = tmp_path / "register.json"
    output_path = tmp_path / "approved-register.json"
    register_path.write_text(json.dumps(register), encoding="utf-8")

    exit_code = manual_ai_feedback.main(
        ["review-feedback", str(register_path), "rossi-mario", "approve", "--output", str(output_path)]
    )

    assert exit_code == 0
    updated = json.loads(output_path.read_text(encoding="utf-8"))
    feedback = updated["students"][0]["ai_feedback"]
    assert feedback["status"] == "approved"
    assert feedback["approved_by_teacher"] is True
    assert feedback["summary"] == "Feedback da approvare."


def test_review_feedback_command_rejects_draft_feedback(tmp_path) -> None:
    register = json.loads(REGISTER_FIXTURE.read_text(encoding="utf-8"))
    register["students"][0]["ai_feedback"] = {
        "status": "draft",
        "summary": "Feedback da respingere.",
        "approved_by_teacher": False,
    }
    register_path = tmp_path / "register.json"
    output_path = tmp_path / "rejected-register.json"
    register_path.write_text(json.dumps(register), encoding="utf-8")

    exit_code = manual_ai_feedback.main(
        ["review-feedback", str(register_path), "rossi-mario", "reject", "--output", str(output_path)]
    )

    assert exit_code == 0
    updated = json.loads(output_path.read_text(encoding="utf-8"))
    feedback = updated["students"][0]["ai_feedback"]
    assert feedback["status"] == "rejected"
    assert feedback["approved_by_teacher"] is False
    assert feedback["summary"] == "Feedback da respingere."


def test_review_feedback_command_reopens_reviewed_feedback(tmp_path) -> None:
    register = json.loads(REGISTER_FIXTURE.read_text(encoding="utf-8"))
    register["students"][0]["ai_feedback"] = {
        "status": "approved",
        "summary": "Feedback da riaprire.",
        "approved_by_teacher": True,
    }
    register_path = tmp_path / "register.json"
    output_path = tmp_path / "draft-register.json"
    register_path.write_text(json.dumps(register), encoding="utf-8")

    exit_code = manual_ai_feedback.main(
        ["review-feedback", str(register_path), "rossi-mario", "reopen", "--output", str(output_path)]
    )

    assert exit_code == 0
    updated = json.loads(output_path.read_text(encoding="utf-8"))
    feedback = updated["students"][0]["ai_feedback"]
    assert feedback["status"] == "draft"
    assert feedback["approved_by_teacher"] is False
    assert feedback["summary"] == "Feedback da riaprire."


def test_review_feedback_command_requires_draft_feedback(tmp_path, capsys) -> None:
    register_path = tmp_path / "register.json"
    output_path = tmp_path / "approved-register.json"
    register_path.write_text(REGISTER_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = manual_ai_feedback.main(
        ["review-feedback", str(register_path), "rossi-mario", "approve", "--output", str(output_path)]
    )

    assert exit_code == 1
    assert "non e una bozza" in capsys.readouterr().err
    assert not output_path.exists()


def test_parse_response_command_prints_normalized_feedback(tmp_path, capsys) -> None:
    response_path = tmp_path / "response.json"
    response_path.write_text(
        json.dumps(
            {
                "schema_version": "ai_feedback_response.v1",
                "status": "draft",
                "summary": "La consegna fallisce un caso limite.",
                "student_feedback": "Rivedi i numeri negativi.",
            }
        ),
        encoding="utf-8",
    )

    exit_code = manual_ai_feedback.main(["parse-response", str(response_path)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "draft"
    assert output["summary"] == "La consegna fallisce un caso limite."
    assert output["student_feedback"] == "Rivedi i numeri negativi."
    assert output["approved_by_teacher"] is False


def test_package_command_reports_invalid_request(tmp_path, capsys) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps({"activity_id": "activity"}), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package", str(request_path)])

    assert exit_code == 1
    assert "grading mancante" in capsys.readouterr().err


def test_package_command_rejects_invalid_grading_status(tmp_path, capsys) -> None:
    payload = request_payload()
    payload["grading"]["status"] = "approved"
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package", str(request_path)])

    assert exit_code == 1
    assert "grading.status non valido" in capsys.readouterr().err


def test_package_command_rejects_invalid_grading_detail(tmp_path, capsys) -> None:
    payload = request_payload()
    payload["grading"]["detail"] = {"message": "errore"}
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = manual_ai_feedback.main(["package", str(request_path)])

    assert exit_code == 1
    assert "grading.detail deve essere una stringa" in capsys.readouterr().err
