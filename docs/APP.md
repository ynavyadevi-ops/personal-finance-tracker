# Personal Finance Tracker — Application Concept & Product Vision

> **DOCUMENT**: `docs/APP.md`  
> **STATUS**: STABLE & APPROVED BASELINE  
> **TECHNOLOGY STACK**: Python + SQL (FastAPI, Streamlit, SQLAlchemy, Alembic, Pydantic, Pandas, Plotly)  
> **CURRENT PHASE**: Phase 0 — Foundation and Documentation

---

## 1. Product Vision

The **Personal Finance Tracker** is an intuitive, secure, and privacy-first full-stack personal finance platform powered entirely by **Python and SQL**. It transforms money management into a real-time, actionable feedback loop that gives users total command over their financial trajectory.

In contrast to cloud SaaS applications that monetize user data, display intrusive affiliate credit card offers, or require closed third-party aggregators, this application delivers:
- **Local-First Autonomy**: High-speed, zero-dependency operation via embedded SQLite and a local Streamlit dashboard.
- **Enterprise-Ready Path**: A clean architectural path toward scalable multi-user PostgreSQL deployments, secured by FastAPI and JWT authentication.
- **Financial Precision**: Absolute mathematical accuracy using Python's `decimal.Decimal` and SQL `Numeric(18, 2)` to eliminate floating-point calculation drift.

### Core Value Pillars
1. **Total Visibility**: Consolidated views of all financial accounts (Checking, Savings, Cash, Credit Cards, Investments, Loans).
2. **Actionable Intelligence**: Responsive dashboards powered by Plotly and Pandas highlighting cash flow patterns, category spending breakdowns, and net worth progress.
3. **Data Sovereignty & Privacy**: Complete user control over personal financial data with full CSV/JSON/Excel import and export and zero telemetry leakage.
4. **Bank-Grade Reliability**: Double-entry inspired ledger integrity, atomic inter-account transfers via SQLAlchemy transactions, and immutable audit trails.

---

## 2. Target Personas & User Scenarios

### Persona A: The Budget-Conscious Saver (Alex, 27)
- **Goal**: Control discretionary spending, monitor daily outlays, and adhere strictly to monthly category budget limits (e.g., dining, entertainment, shopping).
- **Pain Point**: Cumbersome spreadsheet maintenance; frustration with commercial apps that clutter the interface with ads.
- **Streamlit Workflow**: Logs daily expenses through an intuitive Streamlit form, views real-time progress gauges and alert banners when nearing category budget limits, and inspects monthly savings stats.

### Persona B: The Freelancer / Hybrid Earner (Jordan, 34)
- **Goal**: Segregate irregular freelance client earnings from personal living expenses, track inter-account transfers, and prepare clean quarterly expense exports for tax filing.
- **Pain Point**: Inability to easily track which client payments funded specific equipment purchases; lack of clarity regarding liquid reserves.
- **Streamlit Workflow**: Creates multiple accounts in Streamlit, assigns custom project tags, schedules recurring invoice reminders, and exports filtered Pandas DataFrames to CSV/Excel at tax time.

### Persona C: The Wealth Builder (Morgan, 42)
- **Goal**: Track long-term net worth trajectory, accelerate debt payoff on credit lines, and analyze historical spending trends.
- **Pain Point**: Fragmented accounts across disparate institutions; unwilling to share bank login credentials with cloud aggregators.
- **Streamlit Workflow**: Reviews comprehensive Plotly area charts of net worth growth over time, analyzes spending shifts via stacked bar charts, and imports historical bank statements through the Pandas CSV import tool.

---

## 3. High-Level Feature Taxonomy

```
Personal Finance Tracker (Python + SQL)
├── 1. Account Management
│   ├── Multi-account tracking (Checking, Savings, Credit, Cash, Investment, Loan)
│   ├── Real-time deterministic balance calculation
│   ├── Opening balance setup and reconciliation
│   └── Safe account archiving (soft deletion preserving historical ledger)
├── 2. Transaction Ledger
│   ├── Income, Expense, and Inter-Account Transfer recording
│   ├── Atomic balanced transfers (Credit source, Debit destination via DB transaction)
│   ├── Categorization, merchant/payee tracking, notes, and tags
│   ├── Dynamic filtering, sorting, and pagination powered by Pandas & SQLAlchemy
│   └── Split transaction capability (Future Scope)
├── 3. Categorization & Hierarchy
│   ├── Customizable parent and sub-categories
│   ├── Seeded default categories (Housing, Groceries, Utilities, Transport, Healthcare, Salary)
│   └── Color coding and icon customization
├── 4. Budgets & Threshold Alerts
│   ├── Monthly category spending limits
│   ├── Dynamic budget utilization progress bars (Normal <80%, Warning 80-99%, Exceeded ≥100%)
│   └── Month-over-month rollover policies
├── 5. Analytics & Visualizations (Pandas + Plotly)
│   ├── Income vs. Expense monthly grouped bar charts
│   ├── Category spending breakdown (interactive Plotly donut/pie charts)
│   ├── Historical Net Worth trajectory area/line graphs
│   └── Metric cards (Total Income, Total Expenses, Net Savings, Savings Rate %)
├── 6. Recurring Transactions
│   ├── Scheduled bills and recurring income rules (Daily, Weekly, Monthly, Yearly)
│   └── Automated transaction queue generation and due date indicators
└── 7. Data Portability & Audit
    ├── RFC 4180 compliant CSV export and import via Pandas
    ├── JSON database backup and restore facility
    └── Comprehensive AuditLog tracking all balance-altering changes
```

---

## 4. User Experience & Design Ethos (Streamlit Frontend)

- **Frictionless Data Entry**: Logging an expense takes under 5 seconds with Streamlit forms, auto-focusing widgets, and preset defaults (today's date, last-used account).
- **Reactive Visual Feedback**: Streamlit re-evaluates views reactively upon user mutations; Plotly charts provide interactive tooltips, hover coordinates, and zoom capabilities.
- **Clean Component Layout**: Clear visual hierarchy with a persistent sidebar for navigation, key metric callouts (`st.metric`), tabular ledger views (`st.dataframe` with formatting), and tabbed deep-dives.
- **Light & Dark Mode**: Native Streamlit theme support adhering to user system preferences with high-contrast, accessible financial color schemes (Emerald for positive cash flow, Amber for budget warning, Crimson for over-budget or debt).
- **Graceful Error Banners**: Pydantic validation errors and API exceptions display as user-friendly Streamlit warning banners (`st.warning`, `st.error`) without raw stack traces.
