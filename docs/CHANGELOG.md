# Changelog

All notable changes to the **Personal Finance Tracker** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned for Phase 1
- Project initialization with Next.js App Router, TypeScript strict mode, and Tailwind CSS.
- Tooling setup: ESLint, Prettier, Vitest, and Playwright.
- Runtime environment variable validation schema.

---

## [0.1.0] - 2026-11-15 (Phase 0: Foundation & Documentation)

### Added
- **Repository Initialization**: Initialized Git version control and established root `.gitignore`.
- **AI Agent Directives (`AGENTS.md`)**: Codified mandatory operational rules for AI assistants (reading documentation, respecting phase boundaries, running test suites, zero unapproved features, stopping at approval gates).
- **Product Vision (`docs/APP.md`)**: Defined application purpose, user personas (Alex, Jordan, Morgan), core value pillars, and UI/UX design ethos.
- **System Specifications (`docs/SPEC.md`)**: Documented 20 functional requirements, 10 non-functional requirements, business rules, financial invariants, and Given-When-Then acceptance criteria.
- **Technical Architecture (`docs/ARCHITECTURE.md`)**:
  - Detailed multi-tier architecture spanning Next.js App Router, React Server Components, and Prisma ORM.
  - Specified database schema for `User`, `Account`, `Category`, `Transaction`, `Budget`, `RecurringRule`, and `AuditLog`.
  - Formulated API design guidelines, centralized error envelopes, and structured logging.
  - Designed dual-database strategy (SQLite for local development, PostgreSQL for production).
- **Security Baseline (`docs/SECURITY.md`)**:
  - Mapped OWASP Top 10 mitigations to application architecture.
  - Enforced integer minor-unit financial arithmetic to eliminate floating-point drift.
  - Established dependency supply-chain approval criteria, `npm audit`, and OSV-Scanner integration rules.
- **Quality Assurance Strategy (`docs/TESTING.md`)**:
  - Established testing pyramid: 70% Unit (Vitest), 20% Integration, 10% E2E (Playwright).
  - Defined database migration and security testing procedures.
  - Established phase completion criteria gates.
- **Engineering Standards (`docs/DEVELOPMENT_RULES.md`)**:
  - Codified strict TypeScript rules (`strict: true`, zero `any`), clean component separation, and Conventional Commits.
- **Development Roadmap (`docs/PHASES.md`)**: Detailed 9 development phases with objectives, dependencies, deliverables, and acceptance sign-offs.
- **Architectural Decision Records (`docs/DECISIONS.md`)**: Authored ADR-001 through ADR-007 covering framework, database, precision model, design system, testing tools, validation, and phased delivery.
- **Project Readme (`README.md`)**: Authored project landing document with tech stack table, documentation directory, and quickstart overview.
