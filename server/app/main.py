"""
CodeForge Server - Main entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.project import router as project_router
from app.api.chat import router as chat_router
from app.api.completion import router as completion_router
from app.api.update import router as update_router
from app.api.download import router as download_router
from app.services.discovery import get_discovery_service
from app.services.updater import check_for_updates

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

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
app.include_router(completion_router)
app.include_router(update_router)
app.include_router(download_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Return dashboard HTML for browsers, JSON for API clients."""
    accept = request.headers.get("accept", "")
    
    if "text/html" in accept:
        dashboard_path = Path(__file__).parent / "templates" / "dashboard.html"
        if dashboard_path.exists():
            return HTMLResponse(dashboard_path.read_text())
    
    # JSON fallback
    return JSONResponse({
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    })


@app.on_event("startup")
async def startup():
    get_discovery_service().start()
    try:
        update = check_for_updates()
        if update:
            logger.info(f"Update available: {update.version}")
    except Exception:
        pass
    logger.info(f"Server started on {settings.HOST}:{settings.PORT}")


@app.on_event("shutdown")
async def shutdown():
    get_discovery_service().stop()
    logger.info("Server shutting down")