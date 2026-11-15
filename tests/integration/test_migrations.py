"""Integration tests verifying Alembic migration upgrades, downgrades, and schema reflection."""

import os
import sqlite3
import tempfile
from collections.abc import Generator

import pytest

from alembic import command
from alembic.config import Config


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    """Provide a temporary SQLite database path and clean it up after testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    yield path

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def test_alembic_upgrade_downgrade_cycle(temp_db_path: str) -> None:
    """Verify that Alembic migrations upgrade to head, downgrade cleanly, and re-upgrade."""
    # Configure alembic to target the temporary database
    norm_path = os.path.abspath(temp_db_path).replace("\\", "/")
    os.environ["DATABASE_URL"] = f"sqlite:///{norm_path}"
    cfg = Config("alembic.ini")

    # 1. Upgrade from empty database to HEAD
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_head = {r[0] for r in cur.fetchall()}

    expected_tables = {
        "alembic_version",
        "users",
        "financial_accounts",
        "categories",
        "transactions",
        "transaction_entries",
        "budgets",
        "savings_goals",
        "loan_debts",
        "loan_payment_schedules",
        "recurring_rules",
        "investment_assets",
        "investment_holdings",
        "investment_transactions",
        "audit_logs",
    }
    assert expected_tables.issubset(tables_head), f"Missing tables: {expected_tables - tables_head}"

    # 2. Downgrade to Phase 1 head (fba246fe5321)
    command.downgrade(cfg, "fba246fe5321")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_phase1 = {r[0] for r in cur.fetchall()}

    phase2_tables = {
        "categories",
        "transactions",
        "transaction_entries",
        "budgets",
        "savings_goals",
        "loan_debts",
        "loan_payment_schedules",
        "recurring_rules",
        "investment_assets",
        "investment_holdings",
        "investment_transactions",
        "audit_logs",
    }
    for t in phase2_tables:
        assert t not in tables_phase1, f"Table {t} was not dropped during downgrade"

    assert "users" in tables_phase1
    assert "financial_accounts" in tables_phase1

    # 3. Re-upgrade to HEAD
    command.upgrade(cfg, "head")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_reup = {r[0] for r in cur.fetchall()}
    assert expected_tables.issubset(tables_reup)

    conn.close()
    # Reset environment variable
    os.environ.pop("DATABASE_URL", None)
