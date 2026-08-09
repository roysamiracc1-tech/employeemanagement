# EP38 — Employee Lifecycle Workflows — Technical Design — 2026-08-09

> Produced by the **Senior Architect** (`../09_SENIOR_ARCHITECT.md`). This is the technical design for
> **EP38 (BG4 — "Complete the people-ops lifecycle")**, covering **KAN-183** onboarding checklist,
> **KAN-184** offboarding (the only **Must**), **KAN-185** transfer, and **KAN-186** rehire (Later —
> designed only far enough to record the blocker).
>
> **Why this file exists:** `ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` §4 closes with *"Growth epics EP36–EP41
> are broken down in later sprints."* EP38 has been pulled forward into build stage **S3**
> (roadmap §E, D-004) and the breakdown was the missing artifact. This document supplies it. It **extends**
> the kickoff — ADR numbering continues from **ADR-007**, and the registers in §10 are additions to the
> kickoff's §5.1 / §5.2, not replacements.
>
> **Scope boundary for this pass.** This is designed **against the roadmap** (`PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`
> §BG4) and **against the code as it exists on `chore/arch-review-and-hardening`**. The SPM is concurrently
> writing the EP38 story rows in `../../project-management/BACKLOG.md`, the BA the acceptance criteria, and UX
> the screen specs. **None of those were available to me and none are assumed here.** Where a decision is
> theirs, I design the *mechanism* and name the *owner of the policy* — I do not invent the requirement
> (Charter §9.2). A reconciliation pass against their output is required before code starts (§11, OQ-1).
>
> **Owner legend:** **ARCH** Senior Architect · **SNR** Senior Software Engineer · **MID** Mid-Level Engineer ·
> **DEVOPS** Senior DevOps Engineer. Every task obeys `../../CLAUDE.md` and the Engineering Charter DoD (§4).
>
> **Evidence convention:** `file:line` at the time of writing. Counts that will drift are given with the
> command that reproduces them (Charter §5b rule 3).

---

## 1. Verification — I re-derived every premise from the source before designing

I do not design against a brief I have not checked. All six premises handed to me hold; two are stronger than
stated, and I found **two additional findings (V7, V8) that materially change KAN-184's acceptance**.

| # | Finding | Evidence | Classification |
|---|---|---|---|
| **V1** | `employment_status` and `exit_date` already exist. No new column is needed for offboarding. Status is constrained to `ACTIVE / INACTIVE / RESIGNED / TERMINATED`; there is a supporting index. | `database/schema.sql:347` (`employment_status`), `:350` (`exit_date`), `:356` (CHECK), `:1471` (`idx_employees_company_status`) | **Known** |
| **V2** | **No route ever writes `employment_status` after creation.** The single `UPDATE employees` in the entire codebase writes `gender`. Offboarding is not "partially built" — it is *absent*. Status is only ever set to `'ACTIVE'` at insert time. | `app/routes/employees.py:144` is the only `UPDATE employees`; inserts hardcode `'ACTIVE'` at `app/routes/admin.py:181`, `:684`, `app/routes/company.py:126`. Reproduce: `grep -rn "UPDATE employees" app/` | **Known** |
| **V3** | **There is no audit table and no audit code anywhere.** The only matches for "audit" are *comments* describing `org_change_approvals` as a per-step decision trail. KAN-184's "full audit entry" is a **new subsystem**, not a new column. | `grep -rni audit database/schema.sql app/` returns nothing; `database/migrations/06_org_change_workflow.sql:10,48,71` are comments only | **Known** |
| **V4** | `apply_change()` performs **four** `execute()` calls (two unconditional, two conditional on a manager change) with no surrounding transaction, and `decide()` then issues a **fifth** status update outside it. `app/db.py` commits **per statement**, so each is independently durable. | `app/services/org_change_service.py:282`, `:287`, `:294`, `:298`, then `:249`; `app/db.py:29-33` (`execute` calls `db.commit()`) | **Known** |
| **V5** | `employees.email` and `employees.employee_number` carry **globally** unique constraints, not per-company. | `database/schema.sql:986` `employees_email_key UNIQUE (email)`, `:994` `employees_employee_number_key UNIQUE (employee_number)` | **Known** |
| **V6** | Login gates on `employment_status = 'ACTIVE'`, and the status filter is pervasive — **34 filter sites across 12 modules** at time of writing, not ~20. Much of "access removal" genuinely does fall out of a status flip. | `app/routes/auth.py:33`; also `helpers.py`, `org.py`, `dashboard.py`, `admin.py`, `benchmarks.py`, `company_scope.py`, `search_service.py`, `notification_service.py`, `org_change_service.py:88`, `org_change.py`, `company.py`. Reproduce: `grep -rn "employment_status *= *'ACTIVE'" app/ \| wc -l` | **Known** |
| **V7 — NEW** | **A status flip does not end an existing session.** `login_required` checks `'user_id' in session` and nothing else — it never revalidates against the database. `SESSION_LIFETIME` is **8 hours**. An employee offboarded at 09:00 keeps full portal access until their cookie expires. | `app/auth.py:16-22`; `app/config.py:18`; `app/routes/auth.py:99` (`session.permanent = True`) | **Known** |
| **V8 — NEW** | **Offboarding can deadlock an in-flight org-change request.** `_step_approver_user_ids()` filters approvers on `employment_status = 'ACTIVE'`, so offboarding the only eligible approver of a pending step returns an empty approver set. The request becomes permanently undecidable — `decide()` has no timeout, escalation or reassignment path. The same applies to an `approver_employee_id` configured in `org_change_workflow_steps`, which poisons *future* requests too. | `app/services/org_change_service.py:84-93` (ACTIVE filter), `:183-255` (`decide` — no escalation), `:78-83` (EMPLOYEE-type step) | **Known** |

**Two further facts that shape the design:**

- **The registration flow is already non-atomic.** Creating an employee issues up to five independently
  committed statements — `employees`, `employee_org_assignments`, two `manager_relationships`, `users`
  (`app/routes/admin.py:178-232`). A failure midway already leaves a half-created employee today. KAN-183
  inherits this surface, which is a second, independent argument for the KAN-155 dependency in §5.
- **There is no job scheduler.** `requirements.txt` contains exactly `flask`, `psycopg2-binary`, `werkzeug`,
  `pytest`, `pytest-flask` — no Celery, RQ, or APScheduler, and no cron evidence. **Any design that assumes a
  future-dated offboarding fires itself is designing infrastructure we do not have** (see ADR-013).

---

## 2. ADR-008 — Employee lifecycle state machine

**Decision: Build.** Codify the four existing statuses as an explicit, enforced state machine in
`app/services/lifecycle_service.py`. **Add no new status values and change no CHECK constraint in EP38.**

### 2.1 State semantics (currently undefined anywhere — this ADR defines them)

The schema constrains the four values but nothing in the repo says what they *mean*. That ambiguity is itself a
defect: two engineers will implement two different products. Binding definitions:

| Status | Meaning | Portal access | Appears in directory / org tree | Terminal |
|---|---|---|---|---|
| `ACTIVE` | Employed and current. | Yes | Yes | No |
| `INACTIVE` | Employed but suspended — long-term leave, secondment, disciplinary hold. **The employment relationship continues.** | No | No | No — reversible |
| `RESIGNED` | Employment ended, **employee-initiated**. | No | No | Yes (see §2.3) |
| `TERMINATED` | Employment ended, **employer-initiated**. | No | No | Yes (see §2.3) |

`RESIGNED` and `TERMINATED` are not a workflow ordering — they are **two mutually exclusive labels for the same
event**, distinguished by who initiated it. Nothing may transition between them as part of normal operation.

### 2.2 Legal transitions

```
                    ┌──────────────────────────── reinstate ─────────────────────────┐
                    ▼                                                                │
   (create) ──► ACTIVE ──── suspend ────► INACTIVE ───────────────────────────────────┘
                  │                          │
                  │  offboard                │  offboard
                  ▼                          ▼
        ┌──────────────────────────────────────────────┐
        │   RESIGNED          or          TERMINATED   │   ── rehire ──►  ✖ BLOCKED (KAN-186, §7)
        └──────────────────────────────────────────────┘
                  ▲                          ▲
                  └───── correct_exit_type ───┘   (HR_ADMIN only, audited, does not re-open employment)
```

| # | From | To | Trigger | Who may trigger | Reversible | Cascades |
|---|---|---|---|---|---|---|
| T1 | *(none)* | `ACTIVE` | `register_employee` (existing) | `user_accounts` + `employee_profiles` write | — | none (creation) |
| T2 | `ACTIVE` | `INACTIVE` | `lifecycle_service.suspend()` | `offboarding` **w** | **Yes** (T3) | C1, C2, C4, C6 — **not** C3, **not** C5 |
| T3 | `INACTIVE` | `ACTIVE` | `lifecycle_service.reinstate()` | `offboarding` **w** | — | reverses C1 (`is_active=TRUE`); does **not** resurrect closed org/manager rows |
| T4 | `ACTIVE` | `RESIGNED` \| `TERMINATED` | `lifecycle_service.offboard()` | `offboarding` **w** | **No** | C1–C7 (full) |
| T5 | `INACTIVE` | `RESIGNED` \| `TERMINATED` | `lifecycle_service.offboard()` | `offboarding` **w** | **No** | C1–C7 (full) |
| T6 | `RESIGNED` | `TERMINATED` (and reverse) | `lifecycle_service.correct_exit_type()` | **HR_ADMIN or PORTAL_ADMIN only** — an explicit correction API, never the offboarding flow | — | **none** — status label + audit row only |
| T7 | `RESIGNED` \| `TERMINATED` | `ACTIVE` | rehire | **✖ REJECTED in EP38** | — | see §7 |

