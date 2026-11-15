"""Domain service implementing business rules for Recurring Transaction Rules and Schedule Evaluation."""

import calendar
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import (
    CurrencyMismatchError,
    NotFoundError,
    ValidationError,
)
from src.core.logging import logger
from src.core.money import to_decimal
from src.db.models.recurring import Frequency
from src.db.models.transaction import Transaction, TransactionType
from src.repositories.account_repo import AccountRepository
from src.repositories.category_repo import CategoryRepository
from src.repositories.recurring_repo import RecurringRepository
from src.schemas.recurring import RecurringRuleCreate, RecurringRuleRead
from src.schemas.transaction import TransactionCreate, TransactionRead, TransferCreate
from src.services.transaction_service import TransactionService


class RecurringService:
    """Orchestrates recurring bill/income rule evaluation, next-occurrence math, and automated transaction spawning."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.recurring_repo = RecurringRepository(session)
        self.account_repo = AccountRepository(session)
        self.category_repo = CategoryRepository(session)
        self.tx_service = TransactionService(session)

    @staticmethod
    def calculate_next_occurrence(from_date: date, frequency: Frequency, interval: int = 1) -> date:
        """Calculate the subsequent occurrence date for a recurrence rule."""
        if interval <= 0:
            raise ValidationError("Recurrence interval must be strictly positive.")

        if frequency == Frequency.DAILY:
            return from_date + timedelta(days=interval)
        elif frequency == Frequency.WEEKLY:
            return from_date + timedelta(weeks=interval)
        elif frequency == Frequency.BIWEEKLY:
            return from_date + timedelta(weeks=2 * interval)
        elif frequency == Frequency.MONTHLY:
            total_months = from_date.month + interval
            year = from_date.year + (total_months - 1) // 12
            month = (total_months - 1) % 12 + 1
            _, max_day = calendar.monthrange(year, month)
            day = min(from_date.day, max_day)
            return date(year, month, day)
        elif frequency == Frequency.QUARTERLY:
            total_months = from_date.month + (3 * interval)
            year = from_date.year + (total_months - 1) // 12
            month = (total_months - 1) % 12 + 1
            _, max_day = calendar.monthrange(year, month)
            day = min(from_date.day, max_day)
            return date(year, month, day)
        elif frequency == Frequency.YEARLY:
            year = from_date.year + interval
            # Handle Feb 29 leap year rollover
            if from_date.month == 2 and from_date.day == 29 and not calendar.isleap(year):
                return date(year, 2, 28)
            return date(year, from_date.month, from_date.day)

        raise ValidationError(f"Unsupported recurrence frequency: {frequency}")

    def create_rule(self, user_id: str, payload: RecurringRuleCreate) -> RecurringRuleRead:
        """Create and persist a new recurring transaction rule."""
        if payload.end_date and payload.end_date < payload.start_date:
            raise ValidationError("Recurring rule end date cannot be earlier than start date.")

        amt = to_decimal(payload.amount)
        if amt <= Decimal("0.00"):
            raise ValidationError("Recurring transaction amount must be strictly positive.")

        # 1. Validate primary account ownership
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        # 2. Validate destination account for recurring transfers
        if payload.transaction_type == TransactionType.TRANSFER:
            if not payload.destination_account_id:
                raise ValidationError(
                    "Destination account is required for recurring transfer rules."
                )
            if payload.account_id == payload.destination_account_id:
                raise ValidationError("Source and destination accounts must be distinct.")
            dst_acc = self.account_repo.get_by_id(
                account_id=payload.destination_account_id, user_id=user_id
            )
            if not dst_acc:
                raise NotFoundError(
                    f"Destination account with ID '{payload.destination_account_id}' was not found."
                )
            if account.currency != dst_acc.currency:
                raise CurrencyMismatchError(
                    f"Recurring transfer currency mismatch between '{account.currency}' and '{dst_acc.currency}'."
                )

        # 3. Validate category ownership if present
        if payload.category_id:
            cat = self.category_repo.get_user_accessible_category(
                category_id=payload.category_id, user_id=user_id
            )
            if not cat:
                raise NotFoundError(f"Category with ID '{payload.category_id}' was not found.")

        rule = self.recurring_repo.create(
            user_id=user_id,
            account_id=payload.account_id,
            name=payload.name,
            amount=amt,
            currency=account.currency,
            transaction_type=payload.transaction_type,
            frequency=payload.frequency,
            interval=payload.interval,
            start_date=payload.start_date,
            end_date=payload.end_date,
            category_id=payload.category_id,
            destination_account_id=payload.destination_account_id,
            notes=payload.notes,
        )
        self.session.commit()
        self.session.refresh(rule)
        logger.info(
            f"Recurring rule created: {rule.id} ({rule.name}) every {rule.interval} {rule.frequency.value}"
        )
        return RecurringRuleRead.model_validate(rule)

    def list_due_rules(
        self, user_id: str, as_of_date: date | None = None
    ) -> list[RecurringRuleRead]:
        """Fetch active rules that are due for execution as of a specified date."""
        target_date = as_of_date or date.today()
        rules = self.recurring_repo.list_due(as_of_date=target_date, user_id=user_id)
        return [RecurringRuleRead.model_validate(r) for r in rules]

    def execute_due_rule(
        self, user_id: str, rule_id: str, execution_date: date | None = None
    ) -> TransactionRead:
        """Execute a due recurring rule, spawning a real validated transaction and advancing schedule.

        Includes duplicate occurrence prevention.
        """
        rule = self.recurring_repo.get_by_id(rule_id=rule_id, user_id=user_id)
        if not rule:
            raise NotFoundError(f"Recurring rule with ID '{rule_id}' was not found.")

        if not rule.is_active:
            raise ValidationError(f"Recurring rule '{rule.name}' is paused and cannot be executed.")

        exec_date = execution_date or rule.next_occurrence

        # 1. Duplicate occurrence prevention
        existing = self.recurring_repo.find_existing_execution(
            rule_id=rule.id, execution_date=exec_date
        )
        if existing:
            raise ValidationError(
                f"Recurring rule '{rule.name}' has already spawned a transaction for date {exec_date}."
            )

        # 2. Spawn transaction using TransactionService (ensuring all ledger invariants apply)
        tx_desc = f"{rule.name} (Recurring)"
        if rule.transaction_type == TransactionType.INCOME:
            tx_read = self.tx_service.record_income(
                user_id=user_id,
                payload=TransactionCreate(
                    account_id=rule.account_id,
                    category_id=rule.category_id,
                    amount=rule.amount,
                    description=tx_desc,
                    transaction_date=exec_date,
                    currency=rule.currency,
                    notes=f"Auto-spawned from recurring rule {rule.id}",
                ),
            )
        elif rule.transaction_type == TransactionType.EXPENSE:
            tx_read = self.tx_service.record_expense(
                user_id=user_id,
                payload=TransactionCreate(
                    account_id=rule.account_id,
                    category_id=rule.category_id,
                    amount=rule.amount,
                    description=tx_desc,
                    transaction_date=exec_date,
                    currency=rule.currency,
                    notes=f"Auto-spawned from recurring rule {rule.id}",
                ),
            )
        elif rule.transaction_type == TransactionType.TRANSFER:
            if not rule.destination_account_id:
                raise ValidationError("Recurring transfer rule lacks a destination account.")
            tx_read = self.tx_service.record_transfer(
                user_id=user_id,
                payload=TransferCreate(
                    source_account_id=rule.account_id,
                    destination_account_id=rule.destination_account_id,
                    amount=rule.amount,
                    description=tx_desc,
                    transaction_date=exec_date,
                    notes=f"Auto-spawned from recurring rule {rule.id}",
                ),
            )
        else:
            raise ValidationError(
                f"Unsupported transaction type for recurring rule: {rule.transaction_type}"
            )

        # 3. Associate transaction with recurring rule
        tx_entity = self.session.get(Transaction, tx_read.id)
        if tx_entity:
            tx_entity.recurring_rule_id = rule.id

        # 4. Advance next occurrence
        next_date = self.calculate_next_occurrence(
            from_date=rule.next_occurrence, frequency=rule.frequency, interval=rule.interval
        )
        rule.next_occurrence = next_date

        # 5. Check end_date expiration
        if rule.end_date and rule.next_occurrence > rule.end_date:
            rule.is_active = False
            logger.info(
                f"Recurring rule '{rule.name}' completed and set to inactive (reached {rule.end_date})"
            )

        self.session.commit()
        self.session.refresh(rule)
        logger.info(
            f"Recurring rule '{rule.name}' executed -> Tx {tx_read.id}. Next: {rule.next_occurrence}"
        )
        return tx_read

    def pause_rule(self, user_id: str, rule_id: str) -> RecurringRuleRead:
        """Pause a recurring schedule."""
        rule = self.recurring_repo.get_by_id(rule_id=rule_id, user_id=user_id)
        if not rule:
            raise NotFoundError(f"Recurring rule with ID '{rule_id}' was not found.")
        rule.is_active = False
        self.session.commit()
        self.session.refresh(rule)
        logger.info(f"Recurring rule paused: {rule.id}")
        return RecurringRuleRead.model_validate(rule)

    def resume_rule(self, user_id: str, rule_id: str) -> RecurringRuleRead:
        """Resume an active recurring schedule."""
        rule = self.recurring_repo.get_by_id(rule_id=rule_id, user_id=user_id)
        if not rule:
            raise NotFoundError(f"Recurring rule with ID '{rule_id}' was not found.")
        rule.is_active = True
        self.session.commit()
        self.session.refresh(rule)
        logger.info(f"Recurring rule resumed: {rule.id}")
        return RecurringRuleRead.model_validate(rule)

    def list_rules(self, user_id: str, active_only: bool = False) -> list[RecurringRuleRead]:
        """Fetch all recurring rules for a user."""
        rules = self.recurring_repo.list_by_user(user_id=user_id, active_only=active_only)
        return [RecurringRuleRead.model_validate(r) for r in rules]
