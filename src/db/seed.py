"""Database seed script populating default user, initial account, and Phase 2 foundational records."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.logging import logger
from src.db.models import (
    AccountType,
    AssetType,
    Category,
    CategoryType,
    FinancialAccount,
    InvestmentAsset,
    SavingsGoal,
    User,
)
from src.db.session import get_db_context

DEFAULT_USER_ID = "default-user-id"

DEFAULT_CATEGORIES: list[dict[str, str | CategoryType | bool]] = [
    # Income categories
    {
        "name": "Salary",
        "category_type": CategoryType.INCOME,
        "color": "#10b981",
        "icon": "briefcase",
    },
    {
        "name": "Investments & Dividends",
        "category_type": CategoryType.INCOME,
        "color": "#059669",
        "icon": "trending-up",
    },
    {
        "name": "Freelance & Consulting",
        "category_type": CategoryType.INCOME,
        "color": "#34d399",
        "icon": "laptop",
    },
    {
        "name": "Other Income",
        "category_type": CategoryType.INCOME,
        "color": "#6ee7b7",
        "icon": "plus-circle",
    },
    # Expense categories
    {
        "name": "Housing & Rent",
        "category_type": CategoryType.EXPENSE,
        "color": "#ef4444",
        "icon": "home",
    },
    {
        "name": "Groceries & Dining",
        "category_type": CategoryType.EXPENSE,
        "color": "#f97316",
        "icon": "shopping-cart",
    },
    {
        "name": "Utilities & Bills",
        "category_type": CategoryType.EXPENSE,
        "color": "#f59e0b",
        "icon": "zap",
    },
    {
        "name": "Transportation & Fuel",
        "category_type": CategoryType.EXPENSE,
        "color": "#3b82f6",
        "icon": "truck",
    },
    {
        "name": "Healthcare & Insurance",
        "category_type": CategoryType.EXPENSE,
        "color": "#ec4899",
        "icon": "heart",
    },
    {
        "name": "Entertainment & Leisure",
        "category_type": CategoryType.EXPENSE,
        "color": "#8b5cf6",
        "icon": "film",
    },
    {
        "name": "Education",
        "category_type": CategoryType.EXPENSE,
        "color": "#6366f1",
        "icon": "book",
    },
    {
        "name": "Personal Care",
        "category_type": CategoryType.EXPENSE,
        "color": "#14b8a6",
        "icon": "smile",
    },
    {
        "name": "Miscellaneous",
        "category_type": CategoryType.EXPENSE,
        "color": "#64748b",
        "icon": "more-horizontal",
    },
]


def seed_database(session: Session) -> None:
    """Populate default user, account, categories, sample assets, and goals if they do not exist."""
    # 1. Default user
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

    # 2. Default checking account (preserve existing account if already seeded)
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
            institution_name="State Bank of India",
            currency="INR",
            opening_balance=Decimal("1500.00"),
            is_active=True,
        )
        session.add(account)
        logger.info(f"Initial account created: {account.name}")

    # 3. Default Categories
    for cat_data in DEFAULT_CATEGORIES:
        stmt_cat = select(Category).where(
            Category.user_id == user.id,
            Category.name == str(cat_data["name"]),
        )
        existing_cat = session.execute(stmt_cat).scalar_one_or_none()
        if not existing_cat:
            category = Category(
                user_id=user.id,
                name=str(cat_data["name"]),
                category_type=CategoryType(str(cat_data["category_type"])),
                color=str(cat_data["color"]),
                icon=str(cat_data.get("icon")),
                is_default=True,
            )
            session.add(category)

    # 4. Default Sample Investment Asset
    stmt_asset = select(InvestmentAsset).where(InvestmentAsset.symbol == "NIFTYBEES")
    asset = session.execute(stmt_asset).scalar_one_or_none()
    if not asset:
        asset = InvestmentAsset(
            symbol="NIFTYBEES",
            name="Nippon India ETF Nifty 50 BeES",
            asset_type=AssetType.ETF,
            isin="INF732E01015",
            exchange="NSE",
            currency="INR",
            current_price=Decimal("275.50"),
            is_active=True,
        )
        session.add(asset)

    # 5. Default Sample Savings Goal
    stmt_goal = select(SavingsGoal).where(
        SavingsGoal.user_id == user.id,
        SavingsGoal.name == "Emergency Fund",
    )
    goal = session.execute(stmt_goal).scalar_one_or_none()
    if not goal:
        goal = SavingsGoal(
            user_id=user.id,
            name="Emergency Fund",
            target_amount=Decimal("100000.00"),
            current_amount=Decimal("25000.00"),
            currency="INR",
            is_achieved=False,
            notes="3 months of essential living expenses",
        )
        session.add(goal)

    session.commit()
    logger.info("Database seeding completed successfully.")


def main() -> None:
    """Run database seeder directly."""
    with get_db_context() as session:
        seed_database(session)


if __name__ == "__main__":
    main()
