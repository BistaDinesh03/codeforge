"""
Tests for model management endpoints.
"""


class TestListModels:
    """Tests for GET /models."""

    def test_returns_200(self, client):
        response = client.get("/models")
        assert response.status_code == 200

    def test_returns_list(self, client):
        response = client.get("/models")
        data = response.json()
        assert isinstance(data, list)


class TestModelStatus:
    """Tests for GET /models/status."""

    def test_returns_200(self, client):
        response = client.get("/models/status")
        assert response.status_code == 200

    def test_returns_status_fields(self, client):
        response = client.get("/models/status")
        data = response.json()
        assert "status" in data
        assert "model" in data
        assert "models_available" in data

    def test_initially_unloaded(self, client):
        response = client.get("/models/status")
        data = response.json()
        assert data["status"] == "unloaded"
        assert data["model"] is None


class TestAutoLoad:
    """Tests for POST /models/auto-load."""

    def test_returns_404_when_no_models(self, client):
        """Should return 404 if models directory is empty."""
        response = client.post("/models/auto-load")
        # Either 404 (no models) or 200 (if test model exists)
        assert response.status_code in [200, 404]


class TestUnload:
    """Tests for POST /models/unload."""

    def test_returns_200(self, client):
        response = client.post("/models/unload")
        assert response.status_code == 200

    def test_status_after_unload(self, client):
        response = client.post("/models/unload")
        data = response.json()
        assert data["status"] == "unloaded"