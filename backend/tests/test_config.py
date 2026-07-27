"""
Tests for configuration module.
"""

from app.core.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_values(self):
        """Settings should have sensible defaults."""
        settings = Settings()
        assert settings.APP_NAME == "CodeForge Backend"
        assert settings.PORT == 8000
        assert settings.ENVIRONMENT == "development"

    def test_safe_dump_hides_secrets(self):
        """Safe dump should redact API keys."""
        settings = Settings(API_KEY="secret123")
        data = settings.model_dump_safe()
        assert data["API_KEY"] == "***REDACTED***"

    def test_environment_default(self):
        """Default environment should be development."""
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False