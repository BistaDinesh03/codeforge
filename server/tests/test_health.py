"""
Tests for health check and diagnostics endpoints.
"""


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_returns_healthy_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_includes_version(self, client):
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_includes_uptime(self, client):
        response = client.get("/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestDiagnosticsEndpoint:
    """Tests for GET /health/diagnostics."""

    def test_returns_200(self, client):
        response = client.get("/health/diagnostics")
        assert response.status_code == 200

    def test_includes_disk_info(self, client):
        response = client.get("/health/diagnostics")
        data = response.json()
        assert "disk" in data
        assert "free_gb" in data["disk"]
        assert "total_gb" in data["disk"]

    def test_includes_system_info(self, client):
        response = client.get("/health/diagnostics")
        data = response.json()
        assert "system" in data
        assert "python" in data["system"]

    def test_includes_models_count(self, client):
        response = client.get("/health/diagnostics")
        data = response.json()
        assert "models_available" in data
        assert isinstance(data["models_available"], int)


class TestVersionEndpoint:
    """Tests for GET /version."""

    def test_returns_200(self, client):
        response = client.get("/version")
        assert response.status_code == 200

    def test_includes_version(self, client):
        response = client.get("/version")
        data = response.json()
        assert data["version"] == "0.1.0"

    def test_includes_min_extension_version(self, client):
        response = client.get("/version")
        data = response.json()
        assert "min_extension_version" in data


class TestRootEndpoint:
    """Tests for GET /."""

    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_shows_running_status(self, client):
        response = client.get("/")
        data = response.json()
        assert data["status"] == "running"


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_returns_proper_error(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_invalid_method_returns_405(self, client):
        response = client.put("/health")
        assert response.status_code == 405