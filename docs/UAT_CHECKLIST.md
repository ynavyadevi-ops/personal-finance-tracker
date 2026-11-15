# Personal Finance Tracker — User Acceptance Testing (UAT) Manual Checklist

> **DOCUMENT**: `docs/UAT_CHECKLIST.md`  
> **STATUS**: APPROVED & ENFORCED  
> **APPLICATION VERSION**: v0.1.0 (Local MVP Release Candidate)  
> **TARGET AUDIENCE**: QA Engineers, Product Owners, End Users  

---

## 1. Overview & Setup

This document provides a comprehensive, step-by-step browser testing procedure for verifying all 10 core application views, authentication workflows, data import/export pipelines, and security controls.

### Prerequisites
1. Backend running:
   ```cmd
   scripts\run_backend.bat
   ```
   *Health Check*: Navigate to `http://127.0.0.1:8000/health` -> HTTP 200 `{"status": "healthy", "database": "connected"}`.
2. Frontend running:
   ```cmd
   scripts\run_frontend.bat
   ```
   *UI Access*: Navigate to `http://127.0.0.1:8501`.

---

## 2. Test Case Matrix

### 2.1 Authentication & Session Management
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **AUTH-01** | Initial Unauthenticated Access | Open `http://127.0.0.1:8501` without logging in. | Application automatically renders the Login View. Core navigation is locked. | [ ] |
| **AUTH-02** | Invalid Password Attempt | Enter email `user@local.dev` and password `WrongPassword123!`. Click "Log In". | Error alert: "Invalid email or password". Session token remains unset. | [ ] |
| **AUTH-03** | Successful Authentication | Enter valid enrolled credentials. Click "Log In". | Notification banner confirms login. UI redirects to Dashboard. Sidebar navigation unlocks. | [ ] |
| **AUTH-04** | User Logout | Click "Log Out" in the sidebar navigation or Settings view. | Session token cleared from Streamlit state. UI returns to Login View immediately. | [ ] |

---

### 2.2 Dashboard View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **DASH-01** | KPI Metric Cards | View Dashboard with existing accounts and transactions. | Displays Total Balance, Monthly Inflow, Monthly Outflow, and Net Savings with currency symbols. | [ ] |
| **DASH-02** | Currency Isolation | Switch currency dropdown between INR and USD. | Values recompute for selected currency only. INR and USD are never combined into a single sum. | [ ] |
| **DASH-03** | Visual Trends Expander | Expand "Financial Charts & Trends" section. | Interactive Plotly charts render: Monthly Inflow vs Outflow, Net Cash Flow trend, and Category Donut. | [ ] |
| **DASH-04** | Quick Action Shortcuts | Click "+ Record Transaction" button. | Switches active sidebar view to Transactions immediately. | [ ] |

---

### 2.3 Accounts Management View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **ACC-01** | Account Inventory List | Navigate to Accounts view. | Lists all user-owned accounts with type (Checking, Savings, Demat, Credit), currency, and balance. | [ ] |
| **ACC-02** | Create New Account | Click "+ New Account". Enter Name: "HDFC Savings", Type: "Savings", Currency: "INR", Opening: 5000.00. | Account successfully created. Added to account list with ₹5,000.00 balance. | [ ] |
| **ACC-03** | Duplicate Name Conflict | Attempt to create another account named "HDFC Savings" with same currency. | HTTP 409 Conflict error displayed. Prevented duplicate account creation. | [ ] |
| **ACC-04** | Edit Account Details | Click "Edit" on an existing account, rename to "HDFC Salary Savings". | Name updates in database and reflected across all dropdowns. | [ ] |

---

