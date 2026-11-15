# Personal Finance Tracker — Quality Assurance & Testing Strategy

> **DOCUMENT**: `docs/TESTING.md`  
> **STATUS**: APPROVED BASELINE  
> **STACK**: Python 3.12 (Pytest, pytest-asyncio, HTTPX, Bandit, pip-audit)  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation

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
| **Phase 8** | Full Pytest test suite passes (100% pass rate); Bandit SAST reports 0 issues; pip-audit reports 0 vulnerabilities. |
| **Phase 9** | PostgreSQL migration verified with `verify_pg_migration.py`; Docker containers build and run cleanly; production deployment verified. |
