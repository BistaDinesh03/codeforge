"""
Central configuration for CodeTalk server.
Reads from environment variables, .env file, and defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration for CodeTalk server."""

    APP_NAME: str = "CodeTalk"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MODELS_DIR: Path = BASE_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"

    LOG_LEVEL: str = "INFO"
    API_KEY: str = ""
    ALLOWED_ORIGINS: list[str] = ["*"]

    REQUEST_TIMEOUT: int = 120
    MAX_REQUEST_SIZE: int = 100_000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def model_dump_safe(self) -> dict:
        data = self.model_dump()
        if data.get("API_KEY"):
            data["API_KEY"] = "***"
        return data


settings = Settings()
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)