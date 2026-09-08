param([ValidateSet('enable','disable')][string]$Action)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$command = Get-Command tailscale.exe -ErrorAction SilentlyContinue
if (-not $command) { throw 'Install Tailscale on this PC and sign in, then enable the private link.' }
$tailscale = $command.Source
$status = & $tailscale status --json | ConvertFrom-Json
if ($status.BackendState -ne 'Running') { throw 'Sign into Tailscale on the rendering PC first.' }
$hostName = $status.Self.DNSName.TrimEnd('.')
$owner = $status.User.PSObject.Properties[[string]$status.Self.UserID].Value.LoginName
if (-not $hostName.EndsWith('.ts.net') -or -not $owner) { throw 'A personal Tailscale identity is required.' }
$configPath = Join-Path $projectRoot '.local/tailscale.json'
if ($Action -eq 'enable') {
    $existing = & $tailscale serve status --json | ConvertFrom-Json
    $handler = $existing.Web.PSObject.Properties[($hostName + ':5190')].Value.Handlers.'/'.Proxy
    if ($handler -and $handler -ne 'http://127.0.0.1:5190') { throw 'Tailscale port 5190 belongs to another app.' }
    & $tailscale serve --bg --https=5190 http://127.0.0.1:5190 | Out-Null
} else { & $tailscale serve --https=5190 off | Out-Null }
if ($LASTEXITCODE -ne 0) { throw 'Tailscale could not update this application route.' }
$settings = @{ enabled=($Action -eq 'enable'); url="https://${hostName}:5190/"; emails=@($owner.ToLower()) }
New-Item -ItemType Directory -Path (Split-Path $configPath -Parent) -Force | Out-Null
$settings | ConvertTo-Json | Set-Content -LiteralPath $configPath
@{enabled=$settings.enabled;url=$settings.url} | ConvertTo-Json
