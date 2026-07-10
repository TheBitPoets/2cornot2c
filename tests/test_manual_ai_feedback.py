from __future__ import annotations

import json

from scripts import manual_ai_feedback


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
