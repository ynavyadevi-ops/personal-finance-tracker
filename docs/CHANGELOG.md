# Changelog

All notable changes to the **Personal Finance Tracker (Python + SQL)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Future Multi-User Enterprise Deployment (Post-MVP)
- Production container packaging (Dockerfile & multi-stage compose).
- Cloud deployment and managed PostgreSQL replication.
- OAuth2 social login and biometric device authentication.

---

## [0.9.5] - 2026-11-16 (UAT Session 6C: Portfolio Polish)

### Added
- **Streamlit Settings View Data Portability & Archive Downloads**:
  - Implemented 3-column download action cards in `src/frontend/views/settings.py` for CSV, Excel (XLSX), and JSON backup archives.
  - Connected buttons to `ApiClient.export_transactions_csv`, `ApiClient.export_transactions_xlsx`, and `ApiClient.get_user_backup` in `src/frontend/api_client.py`.
  - Added user-friendly loading indicators (`st.spinner`), error alerts, and timestamped filenames (`transactions_export_{date}.csv`, `transactions_export_{date}.xlsx`, `user_backup_{date}.json`).
  - Added unit test `test_render_settings_view_export_download_triggers` in `tests/unit/test_frontend_views.py`.
- **Reusable Disposable Recruiter Portfolio Demo Dataset (`scripts/seed_demo_recruiter.py`)**:
  - Authored standalone seeding script targeting demo account `demo.recruiter@example.com` (isolated in `data/demo_finance.db`).
  - Seeded 4 realistic financial accounts: HDFC Salary Checking (₹68,500), ICICI Savings (₹83,000), Zerodha Demat (₹50,000), HDFC Regalia CC (-₹14,500).
  - Seeded monthly salary income (₹150,000), realistic expenses (Apartment Rent ₹35,000, Groceries ₹12,500, Electricity ₹3,200, Dining ₹4,500, Internet ₹1,200), and transfers (₹25,000 to Savings, ₹50,000 to Demat).
  - Seeded 3 monthly budgets: Housing & Utilities (₹40,000 cap), Groceries & Dining (₹20,000 cap), Transportation & Shopping (₹10,000 cap).
  - Seeded an Emergency Fund savings goal (target ₹300,000, current ₹120,000, 40.0% progress).
  - Seeded an active monthly broadband recurring rule (₹1,199).
  - Seeded an ICICI Home Renovation loan (₹200,000 principal at 10.5% p.a. for 24 months, ₹9,276.10 monthly EMI, ₹183,200 balance remaining).
  - Seeded NIFTYBEES ETF equity holdings (200 units at ₹250.00 cost basis) and ₹500 dividend receipt.
  - Ensured zero modification or disturbance to existing user accounts (`uat.financial@example.com`, `admin@local.dev`, `uat.lifecycle@example.com`).

### Changed
- **README.md Overhaul**:
  - Restructured `README.md` to accurately represent completed Phases 0–8 and UAT Sessions 1–6.
  - Removed unsupported claims regarding licensing, cloud deployment readiness, and coverage metrics.
  - Added Mermaid full-stack architecture diagram and complete documentation index.
  - Added verified local startup instructions for FastAPI backend, Streamlit frontend, administrative bootstrapping, and recruiter demo seeding.

### Security
- **Data Portability Privacy Verification**:
  - Validated that exports (`/api/v1/data/export/csv`, `/xlsx`, `/backup`) strictly filter by authenticated user ID (`where(Transaction.user_id == user_id)`).
  - Validated CSV formula injection prevention prepending `'` to `=`, `+`, `-`, `@`.
  - Confirmed JSON backup payload contains 0 password hashes, JWTs, or cross-tenant records.

### Verified
- **Quality & Regression Testing**:
  - Full automated pytest suite: 231 passed, 0 failed, 1 warning (deprecation notice for datetime.utcnow).
  - Ruff code linting & formatting: 0 errors across `src` and `tests`.
  - Mypy static type checking: 0 errors across 91 source files (`mypy --strict src`).
  - Bandit SAST security audit: 0 issues across 12,354 lines of code.
  - pip-audit vulnerability check: 0 known CVEs across all installed dependencies.
  - Database integrity: `data/finance.db` SHA-256 hash verified identical to baseline (`C7F03B0ADD08361A740AD688F7776FF62BA665D38EAB38BED615C4574E861EC7`).


---

## [0.9.4] - 2026-11-16 (UAT Session 6: Final System Validation & Release Readiness)

### Verified
- **Full Analytics Reconciliation (Phase B)**:
  - Verified deterministic cash flow calculations: Total Income ₹10,000, Total Expenses ₹2,000, Net Cash Flow ₹8,000, Savings Rate 80.00%.
  - Verified strict transfer exclusion: Inter-account transfers (₹3,000) are excluded from income and expense metrics.
  - Verified currency isolation: INR and USD metrics remain strictly separated with zero silent cross-currency mixing.
  - Verified budget utilization: Groceries & Dining cap ₹5,000, spent ₹2,000, remaining ₹3,000 (40.0% utilization, status NORMAL).
  - Verified savings goal progress: Milestone target ₹20,000, contributed ₹3,000 (15.0% progress).
