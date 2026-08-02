from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from installer.artifacts import BoxArtifact
from installer.model import Host, Provider
from installer.vagrant_box import (
    configure_project,
    import_box,
    launch_command,
    parse_installed_boxes,
)


CONTENT = b"classroom box"


def artifact() -> BoxArtifact:
    return BoxArtifact(
        "VMware ARM64",
        Host.MACOS_ARM64,
        Provider.VMWARE,
        "arm64",
        "2cornot2c/ubuntu-vmware-0.1.0",
        "https://downloads.example.test/classroom.box",
        hashlib.sha256(CONTENT).hexdigest(),
        len(CONTENT),
    )


def test_parse_installed_boxes_pairs_name_and_provider() -> None:
    output = "\n".join(
        [
            "1,,box-name,2cornot2c/ubuntu-vmware-0.1.0",
            "1,,box-provider,vmware_desktop",
            "1,,box-version,0",
        ]
    )

    assert parse_installed_boxes(output) == {
        ("2cornot2c/ubuntu-vmware-0.1.0", "vmware_desktop")
    }


def test_import_force_replaces_exact_installed_identity(tmp_path: Path) -> None:
    box = tmp_path / "classroom.box"
    box.write_bytes(CONTENT)
    calls = []

    result = import_box(
        artifact(),
        box,
        runner=lambda command, cwd: (calls.append(command) or (0, "added")),
    )

    assert result.status == "succeeded"
    assert len(calls) == 1
    assert calls[0][:4] == (
        "vagrant",
        "box",
        "add",
        "2cornot2c/ubuntu-vmware-0.1.0",
    )
    assert "--force" in calls[0]


def test_import_uses_an_isolated_vagrant_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "Vagrantfile").write_text(
        'raise "Box Packer 2cornot2c non configurata"\n',
        encoding="utf-8",
    )
    box = project / "classroom.box"
    box.write_bytes(CONTENT)
    calls: list[tuple[tuple[str, ...], Path]] = []

    def fail_closed_runner(command: tuple[str, ...], cwd: Path | None):
        assert cwd is not None
        assert cwd.is_dir()
        assert not (cwd / "Vagrantfile").exists()
        calls.append((command, cwd))
        return 0, ""

    monkeypatch.chdir(project)
    result = import_box(artifact(), box, runner=fail_closed_runner)

    assert result.status == "succeeded"
    assert [call[0][1:3] for call in calls] == [("box", "add")]
    assert Path(calls[0][0][4]).is_absolute()
    assert "--force" in calls[0][0]


def test_configure_project_writes_local_selection(tmp_path: Path) -> None:
    (tmp_path / "Vagrantfile").write_text("", encoding="utf-8")

    configure_project(tmp_path, artifact())

    assert (tmp_path / ".classroom-box").read_text(encoding="utf-8").strip() == (
        "2cornot2c/ubuntu-vmware-0.1.0"
    )
    assert (tmp_path / ".classroom-provider").read_text(encoding="utf-8").strip() == (
        "vmware_desktop"
    )


def test_launch_commands_are_host_specific(tmp_path: Path) -> None:
    assert launch_command(tmp_path, Host.MACOS_ARM64, Provider.VMWARE)[-1] == "--vmware"
    assert launch_command(
        tmp_path, Host.WINDOWS_AMD64, Provider.VIRTUALBOX
    )[0] == "powershell.exe"
    with pytest.raises(ValueError, match="non VM"):
        launch_command(tmp_path, Host.MACOS_ARM64, Provider.DOCKER)
    with pytest.raises(ValueError, match="non supportato"):
        launch_command(tmp_path, Host.MACOS_ARM64, Provider.VIRTUALBOX)


def test_macos_launcher_rejects_virtualbox_before_running_vagrant(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    calls = tmp_path / "vagrant-calls.txt"
    vagrant = fake_bin / "vagrant"
    vagrant.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$VAGRANT_CALLS\"\n",
        encoding="utf-8",
    )
    vagrant.chmod(0o755)

    completed = subprocess.run(
        (
            str(Path(__file__).resolve().parents[1] / "scripts" / "setup-vm.sh"),
            "--virtualbox",
        ),
        env=os.environ
        | {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "VAGRANT_CALLS": str(calls),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "VirtualBox non è supportato" in completed.stderr
    assert not calls.exists()