T6 exists because the alternative is worse. Without a sanctioned correction path an HR admin who miscodes a
departure has no in-app remedy, and the workaround is a manual `UPDATE` against production — unaudited, and
exactly the class of change this epic exists to eliminate. It is deliberately a separate, narrower API that
changes **only** the label and writes an audit row; it does not re-run any cascade and it cannot reach `ACTIVE`.

### 2.3 Invariants — enforced in `lifecycle_service`, not in a route

1. **No self-transition.** An actor may never change their own `employment_status`, in any transition, at any
   privilege level including SYSTEM_ADMIN. This mirrors the org-change rule that an employee can never
   initiate their own move (`CLAUDE.md` §Position Change Workflow #2; `app/routes/org_change.py:23-27`).
   The feature flag alone is **not** sufficient — this is a business-rule check, like `_can_initiate_for`.
2. **Company scope.** Every read and write is `company_id = %s::uuid`. Never `OR company_id IS NULL`. A
   SYSTEM_ADMIN acting cross-company must pass an explicit `company_id`; it is never inferred from session.
3. **No tenant lockout.** `offboard()` and `suspend()` **must refuse** if the subject holds the company's
   **last** `PORTAL_ADMIN` role grant. A tenant that cannot administer itself is a support incident with no
   in-app remedy. Refusal is a 409 with a specific message, not a generic error.
4. **Terminal means terminal.** `RESIGNED`/`TERMINATED` are terminal for the lifecycle service. The only
   permitted onward edges are T6. Any request for T7 returns a structured `REHIRE_NOT_SUPPORTED` error
   referencing KAN-186 — it must fail loudly, never silently no-op.
5. **Every transition writes exactly one `EMPLOYEE_STATUS_CHANGED` audit row**, plus one row per cascade
   effect (§3.4), inside the same transaction as the transition (§5).
6. **Illegal transitions raise.** The service holds an explicit `_LEGAL = {(from, to): handler}` map. An
   unlisted pair raises `IllegalTransition` — it never falls through to a permissive default.

### 2.4 Cascades

| ID | Target | On offboard (T4/T5) | On suspend (T2) | Notes |
|---|---|---|---|---|
| **C1** | `users` | `is_active = FALSE` for every user row with this `employee_id` | same | Second gate on top of the status filter at `app/routes/auth.py:33`. |
| **C2** | **live sessions** | Must be revoked — **does not happen today (V7)** | same | See §5.3. This is a genuine gap in KAN-184's "revokes portal access" AC. |
| **C3** | `user_roles` | **RETAIN — do not delete** | retain | Rationale below. |
| **C4** | `manager_relationships` (subject as employee) | `is_current = FALSE`, `effective_to = exit_date` | `is_current = FALSE`, `effective_to = CURRENT_DATE` | History preserved; rows are never deleted. |
| **C5** | `manager_relationships` (subject as **manager**) | **The orphaned-reports problem — §6** | **not applied** — a suspended manager still holds the relationship | The asymmetry is deliberate: suspension is temporary. |
| **C6** | `employee_org_assignments` | close current row (`is_current = FALSE`, `effective_to = exit_date`) | **not applied** | A suspended employee still belongs to their unit. |
| **C7** | in-flight requests | see table below | pending items are **left alone** — they resume on reinstate | |

**C3 — why roles are retained, not deleted.** Deleting `user_roles` is irreversible, destroys the record of
what access the person held (the exact thing an audit trail is for), and would silently strip roles on
reinstate (T3). It buys nothing: access is already denied by `users.is_active = FALSE` (C1) plus the 34
`employment_status = 'ACTIVE'` filter sites (V6), and the org-change approver query excludes them at
`org_change_service.py:84-93`. **One exception to escalate to the BA:** a departing holder of a
cross-company-capable grant. Retaining that grant on a dormant account is a different risk calculus from
retaining `EMPLOYEE`. I recommend the service flags it and the BA rules on the policy — I will not invent it.

**C7 — in-flight requests.**

| Object | Subject's role in it | Mechanism |
|---|---|---|
| `vacation_requests` | requester, `status='PENDING'` | Cancel → `status='CANCELLED'` (permitted by `chk_vr_status`, `schema.sql:742`). |
| `vacation_requests` | requester, `status='APPROVED'`, dates **after** `exit_date` | **Policy is the BA's call.** Mechanism: `pending_leave_policy` parameter — `CANCEL` \| `RETAIN`. Default `CANCEL`, overridable. Leave that outlives employment is a payroll question, not an engineering one. |
| `vacation_requests` | **approver** (`manager_id`), `status='PENDING'` | Re-point `manager_id` to the resolved successor from §6 — otherwise the request is unapprovable. Must happen in the same transaction as the manager re-point. |
| `org_change_requests` | subject (`employee_id`), `status='PENDING'` | Cancel. **Via `org_change_service`, never by direct UPDATE** — see §4.2. |
| `org_change_requests` | sole eligible approver of the current step | **V8 deadlock.** Mechanism in §6.4. |
| `org_change_workflow_steps` | `approver_employee_id` = subject | Poisons all *future* requests. Detect and **warn at offboarding time**; do not silently rewrite a tenant's configured workflow. |

---

## 3. ADR-009 — Audit subsystem (`audit_log` + `audit_service`)

**Decision: Build.** A single append-only `audit_log` table plus `app/services/audit_service.py`. Rejected
alternatives: per-entity audit tables (N tables, N migrations, no cross-entity timeline); Postgres logical
decoding / CDC (operationally heavy, no deploy target exists — TR-5); an off-the-shelf library (none fits raw
`psycopg2` with no ORM).

This is the highest-leverage piece of EP38. **It is a platform capability, not a KAN-184 detail** — the
roadmap already commits EP35 (import) and EP39 (accruals) to the same surface, and Charter §7 makes
"comprehensive audit logging" a baseline. Getting the shape right once is worth more than KAN-184 itself.

### 3.1 Table

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id                BIGSERIAL PRIMARY KEY,
    company_id        UUID        NOT NULL REFERENCES companies(id),
    actor_user_id     UUID            NULL REFERENCES users(id)     ON DELETE SET NULL,
    actor_employee_id UUID            NULL REFERENCES employees(id) ON DELETE SET NULL,
    actor_label       VARCHAR(255)NOT NULL,
    action            VARCHAR(60) NOT NULL,
    entity_type       VARCHAR(50) NOT NULL,
    entity_id         UUID        NOT NULL,
    before_state      JSONB           NULL,
    after_state       JSONB           NULL,
    metadata          JSONB       NOT NULL DEFAULT '{}'::jsonb,
    retention_class   VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON audit_log (company_id, entity_type, entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_company_time
    ON audit_log (company_id, created_at DESC);
```

**`BIGSERIAL`, not UUID.** The only access patterns are append and range-scan by time. A monotonic key keeps
inserts at the B-tree right edge and keeps the row narrow; random UUIDv4 PKs on a high-insert append-only table
buy nothing here. This is the one place in the schema where deviating from the UUID convention is justified,
and it is deliberate — engineers should not "fix" it.

**`actor_label` is denormalised on purpose.** `actor_user_id` is `ON DELETE SET NULL`; without a captured
label, deleting a user silently anonymises their entire history. An audit trail that forgets who acted is not
an audit trail. Store `"Firstname Lastname <email>"` as it was **at the time of the action**.

**`TIMESTAMPTZ`, not `TIMESTAMP`.** Every other timestamp in `schema.sql` is `timestamp without time zone`.
That is a latent bug the moment a tenant operates in a second timezone, and an audit trail is the one table
where "when" must be unambiguous. New table, new convention, no migration cost. Logged as **TD-12** so the
inconsistency is visible rather than silently divergent.

### 3.2 The four decisions I was asked to make and justify

**(a) Append-only? — Yes, and enforced in the database, not by convention.**

Application code issues `INSERT` only. That is a convention, and conventions decay. Add a trigger:

```sql
CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (attempted %)', TG_OP;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_log_no_update
    BEFORE UPDATE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
```

**`UPDATE` is blocked unconditionally. `DELETE` is deliberately left unblocked**, because retention purge
(3.2d) must be able to delete and this codebase has **no database role separation** to distinguish a purge job
from the app user. Blocking `DELETE` too would either make retention impossible or force a
`SET LOCAL`-flag escape hatch that any code path could set — worse than an honest gap. The correct fix is a
dedicated purge role, which belongs with the purge job itself. Recorded as **TD-13**; not in EP38 scope.
I would rather ship a guarantee that is 80% real and documented than 100% claimed and circumventable.

**(b) JSONB for before/after? — Yes, holding diffs only, never full rows.**

*Why JSONB:* one table must serve `employee`, `user`, `import_batch`, `vacation_policy` and whatever EP39
adds. Typed columns would force either a table per entity or a sparse wide table; both are worse. The accepted
cost is no referential integrity inside the blob — correct, because a snapshot must **not** track later
changes to the live row. That is the point of a snapshot.

*Why diffs only, and this is the load-bearing half:* storing whole `employees` rows would copy name, email,
phone and job title into a permanently retained table on **every** edit. That multiplies the PII surface,
multiplies GDPR erasure obligations, and bloats the table for no analytical gain. Store the changed fields plus
identity:

```json
{"employment_status": "ACTIVE", "exit_date": null}                      // before_state
{"employment_status": "TERMINATED", "exit_date": "2026-09-30"}          // after_state
{"reason": "End of contract", "offboarding_id": "…", "correlation_id": "…"}  // metadata
```

**Hard rule for engineers: never put a password hash, token, or free-text PII narrative in `before_state` /
`after_state`.** Reasons and notes go in `metadata` and are subject to the same rule. This is a review-gate
item, not a suggestion.

**No GIN index on the JSONB columns.** Nothing queries inside the blobs today. Adding one is premature
optimisation with a real write cost. Add it when a query needs it.

**(c) Retention? — Mechanism now, number later. The number is not mine to invent.**

`retention_class` (`STANDARD` / `EMPLOYMENT` / `SECURITY`) is written at record time, so a future purge job
filters on one indexed-adjacent column instead of maintaining a map of every `action` code it has never heard
of. That decoupling is the whole reason the column exists, and it costs 20 bytes.

The retention **periods** are a legal determination — GDPR storage limitation versus statutory employment-record
retention, which varies by jurisdiction. Charter §9 forbids me inventing them and §1 forbids giving legal
advice. **Classification: Needs Validation — owner: DPO/legal via the SPM.** Until they rule, nothing is
purged, which is the safe default (over-retention is remediable; premature deletion is not).

**The purge job itself is explicitly out of EP38 scope.** It needs a scheduler that does not exist, and a
DB role that does not exist. Recorded as **TD-13/TD-14** with a follow-on story.

**(d) GDPR conflict — stated, not buried.** An erasure request against an employee conflicts with an
append-only audit trail. Diff-only storage minimises but does not eliminate this. The known resolution shape
is pseudonymisation of `actor_label` and identity fields rather than row deletion — but that requires `UPDATE`,
which (a) forbids. **This is a genuine unresolved tension. Flagged to the DPO as OQ-4 rather than
quietly designed around.** It does not block KAN-184.

### 3.3 Interface — `app/services/audit_service.py`

```python
def record(action, entity_type, entity_id, *, company_id, actor,
           before=None, after=None, metadata=None, retention_class='STANDARD'): ...
def record_many(entries): ...
def entity_timeline(company_id, entity_type, entity_id, limit=50, offset=0): ...
def company_timeline(company_id, *, action=None, actor_user_id=None,
                     since=None, until=None, limit=50, offset=0): ...
```

`actor` is the same light dict the org-change engine already uses —
`{'user_id', 'employee_id', 'roles', 'company_id'}` (`org_change_service.py:16`). Reuse it; do not invent a
second actor shape.

**The single most important property: `record()` must never open its own connection or commit.** It writes
through `app.db.execute` on the request-scoped `g.db` (`app/db.py:11-14`), so it joins whatever transaction the
caller has open. If audit committed independently, a **rolled-back** offboarding would leave an audit row
claiming an employee was terminated when they were not. **A false audit entry is worse than a missing one.**

Corollary, and engineers must internalise it: **failed and rejected attempts are not in `audit_log`.** They
roll back with everything else. Authorisation denials and validation failures go to the structured application
log. `audit_log` records what *happened*, not what was *attempted*.

**Company scoping.** `company_id` is `NOT NULL` and is taken from the **affected entity**, never from the
session and never from request input. When a SYSTEM_ADMIN acts across tenants the row lands in the *affected
tenant's* trail with the admin as actor — the tenant must be able to see actions taken against them. Every read
filters `company_id = %s::uuid` only, never `OR company_id IS NULL` (`CLAUDE.md`).

### 3.4 Action vocabulary for EP38

`EMPLOYEE_STATUS_CHANGED` · `EMPLOYEE_OFFBOARD_INITIATED` · `EMPLOYEE_OFFBOARD_COMPLETED` ·
`EMPLOYEE_OFFBOARD_CANCELLED` · `EMPLOYEE_SUSPENDED` · `EMPLOYEE_REINSTATED` · `EMPLOYEE_EXIT_TYPE_CORRECTED` ·
`USER_ACCESS_REVOKED` · `MANAGER_RELATIONSHIP_CLOSED` · `MANAGER_REPORTS_REASSIGNED` ·
`ORG_ASSIGNMENT_CLOSED` · `VACATION_REQUEST_CANCELLED_BY_LIFECYCLE` · `ORG_CHANGE_CANCELLED_BY_LIFECYCLE` ·
`CHECKLIST_STARTED` · `CHECKLIST_TASK_COMPLETED` · `CHECKLIST_COMPLETED`.

Verbs are past tense and describe **what happened to the entity**. EP35 and EP39 extend this list; they do not
redefine the shape.

### 3.5 Growth — sized, not hand-waved

| Source | Volume estimate | Verdict |
|---|---|---|
| EP38 lifecycle events | 10k employees × ~5 events/yr ≈ **50k rows/yr/tenant** | Negligible |
| EP39 accruals | if per-employee-per-month ≈ **120k rows/yr/tenant** | Acceptable |
| **EP35 bulk import** | if **one row per imported record**, a monthly full import of 10k employees = **120k rows/yr/tenant**, and a daily sync = **3.6M** | **This is the growth driver** |

**Directive to whoever builds EP35: bulk import writes ONE batch-level audit row** (`IMPORT_BATCH_COMMITTED`
with counts and the batch id in `metadata`), **not one row per record.** Per-record detail already lives in
`employee_import_rows` (`schema.sql`, FK at `:1864`), which is the correct home for it. This single decision is
the difference between a table that stays small indefinitely and one that needs partitioning within a year.

**No partitioning now.** At the volumes above it is speculative complexity. Revisit past ~50M rows or when
`idx_audit_company_time` scans degrade — whichever comes first. Recorded as **TR-13** so it is watched, not
forgotten.

---

## 4. ADR-010 — The `lifecycle_service` boundary

**Decision: Build `app/services/lifecycle_service.py`. Reuse `org_change_service` unchanged for all
approval-gated moves.** The boundary below is normative — a PR that crosses it is returned.

### 4.1 Ownership

| Concern | Owner | Never |
|---|---|---|
| `employment_status` transitions + cascades C1–C7 | **`lifecycle_service`** | never inline in a route |
| Onboarding / offboarding checklist instances and task completion | **`lifecycle_service`** | — |
| Offboarding orchestration (initiate → complete → cancel) | **`lifecycle_service`** | — |
| Rehire eligibility probe (KAN-186) | **`lifecycle_service`** | — |
| Writing audit rows | **`audit_service`**, called by `lifecycle_service` | lifecycle never `INSERT`s into `audit_log` directly |
| Proposal → **sequential approval** → apply, for BU / FU / location / manager | **`org_change_service` — unchanged** | `lifecycle_service` must **never** implement, wrap, shortcut, or duplicate approval logic |
| Cancelling an org-change request | **`org_change_service`** | `lifecycle_service` must never `UPDATE org_change_requests` |

`CLAUDE.md` §Position Change Workflow #5 is explicit: *"The engine lives in
`app/services/org_change_service.py`; reuse it — do not re-implement approval logic inline in routes."* The
same prohibition applies to services. **The failure mode this prevents is concrete:** an engineer under
schedule pressure adds a "quick" manager re-point inside `lifecycle_service` for a transfer, and the sequential
approval chain is silently bypassed for that path. That is a Critical access-control defect, and it is exactly
how it would arrive.

### 4.2 The one permitted call direction

```
routes/lifecycle.py ──► lifecycle_service ──► audit_service ──► app.db
                             │
                             ├──► org_change_service.cancel_system(...)   ← the ONLY write into org-change tables
                             └──► org_change_service.workflow_steps(...)  ← read-only introspection

routes/transfer.py  ──► org_change_service.create_request(...)            ← KAN-185: no lifecycle involvement at all
```

`lifecycle_service` may **read** org-change state freely. It may **write** only through one new function:

```python
# app/services/org_change_service.py — new, owned by the org-change engine
def cancel_system(request_id, actor, reason):
    """Cancel a PENDING request as a consequence of a lifecycle event.
    Bypasses the requester/admin check in cancel() — the caller is the system, not a user —
    but is otherwise identical: PENDING-only, company-scoped, audited, applies nothing."""
```

The existing `cancel()` requires the actor to be the requester or an admin
(`org_change_service.py:306-319`); a system-initiated cancel satisfies neither. Adding `cancel_system` inside
the engine keeps the engine the sole writer of its own tables. **`lifecycle_service` never issues SQL against
`org_change_*`.**

### 4.3 KAN-185 is much smaller than it looks — and that is a finding

*Observation:* KAN-185 asks for "a transfer flow (BU/location/manager) reusing the org-change engine."
*Evidence:* `org_change_service.create_request()` already accepts exactly
`{business_unit_id, functional_unit_id, location_id, manager_id}` (`:136-178`) and already routes them through
the sequential chain. A transfer **is** an org change — there is no functional gap.
*Impact:* KAN-185 needs **no new engine code, no new table, no new feature code**. It is a task-oriented entry
point — a "Transfer employee" screen and route that collects the fields and calls `create_request()` — plus
tests proving the chain cannot be bypassed. Estimated **1.5–2 dev-days**, not the week its S3 slotting implies.
*Recommendation:* re-point KAN-185's effort at the **anti-bypass test suite** (§9, T-185-3) rather than at new
code. The risk in KAN-185 is not building it — it is someone building a second path.
*Expected outcome:* EP38 absorbs the audit subsystem cost without extending the epic. **Confidence: High.**

**Open question to the BA (OQ-2):** should a transfer carry a `reason_category` (`TRANSFER` /
`PROMOTION` / `RESTRUCTURE`)? `org_change_requests` has free-text `reason` only. If yes it is one nullable
column and one migration; if no, zero work. Requirement, not architecture — the BA rules.

---

## 5. Transaction strategy — and the KAN-155 dependency

### 5.1 The exposure

A single `offboard()` call writes to **six tables plus `audit_log`**: `employees`, `users`,
`manager_relationships` (twice — subject and reports), `employee_org_assignments`, `vacation_requests`,
`org_change_requests`, `audit_log`. That is **12–20 statements** depending on the report count.

`app/db.py:29-33` commits **after every statement** (V4). With no transaction, a failure at statement 7 leaves
a durable, self-inconsistent state — for example:

> `employees.employment_status = 'TERMINATED'` committed · `users.is_active` still `TRUE` · reports still
> pointing at the departed manager · **no audit row at all**, because audit is written last.

The employee is terminated in the directory, still able to log in, still an approver, and there is **no record
that anything happened**. That is a Critical data-integrity and access-control defect in the one story whose
entire purpose is a clean, auditable departure. It is not an edge case — any constraint violation,
serialisation failure, or connection drop produces it.

### 5.2 The dependency, stated plainly

**KAN-155 must land before KAN-184 starts. It must NOT be delivered as part of EP38.** Three reasons:

1. **Scope.** ADR-006 changes `execute()` to stop committing per statement (`ARCHITECT_KICKOFF §3`). That
   changes transactional semantics for **every** existing write path — vacations, admin, company, imports —
   not just EP38. Bundling a cross-cutting data-layer change into a feature story produces a PR no one can
   review against acceptance criteria, and it couples EP38's delivery date to a refactor of unrelated code.
   Charter §5: *"Keep PRs small and single-purpose."*
2. **Sequencing already agrees.** The roadmap places KAN-155 in **S2 — Foundation enablers**, explicitly
   ahead of **S3**, where EP38 is built (roadmap §E, lines 276–277), and already names it *"a direct dependency
   of EP35-S2"*. EP38 is the **second** consumer, which strengthens the existing plan rather than changing it.
   I am hardening an existing dependency into a hard gate, not introducing a new one.
3. **Audit correctness depends on it.** Per §3.3, `audit_service.record()` deliberately does not commit. Under
   today's `execute()` **every audit row commits immediately anyway**, so a later rollback cannot retract it —
   producing false audit entries, the exact failure §3.3 is designed to prevent. **Without KAN-155 the audit
   subsystem cannot be built correctly at all.** This makes KAN-155 a blocker for the *audit* work too, not
   only for the multi-table write.

**If KAN-155 slips, KAN-184 does not start.** There is no acceptable degraded mode: shipping a non-atomic
offboarding means shipping a known path to a user who is terminated-but-can-still-log-in. I will not certify
that. Contingency if the SPM needs EP38 to start regardless: KAN-183's checklist tables (§8.2) are
single-table writes and can proceed — but the Must story cannot.

### 5.3 The session gap (V7) — required for KAN-184's own acceptance

The AC says offboarding *"revokes portal access."* It does not, for up to **8 hours** (V7). Options:

| # | Option | Cost | Verdict |
|---|---|---|---|
| O1 | Accept the 8h window | zero | **Reject.** The AC says revoke. An 8-hour window for a terminated employee is precisely the risk this story exists to close, and it will be found in UAT. |
| O2 | Server-side session store (Redis/DB) with explicit revocation | new dependency + infra; no deploy target (TR-5) | **Reject for EP38.** Correct long-term; disproportionate now. |
| O3 | **Revalidate `users.is_active` + `employees.employment_status` once per request in `login_required`, cached in `g`** | **one indexed query per request** | **Adopt.** |
| O4 | Session epoch counter compared per request | same query cost as O3, plus a new column | Reject — same cost, more moving parts. |

**O3 is nearly free in context.** `_load_feature_access()` already issues a per-request DB query for every
non-SYSTEM_ADMIN user (`app/auth.py:38-75`) and caches it on `g`. O3 adds one more single-row indexed lookup on
the same connection, cached identically. Revocation becomes effective on the **next request**, which satisfies
"revokes access" in any practical reading.

**This is a change to `app/auth.py`, a security boundary — ARCH-reviewed, and it needs its own regression
pass** because it puts a new failure mode in front of *every* authenticated route. Tasked as **T-184-2** and
deliberately sequenced **first** within KAN-184 so it is not rushed at the end.

### 5.4 Rules for engineers

- One `with transaction():` per public `lifecycle_service` entry point. **Not** per cascade, **not** per table.
- `audit_service.record()` is called **inside** that block, always.
- Notifications (`notification_service`) are called **after** commit. A notification cannot be rolled back;
  emailing "you have been offboarded" for a transaction that failed is unrecoverable.
- Never nest `transaction()`. If a helper needs the transaction, it takes the open context — it does not open
  its own.

---

## 6. ADR-011 — The orphaned-reports problem

**The business rule is the BA's. The mechanism is mine. This section designs the mechanism and implements all
three policies so the BA's answer is a configuration choice, not a rewrite.**

### 6.1 The problem, precisely

`manager_relationships` rows survive the subject's offboarding untouched (there is no cascade today because
there is no offboarding today — V2). The org tree joins on `mgr.employment_status = 'ACTIVE'`
(`app/routes/org.py:76`, `:85`), so every report of a departed manager is **silently dropped from the
reporting structure** — they do not appear under the old manager, and they appear under no one. In addition:

- Their pending vacation requests point at `manager_id` = the departed manager and become **unapprovable**
  (there is no reassignment path in the vacation flow).
- They cannot be the subject of a manager-initiated org change, because `_can_initiate_for` resolves the
  solid-line manager (`app/routes/org_change.py:23-27`) and gets an inactive one.

This is not cosmetic. It breaks two live workflows.

### 6.2 Options

| # | Mechanism | Pros | Cons |
|---|---|---|---|
| **O1** | Do nothing | zero cost | Breaks the org tree and vacation approvals. **Reject.** |
| **O2** | **Escalate** — re-point each report's `SOLID_LINE` to the departing manager's own solid-line manager | Deterministic, needs no input, never blocks an urgent termination, keeps the tree connected | Can create a wide span at the grandparent; may be organisationally wrong |
| **O3** | **Successor** — HR names a replacement manager at offboarding; refuse if the subject has reports and none is given | Organisationally correct | Blocks a termination that must happen *now*; fails if the successor is not yet hired |
| **O4** | Route each report through `org_change_service` as an approval request | Consistent with the transfer path | **Reject — actively wrong.** N pending approvals leave the tree broken until each is approved; the departing manager may be the *approver* (V8), deadlocking immediately; and it inverts the semantics — the move is a **consequence of an already-approved offboarding**, not a new proposal awaiting approval |
| **O5** | Leave reports unassigned and surface an HR work-queue item | Explicit, no wrong guess | Tree stays broken until worked; needs a queue UI that does not exist |

### 6.3 Recommendation

**Implement O2, O3 and O5 as one parameter. Default to O3-with-O2-fallback. Reject O4 permanently.**

```python
lifecycle_service.offboard(
    employee_id, *, exit_date, target_status, exit_type, reason, actor, company_id,
    successor_manager_id=None,
    reports_policy='SUCCESSOR_ELSE_ESCALATE',   # | 'ESCALATE' | 'REQUIRE_SUCCESSOR' | 'UNASSIGN'
    pending_leave_policy='CANCEL',
)
```

`SUCCESSOR_ELSE_ESCALATE` — use `successor_manager_id` if supplied; otherwise re-point to the departing
manager's own solid-line manager; if *that* is also absent (the subject was a company root), fall back to
`UNASSIGN` and record it. This never blocks an urgent departure and never silently leaves the tree broken.

**Why O4 is rejected permanently, and why this does not contradict `CLAUDE.md`:** the invariant is that
approval *logic* lives in `org_change_service` and is never re-implemented. `lifecycle_service` does not
implement approval logic here — **there is no approval in this path at all.** The re-point is the mechanical
application of an offboarding decision that has already been made and audited, exactly as
`org_change_service.apply_change()` writes `manager_relationships` directly once its own chain has completed.
The invariant forbids a *second approval engine*; it does not forbid a direct write that is not an approval.
Engineers: if you find yourself adding an approver, a step, or a status to this path, **stop — you are building
the thing the invariant forbids.**

### 6.4 Mechanism — inside the offboarding transaction

1. `SELECT` all reports where `manager_id = subject AND is_current` (both `SOLID_LINE` and `DOTTED_LINE`,
   company-scoped).
2. Resolve the successor per `reports_policy`. Validate: successor must be `ACTIVE`, in the same company, and
   **not** the subject (`chk_not_self_manager`, `schema.sql:manager_relationships`).
3. Per report: close the old row (`is_current = FALSE`, `effective_to = exit_date`); insert a new row where a
   successor was resolved. **Never `UPDATE manager_id` in place** — that destroys reporting history, and the
   table's `effective_from`/`effective_to`/`is_current` shape exists precisely to preserve it.
4. Re-point `vacation_requests.manager_id` for that report's **PENDING** requests to the successor. Skip if
   `UNASSIGN`, and surface those as an HR follow-up.
5. **V8 handling:** find `org_change_approvals` on `PENDING` requests where the subject is the sole eligible
   approver of the **current** step. Do **not** auto-approve and do **not** silently reassign a tenant's
   approval chain. Cancel via `org_change_service.cancel_system(..., reason='APPROVER_OFFBOARDED')` and notify
   the requester to re-raise. **Cancelling loses no data and applies nothing** (`org_change_service.py:317`);
   auto-approving would apply an unapproved org change, and reassigning would silently rewrite the tenant's
   configured governance. Cancellation is the only option that violates no invariant.
6. Warn (do not rewrite) if the subject appears in `org_change_workflow_steps.approver_employee_id` — future
   requests will deadlock until an admin edits the chain. Surfaced in the offboarding result payload.
7. One audit row per re-pointed report (`MANAGER_REPORTS_REASSIGNED`) and per cancelled request.

**Policy questions for the BA (OQ-3):** does a *dotted-line* report follow the same rule as solid-line?
Should the default be `REQUIRE_SUCCESSOR` for a manager with more than N reports? Both are one-line
configuration against the mechanism above.

---

## 7. KAN-186 rehire — designed only far enough to record the blocker

**Verdict: correctly deferred to Later. It is blocked on schema, not on effort.** Two independent blockers:

**B1 — Global unique constraints (V5).** `employees_email_key UNIQUE (email)` and
`employees_employee_number_key UNIQUE (employee_number)` are global, not per-company. A returning employee
therefore cannot be inserted as a new row, and no `company_id` scoping can work around a global constraint.

This is **also a live multi-tenancy defect independent of rehire**, which is the more urgent point:

- Two tenants cannot both employ the same person — a real scenario for contractors, and for a group of
  companies on one deployment.
- Employee numbers cannot be tenant-sequential. Tenant B is refused `E001` because tenant A holds it.
- It is an **enumeration oracle**: a tenant admin can probe another tenant's employee numbers and email
  addresses by observing which values are refused at registration
  (`app/routes/admin.py:165-170` reports "already taken" without any company filter). That is a cross-tenant
  information leak in a system whose Charter §3.3 makes tenant isolation a security *and* compliance
  requirement.

*Fix shape (not EP38):* drop both constraints, add `UNIQUE (company_id, email)` and
`UNIQUE (company_id, employee_number)`, and make the duplicate checks in `admin.py` company-scoped.
Reversible; requires a duplicate audit across existing data first. Recorded as **TD-15, P1.**

**B2 — There is no employment-period model.** `employees` carries a single `join_date` and a single
`exit_date` (`schema.sql:220`, `:350`). A rehire must either overwrite the first employment's dates —
destroying the history the story exists to preserve — or create a second `employees` row, which B1 forbids and
which would fragment 16 foreign-key relationships (`grep -c "REFERENCES public.employees(id)" database/schema.sql`
→ 16) across two identities.

*Fix shape:* an `employments` child table (`employee_id`, `sequence`, `join_date`, `exit_date`,
`employment_type`, `exit_type`, `is_current`), with `employees` holding stable identity only. That is a
**materially larger change than all of EP38 combined** — it touches every query that reads `join_date`,
tenure, or `employment_status`, and every one of those 34 filter sites (V6).

**Recommendation:** KAN-186 stays in **Later**, and stays blocked on TD-15 (B1) and a dedicated
employment-period story (B2). **Do not attempt a partial rehire** — reactivating a terminated row in place is
the obvious shortcut and it silently destroys the prior employment's dates and audit continuity, which is the
one thing the story asks for. It is worse than not shipping. **Confidence: High.**

---

## 8. Data model & migration

### 8.1 Migration file

**`database/migrations/08_employee_lifecycle.sql`** — follows the established conventions:
`CREATE TABLE IF NOT EXISTS`, `INSERT … ON CONFLICT DO NOTHING`, fully idempotent, banner comment listing what
it adds (pattern: `06_org_change_workflow.sql:1-13`).

**Reversibility (Charter §4 DoD).** Every object is additive — no column is dropped, no constraint altered, no
existing row rewritten. A companion `08_employee_lifecycle_down.sql` drops the five new tables, the trigger,
the function, and the two `portal_features` rows with their `role_feature_access` children in FK-safe order.
**Rollback is therefore clean and total** *provided it runs before any tenant data lands in the new tables* —
after that, dropping `audit_log` destroys audit history and the rollback becomes a data-loss event. That
caveat goes in the runbook (T-184-9, DEVOPS); it is the kind of thing that must be known **before** an incident,
not discovered during one.

Per ADR-004, if KAN-166 (Alembic) has landed by build time this ships as an Alembic raw-SQL revision instead,
and `schema.sql` is regenerated as the baseline. Either way `setup_db.py` and the migration must not diverge —
that is finding F9 and KAN-167 owns it.

### 8.2 New tables

**Checklist machinery — generalised across onboarding and offboarding.** One set of tables with a `kind`
discriminator, not two near-identical sets:

```sql
lifecycle_checklist_templates (
    id, company_id NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('ONBOARDING','OFFBOARDING')),
    name, is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at,
    UNIQUE (company_id, kind, name)
)

lifecycle_checklist_template_tasks (
    id, template_id NOT NULL REFERENCES … ON DELETE CASCADE,
    sort_order INT NOT NULL, title, description,
    assignee_type VARCHAR(12) NOT NULL CHECK (assignee_type IN ('ROLE','MANAGER','EMPLOYEE')),
    assignee_role VARCHAR(50), assignee_employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    due_offset_days INT NOT NULL DEFAULT 0,
    UNIQUE (template_id, sort_order),
    CHECK ( (assignee_type='ROLE'     AND assignee_role IS NOT NULL AND assignee_employee_id IS NULL)
         OR (assignee_type='EMPLOYEE' AND assignee_employee_id IS NOT NULL AND assignee_role IS NULL)
         OR (assignee_type='MANAGER'  AND assignee_role IS NULL AND assignee_employee_id IS NULL) )
)

employee_checklists (
    id, company_id NOT NULL, employee_id NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL CHECK (kind IN ('ONBOARDING','OFFBOARDING')),
    template_id UUID NULL REFERENCES … ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('IN_PROGRESS','COMPLETED','CANCELLED')),
    started_at, completed_at
)

