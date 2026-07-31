"""Migrazione esplicita e conservativa di una VM Vagrant preesistente."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
import csv
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess

from installer.model import Provider, VM_PROVIDERS


CONFIRMATION = "RICREA VM"
ABSENT_STATES = {"not_created", "not created", ""}
RUNNING_STATES = {"running"}


@dataclass(frozen=True, slots=True)
class MachineState:
    """Stato provider-specifico della VM locale."""

    provider: Provider
    state: str

    @property
    def exists(self) -> bool:
        return self.state not in ABSENT_STATES

    @property
    def running(self) -> bool:
        return self.state in RUNNING_STATES


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Esito della migrazione distruttiva esplicitamente confermata."""

    status: str
    detail: str


Runner = Callable[
    [tuple[str, ...], Path, Mapping[str, str] | None],
    tuple[int, str],
]


def subprocess_runner(
    command: tuple[str, ...],
    cwd: Path,
    environment: Mapping[str, str] | None = None,
) -> tuple[int, str]:
    """Esegue un comando Vagrant senza shell."""

    merged_environment = os.environ.copy()
    if environment:
        merged_environment.update(environment)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=merged_environment,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return 127, f"Comando non trovato: {command[0]}"
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    return completed.returncode, output[-8000:]


def state_directory(provider: Provider) -> str:
    """Mantiene isolati gli stati Vagrant dei due provider."""

    if provider not in VM_PROVIDERS:
        raise ValueError(f"Provider non VM: {provider.value}")
    return ".vagrant-vmware" if provider is Provider.VMWARE else ".vagrant"


def legacy_environment(provider: Provider) -> dict[str, str]:
    """Abilita Bento soltanto per ispezionare/rimuovere la VM da migrare."""

    return {
        "VAGRANT_DOTFILE_PATH": state_directory(provider),
        "CLASSROOM_ALLOW_LEGACY_PROVISIONING": "1",
    }


def parse_machine_state(machine_output: str, provider: Provider) -> MachineState:
    """Legge lo stato della macchina `default` dall'output machine-readable."""

    state = ""
    for row in csv.reader(machine_output.splitlines()):
        if len(row) >= 4 and row[1] == "default" and row[2] == "state":
            state = row[3].strip().lower()
    return MachineState(provider, state)


def inspect_machine(
    project: Path,
    provider: Provider,
    *,
    runner: Runner = subprocess_runner,
) -> MachineState:
    """Ispeziona una sola VM senza modificarla."""

    environment = legacy_environment(provider)
    returncode, output = runner(
        ("vagrant", "status", "--machine-readable"),
        project,
        environment,
    )
    if returncode != 0:
        raise RuntimeError(output or "Impossibile leggere lo stato Vagrant.")
    return parse_machine_state(output, provider)


def validate_shared_folders(project: Path) -> tuple[Path, Path]:
    """Verifica che i dati persistenti siano directory interne al progetto."""

    project = project.resolve(strict=True)
    folders = tuple(project / name for name in ("lab", "lab2"))
    for folder in folders:
        if not folder.is_dir():
            raise RuntimeError(f"Cartella condivisa mancante: {folder}")
        try:
            folder.resolve(strict=True).relative_to(project)
        except ValueError as error:
            raise RuntimeError(
                f"Cartella condivisa fuori dal progetto: {folder}"
            ) from error
    return folders


def project_selection_markers(project: Path) -> tuple[Path, Path]:
    """Restituisce i marker validati della selezione box del progetto."""

    project = project.resolve(strict=True)
    markers = tuple(
        project / name for name in (".classroom-box", ".classroom-provider")
    )
    for marker in markers:
        if marker.is_dir() and not marker.is_symlink():
            raise RuntimeError(f"Marker classroom non valido: {marker}")
    return markers


def project_selection_exists(project: Path) -> bool:
    """Indica se esiste una selezione box, senza modificarla."""

    return any(
        marker.exists() or marker.is_symlink()
        for marker in project_selection_markers(project)
    )


def clear_project_selection(project: Path) -> bool:
    """Rimuove in modo idempotente la selezione della box ormai migrata."""

    markers = project_selection_markers(project)
    removed = any(marker.exists() or marker.is_symlink() for marker in markers)
    for marker in markers:
        marker.unlink(missing_ok=True)
    return removed


def recreate_machine(
    project: Path,
    machine: MachineState,
    confirmation: str,
    *,
    runner: Runner = subprocess_runner,
) -> MigrationResult:
    """Arresta e distrugge soltanto la VM confermata, mai i dati condivisi."""

    if not machine.exists:
        if not project_selection_exists(project):
            return MigrationResult("skipped", "nessuna VM preesistente")
        if confirmation != CONFIRMATION:
            return MigrationResult(
                "blocked",
                f"Conferma non valida: digitare esattamente {CONFIRMATION}",
            )
        clear_project_selection(project)
        return MigrationResult(
            "succeeded",
            "nessuna VM preesistente; selezione box precedente rimossa",
        )
    if confirmation != CONFIRMATION:
        return MigrationResult(
            "blocked",
            f"Conferma non valida: digitare esattamente {CONFIRMATION}",
        )
    validate_shared_folders(project)
    environment = legacy_environment(machine.provider)

    if machine.running:
        returncode, output = runner(("vagrant", "halt"), project, environment)
        if returncode != 0:
            return MigrationResult("failed", output or "Arresto VM non riuscito.")

    returncode, output = runner(
        ("vagrant", "destroy", "--force"),
        project,
        environment,
    )
    if returncode != 0:
        return MigrationResult("failed", output or "Rimozione VM non riuscita.")
    clear_project_selection(project)
    return MigrationResult(
        "succeeded",
        "VM precedente rimossa; lab e lab2 sono rimaste sull'host",
    )


def parser() -> argparse.ArgumentParser:
    """Crea la CLI esplicita di migrazione."""

    result = argparse.ArgumentParser(
        description="Prepara la sostituzione controllata di una VM 2cornot2c."
    )
    result.add_argument(
        "--provider",
        required=True,
        choices=[provider.value for provider in VM_PROVIDERS],
    )
    result.add_argument("--project", type=Path, default=Path.cwd())
    return result


def main(argv: list[str] | None = None) -> int:
    """Mostra stato e richiede una conferma non abbreviabile."""

    args = parser().parse_args(argv)
    provider = Provider(args.provider)
    try:
        machine = inspect_machine(args.project, provider)
        validate_shared_folders(args.project)
        selection_exists = project_selection_exists(args.project)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Migrazione non disponibile: {error}")
        return 1
    if not machine.exists and not selection_exists:
        result = recreate_machine(args.project, machine, "")
        print(f"[{result.status.upper()}] {result.detail}")
        return 0

    if machine.exists:
        print(f"VM trovata: provider={provider.value}, stato={machine.state}")
        print("Saranno conservate soltanto le cartelle host lab e lab2.")
        print("I file salvati esclusivamente dentro la VM andranno persi.")
    else:
        print("Nessuna VM trovata, ma esiste una selezione box configurata.")
        print("Saranno rimossi i marker .classroom-box e .classroom-provider.")
    confirmation = input(f"Digita esattamente {CONFIRMATION}: ")
    result = recreate_machine(args.project, machine, confirmation)
    print(f"[{result.status.upper()}] {result.detail}")
    return 0 if result.status in {"succeeded", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
