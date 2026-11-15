"""Unit tests verifying Phase 2 SQLAlchemy relational models, constraints, and relationships."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import (
    AccountType,
    AssetType,
    AuditLog,
    Budget,
    Category,
    CategoryType,
    EntryType,
    FinancialAccount,
    Frequency,
    InterestType,
    InvestmentAsset,
    InvestmentHolding,
    InvestmentTransaction,
    InvestmentTxType,
    LoanDebt,
    LoanPaymentSchedule,
    RecurringRule,
    SavingsGoal,
    Transaction,
    TransactionEntry,
    TransactionType,
    User,
)


def test_category_hierarchy_and_uniqueness(db_session: Session, sample_user: User) -> None:
    """Verify Category self-referential hierarchy, types, and uniqueness."""
    parent = Category(
        user_id=sample_user.id,
        name="Transportation",
        category_type=CategoryType.EXPENSE,
        color="#3b82f6",
    )
    db_session.add(parent)
    db_session.flush()

    sub = Category(
        user_id=sample_user.id,
        name="Fuel",
        category_type=CategoryType.EXPENSE,
        parent_id=parent.id,
        color="#60a5fa",
    )
    db_session.add(sub)
    db_session.flush()

    assert sub.parent is not None
    assert sub.parent.id == parent.id
    assert len(parent.subcategories) == 1
    assert parent.subcategories[0].name == "Fuel"

    # Test uniqueness constraint (user_id, name, parent_id)
    duplicate_sub = Category(
        user_id=sample_user.id,
        name="Fuel",
        category_type=CategoryType.EXPENSE,
        parent_id=parent.id,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(duplicate_sub)
            db_session.flush()


def test_transaction_double_entry_and_cascade(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify Transaction and double-entry TransactionEntry balanced structure and cascade delete."""
    # Create second account for transfer
    savings = FinancialAccount(
        user_id=sample_user.id,
        name="Savings Account",
        account_type=AccountType.SAVINGS,
        currency="INR",
        opening_balance=Decimal("10000.00"),
    )
    db_session.add(savings)
    db_session.flush()

    tx = Transaction(
        user_id=sample_user.id,
        transaction_date=date.today(),
        transaction_type=TransactionType.TRANSFER,
        description="Transfer to Savings",
        amount=Decimal("2000.00"),
        currency="INR",
    )
    db_session.add(tx)
    db_session.flush()

    # Credit checking (outflow)
    entry_credit = TransactionEntry(
        transaction_id=tx.id,
        account_id=sample_account.id,
        entry_type=EntryType.CREDIT,
        amount=Decimal("2000.00"),
        currency="INR",
    )
    # Debit savings (inflow)
    entry_debit = TransactionEntry(
        transaction_id=tx.id,
        account_id=savings.id,
        entry_type=EntryType.DEBIT,
        amount=Decimal("2000.00"),
        currency="INR",
    )
    db_session.add_all([entry_credit, entry_debit])
    db_session.flush()

    assert len(tx.entries) == 2
    assert entry_credit.account.name == sample_account.name
    assert entry_debit.account.name == savings.name

    # Verify cascade delete: deleting transaction deletes entries
    tx_id = tx.id
    db_session.delete(tx)
    db_session.flush()

    assert db_session.get(Transaction, tx_id) is None
    assert db_session.get(TransactionEntry, entry_credit.id) is None
    assert db_session.get(TransactionEntry, entry_debit.id) is None


