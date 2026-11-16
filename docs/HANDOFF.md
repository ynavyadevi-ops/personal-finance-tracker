# Personal Finance Tracker — Engineering Handoff & Operating Guide

> **DOCUMENT**: `docs/HANDOFF.md`  
> **STATUS**: ACTIVE & ENFORCED  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 8 — System Hardening, Comprehensive Testing, Packaging & Release (COMPLETED & VERIFIED)

---

## 1. Project Context & Current Status

This repository houses the **Personal Finance Tracker**, a production-oriented, secure, full-stack personal finance application implemented in **Python + SQL**.

### Current State
- **Phase 0 (Project Foundation and Documentation)**: **COMPLETE**.
- **Phase 1 (Environment Setup and Application Foundation)**: **COMPLETE & REMEDIATED**.
- **Phase 2 (Database Modeling, SQLAlchemy ORM & Alembic Migrations)**: **COMPLETE & VERIFIED**.
- **Phase 3 (Core Accounting Engine, Financial Services & Domain Logic)**: **COMPLETE & VERIFIED**.
- **Phase 4 (FastAPI REST API & Data Portability Services)**: **COMPLETE & VERIFIED**.
- **Phase 5 (Streamlit Frontend Core UI & Core Pages)**: **COMPLETE & VERIFIED**.
- **Phase 6 (Streamlit Frontend Advanced Views)**: **COMPLETE & VERIFIED**.
- **Phase 7 (Analytics Engine, Plotly Visualizations & AI Insights)**: **COMPLETE & VERIFIED**.
- **Phase 8 (System Hardening, Comprehensive Testing, Packaging & Release)**: **COMPLETED & VERIFIED (LOCAL MVP RELEASE CANDIDATE)**.
- **Post-Phase 8 Enhancement (User Registration & Dedicated Administrator Portal)**: **COMPLETED & VERIFIED**.
  - Added self-service user registration (`POST /api/v1/auth/register`) with Argon2id password hashing, email normalization, complexity enforcement, anti-enumeration protection, and sliding-window rate limiting.
  - Added public registration kill-switch (`SystemSettings` model with `registration_enabled` flag), allowing operators to immediately disable new registrations.
  - Implemented idempotent administrative bootstrap CLI (`src/cli/bootstrap_admin.py` and `scripts/bootstrap_admin.bat`) with interactive masked password entry or `--generate` flag, elevation confirmation prompts, and mandatory first-login password rotation flag (`must_change_password=True`).
  - Implemented Role-Based Access Control (RBAC) with `UserRole.USER` and `UserRole.ADMIN`, `require_admin` dependency enforcement, and `is_active` account deactivation controls.
  - Built dedicated, secure Administrator Portal (`src/frontend/views/admin.py`) featuring Platform Overview KPIs, User Governance (search, enable/disable toggle, temporary password generation), Security Audit Viewer, and System Settings.
  - Strict Financial Privacy Boundary enforced: administrative endpoints and views query only `User`, `AuditLog`, and `SystemSettings`. Customer transactions, accounts, balances, budgets, loans, and investment holdings remain 100% private and inaccessible to administrators.
  - Applied non-destructive migration `f6a91c8230b1` on isolated `data/demo_finance.db`. `data/finance.db` preserved untouched with verified SHA-256 hash.
  - Expanded automated test suite to **214 passed tests** (100% pass rate) with **79% overall test coverage** (5,379 statements, 1,139 missed) in 16.7s.
  - Security and quality audits: Ruff (0 errors, 123 files formatted), Mypy strict (0 errors in 72 files), Bandit SAST (0 issues in 11,923 lines), pip-audit (0 CVE vulnerabilities).
- **Execution is halted at the Release Gate. Public deployment is NOT authorized.**

---

## 2. Phase 2 Architecture & Delivered Database Models

All models are implemented in `src/db/models/` using SQLAlchemy 2.0 `Mapped` and `mapped_column` syntax, inheriting from `Base` and `TimestampMixin`.

