# SPM Product Review & Roadmap — Business Goals → Epics → User Stories — 2026-08-08

> Produced by the **Senior Product Manager** (`02_SENIOR_PRODUCT_MANAGER.md`) after (a) reading the existing
> business, technical, project-management and architecture docs and (b) **driving the running application myself in a
> browser** across four roles and two tenants. This turns the company's intent into a prioritised roadmap of
> **Business Goals → Epics → User Stories with acceptance criteria**, promoted into
> [`../../project-management/BACKLOG.md`](../../project-management/BACKLOG.md) as each epic is scheduled.
> *(Corrected 2026-08-09: this file predates the Atlassian retirement of 8 Aug 2026. **Documentation lives in
> git**; `KAN-###` are local story IDs, not Jira issues — `CLAUDE.md` and `docs/project-management/README.md`.)*
>
> **Numbering:** existing delivered/in-flight work keeps its real keys (`EP1`–`EP34`, `KAN-*`). New work I am
> proposing is numbered `EP35+` with story IDs like `EP35-S1` and marked **(proposed — not yet in the backlog)**.
> An epic gets `KAN-###` story IDs when it is promoted into `BACKLOG.md`; the next free ID is **KAN-241**.
>
> **Discipline:** every goal traces to evidence (product copy, a screen I saw, or a cited doc/finding). I guard
> the MVP — growth items are explicitly **Next/Later**, not **Now**. Engineering obeys `CLAUDE.md`.

---

## ⚠️ AMENDMENT — 2026-08-09 — Security & login re-sequenced to the FINAL stage (Decision D-004)

**Direction from the product owner (2026-08-09):** *"Security and login are last priority until the last stage,
where all requirements are finalised and implemented — login and security only add complexity at this point."*

**SPM verdict: accepted, with a trigger clause.** I agree on the sequencing and I want the reasoning on record,
because this is a *rework-economics* decision, not a change in risk appetite:

- **Auth, CSRF and output-escaping are cross-cutting, not features.** KAN-149 touches **~44 state-changing
  endpoints**; KAN-150/173 touches **every `innerHTML` builder across 7+ templates**; KAN-151 touches the
  branding/upload surface. Every epic still ahead of us — EP35 import wizard, EP38 lifecycle workflows, EP39
  accrual engine, EP37 gap views — **adds new endpoints and new DOM builders to exactly those surfaces.**
  Hardening now means hardening the same surface twice and re-litigating escaping regressions on every new
  screen. Doing it once, over a frozen functional surface, is materially cheaper and more complete.
- **Real login actively slows the build.** The one-click demo personas are how the team, UAT and stakeholders
  exercise four roles across two tenants today (kickoff §7 Q2 — email-only login is a *deliberate* demo
  shortcut, already confirmed). Replacing it before the requirements settle taxes every subsequent
  demo/test cycle for zero functional gain.
- **This does not move the gate — it moves when we reach it.** Per the SPM guardrails I still will not
  recommend **GO** with an open P0. The Production-Ready gate stays **NO-GO**; EP28 simply becomes the
  *final* phase before that gate rather than the first.

**Trigger clause — these items snap back to live P0 immediately, no discussion, if ANY of the following becomes
true.** This is the condition under which the deferral is safe; it is not a standing exemption:

| # | Trigger | Because |
|---|---|---|
| T1 | The app becomes reachable from anything beyond localhost / a trusted private network | F1 (email-only session) becomes a live account-takeover path, not a gate item |
| T2 | Any **real employee PII** is loaded (replacing the synthetic seed data) | GDPR exposure; Charter §1 compliance is first-class |
| T3 | A named customer, pilot, or prospect demo runs on non-synthetic data | Customer-Readiness gate engages |
| T4 | Any account is created for a user outside the build team | Auth becomes a real trust boundary |
| **T5** | **Any real (non-synthetic) compensation value is entered for any employee, in any tenant — including a single manual entry by the build team "just to see how it looks"** | **Added 2026-08-09 with EP42 (SPM decision D-005).** A single real salary is more consequential than an entire synthetic directory. **This fires at a deliberately lower bar than T2: T2 requires a data *load*, T5 requires one row.** |

**Why T5, and why T2 was *not* tripped by EP42 (SPM ruling, 2026-08-09 — recorded because ducking it would have
been easier).** Building a compensation feature and populating it with synthetic salaries for synthetic people
does **not** load real PII. T2 is not tripped, EP42 builds in S3, and D-004's sequencing stands unchanged. What
changes is **the loss, not the probability**: T1–T4 were written when the worst case of a trigger event was the
exposure of names, org placement and leave dates. After EP42 the worst case of the *same* event is the exposure
of **every employee's pay** — the data class that produces individual grievance, works-council escalation and
press attention rather than a breach notification. A risk register that does not re-price when the asset changes
is decorative. Hence T5, at a lower bar.

**Two cheap safeguards that ride with EP42** (same logic as the existing list below — they cost nothing and do
not churn with features): `compensation`, `compensation_self` and `pay_equity` are seeded **disabled for every
tenant**, so R7's commercial switch doubles as a safety default; and a persistent **"Demo compensation data —
synthetic"** banner sits on every compensation screen while the environment is demo-grade.

**One consequence stated plainly:** the first time this is shown to a named prospect using their own pay figures,
or one real payroll extract is loaded, **S5 runs first**. That is T3 and T5 applied to the feature that was just
requested, and it is much better heard now than at the demo.

**Cheap safeguards that stay in force while deferred** (these cost nothing and do not churn with features):
KAN-152 ✅ secure runtime defaults stays; **KAN-153** (required DB config, no personal defaults) stays in the
current phase — it is a 1-file change with no feature coupling; the escaping already landed under KAN-150
(directory, org-tree, team, my-team) is **not** to be reverted; synthetic data only; demo/local network only.

**Standing engineering rule (free, not a project):** where the shared `escH()` helper already exists, new code
uses it. That costs nothing today and shrinks the KAN-173 sweep later. `CLAUDE.md` invariants — feature-access
model, company scoping, org-change rules — are **unaffected by this decision and remain non-negotiable**; they
are correctness and tenancy rules, not the security-hardening backlog.

**Open question this creates → for the product owner:** accessibility (EP33 KAN-174/175) was previously bracketed
with security as a "Now" gate item. It is **not** security, but it has the same rework economics — retro-fitting
a11y onto screens that are still changing gets redone. My recommendation is to treat WCAG 2.2 AA as a **design
standard applied to new work now** and schedule the retro-fit sweep alongside the final hardening phase. I have
**not** moved it unilaterally — see §F Q5.

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

