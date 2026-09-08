param([string]$EngineRoot)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $EngineRoot) {
    $diagnostic = & (Join-Path $PSScriptRoot 'doctor.ps1') -Json | ConvertFrom-Json
    $editor = $diagnostic.UnrealEditors | Select-Object -Last 1
    if (-not $editor) { throw 'Unreal Engine was not found. Supply -EngineRoot.' }
    $EngineRoot = [IO.Path]::GetFullPath((Join-Path (Split-Path $editor -Parent) '..\..\..'))
}
$commandlet = Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
$project = Join-Path $projectRoot 'runtime\ClevelandReal\ClevelandReal.uproject'
$script = Join-Path $PSScriptRoot 'unreal\import_scene.py'
$usd = Join-Path $projectRoot 'SourceAssets\UnrealTransfer\Cleveland.usdc'
$report = Join-Path $projectRoot 'reports\unreal-import.json'
if (-not (Test-Path -LiteralPath $usd)) { throw 'Export the authoring scene using export_unreal.py first.' }
New-Item -ItemType Directory -Path (Join-Path $projectRoot '.local') -Force | Out-Null
$log = Join-Path $projectRoot '.local\unreal-import.log'
$started = [DateTime]::UtcNow
& $commandlet $project -run=pythonscript "-script=$script" -unattended -NullRHI -nosplash -stdout -FullStdOutLogOutput *> $log
$exitCode = $LASTEXITCODE
$freshReport = (Test-Path -LiteralPath $report) -and (Get-Item -LiteralPath $report).LastWriteTimeUtc -gt $started
if ($exitCode -ne 0 -or -not $freshReport) {
    $failure = if (Select-String -LiteralPath $log -Pattern 'ResolutionTooLow' -Quiet) {
        'Windows reported a display below the engine minimum; import did not run.'
    } else { 'Unreal did not produce a fresh import report. Inspect the local log.' }
    throw "$failure Exit code: $exitCode. Log: $log"
}
Get-Content -LiteralPath $report -Raw
