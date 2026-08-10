# EP42 — Compensation, Job Architecture & Pay Equity — Technical Design — 2026-08-09

> ## ⚠️ AMENDED — read §12 before acting on §1–§11
>
> **This document was written in Wave 2. Wave 3 (the SPM's reconciliation, `EP42_SPM_SCOPE_AND_DECISIONS.md`
> §12) and Wave 4 (Amendment A1 — the product owner's answers, §14) have changed parts of it.**
>
> **§12 of this file is the amendment. It supersedes specific sections of §1–§11 and says exactly which.**
> Nothing has been deleted: superseded material is left in place with a marker, because the reasoning trail —
> *why* we thought the reference value was a group median — is what stops the same reasoning being re-derived
> in six months.
>
> **The three changes that move the most:**
> 1. **"5%" is not a detection threshold — it is the pay increment between consecutive steps** (A1 §3, SPM
>    §14.2). The pay-equity reference value stops being a group median and becomes **the step's configured pay
>    point**. Check A becomes **Check A′**: absolute, per employee, no `n≥3`, no coverage gate. **ADR-023 is
>    re-cut (§12.6); ADR-024 is new (§12.5).**
> 2. **A step is a described job, not a number** (SPM §14.3). Entry at `.0`; `step_count` counts increments
>    **above** entry; per level, per company, **no default**. Two new first-class objects — the **step
>    expectation** and the per-employee **step roadmap** — and a **fourth feature code, `job_architecture`.**
>    **ADR-017 is amended (§12.4).**
> 3. **Wave 3 ratified ADR-016 and sent four items back to me** (SPM §12.1). All four are actioned in §12.2.
>
> **Precedence, so there is no ambiguity:** A1 › SPM §14 › SPM §12 › **this §12** › §1–§11 of this file.
> Where §1–§11 and §12 disagree, **§12 wins**.

> Produced by the **Senior Architect** (`../09_SENIOR_ARCHITECT.md`), Wave 2 of the EP42 cycle. Input:
> the SPM's Wave 1 scope and decisions (`EP42_SPM_SCOPE_AND_DECISIONS.md`) — **authoritative on product**.
> Where the shared team brief and the SPM disagree, the SPM wins; his S1 tenancy correction (CFL-42-6) is
> adopted throughout: **Acme Corp 46 employees, Telia 100, "Sam Cpmapny" 0 (3 locations), plus one
> company-less SYSTEM_ADMIN record — 147 total, 146 in-tenant.**
>
> **What this document is.** The technical design and the **engineer-level task breakdown**. The owner asked
> for *"detailed requirement to the level of software engineer etc so all have the task to complete"* — so §9
> is the heart of this file, not an appendix. A mid-level engineer must be able to pick a task and start
> without asking a question. That is the bar.
>
> **What this document is not.** Not acceptance criteria (BA, Wave 2), not screen design (UX, Wave 2), not a
> re-litigation of the SPM's §4 decisions. Where a decision of his is technically infeasible or collides with
> a `CLAUDE.md` invariant I say so as a **conflict-log entry with a counter-proposal** (§10.3) — never a silent
> redesign.
>
> **Numbering.** ADRs continue from **ADR-013** (the highest in use — ADR-001…007 in
> `ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` §3, ADR-008…013 in `EP38_TECHNICAL_DESIGN.md` §11.3; the audit
> subsystem is ADR-009). EP42 adds **ADR-014 … ADR-023**. Migrations continue from `09` → **`10`…`15`**.
> Feature `sort_order` continues from 13 (`audit_log`); 11 and 12 stay reserved for EP38 onboarding/offboarding,
> so EP42 takes **14, 15, 16**.
>
> **Owner legend:** **ARCH** Senior Architect · **SNR** Senior Software Engineer · **MID** Mid-Level Engineer ·
> **DEVOPS** Senior DevOps Engineer. Every task obeys `../../CLAUDE.md` and the Engineering Charter DoD (§4).
>
> **Evidence convention:** `file:line` as at commit `1b8aac8` on `chore/arch-review-and-hardening`. Counts that
> drift are given with the command that reproduces them.

---

## 0. Executive summary — the recommendation, then the reasoning

**Build EP42 as the SPM scoped it, in his wave order, at 63–79 dev-days. Three technical corrections to his
plan are load-bearing and I am making them here rather than discovering them in build.** RAG **🟡 Amber**.
Confidence **Medium-High**.

**The three corrections, in order of how much damage they prevent:**

1. **KAN-188's stated default rule would black out both populated tenants on the day it merges.** D6
   requirement 2 says an absent `company_features` row defaults to **enabled**, and that this changes nothing
   for any existing feature or tenant. The rows are **not absent.** There are 18 of them, and **14 are
   `is_enabled = FALSE`** — for `employee_profiles`, `org_structure`, `user_accounts`, `skills`, `vacations`,
   `company_settings` and `system_config`, across Acme and Telia. Nothing consults them today, so they are
   inert; the moment the central resolver honours them, every non-SYSTEM_ADMIN user in both tenants loses the
   entire product. The fix is not the default — it is a **repair-then-materialise backfill** plus a
   `portal_features.default_enabled` column so "off by default" is a property of the feature and not a
   hardcoded list. **ADR-016, §5.3.** Evidence: `psql -d employee` (§1 V2).

2. **CFL-4 resolves with a re-interpretation, not a data migration.** Adopt **half-open intervals
   `[effective_from, effective_to)`** for every effective-dated table. Under that reading the existing
   `effective_to = CURRENT_DATE` / `effective_from = CURRENT_DATE` pair that CFL-4 calls a one-day overlap is
   **already correct** — the overlap was a reading error, not a data error. Zero rows are rewritten, and the
   read side costs nothing because `effective_to` is **read in exactly zero places in `app/`** today
   (`grep -rn effective_to app/` → one write site, `org_change_service.py:371`). Closed-closed would require
   decrementing every historical row and cannot represent a same-day correction. **ADR-020, §4.7.**

3. **The compensation proposal must not live on `org_change_requests`.** That table is gated by `org_change`,
   and `_DETAIL_COLS` (`org_change_service.py:415-426`) returns its columns to every approver and every
   inbox row. Putting `proposed_amount` there hands a salary to `org_change:r` holders who do not hold
   `compensation:r` — the exact leak D5 and risk R-3 exist to prevent, delivered by construction. It goes in a
   **one-to-one child table** `org_change_compensation_proposals`, so "absent from the payload" is the default
   state of every existing query rather than something each one has to remember. **ADR-021, §4.8.**

**Fourth thing, smaller but nastier than it looks.** `app/db.py:135` `serialize()` converts `Decimal → float`,
and `to_dict()` applies it to every row of every read. A `numeric(14,2)` salary read through the normal path
becomes an IEEE-754 double before it reaches JSON. `audit_service._clean_diff` calls the same function
(`audit_service.py:181`). **Money never goes through `to_dict()`** — ADR-014 defines a separate serialisation
boundary that emits a decimal **string**.

**What is genuinely new construction:** 14 tables in 5 sets, 3 feature codes, ~26 endpoints, one new
computation engine (pay equity), and two surgical changes to shared engines (`app/auth.py`,
`app/services/org_change_service.py`). Everything else reuses what EP38 built: `audit_service` is the only
audit trail, `notification_service` is the only notification path, `org_change_service` is the only approval
engine, `transaction()` is the only write boundary.

**What is already better than the SPM's plan assumes.** DEP-1 (**KAN-155 `transaction()`**) is **✅ Done**, not
"Planned, S2 enabler" — `app/db.py:57-99`, backlog line 505. EP42 does not wait for it.

**What is worse.** **DEP-4 (KAN-168, the real-DB integration tier) is ⬜ not started** (backlog line 548), and
**KAN-200 cannot be certified without it.** Group formation, medians, coverage gates and the exclusion
constraints are SQL semantics; a mocked test asserts that we called `psycopg2`, not that the arithmetic is
right. That is a hard blocker, named in §11.

**Two stories I will not call technically ready, and one dependency I am downgrading:** KAN-200 (blocked on
KAN-168 and on a DPO ruling that the engine's *input* is lawful) and KAN-202 (blocked on DEP-8). And
**KAN-199 is a soft dependency of KAN-200, not a hard one** — D1 already specifies a median fallback, so
wiring a hard dependency would put a large configuration exercise on the critical path for no correctness
gain. Logged as **CFL-42-11**.

---

## 1. Verification — I re-derived every premise before designing

I do not design against a brief I have not checked. The SPM's §2 table holds in full. Below are the twelve
things I verified myself, of which **V2, V3, V6, V8, V9 and V11 are new** and change the design.

| # | Finding | Evidence | Class |
|---|---|---|---|
| **V1** | **KAN-155 has landed.** `transaction()` exists with nesting refused (`RuntimeError`), `execute()`/`insert_returning()` suppress their commit inside a block, connections are `autocommit=True`. `audit_service.record()` correctly joins the caller's block and opens nothing. | `app/db.py:57-99`, `:110-131`; `app/services/audit_service.py:294-304`; BACKLOG.md:505 | **Known** |
| **V2 — NEW, blocking** | **`company_features` is populated and mostly FALSE.** 18 rows: 9 features × Acme + Telia. **Only `reports` and `skills_intelligence` are TRUE** (2 each). `employee_profiles`, `org_structure`, `user_accounts`, `skills`, `vacations`, `company_settings`, `system_config` are **FALSE for both tenants**. `org_change` and `audit_log` have **no rows at all**; "Sam Cpmapny" has **no rows at all**; `seed_rbac.sql` contains **zero** `company_features` rows, so a fresh CI database has none. | `psql -d employee -c "select c.name, pf.code, cf.is_enabled from company_features cf join portal_features pf on pf.id=cf.feature_id join companies c on c.id=cf.company_id order by 1,2"`; `grep -c company_features database/seed_rbac.sql` → 0 | **Known** |
| **V3 — NEW** | **`serialize()` converts `Decimal` to `float`**, and `to_dict()` applies it to every column of every row on every read path. `audit_service._clean_diff()` calls the same function. A `numeric(14,2)` salary therefore becomes a double the moment it is read through the standard helper. | `app/db.py:134-142`; `app/services/audit_service.py:179-181` | **Known** |
| **V4** | `_SECRETISH_KEYS` is a nine-entry **substring** denylist enforced by `_check_no_secrets()` on both diff sides and on `metadata`. **Nothing in it matches a salary.** `ACTIONS` is a frozen 16-code enumeration; unknown codes raise `AuditError`. | `audit_service.py:97-98, 153-159, 73-90, 224-227` | **Known** |
| **V5** | `org_change_requests` has 20 columns and **no effective date, no request type, no job/level field, no money field**. `create_request(company_id, subject_id, requester_user_id, proposed, reason)` takes no date. `_apply_change` closes the outgoing assignment with `effective_to = CURRENT_DATE` and inserts a row that defaults `effective_from = CURRENT_DATE`. | `database/schema.sql:525-546`; `org_change_service.py:157, 369-378` | **Known** |
| **V6 — NEW** | **`effective_to` is read in zero places in the application.** One write site exists (`org_change_service.py:371`); every read filters on `is_current`. `manager_relationships` and `employee_org_assignments` both carry `effective_from DATE DEFAULT CURRENT_DATE NOT NULL`, `effective_to DATE NULL`, `is_current BOOLEAN DEFAULT TRUE NOT NULL`, with **no constraint tying the three together** and **no uniqueness on `is_current`**. | `grep -rn "effective_to" app/ templates/ scripts/`; `database/schema.sql:355-366, 459-473` | **Known** |
| **V7** | **`decide()` contains no four-eyes check**, and its approver test is bypassed entirely for SYSTEM_ADMIN (`org_change_service.py:248`). **The org-change engine writes nothing to `audit_log`** — `audit_service` is not imported by it. | `org_change_service.py:222-312`; `grep -n audit app/services/org_change_service.py` → nothing | **Known** |
| **V8 — NEW** | **`helpers.direct_report_ids()` is not company-scoped.** It filters `manager_id` + `relationship_type` + `is_current` and nothing else. D5's manager row-scope would inherit that gap. `is_direct_report()` has the same shape. | `app/helpers.py:141-158` | **Known** |
| **V9 — NEW** | **`employee_org_assignments` has no `company_id` column** — it is scoped only transitively through `employees`. Every new EP42 table must carry `company_id` directly rather than copy this. | `database/schema.sql:355-366` | **Known** |
| **V10** | The two ad hoc tenant-switch consumers are exactly as the SPM found them: `_analytics_enabled()` / `_check_analytics_access()` and `_si_enabled()` / `_check_si_company_access()`, each issuing its own `company_features` join. `enabled_for_hr` is still written by both. The "off" screen precedent is `templates/admin/analytics_locked.html` (`analytics.py:184`). | `app/routes/analytics.py:19-45, 100-146, 184`; `app/routes/skills_intelligence.py:15-30, 183-209` | **Known** |
| **V11 — NEW** | **PostgreSQL 16.13; `btree_gist` is available but not installed**; `schema.sql:25` installs only `uuid-ossp`. Exclusion constraints on `daterange` are therefore possible but require a new extension in `schema.sql` and in CI's bootstrap. Existing `numeric` precedent: `numeric(4,2)`, `numeric(4,1)`, `numeric(5,1)` — **no money column exists anywhere**. | `psql -At -c "show server_version"`; `select * from pg_available_extensions where name='btree_gist'`; `grep -n numeric database/schema.sql` | **Known** |
| **V12** | `_step_approver_user_ids()` resolves ROLE steps by **role name within the company**, filtered on `u.is_active` and `e.employment_status='ACTIVE'`. This is the query D4(b)'s create-time "can every step be satisfied by a `compensation:r` holder?" check must reuse — not re-implement. | `org_change_service.py:83-98` | **Known** |

**Two facts that shape sequencing rather than design.** `KAN-166` (migration tool) is **⬜ not started**
(BACKLOG.md:536), so EP42 ships hand-numbered idempotent SQL in the established `08`/`09` style with a
companion `_down.sql` — the convention EP38 already proved. `KAN-163` (any scheduler) is **⬜ not planned**
(BACKLOG.md:523), which is why D2's event-driven + on-demand model is the only one available and why nothing
in this design has a timer.

---

## 2. Architecture overview

### 2.1 Where EP42 sits in the existing shape

The application is Flask with **route modules registered directly on one app object** (blueprints are deferred
— ADR-005/F14), a **service layer** under `app/services/`, raw `psycopg2` through `app/db.py`, and Jinja
templates. EP42 adds nothing new to that shape. It adds three services, one route module, one template
directory, and it *extends* two existing files that are security boundaries.

```
templates/compensation/*.html ─┐
templates/admin/job_architecture.html, compensation_settings.html, feature_disabled.html
                               │
app/routes/compensation.py ────┼──► app/services/compensation_service.py ──┐
  (NEW — all EP42 endpoints)   │        (record, coverage, import, scope)   │
                               ├──► app/services/job_architecture_service.py│──► audit_service.record()
                               │        (families, levels, steps, mapping)  │       (the ONLY audit path)
                               └──► app/services/pay_equity_service.py ─────┘            │
                                        (groups, checks, findings)                       ▼
                                                    │                              app.db.execute
app/routes/org_change.py ──► app/services/org_change_service.py ◄── EXTENDED       (caller's transaction())
  (existing, extended)          (the ONLY approval engine — never re-implemented)
                                        │
                                        └──► notification_service ── the ONLY notification path
app/auth.py ◄── EXTENDED (_load_feature_access gains the tenant switch — ADR-016)
```

### 2.2 What is new, what extends, and the one-way call rule

| Concern | Owner | Never |
|---|---|---|
| Job families, levels, steps, title→level mapping, employee ladder assignment | **`job_architecture_service`** (new) | never inline SQL in a route |
| Compensation records, coverage, CSV backfill, **row scoping** | **`compensation_service`** (new) | never writes `org_change_*`; never writes `audit_log` directly |
| Pay markets, bands, comparison groups, the two checks, finding lifecycle | **`pay_equity_service`** (new) | never reads a compensation row except through `compensation_service` |
| Proposal → **sequential approval** → apply, for placement, level **and** pay | **`org_change_service`** (extended) | no second engine, no second chain, no approval logic anywhere else |
| Audit rows | **`audit_service`** (extended: 11 ACTIONS + `_MONEYISH_KEYS` + a per-action key allowlist) | no second audit trail, ever |
| Notifications and bell retirement | **`notification_service`** (unchanged; one new `related_type`) | no direct `user_notifications` INSERT |
| Feature resolution (role grant **AND** tenant switch) | **`app/auth.py::_load_feature_access`** (extended) | no third hand-rolled `company_features` check |
| Write boundary | **`app.db.transaction()`** | never nested; audit inside; notifications after |

**Permitted call directions.** `compensation_service` and `job_architecture_service` may be called **by**
`org_change_service` at apply time; they may never call *it*. `pay_equity_service` is called after commit and
calls nothing but its own tables plus read-only helpers. Any PR that inverts one of these arrows is returned.

**Why three services and not one `compensation_service`.** Because they have three different read audiences
and three different feature codes. A single module would make it trivially easy for an equity query to read a
raw amount without passing the row scope, and the file would be the largest in the repo within one wave. The
Charter's *"add abstraction when a second real case demands it"* is satisfied: all three cases are in scope
now, and the boundary between them is exactly the boundary between `compensation`, `compensation_self` and
`pay_equity`.

### 2.3 Reuse, stated as prohibitions so they are enforceable at review

1. **`org_change_service.py` is reused and never re-implemented.** Promotion is a `request_type`, not an
   engine (ADR-021). No new approval table, no new chain, no new `decide()`.
2. **`audit_service` is the only audit trail.** No `compensation_audit`, no `pay_equity_log`, no "history"
   table that is really an audit table. The compensation history table is a **source of truth for amounts**,
   not a trail of who-did-what; the trail is `audit_log` and the two join on `correlation_id`.
3. **`notification_service` is the only notification path.** The Pay Equity bell section uses
   `create_user_notification(..., related_type='PAY_EQUITY_FLAG', related_id=<finding id>)` and
   `resolve_related()` — the mechanism migration 09 added for DEF-003.
4. **`transaction()` is the only write boundary.** One per public service entry point. Audit inside.
   Notifications and pay-equity evaluation after commit.
5. **`helpers.direct_report_ids()` is reused for row scoping** — after V8 is fixed to take a `company_id`.

---

## 3. Data model

### 3.1 Rules every new table obeys

1. **`company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE` on every table**, including child
   tables whose parent already has one. V9 shows what the alternative costs: `employee_org_assignments` can
   only be company-scoped through a join, so every query has to remember. Denormalising 16 bytes removes a
   whole class of tenancy bug.
2. **Tenancy integrity is enforced by composite foreign keys, not by hope.** Where a child references a parent
   that also has `company_id`, the parent gets `UNIQUE (id, company_id)` and the child references
   `(parent_id, company_id)`. That makes a cross-tenant row **impossible at the database level**, not merely
   absent from the code that currently exists. This is new for this codebase and is deliberate.
3. **`uuid DEFAULT uuid_generate_v4()` primary keys** — matching every existing table. `audit_log`'s
   `BIGSERIAL` was a deliberate one-off for an append-only high-insert trail (ADR-009 §3.1); none of these
   tables has that profile.
4. **`TIMESTAMPTZ` for new `created_at`/`updated_at`**, following ADR-009's precedent and TD-12. Dates that
   are business facts (`effective_from`) stay `DATE` — pay is effective on a day, not at an instant, and a
   timezone on an effective date creates a bug in every jurisdiction but one.
5. **Money is `numeric`. Never `float`, never `real`, never `double precision`, never integer minor units.**
   ADR-014.
6. **Half-open intervals `[effective_from, effective_to)`** on every effective-dated table. ADR-020.

### 3.2 Set 1 — job architecture (migration `11`)

> **⚠️ AMENDED by §12.4.** `job_levels` gains `step_count` (no default, increments **above** entry),
> `step_increment_pct` and `step_tolerance_pct` with the declarative `tolerance*2 < increment` CHECK;
> `job_level_step_targets` is **withdrawn** and replaced by `job_step_expectations`; two new tables
> (`job_step_expectations`, `employee_step_roadmaps`) and `employee_job_assignments` gains `step_no`
> semantics from `.0`, `review_context`, and the fitted-step columns. See §12.4.


```sql
CREATE TABLE IF NOT EXISTS job_families (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id   UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code         VARCHAR(50)  NOT NULL,
    name         VARCHAR(150) NOT NULL,
    description  TEXT,
    sort_order   INT          NOT NULL DEFAULT 0,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (company_id, code),
    UNIQUE (company_id, name),
    UNIQUE (id, company_id)            -- target of the composite FK below
);
CREATE INDEX IF NOT EXISTS idx_job_families_company ON job_families (company_id, is_active, sort_order);

CREATE TABLE IF NOT EXISTS job_levels (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id     UUID         NOT NULL,
    job_family_id  UUID         NOT NULL,
    ordinal        INT          NOT NULL,
    title          VARCHAR(150) NOT NULL,          -- THE canonical job title (D3)
    short_code     VARCHAR(20),                    -- "L1", "P3" — display only
    steps_count    INT          NOT NULL DEFAULT 5,
    description    TEXT,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_job_levels_ordinal     CHECK (ordinal BETWEEN 1 AND 30),
    CONSTRAINT chk_job_levels_steps_count CHECK (steps_count BETWEEN 1 AND 12),
    CONSTRAINT fk_job_levels_family
        FOREIGN KEY (job_family_id, company_id)
        REFERENCES job_families (id, company_id) ON DELETE RESTRICT,
    UNIQUE (job_family_id, ordinal),
    UNIQUE (job_family_id, title),
    UNIQUE (id, company_id)
);
CREATE INDEX IF NOT EXISTS idx_job_levels_family ON job_levels (company_id, job_family_id, ordinal);

-- SPARSE. A step exists as a concept because `steps_count` says so; a ROW exists
-- only where the company configured a target point. Requiring 5 rows per level to
-- express "this level has 5 steps" would be 5x the configuration for zero
-- information, and it would make `steps_count` and the row count two sources of
-- truth for the same fact.
CREATE TABLE IF NOT EXISTS job_level_step_targets (
    job_level_id     UUID          NOT NULL REFERENCES job_levels(id) ON DELETE CASCADE,
    company_id       UUID          NOT NULL,
    step_no          INT           NOT NULL,
    target_percentile NUMERIC(5,2) NOT NULL,       -- position within the band; guidance only
    updated_by_user_id UUID        REFERENCES users(id) ON DELETE SET NULL,
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    PRIMARY KEY (job_level_id, step_no),
    CONSTRAINT chk_step_target_pct CHECK (target_percentile >= 0 AND target_percentile <= 100),
    CONSTRAINT chk_step_target_no  CHECK (step_no BETWEEN 1 AND 12)
);

-- The persisted output of the KAN-191 mapping screen, so it survives the sitting,
-- round-trips through CSV, and can be re-applied to employees hired later.
CREATE TABLE IF NOT EXISTS job_title_level_map (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id    UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_title     VARCHAR(150) NOT NULL,            -- the free-text value as it appears in employees
    job_level_id  UUID         NOT NULL,
    default_step_no INT        NOT NULL DEFAULT 1,
    mapped_by_user_id UUID     REFERENCES users(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_title_map_level
        FOREIGN KEY (job_level_id, company_id) REFERENCES job_levels (id, company_id) ON DELETE CASCADE,
    UNIQUE (company_id, job_title)
);

CREATE TABLE IF NOT EXISTS employee_job_assignments (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id         UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id        UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    job_level_id       UUID        NOT NULL,
    step_no            INT         NOT NULL,
    effective_from     DATE        NOT NULL,
    effective_to       DATE        NULL,            -- EXCLUSIVE (ADR-020)
    is_current         BOOLEAN     NOT NULL DEFAULT TRUE,
    promotion_eligible BOOLEAN     NOT NULL DEFAULT FALSE,
    source             VARCHAR(16) NOT NULL,
    org_change_request_id UUID     NULL REFERENCES org_change_requests(id) ON DELETE SET NULL,
    assigned_by_user_id   UUID     NULL REFERENCES users(id) ON DELETE SET NULL,
    reason             TEXT        NOT NULL,
    correlation_id     UUID        NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_eja_step   CHECK (step_no BETWEEN 1 AND 12),
    CONSTRAINT chk_eja_source CHECK (source IN ('MANUAL','IMPORT','MAPPING','ORG_CHANGE')),
    CONSTRAINT chk_eja_interval CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT chk_eja_current  CHECK ((is_current AND effective_to IS NULL)
                                    OR (NOT is_current AND effective_to IS NOT NULL)),
    CONSTRAINT fk_eja_level
        FOREIGN KEY (job_level_id, company_id) REFERENCES job_levels (id, company_id) ON DELETE RESTRICT
);

-- Exactly one current ladder position per employee. Cheap, no extension needed.
CREATE UNIQUE INDEX IF NOT EXISTS uq_eja_one_current
    ON employee_job_assignments (employee_id) WHERE is_current;

-- No two periods may overlap, current or historical. Requires btree_gist (V11).
ALTER TABLE employee_job_assignments
    ADD CONSTRAINT excl_eja_no_overlap
    EXCLUDE USING gist (
        employee_id WITH =,
        daterange(effective_from, effective_to, '[)') WITH &&
    );

CREATE INDEX IF NOT EXISTS idx_eja_current
    ON employee_job_assignments (company_id, job_level_id, step_no) WHERE is_current;
CREATE INDEX IF NOT EXISTS idx_eja_employee_time
    ON employee_job_assignments (employee_id, effective_from DESC);
```

**`step_no ≤ job_levels.steps_count` cannot be a CHECK** — it spans two tables. I am **not** adding a trigger
for it: the CHECK bounds it at the global maximum of 12, `job_architecture_service.assign()` validates it
against the level, and `tests/test_job_architecture.py` asserts the refusal. A trigger here buys a guarantee
against direct SQL that nothing else in this schema has, at the cost of a per-insert plpgsql call on the
hottest write in W1. Recorded as **TD-21** so the omission is visible rather than accidental.

**`employees.job_title` is untouched** — not dropped, not renamed, not repurposed (S12/CFL-42-4). The index
`idx_employees_job_title` and the `trg_employee_search` trigger keep working exactly as they do. See §4.6 for
the precedence rule.

### 3.3 Set 2 — compensation (migration `12`)

> **⚠️ AMENDED by §12.3.** The stored `is_current` boolean is **withdrawn** on every EP42 effective-dated
> table (SPM CFL-42-16 — "current is computed, never stored"); the GiST exclusion constraint already
> guarantees what the partial unique index was buying. Annualisation constants move from
> `company_compensation_settings` to `pay_markets` (SPM OQ-BA-3). See §12.3.


```sql
CREATE TABLE IF NOT EXISTS employee_compensation (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id         UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id        UUID          NOT NULL REFERENCES employees(id) ON DELETE CASCADE,

    -- ── the money ────────────────────────────────────────────────────────────
    amount             NUMERIC(14,2) NOT NULL,     -- as recorded, in `currency`, at `pay_basis`
    currency           CHAR(3)       NOT NULL,
    pay_basis          VARCHAR(8)    NOT NULL,
    fte                NUMERIC(4,3)  NOT NULL DEFAULT 1.000,
    -- Derived at WRITE time and STORED. See ADR-014 §4.1(d) — the comparison
    -- value must not silently re-value itself when a company edits its standard
    -- annual hours three years later.
    annual_base_fte    NUMERIC(14,2) NOT NULL,

    -- ── effective dating (ADR-020, half-open) ────────────────────────────────
    effective_from     DATE          NOT NULL,
    effective_to       DATE          NULL,
    is_current         BOOLEAN       NOT NULL DEFAULT TRUE,

    -- ── provenance ───────────────────────────────────────────────────────────
    employment_type    VARCHAR(50)   NOT NULL,     -- snapshot: exclusion must be stable over time
    source             VARCHAR(16)   NOT NULL,
    org_change_request_id UUID       NULL REFERENCES org_change_requests(id) ON DELETE SET NULL,
    import_batch_id    UUID          NULL,
    recorded_by_user_id UUID         NULL REFERENCES users(id) ON DELETE SET NULL,
    recorded_by_label  VARCHAR(255)  NOT NULL,     -- ADR-009 §3.1 reasoning: survive user deletion
    reason             TEXT          NOT NULL,
    correlation_id     UUID          NOT NULL,

    -- ── void (the ONLY mutation this table permits) ──────────────────────────
    status             VARCHAR(8)    NOT NULL DEFAULT 'ACTIVE',
    voided_by_user_id  UUID          NULL REFERENCES users(id) ON DELETE SET NULL,
    voided_at          TIMESTAMPTZ   NULL,
    void_reason        TEXT          NULL,

    created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_ec_amount    CHECK (amount > 0),
    CONSTRAINT chk_ec_annual    CHECK (annual_base_fte > 0),
    CONSTRAINT chk_ec_currency  CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT chk_ec_basis     CHECK (pay_basis IN ('ANNUAL','MONTHLY','HOURLY')),
    CONSTRAINT chk_ec_fte       CHECK (fte > 0 AND fte <= 1.000),
    CONSTRAINT chk_ec_source    CHECK (source IN ('MANUAL','IMPORT','ORG_CHANGE')),
    CONSTRAINT chk_ec_status    CHECK (status IN ('ACTIVE','VOIDED')),
    CONSTRAINT chk_ec_interval  CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT chk_ec_current   CHECK ((is_current AND effective_to IS NULL)
                                    OR (NOT is_current AND effective_to IS NOT NULL)),
    CONSTRAINT chk_ec_void      CHECK ((status = 'ACTIVE'  AND voided_at IS NULL AND void_reason IS NULL)
                                    OR (status = 'VOIDED' AND voided_at IS NOT NULL AND void_reason IS NOT NULL)),
    CONSTRAINT chk_ec_void_not_current CHECK (status = 'ACTIVE' OR NOT is_current)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ec_one_current
    ON employee_compensation (employee_id) WHERE is_current;

ALTER TABLE employee_compensation
    ADD CONSTRAINT excl_ec_no_overlap
    EXCLUDE USING gist (
        employee_id WITH =,
        daterange(effective_from, effective_to, '[)') WITH &&
    ) WHERE (status = 'ACTIVE');

-- The equity engine's only hot query: current, active, in-company, by ladder position.
CREATE INDEX IF NOT EXISTS idx_ec_equity
    ON employee_compensation (company_id, employee_id)
    INCLUDE (annual_base_fte, currency, employment_type)
    WHERE is_current AND status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_ec_employee_time
    ON employee_compensation (employee_id, effective_from DESC);
CREATE INDEX IF NOT EXISTS idx_ec_correlation ON employee_compensation (correlation_id);
```

**Partial immutability, trigger-enforced.** The table is append-only *for value*, but closing an interval and
voiding a row are both `UPDATE`s. A blanket UPDATE block (the `audit_log` pattern) is therefore wrong here.
Instead:

```sql
CREATE OR REPLACE FUNCTION employee_compensation_immutable() RETURNS trigger AS $$
BEGIN
    IF NEW.employee_id     IS DISTINCT FROM OLD.employee_id
    OR NEW.company_id      IS DISTINCT FROM OLD.company_id
    OR NEW.amount          IS DISTINCT FROM OLD.amount
    OR NEW.currency        IS DISTINCT FROM OLD.currency
    OR NEW.pay_basis       IS DISTINCT FROM OLD.pay_basis
    OR NEW.fte             IS DISTINCT FROM OLD.fte
    OR NEW.annual_base_fte IS DISTINCT FROM OLD.annual_base_fte
    OR NEW.effective_from  IS DISTINCT FROM OLD.effective_from
    OR NEW.correlation_id  IS DISTINCT FROM OLD.correlation_id
    OR NEW.created_at      IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION 'employee_compensation is append-only for value; '
                        'correct a figure with a NEW row, never by editing one '
                        '(EP42 ADR-015). Only effective_to / is_current / the '
                        'void columns may change.';
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_employee_compensation_immutable
    BEFORE UPDATE ON employee_compensation
    FOR EACH ROW EXECUTE FUNCTION employee_compensation_immutable();
```

**No `DELETE` guard** — same reasoning as ADR-009 §3.2(a), and the same TD-13 caveat: there is no DB role
separation, so a delete block would have to be circumventable to allow erasure/retention work, which is worse
than an honest documented gap.

```sql
-- One row per company. Created lazily on the company's first compensation write,
-- or by the company-create path. Holds every number D1 says is configurable.
CREATE TABLE IF NOT EXISTS company_compensation_settings (
    company_id                 UUID PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
    default_currency           CHAR(3)       NOT NULL,
    standard_annual_hours      NUMERIC(7,2)  NOT NULL DEFAULT 1976.00,
    backdate_limit_days        INT           NOT NULL DEFAULT 90,
    forward_date_limit_days    INT           NOT NULL DEFAULT 180,
    self_view_history          BOOLEAN       NOT NULL DEFAULT FALSE,
    -- D1 thresholds, all per company, all defaults-shown-as-defaults
    coverage_gate_pct          NUMERIC(5,2)  NOT NULL DEFAULT 80.00,
    outlier_low_ratio          NUMERIC(4,3)  NOT NULL DEFAULT 0.950,
    outlier_high_ratio         NUMERIC(4,3)  NOT NULL DEFAULT 1.100,
    gender_gap_threshold_pct   NUMERIC(5,2)  NOT NULL DEFAULT 5.00,
    min_group_size_outlier     INT           NOT NULL DEFAULT 3,
    min_group_size_gap         INT           NOT NULL DEFAULT 5,
    justification_months       INT           NOT NULL DEFAULT 12,
    refire_delta_pp            NUMERIC(4,2)  NOT NULL DEFAULT 2.00,
    equity_first_gate_passed_at TIMESTAMPTZ  NULL,     -- D7.4: equity stays off until coverage crosses once
    gender_gap_check_enabled   BOOLEAN       NOT NULL DEFAULT TRUE,   -- OQ-3 kill switch, no code change
    updated_by_user_id         UUID          NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_at                 TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_ccs_coverage CHECK (coverage_gate_pct BETWEEN 50 AND 100),
    CONSTRAINT chk_ccs_low      CHECK (outlier_low_ratio  BETWEEN 0.500 AND 1.000),
    CONSTRAINT chk_ccs_high     CHECK (outlier_high_ratio BETWEEN 1.000 AND 2.000),
    CONSTRAINT chk_ccs_gap      CHECK (gender_gap_threshold_pct BETWEEN 1 AND 50),
    CONSTRAINT chk_ccs_min_o    CHECK (min_group_size_outlier BETWEEN 2 AND 50),
    CONSTRAINT chk_ccs_min_g    CHECK (min_group_size_gap     BETWEEN 2 AND 50),
    CONSTRAINT chk_ccs_months   CHECK (justification_months BETWEEN 1 AND 60),
    CONSTRAINT chk_ccs_hours    CHECK (standard_annual_hours BETWEEN 500 AND 3000),
    CONSTRAINT chk_ccs_currency CHECK (default_currency ~ '^[A-Z]{3}$')
);

-- D2: the optional named escalation list. ADDS recipients. It has no deny path,
-- by construction — there is no `is_excluded` column and there never will be.
CREATE TABLE IF NOT EXISTS pay_equity_recipients (
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    added_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (company_id, employee_id)
);
```

### 3.4 Set 3 — the org-change compensation proposal (migration `13`)

```sql
ALTER TABLE org_change_requests
    ADD COLUMN IF NOT EXISTS effective_date        DATE        NULL,
    ADD COLUMN IF NOT EXISTS request_type          VARCHAR(20) NOT NULL DEFAULT 'TRANSFER',
    ADD COLUMN IF NOT EXISTS from_job_level_id     UUID        NULL,
    ADD COLUMN IF NOT EXISTS from_step_no          INT         NULL,
    ADD COLUMN IF NOT EXISTS proposed_job_level_id UUID        NULL,
    ADD COLUMN IF NOT EXISTS proposed_step_no      INT         NULL;

ALTER TABLE org_change_requests
    ADD CONSTRAINT chk_ocr_request_type
        CHECK (request_type IN ('TRANSFER','PROMOTION','COMPENSATION_REVIEW'));

CREATE INDEX IF NOT EXISTS idx_ocr_type ON org_change_requests (company_id, request_type, status);
```

`effective_date` is **nullable** so the migration cannot fail on 100+ existing rows, and so a request raised
before KAN-189 keeps meaning "apply on the day it is approved". `create_request()` defaults it to
`CURRENT_DATE` from KAN-189 onward. `request_type` defaults `'TRANSFER'`, which is exactly what every existing
row is.

```sql
-- ADR-021. Deliberately NOT columns on org_change_requests: that table is gated by
-- `org_change`, and _DETAIL_COLS returns its columns to every approver and every
-- inbox row (org_change_service.py:415-426). A one-to-one child table makes
-- "absent from the payload" the DEFAULT state of every existing query.
CREATE TABLE IF NOT EXISTS org_change_compensation_proposals (
    request_id      UUID PRIMARY KEY REFERENCES org_change_requests(id) ON DELETE CASCADE,
    company_id      UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    pay_decision    VARCHAR(12)   NOT NULL,
    proposed_amount    NUMERIC(14,2) NULL,
    proposed_currency  CHAR(3)       NULL,
    proposed_pay_basis VARCHAR(8)    NULL,
    proposed_fte       NUMERIC(4,3)  NULL,
    decision_reason TEXT          NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_ocp_decision CHECK (pay_decision IN ('NO_CHANGE','NEW_SALARY','DEFER')),
    CONSTRAINT chk_ocp_currency CHECK (proposed_currency IS NULL OR proposed_currency ~ '^[A-Z]{3}$'),
    CONSTRAINT chk_ocp_basis    CHECK (proposed_pay_basis IS NULL
                                    OR proposed_pay_basis IN ('ANNUAL','MONTHLY','HOURLY')),
    -- THE D-185-1 KILL. A partial money proposal is not "overlay what changed" —
    -- it is a half-specified salary, and there is no safe way to complete it.
    -- Make it unrepresentable instead of relying on an overlay rule at apply time.
    CONSTRAINT chk_ocp_complete CHECK (
        (pay_decision = 'NEW_SALARY'
             AND proposed_amount   IS NOT NULL AND proposed_amount > 0
             AND proposed_currency IS NOT NULL
             AND proposed_pay_basis IS NOT NULL
             AND proposed_fte      IS NOT NULL AND proposed_fte > 0)
     OR (pay_decision IN ('NO_CHANGE','DEFER')
             AND proposed_amount IS NULL AND proposed_currency IS NULL
             AND proposed_pay_basis IS NULL AND proposed_fte IS NULL)),
    CONSTRAINT chk_ocp_defer_reason CHECK (pay_decision <> 'DEFER'
                                        OR (decision_reason IS NOT NULL AND btrim(decision_reason) <> ''))
);
```

### 3.5 Set 4 — pay markets and bands (migration `14`)

> **⚠️ AMENDED by §12.3 and §12.5.** This set **splits with the story** (SPM Ruling 32): pay markets are a
> **hard** prerequisite and move to W2 as KAN-199; `salary_bands` becomes KAN-205 in W4 and is the level's
> **min/max envelope**, no longer the comparison basis. `pay_markets` gains the annualisation constants.
> The new `job_level_pay_points` table (§12.5) is the comparison basis.


```sql
CREATE TABLE IF NOT EXISTS pay_markets (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    code       VARCHAR(50)  NOT NULL,
    name       VARCHAR(150) NOT NULL,
    currency   CHAR(3)      NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_pm_currency CHECK (currency ~ '^[A-Z]{3}$'),
    UNIQUE (company_id, code),
    UNIQUE (id, company_id)
);

-- PK on location_id: a location belongs to EXACTLY ONE pay market. Two markets
-- claiming one office would make the comparison group non-deterministic, and a
-- non-deterministic comparison group is a finding you cannot defend.
CREATE TABLE IF NOT EXISTS pay_market_locations (
    location_id   UUID PRIMARY KEY REFERENCES locations(id) ON DELETE CASCADE,
    pay_market_id UUID NOT NULL,
    company_id    UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT fk_pml_market FOREIGN KEY (pay_market_id, company_id)
        REFERENCES pay_markets (id, company_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_pml_market ON pay_market_locations (pay_market_id);

CREATE TABLE IF NOT EXISTS salary_bands (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id    UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_level_id  UUID          NOT NULL,
    pay_market_id UUID          NOT NULL,
    min_amount    NUMERIC(14,2) NOT NULL,
    mid_amount    NUMERIC(14,2) NOT NULL,
    max_amount    NUMERIC(14,2) NOT NULL,
    currency      CHAR(3)       NOT NULL,
    effective_from DATE         NOT NULL,
    effective_to   DATE         NULL,
    is_current    BOOLEAN       NOT NULL DEFAULT TRUE,
    created_by_user_id UUID     NULL REFERENCES users(id) ON DELETE SET NULL,
    reason        TEXT          NOT NULL,
    correlation_id UUID         NOT NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_sb_order    CHECK (min_amount <= mid_amount AND mid_amount <= max_amount),
    CONSTRAINT chk_sb_positive CHECK (min_amount > 0),
    CONSTRAINT chk_sb_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT chk_sb_interval CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT chk_sb_current  CHECK ((is_current AND effective_to IS NULL)
                                   OR (NOT is_current AND effective_to IS NOT NULL)),
    CONSTRAINT fk_sb_level  FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE,
    CONSTRAINT fk_sb_market FOREIGN KEY (pay_market_id, company_id)
        REFERENCES pay_markets (id, company_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_sb_one_current
    ON salary_bands (job_level_id, pay_market_id) WHERE is_current;
ALTER TABLE salary_bands
    ADD CONSTRAINT excl_sb_no_overlap
    EXCLUDE USING gist (
        job_level_id WITH =, pay_market_id WITH =,
        daterange(effective_from, effective_to, '[)') WITH &&
    );
```

**No `fx_rates` table in this cycle.** D1 says a merged multi-currency market is *refused* unless an
effective-dated rate exists for every currency in it. OQ-6's default is "no tenant needs it", and it is true
for all three seeded tenants. Building a table whose only job is to make a refusal conditional, when the
refusal is currently unconditional, is speculative generality. **The configuration is refused outright** with
a message naming the currencies in conflict; the `fx_rates` shape is recorded in §10.1 as the Later design so
adding it is additive, not a rewrite. **Confidence High.**

### 3.6 Set 5 — pay-equity findings (migration `15`)

> **⚠️ SUPERSEDED IN PART by §12.6.** `pay_equity_findings` keeps its lifecycle columns and gains
> `finding_type` (`PAY_BELOW_STEP` · `PAY_ABOVE_STEP` · `GENDER_GAP`), `step_no` in the key, `reference_value`
> and `deviation_pct`; the group/coverage columns become **Check B only** and nullable. See §12.6.


```sql
CREATE TABLE IF NOT EXISTS pay_equity_findings (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id    UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    check_type    VARCHAR(24)  NOT NULL,
    -- Group identity. Subject is NULL for the group-level gender-gap check.
    subject_employee_id UUID   NULL REFERENCES employees(id) ON DELETE CASCADE,
    job_family_id UUID         NOT NULL,
    job_level_id  UUID         NOT NULL,
    pay_market_id UUID         NOT NULL,
    -- Explanatory context, carried so a finding is readable a year later without
    -- re-running the engine against data that has since moved.
    subject_step_no INT        NULL,
    group_size    INT          NOT NULL,
    compared_count INT         NOT NULL,
    excluded_count INT         NOT NULL DEFAULT 0,
    coverage_pct  NUMERIC(5,2) NOT NULL,
    basis         VARCHAR(16)  NOT NULL,
    -- A RATIO or a PERCENTAGE. Never an amount. See §8.4 — this is still
    -- invertible when a band exists, which is why the queue gates it (ADR-018).
    measured_value  NUMERIC(9,4) NOT NULL,
    threshold_value NUMERIC(9,4) NOT NULL,

    state         VARCHAR(24)  NOT NULL DEFAULT 'OPEN',
    justification_category VARCHAR(40) NULL,
    disposition_reason TEXT    NULL,
    dispositioned_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    dispositioned_at TIMESTAMPTZ NULL,
    valid_until   DATE         NULL,                -- justification window (D2)
    remediation_owner_employee_id UUID NULL REFERENCES employees(id) ON DELETE SET NULL,
    remediation_target_date DATE NULL,

    first_raised_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id   UUID        NOT NULL,

    CONSTRAINT chk_pef_check  CHECK (check_type IN ('INDIVIDUAL_OUTLIER','GROUP_GENDER_GAP')),
    CONSTRAINT chk_pef_basis  CHECK (basis IN ('BAND_MIDPOINT','GROUP_MEDIAN')),
    CONSTRAINT chk_pef_state  CHECK (state IN ('OPEN','JUSTIFIED','REMEDIATION_PLANNED',
                                               'RESOLVED','RESOLVED_BY_DATA')),
    CONSTRAINT chk_pef_subject CHECK ((check_type = 'INDIVIDUAL_OUTLIER' AND subject_employee_id IS NOT NULL)
                                   OR (check_type = 'GROUP_GENDER_GAP'   AND subject_employee_id IS NULL)),
    -- Every disposition carries a reason. No one-click dismiss anywhere (D2).
    CONSTRAINT chk_pef_reason CHECK (state IN ('OPEN','RESOLVED_BY_DATA')
                                  OR (disposition_reason IS NOT NULL
                                      AND btrim(disposition_reason) <> ''
                                      AND dispositioned_at IS NOT NULL)),
    CONSTRAINT chk_pef_justified CHECK (state <> 'JUSTIFIED'
                                     OR (justification_category IS NOT NULL AND valid_until IS NOT NULL)),
    CONSTRAINT chk_pef_remediation CHECK (state <> 'REMEDIATION_PLANNED'
                                       OR (remediation_owner_employee_id IS NOT NULL
                                           AND remediation_target_date IS NOT NULL)),
    CONSTRAINT fk_pef_level  FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE,
    CONSTRAINT fk_pef_market FOREIGN KEY (pay_market_id, company_id)
        REFERENCES pay_markets (id, company_id) ON DELETE CASCADE
);

-- At most ONE open finding per (subject-or-group, group key, check). This is what
-- makes re-evaluation idempotent: a re-run either updates last_evaluated_at or
-- collides on this index and does nothing. "One person, one finding" (D1) is a
-- database guarantee, not a code convention.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pef_one_open ON pay_equity_findings (
    company_id, check_type,
    COALESCE(subject_employee_id, '00000000-0000-0000-0000-000000000000'::uuid),
    job_level_id, pay_market_id
) WHERE state = 'OPEN';

CREATE INDEX IF NOT EXISTS idx_pef_queue
    ON pay_equity_findings (company_id, state, first_raised_at DESC);
CREATE INDEX IF NOT EXISTS idx_pef_refire
    ON pay_equity_findings (company_id, check_type, subject_employee_id, valid_until)
    WHERE state = 'JUSTIFIED';

-- The run log. Serves the coverage view, the "why did nothing fire?" question,
-- and the cost telemetry in §7.4.
CREATE TABLE IF NOT EXISTS pay_equity_evaluations (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id    UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    scope         VARCHAR(12) NOT NULL,
    trigger_kind  VARCHAR(24) NOT NULL,
    triggered_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    job_level_id  UUID        NULL,
    pay_market_id UUID        NULL,
    groups_evaluated       INT NOT NULL DEFAULT 0,
    groups_skipped_size    INT NOT NULL DEFAULT 0,
    groups_skipped_coverage INT NOT NULL DEFAULT 0,
    findings_raised        INT NOT NULL DEFAULT 0,
    findings_auto_resolved INT NOT NULL DEFAULT 0,
    outcome       VARCHAR(8)  NOT NULL DEFAULT 'SUCCESS',
    error_code    VARCHAR(60) NULL,
    duration_ms   INT         NULL,
    correlation_id UUID       NOT NULL,
    run_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_pee_scope   CHECK (scope IN ('GROUP','COMPANY')),
    CONSTRAINT chk_pee_outcome CHECK (outcome IN ('SUCCESS','FAILED')),
    CONSTRAINT chk_pee_trigger CHECK (trigger_kind IN (
        'COMPENSATION_WRITTEN','LEVEL_CHANGED','MEMBERSHIP_CHANGED',
        'CONFIG_CHANGED','BAND_CHANGED','ON_DEMAND'))
);
CREATE INDEX IF NOT EXISTS idx_pee_company_time ON pay_equity_evaluations (company_id, run_at DESC);
```

### 3.7 Summary — 14 new tables, 2 altered

| Set | Migration | Tables | Story |
|---|---|---|---|
| 0 — platform | `10` | *(none — `portal_features.default_enabled` column + `company_features` backfill)* | KAN-188 |
| 0 — dating | `10` | *(none — `org_change_requests.effective_date`)* | KAN-189 |
| 1 — job architecture | `11` | `job_families` · `job_levels` · `job_level_step_targets` · `job_title_level_map` · `employee_job_assignments` | KAN-190/191/192 |
| 2 — compensation | `12` | `employee_compensation` · `company_compensation_settings` · `pay_equity_recipients` | KAN-193/194 |
| 3 — coupling | `13` | `org_change_compensation_proposals` *(+ 5 columns on `org_change_requests`)* | KAN-196/197 |
| 4 — bands | `14` | `pay_markets` · `pay_market_locations` · `salary_bands` | KAN-199 |
| 5 — equity | `15` | `pay_equity_findings` · `pay_equity_evaluations` | KAN-200/201 |

---

## 4. Architecture Decision Records — ADR-014 … ADR-023

### 4.1 ADR-014 — Money representation and currency

**Decision: Build. `NUMERIC(14,2)` for amounts, `CHAR(3)` ISO-4217 for currency, one currency per record, and
a serialisation boundary that emits money as a decimal *string*. Never `float`, never `double precision`,
never integer minor units.** Confidence **High**.

**(a) Why `numeric`, argued rather than asserted.** `float8` cannot represent `0.1`, `0.01` or most decimal
cents exactly. The failure is not theoretical in this feature: D1's arithmetic divides an FTE-normalised
salary by a band midpoint to four decimal places and compares the result to `0.9500`. Under binary floating
point, two employees on *identical* recorded salaries can produce compa-ratios that differ in the last bit,
and a comparison against a boundary threshold is exactly where that bit decides whether a person is flagged
for a pay-equity finding. A finding that depends on IEEE-754 rounding is one an HR business partner cannot
defend, and the first time somebody recomputes it in a spreadsheet and gets a different answer, the feature
is finished. `numeric` in PostgreSQL is exact decimal, and `psycopg2` maps it to Python `Decimal`.

**(b) Why scale 2 and precision 14.** Scale 2 covers every ISO-4217 currency this product plausibly meets;
zero-decimal currencies (JPY, KRW) store `.00` harmlessly, and three-decimal currencies (KWD, BHD, TND) would
lose a mil — **stated as a known limitation, not discovered later**, and recorded as **TD-16**. Precision 14
gives 12 integer digits: 999,999,999,999.99 in any currency, which is four orders of magnitude past any real
annual salary in any currency including IDR and VND. `numeric(14,2)` is 8 bytes of storage. Going wider costs
nothing but signals a requirement that does not exist.

**(c) Why not integer minor units.** The "store cents as `bigint`" idiom exists because many languages lack a
decimal type. Python and PostgreSQL both have one. Minor units would force every read, every CSV import row,
every comparison and every template to divide by 100 — an arithmetic operation at every boundary, each one a
place to get the factor wrong, and each one silently wrong rather than loudly wrong. And it does not even
solve the problem: dividing two integers to get a compa-ratio produces a float anyway.

**(d) `annual_base_fte` is computed at write and STORED. This is the non-obvious half of the ADR.**

```
pay_basis = ANNUAL   →  annual = amount
pay_basis = MONTHLY  →  annual = amount * 12
pay_basis = HOURLY   →  annual = amount * company_compensation_settings.standard_annual_hours
annual_base_fte      =  annual / fte            -- normalise a part-timer to a full-time equivalent
```
All in `Decimal`, quantised to 2dp with `ROUND_HALF_UP` at the *end*, once. **It is stored, not a generated
column and not computed on read, for one decisive reason: `standard_annual_hours` is per-company and
editable.** If the comparison value were derived on read, a PORTAL_ADMIN editing 1976 → 2080 in 2028 would
silently re-value every historical hourly record and change the answer to a pay-equity question that was
already asked, answered and dispositioned. History must not move. A `GENERATED ALWAYS AS ... STORED` column
cannot reference another table, so storing it explicitly is also the only mechanism available.

**(e) Currency is on the record, and there is exactly one per record.** No multi-currency record, no "amount
in local + amount in reporting currency". A pay market carries one currency (§3.5); a merged multi-currency
market is refused at configuration time; there is no FX in this cycle and **no silent 1:1 conversion
anywhere, ever**. Any code path that would need to compare two currencies must raise, not guess.

**(f) The serialisation boundary — this is the part an engineer will get wrong.** `app/db.py:134-142`
`serialize()` turns `Decimal` into `float`, and `to_dict()` runs it over every column of every row. So the
default, obvious, everywhere-else-correct read helper **destroys the guarantee this ADR just bought**, and it
does so silently — `85000.00` becomes `85000.0`, which looks fine right up to the point where a client sums a
few of them.

> **Rule, and it is a review gate: no compensation amount is ever read through `to_dict()`.**
> `compensation_service` provides the only readers, and they emit money as `{"amount": "85000.00",
> "currency": "EUR"}` — a **decimal string**, because a JSON number is an IEEE-754 double in every JavaScript
> client on earth. A `money_out(Decimal) -> str` helper and a `money_in(str|Decimal) -> Decimal` validator
> live in `compensation_service` and nowhere else.

`tests/test_compensation_money.py` asserts this three ways: `money_out` round-trips 25 awkward values without
loss; a module-inspection gate asserts `compensation_service` never calls `to_dict`; and an API test asserts
the JSON payload's `amount` is a *string*.

**Rejected alternatives.** `float8` (rejected, (a)). `bigint` minor units (rejected, (c)). A `money` column
type (rejected: locale-dependent, fixed to the server's `lc_monetary`, and widely deprecated in practice).
Computing `annual_base_fte` on read (rejected, (d)).

---

### 4.2 ADR-015 — The effective-dated compensation record

**Decision: Build `employee_compensation` as an append-only-for-value, effective-dated history with
database-enforced non-overlap. No UPDATE of a value, no DELETE path, corrections are new rows, voids are
marked.** Confidence **High**.

**(a) Shape follows `manager_relationships`, deliberately.** `effective_from DATE NOT NULL` / `effective_to
DATE NULL` / `is_current BOOLEAN NOT NULL` is the pattern already in `manager_relationships`
(`schema.sql:459-473`) and `employee_org_assignments` (`:355-366`). Engineers know it. A novel bitemporal
model would be gratuitous — nobody has asked "what did we believe this person's salary was last March?", only
"what was it".

**(b) What EP42 adds that the existing pattern lacks, and why.** Those two tables have *no constraint linking
the three fields* and *no uniqueness on `is_current`* (V6). Two current rows are representable today, and for
placement that is a display bug. For pay it is an unanswerable question — "what is this person paid?" would
have two answers, and the equity engine would count them twice. So:
- `chk_ec_current` ties `is_current` to `effective_to IS NULL`;
- `uq_ec_one_current` (partial unique) guarantees exactly one current row per employee;
- `excl_ec_no_overlap` (GiST exclusion on `daterange`) guarantees no two **active** periods overlap, current
  or historical — which the partial unique index alone cannot do for closed periods.

That last one is the answer to *"prevent overlapping periods at the DB level if you can"*: **yes, and it
costs one extension.** `btree_gist` is available on the target (V11) and must be added to `schema.sql:25`
alongside `uuid-ossp` and to the CI bootstrap. Without it we would be relying on the service layer to be
right about interval arithmetic in five call sites; with it, a wrong one fails loudly at the insert.

**(c) No UPDATE of a value, and why the guarantee is *partial* rather than total.** `audit_log` blocks every
UPDATE (ADR-009). That cannot work here, because closing an interval (`effective_to`, `is_current`) and
voiding a row are both UPDATEs and both legitimate. So `trg_employee_compensation_immutable` (§3.3) raises if
any *value* column changes and permits the interval and void columns. This is a weaker guarantee than
`audit_log`'s and I am naming that rather than glossing it: an engineer with SQL access can still set
`is_current = FALSE` on the wrong row. What they cannot do — by accident or by a well-meaning "fix this typo"
UPDATE — is change what somebody was paid. That is the guarantee worth having.

**(d) Correction is a new row; void is a marked row.** A typo'd salary is corrected by inserting a record
with the same `effective_from`, which closes the prior one to a zero-length interval (`effective_to =
effective_from`, empty under half-open — see ADR-020) and leaves it visible in history with its reason. A
record entered against the wrong *person* is **voided** (`status='VOIDED'`, `is_current=FALSE`, mandatory
`void_reason`), gated `compensation:d` — PORTAL_ADMIN only by seeded default. Void is destructive to
*meaning*, not to *data*: the row stays, excluded from every read and every computation by
`WHERE status='ACTIVE'`.

**(e) Correlation to `audit_log`.** Every compensation write generates one `correlation_id` and passes it to
both the compensation row and the audit row. `audit_service.company_timeline(company_id,
correlation_id=...)` then returns the audit half; `compensation_service.history()` returns the money half.
The two are joinable and separately gated, which is the whole point of ADR-019.

**(f) Retention class.** Compensation audit rows are written `retention_class='EMPLOYMENT'`, not
`'STANDARD'` — pay history is the class of record that tax and employment law generally require to outlive
employment. **The period itself is a legal determination I will not invent** (Charter §9.2, ADR-009 §3.2c);
DPO ruling is DEP-9, and CFL-42-3 routes the erasure enumeration to the BA. Nothing is purged until they rule,
which is the safe default.

**(g) Indexing for the equity engine at scale, sized.** `idx_ec_equity` is a partial covering index on
`(company_id, employee_id) INCLUDE (annual_base_fte, currency, employment_type) WHERE is_current AND status =
'ACTIVE'`. The engine's group query joins it against `employee_job_assignments`'s `idx_eja_current`; both
partial indexes contain **one row per employee**, so the working set is 146 rows today and 100k at the
hypothetical scale, ~40 bytes each — under 5 MB, permanently resident. §7.4 has the timings.

---

### 4.3 ADR-016 — The central tenant feature switch (KAN-188, CFL-42-1)

**Decision: Build. `company_features.is_enabled` becomes a term in `_load_feature_access()`. The default for
an absent row is a property of the feature — a new `portal_features.default_enabled` column — not a constant
in Python. The two ad hoc consumers are retro-fitted in the same story. `enabled_for_hr` gains no consumer and
gets a named three-step removal path.** Confidence **High**.

#### (a) The finding that changes the story: the rows are not absent, they are FALSE

The SPM's D6 requirement 2 is *"absent row defaults **enabled** for the eleven existing features — KAN-188
must change nothing for any existing feature or tenant, and that is an acceptance criterion."* That
acceptance criterion is correct and the stated mechanism does not achieve it, because **the rows exist**
(V2):

| Feature | Acme | Telia | Sam Cpmapny |
|---|---|---|---|
| `reports` | ✅ TRUE | ✅ TRUE | *(no row)* |
| `skills_intelligence` | ✅ TRUE | ✅ TRUE | *(no row)* |
| `employee_profiles`, `org_structure`, `user_accounts`, `skills`, `vacations`, `company_settings`, `system_config` | ❌ **FALSE** | ❌ **FALSE** | *(no row)* |
| `org_change`, `audit_log` | *(no row)* | *(no row)* | *(no row)* |

Those 14 FALSE rows are inert today because nothing reads them. On the day the resolver honours them, every
non-SYSTEM_ADMIN user in Acme and Telia loses the employee directory, the org tree, user administration,
skills, vacations and company settings — **the entire product**, in both populated tenants, with the login
page still working so it looks like a permissions catastrophe rather than a feature flag. `seed_rbac.sql`
carries none of these rows, so **CI would be green** the whole way. This is the single highest-consequence
defect available in EP42 and it is available on day one of W0.

#### (b) The mechanism

**One column, three lines of SQL, no hardcoded lists.**

```sql
ALTER TABLE portal_features
    ADD COLUMN IF NOT EXISTS default_enabled BOOLEAN NOT NULL DEFAULT TRUE;
UPDATE portal_features SET default_enabled = FALSE
 WHERE code IN ('compensation','compensation_self','pay_equity');
```

Then in `_load_feature_access()`, one extra `LEFT JOIN` on the query that already runs — **no extra round
trip, no change to `has_feature_access()`'s signature, no second resolution point**:

```sql
FROM role_feature_access rfa
JOIN roles ro          ON ro.id = rfa.role_id
JOIN portal_features pf ON pf.id = rfa.feature_id
LEFT JOIN company_role_feature_access crfa
       ON crfa.role_id = rfa.role_id AND crfa.feature_id = rfa.feature_id
      AND crfa.company_id = %s::uuid
LEFT JOIN company_features cf                       -- ← the only new join
       ON cf.feature_id = pf.id AND cf.company_id = %s::uuid
WHERE ro.name = ANY(%s)
  AND (ro.company_id = %s::uuid OR ro.company_id IS NULL)
GROUP BY pf.code, COALESCE(cf.is_enabled, pf.default_enabled)
```

with each of the three `bool_or(...)` expressions wrapped in
`... AND COALESCE(cf.is_enabled, pf.default_enabled)`. Effective access = **tenant switch AND role grant**,
resolved once, serving `@require_feature_access` and `has_feature_access()` identically because both already
call `can_access_feature()` (`app/auth.py:96-97`).

**Note the pre-existing `OR ro.company_id IS NULL` at `app/auth.py:74`.** It is *not* a `CLAUDE.md` violation
— that rule governs **listing a company's roles**, and this clause resolves the *global template role* a user
actually holds. KAN-188 must not "fix" it. Called out because the reviewer of this PR will see it and reach
for it.

**Why a column and not a Python set.** A hardcoded `_DISABLED_BY_DEFAULT = {'compensation', ...}` in
`auth.py` is a second registry of features that has to be kept in step with `portal_features` — the exact
class of drift `TestFeatureRegistryHasNoDrift` exists to catch, reintroduced one file away from it. A column
is carried by `schema.sql` (structure) and `seed_rbac.sql` (value), survives company creation with no code
change, and is visible to the SYSTEM_ADMIN toggle UI for free.

#### (c) The backfill migration — repair first, then materialise

```sql
-- 1. REPAIR. Rows that are FALSE for a feature nothing consults were never
--    enforcing anything. Honouring them now would black out both tenants (V2).
--    `reports` and `skills_intelligence` are excluded: their value is LIVE today
--    and must be preserved verbatim, TRUE or FALSE.
UPDATE company_features cf
   SET is_enabled = TRUE,
       enabled_at = COALESCE(cf.enabled_at, NOW())
  FROM portal_features f
 WHERE f.id = cf.feature_id
   AND cf.is_enabled = FALSE
   AND f.code NOT IN ('reports','skills_intelligence',
                      'compensation','compensation_self','pay_equity');

-- 2. MATERIALISE. Give every (company, feature) pair an explicit row so the
--    SYSTEM_ADMIN toggle screen shows a real state rather than an inferred one.
INSERT INTO company_features (company_id, feature_id, is_enabled)
SELECT c.id, f.id, f.default_enabled
  FROM companies c CROSS JOIN portal_features f
 ON CONFLICT (company_id, feature_id) DO NOTHING;
```

Step 2 is idempotent (`ON CONFLICT DO NOTHING`, and the PK is `(company_id, feature_id)`,
`schema.sql:944-948`). Step 1 is idempotent by construction. **The acceptance criterion — "no behaviour change
for any existing feature or tenant" — is testable and must be tested as a before/after matrix**: for each of
the 3 companies × 11 features × 10 roles, the resolved `{r,w,d}` after the migration equals the value before.
That is 330 cells and it is a loop, not a chore. Task **T-188-6**.

**Company creation** (`app/routes/company.py:96-147`) inserts the rows from `portal_features.default_enabled`
inside its existing write, so a new tenant gets compensation **off** without anybody remembering.

#### (d) The "off" state is a real screen, and SYSTEM_ADMIN is signposted

`_load_feature_access()` additionally populates `g._tenant_disabled_features` — the set of codes where the
role grant *would* have passed but the tenant switch is off. `require_feature_access()` then branches:

```
can_access_feature(code, action) ................. → run the view
else if code in g._tenant_disabled_features ...... → render templates/feature_disabled.html, HTTP 200
else ............................................. → existing flash + redirect to dashboard
```

Following the `analytics_locked.html` precedent (`analytics.py:184`): a plain explanation, the feature's
label, who can enable it, and nothing actionable. **Not a 403** (the user's *permissions* are fine), **not a
redirect** (which reads as "that page does not exist"), **not blank**.

For **SYSTEM_ADMIN**, `_load_feature_access()` short-circuits to full access (`auth.py:50-53`) and must keep
doing so — invariant 4. But the bypass must be *visible*: a separate g-cached helper
`tenant_feature_state(company_id)` (one query, one row per feature) drives a persistent banner —
*"Not enabled for <Company>. You are seeing this because you are a system administrator."* Bypassing a
commercial switch without knowing you are bypassing it is how a demo shows a prospect a feature they have not
bought.

#### (e) Retro-fitting the two ad hoc consumers, and `enabled_for_hr`

`_analytics_enabled()` / `_check_analytics_access()` and `_si_enabled()` / `_check_si_company_access()` are
**deleted**, not left alongside. Their call sites already sit behind `@require_feature_access('reports')` /
`('skills_intelligence')`, which now carries the tenant term, so the checks become dead code — and dead
access-control code is worse than none, because the next engineer copies it. `analytics_locked.html` is
generalised into `feature_disabled.html`. A **grep-assert test** (`test_tenant_switch.py`) fails if
`company_features` is read anywhere in `app/` outside `app/auth.py` and the SYSTEM_ADMIN toggle route. That
single test is what stops the third copy from ever existing.

**`enabled_for_hr` removal path, named as the SPM required:**
1. **KAN-188** — no new consumer; EP42 never reads or writes it; the grep-assert above covers new code.
2. **Follow-on story (P2, not EP42)** — delete the two read sites (`analytics.py:127-131,144`;
   `skills_intelligence.py:183-209`), the `POST /api/admin/skills-intelligence/toggle-hr` route, and the
   toggle in the SYSTEM_ADMIN feature UI. This is a *behaviour change for an existing feature* and needs its
   own regression pass, which is why it is not in KAN-188's Must.
3. **Migration `16` (later)** — `ALTER TABLE company_features DROP COLUMN enabled_for_hr`, with a `_down`
   that re-adds it `DEFAULT FALSE`. Recorded as **TD-17**.

#### (f) Caching and the "takes effect on the next request" requirement

D6 requirement 6 asks me to confirm this is free. **Confirmed.** `g._feature_access` is populated once per
request and discarded with the request context (`auth.py:38-45`); there is no cross-request cache and no
process-level memo. A toggle is therefore visible to every user of that tenant on their **next** request,
with no invalidation logic and no new code. Cost: the one added `LEFT JOIN` on an existing query, hitting
`idx_co_feat_lookup` (`schema.sql:1511`) — sub-millisecond, one row.

#### (g) Rejected alternatives

| Option | Verdict |
|---|---|
| A decorator wrapper `@require_tenant_feature` beside `@require_feature_access` | **Reject.** Two decorators means every route needs both, so the control is delivered by diligence again — the exact failure D6 exists to end. And nav would still resolve from a different place. |
| Compute the AND in `can_access_feature()` rather than in the SQL | **Reject.** A second query per check, and `_load_feature_access()`'s cache would hold a value that is not the effective one — two truths on one `g`. |
| Copy the hand-rolled check a third time | **Reject**, per D6. Grows by one copy per feature, forever. |
| Hardcode the three EP42 codes as disabled-by-default in Python | **Reject**, per (b). |

---

### 4.4 ADR-017 — Job architecture: family → level → step

> **⚠️ AMENDED by §12.4** (A1: entry at `.0`, count = increments above entry, per level with no default,
> step expectations, the step roadmap, and the fourth feature code `job_architecture`). §4.4(a), (b) and (d)
> stand; **(c) is withdrawn** — steps are still a count, but the sparse `job_level_step_targets` table is
> replaced by `job_step_expectations`; **(e) is refined** by SPM CFL-42-18's ratification plus §12.4.5.


**Decision: Build `job_architecture_service` over the five tables in §3.2. Levels are ordinal within a family
and their ordinal is immutable once an assignment exists. Steps are a count on the level, not rows.
`employees.job_title` is kept, demoted in the UI, and never used as a grouping key again.** Confidence
**High** on the model, **Medium** on the default step count of 5 (it is a default; the first tenant tells us).

**(a) Why the level, not the step, is the unit of everything.** The level carries the canonical title, the
band (ADR-023), the promotion boundary and the equity grouping key. The step exists so pay can move inside a
level without a promotion. Consequently: `salary_bands` attaches to `(job_level_id, pay_market_id)`;
`pay_equity_findings` groups on `(company_id, job_family_id, job_level_id, pay_market_id)`; and **step is
carried on the finding as an explanatory column, never as part of the key** (D1 — comparing across steps
would flag the ladder itself as a pay-equity problem in every group, every time).

**(b) Ordinal immutability once assigned.** `job_levels.ordinal` is `UNIQUE (job_family_id, ordinal)` and is
**refused at the service layer** once any `employee_job_assignments` row points at that level.
Renaming stays allowed; re-ordering does not. *Why:* the ordinal is what "promotion" means — `PROMOTION` is
defined as a move to a strictly higher ordinal in the same family (ADR-021). Re-ordering a live ladder would
retroactively turn somebody's promotion into a demotion in the audit trail, and would re-key every historical
finding. Reordering is available while `steps_count`/titles are still being drafted, which is when tenants
actually do it. Enforced in the service and asserted by test — **not** by a trigger, for the same
proportionality reason as §3.2's `step_no` note.

**(c) Steps are a count, not rows.** `job_levels.steps_count INT CHECK (BETWEEN 1 AND 12) DEFAULT 5`.
Materialising five rows per level to express "this level has five steps" would give two sources of truth for
one fact and quintuple the configuration burden on the hardest screen in the epic. Where a company wants a
*target point* per step, a sparse `job_level_step_targets` row appears — rows only where there is
information. The owner's "1.1 … 1.5" renders as `f"{ordinal}.{step_no}"`; the roll-to-level-2 semantics are a
**signal, not a transition** (D3.4/OQ-1), implemented as `employee_job_assignments.promotion_eligible`, set
by the service when `step_no = level.steps_count`, cleared on any assignment change.

**(d) CFL-42-4 — two titles, precedence written down.** The SPM's steer is *level title canonical, working
title supplementary*. The technical rule, per surface:

| Surface | Shows | Why |
|---|---|---|
| Directory, org tree, employee card, profile header | **Level title**, with `employees.job_title` in parentheses where present and different | The canonical job is the ladder position |
| `employee_search_index` / `trg_employee_search` | **Unchanged** — indexes `job_title` as today | Changing the trigger means re-indexing 147 rows and touching the one trigger nobody has needed to think about. The level title is *added* to the index in a follow-on, not in EP42. **TD-18** |
| CSV / analytics exports | Both, as two named columns | An export that silently swapped a column would break every downstream consumer |
| `ocSummary()` in the bell (`templates/base.html:630-637`) | Level title only, and **never an amount** | §8.3 |
| Employee edit form | `job_title` labelled **"Working title"**; the level is set through the ladder, not typed | Stops the free-text field drifting back into being the job |

**`employees.job_title` is not dropped, not renamed, not made nullable, and its index and trigger are
untouched in EP42.** Confidence High that this is the right conservatism: S12 shows it feeds full-text search,
and the cost of getting search wrong is felt by every user of the product, not just compensation users.

**(e) Reads of the ladder are gated `employee_profiles`; writes are gated `compensation:w`.** This is a
deliberate asymmetry and it needs stating, because the SPM's KAN-190 says `('compensation','w')` and that is
correct **for configuration**. But the level *title* becomes the job title shown in the directory to everyone,
so a read gate of `compensation` would blank out the directory for every EMPLOYEE. **A job level is not a
salary.** Rule: `GET` of families/levels/assignments → `@require_feature_access('employee_profiles')`;
every mutating ladder endpoint and the configurator page → `@require_feature_access('compensation','w')`.
Logged as **CFL-42-8**, resolved here, and the BA needs it in the criteria.

**(f) Why no separate `job_architecture` feature code.** Three codes is already the most this epic can carry
(§5.2). A ladder with no intent to hold pay is an org-design tool nobody asked for, and the SPM's W1 exit gate
scopes it to *"a tenant that has enabled the feature"*. Enabling `compensation` enables the ladder.
**Consequence, stated:** a tenant cannot have job architecture without being licensed for compensation. If the
product owner ever wants to sell them apart, that is a fourth code and a one-line change to the decorators —
recorded so it is a decision, not a discovery.

---

### 4.5 ADR-018 — Row-level salary visibility, and why it is **not** the forbidden sub-flag

**Decision: Build. Three feature codes gate *reachability*. A single `compensation_service.visible_scope()`
resolves *which rows*. The two are different questions, answered in different layers, and neither may ever
answer the other's.** Confidence **High**. This is the ADR CC-2 requires in writing, and an engineer will get
it wrong without it.

#### (a) The distinction, in code, not in prose

```python
# app/services/compensation_service.py

class Scope:
    """Which employees' amounts this actor may see. Resolved ONCE per request."""
    __slots__ = ('kind', 'employee_ids', 'company_id')
    # kind ∈ 'COMPANY' | 'SUBSET' | 'SELF' | 'NONE'

def visible_scope(actor, company_id):
    """The row scope for `compensation` reads. NEVER consults a role to decide
    whether the FEATURE is available — @require_feature_access already did that
    and its answer is final."""
    if not can_access_feature('compensation', 'r'):
        return Scope('NONE', (), company_id)              # the gate said no. Full stop.
    if 'SYSTEM_ADMIN' in actor['roles']:
        return Scope('COMPANY', None, company_id)         # CLAUDE.md invariant 4
    if _has_company_wide_scope(actor):                    # HR_ADMIN / PORTAL_ADMIN — see (c)
        return Scope('COMPANY', None, company_id)
    ids = direct_report_ids(actor['employee_id'], company_id=company_id)   # V8 fix
    return Scope('SUBSET', tuple(ids), company_id)
```

**Every scoped read takes the `Scope` and turns it into a `WHERE` clause. There is no other path to an
amount.** A `NONE` or empty `SUBSET` returns `403` or an empty set **from the server** — never a full payload
filtered in the browser (D5.3, R-3).

#### (b) Why this is not `enabled_for_hr`

The banned pattern had one specific shape, and naming it precisely is what makes the rule enforceable:

| | The forbidden sub-flag (`enabled_for_hr`, `_si_enabled_for_hr`) | `visible_scope()` |
|---|---|---|
| **Question it answers** | *"May this role reach this feature?"* — the same question the matrix answers | *"Which rows does this actor's already-granted access return?"* |
| **Can it deny a role the matrix granted?** | **Yes.** That was the defect: HR_ADMIN held `skills_intelligence` in `role_feature_access` and was blocked anyway. | **No.** The first line short-circuits on the matrix's answer. A granted role always reaches the surface; only the result set differs. |
| **Does it name roles?** | Yes — a hardcoded list inside a route | Only to distinguish *company-wide* from *own-reports* scope, and via (c) below, which is itself matrix-driven |
| **Where does it live?** | Inside the route, after the decorator | In the service, as a value object the route passes down |
| **Precedent** | The mistake `CLAUDE.md` forbids by name | `org_change`'s `_can_initiate_for` (`org_change.py:55-64`) and `_user_matches_step` (`org_change_service.py:101-105`) — business rules **on top of** the gate, which `CLAUDE.md` explicitly sanctions |

**The one-sentence test an engineer can apply at 5pm:** *if removing the check would give a role access to a
**page** it was granted, the check is a forbidden sub-flag; if removing it would give a role **more rows** on
a page it already reaches, it is a scope.*

#### (c) `_has_company_wide_scope()` — the part that must not become a role list

Naively this is `{'HR_ADMIN','PORTAL_ADMIN'} & actor.roles`, and that is a hardcoded role list in a service —
the wrong shape even if the effect is right today, because a tenant that grants `compensation:r` to a
`COMPENSATION_ANALYST` role of their own would silently get a manager's scope.

**Instead, company-wide scope is derived from the matrix: an actor has it if they hold `compensation` **write**
or **delete**.** Rationale: `w` means "enter or propose a compensation record for anybody in this company"
(D5.4) — an actor who may *write* company-wide cannot sensibly be denied *reading* what they may write.
`SOLID_LINE_MANAGER` is seeded `r` only, and therefore gets the direct-report subset. A tenant that wants a
read-only company-wide auditor grants `compensation:r` **and** widens... — no. That case needs an explicit
answer, so:

> **Rule:** company-wide scope = `compensation:w` **or** `compensation:d` **or** an explicit
> `company_role_feature_access` grant of `compensation:r` **to a role that is not a manager line role**.
> Since the second half is not expressible in the matrix, EP42 ships the first half only and the
> read-only-auditor case is **served by granting `compensation:w` with no write route reachable** — which is
> ugly. **This is a genuine gap in the two-table model and I am not going to paper over it: it is
> CFL-42-12, routed to the SPM.** The clean fix is a fourth code (`compensation_all`) and I recommend against
> adding it in this cycle; the workable interim is that `r`-only means "your reports", which serves the
> manager case — the only one in the seeded matrix — correctly.

#### (d) `compensation_self` is hard-scoped server-side

```python
@app.route('/api/me/compensation')
@require_feature_access('compensation_self')
def api_my_compensation():
    return jsonify(compensation_service.self_view(session['employee_id']))   # never request input
```
No `employee_id` parameter exists on this endpoint. Not "validated", not "defaulted" — **absent**, so there
is no parameter to tamper with. `self_view()` asserts its argument equals `session['employee_id']` as a second
belt. It returns current amount, currency, FTE, effective date, level, step and level title; history only if
`company_compensation_settings.self_view_history`; position-in-range as a **plain-language band label**, never
a compa-ratio number (see (e)); and **no comparison to anybody**.

#### (e) The invertibility hazard the SPM's D5 does not cover — **new finding**

A **compa-ratio is a salary in disguise.** `compa_ratio × band_midpoint = the amount`, and band midpoints are
visible to anyone who can see the ladder configuration. So:

- **`pay_equity` read alone must never render a compa-ratio when a band exists for that group.** The equity
  queue renders `measured_value` numerically **only** to an actor who holds **both** `pay_equity:r` and
  `compensation:r`. To a `pay_equity`-only holder it renders a band label — *"below range"*, *"above range"* —
  and the group-level gap as a percentage (a *median-to-median* ratio is not invertible to any individual's
  pay).
- The same rule binds "position in range" on **My Pay**: the employee sees a label, not a number. This is
  also D5.5's requirement for a different reason (plain language, no implied promise) — two arguments, same
  answer.

Logged as **CFL-42-9** and resolved here. It is an acceptance criterion for KAN-201 and a UAT negative-
visibility case.

#### (f) Enumerated absence, asserted by test

D5.7's surface list becomes `tests/test_compensation_visibility.py`, and every case asserts **absence from the
server payload**, not invisibility in the DOM:

`GET /api/employee/<id>` · `GET /api/org-change/<id>` and the inbox list · `ocSummary` payload ·
`GET /api/notifications` bodies · the search index row · every CSV export · the org-tree node payload ·
analytics aggregates · `audit_log` diffs · error messages and application logs · `GET /api/equity/findings`
for a `pay_equity`-only holder. **Twelve surfaces × the ten roles of D5.2**, driven as a table. That suite is
KAN-194's real deliverable.

---

### 4.6 ADR-019 — Money never reaches `audit_log` (CFL-42-2)

> **⚠️ AMENDED by §12.2(d) and §12.7.** `PROMOTION_APPLIED` is renamed **`LEVEL_CHANGE_APPLIED`** with
> `direction` in the diff (SPM CFL-42-25); five A1 actions are added; and the mandatory `reason` becomes a
> **structured category + optional free text** (SPM amendment A-2 / CFL-42-30) because a key-matching guard
> cannot see inside free text — a guarantee I should not have let stand unqualified.


**Decision: Extend `audit_service` with (1) eleven new `ACTIONS`, (2) a `_MONEYISH_KEYS` denylist matched on
`_`-delimited **tokens**, not substrings, and (3) — the stronger control — a **per-action closed allowlist of
diff keys** for every compensation action. My file, my sign-off. Confidence **High**.**

**(a) The gap is real and I verified it.** `_SECRETISH_KEYS` (`audit_service.py:97-98`) is
`('password','token','secret','api_key','apikey','private_key','session_key','salt','credential')`, matched
case-insensitively as substrings by `_check_no_secrets()` (`:153-159`). Nothing there matches a salary.
`_clean_diff()` (`:162-187`) accepts any flat `field → scalar` mapping, and at `:179-181` it passes values
through `serialize()`, which turns a `Decimal` into a `float`. **Today, `record(..., after={'salary':
Decimal('92000.00')})` writes `{"salary": 92000.0}` into a permanently retained, append-only table whose read
audience is a different feature code.** Nobody has to be careless for that to happen; it is what doing the
obvious thing produces.

**(b) Why the SPM's proposed denylist is necessary but not sufficient — and how I am fixing it.**

D5.6 proposes `_MONEYISH_KEYS = ('salary','pay','compensation','amount','wage','remuneration','base_pay',
'annual_base')` matched "the same way", i.e. as substrings. Two problems, in opposite directions:

*Too broad.* Substring `'pay'` matches `pay_decision`, `pay_basis`, `pay_market`, `pay_market_id` — every one
of which D5.6 itself wants **in** the diff. Substring `'compensation'` matches
`compensation_record_id`. The guard as specified would reject the very rows it is designed to permit, an
engineer would discover this at 5pm, and the cheapest way out would be to weaken the guard.

*Too narrow.* A denylist can only refuse names it has heard of. `amt`, `new_figure`, `total`, `gross`,
`base`, `annual`, `comp` and `value` all sail through. The engineer who writes an amount into a diff is by
definition not thinking about the guard.

**The fix, in two layers:**

```python
# Layer 1 — global backstop. TOKEN match, not substring, plus an explicit
# non-monetary allowlist for the tokens that are legitimately structural.
_MONEYISH_TOKENS = frozenset({
    'salary','salaries','pay','wage','wages','amount','amounts','remuneration',
    'compensation','comp','gross','net','base','annual','monthly','hourly',
    'rate','figure','total','value','band','min','mid','max','midpoint',
})
_MONEY_SAFE_KEYS = frozenset({           # structural, carry no monetary value
    'pay_decision','pay_basis','pay_market','pay_market_id','pay_market_code',
    'pct_change_band','band_label','has_change','direction','currency',
})

def _check_no_money(payload, where):
    for key in payload:
        low = str(key).lower()
        if low in _MONEY_SAFE_KEYS:
            continue
        if _MONEYISH_TOKENS & set(re.split(r'[^a-z0-9]+', low)):
            raise AuditError(
                f"{where} may not contain '{key}' — monetary values never reach "
                f"audit_log; the amount lives in employee_compensation and joins "
                f"by correlation_id (EP42 ADR-019)")

# Layer 2 — the real control. For the money-bearing actions, the diff key set is
# a CLOSED ALLOWLIST. A creatively-named key is refused because it is not on the
# list, not because we guessed it might be money.
_ALLOWED_DIFF_KEYS = {
    'COMPENSATION_RECORDED':  frozenset({'has_change','direction','pct_change_band','currency',
                                         'effective_date','pay_basis','fte_band','source'}),
    'COMPENSATION_CHANGED':   frozenset({'has_change','direction','pct_change_band','currency',
                                         'effective_date','pay_basis','fte_band','source'}),
    'COMPENSATION_VOIDED':    frozenset({'status','effective_date'}),
    'PAY_BAND_CHANGED':       frozenset({'currency','effective_date','job_level_id','pay_market_id',
                                         'width_pct_change_band'}),
    'JOB_LEVEL_ASSIGNED':     frozenset({'job_level_id','step_no','effective_date'}),
    'JOB_LEVEL_CHANGED':      frozenset({'job_level_id','step_no','effective_date','direction'}),
    'STEP_ADVANCED':          frozenset({'step_no','promotion_eligible'}),
    'PROMOTION_APPLIED':      frozenset({'job_level_id','step_no','effective_date','has_pay_change',
                                         'direction','pct_change_band'}),
    'PAY_EQUITY_FLAG_RAISED': frozenset({'check_type','state','job_level_id','pay_market_id',
                                         'group_size','compared_count','coverage_pct','basis'}),
    'PAY_EQUITY_FLAG_DISPOSITIONED': frozenset({'state','justification_category','valid_until'}),
    'PAY_EQUITY_THRESHOLD_CHANGED':  frozenset({'setting','old_band','new_band'}),
}
```

Layer 1 runs on **every** action (it is the successor to `_check_no_secrets`, called beside it). Layer 2 runs
only where `action in _ALLOWED_DIFF_KEYS`, and refuses any key not on the list. **A closed allowlist on the
money-bearing actions is strictly stronger than any denylist, and it is the control I actually rely on.** The
denylist protects the other 16 actions.

**Note `pct_change_band` and `fte_band`, not raw percentages.** A precise percentage change plus one known
prior salary reconstructs the new one. Coarse buckets (`0-5`, `5-10`, `10-20`, `20+`, and their negatives)
carry the operational signal without the arithmetic. Same reasoning as ADR-018(e). `width_pct_change_band` on
a band change likewise.

**(c) The eleven new `ACTIONS`.** Appended to the frozenset — extending the enumeration is sanctioned, S8;
redefining its shape is not.

`COMPENSATION_RECORDED` · `COMPENSATION_CHANGED` · `COMPENSATION_VOIDED` · `COMPENSATION_IMPORTED` ·
`JOB_LEVEL_ASSIGNED` · `JOB_LEVEL_CHANGED` · `STEP_ADVANCED` · `PROMOTION_APPLIED` · `PAY_BAND_CHANGED` ·
`PAY_EQUITY_FLAG_RAISED` · `PAY_EQUITY_FLAG_DISPOSITIONED` · `PAY_EQUITY_THRESHOLD_CHANGED` ·
`TENANT_FEATURE_TOGGLED` · `ORG_CHANGE_SELF_APPROVAL_RECORDED`.

That is fourteen, not eleven — the SPM's list plus `COMPENSATION_IMPORTED` (KAN-195's batch-level row, per
ADR-009 §3.5's directive that bulk import writes **one** audit row with counts, never one per record),
`TENANT_FEATURE_TOGGLED` (D6 requirement 7) and `ORG_CHANGE_SELF_APPROVAL_RECORDED` (D4h's warn-and-audit
branch, ADR-022).

**(d) `entity_id` and `retention_class`.** `entity_id` is the **compensation record id**, not the employee id
— the audit row must point at the immutable thing that holds the amount so the two join. `subject_employee_id`
+ `subject_employee_number` carry the person (never the name — ADR-009). `retention_class='EMPLOYMENT'` for
every compensation and job-level action; `'STANDARD'` for equity findings and threshold changes;
`'SECURITY'` for `TENANT_FEATURE_TOGGLED` and `ORG_CHANGE_SELF_APPROVAL_RECORDED`.

**(e) The trade-off, restated so it is not re-litigated casually.** Somebody reading only `audit_log` cannot
see the old and new amounts. That is the point: `audit_log`'s read audience is the `audit_log` feature code
(PORTAL_ADMIN + HR_ADMIN by default, S10), which is *not* the compensation audience. If a tenant narrows
`compensation` to two people and leaves `audit_log` at default, an amount in a diff is readable by exactly
the people they excluded. **Access control that a second feature routes around is not access control.**
Defensibility survives because the audit row points at an immutable compensation record via `entity_id` and
shares its `correlation_id`.

---

### 4.7 ADR-020 — Effective dating: half-open intervals, and the CFL-4 resolution

**Decision: Adopt half-open intervals `[effective_from, effective_to)` as the project-wide convention for
every effective-dated table, existing and new. Add `effective_date` to `org_change_requests` and thread it
through `create_request()` and `_apply_change()`. **No historical rows are rewritten.** Confidence **High**.

#### (a) What CFL-4 actually is

`_apply_change` closes the outgoing assignment with `effective_to = CURRENT_DATE`
(`org_change_service.py:369-373`) and inserts the incoming row with `effective_from` defaulting to
`CURRENT_DATE` (`schema.sql:361`). Read as a **closed** interval `[from, to]`, both rows cover today — a
one-day overlap on every move ever applied. Read as a **half-open** interval `[from, to)`, `effective_to` is
*exclusive*: the outgoing row covers up to but not including today, the incoming row starts today, and
**there is no overlap and never was.**

#### (b) The resolution: change the convention, not the data

**Adopt half-open.** Five arguments, in order of weight:

1. **It rewrites no history.** Every existing row is already correct under this reading. Closed-closed would
   require decrementing `effective_to` on every historical `employee_org_assignments` and
   `manager_relationships` row — a backfill over data whose provenance nobody can reconstruct, to fix a
   defect that only exists in the reading. The SPM asked for the overlap to be corrected *without rewriting
   history*; this is the only convention that does.
2. **It costs nothing on the read side, today.** `effective_to` is **read nowhere in `app/`** (V6). There is
   exactly one write site. Every read filters `is_current`. So the convention can be fixed *before* the first
   date-range read exists — which is the only cheap moment there will ever be. If EP42 does not settle it,
   KAN-202's compensation timeline will settle it by accident.
3. **It is the only convention that can represent a same-day correction.** A salary entered wrong this
   morning and corrected this afternoon needs the first row to cover zero days. Half-open: `effective_to =
   effective_from`, an empty `daterange`, legal under `chk_ec_interval`. Closed-closed: `effective_to =
   effective_from - 1`, which is `to < from` and violates every sane CHECK.
4. **`daterange(a, b, '[)')` is PostgreSQL's native default**, so the GiST exclusion constraints in §3.2–3.6
   need no off-by-one arithmetic anywhere. Under closed-closed every constraint and every query would carry a
   `+ INTERVAL '1 day'`, and one of them would eventually be missing.
5. **It composes.** "In force on date *d*" is `effective_from <= d AND (effective_to IS NULL OR effective_to
   > d)` — one predicate, no successor-date arithmetic, and adjacent periods share a boundary value so
   "did anything change on 1 April?" is a single equality.

**The one cost, named:** `effective_to` displayed raw to a user reads one day late ("ended 2026-04-01" for a
period whose last day was 31 March). **UI rule: never display `effective_to`. Display `effective_to - 1` as
"last day", or render the period as `from → next from`.** One helper, `fmt_period(from, to)`, used by every
timeline; asserted by test. Recorded so no one "fixes" the data instead of the display.

#### (c) KAN-189 — the change, precisely

```python
def create_request(company_id, subject_id, requester_user_id, proposed, reason,
                   *, effective_date=None, request_type='TRANSFER',
                   compensation=None):        # ADR-021
    effective_date = effective_date or datetime.date.today()
    _validate_effective_date(company_id, effective_date, request_type)
    ...
```

`_validate_effective_date` enforces the company window (`backdate_limit_days` 90 / `forward_date_limit_days`
180) **and** the asymmetry D4d requires: a **future-dated placement is refused** (there is no scheduler to
apply it — EP38 R5.6, S16), while a future-dated **pay** record is permitted because it is inert data until
its date and every read filters on the date. Both messages name the reason.

`_apply_change(request_id)` becomes `_apply_change(request_id, effective_date)` and uses it as the single
boundary:

```sql
UPDATE employee_org_assignments
   SET is_current = FALSE, effective_to = %s        -- was CURRENT_DATE
 WHERE employee_id = %s::uuid AND is_current;
INSERT INTO employee_org_assignments (..., effective_from, is_current)
     VALUES (..., %s, TRUE);                        -- was the CURRENT_DATE default
```
— and identically for the `manager_relationships` re-point at `:381-388`, which today **does not set
`effective_to` at all**, leaving a closed relationship with a NULL end date. That is a second, quieter
instance of the same defect and KAN-189 fixes it in the same change.

**One date on the request drives placement, level and pay.** A divergent pay effective date is Later (§3.4 of
the SPM's doc); the column is *designed* for it — `org_change_compensation_proposals` can gain a nullable
`pay_effective_date` that falls back to the request's, with **no change of meaning** to the existing column.
Stated so nobody models it away.

#### (d) What this closes

**`AC-185-07` is unblocked and KAN-185 can close** once KAN-189 merges and the modal renders the field (the
field is deliberately absent today rather than silently discarding input — BACKLOG.md:627). **Coordination
required with whoever finishes KAN-185**: the modal change is one input and one payload key, and it belongs
in KAN-189's PR, not KAN-185's, so the schema and the UI land together. Task **T-189-6**.

---

### 4.8 ADR-021 — Compensation rides the org-change request; promotion is a `request_type`

> **⚠️ AMENDED by §12.2(d) and §12.7.** `request_type = 'PROMOTION'` is renamed **`'LEVEL_CHANGE'`** with a
> stored `direction` of `UP` / `DOWN` / `LATERAL` (SPM CFL-42-25). "Promotion" remains the user-facing word
> when the direction is UP. Also: CFL-42-13's `NOT_ANSWERED_NO_PERMISSION` path, and CFL-42-28's suppression
> of the bell quick-approve on money-bearing requests.


**Decision: Build. `org_change_requests` gains `request_type`, `effective_date` and the two level columns; the
**money lives in a one-to-one child table**; `org_change_service` gains a `PROMOTION` and a
`COMPENSATION_REVIEW` path on the **same** engine, the **same** chain and the **same** apply. No second
engine, no second approval, no parallel workflow.** Confidence **High**.

**(a) Why the money is a child table — the correction to D4.** `org_change_requests` is read by
`_DETAIL_COLS` / `_DETAIL_JOINS` (`org_change_service.py:415-440`), which feed `list_pending()`,
`list_my_requests()` and `request_detail()` — every approver's inbox, every bell entry, every summary line.
Those surfaces are gated by `org_change`, which HR_ADMIN, PORTAL_ADMIN and SOLID_LINE_MANAGER hold by default
and which a tenant may grant to anyone. **A `proposed_amount` column on that table is a salary handed to
`org_change:r`.** Not through a bug — through the query that already exists.

Putting it in `org_change_compensation_proposals` inverts the default: **no existing query returns it, and no
future query returns it unless somebody deliberately joins a table called `..._compensation_proposals`.** The
one accessor is:

```python
def compensation_proposal(request_id, actor):
    """The money on a request. Returns None unless the actor holds compensation:r
    AND the subject is in their visible_scope(). Absent, not redacted."""
```
served by `GET /api/org-change/<id>/compensation` gated `@require_feature_access('compensation')` — a
*compensation* endpoint that happens to be keyed by a request id, not an org-change endpoint with a special
case. **R-3 is mitigated by table design rather than by discipline.**

**(b) `request_type`, inferred from what changed (D4f).** In `org_change_service.create_request`:

```
proposed level ordinal > current ordinal (same family) ......... PROMOTION
proposed level present, ordinal <= current, or family changed .. PROMOTION   (demotion/lateral: same type,
                                                                              mandatory reason — D3.4)
no level change, no placement change, pay only ................. COMPENSATION_REVIEW
otherwise ...................................................... TRANSFER
```
Inference lives in **one function** (`_infer_request_type`) called by `create_request`, never in the route and
never in JavaScript — the client sends what the user changed, the server decides what it is called.

**(c) Chain per type, with a mandatory fallback.** `org_change_workflows` gains
`request_type VARCHAR(20) NULL`; `workflow_steps(company_id, request_type)` resolves the type's chain, falls
back to the `TRANSFER` chain (`request_type IS NULL`), and falls back again to `_DEFAULT_STEPS`
(`org_change_service.py:24-27`). **No request ever runs with no chain** — asserted by test with a company
that has configured nothing.

**(d) The pay decision is mandatory to answer, enforced where it cannot be forgotten.** `create_request`
refuses with `PAY_DECISION_REQUIRED` when the actor holds `compensation:r` and no proposal row would be
written. `PROMOTION` additionally refuses `NO_CHANGE` without a non-blank `decision_reason`. For an actor
**without** `compensation:r`, the block is absent from the modal and the request is a placement-only
`TRANSFER` — absent, not disabled, not blank (D4f).

**(e) D4(b) — approver eligibility, checked at create time, writing nothing on refusal.** For a money-bearing
request, resolve every step through the existing `_step_approver_user_ids()` (V12 — reuse, do not
re-implement), intersect each step's user set with the holders of `compensation:r` in that company, and if any
step's intersection is empty, **refuse before the transaction opens** with
`CHAIN_STEP_UNSATISFIABLE: level {n} ({label}) has no approver holding compensation read`. Same shape as
EP38's AC-184-18: block, name the reason, write nothing.

*Cost note:* resolving `compensation:r` holders needs a role→feature query per company, not per user. One
query, cached on `g` for the request. At ten roles and a dozen approvers this is microseconds.

**(f) The D-185-1 hazard, killed structurally rather than by an overlay rule.** For **placement**, `_apply_change`'s
overlay is right: a NULL proposed BU means "no change", because the four placement dimensions are
independent and a request legitimately touches one. For **pay**, that reasoning does not transfer. There is
no such thing as "change the currency but not the amount" — a partially specified salary is not a partial
change, it is an incomplete record, and there is no safe way to complete it. So instead of an overlay rule
that someone must remember, `chk_ocp_complete` (§3.4) makes a partial money proposal **unrepresentable**:
`NEW_SALARY` requires all four of amount, currency, pay_basis and FTE; `NO_CHANGE` and `DEFER` require all
four to be NULL.

The apply path is then trivially safe:

```python
def _apply_compensation(request_id, effective_date, correlation_id):
    p = _proposal(request_id)
    if p is None or p['pay_decision'] in ('NO_CHANGE', 'DEFER'):
        return None                    # writes NOTHING to employee_compensation
    return compensation_service.record(...)      # all four fields guaranteed non-null by CHECK
```
**No NULL and no zero can ever reach `employee_compensation` through this path**, and `chk_ec_amount CHECK
(amount > 0)` is the second net. The named regression test (`TestApplyNeverZeroesASalary`) still covers all
five proposal shapes D4g lists — pay-only, placement-only, level-only, full, and no-prior-record — because
the test's job is to prove the *behaviour*, not to compensate for a missing constraint.

**(g) One atomic apply.** `decide()`'s final-approval branch already wraps step decision + `_apply_change` +
status close-out in one `transaction()` (`org_change_service.py:302-306`). The level assignment and the
compensation record join **that same block**, plus their audit rows. A promotion that moved the level but not
the pay, or vice versa, is not a state this system can reach. Notifications and the pay-equity re-evaluation
run **after** the block (§7.3).

---

### 4.9 ADR-022 — Four-eyes on money in `decide()` (CFL-42-5, backlog open item #5)

> **⚠️ AMENDED by §12.2(c) and §12.7.** The SPM ratified the SYSTEM_ADMIN narrowing **conditional on a
> cancel-not-approve administrative remedy** (Ruling 13) — added in §12.2(c). Also: the universal
> subject≠initiator / subject≠decider rules move to **KAN-203 in W0** (SPM §12.5, two Critical pre-existing
> defects), initiator≠decider is added, and the control is a **silent no-op on the default chain** unless
> ≥2 independently satisfiable levels are required at create (CFL-42-11, CFL-42-26, CFL-42-31).


**Decision: Build the guard inside `org_change_service.decide()`. Hard refusal for requests carrying a
compensation or level change; warn-allow-and-audit for placement-only. Not configurable. **Not bypassable by
SYSTEM_ADMIN.** Confidence **High** on the mechanism; the policy is the SPM's (D4h) and needs OQ-9.

**(a) The guard.**

```python
def _four_eyes_required(request_id):
    """True if this request moves money or a level."""
    row = query("""
        SELECT EXISTS (SELECT 1 FROM org_change_compensation_proposals
                        WHERE request_id = %s::uuid AND pay_decision = 'NEW_SALARY')
            OR (SELECT proposed_job_level_id IS NOT NULL
                  FROM org_change_requests WHERE id = %s::uuid) AS req
    """, (request_id, request_id), one=True)
    return bool(row and row['req'])

def _levels_already_decided_by(request_id, user_id):
    return [r['step_order'] for r in query("""
        SELECT step_order FROM org_change_approvals
         WHERE request_id = %s::uuid AND decided_by_user_id = %s::uuid
           AND decision IS NOT NULL ORDER BY step_order
    """, (request_id, user_id))]
```

Inserted in `decide()` **immediately after the step-eligibility check and before any write**:

```python
prior = _levels_already_decided_by(request_id, user['user_id'])
if prior:
    if _four_eyes_required(request_id):
        return False, (f'you already decided level {prior[0]} of this request; a change that '
                       f'moves pay or job level needs two different approvers')
    audit_service.record('ORG_CHANGE_SELF_APPROVAL_RECORDED', 'org_change_request', request_id, ...)
```

**(b) SYSTEM_ADMIN does not bypass this, and that is deliberate.** `decide()` currently lets SYSTEM_ADMIN
past the approver test (`org_change_service.py:248`). Four-eyes sits **before and independent of** that
branch. `CLAUDE.md`'s invariant is *"SYSTEM_ADMIN bypasses **feature** checks"* — this is not a feature check,
it is a segregation-of-duties control, and a control that the most privileged account can switch off is a
control that does not exist. The SPM's rule is "not configurable, not overridable"; I am reading SYSTEM_ADMIN
as covered by "not overridable". **Flagged to the SPM as an explicit consequence, not assumed** — it is the
one place EP42 narrows an existing SYSTEM_ADMIN capability, and under demo auth (A-2) SYSTEM_ADMIN is one
click away, so without this the control would be trivially defeated in every demo.

**(c) Blast radius, stated.** This changes `decide()` for **EP27 (drag-and-drop) and EP38 (transfer) as well
as EP42.** Placement-only requests keep working — warn, allow, audit — so no existing flow breaks; the
behaviour change is one new audit row on a path that previously wrote none. Both regression suites
(`tests/ui/test_browser.py`, `tests/test_org_change.py`, `tests/test_transfer_entry_point.py`) must be
extended, and the second decision by the same user on a money-bearing request must be asserted refused with
the specific message, not a generic error.

**(d) The overlap warning at configuration time.** `api_admin_org_change_workflow_get`
(`org_change.py:387-407`) gains a computed `overlaps` array: for each ordered pair of steps, resolve
`_step_approver_user_ids()` for both and report a non-empty intersection as
*"levels 1 and 2 can both be satisfied by the same person"*. `O(steps²)` set intersections on chains of two
to four steps — free. This is the half of D4h that prevents the problem instead of catching it, and it is the
half most likely to be dropped under schedule pressure, so it is its own task (**T-198-4**) with its own test.

**(e) Rejected.** Making it configurable (rejected: a control a tenant can switch off for convenience is one
they will switch off for convenience, and the cost is asymmetric — a blocked second approval is an
inconvenience, an unnoticed one-person pay approval is a finding). Enforcing it for *all* request types
(rejected: D4h, and it would break placement flows tenants deliberately configured that way). Enforcing it at
create time by refusing chains with overlapping approver sets (rejected: it refuses a legal configuration on
the basis of who happens to hold a role today, and role membership changes between create and decide).

---

### 4.10 ADR-023 — Pay-equity computation: placement, groups, and cost

> **⚠️ SUPERSEDED IN LARGE PART by §12.6.** A1 replaces the statistical reference with an absolute one for
> the primary check. The `percentile_cont` group query survives **for Check B only**. Placement
> (event-driven per group, after commit, own transaction, advisory-locked company run) **stands unchanged**
> and is the part of this ADR that was right. The cost model **improves** — re-run in §12.6.5.


**Decision: Build `pay_equity_service`. Evaluation is **event-driven per group, after commit**, plus an
on-demand company run. Findings are **materialised rows**, not a view. No batch, no scheduler.** Confidence
**High** on placement, **Medium-High** on the cost model (measured at 146, modelled above that).

**(a) Where the computation runs — the three options I considered.**

| Option | Verdict |
|---|---|
| **Request-time (a view / computed on page load)** | **Reject.** The queue must support "raised on", "dispositioned by", a justification window and a re-fire delta — all of which are *state about a finding over time*. A view has no state. It also recomputes the whole company on every page load. |
| **On write, inside the caller's transaction** | **Reject.** A derived value must never be able to block source-of-truth data. A bug in the median arithmetic would make it impossible for HR to record a salary at all. |
| **On write, after commit, scoped to the affected group** | **Adopt.** |

**(b) The rule.** `compensation_service.record()` / `job_architecture_service.assign()` / band and threshold
changes call, **after** their `transaction()` has committed:

```python
pay_equity_service.evaluate_group(company_id, job_level_id, pay_market_id,
                                  trigger='COMPENSATION_WRITTEN', correlation_id=cid)
```
which opens its **own** `transaction()` (never nested — `app/db.py:78-82` raises). A failure there leaves the
pay record intact, writes a `pay_equity_evaluations` row with `outcome='FAILED'` and the error code, logs
structurally with the correlation id, and returns. The group is picked up by the next event or the on-demand
run. **Idempotence makes this safe:** `uq_pef_one_open` (§3.6) means re-raising an existing finding is a
no-op, so re-evaluation can never duplicate.

**Which group(s) an event touches:**

| Event | Groups re-evaluated |
|---|---|
| Compensation written / voided | 1 — the subject's current `(family, level, market)` |
| Level or step assignment changed | ≤ 2 — the group left and the group joined |
| Employee joins/leaves the company, location moves market | ≤ 2 |
| Band created or changed | 1 — that `(level, market)` |
| Threshold / coverage gate / pay-market definition changed | **all** — routed to the company run, not the group path |
| "Run equity check" button | all |

**(c) The group query, once, in SQL.** One statement per group; the on-demand run is the same statement
without the group predicate, using `GROUP BY`. `percentile_cont(0.5) WITHIN GROUP (ORDER BY annual_base_fte)`
does the median in the database — moving 100k rows into Python to sort them would be the actual scaling
mistake.

```sql
WITH pop AS (
  SELECT e.id, e.gender, ec.annual_base_fte, ec.currency,
         eja.job_level_id, jl.job_family_id, pml.pay_market_id
    FROM employees e
    JOIN employee_job_assignments eja
      ON eja.employee_id = e.id AND eja.is_current
    JOIN job_levels jl ON jl.id = eja.job_level_id
    LEFT JOIN employee_org_assignments eoa
      ON eoa.employee_id = e.id AND eoa.is_current
    LEFT JOIN pay_market_locations pml ON pml.location_id = eoa.location_id
    LEFT JOIN employee_compensation ec
      ON ec.employee_id = e.id AND ec.is_current AND ec.status = 'ACTIVE'
   WHERE e.company_id = %s::uuid
     AND e.employment_status = 'ACTIVE'
     AND e.employment_type NOT IN ('CONTRACTOR','INTERN')     -- D1, counted below
)
SELECT job_family_id, job_level_id, pay_market_id,
       COUNT(*)                                        AS group_size,
       COUNT(annual_base_fte)                          AS compared_count,
       ROUND(100.0 * COUNT(annual_base_fte) / COUNT(*), 2) AS coverage_pct,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY annual_base_fte) AS median_all,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY annual_base_fte)
           FILTER (WHERE gender = 'MALE')              AS median_male,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY annual_base_fte)
           FILTER (WHERE gender = 'FEMALE')            AS median_female,
       COUNT(*) FILTER (WHERE gender = 'MALE'   AND annual_base_fte IS NOT NULL) AS n_male,
       COUNT(*) FILTER (WHERE gender = 'FEMALE' AND annual_base_fte IS NOT NULL) AS n_female,
       COUNT(DISTINCT currency)                        AS currency_count
  FROM pop
 GROUP BY job_family_id, job_level_id, pay_market_id;
```

**`currency_count > 1` aborts that group with `MULTI_CURRENCY_GROUP`** and no finding — the "no silent 1:1"
rule (D1), enforced at the point of computation rather than only at configuration.

**Gates, in order, before any finding is raised:** currency singular → `coverage_pct >= coverage_gate_pct` →
`compared_count >= min_group_size_outlier` (Check A) or `>= min_group_size_gap` **and** `n_male >= 2` **and**
`n_female >= 2` (Check B) → `company_compensation_settings.equity_first_gate_passed_at IS NOT NULL` (D7.4).
Every skip is **counted into `pay_equity_evaluations` and shown**, never silent.

**(d) Cost, measured and modelled.**

| Population | Distinct groups (est.) | Per-group evaluation | Full company run |
|---|---|---|---|
| **Telia, 100 employees** (75 titles → ~12 levels × ~5 markets, but only ~10 populated groups) | ~10 | index scan of ≤ 20 rows — **< 5 ms** | one aggregate over 100 rows — **< 20 ms** |
| **Acme, 46** | ~6 | **< 5 ms** | **< 15 ms** |
| **10,000 employees** | ~200–400 | ~30 rows — **< 10 ms** | one aggregate over 10k rows via `idx_ec_equity` + `idx_eja_current` (both partial, one row per employee, ~400 KB resident) — **150–400 ms** |
| **100,000 employees** | ~1,000–2,000 | **< 15 ms** | **2–5 s** — acceptable for an explicitly-triggered button with a progress state; **not** acceptable synchronously in a request if it ever needs to run per-tenant unattended, which is what KAN-163 would be for |

**The event-driven path is the one that runs constantly and it is O(group), not O(company).** That is the
whole reason for scoping evaluation to the affected group rather than re-running the tenant. The on-demand
full run is bounded by a per-company advisory lock (`pg_advisory_xact_lock(hashtext(company_id))`) so two
admins pressing the button concurrently produce one run, not two interleaved ones.

**(e) Why findings are rows and not a view.** State: `first_raised_at`, disposition, reason, category,
`valid_until`, remediation owner and target date, and the notification retirement that hangs off
`related_id`. None of that is derivable. The re-fire rule (D2) is then a query, not a memory: a `JUSTIFIED`
finding suppresses a re-raise while `valid_until > CURRENT_DATE`, unless `|measured − threshold|` has widened
past `refire_delta_pp`, or the subject's level/step/salary changed (detected by comparing
`last_evaluated_at` against the subject's newest `employee_compensation.created_at` /
`employee_job_assignments.created_at`), or the configuration changed (`company_compensation_settings.updated_at`).

**(f) `RESOLVED_BY_DATA`.** When a re-evaluation finds an `OPEN` finding's group back inside threshold, the
service transitions it to `RESOLVED_BY_DATA` and calls `notification_service.resolve_related('PAY_EQUITY_FLAG',
finding_id, ['PAY_EQUITY_FLAG_RAISED'])` — retiring the bell entry for **every** eligible recipient, which is
DEF-003's actual defect. `chk_pef_reason` deliberately exempts `RESOLVED_BY_DATA` from the mandatory-reason
rule: the data is the reason.

---

## 5. Migrations and the four-place feature registration rule

### 5.1 Conventions

`KAN-166` (Alembic, ADR-004) is **⬜ not started** (BACKLOG.md:536), so EP42 ships hand-numbered idempotent
SQL in the `08`/`09` style that EP38 proved: a banner comment saying what it adds and which deliberate design
points must not be "fixed", `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `INSERT … ON CONFLICT DO
NOTHING`, and a companion `_down.sql` that reverses in FK-safe order and is itself idempotent. If KAN-166 has
landed by build time, each file ships as an Alembic raw-SQL revision instead and `schema.sql` is regenerated
as the baseline — ADR-004 already covers that, and nothing in this design changes.

**`schema.sql` is regenerated from a fresh apply after every migration in this epic** — F9/KAN-165 made it the
authoritative baseline and CI's second job boots the app against `schema.sql` **alone** (`.github/workflows/
ci.yml:100`). A table that exists only in a migration fails that job, which is how the `org_change_*` drift was
caught.

**One new extension.** `CREATE EXTENSION IF NOT EXISTS btree_gist;` goes into `schema.sql` beside `uuid-ossp`
(`schema.sql:25`), into migration `11`, and into the CI bootstrap step and the `CLAUDE.md` local-CI recipe. It
is required by every `EXCLUDE USING gist` constraint in §3. **DEVOPS task T-190-1** — if it is missed, the
migration fails loudly on a fresh database, which is the right failure.

### 5.2 The three feature codes — all four places, or they do not exist

> **⚠️ AMENDED by §12.4.5. There are FOUR codes, not three** — `job_architecture` is added at `sort_order`
> **17** (SPM §14.3.2), registered in KAN-190. The three-code table below stands for the three it covers.


Existing codes occupy `sort_order` 1–10 and 13 (`audit_log`); 11 and 12 stay reserved for EP38
onboarding/offboarding (`scripts/setup_db.py:112-113`). **EP42 takes 14, 15, 16.**

| Code | Label | Description | sort_order | `default_enabled` |
|---|---|---|---|---|
| `compensation` | Compensation | Job architecture, pay records, bands and backfill for other people | **14** | **FALSE** |
| `compensation_self` | My Pay | An employee's view of their own pay, level and step | **15** | **FALSE** |
| `pay_equity` | Pay Equity | The pay-equity queue, findings and their disposition | **16** | **FALSE** |

Seeded `role_feature_access` defaults, exactly per D5.1 (a *ceiling* a tenant may widen or narrow):

| Role | `compensation` | `compensation_self` | `pay_equity` |
|---|---|---|---|
| `EMPLOYEE` | — | **r** | — |
| `SOLID_LINE_MANAGER` | **r** *(row-scoped to direct reports — ADR-018)* | **r** | — |
| `DOTTED_LINE_MANAGER` | — | **r** | — |
| `DEPARTMENT_HEAD` | — | **r** | — |
| `LOCATION_HEAD` | — | **r** | — |
| `HIRING_MANAGER` | — | **r** | — |
| `COMPANY_ADMIN` | — | **r** | — |
| `HR_ADMIN` | **r + w** | **r** | **r + w** |
| `PORTAL_ADMIN` | **r + w + d** | **r** | **r + w** |
| `SYSTEM_ADMIN` | seeded r+w+d for consistency; **bypasses regardless** (`auth.py:50-53`) | same | same |

**`can_delete` is FALSE for every role but PORTAL_ADMIN on `compensation`, and FALSE for everyone on
`compensation_self` and `pay_equity`.** There is nothing legitimate to delete on the last two: a finding is
dispositioned, never deleted, and an employee cannot delete their own pay. Making it undeletable at the
permission layer is cheaper and more reliable than relying on the absence of a delete route.

**All four places, for each of the three codes:**

1. `scripts/setup_db.py::step4_seed_portal_features` — the `features` tuple **and** the `access_map` dict
   (`:102-176`).
2. `database/migrations/12_compensation.sql` — `INSERT INTO portal_features … ON CONFLICT DO NOTHING` plus
   the `role_feature_access` rows via the `FROM roles ro, portal_features f WHERE ro.name=… AND f.code=…`
   pattern already used at `08_audit_log.sql:117-138`.
3. **`database/seed_rbac.sql`** — the same `portal_features` rows *with explicit UUID literals* (the file's
   convention, `:34-43`) **and** the same `role_feature_access` rows. **This is the one that gets missed and
   it broke CI on 9 Aug (DEF-004).** A fresh database is `schema.sql` + `seed_rbac.sql`; migrations are never
   replayed (TECHNICAL_DOCUMENTATION §10), and a feature row is *data*.
4. `role_feature_access` defaults in **both** the migration and the seed — not one or the other.

**`TestFeatureRegistryHasNoDrift` catches a miss — confirmed by reading it, not assumed.**
`test_every_migration_seeded_feature_survives_a_fresh_build` (`tests/test_regression.py:1340-1364`) regexes
every non-`_down` file under `database/migrations/` for `INSERT INTO portal_features … VALUES (…'code'…)` and
asserts each code exists in the live `portal_features`. Run against a CI-style fresh build, a code in the
migration and missing from the seed **fails**. `test_every_gated_feature_is_registered` (`:1366+`) catches the
inverse — gating on a code no row backs.

**Two gaps in that guard that EP42 must close, because it does not check them:**
- It does **not** check `role_feature_access` rows, only `portal_features`. A feature registered everywhere
  with no default grants is invisible to every role but SYSTEM_ADMIN and every test would pass.
  **T-194-3** adds `test_every_ep42_feature_has_seeded_grants`.
- It does **not** check `scripts/setup_db.py`. **T-194-3** adds a parity assertion that the code sets in
  `setup_db.py::features`, the migrations and `seed_rbac.sql` are equal.

### 5.3 Migration by migration

| # | File | Adds | Down file reverses | Story |
|---|---|---|---|---|
| **10** | `10_tenant_feature_switch.sql` | `portal_features.default_enabled BOOLEAN NOT NULL DEFAULT TRUE`; the `company_features` **repair + materialise** backfill (ADR-016c); `org_change_requests.effective_date DATE NULL` | Drops the column; leaves `company_features` rows (dropping them would be the destructive direction — documented in the runbook) | KAN-188, KAN-189 |
| **11** | `11_job_architecture.sql` | `btree_gist`; `job_families`, `job_levels`, `job_level_step_targets`, `job_title_level_map`, `employee_job_assignments` + indexes + the exclusion constraint | Drops five tables in FK order; leaves the extension | KAN-190/191/192 |
| **12** | `12_compensation.sql` | `employee_compensation` + trigger + function + indexes; `company_compensation_settings`; `pay_equity_recipients`; **the three `portal_features` rows and their `role_feature_access` defaults** | Drops the three tables, the trigger, the function, and the three feature rows **with their `role_feature_access` children in FK-safe order** | KAN-193/194 |
| **13** | `13_org_change_compensation.sql` | `org_change_requests.request_type` (default `'TRANSFER'`), the two `from_/proposed_job_level_id` + `step_no` pairs; `org_change_workflows.request_type`; `org_change_compensation_proposals` | Drops the child table and the six columns | KAN-196/197 |
| **14** | `14_pay_markets_bands.sql` | `pay_markets`, `pay_market_locations`, `salary_bands` + constraints; **a default one-market-per-`locations.country` seed per company** | Drops three tables | KAN-199 |
| **15** | `15_pay_equity.sql` | `pay_equity_findings`, `pay_equity_evaluations` + indexes | Drops two tables | KAN-200/201 |

**Reversibility caveat, in the runbook and not only here** (the EP38 §8.1 precedent): every object is
additive, so rollback is clean and total **provided it runs before tenant data lands in the new tables.**
After that, dropping `employee_compensation` destroys pay history and the rollback is a data-loss event of the
most sensitive class in the product. **DEVOPS T-193-8** writes that into the runbook; it must be known before
an incident, not during one.

### 5.4 The 146-row backfill (KAN-195) is **not** data in a migration or a seed

**Rule: no compensation amount, for any employee, ever appears in `database/migrations/*.sql`,
`database/seed_rbac.sql`, `database/schema.sql` or `scripts/setup_db.py`.**

The backfill is a **user action performed per tenant** — a CSV import or manual entry through the product,
audited as `COMPENSATION_IMPORTED` with the row counts and the actor. That is what makes it a *feature* rather
than a fixture, and it is the only shape in which the coverage meter (the adoption instrument, D7.5) means
anything.

Consequences, made concrete so nobody has to infer them:

1. **CI stays exactly as it is.** A fresh CI database has three feature rows, their grants, and **zero**
   compensation rows. Every EP42 test creates the fixture data it needs. Coverage is 0% on a fresh build and
   the equity queue correctly shows "insufficient coverage — not evaluated". That is the right CI state.
2. **Demo data lives in a separate, clearly-labelled dev-only file** —
   `database/seed_demo_compensation.sql`, referenced from the README, **never** run by
   `.github/workflows/ci.yml` and never by `setup_db.py`'s default path. It carries the D8 "synthetic" marker
   in a comment banner, and every screen it feeds carries the persistent *"Demo compensation data —
   synthetic"* banner (D8.3 safeguard 2).
3. **A grep-assert test makes the rule enforceable rather than aspirational.**
   `tests/test_regression.py::TestNoPayDataInSchemaOrSeed` fails if any file under `database/migrations/`, or
   `seed_rbac.sql`, or `schema.sql`, or `setup_db.py` contains an `INSERT` targeting `employee_compensation`
   or `salary_bands`. **T-195-7.** This is the direct analogue of `TestFeatureRegistryHasNoDrift`: the
   registry test stops a feature row from going missing; this one stops a pay row from going in.
4. **Therefore no seed drift is possible**, because there is nothing in the seed to drift.

---

## 6. Service and API design

### 6.1 Module layout and public signatures

```
app/services/job_architecture_service.py
    families(company_id) · create_family(company_id, *, code, name, actor)
    levels(company_id, family_id) · create_level(...) · update_level(...)
      → update_level REFUSES an ordinal change once any assignment exists (ADR-017b)
    set_step_target(company_id, level_id, step_no, percentile, actor)
    title_counts(company_id)                 -> [{'job_title', 'headcount', 'mapped_level_id'}]
    save_title_map(company_id, rows, actor)  -> counts
    apply_title_map(company_id, actor, *, effective_date, dry_run=False) -> {'created','skipped','errors'}
    assign(company_id, employee_id, *, level_id, step_no, effective_date, reason, actor,
           source='MANUAL', correlation_id=None, org_change_request_id=None) -> assignment_id
    current_assignment(employee_id) · history(company_id, employee_id)
    coverage(company_id)                     -> {'on_level': int, 'active': int, 'pct': Decimal}

app/services/compensation_service.py
    money_in(value) -> Decimal        # the ONLY parser.  Rejects float input outright.
    money_out(Decimal) -> str         # the ONLY formatter.  Never float, never to_dict().
    annualise(amount, pay_basis, fte, standard_annual_hours) -> Decimal
    visible_scope(actor, company_id) -> Scope                       # ADR-018
    settings(company_id) -> dict      # lazily creates the row on first read
    current(company_id, employee_id, scope)  -> dict | None
    history(company_id, employee_id, scope)  -> list[dict]          # KAN-202
    self_view(employee_id) -> dict                                  # compensation_self ONLY
    record(company_id, employee_id, *, amount, currency, pay_basis, fte, effective_date,
           reason, actor, source, correlation_id, org_change_request_id=None,
           import_batch_id=None) -> record_id                       # MUST run inside transaction()
    void(company_id, record_id, *, reason, actor) -> None           # compensation:d
    coverage(company_id) -> {'with_record','active','pct','missing_csv_url'}
    import_preview(company_id, upload, actor) -> diff
    import_commit(company_id, batch_id, actor) -> counts            # one transaction, one audit row

app/services/pay_equity_service.py
    markets(company_id) · save_market(...) · assign_locations(...)  # refuses multi-currency (§3.5)
    bands(company_id) · save_band(...)
    compa_ratio(annual_base_fte, band) -> Decimal | None
    evaluate_group(company_id, level_id, market_id, *, trigger, actor=None, correlation_id) -> summary
    evaluate_company(company_id, *, trigger, actor, correlation_id) -> summary   # advisory-locked
    findings(company_id, *, state=None, level_id=None, age_days=None, scope) -> list[dict]
    disposition(company_id, finding_id, *, state, reason, category=None,
                valid_until=None, owner_employee_id=None, target_date=None, actor) -> None
    recipients(company_id) -> list[user_id]      # matrix holders ∪ named list.  Never subtracts.
```

**`record()` must run inside the caller's `transaction()`** and asserts it
(`app.db._in_transaction()` is available at `app/db.py:34-36`) — a bare `record()` raises rather than
committing a lone salary row without its audit row. Same discipline as `audit_service.record()`, for the same
reason: the two must commit together or not at all.

**`money_in()` rejects a Python `float` outright** (`TypeError`), accepting only `str`, `int` or `Decimal`.
That single line is what stops `float` re-entering through a JSON body, and it is cheap.

### 6.2 Route list, with the exact decorator each one carries

**No route in this table uses `@require_roles(...)`.** Every one is feature-gated; business rules
(`_can_initiate_for`, `visible_scope`, four-eyes) sit in the service **on top of** the gate.

| Method + path | Decorator | Service rule on top | Story |
|---|---|---|---|
| *(no new route)* — `_load_feature_access` + `feature_disabled.html` | — | tenant switch AND role grant | KAN-188 |
| `POST /api/admin/company-features/<company_id>` *(existing)* | `@require_roles('SYSTEM_ADMIN')` *(existing — left alone; it is a platform-admin route, not a feature page)* | + audit `TENANT_FEATURE_TOGGLED` | KAN-188 |
| `GET /admin/job-architecture` | `@require_feature_access('compensation','w')` | company scope | KAN-190 |
| `GET /api/job-architecture` | `@require_feature_access('employee_profiles')` | read is not money (ADR-017e) | KAN-190 |
| `POST /api/job-architecture/family` · `/family/<id>` | `@require_feature_access('compensation','w')` | company scope | KAN-190 |
| `POST /api/job-architecture/level` · `/level/<id>` | `@require_feature_access('compensation','w')` | ordinal immutable once assigned | KAN-190 |
| `POST /api/job-architecture/level/<id>/step-target` | `@require_feature_access('compensation','w')` | `step_no <= steps_count` | KAN-190 |
| `GET /admin/job-mapping` | `@require_feature_access('compensation','w')` | — | KAN-191 |
| `GET /api/job-mapping/titles` | `@require_feature_access('compensation','w')` | company scope | KAN-191 |
| `POST /api/job-mapping/save` · `/apply` | `@require_feature_access('compensation','w')` | dry-run first; atomic commit | KAN-191 |
| `GET /api/job-mapping/export.csv` · `POST /api/job-mapping/import` | `@require_feature_access('compensation','w')` | — | KAN-191 |
| `GET /api/employee/<id>/job-assignment` | `@require_feature_access('employee_profiles')` | subject in actor's company | KAN-191 |
| `POST /api/employee/<id>/job-assignment` | `@require_feature_access('compensation','w')` | not self; level in company | KAN-192 |
| `GET /compensation` *(landing + coverage meter)* | `@require_feature_access('compensation')` | `visible_scope` | KAN-193 |
| `GET /api/employee/<id>/compensation` | `@require_feature_access('compensation')` | `visible_scope`; **403 or absent, never filtered client-side** | KAN-193 |
| `POST /api/employee/<id>/compensation` | `@require_feature_access('compensation','w')` | not self; date window; `visible_scope` | KAN-193 |
| `POST /api/compensation/<record_id>/void` | `@require_feature_access('compensation','d')` | mandatory reason | KAN-193 |
| `GET /api/me/compensation` | `@require_feature_access('compensation_self')` | **hard-scoped to `session['employee_id']`; no parameter exists** | KAN-194 |
| `GET /api/employee/<id>/compensation/history` | `@require_feature_access('compensation')` | `visible_scope` | KAN-202 |
| `GET /api/compensation/coverage` · `/missing.csv` | `@require_feature_access('compensation')` | company scope; **no amounts in the missing list** | KAN-195 |
| `GET /admin/compensation/import` | `@require_feature_access('compensation','w')` | — | KAN-195 |
| `POST /api/compensation/import/preview` · `/commit` | `@require_feature_access('compensation','w')` | atomic per batch; one audit row | KAN-195 |
| `POST /api/org-change/request` *(existing, extended)* | `@require_feature_access('org_change','w')` | `_can_initiate_for`; `PAY_DECISION_REQUIRED`; `CHAIN_STEP_UNSATISFIABLE` | KAN-196 |
| `GET /api/org-change/prefill` *(existing, extended)* | `@require_feature_access('org_change','w')` | compensation block **absent** without `compensation:r` | KAN-196 |
| `GET /api/org-change/<id>/compensation` **(new)** | `@require_feature_access('compensation')` | `visible_scope` on the subject | KAN-196 |
| `POST /api/org-change/<id>/decide` *(existing, extended)* | `@require_feature_access('org_change','w')` | four-eyes (ADR-022) | KAN-198 |
| `GET /admin/compensation/settings` | `@require_feature_access('company_settings','w')` | **see 6.3** | KAN-199/200 |
| `POST /api/admin/compensation/settings` · `/pay-markets` | `@require_feature_access('company_settings','w')` | audited; range CHECKs | KAN-199/200 |
| `GET /api/pay-bands` · `POST /api/pay-bands` | `@require_feature_access('compensation','w')` | company scope | KAN-199 |
| `GET /compensation/equity` | `@require_feature_access('pay_equity')` | — | KAN-200 |
| `GET /api/equity/findings` · `/coverage` | `@require_feature_access('pay_equity')` | **compa-ratio numeric only with `compensation:r` too** (ADR-018e) | KAN-200/201 |
| `POST /api/equity/run` | `@require_feature_access('pay_equity','w')` | advisory lock per company | KAN-200 |
| `POST /api/equity/findings/<id>/disposition` | `@require_feature_access('pay_equity','w')` | mandatory reason; category on `JUSTIFIED` | KAN-201 |
| `GET /api/notifications/equity` *(bell section feed)* | `@require_feature_access('pay_equity')` | only this user's `OPEN` findings | KAN-201 |

Nav: `{% if has_feature_access('compensation') %}`, `('compensation_self')`, `('pay_equity')`. Never
`has_role(...)`.

### 6.3 Thresholds are gated `company_settings:w` — resolving a contradiction in D1 vs D5.2

**Observation.** D1 says thresholds are *"configurable by PORTAL_ADMIN only"*. D5.2's matrix says HR_ADMIN
may *"Configure levels / bands / thresholds"*. Those cannot both be true.
**Evidence.** `CLAUDE.md` forbids expressing "PORTAL_ADMIN only" as a role check on a feature route, so it
must be expressed as a *seeded default* of some permission. `compensation:w` is seeded to HR_ADMIN **and**
PORTAL_ADMIN (`5.2`), so it cannot deliver "PORTAL_ADMIN only". `company_settings:w` is seeded to
**PORTAL_ADMIN only** today (`scripts/setup_db.py:150-160` — HR_ADMIN has no `company_settings` row).
**Impact.** Left unresolved, an engineer writes `if 'PORTAL_ADMIN' not in roles: abort(403)` inside the route
— the exact forbidden pattern, arriving through a perfectly reasonable-looking commit.
**Recommendation.** **Thresholds, the coverage gate and pay-market definition are gated
`@require_feature_access('company_settings','w')`.** Levels and bands stay on `compensation:w`. This is the
project's own established precedent — the org-change **runtime** uses `org_change` while its **workflow
configuration** page uses `org_structure:w` (`app/routes/org_change.py:381-409`), and EP38 §9.1 put checklist
template admin on `company_settings:w` for the same reason.
**Expected outcome.** D1's intent is delivered by seeded default, remains changeable per tenant through the
Feature Access tab, and adds no role check and no fourth feature code. Logged **CFL-42-10**. **Confidence
High.**

---

## 7. Transaction boundaries, computation placement and cost

### 7.1 The units of work

| Operation | One `transaction()` covering | After commit |
|---|---|---|
| Record a salary | `employee_compensation` close-previous + insert · `audit_log` | `pay_equity_service.evaluate_group` · notification (none by default) |
| Void a salary | `employee_compensation` UPDATE · `audit_log` | `evaluate_group` |
| Assign / advance a level or step | `employee_job_assignments` close + insert · `promotion_eligible` · `audit_log` | `evaluate_group` (≤2) · promotion-eligible notification |
| Apply the title→level map | N × close+insert · **one** `audit_log` row with counts | `evaluate_company` |
| CSV import commit | N × `employee_compensation` inserts · **one** `COMPENSATION_IMPORTED` audit row with counts (ADR-009 §3.5) | `evaluate_company` |
| Create an org-change request | `org_change_requests` · N × `org_change_approvals` · `org_change_compensation_proposals` | step-1 approver + requester notifications *(existing behaviour)* |
| Final approval of a money request | step decision · `_apply_change` (placement) · level assignment · `compensation_service.record` · 3–4 `audit_log` rows · status close-out | retire call-to-action · notify · `evaluate_group` |
| Disposition a finding | `pay_equity_findings` UPDATE · `audit_log` | `resolve_related()` for **every** recipient |
| Change a threshold | `company_compensation_settings` UPDATE · `audit_log` | `evaluate_company` |
| Toggle a tenant feature | `company_features` UPSERT · `audit_log` | — |

### 7.2 The rules engineers must internalise

1. **One `transaction()` per public service entry point.** Not per table, not per loop iteration.
2. **`audit_service.record()` is called inside it, always.** It joins the caller's block and never commits
   (`audit_service.py:294-304`). A rolled-back pay change must leave no audit row.
3. **Never nest.** `transaction()` raises `RuntimeError` on nesting (`app/db.py:78-82`). A helper that needs
   the transaction runs inside the caller's block. `compensation_service.record()` **asserts** it is inside
   one rather than opening its own — that is what lets `decide()` compose it into the final-approval block.
4. **Notifications go after the block.** A notification cannot be rolled back; "your pay has changed" for a
   transaction that failed is unrecoverable.
5. **Pay-equity evaluation goes after the block, in its own transaction** (ADR-023b). Derived data never
   blocks source-of-truth data.
6. **The `PROMOTION` apply is one block or it is a bug.** Level moved but pay not written — or the reverse —
   is the worst state in this epic, and it is reachable only by breaking rule 1.

### 7.3 Where the pay-equity computation lives — summary

Event-driven **per group, after commit**, plus an on-demand company run guarded by
`pg_advisory_xact_lock`. No batch, no scheduler (KAN-163 is ⬜ not planned). Full reasoning and the rejected
alternatives are in **ADR-023(a)–(b)**.

### 7.4 Cost, at the sizes that matter

| Population | Per-group event (the path that runs constantly) | Full company run (explicit button) |
|---|---|---|
| Acme 46 / Telia 100 — **today** | **< 5 ms** | **< 20 ms** |
| 10,000 | **< 10 ms** | **150–400 ms** |
| 100,000 | **< 15 ms** | **2–5 s** |

The event path is **O(group)**, ~20–30 rows, which is why it can run synchronously on every salary write. The
company run is one aggregate over two partial covering indexes (`idx_ec_equity`, `idx_eja_current`), each
holding one row per employee. Derivation and the query are in ADR-023(c)–(d). **These are modelled above 146,
not measured** — `pay_equity_evaluations.duration_ms` is written on every run precisely so the model can be
checked against reality instead of believed (**observability, T-200-8**).

---

## 8. Security, tenancy and correctness hazards

### 8.1 The D-185-1 precedent, inherited in a worse form

**Observation.** `_apply_change` overlays only changed fields onto the outgoing assignment row
(`org_change_service.py:346-367`) because a proposal stores NULL for "no change", and inserting the raw
proposal once wiped location and functional unit on every BU-only move. **All 4,628 tests passed through it**,
because every test passed a fully-populated proposal.
**Evidence.** The same shape applied to pay writes NULL or 0 over a salary. `NUMERIC` NULL and `0.00` are both
representable, and both are silent.
**Impact.** Critical, and irreversible in practice — the prior value survives in history, but the *current*
value is wrong and payroll is downstream of it.
**Recommendation.** Do **not** rely on an overlay rule. `chk_ocp_complete` (§3.4) makes a partial money
proposal **unrepresentable**, `chk_ec_amount CHECK (amount > 0)` refuses zero, and `_apply_compensation`
writes *nothing* for `NO_CHANGE`/`DEFER` (ADR-021f). Three independent nets, two of them in the database.
**Expected outcome.** The failure mode cannot be produced by a partial proposal, only by a deliberate one.
`TestApplyNeverZeroesASalary` covers the five shapes D4g names and **asserts the final DB row, not the API
response**. **Confidence High.**

### 8.2 Segregation of duties on money

Fully designed in **ADR-022**. The three points that must not be lost in implementation:
the guard is **not bypassable by SYSTEM_ADMIN**; the **overlap warning at chain-configuration time**
(T-198-4) is the half that prevents rather than catches, and is the half most likely to be dropped; and the
change alters `decide()` for **EP27 and EP38** as well, so both regression suites are extended in the same PR.

### 8.3 Enumerated leak surfaces — checked, not assumed

Every row is a `tests/test_compensation_visibility.py` case asserting **absence from the server payload**.

| Surface | Evidence | Rule |
|---|---|---|
| `ocSummary()` bell summary | `templates/base.html:630-637` | Level title only. Never an amount, never a percentage. |
| Notification bodies + email dispatch | `notification_service.create_user_notification` | No amount, no invertible percentage (D2). |
| `employee_search_index` / `trg_employee_search` | `schema.sql:1861` | Trigger fires on `first_name, last_name, job_title, email` only. **EP42 adds no column to it.** |
| Org tree, directory, cards, tooltips | `app/routes/org.py`, `helpers.TREE_CTE` | Level title added; no compensation join, ever. |
| Analytics + reporting exports | `app/routes/analytics.py` | No compensation table is joinable from `reports`. Grep-assert. |
| `org_change` request detail / inbox | `org_change_service.py:415-440` | Money is in a **child table** (ADR-021a) — absent by construction. |
| Any CSV export | coverage "missing list", mapping CSV | The missing list is employees **without** a record: no amount exists to leak. The mapping CSV carries titles and levels only. |
| Application logs and error messages | EP38 CC-17 bar | Nothing beyond employee id + employee number. `money_out` is never called from a log statement — grep-assert. |
| `audit_log` diffs | ADR-019 | Closed allowlist per action. |
| Every JSON payload | ADR-018f | Absent from the payload, not hidden by CSS or a template condition. |

### 8.4 Inference and invertibility — the surface nobody enumerated

Three inference paths exist that no "does the payload contain an amount?" test would catch:

1. **compa-ratio × published band midpoint = the salary.** Resolved in **ADR-018(e)**: numeric
   `measured_value` renders only to holders of `pay_equity:r` **and** `compensation:r`; everyone else sees a
   band label.
2. **A precise percentage change plus one known prior salary = the new salary.** Resolved in ADR-019(b):
   `pct_change_band` is a coarse bucket, never a percentage.
3. **A group of size 1 or 2 makes a "group median" an individual's salary.** Resolved by the `n ≥ 3` / `n ≥ 5`
   minimums (D1) — which exist for statistical reasons and turn out to be a privacy control as well. **The
   minimums must therefore never be configurable below 2**, and `chk_ccs_min_o` / `chk_ccs_min_g` enforce it
   in the database rather than in the settings form.

### 8.5 Tenancy and row scoping

- **Every EP42 table carries `company_id` directly** (§3.1 rule 1) — not inherited through a join the way
  `employee_org_assignments` does (V9).
- **Composite FKs make a cross-tenant row impossible**, not merely absent (§3.1 rule 2). This is stronger
  than anything currently in the schema and it is the cheapest place to add it.
- **`helpers.direct_report_ids()` must gain a `company_id` parameter** before `visible_scope()` uses it (V8).
  It is used elsewhere, so the parameter is optional-with-a-deprecation-comment and EP42 always passes it.
  **T-194-2.** Recorded as **TD-19** for the other call sites.
- **`OR company_id IS NULL` appears nowhere in EP42.** The one existing instance (`app/auth.py:74`) resolves
  a *global template role a user holds* — a different question from "list this company's roles" — and must
  not be touched by KAN-188.
- **A SYSTEM_ADMIN with "All Companies" selected must see zero cross-tenant amounts** and no cross-tenant
  aggregate of any kind (SPM §3.3, explicit). `visible_scope()` returns `COMPANY` for a *named* company, never
  "all"; the compensation landing page requires a company context and says so if one is not selected.

### 8.6 T2/T5, demo auth, and what must be said out loud

- **D8 stands: T2 is not tripped.** Synthetic salary on synthetic people is not real PII. EP42 builds in S3.
  I agree with the SPM's reasoning and have no technical basis to overturn it.
- **T5 is the operative trigger** and it fires on **one real compensation value, anywhere**. The two cheap
  safeguards are engineering deliverables, not policy: the three feature codes ship
  `default_enabled = FALSE` (ADR-016b — R7 doing double duty as a safety default), and the persistent
  *"Demo compensation data — synthetic"* banner is a template partial included by every compensation screen,
  removed by the same change that clears T5's precondition. **T-194-7.**
- **A-2, in engineering terms:** under `app/routes/auth.py`'s email-only login, `session['roles']` is
  self-asserted, so **the whole of ADR-018 is correct in code and unenforceable in practice.** Every
  compensation demo states this at the start; the Demo Readiness Gate verdict is **CONDITIONAL** on the
  disclosure being in the script. This is not an argument to pull S5 forward — D-004's economics hold — but I
  will not certify the visibility model as a *security* control until KAN-148 lands, only as a *correctness*
  one. **Stated in the readiness verdict, §11, not buried here.**
- **My D5 (access & tenancy) gate contribution** for any compensation demo, with the route or query that
  proves each of the five `CLAUDE.md` checks, is **T-194-9** and is a deliverable of KAN-194, not an
  afterthought at demo time.

---

## 9. The task breakdown — engineer level

> **⚠️ AMENDED by §12.8.** The 112 tasks below stand except where §12.8 supersedes them. §12.8 adds six
> stories (KAN-203, KAN-204, KAN-205, KAN-206, KAN-207, KAN-208 — 33 tasks), amends nine existing stories
> (26 tasks), withdraws four, and **re-cuts the critical path** against the SPM's §14.8 build order.
> **New totals: 21 stories, 167 tasks, 88–108 dev-days, critical path 67.0 dev-days.**


**How to read a row.** *Work · files* is the statement of work and the exact files to create or change.
*Dep* is the task(s) that must be merged first (`—` means it can start on day one of its story). *Est* is
dev-days. *Tests* is what must exist and pass. *Done when* is the definition of done **in addition to** the
Engineering Charter §4 DoD, which applies to every row without exception: peer-reviewed, unit + integration
tests passing, `python -m pytest -q` at 0 failures, the regression flow test at 0 failures, migrations
reversible, WCAG 2.2 AA on changed UI, `escH()` on every new DOM builder, observability on new paths,
**and the affected documentation updated in the same commit**.

**Owner legend:** **ARCH** · **SNR** · **MID** · **DEVOPS**.

### 9.1 W0 — KAN-188 — Central tenant feature switch — **Must · P1** — lead: SNR · design: ARCH (ADR-016)

> **This story gates the start of W1 and it is the most dangerous change in the epic** (V2). Sequence
> T-188-1 → T-188-2 → T-188-6 before anything else; the before/after matrix is the acceptance criterion that
> matters, not the new behaviour.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-188-1** | ARCH | ADR-016 signed off (this §4.3) including the **repair-then-materialise** correction to D6 requirement 2. Walk the V2 evidence with the SPM so the acceptance criterion is understood as *"no change to the resolved matrix"*, not *"absent rows default enabled"*. | — | 0.5 | — | SPM has acknowledged the correction in writing |
| **T-188-2** | SNR | Capture the **before** matrix as a fixture: for all companies × all `portal_features` × all roles, the resolved `{r,w,d}` from today's `_load_feature_access()`. Commit as `tests/fixtures/feature_matrix_before_kan188.json` with the generator script. | T-188-1 | 0.5 | the generator is deterministic and re-runnable | fixture committed; 3 × 11 × 10 cells present |
| **T-188-3** | SNR | `database/migrations/10_tenant_feature_switch.sql` part 1: `portal_features.default_enabled BOOLEAN NOT NULL DEFAULT TRUE`; set FALSE for the three EP42 codes (guarded — they may not exist yet, so `UPDATE … WHERE code IN (…)` is a no-op); the **repair** UPDATE and the **materialise** INSERT of ADR-016(c). Companion `10_..._down.sql`. Regenerate `database/schema.sql`. | T-188-1 | 1.0 | fresh-DB apply; re-apply is a no-op; `reports`/`skills_intelligence` values byte-identical before and after; CI fresh-schema boot job green | migration + down + regenerated `schema.sql` merged |
| **T-188-4** | SNR | `app/auth.py::_load_feature_access` — add the single `LEFT JOIN company_features` and wrap each `bool_or` in `AND COALESCE(cf.is_enabled, pf.default_enabled)` (ADR-016b). Populate `g._tenant_disabled_features`. **No signature change** to `can_access_feature` / `has_feature_access` / `require_feature_access`. SYSTEM_ADMIN short-circuit untouched. | T-188-3 | 1.0 | unit: grant + switch-on → allow; grant + switch-off → deny; no grant + switch-on → deny; absent row honours `default_enabled`; **exactly one** query per request (assert the call count) | ARCH-reviewed — this is a security boundary |
| **T-188-5** | MID | `templates/feature_disabled.html` (generalising `templates/admin/analytics_locked.html`): feature label, plain explanation, who can enable it, nothing actionable, HTTP **200**. `require_feature_access` renders it when the code is in `g._tenant_disabled_features`. SYSTEM_ADMIN banner partial `templates/_tenant_bypass_banner.html` driven by `tenant_feature_state()`. WCAG 2.2 AA. | T-188-4 | 1.0 | a role-denied user still gets flash+redirect; a tenant-disabled user gets the page; SYSTEM_ADMIN gets the page content **and** the banner | both paths distinguishable in a browser |
| **T-188-6** | **SNR** | **The acceptance criterion.** `tests/test_tenant_switch.py::test_no_behaviour_change_for_any_existing_feature_or_tenant` — replay the T-188-2 fixture against the post-migration resolver and assert every one of the ~330 cells is identical. | T-188-4 | 0.5 | the test itself | **zero** cells differ. If any does, the migration is wrong, not the fixture |
| **T-188-7** | SNR | Delete `_analytics_enabled` / `_check_analytics_access` (`app/routes/analytics.py:19-45`) and `_si_enabled` / `_check_si_company_access` (`app/routes/skills_intelligence.py:15-30`) and every call site. Add the grep-assert: `company_features` may be read only in `app/auth.py` and the SYSTEM_ADMIN toggle route. | T-188-4 | 1.0 | existing `test_routes_analytics.py` + `test_routes_skills_intelligence.py` green unchanged; grep-assert test | no third implementation can be added without failing a test |
| **T-188-8** | MID | Audit the toggle: `POST /api/admin/company-features/<company_id>` (`analytics.py:100-135`) records `TENANT_FEATURE_TOGGLED` with `company_id`, feature code, old→new, actor, mandatory reason, `retention_class='SECURITY'`, inside a `transaction()`. Requires the action code from T-193-3 — coordinate or land the `ACTIONS` entry here. | T-188-4 | 0.5 | audit row written; rollback leaves none | toggling without a reason is refused |
| **T-188-9** | MID | Company creation (`app/routes/company.py:96-147`) inserts `company_features` rows from `portal_features.default_enabled` inside its existing write. | T-188-3 | 0.5 | a new company has a full row set; the three EP42 codes are FALSE | — |
| **T-188-10** | ARCH | `docs/TECHNICAL_DOCUMENTATION.md` — the access-control section gains the tenant term; `../../CLAUDE.md` "Access Control" gains **"Access = tenant switch AND role grant, resolved once in `_load_feature_access()`"**. **Same commit.** | T-188-4 | 0.5 | doc-currency review gate | `CLAUDE.md` no longer describes a two-table model that is now three |

**KAN-188 total: 7.0 dev-days.** Critical path: T-188-1 → 3 → 4 → 6.

### 9.2 W0 — KAN-189 — Effective dating (CFL-4, unblocks AC-185-07) — **Must · P1** — lead: SNR

> **Runs in parallel with KAN-188 from day one** — it touches `org_change_service`, not `auth.py`. It is the
> shortest path to unblocking a story that is stuck **today**.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-189-1** | ARCH | ADR-020 signed off: **half-open `[from, to)`**, no history rewrite, `effective_to` never displayed raw. Walk it with whoever holds KAN-185. | — | 0.5 | — | KAN-185's owner has agreed the modal change lands here |
| **T-189-2** | SNR | `10_tenant_feature_switch.sql` part 2: `org_change_requests.effective_date DATE NULL`. Nullable so it cannot fail on existing rows and so a pre-KAN-189 request keeps meaning "apply on approval". Regenerate `schema.sql`. | T-189-1 | 0.5 | fresh apply; re-apply no-op | — |
| **T-189-3** | SNR | `org_change_service.create_request(..., *, effective_date=None)` defaulting to today; `_validate_effective_date(company_id, date, request_type)` enforcing the company window and **refusing a future-dated placement** (no scheduler) while permitting a future-dated pay date. Persist it. | T-189-2 | 0.5 | window boundaries at ±1 day; future placement refused with a named error; future pay date accepted | — |
| **T-189-4** | **SNR** | `_apply_change(request_id, effective_date)` uses the date as the **single boundary**: `effective_to = %s` on the outgoing assignment (replacing `CURRENT_DATE`, `:371`) and explicit `effective_from = %s` on the incoming row. **Also fix the manager re-point at `:381-388`, which today closes a relationship without setting `effective_to` at all.** | T-189-3 | 1.0 | **direct DB assertion**: after any applied change there is **exactly one** current assignment, **exactly one** current SOLID_LINE relationship, and **no overlapping day** under `daterange(from,to,'[)') && ` — for a same-day, a backdated and an immediate move | the CFL-4 overlap is unreproducible |
| **T-189-5** | MID | `fmt_period(effective_from, effective_to)` helper (`app/helpers.py`) rendering the **last day** as `effective_to - 1`, plus `templates/` usages. No surface displays `effective_to` raw. | T-189-1 | 0.5 | a period ending 31 Mar stores `2026-04-01` and renders "31 Mar 2026" | grep-assert: no template prints `effective_to` |
| **T-189-6** | MID | Render the effective-date field in `templates/org_change/_move_modal.html` and add it to the request payload — **the field KAN-185 deliberately left out**. Min/max from the company window; default today. WCAG: labelled, keyboard-operable, error text tied by `aria-describedby`. | T-189-3 | 0.5 | UI test: field present, bounded, submitted; out-of-window value rejected server-side | **`AC-185-07` satisfied; KAN-185 can close** |
| **T-189-7** | SNR | Extend `tests/test_org_change.py` and `tests/test_transfer_entry_point.py`; extend `tests/ui/test_browser.py` for the date field (coordinate with UAT, who owns the suite). | T-189-4, T-189-6 | 0.5 | browser suite pass count reported | suites green, counts reported per `CLAUDE.md` |
| **T-189-8** | ARCH | `docs/TECHNICAL_DOCUMENTATION.md` §22 (org-change) gains the interval convention as a **project-wide rule**; `docs/ARCHITECTURE_REVIEW.md` — **CFL-4 closed** with the resolution; `BACKLOG.md` KAN-185 status corrected. Same commit. | T-189-4 | 0.5 | doc-currency gate | a finding is not closed until the review says so |

**KAN-189 total: 4.5 dev-days.** Off the critical path; delivers the epic's first external value.

### 9.3 W1 — KAN-190 — Job families, levels and steps — **Must · P1** — lead: MID · review: SNR

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-190-1** | **DEVOPS** | `CREATE EXTENSION IF NOT EXISTS btree_gist` into `database/schema.sql:25`, the CI bootstrap (`.github/workflows/ci.yml:49-52` and `:100`), the `CLAUDE.md` local-CI recipe, and the README bootstrap. | KAN-188 | 0.5 | CI green on a fresh DB from `schema.sql` alone | every environment can create an exclusion constraint |
| **T-190-2** | SNR | `database/migrations/11_job_architecture.sql`: `job_families`, `job_levels`, `job_level_step_targets` per §3.2 including the **composite FKs and the `UNIQUE (id, company_id)` targets**. Companion `_down`. Regenerate `schema.sql`. | T-190-1 | 1.0 | fresh apply; re-apply no-op; a cross-tenant `job_family_id` insert is **refused by the FK**, not by code | — |
| **T-190-3** | MID | `app/services/job_architecture_service.py` — families and levels CRUD, `company_id = %s::uuid` only. `update_level` **refuses an ordinal change once any assignment exists** (ADR-017b) with a named error; renaming always allowed. `steps_count` 1–12. One `transaction()` per entry point; `audit_service.record()` inside. | T-190-2, T-193-3 | 1.5 | unit per rule; **a company with no ladder returns an empty list, never another company's and never a global default** | `CLAUDE.md` check 2 answered with a query |
| **T-190-4** | MID | `app/routes/compensation.py` (new module) — the six ladder endpoints of §6.2 with the exact decorators. Reads on `employee_profiles`, writes on `compensation:w` (ADR-017e). | T-190-3 | 1.0 | route-guard test per row; **no `@require_roles` anywhere in the module** — grep-assert | — |
| **T-190-5** | MID | `templates/admin/job_architecture.html` + nav `{% if has_feature_access('compensation') %}`. Empty state first (UX owns the design; this is the implementation). `escH()` on every DOM builder. WCAG 2.2 AA: labelled controls, keyboard-operable reorder, focus management, no colour-only status. | T-190-4, UX | 1.0 | UI test: empty state, create family, create level, refuse reorder-when-assigned | — |
| **T-190-6** | MID | Seed one **worked example** ladder per demo tenant in `database/seed_demo_compensation.sql` (dev-only, never CI — §5.4). No opinionated default ships in `seed_rbac.sql`. | T-190-2 | 0.5 | `TestNoPayDataInSchemaOrSeed` still green | the product ships a configurator, not a ladder |
| **T-190-7** | MID | `docs/TECHNICAL_DOCUMENTATION.md` — new "Job architecture" section (schema + API). Same commit. | T-190-4 | 0.5 | doc-currency gate | — |

**KAN-190 total: 6.0 dev-days.**

### 9.4 W1 — KAN-191 — Everyone on a level (the mapping project) — **Must · P1** — lead: MID · review: SNR

> **Risk R-2 lives here.** 41 + 75 distinct free-text titles for 146 people. The screen is the deliverable;
> the story estimate does not include the tenant's own effort, and that must be said in the release notes.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-191-1** | SNR | Migration `11` part 2: `job_title_level_map`, `employee_job_assignments`, both partial unique indexes and `excl_eja_no_overlap`. | T-190-2 | 0.5 | an overlapping period insert is **refused by the constraint**; two current rows refused | — |
| **T-191-2** | SNR | `job_architecture_service.assign()` — close the current row at `effective_date` (half-open), insert the new one, set/clear `promotion_eligible` when `step_no == level.steps_count`, validate `step_no <= steps_count` against the level, audit `JOB_LEVEL_ASSIGNED`/`JOB_LEVEL_CHANGED`. One `transaction()`. | T-191-1, T-190-3 | 1.0 | backdated, same-day and forward assignment; step beyond `steps_count` refused; `promotion_eligible` set and cleared | — |
| **T-191-3** | MID | `title_counts(company_id)` — every distinct `employees.job_title` for ACTIVE employees with headcount and current mapping. One `GROUP BY`, company-scoped. | T-191-1 | 0.5 | Acme returns 41 rows, Telia 75 (assert the shape, not the numbers — they drift) | — |
| **T-191-4** | MID | `save_title_map` + `apply_title_map(dry_run=)` — dry-run returns create/skip/error per employee; commit is **one** `transaction()` for the whole apply with **one** audit row carrying counts (ADR-009 §3.5). Employees already on a level are skipped, never silently overwritten. | T-191-3, T-191-2 | 1.5 | dry-run changes nothing; a mid-apply failure leaves **zero** assignments and **zero** audit rows | — |
| **T-191-5** | MID | CSV round-trip: `GET /api/job-mapping/export.csv` (title, headcount, family, level, step) and `POST /api/job-mapping/import` reusing the EP35-S2 upload shape. Row-level errors reported, never silent. | T-191-4 | 1.0 | malformed row rejected with its line number; export → import is a no-op | — |
| **T-191-6** | MID | `templates/admin/job_mapping.html` — the R-2 screen: title list with counts, per-title level select, bulk-apply, progress, CSV buttons. `escH()`; WCAG 2.2 AA. | T-191-4, UX | 1.5 | UI test: map 3 titles, bulk-apply, verify counts | — |
| **T-191-7** | MID | Level coverage meter + missing list (`job_architecture_service.coverage`), on the compensation landing page. Unassigned employees are **counted and shown**, never silently dropped. | T-191-2 | 0.5 | coverage arithmetic on a fixture with 3 assigned of 5 | — |
| **T-191-8** | MID | Directory / org tree / profile show the **level title** with `job_title` in parentheses; the employee form relabels `job_title` **"Working title"**. `employees.job_title`, its index and `trg_employee_search` are **untouched** (ADR-017d). | T-191-2 | 1.0 | grep-assert: no migration alters `employees.job_title` or the search trigger; search still returns by working title | CFL-42-4 satisfied |
| **T-191-9** | MID | `docs/TECHNICAL_DOCUMENTATION.md` job-architecture section extended; `docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` access facts supplied to the BA. Same commit. | T-191-8 | 0.5 | doc-currency gate | — |

**KAN-191 total: 8.0 dev-days.** The longest story in W1 and the one most likely to be under-estimated.

### 9.5 W1 — KAN-192 — Step advancement and the promotion-eligible signal — **Must · P1** — lead: MID

> **Sequenced after KAN-197** (SPM §5.6 argument 5): the eligibility signal is a notification with a dead end
> until a `PROMOTION` request exists to act on it. Building it first reproduces DEF-001 exactly.
> **Gated on OQ-1** — build against the default (signal, not automatic).

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-192-1** | MID | `POST /api/employee/<id>/job-assignment` — explicit step advance, gated `compensation:w`, **not self**, mandatory reason. Skip-step, skip-level and **downward** moves permitted with a reason (D3.4). Audit `STEP_ADVANCED`. | T-191-2 | 1.0 | up, down, skip and same-level-different-step; self-advance refused at every privilege level | no automatic roll-up exists anywhere — grep-assert on the service |
| **T-192-2** | MID | Promotion-eligible notification when `promotion_eligible` flips TRUE: to the subject's solid-line manager and every `compensation:w` holder. `related_type='JOB_LEVEL_ELIGIBILITY'`, `related_id=<assignment id>`. Icon `NOTIF_ICON['PROMOTION_ELIGIBLE'] = '🪜'` — **never ❌**. Retires via `resolve_related()` when a `PROMOTION` request is raised for the subject **or** the flag clears. | T-192-1, T-197-2 | 1.0 | fires once, not per read; retires for **every** recipient, not only the one who acted; does **not** retire on read (DEF-003) | D4 blind-spot list answered row by row |
| **T-192-3** | MID | The signal's wording is UX's (it is the most easily misread sentence in the epic). Implement exactly as specified; **no forward-looking language**, no implied entitlement. Quick action deep-links to the promotion modal. | T-192-2, UX | 0.5 | copy matches the UX spec verbatim | — |
| **T-192-4** | MID | Profile panel: current level, step, `<ordinal>.<step>` display, level title, eligibility state, history. Gated `employee_profiles`. | T-191-2 | 1.0 | renders for an employee with no assignment ("Not on a level") | an absent level never looks like a level |
| **T-192-5** | SNR | Extend `tests/ui/test_browser.py` with the eligibility bell content — that it appears **with its action**, wears `🪜`, and leaves once a promotion is raised (coordinate with UAT). | T-192-2 | 0.5 | browser suite green, count reported | — |
| **T-192-6** | MID | Docs: job-architecture section + `BACKLOG.md` status. Same commit. | T-192-4 | 0.5 | doc-currency gate | — |

**KAN-192 total: 4.5 dev-days.**

### 9.6 W2 — KAN-193 — The compensation record — **Must · P1** — lead: SNR · design: ARCH (ADR-014/015)

> **The spine of the epic.** Nothing may render a salary until KAN-194 lands with it (SPM §5.6 argument 4), so
> these two stories ship as one release even though they are two stories.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-193-1** | ARCH | ADR-014 + ADR-015 signed off. Walk the `serialize()` `Decimal→float` hazard (V3) with SNR **before** any code — it is the one an experienced engineer will not expect. | KAN-188 | 0.5 | — | SNR can restate why `to_dict()` is banned here |
| **T-193-2** | SNR | `database/migrations/12_compensation.sql` part 1: `employee_compensation` with all ten CHECKs, `uq_ec_one_current`, `excl_ec_no_overlap`, the three indexes, `employee_compensation_immutable()` + trigger. `company_compensation_settings` with its nine range CHECKs. Companion `_down`. Regenerate `schema.sql`. | T-190-1 | 1.5 | fresh apply; re-apply no-op; **an UPDATE of `amount` raises**; an UPDATE of `effective_to`/`is_current`/void columns succeeds; overlapping periods refused; two current rows refused; `amount = 0` refused; `fte = 0` refused | every invariant is a constraint, not a comment |
| **T-193-3** | **ARCH** | `app/services/audit_service.py` — the fourteen new `ACTIONS`, `_MONEYISH_TOKENS` + `_MONEY_SAFE_KEYS` + `_check_no_money()`, and `_ALLOWED_DIFF_KEYS` per-action closed allowlists (ADR-019b). **My file, my edit.** | T-193-1 | 1.0 | `record(after={'salary': …})` raises `AuditError`; `after={'new_figure': …}` raises via the allowlist; `after={'pay_decision':'NO_CHANGE'}` **succeeds**; every existing `test_audit_service.py` case still green | CFL-42-2 closed |
| **T-193-4** | SNR | `compensation_service` money core: `money_in` (**rejects `float`**), `money_out` (decimal string), `annualise()` in `Decimal` with a single `ROUND_HALF_UP` quantise at the end. | T-193-1 | 0.5 | 25 awkward values round-trip losslessly; monthly/hourly/annual × FTE 1.0/0.6/0.8 against hand-computed answers; `money_in(85000.0)` raises | **grep-assert: `compensation_service` never calls `to_dict`** |
| **T-193-5** | SNR | `compensation_service.record()` — close-previous + insert + `audit_service.record('COMPENSATION_RECORDED'/'COMPENSATION_CHANGED', entity_id=<record id>, retention_class='EMPLOYMENT')`. **Asserts it is inside an open `transaction()`.** `employment_type` snapshotted. Correlation id shared with the audit row. | T-193-2, T-193-3, T-193-4 | 1.0 | rollback leaves neither row; a bare call outside `transaction()` raises; the audit diff contains **no amount**; correlation id matches | — |
| **T-193-6** | SNR | `void()` gated `compensation:d`, mandatory reason, sets `status='VOIDED'`, `is_current=FALSE`; audit `COMPENSATION_VOIDED`. **A voided row is excluded from every read and every computation** (`WHERE status='ACTIVE'`). | T-193-5 | 0.5 | voiding the current record leaves the employee with **no** current record and coverage drops; a voided row never appears in a group | — |
| **T-193-7** | MID | `POST/GET /api/employee/<id>/compensation`, `POST /api/compensation/<id>/void`, `GET /compensation` landing — the decorators of §6.2. Amount emitted as a **string**. | T-193-6, T-194-1 | 1.0 | route-guard test per row; JSON `amount` is a string; a `w`-less `r` holder gets **403 and no state change** | — |
| **T-193-8** | **DEVOPS** | Structured logging with `correlation_id` on every compensation write, **never the amount**. Runbook: the §5.3 rollback caveat (dropping `employee_compensation` after tenant data lands is a data-loss event) and the T5 escalation path. | T-193-5 | 0.5 | log assertion: no `money_out` call reachable from a log statement — grep-assert | runbook ARCH-reviewed |
| **T-193-9** | ARCH | `docs/TECHNICAL_DOCUMENTATION.md` — new "Compensation" section (schema, service, the money rule, the interval convention); `../../CLAUDE.md` gains a **Compensation** block: money is `numeric`, never through `to_dict()`, never in `audit_log`, `record()` inside `transaction()`. Same commit. | T-193-7 | 0.5 | doc-currency gate | `CLAUDE.md` binds the next engineer, which is the point |

**KAN-193 total: 7.0 dev-days.**

### 9.7 W2 — KAN-194 — Who may see a salary — **Must · P1** — lead: SNR · design: ARCH (ADR-018)

> **Its real deliverable is the negative-visibility suite, not the feature codes.** UAT's approach must be
> agreed **before** this is built, not after (SPM DoR).

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-194-1** | SNR | The three feature codes in **all four places** (§5.2): `scripts/setup_db.py` features tuple + `access_map`; migration `12` part 2; **`database/seed_rbac.sql`** with explicit UUID literals; `role_feature_access` defaults in **both**. `default_enabled = FALSE` for all three. | T-193-2 | 1.0 | `TestFeatureRegistryHasNoDrift` green **on a CI-style fresh build** (`dropdb/createdb/schema/seed` recipe in `CLAUDE.md`) | DEF-004 cannot recur |
| **T-194-2** | SNR | `helpers.direct_report_ids(manager_emp_id, line='SOLID_LINE', company_id=None)` — add the company filter (V8); `is_direct_report` likewise. EP42 always passes it; other call sites unchanged, logged **TD-19**. | — | 0.5 | a report in another company is excluded | — |
| **T-194-3** | SNR | Extend `tests/test_regression.py`: `test_every_ep42_feature_has_seeded_grants` and a three-way parity assertion between `setup_db.py::features`, the migrations and `seed_rbac.sql`. | T-194-1 | 0.5 | both fail if a place is missed | the §5.2 gaps in the existing guard are closed |
| **T-194-4** | **SNR** | `compensation_service.visible_scope()` + the `Scope` value object (ADR-018a). `_has_company_wide_scope` derives from `compensation:w`/`:d`, **not** from a role list. Every read takes a `Scope`. | T-194-2, T-193-5 | 1.0 | HR_ADMIN → COMPANY; SOLID_LINE_MANAGER → their reports only, **not** the subtree; DOTTED_LINE_MANAGER → none; a role with no grant → `NONE` **before** any query runs | ARCH-reviewed |
| **T-194-5** | MID | "My Pay" — `GET /api/me/compensation` gated `compensation_self`, **no `employee_id` parameter exists**; `self_view()` re-asserts against the session. Profile panel: amount, currency, FTE, effective date, level, step, level title, **band label not compa-ratio**, history only if the tenant enabled it, **no comparison to anybody**, no forward-looking language. | T-194-4, UX | 1.0 | there is no request parameter to tamper with — assert by inspecting the route signature; the panel renders for an employee with no record ("No salary recorded") | — |
| **T-194-6** | **SNR** | **`tests/test_compensation_visibility.py` — the negative-visibility suite.** For each of the ten roles in D5.2 × the twelve surfaces in §8.3: assert the expected `200`-with-amount / `200`-with-the-field-**absent** / `403`, **from the server payload**, and separately from the rendered HTML. Driven as a table, not 120 hand-written tests. | T-194-4, T-194-5, UAT | 1.5 | the suite itself | a CSS-hidden salary **fails**; that is the point |
| **T-194-7** | MID | The persistent *"Demo compensation data — synthetic"* banner partial, included by every compensation template (D8.3 safeguard 2). | T-193-7 | 0.5 | every compensation route's response contains it | removed only by the change that clears T5 |
| **T-194-8** | MID | Tenant-isolation suite for pay: company A sees zero of company B's amounts under every filter, export, search and aggregate — **including a SYSTEM_ADMIN with "All Companies" selected**. | T-194-4 | 0.5 | — | §8.5 satisfied |
| **T-194-9** | **ARCH** | The **D5 · access & tenancy** section of the Demo Readiness Gate pack for compensation: the five `CLAUDE.md` checks each answered **with the route or query that proves it**, plus the A-2 disclosure line for the demo script. | T-194-6 | 0.5 | — | a compensation demo without the A-2 line is **NO-GO** and I will hold that |
| **T-194-10** | ARCH | `docs/TECHNICAL_DOCUMENTATION.md` access-control section: the CC-2 boundary written down (ADR-018b's table). `BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` access facts to the BA. Same commit. | T-194-6 | 0.5 | doc-currency gate | an engineer cannot conclude that scoping is banned |

**KAN-194 total: 7.5 dev-days.**

### 9.8 W2 — KAN-195 — Backfill: bulk import and manual entry — **Must · P1** — lead: MID · review: SNR

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-195-1** | MID | CSV contract: `employee_number, effective_from, currency, annual_base, fte, pay_basis, reason`. Parser with per-row validation: employee exists **in this company**, currency ISO-4217, `fte` in range, amount `> 0` parsed through `money_in` (**a float literal in the file is a row error, not a coercion**), date inside the company window. | T-193-4 | 1.0 | each rule has a rejecting fixture row with its line number | — |
| **T-195-2** | MID | Dry-run → diff → commit reusing the **EP35-S2 surface** (`app/services/import_service.py`, `templates/imports/`). **Do not fork a second importer.** If EP35-S2 has not landed, implement against its contract and refactor onto the wizard later (R-9). | T-195-1 | 1.5 | preview writes nothing; **a row that would set null or zero over an existing salary is rejected at preview** | one importer exists in the codebase — grep-assert |
| **T-195-3** | SNR | `import_commit` — one `transaction()` per batch, N inserts through `compensation_service.record()`, **one** `COMPENSATION_IMPORTED` audit row with counts and the actor (ADR-009 §3.5 — never one row per record). | T-195-2, T-193-5 | 1.0 | a failure at row 40 of 146 leaves **zero** compensation rows and **zero** audit rows | atomicity asserted against a real DB |
| **T-195-4** | MID | Single-employee manual entry from the profile, gated `compensation:w`. Every tenant needs to fix one row without re-uploading. | T-193-7 | 0.5 | — | — |
| **T-195-5** | MID | Empty states: **"No salary recorded"** + a "Record salary" action for a `compensation:r` holder; **"Not applicable — Contractor / Intern"** for those employment types. **Never a blank, dash or zero**, and the two states must not look like each other. | T-194-5, UX | 0.5 | a contractor never shows "No salary recorded"; an absent value never renders as `0` or `—` | an absent value cannot look like a value |
| **T-195-6** | MID | Company coverage meter — `n of m active employees (x%)` — on the compensation landing page, with the missing list exportable to CSV. **The missing list contains no amounts** (there are none to contain). | T-193-7 | 0.5 | arithmetic on a fixture; contractors/interns excluded from the denominator | the adoption instrument exists |
| **T-195-7** | SNR | `tests/test_regression.py::TestNoPayDataInSchemaOrSeed` (§5.4 point 3) — fails on any `INSERT` into `employee_compensation` or `salary_bands` in `database/migrations/`, `seed_rbac.sql`, `schema.sql` or `setup_db.py`. Create `database/seed_demo_compensation.sql`, dev-only, referenced from the README, **never in CI**. | T-193-2 | 0.5 | the test fails if a pay row is added to a migration | seed drift is structurally impossible |
| **T-195-8** | MID | Docs: import section in `TECHNICAL_DOCUMENTATION.md`; the R-2 note in the release notes that **the mapping and backfill effort belongs to the tenant** and is not in the story estimate. Same commit. | T-195-6 | 0.5 | doc-currency gate | A-4 is on the record where a customer will read it |

**KAN-195 total: 6.0 dev-days.**

### 9.9 W3 — KAN-196 — Pay inside the position-change flow — **Must · P1** — lead: SNR · design: ARCH (ADR-021)

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-196-1** | ARCH | ADR-021 signed off, in particular the **child-table** decision and its reason (`_DETAIL_COLS` returns everything on the parent). | T-194-4 | 0.5 | — | SNR can restate why the money is not a column on the request |
| **T-196-2** | SNR | `database/migrations/13_org_change_compensation.sql`: `org_change_requests.request_type` default `'TRANSFER'` + the two level/step pairs; `org_change_workflows.request_type`; `org_change_compensation_proposals` with **`chk_ocp_complete`**. Companion `_down`. Regenerate `schema.sql`. | T-193-2, T-189-2 | 1.0 | every existing request row reads `TRANSFER`; a `NEW_SALARY` row missing `currency` is **refused by the CHECK**; a `NO_CHANGE` row with an amount is refused | the partial money proposal is unrepresentable |
| **T-196-3** | SNR | `create_request(..., compensation=…)` writes the child row in the **same** `transaction()` as the request and its approvals. `PAY_DECISION_REQUIRED` when the actor holds `compensation:r` and no decision was given; nothing pre-selected client-side. | T-196-2 | 1.0 | request + chain + proposal commit together; a failure writes none of the three | — |
| **T-196-4** | **SNR** | D4(b) — the create-time chain check. Resolve every step through the existing `_step_approver_user_ids()` (V12, **reuse**), intersect with `compensation:r` holders, and refuse with `CHAIN_STEP_UNSATISFIABLE: level {n} ({label}) has no approver holding compensation read` **before the transaction opens**. | T-196-3, T-194-4 | 1.0 | unsatisfiable chain → refusal, **zero rows written**, the step named; the escape hatch (placement-only + a later `COMPENSATION_REVIEW`) works | AC-184-18's pattern followed exactly |
| **T-196-5** | SNR | `_apply_compensation()` inside `decide()`'s final-approval `transaction()` (ADR-021f/g): nothing written for `NO_CHANGE`/`DEFER`; `compensation_service.record()` for `NEW_SALARY`, sharing the request's `effective_date` and `correlation_id`. | T-196-4, T-193-5, T-189-4 | 1.0 | **`TestApplyNeverZeroesASalary`** — pay-only, placement-only, level-only, full, and no-prior-record; **assert the final DB row, not the API response** | R-6 closed |
| **T-196-6** | MID | `GET /api/org-change/<id>/compensation` gated `@require_feature_access('compensation')` + `visible_scope`. **`_DETAIL_COLS` is not extended** — grep-assert that no money column is ever selected there. | T-196-3, T-194-4 | 0.5 | an `org_change:r`-only approver's request detail payload contains **no** money key | ADR-021a delivered |
| **T-196-7** | MID | The compensation block inside `templates/org_change/_move_modal.html` — **one modal, one endpoint, one engine, three entry points**. Collapsed by default with **nothing pre-selected**; the no-change path costs **one deliberate click and no extra scroll**; the block is **absent** (not disabled, not blank) without `compensation:r`. `escH()`; WCAG 2.2 AA. | T-196-6, UX | 1.5 | UI test from all three entry points; a user without `compensation:r` sees no block **and no placeholder** | UX's modal-weight constraint met and demonstrated |
| **T-196-8** | SNR | Extend `tests/test_org_change.py`, `tests/test_transfer_entry_point.py` and `tests/ui/test_browser.py`. | T-196-7 | 0.5 | counts reported | — |
| **T-196-9** | MID | Docs: `TECHNICAL_DOCUMENTATION.md` §22 gains the request types and the child table. Same commit. | T-196-8 | 0.5 | doc-currency gate | — |

**KAN-196 total: 7.5 dev-days.**

### 9.10 W3 — KAN-197 — Promotion as a first-class request type — **Must · P1** — lead: SNR

> Closes backlog open item #3, EP38 OQ-1 and EP38 CFL-7. **Not** a variant of KAN-185.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-197-1** | SNR | `_infer_request_type()` — one function, server-side, per ADR-021b. The client sends what changed; the server names it. | T-196-3, T-191-2 | 0.5 | each of the four inference cases; a demotion is a `PROMOTION` with a mandatory reason, not a new type | inference exists in exactly one place — grep-assert |
| **T-197-2** | SNR | `workflow_steps(company_id, request_type)` — the type's chain, falling back to the `TRANSFER` chain, falling back to `_DEFAULT_STEPS`. **No request ever runs with no chain.** | T-196-2 | 1.0 | a company with nothing configured still gets a chain; a company with only a `PROMOTION` chain still gets one for a `TRANSFER` | — |
| **T-197-3** | SNR | Level/step on the request: `from_*` snapshot at create, `proposed_*` validated in-company via the composite FK. `_apply_change` calls `job_architecture_service.assign(source='ORG_CHANGE')` inside the **same** final-approval transaction. | T-197-1, T-191-2 | 1.0 | a promotion applies placement + level + pay **atomically**; an induced mid-apply failure changes **nothing** | the worst state in the epic is unreachable |
| **T-197-4** | SNR | `NO_CHANGE` on a `PROMOTION` requires a non-blank recorded reason (D4c). `_can_initiate_for` (`org_change.py:55-64`) holds for **every** type — an employee can never initiate their own, at any privilege level. | T-197-3 | 0.5 | self-initiated promotion refused for EMPLOYEE, HR_ADMIN acting on themselves, and SYSTEM_ADMIN | KAN-139 preserved |
| **T-197-5** | MID | Modal: level/step selectors, current position shown, request type displayed as inferred (read-only). `escH()`; WCAG. | T-197-3, UX | 1.0 | UI test end-to-end | — |
| **T-197-6** | MID | Audit `PROMOTION_APPLIED` with level/step before→after and `has_pay_change` + `pct_change_band` — **no amount** (ADR-019). Notifications on the existing `ORG_CHANGE_*` events; the subject is told. | T-197-3, T-193-3 | 0.5 | the diff passes `_ALLOWED_DIFF_KEYS`; an amount in it raises | — |
| **T-197-7** | MID | Docs: `TECHNICAL_DOCUMENTATION.md` §22; `BACKLOG.md` — **mark open items #3 and #4 resolved** with pointers (coordinate with the SPM, who owns the file). Same commit. | T-197-6 | 0.5 | doc-currency gate | EP38 OQ-1 recorded as answered |

**KAN-197 total: 5.0 dev-days.**

### 9.11 W3 — KAN-198 — Four-eyes on money — **Must · P1** — lead: SNR · design: ARCH (ADR-022)

> Closes backlog open item #5. **Changes behaviour for EP27 and EP38 as well as EP42.** Needs OQ-9.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-198-1** | ARCH | ADR-022 signed off **including the SYSTEM_ADMIN consequence** — the guard is not bypassable, and that narrows an existing capability. Confirm OQ-9 with the SPM. | T-196-5 | 0.5 | — | the SPM has ratified, or the default is being built against knowingly |
| **T-198-2** | **SNR** | `_four_eyes_required()` and `_levels_already_decided_by()` in `org_change_service`; the guard inserted after the step-eligibility check and **before any write**, and **before** the SYSTEM_ADMIN branch at `:248`. | T-198-1 | 1.0 | one user decides levels 1 and 2 of a money request → **refused, naming the level they already decided, nothing written**; SYSTEM_ADMIN equally refused; a *different* user at level 2 succeeds | the control cannot be switched off |
| **T-198-3** | SNR | Placement-only branch: warn, allow, and audit `ORG_CHANGE_SELF_APPROVAL_RECORDED` (`retention_class='SECURITY'`) inside the decision transaction. **The org-change engine writes its first audit rows here** (V7) — wire `audit_service` into `decide()`. | T-198-2, T-193-3 | 1.0 | a placement self-approval succeeds and leaves exactly one audit row; a rollback leaves none | — |
| **T-198-4** | MID | **The preventive half.** `api_admin_org_change_workflow_get` (`org_change.py:387-407`) returns an `overlaps` array from pairwise `_step_approver_user_ids()` intersections; the chain admin page renders *"levels 1 and 2 can both be satisfied by the same person"* at configuration time. | T-198-2 | 1.0 | a two-`HR_ADMIN`-step chain reports the overlap; a role/named-person chain with no shared holder reports none | the problem is visible when it is cheap to fix |
| **T-198-5** | SNR | Extend `tests/test_org_change.py`, `tests/test_transfer_entry_point.py`, `tests/ui/test_browser.py`, `tests/ui/test_vacation_workflow.py` if touched. Report counts. | T-198-4 | 0.5 | 0 failures | EP27 and EP38 flows demonstrably unbroken |
| **T-198-6** | ARCH | `docs/TECHNICAL_DOCUMENTATION.md` §22; **`../../CLAUDE.md` org-change invariants gain a sixth: "a user may not decide more than one level of a request that moves pay or job level — not configurable, not bypassable by SYSTEM_ADMIN."** `BACKLOG.md` open item #5 resolved (coordinate with the SPM). Same commit. | T-198-5 | 0.5 | doc-currency gate | the invariant binds every future engineer |

**KAN-198 total: 4.5 dev-days.**

### 9.12 W4 — KAN-199 — Pay markets and salary bands — **Should · P2** — lead: MID · review: SNR

> **A soft dependency of KAN-200, not a hard one** (CFL-42-11). D1 already specifies a group-median fallback,
> so KAN-200 must build and ship without bands; where a band exists it becomes the better basis.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-199-1** | SNR | `database/migrations/14_pay_markets_bands.sql`: `pay_markets`, `pay_market_locations` (**PK on `location_id`** — one market per location), `salary_bands` with `chk_sb_order`, `uq_sb_one_current`, `excl_sb_no_overlap`. Plus the **default seed: one market per `locations.country` per company**, idempotent. Companion `_down`. Regenerate `schema.sql`. | T-190-1, T-190-2 | 1.0 | fresh apply; a location in two markets refused by the PK; overlapping bands refused; `min > mid` refused; the default seed produces 3 markets for Acme, 5 for Telia, 3 for Sam Cpmapny | — |
| **T-199-2** | MID | `pay_equity_service.save_market` / `assign_locations` — **refuses a market whose locations imply more than one currency**, naming the currencies (§3.5, D1). No `fx_rates` table, no silent 1:1. | T-199-1 | 1.0 | merging Sweden + Estonia into one market is refused with both currencies named; merging two SEK locations succeeds | the refusal is unconditional and says why |
| **T-199-3** | MID | Band CRUD gated `compensation:w`; effective-dated with the half-open convention; **`PAY_BAND_CHANGED` audited** with `width_pct_change_band`, never amounts. | T-199-1, T-193-3 | 1.0 | superseding a band closes the old one with no overlap; the audit diff passes `_ALLOWED_DIFF_KEYS` | — |
| **T-199-4** | MID | `compa_ratio()` + **out-of-band is allowed, flagged and requires a reason — never hard-blocked** (D3.5). The flag is a UI state on the pay entry form, not a refusal. | T-199-3, T-193-5 | 0.5 | an amount outside the band saves with a reason and is marked; without a reason it is refused | red-circled pay stays in the system rather than going off-system |
| **T-199-5** | MID | `templates/admin/pay_markets.html` + band editor; `templates/admin/compensation_settings.html` for thresholds, gated **`company_settings:w`** (§6.3). Every threshold shows its default as a default; every change audited `PAY_EQUITY_THRESHOLD_CHANGED`. WCAG. | T-199-3, UX | 1.0 | route-guard test: HR_ADMIN reaches bands, **not** thresholds; PORTAL_ADMIN reaches both — **by seeded default, with no role check in the route** | CFL-42-10 delivered |
| **T-199-6** | MID | Step target points (`job_level_step_targets`) as guidance shown beside the band; **never enforced**. | T-199-3 | 0.5 | a target point never blocks a save | — |
| **T-199-7** | MID | Docs: `TECHNICAL_DOCUMENTATION.md` bands + markets. Same commit. | T-199-5 | 0.5 | doc-currency gate | — |

**KAN-199 total: 5.5 dev-days.**

### 9.13 W4 — KAN-200 — The comparison engine — **Must · P1** — lead: SNR · design: ARCH (ADR-023)

> **⛔ Hard-blocked on KAN-168 (real-DB integration tier), which is ⬜ not started.** Group formation,
> `percentile_cont`, coverage arithmetic and the exclusion semantics are **SQL**; a DB-mocked test asserts we
> called `psycopg2`, not that the arithmetic is right. I will not certify this story on mocks.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-200-1** | ARCH | ADR-023 signed off. Escalate the **KAN-168 blocker** to the SPM the day W4 is scheduled, not the day it starts. | T-199-1 | 0.5 | — | KAN-168 is on the plan ahead of KAN-200, or KAN-200 moves |
| **T-200-2** | SNR | `database/migrations/15_pay_equity.sql`: `pay_equity_findings` with all seven CHECKs, **`uq_pef_one_open`**, `idx_pef_queue`, `idx_pef_refire`; `pay_equity_evaluations`. Companion `_down`. Regenerate `schema.sql`. | T-199-1 | 1.0 | a second OPEN finding for the same (subject, group, check) is **refused by the index**; `JUSTIFIED` without a category refused; `REMEDIATION_PLANNED` without an owner refused | idempotent re-evaluation is a DB guarantee |
| **T-200-3** | **SNR** | The group query (ADR-023c) as one statement: exclusions (`CONTRACTOR`, `INTERN`, no record) **counted not dropped**, `coverage_pct`, `median_all`, gendered medians and counts, `currency_count`. | T-200-2, KAN-168 | 1.5 | **against a real DB** on hand-computed fixtures: ordinary group, n=2, n=3, coverage 79% and 81%, single-gender, all-equal, a 0.6-FTE part-timer, an excluded contractor, and a two-country group | arithmetic verified against numbers UAT computed, not the author |
| **T-200-4** | SNR | The gates, in order: currency singular → coverage gate → group minimum → first-gate-passed. Each skip **counted into `pay_equity_evaluations` and shown**, never silent. A group below a minimum reports *"insufficient comparison group"* and raises **zero** flags. | T-200-3 | 1.0 | each gate blocks independently; a 79%-coverage group produces zero findings and one skip count | D7.3 satisfied |
| **T-200-5** | SNR | **Check A** — individual outlier: compa-ratio to band midpoint where a band exists, else to the group median; default flag below `0.950` or above `1.100`; `n >= 3`. **Never pairwise** — one person, one finding. | T-200-4, T-199-4 | 1.0 | a 10-person group produces at most one finding per person, never 45 | — |
| **T-200-6** | SNR | **Check B** — group gender gap: `(median_male − median_female) / median_male`, `n >= 5` and `>= 2` of each gender compared, default `>= 5%`. Behind `gender_gap_check_enabled` so OQ-3 can be answered without a code change. | T-200-4 | 1.0 | hand-computed fixtures; a single-gender group produces nothing; the kill switch works | — |
| **T-200-7** | SNR | `evaluate_group()` / `evaluate_company()` — **after commit, own `transaction()`**, per-company `pg_advisory_xact_lock`. A failure writes a `FAILED` evaluation row and **never rolls back the pay write** (ADR-023b). | T-200-5, T-200-6 | 1.0 | an induced engine exception leaves the compensation row committed and one FAILED row; two concurrent runs produce one | derived data cannot block source-of-truth data |
| **T-200-8** | **DEVOPS** | `duration_ms`, group counts and skip counts written on every run; a structured log line per run with the correlation id; a "slowest company run" metric. **This is how the §7.4 model gets checked against reality.** | T-200-7 | 0.5 | log + row assertions | the cost model is measurable, not believed |
| **T-200-9** | MID | Plain-language framing on **every** equity screen: this is a **measurement, not a compliance conclusion** (D1.3). Copy is UX's; the requirement that it exists on every screen is mine. | T-200-7, UX | 0.5 | every equity template contains the framing partial | R-10 mitigated where a customer will read it |
| **T-200-10** | MID | Docs: `TECHNICAL_DOCUMENTATION.md` pay-equity section including the exact arithmetic and the gate order. Same commit. | T-200-9 | 0.5 | doc-currency gate | the arithmetic is documented where a reviewer can check it |

**KAN-200 total: 8.5 dev-days.** The largest story in the epic.

### 9.14 W4 — KAN-201 — The queue, the bell, and the lifecycle — **Must · P1** — lead: MID · review: SNR

> **This is where DEF-001/2/3 lived.** Every row of D4's blind-spot list is a task here, and each one is
> asserted for **content**, not presence.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-201-1** | MID | `recipients(company_id)` = holders of `pay_equity:r` in that company **∪** `pay_equity_recipients`. **The named list adds and can never subtract** — there is no exclusion column and the function has no filter branch. | T-200-7, T-194-4 | 0.5 | adding a name never removes anyone; an empty list changes nothing | not a sub-flag, by construction |
| **T-201-2** | MID | `/compensation/equity` queue gated `pay_equity`: subject, level, market, group size, basis, measured gap, threshold, raised date, state, owner. Filters by state, group, age. **No bulk disposition.** | T-200-7 | 1.5 | route guard; filters; empty state is the **coverage meter**, never "no findings ✓" at 40% coverage | D7.4 satisfied — the most dangerous screen is not shipped |
| **T-201-3** | **MID** | **ADR-018(e):** `measured_value` renders numerically **only** to an actor holding `pay_equity:r` **and** `compensation:r`; otherwise a band label. Group-level gap percentages render to `pay_equity:r` (a median-to-median ratio is not invertible to an individual). | T-201-2, T-194-4 | 0.5 | a `pay_equity`-only holder's **payload** contains no compa-ratio; a dual holder's does | CFL-42-9 delivered |
| **T-201-4** | MID | Disposition: `JUSTIFIED` (category from a company-configurable list + `valid_until`) · `REMEDIATION_PLANNED` (owner + target date) · `RESOLVED`. **Mandatory reason on every one; no one-click dismiss anywhere.** Audit `PAY_EQUITY_FLAG_DISPOSITIONED`. | T-201-2, T-193-3 | 1.0 | each transition; a blank reason refused by the **CHECK**, not only the form | — |
| **T-201-5** | **MID** | **The bell — every row of D4's list.** New **fourth section "Pay Equity"** in `templates/base.html` after "Position Changes", **feature-gated** `{% if has_feature_access('pay_equity') %}` (never role-gated — the existing "Pending Approvals" section at `:291` is role-gated and is **not** the pattern to copy). Visible only when the viewer has ≥1 `OPEN` finding. `NOTIF_ICON['PAY_EQUITY_FLAG_RAISED'] = '⚖️'` (`:608-623`) — **never ❌**. Counted in the badge. **One** quick action, *"Review →"*, deep-linking to the filtered queue. **No dispose-from-the-bell** — the `templates/base.html:639-641` precedent: a decision without a recorded reason is not auditable. **No amount and no invertible percentage in the body.** | T-201-4 | 1.5 | section renders only when non-empty; icon asserted; badge arithmetic; the action is present **and works**; the body contains no digits that resolve to money | every DEF-001/2/3 failure mode has a test |
| **T-201-6** | **MID** | Retirement: `resolve_related('PAY_EQUITY_FLAG', finding_id, ['PAY_EQUITY_FLAG_RAISED'])` on **any** exit from `OPEN`, including `RESOLVED_BY_DATA`. **Retires for every eligible recipient, not only the one who acted. Does NOT retire on read.** | T-201-5 | 0.5 | asserted across **three** recipients; reading does not retire (DEF-003 in reverse) | — |
| **T-201-7** | SNR | The re-fire rule: a `JUSTIFIED` finding does not re-fire while `valid_until > CURRENT_DATE`, **unless** the gap widened past `threshold + refire_delta_pp`, or the subject's level/step/salary changed, or the configuration changed. | T-201-4, T-200-7 | 1.0 | each of the three early-refire conditions, and the suppressed case | R-1 mitigated; the feature survives contact with HR |
| **T-201-8** | MID | Extend `tests/ui/test_browser.py` with the equity bell **content** — appears with its action, right icon, retires on disposition for every recipient, not on read (coordinate with UAT, who owns the file). | T-201-6 | 0.5 | counts reported | — |
| **T-201-9** | MID | Docs: `TECHNICAL_DOCUMENTATION.md` notifications section gains the fourth bell section and the new `related_type`. Same commit. | T-201-8 | 0.5 | doc-currency gate | — |

**KAN-201 total: 7.5 dev-days.**

### 9.15 W4 — KAN-202 — Compensation history and the audit join — **Should · P2** — lead: MID

> Blocked on **DEP-8** (the SPM's Wave-3 decision on the audit read surface). Deliberately a **compensation**
> surface, so holding `audit_log:r` alone never reveals an amount.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-202-1** | MID | `compensation_service.history(company_id, employee_id, scope)` — every record, active and voided, newest first: effective period (via `fmt_period`, never raw `effective_to`), amount, currency, FTE, pay basis, level/step **as at that date**, actor label, reason, status. Gated `compensation:r` + `visible_scope`. | T-194-4, T-189-5 | 1.0 | a manager sees their report's history and **403** on anyone else's; a voided row is visibly marked, not hidden | — |
| **T-202-2** | MID | Join to `audit_log` by `correlation_id` — `audit_service.company_timeline(company_id, correlation_id=…)` (`audit_service.py:356-388`) — so the two read as one story: the money from `employee_compensation`, the who/why/when from the trail. | T-202-1 | 1.0 | the pair for one change shares a correlation id; **the audit half contains no amount** | ADR-019's trade-off is visibly paid for |
| **T-202-3** | MID | Timeline panel on the profile, gated `compensation`. Level/step transitions from `employee_job_assignments` interleaved on the same timeline. WCAG: a real `<table>` with headers, not a div grid. | T-202-2, UX | 1.0 | renders for an employee with one record, with none, and with a void | — |
| **T-202-4** | SNR | Assert the separation: holding **`audit_log:r` alone** returns a timeline with **no amounts anywhere**, from the server payload. | T-202-2 | 0.5 | the assertion | the two features' audiences stay separate |
| **T-202-5** | MID | Docs: compensation section + `BACKLOG.md` status. Same commit. | T-202-4 | 0.5 | doc-currency gate | — |

**KAN-202 total: 4.0 dev-days.**

### 9.16 Sequencing, the critical path, and what runs in parallel

```
S2 ┌──────────────────────────────────────────────────────────────────────────┐
   │  KAN-188  tenant switch   7.0d  ◄── SNR. GATES W1. The V2 backfill is    │
   │      │                             the whole risk; T-188-6 is the proof. │
   │  KAN-189  effective date  4.5d  ◄── PARALLEL from day 1 (MID+SNR).       │
   │                                     Unblocks AC-185-07 → KAN-185 closes. │
   └──────┼───────────────────────────────────────────────────────────────────┘
S3        ▼
      KAN-190 ladder 6.0 ──► KAN-191 mapping 8.0 ──────────────────┐
          │                        │                               │
          │                        ▼                               │
          │                    KAN-193 record 7.0 ──► KAN-194 visibility 7.5
          │                        │                       │       │
          │                        │                       ▼       │
          │                        │                   KAN-195 backfill 6.0  ║ parallel
          │                        │                       │
          │                        └───────────────────────┼──► KAN-196 pay-in-flow 7.5
          │                                                │            │
          │                                                │            ▼
          │                                                │      KAN-197 promotion 5.0
          │                                                │            │       │
          │                                                │            │       ▼
          │                                                │            │   KAN-192 progression 4.5  ║
          │                                                │            ▼
          │                                                │      KAN-198 four-eyes 4.5   ║ parallel
          ▼                                                ▼
      KAN-199 bands 5.5  ║ parallel, SOFT dep ──►  KAN-200 engine 8.5 ──► KAN-201 queue+bell 7.5
                                                        ▲                        │
                                              ⛔ KAN-168 real-DB tier            ▼
                                                                          KAN-202 history 4.0  ║
```

**Critical path — 53.5 dev-days, serial:**
`KAN-188 (7.0) → KAN-190 (6.0) → KAN-191 (8.0) → KAN-193 (7.0) → KAN-194 (7.5) → KAN-196 (7.5) → KAN-200 (8.5)
→ KAN-201 (7.5)`. KAN-200's other prerequisites (KAN-191, KAN-193) are already on the chain, and KAN-199 is a
**soft** dependency (CFL-42-11), so it adds nothing to the path. Everything else is float.

**Shortest path to the minimum shippable slice** — the SPM's "could we stop here?" point after W2 —
`188 → 190 → 191 → 193 → 194` = **35.5 dev-days.** That is the number to plan against if the epic ever has to
be cut short, and it is the one I would defend.

**What can run in parallel, and who does it:**

| Track | Stories | Owner | Starts |
|---|---|---|---|
| **A — critical path** | 188 → 190 → 191 → 193 → 194 → 196 → 200 → 201 | SNR-1 with MID-1 | day 1 |
| **B — early independent** | **KAN-189** | SNR-2 or MID-2 | **day 1** — needs nothing from KAN-188 |
| **C — after W2** | KAN-195 (backfill), KAN-199 (bands) | MID-2 | after KAN-194 / after KAN-190 |
| **D — after W3 head** | KAN-197, then KAN-198, then KAN-192 | SNR-2 | after KAN-196 |
| **E — tail** | KAN-202 | MID-2 | after KAN-194, any time |
| **F — DevOps, continuous** | T-190-1 (btree_gist), T-193-8 (logging + runbook), T-200-8 (equity telemetry), CI updates | DEVOPS | day 1 |

**Total effort: 63–79 dev-days** (point estimate 93.0 task-days across 15 stories, discounted for the parallel
tracks' shared context and inflated for the two Medium-confidence stories). With **2 SNR + 2 MID + 0.3 DEVOPS**
that is **≈9–11 calendar weeks** including ARCH review and a regression pass per story. **Confidence
Medium-High** — the uncertainty is concentrated in KAN-191 (the mapping screen, R-2) and KAN-200 (the engine,
R-12), not in the CRUD.

**Estimate by story, for the plan:**

| Story | Est (d) | Conf | Where the uncertainty is |
|---|---|---|---|
| KAN-188 | 7.0 | Medium | The V2 backfill and the 330-cell proof, not the resolver change |
| KAN-189 | 4.5 | **High** | Small, bounded, one convention |
| KAN-190 | 6.0 | High | Straight CRUD over a well-specified model |
| KAN-191 | 8.0 | **Medium** | The mapping screen is a product in itself (R-2) |
| KAN-192 | 4.5 | High | — |
| KAN-193 | 7.0 | Medium-High | The trigger, the constraints and the money boundary |
| KAN-194 | 7.5 | Medium | 120-cell negative-visibility matrix; CFL-42-12 unresolved |
| KAN-195 | 6.0 | Medium | Soft dependency on EP35-S2 (R-9) |
| KAN-196 | 7.5 | Medium-High | The chain-satisfiability check and the modal-weight constraint |
| KAN-197 | 5.0 | High | Rides KAN-196's machinery |
| KAN-198 | 4.5 | Medium-High | Blast radius across EP27/EP38, not the guard itself |
| KAN-199 | 5.5 | High | — |
| KAN-200 | 8.5 | **Medium** | Arithmetic correctness; blocked on KAN-168 |
| KAN-201 | 7.5 | Medium | The bell is where three defects already lived |
| KAN-202 | 4.0 | High | — |
| **Total** | **93.0 task-days → 63–79 dev-days delivered** | **Medium-High** | |

---

## 10. Registers

### 10.1 Deferred designs — recorded so adding them later is additive, not a rewrite

| Item | Shape, so nobody re-designs it | Trigger to build |
|---|---|---|
| **FX rates** (§3.5) | `fx_rates(id, company_id, from_currency, to_currency, rate NUMERIC(18,8), effective_from DATE, effective_to DATE, created_by, reason)` + a half-open exclusion constraint. `pay_equity_service.assign_locations` relaxes its refusal to *"refuse unless a current rate exists for every currency in the market"*. **Purely additive** — no existing column changes meaning. | OQ-6 answered "yes", or a tenant merges currencies |
| **Divergent pay effective date** (D4d, Later) | `org_change_compensation_proposals.pay_effective_date DATE NULL`, falling back to `org_change_requests.effective_date`. **No change of meaning** to the existing column — which is exactly why the request-level date is defined as "the placement boundary" and not "the date" (ADR-020c). | A tenant needs pay and placement on different days |
| **Scheduled periodic equity re-evaluation** | `evaluate_company()` already exists and is idempotent; a `flask equity run-due` CLI command plus whatever scheduler KAN-163 eventually provides. **No engine change.** | KAN-163 lands |
| **Total compensation** (OQ-5) | A `compensation_components` child of `employee_compensation` (`kind`, `amount`, `currency`, `is_guaranteed`), with `annual_base_fte` unchanged as the base-only comparison value and a second `annual_total_fte` for a separate check. **Retrofitting this is a rewrite of KAN-193 and KAN-200 if it arrives after they ship** — which is why OQ-5 is High cost if answered late. | OQ-5 answered "yes" |
| **A read-only company-wide compensation auditor** (CFL-42-12) | A fourth code `compensation_all`, or a `scope` column on `role_feature_access`. **Recommend against in this cycle.** | A tenant asks |
| **Level title in the search index** (TD-18) | Extend `trg_employee_search` to concatenate the current level title, and reindex. | A user complains that searching the canonical job title fails |

### 10.2 Technical Debt Register — additions to `EP38_TECHNICAL_DESIGN.md` §11.1 (TD-1 … TD-15)

| ID | Debt | Source | Planned in | Sev |
|---|---|---|---|---|
| **TD-16** | `numeric(14,2)` loses a mil on three-decimal currencies (KWD, BHD, TND, OMR). No target tenant uses one. | ADR-014(b) | Widen to `(16,3)` if a Gulf tenant appears — one reversible migration | **P4** |
| **TD-17** | `company_features.enabled_for_hr` survives KAN-188 with no consumer. The column is the `CLAUDE.md`-forbidden pattern still physically present. | ADR-016(e) | Follow-on story (remove readers) then migration `16` (drop column) | **P2** |
| **TD-18** | `employee_search_index` / `trg_employee_search` index the *working* title while the *level* title is canonical. Searching a canonical job title can miss. | ADR-017(d), S12 | Follow-on with a reindex | **P3** |
| **TD-19** | `helpers.direct_report_ids` / `is_direct_report` are not company-scoped at their other call sites; EP42 always passes `company_id`, the rest do not. | V8, `app/helpers.py:141-158` | Sweep in the S5 hardening pass | **P2** |
| **TD-20** | `app/db.py::serialize()` floats **every** `Decimal` on every read. EP42 routes around it; `survey_benchmarks.usage_pct`, `employee_skills.years_of_experience` and `dashboard_metric_snapshots.average_rating` are still floated. | V3, `app/db.py:134-142` | A `to_dict(decimals='str')` option + a sweep — **not** EP42 | **P3** |
| **TD-21** | `employee_job_assignments.step_no <= job_levels.steps_count` is service-enforced only; direct SQL can violate it. | §3.2 | Trigger if it is ever violated in practice | **P4** |
| **TD-22** | `employee_org_assignments` and `manager_relationships` still lack `company_id`, an `is_current` uniqueness guarantee and a non-overlap constraint — the guarantees EP42's tables get. After KAN-189 the *dates* are right; the *constraints* are still absent. | V6, V9; §3.1 | A follow-on hardening story; ADR-020's convention makes it a drop-in `EXCLUDE` | **P2** |
| **TD-23** | The org-change engine wrote **no** audit rows before KAN-198. Approvals and applies from EP27/EP38 are unaudited history. | V7 | Backfill is impossible; KAN-198 starts the trail. State it in the release notes | **P3** |
| **TD-24** | `pay_equity_evaluations` rows accumulate with no purge, like `audit_log` (TD-14). One row per pay write per tenant. | ADR-023(b) | The same purge job TD-14 needs | **P4** |

### 10.3 Conflict log — `CFL-42-n`, continuing the SPM's §7.3

| ID | Conflict | Sev | Evidence | Resolution |
|---|---|---|---|---|
| **CFL-42-1** | *(SPM)* Tenant switch not in the central resolver. | High | `app/auth.py:38-95` | **Resolved — ADR-016.** AND applied in `_load_feature_access`; `portal_features.default_enabled`; retro-fit in the same story. |
| **CFL-42-2** | *(SPM)* `ACTIONS` frozen; no money guard. | High | `audit_service.py:73-98` | **Resolved — ADR-019.** Fourteen new actions, token-matched denylist **plus a per-action closed allowlist**, which is the stronger control. My file, my edit. |
| **CFL-42-4** | *(SPM)* Two job titles, unclear precedence. | Medium | `schema.sql:411,1588,1861` | **Resolved — ADR-017(d).** Per-surface table. `employees.job_title`, its index and its trigger untouched in EP42; TD-18 records the search consequence. |
| **CFL-42-5** | *(SPM)* Segregation of duties changes `decide()` for EP27/EP38. | High | `org_change_service.py:222-312` | **Resolved — ADR-022**, subject to OQ-9. **Includes a narrowing of SYSTEM_ADMIN, which I am flagging explicitly rather than assuming.** |
| **CFL-42-8 — NEW** | **KAN-190 gates the ladder on `compensation`, but the level *title* becomes the job title shown in the directory to every employee.** A `compensation` read gate blanks the directory for everyone. | **High** | SPM §5.2 KAN-190 vs D3.1 | **Resolved — ADR-017(e).** Ladder **reads** gated `employee_profiles`; **writes** and the configurator gated `compensation:w`. **The BA needs this in the criteria.** |
| **CFL-42-9 — NEW** | **A compa-ratio is invertible into a salary** when a band exists, so `pay_equity:r` alone can reconstruct pay that D5 withholds. D5.7's surface list does not cover inference. | **High** | ADR-018(e); D5.2 gives HR_ADMIN both, but a tenant may grant `pay_equity` alone | **Resolved — ADR-018(e), T-201-3.** Numeric `measured_value` renders only to holders of **both** codes; otherwise a band label. Group gap percentages are safe (median-to-median). |
| **CFL-42-10 — NEW** | **D1 says thresholds are PORTAL_ADMIN-only; D5.2's matrix gives HR_ADMIN "Configure levels / bands / thresholds".** Direct contradiction, and the obvious implementation of D1 is the forbidden role check. | **Medium** | SPM §4.1.1 vs §4.5.2 | **Resolved — §6.3.** Thresholds, coverage gate and pay-market definition gated `company_settings:w` (PORTAL_ADMIN-only by seeded default, no role check). Levels and bands stay `compensation:w`. **SPM to confirm.** |
| **CFL-42-11 — NEW** | **The SPM's dependency table makes KAN-199 a hard dependency of KAN-200**, but D1 specifies a group-median fallback and KAN-199 is Should · P2. A hard dependency puts a large configuration exercise on the critical path for no correctness gain. | **Medium** | SPM §5.5 KAN-200 "Depends on … KAN-199" vs §4.1.1 | **Resolved — soft dependency.** KAN-200 ships and is correct without bands; where a band exists it becomes the better basis. Shortens the critical path by 5.5 days. **SPM to update the table in Wave 3.** |
| **CFL-42-12 — NEW** | **The two-table matrix cannot express "read company-wide but not write".** `_has_company_wide_scope` derives from `compensation:w`, so a read-only auditor or works-council representative — a case D5.4 explicitly names as real — has no clean grant. | **Medium** | ADR-018(c); D5.4 | **Open — routed to the SPM.** Interim: `r`-only means "your direct reports", which serves the only case in the seeded matrix. Fix shapes in §10.1. **This is a limitation of the access model, not of EP42, and it should be recorded as such.** |
| **CFL-42-13 — NEW** | **The SPM's DEP-1 lists KAN-155 as "Planned, S2 enabler". It is ✅ Done.** Anyone sequencing EP42 behind it waits for nothing. | Low | `app/db.py:57-99`; BACKLOG.md:505 | **Resolved — corrected here.** DEP-1 is satisfied. **DEP-4 (KAN-168) is the one that is genuinely not started and it blocks KAN-200.** |

*(CFL-42-3, -6, -7 are the BA's and the SPM's and are not mine to resolve. CFL-4 — the EP38 conflict — is
**closed by ADR-020**; `docs/ARCHITECTURE_REVIEW.md` must say so in T-189-8's commit.)*

### 10.4 Technical Risk Register — additions to `EP38_TECHNICAL_DESIGN.md` §11.2 (TR-1 … TR-14)

| ID | Risk | Prob | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| **TR-15** | **KAN-188 blacks out both populated tenants.** The 14 FALSE `company_features` rows become live the moment the resolver honours them, and CI is green throughout because `seed_rbac.sql` has no such rows. | **High** if the SPM's stated default is implemented literally | **Critical** | ADR-016(c) repair-then-materialise; **T-188-6's 330-cell before/after proof is the gate**; T-188-2 captures the fixture *before* any code changes | ARCH + SNR |
| **TR-16** | **A salary is written as a `float`** through `to_dict()`, `serialize()` or a JSON body, and cent-level errors appear in comparisons and exports. | **Medium** — it is the default path | **High** | ADR-014(f): `money_out`/`money_in`, `money_in` rejects `float`, grep-assert that `compensation_service` never calls `to_dict`, JSON `amount` is a string | SNR |
| **TR-17** | **An amount reaches `audit_log`** by an inventively-named diff key. Append-only, permanently retained, wrong audience. | Medium | **Critical** | ADR-019's **per-action closed allowlist** — the control that does not depend on guessing the name; the token denylist as backstop | ARCH |
| **TR-18** | **KAN-200's arithmetic is wrong in a way the tests do not catch**, because KAN-168 has not landed and the fixtures are mocked. | **High** while KAN-168 is outstanding | **High** | **Hard blocker, §11.** UAT writes hand-computed fixtures; T-200-3 runs against a real DB or the story does not start | ARCH → SPM |
| **TR-19** | **A pay amount is inferred rather than read** — compa-ratio × midpoint, precise percentage change, or a group of two. | Medium | **High** | §8.4's three resolutions; the group minimums are floored at 2 **in the database** | ARCH |
| **TR-20** | **The four-eyes guard blocks a legitimate approval** in a tenant whose two-level chain is genuinely satisfiable by one person, and HR is stuck with no in-app remedy. | Medium | Medium | T-198-4 shows the overlap **at configuration time**, which is the remedy; the error names the level and the fix | SNR |
| **TR-21** | **A promotion applies its level but not its pay** (or the reverse) because someone splits the apply out of the single transaction to "keep the function short". | Medium | **Critical** | §7.2 rule 6 as a review gate; T-197-3's induced-failure test; `transaction()` raises on nesting so the shortcut fails loudly | ARCH |
| **TR-22** | **`btree_gist` is missing in some environment** and migration `11` fails, or worse, someone removes the exclusion constraints to make it apply. | Medium | **High** | T-190-1 puts it in `schema.sql`, CI, the README and the `CLAUDE.md` recipe. **Removing an exclusion constraint to make a migration pass is a returned PR** | DEVOPS + ARCH |
| **TR-23** | **KAN-195 forks a second importer** because EP35-S2 has not landed (SPM R-9). | Medium | Medium | T-195-2 written against the EP35-S2 contract; grep-assert that one importer exists | MID |
| **TR-24** | **The mapping backfill (KAN-191) never finishes** and the epic delivers a ladder nobody is on, so equity never evaluates a single group. | **High** | **High** | The coverage meter is the instrument (T-191-7); the release notes say the effort is the tenant's (T-195-8); the SPM's A-4 | SPM + MID |
| **TR-25** | **A rollback after tenant data lands destroys pay history.** The `_down` migrations are clean only before first use. | Low | **Critical** | T-193-8's runbook caveat; ARCH-reviewed; stated **before** an incident | DEVOPS |
| **TR-26** | **The equity engine's failure is silent** — a `FAILED` evaluation row nobody reads, so a group is never evaluated and HR believes it is clean. | Medium | **High** | T-200-8's telemetry; the queue's empty state is the **coverage meter**, never "no findings ✓" (T-201-2, D7.4) | DEVOPS + MID |

### 10.5 ADRs added by this design

| ADR | Decision | Affects |
|---|---|---|
| **ADR-014** | Money is `NUMERIC(14,2)` + `CHAR(3)`; `annual_base_fte` computed at write and stored; money crosses the wire as a **decimal string**, never through `to_dict()` | KAN-193, 195, 199, 200 |
| **ADR-015** | `employee_compensation` — append-only for value (partial-immutability trigger), half-open effective dating, GiST non-overlap, void not delete, `retention_class='EMPLOYMENT'` | KAN-193, 202 |
| **ADR-016** | Tenant switch AND role grant in one resolver; `portal_features.default_enabled`; **repair-then-materialise** backfill; two ad hoc consumers deleted; `enabled_for_hr` removal path | KAN-188 · **every feature in the product** |
| **ADR-017** | Job architecture — family/level/step; ordinal immutable once assigned; steps are a count not rows; per-surface title precedence; **ladder reads on `employee_profiles`, writes on `compensation:w`** | KAN-190, 191, 192 |
| **ADR-018** | Row-scoped salary visibility; the `Scope` object; **why it is not the forbidden sub-flag**, in code; the invertibility rule | KAN-194, 200, 201 |
| **ADR-019** | Money never in `audit_log` — token denylist **plus a per-action closed diff-key allowlist**; fourteen new `ACTIONS`; retention classes | KAN-193 … 202 |
| **ADR-020** | **Half-open `[from, to)` intervals project-wide**; `effective_date` threaded through `create_request`/`_apply_change`; **CFL-4 closed with no history rewrite** | KAN-189 · **unblocks KAN-185** |
| **ADR-021** | Compensation rides the org-change request; **money in a one-to-one child table**; `request_type`; chain per type with fallback; the partial proposal made unrepresentable | KAN-196, 197 |
| **ADR-022** | Four-eyes in `decide()` — hard for money/level, warn-and-audit for placement, **not bypassable by SYSTEM_ADMIN**; overlap shown at configuration time | KAN-198 · EP27 · EP38 |
| **ADR-023** | Pay-equity computation: event-driven per group **after commit**, on-demand company run under an advisory lock; materialised findings; the cost model | KAN-200, 201 |

---

## 11. Technical-readiness verdict

> **⚠️ AMENDED by §12.10.** The verdict is re-issued against A1. RAG stays **🟡 Amber**; the blocker set
> changes (B-1 KAN-168 is unchanged and now SPM-owned at P0; B-3 is **closed** — the SPM ratified ADR-016);
> and one new story, **KAN-207**, joins the not-technically-ready list for a reason worth reading.


### 11.1 Is EP42 buildable as scoped?

**Yes — all fifteen stories are buildable at 63–79 dev-days, conditional on three things clearing.** RAG
**🟡 Amber**, and Amber because of the conditions and the open questions, not because of unknowns in the
design. I have **no unresolved architectural unknowns**. **Confidence Medium-High.**

The epic is harder than EP38 by roughly a factor of three and it is honest to say so: 14 tables against 5,
26 endpoints against 13, a new computation engine, and two changes to shared security boundaries
(`app/auth.py`, `org_change_service.decide()`) that alter behaviour for features EP42 does not own. What
makes it tractable is that the engines it needs already exist and are good: `transaction()` landed and is
correct, `audit_service` is exactly the right shape and needs extending rather than rethinking,
`notification_service` already has the `related_type` retirement mechanism DEF-003 forced, and
`org_change_service` already carries sequential approval, the no-self-initiation rule and the D-185-1 overlay.
**EP42 is mostly composition. The genuinely new construction is the pay-equity engine and the money
boundary.**

### 11.2 The riskiest part — and it is not the equity engine

**It is KAN-188, on day one, before anything interesting has been built.** Fourteen `company_features` rows
sitting at FALSE for features nothing consults, in both populated tenants, with no rows at all in
`seed_rbac.sql` — so the change that turns the switch on looks correct locally, passes every test in CI, and
takes the entire product away from every non-SYSTEM_ADMIN user in Acme and Telia the moment it reaches a
database that has those rows. It is a Critical availability defect wearing a feature-flag costume, and it is
exactly the class a reviewer skimming a green suite would wave through. That is why T-188-2 captures the
before-matrix as a fixture **before** any code is written and T-188-6 is the acceptance criterion.

**Second-riskiest:** a salary leaving through a surface nobody enumerated. Mitigated by design rather than by
diligence wherever I could manage it — the money is in a child table so existing queries cannot return it
(ADR-021a); the audit guard is a closed allowlist so it does not depend on guessing key names (ADR-019b); the
group minimums are floored in the database so a "group median" can never be one person's pay (§8.4). The
residue is the inference surface (CFL-42-9), which is new and which the SPM's D5 does not cover.

**Third:** the arithmetic in KAN-200 being confidently wrong. There is no design fix for that. There is
KAN-168 and hand-computed fixtures written by somebody other than the engine's author, and I will not accept
the story without both.

### 11.3 Blockers

| # | Blocker | Owner | Why blocking |
|---|---|---|---|
| **B-1** | **KAN-168 — the real-DB integration tier — is ⬜ not started** (BACKLOG.md:548). | SPM / DevOps (EP32, S2) | **KAN-200 cannot be certified without it.** Group formation, `percentile_cont`, coverage arithmetic and every exclusion constraint in §3 are SQL semantics. A DB-mocked suite proves we called `psycopg2`. `tests/test_audit_service.py` and `tests/test_transactions.py` already run a partial real-Postgres tier — the pattern exists and needs generalising, not inventing. **P0 for W4.** |
| **B-2** | **Reconcile this design against the BA's acceptance criteria, UX's specs and UAT's approach.** All four Wave-2 artifacts were written concurrently. **CFL-42-8, -9, -10 and -11 each change what the BA must write.** | ARCH + BA + UX + UAT | Definition of Ready (Charter §4). **P0 before any code.** |
| **B-3** | **SPM acknowledgement of the ADR-016(c) correction** (V2 / TR-15). | ARCH → SPM | D6 requirement 2 as written produces the outage. The story cannot start against the stated rule. **P0.** |
| **B-4** | **OQ-9 ratification** for KAN-198, **including the SYSTEM_ADMIN narrowing** (ADR-022b), which the SPM's D4h does not explicitly cover. | SPM → product owner | It is a governance policy and it changes EP27 and EP38 behaviour. **P1, blocks KAN-198 only.** |

### 11.4 Open questions I need answered, and by when

| # | Question | Owner | Needed by | Default I am building against |
|---|---|---|---|---|
| **T-OQ-1** | **CFL-42-12** — how should "read company-wide, write nothing" be expressed? A fourth code, a scope column, or accept the gap? | SPM | KAN-194 seed | Accept the gap; `r`-only means "your direct reports" |
| **T-OQ-2** | **CFL-42-10** — confirm thresholds on `company_settings:w` rather than `compensation:w`. | SPM | KAN-199 | As designed in §6.3 |
| **T-OQ-3** | **CFL-42-11** — confirm KAN-199 is a soft dependency of KAN-200. | SPM | W4 planning | Soft |
| **T-OQ-4** | **`employees.gender`** is `MALE/FEMALE/OTHER` and Check B compares two of the three. What happens to `OTHER` and to NULL — excluded and counted, or does the check not run? This is a **DPO** question about the lawful basis and purpose limitation as much as an arithmetic one (SPM §9, DEP-9). | BA + DPO | KAN-200 | `OTHER`/NULL are **excluded from the gap medians, counted in the exclusion count, and named on screen**. The check still runs if `n_male >= 2` and `n_female >= 2`. |
| **T-OQ-5** | **CFL-42-3** — the erasure enumeration must name compensation before KAN-193 fixes `retention_class`. | BA + DPO | KAN-193 | `EMPLOYMENT`, nothing purged until legal rules |
| **T-OQ-6** | Does a **non-ACTIVE** employee's compensation record stay current, or close at `exit_date`? It changes coverage arithmetic and the equity population. | BA | KAN-193 | Close at `exit_date`; excluded from equity by the `employment_status = 'ACTIVE'` filter already in the group query |

### 11.5 Recommended priorities

| Priority | Item |
|---|---|
| **P0** | **B-3** SPM acknowledgement of the ADR-016(c) correction · **B-2** reconcile with BA/UX/UAT · **T-188-2/6** the before/after matrix · **B-1** KAN-168 scheduled ahead of W4 |
| **P1** | KAN-188 → KAN-190 → KAN-191 → KAN-193 → KAN-194 (the critical path to the minimum shippable slice) · **T-193-3** the `audit_service` money guard · **T-194-6** the negative-visibility suite · **T-196-5** `TestApplyNeverZeroesASalary` · **T-190-1** `btree_gist` in every environment · **B-4** OQ-9 |
| **P2** | KAN-189 (parallel, unblocks KAN-185 today) · KAN-195 · KAN-196 · KAN-197 · KAN-198 · TD-17 `enabled_for_hr` removal · TD-19 `direct_report_ids` scoping · TD-22 constraints on the two legacy effective-dated tables |
| **P3** | KAN-199 · KAN-200 · KAN-201 · KAN-192 · TD-18 search index · TD-20 the global `Decimal→float` sweep · TD-23 unaudited org-change history in the release notes |
| **P4** | KAN-202 (blocked on DEP-8) · TD-16 three-decimal currencies · TD-21 the `step_no` trigger · TD-24 evaluation-row purge |

### 11.6 Stories I will **not** call technically ready

| Story | Verdict | What is missing |
|---|---|---|
| **KAN-200** | **NOT READY — and it is the only P0-grade "not ready" in the epic.** | **B-1 (KAN-168).** Plus T-OQ-4, which is a DPO question about the engine's *input*, not its output. Building the engine against mocks and validating it later is the sequence that produces R-12: an engine whose fixtures were written by its author. |
| **KAN-202** | **NOT READY** | **DEP-8** — the SPM's Wave-3 decision on the audit read surface. KAN-202 does not block on it technically (it is a *compensation* surface by design), but shipping a timeline before that decision means designing the two in ignorance of each other, which is how you end up with two viewers. |
| **KAN-192** | **Buildable, not ready** | OQ-1. The default is safe and I would build against it, but if the answer comes back "automatic", KAN-192 is a different story and D3.4's four arguments have to be re-run with the product owner. |
| **KAN-194** | **Buildable with a named gap** | CFL-42-12 is unresolved. It does not stop the build; it means the seeded matrix has a case it cannot express, and the SPM should know that before the defaults are frozen. |
| Everything else | **Technically ready once B-2 and B-3 clear** | BA criteria and UX specs, which are the other half of Wave 2 |

### 11.7 My verdict

**Proceed to design sign-off. Hold code start until B-2 and B-3 clear; hold W4 until B-1 clears.** The design
is complete enough to build against and I have no unresolved architectural unknowns. What I do not have is the
BA's acceptance criteria or UX's specs, and four of my conflict-log entries (CFL-42-8, -9, -10, -11) change
what both of them must write — so a reconciliation pass is not a formality here.

**Three things I want the SPM to take away.**

1. **KAN-188 is not a small platform story.** It is the highest-consequence change in EP42 and its risk is
   entirely in existing data that nobody has looked at since it was written. The sequencing decision to put
   it first is right; the estimate needs to include the proof, not just the change.
2. **I am narrowing SYSTEM_ADMIN in one place** — four-eyes on money-bearing approvals — and that deserves an
   explicit yes rather than my inference. Under demo auth, a control SYSTEM_ADMIN can bypass is a control
   that is one login tile away from not existing.
3. **The visibility model is a correctness control, not a security control, until KAN-148 lands.** I will
   certify that the right rows reach the right roles. I will not certify that the roles are who they say they
   are, because `app/routes/auth.py` does not check a credential. That distinction goes in the demo script
   and the release notes, in those words.

**One recommendation on sequencing.** KAN-189 has no dependency on KAN-188 and unblocks `AC-185-07` on a story
that is stuck **today**. Start it on day one on a second track. It is 4.5 days that closes an EP38 blocker,
settles a project-wide date convention while it is still free to settle (V6 — `effective_to` is read
nowhere), and gives the epic a visible win before the hard part starts. **Confidence High.**

*Everything above obeys `../../CLAUDE.md`. No task is done until `python -m pytest -q` and the regression flow
test pass with 0 failures, and no schema, guard or invariant change is approvable without the corresponding
documentation updated in the same commit.*

---
---

# 12. Amendment A1 — the technical design, re-cut

> **Wave 4.** Input: `EP42_OWNER_ANSWERS_A1.md` (the product owner, verbatim — authoritative) and
> `EP42_SPM_SCOPE_AND_DECISIONS.md` **§12** (the Wave 3 reconciliation) and **§14** (the A1 re-rulings).
> Precedence: **A1 › SPM §14 › SPM §12 › this §12 › §1–§11 above.**
>
> **This is an amendment, not a rewrite.** §1–§11 were sound; A1 changes the *reference value*, adds two
> objects and a feature code, and Wave 3 sent me four additions. Where a section above is superseded it carries
> an inline marker pointing here, and the original text is left standing so the reasoning survives.

## 12.0 What actually changed for engineering, and what did not

**Three things changed. Everything else in §1–§11 stands.**

| # | Change | Where it lands | Net effect on the build |
|---|---|---|---|
| 1 | **The pay-equity reference value is a configured step pay point, not a group median.** "5%" is the **increment between consecutive steps**, compounding. | **ADR-024 (new, §12.5)**; **ADR-023 re-cut (§12.6)**; new table `job_level_pay_points`; `pay_equity_findings` amended | **Simpler and cheaper.** No `percentile_cont`, no group windowing, no `n≥3`, no coverage gate for the primary check. The group machinery survives **for Check B only** |
| 2 | **A step is a described job, not a number.** Entry at `.0`; `step_count` = increments **above** entry; per level, no default. New objects: **step expectation**, **step roadmap**. New feature code **`job_architecture`**. | **ADR-017 amended (§12.4)**; **ADR-025 (new, §12.4.4)**; two new tables; four-place registration for a fourth code | **Larger.** W1 grows by two stories' worth of surface, and gains a shippable, employee-visible outcome with no money in it |
| 3 | **Wave 3 ratified ADR-016 and sent four additions.** | **§12.2** | Bounded. All four land inside stories that are already rewriting the code in question |

**What A1 explicitly did NOT change, restated so nobody re-opens it:** ADR-014 (money representation) ·
ADR-015's append-only, half-open, GiST-non-overlap shape · ADR-016 (ratified in full) · ADR-018 (row scoping
and the CC-2 boundary) · ADR-019's structural guarantee · ADR-020 (half-open intervals; CFL-4 closed) ·
ADR-021's child-table decision · ADR-022's four-eyes mechanism · ADR-023's *placement* (event-driven, after
commit, own transaction, advisory-locked) · the wave model · KAN-194 shipping with KAN-193 · W2 as the minimum
shippable slice.

**One honest note on my own Wave 2 work.** ADR-023 built a statistical engine because the brief said the
reference was a group median. A1 shows the reference was never statistical. **The parts of ADR-023 that
survive are the parts that were about *engineering* — where the computation runs, what transaction it runs
in, what happens when it fails — and the parts that died were the parts that were about *the product's
definition of the answer*.** That is the right split, and it is an argument for designing the mechanism
independently of the policy wherever the policy is still moving. I got that right by accident here; I would
rather record it as a lesson than as a win.

## 12.1 Re-verification — the new facts I checked before amending

| # | Finding | Evidence | Class |
|---|---|---|---|
| **V13** | **`employees.gender` is NULL for 100% of the seeded population**, and there is no admin collection path. Check B has literally nothing to run on today. The column exists with `CHECK (gender IN ('MALE','FEMALE','OTHER'))`. | `psql -d employee -At -c "select coalesce(gender,'NULL'), count(*) from employees group by 1"`; `database/schema.sql:404-429`; DEF-42-3 | **Known** |
| **V14** | **`app/routes/org_change.py:381` already gates the org-change workflow *configuration* page on `@require_feature_access('org_structure','w')`** while its runtime uses `org_change`. `org_structure` is seeded **HR_ADMIN r+w+d and PORTAL_ADMIN r+w+d**, `DEPARTMENT_HEAD` r, and **no manager role at all** (`scripts/setup_db.py:128-160`). This is the exact audience §14.3.1 wants for ladder configuration, and the precedent CFL-42-20 already relied on. | `app/routes/org_change.py:381,387,408`; `scripts/setup_db.py:123-160` | **Known** |
| **V15** | **`require_feature_access` denies with `flash()` + `redirect(url_for('dashboard'))`** — a **302 to HTML**, for JSON endpoints too (`app/auth.py:99-109`). Every "returns 403" criterion in EP42 *and* EP38 describes behaviour the decorator does not have. Confirms BA CFL-42-8. | `app/auth.py:99-109` | **Known** |
| **V16** | **PostgreSQL's `power(numeric, numeric)` is not documented as exact.** For a compounding pay point (`base × (1+i)^n`) computed in SQL, the last cent is not guaranteed reproducible across versions. `numeric` multiplication **is** exact. | PostgreSQL 16 docs, `numeric_power`; V11 (server 16.13) | **Known** — drives ADR-024(d) |
| **V17** | **`_can_initiate_for` (`app/routes/org_change.py:55-64`) never compares the initiator to the subject**, and `decide()` (`org_change_service.py:222-249`) never compares the decider to `req['employee_id']` or to `req['requested_by_user_id']`. An HR_ADMIN can raise and approve a position change for themselves today, on the seeded default chain. Independently found by the BA and UAT; I confirm it. | `app/routes/org_change.py:62-64`; `app/services/org_change_service.py:235-249` | **Known** — DEF-42-4 / DEF-42-5, KAN-203 |
| **V18** | **The seeded default chain is one level** (`_DEFAULT_STEPS`, a single `HR_ADMIN` step, `org_change_service.py:24-27`) and **no company has configured a workflow** — `select count(*) from org_change_workflows` → 0. So four-eyes as specified in ADR-022 would be a **silent no-op in every tenant today**: there is no second level to bind. Confirms BA CFL-42-11. | `org_change_service.py:24-27`; `psql -d employee -At -c "select count(*) from org_change_workflows"` | **Known** |

**V18 is the one that would have embarrassed us.** ADR-022 was correct, tested, and would have shipped doing
nothing. "The control exists" and "the control works" were two different statements and I only wrote the
first. The fix is CFL-42-11's — **≥2 independently satisfiable levels required at create for money-bearing
requests, plus a seeded two-level default chain** — and it is now T-198-7/8.

## 12.2 The four items Wave 3 sent back to me — actioned

### (a) ADR-016 gains `feature_access_for(user_id, company_id)` — the non-session resolver

**Ruling 4 / CFL-42-12.** ADR-021(e) requires a create-time check that *every* step of a chain can be
satisfied by at least one approver holding `compensation:r`. That is a question about **other people's**
access, and `_load_feature_access()` resolves only `session['roles']`. The BA was right that the primitive
does not exist; I was right that it does not block KAN-194. **It blocks KAN-196**, and KAN-188 is already
rewriting that exact query, so it goes there.

```python
# app/auth.py — new public function, added by KAN-188 (T-188-11)

def feature_access_for(user_id, company_id):
    """Resolved {feature_code: {r,w,d}} for ANOTHER user, in a named company.

    Same SQL as _load_feature_access() — the tenant switch AND the role grant,
    with COALESCE(cf.is_enabled, pf.default_enabled) — parameterised on a user id
    instead of the session. NOT cached on `g` per user; callers that need many
    users call feature_access_for_users().
    """

def feature_access_for_users(user_ids, company_id):
    """The same, for a set of users, in ONE query. This is the shape the chain
    check actually needs: resolve every candidate approver of every step at once,
    not N+1 per approver."""
```

**Three properties that are non-negotiable and must be enforced by test:**

1. **One implementation, three entry points.** `_load_feature_access()`, `feature_access_for()` and
   `feature_access_for_users()` share **one** SQL builder, `_feature_access_sql(scope)`. Two copies of a
   permission query is how a bypass arrives: someone fixes one and not the other. **T-188-12 asserts by module
   inspection that `company_features` and `role_feature_access` appear in exactly one SQL string in `app/`.**
2. **`SYSTEM_ADMIN` short-circuits identically.** A SYSTEM_ADMIN candidate approver resolves to full access,
   as in the session path (`auth.py:50-53`). Divergence here would make the chain check disagree with the
   decorator, which is the worst possible failure: a request refused at create for a chain that would in fact
   have worked, or accepted for one that would not.
3. **It is not a back door.** `feature_access_for()` **answers a question; it does not grant anything.** It is
   callable only from the service layer, never from a route as an authorisation decision about the caller —
   the caller is always authorised by the decorator. **T-188-12 grep-asserts it is never called from
   `app/routes/`.**

**Cost.** `feature_access_for_users(ids, company_id)` is one query with `u.id = ANY(%s)`, hitting
`idx_co_feat_lookup` and the role joins already in the plan. For a 2–4 step chain with a dozen candidate
approvers: one query, sub-millisecond. The N+1 shape (one call per approver) would be 12 queries per request
creation and is **forbidden** — `feature_access_for()` singular exists for the one-user case only.

### (b) The repair migration states its reversibility **before** it runs

**Ruling: the migration is reversible, and I am making it reversible rather than declaring it one-way.**
Migration `10` captures the prior state into a table before it changes anything:

```sql
-- 10_tenant_feature_switch.sql — BEFORE the repair UPDATE.
-- The _down migration is worthless without this: it would have no way to know
-- which rows were FALSE on purpose (reports, skills_intelligence) and which were
-- FALSE because nothing read them. Capturing 18 rows costs nothing; NOT capturing
-- them means a rollback re-blacks-out both tenants, which is the same incident
-- twice — and the second time it is our fault rather than an inherited one.
CREATE TABLE IF NOT EXISTS company_features_pre_kan188 (
    company_id UUID        NOT NULL,
    feature_id UUID        NOT NULL,
    is_enabled BOOLEAN     NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (company_id, feature_id)
);
INSERT INTO company_features_pre_kan188 (company_id, feature_id, is_enabled)
SELECT company_id, feature_id, is_enabled FROM company_features
ON CONFLICT (company_id, feature_id) DO NOTHING;   -- idempotent: first run wins
```

`10_tenant_feature_switch_down.sql` then restores from it and deletes rows that did not exist before:

```sql
UPDATE company_features cf SET is_enabled = pre.is_enabled
  FROM company_features_pre_kan188 pre
 WHERE pre.company_id = cf.company_id AND pre.feature_id = cf.feature_id;
DELETE FROM company_features cf
 WHERE NOT EXISTS (SELECT 1 FROM company_features_pre_kan188 pre
                    WHERE pre.company_id = cf.company_id AND pre.feature_id = cf.feature_id);
ALTER TABLE portal_features DROP COLUMN IF EXISTS default_enabled;
-- The capture table is deliberately NOT dropped. It is 18 rows of forensic value
-- and dropping it would make a second down-then-up cycle lossy.
```

**`ON CONFLICT DO NOTHING` on the capture is load-bearing:** re-running the up migration after the repair must
not overwrite the capture with the repaired values. First run wins, and the first run is the only true one.

**T-188-13** proves the round trip: apply → assert the 330-cell matrix is unchanged → reverse → assert the 18
rows are byte-identical to the fixture captured in T-188-2 → re-apply → assert unchanged again. **The runbook
records that the capture table must exist before the repair runs**, and that a rollback after `portal_features`
rows for EP42 have been added is a partial rollback, not a full one (§12.9 TD-25).

### (c) ADR-022 gains a cancel-not-approve remedy — the condition on the SYSTEM_ADMIN narrowing

**Ruling 13.** The SPM said yes to four-eyes binding SYSTEM_ADMIN, conditional on a genuinely stuck chain
having a visible, audited administrative remedy. **The remedy exists today and needs one change.**

`org_change_service.cancel()` (`:393-410`) already refuses anyone who is neither the requester nor an
HR_ADMIN/PORTAL_ADMIN/SYSTEM_ADMIN, is `PENDING`-only, **applies nothing**, and retires the call to action.
It is the right primitive. Three amendments:

1. **`cancel()` writes an audit row.** It currently writes none (V7). New action
   **`ORG_CHANGE_CANCELLED_BY_ADMIN`**, `retention_class='SECURITY'`, mandatory reason, inside a
   `transaction()` with the status update. A cancel that leaves no record is not a remedy, it is a disappearance.
2. **`cancel()` gains a mandatory `reason`** — it takes none today. An unblocking act on a money-bearing
   request with no recorded reason is exactly the thing the four-eyes rule exists to prevent, wearing a
   different hat.
3. **The refusal message from the four-eyes guard names the remedy.** Not *"you already decided level 1"* but
   *"you already decided level 1 of this request; a change that moves pay or job level needs two different
   approvers. Cancel this request, fix the approval chain (Settings → Position change approvals), and re-raise
   it."* A control that blocks without saying what to do instead is how a tenant ends up editing the database.

**Cancel is not approve, and the difference is the whole point:** cancel applies nothing, so the outcome of a
stuck chain is *no change*, never an unapproved change. **`decide()` gains no SYSTEM_ADMIN escape of any kind.**
Tasked as **T-198-9**.

### (d) `PROMOTION` → `LEVEL_CHANGE` throughout — ADR-019 and ADR-021 updated

**CFL-42-25.** The SPM rejected both the derived-display-label and the fourth-enum-value options and ruled a
rename plus a stored direction. **I agree, and the deciding argument is mine to endorse rather than re-argue:
an audit action that says `PROMOTION_APPLIED` for a demotion is a lie in the durable record, and no display
layer can fix a durable record.** Changes:

| Where | Was | Now |
|---|---|---|
| `org_change_requests.request_type` | `'TRANSFER' \| 'PROMOTION' \| 'COMPENSATION_REVIEW'` | `'TRANSFER' \| **'LEVEL_CHANGE'** \| 'COMPENSATION_REVIEW'` |
| `org_change_requests` | — | **+ `direction VARCHAR(8) NULL CHECK (direction IN ('UP','DOWN','LATERAL'))`**, `NOT NULL` when `request_type='LEVEL_CHANGE'`, derived server-side by `_infer_request_type()` from the ordinal comparison, **never** from client input |
| `audit_service.ACTIONS` | `PROMOTION_APPLIED` | **`LEVEL_CHANGE_APPLIED`**, with `direction` on the allowlist |
| `_ALLOWED_DIFF_KEYS` | `PROMOTION_APPLIED: {job_level_id, step_no, effective_date, has_pay_change, direction, pct_change_band}` | same set, keyed on `LEVEL_CHANGE_APPLIED` |
| User-facing copy | "Promotion" | **"Promotion" when `direction = 'UP'`**, "Level change" / "Level change (down)" otherwise. R4 asked for a promotion flow, not for an enum literal |

**A cross-family move is `LATERAL`**, not `UP` or `DOWN` — ordinals are only comparable within a family
(ADR-017a), so comparing a Level 3 Engineer to a Level 2 Accountant is meaningless and must not be attempted.
`_infer_request_type()` returns `('LEVEL_CHANGE', 'LATERAL')` whenever the family changes, regardless of the
ordinals. This is one `if` and it is the sort of thing that gets written the wrong way once.

`_infer_request_type()` remains the **only** place inference happens (ADR-021b), and the direction is stored
so that a later ladder re-ordering cannot retroactively change what a historical request meant. That is the
same reasoning as ADR-017(b)'s ordinal immutability, and the two guarantees back each other up.

### (e) Also landing in KAN-188 — CFL-42-8, the 302-instead-of-403 defect

Not one of the four, but it is in the same file and the same story and I am not going to make it a separate
pass. **V15: `require_feature_access` denies with `flash()` + a 302 redirect to an HTML dashboard, for JSON
endpoints too** (`app/auth.py:99-109`). Every "returns 403" criterion in EP42 — and in EP38 — describes
behaviour that does not exist, and a `fetch()` that receives a 302 to HTML renders whatever the caller's error
path does with an HTML body. That is the DEF-002 shape: a failure that displays as something else.

**Fix: content negotiation, not a second decorator.**

```python
def _deny(feature_code, action):
    wants_json = (request.path.startswith('/api/')
                  or request.accept_mimetypes.best == 'application/json'
                  or request.is_json)
    if wants_json:
        return jsonify({'error': 'forbidden', 'feature': feature_code,
                        'action': action}), 403
    flash('You do not have access to that page.', 'error')
    return redirect(url_for('dashboard'))
```

`request.path.startswith('/api/')` is first because it is the deterministic half — every JSON endpoint in this
codebase is under `/api/`, and content negotiation on `Accept` alone is at the mercy of the caller. **The
tenant-disabled branch (ADR-016d) returns `feature_disabled.html` for HTML and a `403` with
`{'error': 'feature_disabled'}` for JSON** — a distinguishable code, because "you may not" and "your company
has not bought this" are different things a client may want to render differently. **T-188-14**, and it needs
a full regression pass because it changes the response of every gated route on the deny path.

## 12.3 Amended tables — `is_current` withdrawn, annualisation constants re-homed

### 12.3.1 `is_current` is computed, never stored — CFL-42-16

**Ruling ratified, and it makes my own design simpler.** The stored boolean is **withdrawn from every EP42
effective-dated table**: `employee_compensation`, `employee_job_assignments`, `salary_bands` and the new
`job_level_pay_points`.

**Why it is strictly better, not merely compliant:**

1. **The GiST exclusion constraint already delivers the guarantee.** `excl_ec_no_overlap` guarantees no two
   active periods overlap **on any date**. At most one row is therefore in force today — which is exactly what
   `uq_ec_one_current` was buying, for one date only. The partial unique index was the weaker of the two and
   I was carrying both.
2. **A stored flag on a future-dated row is wrong until its date, and there is nothing to flip it.** KAN-163
   does not exist. A future-dated compensation record with `is_current = TRUE` is a lie for up to 180 days; with
   `is_current = FALSE` it never becomes true. Both are wrong. **A computed predicate has no such state.**
3. **It removes a class of bug rather than a column.** Two sources of truth for "current" — the flag and the
   dates — can disagree, and the failure is silent.

**The replacement predicate, used everywhere and defined once:**

```sql
-- app/services/compensation_service.py — the ONE definition. Reused verbatim.
-- Half-open [from, to): in force on date d iff from <= d AND (to IS NULL OR to > d).
_IN_FORCE = "effective_from <= %s AND (effective_to IS NULL OR effective_to > %s)"
```

`current(...)` passes `CURRENT_DATE`; `as_at(date)` passes any date, which is what KAN-202's timeline needs and
what a stored flag could never have given. Per **UAT-F-01d**, the same-date append is permitted (the superseded
row closes to a zero-length interval, which is empty under half-open and so does not violate the exclusion
constraint) and the reader is `ORDER BY effective_from DESC, created_at DESC LIMIT 1`.

**Schema deltas** (applied to §3.2, §3.3, §3.5 as written):

| Table | Remove | Remove | Keep |
|---|---|---|---|
| `employee_compensation` | `is_current BOOLEAN` | `uq_ec_one_current`, `chk_ec_current`, `chk_ec_void_not_current` | `excl_ec_no_overlap` (now the sole guarantee), `chk_ec_interval`, `chk_ec_void` |
| `employee_job_assignments` | `is_current BOOLEAN` | `uq_eja_one_current`, `chk_eja_current` | `excl_eja_no_overlap` |
| `salary_bands` | `is_current BOOLEAN` | `uq_sb_one_current`, `chk_sb_current` | `excl_sb_no_overlap` |

**Index consequence, and it needs stating because it is the one real cost.** The partial covering index
`idx_ec_equity ... WHERE is_current AND status='ACTIVE'` cannot be partial on a computed predicate —
`CURRENT_DATE` is not `IMMUTABLE`, so it cannot appear in an index. Replacement:

```sql
CREATE INDEX IF NOT EXISTS idx_ec_in_force
    ON employee_compensation (company_id, employee_id, effective_from DESC)
    INCLUDE (effective_to, annual_base_fte, currency, employment_type)
    WHERE status = 'ACTIVE';
```
Still partial on `status` (immutable), still covering, and the `(employee_id, effective_from DESC)` ordering
makes "the row in force today" a one-row index scan per employee. **The index is now sized by *history*, not by
headcount** — at 100k employees with five records each, 500k index entries ≈ 25 MB rather than 5 MB. That is
the honest cost of the change and it is comfortably acceptable. Recorded so nobody is surprised by the number.

### 12.3.2 Annualisation constants move to the pay market — OQ-BA-3

**The SPM overruled the BA's own default on the BA's own evidence, and he is right.** Acme spans **Porto
(Portugal, 14 statutory monthly payments)**, **Hamburg (Germany, 12)** and **Tallinn (Estonia, 12)** in one
company. A company-level `monthly_payments_per_year` is wrong for a third of Acme's locations by **~17%** —
more than three times the increment the whole feature is built around. A setting that manufactures a finding
out of a payroll convention is not a default; it is a defect with a shrug attached.

**Deltas:**

```sql
ALTER TABLE pay_markets
    ADD COLUMN monthly_payments_per_year NUMERIC(4,1) NOT NULL DEFAULT 12.0,
    ADD COLUMN standard_annual_hours     NUMERIC(7,2) NOT NULL DEFAULT 1976.00,
    ADD CONSTRAINT chk_pm_payments CHECK (monthly_payments_per_year BETWEEN 12.0 AND 16.0),
    ADD CONSTRAINT chk_pm_hours    CHECK (standard_annual_hours BETWEEN 500 AND 3000);
```
`company_compensation_settings.standard_annual_hours` **stays as the fallback** for an employee whose location
resolves to no pay market, and gains `monthly_payments_per_year` for the same reason. Resolution order in
`compensation_service.annualise()`: **pay market → company settings → hard default**, and the resolved source
is recorded on the compensation row as `annualisation_source VARCHAR(16)` so a figure computed in 2026 can be
explained in 2029. That column is three bytes of insurance against the single most likely "why is this number
different?" support ticket in the feature.

**ADR-014(d) is amended accordingly:** the formula is unchanged, the *constants* are resolved per pay market,
and `annual_base_fte` remains **computed at write and stored** — which is precisely why the constants moving
later cannot silently re-value history. The two decisions were already consistent; A1 makes the second one pay.

## 12.4 ADR-017 — AMENDED. The step is a described job

> Amends §4.4. **(a), (b) and (d) stand unchanged. (c) is withdrawn. (e) is refined.** Confidence **High** on
> the model; **High** on the fourth feature code; **Medium-High** on the configuration gate split in 12.4.5.

### 12.4.1 Step numbering — pinned in the schema, because an off-by-one here is a wrong salary

**`job_levels.step_count` is the number of increments ABOVE entry.** A level with `step_count = 5` has **six
discrete step values** — `0, 1, 2, 3, 4, 5`, displayed `1.0 … 1.5` — and its top-step pay point is the base
compounded **five** times. A level with `step_count = 3` runs `.0 … .3`.

This must be a **constraint, not a convention**, and it cannot be a single-table CHECK because `step_no` lives
on `employee_job_assignments` and `step_count` on `job_levels`. §3.2 accepted that gap as TD-21 on the grounds
of proportionality. **A1 withdraws that judgement: the bound is now load-bearing on money.** A `step_no` of 6
on a `step_count = 5` level does not produce a cosmetic error — it produces a pay point compounded six times,
a `PAY_BELOW_STEP` finding against a rate nobody is entitled to, and a "Propose adjustment" action that
pre-fills a pay rise from a number that should not exist.

**Ruling: one trigger, on `employee_job_assignments`, and TD-21 is closed rather than accepted.**

```sql
CREATE OR REPLACE FUNCTION employee_job_assignment_step_valid() RETURNS trigger AS $$
DECLARE max_step INT;
BEGIN
    SELECT step_count INTO max_step FROM job_levels WHERE id = NEW.job_level_id;
    IF max_step IS NULL THEN
        RAISE EXCEPTION 'job level % does not exist', NEW.job_level_id;
    END IF;
    IF NEW.step_no < 0 OR NEW.step_no > max_step THEN
        RAISE EXCEPTION 'step_no % is outside level %''s ladder: valid steps are 0..% '
                        '(step_count counts increments ABOVE entry, so a step_count of % '
                        'yields % discrete values). EP42 ADR-017 §12.4.1.',
                        NEW.step_no, NEW.job_level_id, max_step, max_step, max_step + 1;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_eja_step_valid
    BEFORE INSERT OR UPDATE OF step_no, job_level_id ON employee_job_assignments
    FOR EACH ROW EXECUTE FUNCTION employee_job_assignment_step_valid();
```

`BEFORE INSERT OR UPDATE **OF step_no, job_level_id**` — the trigger does not fire when only `effective_to` is
closed, which is the hot write. And the exception text states the semantics, because the engineer who hits it
is the one who needed to be told.

**Schema deltas to §3.2:**

```sql
ALTER TABLE job_levels
    ADD COLUMN step_count         INT           NOT NULL,   -- NO DEFAULT. Deliberate.
    ADD COLUMN step_increment_pct NUMERIC(6,4)  NOT NULL,   -- NO DEFAULT. ADR-024.
    ADD COLUMN step_tolerance_pct NUMERIC(6,4)  NOT NULL,   -- NO DEFAULT. ADR-024.
    ADD CONSTRAINT chk_jl_step_count CHECK (step_count BETWEEN 1 AND 12),
    ADD CONSTRAINT chk_jl_increment  CHECK (step_increment_pct > 0 AND step_increment_pct <= 100),
    ADD CONSTRAINT chk_jl_tolerance  CHECK (step_tolerance_pct > 0),
    -- ADR-024(c). The whole feature turns on this one line.
    ADD CONSTRAINT chk_jl_tolerance_lt_half_increment
        CHECK (step_tolerance_pct * 2 < step_increment_pct);

ALTER TABLE employee_job_assignments
    ADD CONSTRAINT chk_eja_step_no CHECK (step_no >= 0 AND step_no <= 12);  -- replaces BETWEEN 1 AND 12
```

**`NOT NULL` with no default on all three columns is the point, not an oversight.** The SPM's D3 ruling is
that a step count *"expresses how much distance there is between this position and the next one"* and that
Trainee→Junior and Junior→Mid are genuinely different distances — so the configurator must **require an
answer**, exactly as D4c requires the pay question to be answered rather than defaulted. A column default is
how "we never decided" becomes indistinguishable from "we decided five". The migration therefore **cannot**
add these columns to a populated `job_levels` table without a value; since `job_levels` does not exist before
migration `11`, this is free — and it is the last moment it will ever be free.

### 12.4.2 `job_step_expectations` — the biggest addition in A1

Replaces the withdrawn `job_level_step_targets` (§3.2's sparse target-point table), which was guidance about
*pay*; this is content about *the job*.

```sql
CREATE TABLE IF NOT EXISTS job_step_expectations (
    job_level_id  UUID         NOT NULL,
    company_id    UUID         NOT NULL,
    step_no       INT          NOT NULL,
    summary       VARCHAR(200) NOT NULL,     -- one line, shown in lists and on the roadmap
    description   TEXT         NOT NULL,     -- the responsibilities and expectations
    updated_by_user_id UUID    NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (job_level_id, step_no),
    CONSTRAINT chk_jse_step CHECK (step_no >= 0 AND step_no <= 12),
    CONSTRAINT chk_jse_text CHECK (btrim(summary) <> '' AND btrim(description) <> ''),
    CONSTRAINT fk_jse_level FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE
);
```

**Sparse, and deliberately so.** A level may be defined before its expectations are authored; an unauthored
step shows *"Expectations not yet defined"* — an explicit empty state, never a blank, and never inherited from
another step. Authoring is a substantial content exercise per tenant (six blocks of text per level × N levels)
and blocking the ladder on it would stall W1.

**Readable by every employee.** `job_architecture:r` is seeded to every role (§12.4.5) precisely so the
transparency the owner asked for is the default and not a grant somebody has to remember. The employee's own
step and the next one are shown side by side on their profile; the whole ladder is browsable.

**No ratings, no scores, no assessment fields — and the schema says so.** There is no `score`, no `rating`, no
`achieved`, no `met_expectations` column here or in `employee_step_roadmaps`, and **there must never be one**.
That is the §14.5 / R-17 boundary expressed where it is enforceable rather than as a note in a design
document. **A PR adding an assessment column to either table is returned** — it is the first increment of a
performance-management module arriving through an entirely reasonable-sounding change.

### 12.4.3 `employee_step_roadmaps` — versioned from the start

```sql
CREATE TABLE IF NOT EXISTS employee_step_roadmaps (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id        UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    employee_id       UUID        NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    version           INT         NOT NULL,
    -- What this roadmap points at. Denormalised from the assignment ON PURPOSE:
    -- the target must survive the employee moving, so "what did we agree in March"
    -- still reads correctly after a level change.
    from_job_level_id UUID        NOT NULL,
    from_step_no      INT         NOT NULL,
    target_job_level_id UUID      NOT NULL,
    target_step_no    INT         NOT NULL,
    content           TEXT        NOT NULL,
    -- §14.5: record the review context, do NOT build the review.
    review_context    VARCHAR(24) NOT NULL,
    review_date       DATE        NULL,
    authored_by_user_id UUID      NOT NULL REFERENCES users(id),
    authored_by_label VARCHAR(255) NOT NULL,
    authored_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at   TIMESTAMPTZ NULL,
    acknowledged_by_user_id UUID  NULL REFERENCES users(id) ON DELETE SET NULL,
    superseded_at     TIMESTAMPTZ NULL,
    correlation_id    UUID        NOT NULL,

    CONSTRAINT chk_esr_version  CHECK (version >= 1),
    CONSTRAINT chk_esr_content  CHECK (btrim(content) <> ''),
    CONSTRAINT chk_esr_steps    CHECK (from_step_no >= 0 AND target_step_no >= 0),
    CONSTRAINT chk_esr_context  CHECK (review_context IN
        ('PROBATION_REVIEW','MID_TERM_GOAL_REVIEW','PERFORMANCE_REVIEW','OFF_CYCLE')),
    CONSTRAINT chk_esr_ack      CHECK ((acknowledged_at IS NULL) = (acknowledged_by_user_id IS NULL)),
    CONSTRAINT fk_esr_target FOREIGN KEY (target_job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE RESTRICT,
    UNIQUE (employee_id, version)
);

-- Exactly one live roadmap per employee. A new version supersedes the previous one
-- inside the same transaction; the previous one stays READABLE, which is the entire
-- reason this table is versioned rather than updated in place.
CREATE UNIQUE INDEX IF NOT EXISTS uq_esr_one_live
    ON employee_step_roadmaps (employee_id) WHERE superseded_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_esr_unacknowledged
    ON employee_step_roadmaps (company_id, authored_by_user_id)
    WHERE superseded_at IS NULL AND acknowledged_at IS NULL;
```

**Five design points, each of which someone would otherwise get wrong:**

1. **Versioned, never overwritten.** *"What did we agree in March"* is the question this object exists to
   answer (§14.3.3). `UPDATE` is permitted only to set `acknowledged_*` and `superseded_at`; a
   `trg_employee_step_roadmap_immutable` trigger, modelled exactly on
   `employee_compensation_immutable()` (§3.3), raises on any change to `content`, `target_*`,
   `review_context`, `version` or `authored_*`. Same pattern, same reasoning, and engineers already know it.
2. **Acknowledgement is recorded, never enforced.** No approval workflow, no blocking gate — an unresponsive
   employee must not be able to freeze their own development plan (§14.3.3). `idx_esr_unacknowledged` is what
   surfaces it back to the manager, and it is a **partial index over exactly the rows that query touches**.
3. **The employee acknowledges; nobody acknowledges on their behalf.** `acknowledged_by_user_id` is asserted
   in the service to be the subject's own user id — server-side, never from a parameter. A manager marking
   their report's roadmap as acknowledged is the failure that makes "mutually decided" a fiction, and it is
   the sort of convenience that gets added in week three.
4. **`from_*` and `target_*` are denormalised snapshots**, not joins to the current assignment. Otherwise a
   level change silently re-points every historical roadmap at a target that was never agreed.
5. **No `job_architecture` roadmap exists for a person with no assignment.** `from_job_level_id` is `NOT NULL`,
   so a roadmap cannot be authored before the employee is on the ladder — which is the right order and makes
   KAN-207 correctly depend on KAN-191.

### 12.4.4 ADR-025 — the roadmap is not performance management, and the boundary is structural

**Decision: Build the roadmap as a versioned statement of expectations with an acknowledgement, and enforce
the performance-management boundary in the schema and the review checklist, not in prose.** Confidence
**High** on the mechanism; the boundary is **the risk** (SPM R-17).

**Why an ADR for what looks like one table.** Because R-17 is real and it is a *drift* risk, not a *design*
risk: nobody will propose building performance management. What will happen is a sequence of individually
reasonable requests — "can the manager mark whether the expectation was met?", "can we show progress?", "can
we roll these up for the department?" — each of which is small, and the third of which is a rating system.
An ADR is the artifact that makes the fourth request visibly a change of decision rather than a change of
scope.

**The boundary, in enforceable terms:**

| Permitted | Forbidden — a PR adding it is returned |
|---|---|
| A text statement of what the next step requires | Any score, rating, grade, percentage or scale |
| An acknowledgement timestamp | Any "met / not met / partially met" field |
| A review context and date | A review *cycle*, schedule, window or reminder |
| Version history | Aggregation of roadmaps across a team, department or company |
| The step's generic expectation shown alongside | Goals, objectives, key results or a competency framework |
| A count of unacknowledged roadmaps, to their author | A dashboard of who has "achieved" what |

**Why this is not merely tidiness.** A rating attached to a person, stored and aggregated, is an
employee-evaluation system — Charter §1's GDPR Art. 22 and EU AI Act territory, and the exact class D3.4
gates. The moment a `met_expectations` boolean exists, the roadmap stops being a transparency artifact and
becomes an assessment record, with a different lawful basis, a different retention obligation and a different
conversation with the works council. **The distinction is not stylistic and it is not the BA's alone to hold.**

**Consequence for the audit vocabulary:** the roadmap's actions are `STEP_ROADMAP_AUTHORED`,
`STEP_ROADMAP_ACKNOWLEDGED` and `STEP_ROADMAP_SUPERSEDED`, `retention_class='EMPLOYMENT'`, and their
`_ALLOWED_DIFF_KEYS` sets contain `target_job_level_id`, `target_step_no`, `review_context`, `version` — **and
nothing that could carry an evaluation**. The allowlist is the boundary again, in the one place that outlives
everybody's memory of this decision.

### 12.4.5 The fourth feature code — `job_architecture` — and the gate split

**§14.3.2's reasoning is correct and I am adopting it: the manager authors the roadmap, and under the Wave 2
model ladder writes were `compensation:w`, so a manager could not have done their job without write access to
everyone's salary.** But the SPM's table puts *both* the ladder configuration and the roadmap behind
`job_architecture:w`, and those two writes need **different audiences**:

- **Roadmap authoring** must reach `SOLID_LINE_MANAGER`, row-scoped to their reports.
- **Ladder configuration** must not. A manager editing the company's job architecture is a much larger grant
  than the one A1 asks for, and it would arrive as a side-effect.

**Ruling — three gates, one new code, no new grant to any manager beyond what A1 requires:**

| Surface | Gate | Seeded audience | Precedent |
|---|---|---|---|
| **Browse the ladder, read step expectations, read own roadmap** | `@require_feature_access('job_architecture')` | **every role `r`** — this is the transparency A1 asked for, and it must be the default rather than a grant | — |
| **Author / supersede a step roadmap** | `@require_feature_access('job_architecture','w')` **+ row scope** (`visible_scope`-shaped: subject is a direct report, or the actor holds company-wide scope) | `SOLID_LINE_MANAGER` **w** · `HR_ADMIN` w · `PORTAL_ADMIN` w | ADR-018's scope object, reused for a second feature |
| **Configure families, levels, `step_count`, step expectations** | `@require_feature_access('org_structure','w')` | **HR_ADMIN r+w+d and PORTAL_ADMIN r+w+d, and no manager role** (`scripts/setup_db.py:128-160`) — exactly §14.3.1's intended audience, with **no seed change at all** | **V14** — `app/routes/org_change.py:381` already gates the org-change *workflow configuration* page this way while its runtime uses `org_change`. Same shape, same code, second use |
| **Base pay point, step increment, step tolerance** | `@require_feature_access('compensation','w')` | HR_ADMIN, PORTAL_ADMIN | It is money (§12.5.4) |

**Why `org_structure:w` rather than a fifth code or a `job_architecture:d`.** A fifth code is permanent
surface area for a distinction two existing codes already draw. `d` was rejected by the SPM in CFL-42-20 for a
reason that applies identically here — a grant labelled *delete* that actually confers *configure* misleads at
the exact moment the tenant admin makes the choice. `org_structure` is, literally, organisational structure
configuration; the ladder is org structure; and the seeded audience is already right without touching
`seed_rbac.sql`. **Logged as CFL-42-35 for the SPM's ratification**, because it is a refinement of his §14.3.2
table rather than an implementation of it.

**Does this re-open CFL-42-18? No — and here is the query that proves it.** CFL-42-18 was: *gating the ladder
on `compensation` blanks the directory job title for everyone.* The split holds because **the level title
displayed for a person is an attribute of that person**, read through the employee path:

```sql
-- app/routes/org.py / helpers.TREE_CTE / the directory query — gated `employee_profiles`,
-- NOT `job_architecture`. Adding the join does not add a gate.
LEFT JOIN employee_job_assignments eja
       ON eja.employee_id = e.id
      AND eja.effective_from <= CURRENT_DATE
      AND (eja.effective_to IS NULL OR eja.effective_to > CURRENT_DATE)
LEFT JOIN job_levels jl ON jl.id = eja.job_level_id
```
**Rule, and it is a review gate: no directory, org-tree, profile-header or search query may be wrapped in
`has_feature_access('job_architecture')`.** A tenant with `job_architecture` switched off still sees everyone's
job title; what they lose is the ladder browser, the expectations and the roadmaps. **T-190-9** asserts it by
rendering the directory for a user with no `job_architecture` access and checking the title is present.

**Four-place registration (amends §5.2) — four codes, `sort_order` 14–17:**

| Code | Label | sort_order | `default_enabled` | Registered in |
|---|---|---|---|---|
| `compensation` | Compensation | 14 | FALSE | KAN-194 (migration `12`) |
| `compensation_self` | My Pay | 15 | FALSE | KAN-194 (migration `12`) |
| `pay_equity` | Pay Equity | 16 | FALSE | KAN-194 (migration `12`) |
| **`job_architecture`** | **Job Architecture** | **17** | **FALSE** | **KAN-190 (migration `11`)** |

Seeded `role_feature_access` for `job_architecture`: **`r` for all ten roles**; **`w` for `SOLID_LINE_MANAGER`,
`HR_ADMIN`, `PORTAL_ADMIN`**; `d` for none — there is no delete path (a ladder in use cannot be deleted, a
superseded roadmap is history). All four places: `scripts/setup_db.py::step4_seed_portal_features` (the
`features` tuple **and** the `access_map`), migration `11`, **`database/seed_rbac.sql`** with explicit UUID
literals, and `role_feature_access` defaults in **both**. `TestFeatureRegistryHasNoDrift` catches a miss in the
migration; **T-194-3's parity assertion is extended to four codes** and now genuinely earns its place, because
this is the first code registered by a *different migration from the other three* — the exact asymmetry that
makes a manual check unreliable.

**`default_enabled = FALSE`** for consistency with the other three and with OQ-7. Deliberate consequence: a
tenant that wants job architecture must be switched on for it, and the "off" state is
`feature_disabled.html` — which, per the rule above, does **not** take the directory with it.

## 12.5 ADR-024 — NEW. The step pay point, compounding, and the configuration this product refuses

**Decision: Build. A configured **base pay point** per `(job level × pay market)`; each step's pay point
derived from it by the level's **compound** increment; a per-level **tolerance** constrained by a declarative
`CHECK` to be strictly less than half the increment; the derivation **computed, never materialised**, in Python
`Decimal`, by **one function** shared by the equity check and the pay proposal.** Confidence **High** on the
model and the storage ruling; **High** on compounding (the SPM ruled it and his reasoning holds); **Medium-High**
on the tolerance default of ±2%, which is a default and the first tenant will tell us.

### 12.5.1 The tables

```sql
-- The base rate at step .0 for one level in one market. Effective-dated, because
-- a base pay point moves — and when it moves, every finding computed against the
-- old one must still be explicable. Half-open, GiST, no stored is_current (§12.3.1).
CREATE TABLE IF NOT EXISTS job_level_pay_points (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id     UUID          NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    job_level_id   UUID          NOT NULL,
    pay_market_id  UUID          NOT NULL,
    base_amount    NUMERIC(14,2) NOT NULL,     -- the rate at step .0, FTE 1.0, annualised
    currency       CHAR(3)       NOT NULL,
    effective_from DATE          NOT NULL,
    effective_to   DATE          NULL,
    created_by_user_id UUID      NULL REFERENCES users(id) ON DELETE SET NULL,
    reason         TEXT          NOT NULL,
    correlation_id UUID          NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_jlpp_amount   CHECK (base_amount > 0),
    CONSTRAINT chk_jlpp_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT chk_jlpp_interval CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CONSTRAINT fk_jlpp_level  FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE,
    CONSTRAINT fk_jlpp_market FOREIGN KEY (pay_market_id, company_id)
        REFERENCES pay_markets (id, company_id) ON DELETE CASCADE
);
ALTER TABLE job_level_pay_points
    ADD CONSTRAINT excl_jlpp_no_overlap
    EXCLUDE USING gist (
        job_level_id WITH =, pay_market_id WITH =,
        daterange(effective_from, effective_to, '[)') WITH &&
    );
CREATE INDEX IF NOT EXISTS idx_jlpp_lookup
    ON job_level_pay_points (company_id, job_level_id, pay_market_id, effective_from DESC);

-- SPARSE. The level's increment applies to every step unless a row here says
-- otherwise. Rows exist only where a company wants the last step of a level worth
-- more than the first (§14.2.1).
CREATE TABLE IF NOT EXISTS job_step_increment_overrides (
    job_level_id  UUID         NOT NULL,
    company_id    UUID         NOT NULL,
    step_no       INT          NOT NULL,          -- the increment FROM step_no-1 TO step_no
    increment_pct NUMERIC(6,4) NOT NULL,
    updated_by_user_id UUID    NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (job_level_id, step_no),
    CONSTRAINT chk_jsio_step CHECK (step_no BETWEEN 1 AND 12),   -- never an override "to" step 0
    CONSTRAINT chk_jsio_pct  CHECK (increment_pct > 0 AND increment_pct <= 100),
    CONSTRAINT fk_jsio_level FOREIGN KEY (job_level_id, company_id)
        REFERENCES job_levels (id, company_id) ON DELETE CASCADE
);
```

`step_increment_pct`, `step_tolerance_pct` and `step_count` live on `job_levels` (§12.4.1) — **not** on the pay
point, because they are properties of the ladder's shape, not of one market's money. A five-step level is a
five-step level in Tallinn and in Stockholm; only the base differs.

### 12.5.2 Compounding — ruled, and the schema proves which was chosen

**`point(n) = base × (1 + i)^n`, compound, not linear.** The SPM ruled it and named exactly why it needed
ruling: across a five-step level at 5% the two readings diverge by **~2.1% of salary** — small enough that an
engineer would guess either way and never notice, large enough to be wrong, and *precisely the same order as
the ±2% tolerance the check turns on*. A linear implementation would put the top step of every level almost
exactly one tolerance band out and generate a `PAY_BELOW_STEP` finding for every correctly-paid senior person
in the tenant. **That is not a rounding difference; it is a systematically wrong answer that looks plausible.**

With per-step overrides the derivation is a product, not a power:

```python
def step_pay_point(base: Decimal, level_increment_pct: Decimal,
                   overrides: dict[int, Decimal], step_no: int) -> Decimal:
    """The pay point for `step_no`. Exact decimal throughout; ONE quantise at the
    end (BR-1.5 / ADR-014). Compound: each step uplifts the PREVIOUS step's point."""
    point = base
    for n in range(1, step_no + 1):
        pct = overrides.get(n, level_increment_pct)
        point = point * (Decimal(1) + pct / Decimal(100))
    return point.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
```

**No intermediate rounding.** Quantising each step would compound the rounding error along with the increment
and make `point(5)` depend on how it was reached. The loop runs at most twelve times.

**The reference table UAT must reproduce by hand** (base 60,000.00, i = 5%, `step_count = 5`), with the linear
values alongside **so a linear implementation fails loudly rather than quietly**:

| Step | Compound (correct) | Linear (wrong) | Δ |
|---|---|---|---|
| `.0` | 60,000.00 | 60,000.00 | — |
| `.1` | 63,000.00 | 63,000.00 | — |
| `.2` | 66,150.00 | 66,000.00 | +150.00 |
| `.3` | 69,457.50 | 69,000.00 | +457.50 |
| `.4` | 72,930.38 | 72,000.00 | +930.38 |
| `.5` | **76,576.89** | 75,000.00 | **+1,576.89 (2.1%)** |

`.4` is `72,930.375` before quantising → **72,930.38** under HALF_UP. That single half-cent is the reason
BR-1.5 exists and the reason the quantise happens once, at the end, and not inside the loop.

### 12.5.3 Computed, not materialised — the §15.2 item 4 ruling

**Ruling: computed. Confidence High.** Four arguments, and one that decides it.

1. **Consistency with CFL-42-16.** "Current is computed, never stored" is now the project's rule for derived
   temporal facts. A materialised pay-point table is the same class of object and would be the one exception.
2. **Materialised means stale.** `(levels × markets × steps)` ≈ 12 × 5 × 6 = **360 rows per tenant** — small,
   which is exactly why the temptation exists. But every base change, increment change, override change and
   `step_count` change would need a regeneration, and "did we regenerate?" is a silent-wrongness bug class on
   the number the entire feature compares against.
3. **The cost is negligible.** The event path evaluates one employee: one row from `job_level_pay_points`, one
   from `job_levels`, ≤12 `Decimal` multiplications. The company run needs at most 360 distinct points,
   computed once per run and cached for its duration.
4. **The decider — one function, one number.** The equity check compares against a pay point, and the
   step-change proposal (§14.4) **pre-fills the same number**. If those two came from different code paths
   they would eventually differ in the last cent, and the consequence is specific and bad: a
   `PAY_BELOW_STEP` finding whose own "Propose adjustment" remedy does not clear it, because the proposed
   amount lands a cent outside the tolerance. The finding would re-open forever and nobody would understand
   why. **One `step_pay_point()`, called by both.** That is the property worth protecting, and materialising
   would give it to us too — but only if the materialiser and the proposal used the same code, which returns
   us to needing one function anyway, plus a table.

**And it must not be computed in SQL.** V16: PostgreSQL's `power(numeric, numeric)` is not documented as
exact. `numeric` multiplication is. The engine therefore computes the (bounded) set of pay points in Python
and **joins them into the query as a `VALUES` list**:

```sql
JOIN (VALUES (%s::uuid, %s::int, %s::numeric), …) AS pp(job_level_id, step_no, point)
  ON pp.job_level_id = eja.job_level_id AND pp.step_no = eja.step_no
```
One row per (level, step) in scope — 1 for an event, ≤360 for a company run. A 360-row `VALUES` list is
nothing, and it buys exact, reproducible, identical-to-the-proposal arithmetic. Cached on `g` per request.

### 12.5.4 The refused configuration — `tolerance < increment / 2`

**This is the single most likely way to render the whole feature useless through a plausible-looking setting**
(SPM R-16), so it gets the strongest enforcement available.

**With a 5% increment and a ±5% tolerance, adjacent steps' tolerance bands overlap.** Step `.2` at 66,150 with
±5% spans 62,842.50–69,457.50; step `.1` at 63,000 spans 59,850–66,150; step `.3` at 69,457.50 spans
65,984.63–72,930.38. Every employee is "correctly paid" for *some* step. **The check reports zero findings, the
screen says everything is fine, and it is measuring nothing.** A control that fails silently while appearing to
work is worse than no control, because the organisation now believes it has one.

**Where it lives, answering §15.2 item 6 — "so it cannot be bypassed by direct SQL or by an import":**

| Case | Enforcement | Bypassable? |
|---|---|---|
| **The common case** — one increment for the whole level | **`chk_jl_tolerance_lt_half_increment CHECK (step_tolerance_pct * 2 < step_increment_pct)` on `job_levels`** (§12.4.1) | **No.** A single-row `CHECK` binds the ORM-less service, direct `psql`, a CSV import, a migration and a future engineer equally |
| **The sparse case** — a per-step increment override lower than 2× the level's tolerance | **One `BEFORE INSERT OR UPDATE` trigger on `job_step_increment_overrides`**, reading the parent level's tolerance and raising with the same message | **No** |
| **Lowering an override below tolerance by raising the tolerance instead** | The level `CHECK` fires against `step_increment_pct`; the trigger must therefore **also** fire on a `job_levels` tolerance update. **Second trigger, `AFTER UPDATE OF step_tolerance_pct ON job_levels`**, validating every override row for that level | **No** |

**Two triggers, and I am justifying them rather than adding them casually** — §3.2 declined a trigger for
`step_no` on proportionality grounds and §12.4.1 has already reversed that judgement for the same reason this
one applies: **this constraint is load-bearing on money, and the failure mode is silence.** The declarative
`CHECK` carries the common case at zero cost; the triggers cover the two cross-table paths, on a sparse table
and on a rarely-updated column. That is the smallest enforcement that is actually complete.

**Strict inequality, deliberately.** `tolerance * 2 < increment`, not `<=`. At exactly half, adjacent bands
*touch*: a salary precisely between two pay points is simultaneously at the top of one band and the bottom of
the next, and which step it "belongs to" depends on evaluation order. Excluding the boundary costs a tenant
nothing and removes an ambiguity that would surface as a non-deterministic finding.

**The error message explains the geometry, because "invalid configuration" teaches nobody:**

> *"A tolerance of ±5.00% cannot be used with a 5.00% step increment: the tolerance bands of adjacent steps
> would overlap, so every employee would count as correctly paid for some step and the check would report
> nothing. The tolerance must be under 2.50% for this level."*

**The second guard — a level base below the previous level's top step — is a WARNING, not a refusal, and the
distinction is architectural.** It spans rows across levels *and* markets, and it is **sometimes legitimate**
(a broad senior band whose entry deliberately overlaps the junior band's top). A refusal would block a real
configuration. So: `job_architecture_service.ladder_warnings(company_id) -> list[Warning]`, computed on
demand, rendered by the configurator **at the point the choice is made** (the SPM's standing rule, §12.4 of
his file), and **never** as a constraint. **Rule for engineers: a refusal is a `CHECK` or a trigger; a warning
is a service function and a screen. Do not implement a warning as a soft constraint that code can skip — that
is a refusal with a hole in it.**

## 12.6 ADR-023 — RE-CUT. Check A′ is absolute; Check B stays statistical

> Supersedes §4.10's Check A. **§4.10's *placement* — event-driven per group, after commit, in its own
> transaction, with an advisory-locked company run — stands unchanged and is the part of that ADR that was
> right.** Confidence **High**.

### 12.6.1 Two engines behind one service, and they are genuinely different shapes

| | **Check A′ — step-pay correspondence** | **Check B — gender pay gap** |
|---|---|---|
| Question | "Does this person's pay match the step they are on?" | "Does this group show a gender gap?" |
| Unit | **One employee** | One `(company, family, level, market)` group |
| Reference | **The step's configured pay point** | Median male vs median female within the group |
| Arithmetic | One subtraction, one division, one quantise | `percentile_cont(0.5)` with `FILTER`, even-group case |
| Group minimum | **None. `n = 1` is valid and meaningful** | **`n ≥ 5`, ≥ 2 of each gender compared** |
| Coverage gate | **None** — replaced by per-employee preconditions + the ladder-fitted-and-reviewed gate | **Retained** |
| Gated on | The ladder gate | The ladder gate **and DPO-1** |
| Finding types | `PAY_BELOW_STEP` (primary) · `PAY_ABOVE_STEP` (secondary) | `GENDER_GAP`, with direction |

**Do not delete the statistical machinery.** §4.10(c)'s group query survives **verbatim for Check B** — the
`percentile_cont`, the gendered `FILTER`s, `n_male` / `n_female`, `currency_count`, the coverage gate and the
`OTHER`/`NULL` excluded-and-counted path. What it loses is `median_all` as the *primary* reference. This is the
single most likely thing to be lost in the clear-out, which is why it is stated as a prohibition.

### 12.6.2 Check A′, precisely

```python
expected  = step_pay_point(base, increment, overrides, step_no)   # Decimal, 2dp (§12.5.2)
actual    = row['annual_base_fte']                                 # Decimal, 2dp, already FTE-normalised
deviation = ((actual - expected) / expected * 100).quantize(Decimal('0.01'), ROUND_HALF_UP)

if deviation < -tolerance:  raise_finding('PAY_BELOW_STEP', deviation, expected)   # primary
elif deviation > tolerance: raise_finding('PAY_ABOVE_STEP', deviation, expected)   # secondary
else:                       no finding
```

**Boundary: exactly `±tolerance` is INSIDE — no finding.** Consistent with the SPM's ratified inclusivities
(UAT-F-01b: the coverage gate evaluates at exactly 80%; the justification window does not re-fire on its last
day) and with the conservative reading — do not flag somebody who is exactly on the line the tenant configured
as acceptable. **Documented in the UI**, per BR-1.6 / CFL-42-34: the comparison uses the **2dp value the screen
shows**, so a user can reproduce the finding from what is in front of them. A check whose result cannot be
recomputed from the displayed numbers destroys trust in a compliance figure faster than being wrong would.

**Per-employee preconditions — each counted and shown, never silent** (§14.2.3). An employee failing any of
these is **"not evaluable"** with the reason named, which is a distinct state from "no finding":

| # | Precondition | Not-evaluable reason |
|---|---|---|
| 1 | Current level **and step** assignment | `NO_LADDER_ASSIGNMENT` |
| 2 | Current compensation record (`status='ACTIVE'`, in force today) | `NO_PAY_RECORD` |
| 3 | Location resolves to a pay market | `NO_PAY_MARKET` |
| 4 | A pay point configured for that `(level, market)` | `NO_PAY_POINT` |
| 5 | `employment_status = 'ACTIVE'` | `NOT_ACTIVE` |
| 6 | `employment_type NOT IN ('CONTRACTOR','INTERN')` | `EXCLUDED_EMPLOYMENT_TYPE` |
| 7 | The compensation currency equals the pay point's currency | `CURRENCY_MISMATCH` — **never converted**, no silent 1:1 |

Counts per reason are written to `pay_equity_evaluations` and rendered above the register. **A register showing
"0 findings" over 90 not-evaluable employees is the most dangerous screen in the epic** (D7.4's reasoning,
which survives A1 intact even though the coverage gate that motivated it does not).

### 12.6.3 The ladder-fitted-and-reviewed gate, and the fitting algorithm

**The risk A1 creates:** a naive `.0`-for-everyone backfill makes every employee paid above entry — which is
most of them — a `PAY_ABOVE_STEP` finding in the first hour. R-1's alert storm returning in a new costume.

**Part 1 — the backfill fits the step to the pay.** `job_architecture_service.fit_step()`:

```python
def fit_step(actual_annual_base_fte, level, market, points):
    """Choose the step whose pay point is closest to what the person is ACTUALLY paid.
    Returns (step_no, fit_state, fit_deviation_pct, reason).

    This is circular ONLY if you read it as measurement. It is not: it is an initial
    load, and the ladder is being fitted to a reality that came first. Measurement
    begins after HR has reviewed the fit — which is what Part 2 gates."""
    if actual is None:                    return 0, 'NEEDS_REVIEW', None, 'NO_PAY_RECORD'
    if not points:                        return 0, 'NEEDS_REVIEW', None, 'NO_PAY_POINT'
    if actual < points[0]:                return 0, 'NEEDS_REVIEW', dev(0), 'PAY_BELOW_ENTRY'
    if actual > points[level.step_count]: return level.step_count, 'NEEDS_REVIEW', \
                                                 dev(level.step_count), 'PAY_ABOVE_TOP_STEP'
    best = min(range(0, level.step_count + 1),
               key=lambda n: (abs(actual - points[n]), n))     # exact-tie → the LOWER step
    return best, 'FITTED', dev(best), None
```

**Four rulings inside that function, each of which someone would otherwise decide differently:**

- **Exact ties resolve to the *lower* step.** Asymmetric cost, conservative side — the same reasoning as D4h.
  Fitting **up** manufactures a *job-content* claim (this person holds step 1.3's responsibilities) on the
  evidence of *pay alone*, and it suppresses a `PAY_BELOW_STEP` finding that may be real. Fitting **down** at
  worst produces a `PAY_ABOVE_STEP` — the secondary, low-severity finding, which is exactly the queue HR is
  meant to work through. Ties are also not hypothetical: with a round base and a round increment, a salary set
  by a previous HR system on the same arithmetic lands exactly between two points regularly.
- **Never extrapolate below `.0` or above the top step.** Clamp, and mark `NEEDS_REVIEW`. Extrapolating would
  invent steps that do not exist on the ladder the tenant configured.
- **Nobody is fitted without a pay record.** Step `.0`, `NEEDS_REVIEW`, reason `NO_PAY_RECORD`. That is the
  honest state and it feeds the review screen rather than the findings register.
- **The fit is recorded as a fit.** `employee_job_assignments.fit_state VARCHAR(16)` ∈ `MANUAL` ·
  `FITTED` · `NEEDS_REVIEW` · `REVIEWED`, plus `fit_deviation_pct NUMERIC(6,2) NULL`. A manually-set step is
  `MANUAL` and is never re-fitted by a subsequent import.

**Part 2 — the gate.** `company_compensation_settings.ladder_fit_reviewed_at TIMESTAMPTZ NULL` and
`ladder_fit_reviewed_by_user_id`. **Check A′ raises no finding for a company until it is set**, by a deliberate
act of an `org_structure:w` holder on the fit-review screen, audited as `LADDER_FIT_REVIEWED`. Until then the
register shows the **review progress** (`n of m reviewed`, grouped by `fit_state`), not findings.

**One gate, one human act, and it is far better targeted than a percentage** — the 80% coverage gate would have
opened the floodgates at 80% of *coverage*, which says nothing about whether the fitted steps are right.
Setting it back to NULL (a re-fit after a ladder change) is permitted, audited, and closes every `OPEN`
Check A′ finding as `RESOLVED_BY_DATA` rather than leaving findings computed against a ladder that has moved.
**Check B is not gated on it** — a gender gap does not depend on the step fit being reviewed.

### 12.6.4 `pay_equity_findings` — amended

```sql
-- Amends §3.6. The lifecycle columns, the CHECK set and uq_pef_one_open stand.
ALTER TABLE pay_equity_findings
    ADD COLUMN finding_type    VARCHAR(24) NOT NULL,
    ADD COLUMN step_no         INT         NULL,      -- part of the key for A′, reported for B
    ADD COLUMN reference_value NUMERIC(14,2) NULL,    -- the pay point used. MONEY — see below
    ADD COLUMN deviation_pct   NUMERIC(6,2)  NULL,    -- signed: negative = below
    ADD COLUMN direction       VARCHAR(8)    NULL,    -- Check B: which gender is ahead
    ALTER COLUMN group_size     DROP NOT NULL,        -- Check B only
    ALTER COLUMN compared_count DROP NOT NULL,        -- Check B only
    ALTER COLUMN coverage_pct   DROP NOT NULL,        -- Check B only
    ADD CONSTRAINT chk_pef_type CHECK (finding_type IN
        ('PAY_BELOW_STEP','PAY_ABOVE_STEP','GENDER_GAP')),
    -- Each finding type carries exactly the columns its own check produces. This is
    -- what stops a Check B finding acquiring a step-level reference by copy-paste.
    ADD CONSTRAINT chk_pef_shape CHECK (
        (finding_type IN ('PAY_BELOW_STEP','PAY_ABOVE_STEP')
             AND subject_employee_id IS NOT NULL AND step_no IS NOT NULL
             AND reference_value IS NOT NULL AND deviation_pct IS NOT NULL)
     OR (finding_type = 'GENDER_GAP'
             AND subject_employee_id IS NULL AND group_size IS NOT NULL
             AND compared_count IS NOT NULL AND direction IS NOT NULL
             AND reference_value IS NULL)),
    ADD CONSTRAINT chk_pef_direction CHECK (direction IS NULL
                                         OR direction IN ('MALE_AHEAD','FEMALE_AHEAD'));

-- The uniqueness key now includes the step and the type: one open finding per
-- (subject, level, market, step, type).
DROP INDEX IF EXISTS uq_pef_one_open;
CREATE UNIQUE INDEX uq_pef_one_open ON pay_equity_findings (
    company_id, finding_type,
    COALESCE(subject_employee_id, '00000000-0000-0000-0000-000000000000'::uuid),
    job_level_id, pay_market_id, COALESCE(step_no, -1)
) WHERE state = 'OPEN';
```

**`reference_value` is money in a `pay_equity`-gated table, and CFL-42-19 applies to it.** The finding stores
the pay point it used so that a finding remains reproducible after the base changes — without it, a base
change makes every historical finding unexplainable. But `reference_value` **is** the step's rate, and
`reference_value × (1 + deviation_pct/100)` **is** the subject's salary. So the same rule the SPM ratified for
compa-ratios binds it:

> **`reference_value` and `deviation_pct` are returned only to an actor holding `pay_equity:r` AND
> `compensation:r`.** To a `pay_equity`-only holder the register renders a **band label** — *"below the step
> rate"* / *"above the step rate"* — and the finding is still fully workable: they can see who, which step,
> which direction, and disposition it. What they cannot do is reconstruct the number.

That is CFL-42-19 applied to a **stored column** rather than a computed ratio, and it is why §4.10's original
`measured_value` design needed re-examining rather than renaming. The `GENDER_GAP` finding carries no
`reference_value` at all (the `chk_pef_shape` CHECK enforces it) — a median-to-median percentage is not
invertible to any individual's pay, which is why Check B's number is safe to render to `pay_equity:r` alone.

**Asymmetric severity, in the data and not only in the copy.** `PAY_BELOW_STEP` is the owner's stated concern
and carries a computable remedy; `PAY_ABOVE_STEP` is legitimate far more often than not (market premium,
red-circled legacy pay, retention). The register defaults to filtering `PAY_BELOW_STEP + GENDER_GAP`, the bell
notifies on `PAY_BELOW_STEP` and `GENDER_GAP` only, and **`PAY_ABOVE_STEP` never raises a notification** — it
is a register-only condition. Treating the two with equal weight is how a queue fills with things nobody
should act on, which is R-1 by another route.

**"Propose adjustment" — the remedy that ships with the finding.** On a `PAY_BELOW_STEP`, an actor holding
`pay_equity:r` **and** `compensation:w` gets an action that pre-fills a `COMPENSATION_REVIEW` request at
`reference_value`, through the **existing** chain — one endpoint, one engine, four-eyes intact, nothing
auto-applied. The finding transitions to `RESOLVED` when a compensation record lands at or above the tolerance
floor, detected by the ordinary post-commit re-evaluation (§4.10b) rather than by the request knowing about
the finding. **The finding does not hold a foreign key to the request**: coupling them would make the finding's
lifecycle depend on a request that can be rejected, cancelled or superseded. The correlation is by re-evaluation,
which is idempotent and self-correcting.

### 12.6.5 Cost, re-run — it improves substantially

Check A′ has **no aggregate, no window function and no group-by**. It is one indexed scan joined to a small
`VALUES` list, evaluated row by row in `Decimal`.

| Population | Check A′ — one employee (the event path) | Check A′ — whole company | Check B — whole company (unchanged) |
|---|---|---|---|
| Acme 46 / Telia 100 | **< 2 ms** | **< 15 ms** | < 20 ms |
| 10,000 | **< 2 ms** | **60–150 ms** *(was 150–400 ms)* | 150–400 ms |
| 100,000 | **< 3 ms** | **0.8–2 s** *(was 2–5 s)* | 2–5 s |

**The event path is now O(1) rather than O(group)** — a salary write re-evaluates *that employee*, not their
comparison group, because the reference is absolute. That is the structural improvement A1 buys and it is
larger than the wall-clock numbers suggest: it removes the whole class of "a colleague's pay change re-raised
my finding" behaviour that a median reference would have produced. **Check B still needs the group**, so a
compensation write triggers a Check A′ re-evaluation for one employee **and** a Check B re-evaluation for one
group; the group path is the §4.10(b) mechanism, unchanged.

`pay_equity_evaluations` gains `check_type VARCHAR(24) NOT NULL CHECK (check_type IN ('A_PRIME','B','BOTH'))`
and `not_evaluable_counts JSONB NOT NULL DEFAULT '{}'` (the §12.6.2 reason tallies). `duration_ms` is still
written on every run — the cost model above is **modelled above 146 and must be checked against reality**
rather than believed (T-200-8, unchanged).

## 12.7 The remaining Wave 3 rulings that change this design

Actioned here rather than scattered, with the task that carries each. §12 of the SPM's file is the
authoritative conflict register; **my §10.3 numbering is superseded by it.**

| SPM ruling | Change to this design | Task |
|---|---|---|
| **CFL-42-9** | `_apply_change` closes `manager_relationships` with no `effective_to`; two such rows exist. Already designed in **T-189-4**; now also **backfills the two rows** to the closing date implied by the successor row, or to `created_at` where no successor exists, recorded in the migration comment | T-189-9 |
| **CFL-42-11 / 26 / 31** | Four-eyes: **≥2 independently satisfiable levels required at create** for money- or level-bearing requests (refused, naming the configuration fix); **a seeded two-level default chain** (HR_ADMIN → PORTAL_ADMIN) for those types; **the initiator may not decide any level**. Without the first two the control is a silent no-op in every tenant today (**V18**) | T-198-7, T-198-8 |
| **CFL-42-13** | A manager without `compensation:r` records `pay_decision = 'NOT_ANSWERED_NO_PERMISSION'`, and **the first `compensation:r` approver must answer before approving**. Added to `chk_ocp_decision`'s enum and to `decide()`'s pre-conditions | T-196-10 |
| **CFL-42-14 / 15** | **Subject ≠ initiator** and **subject ≠ decider**, universal, every role including SYSTEM_ADMIN → **KAN-203, W0, P0**. `CLAUDE.md`'s org-change invariant 2 is tightened in the same commit (my file) | KAN-203 |
| **CFL-42-16** | `is_current` withdrawn; current computed | §12.3.1 |
| **CFL-42-19** | Both halves adopted: the both-codes rule (already T-201-3) **plus a config-time advisory on the Feature Access tab** where `pay_equity` is granted without `compensation` | T-201-12 |
| **CFL-42-24** | The bell badge counts findings **with no owner**; `[ Take ]` is a recorded, audited act (`PAY_EQUITY_FLAG_TAKEN`) that decrements the badge while the finding stays `OPEN` in the register. Adds `owner_user_id` and `taken_at` to `pay_equity_findings` | T-201-13 |
| **CFL-42-25** | `LEVEL_CHANGE` + `direction` | §12.2(d) |
| **CFL-42-27** | The subject may **read** a finding about themselves; the disposition controls are **absent** (not disabled). Where that leaves no eligible dispositioner, the warning goes to Compensation Settings, the Feature Access tab **and** the SYSTEM_ADMIN tenant banner | T-201-14 |
| **CFL-42-28** | The bell's one-click `✓ Approve` is **suppressed** for any request carrying a pay or level change; the line shows "Review →" | T-196-11 |
| **CFL-42-29** | **KAN-204** — EP38's shared shell accessibility fixes (global `:focus-visible`, shared live regions, `prefers-reduced-motion`) land in W0, tagged EP33 | KAN-204 |
| **CFL-42-30 / A-2** | The structural allowlist **stands and is what I rely on**. The mandatory `reason` on compensation-bearing actions becomes a **seeded, company-editable category** + optional free text; the free text carries a **non-blocking numeric-pattern warning** and is in the compensation redaction path. **No criterion may claim the guard covers free text** — I over-claimed in ADR-019 and the correction is right | T-193-10 |
| **CFL-42-32** | No aggregate of any kind rendered below **n = 5**; the configurable minimums **floored in the database** (already `chk_ccs_min_o` / `chk_ccs_min_g`, floor raised from 2 to 2 with the render rule separate) | T-200-12 |
| **CFL-42-33** | **`404`, not `403`, for every EP42 cross-tenant subject substitution** — a 403 confirms the id exists. The EP38 inconsistency is **TD-26** for the S5 sweep, recorded deliberately | T-194-11 |
| **CFL-42-34** | **BR-1.6 wins: compare the value the UI displays.** Already adopted in §12.6.2 | — |
| **OQ-BA-3** | Annualisation constants on the **pay market** | §12.3.2 |
| **OQ-BA-5** — *costed, as asked* | A "who viewed this salary" read log. **Measured, not guessed: four call sites** — `current()`, `history()`, `self_view()` and the equity register's amount rendering — because ADR-018 funnels every scoped read through one `Scope`. One append-only table, one insert per read, `retention_class='SECURITY'`. **Estimate 0.5 dev-days.** Per the SPM's own condition (*"if it is ≤ half a day it lands in KAN-194 as a Should"*), **it lands in KAN-194** | T-194-12 |
| **UXQ3** | Seed a starter list of salary-change reason categories — `Annual review`, `Promotion`, `Market adjustment`, `Role change`, `Correction`, `Other` — company-editable. Supplies the structured half of A-2 | T-193-10 |
| **UXQ5** | An audited salary export in **KAN-202**, row-scoped exactly as the screen is, watermarked with actor and timestamp, audited as `COMPENSATION_EXPORTED` with row count and scope | T-202-6 |
| **UXQ8** | A **contractor's rate is recordable** and **excluded from every comparison with the exclusion counted**. `chk_ec_*` already permits it; what changes is two distinct empty states — *"No rate recorded"* vs *"Not applicable for comparison — contractor rate recorded"* | T-195-5 (amended) |
| **UAT-F-01d** | Same-date append permitted, tie-break by `created_at`, superseded row marked | §12.3.1 |
| **UAT-F-08** | A non-ACTIVE employee: history readable and retained; the record **closes at `exit_date`**; new records refused except a correction | T-193-11 |
| **UAT-Q9** | A third standalone regression suite, `tests/ui/test_compensation_workflow.py`. UAT owns the suite; **the `CLAUDE.md` amendment naming it in the regression-flow-test list is mine, in the same commit** | T-194-13 |

## 12.8 The task breakdown, amended

**Same contract as §9:** one-line statement of work, exact files, owner, estimate in dev-days, dependency,
tests, definition of done — on top of the Engineering Charter §4 DoD, which applies to every row.

**Totals: 21 stories · 175 tasks · 133.5 task-days → 90–110 dev-days delivered · critical path 71.0.**
§9's 112 tasks stand except where withdrawn below. **31 new-story tasks · 33 amendment tasks · 3 re-homed ·
1 withdrawn.**

### 12.8.0 Withdrawn and re-homed

| Task | Was | Now |
|---|---|---|
| **T-200-5** | Check A — compa-ratio to band midpoint / group median, `n ≥ 3` | **WITHDRAWN.** Replaced by **T-200-11** (Check A′). Its group-median code was the thing A1 removed |
| **T-199-3, T-199-4, T-199-6** | Band CRUD · compa-ratio + out-of-band flag · step target points | **RE-HOMED to KAN-205** as T-205-1/2/3 (SPM Ruling 32 — KAN-199 splits). Step *target points* become **step expectations** and move to KAN-190 (T-190-10) |
| **§3.2 `job_level_step_targets`** | A sparse percentile target per step | **WITHDRAWN.** Replaced by `job_step_expectations` (§12.4.2) — the object A1 actually asked for |

### 12.8.1 KAN-203 — subject ≠ initiator, subject ≠ decider — **W0 · Must · P0** — lead: SNR

> **A live Critical defect, not new scope** (V17, SPM §12.5). Today an HR_ADMIN can raise a position change
> for themselves and approve it on the seeded default chain. **P0 and first**, because it is a self-approved
> desk move now and a self-approved pay rise the day KAN-196 lands, and I will not carry a P0 through four waves.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-203-1** | SNR | `_can_initiate_for` (`app/routes/org_change.py:55-64`): the admin branch gains `and subject_id != u.get('employee_id')`. **The exemption exists so HR can move *other* people** — that is its whole purpose. | — | 0.5 | EMPLOYEE, SOLID_LINE_MANAGER, HR_ADMIN, PORTAL_ADMIN and **SYSTEM_ADMIN** each refused on themselves; each still permitted on another | no role, at any privilege level, can initiate for themselves |
| **T-203-2** | SNR | `decide()` (`org_change_service.py:235-249`): refuse when `user['employee_id'] == req['employee_id']`, **before** the SYSTEM_ADMIN branch at `:248` and before any write. Named error, not a generic one. | T-203-1 | 0.5 | the subject cannot decide any level of their own request, at any privilege level | — |
| **T-203-3** | SNR | Hide the affordance: `can_initiate_org_change_for()` (`org_change.py:67`) returns False for self, so the Transfer… entry points do not offer it. **Display only — the route re-checks** (the helper's own docstring already says so). | T-203-1 | 0.5 | the `⋯` menu and the profile button are absent on your own row; a hand-crafted POST is still refused | hiding a button is never the control |
| **T-203-4** | SNR | Extend `tests/test_org_change.py` and `tests/test_transfer_entry_point.py`; add the two defect-reproduction cases named as **DEF-42-4** and **DEF-42-5** so a regression is unmistakable. | T-203-2 | 1.0 | both reproductions fail before the fix and pass after; both regression suites green, counts reported | — |
| **T-203-5** | ARCH | **`../../CLAUDE.md`** — tighten org-change invariant 2 to say explicitly that **nobody, including HR_ADMIN, PORTAL_ADMIN and SYSTEM_ADMIN, may initiate or decide a request whose subject is themselves.** The headline was right and the detailed rule beneath it was wrong. `docs/ARCHITECTURE_REVIEW.md` records DEF-42-4/5 against EP27. **Same commit.** | T-203-4 | 0.5 | doc-currency gate | the invariant that everyone loads as binding rules now matches the code |

**KAN-203: 3.0 dev-days.**

### 12.8.2 KAN-204 — the shared shell accessibility fixes — **W0 · Must · P2** — lead: MID · tagged EP33

> EP38's shell fixes never landed (UX verified: three of nine). EP42 adds ten surfaces; ten private live
> regions is the doubling D-004 exists to prevent. **Tagged EP33 so that epic's scope shrinks honestly.**

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-204-1** | MID | Global `:focus-visible` in the shared stylesheet; verify against the existing shell rather than assuming EP38 delivered it. | — | 1.0 | keyboard traversal of the existing nav, bell and modals shows a visible focus ring on every interactive element | WCAG 2.4.7 met on the **shell**, not per-screen |
| **T-204-2** | MID | Two shared ARIA live regions in `templates/base.html` (`polite` for status, `assertive` for errors) plus `announce(msg, level)` in the shared JS. Every EP42 DOM builder uses them; **no new surface declares its own.** | T-204-1 | 1.0 | a screen-reader announcement fires on save, error and empty-state transitions; grep-assert: exactly one `aria-live` container pair in `templates/` | — |
| **T-204-3** | MID | `@media (prefers-reduced-motion: reduce)` honoured by every transition and the drag-and-drop affordance. | T-204-1 | 0.5 | reduced-motion snapshot | — |
| **T-204-4** | MID | Document the three shell primitives in `TECHNICAL_DOCUMENTATION.md` so EP42's ten screens use them rather than reinventing; note the EP33 tag. Same commit. | T-204-3 | 1.0 | doc-currency gate | a new screen's accessibility is a call to an existing primitive |

**KAN-204: 3.5 dev-days.**

### 12.8.3 KAN-208 — synthetic gender across the seeded population — **W0 · Must · P2** — lead: MID

> **The DEF-004 trap, exactly.** A dev DB updated by hand while `database/seed_data.sql` / `telia_seed.sql`
> stay unchanged is how CI broke on 9 August. Seeds **and** migration, or it does not exist outside one laptop.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-208-1** | MID | The assignment function: **deterministic and reproducible** — `gender = f(employee_number)` via a fixed, documented hash, **not** `random()`. A migration that produces different data on each machine is unreproducible and untestable. | — | 0.5 | running the function twice on the same input yields the same output; documented in the migration banner | two engineers get identical databases |
| **T-208-2** | **MID** | **Shape the distribution so Check B is demonstrable** (SPM §14.6.3). A per-row coin flip across 146 people will not reliably give **≥5 in a group with ≥2 of each gender**. Assign by **comparison group**: pick two groups that will satisfy `n ≥ 5` and `≥2 each`, seed those deliberately, then distribute the remainder. Include `OTHER` for the excluded-and-counted fixture (SPM §12.4 / UAT-F-10). | T-208-1 | 1.0 | **assert after the seed: ≥2 comparison groups satisfy Check B's minimums, and `OTHER` is present** | a gender assignment that leaves Check B undemonstrable has not done its job |
| **T-208-3** | MID | `database/migrations/10b_synthetic_gender.sql` — idempotent `UPDATE employees SET gender = … WHERE gender IS NULL` (never overwrites a value), plus a `_down` that nulls only the rows it set (tracked by a capture table, same pattern as §12.2(b)). | T-208-2 | 0.5 | apply / re-apply / reverse on a fresh DB | — |
| **T-208-4** | **MID** | **The same values in `database/seed_data.sql` and `database/telia_seed.sql`.** A fresh CI database replays no migrations. This is the DEF-004 half and it is the half that gets missed. | T-208-3 | 0.5 | **CI-style fresh build** (`dropdb/createdb/schema/seed`) shows the same distribution as the dev DB | — |
| **T-208-5** | MID | Migration banner + `TECHNICAL_DOCUMENTATION.md`: this is **synthetic data for fictional people**; it does **not** authorise collecting gender from real people; **T5 is unaffected**; **DPO-1 still gates Check B** — having data does not make processing it lawful. Same commit. | T-208-4 | 0.0 | doc-currency gate | nobody later reads the seeded values as a precedent for collection |

**KAN-208: 2.5 dev-days.**

### 12.8.4 KAN-206 — step pay points, increments and tolerance — **W2 · Must · P1** — lead: SNR · design: ARCH (ADR-024)

> **Hard prerequisite of KAN-200 and KAN-192.** It is the reference value for the entire equity feature and
> the pre-fill for every step-change pay proposal.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-206-1** | ARCH | ADR-024 signed off (§12.5). Walk **compounding vs linear** and the **~2.1% divergence** with SNR before any code — it is the one an engineer would guess and never re-examine. | KAN-199 | 0.5 | — | SNR can state why the top step of a five-step level is not `base × 1.25` |
| **T-206-2** | SNR | Migration `12b_step_pay_points.sql`: `job_level_pay_points` (+ `excl_jlpp_no_overlap`, `idx_jlpp_lookup`), `job_step_increment_overrides`. Companion `_down`. Regenerate `schema.sql`. | T-206-1, T-190-8 | 1.0 | fresh apply; re-apply no-op; overlapping pay-point periods refused; a cross-tenant `job_level_id` refused **by the composite FK** | — |
| **T-206-3** | **SNR** | **`compensation_service.step_pay_point(base, increment, overrides, step_no)`** — exact `Decimal`, compound, **one** `ROUND_HALF_UP` quantise at the end (§12.5.2). **This is the only implementation; KAN-200 and KAN-192 both call it.** | T-206-2, T-193-4 | 1.0 | the §12.5.2 reference table (base 60,000, i=5%, 5 steps) **byte-for-byte, including 72,930.38**; the linear values asserted **not** to match; a 3-step level; per-step overrides; `step_no = 0` returns the base unchanged | a linear implementation fails loudly |
| **T-206-4** | **SNR** | **The refused configuration.** `chk_jl_tolerance_lt_half_increment` on `job_levels` (§12.4.1) **plus** the two triggers of §12.5.4 (on `job_step_increment_overrides` insert/update, and on `job_levels` tolerance update). Error text explains the geometry. | T-206-2 | 1.0 | tolerance 2.5 / increment 5.0 **refused** (strict `<`); 2.49 / 5.0 accepted; an override of 4.0 against a 2.5 tolerance refused **by the trigger**; **the same refusals via direct `psql` and via a CSV import**, not only via the service | **R-16 closed at the database, not the form** |
| **T-206-5** | MID | Pay-point CRUD gated `@require_feature_access('compensation','w')`; effective-dated, half-open; audited `PAY_POINT_CHANGED` with `currency`, `effective_date`, `job_level_id`, `pay_market_id` and `pct_change_band` — **never an amount** (ADR-019). | T-206-3 | 1.0 | superseding a pay point closes the old one with no overlap; the audit diff passes `_ALLOWED_DIFF_KEYS` | — |
| **T-206-6** | MID | `job_architecture_service.ladder_warnings(company_id)` — the level-base-below-previous-top-step **warning** (§12.5.4), computed on demand, rendered at the point the choice is made. **A service function and a screen, never a constraint.** | T-206-3 | 0.5 | a descending ladder warns and still saves; an ascending one does not warn | a warning is not a soft constraint |
| **T-206-7** | MID | The joint configuration screen: `step_count`, expectations and titles on `org_structure:w`; base pay point, increment and tolerance on `compensation:w`. **It must read coherently to a holder of one gate and not the other** — absent, not disabled, not broken (SPM CFL-42-20 consequence). | T-206-5, UX | 1.0 | an `org_structure:w` holder without `compensation:w` sees the ladder half and **no money fields in the payload**; the reverse holds | two gates, one screen, no broken state |
| **T-206-8** | MID | "Cost of the ladder" — total gap between current pay and fitted step pay points, for HR to see before adopting (§14.2.6). **Should · P3**, aggregate only, and **not rendered below n = 5** (CFL-42-32). Docs in the same commit. | T-206-7 | 0.0 | the aggregate is absent below n=5 | — |

**KAN-206: 6.0 dev-days.**

### 12.8.5 KAN-207 — the step roadmap and employee transparency — **W1 · Must · P1** — lead: MID · design: ARCH (ADR-025)

> **The object the owner actually asked for.** No compensation dependency, which is why it can close W1 with a
> shippable, employee-visible outcome and no pay data anywhere in it.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-207-1** | ARCH | ADR-025 signed off (§12.4.4), **including the forbidden-column table**. Add "an assessment field on `employee_step_roadmaps` or `job_step_expectations`" to the standing review checklist. | T-190-8 | 0.5 | — | R-17 has a named review gate, not a good intention |
| **T-207-2** | SNR | Migration `11b_step_roadmaps.sql`: `employee_step_roadmaps` with every CHECK in §12.4.3, `uq_esr_one_live`, `idx_esr_unacknowledged`, and `trg_employee_step_roadmap_immutable` (modelled on `employee_compensation_immutable`). Companion `_down`. Regenerate `schema.sql`. | T-207-1 | 1.0 | two live roadmaps for one employee **refused by the index**; an `UPDATE` of `content` **raises**; an `UPDATE` of `acknowledged_at` succeeds | versioning is a database guarantee |
| **T-207-3** | MID | `job_architecture_service.author_roadmap()` — supersede-then-insert in **one** `transaction()`, `version = prev + 1`, snapshot `from_*` and `target_*`, mandatory `review_context`, audit `STEP_ROADMAP_AUTHORED` + `STEP_ROADMAP_SUPERSEDED`. | T-207-2, T-193-3 | 1.0 | a rollback leaves the previous version live; the previous version stays **readable**; no roadmap without a current assignment | — |
| **T-207-4** | **MID** | **Row scoping** (§12.4.5): `@require_feature_access('job_architecture','w')` **+** the subject is a direct report, **or** the actor holds company-wide scope. Reuses ADR-018's `Scope` — a second feature, the same object. **Not a sub-flag: the flag grants the surface, the scope decides the rows.** | T-207-3, T-194-4 | 1.0 | a manager authors for their report and gets **404** on a non-report (CFL-42-33); an HR_ADMIN authors for anyone; an EMPLOYEE gets 403 with no state change | the CC-2 boundary holds for a second feature |
| **T-207-5** | **MID** | **The employee's view — the primary one.** Own current step's expectation, the target step's expectation, the roadmap content, its version history, and **[ I have read and discussed this ]** which sets `acknowledged_at`. Gated `job_architecture:r`, **hard-scoped to `session['employee_id']` server-side — no parameter exists.** | T-207-4, UX | 1.5 | an employee sees **their own** roadmap and **404** on a colleague's, **asserted at the payload**; there is no `employee_id` parameter to tamper with — assert by inspecting the route signature | the transparency the owner asked for is the default |
| **T-207-6** | MID | **The employee acknowledges; nobody acknowledges for them.** `acknowledged_by_user_id` asserted server-side to equal the subject's user id. Unacknowledged roadmaps surface back to their **author** via `idx_esr_unacknowledged` — **a list, not a blocking gate** (§14.3.3). | T-207-5 | 0.5 | a manager cannot acknowledge their report's roadmap; an unacknowledged roadmap never blocks a step change | "mutually decided" is recorded, not enforced |
| **T-207-7** | MID | The manager's authoring view: the target step's generic expectation shown alongside the free-text field so the roadmap is written **against** it. Copy is UX's — **expectations, not an assessment, no implied promise**. WCAG 2.2 AA using KAN-204's primitives. | T-207-5, UX | 1.0 | copy matches the UX spec verbatim; no field on the screen accepts a score or a rating | R-17's boundary visible in the UI |
| **T-207-8** | ARCH | `TECHNICAL_DOCUMENTATION.md` — a "Job architecture: expectations and roadmaps" section **including ADR-025's forbidden-column table**, so the boundary is discoverable by the engineer who gets the "can we add a rating?" request. Same commit. | T-207-7 | 0.5 | doc-currency gate | — |

**KAN-207: 7.0 dev-days.**

### 12.8.6 KAN-205 — salary bands as the level envelope — **W4 · Should · P2** — lead: MID

> Split from KAN-199 (SPM Ruling 32). **Repositioned, not resized:** bands are the level's min/max envelope
> ("is this pay sane for this level at all?"), no longer the comparison basis.

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-205-1** | MID | *(was T-199-3)* `salary_bands` migration + effective-dated CRUD gated `compensation:w`; `PAY_BAND_CHANGED` audited with `width_pct_change_band`, never amounts. **`is_current` withdrawn** (§12.3.1). | T-206-2 | 1.5 | overlapping bands refused; `min > mid` refused | — |
| **T-205-2** | MID | *(was T-199-4)* Out-of-band pay is **allowed, flagged, and requires a reason — never hard-blocked**. The flag is a UI state on the pay form, not a refusal. **Band position is a fact, not a finding** (SPM OQ-BA-1) — it renders on the Compensation card and raises nothing. | T-205-1 | 1.0 | an out-of-band amount saves with a reason and is marked; no `pay_equity_findings` row is created | red-circled pay stays in the system |
| **T-205-3** | MID | *(new — SPM OQ-BA-8)* **Band context for the approver at decision time** on a money-bearing request: where the proposed amount lands in the level's band. Gated `compensation:r`. It could not be in KAN-196 because bands did not exist yet. | T-205-2, T-196-6 | 0.5 | absent for an approver without `compensation:r` | an approver is not deciding blind |
| **T-205-4** | MID | Docs: bands section, and the explicit note that **bands are an envelope, not the equity basis** — so a future reader does not reconnect them to the engine. Same commit. | T-205-3 | 0.5 | doc-currency gate | — |

**KAN-205: 3.5 dev-days.** *(KAN-199 retains T-199-1, T-199-2, T-199-5, T-199-7 — pay markets only, plus the
annualisation constants of §12.3.2 — and drops to **2.5 dev-days**, moving to **W2** as a hard prerequisite.)*

### 12.8.7 Amendment tasks on existing stories

| Task | Owner | Work · files | Dep | Est | Tests | Done when |
|---|---|---|---|---|---|---|
| **T-188-11** | SNR | **`feature_access_for(user_id, company_id)`** and **`feature_access_for_users(ids, company_id)`** in `app/auth.py`, sharing **one** `_feature_access_sql(scope)` builder with `_load_feature_access()` (§12.2a). | T-188-4 | 1.0 | a candidate approver's resolved access matches what they get from their own session; SYSTEM_ADMIN short-circuits identically; the plural form is **one** query for N users | CFL-42-12 / DEP-10 closed |
| **T-188-12** | SNR | Two grep-asserts: `company_features` + `role_feature_access` appear in **exactly one** SQL string in `app/`; `feature_access_for*` is **never called from `app/routes/`**. | T-188-11 | 0.5 | both | a second permission query cannot be added silently |
| **T-188-13** | SNR | `company_features_pre_kan188` capture table **before** the repair UPDATE, and the `_down` that restores from it (§12.2b). `ON CONFLICT DO NOTHING` on the capture — first run wins. | T-188-3 | 0.5 | **round trip**: apply → 330-cell matrix unchanged → reverse → the 18 rows byte-identical to T-188-2's fixture → re-apply → unchanged | a rollback cannot re-black-out both tenants |
| **T-188-14** | SNR | **CFL-42-8 / V15:** `require_feature_access` denies with a **JSON 403** for `/api/*` and JSON `Accept`, and the HTML flash+redirect otherwise; the tenant-disabled branch returns `feature_disabled.html` (HTML) or `403 {'error':'feature_disabled'}` (JSON) — **distinguishable codes** (§12.2e). | T-188-4 | 1.0 | every `/api/*` deny returns 403 with a JSON body; every page deny still redirects; **full regression pass** — this changes the deny response of every gated route | EP38's "returns 403" criteria become true |
| **T-189-9** | SNR | **CFL-42-9:** backfill the two `manager_relationships` rows closed with a NULL `effective_to` — to the successor row's `effective_from`, or to `created_at` where none exists — inside migration `10`, with the reasoning in the banner. | T-189-4 | 0.5 | zero `is_current = FALSE` rows with `effective_to IS NULL` remain | the pattern EP42 copies is no longer broken on its closing side |
| **T-190-8** | SNR | `job_levels` gains `step_count`, `step_increment_pct`, `step_tolerance_pct` — **`NOT NULL`, no default** — plus `chk_jl_step_count`, `chk_jl_increment`, `chk_jl_tolerance` and **`chk_jl_tolerance_lt_half_increment`** (§12.4.1). `employee_job_assignments.chk_eja_step_no` becomes `0..12`. | T-190-2 | 1.0 | a level cannot be created without a step count; the tolerance CHECK refuses 2.5/5.0 | "we never decided" cannot look like "we decided five" |
| **T-190-9** | MID | Register **`job_architecture`** in **all four places** at `sort_order` 17 (§12.4.5) — `setup_db.py` features tuple **and** `access_map`, migration `11`, `seed_rbac.sql` with UUID literals, `role_feature_access` in both. Ladder **reads** move to `job_architecture:r`; **configuration** moves to `org_structure:w`. | T-190-8 | 1.0 | `TestFeatureRegistryHasNoDrift` green **on a CI-style fresh build**; **the directory renders a level title for a user with no `job_architecture` access** — CFL-42-18 does not re-open | four codes, four places, and the directory survives |
| **T-190-10** | MID | `job_step_expectations` table + the expectations editor inside the configurator, gated `org_structure:w`. Sparse; an unauthored step shows *"Expectations not yet defined"* — never blank, never inherited. **No score, rating or assessment field** (ADR-025). | T-190-9, UX | 0.5 | an unauthored step renders the empty state; grep-assert: no `rating`/`score`/`achieved` column in the migration | the biggest addition in A1 exists |
| **T-191-10** | SNR | Assignment carries a **step**; `trg_eja_step_valid` (§12.4.1) enforcing `0 <= step_no <= level.step_count`, firing only on `INSERT OR UPDATE OF step_no, job_level_id`. | T-190-8, T-191-1 | 1.0 | step 6 on a 5-step level **refused by the trigger** with the semantics in the message; closing `effective_to` does not fire it | TD-21 **closed**, not accepted |
| **T-191-11** | **SNR** | **`fit_step()`** (§12.6.3) — nearest pay point, **exact ties to the LOWER step**, clamped at `.0` and the top step, `fit_state` ∈ `MANUAL`/`FITTED`/`NEEDS_REVIEW`/`REVIEWED`, `fit_deviation_pct`. A `MANUAL` step is never re-fitted by a later import. | T-191-10, T-206-3 | 1.5 | hand-computed fixtures incl. **an exact tie**, pay below entry, pay above the top step, and no pay record; the tie resolves **down** | R-1's new route closed |
| **T-191-12** | MID | The **fit-review screen** and the gate: per-employee fitted step with its deviation, HR override, and one deliberate **"Mark ladder fit reviewed"** by an `org_structure:w` holder setting `ladder_fit_reviewed_at`, audited `LADDER_FIT_REVIEWED`. Resetting it closes every `OPEN` Check A′ finding as `RESOLVED_BY_DATA`. | T-191-11, UX | 0.5 | Check A′ raises **nothing** until the flag is set; resetting it retires open A′ findings for **every** recipient | one gate, one human act |
| **T-192-7** | MID | Mandatory **`review_context`** on every step change — `PROBATION_REVIEW` · `MID_TERM_GOAL_REVIEW` · `PERFORMANCE_REVIEW` · `OFF_CYCLE` (+ `INITIAL_LOAD`, `LEVEL_CHANGE` set by the system) — plus `review_date` and an optional note. **Mandatory to answer, with an off-cycle option** (D4c's pattern). | T-191-10 | 0.5 | a step change with no context is refused; `OFF_CYCLE` is a valid answer, not a bypass | **no review cycle, schedule, reminder, goal, rating or probation entity is created** — grep-assert the migration |
| **T-192-8** | **SNR** | **Propose, never apply** (§14.4). Advancing a step **pre-fills a `COMPENSATION_REVIEW`** at `step_pay_point()` and routes it through the existing chain. `job_architecture_service` calls `org_change_service.create_request()` — a permitted call direction (§2.2); it **never** writes `employee_compensation`. The pay answer is mandatory and may be "no change" with a reason. | T-192-7, T-206-3, T-196-3 | 1.0 | **a step change writes zero rows to `employee_compensation`** — asserted directly against the DB; the pre-filled request is an ordinary request subject to four-eyes; the pre-filled amount is **byte-identical** to the one Check A′ compares against | the deliberate consequence — step and pay temporarily out of correspondence — is what Check A′ detects |
| **T-192-9** | MID | The top-step signal narrows to **the reporting manager only** (§14.3.4); HR sees it in the register. **New:** step distribution as a live report of scope taken on, on the team view. | T-192-2 | 0.5 | `compensation:w` holders no longer receive the notification; the manager still does; the subject **never** does (OQ-BA-4) | a straight noise reduction |
| **T-193-10** | SNR | **A-2 / CFL-42-30:** on compensation-bearing actions the mandatory `reason` becomes a **seeded, company-editable category** (`Annual review`, `Promotion`, `Market adjustment`, `Role change`, `Correction`, `Other` — UXQ3) **plus optional free text** carrying a **non-blocking numeric-pattern warning**, and included in the compensation redaction path. | T-193-3 | 1.0 | a category is required; free text with digits warns and still saves; **no test claims the guard covers free text** | I over-claimed in ADR-019; the correction is right |
| **T-193-11** | MID | **UAT-F-08:** a non-ACTIVE employee's record **closes at `exit_date`**; history stays readable and retained; new records refused except a correction. | T-193-5 | 0.0 | offboarding closes the interval; a new record is refused with a named error | — |
| **T-194-11** | MID | **CFL-42-33: `404`, not `403`, for every EP42 cross-tenant subject substitution.** A 403 confirms the id is real. The EP38 inconsistency is **TD-26**, recorded deliberately rather than discovered. | T-194-6 | 0.5 | an Acme admin gets 404 on a Telia employee id across every EP42 endpoint | the existence oracle is closed for EP42 |
| **T-194-12** | MID | **OQ-BA-5, costed at 0.5d and therefore in scope as a Should:** `compensation_read_log` (append-only, `retention_class='SECURITY'`) written from the **four** call sites ADR-018's `Scope` funnels reads through — `current()`, `history()`, `self_view()`, the equity register's amount rendering. | T-194-4 | 0.5 | a read by a manager logs subject, actor, scope and timestamp; a 403 logs nothing | measured, not guessed |
| **T-194-13** | ARCH | **UAT-Q9:** add `tests/ui/test_compensation_workflow.py` to **`../../CLAUDE.md`**'s regression-flow-test list (my file, UAT owns the suite). Same commit as the suite. | T-194-6 | 0.5 | the rule names three suites | — |
| **T-196-10** | SNR | **CFL-42-13:** `pay_decision = 'NOT_ANSWERED_NO_PERMISSION'` added to `chk_ocp_decision`; **the first `compensation:r` approver must answer it before approving.** Satisfies D4c and D4f simultaneously. | T-196-3 | 0.5 | a manager without `compensation:r` raises a move that records the value; the first eligible approver is blocked until they answer | the control is not optional for the population that raises most moves |
| **T-196-11** | MID | **CFL-42-28:** suppress the bell's one-click `✓ Approve` for any request carrying a **pay or level** change; the line shows "Review →". The product's own precedent — reject is already a deep link because a decision without a recorded reason is not auditable. | T-196-7 | 0.5 | a money-bearing request offers no quick approve in the bell; a placement-only one still does | nobody approves an amount they cannot see |
| **T-197-8** | SNR | **CFL-42-25:** rename `'PROMOTION'` → **`'LEVEL_CHANGE'`** in the enum, the CHECK, `_infer_request_type()` and every call site; add **`direction`** (`UP`/`DOWN`/`LATERAL`), `NOT NULL` for that type, derived server-side, **`LATERAL` whenever the family changes regardless of ordinals**. `PROMOTION_APPLIED` → `LEVEL_CHANGE_APPLIED` in `ACTIONS` and `_ALLOWED_DIFF_KEYS`. "Promotion" stays the user-facing word when `direction = 'UP'`. | T-197-1 | 0.5 | a demotion never reads "Promotion" in the inbox, the bell, the timeline **or the audit action**; a cross-family move is `LATERAL` | the durable record stops lying |
| **T-198-7** | **SNR** | **CFL-42-11 / V18 — without this the control does nothing.** For money- or level-bearing requests, **refuse at create unless the chain has ≥2 independently satisfiable levels**, resolved through `feature_access_for_users()` (T-188-11), naming the configuration fix. Also refuse the CFL-42-26 case (one person the only possible approver at two levels). | T-198-2, T-188-11 | 1.0 | the **seeded default single-HR_ADMIN chain refuses a money-bearing request** with a message naming the fix; a two-level chain with one shared holder also refuses; a placement-only request is unaffected | "the control exists" and "the control works" become the same statement |
| **T-198-8** | SNR | Ship a **seeded two-level default chain** (HR_ADMIN → PORTAL_ADMIN) for money- and level-bearing request types, in `seed_rbac.sql` **and** the migration **and** `setup_db.py`. Plus **initiator ≠ decider** on those types (CFL-42-31). | T-198-7 | 0.5 | a tenant that has configured nothing can still raise and approve a money request, with two people; the initiator cannot decide any level | the four-place rule applies to seeded chains too |
| **T-198-9** | SNR | **Ruling 13's condition (§12.2c):** `cancel()` gains a **mandatory reason** and writes `ORG_CHANGE_CANCELLED_BY_ADMIN` (`retention_class='SECURITY'`) inside its transaction; the four-eyes refusal message **names the cancel-and-reconfigure remedy**. **Cancel is not approve; `decide()` gains no SYSTEM_ADMIN escape.** | T-198-2 | 0.5 | a stuck chain can be cancelled by SYSTEM_ADMIN, **applies nothing**, and leaves one audit row; a cancel with no reason is refused | the SYSTEM_ADMIN narrowing has its remedy |
| **T-200-11** | **SNR** | **Check A′ (§12.6.2)** — replaces the withdrawn T-200-5. Absolute, per employee, no group minimum, no coverage gate; the seven per-employee preconditions each **counted and named**; the `±tolerance` boundary **inclusive** (no finding at exactly the tolerance); comparison on the **2dp displayed value** (BR-1.6 / CFL-42-34). | T-206-3, T-191-12 | 1.5 | hand-computed fixtures at exactly ±2%, just inside and just outside; each precondition produces its named not-evaluable reason; **`n = 1` produces a valid finding** | the thin-data problem is dissolved |
| **T-200-12** | SNR | Amend `pay_equity_findings` (§12.6.4): `finding_type`, `step_no`, `reference_value`, `deviation_pct`, `direction`, the nullable Check-B columns, `chk_pef_shape`, and the rebuilt `uq_pef_one_open`. **CFL-42-32:** no aggregate rendered below **n = 5**, minimums floored in the database. | T-200-2 | 1.0 | a `GENDER_GAP` row with a `reference_value` is **refused by `chk_pef_shape`**; a second open A′ finding for the same (subject, level, market, step) is refused by the index; an n=4 aggregate is absent from the payload | each finding type carries exactly its own columns |
| **T-200-13** | SNR | **Keep Check B intact.** T-200-3's group query survives **for Check B only** — `percentile_cont`, gendered `FILTER`s, `n≥5`, ≥2 of each gender, `OTHER`/`NULL` excluded-and-counted, `|gap| ≥ threshold` with direction recorded, coverage gate retained. **Gated on DPO-1.** Step added as a **reported** dimension, not a grouping one. | T-200-3, T-208-2 | 0.5 | every surviving UAT Check-B fixture green; the statistical path is demonstrably still there | the clear-out did not take Check B with it |
| **T-201-12** | MID | **CFL-42-19 second half:** a config-time advisory on the **Feature Access tab** where `pay_equity` is granted without `compensation` — the consequence shown where the choice is made. | T-201-3 | 0.5 | granting `pay_equity` alone shows the advisory | the SPM's standing rule, third application |
| **T-201-13** | MID | **CFL-42-24:** `owner_user_id` + `taken_at` on `pay_equity_findings`; **the badge counts unowned findings**; `[ Take ]` is a recorded, audited act (`PAY_EQUITY_FLAG_TAKEN`) that decrements the badge while the finding stays `OPEN`. | T-201-5 | 1.0 | taking does not retire the finding; the badge drops; the register still shows it; **taking is not reading** | R-1's second route closed |
| **T-201-14** | MID | **CFL-42-27:** the subject may **read** a finding about themselves; the disposition controls are **absent** (not disabled), with the stated line. Where that leaves no eligible dispositioner, the warning goes to Compensation Settings, the Feature Access tab **and** the SYSTEM_ADMIN tenant banner. | T-201-4 | 0.5 | the subject's payload contains the finding and **no disposition affordance**; the no-dispositioner warning appears in all three places | same family as KAN-139 and KAN-203 |
| **T-201-15** | **MID** | **"Propose adjustment"** on `PAY_BELOW_STEP` (§12.6.4) — pre-fills a `COMPENSATION_REVIEW` at `reference_value` through the **existing** chain, for an actor holding `pay_equity:r` **and** `compensation:w`. **No FK from the finding to the request**; the finding retires as `RESOLVED` via ordinary post-commit re-evaluation. `PAY_ABOVE_STEP` **never** raises a notification. | T-201-13, T-200-11 | 1.0 | the pre-filled amount is byte-identical to the reference; a rejected request leaves the finding `OPEN`; the finding resolves when the pay lands | **the best thing A1 gives us**, and it carries its own remedy |
| **T-202-6** | MID | **UXQ5:** an audited salary export — row-scoped **exactly** as the screen is, watermarked with actor and timestamp, audited as `COMPENSATION_EXPORTED` with row count and scope. Plus the **step and roadmap timeline alongside the pay timeline** (§14.8) — "how did this person get here" is one story. | T-202-3, T-207-5 | 1.0 | a manager's export contains their reports only, asserted at the file; every export writes one audit row | the alternative is somebody adding an unaudited CSV button |

### 12.8.8 Revised sequencing and the re-cut critical path

Built against the SPM's §14.8 build order, with the dependency graph resolved rather than the wave order
assumed serial.

```
W0  S2   KAN-203 (3.0, P0)  ∥  KAN-204 (3.5)  ∥  KAN-208 (2.5)  ∥  KAN-188 (9.0)  ∥  KAN-189 (5.0)
              │                                                        │
              └── unblocks nothing; it CLOSES a live P0 ────────────────┤
                                                                       ▼
W1  S3   KAN-190 (8.5) ──► KAN-191 (11.0) ──► KAN-207 (7.0)   ← shippable: ladder + expectations +
              │                  │                              everyone placed + roadmaps.  NO MONEY.
              │                  │
W2  S3   KAN-199 (2.5) ──► KAN-206 (6.0)     ← markets, then pay points.  206 blocks 200 AND 192
              │                  │
              ▼                  │
         KAN-193 (8.0) ──► KAN-194 (9.0) ──► KAN-195 (6.0)      ← minimum shippable slice ends here
                                 │
W3  S3                     KAN-196 (8.5) ──► KAN-197 (5.5) ──► KAN-198 (6.5) ──► KAN-192 (6.5)
                                 │
W4  S3                     KAN-200 (7.5) ──► KAN-201 (9.5) ──► KAN-205 (3.5) ──► KAN-202 (5.0)
                                 ▲
                        ⛔ KAN-168 real-DB tier — SPM Ruling 27: hard entry condition for W4
```

**Critical path — 71.0 dev-days:**
`KAN-188 (9.0) → KAN-190 (8.5) → KAN-191 (11.0) → KAN-193 (8.0) → KAN-194 (9.0) → KAN-196 (8.5) →
KAN-200 (7.5) → KAN-201 (9.5)`.

**KAN-206 is NOT on the critical path**, and that is worth stating because it is a hard prerequisite of
KAN-200 and reads like one: it needs KAN-199 (2.5, startable the moment KAN-188 lands) and KAN-190, so it
completes around day 24 while KAN-200 cannot start before day 54. **KAN-207 is also off-path** — it closes W1
for value, not for dependency. Neither should be sequenced as if it constrains the finish.

| Milestone | Path | Days |
|---|---|---|
| **P0 closed** | KAN-203 alone | **3.0** |
| **W1 shippable** — a ladder, described expectations, everyone on it, roadmaps, **no pay data** | 188 → 190 → 191 → 207 | **35.5** |
| **Minimum shippable slice** (SPM's "could we stop here?") | 188 → 190 → 191 → 193 → 194 | **45.5** |
| **R1–R4, R6, R7 satisfied** (everything but the equity engine) | + 196 → 197 → 198 → 192 | **~72** |
| **Complete** | + 200 → 201 → 205 → 202 | **71.0 critical path / 133.5 task-days** |

**Parallel tracks:** **A** critical path (SNR-1 + MID-1) · **B** KAN-189 + KAN-203 from day 1 (SNR-2) ·
**C** KAN-204 + KAN-208 from day 1 (MID-2, then KAN-199 → KAN-206) · **D** KAN-207 and KAN-195 as float ·
**E** DEVOPS continuous (btree_gist, logging, runbooks, the KAN-208 seed parity check, equity telemetry).

**Effort: 133.5 task-days → 90–110 dev-days delivered.** With 2 SNR + 2 MID + 0.3 DEVOPS the **critical path,
not the total, is the binding constraint: ≈ 14–16 calendar weeks** including ARCH review and a regression pass
per story. **Confidence Medium.** That is a full grade lower than my Wave 2 figure and the reason is honest:
A1 added two objects, a feature code and three stories, and it added them to the two stories (KAN-191, KAN-201)
whose estimates were already the least certain.

**Effort by story, revised:**

| Wave | Story | Was | Now | Δ | Why |
|---|---|---|---|---|---|
| W0 | **KAN-203** | — | **3.0** | new | Live P0 (V17) |
| W0 | **KAN-204** | — | **3.5** | new | EP33 shell debt (CFL-42-29) |
| W0 | **KAN-208** | — | **2.5** | new | Synthetic gender, seeds **and** migration |
| W0 | KAN-188 | 7.0 | **9.0** | +2.0 | Non-session resolver, reversibility capture, JSON denial |
| W0 | KAN-189 | 4.5 | **5.0** | +0.5 | CFL-42-9 backfill |
| W1 | KAN-190 | 6.0 | **8.5** | +2.5 | Fourth code, step columns + CHECK, expectations editor |
| W1 | KAN-191 | 8.0 | **11.0** | +3.0 | Step assignment + trigger, `fit_step`, the fit-review gate |
| W1 | **KAN-207** | — | **7.0** | new | The roadmap — the object the owner asked for |
| W2 | KAN-199 | 5.5 | **2.5** | −3.0 | Split: markets only, moved to W2 |
| W2 | **KAN-206** | — | **6.0** | new | Step pay points, compounding, the refused configuration |
| W2 | KAN-193 | 7.0 | **8.0** | +1.0 | Reason category + numeric warning, `exit_date` closure |
| W2 | KAN-194 | 7.5 | **9.0** | +1.5 | 404, read log, fourth-code parity, `CLAUDE.md` |
| W2 | KAN-195 | 6.0 | **6.0** | — | Contractor empty state absorbed |
| W3 | KAN-196 | 7.5 | **8.5** | +1.0 | `NOT_ANSWERED_NO_PERMISSION`, quick-approve suppression |
| W3 | KAN-197 | 5.0 | **5.5** | +0.5 | `LEVEL_CHANGE` + direction |
| W3 | KAN-198 | 4.5 | **6.5** | +2.0 | ≥2 satisfiable levels, seeded chain, initiator bar, cancel remedy |
| W3 | KAN-192 | 4.5 | **6.5** | +2.0 | `review_context`, propose-not-apply, narrowed signal |
| W4 | KAN-200 | 8.5 | **7.5** | **−1.0** | **Check A′ is genuinely simpler** — no `percentile_cont`, no windowing, no coverage gate |
| W4 | KAN-201 | 7.5 | **9.5** | +2.0 | Three finding types, badge/Take, self-disposition, Propose adjustment |
| W4 | **KAN-205** | — | **3.5** | split | Bands as the envelope |
| W4 | KAN-202 | 4.0 | **5.0** | +1.0 | Audited export, roadmap timeline |
| | **Total** | 93.0 | **133.5** | **+40.5** | |

**KAN-200 getting cheaper is the one number worth pausing on.** A1 removed a group aggregate, a windowing
function, a coverage gate and an entire class of small-group edge case from the epic's largest story, and
replaced them with a subtraction. **A better-specified requirement made the hardest thing we had to build
smaller.** That is worth saying out loud, because the amendment otherwise reads as pure cost.

## 12.9 Register updates

### 12.9.1 ADRs — after A1

| ADR | Status | Change |
|---|---|---|
| ADR-014 | **Stands**, amended | §12.3.2 — annualisation constants resolve **pay market → company → default**, recorded on the row as `annualisation_source` |
| ADR-015 | **Stands**, amended | §12.3.1 — stored `is_current` withdrawn; the GiST exclusion constraint is the sole guarantee; `as_at(date)` becomes possible, which a stored flag never allowed |
| ADR-016 | **Ratified by the SPM**, amended | §12.2(a) `feature_access_for` / `feature_access_for_users` · §12.2(b) the reversibility capture · §12.2(e) the JSON 403 |
| **ADR-017** | **Amended** | §12.4 — entry at `.0`, `step_count` = increments above entry, per level with **no default**, the step trigger (TD-21 **closed**), `job_step_expectations` replacing `job_level_step_targets`, and the three-gate split of §12.4.5 |
| ADR-018 | **Stands**, extended | The `Scope` object is reused by `job_architecture:w` for roadmap authoring (T-207-4) — a second feature, the same boundary |
| ADR-019 | **Stands**, amended | `LEVEL_CHANGE_APPLIED`; five A1 actions; the structural allowlist is what I rely on, and the **free-text `reason` claim is withdrawn** (A-2) |
| ADR-020 | **Stands unchanged** | Half-open intervals; CFL-4 closed. A1 touched nothing here, and §12.3.1 makes it load-bearing rather than merely tidy |
| ADR-021 | **Stands**, amended | `LEVEL_CHANGE` + `direction`; `NOT_ANSWERED_NO_PERMISSION`; the child-table decision is untouched |
| ADR-022 | **Stands**, amended | §12.2(c) cancel-not-approve remedy; ≥2 satisfiable levels; the initiator bar; the universal subject rules move to KAN-203 |
| **ADR-023** | **Re-cut** | §12.6 — Check A′ absolute, Check B statistical and intact, the ladder gate, the improved cost model. **Placement stands unchanged** |
| **ADR-024** | **NEW** | §12.5 — the step pay point, compounding, `tolerance < increment/2` refused declaratively, computed-not-materialised, one shared `step_pay_point()` |
| **ADR-025** | **NEW** | §12.4.4 — the roadmap is a versioned statement of expectations; the performance-management boundary is structural, with a forbidden-column table |

### 12.9.2 Technical Debt — changes and additions

| ID | Change |
|---|---|
| **TD-21** | **CLOSED, not accepted.** The cross-table `step_no <= step_count` bound is now enforced by `trg_eja_step_valid` (§12.4.1). A1 made it load-bearing on money — a step beyond the ladder produces a pay point nobody is entitled to — and proportionality no longer favours leaving it to the service |
| **TD-25** *(new)* | A rollback of migration `10` **after** the EP42 `portal_features` rows exist is a **partial** rollback: `default_enabled` disappears while the four codes remain, so their absent-row default silently flips to enabled. The `_down` refuses to run while any EP42 code exists, and the runbook says so. **P2** |
| **TD-26** *(new)* | **EP38 returns `403` on a cross-tenant id; EP42 returns `404`** (CFL-42-33). A deliberate, recorded inconsistency, not a discovered one. Bringing EP38 into line is an **S5 hardening** item, not an EP42 story. **P3** |
| **TD-27** *(new)* | `idx_ec_in_force` is sized by **history**, not headcount, now that `is_current` is computed — ~25 MB at 100k employees × 5 records rather than ~5 MB. Acceptable and recorded so the growth is expected. **P4** |
| **TD-28** *(new)* | Two triggers now guard `tolerance < increment/2` across tables (§12.5.4). If PostgreSQL ever gains multi-table CHECK constraints — or if the tolerance moves onto a single row with the increment — they collapse to one declarative constraint. **P4** |
| TD-16, 17, 18, 19, 20, 22, 23, 24 | Unchanged |

### 12.9.3 Technical Risk — changes and additions

| ID | Change |
|---|---|
| **TR-15** | **Downgraded to Medium probability.** The SPM ratified ADR-016 in full and made the 330-cell matrix a **release gate** rather than a task. The mechanism is unchanged; what changed is that it can no longer be waved through |
| **TR-18** | **Unchanged in substance, and now SPM-owned at P0.** KAN-168 is a hard entry condition for W4 (Ruling 27). If it slips, **W4 slips and EP42 ships through W3** — which satisfies R1, R2, R3, R4, R6 and R7 |
| **TR-27** *(new)* | **A linear step-pay-point implementation.** Diverges ~2.1% at the top of a five-step level — the same order as the ±2% tolerance — so it would flag every correctly-paid senior person in the tenant while looking plausible. **Medium × High.** Mitigated by T-206-3's reference table with the linear values asserted **not** to match |
| **TR-28** *(new)* | **A plausible configuration silently disables Check A′** (SPM R-16). **Medium × High** → **Low × High** after mitigation: `chk_jl_tolerance_lt_half_increment` plus the two triggers make it unrepresentable through the service, direct SQL **and** an import |
| **TR-29** *(new)* | **The roadmap drifts into performance management** through three individually reasonable requests (SPM R-17). **Medium × High.** Mitigated by ADR-025's forbidden-column table, the absence of any assessment column, and the standing review-checklist item. **This one has no technical fix — it is held by review discipline, and I am naming that rather than implying the schema solves it** |
| **TR-30** *(new)* | **The fitted-step backfill is wrong at scale and HR marks it reviewed anyway**, because reviewing 146 fitted steps is tedious and the button is right there. The gate then certifies a ladder nobody checked. **Medium × High.** Mitigated by showing `fit_deviation_pct` per person and sorting the review screen by it — the worst fits first — so a partial review still catches the worst cases. **Not fully mitigable** |
| **TR-31** *(new)* | **The Check B statistical machinery is deleted in the A1 clear-out** because it looks like the code A1 withdrew. **Medium × High.** Mitigated by T-200-13 being an explicit *retention* task with its own tests, and by the prohibition being written in §12.6.1 rather than implied |
| **R-1 / TR-24** | **Widened then narrowed.** A1 opened a new route (the naive `.0` backfill) and closed it (fitted step + reviewed gate). Net: **lower than Wave 2**, because an absolute reference raises far fewer findings than a 5% dispersion rule ever would |

### 12.9.4 New conflict-log entries

> The SPM's §12.3 register is authoritative and supersedes my §10.3 numbering. These are new, from Wave 4.

| ID | Conflict | Sev | Ruling |
|---|---|---|---|
| **CFL-42-35** | **§14.3.2 puts ladder configuration and roadmap authoring behind one `job_architecture:w` grant, but they need different audiences.** A manager must author roadmaps; a manager must not edit the company's job architecture. Granting `w` for the first hands them the second. | **High** | **Resolved — §12.4.5.** Three gates: reads on `job_architecture:r` (everyone), roadmap writes on `job_architecture:w` + row scope (managers included), **ladder configuration on `org_structure:w`** — which is seeded HR_ADMIN + PORTAL_ADMIN and **no manager**, needs no seed change, and has an in-repo precedent at `app/routes/org_change.py:381`. **SPM to ratify.** |
| **CFL-42-36** | **`reference_value` on `pay_equity_findings` is money in a `pay_equity`-gated table.** `reference_value × (1 + deviation_pct/100)` is the subject's salary. CFL-42-19 was ruled for computed compa-ratios; this is a **stored column** and inherits the same problem. | **High** | **Resolved — §12.6.4.** `reference_value` and `deviation_pct` render only to holders of **both** `pay_equity:r` and `compensation:r`; otherwise a band label. `GENDER_GAP` findings carry no `reference_value` at all, enforced by `chk_pef_shape`. |
| **CFL-42-37** | **The step tolerance must live on `job_levels`** for the `tolerance < increment/2` CHECK to be declarative — but the SPM put thresholds on `company_settings:w` (CFL-42-20) and the increment is money (`compensation:w`). A CHECK spanning two permission domains cannot be satisfied in one transaction from one screen. | Medium | **Resolved with a named consequence.** The increment **and** the tolerance are written together, gated `compensation:w`. The step tolerance therefore sits outside CFL-42-20's `company_settings:w` threshold set. **The alternative — a cross-table trigger instead of a CHECK — trades a guarantee for a permission boundary, and on the constraint that makes or breaks the feature (R-16) I take the guarantee. SPM to ratify.** |
| **CFL-42-38** | **A1 anchors step changes to "the performance review process", which does not exist.** The SPM ruled record-the-context-only (§14.5), and I agree — but the boundary is held by **review discipline, not by architecture**, and three reasonable increments cross it. | Medium | **Resolved as far as it can be — ADR-025 (§12.4.4).** The forbidden-column table, the absence of any assessment field, the audit allowlist, and a standing review-checklist item. **I am recording that this is a discipline control, not a technical one**, so nobody believes the schema is holding it. |

## 12.10 Technical-readiness verdict, re-issued against A1

### 12.10.1 Is EP42 still buildable as scoped?

**Yes. 21 stories, 175 tasks, 133.5 task-days → 90–110 dev-days, critical path 71.0, ≈14–16 calendar weeks.**
RAG **🟡 Amber**. Confidence **Medium** — one grade below Wave 2, and the reason is the amendment's size, not
any unknown in it. **I still have no unresolved architectural unknowns.**

**A1 is, on balance, good news for engineering, and I want that on the record because the effort table reads
the other way.** It removed a statistical reference nobody could reproduce by hand, took `percentile_cont`, a
coverage gate, group minimums and a whole family of small-group edge cases off the **primary** check, and made
the epic's largest story **cheaper**. What it added — expectations, roadmaps, a fourth code, pay points — is
mostly well-bounded CRUD over tables whose shape follows patterns already in this schema. **The +40.5 task-days
buy a feature that answers the owner's actual question rather than the one we inferred.**

### 12.10.2 The riskiest part — it has moved

**It is no longer KAN-188.** The SPM ratified ADR-016 and made the 330-cell before/after matrix a **release
gate**; the mechanism is unchanged but it can no longer be waved through. Still Critical if it fails, now much
less likely to.

**It is now the correspondence between three numbers that must be byte-identical:** the pay point Check A′
compares against, the pay point the step-change proposal pre-fills, and the pay point `fit_step()` fitted the
employee to. If any two diverge — by a cent, from a second implementation, from a linear derivation, from
rounding inside the loop instead of once at the end — the result is not a wrong number on a screen. It is a
**`PAY_BELOW_STEP` finding whose own "Propose adjustment" remedy does not clear it**, re-opening on every
re-evaluation, with no one able to explain why. That is the failure that would make HR stop trusting the
register, and it arrives through three entirely reasonable-looking pieces of code.

**Which is why `step_pay_point()` is one function** (§12.5.3), why the reference table is asserted **including
the 72,930.38 half-cent** (T-206-3), why the linear values are asserted **not** to match, and why T-192-8
asserts the pre-filled amount is byte-identical to the reference. Four controls on one arithmetic function is
not over-engineering; it is proportionate to a defect that presents as a haunting.

**Second-riskiest: TR-31, deleting Check B in the clear-out.** A1's language ("the statistical machinery is
withdrawn") is about the *primary* check, and the engineer doing the removal will be reading the same
sentences. T-200-13 is an explicit retention task for exactly this reason.

**Third: TR-29, the roadmap drifting into performance management.** No technical fix exists. Named as a
discipline control (CFL-42-38) rather than pretended away.

### 12.10.3 Blockers — re-issued

| # | Blocker | Owner | Status |
|---|---|---|---|
| **B-1** | **KAN-168 — the real-DB integration tier — is ⬜ not started** and hard-blocks KAN-200. | **SPM (Ruling 27)** | **UNCHANGED, and now correctly owned.** Promoted to P0 in the S2 enabler set and a hard entry condition for W4. If it slips, W4 slips and EP42 ships through W3. **Check A′ needs it no less than Check A did** — the exclusion constraints, the triggers, the `VALUES`-join and the `_IN_FORCE` predicate are all SQL semantics |
| **B-2** | Reconcile with the BA / UX / UAT Wave 4 outputs. **CFL-42-35, -36, -37 each change what the BA must write.** | ARCH + BA + UX + UAT | **RE-OPENED for Wave 4.** P0 before code |
| **B-3** | SPM acknowledgement of the ADR-016(c) correction | — | **✅ CLOSED.** Ratified in full (SPM A-1), with two additions actioned in §12.2 |
| **B-4** | OQ-9 ratification, now covering **three** rules plus the SYSTEM_ADMIN narrowing | SPM → owner | **Open, P1**, blocks KAN-198 only. The SPM has ruled and attached the cancel-remedy condition, which §12.2(c) delivers |
| **B-5** *(new)* | **DPO-1 gates Check B.** KAN-208 gives it data; it does not make processing that data lawful. Gender is a special category under GDPR Art. 9 on most readings, and the purpose-limitation question (a column collected for vacation eligibility, reused for a pay check) is untouched. | BA + DPO | **Open, P1**, blocks **T-200-13's release**, not its build. Build it, gate the enablement |

### 12.10.4 Stories I will not call technically ready

| Story | Verdict | What is missing |
|---|---|---|
| **KAN-200** | **NOT READY — still the only P0-grade one** | **B-1 (KAN-168).** Unchanged by A1: a simpler computation is not a verified one, and Check A′'s correctness now rests on constraints and triggers that mocks cannot exercise at all |
| **KAN-207** | **NOT READY — and this is a new entry worth reading** | Not for a technical reason. Its acceptance turns on **copy that reads as expectations rather than as an assessment** (SPM §14.3.3, UAT §7.3's must-be-walked-by-a-human list). That is not assertable by any test I can specify, and ADR-025's forbidden-column table constrains the *schema*, not the *sentences*. **KAN-207 is Ready when UX's copy has been reviewed by a human against the R-17 boundary, and not before.** I would rather say that than certify a story whose principal risk my tests cannot see |
| **KAN-202** | **NOT READY** | DEP-8 — the SPM's audit read-surface decision. Unchanged |
| **KAN-192** | **Buildable** | OQ-1 is **CLOSED** (the owner confirmed: not automatic), so its Wave 2 blocker is gone. OQ-A1-2 (propose-not-apply) carries a default and does not block |
| **KAN-206** | **Buildable, needs one ratification** | **CFL-42-37** — the step tolerance sits outside CFL-42-20's threshold set, gated `compensation:w` with the increment, so the CHECK is declarative. SPM to ratify; the build proceeds on the default |
| **KAN-190** | **Buildable, needs one ratification** | **CFL-42-35** — ladder configuration on `org_structure:w` rather than `job_architecture:w`. SPM to ratify; the build proceeds on the default |
| **KAN-203, KAN-204, KAN-208** | **READY** | Nothing outstanding. KAN-203 should start **first**; it closes a live P0 and depends on nothing |
| Everything else | **Ready once B-2 clears** | BA criteria and UX specs for the A1 deltas |

### 12.10.5 Revised priorities

| Priority | Item |
|---|---|
| **P0** | **KAN-203** (a live Critical defect, depends on nothing, start it first) · **B-1** KAN-168 scheduled now, not when W4 opens · **B-2** reconcile with BA/UX/UAT on CFL-42-35/36/37 · T-188-2/6/13 the matrix and its reversibility |
| **P1** | The critical path: 188 → 190 → 191 → 193 → 194 → 196 → 200 → 201 · **T-206-3/4** the pay-point function and the refused configuration · **T-191-11** `fit_step` · **T-198-7/8** the ≥2-satisfiable-levels rule (without it four-eyes does nothing) · **T-200-13** keep Check B · **B-4** OQ-9 · **B-5** DPO-1 |
| **P2** | KAN-189 · KAN-204 · KAN-208 · KAN-207 · KAN-199 · KAN-206 · KAN-195 · KAN-197 · KAN-192 · TD-25 the partial-rollback refusal |
| **P3** | KAN-205 · KAN-202 · TD-18 · TD-20 · TD-26 EP38's 403/404 inconsistency in the S5 sweep |
| **P4** | TD-16 · TD-27 · TD-28 · KAN-206's ladder-cost aggregate |

### 12.10.6 My verdict on A1

**Proceed. Start KAN-203 immediately and independently of everything else — it closes a live P0 and blocks
nothing. Hold the rest until B-2 clears; hold W4 until B-1 clears.**

**Four things I want the SPM to take from this amendment.**

1. **A1 made the hardest story smaller.** KAN-200 drops from 8.5 to 7.5 dev-days, loses `percentile_cont`, the
   coverage gate, the group minimums and a family of small-group edge cases from its primary path, and gains a
   check that works at `n = 1`. A better-specified requirement is the cheapest optimisation available, and this
   is the clearest example of it I have seen on this project.
2. **Three ratifications, all small, all with defaults being built against:** CFL-42-35 (ladder configuration
   on `org_structure:w` — no seed change, existing precedent, and it keeps managers out of the job
   architecture), CFL-42-36 (`reference_value` inherits CFL-42-19), CFL-42-37 (the step tolerance lives with
   the increment so the constraint can be declarative). **None blocks; all three change what the BA writes.**
3. **The four-eyes control was a silent no-op and I did not catch it.** V18: the seeded default chain is one
   level and no tenant has configured a workflow, so ADR-022 as I wrote it would have shipped, passed its
   tests, and bound nobody. The BA and UAT found it from two directions. **T-198-7/8 is not an enhancement to
   KAN-198 — it is the difference between KAN-198 existing and KAN-198 working**, and it should be read as
   part of the control rather than as scope on top of it.
4. **One boundary in this epic is held by review discipline and not by architecture.** ADR-025 constrains the
   schema, the audit allowlist and the review checklist, and none of that stops the third reasonable request
   from turning the roadmap into a rating system. **KAN-207 is not technically ready until a human has read
   the copy against the R-17 boundary**, and I would rather carry that as a named condition than certify
   around it.

*Amendment A1 applied. Everything above obeys `../../CLAUDE.md`. No task is done until `python -m pytest -q`
and the regression flow test pass with 0 failures, and no schema, guard or invariant change is approvable
without the corresponding documentation updated in the same commit.*
