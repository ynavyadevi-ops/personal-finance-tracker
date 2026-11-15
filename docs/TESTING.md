# Personal Finance Tracker — Quality Assurance & Testing Strategy

> **DOCUMENT**: `docs/TESTING.md`  
> **STATUS**: APPROVED BASELINE  
> **STACK**: Python 3.12 (Pytest, pytest-asyncio, HTTPX, Bandit, pip-audit)  
> **CURRENT PHASE**: Phase 4 — FastAPI REST API & Data Portability Services (COMPLETED)

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

---

## 9. Phase 4 Verification & Test Results

### 9.1 Test Execution Metrics
- **Total Automated Tests**: 134 passed, 0 failed, 0 skipped (100% pass rate).
- **Execution Time**: ~6.6 seconds.
- **Overall Code Coverage**: 89% across `src/` (2,894 statements, 319 missed).
- **Test Distribution (88 Unit, 46 Integration)**:
  - **Phase 4 Integration Tests (33 tests)**:
    - `tests/integration/test_auth_api.py` (7 tests: registration with Argon2id hash, OAuth2 form login with JWT issue, invalid credentials failure, public `/enroll` returns 404, public `/enroll` absent from OpenAPI schema, `/me` profile retrieval without password hash, 401 unauthorized when missing token).
    - `tests/integration/test_transactions_api.py` (5 tests: income & expense double-entry recording, atomic inter-account transfer, compensating transaction reversal, mathematical balance reconciliation, cross-user isolation).
    - `tests/integration/test_budgets_api.py` (3 tests: set budget, category utilization with warning threshold, period budget list, cross-user category isolation).
    - `tests/integration/test_goals_api.py` (3 tests: milestone creation, contributions, withdrawals, progress calculations, cross-user isolation).
    - `tests/integration/test_loans_api.py` (3 tests: loan creation with fixed-rate amortization schedule, payment instalment processing, loan list, cross-user isolation).
    - `tests/integration/test_investments_api.py` (4 tests: security buy with weighted-average cost basis, holdings query, security sell with realized capital P&L, insufficient units rejection, dividend earnings log, cross-user isolation).
    - `tests/integration/test_recurring_api.py` (3 tests: recurring rule creation, due rule execution spawning double-entry transaction with duplicate prevention, pause and resume, cross-user isolation).
    - `tests/integration/test_data_portability_api.py` (5 tests: CSV statement import preview & duplicate detection, XLSX statement preview, atomic batch commit, CSV export with formula injection defense, XLSX workbook export, JSON backup snapshot export, dry-run schema validation).
  - **Administrative CLI Tests (14 unit tests)**:
    - `tests/unit/test_cli_enroll.py` (14 tests: legacy user enrollment success with Argon2id hash, user not found handling, anti-overwrite protection preventing re-enrollment, password confirmation mismatch, length boundaries [8-128 chars], operator cancellation, database rollback on commit error, CLI argument validation, `--password` flag rejection, and strict zero-leakage assertions ensuring passwords and hashes never appear in stdout/stderr).
  - **Protected Existing Unit & Integration Tests (87 tests)**:
    - All 87 Phase 1–3 regression tests continue to pass with zero modifications.

### 9.2 Static Quality & Security Audits
- **Ruff Linter**: `ruff check .` -> **0 errors** (all checks passed).
- **Ruff Formatter**: `ruff format --check .` -> **97 files correctly formatted**.
- **Mypy Type Checking**: `mypy` -> **Success: no issues found in 67 source files** (strict mode).
- **Bandit SAST**: `bandit -r src/` -> **0 issues identified** (6,867 lines scanned across `src/`).
- **pip-audit**: `pip-audit` -> **0 known vulnerabilities found**.
- **Database Record Preservation**: `Primary User ('user@local.dev', None)` and `Primary Checking ('USD', 1500.00)` verified intact in `data/finance.db`.

---

## 10. Phase 5 Verification & Test Results (Streamlit Frontend Core UI)

### 10.1 Test Execution Metrics
- **Total Automated Tests**: 151 passed, 0 failed, 0 skipped (100% pass rate).
- **Execution Time**: ~9.1 seconds.
- **Overall Code Coverage**: 83% across `src/` (3,611 statements, 604 missed).
- **Test Distribution (105 Unit, 46 Integration)**:
  - **Phase 5 Frontend Unit Tests (19 tests)**:
    - `tests/unit/test_frontend.py` (13 tests): ApiClient initialization, Bearer token injection, unreachable server error handling, OAuth2 login success and error handling, user profile retrieval, account CRUD (list, get, create, update, archive, reconcile), transaction operations (list, get, create, transfer, reverse), budget operations (period list, utilization, create), and monetary formatting across INR default, USD isolation, EUR/GBP/other symbols, and negative values.
    - `tests/unit/test_frontend_views.py` (6 tests): Login view structure and session expiration alerts, Dashboard multi-currency isolation without cross-currency addition, Accounts directory tabs, Transactions view empty account handling, Budgets period utilization progress, and Settings profile & default currency preference rendering.
  - **Protected Existing Tests (132 tests)**:
    - All 132 Phase 1–4 regression tests (87 core service/repo tests, 33 FastAPI integration tests, and 14 administrative CLI tests) continue to pass with zero regressions.

