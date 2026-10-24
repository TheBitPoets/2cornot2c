"""Run real recovery functions offline; never execute installer entrypoints."""

import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(
    not POWERSHELL or sys.platform != "win32", reason="Windows PowerShell required",
)


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def run_functions(source, body):
    script = """
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    __SOURCE__, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($definition in $ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
}, $true)) { . ([scriptblock]::Create($definition.Extent.Text)) }
__BODY__
""".replace("__SOURCE__", quote(ROOT / "scripts" / source)).replace("__BODY__", body)
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True, text=True, timeout=45, check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("native_code", [0, 3010, -2147012894, 50])
def test_wsl_reports_native_cause_and_only_registers_resume_after_success(tmp_path, native_code):
    result = run_functions("prepare-wsl-windows.ps1", """
$env:LOCALAPPDATA = __TEMP__
$script:resume = 0
function wsl.exe {
    Write-Output 'Underlying WSL failure: 0x80072ee2'
    Write-Error 'Network unavailable'
    $global:LASTEXITCODE = __CODE__
}
function Start-Process {
    param($FilePath, $ArgumentList, $Verb, $WindowStyle, [switch]$Wait, [switch]$PassThru)
    if ($Verb -ne 'RunAs' -or $WindowStyle -ne 'Hidden') { throw 'unsafe invocation' }
    $path = $ArgumentList[-1].Trim('"')
    $code = Invoke-WslInstall -LogPath $path
    return @{ExitCode=$code}
}
function New-ItemProperty { $script:resume++ }
$messages = @(& { $script:code = Invoke-WslSetup -ScriptPath 'offline.ps1' } 6>&1)
$log = Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA '2cornot2c/diagnostics') -Filter '*.json'
@{code=$script:code; resume=$script:resume; messages=($messages | Out-String);
  report=(Get-Content -LiteralPath $log.FullName -Raw | ConvertFrom-Json)} | ConvertTo-Json -Depth 6 -Compress
""".replace("__TEMP__", quote(tmp_path)).replace("__CODE__", str(native_code)))
    success = native_code in (0, 3010)
    assert result["code"] == (0 if success else 1)
    assert result["resume"] == int(success)
    assert result["report"]["exit_code"] == native_code
    assert "0x80072ee2" in result["report"]["output"]
    assert "Network unavailable" in result["report"]["output"]
    if not success:
        assert "WSL_INSTALL_FAILED" in result["messages"]
        assert str(native_code) in result["messages"]
        assert "0x80072ee2" in result["messages"]


@pytest.mark.parametrize("mode, marker", [
    ("cancel", "WSL_UAC_CANCELLED"), ("missing", "WSL_REPORT_MISSING"),
    ("resume", "WSL_RESUME_FAILED"),
])
def test_wsl_separates_uac_report_and_resume_failures(tmp_path, mode, marker):
    result = run_functions("prepare-wsl-windows.ps1", """
$env:LOCALAPPDATA = __TEMP__
function Start-Process {
    param($FilePath, $ArgumentList, $Verb, $WindowStyle, [switch]$Wait, [switch]$PassThru)
    if ('__MODE__' -eq 'cancel') { throw [System.ComponentModel.Win32Exception]::new(1223) }
    if ('__MODE__' -eq 'resume') {
        @{phase='wsl-install'; exit_code=0; output='ok'} | ConvertTo-Json |
            Set-Content -LiteralPath $ArgumentList[-1].Trim('"') -Encoding UTF8
    }
    return @{ExitCode=0}
}
function New-ItemProperty { throw 'registry denied' }
$messages = @(& { $script:code = Invoke-WslSetup -ScriptPath 'offline.ps1' } 6>&1)
@{code=$script:code; messages=($messages | Out-String)} | ConvertTo-Json -Compress
""".replace("__TEMP__", quote(tmp_path)).replace("__MODE__", mode))
    assert result["code"] == 1
    assert marker in result["messages"]


REQUIRED = [
    "scripts/student_lab_cli.py", "installer/tui.py", "requirements-utui.txt",
    *[f"scripts/{name}-windows.ps1" for name in (
        "manage-classroom", "launch-classroom", "prepare-wsl",
        "remove-classroom-shortcuts", "remove-wsl", "update-classroom", "uninstall-classroom",
    )],
]


