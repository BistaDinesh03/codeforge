"""
Smart model downloader with RAM detection, progress tracking, and resume support.
"""

import os
import hashlib
import time
import json
from pathlib import Path
from typing import Optional, Callable
import urllib.request

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Model catalog
MODELS = {
    "qwen-1.5b": {
        "name": "Qwen 2.5 Coder 1.5B",
        "filename": "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf",
        "size_mb": 940,
        "min_ram_gb": 4,
        "description": "Fast, fits in 4GB RAM",
    },
    "deepseek-1.3b": {
        "name": "DeepSeek Coder 1.3B",
        "filename": "DeepSeek-Coder-1.3B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/bartowski/DeepSeek-Coder-1.3B-Instruct-GGUF/resolve/main/DeepSeek-Coder-1.3B-Instruct-Q4_K_M.gguf",
        "size_mb": 780,
        "min_ram_gb": 3,
        "description": "Smallest, works on 3GB RAM",
    },
    "qwen-7b": {
        "name": "Qwen 2.5 Coder 7B",
        "filename": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "size_mb": 4700,
        "min_ram_gb": 8,
        "description": "Smartest, needs 8GB+ RAM",
    },
}


def detect_ram_gb() -> int:
    """Detect available system RAM in GB."""
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024**3))
    except ImportError:
        return 4  # Conservative default


def recommend_model(ram_gb: int | None = None) -> dict:
    """
    Recommend the best model for available RAM.
    
    Returns the smartest model that fits in available RAM.
    """
    if ram_gb is None:
        ram_gb = detect_ram_gb()
    
    # Sort by size descending, pick first that fits
    sorted_models = sorted(MODELS.values(), key=lambda m: m["size_mb"], reverse=True)
    
    for model in sorted_models:
        if ram_gb >= model["min_ram_gb"]:
            return model
    
    # Fallback to smallest model
    return MODELS["deepseek-1.3b"]


def get_download_path(model_key: str) -> Path:
    """Get the full path where a model should be saved."""
    model = MODELS.get(model_key)
    if not model:
        raise ValueError(f"Unknown model: {model_key}")
    return settings.MODELS_DIR / model["filename"]


def verify_checksum(filepath: Path, expected_hash: str | None = None) -> bool:
    """
    Verify a downloaded file using SHA256.
    If no expected hash provided, just check file exists and has reasonable size.
    """
    if not filepath.exists():
        return False
    
    size_mb = filepath.stat().st_size / (1024 * 1024)
    
    # Basic sanity check: file must be > 100MB
    if size_mb < 100:
        return False
    
    if expected_hash:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest() == expected_hash
    
    return True


def download_model(
    model_key: str,
    progress_callback: Optional[Callable[[int, int, float], None]] = None,
) -> Path:
    """
    Download a model with progress tracking and resume support.
    
    Args:
        model_key: Key from MODELS dict (e.g., "qwen-1.5b")
        progress_callback: Called with (downloaded_mb, total_mb, speed_mbps)
    
    Returns:
        Path to the downloaded model file.
    
    Raises:
        ValueError: Unknown model key.
        Exception: Download failed.
    """
    model = MODELS.get(model_key)
    if not model:
        raise ValueError(f"Unknown model: {model_key}")
    
    filepath = get_download_path(model_key)
    url = model["url"]
    total_mb = model["size_mb"]
    
    # Check if already downloaded and valid
    if verify_checksum(filepath):
        logger.info(f"Model already downloaded: {filepath.name}")
        if progress_callback:
            progress_callback(total_mb, total_mb, 0)
        return filepath
    
    # Check for partial download
    existing_size = filepath.stat().st_size if filepath.exists() else 0
    
    logger.info(f"Downloading {model['name']} ({total_mb} MB) to {filepath}")
    
    start_time = time.time()
    downloaded = existing_size
    
    try:
        # Create request with range header for resume
        req = urllib.request.Request(url)
        if existing_size > 0 and existing_size < total_mb * 1024 * 1024:
            req.headers["Range"] = f"bytes={existing_size}-"
            logger.info(f"Resuming from {existing_size / (1024*1024):.0f} MB")
        
        with urllib.request.urlopen(req, timeout=300) as response:
            mode = "ab" if existing_size > 0 else "wb"
            with open(filepath, mode) as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Report progress
                    if progress_callback:
                        elapsed = time.time() - start_time
                        downloaded_mb = downloaded / (1024 * 1024)
                        speed = downloaded_mb / elapsed if elapsed > 0 else 0
                        progress_callback(round(downloaded_mb), total_mb, round(speed, 1))
        
        # Verify
        if not verify_checksum(filepath):
            filepath.unlink(missing_ok=True)
            raise Exception("Downloaded file failed verification. Try again.")
        
        elapsed = time.time() - start_time
        logger.info(f"Downloaded {model['name']} in {elapsed:.0f}s")
        
        return filepath
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        # Keep partial file for resume
        raise


def get_download_status(model_key: str) -> dict:
    """Get the download status of a model."""
    try:
        model = MODELS.get(model_key)
        if not model:
            return {"status": "unknown", "error": f"Unknown model: {model_key}"}
        
        filepath = get_download_path(model_key)
        
        if verify_checksum(filepath):
            return {
                "status": "complete",
                "filename": model["filename"],
                "size_mb": model["size_mb"],
                "path": str(filepath),
            }
        
        if filepath.exists():
            partial_mb = round(filepath.stat().st_size / (1024 * 1024))
            return {
                "status": "partial",
                "filename": model["filename"],
                "downloaded_mb": partial_mb,
                "total_mb": model["size_mb"],
                "percent": round((partial_mb / model["size_mb"]) * 100),
            }
        
        return {
            "status": "not_started",
            "filename": model["filename"],
            "total_mb": model["size_mb"],
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}