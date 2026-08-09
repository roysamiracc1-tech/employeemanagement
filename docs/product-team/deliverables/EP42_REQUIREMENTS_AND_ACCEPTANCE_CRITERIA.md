# EP42 — Compensation, Job Architecture & Pay Equity — Requirements & Acceptance Criteria

> **Owner:** Business Analyst (`../03_BUSINESS_ANALYST.md`) · **Date:** 2026-08-09 · **Status:** Wave 2 — draft for SPM
> reconciliation (Wave 3).
> **Primary input:** `EP42_SPM_SCOPE_AND_DECISIONS.md` (Wave 1) — **authoritative** on scope, waves W0–W4, decisions
> D1–D8 and open questions OQ-1…OQ-9. Where the shared team brief and the SPM document disagree, **the SPM document
> wins** (see CFL-42-6; there are three tenants, not two).
> **Stage:** S1 — requirements finalisation (roadmap §E, D-004).
>
> **House style:** acceptance criteria follow `../../project-management/BACKLOG.md` — one backlog-style summary row per
> story, expanded into numbered, individually testable criteria with stable IDs (`AC-<story>-<nn>`). Every criterion
> appears in the traceability matrix (§21). Structure and depth match
> `EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`.
>
> **Guardrails obeyed.** `../../CLAUDE.md` is authoritative and is not re-litigated: the feature-access model, company
> scoping, the no-sub-flags rule, the four-place feature registration rule and the org-change invariants all bind
> EP42. Where a requirement pushes on one of them it is called out explicitly and routed to that invariant's owner.
> This document specifies **behaviour**, not schema — table design, indexes, migrations and interval conventions are
> the Senior Architect's. It does not re-decide SPM §4; where I disagree or find a hole, it is a numbered conflict or
> an open question, never a silent substitution.
>
> **Legal.** Everything touching GDPR, pay transparency and works councils is **flagged for DPO/legal validation**.
> Nothing here is legal advice (Charter §9.7). §4.7 is the resolution of **CFL-42-3** and is the section the DPO
> should read first.
>
> **Identifiers.** Epic **EP42**. Stories **KAN-188 … KAN-202**. `KAN-###` are local IDs, plain text, never links.
> Nothing existing is renumbered.

---

## 1. Scope

| Wave | Story | Title | MoSCoW · P (SPM §5) | Covered here |
|---|---|---|---|---|
| W0 | **KAN-188** | Tenant feature-exposure switch, centrally resolved (R7) | Must · P1 | Full (§5) |
| W0 | **KAN-189** | Effective date on org-change requests (resolves CFL-4 / `AC-185-07`) | Must · P1 | Full (§6) |
| W1 | **KAN-190** | Job families, levels and steps — per-company configurator (R6) | Must · P1 | Full (§7) |
| W1 | **KAN-191** | Assign every employee to a level and step; title→level mapping (R6, R2) | Must · P1 | Full (§8) |
| W1 | **KAN-192** | Step advancement, `promotion_eligible` signal, no automatic roll-up (R6, D3) | Must · P1 | Full (§9) |
| W2 | **KAN-193** | The effective-dated compensation record (R1) | Must · P1 | Full (§10) |
| W2 | **KAN-194** | Who may see a salary — three feature codes and row scoping (D5) | Must · P1 | Full (§11) |
| W2 | **KAN-195** | Backfill — bulk CSV and manual entry, coverage meter (R2, D7) | Must · P1 | Full (§12) |
| W3 | **KAN-196** | Pay decision inside the position-change request (R3, D4) | Must · P1 | Full (§13) |
| W3 | **KAN-197** | Promotion as a first-class request type (R4, D4e) | Must · P1 | Full (§14) |
| W3 | **KAN-198** | Four-eyes on money — segregation of duties (D4h) | Must · P1 | Full (§15) |
| W4 | **KAN-199** | Salary bands per level × pay market (D3.5) | Should · P2 | Full (§16) |
| W4 | **KAN-200** | The pay-equity comparison engine (R5, D1) | Must · P1 | Full (§17) — the arithmetic |
| W4 | **KAN-201** | Flag delivery, queue and lifecycle (R5, D2) | Must · P1 | Full (§18) |
| W4 | **KAN-202** | Compensation history read surface + audit coupling (D5.6) | Should · P2 | Full (§19) |

**Epic-level out of scope.** SPM §3.3 is adopted verbatim and is not restated. Two additions this document makes
explicit because they are the two things a reader of §4 will assume are in scope and they are not:

- **No retroactive pay recalculation of any kind.** A backdated compensation record changes what the *record* says
  was true from that date; it produces no arrears figure, no adjustment, no payroll instruction, and no recomputation
  of any previously-displayed number (§4.3, AC-193-19).
- **No statistical inference beyond the four arithmetic operations defined in §4.4.** No regression, no
  "explained/unexplained gap" decomposition, no controlled analysis, no confidence intervals, no significance
  testing. The product computes medians and ratios. Anything that models *why* a gap exists is a different product
  and would land squarely in the EU AI Act's employee-evaluation category (Charter §1, roadmap D-003).

---

## 2. Verified current-state baseline — BA additions

**SPM §2 rows S1–S16 are adopted as Known and are not re-derived.** The rows below are the ones the SPM's tasking
(§8.1 item 2) asked for and the ones I found while writing the criteria. Each is **Known** unless labelled otherwise,
verified in the code, schema or database on 2026-08-09 at the cited location.

