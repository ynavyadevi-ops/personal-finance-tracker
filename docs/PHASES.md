# Personal Finance Tracker — Nine-Phase Development Roadmap

> **DOCUMENT**: `docs/PHASES.md`  
> **STATUS**: AUTHORITATIVE BASELINE  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT ACTIVE PHASE**: Phase 1 Remediation (COMPLETED — Awaiting Phase 2 Approval)

---

## Roadmap Overview

Development is partitioned into nine strictly-bounded sequential phases (**Phase 0 through Phase 8**). Advancing to the next phase requires satisfying all deliverables, passing all automated tests, passing security and dependency audits, and obtaining explicit human sign-off.

```
[ Phase 0: Foundation & Docs ] ──▶ [ Phase 1: Environment & Tooling ] ──▶ [ Phase 2: Database Modeling & Migrations ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 3: Core Accounting Engine ] ──▶ [ Phase 4: REST API & Portability ] ──▶ [ Phase 5: Streamlit UI Core ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 6: Advanced Feature Pages ] ──▶ [ Phase 7: Analytics & AI Insights ] ──▶ [ Phase 8: Testing, Security & Release ]
```

---

## Phase 0: Project Foundation and Documentation (COMPLETED)

- **Objective**: Establish the Python + SQL technical architecture, document security and quality baselines, initialize the documentation suite, and define AI operating constraints.
- **Dependencies**: None.
- **Status**: **COMPLETE**.
- **Explicit Scope**:
  - Full workspace inspection and Git version control setup.
  - Creation of `AGENTS.md`, `README.md`, `.gitignore`.
  - Authoring `docs/APP.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT_RULES.md`, `docs/PHASES.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, and `docs/HANDOFF.md`.
  - Verification of stable compatible releases for the Python + SQL stack.
- **Expected Deliverables**: Complete documentation baseline committed to Git.
- **Automated Tests**: Markdown link integrity checks.
- **Security Audit**: Review security baseline policies and supply-chain vetting rules.
- **Dependency Audit**: Review target dependency versions against official PyPI advisories.
- **Acceptance Criteria**: All documents exist and are synchronized; zero application code written.
- **Approval Gate**: User approval granted.

---

## Phase 1: Environment Setup, Python Tooling & Application Foundation (COMPLETED)

- **Objective**: Set up Python 3.12 virtual environment, configure package dependencies via `pyproject.toml`, establish Ruff and Mypy tooling, configure Pytest, initialize core configuration, and establish the application foundation.
- **Dependencies**: Phase 0 approval.
- **Status**: **COMPLETE & REMEDIATED**.
- **Explicit Scope**:
  - Python 3.12.13 virtual environment with pinned dependencies (`requirements.txt`, `requirements.lock`).
  - Code quality tooling: Ruff linter & formatter, Mypy strict mode, Pytest test runner, Bandit SAST, `pip-audit`.
  - Core cross-cutting modules: `src/core/config.py` (Pydantic BaseSettings), `src/core/logging.py`, `src/core/money.py` (Decimal-safe financial math, default currency INR / ₹), `src/core/exceptions.py`.
  - Initial database persistence: SQLAlchemy 2.0 base (`src/db/base.py`, `src/db/session.py`), initial models (`User`, `FinancialAccount`), Alembic migration `fba246fe5321`, development database seeder (`src/db/seed.py`).
  - Backend API foundation: FastAPI app factory (`src/api/main.py`), health checks (`src/api/routers/health.py`), protected account CRUD (`src/api/routers/accounts.py`).
  - Frontend shell: Dark fintech Streamlit layout (`src/frontend/app.py`, `src/frontend/components/ui.py`), decoupled API client (`src/frontend/api_client.py`).
  - Currency remediation: System-wide default currency aligned to **INR (₹)** while preserving existing records without silent conversion.
- **Expected Deliverables**: Operational backend and frontend, passing test suite, clean linting/typing, and zero security vulnerabilities.
- **Automated Tests**: 30 automated tests passing (18 unit tests, 12 API integration tests).
- **Security Audit**: Bandit scan (0 findings across 1,385 LOC); `pip-audit` scan (0 CVE vulnerabilities).
- **Acceptance Criteria**: `ruff check .` clean; `mypy` clean; `pytest` passes; `pip-audit` clean.
- **Approval Gate**: Explicit user approval required to proceed to Phase 2.

---

## Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations (NEXT PHASE — AWAITING APPROVAL)

- **Objective**: Implement comprehensive SQLAlchemy 2.0 declarative models for all approved entities, configure Alembic migrations for dual-database (SQLite local, PostgreSQL production), and expand seed scripts.
- **Dependencies**: Phase 1 explicit approval.
- **Explicit Scope**:
  - Full relational data models (`src/db/models/`):
    - `User`: Identity, authentication credentials, settings, preferences.
    - `FinancialAccount`: Depository, credit, cash, loan, and investment accounts with `Numeric(18, 2)` balances and currency.
    - `Category`: Hierarchical income and expense categories with color codes and icons.
    - `Transaction`: Double-entry inspired ledger records with type (`INCOME`, `EXPENSE`, `TRANSFER`), amounts, tags, and payee.
    - `Budget`: Monthly category expenditure caps and rollover policies.
    - `SavingsGoal`: Target amounts, target dates, current allocated balance, and milestone tracking.
    - `LoanDebtSchedule`: Principal, interest rate, term, minimum payments, and amortization tracking.
    - `InvestmentHolding`: Asset symbol, name, asset class (Equity, Mutual Fund, ETF, Gold), quantity, cost basis, valuation tracking, and account foreign keys.
    - `RecurringRule`: Automated schedules (daily, weekly, monthly, annual) for recurring bills and income.
    - `AuditLog`: Immutable change ledger tracking all balance-altering financial mutations.
  - Alembic migration scripts: autogenerate and review migrations for both SQLite and PostgreSQL dialects.
  - Database seeder update (`src/db/seed.py`): Populate default Indian categories, standard recurring rule samples, and sample goals.
- **Expected Deliverables**: Tested Alembic migration revision, updated `data/finance.db`, and functional seed scripts.
- **Automated Tests**: Pytest tests for schema validation, foreign key cascades, unique constraints, and migration upgrade/downgrade round-trips.
- **Security Audit**: Bandit scan verifies zero SQL injection vulnerabilities in model definitions and queries.
- **Dependency Audit**: `pip-audit` scan.
- **Acceptance Criteria**: `alembic upgrade head` executes cleanly on SQLite and PostgreSQL; seed script executes; model tests pass.
- **Approval Gate**: Explicit user approval required to proceed to Phase 3.

---

## Phase 3: Core Accounting Engine, Financial Services & Domain Logic

- **Objective**: Implement business logic services, double-entry balance calculations, transfer atomicity, recurring transaction queues, savings goal tracking, and loan amortization math.
- **Dependencies**: Phase 2 explicit approval.
- **Explicit Scope**:
  - Exact Decimal financial engine (`src/core/money.py`): quantization, Indian number formatting (`₹`), rounding.
  - Domain business services (`src/services/`):
    - `AccountService`: Protected balance computation, reconciliation, and archiving.
    - `TransactionService`: Atomic multi-account transfers, validation rules (positive amounts), balance conservation.
    - `BudgetService`: Monthly cap utilization, rollover calculations, and threshold alert statuses.
    - `RecurringTransactionService`: Cron-style recurring schedule evaluator and automated due-transaction generator.
    - `SavingsGoalService`: Goal contribution logic, percentage completion, and milestone tracking.
    - `LoanDebtService`: Amortization schedule generator, interest calculations, and early payoff projections.
    - `InvestmentService`: Portfolio asset valuation, cost basis tracking, and realized/unrealized gains.
  - Pydantic v2 schemas for all new entities (`src/schemas/`).
- **Expected Deliverables**: Pure domain service layer decoupled from HTTP transport.
- **Automated Tests**: Comprehensive unit tests achieving $\ge 90\%$ branch coverage on financial arithmetic and business services.
- **Security Audit**: Bandit scan; boundary value testing on negative amounts and arithmetic overflow.
- **Dependency Audit**: `pip-audit` scan.
- **Acceptance Criteria**: 100% of unit tests pass; zero floating-point operations; atomic transfer invariants verified.
- **Approval Gate**: Explicit user approval required to proceed to Phase 4.

---

## Phase 4: FastAPI REST API & Data Portability Services

- **Objective**: Expose all domain services via RESTful API endpoints, implement bank statement CSV/Excel import pipelines with Pandas, and build export utilities.
- **Dependencies**: Phase 3 explicit approval.
- **Explicit Scope**:
  - FastAPI routers (`src/api/routers/`):
    - `/api/v1/auth`: Authentication and tenant context injection.
    - `/api/v1/accounts`: Protected account management.
    - `/api/v1/transactions`: Ledger mutations, filtering, pagination, and atomic transfers.
    - `/api/v1/budgets`: Budget caps, progress statistics.
    - `/api/v1/goals`: Savings goals CRUD and contribution endpoints.
    - `/api/v1/loans`: Loan accounts, payment schedules, and payoff projections.
    - `/api/v1/investments`: Portfolio holdings and valuation endpoints.
    - `/api/v1/recurring`: Recurring transaction rule management and queue execution.
  - Data Portability Pipeline:
    - Statement Import Wizard: Pandas-driven CSV/Excel parsing, column header mapping, preview, duplicate detection, batch commit.
    - Ledger Export: RFC 4180 compliant CSV export stream and Excel (`.xlsx`) generation.
    - JSON database snapshot backup and restore facility.
- **Expected Deliverables**: Fully documented OpenAPI/Swagger endpoints (`/docs`) and tested data portability pipelines.
- **Automated Tests**: HTTPX `AsyncClient` integration tests for all endpoints validating status codes (200, 201, 400, 404, 409, 422).
- **Security Audit**: Bandit scan; file upload security checks (MIME validation, size limits, CSV injection defense).
- **Dependency Audit**: `pip-audit` scan.
- **Acceptance Criteria**: Integration test suite passes; statement import correctly deduplicates; export round-trips validate cleanly.
- **Approval Gate**: Explicit user approval required to proceed to Phase 5.

---

## Phase 5: Streamlit Frontend Core UI & Core Pages

- **Objective**: Build the core Streamlit user experience, polish the dark fintech interface, and implement the primary money management screens.
- **Dependencies**: Phase 4 explicit approval.
- **Explicit Scope**:
  - Streamlit application shell (`src/frontend/app.py`) with responsive sidebar navigation and live API health indicators.
  - Reusable fintech UI components (`src/frontend/components/`):
    - Status badges, metric cards, and responsive summary containers.
    - Form controls with inline validation and toast notifications.
    - Interactive data tables with search, sorting, and pagination.
  - Core User Pages:
    - **Dashboard**: Net worth summary callouts, cash flow pulse, recent transactions, and quick action forms.
    - **Accounts Page**: Protected account listing cards, balance summaries in INR (₹), account creation, and archive toggle.
    - **Transactions Page**: Searchable ledger table, date/category filters, and expense/income/transfer entry forms.
    - **Budgets Page**: Monthly category budget cards, dynamic utilization progress bars, and alert banners.
- **Expected Deliverables**: Interactive, responsive Streamlit dashboard connected to FastAPI backend.
- **Automated Tests**: Unit tests for `api_client.py` and UI helper functions; Streamlit `AppTest` simulations for core journeys.
- **Security Audit**: Bandit scan verifying zero credential or secret disclosure in UI templates.
- **Dependency Audit**: `pip-audit` scan.
- **Acceptance Criteria**: Core financial workflows operate seamlessly; UI updates reactively upon mutations.
- **Approval Gate**: Explicit user approval required to proceed to Phase 6.

---

## Phase 6: Advanced Feature Pages & Specialized Tracking

- **Objective**: Implement dedicated Streamlit interface screens for Savings Goals, Loans & Debt payoff, Investment portfolio, and Recurring Transaction rules.
- **Dependencies**: Phase 5 explicit approval.
- **Explicit Scope**:
  - Specialized Streamlit Pages:
    - **Goals Page**: Visual savings goal cards, progress circles, target date countdowns, and contribution dialogs.
    - **Loans & Debts Page**: Liability breakdown, interest rate displays, debt snowball/avalanche payoff schedules, and extra payment simulations.
    - **Investments Page**: Asset allocation distribution, portfolio holdings list, cost basis vs. current valuation, and performance summaries.
    - **Recurring Rules Page**: Scheduled bills calendar view, frequency editor, and upcoming payment confirmation queue.
- **Expected Deliverables**: Fully functional tracking pages for goals, debts, investments, and recurring schedules.
- **Automated Tests**: UI component tests and API integration tests for specialized feature workflows.
- **Security Audit**: Bandit scan on all new frontend view scripts.
- **Dependency Audit**: `pip-audit` scan.
- **Acceptance Criteria**: Users can manage savings goals, model loan payoff timelines, track asset allocations, and approve recurring bills.
- **Approval Gate**: Explicit user approval required to proceed to Phase 7.

---

## Phase 7: Analytics, Plotly Visualizations & AI Insights

- **Objective**: Build advanced data analytics using Pandas and interactive Plotly charts; implement privacy-first AI financial insights.
- **Dependencies**: Phase 6 explicit approval.
- **Explicit Scope**:
  - Interactive Plotly Visualizations:
    - Monthly Cash Flow: Grouped bar charts comparing Income vs. Expense over rolling 6/12 month windows.
    - Category Expense Distribution: Interactive donut charts with drill-down into sub-categories.
    - Historical Net Worth Trajectory: Time-series area chart tracking assets minus liabilities over time.
  - Financial Analytics Metrics:
    - Savings Rate %, average monthly burn rate, runway calculator, and discretionary vs. non-discretionary ratios.
  - AI Financial Insights Engine:
    - Rule-based anomaly detection (unusual spending spikes, subscription price increases).
    - Optional smart transaction categorization suggestions (strictly opt-in with explicit user consent and zero telemetry leakage).
- **Expected Deliverables**: Rich analytics dashboard with interactive Plotly visual charts and actionable spending insights.
- **Automated Tests**: Tests for Pandas analytical aggregation pipelines and chart generator outputs.
- **Security Audit**: Bandit scan; verification of strict privacy and user consent boundaries for AI insights.
- **Dependency Audit**: `pip-audit` scan.
- **Acceptance Criteria**: Visual charts render interactively in $< 500\text{ ms}$; analytics metrics match exact ledger totals.
- **Approval Gate**: Explicit user approval required to proceed to Phase 8.

---

## Phase 8: Comprehensive Verification, Security Auditing & Production Readiness

- **Objective**: Execute end-to-end regression testing, conduct final security and vulnerability audits, verify PostgreSQL migration parity, package Docker containers, and complete the production release.
- **Dependencies**: Phase 7 explicit approval.
- **Explicit Scope**:
  - Comprehensive Verification & QA:
    - Full Pytest and HTTPX test suite achieving $\ge 85\%$ test coverage across all domain services and APIs.
    - Stress testing with high-volume datasets (50,000+ transactions).
  - Security & Compliance Audit:
    - Bandit SAST scan across the entire repository with zero unresolved findings.
    - `pip-audit` supply-chain audit verifying zero known CVEs.
    - OWASP Top 10 compliance audit (tenant isolation, parameterized SQL, secure headers).
  - Production Packaging & Migration Verification:
    - Multi-stage production `Dockerfile` and `docker-compose.yml` (FastAPI, Streamlit, PostgreSQL 16).
    - Database migration verification script (`scripts/verify_pg_migration.py`) validating SQLite-to-PostgreSQL data parity.
    - Automated backup and recovery scripts (`scripts/backup_db.sh`).
    - Final documentation synchronization and production deployment guide.
- **Expected Deliverables**: Production Docker deployment artifacts, verified PostgreSQL migration pipeline, and final release sign-off.
- **Automated Tests**: Full test suite passes against both SQLite and PostgreSQL backends.
- **Security Audit**: Final zero-vulnerability certification from Bandit and pip-audit.
- **Dependency Audit**: Final clean audit from `pip-audit`.
- **Acceptance Criteria**: Docker stack launches cleanly; test suite passes 100%; database migration verified to the exact cent; production release certified.
- **Approval Gate**: Final human production sign-off and release authorization.
