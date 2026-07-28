$ErrorActionPreference = "Stop"

$StateDir = Join-Path $HOME ".2cornot2c"
$StatePath = Join-Path $StateDir "bootstrap-state.json"
$LogPath = Join-Path $StateDir "installer.jsonl"
$DefaultInstallDir = Join-Path $HOME "2cornot2c"
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

function Stop-WithMessage {
    param([string]$Message)
    Write-Host ""
    Write-Host "ERRORE: $Message" -ForegroundColor Red
    exit 1
}

function Test-SafeInstallDirectory {
    $FullPath = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
    $HomePath = [IO.Path]::GetFullPath($HOME).TrimEnd('\')
    $RootPath = [IO.Path]::GetPathRoot($FullPath).TrimEnd('\')
    if (-not $FullPath -or $FullPath -eq $HomePath -or $FullPath -eq $RootPath) {
        Stop-WithMessage "Directory di installazione non sicura: $FullPath"
    }
    if (Test-Path $FullPath) {
        if (-not (Test-Path (Join-Path $FullPath ".git"))) {
            Stop-WithMessage "La directory non è un clone Git: $FullPath"
        }
        if (Get-Command git -ErrorAction SilentlyContinue) {
            $Origin = git -C $FullPath remote get-url origin 2>$null
            if ($LASTEXITCODE -ne 0 -or $Origin -notmatch "TheBitPoets/2cornot2c") {
                Stop-WithMessage "Repository inatteso: $FullPath"
            }
        }
        if (Test-Path (Join-Path $FullPath ".vagrant")) {
            Stop-WithMessage (
                "È presente una VM VirtualBox. Non verrà rimossa automaticamente. " +
                "Spegni e rimuovi prima la VM con la procedura guidata."
            )
        }
        if (Test-Path (Join-Path $FullPath ".vagrant-vmware")) {
            Stop-WithMessage (
                "È presente una VM VMware. Non verrà rimossa automaticamente."
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
                Stop-WithMessage "Percorso non sicuro nel repository: $RelativePath"
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
Write-Host ""
Write-Host "lab, lab2 e modifiche locali verranno salvati prima della rimozione."
$Confirmation = Read-Host "Digita esattamente DISINSTALLA"
if ($Confirmation -ne "DISINSTALLA") {
    Write-Host "Disinstallazione annullata senza modifiche."
    exit 2
}

$BackupPath = Backup-StudentWork $SafeInstallDir
if ($BackupPath) {
    Write-Host "Backup creato: $BackupPath"
}

if ($ImageReference -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    docker image rm $ImageReference
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Immagine Docker in uso o già assente; continuo."
    }
}

if (Test-Path $SafeInstallDir) {
    Remove-Item -LiteralPath $SafeInstallDir -Recurse -Force
}

if ($OwnedPackages.Count -gt 0 -and -not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Warning "winget non e disponibile: i prerequisiti gestiti non verranno disinstallati."
    Write-Warning "Pacchetti ancora presenti: $($OwnedPackages -join ', ')"
}
elseif ($OwnedPackages.Count -gt 0) {
    foreach ($PackageId in $OwnedPackages | Sort-Object) {
        winget uninstall --id $PackageId --exact --silent
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Disinstallazione non riuscita o già eseguita: $PackageId"
        }
    }
}

if (Test-Path $StateDir) {
    Remove-Item -LiteralPath $StateDir -Recurse -Force
}

Write-Host "Disinstallazione completata."
if ($BackupPath) {
    Write-Host "Dati conservati in: $BackupPath"
}
