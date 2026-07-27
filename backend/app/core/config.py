"""
Application configuration using Pydantic Settings.
Reads from environment variables and .env file.
"""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for CodeForge backend."""

    # ── Application ──
    APP_NAME: str = "CodeForge Backend"
    APP_VERSION: str = "0.0.1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # ── Server ──
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1

    # ── Paths ──
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"
    DATA_DIR: Path = BASE_DIR / "data"

    # ── Model Settings ──
    DEFAULT_MODEL: str = "codellama-7b.Q4_K_M.gguf"
    MODEL_PATH: Path | None = None
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.95
    CONTEXT_LENGTH: int = 4096

    # ── Logging ──
    LOG_LEVEL: str = "INFO"

    # ── Security ──
    API_KEY: str | None = None
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Performance ──
    REQUEST_TIMEOUT: int = 60
    MAX_CONCURRENT_REQUESTS: int = 4

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def model_dump_safe(self) -> dict:
        """Return config as dict, hiding sensitive values."""
        data = self.model_dump()
        # Hide sensitive values
        if "API_KEY" in data and data["API_KEY"]:
            data["API_KEY"] = "***REDACTED***"
        return data


# Global settings instance
settings = Settings()

# Create required directories
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)