"""Piani supportati dall'installer, separati dalla presentazione uTUI."""

from __future__ import annotations

from installer.model import Check, Host, InstallPlan, Provider, Step
from installer.student_dev import immutable_reference


def supported_providers(host: Host) -> tuple[Provider, ...]:
    """Restituisce solo i provider ufficialmente supportati per l'host."""

    if host is Host.MACOS_ARM64:
        return (Provider.VMWARE, Provider.VIRTUALBOX, Provider.DOCKER)
    if host is Host.WINDOWS_AMD64:
        return (Provider.VIRTUALBOX, Provider.DOCKER)
    raise ValueError(f"Host non supportato: {host}")


def install_plan(host: Host, provider: Provider) -> InstallPlan:
    """Costruisce il piano deterministico per host e provider."""

    if provider not in supported_providers(host):
        raise ValueError(f"{provider.value} non è supportato su {host.value}")

    if provider is Provider.DOCKER:
        return _docker_plan(host)
    if host is Host.MACOS_ARM64:
        return _macos_plan(provider)
    return _windows_plan()


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
            Check("git", "Git", ("git", "--version")),
            Check("vagrant", "Vagrant", ("vagrant", "--version")),
            Check("virtualbox", "VirtualBox", ("VBoxManage.exe", "--version")),
        ),
        (
            Step(
                "git",
                "Installa Git",
                ("winget", "install", "--id", "Git.Git", "--exact"),
            ),
            Step(
                "vagrant",
                "Installa Vagrant",
                ("winget", "install", "--id", "Hashicorp.Vagrant", "--exact"),
            ),
            Step(
                "virtualbox",
                "Installa VirtualBox",
                ("winget", "install", "--id", "Oracle.VirtualBox", "--exact"),
            ),
        ),
    )


def _docker_plan(host: Host) -> InstallPlan:
    image = immutable_reference()
    common_checks = (
        Check("docker", "Docker Desktop", ("docker", "--version")),
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
            *common_checks,
        ),
        (
            Step(
                "docker",
                "Installa Docker Desktop",
                (
                    "winget",
                    "install",
                    "--id",
                    "Docker.DockerDesktop",
                    "--exact",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ),
            ),
            Step(
                "docker-engine",
                "Avvia Docker Desktop",
                None,
                manual=True,
                detail=(
                    "Avvia Docker Desktop, completa la configurazione WSL 2 e "
                    "riavvia Windows se richiesto; poi rilancia l'installer."
                ),
                deferred=True,
            ),
            Step("student-image", "Scarica student-dev", ("docker", "pull", image)),
        ),
    )
