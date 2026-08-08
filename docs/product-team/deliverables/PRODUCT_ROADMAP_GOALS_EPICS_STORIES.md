# SPM Product Review & Roadmap — Business Goals → Epics → User Stories — 2026-08-08

> Produced by the **Senior Product Manager** (`02_SENIOR_PRODUCT_MANAGER.md`) after (a) reading the existing
> business, technical, Jira, and architecture docs and (b) **driving the running application myself in a
> browser** across four roles and two tenants. This turns the company's intent into a prioritised roadmap of
> **Business Goals → Epics → User Stories with acceptance criteria** — ready to be created in Jira.
>
> **Numbering:** existing delivered/in-flight work keeps its real keys (`EP1`–`EP34`, `KAN-*`). New work I am
> proposing is numbered `EP35+` with story IDs like `EP35-S1` and marked **(proposed — create in Jira)**. No
> real Jira key is invented for new work.
>
> **Discipline:** every goal traces to evidence (product copy, a screen I saw, or a cited doc/finding). I guard
> the MVP — growth items are explicitly **Next/Later**, not **Now**. Engineering obeys `CLAUDE.md`.

---

## A. What I confirmed hands-on (grounds everything below)

I logged in as **SYSTEM_ADMIN** (Oliver Hartmann, cross-company), **PORTAL_ADMIN/HR/manager** (Ingrid
Mäkinen), an **employee** (Tõnis Rebane), and a **second-tenant admin** (Telia) and walked the live surface.

| Observation (Known — seen in the running app) | Why it matters |
|---|---|
| Login markets the product as **"People ops, built for scale — employees, competencies, org structure and vacations… from one unified platform."** Pillars listed: competency tracking, multi-company org, granular RBAC, leave lifecycle. | This *is* the company's stated intent. The roadmap must serve these four pillars, not drift. |
| Login shows **"Demo environment — no password required"** and one-click role personas. | **Answers kickoff §7 Q2:** email-only login (F1) is a *deliberate demo shortcut*. Product is **demo-grade today**, not a live prod deployment → hardening-first is correct, and F1–F4 are gate-blockers, not live incidents. |
| SYSTEM_ADMIN dashboard: **147 active employees**, live 5s refresh, headcount by location (8 offices) & business unit, **Top Skills by Coverage** (JavaScript 97 people avg 2.6/4, …), pending approvals. | The **skills/competency layer is a real differentiator**, front-and-centre — not a plain HRIS. Worth investing in (BG3). |
| Employee profile (Acme Corp branded): personal info, **skills with self-assessed vs manager-validated** distinction + proficiency bars, **solid- & dotted-line managers** (matrix org), **verified certifications** with expiry dates. | Self-service + competency + matrix reporting are mature. Cert **expiry** is captured but I saw no expiry *alerting* → opportunity (BG4). |
| Nav differs by role and by tenant (employee sees only Dashboard/Org Tree/Vacation/Leave Calendar/Profile; Telia admin's nav omits several features Acme's shows). | **Configurable per-company feature access works** — a genuine strength and a selling point (BG5 multi-tenant config). |
| Flagship flows present and coherent: **vacation request → team approval → leave calendar**, and **org-tree drag-and-drop → position-change approval**. | These are the two flows to harden to full compliance & a11y for the first customer (BG1/BG6). |

**Maturity (confirmed):** **P3 Functional Product**, feature-rich and polished, **pre-production**. RAG **Amber**.
The blockers to P5/P6 are the known security items (EP28) and the absence of customer-onboarding assets — not
missing features.

---

## B. North Star & supporting metrics (proposed)

**North Star:** *"% of target HR workflows (vacation, position-change, profile/skills self-service) completed by
users end-to-end without off-system/manual intervention."* It captures the product's own promise ("one unified
platform") and rewards adoption + trust, not feature count.

| Tier | Metric |
|---|---|
| Adoption | Weekly active employees / managers per tenant; % employees with a complete profile |
| Engagement | Vacation requests & approvals completed in-app; position-changes processed in-app |
| Efficiency | Median approval cycle time; % skills manager-validated; bulk-import success rate |
| Quality | Accessibility conformance (WCAG 2.2 AA pass rate on core flows); defect escape rate |
| Business | Tenants onboarded; time-to-first-value (signup → first workflow completed) |

---

## C. Business Goals (the spine of the roadmap)

