param(
    [switch]$Elevated
)

$ErrorActionPreference = "Stop"

if ($Elevated) {
    Write-Host "Preparazione di WSL 2 e Virtual Machine Platform..."
    & wsl.exe --install --no-distribution
    if ($LASTEXITCODE -notin @(0, 3010)) {
        Write-Error "wsl --install non riuscito: exit code $LASTEXITCODE"
        exit 1
    }
    exit 0
}

$PowerShell = Join-Path `
    $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$Arguments = @(
    "-NoProfile"
    "-ExecutionPolicy"
    "Bypass"
    "-File"
    "`"$PSCommandPath`""
    "-Elevated"
)

Write-Host "Windows mostrerà una richiesta di autorizzazione."
$Process = Start-Process `
    -FilePath $PowerShell `
    -ArgumentList $Arguments `
    -Verb RunAs `
    -Wait `
    -PassThru
if ($Process.ExitCode -ne 0) {
    Write-Error "Preparazione WSL 2 non riuscita o non autorizzata."
    exit 1
}

$Manager = Join-Path $env:LOCALAPPDATA `
    "2cornot2c\manage-classroom-windows.ps1"
$RunOncePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
$RunOnceCommand = (
    "`"$PowerShell`" -NoProfile -ExecutionPolicy Bypass " +
    "-File `"$Manager`" -Resume"
)
New-ItemProperty `
    -Path $RunOncePath `
    -Name "2cornot2c-resume" `
    -Value $RunOnceCommand `
    -PropertyType String `
    -Force | Out-Null

Write-Host "WSL 2 preparato. Riavvia Windows per continuare."
