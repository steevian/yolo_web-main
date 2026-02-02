@echo off
echo ============================================
echo   杂草检测系统 - mkcert一键启动脚本
echo   自动配置HTTPS，解决摄像头权限问题
echo ============================================
echo.

:: 1. 检查Flask服务
echo [1/3] 检查Flask后端服务...
tasklist | find /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo ⚠️  检测到Python进程，请确保Flask已在192.168.0.101:5000运行
) else (
    echo ⚠️  未检测到Flask服务，请手动启动：
    echo     1. 打开新CMD窗口
    echo     2. cd D:\cyd\Desktop\yolo_web-main\yolo_cropDisease_detection_flask
    echo     3. python main.py
)

:: 2. 启动Vue前端（HTTPS）
echo [2/3] 启动Vue前端服务（自动配置HTTPS）...
cd /d "D:\cyd\Desktop\yolo_web-main\yolo_cropDisease_detection_vue"
start "Vue前端HTTPS" cmd /k "npm run dev"
timeout /t 8 /nobreak >nul

:: 3. 自动打开浏览器（HTTPS）
echo [3/3] 打开浏览器访问HTTPS地址...
echo.
echo ✅ 系统启动完成！
echo 📍 访问地址：https://192.168.0.101:5173
echo 📍 首次运行会自动安装本地CA证书
echo.
echo ⚠️  重要提示：
echo     1. 首次启动时，mkcert会要求安装本地CA证书
echo     2. 点击"Yes"或"是"安装证书
echo     3. 证书安装后，所有HTTPS连接都会被信任
echo.
echo 按任意键打开浏览器...
pause >nul

:: 使用Edge打开（支持mkcert证书）
start msedge "https://192.168.0.101:5173"

:: 同时打开localhost备用
start msedge "https://localhost:5173"

echo.
echo 🔍 如果浏览器提示不安全：
echo     1. 点击"高级"
echo     2. 点击"继续前往192.168.0.101(不安全)"
echo     3. 这只是因为证书是自签名的，不影响使用
echo.
pause