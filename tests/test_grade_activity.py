from __future__ import annotations

import json
import argparse

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


def test_positive_int_rejects_zero() -> None:
    try:
        grade_activity.positive_int("0")
    except argparse.ArgumentTypeError as error:
        assert "positivo" in str(error)
    else:
        raise AssertionError("positive_int should reject zero")