employee_checklist_tasks (
    id, checklist_id NOT NULL REFERENCES … ON DELETE CASCADE,
    sort_order INT NOT NULL, title, description,
    assignee_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    assignee_role VARCHAR(50), due_date DATE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING','DONE','SKIPPED')),
    completed_by_user_id UUID NULL, completed_at, note
)
```

**Two design points that are load-bearing:**

1. **This mirrors `org_change_workflows` / `org_change_workflow_steps` deliberately** (same
   template-header/ordered-steps/`ROLE`-or-`EMPLOYEE` shape, same paired CHECK). Engineers already know this
   pattern from `06_org_change_workflow.sql`; a novel shape would be gratuitous.
2. **Template tasks are snapshotted into instance tasks at start**, exactly as `create_request()` snapshots
   workflow steps into `org_change_approvals` (`org_change_service.py:162-168`). Editing a template must never
   retroactively mutate a live checklist. This is an invariant, and it is why `template_id` is
   `ON DELETE SET NULL` rather than `CASCADE`.

**Generalising is justified, not speculative** (Charter §3.1 — *"add abstraction when a second real case
demands it"*): both cases are in scope in this same epic, right now. It also resolves the awkwardness of S2
being built before S1 — **KAN-184 creates these tables with `kind='OFFBOARDING'`, and KAN-183 adds
`kind='ONBOARDING'` plus the template admin UI at near-zero marginal schema cost.**

**Offboarding record:**

```sql
employee_offboardings (
    id, company_id NOT NULL, employee_id NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    initiated_by_user_id UUID NOT NULL REFERENCES users(id),
    exit_date DATE NOT NULL,
    exit_type    VARCHAR(20) NOT NULL CHECK (exit_type IN ('RESIGNATION','TERMINATION','END_OF_CONTRACT','RETIREMENT')),
    target_status VARCHAR(20) NOT NULL CHECK (target_status IN ('RESIGNED','TERMINATED')),
    reason TEXT,
    reports_policy VARCHAR(30) NOT NULL,
    successor_manager_id UUID NULL REFERENCES employees(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('SCHEDULED','COMPLETED','CANCELLED')),
    completed_at, created_at
)
```

This table earns its place: it holds the *intent* (`exit_type`, `reason`, `successor`, `reports_policy`) for
the window between initiation and effect, which `employees` cannot represent and `audit_log` must not be
queried for as operational state. Audit is a record, not a work queue.

### 8.3 ADR-012 — Two-phase offboarding, completed manually

`exit_date` is frequently in the future — notice periods are the norm, not the exception. So:

- **Phase 1 `initiate()`** — writes `employee_offboardings` (`SCHEDULED`), creates the OFFBOARDING checklist,
  audits `EMPLOYEE_OFFBOARD_INITIATED`. **The employee stays `ACTIVE` and keeps access.** Reversible via
  `cancel()`.
- **Phase 2 `complete()`** — runs the status transition and all cascades C1–C7 atomically, sets
  `COMPLETED`, audits `EMPLOYEE_OFFBOARD_COMPLETED`. **Irreversible.**

**Who triggers phase 2?** There is no scheduler (§1). Options: (a) HR clicks "Complete offboarding", enabled
on/after `exit_date`; (b) a scheduled job.

**Decision: (a) manual, in EP38.** It works with zero new infrastructure, and TR-5 records that we have no
evidenced deploy target — introducing a scheduler now means introducing infrastructure we cannot yet operate,
monitor, or roll back. **(b) is a DevOps follow-on story** (a `flask lifecycle complete-due` CLI command plus
whatever scheduler the eventual platform provides), and the CLI is trivial once `complete()` exists.

**The honest trade-off, stated because UAT will find it:** if HR forgets to click, the employee retains access
past their exit date. Mitigations in EP38: a dashboard "offboardings due" indicator for the `offboarding`
feature holders, and a warning state on overdue rows. **This is a known limitation for the release notes
(Charter §4, Customer-Ready), not a silent gap.** Immediate offboarding (`exit_date = today`) runs both phases
in one transaction, so the urgent case has no exposure at all.

---

## 9. Feature-access design

Per `CLAUDE.md` §"Adding a new feature": add to `portal_features` in **both** `scripts/setup_db.py` and the
migration, seed `role_feature_access` defaults, guard with `@require_feature_access(...)`, and gate nav with
`{% if has_feature_access(...) %}`. **No hardcoded `@require_roles(...)` on any feature route. No per-feature
sub-flags** — the `enabled_for_hr` mistake is documented in `CLAUDE.md` and must not recur in any form.

### 9.1 New feature codes — two, not three

Existing codes occupy `sort_order` 1–10 (`scripts/setup_db.py:104-115`).

| Code | Label | Description | sort_order |
|---|---|---|---|
| `onboarding` | Onboarding | Run and complete new-hire onboarding checklists | **11** |
| `offboarding` | Offboarding | Initiate and complete employee offboarding and exit checklists | **12** |

**Why two and not one.** A single `employee_lifecycle` code cannot express the real access split: a line
manager must be able to complete an onboarding task assigned to them, and must **not** be able to terminate
anyone. With one code, `w` grants both. That is a genuine over-grant, not a hypothetical.

**Why two and not three — configuration rides an existing code.** Checklist *template* administration is
gated by **`@require_feature_access('company_settings', 'w')`**, not a new `lifecycle_config` code. This
follows the project's own established convention: the org-change **runtime** uses `org_change`, while its
**workflow configuration page** is gated by an existing admin code, `org_structure','w'`
(`app/routes/org_change.py:148`). Template administration is tenant configuration and belongs with the
PORTAL_ADMIN who owns tenant configuration. Zero new codes for config.

