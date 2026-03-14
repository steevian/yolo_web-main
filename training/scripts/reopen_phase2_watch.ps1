param(
    [string]$Repo = 'D:\cyd\Desktop\yolo_web-main'
)

$ErrorActionPreference = 'Stop'
Set-Location $Repo

$root = Join-Path $Repo 'experiments/YOLOv11-S'
if (-not (Test-Path $root)) {
    throw "Run root not found: $root"
}

$latest = Get-ChildItem -Path $root -Directory |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $latest) {
    throw "No run directory found under $root"
}

$log = Join-Path $latest.FullName 'train.log'
Write-Host "active_run=$($latest.Name)"
Write-Host "log=$log"

if (-not (Test-Path $log)) {
    throw "train.log not found for active run: $log"
}

Get-Content $log -Wait -Tail 120
