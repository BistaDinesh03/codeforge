"""
Diagnostics and health check endpoints.
Provides detailed system information for debugging.
"""

import os
import time
import shutil
import platform
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Track server start time
START_TIME = time.time()


class ComponentStatus(BaseModel):
    """Status of a single system component."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
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


@router.get("/health", response_model=DiagnosticsResponse)
async def health_diagnostics():
    """Full system health check with component status."""
    uptime = time.time() - START_TIME
    checks: list[ComponentStatus] = []

    # Run all checks
    checks.append(_check_disk_space(settings.BASE_DIR))
    checks.append(_check_model())
    checks.append(_check_memory())
    checks.append(_check_llama())

    # Determine overall status
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
    return {"status": "ok"}


@router.get("/health/config")
async def health_config():
    """Show current configuration (safe version, no secrets)."""
    return settings.model_dump_safe()