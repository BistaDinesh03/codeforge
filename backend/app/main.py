"""
Main FastAPI application for CodeForge backend.
Production-ready with logging, diagnostics, and configuration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.diagnostics import router as diagnostics_router

# Setup logging first
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Debug mode: {settings.DEBUG}")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI coding server running on Android via Termux",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diagnostics_router, tags=["diagnostics"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
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
    """Chat endpoint."""
    logger.info(f"Chat request: {request.message[:50]}...")

    if not request.message.strip():
        logger.warning("Empty message received")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Placeholder - will be replaced with real AI
    response_text = f"[{settings.ENVIRONMENT}] You said: {request.message}"

    logger.debug(f"Chat response: {response_text[:50]}...")
    return ChatResponse(response=response_text)


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Server started successfully")
    logger.info(f"API docs available at /docs")
    logger.info(f"Health check at /health")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down")