# Installer Troubleshooting Guide

## Common Installation Issues and Solutions

### Issue 1: "Installation failed - Prerequisites not met"

**Symptoms:**
- Installer shows error about missing prerequisites
- Installation log shows "ERROR: Windows version not compatible" or similar

**Solutions:**

1. **Check Windows Version:**
   - Press `Win + R`, type `winver`, press Enter
   - Ensure you're running Windows 10 (build 1809) or later
   - **Fix:** Upgrade Windows through Windows Update

2. **Run as Administrator:**
   - Right-click the installer
   - Select "Run as administrator"
   - Click "Yes" when prompted

3. **Check Disk Space:**
   - Open File Explorer → This PC
   - Ensure C: drive has at least 500 MB free
   - **Fix:** Free up disk space or install to different drive

### Issue 2: "WebView2 Runtime not found"

**Symptoms:**
- Warning during installation about WebView2
- Application launches but shows blank window

**Solutions:**

1. **Install WebView2 Runtime:**
   - Download from: https://developer.microsoft.com/en-us/microsoft-edge/webview2/
   - Choose "Evergreen Bootstrapper"
   - Run the installer
   - Restart Novel Writer

2. **Update Windows:**
   - Go to Settings → Update & Security → Windows Update
   - Install all available updates
   - WebView2 is included in recent Windows updates

### Issue 3: "Backend executable not found"

**Symptoms:**
- Application launches but can't connect to backend
- Error message: "Failed to start backend server"
- Installation log shows missing backend files

**Solutions:**

