#!/bin/bash
# Automated setup script for Novel Writer (macOS/Linux)

set -e

echo "🚀 Novel Writer - Automated Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for required tools
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
        return 0
    fi
}

echo "📋 Checking prerequisites..."
echo ""

# Check Node.js
if ! check_command node; then
    echo -e "${YELLOW}Please install Node.js from https://nodejs.org/${NC}"
    exit 1
fi

# Check Python
if ! check_command python3; then
    echo -e "${YELLOW}Please install Python from https://python.org/${NC}"
    exit 1
fi

# Check Rust
if ! check_command cargo; then
    echo -e "${YELLOW}Installing Rust...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

echo ""
echo "📦 Installing frontend dependencies..."
npm install

echo ""
echo "🐍 Setting up Python backend..."
cd python-backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install pyinstaller

echo ""
echo "🔨 Building Python backend executable..."
python build.py

cd ..

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start development:"
echo "  1. Terminal 1: cd python-backend && source venv/bin/activate && uvicorn main:app --reload"
echo "  2. Terminal 2: npm run tauri:dev"
echo ""
echo "To build installer:"
echo "  npm run build:all"
echo ""
