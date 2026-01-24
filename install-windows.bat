@echo off
REM Cashflow Dashboard - Windows Installer Launcher
REM This batch file launches the PowerShell installer with Administrator privileges

echo ========================================
echo   Cashflow Dashboard - Windows Installer
echo ========================================
echo.
echo This will install Cashflow Dashboard on your Windows PC.
echo.
echo Requirements:
echo   - Windows 10 or 11
echo   - Administrator privileges
echo   - Internet connection
echo.
pause

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with Administrator privileges...
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1"
) else (
    echo.
    echo ERROR: This installer requires Administrator privileges!
    echo.
    echo Please right-click this file and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

pause
