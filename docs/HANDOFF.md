# Personal Finance Tracker — Engineering Handoff & Operating Guide

> **DOCUMENT**: `docs/HANDOFF.md`  
> **STATUS**: ACTIVE & ENFORCED  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 1 Remediation & Review (AWAITING PHASE 2 APPROVAL)

---

## 1. Project Context & Current Status

This repository houses the **Personal Finance Tracker**, a production-oriented, secure, full-stack personal finance application implemented in **Python + SQL**.

### Current State
- **Phase 0 (Project Foundation and Documentation)**: **COMPLETE**.
- **Phase 1 (Environment and Application Foundation)**: **COMPLETE & REMEDIATED**.
  - Isolated Python 3.12.13 virtual environment established with locked dependencies (`requirements.lock`).
  - Modular FastAPI backend implemented with health checks and initial financial accounts REST endpoints.
  - SQLite database persistence configured with SQLAlchemy 2.0 and Alembic migrations (`fba246fe5321`).
  - Streamlit frontend application built with a dark fintech UI and decoupled HTTP API communication.
  - 30 automated tests (18 unit tests, 12 API integration tests) passing with 100% pass rate.
  - Strict type checking (Mypy) and linting/formatting (Ruff) passing with zero errors across all source files.
  - Security audit completed with zero Bandit SAST issues and zero pip-audit CVEs.
- **Work is halted at the Phase 1 Approval Gate awaiting explicit user authorization to begin Phase 2 execution.**

---

## 2. Phase 1 Remediation Review Findings & Action Plans

### Finding 1: Default Currency Alignment (INR vs USD)
- **Review Finding**: The approved project currency is **INR (₹)**, whereas the initial scaffolding and documentation defaulted to **USD ($)**.
- **System-Wide Reference Inventory**:
  1. *SQLAlchemy Models* (`src/db/models/account.py`): `currency: Mapped[str] = mapped_column(String(3), default="USD")`.
  2. *Pydantic Schemas* (`src/schemas/account.py`): `currency: str = Field(default="USD", ...)`.
  3. *Database Seed* (`src/db/seed.py`): Initial checking account seeded with `currency="USD"`.
  4. *Monetary Formatting* (`src/core/money.py`): `format_currency(..., currency_symbol="$")`.
  5. *Streamlit Frontend* (`src/frontend/app.py`): Label `Opening Balance ($)` and text input default `"USD"`.
  6. *Alembic Migrations* (`alembic/versions/fba246fe5321_*.py`): Created column `currency String(3)` without server-level default.
  7. *Documentation* (`docs/ARCHITECTURE.md`, `docs/SPEC.md`, `docs/DEVELOPMENT_RULES.md`): References to `USD` / `$`.
- **Proposed Safe Correction Plan**:
  1. *Preserve Existing Financial Records*: In accordance with financial ledger integrity, the existing local database row (`'Primary Checking'`, `1500.00`) is preserved without silent numerical conversion. No exchange-rate multiplication or data mutation will be performed.
  2. *Applied Migration Immutability*: The existing migration `fba246fe5321` is never modified in place.
  3. *New Safe Migration*: If server-level column defaults or data migrations are approved, author a new forward migration (`alembic revision -m "set_default_currency_inr"`).
  4. *Application Defaults Correction*: Update Python-level defaults in `src/db/models/account.py`, `src/schemas/account.py`, `src/core/money.py` (default `currency_symbol="₹"`), `src/frontend/app.py` (`Opening Balance (₹)`, default `"INR"`), and `src/db/seed.py` (`currency="INR"`).
  5. *Documentation & Test Alignment*: Update documentation and test assertions to reflect `INR` and `₹`.

---

### Finding 2: Authoritative Roadmap Reconciliation (Phases 0–8)
- **Review Finding**: The generated documentation referenced 10 phases labeled 0–9, whereas the original approved roadmap comprised **Phases 0–8** (9 sequential phases total).
- **Required Inclusions**: The roadmap must explicitly assign ownership of:
  - Recurring transactions (scheduled bills, automated rule queues).
  - Savings goals (target amounts, milestone dates, allocation tracking).
  - Loans & debts (liability tracking, interest calculations, payoff schedules).
  - Investments (portfolio holdings, asset types, cost basis, valuation).
  - AI financial insights (spending trend analysis, assisted categorization with explicit user consent).
