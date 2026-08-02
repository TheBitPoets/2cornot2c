from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

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
    assert "packer/classroom-release-target.version" in workflow
    assert 'RELEASE_VERSION" != "$expected_version' in workflow
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
        "\"${CLASSROOM_ACCEPTANCE_SHARE:-}\" \"${VAGRANT_DOTFILE_PATH:-}\" \"$*\" "
        '>> \"$VAGRANT_CALLS\"\n',
        encoding="utf-8",
    )
    vagrant.chmod(0o755)
    box = tmp_path / "classroom.box"
    box.write_bytes(b"box")
    shares = tmp_path / "shares"
    shares.mkdir()

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
            "TMPDIR": str(shares),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    first_call = calls.read_text(encoding="utf-8").splitlines()[0].split("|")
    assert first_call[0] == str(ROOT / "packer" / "acceptance")
    assert first_call[1] == "2cornot2c/acceptance-vmware_desktop"
    assert Path(first_call[2]).parent == shares
    assert Path(first_call[2]).name.startswith("2cornot2c-acceptance-share.")
    assert first_call[2] != str(ROOT)
    assert first_call[3] == ".vagrant-vmware_desktop"
    assert first_call[4] == (
        "box add 2cornot2c/acceptance-vmware_desktop "
        f"{box} --provider vmware_desktop --force"
    )


@pytest.mark.skipif(os.name == "nt", reason="richiede Bash/Unix")
def test_source_box_bootstrap_uses_isolated_vagrant_context(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    contexts = tmp_path / "contexts"
    contexts.mkdir()
    calls = tmp_path / "vagrant-calls.txt"
    vagrant_home = tmp_path / "vagrant-home"
    vagrant = fake_bin / "vagrant"
    vagrant.write_text(
        "#!/usr/bin/env bash\n"
        "test ! -f \"$PWD/Vagrantfile\" || exit 91\n"
        "printf '%s|%s\\n' \"$PWD\" \"$*\" >> \"$VAGRANT_CALLS\"\n",
        encoding="utf-8",
    )
    vagrant.chmod(0o755)

    completed = subprocess.run(
        (
            "bash",
            str(ROOT / "packer" / "ensure-source-box.sh"),
            "vmware_desktop",
            "202510.26.0",
        ),
        cwd=ROOT / "packer",
        env=os.environ
        | {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "TMPDIR": str(contexts),
            "VAGRANT_CALLS": str(calls),
            "VAGRANT_HOME": str(vagrant_home),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    recorded = [line.split("|", 1) for line in calls.read_text().splitlines()]
    assert [command for _, command in recorded] == [
        "box list --machine-readable",
        (
            "box add bento/ubuntu-24.04 --box-version 202510.26.0 "
            "--provider vmware_desktop "
            "--checksum d3b9ef74295cc3b87f5a8212356c317271b7705ae67272628308b34822e25a5f "
            "--checksum-type sha256"
        ),
    ]
    assert len({cwd for cwd, _ in recorded}) == 1
    assert all(Path(cwd).parent == contexts for cwd, _ in recorded)


@pytest.mark.skipif(os.name == "nt", reason="richiede Bash/Unix")
def test_source_box_bootstrap_rejects_preinstalled_box(tmp_path: Path) -> None:
    vagrant_home = tmp_path / "vagrant-home"
    vagrant_home.mkdir()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    vagrant = fake_bin / "vagrant"
    vagrant.write_text(
        "#!/usr/bin/env bash\n"
        "printf '1,,box-name,untrusted/source\\n'\n",
        encoding="utf-8",
    )
    vagrant.chmod(0o755)

    completed = subprocess.run(
        (
            "bash",
            str(ROOT / "packer" / "ensure-source-box.sh"),
            "virtualbox",
            "202510.26.0",
        ),
        cwd=ROOT / "packer",
        env=os.environ
        | {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "VAGRANT_HOME": str(vagrant_home),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 4
    assert "contiene già una box" in completed.stderr


def test_packer_toolchain_and_source_are_exactly_locked() -> None:
    toolchain = json.loads(
        (ROOT / "packer" / "toolchain.lock.json").read_text(encoding="utf-8")
    )
    sources = json.loads(
        (ROOT / "packer" / "source-boxes.lock.json").read_text(encoding="utf-8")
    )
    template = (ROOT / "packer" / "classroom.pkr.hcl").read_text(
        encoding="utf-8"
    )
    workflow = (
        ROOT / ".github" / "workflows" / "publish-classroom-boxes.yml"
    ).read_text(encoding="utf-8")

    assert toolchain["packer_version"] == "1.16.0"
    assert toolchain["plugins"]["github.com/hashicorp/vagrant"]["version"] == "1.1.5"
    assert toolchain["vagrant_plugins"]["vagrant-vmware-desktop"]["version"] == "3.0.5"
    assert 'required_version = "= 1.16.0"' in template
    assert 'version = "= 1.1.5"' in template
    assert set(sources["boxes"]) == {"virtualbox", "vmware_desktop"}
    assert all(len(box["sha256"]) == 64 for box in sources["boxes"].values())
    assert "install-locked-plugin.py --platform windows_amd64" in workflow
    assert "install-locked-plugin.py --platform darwin_arm64" in workflow
    assert "install-locked-vagrant-plugin.py" in workflow
    assert "--require-vagrant-vmware" in workflow
    assert "VAGRANT_HOME: ${{ runner.temp }}/2cornot2c-vagrant-" in workflow
