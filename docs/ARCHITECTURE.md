# Personal Finance Tracker — System Architecture & Technical Design

> **DOCUMENT**: `docs/ARCHITECTURE.md`  
> **STATUS**: APPROVED BASELINE  
> **PHASE**: Phase 0 — Foundation and Documentation

---

## 1. High-Level Architectural Overview

The **Personal Finance Tracker** follows a clean, modular multi-layer architecture built on **Next.js App Router**, **React Server Components (RSC)**, and **Prisma ORM**. 

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER (UI)                         │
│  Next.js App Router (/app) • Server & Client Components • shadcn/ui    │
│  Tailwind CSS • Recharts Visualizations • React Hook Form + Zod        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Server Actions / Route Handlers
┌───────────────────────────────────▼────────────────────────────────────┐
│                        APPLICATION & API LAYER                         │
│  Next.js Server Actions • API Handlers (/api) • Zod Schema Validation  │
│  Authentication Guards • Rate Limiting & Audit Logging Interceptors    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Direct TypeScript Invocations
┌───────────────────────────────────▼────────────────────────────────────┐
│                         DOMAIN SERVICES LAYER                          │
│  AccountService • TransactionService • BudgetService • AnalyticsService│
│  Financial Arithmetic Engine (Integer Minor Units / Cents)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Repository / Data Access
┌───────────────────────────────────▼────────────────────────────────────┐
│                       PERSISTENCE LAYER (PRISMA)                       │
│  Prisma Client • Type-Safe Queries • Atomic Transactions ($transaction)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
        [ Local Development ]                [ Production Cloud ]
         SQLite (file:dev.db)                 PostgreSQL (v16+)
