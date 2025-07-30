@echo off
title Dr Stoyanov Time Attendance System
color 0B

echo ================================================================
echo      Dr Stoyanov Time Attendance System v2.0
echo                 Starting Application...
echo ================================================================
echo.

REM Change to the application directory
cd /d "%~dp0"

echo [INFO] Starting Dr Stoyanov Time Attendance System...
echo [INFO] Please wait while the system initializes...
echo.
echo [TIP] Your web browser will open automatically when ready.
echo [TIP] Access URLs:
echo       HTTPS: https://localhost:5003
echo       HTTP:  http://localhost:5002
echo.

REM Start the standalone executable
echo [INFO] Launching executable...
DrStoyanovTimeAttendance.exe

echo.
echo [INFO] Application has stopped.
pause
