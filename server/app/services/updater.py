"""
Auto-updater for CodeForge server.
Checks GitHub Releases, downloads updates, supports rollback.
"""

import os
import json
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Optional
import urllib.request

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com/repos/codeforge/codeforge/releases/latest"
BACKUP_DIR_NAME = ".codeforge-backup"


class UpdateInfo:
    """Information about an available update."""
    def __init__(self, version: str, download_url: str, notes: str, size_mb: float):
        self.version = version
        self.download_url = download_url
        self.notes = notes
        self.size_mb = size_mb


def get_current_version() -> str:
    """Get the currently installed version."""
    return settings.APP_VERSION


def check_for_updates() -> Optional[UpdateInfo]:
    """
    Check GitHub for newer versions.
    Returns UpdateInfo if update available, None if current is latest.
    """
    current = get_current_version()
    
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "CodeForge-Updater", "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
        
        latest = data.get("tag_name", "").lstrip("v")
        if not latest:
            logger.warning("Could not parse latest version from GitHub")
            return None
        
        if latest == current:
            logger.debug(f"Already at latest version: {current}")
            return None
        
        # Find server asset
        download_url = ""
        size_mb = 0.0
        for asset in data.get("assets", []):
            if "server" in asset.get("name", "").lower():
                download_url = asset.get("browser_download_url", "")
                size_mb = asset.get("size", 0) / (1024 * 1024)
                break
        
        if not download_url:
            download_url = data.get("zipball_url", "")
        
        notes = data.get("body", "No release notes available.")[:500]
        
        logger.info(f"Update available: {current} -> {latest}")
        return UpdateInfo(
            version=latest,
            download_url=download_url,
            notes=notes,
            size_mb=size_mb,
        )
        
    except Exception as e:
        logger.debug(f"Update check failed (normal if offline): {e}")
        return None


def backup_current_version() -> Path:
    """Create a backup of the current installation."""
    base_dir = settings.BASE_DIR
    backup_dir = base_dir.parent / BACKUP_DIR_NAME
    
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    shutil.copytree(base_dir, backup_dir, ignore=shutil.ignore_patterns(
        "venv", "__pycache__", "*.pyc", "logs", "models", ".git"
    ))
    logger.info(f"Backup created: {backup_dir}")
    return backup_dir


def rollback_to_backup() -> bool:
    """Restore the previous version from backup."""
    base_dir = settings.BASE_DIR
    backup_dir = base_dir.parent / BACKUP_DIR_NAME
    
    if not backup_dir.exists():
        logger.error("No backup found for rollback")
        return False
    
    try:
        for item in base_dir.iterdir():
            if item.name not in ("venv", "models", "logs"):
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink()
        
        for item in backup_dir.iterdir():
            dest = base_dir / item.name
            if item.is_dir():
                if not dest.exists():
                    shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        
        logger.info("Rollback successful")
        return True
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False


def perform_update(download_url: str) -> bool:
    """
    Download and apply an update.
    Returns True on success, False on failure (triggers rollback).
    """
    backup_current_version()
    
    try:
        logger.info(f"Downloading update from {download_url}")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            urllib.request.urlretrieve(download_url, tmp.name)
            zip_path = tmp.name
        
        extract_dir = tempfile.mkdtemp()
        shutil.unpack_archive(zip_path, extract_dir)
        
        server_dir = None
        for root, dirs, files in os.walk(extract_dir):
            if "app" in dirs and "requirements.txt" in files:
                server_dir = Path(root)
                break
        
        if not server_dir:
            raise Exception("Could not find server files in update package")
        
        base_dir = settings.BASE_DIR
        for item in server_dir.iterdir():
            dest = base_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        
        os.unlink(zip_path)
        shutil.rmtree(extract_dir)
        
        logger.info("Update applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        rollback_to_backup()
        return False


def restart_server() -> None:
    """Restart the server process."""
    logger.info("Restarting server...")
    os.execv(sys.executable, [sys.executable] + sys.argv)