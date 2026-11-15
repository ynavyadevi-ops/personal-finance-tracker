# Personal Finance Tracker — System Architecture & Technical Design

> **DOCUMENT**: `docs/ARCHITECTURE.md`  
> **STATUS**: APPROVED BASELINE  
> **STACK**: Python 3.12 + SQL (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 4 — FastAPI REST API & Data Portability Services (COMPLETED)

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
│   │       ├── goals.py
│   │       ├── loans.py
│   │       ├── investments.py
│   │       ├── recurring.py
│   │       ├── data_portability.py
│   │       └── health.py
│   ├── core/                     # Cross-Cutting Concerns
│   │   ├── config.py             # Pydantic BaseSettings (.env loading & validation)
│   │   ├── security.py           # Password hashing (Argon2id) & JWT handling (HS256)
│   │   ├── exceptions.py         # Custom domain exceptions & HTTP mappings
│   │   ├── logging.py            # Structured JSON logger configuration
│   │   └── money.py              # Decimal monetary utilities (rounding, formatting)
│   ├── db/                       # Database & ORM
│   │   ├── session.py            # SQLAlchemy engine, sessionmaker, and base
│   │   ├── base.py               # DeclarativeBase with common timestamp mixins
│   │   ├── seed.py               # Development seeder (categories, default user, demo assets)
│   │   └── models/               # SQLAlchemy 2.0 ORM Models
│   │       ├── user.py
│   │       ├── account.py
│   │       ├── category.py
│   │       ├── transaction.py
│   │       ├── budget.py
│   │       ├── goal.py
│   │       ├── loan.py
│   │       ├── recurring.py
│   │       ├── investment.py
│   │       └── audit.py
│   ├── repositories/             # Data Access Layer (SQLAlchemy queries & tenant scoping)
│   │   ├── base.py
│   │   ├── account_repo.py
│   │   ├── category_repo.py
│   │   ├── transaction_repo.py
│   │   ├── budget_repo.py
│   │   ├── goal_repo.py
│   │   ├── loan_repo.py
│   │   ├── recurring_repo.py
│   │   └── investment_repo.py
│   ├── services/                 # Domain Business Logic Layer
│   │   ├── account_service.py    # Protected account CRUD & archiving
│   │   ├── ledger_service.py     # Double-entry invariant validation & reconciliation
│   │   ├── transaction_service.py # Income, expense, and atomic transfer execution
│   │   ├── budget_service.py     # Budget allocations, monthly spending & rollovers
│   │   ├── goal_service.py       # Savings milestones, contributions & progress
│   │   ├── loan_service.py       # Amortization schedules & loan repayments
│   │   ├── recurring_service.py  # Recurring rules, next dates & automated spawning
│   │   ├── investment_service.py # Trades, weighted cost basis & realized P&L
│   │   └── portability_service.py # Statement CSV/XLSX import, export & backup validation
│   ├── schemas/                  # Pydantic v2 DTOs (Request / Response validation)
│   │   ├── common.py             # GenericResponse[T], PaginationParams
│   │   ├── user.py               # Auth & profile schemas
│   │   ├── account.py
│   │   ├── category.py
│   │   ├── transaction.py
│   │   ├── budget.py
│   │   ├── goal.py
│   │   ├── loan.py
│   │   ├── recurring.py
│   │   ├── investment.py
│   │   └── portability.py        # Import/export/backup schemas
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

### Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    users ||--o{ financial_accounts : "owns"
    users ||--o{ categories : "creates"
    users ||--o{ transactions : "records"
    users ||--o{ budgets : "sets"
    users ||--o{ savings_goals : "tracks"
    users ||--o{ loan_debts : "owes"
    users ||--o{ recurring_rules : "configures"
    users ||--o{ investment_holdings : "holds"
    users ||--o{ investment_transactions : "executes"
    users ||--o{ audit_logs : "generates"

    financial_accounts ||--o{ transaction_entries : "ledger entries"
    financial_accounts ||--o{ loan_debts : "tied loan"
    financial_accounts ||--o{ recurring_rules : "source account"
    financial_accounts ||--o{ investment_holdings : "portfolio holdings"
    financial_accounts ||--o{ investment_transactions : "clearing account"

    categories ||--o{ categories : "subcategories (self-ref)"
    categories ||--o{ transaction_entries : "categorizes"
    categories ||--o{ budgets : "budget allocation"

    transactions ||--o{ transaction_entries : "balanced double-entries"
    recurring_rules ||--o{ transactions : "spawns"

    loan_debts ||--o{ loan_payment_schedules : "amortization instalments"
    transactions ||--o| loan_payment_schedules : "settlement transaction"

    investment_assets ||--o{ investment_holdings : "positions"
    investment_assets ||--o{ investment_transactions : "asset trades"
    transactions ||--o| investment_transactions : "cash leg"
```

### Database Tables & Schema Specifications

The relational schema comprises 12 domain tables plus Alembic migration version tracking:

1. **`users`**
   - Core tenant record.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Fields: `email` (`VARCHAR(255)`, unique, nullable for local dev), `name` (`VARCHAR(100)`).
   - Cascades: Deleting a user cascades to all associated accounts, categories, transactions, budgets, goals, loans, rules, holdings, and audit logs.

2. **`financial_accounts`**
   - Depository, credit, investment, or loan accounts.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`).
   - Fields: `name` (`VARCHAR(100)`), `account_type` (`ENUM`: `CHECKING`, `SAVINGS`, `CREDIT_CARD`, `CASH`, `INVESTMENT`, `LOAN`), `institution_name` (`VARCHAR(100)`), `currency` (`VARCHAR(3)`, default `"INR"`), `opening_balance` (`NUMERIC(18, 2)`), `is_active` (`BOOLEAN`).
   - Protection: Deletion is `RESTRICT`ed if referenced by `transaction_entries`, `loan_debts`, `investment_holdings`, or `investment_transactions`.

3. **`categories`**
   - Hierarchical transaction classification with self-referential nesting.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`, nullable for system defaults), `parent_id` -> `categories.id` (`ON DELETE CASCADE`).
   - Fields: `name` (`VARCHAR(100)`), `category_type` (`ENUM`: `INCOME`, `EXPENSE`), `color` (`VARCHAR(7)`), `icon` (`VARCHAR(50)`), `is_default` (`BOOLEAN`).
   - Constraints: `uq_categories_user_name_parent` (`UNIQUE(user_id, name, parent_id)`).

4. **`transactions`**
   - Business transaction events (income, expense, or inter-account transfer).
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`), `recurring_rule_id` -> `recurring_rules.id` (`ON DELETE SET NULL`).
   - Fields: `transaction_date` (`DATE`), `transaction_type` (`ENUM`: `INCOME`, `EXPENSE`, `TRANSFER`), `description` (`VARCHAR(255)`), `amount` (`NUMERIC(18, 2)`), `currency` (`VARCHAR(3)`), `notes` (`VARCHAR(500)`), `tags` (`VARCHAR(255)`).
   - Constraints: `chk_transactions_positive_amount` (`amount > 0`).

5. **`transaction_entries`**
   - Balanced double-entry ledger line items associated with financial accounts.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `transaction_id` -> `transactions.id` (`ON DELETE CASCADE`), `account_id` -> `financial_accounts.id` (`ON DELETE RESTRICT`), `category_id` -> `categories.id` (`ON DELETE SET NULL`).
   - Fields: `entry_type` (`ENUM`: `DEBIT`, `CREDIT`), `amount` (`NUMERIC(18, 2)`), `currency` (`VARCHAR(3)`), `notes` (`VARCHAR(255)`).
   - Constraints: `chk_transaction_entries_positive_amount` (`amount > 0`).

6. **`budgets`**
   - Monthly category spending allocations.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`), `category_id` -> `categories.id` (`ON DELETE CASCADE`).
   - Fields: `month` (`INTEGER`), `year` (`INTEGER`), `amount` (`NUMERIC(18, 2)`), `rollover_enabled` (`BOOLEAN`), `notes` (`VARCHAR(255)`).
   - Constraints: `uq_budgets_user_cat_period` (`UNIQUE(user_id, category_id, month, year)`), `chk_budgets_valid_month` (`month >= 1 AND month <= 12`), `chk_budgets_positive_amount` (`amount > 0`).

7. **`savings_goals`**
   - Target savings milestones with progress tracking.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`).
   - Fields: `name` (`VARCHAR(100)`), `target_amount` (`NUMERIC(18, 2)`), `current_amount` (`NUMERIC(18, 2)`), `currency` (`VARCHAR(3)`), `target_date` (`DATE`), `is_achieved` (`BOOLEAN`), `notes` (`VARCHAR(500)`).
   - Constraints: `chk_savings_goals_positive_target` (`target_amount > 0`), `chk_savings_goals_non_negative_current` (`current_amount >= 0`).

8. **`loan_debts`**
   - Liability obligations, interest terms, and repayment tracking.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`), `account_id` -> `financial_accounts.id` (`ON DELETE RESTRICT`).
   - Fields: `lender_name` (`VARCHAR(100)`), `principal_amount` (`NUMERIC(18, 2)`), `remaining_balance` (`NUMERIC(18, 2)`), `interest_rate` (`NUMERIC(5, 2)`), `interest_type` (`ENUM`: `FIXED`, `FLOATING`), `term_months` (`INTEGER`), `minimum_monthly_payment` (`NUMERIC(18, 2)`), `start_date` (`DATE`), `due_date` (`DATE`), `is_settled` (`BOOLEAN`), `notes` (`VARCHAR(500)`).
   - Constraints: `chk_loan_debts_positive_principal` (`principal_amount > 0`), `chk_loan_debts_non_negative_remaining` (`remaining_balance >= 0`), `chk_loan_debts_non_negative_interest` (`interest_rate >= 0`), `chk_loan_debts_positive_term` (`term_months > 0`).

9. **`loan_payment_schedules`**
   - Detailed amortization instalment schedule entries.
   - Primary Key: `id` (`VARCHAR(36)` UUID).
   - Foreign Keys: `loan_id` -> `loan_debts.id` (`ON DELETE CASCADE`), `transaction_id` -> `transactions.id` (`ON DELETE SET NULL`).
   - Fields: `payment_number` (`INTEGER`), `due_date` (`DATE`), `principal_component` (`NUMERIC(18, 2)`), `interest_component` (`NUMERIC(18, 2)`), `total_payment` (`NUMERIC(18, 2)`), `remaining_balance` (`NUMERIC(18, 2)`), `is_paid` (`BOOLEAN`), `paid_date` (`DATE`).
   - Constraints: `uq_loan_schedules_loan_number` (`UNIQUE(loan_id, payment_number)`), `chk_loan_schedules_positive_number` (`payment_number > 0`), `chk_loan_schedules_positive_total` (`total_payment > 0`).

10. **`recurring_rules`**
    - Templates and schedules for recurring bills, income, and automated transfers.
    - Primary Key: `id` (`VARCHAR(36)` UUID).
    - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`), `account_id` -> `financial_accounts.id` (`ON DELETE RESTRICT`), `category_id` -> `categories.id` (`ON DELETE SET NULL`), `destination_account_id` -> `financial_accounts.id` (`ON DELETE SET NULL`).
    - Fields: `name` (`VARCHAR(100)`), `amount` (`NUMERIC(18, 2)`), `currency` (`VARCHAR(3)`), `transaction_type` (`ENUM`: `INCOME`, `EXPENSE`, `TRANSFER`), `frequency` (`ENUM`: `DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`), `interval` (`INTEGER`), `start_date` (`DATE`), `end_date` (`DATE`), `next_occurrence` (`DATE`), `is_active` (`BOOLEAN`), `notes` (`VARCHAR(500)`).
    - Constraints: `chk_recurring_rules_positive_amount` (`amount > 0`), `chk_recurring_rules_positive_interval` (`"interval" > 0`).

11. **`investment_assets`**
    - Master catalog of tradeable securities and assets.
    - Primary Key: `id` (`VARCHAR(36)` UUID).
    - Fields: `symbol` (`VARCHAR(20)`, unique), `name` (`VARCHAR(150)`), `asset_type` (`ENUM`: `EQUITY`, `MUTUAL_FUND`, `ETF`, `BOND`, `GOLD`, `CRYPTO`, `OTHER`), `isin` (`VARCHAR(12)`, unique), `exchange` (`VARCHAR(20)`), `currency` (`VARCHAR(3)`), `current_price` (`NUMERIC(18, 2)`), `last_price_update` (`DATETIME`), `is_active` (`BOOLEAN`).

12. **`investment_holdings`**
    - User holdings in securities within designated investment accounts.
    - Primary Key: `id` (`VARCHAR(36)` UUID).
    - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`), `account_id` -> `financial_accounts.id` (`ON DELETE RESTRICT`), `asset_id` -> `investment_assets.id` (`ON DELETE RESTRICT`).
    - Fields: `quantity` (`NUMERIC(18, 4)` for fractional shares and mutual fund units), `cost_basis_per_unit` (`NUMERIC(18, 2)`), `total_cost` (`NUMERIC(18, 2)`), `current_value` (`NUMERIC(18, 2)`), `currency` (`VARCHAR(3)`).
    - Constraints: `uq_holdings_user_acc_asset` (`UNIQUE(user_id, account_id, asset_id)`), `chk_holdings_non_negative_qty` (`quantity >= 0`), `chk_holdings_non_negative_cost_basis` (`cost_basis_per_unit >= 0`), `chk_holdings_non_negative_total_cost` (`total_cost >= 0`).

13. **`investment_transactions`**
    - Ledger of security purchase, sale, dividend, split, and interest operations.
    - Primary Key: `id` (`VARCHAR(36)` UUID).
    - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`), `account_id` -> `financial_accounts.id` (`ON DELETE RESTRICT`), `asset_id` -> `investment_assets.id` (`ON DELETE RESTRICT`), `related_transaction_id` -> `transactions.id` (`ON DELETE SET NULL`).
    - Fields: `transaction_type` (`ENUM`: `BUY`, `SELL`, `DIVIDEND`, `SPLIT`, `INTEREST`), `transaction_date` (`DATE`), `quantity` (`NUMERIC(18, 4)`), `price_per_unit` (`NUMERIC(18, 2)`), `total_amount` (`NUMERIC(18, 2)`), `fees` (`NUMERIC(18, 2)`), `currency` (`VARCHAR(3)`), `notes` (`VARCHAR(500)`).
    - Constraints: `chk_inv_tx_non_negative_qty` (`quantity >= 0`), `chk_inv_tx_non_negative_price` (`price_per_unit >= 0`), `chk_inv_tx_non_negative_amount` (`total_amount >= 0`), `chk_inv_tx_non_negative_fees` (`fees >= 0`).

14. **`audit_logs`**
    - Append-only immutable log of state mutations.
    - Primary Key: `id` (`VARCHAR(36)` UUID).
    - Foreign Keys: `user_id` -> `users.id` (`ON DELETE CASCADE`).
    - Fields: `action` (`VARCHAR(50)`), `entity_name` (`VARCHAR(50)`), `entity_id` (`VARCHAR(36)`), `old_values` (`VARCHAR(2000)` JSON string), `new_values` (`VARCHAR(2000)` JSON string), `ip_address` (`VARCHAR(45)`), `user_agent` (`VARCHAR(255)`), `created_at` (`DATETIME`).

---

## 6. Financial Precision & Decimal-Safe Monetary Handling

To prevent precision loss from IEEE 754 floating-point math:
1. **Python Decimal**: All monetary calculations in services and utilities use Python's built-in `decimal.Decimal` module:
   ```python
   from decimal import Decimal, ROUND_HALF_EVEN

   def round_currency(value: Decimal) -> Decimal:
       return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
   ```
2. **Database Mapping**: In SQLAlchemy, all currency amounts are stored as `Numeric(18, 2)`. Investment quantities use `Numeric(18, 4)` to support fractional shares, mutual fund units, and precious metal gram weights.
3. **Pydantic Validation**: All transaction and account schemas validate monetary inputs using strict Pydantic Decimal validators that reject unrounded non-decimal floats.

---

## 7. Database Transactions & Double-Entry Accounting

- **Transaction Scope**: Database writes are wrapped in atomic transaction contexts (`session.begin()`).
- **Double-Entry Ledger Architecture**:
  Every financial business event (`Transaction`) is backed by balanced `TransactionEntry` ledger lines:
  - **Expense**: 1 `CREDIT` entry reducing account balance; 1 expense categorization line.
  - **Income**: 1 `DEBIT` entry increasing account balance; 1 income categorization line.
  - **Transfer**: 1 `CREDIT` entry reducing source account; 1 `DEBIT` entry increasing destination account.
  - **Ledger Invariant**: Total debits equal total credits for every balanced transaction event.
  - If an exception occurs during ledger creation or balance adjustment, the atomic database transaction automatically rolls back.

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
