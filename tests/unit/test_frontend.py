"""Unit tests for Streamlit ApiClient and frontend helper components."""

from src.frontend.api_client import ApiClient


def test_api_client_initialization() -> None:
    """Verify ApiClient constructs endpoints properly."""
    client = ApiClient(base_url="http://127.0.0.1:8000/api/v1")
    assert client.base_url == "http://127.0.0.1:8000/api/v1"
    assert client.root_url == "http://127.0.0.1:8000"


def test_api_client_handles_unreachable_server() -> None:
    """Verify ApiClient returns clean error tuples on connection failure."""
    # Point to a dead/unbound port
    client = ApiClient(base_url="http://127.0.0.1:54321/api/v1", timeout=0.5)
    is_healthy, data = client.check_health()
    assert is_healthy is False
    assert "Cannot connect" in data.get("message", "")

    ok, accounts = client.list_accounts()
    assert ok is False
    assert accounts == []
