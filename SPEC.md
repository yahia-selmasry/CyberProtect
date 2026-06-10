# CyberProtect — V1 Product Specification

**Version:** 1.0  
**Date:** June 9, 2026  
**Status:** Draft — Ready for Engineering

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Target Users](#2-target-users)
3. [Core Features (V1)](#3-core-features-v1)
4. [Data Model](#4-data-model)
5. [Out of Scope for V1](#5-out-of-scope-for-v1)
6. [Success Metrics](#6-success-metrics)
7. [End-to-End Verification](#7-end-to-end-verification)

---

## 1. Problem Statement

Small to medium-sized businesses (SMBs) are increasingly targeted by cyberattacks, yet most lack the in-house security expertise to run consistent, thorough security audits. Business and account owners worry that their web applications are exposed to vulnerabilities that go undetected for weeks or months — not because they don't care, but because they don't have the tools or knowledge to act.

CyberProtect solves this by providing an AI-powered web application security scanner that automatically audits a business's web properties on a monthly schedule, immediately alerts owners to any findings, prioritizes vulnerabilities by severity, provides plain-English step-by-step remediation instructions, tracks security posture over time, and maps findings to the SOC 2 compliance framework — giving SMBs the confidence that their security is consistent, documented, and audit-ready.

---

## 2. Target Users

### Primary User: Business Owner / Account Owner
- Runs or owns an SMB with one or more web-facing applications
- Non-technical or semi-technical — may not have a dedicated IT team
- Primary concern: "Are we protected? Will we get hacked?"
- Needs to prove security posture to cyber insurers, enterprise clients, or auditors
- Is the ultimate authority on the account — invites team members and revokes access

### Secondary User: Invited Team Member
- Could be an IT staff member, operations manager, or external consultant
- Invited by the business owner and granted access to scan reports and findings
- Can view findings and implement fix instructions but cannot manage billing or account settings
- Access can be immediately revoked by the owner at any time

### Not a Target User (V1)
- Enterprise security teams with dedicated tooling
- Developers needing raw API access to scan data
- Managed Security Service Providers (MSSPs)

---

## 3. Core Features (V1)

### Feature 1: AI-Powered Web Application Scanning

The core of CyberProtect is an AI engine that scans web applications for security vulnerabilities. In V1, scanning is scoped exclusively to web applications via a submitted domain/URL.

**What the scan covers:**
- Injection vulnerabilities (SQL injection, command injection, LDAP injection)
- Cross-site scripting (XSS — reflected, stored, DOM-based)
- Security misconfigurations (exposed admin panels, directory listing, insecure HTTP headers)
- Broken authentication signals (missing HTTPS, weak cookie settings, exposed login endpoints)
- Sensitive data exposure (unprotected files, exposed error messages, insecure forms)
- Known CVEs associated with detectable software versions

**How it works:**
- The business owner submits a domain/URL during onboarding
- Scans run automatically on a monthly schedule (same date each month)
- The AI engine probes only the submitted domain/URL — no adjacent infrastructure is touched
- Optional: owner may provide credentials (username/password) to enable scanning of authenticated pages. This is entirely at the owner's discretion; CyberProtect stores credentials encrypted and accepts no liability for credential misuse
- Scans run in an isolated environment with no ability to modify target systems

**Scan output:**
Each scan produces a structured report containing:
- A summary security score (0–100)
- A list of all findings, each tagged with severity (Critical / High / Medium / Low / Informational)
- Plain-English explanation of what each vulnerability is and why it matters
- Step-by-step remediation instructions written for a non-technical owner
- SOC 2 control mapping for each finding (see Feature 4)

---

### Feature 2: Instant Multi-Channel Alerting

Every finding — regardless of severity — triggers an immediate notification at the moment the scan completes. There is no batching or delay.

**Notification channels (all three fire simultaneously):**
- **Email** — sent to all users on the account with a summary of findings and a link to the full report
- **SMS** — sent to the phone number on file for the account owner (and any team members who have opted in)
- **In-app dashboard notification** — a persistent alert badge visible upon next login

**Notification content:**
- Number of findings by severity
- The single highest-severity finding as a headline
- Direct link to the full scan report
- Time/date of scan completion

**Design principle:** It must be impossible for an owner to miss a finding. Triple-channel delivery with zero delay is non-negotiable.

---

### Feature 3: Multi-Account and Team Access Management

CyberProtect supports multiple businesses, multiple accounts per business, and multiple users per account.

**Account hierarchy:**
```
Business (e.g., "Acme Corp")
  └── Account (e.g., "acmecorp.com scan account")
        ├── Owner (1 per account — full control)
        └── Invited Members (0 or more — view access)
```

**Owner capabilities:**
- Full access to all scan reports, findings, and history
- Invite team members by email
- Immediately revoke any team member's access (effective immediately — active sessions terminated)
- Manage billing and subscription
- Add or remove URLs/domains from the account
- Export reports

**Invited Member capabilities:**
- View scan reports and findings
- View step-by-step remediation instructions
- Receive email/SMS notifications (opt-in)
- Cannot manage team, billing, or account settings

**Access revocation:** When an owner revokes a team member, that member's session is invalidated immediately. They retain no access to historical reports. The owner retains full operational capability regardless of who else is on the account.

**Edge case — owner departure:** Only one owner per account is supported in V1. Owner transfer is out of scope; businesses should ensure the owner account is tied to a business email, not a personal one.

---

### Feature 4: SOC 2 Compliance Mapping

Every finding in a scan report is automatically mapped to the relevant SOC 2 Trust Services Criteria (TSC).

**Mapping coverage:**
- CC6 (Logical and Physical Access Controls)
- CC7 (System Operations — monitoring and detection)
- CC8 (Change Management)
- A1 (Availability)

**What the owner sees:**
- Each finding is tagged with its SOC 2 control (e.g., "This finding relates to CC6.1 — Logical Access")
- A compliance summary section in each report showing which SOC 2 controls have passing/failing/unverified status based on scan findings
- A dedicated SOC 2 Readiness view showing control-by-control status across all historical scans

**Purpose:** SMB owners can share reports with cyber insurers, enterprise procurement teams, or external auditors as evidence of consistent security monitoring and SOC 2 alignment. CyberProtect does not certify SOC 2 compliance — it maps findings to controls and provides evidence documentation.

---

### Feature 5: Historical Reporting, Trend Tracking, and PDF Export

Every scan is stored permanently and accessible for comparison and export.

**Historical dashboard:**
- Security score trend line across all scans (e.g., Jan: 42 → Mar: 67 → Jun: 81)
- Month-over-month comparison view: "New findings this month," "Fixed since last scan," "Persistent findings"
- Total vulnerability count by severity over time

**Side-by-side scan comparison:**
- Owner can select any two scans and view a diff — what appeared, what was resolved, what persists

**PDF export:**
- Any individual scan report can be exported as a professionally formatted PDF
- PDF includes: business name, scan date, security score, all findings with severity and SOC 2 mapping, remediation instructions, and a disclaimer that CyberProtect findings are informational and do not constitute a formal security audit or SOC 2 certification
- Intended use: presenting to cyber insurers, enterprise clients, or internal stakeholders

---

## 4. Data Model

### `businesses`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | Business display name |
| created_at | Timestamp | |
| subscription_status | Enum | active, trialing, cancelled, past_due |
| subscription_plan | Enum | V1 has one plan |

### `accounts`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| business_id | UUID | FK → businesses |
| name | String | Account display name |
| domain_url | String | The URL/domain being scanned |
| scan_schedule_day | Integer | Day of month (1–28) scans run |
| created_at | Timestamp | |
| credentials_stored | Boolean | Whether optional auth credentials are on file |
| credentials_encrypted | Text | AES-256 encrypted, nullable |

### `users`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String | Unique |
| phone_number | String | For SMS alerts, nullable |
| password_hash | String | Bcrypt |
| created_at | Timestamp | |
| sms_notifications_enabled | Boolean | Default true |

### `account_memberships`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| account_id | UUID | FK → accounts |
| user_id | UUID | FK → users |
| role | Enum | owner, member |
| invited_at | Timestamp | |
| revoked_at | Timestamp | Nullable — set on revocation, triggers immediate session invalidation |

### `scans`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| account_id | UUID | FK → accounts |
| scheduled_at | Timestamp | When scan was due |
| started_at | Timestamp | |
| completed_at | Timestamp | Nullable until complete |
| status | Enum | scheduled, running, completed, failed |
| security_score | Integer | 0–100, nullable until complete |
| triggered_by | Enum | scheduled, manual |

### `findings`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| scan_id | UUID | FK → scans |
| title | String | Short name (e.g., "Reflected XSS on /search") |
| description | Text | Plain-English explanation of the vulnerability |
| severity | Enum | critical, high, medium, low, informational |
| affected_url | String | Specific URL/endpoint where found |
| remediation_steps | Text | Step-by-step fix instructions |
| soc2_controls | String[] | Array of SOC 2 control IDs (e.g., ["CC6.1", "CC7.2"]) |
| status | Enum | open, acknowledged, resolved |
| first_seen_scan_id | UUID | FK → scans — for tracking persistence across scans |
| resolved_scan_id | UUID | FK → scans — nullable, set when no longer detected |

### `notifications`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| scan_id | UUID | FK → scans |
| user_id | UUID | FK → users |
| channel | Enum | email, sms, in_app |
| sent_at | Timestamp | |
| status | Enum | sent, failed, delivered |

---

## 5. Out of Scope for V1

The following are explicitly excluded from V1. Any feature request touching these areas must be deferred to V2 or later.

| Feature | Reason Deferred |
|---|---|
| **Penetration testing** (active exploitation) | Legal liability — active exploitation without airtight written authorization agreements and legal framework is too risky for V1 |
| **Network/IP scanning** | Scope — focus is web application layer only in V1 |
| **User account & access permission scanning** | Scope — requires deep integrations with identity providers |
| **Third-party integration scanning** | Scope — requires OAuth flows and API key management at scale |
| **Auto-fix / AI-initiated changes to target systems** | Safety — AI cannot modify customer systems in V1; step-by-step instructions are provided instead |
| **Real-time / continuous scanning** | Cost and complexity — monthly cadence is sufficient for V1 |
| **Compliance frameworks beyond SOC 2** (ISO 27001, HIPAA, PCI-DSS) | Scope — SOC 2 serves the broadest SMB audience; others deferred |
| **Third-party tool integrations** (Slack, Jira, ticketing) | Scope — in-app + email + SMS is sufficient for V1 |
| **Mobile app** (iOS / Android) | Scope — web dashboard with SMS notifications covers mobile use in V1 |
| **Marketplace / consultant referrals** | Scope — V1 focuses on product, not services marketplace |
| **Owner account transfer** | Complexity — single owner per account in V1 |
| **API access for developers** | Scope — UI-first product in V1 |
| **SOC 2 certification** | CyberProtect maps to SOC 2 controls but does not issue certifications |

---

## 6. Success Metrics

At the 6-month mark post-launch, CyberProtect V1 is considered successful if all three targets below are met:

| Metric | Target | Measurement Method |
|---|---|---|
| **Paying businesses onboarded** | ≥ 100 businesses with active paid subscriptions | Count of `businesses` with `subscription_status = active` |
| **Critical vulnerability fix rate** | ≥ 80% of Critical findings marked resolved within 7 days of detection | % of `findings` where `severity = critical` AND `resolved_scan_id` set within 7 days of `first_seen_scan_id` |
| **Scan completion rate** | 95–97% of scheduled scans complete without error | % of `scans` where `status = completed` vs `status = failed` over rolling 30 days |

**Qualitative success signal:** Zero complaints about missed notifications. All critical findings reach owners via at least 2 of 3 channels successfully.

---

## 7. End-to-End Verification

The following scenario must execute successfully to verify the app works as a complete system. Run this as a manual QA walkthrough before any production launch.

---

### Scenario: "Acme Corp finds and resolves a critical vulnerability"

**Prerequisites:**
- Test business: "Acme Corp"
- Test domain: a controlled test web application with known, pre-planted vulnerabilities (e.g., a local DVWA instance or a dedicated test URL)
- Two test users: `owner@acme.com` (owner role) and `staff@acme.com` (member role)
- SMS-capable test phone numbers for both users

---

**Step 1 — Registration and Onboarding**
1. Navigate to the CyberProtect signup page
2. Register as `owner@acme.com`, create business "Acme Corp"
3. Add domain `https://test.acmecorp.com` to the account
4. Verify the account dashboard shows the domain registered and next scan date set
5. ✅ Pass: Account created, domain saved, scan scheduled

**Step 2 — Team Member Invitation**
1. As owner, invite `staff@acme.com` as a member
2. Log in as `staff@acme.com` and confirm access to the account dashboard
3. Confirm `staff@acme.com` cannot see billing settings or team management options
4. ✅ Pass: Member invited, role restrictions enforced

**Step 3 — Scan Execution**
1. Manually trigger a scan on the test domain (V1 must support manual trigger for testing)
2. Confirm scan status changes: `scheduled → running → completed`
3. Confirm `completed_at` is populated and `security_score` is set
4. ✅ Pass: Scan runs to completion without error

**Step 4 — Finding Detection**
1. Open the completed scan report
2. Confirm at least one Critical finding is present (planted XSS or SQLi on test app)
3. Confirm each finding has: title, description, severity, affected URL, remediation steps, and SOC 2 control mapping
4. ✅ Pass: Findings populated with all required fields

**Step 5 — Instant Alerting**
1. Confirm `owner@acme.com` receives an email within 5 minutes of scan completion
2. Confirm `owner@acme.com` receives an SMS within 5 minutes of scan completion
3. Confirm in-app notification badge is visible on next dashboard load
4. Confirm `staff@acme.com` also receives email notification
5. ✅ Pass: All three channels fire, both users notified

**Step 6 — SOC 2 Mapping**
1. Open the scan report and confirm the Critical finding is tagged with at least one SOC 2 control (e.g., CC6.1)
2. Navigate to the SOC 2 Readiness view and confirm the relevant control shows a failing status
3. ✅ Pass: SOC 2 mapping present and accurate

**Step 7 — Remediation and Resolution**
1. Follow the step-by-step remediation instructions for the Critical finding on the test app
2. Manually trigger a second scan
3. Confirm the previously Critical finding is no longer detected
4. Confirm `resolved_scan_id` is set on the finding in the second scan
5. Confirm the security score has improved between scan 1 and scan 2
6. ✅ Pass: Finding resolved, score improved

**Step 8 — Historical Comparison and PDF Export**
1. Navigate to the historical dashboard
2. Confirm security score trend shows improvement between scan 1 and scan 2
3. Use the side-by-side comparison view — confirm the resolved finding shows as "Fixed since last scan"
4. Export scan 1 as a PDF — confirm PDF contains business name, date, score, findings, remediation steps, SOC 2 mapping, and disclaimer
5. ✅ Pass: Trend data accurate, PDF exports correctly

**Step 9 — Access Revocation**
1. As owner, revoke `staff@acme.com`'s access
2. Attempt to load the dashboard as `staff@acme.com` (either in a new session or by refreshing an existing one)
3. Confirm access is denied immediately — redirected to login with an "access revoked" message
4. Confirm `staff@acme.com` receives no further notifications from subsequent scans
5. ✅ Pass: Revocation is immediate and complete

---

**All 9 steps passing = CyberProtect V1 is working end-to-end.**

---

*This specification was produced through a structured discovery interview. Any changes to scope, data model, or success criteria require written sign-off from the product owner before engineering begins.*