| # | Business Goal | Serves which product pillar | Outcome | Horizon |
|---|---|---|---|---|
| **BG1** | **Be safe & trustworthy enough for a real customer** (Production-Ready). | RBAC / all | Real auth, CSRF, output/upload sanitisation; reproducible schema; real-DB CI. | **Now** |
| **BG2** | **Land the first customer** (Customer-Ready). | All | Onboarding, data import/migration, provisioning, training, support, hypercare. | **Now/Next** |
| **BG3** | **Own the competency-intelligence differentiator.** | Competency tracking | Skills gaps, competency frameworks, expiry alerting, development plans. | **Next** |
| **BG4** | **Complete the people-ops lifecycle.** | Org structure + leave | Onboarding/offboarding workflows, transfers, rehire, vacation balances/accruals. | **Next** |
| **BG5** | **Be enterprise-ready & connected.** | Multi-company + RBAC | SSO/OIDC, SCIM, HRIS import/export, calendar; multi-tenant scale (EP30). | **Next/Later** |
| **BG6** | **Be usable by the whole workforce** (a11y + mobile). | All (deskless employees) | WCAG 2.2 AA on core flows; mobile self-service. | **Now (a11y gate) / Next (mobile)** |

Priorities use Charter P0–P4 and MoSCoW. **BG1 and the a11y slice of BG6 are gate-blocking (Now).** Everything
in BG3–BG5 is deliberately deferred behind them — MVP first.

---

## D. Roadmap detail — Epics & User Stories

> Story acceptance criteria follow the existing `JIRA_EPICS_AND_STORIES.md` house style. Each story is sized
> MoSCoW and P0–P4.

### BG1 — Production-Ready (Now) → **existing EP28–EP32, EP34; do not re-create**

This goal is **already scoped** in the architecture backlog. I am adopting it wholesale as the Phase-0 gate,
not writing new epics. Drive these to done first:

| Epic (existing) | Must-close stories | Gate role |
|---|---|---|
| **EP28 Security Hardening** | KAN-148 real auth · KAN-149 CSRF · KAN-150+173 output-escaping · KAN-151 HTML/upload sanitisation · KAN-153 config | **P0 — blocks Production gate** |
| **EP31 Schema Source of Truth** | KAN-166 migration tool · KAN-167 single seeding owner | P1 |
| **EP32 Testing & CI** | KAN-168 real-DB tier · KAN-170 coverage floor · KAN-171 behavior tests | P1 |
| **EP29 Data Layer** | KAN-155 atomic writes · KAN-156 N+1s · KAN-158 directory pagination | P1/P2 |
| **EP34 Architecture** | KAN-178 app factory (enables test/stage/prod configs) | P2 |

*SPM note:* **KAN-148 should be delivered as SSO/OIDC** (see EP37-S1) — it closes F1 *and* delivers the
enterprise-auth customers will demand, instead of building throwaway password auth for a demo.

---

### BG2 — Customer-Ready — **EP35 (proposed — create in Jira)**

**EP35 — Customer Onboarding & Data Migration**
*Goal:* a new tenant can go from zero to running core HR without engineering help. *Why:* Customer-Readiness is
entirely absent today (Charter §4; kickoff §8 NO-GO). Builds on the existing **Bulk Import** feature I saw in nav.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP35-S1 | As a **new customer admin**, I want a guided tenant setup wizard (company, branding, locations, business units, roles) so I can stand up my org without a manual. | Wizard creates company + org scaffold + default roles/feature-access; resumable; validates required fields inline; ends with "invite users". | Must · P1 |
| EP35-S2 | As a **customer admin**, I want validated bulk employee import (CSV) with a dry-run preview so a bad file can't corrupt my data. | Upload → column-map → **dry-run diff** (create/update/error rows) → commit; row-level error report; atomic per batch (ties KAN-155); duplicate detection by employee #/email. | Must · P1 |
| EP35-S3 | As a **customer admin**, I want to bulk-provision user accounts & roles from the import so employees can log in on day one. | Accounts created with correct company scope + roles; invite/first-login flow; no PII in logs. | Must · P2 |
| EP35-S4 | As a **customer admin**, I want a data-migration mapping for our prior HRIS export so historical records come across. | Documented field mapping + importer for the common HRIS export shape; migration run is logged and reversible. | Should · P2 |
| EP35-S5 | As a **customer admin**, I want a known-limitations & getting-started guide surfaced in-app so my team knows what's supported. | In-app help panel + published admin/end-user docs; linked from the wizard. | Should · P3 |

**EP36 — Support, Adoption & Hypercare (proposed)**
*Goal:* the operational wrap a live customer needs. *Why:* Charter §4 Customer-Readiness; no support/feedback/
adoption instrumentation exists today.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP36-S1 | As a **customer admin**, I want an in-app feedback/issue channel so users can report problems without email. | Feedback widget → ticket store; ack to user; admin queue. | Should · P3 |
| EP36-S2 | As **HR leadership**, I want an adoption dashboard (WAU, profile completeness, workflow completion) so I can prove value. | Extends the existing analytics area with the North-Star supporting metrics (§B). | Should · P3 |
| EP36-S3 | As the **operator**, I want a runbook + hypercare checklist so launch issues are handled fast. | Runbook (deploy, rollback, common incidents) published; hypercare rota + severity SLAs defined. | Must (pre-launch) · P2 |