### 10.2 Static Quality & Security Audits
- **Ruff Linter**: `ruff check .` -> **0 errors** (all checks passed).
- **Ruff Formatter**: `ruff format --check .` -> **105 files correctly formatted**.
- **Mypy Type Checking**: `mypy` -> **Success: no issues found in 67 source files** (strict mode).
- **Bandit SAST**: `bandit -r src/` -> **0 issues identified** (8,077 lines scanned across `src/`).
- **pip-audit**: `pip-audit` -> **0 known vulnerabilities found**.
- **Database Record Preservation**: `Primary User ('user@local.dev', None)` and `Primary Checking ('USD', 1500.00)` verified intact in `data/finance.db`.

---

## 11. Phase 6 Verification & Test Results (Advanced Frontend Views)

### 11.1 Test Execution Metrics
- **Total Automated Tests**: 159 passed, 0 failed, 0 skipped (100% pass rate).
- **Execution Time**: 14.00 seconds.
- **Overall Code Coverage**: 80% across `src/` (4,278 statements, 843 missed).
- **Test Distribution (113 Unit, 46 Integration)**:
  - **Phase 6 Advanced Frontend Unit Tests (8 new tests, 27 total frontend tests)**:
    - `tests/unit/test_frontend.py` (+4 tests):
      - `test_api_client_goal_operations`: Savings goals listing, creation, progress tracking, contributions, and withdrawals.
      - `test_api_client_loan_operations`: Loan liabilities listing, schedule details retrieval, loan creation, and installment payment processing.
      - `test_api_client_investment_operations`: Portfolio holdings, buy security with weighted cost basis, sell security with realized capital gain/loss calculation, and dividend receipts.
      - `test_api_client_recurring_operations`: Recurring rules listing, due rule checking, template creation, due rule execution, pause, and resume.
    - `tests/unit/test_frontend_views.py` (+4 tests):
      - `test_render_goals_view`: Empty state rendering and milestone cards with funded progress bars and contribution forms.
      - `test_render_loans_view`: Empty state rendering and active liability summaries with amortization schedules and installment repayment forms.
      - `test_render_investments_view`: Valuation disclaimer, empty state handling, and portfolio positions with weighted-average cost basis per unit.
      - `test_render_recurring_view`: Due execution alerts with manual ledger posting triggers, active/paused rules directory, and schedule controls.
  - **Protected Existing Tests (151 tests)**:
    - All 151 Phase 1–5 regression tests (87 core service/repo tests, 33 FastAPI integration tests, 14 administrative CLI tests, and 17 Phase 5 frontend tests) continue to pass with zero regressions.

### 11.2 Windows Terminal Sandbox Pytest Diagnostic & Workaround Protocol
- **Diagnostic Finding**: When executing integration tests on Windows (`tests/integration/test_accounts_api.py`), `pytest` hung indefinitely inside the standard terminal sandbox (`BypassSandbox: false`).
- **Root Cause**:
  - FastAPI's `TestClient` uses `anyio.from_thread.start_blocking_portal()` to run the ASGI application in a worker thread.
  - On Windows, Python 3.12 `asyncio.ProactorEventLoop` uses internal Windows loopback socket pairs (`127.0.0.1`) for cross-thread messaging.
  - The standard terminal sandbox isolation on Windows drops or blocks loopback socket handshakes, causing `start_blocking_portal()` to block indefinitely waiting for socket I/O.
- **Verified Execution Workaround**:
  - Pure unit tests (`uv run --no-sync pytest tests/unit`) do not initialize ASGI socket loops and run inside the standard sandbox in **2.85s**.
  - Integration tests and the full coverage suite must be executed with `BypassSandbox: true` (e.g. `uv run --no-sync pytest --cov=src`), which restores Windows socket loopback and completes in **14.00s**.

### 11.3 Static Quality & Security Audits
- **Ruff Linter**: `ruff check .` -> **0 errors** (all checks passed).
- **Ruff Formatter**: `ruff format --check .` -> **109 files correctly formatted**.
- **Mypy Type Checking**: `mypy` -> **Success: no issues found in 67 source files** (strict mode).
- **Bandit SAST**: `bandit -r src/` -> **0 issues identified** (9,429 lines scanned across `src/`).
- **pip-audit**: `pip-audit` -> **0 known vulnerabilities found**.
- **Database Record Preservation**: `Primary Checking ('USD', 1500.00)` verified untouched in `data/finance.db`. Zero test writes to persistent SQLite storage.





