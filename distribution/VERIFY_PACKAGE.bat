@echo off
title Distribution Package Verification
color 0A

echo ================================================================
echo   Dr Stoyanov Time Attendance System - Distribution Verification
echo ================================================================
echo.

cd /d "%~dp0"

echo [CHECK] Verifying package contents...
echo.

if exist "DrStoyanovTimeAttendance.exe" (
    echo ✓ DrStoyanovTimeAttendance.exe - Found
    for %%I in (DrStoyanovTimeAttendance.exe) do echo   Size: %%~zI bytes
) else (
    echo ✗ DrStoyanovTimeAttendance.exe - MISSING!
    goto :error
)

if exist "Start_Dr_Stoyanov_TimeAttendance.bat" (
    echo ✓ Start_Dr_Stoyanov_TimeAttendance.bat - Found
) else (
    echo ✗ Start_Dr_Stoyanov_TimeAttendance.bat - MISSING!
    goto :error
)

if exist "README_DISTRIBUTION.md" (
    echo ✓ README_DISTRIBUTION.md - Found
) else (
    echo ✗ README_DISTRIBUTION.md - MISSING!
    goto :error
)

echo.
echo [SUCCESS] ✓ All required files are present!
echo.
echo [INFO] This package is ready for distribution.
echo [INFO] Users can run this on any Windows computer without Python.
echo.
echo Package contents:
echo - DrStoyanovTimeAttendance.exe (Standalone application)
echo - Start_Dr_Stoyanov_TimeAttendance.bat (Easy launcher)
echo - README_DISTRIBUTION.md (User instructions)
echo - VERIFY_PACKAGE.bat (This verification script)
echo.
echo To start the application: Double-click Start_Dr_Stoyanov_TimeAttendance.bat
echo.
goto :end

:error
echo.
echo [ERROR] Package verification failed!
echo Some required files are missing.
echo.

:end
pause
