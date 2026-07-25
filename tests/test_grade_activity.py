from __future__ import annotations

import json
import argparse
import os
import shutil
import subprocess
import sys
import time

import pytest

from scripts import grade_activity


def process_is_running(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return f'"{pid}"' in result.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


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


def write_valid_docker_activity(path) -> None:
    path.write_text(json.dumps(activity()), encoding="utf-8")


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
@pytest.mark.parametrize("language", ["javascript", "nodejs"])
def test_grade_activity_passes_valid_javascript_program(tmp_path, language) -> None:
    source = tmp_path / "main.js"
    source.write_text("let value = ''; process.stdin.on('data', chunk => value += chunk).on('end', () => console.log(Number(value) + 1));\n", encoding="utf-8")

    report = grade_activity.grade_activity(
        {"id": "js-001", "linguaggio": language, "test_cases": [{"stdin": "4\n", "expected_stdout": "5\n"}]},
        source,
    )

    assert report["passed"] is True
    assert report["language"] == language


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


def test_report_metadata_enriches_remote_tracking_identity() -> None:
    original = {"activity_id": "activity-001", "status": "passed"}

    enriched = grade_activity.with_report_metadata(
        original,
        assignment_id=" assignment-001 ",
        student_id=" rossi-mario ",
        commit="a" * 40,
        submitted_at="2026-07-24T18:00:00Z",
        source_repo_path="assignments/activity-001/main.py",
    )

    assert original == {"activity_id": "activity-001", "status": "passed"}
    assert enriched["assignment_id"] == "assignment-001"
    assert enriched["student_id"] == "rossi-mario"
    assert enriched["commit"] == "a" * 40
    assert enriched["submitted_at"] == "2026-07-24T18:00:00Z"
    assert enriched["source"] == "assignments/activity-001/main.py"


def test_docker_command_uses_read_only_workspace(tmp_path) -> None:
    source_path = tmp_path / "main.c"
    source_path.write_text("int main(void){return 0;}", encoding="utf-8")

    command = grade_activity.docker_command(
        source=source_path,
        timeout_seconds=5,
        workspace=tmp_path,
        cidfile=tmp_path / "container.cid",
        container_name="thebitlab-grade-test",
    )

    assert "--network" in command
    assert "-i" in command
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
    assert f"{tmp_path.resolve()}:/submission:ro" in command
    assert "--tmpfs" in command
    assert "/thebitlab-work:rw,exec,nosuid,nodev,mode=1777,size=64m" in command
    assert "TMPDIR=/thebitlab-work" in command
    assert "/thebitlab-output" not in command
    assert "--cidfile" in command
    assert str((tmp_path / "container.cid").resolve()) in command
    assert command[command.index("--name") + 1] == "thebitlab-grade-test"
    assert "--report" not in command
    assert "--activity" not in command
    assert "--language" not in command
    assert "--worker" in command
    assert command[command.index("--source") + 1] == "main.c"


def test_remove_docker_container_validates_id_and_forces_cleanup(
    monkeypatch,
    tmp_path,
) -> None:
    cidfile = tmp_path / "container.cid"
    container_id = "a" * 64
    cidfile.write_text(container_id, encoding="ascii")
    calls = []

    def tracked_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0 if command[1] == "rm" else 1,
            stderr=None if command[1] == "rm" else "Error: No such object: thebitlab-grade-test",
        )

    monkeypatch.setattr(grade_activity.subprocess, "run", tracked_run)

    grade_activity.remove_docker_container(cidfile, "thebitlab-grade-test")

    assert calls[0][0] == ["docker", "rm", "-f", "thebitlab-grade-test"]
    assert calls[1][0] == ["docker", "inspect", "thebitlab-grade-test"]
    assert calls[0][1]["timeout"] == 5
    assert calls[0][1]["stdout"] is subprocess.DEVNULL
    assert calls[0][1]["stderr"] is subprocess.DEVNULL
    assert calls[1][1]["stdout"] is subprocess.DEVNULL
    assert calls[1][1]["stderr"] is subprocess.PIPE
    assert calls[1][1]["text"] is True
    assert not cidfile.exists()


