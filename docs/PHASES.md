# Personal Finance Tracker — Nine-Phase Development Roadmap

> **DOCUMENT**: `docs/PHASES.md`  
> **STATUS**: APPROVED BASELINE  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT ACTIVE PHASE**: Phase 0 — Foundation and Documentation

---

## Roadmap Overview

Development is partitioned into nine strictly-bounded sequential phases. Advancing to the next phase requires satisfying all deliverables, passing all automated tests, passing security and dependency audits, and obtaining explicit human sign-off.

```
[ Phase 0: Foundation & Docs ] ──▶ [ Phase 1: Tooling & Scaffolding ] ──▶ [ Phase 2: SQLAlchemy & Alembic ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 3: Domain & Services ] ──▶ [ Phase 4: FastAPI REST Endpoints ] ──▶ [ Phase 5: Streamlit UI Shell ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 6: Streamlit Pages ]   ──▶ [ Phase 7: Analytics & Plotly ]    ──▶ [ Phase 8: Testing & Audits ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 9: Production Readiness, Docker & PostgreSQL Migration ] ──▶ [ RELEASE ]
```

---

## Phase 0: Project Foundation and Documentation (COMPLETED)

- **Objective**: Establish the Python + SQL technical architecture, document security and quality baselines, initialize the documentation suite, and define AI operating constraints.
- **Dependencies**: None.
- **Explicit Scope**:
  - Full workspace inspection and Git version control setup.
  - Authoring `AGENTS.md`, `README.md`, `.gitignore`.
  - Authoring `docs/APP.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT_RULES.md`, `docs/PHASES.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`, and `docs/HANDOFF.md`.
  - Verification of stable compatible releases for the Python stack.
- **Expected Deliverables**: All 12 markdown files complete, aligned, and committed to Git.
- **Automated Tests**: Markdown link integrity checks.
- **Security Audit**: Review security baseline policies and supply-chain vetting rules.
- **Dependency Audit**: Review target dependency versions against official PyPI advisories.
- **Acceptance Criteria**: All 12 documents exist and are synchronized; zero application code written.
- **Approval Gate**: Mandatory stop; wait for explicit user approval before proceeding to Phase 1.

---

## Phase 1: Environment Setup, Python Tooling & Core Project Scaffolding (COMPLETED)

- **Objective**: Set up Python 3.12 virtual environment, configure package dependencies via `pyproject.toml`, establish Ruff and Mypy tooling, configure Pytest, and create directory structure.
- **Dependencies**: Phase 0 explicit approval.
- **Status**: **COMPLETE**. 21/21 tests passing, Ruff linting/formatting verified, Mypy strict mode passing across 28 files, Bandit 0 issues, pip-audit 0 CVEs.
- **Explicit Scope**:
  - `pyproject.toml` configuration with pinned dependencies (FastAPI, Streamlit, SQLAlchemy, Alembic, Pydantic, Pandas, Plotly, Pytest, HTTPX, Bandit, pip-audit, Ruff, Mypy).
  - Virtual environment creation via `uv` or `python -m venv`.
  - Ruff configuration (`ruff.toml` or `pyproject.toml`) for linting and formatting.
  - Mypy configuration with strict flags (`mypy.ini` or `pyproject.toml`).
  - Pytest setup (`pytest.ini`).
  - Empty package scaffolding (`src/`, `tests/`).
  - Environment settings template (`.env.example`) and validated config loader (`src/core/config.py`).
- **Expected Deliverables**: Clean environment, passing linting, working config loader, and discoverable Pytest setup.
- **Automated Tests**: `pytest` executes and passes against test suite.
- **Security Audit**: `bandit -r src/` scan completes with zero findings.
- **Dependency Audit**: `pip-audit` runs against locked dependencies with zero known CVEs.
- **Acceptance Criteria**: `ruff check .` passes; `mypy` passes; `pytest` passes; `pip-audit` reports 0 vulnerabilities.
- **Approval Gate**: Explicit user approval required to proceed to Phase 2.

---

## Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations (NEXT PHASE — AWAITING APPROVAL)

- **Objective**: Implement SQLAlchemy 2.0 declarative models, configure Alembic migrations for SQLite, and write database seed script.
- **Dependencies**: Phase 1 explicit approval.
- **Explicit Scope**:
  - Database engine and session factory (`src/db/session.py`, `src/db/base.py`).
  - SQLAlchemy models (`User`, `Account`, `Category`, `Transaction`, `Budget`, `RecurringRule`, `AuditLog`).
  - Alembic initialization (`alembic/`) with autogenerate configuration.
  - Initial migration revision generating SQLite schema.
  - Database seed script (`src/db/seed.py`) populating default categories and local test user.
