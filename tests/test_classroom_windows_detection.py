from pathlib import Path
from subprocess import CompletedProcess

import pytest

from installer import diagnostics
from installer.executor import execute_plan
from installer.model import Check, Host, InstallPlan, Provider, Step


@pytest.mark.parametrize(
    "version, compatible", [("7.2.16r174877", True), ("7.0.26r168464", False)]
)
def test_virtualbox_outside_path_is_checked_before_reinstall(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str, compatible: bool
) -> None:
    executable = tmp_path / "Oracle" / "VirtualBox" / "VBoxManage.exe"
    executable.parent.mkdir(parents=True)
    executable.touch()
    monkeypatch.setattr(diagnostics.sys, "platform", "win32")
    monkeypatch.setattr(diagnostics.shutil, "which", lambda _: None)
    monkeypatch.delenv("ProgramW6432", raising=False)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))

    def run(command, **kwargs):
        assert command == (str(executable), "--version")
        return CompletedProcess(command, 0, version, "")

    monkeypatch.setattr(diagnostics.subprocess, "run", run)
    check = Check(
        "virtualbox", "VirtualBox", ("VBoxManage.exe", "--version"),
        minimum_version="7.1.0",
    )
    plan = InstallPlan(
        Host.WINDOWS_AMD64, Provider.VIRTUALBOX, (check,),
        (Step("virtualbox", "VirtualBox", ("install",)),),
    )
    checks = diagnostics.diagnose(plan)
    assert checks[0].present
    assert checks[0].ok is compatible
    calls = []

    def install(command):
        calls.append(command)
        return 0, ""

    results = execute_plan(plan, checks, runner=install)
    assert results[0].status == ("skipped" if compatible else "updated")
    assert calls == ([] if compatible else [("install",)])


@pytest.mark.parametrize("platform, on_path", [("win32", True), ("darwin", False)])
def test_existing_path_and_non_windows_commands_are_preserved(
    monkeypatch: pytest.MonkeyPatch, platform: str, on_path: bool
) -> None:
    monkeypatch.setattr(diagnostics.sys, "platform", platform)
    monkeypatch.setattr(diagnostics.shutil, "which", lambda _: "existing" if on_path else None)
    command = ("VBoxManage.exe", "--version")
    assert diagnostics._resolve_windows_command(command) == command


def test_missing_windows_tool_is_still_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(diagnostics.sys, "platform", "win32")
    monkeypatch.setattr(diagnostics.shutil, "which", lambda _: None)
    monkeypatch.delenv("ProgramW6432", raising=False)
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    command = ("VBoxManage.exe", "--version")
    assert diagnostics._resolve_windows_command(command) == command
