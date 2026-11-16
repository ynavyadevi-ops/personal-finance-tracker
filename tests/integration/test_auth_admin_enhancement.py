"""Comprehensive integration tests for User Registration, RBAC, Admin Portal, and Privacy Boundaries."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.main import app
from src.core.security import create_access_token, hash_password
from src.db.models.user import User, UserRole


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Fixture providing an active administrator user."""
    admin = User(
        id="admin-test-id",
        name="Platform Administrator",
        email="admin@test.dev",
        role=UserRole.ADMIN,
        is_active=True,
        must_change_password=False,
        hashed_password=hash_password("AdminSecurePass123!"),
    )
    db_session.add(admin)
    db_session.flush()
    return admin


@pytest.fixture
def admin_client(db_session: Session, admin_user: User) -> Generator[TestClient, None, None]:
    """Yield an authenticated FastAPI TestClient for the admin user."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(admin_user.id)
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def regular_user(db_session: Session) -> User:
    """Fixture providing an active standard user."""
    user = User(
        id="regular-test-user-id",
        name="Regular Customer",
        email="regular@test.dev",
        role=UserRole.USER,
        is_active=True,
        must_change_password=False,
        hashed_password=hash_password("RegularSecurePass123!"),
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def regular_client(db_session: Session, regular_user: User) -> Generator[TestClient, None, None]:
    """Yield an authenticated FastAPI TestClient for a regular user."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(regular_user.id)
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client
    app.dependency_overrides.clear()


# =============================================================================
# 1. USER REGISTRATION ENDPOINT TESTS
# =============================================================================


