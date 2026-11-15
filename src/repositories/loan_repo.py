"""Repository layer for Loans, Debts, and Payment Schedules."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.loan import InterestType, LoanDebt, LoanPaymentSchedule


class LoanRepository:
    """Encapsulates database operations for LoanDebt and LoanPaymentSchedule entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_loan(
        self,
        user_id: str,
        account_id: str,
        lender_name: str,
        principal_amount: Decimal,
        interest_rate: Decimal,
        interest_type: InterestType,
        term_months: int,
        minimum_monthly_payment: Decimal,
        start_date: date,
        due_date: date | None = None,
        notes: str | None = None,
    ) -> LoanDebt:
        """Create and persist a new loan obligation."""
        loan = LoanDebt(
            user_id=user_id,
            account_id=account_id,
            lender_name=lender_name,
            principal_amount=principal_amount,
            remaining_balance=principal_amount,
            interest_rate=interest_rate,
            interest_type=interest_type,
            term_months=term_months,
            minimum_monthly_payment=minimum_monthly_payment,
            start_date=start_date,
            due_date=due_date,
            is_settled=False,
            notes=notes,
        )
        self.session.add(loan)
        self.session.flush()
        return loan

    def create_schedule_entries(
        self, schedules: list[LoanPaymentSchedule]
    ) -> list[LoanPaymentSchedule]:
        """Persist a batch of payment schedule instalments."""
        self.session.add_all(schedules)
        self.session.flush()
        return schedules

    def get_by_id(self, loan_id: str, user_id: str) -> LoanDebt | None:
        """Fetch a loan liability, scoped to user."""
        stmt = select(LoanDebt).where(LoanDebt.id == loan_id, LoanDebt.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: str) -> list[LoanDebt]:
        """Fetch all loans for a user."""
        stmt = select(LoanDebt).where(LoanDebt.user_id == user_id)
        stmt = stmt.order_by(LoanDebt.is_settled.asc(), LoanDebt.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def get_schedule_entry(self, loan_id: str, payment_number: int) -> LoanPaymentSchedule | None:
        """Fetch a single amortization schedule instalment by number."""
        stmt = select(LoanPaymentSchedule).where(
            LoanPaymentSchedule.loan_id == loan_id,
            LoanPaymentSchedule.payment_number == payment_number,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_schedules(self, loan_id: str) -> list[LoanPaymentSchedule]:
        """Fetch all schedule entries for a loan ordered by payment number."""
        stmt = select(LoanPaymentSchedule).where(LoanPaymentSchedule.loan_id == loan_id)
        stmt = stmt.order_by(LoanPaymentSchedule.payment_number.asc())
        return list(self.session.execute(stmt).scalars().all())

    def update_loan(self, loan: LoanDebt) -> LoanDebt:
        """Flush changes to loan record."""
        self.session.flush()
        return loan

    def update_schedule(self, schedule: LoanPaymentSchedule) -> LoanPaymentSchedule:
        """Flush changes to schedule record."""
        self.session.flush()
        return schedule
