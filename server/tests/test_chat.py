"""Tests for chat API endpoints."""


class TestChatEndpoint:
    """Tests for POST /chat."""

    def test_returns_503_when_no_model_loaded(self, client):
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 503
        assert "No AI model loaded" in response.json()["detail"]

    def test_rejects_empty_message(self, client):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_rejects_missing_message(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_accepts_valid_message(self, client):
        response = client.post("/chat", json={
            "message": "Hello",
            "max_tokens": 100,
            "temperature": 0.5
        })
        assert response.status_code == 503  # No model, but valid request


class TestExplainEndpoint:
    """Tests for POST /chat/explain."""

    def test_returns_503_when_no_model(self, client):
        response = client.post("/chat/explain", json={
            "code": "print('hello')",
            "language": "python"
        })
        assert response.status_code == 503

    def test_rejects_empty_code(self, client):
        response = client.post("/chat/explain", json={
            "code": "",
            "language": "python"
        })
        assert response.status_code == 422


class TestGenerateEndpoint:
    """Tests for POST /chat/generate."""

    def test_returns_503_when_no_model(self, client):
        response = client.post("/chat/generate", json={
            "description": "sort a list",
            "language": "python"
        })
        assert response.status_code == 503

    def test_rejects_empty_description(self, client):
        response = client.post("/chat/generate", json={
            "description": "",
            "language": "python"
        })
        assert response.status_code == 422


class TestRewriteEndpoint:
    """Tests for POST /chat/rewrite."""

    def test_returns_503_when_no_model(self, client):
        response = client.post("/chat/rewrite", json={
            "code": "x=1",
            "language": "python"
        })
        assert response.status_code == 503

    def test_rejects_empty_code(self, client):
        response = client.post("/chat/rewrite", json={
            "code": "",
            "language": "python"
        })
        assert response.status_code == 422

    def test_accepts_valid_request(self, client):
        response = client.post("/chat/rewrite", json={
            "code": "def add(a,b): return a+b",
            "language": "python"
        })
        assert response.status_code == 503  # No model, but valid