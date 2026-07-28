$ErrorActionPreference = "Stop"

$RepositoryUrl = if ($env:CLASSROOM_REPOSITORY_URL) {
    $env:CLASSROOM_REPOSITORY_URL
} else {
    "https://github.com/TheBitPoets/2cornot2c.git"
}
$InstallDir = if ($env:CLASSROOM_INSTALL_DIR) {
    $env:CLASSROOM_INSTALL_DIR
} else {
    Join-Path $HOME "2cornot2c"
}
$StateDir = Join-Path $HOME ".2cornot2c"
$StatePath = Join-Path $StateDir "bootstrap-state.json"
$InstalledByBootstrap = [System.Collections.Generic.List[string]]::new()

if (Test-Path $StatePath) {
    try {
        $PreviousState = Get-Content $StatePath -Raw | ConvertFrom-Json
        foreach ($PackageId in $PreviousState.installed_by_bootstrap) {
            $InstalledByBootstrap.Add([string]$PackageId)
        }
    } catch {
        Write-Warning "Registro precedente non leggibile: $StatePath"
    }
}

function Stop-WithMessage {
    param([string]$Message)
    Write-Host ""
    Write-Host "ERRORE: $Message" -ForegroundColor Red
    exit 1
}

function Install-WingetPackage {
    param([string]$Id)
    winget install --id $Id --exact --silent `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Installazione non riuscita: $Id"
    }
    if (-not $InstalledByBootstrap.Contains($Id)) {
        $InstalledByBootstrap.Add($Id)
    }
    Save-BootstrapState
}

function Save-BootstrapState {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
    $TemporaryPath = "$StatePath.tmp"
    [ordered]@{
        schema_version = "2cornot2c.windows-bootstrap.v1"
        install_dir = $InstallDir
        installed_by_bootstrap = @($InstalledByBootstrap)
        updated_at = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json | Set-Content -Encoding UTF8 $TemporaryPath
    Move-Item -Force $TemporaryPath $StatePath
}

function Test-HostResources {
    try {
        $Computer = Get-CimInstance Win32_ComputerSystem
        $MemoryGiB = [math]::Round(
            [double]$Computer.TotalPhysicalMemory / 1GB,
            1
        )
    } catch {
        Stop-WithMessage "Impossibile misurare la RAM: $($_.Exception.Message)"
    }
    if ($MemoryGiB -lt 4) {
        Stop-WithMessage "RAM insufficiente: $MemoryGiB GiB; minimo 4 GiB."
    }

    $FullInstallDir = [IO.Path]::GetFullPath($InstallDir)
    $DriveRoot = [IO.Path]::GetPathRoot($FullInstallDir)
    $DriveName = $DriveRoot.TrimEnd('\').TrimEnd(':')
    $Drive = Get-PSDrive -Name $DriveName
    $FreeGiB = [math]::Round([double]$Drive.Free / 1GB, 1)
    if ($FreeGiB -lt 3) {
        Stop-WithMessage (
            "Spazio insufficiente per il bootstrap: $FreeGiB GiB; minimo 3 GiB."
        )
    }

    try {
        $Virtualization = Get-CimInstance Win32_Processor |
            Select-Object -First 1 -ExpandProperty VirtualizationFirmwareEnabled
        if ($Virtualization -eq $false) {
            Stop-WithMessage (
                "Virtualizzazione hardware disabilitata. Abilitala nel BIOS/UEFI."
            )
        }
    } catch {
        Write-Warning "Virtualizzazione non verificabile automaticamente."
    }

    try {
        Invoke-WebRequest -UseBasicParsing -Method Head -TimeoutSec 15 `
            "https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/README.md" |
            Out-Null
    } catch {
        Stop-WithMessage "GitHub non raggiungibile. Controlla la connessione."
    }

    Write-Host "RAM: $MemoryGiB GiB"
    Write-Host "Disco libero: $FreeGiB GiB"
    if ($MemoryGiB -le 8) {
        Write-Host "Raccomandazione: Docker leggero (richiede almeno 8 GiB liberi)."
    } else {
        Write-Host "VM completa disponibile con almeno 20 GiB liberi."
    }
}

if (-not [Environment]::Is64BitOperatingSystem) {
    Stop-WithMessage "È richiesto Windows 10/11 a 64 bit."
}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "Windows Package Manager (winget) non è disponibile."
}

Write-Host "Bootstrap ambiente didattico 2cornot2c"
Write-Host "Directory: $InstallDir"
Write-Host "[0/4] Controllo risorse..."
Test-HostResources

Write-Host "[1/4] Preparazione Git e Python 3.12..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "Git.Git"
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "Python.Python.3.12"
}

$env:Path = @(
    "$env:ProgramFiles\Git\cmd"
    "$env:LOCALAPPDATA\Programs\Python\Launcher"
    "$env:LOCALAPPDATA\Programs\Python\Python312"
    "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
    $env:Path
) -join [IO.Path]::PathSeparator

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "Git non è disponibile. Riavvia Windows e riprova."
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "Python Launcher non è disponibile. Riavvia Windows e riprova."
}

Write-Host "[2/4] Preparazione repository..."
if (Test-Path (Join-Path $InstallDir ".git")) {
    git -C $InstallDir pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Aggiornamento repository non riuscito."
    }
} elseif (Test-Path $InstallDir) {
    Stop-WithMessage "La directory esiste ma non è un repository Git: $InstallDir"
} else {
    git clone $RepositoryUrl $InstallDir
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "Clone repository non riuscito."
    }
}

Write-Host "[3/4] Preparazione interfaccia guidata..."
$VenvDir = Join-Path $InstallDir ".installer-venv"
& py -3.12 -m venv $VenvDir
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Creazione ambiente Python non riuscita."
}
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
& $VenvPython -m pip install --disable-pip-version-check `
    -r (Join-Path $InstallDir "requirements-utui.txt")
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Installazione uTUI non riuscita."
}

Write-Host "[4/4] Avvio procedura guidata..."
Push-Location $InstallDir
try {
    & $VenvPython -m installer.tui
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
