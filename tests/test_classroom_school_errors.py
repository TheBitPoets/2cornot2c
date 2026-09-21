"""Regressions for the installation failures photographed in school."""

import json
import subprocess

import pytest

from installer import diagnostics
from installer.diagnostics import CheckResult
from installer.executor import StepResult, execute_plan
from installer.model import Check, Host, InstallPlan, Provider, Step
from installer.student_errors import for_step
from installer.tui import State, _format_results, refresh_report


def docker_plan():
    return InstallPlan(Host.WINDOWS_AMD64, Provider.DOCKER, tuple(
        Check(key, key, (key,)) for key in ("wsl", "docker", "docker-engine", "student-image")
    ), ())


def test_missing_cli_does_not_produce_three_independent_errors(monkeypatch):
    calls = []

    def unavailable(check):
        calls.append(check.key)
        raise FileNotFoundError(check.command[0])

    monkeypatch.setattr(diagnostics, "run_check", unavailable)
    results = diagnostics.diagnose(docker_plan())
    assert calls == ["wsl", "docker"]
    assert [result.reason for result in results] == ["missing", "missing", "dependency", "dependency"]
    assert "FileNotFoundError" not in str(results)
    monkeypatch.setattr("installer.tui.diagnose", lambda plan: results)
    state = State(Host.WINDOWS_AMD64, (Provider.DOCKER,))
    refresh_report(state)
    report = "\n".join(state.report)
    assert "[ATTESA] docker-engine" in report
    assert "[ATTESA] student-image" in report
    assert "Premi a per preparare WSL 2" in report
    assert "Premi a per installare" in report


def test_timeout_is_retryable_and_image_waits_for_engine(monkeypatch):
    calls = []

    def check(item):
        calls.append(item.key)
        if item.key == "docker-engine":
            raise subprocess.TimeoutExpired(item.command, 20)
        return CheckResult(item, True, "ready", True)

    monkeypatch.setattr(diagnostics, "run_check", check)
    results = diagnostics.diagnose(docker_plan())
    assert calls == ["wsl", "docker", "docker-engine"]
    assert results[2].reason == "timeout"
    assert results[3].reason == "dependency"
    monkeypatch.setattr("installer.tui.diagnose", lambda plan: results)
    state = State(Host.WINDOWS_AMD64, (Provider.DOCKER,))
    refresh_report(state)
    assert "[DA RIPROVARE] docker-engine" in "\n".join(state.report)


def test_executor_keeps_first_wsl_cause_and_exit_code_in_ui_and_log(tmp_path):
    check = Check("wsl", "WSL", ("offline",))
    plan = InstallPlan(Host.WINDOWS_AMD64, Provider.DOCKER, (check,), (
        Step("wsl", "WSL", ("offline",)), Step("docker", "Docker", ("must-not-run",)),
    ))
    output = "WSL_INSTALL_FAILED: exit code 50; log: C:/diagnostics/wsl.json\nvirtualization error\nFullyQualifiedErrorId: WriteErrorException"
    calls = []

    def runner(command):
        calls.append(command)
        return 1, output

    log = tmp_path / "installer.jsonl"
    results = execute_plan(plan, (CheckResult(check, False, "missing"),), runner=runner, log_path=log)
    assert calls == [("offline",)]
    assert results[0].status == "failed"
    assert output in results[0].detail
    assert "exit code 1" in results[0].detail
    assert json.loads(log.read_text(encoding="utf-8"))["detail"] == results[0].detail
    assert "virtualization error" in "\n".join(_format_results(Provider.DOCKER, results))


@pytest.mark.parametrize("key, marker, code", [
    ("classroom-image", "CLASSROOM_LEGACY_VM:", "E26"),
    ("classroom-image", "CLASSROOM_STATE_INVALID:", "E27"),
    ("classroom-image", "CLASSROOM_RELEASE_PENDING:", "E28"),
    ("classroom-image", "download failed", "E25"),
    ("wsl", "WSL_UAC_CANCELLED:", "E29"),
])
def test_specific_failures_keep_their_category_through_tui(key, marker, code):
    assert for_step(key, marker).code == code
    report = "\n".join(_format_results(Provider.DOCKER, (StepResult(key, key, "failed", marker),)))
    assert f"ERRORE {code}" in report
    if code in {"E26", "E27", "E28"}:
        assert "Controlla Internet" not in report
