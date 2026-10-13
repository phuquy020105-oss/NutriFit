@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
echo.
echo Python dependencies installed. Configure .env and read README.md for database steps.
pause
endlocal
