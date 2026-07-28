param(
    [switch]$ConfirmedFromTui
)

$ErrorActionPreference = "Stop"

$StateDir = Join-Path $HOME ".2cornot2c"
$StatePath = Join-Path $StateDir "bootstrap-state.json"
$LogPath = Join-Path $StateDir "installer.jsonl"
$DefaultInstallDir = Join-Path $HOME "2cornot2c"
$LauncherDir = Join-Path $env:LOCALAPPDATA "2cornot2c"
$InstallDir = if ($env:CLASSROOM_INSTALL_DIR) {
    $env:CLASSROOM_INSTALL_DIR
} elseif (Test-Path $StatePath) {
    try {
        [string](Get-Content $StatePath -Raw | ConvertFrom-Json).install_dir
    } catch {
        $DefaultInstallDir
    }
} else {
    $DefaultInstallDir
}

if ($ConfirmedFromTui) {
    # Python è avviato dalla cartella che verrà rimossa: la TUI deve avere il
    # tempo di chiudersi prima che inizi il rollback.
    Start-Sleep -Seconds 2
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
    Write-Host "COSA SIGNIFICA" -ForegroundColor Yellow
    Write-Host $Explanation -ForegroundColor Yellow
    Write-Host "COSA DEVI FARE" -ForegroundColor Yellow
    for ($Index = 0; $Index -lt $Actions.Count; $Index++) {
        Write-Host "$($Index + 1). $($Actions[$Index])" -ForegroundColor Yellow
    }
    Write-Host "Se chiedi aiuto, comunica questo codice: $Code" `
        -ForegroundColor Yellow
    if ($Technical) {
        Write-Host "Dettagli tecnici: $Technical" -ForegroundColor DarkGray
    }
    exit 1
}

function Test-SafeInstallDirectory {
    $FullPath = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
    $HomePath = [IO.Path]::GetFullPath($HOME).TrimEnd('\')
    $RootPath = [IO.Path]::GetPathRoot($FullPath).TrimEnd('\')
    if (-not $FullPath -or $FullPath -eq $HomePath -or $FullPath -eq $RootPath) {
        Stop-WithMessage "E26" "La cartella indicata non è sicura" `
            "Non sono certo che sia la cartella 2cornot2c, quindi non cancellerò nulla." `
            @("Non rimuovere file manualmente."; "Comunica E26 al docente.") $FullPath
    }
    if (Test-Path $FullPath) {
        if (-not (Test-Path (Join-Path $FullPath ".git"))) {
            Stop-WithMessage "E26" "La cartella indicata non è sicura" `
                "La cartella non contiene i segni che identificano il progetto. Nessun file è stato cancellato." `
                @("Non rimuovere file manualmente."; "Comunica E26 al docente.") $FullPath
        }
        if (Get-Command git -ErrorAction SilentlyContinue) {
            $Origin = git -C $FullPath remote get-url origin 2>$null
            if ($LASTEXITCODE -ne 0 -or $Origin -notmatch "TheBitPoets/2cornot2c") {
                Stop-WithMessage "E27" "La cartella appartiene a un progetto diverso" `
                    "Per sicurezza la disinstallazione si è fermata e non ha cancellato nulla." `
                    @("Non rimuovere la cartella manualmente."; "Comunica E27 al docente.") $FullPath
            }
        }
        if (Test-Path (Join-Path $FullPath ".vagrant")) {
            Stop-WithMessage "E28" "C'è ancora una macchina virtuale VirtualBox" `
                "La VM può contenere file. Per evitare perdite non verrà eliminata automaticamente." `
                @(
                    "Non cancellare la VM manualmente."
                    "Chiedi al docente come salvarla o rimuoverla."
                    "Poi ripeti la disinstallazione."
                )
        }
        if (Test-Path (Join-Path $FullPath ".vagrant-vmware")) {
            Stop-WithMessage "E28" "C'è ancora una macchina virtuale VMware" `
                "La VM può contenere file. Per evitare perdite non verrà eliminata automaticamente." `
                @(
                    "Non cancellare la VM manualmente."
                    "Chiedi al docente come salvarla o rimuoverla."
                    "Poi ripeti la disinstallazione."
                )
        }
    }
    return $FullPath
}

function Get-OwnedPackages {
    $Owned = [System.Collections.Generic.HashSet[string]]::new()
    if (Test-Path $StatePath) {
        try {
            $State = Get-Content $StatePath -Raw | ConvertFrom-Json
            foreach ($PackageId in $State.installed_by_bootstrap) {
                [void]$Owned.Add([string]$PackageId)
            }
        } catch {
            Write-Warning "Registro bootstrap non leggibile; non rimuovo prerequisiti."
        }
    }
    if (Test-Path $LogPath) {
        foreach ($Line in Get-Content $LogPath) {
            try {
                $Record = $Line | ConvertFrom-Json
                if ($Record.host -ne "windows-amd64" -or
                    $Record.status -ne "succeeded") {
                    continue
                }
                $PackageId = switch ($Record.key) {
                    "docker" { "Docker.DockerDesktop" }
                    "vagrant" { "Hashicorp.Vagrant" }
                    "virtualbox" { "Oracle.VirtualBox" }
                    default { $null }
                }
                if ($PackageId) {
                    [void]$Owned.Add($PackageId)
                }
            } catch {
                Write-Warning "Riga di log ignorata perché non valida."
            }
        }
    }
    return @($Owned | ForEach-Object { $_ })
}

function Test-WslInstalledByClassroom {
    if (-not (Test-Path $LogPath)) {
        return $false
    }
    foreach ($Line in Get-Content $LogPath) {
        try {
            $Record = $Line | ConvertFrom-Json
            if ($Record.host -eq "windows-amd64" -and
                $Record.key -eq "wsl" -and
                $Record.status -in @("restart_required", "succeeded")) {
                return $true
            }
        } catch {
            continue
        }
    }
    return $false
}

function Test-PackageStillInstalled {
    param([string]$PackageId)

    $DisplayNamePattern = switch ($PackageId) {
        "Docker.DockerDesktop" { "^Docker Desktop(?: |$)" }
        "Git.Git" { "^Git(?: |$)" }
        "Hashicorp.Vagrant" { "^Vagrant(?: |$)" }
        "Oracle.VirtualBox" { "^(?:Oracle VM )?VirtualBox(?: |$)" }
        default { return $false }
    }
    $UninstallRoots = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    foreach ($Root in $UninstallRoots) {
        $Match = Get-ItemProperty $Root -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DisplayName -match $DisplayNamePattern
            } |
            Select-Object -First 1
        if ($Match) {
            return $true
        }
    }
    return $false
}

function Get-ClassroomShortcutPaths {
    $Candidates = [System.Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($DesktopDir in @(
        [Environment]::GetFolderPath("Desktop")
        (Join-Path $HOME "Desktop")
        $(if ($env:OneDrive) { Join-Path $env:OneDrive "Desktop" })
        $(if ($env:OneDriveConsumer) {
            Join-Path $env:OneDriveConsumer "Desktop"
        })
        $(if ($env:OneDriveCommercial) {
            Join-Path $env:OneDriveCommercial "Desktop"
        })
    )) {
        if ($DesktopDir) {
            [void]$Candidates.Add(
                (Join-Path $DesktopDir "Ambiente 2cornot2c.lnk")
            )
        }
    }
    [void]$Candidates.Add(
        (Join-Path $env:APPDATA `
            "Microsoft\Windows\Start Menu\Programs\Ambiente 2cornot2c.lnk")
    )
    return @($Candidates)
}

