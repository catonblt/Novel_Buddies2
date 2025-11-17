"""
Build script for creating standalone Python backend executable
"""
import subprocess
import sys
import platform
import shutil
import os

def build_backend():
    """Build the Python backend using PyInstaller"""
    print("🔨 Building Novel Writer Backend...")

    # Install PyInstaller if not present
    print("📦 Ensuring PyInstaller is installed...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Run PyInstaller
    print("🏗️  Running PyInstaller...")
    subprocess.run([
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "novel_writer.spec"
    ], check=True)

    # Get the executable name based on platform
    exe_name = "novel-writer-backend.exe" if platform.system() == "Windows" else "novel-writer-backend"
    exe_path = os.path.join("dist", exe_name)

    if os.path.exists(exe_path):
        print(f"✅ Backend executable created: {exe_path}")

        # Copy to project root for Tauri to find
        target_dir = os.path.join("..", "src-tauri", "binaries")
        os.makedirs(target_dir, exist_ok=True)

        # Platform-specific naming for Tauri sidecar
        system = platform.system().lower()
        arch = platform.machine().lower()

        if system == "windows":
            target_name = f"novel-writer-backend-x86_64-pc-windows-msvc.exe"
        elif system == "darwin":
            if arch == "arm64":
                target_name = "novel-writer-backend-aarch64-apple-darwin"
            else:
                target_name = "novel-writer-backend-x86_64-apple-darwin"
        else:  # Linux
            target_name = f"novel-writer-backend-x86_64-unknown-linux-gnu"

        target_path = os.path.join(target_dir, target_name)
        shutil.copy2(exe_path, target_path)

        # Make executable on Unix
        if system != "windows":
            os.chmod(target_path, 0o755)

        print(f"✅ Backend copied to: {target_path}")
        print("🎉 Backend build complete!")
        return True
    else:
        print("❌ Backend executable not found!")
        return False

if __name__ == "__main__":
    success = build_backend()
    sys.exit(0 if success else 1)
