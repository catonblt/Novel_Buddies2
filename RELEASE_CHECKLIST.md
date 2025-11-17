# Release Checklist

Use this checklist when preparing a new release of Novel Writer.

## Pre-Release

### Version Update
- [ ] Update version in `package.json`
- [ ] Update version in `src-tauri/tauri.conf.json`
- [ ] Update version in `src-tauri/Cargo.toml`
- [ ] Update CHANGELOG.md with new features/fixes

### Testing
- [ ] All linters pass (`npm run lint`)
- [ ] Code formatted (`npm run format`)
- [ ] Manual testing of all 5 agents
- [ ] File operations tested (create, edit, delete)
- [ ] Git integration tested (commits, history, restore)
- [ ] Settings persist correctly
- [ ] Project creation wizard works
- [ ] Backend starts automatically in production build

### Build
- [ ] Run automated setup: `./scripts/setup.sh` or `.\scripts\setup.ps1`
- [ ] Build Python backend: `npm run backend:build`
- [ ] Verify backend executable in `src-tauri/binaries/`
- [ ] Build installers: `npm run build:all`
- [ ] Verify installer files created in `src-tauri/target/release/bundle/`

### Platform-Specific Testing

**Windows**:
- [ ] Install from `.msi` on clean Windows machine
- [ ] Verify desktop shortcut appears
- [ ] Verify Start Menu entry
- [ ] App launches and backend starts automatically
- [ ] Test all features
- [ ] Uninstall cleanly (no leftover files)

**macOS**:
- [ ] Install from `.dmg` on clean macOS machine
- [ ] Drag to Applications folder
- [ ] Verify app launches from Applications
- [ ] Backend starts automatically
- [ ] Test all features
- [ ] Uninstall (drag to trash)

**Linux**:
- [ ] Install `.deb` on Ubuntu/Debian
- [ ] Run `.AppImage` on another distro
- [ ] Verify desktop entry appears
- [ ] App launches and backend starts
- [ ] Test all features
- [ ] Uninstall cleanly

### Security (Optional but Recommended)

**Windows**:
- [ ] Code sign with certificate (if available)
- [ ] Update `src-tauri/tauri.conf.json` with certificate info

**macOS**:
- [ ] Sign with Apple Developer ID (if enrolled)
- [ ] Notarize app for Gatekeeper
- [ ] Update `src-tauri/tauri.conf.json` with signing identity

## Release

### GitHub Release
- [ ] Create new tag: `git tag v1.0.0`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Create GitHub Release
- [ ] Write release notes (features, fixes, known issues)
- [ ] Upload installers:
  - [ ] Windows `.msi`
  - [ ] Windows `.exe` (NSIS)
  - [ ] macOS `.dmg`
  - [ ] Linux `.deb`
  - [ ] Linux `.AppImage`
  - [ ] Linux `.rpm` (if built)
- [ ] Mark as "Latest Release" if applicable

### Documentation
- [ ] Update README.md with download links
- [ ] Update QUICK_START.md if needed
- [ ] Ensure all docs reflect current version
- [ ] Check all links work

### Announcement
- [ ] Post on project website (if applicable)
- [ ] Announce on social media (if applicable)
- [ ] Notify users via email list (if applicable)
- [ ] Update any other distribution channels

## Post-Release

### Monitoring
- [ ] Monitor GitHub Issues for bug reports
- [ ] Check download statistics
- [ ] Collect user feedback
- [ ] Note any installation problems

### Next Steps
- [ ] Plan next version features
- [ ] Address critical bugs immediately
- [ ] Update roadmap in README

## Notes

### Version Numbering

Follow Semantic Versioning (semver):
- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features, backwards compatible
- **Patch** (1.0.1): Bug fixes only

### File Naming

Installers should be named:
```
Novel Writer_[VERSION]_[ARCH]_[PLATFORM].[EXTENSION]

Examples:
- Novel Writer_1.0.0_x64_en-US.msi
- Novel Writer_1.0.0_aarch64.dmg
- novel-writer_1.0.0_amd64.deb
```

### SHA Checksums

Generate checksums for each installer:

```bash
# Windows (PowerShell)
Get-FileHash "Novel Writer_1.0.0_x64.msi" -Algorithm SHA256

# macOS/Linux
shasum -a 256 "Novel Writer_1.0.0_x64.dmg"
```

Include checksums in release notes for verification.

---

**Template Release Notes**:

```markdown
# Novel Writer v1.0.0

## ✨ New Features
- Feature 1 description
- Feature 2 description

## 🐛 Bug Fixes
- Fix 1 description
- Fix 2 description

## 📥 Downloads

**Windows**:
- [Novel Writer v1.0.0 (.msi)](link) - Recommended
- [Novel Writer v1.0.0 (.exe)](link) - Alternative

**macOS**:
- [Novel Writer v1.0.0 (.dmg)](link) - Intel & Apple Silicon

**Linux**:
- [Novel Writer v1.0.0 (.deb)](link) - Debian/Ubuntu
- [Novel Writer v1.0.0 (.AppImage)](link) - Universal

## 🔐 Checksums (SHA256)
```
abc123... Novel Writer_1.0.0_x64.msi
def456... Novel Writer_1.0.0_x64.dmg
ghi789... novel-writer_1.0.0_amd64.deb
```

## ⚠️ Known Issues
- Issue 1
- Issue 2

## 📖 Documentation
- [User Guide](link)
- [Installation Guide](link)

**Full Changelog**: [v0.9.0...v1.0.0](link)
```
