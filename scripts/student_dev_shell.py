"""Avvia la shell Ubuntu leggera e multiarch per lo sviluppo degli studenti."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess

try:
    from scripts import build_student_dev
except ModuleNotFoundError:  # Esecuzione diretta: python scripts/student_dev_shell.py
    import build_student_dev


def image_reference() -> str:
    """Restituisce il tag versionato dichiarato nel manifest controllato."""

    manifest = build_student_dev.load_manifest()
    return f"{manifest['image_repository']}:{manifest['version']}"


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
    except (OSError, ValueError, build_student_dev.StudentDevBuildError) as error:
        print(f"Ambiente student-dev non disponibile: {error}")
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
