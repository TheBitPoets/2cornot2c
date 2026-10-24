from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from installer import environments, lifecycle
from installer.environments import Environment
from installer.model import Provider


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    for relative in ("docker/student-dev/toolchain.lock.json", "packer/classroom-releases.lock.json"):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    return tmp_path


def add_vm(project):
    identity = project / ".vagrant/machines/default/virtualbox/id"
    identity.parent.mkdir(parents=True)
    identity.write_text("classroom-vm-id", encoding="utf-8")
    (project / ".classroom-box").write_text("classroom/test", encoding="utf-8")
    (project / ".classroom-provider").write_text("virtualbox", encoding="utf-8")


@pytest.mark.parametrize("vm,docker", [(True, True), (True, False), (False, True), (False, False)])
def test_inventory_detects_both_independently(project, monkeypatch, vm, docker):
    if vm:
        add_vm(project)
    calls = []

    def probe(*command):
        calls.append(command)
        if command[0] == "docker" and command[1:3] == ("image", "inspect"):
            return 0 if docker else 1
        return 0

    monkeypatch.setattr(environments, "_probe", probe)
    items = environments.detect_windows_environments(project)
    assert [(item.provider, item.launchable) for item in items] == [
        (Provider.VIRTUALBOX, vm), (Provider.DOCKER, docker),
    ]
    assert all(command[1] in {"--version", "info", "image", "showvminfo"} for command in calls)


@pytest.mark.parametrize("failure", ["engine", "image", "cli", "timeout"])
def test_docker_unavailable_never_inferred_from_saved_choice(project, monkeypatch, failure):
    (project / "selected-provider.txt").write_text("docker", encoding="utf-8")
    calls = []

    def probe(*command):
        calls.append(command)
        if command[1] == "--version" and failure == "cli":
            return None
        if command[1] == "info" and failure == "engine":
            return 1
        if command[1] == "image":
            return None if failure == "timeout" else 1
        return 0

    monkeypatch.setattr(environments, "_probe", probe)
    item = environments.detect_windows_environments(project)[1]
    assert not item.launchable
    if failure in {"engine", "cli"}:
        assert not any(command[1] == "image" for command in calls)
    if failure == "engine":
        assert item.status == "Da verificare"
        assert "Docker Desktop" in item.detail


@pytest.mark.parametrize("problem", ["empty-id", "wrong-provider", "unregistered", "missing-vagrant", "other-machine"])
def test_vm_stale_or_unrelated_state_is_not_launchable(project, monkeypatch, problem):
    add_vm(project)
    identity = project / ".vagrant/machines/default/virtualbox/id"
    if problem == "empty-id":
        identity.write_text("", encoding="utf-8")
    elif problem == "wrong-provider":
        (project / ".classroom-provider").write_text("vmware_desktop", encoding="utf-8")
    elif problem == "other-machine":
        identity.parent.rename(identity.parent.with_name("vmware_desktop"))

    def probe(*command):
        if command[0] == "VBoxManage.exe" and problem == "unregistered":
            return 1
        if command[0] == "vagrant" and problem == "missing-vagrant":
            return None
        return 0

    monkeypatch.setattr(environments, "_probe", probe)
    assert not environments.detect_windows_environments(project)[0].launchable


def test_vm_pending_release_uses_existing_vm_only(project, monkeypatch):
    add_vm(project)
    lock_path = project / "packer/classroom-releases.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["targets"]["windows-amd64-virtualbox"].update(
        active_release=None, candidate_version="1.0.0",
    )
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    (project / ".classroom-box").unlink()
    (project / ".classroom-provider").unlink()
    monkeypatch.setattr(environments, "_probe", lambda *args: 0)
    assert environments.detect_windows_environments(project)[0].launchable
    (project / ".vagrant/machines/default/virtualbox/id").unlink()
    assert not environments.detect_windows_environments(project)[0].launchable