| # | Business Goal | Serves which product pillar | Outcome | Horizon *(revised D-004)* |
|---|---|---|---|---|
| **BG1** | **Be safe & trustworthy enough for a real customer** (Production-Ready). | RBAC / all | Real auth, CSRF, output/upload sanitisation; reproducible schema; real-DB CI. | **Split:** non-security enablers (schema, CI, data-layer, factory) **Now** · security & login (EP28, EP40-S1) **Final phase — see D-004** |
| **BG2** | **Land the first customer** (Customer-Ready). | All | Onboarding, data import/migration, provisioning, training, support, hypercare. | **Now** |
| **BG3** | **Own the competency-intelligence differentiator.** | Competency tracking | Skills gaps, competency frameworks, expiry alerting, development plans. | **Now/Next** |
| **BG4** | **Complete the people-ops lifecycle.** | Org structure + leave | Onboarding/offboarding workflows, transfers, rehire, vacation balances/accruals. | **Now/Next** |
| **BG5** | **Be enterprise-ready & connected.** | Multi-company + RBAC | SSO/OIDC, SCIM, HRIS import/export, calendar; multi-tenant scale (EP30). | SSO **Final phase** (it *is* the login work) · SCIM/HRIS/scale **Later** |
| **BG6** | **Be usable by the whole workforce** (a11y + mobile). | All (deskless employees) | WCAG 2.2 AA on core flows; mobile self-service. | a11y **standard now, retro-fit sweep at the end** (pending Q5) / mobile **Next** |
| **BG7** | **Pay decisions this company can defend.** *(new — 2026-08-09; a **three-epic programme**, ordered **EP42 → EP44 → EP43**, ~**50 stories**, ~**8–9 months**)* | Core HR + org structure + RBAC + performance | **The job decides the step, the step decides base pay, and pay never decides the step** (amendment A6). Every employee on a company-defined job ladder with a current, effective-dated, auditable base pay record, plus **additional pay** as a separately-governed, attributed amount for the exceptions; pay moves with position and level through **one** governed approval; **Global HR re-authors the ladder's economics each year, which under A6 *is* the act of granting a rise**; a real performance review produces the judgement that moves people up it; and unexplained differences surface to a named owner before somebody else finds them. | **Now** (requirements, S1) · **Next** (build — EP42 W0 in **S2**, W1–W4 in **S3**; **EP44 in S3 after EP42**; **EP43 last**) |

**Why BG7 is a new goal rather than an extension of BG4** (SPM, 2026-08-09 — argued in full in
`EP42_SPM_SCOPE_AND_DECISIONS.md` §1.2). BG4 is about lifecycle **events**; compensation is a **data class and a
decision discipline** that intersects several of them. It carries a compliance regime no other goal carries (pay
transparency, works-council consultation on job classification, and the tightest read model in the product); it
carries a **commercial control** — R7 exists because the owner intends to expose or withhold it per tenant, and
no other goal has packaging in its requirements; it is measured differently (coverage and defensibility, not
process completion); and it is the first goal whose failure mode is reputational rather than operational.
**The concession:** EP42's wave W3 (pay inside position change, level change, four-eyes) serves **BG7 and BG4
jointly**, and it settles a debt BG4 already owed — the EP38 epic title has promised "promote" since this roadmap
was written and no story ever carried it.

Priorities use Charter P0–P4 and MoSCoW. **Under D-004 the functional backlog (BG2–BG4) is pulled forward and
the security/login slice of BG1+BG5 is pushed to the final phase.** The Production-Ready **gate itself has not
moved** — it is still NO-GO until EP28 closes; we simply reach it last, over a frozen functional surface.

---

## D. Roadmap detail — Epics & User Stories

> Story acceptance criteria follow the existing `project-management/BACKLOG.md` house style. Each story is sized
> MoSCoW and P0–P4.

### BG1 — Production-Ready → **existing EP28–EP32, EP34; do not re-create** *(split by D-004)*

This goal is **already scoped** in the architecture backlog — I adopt it wholesale rather than writing new
epics. **D-004 splits it in two.** The non-security half stays **Now**, because it is what makes a churning
functional backlog cheap to build (reproducible schema, real-DB tests, atomic writes, an app factory). The
security half moves to the **final phase**.

**Now — foundation enablers (keep, they reduce the cost of everything else):**

| Epic (existing) | Must-close stories | Why it stays Now |
|---|---|---|
| **EP31 Schema Source of Truth** | KAN-166 migration tool · KAN-167 single seeding owner | EP35/EP38/EP39 all add tables. Without version-tracked migrations, schema churn becomes drift. **P1** |
| **EP32 Testing & CI** | KAN-168 real-DB tier · KAN-170 coverage floor · KAN-171 behavior tests | New workflow engines must be verified against a real schema, not mocks. **P1** |
| **EP29 Data Layer** | KAN-155 atomic writes · KAN-156 N+1s · KAN-158 directory pagination | KAN-155 is a **direct dependency of EP35-S2** (atomic bulk import). **P1/P2** |
| **EP34 Architecture** | KAN-178 app factory | Enables test/stage configs for the above. **P2** |
| **EP28 (partial)** | **KAN-153** required DB config | 1-file change, zero feature coupling — no reason to defer it. **P2** |

**Final phase — security & login gate (deferred by D-004, unchanged in scope):**

| Epic (existing) | Must-close stories | Gate role |
|---|---|---|
| **EP28 Security Hardening** | KAN-148 real auth · KAN-149 CSRF · KAN-150+173 output-escaping · KAN-151 HTML/upload sanitisation | **P0 — blocks the Production gate, executed last** |
| **EP40-S1 (proposed)** | SSO/OIDC — **this is the delivery vehicle for KAN-148** | P0, same phase |

*SPM note (unchanged, now scheduled later):* **KAN-148 should be delivered as SSO/OIDC** (see EP40-S1) — it
closes F1 *and* delivers the enterprise auth customers will demand, instead of building throwaway password auth
for a demo. Deferring it to the end makes this *more* likely, not less: by then the role/tenant model the SSO
mapping has to target is finalised.

*Entry condition for this phase:* the functional backlog is **feature-frozen** — no new endpoints or DOM
builders queued. That freeze is what makes a single hardening sweep complete instead of perpetual.

---

