"""Modello indipendente dalla UI per diagnosi e installazione dell'ambiente."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Host(str, Enum):
    """Host supportati dall'installer."""

    MACOS_ARM64 = "macos-arm64"
    WINDOWS_AMD64 = "windows-amd64"


class Provider(str, Enum):
    """Ambienti selezionabili dall'installer."""

    VMWARE = "vmware_desktop"
    VIRTUALBOX = "virtualbox"
    DOCKER = "docker"


VM_PROVIDERS = (Provider.VMWARE, Provider.VIRTUALBOX)


@dataclass(frozen=True, slots=True)
class Check:
    """Un controllo diagnostico senza effetti collaterali."""

    key: str
    label: str
    command: tuple[str, ...]
    expected_text: str = ""
    minimum_version: str = ""


@dataclass(frozen=True, slots=True)
class Step:
    """Un passo di installazione idempotente."""

    key: str
    label: str
    command: tuple[str, ...] | None
    manual: bool = False
    detail: str = ""
    deferred: bool = False
    restart_after_success: bool = False


@dataclass(frozen=True, slots=True)
class InstallPlan:
    """Piano completo per una combinazione host/provider."""

    host: Host
    provider: Provider
    checks: tuple[Check, ...]
    steps: tuple[Step, ...]
