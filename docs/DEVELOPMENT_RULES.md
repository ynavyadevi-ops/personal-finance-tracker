# Personal Finance Tracker — Engineering Standards & Development Rules

> **DOCUMENT**: `docs/DEVELOPMENT_RULES.md`  
> **STATUS**: ACTIVE & MANDATORY  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **PHASE**: Phase 0 — Foundation and Documentation

---

## 1. Core Engineering Principles

1. **Explicit Architecture**: Adhere strictly to the four-tier separation:
   $$\text{Streamlit UI} \longrightarrow \text{FastAPI REST Endpoints} \longrightarrow \text{Domain Services} \longrightarrow \text{SQLAlchemy Repositories}$$
2. **Defensive Validation**: Validate every external input using Pydantic schemas before business logic execution.
3. **Immutability & Decimal Safety**: Never use `float` for currency. Always use Python `decimal.Decimal`.
4. **Single Responsibility**: Each module, class, and service must own exactly one domain responsibility.

---

## 2. Python Code Standards & Typing

- **PEP 8 Compliance**: Code must adhere strictly to PEP 8 standards, formatted and linted using **Ruff**:
  ```bash
  ruff format .
  ruff check . --fix
  ```
- **Strict Static Typing**: All code in `src/` must be strictly typed and pass **Mypy** verification:
  ```bash
  mypy --strict src
  ```
  - Prohibit `Any` unless wrapping untyped third-party libraries.
  - Explicit return types are required on all functions and methods.
- **Python 3.12 Constructs**: Use modern Python type annotations (e.g., `list[str]`, `dict[str, Any]`, `X | Y` union syntax).

---

## 3. Financial Calculation Rules

- **Zero Floating-Point Calculations**: Floating-point types (`float`) suffer from binary representation inaccuracies (`0.1 + 0.2 != 0.3`).
- **Mandatory `decimal.Decimal`**:
  - All currency calculations must use `Decimal`:
    ```python
    from decimal import Decimal, ROUND_HALF_EVEN

    amount = Decimal("10.50")
    ```
  - Database mapping uses `Numeric(18, 2)`.
  - Presentation formatting uses `f"${amount:,.2f}"` or `locale` formatting.

---

## 4. Architectural Layer Boundaries

1. **Streamlit UI Layer (`src/frontend/`)**:
   - Streamlit pages **MUST NOT** import SQLAlchemy models or directly connect to the database.
   - All data fetching and mutation must occur via `src/frontend/api_client.py` calling the FastAPI HTTP API.
2. **FastAPI Route Layer (`src/api/routers/`)**:
   - Routers handle HTTP concerns: status codes, cookie/header extraction, and Pydantic serialization.
   - Routers **MUST NOT** contain raw SQL or business logic; they must delegate immediately to Domain Services.
3. **Domain Services Layer (`src/services/`)**:
   - Services implement business rules, financial invariants, balance conservation, and audit logging.
   - Services interact with the database exclusively through Repositories.
4. **Repository Layer (`src/repositories/`)**:
   - Repositories encapsulate SQLAlchemy queries, sessions, and transaction boundaries.

---

## 5. Security & Git Hygiene

- **Static Security Audits**: All code changes must pass **Bandit** SAST scans:
  ```bash
  bandit -r src/ -ll -ii
  ```
- **Dependency Auditing**: Verify zero known vulnerabilities before committing:
  ```bash
  pip-audit
  ```
- **Conventional Commits**: Commit messages must adhere to the standard:
  - `feat: <description>` — New feature
  - `fix: <description>` — Bug fix
  - `docs: <description>` — Documentation update
  - `test: <description>` — Adding or updating tests
  - `refactor: <description>` — Code reorganization without functional changes
  - `chore: <description>` — Tooling, dependency, or configuration updates
- **Branch Naming**:
  - `feature/<phase-number>-<description>` (e.g., `feature/p1-tooling-scaffold`)
  - `fix/<issue-description>`

---

## 6. Phase Boundary Invariant & Governance

- **Strict Scope Boundaries**: Developers and AI agents must work strictly within the scope of the active development phase as documented in `docs/PHASES.md`.
- **No Unapproved Forward Work**: Implementing features assigned to future phases without prior written sign-off is a severe governance violation.
- **Documentation Synchronization**: Any architectural modification, schema change, or bug resolution must immediately be accompanied by updates to:
  - `docs/CHANGELOG.md`
  - `docs/DECISIONS.md`
  - `docs/HANDOFF.md`
