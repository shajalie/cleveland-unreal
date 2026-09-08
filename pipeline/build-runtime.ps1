param(
    [string]$EngineRoot,
    [string]$PortableToolchain,
    [ValidateSet('Development','Shipping')][string]$Configuration = 'Development',
    [switch]$Game
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$project = Join-Path $projectRoot 'runtime\ClevelandReal\ClevelandReal.uproject'
if (-not $EngineRoot) {
    $diagnostic = & (Join-Path $PSScriptRoot 'doctor.ps1') -Json | ConvertFrom-Json
    $editor = $diagnostic.UnrealEditors | Select-Object -Last 1
    if (-not $editor) { throw 'Unreal Engine 5.8 was not found. Supply -EngineRoot.' }
    $EngineRoot = [IO.Path]::GetFullPath((Join-Path (Split-Path $editor -Parent) '..\..\..'))
}
$builder = Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
if (-not (Test-Path -LiteralPath $builder)) { throw "Unreal build script missing: $builder" }
if (-not $PortableToolchain) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $projectRoot '..\..\tools\msvc-2022'))
    if (Test-Path -LiteralPath $candidate) { $PortableToolchain = $candidate }
}
$priorSdkRoot = $env:UE_SDKS_ROOT
try {
    if ($PortableToolchain) {
        $toolchain = (Resolve-Path -LiteralPath $PortableToolchain).Path
        $sdkRoot = Join-Path $projectRoot '.local\autosdk'
        $hostRoot = Join-Path $sdkRoot 'HostWin64\Win64'
        New-Item -ItemType Directory -Path $hostRoot -Force | Out-Null
        $junctions = @{
            'VS2022' = Join-Path $toolchain 'VC\Tools\MSVC'
            'Windows Kits' = Join-Path $toolchain 'Windows Kits'
        }
        foreach ($name in $junctions.Keys) {
            $destination = (Resolve-Path -LiteralPath $junctions[$name]).Path
            $link = Join-Path $hostRoot $name
            if (Test-Path -LiteralPath $link) {
                $existing = Get-Item -LiteralPath $link
                if ($existing.LinkType -ne 'Junction' -or $existing.Target -ne $destination) {
                    throw "Existing AutoSDK path points elsewhere: $link"
                }
            } else {
                New-Item -ItemType Junction -Path $link -Target $destination | Out-Null
            }
        }
        $env:UE_SDKS_ROOT = $sdkRoot
    }
    $target = if ($Game) { 'ClevelandReal' } else { 'ClevelandRealEditor' }
    if (-not $Game -and $Configuration -eq 'Shipping') { throw 'Editor cannot use Shipping configuration.' }
    & $builder $target Win64 $Configuration $project -WaitMutex -Compiler=VisualStudio2022
    if ($LASTEXITCODE -ne 0) { throw "Unreal compilation failed ($LASTEXITCODE)." }
} finally {
    $env:UE_SDKS_ROOT = $priorSdkRoot
}
