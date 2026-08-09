# EP38 — Employee Lifecycle Workflows — Requirements & Acceptance Criteria

> **Owner:** Business Analyst (`../03_BUSINESS_ANALYST.md`) · **Date:** 2026-08-09 · **Status:** Draft for SPM review
> **Unblocks:** Roadmap §G.2 — *"Full acceptance criteria + traceability for … EP38-S2 (offboarding) … plus GDPR
> retention/erasure gaps on offboarding. Nothing can be frozen until these are written."*
> **Stage:** S1 — Requirements finalisation (roadmap §E). This document is an input to the S1 scope freeze.
>
> **House style:** acceptance criteria follow `../../project-management/BACKLOG.md` — one summary row per story in
> the standard `Story ID | User Story | Acceptance Criteria | Priority` table, expanded below into numbered,
> individually testable criteria. Every criterion has an ID (`AC-<story>-<nn>`) and appears in the traceability
> matrix (§10).
>
> **Guardrails obeyed:** `../../CLAUDE.md` is authoritative — feature-access model, company scoping, and the
> org-change invariants are **not** re-litigated here. Where a requirement touches one of those invariants it is
> called out explicitly (§4.6, §7.3). This document specifies **behaviour**, not schema or implementation —
> table design, migrations and job scheduling are the Senior Architect's (`ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md`).
> Legal items are flagged for **DPO/legal validation**; nothing here is legal advice (Charter §9.7).

---

## 1. Scope

| Story | Title | MoSCoW · Priority (from roadmap §D BG4) | Covered here |
|---|---|---|---|
| **KAN-183** | Onboarding checklist workflow (EP38-S1) | Should · P2 | Full (§5) |
| **KAN-184** | Offboarding workflow (EP38-S2) | **Must · P2** | Full (§6) — the substance of this document |
| **KAN-185** | Transfer via the existing org-change engine (EP38-S3) | Should · P2 | Full (§7) |
| **KAN-186** | Rehire (EP38-S4) | Could · P3 — roadmap §E **Later** | Outline only (§8), by direction |

**Epic-level out of scope** (none of the four stories delivers these; do not let them leak in):
recruitment/ATS and offer management · contract generation or e-signature · payroll, final pay, severance
calculation · asset/equipment inventory and returns tracking *(recorded as a checklist task only — the portal
is not an asset register)* · external identity provisioning (AD/Google/email account creation — that is EP40-S2
SCIM) · background checks · promotion and job-title/grade change *(see **OQ-1** — unallocated scope)* ·
cross-tenant employee movement (§7.5) · undo/reversal of a completed offboarding (**OQ-6**).

---

## 2. Verified current-state baseline

Everything in §4–§9 is written against this. Each row is **Known** — verified in the code/schema at the cited
location on 2026-08-09, not taken from documentation.

| # | Fact | Evidence | Consequence for EP38 |
|---|---|---|---|
| B1 | `employees.employment_status` is constrained to `ACTIVE / INACTIVE / RESIGNED / TERMINATED`, defaults `ACTIVE`; `exit_date date` exists and is nullable. | `database/schema.sql:339-362` | No schema change needed to record a leaver. Semantics are undefined today — §4.5 defines them. |
| B2 | **Roughly twenty read paths hard-filter `employment_status='ACTIVE'`** across directory, dashboard, org tree, search, analytics, skills intelligence, notifications, org-change pickers. | `app/helpers.py:130,133,136,179,199,326` · `app/routes/dashboard.py:26,60,68,77,85` · `app/routes/admin.py:78,244,353,356,713,730,749` · `app/routes/org.py:56,76,85` · `app/routes/company.py:64` · `app/services/search_service.py:63,136` · `app/services/notification_service.py:73` · `app/services/org_change_service.py:88` | Setting a non-ACTIVE status **is** the removal mechanism for directory, tree, dashboards, search and pickers. No per-view suppression work is needed. |
| B3 | **Login does NOT check `employment_status`.** `login()` authenticates on `LOWER(u.email) = %s AND u.is_active` only. Only the demo-tile helper `_login_demo_data()` filters `ACTIVE`. | `app/routes/auth.py:84-97` vs `:33` | **The roadmap/task premise that "login already requires ACTIVE" is false.** Access revocation must set `users.is_active = FALSE`. Status alone leaves the leaver able to log in. Logged as **CFL-1** (§9). |
| B4 | **There is no audit table anywhere in the schema.** The only history is effective-dating on `manager_relationships` / `employee_org_assignments`, plus `org_change_approvals`. | `database/schema.sql` — no `audit*` relation among the 47 tables | EP38-S2 must introduce auditing. Content requirements: §4.4. |
| B5 | The org tree CTE anchors and recurses on `employment_status='ACTIVE'`, joining children via `tree t ON t.id = mr.manager_id`. | `app/helpers.py:166-204` | A non-ACTIVE manager is absent from `tree`, so **their entire subtree becomes unreachable** — reports do not merely lose a card, they vanish from every tree rooted above the leaver. Drives §4.1. |
| B6 | The ancestor endpoint requires each ancestor to be `ACTIVE`. | `app/routes/org.py:70-91` | A report of an offboarded manager loses their whole upward breadcrumb and "navigate up" affordance. |
| B7 | A vacation request can only be reviewed by the employee recorded in `vacation_requests.manager_id`: `WHERE id=%s AND manager_id=%s`. There is **no admin override path**. | `app/routes/vacation.py:433-448` | If the recorded manager leaves, every PENDING request naming them is permanently un-actionable. Drives §4.2. |
| B8 | `vacation_requests` has **no `company_id`**; tenancy is derived through `employees.company_id`. Same for `manager_relationships` and `employee_org_assignments`. | `database/schema.sql:726-748, 394-410, 290-304` | Every EP38 query touching these must join `employees` to scope by company. §3.3. |
| B9 | `org_change_service._step_approver_user_ids` resolves an `EMPLOYEE` step to `users WHERE employee_id=… AND is_active`, and a `ROLE` step to active users of active employees in the company. | `app/services/org_change_service.py:78-93` | Deactivating a leaver's account silently empties an approval step → the request stalls with no eligible approver. Drives §4.2(d). |
| B10 | `org_change_workflow_steps.approver_employee_id` is **`ON DELETE CASCADE`**; `users.employee_id`, `vacation_requests.employee_id`, `manager_relationships` (both sides), `org_change_requests.employee_id`, `employee_org_assignments`, `employee_skills`, `employee_certifications` are all `ON DELETE CASCADE` on `employees`. | `database/schema.sql:1856-2184, 2316-2330` | **Hard-deleting an employee destroys vacation and org-change history and silently deletes a company's approval step.** Decisive argument for anonymise-never-delete (§4.3). |
| B11 | `vacation_requests.manager_id → employees(id)` has **no** cascade (default `NO ACTION`). | `database/schema.sql:2336` | A hard delete of anyone who has ever been a named approver fails at the FK — deletion is not even reliably possible. Reinforces §4.3. |
| B12 | `employees.email` and `employees.employee_number` are **globally UNIQUE** (not per company); `users.employee_id`, `users.email`, `users.username` are UNIQUE. | `database/schema.sql:982-1002, 1310-1338` | Anonymisation must mint globally unique tokens. Rehire cannot create a second `users` row for the same employee — it must reuse the existing one. |
| B13 | There is **no route that changes `employment_status`** after registration. Registration hardcodes `'ACTIVE'`; the only related control is `POST /api/admin/toggle-user`, which flips `users.is_active` and nothing else. | `app/routes/admin.py:178-186, 313-331` | Offboarding is entirely new behaviour. `toggle-user` is not a substitute — it leaves the employee ACTIVE everywhere. |
| B14 | Feature access is `role_feature_access` AND `company_role_feature_access`; SYSTEM_ADMIN is granted everything automatically. Seeded feature codes: `employee_profiles`, `org_structure`, `user_accounts`, `skills`, `vacations`, `reports`, `company_settings`, `system_config`, plus `skills_intelligence` (migration 03) and `org_change` (migration 06). | `app/auth.py:38-113` · `database/seed_rbac.sql:34-41` · `database/migrations/03,06` | EP38 needs its own feature codes (§3.2). Route guards must be `@require_feature_access`, never hardcoded role lists (`CLAUDE.md`). |
| B15 | SYSTEM_ADMIN employee records have `company_id IS NULL` by design; admin screens scope through `session['admin_company_id']`. | `app/routes/auth.py:19` · backlog KAN-68 · `app/routes/admin.py:_company_scope` | Company-less records are a real edge case for every EP38 screen (§3.3, AC-184-31). |
| B16 | The application has no scheduler. Background work is ad-hoc `threading.Thread` (email, page-view logging). | `app/services/notification_service.py`, `app/services/page_tracker.py`; backlog KAN-163 | Anything date-triggered (future-dated exit, retention expiry) needs a capability that does not exist yet → **OQ-4**, and constrains §4.5 / §6.3. |
| B17 | `employee_search_index` is **read but never written** by application code. | `app/services/search_service.py:57` — no `INSERT`/`UPDATE` anywhere | Search exclusion for leavers is delivered by the `ACTIVE` filter at `search_service.py:63`, not by index maintenance. Erasure must still delete the row (§4.3). |
| B18 | `used_days` counts `PENDING` + `APPROVED` when enforcing the annual limit. | `app/routes/vacation.py:383` | Auto-cancelling a leaver's requests releases entitlement — relevant to rehire in the same calendar year (§8). |

---

## 3. Cross-cutting requirements (apply to all four stories)