**Transfer (KAN-185) gets no new code** — it reuses `org_change`. A separate transfer code would fragment a
single access decision across two switches and create exactly the bypass risk §4.3 warns about.

**Audit reads get no new code.** An employee's audit timeline renders on their profile and is gated by the
existing `employee_profiles` (read) plus company scoping. A standalone company-wide audit viewer is a separate
story if the BA wants one — it is not in EP38's acceptance.

### 9.2 Default `role_feature_access` seeds

| Role | `onboarding` r/w/d | `offboarding` r/w/d | Rationale |
|---|---|---|---|
| `SYSTEM_ADMIN` | automatic | automatic | Bypasses feature checks (`app/auth.py:51-53`). Seeded explicitly anyway, per the `03_*` migration pattern. |
| `PORTAL_ADMIN` | ✓ / ✓ / ✓ | ✓ / ✓ / ✗ | Tenant admin. |
| `HR_ADMIN` | ✓ / ✓ / ✗ | ✓ / ✓ / ✗ | HR runs both. |
| `SOLID_LINE_MANAGER` | ✓ / ✓ / ✗ | ✗ / ✗ / ✗ | Completes onboarding tasks for their own new hires. **No offboarding access by default.** |
| all others | ✗ | ✗ | Tenants widen via `company_role_feature_access` if they choose. |

