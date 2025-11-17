@echo off
REM This wrapper ensures the build script runs from the correct directory

echo ============================================
echo Novel Writer - Build Installer (Wrapper)
echo ============================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Navigate to project root (two levels up from installer/windows)
cd /d "%SCRIPT_DIR%..\.."

REM Verify we're in the right place
if not exist "package.json" (
    echo ERROR: Could not find project root directory
    echo Expected to find package.json in: %CD%
    pause
    exit /b 1
)

echo Running from project root: %CD%
echo.

REM Call the actual build script
call installer\windows\build-installer.bat

REM Return to original directory
cd /d "%SCRIPT_DIR%"
