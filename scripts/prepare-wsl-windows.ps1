param(
    [switch]$Elevated,
    [string]$DiagnosticPath
)

$ErrorActionPreference = "Stop"

function Invoke-WslInstall {
    param([string]$LogPath)
    $Result = @{ phase = 'wsl-install'; exit_code = 1; output = '' }
    $PreviousPreference = $ErrorActionPreference
    try {
        # Capture native stderr without turning it into a terminating error.
        $ErrorActionPreference = 'Continue'
        $Output = @(& wsl.exe --install --no-distribution 2>&1)
        $Result.exit_code = $LASTEXITCODE
        $Result.output = ($Output | Out-String).Replace([string][char]0, '').Trim()
    } catch {
        $Result.output = $_.Exception.Message
    } finally {
        $ErrorActionPreference = $PreviousPreference
    }
    if ($Result.output.Length -gt 2400) {
        $Result.output = $Result.output.Substring(0, 2400)
    }
    $Result | ConvertTo-Json | Set-Content -LiteralPath $LogPath -Encoding UTF8
    if ($Result.exit_code -in @(0, 3010)) { return 0 }
    return 1
}

function Invoke-WslSetup {
    param([string]$ScriptPath)
    $PowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $LogDirectory = Join-Path $env:LOCALAPPDATA '2cornot2c\diagnostics'
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
    $LogPath = Join-Path $LogDirectory ("wsl-" + [guid]::NewGuid().ToString('N') + '.json')
    $Arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        "`"$ScriptPath`"", '-Elevated', '-DiagnosticPath', "`"$LogPath`"")
    Write-Host 'Windows mostrerà una richiesta di autorizzazione.'
    try {
        $Process = Start-Process -FilePath $PowerShell -ArgumentList $Arguments `
            -Verb RunAs -WindowStyle Hidden -Wait -PassThru
    } catch {
        if ($_.Exception.NativeErrorCode -eq 1223) {
            Write-Host 'WSL_UAC_CANCELLED: autorizzazione annullata. Riprova e autorizza la richiesta di Windows.'
        } else {
            Write-Host ("WSL_ELEVATION_FAILED: " + $_.Exception.Message)
        }
        return 1
    }
    try {
        $Result = Get-Content -LiteralPath $LogPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -eq $Result.exit_code -or $Result.phase -ne 'wsl-install') {
            throw 'Resoconto WSL incompleto.'
        }
    } catch {
        Write-Host "WSL_REPORT_MISSING: processo exit code $($Process.ExitCode); log: $LogPath"
        return 1
    }
    if ($Process.ExitCode -ne 0 -or $Result.exit_code -notin @(0, 3010)) {
        Write-Host "WSL_INSTALL_FAILED: fase $($Result.phase); exit code $($Result.exit_code); log: $LogPath"
        Write-Host $Result.output
        return 1
    }
    $Manager = Join-Path $env:LOCALAPPDATA '2cornot2c\manage-classroom-windows.ps1'
    $RunOnceCommand = "`"$PowerShell`" -NoProfile -ExecutionPolicy Bypass -File `"$Manager`" -Resume"
    try {
        New-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce' `
            -Name '2cornot2c-resume' -Value $RunOnceCommand -PropertyType String -Force | Out-Null
    } catch {
        Write-Host ("WSL_RESUME_FAILED: WSL preparato; impossibile registrare la ripresa: " + $_.Exception.Message)
        Write-Host 'Riavvia Windows e riapri Ambiente 2cornot2c dal collegamento sul desktop.'
        return 1
    }
    Write-Host "WSL 2 preparato. Riavvia Windows per continuare. Log: $LogPath"
    return 0
}

if ($Elevated) {
    if (-not $DiagnosticPath) { throw 'Percorso diagnostico WSL assente.' }
    exit (Invoke-WslInstall -LogPath $DiagnosticPath)
}
exit (Invoke-WslSetup -ScriptPath $PSCommandPath)