def test_register_user_success(unauthenticated_client: TestClient, db_session: Session) -> None:
    """Verify clean registration of a new user account."""
    payload = {
        "name": "Alice Smith",
        "email": "alice@example.dev",
        "password": "StrongPassword999!",
        "confirm_password": "StrongPassword999!",
    }

    response = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["email"] == "alice@example.dev"
    assert data["name"] == "Alice Smith"
    assert data["role"] == "USER"
    assert data["is_active"] is True
    assert "password" not in data
    assert "hashed_password" not in data

    # Verify user can log in immediately
    login_resp = unauthenticated_client.post(
        "/api/v1/auth/token",
        data={"username": "alice@example.dev", "password": "StrongPassword999!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert login_data["role"] == "USER"
    assert login_data["must_change_password"] is False


def test_register_duplicate_email_anti_enumeration(
    unauthenticated_client: TestClient,
    regular_user: User,
) -> None:
    """Verify duplicate registration fails with generic safe message to prevent user enumeration."""
    payload = {
        "name": "Impostor",
        "email": regular_user.email,  # Already exists
        "password": "StrongPassword999!",
        "confirm_password": "StrongPassword999!",
    }

    response = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    # Safe generic message: never reveal account existence
    assert "Unable to complete registration with the provided details." in body["error"]["message"]


def test_register_password_mismatch(unauthenticated_client: TestClient) -> None:
    """Verify registration fails when confirm_password does not match password."""
    payload = {
        "name": "Bob Jones",
        "email": "bob@example.dev",
        "password": "StrongPassword999!",
        "confirm_password": "DifferentPassword888!",
    }

    response = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_weak_password_constraints(unauthenticated_client: TestClient) -> None:
    """Verify password complexity validation rejects weak passwords with specific messages."""
    # 1. No uppercase
    payload1 = {
        "name": "Charlie",
        "email": "charlie@example.dev",
        "password": "weakpassword1!",
        "confirm_password": "weakpassword1!",
    }
    resp1 = unauthenticated_client.post("/api/v1/auth/register", json=payload1)
    assert resp1.status_code == 422
    body1 = resp1.json()
    err_msgs1 = [e["message"] for e in body1["error"]["details"]["validation_errors"]]
    assert any("uppercase" in m for m in err_msgs1)

    # 2. No special character
    payload2 = {
        "name": "Charlie",
        "email": "charlie@example.dev",
        "password": "WeakPassword123",
        "confirm_password": "WeakPassword123",
    }
    resp2 = unauthenticated_client.post("/api/v1/auth/register", json=payload2)
    assert resp2.status_code == 422
    body2 = resp2.json()
    err_msgs2 = [e["message"] for e in body2["error"]["details"]["validation_errors"]]
    assert any("special character" in m for m in err_msgs2)

    # 3. No digit
    payload3 = {
        "name": "Charlie",
        "email": "charlie@example.dev",
        "password": "WeakPassword!",
        "confirm_password": "WeakPassword!",
    }
    resp3 = unauthenticated_client.post("/api/v1/auth/register", json=payload3)
    assert resp3.status_code == 422
    body3 = resp3.json()
    err_msgs3 = [e["message"] for e in body3["error"]["details"]["validation_errors"]]
    assert any("digit" in m for m in err_msgs3)

    # 4. Length under 8 characters
    payload4 = {
        "name": "Charlie",
        "email": "charlie@example.dev",
        "password": "Pass1!",
        "confirm_password": "Pass1!",
    }
    resp4 = unauthenticated_client.post("/api/v1/auth/register", json=payload4)
    assert resp4.status_code == 422

    # 5. Invalid email address
    payload5 = {
        "name": "Charlie",
        "email": "not-a-valid-email",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    resp5 = unauthenticated_client.post("/api/v1/auth/register", json=payload5)
    assert resp5.status_code == 422


# =============================================================================
# 2. RBAC & ADMIN ACCESS CONTROLS
# =============================================================================


def test_admin_endpoints_require_admin_role(
    regular_client: TestClient,
    unauthenticated_client: TestClient,
) -> None:
    """Verify standard users and unauthenticated requests are strictly rejected from admin endpoints."""
    # Unauthenticated
    assert unauthenticated_client.get("/api/v1/admin/overview").status_code == 401
    assert unauthenticated_client.get("/api/v1/admin/users").status_code == 401

    # Standard authenticated user (HTTP 403 Forbidden)
    resp_overview = regular_client.get("/api/v1/admin/overview")
    assert resp_overview.status_code == 403
    assert "Administrative privileges are required" in resp_overview.json()["error"]["message"]

    resp_users = regular_client.get("/api/v1/admin/users")
    assert resp_users.status_code == 403
    assert "Administrative privileges are required" in resp_users.json()["error"]["message"]


def test_admin_overview_metrics(admin_client: TestClient, regular_user: User) -> None:
    """Verify admin user can fetch operational overview metrics."""
    response = admin_client.get("/api/v1/admin/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["total_users"] >= 2
    assert data["active_users"] >= 2
    assert data["disabled_users"] == 0
    assert data["db_connected"] is True
    assert data["registration_enabled"] is True


def test_admin_list_and_search_users(
    admin_client: TestClient,
    admin_user: User,
    regular_user: User,
) -> None:
    """Verify admin can list and filter registered users."""
    response = admin_client.get("/api/v1/admin/users")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    users = body["data"]
    assert len(users) >= 2

    # Verify search by email
    search_resp = admin_client.get("/api/v1/admin/users?search=regular")
    assert search_resp.status_code == 200
    search_users = search_resp.json()["data"]
    assert len(search_users) == 1
    assert search_users[0]["email"] == regular_user.email


# =============================================================================
# 3. ACCOUNT STATUS MANAGEMENT & DEACTIVATION
# =============================================================================


def test_admin_disable_user_account(
    admin_client: TestClient,
    unauthenticated_client: TestClient,
    regular_user: User,
) -> None:
    """Verify admin can disable a user account and disabled user cannot authenticate."""
    # 1. Disable user
    patch_resp = admin_client.patch(
        f"/api/v1/admin/users/{regular_user.id}/status",
        json={"is_active": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["is_active"] is False

    # 2. Deactivated user cannot log in
    login_resp = unauthenticated_client.post(
        "/api/v1/auth/token",
        data={"username": regular_user.email, "password": "RegularSecurePass123!"},
    )
    assert login_resp.status_code == 401
    assert "disabled" in login_resp.json()["error"]["message"]

    # 3. Token check: existing token is rejected
    user_token = create_access_token(regular_user.id)
    me_resp = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert me_resp.status_code == 401
    assert "disabled" in me_resp.json()["error"]["message"]

    # 4. Re-activate user
    reactivate_resp = admin_client.patch(
        f"/api/v1/admin/users/{regular_user.id}/status",
        json={"is_active": True},
    )
    assert reactivate_resp.status_code == 200
    assert reactivate_resp.json()["data"]["is_active"] is True


def test_admin_cannot_disable_self(admin_client: TestClient, admin_user: User) -> None:
    """Verify administrator cannot disable their own account."""
    response = admin_client.patch(
        f"/api/v1/admin/users/{admin_user.id}/status",
        json={"is_active": False},
    )
    assert response.status_code == 422
    assert (
        "Administrators cannot disable their own active account"
        in response.json()["error"]["message"]
    )


# =============================================================================
# 4. PASSWORD RESET & MANDATORY PASSWORD CHANGE
# =============================================================================


def test_admin_password_reset_and_force_change(
    admin_client: TestClient,
    unauthenticated_client: TestClient,
    regular_user: User,
) -> None:
    """Verify temporary password generation, token flag, and mandatory password change workflow."""
    # 1. Admin generates temporary password
    reset_resp = admin_client.post(f"/api/v1/admin/users/{regular_user.id}/reset-password")
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()["data"]
    temp_pwd = reset_data["temporary_password"]
    assert temp_pwd is not None
    assert reset_data["must_change_password"] is True

    # 2. User logs in with temporary password
    login_resp = unauthenticated_client.post(
        "/api/v1/auth/token",
        data={"username": regular_user.email, "password": temp_pwd},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert token_data["must_change_password"] is True
    temp_token = token_data["access_token"]

    # 3. User changes password
    new_password = "BrandNewSuperSecurePass456!"
    change_resp = unauthenticated_client.post(
        "/api/v1/auth/change-password",
        json={
            "old_password": temp_pwd,
            "new_password": new_password,
            "confirm_password": new_password,
        },
        headers={"Authorization": f"Bearer {temp_token}"},
    )
    assert change_resp.status_code == 200
    assert change_resp.json()["success"] is True

    # 4. User logs in with new password
    new_login_resp = unauthenticated_client.post(
        "/api/v1/auth/token",
        data={"username": regular_user.email, "password": new_password},
    )
    assert new_login_resp.status_code == 200
    assert new_login_resp.json()["must_change_password"] is False


# =============================================================================
# 5. REGISTRATION KILL-SWITCH
# =============================================================================


def test_registration_kill_switch(
    admin_client: TestClient,
    unauthenticated_client: TestClient,
) -> None:
    """Verify admin can disable public registration and re-enable it."""
    # Disable registration
    patch_resp = admin_client.patch(
        "/api/v1/admin/settings",
        json={"registration_enabled": False},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["registration_enabled"] == "false"

    # Attempt registration while disabled
    payload = {
        "name": "Denied User",
        "email": "denied@example.dev",
        "password": "ValidPassword123!",
        "confirm_password": "ValidPassword123!",
    }
    reg_resp = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert reg_resp.status_code == 403
    assert "disabled by administrator" in reg_resp.json()["error"]["message"]

    # Re-enable registration
    patch_resp2 = admin_client.patch(
        "/api/v1/admin/settings",
        json={"registration_enabled": True},
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["data"]["registration_enabled"] == "true"

    # Registration succeeds now
    reg_resp2 = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert reg_resp2.status_code == 201


# =============================================================================
# 6. STRICT FINANCIAL PRIVACY SEGREGATION
# =============================================================================


def test_admin_user_response_excludes_financial_records(
    admin_client: TestClient,
    regular_user: User,
) -> None:
    """Verify that administrative user responses strictly contain NO financial data."""
    response = admin_client.get("/api/v1/admin/users")
    assert response.status_code == 200
    users = response.json()["data"]

    for user in users:
        # Check forbidden financial keys
        assert "accounts" not in user
        assert "transactions" not in user
        assert "balance" not in user
        assert "budgets" not in user
        assert "loans" not in user
        assert "investments" not in user
        assert "savings_goals" not in user
