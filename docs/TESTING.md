# Personal Finance Tracker — Quality Assurance & Testing Strategy

> **DOCUMENT**: `docs/TESTING.md`  
> **STATUS**: APPROVED BASELINE  
> **PHASE**: Phase 0 — Foundation and Documentation

---

## 1. Quality Assurance Philosophy & Testing Pyramid

Financial applications require zero tolerance for calculation bugs, data corruption, or unhandled exceptions. To balance thoroughness with execution velocity, we adhere to the **Testing Pyramid**:

```
           / \
          /   \
         / E2E \       10% (Playwright) — Critical user workflows
        /───────\
       / Integr. \     20% (Vitest + Testing Library) — Server actions & components
      /───────────\
     /    Unit     \   70% (Vitest) — Pure domain logic, schemas & arithmetic
    /───────────────\
```

- **Target Coverage**: Minimum 85% branch coverage on Domain Services and financial calculation engines; 100% schema validation coverage on Zod schemas.

---

## 2. Testing Framework Architecture

### Vitest (Unit & Integration)
- **Tool**: `vitest` with `@testing-library/react` and `@testing-library/jest-dom`.
- **Purpose**: Fast in-memory execution, ESM native, compatible with Next.js and Vite transforms.
- **Scope**:
  - Financial calculations (cents conversions, balance updates, rollover calculations).
  - Domain service business logic (`AccountService`, `TransactionService`, `BudgetService`).
  - Zod validation schemas (boundary conditions, malformed input rejection).
  - Server Action handlers and error transformation.

### Playwright (End-to-End)
- **Tool**: `@playwright/test`.
- **Purpose**: Multi-browser automated regression testing against real Chromium, Firefox, and WebKit rendering engines.
- **Scope**:
  - Critical path: User creates account $\to$ logs transactions $\to$ views dashboard balance $\to$ monitors budget consumption $\to$ exports CSV.
  - Form validation error presentation and modal dialog interactions.
  - Theme switching and responsive layout verification.

---

## 3. Test Suites & Categorization

### 1. Unit Testing
- **Location**: `src/**/*.test.ts`
- **Focus**: Pure functions with zero side-effects.
- **Key Test Cases**:
  - `centsToDollars(1050)` returns `"$10.50"`.
  - `dollarsToCents("10.50")` returns `1050`.
  - Rejection of invalid dates, negative amounts, or malformed category names in Zod schemas.
  - Calculation of category percentage utilization against monthly limits.

### 2. Integration Testing
- **Location**: `src/services/__tests__/*.integration.test.ts`
- **Focus**: Domain services interacting with an in-memory or ephemeral test database.
- **Key Test Cases**:
  - Creating a transaction correctly adjusts the parent account balance in the database.
  - Executing a transfer decrements source account and increments destination account atomically.
  - Rolling back a failed transfer leaves both account balances unchanged.
  - Attempting to delete an account with existing transactions throws an error.

### 3. End-to-End (E2E) Testing
- **Location**: `e2e/*.spec.ts`
- **Focus**: Full browser user journeys.
- **Key Test Suites**:
  - `account-management.spec.ts`: Create, update, and archive accounts.
  - `transactions.spec.ts`: Add income, expense, and transfer; filter ledger by category; verify balance cards.
  - `budgets.spec.ts`: Set category monthly limit; trigger budget threshold warning banner; verify progress bar.
  - `data-portability.spec.ts`: Export CSV; verify downloaded file contents; import sample bank CSV.

### 4. Regression & Continuous Testing
- Pre-commit hook runs linting and unit tests (`lint-staged`).
- Pull requests trigger full CI workflow:
  1. Static type checking (`tsc --noEmit`).
  2. Linting (`next lint`).
  3. Vitest suite (`vitest run`).
  4. Playwright E2E suite (`playwright test`).

### 5. Database Testing
- **Prisma Migrations**: Test forward migration and backward compatibility on clean test database.
- **Seed Integrity**: Verify that default categories and demo accounts seed without duplicate key conflicts.

### 6. Security Testing
- **Boundary Testing**: Inject extreme values (`Number.MAX_SAFE_INTEGER`, negative numbers, zero, SQL injection strings, XSS payloads `<script>`).
- **Authorization & Tenant Isolation**: Verify that a user session cannot read, modify, or delete records belonging to another `userId`.
- **Automated Scanning**: Run `npm audit` and OSV-Scanner in CI to detect vulnerable dependencies.

### 7. Build Verification
- Final production build check:
  ```bash
  npm run build
  ```
  Ensures zero compilation errors, zero unresolved imports, and valid static page generation.

---

## 4. Phase Completion Criteria Gates

A development phase is marked complete ONLY when all gate criteria are met:

| Phase | Quality & Testing Gate Criteria |
| :--- | :--- |
| **Phase 0** | All 11 foundational documents exist, verified consistent, no application code written, explicit user sign-off. |
| **Phase 1** | Tooling operational, `npm run build` succeeds on empty scaffold, TypeScript strict mode enabled, Vitest runs empty test. |
| **Phase 2** | Prisma migrations apply cleanly, schema models all required financial entities, seed script creates valid baseline data. |
| **Phase 3** | Domain services written with 90%+ unit test coverage, all financial invariants verified with unit tests. |
| **Phase 4** | Server Actions and API endpoints return standardized envelope responses, Zod validation passes 100% of boundary test cases. |
| **Phase 5** | Design system components render in both light and dark modes, accessible according to WCAG 2.1 AA. |
| **Phase 6** | Feature pages fully functional, integration tests pass for account, transaction, and budget CRUD workflows. |
| **Phase 7** | Analytics correctly aggregate data, Recharts render without console warnings, CSV export matches schema RFC 4180. |
| **Phase 8** | Vitest and Playwright test suites achieve 100% pass rate; security audit (`npm audit`) reports 0 vulnerabilities. |
| **Phase 9** | PostgreSQL migration verified; production build generates clean output; documentation updated. |
