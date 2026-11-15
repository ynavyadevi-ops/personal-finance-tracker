"""Unit tests for SQLAlchemy models, foreign keys, and relationships."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import AccountType, FinancialAccount, User


def test_user_creation(db_session: Session) -> None:
    """Verify User model can be persisted and queried."""
    user = User(name="Alice Smith", email="alice@example.com")
    db_session.add(user)
    db_session.flush()

    queried = db_session.execute(select(User).where(User.id == user.id)).scalar_one()
    assert queried.name == "Alice Smith"
    assert queried.email == "alice@example.com"
    assert queried.created_at is not None


def test_financial_account_creation_and_relationship(
    db_session: Session, sample_user: User
) -> None:
    """Verify FinancialAccount relationship and Decimal balance precision."""
    account = FinancialAccount(
        user_id=sample_user.id,
        name="Emergency Savings",
        account_type=AccountType.SAVINGS,
        institution_name="Ally Bank",
        currency="INR",
        opening_balance=Decimal("10000.55"),
        is_active=True,
    )
    db_session.add(account)
    db_session.flush()

    # Query via user relationship
    db_session.refresh(sample_user)
    account_names = [a.name for a in sample_user.accounts]
    assert "Emergency Savings" in account_names

    # Check exact decimal
    queried = db_session.execute(
        select(FinancialAccount).where(FinancialAccount.id == account.id)
    ).scalar_one()
    assert queried.opening_balance == Decimal("10000.55")
    assert queried.user.name == sample_user.name


def test_foreign_key_constraint_enforcement(db_session: Session) -> None:
    """Verify foreign key constraint rejects orphan accounts."""
    orphan_account = FinancialAccount(
        user_id="non-existent-user-uuid",
        name="Orphan Checking",
        account_type=AccountType.CHECKING,
        opening_balance=Decimal("100.00"),
    )
    db_session.add(orphan_account)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_cascade_delete(db_session: Session) -> None:
    """Verify deleting a user cascades to all associated accounts."""
    user = User(name="Bob Jones", email="bob@example.com")
    db_session.add(user)
    db_session.flush()

    acc1 = FinancialAccount(
        user_id=user.id,
        name="Bob Checking",
        account_type=AccountType.CHECKING,
        opening_balance=Decimal("50.00"),
    )
    acc2 = FinancialAccount(
        user_id=user.id,
        name="Bob Savings",
        account_type=AccountType.SAVINGS,
        opening_balance=Decimal("200.00"),
    )
    db_session.add_all([acc1, acc2])
    db_session.flush()

    # Delete the user
    db_session.delete(user)
    db_session.flush()

    # Verify accounts are deleted
    remaining = (
        db_session.execute(select(FinancialAccount).where(FinancialAccount.user_id == user.id))
        .scalars()
        .all()
    )
    assert len(remaining) == 0