```

---

## 2. Frontend Architecture

### Server Components vs. Client Components
- **Server Components (Default)**: All top-level page routes (`/dashboard`, `/transactions`, `/budgets`, `/accounts`, `/reports`) are React Server Components (RSC). They fetch data directly through Domain Services without exposing public REST endpoints to the browser, minimizing client bundle size and eliminating data-fetching waterfalls.
- **Client Components (`'use client'`)**: Used exclusively for interactive leaves:
  - Form dialogs (Add/Edit Transaction, Account modal).
  - Data table filtering, sorting, and pagination controls.
  - Interactive Recharts components (tooltips, responsive resizing).
  - Theme toggles and notification toasts.

### State Management Strategy
- **URL-Driven State**: Filter parameters (date ranges, category selections, account IDs, page numbers) reside in the URL query string (`/transactions?category=food&page=2`). This enables shareable links, clean browser history, and effortless SSR hydration.
- **Server Actions**: Mutations (creating accounts, logging transactions, adjusting budgets) execute via Next.js Server Actions with optimistic UI updates where appropriate.
- **Form State**: Managed via `react-hook-form` paired with `@hookform/resolvers/zod` for synchronous client-side validation against shared domain schemas.

### UI Design System
- **Tailwind CSS & shadcn/ui**: Accessible headless primitives powered by Radix UI wrapped in Tailwind utility classes.
- **Design Tokens**: Standardized CSS variables for light/dark theme variables, semantic financial states (`--success`, `--warning`, `--destructive`, `--muted`).

---

## 3. Backend Architecture & Domain Services

To prevent vendor lock-in to Next.js internals, the backend employs a decoupled **Service-Repository** pattern:

```
src/
├── app/                  # Next.js App Router (Routing, Pages, Actions, Route Handlers)
│   ├── (dashboard)/      # Authenticated/Main application routes
│   │   ├── accounts/
│   │   ├── transactions/
│   │   ├── budgets/
│   │   └── analytics/
│   └── api/              # Public/External API endpoints (e.g., CSV export stream)
├── components/           # React Components
│   ├── ui/               # shadcn/ui generic primitives (Button, Dialog, Input, Table)
│   └── features/         # Domain-specific components (TransactionForm, NetWorthChart)
├── lib/                  # Shared utilities
│   ├── db.ts             # Prisma client singleton
│   ├── env.ts            # Validated environment configuration
│   └── utils.ts          # Classnames, date helpers, formatters
├── services/             # Core Domain Business Logic (Pure TypeScript)
│   ├── account.service.ts
│   ├── transaction.service.ts
│   ├── budget.service.ts
│   ├── analytics.service.ts
│   └── import-export.service.ts
├── schemas/              # Zod Validation Schemas (Shared between client & server)
│   ├── account.schema.ts
│   ├── transaction.schema.ts
│   └── budget.schema.ts
└── types/                # TypeScript Interfaces and Enums
```

### Domain Services Responsibilities
- **AccountService**: Handles account provisioning, balance recalculations, and archive rules.
- **TransactionService**: Enforces transfer atomicity, category bindings, and ledger immutability.
- **BudgetService**: Evaluates budget consumption against calendar months and computes threshold warnings.
- **AnalyticsService**: Computes aggregated rollups (cash flow, net worth trajectory, spending by category) using optimized SQL/Prisma aggregations.

---

## 4. Database Architecture & Data Modeling

### Prisma Schema Entities

```prisma
// datasource configured dynamically via env variable
datasource db {
  provider = "sqlite" // or "postgresql" in production
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

enum AccountType {
  CHECKING
  SAVINGS
  CREDIT_CARD
  CASH
  INVESTMENT
  LOAN
}

enum TransactionType {
  INCOME
  EXPENSE
  TRANSFER
}

model User {
  id            String         @id @default(cuid())
  email         String?        @unique
  name          String?
  createdAt     DateTime       @default(now())
  updatedAt     DateTime       @updatedAt
  accounts      Account[]
  categories    Category[]
  transactions  Transaction[]
  budgets       Budget[]
  recurringRules RecurringRule[]
  auditLogs     AuditLog[]
}

model Account {
  id             String          @id @default(cuid())
  userId         String
  user           User            @relation(fields: [userId], references: [id], onDelete: Cascade)
  name           String
  type           AccountType
  initialBalance Int             @default(0) // Stored in minor units (cents)
  currency       String          @default("USD")
  isArchived     Boolean         @default(false)
  createdAt      DateTime        @default(now())
  updatedAt      DateTime        @updatedAt
  transactions   Transaction[]
  transfersFrom  Transaction[]   @relation("TransferSource")
  transfersTo    Transaction[]   @relation("TransferDestination")

  @@index([userId])
}

model Category {
  id           String          @id @default(cuid())
  userId       String?         // Nullable for system default categories
  user         User?           @relation(fields: [userId], references: [id], onDelete: Cascade)
  name         String
  color        String          @default("#64748b")
  icon         String?
  isDefault    Boolean         @default(false)
  createdAt    DateTime        @default(now())
  transactions Transaction[]
  budgets      Budget[]

  @@unique([userId, name])
}

model Transaction {
  id                   String          @id @default(cuid())
  userId               String
  user                 User            @relation(fields: [userId], references: [id], onDelete: Cascade)
  accountId            String
  account              Account         @relation(fields: [accountId], references: [id], onDelete: Cascade)
  amount               Int             // Strictly positive, in minor units (cents)
  type                 TransactionType
  date                 DateTime
  categoryId           String?
  category             Category?       @relation(fields: [categoryId], references: [id], onDelete: SetNull)
  payee                String?
  notes                String?
  tags                 String?         // Comma-separated or JSON string
  
  // Transfer relationships
  transferSourceId     String?
  transferSource       Account?        @relation("TransferSource", fields: [transferSourceId], references: [id], onDelete: SetNull)
  transferDestId       String?
  transferDest         Account?        @relation("TransferDestination", fields: [transferDestId], references: [id], onDelete: SetNull)
  linkedTransactionId  String?         @unique // Links paired transfer records
  
  createdAt            DateTime        @default(now())
  updatedAt            DateTime        @updatedAt

  @@index([userId, date])
  @@index([accountId, date])
  @@index([categoryId])
}

model Budget {
  id         String     @id @default(cuid())
  userId     String
  user       User       @relation(fields: [userId], references: [id], onDelete: Cascade)
  categoryId String
  category   Category   @relation(fields: [categoryId], references: [id], onDelete: Cascade)
  month      Int        // 1 - 12
  year       Int        // e.g., 2026
  amount     Int        // Minor units (cents)
  createdAt  DateTime   @default(now())
  updatedAt  DateTime   @updatedAt

  @@unique([userId, categoryId, month, year])
}

model RecurringRule {
  id          String          @id @default(cuid())
  userId      String
  user        User            @relation(fields: [userId], references: [id], onDelete: Cascade)
  name        String
  amount      Int
  type        TransactionType
  frequency   String          // "DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY"
  startDate   DateTime
  nextRunDate DateTime
  isActive    Boolean         @default(true)
  createdAt   DateTime        @default(now())

  @@index([userId, nextRunDate])
}

model AuditLog {
  id        String   @id @default(cuid())
  userId    String
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  action    String   // "CREATE" | "UPDATE" | "DELETE" | "TRANSFER"
  entity    String   // "Account" | "Transaction" | "Budget"
  entityId  String
  details   String   // JSON formatted metadata
  ipAddress String?
  createdAt DateTime @default(now())

  @@index([userId, createdAt])
}
```

---

## 5. API Design Principles

1. **Standardized Response Envelope**:
   All Route Handlers and Server Actions return a consistent response structure:
   ```typescript
   type ApiResponse<T> = 
     | { success: true; data: T; meta?: Record<string, unknown> }
     | { success: false; error: { code: string; message: string; details?: unknown } };
   ```
2. **HTTP Status Codes**:
   - `200 OK`: Successful retrieval / update.
   - `201 Created`: Entity created.
   - `400 Bad Request`: Syntax or semantic error.
   - `401 Unauthorized`: Missing or invalid session.
   - `403 Forbidden`: Cross-tenant resource access attempt.
   - `404 Not Found`: Entity does not exist.
   - `422 Unprocessable Entity`: Zod validation failure.
   - `500 Internal Server Error`: Unhandled server exception.
3. **Idempotency**:
   Mutations accept an optional client-generated `idempotencyKey` to prevent duplicate transaction submissions caused by network retries.

---

## 6. Authentication Strategy for Production

- **Local MVP (Phases 1-8)**: A default local user context (`default-user-id`) is auto-seeded and bound to all sessions. This enables full end-to-end functionality without third-party auth provider lock-in.
- **Production Evolution (Phase 9+)**:
  - Integration with **Auth.js (NextAuth.js v5)**.
  - Providers: Passwordless Magic Links, OAuth 2.0 (Google, GitHub), and Argon2id password-based credentials.
  - Session tokens stored in encrypted `httpOnly`, `SameSite=Strict`, `Secure` cookies.
  - Mandatory tenant context injection into every service call (`where: { userId: session.user.id }`).

---

## 7. Error Handling & Data Validation

### Error Handling
- A dedicated `AppError` class hierarchy (`ValidationError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ConflictError`).
- Global error boundary (`app/error.tsx`) catches unhandled client-side render exceptions.
- API route wrappers catch domain exceptions, log them securely with correlation IDs, and return sanitized error responses preventing internal stack trace disclosure.

### Data Validation
- Validation is performed using **Zod** at runtime before any database access or business logic execution.
- Strict type inference (`z.infer<typeof schema>`) guarantees complete compile-time type safety between form components, Server Actions, and services.

---

## 8. Logging & Observability

- **Structured JSON Logging**: Standardized logs emitting timestamp, log level (`INFO`, `WARN`, `ERROR`), correlation ID, user ID, module name, and event metadata.
- **Audit Logging**: Sensitive mutations (deleting accounts, editing past transactions, modifying budget allocations) write an immutable record to the `AuditLog` table.
- **Zero Financial Data PII in Logs**: Account numbers, raw notes containing personal secrets, and passwords are unconditionally redacted.

---

## 9. Scalability & Performance

- **Database Indexing**: Compound indexes on `(userId, date)` and `(accountId, date)` ensure lightning-fast ledger sorting and range queries.
- **Cursor-Based Pagination**: Employs deterministic cursor pagination (`take: 50, skip: 1, cursor: { id }`) to guarantee steady $O(1)$ query execution even with millions of rows.
- **Connection Pooling**: Prepared for production PostgreSQL via **PgBouncer** or **Prisma Accelerate** to manage concurrent serverless connection limits.

---

## 10. SQLite-to-PostgreSQL Migration Strategy

A fundamental architectural mandate is zero lock-in to SQLite. The application is engineered for seamless migration to PostgreSQL:

1. **Dialect-Agnostic Types**:
   - Monetary amounts are stored as standard `Int` (cents), which is identical across SQLite and PostgreSQL.
   - Strings and enums are modeled to avoid engine-specific type deviations.
   - Dates are standardized as ISO 8601 UTC `DateTime`.
2. **Environment Datasource Switching**:
   - The Prisma schema configures the provider dynamically, or via a build script:
     ```bash
     # Local development
     DATABASE_URL="file:./dev.db"
     
     # Production
     DATABASE_URL="postgresql://user:password@pg-host:5432/personal_finance?sslmode=require"
     ```
3. **Migration Verification Workflow**:
   - A dedicated export/import migration script (`scripts/migrate-sqlite-to-pg.ts`) validates:
     1. Table row counts match identically.
     2. Net worth and account balance recalculations match to the exact cent.
     3. Foreign key constraints and unique constraints remain intact.
