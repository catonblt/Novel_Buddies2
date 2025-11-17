# Novel Writer Installer

This directory contains installer scripts and configurations for building professional installers for Novel Writer.

## Windows Installer (Inno Setup)

### Features

✅ **Wizard-Based Installation**
- Modern wizard interface
- Step-by-step guidance
- Progress tracking with detailed logging

✅ **Prerequisite Checking**
- Windows version validation (Windows 10+)
- Disk space verification (500 MB required)
- Administrator rights check
- WebView2 Runtime detection

✅ **Error Handling**
- Detailed error messages
- Installation logging
- Automatic rollback on failure
- Validation after installation

✅ **User Experience**
- Before/after information screens
- Desktop shortcut creation
- Start menu entries
- Quick Start Guide access

### Prerequisites to Build

1. **Inno Setup 6**
   - Download: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

2. **Development Tools**
   - Node.js 18+
   - Python 3.9+
   - Rust (latest)

### Building the Installer

**Option 1: Automated Build (Recommended)**

```cmd
REM Using batch script
cd installer\windows
build-installer.bat
```

Or PowerShell:
```powershell
cd installer\windows
.\build-installer.ps1
```

**Option 2: Manual Build**

```cmd
REM 1. Build the application
npm run build:all

REM 2. Compile installer with Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\novel-writer.iss
```

### Output

Installer is created at:
```
src-tauri\target\release\bundle\nsis\NovelWriter_Setup_1.0.0.exe
```

## Installer Configuration

### Files

- **novel-writer.iss** - Main Inno Setup script
  - Wizard configuration
  - File mappings
  - Prerequisite checks
  - Error handling logic

- **installer-info.txt** - Pre-installation information
  - System requirements
  - What will be installed
  - First-time setup instructions

- **installer-complete.txt** - Post-installation information
  - Next steps
  - Troubleshooting tips
  - Getting started guide

- **build-installer.bat/ps1** - Automated build scripts
  - Dependency checking
  - Multi-step build process
  - Error handling

### Customization

**Change App Name/Version:**

Edit `novel-writer.iss`:
```pascal
#define MyAppName "Novel Writer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Name"
```

**Modify Prerequisite Checks:**

Edit the `[Code]` section in `novel-writer.iss`:
```pascal
function CheckWindowsVersion(): Boolean;
function CheckDiskSpace(): Boolean;
function CheckWebView2(): Boolean;
```

**Add Custom Steps:**

In `novel-writer.iss`, add to:
```pascal
procedure CurStepChanged(CurStep: TSetupStep);
```

## Installation Process

### What Gets Installed

1. **Main Application**
   - `Novel Writer.exe` (Tauri app)
   - Required DLLs

2. **Python Backend**
   - `backend\novel-writer-backend.exe`
   - Bundled dependencies

3. **Frontend Assets**
   - `dist\*` (React app)

4. **Documentation**
   - `docs\README.txt`
   - `docs\QUICK_START.txt`
   - `docs\LICENSE.txt`

5. **Installation Log**
   - `logs\installation.log`

### Installation Steps

1. **Welcome Screen**
   - Installer introduction

2. **License Agreement**
   - MIT License display

3. **Pre-Installation Information**
   - System requirements
   - What will be installed