- **Data Export & Backup Portability (Phases C & D)**:
  - Validated CSV export (`GET /api/v1/data/export/csv`) with RFC 4180 compliance, formula injection defense (`'`, `=`, `@`), user ownership scoping, and zero credential leakage.
  - Validated XLSX binary export (`GET /api/v1/data/export/xlsx`) readable via openpyxl.
  - Confirmed PDF export is NOT IMPLEMENTED in the REST API.
  - Validated complete user-scoped JSON backup snapshot generation (`GET /api/v1/data/backup`) across 9 domain entity tables without password/credential hashes.
  - Verified dry-run backup validation (`POST /api/v1/data/backup/validate`).
  - Confirmed destructive database restore is disabled by design (ADR-016) to prevent ledger corruption.
- **Security & Authorization Controls (Phase E)**:
  - Verified 401 Unauthorized for expired JWTs and malformed tokens.
  - Verified access rejection for disabled user accounts.
  - Verified RBAC enforcement: ordinary users strictly forbidden from admin endpoints (HTTP 403).
  - Verified administrative financial privacy boundary: administrator queries to financial transactions return zero customer records.
  - Verified cross-user resource isolation: users cannot access or mutate each other's accounts or recurring rules (HTTP 404).
  - Verified recurring cancellation notes bypass defense: recurring rules have no generic PATCH/PUT update endpoints; cancellation state cannot be tampered with via notes.
- **Quality & Release Gates (Phases F & G)**:
  - Pytest full suite: 230 passed, 0 failed, 0 skipped, 0 errors in 12.58s.
  - Static type checking: Mypy strict passed (0 errors across 91 source files).
  - Code formatting: Ruff passed (0 errors across `src` and `tests`).
  - SAST Security: Bandit passed (0 vulnerabilities in 12,195 lines).
  - Dependency Audit: pip-audit passed (0 known CVEs).
  - Production database integrity: `data/finance.db` SHA-256 hash verified identical to baseline (`C7F03B0ADD08361A740AD688F7776FF62BA665D38EAB38BED615C4574E861EC7`).
  - Execution gate halted; public deployment remains unauthorized.

---

## [0.9.3] - 2026-11-16 (UAT Session 5 & 5A: Investment Catalog, Recurring Cancellation & Credential Hardening)

### Security
- **Credential Hygiene & Secret Shielding**:
  - Removed all hardcoded test credentials from scratch scripts; replaced with interactive prompts, environment variables (`TEST_USER_B_PASSWORD`), and cryptographically secure tokens.
  - Added `scratch/` directory to `.gitignore` to prevent test scripts or credentials from being staged.
  - Verified Git commit log history: confirmed zero exposure of test credentials or JWT tokens in repository history.
  - Rotated password for test user `uat.session5@example.com` in `data/demo_finance.db`.
  - Added strict database isolation guard to test scripts (`"demo_finance.db" not in settings.DATABASE_URL` check).

### Added
- **Investment Asset Catalog (`GET /api/v1/investments/assets`)**:
  - Implemented read-only asset catalog query endpoint supporting optional `asset_type` filtering (`EQUITY`, `MUTUAL_FUND`, `BOND`, `ETF`, `CRYPTO`).
  - Added `InvestmentService.list_assets` and `ApiClient.list_investment_assets`.
  - Updated Streamlit UI (`src/frontend/views/investments.py`) to replace raw Asset UUID text input with searchable `st.selectbox` for Buy, Sell, and Dividend operations.
  - Added user-friendly catalog retrieval failure notice with an interactive "Retry Loading Assets" button.
- **Non-Destructive Recurring Cancellation (`DELETE /api/v1/recurring/{rule_id}` & `POST /api/v1/recurring/{rule_id}/cancel`)**:
  - Implemented soft-cancellation setting `is_active = False` with `[CANCELLED]` tag, permanently deactivating future schedule execution while preserving historical ledger transactions.
  - Enforced idempotency on repeated cancellation requests.
  - Added strict validation preventing execution or resumption of cancelled rules.
  - Updated Streamlit UI (`src/frontend/views/recurring.py`) to display `CANCELLED` status badge and interactive "Cancel" button.

### Fixed
- **Type Annotations & Linter Strictness**:
  - Fixed generic dictionary annotation in `src/frontend/views/dashboard.py`.
  - Added `limit` compatibility parameter to `ApiClient.list_transactions` in `src/frontend/api_client.py`.
  - Verified 100% compliance with `mypy --strict src` (0 errors across 91 files) and `ruff check`.

---

## [0.9.2] - 2026-11-16 (UAT Session 4A: Default Category Multi-Tenant Scoping Repair)

### Fixed
- **System Default Category Multi-Tenant Scoping**:
  - Remediated root cause of budget creation failure (HTTP 404): seeded default categories were previously bound to legacy `'default-user-id'`.
  - Updated `src/db/seed.py` so standard default categories are persisted with `user_id = None` and `is_default = True`, making them accessible to all authenticated users.
  - Safely released legacy user scoping on existing default categories in `data/demo_finance.db` (`UPDATE categories SET user_id = NULL WHERE is_default = 1 AND user_id = 'default-user-id'`).
  - Preserved all 13 original category IDs, names, types, colors, icons, and references.

