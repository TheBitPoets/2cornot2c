[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$CodexHome = (Join-Path $env:USERPROFILE ".codex"),
    [string]$TemplatePath = "",
    [string]$AgentsTemplatePath = "",
    [switch]$Overwrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
if (-not $TemplatePath) {
    $TemplatePath = Join-Path $repoRoot "config\codex\codex-system.config.toml"
}
if (-not $AgentsTemplatePath) {
    $AgentsTemplatePath = Join-Path $repoRoot "config\codex\AGENTS.md"
}

function New-Backup {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = "$Path.bak-$stamp"
    Copy-Item -LiteralPath $Path -Destination $backup
    return $backup
}

function Set-Or-AddTopLevelString {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $line = "$Key = `"$Value`""
    $pattern = "(?m)^$([regex]::Escape($Key))\s*=\s*`"[^`"]*`""
    if ($Text -match $pattern) {
        return [regex]::Replace($Text, $pattern, $line)
    }
    return $line + "`r`n" + $Text
}

function Remove-Section {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$SectionName
    )

    $escaped = [regex]::Escape($SectionName)
    $pattern = "(?ms)^\[$escaped\]\s*.*?(?=^\[[^\]]+\]\s*|\z)"
    return [regex]::Replace($Text, $pattern, "").TrimEnd() + "`r`n"
}

function Merge-CodexConfig {
    param(
        [Parameter(Mandatory = $true)][string]$CurrentText,
        [Parameter(Mandatory = $true)][string]$TemplateText
    )

    $result = $CurrentText
    foreach ($key in @("model", "model_reasoning_effort", "service_tier")) {
        $match = [regex]::Match($TemplateText, "(?m)^$key\s*=\s*`"([^`"]+)`"")
        if ($match.Success) {
            $result = Set-Or-AddTopLevelString -Text $result -Key $key -Value $match.Groups[1].Value
        }
    }

    $agentsMatch = [regex]::Match($TemplateText, "(?ms)^\[agents\]\s*.*?(?=^\[[^\]]+\]\s*|\z)")
    if ($agentsMatch.Success) {
        $result = Remove-Section -Text $result -SectionName "agents"
        $result = $result.TrimEnd() + "`r`n`r`n" + $agentsMatch.Value.Trim() + "`r`n"
    }

    return $result
}

$resolvedCodexHome = [System.IO.Path]::GetFullPath($CodexHome)
$resolvedTemplatePath = [System.IO.Path]::GetFullPath($TemplatePath)
$resolvedAgentsTemplatePath = [System.IO.Path]::GetFullPath($AgentsTemplatePath)
$configPath = Join-Path $resolvedCodexHome "config.toml"
$agentsPath = Join-Path $resolvedCodexHome "AGENTS.md"

if (-not (Test-Path -LiteralPath $resolvedTemplatePath)) {
    throw "Template TOML non trovato: $resolvedTemplatePath"
}
if (-not (Test-Path -LiteralPath $resolvedAgentsTemplatePath)) {
    throw "Template AGENTS.md non trovato: $resolvedAgentsTemplatePath"
}

if ($PSCmdlet.ShouldProcess($resolvedCodexHome, "Install Codex system configuration")) {
    New-Item -ItemType Directory -Force -Path $resolvedCodexHome | Out-Null

    $template = Get-Content -LiteralPath $resolvedTemplatePath -Raw
    $configBackup = New-Backup -Path $configPath
    if ($Overwrite -or -not (Test-Path -LiteralPath $configPath)) {
        Set-Content -LiteralPath $configPath -Value $template -Encoding utf8
    } else {
        $current = Get-Content -LiteralPath $configPath -Raw
        $merged = Merge-CodexConfig -CurrentText $current -TemplateText $template
        Set-Content -LiteralPath $configPath -Value $merged -Encoding utf8
    }

    $agentsBackup = New-Backup -Path $agentsPath
    Copy-Item -LiteralPath $resolvedAgentsTemplatePath -Destination $agentsPath -Force

    Write-Output "Configurazione Codex installata in: $resolvedCodexHome"
    if ($configBackup) {
        Write-Output "Backup config.toml: $configBackup"
    }
    if ($agentsBackup) {
        Write-Output "Backup AGENTS.md: $agentsBackup"
    }
    Write-Output "Riavvia VS Code, Codex CLI o ChatGPT desktop per caricare le nuove impostazioni."
}
