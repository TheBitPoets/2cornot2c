"""Piani supportati dall'installer, separati dalla presentazione uTUI."""

from __future__ import annotations

import sys

from installer.model import Check, Host, InstallPlan, Provider, Step
from installer.student_dev import immutable_reference
from installer.tool_versions import MINIMUM_TOOL_VERSIONS


def _winget_ensure(package_id: str) -> tuple[str, ...]:
    """Aggiorna un pacchetto esistente oppure lo installa se assente."""

    agreements = (
        "--accept-package-agreements --accept-source-agreements"
    )
    command = (
        f"winget upgrade --id '{package_id}' --exact --silent {agreements}; "
        "if ($LASTEXITCODE -eq 0) { exit 0 }; "
        f"winget install --id '{package_id}' --exact --silent {agreements}; "
        "exit $LASTEXITCODE"
    )
    return (
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command,
    )


def supported_providers(host: Host) -> tuple[Provider, ...]:
    """Restituisce solo i provider ufficialmente supportati per l'host."""

    if host is Host.MACOS_ARM64:
        return (Provider.VMWARE, Provider.DOCKER)
    if host is Host.WINDOWS_AMD64:
        return (Provider.VIRTUALBOX, Provider.DOCKER)
    raise ValueError(f"Host non supportato: {host}")


def install_plan(host: Host, provider: Provider) -> InstallPlan:
    """Costruisce il piano deterministico per host e provider."""

    if provider not in supported_providers(host):
        raise ValueError(f"{provider.value} non è supportato su {host.value}")

    if provider is Provider.DOCKER:
        plan = _docker_plan(host)
    elif host is Host.MACOS_ARM64:
        plan = _macos_plan(provider)
    else:
        plan = _windows_plan()
    resources = Check(
        "resources",
        "Risorse minime",
        (
            sys.executable,
            "-m",
            "installer.preflight",
            "--provider",
            provider.value,
        ),
    )
    connectivity = (
        Check(
            "network",
            "Connessione download",
            (
                "/usr/bin/curl",
                "--fail",
                "--silent",
                "--show-error",
                "--head",
                "https://raw.githubusercontent.com/"
                "TheBitPoets/2cornot2c/main/README.md",
            ),
        )
        if host is Host.MACOS_ARM64
        else Check(
            "network",
            "Connessione download",
            (
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Invoke-WebRequest -UseBasicParsing -Method Head -TimeoutSec 15 "
                "'https://raw.githubusercontent.com/"
                "TheBitPoets/2cornot2c/main/README.md' | Out-Null",
            ),
        )
    )
    checks = (resources, connectivity, *plan.checks)
    steps = plan.steps
    if provider in {Provider.VMWARE, Provider.VIRTUALBOX}:
        image_command = (
            sys.executable,
            "-m",
            "installer.classroom_images",
            "--provider",
            provider.value,
            "--host",
            host.value,
        )
        checks = (
            *checks,
            Check(
                "classroom-image",
                "Box Packer preconfigurata",
                (*image_command, "--check"),
            ),
        )
        steps = (
            *steps,
            Step(
                "classroom-image",
                "Scarica e configura la box Packer",
                (*image_command, "--install"),
            ),
        )
    return InstallPlan(
        plan.host,
        plan.provider,
        checks,
        steps,
    )


def _macos_plan(provider: Provider) -> InstallPlan:
    checks = [
        Check("brew", "Homebrew", ("brew", "--version")),
        Check("git", "Git", ("git", "--version")),
        Check("vagrant", "Vagrant", ("vagrant", "--version")),
    ]
    steps = [
        Step("brew", "Installa Homebrew", None, manual=True),
        Step("git", "Installa Git", ("brew", "install", "git")),
        Step("vagrant", "Installa Vagrant", ("brew", "install", "--cask", "vagrant")),
    ]

    if provider is Provider.VMWARE:
        checks.extend(
            [
                Check(
                    "fusion",
                    "VMware Fusion",
                    ("test", "-d", "/Applications/VMware Fusion.app"),
                ),
                Check(
                    "vmware-utility",
                    "Vagrant VMware Utility",
                    ("test", "-x", "/opt/vagrant-vmware-desktop/bin/vagrant-vmware-utility"),
                ),
                Check(
                    "vmware-plugin",
                    "Plugin Vagrant VMware",
                    ("vagrant", "plugin", "list"),
                    "vagrant-vmware-desktop",
                ),
            ]
        )
        steps.extend(
            [
                Step(
                    "fusion",
                    "Installa VMware Fusion",
                    None,
                    manual=True,
                    detail="Broadcom richiede login e accettazione della licenza.",
                ),
                Step(
                    "vmware-utility",
                    "Installa Vagrant VMware Utility",
                    ("brew", "install", "--cask", "vagrant-vmware-utility"),
                ),
                Step(
                    "vmware-plugin",
                    "Installa plugin Vagrant VMware",
                    ("vagrant", "plugin", "install", "vagrant-vmware-desktop"),
                ),
            ]
        )
    else:
        checks.append(Check("virtualbox", "VirtualBox", ("VBoxManage", "--version")))
        steps.append(
            Step(
                "virtualbox",
                "Installa VirtualBox",
                ("brew", "install", "--cask", "virtualbox"),
            )
        )

    return InstallPlan(Host.MACOS_ARM64, provider, tuple(checks), tuple(steps))


