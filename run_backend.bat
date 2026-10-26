@echo off
title HotWAY Backend (:8000)
echo ========================================================
echo   Starting HotWAY FastAPI Backend Server on Port 8000
echo   Swagger Docs: http://localhost:8000/docs
echo ========================================================
py -3.13 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
  "C:\Users\Asus\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
)
pause