- **Proposed Single Authoritative Roadmap (Phases 0–8)**:
  - **Phase 0: Project Foundation and Documentation** *(Completed)*
  - **Phase 1: Environment Setup, Python Tooling & Core Project Scaffolding** *(Completed)*
  - **Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations** *(Next Phase)*
    - Comprehensive data models: `User`, `FinancialAccount`, `Category`, `Transaction`, `Budget`, `SavingsGoal`, `LoanDebtSchedule`, `RecurringRule`, `AuditLog`.
  - **Phase 3: Core Accounting Engine, Financial Services & Domain Logic**
    - Double-entry balance calculation, atomic transfer transactions, Decimal precision.
    - Recurring transaction rule queue engine.
    - Savings goal progress calculators & loan amortization payoff math.
  - **Phase 4: FastAPI REST API & Data Portability Services**
    - REST endpoints for Accounts, Transactions, Budgets, Goals, Loans, Investments, Recurring Rules.
    - Bank statement CSV/Excel import pipeline (Pandas parsing, deduplication, column mapping) & RFC 4180 export.
  - **Phase 5: Streamlit Frontend Core UI & Core Pages**
    - App shell, dark fintech styling, navigation state.
    - Core pages: Dashboard metrics, Accounts (protected CRUD), Transaction Ledger (Income/Expense/Transfer), Budgets.
  - **Phase 6: Advanced Feature Pages & Tracking**
    - Savings Goals tracking page.
    - Loans & Debt payoff calculator page.
    - Investment portfolio tracking page.
    - Recurring rules management page.
  - **Phase 7: Analytics, Plotly Visualizations & AI Insights**
    - Interactive Plotly analytics: Cash flow comparisons, category expense donuts, net worth trajectory.
    - AI financial insights (rule-based spending trends, optional AI categorization with explicit user consent).
  - **Phase 8: Comprehensive Verification, Security Auditing & Production Readiness**
    - Complete Pytest and HTTPX test suite (>85% coverage).
    - Security audits: Bandit SAST scan, `pip-audit` CVE verification, OWASP compliance verification.
    - PostgreSQL migration verification (`verify_pg_migration.py`), Dockerization, and production release deployment.

---

### Finding 3: Existing Account Functionality (Designated Protected Status)
- **Review Finding**: Account CRUD endpoints, service layer, and UI forms were scaffolded in Phase 1 ahead of the original Phase 2/4/6 schedule.
- **Mandate**: In accordance with user directives, this functionality **MUST NOT** be removed, rewritten, or discarded.
- **Protected Components**:
  - `src/db/models/account.py`: `FinancialAccount` entity model and `AccountType` enum.
  - `src/repositories/account_repo.py`: `AccountRepository` with query isolation.
  - `src/services/account_service.py`: `AccountService` enforcing unique account names, decimal opening balances, and soft-delete archiving.
  - `src/api/routers/accounts.py`: Endpoints `GET /api/v1/accounts`, `POST /api/v1/accounts`, `GET /api/v1/accounts/{id}`, `PATCH /api/v1/accounts/{id}`, `DELETE /api/v1/accounts/{id}`.
  - `src/frontend/app.py`: Accounts page tab with active account cards, balance display, and new account registration form.
  - `src/frontend/api_client.py`: HTTP client functions for listing, creating, and archiving accounts.
- **Regression Protection Suite**:
  - Authored `tests/unit/test_account_service.py` containing 6 unit regression tests verifying creation, duplicate conflicts, not-found handling, multi-tenant isolation, updating, and archiving.
  - Added integration regression tests in `tests/integration/test_accounts_api.py` verifying zero-balance accounts, archived account inclusion, and explicit currency handling.
  - Total account test coverage: 15 dedicated regression tests guaranteeing zero functional degradation.

---

## 3. Instructions for Successor Developers & AI Agents

When resuming or continuing work on this repository:

1. **Read Before Executing**:
   Before executing commands or editing code, read [AGENTS.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/AGENTS.md) and all documents in the `docs/` folder.
