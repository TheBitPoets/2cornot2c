"""Inventario read-only degli ambienti Windows avviabili dal progetto."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess

from installer.classroom_release_lock import (
    ClassroomReleaseLockError,
    load_target_releases,
)
from installer.diagnostics import _resolve_windows_command
from installer.model import Provider
from installer.student_dev import immutable_reference


PROBE_TIMEOUT_SECONDS = 5


@dataclass(frozen=True, slots=True)
class Environment:
    provider: Provider
    status: str
    detail: str
    launchable: bool = False


def installed_project() -> Path:
    """Usa la stessa cartella del launcher, anche per installazioni personalizzate."""

    state = Path.home() / ".2cornot2c" / "bootstrap-state.json"
    if state.is_file():
        payload = json.loads(state.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("Configurazione dell'installazione non valida.")
        directory = payload.get("install_dir")
        if directory:
            if not isinstance(directory, str) or not Path(directory).is_absolute():
                raise ValueError("Cartella dell'installazione non valida.")
            return Path(directory)
    return Path.home() / "2cornot2c"


def _probe(*command: str) -> int | None:
    try:
        return subprocess.run(
            _resolve_windows_command(tuple(command)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
        ).returncode
    except (OSError, subprocess.TimeoutExpired):
        return None


def _virtualbox(project: Path) -> Environment:
    provider = Provider.VIRTUALBOX
    repair = "Scegli Installa, completa o ripara dal menu principale."
    identity = project / ".vagrant/machines/default/virtualbox/id"
    if not identity.is_file():
        return Environment(provider, "Non installata", repair)
    try:
        vm_id = identity.read_text(encoding="utf-8-sig").strip()
        if not vm_id:
            return Environment(provider, "Incompleta", repair)
        # Vagrantfile legge sempre il lock, anche con marker Packer presenti.
        target = load_target_releases(
            project / "packer/classroom-releases.lock.json"
        )["windows-amd64-virtualbox"]
        box = project / ".classroom-box"
        selection = project / ".classroom-provider"
        if box.is_file() and not re.fullmatch(
            r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+",
            box.read_text(encoding="utf-8-sig").strip(),
        ):
            return Environment(provider, "Da riparare", repair)
        if box.is_file() and selection.is_file():
            configured = (
                selection.read_text(encoding="utf-8-sig").strip() == provider.value
            )
        else:
            configured = not target.active and bool(target.candidate_version)
        if not configured:
            return Environment(provider, "Da riparare", repair)
    except (OSError, UnicodeError, ClassroomReleaseLockError):
        return Environment(provider, "Da verificare", repair)
    if _probe("vagrant", "--version") != 0:
        return Environment(provider, "Da riparare", "Vagrant non disponibile. " + repair)
    result = _probe("VBoxManage.exe", "showvminfo", vm_id, "--machinereadable")
    if result != 0:
        return Environment(provider, "Da verificare", "VM non verificabile in VirtualBox. " + repair)
    return Environment(provider, "Installata", "Avvia la VM completa in una nuova finestra.", True)


def _docker(project: Path) -> Environment:
    provider = Provider.DOCKER
    if _probe("docker", "--version") != 0:
        return Environment(provider, "Non disponibile", "Installa o ripara Docker dal menu principale.")
    if _probe("docker", "info") != 0:
        return Environment(
            provider, "Da verificare",
            "Apri Docker Desktop, attendi che sia pronto e premi r. Immagine non ancora verificabile.",
        )
    try:
        image = immutable_reference(project / "docker/student-dev/toolchain.lock.json")
    except ValueError:
        return Environment(provider, "Da riparare", "Configurazione immagine non valida. Aggiorna l'ambiente.")
    result = _probe("docker", "image", "inspect", image)
    if result is None:
        return Environment(provider, "Da verificare", "Controllo immagine non riuscito. Premi r per riprovare.")
    if result != 0:
        return Environment(provider, "Da completare", "Immagine didattica assente. Installa, completa o ripara Docker.")
    return Environment(provider, "Installato", "Apri la shell Docker in una nuova finestra.", True)


def detect_windows_environments(project: Path | None = None) -> tuple[Environment, ...]:
    """Rileva entrambi i provider, senza usare l'ultima scelta come inventario."""

    project = installed_project() if project is None else project
    return (_virtualbox(project), _docker(project))
