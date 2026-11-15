# Personal Finance Tracker — Nine-Phase Development Roadmap

> **DOCUMENT**: `docs/PHASES.md`  
> **STATUS**: AUTHORITATIVE BASELINE  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT ACTIVE PHASE**: Phase 3 — Core Accounting Engine, Financial Services & Domain Logic (COMPLETED — Awaiting Phase 4 Approval Gate)

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
- **Approval Gate**: Explicit user approval granted.

---

## Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations (COMPLETED)

- **Objective**: Implement comprehensive SQLAlchemy 2.0 declarative models for all approved entities, configure Alembic migrations with SQLite batch mode and PostgreSQL compatibility, and expand seed scripts.
- **Dependencies**: Phase 1 explicit approval (granted).
- **Status**: **COMPLETE & VERIFIED**.
- **Delivered Scope**:
  - Full relational data models (`src/db/models/`):
    - `User`: Identity, authentication credentials, settings, preferences, back-populating relationships to all domain entities.
    - `FinancialAccount`: Depository, credit, cash, loan, and investment accounts with `Numeric(18, 2)` balances, default INR currency, and deletion restricted by historical entries.
    - `Category`: Self-referential hierarchy (`parent_id`), income/expense types, visual colors, icons, default system categories, and uniqueness on `(user_id, name, parent_id)`.
    - `Transaction`: Business events (income, expense, transfer) with check constraint `amount > 0`.
    - `TransactionEntry`: Balanced double-entry line items with account references (`ON DELETE RESTRICT`), debit/credit direction, and check constraint `amount > 0`.
    - `Budget`: Monthly category allocations with `1 <= month <= 12` check, `amount > 0` check, and period uniqueness `(user_id, category_id, month, year)`.
    - `SavingsGoal`: Target amounts (`target_amount > 0`), current progress (`current_amount >= 0`), milestone target dates, and achieved toggle.
    - `LoanDebt` & `LoanPaymentSchedule`: Liability terms, positive principal check, non-negative remaining balance and interest rate checks, positive term months check, and ordered payment schedule entries with uniqueness on `(loan_id, payment_number)`.
    - `RecurringRule`: Periodic rules (daily, weekly, monthly, quarterly, yearly), interval check (`"interval" > 0`), positive amount check (`amount > 0`), and next occurrence indexing.
    - `InvestmentAsset`, `InvestmentHolding`, `InvestmentTransaction`: Asset catalog (Equity, Mutual Fund, ETF, Bond, Gold, Crypto), holdings with 4-decimal quantity precision (`Numeric(18, 4)`), non-negative check constraints, uniqueness on `(user_id, account_id, asset_id)`, and trade operation history.
    - `AuditLog`: Immutable change ledger tracking entity mutations, old/new value JSON snapshots, IP address, and user agent.
  - Alembic migration `472e31906438_create_phase_2_relational_models.py`:
    - Clean upgrade from base to head creating all 15 tables with explicit constraint names.
    - Verified upgrade applied to `data/finance.db`, preserving the existing USD primary checking account without modification.
    - Tested downgrade and re-upgrade cycle on an isolated temporary database.
  - Database seeder update (`src/db/seed.py`):
    - 13 standard default Indian categories seeded (Salary, Investments, Housing, Groceries, Utilities, etc.).
    - Default sample investment asset (`NIFTYBEES`) and sample savings goal (`Emergency Fund`) seeded idempotently.
- **Verification & Tests**:
  - 41 automated tests passing (31 unit, 10 integration, 100% pass rate).
  - 89% code coverage across `src/`.
  - Ruff: 0 lint errors, 48 files formatted.
  - Mypy: 0 type issues across 36 source files.
  - Bandit: 0 security issues across 2,628 lines scanned.
  - pip-audit: 0 known vulnerabilities.
  - Runtime probes: FastAPI `/health` (200 OK), Streamlit `/_stcore/health` (200 OK).
- **Approval Gate**: User approval granted.

---

## Phase 3: Core Accounting Engine, Financial Services & Domain Logic (COMPLETED)

