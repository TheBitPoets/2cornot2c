"""Execute the uninstall flow with native mutations replaced by offline doubles."""

import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
from venv import EnvBuilder

import pytest

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe")
pytestmark = pytest.mark.skipif(sys.platform != "win32" or not POWERSHELL, reason="Windows required")
IMAGE = "ghcr.io/thebitpoets/2cornot2c-student-dev@sha256:" + "a" * 64
ENDPOINT = "npipe:////./pipe/dockerDesktopLinuxEngine"


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def run_ps(script):
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        capture_output=True, text=True, timeout=40,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.fixture
def installation(tmp_path):
    home = tmp_path / "home"
    project = home / "project"
    state = home / ".2cornot2c"
    launcher = tmp_path / "localapp" / "2cornot2c"
    for path in (project / ".git", state, launcher, project / "docker/student-dev"):
        path.mkdir(parents=True, exist_ok=True)
    (project / "exercise.c").write_text("student work", encoding="utf-8")
    (project / "docker/student-dev/toolchain.lock.json").write_text(json.dumps({
        "image_repository": IMAGE.split("@")[0], "digest": IMAGE.split("@")[1],
    }), encoding="utf-8")
    (state / "bootstrap-state.json").write_text(json.dumps({
        "install_dir": str(project), "installed_by_bootstrap": ["Git.Git", "zyedidia.micro"],
    }), encoding="utf-8")
    records = [
        {"host": "windows-amd64", "key": "docker", "status": "succeeded"},
        {"host": "windows-amd64", "key": "virtualbox", "status": "updated"},
        {"host": "windows-amd64", "key": "wsl", "status": "restart_required"},
    ]
    (state / "installer.jsonl").write_text("\n".join(map(json.dumps, records)) + "\n", encoding="utf-8")
    return home, project, state, launcher


