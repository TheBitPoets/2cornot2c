from pathlib import Path

import pytest

from scripts import build_student_dev, student_dev_shell


def test_image_reference_is_immutable() -> None:
    manifest = build_student_dev.load_manifest()
    reference = student_dev_shell.image_reference()

    assert reference.startswith(f"{manifest['image_repository']}@sha256:")
    assert ":latest" not in reference


def test_docker_command_is_lightweight_non_root_image(tmp_path: Path) -> None:
    command = student_dev_shell.docker_command(
        workspace=tmp_path,
        interactive=False,
    )

    assert command[:3] == ["docker", "run", "--rm"]
    assert "-it" not in command
    assert "--read-only" in command
    assert ["--memory", "512m"] == command[
        command.index("--memory") : command.index("--memory") + 2
    ]
    assert any(
        item == f"type=bind,source={tmp_path.resolve()},target=/workspace"
        for item in command
    )
    assert command[-2:] == [student_dev_shell.image_reference(), "/bin/bash"]


def test_docker_command_rejects_file_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "main.c"
    workspace.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="directory"):
        student_dev_shell.docker_command(workspace=workspace)
