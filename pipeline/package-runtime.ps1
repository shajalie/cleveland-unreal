param([string]$EngineRoot, [switch]$SkipBuild, [switch]$SkipCook)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $projectRoot 'runtime/ClevelandReal/ClevelandReal.uproject'
if (-not $EngineRoot) {
    $doctor = & (Join-Path $PSScriptRoot 'doctor.ps1') -Json | ConvertFrom-Json
    $editor = $doctor.UnrealEditors | Select-Object -Last 1
    if (-not $editor) { throw 'Unreal Engine is required to produce a packaged application.' }
    $EngineRoot = [IO.Path]::GetFullPath((Join-Path (Split-Path $editor -Parent) '../../..'))
}
$completed = Get-Content (Join-Path $projectRoot 'reports/unreal-import.json') -Raw | ConvertFrom-Json
if ($completed.map -notmatch '^/Game/Cleveland/Maps/[A-Za-z0-9_/]+$') { throw 'Invalid completed map path.' }
if (-not $SkipBuild) { & (Join-Path $PSScriptRoot 'build-runtime.ps1') -EngineRoot $EngineRoot -Game }
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$archive = Join-Path $projectRoot "Builds/cooked-$stamp"
$priorSdk = $env:UE_SDKS_ROOT
$priorCompatibility = $env:__COMPAT_LAYER
try {
    $portableSdk = Join-Path $projectRoot '.local/autosdk'
    if (Test-Path -LiteralPath $portableSdk) { $env:UE_SDKS_ROOT = $portableSdk }
    $env:__COMPAT_LAYER = (($priorCompatibility + ' HIGHDPIAWARE').Trim())
    $automation = Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat'
    $cookOption = if ($SkipCook) { '-skipcook' } else { '-cook' }
    & $automation BuildCookRun "-project=$project" -noP4 -platform=Win64 -clientconfig=Development -skipbuild $cookOption -stage -pak -archive "-archivedirectory=$archive" "-map=$($completed.map)" -prereqs -unattended -utf8output -nocompileeditor -skipbuildeditor
    if ($LASTEXITCODE -ne 0) { throw "Unreal packaging failed ($LASTEXITCODE)." }
    $executable = Join-Path $archive 'Windows/ClevelandReal.exe'
    if (-not (Test-Path -LiteralPath $executable)) { throw 'Packaging did not produce a runnable executable.' }
    $archive | Set-Content (Join-Path $projectRoot '.local/latest-cooked-build.txt')
    Write-Output "Cooked application: $archive"
} finally {
    $env:UE_SDKS_ROOT = $priorSdk
    $env:__COMPAT_LAYER = $priorCompatibility
}
