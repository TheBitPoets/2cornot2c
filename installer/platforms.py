"""Rilevamento conservativo dell'host."""

from __future__ import annotations

import platform

from installer.model import Host


def detect_host(system: str | None = None, machine: str | None = None) -> Host:
    """Rileva l'host o fallisce senza proporre combinazioni non collaudate."""

    detected_system = platform.system() if system is None else system
    detected_machine = platform.machine() if machine is None else machine
    normalized_machine = detected_machine.lower()

    if detected_system == "Darwin" and normalized_machine in {"arm64", "aarch64"}:
        return Host.MACOS_ARM64
    if detected_system == "Windows" and normalized_machine in {"amd64", "x86_64"}:
        return Host.WINDOWS_AMD64
    raise RuntimeError(
        f"Host non supportato: sistema={detected_system}, architettura={detected_machine}"
    )
