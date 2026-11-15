# Personal Finance Tracker — Architectural Decision Records (ADRs)

> **DOCUMENT**: `docs/DECISIONS.md`  
> **STATUS**: ACTIVE & ENFORCED  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation

---

## Index of Architectural Decisions

- [ADR-001: Backend Framework Selection (FastAPI)](#adr-001-backend-framework-selection-fastapi)
- [ADR-002: Frontend Dashboard Selection (Streamlit)](#adr-002-frontend-dashboard-selection-streamlit)
- [ADR-003: ORM & Migration Strategy (SQLAlchemy 2.0 & Alembic)](#adr-003-orm--migration-strategy-sqlalchemy-20--alembic)
- [ADR-004: Dual Database Strategy (SQLite Local, PostgreSQL Production)](#adr-004-dual-database-strategy-sqlite-local-postgresql-production)
- [ADR-005: Monetary Representation Model (Python Decimal & SQL Numeric)](#adr-005-monetary-representation-model-python-decimal--sql-numeric)
- [ADR-006: Schema Validation & Settings Management (Pydantic v2)](#adr-006-schema-validation--settings-management-pydantic-v2)
- [ADR-007: Data Analytics & Visualizations (Pandas & Plotly)](#adr-007-data-analytics--visualizations-pandas--plotly)
- [ADR-008: Testing Suite Architecture (Pytest & HTTPX)](#adr-008-testing-suite-architecture-pytest--httpx)
- [ADR-009: Security & Supply-Chain Auditing (Bandit & pip-audit)](#adr-009-security--supply-chain-auditing-bandit--pip-audit)
- [ADR-010: Phased Implementation Lifecycle with Approval Gates](#adr-010-phased-implementation-lifecycle-with-approval-gates)

---

## ADR-001: Backend Framework Selection (FastAPI)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: The application requires a fast, robust, asynchronous REST API backend capable of handling transactional financial mutations, serving analytical aggregations, and enforcing strict input validation.
- **Decision**: Adopt **FastAPI** with Uvicorn as the ASGI server.
- **Rationale**:
  - Asynchronous concurrency provides high throughput for I/O bound database operations.
  - Native integration with Pydantic ensures automatic request validation and type safety.
  - Automatic interactive OpenAPI documentation (`/docs` and `/redoc`) simplifies API exploration and client development.
  - Standardized dependency injection system simplifies database session lifecycle and authentication.
- **Consequences**:
  - Frontend and backend are cleanly decoupled; the frontend interacts with the backend strictly via HTTP.

---

## ADR-002: Frontend Dashboard Selection (Streamlit)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: We need an interactive, data-centric user interface capable of displaying rich financial tables, metrics, and charts with rapid development velocity and low maintenance overhead.
- **Decision**: Adopt **Streamlit** for the frontend user interface.
- **Rationale**:
  - Python-native framework allows seamless integration with Pandas and Plotly.
  - Rapid UI composition with built-in state management (`st.session_state`) and reactive execution.
  - Built-in data caching mechanisms (`@st.cache_data`) optimize visual performance.
- **Consequences**:
  - Streamlit re-runs scripts on user interaction; state must be managed carefully using `st.session_state`.
  - Streamlit must communicate with the database exclusively through the FastAPI REST client (`src/frontend/api_client.py`), maintaining strict architectural separation.

---

## ADR-003: ORM & Migration Strategy (SQLAlchemy 2.0 & Alembic)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: The application requires type-safe relational data modeling, query composition, transaction control, and revision-controlled database schema migrations.
- **Decision**: Adopt **SQLAlchemy 2.0** (using modern typed `Mapped[...]` and `mapped_column[...]` syntax) and **Alembic** for schema migrations.
- **Rationale**:
  - SQLAlchemy 2.0 provides fully typed ORM models, explicit transaction management, and an expressive query API.
  - Parameterized queries eliminate SQL injection vulnerabilities.
  - Alembic provides battle-tested schema migration version control supporting both SQLite and PostgreSQL.
- **Consequences**:
  - Developers must use SQLAlchemy 2.0 style queries (`select()`, `session.execute()`) rather than legacy 1.x patterns.

---

## ADR-004: Dual Database Strategy (SQLite Local, PostgreSQL Production)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: For local development, requiring developers to configure a PostgreSQL instance creates friction. In production, enterprise concurrency, connection pooling, and multi-user scaling require a robust client-server RDBMS.
- **Decision**: Support embedded **SQLite** (`data/finance.db`) for local development and **PostgreSQL 16+** for production deployments.
- **Rationale**:
  - SQLAlchemy abstracts SQL dialect differences, allowing identical ORM models to run on both engines.
  - SQLite requires zero configuration and zero external processes.
  - PostgreSQL provides high-concurrency ACID guarantees, connection pooling, and multi-user data isolation.
- **Consequences**:
  - Schema design must use engine-agnostic data types (avoiding SQLite-incompatible features).
  - Migration script (`scripts/verify_pg_migration.py`) verifies data parity between engines.

---

## ADR-005: Monetary Representation Model (Python Decimal & SQL Numeric)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Standard IEEE 754 floating-point numbers (`float`) introduce binary representation rounding errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). In a financial system, this leads to ledger discrepancies and accounting corruption.
- **Decision**: Use Python's built-in **`decimal.Decimal`** for all calculations and map columns to **`Numeric(18, 2)`** in SQLAlchemy.
- **Rationale**:
  - Base-10 exact arithmetic eliminates rounding drift.
  - Database-level `Numeric(18, 2)` constraints guarantee two decimal places of precision across both SQLite and PostgreSQL.
  - Compliant with GAAP and financial auditing standards.
- **Consequences**:
  - Numeric inputs from forms and APIs must be parsed directly into `Decimal` objects (never cast via `float()`).

---

## ADR-006: Schema Validation & Settings Management (Pydantic v2)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Inputs from forms, JSON payloads, and environment variables must be validated at runtime to prevent malformed data or security vulnerabilities.
- **Decision**: Adopt **Pydantic v2** for DTOs/schemas and **`pydantic-settings`** for environment variable management.
- **Rationale**:
  - Pydantic v2's Rust core (`pydantic-core`) delivers high validation performance.
  - Strict type coercion rules and custom validators guarantee data invariants.
  - Centralized `.env` loading and verification via `BaseSettings`.
- **Consequences**:
  - All API request and response models must be defined in `src/schemas/`.

---

## ADR-007: Data Analytics & Visualizations (Pandas & Plotly)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: The user needs dynamic visual analytics (cash flow comparisons, category expense distributions, net worth trajectories) and bank statement import/export capabilities.
- **Decision**: Adopt **Pandas** for analytical data processing and **Plotly** for interactive data visualization.
- **Rationale**:
  - Pandas provides fast in-memory filtering, grouping, time-series bucketing, and seamless CSV/Excel I/O.
  - Plotly produces interactive, responsive charts with zoom, pan, and hover tooltips natively renderable in Streamlit via `st.plotly_chart`.
- **Consequences**:
  - Heavy aggregations should be performed on cached DataFrames in Streamlit to avoid redundant API queries.

---

## ADR-008: Testing Suite Architecture (Pytest & HTTPX)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: The application requires comprehensive automated testing covering unit calculations, API endpoints, database transactions, and user workflows.
- **Decision**: Deploy **Pytest** with `pytest-asyncio` for unit/integration testing and **HTTPX** (`AsyncClient`) for API contract testing.
- **Rationale**:
  - Pytest provides concise test syntax, modular fixtures, and rich plugin support.
  - HTTPX enables in-memory testing of FastAPI applications without network latency or port binding conflicts.
- **Consequences**:
  - All test files reside under `tests/` and adhere to strict naming conventions (`test_*.py`).

---

## ADR-009: Security & Supply-Chain Auditing (Bandit & pip-audit)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Personal finance applications must guard against common web vulnerabilities, insecure coding practices, and supply-chain vulnerabilities in third-party packages.
- **Decision**: Integrate **Bandit** for static code analysis (SAST) and **pip-audit** for dependency vulnerability scanning.
- **Rationale**:
  - Bandit inspects Python ASTs to flag hardcoded secrets, SQL injection risks, and insecure library usage.
  - pip-audit verifies that installed packages have no active CVE entries in the PyPA vulnerability database.
- **Consequences**:
  - Both tools must run cleanly in local pre-commit checks and CI pipelines before any phase completion sign-off.

---

## ADR-010: Phased Implementation Lifecycle with Approval Gates

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Large engineering projects risk architectural drift and unvetted implementations without structured phase boundaries.
- **Decision**: Enforce a strict **Nine-Phase Lifecycle** with mandatory human approval gates at the end of each phase.
- **Rationale**:
  - Ensures each layer (scaffolding, database, services, API, UI, analytics, testing, deployment) is stable and certified before the next starts.
  - Prevents premature application feature coding.
  - Guarantees human-in-the-loop governance.
- **Consequences**:
  - All development halts at the end of each phase until explicit user approval is granted.