---

### BG3 — Competency Intelligence — **EP37 (proposed)**

**EP37 — Competency Frameworks & Skills Gaps**
*Goal:* turn the skills data I saw (self vs validated, top-skills-by-coverage) into decisions. *Why:* it's the
product's headline differentiator and already has rich data; the analytics exist but stop at description.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP37-S1 | As **HR**, I want a competency framework per role (required skills + target proficiency) so gaps are measurable. | Admin defines role→required-skills+level; company-scoped; drives the gap view below. | Should · P2 |
| EP37-S2 | As a **manager**, I want a skills-gap view for my team (have vs required) so I can plan development. | Per-team matrix of coverage vs target; export; respects company scope + feature access. | Should · P2 |
| EP37-S3 | As an **employee**, I want a development plan from my gaps so I know what to learn next. | Gap → suggested skills/certs to close it; visible on My Profile; no automated decisions (human-in-the-loop). | Could · P3 |
| EP37-S4 | As **HR leadership**, I want workforce skills-coverage trends over time so I can see capability building or eroding. | Time-series on top-skills coverage & validated-% by BU/location. | Could · P3 |

*Compliance gate:* any future **AI** scoring/matching on top of this is **EU AI Act high-risk / GDPR Art. 22** —
Strategist to gate behind human-in-the-loop, explainability, and bias testing before it enters the backlog
(kickoff Decision D-003). Not in this cycle.

---

### BG4 — Complete the People-Ops Lifecycle — **EP38, EP39 (proposed)**

**EP38 — Employee Lifecycle Workflows** *(join → transfer → promote → offboard → rehire)*
*Why:* Charter §1 lists these lifecycle events as must-handle; today I saw registration + position-change, but
no first-class **onboarding/offboarding** workflow or **transfer/rehire** handling.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP38-S1 | As **HR**, I want an onboarding checklist workflow for a new hire so nothing is missed before day one. | Configurable task list per company; assignees; status; ties to the register-employee flow. | Should · P2 |
| EP38-S2 | As **HR**, I want an offboarding workflow (access removal, exit date, asset return) so departures are clean and auditable. | Offboarding sets employment_status + exit date; revokes portal access; full audit entry; retention respected (BG links GDPR). | Must · P2 |
| EP38-S3 | As a **manager/HR**, I want a transfer flow (BU/location/manager) reusing the org-change engine so moves are consistent. | Transfers route through the existing sequential approval engine (`org_change`); no bypass; company-scoped. | Should · P2 |
| EP38-S4 | As **HR**, I want rehire to restore/relink a prior employee record so history isn't lost. | Rehire detects prior record; re-activates with new employment; preserves audit trail. | Could · P3 |

**EP39 — Vacation Balances, Accruals & Policy Depth**
*Why:* I saw request/approve/calendar and eligibility rules, but no visible **balance/accrual** engine —
kickoff/Jira note KAN-158/EP26 touch balance visibility; deepen it into real policy.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP39-S1 | As an **employee**, I want to see my leave balance and accrual before requesting so I don't over-book. | Balance = entitlement − taken − pending, per type/location; shown on the request form. | Should · P2 |
| EP39-S2 | As a **customer admin**, I want configurable accrual policies (annual entitlement, carry-over, pro-rata) so leave matches our HR policy. | Policy config per company/type; engine computes balances; boundary cases tested (join mid-year, part-year). | Should · P2 |
| EP39-S3 | As an **employee**, I want an iCal export of my approved leave so it's on my calendar. | Approved leave → iCal feed/download (Business doc §6 "calendar — not built"). | Could · P3 |

---

### BG5 — Enterprise-Ready & Connected — **EP40 (proposed) + existing EP30**

**EP40 — Identity, Provisioning & Integrations**
*Why:* Business doc §6 lists SSO/LDAP, HRIS import/export, calendar as **recommended/not-built**; enterprise
customers require SSO/SCIM; also the clean fix for F1.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP40-S1 | As an **IT admin**, I want SSO via OIDC/SAML so employees use corporate identity (and email-only login is retired). | OIDC/SAML login; JIT provisioning optional; **replaces** the demo email-login; closes F1/KAN-148. | Must (enterprise) · P1 |
| EP40-S2 | As an **IT admin**, I want SCIM user/role provisioning so joiners/leavers sync automatically. | SCIM 2.0 create/update/deactivate mapped to employees + roles + company scope. | Should · P2 |
| EP40-S3 | As a **customer admin**, I want HRIS export (CSV/API) so downstream payroll/BI systems get our data. | Scheduled/on-demand export; documented schema; company-scoped; auditable. | Could · P3 |

