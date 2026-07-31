"""Tests for code completion endpoint."""


class TestCompletionEndpoint:
    """Tests for POST /complete."""

    def test_returns_503_when_no_model(self, client):
        response = client.post("/complete", json={
            "prefix": "def hello():",
            "language": "python"
        })
        assert response.status_code == 503
        assert "No AI model loaded" in response.json()["detail"]

    def test_rejects_empty_prefix(self, client):
        response = client.post("/complete", json={
            "prefix": "",
            "language": "python"
        })
        assert response.status_code == 422

    def test_accepts_valid_request(self, client):
        """Valid request should return 503 (no model) not 422."""
        response = client.post("/complete", json={
            "prefix": "def fibonacci(n):\n    ",
            "suffix": "",
            "language": "python",
            "max_tokens": 32
        })
        assert response.status_code == 503  # No model loaded, but request is valid

    def test_rejects_missing_fields(self, client):
        response = client.post("/complete", json={})
        assert response.status_code == 422