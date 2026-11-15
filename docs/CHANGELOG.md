# Changelog

All notable changes to the **Personal Finance Tracker (Python + SQL)** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Phase 1
- Python 3.12 virtual environment setup and dependency locking via `pyproject.toml`.
- Configuration of Ruff (linting/formatting), Mypy (strict typing), and Pytest test runner.
- Environment settings management via Pydantic `BaseSettings`.

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
