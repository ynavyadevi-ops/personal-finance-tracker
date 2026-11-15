# Personal Finance Tracker — System Architecture & Technical Design

> **DOCUMENT**: `docs/ARCHITECTURE.md`  
> **STATUS**: APPROVED BASELINE  
> **STACK**: Python 3.12 + SQL (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation

---

## 1. High-Level Architectural Overview

The **Personal Finance Tracker** is engineered as a decoupled, multi-tier system built entirely in Python:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND UI (STREAMLIT)                         │
│  Multi-Page Streamlit App (src/frontend) • Interactive Plotly Charts   │
│  st.session_state • Fast Reactive Forms • HTTPX Asynchronous Client    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (/api/v1)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       BACKEND API (FASTAPI)                            │
│  FastAPI (src/api) • Uvicorn ASGI • Pydantic v2 Request Validation     │
│  Dependency Injection (DB Session, Auth) • Structured Error Handling   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Direct Invocations
┌───────────────────────────────────▼────────────────────────────────────┐
│                        DOMAIN SERVICES LAYER                           │
│  AccountService • TransactionService • BudgetService • AnalyticsService│
│  Decimal-Safe Monetary Engine (Python decimal.Decimal)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Abstracted Data Access
┌───────────────────────────────────▼────────────────────────────────────┐
│                    REPOSITORY & PERSISTENCE LAYER                      │
│  SQLAlchemy 2.0 (Async/Sync Sessions) • Generic Repository Pattern     │
│  Atomic Transactions (session.begin()) • Tenant Scoping (user_id)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
        [ Local Development ]                [ Production Cloud ]
         SQLite (data/finance.db)             PostgreSQL 16+
         aiosqlite driver                     asyncpg / psycopg driver
```

---

## 2. Directory Structure & Modular Layout

```
personal-expense-tracker/
├── src/
│   ├── api/                      # FastAPI Backend Application
│   │   ├── main.py               # Application factory, lifespan, CORS, middleware
│   │   ├── dependencies.py       # FastAPI dependency injection (DB sessions, auth)
│   │   └── routers/              # Modular API endpoints (/api/v1)
│   │       ├── auth.py
│   │       ├── accounts.py
│   │       ├── transactions.py
│   │       ├── budgets.py
│   │       └── analytics.py
│   ├── core/                     # Cross-Cutting Concerns
│   │   ├── config.py             # Pydantic BaseSettings (.env loading & validation)
│   │   ├── security.py           # Password hashing (Argon2id/bcrypt) & JWT handling
│   │   ├── exceptions.py         # Custom domain exceptions & HTTP mappings
│   │   ├── logging.py            # Structured JSON logger configuration
│   │   └── money.py              # Decimal monetary utilities (rounding, formatting)
│   ├── db/                       # Database & ORM
│   │   ├── session.py            # SQLAlchemy engine, sessionmaker, and base
│   │   ├── base.py               # DeclarativeBase with common timestamp mixins
│   │   └── models/               # SQLAlchemy ORM Models
│   │       ├── user.py
│   │       ├── account.py
│   │       ├── category.py
│   │       ├── transaction.py
│   │       ├── budget.py
│   │       ├── recurring.py
│   │       └── audit.py
│   ├── repositories/             # Data Access Layer (SQLAlchemy queries)
│   │   ├── base.py               # Generic repository interface
│   │   ├── account_repo.py
│   │   ├── transaction_repo.py
│   │   └── budget_repo.py
│   ├── services/                 # Domain Business Logic
│   │   ├── account_service.py
│   │   ├── transaction_service.py
│   │   ├── budget_service.py
│   │   └── analytics_service.py
│   ├── schemas/                  # Pydantic v2 DTOs (Request / Response)
│   │   ├── common.py             # GenericResponse[T], PaginationParams
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── budget.py
│   │   └── analytics.py
│   └── frontend/                 # Streamlit User Interface
│       ├── app.py                # Streamlit entry point (navigation, auth shell)
│       ├── api_client.py         # HTTPX client communicating with FastAPI
│       ├── state.py              # Session state helpers (user session, active tab)
│       ├── components/           # Reusable UI widgets & Plotly charts
│       │   ├── charts.py         # Plotly figure builders
│       │   ├── forms.py          # Data entry forms
│       │   └── tables.py         # Formatted data tables
│       └── pages/                # Multi-page views
│           ├── 1_Dashboard.py
│           ├── 2_Accounts.py
│           ├── 3_Transactions.py
│           ├── 4_Budgets.py
│           └── 5_Reports.py
├── alembic/                      # Database Schema Migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/                        # Automated Test Suite (Pytest)
│   ├── conftest.py               # Test DB fixtures, mock client
│   ├── unit/                     # Domain & financial calculation tests
│   ├── integration/              # FastAPI route tests via HTTPX AsyncClient
│   └── security/                 # Security tests (injection, tenant isolation)
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project metadata, dependencies, tool configs
└── README.md
```

---

## 3. Frontend Architecture (Streamlit)

### Multi-Page Reactive Structure
- Streamlit serves as an interactive, reactive presentation layer.
- **Entrypoint (`src/frontend/app.py`)**: Renders the application shell, authentication barrier, and sidebar navigation.
- **Pages Directory (`src/frontend/pages/`)**: Modular pages for Accounts, Transactions, Budgets, and Analytics.
- **Decoupled API Client (`src/frontend/api_client.py`)**: Streamlit components DO NOT interact directly with SQLAlchemy models or the database. All operations call the FastAPI backend via an asynchronous `httpx.AsyncClient` wrapper. This cleanly separates UI logic from data persistence and enforces identical security rules across any potential future client (mobile app, CLI).

### State Management & Caching
- **Session State (`st.session_state`)**: Tracks current user credentials, active filters, form draft states, and notifications.
- **Performance Caching**:
  - `@st.cache_data(ttl=60)` caches heavy analytical aggregations and static category metadata.
  - Mutations (adding a transaction) invalidate relevant caches via explicit cache clear keys.

### Data Visualizations (Plotly + Pandas)
- Analytical data fetched from FastAPI is converted into Pandas DataFrames.
- **Plotly Express / Graph Objects** render high-fidelity, interactive charts:
  - Donut charts for category expense distribution.
  - Multi-series bar charts for Income vs. Expense comparisons.
  - Area charts for historical Net Worth progression.

---

## 4. Backend Architecture (FastAPI)

### Application Factory & Lifespan
- Built using FastAPI’s async `lifespan` handler to manage database engine startup, connection pool warmup, and graceful shutdown.
- Cross-Origin Resource Sharing (CORS) restricted to trusted origins via `CORSMiddleware`.
- Standardized request correlation ID middleware (`X-Request-ID`) attached to all incoming requests and structured log entries.

### Dependency Injection
FastAPI’s `Depends` system provides clean, testable injection:
- `get_db()`: Yields an async/sync SQLAlchemy database session bound to the request lifespan with automatic rollback on unhandled exceptions.
- `get_current_user()`: Decodes JWT bearer tokens, checks token revocation, and yields the authenticated `User` context.

### Standardized API Envelope
All FastAPI endpoints return a uniform response envelope:
```python
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class GenericResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[dict] = None
    meta: Optional[dict] = None
```

---

## 5. Database Architecture & SQLAlchemy Layer

### Database Models

```python
import enum
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, DateTime, Date, Numeric, Boolean, ForeignKey, Index, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class AccountType(str, enum.Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT_CARD = "CREDIT_CARD"
    CASH = "CASH"
    INVESTMENT = "INVESTMENT"
    LOAN = "LOAN"

class TransactionType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts: Mapped[List["Account"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[List["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[List["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="account")

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#64748b")
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="categories")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[List["Budget"]] = relationship(back_populates="category")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    payee: Mapped[Optional[str]] = mapped_column(String(150))
    notes: Mapped[Optional[str]] = mapped_column(String(500))
    tags: Mapped[Optional[str]] = mapped_column(String(200)) # Comma-separated tags
    
    # Linked transfer tracking
    linked_transaction_id: Mapped[Optional[str]] = mapped_column(String(36), unique=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped[Optional["Category"]] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_account_date", "account_id", "date"),
    )

class Budget(Base):
    __tablename__ = "budgets"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False)
    month: Mapped[int] = mapped_column(nullable=False) # 1 - 12
    year: Mapped[int] = mapped_column(nullable=False)  # e.g., 2026
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category"] = relationship(back_populates="budgets")

    __table_args__ = (
        Index("ix_budgets_unique_period", "user_id", "category_id", "month", "year", unique=True),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False) # CREATE, UPDATE, DELETE, TRANSFER
    entity: Mapped[str] = mapped_column(String(50), nullable=False) # Account, Transaction, Budget
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[str] = mapped_column(String(1000), nullable=False) # JSON payload string
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## 6. Financial Precision & Decimal-Safe Monetary Handling

To prevent precision loss from IEEE 754 floating-point math:
1. **Python Decimal**: All monetary calculations in services and utilities use Python's built-in `decimal.Decimal` module:
   ```python
   from decimal import Decimal, ROUND_HALF_EVEN

   def round_currency(value: Decimal) -> Decimal:
       return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
   ```
2. **Database Mapping**: In SQLAlchemy, all monetary columns are defined as `Numeric(18, 2)`. This maps to `NUMERIC(18, 2)` in PostgreSQL and `DECIMAL(18, 2)` in SQLite, completely avoiding floating-point storage.
3. **Pydantic Validation**: All transaction and account schemas validate monetary inputs using `pydantic.condecimal(decimal_places=2, max_digits=18)` or custom validators that reject non-decimal floats.

---

## 7. Database Transactions & Atomic Transfers

- **Transaction Scope**: Database writes are wrapped in atomic transaction contexts.
- **Atomic Transfer Implementation**:
  When a user transfers amount $\$X$ from Account A to Account B, the `TransactionService` creates two paired records inside a single `session.begin()` block:
  1. An `EXPENSE` (or `TRANSFER_OUT`) on Account A of amount $\$X$.
  2. An `INCOME` (or `TRANSFER_IN`) on Account B of amount $\$X$.
  3. Both records reference each other via `linked_transaction_id`.
  If an exception occurs during any step, SQLAlchemy rolls back the entire session, ensuring no funds are created or destroyed.

---

## 8. Multi-User Isolation & Authentication Strategy

### Multi-Tenant Data Scoping
- Every repository method automatically enforces the `user_id` query predicate:
  ```python
  stmt = select(Transaction).where(
      Transaction.user_id == current_user.id,
      Transaction.id == transaction_id
  )
  ```
- Cross-tenant lookups return `404 Not Found`, eliminating information disclosure.

### Authentication Strategy
- **Password Security**: Passwords hashed using **Argon2id** (or bcrypt) via `passlib` with high iteration factors.
- **JWT Session Tokens**: FastAPI issues signed JSON Web Tokens (HMAC-SHA256 or asymmetric Ed25519) with explicit expiration (`exp`), subject (`sub = user_id`), and issuer (`iss`).
- **OAuth2 Password Bearer**: Handled cleanly via FastAPI's native `OAuth2PasswordBearer` dependency.
- **Local Development**: In Phase 0-7, an initial default user seed (`default_user`) is automatically created to facilitate frictionless local development without mandatory cloud registration.

---

## 9. SQLite-to-PostgreSQL Migration Strategy

Zero vendor lock-in to SQLite:
1. **Universal Alembic Migrations**:
   Alembic revision scripts are written using generic SQLAlchemy operations without raw dialect-specific SQL snippets.
2. **Dynamic Configuration via Environment**:
   ```python
   # SQLite (Local Dev)
   DATABASE_URL="sqlite+aiosqlite:///./data/finance.db"

   # PostgreSQL (Production)
   DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/finance_db"
   ```
3. **Migration Verification Utility (`scripts/verify_pg_migration.py`)**:
   A dedicated script exports all tables from SQLite to a validated JSON snapshot and re-ingests them into PostgreSQL, verifying that:
   - Row counts match exactly.
   - Account balances and total net worth match to the exact cent.
   - Foreign keys and constraints pass full validation.

---

## 10. Deployment & Containerization Strategy

- **Multi-Stage Dockerfile**: Builds lightweight images using Python 3.12-slim.
- **Docker Compose (`docker-compose.yml`)**:
  - `fastapi-backend`: Exposes API on port 8000.
  - `streamlit-frontend`: Exposes UI on port 8501.
  - `postgres-db`: PostgreSQL 16 container with persistent volume.
  - `adminer` / `pgadmin`: Optional database management GUI.
- **Production Cloud Readiness**: Stateless container architecture compatible with AWS ECS, GCP Cloud Run, Render, or Railway.
