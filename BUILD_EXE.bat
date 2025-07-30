@echo off
title Dr Stoyanov Time Attendance System - Build Process
color 0A

echo.
echo ================================================================
echo      Dr Stoyanov Time Attendance System - Build to EXE
echo ================================================================
echo.
echo This script will create a standalone .exe file that includes:
echo  ✓ Complete Flask web application
echo  ✓ All Python dependencies
echo  ✓ Face recognition libraries
echo  ✓ File sharing systems
echo  ✓ Professional icon and branding
echo  ✓ SSL certificate generation
echo  ✓ Easy-to-share single executable
echo.
echo ================================================================
echo.

pause

echo 📦 Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r build_requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to install dependencies!
    echo Please check your Python installation and try again.
    pause
    exit /b 1
)

echo.
echo 🔨 Starting build process...
python build_exe.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Build process failed!
    echo Check the error messages above for details.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo                    🎉 BUILD COMPLETED! 🎉
echo ================================================================
echo.
echo Your Dr Stoyanov Time Attendance System has been compiled!
echo.
echo 📁 Location: distribution\DrStoyanovTimeAttendance.exe
echo 🚀 To start: Double-click "Start_Time_Attendance.bat"
echo.
echo The executable includes everything needed to run:
echo  ✓ Complete web application
echo  ✓ All dependencies
echo  ✓ SSL security
echo  ✓ Face recognition
echo  ✓ File sharing (Medical 5GB + Enterprise 50GB)
echo  ✓ Employee messaging
echo  ✓ Leave management
echo  ✓ Advanced reporting
echo.
echo 📦 Ready for distribution! Share the 'distribution' folder.
echo.
echo ================================================================

pause