- **Objective**: Implement business logic services, double-entry balance calculations, transfer atomicity, recurring transaction queues, savings goal tracking, and loan amortization math.
- **Dependencies**: Phase 2 explicit approval (granted).
- **Status**: **COMPLETE & VERIFIED**.
- **Delivered Scope**:
  - **Core Exceptions (`src/core/exceptions.py`)**:
    - Added `CurrencyMismatchError` (HTTP 422), `InsufficientUnitsError` (HTTP 422), `PermissionDeniedError` (HTTP 403).
  - **Pydantic v2 DTO Schemas (`src/schemas/`)**:
    - `transaction.py`: `TransactionCreate`, `TransactionEntryCreate`, `TransactionEntryRead`, `TransactionRead`, `TransferCreate`, `AccountReconciliation`.
    - `budget.py`: `BudgetCreate`, `BudgetRead`, `BudgetUtilization`.
    - `goal.py`: `SavingsGoalCreate`, `SavingsGoalRead`, `SavingsGoalProgress`.
    - `loan.py`: `LoanCreate`, `LoanRead`, `LoanPaymentScheduleRead`, `AmortizationScheduleItem`.
    - `recurring.py`: `RecurringRuleCreate`, `RecurringRuleRead`.
    - `investment.py`: `InvestmentBuyRequest`, `InvestmentSellRequest`, `InvestmentAssetRead`, `InvestmentHoldingRead`, `InvestmentTransactionRead`, `RealizedGainLossResult`.
  - **Repository Layer (`src/repositories/`)**:
    - `AccountRepository`: Account data access, tenant scoping, name uniqueness checks.
    - `TransactionRepository`: Transaction and entry creation, date/type/account/category filtering, idempotency lookup.
    - `CategoryRepository`: Category hierarchy, type validation, user-accessible category lookups.
    - `BudgetRepository`: Monthly allocations, period lookups, SQL monthly expense aggregation (strictly excluding transfers).
    - `SavingsGoalRepository`: Goal creation, progress updates, milestone listing.
    - `LoanRepository`: Loan creation, batch payment schedule creation, schedule queries.
    - `RecurringRepository`: Rule creation, due rule queries, execution date tracking, duplicate occurrence lookup.
    - `InvestmentRepository`: Asset queries, holdings tracking, trade transaction logging.
  - **Domain Service Layer (`src/services/`)**:
    - `LedgerService`: Double-entry invariant validation (`Total Debits == Total Credits`), account balance calculation by account type, and statement reconciliation.
    - `TransactionService`: Income, expense, and atomic inter-account transfer execution, idempotency caching, compensating transaction reversals.
    - `BudgetService`: Budget allocations, monthly category spending aggregations, threshold status calculation (NORMAL, WARNING, EXCEEDED), unspent rollover logic.
    - `SavingsGoalService`: Milestone creation, contributions, withdrawals, target completion tracking.
    - `LoanService`: Exact fixed-rate amortization schedule calculation using Decimal arithmetic, repayment tracking with principal vs. interest separation, liability payoff.
    - `RecurringService`: Next occurrence calculation across all frequencies (Daily, Weekly, Biweekly, Monthly, Quarterly, Yearly), due rule evaluation, automated transaction spawning, duplicate prevention.
    - `InvestmentService`: Security purchases with weighted-average cost basis recalculation, sales with holding sufficiency checks, realized gain/loss math, dividend logging.
- **Verification & Tests**:
  - 87 automated tests passing (74 unit tests, 13 integration tests, 100% pass rate).
  - Ruff: 0 lint errors, 75 files formatted.
  - Mypy: 0 type issues across 56 source files.
  - Bandit: 0 security issues across 4,969 lines scanned.
  - pip-audit: 0 known vulnerabilities.
  - Preserved existing database account `('Primary Checking', 'USD', 1500.00)` in `data/finance.db`.
- **Approval Gate**: Stopped at Phase 3 completion gate. Explicit user approval required to proceed to Phase 4.

---

## Phase 4: FastAPI REST API & Data Portability Services

