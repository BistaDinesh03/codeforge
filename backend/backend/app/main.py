"""
Main FastAPI application for CodeForge backend.
Production-ready with logging, diagnostics, and configuration.
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import Settings, settings
from app.core.logging_config import setup_logging, get_logger
from app.api.diagnostics import router as diagnostics_router
from app.middleware.auth import ApiKeyMiddleware
from app.middleware.correlation import CorrelationMiddleware
from app.dependencies import get_settings

setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI coding server running on Android via Termux",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Middleware
app.add_middleware(CorrelationMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
)

app.include_router(diagnostics_router, tags=["diagnostics"])


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=settings.MAX_REQUEST_SIZE,
        description="The user's message (1-100000 characters)"
    )


class ChatResponse(BaseModel):
    response: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


@app.get("/", responses={200: {"description": "Server information"}})
async def root(settings_dep: Settings = Depends(get_settings)):
    return {
        "name": settings_dep.APP_NAME,
        "version": settings_dep.APP_VERSION,
        "environment": settings_dep.ENVIRONMENT,
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
        422: {"description": "Validation error", "model": ErrorResponse},
    },
)
async def chat(
    request: ChatRequest,
    raw_request: Request,
    settings_dep: Settings = Depends(get_settings),
):
    req_id = get_request_id(raw_request)
    safe_message = request.message.replace("\n", " ").replace("\r", " ")[:100]
    logger.info(f"[{req_id}] Chat request: {safe_message}")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response_text = f"[{settings_dep.ENVIRONMENT}] You said: {request.message}"
    return ChatResponse(response=response_text)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Server started on {settings.HOST}:{settings.PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down")