"""Avvia una shell didattica leggera dalla toolchain bloccata del grading."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess

from scripts import toolchain_lock


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docker" / "assignment-runner" / "toolchain.lock.json"


def docker_command(
    *,
    workspace: Path,
    lock_path: Path = DEFAULT_LOCK,
    memory: str = "512m",
    interactive: bool = True,
) -> list[str]:
    """Costruisce il comando senza shell usando l'immagine immutabile del grading."""

    resolved_workspace = workspace.expanduser().resolve(strict=True)
    if not resolved_workspace.is_dir():
        raise ValueError("Il workspace Docker deve essere una directory.")
    lock = toolchain_lock.load_lock(lock_path)

    command = ["docker", "run", "--rm"]
    if interactive:
        command.append("-it")
    command.extend(
        [
            "--platform",
            lock["platform"],
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--memory",
            memory,
            "--cpus",
            "1",
            "--pids-limit",
            "256",
            "--user",
            "runner",
            "--mount",
            f"type=bind,source={resolved_workspace},target=/workspace",
            "--workdir",
            "/workspace",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--entrypoint",
            "/bin/sh",
            toolchain_lock.immutable_reference(lock),
        ]
    )
    return command


def parser() -> argparse.ArgumentParser:
    """Crea il parser della shell Docker studente."""

    result = argparse.ArgumentParser(
        description="Shell C/Python/Node/SQLite con la toolchain esatta del grading."
    )
    result.add_argument("--workspace", type=Path, default=Path.cwd())
    result.add_argument("--memory", default="512m")
    result.add_argument("--print-command", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    """Stampa oppure esegue la shell interattiva."""

    args = parser().parse_args(argv)
    try:
        command = docker_command(workspace=args.workspace, memory=args.memory)
    except (OSError, ValueError, toolchain_lock.ToolchainLockError) as error:
        print(f"Ambiente Docker non disponibile: {error}")
        return 1
    if args.print_command:
        print(shlex.join(command))
        return 0
    try:
        return subprocess.run(command, check=False).returncode
    except FileNotFoundError:
        print("Docker non è installato o non è disponibile nel PATH.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
