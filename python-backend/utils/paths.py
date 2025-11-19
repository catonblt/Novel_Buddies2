"""
Path utilities for NovelWriter application.

Handles platform-specific paths for production (frozen .exe) vs development environments.
When packaged as an .exe, the app cannot write to Program Files and must use %LOCALAPPDATA%.
"""

import os
import sys
from pathlib import Path


def get_app_data_path() -> Path:
    """
    Get the appropriate application data directory.

    In production (frozen .exe), returns %LOCALAPPDATA%/NovelBuddies on Windows
    or appropriate platform-specific directories.

    In development, returns the current working directory.

    Returns:
        Path object for the application data directory
    """
    # Check if we're running as a frozen executable (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Production mode - use platform-specific app data directory
        if sys.platform == 'win32':
            # Windows: use LOCALAPPDATA
            local_app_data = os.environ.get('LOCALAPPDATA')
            if local_app_data:
                app_path = Path(local_app_data) / "NovelBuddies"
            else:
                # Fallback if LOCALAPPDATA is not set
                app_path = Path.home() / "AppData" / "Local" / "NovelBuddies"
        elif sys.platform == 'darwin':
            # macOS: use Application Support
            app_path = Path.home() / "Library" / "Application Support" / "NovelBuddies"
        else:
            # Linux: use XDG_DATA_HOME or ~/.local/share
            xdg_data = os.environ.get('XDG_DATA_HOME')
            if xdg_data:
                app_path = Path(xdg_data) / "NovelBuddies"
            else:
                app_path = Path.home() / ".local" / "share" / "NovelBuddies"

        # Ensure the directory exists
        app_path.mkdir(parents=True, exist_ok=True)
        return app_path
    else:
        # Development mode - use current working directory
        return Path.cwd()


def get_log_path() -> Path:
    """
    Get the path for application logs.

    Returns:
        Path object for the logs directory
    """
    return get_app_data_path() / "logs"


def get_database_path() -> Path:
    """
    Get the path for the SQLite database.

    Returns:
        Path object for the database file
    """
    return get_app_data_path() / "novelwriter.db"


def get_global_chroma_path() -> Path:
    """
    Get the path for global ChromaDB storage.

    Note: For project-specific memory, use the .novel_buddies folder
    within each project directory instead.

    Returns:
        Path object for the ChromaDB directory
    """
    return get_app_data_path() / "chroma_db"