### 2.1 Delivered Entity Inventory

1. **`User`** (`src/db/models/user.py`):
   - Tenant root entity. UUID primary key. Back-populates relationships to all domain models with `cascade="all, delete-orphan"`.
2. **`FinancialAccount`** (`src/db/models/account.py`):
   - Multi-account depository, credit, loan, and investment accounts. Protected from deletion via `ON DELETE RESTRICT` on historical ledger entries and loans.
3. **`Category`** (`src/db/models/category.py`):
   - Hierarchical categories supporting self-referential nesting (`parent_id`), `CategoryType` (`INCOME`, `EXPENSE`), hex color accents, UI icons, and unique constraint `uq_categories_user_name_parent`.
4. **`Transaction`** (`src/db/models/transaction.py`):
   - High-level financial business events with `TransactionType` (`INCOME`, `EXPENSE`, `TRANSFER`), description, tags, currency, and check constraint `chk_transactions_positive_amount`.
5. **`TransactionEntry`** (`src/db/models/transaction.py`):
   - Balanced double-entry ledger lines with `EntryType` (`DEBIT`, `CREDIT`), foreign key to `financial_accounts` (`ON DELETE RESTRICT`), optional category allocation, and check constraint `chk_transaction_entries_positive_amount`.
6. **`Budget`** (`src/db/models/budget.py`):
   - Monthly category spending caps with unique constraint `uq_budgets_user_cat_period`, month bounds check `chk_budgets_valid_month` (`1 <= month <= 12`), and positive amount check `chk_budgets_positive_amount`.
7. **`SavingsGoal`** (`src/db/models/goal.py`):
   - Milestone savings targets with check constraints `chk_savings_goals_positive_target` (`target_amount > 0`) and `chk_savings_goals_non_negative_current` (`current_amount >= 0`).
8. **`LoanDebt`** & **`LoanPaymentSchedule`** (`src/db/models/loan.py`):
   - Debt obligations tracking principal, remaining balance, interest rate, term months, and ordered amortization instalments with unique constraint `uq_loan_schedules_loan_number`.
9. **`RecurringRule`** (`src/db/models/recurring.py`):
   - Automated recurrence templates with `Frequency` (`DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`), interval check `"interval" > 0`, and positive amount check `amount > 0`.
10. **`InvestmentAsset`**, **`InvestmentHolding`**, **`InvestmentTransaction`** (`src/db/models/investment.py`):
    - Asset catalog (`AssetType`: `EQUITY`, `MUTUAL_FUND`, `ETF`, `BOND`, `GOLD`, `CRYPTO`, `OTHER`).
    - Holdings with 4-decimal quantity precision (`Numeric(18, 4)`), cost basis, total cost, and unique constraint `uq_holdings_user_acc_asset`.
    - Trade ledger with `InvestmentTxType` (`BUY`, `SELL`, `DIVIDEND`, `SPLIT`, `INTEREST`), linked transaction references, and fee non-negativity checks.
11. **`AuditLog`** (`src/db/models/audit.py`):
    - Append-only immutable log recording entity mutations, old/new value JSON snapshots, timestamp, user IP address, and client user-agent.

### 2.2 Migrations & Dual-Database Compatibility
- **Alembic Version**: `472e31906438_create_phase_2_relational_models.py` (down_revision: `fba246fe5321`).
- **SQLite Batch Alter**: All table modifications wrapped in `with op.batch_alter_table(...) as batch_op`.
- **PostgreSQL Ready**: SQLEnums configured with `native_enum=False` to ensure portable VARCHAR-based storage with check constraints across SQLite and PostgreSQL.
- **Explicit Constraint Naming**: All check constraints (`chk_...`) and unique constraints (`uq_...`) explicitly named for clean forward and reverse migrations.

---

## 3. Verification & Quality Assurance Summary