### Added
- **Categories API Endpoint (`GET /api/v1/categories`)**:
  - Exposes `list_categories` endpoint supporting optional filtering by `category_type` (`INCOME` / `EXPENSE`).
  - Returns user-accessible personal categories combined with global system default categories.
  - Strictly preserves tenant privacy: users cannot view other users' custom categories.
- **Frontend Category Selection & Dynamic Dropdown**:
  - Added `api_client.list_categories` in `src/frontend/api_client.py`.
  - Updated `src/frontend/views/budgets.py` to replace raw UUID entry with a user-friendly dropdown populated with available expense categories (identifying system defaults).
- **Automated Test Coverage**:
  - Added `tests/unit/test_category_access.py` covering multi-tenant access, private category isolation, idempotency, transaction validity, and budget type constraints.
  - Added `tests/integration/test_categories_api.py` validating the categories REST API endpoint.

---

## [0.9.1] - 2026-11-16 (Post-Phase 8 Enhancement: User Registration & Dedicated Admin Portal)

### Added
- **Public User Registration (`POST /api/v1/auth/register`)**:
  - Secure self-service account creation with normalized emails and Argon2id password hashing.
  - Mandatory password complexity enforcement (min 8 chars, uppercase, lowercase, digit, special character).
  - Anti-enumeration protection: duplicate registration returns generic safe failure (`ValidationError`), preventing user discovery.
  - In-memory sliding-window IP rate limiting to mitigate brute-force registration abuse.
  - Configurable platform kill-switch (`registration_enabled` setting): immediately rejects new registrations with HTTP 403 when deactivated.
- **Idempotent Administrator Bootstrap CLI (`src/cli/bootstrap_admin.py` & `scripts/bootstrap_admin.bat`)**:
  - Local CLI tool supporting `--email` and `--generate` flags for initial administrator setup.
  - Idempotent: detects existing active admins and exits cleanly without modification.
  - Refuses to silently elevate standard `USER` accounts without explicit interactive confirmation.
  - Enforces `must_change_password=True` for mandatory credential rotation on first portal login.
  - Immutably records `ADMIN_BOOTSTRAP` event in `audit_logs`.
- **Role-Based Access Control (RBAC)**:
  - Added `UserRole` enum (`USER`, `ADMIN`) with server-side `require_admin` dependency enforcement.
  - Added `is_active` governance flag; deactivated accounts are blocked at login (HTTP 401) and token validation.
  - Added `must_change_password` flag; users with temporary passwords are gated by a mandatory change screen before accessing financial tools.
- **Dedicated Administrative Portal (`src/frontend/views/admin.py`)**:
  - Accessible strictly to authenticated accounts with `ADMIN` role (`🛡️ Admin Portal` nav item).
  - **Platform Overview**: Real-time KPI metrics for total users, active vs. disabled counts, 30-day velocity, and registration status.
  - **User Governance**: Search and filter users by name, email, role, and active status; activate/deactivate user accounts; one-time temporary password generation with mandatory rotation flag. Admin cannot disable own account.
  - **Security & Audit Log**: Real-time inspectable audit log viewer for security tracking and administrator actions.
  - **System Settings**: Interactive toggle for the public registration kill-switch (`SystemSettings` model).
  - **Strict Financial Privacy Boundary**: Administrative API and views are completely isolated from financial databases—no access to customer transactions, accounts, balances, budgets, loans, or investments.
- **Database Schema Migration (`alembic/versions/f6a91c8230b1_add_user_roles_and_admin_portal_schema.py`)**:
  - Non-destructive batch migration on `users` table adding `role`, `is_active`, `must_change_password` with safe defaults (`USER`, `1`, `0`).
  - Added `system_settings` key-value table initialized with `registration_enabled='true'`.
  - Applied cleanly and verified on isolated demo database `data/demo_finance.db`. `data/finance.db` preserved untouched.
- **Automated Test Suite Expansion**:
  - Added `tests/unit/test_cli_bootstrap_admin.py` (8 unit tests) and `tests/integration/test_auth_admin_enhancement.py` (12 integration tests).
  - Total automated suite expanded from 192 to **214 passed tests** (100% pass rate) with **79% overall coverage** in 16.7s.

---

## [0.9.0] - 2026-11-16 (Phase 8: System Hardening, Comprehensive Testing, Packaging & Release Readiness)

### Added
- **System Hardening Integration Test Suite (`tests/integration/test_system_hardening.py`)**:
  - Implemented 14 rigorous automated integration tests:
    - Zero and negative amount validation across transactions, budgets, goals, loans, and investment orders (HTTP 422).
    - Large numeric boundary precision tests (`Decimal("999999999999.99")`) verifying exact 2-decimal arithmetic without float precision drift.
    - Currency mismatch prevention on transfers (`CurrencyMismatchError` -> HTTP 422).
    - Repeated transaction reversal rejection enforcing compensating idempotency (HTTP 422).
    - Portfolio liquidation sufficiency checks rejecting excess unit sales (`InsufficientUnitsError` -> HTTP 422).
    - Double-entry transfer balance conservation ($5,000 + $1,000 = $3,500 + $2,500 = $6,000) and full balance restoration upon reversal ($5,000 + $1,000 = $6,000).
    - Multi-tenant tenant isolation: User B token cannot read, patch, delete, or reverse User A's accounts, transactions, or records (HTTP 404).
    - Unauthenticated request blocking across all domain endpoints (HTTP 401).
    - Permanent absence confirmation of public enrollment endpoint (`POST /api/v1/auth/enroll` returns 404).
    - Backup snapshot dry-run schema validation: rejects incompatible versions and malformed payloads (`is_valid: False`).
  - Total automated test suite expanded to **192 passed tests** with **81% overall coverage** in 15.2s.
