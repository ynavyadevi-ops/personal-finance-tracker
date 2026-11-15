# Changelog

All notable changes to the **Personal Finance Tracker (Python + SQL)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Phase 2 (Core Accounting & Transaction Engine)
- Complete transaction models (`Transaction`, `TransactionType`, `TransactionSplit`).
- Double-entry balance calculation and balance integrity invariants.
- Transaction categorization and transaction query/filter APIs.
- CSV bank statement parsing and import pipeline.

---

## [0.2.0] - 2026-11-15 (Phase 1: Environment and Application Foundation)

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
