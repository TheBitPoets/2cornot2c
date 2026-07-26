$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectDir

function Stop-WithMessage {
    param([string]$Message)
    Write-Host ""
    Write-Host "ERRORE: $Message" -ForegroundColor Red
    exit 1
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Il comando '$Command $($Arguments -join ' ')' non è riuscito."
    }
}

try {
    if (-not (Get-Command vagrant -ErrorAction SilentlyContinue)) {
        Stop-WithMessage "Vagrant non è installato o non è disponibile nel PATH."
    }
    if (-not (Get-Command VBoxManage -ErrorAction SilentlyContinue)) {
        Stop-WithMessage "VirtualBox non è installato o non è disponibile nel PATH. Riavvia Windows dopo l'installazione."
    }

    Write-Host "Controllo della configurazione..."
    Invoke-Checked "vagrant" @("validate")

    Write-Host ""
    Write-Host "Avvio dell'ambiente didattico (il primo avvio può richiedere alcuni minuti)..."
    Invoke-Checked "vagrant" @("up", "--provider=virtualbox")

    $HealthCheck = @'
set -eu
command -v gcc >/dev/null
command -v gdb >/dev/null
systemctl is-active --quiet vboxadd-service
findmnt -rn /lab >/dev/null
findmnt -rn /lab2 >/dev/null
'@

    Write-Host ""
    Write-Host "Controllo automatico della macchina..."
    & vagrant ssh -c $HealthCheck
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Primo controllo non riuscito: provo un riavvio automatico..."
        Invoke-Checked "vagrant" @("reload")
        & vagrant ssh -c $HealthCheck
        if ($LASTEXITCODE -ne 0) {
            Stop-WithMessage "La macchina è avviata, ma il controllo finale non è riuscito. Comunica questo messaggio al docente."
        }
    }

    Write-Host ""
    Write-Host "AMBIENTE PRONTO." -ForegroundColor Green
    Write-Host "La finestra grafica si apre automaticamente. Per il terminale usa: vagrant ssh"
}
finally {
    Pop-Location
}
