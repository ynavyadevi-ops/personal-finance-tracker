"""FastAPI router for monthly budgets, utilization tracking, and rollover alerts."""

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_budget_service, get_current_user
from src.db.models.user import User
from src.schemas.budget import BudgetCreate, BudgetRead, BudgetUtilization
from src.schemas.common import GenericResponse
from src.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post(
    "",
    response_model=GenericResponse[BudgetRead],
    status_code=status.HTTP_201_CREATED,
    summary="Set Category Budget",
    description="Creates or updates a monthly budget allocation for an expense category.",
)
def set_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service),
) -> GenericResponse[BudgetRead]:
    """Establish monthly budget allocation for a user-owned category."""
    result = budget_service.set_budget(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=result)


@router.get(
    "/utilization",
    response_model=GenericResponse[BudgetUtilization],
    status_code=status.HTTP_200_OK,
    summary="Get Budget Utilization for Category",
    description="Calculates consumption, remaining funds, rollover, and alert threshold status.",
)
def get_budget_utilization(
    category_id: str = Query(..., description="Target expense category ID"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g. 2026)"),
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service),
) -> GenericResponse[BudgetUtilization]:
    """Retrieve detailed utilization metrics for a specific category and period."""
    utilization = budget_service.get_budget_utilization(
        user_id=current_user.id,
        category_id=category_id,
        month=month,
        year=year,
    )
    return GenericResponse(success=True, data=utilization)


@router.get(
    "/period",
    response_model=GenericResponse[list[BudgetUtilization]],
    status_code=status.HTTP_200_OK,
    summary="List Budget Utilizations for Period",
    description="Retrieves consumption and threshold status across all category budgets for a period.",
)
def list_period_budgets(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g. 2026)"),
    current_user: User = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service),
) -> GenericResponse[list[BudgetUtilization]]:
    """List all configured budget utilizations for the specified month and year."""
    results = budget_service.list_budget_utilizations(
        user_id=current_user.id,
        month=month,
        year=year,
    )
    return GenericResponse(success=True, data=results)
