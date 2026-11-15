# Personal Finance Tracker — Quality Assurance & Testing Strategy

> **DOCUMENT**: `docs/TESTING.md`  
> **STATUS**: APPROVED BASELINE  
> **STACK**: Python 3.12 (Pytest, pytest-asyncio, HTTPX, Bandit, pip-audit)  
> **CURRENT PHASE**: Phase 3 — Core Accounting Engine, Financial Services & Domain Logic (COMPLETED)

---

## 1. Quality Assurance Philosophy & Testing Pyramid

Financial applications require deterministic accuracy, ACID compliance, and zero tolerance for calculation bugs. The testing framework adopts the **Testing Pyramid**:

```
           / \
          /   \
         / E2E \       10% (Streamlit AppTest / Full-Journey HTTPX)
        /───────\
       / Integr. \     20% (Pytest + HTTPX AsyncClient + In-Memory DB)
      /───────────\
     /    Unit     \   70% (Pytest) — Decimal calculations, Pydantic & Services
    /───────────────\
```

- **Target Coverage**: Minimum 85% branch coverage on Domain Services and financial calculation engines; 100% schema validation coverage on Pydantic models.

---

## 2. Testing Framework Architecture

### Pytest & pytest-asyncio (Unit & Integration)
- **Tool**: `pytest` with `pytest-asyncio` for asynchronous test coroutines.
- **Purpose**: Fast test discovery, parameterized tests, and modular fixtures (`conftest.py`).
- **Scope**:
  - Exact decimal currency arithmetic (`money.py`).
  - Domain business logic (`AccountService`, `TransactionService`, `BudgetService`).
  - Pydantic v2 validation models and boundary constraints.
  - SQLAlchemy models and repository methods.

### HTTPX AsyncClient (API Integration)
- **Tool**: `httpx.AsyncClient` with `ASGITransport(app=app)`.
- **Purpose**: In-memory HTTP dispatch directly against the FastAPI application without spinning up a live network port.
- **Scope**:
  - Full HTTP request/response cycle for all `/api/v1/*` endpoints.
  - Authentication headers, JWT verification, and 401/403/422 status code validation.
  - JSON payload serialization and deserialization.

### Streamlit App Testing (E2E & UI Verification)
- **Tool**: `streamlit.testing.v1.AppTest`.
- **Purpose**: Programmatic simulation of user interactions with Streamlit forms, buttons, and session state without a browser harness.
- **Scope**:
  - Core journey: User creates account $\to$ logs transaction $\to$ checks dashboard metrics $\to$ inspects budget utilization.

---

## 3. Test Suites & Categorization

### 1. Unit Testing
- **Location**: `tests/unit/`
- **Focus**: Pure functions and isolated domain components.
- **Key Test Cases**:
  - Decimal precision tests: verify that `Decimal("0.10") + Decimal("0.20") == Decimal("0.30")`.
  - Rejection of invalid dates, negative amounts, or malformed category names in Pydantic models.
  - Calculation of category budget utilization percentages and alert thresholds.

### 2. Integration Testing
- **Location**: `tests/integration/`
- **Focus**: API endpoints interacting with an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`).
- **Key Test Cases**:
  - `POST /api/v1/transactions`: Creates transaction, updates account balance, and consumes category budget.
  - `POST /api/v1/transactions/transfer`: Atomic transfer decrements source account and increments destination account.
  - Rollback on failure: Verify that an error midway through a transfer rolls back both accounts.
  - Account deletion protection: Deleting an account with transactions returns HTTP 400 with a descriptive error.

### 3. Database & Migration Testing
- **Location**: `tests/database/`
- **Focus**: Alembic schema migrations and data integrity.
- **Key Test Cases**:
  - Test migration upgrade: `alembic upgrade head` applies cleanly on an empty database.
  - Test migration downgrade: `alembic downgrade -1` rolls back cleanly without leaving orphan tables.
  - Seed script integrity: Verify default categories and demo user populate correctly without duplicate key errors.

### 4. Security Testing
- **Location**: `tests/security/`
- **Focus**: Authorization, injection resistance, and tenant isolation.
- **Key Test Cases**:
  - Tenant scoping: User A cannot read, edit, or delete transactions owned by User B.
  - SQL injection payload testing: Ensure raw SQL strings in filter fields are treated as literal strings.
  - Boundary stress testing: Large numbers (`Decimal("99999999999999.99")`), zero amounts, and negative numbers.

---

## 5. Security & Dependency Verification Tools

Every CI run executes:
```bash
# 1. Static Application Security Testing (SAST)
bandit -r src/ -ll -ii

