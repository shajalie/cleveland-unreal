param(
    [string]$EngineRoot,
    [ValidateSet('Saved','Laptop','RTX5090')][string]$Profile = 'Saved'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$frontend = Join-Path $projectRoot '.local\pixel-streaming-infrastructure\SignallingWebServer\www\player.html'
if (-not (Test-Path -LiteralPath $frontend)) { throw 'Run pipeline/setup-streaming.ps1 first.' }
$health = $null
try { $health = Invoke-RestMethod 'http://127.0.0.1:5190/health' -TimeoutSec 2 } catch {}
if ($health -and $health.service -ne 'Cleveland Unreal preview') { throw 'Preview port belongs to another service.' }
if (-not $health) {
    $node = Join-Path $projectRoot 'tools/node/node.exe'
    if (-not (Test-Path -LiteralPath $node)) { $node = (Get-Command node.exe).Source }
    $server = Start-Process -FilePath $node -ArgumentList 'stream/server.cjs' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.local\stream-preview.log') -RedirectStandardError (Join-Path $projectRoot '.local\stream-preview-error.log') -PassThru
    $server.Id | Set-Content (Join-Path $projectRoot '.local\stream-preview.pid')
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        try { $health = Invoke-RestMethod 'http://127.0.0.1:5190/health' -TimeoutSec 1; break } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $health) { throw 'Preview server did not become ready.' }
}
$existing = Join-Path $projectRoot '.local\unreal-preview.pid'
if (Test-Path -LiteralPath $existing) {
    $running = Get-Process -Id ([int](Get-Content $existing)) -ErrorAction SilentlyContinue
    if ($running -and $running.ProcessName -match '^(UnrealEditor|ClevelandReal.*)$') { throw 'An Unreal preview is already running.' }
}
& (Join-Path $PSScriptRoot 'launch.ps1') -EngineRoot $EngineRoot -Stream -Profile $Profile
Write-Output 'Local Chrome preview: http://127.0.0.1:5190/'
Write-Output 'Authenticated remote access is still being integrated.'
