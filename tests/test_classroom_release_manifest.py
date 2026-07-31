from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

from installer.artifacts import load_release
from installer.model import Host, Provider


ROOT = Path(__file__).resolve().parents[1]


def test_release_manifest_generator_emits_installable_contract(tmp_path: Path) -> None:
    vmware = tmp_path / "vmware.box"
    virtualbox = tmp_path / "virtualbox.box"
    output = tmp_path / "release-manifest.json"
    vmware.write_bytes(b"vmware")
    virtualbox.write_bytes(b"virtualbox")
    script = ROOT / "packer" / "create-release-manifest.py"

    completed = subprocess.run(
        (
            sys.executable,
            str(script),
            "--version",
            "1.2.3",
            "--repository",
            "TheBitPoets/2cornot2c",
            "--vmware",
            str(vmware),
            "--virtualbox",
            str(virtualbox),
            "--output",
            str(output),
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    release = load_release(output)
    assert release.version == "1.2.3"
    assert {(item.host, item.provider) for item in release.artifacts} == {
        (Host.MACOS_ARM64, Provider.VMWARE),
        (Host.WINDOWS_AMD64, Provider.VIRTUALBOX),
    }
    assert all(
        item.url.startswith(
            "https://github.com/TheBitPoets/2cornot2c/releases/download/"
        )
        for item in release.artifacts
    )
    assert {item.name for item in release.artifacts} == {
        "VMware ARM64",
        "VirtualBox AMD64",
    }


def test_release_workflow_keeps_dispatch_input_out_of_shell_source() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "publish-classroom-boxes.yml"
    ).read_text(encoding="utf-8")

    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert "RELEASE_VERSION: ${{ inputs.version }}" in workflow
    run_blocks = re.findall(
        r"(?m)^        run: \|\n((?:^          .*(?:\n|$))*)",
        workflow,
    )
    assert run_blocks
    for run_block in run_blocks:
        assert "${{ inputs.version }}" not in run_block
    assert "Length -ge 2GB" in workflow
    assert "stat -f %z" in workflow


def test_acceptance_import_uses_isolated_vagrantfile(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    calls = tmp_path / "vagrant-calls.txt"
    vagrant = fake_bin / "vagrant"
    vagrant.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s|%s|%s|%s|%s\\n' \"$PWD\" \"${CLASSROOM_BOX_NAME:-}\" "
        "\"${CLASSROOM_REPO_ROOT:-}\" \"${VAGRANT_DOTFILE_PATH:-}\" \"$*\" "
        '>> \"$VAGRANT_CALLS\"\n',
        encoding="utf-8",
    )
    vagrant.chmod(0o755)
    box = tmp_path / "classroom.box"
    box.write_bytes(b"box")

    completed = subprocess.run(
        (
            str(ROOT / "packer" / "acceptance" / "test-box.sh"),
            "vmware_desktop",
            str(box),
        ),
        cwd=ROOT,
        env=os.environ
        | {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "VAGRANT_CALLS": str(calls),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    first_call = calls.read_text(encoding="utf-8").splitlines()[0].split("|")
    assert first_call == [
        str(ROOT / "packer" / "acceptance"),
        "2cornot2c/acceptance-vmware_desktop",
        str(ROOT),
        ".vagrant-vmware_desktop",
        (
            "box add 2cornot2c/acceptance-vmware_desktop "
            f"{box} --provider vmware_desktop --force"
        ),
    ]
