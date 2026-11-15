"""Pytest fixtures for database, FastAPI test client, and domain models."""

import os
import sys

# Ensure project root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.api.dependencies import get_db
from src.api.main import app
from src.db.base import Base
from src.db.models import AccountType, FinancialAccount, User

# Use an in-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# Enforce foreign key constraints in SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    """Create all database tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Yield a transactional database session with default user seeded."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Ensure default user exists for API endpoints targeting default-user-id
    default_user = session.get(User, "default-user-id")
    if not default_user:
        default_user = User(
            id="default-user-id",
            email="default@user.dev",
            name="Default Test User",
        )
        session.add(default_user)
        session.flush()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Yield a FastAPI TestClient with overridden get_db dependency."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Fixture providing a persisted test User entity."""
    user = User(
        id="test-user-123",
        email="test@user.dev",
        name="Test User",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def sample_account(db_session: Session, sample_user: User) -> FinancialAccount:
    """Fixture providing a persisted test FinancialAccount entity."""
    account = FinancialAccount(
        user_id=sample_user.id,
        name="Test Checking",
        account_type=AccountType.CHECKING,
        institution_name="Test Bank",
        currency="USD",
        opening_balance=Decimal("2500.50"),
        is_active=True,
    )
    db_session.add(account)
    db_session.flush()
    return account
