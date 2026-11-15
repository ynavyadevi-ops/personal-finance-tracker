"""Domain service implementing double-entry ledger validation and balance reconciliation."""

from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.core.money import to_decimal
from src.db.models.account import AccountType
from src.db.models.transaction import EntryType, TransactionEntry
from src.repositories.account_repo import AccountRepository
from src.repositories.transaction_repo import TransactionRepository
from src.schemas.transaction import AccountReconciliation


class LedgerService:
    """Orchestrates double-entry ledger invariants, validations, and balance computations."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)
        self.tx_repo = TransactionRepository(session)

    def validate_balanced_entries(self, entries: list[TransactionEntry]) -> None:
        """Validate the core double-entry accounting invariant: Total Debits == Total Credits.

        Raises:
            ValidationError: If total debits do not equal total credits or if any entry has non-positive amount.
        """
        if not entries:
            raise ValidationError("Transaction must contain at least one ledger entry.")

        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")

        for entry in entries:
            amt = to_decimal(entry.amount)
            if amt <= Decimal("0.00"):
                raise ValidationError("Each ledger entry amount must be strictly positive.")

            if entry.entry_type == EntryType.DEBIT:
                total_debits += amt
            elif entry.entry_type == EntryType.CREDIT:
                total_credits += amt

        if total_debits != total_credits:
            raise ValidationError(
                f"Double-entry ledger invariant violation: Total debits (₹{total_debits}) "
                f"must equal total credits (₹{total_credits})."
            )

    def calculate_account_balance(self, user_id: str, account_id: str) -> Decimal:
        """Calculate the deterministic account balance from opening balance and all posted ledger entries.

        Asset accounts (Checking, Savings, Cash, Investment):
            Balance = opening_balance + sum(DEBITS) - sum(CREDITS)
        Liability accounts (Credit Card, Loan):
            Balance = opening_balance + sum(CREDITS) - sum(DEBITS)
            (Where credit card charges are credit entries, and payments are debits).
        """
        account = self.account_repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found.")

        entries = self.tx_repo.get_entries_by_account(account_id=account_id, user_id=user_id)

        total_debits = sum(
            (to_decimal(e.amount) for e in entries if e.entry_type == EntryType.DEBIT),
            Decimal("0.00"),
        )
        total_credits = sum(
            (to_decimal(e.amount) for e in entries if e.entry_type == EntryType.CREDIT),
            Decimal("0.00"),
        )

        if account.account_type in (AccountType.CREDIT_CARD, AccountType.LOAN):
            net_movement = total_credits - total_debits
        else:
            net_movement = total_debits - total_credits

        balance = to_decimal(account.opening_balance) + net_movement
        return to_decimal(balance)

    def reconcile_account(
        self, user_id: str, account_id: str, expected_balance: Decimal | None = None
    ) -> AccountReconciliation:
        """Perform a full reconciliation audit of an account's posted entries and opening balance."""
        account = self.account_repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found.")

        entries = self.tx_repo.get_entries_by_account(account_id=account_id, user_id=user_id)

        total_debits = sum(
            (to_decimal(e.amount) for e in entries if e.entry_type == EntryType.DEBIT),
            Decimal("0.00"),
        )
        total_credits = sum(
            (to_decimal(e.amount) for e in entries if e.entry_type == EntryType.CREDIT),
            Decimal("0.00"),
        )

        if account.account_type in (AccountType.CREDIT_CARD, AccountType.LOAN):
            net_movement = total_credits - total_debits
        else:
            net_movement = total_debits - total_credits

        current_balance = to_decimal(account.opening_balance) + net_movement

        discrepancy = Decimal("0.00")
        is_reconciled = True
        if expected_balance is not None:
            discrepancy = to_decimal(abs(current_balance - to_decimal(expected_balance)))
            is_reconciled = discrepancy == Decimal("0.00")

        return AccountReconciliation(
            account_id=account.id,
            account_name=account.name,
            account_type=account.account_type,
            currency=account.currency,
            opening_balance=to_decimal(account.opening_balance),
            total_debits=to_decimal(total_debits),
            total_credits=to_decimal(total_credits),
            net_movement=to_decimal(net_movement),
            current_balance=to_decimal(current_balance),
            posted_entry_count=len(entries),
            expected_balance=to_decimal(expected_balance) if expected_balance is not None else None,
            discrepancy=discrepancy,
            is_reconciled=is_reconciled,
        )
