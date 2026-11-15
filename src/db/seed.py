"""Database seed script populating default user and initial account for local development."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.logging import logger
from src.db.models import AccountType, FinancialAccount, User
from src.db.session import get_db_context

DEFAULT_USER_ID = "default-user-id"


def seed_database(session: Session) -> None:
    """Populate default user and account if they do not exist."""
    # Check if default user exists
    stmt = select(User).where(User.id == DEFAULT_USER_ID)
    user = session.execute(stmt).scalar_one_or_none()

    if not user:
        logger.info("Creating default local user...")
        user = User(
            id=DEFAULT_USER_ID,
            email="user@local.dev",
            name="Primary User",
        )
        session.add(user)
        session.flush()
        logger.info(f"Default user created with id: {user.id}")

    # Check if default account exists
    stmt_acc = select(FinancialAccount).where(
        FinancialAccount.user_id == user.id,
        FinancialAccount.name == "Primary Checking",
    )
    account = session.execute(stmt_acc).scalar_one_or_none()

    if not account:
        logger.info("Creating initial checking account...")
        account = FinancialAccount(
            user_id=user.id,
            name="Primary Checking",
            account_type=AccountType.CHECKING,
            institution_name="First National Bank",
            currency="USD",
            opening_balance=Decimal("1500.00"),
            is_active=True,
        )
        session.add(account)
        logger.info(f"Initial account created: {account.name}")

    session.commit()
    logger.info("Database seeding completed successfully.")


def main() -> None:
    """Run database seeder directly."""
    with get_db_context() as session:
        seed_database(session)


if __name__ == "__main__":
    main()