- **Windows 11 Reproducible Local MVP Packaging (`scripts/`)**:
  - Added `scripts/run_backend.bat`: automated FastAPI startup bound to `127.0.0.1:8000`.
  - Added `scripts/run_frontend.bat`: automated Streamlit startup bound to `127.0.0.1:8501`.
  - Added `scripts/enroll_user.bat`: local masked administrative credential enrollment CLI.
  - Added `scripts/verify_system.bat`: automated quality gates verification (Pytest, Ruff, Mypy).
- **Manual User Acceptance Testing Checklist (`docs/UAT_CHECKLIST.md`)**:
  - Detailed browser verification procedure covering all 10 core views, authentication, exports, imports, backup validation, and privacy controls with explicit expected results and failure indicators.
- **Configuration Hardening (`.env.example`)**:
  - Documented all application settings, local safe loopback defaults (`127.0.0.1`), token lifetimes, CORS origins, and AI privacy flags with zero hardcoded production secrets.

### Security & Integrity Audits
- **Bandit SAST**: 0 issues identified across 10,625 lines of application code (`src/`).
- **pip-audit**: 0 known CVE vulnerabilities found across all installed dependencies.
- **Ruff Linter & Formatter**: 0 lint errors, 117 files cleanly formatted.
- **Mypy Type Checker**: Strict mode pass across 70 source files (0 errors).
- **Persistent Data Preservation**: Verified `data/finance.db` records (`user@local.dev` and `Primary Checking` USD 1500) remain 100% intact.
- **Release Readiness Verdict**: Classified as **READY FOR LOCAL MVP TESTING**. Public deployment remains strictly non-authorized.

---

## [0.8.0] - 2026-11-15 (Phase 7: Analytics Engine, Plotly Visualizations & AI Insights)

### Added
- **Financial Analytics Engine (`src/services/analytics_service.py`)**:
  - Pure Python & Decimal calculations enforcing double-entry rules: transfers are strictly excluded from income and expenses, reversals are handled without data skew, and multi-currency metrics are rigorously isolated.
  - Computes monthly cash flow, category spending distributions, 6-month and 12-month trend trajectories, account balance distributions, budget vs. actual utilization, savings milestones, and debt paydowns.
- **Rule-Based Deterministic Insights (`src/services/analytics_service.py`)**:
  - Deterministic financial observations on cash flow health, spending acceleration, budget caps, savings targets, and debt milestones, with transparent step-by-step calculation derivations.
- **Plotly Visualizer Component Library (`src/frontend/components/charts.py`)**:
  - Implemented reusable dark fintech chart builders:
    - Grouped bar charts for monthly income vs. expenses (`create_income_expense_bar_chart`).
    - Area & scatter charts for net cash flow trajectories (`create_cash_flow_trend_chart`).
    - Donut charts for category expense distribution (`create_category_donut_chart`) with custom hover templates.
    - Horizontal comparative bar charts for budget caps vs. actuals (`create_budget_vs_actual_chart`).
    - Stacked horizontal bar charts for savings milestone completion (`create_savings_progress_chart`).
    - Donut charts for portfolio asset allocation by cost basis (`create_investment_allocation_chart`).
- **Privacy-First AI Insights Service (`src/services/ai_insights.py`)**:
  - Strict privacy protections: disabled by default with mandatory user opt-in consent toggle.
  - De-identification pipeline: strips all PII, account IDs, merchant names, raw descriptions, passwords, and JWT tokens before processing.
  - Local synthesis generating plain-language observations without third-party cloud leakage.
  - Mandatory informational non-advice disclaimer permanently attached.
- **Dedicated Analytics View (`src/frontend/views/analytics.py`)**:
  - Multi-tab interactive view covering Cash Flow & Trends, Category Spending, Budgets & Milestones, Debts & Portfolio, and Smart Insights & AI Privacy, with currency and timeframe filters.
- **Navigation Shell Update (`src/frontend/app.py`, `src/frontend/views/__init__.py`)**:
  - Added "📈 Analytics & Insights" to sidebar navigation, supporting 10 views seamlessly.
- **Automated Test Suite Expansion (`tests/unit/test_analytics_service.py`, `tests/unit/test_ai_insights.py`, `tests/unit/test_charts.py`)**:
  - Added 19 comprehensive unit tests covering financial analytics math, transfer exclusion, reversal handling, AI privacy boundaries, and Plotly figure generation.
  - Total test suite expanded to 178 passing tests with 81% overall coverage.

---

## [0.7.0] - 2026-11-15 (Phase 6: Streamlit Advanced Feature Pages)

### Added
- **Savings Goals & Milestones (`src/frontend/views/goals.py`)**:
  - Live milestone progress tracking with target amount, current funded amount, remaining balance, and visual progress bars (`st.progress`).
  - Milestone status badges (`ACHIEVED`, `IN PROGRESS`).
  - Goal contribution form with decimal validation and optional notes via `POST /api/v1/goals/{id}/contribute`.
  - Goal withdrawal form with balance boundary enforcement via `POST /api/v1/goals/{id}/withdraw`.
  - Savings goal creation form with target amount, currency selection, target date, and notes via `POST /api/v1/goals`.
