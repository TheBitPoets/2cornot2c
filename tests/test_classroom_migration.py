from __future__ import annotations

from pathlib import Path

import pytest

from installer.migration import (
    CONFIRMATION,
    MachineState,
    parse_machine_state,
    recreate_machine,
    validate_shared_folders,
)
from installer.model import Provider


def project_with_labs(tmp_path: Path) -> Path:
    (tmp_path / "lab").mkdir()
    (tmp_path / "lab2").mkdir()
    return tmp_path


def test_parse_provider_specific_machine_state() -> None:
    output = "\n".join(
        [
            "1,default,metadata,provider,vmware_desktop",
            "1,default,state,not_running",
        ]
    )

    machine = parse_machine_state(output, Provider.VMWARE)

    assert machine.exists is True
    assert machine.running is False


def test_recreate_requires_exact_confirmation_before_commands(tmp_path: Path) -> None:
    calls = []
    machine = MachineState(Provider.VIRTUALBOX, "poweroff")

    result = recreate_machine(
        project_with_labs(tmp_path),
        machine,
        "ricrea vm",
        runner=lambda command, cwd, environment: (
            calls.append((command, environment)) or (0, "")
        ),
    )

    assert result.status == "blocked"
    assert calls == []


def test_running_machine_is_halted_then_destroyed(tmp_path: Path) -> None:
    calls = []
    machine = MachineState(Provider.VMWARE, "running")

    result = recreate_machine(
        project_with_labs(tmp_path),
        machine,
        CONFIRMATION,
        runner=lambda command, cwd, environment: (
            calls.append((command, environment)) or (0, "")
        ),
    )

    assert result.status == "succeeded"
    assert [call[0] for call in calls] == [
        ("vagrant", "halt"),
        ("vagrant", "destroy", "--force"),
    ]
    assert all(
        call[1] == {"VAGRANT_DOTFILE_PATH": ".vagrant-vmware"}
        for call in calls
    )
    assert (tmp_path / "lab").is_dir()
    assert (tmp_path / "lab2").is_dir()


def test_destroy_failure_is_reported(tmp_path: Path) -> None:
    result = recreate_machine(
        project_with_labs(tmp_path),
        MachineState(Provider.VIRTUALBOX, "poweroff"),
        CONFIRMATION,
        runner=lambda command, cwd, environment: (3, "destroy failed"),
    )

    assert result.status == "failed"
    assert result.detail == "destroy failed"


def test_shared_folder_symlink_outside_project_is_rejected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "lab").symlink_to(outside, target_is_directory=True)
    (project / "lab2").mkdir()

    with pytest.raises(RuntimeError, match="fuori dal progetto"):
        validate_shared_folders(project)