def test_remove_docker_container_rejects_invalid_name(monkeypatch, tmp_path) -> None:
    cidfile = tmp_path / "container.cid"
    cidfile.write_text("not-a-container; rm -rf .", encoding="ascii")
    calls = []
    monkeypatch.setattr(
        grade_activity.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(grade_activity.DockerCleanupError, match="Nome container"):
        grade_activity.remove_docker_container(cidfile, "invalid container; rm -rf .")

    assert calls == []
    assert cidfile.exists()


def test_remove_docker_container_preserves_cid_when_container_persists(
    monkeypatch,
    tmp_path,
) -> None:
    cidfile = tmp_path / "container.cid"
    container_id = "b" * 64
    cidfile.write_text(container_id, encoding="ascii")
    calls = []

    def persistent_container(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(grade_activity.subprocess, "run", persistent_container)
    monkeypatch.setattr(grade_activity.time, "sleep", lambda _seconds: None)

    with pytest.raises(grade_activity.DockerCleanupError, match="thebitlab-grade-test"):
        grade_activity.remove_docker_container(cidfile, "thebitlab-grade-test")

    assert calls == [
        ["docker", "rm", "-f", "thebitlab-grade-test"],
        ["docker", "inspect", "thebitlab-grade-test"],
        ["docker", "rm", "-f", "thebitlab-grade-test"],
        ["docker", "inspect", "thebitlab-grade-test"],
    ]
    assert cidfile.read_text(encoding="ascii") == container_id


def test_remove_docker_container_rejects_daemon_errors(
    monkeypatch,
    tmp_path,
) -> None:
    cidfile = tmp_path / "container.cid"
    container_id = "c" * 64
    cidfile.write_text(container_id, encoding="ascii")

    def unavailable_daemon(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            stderr="Cannot connect to the Docker daemon",
        )

    monkeypatch.setattr(grade_activity.subprocess, "run", unavailable_daemon)
    monkeypatch.setattr(grade_activity.time, "sleep", lambda _seconds: None)

    with pytest.raises(
        grade_activity.DockerCleanupError,
        match="Cannot connect to the Docker daemon",
    ):
        grade_activity.remove_docker_container(cidfile, "thebitlab-grade-test")

    assert cidfile.read_text(encoding="ascii") == container_id


def test_prepare_docker_workspace_copies_only_runner_inputs(tmp_path) -> None:
    activity_path = tmp_path / "activity.json"
    source_path = tmp_path / "main.c"
    secret_path = tmp_path / ".secret"
    activity_path.write_text("{}", encoding="utf-8")
    source_path.write_text("int main(void){return 0;}", encoding="utf-8")
    secret_path.write_text("non deve entrare nel container", encoding="utf-8")

    workspace, copied_source = grade_activity.prepare_docker_workspace(
        activity_path,
        source_path,
        tmp_path / "docker",
    )

    assert copied_source == workspace / "source" / "main.c"
    assert not (workspace / "activity").exists()
    assert not (workspace / "scripts").exists()
    assert not (workspace / ".secret").exists()


def test_worker_request_contains_only_current_input() -> None:
    test_case = activity()["test_cases"][0]

    request = grade_activity.build_worker_request(activity(), test_case, "c")

    assert request == {
        "schema_version": grade_activity.DOCKER_WORKER_SCHEMA,
        "language": "c",
        "stdin": "2 3\n",
    }
    serialized = json.dumps(request)
    assert "expected_stdout" not in serialized
    assert "somma positiva" not in serialized
    assert "somma con negativo" not in serialized


def test_worker_rejects_teacher_only_fields() -> None:
    request = {
        "schema_version": grade_activity.DOCKER_WORKER_SCHEMA,
        "language": "python",
        "stdin": "",
        "expected_stdout": "segreto",
    }

    with pytest.raises(ValueError, match="campi non consentiti"):
        grade_activity.load_worker_request(__import__("io").StringIO(json.dumps(request)))


def test_finalize_worker_report_compares_expected_output_only_on_host(tmp_path) -> None:
    teacher_activity = {
        "id": "python-hidden",
        "language": "python",
        "test_cases": [
            {"name": "caso riservato", "stdin": "4\n", "expected_stdout": "5\n"},
        ],
    }
    worker_report = {
        "passed": False,
        "status": "failed",
        "language": "python",
        "source": "/submission/source/main.py",
        "worker_schema_version": grade_activity.DOCKER_WORKER_SCHEMA,
        "tests": [
            {
                "name": "test",
                "status": "failed",
                "returncode": 0,
                "stdout": "5\n",
                "stderr": "",
            }
        ],
    }

    report = grade_activity.finalize_worker_report(
        teacher_activity,
        [worker_report],
        tmp_path / "main.py",
    )

    assert report["passed"] is True
    assert report["summary"] == {"passed": 1, "total": 1}
    assert report["tests"][0]["name"] == "caso riservato"
    assert report["tests"][0]["expected_stdout"] == "5\n"


def test_prepare_docker_workspace_rejects_input_outside_authorized_root(tmp_path) -> None:
    teacher_root = tmp_path / "teacher"
    student_root = tmp_path / "student"
    outside = tmp_path / "outside"
    teacher_root.mkdir()
    student_root.mkdir()
    outside.mkdir()
    activity_path = teacher_root / "activity.json"
    source_path = outside / "main.py"
    activity_path.write_text("{}", encoding="utf-8")
    source_path.write_text("print(1)\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source deve trovarsi dentro"):
        grade_activity.prepare_docker_workspace(
            activity_path,
            source_path,
            tmp_path / "docker",
            activity_root=teacher_root,
            source_root=student_root,
        )


def test_prepare_docker_workspace_rejects_symlink_escaping_source_root(tmp_path) -> None:
    teacher_root = tmp_path / "teacher"
    student_root = tmp_path / "student"
    teacher_root.mkdir()
    student_root.mkdir()
    activity_path = teacher_root / "activity.json"
    outside = tmp_path / "secret.py"
    linked_source = student_root / "main.py"
    activity_path.write_text("{}", encoding="utf-8")
    outside.write_text("print('secret')\n", encoding="utf-8")
    try:
        linked_source.symlink_to(outside)
    except OSError:
        pytest.skip("Creazione symlink non consentita su questa piattaforma.")

    with pytest.raises(ValueError, match="source deve trovarsi dentro"):
        grade_activity.prepare_docker_workspace(
            activity_path,
            linked_source,
            tmp_path / "docker",
            activity_root=teacher_root,
            source_root=student_root,
        )


def test_run_docker_grading_reports_missing_docker(monkeypatch, tmp_path, capsys) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = None
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def missing_docker(*args, **kwargs):
        raise FileNotFoundError

    calls = {"count": 0}

    def tracked_missing_docker(*args, **kwargs):
        calls["count"] += 1
        return missing_docker(*args, **kwargs)

    monkeypatch.setattr(grade_activity, "run_bounded_process", tracked_missing_docker)
    cleanup_calls = []
    monkeypatch.setattr(
        grade_activity,
        "remove_docker_container",
        lambda *args, **kwargs: cleanup_calls.append((args, kwargs)),
    )

    assert grade_activity.run_docker_grading(Args()) == 1
    assert calls["count"] == 1
    assert cleanup_calls == []
    assert "Docker non trovato" in capsys.readouterr().out


def test_run_docker_grading_reports_docker_timeout(monkeypatch, tmp_path) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = None
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def timeout_docker(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="docker run", timeout=kwargs["timeout"])

    calls = {"count": 0}

    def tracked_timeout(*args, **kwargs):
        calls["count"] += 1
        return timeout_docker(*args, **kwargs)

    monkeypatch.setattr(grade_activity, "run_bounded_process", tracked_timeout)

    assert grade_activity.run_docker_grading(Args()) == 1
    assert calls["count"] == 1


def test_docker_timeout_scales_with_test_cases() -> None:
    activity = {"test_cases": [{"name": "uno"}, {"name": "due"}, {"name": "tre"}]}

    assert grade_activity.docker_timeout_seconds(activity, 5) == 30
    assert grade_activity.docker_timeout_seconds({**activity, "linguaggio": "javascript"}, 5) == 60
    assert grade_activity.docker_timeout_seconds({**activity, "linguaggio": "c"}, 5, "javascript") == 60


def test_run_bounded_process_rejects_excessive_output(tmp_path) -> None:
    child_pid_path = tmp_path / "child.pid"
    child_code = (
        "import signal, time; "
        + ("signal.signal(signal.SIGBREAK, signal.SIG_IGN); " if os.name == "nt" else "")
        + "time.sleep(30)"
    )
    parent_code = (
        "import pathlib, subprocess, sys; "
        f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}], "
        "stdin=sys.stdin, stdout=sys.stdout); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "print('x' * 4096, flush=True)"
    )

    with pytest.raises(ValueError, match="limite output"):
        grade_activity.run_bounded_process(
            [sys.executable, "-c", parent_code],
            input_text="",
            timeout=5,
            max_output_bytes=128,
        )

    child_pid = int(child_pid_path.read_text())
    process_deadline = time.monotonic() + 2
    while time.monotonic() < process_deadline and process_is_running(child_pid):
        time.sleep(0.05)
    assert not process_is_running(
        child_pid
    ), "Il processo discendente e rimasto attivo dopo il limite output."


