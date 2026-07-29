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

# Setup logging first
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
logger.info(f"Environment: {settings.ENVIRONMENT}")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI coding server running on Android via Termux",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Auth middleware (only active when API_KEY is set)
app.add_middleware(ApiKeyMiddleware)

# CORS middleware with environment-aware settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Include routers
app.include_router(diagnostics_router, tags=["diagnostics"])


class ChatRequest(BaseModel):
    """Chat request with input validation."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_REQUEST_SIZE,
        description="The user's message"
    )


class ChatResponse(BaseModel):
    """Chat response."""
    response: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with validated input and sanitized logging."""
    safe_message = request.message.replace("\n", " ").replace("\r", " ")[:100]
    logger.info(f"Chat request: {safe_message}")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response_text = f"[{settings.ENVIRONMENT}] You said: {request.message}"
    logger.debug(f"Response generated: {len(response_text)} chars")
    return ChatResponse(response=response_text)


@app.on_event("startup")
async def startup_event():
    auth_status = "enabled" if settings.API_KEY else "disabled"
    logger.info(f"Server started on {settings.HOST}:{settings.PORT}")
    logger.info(f"Authentication: {auth_status}")
    logger.info(f"API docs: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down")