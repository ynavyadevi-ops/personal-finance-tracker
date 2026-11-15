# Personal Finance Tracker

A production-oriented, secure, and modern full-stack web application designed to help individuals monitor their financial health, track transactions, manage categorized budgets, and gain visual insights into spending habits and net worth.

---

## 1. Project Overview

- **Name**: Personal Finance Tracker
- **Current Phase**: **Phase 0 — Project Foundation and Documentation**
- **Architecture**: Next.js App Router, React Server Components (RSC), Prisma ORM, Server Actions, shadcn/ui design system.
- **Data Layer**: Dual database strategy — SQLite for local zero-dependency development/MVP; PostgreSQL for high-concurrency production deployments.
- **Security Posture**: OWASP Top 10 aligned, strict Zod schema validation at all network boundaries, atomic ledger transactions, and no floating-point arithmetic errors for monetary data.

---

## 2. Technology Stack & Verified Versions

| Component | Technology | Target Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js | `^15.2.0` / `^16.0.0` | App Router, Server Components, API routes, optimizations |
| **UI Library** | React | `^19.0.0` | Core declarative UI rendering |
| **Language** | TypeScript | `^5.7.0` | Strict static typing (`strict: true`) across full stack |
| **Styling** | Tailwind CSS | `^4.0.0` (or `^3.4.0` compat) | Utility-first responsive styling |
| **UI Components** | shadcn/ui + Radix UI | Latest | Accessible, customizable headless primitives |
| **ORM** | Prisma ORM | `^6.4.0` / `^7.10.0` | Type-safe database queries and migrations |
| **Local Database** | SQLite | Built-in | Embedded zero-configuration local MVP database |
| **Production DB** | PostgreSQL | `16+` | Robust, ACID-compliant relational production database |
| **Validation** | Zod | `^3.24.0` / `^4.0.0` | Runtime request/action/form data validation |
| **Data Visualization** | Recharts | `^2.15.0` / `^3.0.0` | Interactive charts (spending breakdown, monthly trends) |
| **Unit/Integration Testing** | Vitest | `^3.0.0` / `^5.0.0` | Fast in-memory testing for business logic & components |
| **E2E Testing** | Playwright | `^1.50.0` / `^1.65.0` | Browser automation for end-to-end critical user journeys |

---

## 3. Documentation Index

The project is governed by an exhaustive documentation suite located in the `docs/` directory and root directives:

| Document | Purpose |
| :--- | :--- |
| [AGENTS.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/AGENTS.md) | Mandatory instructions and operational constraints for AI agents. |
| [docs/APP.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/APP.md) | High-level product vision, user personas, core capabilities, and UX ethos. |
| [docs/SPEC.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/SPEC.md) | Detailed functional & non-functional requirements, business rules, and acceptance criteria. |
| [docs/ARCHITECTURE.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/ARCHITECTURE.md) | Full-stack technical architecture, API design, database schemas, and migration path. |
| [docs/SECURITY.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/SECURITY.md) | Security baseline, OWASP protections, dependency scanning, secrets, and auth policies. |
| [docs/TESTING.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/TESTING.md) | Quality assurance framework, testing pyramid, Vitest/Playwright setup, and phase gates. |
| [docs/DEVELOPMENT_RULES.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/DEVELOPMENT_RULES.md) | Engineering standards, code hygiene, Git conventions, and defensive programming. |
| [docs/PHASES.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/PHASES.md) | Nine-phase development roadmap, deliverables, and acceptance sign-off gates. |
| [docs/CHANGELOG.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/CHANGELOG.md) | Chronological version history following Keep a Changelog standard. |
| [docs/DECISIONS.md](file:///c:/Users/visha/OneDrive/Desktop/Navya/Vibe%20coding/Personal%20expense%20tracker/docs/DECISIONS.md) | Architectural Decision Records (ADRs) documenting design rationale and trade-offs. |

---

## 4. Development Workflow & Phase Roadmap

The project follows a strict 9-phase lifecycle:
1. **Phase 0: Project Foundation and Documentation** *(Current Phase — Completed / Awaiting Approval)*
2. **Phase 1: Environment Setup, Tooling & Core Project Scaffolding**
3. **Phase 2: Database Modeling, Prisma Schema & Migrations**
4. **Phase 3: Core Domain Services, Validation Schemas & Business Logic**
5. **Phase 4: Backend API Routes & Server Actions**
6. **Phase 5: UI Design System & Component Library (shadcn/ui + Tailwind)**
7. **Phase 6: Application Pages & User Features (Accounts, Transactions, Budgets)**
8. **Phase 7: Analytics, Visualizations & Data Export (Recharts, CSV/JSON)**
9. **Phase 8: Comprehensive Testing, Security Audits & Performance Optimization**
10. **Phase 9: Production Readiness, PostgreSQL Migration Verification & Deployment**

---

## 5. Getting Started (For Future Phases)

*Note: Application dependencies and code will be initialized starting in Phase 1 following user approval.*

Prerequisites:
- **Node.js**: `v20.x` or `v24.x` (LTS recommended)
- **npm**: `v10.x` or `v11.x`
- **Git**: `2.x+`

```bash
# Clone the repository
git clone <repo-url>
cd "Personal expense tracker"

# Install dependencies (Phase 1)
npm install

# Run database migrations (Phase 2)
npx prisma migrate dev

# Start local development server (Phase 5+)
npm run dev
```

---

## 6. License & Compliance

Proprietary and confidential. Developed under strict data privacy and local-first compliance standards.