### 3.1 Non-negotiable inherited invariants
1. **CC-1** No route in EP38 uses a hardcoded `@require_roles(...)` list for a feature page or feature API. All
   feature routes use `@require_feature_access('<code>', '<action>')`; all nav/UI affordances use
   `{% if has_feature_access('<code>', '<action>') %}`. (`CLAUDE.md` — Access Control.)
2. **CC-2** No sub-flags. No `enabled_for_hr`-style per-feature role gate may be introduced. (`CLAUDE.md` —
   "Past mistakes to never repeat".)
3. **CC-3** SYSTEM_ADMIN bypasses feature checks automatically via `_load_feature_access()`; no EP38 code
   re-implements that bypass.
4. **CC-4** Any query listing or resolving *roles* for a company filters `company_id = %s::uuid` **only** —
   never `OR company_id IS NULL`.
5. **CC-5** Position changes continue to run through `app/services/org_change_service.py`. EP38 must not
   re-implement approval logic inline. The one deliberate, bounded exception is §4.6.

### 3.2 Feature access model for EP38
6. **CC-6** Two new portal features are registered in `portal_features` with a numbered migration under
   `database/migrations/` and matching `setup_db.py` seeding (per `CLAUDE.md` "Adding a new feature"):

   | Code | Label | Governs | Seeded `role_feature_access` defaults |
   |---|---|---|---|
   | `employee_lifecycle` | Employee Lifecycle | Onboarding checklists (S1), offboarding (S2), rehire (S4) | `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w+d · `SOLID_LINE_MANAGER` r (own reports' onboarding tasks) · all others none |
   | `audit_log` | Audit Log | Reading lifecycle audit records | `PORTAL_ADMIN` r · `HR_ADMIN` r · all others none |

   `SYSTEM_ADMIN` needs no row (CC-3). Defaults are a **ceiling**; each tenant's PORTAL_ADMIN may narrow or
   widen them through the existing Feature Access tab, and the implementation must respect that with no extra
   checks (CC-2).
7. **CC-7** Transfers (S3) are gated by the **existing** `org_change` feature — no new code, no new gate.
   Deleting/aborting a request continues to use the existing rules.
8. **CC-8** Write actions that mutate employment state (offboard, rehire, status correction) require the `w`
   action; erasure/anonymisation requires `d`. A role with `r` only can view lifecycle screens and see the
   audit trail but can change nothing, and every mutating API returns `403` with no state change.

### 3.3 Tenant isolation (all stories)
9. **CC-9** Every EP38 query is company-scoped with `company_id = %s::uuid`. Tables without a `company_id`
   column (`vacation_requests`, `manager_relationships`, `employee_org_assignments` — B8) are scoped by joining
   `employees` and filtering there.
10. **CC-10** The subject of any lifecycle action must belong to the actor's company. A PORTAL_ADMIN or HR_ADMIN
    of company A acting on an employee of company B receives `403`, no record is read back in the response body,
    and **no** row is written — including no audit row naming the foreign subject beyond the rejected attempt.
11. **CC-11** Every picker (successor manager, task assignee, transfer target) lists only `ACTIVE` employees of
    the **same** company, mirroring the existing org-change prefill behaviour (`app/routes/org_change.py:135`).
12. **CC-12** A SYSTEM_ADMIN performing a lifecycle action must have a company context selected
    (`session['admin_company_id']`); with "All Companies" selected, mutating lifecycle actions are refused with
    a message naming the reason. Read-only views may span companies.
13. **CC-13** Employee records with `company_id IS NULL` (SYSTEM_ADMIN accounts — B15) are actionable **only**
    by SYSTEM_ADMIN, are never listed to a PORTAL_ADMIN or HR_ADMIN, and never appear in any company's lifecycle
    screen or count.
14. **CC-14** Audit rows carry a non-null `company_id`. A PORTAL_ADMIN of company A querying the audit log
    receives zero rows for company B under every filter combination, including free-text search.

### 3.4 General quality bars
15. **CC-15** Every multi-step lifecycle mutation is **atomic**: either all of it lands or none of it does. A
    failure mid-sequence leaves `employment_status`, `users.is_active`, manager relationships, org assignments,
    vacation requests and org-change requests exactly as they were, and surfaces a specific error. (Depends on
    KAN-155 `transaction()` — §11 DEP-1.)
16. **CC-16** Every mutating endpoint is idempotent against double submission: replaying the same offboarding
    for an already-offboarded subject returns `409` with the existing state, not a second set of changes or
    audit rows.
17. **CC-17** Personal data never appears in application logs or error messages beyond the employee id and
    employee number (roadmap EP35-S3 "no PII in logs" — same bar).
18. **CC-18** New screens meet **WCAG 2.2 AA as a design standard** at build time (roadmap D-004 / §F Q5):
    labelled form controls, keyboard-operable confirmations, focus moved to the dialog, no colour-only status.
19. **CC-19** New DOM builders use the existing global `escH()` helper (standing engineering rule, D-004).
20. **CC-20** `pytest` and both regression suites (`tests/ui/test_browser.py`, `tests/ui/test_vacation_workflow.py`)
    pass with zero failures, and the suites are **extended** to cover the flows EP38 changes — an offboarded
    employee must be asserted absent from directory, org tree and dashboard counts, and asserted unable to
    authenticate (B3). (`CLAUDE.md` — regression flow test.)

---

## 4. Decisions resolved (the five engineering would otherwise guess)

Each decision below is a **rule**, stated once here and enforced by the numbered criteria in §5–§8.

### 4.1 D1 — Orphaned reports: **block completion, force reassignment inline, apply atomically**

**Rule.** Offboarding a subject who has one or more *current* `SOLID_LINE` reports **cannot be submitted** until
a successor manager has been chosen for those reports inside the offboarding flow. The reassignment and the
status change are applied in a single transaction. "Allow and flag" is rejected; "block with no path" is rejected.

**Why (not a preference — a data-integrity failure).** Because the tree CTE recurses through the manager chain
and filters `ACTIVE` at every level (B5), an offboarded manager does not leave a dangling card — **their entire
subtree disappears** from any tree rooted above them, and each report loses their whole ancestor breadcrumb (B6).
Reports would also remain in `direct_report_ids()` for a person who no longer exists in any view, so `/my-team`
and manager dashboard counts would keep counting them for a manager who cannot log in. Flagging a defect the
user cannot see is not a control.

**Sub-rules.**
- **R1.1** Successor must be an `ACTIVE` employee of the same company, and must not be the subject.
- **R1.2** If the chosen successor is themselves one of the subject's direct reports, that person is re-pointed
  to the **subject's own current SOLID_LINE manager** (the grandparent), not to themselves — the `chk_not_self_manager`
  constraint would otherwise abort the whole transaction (`database/schema.sql:406`).
- **R1.3** If the subject has no current manager and the successor is one of their reports, the successor becomes
  a tree root; the flow states this in plain language before confirmation and proceeds.
- **R1.4** Reassignment closes each existing row (`is_current=FALSE`, `effective_to = exit_date`) and inserts a
  new current row for the successor — the same shape `org_change_service.apply_change` uses.
- **R1.5** **`DOTTED_LINE` reports:** a successor is **optional**. Dotted lines do not structure the tree (the CTE
  uses `SOLID_LINE` only). Where no successor is given, the relationships are closed
  (`is_current=FALSE`, `effective_to = exit_date`) and the count of closed dotted lines is reported and audited.
- **R1.6** The subject's own relationships — as employee and as manager, both line types — are all closed with
  `effective_to = exit_date`. No `is_current=TRUE` row may reference the subject in either column afterwards.
- **R1.7** Per-report override: the flow allows a different successor per report (bulk-set-all with individual
  override), because a departing manager's team is often split.
- **R1.8** Reassignment under offboarding does **not** go through the org-change approval chain — see §4.6 for
  why, and for the boundary that keeps this from being a bypass.

### 4.2 D2 — In-flight work

**(a) The leaver's own vacation requests.**
- **R2.1** All `PENDING` requests of the subject are set to `CANCELLED` with a system note
  `"Cancelled automatically — employee offboarded on <exit_date>"`. Rationale: they can never be actioned
  (the approver may also be gone) and leaving them PENDING keeps consuming entitlement (B18) and manager queues.
- **R2.2** `APPROVED` requests **wholly after** `exit_date` are set to `CANCELLED` with the same note — leave that
  cannot be taken must not sit in the calendar or the team schedule.
- **R2.3** `APPROVED` requests that **start on or before** `exit_date` are left **untouched**, whatever their end
  date. They are a record of leave actually taken and are payroll-relevant. This deliberately does **not** reuse
  the self-service rule at `app/routes/vacation.py:299` ("cannot withdraw a request that has already started") —
  that guard protects the *employee* endpoint and must not be invoked by the offboarding service.
- **R2.4** The confirmation step lists every request that will be cancelled (type, dates, working days, status)
  and the count, before the actor confirms. Nothing is cancelled silently.
- **R2.5** `REJECTED` and already-`CANCELLED` requests are not modified.

**(b) Requests where the leaver is the named approver (`vacation_requests.manager_id`).**
- **R2.6** Every `PENDING` request naming the subject as `manager_id` is **re-pointed, not cancelled** — an
  employee's leave request must survive their manager's departure (B7: nobody else can approve it, not even an
  admin).
- **R2.7** Re-point target, in order: (i) the successor chosen for that requester in D1; (ii) if the requester is
  not one of the subject's reports, that requester's own current `SOLID_LINE` manager; (iii) if neither resolves,
  any active `HR_ADMIN` of the company.
- **R2.8** If (iii) also fails to resolve (a company with no active HR_ADMIN), the offboarding is **blocked** with
  a specific error naming the affected requests and the missing role. It is not completed with stuck requests.
- **R2.9** Each new approver receives an in-app notification via the existing `user_notifications` mechanism
  naming the requester, the dates, and why the request moved to them.
- **R2.10** Every re-point is audited as a field-level change of `vacation_requests.manager_id` (old → new).

**(c) `org_change_requests` where the leaver is the subject (`employee_id`).**
- **R2.11** All `PENDING` requests for the subject are set to `CANCELLED` (a status the existing constraint
  already allows) with the reason recorded. **No change is applied** — a move cannot be applied to someone who
  has left, and applying one would resurrect assignments the offboarding just closed.
- **R2.12** `APPROVED` / `REJECTED` / already-`CANCELLED` requests are untouched — they are history.

**(d) `org_change_requests` where the leaver is a named approver.**
- **R2.13** For every `PENDING` request in the company whose **current or any later** step is an `EMPLOYEE` step
  naming the subject, `approver_employee_id` is re-pointed using the same order as R2.7. Later steps are
  re-pointed at offboarding time, not deferred — deferral just relocates the stall.
- **R2.14** If no target resolves, offboarding is **blocked** with a specific error naming the requests. (B9:
  a step with no eligible active user stalls forever, escapable only by SYSTEM_ADMIN.)
- **R2.15** For `ROLE` steps: no re-point is needed (resolution is by role and the leaver drops out when their
  account is deactivated). **But** if the subject is the *last active holder* of a role used in the company's
  configured org-change workflow, the flow shows a **non-blocking warning** naming the role and the number of
  requests that will stall, and the warning is recorded in the audit trail. Blocking would be disproportionate
  (an admin can grant the role to someone else in seconds); silence would not be acceptable.
- **R2.16** The subject's `org_change_workflow_steps` membership is **never** removed by offboarding — the company's
  approval chain is configuration, not employee data, and `ON DELETE CASCADE` on that FK (B10) means any deletion
  path silently mutilates it.

**(e) Everything else in flight.**
- **R2.17** Unread `user_notifications` for the leaver's account are left in place at offboarding (the account is
  deactivated, so they are unreachable) and are deleted at erasure (§4.3).
- **R2.18** Onboarding checklist tasks (S1) assigned **to** the leaver are re-pointed by the same rule as R2.7 and
  flagged as reassigned; tasks **about** the leaver (their own onboarding, if they leave during it) are closed as
  `N_A` with reason `"Employee offboarded"`.
- **R2.19** Rows in `employee_imports` / `employee_import_rows` referencing the leaver are not modified.

### 4.3 D3 — GDPR retention and erasure

> **Flagged for DPO/legal validation.** The BA does not give legal advice (Charter §9.7). The *default periods*
> below are proposals requiring confirmation per jurisdiction; the *mechanisms* are product requirements
> regardless of what period is confirmed.

**Roles.** The tenant company is the **controller**; the portal operator is the **processor**. Consequence for
the product: retention length and erasure decisions are **per-company configuration**, not a platform-wide
constant, and the platform must give the tenant the controls rather than deciding for them.

**Lawful basis (proposed, needs DPO confirmation — OQ-2).**

| Phase | Data | Proposed lawful basis |
|---|---|---|
| During employment | Core employment record, org placement, leave | Art. 6(1)(b) performance of the employment contract; Art. 6(1)(c) where employment/social-security law compels it |
| After exit, within retention | Employment record, leave history, org and approval history | Art. 6(1)(c) legal obligation (employment, tax and social-security record-keeping) **and** Art. 6(1)(f) legitimate interests — establishment/exercise/defence of legal claims |
| Special-category data | The portal stores `gender` only (`employees.gender`, used solely for vacation eligibility) | Art. 9(2)(b) employment-law obligations. **Gender is not special-category per se**, but is close enough to warrant DPO review of the eligibility use case |

- **R3.1 Retention period.** Each company has a configurable **post-exit retention period in whole years**,
  default **7**, minimum 1, maximum 30, editable by PORTAL_ADMIN and SYSTEM_ADMIN only, every change audited.
  The clock starts at `exit_date`. 7 years is a proposal aligned to common EU employment/tax record-retention
  floors — **DPO to confirm per jurisdiction** (OQ-2).
- **R3.2 Visibility of the clock.** For any non-ACTIVE employee, the lifecycle screen shows `exit_date`, the
  retention expiry date, and the days remaining. An admin view lists all records **past** retention for the
  company, sorted oldest first. Storage limitation that nobody can see is not compliance.
- **R3.3 Expiry action.** At retention expiry the record is **anonymised** (R3.5), not deleted. Whether that runs
  automatically or as an admin-triggered batch depends on scheduler capability the app does not have (B16) —
  **OQ-4**. The *must* for S2 is: configurable period (R3.1) + visibility (R3.2) + a manual "anonymise now"
  action on an expired record. Automatic expiry is a **Should**, dependent on OQ-4.
- **R3.4 Erasure requests (Art. 17) are recorded, then either executed or refused — both audited.** The system
  provides an erasure action on a non-ACTIVE record; the actor must record the request date and the requester,
  and either execute anonymisation or record a **refusal with a stated ground** (typically an overriding legal
  retention obligation under Art. 17(3)(b)/(e)). Both outcomes produce an audit row. The tool must be operable
  within the Art. 12(3) one-month response window; the SLA itself is the tenant's responsibility.
- **R3.5 Erasure = anonymisation, never hard delete.** Hard deletion is **forbidden** and no application code path
  may issue `DELETE FROM employees`. Evidence, not preference: `ON DELETE CASCADE` on `employees` would destroy
  the leaver's entire vacation and org-change history and **silently delete a company's approval-workflow step**
  (B10), and the un-cascaded `vacation_requests.manager_id` FK means deletion would often just fail at the
  constraint (B11).

**R3.6 — What erasure REMOVES or replaces** (identifying and free-text data):

| Data | Action |
|---|---|
| `employees.first_name` / `last_name` | Replaced with `"Former"` / `"Employee <token>"` |
| `employees.email` | Replaced with a globally unique token at a non-routable domain (B12 — the column is UNIQUE across all tenants) |
| `employees.phone_number`, `gender`, `profile_photo_url` | `NULL`; the photo file is deleted from disk |
| `users` row | `email`, `username` tokenised (both UNIQUE — B12); `password_hash` `NULL`; `is_active` FALSE; `last_login_at` `NULL` |
| `user_notifications` for that user | Deleted (free text naming colleagues and dates) |
| `employee_search_index` row | Deleted |
| `employee_skills`, `employee_certifications` | Deleted — competency claims about a named individual with no retention justification (**OQ-3**: does any tenant need regulated-role certification evidence retained?) |
| `vacation_requests.notes`, `manager_note` | `NULL` — free text, frequently contains health or family information |
| `org_change_requests.reason`, `org_change_approvals.note` | `NULL` — free text, frequently contains performance commentary |
| `page_views.user_id` / `employee_id`, `search_logs.user_id` | `NULL` (behavioural data) |
| Audit rows **about** the subject | Free-text `reason` fields `NULL`; identifiers retained (R3.7) |

**R3.7 — What MUST SURVIVE erasure** (pseudonymised, and stated so the Architect does not "tidy" it away):
`employees.id` as the stable pseudonymous key · `employee_number` · `company_id` · `join_date`, `exit_date`,
`employment_status`, `employment_type` · **all** `employee_org_assignments` and `manager_relationships` rows with
their dates and unit ids (historical org structure, headcount and span-of-control reporting must remain correct
for prior periods) · **all** `vacation_requests` rows with dates, working days, type, status and timestamps
(free text stripped) · **all** `org_change_requests` and `org_change_approvals` rows with from/to ids, decisions,
decider identity and timestamps — *the decider is a different data subject and their decision record is not
erased by this subject's request* · **every audit row** concerning the subject, with the actor identity intact
and the subject identified by `employees.id` + `employee_number` only.

- **R3.8** The erasure operation is itself audited: actor, subject, timestamp, company, the categories removed,
  and the ground where refused. **That audit row must not contain any of the erased values.**
- **R3.9** Erasure is irreversible and the confirmation says so, requiring the actor to type the employee number
  to proceed. An anonymised record can never be rehired into (§8).
- **R3.10 Subject access / portability (Art. 15 / 20).** A per-employee export (machine-readable) of the subject's
  own records — profile, org history, leave history, skills, certifications, and the audit rows where they are the
  subject. **Should**, not Must, for S2; it is a distinct capability from erasure and the SPM may schedule it
  separately (**OQ-5**).
- **R3.11 Documentation debt.** `docs/BUSINESS_DOCUMENTATION.md` §4 currently states *"Employee records | Retained
  regardless of `employment_status`"* and *"Vacation requests | Permanently retained"* — indefinite retention,
  which contradicts GDPR storage limitation and this section. The BA owns that file and will correct it **in the
  same commit as the KAN-184 implementation** (Charter §5b rule 1). Logged as **CFL-3** (§9).

### 4.4 D4 — Audit content

**Rule.** An offboarding is defensible only if a single, immutable, company-scoped record answers: *who did what
to whom, when, from what state to what state, and why.* Schema design is the Architect's; the following are
**requirements on content and behaviour** and each is individually testable.

**R4.1 — Required fields per audit row:**

| # | Field | Requirement |
|---|---|---|
| 1 | Event id | Server-generated, immutable, unique |
| 2 | `occurred_at` | Server clock, timezone-aware, never client-supplied |
| 3 | Actor identity | `user_id` **and** `employee_id`, **plus a snapshot** of the actor's display name/email/username **and roles as at the time of the action** — denormalised so the row stays meaningful after the actor is later renamed, offboarded or erased |
| 4 | Actor context | Source IP and session identifier. **Should** — becomes meaningful only once real authentication lands (EP28/KAN-148, stage S5); until then record what is available and leave the fields nullable |
| 5 | Subject identity | `employee_id` **and** a snapshot of `employee_number`. Name is **not** snapshotted — it would survive erasure and defeat it |
| 6 | `company_id` | Mandatory, non-null — the tenant scope of the event (CC-14) |
| 7 | Action code | From a closed enumeration, e.g. `EMPLOYEE_OFFBOARDED`, `EMPLOYEE_STATUS_CORRECTED`, `REPORTS_REASSIGNED`, `PORTAL_ACCESS_REVOKED`, `ROLES_REVOKED`, `VACATION_AUTO_CANCELLED`, `VACATION_MANAGER_REPOINTED`, `ORG_CHANGE_AUTO_CANCELLED`, `ORG_CHANGE_APPROVER_REPOINTED`, `ONBOARDING_TASK_COMPLETED`, `EMPLOYEE_REHIRED`, `EMPLOYEE_ANONYMISED`, `ERASURE_REFUSED`, `RETENTION_PERIOD_CHANGED` |
| 8 | Entity affected | Entity type + entity id (an offboarding touches employees, users, manager_relationships, vacation_requests, org_change_requests — each gets its own row) |
| 9 | **Before / after state** | A structured **field-level diff**: field name, old value, new value, for every field changed. The **old value must be captured even though the write overwrites it** — this is the single most important field for defensibility and the one most easily lost |
| 10 | Reason | Actor-supplied. **Mandatory** for offboarding (a termination reason category from a company-configurable list, plus optional free text), for status correction, and for erasure refusal |
| 11 | Correlation id | Groups every row produced by one lifecycle transaction, so an offboarding reads as one story rather than eleven scattered rows |
| 12 | Outcome | `SUCCESS` / `FAILED` plus an error code; a failed-and-rolled-back attempt is still recorded |

**R4.2 — Behavioural invariants:**
- **Append-only.** No application code path issues `UPDATE` or `DELETE` against audit rows. The only permitted
  mutation is the erasure redaction of free-text `reason` fields (R3.6), which is itself audited.
- **Same transaction.** Audit rows are written in the same DB transaction as the change they describe, so an
  applied change can never exist without its audit row and a rolled-back change never leaves a phantom one.
- **Pre-change snapshot.** For an offboarding the row set must capture the prior `employment_status`, the prior
  `users.is_active`, the prior solid-line manager, and the prior current org assignment — those are precisely the
  facts a tribunal or DSAR asks about.
- **Read access.** SYSTEM_ADMIN (all companies), and `audit_log` read holders within their own company (default
  PORTAL_ADMIN + HR_ADMIN). Never exposed to `EMPLOYEE`, never to another tenant (CC-14).
- **Retention.** Audit rows follow the company retention period and **survive** subject erasure in pseudonymised
  form (R3.7).

### 4.5 D5 — Status semantics

| Status | Meaning | Employment relationship | Portal access | `exit_date` | Terminal? |
|---|---|---|---|---|---|
| `ACTIVE` | Currently employed and working | Live | Yes | `NULL` | No |
| `INACTIVE` | **Still employed**, temporarily not working — long-term leave (parental, sabbatical, long-term sick) or suspension pending investigation | **Live** | **Suspended** (`users.is_active = FALSE`) | **Must be `NULL`** | **No — reversible** |
| `RESIGNED` | Employment ended at the **employee's** initiative (voluntary) | Ended | No | **Mandatory** | **Yes** |
| `TERMINATED` | Employment ended at the **employer's** initiative — dismissal, redundancy, end of fixed term, death in service | Ended | No | **Mandatory** | **Yes** |

- **R5.1** `INACTIVE` is **not** a leaver state. Offboarding never sets it. This is the load-bearing call: because
  ~20 queries treat "not ACTIVE" as "invisible" (B2), `INACTIVE` already behaves as "suspended from operational
  views" — that is exactly the semantics a long-term-leave or suspension case needs, and reusing it for leavers
  would destroy the ability to distinguish "will be back" from "gone".
- **R5.2** `RESIGNED` vs `TERMINATED` exist as separate codes because the distinction drives voluntary-vs-involuntary
  attrition analytics, rehire eligibility (§8), and legal defensibility. The offboarding flow requires the actor to
  choose one explicitly; there is no default and no inference.

**Who may set what:**

| Transition | Permitted actor | Route | Reversible |
|---|---|---|---|
| `ACTIVE` → `INACTIVE` and back | `employee_lifecycle` **w** holders (default HR_ADMIN, PORTAL_ADMIN) + SYSTEM_ADMIN | Status change action, reason mandatory | **Yes**, unlimited, each transition audited |
| `ACTIVE`/`INACTIVE` → `RESIGNED`/`TERMINATED` | `employee_lifecycle` **w** holders + SYSTEM_ADMIN | **Only** the offboarding workflow (KAN-184) | **No** (R5.4) |
| `RESIGNED` ↔ `TERMINATED` (code correction) | PORTAL_ADMIN, SYSTEM_ADMIN only | `EMPLOYEE_STATUS_CORRECTED`, reason mandatory | n/a — changes no access and no org data, so low risk |
| `RESIGNED`/`TERMINATED` → `ACTIVE` | **Nobody, by direct edit** | Rehire workflow only (KAN-186) | — |

- **R5.3** A manager (`SOLID_LINE_MANAGER`) may **never** set any of these, and no actor may change their own
  employment status — mirroring the existing rule that an admin cannot remove their own roles (KAN-16).
- **R5.4** **Terminal statuses are not directly reversible.** A silent flip back to `ACTIVE` would restore portal
  access, resurrect closed manager relationships and org assignments, and leave no record of the employment gap.
  The only route back is rehire, which is a deliberate new employment period. Whether a same-day "undo mistaken
  offboarding" is wanted is **OQ-6** — out of scope until answered.
- **R5.5 `exit_date` rules.** Mandatory and non-null for `RESIGNED`/`TERMINATED`; must be `>= join_date`; must be
  `NULL` for `ACTIVE`/`INACTIVE`. For S2 (Must) `exit_date` must be **today or in the past** — an immediate
  offboarding. A retrospective date more than 30 days old is accepted but triggers a confirmation prompt.
- **R5.6 Future-dated (scheduled) offboarding is a Should, not a Must,** and is blocked on OQ-4: with no scheduler
  (B16) a future `exit_date` would either revoke access early (wrong) or never (worse). Until a scheduling
  capability exists, a future `exit_date` is rejected with a clear message.

### 4.6 The one deliberate exception to the org-change engine — stated so it is not mistaken for a bypass

`CLAUDE.md` requires position changes to go through `org_change_service`. Offboarding's **reassignment of the
leaver's reports** (R1.4) does **not**. This is deliberate and bounded:

1. **It cannot go through the chain without deadlocking.** The chain may name the leaver themselves as an approver
   (B9), and it is asynchronous — the tree would stay broken for the whole approval period, which is precisely the
   damage the rule exists to prevent.
2. **It is not a position change.** It changes only the `SOLID_LINE` manager pointer of *other* employees as a
   consequence of a removal. BU, functional unit, location and cost centre are **unchanged** for every reassigned
   report — this is an explicit acceptance criterion (AC-184-09), not an assumption.
3. **The invariant it protects is untouched.** `CLAUDE.md` invariant 2 — *an individual employee can never
   initiate their own move* — still holds: the actor is an HR/Portal/System admin performing a removal, never the
   subject or the reports.
4. **A genuine relocation of a report** (new BU/FU/location) after a manager leaves is a normal transfer and
   **must** go through the chain (KAN-185). The offboarding screen must not offer BU/FU/location fields at all.

**This exception requires Senior Architect sign-off before implementation** (it is their document that owns the
invariant). Logged as **CFL-2** (§9).

---

## 5. KAN-183 — Onboarding checklist workflow (EP38-S1)

### 5.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-183 | As **HR**, I want a configurable onboarding checklist that is instantiated for every new hire so nothing is missed before day one. | Company-scoped task templates (name, description, assignee, due-offset from `join_date`, mandatory flag, order); instantiated automatically on employee registration and bulk import; per-task status with audit; assignee sees their tasks, the new hire sees only their own; day-one readiness view lists incomplete mandatory tasks; template edits never retro-change live checklists. | Should Have |

### 5.2 Happy path
- **AC-183-01** A `employee_lifecycle` **w** holder can create, reorder, edit and deactivate onboarding task
  templates for their own company. Each template has: name (required, ≤150 chars), description (optional),
  assignee type (`ROLE` | `EMPLOYEE` | `HIRING_MANAGER` — meaning the new hire's solid-line manager | `NEW_HIRE`),
  assignee value where applicable, due offset in days relative to `join_date` (may be negative for pre-boarding),
  mandatory flag, and sort order.
- **AC-183-02** When an employee is created via `/admin/register-user` **or** via bulk import, one task instance
  per active template of that employee's company is created, with `due_date = join_date + offset`, status
  `NOT_STARTED`, and the assignee resolved as at instantiation time.
- **AC-183-03** Each task instance moves between `NOT_STARTED → IN_PROGRESS → DONE`, or to `BLOCKED` (reason
  required) or `N_A` (reason required). Every transition records actor and timestamp and writes an audit row
  (`ONBOARDING_TASK_COMPLETED` and siblings) per §4.4.
- **AC-183-04** The new hire's profile shows an onboarding panel with completion progress (`x/y`, and `a/b`
  mandatory), each task's status, assignee and due date, visible to `employee_lifecycle` read holders and to the
  new hire's solid-line manager.
- **AC-183-05** A "day-one readiness" view lists, for all in-progress hires in the company, every incomplete
  **mandatory** task with its owner and due date, sorted by `join_date`.

### 5.3 Edge and boundary cases
- **AC-183-06** `join_date` is nullable (`database/schema.sql:349`; `app/routes/admin.py:185` passes `None`).
  Where it is absent, tasks are created **without** due dates and shown as "due date pending"; setting `join_date`
  later recomputes every not-yet-`DONE` task's due date and leaves `DONE` tasks alone.
- **AC-183-07** A `join_date` in the past creates immediately-overdue tasks, flagged overdue in the UI, with **no**
  backfilled notifications (a retrospective hire must not generate a notification storm).
- **AC-183-08** Assignee resolution is a **snapshot at instantiation**: a `ROLE` assignee resolves to the active
  holders at that moment. A later role change does not silently move existing tasks.
- **AC-183-09** If a `ROLE` assignee has **no** active holder in the company at instantiation, the task is assigned
  to the company's PORTAL_ADMIN and flagged `unassigned-fallback` in the UI; the task is never created ownerless.
- **AC-183-10** Editing or deactivating a template **never** alters already-instantiated checklists. Adding a
  template does not retro-add tasks to hires already in progress.
- **AC-183-11** A company with zero templates produces zero tasks and an explicit empty state ("No onboarding
  checklist configured") — never a list of another company's or a global default's tasks (`CLAUDE.md` empty-state
  rule).
- **AC-183-12** Bulk import of N employees instantiates tasks for every successfully created row; task
  instantiation must not materially slow the import and must not run inside the per-row loop as separate commits.
- **AC-183-13** If the new hire is offboarded before completing onboarding, all their incomplete tasks are closed
  `N_A` with reason `"Employee offboarded"` (R2.18).

### 5.4 Error and failure behaviour
- **AC-183-14** If task instantiation fails, the **employee is still created** — the failure is surfaced to the
  actor with a retry action and recorded; a checklist failure must never lose a hire record.
- **AC-183-15** Completing an already-`DONE` task returns `409` and writes no second audit row (CC-16).
- **AC-183-16** A template with a duplicate name in the same company is rejected with a field-level message; a
  template with an empty name or a non-integer offset is rejected before any write.

### 5.5 Permissions per role

| Role | Manage templates | Instantiate | Update any task | Update tasks assigned to them | View a hire's checklist |
|---|---|---|---|---|---|
| SYSTEM_ADMIN | Yes (in company context) | Yes | Yes | Yes | Yes |
| PORTAL_ADMIN | Yes | Automatic | Yes | Yes | Yes (own company) |
| HR_ADMIN | Yes (default w) | Automatic | Yes | Yes | Yes (own company) |
| SOLID_LINE_MANAGER | No | No | No | Yes | Own reports only |
| EMPLOYEE (the new hire) | No | No | No | Yes (`NEW_HIRE` tasks only) | Own only |
| All other roles | No | No | No | No | No — default deny |

- **AC-183-17** Every route is gated by `@require_feature_access('employee_lifecycle', …)`; there is no hardcoded
  role list anywhere in the story (CC-1). Granting `employee_lifecycle` write to any additional role through the
  admin matrix immediately gives that role the manage capability, with no code change and no extra check (CC-2).

### 5.6 Tenant isolation
- **AC-183-18** Templates, task instances and the readiness view are company-scoped (CC-9). A PORTAL_ADMIN of
  company A sees zero of company B's templates and tasks under every filter.
- **AC-183-19** Assignee pickers list only `ACTIVE` employees and only roles of that company (CC-4, CC-11).

### 5.7 Out of scope (S1)
Equipment/asset issue and return tracking beyond a checklist line · document upload or e-signature · external
account provisioning · task-level SLA reporting and escalation · email reminders (in-app notification only;
email would ride on EP18's existing dispatcher and is not requested here) · offboarding checklists (the
offboarding flow in §6 is a wizard, not a task list — **OQ-7**).

---

## 6. KAN-184 — Offboarding workflow (EP38-S2) — **Must**

### 6.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-184 | As **HR**, I want an offboarding workflow (access removal, exit date, reassignment of reports, in-flight work) so departures are clean, safe and auditable. | Sets `employment_status` to `RESIGNED`/`TERMINATED` with a mandatory `exit_date` and reason; **sets `users.is_active = FALSE` so the leaver cannot authenticate**; revokes role assignments; blocks until direct reports are reassigned inline; cancels the leaver's pending/future leave and re-points leave and org-change approvals naming them; the leaver is absent from directory, org tree, search, dashboards and every picker; a correlated set of audit rows records actor, subject, company, action, before/after state, reason and timestamp; company retention period applies from `exit_date`; erasure anonymises and never deletes. | Must Have |

### 6.2 Happy path
- **AC-184-01** A `employee_lifecycle` **w** holder opens offboarding from the employee's profile or the
  directory row. The flow shows, before any confirmation: subject identity, current status, current manager,
  current org placement, count of solid-line reports, count of dotted-line reports, list of the subject's
  PENDING/future-APPROVED leave, count of leave requests awaiting the subject's approval, count of org-change
  requests where the subject is subject or approver, and whether the subject is the last holder of any
  workflow-critical role.
- **AC-184-02** The actor must supply: departure type (`RESIGNED` | `TERMINATED` — no default, R5.2), `exit_date`
  (mandatory, R5.5), and a reason category from the company's configurable list plus optional free text
  (mandatory, R4.1 #10).
- **AC-184-03** On confirm, **in one transaction** (CC-15): `employment_status` set to the chosen terminal value;
  `exit_date` set; `users.is_active = FALSE`; all `user_roles` rows for the leaver's account removed; every
  `manager_relationships` row referencing the subject in either column closed with `effective_to = exit_date`
  (R1.6); reports re-pointed to their successors (R1.4); the subject's current `employee_org_assignments` row
  closed with `effective_to = exit_date`; leave and org-change items handled per §4.2; audit rows written per §4.4.
- **AC-184-04** **After offboarding, the leaver cannot authenticate.** Submitting their email at `/login`
  produces the standard "No active account found" error and issues **no** session. *(This criterion exists
  because it does not hold today by status alone — B3/CFL-1. It must be covered by an automated test.)*
- **AC-184-05** The leaver is absent from: employee directory, org tree (their card and their subtree
  re-parented under the successor), `/api/org-tree/context` ancestors, full-text search results, `/my-team`,
  vacation calendar scopes, all dashboard counts, all analytics headcount, the org-change employee picker, the
  successor/assignee pickers, and the login demo tiles. *(Delivered by B2 — this criterion verifies it rather
  than adding filters.)*
- **AC-184-06** The leaver **remains** visible on lifecycle/admin screens as a non-active record with status,
  `exit_date`, retention expiry and full history, to `employee_lifecycle` read holders.
- **AC-184-07** The leaver's former manager and each affected employee receive an in-app notification: the manager
  that the report has left, each reassigned report that their manager has changed, each new approver per R2.9.

### 6.3 Reports, in-flight work, and the decisions
- **AC-184-08** Offboarding a subject with ≥1 current `SOLID_LINE` report **cannot be submitted** without a
  successor for each report; the submit control is disabled and the API returns `422` naming the unassigned
  reports (R1.1, D1).
- **AC-184-09** Reassignment changes the `SOLID_LINE` manager **only**. Each reassigned report's business unit,
  functional unit, location and cost centre are byte-for-byte unchanged (§4.6 point 2), and **no**
  `org_change_requests` row is created for them.
- **AC-184-10** Choosing a successor who is one of the subject's own reports re-points **that** person to the
  subject's manager instead of to themselves; the transaction completes and no `chk_not_self_manager` violation
  occurs (R1.2).
- **AC-184-11** Where the subject has no manager and the successor is one of their reports, the successor becomes
  a tree root, the flow says so in plain language before confirmation, and the tree renders correctly afterwards
  (R1.3).
- **AC-184-12** Dotted-line reports may be reassigned or left; where left, the relationships are closed and the
  count is shown before confirmation and recorded in the audit trail (R1.5).
- **AC-184-13** After offboarding, **no** `manager_relationships` row with `is_current = TRUE` references the
  subject in either `employee_id` or `manager_id` (R1.6) — asserted by a direct DB query in the integration test.
- **AC-184-14** The subject's `PENDING` leave requests are `CANCELLED` with the system note (R2.1), and `APPROVED`
  requests wholly after `exit_date` are `CANCELLED` (R2.2).
- **AC-184-15** `APPROVED` requests starting on or before `exit_date` are **unchanged** in status, dates and
  working days (R2.3), including where the end date is after `exit_date`.
- **AC-184-16** Every request that will be cancelled is listed with type, dates, working days and status before
  the actor confirms; the confirmation states the count (R2.4).
- **AC-184-17** `PENDING` requests naming the subject as `manager_id` are re-pointed per R2.7, remain `PENDING`,
  and the new approver can open and decide them through the existing review endpoint with no error (B7).
- **AC-184-18** Where no re-point target resolves for a leave request, offboarding is **blocked** with an error
  naming the affected requests and the missing role; **nothing** is written (R2.8, CC-15).
- **AC-184-19** `PENDING` `org_change_requests` where the subject is `employee_id` are set to `CANCELLED`, and no
  `employee_org_assignments` or `manager_relationships` change is applied for them (R2.11).
- **AC-184-20** `PENDING` `org_change_requests` with an `EMPLOYEE` step naming the subject — at the current step
  **or any later step** — have that step re-pointed per R2.13; where no target resolves, offboarding is blocked
  (R2.14) and nothing is written.
- **AC-184-21** Where the subject is the last active holder of a role used in the company's org-change workflow,
  a non-blocking warning naming the role and the number of requests that will stall is shown before confirmation
  and recorded in the audit trail (R2.15).
- **AC-184-22** `org_change_workflow_steps` rows naming the subject are **not** deleted or modified (R2.16);
  the company's configured chain is byte-for-byte unchanged after the offboarding.
- **AC-184-23** Onboarding tasks assigned to the subject are re-pointed and flagged; the subject's own incomplete
  onboarding tasks are closed `N_A` (R2.18).

### 6.4 Status, audit, retention and erasure
- **AC-184-24** Offboarding sets only `RESIGNED` or `TERMINATED` — never `INACTIVE` (R5.1). Submitting `INACTIVE`
  through the offboarding API returns `400`.
- **AC-184-25** `exit_date` is rejected when null, when `< join_date`, or when in the future (R5.5, R5.6); a date
  more than 30 days in the past requires an explicit confirmation.
- **AC-184-26** A terminal status cannot be changed back to `ACTIVE` by any direct edit or API call by any role,
  including SYSTEM_ADMIN; the attempt returns `409` naming the rehire workflow (R5.4).
- **AC-184-27** `RESIGNED ↔ TERMINATED` correction is available to PORTAL_ADMIN and SYSTEM_ADMIN only, requires a
  reason, changes no access and no org data, and writes an `EMPLOYEE_STATUS_CORRECTED` audit row (R5.2 table).
- **AC-184-28** The offboarding writes a **correlated** set of audit rows (shared correlation id) covering every
  field-level change with **old and new values**, actor snapshot with roles-as-at-the-time, subject id and
  employee number, company id, action codes, reason, and timestamps — per every field in R4.1.
- **AC-184-29** Audit rows are written in the **same transaction** as the changes. A deliberately failed
  offboarding (e.g. AC-184-18) leaves zero audit rows describing changes that did not happen, and one `FAILED`
  attempt row (R4.2).
- **AC-184-30** No application code path deletes an employee. `DELETE FROM employees` does not appear anywhere in
  `app/` — assertable by a static check (R3.5).
- **AC-184-31** Retention: the record shows `exit_date`, retention expiry (`exit_date` + the company's configured
  years, default 7) and days remaining; the past-retention admin list includes it once expired (R3.1, R3.2).
- **AC-184-32** Erasure on a non-active record anonymises exactly the fields in R3.6 and preserves exactly the
  data in R3.7. Verified concretely: after erasure the employee's `vacation_requests` rows still exist with
  unchanged dates, working days, type and status, and `notes`/`manager_note` are `NULL`; `org_change_approvals`
  still record the decision, decider and timestamp; the org tree for prior periods still reconstructs.
- **AC-184-33** Erasure requires typing the employee number to confirm, is irreversible, and writes an
  `EMPLOYEE_ANONYMISED` audit row that contains **none** of the erased values (R3.8, R3.9).
- **AC-184-34** Refusing an erasure request records the request, the refusal and the stated ground as an
  `ERASURE_REFUSED` audit row (R3.4).
- **AC-184-35** After erasure the leaver's email and username are globally unique tokens, so a later hire can
  reuse the original address without hitting the UNIQUE constraints (B12).

### 6.5 Error and failure behaviour
- **AC-184-36** Any failure at any step rolls back the entire offboarding: `employment_status`, `users.is_active`,
  `user_roles`, manager relationships, org assignments, vacation requests and org-change requests are all exactly
  as before, and the actor sees a specific error naming the failing step (CC-15).
- **AC-184-37** Offboarding an already-offboarded subject returns `409` with the existing state; no second set of
  changes and no duplicate audit rows (CC-16).
- **AC-184-38** Two actors offboarding the same subject concurrently: exactly one succeeds; the other receives
  `409` and writes nothing.
- **AC-184-39** A subject who is the **last active user holding `PORTAL_ADMIN`** in the company **cannot** be
  offboarded; the flow returns `422` requiring another PORTAL_ADMIN to be appointed first. (Tenant lockout
  prevention, mirroring KAN-16's "own roles cannot be removed".)
- **AC-184-40** An actor cannot offboard **themselves**: `403`, no state change (R5.3).
- **AC-184-41** Offboarding a subject who does not exist, or whose id is not a valid UUID, returns `404`/`400`
  with no stack trace and no PII in the log line (CC-17).

### 6.6 Permissions per role

| Role | Offboard | Reassign reports in-flow | Correct status | Erase / anonymise | Set retention period | Read audit |
|---|---|---|---|---|---|---|
| SYSTEM_ADMIN | Yes (company context required, CC-12) | Yes | Yes | Yes | Yes | All companies |
| PORTAL_ADMIN | Yes (own company) | Yes | Yes | Yes (`d`) | Yes | Own company |
| HR_ADMIN | Yes (default `w`) | Yes | No | **No** (no `d` by default) | No | Own company |
| SOLID_LINE_MANAGER | **No** | No | No | No | No | No |
| DEPARTMENT_HEAD / LOCATION_HEAD / HIRING_MANAGER / DOTTED_LINE_MANAGER | No | No | No | No | No | No |
| EMPLOYEE | No | No | No | No | No | No |

- **AC-184-42** Every route is `@require_feature_access('employee_lifecycle', 'w'|'d')` or
  `@require_feature_access('audit_log', 'r')`; a role granted `employee_lifecycle` write through the admin matrix
  gains offboarding with **no** code change and **no** additional role check (CC-1, CC-2).
- **AC-184-43** A user with `r` but not `w` sees the lifecycle screen and the audit trail but every mutating API
  returns `403` and changes nothing (CC-8).
- **AC-184-44** A company with no custom roles shows an **empty** role list on any lifecycle role picker — never
  the global template roles (`CLAUDE.md`; CC-4).

### 6.7 Tenant isolation
- **AC-184-45** Offboarding an employee of another company returns `403`, reads nothing back and writes nothing,
  for PORTAL_ADMIN, HR_ADMIN and any other non-SYSTEM_ADMIN role (CC-10).
- **AC-184-46** Successor pickers, reason-category lists, retention settings and audit views are company-scoped;
  company B's data appears in none of them under any filter or search term (CC-9, CC-11, CC-14).
- **AC-184-47** An employee record with `company_id IS NULL` (SYSTEM_ADMIN account) is invisible to PORTAL_ADMIN
  and HR_ADMIN lifecycle screens and can be offboarded only by SYSTEM_ADMIN (CC-13).
- **AC-184-48** Re-point resolution (R2.7) never selects a manager or HR_ADMIN from a different company, even
  where the requester's own manager chain has been broken.

### 6.8 Out of scope (S2)
Exit interviews and their content · final-pay, severance or notice-period calculation · asset return tracking
beyond an optional checklist line · revocation of access in **external** systems (EP40-S2 SCIM) · mailbox
forwarding or delegation · scheduled/future-dated offboarding (R5.6, OQ-4) · undo/reversal of a completed
offboarding (R5.4, OQ-6) · bulk offboarding of many employees at once (**OQ-8**) · automatic retention-expiry
purge without an admin action (R3.3, OQ-4) · subject-access export (R3.10, OQ-5).

---

## 7. KAN-185 — Transfer via the org-change engine (EP38-S3)

### 7.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-185 | As a **manager or HR**, I want an HR-initiated transfer flow (business unit / functional unit / location / manager) that reuses the existing sequential approval engine so moves are consistent however they start. | Transfer is a second entry point to `org_change_service.create_request` — same initiator rule, same sequential chain, same apply, no second engine; company-scoped; concurrent requests for one subject blocked; the subject's pending leave re-points to the new manager on apply; assignment history is contiguous and non-overlapping. | Should Have |

### 7.2 Happy path
- **AC-185-01** A form-based transfer is available from the employee profile and directory row, in addition to
  the existing org-tree drag-and-drop. It calls `org_change_service.create_request` with the same payload shape;
  **no** approval, eligibility or apply logic is re-implemented (CC-5).
- **AC-185-02** The initiator rule is unchanged: the requester must be the subject's current `SOLID_LINE` manager
  **or** hold `HR_ADMIN`/`PORTAL_ADMIN`/`SYSTEM_ADMIN`; a plain `EMPLOYEE` receives `403`, and no employee can
  initiate their own move through this entry point either (`CLAUDE.md` org-change invariant 2).
- **AC-185-03** The request is gated by `@require_feature_access('org_change', 'w')`; the workflow config page
  remains `org_structure` write (`CLAUDE.md` invariant 1). No new feature code is introduced (CC-7).
- **AC-185-04** Approvals remain strictly sequential; a single rejection sets `status='REJECTED'` and applies no
  change; only the final approval applies (`CLAUDE.md` invariant 3).
- **AC-185-05** On final approval the existing `apply_change` runs — old assignment closed, new current assignment
  inserted with the cost centre carried, solid-line manager re-pointed when changed.
- **AC-185-06** A transfer initiated from the form and one initiated from drag-and-drop are indistinguishable in
  the approver's queue, in `org_change_requests`, and in the resulting data.

### 7.3 New requirements this story adds (beyond today's behaviour)
- **AC-185-07** **Effective date.** The request carries an effective date (default today, may be future). On
  apply, the closing assignment's `effective_to` and the new assignment's `effective_from` must **not overlap**:
  for any employee, no two `employee_org_assignments` rows may cover the same date, and exactly one row may have
  `is_current = TRUE`. *(Today `apply_change` sets the old row's `effective_to = CURRENT_DATE` while the new row
  defaults `effective_from = CURRENT_DATE` — a one-day overlap on every move. Logged as **CFL-4**, §9.)*
- **AC-185-08** **Concurrency.** Creating a transfer for a subject who already has a `PENDING`
  `org_change_requests` row returns `409` naming the existing request. *(Today nothing prevents two concurrent
  requests; both would apply, and the second would carry a stale "from" snapshot — silently falsifying the audit
  record the workflow exists to produce. Logged as **CFL-5**, §9.)*
- **AC-185-09** **Leave follows the manager.** When apply changes the solid-line manager, every `PENDING`
  `vacation_requests` row for the subject has `manager_id` re-pointed to the new manager; both the old and new
  manager are notified; the change is audited (consistent with R2.6/R2.10; without it the *old* manager remains
  the only person who can approve — B7).
- **AC-185-10** **Transferring a manager does not move their team.** Where the subject has direct reports, the
  flow states "N direct reports will continue to report to <subject>" before submission, and after apply **no**
  report's BU, FU, location or manager has changed.
- **AC-185-11** A transfer that changes nothing (all proposed values equal the current placement) is rejected at
  submission with `400`.

### 7.4 Edge, boundary and error behaviour
- **AC-185-12** The subject must be `ACTIVE`. A transfer targeting a `RESIGNED`/`TERMINATED`/`INACTIVE` employee
  returns `400` and creates no request.
- **AC-185-13** The proposed manager must be an `ACTIVE` employee of the same company, must not be the subject,
  and must not be one of the subject's own descendants where that would create a reporting cycle; violations
  return `400` and create no request.
- **AC-185-14** Where the subject is offboarded while a transfer is pending, the request is `CANCELLED` and not
  applied (R2.11) — asserted end-to-end.
- **AC-185-15** Where a named approver is offboarded while the transfer is pending, the step is re-pointed
  (R2.13) and the request remains decidable — asserted end-to-end.
- **AC-185-16** A proposed BU, FU or location belonging to **another company** returns `403` and creates no
  request, even if a valid UUID is supplied directly to the API.

### 7.5 Permissions and tenant isolation
- **AC-185-17** Permission behaviour is exactly the existing org-change matrix; this story adds no role checks and
  removes none. `SOLID_LINE_MANAGER` may transfer their own reports; `HR_ADMIN`/`PORTAL_ADMIN`/`SYSTEM_ADMIN` may
  transfer anyone in scope; `EMPLOYEE` and `DOTTED_LINE_MANAGER` may not initiate.
- **AC-185-18** All prefill and picker queries stay company-scoped (`app/routes/org_change.py:135,167`); approver
  resolution continues to match role **by name within the company** (`CLAUDE.md` invariant 4).
- **AC-185-19** **Cross-company transfer is not supported.** `employees.company_id` is never modified by this
  story; an attempt returns `403`. Moving a person between tenants is a leave-and-rehire, not a transfer.

### 7.6 Out of scope (S3)
Promotion — job title, grade, or `employment_type` change (**OQ-1**: `org_change_requests` has no column for
these and the roadmap epic title promises "promote" with no story to carry it) · compensation · cross-company
moves (AC-185-19) · retroactive transfers with recalculation of past leave entitlement · bulk transfers
(re-org tooling) · changing the approval chain per transfer (the chain is company configuration).

---

## 8. KAN-186 — Rehire (EP38-S4) — outline only

> Roadmap §E places this in **Later**. Specified to the depth needed to prevent S2 from foreclosing it —
> deliberately not elaborated further.

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-186 | As **HR**, I want rehire to detect and relink a prior employee record so history is not lost and duplicates are not created. | Detects a prior record on email/employee number; reuses the same `employees` row for continuity; records a **new employment period** without destroying the prior `join_date`/`exit_date`; roles and manager relationships are re-granted explicitly, never auto-restored; anonymised records are never rehired into; every step audited. | Could Have |

- **AC-186-01** At registration and at bulk import, a prior record matching on email or employee number is
  detected and the actor is offered "rehire this person" rather than a duplicate-key error. *(Today
  `app/routes/admin.py:163-166` returns a flat "already in use" error, and `employees.email`/`employee_number`
  are globally UNIQUE — B12 — so a rehire currently cannot be entered at all without inventing a fake address.)*
- **AC-186-02** Rehire reuses the same `employees.id`, preserving all prior history, and sets
  `employment_status = 'ACTIVE'`.
- **AC-186-03** **The prior `join_date` and `exit_date` must remain retrievable.** A rehire that overwrites
  `join_date` destroys tenure and silently corrupts the work-anniversary feature (KAN-63 computes from
  `join_date`). Employment periods therefore need first-class representation — **the Architect's design call**;
  the requirement is only that both periods are recoverable and that tenure is computed from the current period
  unless the company configures continuous service.
- **AC-186-04** Prior roles are **not** restored automatically — they must be re-granted (least privilege). Prior
  manager relationships and org assignments are **not** reopened; the rehire flow requires a new manager and a
  new assignment.
- **AC-186-05** The portal account is **reactivated**, not recreated — `users.employee_id` is UNIQUE (B12), so a
  second row for the same employee is impossible.
- **AC-186-06** A record that has been **anonymised** can never be rehired into; the matcher must not match on
  tokenised values, and a new record is created instead (R3.9).
- **AC-186-07** Rehire eligibility: offboarding may set a "not eligible for rehire" flag with a reason (typically
  on `TERMINATED`). Rehiring such a record requires PORTAL_ADMIN and a recorded override reason; both the flag and
  the override are audited.
- **AC-186-08** Rehire is company-scoped: a prior record in **another** tenant is never matched or surfaced, and
  rehire never changes `company_id` (CC-9, AC-185-19).
- **AC-186-09** Leave entitlement is evaluated per calendar year against `used_days`, which counts PENDING +
  APPROVED (B18); cancelled requests from the prior period do not consume the rehire year's entitlement.
- **Out of scope (S4):** merging duplicate records created because a rehire was not detected (data-repair
  tooling) · continuous-service and seniority-bridging policy engines · cross-tenant rehire · restoring skills or
  certifications deleted at erasure.

---

## 9. Conflict log (Charter §5 — never resolved silently)

| ID | Conflict | Severity | Evidence | Resolution required from |
|---|---|---|---|---|
| **CFL-1** | The roadmap and the S1 tasking state that *"login already requires `employment_status = 'ACTIVE'`"*. **It does not.** `login()` authenticates on `u.is_active` alone. Only the demo-tile query filters ACTIVE. | **Critical** — an offboarding built on that premise would leave leavers able to log in | `app/routes/auth.py:84-97` vs `:33` | Resolved in these criteria (AC-184-03, AC-184-04). SPM to note that the roadmap statement is false; the roadmap is the SPM's document to correct. |
| **CFL-2** | Offboarding re-points direct reports **without** the org-change approval chain, while `CLAUDE.md` requires position changes to go through `org_change_service`. | **High** — a governance invariant | §4.6, with the reasoning and the bounded exception | **Senior Architect sign-off** before implementation. They own `CLAUDE.md`. |
| **CFL-3** | `docs/BUSINESS_DOCUMENTATION.md` §4 states employee records are *"retained regardless of `employment_status`"* and vacation requests *"permanently retained"* — indefinite retention, contradicting §4.3 and GDPR storage limitation. | **High** (compliance) | `docs/BUSINESS_DOCUMENTATION.md:238-245` | BA (owner) corrects it **in the same commit as the KAN-184 implementation** — not in this document, per the single-file constraint on this task. |
| **CFL-4** | `apply_change` closes the outgoing assignment with `effective_to = CURRENT_DATE` while the incoming row defaults `effective_from = CURRENT_DATE` — every org move creates a one-day overlap in assignment history. | **Medium** (data quality; affects any point-in-time headcount report) | `app/services/org_change_service.py:282-291` + `database/schema.sql:296-298` | Architect to pick a convention (half-open vs `effective_to = date - 1`); AC-185-07 asserts non-overlap either way. |
| **CFL-5** | Nothing prevents two concurrent `PENDING` org-change requests for the same subject; both would apply and the second carries a stale "from" snapshot — falsifying the record the workflow exists to produce. | **Medium** | `org_change_service.create_request` — no such check | AC-185-08. Confirm with SPM that blocking (rather than superseding) is the wanted behaviour. |
| **CFL-6** | `org_change_workflow_steps.approver_employee_id` is `ON DELETE CASCADE` — deleting an employee silently deletes a company's approval step, corrupting the configured chain with no trace. | **Medium** (latent; only reachable if a delete path is ever added) | `database/schema.sql:2176` | Mitigated by R3.5/AC-184-30 (no delete path). Architect to consider `RESTRICT` when next touching the schema. |
| **CFL-7** | The EP38 epic title promises *"join → transfer → **promote** → offboard → rehire"*, but no story covers promotion and `org_change_requests` carries no job-title/grade/employment-type column. | **Medium** (scope gap — blocks the S1 freeze) | Roadmap §D BG4 heading vs its four stories | **SPM** — add a story or declare promotion out of scope (**OQ-1**). |

---

## 10. Traceability matrix

Objective → Requirement → Story → Criteria. Chain per Charter §4 (BA method step 4); UX / Technical / Test / UAT
columns are the owning roles' to complete and are deliberately left as pointers, not invented here.

| Business goal | Requirement / decision | Story | Acceptance criteria | UX | Technical | Test |
|---|---|---|---|---|---|---|
| BG4 Complete the people-ops lifecycle | Onboarding checklist configuration | KAN-183 | AC-183-01, 02, 10, 11, 16 | UX — checklist admin | Architect | pytest + UI |
| BG4 | Onboarding execution & visibility | KAN-183 | AC-183-03, 04, 05, 17 | UX | Architect | pytest |
| BG4 | Onboarding edge/failure handling | KAN-183 | AC-183-06 – 09, 12 – 15 | — | Architect | pytest |
| BG4 | Onboarding tenancy & permissions | KAN-183 | AC-183-17, 18, 19 | — | Architect | pytest (tenant-isolation tier) |
| BG4 / BG1 | **D1 orphaned reports** — block + inline reassignment | **KAN-184** | AC-184-08, 09, 10, 11, 12, 13 | UX — offboarding wizard step 2 | Architect (+ CFL-2 sign-off) | pytest + real-DB tier (KAN-168) |
| BG4 | **D2 in-flight leave** | **KAN-184** | AC-184-14, 15, 16, 17, 18 | UX — wizard step 3 | Architect | pytest + `tests/ui/test_vacation_workflow.py` |
| BG4 | **D2 in-flight org-change** | **KAN-184** | AC-184-19, 20, 21, 22, 23 | UX | Architect | pytest + real-DB tier |
| BG1 / compliance | **D3 retention** | **KAN-184** | AC-184-31; R3.1 – R3.3 | UX — retention settings | Architect (+ OQ-4) | pytest |
| BG1 / compliance | **D3 erasure & anonymisation** | **KAN-184** | AC-184-30, 32, 33, 34, 35 | UX — erasure confirmation | Architect | pytest + real-DB tier |
| BG1 / compliance | **D4 audit content** | **KAN-184** | AC-184-28, 29; R4.1, R4.2 | UX — audit view | **Architect owns schema** | pytest + real-DB tier |
| BG4 | **D5 status semantics** | **KAN-184** | AC-184-24, 25, 26, 27 | UX — status control | Architect | pytest |
| BG1 | Access revocation actually blocks login | **KAN-184** | **AC-184-03, 04**, 05, 06 | — | Architect | **`tests/ui/test_browser.py` (new check)** |
| BG4 | Offboarding failure & concurrency | **KAN-184** | AC-184-36 – 41 | — | Architect (needs KAN-155) | pytest |
| BG1 | Offboarding permissions | **KAN-184** | AC-184-42, 43, 44; §6.6 table | — | Architect | pytest |
| BG1 | Offboarding tenant isolation | **KAN-184** | AC-184-45, 46, 47, 48 | — | Architect | pytest (tenant-isolation tier) |
| BG4 | Transfer reuses the engine | KAN-185 | AC-185-01 – 06, 17, 18 | UX — transfer form | Architect | pytest + `tests/test_org_change.py` |
| BG4 | Transfer new rules (effective date, concurrency, leave follows manager) | KAN-185 | AC-185-07, 08, 09, 10, 11 | UX | Architect (CFL-4, CFL-5) | real-DB tier |
| BG4 | Transfer edge/tenancy | KAN-185 | AC-185-12 – 16, 19 | — | Architect | pytest |
| BG4 | Rehire continuity | KAN-186 | AC-186-01 – 09 | UX — later | Architect — later | later |

---

## 11. Dependencies

| ID | Dependency | Needed by | Status |
|---|---|---|---|
| DEP-1 | **KAN-155** — `transaction()` context manager for atomic multi-statement writes | CC-15, AC-184-03, AC-184-36. Offboarding is an eleven-statement unit; without it a mid-sequence failure leaves a half-offboarded employee — the worst possible state | Planned, roadmap S2 enabler. **Blocking for KAN-184.** |
| DEP-2 | **KAN-168** — real-DB integration test tier | AC-184-13, 32 and every criterion asserting final row state. The mocked suite cannot verify these | Planned, roadmap S2 enabler |
| DEP-3 | **KAN-166** — versioned migrations | The new feature codes (CC-6) and the audit table are schema changes | Planned, roadmap S2 enabler |
| DEP-4 | A **scheduled-job capability** (none exists — B16) | R3.3 automatic retention expiry, R5.6 future-dated offboarding. Both are downgraded to Should here because of this | **Not planned** → OQ-4 |
| DEP-5 | **EP28/KAN-148 real authentication** | R4.1 field 4 (session/IP in audit) is only meaningful afterwards | Deferred to S5 by D-004 — acceptable; audit fields stay nullable until then |

---

## 12. Open questions (block Definition of Ready where marked)

| ID | Question | Owner | Blocks | BA note |
|---|---|---|---|---|
| **OQ-1** | The epic promises "**promote**" but no story covers job-title / grade / `employment_type` change, and `org_change_requests` has no column for it. Add a story, extend KAN-185, or declare it out of scope? | **SPM** | **S1 freeze** — unallocated scope cannot be frozen | I have scoped it **out** of KAN-185 (§7.6) rather than inventing it. |
| **OQ-2** | Confirm the post-exit retention default (proposed **7 years**), the lawful bases in §4.3, and whether `gender` processing for vacation eligibility needs a documented justification. | **DPO / legal**, via SPM | KAN-184 configuration default only — the *mechanism* is not blocked | Charter §9.7 — I do not give legal advice. |
| **OQ-3** | Should `employee_certifications` be deletable at erasure, or retained where a regulated role required evidence of qualification? | **DPO / legal** + SPM | R3.6 row only | Defaulted to **delete**; a retention exception needs a controller decision. |
| **OQ-4** | Will a scheduled-job capability exist? Without it, automatic retention expiry and future-dated offboarding cannot be built. | **Architect + SPM** | Downgrades R3.3 and R5.6 from Must to Should | Manual "anonymise now" and immediate-only offboarding are specified as the S2 Must so KAN-184 is not blocked. |
| **OQ-5** | Is the Art. 15/20 subject-access export in EP38-S2, or a separate story? | **SPM** | Scope of KAN-184 | Specified as **Should** (R3.10). It is a distinct capability from erasure. |
| **OQ-6** | Is a same-day "undo mistaken offboarding" wanted? It is materially more complex than it looks — it must restore closed manager relationships, reopen org assignments, and un-cancel leave. | **SPM / product owner** | Nothing today — out of scope until answered (R5.4) | I did **not** invent a reversal window. Mistakes route through rehire. |
| **OQ-7** | Should offboarding be a **checklist** (like S1) as well as a wizard — laptop return, badge, exit interview as trackable tasks? | **SPM** | Scope of KAN-184 | Specified as a **wizard only**. A checklist is a natural extension of the S1 template engine if wanted. |
| **OQ-8** | Is **bulk offboarding** (site closure, mass redundancy) required for the first customer? Reassignment and re-pointing rules interact badly at volume — e.g. reassigning to someone who is themselves in the batch. | **SPM** | Nothing today — out of scope (§6.8) | Flagging now because retrofitting it into a single-subject transactional flow is expensive. |
| **OQ-9** | Confirm the default feature matrix in CC-6 — specifically whether `HR_ADMIN` should hold **delete** (erasure) by default. I have said **no**; erasure is irreversible and PORTAL_ADMIN/SYSTEM_ADMIN-only by default. | **SPM** | KAN-184 seed data | Tenants can widen it themselves through the existing matrix. |
| **OQ-10** | Company-configurable **termination reason categories** (R4.1 #10) — is a company-editable list required, or is a fixed platform list acceptable for the first customer? | **SPM** | Scope of KAN-184 | Specified as company-configurable; a fixed list would reduce scope. |

**Definition of Ready status:** KAN-184 and KAN-185 are **READY** subject to CFL-2 (Architect sign-off) and
DEP-1 (KAN-155). KAN-183 is **READY** subject to OQ-7. KAN-186 is **NOT READY** — outline only, by direction,
and correctly placed in Later.

---

## 13. Assumption & unknown register (new entries)

| Item | Type | Impact if wrong | Validation needed | Owner |
|---|---|---|---|---|
| The tenant company is the GDPR **controller** and the portal operator the **processor** | Assumption | Determines whether retention/erasure are per-company settings or platform policy — a structural product decision | Confirm with DPO / commercial terms | SPM |
| 7 years is a defensible default post-exit retention in the target jurisdictions | Assumption | Wrong default is a compliance exposure at every tenant | DPO per jurisdiction (OQ-2) | DPO |
| Companies will accept that terminal statuses are irreversible without an undo | Assumption | If wrong, HR will work around it by editing the DB — worse than a governed undo | Validate with the first customer / UAT | SPM (OQ-6) |
| A departing manager's reports usually move to one successor (bulk-set with per-report override is the right UX) | Assumption | Wrong shape means a painful screen for the most common case | UX to validate | UX |
| `employee_search_index` staleness does not affect leaver visibility (search filters `ACTIVE` at query time — B17) | Known, but fragile | If search is ever refactored to trust the index, leavers could reappear in search | Note for the Architect when EP19 is next touched | Architect |
| No tenant currently needs certification evidence retained past erasure | Unknown | Would change R3.6 | OQ-3 | DPO / SPM |
