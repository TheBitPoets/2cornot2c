"""Preflight read-only delle risorse prima di installare VM o Docker."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from installer.model import Host, Provider
from installer.platforms import detect_host
from installer.resources import total_memory_bytes


GIB = 1024**3
MINIMUM_DISK = {
    Provider.DOCKER: 8 * GIB,
    Provider.VIRTUALBOX: 20 * GIB,
    Provider.VMWARE: 20 * GIB,
}
MINIMUM_MEMORY = {
    Provider.DOCKER: 4 * GIB,
    Provider.VIRTUALBOX: 8 * GIB,
    Provider.VMWARE: 8 * GIB,
}


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    """Risorse misurate senza modificare il sistema."""

    total_memory: int | None
    free_disk: int
    virtualization: bool | None


@dataclass(frozen=True, slots=True)
class ResourceResult:
    """Esito semplice consumabile sia dalla CLI sia da uTUI."""

    key: str
    status: str
    detail: str


def virtualization_available(host: Host) -> bool | None:
    """Controlla la virtualizzazione; None indica che non è misurabile."""

    if host is Host.MACOS_ARM64:
        return True
    try:
        completed = subprocess.run(
            (
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "(Get-CimInstance Win32_Processor | "
                "Select-Object -First 1 -ExpandProperty "
                "VirtualizationFirmwareEnabled)",
            ),
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    value = completed.stdout.strip().lower()
    if completed.returncode != 0 or value not in {"true", "false"}:
        return None
    return value == "true"


def snapshot(host: Host, target: Path) -> ResourceSnapshot:
    """Misura RAM, disco della destinazione e virtualizzazione."""

    existing_target = target.expanduser()
    while not existing_target.exists() and existing_target != existing_target.parent:
        existing_target = existing_target.parent
    free_disk = shutil.disk_usage(existing_target).free
    return ResourceSnapshot(
        total_memory_bytes(host),
        free_disk,
        virtualization_available(host),
    )


def evaluate(
    host: Host,
    provider: Provider,
    measured: ResourceSnapshot,
) -> tuple[ResourceResult, ...]:
    """Applica soglie conservative e non nasconde misure sconosciute."""

    results: list[ResourceResult] = []
    minimum_memory = MINIMUM_MEMORY[provider]
    if measured.total_memory is None:
        results.append(
            ResourceResult("memory", "warning", "RAM non misurabile automaticamente")
        )
    elif measured.total_memory < minimum_memory:
        results.append(
            ResourceResult(
                "memory",
                "blocked",
                f"RAM {measured.total_memory / GIB:.1f} GiB; "
                f"servono almeno {minimum_memory / GIB:.0f} GiB",
            )
        )
    else:
        results.append(
            ResourceResult(
                "memory",
                "ok",
                f"RAM {measured.total_memory / GIB:.1f} GiB",
            )
        )

    minimum_disk = MINIMUM_DISK[provider]
    if measured.free_disk < minimum_disk:
        results.append(
            ResourceResult(
                "disk",
                "blocked",
                f"disco libero {measured.free_disk / GIB:.1f} GiB; "
                f"servono almeno {minimum_disk / GIB:.0f} GiB",
            )
        )
    else:
        results.append(
            ResourceResult(
                "disk",
                "ok",
                f"disco libero {measured.free_disk / GIB:.1f} GiB",
            )
        )

    if measured.virtualization is False:
        results.append(
            ResourceResult(
                "virtualization",
                "blocked",
                "virtualizzazione hardware disabilitata nel firmware",
            )
        )
    elif measured.virtualization is None:
        results.append(
            ResourceResult(
                "virtualization",
                "warning",
                "virtualizzazione non verificabile automaticamente",
            )
        )
    else:
        results.append(
            ResourceResult("virtualization", "ok", "virtualizzazione disponibile")
        )
    return tuple(results)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Controlla le risorse 2cornot2c")
    result.add_argument(
        "--provider",
        required=True,
        choices=[provider.value for provider in Provider],
    )
    result.add_argument("--target", type=Path, default=Path.cwd())
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    host = detect_host()
    provider = Provider(args.provider)
    results = evaluate(host, provider, snapshot(host, args.target))
    print(
        "; ".join(
            f"{result.status.upper()} {result.detail}" for result in results
        )
    )
    return 1 if any(result.status == "blocked" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
