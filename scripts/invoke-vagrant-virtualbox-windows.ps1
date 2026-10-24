param(
    [ValidateSet("up", "reload")]
    [string]$Action = "up",
    [int]$RecoveryAfterSeconds = 75,
    [string]$VagrantCommand,
    [string]$VBoxManageCommand
)

$ErrorActionPreference = "Stop"

function Get-ClassroomVirtualBoxId {
    $IdPath = Join-Path (Get-Location) `
        ".vagrant\machines\default\virtualbox\id"
    if (-not (Test-Path $IdPath)) {
        return $null
    }

    $Id = (Get-Content $IdPath -Raw).Trim()
    if ($Id -notmatch `
        "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$") {
        return $null
    }
    return $Id
}

function Get-VirtualBoxState {
    param(
        [string]$VBoxManage,
        [string]$MachineId
    )

    $Info = & $VBoxManage showvminfo $MachineId --machinereadable `
        2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    $StateLine = $Info | Where-Object { $_ -match '^VMState=' } |
        Select-Object -First 1
    if ($StateLine -match '^VMState="([^"]+)"') {
        return $Matches[1]
    }
    return $null
}

function Test-GuestAdditionsActive {
    param(
        [string]$VBoxManage,
        [string]$MachineId
    )

    $Version = & $VBoxManage guestproperty get $MachineId `
        "/VirtualBox/GuestAdd/Version" 2>$null
    return (
        $LASTEXITCODE -eq 0 -and
        $Version -match '^Value:\s+\S+'
    )
}

if (-not $VagrantCommand) {
    $VagrantLookup = Get-Command vagrant -ErrorAction SilentlyContinue
    $VagrantCommand = if ($VagrantLookup) {
        $VagrantLookup.Source
    } else {
        Join-Path $env:ProgramFiles "Vagrant\bin\vagrant.exe"
    }
}
if (-not (Test-Path $VagrantCommand)) {
    throw "Vagrant non è installato."
}

if (-not $VBoxManageCommand) {
    $VBoxLookup = Get-Command VBoxManage -ErrorAction SilentlyContinue
    $VBoxManageCommand = if ($VBoxLookup) {
        $VBoxLookup.Source
    } else {
        Join-Path $env:ProgramFiles "Oracle\VirtualBox\VBoxManage.exe"
    }
}
if (-not (Test-Path $VBoxManageCommand)) {
    $VBoxManageCommand = $null
}

Write-Host "Avvio della macchina virtuale..." -ForegroundColor Cyan
$VagrantArguments = @($Action)
if ($Action -eq "up") {
    $VagrantArguments += "--provider=virtualbox"
}
$Process = Start-Process -FilePath $VagrantCommand `
    -ArgumentList $VagrantArguments `
    -NoNewWindow -PassThru

$RunningSince = $null
$RecoveryAttempted = $false
$PausedByUs = $false

try {
    while (-not $Process.HasExited) {
        Start-Sleep -Seconds 2
        $Process.Refresh()

        if ($RecoveryAttempted -or -not $VBoxManageCommand) {
            continue
        }

        $MachineId = Get-ClassroomVirtualBoxId
        if (-not $MachineId) {
            $RunningSince = $null
            continue
        }

        $State = Get-VirtualBoxState `
            -VBoxManage $VBoxManageCommand `
            -MachineId $MachineId
        if ($State -ne "running") {
            $RunningSince = $null
            continue
        }
        if (Test-GuestAdditionsActive `
            -VBoxManage $VBoxManageCommand `
            -MachineId $MachineId) {
            $RecoveryAttempted = $true
            continue
        }

        if (-not $RunningSince) {
            $RunningSince = Get-Date
            continue
        }
        if (((Get-Date) - $RunningSince).TotalSeconds -lt `
            $RecoveryAfterSeconds) {
            continue
        }

        $RecoveryAttempted = $true
        Write-Host ""
        Write-Host (
            "L'avvio sta impiegando più del previsto. " +
            "Provo a sbloccarlo automaticamente: non devi fare nulla."
        ) -ForegroundColor Yellow

        & $VBoxManageCommand controlvm $MachineId pause
        if ($LASTEXITCODE -ne 0) {
            Write-Host (
                "Il tentativo automatico non è riuscito; " +
                "l'avvio normale continua."
            ) -ForegroundColor Yellow
            continue
        }

        $PausedByUs = $true
        Start-Sleep -Seconds 2
        foreach ($Attempt in 1..3) {
            & $VBoxManageCommand controlvm $MachineId resume
            if ($LASTEXITCODE -eq 0) {
                $PausedByUs = $false
                Write-Host (
                    "Macchina ripresa. Attendo il completamento dell'avvio..."
                ) -ForegroundColor Green
                break
            }
            Start-Sleep -Seconds 1
        }
        if ($PausedByUs) {
            throw (
                "VirtualBox non è riuscito a riprendere la macchina. " +
                "Chiudi la finestra e scegli di nuovo Avvia ambiente."
            )
        }
    }
}
catch {
    if (-not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
    }
    throw
}
finally {
    if ($PausedByUs -and $VBoxManageCommand) {
        & $VBoxManageCommand controlvm $MachineId resume `
            2>$null
    }
}

$Process.WaitForExit()
exit $Process.ExitCode
