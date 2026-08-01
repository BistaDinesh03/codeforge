"""CodeTalk Server - Main entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.health import router as health_router
from app.api.workspace import router as workspace_router
from app.api.insights import router as insights_router

setup_logging()
logger = get_logger(__name__)
app = FastAPI(title="CodeTalk", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["GET","POST"], allow_headers=["Content-Type"])
app.include_router(health_router)
app.include_router(workspace_router)
app.include_router(insights_router)

@app.exception_handler(Exception)
async def handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}")
    return JSONResponse(status_code=500, content={"detail":"Internal error"})

@app.get("/")
async def root():
    return {"name":"CodeTalk","version":"1.0.0","status":"running"}

@app.on_event("startup")
async def startup():
    logger.info("CodeTalk server started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("CodeTalk server shutting down")