"""FastAPI dependency injection providers enforcing verified JWT identity and domain service instantiation."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.exceptions import AuthenticationError
from src.core.security import decode_access_token
from src.db.models.user import User
from src.db.session import get_db
from src.services.account_service import AccountService
from src.services.budget_service import BudgetService
from src.services.goal_service import SavingsGoalService
from src.services.investment_service import InvestmentService
from src.services.ledger_service import LedgerService
from src.services.loan_service import LoanService
from src.services.portability_service import (
    BackupService,
    DataExportService,
    StatementImportService,
)
from src.services.recurring_service import RecurringService
from src.services.transaction_service import TransactionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency verifying Bearer JWT token and resolving the authenticated User entity.

    Raises:
        AuthenticationError: If token is missing, invalid, expired, or references a non-existent user.
    """
    user_id = decode_access_token(token)
    user = db.get(User, user_id)
    if not user:
        raise AuthenticationError("Authenticated user was not found or has been disabled.")
    return user


def get_current_user_id(
    current_user: User = Depends(get_current_user),
) -> str:
    """Dependency extracting the authenticated user's ID from verified server-side identity context."""
    return current_user.id


def get_account_service(db: Session = Depends(get_db)) -> AccountService:
    """Dependency injecting AccountService with active database session."""
    return AccountService(session=db)


def get_ledger_service(db: Session = Depends(get_db)) -> LedgerService:
    """Dependency injecting LedgerService with active database session."""
    return LedgerService(session=db)


def get_transaction_service(db: Session = Depends(get_db)) -> TransactionService:
    """Dependency injecting TransactionService with active database session."""
    return TransactionService(session=db)


def get_budget_service(db: Session = Depends(get_db)) -> BudgetService:
    """Dependency injecting BudgetService with active database session."""
    return BudgetService(session=db)


def get_goal_service(db: Session = Depends(get_db)) -> SavingsGoalService:
    """Dependency injecting SavingsGoalService with active database session."""
    return SavingsGoalService(session=db)


def get_loan_service(db: Session = Depends(get_db)) -> LoanService:
    """Dependency injecting LoanService with active database session."""
    return LoanService(session=db)


def get_recurring_service(db: Session = Depends(get_db)) -> RecurringService:
    """Dependency injecting RecurringService with active database session."""
    return RecurringService(session=db)


def get_investment_service(db: Session = Depends(get_db)) -> InvestmentService:
    """Dependency injecting InvestmentService with active database session."""
    return InvestmentService(session=db)


def get_statement_import_service(db: Session = Depends(get_db)) -> StatementImportService:
    """Dependency injecting StatementImportService with active database session."""
    return StatementImportService(session=db)


def get_data_export_service(db: Session = Depends(get_db)) -> DataExportService:
    """Dependency injecting DataExportService with active database session."""
    return DataExportService(session=db)


def get_backup_service(db: Session = Depends(get_db)) -> BackupService:
    """Dependency injecting BackupService with active database session."""
    return BackupService(session=db)