### BG2 — Customer-Ready — **EP35 (proposed — not yet promoted into the backlog)**

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
the kickoff note and KAN-158/EP26 touch balance visibility; deepen it into real policy.

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
| EP40-S1 | As an **IT admin**, I want SSO via OIDC/SAML so employees use corporate identity (and email-only login is retired). | OIDC/SAML login; JIT provisioning optional; **replaces** the demo email-login; closes F1/KAN-148. | Must (enterprise) · P0 — **final phase per D-004**; keep demo personas working until this lands |
| EP40-S2 | As an **IT admin**, I want SCIM user/role provisioning so joiners/leavers sync automatically. | SCIM 2.0 create/update/deactivate mapped to employees + roles + company scope. | Should · P2 |
| EP40-S3 | As a **customer admin**, I want HRIS export (CSV/API) so downstream payroll/BI systems get our data. | Scheduled/on-demand export; documented schema; company-scoped; auditable. | Could · P3 |

**Scale (existing EP30):** connection pooling (KAN-159), cross-request feature-access cache (KAN-160),
push-not-poll (KAN-161), shared object storage for logos (KAN-162), bounded background workers (KAN-163). These
back the "built for scale" promise — **Later**, after a first customer proves the flows.

---

### BG6 — Usable by the whole workforce — **EP33 (existing) + EP41 (proposed)**

**Accessibility (existing EP33):** KAN-174 keyboard path for org-tree drag-drop (F20), KAN-175 modal dialog
semantics/focus trap (F21), KAN-172/173 shared JS modules with escape-by-default.
**WCAG 2.2 AA on the two flagship flows remains a release gate (Charter §1), not polish** — D-004 does not
weaken the gate. What is in question is *when* the retro-fit sweep runs (§F Q5): my recommendation is a11y as a
**design standard on all new work from now**, with the sweep executed alongside the final hardening phase, since
KAN-172/173 (shared JS modules + escape-by-default) is the same code as the KAN-150/173 escaping work and should
be done once, together.

**EP41 — Mobile Self-Service (proposed)**
*Why:* HR-UX reality (Charter/UX role) — many employees are deskless with a phone; the employee nav is already
lean (Dashboard/Org Tree/Vacation/Leave Calendar/Profile), a good mobile target.

| Story | User story | Acceptance criteria | MoSCoW · P |
|---|---|---|---|
| EP41-S1 | As a **deskless employee**, I want to request leave and view my profile comfortably on a phone. | Core self-service flows pass mobile UX review (touch targets, no horizontal scroll); builds on existing EP22 responsive work. | Should · P2 |
| EP41-S2 | As a **manager**, I want to approve/reject vacation in one or two taps on mobile. | Approve/reject actionable from a phone; notification deep-links to the item. | Could · P3 |

---

### BG7 — Pay decisions this company can defend — **EP42** *(added 2026-08-09)*

**EP42 — Compensation, Job Architecture & Pay Equity**
*Goal:* every employee on a company-defined job ladder with a governed, effective-dated pay record; pay decided
together with the move that causes it; unjustified gaps found before somebody else finds them.
*Why:* the product holds **no** compensation data of any kind, and `employees.job_title` is free text with no
catalogue behind it. Every pay decision its users make is therefore made off-system — the largest single
off-system intervention left in the people-ops surface, sitting inside two workflows the portal already runs end
to end. It is the direct answer to the product owner's request of 2026-08-09 (asks **R1–R7**).

**Twenty-three stories in five waves** *(18 at Wave 3; **A1** added KAN-206/207/208; the **Wave-5 reconciliation** added KAN-209; **A2** added KAN-210)*. Full detail — decisions, 532 acceptance criteria, ADR-014…023, every screen,
and 300 test cases — lives in the five `EP42_*` deliverables in this directory and in the EP42 section of
[`../../project-management/BACKLOG.md`](../../project-management/BACKLOG.md). Summary only here:

| Wave | Stage | Delivers | Stories |
|---|---|---|---|
| **W0** | **S2** | Platform, plus two debts that are not EP42's fault and one data task: a **P0 Critical defect fix**, the shared-shell a11y that EP38 never landed, synthetic gender so the gap check has data, the tenant switch made central (R7), and effective dating (which **unblocks KAN-185**) | KAN-203 · KAN-204 · KAN-208 · KAN-188 · KAN-189 |
| **W1** | S3 | The job ladder **with each step's responsibilities and expectations**, everybody placed on a **step**, and **the manager-authored roadmap every employee can read** (**R6**). **A complete, shippable slice with no compensation data in it at all** | KAN-190 · KAN-191 · KAN-207 |
| **W2** | S3 | Pay markets, **the step pay-point model**, **ladder re-basing**, the compensation record, the visibility model, the backfill, **then fitting every employee's step to their actual pay and releasing the gate** (**R1, R2**) — **the minimum shippable slice for the epic as a whole** | KAN-199 · KAN-206 · KAN-210 · KAN-193 · KAN-194 · KAN-195 · KAN-209 |
| **W3** | S3 | Pay inside position change, level change, four-eyes on money, progression (**R3, R4**) | KAN-196 · KAN-197 · KAN-198 · KAN-192 |
| **W4** | S3 | Pay equity: the engine (**now measuring pay against the step, not against the group**), the register, bands, history (**R5**) | KAN-200 · KAN-201 · KAN-205 · KAN-202 |

**Three things the roadmap must carry forward:**

1. **R6 is a prerequisite of R5, and it is measured.** Acme has 46 employees across **41 distinct free-text job
   titles**, of which exactly **one** has three or more people in it; Telia 100 across 75. A "same position"
   comparison keyed on `job_title` produces comparison groups of size one. The ladder supplies the grouping key.
2. **W4 is gated on KAN-168** (real-DB test tier, EP32, ⬜ not started). **SPM ruling: if KAN-168 slips, W4
   slips** — EP42 ships through W3, satisfying six of the seven asks, and the equity engine waits. An equity
   engine certified against mocks is not an acceptable alternative.
3. **EP42 enlarges S4.** Roughly 18 stories, 3 feature codes, 14 new tables and ~26 endpoints all enter the S5
   hardening sweep and the WCAG retro-fit. **The feature-freeze date moves out by the size of this epic.** That
   is the price of the request; it is worth paying, and it should be paid knowingly.

### Amendment A1 — the product owner's answers, 2026-08-09

