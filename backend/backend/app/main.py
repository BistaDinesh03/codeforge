"""
Main FastAPI application for CodeForge backend.
Production-ready with logging, diagnostics, and configuration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.diagnostics import router as diagnostics_router
from app.middleware.auth import ApiKeyMiddleware

setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI coding server running on Android via Termux",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(ApiKeyMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(diagnostics_router, tags=["diagnostics"])


class ChatRequest(BaseModel):
    """Chat request with input validation."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_REQUEST_SIZE,
        description="The user's message (1-100000 characters)"
    )


class ChatResponse(BaseModel):
    """Chat response."""
    response: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: str | None = None


@app.get(
    "/",
    responses={
        200: {"description": "Server information"},
    }
)
async def root():
    """Root endpoint returning server metadata."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        200: {"description": "Successful chat response"},
        400: {"description": "Empty message", "model": ErrorResponse},
        401: {"description": "Invalid or missing API key", "model": ErrorResponse},
        422: {"description": "Validation error - message too long or missing", "model": ErrorResponse},
    },
)
async def chat(request: ChatRequest):
    """Send a message to the AI and get a response."""
    safe_message = request.message.replace("\n", " ").replace("\r", " ")[:100]
    logger.info(f"Chat request: {safe_message}")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response_text = f"[{settings.ENVIRONMENT}] You said: {request.message}"
    return ChatResponse(response=response_text)


@app.on_event("startup")
async def startup_event():
    auth_status = "enabled" if settings.API_KEY else "disabled"
    logger.info(f"Server started on {settings.HOST}:{settings.PORT}")
    logger.info(f"Authentication: {auth_status}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down")