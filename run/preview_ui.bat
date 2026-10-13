@echo off
setlocal
cd /d "%~dp0.."
start "NutriFit Studio Frontend" cmd /k "python -m http.server 5500"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5500/frontend/index.html"
endlocal
