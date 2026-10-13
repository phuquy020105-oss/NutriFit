@echo off
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" backend\wsgi.py
) else (
  python backend\wsgi.py
)
endlocal