- **Loans & Debt Liabilities (`src/frontend/views/loans.py`)**:
  - Loan liability summaries displaying lender, principal, remaining balance, annual interest rate, term duration, and monthly EMI.
  - Interactive amortization schedule viewer displaying installment breakdown: principal component, interest component, total payment, and remaining principal.
  - Installment repayment form selecting unpaid payment numbers via `POST /api/v1/loans/{id}/payment`.
  - Loan obligation creation form binding liabilities to user accounts via `POST /api/v1/loans`.
- **Investment Portfolio & Holdings (`src/frontend/views/investments.py`)**:
  - Prominent architectural valuation disclaimer emphasizing that positions reflect historical weighted-average cost basis rather than live market quotes.
  - Holdings directory displaying units held (4 decimal precision), cost basis per unit, and total acquisition cost basis.
  - Security purchase form via `POST /api/v1/investments/buy`.
  - Security liquidation form with unit sufficiency check and real-time realized capital gains/losses breakdown via `POST /api/v1/investments/sell`.
  - Dividend income logging form via `POST /api/v1/investments/dividend`.
- **Recurring Transaction Rules (`src/frontend/views/recurring.py`)**:
  - Proactive due executions alert banner highlighting transactions that have reached scheduled recurrence dates.
  - Manual execution triggers generating verified double-entry ledger postings via `POST /api/v1/recurring/{id}/execute`.
  - Recurring rules directory displaying frequency, intervals, amounts, and next occurrence dates.
  - One-click pause and resume schedule toggles via `POST /api/v1/recurring/{id}/pause` and `resume`.
  - Recurring template creation form supporting Daily, Weekly, Biweekly, Monthly, Quarterly, and Yearly schedules via `POST /api/v1/recurring`.
- **Expanded Navigation & Views (`src/frontend/app.py`, `src/frontend/views/__init__.py`)**:
  - Integrated all 9 application views into sidebar navigation: Dashboard, Accounts, Transactions, Budgets, Savings Goals, Loans & Debts, Investments, Recurring Rules, and Settings.
- **ApiClient Advanced Method Extensions (`src/frontend/api_client.py`)**:
  - Added 17 authenticated endpoints covering goals, loans, investments, and recurring rules with Bearer header injection and error handling.
- **Automated Test Suite Expansion (`tests/unit/test_frontend.py`, `tests/unit/test_frontend_views.py`)**:
  - Added 8 comprehensive unit tests covering all new ApiClient methods and view rendering functions.
  - Full test suite expanded to 159 passing tests with 80% coverage.

### Fixed
- **Windows Terminal Sandbox Pytest Workaround**:
  - Identified and documented root cause of integration test hangs inside restricted Windows sandboxes due to AnyIO/Proactor loopback socket blocking.
  - Verified unsandboxed execution protocol (`BypassSandbox: true`), enabling all 159 tests to pass in 14.0 seconds.
- **Recurring View Category Dependency Alignment**:
  - Removed extraneous `list_categories` call from `src/frontend/views/recurring.py` to match backend contract where `category_id` is purely optional.

---

## [0.6.0] - 2026-11-15 (Phase 5: Streamlit Frontend Core UI & Core Pages)

### Added
- **Centralized Authenticated API Client (`src/frontend/api_client.py`)**:
  - Implemented `ApiClient` wrapping `httpx.Client` with Bearer token injection, connection timeout handling, structured error tuple extraction, and automatic 401 session expiration handling.
  - Strictly prevented automatic retries on state-mutating POST operations (financial transactions and transfers).
  - Sanitized logging ensuring passwords, tokens, and credentials are never recorded in application logs.
- **Dark Fintech Design System (`src/frontend/components/ui.py`)**:
  - Designed premium dark palette (`#0B1120` background, `#151E30` surface, `#1D2940` elevated surface, `#38BDF8` accent, `#22C55E` positive, `#F87171` negative, `#F8FAFC` text, `#94A3B8` secondary text).
  - Built custom CSS injection for containers, metric cards, input fields, and status badges (`render_badge`).
  - Implemented decimal-safe currency display utility (`format_money`) enforcing Indian Rupee (`₹`) default, accurate USD (`$`) rendering, and strict prevention of cross-currency summation.
- **Authentication Barrier & Navigation Shell (`src/frontend/app.py`, `src/frontend/views/login.py`)**:
  - Enforced authentication gate redirecting unauthenticated users to a secure login portal consuming `POST /api/v1/auth/token`.
  - In-memory session state management in `st.session_state` with automatic token revocation on logout.
  - Built sidebar navigation controller with authenticated user identity badge, backend connection health probe, and access to Dashboard, Accounts, Transactions, Budgets, and Settings.
- **Core Page 1 — Financial Overview Dashboard (`src/frontend/views/dashboard.py`)**:
  - Total balances grouped strictly by currency (INR assets, USD assets) preventing combined summation without an exchange policy.
  - Monthly cash flow cards (Income, Expense, Net Flow) strictly excluding inter-account transfers.
  - Real-time active budget utilization progress bars with status badges (`NORMAL`, `WARNING`, `EXCEEDED`).
  - Recent transactions table previewing latest activity.
