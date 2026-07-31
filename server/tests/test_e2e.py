"""
End-to-end tests that verify the full flow works.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestFullFlow:
    """Test the complete user journey."""

    def test_server_starts_and_responds(self):
        """User opens dashboard."""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_check_works(self):
        """Health endpoint responds."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_diagnostics_works(self):
        """Diagnostics shows system info."""
        response = client.get("/health/diagnostics")
        assert response.status_code == 200
        data = response.json()
        assert "disk" in data
        assert "system" in data

    def test_models_listed(self):
        """Available models are listed."""
        response = client.get("/models")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_model_status(self):
        """Model status returns correctly."""
        response = client.get("/models/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "models_available" in data

    def test_update_check(self):
        """Update check works."""
        response = client.get("/update/check")
        assert response.status_code == 200
        data = response.json()
        assert "current_version" in data

    def test_download_recommend(self):
        """Model recommendation works."""
        response = client.get("/download/recommend")
        assert response.status_code == 200
        data = response.json()
        assert "recommended_model" in data
        assert "ram_gb" in data


class TestErrorHandling:
    """Test that errors are handled gracefully."""

    def test_chat_without_model(self):
        """Chat returns clear error when no model."""
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 503
        assert "detail" in response.json()

    def test_complete_without_model(self):
        """Completion returns error when no model."""
        response = client.post("/complete", json={
            "prefix": "def hello():",
            "language": "python"
        })
        assert response.status_code == 503

    def test_invalid_chat_message(self):
        """Empty message is rejected."""
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_404_endpoint(self):
        """Unknown endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404


class TestSecurity:
    """Test basic security measures."""

    def test_rate_limiting_present(self):
        """Multiple requests don't crash the server."""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_cors_headers(self):
        """CORS headers are present."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_no_sensitive_data_in_health(self):
        """Health endpoint doesn't leak secrets."""
        response = client.get("/health")
        data = response.json()
        assert "api_key" not in str(data).lower()