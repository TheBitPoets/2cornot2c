"""Rilevamento prudente delle risorse usato soltanto per la raccomandazione."""

from __future__ import annotations

import ctypes
import subprocess

from installer.model import Host, Provider


LOW_MEMORY_LIMIT_BYTES = 8 * 1024**3


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def total_memory_bytes(host: Host) -> int | None:
    """Restituisce la RAM fisica o None senza impedire l'installazione."""

    try:
        if host is Host.MACOS_ARM64:
            result = subprocess.run(
                ("sysctl", "-n", "hw.memsize"),
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return int(result.stdout.strip())
        status = _MemoryStatusEx()
        status.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
    except (AttributeError, OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def order_by_recommendation(
    providers: tuple[Provider, ...],
    memory_bytes: int | None,
) -> tuple[Provider, ...]:
    """Mette Docker per primo soltanto su host con non più di 8 GiB."""

    if (
        memory_bytes is not None
        and memory_bytes <= LOW_MEMORY_LIMIT_BYTES
        and Provider.DOCKER in providers
    ):
        return (Provider.DOCKER,) + tuple(
            provider for provider in providers if provider is not Provider.DOCKER
        )
    return providers
