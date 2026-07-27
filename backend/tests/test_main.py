"""
Tests for the main FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_simple_health(self):
        """Simple health check should return ok."""
        response = client.get("/health/simple")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_full_health(self):
        """Full health check should return diagnostics."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "checks" in data
        assert len(data["checks"]) > 0

    def test_config_endpoint(self):
        """Config endpoint should return safe settings."""
        response = client.get("/health/config")
        assert response.status_code == 200
        data = response.json()
        assert data["APP_NAME"] == "CodeForge Backend"


class TestChatEndpoint:
    """Tests for the chat endpoint."""

    def test_chat_with_message(self):
        """Chat should respond to valid messages."""
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0

    def test_chat_empty_message(self):
        """Chat should reject empty messages."""
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_chat_whitespace_message(self):
        """Chat should reject whitespace-only messages."""
        response = client.post("/chat", json={"message": "   "})
        assert response.status_code == 400


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_info(self):
        """Root should return basic app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CodeForge Backend"
        assert "version" in data
        assert "environment" in data