**OQ-1 CONFIRMED — progression is not automatic**, and the model is richer than we specified: every step carries
its own **defined responsibilities and expectations**; the **manager authors the next step as a forward-looking
roadmap for that specific employee**, whose stated purpose is transparency, so the employee must be able to see
it; and **step counts are configured per level per company**, with an employee entering a level at step `.0`.

**OQ-3 REINTERPRETED — "5%" is the pay increment between consecutive steps, not a pay-equity threshold.** The
reference value stops being the **group median** and becomes the **step's configured pay point**, so the primary
check is absolute rather than statistical: **the `n ≥ 3` minimum and the 80% coverage gate are withdrawn** for it,
and the thin-data problem largely dissolves. The gender-gap check remains statistical and keeps its group sizes.
R5's original ask is still satisfied by construction — two people at the same step are measured against the same
point. Three new stories (**KAN-206** step pay points, **KAN-207** the roadmap, **KAN-208** synthetic gender) and
a fourth feature code (`job_architecture`, because **the manager authors the roadmap and managers must not need
write access to everyone's salary to do it**).

**One boundary stated plainly, because the owner anchored progression to the performance review, the probation
period and the mid-term goal review — none of which exists in this product:**

> **EP42 records that a step change happened at a review. It does not build the review.**

No cycles, no scheduling, no reminders, no goals, no ratings, no calibration, no probation entity. A
**Performance, Goals & Reviews** epic is recorded in **Later** below — unnumbered and unscoped. If it is wanted,
that is a conversation about a new epic, not an expansion of this one.

### Wave-5 reconciliation — 2026-08-09

Two rulings at roadmap level. **(1) The nearest-step rule.** UAT proved that the tolerance-based finding boundary
left a *dead zone* — because the tolerance had to be strictly less than half the step increment, **a perfectly
fitted ladder still flagged ~20% of the workforce**. A finding is now raised when an employee's pay is **nearer to
a different step's pay point than to their own**; the dead zone becomes zero by construction, a fitted backfill
raises **no findings on day one**, and four separate Wave-4 conflicts dissolve at once. **(2) A build-order
defect, and it was the SPM's:** the story that fits steps to pay was scheduled a wave before the stories that
create pay points *and* pay data. Fitting is now **KAN-209 at the end of W2**, and the ladder-fitted-and-reviewed
gate ships **closed** so the intervening window is safe.

### Amendment A2 — the product owner's second answer, 2026-08-09

**OQ-5 CLOSED — base salary only** (his *"at this point"* makes it an extensibility rule, not a permanent
exclusion) · **the job-family model is CONFIRMED unchanged** — his worked example maps onto the existing
`job_families` → `job_levels` design exactly, so no positions table and nothing to rebuild · **the employee's job
level may be hidden per company policy**, a narrow switch over one field that leaves the ladder and all its
expectations fully visible, defaults to disclosed, and is labelled *"do not display"* rather than *"hide"*
because an employee can still infer their level by matching expectations.

**And one genuinely new capability: an annual hike cycle — which is EP43, not EP42.**

**EP43 — Annual Compensation Review Cycle** *(new)*
*Goal:* the second trigger for a pay change. EP42 moves pay because somebody's **job** changed; EP43 moves it
because the **year** changed — a company-set hike percentage driven by market movement, company income and
individual performance, differentiated per employee, approved once, applied on an effective date.

| Story | Scope | MoSCoW · P |
|---|---|---|
| KAN-216 | **Performance-input policy** — company-defined bands and multipliers, employer-authored on an admin page, **nothing predetermined and nothing suggested**, versioned and inspectable without exposing individuals' data (works councils) | Must · P2 |
| KAN-217 | **Per-employee performance input** — a manager records one band per person per cycle. *Said plainly: this is a performance rating, and it is the one line EP43 deliberately crosses.* Single-purpose, row-scoped, no history surface, absent from every other surface | Must · P2 |
| KAN-211 | The cycle: per company, per year, `DRAFT → OPEN → APPROVED → APPLIED → CLOSED` | Must · P2 |
| KAN-212 | The three inputs — market movement **per pay market**, company affordability, and the performance band from KAN-216/217 | Must · P2 |
| KAN-213 | Per-employee proposals and the manager worksheet, with the budget as a **warning, not a block** | Must · P2 |
| KAN-214 | **One** cycle-level approval satisfying the four-eyes rule, then an atomic bulk apply | Must · P2 |
| KAN-215 | Close-out, and **re-basing the ladder** by the market component | Must · P2 |

**Why a sibling epic rather than an EP42 W5** (SPM judgement, `EP42_SPM_SCOPE_AND_DECISIONS.md` §18.4): EP42 is
already 23 stories and ~14–16 weeks and has been amended twice in one day — a recurring annual process with a
performance input would take it past the size defensible as one commitment; it is a **process**, not a data
model, and closer in shape to EP38 than to EP42; and the split lets **§14.5's performance boundary stay true for
EP42** while EP43 owns its own explicit, narrow crossing of it. **The one real counter-argument — that an
un-re-based hike degrades EP42's equity check — is answered by separating the capability from the process:
effective-dated pay points and ladder re-basing are KAN-206 and KAN-210, inside EP42.** A company can therefore
re-base manually on the day it grants a hike. **EP42 shipping without EP43 is safe rather than degrading, and
EP43 is the natural descope if S3 runs long.**

### Amendment A3 — 2026-08-09 — a performance module is authorised, and BG7 becomes a programme

**The owner has authorised a performance module**, which **supersedes the SPM's §14.5** (*"EP42 records that a
step change happened at a review; it does not build the review"*). Recorded as superseded by owner decision, not
dropped: §14.5's job was to stop performance management arriving *by accident* inside an amendment, and it did
that — it did not stop him choosing the scope **on purpose, with the cost visible**.

**His phrase reads two ways and they are a quarter apart, so the choice is back with him.** **(a)** a
manager-entered performance band per cycle, feeding the hike and nothing else — **2 stories, ~2–3 weeks, no
delay**, inside EP43. **(b)** full performance management — cycles, goals, self-assessment, calibration, ratings
history — **≈20–25 stories, 12–16 weeks**, its own epic **EP44**, and under his own instruction it would go
*first*, pushing the hike cycle out by **roughly a quarter**. **SPM recommends (a)** and the team builds it
meanwhile; the decisive argument is his own conditional — *"implement this first if required **if this the
blocker**"* — because under (a) nothing is blocked for a fortnight whereas **(b) becomes the blocker he was
routing around**.

**BG7 is therefore a multi-epic programme and the roadmap should show it as one:** **EP42** (23 stories,
~14–16 weeks) → **EP43** (7 stories) → **EP44** (named, unscoped, only if he picks (b)). Under (a) the programme
is ~30 stories and ~5 months; under (b), ~52 stories and ~8–9 months.

**The Charter §1 gate, kept visible so it is not crossed by increment:** nothing in EP43 scores, ranks or
automatically decides anything about a person — a manager enters a band, a company-configured multiplier turns
it into a number, a human approves the result. **The EU AI Act / GDPR Art. 22 gate engages the moment anyone
proposes a suggested rating, a ranked list, a forced distribution, or any model output influencing pay.**

**Also settled by A3:** the hike policy is **employer-authored, with nothing predetermined and nothing
suggested** · the employee-disclosure switch governs the **step, not the level** — the job title already
discloses the level (*Junior Software Fullstack Engineer* **is** level 2), so the original switch would have
hidden nothing while claiming to · and **`/ladder` as a main-nav surface is confirmed**, with **job family** now
an explicit part of what it shows. **The ladder is public; the pin on the ladder is not.**

### Amendments A4, A5 and A6 — 2026-08-09 — **the owner overturned the pay/step model, and BG7 becomes a three-epic programme**

**Full re-ruling in `EP42_SPM_SCOPE_AND_DECISIONS.md` §22. Five things belong at roadmap level.**

**1. The corrected model, and it only runs one way.** He rejected the model the team built in the strongest
terms he has used — *"No you have not got correct!!"*:

> **job content & responsibility → STEP → BASE PAY.** Never base pay → step.

A step is an assignment about **what work someone does**, made by a human at a review; base pay **is** that
step's defined value × FTE. **The system must never propose, infer, imply, suggest, pre-select or "fit" a step
from a salary figure.** The **nearest-step rule is withdrawn in full** — as a mechanism *and* as a description,
because *"paid closer to step 2.2"* is a claim about somebody's step. **KAN-191's step-fitting backfill is
forbidden**: the step now comes from the **manager's assessment against the written step expectations**, in W1,
with no money involved, and **KAN-209 is repurposed into a human pay reconciliation** at the end of W2 that
opens with the totals (*"31 below their step value by €214,000"*) and requires one recorded disposition per
person — **align · attribute the surplus as additional pay · accept a residual deviation with a reason**.
Day-one findings are still zero, but now **because a human decided each case** rather than because the system
quietly re-labelled everyone's step to match their salary. *(This also closes CFL-42-41, the SPM's own Wave-4
build-order defect, rather than working around it.)*

