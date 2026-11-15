# Personal Finance Tracker — Engineering Handoff & Operating Guide

> **DOCUMENT**: `docs/HANDOFF.md`  
> **STATUS**: ACTIVE & ENFORCED  
> **STACK**: Python 3.12 (FastAPI, Streamlit, SQLAlchemy 2.0, Alembic, Pydantic v2, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation (COMPLETED)

---

## 1. Project Context & Current Status

This repository houses the **Personal Finance Tracker**, a production-oriented, secure, full-stack personal finance application implemented in **Python + SQL**.

### Current State
- **Phase 0 (Project Foundation and Documentation)** is **COMPLETE**.
- The repository has been initialized with Git version control, `.gitignore`, and a comprehensive 12-document architecture and governance suite.
- **ZERO application code or dependencies have been implemented yet.**
- **Work is halted at the Phase 0 Completion Gate awaiting explicit user approval to proceed to Phase 1.**

---

## 2. Instructions for Successor Developers & AI Agents

When resuming or continuing work on this repository:

1. **Read Before Executing**:
   Before executing commands or editing code, read [AGENTS.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/AGENTS.md) and all documents in the `docs/` folder.
2. **Respect the Active Phase**:
   Inspect [docs/PHASES.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/PHASES.md). Execute **ONLY** the tasks specified for the currently authorized phase. Never pre-implement future phase tasks.
3. **Preserve Decimal Invariants**:
   Never use `float` for currency. Always use Python's `decimal.Decimal` and SQLAlchemy `Numeric(18, 2)`.
4. **Architectural Separation**:
   Streamlit frontend components (`src/frontend/`) **MUST NOT** import SQLAlchemy models or query the database directly. They must interact with data strictly through `src/frontend/api_client.py` calling the FastAPI backend.
5. **Enforce Approval Gates**:
   At the end of every phase, run the required automated test suites and security audits (`bandit`, `pip-audit`), generate a comprehensive Phase Completion Report, and **STOP**. Do not proceed to the next phase without explicit user authorization.

---

## 3. Developer & Environment Command Cheatsheet

Once Phase 1 is authorized, the following standard commands govern development:

### Environment Setup & Package Management (Phase 1+)
```bash
# Create virtual environment (using uv or venv)
uv venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on Unix/macOS:
source .venv/bin/activate

# Install locked dependencies
uv pip install -r requirements.txt
```

### Code Quality, Linting & Type Checking
```bash
# Format code using Ruff
ruff format .

# Lint and check code using Ruff
ruff check . --fix

# Static type check using Mypy in strict mode
mypy --strict src
```

### Database & Migrations (Phase 2+)
```bash
# Generate a new Alembic migration revision
alembic revision --autogenerate -m "describe_migration"

# Apply migrations to database
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Populate database with seed data
python -m src.db.seed
```

### Running the Application (Phase 4 & 5+)
```bash
# Terminal 1: Launch FastAPI backend server (Port 8000)
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Launch Streamlit web dashboard (Port 8501)
streamlit run src/frontend/app.py --server.port 8501
```

### Automated Testing (Phase 3+)
```bash
# Run all Pytest suites
pytest

# Run with verbose output and coverage
pytest -v --cov=src --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Security & Supply-Chain Audits
```bash
# Static Application Security Testing (Bandit)
bandit -r src/ -ll -ii

# Dependency Vulnerability Audit (pip-audit)
pip-audit
```

---

## 4. Phase 0 Verification Checklist

Before accepting Phase 0 completion, verify the following baseline criteria:

- [x] Repository initialized with Git version control.
- [x] Python-centric `.gitignore` in place (ignoring `.venv`, `__pycache__`, `*.db`, `.env*`).
- [x] `AGENTS.md` established with mandatory directives.
- [x] `README.md` updated with Python + SQL stack details and verified versions.
- [x] `docs/APP.md` authored with product vision, personas, and feature taxonomy.
- [x] `docs/SPEC.md` authored with 20 FRs, 10 NFRs, workflows, and acceptance criteria.
- [x] `docs/ARCHITECTURE.md` authored with Streamlit, FastAPI, SQLAlchemy 2.0, and Postgres migration details.
- [x] `docs/SECURITY.md` authored with OWASP mitigations, Bandit SAST, and pip-audit policies.
- [x] `docs/TESTING.md` authored with Pytest, HTTPX, and testing pyramid.
- [x] `docs/DEVELOPMENT_RULES.md` authored with PEP 8, Decimal math rules, and layer boundaries.
- [x] `docs/PHASES.md` authored with detailed scope, deliverables, tests, and gates for all 9 phases.
- [x] `docs/CHANGELOG.md` updated with Phase 0 initial release entry.
- [x] `docs/DECISIONS.md` authored with ADR-001 through ADR-010.
- [x] `docs/HANDOFF.md` authored with operational instructions and cheatsheet.
- [x] **Zero application code or dependencies installed.**
- [x] Clean Git working tree with all documentation committed.

---

## 5. Next Steps (Upon Phase 1 Approval)

When the user grants explicit approval to proceed to Phase 1:
1. Initialize `pyproject.toml` with the pinned, verified dependencies.
2. Create and activate a Python 3.12 virtual environment (`uv venv .venv`).
3. Configure `ruff.toml`, `mypy.ini`, and `pytest.ini`.
4. Create the core directory structure (`src/`, `tests/`).
5. Establish `.env.example` and Pydantic `BaseSettings` loader.
6. Verify empty Pytest discovery, Bandit scan, and `pip-audit` scan.
7. Halt and deliver Phase 1 completion report.
