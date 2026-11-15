"""Unit tests for BudgetService: budget allocations, spending utilization, and rollovers."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.core.exceptions import ValidationError
from src.db.models.account import AccountType, FinancialAccount
from src.db.models.category import Category, CategoryType
from src.db.models.user import User
from src.schemas.budget import BudgetCreate
from src.schemas.transaction import TransactionCreate, TransferCreate
from src.services.budget_service import BudgetService
from src.services.transaction_service import TransactionService


@pytest.fixture
def expense_cat(db_session: Session, sample_user: User) -> Category:
    """Fixture providing an expense category for budgeting."""
    cat = Category(
        user_id=sample_user.id,
        name="Dining Out",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


@pytest.fixture
def income_cat(db_session: Session, sample_user: User) -> Category:
    """Fixture providing an income category."""
    cat = Category(
        user_id=sample_user.id,
        name="Freelance",
        category_type=CategoryType.INCOME,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


def test_set_budget_success(db_session: Session, sample_user: User, expense_cat: Category) -> None:
    """Verify creating a new monthly budget allocation."""
    service = BudgetService(db_session)
    payload = BudgetCreate(
        category_id=expense_cat.id,
        month=11,
        year=2026,
        amount=Decimal("5000.00"),
        rollover_enabled=True,
        notes="Monthly dining allowance",
    )
    res = service.set_budget(sample_user.id, payload)
    assert res.id is not None
    assert res.amount == Decimal("5000.00")
    assert res.month == 11
    assert res.year == 2026
    assert res.rollover_enabled is True


def test_set_budget_updates_existing(
    db_session: Session, sample_user: User, expense_cat: Category
) -> None:
    """Verify updating an existing budget for the same month/year/category."""
    service = BudgetService(db_session)
    payload1 = BudgetCreate(
        category_id=expense_cat.id,
        month=11,
        year=2026,
        amount=Decimal("4000.00"),
    )
    res1 = service.set_budget(sample_user.id, payload1)

    payload2 = BudgetCreate(
        category_id=expense_cat.id,
        month=11,
        year=2026,
        amount=Decimal("6000.00"),
    )
    res2 = service.set_budget(sample_user.id, payload2)
    assert res1.id == res2.id
    assert res2.amount == Decimal("6000.00")


def test_set_budget_invalid_amount_fails(
    db_session: Session, sample_user: User, expense_cat: Category
) -> None:
    """Verify non-positive budget amount raises ValidationError."""
    service = BudgetService(db_session)
    with pytest.raises((ValidationError, PydanticValidationError)):
        payload = BudgetCreate(
            category_id=expense_cat.id,
            month=11,
            year=2026,
            amount=Decimal("0.00"),
        )
        service.set_budget(sample_user.id, payload)


def test_set_budget_income_category_fails(
    db_session: Session, sample_user: User, income_cat: Category
) -> None:
    """Verify assigning a budget to an INCOME category raises ValidationError."""
    service = BudgetService(db_session)
    payload = BudgetCreate(
        category_id=income_cat.id,
        month=11,
        year=2026,
        amount=Decimal("10000.00"),
    )
    with pytest.raises(ValidationError) as exc:
        service.set_budget(sample_user.id, payload)
    assert "EXPENSE categories" in exc.value.message


def test_budget_utilization_thresholds(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    expense_cat: Category,
) -> None:
    """Verify budget threshold calculation: NORMAL, WARNING (>=80%), and EXCEEDED (>=100%)."""
    budget_service = BudgetService(db_session)
    tx_service = TransactionService(db_session)

    # 1. Budget = 10,000
    budget_service.set_budget(
        sample_user.id,
        BudgetCreate(
            category_id=expense_cat.id,
            month=11,
            year=2026,
            amount=Decimal("10000.00"),
        ),
    )

    # Spending 0 -> NORMAL
    util0 = budget_service.get_budget_utilization(sample_user.id, expense_cat.id, 11, 2026)
    assert util0.status == "NORMAL"
    assert util0.spent_amount == Decimal("0.00")
    assert util0.remaining_amount == Decimal("10000.00")

    # Add expense = 8,500 (85%) -> WARNING
    tx_service.record_expense(
        sample_user.id,
        TransactionCreate(
            account_id=sample_account.id,
            category_id=expense_cat.id,
            amount=Decimal("8500.00"),
            currency="INR",
            description="Restaurant dining",
            transaction_date=date(2026, 11, 10),
        ),
    )

    util1 = budget_service.get_budget_utilization(sample_user.id, expense_cat.id, 11, 2026)
    assert util1.status == "WARNING"
    assert util1.spent_amount == Decimal("8500.00")
    assert util1.remaining_amount == Decimal("1500.00")
    assert util1.is_overspent is False

    # Add expense = 2,000 (total 10,500 > 10,000) -> EXCEEDED
    tx_service.record_expense(
        sample_user.id,
        TransactionCreate(
            account_id=sample_account.id,
            category_id=expense_cat.id,
            amount=Decimal("2000.00"),
            currency="INR",
            description="Fine dining",
            transaction_date=date(2026, 11, 15),
        ),
    )

    util2 = budget_service.get_budget_utilization(sample_user.id, expense_cat.id, 11, 2026)
    assert util2.status == "EXCEEDED"
    assert util2.spent_amount == Decimal("10500.00")
    assert util2.remaining_amount == Decimal("-500.00")
    assert util2.is_overspent is True


def test_budget_rollover_from_previous_month(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    expense_cat: Category,
) -> None:
    """Verify unspent balance rolls over when rollover_enabled is True."""
    budget_service = BudgetService(db_session)
    tx_service = TransactionService(db_session)

    # Previous month: Oct 2026, budget 10,000, spent 7,000 -> 3,000 unspent
    budget_service.set_budget(
        sample_user.id,
        BudgetCreate(
            category_id=expense_cat.id,
            month=10,
            year=2026,
            amount=Decimal("10000.00"),
        ),
    )
    tx_service.record_expense(
        sample_user.id,
        TransactionCreate(
            account_id=sample_account.id,
            category_id=expense_cat.id,
            amount=Decimal("7000.00"),
            currency="INR",
            description="Oct dining",
            transaction_date=date(2026, 10, 15),
        ),
    )

    # Current month: Nov 2026, budget 5,000 with rollover_enabled=True
    budget_service.set_budget(
        sample_user.id,
        BudgetCreate(
            category_id=expense_cat.id,
            month=11,
            year=2026,
            amount=Decimal("5000.00"),
            rollover_enabled=True,
        ),
    )

    util = budget_service.get_budget_utilization(sample_user.id, expense_cat.id, 11, 2026)
    # Rollover = 3,000. Effective budget = 5,000 + 3,000 = 8,000
    assert util.rollover_amount == Decimal("3000.00")
    assert util.budgeted_amount == Decimal("5000.00")
    assert util.remaining_amount == Decimal("8000.00")


def test_transfers_excluded_from_budget_spending(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    expense_cat: Category,
) -> None:
    """Verify account transfers are excluded from monthly category budget spending."""
    budget_service = BudgetService(db_session)
    tx_service = TransactionService(db_session)

    savings = FinancialAccount(
        user_id=sample_user.id,
        name="Emergency Savings Account",
        account_type=AccountType.SAVINGS,
        currency="INR",
        opening_balance=Decimal("20000.00"),
    )
    db_session.add(savings)
    db_session.flush()

    budget_service.set_budget(
        sample_user.id,
        BudgetCreate(
            category_id=expense_cat.id,
            month=11,
            year=2026,
            amount=Decimal("5000.00"),
        ),
    )

    # Add a TRANSFER transaction
    tx_service.record_transfer(
        sample_user.id,
        TransferCreate(
            source_account_id=sample_account.id,
            destination_account_id=savings.id,
            amount=Decimal("3000.00"),
            currency="INR",
            description="Transfer between accounts",
            transaction_date=date(2026, 11, 5),
        ),
    )

    util = budget_service.get_budget_utilization(sample_user.id, expense_cat.id, 11, 2026)
    # Transfer must not count as expense
    assert util.spent_amount == Decimal("0.00")
    assert util.remaining_amount == Decimal("5000.00")
