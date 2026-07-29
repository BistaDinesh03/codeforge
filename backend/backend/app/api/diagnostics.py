"""
Diagnostics and health check endpoints.
Provides detailed system information for debugging.
"""

import os
import time
import shutil
import platform
import subprocess
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

START_TIME = time.time()
LAST_REQUEST_TIME: float | None = None


class ComponentStatus(BaseModel):
    """Status of a single system component."""
    name: str
    status: str
    details: str


class DiagnosticsResponse(BaseModel):
    """Complete system diagnostics."""
    status: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str
    system: dict
    services: list[ComponentStatus]
    checks: list[ComponentStatus]


def _check_disk_space(path: Path, min_free_gb: float = 1.0) -> ComponentStatus:
    """Check available disk space."""
    try:
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)

        if free_gb < min_free_gb:
            return ComponentStatus(
                name="disk_space",
                status="degraded",
                details=f"Low disk space: {free_gb:.1f}GB free of {total_gb:.1f}GB"
            )
        return ComponentStatus(
            name="disk_space",
            status="healthy",
            details=f"{free_gb:.1f}GB free of {total_gb:.1f}GB"
        )
    except Exception as e:
        return ComponentStatus(
            name="disk_space",
            status="unhealthy",
            details=f"Failed to check disk: {str(e)}"
        )


def _check_model() -> ComponentStatus:
    """Check if the AI model file exists."""
    model_path = settings.MODEL_PATH or (settings.MODELS_DIR / settings.DEFAULT_MODEL)

    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 ** 2)
        return ComponentStatus(
            name="model",
            status="healthy",
            details=f"Model found: {model_path.name} ({size_mb:.0f}MB)"
        )
    return ComponentStatus(
        name="model",
        status="degraded",
        details=f"Model not found at {model_path}. AI features unavailable."
    )


def _check_memory() -> ComponentStatus:
    """Check available system memory."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        free_gb = mem.available / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)

        if free_gb < 0.5:
            return ComponentStatus(
                name="memory",
                status="degraded",
                details=f"Low memory: {free_gb:.1f}GB free of {total_gb:.1f}GB"
            )
        return ComponentStatus(
            name="memory",
            status="healthy",
            details=f"{free_gb:.1f}GB free of {total_gb:.1f}GB"
        )
    except ImportError:
        return ComponentStatus(
            name="memory",
            status="healthy",
            details="psutil not installed, memory check skipped"
        )


def _check_llama() -> ComponentStatus:
    """Check if llama.cpp is available."""
    try:
        from llama_cpp import Llama
        return ComponentStatus(
            name="llama_cpp",
            status="healthy",
            details="llama-cpp-python is installed and importable"
        )
    except ImportError:
        return ComponentStatus(
            name="llama_cpp",
            status="degraded",
            details="llama-cpp-python not installed. AI features unavailable."
        )
    except Exception as e:
        return ComponentStatus(
            name="llama_cpp",
            status="unhealthy",
            details=f"llama.cpp error: {str(e)}"
        )


def _check_adb() -> ComponentStatus:
    """Check if ADB port forwarding is active."""
    try:
        result = subprocess.run(
            ["adb", "forward", "--list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout.strip()
        
        if "tcp:8000" in output:
            return ComponentStatus(
                name="adb_forwarding",
                status="healthy",
                details=f"Port forwarding active: {output}"
            )
        return ComponentStatus(
            name="adb_forwarding",
            status="degraded",
            details="No port forwarding found. Run 'codeforge connect' on your computer."
        )
    except FileNotFoundError:
        return ComponentStatus(
            name="adb_forwarding",
            status="degraded",
            details="ADB not found on this device (expected on phone)"
        )
    except subprocess.TimeoutExpired:
        return ComponentStatus(
            name="adb_forwarding",
            status="degraded",
            details="ADB check timed out"
        )
    except Exception as e:
        return ComponentStatus(
            name="adb_forwarding",
            status="degraded",
            details=f"ADB check unavailable: {str(e)}"
        )


def _check_connectivity() -> ComponentStatus:
    """Check when the last client request was received."""
    global LAST_REQUEST_TIME
    
    if LAST_REQUEST_TIME is None:
        return ComponentStatus(
            name="client_activity",
            status="degraded",
            details="No client requests received yet. Connect from VS Code."
        )
    
    seconds_ago = time.time() - LAST_REQUEST_TIME
    if seconds_ago < 60:
        return ComponentStatus(
            name="client_activity",
            status="healthy",
            details=f"Last request {seconds_ago:.0f} seconds ago"
        )
    return ComponentStatus(
        name="client_activity",
        status="degraded",
        details=f"Last request {seconds_ago:.0f} seconds ago (may be disconnected)"
    )


@router.get("/health", response_model=DiagnosticsResponse)
async def health_diagnostics():
    """Full system health check with component status."""
    uptime = time.time() - START_TIME
    checks: list[ComponentStatus] = []

    checks.append(_check_disk_space(settings.BASE_DIR))
    checks.append(_check_model())
    checks.append(_check_memory())
    checks.append(_check_llama())
    checks.append(_check_adb())
    checks.append(_check_connectivity())

    statuses = [c.status for c in checks]
    if "unhealthy" in statuses:
        overall = "unhealthy"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return DiagnosticsResponse(
        status=overall,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(uptime, 1),
        timestamp=datetime.now(timezone.utc).isoformat(),
        system={
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        },
        services=[
            ComponentStatus(
                name="fastapi",
                status="healthy",
                details=f"Uptime: {timedelta(seconds=int(uptime))}"
            )
        ],
        checks=checks,
    )


@router.get("/health/simple")
async def health_simple():
    """Simple health check (for load balancers / monitoring)."""
    global LAST_REQUEST_TIME
    LAST_REQUEST_TIME = time.time()
    return {"status": "ok"}


@router.get("/health/config")
async def health_config():
    """Show current configuration (safe version, no secrets)."""
    return settings.model_dump_safe()