"""Importazione idempotente della box e configurazione locale del progetto."""

from __future__ import annotations

from collections.abc import Callable
import csv
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile

from installer.artifacts import BoxArtifact, verify_box
from installer.model import Host, Provider, VM_PROVIDERS


@dataclass(frozen=True, slots=True)
class VagrantResult:
    """Esito di importazione o primo avvio."""

    status: str
    detail: str


Runner = Callable[[tuple[str, ...], Path | None], tuple[int, str]]


def subprocess_runner(
    command: tuple[str, ...], cwd: Path | None = None
) -> tuple[int, str]:
    """Esegue Vagrant senza shell conservando un output diagnostico limitato."""

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return 127, f"Comando non trovato: {command[0]}"
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    return completed.returncode, output[-8000:]


def parse_installed_boxes(machine_output: str) -> set[tuple[str, str]]:
    """Estrae coppie nome/provider dall'output machine-readable di Vagrant."""

    installed: set[tuple[str, str]] = set()
    current_name = ""
    for row in csv.reader(machine_output.splitlines()):
        if len(row) < 4:
            continue
        event, data = row[2], row[3]
        if event == "box-name":
            current_name = data
        elif event == "box-provider" and current_name:
            installed.add((current_name, data))
            current_name = ""
    return installed


def import_box(
    artifact: BoxArtifact,
    box_path: Path,
    *,
    runner: Runner = subprocess_runner,
) -> VagrantResult:
    """Verifica e reimporta la box, sostituendo la stessa identità locale."""

    box_path = box_path.resolve(strict=True)
    verify_box(box_path, artifact)
    with tempfile.TemporaryDirectory(prefix="2cornot2c-vagrant-box-") as directory:
        isolated_cwd = Path(directory)
        returncode, output = runner(
            (
                "vagrant",
                "box",
                "add",
                artifact.box_name,
                str(box_path),
                "--provider",
                artifact.provider.value,
                "--force",
            ),
            isolated_cwd,
        )
    if returncode != 0:
        return VagrantResult("failed", output or "Reimportazione box non riuscita.")
    return VagrantResult("succeeded", "box verificata e reimportata")


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        Path(temporary_name).replace(path)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


def configure_project(project: Path, artifact: BoxArtifact) -> None:
    """Attiva atomicamente box e provider per i successivi comandi Vagrant."""

    project = project.resolve(strict=True)
    if not (project / "Vagrantfile").is_file():
        raise ValueError(f"Vagrantfile non trovato in {project}")
    _atomic_text(project / ".classroom-box", f"{artifact.box_name}\n")
    _atomic_text(project / ".classroom-provider", f"{artifact.provider.value}\n")


def launch_command(project: Path, host: Host, provider: Provider) -> tuple[str, ...]:
    """Restituisce il comando supportato per il primo avvio e health check."""

    if provider not in VM_PROVIDERS:
        raise ValueError(f"Provider non VM: {provider.value}")
    if host is Host.MACOS_ARM64 and provider is Provider.VMWARE:
        return ("bash", str(project / "scripts" / "setup-vm.sh"), "--vmware")
    if host is Host.WINDOWS_AMD64 and provider is Provider.VIRTUALBOX:
        return (
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(project / "scripts" / "setup-vm.ps1"),
        )
    raise ValueError(f"Avvio non supportato: {host.value}/{provider.value}")


def launch_classroom(
    project: Path,
    host: Host,
    provider: Provider,
    *,
    runner: Runner = subprocess_runner,
) -> VagrantResult:
    """Avvia la VM tramite lo script provider-specifico già dotato di health check."""

    returncode, output = runner(launch_command(project, host, provider), project)
    if returncode != 0:
        return VagrantResult("failed", output or "Primo avvio non riuscito.")
    return VagrantResult("succeeded", "VM avviata e verificata")