- **Core Page 2 — Accounts Management (`src/frontend/views/accounts.py`)**:
  - Live accounts directory presenting account types, institutions, currencies, and reconciled current balances.
  - In-place metadata editing form for account names and institutions via `PUT /api/v1/accounts/{id}`.
  - Safe account archiving workflow with mandatory operator confirmation checkbox.
  - New account registration form validating exact decimal opening balances.
- **Core Page 3 — Transactions & Ledger (`src/frontend/views/transactions.py`)**:
  - Queryable ledger with account, transaction type, and pagination filters.
  - Income and expense recording form with decimal validation, description enforcement, and error display.
  - Inter-account transfer form with proactive cross-currency mismatch warnings.
  - Compensating transaction reversal modal with reason input and mandatory operator confirmation.
- **Core Page 4 — Category Budgets (`src/frontend/views/budgets.py`)**:
  - Monthly category budget overview with utilization percentages, remaining amounts, and overspending indicators.
  - Interactive month and year period selector.
  - Monthly budget allocation creation form with optional unspent rollover toggle.
- **Core Page 5 — Settings & Profile (`src/frontend/views/settings.py`)**:
  - Authenticated user profile presentation (Name, Email, User ID, Creation timestamp).
  - Default core currency preference (`INR (₹)`) clearly highlighted.
  - System runtime and security architecture specifications.
  - One-click session termination and logout button.
- **Automated Frontend Test Suite (`tests/unit/test_frontend.py`, `tests/unit/test_frontend_views.py`)**:
  - Added 19 comprehensive unit tests covering API client methods, Bearer authorization, 401 error extraction, currency formatting across currencies, and view rendering.
  - Total automated tests increased from 134 to 151 tests (100% pass rate in ~9.1s, 83% overall code coverage).
  - Preserved existing database records `Primary User ('user@local.dev', None)` and `Primary Checking ('USD', 1500.00)` intact in `data/finance.db`.

---

## [0.5.0] - 2026-11-15 (Phase 4: FastAPI REST API & Data Portability Services)

### Added
- **Authentication & Security Foundation (`src/core/security.py`, `src/api/routers/auth.py`, `src/cli/enroll.py`)**:
  - Implemented Argon2id password hashing and cryptographic verification via `pwdlib[argon2]`.
  - Implemented signed, short-lived JSON Web Token (JWT) issuing and decoding using `pyjwt` (`HS256`, 60-minute lifetime, standard claims: `sub`, `exp`, `iat`, `type="access"`, `iss="personal-finance-tracker"`).
  - Added Alembic migration `6c8ca07763d0` safely adding `hashed_password` (nullable) to the `users` table via `batch_alter_table`.
  - Implemented `POST /api/v1/auth/register` (new user registration with secure Argon2id hash).
  - Implemented `POST /api/v1/auth/token` (OAuth2 password form login returning standard OAuth2 Bearer token).
  - Implemented `GET /api/v1/auth/me` (retrieval of current user profile; strictly excludes password hashes).
  - Injected `get_current_user` into `get_current_user_id` so all financial endpoints automatically enforce JWT authentication.
  - Implemented administrative CLI `src/cli/enroll.py` (`python -m src.cli.enroll --email <email>`) for secure, local password enrollment of legacy accounts with masked `getpass` entry, anti-overwrite protection, and atomic commits.
- **RESTful Domain Routers (`src/api/routers/`)**:
  - `src/api/routers/transactions.py`: Income/expense posting (`POST /`), atomic transfers (`POST /transfer`), compensating reversals (`POST /{id}/reverse`), pagination/filtering (`GET /`), transaction detail (`GET /{id}`), and mathematical balance reconciliation (`GET /reconcile/{account_id}`).
  - `src/api/routers/budgets.py`: Category budget allocations (`POST /`), single category utilization (`GET /utilization`), and period overviews (`GET /period`).
  - `src/api/routers/goals.py`: Savings milestones (`POST /`, `GET /`), milestone contributions (`POST /{id}/contribute`), withdrawals (`POST /{id}/withdraw`), and progress calculations (`GET /{id}/progress`).
  - `src/api/routers/loans.py`: Loan debt liabilities with auto-generated fixed-rate amortization schedules (`POST /`), loans list (`GET /`), loan details (`GET /{id}`), and payment instalment recording (`POST /{id}/payment`).
  - `src/api/routers/investments.py`: Security purchase trades with weighted-average cost basis (`POST /buy`), liquidation trades with realized capital P&L (`POST /sell`), dividend earnings logs (`POST /dividend`), and portfolio holdings (`GET /holdings`).
  - `src/api/routers/recurring.py`: Recurrence rules (`POST /`, `GET /`), due rule queries (`GET /due`), schedule execution with duplicate occurrence prevention (`POST /{id}/execute`), and pause/resume (`POST /{id}/pause`, `POST /{id}/resume`).
