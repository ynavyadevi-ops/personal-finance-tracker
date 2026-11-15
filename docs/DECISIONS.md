# Personal Finance Tracker — Architectural Decision Records (ADRs)

> **DOCUMENT**: `docs/DECISIONS.md`  
> **STATUS**: ACTIVE & ENFORCED  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation

---

## Index of Architectural Decisions

- [ADR-001: Full-Stack Framework Selection (Next.js App Router)](#adr-001-full-stack-framework-selection-nextjs-app-router)
- [ADR-002: Dual Database Strategy (SQLite Local, PostgreSQL Production)](#adr-002-dual-database-strategy-sqlite-local-postgresql-production)
- [ADR-003: Monetary Representation Model (Integer Minor Units)](#adr-003-monetary-representation-model-integer-minor-units)
- [ADR-004: UI Component Architecture (Tailwind CSS & shadcn/ui)](#adr-004-ui-component-architecture-tailwind-css--shadcnui)
- [ADR-005: Testing Suite Strategy (Vitest & Playwright)](#adr-005-testing-suite-strategy-vitest--playwright)
- [ADR-006: Schema Validation & Type Invariance (Zod)](#adr-006-schema-validation--type-invariance-zod)
- [ADR-007: Phased Implementation Lifecycle with Approval Gates](#adr-007-phased-implementation-lifecycle-with-approval-gates)

---

## ADR-001: Full-Stack Framework Selection (Next.js App Router)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: The Personal Finance Tracker requires a unified full-stack architecture that supports server-side rendering for optimal performance and SEO/speed, server-side data fetching without exposing internal APIs, and interactive client components for financial forms and charts.
- **Decision**: Adopt **Next.js 15+ with the App Router** and React 19.
- **Rationale**:
  - React Server Components (RSC) fetch data directly from domain services without client network waterfalls.
  - Server Actions provide a seamless, type-safe mutation model eliminating boilerplate REST controller layers.
  - Built-in optimizations for bundling, streaming, dynamic imports, and security headers.
- **Consequences**:
  - Developers must understand the distinction between Server and Client components.
  - Third-party chart components (Recharts) require `'use client'` wrappers.

---

## ADR-002: Dual Database Strategy (SQLite Local, PostgreSQL Production)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: For local MVP development, requiring users to install, configure, and maintain a local PostgreSQL or Docker daemon creates onboarding friction. However, enterprise production deployments require high concurrency, row-level security, connection pooling, and multi-tenant scaling.
- **Decision**: Use **Prisma ORM** with a dual-database approach:
  - **Local Development / MVP**: Embedded SQLite (`file:./dev.db`).
  - **Production Deployment**: PostgreSQL 16+ via managed cloud services (Neon, Supabase, AWS RDS).
- **Rationale**:
  - Prisma abstracts SQL dialect differences, allowing identical schema models to target both databases.
  - SQLite requires zero configuration, zero cloud dependencies, and zero background services during local testing.
  - PostgreSQL provides connection pooling (PgBouncer), concurrent write scalability, and robust ACID isolation.
- **Consequences**:
  - Database schema must avoid SQLite-incompatible features (such as database-level enum types in SQLite, simulated via Prisma, or database-specific JSON functions).
  - Migration script (`scripts/migrate-sqlite-to-pg.ts`) must be maintained to verify data fidelity during migration.

---

## ADR-003: Monetary Representation Model (Integer Minor Units)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: IEEE 754 floating-point numbers inherently produce rounding inaccuracies (e.g., `0.1 + 0.2 = 0.30000000000000004`). In a financial application, floating-point drift can result in corrupted balances, failing ledger reconciliations, and loss of user trust.
- **Decision**: Store and compute all monetary values as **integers in minor currency units (cents)**.
  - Example: `$12.50` is stored and calculated as `1250`.
- **Rationale**:
  - Exact arithmetic: integer addition and subtraction are 100% exact and free from floating-point distortion.
  - High performance: integer math is natively supported and lightning-fast across all CPU architectures and database engines.
  - Universal database compatibility: integer columns behave identically in SQLite, PostgreSQL, and MySQL.
- **Consequences**:
  - User-facing values must be converted to cents on input and formatted to currency strings on output.
  - Dedicated formatting utility functions (`centsToDollars`, `dollarsToCents`) must be central and thoroughly unit-tested.

---

## ADR-004: UI Component Architecture (Tailwind CSS & shadcn/ui)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: We need a modern, visually appealing, accessible, and easily customizable design system without the overhead and bundle weight of heavy component libraries (like MUI or Ant Design).
- **Decision**: Adopt **Tailwind CSS** combined with **shadcn/ui** (built on top of Radix UI primitives).
- **Rationale**:
  - Zero runtime style injection: Tailwind generates static CSS, maximizing runtime performance.
  - Code ownership: shadcn/ui copies accessible, unstyled primitives into the codebase (`src/components/ui/`), giving full control over markup and styling.
  - Built-in accessibility: Radix UI handles keyboard navigation, focus management, and ARIA attributes out of the box.
- **Consequences**:
  - Developers must follow consistent utility class conventions.

---

## ADR-005: Testing Suite Strategy (Vitest & Playwright)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Financial calculations, ledger invariants, and user workflows require comprehensive automated testing with fast feedback loops for developers and reliable end-to-end verification.
- **Decision**: Deploy **Vitest** for unit and integration testing, and **Playwright** for end-to-end (E2E) browser testing.
- **Rationale**:
  - Vitest provides instant HMR, native TypeScript/ESM execution, and a Jest-compatible API without transform overhead.
  - Playwright enables cross-browser automation (Chromium, WebKit, Firefox) with built-in tracing, video capture, and robust auto-wait assertions.
- **Consequences**:
  - Developers run unit tests during active coding (`npm run test`) and E2E tests before releases or phase gates (`npm run test:e2e`).

---

## ADR-006: Schema Validation & Type Invariance (Zod)

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Runtime data entering from external boundaries (HTTP requests, URL search params, form submissions, CSV uploads) must be strictly validated to prevent malformed data or security vulnerabilities.
- **Decision**: Adopt **Zod** as the single source of truth for runtime validation and static TypeScript type inference.
- **Rationale**:
  - Seamless integration with `react-hook-form` via `@hookform/resolvers/zod`.
  - Type inference (`z.infer<typeof schema>`) eliminates duplicate interface definitions.
  - Strict parsing strips unrecognised attributes, mitigating parameter injection attacks.
- **Consequences**:
  - All form and API inputs must declare corresponding Zod schemas in `src/schemas/`.

---

## ADR-007: Phased Implementation Lifecycle with Approval Gates

- **Date**: 2026-11-15
- **Status**: **ACCEPTED**
- **Context**: Complex full-stack applications often suffer from scope creep, architectural drift, and half-implemented features when development lacks strict boundaries.
- **Decision**: Establish an immutable **Nine-Phase Lifecycle** with mandatory stop-and-review approval gates at the conclusion of each phase.
- **Rationale**:
  - Enforces systematic, verifiable progress where each phase is tested and stable before the next commences.
  - Prevents premature application coding before infrastructure and architecture are sound.
  - Ensures human-in-the-loop oversight and governance.
- **Consequences**:
  - Work must halt at the end of each phase until explicit user approval is granted.
