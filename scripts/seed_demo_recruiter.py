"""Seed script for Recruiter Portfolio Demo Dataset.
Strictly targets data/demo_finance.db and user 'demo.recruiter@example.com'.
Never touches data/finance.db or any other user-created records.
"""

from __future__ import annotations

import argparse
import getpass
import os
import secrets
import sys
from datetime import date, timedelta
from decimal import Decimal

# Ensure local source root is on sys.path
sys.path.insert(0, ".")

from src.core.config import settings
from src.core.security import hash_password
from src.db.models import (
    AccountType,
    AssetType,
    Category,
    Frequency,
    InterestType,
    InvestmentAsset,
    TransactionType,
    User,
    UserRole,
)
from src.db.session import get_db_context
from src.schemas.account import AccountCreate
from src.schemas.budget import BudgetCreate
from src.schemas.goal import SavingsGoalCreate
from src.schemas.investment import InvestmentBuyRequest
from src.schemas.loan import LoanCreate
from src.schemas.recurring import RecurringRuleCreate
from src.schemas.transaction import TransactionCreate, TransferCreate
from src.services.account_service import AccountService
from src.services.budget_service import BudgetService
from src.services.goal_service import SavingsGoalService
from src.services.investment_service import InvestmentService
from src.services.loan_service import LoanService
from src.services.recurring_service import RecurringService
from src.services.transaction_service import TransactionService

# STRICT SAFETY GUARD: Demo database isolation only
if "demo_finance.db" not in settings.DATABASE_URL:
    raise RuntimeError(
        f"CRITICAL SAFETY VIOLATION: DATABASE_URL is '{settings.DATABASE_URL}'. Must be demo_finance.db!"
    )


def resolve_demo_password(prompt_if_interactive: bool = True) -> str:
    """Retrieve demo password from env or interactive prompt, or generate a secure credential."""
    env_pass = os.getenv("DEMO_RECRUITER_PASSWORD") or os.getenv("RECRUITER_DEMO_PASSWORD")
    if env_pass:
        return env_pass

    if prompt_if_interactive and sys.stdin.isatty():
        try:
            entered = getpass.getpass(
                "Enter password for demo.recruiter@example.com (or leave empty to auto-generate): "
            )
            if entered.strip():
                return entered.strip()
        except Exception:
            pass

    # Generate a cryptographically secure credential satisfying complexity requirements
    return f"Demo!{secrets.token_urlsafe(16)}9Aa"


