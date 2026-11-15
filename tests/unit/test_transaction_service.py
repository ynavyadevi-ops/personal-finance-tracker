"""Unit tests for TransactionService: income, expense, transfers, idempotency, and reversals."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.core.exceptions import (
    CurrencyMismatchError,
    NotFoundError,
    ValidationError,
)
from src.db.models.account import AccountType, FinancialAccount
from src.db.models.category import Category, CategoryType
from src.db.models.transaction import EntryType, TransactionType
from src.db.models.user import User
from src.schemas.transaction import TransactionCreate, TransferCreate
from src.services.transaction_service import TransactionService


@pytest.fixture
def sample_category(db_session: Session, sample_user: User) -> Category:
    """Fixture providing a test expense category."""
    cat = Category(
        user_id=sample_user.id,
        name="Groceries",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


@pytest.fixture
def sample_income_category(db_session: Session, sample_user: User) -> Category:
    """Fixture providing a test income category."""
    cat = Category(
        user_id=sample_user.id,
        name="Salary",
        category_type=CategoryType.INCOME,
    )
    db_session.add(cat)
    db_session.flush()
    return cat


def test_record_income_success(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    sample_income_category: Category,
) -> None:
    """Verify recording income creates a transaction with DEBIT entry on the asset account."""
    service = TransactionService(db_session)
    payload = TransactionCreate(
        transaction_type=TransactionType.INCOME,
        amount=Decimal("50000.00"),
        currency="INR",
        transaction_date=date(2026, 11, 1),
        description="Monthly salary",
        category_id=sample_income_category.id,
        account_id=sample_account.id,
    )
    tx = service.record_transaction(sample_user.id, payload)
    assert tx.id is not None
    assert tx.transaction_type == TransactionType.INCOME
    assert tx.amount == Decimal("50000.00")
    assert len(tx.entries) == 1
    assert tx.entries[0].entry_type == EntryType.DEBIT
    assert tx.entries[0].amount == Decimal("50000.00")
    assert tx.entries[0].account_id == sample_account.id


def test_record_expense_success(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    sample_category: Category,
) -> None:
    """Verify recording expense creates a transaction with CREDIT entry on the paying account."""
    service = TransactionService(db_session)
    payload = TransactionCreate(
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("250.75"),
        currency="INR",
        transaction_date=date(2026, 11, 2),
        description="Supermarket groceries",
        category_id=sample_category.id,
        account_id=sample_account.id,
    )
    tx = service.record_transaction(sample_user.id, payload)
    assert tx.id is not None
    assert tx.transaction_type == TransactionType.EXPENSE
    assert tx.amount == Decimal("250.75")
    assert len(tx.entries) == 1
    assert tx.entries[0].entry_type == EntryType.CREDIT
    assert tx.entries[0].amount == Decimal("250.75")
    assert tx.entries[0].account_id == sample_account.id


def test_record_transfer_success(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify atomic transfer creates 1 CREDIT on source and 1 DEBIT on destination."""
    savings = FinancialAccount(
        user_id=sample_user.id,
        name="Emergency Savings",
        account_type=AccountType.SAVINGS,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    db_session.add(savings)
    db_session.flush()

    service = TransactionService(db_session)
    payload = TransferCreate(
        source_account_id=sample_account.id,
        destination_account_id=savings.id,
        amount=Decimal("500.00"),
        currency="INR",
        transaction_date=date(2026, 11, 3),
        description="Transfer to savings",
    )
    tx = service.record_transfer(sample_user.id, payload)
    assert tx.transaction_type == TransactionType.TRANSFER
    assert tx.amount == Decimal("500.00")
    assert len(tx.entries) == 2

    # Check credit entry on source
    credit_entry = next(e for e in tx.entries if e.entry_type == EntryType.CREDIT)
    assert credit_entry.account_id == sample_account.id
    assert credit_entry.amount == Decimal("500.00")

    # Check debit entry on destination
    debit_entry = next(e for e in tx.entries if e.entry_type == EntryType.DEBIT)
    assert debit_entry.account_id == savings.id
    assert debit_entry.amount == Decimal("500.00")


def test_transfer_same_account_fails(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify transfer fails if source and destination accounts are the same."""
    service = TransactionService(db_session)
    payload = TransferCreate(
        source_account_id=sample_account.id,
        destination_account_id=sample_account.id,
        amount=Decimal("100.00"),
        currency="INR",
    )
    with pytest.raises(ValidationError) as exc:
        service.record_transfer(sample_user.id, payload)
    assert "must be distinct" in exc.value.message


def test_transfer_currency_mismatch_fails(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify transfer raises CurrencyMismatchError if account currencies do not match."""
    usd_account = FinancialAccount(
        user_id=sample_user.id,
        name="US Brokerage",
        account_type=AccountType.INVESTMENT,
        currency="USD",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(usd_account)
    db_session.flush()

    service = TransactionService(db_session)
    payload = TransferCreate(
        source_account_id=sample_account.id,
        destination_account_id=usd_account.id,
        amount=Decimal("100.00"),
        currency="INR",
    )
    with pytest.raises(CurrencyMismatchError) as exc:
        service.record_transfer(sample_user.id, payload)
    assert "Direct transfers between different currencies are not permitted" in exc.value.message


def test_transfer_cross_user_fails(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify transfer raises NotFoundError when referencing an account of another user."""
    other_user = User(id="other-user-999", email="other@domain.dev", name="Other User")
    db_session.add(other_user)
    db_session.flush()

    other_account = FinancialAccount(
        user_id=other_user.id,
        name="Other User Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
    )
    db_session.add(other_account)
    db_session.flush()

    service = TransactionService(db_session)
    payload = TransferCreate(
        source_account_id=sample_account.id,
        destination_account_id=other_account.id,
        amount=Decimal("100.00"),
        currency="INR",
    )
    with pytest.raises(NotFoundError):
        service.record_transfer(sample_user.id, payload)


def test_idempotency_prevents_duplicate_transactions(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify that submitting with the same idempotency key returns the cached transaction."""
    service = TransactionService(db_session)
    key = f"idem-key-{uuid.uuid4()}"

    payload = TransactionCreate(
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("120.00"),
        currency="INR",
        description="Online subscription",
        account_id=sample_account.id,
        idempotency_key=key,
    )
    tx1 = service.record_transaction(sample_user.id, payload)
    tx2 = service.record_transaction(sample_user.id, payload)

    assert tx1.id == tx2.id
    assert tx1.amount == tx2.amount


def test_reversal_creates_compensating_transaction(
    db_session: Session,
    sample_user: User,
    sample_account: FinancialAccount,
    sample_category: Category,
) -> None:
    """Verify reversing a transaction creates compensating offsetting ledger entries."""
    service = TransactionService(db_session)
    payload = TransactionCreate(
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("300.00"),
        currency="INR",
        description="Mistaken purchase",
        category_id=sample_category.id,
        account_id=sample_account.id,
    )
    orig_tx = service.record_transaction(sample_user.id, payload)

    # Reverse transaction
    reversal_tx = service.reverse_transaction(
        sample_user.id, orig_tx.id, reason="Customer refunded"
    )
    assert reversal_tx.id is not None
    assert reversal_tx.id != orig_tx.id
    assert reversal_tx.amount == Decimal("300.00")
    # Original had CREDIT on sample_account; compensating transaction must have DEBIT
    assert len(reversal_tx.entries) == 1
    assert reversal_tx.entries[0].entry_type == EntryType.DEBIT
    assert reversal_tx.entries[0].amount == Decimal("300.00")
    assert reversal_tx.entries[0].account_id == sample_account.id

    # Trying to reverse again should fail
    with pytest.raises(ValidationError) as exc:
        service.reverse_transaction(sample_user.id, orig_tx.id)
    assert "already been reversed" in exc.value.message


def test_record_transaction_invalid_amount_fails(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify that non-positive transaction amount raises ValidationError."""
    service = TransactionService(db_session)
    with pytest.raises((ValidationError, PydanticValidationError)):
        payload = TransactionCreate(
            transaction_type=TransactionType.EXPENSE,
            amount=Decimal("0.00"),
            currency="INR",
            description="Invalid transaction",
            account_id=sample_account.id,
        )
        service.record_transaction(sample_user.id, payload)


def test_record_transaction_foreign_category_fails(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify that referencing another user's category raises NotFoundError."""
    other_user = User(id="other-user-888", email="other2@domain.dev", name="Other 2")
    db_session.add(other_user)
    foreign_cat = Category(
        user_id=other_user.id,
        name="Private Category",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(foreign_cat)
    db_session.flush()

    service = TransactionService(db_session)
    payload = TransactionCreate(
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("50.00"),
        currency="INR",
        description="Test private category",
        category_id=foreign_cat.id,
        account_id=sample_account.id,
    )
    with pytest.raises(NotFoundError):
        service.record_transaction(sample_user.id, payload)
