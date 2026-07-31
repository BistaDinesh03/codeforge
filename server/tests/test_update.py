"""Tests for update endpoints."""


class TestUpdateCheck:
    """Tests for GET /update/check."""

    def test_returns_200(self, client):
        response = client.get("/update/check")
        assert response.status_code == 200

    def test_returns_current_version(self, client):
        response = client.get("/update/check")
        data = response.json()
        assert data["current_version"] == "0.1.0"
        assert "update_available" in data

    def test_returns_latest_version_when_available(self, client):
        response = client.get("/update/check")
        data = response.json()
        # May or may not have update available (depends on GitHub)
        assert "latest_version" in data or data["update_available"] is False


class TestRollback:
    """Tests for POST /update/rollback."""

    def test_returns_500_when_no_backup(self, client):
        response = client.post("/update/rollback")
        assert response.status_code == 500
        assert "No backup found" in response.json()["detail"]


class TestApplyUpdate:
    """Tests for POST /update/apply."""

    def test_returns_400_when_no_update(self, client):
        response = client.post("/update/apply")
        assert response.status_code == 400
        assert "No update available" in response.json()["detail"]