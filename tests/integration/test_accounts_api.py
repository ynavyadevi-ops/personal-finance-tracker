"""Integration tests for the Financial Accounts API endpoints."""

from fastapi.testclient import TestClient


def test_list_accounts_empty_initial(client: TestClient) -> None:
    """Verify listing accounts for user returns a list."""
    response = client.get("/api/v1/accounts")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert isinstance(response.json()["data"], list)


def test_create_and_retrieve_account(client: TestClient) -> None:
    """Verify creating a new account and retrieving it by ID."""
    payload = {
        "name": "Personal Checking",
        "account_type": "CHECKING",
        "institution_name": "JPMorgan Chase",
        "currency": "USD",
        "opening_balance": "1250.75",
    }
    create_res = client.post("/api/v1/accounts", json=payload)
    assert create_res.status_code == 201

    created_data = create_res.json()["data"]
    account_id = created_data["id"]
    assert created_data["name"] == "Personal Checking"
    assert created_data["opening_balance"] == "1250.75"
    assert created_data["is_active"] is True

    # Retrieve by ID
    get_res = client.get(f"/api/v1/accounts/{account_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == account_id


def test_create_account_duplicate_name_conflict(client: TestClient) -> None:
    """Verify duplicate account names for the same user return 409 Conflict."""
    payload = {
        "name": "Unique Name Checking",
        "account_type": "CHECKING",
        "opening_balance": "100.00",
    }
    res1 = client.post("/api/v1/accounts", json=payload)
    assert res1.status_code == 201

    # Attempt second creation with identical name
    res2 = client.post("/api/v1/accounts", json=payload)
    assert res2.status_code == 409
    assert res2.json()["success"] is False
    assert res2.json()["error"]["code"] == "CONFLICT"


def test_update_account(client: TestClient) -> None:
    """Verify modifying account attributes."""
    create_res = client.post(
        "/api/v1/accounts",
        json={"name": "Old Name", "account_type": "SAVINGS", "opening_balance": "500.00"},
    )
    acc_id = create_res.json()["data"]["id"]

    patch_res = client.patch(
        f"/api/v1/accounts/{acc_id}",
        json={"name": "Updated Name", "institution_name": "New Bank"},
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()["data"]
    assert updated_data["name"] == "Updated Name"
    assert updated_data["institution_name"] == "New Bank"


def test_archive_account(client: TestClient) -> None:
    """Verify archiving (soft-deleting) an account marks it inactive."""
    create_res = client.post(
        "/api/v1/accounts",
        json={"name": "To Archive", "account_type": "CASH", "opening_balance": "20.00"},
    )
    acc_id = create_res.json()["data"]["id"]

    delete_res = client.delete(f"/api/v1/accounts/{acc_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["data"]["is_active"] is False

    # Default active_only=True list should not include it
    list_res = client.get("/api/v1/accounts?active_only=true")
    ids = [acc["id"] for acc in list_res.json()["data"]]
    assert acc_id not in ids


def test_get_nonexistent_account_returns_404(client: TestClient) -> None:
    """Verify 404 response on non-existent account ID."""
    response = client.get("/api/v1/accounts/non-existent-uuid")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_on_empty_name(client: TestClient) -> None:
    """Verify 422 Unprocessable Entity when required fields are invalid."""
    response = client.post("/api/v1/accounts", json={"name": "", "account_type": "CHECKING"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_account_zero_balance(client: TestClient) -> None:
    """Verify account creation with zero balance is valid."""
    res = client.post(
        "/api/v1/accounts",
        json={
            "name": "Zero Balance Cash",
            "account_type": "CASH",
            "opening_balance": "0.00",
            "currency": "INR",
        },
    )
    assert res.status_code == 201
    assert res.json()["data"]["opening_balance"] == "0.00"
    assert res.json()["data"]["currency"] == "INR"


def test_list_accounts_includes_archived_when_requested(client: TestClient) -> None:
    """Verify active_only=false returns both active and archived accounts."""
    create_res = client.post(
        "/api/v1/accounts",
        json={"name": "Will Archive", "account_type": "SAVINGS", "opening_balance": "100.00"},
    )
    acc_id = create_res.json()["data"]["id"]
    client.delete(f"/api/v1/accounts/{acc_id}")

    res_all = client.get("/api/v1/accounts?active_only=false")
    assert res_all.status_code == 200
    ids = [acc["id"] for acc in res_all.json()["data"]]
    assert acc_id in ids
