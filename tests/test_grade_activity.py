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
    activity_path.write_text("{}", encoding="utf-8")
    source_path.write_text("int main(void){return 0;}", encoding="utf-8")

    command = grade_activity.docker_command(
        activity=activity_path,
        source=source_path,
        language="c",
        timeout_seconds=5,
        workspace=tmp_path,
    )

    assert "--network" in command
    assert "none" in command
    assert "--read-only" in command
    assert "--cap-drop" in command
    assert "ALL" in command
    assert "--security-opt" in command
    assert "no-new-privileges" in command
    assert "--pids-limit" in command
    assert "128" in command
    assert "--memory" in command
    assert "256m" in command
    assert "--cpus" in command
    assert "1" in command
    assert f"{tmp_path.resolve()}:/workspace:ro" in command
    assert "--tmpfs" in command
    assert "/thebitlab-work:rw,nosuid,nodev,size=64m" in command
    assert "TMPDIR=/thebitlab-work" in command
    assert "/thebitlab-output" not in command
    assert "--report" not in command
    assert "--language" in command
    assert "c" in command


def test_prepare_docker_workspace_copies_only_runner_inputs(tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.c"
    secret_path = tmp_path / ".secret"
    activity_path.write_text("{}", encoding="utf-8")
    source_path.write_text("int main(void){return 0;}", encoding="utf-8")
    secret_path.write_text("non deve entrare nel container", encoding="utf-8")

    workspace, copied_activity, copied_source = grade_activity.prepare_docker_workspace(
        activity_path,
        source_path,
        tmp_path / "docker",
    )

    assert (workspace / "scripts" / "grade_activity.py").exists()
    assert copied_activity == workspace / "activity" / "activity.json"
    assert copied_source == workspace / "source" / "main.c"
    assert not (workspace / ".secret").exists()


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
    monkeypatch.chdir(tmp_path)

    def missing_docker(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(grade_activity.subprocess, "run", missing_docker)

    assert grade_activity.run_docker_grading(Args()) == 1


def test_run_docker_grading_reports_docker_timeout(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = None
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def timeout_docker(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="docker run", timeout=kwargs["timeout"])

    monkeypatch.setattr(grade_activity.subprocess, "run", timeout_docker)

    assert grade_activity.run_docker_grading(Args()) == 1


def test_docker_timeout_scales_with_test_cases() -> None:
    activity = {"test_cases": [{"name": "uno"}, {"name": "due"}, {"name": "tre"}]}

    assert grade_activity.docker_timeout_seconds(activity, 5) == 30


def test_run_docker_grading_reports_missing_input_before_docker(tmp_path) -> None:
    class Args:
        activity = tmp_path / "missing.json"
        source = tmp_path / "main.c"
        report = None
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")

    assert grade_activity.run_docker_grading(Args()) == 1


def test_run_docker_grading_rejects_invalid_json_output(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = tmp_path / "report.json"
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = "non-json"
        stderr = "errore container"

    monkeypatch.setattr(grade_activity.subprocess, "run", lambda *args, **kwargs: Result())

    assert grade_activity.run_docker_grading(Args()) == 1
    assert not Args.report.exists()


def test_run_docker_grading_rejects_non_report_json_on_container_error(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = tmp_path / "report.json"
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = json.dumps({"error": "errore infrastrutturale"})
        stderr = "errore container"

    monkeypatch.setattr(grade_activity.subprocess, "run", lambda *args, **kwargs: Result())

    assert grade_activity.run_docker_grading(Args()) == 1
    assert not Args.report.exists()


def test_run_docker_grading_rejects_non_report_json_on_success(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = tmp_path / "report.json"
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 0
        stdout = json.dumps({"ok": True})
        stderr = ""

    monkeypatch.setattr(grade_activity.subprocess, "run", lambda *args, **kwargs: Result())

    assert grade_activity.run_docker_grading(Args()) == 1
    assert not Args.report.exists()


def test_run_docker_grading_rejects_report_with_invalid_field_types(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = tmp_path / "report.json"
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = json.dumps({"passed": "false", "status": 500})
        stderr = "errore container"

    monkeypatch.setattr(grade_activity.subprocess, "run", lambda *args, **kwargs: Result())

    assert grade_activity.run_docker_grading(Args()) == 1
    assert not Args.report.exists()


def test_run_docker_grading_rejects_success_report_on_container_error(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = tmp_path / "report.json"
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = json.dumps({"passed": True, "status": "passed"})
        stderr = "errore container"

    monkeypatch.setattr(grade_activity.subprocess, "run", lambda *args, **kwargs: Result())

    assert grade_activity.run_docker_grading(Args()) == 1
    assert not Args.report.exists()


def test_run_docker_grading_writes_report_on_host(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = tmp_path / "nested" / "report.json"
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    Args.activity.write_text("{}", encoding="utf-8")
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 0
        stdout = json.dumps({"passed": True, "status": "passed"})
        stderr = ""

    monkeypatch.setattr(grade_activity.subprocess, "run", lambda *args, **kwargs: Result())

    assert grade_activity.run_docker_grading(Args()) == 0
    assert json.loads(Args.report.read_text(encoding="utf-8")) == {"passed": True, "status": "passed"}


def test_docker_command_requires_paths_inside_workspace(tmp_path) -> None:
    outside = tmp_path.parent / "outside.c"
    outside.write_text("int main(void){return 0;}", encoding="utf-8")
    activity_path = tmp_path / "activity.json"
    activity_path.write_text("{}", encoding="utf-8")

    try:
        grade_activity.docker_command(
            activity=activity_path,
            source=outside,
            language="c",
            timeout_seconds=5,
            workspace=tmp_path,
        )
    except ValueError as error:
        assert "source deve trovarsi dentro il workspace" in str(error)
    else:
        raise AssertionError("docker_command should reject paths outside workspace")