- **Objective**: Expose all domain services via RESTful API endpoints, implement bank statement CSV/Excel import pipelines with Pandas, and build export and backup utilities.
- **Dependencies**: Phase 3 explicit approval.
- **Status**: **COMPLETED & VERIFIED** (Phase gate active; awaiting explicit approval to begin Phase 5).
- **Delivered Scope**:
  - **Authentication & Security Foundation (`src/core/security.py`, `src/api/routers/auth.py`)**:
    - Argon2id password hashing via `pwdlib[argon2]`.
    - Short-lived signed JWT access tokens via `pyjwt` with UTC expiration, issuer validation, and signature verification.
    - Secure administrative CLI (`src/cli/enroll.py`) ensuring legacy unauthenticated accounts can enroll initial passwords locally with anti-overwrite protection without public endpoint exposure.
    - OAuth2 password form login (`/api/v1/auth/token`) and profile retrieval (`/api/v1/auth/me`).
    - Server-side tenant extraction (`get_current_user`, `get_current_user_id`), never trusting client-supplied identity.
  - **Financial REST API Endpoints (`src/api/routers/`)**:
    - `/api/v1/accounts`: Protected account management with active filtering and soft delete.
    - `/api/v1/transactions`: Income/expense posting, atomic transfers (`/transfer`), compensating reversals (`/{id}/reverse`), pagination, filters, and mathematical balance reconciliation (`/reconcile/{account_id}`).
    - `/api/v1/budgets`: Budget allocations (`POST /budgets`), single category utilization (`/utilization`), period overviews (`/period`), threshold classification (NORMAL, WARNING, EXCEEDED), and rollover.
    - `/api/v1/goals`: Savings milestones, contributions (`/{id}/contribute`), withdrawals (`/{id}/withdraw`), and progress tracking (`/{id}/progress`).
    - `/api/v1/loans`: Debt obligations, auto-generated fixed-rate amortization schedules, payment instalment recording (`/{id}/payment`).
    - `/api/v1/investments`: Securities purchasing (`/buy`) with weighted-average cost basis, sales (`/sell`) with unit sufficiency checks and realized P&L, dividend logs (`/dividend`), and holdings queries (`/holdings`).
    - `/api/v1/recurring`: Recurrence rule definitions, due rule queries (`/due`), execution spawning ledger transactions with duplicate occurrence prevention (`/{id}/execute`), pause/resume (`/pause`, `/resume`).
  - **Data Portability Pipeline (`src/services/portability_service.py`, `src/api/routers/data_portability.py`)**:
    - Statement Import Wizard (`POST /api/v1/data/import/preview`, `POST /api/v1/data/import/commit`): Pandas/openpyxl CSV and XLSX parsing, configurable column mappings, validation limits (5MB, 1000 rows), duplicate detection against existing ledger records, and atomic batch commit.
    - Data Export (`GET /api/v1/data/export/csv`, `GET /api/v1/data/export/xlsx`): Filtered transaction exports with formula injection defense (`=, +, -, @, \t, \r` escaping).
    - Backup & Dry-Run Validation (`GET /api/v1/data/backup`, `POST /api/v1/data/backup/validate`): Full user-scoped JSON backup snapshot across 11 tables with exact Decimal string formatting. Destructive restore is strictly non-executable per security directives; only non-destructive export and dry-run validation are exposed.
- **Verification & Tests**:
  - 119 automated tests passing (74 unit tests, 45 integration tests, 100% pass rate).
  - Code Coverage: 89% overall across `src/`.
  - Ruff: 0 lint errors, all files formatted.
  - Mypy: 0 type issues across 67 source files in strict mode.
  - Bandit: 0 security issues across 6,770 lines of code.
  - pip-audit: 0 known vulnerabilities.
  - Preserved existing database account `('Primary Checking', 'USD', 1500.00)` in `data/finance.db`.
- **Approval Gate**: Stopped at Phase 4 completion gate. Explicit user approval required to proceed to Phase 5.

---

## Phase 5: Streamlit Frontend Core UI & Core Pages

- **Objective**: Build the core Streamlit user experience, polish the dark fintech interface, and implement the primary money management screens.
- **Dependencies**: Phase 4 explicit approval.
- **Status**: **PENDING AUTHORIZATION**.

---

## Phase 6: Streamlit Advanced Feature Pages

- **Objective**: Build dedicated Streamlit user interfaces for advanced financial management.
- **Dependencies**: Phase 5 explicit approval.
- **Status**: **PENDING AUTHORIZATION**.

---

## Phase 7: Analytics Engine, Plotly Visualizations & AI Financial Insights

- **Objective**: Implement financial analytics, generate Plotly visual charts, build cash flow projections, and integrate local AI financial insights.
- **Dependencies**: Phase 6 explicit approval.
- **Status**: **PENDING AUTHORIZATION**.

---

## Phase 8: System Hardening, Comprehensive Testing, Packaging & Release

- **Objective**: Perform comprehensive verification, security hardening, container packaging, production deployment readiness checks, and final release.
- **Dependencies**: Phase 7 explicit approval.
- **Status**: **PENDING AUTHORIZATION**.
