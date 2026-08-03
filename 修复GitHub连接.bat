@echo off
:: ============================================
::  Fix GitHub connection (hosts pinning)
::  Run as Administrator (UAC will prompt)
:: ============================================

:: Request admin rights if not already elevated
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator permission...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

set "HOSTS=%SystemRoot%\System32\drivers\etc\hosts"

:: Backup once
if not exist "%HOSTS%.bak" (
    copy "%HOSTS%" "%HOSTS%.bak" >nul
    echo Backup saved: hosts.bak
)

:: Add entry if missing
findstr /C:"140.82.112.3 github.com" "%HOSTS%" >nul 2>&1
if %errorlevel% neq 0 (
    echo.>> "%HOSTS%"
    echo # GitHub connectivity fix ^(remove this line to undo^)>> "%HOSTS%"
    echo 140.82.112.3 github.com>> "%HOSTS%"
    echo Entry added: 140.82.112.3 github.com
) else (
    echo Entry already exists.
)

ipconfig /flushdns >nul
echo DNS cache flushed.
echo.
echo ============================================
echo  Done! Now double-click  Deploy-push.bat
echo  (推送到 GitHub 的脚本: 部署推送.bat)
echo ============================================
echo.
pause
