param([ValidateSet('Start','Stop')][string]$Action)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $projectRoot 'runtime/ClevelandReal/ClevelandReal.uproject'
$packagedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runtime/Windows')) + '\'
$owned = @(Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe' OR Name = 'ClevelandReal.exe'" | Where-Object {
    ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($packagedRoot,[StringComparison]::OrdinalIgnoreCase)) -or
    ($_.Name -eq 'UnrealEditor.exe' -and $_.CommandLine -and $_.CommandLine.Contains($project))
})
if ($Action -eq 'Stop') {
    foreach ($process in $owned) { Stop-Process -Id $process.ProcessId -ErrorAction SilentlyContinue }
    Write-Output 'Stopped this project preview'
} elseif ($owned.Count) { Write-Output 'This project is already running' }
else { & (Join-Path $PSScriptRoot 'launch.ps1') -Stream }
