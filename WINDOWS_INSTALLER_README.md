# ✨ Windows Installer Wizard - Complete Guide

## 🎉 Professional Installation Experience

Your Novel Writer application now has a **professional Windows installer wizard** with comprehensive error handling, prerequisite checking, and detailed logging!

## 📥 For End Users

### Simple Installation

1. **Download**: `NovelWriter_Setup_1.0.0.exe`
2. **Double-click** to launch the installer wizard
3. **Follow the wizard**:
   - Welcome screen
   - License agreement
   - Pre-installation information
   - Choose installation directory
   - Click "Install"
4. **Automatic checks** happen:
   - Windows version verified
   - Administrator rights confirmed
   - Disk space checked
   - WebView2 detected (auto-installs if missing)
5. **Installation completes**
6. **Desktop shortcut** appears automatically
7. **Launch and enjoy!**

### What Makes This Better?

✅ **Step-by-Step Wizard** - Professional installation experience
✅ **Prerequisite Checking** - Validates your system before installing
✅ **Clear Error Messages** - If something fails, you know exactly what and why
✅ **Installation Logging** - Complete log file for troubleshooting
✅ **Automatic Validation** - Verifies installation succeeded
✅ **Rollback on Failure** - No partial installations left behind
✅ **Help Screens** - Information before and after installation

## 🛠️ For Developers

### Building the Wizard Installer

#### Prerequisites

1. **Install Inno Setup 6**:
   - Download: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`
   - This is the tool that creates the wizard installer

2. **Have Development Tools**:
   - Node.js 18+ (for frontend)
   - Python 3.9+ (for backend)
   - Rust (for Tauri)

#### Quick Build

**Method 1: Automated Build Script (Recommended)**

```cmd
cd installer\windows
build-installer.bat
```

Or PowerShell:
```powershell
cd installer\windows
.\build-installer.ps1
```

This script:
- ✅ Checks for all required tools
- ✅ Installs npm dependencies
- ✅ Sets up Python environment
- ✅ Builds Python backend executable
- ✅ Builds frontend
- ✅ Builds Tauri application
- ✅ Compiles Inno Setup installer
- ✅ Shows progress at each step
- ✅ Handles errors gracefully

**Method 2: Manual Steps**

```cmd
REM 1. Install dependencies
npm install

REM 2. Setup Python
cd python-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

REM 3. Build backend
python build.py
cd ..

REM 4. Build frontend
npm run build

REM 5. Build Tauri
npm run tauri build

REM 6. Compile installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\novel-writer.iss
```

#### Output

Installer created at:
```
src-tauri\target\release\bundle\nsis\NovelWriter_Setup_1.0.0.exe
```

**File size**: ~120-150 MB (everything bundled!)

## 🔍 What's Included

### Installer Features

#### 1. Prerequisite Checks

The installer automatically checks:

**Windows Version:**
- Requires Windows 10 or later
- Shows your current version
- Blocks installation if too old

**Administrator Rights:**
- Checks if running as admin
- Prompts to run as admin if not
- Required for Program Files installation

**Disk Space:**
- Requires 500 MB minimum
- Shows available space
- Warns if insufficient

**WebView2 Runtime:**
- Checks if WebView2 is installed
- Warns if missing (not blocking)
- Can auto-install WebView2

#### 2. Error Handling

Every error includes:
- ❌ **Clear error message**: What went wrong
- ℹ **Context**: Why it's a problem
- 💡 **Solution**: How to fix it
- 📝 **Logging**: Saved to installation.log

**Example Error:**
```
❌ ERROR: Insufficient disk space
   Required: 500 MB
   Available: 234 MB

ℹ INFO: Please free up disk space and try again.
        See installation log at:
        C:\Program Files\Novel Writer\logs\installation.log

💡 SOLUTION:
   - Delete temporary files
   - Empty Recycle Bin
   - Or install to different drive