**2. `additional pay` — the owner's own mechanism, and it makes the rest work.** Base and additional are two
distinct, separately-governed amounts. Tom is at step 2.1 on €51,000 and about to resign; local HR grants 5%.
**Tom stays a 2.1**, his base stays €51,000, and €2,550 is recorded as additional pay with a reason. The
retention save no longer corrupts the ladder, the fairness check becomes a clean equality, and the "dead zone"
disappears — it existed only because pay was being mapped back onto steps. New story **KAN-218**, W2.

**3. The hike rate is per step-transition, per year, set by Global HR** — *"from 2.0 to 2.1 the hike will be 2%
this year while from 2.1 to 2.2 it will be 2.4"*. So the rate belongs on the **transition**, year-scoped with
history, not on the level. Compounding survives and generalises: €50,000 → €51,000 → **€52,224**. **And the
re-basing question, asked three times and never answered, is dead rather than deferred** — it assumed an
across-the-board hike drifting away from a static ladder, and under A6 **moving the ladder and paying people
are the same act**, which promotes KAN-210 from a maintenance action to the mechanism by which a company grants
a rise. One narrower, genuinely new question replaces it (*what does an employee who stays on the same step all
year earn next year?*), put to him with numbers. A fifth feature code, **`pay_policy`**, separates **Global HR**
(the ladder's economics) from **local HR** (one person's pay) using the mechanism `CLAUDE.md` already mandates.

**4. Advise, do not block — his principle, with a boundary the roadmap should carry.** *"Local HR managers can
always override the system recommendation because otherwise there might be a situation that employee may
leave."* Adopted as a standing rule for BG7 — **and explicitly bounded**: judgements about an **amount** are
advisory and overridable with a recorded actor, a mandatory reason **code**, an audit row carrying no figure,
and **visibility to the approval chain at decision time**. **Integrity controls are not overridable**, and that
list — subject≠initiator, subject≠decider, initiator≠approver on money, approver≠approver, ≥2 satisfiable
levels, no SYSTEM_ADMIN bypass — **is closed and may not be eroded by citing this principle, because the
principle is about amounts and says nothing about actors.** Override rates become data a company should see,
with a 40% configuration-review tripwire: a company overriding most flags has a mis-set ladder, not an
exceptional workforce.

**5. The programme, stated once and honestly.** His original request was *hold salary, put people on job
levels, flag a 5% difference*. It is now:

| | Stories | What it is |
|---|---|---|
| **EP42** — Compensation, Job Architecture & Pay Equity | **23** | The pay record, the ladder, the fairness check *(unchanged in count: KAN-218 added, KAN-205 moved to Later, KAN-209 repurposed, KAN-208 made conditional)* |
| **EP44** — Performance Management | **22** | The review that produces the judgement — **entered, not named** |
| **EP43** — Annual Compensation Review Cycle | **5** *(was 7)* | The annual round — **reduced by A6**, which collapsed the per-employee hike percentage |
| **BG7 total** | **~50 stories, ~8–9 months** | **Ordered EP42 → EP44 → EP43** |

**He has chosen every increment with the cost shown, which is his right. The cumulative shape is stated here
once, as a fact, rather than as a per-amendment reminder.**

### Amendment A4/A5 — **EP44 — Performance Management** *(entered; the owner chose (b) and accepted the delay)*

*Goal:* build the review that EP42 records the context of and EP43 consumes the output of. **Decision D-006:**
the SPM sized a 2-story performance *input* against full performance *management* and **recommended (a) with
Confidence High**; the owner chose **(b)** — *"I want a full performance-management capability (cycles, goals,
calibration)"* — and confirmed it with the cost accepted in his own words: *"go ahead with full implemenation
cycle as Product owneer accepting the delay."* **Recorded as "recommended (a), owner chose (b)" and not
re-litigated.** **§14.5 is superseded by owner decision** — it stopped performance management arriving *by
accident* and did not stop him choosing it *on purpose*; that is the boundary working, not the ruling failing.

