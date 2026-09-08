param([switch]$Json)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$engineCandidates = @()
$epicRegistry = 'HKLM:\SOFTWARE\EpicGames\Unreal Engine'
if (Test-Path $epicRegistry) {
    Get-ChildItem $epicRegistry | ForEach-Object {
        $engineLocation = (Get-ItemProperty $_.PSPath).InstalledDirectory
        if ($engineLocation) { $engineCandidates += Join-Path $engineLocation 'Engine\Binaries\Win64\UnrealEditor.exe' }
    }
}
foreach ($engineRoot in @('C:\Program Files\Epic Games','C:\Unreal','C:\Users\sammy\Documents\sunsimulationhouses\tools')) {
    if (Test-Path $engineRoot) {
        Get-ChildItem $engineRoot -Directory -Filter 'UE_*' | ForEach-Object {
            $engineCandidates += Join-Path $_.FullName 'Engine\Binaries\Win64\UnrealEditor.exe'
        }
    }
}
$engines = @($engineCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -Unique)
$gpuCommand = Get-Command nvidia-smi -ErrorAction SilentlyContinue
$gpu = if ($gpuCommand) { & $gpuCommand.Source --query-gpu=name,memory.total,driver_version --format=csv,noheader } else { 'NVIDIA driver utility unavailable' }
$disk = Get-PSDrive -Name ([System.IO.Path]::GetPathRoot($projectRoot).Substring(0,1))
$result = [ordered]@{
    Project = $projectRoot
    UnrealEditors = $engines
    UnrealInstalled = $engines.Count -gt 0
    NvidiaGpu = $gpu
    FreeDiskGB = [math]::Round($disk.Free / 1GB,1)
    EditableSceneExists = Test-Path (Join-Path $projectRoot 'SourceAssets\Cleveland-Reconstruction.blend')
    RuntimeStatus = 'Not built or tested; engine installation required'
}
if ($Json) { $result | ConvertTo-Json -Depth 4 } else { [pscustomobject]$result | Format-List }
