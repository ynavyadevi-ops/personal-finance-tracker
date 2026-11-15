# Personal Finance Tracker (Python + SQL)

A production-oriented, secure, and modern full-stack financial management web application built entirely on **Python and SQL**. It provides real-time personal net worth tracking, transaction ledger management, category budgeting, and interactive financial analytics.

---

## 1. Project Overview

- **Project Name**: Personal Finance Tracker
- **Architecture**: Decoupled full-stack architecture:
  - **Frontend UI**: [Streamlit](https://streamlit.io/) reactive web dashboard with interactive [Plotly](https://plotly.com/) visual analytics.
  - **Backend API**: [FastAPI](https://fastapi.tiangolo.com/) high-performance asynchronous REST service.
  - **Database Layer**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) ORM + [Alembic](https://alembic.sqlalchemy.org/) schema migrations.
  - **Data Processing**: [Pandas](https://pandas.pydata.org/) for transaction aggregations, rollups, and statement imports.
  - **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/) for strict runtime type enforcement.
- **Data Persistence**:
  - **Local Development / MVP**: Embedded zero-configuration SQLite (`data/finance.db`).
  - **Production Environment**: High-concurrency, ACID-compliant PostgreSQL 16+.
- **Security & Quality Baseline**:
  - Static Application Security Testing via [Bandit](https://github.com/PyCQA/bandit).
  - Dependency vulnerability auditing via [pip-audit](https://github.com/pypa/pip-audit).
  - Automated testing via [Pytest](https://docs.pytest.org/) and asynchronous HTTP testing via [HTTPX](https://www.python-httpx.org/).
  - Exact financial arithmetic with Python's native `decimal.Decimal` and database `Numeric(18, 2)` (zero floating-point inaccuracies).
- **Current Phase**: **Phase 0 — Project Foundation and Documentation (Completed / Awaiting User Approval)**.

---

## 2. Technology Stack & Verified Stable Releases

| Component | Technology | Target Version | Verified Role / Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `3.12.x` (or `>=3.11, <3.13`) | Core programming language; robust wheel support |
| **Backend Framework** | FastAPI | `^0.115.0` (or `^0.162.0`) | High-performance asynchronous REST API backend |
| **ASGI Server** | Uvicorn | `^0.34.0` | Production-grade ASGI server implementation |
| **Frontend Dashboard** | Streamlit | `^1.40.0` (or `^1.67.0`) | Reactive, low-latency UI & data presentation |
| **Database ORM** | SQLAlchemy | `^2.0.38` (2.0 series) | Type-safe declarative database access & session management |
| **Schema Migrations** | Alembic | `^1.14.0` | Revision-controlled schema migrations for SQLite & PostgreSQL |
| **Data Validation** | Pydantic | `^2.10.0` (v2 series) | Strict schema validation, serialization, and typing |
| **Settings Management**| Pydantic-Settings | `^2.7.0` | Environment configuration loading from `.env` |
| **Data Analysis** | Pandas | `^2.2.0` (or `^3.1.0`) | Statement parsing, aggregation, and time-series rollups |
| **Visualization** | Plotly | `^5.24.0` (or `^6.0.0`) | Dynamic charts (cash flow, net worth, category breakdowns) |
| **Local Database** | SQLite (`aiosqlite`) | `3.x` | Zero-configuration local development file database |
| **Production DB** | PostgreSQL (`asyncpg` / `psycopg`) | `16+` | Scalable relational database for cloud deployment |
| **Automated Testing** | Pytest + pytest-asyncio | `^8.3.0` | Unit and integration test execution |
| **HTTP Client Testing**| HTTPX | `^0.28.0` | Async HTTP client for testing FastAPI endpoints |
| **Security SAST** | Bandit | `^1.8.0` | Static security scanner for Python source code |
| **Dependency Audit** | pip-audit | `^2.8.0` | Supply-chain CVE scanner against PyPI database |
| **Formatting / Lint** | Ruff | `^0.9.0` | Lightning-fast Python linter and formatter (PEP 8) |

---

## 3. Documentation Index

The repository governance and technical designs are thoroughly documented across 10 specialized records:

| Document | Description |
| :--- | :--- |
| [AGENTS.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/AGENTS.md) | Mandatory rules, phase constraints, and operating instructions for AI agents. |
| [docs/APP.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/APP.md) | Product vision, target user personas, core feature taxonomy, and UX philosophy. |
| [docs/SPEC.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/SPEC.md) | 20 Functional Requirements, 10 NFRs, business rules, financial invariants, and acceptance criteria. |
| [docs/ARCHITECTURE.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/ARCHITECTURE.md) | Technical architecture: Streamlit, FastAPI, SQLAlchemy 2.0, Alembic, and PostgreSQL migration. |
| [docs/SECURITY.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/SECURITY.md) | Security baseline: OWASP compliance, SQL injection prevention, Bandit, pip-audit, and secret isolation. |
| [docs/TESTING.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/TESTING.md) | Quality assurance framework, testing pyramid, Pytest suites, HTTPX tests, and completion gates. |
| [docs/DEVELOPMENT_RULES.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/DEVELOPMENT_RULES.md) | Python engineering guidelines, type hinting, Decimal math rules, and Conventional Commits. |
| [docs/PHASES.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/PHASES.md) | Nine-phase development roadmap with deliverables, tests, security audits, and approval gates. |
| [docs/CHANGELOG.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/CHANGELOG.md) | Version history following Keep a Changelog standard. |
| [docs/DECISIONS.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/DECISIONS.md) | Architectural Decision Records (ADRs) explaining technical trade-offs. |
| [docs/HANDOFF.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/HANDOFF.md) | Comprehensive engineering handoff guide, transition protocols, and CLI command cheatsheet. |

---

## 4. Nine-Phase Development Lifecycle

Progress is strictly gated across nine sequential stages:
1. **Phase 0: Project Foundation and Documentation** *(Current Phase — Complete / Awaiting Approval)*
2. **Phase 1: Environment Setup, Python Tooling & Scaffolding**
3. **Phase 2: Database Modeling, SQLAlchemy & Alembic Migrations**
4. **Phase 3: Core Domain Services, Pydantic Schemas & Financial Arithmetic**
5. **Phase 4: FastAPI REST API, Endpoints & Authentication**
6. **Phase 5: Streamlit UI Framework, Layout & Reusable Widgets**
7. **Phase 6: Streamlit Application Pages (Accounts, Transactions, Budgets)**
8. **Phase 7: Analytics, Plotly Visualizations & Pandas Data Processing**
9. **Phase 8: Comprehensive Testing (Pytest/HTTPX), Security Audits (Bandit, pip-audit) & Performance**
10. **Phase 9: Production Readiness, Dockerization, PostgreSQL Migration Verification & Deployment**

---

## 5. Getting Started (For Phase 1+)

*Note: Application dependencies and code will be initialized in Phase 1 following explicit user approval.*

```bash
# 1. Create a Python virtual environment (using uv or standard python)
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies (Phase 1)
uv pip install -r requirements.txt

# 3. Apply database migrations (Phase 2)
alembic upgrade head

# 4. Start the FastAPI backend service (Phase 4+)
uvicorn src.api.main:app --reload --port 8000

# 5. Launch the Streamlit web dashboard (Phase 5+)
streamlit run src/frontend/app.py --server.port 8501
```

---

## 6. License & Compliance

Proprietary and confidential. Built with strict data privacy, zero unauthorized telemetry, and bank-grade data integrity standards.