@pytest.mark.parametrize("problem", ["missing-lock", "invalid-lock", "invalid-box"])
def test_vm_markers_do_not_override_invalid_vagrant_configuration(project, monkeypatch, problem):
    add_vm(project)
    lock_path = project / "packer/classroom-releases.lock.json"
    if problem == "missing-lock":
        lock_path.unlink()
    elif problem == "invalid-lock":
        lock_path.write_text("{}", encoding="utf-8")
    else:
        (project / ".classroom-box").write_text("invalid box name", encoding="utf-8")
    monkeypatch.setattr(environments, "_probe", lambda *args: 0)

    vm, docker = environments.detect_windows_environments(project)

    assert not vm.launchable
    assert docker.launchable


@pytest.mark.parametrize("exception", [OSError("unavailable"), subprocess.TimeoutExpired("docker", 5)])
def test_probe_is_bounded_and_read_only(monkeypatch, exception):
    def run(command, **kwargs):
        assert kwargs["timeout"] == 5
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert "shell" not in kwargs
        raise exception

    monkeypatch.setattr(environments.subprocess, "run", run)
    assert environments._probe("docker", "info") is None


def test_null_active_vm_version_keeps_docker_and_tui_available(project, monkeypatch):
    pytest.importorskip("utui")
    from installer import tui
    from installer.model import Host

    add_vm(project)
    lock_path = project / "packer/classroom-releases.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["targets"]["windows-amd64-virtualbox"]["active_release"]["version"] = None
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    monkeypatch.setattr(environments, "installed_project", lambda: project)
    monkeypatch.setattr(environments, "_probe", lambda *args: 0)
    state = tui.State(Host.WINDOWS_AMD64, (Provider.VIRTUALBOX, Provider.DOCKER), screen="home")

    tui.open_home_action(state)

    vm, docker = state.environments
    assert state.running and state.screen == "launch"
    assert not vm.launchable and docker.launchable
    assert "Docker leggero - Installato" in "\n".join(tui.frame(state, 80, 25, color=False))


def test_custom_installation_and_explicit_provider_use_current_launcher(tmp_path, monkeypatch):
    monkeypatch.setattr(environments.Path, "home", lambda: tmp_path)
    project = tmp_path / "custom project"
    script = project / "scripts/launch-classroom-windows.ps1"
    script.parent.mkdir(parents=True)
    script.touch()
    state = tmp_path / ".2cornot2c"
    state.mkdir()
    (state / "bootstrap-state.json").write_text(json.dumps({"install_dir": str(project)}), encoding="utf-8-sig")
    for provider in (Provider.VIRTUALBOX, Provider.DOCKER):
        command = lifecycle.powershell_action_command("launch", provider=provider)
        assert command[-3:] == (str(script), "-Provider", provider.value)
    with pytest.raises(ValueError):
        lifecycle.powershell_action_command("reset", provider=Provider.DOCKER)


def test_tui_selects_and_launches_both_without_closing(monkeypatch):
    pytest.importorskip("utui")
    from installer import tui
    from installer.model import Host
    from utui import Key

    items = (
        Environment(Provider.VIRTUALBOX, "Installata", "VM pronta", True),
        Environment(Provider.DOCKER, "Installato", "Docker pronto", True),
    )
    monkeypatch.setattr(tui, "detect_windows_environments", lambda: items)
    launched = []
    monkeypatch.setattr(tui, "launch_windows_action", lambda action, **kwargs: launched.append(kwargs["provider"]))
    state = tui.State(Host.WINDOWS_AMD64, (Provider.DOCKER, Provider.VIRTUALBOX), screen="home")
    tui.open_home_action(state)
    assert state.screen == "launch" and not launched
    for width, height in ((80, 25), (120, 30)):
        output = "\n".join(tui.frame(state, width, height, color=False))
        assert "VM completa - Installata" in output
        assert "Docker leggero - Installato" in output
        assert "Invio: avvia" in output
        assert "r: aggiorna elenco" in output
        assert "m/Esc: menu, q: esci" in output
    tui.handle_launch_key(state, Key.ENTER)
    tui.handle_launch_key(state, Key.DOWN)
    tui.handle_launch_key(state, Key.ENTER)
    assert launched == [Provider.VIRTUALBOX, Provider.DOCKER]
    assert state.running
    tui.handle_launch_key(state, Key.ESCAPE)
    assert state.screen == "home" and state.running


