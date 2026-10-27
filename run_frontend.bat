@echo off
title HotWAY Frontend (:3001)
echo ========================================================
echo   Starting HotWAY WebGIS Frontend on Port 3001
echo   Research Landing: http://localhost:3001/
echo   OptimoRoute Demo: http://localhost:3001/demo
echo   (Port 3000 protected & prohibited)
echo ========================================================

:: 1. Tự động dọn dẹp tiến trình Node cũ đang chiếm cổng 3001
echo [*] Kiem tra va giai phong cong 3001 neu co tien trinh cu...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3001 ^| findstr LISTENING') do (
    echo [*] Dang giai phong PID %%a tren cong 3001...
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Chuyen vao thu muc frontend va don sach cache Webpack cu
cd frontend

echo [*] Don dep cache Webpack (.next\cache) de tranh loi thieu chunk...
if exist .next\cache (
    rmdir /s /q .next\cache >nul 2>&1
)

:: 3. Khoi dong Next.js dev server tren cong 3001
echo [*] Khoi dong Next.js Development Server...
npm run dev

pause
