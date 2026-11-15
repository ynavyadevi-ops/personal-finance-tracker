# Personal Finance Tracker — Nine-Phase Development Roadmap

> **DOCUMENT**: `docs/PHASES.md`  
> **STATUS**: APPROVED BASELINE  
> **CURRENT ACTIVE PHASE**: Phase 0 — Foundation and Documentation

---

## Roadmap Overview

Development proceeds through nine sequential phases. Each phase establishes a rigorous foundation for subsequent work. Advancing between phases requires fulfilling all phase deliverables and obtaining explicit human sign-off.

```
[ Phase 0: Foundation & Docs ] ──▶ [ Phase 1: Tooling & Scaffolding ] ──▶ [ Phase 2: Database & Prisma ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 3: Domain & Services ] ──▶ [ Phase 4: Server Actions & API ]  ──▶ [ Phase 5: Design System ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 6: Feature Pages ]     ──▶ [ Phase 7: Analytics & Export ]    ──▶ [ Phase 8: Testing & Audits ]
                                                                                   │
┌──────────────────────────────────────────────────────────────────────────────────┘
▼
[ Phase 9: Production Readiness & PostgreSQL Migration ] ──▶ [ RELEASE ]
```

---

## Phase 0: Project Foundation and Documentation (CURRENT)

- **Objective**: Inspect environment, establish system architecture, enforce security baseline, initialize test strategy, author complete documentation suite, and define AI agent operational constraints.
- **Dependencies**: None.
- **In-Scope**:
  - Full repository inspection and Git status verification.
  - Creation of `AGENTS.md`, `README.md`, `.gitignore`.
  - Authoring `docs/APP.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/TESTING.md`, `docs/DEVELOPMENT_RULES.md`, `docs/PHASES.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`.
  - Selection and verification of compatible tech stack versions.
- **Forbidden**: Writing application code, installing application dependencies, scaffolding folders ahead of time.
- **Deliverables**: All 11 markdown documentation files complete, consistent, and committed.
- **Acceptance Gate**: Explicit user sign-off on Phase 0 completion report.

---

## Phase 1: Environment Setup, Tooling & Core Project Scaffolding

- **Objective**: Initialize Next.js project with TypeScript, configure ESLint, Prettier, Tailwind CSS, Vitest, and Playwright.
- **Dependencies**: Phase 0 approval.
- **In-Scope**:
  - `package.json` initialization with approved dependencies and pinned versions.
  - Next.js App Router configuration (`next.config.js`).
  - TypeScript configuration (`tsconfig.json`) with strict flags.
  - Tailwind CSS and PostCSS configuration.
  - Vitest test runner setup (`vitest.config.ts`).
  - Playwright test runner configuration (`playwright.config.ts`).
  - Setup `.env.example` and validated `src/lib/env.ts`.
- **Forbidden**: Implementing application features, writing database schemas.
- **Deliverables**: Clean `npm run build`, `npm run typecheck`, and `npm run test` on empty scaffold.
- **Acceptance Gate**: Passing build and test runs; zero dependency security warnings (`npm audit`).

---

## Phase 2: Database Modeling, Prisma Schema & Migrations

- **Objective**: Configure Prisma ORM with SQLite, create full schema modeling, generate migrations, and implement database seed script.
- **Dependencies**: Phase 1 approval.
- **In-Scope**:
  - `prisma/schema.prisma` modeling `User`, `Account`, `Category`, `Transaction`, `Budget`, `RecurringRule`, `AuditLog`.
  - SQLite database migration (`npx prisma migrate dev`).
  - Prisma client singleton setup (`src/lib/db.ts`).
  - Database seed script (`prisma/seed.ts`) populating default categories, test user, and initial demo accounts.
- **Forbidden**: Writing frontend pages or UI components.
- **Deliverables**: Applied migrations, valid SQLite database file, successful seed execution, type-safe Prisma client.
- **Acceptance Gate**: Successful migration replay, verified relations and constraints.

---

## Phase 3: Core Domain Services, Validation Schemas & Business Logic

- **Objective**: Implement pure TypeScript domain business logic, financial arithmetic utilities, and Zod validation schemas.
- **Dependencies**: Phase 2 approval.
- **In-Scope**:
  - Financial utility functions (`centsToDollars`, `dollarsToCents`, rounding safeguards).
  - Zod schemas: `account.schema.ts`, `transaction.schema.ts`, `budget.schema.ts`.
  - Domain services:
    - `AccountService`: balance calculations, account lifecycle.
    - `TransactionService`: atomic transfers, categorization, transaction filtering.
    - `BudgetService`: monthly limits, threshold alert computation.
  - Comprehensive unit test suite for services and arithmetic with 90%+ branch coverage.
- **Forbidden**: Building UI pages or HTTP route endpoints.
- **Deliverables**: Fully tested service layer with passing Vitest unit tests.
- **Acceptance Gate**: 100% passing unit tests, zero floating-point arithmetic errors.