| Check | Tool / Framework | Scope | Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Unit Tests** | Pytest | 74 unit test functions across models, services, core | 74 passed in 0.5s | **PASS** |
| **Integration Tests** | Pytest + HTTPX + Alembic | 45 integration test functions (API, Auth, Portability, Migrations) | 45 passed in 3.1s | **PASS** |
| **Total Automated Tests** | Pytest | Complete test suite (119 tests) | 119 passed, 0 failed | **PASS** |
| **Test Coverage** | pytest-cov | Entire `src/` application code | 89% coverage (2,831 stmts) | **PASS** |
| **Code Formatting** | Ruff | 86 project Python files | 86 files formatted | **PASS** |
| **Code Linting** | Ruff | Complete repository | 0 lint errors | **PASS** |
| **Type Checking** | Mypy (strict) | 67 source files in `src/` | 0 type errors | **PASS** |
| **SAST Security Scan** | Bandit | 6,770 lines of application code (`src/`) | 0 issues identified | **PASS** |
| **Dependency CVE Scan** | pip-audit | 100 installed dependencies against PyPI DB | 0 vulnerabilities found | **PASS** |
| **FastAPI Backend Probe** | Uvicorn + HTTPX | Startup and `/health` probe on port 8005 | HTTP 200 OK (DB Connected) | **PASS** |
| **Streamlit UI Probe** | Streamlit + HTTPX | Headless startup and `/_stcore/health` probe | HTTP 200 OK | **PASS** |

---

## 4. Protected Functionality Verification

In accordance with Directive 3 and ADR-015:
- **Financial Account CRUD**: `AccountService`, `AccountRepository`, and `/api/v1/accounts` REST endpoints remain completely functional.
- **Regression Tests**: All 15 account tests pass cleanly without regressions.
- **Data Preservation**: Existing database record in `data/finance.db` (`Primary Checking`, `USD`, `1500.00`) was preserved untouched and unmutated during migration upgrade and seeding.

---

## 5. Authoritative Nine-Phase Roadmap Status

| Phase | Phase Name | Status | Deliverables |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Project Foundation and Documentation | **COMPLETED** | Architecture, ADRs, documentation baseline. |
| **Phase 1** | Environment Setup & Application Foundation | **COMPLETED** | Tooling, virtualenv, FastAPI & Streamlit foundation, INR currency alignment. |
| **Phase 2** | Database Modeling & Alembic Migrations | **COMPLETED** | Full relational models, migration `472e31906438`, 41 tests, 89% coverage. |
| **Phase 3** | Core Accounting Engine & Financial Services | **PENDING APPROVAL** | Double-entry calculation engine, transfers, budgets, loans, investments logic. |
| **Phase 4** | FastAPI REST API & Data Portability | PLANNED | Complete REST endpoints, CSV/Excel import/export pipelines. |
| **Phase 5** | Streamlit Frontend Core UI & Core Pages | PLANNED | Layout, state management, Accounts, Transactions, Budgets pages. |
| **Phase 6** | Advanced Feature Pages | PLANNED | Goals, Loans/Debts, Investments, Recurring rules UI pages. |
| **Phase 7** | Analytics & AI Insights | PLANNED | Plotly charts, Cash flow, Net worth, spending trends, smart category suggestions. |
| **Phase 8** | Verification, Security & Production Release | PLANNED | PostgreSQL migration script, Docker packaging, final audit sign-off. |

---

## 6. Phase 3 Scope & Approval Gate

### Scope of Phase 3 (Core Accounting Engine, Financial Services & Domain Logic)
Upon receiving user authorization, Phase 3 will implement:
1. **Transaction Domain Service (`TransactionService`)**:
   - Double-entry ledger line creation (balanced debit/credit entries).
   - Atomic balance adjustments for depository, credit, and investment accounts.
   - Atomic inter-account transfers.
2. **Budget Domain Service (`BudgetService`)**:
   - Monthly category spending calculations and threshold monitoring (Normal $<80\%$, Warning $80-99\%$, Exceeded $\ge 100\%$).
   - Rollover policy calculation for enabled categories.
3. **Savings Goal Service (`SavingsGoalService`)**:
   - Contribution allocation and milestone target progress computation.
