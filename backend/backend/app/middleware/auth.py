"""
Authentication middleware for CodeForge backend.
Enforces API key authentication when configured.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = ["/health", "/health/simple", "/", "/docs", "/openapi.json"]


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces API key authentication.
    Only active when API_KEY is configured in settings.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip authentication if no API key configured
        if not settings.API_KEY:
            return await call_next(request)

        # Skip authentication for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Check API key header
        provided_key = request.headers.get("X-API-Key")
        if not provided_key:
            logger.warning(f"Missing API key for {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="API key required. Set X-API-Key header.",
            )

        if provided_key != settings.API_KEY:
            logger.warning(f"Invalid API key for {request.url.path}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key.",
            )

        return await call_next(request)