def exercise(installation, components="", *, preview=False, vm=False, answers=None,
             package_exit=0, package_present=False, image_exit=0, cleanup_exit=0,
             select_menu=False, external_packages=(), distributions=(), docker_inventory=None,
             during_package_removal="", without_filehash=False):
    home, project, state, launcher = installation
    if vm:
        (project / ".vagrant").mkdir(exist_ok=True)
    # Load the real entrypoint in an isolated script. No HOME reassignment:
    # replace its references with the fixture root in this test copy only.
    source = (ROOT / "scripts/uninstall-classroom-windows.ps1").read_text(encoding="utf-8")
    source = source.replace("$HOME", "$TestHome")
    mocks = r"""
function Read-Host {
    param($Prompt)
    $global:events.Add('prompt:' + $Prompt)
    if (-not $global:answers.Count) { throw 'Unexpected confirmation' }
    return $global:answers.Dequeue()
}
function winget {
    $global:events.Add('winget:' + ($args -join ' '))
    __DURING_PACKAGE_REMOVAL__
    $global:LASTEXITCODE = __PACKAGE_EXIT__
}
function docker { $global:events.Add('docker:' + ($args -join ' ')); $global:LASTEXITCODE = __IMAGE_EXIT__ }
function vagrant { $global:events.Add('vagrant:' + ($args -join ' ')); $global:LASTEXITCODE = 0 }
function Get-DetectedPackages { return @(__EXTERNAL__) }
$global:wslNames = @(__DISTROS__)
function Get-WslInventory { return @{installed=$true; distributions=@($global:wslNames); error=''} }
function wsl.exe {
    $global:events.Add('wsl:' + ($args -join ' ')); $global:LASTEXITCODE = 0
    $Deleted = $args[-1]
    $global:wslNames = @($global:wslNames | Where-Object { $_ -cne $Deleted })
}
function Get-DockerInventory {
    $Parsed = __DOCKER__ | ConvertFrom-Json
    $Result = @{}
    foreach ($Property in $Parsed.PSObject.Properties) { $Result[$Property.Name] = $Property.Value }
    return $Result
}
function git { $global:LASTEXITCODE = 0; return 'https://github.com/TheBitPoets/2cornot2c.git' }
function Start-Sleep { }
function Start-Process {
    $global:events.Add('wsl-cleanup'); return @{ ExitCode=__CLEANUP_EXIT__ }
}
function Test-PackageStillInstalled { param($PackageId); return __PRESENT__ }
function Remove-ItemProperty { $global:events.Add('remove-runonce') }
function Get-ClassroomShortcutPaths { return (Join-Path $LauncherDir 'test.lnk') }
function Remove-Item {
    param($LiteralPath, [switch]$Recurse, [switch]$Force)
    if ($LiteralPath -eq 'Env:VAGRANT_DOTFILE') { return }
    if (-not ([IO.Path]::GetFullPath($LiteralPath)).StartsWith(__ROOT__)) { throw 'Escaped fixture!' }
    $global:events.Add('remove:' + $LiteralPath)
}
""".replace("__PACKAGE_EXIT__", str(package_exit)).replace("__IMAGE_EXIT__", str(image_exit))
    mocks = mocks.replace("__CLEANUP_EXIT__", str(cleanup_exit))
    mocks = mocks.replace("__PRESENT__", "$true" if package_present else "$false")
    mocks = mocks.replace("__ROOT__", quote(home.parent))
    mocks = mocks.replace("__EXTERNAL__", ",".join(map(quote, external_packages)))
    mocks = mocks.replace("__DISTROS__", ",".join(map(quote, distributions)))
    if docker_inventory is None:
        docker_inventory = {"endpoint": ENDPOINT, "error": "", "containers": [], "volumes": [], "images": [], "networks": []}
    mocks = mocks.replace("__DOCKER__", quote(json.dumps(docker_inventory)))
    mocks = mocks.replace("__DURING_PACKAGE_REMOVAL__", during_package_removal)
    if without_filehash:
        mocks += "\nfunction Get-FileHash { throw [System.Management.Automation.CommandNotFoundException]::new('Get-FileHash unavailable') }\n"
    source = source.replace("$SafeInstallDir = Test-SafeInstallDirectory", mocks + "\n$SafeInstallDir = Test-SafeInstallDirectory", 1)
    script_file = home.parent / "isolated-uninstall.ps1"
    script_file.write_text(source, encoding="utf-8-sig")
    # The shortcut helper is absent, so no external PowerShell process is run.
    (launcher / "test.lnk").touch()
    args = "-Preview" if preview else "-SelectComponents" if select_menu else ""
    if not select_menu:
        args += " -Components " + quote(components)
    answers = ["DISINSTALLA"] if answers is None else answers
    setup = "\n".join("$global:answers.Enqueue(" + quote(a) + ")" for a in answers)
    return run_ps(f"""
$ErrorActionPreference = 'Stop'
$TestHome = {quote(home)}
$env:LOCALAPPDATA = {quote(launcher.parent)}
$env:CLASSROOM_INSTALL_DIR = {quote(project)}
$global:events = [System.Collections.Generic.List[string]]::new()
$global:answers = [System.Collections.Generic.Queue[string]]::new()
{setup}
$failure = $null
$output = @()
try {{ $output = @(& {quote(script_file)} {args} 6>&1) }} catch {{ $failure = $_.Exception.Message }}
@{{ events=@($global:events.ToArray()); error=$failure; output=($output -join "`n"); code=$LASTEXITCODE }} |
    ConvertTo-Json -Depth 8 -Compress
""")