- **Data Portability Pipeline (`src/services/portability_service.py`, `src/api/routers/data_portability.py`)**:
  - `StatementImportService`: Pandas/openpyxl engine parsing CSV and XLSX statements with configurable column mappings (Date, Amount, Description, Category, Type), duplicate transaction detection, dry-run preview (`POST /api/v1/data/import/preview`), and atomic batch commit (`POST /api/v1/data/import/commit`).
  - `DataExportService`: Filtered user transaction export streaming in RFC 4180 CSV (`GET /api/v1/data/export/csv`) and Excel XLSX (`GET /api/v1/data/export/xlsx`) with spreadsheet formula injection defense (`=, +, -, @, \t, \r` escaping).
  - `BackupService`: Complete user-scoped JSON backup snapshot generation across all 11 database entities (`GET /api/v1/data/backup`) with exact Decimal string formatting, strictly excluding password hashes.
  - Non-destructive dry-run backup validation endpoint (`POST /api/v1/data/backup/validate`) verifying schema version and completeness without modifying database state. Destructive restore is strictly non-executable.
- **Automated Integration & Unit Test Suite**:
  - Added 33 new integration tests across `test_auth_api.py`, `test_transactions_api.py`, `test_budgets_api.py`, `test_goals_api.py`, `test_loans_api.py`, `test_investments_api.py`, `test_recurring_api.py`, and `test_data_portability_api.py`.
  - Added 14 administrative CLI unit tests in `tests/unit/test_cli_enroll.py` verifying legacy account password enrollment, anti-overwrite protection, and zero credential leakage.
  - Total automated tests increased from 87 to 134 tests (100% pass rate, 89% overall test coverage).
  - All existing Account CRUD regression tests pass without modification.
  - Preserved existing database records `Primary User ('user@local.dev', None)` and `Primary Checking ('USD', 1500.00)` in `data/finance.db`.

### Removed
- **Eliminated Public Legacy Enrollment Endpoint**:
  - Completely removed `POST /api/v1/auth/enroll` from `src/api/routers/auth.py` and `UserEnrollPassword` from `src/schemas/user.py` to eliminate vulnerability where unauthenticated callers could claim legacy accounts using email alone. Legacy password enrollment is now strictly restricted to the local administrative CLI (`python -m src.cli.enroll`).

---

## [0.4.0] - 2026-11-15 (Phase 3: Core Accounting Engine, Financial Services & Domain Logic)

### Added
- **Core Financial Domain Services (`src/services/`)**:
  - `src/services/ledger_service.py`: `LedgerService` implementing double-entry accounting invariant validation ($\sum \text{Debits} == \sum \text{Credits}$), deterministic account balance computation across asset and liability accounts, and bank statement balance reconciliation.
  - `src/services/transaction_service.py`: `TransactionService` supporting income recording (debit to asset), expense recording (credit to asset/liability), atomic inter-account transfers, transparent idempotency protection, and compensating transaction reversals.
  - `src/services/budget_service.py`: `BudgetService` managing monthly category allocations, SQL monthly spending aggregation (strictly excluding transfers), threshold status calculation (NORMAL, WARNING, EXCEEDED), and unspent rollover carryforward.
  - `src/services/goal_service.py`: `SavingsGoalService` orchestrating savings milestone targets, contributions, withdrawals, progress percentages, and automatic achievement tracking.
  - `src/services/loan_service.py`: `LoanService` implementing exact fixed-rate amortization schedules using Decimal compound formulas, instalment repayments with principal vs. interest separation, and loan payoff settlement.
  - `src/services/recurring_service.py`: `RecurringService` computing next occurrence dates across all calendar frequencies (Daily, Weekly, Biweekly, Monthly, Quarterly, Yearly), due rule evaluation, automated transaction spawning, and duplicate execution prevention.
  - `src/services/investment_service.py`: `InvestmentService` tracking security purchases with weighted-average cost basis recalculation, sales with holding sufficiency validation and realized gain/loss math, and dividend logging.
- **Repository Data Access Layer (`src/repositories/`)**:
  - Added dedicated repositories: `TransactionRepository`, `CategoryRepository`, `BudgetRepository`, `SavingsGoalRepository`, `LoanRepository`, `RecurringRepository`, and `InvestmentRepository`.
- **Pydantic v2 DTO Schemas (`src/schemas/`)**:
  - Added validation schemas: `TransactionCreate`, `TransferCreate`, `TransactionRead`, `AccountReconciliation`, `BudgetCreate`, `BudgetUtilization`, `SavingsGoalCreate`, `SavingsGoalProgress`, `LoanCreate`, `AmortizationScheduleItem`, `RecurringRuleCreate`, `InvestmentBuyRequest`, `InvestmentSellRequest`, and `RealizedGainLossResult`.
- **Domain Exceptions (`src/core/exceptions.py`)**:
  - Added `CurrencyMismatchError` (HTTP 422), `InsufficientUnitsError` (HTTP 422), and `PermissionDeniedError` (HTTP 403).
- **Automated Unit Test Suite**:
  - Added 46 comprehensive unit tests across all 7 new domain services in `tests/unit/`.
  - Total automated test count increased from 41 to 87 tests (100% pass rate).
  - Code formatting: 75 files verified with Ruff.
  - Type checking: 0 errors across 56 files in Mypy strict mode.
  - Security scanning: 0 issues in Bandit (4,969 LOC) and 0 vulnerabilities in pip-audit.

---

## [0.3.0] - 2026-11-15 (Phase 2: Database Modeling, SQLAlchemy ORM & Alembic Migrations)