def git(*args):
    result = subprocess.run(["git", *map(str, args)], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture
def origin(tmp_path):
    source = tmp_path / "origin with spaces"
    source.mkdir()
    git("init", source)
    for name in REQUIRED:
        file = source / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("fixture\n", encoding="utf-8")
    git("-C", source, "add", ".")
    git("-C", source, "-c", "user.name=Test", "-c", "user.email=test@example.test",
        "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
    return source


def prepare(directory, source):
    return run_functions("bootstrap-classroom-windows.ps1", """
try {
    Initialize-ClassroomRepository -Directory __DIR__ -Url __URL__ | Out-Null
    @{ok=$true} | ConvertTo-Json -Compress
} catch {
    @{ok=$false; error=$_.Exception.Message} | ConvertTo-Json -Compress
}
""".replace("__DIR__", quote(directory)).replace("__URL__", quote(source)))


def test_incomplete_checkout_is_backed_up_and_rerun_becomes_idempotent(tmp_path, origin):
    target = tmp_path / "student workspace"
    git("init", target)
    git("-C", target, "remote", "add", "origin", origin)
    original_config = (target / ".git/config").read_bytes()
    assert prepare(target, origin)["ok"]
    backup, = tmp_path.glob("student workspace.incomplete-*")
    assert (backup / ".git/config").read_bytes() == original_config
    assert all((target / name).is_file() for name in REQUIRED)
    assert prepare(target, origin)["ok"]
    assert len(list(tmp_path.glob("student workspace.incomplete-*"))) == 1


@pytest.mark.parametrize("condition", ["user-file", "wrong-origin", "lock", "occupied"])
def test_recovery_preserves_uncertain_or_occupied_checkout(tmp_path, origin, condition):
    target = tmp_path / "student"
    target.mkdir()
    if condition != "occupied":
        git("init", target)
        git("-C", target, "remote", "add", "origin", origin if condition != "wrong-origin" else "wrong")
    if condition in ("user-file", "occupied"):
        (target / "exercise.c").write_text("my work", encoding="utf-8")
    if condition == "lock":
        (target / ".git/index.lock").write_text("busy", encoding="utf-8")
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    result = prepare(target, origin)
    assert not result["ok"]
    assert "E1" in result["error"]
    assert before == {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    assert not list(tmp_path.glob("student.incomplete-*"))


def test_existing_checkout_with_missing_entrypoint_is_not_overwritten(tmp_path, origin):
    target = tmp_path / "student"
    git("clone", origin, target)
    (target / REQUIRED[0]).unlink()
    (target / "exercise.c").write_text("keep", encoding="utf-8")
    result = prepare(target, origin)
    assert not result["ok"]
    assert "checkout incompleto" in result["error"]
    assert not (target / REQUIRED[0]).exists()
    assert (target / "exercise.c").read_text() == "keep"


@pytest.mark.parametrize("actual,expected,equivalent", [
    ("https://github.com/TheBitPoets/2cornot2c", "https://github.com/TheBitPoets/2cornot2c.git", True),
    ("HTTPS://GITHUB.COM/TheBitPoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c", True),
    ("https://github.com/Other/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com/TheBitPoets/other.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com/thebitpoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("http://github.com/TheBitPoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://user:secret@github.com/TheBitPoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com:443/TheBitPoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com/TheBitPoets/2cornot2c.git?x=1", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com/TheBitPoets/2cornot2c.git#x", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com/TheBitPoets/2cornot2c.git/", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com/TheBitPoets%2fother/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://github.com.example/TheBitPoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("https://example.test/repo", "https://example.test/repo.git", False),
    ("git@github.com:TheBitPoets/2cornot2c.git", "https://github.com/TheBitPoets/2cornot2c.git", False),
    ("custom path", "custom path", True),
    ("custom path", "CUSTOM PATH", False),
])
def test_origin_equivalence_is_restricted(actual, expected, equivalent):
    result = run_functions("bootstrap-classroom-windows.ps1", """
@{equivalent=(Test-ClassroomRepositoryOrigin -Actual __ACTUAL__ -Expected __EXPECTED__)} |
    ConvertTo-Json -Compress
""".replace("__ACTUAL__", quote(actual)).replace("__EXPECTED__", quote(expected)))
    assert result["equivalent"] is equivalent


@pytest.mark.parametrize("condition,marker", [
    ("absent", "origine Git assente"),
    ("empty", "origine Git assente"),
    ("malformed", "lettura dell'origine Git non riuscita"),
    ("multiple", "origine Git ambigua"),
    ("different", "origine Git diversa da quella attesa"),
    ("without-suffix", "operazione Git in corso o interrotta"),
    ("host-case", "operazione Git in corso o interrotta"),
])
def test_origin_diagnostics_preserve_checkout_and_hide_credentials(tmp_path, condition, marker):
    target = tmp_path / "student"
    expected = "https://github.com/TheBitPoets/2cornot2c.git"
    git("init", target)
    config = target / ".git/config"
    if condition == "malformed":
        config.write_text("[invalid secret-value\n", encoding="utf-8")
    elif condition == "empty":
        with config.open("a", encoding="utf-8") as stream:
            stream.write('\n[remote "origin"]\nurl =\n')
    elif condition != "absent":
        actual = {
            "multiple": expected,
            "different": "https://user:secret-value@example.test/repo.git",
            "without-suffix": expected.removesuffix(".git"),
            "host-case": expected.replace("github.com", "GITHUB.COM"),
        }[condition]
        git("-C", target, "remote", "add", "origin", actual)
        if condition == "multiple":
            git("-C", target, "config", "--add", "remote.origin.url", "secret-value")
    # Stop the accepted variants before clone/pull, proving the origin gate passed.
    (target / ".git/index.lock").write_text("audit lock", encoding="utf-8")
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    result = prepare(target, expected)
    assert not result["ok"]
    assert marker in result["error"]
    assert "secret-value" not in result["error"]
    assert before == {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
    assert not list(tmp_path.glob("student.incomplete-*"))


def test_failed_reclone_keeps_original_metadata(tmp_path):
    target = tmp_path / "student"
    missing = tmp_path / "unreachable-origin"
    git("init", target)
    git("-C", target, "remote", "add", "origin", missing)
    original = (target / ".git/config").read_bytes()
    result = prepare(target, missing)
    assert not result["ok"]
    assert "E12" in result["error"]
    backup, = tmp_path.glob("student.incomplete-*")
    assert (backup / ".git/config").read_bytes() == original


@pytest.mark.parametrize("existing", [False, True])
def test_new_or_empty_directory_is_populated(tmp_path, origin, existing):
    target = tmp_path / "new student"
    if existing:
        target.mkdir()
    assert prepare(target, origin)["ok"]
    assert all((target / name).is_file() for name in REQUIRED)


@pytest.mark.parametrize("link_metadata", [False, True])
def test_junctions_are_rejected_without_touching_their_destination(tmp_path, origin, link_metadata):
    real = tmp_path / "real-repository"
    git("init", real)
    git("-C", real, "remote", "add", "origin", origin)
    target = tmp_path / "student"
    if link_metadata:
        target.mkdir()
    link = target / ".git" if link_metadata else target
    destination = real / ".git" if link_metadata else real
    before = (real / ".git/config").read_bytes()
    result = run_functions("bootstrap-classroom-windows.ps1", """
New-Item -ItemType Junction -Path __LINK__ -Target __DEST__ | Out-Null
try {
    Initialize-ClassroomRepository -Directory __DIR__ -Url __URL__ | Out-Null
    @{ok=$true} | ConvertTo-Json -Compress
} catch {
    @{ok=$false; error=$_.Exception.Message} | ConvertTo-Json -Compress
}
""".replace("__LINK__", quote(link)).replace("__DEST__", quote(destination))
        .replace("__DIR__", quote(target)).replace("__URL__", quote(origin)))
    assert not result["ok"]
    assert "E1" in result["error"]
    assert (real / ".git/config").read_bytes() == before
    assert not list(tmp_path.glob("student.incomplete-*"))
