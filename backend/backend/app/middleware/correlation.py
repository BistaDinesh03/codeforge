"""
Correlation ID middleware.
Adds a unique X-Request-ID to every request for log tracing.
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Adds X-Request-ID header to requests and responses.
    Uses existing header if provided, otherwise generates new UUID.
    """

    async def dispatch(self, request: Request, call_next):
        # Use existing request ID or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers so client can trace
        response.headers["X-Request-ID"] = request_id

        return response