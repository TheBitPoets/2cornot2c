"""Exercise the real PowerShell functions with an offline winget double."""

import base64
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from installer.plans import _winget_ensure


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("powershell.exe") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(not POWERSHELL, reason="PowerShell unavailable")


def run_powershell(body: str) -> dict:
    # Load definitions only: never execute the bootstrap's installation body.
    source = str(ROOT / "scripts/bootstrap-classroom-windows.ps1").replace("'", "''")
    script = r"""
$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    '__SOURCE__', [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Bootstrap syntax error' }
$wanted = @('Install-WingetPackage', 'Update-WingetPackage', 'Stop-WingetFailure')
$definitions = $ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -in $wanted
}, $true)
foreach ($definition in $definitions) {
    . ([scriptblock]::Create($definition.Extent.Text))
}
$InstalledByBootstrap = [System.Collections.Generic.List[string]]::new()
$script:saveCount = 0
$script:calls = [System.Collections.Generic.List[object]]::new()
$script:failure = $null
$script:forcedCode = 0
function Save-BootstrapState { $script:saveCount++ }
function Stop-WithMessage {
    param($Code, $Title, $Explanation, $Actions, $Technical)
    $script:failure = @{code=$Code; title=$Title; explanation=$Explanation;
        actions=$Actions; technical=$Technical}
    throw 'expected-stop'
}
function winget {
    $script:calls.Add(@($args))
    $position = [array]::IndexOf($args, '--source')
    # Model a broken msstore source; the requested package exists in winget.
    $global:LASTEXITCODE = if ($position -lt 0 -or
        $args[$position + 1] -ne 'winget') { -1978335138 } else { $script:forcedCode }
}
try {
__BODY__
} catch {
    if ($_.Exception.Message -ne 'expected-stop') { throw }
} finally {
    @{calls=@($script:calls.ToArray()); owned=@($InstalledByBootstrap.ToArray());
      saves=$script:saveCount; failure=$script:failure} | ConvertTo-Json -Depth 8 -Compress
}
""".replace("__SOURCE__", source).replace("__BODY__", body)
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("package", ["Git.Git", "Python.Python.3.12", "zyedidia.micro"])
def test_install_ignores_broken_msstore_and_tracks_success_once(package):
    result = run_powershell(f"Install-WingetPackage '{package}'\nInstall-WingetPackage '{package}'")
    assert result["failure"] is None
    assert len(result["calls"]) == 2
    assert result["owned"] == [package]
    assert result["saves"] == 2
    for call in result["calls"]:
        assert call[call.index("--source") + 1] == "winget"
        assert call[call.index("--id") + 1] == package


def test_upgrade_selects_source_without_claiming_preexisting_package():
    result = run_powershell("Update-WingetPackage 'Git.Git'")
    assert result["failure"] is None
    assert result["owned"] == []
    assert result["saves"] == 1
    assert result["calls"][0][0] == "upgrade"


@pytest.mark.parametrize("action", ["Install", "Update"])
@pytest.mark.parametrize("code, reason", [
    (-1978335138, "certificato"), (-2147012894, "tempo"), (1603, "winget"),
])
def test_real_source_or_installer_failure_is_reported_and_not_saved(action, code, reason):
    result = run_powershell(
        f"$script:forcedCode = {code}\n{action}-WingetPackage 'Git.Git'"
    )
    assert len(result["calls"]) == 1
    assert result["failure"]["code"] == "E09"
    assert reason in result["failure"]["explanation"].lower()
    assert str(code) in result["failure"]["technical"]
    assert "source winget" in result["failure"]["technical"]
    assert result["owned"] == []
    assert result["saves"] == 0


@pytest.mark.parametrize("package", [
    "Git.Git", "Hashicorp.Vagrant", "Oracle.VirtualBox", "Docker.DockerDesktop",
])
@pytest.mark.parametrize("upgrade_succeeds", [False, True])
def test_tui_plan_pins_source_for_upgrade_and_install(package, upgrade_succeeds):
    command = _winget_ensure(package)[-1]
    # Execute the exact plan, including exit; the harness records calls in finally.
    setup = """
$script:upgradeSucceeds = __SUCCESS__
function winget {
    $script:calls.Add(@($args))
    $position = [array]::IndexOf($args, '--source')
    if ($position -lt 0 -or $args[$position + 1] -ne 'winget') {
        throw 'unexpected msstore lookup'
    }
    $global:LASTEXITCODE = if ($args[0] -eq 'upgrade' -and
        -not $script:upgradeSucceeds) { 1 } else { 0 }
}
""".replace("__SUCCESS__", "$true" if upgrade_succeeds else "$false")
    result = run_powershell(setup + "\n& { " + command + " }")
    assert [call[0] for call in result["calls"]] == (
        ["upgrade"] if upgrade_succeeds else ["upgrade", "install"]
    )
