"""
Dependency injection for CodeForge backend.
Provides reusable dependencies via FastAPI's Depends().
"""

from app.core.config import Settings, settings


async def get_settings() -> Settings:
    """
    Returns application settings.
    Can be overridden in tests by dependency override.
    """
    return settings