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
    param(
        [string]$Code,
        [string]$Title,
        [string]$Explanation,
        [string[]]$Actions = @(),
        [string]$Technical = ""
    )
    Write-Host ""
    Write-Host "ERRORE $Code - $Title" -ForegroundColor Red
    Write-Host ""
    Write-Host "COSA SIGNIFICA" -ForegroundColor Yellow
    Write-Host $Explanation -ForegroundColor Yellow
    if ($Actions.Count -gt 0) {
        Write-Host ""
        Write-Host "COSA DEVI FARE" -ForegroundColor Yellow
        for ($Index = 0; $Index -lt $Actions.Count; $Index++) {
            Write-Host "$($Index + 1). $($Actions[$Index])" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    Write-Host "Se chiedi aiuto, comunica questo codice: $Code" -ForegroundColor Yellow
    if ($Technical) {
        Write-Host "Dettagli tecnici: $Technical" -ForegroundColor DarkGray
    }
    exit 1
}

function Install-WingetPackage {
    param([string]$Id)
    winget install --id $Id --exact --silent `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "E09" "Installazione di $Id non riuscita" `
            "Windows ha interrotto o rifiutato l'installazione. Non devi ricominciare da zero." `
            @(
                "Controlla se Windows aspetta una conferma e scegli Sì."
                "Rilancia lo stesso comando: i componenti presenti saranno saltati."
                "Se ricompare, comunica E09 al docente."
            ) "winget exit code $LASTEXITCODE"
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

function Install-ClassroomLauncher {
    $LauncherDir = Join-Path $env:LOCALAPPDATA "2cornot2c"
    New-Item -ItemType Directory -Force -Path $LauncherDir | Out-Null
    foreach ($ScriptName in @(
        "manage-classroom-windows.ps1"
        "prepare-wsl-windows.ps1"
        "remove-wsl-windows.ps1"
        "update-classroom-windows.ps1"
        "uninstall-classroom-windows.ps1"
    )) {
        Copy-Item -Force `
            (Join-Path $InstallDir "scripts\$ScriptName") `
            (Join-Path $LauncherDir $ScriptName)
    }

    $PowerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $Manager = Join-Path $LauncherDir "manage-classroom-windows.ps1"
    $ShortcutTargets = @(
        (Join-Path ([Environment]::GetFolderPath("Desktop")) "Ambiente 2cornot2c.lnk")
        (Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Ambiente 2cornot2c.lnk")
    )
    $Shell = New-Object -ComObject WScript.Shell
    foreach ($ShortcutPath in $ShortcutTargets) {
        $Shortcut = $Shell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $PowerShell
        $Shortcut.Arguments = (
            "-NoProfile -ExecutionPolicy Bypass -File `"$Manager`""
        )
        $Shortcut.WorkingDirectory = $LauncherDir
        $Shortcut.Description = "Installa e gestisci l'ambiente 2cornot2c"
        $Shortcut.Save()
    }
}

