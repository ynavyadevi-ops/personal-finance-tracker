"""Domain service implementing business rules for Transactions, Transfers, and Reversals."""

from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import (
    CurrencyMismatchError,
    NotFoundError,
    ValidationError,
)
from src.core.logging import logger
from src.core.money import to_decimal
from src.db.models.category import CategoryType
from src.db.models.transaction import EntryType, TransactionType
from src.repositories.account_repo import AccountRepository
from src.repositories.category_repo import CategoryRepository
from src.repositories.transaction_repo import TransactionRepository
from src.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransferCreate,
)
from src.services.ledger_service import LedgerService


class TransactionService:
    """Orchestrates financial transaction processing, double-entry validation, and transfers."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.tx_repo = TransactionRepository(session)
        self.ledger_service = LedgerService(session)

    def record_transaction(self, user_id: str, payload: TransactionCreate) -> TransactionRead:
        """Route and execute a transaction according to its transaction_type."""
        if payload.transaction_type == TransactionType.INCOME:
            return self.record_income(user_id=user_id, payload=payload)
        elif payload.transaction_type == TransactionType.EXPENSE:
            return self.record_expense(user_id=user_id, payload=payload)
        raise ValidationError(
            f"Unsupported transaction type '{payload.transaction_type}'. Use record_transfer for transfers."
        )

    def record_income(self, user_id: str, payload: TransactionCreate) -> TransactionRead:
        """Record an income business event (Debit to depository/asset account)."""
        amt = to_decimal(payload.amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Income transaction amount must be strictly positive.")

        # 1. Validate account ownership
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        # 2. Validate category ownership and type if specified
        if payload.category_id:
            category = self.category_repo.get_user_accessible_category(
                category_id=payload.category_id, user_id=user_id
            )
            if not category:
                raise NotFoundError(f"Category with ID '{payload.category_id}' was not found.")
            if category.category_type != CategoryType.INCOME:
                raise ValidationError(
                    f"Category '{category.name}' is an {category.category_type.value} category, not an INCOME category."
                )

        # 3. Idempotency protection
        if payload.idempotency_key:
            existing_tx = self.tx_repo.find_by_idempotency_key(
                user_id=user_id, idempotency_key=payload.idempotency_key
            )
            if existing_tx:
                logger.info(f"Idempotent transaction replay returned: {existing_tx.id}")
                return TransactionRead.model_validate(existing_tx)

        # 4. Atomic transaction processing
        tags_str = payload.tags
        if payload.idempotency_key:
            idemp_tag = f"idempotency:{payload.idempotency_key}"
            tags_str = f"{tags_str},{idemp_tag}" if tags_str else idemp_tag

        try:
            tx = self.tx_repo.create_transaction(
                user_id=user_id,
                transaction_date=payload.transaction_date,
                transaction_type=TransactionType.INCOME,
                description=payload.description,
                amount=amt,
                currency=account.currency,
                notes=payload.notes,
                tags=tags_str,
            )
            # In double-entry convention, debit increases asset account
            self.tx_repo.create_entry(
                transaction_id=tx.id,
                account_id=account.id,
                category_id=payload.category_id,
                entry_type=EntryType.DEBIT,
                amount=amt,
                currency=account.currency,
                notes=payload.notes,
            )
            self.session.commit()
            self.session.refresh(tx)
            logger.info(f"Income transaction recorded successfully: {tx.id}")
            return TransactionRead.model_validate(tx)
        except Exception:
            self.session.rollback()
            raise

    def record_expense(self, user_id: str, payload: TransactionCreate) -> TransactionRead:
        """Record an expense business event (Credit to paying asset account or credit card)."""
        amt = to_decimal(payload.amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Expense transaction amount must be strictly positive.")

        # 1. Validate account ownership
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        # 2. Validate category ownership and type if specified
        if payload.category_id:
            category = self.category_repo.get_user_accessible_category(
                category_id=payload.category_id, user_id=user_id
            )
            if not category:
                raise NotFoundError(f"Category with ID '{payload.category_id}' was not found.")
            if category.category_type != CategoryType.EXPENSE:
                raise ValidationError(
                    f"Category '{category.name}' is an {category.category_type.value} category, not an EXPENSE category."
                )

        # 3. Idempotency protection
        if payload.idempotency_key:
            existing_tx = self.tx_repo.find_by_idempotency_key(
                user_id=user_id, idempotency_key=payload.idempotency_key
            )
            if existing_tx:
                logger.info(f"Idempotent transaction replay returned: {existing_tx.id}")
                return TransactionRead.model_validate(existing_tx)

        # 4. Atomic transaction processing
        tags_str = payload.tags
        if payload.idempotency_key:
            idemp_tag = f"idempotency:{payload.idempotency_key}"
            tags_str = f"{tags_str},{idemp_tag}" if tags_str else idemp_tag

        try:
            tx = self.tx_repo.create_transaction(
                user_id=user_id,
                transaction_date=payload.transaction_date,
                transaction_type=TransactionType.EXPENSE,
                description=payload.description,
                amount=amt,
                currency=account.currency,
                notes=payload.notes,
                tags=tags_str,
            )
            # In double-entry convention, credit reduces asset account (or increases credit card liability)
            self.tx_repo.create_entry(
                transaction_id=tx.id,
                account_id=account.id,
                category_id=payload.category_id,
                entry_type=EntryType.CREDIT,
                amount=amt,
                currency=account.currency,
                notes=payload.notes,
            )
            self.session.commit()
            self.session.refresh(tx)
            logger.info(f"Expense transaction recorded successfully: {tx.id}")
            return TransactionRead.model_validate(tx)
        except Exception:
            self.session.rollback()
            raise

    def record_transfer(self, user_id: str, payload: TransferCreate) -> TransactionRead:
        """Record an atomic inter-account transfer with strict double-entry balancing.

        - Decrements source account (Credit).
        - Increments destination account (Debit).
        - Mandatory check: Total Debits == Total Credits == Amount.
        - Enforces currency compatibility.
        """
        amt = to_decimal(payload.amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Transfer amount must be strictly positive.")

        if payload.source_account_id == payload.destination_account_id:
            raise ValidationError(
                "Source and destination accounts for a transfer must be distinct."
            )

        # 1. Validate ownership of both accounts
        source_account = self.account_repo.get_by_id(
            account_id=payload.source_account_id, user_id=user_id
        )
        if not source_account:
            raise NotFoundError(
                f"Source account with ID '{payload.source_account_id}' was not found for this user."
            )

        dest_account = self.account_repo.get_by_id(
            account_id=payload.destination_account_id, user_id=user_id
        )
        if not dest_account:
            raise NotFoundError(
                f"Destination account with ID '{payload.destination_account_id}' was not found for this user."
            )

        # 2. Currency compatibility enforcement
        if source_account.currency != dest_account.currency:
            raise CurrencyMismatchError(
                f"Transfer currency mismatch: source is '{source_account.currency}' but destination is "
                f"'{dest_account.currency}'. Direct transfers between different currencies are not permitted."
            )

        # 3. Idempotency protection
        if payload.idempotency_key:
            existing_tx = self.tx_repo.find_by_idempotency_key(
                user_id=user_id, idempotency_key=payload.idempotency_key
            )
            if existing_tx:
                logger.info(f"Idempotent transfer replay returned: {existing_tx.id}")
                return TransactionRead.model_validate(existing_tx)

        tags_str = payload.tags
        if payload.idempotency_key:
            idemp_tag = f"idempotency:{payload.idempotency_key}"
            tags_str = f"{tags_str},{idemp_tag}" if tags_str else idemp_tag

        # 4. Atomic double-entry transfer commit
        try:
            tx = self.tx_repo.create_transaction(
                user_id=user_id,
                transaction_date=payload.transaction_date,
                transaction_type=TransactionType.TRANSFER,
                description=payload.description,
                amount=amt,
                currency=source_account.currency,
                notes=payload.notes,
                tags=tags_str,
            )
            # Credit source (outflow)
            entry_src = self.tx_repo.create_entry(
                transaction_id=tx.id,
                account_id=source_account.id,
                entry_type=EntryType.CREDIT,
                amount=amt,
                currency=source_account.currency,
                notes=f"Transfer to {dest_account.name}",
            )
            # Debit destination (inflow)
            entry_dst = self.tx_repo.create_entry(
                transaction_id=tx.id,
                account_id=dest_account.id,
                entry_type=EntryType.DEBIT,
                amount=amt,
                currency=dest_account.currency,
                notes=f"Transfer from {source_account.name}",
            )

            # Strict double-entry ledger validation
            self.ledger_service.validate_balanced_entries([entry_src, entry_dst])

            self.session.commit()
            self.session.refresh(tx)
            logger.info(
                f"Transfer executed: {tx.id} from {source_account.name} to {dest_account.name} (₹{amt})"
            )
            return TransactionRead.model_validate(tx)
        except Exception:
            self.session.rollback()
            raise

    def reverse_transaction(
        self, user_id: str, transaction_id: str, reason: str = "User requested reversal"
    ) -> TransactionRead:
        """Create a compensating reversal transaction preserving full historical ledger audit."""
        orig_tx = self.tx_repo.get_by_id(transaction_id=transaction_id, user_id=user_id)
        if not orig_tx:
            raise NotFoundError(f"Transaction with ID '{transaction_id}' was not found.")

        if orig_tx.tags and "reversed_by:" in orig_tx.tags:
            raise ValidationError(f"Transaction '{transaction_id}' has already been reversed.")

        try:
            desc = f"Reversal of {orig_tx.description}: {reason}"
            reversal_tags = f"reversal_of:{orig_tx.id}"

            reversal_tx = self.tx_repo.create_transaction(
                user_id=user_id,
                transaction_date=orig_tx.transaction_date,
                transaction_type=orig_tx.transaction_type,
                description=desc,
                amount=orig_tx.amount,
                currency=orig_tx.currency,
                notes=f"Compensating reversal for {orig_tx.id}",
                tags=reversal_tags,
            )

            reversal_entries = []
            for orig_entry in orig_tx.entries:
                # Invert the entry direction
                inverted_type = (
                    EntryType.CREDIT
                    if orig_entry.entry_type == EntryType.DEBIT
                    else EntryType.DEBIT
                )
                rev_entry = self.tx_repo.create_entry(
                    transaction_id=reversal_tx.id,
                    account_id=orig_entry.account_id,
                    category_id=orig_entry.category_id,
                    entry_type=inverted_type,
                    amount=orig_entry.amount,
                    currency=orig_entry.currency,
                    notes=f"Reversal of entry {orig_entry.id}",
                )
                reversal_entries.append(rev_entry)

            if orig_tx.transaction_type == TransactionType.TRANSFER:
                self.ledger_service.validate_balanced_entries(reversal_entries)

            # Mark original as reversed
            existing_tags = orig_tx.tags or ""
            orig_tx.tags = (
                f"{existing_tags},reversed_by:{reversal_tx.id}"
                if existing_tags
                else f"reversed_by:{reversal_tx.id}"
            )

            self.session.commit()
            self.session.refresh(reversal_tx)
            logger.info(
                f"Transaction {orig_tx.id} reversed via compensating transaction {reversal_tx.id}"
            )
            return TransactionRead.model_validate(reversal_tx)
        except Exception:
            self.session.rollback()
            raise

    def get_transaction(self, transaction_id: str, user_id: str) -> TransactionRead:
        """Fetch a specific transaction with entries, verifying ownership."""
        tx = self.tx_repo.get_by_id(transaction_id=transaction_id, user_id=user_id)
        if not tx:
            raise NotFoundError(f"Transaction with ID '{transaction_id}' was not found.")
        return TransactionRead.model_validate(tx)

    def list_transactions(
        self,
        user_id: str,
        account_id: str | None = None,
        category_id: str | None = None,
        transaction_type: TransactionType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TransactionRead]:
        """Query user transactions."""
        txs = self.tx_repo.list_by_user(
            user_id=user_id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            limit=limit,
            offset=offset,
        )
        return [TransactionRead.model_validate(tx) for tx in txs]