### Added
- **Complete Relational Domain Models (`src/db/models/`)**:
  - `src/db/models/category.py`: `Category` with self-referential hierarchy (`parent_id`), `CategoryType` (`INCOME`, `EXPENSE`), visual colors, icons, and unique constraint `uq_categories_user_name_parent`.
  - `src/db/models/transaction.py`: `Transaction` business events and `TransactionEntry` double-entry ledger line items with `EntryType` (`DEBIT`, `CREDIT`), `TransactionType` (`INCOME`, `EXPENSE`, `TRANSFER`), `ondelete="RESTRICT"` on accounts, and positive amount check constraints (`chk_transactions_positive_amount`, `chk_transaction_entries_positive_amount`).
  - `src/db/models/budget.py`: `Budget` monthly category allocation with month check (`1 <= month <= 12`), positive amount check, and period uniqueness `uq_budgets_user_cat_period`.
  - `src/db/models/goal.py`: `SavingsGoal` milestone tracking with positive target and non-negative current amount check constraints.
  - `src/db/models/loan.py`: `LoanDebt` and `LoanPaymentSchedule` models with `InterestType` (`FIXED`, `FLOATING`), positive principal check, non-negative remaining balance and interest checks, positive term months check, and ordered amortization schedule entries with uniqueness `uq_loan_schedules_loan_number`.
  - `src/db/models/recurring.py`: `RecurringRule` with `Frequency` (`DAILY`, `WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`), interval check constraint (`"interval" > 0`), and positive amount check constraint.
  - `src/db/models/investment.py`: Comprehensive investment models:
    - `InvestmentAsset`: Master security catalog with `AssetType` (`EQUITY`, `MUTUAL_FUND`, `ETF`, `BOND`, `GOLD`, `CRYPTO`, `OTHER`), unique symbol and ISIN.
    - `InvestmentHolding`: User positions with 4-decimal quantity precision (`Numeric(18, 4)`), cost basis, total cost, and uniqueness on `(user_id, account_id, asset_id)`.
    - `InvestmentTransaction`: Trade ledger with `InvestmentTxType` (`BUY`, `SELL`, `DIVIDEND`, `SPLIT`, `INTEREST`), linked transaction reference, and non-negative constraints.
  - `src/db/models/audit.py`: `AuditLog` append-only immutable ledger tracking entity mutations, old/new value JSON snapshots, user IP address, and client user-agent.
- **Back-Populating Model Relationships**:
  - Updated `User` (`src/db/models/user.py`) to expose back-populating collections to categories, transactions, budgets, goals, loans, recurring rules, holdings, investment transactions, and audit logs.
  - Updated `FinancialAccount` (`src/db/models/account.py`) to expose relationships to transaction entries, loans, recurring rules, holdings, and investment transactions.
  - Re-exported all models and enums cleanly in `src/db/models/__init__.py`.
- **Alembic Database Migration (`472e31906438`)**:
  - Generated and validated migration `alembic/versions/472e31906438_create_phase_2_relational_models.py` with explicit constraint names and SQLite batch mode support (`render_as_batch=True`).
  - Applied migration cleanly to `data/finance.db` via `alembic upgrade head`.
  - Verified existing database records (specifically `Primary Checking` with `USD` and `1500.00` balance) were preserved without modification.
  - Tested migration downgrade to `fba246fe5321` and re-upgrade to head on an isolated disposable test database.
- **Development Database Seeder Expansion (`src/db/seed.py`)**:
  - Added 13 default Indian categories across income and expense flows (Salary, Investments, Housing, Groceries, Utilities, Transport, etc.).
  - Added sample investment asset (`NIFTYBEES` ETF) and sample savings goal (`Emergency Fund`) seeded idempotently.
- **Automated Test Suite**:
  - `tests/unit/test_phase2_models.py`: 10 comprehensive unit tests covering model relationships, check constraints, unique constraints, cascade deletes, account deletion restrictions, and 4-decimal quantity precision.
  - `tests/integration/test_migrations.py`: 1 integration test verifying Alembic upgrade, reflection of all 15 tables, downgrade to Phase 1, and re-upgrade to head.
  - Total automated tests increased from 30 to 41 tests (100% pass rate).
  - Code coverage: 89% across `src/`.

---

## [0.2.0] - 2026-11-15 (Phase 1: Environment and Application Foundation)

### Changed & Remediated
- **Currency System Alignment to INR (₹)**:
  - Transitioned default currency from USD to **INR (₹)** across SQLAlchemy models (`FinancialAccount.currency`), Pydantic schemas (`AccountCreate.currency`), monetary utilities (`format_currency`), and Streamlit forms.
  - Preserved existing database records without automated conversion or exchange-rate distortion.
  - Guaranteed migration immutability by leaving previously applied migration `fba246fe5321` intact.
- **Authoritative Roadmap Adoption (Phases 0–8)**:
  - Reconciled documentation roadmap to the authoritative 9-phase lifecycle (Phases 0 through 8).
  - Explicitly mapped recurring transactions, savings goals, loans & debts, investments, and AI insights to dedicated delivery phases.
- **Protected Status for Existing Account CRUD**:
  - Formally protected existing account models, repository, service, and FastAPI REST endpoints.
  - Added 8 unit and integration regression tests (total 30 automated tests, 100% pass rate).

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
