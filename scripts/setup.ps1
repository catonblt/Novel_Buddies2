# Automated setup script for Novel Writer (Windows)

Write-Host "🚀 Novel Writer - Automated Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check for required tools
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            Write-Host "✓ $Command is installed" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "✗ $Command is not installed" -ForegroundColor Red
        return $false
    }
}

Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check Node.js
if (-not (Test-Command node)) {
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check Python
if (-not (Test-Command python)) {
    Write-Host "Please install Python from https://python.org/" -ForegroundColor Yellow
    exit 1
}

# Check Rust
if (-not (Test-Command cargo)) {
    Write-Host "Installing Rust..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile "rustup-init.exe"
    .\rustup-init.exe -y
    Remove-Item rustup-init.exe
    $env:Path += ";$env:USERPROFILE\.cargo\bin"
}

Write-Host ""
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
npm install

Write-Host ""
Write-Host "🐍 Setting up Python backend..." -ForegroundColor Yellow
Set-Location python-backend

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller

Write-Host ""
Write-Host "🔨 Building Python backend executable..." -ForegroundColor Yellow
python build.py

Set-Location ..

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start development:"
Write-Host "  1. Terminal 1: cd python-backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload"
Write-Host "  2. Terminal 2: npm run tauri:dev"
Write-Host ""
Write-Host "To build installer:"
Write-Host "  npm run build:all"
Write-Host ""
