"""Domain service implementing business rules for financial accounts."""

from sqlalchemy.orm import Session

from src.core.exceptions import ConflictError, NotFoundError
from src.core.logging import logger
from src.repositories.account_repo import AccountRepository
from src.schemas.account import AccountCreate, AccountRead, AccountUpdate


class AccountService:
    """Orchestrates business operations on FinancialAccounts."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AccountRepository(session)

    def create_account(self, user_id: str, payload: AccountCreate) -> AccountRead:
        """Create a new financial account, ensuring unique name for user."""
        existing = self.repo.list_by_user(user_id=user_id, active_only=False)
        for acc in existing:
            if acc.name.lower() == payload.name.lower():
                raise ConflictError(
                    f"An account named '{payload.name}' already exists for this user."
                )

        account = self.repo.create(user_id=user_id, payload=payload)
        self.session.commit()
        self.session.refresh(account)
        logger.info(f"Account created successfully: {account.id} ({account.name})")
        return AccountRead.model_validate(account)

    def get_account(self, account_id: str, user_id: str) -> AccountRead:
        """Retrieve an account by ID, verifying user ownership."""
        account = self.repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found.")
        return AccountRead.model_validate(account)

    def list_accounts(self, user_id: str, active_only: bool = True) -> list[AccountRead]:
        """List accounts owned by user."""
        accounts = self.repo.list_by_user(user_id=user_id, active_only=active_only)
        return [AccountRead.model_validate(acc) for acc in accounts]

    def update_account(self, account_id: str, user_id: str, payload: AccountUpdate) -> AccountRead:
        """Update an existing account's metadata."""
        account = self.repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found.")

        if payload.name and payload.name.lower() != account.name.lower():
            existing = self.repo.list_by_user(user_id=user_id, active_only=False)
            if any(a.name.lower() == payload.name.lower() and a.id != account_id for a in existing):
                raise ConflictError(f"An account named '{payload.name}' already exists.")

        updated = self.repo.update(account=account, payload=payload)
        self.session.commit()
        self.session.refresh(updated)
        logger.info(f"Account updated: {updated.id}")
        return AccountRead.model_validate(updated)

    def archive_account(self, account_id: str, user_id: str) -> AccountRead:
        """Soft-delete an account (archive)."""
        account = self.repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found.")

        archived = self.repo.archive(account=account)
        self.session.commit()
        self.session.refresh(archived)
        logger.info(f"Account archived: {archived.id}")
        return AccountRead.model_validate(archived)
