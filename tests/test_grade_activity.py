from __future__ import annotations

import json
import argparse
import shutil
import subprocess

import pytest

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


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc non disponibile nell'ambiente di test")
def test_grade_activity_passes_valid_c_program(tmp_path) -> None:
    source = tmp_path / "main.c"
    source.write_text(
        '#include <stdio.h>\nint main(void){int a,b; scanf("%d %d",&a,&b); printf("%d\\n", a+b); return 0;}\n',
        encoding="utf-8",
    )

    report = grade_activity.grade_activity(activity(), source)

    assert report["passed"] is True
    assert report["summary"] == {"passed": 2, "total": 2}


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc non disponibile nell'ambiente di test")
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


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc non disponibile nell'ambiente di test")
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


def test_grade_activity_passes_valid_python_program(tmp_path) -> None:
    source = tmp_path / "main.py"
    source.write_text("value = input().strip()\nprint(int(value) + 1)\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {
            "id": "python-001",
            "linguaggio": "python",
            "test_cases": [{"name": "incremento", "stdin": "4\n", "expected_stdout": "5\n"}],
        },
        source,
    )

    assert report["passed"] is True
    assert report["status"] == "passed"
    assert report["language"] == "python"


def test_grade_activity_reports_python_wrong_output(tmp_path) -> None:
    source = tmp_path / "main.py"
    source.write_text("print('wrong')\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {
            "id": "python-002",
            "linguaggio": "python",
            "test_cases": [{"name": "output", "expected_stdout": "right\n"}],
        },
        source,
    )

    assert report["passed"] is False
    assert report["status"] == "failed"
    assert report["summary"] == {"passed": 0, "total": 1}


@pytest.mark.skipif(shutil.which("node") is None, reason="node non disponibile nell'ambiente di test")
def test_grade_activity_passes_valid_javascript_program(tmp_path) -> None:
    source = tmp_path / "main.js"
    source.write_text("let value = ''; process.stdin.on('data', chunk => value += chunk).on('end', () => console.log(Number(value) + 1));\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {"id": "js-001", "linguaggio": "javascript", "test_cases": [{"stdin": "4\n", "expected_stdout": "5\n"}]},
        source,
    )

    assert report["passed"] is True
    assert report["language"] == "javascript"


def test_node_runner_keeps_startup_grace_separate_from_student_timeout(monkeypatch, tmp_path) -> None:
    captured: dict[str, int | list[str]] = {}

    class StartupResult:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_startup(command, **kwargs):
        captured["startup_command"] = command
        captured["startup_timeout"] = kwargs["timeout"]
        return StartupResult()

    def fake_run(command, test_case, *, timeout_seconds):
        captured["student_timeout"] = timeout_seconds
        return {"passed": True, "status": "passed"}

    monkeypatch.setattr(grade_activity.subprocess, "run", fake_startup)
    monkeypatch.setattr(grade_activity, "run_command_test_case", fake_run)
    source = tmp_path / "main.js"

    grade_activity.run_node_test_case(source, {}, timeout_seconds=2)

    assert captured["startup_command"] == ["node", "--check", str(source)]
    assert captured["startup_timeout"] == grade_activity.DEFAULT_NODE_STARTUP_GRACE_SECONDS
    assert captured["student_timeout"] == 2


def test_grade_activity_passes_valid_sql_script(tmp_path) -> None:
    source = tmp_path / "main.sql"
    source.write_text("SELECT 2 + 3;\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {"id": "sql-001", "linguaggio": "sql", "test_cases": [{"expected_stdout": "5\n"}]},
        source,
    )

    assert report["passed"] is True
    assert report["language"] == "sql"