2. **Respect the Active Phase**:
   Inspect [docs/PHASES.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/PHASES.md). Execute **ONLY** the tasks specified for the currently authorized phase. Never pre-implement future phase tasks.
3. **Preserve Decimal Invariants**:
   Never use `float` for currency. Always use Python's `decimal.Decimal` and SQLAlchemy `Numeric(18, 2)`.
4. **Architectural Separation**:
   Streamlit frontend components (`src/frontend/`) **MUST NOT** import SQLAlchemy models or query the database directly. They must interact with data strictly through `src/frontend/api_client.py` calling the FastAPI backend.
5. **Enforce Approval Gates**:
   At the end of every phase, run the required automated test suites and security audits (`bandit`, `pip-audit`), generate a comprehensive Phase Completion Report, and **STOP**. Do not proceed to the next phase without explicit user authorization.

---

## 4. Developer & Environment Command Cheatsheet

### Environment Setup & Package Management
```bash
# Activate on Windows:
.venv\Scripts\activate
# Activate on Unix/macOS:
source .venv/bin/activate

# Install locked dependencies
uv pip install -r requirements.txt
```

### Code Quality, Linting & Type Checking
```bash
# Format code using Ruff
ruff format .

# Lint and check code using Ruff
ruff check . --fix

# Static type check using Mypy in strict mode
mypy
```

### Database & Migrations
```bash
# Generate a new Alembic migration revision
alembic revision --autogenerate -m "describe_migration"

# Apply migrations to database
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Populate database with seed data
python -m src.db.seed
```

### Running the Application
```bash
# Terminal 1: Launch FastAPI backend server (Port 8000)
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Launch Streamlit web dashboard (Port 8501)
streamlit run src/frontend/app.py --server.port 8501
```

### Automated Testing
```bash
# Run all Pytest suites
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Security & Supply-Chain Audits
```bash
# Static Application Security Testing (Bandit)
bandit -r src/ -ll -ii

# Dependency Vulnerability Audit (pip-audit)
pip-audit
```

---

## 5. Actual Verification Results

| Check / Tool | Actual Command Executed | Result / Output Summary | Status |
| :--- | :--- | :--- | :--- |
| **Pytest Suite** | `pytest` | **30 passed, 0 failed** in 1.41s across 7 test modules | **PASS** |
| **Ruff Linter** | `ruff check .` | **All checks passed** | **PASS** |
| **Ruff Formatter** | `ruff format --check .` | **38 files already formatted** | **PASS** |
| **Mypy Type Checker**| `mypy` | **Success: no issues found in 28 source files** (strict mode) | **PASS** |
| **Bandit SAST** | `bandit -r src/` | **0 issues identified** across 1,381 LOC (Zero High/Med/Low) | **PASS** |
| **pip-audit** | `pip-audit` | **No known vulnerabilities found** across all 96 dependencies | **PASS** |
| **FastAPI Startup** | In-process uvicorn server startup probe | **HTTP 200 OK** on `/health` (`status: healthy`, `database_connected: True`) | **PASS** |
| **Streamlit Startup**| `AppTest.from_file("src/frontend/app.py").run()` | **Success: True**, clean execution with zero unhandled exceptions | **PASS** |

---

## 6. Approvals Completed & Gate Status

### Approved Remediation Actions Completed:
1. [x] **Default Currency Corrected to INR (₹)**: Applied across models, Pydantic schemas, UI labels, formatting utilities, seed script, tests, and documentation.
2. [x] **Financial Record Preservation**: Existing database records (`'Primary Checking'`, `1500.00`, `USD`) are preserved intact without automated conversion or relabeling. Previously applied migration `fba246fe5321` left unmodified.
3. [x] **Authoritative Roadmap Formally Adopted**: Authoritative 9-phase lifecycle (**Phase 0 through Phase 8**) adopted in `docs/PHASES.md`, `README.md`, `docs/DECISIONS.md` (ADR-014), and `docs/CHANGELOG.md`.
4. [x] **Protected Account Functionality Safeguarded**: Existing Account CRUD functionality preserved and defended by 15 dedicated regression tests.

### Gate Requirement:
- **Phase 1 Remediation is COMPLETE**.
- **Phase 2 functionality is NOT started.**
- **Development is strictly HALTED awaiting explicit user instruction to begin Phase 2.**
