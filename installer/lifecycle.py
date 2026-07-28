"""Avvio sicuro delle operazioni Windows che devono sopravvivere alla TUI."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess


WINDOWS_ACTION_SCRIPTS = {
    "update": "update-classroom-windows.ps1",
    "uninstall": "uninstall-classroom-windows.ps1",
}


def launcher_directory() -> Path:
    """Restituisce la cartella persistente preparata dal bootstrap Windows."""

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA non è disponibile")
    return Path(local_app_data) / "2cornot2c"


def powershell_action_command(action: str) -> tuple[str, ...]:
    """Costruisce il comando senza shell per uno script verificato."""

    try:
        script_name = WINDOWS_ACTION_SCRIPTS[action]
    except KeyError as error:
        raise ValueError(f"Operazione non supportata: {action}") from error
    script = launcher_directory() / script_name
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
    if action == "uninstall":
        command += ("-ConfirmedFromTui",)
    return command


def launch_windows_action(action: str) -> None:
    """Apre una nuova console, lasciando che la TUI possa terminare."""

    creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(  # noqa: S603 - comando costruito da valori interni
        powershell_action_command(action),
        creationflags=creation_flags,
        close_fds=True,
    )