| Wave | Stories | Delivers |
|---|---|---|
| **P0** | KAN-219 · KAN-220 | The review cycle and who is in it |
| **P1** | KAN-221 · KAN-222 · KAN-223 | Goals, narrative check-ins (**never a completion percentage — that is a rating with a friendlier name**), company templates |
| **P2** | KAN-224 · KAN-225 · KAN-226 · KAN-227 · KAN-228 | Self- and manager assessment, the company-defined **versioned** rating scale, the form configurator, and the conversation record — **`Confirm we discussed this`, never `Accept`** |
| **P3** | KAN-229 · KAN-230 · KAN-231 · **KAN-232** | Calibration as a **human forum**; distribution **shown, never enforced**; every calibration change attributed; and **the EU AI Act / Art. 22 gate as a story in the build, not a note after it** |
| **P4** | KAN-233 · KAN-234 · KAN-235 · KAN-236 · KAN-237 | Ratings history with its own negative-visibility suite, the employee's own view and right of reply, **the pay seam** (gated by KAN-232), **the step seam** into EP42's `review_context`, and completion reporting only |
| **P5** | KAN-238 · KAN-239 · KAN-240 | Works-council inspectability, retention and erasure, and bias testing that **measures and reports but never auto-corrects** |

**Two compliance items are carried as design inputs rather than notes, and this is the difference between EP44
being buildable in Germany and not.** **(1)** A full performance capability **with calibration**, feeding
**pay**, is the doorstep of *"a decision with legal or similarly significant effect"* — so human-in-the-loop
attestation, an explainability record, no automated ranking and bias testing are **stories** (KAN-232,
KAN-240), and **a configurable forced curve is refused at product level, not left to a tenant**. **(2)
Works councils (OQ-8) escalate a third time and are now plausibly market-gating** for Germany and the Nordics,
where the seed data lives: the **policy** — scale, forms, calibration rules, and the rating-to-pay mapping —
must be versioned and inspectable **without exposing any individual's data** (KAN-238), because a council may
need to agree it before the first cycle runs. **A launch blocker, not a build blocker.** Flagged for DPO/legal
validation; nothing here is legal advice.

**EP43 shrinks to five stories, and A6 is why.** The per-employee annual hike percentage was an artefact of the
same wrong model. Under A6 pay moves for exactly three reasons — the step moved, the ladder moved, or an
exception was **attributed** — so KAN-212 is withdrawn (merged into EP42's rate schedule and KAN-216) and
KAN-217 is withdrawn (superseded by EP44). **EP43 becomes a round-management epic, not a differentiation one**,
it is sequenced last, and it remains the designated descope if S3 runs long. **Nothing is blocked while EP44
runs:** EP42's KAN-210 lets a company move the whole ladder today, and under A6 that **is** an across-the-board
rise.

**⚠ One process finding at roadmap level (`CFL-42-60`).** *"Pay position implies step position"* was **never in
the owner's request** — it was a team inference, correctly labelled as one when it was made, that then acquired
a decision number and was reinforced by four specialist reviews and two SPM reconciliations because every
tasking brief said **apply** rather than **test**. Three changes now bind every epic: a **Load-Bearing Premise
Register** with each premise tagged **OWNER / EVIDENCE / TEAM** and a falsifying question named for every TEAM
row · **origin tagging on every requirement** · and **"Premises I challenged" as a required section in every
specialist report**. Plus one line for the SPM's own checklist: **agreement between specialists tasked from the
same brief is not evidence.**

**The same pass found a second unexamined premise.** The **gender pay-gap check** has no owner requirement
behind it either — it came from the SPM's reading of the EU Pay Transparency Directive, and it carries a change
to live vacation-eligibility behaviour and an Art. 9 data-protection clearance. It is **kept, re-labelled a
team requirement, descoped to a separable conditional slice, and put to him.** His original ask is satisfied
without it: under A6 two people at the same step in the same market earn the same base **by construction**.

**This epic closes three long-standing open items** — backlog #3 ("promote" has no story → KAN-197, and the type
is named `LEVEL_CHANGE` because downward moves are permitted), #4 (transfer vs the EP27 drag-and-drop boundary →
one modal, one endpoint, one engine, three entry points), and #5 (segregation of duties → KAN-203 + KAN-198) —
and **repays EP38** by resolving CFL-4, which is what `AC-185-07` on KAN-185 is currently blocked on.

---

## E. Sequencing (revised by D-004, 2026-08-09)

The old order was *harden → build*. The revised order is **build → freeze → harden**. Nothing is removed from
scope; the security/login block moves from first to last.