def seed_recruiter_demo(rotate_password: bool = False) -> None:
    """Populate clean, realistic portfolio dataset for demo.recruiter@example.com."""
    print("=== Seeding Recruiter Portfolio Demo Dataset ===")

    with get_db_context() as session:
        # 1. Ensure user exists
        demo_user = (
            session.query(User).filter(User.email == "demo.recruiter@example.com").first()
        )
        if not demo_user:
            demo_password = resolve_demo_password()
            demo_user = User(
                email="demo.recruiter@example.com",
                name="Recruiter Demo",
                hashed_password=hash_password(demo_password),
                role=UserRole.USER,
                is_active=True,
            )
            session.add(demo_user)
            session.commit()
            session.refresh(demo_user)
            print(f"Created user: {demo_user.email} (ID: {demo_user.id})")
        else:
            if rotate_password:
                new_password = resolve_demo_password()
                demo_user.hashed_password = hash_password(new_password)
                session.commit()
                print(f"Rotated password for user: {demo_user.email}")
            else:
                print(f"Using existing user: {demo_user.email} (ID: {demo_user.id})")

        user_id = demo_user.id

        # Initialize domain services
        acc_service = AccountService(session)
        tx_service = TransactionService(session)
        budget_service = BudgetService(session)
        goal_service = SavingsGoalService(session)
        loan_service = LoanService(session)
        inv_service = InvestmentService(session)
        rec_service = RecurringService(session)

        # 2. Financial Accounts
        existing_accs = acc_service.list_accounts(user_id=user_id)
        acc_map: dict[str, str] = {a.name: a.id for a in existing_accs}

        if "HDFC Salary Account" not in acc_map:
            acc_salary = acc_service.create_account(
                user_id=user_id,
                payload=AccountCreate(
                    name="HDFC Salary Account",
                    account_type=AccountType.CHECKING,
                    institution_name="HDFC Bank",
                    currency="INR",
                    opening_balance=Decimal("50000.00"),
                ),
            )
            acc_map["HDFC Salary Account"] = acc_salary.id

        if "ICICI Savings Account" not in acc_map:
            acc_savings = acc_service.create_account(
                user_id=user_id,
                payload=AccountCreate(
                    name="ICICI Savings Account",
                    account_type=AccountType.SAVINGS,
                    institution_name="ICICI Bank",
                    currency="INR",
                    opening_balance=Decimal("120000.00"),
                ),
            )
            acc_map["ICICI Savings Account"] = acc_savings.id

        if "Zerodha Trading Demat" not in acc_map:
            acc_inv = acc_service.create_account(
                user_id=user_id,
                payload=AccountCreate(
                    name="Zerodha Trading Demat",
                    account_type=AccountType.INVESTMENT,
                    institution_name="Zerodha",
                    currency="INR",
                    opening_balance=Decimal("80000.00"),
                ),
            )
            acc_map["Zerodha Trading Demat"] = acc_inv.id

        if "HDFC Regalia Credit Card" not in acc_map:
            acc_cc = acc_service.create_account(
                user_id=user_id,
                payload=AccountCreate(
                    name="HDFC Regalia Credit Card",
                    account_type=AccountType.CREDIT_CARD,
                    institution_name="HDFC Bank",
                    currency="INR",
                    opening_balance=Decimal("0.00"),
                ),
            )
            acc_map["HDFC Regalia Credit Card"] = acc_cc.id

        print(f"Configured accounts: {list(acc_map.keys())}")

        # 3. Retrieve system categories
        categories = (
            session.query(Category)
            .filter((Category.user_id == user_id) | (Category.user_id.is_(None)))
            .all()
        )
        cat_by_name = {c.name: c for c in categories}

        cat_salary = cat_by_name.get("Salary & Wages") or cat_by_name.get("Salary")
        cat_housing = cat_by_name.get("Housing & Rent") or cat_by_name.get("Housing")
        cat_groceries = cat_by_name.get("Groceries & Dining") or cat_by_name.get("Food & Dining") or cat_by_name.get("Groceries")
        cat_utilities = cat_by_name.get("Utilities & Bills") or cat_by_name.get("Utilities")

        today = date.today()

        # 4. Record Double-Entry Transactions
        salary_acc_id = acc_map["HDFC Salary Account"]
        savings_acc_id = acc_map["ICICI Savings Account"]
        inv_acc_id = acc_map["Zerodha Trading Demat"]

        # Income: Monthly Salary ₹1,50,000.00
        tx_service.record_income(
            user_id=user_id,
            payload=TransactionCreate(
                account_id=salary_acc_id,
                category_id=cat_salary.id if cat_salary else None,
                amount=Decimal("150000.00"),
                description="Monthly Salary Credit",
                transaction_date=today - timedelta(days=15),
                currency="INR",
                notes="Net monthly take-home salary",
            ),
        )

        # Expense: Rent ₹32,000.00
        tx_service.record_expense(
            user_id=user_id,
            payload=TransactionCreate(
                account_id=salary_acc_id,
                category_id=cat_housing.id if cat_housing else None,
                amount=Decimal("32000.00"),
                description="Apartment Rent",
                transaction_date=today - timedelta(days=12),
                currency="INR",
                notes="November Rent payment",
            ),
        )

        # Expense: Groceries ₹12,500.00
        tx_service.record_expense(
            user_id=user_id,
            payload=TransactionCreate(
                account_id=salary_acc_id,
                category_id=cat_groceries.id if cat_groceries else None,
                amount=Decimal("12500.00"),
                description="Supermarket & Provisions",
                transaction_date=today - timedelta(days=8),
                currency="INR",
                notes="Monthly grocery restock",
            ),
        )

        # Expense: Utilities ₹3,450.00
        tx_service.record_expense(
            user_id=user_id,
            payload=TransactionCreate(
                account_id=salary_acc_id,
                category_id=cat_utilities.id if cat_utilities else None,
                amount=Decimal("3450.00"),
                description="Electricity & Broadband",
                transaction_date=today - timedelta(days=5),
                currency="INR",
            ),
        )

        # Transfer: Savings Transfer ₹40,000.00
        tx_service.record_transfer(
            user_id=user_id,
            payload=TransferCreate(
                source_account_id=salary_acc_id,
                destination_account_id=savings_acc_id,
                amount=Decimal("40000.00"),
                description="Monthly Savings Transfer",
                transaction_date=today - timedelta(days=14),
                currency="INR",
                notes="Automated allocation to high-yield savings",
            ),
        )

        # Transfer: Investment Allocation ₹25,000.00
        tx_service.record_transfer(
            user_id=user_id,
            payload=TransferCreate(
                source_account_id=salary_acc_id,
                destination_account_id=inv_acc_id,
                amount=Decimal("25000.00"),
                description="Demat Capital Allocation",
                transaction_date=today - timedelta(days=10),
                currency="INR",
                notes="Monthly equity investment funds",
            ),
        )
        print("Recorded income, expense, and inter-account transfer transactions.")

        # 5. Budgets
        if cat_housing:
            budget_service.set_budget(
                user_id=user_id,
                payload=BudgetCreate(
                    category_id=cat_housing.id,
                    amount=Decimal("35000.00"),
                    month=today.month,
                    year=today.year,
                    notes="Housing limit ₹35k",
                ),
            )
        if cat_groceries:
            budget_service.set_budget(
                user_id=user_id,
                payload=BudgetCreate(
                    category_id=cat_groceries.id,
                    amount=Decimal("15000.00"),
                    month=today.month,
                    year=today.year,
                    notes="Dining & Groceries limit ₹15k",
                ),
            )
        if cat_utilities:
            budget_service.set_budget(
                user_id=user_id,
                payload=BudgetCreate(
                    category_id=cat_utilities.id,
                    amount=Decimal("5000.00"),
                    month=today.month,
                    year=today.year,
                    notes="Utilities cap ₹5k",
                ),
            )
        print("Established monthly budgets with threshold tracking.")

        # 6. Savings Goals
        new_goal = goal_service.create_goal(
            user_id=user_id,
            payload=SavingsGoalCreate(
                name="Emergency Safety Fund",
                target_amount=Decimal("300000.00"),
                currency="INR",
                target_date=today + timedelta(days=180),
                notes="6-months reserve fund",
            ),
        )
        # Contribute to goal
        goal_service.add_contribution(
            user_id=user_id,
            goal_id=new_goal.id,
            amount=Decimal("120000.00"),
            notes="Initial reserve allocation",
        )
        print("Configured savings goals with progress tracking.")

        # 7. Recurring Rules
        rec_service.create_rule(
            user_id=user_id,
            payload=RecurringRuleCreate(
                name="Broadband Fiber Internet",
                amount=Decimal("1299.00"),
                currency="INR",
                transaction_type=TransactionType.EXPENSE,
                frequency=Frequency.MONTHLY,
                interval=1,
                start_date=today,
                account_id=salary_acc_id,
                category_id=cat_utilities.id if cat_utilities else None,
            ),
        )
        print("Configured monthly recurring automation schedule.")

        # 8. Loan & Debt
        loan_service.create_loan(
            user_id=user_id,
            payload=LoanCreate(
                account_id=salary_acc_id,
                lender_name="ICICI Bank",
                principal_amount=Decimal("200000.00"),
                interest_rate=Decimal("10.50"),
                interest_type=InterestType.FIXED,
                term_months=24,
                start_date=today - timedelta(days=60),
                notes="Home Renovation Loan",
            ),
        )
        print("Created loan debt obligation with monthly amortization schedule.")

        # 9. Securities & Investments
        # Find or create an equity asset
        nifty_asset = session.query(InvestmentAsset).filter(InvestmentAsset.symbol == "NIFTYBEES").first()
        if not nifty_asset:
            nifty_asset = InvestmentAsset(
                symbol="NIFTYBEES",
                name="Nippon India ETF Nifty 50 BeES",
                asset_type=AssetType.ETF,
                exchange="NSE",
                currency="INR",
                current_price=Decimal("260.00"),
                is_active=True,
            )
            session.add(nifty_asset)
            session.commit()
            session.refresh(nifty_asset)

        # Execute purchase trade: Buy 100 units of NIFTYBEES @ ₹250.00
        inv_service.buy_asset(
            user_id=user_id,
            payload=InvestmentBuyRequest(
                account_id=inv_acc_id,
                asset_id=nifty_asset.id,
                quantity=Decimal("100.0000"),
                price_per_unit=Decimal("250.00"),
                fees=Decimal("25.00"),
                transaction_date=today - timedelta(days=7),
                notes="SIP purchase of Nifty 50 ETF",
            ),
        )

        # Record dividend receipt: ₹350.00
        inv_service.record_dividend(
            user_id=user_id,
            account_id=inv_acc_id,
            asset_id=nifty_asset.id,
            amount=Decimal("350.00"),
            transaction_date=today - timedelta(days=2),
            notes="Quarterly interim distribution",
        )
        print("Executed investment security purchase and recorded dividend receipt.")

    print("=== Recruiter Portfolio Demo Dataset Successfully Seeded! ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed recruiter portfolio demo dataset")
    parser.add_argument(
        "--rotate-password",
        action="store_true",
        help="Rotate demo user password using RECRUITER_DEMO_PASSWORD or secure generation",
    )
    args = parser.parse_args()
    seed_recruiter_demo(rotate_password=args.rotate_password)
