@echo off
title Dr Stoyanov Time Attendance System - Uninstall
color 0C

echo.
echo ================================================================
echo      Dr Stoyanov Time Attendance System - Uninstall
echo ================================================================
echo.
echo This will remove desktop shortcuts and Start Menu entries.
echo Your data files will NOT be deleted.
echo.

set /p confirm="Are you sure you want to uninstall? (Y/N): "

if /i not "%confirm%"=="Y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo 🗑️ Removing Dr Stoyanov Time Attendance System...

REM Remove desktop shortcut
if exist "%USERPROFILE%\Desktop\Dr Stoyanov Time Attendance.lnk" (
    del "%USERPROFILE%\Desktop\Dr Stoyanov Time Attendance.lnk" >nul 2>&1
    echo ✅ Removed desktop shortcut
)

REM Remove Start Menu folder
set "startmenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Dr Stoyanov Time Attendance"
if exist "%startmenu%" (
    rmdir /s /q "%startmenu%" >nul 2>&1
    echo ✅ Removed Start Menu entries
)

echo.
echo ✅ Uninstall completed successfully!
echo.
echo Note: Your data files have been preserved:
echo  • attendance_data\
echo  • file_storage\
echo  • enterprise_lan_storage\
echo.
echo You can safely delete the entire application folder if desired.
echo.
pause