4. **Loan & Debt Service (`LoanService`)**:
   - Standard amortization schedule generation and EMI payment registration.
5. **Recurring Transaction Service (`RecurringService`)**:
   - Next-occurrence date calculation and recurring queue execution.
6. **Investment Position Service (`InvestmentService`)**:
   - Holdings quantity updates, weighted-average cost basis calculation, and unrealized gain/loss math.
7. **Comprehensive Pytest Suite**:
   - Unit tests targeting 90%+ branch coverage across all financial domain calculations.

### Approval Requirement
> **STOPPED AT APPROVAL GATE**: Phase 2 implementation is complete and verified. No Phase 3 code or logic has been scaffolded or implemented. The agent is halted and awaits explicit user approval to begin Phase 3.

---

## 7. Phase 2 Final Financial Data Integrity Review

A comprehensive, empirical integrity audit was conducted across the database schema, models, migrations, constraints, and precision boundaries:

### 7.1 Double-Entry Ledger Integrity
- **Finding 1.1 (Transaction & Entry Relationship)**: `Transaction` and `TransactionEntry` establish a strict 1-to-N parent-child relationship with `cascade="all, delete-orphan"` on transaction deletion and `ondelete="RESTRICT"` on account references.
  - *Status*: **PASS**
  - *Evidence*: `test_transaction_double_entry_and_cascade` verifies child collection cascade; `test_transaction_entry_restrict_account_deletion` verifies foreign key restriction.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.
- **Finding 1.2 (Ledger Balancing Enforcement)**: Pure relational SQL DDL cannot enforce multi-row aggregate check constraints (`sum(debits) == sum(credits)`) across child rows. Raw DBAPI inserts without application services can technically insert unbalanced entries.
  - *Status*: **NOT IMPLEMENTED (BY DESIGN IN PHASE 2)**
  - *Evidence*: Empirical test confirms SQLite DDL accepts a single entry transaction if directly injected without service checks.
  - *Severity*: High (if omitted in Phase 3).
  - *Remediation*: In Phase 3, `TransactionService.create_transaction()` and `TransactionService.transfer()` must mandate that total debits equal total credits, matching `Transaction.amount`, before committing to the session.
  - *Blocks Phase 3*: No (This is the primary deliverable of Phase 3).

### 7.2 User Data Isolation & Cross-Tenant Boundary
- **Finding 2.1 (Tenant Scoping Across Models)**: Every top-level entity (`FinancialAccount`, `Transaction`, `Budget`, `SavingsGoal`, `LoanDebt`, `RecurringRule`, `InvestmentHolding`, `InvestmentTransaction`, `AuditLog`) enforces a mandatory foreign key to `users.id` with `ON DELETE CASCADE`.
  - *Status*: **PASS**
  - *Evidence*: Schema DDL and tests confirm all user foreign keys and cascade erasure.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.
- **Finding 2.2 (Cross-Tenant Account/Category Referencing at DDL Layer)**: `TransactionEntry` references `financial_accounts.id` and `categories.id` directly. DDL does not enforce that `transaction.user_id == account.user_id` across tables.
  - *Status*: **NOT IMPLEMENTED (BY DESIGN IN PHASE 2 DDL)**
  - *Evidence*: Empirical test confirmed that a raw insert bypassing services can link User 1's transaction to User 2's account.
  - *Severity*: High (if omitted in Phase 3).
  - *Remediation*: In Phase 3, `TransactionService` must validate ownership of all referenced `account_id` and `category_id` parameters against `current_user.id` (consistent with `AccountService` in Phase 1).
  - *Blocks Phase 3*: No.

### 7.3 Financial Precision & SQLite vs PostgreSQL Compatibility
- **Finding 3.1 (Decimal-Safe Arithmetic & Fractional Precision)**: Python `decimal.Decimal` is preserved through SQLAlchemy session querying. Fractional investment quantities (`Numeric(18, 4)`) and currency values (`Numeric(18, 2)`) return exact `Decimal` instances.
  - *Status*: **PASS**
  - *Evidence*: Round-trip query tests in SQLite verify exact decimal precision: `Decimal('123.4567')` and `Decimal('123456789.99')` return `<class 'decimal.Decimal'>` with 0 drift.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.
