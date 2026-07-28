$ErrorActionPreference = "Stop"

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

$Removed = 0
foreach ($ShortcutPath in $Candidates) {
    if (Test-Path -LiteralPath $ShortcutPath) {
        Remove-Item -LiteralPath $ShortcutPath -Force
        $Removed++
        Write-Host "Collegamento rimosso: $ShortcutPath"
    }
}

$IconRefresh = Join-Path $env:SystemRoot "System32\ie4uinit.exe"
if (Test-Path $IconRefresh) {
    & $IconRefresh -show
}

if ($Removed -eq 0) {
    Write-Host "Nessun collegamento 2cornot2c residuo trovato."
} else {
    Write-Host "Pulizia dei collegamenti completata."
}