---

## Phase 4: Backend API Routes & Server Actions

- **Objective**: Expose domain services via Next.js Server Actions and Route Handlers with error envelopes and audit logging.
- **Dependencies**: Phase 3 approval.
- **In-Scope**:
  - Server Actions for Account, Transaction, and Budget mutations.
  - Next.js Route Handlers for CSV export stream and bulk import (`/api/transactions/export`, `/api/transactions/import`).
  - Standardized JSON response envelope (`ApiResponse<T>`).
  - Global error handling and logging wrapper.
  - Integration tests for Server Actions using test database.
- **Forbidden**: Frontend page construction.
- **Deliverables**: Working Server Actions, passing integration tests.
- **Acceptance Gate**: Integration tests verify happy paths and error handling (400, 404, 422).

---

## Phase 5: UI Design System & Component Library

- **Objective**: Establish shadcn/ui component library, theme tokens, layout shell, and navigation.
- **Dependencies**: Phase 4 approval.
- **In-Scope**:
  - shadcn/ui components (`Button`, `Card`, `Dialog`, `DropdownMenu`, `Input`, `Select`, `Table`, `Tabs`, `Toast`).
  - App shell layout (`Sidebar`, `Header`, `ThemeToggle`, `MobileNav`).
  - Responsive design tokens and dark/light mode themes.
  - Accessible form components with React Hook Form & Zod error integration.
- **Forbidden**: Deep feature logic or backend modifications.
- **Deliverables**: Reusable UI component library rendered in isolation or styleguide page.
- **Acceptance Gate**: Accessibility audit (WCAG 2.1 AA), responsive across mobile/tablet/desktop.

---

## Phase 6: Application Pages & User Features

- **Objective**: Construct user-facing application screens connecting UI components to Server Actions.
- **Dependencies**: Phase 5 approval.
- **In-Scope**:
  - Dashboard overview (`/dashboard`): balance summary cards, recent transactions, quick actions.
  - Accounts page (`/accounts`): list accounts, create/edit account modal, archive toggle.
  - Transactions page (`/transactions`): searchable, filterable data table, transaction creation modal, transfer dialog.
  - Budgets page (`/budgets`): category budget cards, progress bars, threshold alerts, budget editing.
- **Forbidden**: Complex analytics charts or data export (reserved for Phase 7).
- **Deliverables**: Fully operational core application workflows.
- **Acceptance Gate**: Playwright E2E tests passing for account, transaction, and budget CRUD journeys.

---

## Phase 7: Analytics, Visualizations & Data Export

- **Objective**: Implement Recharts data visualizations, cash flow trends, net worth tracking, and CSV/JSON import/export.
- **Dependencies**: Phase 6 approval.
- **In-Scope**:
  - Recharts components:
    - Category spending distribution (Donut / Pie chart).
    - Monthly Income vs. Expense (Grouped Bar chart).
    - Net Worth historical trajectory (Area / Line chart).
  - Reports page (`/reports`) with custom date-range filters.
  - CSV export stream generator (RFC 4180).
  - Bank CSV import wizard: file upload, column mapping preview, deduplication, batch insert.
- **Deliverables**: Interactive analytics dashboards and verified data portability tools.
- **Acceptance Gate**: Accurate visual renderings with zero console errors; valid CSV export/import round-trip.

---

## Phase 8: Comprehensive Testing, Security Audits & Performance Optimization

- **Objective**: Execute end-to-end regression testing, conduct security audits, optimize database queries, and verify bundle performance.
- **Dependencies**: Phase 7 approval.
- **In-Scope**:
  - Full Playwright E2E suite covering all user workflows across browsers.
  - Security audit: `npm audit`, OSV-Scanner, OWASP checklist verification.
  - Boundary stress testing: negative amounts, large numbers, deep pagination.
  - Bundle size optimization (dynamic imports for Recharts).
  - Accessibility and Lighthouse performance audits (Performance >90, Accessibility >95).
- **Deliverables**: QA test execution report, zero open security vulnerabilities.
- **Acceptance Gate**: All unit, integration, and E2E tests passing in CI; clean security scan.

---

## Phase 9: Production Readiness, PostgreSQL Migration Verification & Deployment

- **Objective**: Validate PostgreSQL schema compatibility, verify migration pipeline, configure production environment, and finalize documentation.
- **Dependencies**: Phase 8 approval.
- **In-Scope**:
  - Dual database verification: run migrations and test suite against PostgreSQL instance.
  - Verification of data migration script (`scripts/migrate-sqlite-to-pg.ts`).
  - Production build configuration, security headers, and connection pooling settings.
  - Deployment instructions (Vercel, Docker, AWS/Render).
  - Final documentation review and project handoff.
- **Deliverables**: Production-ready code, verified PostgreSQL migration path, deployment artifacts.
- **Acceptance Gate**: Successful test execution against PostgreSQL; final production sign-off.
