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
        response = client.get("/health/simple")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_full_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_config_endpoint(self):
        response = client.get("/health/config")
        assert response.status_code == 200
        data = response.json()
        assert data["APP_NAME"] == "CodeForge Backend"


class TestChatEndpoint:
    """Tests for the chat endpoint."""

    def test_chat_with_message(self):
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    def test_chat_empty_message(self):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_very_long_message(self):
        long_message = "x" * 200000
        response = client.post("/chat", json={"message": long_message})
        assert response.status_code == 422


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_info(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "CodeForge Backend"