**`can_delete` is `FALSE` for `offboarding` for every role including PORTAL_ADMIN.** There is nothing
legitimate to delete — a completed offboarding is an audited employment record. Making it undeletable at the
permission layer is cheaper and more reliable than relying on the absence of a delete route.

**`SOLID_LINE_MANAGER` gets `onboarding` write, restricted by a business rule.** The guard admits them to the
route; a service check restricts them to tasks assigned to them or to their own reports. This is exactly the
existing org-change pattern — `@require_feature_access('org_change','w')` plus `_user_matches_step()`
(`org_change_service.py:96-100`) — and it is the sanctioned way to express "may act, but only on their own
items." It is **not** a sub-flag: it does not consult a role list and it cannot override a granted permission.

### 9.3 Route guards

| Route | Guard | Additional business rule (in the service) |
|---|---|---|
| `GET /onboarding` | `@require_feature_access('onboarding')` | company scope |
| `GET /onboarding/<employee_id>` | `@require_feature_access('onboarding')` | subject in actor's company |
| `POST /api/onboarding/start` | `@require_feature_access('onboarding','w')` | — |
| `POST /api/onboarding/task/<id>/complete` | `@require_feature_access('onboarding','w')` | assignee, or HR/PORTAL_ADMIN |
| `GET /offboarding` | `@require_feature_access('offboarding')` | company scope |
| `POST /api/offboarding/initiate` | `@require_feature_access('offboarding','w')` | **not self**; not last PORTAL_ADMIN; subject not already terminal |
| `POST /api/offboarding/<id>/complete` | `@require_feature_access('offboarding','w')` | **not self**; status is `SCHEDULED` |
| `POST /api/offboarding/<id>/cancel` | `@require_feature_access('offboarding','w')` | status is `SCHEDULED` |
| `POST /api/lifecycle/suspend` · `/reinstate` | `@require_feature_access('offboarding','w')` | **not self** |
| `POST /api/lifecycle/correct-exit-type` | `@require_feature_access('offboarding','w')` | HR_ADMIN/PORTAL_ADMIN business rule; T6 only |
| `GET/POST /admin/lifecycle-templates` | `@require_feature_access('company_settings','w')` | company scope |
| `GET /transfer` · `POST /api/transfer` | `@require_feature_access('org_change','w')` | **`_can_initiate_for`** — unchanged |
| `GET /api/employee/<id>/audit` | `@require_feature_access('employee_profiles')` | company scope; subject in actor's company |

