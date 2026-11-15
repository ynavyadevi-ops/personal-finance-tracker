"""Unit regression tests for AccountService business logic and tenant isolation."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.core.exceptions import ConflictError, NotFoundError
from src.db.models import AccountType, User
from src.schemas.account import AccountCreate, AccountUpdate
from src.services.account_service import AccountService


def test_service_create_account(db_session: Session, sample_user: User) -> None:
    """Verify AccountService successfully creates an account for a user."""
    service = AccountService(db_session)
    data = AccountCreate(
        name="Salary Checking",
        account_type=AccountType.CHECKING,
        institution_name="HDFC Bank",
        currency="INR",
        opening_balance=Decimal("25000.00"),
    )
    account = service.create_account(sample_user.id, data)
    assert account.id is not None
    assert account.name == "Salary Checking"
    assert account.institution_name == "HDFC Bank"
    assert account.currency == "INR"
    assert account.opening_balance == Decimal("25000.00")
    assert account.is_active is True


def test_service_create_duplicate_account_conflict(db_session: Session, sample_user: User) -> None:
    """Verify AccountService raises ConflictError on duplicate account name."""
    service = AccountService(db_session)
    data = AccountCreate(
        name="Unique Checking",
        account_type=AccountType.CHECKING,
        opening_balance=Decimal("1000.00"),
    )
    service.create_account(sample_user.id, data)

    with pytest.raises(ConflictError) as exc_info:
        service.create_account(sample_user.id, data)
    assert "already exists" in exc_info.value.message


def test_service_get_account_not_found(db_session: Session, sample_user: User) -> None:
    """Verify AccountService raises NotFoundError for missing account ID."""
    service = AccountService(db_session)
    with pytest.raises(NotFoundError):
        service.get_account("non-existent-id", sample_user.id)


def test_service_tenant_isolation(db_session: Session, sample_user: User) -> None:
    """Verify user cannot access an account belonging to another user (tenant isolation)."""
    service = AccountService(db_session)

    # Create second user
    other_user = User(name="Other User", email="other@domain.dev")
    db_session.add(other_user)
    db_session.flush()

    data = AccountCreate(
        name="Private Fund",
        account_type=AccountType.SAVINGS,
        opening_balance=Decimal("5000.00"),
    )
    acc = service.create_account(sample_user.id, data)

    # other_user attempts to retrieve sample_user's account
    with pytest.raises(NotFoundError):
        service.get_account(acc.id, other_user.id)

    # other_user attempts to update sample_user's account
    with pytest.raises(NotFoundError):
        service.update_account(acc.id, other_user.id, AccountUpdate(name="Hijacked"))

    # other_user attempts to archive sample_user's account
    with pytest.raises(NotFoundError):
        service.archive_account(acc.id, other_user.id)


def test_service_update_account(db_session: Session, sample_user: User) -> None:
    """Verify AccountService updates allowed fields."""
    service = AccountService(db_session)
    data = AccountCreate(
        name="Old Account Name",
        account_type=AccountType.CHECKING,
        opening_balance=Decimal("100.00"),
    )
    acc = service.create_account(sample_user.id, data)

    updated = service.update_account(
        acc.id,
        sample_user.id,
        AccountUpdate(name="Renamed Account", institution_name="New Bank"),
    )
    assert updated.name == "Renamed Account"
    assert updated.institution_name == "New Bank"


def test_service_archive_and_list_accounts(db_session: Session, sample_user: User) -> None:
    """Verify archiving marks account inactive and filtering respects active_only."""
    service = AccountService(db_session)
    data = AccountCreate(
        name="Disposable Account",
        account_type=AccountType.CASH,
        opening_balance=Decimal("50.00"),
    )
    acc = service.create_account(sample_user.id, data)

    # Initially listed in active
    active_accounts = service.list_accounts(sample_user.id, active_only=True)
    assert any(a.id == acc.id for a in active_accounts)

    # Archive
    archived = service.archive_account(acc.id, sample_user.id)
    assert archived.is_active is False

    # No longer in active_only list
    active_after = service.list_accounts(sample_user.id, active_only=True)
    assert not any(a.id == acc.id for a in active_after)

    # Present in all accounts list
    all_accounts = service.list_accounts(sample_user.id, active_only=False)
    assert any(a.id == acc.id for a in all_accounts)
