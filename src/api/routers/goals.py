"""FastAPI router for savings goals, contributions, and milestone tracking."""

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user, get_goal_service
from src.db.models.user import User
from src.schemas.common import GenericResponse
from src.schemas.goal import (
    GoalContributionRequest,
    GoalWithdrawalRequest,
    SavingsGoalCreate,
    SavingsGoalProgress,
    SavingsGoalRead,
)
from src.services.goal_service import SavingsGoalService

router = APIRouter(prefix="/goals", tags=["Savings Goals"])


@router.post(
    "",
    response_model=GenericResponse[SavingsGoalRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Savings Goal",
    description="Initializes a new target milestone for personal savings.",
)
def create_goal(
    payload: SavingsGoalCreate,
    current_user: User = Depends(get_current_user),
    goal_service: SavingsGoalService = Depends(get_goal_service),
) -> GenericResponse[SavingsGoalRead]:
    """Create a savings goal milestone with a target monetary value."""
    result = goal_service.create_goal(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=result)


@router.get(
    "",
    response_model=GenericResponse[list[SavingsGoalRead]],
    status_code=status.HTTP_200_OK,
    summary="List Savings Goals",
    description="Retrieves all savings milestones configured for the user.",
)
def list_goals(
    current_user: User = Depends(get_current_user),
    goal_service: SavingsGoalService = Depends(get_goal_service),
) -> GenericResponse[list[SavingsGoalRead]]:
    """List all goals belonging to the authenticated user."""
    items = goal_service.list_goals(user_id=current_user.id)
    return GenericResponse(success=True, data=items)


@router.get(
    "/{goal_id}/progress",
    response_model=GenericResponse[SavingsGoalProgress],
    status_code=status.HTTP_200_OK,
    summary="Get Goal Progress",
    description="Calculates progress percentage, remaining balance, and completion flag.",
)
def get_goal_progress(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    goal_service: SavingsGoalService = Depends(get_goal_service),
) -> GenericResponse[SavingsGoalProgress]:
    """Compute progress percentage and remaining amount for a savings goal."""
    progress = goal_service.get_goal_progress(user_id=current_user.id, goal_id=goal_id)
    return GenericResponse(success=True, data=progress)


@router.post(
    "/{goal_id}/contribute",
    response_model=GenericResponse[SavingsGoalProgress],
    status_code=status.HTTP_200_OK,
    summary="Contribute to Goal",
    description="Allocates savings funds towards a milestone.",
)
def contribute_to_goal(
    goal_id: str,
    payload: GoalContributionRequest,
    current_user: User = Depends(get_current_user),
    goal_service: SavingsGoalService = Depends(get_goal_service),
) -> GenericResponse[SavingsGoalProgress]:
    """Record a contribution towards achieving the goal target."""
    progress = goal_service.add_contribution(
        user_id=current_user.id,
        goal_id=goal_id,
        amount=payload.amount,
        notes=payload.notes,
    )
    return GenericResponse(success=True, data=progress)


@router.post(
    "/{goal_id}/withdraw",
    response_model=GenericResponse[SavingsGoalProgress],
    status_code=status.HTTP_200_OK,
    summary="Withdraw from Goal",
    description="Deducts allocated funds from a savings milestone.",
)
def withdraw_from_goal(
    goal_id: str,
    payload: GoalWithdrawalRequest,
    current_user: User = Depends(get_current_user),
    goal_service: SavingsGoalService = Depends(get_goal_service),
) -> GenericResponse[SavingsGoalProgress]:
    """Withdraw funds from savings goal balance."""
    progress = goal_service.withdraw_contribution(
        user_id=current_user.id,
        goal_id=goal_id,
        amount=payload.amount,
    )
    return GenericResponse(success=True, data=progress)
