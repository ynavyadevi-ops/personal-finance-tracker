"""FastAPI router for loans, amortization schedules, and debt instalment payments."""

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user, get_loan_service
from src.db.models.user import User
from src.schemas.common import GenericResponse
from src.schemas.loan import (
    LoanCreate,
    LoanPaymentRequest,
    LoanPaymentScheduleRead,
    LoanRead,
)
from src.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post(
    "",
    response_model=GenericResponse[LoanRead],
    status_code=status.HTTP_201_CREATED,
    summary="Record New Loan Liability",
    description="Records a loan obligation and auto-generates its fixed-rate amortization schedule.",
)
def create_loan(
    payload: LoanCreate,
    current_user: User = Depends(get_current_user),
    loan_service: LoanService = Depends(get_loan_service),
) -> GenericResponse[LoanRead]:
    """Create loan liability and generate monthly payment schedules."""
    loan = loan_service.create_loan(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=loan)


@router.get(
    "",
    response_model=GenericResponse[list[LoanRead]],
    status_code=status.HTTP_200_OK,
    summary="List User Loans",
    description="Retrieves all debt obligations and liabilities for the authenticated user.",
)
def list_loans(
    current_user: User = Depends(get_current_user),
    loan_service: LoanService = Depends(get_loan_service),
) -> GenericResponse[list[LoanRead]]:
    """List all loans belonging to the user."""
    loans = loan_service.list_loans(user_id=current_user.id)
    return GenericResponse(success=True, data=loans)


@router.get(
    "/{loan_id}",
    response_model=GenericResponse[LoanRead],
    status_code=status.HTTP_200_OK,
    summary="Get Loan Details",
    description="Retrieves specific loan details including its amortization payment schedules.",
)
def get_loan(
    loan_id: str,
    current_user: User = Depends(get_current_user),
    loan_service: LoanService = Depends(get_loan_service),
) -> GenericResponse[LoanRead]:
    """Fetch loan details and full payment schedule."""
    loan = loan_service.get_loan(user_id=current_user.id, loan_id=loan_id)
    return GenericResponse(success=True, data=loan)


@router.post(
    "/{loan_id}/payment",
    response_model=GenericResponse[LoanPaymentScheduleRead],
    status_code=status.HTTP_200_OK,
    summary="Record Loan Instalment Payment",
    description="Marks a payment instalment as paid, adjusting remaining loan balance.",
)
def record_loan_payment(
    loan_id: str,
    payload: LoanPaymentRequest,
    current_user: User = Depends(get_current_user),
    loan_service: LoanService = Depends(get_loan_service),
) -> GenericResponse[LoanPaymentScheduleRead]:
    """Process payment instalment, updating loan principal balance and schedule status."""
    schedule = loan_service.record_payment(
        user_id=current_user.id,
        loan_id=loan_id,
        payment_number=payload.payment_number,
        transaction_id=payload.transaction_id,
    )
    return GenericResponse(success=True, data=schedule)
