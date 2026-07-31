"""
Model management API endpoints.
List models, load/unload, check status.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.model_manager import ModelManager, ModelStatus
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/models", tags=["models"])


class ModelListItem(BaseModel):
    """A model in the list response."""
    name: str
    size_mb: float
    path: str


class LoadRequest(BaseModel):
    """Request to load a specific model."""
    model_name: str


class ModelStatusResponse(BaseModel):
    """Current model status."""
    status: str
    model: str | None
    load_time_seconds: float | None
    models_available: int


def _get_manager() -> ModelManager:
    return ModelManager()


@router.get("", response_model=list[ModelListItem])
async def list_models():
    """List all available models in the models directory."""
    manager = _get_manager()
    models = manager.list_available_models()
    
    return [
        ModelListItem(name=m.name, size_mb=m.size_mb, path=m.path)
        for m in models
    ]


@router.get("/status", response_model=ModelStatusResponse)
async def model_status():
    """Get current model status (loaded, loading, unloaded, error)."""
    manager = _get_manager()
    return ModelStatusResponse(**manager.get_status_dict())


@router.post("/load", response_model=ModelStatusResponse)
async def load_model(request: LoadRequest):
    """
    Load a specific model by name.
    The model must be in the models directory as {name}.gguf
    """
    manager = _get_manager()
    
    try:
        manager.load_model(request.model_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return ModelStatusResponse(**manager.get_status_dict())


@router.post("/unload", response_model=ModelStatusResponse)
async def unload_model():
    """Unload the current model to free RAM."""
    manager = _get_manager()
    manager.unload_model()
    return ModelStatusResponse(**manager.get_status_dict())


@router.post("/auto-load", response_model=ModelStatusResponse)
async def auto_load_model():
    """Auto-detect and load the best model for this hardware."""
    manager = _get_manager()
    model_name = manager.auto_detect_model()
    
    if not model_name:
        raise HTTPException(
            status_code=404,
            detail="No models found. Download a GGUF model to the models directory."
        )
    
    try:
        manager.load_model(model_name)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return ModelStatusResponse(**manager.get_status_dict())