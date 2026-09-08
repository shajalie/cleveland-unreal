param(
    [string]$EngineRoot,
    [ValidateSet('Saved','Laptop','RTX5090')][string]$Profile = 'Saved'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.local/gpu-settings.json'))) {
    & (Join-Path $PSScriptRoot 'gpu-settings.ps1') -Profile $Profile -Save | Out-Null
}
$frontend = Join-Path $projectRoot '.local\pixel-streaming-infrastructure\SignallingWebServer\www\player.html'
if (-not (Test-Path -LiteralPath $frontend)) { throw 'Run pipeline/setup-streaming.ps1 first.' }
$health = $null
try { $health = Invoke-RestMethod 'http://127.0.0.1:5190/health' -TimeoutSec 2 } catch {}
if ($health -and $health.service -ne 'Cleveland Unreal preview') { throw 'Preview port belongs to another service.' }
if ($health -and $health.instance) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $expected = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($projectRoot.ToLower())))).Replace('-','').ToLower().Substring(0,16) } finally { $sha.Dispose() }
    if ($health.instance -ne $expected) { throw 'Another extracted copy is running. Stop that dashboard before starting this copy.' }
}
if (-not $health) {
    $node = Join-Path $projectRoot 'tools/node/node.exe'
    if (-not (Test-Path -LiteralPath $node)) { $node = (Get-Command node.exe).Source }
    $server = Start-Process -FilePath $node -ArgumentList 'stream/server.cjs' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.local\stream-preview.log') -RedirectStandardError (Join-Path $projectRoot '.local\stream-preview-error.log') -PassThru
    $server.Id | Set-Content (Join-Path $projectRoot '.local\stream-preview.pid')
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try { $health = Invoke-RestMethod 'http://127.0.0.1:5190/health' -TimeoutSec 1; break } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $health) { throw 'Preview server did not become ready.' }
}
if ($Profile -ne 'Saved') { & (Join-Path $PSScriptRoot 'gpu-settings.ps1') -Profile $Profile -Save | Out-Null }
& (Join-Path $PSScriptRoot 'runtime-control.ps1') -Action Start
Write-Output 'Local Chrome preview: http://127.0.0.1:5190/'
Write-Output 'Use Connection options in the dashboard for optional phone access.'
