"""Domain service implementing business rules for Loans, Fixed-Rate Amortization, and Debt Payments."""

import calendar
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import logger
from src.core.money import to_decimal
from src.db.models.loan import LoanPaymentSchedule
from src.repositories.account_repo import AccountRepository
from src.repositories.loan_repo import LoanRepository
from src.schemas.loan import (
    AmortizationScheduleItem,
    LoanCreate,
    LoanPaymentScheduleRead,
    LoanRead,
)


class LoanService:
    """Orchestrates loan obligations, amortization schedules, and principal/interest repayments."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.loan_repo = LoanRepository(session)
        self.account_repo = AccountRepository(session)

    @staticmethod
    def _advance_months(start_date: date, months_to_add: int) -> date:
        """Advance a calendar date by n months, adjusting for varying month lengths."""
        year = start_date.year + (start_date.month + months_to_add - 1) // 12
        month = (start_date.month + months_to_add - 1) % 12 + 1
        _, max_day = calendar.monthrange(year, month)
        day = min(start_date.day, max_day)
        return date(year, month, day)

    @classmethod
    def calculate_fixed_amortization(
        cls, principal: Decimal, annual_rate: Decimal, term_months: int, start_date: date
    ) -> list[AmortizationScheduleItem]:
        """Generate a complete fixed-rate amortization schedule using Decimal arithmetic.

        Formula:
            EMI = P * (r * (1 + r)^n) / ((1 + r)^n - 1)
            where r = annual_rate / 1200
        """
        p = to_decimal(principal)
        if p <= Decimal("0.00"):
            raise ValidationError("Principal amount must be strictly positive.")
        if term_months <= 0:
            raise ValidationError("Term in months must be greater than zero.")
        if annual_rate < Decimal("0.00"):
            raise ValidationError("Interest rate cannot be negative.")

        schedule_items: list[AmortizationScheduleItem] = []
        remaining_balance = p

        # Handle 0% interest case
        if annual_rate == Decimal("0.00"):
            base_monthly = to_decimal(p / Decimal(term_months))
            for i in range(1, term_months + 1):
                due_date = cls._advance_months(start_date, i)
                if i == term_months:
                    principal_comp = remaining_balance
                    remaining_balance = Decimal("0.00")
                else:
                    principal_comp = base_monthly
                    remaining_balance -= principal_comp

                schedule_items.append(
                    AmortizationScheduleItem(
                        payment_number=i,
                        due_date=due_date,
                        principal_component=principal_comp,
                        interest_component=Decimal("0.00"),
                        total_payment=principal_comp,
                        remaining_balance=remaining_balance,
                    )
                )
            return schedule_items

        # Fixed rate compound amortization calculation
        monthly_rate = annual_rate / Decimal("1200.00")
        factor = (Decimal("1.00") + monthly_rate) ** term_months
        emi = to_decimal(p * (monthly_rate * factor) / (factor - Decimal("1.00")))

        for i in range(1, term_months + 1):
            due_date = cls._advance_months(start_date, i)
            interest_comp = to_decimal(remaining_balance * monthly_rate)

            if i == term_months:
                # Final instalment cleans up any remaining rounding fractions
                principal_comp = remaining_balance
                total_payment = principal_comp + interest_comp
                remaining_balance = Decimal("0.00")
            else:
                principal_comp = emi - interest_comp
                total_payment = emi
                remaining_balance = to_decimal(remaining_balance - principal_comp)

            schedule_items.append(
                AmortizationScheduleItem(
                    payment_number=i,
                    due_date=due_date,
                    principal_component=principal_comp,
                    interest_component=interest_comp,
                    total_payment=total_payment,
                    remaining_balance=remaining_balance,
                )
            )

        return schedule_items

    def create_loan(self, user_id: str, payload: LoanCreate) -> LoanRead:
        """Record a loan obligation and persist its initial amortization schedule."""
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        principal = to_decimal(payload.principal_amount)
        rate = to_decimal(payload.interest_rate)

        # 1. Calculate amortization schedule
        amortization = self.calculate_fixed_amortization(
            principal=principal,
            annual_rate=rate,
            term_months=payload.term_months,
            start_date=payload.start_date,
        )
        monthly_emi = amortization[0].total_payment if amortization else Decimal("0.00")

        # 2. Persist Loan record
        loan = self.loan_repo.create_loan(
            user_id=user_id,
            account_id=payload.account_id,
            lender_name=payload.lender_name,
            principal_amount=principal,
            interest_rate=rate,
            interest_type=payload.interest_type,
            term_months=payload.term_months,
            minimum_monthly_payment=monthly_emi,
            start_date=payload.start_date,
            due_date=payload.due_date or amortization[-1].due_date,
            notes=payload.notes,
        )

        # 3. Persist amortization schedule instalments
        schedules = [
            LoanPaymentSchedule(
                loan_id=loan.id,
                payment_number=item.payment_number,
                due_date=item.due_date,
                principal_component=item.principal_component,
                interest_component=item.interest_component,
                total_payment=item.total_payment,
                remaining_balance=item.remaining_balance,
                is_paid=False,
            )
            for item in amortization
        ]
        self.loan_repo.create_schedule_entries(schedules)

        self.session.commit()
        self.session.refresh(loan)
        logger.info(f"Loan liability recorded: {loan.id} ({loan.lender_name}) for ₹{principal}")
        return LoanRead.model_validate(loan)

    def record_payment(
        self,
        user_id: str,
        loan_id: str,
        payment_number: int,
        transaction_id: str | None = None,
    ) -> LoanPaymentScheduleRead:
        """Mark a loan instalment as paid, adjusting remaining balance.

        Principal repayment reduces liability; interest is an expense.
        """
        loan = self.loan_repo.get_by_id(loan_id=loan_id, user_id=user_id)
        if not loan:
            raise NotFoundError(f"Loan with ID '{loan_id}' was not found.")

        schedule = self.loan_repo.get_schedule_entry(loan_id=loan_id, payment_number=payment_number)
        if not schedule:
            raise NotFoundError(
                f"Schedule instalment #{payment_number} for loan '{loan_id}' was not found."
            )

        if schedule.is_paid:
            raise ValidationError(
                f"Instalment #{payment_number} for loan '{loan.lender_name}' has already been recorded as paid."
            )

        # 1. Update loan remaining balance
        loan.remaining_balance = to_decimal(loan.remaining_balance - schedule.principal_component)
        if loan.remaining_balance <= Decimal("0.00"):
            loan.remaining_balance = Decimal("0.00")
            loan.is_settled = True

        # 2. Mark schedule as paid
        schedule.is_paid = True
        schedule.paid_date = date.today()
        schedule.transaction_id = transaction_id

        self.session.commit()
        self.session.refresh(schedule)
        self.session.refresh(loan)
        logger.info(
            f"Loan payment #{payment_number} registered for {loan.lender_name} "
            f"(Principal: ₹{schedule.principal_component}, Remaining: ₹{loan.remaining_balance})"
        )
        return LoanPaymentScheduleRead.model_validate(schedule)

    def get_loan(self, user_id: str, loan_id: str) -> LoanRead:
        """Fetch a specific loan obligation."""
        loan = self.loan_repo.get_by_id(loan_id=loan_id, user_id=user_id)
        if not loan:
            raise NotFoundError(f"Loan with ID '{loan_id}' was not found.")
        return LoanRead.model_validate(loan)

    def list_loans(self, user_id: str) -> list[LoanRead]:
        """Fetch all loan liabilities for a user."""
        loans = self.loan_repo.list_by_user(user_id=user_id)
        return [LoanRead.model_validate(loan) for loan in loans]
