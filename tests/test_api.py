from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestBlogAPI:
    """API endpoint tests."""

    def test_missing_topic_returns_422(self):
        from app import app
        client = TestClient(app)
        response = client.post("/blogs", json={"language": "hindi"})
        assert response.status_code == 422

    def test_empty_topic_returns_400(self):
        from app import app
        client = TestClient(app)
        response = client.post("/blogs", json={"topic": "  "})
        assert response.status_code == 400

    def test_invalid_json_returns_422(self):
        from app import app
        client = TestClient(app)
        response = client.post("/blogs", content="not json",
                               headers={"Content-Type": "application/json"})
        assert response.status_code == 422