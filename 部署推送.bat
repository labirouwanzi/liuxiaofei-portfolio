@echo off
cd /d "%~dp0"

echo ============================================
echo  Deploying to GitHub: labirouwanzi/liuxiaofei-portfolio
echo  (auto-retry up to 6 times)
echo ============================================
echo.

git remote add origin https://github.com/labirouwanzi/liuxiaofei-portfolio.git 2>nul
git remote set-url origin https://github.com/labirouwanzi/liuxiaofei-portfolio.git

git add .
git commit -m "update" 2>nul

set /a tries=0

:pushloop
set /a tries+=1
echo --- pushing, attempt %tries% / 6 ---
git push origin main
if %errorlevel%==0 goto success
if %tries% geq 6 goto failed
echo.
echo  Connection failed. Retrying in 10 seconds...
timeout /t 10 /nobreak >nul
echo.
goto pushloop

:success
echo.
echo ============================================
echo  DONE! Site is updated.
echo ============================================
goto end

:failed
echo.
echo ============================================
echo  Still failing after 6 tries.
echo  Your network to github.com is unstable.
echo  Close this window and try again later.
echo ============================================
goto end

:end
pause