function Backup-StudentWork {
    param([string]$Source)
    if (-not (Test-Path $Source)) {
        return $null
    }
    $NeedsBackup = (Test-Path (Join-Path $Source "lab")) -or
        (Test-Path (Join-Path $Source "lab2"))
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $Status = git -C $Source status --porcelain
        $NeedsBackup = $NeedsBackup -or [bool]$Status
    }
    if (-not $NeedsBackup) {
        return $null
    }

    $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Backup = Join-Path $HOME "2cornot2c-backup-$Stamp"
    New-Item -ItemType Directory -Path $Backup | Out-Null
    foreach ($Name in @("lab", "lab2")) {
        $Folder = Join-Path $Source $Name
        if (Test-Path $Folder) {
            Copy-Item -Recurse -Force $Folder $Backup
        }
    }
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git -C $Source diff --binary |
            Set-Content -Encoding UTF8 (Join-Path $Backup "modifiche.patch")
        $Prefix = [IO.Path]::GetFullPath($Source).TrimEnd('\') + '\'
        foreach ($RelativePath in git -C $Source ls-files --others --exclude-standard) {
            $Candidate = [IO.Path]::GetFullPath((Join-Path $Source $RelativePath))
            if (-not $Candidate.StartsWith(
                $Prefix,
                [StringComparison]::OrdinalIgnoreCase
            )) {
                Stop-WithMessage "E29" "Non riesco a salvare tutti i tuoi file" `
                    "La copia di sicurezza non può essere completata. La disinstallazione è stata fermata." `
                    @(
                        "Non cancellare il progetto."
                        "Controlla lo spazio libero."
                        "Comunica E29 al docente."
                    ) $RelativePath
            }
            $Destination = Join-Path $Backup $RelativePath
            New-Item -ItemType Directory -Force `
                -Path (Split-Path $Destination) | Out-Null
            Copy-Item -Recurse -Force $Candidate $Destination
        }
    }
    return $Backup
}

$SafeInstallDir = Test-SafeInstallDirectory
$OwnedPackages = Get-OwnedPackages
$OwnedWsl = Test-WslInstalledByClassroom
$ImageReference = $null
$LockPath = Join-Path $SafeInstallDir "docker\student-dev\toolchain.lock.json"
if (Test-Path $LockPath) {
    try {
        $Lock = Get-Content $LockPath -Raw | ConvertFrom-Json
        $ImageReference = "$($Lock.image_repository)@$($Lock.digest)"
    } catch {
        Write-Warning "Lock student-dev non leggibile; immagine non rimossa."
    }
}

Write-Host "Disinstallazione ambiente 2cornot2c"
Write-Host "Repository: $SafeInstallDir"
if ($ImageReference) {
    Write-Host "Immagine Docker: $ImageReference"
}
if ($OwnedPackages.Count -gt 0) {
    Write-Host "Programmi installati da 2cornot2c:"
    $OwnedPackages | Sort-Object | ForEach-Object { Write-Host "  - $_" }
} else {
    Write-Host "Nessun programma esterno attribuito a 2cornot2c."
}
if ($OwnedWsl) {
    Write-Host "Componente Windows installato da 2cornot2c:"
    Write-Host "  - WSL 2 e Virtual Machine Platform"
}
if (-not $ConfirmedFromTui) {
    Write-Host ""
    Write-Host "lab, lab2 e modifiche locali verranno salvati prima della rimozione."
    $Confirmation = Read-Host "Digita esattamente DISINSTALLA"
    if ($Confirmation -ne "DISINSTALLA") {
        Write-Host "Disinstallazione annullata senza modifiche."
        exit 2
    }
} else {
    Write-Host ""
    Write-Host "Conferma ricevuta dal menu guidato."
}

try {
    $BackupPath = Backup-StudentWork $SafeInstallDir
} catch {
    Stop-WithMessage "E29" "Non sono riuscito a salvare i tuoi esercizi" `
        "La copia di sicurezza non è completa. La disinstallazione è stata fermata." `
        @(
            "Non cancellare il progetto."
            "Controlla lo spazio libero sul disco."
            "Comunica E29 al docente."
        ) $_.Exception.Message
}
if ($BackupPath) {
    Write-Host "Backup creato: $BackupPath"
}

if ($ImageReference -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    docker image rm $ImageReference
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Immagine Docker in uso o già assente; continuo."
    }
}

if ($OwnedPackages.Count -gt 0 -and -not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Stop-WithMessage "E31" "Non posso rimuovere i programmi installati" `
        "Windows Package Manager non è disponibile. Conservo il registro e il collegamento per permetterti di riprovare." `
        @(
            "Non cancellare manualmente le cartelle."
            "Riavvia Windows e scegli di nuovo Disinstalla l'ambiente."
            "Se ricompare, comunica E31 al docente."
        ) "Pacchetti ancora presenti: $($OwnedPackages -join ', ')"
}
elseif ($OwnedPackages.Count -gt 0) {
    $PackageFailures = [System.Collections.Generic.List[string]]::new()
    foreach ($PackageId in $OwnedPackages | Sort-Object) {
        winget uninstall --id $PackageId --exact --silent
        $ExitCode = $LASTEXITCODE
        Start-Sleep -Seconds 2
        if (Test-PackageStillInstalled $PackageId) {
            $PackageFailures.Add("$PackageId (codice $ExitCode)")
        }
    }
    if ($PackageFailures.Count -gt 0) {
        Stop-WithMessage "E31" "Uno o più programmi non sono stati rimossi" `
            "La disinstallazione si è fermata senza cancellare il registro, così puoi riprovare in sicurezza." `
            @(
                "Chiudi Docker Desktop e gli altri programmi dell'ambiente."
                "Riavvia Windows."
                "Scegli di nuovo Disinstalla l'ambiente."
                "Se ricompare, comunica E31 al docente."
            ) ($PackageFailures -join ", ")
    }
}

if ($OwnedWsl) {
    $WslCleanup = Join-Path $LauncherDir "remove-wsl-windows.ps1"
    $PowerShell = Join-Path `
        $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $Cleanup = Start-Process `
        -FilePath $PowerShell `
        -ArgumentList @(
            "-NoProfile"
            "-ExecutionPolicy"
            "Bypass"
            "-File"
            "`"$WslCleanup`""
        ) `
        -Verb RunAs `
        -Wait `
        -PassThru
    if ($Cleanup.ExitCode -eq 2) {
        Write-Warning (
            "WSL non è stato rimosso per proteggere eventuali dati personali. " +
            "Comunica E30 al docente."
        )
    } elseif ($Cleanup.ExitCode -ne 0) {
        Stop-WithMessage "E32" "Windows non ha completato la rimozione di WSL" `
            "La verifica finale rileva ancora uno o più componenti di WSL. Il registro è stato conservato per permetterti di riprovare." `
            @(
                "Riavvia Windows."
                "Scegli di nuovo Disinstalla l'ambiente."
                "Se ricompare, comunica E32 al docente."
            ) "remove-wsl-windows.ps1 exit code $($Cleanup.ExitCode)"
    }
}

if (Test-Path $SafeInstallDir) {
    Remove-Item -LiteralPath $SafeInstallDir -Recurse -Force
}

if (Test-Path $StateDir) {
    Remove-Item -LiteralPath $StateDir -Recurse -Force
}

$RunOncePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
Remove-ItemProperty `
    -Path $RunOncePath `
    -Name "2cornot2c-resume" `
    -ErrorAction SilentlyContinue

foreach ($ShortcutPath in Get-ClassroomShortcutPaths) {
    if (Test-Path $ShortcutPath) {
        Remove-Item -LiteralPath $ShortcutPath -Force
    }
}
if (Test-Path $LauncherDir) {
    Remove-Item -LiteralPath $LauncherDir -Recurse -Force
}

Write-Host "Disinstallazione completata."
if ($BackupPath) {
    Write-Host "Dati conservati in: $BackupPath"
}