- **Expected Deliverables**: Alembic migration files, generated `data/finance.db`, and functional seed script.
- **Automated Tests**: Pytest tests for database model creation, foreign key constraints, and migration upgrade/downgrade cycles.
- **Security Audit**: Bandit scan verifies no raw SQL string concatenation in models or seeds.
- **Dependency Audit**: `pip-audit` check.
- **Acceptance Criteria**: `alembic upgrade head` runs cleanly; seed script populates data; unit tests pass.
- **Approval Gate**: Explicit user approval required to proceed to Phase 3.

---

## Phase 3: Core Domain Services, Pydantic Schemas & Financial Arithmetic

- **Objective**: Implement exact decimal financial calculations, Pydantic request/response schemas, and core domain business services.
- **Dependencies**: Phase 2 explicit approval.
- **Explicit Scope**:
  - Decimal currency calculation utilities (`src/core/money.py`): rounding, formatting, conversions.
  - Pydantic v2 validation models (`src/schemas/`): `AccountCreate`, `TransactionCreate`, `BudgetCreate`, etc.
  - Generic repository interface and implementations (`src/repositories/`).
  - Domain business services (`src/services/`):
    - `AccountService`: balance computation, account lifecycle.
    - `TransactionService`: atomic transfers, categorization, pagination filters.
    - `BudgetService`: monthly limits, threshold alert computation.
- **Expected Deliverables**: Fully tested service layer with pure business logic decoupled from HTTP frameworks.
- **Automated Tests**: Unit test suite achieving $\ge 90\%$ branch coverage on services and money calculations.
- **Security Audit**: Bandit scan on services; boundary tests on monetary validation.
- **Dependency Audit**: `pip-audit` check.
- **Acceptance Criteria**: 100% of unit tests pass; zero floating-point arithmetic used; Zod/Pydantic validation rejects all invalid inputs.
- **Approval Gate**: Explicit user approval required to proceed to Phase 4.

---

## Phase 4: FastAPI REST API, Endpoints & Authentication

- **Objective**: Expose domain services via FastAPI REST endpoints, implement JWT authentication, error handling, and request correlation.
- **Dependencies**: Phase 3 explicit approval.
- **Explicit Scope**:
  - FastAPI application factory (`src/api/main.py`) with CORS, exception handlers, and correlation ID middleware.
  - Dependency injection providers (`src/api/dependencies.py`): DB session, current user.
  - Routers (`src/api/routers/`):
    - `/api/v1/auth`: login, token refresh.
    - `/api/v1/accounts`: account CRUD, archive.
    - `/api/v1/transactions`: ledger CRUD, atomic transfer endpoint, CSV stream.
    - `/api/v1/budgets`: budget CRUD, progress stats.
    - `/api/v1/analytics`: summary metrics, cash flow rollups.
- **Expected Deliverables**: Fully operational, documented REST API with Swagger/OpenAPI docs (`/docs`).
- **Automated Tests**: HTTPX `AsyncClient` integration tests for every endpoint, validating 200, 201, 400, 401, 404, and 422 responses.
- **Security Audit**: Bandit scan; tenant isolation tests verifying User A cannot access User B's resources.
- **Dependency Audit**: `pip-audit` check.
- **Acceptance Criteria**: All integration tests pass; OpenAPI schema renders without error; tenant security verified.
- **Approval Gate**: Explicit user approval required to proceed to Phase 5.

---

## Phase 5: Streamlit UI Framework, Layout & Reusable Widgets

- **Objective**: Build the Streamlit multi-page foundation, navigation sidebar, theme configuration, and reusable UI components.
- **Dependencies**: Phase 4 explicit approval.
- **Explicit Scope**:
  - Streamlit entry point (`src/frontend/app.py`) with authentication gate and session state handling.
  - Asynchronous HTTPX client wrapper (`src/frontend/api_client.py`).
  - Reusable UI component modules:
    - Metric cards (`src/frontend/components/metrics.py`).
    - Plotly chart builders (`src/frontend/components/charts.py`).
    - Standardized data tables with formatting (`src/frontend/components/tables.py`).
    - Forms with validation and error toasts (`src/frontend/components/forms.py`).
  - Streamlit configuration (`.streamlit/config.toml`) for theming and server settings.
- **Expected Deliverables**: Operational Streamlit shell communicating with FastAPI backend.
- **Automated Tests**: Unit tests for `api_client.py` and Plotly chart generators using mock API responses.
- **Security Audit**: Bandit scan verifying no secret leakage in Streamlit frontend.
- **Dependency Audit**: `pip-audit` check.
- **Acceptance Criteria**: Streamlit renders cleanly; theme switches between light and dark; API client handles network errors gracefully.
- **Approval Gate**: Explicit user approval required to proceed to Phase 6.

---

## Phase 6: Streamlit Application Pages (Accounts, Transactions, Budgets)

