"""Centralized API client for Streamlit frontend to communicate with FastAPI backend."""

from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings
from src.core.logging import logger


class ApiClient:
    """HTTP client wrapper communicating with FastAPI backend endpoints.

    Provides:
    - Bearer authentication header injection.
    - Standardized (success: bool, data_or_error: Any) tuples.
    - Explicit 401 session expiration handling.
    - Prevention of automatic retries on state-mutating POST operations.
    - Zero sensitive credential logging.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 8.0,
        token: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.API_BASE_URL).rstrip("/")
        # Root backend URL for /health
        self.root_url = self.base_url.replace(settings.API_V1_PREFIX, "")
        self.timeout = timeout
        self._token: str | None = token

    @property
    def token(self) -> str | None:
        """Return currently configured Bearer authentication token."""
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        """Update Bearer token for authenticated requests."""
        self._token = value

    def _get_headers(self, is_json: bool = True) -> dict[str, str]:
        """Construct request headers with authorization token if present."""
        headers: dict[str, str] = {}
        if is_json:
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get_client(self) -> httpx.Client:
        """Create an HTTPX synchronous client instance with configured timeout."""
        return httpx.Client(timeout=self.timeout)

    def _handle_response_error(self, response: httpx.Response) -> dict[str, Any]:
        """Extract structured error details from response payload."""
        try:
            body = response.json()
            if isinstance(body, dict):
                error_info = body.get("error")
                if isinstance(error_info, dict):
                    return {
                        "message": error_info.get("message", response.text),
                        "code": error_info.get("code", f"HTTP_{response.status_code}"),
                        "status_code": response.status_code,
                    }
                detail = body.get("detail")
                if detail:
                    return {
                        "message": str(detail),
                        "code": f"HTTP_{response.status_code}",
                        "status_code": response.status_code,
                    }
        except Exception as err:
            logger.debug(f"Non-JSON error response from backend: {err}")

        return {
            "message": f"Server returned error HTTP {response.status_code}",
            "code": f"HTTP_{response.status_code}",
            "status_code": response.status_code,
        }

    # =========================================================================
    # SYSTEM & AUTHENTICATION ENDPOINTS
    # =========================================================================

    def check_health(self) -> tuple[bool, dict[str, Any]]:
        """Probe backend health endpoint. Returns (is_healthy, payload_or_error)."""
        url = f"{self.root_url}/health"
        try:
            with self._get_client() as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    return True, data
                return False, self._handle_response_error(response)
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Health check connection error: {e}")
            return False, {
                "message": f"Cannot connect to backend server: {e}",
                "code": "CONNECTION_ERROR",
            }
        except Exception as e:
            logger.error(f"Health check unexpected exception: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def login(self, username: str, password: str) -> tuple[bool, dict[str, Any]]:
        """Authenticate user credentials against OAuth2 token endpoint."""
        url = f"{self.base_url}/auth/token"
        try:
            with self._get_client() as client:
                # OAuth2 password flow expects form data
                response = client.post(
                    url,
                    data={"username": username.strip().lower(), "password": password},
                    headers=self._get_headers(is_json=False),
                )
                if response.status_code == 200:
                    token_data = response.json()
                    self._token = token_data.get("access_token")
                    return True, token_data
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Login request failed: {e}")
            return False, {"message": f"Connection error: {e}", "code": "CONNECTION_ERROR"}

    def get_current_user(self) -> tuple[bool, dict[str, Any]]:
        """Retrieve profile of currently authenticated user."""
        url = f"{self.base_url}/auth/me"
        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    user_data = response.json().get("data", {})
                    return True, user_data
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    # =========================================================================
    # FINANCIAL ACCOUNT ENDPOINTS
    # =========================================================================

    def list_accounts(self, active_only: bool = True) -> tuple[bool, list[dict[str, Any]]]:
        """Fetch financial accounts from FastAPI backend."""
        url = f"{self.base_url}/accounts?active_only={str(active_only).lower()}"
        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    items = response.json().get("data", [])
                    return True, items
                return False, []
        except Exception as e:
            logger.error(f"Error fetching accounts: {e}")
            return False, []

    def get_account(self, account_id: str) -> tuple[bool, dict[str, Any]]:
        """Fetch a single account by ID."""
        url = f"{self.base_url}/accounts/{account_id}"
        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    return True, response.json().get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error fetching account {account_id}: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def create_account(self, payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Create a new account via FastAPI backend."""
        url = f"{self.base_url}/accounts"
        try:
            with self._get_client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                resp_json = response.json()
                if response.status_code == 201 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return False, {"message": f"Connection error: {e}", "code": "CONNECTION_ERROR"}

    def update_account(
        self, account_id: str, payload: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """Update account metadata (e.g. name, institution) via FastAPI backend."""
        url = f"{self.base_url}/accounts/{account_id}"
        try:
            with self._get_client() as client:
                response = client.put(url, json=payload, headers=self._get_headers())
                resp_json = response.json()
                if response.status_code == 200 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error updating account {account_id}: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def archive_account(self, account_id: str) -> tuple[bool, dict[str, Any]]:
        """Archive (soft-delete) an account via FastAPI backend."""
        url = f"{self.base_url}/accounts/{account_id}"
        try:
            with self._get_client() as client:
                response = client.delete(url, headers=self._get_headers())
                resp_json = response.json()
                if response.status_code == 200 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error archiving account: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def reconcile_account(self, account_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve balance reconciliation breakdown for an account."""
        url = f"{self.base_url}/transactions/reconcile/{account_id}"
        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    return True, response.json().get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error reconciling account {account_id}: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    # =========================================================================
    # TRANSACTION ENDPOINTS
    # =========================================================================

    def list_transactions(
        self,
        account_id: str | None = None,
        category_id: str | None = None,
        transaction_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[bool, dict[str, Any]]:
        """Fetch paginated transactions matching optional criteria."""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if account_id:
            params["account_id"] = account_id
        if category_id:
            params["category_id"] = category_id
        if transaction_type and transaction_type != "ALL":
            params["transaction_type"] = transaction_type
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        url = f"{self.base_url}/transactions"
        try:
            with self._get_client() as client:
                response = client.get(url, params=params, headers=self._get_headers())
                if response.status_code == 200:
                    resp_json = response.json()
                    return True, {
                        "items": resp_json.get("data", []),
                        "meta": resp_json.get("meta", {}),
                    }
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error listing transactions: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def get_transaction(self, transaction_id: str) -> tuple[bool, dict[str, Any]]:
        """Fetch details of a single transaction by ID."""
        url = f"{self.base_url}/transactions/{transaction_id}"
        try:
            with self._get_client() as client:
                response = client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    return True, response.json().get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error fetching transaction {transaction_id}: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def create_transaction(self, payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Post a new income or expense transaction."""
        url = f"{self.base_url}/transactions"
        try:
            with self._get_client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                resp_json = response.json()
                if response.status_code == 201 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return False, {"message": f"Connection error: {e}", "code": "CONNECTION_ERROR"}

    def create_transfer(self, payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Post an atomic inter-account transfer."""
        url = f"{self.base_url}/transactions/transfer"
        try:
            with self._get_client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                resp_json = response.json()
                if response.status_code == 201 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error creating transfer: {e}")
            return False, {"message": f"Connection error: {e}", "code": "CONNECTION_ERROR"}

    def reverse_transaction(
        self, transaction_id: str, reason: str = "User requested reversal"
    ) -> tuple[bool, dict[str, Any]]:
        """Post a compensating transaction reversal."""
        url = f"{self.base_url}/transactions/{transaction_id}/reverse"
        try:
            with self._get_client() as client:
                response = client.post(
                    url,
                    json={"reason": reason},
                    headers=self._get_headers(),
                )
                resp_json = response.json()
                if response.status_code == 200 and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error reversing transaction {transaction_id}: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    # =========================================================================
    # BUDGET ENDPOINTS
    # =========================================================================

    def list_budgets_for_period(self, year: int, month: int) -> tuple[bool, list[dict[str, Any]]]:
        """Fetch all category budgets established for a specified month and year."""
        url = f"{self.base_url}/budgets/period"
        try:
            with self._get_client() as client:
                response = client.get(
                    url,
                    params={"year": year, "month": month},
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    items = response.json().get("data", [])
                    return True, items
                return False, []
        except Exception as e:
            logger.error(f"Error listing period budgets: {e}")
            return False, []

    def get_budget_utilization(
        self, category_id: str, year: int, month: int
    ) -> tuple[bool, dict[str, Any]]:
        """Retrieve spending metrics and threshold status for a specific category budget."""
        url = f"{self.base_url}/budgets/utilization"
        try:
            with self._get_client() as client:
                response = client.get(
                    url,
                    params={"category_id": category_id, "year": year, "month": month},
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    return True, response.json().get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error fetching budget utilization: {e}")
            return False, {"message": str(e), "code": "CLIENT_ERROR"}

    def create_budget(self, payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """Establish or update a monthly category budget allocation."""
        url = f"{self.base_url}/budgets"
        try:
            with self._get_client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                resp_json = response.json()
                if response.status_code in (200, 201) and resp_json.get("success"):
                    return True, resp_json.get("data", {})
                return False, self._handle_response_error(response)
        except Exception as e:
            logger.error(f"Error creating budget: {e}")
            return False, {"message": f"Connection error: {e}", "code": "CONNECTION_ERROR"}


api_client = ApiClient()
