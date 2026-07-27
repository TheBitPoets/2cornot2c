from __future__ import annotations

import json
from pathlib import Path

from scripts.student_docker_shell import docker_command


REFERENCE = (
    "ghcr.io/thebitpoets/2cornot2c-assignment-runner"
    "@sha256:62f0f7b7bc1d48d01b7f8e5fa765e0b43be3622e70a614033b1bb4a4e522e159"
)


def write_lock(path: Path) -> Path:
    lock = path / "toolchain.lock.json"
    lock.write_text(
        json.dumps(
            {
                "schema_version": "thebitlab.grading-toolchain-lock.v1",
                "version": "2026.07.1",
                "platform": "linux/amd64",
                "image_repository": "ghcr.io/thebitpoets/2cornot2c-assignment-runner",
                "source_revision": "bd102146a684a9b06835204ec1b7f668f7655a03",
                "immutable_reference": REFERENCE,
            }
        ),
        encoding="utf-8",
    )
    return lock


def test_shell_reuses_locked_grading_image(tmp_path: Path) -> None:
    workspace = tmp_path / "lab"
    workspace.mkdir()

    command = docker_command(
        workspace=workspace,
        lock_path=write_lock(tmp_path),
        interactive=False,
    )

    assert command[:3] == ["docker", "run", "--rm"]
    assert "--network" in command
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "--cap-drop" in command
    assert "--user" in command
    assert command[command.index("--user") + 1] == "runner"
    assert command[-1] == REFERENCE


def test_shell_has_small_default_memory_limit(tmp_path: Path) -> None:
    workspace = tmp_path / "lab"
    workspace.mkdir()

    command = docker_command(
        workspace=workspace,
        lock_path=write_lock(tmp_path),
        interactive=False,
    )

    assert command[command.index("--memory") + 1] == "512m"
