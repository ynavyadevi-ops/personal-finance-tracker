# Changelog

All notable changes to the **Personal Finance Tracker (Python + SQL)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Phase 3 (Core Accounting Engine, Financial Services & Domain Logic)
- Implement domain transaction service supporting double-entry accounting entries.
- Implement atomic inter-account transfer execution with debit/credit balance adjustment.
- Implement monthly category budget tracking, calculation of utilization percentages, and rollover logic.
- Implement savings goal contribution tracking and progress calculations.
- Implement loan repayment schedules and amortization logic.
- Implement recurring transaction rule processing queue.

---

## [0.3.0] - 2026-11-15 (Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations)

### Added
- **Complete Relational Domain Models (`src/db/models/`)**:
  - `src/db/models/category.py`: `Category` with self-referential hierarchy (`parent_id`), `CategoryType` (`INCOME`, `EXPENSE`), visual colors, icons, and unique constraint `uq_categories_user_name_parent`.
  - `src/db/models/transaction.py`: `Transaction` business events and `TransactionEntry` double-entry ledger line items with `EntryType` (`DEBIT`, `CREDIT`), `TransactionType` (`INCOME`, `EXPENSE`, `TRANSFER`), `ondelete="RESTRICT"` on accounts, and positive amount check constraints (`chk_transactions_positive_amount`, `chk_transaction_entries_positive_amount`).
  - `src/db/models/budget.py`: `Budget` monthly category allocation with month check (`1 <= month <= 12`), positive amount check, and period uniqueness `uq_budgets_user_cat_period`.
  - `src/db/models/goal.py`: `SavingsGoal` milestone tracking with positive target and non-negative current amount check constraints.
  - `src/db/models/loan.py`: `LoanDebt` and `LoanPaymentSchedule` models with `InterestType` (`FIXED`, `FLOATING`), positive principal check, non-negative remaining balance and interest checks, positive term months check, and ordered amortization schedule entries with uniqueness `uq_loan_schedules_loan_number`.
  - `src/db/models/recurring.py`: `RecurringRule` with `Frequency` (`DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`), interval check constraint (`"interval" > 0`), and positive amount check constraint.
  - `src/db/models/investment.py`: Comprehensive investment models:
    - `InvestmentAsset`: Master security catalog with `AssetType` (`EQUITY`, `MUTUAL_FUND`, `ETF`, `BOND`, `GOLD`, `CRYPTO`, `OTHER`), unique symbol and ISIN.
    - `InvestmentHolding`: User positions with 4-decimal quantity precision (`Numeric(18, 4)`), cost basis, total cost, and uniqueness on `(user_id, account_id, asset_id)`.
    - `InvestmentTransaction`: Trade ledger with `InvestmentTxType` (`BUY`, `SELL`, `DIVIDEND`, `SPLIT`, `INTEREST`), linked transaction reference, and non-negative constraints.
  - `src/db/models/audit.py`: `AuditLog` append-only immutable ledger tracking entity mutations, old/new value JSON snapshots, user IP address, and client user-agent.
- **Back-Populating Model Relationships**:
  - Updated `User` (`src/db/models/user.py`) to expose back-populating collections to categories, transactions, budgets, goals, loans, recurring rules, holdings, investment transactions, and audit logs.
  - Updated `FinancialAccount` (`src/db/models/account.py`) to expose relationships to transaction entries, loans, recurring rules, holdings, and investment transactions.
  - Re-exported all models and enums cleanly in `src/db/models/__init__.py`.
- **Alembic Database Migration (`472e31906438`)**:
  - Generated and validated migration `alembic/versions/472e31906438_create_phase_2_relational_models.py` with explicit constraint names and SQLite batch mode support (`render_as_batch=True`).
  - Applied migration cleanly to `data/finance.db` via `alembic upgrade head`.
  - Verified existing database records (specifically `Primary Checking` with `USD` and `1500.00` balance) were preserved without modification.
  - Tested migration downgrade to `fba246fe5321` and re-upgrade to head on an isolated disposable test database.
- **Development Database Seeder Expansion (`src/db/seed.py`)**:
  - Added 13 default Indian categories across income and expense flows (Salary, Investments, Housing, Groceries, Utilities, Transport, etc.).
  - Added sample investment asset (`NIFTYBEES` ETF) and sample savings goal (`Emergency Fund`) seeded idempotently.