- **Finding 3.2 (SQLite 64-Bit Float Storage vs PostgreSQL Native Arbitrary Precision)**: SQLite lacks an arbitrary-precision numeric storage class, storing `Numeric` as IEEE 754 64-bit real numbers. Amounts exceeding 15 significant digits (e.g. ₹90+ trillion) undergo float rounding in SQLite. In contrast, production PostgreSQL natively stores `NUMERIC(18, 2)` as exact binary-coded decimals with zero rounding drift.
  - *Status*: **PASS (WITH DOCUMENTED POSTGRESQL ADVANTAGE)**
  - *Evidence*: Raw SQLite typeof inspection confirmed storage as `real` for numbers within personal finance scale ($< 90$ trillion INR).
  - *Severity*: Low for local development; Zero for PostgreSQL production.
  - *Remediation*: Documented in architecture; verified in verification scripts.
  - *Blocks Phase 3*: No.

### 7.4 Audit Log Immutability & Retention Safeguards
- **Finding 4.1 (Audit Log Update/Delete Prevention)**: At the current SQLite ORM level, `AuditLog` does not possess update/delete restrictions enforced by DB triggers.
  - *Status*: **NOT IMPLEMENTED (PLANNED FOR PHASE 8 HARDENING)**
  - *Evidence*: Empirical test shows that an unrestricted session can execute update or delete on `AuditLog`.
  - *Severity*: Medium.
  - *Remediation*: Enforce append-only repository in services; configure PostgreSQL role permissions (`REVOKE UPDATE, DELETE ON audit_logs FROM app_user`) in Phase 8.
  - *Blocks Phase 3*: No.
- **Finding 4.2 (Cascading User Erasure vs Audit Retention)**: `AuditLog.user_id` has `ON DELETE CASCADE`, erasing audit records upon user deletion.
  - *Status*: **PASS (COMPLIANT WITH PRIVACY / RIGHT TO ERASURE)**
  - *Evidence*: User cascade deletion tests confirm full child audit erasure.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.

### 7.5 Migration Safety & Historical Record Preservation
- **Finding 5.1 (Alembic Revision Linearity & Record Preservation)**: Linear revision chain `fba246fe5321 -> 472e31906438`. Existing database record `('Primary Checking', 'USD', 1500.00)` in `data/finance.db` is 100% intact and unmutated.
  - *Status*: **PASS**
  - *Evidence*: `alembic history` confirms single head; database query confirms record preserved.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.
- **Finding 5.2 (Disposable Database Upgrade/Downgrade Lifecycle)**: Migrations upgrade cleanly from base to head, creating 15 tables, downgrade to base removing all tables, and re-upgrade cleanly.
  - *Status*: **PASS**
  - *Evidence*: Automated integration test `test_alembic_upgrade_downgrade_cycle` passed in 0.60s.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.

### 7.6 Security & Regression Test Suite
- **Finding 6.1 (Full Test & Audit Verification)**: Pytest (41 passed), Ruff check (0 errors), Ruff format (48 files formatted), Mypy (0 errors in 36 files), Bandit SAST (0 issues in 2,628 lines), pip-audit (0 CVEs).
  - *Status*: **PASS**
  - *Evidence*: Clean runs across all six quality tools.
  - *Severity*: Informational.
  - *Blocks Phase 3*: No.

---

## 8. Phase 3 Architecture & Financial Services Delivery

Phase 3 delivers the complete business logic layer governing transactions, accounts, budgets, goals, debts, recurrence, and investments.

### 8.1 Domain Services & Accounting Logic