def test_transaction_positive_amount_constraint(db_session: Session, sample_user: User) -> None:
    """Verify check constraint rejects zero or negative amounts on Transaction."""
    tx = Transaction(
        user_id=sample_user.id,
        transaction_date=date.today(),
        transaction_type=TransactionType.EXPENSE,
        description="Invalid Zero Tx",
        amount=Decimal("0.00"),
        currency="INR",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(tx)
            db_session.flush()


def test_transaction_entry_restrict_account_deletion(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify ondelete='RESTRICT' prevents deleting account when transaction entries exist."""
    tx = Transaction(
        user_id=sample_user.id,
        transaction_date=date.today(),
        transaction_type=TransactionType.EXPENSE,
        description="Groceries",
        amount=Decimal("500.00"),
        currency="INR",
    )
    db_session.add(tx)
    db_session.flush()

    entry = TransactionEntry(
        transaction_id=tx.id,
        account_id=sample_account.id,
        entry_type=EntryType.CREDIT,
        amount=Decimal("500.00"),
        currency="INR",
    )
    db_session.add(entry)
    db_session.flush()

    # Attempting to delete the account must fail due to foreign key RESTRICT
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.delete(sample_account)
            db_session.flush()


def test_budget_constraints_and_uniqueness(db_session: Session, sample_user: User) -> None:
    """Verify Budget period uniqueness and month check constraint."""
    cat = Category(
        user_id=sample_user.id,
        name="Groceries",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add(cat)
    db_session.flush()

    budget = Budget(
        user_id=sample_user.id,
        category_id=cat.id,
        month=11,
        year=2026,
        amount=Decimal("15000.00"),
    )
    db_session.add(budget)
    db_session.flush()

    # Duplicate period budget should raise IntegrityError
    dup = Budget(
        user_id=sample_user.id,
        category_id=cat.id,
        month=11,
        year=2026,
        amount=Decimal("20000.00"),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(dup)
            db_session.flush()

    # Month out of range (month > 12)
    invalid_month = Budget(
        user_id=sample_user.id,
        category_id=cat.id,
        month=13,
        year=2026,
        amount=Decimal("1000.00"),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(invalid_month)
            db_session.flush()


def test_savings_goal_constraints(db_session: Session, sample_user: User) -> None:
    """Verify SavingsGoal non-negative and positive target constraints."""
    goal = SavingsGoal(
        user_id=sample_user.id,
        name="Vacation Fund",
        target_amount=Decimal("50000.00"),
        current_amount=Decimal("10000.00"),
        currency="INR",
        target_date=date(2027, 3, 31),
    )
    db_session.add(goal)
    db_session.flush()

    assert goal.is_achieved is False
    assert goal.current_amount == Decimal("10000.00")

    # Target amount <= 0 check constraint
    invalid_target = SavingsGoal(
        user_id=sample_user.id,
        name="Invalid Goal",
        target_amount=Decimal("0.00"),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(invalid_target)
            db_session.flush()


def test_loan_debt_and_payment_schedule(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify LoanDebt obligations, payment schedules, and cascade deletion."""
    loan = LoanDebt(
        user_id=sample_user.id,
        account_id=sample_account.id,
        lender_name="HDFC Bank",
        principal_amount=Decimal("500000.00"),
        remaining_balance=Decimal("480000.00"),
        interest_rate=Decimal("8.50"),
        interest_type=InterestType.FIXED,
        term_months=60,
        minimum_monthly_payment=Decimal("10258.00"),
        start_date=date(2026, 1, 1),
    )
    db_session.add(loan)
    db_session.flush()

    # Schedule instalment 1
    sched = LoanPaymentSchedule(
        loan_id=loan.id,
        payment_number=1,
        due_date=date(2026, 2, 1),
        principal_component=Decimal("6716.00"),
        interest_component=Decimal("3542.00"),
        total_payment=Decimal("10258.00"),
        remaining_balance=Decimal("493284.00"),
        is_paid=True,
    )
    db_session.add(sched)
    db_session.flush()

    assert len(loan.payment_schedules) == 1
    assert loan.payment_schedules[0].payment_number == 1

    # Unique constraint (loan_id, payment_number)
    dup_sched = LoanPaymentSchedule(
        loan_id=loan.id,
        payment_number=1,
        due_date=date(2026, 3, 1),
        principal_component=Decimal("6750.00"),
        interest_component=Decimal("3508.00"),
        total_payment=Decimal("10258.00"),
        remaining_balance=Decimal("486534.00"),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(dup_sched)
            db_session.flush()


def test_recurring_rule_model(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify RecurringRule model creation and constraints."""
    rule = RecurringRule(
        user_id=sample_user.id,
        account_id=sample_account.id,
        name="Broadband Internet Bill",
        amount=Decimal("999.00"),
        currency="INR",
        transaction_type=TransactionType.EXPENSE,
        frequency=Frequency.MONTHLY,
        interval=1,
        start_date=date(2026, 1, 1),
        next_occurrence=date(2026, 12, 1),
        is_active=True,
    )
    db_session.add(rule)
    db_session.flush()

    assert rule.frequency == Frequency.MONTHLY
    assert rule.account.name == sample_account.name


def test_investment_models_precision_and_holdings(
    db_session: Session, sample_user: User, sample_account: FinancialAccount
) -> None:
    """Verify InvestmentAsset, 4-decimal quantity on InvestmentHolding, and InvestmentTransaction."""
    asset = InvestmentAsset(
        symbol="TCS",
        name="Tata Consultancy Services Ltd",
        asset_type=AssetType.EQUITY,
        isin="INE467B01029",
        exchange="NSE",
        currency="INR",
        current_price=Decimal("4120.50"),
    )
    db_session.add(asset)
    db_session.flush()

    holding = InvestmentHolding(
        user_id=sample_user.id,
        account_id=sample_account.id,
        asset_id=asset.id,
        quantity=Decimal("25.5432"),  # 4-decimal precision
        cost_basis_per_unit=Decimal("3950.00"),
        total_cost=Decimal("100895.64"),
        currency="INR",
    )
    db_session.add(holding)
    db_session.flush()

    assert holding.quantity == Decimal("25.5432")
    assert holding.asset.symbol == "TCS"

    # Test unique constraint on (user_id, account_id, asset_id)
    dup_holding = InvestmentHolding(
        user_id=sample_user.id,
        account_id=sample_account.id,
        asset_id=asset.id,
        quantity=Decimal("10.0000"),
        cost_basis_per_unit=Decimal("4000.00"),
        total_cost=Decimal("40000.00"),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(dup_holding)
            db_session.flush()

    # InvestmentTransaction test
    inv_tx = InvestmentTransaction(
        user_id=sample_user.id,
        account_id=sample_account.id,
        asset_id=asset.id,
        transaction_type=InvestmentTxType.BUY,
        transaction_date=date.today(),
        quantity=Decimal("10.0000"),
        price_per_unit=Decimal("4000.00"),
        total_amount=Decimal("40000.00"),
        fees=Decimal("80.00"),
        currency="INR",
    )
    db_session.add(inv_tx)
    db_session.flush()

    assert inv_tx.asset.symbol == "TCS"
    assert inv_tx.transaction_type == InvestmentTxType.BUY


def test_audit_log_model(db_session: Session, sample_user: User) -> None:
    """Verify AuditLog immutable logging record."""
    log = AuditLog(
        user_id=sample_user.id,
        action="UPDATE",
        entity_name="FinancialAccount",
        entity_id="acc-123",
        old_values='{"opening_balance": "1000.00"}',
        new_values='{"opening_balance": "1500.00"}',
        ip_address="127.0.0.1",
        user_agent="pytest-client",
        created_at=datetime.utcnow(),
    )
    db_session.add(log)
    db_session.flush()

    assert log.entity_name == "FinancialAccount"
    assert log.action == "UPDATE"
    assert log.user.id == sample_user.id