1. **Check Installation:**
   - Navigate to installation folder (usually `C:\Program Files\Novel Writer\`)
   - Verify `backend\novel-writer-backend.exe` exists
   - **Fix:** Reinstall the application

2. **Antivirus Blocking:**
   - Check Windows Defender or antivirus logs
   - The backend executable might be quarantined
   - **Fix:** Add Novel Writer folder to antivirus exclusions:
     ```
     C:\Program Files\Novel Writer\
     ```

3. **Firewall Blocking:**
   - Backend runs on port 8000
   - Windows Firewall might block it
   - **Fix:** Allow Novel Writer through firewall:
     - Settings → Update & Security → Windows Security → Firewall & network protection
     - Allow an app through firewall
     - Add `novel-writer-backend.exe`

### Issue 4: "Access Denied" errors

**Symptoms:**
- Installation fails with "Access Denied"
- Can't write to Program Files
- Installation log shows ERROR_ACCESS_DENIED

**Solutions:**

1. **Run Installer as Administrator:**
   - Right-click installer
   - Select "Run as administrator"
   - This is required for Program Files installation

2. **Check User Permissions:**
   - Ensure you have admin rights on the computer
   - **Fix:** Contact your IT administrator

3. **Antivirus Interference:**
   - Some antivirus programs block installations
   - Temporarily disable antivirus during installation
   - Re-enable after installation completes

### Issue 5: "Installation validation failed"

**Symptoms:**
- Installer completes but shows validation errors
- Some components reported as missing
- Application won't launch

**Solutions:**

1. **Check Installation Log:**
   - Open `C:\Program Files\Novel Writer\logs\installation.log`
   - Look for specific errors
   - Share log when reporting issues

2. **Corrupted Download:**
   - Installer file may be corrupted
   - **Fix:** Re-download the installer
   - Verify file size matches expected size
   - Compare SHA256 checksum if provided

3. **Incomplete Installation:**
   - Installation was interrupted
   - **Fix:**
     - Uninstall Novel Writer completely
     - Delete `C:\Program Files\Novel Writer\` folder
     - Restart computer
     - Reinstall

### Issue 6: "Application won't start after installation"

**Symptoms:**
- Installation succeeds
- Double-clicking icon does nothing
- Or application crashes immediately

**Solutions:**

1. **Check Event Viewer:**
   - Press `Win + X` → Event Viewer
   - Look under Windows Logs → Application
   - Find Novel Writer errors
   - Share error details when reporting

2. **Missing Dependencies:**
   - Open installation folder
   - Look for `*.dll` files
   - **Fix:** Reinstall Microsoft Visual C++ Redistributables:
     - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
     - Install and restart

3. **Port 8000 Already in Use:**
   - Another program might be using port 8000
   - Check with: `netstat -ano | findstr :8000`
   - **Fix:** Close the conflicting program or change Novel Writer's port

4. **Run Compatibility Troubleshooter:**
   - Right-click Novel Writer shortcut
   - Properties → Compatibility → Run compatibility troubleshooter
   - Try recommended settings

### Issue 7: "Installation hangs or freezes"

**Symptoms:**
- Installer stops responding
- Progress bar stuck
- "Not Responding" in Task Manager

**Solutions:**

1. **Wait Patiently:**
   - Building backend executable takes 2-5 minutes
   - Progress dialog might not update frequently
   - Give it 10 minutes before force-closing

2. **Check Task Manager:**
   - Press `Ctrl + Shift + Esc`
   - Look for `python.exe` or `pyinstaller`
   - If CPU usage is high, installation is working

3. **Force Close and Retry:**
   - If truly frozen (10+ minutes, no disk/CPU activity):
   - End installer process in Task Manager
   - Delete partial installation
   - Restart computer
   - Try again

4. **Disable Antivirus Temporarily:**
   - Antivirus real-time scanning can slow installation
   - Disable temporarily, install, then re-enable

### Issue 8: "Desktop shortcut not created"

**Symptoms:**
- Installation completes
- No shortcut on desktop
- Application installed but hard to find

**Solutions:**

1. **Check Start Menu:**
   - Press Windows key
   - Type "Novel Writer"
   - Right-click → Pin to Start or Pin to Taskbar

2. **Create Shortcut Manually:**
   - Navigate to `C:\Program Files\Novel Writer\`
   - Right-click `Novel Writer.exe`
   - Send to → Desktop (create shortcut)

3. **Reinstall with Desktop Icon:**
   - During installation
   - Ensure "Create a desktop icon" is checked

## Advanced Troubleshooting

### Viewing Installation Logs

**Location:**
```
C:\Program Files\Novel Writer\logs\installation.log
```

**What to Look For:**
- Lines starting with `ERROR:`
- Lines starting with `WARNING:`
- Last few lines before failure

**Sharing Logs:**
When reporting issues, include:
1. Complete installation log
2. Windows version (`winver`)
3. Steps that led to the error
4. Screenshots of error messages

### Clean Reinstallation

If all else fails:

1. **Uninstall:**
   - Settings → Apps → Novel Writer → Uninstall
   - Or use uninstaller in Start Menu

2. **Clean Up:**
   - Delete `C:\Program Files\Novel Writer\`
   - Delete `C:\Users\[YourName]\AppData\Local\Novel Writer\`
   - Empty Recycle Bin

3. **Restart:**
   - Restart computer

4. **Reinstall:**
   - Download fresh installer
   - Run as administrator
   - Watch for errors

### Checking File Integrity

**Verify downloaded installer:**

```powershell
# PowerShell command
Get-FileHash "NovelWriter_Setup_1.0.0.exe" -Algorithm SHA256
```

Compare with published checksum.

### Manual Backend Test

Test if backend works independently:

```cmd
cd "C:\Program Files\Novel Writer\backend"
novel-writer-backend.exe --port 8000
```

If it starts, you should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Press `Ctrl+C` to stop.

## Still Having Issues?

### Before Reporting:

- [ ] Tried running as administrator
- [ ] Checked installation log
- [ ] Verified Windows version (10+)
- [ ] Disabled antivirus temporarily
- [ ] Tried clean reinstallation
- [ ] Checked firewall settings

### Report an Issue:

1. **GitHub Issues:** https://github.com/yourusername/novel-writer/issues

2. **Include:**
   - Windows version
   - Installation log
   - Error messages (screenshots)
   - Steps to reproduce
   - What you've already tried

3. **Template:**
   ```
   **Problem:**
   Describe the issue

   **Windows Version:**
   (Press Win+R, type "winver")

   **Steps to Reproduce:**
   1. Downloaded installer
   2. Ran as admin
   3. ...

   **Error Messages:**
   (Paste or screenshot)

   **Installation Log:**
   (Attach installation.log file)

   **What I've Tried:**
   - Ran as administrator
   - Disabled antivirus
   - ...
   ```

## Known Issues

### Issue: Installation Slow on Some Systems

**Cause:** PyInstaller bundling can be slow on systems with aggressive antivirus

**Workaround:** Temporarily disable real-time scanning during installation

### Issue: False Positive Virus Detection

**Cause:** PyInstaller executables sometimes trigger false positives

**Solution:**
- Novel Writer is open source and safe
- Add to antivirus exclusions
- Or wait for signed releases (future)

---

**Need more help?**
- Documentation: https://github.com/yourusername/novel-writer
- Community: https://github.com/yourusername/novel-writer/discussions