| Stage | Goals / Epics | Exit criteria | Ties to Delivery phase (`06_*`) |
|---|---|---|---|
| **S1 — Requirements finalisation** *(Now)* | BA + UX + Strategist close the functional scope: EP35, EP36, EP37, EP38, EP39, EP41 written to full acceptance criteria; **EP42 — six amendment rounds, A1…A6, 2026-08-09**; **EP44 outline entered, full requirements exercise to follow**; product owner answers Q1/Q3 (§F) and EP42's four remaining questions | Functional scope signed off; no open "we might also…" items. **For EP42 specifically, S1 closes when the four gates in `EP42_SPM_SCOPE_AND_DECISIONS.md` §13.1 clear, and the Wave-7 amendment round for A4–A6 (§22.14) has landed in all four specialist documents.** **EP44's requirements exercise is now OPEN** — the owner confirmed the shape by choosing Option C on 10 Aug 2026 with the capacity cost in front of him (D-008), which is precisely the agreement this gate was waiting for. The gate existed because the last three amendments cost what they cost when specification ran ahead of agreement; it is satisfied, not bypassed. **P0–P2 acceptance criteria first**, because those are the stories Option C runs in parallel | Phase 1 intake |
| **S2 — Foundation enablers** *(Now, parallel to S1)* | EP31 (KAN-166/167) · EP32 (KAN-168/170/171) · EP29 (KAN-155 ✅/156/158) · EP34 (KAN-178) · EP28 **KAN-153 only** · **EP42 W0 (KAN-203 · KAN-204 · KAN-208 · KAN-188 · KAN-189)** | Schema rebuildable + versioned; real-DB test tier green; atomic writes in place (**KAN-155 ✅ done**); **the tenant feature switch resolved centrally; the P0 self-approval defect closed; the shared-shell a11y landed; KAN-185 unblocked**. **KAN-168 is now P0 here — it hard-blocks EP42 W4** | **Phase 0 (non-security half)** |
| **S3 — Build the functional product** *(Now/Next)* | BG2 EP35 + EP36 · BG4 EP38 (S2/S3 first) + EP39 · BG3 EP37 (S1/S2) · BG6 EP41 · **BG7 (⚠ D-008, Option C — TWO PARALLEL TRACKS): EP42 W1→W2→W3→W4 on the critical path, with EP44 P0–P2 ALONGSIDE W1–W3, then the rest of EP44 → EP43** | All finalised requirements implemented; pytest + regression flow test green per `CLAUDE.md`; **a11y applied as a standard to new screens**. **EP42 W2 is its minimum shippable slice; W4 does not open until KAN-168 has landed.** **⚠ SUPERSEDED BY D-008 (10 Aug 2026, owner chose Option C): EP44's P0–P2 now runs PARALLEL to EP42 W1–W3, not after EP42.** The reason the serial order looked safe was the statement that *"nothing in EP42 needs a performance rating"* — true of a rating, but it **missed the seam**: EP42's KAN-192 carries a mandatory `review_context` whose `PERFORMANCE_REVIEW` option points at nothing until EP44's KAN-236. The owner objected to exactly that, and Option C closes it by using slack that already existed — KAN-192 is the LAST story in W3, and the two epics share no tables. **KAN-192 is now gated on EP44 being able to close a review cycle**; if that track slips, KAN-192 waits. Costs +1 SNR +1 MID for ~8–10 weeks and brings the hike cycle in at ~26–30 weeks rather than ~30–36. Full reasoning, including a retracted engineering recommendation, in `BACKLOG.md` D-008. **EP43 starts after EP44** (except KAN-211/215, which may parallelise if capacity allows — a Delivery call, not a dependency) **and is the designated descope if this stage runs long**; EP42's KAN-210 is the manual fallback and under amendment A6 moving the ladder **is** granting a rise | Phase 1 — MVP/GA-lite |
| **S4 — Feature freeze** | No new endpoints or DOM builders queued | Written freeze declared by SPM | Gate into S5 |
| **S5 — Security, login & hardening sweep** *(FINAL — D-004)* | **EP28 in full** (KAN-148 auth via **EP40-S1 SSO**, KAN-149 CSRF, KAN-150+173 escaping, KAN-151 sanitisation) · EP33 a11y retro-fit sweep (pending Q5) | Production Readiness checklist green; UAT signs off flagship flows; **only now can the Production gate go GO** | **Phase 2 — Production Readiness → Phase 3 — Customer Launch** |
| **Later (grow & scale)** | BG3 depth (EP37-S3/S4) · BG4 rehire (EP38-S4) · BG5 SCIM/HRIS (EP40-S2/S3) · EP30 scale · **BG7 depth: total compensation, pay-transparency statements, statutory gap reporting, and KAN-205 salary bands** (descoped from EP42 by A6 — with base pay *being* the step's defined value, a min/max envelope answers approximately what the step value answers exactly) · **the gender pay-gap check (Check B) is parked as a conditional slice, not Later** — it is specified and separable, and it is with the owner because it was never his requirement · any **compliance-gated AI** | — | Phase 4 → Phase 5 |

**S5 is not optional and not reducible.** Deferring it is a sequencing choice justified by the demo-grade,
synthetic-data status quo (D-001). Any trigger T1–T4 in the amendment above pulls S5 forward immediately,
regardless of where S3 has got to.

---

## F. Decisions & open items for the SPM to confirm with the business

| # | Item | My recommendation | Needs |
|---|---|---|---|
| Q1 | Is there a target first customer / segment (SMB vs enterprise)? | Assume **enterprise-leaning** (multi-company + RBAC + SSO demand) → EP40-S1 SSO is the auth solution when S5 runs. **Now urgent:** a named customer trips trigger T3. | Product owner confirm. |
| Q2 | Deliver auth (KAN-148) as throwaway password login **or** go straight to SSO/OIDC (EP40-S1)? | **ANSWERED (2026-08-09).** SSO/OIDC, **and scheduled in S5, not now** — D-004. Deferral strengthens the choice: the tenant/role model SSO maps onto will be final by then. | Closed. |
| Q3 | Is competency-intelligence (BG3) the intended wedge vs generic HRIS? | The product's own copy + dashboard say **yes** — invest in EP37 as the differentiator. **Now blocking S1**: functional scope can't be frozen until this is settled. | Strategist to RICE-rank vs BG4 — **needed to close S1**. |
| Q4 | Any AI ambitions? | **Defer** behind EU AI Act / GDPR Art. 22 gate (D-003). Do not enter this cycle. | Compliance/DPO validation when raised. |
| **Q5** | **New (D-004):** does accessibility (EP33 KAN-174/175) move to the final sweep with security, or stay a per-screen "Now" requirement? | **Move the retro-fit sweep to S5** (it shares code with the escaping work — KAN-172/173), **but apply WCAG 2.2 AA as a design standard to every new screen built in S3** so the sweep stays small. The gate is unchanged either way. | **Product owner decision** — I have not moved it unilaterally. |
| **Q6** | **New (D-004):** who confirms the environment stays demo-grade (localhost/private network, synthetic data only) for the duration of S1–S4? | Assign an owner. The whole deferral rests on triggers T1–T4 **and now T5** staying false; unowned, that assumption rots silently. | **Delivery/Release Manager** to own as a standing risk-register entry. **T5 extends this ownership to "no real pay figure, ever, including one".** |
| **Q7** | **EP42 / EP44 / EP43 (BG7), 2026-08-09.** Six rounds of answers — **A1…A6** — have closed OQ-1, OQ-3, OQ-5, the step-disclosure switch and the performance sizing. **A6 overturned the epic's central mechanism** (*"No you have not got correct!!"*): **the job decides the step, the step decides base pay, and pay never decides the step.** **Four questions remain, and they are on one page written as worked examples with his own numbers, per his standing instruction** (`EP42_SPM_SCOPE_AND_DECISIONS.md` §22.13): **Q1** does the entry value of a level move each year — *what does Anna, who stays at step 2.1 all year, earn next year?* · **Q2** Global vs local HR — *can Lars in Oslo grant additional pay to a Hamburg employee?* · **Q3** is a discretionary per-employee percentage still wanted · **Q4** did he ever ask for a **gender pay-gap check**. Carried from earlier rounds: OQ-2, OQ-4, OQ-6, OQ-7, OQ-9 and **OQ-8 (works councils)**. | **All four carry a recommended default the team is building against, so none of them blocks.** **Q1 — C** (employer-authored each year, no automatic rise, staleness warning at 18 months; B silently freezes everyone who does not move a step and nothing would notice) · **Q2 — A** (two permissions, one HR role, via the new `pay_policy` feature code; organisational scoping is a separate epic and is **not** being built on this evidence) · **Q3 — A** (no — step moves and additional pay cover both cases, **which is why EP43 drops from 7 stories to 5**) · **Q4 — park it** (it was the SPM's inference from the EU Pay Transparency Directive, never his requirement, and his original ask is satisfied without it because two people at the same step now earn the same base **by construction**). **OQ-8 is now the highest-value unanswered question in the programme** — performance-related pay with calibration across Germany and the Nordics is plausibly **market-gating**; a launch blocker, not a build blocker. **OQ-5 is closed** and no open question now forces a rewrite. | **Product owner** (Q1–Q4, OQ-2/4/6/7/8/9) · **DPO/legal** (DPO-2 blocks the retention class; DPO-1 travels with Q4). |