# 2. Dependency Vulnerability Audit
pip-audit

# 3. Static Type Checking
mypy --strict src

# 4. Code Formatting & Linting
ruff check .
```

---

## 6. Phase Completion Criteria Gates

A development phase is marked complete ONLY when all gate criteria are met:

| Phase | Quality, Testing & Security Gate Criteria |
| :--- | :--- |
| **Phase 0** | All 12 foundational documents exist, Python architecture established, Bandit & pip-audit policies set, explicit user approval. |
| **Phase 1** | Virtual environment functional, `pyproject.toml` locked, `ruff check` passes, Pytest discovers empty test suite, `pip-audit` reports 0 CVEs. |
| **Phase 2** | Alembic migrations apply cleanly to SQLite, models define all financial entities, seed script populates default categories. |
| **Phase 3** | Domain services and decimal money utilities achieve 90%+ branch coverage in Pytest; zero floating-point math detected. |
| **Phase 4** | FastAPI endpoints return standardized `GenericResponse[T]`, HTTPX integration tests pass for all CRUD operations, Pydantic validation handles 100% boundary cases. |
| **Phase 5** | Streamlit UI framework operational, custom Plotly charts render cleanly, session state helpers tested. |
| **Phase 6** | Full Streamlit application pages functional; AppTest / HTTPX verifies account, transaction, and budget user journeys. |
| **Phase 7** | Pandas analytics aggregate historical data, Plotly graphs render without errors, CSV/Excel export/import passes round-trip tests. |
| **Phase 8** | Full Pytest test suite passes (100% pass rate); Bandit SAST reports 0 issues; pip-audit reports 0 vulnerabilities; PostgreSQL migration verified with `verify_pg_migration.py`; Docker containers build and launch cleanly; production release certified. |

---

## 7. Phase 2 Verification & Test Results

### 7.1 Test Execution Metrics
- **Total Automated Tests**: 41 passed, 0 failed, 0 skipped (100% pass rate).
- **Execution Time**: ~2.70 seconds.
- **Code Coverage**: 89% across `src/` (892 statements, 97 misses, mostly Phase 3-5 empty stub branches).
- **Test Distribution**:
  - **Unit Tests (31 tests)**:
    - `tests/unit/test_account_service.py` (6 tests: create, duplicate conflict, not found, tenant isolation, update, archive)
    - `tests/unit/test_config.py` (2 tests: defaults, invalid environment validation)
    - `tests/unit/test_frontend.py` (2 tests: api client initialization, unreachable server handling)
    - `tests/unit/test_models.py` (4 tests: user creation, account relationship, foreign key enforcement, cascade delete)
    - `tests/unit/test_money.py` (4 tests: decimal arithmetic, string conversion, invalid input, currency formatting)
    - `tests/unit/test_phase2_models.py` (10 tests: category hierarchy/uniqueness, double-entry ledger cascade, positive amount check constraints, account delete restriction, budget constraints/uniqueness, savings goal constraints, loan debts & payment schedules, recurring rules, investment models & 4-decimal quantity precision, audit log persistence)
  - **Integration Tests (10 tests)**:
    - `tests/integration/test_accounts_api.py` (9 tests: full CRUD, validation, 404, default INR currency, archive)
    - `tests/integration/test_health_api.py` (2 tests: root `/health`, `/api/v1/health`)
    - `tests/integration/test_migrations.py` (1 test: full upgrade, downgrade, re-upgrade lifecycle)

### 7.2 Static Quality & Security Audits
- **Ruff Linter**: `ruff check .` -> **0 errors** (all checks passed).
- **Ruff Formatter**: `ruff format --check .` -> **48 files correctly formatted**.
- **Mypy Type Checking**: `mypy` -> **Success: no issues found in 36 source files**.
- **Bandit SAST**: `bandit -r src/` -> **0 issues identified** (2,628 lines scanned).
- **pip-audit**: `pip-audit` -> **0 known vulnerabilities found**.
- **Runtime Probes**:
  - FastAPI server (`src.api.main:app`) on port 8005 -> `/health` returned 200 OK (`database_connected: True`).
  - Streamlit UI (`src/frontend/app.py`) on port 8505 -> `/_stcore/health` returned 200 OK.

---

## 8. Phase 3 Verification & Test Results

### 8.1 Test Execution Metrics
- **Total Automated Tests**: 87 passed, 0 failed, 0 skipped (100% pass rate).
- **Execution Time**: ~2.3 seconds.
- **Test Distribution (74 Unit, 13 Integration)**:
  - **Phase 3 Services Unit Tests (46 tests)**:
    - `tests/unit/test_ledger_service.py` (8 tests: balanced entries pass, empty/unbalanced fail, non-positive fail, asset account balance, liability balance, reconciliation matching and discrepancy, not found handling).
    - `tests/unit/test_transaction_service.py` (10 tests: income debit, expense credit, transfer credit/debit atomic commit, same account error, currency mismatch error, cross-user error, idempotency caching, compensating transaction reversal, non-positive validation, foreign category error).
    - `tests/unit/test_budget_service.py` (7 tests: budget creation, update existing, invalid amount, income category rejection, threshold status calculation [NORMAL, WARNING, EXCEEDED], previous month rollover unspent calculation, transfer exclusion).
    - `tests/unit/test_goal_service.py` (6 tests: goal creation, invalid target, contributions and achievement toggle, withdrawals, overdraft rejection, not found).
    - `tests/unit/test_loan_service.py` (5 tests: fixed-rate amortization mathematical accuracy, 0% interest division, loan creation with schedules, repayment and liability settlement, invalid inputs).
    - `tests/unit/test_recurring_service.py` (5 tests: next occurrence calculation across all frequencies, rule creation, validation, due rule execution with duplicate prevention, pause and resume).
    - `tests/unit/test_investment_service.py` (5 tests: initial purchase with cost basis, subsequent purchases with weighted-average cost basis, sale with realized gains and holding reduction, insufficient units error, dividend logging).
  - **Phase 1-2 Existing Protected Regression Tests (41 tests)**:
    - `tests/unit/test_account_service.py` (6 tests)
    - `tests/unit/test_config.py` (2 tests)
    - `tests/unit/test_frontend.py` (2 tests)
    - `tests/unit/test_models.py` (4 tests)
    - `tests/unit/test_money.py` (4 tests)
    - `tests/unit/test_phase2_models.py` (10 tests)
    - `tests/integration/test_accounts_api.py` (10 tests)
    - `tests/integration/test_health_api.py` (2 tests)
    - `tests/integration/test_migrations.py` (1 test)

### 8.2 Static Quality & Security Audits
- **Ruff Linter**: `ruff check .` -> **0 errors** (all checks passed).
- **Ruff Formatter**: `ruff format --check .` -> **75 files correctly formatted**.
- **Mypy Type Checking**: `mypy` -> **Success: no issues found in 56 source files**.
- **Bandit SAST**: `bandit -r src/` -> **0 issues identified** (4,969 lines scanned).
- **pip-audit**: `pip-audit` -> **0 known vulnerabilities found**.
- **Database Record Preservation**: `Primary Checking ('USD', 1500.00)` verified untouched in `data/finance.db`.