4. **Installation Directory**
   - Choose where to install
   - Default: `C:\Program Files\Novel Writer\`

5. **Ready to Install**
   - Confirm settings
   - **Prerequisite checks run here**

6. **Installation Progress**
   - File copying
   - Validation
   - Logging

7. **Post-Installation Information**
   - Next steps
   - Getting started

8. **Finish**
   - Option to launch app immediately

## Error Handling

### Logging

Installation creates detailed logs at:
```
C:\Program Files\Novel Writer\logs\installation.log
```

**Log Format:**
```
2024-01-15 14:30:00 - INFO: Checking system prerequisites...
2024-01-15 14:30:01 - SUCCESS: Windows version compatible: 10.0
2024-01-15 14:30:02 - SUCCESS: All prerequisites met
2024-01-15 14:30:10 - SUCCESS: Installation completed successfully!
```

### Error Messages

The installer provides detailed error messages:

**Prerequisites Failed:**
```
Installation cannot continue due to failed prerequisites.
Please check the Installation Progress page for details.
```

**File Not Found:**
```
ERROR: Installation file not found: [filename]
```

**Access Denied:**
```
ERROR: Access denied. Please run as administrator: [details]
```

**Validation Failed:**
```
Installation validation failed. Some components may be missing.
Please check the installation log.
```

### Troubleshooting

See [INSTALLER_TROUBLESHOOTING.md](INSTALLER_TROUBLESHOOTING.md) for:
- Common issues and solutions
- Step-by-step troubleshooting
- Log analysis
- Manual fixes

## Testing the Installer

### Pre-Release Testing

1. **Clean Test Environment:**
   - Use fresh Windows 10/11 VM
   - No dev tools installed
   - Standard user permissions

2. **Installation Test:**
   - Run installer as admin
   - Verify all steps complete
   - Check desktop shortcut created
   - Launch application

3. **Validation:**
   - Backend starts automatically
   - UI loads correctly
   - Can create project
   - Settings persist

4. **Uninstallation Test:**
   - Uninstall via Windows Settings
   - Verify clean removal
   - No leftover files in Program Files
   - No leftover registry entries

### Automated Testing

```powershell
# Install silently
NovelWriter_Setup_1.0.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG="install.log"

# Check if installed
Test-Path "C:\Program Files\Novel Writer\Novel Writer.exe"

# Uninstall silently
& "C:\Program Files\Novel Writer\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
```

## Distribution

### File Naming

Follow convention:
```
NovelWriter_Setup_[VERSION].exe

Example:
NovelWriter_Setup_1.0.0.exe
```

### Checksums

Generate SHA256 checksum for verification:

```powershell
Get-FileHash "NovelWriter_Setup_1.0.0.exe" -Algorithm SHA256
```

Include in release notes.

### Hosting

Recommended platforms:
- **GitHub Releases** - Free, version controlled
- **Website** - Direct download
- **Microsoft Store** - Requires signing

### Code Signing (Future)

For production releases:

1. Obtain code signing certificate
2. Update `novel-writer.iss`:
   ```pascal
   SignTool=signtool sign /f "cert.pfx" /p "password" /t http://timestamp.server $f
   ```
3. Sign both installer and application

## Maintenance

### Updating Version

1. Update `package.json`:
   ```json
   "version": "1.0.1"
   ```

2. Update `src-tauri/tauri.conf.json`:
   ```json
   "version": "1.0.1"
   ```

3. Update `installer/windows/novel-writer.iss`:
   ```pascal
   #define MyAppVersion "1.0.1"
   ```

4. Rebuild installer

### Adding New Files

Edit `novel-writer.iss` `[Files]` section:
```pascal
Source: "path\to\new\file"; DestDir: "{app}\destination"; Flags: ignoreversion
```

### Modifying Checks

Add new prerequisite checks in `[Code]` section:
```pascal
function CheckNewRequirement(): Boolean;
begin
  // Check logic
  if (requirement_met) then
  begin
    LogSuccess('Requirement met');
    Result := True;
  end
  else
  begin
    LogError('Requirement not met');
    Result := False;
  end;
end;
```

Call in `NextButtonClick`:
```pascal
if not CheckNewRequirement() then
  Result := False;
```

## Support

**Build Issues:**
- Check [INSTALLER_TROUBLESHOOTING.md](INSTALLER_TROUBLESHOOTING.md)
- Verify Inno Setup is installed correctly
- Ensure all build steps completed

**Runtime Issues:**
- Check installation log
- Verify WebView2 installed
- Run as administrator

**Questions:**
- GitHub Issues: https://github.com/yourusername/novel-writer/issues
- Discussions: https://github.com/yourusername/novel-writer/discussions

---

**Happy Building! 🚀**