function Test-HostResources {
    try {
        $Computer = Get-CimInstance Win32_ComputerSystem
        $MemoryGiB = [math]::Round(
            [double]$Computer.TotalPhysicalMemory / 1GB,
            1
        )
    } catch {
        Stop-WithMessage "E06" "Non riesco a controllare la memoria del computer" `
            "Windows non ha permesso alla procedura di leggere la RAM. Non è stato modificato nulla." `
            @(
                "Chiudi PowerShell e riaprilo."
                "Rilancia lo stesso comando."
                "Se ricompare, comunica E06 al docente."
            ) $_.Exception.Message
    }
    if ($MemoryGiB -lt 4) {
        Stop-WithMessage "E02" "Il computer non ha abbastanza memoria RAM" `
            "La RAM è lo spazio di lavoro temporaneo del computer. Docker richiede almeno 4 GiB." `
            @(
                "Chiudi gli altri programmi e riprova."
                "Se l'errore rimane, comunica E02 al docente."
            ) "RAM trovata: $MemoryGiB GiB; necessaria: 4 GiB"
    }

    $FullInstallDir = [IO.Path]::GetFullPath($InstallDir)
    $DriveRoot = [IO.Path]::GetPathRoot($FullInstallDir)
    $DriveName = $DriveRoot.TrimEnd('\').TrimEnd(':')
    $Drive = Get-PSDrive -Name $DriveName
    $FreeGiB = [math]::Round([double]$Drive.Free / 1GB, 1)
    if ($FreeGiB -lt 3) {
        Stop-WithMessage "E05" "Non c'è abbastanza spazio libero sul disco" `
            "Il disco conserva programmi ed esercizi. Per iniziare servono almeno 3 GiB liberi; Docker ne richiederà 8 e una VM 20." `
            @(
                "Svuota il Cestino o sposta file personali su un altro disco."
                "Non cancellare file che non riconosci."
                "Rilancia il comando."
            ) "Spazio disponibile: $FreeGiB GiB; necessario ora: 3 GiB"
    }

    try {
        $Processor = Get-CimInstance Win32_Processor | Select-Object -First 1
        $Virtualization = $Processor.VirtualizationFirmwareEnabled
        if ($Computer.HypervisorPresent -eq $true) {
            Write-Host "Virtualizzazione: disponibile (hypervisor Windows attivo)."
        } elseif ($Virtualization -eq $false) {
            Write-Host (
                "AVVISO W03 - Windows fornisce indicazioni contrastanti " +
                "sulla virtualizzazione."
            ) -ForegroundColor Yellow
            Write-Host (
                "Il controllo automatico non è abbastanza affidabile per " +
                "fermare l'installazione."
            ) -ForegroundColor Yellow
            Write-Host (
                "Se Gestione attività, Prestazioni, CPU mostra Abilitata, " +
                "puoi continuare."
            ) -ForegroundColor Yellow
        }
    } catch {
        Write-Host "AVVISO W04 - Virtualizzazione non verificabile automaticamente." `
            -ForegroundColor Yellow
        Write-Host "Puoi continuare. Se Docker non parte, comunica W04 al docente." `
            -ForegroundColor Yellow
    }

    try {
        Invoke-WebRequest -UseBasicParsing -Method Head -TimeoutSec 15 `
            "https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/README.md" |
            Out-Null
    } catch {
        Stop-WithMessage "E07" "Non riesco a collegarmi al server di download" `
            "La procedura ha bisogno di Internet. L'antivirus o la rete potrebbero bloccare GitHub." `
            @(
                "Controlla con il browser che Internet funzioni."
                "Non disattivare l'antivirus."
                "Riprova; se ricompare, comunica E07 al docente."
            ) $_.Exception.Message
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
    Stop-WithMessage "E01" "Serve Windows 10 o Windows 11 a 64 bit" `
        "Questo computer usa una versione di Windows non compatibile. Non hai sbagliato nulla." `
        @(
            "Apri Impostazioni, Sistema, Informazioni."
            "Fai una foto della voce Tipo sistema e mostrala al docente."
        )
}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "E08" "Il programma di installazione di Windows non è disponibile" `
        "winget è lo strumento ufficiale che Windows usa per installare le applicazioni." `
        @(
            "Apri Microsoft Store."
            "Cerca App Installer di Microsoft e installalo o aggiornalo."
            "Chiudi e riapri PowerShell, poi rilancia il comando."
        )
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
    Stop-WithMessage "E10" "Git è installato ma Windows non riesce ancora a trovarlo" `
        "A volte Windows riconosce un nuovo programma solamente dopo un riavvio." `
        @("Riavvia Windows."; "Riapri PowerShell e rilancia lo stesso comando.")
}
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "E10" "Python è installato ma Windows non riesce ancora a trovarlo" `
        "A volte Windows riconosce un nuovo programma solamente dopo un riavvio." `
        @("Riavvia Windows."; "Riapri PowerShell e rilancia lo stesso comando.")
}

Write-Host "[2/4] Preparazione repository..."
if (Test-Path (Join-Path $InstallDir ".git")) {
    git -C $InstallDir pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "E13" "Non posso aggiornare il progetto in sicurezza" `
            "La rete potrebbe essere assente oppure alcuni file potrebbero essere stati modificati. Ho fermato tutto per non perdere il tuo lavoro." `
            @(
                "Non cancellare la cartella e non usare comandi Git trovati su Internet."
                "Controlla Internet."
                "Se l'errore rimane, comunica E13 al docente."
            ) "git pull exit code $LASTEXITCODE"
    }
} elseif (Test-Path $InstallDir) {
    Stop-WithMessage "E11" "La cartella 2cornot2c è già occupata" `
        "La cartella esiste ma non contiene il nostro ambiente. Per sicurezza non verrà modificata o cancellata." `
        @(
            "Rinomina la cartella in 2cornot2c-vecchia oppure chiedi al docente di controllarla."
            "Rilancia il comando."
        ) $InstallDir
} else {
    git clone $RepositoryUrl $InstallDir
    if ($LASTEXITCODE -ne 0) {
        Stop-WithMessage "E12" "Non sono riuscito a scaricare l'ambiente 2cornot2c" `
            "Il download è stato interrotto. Non cancellare manualmente una cartella rimasta incompleta." `
            @(
                "Controlla Internet e riprova."
                "Se ricompare, comunica E12 al docente."
            ) "git clone exit code $LASTEXITCODE"
    }
}

Install-ClassroomLauncher

Write-Host "[3/4] Preparazione interfaccia guidata..."
$VenvDir = Join-Path $InstallDir ".installer-venv"
& py -3.12 -m venv $VenvDir
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "E14" "Non sono riuscito a preparare l'interfaccia guidata" `
        "Il progetto è stato scaricato, ma Python non ha preparato il menu. Il lavoro già svolto non è andato perso." `
        @("Riavvia Windows."; "Rilancia lo stesso comando."; "Se ricompare, comunica E14 al docente.") `
        "venv exit code $LASTEXITCODE"
}
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
& $VenvPython -m pip install --disable-pip-version-check `
    -r (Join-Path $InstallDir "requirements-utui.txt")
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "E15" "Non sono riuscito a installare il menu guidato" `
        "Python funziona, ma non ha scaricato un componente del menu." `
        @(
            "Controlla Internet."
            "Rilancia lo stesso comando."
            "Se ricompare, comunica E15 al docente."
        ) "pip exit code $LASTEXITCODE"
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
