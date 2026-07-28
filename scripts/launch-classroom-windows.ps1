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

function Find-ExistingProvider {
    $LogPath = Join-Path $StateDir "installer.jsonl"
    if (Test-Path $LogPath) {
        $Lines = @(Get-Content $LogPath)
        [array]::Reverse($Lines)
        foreach ($Line in $Lines) {
            try {
                $Record = $Line | ConvertFrom-Json
                if ($Record.host -eq "windows-amd64" -and
                    $Record.provider -eq "docker" -and
                    $Record.key -eq "student-image" -and
                    $Record.status -in @("succeeded", "skipped")) {
                    return "docker"
                }
            } catch {
                continue
            }
        }
    }

    $DockerCommand = Get-Command docker -ErrorAction SilentlyContinue
    $DockerExecutable = if ($DockerCommand) {
        $DockerCommand.Source
    } else {
        $null
    }
    if (-not $DockerExecutable) {
        $DockerPath = Join-Path $env:ProgramFiles `
            "Docker\Docker\resources\bin\docker.exe"
        if (Test-Path $DockerPath) {
            $DockerExecutable = $DockerPath
        }
    }
    $LockPath = Join-Path $InstallDir `
        "docker\student-dev\toolchain.lock.json"
    if ($DockerExecutable -and (Test-Path $LockPath)) {
        try {
            $Lock = Get-Content $LockPath -Raw | ConvertFrom-Json
            $Image = "$($Lock.image_repository)@$($Lock.digest)"
            & $DockerExecutable info *> $null
            if ($LASTEXITCODE -eq 0) {
                & $DockerExecutable image inspect $Image *> $null
                if ($LASTEXITCODE -eq 0) {
                    return "docker"
                }
            }
        } catch {
            Write-Warning "Ambiente Docker precedente non verificabile."
        }
    }

    if (Test-Path (Join-Path $InstallDir ".vagrant")) {
        return "virtualbox"
    }
    return $null
}

if (-not (Test-Path $ProviderPath)) {
    $ExistingProvider = Find-ExistingProvider
    if ($ExistingProvider) {
        New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
        Set-Content -Encoding UTF8 $ProviderPath $ExistingProvider
        Write-Host (
            "Ambiente precedente riconosciuto: $ExistingProvider."
        ) -ForegroundColor Green
    } else {
        Write-Host "AMBIENTE NON ANCORA PRONTO" -ForegroundColor Yellow
        Write-Host (
            "Apri Ambiente 2cornot2c e scegli Installa, completa o ripara."
        ) -ForegroundColor Yellow
        Read-Host "Premi Invio per chiudere"
        exit 1
    }
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
