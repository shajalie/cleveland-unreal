param([ValidateSet('Start','Stop')][string]$Action)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $projectRoot 'runtime/ClevelandReal/ClevelandReal.uproject'
$packagedRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'runtime/Windows')) + '\'
function Get-PreviewProcesses {
    Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe' OR Name = 'ClevelandReal.exe'" | Where-Object {
        ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($packagedRoot,[StringComparison]::OrdinalIgnoreCase)) -or
        ($_.Name -eq 'UnrealEditor.exe' -and $_.CommandLine -and $_.CommandLine.Contains($project))
    }
}
$owned = @(Get-PreviewProcesses)
if ($Action -eq 'Stop') {
    # Termination is asynchronous: wait for the game to release its executable
    # and GPU DLLs. Re-query because a bootstrapper can spawn the real game
    # between the first process snapshot and its termination.
    for ($attempt = 0; $attempt -lt 12 -and $owned.Count; $attempt++) {
        foreach ($process in $owned) { Stop-Process -Id $process.ProcessId -ErrorAction SilentlyContinue }
        Wait-Process -Id $owned.ProcessId -Timeout 1 -ErrorAction SilentlyContinue
        # Windows may keep a terminated bootstrapper's CIM record briefly.
        Start-Sleep -Milliseconds 500
        $owned = @(Get-PreviewProcesses)
    }
    if ($owned.Count) { throw 'The renderer is still closing. Try again before replacing or restarting it.' }
    Write-Output 'Stopped this project preview'
} elseif ($owned.Count) { Write-Output 'This project is already running' }
else { & (Join-Path $PSScriptRoot 'launch.ps1') -Stream }