**Scale (existing EP30):** connection pooling (KAN-159), cross-request feature-access cache (KAN-160),
push-not-poll (KAN-161), shared object storage for logos (KAN-162), bounded background workers (KAN-163). These
back the "built for scale" promise — **Later**, after a first customer proves the flows.

---

### BG6 — Usable by the whole workforce — **EP33 (existing) + EP41 (proposed)**

**Accessibility (existing EP33 — gate-relevant, do first):** KAN-174 keyboard path for org-tree drag-drop
(F20), KAN-175 modal dialog semantics/focus trap (F21), KAN-172/173 shared JS modules with escape-by-default.
**WCAG 2.2 AA on the two flagship flows is a release gate (Charter §1), not polish.**

**EP41 — Mobile Self-Service (proposed)**
*Why:* HR-UX reality (Charter/UX role) — many employees are deskless with a phone; the employee nav is already
lean (Dashboard/Org Tree/Vacation/Leave Calendar/Profile), a good mobile target.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP41-S1 | As a **deskless employee**, I want to request leave and view my profile comfortably on a phone. | Core self-service flows pass mobile UX review (touch targets, no horizontal scroll); builds on existing EP22 responsive work. | Should · P2 |
| EP41-S2 | As a **manager**, I want to approve/reject vacation in one or two taps on mobile. | Approve/reject actionable from a phone; notification deep-links to the item. | Could · P3 |

---

## E. Sequencing (Now / Next / Later) & phase mapping

| Horizon | Goals / Epics | Ties to Delivery phase (`06_*`) |
|---|---|---|
| **Now (P0–P1, gate-blocking)** | BG1 (EP28/31/32/29/34) · BG6 accessibility slice (EP33 KAN-174/175/172/173) | **Phase 0 — Foundation & Hardening** |
| **Next (first customer)** | BG2 (EP35/EP36) · BG4 offboarding+transfer (EP38-S2/S3) · BG3 framework+gaps (EP37-S1/S2) · BG5 SSO (EP40-S1) | **Phase 1 — MVP/GA-lite → Phase 3 — Customer Launch** |
| **Later (grow & scale)** | BG3 depth (EP37-S3/S4) · BG4 balances/rehire (EP39, EP38-S4) · BG5 SCIM/HRIS/scale (EP40-S2/S3, EP30) · BG6 mobile (EP41) · any **compliance-gated AI** | **Phase 4 — Expansion → Phase 5 — Scale** |

---

## F. Decisions & open items for the SPM to confirm with the business

| # | Item | My recommendation | Needs |
|---|---|---|---|
| Q1 | Is there a target first customer / segment (SMB vs enterprise)? | Assume **enterprise-leaning** (multi-company + RBAC + SSO demand) → prioritise EP40-S1 SSO as the auth solution. | Product owner confirm. |
| Q2 | Deliver auth (KAN-148) as throwaway password login **or** go straight to SSO/OIDC (EP40-S1)? | **SSO/OIDC** — closes F1 and delivers enterprise value in one move. | Product owner + eng sizing. |
| Q3 | Is competency-intelligence (BG3) the intended wedge vs generic HRIS? | The product's own copy + dashboard say **yes** — invest in EP37 as the differentiator. | Strategist to RICE-rank vs BG4. |
| Q4 | Any AI ambitions? | **Defer** behind EU AI Act / GDPR Art. 22 gate (D-003). Do not enter this cycle. | Compliance/DPO validation when raised. |

---

## G. Immediate next actions (tasking)

1. **Delivery/Release Mgr:** fold BG1 into the Phase-0 gate; add EP35/EP36 to the Customer-Readiness checklist; keep the Release Gate at **NO-GO** until EP28 P0s close.
2. **Business Analyst:** write full acceptance criteria + traceability for EP35 (onboarding/import) and EP38-S2 (offboarding); open compliance gaps for GDPR retention/erasure on offboarding.
3. **UX:** design the EP35-S1 setup wizard and the EP35-S2 import dry-run; complete the a11y fixes (EP33) on the two flagship flows.
4. **UAT:** build test cases for EP35 import (happy/edge/adversarial CSV, tenant isolation) and the offboarding audit trail.
5. **Strategist:** RICE-rank BG3 vs BG4 vs BG5-SSO for the "Next" slot; keep AI out of scope this cycle.
6. **SPM (me):** confirm Q1–Q3 with the business, then approve the "Next" scope and re-task for Phase 1.

*All engineering obeys `CLAUDE.md` — feature-access model, company scoping, org-change invariants, and the
regression flow-test discipline. Nothing is "done" until pytest + the regression flow test pass.*
