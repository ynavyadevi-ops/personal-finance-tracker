"""Integration tests for Categories API."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.security import create_access_token
from src.db.models import Category, CategoryType, User, UserRole


def test_list_categories_api(client: TestClient, db_session: Session) -> None:
    """Verify listing categories via API including defaults and user isolation."""
    # Create test user
    user = User(
        id="cat-api-user-id",
        email="catuser@example.com",
        name="Category User",
        role=UserRole.USER,
        is_active=True,
    )
    other_user = User(
        id="other-user-uuid",
        email="otheruser@example.com",
        name="Other User",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add_all([user, other_user])

    # Seed default category (user_id=None) and private category
    default_cat = Category(
        user_id=None,
        name="Global Dining",
        category_type=CategoryType.EXPENSE,
        is_default=True,
    )
    private_cat = Category(
        user_id=user.id,
        name="User Custom Expense",
        category_type=CategoryType.EXPENSE,
        is_default=False,
    )
    other_private_cat = Category(
        user_id="other-user-uuid",
        name="Other User Private",
        category_type=CategoryType.EXPENSE,
        is_default=False,
    )
    db_session.add_all([default_cat, private_cat, other_private_cat])
    db_session.flush()

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch categories
    res = client.get("/api/v1/categories", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    cat_names = [c["name"] for c in data]

    assert "Global Dining" in cat_names
    assert "User Custom Expense" in cat_names
    assert "Other User Private" not in cat_names

    # Filter by category_type=EXPENSE
    res_expense = client.get("/api/v1/categories?category_type=EXPENSE", headers=headers)
    assert res_expense.status_code == 200
    assert all(c["category_type"] == "EXPENSE" for c in res_expense.json()["data"])
