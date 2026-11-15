"""Repository layer for Transactions and double-entry TransactionEntries."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models.account import FinancialAccount
from src.db.models.transaction import EntryType, Transaction, TransactionEntry, TransactionType


class TransactionRepository:
    """Encapsulates database operations for Transaction and TransactionEntry entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_transaction(
        self,
        user_id: str,
        transaction_date: date,
        transaction_type: TransactionType,
        description: str,
        amount: Decimal,
        currency: str = "INR",
        notes: str | None = None,
        tags: str | None = None,
        recurring_rule_id: str | None = None,
    ) -> Transaction:
        """Create a new parent transaction event."""
        tx = Transaction(
            user_id=user_id,
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            description=description,
            amount=amount,
            currency=currency,
            notes=notes,
            tags=tags,
            recurring_rule_id=recurring_rule_id,
        )
        self.session.add(tx)
        self.session.flush()
        return tx

    def create_entry(
        self,
        transaction_id: str,
        account_id: str,
        entry_type: EntryType,
        amount: Decimal,
        currency: str = "INR",
        category_id: str | None = None,
        notes: str | None = None,
    ) -> TransactionEntry:
        """Create and associate an individual double-entry ledger line."""
        entry = TransactionEntry(
            transaction_id=transaction_id,
            account_id=account_id,
            category_id=category_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            notes=notes,
        )
        self.session.add(entry)
        self.session.flush()
        return entry

    def get_by_id(self, transaction_id: str, user_id: str) -> Transaction | None:
        """Fetch a transaction by ID, verifying tenant user ownership."""
        stmt = select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(
        self,
        user_id: str,
        account_id: str | None = None,
        category_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        transaction_type: TransactionType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Query user transactions with optional filtering and pagination."""
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)

        if account_id:
            stmt = stmt.join(Transaction.entries).where(TransactionEntry.account_id == account_id)
        if category_id:
            stmt = stmt.join(Transaction.entries).where(TransactionEntry.category_id == category_id)

        stmt = stmt.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().unique().all())

    def get_entries_by_account(
        self, account_id: str, user_id: str | None = None
    ) -> list[TransactionEntry]:
        """Fetch all posted ledger entries associated with a financial account."""
        stmt = select(TransactionEntry).join(TransactionEntry.account)
        stmt = stmt.where(TransactionEntry.account_id == account_id)
        if user_id:
            stmt = stmt.where(FinancialAccount.user_id == user_id)
        stmt = stmt.order_by(TransactionEntry.created_at.asc())
        return list(self.session.execute(stmt).scalars().all())

    def find_by_idempotency_key(self, user_id: str, idempotency_key: str) -> Transaction | None:
        """Locate an existing transaction tagged with a specific idempotency key."""
        marker = f"idempotency:{idempotency_key}"
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.tags.contains(marker),
        )
        return self.session.execute(stmt).scalars().first()

    def count_by_user(self, user_id: str) -> int:
        """Total transactions count for user."""
        stmt = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        return int(self.session.execute(stmt).scalar() or 0)
