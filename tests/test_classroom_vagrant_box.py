from __future__ import annotations

import hashlib
from pathlib import Path

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


def test_import_skips_exact_installed_box(tmp_path: Path) -> None:
    box = tmp_path / "classroom.box"
    box.write_bytes(CONTENT)
    calls = []

    result = import_box(
        artifact(),
        box,
        runner=lambda command, cwd: (
            calls.append(command)
            or (
                0,
                "1,,box-name,2cornot2c/ubuntu-vmware-0.1.0\n"
                "1,,box-provider,vmware_desktop\n",
            )
        ),
    )

    assert result.status == "skipped"
    assert len(calls) == 1


def test_import_does_not_force_overwrite(tmp_path: Path) -> None:
    box = tmp_path / "classroom.box"
    box.write_bytes(CONTENT)
    calls = []

    result = import_box(
        artifact(),
        box,
        runner=lambda command, cwd: (
            calls.append(command) or (0, "" if len(calls) == 1 else "added")
        ),
    )

    assert result.status == "succeeded"
    assert calls[1][:4] == (
        "vagrant",
        "box",
        "add",
        "2cornot2c/ubuntu-vmware-0.1.0",
    )
    assert "--force" not in calls[1]


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
