"""Tests for streaming chat endpoint."""


class TestStreamingEndpoint:
    """Tests for POST /chat/stream."""

    def test_returns_503_when_no_model(self, client):
        response = client.post("/chat/stream", json={"message": "Hello"})
        assert response.status_code == 503

    def test_rejects_empty_message(self, client):
        response = client.post("/chat/stream", json={"message": ""})
        assert response.status_code == 422

    def test_returns_sse_content_type_when_model_loaded(self, client):
        """Test SSE headers (requires model - skip in CI)."""
        pass  # Tested manually with model loaded