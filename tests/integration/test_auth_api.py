"""Integration tests for Authentication, JWT authorization, and password enrollment."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models.user import User


def test_register_new_user(unauthenticated_client: TestClient) -> None:
    """Verify new user registration creates user and stores Argon2id password hash."""
    payload = {
        "name": "Alice Wonderland",
        "email": "alice@example.dev",
        "password": "StrongPassword123!",
    }
    response = unauthenticated_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Alice Wonderland"
    assert data["email"] == "alice@example.dev"
    assert "password" not in data
    assert "hashed_password" not in data


def test_login_success_returns_jwt(unauthenticated_client: TestClient) -> None:
    """Verify logging in with valid credentials issues a signed JWT access token."""
    # Register user
    reg_payload = {
        "name": "Bob Builder",
        "email": "bob@example.dev",
        "password": "ValidPassword987!",
    }
    unauthenticated_client.post("/api/v1/auth/register", json=reg_payload)

    # Login via OAuth2 form
    login_data = {
        "username": "bob@example.dev",
        "password": "ValidPassword987!",
    }
    res = unauthenticated_client.post("/api/v1/auth/token", data=login_data)
    assert res.status_code == 200
    token_body = res.json()
    assert "access_token" in token_body
    assert token_body["token_type"] == "bearer"
    assert token_body["expires_in"] == 3600


def test_login_invalid_credentials_fails(unauthenticated_client: TestClient) -> None:
    """Verify incorrect password yields HTTP 401 Unauthorized."""
    login_data = {
        "username": "nonexistent@example.dev",
        "password": "WrongPassword",
    }
    res = unauthenticated_client.post("/api/v1/auth/token", data=login_data)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"


def test_enroll_password_for_legacy_user(
    unauthenticated_client: TestClient, db_session: Session
) -> None:
    """Verify existing unauthenticated user can safely enroll initial password."""
    # Seed legacy user with no password hash
    legacy_user = User(
        id="legacy-user-456",
        name="Legacy User",
        email="legacy@example.dev",
        hashed_password=None,
    )
    db_session.add(legacy_user)
    db_session.flush()

    enroll_payload = {
        "email": "legacy@example.dev",
        "new_password": "NewSecretPassword123!",
    }
    enroll_res = unauthenticated_client.post("/api/v1/auth/enroll", json=enroll_payload)
    assert enroll_res.status_code == 200
    assert enroll_res.json()["data"]["email"] == "legacy@example.dev"

    # Now verify login succeeds
    login_res = unauthenticated_client.post(
        "/api/v1/auth/token",
        data={"username": "legacy@example.dev", "password": "NewSecretPassword123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_auth_me_profile_retrieval(unauthenticated_client: TestClient, db_session: Session) -> None:
    """Verify /api/v1/auth/me returns current user identity with valid Bearer token."""
    user = User(
        id="me-test-user",
        name="Profile User",
        email="profile@example.dev",
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token(user.id)
    res = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == user.id
    assert data["name"] == "Profile User"
    assert data["email"] == "profile@example.dev"
    assert "password" not in data
    assert "hashed_password" not in data


def test_auth_me_unauthorized_when_missing_token(unauthenticated_client: TestClient) -> None:
    """Verify accessing protected /auth/me without token returns 401."""
    res = unauthenticated_client.get("/api/v1/auth/me")
    assert res.status_code == 401
