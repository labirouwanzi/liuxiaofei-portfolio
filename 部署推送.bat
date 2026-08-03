@echo off
cd /d "%~dp0"

echo ============================================
echo  Deploying to GitHub: labirouwanzi/liuxiaofei-portfolio
echo  (if a browser window pops up, click Authorize/Allow)
echo ============================================
echo.

git remote add origin https://github.com/labirouwanzi/liuxiaofei-portfolio.git 2>nul
git remote set-url origin https://github.com/labirouwanzi/liuxiaofei-portfolio.git

git add .
git commit -m "update" 2>nul

echo --- pushing ---
git push -u origin main

echo.
echo ============================================
echo  Done. If you saw "fatal: ...", copy the text here.
echo  Otherwise your site is uploaded.
echo ============================================
echo.
pause
