from __future__ import annotations

from pathlib import Path

from installer.model import Host, Provider
from installer.preflight import GIB, ResourceSnapshot, evaluate


ROOT = Path(__file__).resolve().parents[1]


def test_docker_preflight_accepts_minimum_resources() -> None:
    results = evaluate(
        Host.WINDOWS_AMD64,
        Provider.DOCKER,
        ResourceSnapshot(4 * GIB, 8 * GIB, True),
    )

    assert {result.status for result in results} == {"ok"}


def test_vm_preflight_blocks_resources_but_warns_on_unreliable_virtualization() -> None:
    results = evaluate(
        Host.WINDOWS_AMD64,
        Provider.VIRTUALBOX,
        ResourceSnapshot(6 * GIB, 10 * GIB, False),
    )

    assert [result.status for result in results] == [
        "blocked",
        "blocked",
        "warning",
    ]


def test_unknown_measurements_warn_but_do_not_block_sufficient_disk() -> None:
    results = evaluate(
        Host.WINDOWS_AMD64,
        Provider.DOCKER,
        ResourceSnapshot(None, 9 * GIB, None),
    )

    assert [result.status for result in results] == ["warning", "ok", "warning"]


def test_windows_virtualization_probe_accepts_an_active_hypervisor() -> None:
    source = (ROOT / "installer" / "preflight.py").read_text(encoding="utf-8")

    assert "HypervisorPresent" in source
    assert "stato virtualizzazione incerto" in source


def test_windows_lifecycle_scripts_keep_destructive_actions_guarded() -> None:
    bootstrap = (ROOT / "scripts" / "bootstrap-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )
    update = (ROOT / "scripts" / "update-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )
    uninstall = (ROOT / "scripts" / "uninstall-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )
    manager = (ROOT / "scripts" / "manage-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )

    assert "Test-HostResources" in bootstrap
    assert "installed_by_bootstrap" in bootstrap
    assert "Install-ClassroomLauncher" in bootstrap
    assert "launch-classroom-windows.ps1" in bootstrap
    assert "prepare-wsl-windows.ps1" in bootstrap
    assert "remove-wsl-windows.ps1" in bootstrap
    assert "Ambiente 2cornot2c.lnk" in bootstrap
    assert "bootstrap-classroom-windows.ps1" in update
    assert ".installer-venv\\Scripts\\python.exe" in manager
    assert "bootstrap-classroom-windows.ps1" in manager
    assert 'if ($Confirmation -ne "DISINSTALLA")' in uninstall
    assert "Remove-Item -LiteralPath $SafeInstallDir" in uninstall
    assert "TheBitPoets/2cornot2c" in uninstall
    assert "vagrant destroy" not in uninstall
    assert "docker image rm $ImageReference" in uninstall
    assert "docker image rm --force" not in uninstall
    assert "Ambiente 2cornot2c.lnk" in uninstall


def test_windows_launcher_hides_technical_start_commands() -> None:
    launcher = (ROOT / "scripts" / "launch-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )

    assert "selected-provider.txt" in launcher
    assert "student_dev_shell.py" in launcher
    assert "vagrant up --provider=virtualbox" in launcher
    assert "AMBIENTE NON ANCORA PRONTO" in launcher
    assert "Find-ExistingProvider" in launcher
    assert 'Record.key -eq "student-image"' in launcher
    assert "image inspect" in launcher
    assert "Ambiente precedente riconosciuto" in launcher


def test_wsl_preparation_is_elevated_and_resumes_after_restart() -> None:
    source = (ROOT / "scripts" / "prepare-wsl-windows.ps1").read_text(
        encoding="utf-8"
    )

    assert "wsl.exe --install --no-distribution" in source
    assert "-Verb RunAs" in source
    assert "2cornot2c-resume" in source
    assert "RunOnce" in source


def test_wsl_rollback_refuses_to_remove_personal_distributions() -> None:
    cleanup = (ROOT / "scripts" / "remove-wsl-windows.ps1").read_text(
        encoding="utf-8"
    )
    uninstall = (ROOT / "scripts" / "uninstall-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )

    assert "PersonalDistributions" in cleanup
    assert "docker-desktop" in cleanup
    assert "dati personali" in cleanup
    assert "wsl.exe --uninstall" in cleanup
    assert "Test-WslInstalledByClassroom" in uninstall
    assert '"restart_required", "succeeded"' in uninstall
    assert "Start-Sleep -Seconds 2" in uninstall
