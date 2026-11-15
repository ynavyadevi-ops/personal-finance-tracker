# AGENTS.md — Mandatory AI Agent Operating Directives

> **TARGET AGENTS**: OpenAI Codex, GitHub Copilot Workspace, Google Antigravity, Claude Code, and all autonomous or semi-autonomous development agents.
> **SCOPE**: Entire Repository lifecycle for **Personal Finance Tracker (Python + SQL Stack)**.
> **STATUS**: ACTIVE & ENFORCED

---

## 1. Prime Directives

Every AI agent working within this repository MUST strictly abide by the following operational directives. Any deviation constitutes a protocol failure and must be halted immediately.

### Directive 1: Read Project Documentation Before Every Phase
Before reading code, formulating plans, or executing commands for any task or phase:
- Thoroughly read `README.md` and all documents in the `docs/` directory:
  - `docs/APP.md`
  - `docs/SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/SECURITY.md`
  - `docs/TESTING.md`
  - `docs/DEVELOPMENT_RULES.md`
  - `docs/PHASES.md`
  - `docs/CHANGELOG.md`
  - `docs/DECISIONS.md`
  - `docs/HANDOFF.md`
- Do not assume requirements or technical specifications; adhere strictly to the written architecture.

### Directive 2: Respect Phase Boundaries
- Development is strictly partitioned into **Nine Phases** (defined in `docs/PHASES.md`).
- Execute ONLY the tasks assigned to the active phase.
- **NEVER** anticipate, pre-implement, scaffold, or install dependencies for future phases without explicit user instruction.
- Phase 0 is strictly for documentation, inspection, and architectural definition. **No application features may be implemented in Phase 0.**

### Directive 3: Preserve Approved Functionality
- Never refactor, rename, or delete existing working code or tests unless explicitly requested.
- Maintain backwards compatibility across iterations.
- Run regression tests after every change to ensure zero breakage of previously approved features.

### Directive 4: Never Implement Unapproved Features
- Do not add "nice-to-have" features, speculative helper utilities, unvetted third-party libraries, or UI components outside the specifications in `docs/SPEC.md`.
- Adhere strictly to the MVP boundary during early phases.

### Directive 5: Run Tests After Modifications
- Every code modification must be verified:
  - Unit and Integration tests: `pytest`
  - API Integration: `pytest -m integration` (using `httpx.AsyncClient`)
  - Static Type Checking: `mypy --strict src`
  - Code Formatting and Linting: `ruff check .`
- Never submit or mark a task complete if any test or check fails.

### Directive 6: Perform Security & Dependency Audits
- Verify all dependencies using `pip-audit` to ensure zero high/critical vulnerabilities exist.
- Run `bandit -r src/` for Static Application Security Testing (SAST).
- Comply with `docs/SECURITY.md` (OWASP Top 10, Pydantic input validation, SQLAlchemy parameterized queries, secure session handling, zero sensitive data leakage).
- Validate that financial values are protected against float precision errors (using `decimal.Decimal` and `Numeric(18, 2)`).

### Directive 7: Update Documentation
- Any architectural evolution, API change, schema modification, or new feature MUST be documented in:
  - `docs/CHANGELOG.md` (chronological record)
  - `docs/DECISIONS.md` (new or updated ADRs)
  - `docs/HANDOFF.md` (context transition protocol)
  - Relevant domain document (`docs/ARCHITECTURE.md`, `docs/SPEC.md`, etc.)

### Directive 8: Stop at Approval Gates
- At the conclusion of every phase, the agent **MUST STOP**.
- Present a clear Phase Completion Report summarizing:
  1. Tasks completed.
  2. Test results.
  3. Security and audit scan results (`bandit`, `pip-audit`).
  4. Artifacts generated.
  5. Known limitations or assumptions.
- **DO NOT PROCEED** to the next phase until the user provides explicit, unambiguous approval.

---

## 2. Python & SQL Command Execution Guidelines

1. **Sandboxing & Safety**:
   - Run commands inside the default sandbox whenever possible.
   - Never run destructive commands (`rm -rf /`, `git reset --hard` without confirmation).
   - Never suppress type errors (`# type: ignore`) or linter errors (`# noqa`) without documented justification in `docs/DECISIONS.md`.

2. **Package & Environment Management**:
   - Use `uv` or standard Python `venv` for virtual environment isolation.
   - Install only approved packages listed in `docs/ARCHITECTURE.md`.
   - Never install untrusted, unvetted, or unmaintained packages.
   - Run dependency audit commands (`pip-audit`) upon adding or modifying packages.

---

## 3. Communication Protocol

- Keep progress reports concise, structured, and factual.
- Use GitHub Flavored Markdown with clickable links (`file:///...`).
- When encountering ambiguities or architectural trade-offs, pause and ask the user rather than making unverified assumptions.
