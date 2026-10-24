param(
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

if ($Resume) {
    $env:CLASSROOM_AUTO_RESUME = "1"
}

$StatePath = Join-Path $HOME ".2cornot2c\bootstrap-state.json"
$DefaultInstallDir = Join-Path $HOME "2cornot2c"
$BootstrapUrl = if ($env:CLASSROOM_BOOTSTRAP_URL) {
    $env:CLASSROOM_BOOTSTRAP_URL
} else {
    "https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/bootstrap-classroom-windows.ps1"
}

$InstallDir = $DefaultInstallDir
if (Test-Path $StatePath) {
    try {
        $SavedInstallDir = [string](
            Get-Content $StatePath -Raw | ConvertFrom-Json
        ).install_dir
        if ($SavedInstallDir) {
            $InstallDir = $SavedInstallDir
        }
    } catch {
        Write-Warning "Configurazione precedente non leggibile."
    }
}

$VenvPython = Join-Path $InstallDir ".installer-venv\Scripts\python.exe"
$PythonReady = $false
if ((Test-Path (Join-Path $InstallDir ".git")) -and
    (Test-Path $VenvPython)) {
    # A venv launcher survives removal of its base Python installation.
    try {
        & $VenvPython -I -c 'pass' *> $null
        $PythonReady = $LASTEXITCODE -eq 0
    } catch {
        $PythonReady = $false
    }
}
if ($PythonReady) {
    Push-Location $InstallDir
    try {
        & $VenvPython -m installer.tui
        exit $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

Write-Host "L'ambiente non è ancora completo."
$SelectiveUninstaller = Join-Path $env:LOCALAPPDATA '2cornot2c\uninstall-classroom-windows.ps1'
if ((Test-Path -LiteralPath $StatePath) -and (Test-Path -LiteralPath $SelectiveUninstaller)) {
    Write-Host '1. Installa, completa o ripara'
    Write-Host '2. Disinstalla: scegli i componenti rimasti'
    Write-Host '0. Esci senza modifiche'
    $Choice = Read-Host 'Scegli una voce'
    if ($Choice -eq '2') {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $SelectiveUninstaller -SelectComponents
        exit $LASTEXITCODE
    }
    if ($Choice -ne '1') { exit 2 }
}
Write-Host "Avvio automaticamente la preparazione guidata..."
try {
    $Bootstrap = Invoke-RestMethod -TimeoutSec 30 $BootstrapUrl
} catch {
    Write-Host "ERRORE E25 - Non riesco a scaricare la preparazione" `
        -ForegroundColor Red
    Write-Host "COSA SIGNIFICA" -ForegroundColor Yellow
    Write-Host "Internet non è disponibile oppure GitHub non risponde." `
        -ForegroundColor Yellow
    Write-Host "COSA DEVI FARE" -ForegroundColor Yellow
    Write-Host "1. Controlla Internet e fai doppio clic di nuovo sul collegamento." `
        -ForegroundColor Yellow
    Write-Host "2. Se ricompare, comunica E25 al docente." `
        -ForegroundColor Yellow
    Read-Host "Premi Invio per chiudere"
    exit 1
}

& ([ScriptBlock]::Create([string]$Bootstrap))
