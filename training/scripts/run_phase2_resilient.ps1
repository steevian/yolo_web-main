param(
    [string]$Repo = 'D:\cyd\Desktop\yolo_web-main',
    [string]$PythonExe = 'C:/Users/cyd/miniconda3/envs/weedweb_detection/python.exe',
    [ValidateSet('fresh','resume')]
    [string]$Mode = 'fresh',
    [string]$Checkpoint = '',
    [int]$MaxRestarts = 500,
    [int]$Epochs = 200,
    [int]$Workers = 0,
    [int]$Batch = 6,
    [string]$CacheMode = 'disk',
    [string]$Device = '0',
    [int]$RetryDelaySeconds = 20,
    [string]$FailureLogDir = 'D:/cyd/Desktop/yolo_web-main/experiments/logs/phase2_failures',
    [switch]$Amp
)

$ErrorActionPreference = 'Stop'

$env:KMP_DUPLICATE_LIB_OK = 'TRUE'
Set-Location $Repo

$trianlog = Join-Path $Repo 'docs/trianlog.md'
if (-not (Test-Path $trianlog)) {
    New-Item -ItemType File -Path $trianlog -Force | Out-Null
}

New-Item -ItemType Directory -Force $FailureLogDir | Out-Null

function Write-Trianlog {
    param([string]$Title, [string[]]$Lines)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $trianlog -Encoding UTF8 -Value "## $ts | $Title"
    Add-Content -Path $trianlog -Encoding UTF8 -Value ""
    foreach ($line in $Lines) {
        Add-Content -Path $trianlog -Encoding UTF8 -Value "- $line"
    }
    Add-Content -Path $trianlog -Encoding UTF8 -Value ""
}

if ($Mode -eq 'resume') {
    if ([string]::IsNullOrWhiteSpace($Checkpoint)) {
        $latest = Get-ChildItem -Path (Join-Path $Repo 'experiments/YOLOv11-S') -Filter last.pt -Recurse -File |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($null -eq $latest) {
            throw "No resumable checkpoint found under experiments/YOLOv11-S"
        }
        $Checkpoint = $latest.FullName.Replace('\\', '/')
    }

    if (-not (Test-Path $Checkpoint)) {
        throw "Checkpoint not found: $Checkpoint"
    }
}

Write-Host "[RESILIENT] Phase2 resilient resume started."
Write-Host "[RESILIENT] mode=$Mode"
Write-Host "[RESILIENT] checkpoint=$Checkpoint"
Write-Host "[RESILIENT] epochs=$Epochs, workers=$Workers, batch=$Batch, cache=$CacheMode, device=$Device, maxRestarts=$MaxRestarts"

Write-Trianlog -Title "Phase2 watchdog start" -Lines @(
    "mode=$Mode",
    "checkpoint=$Checkpoint",
    "epochs=$Epochs, batch=$Batch, workers=$Workers, cache=$CacheMode, device=$Device"
)

for ($attempt = 1; $attempt -le $MaxRestarts; $attempt++) {
    Write-Host "[RESILIENT] attempt $attempt/$MaxRestarts"

    $cmdArgs = @(
        "$Repo\training\scripts\phase2_train_yolo11s.py",
        '--epochs', $Epochs,
        '--workers', $Workers,
        '--batch', $Batch,
        '--cache', $CacheMode,
        '--device', $Device
    )

    if ($Amp.IsPresent) {
        $cmdArgs += '--amp'
    }

    if ($Mode -eq 'resume') {
        $cmdArgs += '--resume'
        $cmdArgs += '--checkpoint'
        $cmdArgs += $Checkpoint
    }

    & $PythonExe @cmdArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "[RESILIENT] training completed successfully."
        Write-Trianlog -Title "Phase2 watchdog completed" -Lines @("attempt=$attempt", "exit_code=0")
        exit 0
    }

    if ($Mode -eq 'resume' -and -not (Test-Path $Checkpoint)) {
        throw "[RESILIENT] checkpoint disappeared after failure, cannot resume: $Checkpoint"
    }

    $ts = Get-Date -Format 'yyyyMMdd_HHmmss'
    $failureFile = Join-Path $FailureLogDir "attempt_${attempt}_${ts}.log"
    if ($Mode -eq 'resume' -and (Test-Path $Checkpoint)) {
        $checkpointInfo = Get-Item $Checkpoint | Select-Object FullName, LastWriteTime, Length
    } else {
        $checkpointInfo = [PSCustomObject]@{
            FullName = 'N/A'
            LastWriteTime = 'N/A'
            Length = 'N/A'
        }
    }
    @(
        "exit_code=$exitCode"
        "attempt=$attempt"
        "mode=$Mode"
        "timestamp=$ts"
        "checkpoint_path=$($checkpointInfo.FullName)"
        "checkpoint_last_write=$($checkpointInfo.LastWriteTime)"
        "checkpoint_size=$($checkpointInfo.Length)"
    ) | Set-Content -Path $failureFile -Encoding UTF8

    Write-Warning "[RESILIENT] training exited with code $exitCode, retrying in $RetryDelaySeconds seconds... details: $failureFile"
    Write-Trianlog -Title "Phase2 watchdog retry" -Lines @(
        "attempt=$attempt",
        "exit_code=$exitCode",
        "failure_file=$failureFile"
    )
    Start-Sleep -Seconds $RetryDelaySeconds
}

Write-Trianlog -Title "Phase2 watchdog failed" -Lines @("max_restarts=$MaxRestarts")
throw "[RESILIENT] exceeded max restart attempts: $MaxRestarts"
