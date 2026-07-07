from __future__ import annotations

import json
import argparse
import subprocess

from scripts import grade_activity


def activity() -> dict:
    return {
        "id": "c-base-somma-001",
        "linguaggio": "c",
        "test_cases": [
            {
                "name": "somma positiva",
                "stdin": "2 3\n",
                "expected_stdout": "5\n",
            },
            {
                "name": "somma con negativo",
                "stdin": "-2 3\n",
                "expected_stdout": "1\n",
            },
        ],
    }


def test_grade_activity_passes_valid_c_program(tmp_path) -> None:
    source = tmp_path / "main.c"
    source.write_text(
        '#include <stdio.h>\nint main(void){int a,b; scanf("%d %d",&a,&b); printf("%d\\n", a+b); return 0;}\n',
        encoding="utf-8",
    )

    report = grade_activity.grade_activity(activity(), source)

    assert report["passed"] is True
    assert report["summary"] == {"passed": 2, "total": 2}


def test_grade_activity_reports_wrong_output(tmp_path) -> None:
    source = tmp_path / "main.c"
    source.write_text(
        '#include <stdio.h>\nint main(void){int a,b; scanf("%d %d",&a,&b); printf("%d\\n", a-b); return 0;}\n',
        encoding="utf-8",
    )

    report = grade_activity.grade_activity(activity(), source)

    assert report["passed"] is False
    assert report["status"] == "failed"
    assert report["summary"]["passed"] == 0


def test_grade_activity_reports_compile_error(tmp_path) -> None:
    source = tmp_path / "main.c"
    source.write_text("int main(void){ return }\n", encoding="utf-8")

    report = grade_activity.grade_activity(activity(), source)

    assert report["passed"] is False
    assert report["status"] == "compile-error"
    assert report["tests"] == []


def test_grade_activity_requires_test_cases(tmp_path) -> None:
    source = tmp_path / "main.c"
    source.write_text("int main(void){ return 0; }\n", encoding="utf-8")

    report = grade_activity.grade_activity({"id": "vuota", "linguaggio": "c"}, source)

    assert report["passed"] is False
    assert report["status"] == "invalid-activity"
    assert report["activity_id"] == "vuota"
    assert report["language"] == "c"
    assert report["source"] == str(source)
    assert report["tests"] == []


def test_grade_activity_requires_expected_stdout(tmp_path) -> None:
    source = tmp_path / "main.c"
    source.write_text("int main(void){ return 0; }\n", encoding="utf-8")

    report = grade_activity.grade_activity({"id": "senza-output", "linguaggio": "c", "test_cases": [{"stdin": ""}]}, source)

    assert report["passed"] is False
    assert report["status"] == "invalid-activity"
    assert "test_cases[0].expected_stdout mancante" in report["errors"]


def test_grade_activity_reports_missing_source(tmp_path) -> None:
    source = tmp_path / "missing.c"

    report = grade_activity.grade_activity(activity(), source)

    assert report["passed"] is False
    assert report["status"] == "source-not-found"
    assert report["tests"] == []


def test_write_report_writes_json(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    report = {"passed": True, "status": "passed"}

    grade_activity.write_report(report, report_path)

    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_grade_activity_reports_unsupported_planned_language(tmp_path) -> None:
    source = tmp_path / "main.py"
    source.write_text("print(5)\n", encoding="utf-8")

    report = grade_activity.grade_activity({"id": "python-001", "linguaggio": "python", "test_cases": []}, source)

    assert report["passed"] is False
    assert report["status"] == "unsupported-language"
    assert report["language"] == "python"


def test_grade_activity_reports_unknown_language(tmp_path) -> None:
    source = tmp_path / "main.xyz"
    source.write_text("contenuto\n", encoding="utf-8")

    report = grade_activity.grade_activity({"id": "x-001", "linguaggio": "brainheck", "test_cases": []}, source)

    assert report["passed"] is False
    assert report["status"] == "unknown-language"
    assert report["language"] == "brainheck"


def test_activity_language_strips_spaces() -> None:
    assert grade_activity.activity_language({"linguaggio": " C "}) == "c"


def test_timeout_report_has_null_returncode(monkeypatch) -> None:
    def timeout_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="submission", timeout=1)

    monkeypatch.setattr(grade_activity.subprocess, "run", timeout_run)

    report = grade_activity.run_test_case("submission", {"expected_stdout": ""}, timeout_seconds=1)

    assert report["returncode"] is None


def test_positive_int_rejects_zero() -> None:
    try:
        grade_activity.positive_int("0")
    except argparse.ArgumentTypeError as error:
        assert "positivo" in str(error)
    else:
        raise AssertionError("positive_int should reject zero")


def test_docker_command_uses_read_only_workspace(tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.c"
    report_path = tmp_path / "report.json"
    activity_path.write_text("{}", encoding="utf-8")
    source_path.write_text("int main(void){return 0;}", encoding="utf-8")

    command = grade_activity.docker_command(
        activity=activity_path,
        source=source_path,
        report=report_path,
        language="c",
        timeout_seconds=5,
        workspace=tmp_path,
    )

    assert "--network" in command
    assert "none" in command
    assert f"{tmp_path.resolve()}:/workspace:ro" in command
    assert "--language" in command
    assert "c" in command


def test_run_docker_grading_reports_missing_docker(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = None
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")

    def missing_docker(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(grade_activity.subprocess, "run", missing_docker)

    assert grade_activity.run_docker_grading(Args()) == 1
