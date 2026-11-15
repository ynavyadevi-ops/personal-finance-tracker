# Personal Finance Tracker — Engineering Standards & Development Rules

> **DOCUMENT**: `docs/DEVELOPMENT_RULES.md`  
> **STATUS**: ACTIVE & MANDATORY  
> **PHASE**: Phase 0 — Foundation and Documentation

---

## 1. Core Engineering Principles

1. **Defensive Programming**: Validate every boundary. Never trust input from forms, API requests, query parameters, or external files.
2. **Explicit over Implicit**: Code should be readable, self-documenting, and free from "magic" behaviors.
3. **Immutability & Purity**: Favor pure functions for financial calculations, date manipulation, and state transformations.
4. **Single Responsibility**: Keep components, services, and modules small, focused, and independently testable.

---

## 2. TypeScript & Code Standards

- **Strict Mode**: `tsconfig.json` MUST enforce `"strict": true`, `"noImplicitAny": true`, and `"strictNullChecks": true`.
- **Zero `any` Policy**: The `any` type is strictly forbidden. Use `unknown` with runtime type narrowing or generic type parameters.
- **Explicit Return Types**: All exported functions, service methods, and Server Actions must specify explicit return types.
- **Type Colocation**: Domain schemas and types live in `src/schemas/` or `src/types/`. Avoid ad-hoc inlined type definitions across pages.

---

## 3. Financial Computation Rules

- **Zero Floating-Point Calculations**: Floating-point operations (e.g. `0.1 + 0.2`) produce rounding discrepancies that corrupt financial balances.
- **Minor Units (Cents)**: All database storage and internal domain calculations MUST represent money as integers in minor units (cents):
  - `$10.00` = `1000`
  - `$0.99` = `99`
- **Formatting Utilities**: Convert to user-facing decimal strings (e.g., `Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })`) exclusively at the presentation layer.

---

## 4. Next.js & React Guidelines

- **Server Components First**: Render components on the server by default. Add `'use client'` ONLY when using React hooks (`useState`, `useEffect`, `useForm`), browser APIs, or event listeners.
- **No Secret Leakage**: Never prefix server secrets with `NEXT_PUBLIC_`. Environment variables containing sensitive credentials must only be imported into server-only modules.
- **Server Actions for Mutations**: Handle state updates and forms using Next.js Server Actions with built-in revalidation (`revalidatePath`, `revalidateTag`).
- **Clean Component Hierarchy**:
  - `src/components/ui/`: Atomic, reusable shadcn/ui primitives.
  - `src/components/features/`: Domain-specific components (e.g., `AccountCard`, `TransactionTable`, `BudgetProgressBar`).
  - `src/app/`: Routing, layout, and top-level data fetching.

---

## 5. Styling & Accessibility (a11y)

- **Tailwind CSS**: Use Tailwind classes for all styling. Avoid custom arbitrary CSS files unless defining root theme variables in `globals.css`.
- **shadcn/ui Standards**: Do not rewrite basic UI controls (dialogs, dropdowns, inputs, tooltips) from scratch. Utilize official shadcn/ui components built on Radix UI.
- **Responsive by Default**: Design mobile-first using Tailwind responsive breakpoints (`sm:`, `md:`, `lg:`, `xl:`).
- **Accessibility**:
  - Interactive elements must be keyboard focusable (`Tab`, `Enter`, `Escape`).
  - Maintain color contrast ratios compliant with WCAG 2.1 AA.
  - Always provide meaningful `aria-label` or visually hidden screen reader text on icon-only buttons.

---

## 6. Git Workflow & Version Control

- **Conventional Commits**: Commit messages must adhere to the Conventional Commits specification:
  - `feat: <description>` — New feature
  - `fix: <description>` — Bug fix
  - `docs: <description>` — Documentation update
  - `test: <description>` — Adding or updating tests
  - `refactor: <description>` — Code change that neither fixes a bug nor adds a feature
  - `chore: <description>` — Tooling, dependency, or configuration update
- **Branch Naming**:
  - `feature/<phase-number>-<short-description>` (e.g., `feature/p1-env-setup`)
  - `fix/<issue-description>`
- **Clean Git Status**: No temporary scratch files, build artifacts, or secret files may be staged or committed.

---

## 7. Phase Boundary Invariant & Governance

- **Strict Scope Boundaries**: Developers and AI agents must work strictly within the scope of the active development phase as documented in `docs/PHASES.md`.
- **No Unapproved Forward Work**: Implementing features assigned to future phases without prior written sign-off is a severe governance violation.
- **Documentation Synchronization**: Any architectural modification, schema change, or bug resolution must immediately be accompanied by updates to:
  - `docs/CHANGELOG.md`
  - `docs/DECISIONS.md` (if an architectural decision is made or amended)
  - Applicable technical specification documents.
