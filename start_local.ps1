param()

$ErrorActionPreference = 'Stop'

try {
	$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
	$backendDir = Join-Path $rootDir 'yolo_weed_detection_flask'
	$frontendDir = Join-Path $rootDir 'yolo_weed_detection_vue'

	$env:PORT = '8080'
	$env:VITE_FLASK_BASE_URL = 'http://localhost:8080'

	Write-Host '============================================================'
	Write-Host '[Local Dev] 正在启动项目...'
	Write-Host "[Env] PORT=$($env:PORT)"
	Write-Host "[Env] VITE_FLASK_BASE_URL=$($env:VITE_FLASK_BASE_URL)"
	Write-Host "[Backend] $backendDir"
	Write-Host "[Frontend] $frontendDir"
	Write-Host '============================================================'

	if (-not (Test-Path (Join-Path $backendDir 'main.py'))) {
		throw "未找到后端入口: $backendDir\\main.py"
	}

	if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
		throw "未找到前端入口: $frontendDir\\package.json"
	}

	$backendCmd = "Set-Location -LiteralPath '$backendDir'; `$env:PORT='$($env:PORT)'; python main.py"
	$frontendCmd = "Set-Location -LiteralPath '$frontendDir'; `$env:VITE_FLASK_BASE_URL='$($env:VITE_FLASK_BASE_URL)'; npm run dev"

	$backendProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $backendCmd) -PassThru
	Start-Sleep -Seconds 2
	$frontendProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoExit', '-ExecutionPolicy', 'Bypass', '-Command', $frontendCmd) -PassThru

	Write-Host ''
	Write-Host '=================== 访问地址 ==================='
	Write-Host '后端 Flask: http://localhost:8080'
	Write-Host '前端 Vue  : http://localhost:5173'
	Write-Host '================================================'
	Write-Host ''
	Write-Host '按任意键停止本脚本启动的后端/前端进程...'
	[void][System.Console]::ReadKey($true)

	foreach ($p in @($frontendProcess, $backendProcess)) {
		if ($null -ne $p) {
			try {
				if (-not $p.HasExited) {
					Stop-Process -Id $p.Id -Force -ErrorAction Stop
					Write-Host "[Stop] 已停止进程 PID=$($p.Id)"
				}
			}
			catch {
				Write-Warning "停止进程失败 PID=$($p.Id): $($_.Exception.Message)"
			}
		}
	}

	Write-Host '[Done] 已完成停止。'
}
catch {
	Write-Error $_.Exception.Message
}
