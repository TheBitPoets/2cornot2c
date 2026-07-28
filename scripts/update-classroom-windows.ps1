$ErrorActionPreference = "Stop"

$BootstrapUrl = if ($env:CLASSROOM_BOOTSTRAP_URL) {
    $env:CLASSROOM_BOOTSTRAP_URL
} else {
    "https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/bootstrap-classroom-windows.ps1"
}

Write-Host "Aggiornamento ambiente didattico 2cornot2c"
Write-Host "La procedura conserva esercizi e configurazioni locali."

try {
    $Bootstrap = Invoke-RestMethod -TimeoutSec 30 $BootstrapUrl
} catch {
    Write-Host "ERRORE: impossibile scaricare il bootstrap aggiornato." `
        -ForegroundColor Red
    exit 1
}

& ([ScriptBlock]::Create([string]$Bootstrap))
