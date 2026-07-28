"""Avvia la shell Ubuntu leggera e multiarch per lo sviluppo degli studenti."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess

try:
    from installer import student_dev
except ModuleNotFoundError:  # Esecuzione diretta: python scripts/student_dev_shell.py
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from installer import student_dev

from installer.student_errors import ERRORS, print_error


def image_reference() -> str:
    """Restituisce il riferimento GHCR immutabile verificato."""

    return student_dev.immutable_reference()


def docker_command(
    *,
    workspace: Path,
    memory: str = "512m",
    interactive: bool = True,
) -> list[str]:
    """Costruisce il comando isolato mantenendo scrivibile solo il workspace."""

    resolved_workspace = workspace.expanduser().resolve(strict=True)
    if not resolved_workspace.is_dir():
        raise ValueError("Il workspace student-dev deve essere una directory.")
    command = ["docker", "run", "--rm"]
    if interactive:
        command.append("-it")
    command.extend(
        [
            "--init",
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
            "--mount",
            f"type=bind,source={resolved_workspace},target=/workspace",
            "--workdir",
            "/workspace",
            "--tmpfs",
            "/tmp:rw,nosuid,size=64m",
            "--tmpfs",
            "/home/student:rw,nosuid,size=32m,uid=1000,gid=1000",
            image_reference(),
            "/bin/bash",
        ]
    )
    return command


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Shell Ubuntu student-dev per PC con poca RAM."
    )
    result.add_argument("--workspace", type=Path, default=Path.cwd())
    result.add_argument("--memory", default="512m")
    result.add_argument("--print-command", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        command = docker_command(workspace=args.workspace, memory=args.memory)
    except (OSError, ValueError, student_dev.StudentDevLockError) as error:
        print_error(ERRORS["student-security"], str(error))
        return 1
    if args.print_command:
        print(shlex.join(command))
        return 0
    try:
        returncode = subprocess.run(command, check=False).returncode
    except FileNotFoundError:
        print_error(ERRORS["docker-command"])
        return 1
    if returncode != 0:
        print_error(ERRORS["container"], f"docker exit code {returncode}")
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
