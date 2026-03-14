$ErrorActionPreference = 'Stop'

$repo = 'D:\cyd\Desktop\yolo_web-main'
$python = 'C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe'
$baseBest = Join-Path $repo 'experiments\YOLOv11-S\baseline_20260310_141013\weights\best.pt'
$mbv3Best = Join-Path $repo 'experiments\YOLOv11-S-MBV3\mbv3_20260310_155214\weights\best.pt'

$phase4Root = Join-Path $repo 'experiments\YOLOv11-S-MBV3-ECA'
Write-Host "[CHAIN] Waiting for phase4 completion..."
while (-not (Test-Path $phase4Root)) {
    Start-Sleep -Seconds 20
}

$latestPhase4 = Get-ChildItem -Path $phase4Root -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
while (-not (Test-Path (Join-Path $latestPhase4.FullName 'run_summary.json'))) {
    Start-Sleep -Seconds 60
    $latestPhase4 = Get-ChildItem -Path $phase4Root -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

$mbv3EcaBest = Join-Path $latestPhase4.FullName 'weights\best.pt'

Write-Host "[CHAIN] Running phase5 evaluate/export/report..."
& $python "$repo\training\scripts\phase5_evaluate_all.py" --baseline $baseBest --mbv3 $mbv3Best --mbv3-eca $mbv3EcaBest
& $python "$repo\training\scripts\phase5_export_samples.py" --weights $mbv3EcaBest
& $python "$repo\training\scripts\phase5_generate_report.py"

Write-Host "[CHAIN] Done phase5."
