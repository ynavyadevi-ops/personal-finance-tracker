"""Financial accounts API router."""

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_account_service, get_current_user_id
from src.schemas.account import AccountCreate, AccountRead, AccountUpdate
from src.schemas.common import GenericResponse
from src.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get(
    "",
    response_model=GenericResponse[list[AccountRead]],
    status_code=status.HTTP_200_OK,
    summary="List Accounts",
    description="Retrieve all financial accounts belonging to the current user.",
)
def list_accounts(
    active_only: bool = Query(default=True, description="Filter for active accounts only."),
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> GenericResponse[list[AccountRead]]:
    """List financial accounts owned by the user."""
    accounts = service.list_accounts(user_id=user_id, active_only=active_only)
    return GenericResponse(data=accounts, meta={"count": len(accounts)})


@router.post(
    "",
    response_model=GenericResponse[AccountRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Account",
    description="Create a new financial account (Checking, Savings, Credit Card, etc.).",
)
def create_account(
    payload: AccountCreate,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> GenericResponse[AccountRead]:
    """Create a new financial account."""
    account = service.create_account(user_id=user_id, payload=payload)
    return GenericResponse(data=account)


@router.get(
    "/{account_id}",
    response_model=GenericResponse[AccountRead],
    status_code=status.HTTP_200_OK,
    summary="Get Account by ID",
    description="Retrieve a specific account by its unique identifier.",
)
def get_account(
    account_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> GenericResponse[AccountRead]:
    """Fetch an account by ID."""
    account = service.get_account(account_id=account_id, user_id=user_id)
    return GenericResponse(data=account)


@router.patch(
    "/{account_id}",
    response_model=GenericResponse[AccountRead],
    status_code=status.HTTP_200_OK,
    summary="Update Account",
    description="Update an account's name, type, or institution.",
)
def update_account(
    account_id: str,
    payload: AccountUpdate,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> GenericResponse[AccountRead]:
    """Update an existing account."""
    updated = service.update_account(account_id=account_id, user_id=user_id, payload=payload)
    return GenericResponse(data=updated)


@router.delete(
    "/{account_id}",
    response_model=GenericResponse[AccountRead],
    status_code=status.HTTP_200_OK,
    summary="Archive Account",
    description="Soft-delete (archive) an account, marking it inactive.",
)
def archive_account(
    account_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> GenericResponse[AccountRead]:
    """Archive an account."""
    archived = service.archive_account(account_id=account_id, user_id=user_id)
    return GenericResponse(data=archived)
