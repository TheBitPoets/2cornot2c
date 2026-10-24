"""Avvio sicuro delle operazioni Windows che devono sopravvivere alla TUI."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess

from installer.environments import installed_project
from installer.model import Provider


WINDOWS_ACTION_SCRIPTS = {
    "launch": "launch-classroom-windows.ps1",
    "update": "update-classroom-windows.ps1",
    "uninstall": "uninstall-classroom-windows.ps1",
    "select-uninstall": "uninstall-classroom-windows.ps1",
    "reset": "uninstall-classroom-windows.ps1",
}


def launcher_directory() -> Path:
    """Restituisce la cartella persistente preparata dal bootstrap Windows."""

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA non è disponibile")
    return Path(local_app_data) / "2cornot2c"


def powershell_action_command(action: str, *, provider: Provider | None = None) -> tuple[str, ...]:
    """Costruisce il comando senza shell per uno script verificato."""

    try:
        script_name = WINDOWS_ACTION_SCRIPTS[action]
    except KeyError as error:
        raise ValueError(f"Operazione non supportata: {action}") from error
    if provider is not None and (
        action != "launch" or provider not in {Provider.DOCKER, Provider.VIRTUALBOX}
    ):
        raise ValueError("Provider non supportato per questa operazione")
    # Il launcher persistente può appartenere a una versione precedente alla scelta.
    script = (
        installed_project() / "scripts" / script_name
        if provider is not None
        else launcher_directory() / script_name
    )
    if not script.is_file():
        raise RuntimeError(f"Script di gestione non trovato: {script}")
    command = (
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
    )
    if action in {"uninstall", "reset"}:
        command += ("-ConfirmedFromTui",)
    if action == "reset":
        command += ("-DestroyClassroomVm",)
    if action == "select-uninstall":
        command += ("-SelectComponents",)
    if provider is not None:
        command += ("-Provider", provider.value)
    return command


def launch_windows_action(action: str, *, provider: Provider | None = None) -> None:
    """Apre una nuova console, lasciando che la TUI possa terminare."""

    creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(  # noqa: S603 - comando costruito da valori interni
        powershell_action_command(action, provider=provider),
        creationflags=creation_flags,
        close_fds=True,
    )
