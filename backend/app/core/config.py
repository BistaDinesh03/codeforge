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

    # ── CORS ──
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    ALLOW_CREDENTIALS: bool = False

    # ── Security ──
    API_KEY: str | None = None
    MAX_REQUEST_SIZE: int = 100000
    RATE_LIMIT_REQUESTS: int = 30
    RATE_LIMIT_WINDOW: int = 60

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
        if "API_KEY" in data and data["API_KEY"]:
            data["API_KEY"] = "***REDACTED***"
        return data

    @property
    def cors_origins(self) -> list[str]:
        """Get appropriate CORS origins for current environment."""
        if self.ENVIRONMENT == "development":
            return ["*"]
        return self.ALLOWED_ORIGINS

    @property
    def cors_credentials(self) -> bool:
        """Credentials only with explicit origins, never with wildcard."""
        if self.ENVIRONMENT == "development":
            return False
        return self.ALLOW_CREDENTIALS


# Global settings instance
settings = Settings()

# Create required directories
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)