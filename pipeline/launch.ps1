param(
    [string]$EngineRoot,
    [switch]$Walk,
    [switch]$Stream,
    [switch]$Verify,
    [ValidateSet('Saved','Laptop','RTX5090')][string]$Profile = 'Saved',
    [ValidateSet('Laptop','High')][string]$Quality
)
$ErrorActionPreference = 'Stop'
if ($Stream) { $Walk = $true }
$projectRoot = Split-Path $PSScriptRoot -Parent
# Keep the earlier -Quality interface working; all new launches use saved profiles.
if ($Quality) { $Profile = if ($Quality -eq 'High') { 'RTX5090' } else { 'Laptop' } }
$gpu = & (Join-Path $PSScriptRoot 'gpu-settings.ps1') -Profile $Profile
$project = Join-Path $projectRoot 'runtime\ClevelandReal\ClevelandReal.uproject'
$packagedGame = Join-Path $projectRoot 'runtime\Windows\ClevelandReal.exe'
$isPackaged = Test-Path -LiteralPath $packagedGame
if ($isPackaged) {
    $editor = $packagedGame
    $Walk = $true
} elseif (-not (Test-Path -LiteralPath $project)) { throw 'Create the Unreal runtime project first.' }
elseif ($EngineRoot) {
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
    $report = Join-Path $projectRoot 'reports\unreal-import.json'
    if (-not (Test-Path -LiteralPath $report)) {
        throw 'The Unreal scene import has not completed. Run import-runtime.ps1 after building/exporting the scene.'
    }
    $completed = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    if ($completed.map -notmatch '^/Game/Cleveland/Maps/[A-Za-z0-9_/]+$') { throw 'Invalid completed map path.' }
    $map = Join-Path $projectRoot ('runtime/ClevelandReal/Content/' + $completed.map.Substring(6) + '.umap')
    if (-not $isPackaged -and -not (Test-Path -LiteralPath $map)) { throw 'The completed map file is missing.' }
    $arguments = @($completed.map, '-dx12', '-preferNvidia', '-log')
    if (-not $isPackaged) { $arguments = @(('"' + $project + '"')) + $arguments }
    $arguments += @('-game','-windowed')
    $arguments += @("-ResX=$($gpu.width)","-ResY=$($gpu.height)")
    $commands = "r.ScreenPercentage $($gpu.screenPercentage),t.MaxFPS $($gpu.maxFPS)"
    $commands += ",sg.GlobalIlluminationQuality $($gpu.lightingQuality),sg.ReflectionQuality $($gpu.lightingQuality)"
    $commands += ",r.Streaming.PoolSize $($gpu.texturePoolMB),r.Nanite.Streaming.StreamingPoolSize $($gpu.nanitePoolMB)"
    $commands += ",r.Shadow.Virtual.Enable $([int]$gpu.virtualShadows),r.RayTracing.Shadows 1"
    $arguments += ('-ExecCmds="' + $commands + '"')
}
if ($Stream) {
    $arguments += @('-RenderOffscreen', '-ForceRes', '-AudioMixer',
        '-PixelStreamingUseMediaCapture=false',
        '-PixelStreamingConnectionURL=ws://127.0.0.1:5191', '-PixelStreamingID=Cleveland',
        '-PixelStreamingEncoderCodec=H264', "-PixelStreamingWebRTCFps=$($gpu.maxFPS)",
        "-PixelStreamingWebRTCMaxBitrate=$($gpu.maxBitrateMbps * 1000000)")
}
if ($Verify) { $arguments += '-ClevelandVerify' }
$previousCompatibility = $env:__COMPAT_LAYER
try {
    $env:__COMPAT_LAYER = (($previousCompatibility + ' HIGHDPIAWARE').Trim())
    New-Item -ItemType Directory -Path (Join-Path $projectRoot '.local') -Force | Out-Null
    $workingDirectory = if ($isPackaged) { Split-Path $packagedGame -Parent } else { Split-Path $project -Parent }
    $launchOptions = @{ FilePath = $editor; ArgumentList = $arguments; WorkingDirectory = $workingDirectory; PassThru = $true }
    # Streaming renders offscreen. A normal launch intentionally opens the editor/game.
    if ($Stream) { $launchOptions.WindowStyle = 'Hidden' }
    $launched = Start-Process @launchOptions
    $launched.Id | Set-Content (Join-Path $projectRoot '.local\unreal-preview.pid')
    $gpu | ConvertTo-Json | Set-Content (Join-Path $projectRoot '.local\last-launch-gpu.json')
    Write-Output "Unreal process: $($launched.Id)"
    Write-Output "GPU profile: $($gpu.label); texture pool $($gpu.texturePoolMB) MB; geometry pool $($gpu.nanitePoolMB) MB"
} finally {
    $env:__COMPAT_LAYER = $previousCompatibility
}
