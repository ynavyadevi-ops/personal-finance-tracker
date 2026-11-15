# Personal Finance Tracker — Application Concept & Product Vision

> **DOCUMENT**: `docs/APP.md`  
> **STATUS**: STABLE & APPROVED BASELINE  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation

---

## 1. Product Vision

The **Personal Finance Tracker** is an intuitive, robust, and privacy-first full-stack financial management platform. It transforms personal money management from a tedious chore into an empowering, real-time feedback loop. 

Unlike cluttered commercial software that monetizes user financial data or forces rigid cloud synchronization, this application begins with a local-first, zero-telemetry architecture designed for ultimate privacy and speed, while maintaining an architectural path toward scalable, multi-tenant cloud deployment.

### Core Value Pillars
1. **Total Visibility**: Consolidated views of all financial accounts (Checking, Savings, Cash, Credit Cards, Investments).
2. **Actionable Intelligence**: Clear visual dashboards highlighting cash flow patterns, monthly burn rates, and budget variance.
3. **Data Sovereignty & Privacy**: Complete user control over personal financial data with full CSV/JSON export and zero unauthorized data harvesting.
4. **Bank-Grade Reliability**: Double-entry inspired ledger integrity, atomic transactions, and zero tolerance for floating-point calculation errors.

---

## 2. Target Personas & User Scenarios

### Persona A: The Budget-Conscious Saver (Alex, 27)
- **Goal**: Wants to control impulsive spending, track daily discretionary purchases, and establish monthly category budget limits (e.g., dining, entertainment).
- **Pain Point**: Overwhelmed by complex spreadsheet formulas; frustrated by commercial tools that constantly push credit card advertisements.
- **Workflow**: Adds daily expenses via a fast mobile-responsive web form, receives real-time visual warnings when approaching category thresholds, and inspects monthly savings progress.

### Persona B: The Freelancer / Hybrid Earner (Jordan, 34)
- **Goal**: Needs to segregate irregular freelance income from household living expenses, manage multi-account transfers, and prepare clean expense exports for tax filing.
- **Pain Point**: Difficult to track which invoice payments cover specific quarterly expenses; lacks a clear view of cash reserves across multiple bank accounts.
- **Workflow**: Creates multiple custom accounts, tags transactions with project codes, schedules recurring subscriptions, and exports categorized CSVs at year-end.

### Persona C: The Wealth Builder (Morgan, 42)
- **Goal**: Tracks total net worth trajectory over time, monitors debt payoff progress on loans/credit cards, and maintains historical spending records.
- **Pain Point**: Fragmented view across disparate institutions; concerned about security leaks of aggregated bank credentials.
- **Workflow**: Reviews high-level net worth charts, analyzes year-over-year spending shifts, and performs periodic manual or batch CSV imports.

---

## 3. High-Level Feature Taxonomy

```
Personal Finance Tracker
├── 1. Account Management
│   ├── Multi-account support (Checking, Savings, Credit, Cash, Investment)
│   ├── Real-time balance recalculation
│   ├── Starting balance initialization & reconciliation
│   └── Account archive/deactivation
├── 2. Transaction Management
│   ├── Income, Expense, and Internal Transfer logging
│   ├── Split transactions across categories (Future Scope)
│   ├── Custom tagging & merchant metadata
│   ├── Search, filter, and pagination
│   └── Atomic inter-account transfers (balanced debit/credit)
├── 3. Categorization & Hierarchy
│   ├── Customizable parent and sub-categories
│   ├── Default preset taxonomy (Housing, Food, Utilities, Transport, etc.)
│   └── Color coding and icon customization
├── 4. Budgets & Goal Tracking
│   ├── Monthly category spending limits
│   ├── Real-time visual progress bars & alert thresholds
│   └── Month-over-month rollover policies
├── 5. Analytics & Visualizations
│   ├── Income vs. Expense monthly bar charts
│   ├── Category spending breakdown (interactive donut/pie charts)
│   ├── Historical Net Worth trajectory line graph
│   └── Key financial metrics cards (Savings Rate, Burn Rate, Liquid Cash)
├── 6. Recurring Transactions
│   ├── Subscription and recurring bill scheduling (weekly, monthly, yearly)
│   └── Automatic transaction generation / reminder queue
└── 7. Data Portability & Audit
    ├── Standardized CSV / JSON import and export
    ├── Audit trail of financial balance changes
    └── Local backup and database snapshot generation
```

---

## 4. User Experience & Design Ethos

- **Speed & Frictionless Entry**: Logging an expense must take less than 5 seconds. Keyboard shortcuts, auto-focusing inputs, and sensible defaults (e.g., today's date, last-used account) are prioritized.
- **Design System**: Built upon clean, modern typography and minimalist components provided by Tailwind CSS and shadcn/ui.
- **Adaptive Visual Themes**: Native Dark and Light mode support with high-contrast color palettes for charts and indicators (e.g., green for positive cash flow, amber for budget warning, red for deficit).
- **Responsive Layout**: Fluid experience across mobile phones (bottom navigation/sticky actions), tablets, and high-resolution desktop displays (split-pane ledger and dashboard).
- **Accessible & Transparent**: WCAG 2.1 AA compliant color contrasts, ARIA live regions for balance updates, and explicit confirmation modals for destructive financial actions.
