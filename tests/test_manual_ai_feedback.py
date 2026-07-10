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
