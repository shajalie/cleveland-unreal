param(
    [string]$EngineRoot,
    [switch]$Walk,
    [ValidateSet('Laptop','High')][string]$Quality = 'Laptop'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $projectRoot 'runtime\ClevelandReal\ClevelandReal.uproject'
if (-not (Test-Path -LiteralPath $project)) { throw 'Create the Unreal runtime project first.' }
if ($EngineRoot) {
    $editor = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
} else {
    $doctor = & (Join-Path $PSScriptRoot 'doctor.ps1') -Json | ConvertFrom-Json
    $editor = $doctor.UnrealEditors | Select-Object -Last 1
}
if (-not $editor -or -not (Test-Path -LiteralPath $editor)) {
    throw 'Install Unreal Engine 5.8 through Epic Games Launcher, or supply -EngineRoot.'
}
$arguments = @(('"' + $project + '"'), '-dx12', '-preferNvidia', '-log')
if ($Walk) {
    $map = Join-Path $projectRoot 'runtime\ClevelandReal\Content\Cleveland\Maps\Cleveland.umap'
    $report = Join-Path $projectRoot 'reports\unreal-import.json'
    if (-not (Test-Path -LiteralPath $map) -or -not (Test-Path -LiteralPath $report)) {
        throw 'The Unreal scene import has not completed. Run import-runtime.ps1 after building/exporting the scene.'
    }
    $arguments += @('-game','-windowed','-ResX=1280','-ResY=720')
    $screenPercentage = if ($Quality -eq 'Laptop') { 67 } else { 100 }
    $arguments += ('-ExecCmds="r.ScreenPercentage ' + $screenPercentage + ',t.MaxFPS 30"')
}
# Visible editor/game is intentional: this command opens the user's walkthrough.
Start-Process -FilePath $editor -ArgumentList $arguments -WorkingDirectory (Split-Path $project -Parent)
