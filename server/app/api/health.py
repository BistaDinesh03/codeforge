"""
Health check, diagnostics, and version endpoints.
No authentication required.
"""

import time
import platform
import shutil
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])

SERVER_START_TIME = time.time()


class HealthResponse(BaseModel):
    """Simple health check response."""
    status: str
    version: str
    uptime_seconds: float


class DiagnosticsResponse(BaseModel):
    """Detailed system diagnostics."""
    status: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str
    system: dict
    disk: dict
    models_available: int


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Quick health check. Returns 200 if server is running."""
    response = HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        uptime_seconds=round(time.time() - SERVER_START_TIME, 1),
    )
    return JSONResponse(
        content=response.model_dump(),
        headers={"Cache-Control": "no-cache"}
    )


@router.get("/health/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics():
    """Full system diagnostics."""
    disk_usage = shutil.disk_usage(settings.BASE_DIR)
    disk_info = {
        "total_gb": round(disk_usage.total / (1024**3), 1),
        "free_gb": round(disk_usage.free / (1024**3), 1),
        "used_percent": round((disk_usage.used / disk_usage.total) * 100, 1),
    }

    model_files = list(settings.MODELS_DIR.glob("*.gguf"))
    models_available = len(model_files)

    if disk_info["free_gb"] < 1.0:
        overall = "degraded"
    elif models_available == 0:
        overall = "degraded"
    else:
        overall = "healthy"

    return DiagnosticsResponse(
        status=overall,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(time.time() - SERVER_START_TIME, 1),
        timestamp=datetime.now(timezone.utc).isoformat(),
        system={
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": platform.processor() or "unknown",
        },
        disk=disk_info,
        models_available=models_available,
    )


@router.get("/version")
async def version():
    """Return server version for compatibility check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "min_extension_version": "0.1.0",
    }