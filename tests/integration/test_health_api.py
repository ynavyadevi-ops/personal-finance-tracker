"""Integration tests for the Health Check API."""

from fastapi.testclient import TestClient


def test_root_health_check(client: TestClient) -> None:
    """Verify root /health endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data

    # Verify no sensitive credentials or connection strings are leaked
    response_text = response.text.lower()
    assert "secret" not in response_text
    assert "password" not in response_text
    assert "sqlite" not in response_text
    assert "postgres" not in response_text


def test_api_v1_health_check(client: TestClient) -> None:
    """Verify /api/v1/health endpoint behaves identically."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "healthy"
