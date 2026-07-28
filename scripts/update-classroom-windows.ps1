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
    Write-Host "ERRORE E25 - Non riesco a scaricare l'aggiornamento" `
        -ForegroundColor Red
    Write-Host "COSA SIGNIFICA" -ForegroundColor Yellow
    Write-Host (
        "Il collegamento è stato interrotto. L'ambiente già installato " +
        "non è stato modificato e puoi continuare a usarlo."
    ) -ForegroundColor Yellow
    Write-Host "COSA DEVI FARE" -ForegroundColor Yellow
    Write-Host "1. Controlla con il browser che Internet funzioni." `
        -ForegroundColor Yellow
    Write-Host "2. Riprova più tardi." -ForegroundColor Yellow
    Write-Host "3. Se ricompare, comunica E25 al docente." `
        -ForegroundColor Yellow
    Write-Host "Dettagli tecnici: $($_.Exception.Message)" `
        -ForegroundColor DarkGray
    exit 1
}

& ([ScriptBlock]::Create([string]$Bootstrap))
