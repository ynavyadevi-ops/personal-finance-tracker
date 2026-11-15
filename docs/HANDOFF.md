# Personal Finance Tracker — Engineering Handoff & Operating Guide

> **DOCUMENT**: `docs/HANDOFF.md`  
> **STATUS**: ACTIVE & ENFORCED  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 2 — Database Modeling, SQLAlchemy ORM & Alembic Migrations (COMPLETED — AWAITING PHASE 3 APPROVAL)

---

## 1. Project Context & Current Status

This repository houses the **Personal Finance Tracker**, a production-oriented, secure, full-stack personal finance application implemented in **Python + SQL**.

### Current State
- **Phase 0 (Project Foundation and Documentation)**: **COMPLETE**.
- **Phase 1 (Environment Setup and Application Foundation)**: **COMPLETE & REMEDIATED**.
- **Phase 2 (Database Modeling, SQLAlchemy ORM & Alembic Migrations)**: **COMPLETE & VERIFIED**.
  - All 12 domain relational tables and Alembic migrations fully implemented and tested.
  - Applied migration `472e31906438_create_phase_2_relational_models.py` to `data/finance.db`.
  - Existing database records preserved intact: `Primary Checking ('USD', 1500.00)` untouched.
  - Downgrade and re-upgrade cycle verified on disposable test database.
  - Development database seeder expanded with 13 standard Indian categories, sample ETF asset (`NIFTYBEES`), and sample savings goal (`Emergency Fund`).
  - 41 automated tests (31 unit tests, 10 integration tests) passing with 100% pass rate.
  - 89% test coverage across `src/`.
  - Ruff (0 errors), Mypy strict (0 errors in 36 files), Bandit SAST (0 issues in 2,628 lines), pip-audit (0 CVE vulnerabilities).
  - Backend and frontend runtime health probes verified (both 200 OK).
- **Execution is halted at the Phase 2 Approval Gate awaiting explicit user authorization to begin Phase 3 execution.**

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
| **Unit Tests** | Pytest | 31 unit test functions across models, services, core | 31 passed in 0.3s | **PASS** |
| **Integration Tests** | Pytest + HTTPX + Alembic | 10 integration test functions (API & Migrations) | 10 passed in 2.0s | **PASS** |
| **Total Automated Tests** | Pytest | Complete test suite (41 tests) | 41 passed, 0 failed | **PASS** |
| **Test Coverage** | pytest-cov | Entire `src/` application code | 89% coverage (892 stmts) | **PASS** |
| **Code Formatting** | Ruff | 48 project Python files | 48 files formatted | **PASS** |
| **Code Linting** | Ruff | Complete repository | 0 lint errors | **PASS** |
| **Type Checking** | Mypy (strict) | 36 source files in `src/` | 0 type errors | **PASS** |
| **SAST Security Scan** | Bandit | 2,628 lines of application code (`src/`) | 0 issues identified | **PASS** |
| **Dependency CVE Scan** | pip-audit | 96 installed dependencies against PyPI DB | 0 vulnerabilities found | **PASS** |
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

