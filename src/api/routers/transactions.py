"""FastAPI router for financial transactions, transfers, reversals, and reconciliation."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import (
    get_current_user,
    get_ledger_service,
    get_transaction_service,
)
from src.db.models.transaction import TransactionType
from src.db.models.user import User
from src.schemas.common import GenericResponse
from src.schemas.transaction import (
    AccountReconciliation,
    TransactionCreate,
    TransactionRead,
    TransactionReversalRequest,
    TransferCreate,
)
from src.services.ledger_service import LedgerService
from src.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=GenericResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Record Income or Expense Transaction",
    description="Records a business transaction with balanced double-entry ledger entries.",
)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    tx_service: TransactionService = Depends(get_transaction_service),
) -> GenericResponse[TransactionRead]:
    """Execute double-entry posting for a single income or expense event."""
    result = tx_service.record_transaction(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=result)


@router.post(
    "/transfer",
    response_model=GenericResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Record Inter-Account Transfer",
    description="Atomically transfers funds between two user-owned accounts, enforcing ledger balancing.",
)
def create_transfer(
    payload: TransferCreate,
    current_user: User = Depends(get_current_user),
    tx_service: TransactionService = Depends(get_transaction_service),
) -> GenericResponse[TransactionRead]:
    """Transfer funds between accounts, validating matching currencies and distinct accounts."""
    result = tx_service.record_transfer(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=result)


@router.post(
    "/{transaction_id}/reverse",
    response_model=GenericResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Compensating Transaction Reversal",
    description="Creates an inverted compensating transaction preserving full audit trail.",
)
def reverse_transaction(
    transaction_id: str,
    payload: TransactionReversalRequest,
    current_user: User = Depends(get_current_user),
    tx_service: TransactionService = Depends(get_transaction_service),
) -> GenericResponse[TransactionRead]:
    """Reverse an existing transaction by posting compensating debits and credits."""
    result = tx_service.reverse_transaction(
        user_id=current_user.id,
        transaction_id=transaction_id,
        reason=payload.reason,
    )
    return GenericResponse(success=True, data=result)


@router.get(
    "",
    response_model=GenericResponse[list[TransactionRead]],
    status_code=status.HTTP_200_OK,
    summary="List User Transactions",
    description="Queries paginated transaction history with optional filters.",
)
def list_transactions(
    account_id: str | None = Query(None, description="Filter by account ID"),
    category_id: str | None = Query(None, description="Filter by category ID"),
    transaction_type: TransactionType | None = Query(
        None, description="Filter by transaction type"
    ),
    limit: int = Query(100, ge=1, le=500, description="Page size limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    tx_service: TransactionService = Depends(get_transaction_service),
) -> GenericResponse[list[TransactionRead]]:
    """Retrieve transactions filtered by account, category, or type."""
    items = tx_service.list_transactions(
        user_id=current_user.id,
        account_id=account_id,
        category_id=category_id,
        transaction_type=transaction_type,
        limit=limit,
        offset=offset,
    )
    return GenericResponse(
        success=True,
        data=items,
        meta={"limit": limit, "offset": offset, "count": len(items)},
    )


@router.get(
    "/reconcile/{account_id}",
    response_model=GenericResponse[AccountReconciliation],
    status_code=status.HTTP_200_OK,
    summary="Reconcile Account Balance",
    description="Calculates cumulative debits and credits against opening balance.",
)
def reconcile_account(
    account_id: str,
    expected_balance: Decimal | None = Query(
        None, description="Optional expected statement balance"
    ),
    current_user: User = Depends(get_current_user),
    ledger_service: LedgerService = Depends(get_ledger_service),
) -> GenericResponse[AccountReconciliation]:
    """Compute mathematical reconciliation and discrepancy report for an account."""
    reconciliation = ledger_service.reconcile_account(
        account_id=account_id,
        user_id=current_user.id,
        expected_balance=expected_balance,
    )
    return GenericResponse(success=True, data=reconciliation)


@router.get(
    "/{transaction_id}",
    response_model=GenericResponse[TransactionRead],
    status_code=status.HTTP_200_OK,
    summary="Get Transaction by ID",
    description="Fetches a transaction and its line items, verifying user ownership.",
)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    tx_service: TransactionService = Depends(get_transaction_service),
) -> GenericResponse[TransactionRead]:
    """Retrieve details for a specific transaction."""
    tx = tx_service.get_transaction(transaction_id=transaction_id, user_id=current_user.id)
    return GenericResponse(success=True, data=tx)
