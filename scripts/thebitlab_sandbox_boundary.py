from __future__ import annotations

from pathlib import Path


def docker_boundary_command(
    *,
    image: str,
    workspace: Path,
    cidfile: Path | None = None,
    container_name: str | None = None,
    platform: str | None = None,
) -> list[str]:
    """Return the single hardened Docker boundary shared by all runners."""

    command = [
        "docker",
        "run",
        "-i",
        "--rm",
        "--network",
        "none",
        "--user",
        "runner",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "128",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "-v",
        f"{workspace.resolve()}:/submission:ro",
        "--tmpfs",
        "/thebitlab-work:rw,exec,nosuid,nodev,mode=1777,size=64m",
        "-e",
        "TMPDIR=/thebitlab-work",
        "-w",
        "/submission",
    ]
    if platform is not None:
        command.extend(["--platform", platform])
    if cidfile is not None:
        command.extend(["--cidfile", str(cidfile.resolve())])
    if container_name is not None:
        command.extend(["--name", container_name])
    command.append(image)
    return command
