$ErrorActionPreference = "Stop"

$StateDir = Join-Path $HOME ".2cornot2c"
$StatePath = Join-Path $StateDir "bootstrap-state.json"
$ProviderPath = Join-Path $StateDir "selected-provider.txt"
$InstallDir = Join-Path $HOME "2cornot2c"
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

if (-not (Test-Path $ProviderPath)) {
    Write-Host "AMBIENTE NON ANCORA PRONTO" -ForegroundColor Yellow
    Write-Host (
        "Apri Ambiente 2cornot2c e scegli Installa, completa o ripara."
    ) -ForegroundColor Yellow
    Read-Host "Premi Invio per chiudere"
    exit 1
}

$Provider = (Get-Content $ProviderPath -Raw).Trim()
Push-Location $InstallDir
try {
    if ($Provider -eq "docker") {
        $Python = Join-Path $InstallDir ".installer-venv\Scripts\python.exe"
        & $Python (Join-Path $InstallDir "scripts\student_dev_shell.py")
        exit $LASTEXITCODE
    }
    if ($Provider -eq "virtualbox") {
        & vagrant up --provider=virtualbox
        exit $LASTEXITCODE
    }
    Write-Host "ERRORE E31 - Ambiente da avviare non riconosciuto" `
        -ForegroundColor Red
    Write-Host "COSA SIGNIFICA" -ForegroundColor Yellow
    Write-Host "La configurazione salvata non è valida." -ForegroundColor Yellow
    Write-Host "COSA DEVI FARE" -ForegroundColor Yellow
    Write-Host (
        "Apri Ambiente 2cornot2c e scegli Installa, completa o ripara."
    ) -ForegroundColor Yellow
    Read-Host "Premi Invio per chiudere"
    exit 1
} finally {
    Pop-Location
}
