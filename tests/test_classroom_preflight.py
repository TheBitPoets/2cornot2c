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
    assert "function Test-GitMinimumVersion" in bootstrap
    assert '[version]"2.30.0"' in bootstrap
    assert "function Update-WingetPackage" in bootstrap
    assert 'Update-WingetPackage "Git.Git"' in bootstrap
    assert "function Test-Python312" in bootstrap
    assert "sys.version_info[:2] != (3, 12)" in bootstrap
    assert '$ErrorActionPreference = "SilentlyContinue"' in bootstrap
    assert "$ProbeExitCode = 1" in bootstrap
    assert "if (-not (Test-Python312))" in bootstrap
    assert "venv --clear" in bootstrap
    assert "$VenvOutput" in bootstrap
    assert "$VenvExitCode" in bootstrap
    assert "installed_by_bootstrap" in bootstrap
    assert "Install-ClassroomLauncher" in bootstrap
    assert "launch-classroom-windows.ps1" in bootstrap
    assert "prepare-wsl-windows.ps1" in bootstrap
    assert "remove-wsl-windows.ps1" in bootstrap
    assert "remove-classroom-shortcuts-windows.ps1" in bootstrap
    assert "Ambiente 2cornot2c.lnk" in bootstrap
    assert "bootstrap-classroom-windows.ps1" in update
    assert ".installer-venv\\Scripts\\python.exe" in manager
    assert "bootstrap-classroom-windows.ps1" in manager
    assert "if ($Confirmation -ne $RequiredConfirmation)" in uninstall
    assert "Remove-Item -LiteralPath $SafeInstallDir" in uninstall
    assert "TheBitPoets/2cornot2c" in uninstall
    assert "Remove-ClassroomVirtualMachines" in uninstall
    assert "vagrant destroy --force" in uninstall
    assert '"DISINSTALLA TUTTO"' in uninstall
    assert "[switch]$DestroyClassroomVm" in uninstall
    assert '"^2cornot2c/"' in uninstall
    assert "docker image rm $ImageReference" in uninstall
    assert "docker image rm --force" not in uninstall
    assert "Ambiente 2cornot2c.lnk" in uninstall
    assert "Test-PackageStillInstalled" in uninstall
    assert '$Record.status -ne "succeeded"' in uninstall
    assert "Get-ClassroomShortcutPaths" in uninstall
    assert '$LauncherDir "remove-classroom-shortcuts-windows.ps1"' in uninstall
    assert "$ShortcutCleanupSucceeded" in uninstall
    assert "OneDriveConsumer" in uninstall
    assert "CommonDesktopDirectory" in uninstall
    assert "CommonPrograms" in uninstall
    assert '"E31"' in uninstall
    assert uninstall.index("winget uninstall") < uninstall.index(
        "Remove-Item -LiteralPath $SafeInstallDir"
    )

    shortcut_cleanup = (
        ROOT / "scripts" / "remove-classroom-shortcuts-windows.ps1"
    ).read_text(encoding="utf-8")
    assert "Ambiente 2cornot2c.lnk" in shortcut_cleanup
    assert "CommonDesktopDirectory" in shortcut_cleanup
    assert "CommonPrograms" in shortcut_cleanup
    assert "OneDriveConsumer" in shortcut_cleanup
    assert "ie4uinit.exe" in shortcut_cleanup


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
    assert '-File `"$Manager`" -Resume' in source

    manager = (ROOT / "scripts" / "manage-classroom-windows.ps1").read_text(
        encoding="utf-8"
    )
    assert "[switch]$Resume" in manager
    assert 'CLASSROOM_AUTO_RESUME = "1"' in manager


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
    assert "Get-WindowsOptionalFeature" in cleanup
    assert "$RemainingFeatures" in cleanup
    assert "Test-WslInstalledByClassroom" in uninstall
    assert '"restart_required", "succeeded"' in uninstall
    assert "Start-Sleep -Seconds 2" in uninstall
    assert '"E32"' in uninstall
