"""Unit tests for LedgerService: double-entry validation, account balance, and reconciliation."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.db.models.account import AccountType, FinancialAccount
from src.db.models.transaction import EntryType, Transaction, TransactionEntry, TransactionType
from src.db.models.user import User
from src.services.ledger_service import LedgerService


def test_validate_balanced_entries_success(db_session: Session) -> None:
    """Verify that entries where debits == credits pass validation."""
    service = LedgerService(db_session)
    entries = [
        TransactionEntry(
            id=str(uuid.uuid4()),
            account_id="acc-1",
            entry_type=EntryType.DEBIT,
            amount=Decimal("1500.00"),
        ),
        TransactionEntry(
            id=str(uuid.uuid4()),
            account_id="acc-2",
            entry_type=EntryType.CREDIT,
            amount=Decimal("1500.00"),
        ),
    ]
    # Should not raise
    service.validate_balanced_entries(entries)


def test_validate_balanced_entries_empty_fails(db_session: Session) -> None:
    """Verify that empty entries list raises ValidationError."""
    service = LedgerService(db_session)
    with pytest.raises(ValidationError) as exc:
        service.validate_balanced_entries([])
    assert "at least one" in exc.value.message


def test_validate_balanced_entries_unbalanced_fails(db_session: Session) -> None:
    """Verify that unbalanced entries (debits != credits) raise ValidationError."""
    service = LedgerService(db_session)
    entries = [
        TransactionEntry(
            id=str(uuid.uuid4()),
            account_id="acc-1",
            entry_type=EntryType.DEBIT,
            amount=Decimal("1500.00"),
        ),
        TransactionEntry(
            id=str(uuid.uuid4()),
            account_id="acc-2",
            entry_type=EntryType.CREDIT,
            amount=Decimal("1400.00"),
        ),
    ]
    with pytest.raises(ValidationError) as exc:
        service.validate_balanced_entries(entries)
    assert "Total debits" in exc.value.message


def test_validate_balanced_entries_non_positive_fails(db_session: Session) -> None:
    """Verify that non-positive amount raises ValidationError."""
    service = LedgerService(db_session)
    entries = [
        TransactionEntry(
            id=str(uuid.uuid4()),
            account_id="acc-1",
            entry_type=EntryType.DEBIT,
            amount=Decimal("0.00"),
        ),
        TransactionEntry(
            id=str(uuid.uuid4()),
            account_id="acc-2",
            entry_type=EntryType.CREDIT,
            amount=Decimal("0.00"),
        ),
    ]
    with pytest.raises(ValidationError) as exc:
        service.validate_balanced_entries(entries)
    assert "must be strictly positive" in exc.value.message


def test_calculate_account_balance_asset_account(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify asset account balance calculation: opening + debits - credits."""
    service = LedgerService(db_session)

    # Initial opening balance is 2500.50
    bal_initial = service.calculate_account_balance(sample_user.id, sample_account.id)
    assert bal_initial == Decimal("2500.50")

    # Add a DEBIT entry (+500.00)
    tx = Transaction(
        id=str(uuid.uuid4()),
        user_id=sample_user.id,
        transaction_date=date(2026, 11, 1),
        transaction_type=TransactionType.INCOME,
        amount=Decimal("500.00"),
        currency="INR",
        description="Bonus",
    )
    db_session.add(tx)
    entry_debit = TransactionEntry(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        account_id=sample_account.id,
        entry_type=EntryType.DEBIT,
        amount=Decimal("500.00"),
    )
    db_session.add(entry_debit)

    # Add a CREDIT entry (-200.00)
    tx2 = Transaction(
        id=str(uuid.uuid4()),
        user_id=sample_user.id,
        transaction_date=date(2026, 11, 2),
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("200.00"),
        currency="INR",
        description="Groceries",
    )
    db_session.add(tx2)
    entry_credit = TransactionEntry(
        id=str(uuid.uuid4()),
        transaction_id=tx2.id,
        account_id=sample_account.id,
        entry_type=EntryType.CREDIT,
        amount=Decimal("200.00"),
    )
    db_session.add(entry_credit)
    db_session.flush()

    bal_updated = service.calculate_account_balance(sample_user.id, sample_account.id)
    # 2500.50 + 500.00 - 200.00 = 2800.50
    assert bal_updated == Decimal("2800.50")


def test_calculate_account_balance_liability_account(
    db_session: Session, sample_user: User
) -> None:
    """Verify liability account balance calculation: opening + credits - debits."""
    service = LedgerService(db_session)

    credit_card = FinancialAccount(
        user_id=sample_user.id,
        name="Visa Credit Card",
        account_type=AccountType.CREDIT_CARD,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(credit_card)
    db_session.flush()

    # Initial opening balance is 1000.00
    bal_initial = service.calculate_account_balance(sample_user.id, credit_card.id)
    assert bal_initial == Decimal("1000.00")

    # Add a CREDIT entry (increases liability +400.00)
    tx = Transaction(
        id=str(uuid.uuid4()),
        user_id=sample_user.id,
        transaction_date=date(2026, 11, 1),
        transaction_type=TransactionType.EXPENSE,
        amount=Decimal("400.00"),
        currency="INR",
        description="Electronics purchase",
    )
    db_session.add(tx)
    entry_credit = TransactionEntry(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        account_id=credit_card.id,
        entry_type=EntryType.CREDIT,
        amount=Decimal("400.00"),
    )
    db_session.add(entry_credit)

    # Add a DEBIT entry (payment to card -300.00)
    tx2 = Transaction(
        id=str(uuid.uuid4()),
        user_id=sample_user.id,
        transaction_date=date(2026, 11, 2),
        transaction_type=TransactionType.TRANSFER,
        amount=Decimal("300.00"),
        currency="INR",
        description="Card bill payment",
    )
    db_session.add(tx2)
    entry_debit = TransactionEntry(
        id=str(uuid.uuid4()),
        transaction_id=tx2.id,
        account_id=credit_card.id,
        entry_type=EntryType.DEBIT,
        amount=Decimal("300.00"),
    )
    db_session.add(entry_debit)
    db_session.flush()

    bal_updated = service.calculate_account_balance(sample_user.id, credit_card.id)
    # 1000.00 + 400.00 - 300.00 = 1100.00
    assert bal_updated == Decimal("1100.00")


def test_reconcile_account_matching_and_discrepancy(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify account balance reconciliation against expected statement balance."""
    service = LedgerService(db_session)

    # Reconcile matching balance
    recon = service.reconcile_account(
        user_id=sample_user.id,
        account_id=sample_account.id,
        expected_balance=Decimal("2500.50"),
    )
    assert recon.is_reconciled is True
    assert recon.discrepancy == Decimal("0.00")
    assert recon.current_balance == Decimal("2500.50")

    # Reconcile discrepant balance
    recon_diff = service.reconcile_account(
        user_id=sample_user.id,
        account_id=sample_account.id,
        expected_balance=Decimal("2600.00"),
    )
    assert recon_diff.is_reconciled is False
    assert recon_diff.discrepancy == Decimal("99.50")


def test_reconcile_account_not_found(db_session: Session, sample_user: User) -> None:
    """Verify NotFoundError when reconciling a non-existent account."""
    service = LedgerService(db_session)
    with pytest.raises(NotFoundError):
        service.reconcile_account(
            user_id=sample_user.id,
            account_id="missing-account-id",
            expected_balance=Decimal("100.00"),
        )
