param([ValidateSet('Status','Balanced','Performance','Restore')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$statePath = Join-Path $projectRoot '.local/windows-power.json'
function Get-CurrentScheme {
    $line = (& powercfg.exe /getactivescheme) -join ' '
    if ($LASTEXITCODE -ne 0 -or $line -notmatch '([0-9a-fA-F-]{36})\s+\(([^)]+)\)') { throw 'Windows power settings are unavailable.' }
    @{ guid = $Matches[1]; name = $Matches[2] }
}
$active = Get-CurrentScheme
$previous = $null
if (Test-Path -LiteralPath $statePath) { $previous = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json }
$balanced = '381b4222-f694-41f0-9685-ff5bb260df2e'
$performance = $null
foreach ($line in (& powercfg.exe /list)) {
    if ($line -match '([0-9a-fA-F-]{36})\s+\(([^)]+)\)' -and
        ($Matches[1] -eq '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c' -or $Matches[2] -eq 'High performance')) {
        $performance = $Matches[1]; break
    }
}
$target = if ($Action -eq 'Balanced') { $balanced } elseif ($Action -eq 'Performance') { $performance } else { $null }
if ($Action -eq 'Performance' -and -not $target) { throw 'This PC does not have a High performance power plan.' }
if ($target -and $active.guid -ne $target) {
    if (-not $previous) {
        New-Item -ItemType Directory -Path (Split-Path $statePath -Parent) -Force | Out-Null
        $active | ConvertTo-Json | Set-Content -LiteralPath $statePath
        $previous = [PSCustomObject]$active
    }
    & powercfg.exe /setactive $target
    if ($LASTEXITCODE -ne 0) { throw 'Windows could not change the power plan.' }
    $active = Get-CurrentScheme
} elseif ($Action -eq 'Restore') {
    if (-not $previous -or $previous.guid -notmatch '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') {
        throw 'There is no saved power plan to restore.'
    }
    & powercfg.exe /setactive $previous.guid
    if ($LASTEXITCODE -ne 0) { throw 'Windows could not restore the previous power plan.' }
    Remove-Item -LiteralPath $statePath
    $previous = $null
    $active = Get-CurrentScheme
}
@{ name=$active.name; balanced=($active.guid -eq $balanced); performance=($active.guid -eq $performance); performanceAvailable=[bool]$performance; previousName=$(if($previous){$previous.name}else{''}); canRestore=[bool]$previous } | ConvertTo-Json -Compress