- **Automated Test Suite**:
  - `tests/unit/test_phase2_models.py`: 10 comprehensive unit tests covering model relationships, check constraints, unique constraints, cascade deletes, account deletion restrictions, and 4-decimal quantity precision.
  - `tests/integration/test_migrations.py`: 1 integration test verifying Alembic upgrade, reflection of all 15 tables, downgrade to Phase 1, and re-upgrade to head.
  - Total automated tests increased from 30 to 41 tests (100% pass rate).
  - Code coverage: 89% across `src/`.

---

## [0.2.0] - 2026-11-15 (Phase 1: Environment and Application Foundation)

### Changed & Remediated
- **Currency System Alignment to INR (₹)**:
  - Transitioned default currency from USD to **INR (₹)** across SQLAlchemy models (`FinancialAccount.currency`), Pydantic schemas (`AccountCreate.currency`), monetary utilities (`format_currency`), and Streamlit forms.
  - Preserved existing database records without automated conversion or exchange-rate distortion.
  - Guaranteed migration immutability by leaving previously applied migration `fba246fe5321` intact.
- **Authoritative Roadmap Adoption (Phases 0–8)**:
  - Reconciled documentation roadmap to the authoritative 9-phase lifecycle (Phases 0 through 8).
  - Explicitly mapped recurring transactions, savings goals, loans & debts, investments, and AI insights to dedicated delivery phases.
- **Protected Status for Existing Account CRUD**:
  - Formally protected existing account models, repository, service, and FastAPI REST endpoints.
  - Added 8 unit and integration regression tests (total 30 automated tests, 100% pass rate).

### Added
- **Python 3.12 Virtual Environment & Dependency Locking**:
  - Configured project metadata in `pyproject.toml`, pinned dependencies in `requirements.txt`, and generated frozen `requirements.lock`.
  - Configured standalone Python 3.12.13 virtual environment with `uv`.
- **Code Quality & Verification Tooling**:
  - Configured **Ruff** for high-speed PEP 8 linting and code formatting (`line-length = 100`).
  - Configured **Mypy** in strict mode (`disallow_untyped_defs = true`, `strict = true`) passing cleanly across all 28 source files.
  - Configured **Pytest** with `pytest-asyncio` and `pytest-cov`.
  - Added **Bandit** (SAST, 0 issues detected across 1,381 lines) and **pip-audit** (0 CVE vulnerabilities).
- **Configuration & Core Services**:
  - `src/core/config.py`: `Settings` class using `pydantic-settings` for runtime environment validation with `.env` / `.env.example`.
  - `src/core/logging.py`: Structured logger with timestamp, log level, module origin, and zero credential/PII leakage.
  - `src/core/money.py`: Strict base-10 financial arithmetic (`to_decimal`, `format_currency`) preventing IEEE 754 float rounding errors.
  - `src/core/exceptions.py`: Centralized domain exceptions (`AppException`, `NotFoundError`, `ConflictError`, `ValidationError`) and standardized FastAPI JSON error response envelopes.
- **Database & Alembic Migration Foundation**:
  - `src/db/base.py`: Declarative Base with UUID primary keys and `TimestampMixin` (`created_at`, `updated_at`).
  - `src/db/models/user.py`: `User` entity model.
  - `src/db/models/account.py`: `FinancialAccount` entity model with `AccountType` enum, currency, `Numeric(18, 2)` opening balance, and foreign key cascades.
  - `src/db/session.py`: Synchronous SQLAlchemy engine with SQLite multi-thread safety (`check_same_thread=False`) and automatic `PRAGMA foreign_keys=ON` enforcement.
  - `alembic/`: Initial Alembic migration `fba246fe5321_create_users_and_financial_accounts.py` applied to `data/finance.db`.
  - `src/db/seed.py`: Development database seeder providing a default user and checking account.
