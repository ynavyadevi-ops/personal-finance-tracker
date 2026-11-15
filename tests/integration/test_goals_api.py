"""Integration tests for Savings Goals and Milestone Progress API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import User


def test_create_goal_contribute_and_withdraw(client: TestClient) -> None:
    """Verify creating a savings goal, allocating contributions, and withdrawing."""
    # 1. Create goal
    create_res = client.post(
        "/api/v1/goals",
        json={
            "name": "New Laptop",
            "target_amount": "80000.00",
            "currency": "INR",
        },
    )
    assert create_res.status_code == 201
    goal_id = create_res.json()["data"]["id"]

    # 2. Add contribution
    contrib_res = client.post(
        f"/api/v1/goals/{goal_id}/contribute",
        json={"amount": "20000.00", "notes": "From bonus"},
    )
    assert contrib_res.status_code == 200
    prog = contrib_res.json()["data"]
    assert prog["current_amount"] == "20000.00"
    assert prog["progress_percentage"] == "25.00"
    assert prog["is_achieved"] is False

    # 3. Withdraw part of contribution
    with_res = client.post(
        f"/api/v1/goals/{goal_id}/withdraw",
        json={"amount": "5000.00"},
    )
    assert with_res.status_code == 200
    prog_after = with_res.json()["data"]
    assert prog_after["current_amount"] == "15000.00"
    assert prog_after["progress_percentage"] == "18.75"

    # 4. Fetch goal progress
    get_res = client.get(f"/api/v1/goals/{goal_id}/progress")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["current_amount"] == "15000.00"


def test_list_goals(client: TestClient) -> None:
    """Verify listing goals for authenticated user."""
    client.post(
        "/api/v1/goals",
        json={"name": "Vacation Fund", "target_amount": "50000.00"},
    )
    res = client.get("/api/v1/goals")
    assert res.status_code == 200
    goals = res.json()["data"]
    assert isinstance(goals, list)
    assert any(g["name"] == "Vacation Fund" for g in goals)


def test_cross_user_goal_isolation(unauthenticated_client: TestClient, db_session: Session) -> None:
    """Verify user B cannot view or contribute to user A's savings goal."""
    user_a = User(id="user-goal-a", name="User A", email="goala@iso.dev")
    user_b = User(id="user-goal-b", name="User B", email="goalb@iso.dev")
    db_session.add_all([user_a, user_b])
    db_session.flush()

    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    # User A creates goal
    goal_res = unauthenticated_client.post(
        "/api/v1/goals",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "User A Private Goal", "target_amount": "10000.00"},
    )
    goal_id = goal_res.json()["data"]["id"]

    # User B attempts to contribute -> 404
    res = unauthenticated_client.post(
        f"/api/v1/goals/{goal_id}/contribute",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"amount": "500.00"},
    )
    assert res.status_code == 404