def snapshot(root):
    return {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_preview_has_no_mutations_and_distinguishes_external_packages(installation):
    before = snapshot(installation[0])
    result = exercise(installation, "Git.Git", preview=True, answers=[], external_packages=["Oracle.VirtualBox"])
    assert result["error"] is None
    assert result["events"] == []
    plan = json.loads(result["output"])
    ids = [item["id"] for item in plan["options"]]
    assert "Git.Git" in ids and "Docker.DockerDesktop" in ids and "wsl" in ids
    external, = [item for item in plan["options"] if item["id"] == "Oracle.VirtualBox"]
    assert external["external"] is True
    assert plan["selected"] == ["Git.Git"]
    assert snapshot(installation[0]) == before


@pytest.mark.parametrize("selection", ["Oracle.VirtualBox", "not-a-component", "Git.Git,project"])
def test_invalid_or_vm_dependent_selection_fails_before_any_mutation(installation, selection):
    before = snapshot(installation[2])
    result = exercise(installation, selection, vm=True, answers=[])
    assert result["error"]
    assert "Componente non disponibile" in result["error"] or "La VM viene conservata" in result["error"]
    assert result["events"] == []
    assert snapshot(installation[2]) == before


def test_partial_removal_only_invokes_selected_package_and_keeps_other_ownership(installation):
    result = exercise(installation, "zyedidia.micro")
    assert result["error"] is None
    assert [e for e in result["events"] if not e.startswith("prompt:")] == [
        "winget:uninstall --id zyedidia.micro --exact --silent",
    ]
    home, project, state, launcher = installation
    saved = json.loads((state / "bootstrap-state.json").read_text(encoding="utf-8-sig"))
    assert saved["installed_by_bootstrap"] == ["Git.Git"]
    assert project.exists() and launcher.exists()
    assert '"docker"' in (state / "installer.jsonl").read_text()
    second = exercise(installation, "zyedidia.micro", answers=[])
    assert second["error"] and not second["events"]


@pytest.mark.parametrize("component,key", [("Git.Git", "git"), ("wsl", "wsl")])
def test_partial_removal_preserves_utf8_records(installation, component, key):
    log = installation[2] / "installer.jsonl"
    message = "Operazione già riuscita: perché è disponibile — 日本語 🐍"
    records = [
        {"host": "windows-amd64", "key": key, "status": "succeeded", "message": message},
        {"host": "windows-amd64", "key": "docker", "status": "succeeded", "message": message},
        {"host": "windows-amd64", "key": key, "status": "restart_required", "message": message},
        {"host": "windows-amd64", "key": key, "status": "updated", "message": message},
        {"host": "linux-amd64", "key": key, "status": "succeeded", "message": message},
    ]
    lines = [json.dumps(record, ensure_ascii=False).encode("utf-8") for record in records]
    log.write_bytes(b"\n".join(lines) + b"\n")  # Executor format: UTF-8 without BOM.

    answers = ["RIMUOVI WSL", "DISINSTALLA"] if component == "wsl" else ["DISINSTALLA"]
    result = exercise(installation, component, answers=answers)

    assert result["error"] is None
    assert result["code"] == 0
    assert log.read_bytes().splitlines() == [lines[1], lines[3], lines[4]]


@pytest.mark.parametrize("code,present", [(1603, False), (0, True)])
def test_failed_package_removal_retains_registry_and_project(installation, code, present):
    before = snapshot(installation[2])
    result = exercise(installation, "Git.Git", package_exit=code, package_present=present)
    assert result["code"] == 1
    assert snapshot(installation[2]) == before
    assert not any(e.startswith("remove:") for e in result["events"])


def test_image_only_never_uninstalls_docker_or_touches_project(installation):
    before = snapshot(installation[1])
    result = exercise(installation, "docker-image")
    assert result["error"] is None
    assert [e for e in result["events"] if not e.startswith("prompt:")] == ["docker:--host " + ENDPOINT + " image rm " + IMAGE]
    assert snapshot(installation[1]) == before


def test_image_failure_stops_before_package_or_project_removal(installation):
    result = exercise(installation, "docker-image,Git.Git,project", image_exit=1)
    assert result["error"], result["output"]
    assert not any(e.startswith(("winget:", "remove:")) for e in result["events"])


def test_project_only_creates_complete_backup_and_retains_image_and_registry(installation):
    home, project, state, launcher = installation
    (project / ".git/index").write_bytes(b"staged work")
    (project / "ignored.bin").write_bytes(b"ignored work")
    before = snapshot(project)
    result = exercise(installation, "project")
    assert result["error"] is None and result["code"] == 0, result["output"]
    backup, = home.glob("2cornot2c-backup-*")
    assert snapshot(backup) == before
    assert "remove:" + str(project) in result["events"]
    assert not any(e.startswith(("winget:", "docker:")) for e in result["events"])
    assert json.loads((state / "uninstall-retained-image.json").read_text(encoding="utf-8-sig"))["image"] == IMAGE
    assert (state / "bootstrap-state.json").exists() and launcher.exists()


def test_project_backup_and_recheck_do_not_require_filehash_cmdlet(installation):
    before = snapshot(installation[1])
    result = exercise(installation, "project", without_filehash=True)
    assert result["error"] is None and result["code"] == 0, result["output"]
    backup, = installation[0].glob("2cornot2c-backup-*")
    assert snapshot(backup) == before
    assert "remove:" + str(installation[1]) in result["events"]


@pytest.mark.parametrize("change", ["save", "create", "rename", "junction", "backup", "missing", "locked"])
def test_project_changes_after_backup_block_removal(installation, change):
    home, project, state, launcher = installation
    before = snapshot(project)
    changes = {
        # Same length: a size-only check would miss this save.
        "save": "[IO.File]::WriteAllText((Join-Path $SafeInstallDir 'exercise.c'), 'changed work')",
        "create": "[IO.File]::WriteAllText((Join-Path $SafeInstallDir 'new-exercise.c'), 'new work')",
        "rename": "Move-Item -LiteralPath (Join-Path $SafeInstallDir 'exercise.c') -Destination (Join-Path $SafeInstallDir 'renamed.c')",
        "junction": "New-Item -ItemType Junction -Path (Join-Path $SafeInstallDir 'link') -Target $StateDir | Out-Null",
        "backup": "[IO.File]::WriteAllText((Join-Path $BackupPath 'exercise.c'), 'bad backup')",
        "missing": "Move-Item -LiteralPath (Join-Path $SafeInstallDir 'exercise.c') -Destination (Join-Path $TestHome 'saved-exercise.c')",
        "locked": "$script:lockedExercise = [IO.File]::Open((Join-Path $SafeInstallDir 'exercise.c'), [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)",
    }
    result = exercise(installation, "project,zyedidia.micro", during_package_removal=changes[change])
    assert result["code"] == 1
    assert "winget:uninstall --id zyedidia.micro --exact --silent" in result["events"]
    assert not any(e.startswith("remove:") or e == "remove-runonce" for e in result["events"])
    assert project.exists() and launcher.exists()
    backup, = home.glob("2cornot2c-backup-*")
    if change != "backup":
        assert snapshot(backup) == before
    if change == "save":
        assert (project / "exercise.c").read_text() == "changed work"
    elif change == "create":
        assert (project / "new-exercise.c").read_text() == "new work"
    saved = json.loads((state / "bootstrap-state.json").read_text(encoding="utf-8-sig"))
    assert saved["installed_by_bootstrap"] == ["Git.Git"]


def test_unchanged_project_can_be_removed_after_package_operations(installation):
    before = snapshot(installation[1])
    result = exercise(installation, "project,zyedidia.micro")
    assert result["error"] is None and result["code"] == 0
    backup, = installation[0].glob("2cornot2c-backup-*")
    assert snapshot(backup) == before
    assert "remove:" + str(installation[1]) in result["events"]


@pytest.mark.parametrize("selection,answers", [("vm", ["no"]), ("wsl", ["no"]), ("Git.Git", ["no"]), ("", [])])
def test_cancellation_and_empty_selection_do_nothing(installation, selection, answers):
    result = exercise(installation, selection, vm=True, answers=answers)
    assert not any(not e.startswith("prompt:") for e in result["events"])
    assert result["code"] == 2


def test_menu_toggles_selection_without_preselecting_others(installation):
    # Project, image, Docker, Git, micro, WSL, shortcuts (no VM).
    result = exercise(installation, select_menu=True, answers=["5", "", "DISINSTALLA"])
    assert result["error"] is None
    assert [e for e in result["events"] if e.startswith("winget:")] == [
        "winget:uninstall --id zyedidia.micro --exact --silent",
    ]


def test_wsl_refusal_preserves_ownership(installation):
    before = snapshot(installation[2])
    result = exercise(installation, "wsl", answers=["RIMUOVI WSL", "DISINSTALLA"], cleanup_exit=2)
    assert result["error"]
    assert snapshot(installation[2]) == before
    assert "wsl-cleanup" in result["events"]


def test_wsl_cannot_be_removed_under_retained_docker(installation):
    result = exercise(installation, "wsl", package_present=True, answers=[])
    assert "Docker Desktop" in result["error"]
    assert not result["events"]


def test_vm_removal_requires_distinct_confirmation_and_preserves_project(installation):
    result = exercise(installation, "vm", vm=True, answers=["ELIMINA VM", "DISINSTALLA"])
    assert result["error"] is None
    assert "vagrant:destroy --force" in result["events"]
    assert "remove:" + str(installation[1]) not in result["events"]
    assert list(installation[0].glob("2cornot2c-backup-*"))
    assert not any(e.startswith(("winget:", "docker:")) for e in result["events"])


def test_successful_wsl_removal_clears_only_its_ownership(installation):
    result = exercise(installation, "wsl", answers=["RIMUOVI WSL", "DISINSTALLA"])
    assert result["error"] is None
    log = (installation[2] / "installer.jsonl").read_text(encoding="utf-8-sig")
    assert '"wsl"' not in log and '"docker"' in log
    assert json.loads((installation[2] / "bootstrap-state.json").read_text(encoding="utf-8-sig"))["installed_by_bootstrap"] == ["Git.Git", "zyedidia.micro"]


def test_shortcuts_only_keeps_software_and_project(installation):
    result = exercise(installation, "shortcuts")
    assert result["error"] is None
    assert [e for e in result["events"] if not e.startswith("prompt:")] == [
        "remove:" + str(installation[3] / "test.lnk"),
    ]


def test_backup_rejects_junction_before_removing_project(installation):
    project = installation[1]
    outside = installation[0] / "personal"
    outside.mkdir()
    (outside / "notes").write_text("keep", encoding="utf-8")
    run_ps(f"New-Item -ItemType Junction -Path {quote(project / 'link')} -Target {quote(outside)} | Out-Null; '{{}}'")
    result = exercise(installation, "project")
    assert result["code"] == 1
    assert not any(e.startswith(("remove:", "winget:", "docker:")) for e in result["events"])
    assert (outside / "notes").read_text() == "keep"


def test_corrupt_ownership_stops_before_confirmation_or_removal(installation):
    (installation[2] / "installer.jsonl").write_text("not json", encoding="utf-8")
    result = exercise(installation, "Git.Git", answers=[])
    assert result["error"]
    assert not result["events"]


def test_retained_image_remains_selectable_after_project_removal(installation):
    home, project, state, _ = installation
    project.rename(home / "saved-project")
    (state / "uninstall-retained-image.json").write_text(json.dumps({"image": IMAGE}), encoding="utf-8")
    result = exercise(installation, "docker-image", preview=True, answers=[])
    assert result["error"] is None
    plan = json.loads(result["output"])
    assert plan["image"] == IMAGE
    assert "project" not in [item["id"] for item in plan["options"]]
    assert not plan["blockers"] and not result["events"]


@pytest.mark.parametrize("choice,expected", [("2", ["uninstall"]), ("0", []), ("1", ["bootstrap"])])
@pytest.mark.parametrize("runtime", ["absent", "removed", "unlaunchable"])
def test_incomplete_environment_respects_recovery_choice(installation, choice, expected, runtime):
    home, project, _, launcher = installation
    if runtime != "absent":
        venv = project / ".installer-venv"
        if runtime == "removed":
            # Build a real redirector even when pytest uses the base interpreter.
            EnvBuilder(with_pip=False, symlinks=False).create(venv)
            probe = subprocess.run(
                [str(venv / "Scripts/python.exe"), "-I", "-c", "pass"],
                capture_output=True, timeout=10,
            )
            assert probe.returncode == 0, probe.stderr
        else:
            (venv / "Scripts").mkdir(parents=True)
            (venv / "Scripts/python.exe").write_bytes(b"invalid executable")
        (venv / "pyvenv.cfg").write_text(f"home = {home / 'missing-python'}\n", encoding="utf-8")
        if runtime == "removed":
            probe = subprocess.run(
                [str(venv / "Scripts/python.exe"), "-I", "-c", "pass"],
                capture_output=True, timeout=10,
            )
            assert probe.returncode != 0, "The orphaned venv must not start Python"
    (launcher / "uninstall-classroom-windows.ps1").touch()
    source = (ROOT / "scripts/manage-classroom-windows.ps1").read_text(encoding="utf-8")
    manager = home.parent / "manager.ps1"
    manager.write_text(source.replace("$HOME", "$TestHome"), encoding="utf-8-sig")
    result = run_ps(f"""
$ErrorActionPreference = 'Stop'
$TestHome = {quote(home)}
$env:LOCALAPPDATA = {quote(launcher.parent)}
$global:calls = [System.Collections.Generic.List[string]]::new()
function Read-Host {{ return {quote(choice)} }}
function Invoke-RestMethod {{
    if ({quote(choice)} -ne '1') {{ throw 'Unexpected bootstrap download' }}
    $global:calls.Add('bootstrap'); return 'exit 0'
}}
function powershell.exe {{
    if ('-SelectComponents' -notin $args) {{ throw 'Selection required' }}
    $global:calls.Add('uninstall'); $global:LASTEXITCODE = 0
}}
& {quote(manager)}
@{{ calls=@($global:calls.ToArray()); code=$LASTEXITCODE }} | ConvertTo-Json -Compress
""")
    assert result["calls"] == expected
    assert result["code"] == (2 if choice == "0" else 0)


@pytest.mark.parametrize("exit_code", [0, 2, 1])
def test_working_python_runs_tui_without_recovery_and_preserves_exit_code(installation, exit_code):
    home, project, _, launcher = installation
    venv = project / ".installer-venv"
    EnvBuilder(with_pip=False, symlinks=False).create(venv)
    (project / "installer").mkdir()
    (project / "installer/__init__.py").touch()
    (project / "installer/tui.py").write_text(
        "from pathlib import Path\nPath('tui-started').touch()\n" + f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    (launcher / "uninstall-classroom-windows.ps1").touch()
    source = (ROOT / "scripts/manage-classroom-windows.ps1").read_text(encoding="utf-8")
    manager = home.parent / "manager.ps1"
    manager.write_text(source.replace("$HOME", "$TestHome"), encoding="utf-8-sig")
    result = run_ps(f"""
$ErrorActionPreference = 'Stop'
$TestHome = {quote(home)}
$env:LOCALAPPDATA = {quote(launcher.parent)}
function Read-Host {{ throw 'Unexpected recovery menu' }}
function Invoke-RestMethod {{ throw 'Unexpected bootstrap download' }}
function powershell.exe {{ throw 'Unexpected uninstall' }}
& {quote(manager)}
@{{ code=$LASTEXITCODE }} | ConvertTo-Json -Compress
""")
    assert result["code"] == exit_code
    assert (project / "tui-started").exists()


def test_external_program_requires_extra_consent_and_can_be_removed(installation):
    result = exercise(installation, "Oracle.VirtualBox", external_packages=["Oracle.VirtualBox"],
                      answers=["RIMUOVI COMPONENTI ESTERNI", "DISINSTALLA"])
    assert result["error"] is None
    assert "winget:uninstall --id Oracle.VirtualBox --exact --silent" in result["events"]
    saved = json.loads((installation[2] / "bootstrap-state.json").read_text(encoding="utf-8-sig"))
    assert saved["installed_by_bootstrap"] == ["Git.Git", "zyedidia.micro"]


def test_external_program_cannot_be_removed_with_ordinary_confirmation(installation):
    result = exercise(installation, "Oracle.VirtualBox", external_packages=["Oracle.VirtualBox"], answers=["DISINSTALLA"])
    assert result["code"] == 2
    assert not any(e.startswith("winget:") for e in result["events"])


def test_only_named_wsl_distribution_is_removed(installation):
    result = exercise(installation, "wsl-distro:Ubuntu", distributions=["Ubuntu", "Debian"],
                      answers=["RIMUOVI COMPONENTI ESTERNI", "ELIMINA WSL Ubuntu", "DISINSTALLA"])
    assert result["error"] is None
    assert [e for e in result["events"] if e.startswith("wsl:")] == ["wsl:--unregister Ubuntu"]
    assert "wsl-cleanup" not in result["events"]
    assert not any(e.startswith(("docker:", "winget:", "remove:")) for e in result["events"])


def test_wsl_component_is_blocked_while_an_unselected_distribution_remains(installation):
    result = exercise(installation, "wsl,wsl-distro:Ubuntu", distributions=["Ubuntu", "Debian"], answers=[])
    assert "Debian" in result["error"]
    assert not result["events"]


def test_distro_confirmation_must_name_the_selected_distribution(installation):
    result = exercise(installation, "wsl-distro:Ubuntu", distributions=["Ubuntu"],
                      answers=["RIMUOVI COMPONENTI ESTERNI", "ELIMINA WSL Debian"])
    assert result["code"] == 2
    assert not any(e.startswith("wsl:") for e in result["events"])


def test_docker_uninstall_requires_selection_of_its_data(installation):
    result = exercise(installation, "Docker.DockerDesktop", answers=[])
    assert "anche i suoi dati" in result["error"]
    assert not result["events"]


def test_external_docker_uninstall_requires_data_consent(installation):
    (installation[2] / "installer.jsonl").write_text("", encoding="utf-8")
    result = exercise(installation, "Docker.DockerDesktop,docker-data", external_packages=["Docker.DockerDesktop"],
                      answers=["RIMUOVI COMPONENTI ESTERNI", "ELIMINA DATI DOCKER", "DISINSTALLA"])
    assert result["error"] is None
    assert "winget:uninstall --id Docker.DockerDesktop --exact --silent" in result["events"]
    assert not any(e.startswith("docker:") for e in result["events"])


def test_docker_data_deletes_only_enumerated_objects_on_explicit_local_endpoint(installation):
    inventory = {"endpoint": ENDPOINT, "error": "", "containers": [{"ID": "abc", "Names": "personal-app"}],
                 "volumes": [{"Name": "personal-files"}], "images": [{"ID": "sha256:def"}],
                 "networks": [{"ID": "123", "Name": "personal-network"}]}
    result = exercise(installation, "docker-data", docker_inventory=inventory,
                      answers=["RIMUOVI COMPONENTI ESTERNI", "ELIMINA DATI DOCKER", "DISINSTALLA"])
    assert result["error"] is None
    assert [e for e in result["events"] if e.startswith("docker:")] == [
        f"docker:--host {ENDPOINT} container rm --force abc",
        f"docker:--host {ENDPOINT} volume rm personal-files",
        f"docker:--host {ENDPOINT} image rm --force sha256:def",
        f"docker:--host {ENDPOINT} network rm 123",
    ]
    assert not any(e.startswith(("winget:", "wsl:")) for e in result["events"])


def test_docker_data_is_not_removable_when_local_inventory_is_unavailable(installation):
    inventory = {"endpoint": "", "error": "Contesto Docker non locale", "containers": [], "volumes": [], "images": [], "networks": []}
    result = exercise(installation, "docker-data", docker_inventory=inventory, answers=[])
    assert "non locale" in result["error"]
    assert not result["events"]


def test_select_all_then_clear_never_runs_a_removal(installation):
    result = exercise(installation, select_menu=True, answers=["t", "z", ""])
    assert result["code"] == 2
    assert all(e.startswith("prompt:") for e in result["events"])


def run_definitions(body):
    source = ROOT / "scripts/uninstall-classroom-windows.ps1"
    return run_ps(f"""
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput(
    [IO.File]::ReadAllText({quote(source)}), [ref]$tokens, [ref]$errors)
if ($errors.Count) {{ throw ($errors | Out-String) }}
foreach ($definition in $ast.FindAll({{ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
}}, $true)) {{ . ([scriptblock]::Create($definition.Extent.Text)) }}
{body}
""")


def test_inventory_rejects_remote_context_before_contacting_daemon():
    result = run_definitions(r"""
$env:DOCKER_HOST = 'tcp://remote.example:2375'
$env:DOCKER_CONTEXT = ''
function Invoke-InventoryCommand { throw 'No remote request allowed' }
Get-DockerInventory | ConvertTo-Json -Compress
""")
    assert "non locale" in result["error"]
    assert result["endpoint"] == ""


def test_docker_cleanup_rejects_changed_inventory_before_removing_anything():
    result = run_definitions(r"""
$Original = @{endpoint='npipe:////./pipe/docker_engine'; error=''; containers=@(@{ID='old'}); volumes=@(); images=@(); networks=@()}
function Get-DockerInventory {
    return @{endpoint='npipe:////./pipe/docker_engine'; error=''; containers=@(@{ID='new'}); volumes=@(); images=@(); networks=@()}
}
$script:removed = $false
function docker { $script:removed = $true; throw 'Unexpected mutation' }
$failure = ''
try { Remove-SelectedDockerData $Original } catch { $failure=$_.Exception.Message }
@{error=$failure; removed=$script:removed} | ConvertTo-Json -Compress
""")
    assert "cambiati" in result["error"]
    assert result["removed"] is False


def test_inventory_probe_decodes_wsl_unicode_without_nulls():
    code = "$b = [Text.Encoding]::Unicode.GetBytes('Ubuntu'); [Console]::OpenStandardOutput().Write($b,0,$b.Length)"
    encoded = base64.b64encode(code.encode("utf-16-le")).decode("ascii")
    result = run_definitions(f"Invoke-InventoryCommand 'powershell.exe' @('-NoProfile','-EncodedCommand',{quote(encoded)}) | ConvertTo-Json -Compress")
    assert result["code"] == 0
    assert result["output"] == "Ubuntu"


def test_inventory_probe_times_out_and_reaps_child():
    encoded = base64.b64encode("Start-Sleep -Seconds 20".encode("utf-16-le")).decode("ascii")
    result = run_definitions(f"Invoke-InventoryCommand 'powershell.exe' @('-NoProfile','-EncodedCommand',{quote(encoded)}) -TimeoutMilliseconds 150 | ConvertTo-Json -Compress")
    assert result["code"] == 124


def test_inventory_probe_passes_native_switches_without_quotes(tmp_path):
    # WSL reads the raw command line; quoting a switch can launch it as a
    # Linux command. A native fixture verifies the actual process boundary.
    executable = tmp_path / "native probe.exe"
    result = run_definitions(f"""
Add-Type -TypeDefinition 'using System; class Probe {{ public static void Main() {{ Console.WriteLine(Environment.CommandLine); }} }}' -OutputAssembly {quote(executable)} -OutputType ConsoleApplication
Invoke-InventoryCommand {quote(executable)} @('--list', '--quiet') | ConvertTo-Json -Compress
""")
    assert result["code"] == 0
    assert result["output"].endswith(" --list --quiet")


@pytest.mark.parametrize("exit_code,distribution,require_empty", [(1, "", False), (0, "Ubuntu", False), (0, "docker-desktop", True)])
def test_wsl_cleanup_fails_closed_without_mutating_distributions(tmp_path, exit_code, distribution, require_empty):
    source = (ROOT / "scripts/remove-wsl-windows.ps1").read_text(encoding="utf-8")
    cleanup = tmp_path / "cleanup.ps1"
    cleanup.write_text(source, encoding="utf-8-sig")
    result = run_ps(f"""
$global:calls = [System.Collections.Generic.List[string]]::new()
function wsl.exe {{
    $global:calls.Add(($args -join ' '))
    if (($args -join ' ') -ne '--list --quiet') {{ throw 'Mutation attempted' }}
    $global:LASTEXITCODE = {exit_code}
    Write-Output {quote(distribution)}
}}
& {quote(cleanup)} {"-RequireEmpty" if require_empty else ""}
@{{ calls=@($global:calls.ToArray()); code=$LASTEXITCODE }} | ConvertTo-Json -Compress
""")
    assert result == {"calls": ["--list --quiet"], "code": 2}


def test_wsl_cleanup_refuses_a_different_administrative_account(tmp_path):
    source = (ROOT / "scripts/remove-wsl-windows.ps1").read_text(encoding="utf-8")
    cleanup = tmp_path / "cleanup.ps1"
    cleanup.write_text(source, encoding="utf-8-sig")
    result = run_ps(f"""
$global:called = $false
function wsl.exe {{ $global:called=$true; throw 'Unexpected WSL command' }}
& {quote(cleanup)} -RequireEmpty -ExpectedUserSid 'S-1-0-0'
@{{ called=$global:called; code=$LASTEXITCODE }} | ConvertTo-Json -Compress
""")
    assert result == {"called": False, "code": 2}
