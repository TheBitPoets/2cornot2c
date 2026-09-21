param(
    [switch]$ConfirmedFromTui,
    [switch]$DestroyClassroomVm,
    [switch]$SelectComponents,
    [string]$Components,
    [switch]$Preview
)

$ErrorActionPreference = "Stop"
$Selective = $SelectComponents -or $Preview -or $PSBoundParameters.ContainsKey('Components')

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

if ($ConfirmedFromTui -and -not $Selective) {
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
    $Ancestor = $FullPath
    while ($Ancestor) {
        if ((Test-Path -LiteralPath $Ancestor) -and
            ((Get-Item -LiteralPath $Ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Percorso del progetto con collegamenti: nessuna rimozione consentita.'
        }
        $Ancestor = Split-Path -Parent $Ancestor
    }
    if (Test-Path $FullPath) {
        if (-not (Test-Path (Join-Path $FullPath ".git"))) {
            Stop-WithMessage "E26" "La cartella indicata non è sicura" `
                "La cartella non contiene i segni che identificano il progetto. Nessun file è stato cancellato." `
                @("Non rimuovere file manualmente."; "Comunica E26 al docente.") $FullPath
        }
        if (Get-Command git -ErrorAction SilentlyContinue) {
            $Origin = git -C $FullPath remote get-url origin 2>$null
            if ($LASTEXITCODE -ne 0 -or $Origin -notmatch '^(?:https://github\.com/|git@github\.com:)TheBitPoets/2cornot2c(?:\.git)?/?$') {
                Stop-WithMessage "E27" "La cartella appartiene a un progetto diverso" `
                    "Per sicurezza la disinstallazione si è fermata e non ha cancellato nulla." `
                    @("Non rimuovere la cartella manualmente."; "Comunica E27 al docente.") $FullPath
            }
        }
        if ((Test-Path (Join-Path $FullPath ".vagrant")) -and
            -not $DestroyClassroomVm -and -not $Selective) {
            Stop-WithMessage "E28" "C'è ancora una macchina virtuale VirtualBox" `
                "La VM può contenere file. Per evitare perdite non verrà eliminata automaticamente." `
                @(
                    "Non cancellare la VM manualmente."
                    "Chiedi al docente come salvarla o rimuoverla."
                    "Poi ripeti la disinstallazione."
                )
        }
        if ((Test-Path (Join-Path $FullPath ".vagrant-vmware")) -and
            -not $DestroyClassroomVm -and -not $Selective) {
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
        "zyedidia.micro" { "^micro(?: |$)" }
        "Python.Python.3.12" { "^Python 3\.12(?:\.| |$)" }
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
        [Environment]::GetFolderPath("CommonDesktopDirectory")
        (Join-Path $HOME "Desktop")
        $(if ($env:PUBLIC) { Join-Path $env:PUBLIC "Desktop" })
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
    foreach ($ProgramsDir in @(
        [Environment]::GetFolderPath("Programs")
        [Environment]::GetFolderPath("CommonPrograms")
        $(if ($env:APPDATA) {
            Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
        })
        $(if ($env:ProgramData) {
            Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs"
        })
    )) {
        if ($ProgramsDir) {
            [void]$Candidates.Add(
                (Join-Path $ProgramsDir "Ambiente 2cornot2c.lnk")
            )
        }
    }
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

function Remove-ClassroomVirtualMachines {
    param([string]$Project)

    $StateDirectories = @(
        ".vagrant"
        ".vagrant-vmware"
    ) | Where-Object { Test-Path (Join-Path $Project $_) }
    if ($StateDirectories.Count -eq 0) {
        return
    }
    if (-not (Get-Command vagrant -ErrorAction SilentlyContinue)) {
        Stop-WithMessage "E33" "Non posso eliminare la macchina virtuale" `
            "La VM esiste, ma Vagrant non è disponibile. Nessun disco è stato cancellato." `
            @(
                "Non eliminare file o dischi manualmente."
                "Comunica E33 al docente."
            )
    }

    Push-Location $Project
    try {
        foreach ($StateDirectory in $StateDirectories) {
            $PreviousDotfile = $env:VAGRANT_DOTFILE
            $env:VAGRANT_DOTFILE = $StateDirectory
            & vagrant destroy --force
            $ExitCode = $LASTEXITCODE
            if ($null -eq $PreviousDotfile) {
                Remove-Item Env:VAGRANT_DOTFILE -ErrorAction SilentlyContinue
            } else {
                $env:VAGRANT_DOTFILE = $PreviousDotfile
            }
            if ($ExitCode -ne 0) {
                Stop-WithMessage "E33" "La VM non è stata eliminata" `
                    "Vagrant non ha confermato la rimozione del disco. La disinstallazione si è fermata per sicurezza." `
                    @(
                        "Chiudi VirtualBox e VMware."
                        "Riprova il ripristino completo."
                        "Se ricompare, comunica E33 al docente."
                    ) "vagrant destroy exit code $ExitCode; $StateDirectory"
            }
            $StatePath = Join-Path $Project $StateDirectory
            if (Test-Path $StatePath) {
                Remove-Item -LiteralPath $StatePath -Recurse -Force
            }
        }
    } finally {
        Pop-Location
    }

    $BoxFile = Join-Path $Project ".classroom-box"
    if (Test-Path $BoxFile) {
        $BoxName = (Get-Content $BoxFile -Raw).Trim()
        if ($BoxName -match "^2cornot2c/") {
            $ProviderFile = Join-Path $Project ".classroom-provider"
            $ProviderArgs = @()
            if (Test-Path $ProviderFile) {
                $Provider = (Get-Content $ProviderFile -Raw).Trim()
                if ($Provider -match "^[a-z0-9_-]+$") {
                    $ProviderArgs = @("--provider", $Provider)
                }
            }
            & vagrant box remove $BoxName @ProviderArgs --force
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Box $BoxName già assente o non rimovibile."
            }
        }
    }
}

function Invoke-InventoryCommand {
    param([string]$Executable, [string[]]$Arguments, [int]$TimeoutMilliseconds = 10000)
    $Command = Get-Command $Executable -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $Command) { return @{ code=127; output=''; error="$Executable non disponibile" } }
    $Quoted = @(foreach ($Argument in $Arguments) {
        if ($Argument -match '["\r\n\x00]') { throw 'Argomento del comando non valido.' }
        # WSL parses switches from the raw Windows command line. Quote only
        # arguments that need it, otherwise --list can become a Linux command.
        if ($Argument -ne '' -and $Argument -notmatch '\s') { $Argument }
        else { '"' + ($Argument -replace '(\\+)$', '$1$1') + '"' }
    })
    $Process = [Diagnostics.Process]::new()
    $Process.StartInfo = [Diagnostics.ProcessStartInfo]::new($Command.Source, ($Quoted -join ' '))
    $Process.StartInfo.UseShellExecute = $false
    $Process.StartInfo.CreateNoWindow = $true
    $Process.StartInfo.RedirectStandardOutput = $true
    $Process.StartInfo.RedirectStandardError = $true
    $Output = [IO.MemoryStream]::new()
    try {
        [void]$Process.Start()
        $Copy = $Process.StandardOutput.BaseStream.CopyToAsync($Output)
        $Errors = $Process.StandardError.ReadToEndAsync()
        if (-not $Process.WaitForExit($TimeoutMilliseconds)) {
            $Process.Kill()
            $Process.WaitForExit()
            return @{ code=124; output=''; error="${Executable}: tempo di attesa superato" }
        }
        [void]$Copy.GetAwaiter().GetResult()
        $Bytes = $Output.ToArray()
        # WSL versions emit either UTF-16LE or UTF-8 when stdout is redirected.
        $Encoding = if ($Bytes.Length -gt 1 -and ($Bytes[1] -eq 0 -or
            ($Bytes[0] -eq 255 -and $Bytes[1] -eq 254))) { [Text.Encoding]::Unicode } else { [Text.Encoding]::UTF8 }
        return @{ code=$Process.ExitCode; output=$Encoding.GetString($Bytes).Trim([char]0xfeff).Trim();
            error=$Errors.GetAwaiter().GetResult() }
    } finally { $Process.Dispose(); $Output.Dispose() }
}

function Get-DetectedPackages {
    foreach ($Id in @('Git.Git', 'Python.Python.3.12', 'zyedidia.micro',
        'Docker.DockerDesktop', 'Hashicorp.Vagrant', 'Oracle.VirtualBox')) {
        if (Test-PackageStillInstalled $Id) { $Id }
    }
}

function Get-WslInventory {
    $Result = Invoke-InventoryCommand 'wsl.exe' @('--list', '--quiet')
    $Names = @()
    if ($Result.code -eq 0) {
        $Names = @($Result.output -split '\r?\n' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }
    # A registered app is also evidence when the engine cannot answer.
    $Registered = @(Get-AppxPackage 'MicrosoftCorporationII.WindowsSubsystemForLinux' -ErrorAction SilentlyContinue).Count -gt 0
    return @{ installed=($Result.code -eq 0 -or $Registered); distributions=$Names;
        error=$(if ($Result.code -ne 0) { "Elenco WSL non verificabile (exit $($Result.code)): " + ($Result.error + ' ' + $Result.output).Trim() } else { '' }) }
}

function Get-DockerInventory {
    $Endpoint = $env:DOCKER_HOST
    if (-not $Endpoint -or $env:DOCKER_CONTEXT) {
        $Arguments = @('context', 'inspect', '--format', '{{json .Endpoints.docker.Host}}')
        if ($env:DOCKER_CONTEXT) { $Arguments += $env:DOCKER_CONTEXT }
        $Context = Invoke-InventoryCommand 'docker' $Arguments
        if ($Context.code -ne 0) { return @{ error='Docker non disponibile'; endpoint=''; containers=@(); volumes=@(); images=@(); networks=@() } }
        $Endpoint = $Context.output | ConvertFrom-Json
    }
    if ($Endpoint -notmatch '^npipe:/{4}\./pipe/(docker_engine|dockerDesktopLinuxEngine|dockerDesktopWindowsEngine)$') {
        return @{ error='Contesto Docker non locale: nessun dato remoto può essere selezionato.'; endpoint=''; containers=@(); volumes=@(); images=@(); networks=@() }
    }
    $Data = @{ endpoint=$Endpoint; error=''; containers=@(); volumes=@(); images=@(); networks=@() }
    foreach ($Type in @('container', 'volume', 'image', 'network')) {
        $Arguments = @('--host', $Endpoint, $Type, 'ls', '--format', '{{json .}}')
        if ($Type -in @('container', 'image')) { $Arguments += @('--all', '--no-trunc') }
        if ($Type -eq 'network') { $Arguments += '--no-trunc' }
        $Result = Invoke-InventoryCommand 'docker' $Arguments
        if ($Result.code -ne 0) { $Data.error='Inventario Docker incompleto: avvia Docker Desktop e riprova.'; return $Data }
        $Items = @(foreach ($Line in ($Result.output -split '\r?\n')) {
            if ($Line.Trim()) { $Line | ConvertFrom-Json }
        })
        if ($Type -eq 'network') { $Items = @($Items | Where-Object { $_.Name -notin @('bridge', 'host', 'none', 'nat', 'Default Switch') }) }
        $Key = if ($Type -eq 'image') { 'images' } else { $Type + 's' }
        $Data[$Key] = $Items
    }
    return $Data
}

function Remove-SelectedDockerData {
    param($Inventory)
    $Current = Get-DockerInventory
    if ($Current.error -or $Current.endpoint -ne $Inventory.endpoint) { throw 'Motore Docker cambiato o non verificabile. Riapri la selezione.' }
    # Recheck the exact identities shown in the preview. Never use prune.
    foreach ($Kind in @('containers', 'volumes', 'images', 'networks')) {
        $Field = if ($Kind -eq 'volumes') { 'Name' } else { 'ID' }
        $Before = @($Inventory[$Kind] | ForEach-Object { $_.$Field } | Sort-Object -Unique)
        $After = @($Current[$Kind] | ForEach-Object { $_.$Field } | Sort-Object -Unique)
        if (($Before -join "`n") -cne ($After -join "`n")) { throw 'I dati Docker sono cambiati. Riapri la selezione.' }
    }
    foreach ($Kind in @('containers', 'volumes', 'images', 'networks')) {
        $Type = @{ containers='container'; volumes='volume'; images='image'; networks='network' }[$Kind]
        $Field = if ($Kind -eq 'volumes') { 'Name' } else { 'ID' }
        foreach ($Id in @($Inventory[$Kind] | ForEach-Object { $_.$Field } | Sort-Object -Unique)) {
            $Arguments = @('--host', $Inventory.endpoint, $Type, 'rm')
            if ($Kind -in @('containers', 'images')) { $Arguments += '--force' }
            $Arguments += $Id
            & docker @Arguments
            if ($LASTEXITCODE -ne 0) { throw "Dato Docker non rimosso: $Type $Id. Operazione interrotta." }
        }
    }
}

function Get-UninstallOptions {
    param([string]$Project, [string[]]$Packages, [bool]$Wsl, [string]$Image)
    $Options = @()
    if (Test-Path -LiteralPath $Project) {
        $Options += [pscustomobject]@{ id='project'; label='Cartella progetto (backup completo prima della rimozione)' }
    }
    if ($Image) {
        $Options += [pscustomobject]@{ id='docker-image'; label='Immagine Docker didattica (non i volumi personali)' }
    }
    if ((Test-Path -LiteralPath (Join-Path $Project '.vagrant')) -or
        (Test-Path -LiteralPath (Join-Path $Project '.vagrant-vmware'))) {
        $Options += [pscustomobject]@{ id='vm'; label='VM, disco e box didattica: dati interni eliminati definitivamente' }
    }
    $Labels = @{
        'Git.Git'='Git'; 'Python.Python.3.12'='Python 3.12'; 'zyedidia.micro'='Editor micro'
        'Docker.DockerDesktop'='Docker Desktop (può contenere dati di altri progetti)'
        'Hashicorp.Vagrant'='Vagrant'; 'Oracle.VirtualBox'='VirtualBox'
    }
    foreach ($Package in @(@($Packages) + @(Get-DetectedPackages) | Sort-Object -Unique)) {
        if ($Labels.ContainsKey($Package)) {
            $External = $Package -notin $Packages
            $Suffix = if ($External) { ' [non attribuito a 2cornot2c]' } else { ' [installato da 2cornot2c]' }
            $Options += [pscustomobject]@{ id=$Package; label=($Labels[$Package] + $Suffix); external=$External }
        }
    }
    if ($Wsl -or $WslInventory.installed) {
        $Suffix = if ($Wsl) { ' [installato da 2cornot2c]' } else { ' [non attribuito a 2cornot2c]' }
        $Options += [pscustomobject]@{ id='wsl'; label=('WSL 2 e Virtual Machine Platform' + $Suffix); external=(-not $Wsl) }
    }
    foreach ($Name in $WslInventory.distributions) {
        $Options += [pscustomobject]@{ id=('wsl-distro:' + $Name); label=('Distribuzione WSL ' + $Name + ': elimina TUTTI i suoi dati'); external=$true }
    }
    if ('Docker.DockerDesktop' -in $Options.id -or $DockerInventory.endpoint) {
        $Options += [pscustomobject]@{ id='docker-data'; label='Dati Docker: container, immagini, volumi e reti del motore locale'; external=$true }
    }
    $Options += [pscustomobject]@{ id='shortcuts'; label='Collegamenti desktop e menu Start' }
    return $Options
}

function Read-UninstallSelection {
    param([object[]]$Options)
    $Chosen = [System.Collections.Generic.HashSet[string]]::new()
    while ($true) {
        Write-Host ''
        Write-Host 'Scegli cosa disinstallare. Nessun componente è selezionato automaticamente.'
        for ($Index = 0; $Index -lt $Options.Count; $Index++) {
            $Mark = if ($Chosen.Contains($Options[$Index].id)) { 'x' } else { ' ' }
            Write-Host ("{0}. [{1}] {2}" -f ($Index + 1), $Mark, $Options[$Index].label)
        }
        $Answer = Read-Host 'Numero per selezionare/deselezionare, t per tutti, z per azzerare, invio per riepilogo, q per annullare'
        if ($Answer -eq 'q') { return @() }
        if ($Answer -eq '') { return @($Chosen | Sort-Object) }
        if ($Answer -eq 't') { foreach ($Option in $Options) { [void]$Chosen.Add($Option.id) }; continue }
        if ($Answer -eq 'z') { $Chosen.Clear(); continue }
        $Number = 0
        if ([int]::TryParse($Answer, [ref]$Number) -and $Number -ge 1 -and $Number -le $Options.Count) {
            $Id = $Options[$Number - 1].id
            if (-not $Chosen.Add($Id)) { [void]$Chosen.Remove($Id) }
        } else { Write-Host 'Inserisci uno dei numeri mostrati.' }
    }
}

function Get-SelectionBlockers {
    param([object[]]$Options, [string[]]$Selected)
    foreach ($Id in $Selected) {
        if ($Id -cnotin @($Options.id)) { "Componente non disponibile: $Id" }
    }
    if (@($Selected | Where-Object { $_ -in @('project', 'vm') }).Count -and
        -not (Get-Command git -ErrorAction SilentlyContinue)) {
        'Git non disponibile: impossibile verificare la provenienza del progetto prima della rimozione.'
    }
    if ('vm' -in $Options.id -and 'vm' -notin $Selected -and
        @($Selected | Where-Object { $_ -in @('project', 'Hashicorp.Vagrant', 'Oracle.VirtualBox') }).Count) {
        'La VM viene conservata: conserva anche progetto, Vagrant e VirtualBox, oppure seleziona esplicitamente la VM.'
    }
    if ('wsl' -in $Selected -and 'Docker.DockerDesktop' -notin $Selected -and
        (Test-PackageStillInstalled 'Docker.DockerDesktop')) {
        'Docker Desktop usa WSL: conserva WSL oppure seleziona anche Docker Desktop e i suoi dati.'
    }
    if ('Docker.DockerDesktop' -in $Selected -and 'docker-data' -notin $Selected) {
        'Disinstallare Docker Desktop elimina anche i suoi dati: seleziona e conferma anche Dati Docker.'
    }
    if ('docker-data' -in $Selected -and 'Docker.DockerDesktop' -notin $Selected -and $DockerInventory.error) {
        $DockerInventory.error
    }
    if ('docker-image' -in $Selected -and 'docker-data' -notin $Selected -and $DockerInventory.error) { $DockerInventory.error }
    if ('wsl' -in $Selected) {
        if ($WslInventory.error) { $WslInventory.error }
        foreach ($Name in $WslInventory.distributions) {
            if (('wsl-distro:' + $Name) -notin $Selected -and
                -not ($Name -match '^docker-desktop(?:-data)?$' -and 'Docker.DockerDesktop' -in $Selected)) {
                "WSL contiene $Name non selezionata. Conserva WSL oppure seleziona esplicitamente questa distribuzione."
            }
        }
    }
    foreach ($Id in @($Selected | Where-Object { $_ -like 'wsl-distro:*' })) {
        if ($Id -match '^wsl-distro:docker-desktop(?:-data)?$' -and
            ('Docker.DockerDesktop' -notin $Selected -or 'docker-data' -notin $Selected)) {
            'Le distribuzioni gestite da Docker richiedono anche la selezione di Docker Desktop e dei suoi dati.'
        }
    }
}

function Save-RetainedImage {
    param([string]$Reference)
    New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    $Path = Join-Path $StateDir 'uninstall-retained-image.json'
    $Temporary = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    @{ image=$Reference } | ConvertTo-Json | Set-Content -LiteralPath $Temporary -Encoding UTF8
    Move-Item -LiteralPath $Temporary -Destination $Path -Force
}

function Save-UninstalledComponent {
    param([string]$Id)
    # Keep ownership for every unselected component; do not erase the registry.
    if (Test-Path -LiteralPath $StatePath) {
        $Saved = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        $Saved.installed_by_bootstrap = @($Saved.installed_by_bootstrap | Where-Object { $_ -ne $Id })
        $Temporary = "$StatePath.$([guid]::NewGuid().ToString('N')).tmp"
        $Saved | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Temporary -Encoding UTF8
        Move-Item -LiteralPath $Temporary -Destination $StatePath -Force
    }
    $Key = switch ($Id) {
        'Docker.DockerDesktop' { 'docker' }; 'Hashicorp.Vagrant' { 'vagrant' }
        'Oracle.VirtualBox' { 'virtualbox' }; 'Git.Git' { 'git' }
        'wsl' { 'wsl' }; default { $null }
    }
    if ($Key -and (Test-Path -LiteralPath $LogPath)) {
        $Kept = @(foreach ($Line in Get-Content -LiteralPath $LogPath -Encoding UTF8) {
            if (-not $Line.Trim()) { continue }
            $Record = $Line | ConvertFrom-Json
            if ($Record.host -ne 'windows-amd64' -or $Record.key -ne $Key -or
                $Record.status -notin @('succeeded', 'restart_required')) { $Line }
        })
        $Temporary = "$LogPath.$([guid]::NewGuid().ToString('N')).tmp"
        [IO.File]::WriteAllLines($Temporary, [string[]]$Kept, [Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $Temporary -Destination $LogPath -Force
    }
}

function Get-SelectedProjectEntries {
    param([string]$Source)
    $Root = Get-Item -LiteralPath $Source -Force -ErrorAction Stop
    if (-not $Root.PSIsContainer -or ($Root.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Cartella non verificabile: $Source"
    }
    # Inspect each directory before descending; never follow junctions.
    $Pending = [System.Collections.Generic.Queue[string]]::new()
    $Pending.Enqueue($Source)
    $Entries = [System.Collections.Generic.List[object]]::new()
    while ($Pending.Count) {
        foreach ($Item in Get-ChildItem -LiteralPath $Pending.Dequeue() -Force -ErrorAction Stop) {
            if ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Backup interrotto: collegamento da verificare con il docente: $($Item.FullName)"
            }
            $Entries.Add($Item)
            if ($Item.PSIsContainer) { $Pending.Enqueue($Item.FullName) }
        }
    }
    return $Entries.ToArray()
}

function Backup-SelectedProject {
    param([string]$Source)
    if (-not (Test-Path -LiteralPath $Source)) { return $null }
    # Include staged, ignored and untracked files, plus Git metadata.
    $Entries = @(Get-SelectedProjectEntries $Source)
    $Backup = Join-Path $HOME ("2cornot2c-backup-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $Backup -ErrorAction Stop | Out-Null
    foreach ($Item in $Entries) {
        $Relative = $Item.FullName.Substring($Source.TrimEnd('\').Length).TrimStart('\')
        $Destination = Join-Path $Backup $Relative
        if ($Item.PSIsContainer) {
            New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        } else {
            Copy-Item -LiteralPath $Item.FullName -Destination $Destination -ErrorAction Stop
            if ((Get-FileHash -LiteralPath $Item.FullName).Hash -ne
                (Get-FileHash -LiteralPath $Destination).Hash) { throw "Backup non verificato: $Relative" }
        }
    }
    return $Backup
}

function Assert-SelectedProjectBackup {
    param([string]$Source, [string]$Backup)
    if (-not $Backup) { throw 'Copia di sicurezza assente.' }
    $Current = @(Get-SelectedProjectEntries $Source)
    $Saved = @(Get-SelectedProjectEntries $Backup)
    if ($Current.Count -ne $Saved.Count) { throw 'Il contenuto del progetto è cambiato dopo il backup.' }
    $SavedByPath = @{}
    foreach ($Item in $Saved) {
        $Relative = $Item.FullName.Substring($Backup.TrimEnd('\').Length).TrimStart('\')
        $SavedByPath[$Relative] = $Item
    }
    foreach ($Item in $Current) {
        $Relative = $Item.FullName.Substring($Source.TrimEnd('\').Length).TrimStart('\')
        $Copy = $SavedByPath[$Relative]
        if (-not $Copy -or $Item.PSIsContainer -ne $Copy.PSIsContainer) {
            throw "Il contenuto del progetto è cambiato dopo il backup: $Relative"
        }
        if (-not $Item.PSIsContainer) {
            $SourceHash = (Get-FileHash -LiteralPath $Item.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
            $BackupHash = (Get-FileHash -LiteralPath $Copy.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
            if (-not $SourceHash -or -not $BackupHash -or $SourceHash -ne $BackupHash) {
                throw "Il file non corrisponde al backup: $Relative"
            }
        }
    }
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
$RetainedImagePath = Join-Path $StateDir 'uninstall-retained-image.json'
if (-not $ImageReference -and (Test-Path -LiteralPath $RetainedImagePath)) {
    $ImageReference = [string](Get-Content -LiteralPath $RetainedImagePath -Raw | ConvertFrom-Json).image
}
# A lock/retained record is data, never a command option or an arbitrary image.
if ($ImageReference -and $ImageReference -cnotmatch '^ghcr\.io/thebitpoets/2cornot2c-student-dev@sha256:[a-f0-9]{64}$') {
    throw 'Riferimento immagine didattica non valido: nessuna rimozione consentita.'
}
$RetainedImage = $ImageReference

$Selected = @()
if ($Selective) {
    $WslInventory = Get-WslInventory
    $DockerInventory = Get-DockerInventory
    $Options = @(Get-UninstallOptions $SafeInstallDir $OwnedPackages $OwnedWsl $ImageReference)
    $Selected = if ($Components) { @($Components.Split(',') | Sort-Object -Unique) } else { @() }
    if ($SelectComponents -and -not $Preview -and -not $PSBoundParameters.ContainsKey('Components')) {
        $Selected = @(Read-UninstallSelection $Options)
    }
    $Blockers = @(Get-SelectionBlockers $Options $Selected)
    if ($Preview) {
        [ordered]@{ project=$SafeInstallDir; options=@($Options); selected=@($Selected);
            blockers=@($Blockers); image=$ImageReference; registry_preserved=$true;
            wsl=$WslInventory; docker=$DockerInventory } |
            ConvertTo-Json -Depth 6
        exit 0
    }
    if ($Blockers.Count) { throw ($Blockers -join "`n") }
    if (-not $Selected.Count) { Write-Host 'Nessun componente selezionato. Nessuna modifica.'; exit 2 }
    # Validate both ownership files before the first destructive operation.
    if (Test-Path -LiteralPath $StatePath) {
        $Registry = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        if (-not $Registry.PSObject.Properties['installed_by_bootstrap']) { throw 'Registro bootstrap incompleto.' }
    }
    if (Test-Path -LiteralPath $LogPath) {
        foreach ($Line in Get-Content -LiteralPath $LogPath) {
            if ($Line.Trim()) { $null = $Line | ConvertFrom-Json }
        }
    }
    Write-Host 'Verranno rimossi SOLO i componenti selezionati:'
    $Options | Where-Object { $_.id -in $Selected } | ForEach-Object { Write-Host "  - $($_.label)" }
    Write-Host 'I programmi condivisi selezionati possono servire anche ad altri progetti.'
    Write-Host 'Registro e strumenti di gestione saranno conservati per le rimozioni successive.'
    if (@($Options | Where-Object { $_.id -in $Selected -and $_.external }).Count) {
        if ((Read-Host 'Sono inclusi componenti o dati esterni: digita RIMUOVI COMPONENTI ESTERNI') -cne 'RIMUOVI COMPONENTI ESTERNI') { exit 2 }
    }
    if ('docker-data' -in $Selected) {
        foreach ($Kind in @('containers', 'volumes', 'images', 'networks')) {
            Write-Host ("{0}: {1}" -f $Kind, (($DockerInventory[$Kind] | ConvertTo-Json -Compress -Depth 4) -join ''))
        }
        if ('Docker.DockerDesktop' -in $Selected) {
            Write-Host 'Disinstallare Docker Desktop elimina TUTTI i suoi dati locali, anche di motori non attivi o non elencabili.'
        } elseif ($DockerInventory.error) { throw $DockerInventory.error }
        if ((Read-Host 'Conferma la cancellazione dei dati elencati digitando ELIMINA DATI DOCKER') -cne 'ELIMINA DATI DOCKER') { exit 2 }
    }
    foreach ($Id in @($Selected | Where-Object { $_ -like 'wsl-distro:*' })) {
        $Name = $Id.Substring(11)
        if ((Read-Host "Tutti i dati di $Name saranno persi. Digita ELIMINA WSL $Name") -cne "ELIMINA WSL $Name") { exit 2 }
    }
    if ('vm' -in $Selected) {
        Write-Host 'Il backup del progetto NON salva i file presenti soltanto nel disco della VM.'
        if ((Read-Host 'Per eliminare definitivamente VM e disco digita ELIMINA VM') -cne 'ELIMINA VM') { exit 2 }
    }
    if ('wsl' -in $Selected) {
        if ((Read-Host 'Per rimuovere WSL digita RIMUOVI WSL') -cne 'RIMUOVI WSL') { exit 2 }
    }
    if ((Read-Host 'Conferma la selezione digitando DISINSTALLA') -cne 'DISINSTALLA') { exit 2 }
    $DestroyClassroomVm = 'vm' -in $Selected
    $OwnedPackages = @(@($OwnedPackages) + @(Get-DetectedPackages) | Sort-Object -Unique | Where-Object { $_ -in $Selected })
    $OwnedWsl = 'wsl' -in $Selected
    if ('docker-image' -notin $Selected -or 'docker-data' -in $Selected) { $ImageReference = $null }
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
if (-not $ConfirmedFromTui -and -not $Selective) {
    Write-Host ""
    Write-Host "lab, lab2 e modifiche locali verranno salvati prima della rimozione."
    $RequiredConfirmation = if ($DestroyClassroomVm) {
        "DISINSTALLA TUTTO"
    } else {
        "DISINSTALLA"
    }
    $Confirmation = Read-Host "Digita esattamente $RequiredConfirmation"
    if ($Confirmation -ne $RequiredConfirmation) {
        Write-Host "Disinstallazione annullata senza modifiche."
        exit 2
    }
} elseif (-not $Selective) {
    Write-Host ""
    Write-Host "Conferma ricevuta dal menu guidato."
}

try {
    $BackupPath = if ($Selective) {
        if ('project' -in $Selected -or 'vm' -in $Selected) { Backup-SelectedProject $SafeInstallDir }
    } else { Backup-StudentWork $SafeInstallDir }
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

if ($Selective) {
    $SelectedDistros = @($Selected | Where-Object { $_ -like 'wsl-distro:*' })
    if ($SelectedDistros.Count) {
        $CurrentWsl = Get-WslInventory
        if ($CurrentWsl.error) { throw $CurrentWsl.error }
        foreach ($Id in $SelectedDistros) {
            $Name = $Id.Substring(11)
            if ($Name -cnotin $CurrentWsl.distributions) { throw "Distribuzione cambiata: $Name. Riapri la selezione." }
            & wsl.exe --unregister $Name
            if ($LASTEXITCODE -ne 0) { throw "Distribuzione non rimossa: $Name" }
            $VerifiedWsl = Get-WslInventory
            if ($VerifiedWsl.error -or $Name -cin $VerifiedWsl.distributions) {
                throw "Rimozione della distribuzione non verificata: $Name"
            }
        }
    }
    if ('docker-data' -in $Selected -and 'Docker.DockerDesktop' -notin $Selected) {
        Remove-SelectedDockerData $DockerInventory
        Save-RetainedImage ''
    }
}

if ($DestroyClassroomVm) {
    Write-Host "Eliminazione della VM 2cornot2c e del relativo disco..."
    Remove-ClassroomVirtualMachines $SafeInstallDir
}

if ($ImageReference -and (Get-Command docker -ErrorAction SilentlyContinue)) {
    if ($Selective) { docker --host $DockerInventory.endpoint image rm $ImageReference }
    else { docker image rm $ImageReference }
    if ($LASTEXITCODE -ne 0) {
        if ($Selective) { throw 'Immagine Docker non rimossa. Nessun container o volume viene forzato.' }
        Write-Warning "Immagine Docker in uso o già assente; continuo."
    } elseif ($Selective) {
        Save-RetainedImage ''
    }
} elseif ($Selective -and $ImageReference) {
    throw 'Docker non disponibile: impossibile rimuovere o verificare questa immagine.'
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
        } elseif ($Selective -and $ExitCode -ne 0) {
            $PackageFailures.Add("$PackageId (codice $ExitCode; rimozione non confermata)")
        } elseif ($Selective) {
            Save-UninstalledComponent $PackageId
            if ($PackageId -eq 'Docker.DockerDesktop') { Save-RetainedImage '' }
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
    if ($Selective -and $PSScriptRoot -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'remove-wsl-windows.ps1'))) {
        $WslCleanup = Join-Path $PSScriptRoot 'remove-wsl-windows.ps1'
    }
    $PowerShell = Join-Path `
        $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    $CleanupArguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$WslCleanup`"")
    if ($Selective) {
        $CleanupArguments += @('-RequireEmpty', '-ExpectedUserSid', [Security.Principal.WindowsIdentity]::GetCurrent().User.Value)
    }
    $Cleanup = Start-Process `
        -FilePath $PowerShell `
        -ArgumentList $CleanupArguments `
        -Verb RunAs `
        -WindowStyle Hidden `
        -Wait `
        -PassThru
    if ($Cleanup.ExitCode -eq 2) {
        if ($Selective) { throw 'WSL conservato per proteggere dati personali; registro mantenuto.' }
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
    if ($Selective -and $Cleanup.ExitCode -eq 0) { Save-UninstalledComponent 'wsl' }
}

if ((-not $Selective -or 'project' -in $Selected) -and (Test-Path $SafeInstallDir)) {
    $null = Test-SafeInstallDirectory
    if ($Selective -and 'docker-image' -notin $Selected -and 'docker-data' -notin $Selected -and $RetainedImage) {
        Save-RetainedImage $RetainedImage
    }
    if ($Selective) {
        # VM/package/WSL operations may take time and change the project. Check
        # the complete tree again at the deletion boundary, not just at copy time.
        try { Assert-SelectedProjectBackup $SafeInstallDir $BackupPath } catch {
            Stop-WithMessage 'E29' 'Il progetto non corrisponde alla copia di sicurezza' `
                'La cartella progetto e il backup sono conservati. Le rimozioni già riuscite non sono annullate.' `
                @('Chiudi gli editor e i programmi che modificano il progetto.';
                  'Ripeti la selezione per creare una nuova copia di sicurezza.';
                  'Se ricompare, comunica E29 al docente.') $_.Exception.Message
        }
    }
    Remove-Item -LiteralPath $SafeInstallDir -Recurse -Force
}

if (-not $Selective -and (Test-Path $StateDir)) {
    Remove-Item -LiteralPath $StateDir -Recurse -Force
}

if (-not $Selective -or 'project' -in $Selected -or 'wsl' -in $Selected) {
    $RunOncePath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
    Remove-ItemProperty `
        -Path $RunOncePath `
        -Name "2cornot2c-resume" `
        -ErrorAction SilentlyContinue
}

if ($Selective -and 'shortcuts' -notin $Selected) {
    Write-Host 'Rimozione selezionata completata. Registro e collegamenti conservati.'
    exit 0
}

$ShortcutCleanup = Join-Path `
    $LauncherDir "remove-classroom-shortcuts-windows.ps1"
$ShortcutCleanupSucceeded = $false
if (Test-Path $ShortcutCleanup) {
    $CleanupPowerShell = Join-Path `
        $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
    & $CleanupPowerShell `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $ShortcutCleanup
    $ShortcutCleanupSucceeded = $LASTEXITCODE -eq 0
}
if (-not $ShortcutCleanupSucceeded) {
    Write-Warning (
        "Uso la pulizia collegamenti integrata perché lo script dedicato " +
        "non è disponibile."
    )
    foreach ($ShortcutPath in Get-ClassroomShortcutPaths) {
        if (Test-Path $ShortcutPath) {
            Remove-Item -LiteralPath $ShortcutPath -Force
        }
    }
}
if (-not $Selective -and (Test-Path $LauncherDir)) {
    Remove-Item -LiteralPath $LauncherDir -Recurse -Force
}

Write-Host "Disinstallazione completata."
if ($BackupPath) {
    Write-Host "Dati conservati in: $BackupPath"
}
