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
- [ADR-011: Synchronous Engine for SQLite in Local Development](#adr-011-synchronous-engine-for-sqlite-in-local-development)
- [ADR-012: Pinned Dependency Upgrades for Proactive CVE Remediation](#adr-012-pinned-dependency-upgrades-for-proactive-cve-remediation)
- [ADR-013: Default Currency Selection (Indian Rupee - INR / ₹)](#adr-013-default-currency-selection-indian-rupee---inr---)
- [ADR-014: Authoritative Nine-Phase Roadmap (Phases 0–8)](#adr-014-authoritative-nine-phase-roadmap-phases-08)
- [ADR-015: Protected Status for Existing Financial Account CRUD](#adr-015-protected-status-for-existing-financial-account-crud)
- [ADR-016: Relational Schema Architecture, Double-Entry Ledger Representation, and Decimal Precision Storage](#adr-016-relational-schema-architecture-double-entry-ledger-representation-and-decimal-precision-storage)
- [ADR-017: Domain Services Architecture & Accounting Conventions](#adr-017-domain-services-architecture--accounting-conventions)

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

---

## ADR-011: Synchronous Engine for SQLite in Local Development

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: In Phase 1 development and local environments (especially Windows sandbox environments), `aiosqlite` threads attempt to wake the asyncio event loop via loopback sockets (`call_soon_threadsafe`), which blocks or hangs without network permissions. SQLite is an in-process single-file embedded database where thread hops add overhead without concurrency advantages.
- **Decision**: Use SQLAlchemy synchronous `create_engine` with `SessionLocal` and automatic `PRAGMA foreign_keys=ON` connection listener for SQLite local development and test fixtures, while keeping FastAPI route handlers asynchronous.
- **Rationale**:
  - Sub-millisecond synchronous execution on local SQLite with zero socket requirements.
  - Explicit enforcement of SQLite foreign key cascades via connection event listeners.
  - Aligns with standard FastAPI synchronous dependency injection pattern (`yield db`).
- **Consequences**:
  - `src/db/session.py` provides synchronous `get_db` generator and `SessionLocal`.
  - When migrating to PostgreSQL in production, asynchronous drivers (`asyncpg`) or standard connection pooling (`psycopg2`/`psycopg`) can be selected via `DATABASE_URL`.

---

## ADR-012: Pinned Dependency Upgrades for Proactive CVE Remediation

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: During initial dependency auditing with `pip-audit`, legacy releases of transitive dependencies (e.g., `pillow` 11.3 and `streamlit` 1.41) were found to carry known public CVE vulnerabilities.
- **Decision**: Upgrade and pin safe modern releases in `pyproject.toml` and `requirements.txt`:
  - `fastapi>=0.163.0`
  - `starlette>=1.10.0`
  - `streamlit>=1.67.0`
  - `pillow>=13.0.0`
  - `pytest>=9.2.0`
  - `pytest-asyncio>=1.5.0`
- **Rationale**:
  - Completely eliminates all 69 legacy vulnerabilities identified in older releases.
  - Maintains strict 100% clean security pass in `pip-audit`.
- **Consequences**:
  - All environments and CI pipelines use reproducible pinned versions verified by `pip-audit`.

---

## ADR-013: Default Currency Selection (Indian Rupee - INR / ₹)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: The approved default currency for the Personal Finance Tracker application is the Indian Rupee (INR / ₹). Initial scaffolding defaulted to USD ($). Existing financial records in development databases must be preserved without silent conversion or exchange-rate drift, and previously applied migrations must not be modified in place.
- **Decision**: Set the application default currency to `INR` with symbol `₹` across SQLAlchemy models, Pydantic schemas, UI text inputs, and formatting utilities (`src/core/money.py`). Existing database records retain their original numeric values and currency tags without automatic alteration.
- **Rationale**:
  - Adheres strictly to the user's regional and currency specifications.
  - Enforces ledger integrity by prohibiting silent or automatic exchange-rate conversions of existing balances.
  - Preserves migration immutability: the underlying schema (`sa.String(3)`) natively supports `INR` without requiring destructive DDL alterations.
- **Consequences**:
  - New accounts default to `INR` and display with `₹`.
  - Formatting helper `format_currency` defaults to `₹`.

---

## ADR-014: Authoritative Nine-Phase Roadmap (Phases 0–8)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Project documentation previously exhibited an off-by-one labeling inconsistency, referencing 10 stages labeled Phase 0 through Phase 9 while intending a nine-phase lifecycle. Furthermore, required features (recurring transactions, savings goals, loans & debts, investments, AI insights) required explicit phase ownership.
- **Decision**: Consolidate the lifecycle into a single authoritative **Nine-Phase Roadmap numbered Phase 0 through Phase 8**:
  - Phase 0: Project Foundation and Documentation (COMPLETED)
  - Phase 1: Environment Setup & Application Foundation (COMPLETED & REMEDIATED)
  - Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations (NEXT PHASE)
  - Phase 3: Core Accounting Engine, Financial Services & Domain Logic
  - Phase 4: FastAPI REST API & Data Portability Services
  - Phase 5: Streamlit Frontend Core UI & Core Pages
  - Phase 6: Advanced Feature Pages & Specialized Tracking
  - Phase 7: Analytics, Plotly Visualizations & AI Insights
  - Phase 8: Comprehensive Verification, Security Auditing & Production Readiness
- **Rationale**:
  - Reconciles roadmap documentation with approved project requirements.
  - Retains Phase 0 and Phase 1 numbering and completed deliverables without churn.
  - Maps every required functional capability into an explicit delivery phase.
- **Consequences**:
  - `docs/PHASES.md`, `README.md`, and `docs/HANDOFF.md` are unified on the 0–8 sequence.

---

## ADR-015: Protected Status for Existing Financial Account CRUD

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: During Phase 1, basic Financial Account CRUD endpoints, repository, service, and UI registration forms were implemented ahead of the original Phase 2/4/6 schedule.
- **Decision**: Designate all existing account CRUD components as **Protected Approved Functionality**. These components shall not be removed, rewritten, or refactored.
- **Rationale**:
  - Respects Directive 3 (Preserve Approved Functionality).
  - Backed by 15 dedicated unit and integration regression tests verifying creation, duplicate conflicts, not-found handling, multi-tenant isolation, updating, and soft-delete archiving.
- **Consequences**:
  - Future phases build directly upon the existing `AccountService`, `AccountRepository`, and accounts REST router.

---

## ADR-016: Relational Schema Architecture, Double-Entry Ledger Representation, and Decimal Precision Storage

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 2 requires designing the full relational database foundation supporting multiple accounts, income/expense flows, inter-account transfers, budgets, goals, loan debts, recurring schedules, investments, and audit histories, compatible with both local SQLite and production PostgreSQL.
- **Decision**:
  1. **Normalized Double-Entry Ledger**: Implement `Transaction` as the high-level business event, paired with balanced `TransactionEntry` lines representing debit and credit ledger rows associated with specific `FinancialAccount` records.
  2. **Decimal Precision Rules**: Store all monetary values as `Numeric(18, 2)` (supporting sums up to 10 quadrillion with 2 decimal places). Store investment quantities as `Numeric(18, 4)` to support fractional share transactions, mutual fund units, and gold gram quantities.
  3. **Engine-Level Integrity**: Enforce explicit check constraints (`amount > 0`, month bounds `1 <= month <= 12`, non-negative balances and quantities) directly in the database DDL.
  4. **Deletion Protection**: Enforce `ON DELETE RESTRICT` on foreign keys from ledger lines, loan debts, and investment transactions to accounts, preventing catastrophic cascade deletion of accounts containing audit histories.
  5. **Cross-Dialect Compatibility**: Configure SQLEnum columns with `native_enum=False` to store string representations with check constraints, ensuring seamless dual-database execution across SQLite and PostgreSQL without dialect-specific DDL scripts. Use `render_as_batch=True` in Alembic for SQLite table alterations.
- **Rationale**:
  - Double-entry ledger architecture guarantees mathematical conservation of funds across transfers and multi-account transactions.
  - Check constraints protect against corrupted data injection regardless of application-layer bypass.
  - `Numeric(18, 4)` precision ensures full support for Indian mutual funds (where NAV and units are measured to 4 decimals) and fractional crypto/gold assets.
- **Consequences**:
  - Phase 3 accounting services can rely on balanced ledger rows and atomic transfers without ad-hoc single-column balance drift.
  - Foreign key restrict requires accounts with transactions to be archived rather than hard-deleted, maintaining complete auditability.

---

## ADR-017: Domain Services Architecture & Accounting Conventions

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 3 requires implementing pure Python domain logic to execute financial transactions, validate double-entry ledger invariants, process atomic transfers, calculate budget utilization with rollovers, manage savings goals, compute fixed-rate loan amortization, evaluate recurring schedules, and calculate investment cost basis and realized gains.
- **Decision**:
  1. **Separation of Services & Repositories**: Create specialized domain services in `src/services/` backed by dedicated repository classes in `src/repositories/`. Each service encapsulates business rules, tenant authorization (`user_id`), and input validations, keeping the repository layer focused strictly on query composition.
  2. **Double-Entry Ledger Balancing**: Enforce the fundamental accounting invariant $\sum \text{Debits} == \sum \text{Credits}$ across all balanced multi-entry transactions. Internal transfers generate balanced dual entries (1 `CREDIT` on source account, 1 `DEBIT` on destination account) ensuring conservation of funds.
  3. **Strict Currency Compatibility**: Reject cross-currency transfers with `CurrencyMismatchError` (HTTP 422). The system forbids silent currency conversion or relabeling.
  4. **Idempotency Protection**: Implement transparent idempotency caching via transaction tags (`idempotency:<key>`). Replaying a request with an existing idempotency key safely returns the cached transaction without creating duplicate database records.
  5. **Compensating Transaction Reversal**: Transaction reversals create compensating ledger entries rather than performing hard row deletions, preserving full immutable auditability.
  6. **Budget Spending Aggregation**: Monthly category spending aggregations strictly exclude internal transfers and income, computing utilization percentages against configurable alert thresholds: Normal ($<80\%$), Warning ($80\% - 99.99\%$), and Exceeded ($\ge 100\%$), with optional unspent rollover from previous months.
  7. **Exact Fixed-Rate Loan Amortization**: Use exact Decimal compound interest calculations for EMI generation: $\text{EMI} = P \times \frac{r(1+r)^n}{(1+r)^n - 1}$. The final instalment absorbs rounding cents so the final remaining balance reaches exactly ₹0.00.
  8. **Weighted-Average Cost Basis for Securities**: Security purchases recalculate weighted-average cost basis: $\text{Cost Basis} = \frac{\text{Previous Cost} + \text{New Trade Amount}}{\text{Total Units}}$. Sales enforce unit sufficiency with `InsufficientUnitsError` (HTTP 422) and compute realized capital gains/losses.
- **Rationale**:
  - Encapsulating business rules in domain services guarantees that future Phase 4 REST endpoints and data import pipelines execute identical, validated business rules.
  - Transparent idempotency prevents double charges resulting from network retries.
  - Weighted-average cost basis conforms to standard Indian income tax accounting rules for capital gains.
- **Consequences**:
  - All financial state mutations must flow through domain services; raw database mutations in routers or scripts are strictly prohibited.

---

## ADR-018: Authentication Architecture, Argon2id Hashing, and JWT Authorization

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 4 requires securing all REST API endpoints with authenticated user identities, preventing cross-user data access, and replacing the hardcoded default user ID with verified JWT bearer credentials. Existing legacy users in development databases must be preserved without silent credential provisioning.
- **Decision**:
  1. **Password Hashing with Argon2id**: Use `pwdlib[argon2]` with cryptographic salt to hash and verify passwords. Never store plaintext passwords or use fast general-purpose hashes (e.g. SHA-256).
  2. **Short-Lived Signed JWT Access Tokens**: Issue signed HS256 JWT tokens via `pyjwt` with explicit expiration (60 minutes UTC), issued-at (`iat`), token classification (`type="access"`), and issuer (`iss="personal-finance-tracker"`). Never store secrets or sensitive credentials in token payloads.
  3. **Safe Legacy Account Enrollment via Administrative CLI**: Add `hashed_password` (nullable) to the `users` table via Alembic migration `6c8ca07763d0`. Legacy accounts without passwords cannot authenticate until safe password enrollment is completed via local administrative CLI (`src/cli/enroll.py`). The public `/api/v1/auth/enroll` HTTP endpoint was eliminated to prevent unauthenticated account claiming.
  4. **Server-Side Identity Derivation**: All financial API operations derive user ownership strictly from the verified server-side identity context (`current_user: User = Depends(get_current_user)`). Client-supplied `user_id` query/body parameters are strictly rejected.
- **Rationale**:
  - Argon2id is the OWASP-recommended password hashing standard resistant to GPU/ASIC cracking.
  - Server-side identity injection prevents broken object level authorization (BOLA / IDOR) vulnerabilities.
  - Administrative CLI enrollment satisfies Directive 3 by preserving existing user and account records while enforcing operator verification and anti-overwrite protection on the host.
- **Consequences**:
  - All financial endpoints require valid Bearer JWT tokens in `Authorization` header.
  - Public endpoints are limited strictly to `/health`, `/api/v1/health`, `/api/v1/auth/register`, and `/api/v1/auth/token`.

---

## ADR-019: Data Portability, Spreadsheet Formula Injection Defense, and Safe Backup Architecture

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 4 requires bank/credit card statement import (CSV and Excel XLSX) with duplicate detection, user data export, and database backup snapshots. Data imports/exports must be resilient against spreadsheet formula execution exploits, and database backups must not expose destructive restore capabilities without explicit authorization.
- **Decision**:
  1. **Statement Parsing Engine**: Use Pandas with `openpyxl` to parse CSV and XLSX file buffers into dataframes. Support configurable column mapping (`date_column`, `amount_column`, `description_column`, `category_column`, `type_column`), enforce file size limits ($\le 5\text{MB}$) and row count caps ($\le 1000\text{ rows}$).
  2. **Duplicate Transaction Detection**: Query existing ledger transactions matching `(user_id, transaction_date, amount, description)`. Flag duplicates during dry-run preview (`POST /api/v1/data/import/preview`) without writing data. Batch commit (`POST /api/v1/data/import/commit`) writes transactions through `TransactionService` inside an atomic transaction.
  3. **Formula Injection Mitigation**: Sanitize all exported cells starting with dangerous characters (`=, +, -, @, \t, \r`) by prefixing them with a single quote (`'`), preventing Excel/Calc from evaluating malicious expressions.
  4. **User-Scoped JSON Backup Snapshot**: Export user data across all 11 domain models in a versioned envelope (`schema_version: "1.0.0"`) with exact Decimal string formatting. Strictly exclude password hashes and internal credentials.
  5. **Non-Destructive Dry-Run Backup Validation**: Expose dry-run validation (`POST /api/v1/data/backup/validate`) verifying schema version and completeness. Destructive restore (`mode="REPLACE_USER_DATA"`) is strictly non-executable and not exposed in Phase 4.
- **Rationale**:
  - Comply with OWASP Top 10 guidelines on CSV/formula injection.
  - Guarantees data portability without risking database corruption or accidental user data replacement.
- **Consequences**:
  - Users can export and preview imports safely without spreadsheet risks.
  - Backups can be verified without altering database state.

---

## ADR-020: Streamlit Frontend Architecture, Decoupled REST Integration, and In-Memory Session Management

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 5 requires implementing a responsive dark-themed personal finance frontend in Streamlit that consumes the Phase 4 REST API, enforces strict authentication barriers, preserves multi-currency integrity without cross-currency summation, and adheres to zero-trust architectural boundaries.
- **Decision**:
  1. **Strictly Decoupled Presentation Layer**: Streamlit views and components never import SQLAlchemy models or directly access SQLite database files. All operations execute through a centralized `ApiClient` communicating with authorized FastAPI endpoints (`/api/v1/*`) via Bearer JWT tokens.
  2. **In-Memory Session Lifecycle Management**: JWT access tokens and user profile objects are stored strictly in Streamlit's server-side memory (`st.session_state`). Tokens are never persisted to disk, browser local storage, or URL query parameters.
  3. **Automated Session Expiration Interception**: `ApiClient` intercepts HTTP 401 Unauthorized responses across all protected endpoints, immediately revokes the local token, marks `session_expired = True`, and redirects the operator to the login portal with a clear warning.
  4. **Strict Currency Isolation**: The user interface sets Indian Rupee (INR) as default, renders USD accounts accurately ($), strictly prohibits summing disparate currencies into a combined total without an approved conversion mechanism, and excludes transfers from income and expense metrics.
  5. **Explicit Confirmation on State Alterations**: Compensating transaction reversals and account archiving workflows enforce explicit operator confirmation prompts prior to dispatching API mutation requests.
  6. **No Automatic POST Retries**: To prevent duplicate financial charges or ledger imbalances, `ApiClient` forbids automatic retries on state-mutating POST operations.
- **Rationale**:
  - Enforces separation of concerns and guarantees that all business, accounting, and security constraints are mediated by the FastAPI backend.
  - Mitigates token leakage vulnerabilities and prevents cross-user authorization bypasses.
  - Ensures accurate financial presentation conforming to accounting invariants.
- **Consequences**:
  - Frontend execution requires an active FastAPI backend process.
  - Public password enrollment is strictly prohibited in the UI; legacy account enrollment remains restricted to the local administrative CLI.

---

## ADR-021: Phase 6 Advanced Feature Views, Historical Cost Basis Valuation, and Windows Loopback Test Protocol

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 6 requires implementing dedicated Streamlit frontend views for specialized financial management: Savings Goals milestones, Loans and Debt amortization liabilities, Investment portfolio tracking, and Recurring transaction rules. During test verification on Windows, integration tests hung in the standard restricted terminal sandbox environment.
- **Decision**:
  1. **Savings Goals Milestones**: Build `src/frontend/views/goals.py` exposing target milestones, visual funded progress bars (`st.progress`), dedicated contribution forms, withdrawal forms, and milestone creation. Contributions and withdrawals are presented as balance movements rather than income/expense.
  2. **Loan Amortization Liabilities**: Build `src/frontend/views/loans.py` presenting liability summaries, full installment amortization schedules (principal component, interest component, remaining balance, due dates), installment repayment forms selecting unpaid installments, and loan obligation creation.
  3. **Historical Weighted-Average Cost Basis & Valuation Disclaimer**: Build `src/frontend/views/investments.py` presenting portfolio positions with 4-decimal quantity precision and weighted-average acquisition cost basis per unit. Display a prominent architectural disclaimer confirming that live market feeds and automated brokerage sync are outside active scope boundaries. Liquidations display realized capital gain/loss breakdowns.
  4. **Recurring Transactions & Manual Ledger Execution**: Build `src/frontend/views/recurring.py` presenting a proactive due executions alert banner. In compliance with architectural rules, recurring transactions are not automated via background cron daemons; operators explicitly trigger due executions to create verified double-entry ledger transactions. Rules can be paused and resumed.
  5. **Navigation Integration**: Update `src/frontend/app.py` and `src/frontend/views/__init__.py` to provide seamless navigation across all 9 core views.
  6. **Windows Loopback Test Protocol**:
     - *Root Cause*: FastAPI's `TestClient` uses AnyIO's blocking portal with Python 3.12 `asyncio.ProactorEventLoop` on Windows, which utilizes local loopback socket pairs (`127.0.0.1`) for cross-thread synchronization. Under the Windows restricted terminal sandbox (`BypassSandbox: false`), local loopback socket traffic is dropped or blocked, causing AnyIO to hang indefinitely on socket handshakes.
     - *Protocol*: Execute pure unit tests (`pytest tests/unit`) within the standard sandbox (passing in 2.85s). Execute full test suites requiring ASGI loopback sockets (`pytest --cov=src`) with `BypassSandbox: true` (passing in 14.0s).
- **Rationale**:
  - Delivers all required advanced personal finance capabilities while preserving strict accounting invariants.
  - Transparently explains valuation mechanics to prevent user misunderstanding.
  - Establishes a verified, reproducible testing workflow on Windows platforms without modifying application security boundaries.
- **Consequences**:
  - Frontend users have complete visual control over goals, debts, investments, and recurring rules.
  - Continuous integration and local testing on Windows must account for loopback socket requirements in sandboxed environments.

---

## ADR-022: Phase 7 Financial Analytics Engine, Plotly Visualizations, and Privacy-First AI Architecture

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Phase 7 requires developing financial analytics, Plotly interactive charts, rule-based explainable insights, and optional AI-assisted summaries, while strictly maintaining user privacy, currency isolation, and accounting invariants.
- **Decision**:
  1. **Deterministic Analytics Engine**: Build `src/services/analytics_service.py` (`FinancialAnalyticsEngine`) using exact Decimal calculations. Transfers (`TransactionType.TRANSFER`) are strictly excluded from income and expenses; compensating reversals are netted out; all aggregations are strictly partitioned by currency.
  2. **Interactive Plotly Visualizer Library**: Build `src/frontend/components/charts.py` generating Plotly figures adhering to the dark fintech design system (`#0B1120`, `#151E30`, `#1D2940`, `#38BDF8`, `#22C55E`, `#F87171`): income vs. expense grouped bars, cash flow area trends, category spending donuts, budget comparative bars, savings milestone stacks, and investment allocation donuts.
  3. **Privacy-First AI Architecture**: Build `src/services/ai_insights.py`:
     - AI insights are strictly disabled by default; explicit user opt-in is required via UI toggle.
     - Strict data de-identification: strips all PII, account IDs, merchant names, raw descriptions, passwords, and JWT tokens before processing.
     - Local synthesis generates plain-language observations without third-party cloud leakage.
     - All AI-generated outputs carry a permanent non-advice disclaimer.
  4. **Dedicated Analytics View**: Build `src/frontend/views/analytics.py` integrating multi-tab interactive analytics with currency and timeframe filters.
- **Rationale**:
  - Guarantees financial mathematical precision conforming to Phase 3 ledger rules.
  - Protects user confidentiality and complies with privacy-first AI principles.
  - Provides intuitive visual exploratory tools for personal finance management.
- **Consequences**:
  - Users receive rich interactive visual analytics and explainable insights.
  - Zero external third-party cloud API costs or data leakage risks are introduced.

---

## ADR-023: Phase 8 System Hardening, Local MVP Packaging, and Release Readiness

- **Date**: 2026-11-16
- **Status**: **ACCEPTED**
- **Context**: Phase 8 is the final phase of the Phase 0–8 roadmap: System Hardening, Comprehensive Testing, Packaging & Release. It requires comprehensive security and financial integrity audits, boundary and edge case testing, configuration hardening, Windows 11 reproducible packaging, and a manual browser UAT procedure, leading to a local MVP release candidate. Public deployment remains strictly non-authorized.
- **Decision**:
  1. **Comprehensive System Hardening Test Suite**: Created `tests/integration/test_system_hardening.py` expanding test coverage to 192 passed automated tests (81% overall coverage):
     - Validated zero and negative amount rejections across transactions, budgets, goals, loans, and investment trades (HTTP 422).
     - Verified large numeric boundary arithmetic (`Decimal("999999999999.99")`) ensuring exact Decimal precision without float drift.
     - Verified currency mismatch prevention on inter-account transfers (`CurrencyMismatchError` -> HTTP 422).
     - Verified repeated reversal prevention on already-reversed transactions (HTTP 422).
     - Verified holding sufficiency checks rejecting liquidation of unheld or excess investment units (`InsufficientUnitsError` -> HTTP 422).
     - Verified double-entry transfer balance conservation ($5,000 + $1,000 = $3,500 + $2,500 = $6,000) and restoration upon reversal ($5,000 + $1,000 = $6,000).
     - Enforced multi-tenant cross-user authorization isolation: User B token cannot read, patch, delete, or reverse User A's financial records (HTTP 404).
     - Enforced unauthenticated request blocking across all domain endpoints (HTTP 401).
     - Confirmed permanent absence of public account enrollment endpoint (`POST /api/v1/auth/enroll` returns 404).
     - Enforced backup snapshot schema validation: invalid schema versions or malformed payloads fail dry-run validation (`is_valid: False`).
  2. **Destructive Restore Boundary**: Confirmed `mode="REPLACE_USER_DATA"` is strictly non-executable in `PortabilityService`. Backups are validated and exported as JSON snapshots without enabling destructive database replacement.
  3. **Configuration & Packaging**:
     - Hardened `.env.example` with documented environment parameters, safe local defaults (`127.0.0.1` binding), and zero hardcoded secrets.
     - Provided Windows 11 batch automation scripts:
       * `scripts/run_backend.bat`: Launches FastAPI API server on `127.0.0.1:8000`.
       * `scripts/run_frontend.bat`: Launches Streamlit frontend app on `127.0.0.1:8501`.
       * `scripts/enroll_user.bat`: Launches local interactive administrative credential enrollment.
       * `scripts/verify_system.bat`: Runs full local quality gates (Pytest, Ruff, Mypy).
  4. **Manual Browser Acceptance**: Created `docs/UAT_CHECKLIST.md` defining step-by-step verification procedures for all 10 views, authentication, exports, imports, and privacy controls with explicit expected results and failure indicators.
- **Rationale**:
  - Validates that the entire system is resilient against invalid inputs, unauthorized tenant access, and financial integrity violations.
  - Ensures local desktop operators can reliably initialize, configure, run, and audit the application on Windows 11.
  - Formally satisfies all Phase 0–8 architectural and security directives.
- **Consequences**:
  - Application achieves **READY FOR LOCAL MVP TESTING** status.
  - Public deployment is strictly non-authorized and deferred until future multi-user production infrastructure is approved.

---

## ADR-024: Post-Phase 8 User Registration, Administrator Portal, and Strict Financial Privacy Boundary

- **Date**: 2026-11-16
- **Status**: **ACCEPTED**
- **Context**: Following Phase 8 release readiness, requirements emerged to enable self-service user registration and provide a dedicated governance portal for administrators to manage user lifecycles, inspect audit trails, and toggle platform settings without ever exposing private customer financial data.
- **Decision**:
  1. **Public User Registration Architecture**:
     - Endpoint `POST /api/v1/auth/register` accepts `name`, `email`, `password`, and optional `confirm_password`.
     - Strictly validates password complexity (minimum 8 characters, uppercase, lowercase, digit, and special character).
     - Employs Argon2id password hashing via `pwdlib`.
     - Assigns `UserRole.USER` by default; role elevation via public registration is technically impossible.
     - Implements anti-enumeration protection: duplicate email registration returns a generic safe `ValidationError` ("Unable to complete registration with the provided details.") without revealing existing account status.
     - Enforces sliding-window rate limiting on authentication operations to prevent brute-force attacks.
     - Provides an emergency registration kill-switch (`registration_enabled` setting in `system_settings`), immediately rejecting registrations with HTTP 403 when disabled.
  2. **Idempotent Administrator Bootstrap CLI**:
     - Implemented `src/cli/bootstrap_admin.py` and `scripts/bootstrap_admin.bat`.
     - Idempotent: detects existing active administrator accounts and exits cleanly without modifying database state.
     - Interactive password input with masked prompts or cryptographically strong `--generate` flag (32-character random string).
     - Refuses to elevate standard `USER` accounts without explicit operator confirmation (`[y/N]`).
     - Flags bootstrapped admins with `must_change_password=True`, requiring mandatory credential rotation upon initial portal sign-in.
     - Immutably records `ADMIN_BOOTSTRAP` event in `audit_logs`.
  3. **Role-Based Access Control (RBAC) & Account Governance**:
     - Introduced `UserRole` enum (`USER`, `ADMIN`).
     - Added `require_admin` FastAPI dependency: rejects non-admin users with HTTP 403 Forbidden.
     - Added `is_active` boolean flag on `users`: deactivated users are rejected at token generation and profile retrieval with HTTP 401 Unauthorized.
     - Added `must_change_password` boolean flag: gated by a blocking UI barrier in Streamlit until updated.
  4. **Dedicated Administrator Portal (`src/frontend/views/admin.py`)**:
     - Visible strictly to authenticated operators with `ADMIN` role (`🛡️ Admin Portal` sidebar item).
     - Provides four functional tabs:
       * **Platform Overview**: System health, active/disabled user ratios, 30-day registration velocity, and registration kill-switch state.
       * **User Management**: Search/filter users, toggle account active/disabled status (with self-disable prevention), and generate temporary passwords for account recovery.
       * **Security & Audit**: Real-time inspectable audit log viewer for governance tracking.
       * **System Settings**: Platform-wide configuration controls (e.g. registration kill-switch toggle).
  5. **Strict Financial Privacy Boundary**:
     - Administrator endpoints and views query only `User`, `AuditLog`, and `SystemSettings` tables.
     - Joins or queries against financial tables (`FinancialAccount`, `Transaction`, `Budget`, `SavingsGoal`, `LoanDebt`, `InvestmentHolding`) are strictly forbidden in administrative code paths.
     - Customer balances, account numbers, transactions, budgets, debts, and investments remain 100% private and inaccessible to platform administrators.
  6. **Database Migration Safety**:
     - Authored Alembic migration `f6a91c8230b1_add_user_roles_and_admin_portal_schema.py`.
     - Non-destructive batch alteration adding `role`, `is_active`, `must_change_password` to `users`, and creating `system_settings`.
     - Applied and validated strictly on isolated test database `data/demo_finance.db`. `data/finance.db` verified untouched with SHA-256 integrity check.
- **Rationale**:
  - Delivers seamless user onboarding and necessary governance tools while rigorously upholding zero-trust tenant privacy principles.
  - Mitigates user discovery and brute-force registration risks.
  - Protects customer financial privacy by architectural construction rather than administrative policy alone.
- **Consequences**:
  - System supports multi-user self-service registration and administrative governance.
  - Automated test suite expanded to 214 tests (100% pass rate).
  - Production deployment remains strictly non-authorized until explicit release approval is granted.








