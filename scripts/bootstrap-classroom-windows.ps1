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
}

if (-not [Environment]::Is64BitOperatingSystem) {
    Stop-WithMessage "È richiesto Windows 10/11 a 64 bit."
}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "Windows Package Manager (winget) non è disponibile."
}

Write-Host "Bootstrap ambiente didattico 2cornot2c"
Write-Host "Directory: $InstallDir"

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
