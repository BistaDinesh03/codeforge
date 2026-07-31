"""
Central configuration for CodeForge server.
Reads from environment variables, .env file, and defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration for CodeForge server."""

    # ── Application ──
    APP_NAME: str = "CodeForge Server"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False

    # ── Server ──
    HOST: str = "0.0.0.0"  # Accept connections from any device on network
    PORT: int = 8000
    WORKERS: int = 1  # Single worker for model inference (CPU-bound)

    # ── Paths ──
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # ── Model defaults ──
    DEFAULT_MODEL: str = ""  # Auto-detect if empty
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    CONTEXT_LENGTH: int = 4096

    # ── Logging ──
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR

    # ── Security ──
    API_KEY: str = ""  # Empty = no authentication required
    ALLOWED_ORIGINS: list[str] = ["*"]

    # ── Performance ──
    REQUEST_TIMEOUT: int = 120  # Seconds before request times out
    MAX_REQUEST_SIZE: int = 100_000  # Max chat message size in characters

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def model_dump_safe(self) -> dict:
        """Return settings as dict, hiding API key if set."""
        data = self.model_dump()
        if data.get("API_KEY"):
            data["API_KEY"] = "***"
        return data


# Create global settings instance
settings = Settings()

# Ensure directories exist
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)