"""Piani supportati dall'installer, separati dalla presentazione uTUI."""

from __future__ import annotations

from installer.model import Check, Host, InstallPlan, Provider, Step


def supported_providers(host: Host) -> tuple[Provider, ...]:
    """Restituisce solo i provider ufficialmente supportati per l'host."""

    if host is Host.MACOS_ARM64:
        return (Provider.VMWARE, Provider.VIRTUALBOX)
    if host is Host.WINDOWS_AMD64:
        return (Provider.VIRTUALBOX,)
    raise ValueError(f"Host non supportato: {host}")


def install_plan(host: Host, provider: Provider) -> InstallPlan:
    """Costruisce il piano deterministico per host e provider."""

    if provider not in supported_providers(host):
        raise ValueError(f"{provider.value} non è supportato su {host.value}")

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
