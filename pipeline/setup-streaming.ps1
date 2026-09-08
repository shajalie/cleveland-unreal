param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$dependency = Get-Content (Join-Path $projectRoot 'stream\dependency.json') -Raw | ConvertFrom-Json
$checkout = Join-Path $projectRoot $dependency.installDirectory
if (-not (Test-Path -LiteralPath $checkout)) {
    git init $checkout
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the streaming dependency checkout.' }
    git -C $checkout remote add origin $dependency.repository
    if ($LASTEXITCODE -ne 0) { throw 'Could not configure the Epic source repository.' }
    git -C $checkout fetch --depth 1 origin $dependency.commit
    if ($LASTEXITCODE -ne 0) { throw 'Could not download the reviewed streaming revision.' }
    git -C $checkout checkout --detach FETCH_HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Could not check out the reviewed streaming revision.' }
}
$revision = git -C $checkout rev-parse HEAD
if ($revision -ne $dependency.commit) {
    throw "Streaming dependency must be at the reviewed commit $($dependency.commit); found $revision."
}
Push-Location $checkout
try {
    npm.cmd ci --ignore-scripts --workspace Common --workspace Signalling --workspace SignallingWebServer --workspace Frontend/library --workspace Frontend/ui-library --workspace Frontend/implementations/typescript --include-workspace-root --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Streaming dependency installation failed.' }
    $steps = @(@('Common','build:cjs'), @('Signalling','build:cjs'), @('SignallingWebServer','build'), @('Frontend/library','build:cjs'), @('Frontend/ui-library','build:cjs'), @('Frontend/implementations/typescript','build:prod'))
    foreach ($step in $steps) {
        npm.cmd run $step[1] --workspace $step[0]
        if ($LASTEXITCODE -ne 0) { throw "Streaming build failed for $($step[0])." }
    }
} finally { Pop-Location }
