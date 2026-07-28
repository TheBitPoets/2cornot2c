$ErrorActionPreference = "Stop"

$Distributions = @(
    & wsl.exe --list --quiet 2>$null |
        ForEach-Object { ([string]$_).Trim() } |
        Where-Object { $_ }
)
$PersonalDistributions = @(
    $Distributions |
        Where-Object { $_ -notmatch "^docker-desktop(?:-data)?$" }
)
if ($PersonalDistributions.Count -gt 0) {
    Write-Error (
        "WSL contiene distribuzioni non create da 2cornot2c: " +
        ($PersonalDistributions -join ", ") +
        ". WSL viene conservato per non cancellare dati personali."
    )
    exit 2
}

foreach ($Distribution in $Distributions) {
    & wsl.exe --unregister $Distribution
}
& wsl.exe --shutdown 2>$null
& wsl.exe --uninstall 2>$null

Get-AppxPackage "MicrosoftCorporationII.WindowsSubsystemForLinux" |
    Remove-AppxPackage -ErrorAction SilentlyContinue

foreach ($Feature in @(
    "VirtualMachinePlatform"
    "Microsoft-Windows-Subsystem-Linux"
)) {
    & dism.exe /online /disable-feature `
        /featurename:$Feature /norestart | Out-Null
}

$RemainingApp = Get-AppxPackage `
    "MicrosoftCorporationII.WindowsSubsystemForLinux" `
    -ErrorAction SilentlyContinue
$RemainingFeatures = @(
    foreach ($Feature in @(
        "VirtualMachinePlatform"
        "Microsoft-Windows-Subsystem-Linux"
    )) {
        $FeatureState = Get-WindowsOptionalFeature `
            -Online `
            -FeatureName $Feature `
            -ErrorAction SilentlyContinue
        if ($FeatureState -and $FeatureState.State -ne "Disabled") {
            $Feature
        }
    }
)
if ($RemainingApp -or $RemainingFeatures.Count -gt 0) {
    Write-Error (
        "La verifica finale rileva ancora WSL: " +
        ($RemainingFeatures -join ", ")
    )
    exit 3
}

Write-Host "WSL installato da 2cornot2c è stato rimosso."