def _windows_plan() -> InstallPlan:
    return InstallPlan(
        Host.WINDOWS_AMD64,
        Provider.VIRTUALBOX,
        (
            Check("winget", "Windows Package Manager", ("winget", "--version")),
            Check(
                "git",
                "Git",
                ("git", "--version"),
                minimum_version=MINIMUM_TOOL_VERSIONS["git"],
            ),
            Check(
                "vagrant",
                "Vagrant",
                ("vagrant", "--version"),
                minimum_version=MINIMUM_TOOL_VERSIONS["vagrant"],
            ),
            Check(
                "virtualbox",
                "VirtualBox",
                ("VBoxManage.exe", "--version"),
                minimum_version=MINIMUM_TOOL_VERSIONS["virtualbox"],
            ),
        ),
        (
            Step(
                "git",
                "Installa o aggiorna Git",
                _winget_ensure("Git.Git"),
            ),
            Step(
                "vagrant",
                "Installa o aggiorna Vagrant",
                _winget_ensure("Hashicorp.Vagrant"),
            ),
            Step(
                "virtualbox",
                "Installa o aggiorna VirtualBox",
                _winget_ensure("Oracle.VirtualBox"),
            ),
        ),
    )


def _docker_plan(host: Host) -> InstallPlan:
    image = immutable_reference()
    common_checks = (
        Check(
            "docker",
            "Docker CLI",
            ("docker", "--version"),
            minimum_version=(
                MINIMUM_TOOL_VERSIONS["docker"]
                if host is Host.WINDOWS_AMD64
                else ""
            ),
        ),
        Check("docker-engine", "Motore Docker avviato", ("docker", "info")),
        Check(
            "student-image",
            "Immagine Ubuntu student-dev",
            ("docker", "image", "inspect", image),
        ),
    )
    if host is Host.MACOS_ARM64:
        return InstallPlan(
            host,
            Provider.DOCKER,
            (
                Check("brew", "Homebrew", ("brew", "--version")),
                *common_checks,
            ),
            (
                Step("brew", "Installa Homebrew", None, manual=True),
                Step(
                    "docker",
                    "Installa Docker Desktop",
                    ("brew", "install", "--cask", "docker-desktop"),
                ),
                Step(
                    "docker-engine",
                    "Avvia Docker Desktop",
                    None,
                    manual=True,
                    detail=(
                        "Apri Docker Desktop e completa autorizzazioni e condizioni "
                        "d'uso; poi rilancia l'installer."
                    ),
                    deferred=True,
                ),
                Step("student-image", "Scarica student-dev", ("docker", "pull", image)),
            ),
        )
    return InstallPlan(
        host,
        Provider.DOCKER,
        (
            Check("winget", "Windows Package Manager", ("winget", "--version")),
            Check("wsl", "WSL 2", ("wsl.exe", "--status")),
            *common_checks,
        ),
        (
            Step(
                "wsl",
                "Prepara WSL 2",
                (
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    (
                        "& (Join-Path $env:LOCALAPPDATA "
                        "'2cornot2c\\prepare-wsl-windows.ps1')"
                    ),
                ),
                detail=(
                    "WSL 2 e Virtual Machine Platform vengono installati "
                    "automaticamente."
                ),
                restart_after_success=True,
            ),
            Step(
                "docker",
                "Installa o aggiorna Docker Desktop",
                _winget_ensure("Docker.DockerDesktop"),
            ),
            Step(
                "docker-engine",
                "Avvia e prepara Docker Desktop",
                (
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    (
                        "$app = Join-Path $env:ProgramFiles "
                        "'Docker\\Docker\\Docker Desktop.exe'; "
                        "$cli = Join-Path $env:ProgramFiles "
                        "'Docker\\Docker\\resources\\bin\\docker.exe'; "
                        "if (-not (Test-Path $app)) { "
                        "Write-Error 'Docker Desktop non trovato'; exit 17 }; "
                        "Start-Process -FilePath $app; "
                        "Write-Output "
                        "'Docker Desktop avviato: attendo che sia pronto...'; "
                        "for ($i = 0; $i -lt 120; $i++) { "
                        "& $cli info *> $null; "
                        "if ($LASTEXITCODE -eq 0) { "
                        "Write-Output 'Docker Desktop è pronto'; exit 0 }; "
                        "Start-Sleep -Seconds 5 }; "
                        "Write-Error "
                        "'Docker Desktop non è diventato pronto in 10 minuti'; "
                        "exit 19"
                    ),
                ),
                detail=(
                    "Docker Desktop viene aperto automaticamente e il setup "
                    "attende che sia pronto."
                ),
            ),
            Step(
                "student-image",
                "Scarica student-dev",
                (
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    (
                        "$dockerBin = Join-Path $env:ProgramFiles "
                        "'Docker\\Docker\\resources\\bin'; "
                        "$env:Path = $dockerBin + ';' + $env:Path; "
                        "$cli = Join-Path $dockerBin 'docker.exe'; "
                        "$credential = Join-Path $dockerBin "
                        "'docker-credential-desktop.exe'; "
                        "if (-not (Test-Path $credential)) { "
                        "Write-Error "
                        "'Helper credenziali Docker Desktop non trovato'; "
                        "exit 20 }; "
                        f"& $cli pull '{image}'; exit $LASTEXITCODE"
                    ),
                ),
            ),
        ),
    )
