"""Tests for health and root endpoints."""

class TestHealthEndpoint:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_returns_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

class TestRootEndpoint:
    def test_returns_200(self, client):
        assert client.get("/").status_code == 200

    def test_shows_name(self, client):
        data = client.get("/").json()
        assert data["name"] == "CodeTalk"

class TestErrorHandling:
    def test_404(self, client):
        assert client.get("/nonexistent").status_code == 404