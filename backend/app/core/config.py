"""
Application configuration.
Reads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path


class Settings:
    """Central configuration for CodeForge backend."""

    # Application
    APP_NAME: str = "CodeForge Backend"
    APP_VERSION: str = "0.0.1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Model settings
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "codellama-7b")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # Security (future use)
    API_KEY: str | None = os.getenv("API_KEY", None)

    class Config:
        """Pydantic config."""
        case_sensitive = True


# Create a global settings instance
settings = Settings()