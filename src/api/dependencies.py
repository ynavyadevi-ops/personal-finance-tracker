"""FastAPI dependency injection providers."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.services.account_service import AccountService

# Constant default user identifier for local MVP single-tenant operation
DEFAULT_USER_ID = "default-user-id"


def get_current_user_id() -> str:
    """Dependency returning current user ID.

    For Phase 1 local MVP, binds to the seeded default local user.
    """
    return DEFAULT_USER_ID


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    """Dependency injecting AccountService with an active database session."""
    return AccountService(session=db)
