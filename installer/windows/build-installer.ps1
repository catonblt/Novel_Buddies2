# Build Novel Writer Installer - PowerShell Version
# This script builds the Windows installer with full error handling

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Novel Writer - Build Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Set error action preference
$ErrorActionPreference = "Stop"

# Ensure we're in the project root
if (-not (Test-Path "package.json")) {
    Write-Host "ERROR: This script must be run from the project root directory" -ForegroundColor Red
    Write-Host ""
    Write-Host "Current directory: $PWD" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Cyan
    Write-Host "  cd C:\path\to\Novel_Buddies" -ForegroundColor Yellow
    Write-Host "  .\installer\windows\build-installer.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Running from: $PWD" -ForegroundColor Green
Write-Host ""

function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Check for Inno Setup
$InnoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoPath)) {
    Write-Host "ERROR: Inno Setup not found at: $InnoPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Inno Setup from:" -ForegroundColor Yellow
    Write-Host "https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for Node.js
if (-not (Test-Command node)) {
    Write-Host "ERROR: Node.js not found" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check for Python
if (-not (Test-Command python)) {
    Write-Host "ERROR: Python not found" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    Write-Host "[1/6] Installing Node dependencies..." -ForegroundColor Green
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }

    Write-Host ""
    Write-Host "[2/6] Setting up Python environment..." -ForegroundColor Green
    Set-Location python-backend

    if (-not (Test-Path "venv")) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        if ($LASTEXITCODE -ne 0) { throw "Failed to create Python virtual environment" }
    }

    Write-Host "Activating Python environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1

    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies" }

    Write-Host ""
    Write-Host "[3/6] Building Python backend executable..." -ForegroundColor Green
    python build.py
    if ($LASTEXITCODE -ne 0) { throw "Failed to build Python backend" }

    Set-Location ..

    Write-Host ""
    Write-Host "[4/6] Building frontend..." -ForegroundColor Green
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }

    Write-Host ""
    Write-Host "[5/6] Building Tauri application..." -ForegroundColor Green
    npm run tauri build
    if ($LASTEXITCODE -ne 0) { throw "Tauri build failed" }

    Write-Host ""
    Write-Host "[6/6] Creating installer with Inno Setup..." -ForegroundColor Green
    & $InnoPath /Qp "installer\windows\novel-writer.iss"
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed" }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "SUCCESS! Installer created" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installer location:" -ForegroundColor Cyan
    Write-Host "src-tauri\target\release\bundle\nsis\NovelWriter_Setup_1.0.0.exe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can now distribute this installer to users." -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error message: $_" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please check the error message above and try again." -ForegroundColor Yellow
    Write-Host "For help, visit: https://github.com/yourusername/novel-writer/issues" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"
