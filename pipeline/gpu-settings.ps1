param(
    [ValidateSet('Saved','Laptop','RTX5090')][string]$Profile = 'Saved',
    [ValidateRange(256,24576)][int]$TexturePoolMB,
    [ValidateRange(64,4096)][int]$NanitePoolMB,
    [ValidateRange(256,8192)][int]$RayTracingPoolMB,
    [ValidateRange(640,3840)][int]$Width,
    [ValidateRange(360,2160)][int]$Height,
    [ValidateRange(25,100)][int]$ScreenPercentage,
    [ValidateRange(15,120)][int]$MaxFPS,
    [ValidateRange(2,80)][int]$MaxBitrateMbps,
    [switch]$Save,
    [switch]$Json
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$catalog = Get-Content (Join-Path $projectRoot 'Config/gpu-profiles.json') -Raw | ConvertFrom-Json
$settingsPath = Join-Path $projectRoot '.local/gpu-settings.json'
$saved = $null
if ($Profile -eq 'Saved' -and (Test-Path -LiteralPath $settingsPath)) {
    $saved = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
    $Profile = $saved.profile
}
if ($Profile -eq 'Saved') {
    $adapters = Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue
    $Profile = if ($adapters.Name -match 'RTX 5090') { 'RTX5090' } else { 'Laptop' }
}
if ($Profile -notin @('Laptop','RTX5090')) { throw 'Unknown saved GPU profile.' }
$settings = [ordered]@{ profile = $Profile }
foreach ($property in $catalog.profiles.$Profile.PSObject.Properties) { $settings[$property.Name] = $property.Value }
$ranges = @{
    texturePoolMB = @(256,24576); nanitePoolMB = @(64,4096); rayTracingPoolMB = @(256,8192)
    width = @(640,3840); height = @(360,2160); screenPercentage = @(25,100)
    maxFPS = @(15,120); maxBitrateMbps = @(2,80); lightingQuality = @(2,3)
}
foreach ($key in $ranges.Keys) {
    if ($saved -and $null -ne $saved.$key) { $settings[$key] = $saved.$key }
    if ($PSBoundParameters.ContainsKey($key)) { $settings[$key] = $PSBoundParameters[$key] }
    $number = 0
    if (-not [int]::TryParse([string]$settings[$key], [ref]$number) -or
        $number -lt $ranges[$key][0] -or $number -gt $ranges[$key][1]) {
        throw "Invalid GPU setting: $key"
    }
    $settings[$key] = $number
}
# These are pool budgets, not a cap on total GPU memory. RT acceleration
# structures, render targets, the driver and other apps also consume VRAM.
if ($Save) {
    New-Item -ItemType Directory -Path (Split-Path $settingsPath -Parent) -Force | Out-Null
    $settings | ConvertTo-Json | Set-Content -LiteralPath $settingsPath
}
if ($Json) { $settings | ConvertTo-Json } else { [pscustomobject]$settings }
