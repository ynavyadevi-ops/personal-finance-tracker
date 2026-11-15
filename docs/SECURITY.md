# Personal Finance Tracker — Security Baseline & Compliance Policy

> **DOCUMENT**: `docs/SECURITY.md`  
> **STATUS**: ENFORCED & ACTIVE  
> **PHASE**: Phase 0 — Foundation and Documentation

---

## 1. Security Overview & Threat Model

Financial management applications handle sensitive personal data. A breach or integrity violation could expose private net worth, transaction history, and banking relationships, or corrupt balance records.

This security policy defines strict preventive, detective, and corrective controls across every layer of the application lifecycle.

---

## 2. OWASP Top 10 Mitigation Matrix

| OWASP Risk | Threat Description | Architectural Mitigation in Personal Finance Tracker |
| :--- | :--- | :--- |
| **A01: Broken Access Control** | Unauthorized user accesses another user's accounts or financial ledger. | **Strict Tenant Isolation**: Every database query through Prisma MUST enforce user ownership (`where: { userId: currentUserId, id: resourceId }`). Server Actions re-verify session authenticity before every write. |
| **A02: Cryptographic Failures** | Exposure of passwords, sensitive tokens, or unencrypted data in transit. | **Strong Cryptography**: TLS 1.3 enforced in production. Session cookies use `Secure`, `HttpOnly`, `SameSite=Strict`. Password hashing utilizes **Argon2id** with calibrated memory and iteration costs. |
| **A03: Injection** | SQL, NoSQL, or Command injection via malicious form or query input. | **Prisma Parameterized Queries**: Zero raw SQL string concatenation. All database interactions occur via Prisma ORM parameterized statements. Zod strictly sanitizes and validates all incoming fields. |
| **A04: Insecure Design** | Flawed business logic enabling race conditions or money creation. | **Double-Entry Balance Conservation & Atomic Transactions**: Inter-account transfers and balance changes are executed within atomic `$transaction` blocks. Negative values are strictly checked against business invariants. |
| **A05: Security Misconfiguration** | Insecure default configs, unhardened headers, exposed debug endpoints. | **Security Headers**: Production builds configure strict HTTP response headers via `next.config.js`: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`. |
| **A06: Vulnerable Components** | Dependencies with known CVEs or supply-chain malware. | **Automated Audits**: Mandatory `npm audit` and **OSV-Scanner** integration in CI pipelines. Dependency approval process strictly enforced before installation. |
| **A07: Identification & Auth Failures** | Brute force attacks, session hijacking, or credential stuffing. | **Rate Limiting & Secure Sessions**: In-memory / Redis rate limiting on authentication routes; session token invalidation upon password reset or logout; short idle session timeouts. |
| **A08: Software & Data Integrity Failures** | Unverified packages or tampering with serialized data. | **Immutable Lockfiles**: `package-lock.json` enforced via `npm ci`. Strict SHA-512 package integrity verification. Tamper-evident audit logging for financial state changes. |
| **A09: Logging & Monitoring Failures** | Breaches undetected due to absent or inadequate logs. | **Structured Security Logging**: Centralized logging for authentication events, permission denials, and critical financial mutations. Zero PII/financial secrets in log outputs. |
| **A10: Server-Side Request Forgery (SSRF)** | Exploitation of export/import or webhook services to probe internal networks. | **Disabled Outbound Fetching**: The application does not fetch arbitrary user-supplied URLs. CSV/JSON imports are performed strictly via uploaded file streams with size and MIME validation. |

---

## 3. Dependency Supply-Chain Security & Approval Policy

To protect against malicious supply chain attacks, typojquatting, and compromised packages:

### Strict Dependency Approval Rules
No package may be introduced into `package.json` without fulfilling all criteria:
1. **Established Reputation**: Minimum of 1,000+ weekly npm downloads.
2. **Active Maintenance**: Latest commit/release within the previous 12 months.
3. **Clean Security History**: Zero unresolved High or Critical CVEs.
4. **Minimal Transitive Footprint**: Avoid packages that bring hundreds of unvetted sub-dependencies.
5. **Architectural Approval**: Any new dependency must be formally documented in `docs/DECISIONS.md`.

### Vulnerability Scanning Protocol
- **npm audit**:
  ```bash
  npm audit --audit-level=high
  ```
  Any detected high or critical vulnerability fails the build immediately.
- **OSV-Scanner**:
  The Google OSV-Scanner checks against the open-source vulnerability database:
  ```bash
  osv-scanner --lockfile=package-lock.json
  ```
  Run periodically and as a pre-commit / CI gate.

---

## 4. Environment Variables & Secret Management

1. **Strict Segregation**:
   - `.env.example` contains variable names and dummy values. This file is tracked in Git.
   - `.env`, `.env.local`, `.env.production` are strictly ignored by `.gitignore` and must NEVER be committed.
2. **Runtime Validation**:
   - Environment variables are validated at application startup using a dedicated Zod schema (`src/lib/env.ts`).
   - If a mandatory secret (e.g., `DATABASE_URL`, `AUTH_SECRET`) is missing or invalid, the application immediately aborts with a descriptive error.
3. **Production Secret Storage**:
   - Production secrets are injected via secure platform secret managers (e.g., Vercel Environment Variables, AWS Secrets Manager, GitHub Secrets).

---

## 5. Database Access & Financial Data Protection

1. **Principle of Least Privilege**:
   - In production PostgreSQL, the application connects using a dedicated database role with permissions restricted strictly to `SELECT`, `INSERT`, `UPDATE`, `DELETE` on application tables. Schema modification permissions (`ALTER`, `DROP`) are reserved for migration scripts.
2. **Protection Against Floating-Point Errors**:
   - Floating-point representations (`0.1 + 0.2 = 0.30000000000000004`) lead to balance drift and financial accounting fraud.
   - **Mandate**: All monetary amounts are stored as **integer minor units** (e.g., USD cents: `$15.99` $\to$ `1599`) or database `Decimal` types.
3. **Database Backups & Snapshot Security**:
   - Automated daily database backups must be encrypted at rest using AES-256.
   - Database connection strings in production must enforce TLS (`sslmode=require`).

---

## 6. Security Incident Response Protocol

In the event a security flaw or CVE is discovered:
1. **Assess Impact**: Determine affected versions, data exposure risks, and exploitation feasibility.
2. **Containment**: Temporarily disable vulnerable endpoints or rollback the deployment if active exploitation occurs.
3. **Remediation**: Apply upstream patches, update dependencies, or implement a targeted code fix.
4. **Verification**: Execute `npm audit`, unit security test suites, and Playwright regressions.
5. **Post-Mortem**: Document root cause, resolution, and preventative safeguards in `docs/CHANGELOG.md` and `docs/DECISIONS.md`.
