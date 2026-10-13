@echo off
setlocal
start "NutriFit Backend" cmd /k ""%~dp0run_backend.bat""
start "NutriFit Frontend" cmd /k ""%~dp0run_frontend.bat""
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:5500/frontend/index.html"
endlocal