1. **`LedgerService`** (`src/services/ledger_service.py`):
   - Enforces the core double-entry accounting invariant ($\sum \text{Debits} == \sum \text{Credits}$).
   - Deterministically calculates balances based on account classification:
     - Asset accounts (`CHECKING`, `SAVINGS`, `CASH`, `INVESTMENT`): $\text{Balance} = \text{Opening} + \sum \text{Debits} - \sum \text{Credits}$.
     - Liability accounts (`CREDIT_CARD`, `LOAN`): $\text{Balance} = \text{Opening} + \sum \text{Credits} - \sum \text{Debits}$.
   - Provides statement balance reconciliation with discrepancy quantification.

2. **`TransactionService`** (`src/services/transaction_service.py`):
   - Handles `record_income` (Debit to asset), `record_expense` (Credit to asset/liability), and `record_transfer` (Credit source, Debit destination).
   - Validates that source and destination accounts are distinct.
   - Enforces strict multi-tenant authorization (`account.user_id == user_id`).
   - Rejects cross-currency transfers with `CurrencyMismatchError` (HTTP 422).
   - Prevents duplicate operations via tag-based idempotency caching (`idempotency:<key>`).
   - Implements immutable transaction reversals using compensating entries.

3. **`BudgetService`** (`src/services/budget_service.py`):
   - Configures monthly category spending caps.
   - Aggregates actual monthly expenses using SQL queries that strictly exclude internal transfers and income.
   - Evaluates visual threshold alert statuses: `NORMAL` ($< 80\%$), `WARNING` ($80\% - 99.99\%$), `EXCEEDED` ($\ge 100\%$).
   - Carries forward unspent balances from the prior month when `rollover_enabled=True`.

4. **`SavingsGoalService`** (`src/services/goal_service.py`):
   - Sets savings targets with target dates.
   - Tracks incremental contributions, decrementing withdrawals, and progress percentages.
   - Automatically sets `is_achieved = True` when cumulative savings reach or exceed target.

5. **`LoanService`** (`src/services/loan_service.py`):
   - Generates exact fixed-rate amortization schedules using Decimal compound interest mathematics: $\text{EMI} = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$.
   - Resolves rounding fractional cents in the final instalment ($n$), ensuring remaining balance reaches exactly ₹0.00.
   - Records repayments with explicit principal reduction vs. interest expense separation.
   - Automatically marks loans as settled when balance reaches zero.

6. **`RecurringService`** (`src/services/recurring_service.py`):
   - Computes calendar recurrence intervals across `DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`, and `YEARLY` schedules.
   - Identifies active due rules and spawns validated transactions via `TransactionService`.
   - Prevents duplicate executions on the same date.
   - Provides schedule pausing and resumption.

7. **`InvestmentService`** (`src/services/investment_service.py`):
   - Tracks portfolio security purchases with weighted-average cost basis recalculation: $\text{Cost Basis} = \frac{\text{Previous Cost} + \text{New Trade Amount}}{\text{Total Units}}$.
   - Enforces holding sufficiency on sell operations with `InsufficientUnitsError` (HTTP 422).
   - Calculates gross proceeds, net proceeds after fees, cost of sold units, and realized capital gains/losses.
   - Records dividend income without altering held unit counts.

### 8.2 Phase 3 Gate Transition
Phase 3 was completed, approved, and handed off with all 87 tests passing and zero blockers.

---

## 9. Phase 4 Architecture & Security Remediation Summary

Phase 4 delivers the complete REST API interface, JWT authentication foundation, and data portability pipeline.

### 9.1 Delivered REST Routers & Domain Endpoints
- `src/api/routers/auth.py`: Registration (`POST /register`), OAuth2 form login (`POST /token`), profile lookup (`GET /me`).
- `src/api/routers/accounts.py`: Account listing and detail.
- `src/api/routers/transactions.py`: Income, expense, inter-account transfer, reversal, and balance reconciliation.
- `src/api/routers/budgets.py`: Category budget allocations and utilization metrics.
- `src/api/routers/goals.py`: Savings milestone targets, contributions, withdrawals, and progress tracking.
- `src/api/routers/loans.py`: Loan debt tracking, fixed-rate amortization schedules, and payments.
- `src/api/routers/investments.py`: Security buy/sell trades with weighted-average cost basis and dividends.
- `src/api/routers/recurring.py`: Recurrence rules, execution scheduling, and pause/resume.
- `src/api/routers/data_portability.py`: Statement import dry-run preview and batch commit, CSV/XLSX transaction export, user data JSON backup snapshot, and dry-run backup validation.
- `src/api/routers/health.py`: Health and readiness probe.