### 2.4 Transactions & Double-Entry Ledger View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **TX-01** | Record Expense | Select account, Type: EXPENSE, Amount: 450.00, Category: Groceries, Desc: "Weekly Mart". | Transaction committed. Account balance reduces by 450.00. Credit entry logged in ledger. | [ ] |
| **TX-02** | Record Income | Select account, Type: INCOME, Amount: 25000.00, Category: Salary, Desc: "Freelance Client". | Transaction committed. Account balance increases by 25,000.00. Debit entry logged in ledger. | [ ] |
| **TX-03** | Zero/Negative Amount Rejection | Enter Amount: 0.00 or -50.00. Click "Record". | Client-side and server-side validation error displayed. Transaction rejected. | [ ] |
| **TX-04** | Inter-Account Transfer | Select Source Account (INR), Destination Account (INR), Amount: 2000.00. | Atomic transfer executes. Source balance -2000.00, Destination balance +2000.00. Sum conserved. | [ ] |
| **TX-05** | Cross-Currency Transfer Block | Select Source Account (INR), Destination Account (USD). | Transfer rejected with "Currency mismatch between accounts" error. Balances unaltered. | [ ] |
| **TX-06** | Compensating Reversal | Select an existing transaction, click "Reverse", enter reason: "Duplicate charge". | Compensating inverted transaction created. Balance restored. Reversal tag attached. | [ ] |
| **TX-07** | Repeated Reversal Block | Click "Reverse" again on the already-reversed transaction. | Reversal rejected with error: "Transaction has already been reversed." | [ ] |

---

### 2.5 Budgets & Spending Caps View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **BUD-01** | Set Category Budget | Select Category: Dining Out, Month: Current, Year: Current, Cap: 5000.00. | Budget created. Displayed in monthly budget list. | [ ] |
| **BUD-02** | Budget Utilization Warning | Record dining transactions totaling 4200.00 (84% of 5000.00). | Warning badge (Yellow/Amber) displayed indicating budget >= 80% consumed. | [ ] |
| **BUD-03** | Budget Exceeded Alert | Record additional dining transactions totaling 5500.00 (110% of 5000.00). | Danger badge (Red) displayed indicating budget exceeded with overspent amount. | [ ] |

---

### 2.6 Savings Goals View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **GOAL-01** | Create Savings Goal | Enter Name: "Emergency Fund", Target: 100000.00, Currency: INR, Target Date: 2027-12-31. | Goal saved. Progress bar displays 0% achieved. | [ ] |
| **GOAL-02** | Contribute to Goal | Click "Contribute", enter Amount: 25000.00 from Checking Account. | Goal balance increases to 25,000.00. Progress bar updates to 25.0%. | [ ] |
| **GOAL-03** | Goal Achievement | Contribute remaining balance until target is reached or exceeded. | Progress bar fills to 100%. "Goal Achieved!" celebratory badge renders. | [ ] |

---

### 2.7 Loans & Debt Obligations View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **LOAN-01** | Add Loan Liability | Enter Lender: "HDFC Home Loan", Principal: 500000.00, Rate: 8.5%, Term: 60 months. | Loan obligation created. Full 60-month amortization schedule generated. | [ ] |
| **LOAN-02** | Amortization Breakdown | Inspect the payment schedule table. | Each instalment displays principal component, interest component, total EMI, and balance. | [ ] |
| **LOAN-03** | Record Instalment Payment | Click "Pay Instalment #1". Select payment checking account. | Instalment marked paid with paid date. Outstanding loan balance reduces. | [ ] |

---

### 2.8 Investments & Securities Portfolio View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **INV-01** | Purchase Security (BUY) | Select Brokerage Account, Asset: TCS.NS, Qty: 10.0000, Price: 3500.00, Fees: 20.00. | Trade executed. Holding created with 10 units @ ₹3502.00 weighted-average cost basis. | [ ] |
| **INV-02** | Weighted-Average Addition | Buy additional 5.0000 units of TCS.NS @ 3800.00, Fees: 10.00. | Total units = 15.0000. Cost basis recalculated accurately: ₹3602.00/unit. | [ ] |
| **INV-03** | Liquidate Security (SELL) | Sell 5.0000 units of TCS.NS @ 4000.00, Fees: 15.00. | Trade executed. Realized capital gain of ₹1,975.00 computed. Remaining units = 10.0000. | [ ] |
| **INV-04** | Insufficient Units Rejection | Attempt to sell 25.0000 units of TCS.NS (only 10 units held). | Trade rejected with "Cannot sell 25.0000 units; only 10.0000 held" error. | [ ] |