Nav: `{% if has_feature_access('onboarding') %}` / `('offboarding')`. Never `has_role(...)`.

---

## 10. Technical task breakdown

**Build order — normative. What blocks what:**

```
  KAN-155 (transaction(), ADR-006)      ← EXTERNAL BLOCKER. Not EP38 work. Must be merged first (§5.2).
        │
        ├──► T-AUD-*  audit_log + audit_service        ← blocks all of KAN-184
        │        │
        │        └──► KAN-184  offboarding (the Must)  ← creates the checklist tables
        │                  │
        │                  └──► KAN-183  onboarding    ← rides KAN-184's tables
        │
        └──► KAN-185  transfer   ← independent of the above; can run in parallel from day 1
                                    (needs no new schema, no audit, no transaction work)
```

**KAN-185 is the parallel track.** It has no dependency on KAN-155 or the audit work, so MID can start it on
day 1 while SNR waits on KAN-155. That keeps the team productive through the blocker.

### 10.1 Audit subsystem — prerequisite for KAN-184 — lead: SNR · design: ARCH (ADR-009)

| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-AUD-1 | ARCH | ADR-009 finalised (this §3). Action vocabulary (§3.4) frozen. PII rule for `before_state`/`after_state` added to the review checklist. | — |
| T-AUD-2 | SNR | `database/migrations/08_employee_lifecycle.sql` part 1: `audit_log`, two indexes, immutability trigger + function. Idempotent. Companion `…_down.sql`. | fresh-DB apply; re-apply is a no-op; `UPDATE audit_log` raises |
| T-AUD-3 | SNR | `app/services/audit_service.py` — `record`, `record_many`, `entity_timeline`, `company_timeline`. **Must not commit; must not open a connection.** Company scope from the entity, never the session. | unit: no commit issued; rollback discards the audit row; `company_id` never read from session |
| T-AUD-4 | MID | Company-scoping tests: tenant A can never read tenant B's rows via either timeline function; no `OR company_id IS NULL` anywhere. | tenancy test per `CLAUDE.md` check 3 |
| T-AUD-5 | ARCH | Document `audit_log` + `audit_service` in `../TECHNICAL_DOCUMENTATION.md` (schema + new section) **in the same commit** (Charter §5b rule 1). | doc-currency review gate |

### 10.2 KAN-184 — Offboarding — **Must, P2** — lead: SNR · design: ARCH

| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-184-1 | ARCH | ADR-008 / ADR-010 / ADR-011 / ADR-012 signed off with the BA's acceptance criteria reconciled (OQ-1, OQ-3). | — |
| **T-184-2** | **SNR** | **Session revalidation (§5.3 O3):** `login_required` revalidates `users.is_active` + `employees.employment_status`, cached in `g`. Security boundary — **ARCH review, sequenced first.** | integration: offboarded user's **next** request redirects to login; active user unaffected; **exactly one** extra query per request |
| T-184-3 | SNR | Migration part 2: `employee_offboardings`, `lifecycle_checklist_*`, `employee_checklist_*` (§8.2) + `portal_features` rows 11/12 + `role_feature_access` seeds (§9.2) + the same rows in `scripts/setup_db.py` (F9/KAN-167 — the two must not diverge). | fresh-DB boot drift check green (CI job, KAN-169) |
| T-184-4 | SNR | `app/services/lifecycle_service.py`: `_LEGAL` transition map, `offboard_initiate`, `offboard_complete`, `offboard_cancel`, `suspend`, `reinstate`, `correct_exit_type`. One `transaction()` per entry point. Invariants §2.3 #1–#6. | unit per transition incl. **every** illegal pair raising `IllegalTransition`; **self-transition refused at every privilege level incl. SYSTEM_ADMIN**; last-PORTAL_ADMIN refusal |
| T-184-5 | SNR | Cascades C1–C7 (§2.4) inside the transaction; audit row per effect. | **integration on a real DB (KAN-168 tier): induced mid-cascade failure leaves ZERO rows changed and ZERO audit rows** |
| T-184-6 | SNR | Orphaned reports (§6.4): all four `reports_policy` values; successor validation; vacation `manager_id` re-point. | manager with 3 reports × 4 policies; successor = self refused; root-manager fallback to `UNASSIGN` |
| T-184-7 | SNR | `org_change_service.cancel_system()` (§4.2) + V8 detection and cancellation. **`lifecycle_service` issues no SQL against `org_change_*`.** | V8 repro: offboard the sole approver → request `CANCELLED`, requester notified, **nothing applied**; grep-assert no `org_change_` SQL in `lifecycle_service` |
| T-184-8 | MID | Routes + templates per §9.3; nav via `has_feature_access`; UI states (loading / confirm / error / overdue); notifications **after** commit. | route guard test per row of §9.3; **no `@require_roles` on any of them** |
| T-184-9 | DEVOPS | Structured logging with a correlation id on every lifecycle transition; "offboardings due" metric; **runbook including the §8.1 rollback caveat**. | log assertions; runbook reviewed by ARCH |
| T-184-10 | MID | Extend `tests/ui/test_browser.py` with the offboarding flow (UAT Lead owns the suite, Charter §5b — coordinate). | suite green, count reported per `CLAUDE.md` |
| T-184-11 | ARCH | Update `../TECHNICAL_DOCUMENTATION.md` (schema + lifecycle section) and `../BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` (two new features + access matrix — BA owns, ARCH supplies the access facts). Same commit. | doc-currency gate |

### 10.3 KAN-183 — Onboarding checklist — **Should, P2** — lead: MID · review: SNR

| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-183-1 | MID | Template CRUD on `lifecycle_checklist_templates` (+tasks) with `kind='ONBOARDING'`, gated `('company_settings','w')`. Company-scoped; ordered tasks. | CRUD + company-scope tests |
| T-183-2 | MID | `lifecycle_service.start_checklist(kind='ONBOARDING')` — **snapshot** template → instance (§8.2 point 2). Resolve `MANAGER` assignee to the current solid-line manager at start. | editing the template after start does **not** mutate the live checklist |
| T-183-3 | MID | Task completion route + assignee-or-HR business rule (§9.3); `CHECKLIST_TASK_COMPLETED` audit; checklist auto-completes on last task. | a manager cannot complete another manager's task; HR can |
| T-183-4 | SNR | Hook into `admin_register_user` (`app/routes/admin.py:178-232`) — auto-start the default ONBOARDING checklist. **Wrap the existing five-statement registration in `transaction()` while here** (the pre-existing non-atomic path, §1). | registration failure creates **no** employee, user, or checklist |
| T-183-5 | MID | Screens + nav (`has_feature_access('onboarding')`); due-date badges. | route guard tests |
| T-183-6 | MID | Update `../TECHNICAL_DOCUMENTATION.md` onboarding section + `../../project-management/BACKLOG.md` status marker. | doc-currency gate |

### 10.4 KAN-185 — Transfer via the org-change engine — **Should, P2** — lead: MID · review: ARCH

| Task | Owner | Detail / files | Tests |
|---|---|---|---|
| T-185-1 | MID | `/transfer` screen + `POST /api/transfer` calling **`org_change_service.create_request()` only**. Guard `('org_change','w')` + existing `_can_initiate_for`. **No new engine code, no new table, no new feature code.** | request created with correct from/to snapshot; step-1 approvers notified |
| T-185-2 | MID | Reuse the existing prefill endpoint (`org_change.py:115-146`) for BU/FU/location/manager options. No duplicate query. | option lists company-scoped |
| **T-185-3** | **SNR** | **Anti-bypass suite — the real deliverable (§4.3).** Prove: nothing is applied before final approval; a self-initiated transfer is refused; single rejection ⇒ `REJECTED` and no change; approvals strictly sequential; all queries company-scoped. | the five `CLAUDE.md` org-change invariants asserted against a **real DB** (KAN-168 tier) |
| T-185-4 | ARCH | Review specifically for a second write path into `manager_relationships` / `employee_org_assignments`. Any such path is a **returned PR**. | code review gate |
| T-185-5 | MID | Update `../TECHNICAL_DOCUMENTATION.md` §22 (org-change) to note the transfer entry point. | doc-currency gate |

**Status — KAN-185 🟡 in progress.** **T-185-1 ✅ delivered, but not as specified — and the deviation is
the point of §4.3.** No `/transfer` screen and no `POST /api/transfer` were built: a second route would
have been a second path, which T-185-4 exists to reject. Instead the shared dialog was extracted to
`templates/org_change/_move_modal.html` and given a second opener (`openTransferModal`), wired onto the
**employee profile** and the **directory row `⋯` menu**. `POST /api/org-change/request` remains the only
caller of `create_request()`. The task text should be read as superseded by §4.3; it is left unedited so
the deviation stays visible. **T-185-2 ✅** — the existing prefill endpoint was extended, not duplicated;
it now also returns the subject, their placement by name, the approval chain, the direct-report count and
any PENDING request id, all additive so the drag-and-drop path is unchanged. **T-185-3 ✅**
`tests/test_transfer_entry_point.py` (59) — all five invariants, plus module-inspection gates asserting the
route module contains no SQL writes and does not import `execute`/`insert_returning`. *Caveat:* it runs
DB-mocked, **not** against a real DB — the KAN-168 tier this task asked for is **still outstanding**.
**T-185-5 ✅** §22.1, §22.5a and the API table. **T-185-4 (ARCH review) not yet done.**

**Blocking KAN-185's close: `AC-185-07` effective-dating.** `org_change_requests` has no column to carry
an effective date and `create_request()` no parameter for one, so the field is deliberately not rendered
rather than silently discarding user input. This needs the schema call in **CFL-4** — until then KAN-185
cannot be marked Done, and the UX spec §6.2/§6.4 rows for the date field (E6, E7) are unimplementable.

### 10.5 Effort, and what it is worth

| Item | Estimate (dev-days) | Confidence |
|---|---|---|
| Audit subsystem (T-AUD-1…5) | **3–4** | High — small, well-bounded, one table |
| KAN-184 offboarding (T-184-1…11) | **9–12** | **Medium** — the cascade matrix and V8 carry the uncertainty, not the CRUD |
| KAN-183 onboarding (T-183-1…6) | **4–5** | High — rides KAN-184's tables |
| KAN-185 transfer (T-185-1…5) | **1.5–2** | High — thin by construction (§4.3) |
| **EP38 total** | **17.5–23 dev-days** | Medium-High |
| *KAN-155 (external prerequisite)* | *2–3* | *Not EP38 scope; already in S2* |

With SNR + MID in parallel and KAN-185 absorbing MID's time during the KAN-155 wait, this is **≈2.5–3 calendar
weeks**, plus ARCH review and a regression pass per `CLAUDE.md`. **The audit subsystem is ~20% of EP38's cost
and is reused by EP35 and EP39** — on a whole-roadmap view it is the cheapest thing in this epic.

---

## 11. Register updates

### 11.1 Technical Debt Register — additions to `ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` §5.1

| ID | Debt | Source | Planned in | Sev |
|---|---|---|---|---|
| **TD-7** | `apply_change()` writes 4 statements with no transaction; `decide()` adds a 5th outside it. A partial apply leaves an employee half-moved. **KAN-185 inherits this.** | V4 — `org_change_service.py:282,287,294,298`; `:249` | **KAN-155** (already scoped, T-155-2) | **P1** |
| **TD-8** | `employees.email` / `employee_number` are **globally** unique, not per-company. Blocks rehire; prevents two tenants employing one person; makes employee numbers non-tenant-sequential; **leaks cross-tenant existence via registration errors** (`admin.py:165-170`). | V5 — `schema.sql:986,994` | **New story required** — blocks KAN-186 | **P1** |
| **TD-9** | No employment-period model. Single `join_date`/`exit_date` cannot represent two employments; 16 FKs bind history to one `employees` row. | §7 B2 — `schema.sql:220,350`; `grep -c "REFERENCES public.employees(id)"` → 16 | **New story required** — blocks KAN-186 | **P2** |
| **TD-10** | Sessions are never revalidated against the DB; an offboarded user retains access for up to 8h. | V7 — `app/auth.py:16-22`; `config.py:18` | **T-184-2** | **P1** |
| **TD-11** | Employee registration writes 5 statements non-atomically — a half-created employee is already possible today. | §1 — `admin.py:178-232` | KAN-155 + **T-183-4** | **P2** |
| **TD-12** | `audit_log` uses `TIMESTAMPTZ` while all 46 existing tables use `timestamp without time zone`. Deliberate (§3.1) but inconsistent; the *existing* convention is the latent bug. | ADR-009 | Broader timezone story (not EP38) | **P3** |
| **TD-13** | `audit_log` `DELETE` is not blocked, because there is no DB role separation to distinguish a purge job from the app user. Append-only is 80% enforced. | ADR-009 §3.2a | Follow-on with the purge job | **P2** |
| **TD-14** | No retention purge job and no scheduler in the stack. Audit grows unbounded until one exists. | ADR-009 §3.2c; `requirements.txt` | Follow-on (DEVOPS) | **P3** |
| **TD-15** | No scheduler ⇒ future-dated offboardings require a manual click; an overdue offboarding leaves access open. | ADR-012 §8.3 | Follow-on CLI + scheduler (DEVOPS) | **P2** |

