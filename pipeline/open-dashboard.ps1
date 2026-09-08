$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
& (Join-Path $PSScriptRoot 'stream.ps1')
$candidates = @(
    (Join-Path $env:ProgramFiles 'Google/Chrome/Application/chrome.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Google/Chrome/Application/chrome.exe'),
    (Join-Path $env:LOCALAPPDATA 'Google/Chrome/Application/chrome.exe')
)
$chrome = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($chrome) { Start-Process -FilePath $chrome -ArgumentList 'http://127.0.0.1:5190/' }
else { Write-Output 'Open Chrome at http://127.0.0.1:5190/' }
