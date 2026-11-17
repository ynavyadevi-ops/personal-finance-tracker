"""FastAPI router for recurring transaction rules, automated bill schedules, and execution."""

from datetime import date

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_current_user, get_recurring_service
from src.db.models.user import User
from src.schemas.common import GenericResponse
from src.schemas.recurring import RecurringRuleCreate, RecurringRuleRead
from src.schemas.transaction import TransactionRead
from src.services.recurring_service import RecurringService

router = APIRouter(prefix="/recurring", tags=["Recurring Transactions"])


@router.post(
    "",
    response_model=GenericResponse[RecurringRuleRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Recurring Rule",
    description="Schedules an automated recurring transaction rule for expenses, income, or transfers.",
)
def create_recurring_rule(
    payload: RecurringRuleCreate,
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[RecurringRuleRead]:
    """Create a recurring template schedule."""
    rule = recurring_service.create_rule(user_id=current_user.id, payload=payload)
    return GenericResponse(success=True, data=rule)


@router.get(
    "",
    response_model=GenericResponse[list[RecurringRuleRead]],
    status_code=status.HTTP_200_OK,
    summary="List Recurring Rules",
    description="Retrieves all scheduled recurrence rules for the user.",
)
def list_recurring_rules(
    active_only: bool = Query(False, description="Filter active schedules only"),
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[list[RecurringRuleRead]]:
    """List recurring rules belonging to the user."""
    rules = recurring_service.list_rules(user_id=current_user.id, active_only=active_only)
    return GenericResponse(success=True, data=rules)


@router.get(
    "/due",
    response_model=GenericResponse[list[RecurringRuleRead]],
    status_code=status.HTTP_200_OK,
    summary="List Due Recurring Rules",
    description="Retrieves active recurrence rules that are due for execution as of a target date.",
)
def list_due_rules(
    as_of_date: date | None = Query(
        None, description="Optional target evaluation date (defaults to today)"
    ),
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[list[RecurringRuleRead]]:
    """Query recurring rules due for ledger posting."""
    rules = recurring_service.list_due_rules(user_id=current_user.id, as_of_date=as_of_date)
    return GenericResponse(success=True, data=rules)


@router.post(
    "/{rule_id}/execute",
    response_model=GenericResponse[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Execute Due Recurring Rule",
    description="Executes a due recurring rule, creating a validated ledger transaction and advancing the schedule.",
)
def execute_due_rule(
    rule_id: str,
    execution_date: date | None = Query(None, description="Optional execution date override"),
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[TransactionRead]:
    """Execute a scheduled recurring rule with duplicate occurrence protection."""
    tx = recurring_service.execute_due_rule(
        user_id=current_user.id,
        rule_id=rule_id,
        execution_date=execution_date,
    )
    return GenericResponse(success=True, data=tx)


@router.post(
    "/{rule_id}/pause",
    response_model=GenericResponse[RecurringRuleRead],
    status_code=status.HTTP_200_OK,
    summary="Pause Recurring Rule",
    description="Deactivates a recurring schedule.",
)
def pause_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[RecurringRuleRead]:
    """Pause an active recurring schedule."""
    rule = recurring_service.pause_rule(user_id=current_user.id, rule_id=rule_id)
    return GenericResponse(success=True, data=rule)


@router.post(
    "/{rule_id}/resume",
    response_model=GenericResponse[RecurringRuleRead],
    status_code=status.HTTP_200_OK,
    summary="Resume Recurring Rule",
    description="Reactivates a paused recurring schedule.",
)
def resume_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[RecurringRuleRead]:
    """Resume a paused recurring schedule."""
    rule = recurring_service.resume_rule(user_id=current_user.id, rule_id=rule_id)
    return GenericResponse(success=True, data=rule)


@router.delete(
    "/{rule_id}",
    response_model=GenericResponse[RecurringRuleRead],
    status_code=status.HTTP_200_OK,
    summary="Cancel Recurring Rule",
    description="Non-destructively cancels a recurring rule, deactivating it permanently while preserving historical ledger transactions.",
)
@router.post(
    "/{rule_id}/cancel",
    response_model=GenericResponse[RecurringRuleRead],
    status_code=status.HTTP_200_OK,
    summary="Cancel Recurring Rule (Alternative Endpoint)",
    description="Non-destructively cancels a recurring rule.",
)
def cancel_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    recurring_service: RecurringService = Depends(get_recurring_service),
) -> GenericResponse[RecurringRuleRead]:
    """Cancel an active or paused recurring schedule non-destructively."""
    rule = recurring_service.cancel_rule(user_id=current_user.id, rule_id=rule_id)
    return GenericResponse(success=True, data=rule)
