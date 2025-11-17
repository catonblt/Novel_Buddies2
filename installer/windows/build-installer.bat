@echo off
REM Build Novel Writer Installer using Inno Setup
REM This script builds the Windows installer with full error handling

echo ============================================
echo Novel Writer - Build Installer
echo ============================================
echo.

REM Check for Inno Setup
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%INNO_PATH%" (
    echo ERROR: Inno Setup not found at: %INNO_PATH%
    echo.
    echo Please install Inno Setup from:
    echo https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

REM Check for Node.js
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo [1/6] Installing Node dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm install failed
    pause
    exit /b 1
)

echo.
echo [2/6] Setting up Python environment...
cd python-backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create Python virtual environment
        cd ..
        pause
        exit /b 1
    )
)

echo Activating Python environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install Python dependencies
    cd ..
    pause
    exit /b 1
)

echo.
echo [3/6] Building Python backend executable...
python build.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Python backend
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo [4/6] Building frontend...
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Frontend build failed
    pause
    exit /b 1
)

echo.
echo [5/6] Building Tauri application...
call npm run tauri build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Tauri build failed
    pause
    exit /b 1
)

echo.
echo [6/6] Creating installer with Inno Setup...
echo Running from: %CD%
echo Inno Setup script: installer\windows\novel-writer.iss

REM Ensure we're in the project root
if not exist "installer\windows\novel-writer.iss" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

"%INNO_PATH%" /Qp "installer\windows\novel-writer.iss"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Inno Setup compilation failed
    echo.
    echo Make sure you're running this from the project root directory:
    echo   cd C:\path\to\Novel_Buddies
    echo   installer\windows\build-installer.bat
    pause
    exit /b 1
)

echo.
echo ============================================
echo SUCCESS! Installer created
echo ============================================
echo.
echo Installer location:
echo src-tauri\target\release\bundle\nsis\NovelWriter_Setup_1.0.0.exe
echo.
echo You can now distribute this installer to users.
echo.
pause