### 9.2 Security Remediation: Administrative CLI for Legacy User Enrollment
- **Vulnerability Identified**: The initial `POST /api/v1/auth/enroll` endpoint allowed any unauthenticated caller to set a password for existing accounts using only their email address.
- **Remediation Executed**:
  1. Completely removed `POST /api/v1/auth/enroll` from `src/api/routers/auth.py`.
  2. Removed `UserEnrollPassword` schema from `src/schemas/user.py` and `src/schemas/__init__.py`.
  3. Verified endpoint absence from FastAPI route registration and OpenAPI schema (`/openapi.json`).
  4. Implemented `src/cli/enroll.py` (`python -m src.cli.enroll --email <email>`):
     - Executed locally from an administrative terminal on the host.
     - Verifies user exists in the database prior to prompting for passwords.
     - **Anti-Overwrite Protection**: Accounts with existing password hashes cannot be re-enrolled or overwritten.
     - Interactive masked password prompt with confirmation (`getpass.getpass`).
     - Command-line arguments for passwords (`--password`) are strictly forbidden.
     - Enforces password complexity constraints (8–128 characters).
     - Prompts explicit operator confirmation (`[y/N]`) before database write.
     - Commits atomically with rollback on error.
     - Zero credential or hash leakage to stdout, stderr, or shell history.
  5. Implemented comprehensive test suites:
     - `tests/unit/test_cli_enroll.py` (14 unit tests).
     - `tests/integration/test_auth_api.py` (updated to verify 404 on `/enroll` and OpenAPI schema absence).

### 9.3 Phase 4 Gate Transition
Phase 4 and its security remediation were fully verified, committed, and approved.

---

## 10. Phase 5 Architecture, Frontend Core UI & Phase 6 Readiness

Phase 5 delivers the complete reactive Streamlit frontend application consuming FastAPI backend REST endpoints.

### 10.1 Frontend Architecture & Component Structure
- **Application Controller (`src/frontend/app.py`)**: Configures dark theme page layout, enforces the session authentication barrier, manages sidebar navigation, and routes between views.
- **Decoupled API Client (`src/frontend/api_client.py`)**: Intermediates all HTTP communications with FastAPI using Bearer JWT authentication, structured error handling, 401 session expiration handling, and zero automatic retries on POST.
- **Design System (`src/frontend/components/ui.py`)**: Implements the approved color tokens (`#0B1120`, `#151E30`, `#1D2940`, `#38BDF8`, `#22C55E`, `#F87171`), custom CSS styles, and currency display utilities.
- **Modular Views (`src/frontend/views/`)**:
  1. `login.py`: Authentication portal with masked password entry and error display.
  2. `dashboard.py`: Accounts overview, isolated currency totals, monthly cash flow, and budget utilization cards.
  3. `accounts.py`: Directory, create form, metadata edit expander, and archiving with confirmation.
  4. `transactions.py`: Paginated ledger, income/expense entry form, inter-account transfers, and compensating reversals with confirmation.
  5. `budgets.py`: Monthly category spending caps, utilization progress bars, remaining amounts, and overspending indicators.
  6. `settings.py`: Profile data, default INR currency preference display, runtime architecture specs, and session logout.

### 10.2 Phase 6 Implementation Readiness
Phase 6 will build dedicated Streamlit user interfaces for advanced financial features implemented in the Phase 3 domain layer and Phase 4 API:

- **Phase 6 Scope**:
  - Savings Goals Page: Milestone target setting, progress bars, and contribution/withdrawal forms.
  - Loans & Debt Page: Liability tracking, amortization schedules, and payment processing.
  - Investments Page: Asset portfolio, holdings overview, and buy/sell/dividend trade entry.
  - Recurring Transactions Page: Recurrence rule management, due schedules, and pause/resume controls.
- **Gate Status**:
  - Execution is **HALTED** at the Phase 5 completion gate.
  - Awaiting user approval to proceed to Phase 6.

---

## 11. Phase 8 System Hardening, Local MVP Packaging & Operational Runbook

### 11.1 System Hardening Audit Summary
1. **Negative & Zero Amount Protection**: Strictly enforced via Pydantic v2 schemas across all domain entities (HTTP 422).
2. **Double-Entry Value Conservation**: Atomically validated in `TransactionService.record_transfer` and reversed via compensating entries in `TransactionService.reverse_transaction`. Reversals are strictly idempotent.
3. **Multi-Tenant Isolation**: Verified across all REST endpoints. User B cannot access or mutate User A's accounts, transactions, budgets, goals, loans, or investments (HTTP 404).
4. **Permanent Removal of Public Enrollment**: `POST /api/v1/auth/enroll` returns HTTP 404. Account password provisioning is restricted to the local administrative CLI (`src/cli/enroll.py`).
5. **Data Portability & Backup Tamper Defense**: CSV exports escape formula injection prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`). Backup dry-run validation enforces schema versioning ("1.0.0"). Destructive restore (`REPLACE_USER_DATA`) is strictly non-executable and disabled.

### 11.2 Windows 11 Local MVP Packaging & Startup Guide
To run the application locally on Windows 11 using `uv`:

1. **Step 1: Configuration**:
   ```cmd
   copy .env.example .env
   ```
   (Verify `BACKEND_HOST=127.0.0.1`, `BACKEND_PORT=8000`, `FRONTEND_PORT=8501`, `DATABASE_URL=sqlite:///./data/finance.db`).

2. **Step 2: Administrative User Password Enrollment**:
   ```cmd
   scripts\enroll_user.bat
   ```
   Follow the interactive prompts to assign an initial secure password to `user@local.dev`.

3. **Step 3: Start the Backend API Server**:
   ```cmd
   scripts\run_backend.bat
   ```
   *Health Check*: Open `http://127.0.0.1:8000/health` (HTTP 200 `{"status": "healthy", "database": "connected"}`).

4. **Step 4: Start the Frontend Web Application**:
   - Via PowerShell (Recommended):
     ```powershell
     powershell -ExecutionPolicy Bypass -File scripts\run_frontend.ps1
     ```
   - Or via Command Prompt:
     ```cmd
     scripts\run_frontend.bat
     ```
   Opens browser at `http://127.0.0.1:8501`. Enter your credentials or switch to "Create Account" tab. Both launchers automatically resolve the repository root, export `PYTHONPATH`, avoid duplicate processes on port 8501, and invoke Streamlit via `uv run`.

5. **Step 5: Shutdown**:
   Press `Ctrl+C` in both terminal windows to gracefully terminate the backend and frontend processes.

### 11.3 Local Quality Gate Verification
Run the consolidated quality verification script:
```cmd
scripts\verify_system.bat
```
Executes `pytest --cov=src`, `ruff check .`, `ruff format --check .`, and `mypy`.

### 11.4 Phase 8 Final Release Gate Status
- **Automated Tests**: **192 passed, 0 failed** in 15.2s.
- **Test Coverage**: **81%** across `src/` (4,748 statements, 898 missed).
- **Security Audits**: Bandit: 0 issues; pip-audit: 0 vulnerabilities.
- **Data Preservation**: Existing financial records in `data/finance.db` intact.
- **Release Readiness Verdict**: **READY FOR LOCAL MVP TESTING**.
- **PUBLIC DEPLOYMENT IS NOT AUTHORIZED. EXECUTION IS HALTED AT THE PHASE 8 APPROVAL GATE.**





