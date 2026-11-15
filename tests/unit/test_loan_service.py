"""Unit tests for LoanService: fixed-rate amortization schedule, repayments, and balance tracking."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

from src.core.exceptions import ValidationError
from src.db.models.account import AccountType, FinancialAccount
from src.db.models.loan import InterestType
from src.db.models.user import User
from src.schemas.loan import LoanCreate
from src.services.loan_service import LoanService


@pytest.fixture
def loan_account(db_session: Session, sample_user: User) -> FinancialAccount:
    """Fixture providing a loan liability account."""
    acc = FinancialAccount(
        user_id=sample_user.id,
        name="Personal Loan Account",
        account_type=AccountType.LOAN,
        currency="INR",
        opening_balance=Decimal("120000.00"),
    )
    db_session.add(acc)
    db_session.flush()
    return acc


def test_calculate_fixed_amortization() -> None:
    """Verify mathematical correctness of fixed-rate amortization schedule."""
    # Principal 120,000, 12% per year (1% monthly), 12 months
    schedule = LoanService.calculate_fixed_amortization(
        principal=Decimal("120000.00"),
        annual_rate=Decimal("12.00"),
        term_months=12,
        start_date=date(2026, 1, 1),
    )

    assert len(schedule) == 12
    # Verify monthly payment consistency (EMI around ~10,661.85)
    emi = schedule[0].total_payment
    assert Decimal("10600.00") < emi < Decimal("10700.00")

    # Sum of principal components must exactly equal 120,000.00
    total_principal = sum((item.principal_component for item in schedule), Decimal("0.00"))
    assert total_principal == Decimal("120000.00")

    # Final remaining balance must be exactly 0.00
    assert schedule[-1].remaining_balance == Decimal("0.00")

    # First month interest: 120,000 * 1% = 1,200.00
    assert schedule[0].interest_component == Decimal("1200.00")


def test_calculate_amortization_zero_interest() -> None:
    """Verify 0% interest loan calculation divides principal evenly."""
    schedule = LoanService.calculate_fixed_amortization(
        principal=Decimal("60000.00"),
        annual_rate=Decimal("0.00"),
        term_months=6,
        start_date=date(2026, 1, 1),
    )
    assert len(schedule) == 6
    for item in schedule:
        assert item.interest_component == Decimal("0.00")
        assert item.principal_component == Decimal("10000.00")
        assert item.total_payment == Decimal("10000.00")
    assert schedule[-1].remaining_balance == Decimal("0.00")


def test_create_loan_with_schedule(
    db_session: Session, sample_user: User, loan_account: FinancialAccount
) -> None:
    """Verify creating a loan creates the loan entity and 12 scheduled payment entries."""
    service = LoanService(db_session)
    payload = LoanCreate(
        account_id=loan_account.id,
        lender_name="HDFC Personal Loan",
        principal_amount=Decimal("120000.00"),
        interest_rate=Decimal("10.50"),
        interest_type=InterestType.FIXED,
        term_months=12,
        start_date=date(2026, 1, 1),
        notes="Education loan",
    )
    loan = service.create_loan(sample_user.id, payload)
    assert loan.id is not None
    assert loan.lender_name == "HDFC Personal Loan"
    assert loan.principal_amount == Decimal("120000.00")
    assert loan.remaining_balance == Decimal("120000.00")
    assert loan.is_settled is False

    # Fetch schedules from repository
    schedules = service.loan_repo.list_schedules(loan.id)
    assert len(schedules) == 12
    assert schedules[0].payment_number == 1
    assert schedules[0].is_paid is False


def test_record_loan_payment_success_and_settlement(
    db_session: Session, sample_user: User, loan_account: FinancialAccount
) -> None:
    """Verify recording loan payments reduces remaining balance and marks is_settled when paid off."""
    service = LoanService(db_session)
    payload = LoanCreate(
        account_id=loan_account.id,
        lender_name="Short Term Loan",
        principal_amount=Decimal("10000.00"),
        interest_rate=Decimal("0.00"),
        interest_type=InterestType.FIXED,
        term_months=2,
        start_date=date(2026, 1, 1),
    )
    loan = service.create_loan(sample_user.id, payload)

    # Pay instalment #1 (5,000 principal)
    p1 = service.record_payment(sample_user.id, loan.id, payment_number=1)
    assert p1.is_paid is True
    assert p1.principal_component == Decimal("5000.00")

    updated_loan = service.get_loan(sample_user.id, loan.id)
    assert updated_loan.remaining_balance == Decimal("5000.00")
    assert updated_loan.is_settled is False

    # Duplicate payment of instalment #1 raises ValidationError
    with pytest.raises(ValidationError) as exc:
        service.record_payment(sample_user.id, loan.id, payment_number=1)
    assert "already been recorded as paid" in exc.value.message

    # Pay instalment #2 (5,000 principal) -> Settled!
    p2 = service.record_payment(sample_user.id, loan.id, payment_number=2)
    assert p2.is_paid is True

    settled_loan = service.get_loan(sample_user.id, loan.id)
    assert settled_loan.remaining_balance == Decimal("0.00")
    assert settled_loan.is_settled is True


def test_create_loan_invalid_inputs_fails(
    db_session: Session, sample_user: User, loan_account: FinancialAccount
) -> None:
    """Verify non-positive principal or tenure raises ValidationError."""
    service = LoanService(db_session)

    # Zero principal
    with pytest.raises((ValidationError, PydanticValidationError)):
        service.create_loan(
            sample_user.id,
            LoanCreate(
                account_id=loan_account.id,
                lender_name="Bank",
                principal_amount=Decimal("0.00"),
                interest_rate=Decimal("10.00"),
                term_months=12,
                start_date=date(2026, 1, 1),
            ),
        )

    # Zero term
    with pytest.raises((ValidationError, PydanticValidationError)):
        service.create_loan(
            sample_user.id,
            LoanCreate(
                account_id=loan_account.id,
                lender_name="Bank",
                principal_amount=Decimal("1000.00"),
                interest_rate=Decimal("10.00"),
                term_months=0,
                start_date=date(2026, 1, 1),
            ),
        )