- **Objective**: Develop user-facing feature pages in Streamlit for account management, transaction ledger, and monthly budgeting.
- **Dependencies**: Phase 5 explicit approval.
- **Explicit Scope**:
  - `pages/1_Dashboard.py`: Net worth callout, recent transactions, quick actions.
  - `pages/2_Accounts.py`: Account summary table, add/edit modal forms, archive toggle.
  - `pages/3_Transactions.py`: Searchable, filterable ledger table, expense/income/transfer entry forms.
  - `pages/4_Budgets.py`: Category budget cards, dynamic progress bars, over-budget warning alerts.
- **Expected Deliverables**: Complete, functional personal finance user interface.
- **Automated Tests**: Streamlit `AppTest` or automated integration tests simulating end-to-end user workflows.
- **Security Audit**: Bandit scan; verification of input sanitization across all Streamlit forms.
- **Dependency Audit**: `pip-audit` check.
- **Acceptance Criteria**: Users can create accounts, log transactions, perform transfers, and set budgets with immediate visual feedback.
- **Approval Gate**: Explicit user approval required to proceed to Phase 7.

---

## Phase 7: Analytics, Plotly Visualizations & Pandas Data Processing

- **Objective**: Implement advanced financial analytics using Pandas and interactive Plotly visualizations; implement CSV/Excel statement import and export.
- **Dependencies**: Phase 6 explicit approval.
- **Explicit Scope**:
  - `pages/5_Reports.py`:
    - Monthly Cash Flow (Plotly grouped bar chart: Income vs. Expense).
    - Category Expense Breakdown (Plotly interactive donut chart).
    - Net Worth Trajectory (Plotly time-series area chart).
  - Pandas data processing pipelines: monthly rollups, average burn rate, savings rate percentage.
  - Statement Import Wizard: upload CSV/Excel, map columns via Pandas, preview DataFrame, batch commit.
  - Data Export: download full or filtered transaction ledger as CSV or Excel.
- **Expected Deliverables**: Interactive analytics dashboard and full data portability tools.
- **Automated Tests**: Unit and integration tests for Pandas aggregation pipelines and CSV export/import round-trips.
- **Security Audit**: Bandit scan; file upload validation (MIME type, file size limit, malicious content prevention).
- **Dependency Audit**: `pip-audit` check.
- **Acceptance Criteria**: Charts render interactively; statement import correctly deduplicates; CSV export is RFC 4180 compliant.
- **Approval Gate**: Explicit user approval required to proceed to Phase 8.

---

## Phase 8: Comprehensive Testing, Security Audits & Performance Optimization

- **Objective**: Conduct comprehensive regression testing, static and dynamic security audits, query performance profiling, and bundle optimization.
- **Dependencies**: Phase 7 explicit approval.
- **Explicit Scope**:
  - Full end-to-end regression test suite execution.
  - Boundary stress testing: extreme amounts, high volume transaction datasets (50,000+ rows).
  - Static security audit: `bandit -r src/ -ll -ii` with zero unresolved findings.
  - Dependency audit: `pip-audit` with zero unresolved vulnerabilities.
  - Database index profiling: EXPLAIN QUERY PLAN verification on ledger filtering.
  - Caching optimization in Streamlit (`@st.cache_data`).
- **Expected Deliverables**: Comprehensive QA test report and clean security audit certifications.
- **Automated Tests**: 100% pass rate across unit, integration, and security test suites.
- **Security Audit**: Zero High or Critical findings in Bandit and pip-audit.
- **Dependency Audit**: Clean bill of health from `pip-audit`.
- **Acceptance Criteria**: All automated tests pass; zero security vulnerabilities; query execution $< 100\text{ ms}$.
- **Approval Gate**: Explicit user approval required to proceed to Phase 9.

---

## Phase 9: Production Readiness, Dockerization, PostgreSQL Migration Verification & Deployment

- **Objective**: Package application into production Docker containers, verify SQLite-to-PostgreSQL migration pipeline, configure production logging and backups, and finalize documentation.
- **Dependencies**: Phase 8 explicit approval.
- **Explicit Scope**:
  - Production `Dockerfile` and `docker-compose.yml` (FastAPI, Streamlit, PostgreSQL 16).
  - Dual database verification: apply Alembic migrations against live PostgreSQL container.
  - Verification of data migration utility (`scripts/verify_pg_migration.py`).
  - Production security hardening: SSL enforcement, environment variable secret injection.
  - Automated database backup script (`scripts/backup_db.sh`).
  - Final documentation update and handoff readiness (`docs/HANDOFF.md`).
- **Expected Deliverables**: Production Docker configuration, verified PostgreSQL migration, and complete operations guide.
- **Automated Tests**: Full test suite passes against PostgreSQL database backend.
- **Security Audit**: Final Bandit and pip-audit certification.
- **Dependency Audit**: Final supply-chain verification.
- **Acceptance Criteria**: Docker containers launch cleanly; PostgreSQL migration reconciles balances to the exact cent; production sign-off.
- **Approval Gate**: Final production sign-off.
