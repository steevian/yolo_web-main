$ErrorActionPreference = 'Stop'

$repo = 'D:\cyd\Desktop\yolo_web-main'
$python = 'C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe'
$env:KMP_DUPLICATE_LIB_OK = 'TRUE'
$thesisBatch = 6
$thesisDataYaml = (Join-Path $repo 'training\configs\data_3seasonweeddet10.yaml')

function Assert-LastExitCode([string]$stageName) {
    if ($LASTEXITCODE -ne 0) {
        throw "[FORMAL] $stageName failed with exit code $LASTEXITCODE"
    }
}

function Get-LatestRunDirWithBest([string]$rootPath) {
    $dirs = Get-ChildItem -Path $rootPath -Directory | Sort-Object LastWriteTime -Descending
    foreach ($d in $dirs) {
        $best = Join-Path $d.FullName 'weights\best.pt'
        if (Test-Path $best) {
            return $d
        }
    }
    throw "[FORMAL] No valid run with weights\\best.pt found under $rootPath"
}

function Read-RunArgValue([string]$argsFile, [string]$key) {
    if (-not (Test-Path $argsFile)) {
        throw "[FORMAL] Missing args.yaml: $argsFile"
    }
    $line = Select-String -Path $argsFile -Pattern "^$key:\s*(.+)$" | Select-Object -First 1
    if (-not $line) {
        throw "[FORMAL] Key '$key' not found in $argsFile"
    }
    return $line.Matches[0].Groups[1].Value.Trim().Trim("'\"")
}

function Assert-RunHyperparams([string]$runDir, [int]$expectedBatch, [string]$expectedDataYaml) {
    $argsFile = Join-Path $runDir 'args.yaml'
    $actualBatchRaw = Read-RunArgValue -argsFile $argsFile -key 'batch'
    $actualData = Read-RunArgValue -argsFile $argsFile -key 'data'
    $actualBatch = [int]$actualBatchRaw
    $expectedData = [System.IO.Path]::GetFullPath($expectedDataYaml)
    $actualDataFull = [System.IO.Path]::GetFullPath($actualData)

    if ($actualBatch -ne $expectedBatch) {
        throw "[FORMAL] Hyperparam mismatch in $runDir: batch=$actualBatch, expected=$expectedBatch"
    }
    if ($actualDataFull -ne $expectedData) {
        throw "[FORMAL] Hyperparam mismatch in $runDir: data=$actualDataFull, expected=$expectedData"
    }

    Write-Host "[FORMAL] Hyperparam check passed: batch=$actualBatch, data=$actualDataFull"
}

Write-Host "[FORMAL] Phase2 200 epochs start"
& $python "$repo\training\scripts\phase2_train_yolo11s.py" --epochs 200 --batch $thesisBatch --run-prefix baseline_full200
Assert-LastExitCode "Phase2"
$phase2Dir = (Get-LatestRunDirWithBest "$repo\experiments\YOLOv11-S").FullName
$phase2Best = Join-Path $phase2Dir 'weights\best.pt'
Assert-RunHyperparams -runDir $phase2Dir -expectedBatch $thesisBatch -expectedDataYaml $thesisDataYaml
Write-Host "[FORMAL] Phase2 done: $phase2Dir"

Write-Host "[FORMAL] Phase3 200 epochs start"
& $python "$repo\training\scripts\phase3_train_yolo11s_mbv3.py" --epochs 200 --batch $thesisBatch --run-prefix mbv3_full200
Assert-LastExitCode "Phase3"
$phase3Dir = (Get-LatestRunDirWithBest "$repo\experiments\YOLOv11-S-MBV3").FullName
$phase3Best = Join-Path $phase3Dir 'weights\best.pt'
Assert-RunHyperparams -runDir $phase3Dir -expectedBatch $thesisBatch -expectedDataYaml $thesisDataYaml
Write-Host "[FORMAL] Phase3 done: $phase3Dir"

Write-Host "[FORMAL] Phase4 200 epochs start"
& $python "$repo\training\scripts\phase4_train_yolo11s_mbv3_eca.py" --epochs 200 --batch $thesisBatch --run-prefix mbv3_eca_full200 --ultralytics-root "$repo\training\ultralytics_custom"
Assert-LastExitCode "Phase4"
$phase4Dir = (Get-LatestRunDirWithBest "$repo\experiments\YOLOv11-S-MBV3-ECA").FullName
$phase4Best = Join-Path $phase4Dir 'weights\best.pt'
Assert-RunHyperparams -runDir $phase4Dir -expectedBatch $thesisBatch -expectedDataYaml $thesisDataYaml
Write-Host "[FORMAL] Phase4 done: $phase4Dir"

Write-Host "[FORMAL] Phase5 evaluate/export/report start"
& $python "$repo\training\scripts\phase5_evaluate_all.py" --baseline $phase2Best --mbv3 $phase3Best --mbv3-eca $phase4Best --ultralytics-root "$repo\training\ultralytics_custom"
Assert-LastExitCode "Phase5 evaluate"
& $python "$repo\training\scripts\phase5_export_samples.py" --weights $phase4Best --ultralytics-root "$repo\training\ultralytics_custom"
Assert-LastExitCode "Phase5 export samples"
& $python "$repo\training\scripts\phase5_generate_report.py"
Assert-LastExitCode "Phase5 generate report"

Write-Host "[FORMAL] All phases completed."
