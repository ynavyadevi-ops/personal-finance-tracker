"""FastAPI router for investments, securities trading, portfolio holdings, and dividends."""

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_current_user, get_investment_service
from src.db.models.user import User
from src.schemas.common import GenericResponse
from src.schemas.investment import (
    DividendRequest,
    InvestmentBuyRequest,
    InvestmentHoldingRead,
    InvestmentSellRequest,
    InvestmentTransactionRead,
    RealizedGainLossResult,
)
from src.services.investment_service import InvestmentService

router = APIRouter(prefix="/investments", tags=["Investments"])


@router.post(
    "/buy",
    response_model=GenericResponse[InvestmentHoldingRead],
    status_code=status.HTTP_201_CREATED,
    summary="Buy Investment Security",
    description="Records a security purchase, updating holdings with weighted-average cost basis.",
)
def buy_security(
    payload: InvestmentBuyRequest,
    current_user: User = Depends(get_current_user),
    inv_service: InvestmentService = Depends(get_investment_service),
) -> GenericResponse[InvestmentHoldingRead]:
    """Execute a purchase trade and update holding cost basis."""
    holding = inv_service.buy_asset(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=holding)


@router.post(
    "/sell",
    response_model=GenericResponse[RealizedGainLossResult],
    status_code=status.HTTP_200_OK,
    summary="Sell Investment Security",
    description="Processes a security liquidation and computes realized capital gains/losses.",
)
def sell_security(
    payload: InvestmentSellRequest,
    current_user: User = Depends(get_current_user),
    inv_service: InvestmentService = Depends(get_investment_service),
) -> GenericResponse[RealizedGainLossResult]:
    """Execute a sale trade, verifying unit sufficiency and calculating realized P&L."""
    gain_loss = inv_service.sell_asset(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=gain_loss)


@router.post(
    "/dividend",
    response_model=GenericResponse[InvestmentTransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Record Dividend Receipt",
    description="Records dividend income from a held security position without altering share counts.",
)
def record_dividend(
    payload: DividendRequest,
    current_user: User = Depends(get_current_user),
    inv_service: InvestmentService = Depends(get_investment_service),
) -> GenericResponse[InvestmentTransactionRead]:
    """Record dividend earnings for a security."""
    inv_tx = inv_service.record_dividend(
        user_id=current_user.id,
        account_id=payload.account_id,
        asset_id=payload.asset_id,
        amount=payload.amount,
        transaction_date=payload.transaction_date,
        notes=payload.notes,
    )
    return GenericResponse(success=True, data=inv_tx)


@router.get(
    "/holdings",
    response_model=GenericResponse[list[InvestmentHoldingRead]],
    status_code=status.HTTP_200_OK,
    summary="List Investment Holdings",
    description="Retrieves active portfolio holdings and cost basis information.",
)
def list_holdings(
    account_id: str | None = Query(None, description="Optional account ID filter"),
    current_user: User = Depends(get_current_user),
    inv_service: InvestmentService = Depends(get_investment_service),
) -> GenericResponse[list[InvestmentHoldingRead]]:
    """List portfolio security holdings for the user."""
    holdings = inv_service.list_holdings(user_id=current_user.id, account_id=account_id)
    return GenericResponse(success=True, data=holdings)
