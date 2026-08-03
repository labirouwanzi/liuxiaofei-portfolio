@echo off
chcp 65001 >nul
title 刘晓菲个人主页 - 本地预览
cd /d "%~dp0"

echo ============================================
echo   刘晓菲个人主页 · 本地预览
echo   关闭本窗口即停止服务
echo ============================================
echo.

start "" "http://127.0.0.1:8765"

python -m http.server 8765 --bind 127.0.0.1

pause
