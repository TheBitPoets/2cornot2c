"""Exercise network failures offline, including the real PowerShell wrapper."""

from dataclasses import replace
import shutil
import subprocess

import pytest

from installer import diagnostics, tui
from installer.executor import execute_plan
from installer.model import Check, Host, Provider
from installer.plans import NETWORK_CHECK_URL, install_plan


def network_plan(provider=Provider.DOCKER):
    plan = install_plan(Host.WINDOWS_AMD64, provider)
    check = next(check for check in plan.checks if check.key == "network")
    return replace(plan, checks=(check,))


@pytest.mark.parametrize("provider", [Provider.DOCKER, Provider.VIRTUALBOX])
@pytest.mark.parametrize("failure", ["request-timeout", "process-timeout", "other", "missing"])
def test_network_failure_context_and_retry_guidance(monkeypatch, provider, failure):
    plan = network_plan(provider)

    def fail(command, **kwargs):
        assert kwargs["timeout"] == 20
        if failure == "process-timeout":
            raise subprocess.TimeoutExpired(command, 20)
        if failure == "missing":
            raise FileNotFoundError(command[0])
        detail = "CLASSROOM_NETWORK_TIMEOUT: request expired" if failure == "request-timeout" else "HTTP 403"
        return subprocess.CompletedProcess(command, 1, "", detail)

    monkeypatch.setattr(diagnostics.subprocess, "run", fail)
    result, = diagnostics.diagnose(plan)
    is_timeout = failure.endswith("timeout")
    assert not result.ok
    assert result.reason == ("timeout" if is_timeout else "missing" if failure == "missing" else "")
    assert NETWORK_CHECK_URL in result.detail
    assert "metodo: HEAD" in result.detail
    assert "timeout richiesta: 15 s" in result.detail
    assert "limite controllo: 20 s" in result.detail
    monkeypatch.setattr(tui, "install_plan", lambda *args: plan)
    state = tui.State(Host.WINDOWS_AMD64, (provider,))
    tui.refresh_report(state)
    report = "\n".join(state.report)
    assert "ERRORE E07" in report
    assert ("[DA RIPROVARE]" in report) is is_timeout
    assert ("controllo della connessione è scaduto" in report) is is_timeout
    assert NETWORK_CHECK_URL in report
    assert "l'URL indicato nei dettagli" in report
    assert "Controlla con il browser che Internet funzioni" not in report
    calls = []
    applied = execute_plan(plan, (result,), runner=lambda cmd: calls.append(cmd))
    assert not calls
    assert applied[0].status == "blocked"


@pytest.mark.skipif(not shutil.which("powershell.exe"), reason="Windows PowerShell required")
@pytest.mark.parametrize("status", ["Timeout", "NameResolutionFailure", "ProtocolError", "success"])
def test_powershell_reports_typed_timeout_without_network(status):
    plan = network_plan()
    check = plan.checks[0]
    stub = """
function Invoke-WebRequest {
    [CmdletBinding()]
    param([Parameter(Position=0)][string]$Uri, [switch]$UseBasicParsing,
          [string]$Method, [int]$TimeoutSec)
    if ($Method -ne 'Head' -or $TimeoutSec -ne 15 -or $Uri -ne '__URL__') {
        throw 'Unexpected request parameters'
    }
    __RESULT__
}
""".replace("__URL__", NETWORK_CHECK_URL).replace(
        "__RESULT__", "return 'OK'" if status == "success" else
        f"throw [System.Net.WebException]::new('offline cause', [System.Net.WebExceptionStatus]::{status})",
    )
    check = replace(check, command=(*check.command[:-1], stub + check.command[-1]))
    result = diagnostics.run_check(check)
    assert result.ok is (status == "success")
    assert result.reason == ("timeout" if status == "Timeout" else "")
    if not result.ok:
        assert "offline cause" in result.detail
        assert NETWORK_CHECK_URL in result.detail
    else:
        assert result.detail == "exit code 0"


def test_failure_context_survives_large_stderr(monkeypatch):
    check = network_plan().checks[0]
    monkeypatch.setattr(diagnostics.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args[0], 1, "", "x" * 900))
    result = diagnostics.run_check(check)
    assert len(result.detail) == 600
    assert result.detail.startswith(check.failure_context)


def test_timeout_marker_does_not_reclassify_unrelated_checks(monkeypatch):
    monkeypatch.setattr(diagnostics.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args[0], 1, "", "CLASSROOM_NETWORK_TIMEOUT: text"))
    result = diagnostics.run_check(Check("docker", "Docker", ("docker", "info")))
    assert result.reason == ""


def test_macos_context_matches_its_probe():
    plan = install_plan(Host.MACOS_ARM64, Provider.DOCKER)
    check = next(check for check in plan.checks if check.key == "network")
    assert check.command[-1] == NETWORK_CHECK_URL
    assert "--head" in check.command
    assert "metodo: HEAD" in check.failure_context
    assert "limite controllo: 20 s" in check.failure_context
    assert "15 s" not in check.failure_context