def test_run_bounded_process_discards_stderr() -> None:
    result = grade_activity.run_bounded_process(
        [
            sys.executable,
            "-c",
            "import sys; sys.stderr.write('x' * 4096); print('{}')",
        ],
        input_text="",
        timeout=5,
        max_output_bytes=128,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "{}"
    assert result.stderr == ""


def test_run_bounded_process_times_out_while_stdin_is_blocked() -> None:
    started = time.monotonic()

    with pytest.raises(subprocess.TimeoutExpired):
        grade_activity.run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            input_text="x" * (8 * 1024 * 1024),
            timeout=0.1,
        )

    assert time.monotonic() - started < 2


def test_run_bounded_process_times_out_when_descendant_keeps_stdout_open() -> None:
    started = time.monotonic()
    child_code = "import time; time.sleep(30)"
    parent_code = (
        "import subprocess, sys; "
        f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}], "
        "stdin=sys.stdin, stdout=sys.stdout); "
        "print(child.pid, flush=True)"
    )

    with pytest.raises(subprocess.TimeoutExpired) as raised:
        grade_activity.run_bounded_process(
            [sys.executable, "-c", parent_code],
            input_text="",
            timeout=0.5,
        )

    assert time.monotonic() - started < 2
    child_pid = int(raised.value.output.decode("ascii").strip())

    process_deadline = time.monotonic() + 2
    while time.monotonic() < process_deadline and process_is_running(child_pid):
        time.sleep(0.05)
    assert not process_is_running(
        child_pid
    ), "Il processo discendente e rimasto attivo dopo il timeout."


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

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = "non-json"
        stderr = "errore container"

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())

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

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = json.dumps({"error": "errore infrastrutturale"})
        stderr = "errore container"

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())

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

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 0
        stdout = json.dumps({"ok": True})
        stderr = ""

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())

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

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = json.dumps({"passed": "false", "status": 500})
        stderr = "errore container"

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())

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

    write_valid_docker_activity(Args.activity)
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 1
        stdout = json.dumps({"passed": True, "status": "passed"})
        stderr = "errore container"

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())

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

    Args.activity.write_text(
        json.dumps(
            {
                "id": "c-one",
                "language": "c",
                "test_cases": [{"name": "uno", "stdin": "", "expected_stdout": "5\n"}],
            }
        ),
        encoding="utf-8",
    )
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Result:
        returncode = 0
        stdout = json.dumps(
            {
                "passed": False,
                "status": "failed",
                "language": "c",
                "worker_schema_version": grade_activity.DOCKER_WORKER_SCHEMA,
                "tests": [{"name": "test", "status": "failed", "returncode": 0, "stdout": "5\n", "stderr": ""}],
            }
        )
        stderr = ""

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())
    monkeypatch.setattr(
        grade_activity,
        "remove_docker_container",
        lambda *args, **kwargs: None,
    )

    assert grade_activity.run_docker_grading(Args()) == 0
    report = json.loads(Args.report.read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["summary"] == {"passed": 1, "total": 1}


def test_run_docker_grading_omits_worker_stderr_from_cli_output(monkeypatch, tmp_path, capsys) -> None:
    class Args:
        activity = tmp_path / "activity.json"
        source = tmp_path / "main.c"
        report = None
        language = "c"
        timeout = 5
        docker_image = "thebitlab-assignment-runner"
        assignment_id = "assignment-001"
        student_id = "rossi-mario"
        commit = "a" * 40
        submitted_at = "2026-07-24T18:00:00Z"
        source_repo_path = "assignments/activity-001/main.c"

    Args.activity.write_text(
        json.dumps(
            {
                "id": "activity-001",
                "language": "c",
                "test_cases": [{"name": "uno", "stdin": "", "expected_stdout": "ok\n"}],
            }
        ),
        encoding="utf-8",
    )
    Args.source.write_text("int main(void){return 0;}", encoding="utf-8")

    class Result:
        returncode = 0
        stdout = json.dumps(
            {
                "passed": False,
                "status": "failed",
                "language": "c",
                "worker_schema_version": grade_activity.DOCKER_WORKER_SCHEMA,
                "tests": [{"name": "test", "status": "failed", "returncode": 0, "stdout": "ok\n", "stderr": ""}],
            }
        )
        stderr = "THEBITLAB_HIDDEN_STDIN_91d5f0"

    monkeypatch.setattr(grade_activity, "run_bounded_process", lambda *args, **kwargs: Result())
    monkeypatch.setattr(
        grade_activity,
        "remove_docker_container",
        lambda *args, **kwargs: None,
    )

    assert grade_activity.run_docker_grading(Args()) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert captured.err == ""
    assert "THEBITLAB_HIDDEN_STDIN_91d5f0" not in captured.out
    assert report["assignment_id"] == "assignment-001"
    assert report["student_id"] == "rossi-mario"
    assert report["commit"] == "a" * 40
    assert report["submitted_at"] == "2026-07-24T18:00:00Z"
    assert report["source"] == "assignments/activity-001/main.c"


def test_main_applies_authorized_roots_without_docker(monkeypatch, tmp_path) -> None:
    teacher_root = tmp_path / "teacher"
    student_root = tmp_path / "student"
    outside = tmp_path / "outside"
    teacher_root.mkdir()
    student_root.mkdir()
    outside.mkdir()
    activity_path = teacher_root / "activity.json"
    source_path = outside / "main.py"
    activity_path.write_text(
        json.dumps(
            {
                "id": "activity-001",
                "linguaggio": "python",
                "test_cases": [{"expected_stdout": "1\n"}],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text("print(1)\n", encoding="utf-8")
    monkeypatch.setattr(
        grade_activity,
        "parse_args",
        lambda: argparse.Namespace(
            activity=activity_path,
            source=source_path,
            activity_root=teacher_root,
            source_root=student_root,
            language="python",
            timeout=5,
            docker=False,
            report=None,
            assignment_id=None,
            student_id=None,
            commit=None,
            submitted_at=None,
            source_repo_path=None,
        ),
    )

    with pytest.raises(ValueError, match="source deve trovarsi dentro"):
        grade_activity.main()


def test_docker_command_requires_paths_inside_workspace(tmp_path) -> None:
    outside = tmp_path.parent / "outside.c"
    outside.write_text("int main(void){return 0;}", encoding="utf-8")
    try:
        grade_activity.docker_command(
            source=outside,
            timeout_seconds=5,
            workspace=tmp_path,
        )
    except ValueError as error:
        assert "source deve trovarsi dentro il workspace" in str(error)
    else:
        raise AssertionError("docker_command should reject paths outside workspace")
