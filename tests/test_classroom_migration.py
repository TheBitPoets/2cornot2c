from __future__ import annotations

from pathlib import Path

import pytest

from installer import migration
from installer.migration import (
    CONFIRMATION,
    MachineState,
    legacy_environment,
    parse_machine_state,
    recreate_machine,
    state_directory,
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


def test_docker_is_not_a_vagrant_migration_provider() -> None:
    with pytest.raises(ValueError, match="non VM"):
        state_directory(Provider.DOCKER)


def test_migration_explicitly_enables_legacy_vagrantfile_only_for_its_process() -> None:
    assert legacy_environment(Provider.VIRTUALBOX) == {
        "VAGRANT_DOTFILE_PATH": ".vagrant",
        "CLASSROOM_ALLOW_LEGACY_PROVISIONING": "1",
        "CLASSROOM_BOX_NAME": "bento/ubuntu-24.04",
    }


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
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text("2cornot2c/old-box\n", encoding="utf-8")
    (project / ".classroom-provider").write_text(
        "vmware_desktop\n", encoding="utf-8"
    )

    result = recreate_machine(
        project,
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
        call[1]
        == {
            "VAGRANT_DOTFILE_PATH": ".vagrant-vmware",
            "CLASSROOM_ALLOW_LEGACY_PROVISIONING": "1",
            "CLASSROOM_BOX_NAME": "bento/ubuntu-24.04",
        }
        for call in calls
    )
    assert (tmp_path / "lab").is_dir()
    assert (tmp_path / "lab2").is_dir()
    assert not (tmp_path / ".classroom-box").exists()
    assert not (tmp_path / ".classroom-provider").exists()


def test_absent_machine_requires_confirmation_to_clear_selection(
    tmp_path: Path,
) -> None:
    calls = []
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text("2cornot2c/old-box\n", encoding="utf-8")
    (project / ".classroom-provider").write_text(
        "virtualbox\n", encoding="utf-8"
    )

    blocked = recreate_machine(
        project,
        MachineState(Provider.VIRTUALBOX, "not_created"),
        "",
        runner=lambda command, cwd, environment: (
            calls.append((command, environment)) or (0, "")
        ),
    )

    assert blocked.status == "blocked"
    assert calls == []
    assert (project / ".classroom-box").is_file()
    assert (project / ".classroom-provider").is_file()

    confirmed = recreate_machine(
        project,
        MachineState(Provider.VIRTUALBOX, "not_created"),
        CONFIRMATION,
        runner=lambda command, cwd, environment: (
            calls.append((command, environment)) or (0, "")
        ),
    )

    assert confirmed.status == "succeeded"
    assert "selezione box precedente rimossa" in confirmed.detail
    assert calls == []
    assert not (project / ".classroom-box").exists()
    assert not (project / ".classroom-provider").exists()


def test_absent_machine_without_selection_remains_idempotent(tmp_path: Path) -> None:
    result = recreate_machine(
        project_with_labs(tmp_path),
        MachineState(Provider.VIRTUALBOX, "not_created"),
        "",
        runner=lambda command, cwd, environment: pytest.fail(
            "nessun comando Vagrant atteso"
        ),
    )

    assert result.status == "skipped"
    assert result.detail == "nessuna VM preesistente"


def test_migration_does_not_clear_selection_for_another_provider(
    tmp_path: Path,
) -> None:
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text(
        "2cornot2c/vmware-box\n", encoding="utf-8"
    )
    (project / ".classroom-provider").write_text(
        "vmware_desktop\n", encoding="utf-8"
    )

    result = recreate_machine(
        project,
        MachineState(Provider.VIRTUALBOX, "not_created"),
        CONFIRMATION,
        runner=lambda command, cwd, environment: pytest.fail(
            "nessun comando Vagrant atteso"
        ),
    )

    assert result.status == "skipped"
    assert "selezione vmware_desktop conservata" in result.detail
    assert (project / ".classroom-box").is_file()
    assert (project / ".classroom-provider").is_file()


def test_migration_destroys_legacy_other_provider_and_preserves_selection(
    tmp_path: Path,
) -> None:
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text(
        "2cornot2c/vmware-box\n", encoding="utf-8"
    )
    (project / ".classroom-provider").write_text(
        "vmware_desktop\n", encoding="utf-8"
    )
    calls = []

    result = recreate_machine(
        project,
        MachineState(Provider.VIRTUALBOX, "poweroff"),
        CONFIRMATION,
        runner=lambda command, cwd, environment: (
            calls.append((command, environment)) or (0, "destroyed")
        ),
    )

    assert result.status == "succeeded"
    assert calls[0][0] == ("vagrant", "destroy", "--force")
    assert calls[0][1]["VAGRANT_DOTFILE_PATH"] == ".vagrant"
    assert calls[0][1]["CLASSROOM_BOX_NAME"] == "bento/ubuntu-24.04"
    assert "selezione vmware_desktop conservata" in result.detail
    assert (project / ".classroom-box").read_text(encoding="utf-8").strip() == (
        "2cornot2c/vmware-box"
    )
    assert (project / ".classroom-provider").is_file()


def test_partial_selection_without_provider_can_be_confirmed(tmp_path: Path) -> None:
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text(
        "2cornot2c/incomplete-box\n", encoding="utf-8"
    )

    result = recreate_machine(
        project,
        MachineState(Provider.VIRTUALBOX, "not_created"),
        CONFIRMATION,
        runner=lambda command, cwd, environment: pytest.fail(
            "nessun comando Vagrant atteso"
        ),
    )

    assert result.status == "succeeded"
    assert not (project / ".classroom-box").exists()


def test_cli_preserves_other_provider_when_requested_legacy_vm_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text(
        "2cornot2c/vmware-box\n", encoding="utf-8"
    )
    (project / ".classroom-provider").write_text(
        "vmware_desktop\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        migration,
        "inspect_machine",
        lambda selected_project, provider: MachineState(provider, "not_created"),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: pytest.fail("prompt non atteso"),
    )

    exit_code = migration.main(
        ["--provider", "virtualbox", "--project", str(project)]
    )

    assert exit_code == 0
    assert (project / ".classroom-box").is_file()
    assert (project / ".classroom-provider").is_file()


def test_cli_prompts_before_clearing_selection_without_machine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text("2cornot2c/old-box\n", encoding="utf-8")
    (project / ".classroom-provider").write_text(
        "virtualbox\n", encoding="utf-8"
    )
    prompts: list[str] = []
    monkeypatch.setattr(
        migration,
        "inspect_machine",
        lambda selected_project, provider: MachineState(provider, "not_created"),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: prompts.append(prompt) or CONFIRMATION,
    )

    exit_code = migration.main(
        ["--provider", "virtualbox", "--project", str(project)]
    )

    assert exit_code == 0
    assert prompts == [f"Digita esattamente {CONFIRMATION}: "]
    assert not (project / ".classroom-box").exists()
    assert not (project / ".classroom-provider").exists()


def test_destroy_failure_is_reported(tmp_path: Path) -> None:
    project = project_with_labs(tmp_path)
    (project / ".classroom-box").write_text("2cornot2c/old-box\n", encoding="utf-8")
    (project / ".classroom-provider").write_text(
        "virtualbox\n", encoding="utf-8"
    )
    result = recreate_machine(
        project,
        MachineState(Provider.VIRTUALBOX, "poweroff"),
        CONFIRMATION,
        runner=lambda command, cwd, environment: (3, "destroy failed"),
    )

    assert result.status == "failed"
    assert result.detail == "destroy failed"
    assert (project / ".classroom-box").is_file()
    assert (project / ".classroom-provider").is_file()


def test_shared_folder_symlink_outside_project_is_rejected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "lab").symlink_to(outside, target_is_directory=True)
    (project / "lab2").mkdir()

    with pytest.raises(RuntimeError, match="fuori dal progetto"):
        validate_shared_folders(project)
