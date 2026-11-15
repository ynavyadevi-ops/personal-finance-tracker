"""Repository layer handling database interactions for FinancialAccount."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.account import FinancialAccount
from src.schemas.account import AccountCreate, AccountUpdate


class AccountRepository:
    """Encapsulates database operations for FinancialAccount entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_id: str, payload: AccountCreate) -> FinancialAccount:
        """Create and persist a new financial account."""
        account = FinancialAccount(
            user_id=user_id,
            name=payload.name,
            account_type=payload.account_type,
            institution_name=payload.institution_name,
            currency=payload.currency,
            opening_balance=payload.opening_balance,
            is_active=True,
        )
        self.session.add(account)
        self.session.flush()
        return account

    def get_by_id(self, account_id: str, user_id: str) -> FinancialAccount | None:
        """Fetch a specific account owned by the user."""
        stmt = select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_user(self, user_id: str, active_only: bool = True) -> list[FinancialAccount]:
        """Retrieve all accounts belonging to a user, optionally filtered by active status."""
        stmt = select(FinancialAccount).where(FinancialAccount.user_id == user_id)
        if active_only:
            stmt = stmt.where(FinancialAccount.is_active.is_(True))
        stmt = stmt.order_by(FinancialAccount.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def update(self, account: FinancialAccount, payload: AccountUpdate) -> FinancialAccount:
        """Update existing account fields."""
        if payload.name is not None:
            account.name = payload.name
        if payload.account_type is not None:
            account.account_type = payload.account_type
        if payload.institution_name is not None:
            account.institution_name = payload.institution_name
        if payload.is_active is not None:
            account.is_active = payload.is_active
        self.session.flush()
        return account

    def archive(self, account: FinancialAccount) -> FinancialAccount:
        """Soft-delete an account by setting is_active to False."""
        account.is_active = False
        self.session.flush()
        return account