### 11.2 Technical Risk Register — additions to §5.2

| ID | Risk | Prob | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| **TR-6** | **KAN-155 slips ⇒ KAN-184 cannot start.** Non-atomic offboarding would ship a terminated-but-logged-in path and structurally false audit rows. | **Med** | **High** | Hard gate (§5.2). KAN-185 runs in parallel to keep the team productive. Escalate to the SPM the day KAN-155 slips — **do not** start KAN-184 non-atomically. | ARCH |
| **TR-7** | **Orphaned reports detach the org tree.** `org.py:76,85` filter managers on ACTIVE, so reports of a departed manager vanish from the structure and their pending leave becomes unapprovable. | **High** if unhandled | **High** | ADR-011 §6; default `SUCCESSOR_ELSE_ESCALATE` never leaves the tree broken; T-184-6 tests all four policies. | SNR |
| **TR-8** | **V8 — offboarding the sole approver deadlocks a pending org change permanently.** No timeout, escalation or reassignment exists. | **Med** | **Med** | Detect and `cancel_system()` (§6.4 step 5); warn on `approver_employee_id` in workflow steps. **Pre-existing defect** — a stuck request is possible today via any inactivation. | SNR |
| **TR-9** | **Offboarding the last PORTAL_ADMIN locks a tenant out** of its own administration with no in-app remedy. | Low | **High** | Hard refusal in `lifecycle_service` (§2.3 #3), tested. | SNR |
| **TR-10** | **Session revalidation (T-184-2) touches `login_required` — every authenticated route.** A defect here is a total outage or a total auth bypass. | Med | **High** | ARCH-reviewed; sequenced **first** in KAN-184; full regression flow test; `g`-cached to hold the cost at one indexed query/request. | ARCH + SNR |
| **TR-11** | **Audit rows contain PII, colliding with GDPR erasure and an append-only table.** Unresolved (§3.2d). | Med | Med | Diff-only storage minimises exposure; explicit PII rule in review; **DPO ruling required (OQ-4)**. | ARCH → DPO |
| **TR-12** | **Retention periods are a legal determination we cannot make.** Nothing is purged until legal rules. | Med | Low | `retention_class` written now so the future job needs no backfill; over-retention is remediable, premature deletion is not. | SPM → legal |
| **TR-13** | **`audit_log` growth if EP35 writes one row per imported record** (up to 3.6M rows/yr/tenant). | Med | Med | Directive: **batch-level audit rows only** (§3.5); per-record detail stays in `employee_import_rows`. Revisit partitioning past ~50M rows. | ARCH |
| **TR-14** | **A second write path into `manager_relationships` / `employee_org_assignments`** appears in `lifecycle_service`, silently bypassing the approval chain. | Med | **Critical** | ADR-010 boundary is normative; T-185-4 review gate; grep-assert in T-184-7. | ARCH |

### 11.3 ADRs added by this design

| ADR | Decision | Affects |
|---|---|---|
| **ADR-008** | Employee lifecycle state machine — 4 existing statuses, 7 transitions, cascades C1–C7, no new status values in EP38 | KAN-184, KAN-186 |
| **ADR-009** | `audit_log` (append-only, JSONB diffs, BIGSERIAL, TIMESTAMPTZ, company-scoped) + `audit_service` that joins the caller's transaction | KAN-184, EP35, EP39 |
| **ADR-010** | `lifecycle_service` owns status + checklists; `org_change_service` remains the sole approval engine and sole writer of its tables; `cancel_system()` is the only crossing | KAN-184, KAN-185 |
| **ADR-011** | Orphaned reports — `reports_policy` parameter, default `SUCCESSOR_ELSE_ESCALATE`; routing through the approval engine permanently rejected | KAN-184 |
| **ADR-012** | Two-phase offboarding (`initiate` → `complete`) with **manual** phase 2; no scheduler introduced in EP38 | KAN-184 |
| **ADR-013** | One generalised checklist table set with a `kind` discriminator, built by KAN-184 and reused by KAN-183; template snapshotted at instance start | KAN-183, KAN-184 |

---

## 12. Technical-readiness read on EP38

### Is it buildable as scoped?

**Yes — KAN-184, KAN-183 and KAN-185 are buildable at 17.5–23 dev-days, conditional on KAN-155 landing first.
KAN-186 is not, and is correctly parked in Later.** RAG: 🟡 **Amber**, and Amber only because of the
prerequisite and three open questions — not because of unknowns in the design. **Confidence: Medium-High.**

The epic is better-positioned than it looks. The status column, its CHECK constraint, its index and 34 query
sites that already respect it all exist (V1, V6); the approval engine KAN-185 needs already accepts exactly
the right fields (§4.3). **EP38 is mostly wiring up capability the schema already anticipated.** The genuinely
new construction is the audit subsystem — and that is a platform asset EP35 and EP39 are already committed to.

### The riskiest part

**Not the audit table, and not the state machine. It is the offboarding cascade — specifically the
interaction between C5 (orphaned reports), V8 (approver deadlock) and V7 (live sessions).**

Each is individually tractable. Together they mean a "simple status flip" quietly reaches into
`manager_relationships`, `vacation_requests`, `org_change_requests`, `users` **and** the session layer — and
every one of those has to be correct, atomic, and audited in a single transaction. The failure mode is not a
crash; it is a **silently half-offboarded employee** who is gone from the directory but can still log in, still
approves their team's leave, and has no audit trail explaining any of it. That is a Critical access-control
defect wearing a data-integrity costume, and it is exactly what a reviewer skimming a green test suite would
miss.

Second-riskiest: **TR-14** — someone adding a "quick" manager re-point to `lifecycle_service` and bypassing
the approval chain. That is a Critical defect arriving through an entirely reasonable-looking commit.

### What must be decided before code starts

**Blocking:**

| # | Blocker | Owner | Why blocking |
|---|---|---|---|
| **B-1** | **KAN-155 `transaction()` merged.** | SNR (S2) | §5.2. Without it, neither the cascade nor the audit subsystem can be built correctly. **P0 for EP38.** |
| **B-2** | **Reconcile this design against the BA's acceptance criteria, the SPM's backlog rows and UX's screen specs** — all written concurrently and none available to me. | ARCH + BA + SPM + UX | Definition of Ready (Charter §4). I designed against the roadmap; if the AC diverge, the cascade matrix moves. **P0.** |
| **B-3** | **The four `reports_policy` / `pending_leave_policy` defaults** (§6.3, C7). | **BA** | Mechanism is built either way, but the default is a business rule and I will not invent one (Charter §9.2). **P1.** |

**Non-blocking but needed before the relevant task:**

| # | Open question | Owner | Needed by |
|---|---|---|---|
| **OQ-1** | Does KAN-184's "full audit entry" require a **user-visible** audit viewer, or is a queryable trail sufficient? Changes UI scope, not the schema. | BA | T-184-8 |
| **OQ-2** | Should transfers carry a `reason_category`? One nullable column if yes. | BA | T-185-1 |
| **OQ-3** | Do **dotted-line** reports follow the same reassignment rule as solid-line? | BA | T-184-6 |
| **OQ-4** | **GDPR:** how does erasure interact with an append-only audit trail (§3.2d)? And what are the retention periods per `retention_class` (§3.2c)? | **DPO / legal via SPM** | Not blocking EP38 — nothing is purged until answered. **Answer before the Production gate.** |
| **OQ-5** | Should a departing holder of a cross-company-capable role have it revoked rather than retained (C3 exception)? | BA + security | T-184-5 |

### Recommended priorities

| Priority | Item |
|---|---|
| **P0** | B-1 KAN-155 merged · B-2 reconcile with BA/SPM/UX before code |
| **P1** | T-184-2 session revalidation (TD-10) · T-AUD-2/3 audit subsystem · T-184-5/6 atomic cascade + orphaned reports · B-3 policy defaults · TD-8 global unique constraints (own story) |
| **P2** | KAN-183 onboarding · T-184-7 V8 handling · TD-11 atomic registration · TD-13 purge role · TD-15 scheduled completion |
| **P3** | KAN-185 polish · TD-9 employment-period model (prerequisite for KAN-186) · TD-12 timezone convention · TD-14 retention purge |
| **P4** | KAN-186 rehire — **remains blocked on TD-8 and TD-9. Do not schedule until both are closed.** |

### My verdict

**Proceed with EP38 to design sign-off, and hold code start until B-1 and B-2 clear.** The design is complete
enough to build against and I have no unresolved architectural unknowns. What I do **not** yet have is the
product side's acceptance criteria, and I will not certify a Definition of Ready on a design reconciled only
against a roadmap.

**One recommendation to the SPM on sequencing.** EP38 is scoped as one epic, but it contains a platform
capability — the audit subsystem — that EP35 and EP39 both depend on. I recommend it be tracked as its own
story rather than buried inside KAN-184, so that its dependents are visible in the backlog and it is not
quietly descoped if KAN-184 comes under schedule pressure. **This is the single change most likely to
prevent EP35 and EP39 each inventing their own audit trail.** Confidence: **High**.

*Everything above obeys `../../CLAUDE.md`. No task is "done" until `python -m pytest -q` and the regression
flow test pass, and no schema, guard, or invariant change is approvable without the corresponding
documentation updated in the same commit.*