- **FastAPI REST API**:
  - `src/api/main.py`: Modular app factory with lifespan database health checks, CORS middleware, and custom exception handlers.
  - `src/schemas/`: Pydantic request/response schemas (`GenericResponse[T]`, `HealthResponse`, `AccountCreate`, `AccountUpdate`, `AccountRead`, `UserRead`).
  - `src/repositories/account_repo.py`: Repository isolating SQLAlchemy query execution.
  - `src/services/account_service.py`: Domain service enforcing business rules and duplicate name checks.
  - `src/api/routers/health.py`: `GET /health` and `GET /api/v1/health` connectivity verification without leaking secrets.
  - `src/api/routers/accounts.py`: Full REST API endpoints (`GET`, `POST`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`).
- **Streamlit Frontend Application**:
  - `.streamlit/config.toml`: Custom dark fintech theme (dark background `#0d1117`, emerald accent `#10b981`).
  - `src/frontend/api_client.py`: Decoupled HTTP client connecting to FastAPI backend via HTTPX.
  - `src/frontend/components/ui.py`: Custom CSS injection, metric cards, status indicators, and phase roadmap cards.
  - `src/frontend/app.py`: Nine-tab navigation layout (Dashboard, Accounts, Transactions, Budgets, Goals, Loans & Debts, Investments, Analytics, Settings), live backend status badge, account registration form, and account listing with archive actions.
- **Automated Test Suite**:
  - 21 automated tests (12 unit tests, 9 API integration tests) achieving 100% pass rate.

---

## [0.1.0] - 2026-11-15 (Phase 0: Project Foundation & Architecture)

### Added
- **Technology Direction Alignment**: Established the Python + SQL core stack:
  - **Frontend UI**: Streamlit reactive dashboard with Plotly interactive charts.
  - **Backend API**: FastAPI asynchronous REST framework.
  - **Database & Persistence**: SQLAlchemy 2.0 ORM + Alembic schema migrations (dual database: SQLite local, PostgreSQL production).
  - **Data Processing & Validation**: Pandas dataframes + Pydantic v2 validation.
  - **Testing & Security**: Pytest + HTTPX, Bandit (SAST), and pip-audit (dependency CVE scanning).
- **Mandatory AI Agent Directives (`AGENTS.md`)**: Codified operational rules for autonomous agents (strict phase boundaries, regression testing, zero unapproved features, security audit enforcement, stopping at approval gates).
- **Product Vision (`docs/APP.md`)**: Defined application purpose, user personas (Alex, Jordan, Morgan), core value pillars, and Streamlit UX philosophy.
- **System Specifications (`docs/SPEC.md`)**: Documented 20 functional requirements, 10 non-functional requirements, business rules, financial invariants, and Given-When-Then acceptance criteria.
- **Technical Architecture (`docs/ARCHITECTURE.md`)**:
  - Detailed multi-tier decoupled architecture: Streamlit $\to$ FastAPI $\to$ Domain Services $\to$ SQLAlchemy Repositories.
  - Formulated SQLAlchemy 2.0 ORM models for `User`, `Account`, `Category`, `Transaction`, `Budget`, `RecurringRule`, and `AuditLog`.
  - Designed SQLite-to-PostgreSQL migration path via Alembic and environment-driven `DATABASE_URL`.
  - Established Decimal-safe financial precision model (`decimal.Decimal` and `Numeric(18, 2)`).
  - Designed Docker and Docker Compose containerization strategy.
- **Security Baseline (`docs/SECURITY.md`)**:
  - Mapped OWASP Top 10 risks to Python/FastAPI mitigations.
  - Codified Static Application Security Testing via **Bandit** and dependency scanning via **pip-audit**.
  - Documented strict Pydantic input sanitization and parameter-driven SQL execution.
- **Quality Assurance Framework (`docs/TESTING.md`)**:
  - Established testing pyramid: 70% Unit (Pytest), 20% Integration (HTTPX AsyncClient), 10% E2E (Streamlit AppTest).
  - Specified automated security and dependency testing in CI pipelines.
  - Defined explicit phase completion gate criteria.
- **Engineering Standards (`docs/DEVELOPMENT_RULES.md`)**:
  - Codified PEP 8, Ruff formatting, strict Mypy rules, and layer separation boundaries.
- **Development Roadmap (`docs/PHASES.md`)**: Detailed all nine sequential phases with explicit scope, deliverables, automated tests, security audits, dependency audits, acceptance criteria, and approval gates.
- **Architectural Decision Records (`docs/DECISIONS.md`)**: Authored ADR-001 through ADR-010 documenting design rationale and trade-offs.
- **Engineering Handoff Protocol (`docs/HANDOFF.md`)**: Authored comprehensive onboarding and handoff document with command cheatsheets and transition protocols.
- **Project Landing (`README.md`)**: Created comprehensive project guide with verified stack versions, documentation index, and roadmap.
