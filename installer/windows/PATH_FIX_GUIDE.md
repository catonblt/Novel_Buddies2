# Path Fix Guide for Windows Installer

## Problem

When building the Inno Setup installer, it needs to find files relative to where the `.iss` script is located (`installer/windows/`).

## Solution

The paths in `novel-writer.iss` now use **double dots** (`..\..\`) to go up two levels to the project root.

### Path Structure

```
Novel_Buddies/                      (Project Root)
├── installer/
│   └── windows/
│       ├── novel-writer.iss        (You are here)
│       └── build-installer.bat
├── src-tauri/
│   ├── target/release/
│   │   └── Novel Writer.exe
│   └── binaries/
│       └── novel-writer-backend-*.exe
├── dist/                           (Frontend build output)
├── package.json
└── LICENSE
```

### Corrected Paths

From `installer/windows/novel-writer.iss`:

| What | Old Path | New Path |
|------|----------|----------|
| License | `..\LICENSE` | `..\..\LICENSE` |
| Icon | `..\src-tauri\icons\icon.ico` | `..\..\src-tauri\icons\icon.ico` |
| Output | `..\src-tauri\target\...` | `..\..\src-tauri\target\...` |
| Main App | `..\src-tauri\target\release\...` | `..\..\src-tauri\target\release\...` |
| Backend | `..\src-tauri\binaries\...` | `..\..\src-tauri\binaries\...` |
| Frontend | `..\dist\*` | `..\..\dist\*` |
| Docs | `..\README.md` | `..\..\README.md` |

## How to Build

### Option 1: From Project Root (Recommended)

```cmd
cd C:\path\to\Novel_Buddies
installer\windows\build-installer.bat
```

The script now checks that you're in the project root.

### Option 2: From installer/windows Directory

Use the wrapper script:

```cmd
cd C:\path\to\Novel_Buddies\installer\windows
build-from-here.bat
```

This automatically navigates to project root before building.

### Option 3: PowerShell

```powershell
cd C:\path\to\Novel_Buddies
.\installer\windows\build-installer.ps1
```

Or use the wrapper:

```powershell
cd C:\path\to\Novel_Buddies\installer\windows
.\build-from-here.ps1
```

## Verification

Before running Inno Setup, the build script now:

1. ✅ Checks you're in project root
2. ✅ Verifies `package.json` exists
3. ✅ Shows current directory
4. ✅ Gives clear error if in wrong location

## What If It Still Fails?

### Check Your Location

```cmd
cd
```

Should show: `C:\path\to\Novel_Buddies` (project root)

### Verify Files Exist

```cmd
dir src-tauri\target\release\Novel Writer.exe
dir src-tauri\binaries\novel-writer-backend-*.exe
dir dist
dir LICENSE
```

All should exist before running Inno Setup.

### Build Order

1. Frontend must be built first: `npm run build`
2. Backend must be built: `cd python-backend && python build.py`
3. Tauri must be built: `npm run tauri build`
4. Then run Inno Setup

The `build-installer.bat` script does all this automatically!

## Error Messages

### "ERROR: Please run this script from the project root directory"

**Solution**:
```cmd
cd C:\path\to\Novel_Buddies
installer\windows\build-installer.bat
```

### "Cannot find file: ..\..\LICENSE"

**Cause**: Running from wrong directory or file doesn't exist

**Solution**: Make sure LICENSE file exists in project root

### "Cannot find file: ..\..\src-tauri\target\release\Novel Writer.exe"

**Cause**: Tauri app not built yet

**Solution**: Run `npm run tauri build` first, or use `build-installer.bat` which does it automatically

## Quick Reference

**Always run from project root:**
```
Novel_Buddies/
├── You should be here when running: installer\windows\build-installer.bat
```

**Not from here:**
```
Novel_Buddies/installer/windows/
├── Don't run from here (unless using build-from-here.bat)
```
