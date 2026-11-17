# Personal Finance Tracker (Python + SQL)

A secure, audit-ready, full-stack personal finance and wealth management platform built on **Python 3.12** and **SQL**. It provides double-entry transaction ledgers, monthly category budgets, savings milestones, debt amortization, investment portfolio cost basis tracking, and deterministic analytics.

---

## 1. Project Overview

- **Architecture**: Decoupled full-stack architecture:
  - **Frontend UI**: [Streamlit](https://streamlit.io/) reactive web dashboard with interactive [Plotly](https://plotly.com/) visual analytics.
  - **Backend API**: [FastAPI](https://fastapi.tiangolo.com/) high-performance asynchronous REST service.
  - **Database Layer**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) ORM + [Alembic](https://alembic.sqlalchemy.org/) schema migrations.
  - **Data Processing**: [Pandas](https://pandas.pydata.org/) for transaction aggregations, statement import parsing, and tabular exports.
  - **Validation & Typing**: [Pydantic v2](https://docs.pydantic.dev/) for runtime request/response validation and strict schema typing.
- **Financial Arithmetic & Invariants**:
  - Exact monetary arithmetic using Python's native `decimal.Decimal` and SQL `Numeric(18, 2)` (zero IEEE 754 floating-point drift).
  - Double-entry accounting core enforcing $\sum \text{Debits} == \sum \text{Credits}$ across all financial mutations.
  - Inter-account transfers and balance reversals strictly excluded from income and expense analytics.
- **Persistence Strategy**:
  - **Current Runtime**: Embedded SQLite with enforced foreign key constraints (`data/finance.db` for protected baseline, `data/demo_finance.db` for local UAT).
  - **Post-MVP Architectural Target**: Designed for PostgreSQL 16+ via SQLAlchemy 2.0 engine abstraction.
- **Security & Quality Baseline**:
  - Static Application Security Testing via [Bandit](https://github.com/PyCQA/bandit) (0 findings across 12,000+ lines).
  - Dependency vulnerability auditing via [pip-audit](https://github.com/pypa/pip-audit) (0 known CVEs).
  - Strict static type checking via [Mypy](https://mypy.readthedocs.io/) strict mode (0 errors across 91 source files).
  - PEP 8 code linting and formatting via [Ruff](https://astral.sh/ruff) (0 errors).
  - Comprehensive automated test suite featuring **231 passed tests** via [Pytest](https://docs.pytest.org/).
- **Current Status**: **Local MVP Release Candidate (Phases 0–8 & UAT Sessions 1–6 Completed & Verified)**. Public cloud deployment is strictly non-authorized in this local phase.

---

## 2. System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          Streamlit Web Dashboard             │
                  │   (Reactive Views, Plotly Visualizations)    │
                  └───────────────────────┬──────────────────────┘
                                          │ HTTP / JSON
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │             FastAPI REST API v1              │
                  │ (OAuth2 Bearer Auth, Pydantic v2 Validation) │
                  └──────┬───────────────────────────────┬───────┘
                         │                               │
                         ▼                               ▼
       ┌──────────────────────────────────┐   ┌───────────────────────────┐
       │     Domain Services Layer        │   │    Security & Governance  │
       │ • LedgerService (Double-Entry)   │   │ • Argon2id Password Hash  │
       │ • AccountService                 │   │ • Role-Based Access (RBAC)│
       │ • BudgetService & CategoryService│   │ • Sliding-Window Rate Lim │
       │ • SavingsGoalService             │   │ • Formula Injection Guard │
       │ • LoanService (Amortization)     │   │ • Tamper-Evident Audit Log│
       │ • InvestmentService (Cost Basis) │   └───────────────────────────┘
       │ • AnalyticsEngine (Deterministic)│
       │ • PortabilityService (CSV/Excel) │
       └─────────────────┬────────────────┘
                         │
                         ▼
       ┌──────────────────────────────────┐
       │   SQLAlchemy 2.0 ORM & Alembic   │
       │ (11 Relational Models, Decimals) │
       └─────────────────┬────────────────┘
                         │
                         ▼
       ┌──────────────────────────────────┐
       │       SQLite Database Engine     │
       │   (data/demo_finance.db or       │
       │    protected data/finance.db)    │
       └──────────────────────────────────┘
```

---

## 3. Technology Stack & Verified Releases

| Component | Technology | Target Version | Verified Role / Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `3.12.x` | Core programming runtime |
| **Backend Framework** | FastAPI | `0.115.x` | High-performance asynchronous REST API backend |
| **ASGI Server** | Uvicorn | `0.34.x` | Production-grade ASGI server implementation |
| **Frontend Dashboard** | Streamlit | `1.41.x` | Reactive financial dashboard UI & data presentation |
| **Database ORM** | SQLAlchemy | `2.0.x` | Declarative relational database mapping & session lifecycle |
| **Schema Migrations** | Alembic | `1.14.x` | Revision-controlled database schema migrations |
| **Data Validation** | Pydantic | `2.10.x` | Strict request/response DTO validation and typing |
| **Data Analysis** | Pandas | `2.2.x` | Statement parsing, aggregation, and export formatting |
| **Visualization** | Plotly | `5.24.x` | Dynamic charts (cash flow trends, category donuts, budgets) |
| **Password Hashing** | Argon2-cffi | `23.x` | Memory-hard Argon2id cryptographic password hashing |
| **Testing** | Pytest + HTTPX | `8.3.x` / `0.28.x` | 231 unit, integration, and security tests |
| **Security SAST** | Bandit | `1.8.x` | Static security scanner for Python source code |
| **Dependency Audit** | pip-audit | `2.8.x` | Supply-chain CVE scanner against PyPI advisories |
| **Formatting / Lint** | Ruff | `0.9.x` | Fast Python linter and formatter (PEP 8) |
| **Type Checking** | Mypy | `1.15.x` | Strict static type checking |

---

## 4. Documentation Index

| Document | Description |
| :--- | :--- |
| [AGENTS.md](file:///AGENTS.md) | Mandatory AI agent operating directives and phase constraints. |
| [docs/APP.md](file:///docs/APP.md) | Product vision, user personas, core feature taxonomy, and UX philosophy. |
| [docs/SPEC.md](file:///docs/SPEC.md) | Functional requirements, NFRs, financial invariants, and acceptance criteria. |
| [docs/ARCHITECTURE.md](file:///docs/ARCHITECTURE.md) | Technical architecture: Streamlit, FastAPI, SQLAlchemy 2.0, and data models. |
| [docs/SECURITY.md](file:///docs/SECURITY.md) | Security baseline: OWASP compliance, RBAC, Argon2id, and audit logging. |
| [docs/TESTING.md](file:///docs/TESTING.md) | Quality assurance framework, testing pyramid, and completion gates. |
| [docs/DEVELOPMENT_RULES.md](file:///docs/DEVELOPMENT_RULES.md) | Engineering standards, Decimal math rules, and Conventional Commits. |
| [docs/PHASES.md](file:///docs/PHASES.md) | Phased development roadmap with deliverables and approval gates. |
| [docs/CHANGELOG.md](file:///docs/CHANGELOG.md) | Chronological version history following Keep a Changelog. |
| [docs/DECISIONS.md](file:///docs/DECISIONS.md) | Architectural Decision Records (ADR-001 through ADR-027). |
| [docs/HANDOFF.md](file:///docs/HANDOFF.md) | Engineering handoff guide, transition protocols, and CLI command cheatsheet. |

---

## 5. Local Setup & Verified Startup Instructions

### Prerequisites
- Python 3.12+ (tested on CPython 3.12.13)
- `uv` (recommended) or standard Python `venv`

### Step 1: Install Dependencies
```bash
# Using uv (fastest):
uv sync

# Or using standard venv:
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -e .
```

### Step 2: Configure Environment & Database
```bash
# Copy example environment configuration
cp .env.example .env

# Verify database migrations are at head revision:
uv run alembic current
# Expected: f6a91c8230b1 (head)
```

### Step 3: Seed Recruiter Portfolio Demo Dataset (Optional)
To immediately explore a realistic portfolio with INR salary accounts, expenses, budgets, savings goals, loans, and investment holdings:
```bash
# Provide password via environment or interactive prompt (or let script auto-generate):
uv run python scripts/seed_demo_recruiter.py
# Target user: demo.recruiter@example.com (Rotatable via --rotate-password)
```

### Step 4: Bootstrap Initial Administrator (Optional)
```bash
# Interactive masked password prompt:
uv run python src/cli/bootstrap_admin.py --username admin --email admin@local.dev

# Or Windows batch launcher:
scripts\bootstrap_admin.bat
```

### Step 5: Launch the Application Services

**Terminal 1 — FastAPI Backend**:
```bash
uv run uvicorn src.api.main:app --host 127.0.0.1 --port 8000
# OpenAPI Interactive Docs: http://127.0.0.1:8000/docs
# Health Endpoint:          http://127.0.0.1:8000/health
```

**Terminal 2 — Streamlit Frontend**:
```bash
# Recommended on Windows (PowerShell launcher handles module path resolution):
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_frontend.ps1

# Or Windows Command Prompt / Batch:
scripts\run_frontend.bat

# Or direct invocation:
uv run streamlit run src/frontend/app.py --server.port 8501 --server.address 127.0.0.1
# Web Application: http://127.0.0.1:8501
```

---

## 6. Verification & Automated Quality Audits

Run the full local quality and security test suite:

```bash
# 1. Full Pytest Suite (231 tests)
uv run pytest

# 2. PEP 8 Linting & Formatting Check
uv run ruff check src tests

# 3. Static Type Checking (Strict Mode across 91 files)
uv run mypy --strict src

# 4. Static Application Security Testing (SAST)
uv run bandit -r src/

# 5. Dependency Vulnerability Audit
uv run pip-audit
```

---

## 7. License & Compliance Notice

This repository is maintained for demonstration, technical evaluation, and portfolio review. Built with strict data privacy, zero unauthorized telemetry, and bank-grade double-entry accounting integrity standards.