---

## G. Immediate next actions (re-tasked under D-004, 2026-08-09)

1. **Delivery/Release Mgr:** re-cut the phase plan to **S1–S5** (§E) — the Phase-0 gate is now the *non-security*
   enabler set only, and EP28+EP40-S1 become the S5 pre-production gate. Keep the Release Gate at **NO-GO**
   (unchanged — D-004 does not touch it). **Add triggers T1–T4 to the Risk Register with a named owner (Q6),**
   and add "environment stays demo-grade / synthetic data only" as a monitored standing risk.
2. **Business Analyst:** priority shifts to **closing S1**. Full acceptance criteria + traceability for EP35
   (onboarding/import), EP38-S2 (offboarding), EP39-S1/S2 (balances/accruals) — plus GDPR retention/erasure gaps
   on offboarding. **Nothing can be frozen until these are written.**
3. **UX:** design the EP35-S1 setup wizard and the EP35-S2 import dry-run. **Apply WCAG 2.2 AA as a design
   standard to every new screen now** (cheap at design time); hold the EP33 retro-fit sweep for S5 pending Q5.
4. **UAT:** test cases for EP35 import (happy/edge/adversarial CSV, tenant isolation) and the offboarding audit
   trail. **Note:** UAT continues to run against demo personas — that is now the *supported* path until S5.
5. **Strategist:** RICE-rank BG3 vs BG4 to settle **Q3**, which is on the S1 critical path. SSO drops out of the
   "Next" ranking entirely — it is scheduled in S5. AI stays out of scope.
6. **Engineering (Architect):** keep the standing rule — **new DOM code uses the existing `escH()` helper**. Do
   not start KAN-148/149/151; do proceed with KAN-153, KAN-155, KAN-166/167, KAN-168, KAN-178.
7. **SPM (me):** confirm **Q1, Q3, Q5, Q6, Q7** with the business; declare the S4 feature freeze in writing when S3
   completes; then convene the S5 hardening phase.

**Added 2026-08-09 — EP42 (BG7).** Full tasking, by wave and by role, is in
`EP42_SPM_SCOPE_AND_DECISIONS.md` §13. The four items that belong on *this* plan:

8. **Delivery/Release Mgr:** **schedule KAN-168 with a date, inside S2** — it hard-blocks EP42 W4, and if it
   cannot be committed to then W4 is descoped from this cycle **now** rather than discovered later. Add **T5** and
   EP42 risks **R-13** (KAN-188 blacks out both tenants, CI green throughout), **R-14** (the four-eyes control
   ships and does nothing) and **R-15** (the gender-gap check has no data) to the Risk Register with owners.
9. **Senior Architect:** publish the amended **ADR-016** first — it gates EP42 W1 — and reword `CLAUDE.md`'s
   org-change invariant 2 in the same commit as KAN-203, because **the headline invariant is right and the code
   is wrong**: today an HR_ADMIN can raise a position change for themselves and approve it.
10. **Engineering:** **KAN-203 (P0) and DEF-42-1 start immediately** — both are pre-existing defects with no EP42
    dependency. Nothing else in EP42 starts until the §13.1 gates clear.
11. **Standing gate:** **a compensation demo without the "the visibility model is unenforceable under demo auth"
    disclosure in its written script is NO-GO.** The visibility model is a *correctness* control, not a security
    control, until KAN-148 lands.

**Added 2026-08-09 — amendments A4, A5 and A6.** Full tasking in `EP42_SPM_SCOPE_AND_DECISIONS.md` §22.14. Five
items belong on *this* plan:

12. **SPM (me):** put the **four-question one-pager (§22.13)** in front of the product owner — worked examples,
    real names, real numbers, a distinguishing outcome and a recommendation each, per his standing instruction.
    Abstract framing has now failed three times on the same question and it is not going to be tried a fourth.
13. **BA · Architect · UX · UAT:** run the **Wave-7 amendment round (§22.14)**. Each brief names the sections
    A4–A6 invalidate in your own document and what to write instead. **Every one of you returns a "Premises I
    challenged" section — it is a required deliverable, not an optional extra**, and it must contain at least
    one premise you checked **at source** (his words, the code, the database) with the result stated either way.
14. **Delivery/Release Mgr:** re-cut the phase plan for **50 stories across three epics, ordered EP42 → EP44 →
    EP43**. **R-15 comes off the critical path** (the gender-gap check is now a conditional slice and KAN-208
    leaves W0, taking R-19's vacation side effect with it). **Add R-20** (a step assessment done badly at
    speed), **R-21** (additional pay becomes the dumping ground) and **R-22** (EP44 crosses the Art. 22 line by
    increment) to the Risk Register with named owners, and **escalate R-18** — an undescribed ladder now blocks
    the backfill rather than merely reading poorly.
15. **Everyone, standing:** the **Load-Bearing Premise Register** applies from now on — max ten rows per epic,
    each premise tagged **OWNER / EVIDENCE / TEAM**, a falsifying question named for every TEAM row, and **no
    TEAM premise load-bearing across more than one wave without a validating answer.** Requirements carry their
    origin as a column. **Agreement between specialists tasked from the same brief is not evidence.**

*All engineering obeys `CLAUDE.md` — feature-access model, company scoping, org-change invariants, and the
regression flow-test discipline. Nothing is "done" until pytest + the regression flow test pass.*
