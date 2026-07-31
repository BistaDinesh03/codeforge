"""
CodeForge Server - Main entry point.
Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.project import router as project_router
from app.api.chat import router as chat_router
from app.services.discovery import get_discovery_service

setup_logging()
logger = get_logger(__name__)

logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

app = FastAPI(
    title=settings.APP_NAME,
    description="Private AI coding server. Runs on any computer, connects to VS Code.",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(health_router)
app.include_router(models_router)
app.include_router(project_router)
app.include_router(chat_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "diagnostics": "/health/diagnostics",
            "version": "/version",
            "models": "/models",
            "project": "/project",
            "chat": "/chat",
        },
    }


@app.on_event("startup")
async def startup():
    discovery = get_discovery_service()
    discovery.start()
    logger.info(f"Server started on {settings.HOST}:{settings.PORT}")


@app.on_event("shutdown")
async def shutdown():
    discovery = get_discovery_service()
    discovery.stop()
    logger.info("Server shutting down")