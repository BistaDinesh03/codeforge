"""
Model download API - smart recommendations, progress tracking, resume support.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio

from app.services.model_downloader import (
    MODELS, recommend_model, detect_ram_gb,
    download_model, get_download_status, verify_checksum, get_download_path,
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/download", tags=["download"])


class RecommendResponse(BaseModel):
    """Model recommendation based on system RAM."""
    ram_gb: int
    recommended_model: str
    model_name: str
    size_mb: int
    description: str


class DownloadStatus(BaseModel):
    """Current download status."""
    status: str
    filename: str | None = None
    downloaded_mb: int | None = None
    total_mb: int | None = None
    percent: float | None = None
    error: str | None = None


@router.get("/recommend", response_model=RecommendResponse)
async def recommend():
    """Recommend the best model for this system."""
    ram = detect_ram_gb()
    model = recommend_model(ram)
    
    # Find the model key
    model_key = None
    for key, info in MODELS.items():
        if info["filename"] == model["filename"]:
            model_key = key
            break
    
    return RecommendResponse(
        ram_gb=ram,
        recommended_model=model_key or "unknown",
        model_name=model["name"],
        size_mb=model["size_mb"],
        description=model["description"],
    )


@router.get("/status/{model_key}", response_model=DownloadStatus)
async def status(model_key: str):
    """Get download status for a model."""
    if model_key not in MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_key}")
    
    return DownloadStatus(**get_download_status(model_key))


@router.post("/start/{model_key}")
async def start_download(model_key: str):
    """Start downloading a model. Returns immediately, download runs in background."""
    if model_key not in MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_key}")
    
    status = get_download_status(model_key)
    if status["status"] == "complete":
        return {"status": "already_downloaded", "message": "Model already installed"}
    
    # Start download in background thread
    import threading
    
    def download_task():
        try:
            download_model(model_key)
            logger.info(f"Model download complete: {model_key}")
        except Exception as e:
            logger.error(f"Model download failed: {e}")
    
    thread = threading.Thread(target=download_task, daemon=True)
    thread.start()
    
    return {"status": "downloading", "message": "Download started"}


@router.get("/progress/{model_key}")
async def download_progress(model_key: str):
    """Stream download progress as SSE."""
    if model_key not in MODELS:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_key}")
    
    async def generate():
        while True:
            status = get_download_status(model_key)
            yield f"data: {json.dumps(status)}\n\n"
            
            if status["status"] in ("complete", "error"):
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )