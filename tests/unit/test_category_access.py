"""Unit tests verifying category multi-tenancy, system defaults, and isolation."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.core.exceptions import ValidationError
from src.db.models import (
    AccountType,
    Category,
    CategoryType,
    FinancialAccount,
    User,
    UserRole,
)
from src.db.seed import seed_database
from src.repositories.category_repo import CategoryRepository
from src.schemas.budget import BudgetCreate
from src.schemas.transaction import TransactionCreate
from src.services.budget_service import BudgetService
from src.services.transaction_service import TransactionService


def test_category_access_and_isolation(db_session: Session) -> None:
    """Validate Step 4 requirements 1-8 for category access, isolation, and budgets."""
    repo = CategoryRepository(db_session)

    # Create two test users
    user_a = User(
        id="user-a-uuid",
        email="user_a@example.com",
        name="User A",
        role=UserRole.USER,
        is_active=True,
    )
    user_b = User(
        id="user-b-uuid",
        email="user_b@example.com",
        name="User B",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    db_session.flush()

    # 1 & 2. System defaults accessible to both USER A and USER B
    default_cat = Category(
        user_id=None,
        name="Groceries & Dining",
        category_type=CategoryType.EXPENSE,
        is_default=True,
    )
    default_income_cat = Category(
        user_id=None,
        name="Salary",
        category_type=CategoryType.INCOME,
        is_default=True,
    )
    db_session.add_all([default_cat, default_income_cat])
    db_session.flush()

    # USER A access check
    cat_a = repo.get_user_accessible_category(default_cat.id, user_a.id)
    assert cat_a is not None
    assert cat_a.id == default_cat.id
    assert cat_a.name == "Groceries & Dining"

    # USER B access check
    cat_b = repo.get_user_accessible_category(default_cat.id, user_b.id)
    assert cat_b is not None
    assert cat_b.id == default_cat.id
    assert cat_b.name == "Groceries & Dining"

    # 3. USER A cannot access USER B's private categories
    private_b = repo.create(
        user_id=user_b.id,
        name="User B Private Project",
        category_type=CategoryType.EXPENSE,
        is_default=False,
    )
    db_session.flush()

    # USER B can access their private category
    assert repo.get_user_accessible_category(private_b.id, user_b.id) is not None

    # USER A CANNOT access USER B's private category
    assert repo.get_user_accessible_category(private_b.id, user_a.id) is None

    # In listing, USER A's categories do not include USER B's private category
    user_a_cats = repo.list_by_user(user_a.id)
    user_a_cat_ids = [c.id for c in user_a_cats]
    assert private_b.id not in user_a_cat_ids
    assert default_cat.id in user_a_cat_ids
    assert default_income_cat.id in user_a_cat_ids

    # 4. Duplicate system defaults are prevented in seed_database
    seed_database(db_session)
    seed_database(db_session)  # Second run should be idempotent
    groceries_count = len([
        c for c in repo.list_by_user(user_a.id)
        if c.name == "Groceries & Dining" and c.is_default
    ])
    assert groceries_count == 1

    # 5. Existing transactions remain valid with category
    acc_a = FinancialAccount(
        user_id=user_a.id,
        name="User A Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("10000.00"),
        is_active=True,
    )
    db_session.add(acc_a)
    db_session.flush()

    tx_service = TransactionService(db_session)
    expense_tx = tx_service.record_expense(
        user_id=user_a.id,
        payload=TransactionCreate(
            account_id=acc_a.id,
            category_id=default_cat.id,
            amount=Decimal("2000.00"),
            transaction_date="2026-11-16",
            description="Supermarket run",
        ),
    )
    assert expense_tx.amount == Decimal("2000.00")
    assert len(expense_tx.entries) == 1
    assert expense_tx.entries[0].category_id == default_cat.id

    # 6. Budget creation accepts a valid system-default category
    budget_service = BudgetService(db_session)
    budget = budget_service.set_budget(
        user_id=user_a.id,
        payload=BudgetCreate(
            category_id=default_cat.id,
            month=11,
            year=2026,
            amount=Decimal("5000.00"),
        ),
    )
    assert budget.category_id == default_cat.id
    assert budget.amount == Decimal("5000.00")

    # Verify utilization calculation
    util = budget_service.get_budget_utilization(
        user_id=user_a.id,
        category_id=default_cat.id,
        month=11,
        year=2026,
    )
    assert util.budgeted_amount == Decimal("5000.00")
    assert util.spent_amount == Decimal("2000.00")
    assert util.remaining_amount == Decimal("3000.00")
    assert util.utilization_percentage == Decimal("40.00")
    assert util.status == "NORMAL"

    # 7. New users can use default categories immediately
    user_new = User(
        id="user-new-uuid",
        email="new_user@example.com",
        name="New User",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user_new)
    db_session.flush()

    new_user_cats = repo.list_by_user(user_new.id)
    assert any(c.id == default_cat.id for c in new_user_cats)
    assert any(c.id == default_income_cat.id for c in new_user_cats)

    # 8. Category types remain consistent (cannot allocate budget to INCOME category)
    with pytest.raises(ValidationError) as exc:
        budget_service.set_budget(
            user_id=user_a.id,
            payload=BudgetCreate(
                category_id=default_income_cat.id,
                month=11,
                year=2026,
                amount=Decimal("1000.00"),
            ),
        )
    assert "EXPENSE" in str(exc.value)