---

### 2.9 Recurring Transaction Templates View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **REC-01** | Create Monthly Recurring Rule | Name: "Internet Fiber", Amount: 999.00, Freq: MONTHLY, Interval: 1, Account: Checking. | Recurring rule created. Next occurrence calculated for next month. | [ ] |
| **REC-02** | Manual Trigger Execution | Click "Execute Now" on the recurring rule. | Generates real ledger transaction with tag `recurring_rule:<id>`. Next date increments. | [ ] |

---

### 2.10 Financial Analytics & AI Insights View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **ANA-01** | Cash Flow & Trends Tab | Select timeframe: "Last 6 Months", Currency: "INR". | Interactive Plotly charts render: Monthly Inflow vs Outflow, Net Cash Flow area trend. | [ ] |
| **ANA-02** | Category Spending Tab | View Category Breakdown. | Plotly donut chart displays category allocation percentages with formatted tooltips. | [ ] |
| **ANA-03** | Rule-Based Smart Insights | View "Rule-Based Deterministic Observations" section. | Shows explainable derivations for spending rate, savings rate, and budget threshold alerts. | [ ] |
| **ANA-04** | AI Insights Opt-In Privacy | Navigate to "AI Insights & Privacy Controls" tab. Check default state. | AI Insights is DISABLED by default. Clear privacy policy and non-advice disclaimer shown. | [ ] |
| **ANA-05** | AI Consent Activation | Toggle "Enable AI Financial Observations" checkbox. | Generates narrative observations using locally sanitized aggregate data. Zero PII transmitted. | [ ] |

---

### 2.11 Statement Ingestion & Data Portability View
| ID | Test Scenario | Steps | Expected Result | Pass/Fail |
| :--- | :--- | :--- | :--- | :--- |
| **PORT-01** | CSV Statement Import | Upload bank statement CSV, map Date, Amount, Description columns. Click "Preview". | Displays parsed valid rows. Duplicate detection identifies previously committed entries. | [ ] |
| **PORT-02** | CSV Export Formula Defense | Record transaction with desc `=SUM(A1:A10)`. Click "Export CSV". Open file in Notepad. | Formula character is escaped with leading single quote: `'=SUM(A1:A10)`. No formula injection. | [ ] |
| **PORT-03** | XLSX Binary Export | Click "Export Excel (.xlsx)". | Generates and downloads valid binary Microsoft Excel spreadsheet. | [ ] |
| **PORT-04** | JSON Backup Snapshot | Click "Download Complete JSON Backup". | Downloads user-scoped JSON snapshot containing accounts, transactions, budgets, goals, loans. | [ ] |
| **PORT-05** | Dry-Run Backup Validation | Upload downloaded JSON file to "Validate Backup Snapshot" section. | Confirms valid version ("1.0.0"), table counts, and displays message: "No destructive changes". | [ ] |

---

## 3. Failure Indicators & Troubleshooting Guide

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| "Connection Refused" on frontend | FastAPI backend service not running on port 8000 | Run `scripts\run_backend.bat` in a dedicated terminal. |
| "Authentication Required" 401 error | Session JWT expired or missing | Re-login via `http://127.0.0.1:8501`. Default token lifetime is 60 minutes. |
| "Currency mismatch between accounts" | Attempting to transfer funds between differing currencies (e.g. INR to USD) | Transfers must occur between accounts sharing identical currency. Create currency conversion entry manually. |
| "Insufficient units" error | Attempting to liquidate more security units than currently held | Check holdings balance before submitting sell order. Verify previous trade executions. |
| Duplicate account name error (409) | Account with identical name already exists for user | Choose a unique display name (e.g. append bank name or account number digits). |