def test_tui_unavailable_refresh_and_failed_launch(monkeypatch):
    pytest.importorskip("utui")
    from installer import tui
    from installer.model import Host
    from utui import Key

    state = tui.State(Host.WINDOWS_AMD64, (Provider.DOCKER,))
    monkeypatch.setattr(tui, "detect_windows_environments", lambda: (
        Environment(Provider.DOCKER, "Da verificare", "Apri Docker Desktop"),
    ))
    calls = []
    monkeypatch.setattr(tui, "launch_windows_action", lambda *args, **kwargs: calls.append(args))
    tui.open_home_action(state)
    tui.handle_launch_key(state, Key.ENTER)
    assert not calls and "Docker Desktop" in state.report[0]
    monkeypatch.setattr(tui, "detect_windows_environments", lambda: (
        Environment(Provider.DOCKER, "Installato", "Pronto", True),
    ))
    tui.handle_launch_key(state, Key.CHARACTER, "r")
    tui.handle_launch_key(state, Key.ENTER)
    assert len(calls) == 1

    def fail(*args, **kwargs):
        raise OSError("launcher assente")

    monkeypatch.setattr(tui, "launch_windows_action", fail)
    tui.handle_launch_key(state, Key.ENTER)
    assert state.running and "launcher assente" in "\n".join(state.report)
    monkeypatch.setattr(tui, "detect_windows_environments", fail)
    tui.handle_launch_key(state, Key.CHARACTER, "r")
    tui.handle_launch_key(state, Key.DOWN)
    tui.handle_launch_key(state, Key.ENTER)
    assert not state.environments and state.running
    tui.frame(state, 80, 25, color=False)


@pytest.mark.skipif(not shutil.which("powershell.exe"), reason="Windows PowerShell required")
@pytest.mark.parametrize("selected,saved", [
    ("docker", "virtualbox"), ("virtualbox", "docker"), ("docker", None),
    (None, "docker"), (None, "virtualbox"),
])
def test_real_powershell_dispatch_uses_explicit_selection(tmp_path, selected, saved):
    def quote(path):
        return "'" + str(path).replace("'", "''") + "'"

    state = tmp_path / ".2cornot2c"
    state.mkdir()
    project = tmp_path / "2cornot2c"
    (project / "scripts").mkdir(parents=True)
    (project / ".classroom-box").touch()
    (project / ".classroom-provider").write_text("virtualbox", encoding="utf-8")
    (project / "scripts/setup-vm.ps1").write_text("Write-Output 'LAUNCHED:virtualbox'", encoding="utf-8")
    if saved:
        (state / "selected-provider.txt").write_text(saved, encoding="utf-8")
    source = (ROOT / "scripts/launch-classroom-windows.ps1").read_text(encoding="utf-8-sig")
    source = source.replace("$HOME", quote(tmp_path))
    source = source.replace(
        '$Python = Join-Path $InstallDir ".installer-venv\\Scripts\\python.exe"',
        "$Python = { param($script) Write-Output 'LAUNCHED:docker'; $global:LASTEXITCODE = 0 }",
    )
    script = tmp_path / "launcher.ps1"
    script.write_text(source, encoding="utf-8-sig")
    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
    if selected:
        command.extend(["-Provider", selected])
    result = subprocess.run(
        command,
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    expected = selected or saved
    assert f"LAUNCHED:{expected}" in result.stdout
    assert f"LAUNCHED:{'docker' if expected == 'virtualbox' else 'virtualbox'}" not in result.stdout
    if saved:
        assert (state / "selected-provider.txt").read_text(encoding="utf-8") == saved
    else:
        assert not (state / "selected-provider.txt").exists()
