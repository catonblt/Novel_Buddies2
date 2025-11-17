# PowerShell wrapper to run build script from correct directory

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Novel Writer - Build Installer (Wrapper)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navigate to project root (two levels up from installer/windows)
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $ProjectRoot

# Verify we're in the right place
if (-not (Test-Path "package.json")) {
    Write-Host "ERROR: Could not find project root directory" -ForegroundColor Red
    Write-Host "Expected to find package.json in: $PWD" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Running from project root: $PWD" -ForegroundColor Green
Write-Host ""

# Call the actual build script
& "installer\windows\build-installer.ps1"

# Return to original directory
Set-Location $ScriptDir