```

#### 3. Installation Logging

Complete log saved to:
```
C:\Program Files\Novel Writer\logs\installation.log
```

**Log includes:**
```
2024-01-15 14:30:00 - === Novel Writer Installation Started ===
2024-01-15 14:30:00 - INFO: Installer Version: 1.0.0
2024-01-15 14:30:01 - INFO: Checking system prerequisites...
2024-01-15 14:30:01 - SUCCESS: Windows version compatible: 10.0
2024-01-15 14:30:02 - SUCCESS: Administrator privileges confirmed
2024-01-15 14:30:03 - SUCCESS: Disk space available: 52347 MB
2024-01-15 14:30:04 - WARNING: WebView2 Runtime not found
2024-01-15 14:30:05 - INFO: WebView2 will be installed
2024-01-15 14:30:15 - SUCCESS: All prerequisites met
2024-01-15 14:30:16 - INFO: Beginning file installation...
2024-01-15 14:30:45 - INFO: Validating installation...
2024-01-15 14:30:46 - SUCCESS: Main application installed successfully
2024-01-15 14:30:47 - SUCCESS: Backend installed successfully
2024-01-15 14:30:48 - SUCCESS: Frontend assets installed successfully
2024-01-15 14:30:49 - SUCCESS: Installation completed successfully!
2024-01-15 14:30:50 - === Installation Process Ended ===
```

#### 4. Validation

After installation, automatic validation checks:
- ✅ Main executable exists
- ✅ Backend executable exists
- ✅ Frontend assets present
- ✅ All required DLLs in place

If validation fails:
- Clear error message
- Installation log shows details
- Option to retry or contact support

#### 5. Wizard Screens

**Welcome:**
- Application introduction
- What will be installed

**License:**
- MIT License text
- Must accept to continue

**Pre-Installation Info:**
- System requirements
- What's included
- First-time setup steps

**Select Directory:**
- Choose installation location
- Default: `C:\Program Files\Novel Writer\`
- Shows required disk space

**Ready to Install:**
- Confirms settings
- **Prerequisite checks run here**
- Shows any warnings/errors

**Installing:**
- Progress bar
- Current step shown
- Real-time logging visible

**Post-Installation Info:**
- Success message
- Next steps (API key setup)
- Troubleshooting quick tips
- Links to documentation

**Finish:**
- Option to launch immediately
- Links to Quick Start Guide

## 📖 Configuration Files

### Installer Script

**File**: `installer/windows/novel-writer.iss`

Inno Setup script with:
- 600+ lines of code
- Prerequisite checking functions
- Error handling logic
- Logging system
- Validation functions
- Custom wizard pages

**Key Sections:**
```pascal
[Setup]          - Installer configuration
[Languages]      - Supported languages
[Tasks]          - Desktop/Start Menu shortcuts
[Files]          - What to install
[Icons]          - Shortcuts to create
[Code]           - Pascal scripting (logic)
```

### Information Screens

**installer-info.txt** - Before installation:
- System requirements
- What will be installed
- Prerequisite software
- First-time setup guide

**installer-complete.txt** - After installation:
- Success message
- Next steps
- Troubleshooting tips
- Documentation links

### Build Scripts

**build-installer.bat** - Windows batch script
**build-installer.ps1** - PowerShell script

Both scripts:
- Check for required tools
- Run all build steps
- Handle errors
- Show progress
- Create final installer

## 🚨 Troubleshooting

### Installation Fails

**Check the log file:**
```
C:\Program Files\Novel Writer\logs\installation.log
```

**Common issues:**

1. **"Prerequisites not met"**
   - Run as administrator
   - Check Windows version (need Windows 10+)
   - Free up disk space (need 500 MB)

2. **"WebView2 not found"**
   - Download: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
   - Or update Windows (includes WebView2)

3. **"Access Denied"**
   - Right-click installer
   - Select "Run as administrator"

4. **"Validation failed"**
   - Antivirus might be blocking
   - Add Novel Writer folder to exclusions
   - Or temporarily disable antivirus

5. **Installation hangs**
   - Building backend takes 2-5 minutes
   - Check Task Manager for activity
   - If truly frozen, restart and try again

### Comprehensive Guide

See **installer/INSTALLER_TROUBLESHOOTING.md** for:
- 8 common issues with solutions
- Step-by-step fixes
- Error message explanations
- Advanced troubleshooting
- Clean reinstallation guide
- Issue reporting template

## 📊 What Users Experience

### Before (Old Way):
1. Download source code
2. Install Node.js manually
3. Install Python manually
4. Install Rust manually
5. Open terminal
6. Run npm install
7. Create Python venv
8. pip install requirements
9. Run two terminals
10. Figure out how to start both servers
11. Configure settings
12. Finally start using...

**Time**: 30-60 minutes for technical users

### After (New Way):
1. Download NovelWriter_Setup_1.0.0.exe
2. Double-click
3. Click "Next" a few times
4. Done!

**Time**: 2-3 minutes for anyone!

## 🎯 Key Improvements

### Error Messages

**Before:**
```
Installation failed.
```

**After:**
```
❌ ERROR: Insufficient disk space
   Required: 500 MB
   Available: 234 MB

