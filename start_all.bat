@echo off
echo ========================================================
echo   Launching HotWAY Fullstack System
echo   Backend:  http://localhost:8000 (API & SSE Stream)
echo   Frontend: http://localhost:3001 (Research & WebGIS)
echo ========================================================

start "HotWAY Backend (:8000)" cmd /k "run_backend.bat"
timeout /t 3 /nobreak > nul
start "HotWAY Frontend (:3001)" cmd /k "run_frontend.bat"

echo.
echo Both servers have been launched in separate terminal windows!
echo Open your browser at:
echo   - Research Report: http://localhost:3001
echo   - WebGIS Live Demo: http://localhost:3001/demo
echo   - Backend Swagger: http://localhost:8000/docs
echo.
