@echo off
title NutriFit - Khoi dong he thong
echo ===================================================
echo     DANG KHOI DONG BACKEND VA GIAO DIEN NUTRIFIT
echo ===================================================
echo.
echo 1. Dang khoi dong Backend API ket noi SQL Server (SSMS)...
start "NutriFit Backend" cmd /k "python server.py"
timeout /t 2 /nobreak >nul
echo.
echo 2. Dang mo giao dien tren trinh duyet...
start "" index.html
echo.
echo ===================================================
echo   KHOI DONG THANH CONG! DU LIEU DUOC LUU TREN SQL SERVER
echo ===================================================
exit