ℹ INFO: Installation cannot continue

💡 SOLUTIONS:
   1. Free up disk space:
      - Delete temporary files (Win + R → temp)
      - Empty Recycle Bin
      - Run Disk Cleanup

   2. Install to different drive:
      - Click Back
      - Choose different installation directory

   3. Check what's using space:
      - Open Settings → System → Storage

📝 Details logged to:
   C:\...\installation.log

❓ Need help?
   https://github.com/yourusername/novel-writer/issues
```

### User Confidence

**Old way**: "I hope this works... 🤞"
**New way**: "The installer checked everything! ✅"

## 📝 Files Created

```
installer/
├── windows/
│   ├── novel-writer.iss              (Inno Setup script - 600+ lines)
│   ├── installer-info.txt            (Pre-install information)
│   ├── installer-complete.txt        (Post-install information)
│   ├── install-log-template.txt      (Log file template)
│   ├── build-installer.bat           (Windows build script)
│   └── build-installer.ps1           (PowerShell build script)
├── INSTALLER_TROUBLESHOOTING.md      (Complete troubleshooting guide)
└── README.md                         (Installer documentation)
```

## 🚀 Distribution

### File to Distribute

```
NovelWriter_Setup_1.0.0.exe
Size: ~120-150 MB
```

### Where to Host

**GitHub Releases** (Recommended):
- Free hosting
- Version tracking
- Download statistics
- Automatic checksums

**Website**:
- Direct download link
- Full control
- Custom landing page

**Microsoft Store** (Future):
- Requires developer account ($19/year)
- Needs code signing certificate
- Automatic updates built-in

### Checksum

Generate SHA256 for verification:

```powershell
Get-FileHash "NovelWriter_Setup_1.0.0.exe" -Algorithm SHA256
```

Include in release notes so users can verify download.

## ✨ Summary

You now have a **professional, production-ready Windows installer** that:

✅ Provides step-by-step wizard interface
✅ Checks all prerequisites automatically
✅ Gives detailed error messages with solutions
✅ Creates complete installation logs
✅ Validates installation success
✅ Includes comprehensive troubleshooting guide
✅ Handles errors gracefully
✅ Makes your app installable by anyone!

**Build it with one command:**
```cmd
cd installer\windows
build-installer.bat
```

**Distribute it confidently:**
Users get a professional installation experience with clear feedback and helpful error messages!

---

**Questions or issues?**
- See: `installer/INSTALLER_TROUBLESHOOTING.md`
- Or: `installer/README.md`
- Report: https://github.com/yourusername/novel-writer/issues
