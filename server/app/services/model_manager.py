"""
Model Manager - handles loading, unloading, and switching AI models.
Singleton pattern ensures only one model is loaded at a time.
"""

import time
import threading
from pathlib import Path
from typing import Optional
from llama_cpp import Llama

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ModelStatus:
    """Tracks the current state of model loading."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class ModelInfo:
    """Information about an available model file."""
    
    def __init__(self, path: Path):
        self.name = path.stem
        self.path = str(path)
        self.size_mb = round(path.stat().st_size / (1024 * 1024), 1)


class ModelManager:
    """
    Singleton manager for AI models.
    Only one model can be loaded at a time to conserve RAM.
    """
    
    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._model: Optional[Llama] = None
        self._status: str = ModelStatus.UNLOADED
        self._current_model_name: str = ""
        self._load_time: float = 0.0
        self._initialized = True
        
        logger.info("ModelManager initialized")
    
    @property
    def status(self) -> str:
        return self._status
    
    @property
    def current_model(self) -> Optional[Llama]:
        return self._model
    
    @property
    def current_model_name(self) -> str:
        return self._current_model_name
    
    @property
    def load_time(self) -> float:
        return self._load_time
    
    def list_available_models(self) -> list[ModelInfo]:
        """List all GGUF models in the models directory."""
        models = []
        if settings.MODELS_DIR.exists():
            for file in settings.MODELS_DIR.glob("*.gguf"):
                models.append(ModelInfo(file))
        return sorted(models, key=lambda m: m.name)
    
    def auto_detect_model(self) -> Optional[str]:
        """Find the best model for this hardware."""
        models = self.list_available_models()
        if not models:
            return None
        
        # Prefer smaller models for low-RAM systems
        # Sort by size, pick smallest that's still a coder model
        coder_models = [m for m in models if "coder" in m.name.lower()]
        if coder_models:
            return coder_models[0].name
        
        # Fall back to any model
        return models[0].name
    
    def load_model(self, model_name: str) -> Llama:
        """
        Load a model by name (without .gguf extension).
        
        Args:
            model_name: Name of the model file without extension.
            
        Returns:
            Loaded Llama model instance.
            
        Raises:
            FileNotFoundError: If model file doesn't exist.
            RuntimeError: If model fails to load.
        """
        if self._status == ModelStatus.LOADING:
            raise RuntimeError("Model is already loading")
        
        # Unload current model if any
        if self._model is not None:
            self.unload_model()
        
        model_path = settings.MODELS_DIR / f"{model_name}.gguf"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        logger.info(f"Loading model: {model_name}")
        self._status = ModelStatus.LOADING
        start = time.time()
        
        try:
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=settings.CONTEXT_LENGTH,
                n_threads=4,
                verbose=False,
            )
            self._load_time = time.time() - start
            self._status = ModelStatus.LOADED
            self._current_model_name = model_name
            
            logger.info(
                f"Model loaded in {self._load_time:.1f}s "
                f"(context: {settings.CONTEXT_LENGTH} tokens)"
            )
            return self._model
            
        except Exception as e:
            self._status = ModelStatus.ERROR
            self._model = None
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to load model '{model_name}': {e}")
    
    def unload_model(self) -> None:
        """Unload the current model to free RAM."""
        if self._model is not None:
            name = self._current_model_name
            self._model = None
            self._current_model_name = ""
            self._status = ModelStatus.UNLOADED
            self._load_time = 0.0
            logger.info(f"Model unloaded: {name}")
    
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._status == ModelStatus.LOADED and self._model is not None
    
    def get_status_dict(self) -> dict:
        """Return current status as a dictionary."""
        return {
            "status": self._status,
            "model": self._current_model_name or None,
            "load_time_seconds": round(self._load_time, 1) if self._load_time else None,
            "models_available": len(self.list_available_models()),
        }