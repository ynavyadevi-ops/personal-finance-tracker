"""Centralized API client for Streamlit frontend to communicate with FastAPI backend."""

from typing import Any

import httpx

from src.core.config import settings
from src.core.logging import logger


class ApiClient:
    """HTTP client wrapper communicating with FastAPI backend endpoints."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self.base_url = (base_url or settings.API_BASE_URL).rstrip("/")
        # Root backend URL for /health
        self.root_url = self.base_url.replace(settings.API_V1_PREFIX, "")
        self.timeout = timeout

    def _get_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout)

    def check_health(self) -> tuple[bool, dict[str, Any]]:
        """Probe backend health endpoint. Returns (is_healthy, payload_or_error)."""
        url = f"{self.root_url}/health"
        try:
            with self._get_client() as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    return True, data
                return False, {"message": f"Backend returned status {response.status_code}"}
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Health check connection error: {e}")
            return False, {"message": f"Cannot connect to backend server: {e}"}
        except Exception as e:
            logger.error(f"Health check unexpected exception: {e}")
            return False, {"message": str(e)}

    def list_accounts(self, active_only: bool = True) -> tuple[bool, list[dict[str, Any]]]:
        """Fetch financial accounts from FastAPI backend."""
        url = f"{self.base_url}/accounts?active_only={str(active_only).lower()}"
        try:
            with self._get_client() as client:
                response = client.get(url)
                if response.status_code == 200:
                    items = response.json().get("data", [])
                    return True, items
                return False, []
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            return False, []

    def create_account(self, payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Create a new account via FastAPI backend."""
        url = f"{self.base_url}/accounts"
        try:
            with self._get_client() as client:
                response = client.post(url, json=payload)
                resp_json = response.json()
                if response.status_code == 201 and resp_json.get("success"):
                    return True, resp_json.get("data", {})

                err_msg = resp_json.get("error", {}).get("message", "Failed to create account")
                return False, {"message": err_msg}
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return False, {"message": f"Connection error: {e}"}

    def archive_account(self, account_id: str) -> tuple[bool, dict[str, Any]]:
        """Archive (soft-delete) an account via FastAPI backend."""
        url = f"{self.base_url}/accounts/{account_id}"
        try:
            with self._get_client() as client:
                response = client.delete(url)
                resp_json = response.json()
                if response.status_code == 200 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                err_msg = resp_json.get("error", {}).get("message", "Failed to archive account")
                return False, {"message": err_msg}
        except Exception as e:
            logger.error(f"Error archiving account: {e}")
            return False, {"message": str(e)}


api_client = ApiClient()
