@echo off
title Dr Stoyanov Time Attendance System - First Run Setup
color 0B

echo.
echo ================================================================
echo      Dr Stoyanov Time Attendance System v2.0
echo                    Welcome Setup
echo ================================================================
echo.
echo This will set up the Time Attendance System on your computer.
echo.

REM Check if running from distribution folder
if not exist "DrStoyanovTimeAttendance.exe" (
    echo ❌ Error: DrStoyanovTimeAttendance.exe not found!
    echo Please run this from the distribution folder.
    pause
    exit /b 1
)

echo 🔧 Setting up Dr Stoyanov Time Attendance System...
echo.

REM Ask user about desktop shortcut
echo Would you like to create a desktop shortcut? (Y/N)
set /p create_shortcut="Create desktop shortcut (recommended): "

if /i "%create_shortcut%"=="Y" (
    echo 📋 Creating desktop shortcut...
    
    REM Create VBS script to create shortcut
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
    echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Dr Stoyanov Time Attendance.lnk" >> CreateShortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
    echo oLink.TargetPath = "%CD%\DrStoyanovTimeAttendance.exe" >> CreateShortcut.vbs
    echo oLink.WorkingDirectory = "%CD%" >> CreateShortcut.vbs
    echo oLink.Description = "Dr Stoyanov Time Attendance System - Enterprise Workforce Management" >> CreateShortcut.vbs
    echo oLink.IconLocation = "%CD%\DrStoyanovTimeAttendance.exe,0" >> CreateShortcut.vbs
    echo oLink.Save >> CreateShortcut.vbs
    
    REM Execute VBS script
    cscript CreateShortcut.vbs >nul 2>&1
    
    REM Clean up
    del CreateShortcut.vbs >nul 2>&1
    
    echo ✅ Desktop shortcut created successfully!
    echo.
)

REM Ask user about Start Menu shortcut
echo Would you like to add to Start Menu? (Y/N)
set /p create_startmenu="Add to Start Menu (recommended): "

if /i "%create_startmenu%"=="Y" (
    echo 📋 Creating Start Menu entry...
    
    REM Create Start Menu folder
    set "startmenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Dr Stoyanov Time Attendance"
    if not exist "%startmenu%" mkdir "%startmenu%"
    
    REM Create VBS script for Start Menu shortcut
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateStartMenu.vbs
    echo sLinkFile = "%startmenu%\Dr Stoyanov Time Attendance.lnk" >> CreateStartMenu.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateStartMenu.vbs
    echo oLink.TargetPath = "%CD%\DrStoyanovTimeAttendance.exe" >> CreateStartMenu.vbs
    echo oLink.WorkingDirectory = "%CD%" >> CreateStartMenu.vbs
    echo oLink.Description = "Dr Stoyanov Time Attendance System" >> CreateStartMenu.vbs
    echo oLink.IconLocation = "%CD%\DrStoyanovTimeAttendance.exe,0" >> CreateStartMenu.vbs
    echo oLink.Save >> CreateStartMenu.vbs
    
    REM Create uninstall shortcut
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateUninstall.vbs
    echo sLinkFile = "%startmenu%\Uninstall Dr Stoyanov Time Attendance.lnk" >> CreateUninstall.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateUninstall.vbs
    echo oLink.TargetPath = "%CD%\Uninstall.bat" >> CreateUninstall.vbs
    echo oLink.WorkingDirectory = "%CD%" >> CreateUninstall.vbs
    echo oLink.Description = "Remove Dr Stoyanov Time Attendance System" >> CreateUninstall.vbs
    echo oLink.Save >> CreateUninstall.vbs
    
    REM Execute VBS scripts
    cscript CreateStartMenu.vbs >nul 2>&1
    cscript CreateUninstall.vbs >nul 2>&1
    
    REM Clean up
    del CreateStartMenu.vbs >nul 2>&1
    del CreateUninstall.vbs >nul 2>&1
    
    echo ✅ Start Menu entry created successfully!
    echo.
)

REM Ask about running now
echo Setup complete! Would you like to start the system now? (Y/N)
set /p start_now="Start Dr Stoyanov Time Attendance System: "

if /i "%start_now%"=="Y" (
    echo.
    echo 🚀 Starting Dr Stoyanov Time Attendance System...
    echo 💡 Your browser will open automatically in a few seconds.
    echo.
    start "" DrStoyanovTimeAttendance.exe
) else (
    echo.
    echo ✅ Setup completed successfully!
    echo.
    echo To start the system:
    if /i "%create_shortcut%"=="Y" (
        echo  • Double-click the desktop shortcut
    )
    if /i "%create_startmenu%"=="Y" (
        echo  • Use Start Menu: Dr Stoyanov Time Attendance
    )
    echo  • Double-click DrStoyanovTimeAttendance.exe
    echo  • Double-click Start_Time_Attendance.bat
    echo.
)

echo ================================================================
echo                Dr Stoyanov Time Attendance System
echo                    Setup Complete! 🎉
echo ================================================================
echo.
echo System Features Available:
echo  ✓ Time Attendance Tracking
echo  ✓ Employee Management
echo  ✓ Face Recognition Authentication
echo  ✓ Employee Messaging System
echo  ✓ Medical File Sharing (5GB)
echo  ✓ Enterprise LAN File Sharing (50GB)
echo  ✓ Leave Management System
echo  ✓ Advanced Reporting & Analytics
echo.
echo Access URLs (when running):
echo  • Admin Panel: https://localhost:5003/admin
echo  • Employee Terminal: https://localhost:5003/terminal
echo.
echo For support, see README.md or QUICK_SETUP.md
echo.
pause
