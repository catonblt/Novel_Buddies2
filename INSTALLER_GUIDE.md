# Installer Guide - Novel Writer

This guide explains how to build and distribute installers for Novel Writer.

## 🎯 Overview

Novel Writer uses **Tauri** to create native installers for Windows, macOS, and Linux. The Python backend is bundled using **PyInstaller** and included as a sidecar binary that runs automatically when the app launches.

**End users simply download one installer file and run it** - no manual setup required!

### Windows Wizard Installer

For Windows, we provide a **professional wizard-based installer** using **Inno Setup** that includes:
- ✅ Step-by-step installation wizard
- ✅ Prerequisite checking (Windows version, disk space, admin rights)
- ✅ Detailed error messages and logging
- ✅ Installation validation
- ✅ Automatic rollback on failure
- ✅ Before/after information screens

See `installer/windows/` for the wizard installer configuration.

## 📦 What Gets Bundled

When you build an installer, it includes:

1. **React Frontend** - Compiled to static HTML/CSS/JS
2. **Tauri Shell** - Native OS wrapper (Rust)
3. **Python Backend** - Bundled standalone executable (PyInstaller)
4. **Dependencies** - All runtime dependencies bundled

**Total size**: ~100-150 MB (varies by platform)

## 🚀 Quick Build (Recommended)

### One-Command Build

```bash
npm run build:all
```

This command:
1. Builds the Python backend into a standalone executable
2. Builds the frontend
3. Creates native installers for your current platform

### Output Locations

Installers are created in `src-tauri/target/release/bundle/`:

- **Windows**: `.msi` and `.exe` installers
- **macOS**: `.dmg` and `.app` bundle
- **Linux**: `.deb`, `.AppImage`, and `.rpm`

## 🛠️ Step-by-Step Build Process

### Prerequisites

Before building, ensure you have:

- ✅ **Node.js** 18+ ([Download](https://nodejs.org/))
- ✅ **Python** 3.9+ ([Download](https://python.org/))
- ✅ **Rust** latest ([Download](https://rustup.rs/))

**Platform-Specific Requirements**:

**Windows**:
- Visual Studio Build Tools
- WebView2 (usually pre-installed on Windows 10/11)

**macOS**:
- Xcode Command Line Tools: `xcode-select --install`

**Linux** (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

### Step 1: Run Setup Script

Choose your platform:

**macOS/Linux**:
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows** (PowerShell):
```powershell
.\scripts\setup.ps1
```

This script:
- Checks for required tools
- Installs dependencies
- Sets up Python virtual environment
- Builds the Python backend

### Step 2: Build the Installer

```bash
npm run build:all
```

**Or build components separately**:

```bash
# 1. Build Python backend
npm run backend:build

# 2. Build Tauri app with installers
npm run tauri:build
```

### Step 3: Find Your Installer

Navigate to: `src-tauri/target/release/bundle/`

**Windows**:
- `msi/Novel Writer_1.0.0_x64_en-US.msi` - Recommended installer
- `nsis/Novel Writer_1.0.0_x64-setup.exe` - Alternative installer

**macOS**:
- `dmg/Novel Writer_1.0.0_x64.dmg` - Drag-to-install disk image
- `macos/Novel Writer.app` - Application bundle

**Linux**:
- `deb/novel-writer_1.0.0_amd64.deb` - Debian/Ubuntu package
- `appimage/novel-writer_1.0.0_amd64.AppImage` - Universal Linux binary
- `rpm/novel-writer-1.0.0-1.x86_64.rpm` - Fedora/RHEL package

## 📋 What Happens When Users Install

### Installation Process

1. **User downloads installer** (e.g., `Novel Writer_1.0.0_x64.msi`)
2. **User runs installer**
   - Accepts permissions/license
   - Chooses install location (default: Program Files or Applications)
3. **Installer extracts files**
   - Main application
   - Python backend (bundled as `novel-writer-backend` executable)
   - Assets and resources
4. **Creates desktop shortcut** (automatic)
5. **Adds to Start Menu/Applications** (automatic)

### First Launch

1. User clicks desktop shortcut or Start Menu icon
2. Tauri app launches
3. **Python backend automatically starts** (bundled sidecar)
4. Frontend connects to backend (localhost:8000)
5. User sees setup wizard for first project

**No manual configuration required!**

## 🔧 Advanced Build Options

### Build for Specific Platform Only

```bash
# Build only .msi (Windows)
npm run tauri:build -- --bundles msi

# Build only .dmg (macOS)
npm run tauri:build -- --bundles dmg

# Build only .deb (Linux)
npm run tauri:build -- --bundles deb
```

### Build with Custom Icon

Place your icons in `src-tauri/icons/`:
- `icon.icns` - macOS
- `icon.ico` - Windows
- `32x32.png`, `128x128.png`, etc. - Linux

Then rebuild:
```bash
npm run tauri:build
```

### Debug Build (Faster, Larger)

```bash
npm run tauri:build -- --debug
```

## 📦 Distributing Your Installer

### Hosting Options

1. **GitHub Releases**
   - Upload installer to GitHub Releases
   - Users download directly from GitHub

2. **Website Download**
   - Host on your own server
   - Provide download links by platform

3. **Microsoft Store / Mac App Store**
   - Requires developer account
   - Additional signing/certification steps

### File Naming Convention

Follow semantic versioning and platform naming:

```
Novel Writer_[VERSION]_[ARCH]_[PLATFORM].[EXTENSION]

Examples:
- Novel Writer_1.0.0_x64_en-US.msi
- Novel Writer_1.0.0_aarch64.dmg
- novel-writer_1.0.0_amd64.deb
```

### Code Signing (Recommended for Production)

**Windows**:
```bash
# Get a code signing certificate
# Update src-tauri/tauri.conf.json:
"windows": {
  "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
  "digestAlgorithm": "sha256"
}
```

**macOS**:
```bash
# Enroll in Apple Developer Program
# Update src-tauri/tauri.conf.json:
"macOS": {
  "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)"
}
```

**Linux**: Generally doesn't require code signing

## 🧪 Testing the Installer

### Before Distribution

1. **Clean Install Test**
   - Use a fresh VM or test machine
   - Install from the .msi/.dmg/.deb
   - Verify app launches correctly
   - Test all features (agents, file operations, git)

2. **Uninstall Test**
   - Uninstall the application
   - Verify all files are removed
   - Check no leftover registry entries (Windows)

3. **Upgrade Test**
   - Install version 1.0.0
   - Install version 1.1.0 over it
   - Verify settings and projects are preserved

### Automated Testing

```bash
# Run tests before building
npm run lint
npm run format

# Test the Python backend
cd python-backend
pytest  # (add tests first)
```

## 📝 Checklist Before Release

- [ ] Updated version number in `package.json` and `src-tauri/tauri.conf.json`
- [ ] All tests passing
- [ ] Python backend builds without errors
- [ ] Frontend builds without errors
- [ ] Tested on clean machine
- [ ] Desktop shortcut appears after install
- [ ] App launches and backend starts automatically
- [ ] All 5 agents working
- [ ] File operations work
- [ ] Git integration works
- [ ] Created release notes
- [ ] Code signed (if applicable)

## 🐛 Troubleshooting

### "Python backend not found"

**Cause**: PyInstaller build failed or sidecar path incorrect

**Solution**:
1. Manually build backend: `cd python-backend && python build.py`
2. Check `src-tauri/binaries/` for the executable
3. Verify filename matches platform convention

### "Installer build fails"

**Cause**: Missing dependencies or incorrect configuration

**Solution**:
1. Run setup script again: `./scripts/setup.sh`
2. Check Rust installation: `rustc --version`
3. Check Tauri CLI: `npm run tauri --version`
4. Review error logs in console

### "App launches but backend doesn't start"

**Cause**: Backend executable missing execute permissions

**Solution** (Linux/macOS):
```bash
chmod +x src-tauri/binaries/novel-writer-backend-*
```

### "Large file size"

**Cause**: Debug symbols included

**Solution**: Use release build:
```bash
npm run tauri:build  # (not --debug)
```

## 📊 Expected File Sizes

| Platform | Format | Size (Approx) |
|----------|--------|---------------|
| Windows  | .msi   | 120-150 MB    |
| macOS    | .dmg   | 130-160 MB    |
| Linux    | .deb   | 110-140 MB    |
| Linux    | .AppImage | 140-170 MB |

*Sizes include the bundled Python interpreter and all dependencies*

## 🔄 Updating the Application

### For Developers

1. Make your changes
2. Update version in `package.json` and `src-tauri/tauri.conf.json`
3. Run `npm run build:all`
4. Test the new installer
5. Distribute to users

### For End Users

Users simply:
1. Download new installer
2. Run it (will upgrade existing installation)
3. Launch app with new features

**Note**: Add auto-update feature in future versions using Tauri's updater

## 🎉 Summary

Building installers for Novel Writer is straightforward:

```bash
# One command to rule them all
npm run build:all
```

This creates professional, distributable installers that:
- Install with one click
- Create desktop shortcuts automatically
- Bundle all dependencies
- Work offline (except for API calls)
- Uninstall cleanly

Users get a **native desktop app experience** - no Python installation, no terminal commands, no configuration files!

---

**Need help?** Check the [main README](README.md) or open an issue on GitHub.