def test_grade_activity_sql_matches_sqlite_cli_rows_and_nulls(tmp_path) -> None:
    source = tmp_path / "main.sql"
    source.write_text(
        "CREATE TABLE studenti (nome TEXT, voto INTEGER);\n"
        "INSERT INTO studenti VALUES ('Ada', 9), ('Linus', NULL);\n"
        "SELECT nome, voto FROM studenti ORDER BY nome;\n",
        encoding="utf-8",
    )

    report = grade_activity.grade_activity(
        {
            "id": "sql-rows-001",
            "linguaggio": "sql",
            "test_cases": [{"expected_stdout": "Ada|9\nLinus|\n"}],
        },
        source,
    )

    assert report["passed"] is True
    assert report["tests"][0]["stdout"] == "Ada|9\nLinus|\n"


def test_grade_activity_sql_matches_sqlite_cli_blob_output(tmp_path) -> None:
    source = tmp_path / "main.sql"
    source.write_text("SELECT X'4142';\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {
            "id": "sql-blob-001",
            "linguaggio": "sql",
            "test_cases": [{"expected_stdout": "AB\n"}],
        },
        source,
    )

    assert report["passed"] is True
    assert report["tests"][0]["stdout"] == "AB\n"


def test_grade_activity_reports_sql_error(tmp_path) -> None:
    source = tmp_path / "main.sql"
    source.write_text("SELECT colonna_inesistente FROM studenti;\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {
            "id": "sql-error-001",
            "linguaggio": "sql",
            "test_cases": [{"expected_stdout": ""}],
        },
        source,
    )

    assert report["passed"] is False
    assert report["status"] == "failed"
    assert report["tests"][0]["status"] == "execution-error"
    assert report["tests"][0]["returncode"] == 1
    assert report["tests"][0]["stderr"]


def test_grade_activity_reports_sql_timeout(tmp_path) -> None:
    source = tmp_path / "main.sql"
    source.write_text(
        "WITH RECURSIVE numeri(n) AS ("
        "SELECT 1 UNION ALL SELECT n + 1 FROM numeri WHERE n < 1000000"
        ") SELECT sum(n) FROM numeri;\n",
        encoding="utf-8",
    )

    report = grade_activity.grade_activity(
        {
            "id": "sql-timeout-001",
            "linguaggio": "sql",
            "test_cases": [{"expected_stdout": ""}],
        },
        source,
        timeout_seconds=0,
    )

    assert report["passed"] is False
    assert report["tests"][0]["status"] == "timeout"
    assert report["tests"][0]["returncode"] is None


def test_grade_activity_applies_sql_timeout_during_parsing(tmp_path) -> None:
    source = tmp_path / "main.sql"
    source.write_text("-- " + ("commento " * 10000), encoding="utf-8")

    report = grade_activity.grade_activity(
        {
            "id": "sql-parse-timeout-001",
            "linguaggio": "sql",
            "test_cases": [{"expected_stdout": ""}],
        },
        source,
        timeout_seconds=0,
    )

    assert report["passed"] is False
    assert report["tests"][0]["status"] == "timeout"


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


def test_execution_error_report_has_null_returncode(monkeypatch) -> None:
    def permission_error_run(*args, **kwargs):
        raise PermissionError("permesso negato")

    monkeypatch.setattr(grade_activity.subprocess, "run", permission_error_run)

    report = grade_activity.run_test_case("submission", {"expected_stdout": ""}, timeout_seconds=1)

    assert report["passed"] is False
    assert report["status"] == "execution-error"
    assert report["returncode"] is None
    assert "permesso negato" in report["stderr"]


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
    assert "/thebitlab-work:rw,exec,nosuid,nodev,mode=1777,size=64m" in command
    assert "TMPDIR=/thebitlab-work" in command
    assert "/thebitlab-output" not in command
    assert "--report" not in command
    assert "--language" in command
    assert "c" in command
    assert command[command.index("--activity") + 1] == "activity.json"
    assert command[command.index("--source") + 1] == "main.c"


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
    assert grade_activity.docker_timeout_seconds({**activity, "linguaggio": "javascript"}, 5) == 60


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