| # | Fact | Evidence | Consequence for EP42 |
|---|---|---|---|
| **B42-01** | **One shared projection feeds six read surfaces.** `_EMP_SELECT` (`app/helpers.py:42-72`) is the single employee SELECT behind `fetch_employees()`, `/api/employees`, `/api/my-team`, the profile page, the directory and the admin employee list (`app/helpers.py:126-138`, `app/routes/employees.py:83,93,147,150,152,160`, `app/routes/admin.py:353,356`). | grep, cited lines | **The highest-probability leak path in the epic (SPM R-3).** Adding a salary column to `_EMP_SELECT` exposes it on six surfaces in one commit, three of which have no compensation gate. A UAT assertion on `_EMP_SELECT`'s column list is worth more than six per-surface assertions. |
| **B42-02** | **`/api/employees` is `@login_required` only** and does its scoping with a **hardcoded role list inside the handler** (`app/routes/employees.py:136-153`): SYSTEM_ADMIN / HR_ADMIN / **DEPARTMENT_HEAD / LOCATION_HEAD / HIRING_MANAGER** get the whole company; managers get `direct_report_ids()`; everyone else gets themselves. `/api/my-team` is `@require_roles('SOLID_LINE_MANAGER','DOTTED_LINE_MANAGER')`. | cited lines | Three roles that D5 defaults to **no pay access** (DEPARTMENT_HEAD, LOCATION_HEAD, HIRING_MANAGER) already receive the full company employee payload from an endpoint with **no feature gate at all**. If pay ever joins that payload it is exposed to exactly the roles D5 says must not see it. **AC-194-19 asserts the negative.** |
| **B42-03** | **`@require_feature_access` denies by `flash()` + `redirect(url_for('dashboard'))`** — a **302**, for HTML and JSON routes alike (`app/auth.py:102-115`). There is no JSON-aware variant. API routes that return 403 do so with hand-written checks *inside* the handler (`app/routes/org_change.py:197,200,222,232,327`). | cited lines | Every "returns `403`" criterion in this document (and in EP38's) is **not what the current decorator does**. A `fetch()` receiving a 302 to an HTML dashboard is the DEF-002 failure shape. Logged as **CFL-42-8**; the mechanism is the Architect's. |
| **B42-04** | **`_load_feature_access()` resolves the access of the *session user only*** — it reads `session['roles']` and caches on `g._feature_access` (`app/auth.py:38-95`). There is no function anywhere that answers *"does user X hold feature F in company C"* for a user who is not the caller. | cited lines | D4b requires checking, at create time, that **every chain step is satisfiable by an approver holding `compensation:r`**. That check cannot be written today. New capability, Architect's design. Logged as **CFL-42-12**. |
| **B42-05** | **`_can_initiate_for` does not stop an admin initiating for themselves.** It returns `True` for any holder of `HR_ADMIN`/`PORTAL_ADMIN`/`SYSTEM_ADMIN` **regardless of subject** (`app/routes/org_change.py:55-62`), and `POST /api/org-change/request` calls only that (`:199`). The manager branch self-blocks incidentally (`chk_not_self_manager` means nobody is their own manager). The `not is_own` test in `_can_transfer` (`app/routes/employees.py:126-131`) is **display only and says so**. | cited lines | `CLAUDE.md` org-change invariant 2 says an employee can **never** initiate their own move. It holds for managers and **does not hold for admins**. Today that buys an HR_ADMIN a self-requested desk move. After EP42 it buys them a **self-requested pay rise**. **Critical. CFL-42-14.** |
| **B42-06** | **The subject of a request can approve it.** `decide()` checks company and `_user_matches_step()`; `_user_matches_step` for a `ROLE` step is `step['approver_role'] in user['roles']` (`app/services/org_change_service.py:101-105, 222-262`). Nothing compares the decider to `req['employee_id']`. | cited lines | An HR_ADMIN who is the subject of an HR_ADMIN-approved request approves their own change. Combined with B42-05, one HR_ADMIN can raise **and** approve their own pay rise end-to-end on the default chain. **Critical. CFL-42-15.** KAN-198 must cover the subject, not only the multi-level case. |
| **B42-07** | **The default approval chain is a single HR_ADMIN step.** `_DEFAULT_STEPS` = one `ROLE`/`HR_ADMIN` level, applied whenever a company has no configured active workflow (`app/services/org_change_service.py:23-26, 32-45`). | cited lines | D4h's four-eyes rule is *"a user may not decide more than one level"*. On a one-level chain there is no second level, so in a **default-configured tenant the control decided in D4h is a no-op**. KAN-198 must also require ≥2 independently-satisfiable levels for money-bearing requests, or the control is decorative. **CFL-42-11.** |
| **B42-08** | **`_apply_change` closes `manager_relationships` with `is_current=FALSE` and never sets `effective_to`** (`app/services/org_change_service.py:381-385`), while the org-assignment close does set it (`:370-374`). The dev database currently holds **2 rows** with `is_current = FALSE AND effective_to IS NULL`. | cited lines; `psql -d employee -c "select count(*) from manager_relationships where not is_current and effective_to is null"` → 2 | `manager_relationships` is the pattern the SPM tells EP42 to copy for effective dating. **It is not clean.** KAN-189 must fix the manager-side close in the same change, or EP42 copies a defect. **CFL-42-9.** |
| **B42-09** | **`employees.gender` is NULL for all 147 rows**, is optional, and is populated only by employee self-service (`POST /api/profile/gender`, `app/routes/employees.py:176-186`), the admin registration form (`app/routes/admin.py:140`) and the CSV importer (`app/services/import_service.py:69-73`). It is documented as *"used only for vacation eligibility filtering"* (`docs/BUSINESS_DOCUMENTATION.md:245`) and is consumed only there (`app/helpers.py:269-280`). | `psql`: `select gender, count(*) from employees group by 1` → `NULL\|147`; cited lines | **D1's Check B has zero data and a purpose-limitation problem.** Zero gender coverage means Check B produces nothing on any seeded tenant, and reusing a field collected for leave eligibility to compute a pay gap is a **new purpose** under Art. 5(1)(b). §4.7.3 and AC-200-24…28. **DPO decision required before Check B ships.** |
| **B42-10** | **`locations.country` is free text `varchar(100)` with no normalisation and inconsistent real values.** Acme: `Germany`, `Portugal`, `Estonia`. Telia: `Sweden`, `Norway`, `Denmark`, `Finland`, `Estonia`. "Sam Cpmapny": `INDIA`, `UK`, `US`. There is also **one company-less location** — `Wroclaw IT center`, `Poland`, `company_id IS NULL`. | `database/schema.sql:445-452`; `psql` join of `locations`→`companies` | D1's default *"one pay market per `locations.country`"* is a **grouping on dirty free text**. `Germany` and `GERMANY` would be two markets. The company-less location must never appear in any tenant's market list. Normalisation and exclusion rules: AC-199-04…07. |
| **B42-11** | **One ACTIVE Acme employee has a current org assignment with `location_id IS NULL`.** `employee_org_assignments.location_id` is nullable (`database/schema.sql:355-370`). No employee lacks a current assignment. | `psql` group-by over `employee_org_assignments` where `is_current` | Pay market is derived from the current assignment's location. That employee is in **no** pay market and therefore in **no** comparison group. Acme's maximum achievable group population is **45 of 46**. The coverage meter must show this as a distinct reason, not as "no salary". AC-200-08, AC-195-14. |
| **B42-12** | **The CSV importer cannot write a valid `employment_type`, and fails silently when it tries.** `EMPLOYMENT_TYPES = {'FULL_TIME','PART_TIME','CONTRACTOR','INTERN'}` (`app/services/import_service.py:16`) — it **includes `FULL_TIME`, which the DB CHECK rejects, and omits `PERMANENT`, which the DB requires** (`database/schema.sql:421-422`). A blank cell defaults to `'FULL_TIME'` (`:63`, `:152`) and the INSERT then violates `employees_employment_type_check`; the exception is swallowed and the row is marked `SKIPPED` (`:161-165`). | cited lines | **Live defect, pre-existing, and directly material.** D1 keys its exclusions (`CONTRACTOR`, `INTERN`) and its FTE handling (`PART_TIME`) on `employment_type`. KAN-195 reuses the EP35-S2 import surface. Importing employees is currently the *only* bulk path and it cannot set the field the equity engine depends on. **DEF-42-1, §20.** |
| **B42-13** | **The analytics CSV export builds its column list from the result set** — `csv.DictWriter(buf, fieldnames=list(rows[0].keys()))` (`app/routes/analytics.py:310`), `Content-Disposition: attachment` (`:317`). | cited lines | Any compensation column that reaches an analytics query reaches the export **without anyone adding it to the export**. This is exactly SPM risk R-3's "a surface nobody listed". AC-194-22. |
| **B42-14** | **The search index is written by a DB trigger over four columns only** — `trg_employee_search AFTER INSERT OR UPDATE OF first_name, last_name, job_title, email` calling `fn_update_employee_search()` (`database/schema.sql:52-70, 1861`), and `employee_search_index` is **never written by application code** (EP38 B17, re-confirmed). | cited lines | Two consequences. (a) A **level title is not searchable** — searching "Junior Software Engineer" returns nothing unless the trigger or the search path changes; CFL-42-4 must cover this, not just display precedence. (b) A salary can only reach the index if someone adds a column to the trigger — a narrow, auditable surface. AC-191-18, AC-194-21. |
| **B42-15** | **The audit action vocabulary does not yet contain EP38's own erasure codes.** `ACTIONS` (`app/services/audit_service.py:73-90`) holds 16 codes and includes neither `EMPLOYEE_ANONYMISED` nor `ERASURE_REFUSED`, both of which EP38 `AC-184-33`/`AC-184-34` require. `RETENTION_CLASSES = {STANDARD, EMPLOYMENT, SECURITY}` (`:92`), and **`retention_class` is read by no code anywhere** — it is a label with no enforcement. | cited lines; repo-wide grep for `retention_class` outside `audit_service.py`/schema/migrations returns nothing | EP42's retention design cannot lean on an existing enforcement mechanism because there is none. §4.7.4 specifies the retention *rule* per entity and routes the *enforcement* to OQ-4 (no scheduler). The erasure codes are added alongside EP42's, all under CFL-42-2. |
| **B42-16** | **`company_features.is_enabled` defaults to `FALSE`** at the column level (`database/schema.sql:180-187`) and rows are created only by the SYSTEM_ADMIN toggler (`app/routes/analytics.py:119-135`), which writes **no audit row and takes no reason**. `GET /api/admin/company-features/<id>` LEFT JOINs, so an absent row currently reads as "not enabled" in the admin UI (`:174-190`). | cited lines | KAN-188's *"absent row defaults enabled for the eleven existing features"* is therefore **not** satisfiable by relying on the column default: either the migration materialises `TRUE` rows or the resolver carries a per-feature default. Behaviour is what matters (AC-188-05); the mechanism is the Architect's. The missing audit is AC-188-16. |
| **B42-17** | **`_analytics_enabled()` and `_si_enabled()` are two copies of the same three-line query** (`app/routes/analytics.py:20-31` and `app/routes/skills_intelligence.py:15-26`), and `enabled_for_hr` is still written and read by both (`analytics.py:109,127-131,144`; `skills_intelligence.py:183-209`). The locked-state precedent is `templates/admin/analytics_locked.html` (rendered at `analytics.py:184`); a sibling `templates/admin/skills_intelligence_locked.html` also exists. | cited lines; `find templates -iname '*lock*'` | KAN-188's retro-fit is assertable as a **static check**: after the story, `company_features` appears in `app/` only in the central resolver and the admin toggler. AC-188-13. |
| **B42-18** | **No compensation vocabulary exists anywhere.** A case-insensitive repo-wide grep for `salary|payroll|remuneration|wage|compa_ratio|job_level|pay_band` across `app/`, `database/`, `templates/` and `setup_db.py` returns **zero** matches. | `grep -rniE …` | Confirms SPM §1.3. Greenfield: there is no legacy naming, no partial implementation and no dead code to reconcile — and no existing test asserting the absence, which is what AC-194-20 adds. |
| **B42-19** | **Employment periods are not modelled.** `employees` carries a single `join_date` and a single `exit_date` (`database/schema.sql:404-425`); EP38 `AC-186-03` records that first-class employment periods are an **unresolved Architect design call**. | cited lines; EP38 §8 | *"Current salary"* is *"the latest record effective on or before today"*. After a rehire into the same `employees.id` (EP38 AC-186-02) that rule silently returns the **pre-exit** salary. §4.3.7 specifies the interim rule that makes this safe without waiting for employment periods. AC-193-21, AC-193-22. |
| **B42-20** | **Tenancy, re-verified independently of the SPM.** Telia 100, Acme Corp 46, one company-less record, "Sam Cpmapny" **0 employees / 3 locations**; 146 `PERMANENT` + 1 `CONTRACTOR`, **0 `PART_TIME`**, **0 `INTERN`**, all `ACTIVE`; Acme 46 employees / 41 distinct `job_title`; Telia 100 / 75. | `psql -d employee`, 2026-08-09 | Confirms SPM S1/S2/S4. **"Sam Cpmapny" is the epic's most valuable tenant fixture**: it exercises a zero-denominator coverage meter, an empty ladder, an empty equity queue and a tenant switch with nothing behind it. AC-195-17, AC-200-11, AC-190-14. |

---

## 3. Cross-cutting requirements

Numbered `CC-42-n` so they cannot collide with EP38's `CC-1…CC-20`. EP38's cross-cutting set continues to apply to
everything EP42 touches; the rows below are additional or sharpened.

### 3.1 Inherited invariants (`CLAUDE.md` — these always win)

1. **CC-42-1** No EP42 route uses a hardcoded `@require_roles(...)` list for a feature page or feature API. Every
   feature route is `@require_feature_access('<code>', '<action>')`; every nav affordance is
   `{% if has_feature_access('<code>', '<action>') %}`.
2. **CC-42-2** **No sub-flags.** No `enabled_for_hr`-shaped per-feature role gate is introduced, read or written by
   any EP42 code. A static check over the EP42 file set asserts zero references to `enabled_for_hr`.
3. **CC-42-3** SYSTEM_ADMIN bypasses feature checks automatically via `_load_feature_access()`; no EP42 code
   re-implements the bypass. **Exception, stated deliberately:** the four-eyes control (KAN-198) is a *business
   control*, not a feature check, and it binds SYSTEM_ADMIN too — see AC-198-09 and the reasoning there.
4. **CC-42-4** Any query listing or resolving *roles* for a company filters `company_id = %s::uuid` **only**, never
   `OR company_id IS NULL`.
5. **CC-42-5** Position changes, promotions and compensation reviews all run through
   `app/services/org_change_service.py`. EP42 adds request types and proposed fields; it does not create a second
   approval engine, a second apply path or a second notification vocabulary.
6. **CC-42-6** Multi-table units of work go through **one** `transaction()` boundary (KAN-155). `audit_service.record()`
   joins the caller's transaction and never opens its own.

### 3.2 Feature access model for EP42

7. **CC-42-7** Three feature codes are registered in **all four places** — `portal_features` in `setup_db.py`, a
   numbered migration under `database/migrations/`, **`database/seed_rbac.sql`**, and default `role_feature_access`
   rows **in both the migration and the seed**. `TestFeatureRegistryHasNoDrift` (`tests/test_regression.py`) must fail
   if any one of the four is missed. This is the DEF-004 lesson and it applies three times over.

   | Code | Label | Governs | Seeded `role_feature_access` defaults (SPM D5.1) |
   |---|---|---|---|
   | `compensation` | Compensation | Other people's pay in scope; entering and proposing pay; bands; backfill; history | `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w+d · `SOLID_LINE_MANAGER` **r** (row-scoped) · all others none |
   | `compensation_self` | My Pay | The "My Pay" panel on your own profile, hard-scoped to yourself | every role **r** (everyone is also an employee) |
   | `pay_equity` | Pay Equity | The equity queue, flags and their disposition | `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w · all others none |

8. **CC-42-8** All three codes are seeded `company_features.is_enabled = FALSE` for **every existing tenant**
   (SPM D6 req. 2, D8 safeguard, OQ-7). The capability is invisible until the product owner switches it on.
9. **CC-42-9** Defaults are a **ceiling a tenant may widen or narrow** through the existing Feature Access tab, and
   the implementation respects that with **no extra checks inside any route** (CC-42-2). Granting `compensation`
   read to any additional role through the matrix gives that role scoped access with **no code change**.
10. **CC-42-10** `r` / `w` / `d` are separable and mean exactly what §4.8.4 says. A holder of `r` only receives
    `403` **with no state change** from every mutating endpoint.

### 3.3 Tenant isolation

11. **CC-42-11** Every EP42 query is company-scoped `company_id = %s::uuid`. Tables without a `company_id` column are
    scoped by joining `employees` and filtering there (EP38 CC-9).
12. **CC-42-12** **There is no cross-tenant pay surface of any kind, for any role, including SYSTEM_ADMIN.** No
    comparison, no aggregate, no export, no count, no median that spans companies. A SYSTEM_ADMIN with **All
    Companies** selected sees a "select a company" state on every compensation and equity surface — not a merged
    list and not an empty one.
13. **CC-42-13** A SYSTEM_ADMIN performing any compensation **mutation** must have a company context selected
    (`session['admin_company_id']`); without one, the action is refused with a message naming the reason (EP38 CC-12).
14. **CC-42-14** Employee records with `company_id IS NULL` (SYSTEM_ADMIN accounts — EP38 B15) **cannot hold a
    compensation record or a level assignment at all**. The write is refused with a specific message; they appear in
    no coverage denominator, no group, no queue and no export.
15. **CC-42-15** Locations with `company_id IS NULL` (B42-10) never appear in any tenant's pay-market configuration,
    picker or grouping key.
16. **CC-42-16** Audit rows for EP42 events carry a non-null `company_id` taken from the **affected entity**, never
    from the session (existing `audit_service` rule).

### 3.4 Quality bars specific to money

17. **CC-42-17** **Monetary amounts are exact decimals, never binary floating point**, at every layer: storage,
    service, JSON payload and template. A value written and read back is byte-identical. Arithmetic follows §4.1.
18. **CC-42-18** **No amount is ever derived, estimated, imputed, defaulted or inferred** — not from a band, not from
    a level, not from a group median, not from a colleague, not from a prior period (D7.6). An absent value is
    absent and says so (§4.6).
19. **CC-42-19** **Absence must never be able to look like a value.** No blank, no dash, no `0`, no `—`, no
    `€0.00` in place of an unknown salary, on any surface, in any export, in any payload (D7.1).
20. **CC-42-20** **Every mutating EP42 endpoint is idempotent against double submission**: a replay returns `409`
    with the existing state and produces no second write and no second audit row (EP38 CC-16).
21. **CC-42-21** **No amount in any application log or error message** — the EP38 CC-17 bar (employee id and employee
    number only) extends to compensation values, compa-ratios, gap percentages and band boundaries.
22. **CC-42-22** New screens meet **WCAG 2.2 AA** at build time (roadmap D-004 / Q5); new DOM builders use the
    existing global `escH()` helper (`templates/base.html:661`).
23. **CC-42-23** `pytest` and both regression suites (`tests/ui/test_browser.py`, `tests/ui/test_vacation_workflow.py`)
    pass with zero failures, and the suites are **extended** to cover the flows EP42 changes — including at least one
    assertion that a salary is **absent from the payload** for a role without scope (not merely invisible).
24. **CC-42-24** **Every compensation screen carries the "Demo compensation data — synthetic" banner** while the
    environment is demo-grade (SPM D8.3 safeguard 2), and any compensation demo script states the A-2 disclosure —
    that under demo auth the visibility model is correct in code and unenforceable in practice.

---

## 4. Business rules pinned down

*SPM §4 decided the shape. This section states the arithmetic, the dating and the data-handling rules precisely
enough that two engineers implementing independently produce the same numbers. Everything here is enforced by the
numbered criteria in §5–§19. Where I have had to make a call the SPM did not, it is marked **[BA call]** and carries
its reasoning; where the call could reasonably go the other way it is also an open question in §23.*

### 4.1 Money, currency, precision and rounding

- **BR-1.1 Representation.** An amount is an **exact decimal with 2 fractional digits**, in the **major unit** of its
  currency (EUR 60000.00, not 6000000 cents). Never a binary float, at any layer (CC-42-17).
- **BR-1.2 Currency.** ISO 4217 alpha-3, uppercase, validated against a fixed list. Stored on every compensation
  record and every band. There is no company "default currency" that is silently applied — the currency is always
  explicit on the record. **[BA call]** — a defaulted currency is indistinguishable from a stated one, and the first
  time a tenant adds a second country it becomes a wrong value rather than a missing one.
- **BR-1.3 Range.** An amount must be **> 0**. Zero and negative are rejected at every entry point (form, API, CSV
  preview) with a field-level message. There is no "unpaid" compensation record; an unpaid person has **no** record.
- **BR-1.4 Upper bound.** A sanity ceiling of **100,000,000.00** per record, rejected above with a confirmable
  override for `compensation:w` holders (typo protection for currencies with small units — a JPY figure pasted into
  an EUR field). **[BA call]**, Low confidence on the constant; it is a guard, not a policy.
- **BR-1.5 Rounding.** All intermediate arithmetic is exact decimal with **no intermediate rounding**. Rounding is
  applied **once, at the final step**, mode **HALF_UP** (0.005 → 0.01). Monetary results round to **2** decimal
  places; ratios round to **3**; percentages are derived from the 3-dp ratio and displayed to **1** decimal place.
- **BR-1.6 Display and decision agree.** A threshold comparison uses the **same rounded value that the UI shows**.
  The consequence is explicit and must be documented in the UI: with 3-dp ratio rounding, a configured bound of
  `0.95` has an **effective boundary at 0.9495**. A value of 0.94951 rounds to 0.950 and is **not** flagged. This is
  deliberate, and it is stated so nobody "fixes" it later by comparing an unrounded value against a displayed one.
- **BR-1.7 No FX, no implicit conversion, ever.** Two amounts in different currencies are **never** compared, summed,
  averaged or converted. Where a comparison would require it, the group is not evaluated and says why (BR-4.14).

### 4.2 Annualisation and FTE normalisation

- **BR-2.1 Pay basis.** `ANNUAL` · `MONTHLY` · `HOURLY`. Mandatory on every compensation record.
- **BR-2.2 Company constants.** Two per-company settings, PORTAL_ADMIN-only, every change audited:
  `standard_annual_hours` (integer, default **1800**, range 500–2600) and `monthly_payments_per_year` (integer,
  default **12**, range 12–14).
- **BR-2.3 Annualisation.**

  | Pay basis | `annualised_base` |
  |---|---|
  | `ANNUAL` | `amount` |
  | `MONTHLY` | `amount × monthly_payments_per_year` |
  | `HOURLY` | `amount × standard_annual_hours` |

  **Why `monthly_payments_per_year` is configurable and not the constant 12.** Acme Corp has a Porto office
  (Portugal — B42-10 / SPM S3), where **14 monthly payments** is the statutory norm for base pay. Multiplying a
  Portuguese monthly salary by 12 understates it by roughly 17%, which is more than three times the 5% threshold the
  whole feature is built around — it would manufacture a pay-equity finding out of a payroll convention. This is not
  the "13th month as bonus" that §3.3 excludes; it is base pay expressed in a different number of instalments.
  **[BA call]**, Medium confidence on where the setting belongs (company vs pay market) → **OQ-BA-3**.
- **BR-2.4 FTE.** Decimal, 2 dp, range **0.01 – 1.00** inclusive. Mandatory on every compensation record; **default
  1.00** only where the employee's `employment_type` is not `PART_TIME`. For `PART_TIME` the value is **mandatory and
  has no default** — a defaulted 1.00 on a part-timer is the single most damaging silent error in the arithmetic
  (it makes the person look underpaid by exactly the amount they do not work). Values > 1.00 are rejected.
- **BR-2.5 FTE normalisation — and the trap.**

  | Pay basis | `fte_normalised_annual` |
  |---|---|
  | `ANNUAL` | `annualised_base ÷ fte` |
  | `MONTHLY` | `annualised_base ÷ fte` |
  | `HOURLY` | `annualised_base` — **FTE is not applied a second time** |

  **Why `HOURLY` is different.** An hourly *rate* multiplied by the company's *standard full-time annual hours* is
  already a full-time-equivalent figure. Dividing it by FTE as well double-counts the part-time reduction and
  inflates a 0.5 FTE hourly worker's comparable pay by 100%. FTE is still recorded on an hourly record (it is real
  information and it drives the UI's plain-language explanation), but it is **not** an input to normalisation.
  This is the most likely arithmetic defect in the epic; UAT's hand-computed fixtures must include it (AC-200-31).
- **BR-2.6 Worked example WE-1** — hand-computed; UAT uses these exact numbers.

  | # | `employment_type` | basis | amount | ccy | FTE | `annualised_base` | `fte_normalised_annual` |
  |---|---|---|---|---|---|---|---|
  | E1 | PERMANENT | ANNUAL | 60,000.00 | EUR | 1.00 | 60,000.00 | **60,000.00** |
  | E2 | PART_TIME | MONTHLY | 3,000.00 | EUR | 0.60 | 36,000.00 | **60,000.00** |
  | E3 | PERMANENT | HOURLY | 32.50 | EUR | 1.00 | 58,500.00 | **58,500.00** |
  | E4 | PART_TIME | HOURLY | 30.00 | EUR | 0.50 | 54,000.00 | **54,000.00** *(not 108,000)* |
  | E5 | PERMANENT | MONTHLY | 3,000.00 | EUR | 1.00 | 42,000.00 *(Porto, 14 payments)* | **42,000.00** |

- **BR-2.7 Exclusions from every comparison** (D1), each **counted and displayed**, never silent:
  `employment_type = 'CONTRACTOR'` · `'INTERN'` · `employment_status <> 'ACTIVE'` · no compensation record in effect
  on the evaluation date · no level assignment in effect · no pay market resolvable (B42-11) · currency mismatch
  with the group. `'PART_TIME'` is **included**, via BR-2.5.

### 4.3 Effective dating — the timeline rules

These apply to **compensation records** and **level/step assignments** alike, and KAN-189 brings the org-change
request into the same convention.

- **BR-3.1 Intervals are half-open, keyed on `effective_from`.** A record is in effect from and including its
  `effective_from` until, but excluding, the `effective_from` of the next non-voided record for the same employee and
  the same record type. **The requirement is the property, not the storage convention**: for any employee and any
  date D, **at most one** compensation record and **at most one** level assignment are in effect, and there is **no
  day covered by two**. Whether that is expressed as a half-open interval, an `effective_to = next − 1`, or a
  computed window is the Architect's call (CFL-4).
- **BR-3.2 "Current" is computed, never stored.** The record in effect *today* is derived by date comparison at read
  time. **There is no `is_current` flag on compensation.** This is a deliberate divergence from
  `manager_relationships` and `employee_org_assignments`, and it is load-bearing: with no scheduler (SPM S16), a
  stored `is_current` on a future-dated record would need a job to flip it and would therefore be wrong from the
  moment it is written. Flagged to the Architect (**CFL-42-16**) because the instruction to "copy the
  `manager_relationships` pattern" would produce the wrong answer here.
- **BR-3.3 Boundary semantics.** A record with `effective_from = D` is in effect **on D**. The preceding record's
  last effective day is **D − 1**. A query "what was this person paid on D" returns exactly one answer.
- **BR-3.4 Two changes on the same date are refused.** At most **one non-voided** record per
  `(employee, record type, effective_from)`. The second write returns `409`, names the existing record, and offers
  the correction path (void + new record on the same date, carrying a `supersedes` pointer). **Why:** with two
  records on the same date, "current salary" depends on insertion order, and the answer to a tribunal question
  becomes "it depends which row you read".
- **BR-3.5 Retroactive (backdated) records.** Permitted within a per-company **backdating window**, default **90
  days**, range 0–3650, PORTAL_ADMIN-configurable, audited. A backdated record:
  - is inserted into the timeline at its own date and **splits** it — every later record keeps its own period;
  - **does not** change what is currently in effect unless its date is later than the currently-effective record's;
  - **produces no arrears, no recalculation and no adjustment of anything** (CC-42-18, §1 out-of-scope), and the
    confirmation screen says so in plain language;
  - **is refused** if its date is before the employee's `join_date`, or before the start of the current employment
    period after a rehire (BR-3.7).
  - **Worked example WE-2.** Existing: R1 `2024-01-01 = 50,000`; R2 `2026-01-01 = 58,000`. Insert R3
    `2025-04-01 = 54,000`. Result: 50,000 for 2024-01-01→2025-03-31; 54,000 for 2025-04-01→2025-12-31; 58,000 from
    2026-01-01. **Current pay is unchanged at 58,000.** No equity re-evaluation is triggered, because the
    currently-effective record did not change (BR-4.19).
- **BR-3.6 Future-dated records.** Permitted within a per-company **forward window**, default **180 days**, range
  0–730. A future-dated compensation record is **inert**: it is not the current record, does not appear as the
  employee's pay, is not used by the equity engine, is excluded from coverage, and is labelled *"takes effect on
  <date>"*. It becomes current **by the passage of time** (BR-3.2) with no job and no flip.
  **A future-dated *placement* remains rejected** (EP38 R5.6 — with no scheduler it would either apply early or
  never). The two must not be conflated, and because KAN-189 makes placement and pay share **one** date, the
  consequence is a rule, not a preference:
  > **BR-3.6a** A `TRANSFER` or `PROMOTION` request may **not** carry a future effective date (placement moves).
  > A `COMPENSATION_REVIEW` request — pay only, no placement — **may**, within the forward window.

  This is a real tension created by the single shared date and is logged as **CFL-42-10**.
- **BR-3.7 Employment-period boundary (the rehire trap).** Because rehire reuses the same `employees.id` (EP38
  AC-186-02) and employment periods are not modelled (B42-19), "the latest record effective on or before today"
  would return the **pre-exit** salary to a rehired employee. Interim rule until employment periods land:
  - a compensation record is **not in effect** on any date D where the employee's `employment_status` is terminal
    and `D > exit_date`;
  - at the moment of rehire, every prior compensation record and level assignment is **closed at `exit_date`** and
    marked as belonging to the prior period;
  - the rehired employee shows **"No salary recorded"** and **"No level assigned"** until a new record is entered
    with `effective_from >= ` the new join date. Prior pay is **never** carried forward or restored (mirroring EP38
    AC-186-04 for roles);
  - a new record with `effective_from <= exit_date` of the prior period is refused.
- **BR-3.8 Dates are dates.** `effective_from` is a calendar **date**, interpreted in the company's locale, never
  derived from a client clock, never a timestamp. Comparisons use the server's current date. (`audit_log.created_at`
  is `timestamptz`; the two conventions coexist and must not be mixed in one comparison.)
- **BR-3.9 Voiding.** A record is never updated and never deleted (append-only, D-193). A correction is a **new**
  record; an erroneous record is **voided** — marked, retained, excluded from every computation, still visible in the
  timeline as voided with the actor and reason. Voiding requires `compensation:d`. Voiding the only record for an
  employee returns them to "No salary recorded", and that is a legitimate outcome.

### 4.4 The pay-equity engine — group formation, coverage and the two checks

*This is the section UAT builds hand-computed fixtures from. Every number below is arithmetic, not guidance.*

#### 4.4.1 Group formation

- **BR-4.1 The key.** `(company_id, job_family_id, job_level_id, pay_market_id)` — **never `job_title`, never step**
  (D1). Step is carried into a finding as an explanatory factor only.
- **BR-4.2 Pay market derivation.** From the employee's **current org assignment's** `location_id`
  (`employee_org_assignments` where in effect on the evaluation date) → that location's pay market. An employee whose
  current assignment has `location_id IS NULL`, or whose location belongs to no pay market, is in **no group** and is
  counted under the reason **"no pay market — location not set"** (B42-11: this is one real Acme employee today).
- **BR-4.3 Two populations, and confusing them is how the meter lies.**

  | Term | Definition |
  |---|---|
  | **Group population** | ACTIVE employees of the company, with `employment_type IN ('PERMANENT','PART_TIME')`, holding a **level assignment in effect** on the evaluation date, whose pay market resolves — i.e. everyone the group key can be computed for. |
  | **Compared set** | Members of the group population who **also** hold a compensation record in effect on the evaluation date, with `fte > 0` and a currency equal to the group's currency. |
  | **Group coverage** | `|compared| ÷ |population|`, as a percentage, HALF_UP to **1 dp**. |

  An employee with **no level assignment is in no group at all** and therefore appears in **neither** number. They
  are counted only in the *level* coverage meter (KAN-191). **There are two coverage figures in this product and
  they have different denominators; every screen that shows one must name which.** **[BA call]** — the SPM's D7
  specifies a single "coverage" and the distinction is unavoidable once the group key requires a level.
- **BR-4.4 Zero denominator.** Where `|population| = 0`, coverage is displayed as **"—  (no employees in scope)"**.
  It is **never** rendered as 0% or 100%, the gate is not met, nothing is evaluated and no flag is produced. (This is
  the "Sam Cpmapny" case, B42-20.)
- **BR-4.5 Coverage gate.** Per-company, default **80.0%**, range 50–100, PORTAL_ADMIN-only, audited. Evaluated
  **first**, before any check. Below the gate the group state is `NOT_EVALUATED_COVERAGE`, it reports
  *"insufficient coverage — not evaluated"*, and it produces **zero** flags. Comparison uses the 1-dp rounded value:
  **79.9% → not evaluated; 80.0% → evaluated.**
  - **WE-3.** population 12, compared 9 → 75.0% → not evaluated, even though 9 ≥ 3.
  - population 10, compared 8 → 80.0% → evaluated.
- **BR-4.6 Company gate.** Equity is disabled for a company until its **overall** compensation coverage crosses the
  gate at least once (D7.4). Until then the queue shows the coverage meter and the missing list — never an empty
  "no findings" state.
- **BR-4.7 k-anonymity on the coverage view.** Where `|population| ≤ 2`, the group is listed with its **counts
  only** — no median, no statistic, no ratio, no band position — to any audience. With a group of 1 or 2, a
  statistic is a colleague's salary with one arithmetic step removed. **[BA call]**, and it is a privacy requirement,
  not a nicety.

#### 4.4.2 Check A — individual outlier

- **BR-4.8 Basis selection.** If a **band** exists for `(job_level, pay_market)` and is in effect on the evaluation
  date → basis `BAND_MIDPOINT`. Otherwise → basis `GROUP_MEDIAN`. The basis actually used is **recorded on the flag
  and displayed**; a finding whose comparator is unstated is not actionable.
- **BR-4.9 Minimum group size.** `|compared| >= 3`. Below it: `INSUFFICIENT_GROUP`, **never a flag**. Boundary:
  2 → not evaluated; 3 → evaluated.
  - **Property to state on screen:** with `|compared| = 3` and a `GROUP_MEDIAN` basis, the middle member's ratio is
    exactly 1.000 and can never be flagged. With `|compared| = 2` the median is the midpoint and both members are
    equidistant from it, so both flag or neither — arithmetically useless, which is the justification for n ≥ 3.
- **BR-4.10 Median.** Over the **multiset** of `fte_normalised_annual` values of the compared set, ascending:
  odd n → the middle value; **even n → the arithmetic mean of the two middle values**, exact decimal, HALF_UP to 2 dp.
  Duplicates count as separate members. **The subject's own value is included** in the median of their own group.
  - **Alternative considered and rejected:** a leave-one-out median (excluding the subject) is arguably a better
    outlier statistic, but it makes the comparator *different for every row in the queue*, which an HR business
    partner cannot explain to the person they are discussing. Recorded so it is not reopened casually.
- **BR-4.11 Ratio.** `ratio = fte_normalised_annual ÷ comparator`, HALF_UP to **3 dp**, where `comparator` is the band
  midpoint or the group median per BR-4.8.
- **BR-4.12 Thresholds and boundaries.** Defaults: flag when `ratio < 0.950` (LOW) or `ratio > 1.100` (HIGH). Both
  comparisons are **strict**; exactly 0.950 and exactly 1.100 are **not** flagged. Configurable per company: low
  bound 0.50–1.00, high bound 1.00–2.00, PORTAL_ADMIN-only, audited. Per BR-1.6 the effective boundaries are 0.9495
  and 1.1005.
- **BR-4.13 One person, one finding.** Never pairwise. A group of ten produces at most ten findings, not 45.
- **BR-4.14 Currency guard.** If the compared set contains more than one currency, the group is
  `NOT_EVALUATED_CURRENCY`, produces **zero** flags, and raises a configuration warning to `pay_equity:w` holders.
  No conversion, no 1:1, no "mostly EUR" (BR-1.7).
- **BR-4.15 Worked example WE-4** — Acme · Engineering · L3 · Germany, `GROUP_MEDIAN` basis, all EUR.

  | Compared | `fte_normalised_annual` |
  |---|---|
  | A | 54,000.00 |
  | B | 58,500.00 |
  | C | 60,000.00 |
  | D | 61,000.00 |

  n = 4 (even) → median = (58,500.00 + 60,000.00) ÷ 2 = **59,250.00**.
  A: 54,000 ÷ 59,250 = 0.911392… → **0.911** → < 0.950 → **FLAG (LOW)**.
  B: 0.987341… → **0.987** → no flag. C: 1.012658… → **1.013** → no flag. D: 1.029536… → **1.030** → no flag.
  **One flag, on A.**

  Add E = 90,000.00 → n = 5 (odd) → median = **60,000.00**. A: 0.900 → FLAG (LOW). B: 0.975 → no. C: 1.000 → no.
  D: 1.017 → no. E: 1.500 → **FLAG (HIGH)**. **Two flags.** *(The mean of the same five values is 64,700, which
  would give A a ratio of 0.835 and E 1.391 — the mean moves every member's answer because of one salary. This is
  the D1 median-not-mean decision, demonstrated.)*
- **BR-4.16 Worked example WE-5 — boundaries.** Median 60,000.00. 57,000.00 → 0.950 → **not** flagged.
  56,999.99 → 0.9499998 → rounds to 0.950 → **not** flagged. 56,940.00 → 0.949 → **flagged**.
  66,000.00 → 1.100 → **not** flagged. 66,060.00 → 1.101 → **flagged**.
- **BR-4.17 Worked example WE-6 — band basis.** Band L3 × Germany: min 54,000, **mid 62,000**, max 72,000, EUR.
  A at 54,000 → 0.871 → FLAG (LOW), and **in band** (at the minimum) — the out-of-band flag is a separate,
  independent signal (BR-4.22). E at 75,000 → 1.210 → FLAG (HIGH) **and** out-of-band high.

#### 4.4.3 Check B — group gender pay gap

- **BR-4.18 Formula.** `gap = (median_male − median_female) ÷ median_male`, over the compared set of the group, using
  `fte_normalised_annual`. Each median follows BR-4.10. Result HALF_UP to **3 dp**; displayed as a percentage to
  1 dp.
- **BR-4.19 Minimums.** `|compared| >= 5` **and** at least **2 compared MALE** and **2 compared FEMALE**. Below any
  of these: `INSUFFICIENT_GENDER_GROUP`, **never a flag**. A single-gender group is never evaluated.
- **BR-4.20 Gender coverage sub-gate. [BA call]** Additionally, **≥ 80% of the compared set must have a recorded
  gender**. Below that, Check B is `NOT_EVALUATED_GENDER_COVERAGE`, produces zero flags, and reports
  *"gender not recorded for n of m compared"*. **Why this is necessary and the SPM did not have it:** `gender` is
  NULL for **100% of the seeded population** and is populated only by employee self-service (B42-09). A gap computed
  over a self-selected minority of a group is not a weak number, it is a **biased** one, and it is the exact shape of
  the "first wrong finding" D1 exists to prevent.
- **BR-4.21 `OTHER` and unrecorded.** Employees with `gender = 'OTHER'` or NULL are **excluded from Check B's
  medians** (there is no third median to compare against) and **counted and displayed**. They remain fully in
  Check A. The screen states this; silently dropping them is both a data-quality lie and a dignity failure.
- **BR-4.22 Threshold, direction and boundary.** Default **5.0%**, range 1–50, per company, PORTAL_ADMIN-only,
  audited. Flag when `|gap| >= threshold` — **inclusive**, so exactly 5.0% flags. The **signed** value and its
  **direction** ("in favour of MALE" / "in favour of FEMALE") are recorded and displayed. A gap in either direction
  is a finding, because the product measures rather than concludes (D1.3).
- **BR-4.23 Degenerate.** `median_male = 0` is impossible (BR-1.3) but is defended against: the group is
  `NOT_EVALUATABLE_DATA`, zero flags, and an integrity warning is raised to `pay_equity:w` holders.
- **BR-4.24 Worked example WE-7.** Group of 8 compared: 4 MALE, 3 FEMALE, 1 unrecorded. Gender coverage
  7 ÷ 8 = 87.5% ≥ 80% → evaluable.
  MALE: 60,000 / 62,000 / 66,000 / 70,000 → median (62,000 + 66,000) ÷ 2 = **64,000.00**.
  FEMALE: 57,000 / 58,000 / 61,000 → median = **58,000.00**.
  `gap = (64,000 − 58,000) ÷ 64,000 = 0.09375` → **0.094** → **9.4% ≥ 5.0% → FLAG**, direction *in favour of MALE*.
  Reversed medians (male 58,000, female 64,000) → `gap = −0.103448…` → **−0.103** → |10.3%| → **FLAG**, direction
  *in favour of FEMALE*.
  Boundary: male median 60,000, female median 57,000 → `gap = 0.050` → exactly 5.0% → **FLAG** (inclusive).

#### 4.4.4 Evaluation, re-fire and the anti-fatigue rule

- **BR-4.25 Cadence.** Event-driven plus on-demand, **no batch** (SPM S16 — there is no scheduler). A group is
  re-evaluated when: a compensation record that becomes the currently-effective one is written or voided; a level or
  step assignment changes; an employee joins or leaves the group (including via offboarding, transfer or a location
  change); a band changes; or any threshold, minimum, gate or pay-market definition changes. Plus a manual
  **"Run equity check"** on the queue, available to `pay_equity:w` holders.
- **BR-4.26 A backdated record that does not become the currently-effective one triggers no re-evaluation**
  (WE-2). Stated because the naive implementation re-evaluates on every write.
- **BR-4.27 Suppression key.** `(subject_employee_id, group_key, check_code, basis_code)`.
- **BR-4.28 Validity window.** A `JUSTIFIED` flag suppresses re-firing on the same suppression key for a per-company
  **validity window**, default **12 months**, range 1–60 months, audited.
- **BR-4.29 Early re-fire — stated as arithmetic, because "threshold + 2 percentage points" is ambiguous for a
  ratio bound. [BA call]** A suppressed condition re-fires before its window expires if **any** of:

  | # | Condition | Precise test |
  |---|---|---|
  | (a) | The gap widens materially — Check A LOW | `ratio < (low_bound − 0.020)` |
  | (a) | The gap widens materially — Check A HIGH | `ratio > (high_bound + 0.020)` |
  | (a) | The gap widens materially — Check B | `|gap| >= (threshold + 0.020)` (i.e. +2 percentage points) |
  | (b) | The subject's own facts change | any change to the subject's level, step, or currently-effective compensation record |
  | (c) | The configuration changes | any change to a threshold, group minimum, coverage gate, pay-market definition, or a band for that level × market |

- **BR-4.30 A re-fire raises a NEW flag.** The justified flag stays `JUSTIFIED` with its reason and category intact
  and is linked as `superseded_by` the new one. Re-opening the old flag would overwrite a disposition somebody made
  and signed, which is the record the feature exists to produce. **[BA call]**, High confidence.
- **BR-4.31 Historical results are never recomputed.** An evaluation records the values it used (medians, counts,
  thresholds, coverage) at the moment it ran. A later change produces a new evaluation, not a rewritten one.

### 4.5 The job ladder — validity rules

- **BR-5.1 Family.** Company-scoped. Name mandatory, ≤ 150 chars, **unique within the company case-insensitively
  after trimming**. The product ships **no** families (D3.2 — no opinionated ladder).
- **BR-5.2 Level.** Belongs to exactly one family. Carries `ordinal` (integer ≥ 1), `title` (mandatory, ≤ 150 chars,
  unique within the family case-insensitively after trimming) and `steps_count` (integer, default **5**, range
  **1–12**).
- **BR-5.3 Ordinals are contiguous from 1 with no gaps.** Creating level 3 when only levels 1 and 2 exist is
  permitted (it appends); creating level 5 when the highest is 2 is **refused**. **Why:** promotion and the
  "last step" signal both need a deterministic *next* level; a hole makes "the next level" undefined.
- **BR-5.4 Reordering.** Levels may be reordered freely **while the family has zero assignments, current or
  historical**. Once any assignment exists, **ordinal positions are frozen**; new levels may only be **appended above
  the current highest ordinal**. Renaming a level's title remains permitted at all times and is audited. (SPM D3 /
  KAN-190 backlog criteria.)
  - **Consequence, stated rather than hidden:** a company that later needs a level *between* 2 and 3 has **no path**
    other than creating a new family and re-mapping. Recorded as **OQ-BA-2** with a recommendation.
- **BR-5.5 Steps.** Steps are implicit `1 … steps_count`, displayed `<ordinal>.<step>` (e.g. `1.1`, `1.5`, `3.2`).
  They are not separately created. **Increasing** `steps_count` is always allowed. **Decreasing** it below the
  highest step currently assigned to any employee (current assignment) is **refused**, naming the count of affected
  employees and the highest step in use.
- **BR-5.6 Deletion.** A level or family referenced by **any** assignment — current **or** historical — cannot be
  deleted; the attempt returns `409` and offers **archive** instead. An archived level accepts no new assignments,
  disappears from pickers, keeps its existing assignments and still participates in historical grouping. A level with
  no assignment in its entire history may be deleted only if it is the **highest** ordinal in its family (otherwise
  it would create a gap, BR-5.3). Every delete and archive is audited.
- **BR-5.7 Assignment.** An employee holds at most **one** level assignment in effect on any date (BR-3.1). An
  assignment names `(family, level, step)`; the level must belong to the family and the step must be within
  `1 … steps_count`. All three are mandatory — there is no "level without a step".
- **BR-5.8 The last-step signal is a signal.** A `promotion_eligible` marker is raised on the assignment when, and
  only when, an assignment **becomes** current with `step == steps_count`. It is **not** raised again for an
  unrelated later edit that leaves the step unchanged, and it is **not** raised at all when the level is the
  **highest ordinal in its family** (there is no next level — the UI shows "top of ladder" instead). **[BA call]** on
  both edges; neither is in D3.
- **BR-5.9 The signal can be un-raised.** If `steps_count` is later increased (5 → 7), an employee at step 5 is no
  longer at the last step: the marker is **cleared** and its notification **retired** for every recipient. Leaving a
  stale "eligible for promotion" in somebody's bell after the ladder changed under them is the DEF-003 failure mode
  wearing a new hat.
- **BR-5.10 Direction is recorded. [BA call]** Because SPM D3.4 routes skip-step, skip-level **and downward** moves
  through the same `PROMOTION` request type, a demotion would be recorded as a promotion and every promotion metric
  would be wrong. The request and the resulting assignment therefore carry a derived, recorded
  `level_direction ∈ UP · DOWN · LATERAL` (comparing `(ordinal, step)` before and after). This does not change D4e's
  request-type decision; it makes the data readable.
- **BR-5.11 The working title survives.** `employees.job_title` is **not** dropped, renamed or repurposed in this
  cycle. It stays free text, stays indexed (`idx_employees_job_title`), stays in the search trigger (B42-14), and is
  relabelled in the UI as **"Working title"**. Precedence (CFL-42-4, SPM's steer adopted):

  | Surface | Shows |
  |---|---|
  | Directory row, org-tree card, profile header, `/api/employees`, `/api/my-team` | **Level title**, canonical. Working title in parentheses where both exist and differ. |
  | Employee has a level, no working title | Level title alone |
  | Employee has a working title, no level | Working title alone, plus a "No level assigned" marker to `compensation:r`/ladder-admin holders |
  | Employee has neither | **"No job title recorded"** — never blank |
  | Level title and working title are identical (case-insensitive, trimmed) | Show once, not twice |
  | Full-text search | **Both** must match. This does **not** work today (B42-14) and is a required change, not a display decision. |
  | Equity grouping | **Neither title.** The key is `job_level_id` (BR-4.1). |

### 4.6 Behaviour while the data is partial — the surface matrix

Per SPM D7 the product must be correct and honest at 40% coverage, not only at 95%. Every cell below is a testable
expectation. States: **N** = no level, no salary · **L** = level, no salary · **S** = salary, no level ·
**B** = both · **X** = contractor/intern · **T** = non-ACTIVE (leaver) · **U** = viewer lacks `compensation:r`.

| Surface | N | L | S | B | X | T | U |
|---|---|---|---|---|---|---|---|
| Profile → Compensation panel | "No salary recorded" + **Record salary** action | same | amount + "No level assigned" | amount, level, step | **"Not applicable — Contractor"** (no Record action) | last record, labelled "as at exit date <d>" | **panel absent from the page and from the payload** |
| **My Pay** (`compensation_self`) | "No pay information recorded. Contact HR." | same | amount, no level line | amount, level title, step, position-in-range in words | "Not applicable — Contractor" | as at exit date | n/a (self-scope is its own code) |
| Directory row / org-tree card | working title or "No job title recorded" | level title | working title | level title (+working in parens) | as others | absent (non-ACTIVE filtered) | **no pay field in the payload at all** |
| Move modal → compensation block | "No current salary recorded" as context; New salary permitted | same | amount shown as context | amount shown as context | block shows "Not applicable — Contractor"; New salary disabled | subject not transferable (EP38 AC-185-12) | **block absent, not disabled** |
| Compensation coverage meter | counted in the **missing** list, reason "no salary" | counted in **missing**, reason "no salary" | counted as **covered** | covered | **excluded from the denominator**, reason "not applicable" | excluded (not ACTIVE) | meter absent |
| Level coverage meter (KAN-191) | counted in **missing**, reason "no level" | covered | missing | covered | counted (levels apply to contractors) | excluded | visible to ladder admins |
| Equity group population | **not in any group** | in population, **not** in compared set | not in any group (no level) | in population and compared | **excluded from the population** | excluded | queue absent |
| Equity queue row | n/a | n/a | n/a | may appear | never | never | n/a |
| Any CSV export | reason string, never a blank cell | reason string | amount if in scope | amount if in scope | "Not applicable — Contractor" | as at exit date | **column absent from the file** |
| Full-text search | unchanged | unchanged | unchanged | unchanged | unchanged | unchanged | **never indexes an amount** |

- **BR-6.1** *"Not applicable — <employment type>"* and *"No salary recorded"* are **two different states that must
  never look like each other**, because conflating them makes the coverage meter lie (D7.7). One is a designed
  exclusion; the other is missing work.
- **BR-6.2** The coverage meter states its denominator in words — e.g. *"Compensation data: 62% of active employees
  (91 of 146). Excludes 1 contractor and 0 interns."* A percentage without its denominator is not an adoption
  instrument, it is a number.
- **BR-6.3** The missing list is exportable to CSV, carries the **reason** per row (no salary · no level · no pay
  market · not applicable), and contains **no amounts**.

### 4.7 GDPR — lawful basis, retention and erasure for compensation (**resolution of CFL-42-3**)

> **This section is mine to close (SPM §8.1 item 5) and it amends my own EP38 §4.3.** EP38's R3.6 (what erasure
> removes) and R3.7 (what survives) enumerate every table in the product and **do not mention pay, because pay did
> not exist**. Left alone, an erasure would either destroy pay history that tax and employment law require be kept,
> or retain identifying pay data that should have gone.
>
> **Flagged for DPO/legal validation.** The *mechanisms* below are product requirements whatever the answer; the
> *periods* and the *lawful bases* are proposals requiring confirmation per jurisdiction. I do not give legal advice
> (Charter §9.7).
>
> **Where this lands.** EP38 §4.3 R3.6/R3.7 are amended by §4.7.4 and §4.7.5 below. `docs/BUSINESS_DOCUMENTATION.md`
> §4 (which still says employee records are *"retained regardless of `employment_status`"* — EP38 CFL-3) and
> `docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` (which has no compensation feature) are **mine** and I will correct
> them **in the same commit as the KAN-193/KAN-194 implementation**, not now (Charter §5b rule 1; SPM CFL-42-7).

#### 4.7.1 Controller / processor

Unchanged from EP38 §4.3: the **tenant company is the controller**, the portal operator is the **processor**.
Consequence for EP42: retention periods, erasure decisions and the decision to run a gender-gap computation at all
are **per-company configuration**, not platform policy. The platform supplies the controls and the record; it does
not decide for the tenant.

#### 4.7.2 Lawful basis — proposed, **Needs Validation**

| Data | Purpose | Proposed lawful basis |
|---|---|---|
| Compensation record **during** employment | Administering the pay term of the employment contract | **Art. 6(1)(b)** performance of a contract; **Art. 6(1)(c)** where tax/social-security/pay-transparency law compels the record |
| Job family / level / step **assignment** | Job classification, org design, progression | **Art. 6(1)(b)**; **Art. 6(1)(f)** legitimate interests for workforce planning |
| Compensation history **after exit**, within retention | Tax and employment record-keeping; defending equal-pay and unfair-dismissal claims | **Art. 6(1)(c)** legal obligation; **Art. 6(1)(f)** establishment/exercise/defence of legal claims. **Limitation periods for equal-pay claims are long in several of the seed jurisdictions — DPO to state the period per jurisdiction** |
| **Check A** (individual outlier) | Internal pay governance | **Art. 6(1)(f)** legitimate interests, with a balancing test the controller must be able to produce |
| **Check B** (gender pay gap) using `employees.gender` | Pay-gap measurement | **Unresolved — see §4.7.3. This is the one that must not be assumed.** |
| Job families, levels, steps, pay markets, bands, thresholds | Configuration | **Not personal data.** No lawful basis needed; not in scope of erasure |
| Compensation import staging rows (raw CSV, including amounts) | Loading data | **Art. 6(1)(b)/(c)** as the underlying record, but **only for the duration of the import** — see §4.7.4 |

#### 4.7.3 The gender question — a purpose-limitation problem, not a permissions problem

**Observation.** `employees.gender` exists, is nullable, and is documented and used for exactly one purpose:
**vacation eligibility filtering** (`docs/BUSINESS_DOCUMENTATION.md:245`; `app/helpers.py:269-280`). It is populated
by employee self-service (`app/routes/employees.py:176-186`) and is **NULL for all 147 rows** (B42-09).

**Evidence of the problem.** Using data collected for leave eligibility to compute a pay-gap statistic is
processing for a **new purpose** under **Art. 5(1)(b)**. EP38 §4.3 already flagged this column for DPO review for
the *leave* purpose; there are now **two** purposes, which is itself the question. Separately, several
jurisdictions treat gender data in an employment context as requiring an **Art. 9** analysis even though gender is
not, in itself, a special category.

**Impact.** If the DPO rejects the reuse, Check B cannot run at all and D1's answer to R5 loses half its shape. If
it is built and shipped without the question being asked, the first works-council conversation finds it.

**Recommendation — product requirements that hold whatever the legal answer is:**

- **BR-7.1** Check B is **individually switchable per company**, independently of Check A, and is **OFF by default**.
- **BR-7.2** Check B cannot be switched on until a PORTAL_ADMIN records a **lawful-basis acknowledgement** — a
  free-text basis reference plus actor and timestamp, written to `audit_log`. The product does not judge the answer;
  it refuses to compute the statistic until the controller has recorded that they have one. This is the only
  mechanism available to a processor and it is cheap.
- **BR-7.3** The gender field's **purpose statement is shown at the point of collection** (`/api/profile/gender` and
  the registration form) and lists **both** purposes once Check B is enabled for that tenant. A purpose that changed
  after collection and was never disclosed is the failure mode.
- **BR-7.4** A subject may decline to record a gender, and the product must work with the gap that creates —
  BR-4.20's gender-coverage sub-gate exists precisely for this. Nothing anywhere pressures the subject to supply it
  (Charter §9.8, no dark patterns).
- **BR-7.5** No individual's gender is ever displayed on any equity surface. Check B publishes **group medians and
  counts only**, subject to BR-4.19's minimums.

**Expected outcome.** Check B is buildable, and the decision about whether it may lawfully run sits with the person
who can make it, recorded, per tenant.

**Evidence classification: Needs Validation. Owner: DPO, via SPM. This blocks KAN-200's Check B, not KAN-200.**

#### 4.7.4 Retention class per new entity — **the amendment to EP38 R3.7**

Using the existing `audit_log` vocabulary (`STANDARD` / `EMPLOYMENT` / `SECURITY`). **Note B42-15: `retention_class`
is a label with no enforcement anywhere in the product today.** The rules below are requirements on behaviour; the
enforcement mechanism inherits EP38 **OQ-4** (there is no scheduler), so the Must for this cycle is *a stated class,
a visible expiry, and a manual purge action*, with automatic expiry a Should.

| Entity | Personal data? | Class | Clock starts | At retention expiry |
|---|---|---|---|---|
| Job families / levels / steps / pay markets / bands / thresholds | **No** — company configuration | n/a | — | Retained indefinitely; untouched by any erasure |
| Level / step **assignment** history | Yes (pseudonymous) | **EMPLOYMENT** | `exit_date` | Free-text reason NULLed; **dates and level/step ids retained** (historical org and progression reporting must stay correct) |
| **Compensation records** | **Yes — the most sensitive class in the product** | **EMPLOYMENT** | `exit_date` | **The amount and currency are destroyed** and the row is marked `PURGED`, retaining `effective_from`, FTE, pay basis, level/step and the actor. The *shape* of the timeline survives; the *figure* does not |
| Pay-equity flags and dispositions | Yes (subject) | **EMPLOYMENT** | `exit_date` | Free-text disposition reason NULLed; category, state, dates and the **basis type** retained; the **measured value is destroyed** with the amounts |
| Compensation `audit_log` rows | Yes (pseudonymous) | **EMPLOYMENT** | `exit_date` | Free-text `reason` NULLed (EP38 R3.6). They contain **no amounts by construction** (D5.6), so there is nothing else to destroy |
| Compensation **import staging** rows (raw CSV including amounts) | **Yes — raw, unscoped, amount-bearing** | **STANDARD** | Completion of the import run | **Hard-deleted.** Default **30 days**, range 1–90, per company, audited. This is the one EP42 table that is genuinely deleted, and it is the one nobody would think of |

- **BR-7.6** The post-exit retention period is the **existing per-company setting** (EP38 R3.1, default **7 years**,
  min 1, max 30). EP42 introduces **no second retention clock** for pay. **[BA call]** — a separate pay clock would
  be the first thing to drift out of sync with the employee clock, and there is no evidence any tenant needs one.
  → **OQ-BA-6** if the DPO says pay must be kept longer than the employee record in some jurisdiction, in which case
  it becomes a per-class period and the shape changes.
- **BR-7.7** The retention screen (EP38 R3.2) gains a line per employee: *"Compensation history: n records, retained
  until <date>"*, and a company-level list of records **past** retention, oldest first.

#### 4.7.5 What erasure does — **the amendment to EP38 R3.6**

**The rule.** An Art. 17 erasure request against a leaver **does not destroy the compensation amount history at the
time of the request**, because retaining pay records is ordinarily a legal obligation for tax, social-security and
employment record-keeping, and **Art. 17(3)(b)** disapplies the erasure right where processing is necessary for
compliance with such an obligation. What makes that defensible rather than convenient is that after EP38's erasure
the record is already **pseudonymous**: name, email, phone and photo are tokenised (EP38 R3.6), and the pay figure
remains attached to `employees.id` + `employee_number`, which no longer resolve to a person by name.

**Because erasure no longer removes the figure, the retention period becomes the only storage-limitation control** —
which is why §4.7.4 destroys the amount at expiry rather than merely relabelling it. These two rules are a pair;
neither is safe alone.

| Data | On erasure |
|---|---|
| Compensation record — **amount, currency, FTE, pay basis, effective_from** | **Retained.** Art. 17(3)(b) / 17(3)(e). Destroyed later at retention expiry (§4.7.4) |
| Compensation record — **free-text reason** | **NULLed.** Reasons contain performance commentary, health context and named colleagues |
| Level / step assignment — ids, dates | **Retained** |
| Level / step assignment — free-text reason | **NULLed** |
| Pay-equity flag — subject link, state, category, dates | **Retained**, pseudonymous |
| Pay-equity flag — **free-text disposition reason and any narrative** | **NULLed** |
| Compensation import staging rows for the subject | **Deleted immediately**, not at the 30-day clock |
| `audit_log` rows for compensation actions | **Retained**, free-text `reason` NULLed (EP38 R3.6, unchanged) — they contain no amounts |
| Any exported CSV held on disk | Out of the product's control; named in the erasure confirmation so the actor knows |

- **BR-7.8 Partial refusal is a first-class outcome.** Where an erasure is executed but pay history is retained on
  Art. 17(3)(b) grounds, the system records an **`ERASURE_PARTIALLY_REFUSED`** outcome naming the **categories
  retained**, the **ground**, and the **date the retention expires** — so the subject can be told when it will go.
  This extends EP38 R3.4's binary execute-or-refuse. **Note B42-15: neither `EMPLOYEE_ANONYMISED` nor
  `ERASURE_REFUSED` is in the current `ACTIONS` enumeration, so EP38's own criteria are not implementable either.**
  All three codes are added under CFL-42-2.
- **BR-7.9 The erasure audit row contains none of the erased values and no amount** (EP38 R3.8, and D5.6).
- **BR-7.10 Erasure is refused outright while the employee is ACTIVE** (EP38 R3.4 operates on non-ACTIVE records
  only). A compensation record can never be erased "in passing" while somebody is employed.

#### 4.7.6 Subject access (Art. 15 / 20) — and the thing it must not disclose

- **BR-7.11** The subject's own compensation and level history **is their personal data** and is included in the
  EP38 R3.10 export: effective dates, amounts, currency, FTE, pay basis, level, step, level title, actor and reason.
- **BR-7.12** Where the subject has been the subject of a pay-equity flag, the export includes: the check, the
  **basis type** (band midpoint / group median), the threshold in force, their **own** ratio, the flag's state, and
  its disposition category. **[BA call]** — this is the Art. 15(1)(h)-shaped "meaningful information about the
  logic", and withholding it would be indefensible.
- **BR-7.13 And it must not include:** any other individual's amount, any individual's gender, the identity or
  headcount composition of the comparison group, or **any group statistic computed on fewer than 5 compared
  employees**. **[BA call]** — with `|compared| = 3`, disclosing the median discloses a colleague's salary to within
  one arithmetic step. The threshold of 5 mirrors Check B's minimum for the same reason.
- **BR-7.14** Where the subject asks *why* they were flagged and BR-7.13 prevents a full answer, the response states
  that the comparison group is too small to disclose a statistic without revealing a colleague's pay. That is an
  honest answer and it is the right one.

#### 4.7.7 Art. 22 and the EU AI Act

- **BR-7.15** No pay change, level change or step change is ever automatic (SPM D3.4, §3.3). Every consequence of
  every computation requires a **human decision with a recorded reason**, taken through the approval chain. The
  product therefore does not perform automated decision-making with legal or similarly significant effect.
- **BR-7.16** The equity engine produces a **measurement**, never a conclusion. Every equity screen carries
  plain-language framing that the product does not determine whether work is of equal value and does not decide
  whether a gap is objectively justified (D1.3). **No product surface and no documentation may claim or imply that
  the product makes a customer compliant with any pay-transparency regime** (SPM R-10).
- **BR-7.17** No algorithmic pay recommendation, market-matching score, "suggested increase" or predicted-attrition
  input to a pay decision, in this cycle or any other, without a compliance gate (§3.3).

#### 4.7.8 Interaction with offboarding (KAN-184) and rehire (KAN-186)

**Offboarding:**

- **BR-7.18** Offboarding **does not** delete, void or alter any compensation record. The record in effect at
  `exit_date` remains the last record of the employment; **no new record is created** and no "final pay" is computed
  (§3.3).
- **BR-7.19** The subject's **level/step assignment is closed with `effective_to = exit_date`**, exactly as manager
  relationships and org assignments are (EP38 R1.6). After offboarding, no level assignment for the subject is in
  effect on any date after `exit_date`.
- **BR-7.20** The subject leaves **every** equity group from the evaluation date forward. Historical evaluations are
  not recomputed (BR-4.31).
- **BR-7.21 Offboarding triggers a re-evaluation of every group the leaver was in** (BR-4.25). This is not
  housekeeping: removing a member changes the median and can drop a group below `n = 3` or below the coverage gate.
  Where that happens, **every OPEN flag in the affected group is auto-dispositioned `RESOLVED_BY_DATA`** with reason
  *"comparison group no longer evaluable"* and **retired from the bell of every eligible recipient** (D2, DEF-003).
- **BR-7.22** Any OPEN flag whose **subject** is the leaver is auto-dispositioned `RESOLVED_BY_DATA` with reason
  *"subject offboarded"* and retired for every recipient. Otherwise the queue accumulates items nobody can action —
  the exact DEF-003 shape.
- **BR-7.23** An open pay-equity flag **never blocks an offboarding**, and the offboarding pre-confirmation summary
  (EP38 AC-184-01) **does not mention pay-equity flags or amounts** — that summary is visible to
  `employee_lifecycle` holders, who are a different audience from `compensation:r` (the D5.6 argument, applied
  again).

**Rehire:**

- **BR-7.24** Prior compensation is **never restored, carried forward or defaulted** into the new employment period
  (BR-3.7). The rehire flow requires a **new** compensation record and a **new** level assignment before the employee
  appears in any pay surface, coverage denominator or comparison group. Until then: "No salary recorded",
  "No level assigned".
- **BR-7.25** Between `exit_date` and the new join date there is **no compensation record in effect**. A query for
  that period returns "not employed", not the old salary.
- **BR-7.26** Prior pay and level history remain visible to `compensation:r` holders on the timeline (KAN-202),
  **labelled with the employment period they belong to**. Tenure, seniority and continuous-service policy remain out
  of scope (EP38 §8).
- **BR-7.27** A record whose amount has been **purged at retention expiry** (§4.7.4) displays as
  *"Amount destroyed at retention expiry on <date>"* — not as zero, not as blank (CC-42-19). Rehire into an
  **anonymised** record remains forbidden (EP38 AC-186-06).

#### 4.7.9 Items requiring DPO / legal validation — the list, so it can be worked as one conversation

| # | Item | Blocks |
|---|---|---|
| **DPO-1** | Reuse of `employees.gender` — collected for leave eligibility — as the input to a pay-gap computation (§4.7.3). Purpose limitation, Art. 5(1)(b); Art. 9 analysis where a jurisdiction requires one | **Check B only**, not KAN-200 |
| **DPO-2** | Confirmation that pay history is on the **survive-erasure** list under Art. 17(3)(b)/(e), per jurisdiction (§4.7.5) | The retention class in KAN-193 |
| **DPO-3** | The retention period for pay records — EP38's 7-year default, and whether any seed jurisdiction requires longer than the employee record itself (BR-7.6) | Retention configuration only |
| **DPO-4** | Whether the lawful basis for Check A is Art. 6(1)(f) and whether a legitimate-interests balancing test must be producible per tenant | Documentation, not the build |
| **DPO-5** | Whether the product may state a measured gender pay gap at all without the works-council consultation OQ-8 raises (Germany + four Nordic jurisdictions in the seed data) | Launch, not the build |
| **DPO-6** | Whether BR-7.13's disclosure floor (no group statistic below 5 compared employees) is sufficient for a DSAR response | KAN-202 / the export |
| **DPO-7** | Whether SPM S13's reading of Directive (EU) 2023/970 — a 5% **gender gap within a category of workers**, not a raw dispersion — is correct. **Assumption, Medium confidence, not verified against any legal source in this repo** | The framing copy, not the arithmetic |

### 4.8 Who may see a salary — the matrix expanded

*SPM §8.1 item 3: for every cell of D5.2, the expected response for the HTML surface and the JSON payload. This is
the highest-value table in the document and the one UAT's negative-visibility suite is written from.*

#### 4.8.1 Scopes, defined once

| Scope | Definition |
|---|---|
| `SELF` | `employee_id = session['employee_id']`, resolved **server-side**, never from a request parameter |
| `DIRECT` | `direct_report_ids(session['employee_id'], 'SOLID_LINE')` — **one level only**, from `manager_relationships` where in effect (`app/helpers.py:141-148`). Not the subtree, not dotted lines |
| `COMPANY` | `company_id = ` the actor's company (or `session['admin_company_id']` for SYSTEM_ADMIN) |
| `NONE` | No rows |

- **BR-8.1** Where a user holds several roles, their effective scope is the **union** of their roles' scopes. A user
  who is both `SOLID_LINE_MANAGER` and `HR_ADMIN` gets `COMPANY`.
- **BR-8.2** Row scoping is a **service-layer rule on the result set**, not a per-feature role check inside a route.
  It is **not** the forbidden `enabled_for_hr` pattern: the forbidden pattern *denies a granted role access to a
  feature*; a scope *determines which rows the granted feature returns*, exactly as company scoping already does on
  every query in the product (SPM D5.3, CC-42-2).
- **BR-8.3** Every scoped read is enforced **on the server**. Out-of-scope rows are **absent from the payload** —
  never returned and hidden by CSS, a template condition, or client-side filtering (SPM R-3).

#### 4.8.2 The response matrix — defaults

Read as: *what this role gets **by default**, before the tenant changes anything*. Every cell is a ceiling a
PORTAL_ADMIN may widen or narrow through the Feature Access tab, with **no code change and no extra check**.

`200+amt` = 200 with the amount present · `200−amt` = 200 with the amount **field absent from the payload** ·
`403` = refused with no state change · `—` = surface not offered to this role.

| Role | Own pay (`compensation_self`) | Direct report's pay | Skip-level / subtree | Dotted-line report | Their dept or location | Any other employee in company | Another company | Equity queue | Propose a pay change | Configure ladder / bands / thresholds |
|---|---|---|---|---|---|---|---|---|---|---|
| **EMPLOYEE** | `200+amt` | — | — | — | — | `200−amt` | `403` | — | `403` | `403` |
| **SOLID_LINE_MANAGER** | `200+amt` | **`200+amt`** | **`200−amt`** | **`200−amt`** | — | `200−amt` | `403` | — | **Yes** (initiates) | `403` |
| **DOTTED_LINE_MANAGER** | `200+amt` | — | — | **`200−amt`** | — | `200−amt` | `403` | — | `403` | `403` |
| **DEPARTMENT_HEAD** | `200+amt` | — | — | — | **`200−amt`** | `200−amt` | `403` | — | `403` | `403` |
| **LOCATION_HEAD** | `200+amt` | — | — | — | **`200−amt`** | `200−amt` | `403` | — | `403` | `403` |
| **HIRING_MANAGER** | `200+amt` | — | — | — | — | `200−amt` | `403` | — | `403` | `403` |
| **HR_ADMIN** | `200+amt` | `200+amt` | `200+amt` | `200+amt` | `200+amt` | **`200+amt`** | `403` | **Yes (r+w)** | **Yes** | **Yes** |
| **COMPANY_ADMIN** | `200+amt` | `200−amt` | `200−amt` | `200−amt` | `200−amt` | **`200−amt`** | `403` | — | `403` | `403` |
| **PORTAL_ADMIN** | `200+amt` | `200+amt` | `200+amt` | `200+amt` | `200+amt` | **`200+amt` (r+w+d)** | `403` | **Yes (r+w)** | **Yes** | **Yes** |
| **SYSTEM_ADMIN** | n/a | `200+amt` | `200+amt` | `200+amt` | `200+amt` | `200+amt` **within the selected company** | **`403` / "select a company"** (CC-42-12) | Yes | Yes | Yes |

- **BR-8.4** `200−amt` is the **default answer for every ambiguous cell**. A role that has not been granted
  `compensation` read does not get a null salary field, an empty string or a masked value — **the key is not in the
  JSON object**, and the HTML contains no element for it.
- **BR-8.5** A `403` on a **JSON** endpoint is a JSON body with a machine-readable code and **no state change**.
  Per B42-03 this is **not** what `@require_feature_access` does today (it 302-redirects); CFL-42-8.
- **BR-8.6** A `403` on an **HTML page** may remain the existing flash-and-redirect for the *page*, **except** for the
  tenant-switch-off state, which is a real explanatory screen (KAN-188, AC-188-08).
- **BR-8.7 The three defaults worth defending** (SPM D5.2, adopted): a solid-line manager sees **one level down, not
  the subtree**; department and location heads default to **no**; `COMPANY_ADMIN` defaults to **no**, because
  administrative reach is not a reason to see pay. All three are OQ-2 for the owner and are seed data, not code.

#### 4.8.3 Read / write / delete

| Action | Meaning | Default holders |
|---|---|---|
| `r` | See amounts within your scope | HR_ADMIN, PORTAL_ADMIN, SOLID_LINE_MANAGER (scoped `DIRECT`) |
| `w` | Enter or propose a compensation record; run a backfill; edit bands, ladders and thresholds | HR_ADMIN, PORTAL_ADMIN |
| `d` | **Void** a historical compensation record — destructive, because the history is the defensibility | **PORTAL_ADMIN only** |
| *(approve)* | **Not a compensation permission.** Approval is the chain's job. A step on a money-bearing request additionally requires `compensation:r` (D4b) | per the chain |

- **BR-8.8** `r` without `w` is a real configuration (an auditor; a works-council representative in some tenants).
  Every mutating endpoint returns `403` with **no state change** for an `r`-only holder.
- **BR-8.9** `w` without `r` is **refused as a configuration**: the Feature Access tab rejects granting
  `compensation` write to a role that lacks read, naming the reason. Writing a salary you cannot read means writing
  over a value you cannot see — the D-185-1 hazard with the safety off. **[BA call]**, High confidence.

#### 4.8.4 The surfaces where an amount must never appear

Enumerated with evidence, because leaks happen at the edges. Each is a UAT assertion.

| # | Surface | Evidence it is a real path |
|---|---|---|
| 1 | `_EMP_SELECT` and its six consumers | `app/helpers.py:42-72,126-138`; `app/routes/employees.py:83,93,147,150,152,160`; `app/routes/admin.py:353,356` (B42-01) |
| 2 | `/api/employees` — no feature gate, hardcoded role scoping | `app/routes/employees.py:136-153` (B42-02) |
| 3 | `/api/my-team` | `app/routes/employees.py:156-160` |
| 4 | Notification bodies and the bell | `app/services/notification_service.py:100-117`; `templates/base.html:290-320` |
| 5 | Email dispatch | `app/services/notification_service.py` |
| 6 | `employee_search_index` and `fn_update_employee_search()` | `database/schema.sql:52-70, 1861` (B42-14) |
| 7 | Org tree, ancestors, cards, tooltips | `app/helpers.py:166-204`; `app/routes/org.py:56,70-91` |
| 8 | Analytics CSV export — **column list built from the result set** | `app/routes/analytics.py:310,317` (B42-13) |
| 9 | The org-change bell summary line `ocSummary()` | `templates/base.html:630-637` |
| 10 | Any other CSV export | `app/routes/imports.py`, `app/services/import_service.py` |
| 11 | Application logs and error messages | CC-42-21 |
| 12 | `audit_log` diffs, `metadata` and `reason` | §4.9 |
| 13 | Any JSON payload returned to a client lacking `compensation:r` | BR-8.3, BR-8.4 |

### 4.9 Salary values and the audit trail

- **BR-9.1** **A monetary amount is never written into an `audit_log` diff, `metadata` or `reason`** (SPM D5.6). The
  decisive argument is not preference: the `audit_log` read audience is defined by a **different feature code**
  (`audit_log`, default PORTAL_ADMIN + HR_ADMIN — SPM S10), so in a tenant that narrows `compensation` to two people
  but leaves `audit_log` at its default, a salary in a diff is readable by exactly the people the tenant excluded.
  Access control routable around by a second feature is not access control. And the table is append-only by DB
  trigger — a figure written there cannot be un-written.
- **BR-9.2 The permitted diff keys for a compensation event**, exhaustively:
  `has_change` (bool) · `direction` (`INCREASE`/`DECREASE`/`NONE`) · `pct_change_band` · `currency` ·
  `effective_date` · `pay_basis` · `fte_from` / `fte_to` · `level_from` / `level_to` · `step_from` / `step_to` ·
  `level_direction`. `entity_id` is the **compensation record id**. Nothing else.
- **BR-9.3 `pct_change_band` boundaries**, on `|Δ fte_normalised_annual| ÷ prior`, left-closed / right-open:
  **`INITIAL`** (no prior record) · **`0`** (exactly no change) · **`0-5`** · **`5-10`** · **`10-20`** · **`20+`**.
  `INITIAL` exists because without it every first record reads as a 20%+ rise, which is both wrong and a disclosure.
- **BR-9.4** `pct_change_band` is itself a partial disclosure: combined with a known prior figure it narrows the new
  one. It is coarse by design, and it is readable only by `audit_log:r` holders.
- **BR-9.5 `_MONEYISH_KEYS` guard.** A guard beside the existing `_SECRETISH_KEYS`
  (`app/services/audit_service.py:97-98, 153-159`) refusing diff and metadata keys containing `salary`, `pay`,
  `compensation`, `amount`, `wage`, `remuneration`, `base_pay`, `annual_base`, `compa`, `midpoint` — matched the same
  case-insensitive substring way, raising `AuditError`. Note the deliberate consequence: a key such as
  `compensation_record_id` **would be refused**, which is why BR-9.2's permitted set avoids those substrings
  entirely and the record id travels as `entity_id`.
- **BR-9.6 New `ACTIONS` codes** (Architect's file, Architect's edit — CFL-42-2):
  `COMPENSATION_RECORDED` · `COMPENSATION_CHANGED` · `COMPENSATION_VOIDED` · `COMPENSATION_PURGED` ·
  `JOB_LADDER_CHANGED` · `JOB_LEVEL_ASSIGNED` · `JOB_LEVEL_CHANGED` · `STEP_ADVANCED` · `PROMOTION_APPLIED` ·
  `PAY_BAND_CHANGED` · `PAY_MARKET_CHANGED` · `PAY_EQUITY_FLAG_RAISED` · `PAY_EQUITY_FLAG_DISPOSITIONED` ·
  `PAY_EQUITY_THRESHOLD_CHANGED` · `PAY_EQUITY_BASIS_ACKNOWLEDGED` · `TENANT_FEATURE_TOGGLED` ·
  `SELF_APPROVAL_RECORDED` — **plus the two EP38 already needs and does not have** (B42-15):
  `EMPLOYEE_ANONYMISED` · `ERASURE_REFUSED`, and the new `ERASURE_PARTIALLY_REFUSED` (BR-7.8).
- **BR-9.7 Retention class** for every EP42 audit row is **`EMPLOYMENT`**, except tenant-feature toggles
  (`STANDARD`) and self-approval records (`SECURITY`).
- **BR-9.8 The trade-off, named.** Somebody reading only the audit log cannot see the old and new amounts. That is
  the point. Defensibility is preserved because the audit row points at an immutable, effective-dated compensation
  record that carries them, joined by **`correlation_id`** (KAN-202).

---

## 5. KAN-188 — Tenant feature-exposure switch, centrally resolved (W0 · R7 · D6)

### 5.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-188 | As the **product owner**, I want to expose or hide a feature for one company without hiding it for another, and have that honoured everywhere, so I can package the product per tenant. | `company_features.is_enabled` becomes part of the **single central** access resolution; effective access = tenant switch **AND** role grant; absent row defaults **enabled** for the eleven existing features (no behaviour change for any existing tenant, asserted by a full before/after matrix snapshot) and **disabled** for the three EP42 codes; nav and routes resolve from the same place; the off state is a real explanatory screen, never a 403 or a redirect, and a JSON 403 with a machine-readable code on APIs; SYSTEM_ADMIN bypass preserved **and visibly signposted**; `reports` and `skills_intelligence` retro-fitted off their hand-rolled checks so `company_features` appears in `app/` in exactly two places; every toggle audited with a reason; `enabled_for_hr` gains no new consumer. | Must Have · P1 |

### 5.2 Happy path

- **AC-188-01** Effective access to a feature is `company_features.is_enabled` for the tenant **AND** the role grant
  resolved from `role_feature_access` + `company_role_feature_access`. Both conditions, evaluated at **one**
  resolution point (`app/auth.py::_load_feature_access()` or a wrapper the Architect designates — CFL-42-1).
- **AC-188-02** `has_feature_access()` in templates and `@require_feature_access()` on routes return the **same
  answer from the same code path** for every (user, feature, action) triple. A test enumerates every feature code
  and asserts template and route agree; two implementations are forbidden because they diverge.
- **AC-188-03** A SYSTEM_ADMIN toggles a feature for one company through the existing
  `POST /api/admin/company-features/<company_id>` surface, supplying a **reason** (new, mandatory), and the change
  takes effect for every user of that tenant **on their next request** — `g._feature_access` is per-request, so no
  session invalidation, no logout and no restart is required.
- **AC-188-04** With the feature enabled and the role granted, behaviour is exactly as today: the nav link renders,
  the page loads, the API responds.

### 5.3 The no-regression requirement — the criterion that matters

- **AC-188-05** **KAN-188 changes nothing for any existing feature or tenant.** Verified by a mechanical
  before/after comparison: for the **full cross-product of every company × every seeded role × all eleven existing
  feature codes × {r, w, d}**, the resolved answer is byte-identical before and after the change. The test builds
  the matrix from the database rather than from a fixture list, so a newly seeded company or role cannot slip past
  it. Any single differing cell fails the story.
- **AC-188-06** The absent-row default is **enabled** for the eleven existing codes (`employee_profiles`,
  `org_structure`, `user_accounts`, `skills`, `vacations`, `reports`, `company_settings`, `system_config`,
  `skills_intelligence`, `org_change`, `audit_log`) and **disabled** for the three EP42 codes. Note **B42-16**: the
  column default is `FALSE` and rows exist only where someone toggled, so this cannot be delivered by the column
  default alone — either the migration materialises `TRUE` rows for existing tenant × feature pairs or the resolver
  carries a per-feature default. **The requirement is the behaviour in AC-188-05; the mechanism is the Architect's.**
- **AC-188-07** Whichever mechanism is chosen, adding a **new company** after KAN-188 lands must not accidentally
  enable the three EP42 codes for it. A test creates a company and asserts all three resolve to disabled.

### 5.4 The off state

- **AC-188-08** A user whose role grants the feature but whose **tenant** has it disabled sees a **real explanatory
  screen** following the `templates/admin/analytics_locked.html` precedent (`app/routes/analytics.py:184`): a plain
  statement that the capability is not enabled for this company and who to contact. **Not** a 403, **not** a
  redirect to the dashboard, **not** a blank page, **not** a flash message.
- **AC-188-09** The corresponding **JSON** endpoints return **`403`** with a body carrying a machine-readable code
  `FEATURE_NOT_ENABLED_FOR_TENANT` and a human-readable message — **never** a 302 to an HTML page, which is what the
  current decorator does (B42-03, CFL-42-8). A `fetch()` receiving HTML where it expected JSON is the DEF-002
  failure shape and must not be reintroduced here.
- **AC-188-10** Nav links, dashboard tiles and any other affordance for a tenant-disabled feature are **absent from
  the rendered HTML**, not hidden with CSS.
- **AC-188-11** A **SYSTEM_ADMIN** working in a company context where the feature is disabled still reaches the
  feature (bypass preserved, CC-42-3) **and sees an unmistakable persistent banner**: *"This feature is disabled for
  <company>. You are seeing it because you are a system administrator."* Bypassing a commercial switch without
  knowing you are bypassing it is how a demo shows a prospect a feature they have not bought.

### 5.5 Retro-fitting the two existing consumers

- **AC-188-12** `reports` (analytics) and `skills_intelligence` are moved onto the central mechanism.
  `_analytics_enabled()` / `_check_analytics_access()` (`app/routes/analytics.py:20-40`) and `_si_enabled()` /
  `_check_si_company_access()` (`app/routes/skills_intelligence.py:15-30`) are removed, not left alongside it.
- **AC-188-13** **Assertable as a static check:** after this story, the string `company_features` appears in `app/`
  in exactly **two** places — the central resolver and the SYSTEM_ADMIN toggler. A test greps for it and fails on a
  third. (Today it appears in two blueprints and not in the resolver at all — B42-17.)
- **AC-188-14** Behaviour for both retro-fitted features is unchanged for every combination of
  (tenant enabled/disabled × role granted/not granted × SYSTEM_ADMIN/not), asserted by test before and after.
- **AC-188-15** **`enabled_for_hr` is deprecated in place.** No EP42 code reads or writes it; no new consumer is
  added; the column and its two existing consumers are left functioning. A static check asserts zero references to
  `enabled_for_hr` in any file EP42 adds or modifies (CC-42-2). Its removal path is named in the Architect's ADR and
  is **not** in this story's Must, because removing it changes behaviour for an existing feature.

### 5.6 Audit

- **AC-188-16** Every toggle writes an audit row: `company_id` (the affected tenant), feature code, `is_enabled`
  before → after, actor, **mandatory reason**, correlation id, action `TENANT_FEATURE_TOGGLED`, retention class
  `STANDARD`. Today the toggler writes no audit row and takes no reason (B42-16) — both are added.
- **AC-188-17** The audit row is written **inside the same transaction** as the toggle (CC-42-6); a failed toggle
  leaves no audit row.

### 5.7 Error and failure behaviour

- **AC-188-18** Toggling an unknown feature code returns `400` and changes nothing (existing behaviour, preserved).
- **AC-188-19** Toggling for a company id that does not exist, or is not a valid UUID, returns `404`/`400` with no
  stack trace and no PII in the log line (CC-42-21).
- **AC-188-20** If the toggle write fails, no partial state is left: the feature's resolved access for that tenant is
  exactly what it was, and the actor sees a specific error.
- **AC-188-21** Two SYSTEM_ADMINs toggling the same (company, feature) concurrently: the last write wins, both are
  audited with their own before→after values, and the audit trail reconstructs the sequence via `created_at`.

### 5.8 Permissions per role

| Role | Toggle a tenant switch | See the toggle UI | Reach a tenant-disabled feature |
|---|---|---|---|
| SYSTEM_ADMIN | **Yes**, all companies | Yes | Yes, with the AC-188-11 banner |
| PORTAL_ADMIN | **No** | No | No — AC-188-08 screen |
| HR_ADMIN and all other roles | No | No | No — AC-188-08 screen |

- **AC-188-22** The toggler remains SYSTEM_ADMIN-only. *(Observation, not a conflict: it is currently
  `@require_roles('SYSTEM_ADMIN')` — `app/routes/analytics.py:119`. `CLAUDE.md`'s prohibition on hardcoded role lists
  is about **feature** routes; a platform-ownership route is a defensible exception. If the Architect prefers, it
  becomes `@require_feature_access('system_config','w')`, which SYSTEM_ADMIN satisfies by bypass anyway. Either is
  acceptable; the choice must be deliberate.)*
- **AC-188-23** A PORTAL_ADMIN cannot enable a feature for their own company by any route, including a hand-crafted
  API call: `403`, no state change. R7 is the **product owner's** control, not the tenant's.

### 5.9 Tenant isolation

- **AC-188-24** Enabling a feature for company A changes the resolved access of **no user of company B**, asserted
  by the AC-188-05 matrix snapshot taken for B before and after A's toggle.
- **AC-188-25** `GET /api/admin/company-features/<id>` returns only that company's rows; there is no endpoint that
  returns the switch state of all tenants to a non-SYSTEM_ADMIN.
- **AC-188-26** The three EP42 codes are seeded disabled for **all three** existing tenants including the empty
  "Sam Cpmapny" (B42-20), and enabling them for "Sam Cpmapny" — which has 3 locations and 0 employees — produces
  working, empty-stated screens rather than errors (AC-190-14, AC-195-17, AC-200-11).

### 5.10 Out of scope (KAN-188)

Removing `enabled_for_hr` (AC-188-15 — named, not done) · a self-service tenant-provisioning or licensing surface ·
per-feature trial periods, expiry dates or entitlement records · billing of any kind · a per-*user* feature switch ·
making the toggle available to PORTAL_ADMIN (AC-188-23) · migrating the two locked-state templates into one shared
component (cosmetic; the Architect may, but it is not required).

---

## 6. KAN-189 — Effective date on org-change requests (W0 · D4d · resolves CFL-4, unblocks `AC-185-07`)

### 6.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-189 | As **HR**, I want a position change to carry the date it takes effect, so placement and pay move on the same day and history is not fudged. | One `effective_date` on `org_change_requests`, threaded through `create_request()` and `_apply_change`, rendered in the shared move modal (it is deliberately absent today rather than silently discarded); it is the boundary date for closing the outgoing assignment and opening the incoming one; **after any applied change there is exactly one assignment in effect and no day covered twice**, asserted by direct DB query; the **manager relationship is closed with a date too** (it is not today — B42-08); back-dating within a company window; a future-dated **placement** remains rejected while there is no scheduler; the column is designed so a divergent pay effective date can be added later without changing this one's meaning. | Must Have · P1 |

### 6.2 Happy path

- **AC-189-01** `org_change_requests` carries a single `effective_date` (a **date**, BR-3.8), and
  `create_request(company_id, subject_id, requester_user_id, proposed, reason, effective_date)` accepts it. Today the
  function has no such parameter (`app/services/org_change_service.py:157`).
- **AC-189-02** The shared move modal (`templates/org_change/_move_modal.html`) renders an effective-date control,
  defaulting to **today**. It is currently absent by deliberate choice on KAN-185 because there was nowhere to put
  the value; after this story the value is stored.
- **AC-189-03** On final approval, `_apply_change` uses `effective_date` — **not `CURRENT_DATE`** — as the boundary:
  the outgoing `employee_org_assignments` row is closed at that boundary and the incoming row opens at it.
- **AC-189-04** **After any applied change, for the subject employee: exactly one `employee_org_assignments` row is
  in effect, and no calendar day is covered by two rows.** Asserted by a direct SQL query in the integration test,
  not by an API response. *(Today the outgoing row is closed with `effective_to = CURRENT_DATE` while the incoming
  row defaults `effective_from = CURRENT_DATE` — a one-day overlap on every move. CFL-4.)*
- **AC-189-05** **The manager relationship is closed with a date.** Where the move changes the solid-line manager,
  the outgoing `manager_relationships` row is closed with **both** `is_current = FALSE` **and** an `effective_to`
  consistent with the interval convention, and the incoming row opens at the boundary. *(Today only `is_current` is
  set — `app/services/org_change_service.py:381-385` — and the dev database holds 2 rows with
  `is_current = FALSE AND effective_to IS NULL`. B42-08 / CFL-42-9. Without this, the pattern EP42 is told to copy
  is itself broken.)*
- **AC-189-06** `AC-185-07` on KAN-185 can be marked satisfied by this story, and KAN-185 can close. The
  non-overlap assertion in AC-189-04 is the same assertion `AC-185-07` asks for.

### 6.3 Interval convention

- **AC-189-07** The **property** is the requirement, not the convention: for any employee and any date, at most one
  assignment and at most one manager relationship are in effect, with no overlapping day and no unintended gap.
  Whether that is half-open `[from, next_from)` or `effective_to = next_from − 1` is the **Architect's call**
  (CFL-4), and the same convention is used for org assignments, manager relationships, level assignments and
  compensation records — **one convention across all four, not two**.
- **AC-189-08** The chosen convention is applied to **new** rows only. **Existing history is not rewritten.** Any
  pre-existing one-day overlap or undated close stays as it is, is documented as pre-KAN-189 data, and any
  point-in-time report states the caveat rather than silently correcting it. Rewriting historical rows would change
  what the audit trail says happened.

### 6.4 Back-dating and future-dating

- **AC-189-09** `effective_date` may be **backdated** within a per-company window, default **90 days**, range
  0–3650, PORTAL_ADMIN-configurable, every change audited (BR-3.5). Outside the window: `422`, naming the window,
  creating no request.
- **AC-189-10** `effective_date` **before the subject's `join_date`** is rejected (`422`), and before the start of
  the current employment period after a rehire (BR-3.7).
- **AC-189-11** A **future** `effective_date` on a `TRANSFER` or `PROMOTION` is **rejected** (`422`) with a message
  explaining that scheduled placement changes are not supported. *(EP38 R5.6 — with no scheduler, a future-dated
  placement would either apply early, which is wrong, or never, which is worse.)*
- **AC-189-12** A future `effective_date` on a **`COMPENSATION_REVIEW`** (pay only, no placement) **is** permitted
  within the forward window, default 180 days (BR-3.6a). The resulting compensation record is inert until its date
  (BR-3.6). **This asymmetry is deliberate and is logged as CFL-42-10** — it exists because one date is shared
  between two things with different scheduler dependencies.
- **AC-189-13** The date is validated **server-side on the create path**. A hand-crafted API call with a date
  outside the window or in the past beyond it is refused; the client control is a convenience, never the control.
- **AC-189-14** Time between creation and final approval does **not** change the effective date. A request created
  with `effective_date = today` and approved eight days later applies with that original date, and the boundary is
  that date, not the approval date. The approval timestamp is recorded separately (`decided_at`, existing).

### 6.5 Edge and boundary cases

- **AC-189-15** Two applied changes for the same subject on the **same** `effective_date`: the second apply is
  refused (`409`) naming the first, because it would produce two rows opening on one day and an undefined "current".
  The initiator is directed to cancel or supersede the first request.
- **AC-189-16** A request whose `effective_date` is **earlier than the `effective_from` of the subject's current
  assignment** is refused at create time (`422`) — applying it would insert a row that starts before the row it is
  supposed to succeed.
- **AC-189-17** Where the subject has **no** current org assignment at all, apply opens a new assignment at
  `effective_date` and closes nothing; the transaction succeeds. *(`_apply_change` is already None-safe here —
  `app/services/org_change_service.py:356-364` — and must stay so.)*
- **AC-189-18** The D-185-1 overlay rule is unchanged: a proposal carries only the dimensions the requester changed,
  and unchanged dimensions are carried forward from the outgoing row. Adding a date must not disturb the overlay
  (`app/services/org_change_service.py:365-380`).

### 6.6 Error and failure behaviour

- **AC-189-19** A malformed date (`2026-13-45`, `""`, `"today"`, a timestamp) is rejected at the API boundary with
  `400` and a field-level message; no request is created.
- **AC-189-20** Any failure during apply rolls the whole thing back: the assignment rows, the manager relationship,
  the request status and the audit rows are exactly as before (CC-42-6).
- **AC-189-21** An existing `org_change_requests` row created before this story (no effective date) still applies
  correctly, using its `created_at` date as the boundary, and the migration states this default explicitly rather
  than leaving NULL to be interpreted at read time.

### 6.7 Permissions and tenant isolation

- **AC-189-22** The date field is available to whoever may already create a request; this story adds **no** role
  check and removes none (`@require_feature_access('org_change','w')` plus `_can_initiate_for`).
- **AC-189-23** The backdating-window setting is PORTAL_ADMIN + SYSTEM_ADMIN only, company-scoped, and a
  PORTAL_ADMIN of company A cannot read or change company B's window: `403`, no state change.
- **AC-189-24** All queries remain company-scoped (CC-42-11).

### 6.8 Out of scope (KAN-189)

A **divergent** pay effective date distinct from the placement date (SPM §3.4 — Later; the column must be *designed*
so it can be added without changing this one's meaning) · scheduled/deferred application of a future-dated placement
(needs KAN-163) · rewriting existing overlapping history (AC-189-08) · effective dating of anything outside
`org_change_requests`, `employee_org_assignments` and `manager_relationships` · retroactive recalculation of leave
entitlement, headcount snapshots or any prior report.

---

## 7. KAN-190 — Job families, levels and steps: the configurator (W1 · R6 · D3)

### 7.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-190 | As a **customer admin**, I want to define my own job families, levels and steps with our own titles, so the ladder matches how we actually organise work. | Company-scoped families; ordinal levels within a family, **contiguous from 1**, each carrying its own title; `steps_count` per level, default **5**, range 1–12, displayed `<level>.<step>`; levels reorderable only while the family has no assignments and **frozen thereafter** (renaming always allowed); a level or family that has ever been assigned cannot be deleted — it is **archived**; a company with no ladder shows an **explicit empty state** and never another company's or a global default's levels; all queries `company_id = %s::uuid` only; gated `@require_feature_access('compensation','w')`; every change audited; WCAG 2.2 AA. | Must Have · P1 |

### 7.2 Happy path

- **AC-190-01** A `compensation:w` holder creates a **job family** for their own company: name mandatory, ≤ 150
  chars, unique within the company **case-insensitively after trimming** (BR-5.1). The product ships **no**
  families and no example ladder is imposed (D3.2).
- **AC-190-02** Within a family they create **levels**, each with an `ordinal` (auto-assigned as the next integer),
  a **title** (mandatory, ≤ 150 chars, unique within the family case-insensitively after trimming) and a
  `steps_count` (default **5**, range **1–12**).
- **AC-190-03** Steps are implicit `1 … steps_count` and are displayed **`<ordinal>.<step>`** — `1.1`, `1.5`, `3.2`.
  There is no separate step-creation action.
- **AC-190-04** A level optionally carries a **step target point** per step — a percentile within the level's band
  — which is **guidance only** and never enforced (D3.5). Absent by default.
- **AC-190-05** The configurator shows the ladder as it will be read: family → levels in ordinal order → each
  level's title, step count and the step labels it produces.
- **AC-190-06** Every create, rename, reorder, step-count change, archive and delete writes an audit row
  (`JOB_LADDER_CHANGED`) with the field-level before → after, actor, mandatory reason, correlation id and
  `retention_class = 'EMPLOYMENT'`.

### 7.3 Ladder validity — the rules that make a ladder well-formed

- **AC-190-07** **Ordinals are contiguous from 1.** Creating a level appends at `max(ordinal) + 1`. An API call
  supplying an ordinal that would leave a gap is refused (`422`) naming the gap (BR-5.3).
- **AC-190-08** **Reordering is permitted only while the family has zero level assignments, current or historical.**
  The moment any assignment exists, ordinal positions are **frozen** and the reorder control is disabled with an
  explanation naming the assignment count. A hand-crafted API reorder is refused (`409`).
- **AC-190-09** **Renaming a level's title is always permitted**, including after assignments exist, and is audited
  with before → after. The level's identity is its id, not its title; existing assignments follow it and the
  directory/org-tree display updates for everyone at once (BR-5.11).
- **AC-190-10** **Appending above the highest ordinal is always permitted**, including after assignments exist.
  **Inserting between two existing levels is refused** (`409`) with an explanation. *(Consequence stated, not
  hidden: a company that later needs a level between 2 and 3 has no path other than a new family and a re-map —
  **OQ-BA-2**.)*
- **AC-190-11** **Increasing `steps_count` is always permitted.** **Decreasing it below the highest step currently
  assigned** to any employee with a current assignment is refused (`422`), naming the count of affected employees
  and the highest step in use.
- **AC-190-12** Decreasing `steps_count` such that an employee who **was** at the last step is no longer at the last
  step, or vice versa, updates the `promotion_eligible` marker accordingly and **retires any now-false notification
  for every recipient** (BR-5.9, KAN-192).
- **AC-190-13** **Deletion.** A level or family referenced by **any** assignment — current or historical — cannot be
  deleted: `409`, with **Archive** offered instead. An archived level accepts no new assignments, disappears from
  every picker, keeps its existing assignments and still participates in historical grouping. A level never
  assigned may be deleted **only if it is the highest ordinal in its family** (otherwise it would create a gap).
  Deleting a family requires every level in it to be deletable.

### 7.4 Edge and boundary cases

- **AC-190-14** A company with **no ladder** shows an explicit empty state — *"No job architecture configured"* with
  a create action — and **never** another company's families, never a global default, never a suggested ladder
  (`CLAUDE.md` empty-state rule; CC-42-4). Verified against the empty "Sam Cpmapny" tenant (B42-20).
- **AC-190-15** A family with **zero levels** is valid, is shown as such, and offers no assignment path until a
  level exists.
- **AC-190-16** `steps_count = 1` is valid: the level has exactly one step, displayed `<ordinal>.1`, and **every**
  assignment to it is immediately at the last step — so the `promotion_eligible` signal raises on assignment
  (BR-5.8). This must not be treated as an error state.
- **AC-190-17** `steps_count = 12` is valid; 0 and 13 are rejected with a field-level message.
- **AC-190-18** A family or level name differing only by case or surrounding whitespace from an existing one is
  **rejected as a duplicate** (`Engineering` / `engineering` / ` Engineering `), naming the existing record.
- **AC-190-19** Titles containing markup are stored verbatim and escaped on output through `escH()` (CC-42-22); no
  script executes on any surface that displays a level title.
- **AC-190-20** A single company may hold many families and many levels; the configurator does not degrade at
  20 families × 12 levels, and the ladder queries do not become per-row lookups on the directory
  (performance shape is the Architect's, the requirement is that displaying 100 employees does not issue 100 ladder
  queries).

### 7.5 Error and failure behaviour

- **AC-190-21** Every validation failure is reported **before any write**, at field level, with the offending value
  named. A multi-field form failure reports all failures at once, not one at a time.
- **AC-190-22** A partially-failed ladder edit leaves the ladder exactly as it was (CC-42-6). There is no state in
  which a level exists without its family, or an ordinal sequence has a gap.
- **AC-190-23** Two admins editing the same level concurrently: the second write is refused (`409`) with the current
  server state shown, rather than silently overwriting. **[BA call]** — a silently-lost rename of a level title
  changes what the whole directory displays.
- **AC-190-24** Requesting a level or family belonging to another company by UUID returns `403`, reads nothing back
  and writes nothing (CC-42-11).

### 7.6 Permissions per role

| Role | Create/edit ladder | Archive / delete | View the ladder | Assign employees (KAN-191) |
|---|---|---|---|---|
| SYSTEM_ADMIN | Yes (company context required, CC-42-13) | Yes | Yes | Yes |
| PORTAL_ADMIN | Yes (`compensation:w`) | Yes (`compensation:w`) | Yes | Yes |
| HR_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes |
| SOLID_LINE_MANAGER | No | No | **Yes** — level titles are how the job is displayed (BR-5.11), so reading the ladder is not a pay permission | No |
| All other roles | No | No | Yes (titles only) | No |

- **AC-190-25** Configuration routes are `@require_feature_access('compensation', 'w')`; there is **no hardcoded
  role list** anywhere in the story (CC-42-1). Granting `compensation` write to any additional role through the
  matrix gives that role the configurator with **no code change and no extra check** (CC-42-9).
- **AC-190-26** **Reading a level title is not a pay permission.** Level titles appear in the directory and org tree
  for everyone (BR-5.11); they carry no amount. The read path for titles must therefore **not** be gated on
  `compensation:r`, or the directory breaks for every employee. *(This is the one place where a compensation-adjacent
  read is deliberately ungated, and it is stated so nobody "tightens" it into a regression.)*
- **AC-190-27** An `r`-only `compensation` holder sees the configurator read-only; every mutating endpoint returns
  `403` with no state change (CC-42-10).

### 7.7 Tenant isolation

- **AC-190-28** Families, levels and steps are company-scoped (`company_id = %s::uuid` **only**, never
  `OR company_id IS NULL`). A PORTAL_ADMIN of company A sees zero of company B's families under every filter and
  every search term.
- **AC-190-29** There is **no global template ladder**. Nothing seeds a default family or level into any tenant, and
  the empty state is the correct first experience (AC-190-14). *(SPM D3.2: the product ships a configurator and a
  worked example, not an opinionated ladder — and the worked example is documentation, not seeded data.)*
- **AC-190-30** A SYSTEM_ADMIN with **All Companies** selected cannot create or edit a ladder (CC-42-13) and sees a
  "select a company" state.

### 7.8 Out of scope (KAN-190)

Cross-company or template ladders shared between tenants · job-family hierarchies (sub-families, tracks, IC-vs-manager
parallel ladders) · competency or skill frameworks attached to a level (that is `skills`, EP-existing) · job
descriptions, job codes or an external job-catalogue import · level-based approval routing · mapping a level to an
external grading scheme (Hay, Mercer, Radford) · **any band or pay figure** (KAN-199) · automatic level suggestion
from a job title (that is a human mapping decision — KAN-191).

---

## 8. KAN-191 — Every employee on a level; the title→level mapping (W1 · R6 · R2 · D7)

### 8.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-191 | As **HR**, I want every existing employee placed on a level and step, so comparisons and promotions have something to stand on. | Effective-dated assignment of an employee to a (family, level, step); a **mapping screen** listing every distinct free-text `job_title` in the company with its headcount, a level assignable per title and bulk-applied, plus a **CSV round-trip**; `employees.job_title` is **not** dropped — it is relabelled "Working title", and level title becomes canonical with a stated precedence in every surface; a **level coverage meter** with the remainder exportable and a reason per row; unassigned employees are in **no comparison group** and are **counted, never silently dropped**; company-scoped; audited. | Must Have · P1 |

### 8.2 Happy path

- **AC-191-01** A `compensation:w` holder assigns an employee a **(family, level, step)** with an `effective_from`
  date. All three parts are mandatory; the level must belong to the family and the step must be within
  `1 … steps_count` (BR-5.7).
- **AC-191-02** Assignments are **effective-dated and append-only**, following §4.3 exactly: at most one assignment
  in effect on any date, no overlapping day, no update-in-place, corrections are new records, the interval
  convention is the one KAN-189 establishes (AC-189-07).
- **AC-191-03** The **mapping screen** lists every distinct `employees.job_title` in the company with its headcount,
  descending. A level is chosen per title and **bulk-applied** to every ACTIVE employee holding that title. Titles
  already fully mapped are visually separated from those outstanding. *(Acme: 41 distinct titles over 46 people.
  Telia: 75 over 100 — B42-20. This screen decides whether the backfill finishes; SPM R-2.)*
- **AC-191-04** **CSV round-trip.** Export produces one row per distinct title with `job_title`, `headcount`,
  `job_family`, `job_level`, `default_step`. The same shape re-imports, with a dry-run preview showing
  create/update/error per row before any write, and a single atomic commit (CC-42-6).
- **AC-191-05** A **level coverage meter** on the compensation landing page: *"Job levels: 62% of active employees
  (91 of 146)"*, naming its denominator (BR-6.2), with the missing list exportable to CSV carrying a **reason** per
  row (BR-6.3).
- **AC-191-06** Every assignment, bulk apply and CSV commit writes audit rows (`JOB_LEVEL_ASSIGNED` /
  `JOB_LEVEL_CHANGED`) with level/step before → after, actor, mandatory reason, one shared correlation id per bulk
  operation so the whole apply reads as one story.

### 8.3 The fate of `employees.job_title` (**CFL-42-4**)

- **AC-191-07** `employees.job_title` is **not dropped, renamed, repurposed or cleared** by this story. It remains
  free text, remains indexed (`idx_employees_job_title`), remains in the search trigger, and remains writable
  through the existing edit paths.
- **AC-191-08** It is **relabelled "Working title"** in every UI surface that shows it, with helper text explaining
  that the level title is the job.
- **AC-191-09** Display precedence is exactly **BR-5.11**'s table, and every listed surface is asserted:
  directory row, org-tree card, profile header, `/api/employees`, `/api/my-team`, the org-change modal's subject
  line, the approver's queue row. Both-present → level title with working title in parentheses; level only → level
  title; working only → working title plus a "No level assigned" marker for ladder admins; neither →
  **"No job title recorded"**, never blank; identical (case-insensitively, trimmed) → shown once.
- **AC-191-10** **Level titles are searchable.** Searching a level title returns the employees on that level.
  *(This does not work today and is not a display change: `employee_search_index` is written only by
  `trg_employee_search` over `first_name, last_name, job_title, email`, and no application code writes the index —
  B42-14. The mechanism is the Architect's; the behaviour is required, because relabelling `job_title` to "working
  title" while making the level title canonical and then not indexing it makes the directory search worse than it
  is today.)*
- **AC-191-11** Changing a **level title** (AC-190-09) updates what every affected employee's card and search result
  shows, for every employee on that level, without touching any `employees` row.

### 8.4 Edge and boundary cases

- **AC-191-12** An employee with **no level** is in **no comparison group at all** (BR-4.3) and is **counted** in the
  level coverage meter with reason "no level". They are never silently dropped from a denominator and never assumed
  into a group.
- **AC-191-13** An employee with a **NULL or empty `job_title`** appears on the mapping screen under an explicit
  *"(no working title)"* bucket with its headcount, and can be bulk-assigned like any other bucket. They are not
  hidden.
- **AC-191-14** Bulk-applying a level to a title where **some** employees already have a different level: the
  preview shows the count that will change and the count that will be created, per level, **before** the commit, and
  the actor confirms. Nothing is overwritten silently.
- **AC-191-15** Bulk-applying to a title held by employees in **different families** is permitted (a title can span
  families) but the mapping is per (title → family, level), and an employee already in another family is shown as a
  **family change**, which requires an explicit confirmation because it changes their comparison group.
- **AC-191-16** Assigning a level from an **archived** level (AC-190-13) is refused (`422`).
- **AC-191-17** Backdating an assignment follows BR-3.5 (90-day default window); a date before `join_date` or before
  the current employment period's start is refused (BR-3.7).
- **AC-191-18** A **non-ACTIVE** employee cannot be given a new level assignment (`422`); their existing assignment
  is closed at `exit_date` (BR-7.19) and remains visible in history.
- **AC-191-19** A **contractor or intern** *can* be assigned a level. Levels are job architecture, not pay: they are
  excluded from **pay** comparison (BR-2.7), not from the ladder. The level coverage denominator therefore includes
  them, while the pay coverage denominator does not (BR-6.4's row for state **X**). Conflating the two denominators
  is the most likely reporting error in this story.
- **AC-191-20** An employee with `company_id IS NULL` cannot be assigned a level (CC-42-14).
- **AC-191-21** Two admins assigning the same employee concurrently with the same `effective_from`: one succeeds,
  the other receives `409` naming the existing assignment (BR-3.4).

### 8.5 Error and failure behaviour

- **AC-191-22** A CSV whose header does not match the exported shape is rejected **at upload** with the expected
  columns listed; nothing is written.
- **AC-191-23** Row-level errors (unknown family, unknown level, step out of range, archived level, unknown title)
  are reported **per row with the row number** in the preview, and the actor chooses to commit the valid rows or
  abandon. **No error is silent.** *(Contrast B42-12: the existing employee importer swallows the exception and
  marks the row `SKIPPED` with no reason surfaced. That pattern must not be copied.)*
- **AC-191-24** A bulk apply is **atomic per commit** (CC-42-6): a failure part-way leaves zero assignments written
  and zero audit rows, and the actor sees which row failed.
- **AC-191-25** A bulk apply over the largest realistic tenant population completes as one unit of work without
  per-row commits, and its audit rows share one correlation id.

### 8.6 Permissions per role

| Role | Assign a level | Bulk map | Export missing list | View own level | View others' level |
|---|---|---|---|---|---|
| SYSTEM_ADMIN | Yes (company context) | Yes | Yes | n/a | Yes |
| PORTAL_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes | Yes |
| HR_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes | Yes |
| SOLID_LINE_MANAGER | **No** | No | No | Yes | Yes — level titles are public (AC-190-26) |
| EMPLOYEE | No | No | No | Yes | Yes (titles only) |

- **AC-191-26** Assignment routes are `@require_feature_access('compensation', 'w')`; there is no hardcoded role
  list (CC-42-1). *(Note the deliberate consequence: a solid-line manager who holds `compensation:r` for their
  reports' pay still cannot change a report's level, because that is a `w` action and a ladder decision. Level
  changes go through the promotion request — KAN-197.)*
- **AC-191-27** An `r`-only holder sees the coverage meter and the mapping screen read-only; every mutating endpoint
  returns `403` with no state change.

### 8.7 Tenant isolation

- **AC-191-28** The mapping screen lists only company A's distinct titles and only company A's families and levels.
  A title string that exists in both tenants (e.g. "Software Engineer", which spans both — SPM S2) produces two
  independent mapping rows, one per tenant, and mapping it in A changes nothing in B.
- **AC-191-29** The coverage meter, the missing list and every export are company-scoped; company B appears in none
  of them under any filter or search term.
- **AC-191-30** A CSV naming an `employee_number` belonging to another company is rejected at preview with a
  row-level error; nothing is written, and the error names the row, not the foreign employee.

### 8.8 Out of scope (KAN-191)

Automatic or suggested title→level mapping of any kind (it is a human judgement — §3.3's automation exclusion) ·
fuzzy title matching or clustering · migrating `employee_directory.designation` (a second, unrelated legacy free-text
title, `database/schema.sql:281`) · retiring or cleaning `employees.job_title` values · bulk **unassignment** ·
level-based reporting or analytics beyond the coverage meter · any pay figure (KAN-193/199) · promotion (KAN-197).

---

## 9. KAN-192 — Step advancement and the promotion-eligible signal (W1 · R6 · D3.4)

> **Contingent on OQ-1.** Every criterion below is written against the SPM's default — *reaching the last step is a
> **signal**, not an automatic promotion*. If the product owner answers OQ-1 differently, AC-192-06 through
> AC-192-14 change shape and the story needs a rules engine and a trigger that do not exist (SPM S16). This is the
> only story in EP42 gated on a product-owner answer rather than on Wave 2 work.

### 9.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-192 | As a **manager or HR admin**, I want step advancement and level promotion to be explicit, recorded decisions, so nobody is promoted by side-effect. | Step advancement is an explicit audited action; **no automatic roll-up** on reaching the last step — instead a `promotion_eligible` signal to the subject's solid-line manager and `compensation:w` holders, worded as a signal with no implied promise; promotion between levels happens **only** through a `PROMOTION` request (KAN-197); **skip-step, skip-level and downward moves are all permitted with a mandatory reason** and full audit, with the **direction recorded**; every transition writes level/step before → after to the audit trail with **no amounts**; the signal specifies section, icon, quick action and retirement per D2's checklist. | Must Have · P1 |

### 9.2 Happy path — step advancement

- **AC-192-01** A `compensation:w` holder **or the subject's current solid-line manager** advances an employee's
  step within their current level. The action requires a **mandatory reason** and an `effective_from` date.
- **AC-192-02** A step change that carries **no** pay change does **not** require the approval chain (D3.4). A step
  change accompanied by a pay change **is** a compensation change and goes through the chain as a
  `COMPENSATION_REVIEW` (KAN-197, D4).
- **AC-192-03** The new assignment follows §4.3: effective-dated, append-only, at most one in effect on any date,
  no overlapping day.
- **AC-192-04** Every transition writes an audit row (`STEP_ADVANCED`) carrying `level_from`/`level_to`,
  `step_from`/`step_to`, `level_direction` and the actor's reason. **No amount, no compa-ratio, no band position**
  appears in the diff, the metadata or the reason (BR-9.1, BR-9.2).
- **AC-192-05** **Skip-step, skip-level and downward moves are all permitted**, each with a mandatory reason and
  full audit (D3.4). A one-way ratchet is a fiction, and blocking a correction means HR edits the database. A
  **downward** move additionally requires an explicit confirmation naming the current and proposed level.

### 9.3 The promotion-eligible signal — a signal, not a transition

- **AC-192-06** **Nothing is automatic.** Reaching the last step of a level changes no title, no level, no band, no
  pay, no comparison group and no record other than the marker itself. There is **no** code path anywhere in EP42
  that changes an employee's level without a human decision recorded through KAN-197 (BR-7.15, D3.4).
- **AC-192-07** A `promotion_eligible` marker is set on the assignment when — and only when — an assignment
  **becomes** current with `step == steps_count` (BR-5.8).
- **AC-192-08** The marker is **not** raised again by a later edit that leaves the step unchanged, so a reason edit
  or an unrelated correction does not re-notify (BR-5.8).
- **AC-192-09** The marker is **not raised at all** when the level is the **highest ordinal in its family** — there
  is no next level. The UI shows *"Top of ladder"* instead. **[BA call]**; without it, everyone at the top of every
  ladder receives a permanent, unactionable notification, which is the DEF-001 dead-end shape.
- **AC-192-10** If `steps_count` is later **increased** (5 → 7), an employee at step 5 is no longer at the last
  step: the marker is **cleared** and its notification **retired for every recipient**, not just the one who looked
  (BR-5.9, DEF-003).
- **AC-192-11** **The notification, against D4's blind-spot list — every row answered, none blank:**

  | Blind-spot item | Answer |
  |---|---|
  | **Which bell section** | **"My Notifications"** — it is information, not an approval. It does **not** go in "Pending Approvals" (role-gated, and this is not an approval) and not in "Position Changes" (that section is the org-change call-to-action queue) |
  | **How is it gated** | The recipient set is defined below; the section itself is visible to everyone (`templates/base.html:313-319`) |
  | **Recipients** | The subject's **current solid-line manager**, and all `compensation:w` holders in the company. **Not the subject.** *(**[BA call]**, and the reason matters: telling an employee the system considers them "promotion eligible" before any human has decided anything is precisely the implied promise D3.4 warns about, and Charter §9.8 forbids the dark-pattern version of it. → **OQ-BA-4**)* |
  | **Event type / icon** | `PROMOTION_ELIGIBLE` → **`🪜`**, added to `NOTIF_ICON` (`templates/base.html:608-623`). **Never `❌`** (DEF-002); the neutral `🔔` fallback stays |
  | **Badge** | Counted in the existing bell badge total |
  | **Quick action** | **One: "Review →"**, deep-linking to the subject's profile with the promotion action in view. **No promote-from-the-bell** — a level change without a recorded reason is not auditable (the `templates/base.html:639-641` precedent) |
  | **Does the body contain an amount** | **No.** Never. Not a salary, not a band position, not a compa-ratio (BR-9.1, §4.8.4 row 4) |
  | **Wording** | A signal with **no implied promise**: it states that the employee has reached the last step of their level, and that promotion is a decision. UX owns the exact sentence (SPM §8.3.8) and it is the single most easily misread sentence in the epic |
  | **When does it retire** | On the marker being cleared: a `PROMOTION` request for the subject being **applied**, the step moving off the last step, or `steps_count` increasing (AC-192-10). Via `notification_service.resolve_related()` with `related_type = 'JOB_LEVEL_ASSIGNMENT'` |
  | **Does it retire on read** | **No.** Reading is not deciding (DEF-003 in reverse), and this must be asserted by test |
  | **Who sees it retire** | **Every** eligible recipient, not only the one who acted. Asserted across at least three recipients (SPM §8.4.5) |

- **AC-192-12** A **rejected** `PROMOTION` request does **not** clear the marker — the employee is still at the last
  step and still eligible. The notification is re-raised only if it had been retired, and the rejection reason is
  visible to the initiator (existing org-change behaviour).
- **AC-192-13** A **cancelled** promotion request behaves the same as a rejected one.
- **AC-192-14** Promotion between levels happens **only** through a `PROMOTION` request (KAN-197). There is no
  direct level-change endpoint, for any role, including SYSTEM_ADMIN. An attempt returns `409` naming the promotion
  workflow. *(Mirrors EP38 AC-184-26's "no direct edit back to ACTIVE" reasoning: the governed path is the only
  path, or the governance is optional.)*

### 9.4 Edge and boundary cases

- **AC-192-15** An employee with **no level assignment** cannot have a step advanced: `422`, directing the actor to
  assign a level first (KAN-191).
- **AC-192-16** Advancing to a step **above `steps_count`** is refused (`422`); the correct action is a promotion.
- **AC-192-17** Advancing to a step **below 1** is refused (`400`).
- **AC-192-18** Advancing to the **same** step with the same effective date is refused as a no-op (`400`) —
  consistent with AC-185-11's no-op transfer rule.
- **AC-192-19** A step change on a **non-ACTIVE** employee is refused (`422`).
- **AC-192-20** A step change **backdated** beyond the company window is refused (BR-3.5); a **future-dated** step
  change with no pay component is permitted within the forward window and is inert until its date (BR-3.6) — it is
  a level-assignment record, not a placement.
- **AC-192-21** Where the subject's level is **archived** (AC-190-13), step advancement within it is still permitted
  (people already on it must be able to progress); assignment **to** it is not.
- **AC-192-22** A step change **changes the employee's comparison group only if it changes level**. Step is not part
  of the group key (BR-4.1), so a step advance triggers a re-evaluation of the group only because the subject's
  facts changed (BR-4.29 (b)), not because the group membership changed.

### 9.5 Error and failure behaviour

- **AC-192-23** A step change with a blank reason is refused (`400`) before any write.
- **AC-192-24** Any failure rolls back the assignment, the marker and the audit rows together (CC-42-6); a marker
  never exists without the assignment that justifies it.
- **AC-192-25** A failure while sending the notification does **not** roll back the step change. Notifications are
  sent **after** the unit of work commits — the existing engine's rule
  (`app/services/org_change_service.py:196-198`) — and a failed send is logged and retryable.
- **AC-192-26** Replaying the same step change returns `409` with the existing state and writes no second audit row
  and no second notification (CC-42-20).

### 9.6 Permissions per role

| Role | Advance a step | Move down a step/level | Receive the eligibility signal | See a subject's level history |
|---|---|---|---|---|
| SYSTEM_ADMIN | Yes (company context) | Yes | Yes | Yes |
| PORTAL_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes |
| HR_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes |
| SOLID_LINE_MANAGER | **Yes, for their own direct reports only** | Yes, own reports, with confirmation | **Yes**, for their own reports | Own reports |
| DOTTED_LINE_MANAGER / DEPARTMENT_HEAD / LOCATION_HEAD / HIRING_MANAGER / COMPANY_ADMIN | No | No | No | No |
| EMPLOYEE (the subject) | No | No | **No** — AC-192-11, OQ-BA-4 | Own level and step (KAN-194 "My Pay") |

- **AC-192-27** Routes are `@require_feature_access('compensation', 'w')` plus the **row-scope** rule (BR-8.2): a
  solid-line manager's writes are confined to their `DIRECT` set, server-side. Attempting a step change for a
  non-report returns `403` with no state change, even with a valid UUID supplied directly to the API.
- **AC-192-28** A manager may **never** advance their **own** step: `403`, no state change — the pay-and-progression
  equivalent of `CLAUDE.md` org-change invariant 2. **This must be an explicit check on the subject, because
  `_can_initiate_for` does not provide it for admins today (B42-05 / CFL-42-14).**
- **AC-192-29** An HR_ADMIN or PORTAL_ADMIN may **never** advance their **own** step either: `403`, no state change.
  Same reason; the admin branch is exactly where the existing rule leaks.

### 9.7 Tenant isolation

- **AC-192-30** A step change for an employee of another company returns `403`, reads nothing back and writes
  nothing, for every non-SYSTEM_ADMIN role.
- **AC-192-31** Eligibility notifications are delivered only to recipients **within the subject's company**;
  `compensation:w` holders in another tenant receive nothing, under any configuration.
- **AC-192-32** Level history queries are company-scoped (CC-42-11).

### 9.8 Out of scope (KAN-192)

**Automatic level roll-up of any kind** (D3.4; and there is no scheduler to trigger it — SPM S16) · time-in-step or
time-in-level rules, minimum tenure gates, eligibility windows · a promotion nomination, calibration or
talent-review round (§3.3) · performance data as an input to eligibility (no performance module exists, and it would
be an Art. 22 / AI Act question — BR-7.17) · bulk step advancement across a population (an annual step-progression
cycle is comp-review-cycle territory, §3.3) · the promotion request itself (KAN-197) · any pay consequence (KAN-196).

---

## 10. KAN-193 — The effective-dated compensation record (W2 · R1 — the spine of the epic)

### 10.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-193 | As **HR**, I want the product to hold an effective-dated salary for an employee, so pay is a governed record rather than a spreadsheet. | **Append-only, effective-dated** compensation history per employee: amount, **currency**, **FTE**, pay basis (annual/monthly/hourly with company constants), `effective_from`, actor, mandatory reason, correlation id, and the `employment_type` as at the record; **at most one record in effect on any date** and **no day covered twice**; **no UPDATE and no DELETE path** — a correction is a new record, an error is a **void**; "current" is **computed, never stored** (no `is_current` flag); written inside the caller's `transaction()` (KAN-155) together with its `audit_log` row, which carries **no amount**; company-scoped; retention class `EMPLOYMENT`; prior-period records never leak into a new employment period after rehire. | Must Have · P1 |

### 10.2 Happy path

- **AC-193-01** A `compensation:w` holder records a compensation record for an employee in their own company. The
  record carries, all mandatory unless stated: **amount** (BR-1.1, BR-1.3), **currency** (BR-1.2), **FTE**
  (BR-2.4), **pay basis** (BR-2.1), **`effective_from`** (BR-3.8), **reason** (free text, mandatory, non-blank),
  the **actor**, a **correlation id**, and the subject's **`employment_type` as at the record** (so contractor and
  intern exclusion stays stable if the employee's type later changes).
- **AC-193-02** `annualised_base` and `fte_normalised_annual` are **derived** per BR-2.3 and BR-2.5 — whether they
  are computed on read or stored as generated values is the Architect's call, but they are never independently
  editable and never diverge from the stored inputs.
- **AC-193-03** The record and its `audit_log` row (`COMPENSATION_RECORDED` or `COMPENSATION_CHANGED`) are written
  in **one** `transaction()` (CC-42-6). A rolled-back write leaves neither.
- **AC-193-04** The audit row carries **no amount** — only BR-9.2's permitted keys — and its `entity_id` is the
  **compensation record id**, so the audit row and the record join by `correlation_id` into one story (KAN-202).
- **AC-193-05** Reading "what is this person paid" returns exactly one answer for any given date, computed per
  BR-3.2 and BR-3.3.

### 10.3 Append-only, corrections and voids

- **AC-193-06** **There is no UPDATE path and no DELETE path on a compensation record.** No application code issues
  `UPDATE compensation_records SET amount = …` or `DELETE FROM compensation_records`, assertable by a static check
  over `app/` (the EP38 AC-184-30 pattern).
- **AC-193-07** A **correction** is a **new record**. Correcting the amount on a record effective 2026-01-01 means
  voiding it and writing a new record on the same date carrying a `supersedes` pointer, with a mandatory reason.
- **AC-193-08** A **void** marks the record voided, retains it in the timeline with the voiding actor, timestamp and
  reason, and excludes it from every computation (current pay, coverage, comparison, export). Voiding requires
  **`compensation:d`** (PORTAL_ADMIN only by default — BR-8.7).
- **AC-193-09** Voiding the **only** record for an employee returns them to **"No salary recorded"** with the
  Record-salary action, and they leave every compared set on the next evaluation (BR-4.25). This is a legitimate
  outcome, not an error state.
- **AC-193-10** A voided record cannot be un-voided. The way back is a new record.
- **AC-193-11** Every void writes a `COMPENSATION_VOIDED` audit row with a mandatory reason and no amount.

### 10.4 Effective dating

- **AC-193-12** For any employee and any date: **at most one** non-voided record is in effect, and **no calendar day
  is covered by two records**. Asserted by a direct DB query over the whole seeded population in the integration
  test, not by an API response.
- **AC-193-13** **"Current" is computed, not stored.** There is no `is_current` column on the compensation record.
  *(BR-3.2, CFL-42-16 — this deliberately diverges from `manager_relationships` and `employee_org_assignments`,
  because a stored flag on a future-dated record would need a scheduler to flip it and there is none.)*
- **AC-193-14** A record with `effective_from = D` is in effect **on D**; the previous record's last effective day
  is **D − 1** (BR-3.3). Tested at the boundary with a query for D − 1, D and D + 1.
- **AC-193-15** **Two non-voided records for one employee on the same `effective_from` are impossible.** The second
  write returns `409` naming the existing record and offering the correction path (BR-3.4). Enforced at the data
  layer, not only in the service, so a concurrent write cannot slip past.
- **AC-193-16** **Backdating** is permitted within the company window (default 90 days) and **splits the timeline**
  per BR-3.5 / WE-2: later records keep their own periods and the currently-effective record is unchanged unless the
  new record is later than it.
- **AC-193-17** **Future-dating** is permitted within the forward window (default 180 days). The record is **inert**:
  excluded from current pay, from coverage, from every comparison, and from every export of current pay; it is
  displayed in the timeline labelled *"takes effect on <date>"* (BR-3.6).
- **AC-193-18** A future-dated record becomes current **by the passage of time**, with no job, no flip and no
  scheduler — verified by a test that sets the record's date to tomorrow, advances the evaluation date, and asserts
  the new value is returned with no intervening write.
- **AC-193-19** **A backdated record produces no arrears, no adjustment and no recalculation of anything.** The
  confirmation screen states this in plain language (§1 out-of-scope, CC-42-18).
- **AC-193-20** A record whose `effective_from` is before the employee's `join_date` is refused (`422`).

### 10.5 The rehire boundary (B42-19, BR-3.7)

- **AC-193-21** A compensation record is **not in effect** on any date after `exit_date` for an employee with a
  terminal status. Querying current pay for such an employee returns **"not employed"**, not the last salary.
- **AC-193-22** **After a rehire into the same `employees.id`, the pre-exit records are never returned as current.**
  On rehire, prior records are closed at the prior `exit_date` and marked as belonging to the prior employment
  period; the employee shows **"No salary recorded"** until a new record with `effective_from >=` the new join date
  is entered. **This is the single most important criterion in the story**: without it, the plain
  greatest-`effective_from`-≤-today rule silently pays a rehired employee their 2019 salary, and every surface —
  My Pay, the coverage meter, the equity engine — repeats the error consistently, which is what makes it hard to
  spot. Asserted end-to-end against a rehire fixture.
- **AC-193-23** A new record with `effective_from <= ` the prior period's `exit_date` is refused (`422`).
- **AC-193-24** Prior-period records remain visible on the timeline to `compensation:r` holders, **labelled with the
  employment period they belong to** (BR-7.26).

### 10.6 Validation, edge and boundary cases

- **AC-193-25** Amount `0`, negative, blank, non-numeric, or with more than 2 fractional digits is rejected with a
  field-level message before any write (BR-1.3). `60000.005` is rejected, not rounded.
- **AC-193-26** Amount above the sanity ceiling (BR-1.4, default 100,000,000.00) is refused with a confirmable
  override for `compensation:w` holders, and the override is recorded in the audit reason.
- **AC-193-27** Currency not in the ISO 4217 list, lowercase, or 2/4 characters is rejected (BR-1.2). There is no
  defaulted currency.
- **AC-193-28** FTE `0`, negative, `> 1.00`, blank or with more than 2 decimals is rejected (BR-2.4). For an
  employee whose `employment_type = 'PART_TIME'`, a blank FTE is rejected with a specific message — **it is not
  defaulted to 1.00**, because a defaulted 1.00 on a part-timer is the most damaging silent error in the arithmetic.
- **AC-193-29** Pay basis outside `{ANNUAL, MONTHLY, HOURLY}` is rejected. Where basis is `HOURLY`, the UI states
  that FTE is recorded but is **not** re-applied in normalisation (BR-2.5), because an engineer or an HR user
  reading the number will otherwise assume it is.
- **AC-193-30** A blank or whitespace-only reason is rejected (`400`) before any write.
- **AC-193-31** A record for an employee with `company_id IS NULL` is refused (CC-42-14).
- **AC-193-32** A record for a **non-ACTIVE** employee is refused (`422`) except through the retention/void paths;
  offboarding creates no record (BR-7.18).
- **AC-193-33** Values round-trip exactly: `59999.99` written and read back is `59999.99`, and appears as such in the
  JSON payload — never `59999.990000000005` (CC-42-17). Asserted with a set of values chosen to break binary floats.
- **AC-193-34** A record may be created for a **contractor or intern**. They are excluded from **comparison**
  (BR-2.7), not from **record-keeping** — a contractor's day rate is real data. Their compensation surfaces show
  *"Not applicable — Contractor"* for comparison purposes while still showing the recorded figure to
  `compensation:r` holders (BR-6.1).

### 10.7 Error and failure behaviour

- **AC-193-35** Any failure rolls back the record and its audit row together; there is never a record without an
  audit row, nor an audit row describing a record that does not exist (CC-42-6).
- **AC-193-36** Replaying the same create returns `409` with the existing record and writes no second row and no
  second audit row (CC-42-20).
- **AC-193-37** Two actors writing a record for the same employee and the same `effective_from` concurrently:
  exactly one succeeds; the other receives `409` and writes nothing (AC-193-15).
- **AC-193-38** A request for a compensation record by an id belonging to another company returns `403`, reads
  nothing back and writes nothing.
- **AC-193-39** No error message, validation message, stack trace or log line contains an amount (CC-42-21).

### 10.8 Permissions and tenant isolation

- **AC-193-40** Every route is `@require_feature_access('compensation', 'r'|'w'|'d')`; there is no hardcoded role
  list (CC-42-1). Row scoping is the §4.8 matrix, enforced server-side (BR-8.3).
- **AC-193-41** An `r`-only holder receives `403` with no state change from every write and void endpoint
  (CC-42-10, BR-8.8).
- **AC-193-42** A `w` grant without `r` is refused as a configuration by the Feature Access tab, naming the reason
  (BR-8.9).
- **AC-193-43** All queries are company-scoped (CC-42-11). A PORTAL_ADMIN of company A retrieves zero of company B's
  records under every filter, every search term, every date range and every export.
- **AC-193-44** A SYSTEM_ADMIN with **All Companies** selected cannot write a compensation record (CC-42-13) and
  sees no cross-tenant list (CC-42-12).

### 10.9 Retention

- **AC-193-45** Compensation records carry retention class **`EMPLOYMENT`**; the clock runs from `exit_date` on the
  employee's existing per-company retention period (EP38 R3.1, default 7 years — BR-7.6). No second clock is
  introduced.
- **AC-193-46** At retention expiry, **the amount and currency are destroyed** and the row is marked `PURGED`,
  retaining `effective_from`, FTE, pay basis and level/step so the shape of the history survives (§4.7.4). A purged
  record displays as *"Amount destroyed at retention expiry on <date>"* — never as zero, never as blank (CC-42-19,
  BR-7.27), and the purge writes a `COMPENSATION_PURGED` audit row.
- **AC-193-47** Automatic purge at expiry is a **Should**, dependent on EP38 **OQ-4** (there is no scheduler —
  SPM S16). The **Must** for this cycle is: a stated class, a **visible** expiry date and days remaining on the
  record, and a **manual "purge now"** action on an expired record for `compensation:d` holders.
- **AC-193-48** Erasure behaviour is exactly §4.7.5: the amount is **retained** at erasure and the free-text reason
  is **NULLed**; the erasure records `ERASURE_PARTIALLY_REFUSED` naming the retained category, the ground and the
  retention expiry date (BR-7.8).

### 10.10 Out of scope (KAN-193)

Any variable pay component — bonus, commission, equity, pension, allowances, benefits (§3.3, OQ-5) · a computed
"total compensation" figure · payroll, payslips, gross-to-net, deductions, banking details · currency conversion or
FX (BR-1.7) · retroactive pay calculation (AC-193-19) · pay for candidates or offers (there is no ATS) · a
compensation record for a non-employee · the read surfaces themselves (KAN-194 gates them, KAN-202 builds the
timeline) · the import (KAN-195).

---

## 11. KAN-194 — Who may see a salary (W2 · D5) — **nothing may render a salary before this lands**

### 11.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-194 | As an **employee, manager and HR admin**, I want to see exactly the pay I am entitled to see and nothing else, so the most sensitive data in the product is safe by default. | Three feature codes registered in **all four places**; the §4.8.2 default matrix seeded as a ceiling a tenant may widen or narrow with **no extra checks in any route**; **row scoping in the service layer** (manager → direct reports only, one level) with the CC-2 distinction written down; **"My Pay"** on the employee's own profile, server-scoped to `session['employee_id']`, never from a parameter; `r`/`w`/`d` separable; **`_MONEYISH_KEYS` guard added to `audit_service`**; an amount is **absent from the JSON payload** — not hidden in the DOM — for every role lacking scope, asserted across every surface in §4.8.4. | Must Have · P1 |

### 11.2 Feature registration

- **AC-194-01** The three codes `compensation`, `compensation_self` and `pay_equity` are registered in **all four
  places**: `portal_features` in `setup_db.py`, a numbered migration under `database/migrations/`,
  **`database/seed_rbac.sql`**, and default `role_feature_access` rows **in both the migration and the seed**
  (CC-42-7). `TestFeatureRegistryHasNoDrift` fails if any one is missed — verified by deliberately removing the seed
  row in a scratch branch and observing the failure. *(This is the DEF-004 lesson, and it applies three times.)*
- **AC-194-02** A **fresh CI database** built the way CI builds one — `schema.sql` + `seed_rbac.sql`, migrations
  **not** replayed — contains all three features and all their default grants, and the whole compensation suite
  passes against it.
- **AC-194-03** Seeded `role_feature_access` defaults are exactly CC-42-7's table. `SYSTEM_ADMIN` needs no row
  (CC-42-3).
- **AC-194-04** All three codes are seeded `company_features.is_enabled = FALSE` for every existing tenant
  (CC-42-8, OQ-7).
- **AC-194-05** **`compensation_self` is a separate code, not a setting**, so that a PORTAL_ADMIN narrowing who can
  see *other people's* pay does not silently blind every employee to their own — and so that a tenant who keeps pay
  in payroll can switch self-view off through the mechanism that already exists (D5.1). Verified: narrowing
  `compensation` to zero roles leaves every employee's My Pay working.

### 11.3 The response matrix — the highest-value test surface

- **AC-194-06** Every cell of §4.8.2 is asserted, for **both** the HTML surface and the JSON payload, for **every
  listed role**, against a fixture tenant containing: the actor, one direct report, one skip-level report, one
  dotted-line report, one same-department non-report, one same-location non-report, one unrelated colleague, and one
  employee of a second company.
- **AC-194-07** `200−amt` means the **key is absent from the JSON object** — not `null`, not `""`, not `"***"`, not
  `0`, not present-and-hidden. Asserted on the parsed payload, not on the rendered page (BR-8.4).
- **AC-194-08** `200−amt` in HTML means **no element containing the value exists in the response body**. A
  CSS-hidden salary is a leak that passes a screenshot review and it must fail this test (SPM §8.4.2).
- **AC-194-09** `403` on a **JSON** endpoint is a JSON body with a machine-readable code and **no state change**
  (BR-8.5). *(Per B42-03 this is not what `@require_feature_access` does today — CFL-42-8.)*
- **AC-194-10** A **solid-line manager sees one level down, not the subtree** (BR-8.7). Their skip-level report's
  amount is `200−amt`. Asserted with a three-level chain.
- **AC-194-11** A manager's **dotted-line** reports' amounts are `200−amt` by default. Dotted lines do not carry pay
  visibility.
- **AC-194-12** **DEPARTMENT_HEAD, LOCATION_HEAD, HIRING_MANAGER and COMPANY_ADMIN default to no pay visibility at
  all** — `200−amt` for everyone including people in their own department or location (BR-8.7). This will surprise
  someone; it should.
- **AC-194-13** Granting `compensation` read to any of those roles through the **Feature Access tab** immediately
  gives them their role's defined scope, with **no code change and no extra check anywhere in any route**
  (CC-42-9, CC-42-2). Asserted by toggling the matrix in a test and re-running the payload assertions.
- **AC-194-14** Narrowing `compensation` read for `SOLID_LINE_MANAGER` through the tab immediately removes their
  reports' amounts from every payload, without a logout.
- **AC-194-15** Where a user holds several roles, their scope is the **union** (BR-8.1). Asserted with a user
  holding both `SOLID_LINE_MANAGER` and `HR_ADMIN`.

### 11.4 Row scoping — and why it is not the forbidden sub-flag

- **AC-194-16** Row scoping lives in the **service layer** and is applied to the query, not to the response after
  the fact (BR-8.3). A test asserts that the SQL issued for a manager's compensation read is constrained to their
  `DIRECT` set — the server never fetches the company's rows and then filters them.
- **AC-194-17** **There is no per-feature role check inside any route.** The distinction is written into the
  Architect's ADR and restated here so an engineer reading CC-42-2 does not conclude that scoping is banned: the
  **feature flag** answers *"may this role reach this surface at all"*; the **row scope** answers *"which rows does
  the surface return for this user"*. The forbidden `enabled_for_hr` pattern **denied a granted role access to a
  feature**; a scope does not (SPM D5.3).
- **AC-194-18** A scope never narrows below what the matrix grants for that role's defined scope, and never widens
  above it. Asserted in both directions.

### 11.5 The surfaces where an amount must not appear — the negative-visibility suite

- **AC-194-19** **`/api/employees` and `/api/my-team` contain no compensation field, for any role.** These two
  endpoints are the sharpest edge in the epic: `/api/employees` is `@login_required` **only** and scopes with a
  hardcoded role list that hands the whole company to DEPARTMENT_HEAD, LOCATION_HEAD and HIRING_MANAGER — three
  roles that default to no pay access (B42-02). Asserted as an explicit negative for all ten roles.
- **AC-194-20** **`_EMP_SELECT` contains no compensation column.** Asserted directly against the projection's column
  list, because it feeds six surfaces at once and adding a column there exposes all six in one commit (B42-01).
  This single assertion is worth more than six per-surface ones and must be written as such.
- **AC-194-21** **The search index contains no amount.** `fn_update_employee_search()` indexes exactly
  `first_name, last_name, job_title, email` and the trigger fires on exactly those columns (B42-14); a test asserts
  the trigger's column list is unchanged, and that no application code writes `employee_search_index`.
- **AC-194-22** **No CSV export contains an amount for a role without scope.** Specifically asserted for
  `/api/analytics/export/csv`, whose column list is built from the result set
  (`csv.DictWriter(fieldnames=list(rows[0].keys()))` — B42-13), so a compensation column reaching an analytics query
  would reach the file with nobody adding it.
- **AC-194-23** **No notification body, bell entry, email or `ocSummary()` line contains an amount**, a compa-ratio,
  a gap percentage, or any number from which one could be derived (§4.8.4 rows 4, 5, 9).
- **AC-194-24** **No org-tree card, ancestor payload, tooltip or directory row contains an amount** for any role
  (§4.8.4 row 7).
- **AC-194-25** **No application log line or error message contains an amount** (CC-42-21). Asserted by driving a
  deliberate failure at each write path and grepping the captured log.
- **AC-194-26** **`_MONEYISH_KEYS` is added to `audit_service`** beside `_SECRETISH_KEYS`
  (`app/services/audit_service.py:97-98`), matched the same case-insensitive substring way, raising `AuditError`
  (BR-9.5). A test proves an amount written into a diff or into `metadata` is **refused**, not stored. *(Today it
  would be written verbatim — `_SECRETISH_KEYS` catches nothing money-shaped, and `_clean_diff` accepts any scalar.
  SPM S9.)* This is the Architect's file: **CFL-42-2.**
- **AC-194-27** The permitted compensation diff keys are exactly BR-9.2's list, and none of them collides with
  `_MONEYISH_KEYS`. A test asserts each permitted key is accepted and each money-shaped key is refused.

### 11.6 "My Pay" (`compensation_self`)

- **AC-194-28** "My Pay" sits on the employee's own profile, gated `@require_feature_access('compensation_self')`,
  and is **hard-scoped server-side to `session['employee_id']`**. The scope is **never** taken from a route
  parameter, a query string or a request body. Supplying another employee's id to the endpoint returns the caller's
  own data or `403` — never the other person's.
- **AC-194-29** It shows: current base amount, currency, FTE, pay basis, effective date, level, step and level
  title. Once bands exist (KAN-199) it shows **position in range as a plain-language statement**, not a raw
  compa-ratio number.
- **AC-194-30** It shows **history only if the tenant enables it** (default: current record only), through a
  company setting, PORTAL_ADMIN-only, audited.
- **AC-194-31** It shows **no comparison to anybody else, ever** — no group median, no band position of colleagues,
  no percentile within the team, no headcount of the comparison group.
- **AC-194-32** It contains **no forward-looking language** that could be read as a promise of a future increase
  (Charter §9.8, no dark patterns). UX owns the exact wording; it is the most easily misread copy in the epic
  (SPM §8.3.7).
- **AC-194-33** Where the employee has no record: *"No pay information recorded. Contact HR."* — never a blank,
  a dash or a zero (CC-42-19). Where the employee is a contractor or intern:
  *"Not applicable — <employment type>"* (BR-6.1).
- **AC-194-34** With `compensation_self` **disabled for the tenant**, the panel is absent from the page and from the
  payload, and the employee sees the AC-188-08 explanatory state if they navigate directly.
- **AC-194-35** The subject of a **pay-equity flag** learns nothing about it from My Pay. They are **not** a
  recipient (AC-201-08), and no flag state, no measured ratio and no group statistic appears on their own view.
  *(Their Art. 15 rights are separately satisfied per BR-7.11 to BR-7.14 — through a DSAR, with the disclosure floor,
  not through a self-service screen.)*

### 11.7 Error, edge and failure behaviour

- **AC-194-36** A user with no roles, or with a role holding none of the three codes, sees no compensation surface,
  no nav entry and no field in any payload.
- **AC-194-37** A user whose employee record has `company_id IS NULL` (SYSTEM_ADMIN account) has no My Pay panel and
  no compensation record (CC-42-14).
- **AC-194-38** Changing a user's roles mid-session takes effect on their **next request** — `g._feature_access` is
  per-request. Asserted by revoking `compensation` and confirming the next payload omits the amount without a
  logout.
- **AC-194-39** A hand-crafted API call supplying `?company_id=` for another tenant returns `403` and reads nothing
  back, for every role including the SYSTEM_ADMIN pathway at `app/routes/employees.py:145`.
- **AC-194-40** Where scoping resolves to an empty set (a manager with no reports), the response is `200` with an
  empty list and an explicit empty state — **not** `403`, and **not** the company's rows.

### 11.8 Tenant isolation

- **AC-194-41** Company A sees **zero** of company B's amounts under every filter, every search term, every export,
  every aggregate and every date range — including a SYSTEM_ADMIN with "All Companies" selected, who sees a
  "select a company" state instead (CC-42-12). Asserted as SPM §8.4.3 requires.
- **AC-194-42** No aggregate anywhere (count, sum, average, median, min, max, coverage percentage) spans companies,
  for any role.

### 11.9 The disclosure that must be said out loud

- **AC-194-43** **Under the current demo-grade authentication (email-only, one click, no password —
  `app/routes/auth.py:84-97`), this entire matrix is correct in code and unenforceable in practice**, because
  identity is self-asserted from the login tiles. Every compensation demo states this at the **start**, in the
  written script, not in answer to a question (SPM A-2, Demo Readiness Gate rule 5). A compensation demo without
  that line in the script is **NO-GO**.
- **AC-194-44** The persistent **"Demo compensation data — synthetic"** banner appears on every compensation screen
  while the environment is demo-grade (CC-42-24, SPM D8.3).

### 11.10 Out of scope (KAN-194)

Real authentication (EP28/KAN-148, stage S5 — and AC-194-43 is the honest statement of what that means for this
story) · field-level encryption or tokenisation of amounts at rest · per-record ACLs or sharing · a "who viewed this
salary" access log *(deliberately named: it is a reasonable ask and it is **not** in this cycle — the audit trail
records writes, not reads → **OQ-BA-5**)* · delegated or temporary pay access · break-glass access · masking
patterns (`***`) — the rule is absence, not masking · consent-based self-view.

---

## 12. KAN-195 — Backfill: bulk import, manual entry, coverage (W2 · R2 · D7)

### 12.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-195 | As **HR**, I want to load our existing salaries in bulk and fix individual rows by hand, so we can get to usable coverage in days rather than a quarter. | CSV import with **dry-run → diff → commit** reusing the EP35-S2 surface, not a second importer; **row-level error reporting with a reason per row, never a silent skip**; a file that would write null or zero over an existing salary is **rejected at preview**; atomic per batch; single-employee manual entry gated `compensation:w`; **"No salary recorded"** with a Record-salary action — never a blank, dash or zero; contractors and interns show **"Not applicable"**; a **company coverage meter** naming its denominator, with the missing list exportable and a reason per row; **no derived, estimated or imputed salary anywhere**; every run audited with row counts and actor. | Must Have · P1 |

### 12.2 Happy path — bulk

- **AC-195-01** The CSV shape is `employee_number, effective_from, currency, annual_base, fte, pay_basis, reason`.
  Header matching is case-insensitive; column order is irrelevant; a column map is offered where headers differ.
  *(Note the column is named `annual_base` but carries the amount **in the stated `pay_basis`** — a monthly figure
  goes in it with `pay_basis = MONTHLY`. The name is inherited from the SPM's D7 shape; the header text and the
  in-app guidance must say **"amount in the stated pay basis"** or every first import will be wrong by a factor of
  twelve. **[BA call]** — I recommend renaming the column to `amount`; recorded as **OQ-BA-7**.)*
- **AC-195-02** **Dry-run → diff → commit**, reusing the existing Bulk Import surface (EP35-S2), **not** a second
  importer. Upload → column map → preview → single atomic commit.
- **AC-195-03** The preview shows, per row: the employee (number and name), the action (**create** / **new record
  for an employee who already has one** / **error**), the parsed values, and the derived `annualised_base` and
  `fte_normalised_annual` so the actor can see the arithmetic **before** committing.
- **AC-195-04** The preview shows totals: rows, valid, errors, creates, changes, and the **coverage the company will
  have after the commit**. That last number is the adoption instrument.
- **AC-195-05** Commit is **one atomic unit of work** (CC-42-6, KAN-155): all valid rows land or none do. There are
  no per-row commits.
- **AC-195-06** The run writes one audit row per record created plus one run-level row carrying the actor, filename,
  row counts and a shared **correlation id**, so the whole import reads as one story. **No amount appears in any of
  them** (BR-9.1).

### 12.3 Happy path — manual

- **AC-195-07** A `compensation:w` holder records or corrects a single employee's compensation from the profile,
  with the full validation set of AC-193-25 to AC-193-34. Every tenant will need to fix one row without re-uploading
  a file, and an import-only design guarantees shadow spreadsheets.
- **AC-195-08** Manual entry and import produce **identical** records — same fields, same validation, same audit
  shape, same effective-dating rules. A record's origin (import run id or manual) is recorded but changes nothing
  about its behaviour.

### 12.4 Validation and the rules that stop a bad import

- **AC-195-09** **A row that would write null, blank or zero over an existing salary is rejected at preview**, per
  row, naming the employee and the reason. It is never committed and never silently skipped (D-185-1's lesson
  applied to a file — a whole column of blanks is the bulk version of the partial-proposal hazard).
- **AC-195-10** **Row-level errors are reported per row with the row number and a human-readable reason**, and the
  actor chooses to commit only the valid rows or abandon the run. **No row is ever skipped silently.**
  *(This is a direct correction of the existing importer's behaviour: `import_service.py:161-165` catches the
  exception, marks the row `SKIPPED` and surfaces no reason — B42-12. KAN-195 must not inherit that pattern, and the
  criterion is written so a reviewer can check it.)*
- **AC-195-11** Rejected row conditions, each with its own message: unknown `employee_number` · employee in another
  company · employee with `company_id IS NULL` · non-ACTIVE employee · amount ≤ 0, blank, non-numeric or > 2
  decimals · currency not ISO 4217 · FTE out of `0.01–1.00` · **FTE blank for a `PART_TIME` employee** (AC-193-28) ·
  `pay_basis` not in the enumeration · `effective_from` malformed, before `join_date`, before the current employment
  period, or outside the back/forward windows · a second row in the **same file** for the same employee and the same
  `effective_from` · a row duplicating an existing non-voided record's `(employee, effective_from)`.
- **AC-195-12** **Two rows in one file for the same employee** with **different** effective dates are both valid and
  both land, producing two timeline entries in date order. This must be supported: a backfill of history is exactly
  what a first import is.
- **AC-195-13** **No value is ever derived, estimated, imputed or defaulted from a band, a level, a group median, a
  colleague or a prior period** (CC-42-18, D7.6). An imputed figure reaching a screen or an export is
  indistinguishable from a real one. A blank amount is an error, never a guess.
- **AC-195-14** A file containing an amount for a **contractor or intern** is accepted (they may hold a record —
  AC-193-34) and the preview flags them as **excluded from comparison**, not as errors.

### 12.5 Coverage and the partial-data behaviour

- **AC-195-15** The compensation **coverage meter** on the compensation landing page states its denominator in
  words: *"Compensation data: 62% of active employees (91 of 146). Excludes 1 contractor and 0 interns."*
  (BR-6.2). Rounded HALF_UP to 1 dp.
- **AC-195-16** There are **two** coverage figures — compensation coverage and **level** coverage (KAN-191) — with
  **different denominators**, and every screen showing one names which it is (BR-4.3). Displaying an unlabelled
  "coverage: 62%" is a defect.
- **AC-195-17** Where the denominator is **0** — the empty "Sam Cpmapny" tenant (B42-20) — the meter reads
  **"—  (no employees in scope)"**. It is never rendered as 0% or 100% and never divides by zero (BR-4.4).
- **AC-195-18** The **missing list** is exportable to CSV, one row per employee, carrying the **reason**:
  `no salary` · `no level` · `no pay market — location not set` · `not applicable — <employment type>`. It contains
  **no amounts** (BR-6.3). *(The "no pay market" reason is real today: one ACTIVE Acme employee has a current
  assignment with a null location — B42-11.)*
- **AC-195-19** Every state in the §4.6 surface matrix renders as specified, in particular that **"No salary
  recorded"** and **"Not applicable — Contractor"** never look like each other and never look like a value
  (BR-6.1, CC-42-19).
- **AC-195-20** The coverage meter and the missing list are visible only to `compensation:r` holders; to everyone
  else they are absent from the page and the payload.

### 12.6 Error and failure behaviour

- **AC-195-21** A file whose header cannot be mapped is rejected at upload, listing the expected columns; nothing is
  written and no staging row is created.
- **AC-195-22** A malformed, empty, non-UTF-8, wrong-delimiter or non-CSV file is rejected with a specific message;
  no stack trace and no PII in the log (CC-42-21).
- **AC-195-23** A commit failure part-way leaves **zero** records and **zero** audit rows from that run, and the
  actor sees which row failed (CC-42-6).
- **AC-195-24** Re-committing the same preview returns `409` with the existing run's result; it does not double the
  records (CC-42-20).
- **AC-195-25** Two actors committing imports touching the same employee concurrently: the second fails on the
  `(employee, effective_from)` uniqueness rule (AC-193-15) and its **whole batch** rolls back, with the conflicting
  row named.
- **AC-195-26** An oversized file is rejected with a stated row limit rather than timing out.

### 12.7 Staging data and its retention — the table nobody thinks of

- **AC-195-27** Import staging rows hold **raw personal data including amounts**. They carry retention class
  `STANDARD` and are **hard-deleted** after a per-company window, default **30 days** from run completion, range
  1–90, audited (§4.7.4). This is the one EP42 table that is genuinely deleted.
- **AC-195-28** Staging rows are readable only by `compensation:r` holders of that company, are company-scoped, and
  are **deleted immediately** on an erasure request naming any employee in them (§4.7.5).
- **AC-195-29** Staging rows appear in **no** coverage figure, **no** comparison and **no** export other than the
  preview itself.

### 12.8 Permissions per role

| Role | Import | Manual entry | Preview only | See the coverage meter | Export the missing list |
|---|---|---|---|---|---|
| SYSTEM_ADMIN | Yes (company context, CC-42-13) | Yes | Yes | Yes | Yes |
| PORTAL_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes | Yes |
| HR_ADMIN | Yes (`compensation:w`) | Yes | Yes | Yes | Yes |
| SOLID_LINE_MANAGER (`compensation:r`) | No | No | No | **No** — the meter is a company aggregate and their scope is `DIRECT` | No |
| All other roles | No | No | No | No | No |

- **AC-195-30** Every route is `@require_feature_access('compensation', 'w'|'r')`; no hardcoded role list
  (CC-42-1). An `r`-only holder can view the meter but every import and entry endpoint returns `403` with no state
  change (CC-42-10).
- **AC-195-31** **A company-wide coverage percentage is a company-scope read.** A `DIRECT`-scoped holder does not
  see it, because "62% of 146" is an aggregate over rows they may not read. **[BA call]** — the alternative, showing
  a manager the company meter, leaks nothing individually but is inconsistent with the scope model, and consistency
  is what makes the model reviewable.

### 12.9 Tenant isolation

- **AC-195-32** A file naming an `employee_number` from another company is rejected **per row at preview**; nothing
  is written, and the error message names the row, not the foreign employee (CC-42-11, EP38 CC-10).
- **AC-195-33** The coverage meter, the missing list and every export are company-scoped; company B appears in none
  of them under any filter.
- **AC-195-34** A SYSTEM_ADMIN with "All Companies" selected cannot run an import and sees a "select a company"
  state (CC-42-12, CC-42-13).

### 12.10 Sequencing risk

- **AC-195-35** KAN-195 is written **against the EP35-S2 import-wizard contract**. If EP35-S2 has not landed when
  this story starts, the minimal importer built here is **refactored onto the wizard** when it does, and is not left
  as a parallel path (SPM R-9, DEP-6). This is an acceptance criterion so it is not quietly forgotten.

### 12.11 Out of scope (KAN-195)

Bulk **level** mapping (that is KAN-191) · payroll-system integration in either direction (EP40-S3) · salary history
import from a prior HRIS beyond this CSV shape · an "undo import" that reverses a committed run *(a correction is a
new record or a void — AC-193-07, AC-193-08)* · scheduled or recurring imports (no scheduler) · bulk **void** ·
importing bands, ladders or thresholds · any derived or estimated value (AC-195-13) · fixing the pre-existing
employee-importer defect DEF-42-1 (named in §20, owned separately — but KAN-195 must not copy its silent-skip
pattern, AC-195-10).

---

## 13. KAN-196 — The pay decision inside the position-change request (W3 · R3 · D4)

### 13.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-196 | As a **manager or HR admin**, I want a position change to carry its pay decision through the same approval, so a move is never applied with the pay question unanswered. | The compensation block lives **inside** the shared `templates/org_change/_move_modal.html` — one modal, one endpoint, one engine, three entry points; the pay decision is **mandatory to answer, not mandatory to change** — *No change · New salary · Defer (reason required)* — with **nothing pre-selected**; a money-bearing request is **refused at create time** if any chain step has no approver holding `compensation:r`, naming the step and writing nothing; **the apply never writes null or zero over an existing salary**, with a named regression test over five proposal shapes; the block is **absent** (not disabled) for a user without `compensation:r`, and the pay question then passes to the first `compensation:r` approver rather than being skipped; placement and pay share the KAN-189 effective date; nothing is applied until final approval and any rejection applies nothing. | Must Have · P1 |

### 13.2 Happy path

- **AC-196-01** A compensation block is added **inside** the existing shared move modal
  (`templates/org_change/_move_modal.html`, extracted under KAN-185). **One modal, one endpoint, one engine, three
  entry points** — org-tree drop, employee profile, directory row `⋯` (D4f). There is no second dialog and no second
  create path.
- **AC-196-02** The pay decision is **mandatory to answer, not mandatory to change**. Three options, **nothing
  pre-selected**:
  1. **No change** — recorded as an affirmative decision, with the current salary shown as context.
  2. **New salary** — amount, currency, FTE, pay basis, reason. The effective date is the **request's single
     effective date** (KAN-189); there is no separate pay date in this cycle (SPM §3.4).
  3. **Defer to a separate review** — reason **mandatory**, and it creates a visible follow-up rather than a silence.
- **AC-196-03** Submitting with the pay question unanswered returns **`422`** naming the field; **no request is
  created**. "Considered" is satisfied by a recorded answer and by nothing less — an unanswered optional field is
  precisely the status quo this story replaces.
- **AC-196-04** The recorded **"No change"** is itself the evidence that the question was considered, and it is
  visible to approvers, in the request detail and in the audit trail.
- **AC-196-05** All four existing proposed dimensions (BU, functional unit, location, manager) require the answer.
  **There is no "trivial change" exemption**, because deciding what is trivial is how exemptions grow.
- **AC-196-06** On **final** approval only, in **one** transaction (CC-42-6): the placement change applies
  (`_apply_change`), the compensation record is written with `effective_from = ` the request's effective date, the
  request closes, and every audit row is written with one shared correlation id.
- **AC-196-07** **Nothing is applied until the final level approves, and any single rejection applies nothing** —
  including no compensation record, no partial record and no draft (`CLAUDE.md` org-change invariant 3). Asserted by
  a direct DB query after a rejection: zero compensation rows for the subject from that request.
- **AC-196-08** A cancelled request applies nothing, by the same assertion.

### 13.3 Approver eligibility on a money-bearing request (D4b)

- **AC-196-09** **Definition, stated once so it is testable.** A request is **money-bearing** if it carries a
  `New salary` pay decision **or** a level/step change. A `No change` or `Defer` answer does **not** make a request
  money-bearing. *(This matters: without the definition, every transfer becomes a two-approver request and D4h's
  control becomes universal friction.)*
- **AC-196-10** At **create time**, every step of the resolved chain must be satisfiable by **at least one approver
  holding `compensation:r` in that company**. If any step cannot be, the request is **refused** (`422`), the message
  names **the step** and **the missing permission**, and **nothing is written** — no request, no approval rows, no
  notifications. *(This follows EP38 AC-184-18's pattern: block, name the reason, write nothing, rather than
  creating a request that stalls forever.)*
- **AC-196-11** **This check cannot be written with what exists today.** `_load_feature_access()` resolves the
  **session user's** access only (B42-04 / CFL-42-12); there is no function answering *"does user X hold feature F
  in company C"*. A non-session feature-access resolver is required and is the Architect's design.
- **AC-196-12** The check resolves `ROLE` steps to the active users holding that role in the company
  (`_step_approver_user_ids`, `app/services/org_change_service.py:83-99`) and `EMPLOYEE` steps to that named person,
  then tests each for `compensation:r`. A step whose only holder lacks it fails the check.
- **AC-196-13** **The escape hatch exists and is offered in the error.** The initiator may raise the **placement
  change without pay** (option 3, Defer) and the pay change as a **separate, subsequent** `COMPENSATION_REVIEW`
  (KAN-197). The refusal message says so. Sequential, not parallel — so it does not reopen the
  disagreement problem D4a solves.
- **AC-196-14** An approver who holds `compensation:r` sees the proposed amount, the current amount and the delta in
  the approval view. An approver on a **placement-only** request sees no compensation block at all.

### 13.4 The initiator without pay access — **CFL-42-13**

- **AC-196-15** A user who holds `org_change:w` but **not** `compensation:r` opens the modal with the compensation
  block **absent** — not disabled, not blank, not greyed. Absent from the DOM **and** absent from the prefill JSON
  payload (BR-8.4, D4f).
- **AC-196-16** **The pay question is deferred to an approver, not skipped.** The request they create is recorded
  with pay decision **`NOT_ANSWERED_NO_PERMISSION`**, and **the first chain step held by a `compensation:r` holder
  must answer the pay question before they may approve** — their approval control is disabled until they do, and
  the API refuses their approval with `422` naming the unanswered decision.
  > **This is a BA resolution of a conflict inside SPM §4, not a new requirement.** D4c says every position change
  > carries an explicitly-answered pay decision and the W3 gate says *"no position change can be applied without an
  > explicit, recorded pay decision"*; D4f says a user without `compensation:r` raises a placement-only `TRANSFER`.
  > Read together, any manager without pay access can route around the mandatory decision entirely, which is exactly
  > the hole R3 exists to close. Deferring the answer to the first approver who *can* see pay satisfies both rules
  > and gives the manager no pay visibility. **Logged as CFL-42-13; needs the SPM's ratification.**
- **AC-196-17** If **no** step in the chain is held by a `compensation:r` holder, the request is created as a
  genuinely placement-only `TRANSFER` with pay decision `NOT_APPLICABLE_NO_ELIGIBLE_APPROVER`, and the company's
  configuration is surfaced to `compensation:w` holders as a warning — not silently accepted.

### 13.5 The partial-proposal hazard — D-185-1 in a worse form (D4g)

- **AC-196-18** **A compensation apply may never write NULL or zero over an existing salary.** The apply overlays
  only what the request actually proposed, exactly as `_apply_change` now does for placement
  (`app/services/org_change_service.py:365-380`).
- **AC-196-19** **A named regression test** — the compensation equivalent of
  `TestApplyCarriesUnchangedFieldsForward` — asserts the **final database row**, not the API response, across all
  five proposal shapes:

  | # | Proposal shape | Required outcome |
  |---|---|---|
  | 1 | **Pay only** (`COMPENSATION_REVIEW`) | A new compensation record; **BU, FU, location, cost centre and manager byte-for-byte unchanged** |
  | 2 | **Placement only**, pay decision `No change` | Placement applies; **the existing compensation record is untouched** — no new record, no null, no zero |
  | 3 | **Level only** (`PROMOTION`, no pay change, reason recorded) | New level assignment; **compensation untouched**; placement untouched |
  | 4 | **Full** (placement + level + pay) | All three apply, in one transaction, sharing one effective date and one correlation id |
  | 5 | **No prior compensation record**, pay decision `No change` | **No record is created.** The employee remains "No salary recorded" — a `No change` against nothing must not manufacture a zero row |

  *(D-185-1 was a live data-loss defect that **all 4,628 tests passed through**, because every existing test passed a
  fully-populated proposal. The same shape applied to pay silently zeroes somebody's salary. Shape 5 is the one an
  engineer will not think of.)*
- **AC-196-20** A proposal that changes **nothing at all** — no placement dimension, no level, and a `No change` pay
  answer — is rejected at submission with `400` (AC-185-11 extended to the new dimensions).

### 13.6 Effective dating and concurrency

- **AC-196-21** Placement and pay share **one** effective date (KAN-189, D4d). The compensation record's
  `effective_from` **is** the request's `effective_date`.
- **AC-196-22** A `TRANSFER` may not carry a **future** effective date (AC-189-11); a pay-only
  `COMPENSATION_REVIEW` may, within the forward window (AC-189-12, BR-3.6a, CFL-42-10).
- **AC-196-23** **One PENDING request per subject, regardless of type.** Creating any request for a subject who
  already has a `PENDING` `org_change_requests` row returns `409` naming the existing request (AC-185-08 extended).
  *Why regardless of type:* a pending `TRANSFER` and a pending `COMPENSATION_REVIEW` can both write to the same
  employee on apply, and the second carries a stale "from" snapshot — which falsifies exactly the record the
  workflow exists to produce (EP38 CFL-5). It is also consistent with D4b's escape hatch, which is explicitly
  **sequential**.
- **AC-196-24** Where the request's effective date has **passed** by the time the final approval lands, the apply
  still uses the original date (AC-189-14) and the compensation record is created with that past `effective_from` —
  which may be outside the backdating window. **That is permitted**, because the date was validated at create time
  and approval latency is not the initiator's doing. Stated explicitly so nobody adds a second validation at apply
  time that starts rejecting approved requests.

### 13.7 Edge, error and failure behaviour

- **AC-196-25** The compensation block must **not make the common case heavier**: most moves carry no pay change.
  It opens **collapsed** with **nothing pre-selected**, costs **one deliberate click** to answer "No change", and
  adds **no extra scroll** to the existing flow. **UX owns proving this** (SPM §8.3.3); the acceptance test is a
  click count and a viewport check, not an opinion.
- **AC-196-26** "No change" cannot be selected by inertia — no default, no pre-check, no "continue" that implies it.
  The whole point is that it is an answer.
- **AC-196-27** A `New salary` answer runs the **full** AC-193-25…AC-193-34 validation set at submission, not at
  apply. An invalid amount never reaches an approver.
- **AC-196-28** A subject with **no** current compensation record: the block shows *"No current salary recorded"* as
  context (never a zero), `New salary` is permitted, and `No change` is permitted and creates nothing (shape 5).
- **AC-196-29** A subject who is a **contractor or intern**: the block shows *"Not applicable — <type>"*, and
  `New salary` is permitted but flagged as excluded from comparison (AC-193-34, AC-195-14).
- **AC-196-30** Where the subject's compensation changes **outside** the request between create and final approval,
  the approval view shows the **current** value alongside the value that was current at create time, and the
  approver is warned that the baseline moved. The apply still writes the proposed amount. **[BA call]** — the
  alternative (auto-refresh the baseline) hides a change from the person deciding.
- **AC-196-31** Any failure at any point rolls back placement, compensation, level and audit rows together; the
  request stays `PENDING` and the actor sees which step failed (CC-42-6).
- **AC-196-32** Replaying the final approval returns `409` with the existing state, writes no second record and no
  second audit row (CC-42-20).

### 13.8 Permissions and tenant isolation

- **AC-196-33** Routes remain `@require_feature_access('org_change', …)`; the compensation block's visibility is
  `compensation:r` and its write is `compensation:w`. **No hardcoded role list is added anywhere** (CC-42-1), and
  the existing `_can_initiate_for` business rule continues to sit **on top of** the feature gate, not in place of it.
- **AC-196-34** **An employee can never initiate their own move or their own pay change — including an admin.**
  A request whose subject is the requester's own employee record is refused (`403`, nothing written) for **every**
  role, including HR_ADMIN, PORTAL_ADMIN and SYSTEM_ADMIN. *(This is new enforcement, not a restatement:
  `_can_initiate_for` returns `True` for any admin regardless of subject and the API checks nothing else —
  B42-05 / CFL-42-14. Today that is a self-requested desk move; after this story it would be a self-requested pay
  rise.)*
- **AC-196-35** A `compensation:r`-only holder can see the block but cannot submit a `New salary`: `403`, no state
  change (CC-42-10).
- **AC-196-36** All prefill, picker and approver-resolution queries stay company-scoped, and approver resolution
  continues to match role **by name within the company** (CC-42-11, `CLAUDE.md` invariant 4).
- **AC-196-37** A proposed amount, currency or FTE supplied for a subject in another company returns `403` and
  creates no request, even with valid UUIDs supplied directly to the API.

### 13.9 Out of scope (KAN-196)

A **divergent** pay effective date (SPM §3.4 — Later) · a second approval chain for pay · budget-aware or
headcount-cost-aware approval (§3.3) · off-cycle increase workflows outside this engine · bulk position change ·
retroactive pay calculation · showing the approver a band, a compa-ratio or a peer comparison at decision time
*(**[BA call]** — genuinely useful, genuinely out of scope; the band exists only after KAN-199 and putting a
comparison in front of an approver is a design question UX has not been asked → **OQ-BA-8**)*.

---

## 14. KAN-197 — Promotion as a first-class request type (W3 · R4 · D4e — closes backlog open item #3 and EP38 OQ-1/CFL-7)

### 14.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-197 | As **HR**, I want promotion to be a first-class request with a salary review that cannot be skipped, so a promotion never quietly happens without a pay decision. | `request_type` ∈ `TRANSFER` · `PROMOTION` · `COMPENSATION_REVIEW` on `org_change_requests`, defaulting every existing row to `TRANSFER`; all three run on the **existing** engine, chain and apply path — no second engine; a `PROMOTION` proposes a new (family, level, step) and may also change placement; **"no change" on a promotion requires an explicit recorded reason**; a company may configure a **different chain per request type**, falling back to the `TRANSFER` chain, and no request ever runs with no chain; the KAN-139 rule holds for every type — **nobody, including an admin, initiates their own**; type is inferred from what changed; direction (`UP`/`DOWN`/`LATERAL`) is recorded; applied atomically with the level assignment and the compensation record. | Must Have · P1 |

### 14.2 Happy path

- **AC-197-01** `org_change_requests` carries `request_type ∈ {TRANSFER, PROMOTION, COMPENSATION_REVIEW}`. **Every
  existing row defaults to `TRANSFER`** in the migration, and every existing behaviour is unchanged for those rows
  — asserted by running the existing org-change test suite unmodified.
- **AC-197-02** All three types run on **the existing engine**: the same `create_request`, the same sequential
  `decide()`, the same `_apply_change`, the same notification vocabulary, the same retirement mechanism. **No second
  engine, no second apply path, no parallel workflow** (CC-42-5, `CLAUDE.md` invariant 5).
- **AC-197-03** `TRANSFER` proposes BU / functional unit / location / manager; pay decision **mandatory to answer**
  (KAN-196).
- **AC-197-04** `PROMOTION` proposes a new **(family, level, step)** and **may** also change placement. Pay decision
  mandatory to answer, and **"No change" requires an explicit recorded reason** — a promotion with no pay movement
  and no explanation is exactly what R4 exists to stop.
- **AC-197-05** `COMPENSATION_REVIEW` proposes **only** a pay change: no placement dimension and no level. This is
  D4b's escape hatch and the vehicle for an ordinary off-cycle increase. It is **not** a comp-review *cycle* (§3.3).
- **AC-197-06** On final approval, in **one** transaction: the level assignment is written (KAN-191's rules), the
  placement applies where proposed, the compensation record is written, the request closes, and all audit rows share
  one correlation id. A partial promotion — level applied, pay not — is the worst state in the epic and must be
  impossible (DEP-1, KAN-155).
- **AC-197-07** The applied promotion writes `PROMOTION_APPLIED` plus `JOB_LEVEL_CHANGED` audit rows carrying
  `level_from`/`level_to`, `step_from`/`step_to` and `level_direction`, and **no amount** (BR-9.2).

### 14.3 Type inference and direction

- **AC-197-08** The type is **inferred from what the user changed** in the shared modal (D4f): placement only →
  `TRANSFER`; level changed → `PROMOTION` (level wins even if placement also changed); pay only → `COMPENSATION_REVIEW`;
  nothing changed → `400` (AC-196-20). The inferred type is **shown to the user before submission** — an inferred
  classification the user cannot see is one they cannot correct.
- **AC-197-09** **`level_direction` is derived and recorded** on the request and on the resulting assignment, by
  comparing `(ordinal, step)` before and after: `UP` · `DOWN` · `LATERAL` (BR-5.10). *(Necessary because D4e routes
  downward moves through `request_type = PROMOTION`; without a recorded direction every promotion metric counts
  demotions as promotions. This does not change D4e — it makes the data readable.)*
- **AC-197-10** A **`DOWN`** direction requires an explicit confirmation naming the current and proposed level, and
  a mandatory reason, before submission (AC-192-05).
- **AC-197-11** **Skip-step and skip-level moves are permitted** with a mandatory reason and full audit (D3.4). The
  proposed level need not be `current + 1`.
- **AC-197-12** A proposed level in a **different family** is permitted and is flagged as a **family change** at
  confirmation, because it changes the subject's comparison group (AC-191-15).

### 14.4 Chains per type

- **AC-197-13** A company may configure a **different approval chain per request type** — a pay change may need a
  level a transfer does not.
- **AC-197-14** Where no chain is configured for a type, the **`TRANSFER` chain applies**; where no chain is
  configured at all, the existing `_DEFAULT_STEPS` single-HR_ADMIN fallback applies
  (`app/services/org_change_service.py:23-26`). **No request ever runs with no chain.**
- **AC-197-15** The chain in force is resolved and **frozen at create time** into `org_change_approvals` (existing
  behaviour). Changing the company's chain afterwards does not alter an in-flight request — asserted, because it is
  the property that makes an approval trail meaningful.
- **AC-197-16** The chain-configuration page shows which chain applies to which type, and shows the **fallback**
  explicitly rather than leaving the type blank.

### 14.5 The initiator rule — for every type, including admins

- **AC-197-17** **Nobody initiates their own request, of any type.** The subject may not be the requester's own
  employee record, for **every** role including HR_ADMIN, PORTAL_ADMIN and SYSTEM_ADMIN: `403`, nothing written
  (AC-196-34). *(New enforcement — B42-05 / CFL-42-14.)*
- **AC-197-18** The existing rule stands unchanged for everyone else: the requester must be the subject's current
  `SOLID_LINE` manager or hold `HR_ADMIN`/`PORTAL_ADMIN`/`SYSTEM_ADMIN` (`_can_initiate_for`,
  `CLAUDE.md` invariant 2). A plain `EMPLOYEE` receives `403` on every type.
- **AC-197-19** A `COMPENSATION_REVIEW` obeys the same initiator rule. **An employee can never request their own pay
  review through this product** — a self-service pay-rise request is a different feature with a different design and
  it is not in scope.
- **AC-197-20** **The subject may not approve their own request, of any type.** Where the subject holds a role that
  satisfies a step, `decide()` refuses with a specific message. *(New enforcement: `_user_matches_step` compares
  role to step and nothing compares the decider to the subject — B42-06 / CFL-42-15. Combined with B42-05, one
  HR_ADMIN can today raise and approve their own request end-to-end on the default chain.)*

### 14.6 Edge, error and failure behaviour

- **AC-197-21** A `PROMOTION` for a subject with **no current level assignment** is refused (`422`), directing the
  actor to assign a level first (KAN-191). There is no "promotion from nothing".
- **AC-197-22** A `PROMOTION` proposing the subject's **current** (family, level, step) with no placement and no pay
  change is rejected as a no-op (`400`).
- **AC-197-23** A `PROMOTION` proposing an **archived** level is refused (`422`) (AC-191-16).
- **AC-197-24** A `PROMOTION` proposing a step outside `1 … steps_count` of the proposed level is refused (`422`).
- **AC-197-25** Where the ladder changes **between** create and final approval such that the proposed level is
  archived or the proposed step no longer exists, the apply **fails safe**: the whole transaction rolls back, the
  request stays `PENDING`, and the approver sees a specific error naming the ladder change. Nothing is applied
  partially. **[BA call]** — the alternative (silently clamp the step) applies something nobody approved.
- **AC-197-26** A `COMPENSATION_REVIEW` with a `No change` pay decision is rejected at submission (`400`) — a pay
  review that changes no pay and has no placement or level component is a no-op.
- **AC-197-27** All of AC-196's rules apply unchanged to `PROMOTION` and `COMPENSATION_REVIEW`: the mandatory pay
  answer, the create-time approver-eligibility check, the five overlay shapes, the single-PENDING-request rule, the
  shared effective date, and nothing applied before final approval.
- **AC-197-28** A subject offboarded while a request of any type is pending has it `CANCELLED` and not applied
  (EP38 R2.11 / AC-185-14), and the subject's level assignment closes at `exit_date` (BR-7.19).
- **AC-197-29** Any failure rolls back level, placement, compensation, request status and audit rows together
  (CC-42-6). There is no state in which a level moved and pay did not, or the reverse.

### 14.7 Permissions and tenant isolation

- **AC-197-30** Routes are `@require_feature_access('org_change', …)` for the request and `compensation:r`/`:w` for
  the pay block; **no hardcoded role list** (CC-42-1). A level change is a `compensation:w`-class action, so a
  solid-line manager may **initiate** a promotion for their report but the chain decides it.
- **AC-197-31** Approver resolution matches role **by name within the company** (`CLAUDE.md` invariant 4), and all
  queries are company-scoped (CC-42-11).
- **AC-197-32** A proposed family or level belonging to **another company** returns `403` and creates no request,
  even with a valid UUID supplied directly to the API (mirrors AC-185-16 for org units).
- **AC-197-33** **Cross-company promotion is not supported.** `employees.company_id` is never modified; an attempt
  returns `403` (EP38 AC-185-19).

### 14.8 Closing three long-standing open items

- **AC-197-34** This story **closes backlog open item #3, EP38 OQ-1 and EP38 CFL-7**: promotion is KAN-197 in EP42,
  and is explicitly **not** a variant of KAN-185. The BA records EP38 OQ-1 as **answered** and EP38 CFL-7 as
  **resolved** when this document is consolidated in Wave 3.
- **AC-197-35** **Backlog open item #4** (the boundary between the transfer flow and EP27's drag-and-drop) is
  answered by AC-196-01: one modal, one endpoint, one engine, three entry points. The drag-and-drop path is not a
  second way to do the same thing; it is a third way to open the same thing.

### 14.9 Out of scope (KAN-197)

Promotion nomination, calibration or talent-review rounds (§3.3) · eligibility rules based on time in level, tenure
or performance (AC-192 out-of-scope; and performance data does not exist) · a promotion budget or a promotion quota ·
bulk promotion · automatic level roll-up (D3.4) · a self-service pay-review request by the employee (AC-197-19) ·
title change without a level change *(the working title is edited through the existing profile edit — BR-5.11)* ·
cross-company moves (AC-197-33).

---

## 15. KAN-198 — Four eyes on money (W3 · D4h — closes backlog open item #5)

> **Contingent on OQ-9** (owner ratification) **and CFL-42-5** (Architect sign-off — it changes `decide()` in the
> shared engine and therefore changes behaviour for EP27 and EP38 as well as EP42).

### 15.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-198 | As a **compliance owner**, I want two different people to be required on any approval chain that moves money, so a two-level control is not one person twice. | For any request carrying a **compensation or level** change: a user who has decided one level **cannot** decide another on the same request — refused with a message naming the level they already decided; **not configurable, not overridable**, and it **binds SYSTEM_ADMIN too**; **the subject may never decide any level of their own request**, of any type; a money-bearing request whose resolved chain has fewer than **two independently-satisfiable** levels is refused at create time, naming the configuration; for **placement-only** requests: warn, allow, and record it in `audit_log` as a self-approval; the chain-configuration page **shows the overlap at configuration time**; behaviour change applies to EP27 and EP38 and both regression suites are extended. | Must Have · P1 |

### 15.2 The hard rule — money and level

- **AC-198-01** For any **money-bearing** request (AC-196-09: a `New salary` pay decision **or** a level/step
  change), a user who has already recorded a decision on **any** level of that request **cannot** decide another.
  The second decision is refused with a message **naming the level they already decided**.
- **AC-198-02** The rule is **not configurable, not overridable and has no warn-and-allow mode**. There is no
  setting, no per-company toggle and no admin override.
- **AC-198-03** **The rule binds every role, including SYSTEM_ADMIN.** *(Deliberate exception to CC-42-3, stated
  with its reasoning: SYSTEM_ADMIN's automatic bypass is a **feature-access** rule — it answers "may this role reach
  this surface". Four-eyes is a **business control** on a decision, not a surface. A control that SYSTEM_ADMIN can
  satisfy alone is not a control, and under the current demo-grade authentication anybody can be SYSTEM_ADMIN
  (`app/routes/auth.py:84-97`). The only escape is another human.)*
- **AC-198-04** **The subject may never decide any level of their own request, of any type — money-bearing or not.**
  Refused with a specific message. *(New enforcement: nothing in `decide()` compares the decider to
  `req['employee_id']` — B42-06 / CFL-42-15.)*
- **AC-198-05** **The initiator may not decide a money-bearing request they raised.** **[BA call]** — the standard
  segregation is initiator ≠ approver; without it, an HR_ADMIN raises a pay rise for a colleague and approves it,
  which is one person's decision wearing two hats. → **OQ-BA-9** for the SPM, because it is a policy call with a
  workflow cost in a small tenant.
- **AC-198-06** Refusal returns `409` with **no state change**: no decision recorded, no step advanced, no
  notification sent, no audit row describing a decision that did not happen.
- **AC-198-07** The refusal is enforced **server-side in `decide()`**, not by hiding the control. The bell's quick
  approve (`quickApproveOrgChange`, `templates/base.html:642-655`) must also handle the refusal cleanly — it must not
  optimistically remove the item from the bell when the server refused (a DEF-003-adjacent failure).

### 15.3 The chain must actually have two people — **CFL-42-11**

- **AC-198-08** A **money-bearing** request whose resolved chain has fewer than **two independently-satisfiable
  levels** is **refused at create time** (`422`), naming the configuration and the missing level, and **writing
  nothing**.
- **AC-198-09** *"Independently satisfiable"* means: there exist at least two levels, and there exists an assignment
  of distinct people to those levels such that every level is satisfied. Two `ROLE` levels both naming `HR_ADMIN`
  in a company with **one** active HR_ADMIN is **not** independently satisfiable and is refused.
- **AC-198-10** **Why this criterion exists.** `_DEFAULT_STEPS` is a **single** `HR_ADMIN` level
  (`app/services/org_change_service.py:23-26`), applied whenever a company has no configured chain — which is the
  state of every tenant today. On a one-level chain there is no second level to refuse, so **without AC-198-08 the
  control decided in D4h is a no-op in a default-configured tenant** (B42-07). A control that only works in tenants
  that already configured a chain is not a control. **CFL-42-11.**
- **AC-198-11** To keep the feature usable out of the box, the **seeded default chain for `PROMOTION` and
  `COMPENSATION_REVIEW`** is **two `ROLE` levels — `HR_ADMIN` then `PORTAL_ADMIN`** — while `TRANSFER` keeps the
  existing single-`HR_ADMIN` default. **[BA call]**, and it is a product default the SPM should ratify →
  **OQ-BA-10**. Without it, every tenant hits AC-198-08 on their first pay change.
- **AC-198-12** The refusal message names the escape: configure a second level, or raise the placement change
  without pay (AC-196-13).

### 15.4 Placement-only requests — warn, allow, record

- **AC-198-13** For a **placement-only** request (no pay decision of type `New salary`, no level change), a user who
  has decided one level **may** decide another. Behaviour is unchanged from today.
- **AC-198-14** Before the second decision, the UI shows a **warning** naming the level they already decided and
  stating that this will be recorded as a self-approval. The warning is not a blocker.
- **AC-198-15** The second decision writes a `SELF_APPROVAL_RECORDED` audit row with retention class **`SECURITY`**,
  carrying the request id, both levels, the actor and the correlation id of the request.
- **AC-198-16** AC-198-04 (the subject may not decide) applies to placement-only requests too. That one is not a
  warning.

### 15.5 Making the overlap visible at configuration time

- **AC-198-17** The approval-chain admin page **shows the overlap when the chain is configured**: *"Levels 1 and 2
  can both be satisfied by the same person (Ana Costa holds HR_ADMIN and is the named approver at level 2)."*
  Shown when it is cheap to fix, not when a request is stuck.
- **AC-198-18** The page shows, per level and per request type, the **count of people who can satisfy it today**,
  and warns where any level has **zero** or **one**.
- **AC-198-19** Where a chain is configured such that money-bearing requests would be refused at create time
  (AC-198-08), the page says so **at configuration time**, naming the request types affected.
- **AC-198-20** The overlap analysis is company-scoped and resolves roles **by name within the company**
  (CC-42-4, `CLAUDE.md` invariant 4).

### 15.6 Edge, error and failure behaviour

- **AC-198-21** A single-level chain on a **placement-only** request is unaffected: one person decides, as today.
- **AC-198-22** Where a request **becomes** money-bearing after creation — it cannot under AC-196-02, since the pay
  decision is fixed at create time — the rule is evaluated against the request's recorded decision, not against a
  later edit. Stated so nobody adds an edit path that quietly changes the class of a request mid-flight.
- **AC-198-23** Where the only eligible approver for level 2 is the person who decided level 1, the request
  **stalls** rather than being auto-approved or auto-escalated. The stall is **visible**: the request detail names
  the reason, and `compensation:w` holders see it in the queue. **[BA call]** — a silent stall is the EP38 B9 failure
  mode, and the fix is a configuration change, not an override.
- **AC-198-24** A SYSTEM_ADMIN can resolve a stall by **appointing another approver** or **cancelling the request** —
  not by deciding twice (AC-198-03).
- **AC-198-25** Replaying a refused decision returns `409` with the same message and writes nothing (CC-42-20).
- **AC-198-26** Two eligible approvers deciding the same level concurrently: exactly one decision is recorded; the
  other receives `409` with the current state. *(Existing `decide()` re-reads `current_step` and `status` inside its
  transaction; this criterion asserts the property rather than assuming it.)*

### 15.7 Blast radius — EP27 and EP38

- **AC-198-27** The change is in the **shared** `decide()`, so it changes behaviour for **EP27 drag-and-drop moves
  and EP38 transfers** as well as EP42. Both regression suites (`tests/ui/test_browser.py`,
  `tests/ui/test_vacation_workflow.py`) are **extended**, not merely re-run, and the existing 93 + 39 checks
  continue to pass.
- **AC-198-28** No existing **placement-only** flow changes behaviour except for the AC-198-14 warning and the
  AC-198-15 audit row, and the AC-198-04 subject rule. Every other existing approval path behaves identically,
  asserted before and after.
- **AC-198-29** This story **closes backlog open item #5**. The BA records it resolved in Wave 3.

### 15.8 Permissions and tenant isolation

- **AC-198-30** The rule adds **no** feature gate and **no** role list; it is a guard inside the engine (CC-42-1,
  CC-42-5).
- **AC-198-31** The overlap analysis and every query in this story are company-scoped (CC-42-11); a PORTAL_ADMIN of
  company A sees nothing of company B's chains or approvers.

### 15.9 Out of scope (KAN-198)

A general segregation-of-duties framework across other workflows (vacation approval, user administration, role
grants) · delegation or "approve on behalf of" · time-boxed approval delegation during absence *(a real gap, and it
interacts badly with this rule — named so it is not forgotten → §23)* · approval reminders or escalation on a stall
(AC-198-23 makes the stall visible; chasing it is not in scope) · an approval SLA · configurable four-eyes for
placement-only requests (AC-198-02: not configurable, either way).

---

## 16. KAN-199 — Salary bands per level × pay market (W4 · D3.5 · D1 basis)

### 16.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-199 | As a **customer admin**, I want salary bands for each level in each pay market, so pay decisions have an intended range and not just an average. | A band is `(job_level, pay_market) → min, midpoint, max, currency, effective_from`; a **pay market** is a company-defined grouping of locations defaulting to **one per `locations.country`**, normalised case-insensitively; an optional **target point** (percentile) per step, guidance only; **compa-ratio** computed and displayed to `compensation:r` holders; **out-of-band pay is allowed, flagged and requires a reason — never hard-blocked**; a merged multi-currency market is **refused** unless an effective-dated FX rate exists for every currency in it, with **no silent 1:1**; every band and market change audited. | Should Have · P2 |

### 16.2 Pay markets

- **AC-199-01** A **pay market** is a company-defined, named grouping of that company's locations. Name mandatory,
  unique within the company case-insensitively after trimming.
- **AC-199-02** **The default is one pay market per `locations.country`**, generated on first use and freely
  editable. PORTAL_ADMIN may merge countries into one market or split a country into several by assigning individual
  locations.
- **AC-199-03** Every location belongs to **at most one** pay market. A location in none is valid and means its
  employees resolve to **no** pay market (BR-4.2) — they are counted with reason
  *"no pay market — location not in a market"*, not silently dropped.
- **AC-199-04** **Country grouping normalises the free-text value**: trimmed and compared case-insensitively, so
  `Germany`, `GERMANY` and ` germany ` produce **one** market, not three. *(`locations.country` is free text
  `varchar(100)` with genuinely inconsistent casing in the seed data — Acme uses `Germany`, "Sam Cpmapny" uses
  `INDIA`/`UK`/`US` — B42-10.)*
- **AC-199-05** The generated default market **displays the country string as it was first encountered** and lists
  the variant spellings it absorbed, so an admin can see that `UK` and `United Kingdom` were treated as one and
  correct it if they were not meant to be. Silent merging of two real markets is as bad as splitting one.
- **AC-199-06** **Locations with `company_id IS NULL` never appear** in any tenant's market configuration, picker or
  grouping (CC-42-15). *(One exists today: `Wroclaw IT center`, Poland — B42-10.)*
- **AC-199-07** Changing a location's market, or a market's membership, **triggers re-evaluation of every affected
  group** (BR-4.25 / BR-4.29(c)) and is audited (`PAY_MARKET_CHANGED`) with before → after membership.

### 16.3 Bands

- **AC-199-08** A band is `(job_level, pay_market) → (min, midpoint, max, currency, effective_from)`. All five are
  mandatory. Amounts follow §4.1; the currency follows BR-1.2.
- **AC-199-09** **Validity: `min <= midpoint <= max`**, all `> 0`, all in the same currency. A band violating this is
  rejected with a field-level message before any write. `min == midpoint == max` is permitted (a single-point band)
  and produces a compa-ratio of exactly 1.000 for anyone at that value.
- **AC-199-10** Bands are **effective-dated** and follow §4.3: at most one band in effect for a
  `(level, market)` pair on any date, no overlapping day, append-only, corrections are new bands, errors are voids.
- **AC-199-11** **Steps do not carry bands.** A step may optionally carry a **target point** — a percentile
  (integer 0–100) within the level's band — which is **guidance only** and is **never enforced, never defaulted into
  a pay decision and never used as a comparison basis** (D3.5).
- **AC-199-12** **Compa-ratio** is computed per BR-4.11 and displayed to `compensation:r` holders wherever an amount
  is shown in scope. To the **subject** on My Pay it is shown as a **plain-language position-in-range statement, not
  a raw ratio** (AC-194-29).
- **AC-199-13** Every band create, change and void writes a `PAY_BAND_CHANGED` audit row with field-level
  before → after, actor, mandatory reason and correlation id. **A band is company configuration, not an individual's
  pay, so band figures may appear in the audit diff** — this is a deliberate, stated exception to BR-9.1, which
  concerns an *individual's* amount. *(Named explicitly so the `_MONEYISH_KEYS` guard's key list does not
  accidentally block band audit rows: band diffs use keys `band_min`, `band_mid`, `band_max`, which do **not**
  contain any `_MONEYISH_KEYS` substring. **[BA call]**, and it needs the Architect's confirmation under CFL-42-2.)*

### 16.4 Out-of-band pay — flagged, never blocked

- **AC-199-14** A salary **below the band minimum or above the band maximum is allowed**. It is **flagged** at entry
  and requires a **reason**; it is **never hard-blocked**. Red-circled legacy pay and genuine market premiums exist,
  and hard-blocking pushes the decision off-system — which is the problem the epic started with (D3.5).
- **AC-199-15** The out-of-band condition is a **separate, independent signal** from the Check A outlier flag
  (BR-4.17). An employee may be out of band and not flagged by Check A, or flagged by Check A and inside the band.
  Both are shown, both are explained, and neither is derived from the other.
- **AC-199-16** Out-of-band status is shown on the profile, in the move modal's context, in the approver's view of a
  money-bearing request, and in the equity queue as an explanatory factor. It appears **nowhere** to a viewer
  without `compensation:r`.
- **AC-199-17** Changing a band such that existing employees become out of band does **not** change their pay and
  raises **no** flag retroactively for the band change alone; it does trigger re-evaluation of the affected groups
  (BR-4.29(c)) and the out-of-band status becomes visible.

### 16.5 Currency and the FX refusal

- **AC-199-18** A pay market has **one currency**, taken from its bands. Where a market contains locations in
  countries with different currencies, that is permitted **only** if every currency in the market has an
  **effective-dated, manually-maintained FX rate** on the evaluation date. Otherwise the configuration is
  **refused** with a message naming the currencies (D1).
- **AC-199-19** **There is no silent 1:1, no implicit conversion and no default rate, ever** (BR-1.7). An absent rate
  refuses the configuration; it never assumes parity.
- **AC-199-20** **FX rate feeds are out of scope** (SPM §3.4). Where the default configuration is used — one market
  per country — **no FX is needed at all**, which is true for both populated seed tenants (SPM S3, OQ-6).
- **AC-199-21** Where a band's currency differs from a compensation record's currency for an employee in that
  market, **no compa-ratio is computed** for that employee; they are reported with reason *"currency mismatch"* and
  are excluded from the compared set (BR-2.7, BR-4.14).

### 16.6 Edge, error and failure behaviour

- **AC-199-22** A band for an **archived** level is permitted to exist (people are still on it) but no new band may
  be created for it.
- **AC-199-23** A band for a level in a family with no assignments is valid; it simply matches nobody.
- **AC-199-24** A market with **zero** locations is valid and matches nobody; it is shown as such, not as an error.
- **AC-199-25** Deleting a pay market referenced by any band or any historical evaluation is refused (`409`);
  **archive** is offered instead, with the same semantics as an archived level (AC-190-13).
- **AC-199-26** Every validation failure is reported before any write, at field level, with the offending value
  named. Concurrent band edits follow AC-190-23 (`409`, current state shown, no silent overwrite).
- **AC-199-27** Any failure rolls the band, its market membership changes and its audit rows back together
  (CC-42-6).

### 16.7 Permissions and tenant isolation

- **AC-199-28** Band and market configuration is `@require_feature_access('compensation', 'w')`; there is **no
  hardcoded role list** (CC-42-1). Default write holders are HR_ADMIN and PORTAL_ADMIN (CC-42-7).
- **AC-199-29** **Band figures are `compensation:r` data.** A role without it sees no band, no midpoint, no
  compa-ratio and no out-of-band marker — absent from the payload, not hidden (BR-8.4).
- **AC-199-30** Bands, markets and location membership are company-scoped (`company_id = %s::uuid` only). A
  PORTAL_ADMIN of company A sees zero of company B's bands and markets, under every filter, and cannot assign a
  location of company B to a market of company A (`403`, nothing written).
- **AC-199-31** There is **no** cross-tenant band, no shared benchmark and no global default band (CC-42-12).

### 16.8 Out of scope (KAN-199)

External market or benchmark data feeds (§3.3) · band derivation from market data · FX rate **feeds** (AC-199-20 —
manual, effective-dated rates only, and only where a merged market forces it) · automatic band progression or
indexation · geographic differential *engines* beyond the pay-market grouping key · band modelling ("what if we
raised L3 by 3%") · enforcing a band on a pay decision (AC-199-14) · communicating bands to employees as ranges
(pay-transparency statements are §3.3) · a step's target point being used as a comparison basis (AC-199-11).

---

## 17. KAN-200 — The pay-equity comparison engine (W4 · R5 · D1) — the arithmetic

### 17.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-200 | As **HR**, I want the system to tell me where pay in the same job and market is out of line, so I find it before an employee or a regulator does. | Comparison group = `(company, job_family, job_level, pay_market)` — **never `job_title`, never step**; basis = **compa-ratio to band midpoint where a band exists, else the group median** — **never pairwise**; compared value = **FTE-normalised annualised base** per §4.2, contractors and interns excluded and the exclusion counted; **Check A** individual outlier (default `< 0.950` / `> 1.100`, `n >= 3`); **Check B** group **gender pay gap** (default `>= 5.0%`, `n >= 5`, `>= 2` of each gender, **and a gender-coverage sub-gate**); below a minimum → *"insufficient comparison group"*, **never a flag**; **coverage gate** default 80% → *"insufficient coverage — not evaluated"*, zero flags; equity disabled for a company until coverage crosses the gate once; **every threshold, minimum, gate and market definition configurable per company by PORTAL_ADMIN only, every change audited**; evaluation **event-driven plus on-demand — no batch**; every screen carries plain-language framing that this is a **measurement, not a compliance conclusion**. | Must Have · P1 |

### 17.2 Group formation

- **AC-200-01** The group key is `(company_id, job_family_id, job_level_id, pay_market_id)` (BR-4.1). **Never
  `job_title`** — measured, not asserted: Acme has 41 distinct titles over 46 people with exactly one title reaching
  n≥3; Telia 75 over 100 (B42-20, SPM S2). **Never step** — steps are *designed* to differ in pay, so grouping by
  them would flag the ladder itself, every time.
- **AC-200-02** Step is carried into every finding as an **explanatory factor**, displayed alongside the subject.
- **AC-200-03** **Group population** and **compared set** are exactly BR-4.3's definitions, and every surface that
  shows a count names which one it is showing.
- **AC-200-04** Every exclusion is **counted and displayed by reason**, never silent (BR-2.7): contractor · intern ·
  non-ACTIVE · no compensation record · no level · no pay market · currency mismatch. The group view shows
  `n compared / m in group` plus the exclusion breakdown.
- **AC-200-05** `PART_TIME` employees are **included**, via FTE normalisation (BR-2.5).
- **AC-200-06** An employee with **no level assignment** is in **no group at all** and appears in neither count
  (BR-4.3, AC-191-12).
- **AC-200-07** An employee whose pay market cannot be resolved is excluded with reason *"no pay market"*
  (BR-4.2). *(Real today: one ACTIVE Acme employee has a current assignment with a null `location_id` — B42-11.)*
- **AC-200-08** Group membership is evaluated **as at the evaluation date**, using the level assignment and
  compensation record in effect on that date (§4.3). A future-dated record does not affect today's evaluation
  (AC-193-17).

### 17.3 Coverage gates

- **AC-200-09** **Group coverage** = `|compared| ÷ |population|`, HALF_UP to **1 dp** (BR-4.3), compared against the
  per-company **coverage gate**, default **80.0%**, range 50–100. Evaluated **first**, before any check.
- **AC-200-10** Below the gate: state `NOT_EVALUATED_COVERAGE`, the group reports *"insufficient coverage — not
  evaluated"*, and it produces **zero** flags. Boundary asserted: **79.9% → not evaluated; 80.0% → evaluated**
  (WE-3).
- **AC-200-11** Where `|population| = 0`, coverage displays **"—  (no employees in scope)"**, the gate is not met,
  nothing is evaluated and nothing divides by zero (BR-4.4). Asserted against the empty "Sam Cpmapny" tenant
  (B42-20).
- **AC-200-12** **Equity is disabled for a company until its overall compensation coverage crosses the gate at least
  once** (D7.4). Until then the queue shows the coverage meter and the missing list — **never** an empty
  "no findings ✓" state, which at 40% coverage reads as "we are fine" and is the most dangerous screen the epic
  could ship.
- **AC-200-13** **k-anonymity:** where `|population| <= 2`, the group is listed with **counts only** — no median,
  no ratio, no band position, to any audience (BR-4.7).

### 17.4 Check A — individual outlier

- **AC-200-14** **Basis selection** per BR-4.8: band midpoint where a band is in effect for `(level, market)`,
  otherwise the group median. The basis used is **recorded on the flag and displayed**.
- **AC-200-15** **Minimum group size `|compared| >= 3`.** Below it: `INSUFFICIENT_GROUP`, **never a flag**
  (BR-4.9). Boundary asserted at 2 and 3.
- **AC-200-16** **Median** computed exactly per BR-4.10: over the multiset, ascending; odd n → the middle value;
  **even n → the mean of the two middle values**, HALF_UP to 2 dp; duplicates count separately; **the subject's own
  value is included**.
- **AC-200-17** **Ratio** = `fte_normalised_annual ÷ comparator`, HALF_UP to **3 dp** (BR-4.11).
- **AC-200-18** **Thresholds** default `< 0.950` (LOW) and `> 1.100` (HIGH), both **strict** — exactly 0.950 and
  exactly 1.100 are **not** flagged (BR-4.12). Configurable per company: low 0.50–1.00, high 1.00–2.00.
- **AC-200-19** **Never pairwise** (BR-4.13). One person, one finding. A group of ten produces at most ten findings.
- **AC-200-20** **WE-4 is asserted verbatim** as a fixture with hand-computed answers:
  {54,000 · 58,500 · 60,000 · 61,000} → median **59,250.00**; ratios 0.911 / 0.987 / 1.013 / 1.030; **one** flag.
  Adding 90,000 → median **60,000.00**; ratios 0.900 / 0.975 / 1.000 / 1.017 / 1.500; **two** flags.
- **AC-200-21** **WE-5 boundaries are asserted verbatim**: at median 60,000 — 57,000 → 0.950 → **no flag**;
  56,999.99 → **no flag** (rounds to 0.950); 56,940 → 0.949 → **flag**; 66,000 → 1.100 → **no flag**;
  66,060 → 1.101 → **flag**.
- **AC-200-22** **The n=3 property is asserted**: with three compared and a median basis, the middle member's ratio
  is exactly 1.000 and can never be flagged. **The n=2 property is asserted** as the justification for the minimum:
  both members are equidistant from the midpoint, so both would flag or neither.
- **AC-200-23** **WE-6 (band basis) is asserted verbatim**: band mid 62,000 → 54,000 → 0.871 → flag LOW and in band;
  75,000 → 1.210 → flag HIGH and out of band.

### 17.5 Check B — group gender pay gap

- **AC-200-24** **Check B is switchable per company, independently of Check A, and is OFF by default** (BR-7.1).
- **AC-200-25** **Check B cannot be switched on until a PORTAL_ADMIN records a lawful-basis acknowledgement** — a
  basis reference, actor and timestamp, written as a `PAY_EQUITY_BASIS_ACKNOWLEDGED` audit row (BR-7.2). The product
  does not judge the answer; it refuses to compute the statistic until the controller records that they have one.
  *(This exists because `employees.gender` was collected for **vacation eligibility** and reusing it for a pay-gap
  computation is a new purpose under Art. 5(1)(b) — §4.7.3, B42-09. **DPO-1.**)*
- **AC-200-26** **Formula** exactly BR-4.18: `gap = (median_male − median_female) ÷ median_male`, each median per
  BR-4.10, result HALF_UP to **3 dp**, displayed as a percentage to 1 dp.
- **AC-200-27** **Minimums** exactly BR-4.19: `|compared| >= 5` **and** `>= 2` compared MALE **and** `>= 2` compared
  FEMALE. Below any: `INSUFFICIENT_GENDER_GROUP`, **never a flag**. A single-gender group is never evaluated.
- **AC-200-28** **Gender-coverage sub-gate** (BR-4.20): at least **80%** of the compared set must have a recorded
  gender. Below it: `NOT_EVALUATED_GENDER_COVERAGE`, zero flags, reporting *"gender not recorded for n of m
  compared"*. *(Necessary because gender is NULL for 100% of the seeded population and is self-declared — a gap
  computed over a self-selected minority is biased, not weak. **[BA call]**, not in D1.)*
- **AC-200-29** `OTHER` and unrecorded genders are **excluded from Check B's medians** and **counted and displayed**;
  they remain fully in Check A (BR-4.21). The screen states this.
- **AC-200-30** **Threshold** default **5.0%**, range 1–50, per company. Flag when `|gap| >= threshold` —
  **inclusive**, so exactly 5.0% flags (BR-4.22). The **signed** value and its **direction** are recorded and
  displayed; a gap in either direction is a finding.
- **AC-200-31** **WE-7 is asserted verbatim**: MALE {60,000 · 62,000 · 66,000 · 70,000} → median 64,000;
  FEMALE {57,000 · 58,000 · 61,000} → median 58,000; `gap = 0.09375` → **0.094** → **9.4% → FLAG**, direction
  *in favour of MALE*. Reversed → **−0.103** → **FLAG**, direction *in favour of FEMALE*. Boundary: 60,000 vs
  57,000 → **0.050 → 5.0% → FLAG** (inclusive).
- **AC-200-32** **No individual's gender appears on any equity surface** (BR-7.5). Check B publishes group medians
  and counts only.

### 17.6 The FTE and annualisation arithmetic — hand-computed fixtures

- **AC-200-33** **WE-1 is asserted verbatim** as a fixture: E1 annual 60,000 @ 1.00 → 60,000; E2 monthly 3,000 @ 0.60
  → 36,000 → **60,000**; E3 hourly 32.50 @ 1.00 → **58,500**; **E4 hourly 30.00 @ 0.50 → 54,000 — not 108,000**;
  E5 monthly 3,000 @ 1.00 with `monthly_payments_per_year = 14` → **42,000**.
- **AC-200-34** **The E4 case has its own named test.** Applying FTE twice to an hourly rate is the most likely
  arithmetic defect in the epic (BR-2.5) and the fixture must be written by someone other than the engine's author
  (SPM §8.4.4, R-12).
- **AC-200-35** **The E5 case has its own named test.** Acme has a Porto (Portugal) office where 14 monthly payments
  is the norm; multiplying by 12 understates base pay by ~17%, which is more than three times the gap threshold and
  would manufacture a finding out of a payroll convention (BR-2.3).
- **AC-200-36** No intermediate value is rounded; rounding happens once, at the end, HALF_UP (BR-1.5). Asserted with
  a fixture whose answer differs if intermediate rounding is applied.
- **AC-200-37** **Currency guard**: a compared set containing more than one currency yields
  `NOT_EVALUATED_CURRENCY`, **zero** flags and a configuration warning to `pay_equity:w` holders. **No conversion,
  no 1:1** (BR-4.14, BR-1.7).

### 17.7 Configuration

- **AC-200-38** Every parameter is **per company, PORTAL_ADMIN-only, with the defaults shown as defaults, and every
  change audited** (`PAY_EQUITY_THRESHOLD_CHANGED`) with before → after: Check A low bound (0.50–1.00), Check A high
  bound (1.00–2.00), Check A minimum group size (2–50), Check B threshold (1–50%), Check B minimum group size
  (2–50), Check B minimum per gender (1–25), gender-coverage sub-gate (0–100%), coverage gate (50–100%), validity
  window (1–60 months), pay-market definitions.
- **AC-200-39** **Nothing is hardcoded.** *"Let's say 5%"* is the owner explicitly telling us it is a parameter
  (D1). A test asserts that changing each parameter changes the engine's output accordingly.
- **AC-200-40** A parameter change **triggers re-evaluation** of every affected group (BR-4.25) and is a **re-fire
  condition** (BR-4.29(c)).
- **AC-200-41** Threshold configuration is refused to anyone but PORTAL_ADMIN and SYSTEM_ADMIN: `403`, no state
  change — including to an HR_ADMIN who holds `pay_equity:w` (they work the queue; they do not set the thresholds
  they are measured by). **[BA call]** consistent with D1's "PORTAL_ADMIN only".

### 17.8 Evaluation cadence

- **AC-200-42** Evaluation is **event-driven plus on-demand. There is no batch and no schedule** (SPM S16 — there is
  no scheduler; do not design around one). Triggers are exactly BR-4.25's list.
- **AC-200-43** A backdated record that does **not** become the currently-effective one triggers **no**
  re-evaluation (BR-4.26, WE-2).
- **AC-200-44** **"Run equity check"** on the queue is available to `pay_equity:w` holders, runs synchronously for a
  single company, reports what it evaluated and what it skipped and why, and is audited.
- **AC-200-45** An evaluation **records the values it used** — medians, counts, coverage, thresholds, basis — at the
  moment it ran. Later changes produce a **new** evaluation, never a rewritten one (BR-4.31).
- **AC-200-46** Periodic automatic re-evaluation is **Later**, dependent on KAN-163 (DEP-7). No criterion in this
  story assumes it.

### 17.9 Framing — what the product must never claim

- **AC-200-47** Every equity screen carries plain-language framing that the product **computes a measurement, does
  not determine whether work is of equal value, and does not decide whether a gap is objectively justified**
  (D1.3, BR-7.16). The framing is on the screen, not in a help article.
- **AC-200-48** **No product surface and no documentation claims or implies that the product makes a customer
  compliant with any pay-transparency law** (SPM R-10). Asserted by review of every string the story adds.
- **AC-200-49** The base-only limitation is **stated on the screen, not hidden**: the comparison uses base pay, and
  bonus and variable pay are not modelled (D1, §3.3, OQ-5).

### 17.10 Error and failure behaviour

- **AC-200-50** An evaluation that cannot complete for a group leaves that group's **previous** evaluation intact,
  records the failure with a reason, and does **not** raise, retire or alter any flag for it.
- **AC-200-51** An evaluation failure for one group does not abort the run for other groups; the run reports its
  partial result honestly.
- **AC-200-52** No amount, ratio, median or gap appears in any log line or error message (CC-42-21).
- **AC-200-53** The engine's group queries are verified against the **real-DB integration tier** (KAN-168, DEP-4).
  Group formation, medians and coverage gates cannot be verified against mocks.

### 17.11 Permissions and tenant isolation

- **AC-200-54** Every route is `@require_feature_access('pay_equity', 'r'|'w')`; no hardcoded role list (CC-42-1).
  Defaults are HR_ADMIN r+w and PORTAL_ADMIN r+w (CC-42-7); everyone else none.
- **AC-200-55** **`pay_equity` read does not imply `compensation` read.** A holder of `pay_equity:r` without
  `compensation:r` sees ratios, gaps, counts and states — but **no absolute amounts** (BR-8.4). **[BA call]**, and
  it is the configuration a works-council representative or an auditor would be given. *(Note: a ratio plus a
  visible median is an amount with one arithmetic step removed, which is why AC-200-13's k-anonymity floor and
  BR-7.13's disclosure floor both exist.)*
- **AC-200-56** A group is evaluated **within one company only**. There is **no cross-tenant group, median, gap or
  aggregate, for any role including SYSTEM_ADMIN** (CC-42-12). Asserted with an identical `(family, level, market)`
  configured in two tenants: the two groups never merge and never see each other's members.
- **AC-200-57** A SYSTEM_ADMIN with "All Companies" selected sees a "select a company" state, not a merged queue.
- **AC-200-58** All queries are company-scoped, and roles are resolved by name within the company (CC-42-11,
  CC-42-4).

### 17.12 Out of scope (KAN-200)

Any statistical method beyond §4.4's arithmetic — regression, explained/unexplained decomposition, controlled
analysis, significance testing, confidence intervals (§1) · pairwise comparison (AC-200-19) · comparison across
levels, families, markets or tenants · statutory gender-pay-gap **report generation or filing** (§3.3) · any
non-binary gender pay gap computation *(the schema offers `MALE`/`FEMALE`/`OTHER`; a three-way gap has no agreed
definition and `OTHER` group sizes would breach AC-200-13 immediately — **[BA call]**, and it is named rather than
silently omitted)* · comparison of anything other than base pay (OQ-5) · scheduled re-evaluation (AC-200-46) ·
remediation cost modelling · the flag's delivery and lifecycle (KAN-201).

---

## 18. KAN-201 — Flag delivery, the queue and the lifecycle (W4 · R5 delivery · D2)

### 18.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-201 | As the **pay-equity responsible**, I want each finding to reach me, stay in one place until I have dealt with it, and then go away, so the queue is worth working. | Recipients = holders of `pay_equity` read in that company **plus** an optional per-company named escalation list that **adds recipients and can never remove access**; the primary surface is a **queue** at `/compensation/equity` with filters and per-flag disposition; **bell: a new "Pay Equity" section, feature-gated, hidden when empty, icon ⚖️, counted in the badge, one quick action "Review →" — no dispose-from-the-bell**; **notification bodies contain no amount and no invertible percentage**; lifecycle `OPEN → JUSTIFIED / REMEDIATION_PLANNED / RESOLVED / RESOLVED_BY_DATA` with a **mandatory reason on every disposition** and a category on `JUSTIFIED`; **retires via `resolve_related()` on disposition for every eligible recipient — not on read**; a `JUSTIFIED` flag **does not re-fire** within its validity window unless BR-4.29's conditions are met; **no bulk disposition**. | Must Have · P1 |

### 18.2 Who the "HR responsible" is

- **AC-201-01** **No new role.** The recipients of a pay-equity flag are **the holders of `pay_equity` read in that
  company**, resolved exactly the way every other feature audience is resolved (D2.1). Seeded defaults: HR_ADMIN
  r+w, PORTAL_ADMIN r+w, everyone else none. SYSTEM_ADMIN needs no row (CC-42-3).
- **AC-201-02** A company may **optionally** name **0..n specific employees** as escalation recipients in company
  settings. Where the list is non-empty, those people are notified **in addition to** the matrix holders.
- **AC-201-03** **The named list may never remove access from anybody the matrix grants.** It adds recipients; it
  does not gate the feature. A list that could deny is the `enabled_for_hr` mistake wearing a different hat
  (CC-42-2). **This is an explicit criterion because it is exactly the kind of thing that gets implemented as a
  filter by accident**: a test configures a named list of one person and asserts that every matrix holder still
  receives the notification and still sees the queue.
- **AC-201-04** A named recipient who does **not** hold `pay_equity:r` receives the **notification** but sees no
  amounts and no ratios in the queue beyond what their own feature access allows (AC-200-55). Adding somebody to a
  list is not a grant.
- **AC-201-05** Changing the escalation list is PORTAL_ADMIN-only and audited.

### 18.3 The queue — the primary surface

- **AC-201-06** The primary surface is a **queue** at `/compensation/equity`, gated
  `@require_feature_access('pay_equity')`. A pay-equity flag is a **standing condition**, not a task: conditions
  belong in a register you can filter, sort, disposition and report on. The bell is how somebody *discovers* there
  is something in the register.
- **AC-201-07** Columns: subject, level, pay market, group size, basis (band midpoint / group median), measured
  value, threshold in force, raised date, state, owner. Filters by state, group, check, age and owner.
- **AC-201-08** **The subject of a flag is not a recipient** and does not see the queue by virtue of being a
  subject. Their Art. 15 rights are satisfied separately, through a DSAR, with BR-7.13's disclosure floor
  (AC-194-35).
- **AC-201-09** **No bulk disposition.** Each flag is dispositioned individually with its own reason (D2.2). A
  bulk "mark all justified" is a one-click dismissal of a compliance control and is not offered.
- **AC-201-10** Where equity is not yet evaluable for the company (AC-200-12), the queue shows the **coverage meter
  and the missing list**, not an empty "no findings" state.

### 18.4 The bell — D4's blind-spot list, every row answered

- **AC-201-11** **Section.** A **new fourth section, "Pay Equity"**, placed after "Position Changes" and before
  "My Notifications" (`templates/base.html:290-320`).
- **AC-201-12** **Gating.** `{% if has_feature_access('pay_equity') %}` — **feature-gated, never role-gated**
  (CC-42-1). *(The existing "Pending Approvals" section is role-gated — `templates/base.html:292` — and is
  explicitly **not** the pattern to copy.)*
- **AC-201-13** **Visibility.** The section is rendered **only when the viewer has ≥1 flag in `OPEN` state**, and is
  hidden entirely otherwise. **Never** an empty "no findings ✓", which could be read as "we are fine" while coverage
  is 40% (D7).
- **AC-201-14** **Icon.** `PAY_EQUITY_FLAG_RAISED → '⚖️'`, added to `NOTIF_ICON` (`templates/base.html:608-623`).
  **Never `❌`** — a standing condition is not a rejection (DEF-002) — and the neutral `🔔` fallback stays
  (`templates/base.html:624`).
- **AC-201-15** **Badge.** `OPEN` flags visible to this user are counted in the existing bell badge total, and the
  count is correct for a user who is both a matrix holder and a named recipient (counted once, not twice).
- **AC-201-16** **Quick action.** Exactly **one: "Review →"**, deep-linking to the queue filtered to that flag.
  **No dispose-from-the-bell.** *(The precedent is explicit: reject is a deep link and not a quick action precisely
  because a decision without a recorded reason is not auditable — `templates/base.html:639-641`. Dismissing a
  pay-equity finding is exactly that decision.)*
- **AC-201-17** **No amount in the body.** The message names the subject, the group and that a threshold was
  exceeded. **No salary, no median, no ratio, and no percentage from which an amount could be inverted** (BR-9.1,
  §4.8.4 row 4). Notification bodies are readable by anyone who can read the row and are **not** scoped by
  `compensation:r`.
- **AC-201-18** **Retirement.** On the flag leaving `OPEN` — any disposition, or `RESOLVED_BY_DATA` — via
  `notification_service.resolve_related()` with `related_type = 'pay_equity_flag'` and `related_id = <flag id>`
  (`app/services/notification_service.py:122-141`, the mechanism migration 09 added for DEF-003).
- **AC-201-19** **It does not retire on read.** Reading is not deciding. This is the DEF-003 failure mode in reverse
  and **must be asserted by test**: open the bell, read the item, reload, and assert it is still there.
- **AC-201-20** **It retires for every eligible recipient, not only the one who acted** — DEF-003's actual defect.
  Asserted across **at least three** recipients (SPM §8.4.5).
- **AC-201-21** **Four actors are walked** for the Demo Readiness Gate D4 check: a recipient with an open flag; a
  recipient **after somebody else dispositioned it**; a user without `pay_equity`; and **the subject of the flag**,
  who is not a recipient and must see nothing.

### 18.5 The lifecycle

```
                     re-evaluation finds the condition below threshold
        ┌───────────────────────────────────────────────────────────┐
        │                                                           ▼
     OPEN ──► JUSTIFIED (reason + category mandatory, validity window)   RESOLVED_BY_DATA
        │
        ├──► REMEDIATION_PLANNED (owner + target date mandatory) ──► RESOLVED
        │
        └──► RESOLVED (gap closed by an actual pay change)
```

- **AC-201-22** **Every disposition requires a recorded reason.** There is **no one-click dismiss anywhere in the
  product** (D2.3).
- **AC-201-23** `JUSTIFIED` additionally requires a **justification category** from a company-configurable list —
  seniority · tenure in role · performance · market premium · red-circled legacy pay · other (free text mandatory).
  The list is PORTAL_ADMIN-editable and audited.
- **AC-201-24** `REMEDIATION_PLANNED` requires a named **owner** (an ACTIVE employee of the company) and a
  **target date** (today or future). It transitions to `RESOLVED` only through an explicit action or through
  `RESOLVED_BY_DATA`.
- **AC-201-25** `RESOLVED_BY_DATA` is set **automatically** when a re-evaluation finds the condition below threshold
  — including because the subject's pay changed, the group changed, or the group ceased to be evaluable
  (BR-7.21, BR-7.22). It requires no human action and is audited with the reason that caused it.
- **AC-201-26** **Every state transition writes an audit row** (`PAY_EQUITY_FLAG_DISPOSITIONED`) with actor,
  before → after state, category, reason and correlation id — and, per BR-9.1, **without the amount and without the
  measured value**.
- **AC-201-27** A flag can never return to `OPEN`. A recurrence is a **new** flag (BR-4.30), linked to the old one
  by `superseded_by`, so the earlier disposition and the person who made it are never overwritten.

### 18.6 The anti-fatigue rule

- **AC-201-28** A `JUSTIFIED` flag **does not re-fire** for the same suppression key
  `(subject, group, check, basis)` while its justification is inside its **validity window** — default 12 months,
  company-configurable 1–60 (BR-4.27, BR-4.28).
- **AC-201-29** It re-fires early **only** under BR-4.29's precisely-stated conditions: the measured value crosses
  `bound ∓ 0.020` (Check A) or `threshold + 0.020` (Check B, i.e. +2 percentage points); or the subject's level,
  step or currently-effective compensation record changes; or the company changes a threshold, minimum, gate,
  pay-market definition, or a band for that level × market. Each of the six sub-conditions has its own test.
- **AC-201-30** **This rule is a requirement, not an optimisation.** Without it, every re-evaluation re-raises every
  previously-justified finding, HR mutes the channel — `notification_mutes` already exists — and the organisation
  then believes it has a control it does not have (SPM R-1, the Critical risk of the epic).
- **AC-201-31** The **quality tripwire** is instrumented: the proportion of flags dispositioned `JUSTIFIED` on first
  review is measurable per company. Above **40%** it is surfaced to PORTAL_ADMIN as a prompt to review the threshold
  or the grouping — not as a defect and not as a nag (SPM §1.5).
- **AC-201-32** Muting the Pay Equity notification channel does **not** remove flags from the queue, does not change
  their state and does not suppress the badge on the queue itself. Muting silences a channel; it must not silence a
  control.

### 18.7 Edge, error and failure behaviour

- **AC-201-33** A flag whose **subject is offboarded** is auto-dispositioned `RESOLVED_BY_DATA` with reason
  *"subject offboarded"* and retired for **every** recipient (BR-7.22).
- **AC-201-34** A flag whose **group ceases to be evaluable** — dropping below `n = 3`, below the coverage gate, or
  becoming multi-currency — is auto-dispositioned `RESOLVED_BY_DATA` with reason *"comparison group no longer
  evaluable"* and retired (BR-7.21).
- **AC-201-35** A flag whose **subject's compensation record is voided** re-evaluates immediately; where the subject
  leaves the compared set, the flag is `RESOLVED_BY_DATA`.
- **AC-201-36** Two recipients dispositioning the same flag concurrently: exactly one succeeds; the other receives
  `409` with the recorded disposition, and no second audit row is written (CC-42-20).
- **AC-201-37** A disposition with a blank reason, or `JUSTIFIED` without a category, or `REMEDIATION_PLANNED`
  without an owner or a target date, is refused (`400`) before any write.
- **AC-201-38** A `REMEDIATION_PLANNED` owner who is subsequently offboarded leaves the flag in state with the owner
  shown as a former employee and a prompt to reassign — the flag is **not** silently reassigned and **not** closed.
- **AC-201-39** Any failure rolls the disposition, its audit row and the notification retirement back together
  (CC-42-6); notifications are sent **after** commit (the existing engine rule).
- **AC-201-40** No amount, median, ratio or gap appears in any log line or error message (CC-42-21).

### 18.8 Permissions and tenant isolation

- **AC-201-41** Every route is `@require_feature_access('pay_equity', 'r'|'w')`; no hardcoded role list (CC-42-1).
  Reading the queue is `r`; dispositioning is `w`; an `r`-only holder receives `403` with no state change from every
  disposition endpoint (CC-42-10).
- **AC-201-42** A holder of `pay_equity:r` without `compensation:r` sees states, counts, ratios and gaps but **no
  absolute amounts** (AC-200-55).
- **AC-201-43** A user without `pay_equity` sees no queue, no bell section, no badge contribution and no flag in any
  payload.
- **AC-201-44** Flags, dispositions, escalation lists and categories are company-scoped. A `pay_equity:r` holder in
  company A sees **zero** of company B's flags under every filter, every search term and every export (CC-42-11).
- **AC-201-45** Notifications are delivered only to recipients within the subject's company (AC-192-31's rule,
  applied here).
- **AC-201-46** A SYSTEM_ADMIN with "All Companies" selected sees a "select a company" state, never a merged queue
  (CC-42-12).

### 18.9 Out of scope (KAN-201)

Bulk disposition (AC-201-09) · email or Slack delivery of flags *(in-app only; email would ride on the existing
dispatcher and is not requested)* · an SLA, escalation ladder or automatic reminder on an ageing flag *(the §1.5
measure is instrumented; chasing is not built)* · a remediation **plan** with costed actions and budget approval ·
notifying the **subject** of a flag (AC-201-08) · exporting the queue to a regulator-shaped filing (§3.3) ·
cross-tenant benchmarking of flag rates · a "pay equity score".

---

## 19. KAN-202 — Compensation history and the audit coupling (W4 · D5.6)

### 19.1 Backlog-style summary

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| KAN-202 | As **HR or a compliance owner**, I want to see how someone's pay got to where it is, without pay amounts leaking into the audit trail. | A per-employee **compensation timeline** (effective date, amount, currency, FTE, pay basis, level/step, actor, reason, source), gated `compensation:r` and row-scoped; joined to the `audit_log` rows by **`correlation_id`** so the two read as one story; `audit_log` diffs carry **no amounts** — only BR-9.2's permitted keys; the new `ACTIONS` codes registered; **`_MONEYISH_KEYS` enforced with a test that proves an amount is refused**; the timeline is a **compensation** surface, not an `audit_log` surface, and holding `audit_log:r` alone never reveals an amount. | Should Have · P2 |

### 19.2 The timeline

- **AC-202-01** A per-employee **compensation timeline**, newest first, showing per entry: `effective_from`, amount,
  currency, FTE, pay basis, derived `annualised_base` and `fte_normalised_annual`, level and step in force, the
  actor, the reason, the source (manual / import run / request id) and the state (in effect / superseded / future /
  voided / purged).
- **AC-202-02** The timeline reads as a **continuous history**: each entry shows the period it was in effect
  (§4.3), and the reader can answer "what was this person paid on 4 March 2025" without arithmetic.
- **AC-202-03** Each entry links to the `audit_log` rows produced by the same unit of work, joined by
  **`correlation_id`** (`audit_service.company_timeline(..., correlation_id=…)`,
  `app/services/audit_service.py:356-388`), so the *what* and the *why* read as one story rather than as two
  systems.
- **AC-202-04** Where an entry came from an approved request, it links to that request and its approval chain, so
  the trail runs amount → decision → approvers → reason.
- **AC-202-05** Voided entries are shown as voided with the voiding actor, timestamp and reason (AC-193-08).
  Purged entries show *"Amount destroyed at retention expiry on <date>"* (AC-193-46, BR-7.27).
- **AC-202-06** Entries from a **prior employment period** are shown, grouped and labelled with that period
  (BR-7.26, AC-193-24).
- **AC-202-07** A **level and step timeline** is shown alongside, sharing the same date axis, so a reader can see
  that a pay change accompanied a promotion.

### 19.3 The audit coupling

- **AC-202-08** **`audit_log` diffs for compensation events carry no amounts** — only BR-9.2's permitted keys:
  `has_change`, `direction`, `pct_change_band`, `currency`, `effective_date`, `pay_basis`, `fte_from`/`fte_to`,
  `level_from`/`level_to`, `step_from`/`step_to`, `level_direction`. `entity_id` is the **compensation record id**.
- **AC-202-09** `pct_change_band` uses BR-9.3's exact buckets — `INITIAL` · `0` · `0-5` · `5-10` · `10-20` · `20+`,
  left-closed / right-open — and `INITIAL` is used where there is no prior record, so a first record never reads as
  a 20%+ rise.
- **AC-202-10** **`_MONEYISH_KEYS` is enforced with a test that proves an amount is refused**, not merely absent: a
  deliberate attempt to write `{'salary': 60000}` into a diff or into `metadata` raises `AuditError` and writes no
  row (BR-9.5, AC-194-26).
- **AC-202-11** The permitted key set is asserted positively too — each of BR-9.2's keys is accepted — so the guard
  cannot be over-tightened into blocking legitimate audit rows (AC-199-13's band keys included).
- **AC-202-12** All of BR-9.6's new `ACTIONS` codes are registered in `audit_service.ACTIONS`, **including the two
  EP38 already requires and does not have** — `EMPLOYEE_ANONYMISED` and `ERASURE_REFUSED` — and the new
  `ERASURE_PARTIALLY_REFUSED` (B42-15, BR-7.8). *(The enumeration is deliberately frozen and extending it is the
  Architect's edit — CFL-42-2, SPM S8.)*
- **AC-202-13** Compensation audit rows carry `retention_class = 'EMPLOYMENT'`; tenant-feature toggles `STANDARD`;
  self-approval records `SECURITY` (BR-9.7).
- **AC-202-14** **Holding `audit_log:r` alone never reveals an amount.** Asserted directly: a user with
  `audit_log:r` and **no** `compensation:r` reads the full compensation audit trail for an employee and no amount,
  no ratio and no band figure appears in any row, any diff, any `metadata` or any `reason`. **This is the criterion
  that justifies the whole D5.6 split** and it must be a named test.
- **AC-202-15** Conversely, a `compensation:r` holder **without** `audit_log:r` sees the timeline with amounts and
  reasons, and sees no `audit_log` rows. The two features are separate audiences by design.

### 19.4 Edge, error and failure behaviour

- **AC-202-16** An employee with **no** compensation history shows an explicit empty state — *"No compensation
  history recorded"* — never a blank panel and never a zero row (CC-42-19).
- **AC-202-17** An employee whose entire history has been **purged** shows the timeline shape with every amount
  replaced by the purge statement (AC-202-05), not an empty timeline — the fact that pay existed is itself part of
  the record.
- **AC-202-18** The timeline paginates and does not degrade for an employee with many entries; a bulk import that
  loaded ten years of history renders without a per-row query per entry.
- **AC-202-19** A timeline request for an out-of-scope employee returns `403` with nothing read back — a manager
  requesting a skip-level report's timeline, an employee requesting a colleague's (BR-8.3).
- **AC-202-20** A timeline request for an employee in another company returns `403`, reads nothing back and writes
  nothing.
- **AC-202-21** No amount appears in any log line or error message produced by this surface (CC-42-21).

### 19.5 Permissions and tenant isolation

- **AC-202-22** The timeline is `@require_feature_access('compensation', 'r')` and is **row-scoped** by §4.8.1:
  `SELF` for an employee (their own, and only if `compensation_self` is enabled), `DIRECT` for a solid-line manager,
  `COMPANY` for HR_ADMIN and PORTAL_ADMIN.
- **AC-202-23** **The timeline is a `compensation` surface, not an `audit_log` surface.** It is gated by
  `compensation`, it appears in the compensation navigation, and it does not appear to a holder of `audit_log:r`
  alone (AC-202-14).
- **AC-202-24** All queries are company-scoped (CC-42-11); a SYSTEM_ADMIN with "All Companies" selected sees a
  "select a company" state (CC-42-12).

### 19.6 Dependency on the audit read surface

- **AC-202-25** KAN-202 **does not block** on the SPM's unresolved audit read-surface decision (backlog open item
  #1, DEP-8): the compensation timeline is its own surface with its own feature code. But the two must not be
  designed in ignorance of each other — if the audit read surface later offers a per-employee timeline, the two must
  not present contradictory histories of the same events, and the `correlation_id` join is what keeps them
  consistent.

### 19.7 Out of scope (KAN-202)

The general `audit_log` read surface (backlog open item #1, SPM Wave 3) · a company-wide compensation change report ·
compensation analytics, trend charts or cost-of-workforce reporting (§3.3) · exporting the timeline to a
regulator-shaped format · a "who viewed this timeline" access log (OQ-BA-5) · restoring a voided or purged record ·
diffing two employees' timelines.

---

## 20. Conflict log and defects

### 20.1 Conflicts carried forward from the SPM (§7.3) with the BA's position

*Never resolved silently (Charter §9.3). Numbered `CFL-42-n`, continuing the SPM's sequence.*

| ID | Conflict | Severity | Evidence | Status / resolution required from |
|---|---|---|---|---|
| **CFL-42-1** | The documented access model is `role_feature_access` AND `company_role_feature_access`; `company_features.is_enabled` is a **third**, undocumented mechanism the central resolver does not consult. R7 requires it to work. | **High** | `app/auth.py:38-95` vs `app/routes/analytics.py:20-40`, `app/routes/skills_intelligence.py:15-30` | **Senior Architect** — ADR + KAN-188. **Open.** BA criteria written against the behaviour (AC-188-01…07), not the mechanism. **Gates W1.** |
| **CFL-42-2** | `audit_service.ACTIONS` is a deliberately frozen closed enumeration and `_check_no_secrets` has no money guard, so a salary diff would be written verbatim today. | **High** | `app/services/audit_service.py:73-90, 95-98, 153-159` | **Senior Architect** — his file. **Open.** BA extends the ask: the enumeration must also gain `EMPLOYEE_ANONYMISED` and `ERASURE_REFUSED`, **which EP38 already requires and which are absent** (B42-15), plus `ERASURE_PARTIALLY_REFUSED` (BR-7.8). Sign-off before KAN-193. |
| **CFL-42-3** | **EP38's erasure enumeration predates compensation.** R3.6/R3.7 list every table in the product and do not mention pay. Left alone, erasure destroys legally-required pay history or retains identifying pay data. | **High** (compliance) | EP38 §4.3 R3.6/R3.7 | **BA — RESOLVED in §4.7 of this document.** Lawful basis §4.7.2; gender purpose-limitation §4.7.3; retention class per entity §4.7.4; what erasure does §4.7.5; DSAR §4.7.6; offboarding/rehire §4.7.8. **Seven items remain open with the DPO (DPO-1…DPO-7)** and are listed in §4.7.9. The amendment to EP38's own file lands in the KAN-193/194 commit (Charter §5b rule 1). |
| **CFL-42-4** | **Two job titles, unclear precedence.** `employees.job_title` is indexed and feeds the search trigger; EP42 makes the level title canonical. | **Medium** | `database/schema.sql:411, 1588, 1861` | **BA + Architect.** BA position: **BR-5.11's precedence table**, adopting the SPM's steer. **Extended:** this is not only a display question — **level titles are not searchable** because the index is trigger-written over four `employees` columns and no application code writes it (B42-14). AC-191-10 makes searchability a requirement; the mechanism is the Architect's. |
| **CFL-42-5** | Segregation of duties is unresolved, and EP42's position changes `decide()` for EP27 and EP38 as well. | **High** | `app/services/org_change_service.py:222-262`; backlog open item #5 | **Architect** (shared engine) + **owner ratification (OQ-9)**. **Open.** BA criteria in §15, with two additions the SPM's D4h did not cover — CFL-42-11 and CFL-42-15. |
| **CFL-42-6** | The shared brief's tenancy baseline is wrong. | **Medium** | SPM S1 | **Resolved by the SPM.** BA re-verified independently (B42-20) and uses S1. |
| **CFL-42-7** | The roadmap has no compensation epic and no BG7; the two business documents have no compensation feature and no pay retention rule. | **Medium** | Roadmap §C/§D; `docs/BUSINESS_DOCUMENTATION.md`; `docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` | **SPM** amends roadmap + `BACKLOG.md` in Wave 3. **BA** amends the two business documents **in the same commit as the implementation**, not now — this task is documentation-only and single-file. **Note the pre-existing falsehood:** `docs/BUSINESS_DOCUMENTATION.md:242-243` still states employee records are *"retained regardless of `employment_status`"* and vacation requests *"permanently retained"* — indefinite retention, contradicting GDPR storage limitation and now also §4.7 (this is EP38 **CFL-3**, still open). |

### 20.2 New conflicts found by the BA

| ID | Conflict | Severity | Evidence | Resolution required from |
|---|---|---|---|---|
| **CFL-42-8** | **`@require_feature_access` denies with a 302 redirect, for JSON endpoints as well as pages.** Every "returns `403`" criterion in this document — and in EP38's — describes behaviour the decorator does not have. A `fetch()` receiving a 302 to an HTML dashboard is the DEF-002 shape. | **High** | `app/auth.py:102-115`; contrast the hand-written 403s at `app/routes/org_change.py:197,200,222,232,327` | **Senior Architect.** A JSON-aware denial (or an API variant of the decorator) is needed before the first compensation API. Named in AC-188-09, AC-194-09, BR-8.5. |
| **CFL-42-9** | **`_apply_change` closes `manager_relationships` without an `effective_to`.** The pattern EP42 is told to copy for effective dating is itself undated on the closing side, and the dev DB holds 2 such rows. | **Medium** (data quality; **High** if copied) | `app/services/org_change_service.py:381-385` vs `:370-374`; `psql` → 2 rows `is_current=FALSE AND effective_to IS NULL` | **Architect**, inside KAN-189 (AC-189-05). Fixing it in the same change is cheap; copying it into three new tables is not. |
| **CFL-42-10** | **One shared effective date, two different scheduler dependencies.** D4d makes placement and pay share one date; EP38 R5.6 forbids a future-dated *placement* (no scheduler); a future-dated *compensation record* is safe and useful. The shared date therefore cannot be uniformly future-datable. | **Medium** | SPM D4d vs EP38 R5.6; SPM S16 | **BA position: BR-3.6a** — `TRANSFER`/`PROMOTION` may not be future-dated; a pay-only `COMPENSATION_REVIEW` may (AC-189-11, AC-189-12). **SPM to ratify.** |
| **CFL-42-11** | **D4h's four-eyes control is a no-op in a default-configured tenant.** `_DEFAULT_STEPS` is a **single** `HR_ADMIN` level, applied whenever a company has not configured a chain — which is every tenant today. On a one-level chain there is no second level to refuse. | **High** | `app/services/org_change_service.py:23-26, 32-45` | **BA position: AC-198-08** (money-bearing requests require ≥2 independently-satisfiable levels, refused at create time) **plus AC-198-11** (a seeded two-level default chain for `PROMOTION` and `COMPENSATION_REVIEW`). **SPM to ratify (OQ-BA-10); Architect to sign off (CFL-42-5).** |
| **CFL-42-12** | **The create-time approver-eligibility check D4b requires cannot be written today.** `_load_feature_access()` resolves the **session user's** access only; nothing answers *"does user X hold feature F in company C"*. | **High** | `app/auth.py:38-95` | **Senior Architect** — a non-session feature-access resolver. Blocks AC-196-10 / AC-196-11. |
| **CFL-42-13** | **A manager without `compensation:r` can route around the mandatory pay decision.** D4c and the W3 gate say no position change is applied with the pay question unanswered; D4f says a user without `compensation:r` raises a placement-only `TRANSFER`. Read together, R3's control is optional for exactly the population that raises most moves. | **High** | SPM D4c / D4f / W3 gate | **BA position: AC-196-16** — the request records `NOT_ANSWERED_NO_PERMISSION` and the **first `compensation:r` approver must answer before approving**. Satisfies both rules and gives the manager no pay visibility. **SPM to ratify.** |
| **CFL-42-14** | **`CLAUDE.md` org-change invariant 2 does not hold for admins.** `_can_initiate_for` returns `True` for any HR_ADMIN/PORTAL_ADMIN/SYSTEM_ADMIN **regardless of subject**; the only self-check is a display helper. Today: a self-requested desk move. After EP42: **a self-requested pay rise.** | **Critical** | `app/routes/org_change.py:55-62, 199`; `app/routes/employees.py:126-131` (display only, and says so) | **Architect + SPM.** BA criteria AC-196-34, AC-197-17, AC-192-28, AC-192-29. This is a pre-existing invariant violation, not an EP42 regression — but EP42 is what makes it material. |
| **CFL-42-15** | **The subject of a request can approve it.** `decide()` checks company and role-vs-step; nothing compares the decider to `req['employee_id']`. Combined with CFL-42-14, **one HR_ADMIN can raise and approve their own pay rise end-to-end on the default chain**. | **Critical** | `app/services/org_change_service.py:101-105, 222-262` | **Architect + SPM.** BA criteria AC-197-20, AC-198-04. Belongs in KAN-198. |
| **CFL-42-16** | **"Copy the `manager_relationships` pattern" produces the wrong answer for compensation.** A stored `is_current` flag on a future-dated record would need a scheduler to flip it, and there is none. | **Medium** | SPM D4d's steer; SPM S16 | **BA position: BR-3.2 / AC-193-13** — "current" is **computed**, never stored, for compensation and level assignments. **Architect to confirm** in the data-model ADR. |
| **CFL-42-17** | **Two coverage numbers with different denominators.** D7 specifies "coverage"; the group key requires a level, so pay coverage and level coverage cannot share a denominator. An unlabelled "62%" is ambiguous and will be quoted at a customer. | **Medium** | SPM D7.5 vs D1's group key | **BA position: BR-4.3 / AC-195-16** — two named figures, each naming its denominator. **SPM to note**, since D7.5's example string is now insufficient. |

### 20.3 Defects found while writing these criteria

*Pre-existing, not caused by EP42, but material to it. Raised for the SPM and the Delivery Manager to route; the BA
does not own the defect log.*

| ID | Defect | Severity | Evidence | Why it matters to EP42 |
|---|---|---|---|---|
| **DEF-42-1** | **The CSV employee importer cannot write a valid `employment_type`, and fails silently when it tries.** `EMPLOYMENT_TYPES` contains `FULL_TIME` (which the DB CHECK rejects) and omits `PERMANENT` (which it requires); a blank cell defaults to `'FULL_TIME'`; the resulting CHECK violation is caught and the row is marked `SKIPPED` with **no reason surfaced to the user**. | **High** | `app/services/import_service.py:16, 63-67, 152, 161-165` vs `database/schema.sql:421-422` | D1 keys its exclusions (`CONTRACTOR`, `INTERN`) and its FTE handling (`PART_TIME`) on `employment_type`. Bulk import is the only bulk path and cannot set it. KAN-195 reuses this surface and **must not inherit the silent-skip pattern** (AC-195-10). |
| **DEF-42-2** | **`manager_relationships` rows are closed without an `effective_to`** — 2 in the dev database. | **Medium** | `app/services/org_change_service.py:381-385`; `psql` | Point-in-time org history is already lossy; EP42 depends on this table for the `DIRECT` scope and for pay-market/manager context. Fixed inside KAN-189 (AC-189-05). Same root as CFL-42-9. |
| **DEF-42-3** | **`employees.gender` is NULL for 100% of the population** and has no admin-facing collection path beyond registration and CSV — it is otherwise self-service only. | **Medium** (data) | `psql`; `app/routes/employees.py:176-186` | Check B has no data to run on and would report "insufficient gender representation" for every group on every seeded tenant. UAT fixtures must supply it (SPM §8.4.4); a demo of Check B on seed data would show nothing. |

---

## 21. Traceability matrix

### 21.1 Forward — owner's ask → decision → story → acceptance criteria

| Ask (brief §1) | SPM decision(s) | Story | Acceptance criteria | Contingent on |
|---|---|---|---|---|
| **R1** — hold salary data at all | **D5** (visibility), D4d (dating), D5.6 (audit) | **KAN-193** | AC-193-01 … AC-193-48 (the record, dating, void, rehire, validation, retention) | OQ-5 (total comp shape) |
| **R1** | D5 | **KAN-194** | AC-194-01 … AC-194-44 (registration, matrix, scoping, My Pay, negative visibility) | **OQ-2** (three matrix cells — seed data only) |
| **R1** | D5.6 | **KAN-202** | AC-202-01 … AC-202-25 (timeline, audit coupling, `_MONEYISH_KEYS`, `audit_log:r` reveals nothing) | DEP-8 (audit read surface) |
| **R2** — assign salary to existing employees | **D7** | **KAN-195** | AC-195-01 … AC-195-35 (import, manual, coverage, staging retention) | DEP-6 (EP35-S2), OQ-BA-7 (column name) |
| **R2** (the level half) | D7.1, D3 | **KAN-191** | AC-191-01 … AC-191-30 (assignment, mapping screen, CSV round-trip, coverage, title precedence) | **CFL-42-4** |
| **R3** — position change considers a salary update | **D4a–d, D4f, D4g** | **KAN-196** | AC-196-01 … AC-196-37 (mandatory answer, approver eligibility, five overlay shapes, shared date) | **CFL-42-12, CFL-42-13** |
| **R3** (the enabler) | D4d | **KAN-189** | AC-189-01 … AC-189-24 (effective date, non-overlap, manager close, windows) | **CFL-4** (interval convention), **CFL-42-10** |
| **R4** — promotion triggers a salary review | **D4e, D3.4** | **KAN-197** | AC-197-01 … AC-197-35 (request type, chains per type, direction, initiator rule) | — |
| **R4** (the progression half) | **D3.4** | **KAN-192** | AC-192-01 … AC-192-32 (step advancement, the signal, the bell checklist, no roll-up) | **OQ-1** — the whole section |
| **R3 / R4** (control on the approval that carries them) | **D4h** | **KAN-198** | AC-198-01 … AC-198-31 (four-eyes, ≥2 satisfiable levels, subject rule, overlap at config time) | **OQ-9**, **CFL-42-5**, **CFL-42-11** |
| **R5** — flag a >5% difference to the HR responsible | **D1**, D7 | **KAN-200** | AC-200-01 … AC-200-58 (grouping, coverage, Check A, Check B, config, cadence, framing) | **OQ-3**, **OQ-6**, **DPO-1** (Check B only), DEP-4 |
| **R5** (the basis) | D3.5, D1 | **KAN-199** | AC-199-01 … AC-199-31 (pay markets, bands, out-of-band, FX refusal) | **OQ-6** |
| **R5** (the delivery) | **D2** | **KAN-201** | AC-201-01 … AC-201-46 (recipients, queue, bell checklist, lifecycle, anti-fatigue) | — |
| **R6** — job levels with steps, per company, each with its own title | **D3** | **KAN-190** | AC-190-01 … AC-190-30 (families, levels, steps, validity, archive, empty state) | **OQ-4** (example ladder — seed data), **OQ-BA-2** (mid-insertion) |
| **R6** | D3 | **KAN-191**, **KAN-192** | as above | **OQ-1** for KAN-192 |
| **R7** — expose/hide per company | **D6** | **KAN-188** | AC-188-01 … AC-188-26 (central AND, no-regression matrix, off state, retro-fit, audit) | **CFL-42-1**, **OQ-7** |

### 21.2 Reverse — every story traces to an ask; no orphans

| Story | Ask | Also serves |
|---|---|---|
| KAN-188 | **R7** | Every other EP42 story (gates them all) |
| KAN-189 | **R3** (enabler) | Repays **CFL-4** / unblocks `AC-185-07` on KAN-185 |
| KAN-190 | **R6** | Supplies the grouping key R5 needs |
| KAN-191 | **R6**, **R2** | Same |
| KAN-192 | **R6** | R4 (the signal that starts a promotion) |
| KAN-193 | **R1** | R2, R3, R4, R5 all depend on it |
| KAN-194 | **R1** | The precondition for rendering anything from R1–R5 |
| KAN-195 | **R2** | Coverage gate for R5 |
| KAN-196 | **R3** | — |
| KAN-197 | **R4** | Closes backlog open items #3 and #4, EP38 OQ-1, EP38 CFL-7 |
| KAN-198 | **R3 / R4** (control on the approval) | Closes backlog open item #5 |
| KAN-199 | **R5** (the basis) | R1 (position in range on My Pay) |
| KAN-200 | **R5** | — |
| KAN-201 | **R5** (delivery) | — |
| KAN-202 | **R1** (the history half) | R5 (defensibility of a flag's disposition) |

**No orphan stories. No unallocated asks.** R5 is delivered with a **deliberate reinterpretation** — split into an
individual-outlier check and a group gender-gap check (D1.2) — which the owner should be told explicitly (**OQ-3**),
and Check B additionally carries a lawful-basis gate the SPM did not specify (**BR-7.2 / DPO-1**).

### 21.3 Decisions D1–D8 as inputs — where each is enforced

| Decision | Enforced by |
|---|---|
| **D1** — comparison group, basis, two checks | §4.4 in full; AC-200-01…AC-200-37; AC-199-08…AC-199-21 |
| **D2** — who the HR responsible is, and how a flag reaches them | AC-201-01…AC-201-32; the bell checklist AC-201-11…AC-201-21 |
| **D3** — the job-level model, no automatic roll-up | §4.5; AC-190-*, AC-191-*, AC-192-* |
| **D4** — coupling to position change and promotion | §4.3; AC-189-*, AC-196-*, AC-197-*, AC-198-* |
| **D5** — who may see a salary | §4.8, §4.9; AC-194-* in full; AC-202-14 |
| **D6** — the tenant switch, centrally | AC-188-01…AC-188-26 |
| **D7** — backfill and partial-data behaviour | §4.6; AC-195-*; AC-200-09…AC-200-13 |
| **D8** — T2/T5 and the demo safeguards | CC-42-8, CC-42-24, AC-194-04, AC-194-43, AC-194-44 |

### 21.4 Criteria contingent on an unanswered question

| OQ | Contingent criteria | If the answer differs |
|---|---|---|
| **OQ-1** — the roll-up | **AC-192-06 … AC-192-14**, and by extension AC-197-04 | An automatic roll-up needs a rules engine and a trigger that do not exist (SPM S16). KAN-192 is redesigned, not adjusted. **This is the one story genuinely gated on the owner.** |
| **OQ-2** — three matrix cells | AC-194-06 (three rows of the matrix), AC-194-10, AC-194-12 | **Seed data only.** One `seed_rbac.sql` edit; no code change. |
| **OQ-3** — what "5%" means | AC-200-24 … AC-200-32 (all of Check B) | Dropping Check B after KAN-200 is easy; adding it later reopens the engine and the grouping. |
| **OQ-4** — the example ladder | Nothing in code. Documentation and any worked example only | **Seed data only.** |
| **OQ-5** — total compensation | **AC-193-01** (the record's shape) and AC-200-49 | **High cost if late.** Retrofitting variable pay into a base-only record and a base-only comparison is a rewrite of KAN-193 and KAN-200. |
| **OQ-6** — currency per pay market | AC-199-18 … AC-199-21, AC-200-37 | An FX table added later is additive; an engine written assuming single currency and then made multi-currency is not. |
| **OQ-7** — default exposure | CC-42-8, AC-194-04, AC-188-26 | **One seed value.** |
| **OQ-8** — works councils | Nothing in the build. Customer-Readiness only | **Launch blocker, not a build blocker.** |
| **OQ-9** — segregation of duties | **AC-198-01 … AC-198-31** | It is a guard in `decide()` either way; the question is which requests it binds. |
| **DPO-1** — gender purpose limitation | **AC-200-24 … AC-200-32**, BR-7.1 … BR-7.5 | Check B cannot ship. Check A, the queue and the lifecycle are unaffected. |
| **DPO-2** — pay history survives erasure | **AC-193-48**, §4.7.5 | Reverses the erasure rule; §4.7.4's purge becomes the only control or the amounts go at erasure. |

---

## 22. Dependencies

| ID | Dependency | Needed by | Status | Note |
|---|---|---|---|---|
| **DEP-1** | **KAN-155** — `transaction()` atomic writes | KAN-189, 193, 195, 196, 197, 198, 201 | Planned, S2 enabler | **Hard prerequisite.** A promotion writes the assignment, the level/step, the compensation record and several audit rows. A half-applied promotion is the worst state in this epic (AC-197-06). |
| **DEP-2** | **KAN-166** — versioned migrations | KAN-188, 189, 190, 193, 199, 200, 201 | Planned, S2 enabler | Five new table sets and three feature codes. The `org_change_*` drift is exactly what this exists to stop. |
| **DEP-3** | **KAN-187** — audit trail | Every mutating story | ✅ **Done** | Reused, not re-invented. Needs `ACTIONS` extended and `_MONEYISH_KEYS` added — **CFL-42-2**, and it must also gain the two codes **EP38 already needs and does not have** (B42-15). |
| **DEP-4** | **KAN-168** — real-DB integration tier | **KAN-200 above all**; also AC-189-04, AC-193-12, AC-196-19 | Planned, S2 enabler | Group formation, medians, coverage gates and the five overlay shapes cannot be verified against mocks (AC-200-53). |
| **DEP-5** | **KAN-185** — transfer flow | Not a dependency — **the reverse** | 🟡 In progress, blocked | **KAN-189 unblocks `AC-185-07`.** EP42 repays EP38 (AC-189-06). |
| **DEP-6** | **EP35-S2** — bulk import wizard | KAN-195 (soft) | Planned, S3 | AC-195-35 makes the refactor-onto-the-wizard obligation an acceptance criterion rather than an intention (SPM R-9). |
| **DEP-7** | **KAN-163** — any scheduler | Periodic equity re-evaluation; automatic retention purge; time-based progression; future-dated placement | **Not planned** | Why evaluation is event-driven + on-demand (AC-200-42), why the purge is manual-Must / automatic-Should (AC-193-47), why there is no roll-up (AC-192-06) and why a future-dated placement is refused (AC-189-11). **Do not design around a scheduler that does not exist.** |
| **DEP-8** | **Backlog open item #1** — the audit read-surface decision | KAN-202 | **Unresolved — SPM, Wave 3** | KAN-202 does not block on it (AC-202-25), but the two must not present contradictory histories. |
| **DEP-9** | **DPO / legal validation** — the seven items in §4.7.9 | Check B (KAN-200); the retention class (KAN-193); the launch | **Not started** | **DPO-1 blocks Check B, not KAN-200.** DPO-2 blocks the retention class. The rest are launch, not build. Charter §9.7. |
| **DEP-10** | **A non-session feature-access resolver** (CFL-42-12) | **AC-196-10, AC-196-11** | **Does not exist** | D4b's create-time approver-eligibility check cannot be written without it. Architect. |
| **DEP-11** | **A JSON-aware feature-access denial** (CFL-42-8) | Every EP42 API criterion that says `403` | **Does not exist** | `@require_feature_access` 302-redirects today. Architect, before the first compensation API. |
| **DEP-12** | **EP28 / KAN-148 real authentication** | Nothing in the build — but everything in the *enforceability* of §4.8 | Deferred to S5 by D-004 | AC-194-43 is the honest statement of the consequence, and it is a Demo Readiness Gate item, not a build blocker. |

---

## 23. Open questions and Definition of Ready

### 23.1 The SPM's OQ-1 … OQ-9

Not restated — they are in SPM §6 with recommended defaults, and **every criterion in this document is written
against those defaults**. §21.4 maps each to the criteria it would change. The BA adds nothing to them except:
**OQ-3 should be put to the owner together with DPO-1**, because "does he want the gender-gap check" and "may we
lawfully compute it from the data we have" are one conversation, not two.

### 23.2 New open questions raised by the BA

| ID | Question | Owner | Recommended default *(build against this now)* | Blocks | Cost if late |
|---|---|---|---|---|---|
| **OQ-BA-1** | Should the `n >= 3` minimum and the coverage gate apply when the basis is a **band midpoint**? A band is company policy, not a colleague, so a group of one can be compared to it without disclosing anybody's pay — and given Acme's 41-titles-over-46-people reality, most groups will be small. | **SPM** | **Apply both, as D1 states.** Recommend revisiting after the first tenant: exempting the band basis would materially widen coverage without widening disclosure. | KAN-200 scope | **Low** — it is a condition in the engine either way. |
| **OQ-BA-2** | **Inserting a level between two existing ones** has no path once assignments exist (BR-5.4/AC-190-10). A company that discovers it needs a level between 2 and 3 must create a new family and re-map. Acceptable? | **SPM** | **Accept for this cycle** and state the limitation in the configurator. | KAN-190 | **Medium** — allowing it later means renumbering, which changes every historical group key. |
| **OQ-BA-3** | **`monthly_payments_per_year`** — should it sit on the company or on the **pay market**? Acme's Porto office (Portugal, 14 payments) sits alongside Hamburg and Tallinn (12) **in the same company**. | **SPM + Architect** | **Per company for this cycle** (BR-2.2), with the field designed so it can move to the pay market without a change of meaning. | KAN-193, KAN-200 arithmetic | **Medium.** A company-level constant is wrong for Acme the day Porto has a monthly-paid employee. |
| **OQ-BA-4** | Should the **subject** receive the `promotion_eligible` signal? | **SPM** (product policy) | **No** (AC-192-11). Telling someone the system considers them promotion-eligible before any human has decided is the implied promise D3.4 warns about. | KAN-192 | **Low** — a recipient list. |
| **OQ-BA-5** | Should there be a **"who viewed this salary" access log**? The audit trail records writes, not reads. | **SPM + DPO** | **Not in this cycle.** Named rather than omitted; it is a reasonable expectation for pay data and a common audit requirement. | Nothing today | **Medium** — read logging is cheap to add early and awkward to retrofit across a dozen endpoints. |
| **OQ-BA-6** | Does any target jurisdiction require **pay records to be retained longer than the employee record itself**? BR-7.6 uses one clock. | **DPO**, via SPM | **One clock** (EP38's per-company period, default 7 years). | The retention model in KAN-193 | **Medium** — a second clock changes the retention model from per-employee to per-class. |
| **OQ-BA-7** | The SPM's CSV column is named **`annual_base`** but carries the amount **in the stated `pay_basis`**. Rename to `amount`? | **SPM** | **Rename to `amount`**, with `annual_base` accepted as an alias. A column called `annual_base` holding a monthly figure will produce a first import wrong by a factor of twelve. | KAN-195 | **Very low** now; **High** after the first customer import. |
| **OQ-BA-8** | Should an approver of a money-bearing request see the **band position and comparison context** at decision time? | **SPM + UX** | **Not in this cycle** (AC-196 out-of-scope). Genuinely useful; the band exists only after KAN-199 and UX has not been asked. | Nothing | **Low.** |
| **OQ-BA-9** | Should the **initiator** of a money-bearing request be barred from deciding it (initiator ≠ approver)? | **SPM** (governance policy) | **Yes** (AC-198-05). Without it, an HR_ADMIN raises a colleague's pay rise and approves it — one person, two hats. | KAN-198 | **Low** — a guard either way; the question is scope. |
| **OQ-BA-10** | Confirm the **seeded default chain for `PROMOTION` and `COMPENSATION_REVIEW`** as two `ROLE` levels (HR_ADMIN → PORTAL_ADMIN). | **SPM** | **Confirm** (AC-198-11). Without it every tenant hits AC-198-08 on their first pay change, because the current default chain is a single HR_ADMIN level. | KAN-198 seed data | **Low** — one seed value, but it is the difference between the control working and the feature not working. |
| **OQ-BA-11** | **DEF-42-1** (the employee importer cannot write a valid `employment_type` and fails silently) — is it fixed inside EP42 or raised as an independent defect? | **SPM + Delivery** | **Independent defect**, fixed before KAN-195 starts. EP42 depends on `employment_type` being correct but should not absorb an unrelated fix. | KAN-195 quality, KAN-200 exclusions | **Medium** — if unfixed, part-time and contractor paths are untestable through the only bulk path. |

### 23.3 Definition of Ready — verdict per story

Assessed against Charter §4: problem understood · persona identified · business value defined · **requirements and
acceptance criteria documented** · UX understood · dependencies identified · data requirements known ·
security/privacy considered · technical feasibility assessed · test approach understood.

| Story | DoR after Wave 2 (BA) | What is still missing |
|---|---|---|
| **KAN-188** | **NOT READY** | Architect ADR (**CFL-42-1**) and the JSON-denial decision (**CFL-42-8**, DEP-11). Criteria complete. UX needed only for the off-state screen, which has a precedent. **Closest to Ready in the epic.** |
| **KAN-189** | **NOT READY** | Architect's interval convention (**CFL-4**) and the manager-close fix (**CFL-42-9**). SPM ratification of **CFL-42-10**. Criteria complete. |
| **KAN-190** | **NOT READY** | UX — the configurator is the hardest screen in the epic and its empty state matters more than its populated one. **OQ-BA-2**. Criteria complete. |
| **KAN-191** | **NOT READY** | UX — the mapping screen decides whether the backfill finishes (SPM R-2). **CFL-42-4** including the searchability half (AC-191-10). Criteria complete. |
| **KAN-192** | **NOT READY** | **OQ-1** — the only story genuinely gated on a product-owner answer. Also **OQ-BA-4** and UX's one sentence. Criteria complete **against the default**. |
| **KAN-193** | **NOT READY** | Architect's data-model ADR including **CFL-42-16**; **CFL-42-2**; **DPO-2** for the retention class; **OQ-5** for the record's shape. Criteria complete. |
| **KAN-194** | **NOT READY** | **UAT's negative-visibility approach must be agreed before it is built, not after** (SPM DoR note — and §4.8.4's thirteen surfaces are the input). **CFL-42-8** / DEP-11. **OQ-2** for seed data. Criteria complete. |
| **KAN-195** | **NOT READY** | UX; **DEP-6** sequencing; **OQ-BA-7**; **DEF-42-1** resolved (OQ-BA-11). Criteria complete. |
| **KAN-196** | **NOT READY** | **CFL-42-12 / DEP-10** — D4b's check cannot be written today. **CFL-42-13** needs the SPM. **CFL-42-14** needs the Architect. UX must prove the modal-weight constraint (AC-196-25). Criteria complete. |
| **KAN-197** | **NOT READY** | **CFL-42-14**, **CFL-42-15**. DEP-1. Criteria complete. |
| **KAN-198** | **NOT READY** | **OQ-9** ratification, **CFL-42-5** sign-off, **CFL-42-11** + **OQ-BA-10**, **OQ-BA-9**. This story now carries more unresolved governance than any other. Criteria complete. |
| **KAN-199** | **NOT READY** | **OQ-6**; UX for the band editor; **AC-199-13**'s band-key exception needs Architect confirmation under CFL-42-2. Criteria complete. |
| **KAN-200** | **NOT READY** | **OQ-3**, **OQ-BA-1**, **OQ-BA-3**, **DPO-1** (Check B only), **DEP-4** (KAN-168), and **UAT's hand-computed fixtures written by someone other than the engine's author** (SPM R-12). Criteria and arithmetic complete — §4.4's worked examples are the fixture specification. |
| **KAN-201** | **NOT READY** | UX for the queue, the disposition flow and D4's four-actor bell walk. Criteria complete. |
| **KAN-202** | **NOT READY** | **DEP-8** (audit read surface — does not block, but should not be designed in ignorance); **CFL-42-2**. Criteria complete. |

**Nothing in EP42 is Ready, and nothing should be — this is Wave 2 of three and S1 has not closed.** What has
changed since Wave 1 is *what* is missing: **acceptance criteria are no longer the gap on any story.** Every
remaining blocker is an Architect decision, a UX design, an owner ratification or a DPO answer. The three that would
unblock the most, in order: **CFL-42-1** (gates W1 and therefore everything), **CFL-42-12/DEP-10** (gates KAN-196's
central control), and **OQ-1** (gates KAN-192 entirely).

---

## 24. Assumption and unknown register — BA additions

The SPM's §9 register is adopted in full and not restated. These are new.

| Item | Type | Impact if wrong | Validation needed | Owner |
|---|---|---|---|---|
| Retaining pay history past exit is **required** by tax/employment law in the seed jurisdictions, so it belongs on the survive-erasure list | **Needs Validation** | Getting it backwards is a GDPR finding in one direction or a legal-retention failure in the other. §4.7.5 is built on it | **DPO-2**, per jurisdiction | BA / DPO |
| `employees.gender`, collected for vacation eligibility, may lawfully be reused to compute a pay gap | **Needs Validation** (this is a **purpose-limitation** question, not a permissions one) | Check B cannot ship, or ships on a basis the DPO rejects. BR-7.2's acknowledgement gate is the mitigation, not the answer | **DPO-1** | BA / DPO |
| Destroying the amount at retention expiry while keeping the timeline shape (§4.7.4) is an acceptable storage-limitation control | **Assumption** (Medium) | If the DPO requires full deletion, historical headcount and level reporting for prior periods loses its spine | **DPO-3** | BA / DPO |
| A disclosure floor of **5 compared employees** for any group statistic in a DSAR response (BR-7.13) is sufficient | **Assumption** (Medium) | Too low re-identifies a colleague's pay; too high makes the Art. 15(1)(h) explanation useless | **DPO-6** | BA / DPO |
| **`monthly_payments_per_year` belongs on the company, not the pay market** | **Assumption** (Low confidence — Acme spans Portugal and Germany in one company) | Every Portuguese monthly-paid employee is understated by ~17%, which is 3× the gap threshold — a manufactured finding | **OQ-BA-3**; validate against Acme's actual payroll conventions | BA / SPM |
| `standard_annual_hours = 1800` is a reasonable default for hourly annualisation | **Assumption** (Low) | Hourly employees' comparable pay is wrong by the ratio of the true hours to 1800 | Configurable 500–2600; tune per tenant | SPM |
| A **single retention clock** (EP38's per-company period) suffices for both the employee record and pay history | **Assumption** (Medium) | A second clock changes the retention model from per-employee to per-class, which is a structural change late | **OQ-BA-6** | BA / DPO |
| The **subject's value is included** in their own group median (BR-4.10), rather than a leave-one-out median | **Assumption** (High confidence on the product reasoning, Medium on the statistics) | Small groups behave differently — at n=3 the middle member can never be flagged. Leave-one-out is arguably a better outlier statistic and is definitely a worse explanation | Validate against the first tenant's first run | BA / SPM |
| The **n=2 group** produces arithmetically useless results (both members equidistant from the midpoint) and this is the justification for `n >= 3` | **Known** (arithmetic) | None — it is provable, and AC-200-22 asserts it | — | BA |
| Tenants will accept that **"No change" must be actively answered** on every position change, including trivial ones (D4c, no exemption) | **Assumption** | If it is felt as friction, managers route around it — via the no-permission path (CFL-42-13) or by not using the modal at all | UX's click-count proof (AC-196-25); first-tenant feedback | UX / SPM |
| **Level titles need to be searchable**, and shipping without it is a regression against today's directory search | **Known** (B42-14) — but the **cost** is an Assumption | If searchability is deferred, relabelling `job_title` to "working title" while making the level title canonical makes search worse than it is today | Architect's estimate under CFL-42-4 | BA / Architect |
| Row scoping in the service layer will not be read by an engineer as the forbidden `enabled_for_hr` sub-flag | **Assumption** (Low confidence — it is a subtle distinction and CC-2 is emphatic) | An engineer "fixes" the scoping out, and every manager sees the whole company's pay | BR-8.2 written here, in the Architect's ADR (SPM §8.2.6), and as a comment in the code | Architect |
| The seeded population (146 PERMANENT, 1 CONTRACTOR, **0 PART_TIME, 0 INTERN**, **0 gender recorded**) will not exercise FTE normalisation, contractor exclusion, intern exclusion **or Check B at all** | **Known** (B42-20, B42-09) | Real defects in four paths would ship untested, and a Check B demo on seed data would show nothing | UAT builds fixtures that do (SPM §8.4.4); a demo needs seeded gender and part-time fixtures | UAT |
| No tenant needs a **"who viewed this salary"** read log in the first release | **Unknown** | It is a common audit expectation for pay data and is awkward to retrofit across a dozen endpoints | **OQ-BA-5** | SPM / DPO |

---

*End of document. Owner: Business Analyst. Consolidated by the SPM in Wave 3. The amendments this document commits
the BA to — `docs/BUSINESS_DOCUMENTATION.md` §4 (retention, and the pre-existing EP38 CFL-3 falsehood),
`docs/BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` (three new feature codes and the §4.8 matrix), and EP38 §4.3
R3.6/R3.7 (the erasure enumeration) — land in the same commit as the implementation they describe, per Charter §5b
rule 1, not in this wave.*
