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

function Stop-WingetFailure {
    param([string]$Title, [int]$ExitCode)

    $Explanation = "winget non ha completato l'operazione. Il codice tecnico distingue la causa; non devi ricominciare da zero."
    $Actions = @(
        "Controlla se il programma di installazione mostra una richiesta da confermare."
        "Rilancia lo stesso comando: i componenti compatibili presenti saranno saltati."
        "Se ricompare, comunica E09 e il codice tecnico al docente."
    )
    if ($ExitCode -eq -1978335138) {
        $Explanation = "winget non ha potuto verificare il certificato di una sorgente. Non si tratta di un rifiuto dell'installazione da parte di Windows."
        $Actions = @(
            "Chiedi al docente di verificare data e ora del PC e l'accesso alla sorgente winget."
            "Non disattivare la verifica dei certificati; riprova dopo il controllo."
            "Se ricompare, comunica E09 e il codice tecnico al docente."
        )
    } elseif ($ExitCode -eq -2147012894) {
        $Explanation = "winget ha superato il tempo di attesa della connessione alla sorgente o al server di download. Non devi ricominciare da zero."
        $Actions = @(
            "Controlla la connessione e riprova tra poco."
            "Se Internet funziona ma l'errore continua, chiedi al docente di verificare l'accesso ai server di download."
            "Comunica E09 e il codice tecnico; non devi ricominciare da zero."
        )
    }
    Stop-WithMessage "E09" $Title $Explanation $Actions `
        "winget exit code $ExitCode; source winget"
}

function Install-WingetPackage {
    param(
        [string]$Id,
        [bool]$TrackOwnership = $true
    )
    winget install --id $Id --exact --source winget --silent `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Stop-WingetFailure "Installazione di $Id non riuscita" $LASTEXITCODE
    }
    if ($TrackOwnership -and -not $InstalledByBootstrap.Contains($Id)) {
        $InstalledByBootstrap.Add($Id)
    }
    Save-BootstrapState
}

function Update-WingetPackage {
    param([string]$Id)
    winget upgrade --id $Id --exact --source winget --silent `
        --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Stop-WingetFailure "Aggiornamento di $Id non riuscito" $LASTEXITCODE
    }
    Save-BootstrapState
}

function Test-GitMinimumVersion {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return $false
    }
    $Output = [string](& git --version)
    if ($Output -notmatch "(\d+\.\d+(?:\.\d+)?)") {
        return $false
    }
    return [version]$Matches[1] -ge [version]"2.30.0"
}

function Test-Python312 {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        return $false
    }
    $PreviousErrorAction = $ErrorActionPreference
    try {
        # Il launcher scrive su stderr quando la versione non è installata.
        # È un esito atteso della diagnosi e non deve interrompere il bootstrap.
        $ErrorActionPreference = "SilentlyContinue"
        & py -3.12 -c `
            "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))" `
            *> $null
        $ProbeExitCode = $LASTEXITCODE
    } catch {
        $ProbeExitCode = 1
    } finally {
        $ErrorActionPreference = $PreviousErrorAction
    }
    return $ProbeExitCode -eq 0
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
        "launch-classroom-windows.ps1"
        "prepare-wsl-windows.ps1"
        "remove-classroom-shortcuts-windows.ps1"
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

function Initialize-ClassroomRepository {
    param([string]$Directory, [string]$Url)
    $Target = [System.IO.Path]::GetFullPath($Directory).TrimEnd('\', '/')
    $Parent = Split-Path -Parent $Target
    if (-not $Parent -or $Target -eq [System.IO.Path]::GetPathRoot($Target).TrimEnd('\', '/')) {
        throw 'E11: la cartella del progetto non può essere la radice del disco.'
    }
    # Never move or populate a directory through a junction/symbolic link.
    $Ancestor = $Target
    while ($Ancestor) {
        if (Test-Path -LiteralPath $Ancestor) {
            $Item = Get-Item -LiteralPath $Ancestor -Force
            if ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw 'E11: percorso con collegamenti; chiedi al docente di verificarlo.'
            }
        }
        $Ancestor = Split-Path -Parent $Ancestor
    }
    $GitDirectory = Join-Path $Target '.git'
    $Clone = -not (Test-Path -LiteralPath $Target)
    if (-not $Clone) {
        $Children = @(Get-ChildItem -LiteralPath $Target -Force)
        if ($Children.Count -eq 0) {
            $Clone = $true
        } elseif (Test-Path -LiteralPath $GitDirectory -PathType Container) {
            if ((Get-Item -LiteralPath $GitDirectory -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw 'E13: metadati Git collegati altrove; chiedi al docente, cartella preservata.'
            }
            $Origin = & git -C $Target config --get remote.origin.url
            if ($LASTEXITCODE -ne 0 -or $Origin -cne $Url) {
                throw 'E13: origine Git diversa o assente; cartella preservata, chiedi al docente.'
            }
            if ($Children.Count -eq 1 -and $Children[0].Name -eq '.git') {
                if (@(Get-ChildItem -LiteralPath $GitDirectory -Filter '*.lock' -Recurse -Force).Count) {
                    throw 'E13: operazione Git in corso o interrotta; chiedi al docente, nessun file rimosso.'
                }
                $Backup = $Target + '.incomplete-' + [guid]::NewGuid().ToString('N')
                # Validate both absolute paths immediately before moving.
                if ([IO.Path]::GetFullPath($Backup) -ne $Backup -or
                    (Split-Path -Parent $Backup) -ne $Parent -or
                    (Test-Path -LiteralPath $Backup)) {
                    throw 'E13: impossibile creare una copia di sicurezza del checkout.'
                }
                Move-Item -LiteralPath $Target -Destination $Backup -ErrorAction Stop
                Write-Host "Checkout incompleto conservato in: $Backup"
                $Clone = $true
            } else {
                & git -C $Target rev-parse --verify HEAD
                if ($LASTEXITCODE -ne 0) {
                    throw 'E13: checkout incompleto con file presenti; chiedi al docente, file preservati.'
                }
                & git -C $Target pull --ff-only
                if ($LASTEXITCODE -ne 0) {
                    throw "E13: aggiornamento non riuscito (exit code $LASTEXITCODE). Controlla Internet o chiedi al docente; non cancellare la cartella."
                }
            }
        } else {
            throw 'E11: cartella occupata; chiedi al docente di verificarla prima di rilanciare.'
        }
    }
    if ($Clone) {
        & git clone $Url $Target
        if ($LASTEXITCODE -ne 0) {
            throw "E12: download interrotto (exit code $LASTEXITCODE). Controlla Internet e rilancia lo stesso comando; le copie precedenti sono conservate."
        }
    }
    $Required = @('scripts/student_lab_cli.py', 'installer/tui.py', 'requirements-utui.txt',
        'scripts/manage-classroom-windows.ps1', 'scripts/launch-classroom-windows.ps1',
        'scripts/prepare-wsl-windows.ps1', 'scripts/remove-classroom-shortcuts-windows.ps1',
        'scripts/remove-wsl-windows.ps1', 'scripts/update-classroom-windows.ps1',
        'scripts/uninstall-classroom-windows.ps1')
    foreach ($Relative in $Required) {
        if (-not (Test-Path -LiteralPath (Join-Path $Target $Relative) -PathType Leaf)) {
            throw "E13: checkout incompleto, manca $Relative. File preservati; chiedi al docente."
        }
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

Write-Host "[1/4] Preparazione Git, Python 3.12 e editor micro..."
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "Git.Git"
} elseif (-not (Test-GitMinimumVersion)) {
    Write-Host "Git è presente ma troppo vecchio: provo ad aggiornarlo."
    Update-WingetPackage "Git.Git"
}
if (-not (Test-Python312)) {
    Install-WingetPackage "Python.Python.3.12"
}
if (-not (Get-Command micro -ErrorAction SilentlyContinue)) {
    Install-WingetPackage "zyedidia.micro"
}

$env:Path = @(
    "$env:ProgramFiles\Git\cmd"
    "$env:LOCALAPPDATA\Programs\Python\Launcher"
    "$env:LOCALAPPDATA\Programs\Python\Python312"
    "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
    $env:Path
) -join [IO.Path]::PathSeparator

if (-not (Test-GitMinimumVersion)) {
    Stop-WithMessage "E10" "Git non è disponibile in una versione compatibile" `
        "Serve Git 2.30 o successivo per aggiornare il progetto in sicurezza." `
        @(
            "Chiudi PowerShell."
            "Riapri PowerShell e rilancia lo stesso comando."
            "Se ricompare, comunica E10 al docente."
        )
}
if (-not (Test-Python312)) {
    Stop-WithMessage "E10" "Python 3.12 non è disponibile" `
        "Il comando Python esiste, ma non riesce ad avviare la versione 3.12 necessaria al menu guidato." `
        @(
            "Chiudi PowerShell."
            "Riapri PowerShell e rilancia lo stesso comando."
            "Se ricompare, comunica E10 al docente."
        )
}

Write-Host "[2/4] Preparazione repository..."
try {
    Initialize-ClassroomRepository -Directory $InstallDir -Url $RepositoryUrl
} catch {
    $Detail = $_.Exception.Message
    $Code = if ($Detail -match '^(E1[123]):') { $Matches[1] } else { 'E13' }
    Stop-WithMessage $Code 'Preparazione del progetto non completata' `
        'Il progetto non è pronto per avviare il menu guidato.' `
        @('Segui il dettaglio qui sotto; non cancellare cartelle o esercizi.',
          'Se ricompare, comunica il codice e il dettaglio al docente.') $Detail
}

Install-ClassroomLauncher

Write-Host "[3/4] Preparazione interfaccia guidata..."
$VenvDir = Join-Path $InstallDir ".installer-venv"
$PreviousErrorAction = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    $VenvOutput = @(& py -3.12 -m venv --clear $VenvDir 2>&1)
    $VenvExitCode = $LASTEXITCODE
} catch {
    $VenvOutput = @($_.Exception.Message)
    $VenvExitCode = 1
} finally {
    $ErrorActionPreference = $PreviousErrorAction
}
if ($VenvExitCode -ne 0) {
    Stop-WithMessage "E14" "Non sono riuscito a preparare l'interfaccia guidata" `
        "Python 3.12 è presente, ma Windows non ha permesso di creare il menu. Il progetto e gli esercizi non sono stati cancellati." `
        @(
            "Chiudi eventuali finestre Ambiente 2cornot2c ancora aperte."
            "Rilancia lo stesso comando."
            "Se ricompare, comunica E14 al docente."
        ) `
        "venv exit code $VenvExitCode; $($VenvOutput -join ' ')"
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
