# EP42 — Compensation, Job Architecture & Pay Equity — SPM Scope & Resolved Decisions

> **Owner:** Senior Product Manager (`../02_SENIOR_PRODUCT_MANAGER.md`) · **Date:** 2026-08-09 · **Status:** Wave 1 —
> issued to the team as the input to Wave 2 (BA, Senior Architect, UX, UAT).
> **Source:** the product owner's request of 2026-08-09, decomposed as **R1–R7** in the shared team brief.
> **Stage:** **S1 — requirements finalisation** (roadmap §E, D-004). Build stage is set per wave in §3.
>
> **What this document is.** Scope boundaries and **decisions**, not questions. Wave 2 starts from here: the BA
> writes acceptance criteria against §4 and §5, the Architect writes ADRs against §4 and §7, UX designs against
> §4 and §8, UAT writes cases against §4, §5 and §7. Where I have *not* decided something, it is in §6 with a
> recommended default so nobody is blocked waiting for an answer.
>
> **What this document is not.** It is not acceptance criteria (BA, Wave 2), not schema (Architect, Wave 2), and
> not legal advice (Charter §9.7 — everything touching pay-transparency law, works councils and GDPR is flagged
> for DPO/legal validation and is written as a product requirement, not an opinion on the law).
>
> **Guardrails obeyed.** `../../CLAUDE.md` is authoritative and is not re-litigated here: the feature-access
> model, company scoping, the no-sub-flags rule, the four-place feature registration rule, and the org-change
> invariants all bind EP42. Where EP42 pushes on one of them it is called out explicitly (§4.6, §4.5, §7.3) and
> routed to the owner of that invariant for sign-off.
>
> **Identifiers.** Epic **EP42**. Stories **KAN-188 … KAN-202**, continuing the sequence from KAN-187. Plain text,
> never links — they are local IDs (`../../docs/project-management/README.md` §Identifiers). Nothing existing is
> renumbered.

---

## 0. Executive summary — the recommendation, then the reasoning

**Build it, in five waves, under a new business goal BG7, with the platform enabler first.** The owner has asked
for three products in one sentence: a **compensation record**, a **job-architecture framework**, and a **pay-equity
engine**. They are not independent — the second is a hard prerequisite for the third, and both are worthless
without the first. Sequencing them as one epic with ordered waves is the only shape that ships value early
without building the equity engine on sand.

**The five things I most want the team to take from this document:**

1. **R5 cannot be built on `job_title`, and this is not a detail — it is measured.** In the seeded data Acme Corp
   has **46 active employees across 41 distinct free-text job titles**, of which exactly **one** title has three
   or more people in it. Telia: **100 employees, 75 distinct titles, six groups of three or more.** A
   "same position" comparison keyed on `job_title` yields comparison groups of size one, and a pay-equity check
   on a group of one is not a weak check — it is *no* check. **R6 (job levels) is therefore a prerequisite of R5,
   not a parallel feature.** Evidence: `psql -d employee` counts, 2026-08-09; `database/schema.sql:411`.

2. **The literal reading of "flag a 5% difference" produces an alert storm that will kill the feature in a week.**
   Any real pay distribution has a >5% max–min spread in almost every group. I have split R5 into two checks with
   different jobs — an **individual outlier** check against the group median (the one a manager acts on) and a
   **gender pay gap** check at group level (the one that matches the 5% figure, and the shape the EU Pay
   Transparency Directive uses) — with minimum group sizes, a data-coverage gate, and an explicit anti-re-fire
   rule. Adoption beats feature count; a muted notification channel is worth zero. See **D1** and **D2**.

3. **R7 must be fixed centrally, not copied a third time.** `company_features.is_enabled` exists but
   `_load_feature_access()` (`app/auth.py:38-95`) does not consult it; it is enforced by hand-rolled checks in
   exactly two blueprints (`app/routes/analytics.py:20-40`, `app/routes/skills_intelligence.py:21`). A commercial
   gate honoured only by the blueprints that remembered to check it is a convention, not a control — and the
   blast radius just changed from "analytics" to "everyone's pay". **KAN-188 makes the tenant switch part of the
   central resolution, sequenced ahead of every compensation story**, exactly the way KAN-187 (audit) was
   sequenced ahead of KAN-184. See **D6**.

4. **"Reaching 1.5 means level 2" is the single biggest ambiguity in the request, and my answer is: not
   automatic.** Automatic roll-up would have the system change a person's job title and pay band with no human
   decision — an automated decision with significant effect on the individual, which is precisely what Charter §1
   tells us to gate, and which no works council will accept. It also has no trigger: there is no scheduler in this
   application. Reaching the last step raises a **promotion-eligible** signal; promotion is a **decision a person
   makes**, routed through the existing approval chain with a mandatory salary review. **Flagged for the owner's
   confirmation as OQ-1** with that default. See **D3**.

5. **T2 is not tripped, and I am not going to pretend it is — but the risk has been re-priced and I am adding
   T5.** Synthetic salary on synthetic people is still synthetic; D-004's sequencing stands and EP42 builds in S3.
   What changes is consequence, not probability: after EP42 the worst case of a T1/T3/T4 event stops being a leak
   of names and org placement and becomes a leak of **every employee's pay**. So I am adding a fifth trigger that
   fires at a much lower bar than T2 — **one real compensation value, anywhere, in any tenant, including a single
   manual entry by the build team**. See **D8**.

**Three long-standing open items close here.** Backlog open item #3 ("promote has no story" — also EP38 **OQ-1**
and **CFL-7**) is answered: promotion is **KAN-197**, in EP42, not a variant of KAN-185. Open item #4 (transfer vs
the EP27 drag-and-drop boundary) is answered in **D4(f)**. Open item #5 (segregation of duties — one person can
satisfy every approval level) is answered in **D4(g)** and carried as **KAN-198**; on money it stops being
theoretical.

**One thing I want on the record before anybody demos this.** Under the current demo-grade auth (email-only, one
click, no password — `app/routes/auth.py`), the compensation visibility matrix in **D5** is correct in code and
**unenforceable in practice**, because identity is self-asserted. That is not an argument to pull security
forward — D-004's rework economics still hold. It *is* a limitation that must be stated out loud at the start of
any compensation demo (Demo Readiness Gate rule 5), and it belongs in the demo script, not in the Q&A.

**Cost I am not hiding.** EP42 adds roughly fifteen stories, three feature codes, five new table sets and on the
order of a dozen new endpoints and several new DOM builders. Every one of those enters the S5 hardening sweep
(KAN-149 CSRF, KAN-150/173 escaping) and the WCAG retro-fit. D-004's S4 feature freeze moves later by the size of
this epic. That is the price of the request and it is worth paying — but it should be paid knowingly.

---

## 1. Epic definition

### 1.1 The epic

| Field | Value |
|---|---|
| **Epic** | **EP42 — Compensation, Job Architecture & Pay Equity** |
| **Business goal** | **BG7 — Pay decisions this company can defend** *(new — argued in §1.2)* |
| **Stage (D-004)** | **S1 now** (this document + Wave 2). **W0 builds in S2** (platform enablers, alongside EP29/EP31/EP32). **W1–W4 build in S3.** Security remains S5 — see D8. |
| **Maturity impact** | **None on its own.** EP42 does not move the product past **P3 Functional Product**; it widens the functional surface that S5 must harden. Claiming otherwise would confuse development-complete with production-ready (Charter §3). |
| **Feature codes** | `compensation` · `compensation_self` · `pay_equity` — three, registered in **all four places** per `CLAUDE.md` (§4.5, D5) |
| **Depends on** | KAN-155 (atomic writes) · KAN-166 (migrations) · KAN-187 (audit — ✅ done, extended) · KAN-168 (real-DB test tier) |
| **Unblocks** | **KAN-185** — its blocked criterion `AC-185-07` (effective dating, CFL-4) is resolved by **KAN-189** |
| **Answers** | Backlog open items #3, #4, #5 · EP38 OQ-1 · EP38 CFL-7 |

### 1.2 Business goal — why **BG7**, not an extension of BG4

**Recommendation: create BG7. Confidence High.** Five arguments, one concession.

1. **BG4 is about lifecycle *events*; compensation is a *data class* and a *decision discipline*.** BG4's stated
   outcome is "onboarding/offboarding workflows, transfers, rehire, vacation balances/accruals" — process
   completeness across the employment lifecycle (roadmap §C). Pay is not an event in that list; it *intersects*
   several of them. Filing the job-architecture framework and the equity engine under BG4 makes them look like
   cousins of offboarding, which they are not, and buries the two largest pieces of this request inside a goal
   whose success measure has nothing to do with them.
2. **It carries a compliance regime no other goal carries.** Pay transparency obligations, works-council
   consultation on job classification, and the tightest read model in the product all attach here and nowhere
   else. Charter §1 makes compliance first-class; a goal with its own regulatory driver needs its own line,
   otherwise it inherits gates from a goal that was never designed to hold them.
3. **It carries a commercial control.** R7 exists because the owner intends to expose or withhold this per
   tenant. No other business goal has packaging in its requirements. That is a business-model objective, not a
   people-ops one.
4. **It measures differently.** BG4 measures process completion. BG7 measures **coverage and defensibility** —
   what fraction of the workforce has a current pay record, what fraction of comparison groups are evaluable, how
   long a flag sits before it is dispositioned. Different numerator, different denominator, different owner.
5. **It is the first goal whose failure mode is reputational rather than operational.** A broken offboarding is a
   bad week. A leaked or wrong pay figure is a grievance, a works-council escalation, and — for a vendor — a lost
   renewal. Risk of that class deserves to be visible at goal level, not three layers down.

**The concession, stated honestly.** R3 (position change) and R4 (promotion) *are* lifecycle couplings and belong
to BG4's territory as much as BG7's. I am not splitting them out. **Wave W3 (KAN-196, KAN-197, KAN-198) is traced
to BG7 and BG4 jointly**, and KAN-197 pays a debt BG4 already owed — the EP38 epic title has promised "promote"
since the roadmap was written and no story has ever carried it (EP38 CFL-7). Creating BG7 does not orphan BG4; it
settles one of its open accounts.

**Proposed BG7 row for the roadmap §C table** *(to be applied in Wave 3 — I am not editing the roadmap in this
wave):*

| # | Business Goal | Serves which product pillar | Outcome | Horizon |
|---|---|---|---|---|
| **BG7** | **Pay decisions this company can defend.** | Core HR / org structure / RBAC | Every employee has a current, effective-dated, auditable pay record on a company-defined job ladder; pay moves with position and promotion through one governed approval; unjustified gaps surface to a named owner before somebody else finds them. | **Now** (requirements, S1) · **Next** (build, S2/S3) |

### 1.3 The problem

**Observation.** The product holds no compensation data of any kind — no salary, pay, grade, band, level or
currency column, table, route, service or template anywhere in the codebase (verified: repo-wide grep,
2026-08-09). It also has no job catalogue: `employees.job_title` is a free-text `varchar(150)`
(`database/schema.sql:411`) and `employee_directory.designation` is a second, unrelated free-text title.

**Evidence of the consequence, not just the absence.** Because there is no pay record, every pay decision this
product's users make is made **off-system** — in a spreadsheet, by email, or in the payroll system that HR cannot
join to org data. That means:
- a position change can be approved through a governed multi-level chain (`org_change_service.py`) while the pay
  consequence of that same change is decided by nobody, in no system, with no record;
- a promotion has no representation at all — the word appears in the EP38 epic title and in no story;
- nobody can answer "are two people doing the same job here paid differently, and can we justify it?" without a
  manual export and a spreadsheet, which means in practice nobody asks until an employee or a regulator does.

**Impact.** The product's own North Star is *"% of target HR workflows completed end-to-end without off-system or
manual intervention"* (roadmap §B). Compensation is the largest single off-system intervention left in the
people-ops surface, and it sits inside two workflows the product already owns end-to-end. Every position change
the portal processes today is a workflow it completes **incompletely**.

**Recommendation.** Build EP42 as scoped in §3.

**Expected outcome.** Position change and promotion become the first two HR decisions in this product where the
org consequence and the pay consequence are decided together, once, by the right people, with a record that
survives the people who made it.

### 1.4 Personas and jobs to be done

Drawn from Charter §1; only the personas EP42 actually serves are listed.

| Persona | Job to be done in EP42 | What they need | Which stories |
|---|---|---|---|
| **HR Administrator / Ops** *(primary)* | Define the ladder, get pay data in, keep it current, answer the equity question before somebody else asks it | Bulk actions, guardrails, a coverage meter that shows how far off "done" they are, error recovery, audit | KAN-190…195, 199…202 |
| **Manager (people leader)** | Decide pay for their own team at transfer and promotion, and understand where a person sits in their range | Their reports' pay only, in the flow they are already in, with no separate screen and no training | KAN-194, 196, 197 |
| **HR Business Partner / pay-equity responsible** | Work a queue of standing pay-equity conditions to disposition | A register, not a task list; a reason field; the ability to say "justified" and have it stay justified | KAN-200, 201 |
| **Employee (self-service)** | See their own pay, level, step and position in range, and trust it | Plain language, no jargon, no implied promise of a future increase | KAN-194 (`compensation_self`) |
| **Customer Administrator (tenant / PORTAL_ADMIN)** | Configure the ladder, the pay markets, the thresholds, and who may see pay | Configuration without engineering; visible consequences of each choice | KAN-190, 194, 199, 200 |
| **Product owner / SYSTEM_ADMIN** | Expose or hide the whole capability per tenant | One switch, honoured everywhere, with a real "not available" screen rather than a 403 | KAN-188 |
| **HR Leadership** | Read coverage and gap trend | Aggregates, never individual amounts unless separately granted | KAN-200 (aggregate view) |

**Deliberately not served in this cycle:** Recruiter and Hiring Manager (offer/candidate compensation needs an ATS
that does not exist), Payroll (no payroll entity, and see §3.3), IT/Platform Admin (no pay integration in scope).

### 1.5 Value and measures of success

The North Star is unchanged (roadmap §B). EP42's contribution is measured by these, and I want them instrumented
as part of the build, not retro-fitted:

| Tier | Measure | Target for a first tenant | Why this one |
|---|---|---|---|
| **Coverage** | % of ACTIVE employees with a current compensation record | **≥ 95%** before equity is enabled | Everything else is meaningless below it — see D7 |
| **Coverage** | % of ACTIVE employees assigned to a job level | **≥ 98%** | The grouping key for R5 |
| **Adoption** | % of applied position changes carrying an explicit salary decision (including a recorded "no change") | **100%** — it is mandatory to answer | Proves R3 is actually happening rather than being skipped |
| **Time-to-value** | Time from tenant enablement to first equity run with ≥95% coverage | **≤ 10 working days** | The backfill is the adoption cliff (D7); if it takes a quarter, the feature never starts |
| **Efficiency** | Median time from a flag being raised to being dispositioned | **≤ 15 working days** | A queue nobody works is worse than no queue |
| **Quality** | % of raised flags dispositioned `JUSTIFIED` on first review | **< 40%** | Above that the threshold or the grouping is wrong and we are generating noise — this is the alert-fatigue tripwire, and it should trigger a config review, not a shrug |
| **Trust** | Number of pay amounts appearing in any surface outside `compensation:r` scope (bell messages, exports, audit diffs, logs, search index) | **Zero, asserted by test** | See D5 and R-3 in §7 |

---

## 2. Verified current-state baseline — my corrections and additions to the brief

The shared brief's §2 baseline is accepted as **Known** except where noted. Everything below I verified myself on
2026-08-09; each row is **Known** unless labelled otherwise. Wave 2 should build on this table, not re-derive it.

| # | Fact | Evidence | Consequence for EP42 |
|---|---|---|---|
| **S1** | **The brief's tenant description is wrong and the correction matters for sizing.** There are **three** companies, not two: **Acme Corp — 46 employees**, **Telia — 100**, **"Sam Cpmapny" — 0 employees but 3 locations (UK, US, India)**, plus **one company-less SYSTEM_ADMIN employee record**. Total 147. The "147 Acme employees" figure in the brief is the *cross-company* SYSTEM_ADMIN dashboard count. | `psql -d employee` — `select c.name, count(*) from employees e left join companies c on c.id=e.company_id group by 1` | The backfill (R2/D7) is **146 rows across two populated tenants**, not 147 in one. The empty third tenant is a genuinely useful test case: a company with locations, zero employees, and a feature switch. |
| **S2** | **Free-text titles do not form comparison groups.** Acme: 46 employees / **41 distinct** `job_title` values / **1** title with n≥3. Telia: 100 / **75 distinct** / **6** titles with n≥3. Largest group system-wide is "Software Engineer" with **5** people, spanning both tenants. | same session — group-by on `job_title`, and a lateral count of per-company groups with n≥3 | **This is the load-bearing fact of the whole epic.** It makes R6 a prerequisite of R5 (D1) and it makes the title→level mapping a real data project, not a story detail (risk R-2). |
| **S3** | **Locations span countries with materially different pay markets.** Acme: Hamburg (Germany), Porto (Portugal), Tallinn (Estonia). Telia: Stockholm (Sweden), Oslo (Norway), Copenhagen (Denmark), Helsinki (Finland), Tallinn (Estonia). `locations` carries `country`, `city`, `office_code`. | `select c.name, l.name, l.country from locations l join companies c…` | Geography is **not optional** in the equity comparison. A Tallinn/Stockholm gap is a labour-market fact; flagging it as a pay-equity finding would be wrong and would discredit the feature on day one. Drives D1's **pay market** concept. |
| **S4** | **There is no FTE and no currency anywhere in the schema**, and `employment_type` is `PERMANENT / CONTRACTOR / INTERN / PART_TIME` with the seeded population at **146 PERMANENT, 1 CONTRACTOR, 0 PART_TIME**. | `database/schema.sql:413,422`; repo-wide grep for `currency`/`fte` in `database/schema.sql` returns nothing; `select employment_type, count(*)…` | Both must be captured on the compensation record (D1). The seeded population is *not* representative — it will not exercise part-time normalisation, so UAT needs fixtures that do. |
| **S5** | **`company_features.is_enabled` is not consulted by the central access resolution.** `_load_feature_access()` reads `role_feature_access` + `company_role_feature_access` only. `company_features` appears in application code in exactly two places: `app/routes/skills_intelligence.py:21,204` and `app/routes/analytics.py:26,119,129,139,146,174`. Nowhere else in `app/`, `templates/` or `setup_db.py`. | `app/auth.py:38-95`; repo grep | Confirms the brief §4 and drives **D6**. The switch works today only because two blueprints remember to ask. |
| **S6** | **`enabled_for_hr` is alive.** The column exists on `company_features` and is still written and read by `app/routes/analytics.py:109,127-131,144` and `app/routes/skills_intelligence.py:183-209`. | same | `CLAUDE.md` forbids introducing the pattern. EP42 must not consume it, and KAN-188 deprecates it (D6). |
| **S7** | **`org_change_requests` has no effective date.** Columns are id, company_id, employee_id, requested_by_user_id, reason, four `from_*`, four `proposed_*`, workflow_id, current_step, status, created_at, updated_at, decided_at. `create_request(company_id, subject_id, requester_user_id, proposed, reason)` has no parameter for one. | `information_schema.columns` for `org_change_requests`; `app/services/org_change_service.py:157` | CFL-4 / `AC-185-07` is real and **EP42 collides with it head-on** — salary is inherently effective-dated. Resolved together in **KAN-189** (D4c). |
| **S8** | **The audit action vocabulary is a deliberately frozen closed enumeration** of 16 codes, with the in-code comment *"Frozen for EP38 … later epics extend the list, they do not redefine the shape."* Retention classes are `STANDARD / EMPLOYMENT / SECURITY`. | `app/services/audit_service.py:73-93` | EP42 extends `ACTIONS`; that is sanctioned, but it is the Architect's edit and needs his sign-off (CFL-42-2). |
| **S9** | **The audit service already refuses secrets by key-substring match** — `_SECRETISH_KEYS = ('password','token','secret','api_key','apikey','private_key','session_key','salt','credential')`, enforced in `_check_no_secrets()`. **Nothing in that list catches a salary.** Diffs are validated as a flat `field -> scalar` mapping, so an amount would be written verbatim today. | `app/services/audit_service.py:95-98, 153-166` | Exactly the mechanism D5 needs, and exactly the gap D5 closes. A `_MONEYISH_KEYS` guard is a small, testable, high-value addition. |
| **S10** | **The audit read surface does not exist yet** and its shape is an open SPM decision (backlog open item #1, Wave 3). Read defaults for the `audit_log` feature are PORTAL_ADMIN + HR_ADMIN. | backlog KAN-187 row; `database/seed_rbac.sql` | The `audit_log` read audience is defined by a **different feature code** than pay will be. This is the decisive argument in D5 for keeping amounts out of the audit diff. |
| **S11** | **The notification bell has three sections**, gated as follows: "Pending Approvals" — **role-gated** `has_role(SOLID_LINE_MANAGER, DOTTED_LINE_MANAGER, HR_ADMIN, SYSTEM_ADMIN, PORTAL_ADMIN)`; "Position Changes" — **feature-gated** `has_feature_access('org_change')`; "My Notifications" — everyone. Icons come from an explicit `NOTIF_ICON` map with a neutral 🔔 fallback that never falls back to ❌. Retirement is via `related_type`/`related_id` and `notification_service.resolve_related()`. | `templates/base.html:290-320, 608-624`; `app/services/notification_service.py:122-141` | D2 must name its section, its icon, its action and its retirement condition against these exact mechanisms. Note the existing precedent at `templates/base.html:639-641`: **reject is a deep link, not a quick action, precisely because a decision without a recorded reason is not auditable.** D2 reuses that reasoning. |
| **S12** | `employees.job_title` is **indexed** (`idx_employees_job_title`) and feeds the full-text search trigger `trg_employee_search` on INSERT/UPDATE of first_name, last_name, job_title, email. | `database/schema.sql:1588, 1861` | Demoting `job_title` to a "working title" while a level title becomes canonical creates two titles with unclear precedence in directory and search. Logged as **CFL-42-4**; EP42 does **not** drop or repurpose the column in this cycle. |
| **S13** | **Assumption (Medium confidence).** The EU Pay Transparency Directive (EU) 2023/970 — whose member-state transposition deadline was 7 June 2026 — uses a **5% gender pay gap within a category of workers** as the trigger for a joint pay assessment where the gap is not objectively justified, and requires employers to group workers into categories performing equal work or work of equal value. | Directive text, from general knowledge — **not** verified against a legal source in this repo | The owner's "let's say 5%" coincides with a real regulatory number of a *different shape* (a gender gap, not a raw dispersion). This is why D1 recommends **two** checks. **Flagged for DPO/legal validation — Charter §9.7. The product must never claim compliance with it; it provides a measurement, not a conclusion.** |
| **S14** | **Known.** `_can_initiate_for` in `org_change_service` prevents an employee initiating their own move (KAN-139); `decide()` contains **no** check preventing one user satisfying multiple approval levels (backlog open item #5, unresolved). | `app/services/org_change_service.py`; backlog open item #5 | A pay equivalent of the first rule is mandatory. The absence of the second becomes materially more serious once requests carry money — **D4(g)**, KAN-198. |
| **S15** | **Known.** `_apply_change` overlays only changed fields onto the outgoing assignment row, after defect D-185-1 silently erased untouched placement data. | backlog D-185-1; `app/services/org_change_service.py` | Any compensation field added to a request inherits this hazard in a worse form: a NULL overwriting an existing salary is data loss of the most sensitive kind. **D4(d)** makes it an explicit rule with a named regression test. |
| **S16** | **Known.** There is no scheduler; background work is ad-hoc `threading.Thread` (KAN-163 not planned). | EP38 baseline B16, re-confirmed | Rules out nightly equity batches and any time-based automatic level progression. Drives **D2** (event-driven + on-demand) and reinforces **D3** (no automatic roll-up — there is nothing to trigger it). |

---

## 3. Scope — in, out, later

### 3.1 The wave model — one epic, five ordered waves

**Recommendation: keep one epic number (EP42) with waves W0–W4. Confidence High.** Three sibling epics would give
three roadmap rows, three sets of dependencies to keep in sync, and a traceability chain that breaks the first
time a story moves. The dependency graph here is a chain, not a lattice — R6 → R5, R1 → R3/R4, platform → all —
and a chain is what waves express.

| Wave | Name | Serves | Build stage | Gate to leave the wave |
|---|---|---|---|---|
| **W0** | **Platform enablers** | R7, and CFL-4 | **S2** (with EP29/EP31/EP32) | The tenant switch is honoured by one central resolution point; `org_change_requests` carries an effective date and KAN-185 can close |
| **W1** | **Job architecture** | R6 | S3 | Every ACTIVE employee in a tenant that has enabled the feature is on a level; the mapping from free-text titles is complete and reviewable |
| **W2** | **The compensation record** | R1, R2 | S3 | ≥95% coverage in at least one tenant; the visibility matrix is asserted by a negative-visibility test suite |
| **W3** | **Coupling to workflows** | R3, R4 | S3 | No position change or promotion can be applied without an explicit, recorded pay decision |
| **W4** | **Pay equity** | R5 | S3 | A flag can be raised, found, dispositioned with a reason, and retired — for every eligible recipient |

**W0 is deliberately in S2, not S3.** It is platform work of exactly the kind the S2 enabler set already holds, it
unblocks a story that is stuck **today** (KAN-185 / `AC-185-07`), and putting it in S3 would mean the first
compensation story is written against an access model we already know is wrong.

### 3.2 In scope

**W0 — platform**
- The tenant exposure switch (`company_features.is_enabled`) becomes part of the central feature-access
  resolution, applied uniformly to every feature, with a real "not available for this tenant" state.
- Retro-fit of the two existing ad hoc consumers (`reports`, `skills_intelligence`) onto the central mechanism, so
  there is one implementation and not three.
- `effective_date` on `org_change_requests` and `create_request()`, used as the boundary date by `_apply_change`,
  resolving CFL-4's one-day assignment overlap in the same change.

**W1 — job architecture (R6)**
- Per-company **job families**, **job levels** (ordinal, each carrying its own title), and **steps** within a
  level (count configurable per level, default 5, displayed `<level>.<step>`).
- Assignment of an employee to a (family, level, step), with effective dating.
- A mapping surface to get the existing free-text `job_title` population onto levels, with CSV round-trip.
- Step advancement and level promotion as **explicit, audited, reversible decisions** — including skip-step,
  skip-level and downward moves, each with a mandatory reason.

**W2 — the compensation record (R1, R2)**
- An **effective-dated, append-only compensation history** per employee: annual base amount, currency, **FTE**,
  pay basis (annual / monthly / hourly, normalised to annual for comparison), effective_from, actor, reason,
  correlation id.
- The visibility model of **D5**, expressed as three feature codes plus service-layer row scoping.
- **"My Pay"** on the employee's own profile (`compensation_self`).
- Backfill: **bulk CSV import with dry-run → diff → commit** (reusing the EP35-S2 shape) **and** single-employee
  manual entry; a company-level **coverage meter** and an exportable missing list.

**W3 — coupling (R3, R4)**
- A **compensation block inside the existing shared position-change modal** — one modal, one endpoint, one engine,
  three entry points (org-tree drop, profile, directory `⋯`).
- A mandatory, explicitly-answered pay decision on every position change: *no change · new salary · defer with a
  reason*.
- **Promotion** as a first-class request type on the same engine, proposing a new (family, level, step) and
  carrying a salary review that cannot be silently skipped.
- **Four-eyes on money**: a user may not satisfy more than one approval level of a request that carries a
  compensation change.

**W4 — pay equity (R5)**
- Per-level, per-pay-market **salary bands** with a midpoint and a compa-ratio.
- The **comparison engine**: group formation, minimum group sizes, coverage gate, individual-outlier check against
  the group median (or band midpoint where one exists), and a group-level **gender pay gap** check.
- Per-company configurable **thresholds** (per check), pay-market definition, and justification validity window.
- The **flag lifecycle**: raise → deliver → disposition (`JUSTIFIED` / `REMEDIATION_PLANNED` / `RESOLVED`) →
  retire → controlled re-fire.
- A **compensation history read surface** (per-employee timeline), and the audit coupling of D5.

### 3.3 Out of scope — explicit, and do not let these leak in

None of the fifteen stories delivers any of the following. If one appears in a Wave 2 artifact, it is scope creep
and I will send it back.

**Pay mechanics we are not building:** payroll processing · payslips · gross-to-net, tax, social contributions,
deductions · payment instruction or banking details · pay runs or pay periods · retroactive pay recalculation ·
final pay, severance or notice-period calculation.

**Reward components we are not building:** bonus, commission, variable pay, sales incentives · equity, options,
LTIP, RSUs · pension and employer contributions · benefits, allowances, car, insurance, company-paid anything ·
total-reward statements · **"total compensation" as a computed figure** (see OQ-5 — base only, this cycle).

**Compensation processes we are not building:** annual merit / comp-review **cycles** — budgets, matrices, manager
worksheets, calibration, approvals-by-budget. This is a product in its own right and is easily larger than EP42
entire · promotion nomination and calibration rounds · off-cycle increase request workflows separate from the
position-change engine · budget-aware or headcount-cost-aware approval.

**Data and integration we are not building:** payroll-system integration in either direction (EP40-S3 territory) ·
external market or benchmark data feeds · **FX rate feeds** (see D1 — the default configuration does not need one)
· salary history import from a prior HRIS beyond the defined CSV shape · candidate or offer compensation (there is
no ATS).

**Compliance artefacts we are not building:** statutory gender-pay-gap **report generation or filing** — we compute
a gap and show it; producing a regulator-shaped filing is a separate, jurisdiction-specific deliverable ·
pay-transparency statements in job adverts (no recruitment surface exists) · any claim, in product or
documentation, that the product makes a customer compliant with any pay-transparency law.

**Automation we will not build, in this cycle or any other, without a compliance gate:** any **automatic** pay
change · any **automatic** level or step progression (D3) · any algorithmic pay recommendation, market-matching
score or "suggested increase". Charter §1 (GDPR Art. 22, EU AI Act) and roadmap Decision D-003 apply, and pay is
the clearest "legal or similarly significant effect" in the whole product.

**Also out:** cost-of-living or geo-differential *engines* beyond the pay-market grouping key · headcount cost
budgeting and forecasting · compensation analytics dashboards beyond the equity queue and the coverage meter ·
cross-tenant pay comparison of any kind, for any role, including SYSTEM_ADMIN aggregates.

### 3.4 Later — named so they are not forgotten, and not scheduled

Total compensation (OQ-5) · comp-review cycle tooling · pay-transparency statements to employees and candidates ·
statutory gap-report export · **scheduled periodic equity re-evaluation** (needs KAN-163 — until then, event-driven
and on-demand only, D2) · a **divergent pay effective date** distinct from the placement effective date (D4c) · FX
rates and multi-currency pay markets (D1) · band derivation from market data · budget-aware approvals · manager
self-service "what would this cost" modelling.

### 3.5 Why not three sibling epics

Considered and rejected. **Options:** (a) one epic, five waves — *chosen*; (b) three epics EP42 job architecture /
EP43 compensation / EP44 pay equity; (c) fold compensation into EP38 and job architecture into EP27.

(b) is superficially tidier and genuinely worse: the dependency between them is a hard chain, so three epics would
carry three copies of the same sequencing constraint and drift the first time one moves; the three share one
feature-code family, one permission model and one audit vocabulary, so a change to any of those would need three
epic updates; and the roadmap would show three "Now" epics for what is one commitment. (c) is wrong on ownership —
EP38 is a lifecycle epic with its own stage and its own BA deliverable already in flight, and burying a new data
class inside it would make both harder to reason about.

---

## 4. Decisions resolved

*These are **rules**, not preferences. They are the calls engineering would otherwise each make differently. Each
is stated once here, and Wave 2 enforces it through numbered acceptance criteria (BA), an ADR (Architect), a
design (UX) and a test case (UAT). Where a decision needs the product owner's ratification it says so and appears
in §6 with a default so nobody waits.*

### 4.1 D1 — Pay equity: the comparison group, the basis, and why there are **two** checks (R5)

> **Owner of the call:** SPM. **Confidence: High** on the grouping and basis; **Medium** on the specific default
> thresholds, which are configuration and should be tuned against the first tenant's real distribution.
> **Ratification needed** on one point only — OQ-3, whether the owner wants the gender-gap check at all.

#### 4.1.1 The rule

**Comparison group = `(company_id, job_family, job_level, pay_market)`.** Not `job_title`. Not step. Not location.

- **Not `job_title`** — measured, not asserted: Acme has 41 distinct titles over 46 people with exactly **one**
  title reaching n≥3; Telia 75 over 100 with six. Grouping on free text produces groups of one, and a group of one
  has no median, no spread and no finding. It would also split real groups on spelling ("Software Engineer" /
  "Senior Software Engineer" / "Backend Engineer" are three groups today) and merge unrelated ones across tenants.
  Evidence: S2.
- **Not step** — steps within a level are *designed* to differ in pay. Comparing across steps and flagging the
  spread would flag the ladder itself as a pay-equity problem, every time, in every group. Step is carried into
  the finding as an **explanatory factor**, not as part of the key.
- **`pay_market` is mandatory, not optional.** A **pay market** is a company-defined grouping of locations;
  the **default is one pay market per `locations.country`**, and PORTAL_ADMIN may merge countries into one market
  or split a country. Evidence for why this is not a nicety: Telia's five locations span Sweden, Norway, Denmark,
  Finland and Estonia (S3). A 5% Stockholm-versus-Tallinn gap is a labour-market fact. Reporting it as a
  pay-equity finding would be **wrong**, and the first wrong finding is the one that costs the feature its
  credibility permanently.
- **Job family** is in the key because a level-3 engineer and a level-3 accountant are not doing equal work, and
  levels are ordinal within a family by construction (D3).

**Comparison basis: against the group, never pairwise.**

- **Primary basis where a band exists (after KAN-199): compa-ratio to the band midpoint** for the employee's level
  and pay market. A band encodes *intent*; the group median only encodes *who happens to be in the group today*.
- **Fallback basis where no band exists: the group median.** Median, not mean — a single executive salary in a
  group of eight drags a mean far enough to hide a genuine outlier.
- **Never pairwise.** Every-pair comparison on a group of ten is 45 comparisons and, at a 5% threshold, produces
  dozens of "findings" describing the same one person. One person, one finding.

**What is compared: FTE-normalised annualised base salary, in the currency of the pay market.**

- **Base only.** No variable pay exists in the data model and none is in scope (§3.3). Comparing base while
  bonuses differ is a known limitation and must be stated on the screen, not hidden.
- **FTE-normalised** — FTE is stored on the compensation record and is **not** in the schema today (S4). A
  0.6 FTE part-timer's headline salary is not comparable to a full-timer's; normalising is the only honest
  arithmetic.
- **Annualised** from the recorded pay basis (annual / monthly / hourly), using the company's configured
  standard annual hours where hourly.
- **Excluded from every comparison, by default:** `employment_type = 'CONTRACTOR'` (a day rate is not a salary),
  `'INTERN'`, and any employee with no compensation record (D7). Exclusions are **counted and shown**, never
  silent. `'PART_TIME'` is **included** via FTE normalisation.
- **Currency.** Because the default pay market is one country, the default configuration is **single-currency
  within a group and needs no FX at all**. Where a company merges countries into one market, that configuration is
  **refused** unless a manually-maintained, effective-dated FX rate exists for every currency in the market. No
  silent 1:1, no implicit conversion, ever. FX feeds are Later (§3.4).

**Two checks, because one number cannot do two jobs.**

| | **Check A — individual outlier** | **Check B — group gender pay gap** |
|---|---|---|
| **Question it answers** | "Is *this person* paid out of line for their level?" | "Does *this group* show a gender gap we cannot justify?" |
| **Audience** | HR admin, manager | Pay-equity responsible, HR leadership, and eventually the regulator |
| **Unit** | One employee | One comparison group |
| **Basis** | Compa-ratio to band midpoint, else to group median | (Median male − median female) / median male, within the group |
| **Default threshold** | Flag below **0.95** or above **1.10** compa-ratio | Flag at **≥ 5%** |
| **Minimum group size** | **n ≥ 3** comparable employees | **n ≥ 5**, and **≥ 2 of each gender compared** |
| **Below the minimum** | "Insufficient comparison group" — reported in the coverage view, **never raised as a flag** | Same |
| **Maps to** | The owner's operational intent | The owner's literal "5% for the same position", in the shape the law uses (S13) |

**Threshold configuration.** Every threshold above is **per company, per check, configurable by PORTAL_ADMIN
only, every change audited, with the defaults shown as defaults.** Ranges: compa-ratio bounds 0.50–1.00 and
1.00–2.00; gender-gap threshold 1–50%; minimum group sizes 2–50; coverage gate 50–100%. **Nothing is hardcoded —
"let's say 5%" is explicitly the owner telling us it is a parameter.**

#### 4.1.2 Why two checks rather than the one the owner asked for

**Observation.** Read literally, R5 says: flag when two people in the same position differ by 5%.
**Evidence.** In any real salary distribution, a 5% max–min spread inside a group of three or more is close to
universal — it is roughly one annual merit increment. Applied literally to Telia's six evaluable groups, this
would flag most of the population on the first run.
**Impact.** HR mutes it. They can, trivially: `notification_mutes` already exists. A muted compliance control is
worse than no control, because the organisation now believes it has one.
**Recommendation.** Split as above: an individual outlier check tuned to produce a workable number of actionable
findings, and a group gender-gap check that carries the 5% and the compliance meaning.
**Expected outcome.** A queue an HR business partner can actually clear, and a number that means something when
somebody asks for it. The quality tripwire in §1.5 (>40% of flags dispositioned "justified") is the instrument
that tells us if the thresholds are still wrong.

#### 4.1.3 What EP42 must never claim

The product **computes a measurement**. It does not determine whether work is "of equal value", it does not decide
whether a gap is objectively justified, and it must not describe its output as a compliance result. Every equity
screen carries plain-language framing to that effect. **Flagged for DPO/legal validation** (Charter §9.7); S13 is
an Assumption, not a Known.

### 4.2 D2 — Who the "HR responsible" is, and how a flag reaches them (R5)

> **Owner of the call:** SPM. **Confidence: High.** No product-owner ratification needed except the default
> recipient set, which is a matrix default a tenant can change.

#### 4.2.1 Who

**Rule: no new role. The "HR responsible" is defined by the existing feature-access matrix, plus an optional
per-company named escalation recipient.**

- The recipients of a pay-equity flag are **the holders of `pay_equity` read in that company**, resolved exactly
  the way every other feature audience is resolved. Seeded defaults: **HR_ADMIN r+w**, **PORTAL_ADMIN r+w**,
  everyone else none. SYSTEM_ADMIN needs no row (`CLAUDE.md` — automatic bypass).
- **Optionally**, a company may name **0..n specific employees** as escalation recipients in company settings.
  Where the list is non-empty, those people are notified **in addition to** the matrix holders.

**Two rejections, stated so nobody re-opens them:**

- **A new global role (`COMPENSATION_ADMIN` / `PAY_EQUITY_RESPONSIBLE`) is rejected.** Roles are per-company rows
  matched by name; a new global template role must be seeded into every tenant and then granted, which is more
  moving parts than the matrix that already exists to answer this exact question. The matrix *is* the mechanism
  `CLAUDE.md` mandates.
- **The named-recipient list may never remove access from anybody the matrix grants.** It adds recipients; it does
  not gate the feature. A list that could deny is the `enabled_for_hr` mistake wearing a different hat, and
  `CLAUDE.md` forbids it by name. This must be an explicit acceptance criterion, because it is exactly the kind of
  thing that gets implemented as a filter by accident.

#### 4.2.2 How it is delivered — a queue **and** a bell entry, with different jobs

**The primary surface is a queue, not a notification.** A pay-equity flag is a **standing condition**, not a task.
Conditions belong in a register you can filter, sort, disposition and report on. The bell is how somebody
*discovers* there is something in the register; the register is where the work happens.

**Queue** — `/compensation/equity`, gated `@require_feature_access('pay_equity')`. Columns: subject, level, pay
market, group size, basis, measured gap, threshold, raised date, state, owner. Filters by state, group and age.
Bulk disposition is **not** offered — see below.

**Bell — every element of D4's blind-spot list, answered explicitly** (this is the checklist DEF-001/2/3 exist to
enforce, and I will not accept a Wave 2 artifact that leaves any row blank):

| Blind-spot item | Decision |
|---|---|
| **Which section** | A **new fourth section, "Pay Equity"**, placed after "Position Changes" and before "My Notifications" (`templates/base.html:290-320`) |
| **How is it gated** | `{% if has_feature_access('pay_equity') %}` — **feature-gated, never role-gated** (`CLAUDE.md`; the existing "Pending Approvals" section is role-gated and is *not* the pattern to copy) |
| **When is the section visible** | Only when the viewer has ≥1 flag in `OPEN` state; hidden entirely otherwise. Never an empty "no findings ✓" that could be read as "we are fine" while coverage is 40% (D7) |
| **Icon** | **⚖️**, added to `NOTIF_ICON` as `PAY_EQUITY_FLAG_RAISED: '⚖️'`. Never ❌ — the neutral 🔔 fallback stays, and a standing condition is not a rejection (DEF-002) |
| **Badge** | Counts `OPEN` flags visible to this user, added to the existing bell badge total |
| **Quick action** | **One: "Review →"**, deep-linking to the queue filtered to that flag. **No dispose-from-the-bell.** Rationale is the existing precedent at `templates/base.html:639-641` — rejection is a deep link *because a decision without a recorded reason is not auditable*. Dismissing a pay-equity finding is exactly that decision |
| **Does the message contain an amount** | **No. Never.** Notification bodies are readable by anyone who can read the row and are not scoped by `compensation:r`. The message names the subject, the group and that a threshold was exceeded — no salary, no gap percentage that could be inverted to one. See D5 and risk R-3 |
| **When does it retire** | On the flag leaving `OPEN` — i.e. on **disposition** (`JUSTIFIED`, `REMEDIATION_PLANNED`, `RESOLVED`), or automatically as `RESOLVED_BY_DATA` when a re-evaluation finds the gap below threshold. Implemented with `notification_service.resolve_related()` and `related_type='pay_equity_flag'` / `related_id=<flag id>` — the mechanism migration 09 added for DEF-003 |
| **Does it retire on read** | **No.** Reading is not deciding. This is the DEF-003 failure mode in reverse and it must be asserted by test |
| **Who else sees it retire** | **Every** eligible recipient, not only the one who acted — DEF-003's actual defect. UAT asserts this across at least three recipients |

#### 4.2.3 The flag lifecycle, and the anti-fatigue rule

```
                     re-evaluation finds gap < threshold
        ┌──────────────────────────────────────────────────────┐
        │                                                      ▼
     OPEN ──► JUSTIFIED (reason mandatory, validity window)  RESOLVED_BY_DATA
        │
        ├──► REMEDIATION_PLANNED (owner + target date mandatory) ──► RESOLVED
        │
        └──► RESOLVED (gap closed by an actual pay change)
```

- **Every disposition requires a recorded reason.** No one-click dismiss anywhere in the product. `JUSTIFIED`
  additionally requires selecting a justification category from a company-configurable list (seniority, tenure in
  role, performance, market premium, red-circled legacy pay, other-with-text).
- **A `JUSTIFIED` flag does not re-fire** for the same `(subject, group, basis)` while its justification is inside
  its **validity window — default 12 months, company-configurable**. It re-fires early only if **(a)** the gap
  widens beyond `threshold + 2 percentage points`, or **(b)** the subject's level, step or salary changes, or
  **(c)** the company changes the threshold or the pay-market definition. **This rule is a requirement, not an
  optimisation.** Without it, every re-evaluation re-raises every previously-justified finding, HR mutes the
  channel, and the feature is dead — see §1.5's quality tripwire.
- **Evaluation cadence: event-driven plus on-demand. No batch.** There is no scheduler (S16). A group is
  re-evaluated when a compensation record is written, a level/step assignment changes, an employee joins or leaves
  the group, or a threshold/pay-market setting changes; plus a manual **"Run equity check"** on the queue. Periodic
  automatic re-evaluation is **Later**, dependent on KAN-163.
- **Every state transition is audited** with actor, reason and correlation id, and — per D5 — **without the
  amount**.

### 4.3 D3 — The job-level model (R6)

> **Owner of the call:** SPM, with **one point requiring the product owner's confirmation** — the roll-up
> semantics, **OQ-1**. **Confidence: High** on the model; **High** on the recommendation against automatic
> roll-up; **Medium** on the default step count.

#### 4.3.1 The four objects, defined

| Object | Definition | Carries a title? | Carries pay? | Scope |
|---|---|---|---|---|
| **Job family** | A discipline whose roles are comparable to one another — Engineering, Sales, Finance. Company-defined; the product ships none. | No | No | Per company |
| **Job level** | An ordinal rung **within** a family (1, 2, 3 …). This is the unit of job architecture, the grouping key for R5, and the thing a promotion moves you between. | **Yes** — the level's title *is* the canonical job title ("Software Engineer", "Junior Software Engineer") | From KAN-199: **a band per (level × pay market)** | Per company, per family |
| **Step** | A sub-rung **within** a level, displayed `<level>.<step>` — 1.1, 1.2 … Steps exist so pay can progress inside a level without a promotion. | **No** | Optionally a **target point** in the band (a percentile) | Per level |
| **Working title** | `employees.job_title` — the free text that exists today ("Payments Platform Engineer"). Kept, **demoted**, never used as a grouping key again. | It *is* a title, but not the canonical one | No | Per employee |

**On `employees.job_title`.** It is **not** dropped, repurposed or renamed in this cycle. It is indexed
(`idx_employees_job_title`) and feeds the search trigger (`trg_employee_search`) — S12. It is relabelled in the UI
as **"Working title"** and the level title becomes what directory, org tree and reporting display as the job.
**Precedence between the two, in every surface, is a real question and I am handing it to the BA and the Architect
as CFL-42-4** rather than deciding it from a distance; my steer is *level title is canonical, working title is
supplementary and shown in parentheses where both exist*.

#### 4.3.2 The disputed example — defused

The owner wrote: *"Software engineer level 1 … 1.1 1.2 and 1.3 till 1.5 level and while employee reaches to 1.5
level 2 will be considered as Junior Software engineer"*. Read literally, that puts "Junior Software Engineer"
**above** an unnamed level 1, which is the opposite of most conventions.

**This is not a product ambiguity — it is seed data.** The mechanism is "each level carries its own title"; which
titles sit on which rungs is a per-tenant configuration decision that Acme and Telia will each make differently.
**EP42 ships a configurator and a worked example, and no opinionated ladder.** I am not going to encode one
company's naming convention in a platform. *(Recorded as OQ-4 with that default, so the owner can confirm the
example was illustrative rather than prescriptive.)*

#### 4.3.3 Step count: **configurable per level, default 5, range 1–12**

The owner's "1.1 … 1.5" is prefaced with "let's say". Five is a sane default and a terrible constant: companies
genuinely differ, a level near the top of a ladder often has fewer steps than one at the bottom, and hardcoding
five buys a migration later for nothing saved now. A `steps_count` integer on the level costs nothing today.
**Confidence Medium on the default 5 — it is a default, and the first tenant will tell us.**

#### 4.3.4 The roll-up: **not automatic. Promotion is a decision a person makes.** — the biggest call in EP42

**Observation.** The request can be read as "on reaching step 1.5, the employee automatically becomes level 2".

**Evidence and reasoning against automating it:**

1. **It would be an automated decision with a significant effect on an individual.** Changing a person's job level
   changes their title, their salary band, their comparison group and their promotion history, with no human in
   the loop. Charter §1 flags exactly this class (GDPR Art. 22, and the EU AI Act's employee-evaluation category)
   as requiring human oversight and a right to explanation. It is also, in most of the jurisdictions in this
   product's seed data (Germany, the Nordics), the kind of job-classification change a works council expects to be
   consulted on. We would be building the one thing our own charter tells us to gate.
2. **There is no trigger.** The application has no scheduler (S16). Nothing advances a step by itself; a step
   change is *already* a human write. "Automatic on reaching 1.5" would in practice mean "as a side-effect of
   whatever human action set the step", which is a hidden consequence, not an automation.
3. **The asymmetry is decisive.** A company that *wants* rule-based progression can be served later by a policy
   engine on top of an explicit decision model. A company that gets a promotion *by accident* cannot be un-served
   — the title changed, the band changed, the person was told.
4. **It conflicts with the shape of the rest of the product.** Every other consequential change here goes through
   a sequential, company-configurable approval chain in which nothing is applied until the final level approves
   (`CLAUDE.md`, org-change invariant 3). An automatic promotion would be the only material change to a person's
   record that bypasses it.

**The rule:**

- **Step advancement** is an explicit, audited action by a `compensation`-write holder or the subject's solid-line
  manager. It does **not** require the approval chain unless it carries a pay change — in which case it is a
  compensation change and D4 applies.
- **Reaching the last step of a level** sets a **`promotion_eligible`** marker on the assignment and raises a
  notification to the subject's solid-line manager and to `compensation` write holders. It is a **signal, not a
  transition** — and it must be worded as one, in plain language, with no implied promise. UX owns that wording;
  it is the single most easily misread sentence in the epic.
- **Promotion to the next level is a `PROMOTION` request** on the existing org-change engine (D4e, KAN-197),
  proposing a new (family, level, step) and carrying a mandatory salary review.
- **Skips and reversals are allowed, with a reason.** Skip-step, skip-level and **downward** moves (demotion,
  restructure, correction) are all supported through the same request type with a mandatory reason and full audit.
  A one-way ratchet is a fiction, and blocking these means HR edits the database — which is worse than a governed
  path with a recorded justification.

**Flagged to the product owner as OQ-1** with "human decision" as the default. This is the one place where I want
his explicit word rather than my inference, because the two readings produce genuinely different products.

#### 4.3.5 Bands: attach to **level × pay market**, and they are a **Should**, not a Must

- A band is `(job_level, pay_market) → (min, midpoint, max, currency, effective_from)`.
- **Steps do not carry bands.** A step may optionally carry a **target point** — a percentile within the level's
  band — which is guidance for a pay decision, never an enforced value.
- **Bands are KAN-199, in W4, and Should · P2.** The equity engine works off the group median without them (D1),
  so bands are not on the critical path; where a band exists, it becomes the better comparison basis. Making them
  a Must would put a large configuration exercise between the tenant and their first useful equity run.
- Nothing in the product **enforces** a band: a salary outside the band is **allowed**, **flagged**, and requires a
  reason. Hard-blocking out-of-band pay would be wrong (red-circled legacy pay and genuine market premiums exist)
  and would push the decision off-system, which is the problem we started with.

### 4.4 D4 — How salary couples to position change (R3) and promotion (R4)

> **Owner of the call:** SPM, with **(g)** needing ratification (OQ-9) and **(c)** needing the Architect's schema
> design. **Confidence: High.**

#### 4.4.1 (a) Salary rides **inside** the existing `org_change` request. There is no parallel approval.

**Rule.** A position change and its pay consequence are **one request, one chain, one decision, one effective
date**, carried by `org_change_service` with additional proposed fields. Not a second workflow, not a second
engine, not a linked pair.

**Why.** Two parallel approvals for one event can disagree, and there is no coherent state on the other side of
that disagreement: transfer approved and salary rejected leaves a person moved with no pay decision; the reverse
leaves a pay change for a role they are not in. Nobody owns the reconciliation. Beyond that, the existing engine
already provides sequential company-configurable multi-level approval where nothing is applied until the final
level approves and any rejection applies nothing (`CLAUDE.md`, invariants 3 and 5), and it already carries the
rule that **an employee can never initiate their own move** (`_can_initiate_for`, KAN-139) — a rule that is
*mandatory* for pay and would otherwise have to be reinvented, less well, in a second place.

#### 4.4.2 (b) Approver eligibility when a request carries money

**Rule.** If a request carries a compensation change, **every step of its resolved chain must be satisfiable by at
least one approver who holds `compensation` read.** This is checked **at create time**; if any step cannot be
satisfied, the request is **refused** with an error naming the step and the missing permission, and **nothing is
written**.

**Why, and what was rejected.** The alternative — let an approver decide a change whose amount they cannot see —
is asking someone to approve a blank cheque. The other alternative — show the amount to every approver regardless
of permission — makes the chain a hole in the visibility model of D5. Refusing at create time follows the pattern
EP38 already established for unsatisfiable approvals (block, name the reason, write nothing — AC-184-18) rather
than creating a request that stalls forever.

**The escape hatch, so this is not a trap.** The initiator may raise the **placement change without pay** (the
"defer" option in (c)) and the pay change as a **separate, subsequent** compensation request. That is sequential,
not parallel, so it does not re-open the disagreement problem — and it makes the configuration consequence visible
to the tenant rather than silent.

#### 4.4.3 (c) Every position change carries an **explicitly answered** pay decision — which may be "no change"

**Rule.** The compensation block on the request is **mandatory to answer, not mandatory to change**. Three
options, no default pre-selected:

1. **No change** — recorded as an affirmative decision, with the current salary shown for context.
2. **New salary** — amount, currency, FTE, effective date, reason.
3. **Defer to a separate review** — reason mandatory, and it creates a visible follow-up rather than a silence.

**Why.** R3 says a position change *"should also consider a salary update"*. "Considered" is satisfied by a
recorded answer and by nothing less; an unanswered optional field means the pay question fell on the floor, which
is precisely the status quo we are replacing. The recorded "no change" *is* the evidence that it was considered.
All four existing proposed dimensions (BU, functional unit, location, manager) are material enough to require the
answer; there is no "trivial change" exemption, because deciding what is trivial is how exemptions grow.

**For a `PROMOTION` request the bar is higher:** "no change" requires an explicit recorded reason. R4 asks for a
salary review at promotion; a promotion with no pay movement and no explanation is the thing R4 exists to stop.

#### 4.4.4 (d) Effective dating: EP42 and CFL-4 resolve **together**, once, in KAN-189

**The collision.** `AC-185-07` is BLOCKED because `org_change_requests` has no effective-date column and
`create_request()` no parameter for one (S7). Separately, CFL-4 records that `_apply_change` closes the outgoing
assignment with `effective_to = CURRENT_DATE` while the incoming row defaults `effective_from = CURRENT_DATE`,
producing a one-day overlap in every move. And salary is **inherently** effective-dated.

**The rule.** **KAN-189 adds one `effective_date` to the request** and threads it through `create_request()` and
`_apply_change`, where it becomes the boundary date for closing the outgoing assignment and opening the incoming
one — which resolves the CFL-4 overlap in the same change rather than leaving two date conventions to diverge.
**That same date drives the compensation record's `effective_from`.** One date on the request; placement and pay
move together.

**Consequences, stated:**
- **KAN-189 is in W0 (stage S2), not W3.** It unblocks KAN-185 **today**, and KAN-185 is 🟡 in progress and stuck.
  EP42 pays a debt EP38 is carrying.
- The **convention** for the boundary (half-open intervals versus `effective_to = date − 1`) is the **Architect's**
  call — it is his conflict (CFL-4) and his schema. EP42's requirement is only that after any applied change there
  is **exactly one** current assignment and **no overlapping day**, asserted by test.
- **A pay effective date that differs from the placement effective date is a real HR case and is Later** (§3.4).
  The column must be **designed** so a divergent date can be added without a migration of meaning, but this cycle
  ships one date. Stated so the Architect does not model it away.
- **Backdating and future-dating.** Both are permitted for compensation, within a company-configured window
  (default: 90 days back, 180 days forward). A future-dated *placement* remains constrained by the absence of a
  scheduler (EP38 R5.6) — a future-dated compensation record is inert data until its date, which is safe; a
  future-dated placement is not. Do not let the two be conflated.

#### 4.4.5 (e) Promotion (R4) is a **request type**, not a new engine

**Rule.** `org_change_requests` gains a **`request_type`** ∈ `TRANSFER` · `PROMOTION` · `COMPENSATION_REVIEW`,
defaulting to `TRANSFER` for every existing row. All three run on the same engine, the same chain and the same
apply path.

- `TRANSFER` — proposes BU / functional unit / location / manager. Pay decision mandatory to answer (c).
- `PROMOTION` — proposes a new (family, level, step), optionally with placement changes. Pay decision mandatory to
  answer, and "no change" requires a reason.
- `COMPENSATION_REVIEW` — proposes **only** a pay change. This is the escape hatch in (b) and the vehicle for an
  ordinary off-cycle increase. It is **not** a comp-review *cycle* (§3.3).

A company may configure a **different approval chain per request type** (a pay change may need a level a transfer
does not). Where no chain is configured for a type, the `TRANSFER` chain applies — no request may ever run with
*no* chain.

**This closes backlog open item #3 and EP38 OQ-1/CFL-7:** promotion is **KAN-197 in EP42**, and it is explicitly
**not** a variant of KAN-185. The BA should record EP38 OQ-1 as answered.

#### 4.4.6 (f) The boundary with EP27's drag-and-drop — backlog open item #4, answered

**Rule.** **One modal, one endpoint, one engine, three entry points.** The shared dialog already extracted to
`templates/org_change/_move_modal.html` under KAN-185 gains the compensation block, and is reached from the
org-tree drop, the employee profile, and the directory row `⋯` menu. The **request type is inferred from what the
user changed**: placement only → `TRANSFER`; level changed → `PROMOTION`; pay only → `COMPENSATION_REVIEW`.

**Therefore the drag-and-drop path is not a second way to do the same thing — it is a third way to open the same
thing.** That is the boundary open item #4 asked for. Two constraints on it:
- The compensation block must **not** make the common case heavier. Most moves have no pay change; the block opens
  collapsed on "No change" **unselected**, requiring one deliberate click, and must not add a step or a scroll to
  the existing flow. **UX owns proving this** (§8.3).
- A drop by a user without `compensation:r` opens the modal with the compensation block **absent** — not disabled,
  not blank — and the request it creates is a placement-only `TRANSFER`. Absent, not hidden: see D5 and R-3.

#### 4.4.7 (g) The partial-proposal hazard — D-185-1, in a worse form

**Rule.** A compensation apply may **never** write a NULL or a zero over an existing salary. The apply path
overlays only what the request actually proposed, exactly as `_apply_change` now does for placement (S15).

This is not a hypothetical: D-185-1 was a live data-loss defect that **all 4,628 tests passed through**, because
every existing test passed a fully-populated proposal. The same shape applied to pay silently zeroes somebody's
salary. **A named regression test is required** — the Wave 2 UAT brief calls for the compensation equivalent of
`TestApplyCarriesUnchangedFieldsForward`, covering pay-only, placement-only, level-only, full and
no-prior-record proposals.

#### 4.4.8 (h) Segregation of duties on money — backlog open item #5, decided

**Rule, and it is a split decision:**

- **For any request carrying a compensation change or a level change: option (a) — a hard rule.** A user may not
  decide more than one level of the same request. The second decision is refused with a specific message naming
  the level they already decided. Not configurable, not overridable, not warn-and-allow.
- **For placement-only requests: option (b) — warn, allow, and record it in the audit trail as a self-approval.**
  Unchanged behaviour, made visible.
- **In both cases**, the approval-chain admin page must **show the overlap at configuration time** — "levels 1 and
  2 can both be satisfied by the same person" — so a company sees it when it is cheap to fix.

**Why the split.** The observed case (Acme: level 1 is the `HR_ADMIN` role, level 2 a named approver who also
holds `HR_ADMIN`) means a chain the company configured as two-level control operates as one-person control. On
placement that is a governance smell the company may genuinely have intended. On **money** it is the textbook
control failure, and the cost of getting it wrong is not symmetrical: a blocked second approval is an
inconvenience, an unnoticed single-person pay approval is a finding. Where the cost is asymmetric, take the
conservative side.

**This is carried as KAN-198.** It touches `decide()` in the shared engine, so it needs the **Architect's**
sign-off (CFL-42-5) and it changes behaviour for EP27 and EP38 as well as EP42 — which is a further argument for
doing it deliberately, once, rather than as a side-effect of a compensation story. **Ratification: OQ-9.**

### 4.5 D5 — Who may see a salary

> **Owner of the call:** SPM. **Confidence: High** on the structure and on the audit-redaction rule; the specific
> defaults are a matrix ceiling every tenant may change, and three cells need the owner's word — **OQ-2**.
>
> This is the most sensitive data the product will ever hold. The default in every ambiguous cell is **no**.

#### 4.5.1 Three feature codes, no sub-flags

`CLAUDE.md` forbids per-feature sub-flags inside routes and requires every feature route to be gated by
`@require_feature_access`. Everything below is expressed in that one mechanism. Three codes, all registered in
**all four places** (`setup_db.py`, a numbered migration, **`database/seed_rbac.sql`**, and default
`role_feature_access` rows in both the migration and the seed — the DEF-004 lesson):

| Code | Label | Governs | Seeded `role_feature_access` defaults |
|---|---|---|---|
| `compensation` | Compensation | Viewing **other people's** pay in scope, entering and proposing pay, bands, backfill, history | `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w+d · `SOLID_LINE_MANAGER` **r** (scoped — see 4.5.3) · all others none |
| `compensation_self` | My Pay | The **"My Pay"** panel on your own profile, hard-scoped to yourself | `EMPLOYEE` r · every other role r (everyone is also an employee) |
| `pay_equity` | Pay Equity | The equity queue, flags and their disposition | `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w · all others none |

**Why `compensation_self` is its own code rather than a setting.** Self-view must be switchable per tenant (some
companies deliberately keep pay in payroll and out of the HR portal) and must **not** be an accidental casualty of
an admin narrowing the `compensation` matrix — an admin tightening who can see *other people's* pay should not
silently blind every employee to their own. A separate feature code gives the tenant that switch through the
mechanism that already exists, adds no new flag, and keeps `CLAUDE.md` intact. SYSTEM_ADMIN bypasses all three
automatically; no EP42 code re-implements that.

#### 4.5.2 The visibility matrix — defaults

Read as: *what this role can see **by default**, before the tenant changes anything.* Every cell is a ceiling a
PORTAL_ADMIN may widen or narrow through the existing Feature Access tab, and the implementation must respect that
with **no extra checks** in the route.

| Role | Own pay | Direct (solid-line) reports | Indirect / whole subtree | Dotted-line reports | Their department or location | Company-wide | Propose a pay change | Be a chain approver on a money request | Configure levels / bands / thresholds |
|---|---|---|---|---|---|---|---|---|---|
| **EMPLOYEE** | **Yes** (`compensation_self`) | – | – | – | – | – | No | – | No |
| **SOLID_LINE_MANAGER** | Yes | **Yes** | **No** | **No** | – | – | **Yes** (initiates the request) | Yes, if granted `compensation` r | No |
| **DOTTED_LINE_MANAGER** | Yes | – | – | **No** | – | – | No | Only if granted | No |
| **DEPARTMENT_HEAD** | Yes | – | – | – | **No** | – | No | Only if granted | No |
| **LOCATION_HEAD** | Yes | – | – | – | **No** | – | No | Only if granted | No |
| **HIRING_MANAGER** | Yes | – | – | – | – | – | No | No | No |
| **HR_ADMIN** | Yes | – | – | – | – | **Yes (r+w)** | Yes | Yes | Yes |
| **COMPANY_ADMIN** | Yes | – | – | – | – | **No** by default | No | Only if granted | No |
| **PORTAL_ADMIN** | Yes | – | – | – | – | **Yes (r+w+d)** | Yes | Yes | Yes |
| **SYSTEM_ADMIN** | n/a | – | – | – | – | **Bypass, all tenants** | Yes | Yes | Yes |

**The three calls worth defending:**

1. **A solid-line manager sees their direct reports' pay — one level down, not the subtree.** They need it: they
   are the person who initiates a transfer or promotion and therefore the person making the pay proposal. They do
   not need the skip-level view: a director seeing forty salaries by default is a leak by default, and the manager
   who needs it can be granted it. *Needs the owner's word — OQ-2(a).*
2. **Department and location heads default to no.** They are org-structure roles, not pay roles; nothing in their
   job-to-be-done requires an amount. A tenant that disagrees grants it in one click.
3. **`COMPANY_ADMIN` defaults to no.** It is an administrative role, and administrative reach is not a reason to
   see pay. This will surprise someone; it should.

#### 4.5.3 Row scoping is a service rule, and it is **not** the forbidden sub-flag

**This distinction must be written into the Architect's ADR and the BA's criteria, or an engineer will read CC-2
and conclude that scoping is banned.**

- The **feature flag** answers *"may this role reach this surface at all?"* — `@require_feature_access('compensation')`.
- The **row scope** answers *"which rows does the surface return for this user?"* — a manager with
  `compensation:r` gets their `direct_report_ids()`; an HR_ADMIN with `compensation:r` gets the company.

The forbidden pattern (`enabled_for_hr`, `_si_enabled_for_hr`) is a check that **denied a granted role access to a
feature**. A row scope does not deny access to the feature; it determines the result set — exactly what company
scoping already does on every query in the product. **Rule: scoping never narrows below what the matrix grants for
that role's defined scope, and there is never a per-feature role check inside a route.**

**Every scoped read must return `403` or an empty set on the server**, never a full payload filtered in the
browser. See R-3.

#### 4.5.4 Read, write and approve are separable

| Action | Meaning | Default holders |
|---|---|---|
| `r` | See amounts within your scope | HR_ADMIN, PORTAL_ADMIN, SOLID_LINE_MANAGER (scoped) |
| `w` | Enter or propose a compensation record; run a backfill; edit bands and levels | HR_ADMIN, PORTAL_ADMIN |
| `d` | Void or correct a **historical** compensation record — destructive, because history is the defensibility | **PORTAL_ADMIN only** |
| *(approve)* | **Not a compensation permission.** Approving is the org-change chain's job. A step on a money-bearing request additionally requires `compensation:r` (D4b) | per the chain |

`r` without `w` is a real and useful configuration (an auditor, a works-council representative in some tenants),
and every mutating endpoint returns `403` with **no state change** for a holder of `r` only.

#### 4.5.5 Self-view

"**My Pay**" on the employee's own profile, gated by `compensation_self` and hard-scoped to
`employee_id = session.employee_id` **server-side** — the scope is never taken from a request parameter. It shows:
current base, currency, FTE, effective date, level and step, level title, and — once bands exist — position in
range as a plain-language statement, not a raw compa-ratio number. It shows history if the tenant enables it
(default: current only). It shows **no comparison to anybody else**, ever, and **no forward-looking language**
that could be read as a promise. UX owns the wording; it is the most easily misread copy in the epic.

#### 4.5.6 Salary values and the audit log — **redacted, and enforced in code**

**Rule: a monetary amount is never written into an `audit_log` diff, metadata or reason.**

**Evidence for the rule, not preference:**
- The `audit_log` read audience is defined by a **different feature code** (`audit_log`, default PORTAL_ADMIN +
  HR_ADMIN — S10) than the compensation audience. In a tenant that narrows `compensation` to two people but leaves
  `audit_log` at its default, a salary in an audit diff is readable by people the tenant deliberately excluded.
  Access control that can be routed around by a second feature is not access control.
- `audit_log` is **append-only, enforced by a DB trigger on UPDATE** (KAN-187). A pay figure written there cannot
  be un-written. Its `retention_class` outlives employment.
- The existing guard proves the mechanism and the gap: `_check_no_secrets()` refuses keys containing
  `password`, `token`, `secret`… — **and nothing in that list catches a salary** (S9). Today a salary diff would
  be written verbatim, by accident, by the first engineer who does the obvious thing.

**What a compensation change writes instead:**

| Where | What |
|---|---|
| **`audit_log`** | *That* pay changed, never *what to*. Diff carries **non-monetary facts only**: `has_change`, `direction` (`INCREASE`/`DECREASE`/`NONE`), `pct_change_band` (a coarse bucket — `0-5`, `5-10`, `10-20`, `20+`), `currency`, `effective_date`, `level_from`/`level_to`, `step_from`/`step_to`. `entity_id` is the **compensation record id**. Plus actor, mandatory reason, correlation id — unchanged from KAN-187 |
| **The compensation history table** | The amounts. **Append-only, effective-dated**, each row carrying actor, reason and the **same `correlation_id`** as the audit row, so the two join into one story. Gated by `compensation:r`. This is the source of truth for "from what to what" |

**Enforcement, so this cannot rot:** add a **`_MONEYISH_KEYS`** guard to `audit_service` beside `_SECRETISH_KEYS`
— `salary`, `pay`, `compensation`, `amount`, `wage`, `remuneration`, `base_pay`, `annual_base` — matched the same
way, raising `AuditError`. A future engineer who writes an amount into a diff gets a test failure, not a leak.
`audit_service` is the **Architect's** file: this is a requirement, and **CFL-42-2** routes it to him for sign-off,
together with the new `ACTIONS` entries (`COMPENSATION_RECORDED`, `COMPENSATION_CHANGED`, `COMPENSATION_VOIDED`,
`JOB_LEVEL_ASSIGNED`, `JOB_LEVEL_CHANGED`, `STEP_ADVANCED`, `PROMOTION_APPLIED`, `PAY_BAND_CHANGED`,
`PAY_EQUITY_FLAG_RAISED`, `PAY_EQUITY_FLAG_DISPOSITIONED`, `PAY_EQUITY_THRESHOLD_CHANGED`) — the enumeration is
deliberately frozen and extending it is his edit (S8).

**Trade-off accepted and named.** Someone reading only the audit log cannot see the old and new amounts. That is
the point. Defensibility is preserved because the audit row points at an immutable, effective-dated compensation
record that carries them, and the correlation id ties them together. If the DPO or a tenant's auditor rejects this
split, the fallback is amounts in the audit log **with `audit_log` read narrowed to `compensation:r` holders** —
worse, because it couples two features' permission models. Recorded so the trade-off is visible, not so it is
re-litigated casually.

#### 4.5.7 The surfaces where a salary must **not** appear — checked, not assumed

Enumerated because leaks happen at the edges, not in the feature. Every one is a UAT assertion (§8.4):

notification bodies and the bell · email templates (`app/services/notification_service.py` dispatch) ·
`employee_search_index` and the `trg_employee_search` trigger (S12) · the org tree, directory and any card or
tooltip · analytics and reporting exports · the org-change request summary line (`ocSummary()` in
`templates/base.html:630-637`) · CSV exports of any kind · application logs and error messages (EP38 CC-17's bar:
nothing beyond employee id and employee number) · the audit log (4.5.6) · any JSON payload returned to a client
that lacks `compensation:r` — **absent from the payload, not hidden by CSS or by a template condition.**

### 4.6 D6 — R7, the per-company exposure switch: fix it centrally, ahead of everything else

> **Owner of the call:** SPM makes the product call; **the Architect owns the technical one** and I am handing it
> to him explicitly. **Confidence: High.**

#### 4.6.1 The decision

**KAN-188: `company_features.is_enabled` becomes part of the central feature-access resolution, applied uniformly
to every feature, sequenced in W0 ahead of every compensation story.** EP42 does **not** hand-roll a third
per-blueprint check.

#### 4.6.2 Why — the product argument

**Observation.** R7 is a **commercial control**: the product owner decides which tenant gets this capability.
**Evidence.** That control is currently honoured by exactly two blueprints that remember to ask
(`app/routes/analytics.py:20-40`, `app/routes/skills_intelligence.py:21`), while the central resolver
(`app/auth.py:38-95`) does not consult `company_features` at all — verified by repo-wide grep (S5).
**Impact.** A control that depends on each feature author remembering it is a convention, not a control. Until
now the cost of a miss was a tenant seeing an analytics page they had not bought. After EP42 the cost of the same
miss is a tenant seeing **salaries** — and there will be a dozen new endpoints, written by more than one person,
each of which would need the check copied correctly.
**Recommendation.** Fix it once, centrally, before the first compensation route exists.
**Expected outcome.** Every feature — the eleven that exist and the three EP42 adds — gets the tenant switch for
free, and R7 is delivered by construction rather than by diligence.

**The precedent is exact.** KAN-187 (audit) was sequenced ahead of KAN-184 precisely so that EP35 and EP39 would
not each invent an audit trail. That call was right and it paid. This is the same call about the same kind of
capability, and the argument against it is the same argument that was made and rejected then.

**Cost comparison, stated plainly.** The central fix is one bounded, one-off change to a resolver that already
exists, plus a backfill migration. The third copy is cheaper this week and permanent thereafter: it grows by one
copy per feature forever, and each copy is a place the control can be forgotten.

#### 4.6.3 The product requirements on KAN-188 (the Architect decides *how*)

1. **Effective access = tenant switch AND role grant.** A feature is reachable only if `company_features.is_enabled`
   is true for the tenant **and** the role matrix grants it. Both, one resolution point.
2. **Default for an absent row.** **Enabled** for the eleven existing features — KAN-188 must change nothing for
   any existing feature or tenant, and that is an acceptance criterion. **Disabled** for the three EP42 codes, so
   R7's default posture is *hidden until the owner exposes it* (and, per D8, so compensation is off by default).
3. **SYSTEM_ADMIN bypass is preserved, and made visible rather than silent.** A SYSTEM_ADMIN working in a company
   context where the feature is off sees an unmistakable "disabled for this tenant" state, not a normal screen.
   Bypassing a switch without knowing you are bypassing it is how a demo shows a customer a feature they do not
   have.
4. **One resolution point serves nav and routes.** `has_feature_access()` in templates and
   `@require_feature_access()` on routes must give the same answer from the same place. Two implementations will
   diverge; they always do.
5. **The off state is a real screen**, following the `analytics_locked.html` precedent — a plain explanation and
   nothing actionable. Not a 403, not a redirect to the dashboard, not a blank page.
6. **Toggling the switch takes effect on the next request** for every user of that tenant. `g._feature_access` is
   per-request, so this should be free — the Architect confirms it.
7. **Every toggle is audited** (`company_id`, feature, old→new, actor, reason).
8. **The two existing ad hoc consumers are retro-fitted** onto the central mechanism as part of this story —
   otherwise we have three implementations instead of two and the story has made things worse.
9. **`enabled_for_hr` is deprecated in place.** No new consumer, ever; EP42 must not read or write it. Its removal
   changes behaviour for an existing feature, so it is **not** in KAN-188's Must — but the Architect names a
   removal path in the ADR, and `CLAUDE.md` already forbids the pattern by name.

#### 4.6.4 Handed to the Architect (CFL-42-1)

Where the AND is applied (inside `_load_feature_access()` versus a wrapper); the shape of the backfill migration
that materialises `company_features` rows for existing tenant/feature pairs without changing any current
behaviour; whether `has_feature_access()`'s signature changes; per-request caching; and the removal path for
`enabled_for_hr`. **His ADR gates the start of W1.**

### 4.7 D7 — Backfill (R2), and what the product does while data is partial

> **Owner of the call:** SPM. **Confidence: High.** The partial-data behaviour matters more than the import
> mechanism and gets more space accordingly.

#### 4.7.1 Both mechanisms, in a defined order

**Bulk import first, manual entry always available.**

- **Bulk (KAN-195, Must).** A compensation CSV — `employee_number, effective_from, currency, annual_base, fte,
  pay_basis, reason` — with the **dry-run → diff → commit** shape EP35-S2 already defines: upload, column-map,
  preview showing create/update/error per row, then a single atomic commit (KAN-155). **Reuse the existing Bulk
  Import surface; do not fork a second importer.** If EP35-S2 has not landed when KAN-195 starts, ship the minimal
  importer against the same contract and refactor onto the wizard — flagged as a sequencing risk (§7, R-9).
  Rejections are row-level and reported, never silent; a file that would set a salary to null or zero is rejected
  at preview.
- **Manual (KAN-195, Must).** Single-employee entry from the profile, gated `compensation:w`. Every tenant will
  need to fix one row without re-uploading a file, and an import-only design guarantees shadow spreadsheets.
- **Volume, corrected:** **146 employees across two populated tenants** (Acme 46, Telia 100), not "147 Acme" — S1.

**The level backfill is the harder half and is a separate story (KAN-191).** Mapping 41 + 75 free-text titles onto
a ladder is a **data project the tenant owns**, not a story detail — see risk R-2. It gets a mapping screen
(distinct titles listed with counts, assign a level to each, bulk-apply) and a CSV round-trip, because someone
will want to do it in a spreadsheet with the HR director.

#### 4.7.2 Behaviour while data is partial — the part that determines whether this is trusted

1. **An employee with no compensation record shows "No salary recorded" and a "Record salary" action** to a
   `compensation:r` holder. **Never** a blank, a dash, a zero, or a hyphen. An absent value must never be able to
   look like a value. (This is `CLAUDE.md`'s empty-state rule generalised — a company with no custom roles shows an
   empty state, not global defaults; same principle, higher stakes.)
2. **Employees with no record are excluded from every equity computation, and the exclusion is counted and
   shown.** Each group displays `n compared / m in group` and a **coverage percentage**.
3. **A group below the coverage gate is not evaluated at all.** Default **80%**, company-configurable 50–100%.
   Below it the group reports **"insufficient coverage — not evaluated"** and produces **zero flags**.
   *Why this is a hard rule:* an equity finding computed on half a group is not a weak signal, it is a **wrong**
   one, and wrong in a direction nobody can predict — the missing half could be the entire explanation. The first
   wrong flag is the one that ends the feature's credibility, and credibility does not come back.
4. **Equity is disabled for a company until coverage crosses the gate at least once.** Until then the queue shows
   the **coverage meter and the missing list**, not an empty "no findings" state. "No findings" at 40% coverage
   reads as "we are fine", and that is the most dangerous screen we could ship.
5. **A company-level coverage meter** — "Compensation data: 62% of active employees (91 of 146)" — sits on the
   compensation landing page with the missing list exportable to CSV. This is the adoption instrument: it is the
   thing that makes a backfill actually finish, and it is why the time-to-value measure in §1.5 is achievable.
6. **Never derive, estimate or impute a salary** — not from the band, not from the level, not from the group
   median. An imputed figure that reaches a screen or an export is indistinguishable from a real one.
7. **Contractors and interns** show "Not applicable — <employment type>" rather than "No salary recorded". They
   are excluded by design, not missing, and conflating the two makes the coverage meter lie.

### 4.8 D8 — Does EP42 trip trigger T2?

> **Owner of the call:** SPM. **Confidence: High.** I am not ducking it, and I am not manufacturing a P0 to look
> careful.

#### 4.8.1 The answer: **No — and D-004's sequencing stands unchanged.**

T2 reads *"any real employee PII is loaded (replacing the synthetic seed data)"*. Building a compensation feature
and populating it with synthetic salaries for synthetic people does not load real PII. **T2 is not tripped, EP42
builds in S3, and the security phase stays in S5.** The deferral's core premise — the environment is demo-grade,
on synthetic data, on localhost, so the email-only session is a gate item and not a live incident — is about
**exposure**, and EP42 does not change exposure.

I could construct an argument that it does. It would be wrong, it would burn the credibility of the trigger
mechanism, and the next time I say something is a P0 nobody would believe me.

#### 4.8.2 What *does* change: the loss, not the probability

The trigger set T1–T4 was written when the worst case of a trigger event was the exposure of names, org placement,
skills and leave dates. After EP42 the worst case of the **same** event is the exposure of **every employee's
pay** — the data class that produces individual grievance, works-council escalation and press attention rather
than a breach notification and an apology. Same likelihood, materially larger loss.

**A risk register that does not re-price when the asset changes is decorative.** So:

#### 4.8.3 Three actions, taken now

**1. Add trigger T5 to the roadmap amendment.** *(The roadmap is my document — Charter §5b. I am recording the
decision here in Wave 1 and will apply it to `PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` in Wave 3, in the same
commit as the backlog update.)*

| # | Trigger | Because |
|---|---|---|
| **T5** | **Any real (non-synthetic) compensation value is entered for any employee, in any tenant — including a single manual entry by the build team "just to see how it looks".** | A single real salary is more consequential than an entire synthetic directory. This fires at a **deliberately lower bar than T2**: T2 needs a data *load*, T5 needs **one row**. |

T5 fires **S5 immediately**, on the same no-discussion terms as T1–T4. It also needs the standing owner assigned
under roadmap Q6 — the same person who owns "the environment stays demo-grade".

**2. Two cheap safeguards inside EP42's own build**, in force from KAN-194 onward. Same logic as D-004's existing
"cheap safeguards that stay in force": they cost nothing and do not churn with features.
- **Compensation and pay_equity are seeded `is_enabled = FALSE` for every existing tenant** (D6 requirement 2).
  R7 does double duty as a safety default: the capability is off until the owner deliberately turns it on.
- **A persistent "Demo compensation data — synthetic" banner** on every compensation screen while the environment
  is demo-grade, so no one — including us — mistakes seeded figures for real ones. Removed by the same change that
  clears T5's precondition.

**3. The disclosure that must be said out loud, not discovered.** Under demo auth, **the D5 visibility matrix is
correct in code and unenforceable in practice** — anyone can assume any identity from the login tiles. Every
compensation demo states this at the start (Demo Readiness Gate rule 5: if a known limitation is carried in, say
so), and it goes in the written demo script, not in the answer to a stakeholder's question. The gate verdict for
any compensation demo is **CONDITIONAL** on that disclosure being in the script.

#### 4.8.4 The consequence the product owner should hear now

**The first time he wants to show this to a named prospect using their own pay figures, or load one real payroll
extract, S5 runs first.** That is not a new rule — it is T3 and T5 applied to the feature he has just asked for.
It is much better heard now, while it is a sequencing fact, than at the point where it looks like an obstruction.
Recorded as an acknowledgement in §6, not as a question.

---

## 5. Story breakdown — KAN-188 … KAN-202

> **Numbering.** KAN-187 is the highest ID in use (`docs/project-management/BACKLOG.md`, EP38). EP42 continues at
> **KAN-188** and runs to **KAN-202**. Plain text, never links. Nothing existing is renumbered. **Stories are
> numbered in build order**, so the ID sequence *is* the sequence.
>
> **Acceptance criteria below are backlog-level summaries.** The BA expands each into numbered, individually
> testable criteria (`AC-<story>-<nn>`) in Wave 2, to the depth of
> `EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`. Where the two differ, the BA's file is authoritative for detail
> and this table for scope.
>
> **Status marker for all fifteen: ⬜ Planned.** Nothing here has started.

### 5.1 W0 — Platform enablers (stage **S2**)

| Story ID | User story | Backlog-level acceptance criteria | MoSCoW · P | Depends on |
|---|---|---|---|---|
| **KAN-188** | As the **product owner**, I want to expose or hide a feature for one company without hiding it for another, and have that honoured everywhere, so I can package the product per tenant. (R7 · D6) | `company_features.is_enabled` is consulted by the **single central** access resolution; effective access = tenant switch **AND** role grant; absent row defaults **enabled** for the eleven existing features (no behaviour change for any existing feature or tenant — asserted) and **disabled** for the three EP42 codes; nav (`has_feature_access`) and routes (`@require_feature_access`) resolve from the same place; the off state is a real explanatory screen following the `analytics_locked.html` precedent, never a 403 or redirect; SYSTEM_ADMIN bypass preserved **and visibly signposted**; `reports` and `skills_intelligence` retro-fitted off their hand-rolled checks; every toggle audited; `enabled_for_hr` gains no new consumer and its removal path is named in the ADR. | **Must · P1** | Architect ADR (CFL-42-1) |
| **KAN-189** | As **HR**, I want a position change to carry the date it takes effect, so placement and pay move on the same day and history is not fudged. (D4d · resolves **CFL-4** and unblocks **AC-185-07** on KAN-185) | `effective_date` added to `org_change_requests` and to `create_request()`; the field is rendered in the shared move modal (it is deliberately absent today rather than silently discarded); `_apply_change` uses it as the boundary for closing the outgoing assignment and opening the incoming one; **after any applied change there is exactly one current assignment and no overlapping day** (asserted by direct DB query); the column is designed so a **divergent pay effective date** can be added later without changing the meaning of this one; back/forward-dating windows are company-configurable; a future-dated *placement* remains rejected while there is no scheduler (EP38 R5.6). | **Must · P1** | KAN-155 · KAN-166 · Architect's overlap convention (CFL-4) |

### 5.2 W1 — Job architecture (stage **S3**) — R6

| Story ID | User story | Backlog-level acceptance criteria | MoSCoW · P | Depends on |
|---|---|---|---|---|
| **KAN-190** | As a **customer admin**, I want to define my own job families, levels and steps with our own titles, so the ladder matches how we actually organise work. (R6 · D3) | Company-scoped job families; ordinal levels within a family, each carrying **its own title**; steps within a level with a **configurable count, default 5, range 1–12**, displayed `<level>.<step>`; levels reorderable before they are in use and **immutable in ordinal position once assignments exist** (renaming stays allowed); a company with no ladder shows an **explicit empty state** and never another company's or a global default's levels; all queries `company_id = %s::uuid` only; gated `@require_feature_access('compensation','w')`; every configuration change audited; WCAG 2.2 AA. | **Must · P1** | KAN-188 · KAN-166 |
| **KAN-191** | As **HR**, I want every existing employee placed on a level and step, so comparisons and promotions have something to stand on. (R6 · R2 · D7) | Effective-dated assignment of an employee to a (family, level, step); a **mapping screen** listing every distinct free-text `job_title` in the company with its headcount, allowing a level to be assigned per title and bulk-applied, plus a **CSV round-trip**; `employees.job_title` is **not** dropped or repurposed — it is relabelled "Working title" (S12, CFL-42-4); a **coverage meter** shows % of ACTIVE employees on a level with the remainder exportable; unassigned employees are excluded from every comparison and **counted, never silently dropped**; company-scoped; audited. | **Must · P1** | KAN-190 |
| **KAN-192** | As a **manager or HR admin**, I want step advancement and level promotion to be explicit, recorded decisions, so nobody is promoted by side-effect. (R6 · **D3** — the roll-up call) | Step advancement is an explicit audited action; **no automatic roll-up** on reaching the last step — instead a `promotion_eligible` signal to the solid-line manager and `compensation:w` holders, worded as a signal with **no implied promise**; promotion between levels happens **only** through a `PROMOTION` request (KAN-197); **skip-step, skip-level and downward moves are all permitted with a mandatory reason** and full audit; every transition writes level/step before→after to the audit trail (no amounts — D5); the eligibility notification specifies section, icon, action and retirement per D2's checklist. | **Must · P1** | KAN-191 · KAN-197 (for the promotion path) |

### 5.3 W2 — The compensation record (stage **S3**) — R1, R2

| Story ID | User story | Backlog-level acceptance criteria | MoSCoW · P | Depends on |
|---|---|---|---|---|
| **KAN-193** | As **HR**, I want the product to hold an effective-dated salary for an employee, so pay is a governed record rather than a spreadsheet. (**R1** — the spine of the epic) | **Append-only, effective-dated** compensation history per employee: annual base amount, **currency**, **FTE**, pay basis (annual/monthly/hourly with company standard annual hours), `effective_from`, actor, mandatory reason, correlation id; exactly one current record per employee per date; **no UPDATE and no DELETE path** — a correction is a new record, a void is a marked record (`compensation:d`); written inside the caller's `transaction()` (KAN-155) with its `audit_log` row (D5.6, amounts excluded); company-scoped; `employment_type` recorded on the record so contractor/intern exclusion is stable over time. | **Must · P1** | KAN-188 · KAN-155 · KAN-166 · KAN-187 (extended) |
| **KAN-194** | As an **employee, manager and HR admin**, I want to see exactly the pay I am entitled to see and nothing else, so the most sensitive data in the product is safe by default. (**D5**) | Three feature codes registered in **all four places** (`setup_db.py`, migration, **`seed_rbac.sql`**, default `role_feature_access` in both) — `compensation`, `compensation_self`, `pay_equity`; the §4.5.2 default matrix seeded as a ceiling a tenant may widen or narrow with **no extra checks in any route**; **row scoping in the service layer** (manager → direct reports only) with the CC-2 distinction documented; **"My Pay"** on the employee's own profile, server-scoped to `session.employee_id`, never from a parameter; `r`/`w`/`d` separable, `w`-less holders get `403` with **no state change**; **`_MONEYISH_KEYS` guard added to `audit_service`**; an amount is **absent from the JSON payload** — not hidden in the DOM — for every role lacking scope, asserted across every surface in §4.5.7. | **Must · P1** — *nothing may render a salary before this lands* | KAN-193 · Architect sign-off (CFL-42-2) |
| **KAN-195** | As **HR**, I want to load our existing salaries in bulk and fix individual rows by hand, so we can get to usable coverage in days rather than a quarter. (**R2** · D7) | CSV import with **dry-run → diff → commit** reusing the EP35-S2 surface (not a second importer); row-level error reporting; a file that would write null or zero over an existing salary is **rejected at preview**; atomic per batch (KAN-155); single-employee manual entry gated `compensation:w`; **"No salary recorded"** empty state with a "Record salary" action — never a blank, dash or zero; contractors/interns show "Not applicable"; a **company coverage meter** with the missing list exportable; **no derived, estimated or imputed salary anywhere, ever**; every import run audited with the row counts and the actor. | **Must · P1** | KAN-193 · KAN-194 · *(soft)* EP35-S2 |

### 5.4 W3 — Coupling to the workflows (stage **S3**) — R3, R4

| Story ID | User story | Backlog-level acceptance criteria | MoSCoW · P | Depends on |
|---|---|---|---|---|
| **KAN-196** | As a **manager or HR admin**, I want a position change to carry its pay decision through the same approval, so a move is never applied with the pay question unanswered. (**R3** · D4) | The compensation block lives **inside** the shared `templates/org_change/_move_modal.html` — one modal, one endpoint, one engine, three entry points (drop, profile, directory `⋯`); the pay decision is **mandatory to answer, not mandatory to change** — *No change · New salary · Defer (reason required)*, **nothing pre-selected**; a money-bearing request is **refused at create time** if any chain step has no approver holding `compensation:r`, naming the step, writing nothing; **the apply never writes null or zero over an existing salary** (D-185-1 pattern) with a named regression test covering pay-only, placement-only, level-only, full and no-prior-record proposals; the block is **absent** (not disabled) for a user without `compensation:r`, and the request they raise is a placement-only `TRANSFER`; placement and pay share the KAN-189 effective date; nothing applied until final approval, any rejection applies nothing. | **Must · P1** | KAN-189 · KAN-193 · KAN-194 · KAN-155 |
| **KAN-197** | As **HR**, I want promotion to be a first-class request with a salary review that cannot be skipped, so a promotion never quietly happens without a pay decision. (**R4** · D4e · closes backlog open item #3 / EP38 OQ-1) | `request_type` ∈ `TRANSFER` · `PROMOTION` · `COMPENSATION_REVIEW` added to `org_change_requests`, defaulting every existing row to `TRANSFER`; all three run on the **existing** engine and chain — no second engine; a `PROMOTION` proposes a new (family, level, step) and may also change placement; **"no change" on a promotion requires an explicit recorded reason**; a company may configure a **different chain per request type**, falling back to the `TRANSFER` chain so no request ever runs with no chain; the KAN-139 rule holds for every type — **an employee can never initiate their own**; type is inferred from what changed in the shared modal (D4f); applied atomically with the level/step assignment and the compensation record. | **Must · P1** | KAN-196 · KAN-191 |
| **KAN-198** | As a **compliance owner**, I want two different people to be required on any approval chain that moves money, so a two-level control is not one person twice. (D4h · closes backlog open item #5) | For any request carrying a **compensation or level** change: a user who has decided one level **cannot** decide another on the same request — refused with a message naming the level they already decided; **not configurable, not overridable**; for **placement-only** requests: warn, allow, and record it in `audit_log` as a self-approval; the approval-chain admin page **shows the overlap at configuration time** ("levels 1 and 2 can both be satisfied by the same person"); behaviour change applies to EP27 and EP38 as well as EP42 and both regression suites are extended. | **Must · P1** | KAN-196 · Architect sign-off (CFL-42-5) · **owner ratification OQ-9** |

### 5.5 W4 — Pay equity (stage **S3**) — R5

| Story ID | User story | Backlog-level acceptance criteria | MoSCoW · P | Depends on |
|---|---|---|---|---|
| **KAN-199** | As a **customer admin**, I want salary bands for each level in each pay market, so pay decisions have an intended range and not just an average. (D3.5 · D1 basis) | A band is `(job_level, pay_market) → min, midpoint, max, currency, effective_from`; **pay market** is a company-defined grouping of locations defaulting to **one per `locations.country`**; an optional **target point** (percentile) per step, as guidance only; **compa-ratio** computed and displayed to `compensation:r` holders; **out-of-band pay is allowed, flagged and requires a reason — never hard-blocked**; a merged multi-currency pay market is **refused** unless an effective-dated FX rate exists for every currency in it, with **no silent 1:1**; every band change audited. | **Should · P2** | KAN-191 · KAN-193 |
| **KAN-200** | As **HR**, I want the system to tell me where pay in the same job and market is out of line, so I find it before an employee or a regulator does. (**R5** · D1) | Comparison group = `(company, job_family, job_level, pay_market)` — **never `job_title`, never step**; basis = **compa-ratio to band midpoint where a band exists, else the group median** — **never pairwise**; compared value = **FTE-normalised annualised base**, contractors and interns excluded and the exclusion counted; **Check A** individual outlier (default flag below 0.95 / above 1.10 compa-ratio, **n ≥ 3**); **Check B** group **gender pay gap** (default **≥ 5%**, **n ≥ 5** and ≥ 2 of each gender compared); below the minimum → **"insufficient comparison group", never a flag**; **coverage gate** default 80% → **"insufficient coverage — not evaluated", zero flags**; equity disabled for a company until coverage crosses the gate once; **all thresholds, group minimums, the coverage gate and the pay-market definition are per-company configurable by PORTAL_ADMIN only, every change audited**; evaluation is **event-driven plus an on-demand "Run equity check"** — **no batch** (no scheduler, S16); every screen carries plain-language framing that this is a **measurement, not a compliance conclusion**. | **Must · P1** | KAN-191 · KAN-193 · KAN-199 · KAN-168 |
| **KAN-201** | As the **pay-equity responsible**, I want each finding to reach me, stay in one place until I have dealt with it, and then go away, so the queue is worth working. (**R5** delivery · **D2**) | Recipients = holders of `pay_equity` read in that company **plus** an optional per-company named escalation list which **adds recipients and can never remove access** (not a sub-flag); primary surface is a **queue** at `/compensation/equity` with filters and per-flag disposition; **bell: a new "Pay Equity" section, feature-gated `has_feature_access('pay_equity')`, hidden when empty, icon ⚖️ in `NOTIF_ICON` (never ❌), counted in the badge, one quick action "Review →" deep-linking to the filtered queue — no dispose-from-the-bell**; **notification bodies contain no amount and no invertible percentage**; lifecycle `OPEN → JUSTIFIED / REMEDIATION_PLANNED / RESOLVED / RESOLVED_BY_DATA` with a **mandatory reason on every disposition** and a category on `JUSTIFIED`; **retires via `resolve_related()` on disposition, for every eligible recipient — not on read** (DEF-003); **a `JUSTIFIED` flag does not re-fire** within its validity window (default 12 months) unless the gap widens beyond threshold + 2pp, the subject's level/step/salary changes, or the configuration changes; no bulk disposition. | **Must · P1** | KAN-200 |
| **KAN-202** | As **HR or a compliance owner**, I want to see how someone's pay got to where it is, without pay amounts leaking into the audit trail. (D5.6) | A per-employee **compensation timeline** (effective date, amount, currency, FTE, level/step, actor, reason), gated `compensation:r` and row-scoped; joined to the `audit_log` rows by **`correlation_id`** so the two read as one story; `audit_log` diffs carry **no amounts** — `has_change`, `direction`, `pct_change_band`, `currency`, `effective_date`, level/step before→after only; the new `ACTIONS` codes registered in `audit_service`; `_MONEYISH_KEYS` enforced with a test that proves an amount is refused; the timeline is a **compensation** surface, not an `audit_log` surface, and holding `audit_log:r` alone never reveals an amount. | **Should · P2** | KAN-193 · KAN-194 · SPM decision on the audit read surface (backlog open item #1) |

### 5.6 Build order, and why it is this order

```
S2   KAN-188 ──► KAN-189                                    platform; KAN-189 also unblocks KAN-185
        │           │
S3      ▼           │
     KAN-190 ──► KAN-191 ──────────────┐                    the ladder, then everyone on it
        │                              │
        ▼                              ▼
     KAN-193 ──► KAN-194 ──► KAN-195   │                    the record, then who sees it, then the data
                    │                  │
                    ▼                  ▼
                 KAN-196 ──► KAN-197 ──► KAN-192            pay in the flow; promotion; progression
                    │
                    ▼
                 KAN-198                                    four-eyes on money
                    │
                    ▼
     KAN-199 ──► KAN-200 ──► KAN-201 ──► KAN-202            bands, engine, delivery, history
```

**The five sequencing arguments:**

1. **KAN-188 before anything that renders a salary.** If the tenant switch is not central before the first
   compensation route exists, R7 is delivered by each engineer remembering — and the first one who forgets exposes
   pay to a tenant that did not buy it. This is the KAN-187 precedent applied to the same class of problem (D6).
2. **KAN-189 in S2, ahead of its own wave.** It unblocks `AC-185-07` on KAN-185, which is **stuck today**. There is
   no reason to hold a fix for an in-flight story behind an epic that has not started.
3. **The ladder (W1) before the record (W2), and both before equity (W4).** R5 has no grouping key without R6 —
   measured, not asserted (S2). Building the equity engine first would mean building it against `job_title` and
   rewriting it, which is the most expensive possible order.
4. **KAN-194 immediately after KAN-193, never later.** The record and the permission model ship together. A
   compensation record that exists for even one release without an enforced visibility model is a leak waiting for
   a route. This is why KAN-194 is P1 despite being "just permissions".
5. **KAN-192 (progression) after KAN-197 (promotion).** The promotion-eligible signal is pointless until there is
   a promotion request to act on it. Building the signal first ships a notification with a dead end — precisely
   the DEF-001/DEF-003 failure mode.

**Deliverable value at each wave boundary** *(the "could we stop here?" test)*:
- **After W1** — the tenant has a job architecture and every employee is on it. Useful on its own for org design
  and reporting, even with no pay data.
- **After W2** — pay is in the product, visible to the right people, backfilled. This is the **minimum shippable
  slice** and the one I would defend if the epic had to stop.
- **After W3** — position change and promotion are complete workflows. This is where R3 and R4 are satisfied.
- **After W4** — the equity question is answerable. This is the differentiator, and it is correctly last because
  it depends on all three.

### 5.7 Traceability — every ask lands in at least one story

| Ask | What the owner asked for | Stories | Decisions that shape it | Coverage |
|---|---|---|---|---|
| **R1** | Hold salary data at all | **KAN-193**, KAN-194, KAN-202 | D5 | **Full** |
| **R2** | Assign salary to existing employees (backfill) | **KAN-195**, KAN-191 (level backfill) | D7 | **Full** |
| **R3** | Any position change also considers a salary update | **KAN-196**, KAN-189 | D4a–d, D4f, D4g | **Full** |
| **R4** | Promotion triggers a salary review | **KAN-197**, KAN-192 | D3.4, D4e | **Full** |
| **R5** | Flag a >5% difference for the same position to the HR responsible | **KAN-200** (engine), **KAN-201** (delivery), KAN-199 (bands) | **D1**, **D2**, D7 | **Full**, with a **deliberate reinterpretation**: split into an individual-outlier check and a group gender-gap check (D1.2). **The owner should be told this explicitly** — OQ-3 |
| **R6** | Job levels with steps, per-company, each level with its own title | **KAN-190**, **KAN-191**, **KAN-192** | **D3** | **Full**, with **one open point** — the roll-up semantics, OQ-1 |
| **R7** | Product owner exposes/hides the feature per company | **KAN-188** | **D6** | **Full**, and delivered *centrally* rather than for this feature only — a deliberate widening, argued in D6 |

**Reverse check — every story traces to an ask.** KAN-188→R7 · KAN-189→R3 (enabler; also repays CFL-4) ·
KAN-190/191/192→R6 · KAN-193/194→R1 · KAN-195→R2 · KAN-196→R3 · KAN-197→R4 · KAN-198→R3/R4 (control on the
approval that carries them; also closes backlog open item #5) · KAN-199/200/201→R5 · KAN-202→R1 (the history and
audit half of holding the data). **No orphan stories.**

---

## 6. Open questions for the product owner

**Only questions that genuinely need *his* answer are here.** Everything else I have decided in §4. **Every row
carries a recommended default that the team builds against from today** — nobody waits, and if an answer comes back
different we change one decision, not the epic.

| # | Question | My recommended default *(build against this now)* | Why it needs **him**, not me | Cost if the answer arrives late | Blocks |
|---|---|---|---|---|---|
| **OQ-1** | **The roll-up.** "While employee reaches to 1.5, level 2 will be considered as…" — is reaching the last step of a level an **automatic** promotion, or a **signal** that a human then decides on? | **A signal. Promotion is an explicit human decision** through the approval chain, with a mandatory salary review (D3.4). | The two readings are different products with different compliance postures. I have a strong recommendation and clear reasoning, but this is his sentence and his intent — I will not infer a promotion mechanism from a fragment. | **Low if answered before KAN-192 starts; high after.** Automatic progression would need a rules engine and a trigger that does not exist. | KAN-192 |
| **OQ-2** | **The visibility matrix** (D5.2), specifically three cells: **(a)** does a solid-line manager see their direct reports' pay by default? **(b)** do department and location heads see pay for their area? **(c)** do employees see their own pay in this product at all? | **(a) Yes, direct reports only — not the subtree. (b) No. (c) Yes, via `compensation_self`, on by default and switchable per tenant.** | This is a company-policy question wearing a permissions costume. In some organisations a manager seeing their team's pay is normal; in others it is a works-council matter. He knows which customers he is selling to. | **Low** — all three are matrix defaults, changeable per tenant with no code change. Answering late costs a seed-data edit. | KAN-194 seed data only |
| **OQ-3** | **What "5%" means.** Is R5's 5% a **gender pay gap** within a comparison group (the regulatory shape — S13), a **raw dispersion** between individuals doing the same job, or both? | **Both, as two separate checks** — an individual outlier check for management action and a group gender-gap check carrying the 5% and the compliance meaning (D1). | I have deliberately reinterpreted his sentence to avoid an alert storm, and he should know I did. Reinterpreting a stakeholder's requirement silently is how a product ends up solving a problem nobody had. | **Medium.** Dropping Check B after KAN-200 is easy; adding it later means re-opening the engine and the grouping. | KAN-200 scope |
| **OQ-4** | **The example ladder.** In "Software Engineer level 1 … 1.5, then level 2 is Junior Software Engineer", was the naming illustrative, or is that specific ladder a requirement? | **Illustrative. The product ships a configurator and one worked example per seed tenant — no opinionated ladder** (D3.2). | If he means it literally, level 1 sits *below* "Junior", which inverts the usual convention and would confuse every customer who saw the default. Cheap to confirm, expensive to guess wrong in seed data. | **Very low** — it is seed data. | Seed data only |
| **OQ-5** | **Total compensation.** Are bonus, commission, equity, allowances or benefits in scope at any point in this epic? | **No. Base salary only, this cycle.** Everything else is Later (§3.4). | It roughly triples the data model, the import, the equity arithmetic and the visibility surface. If he needs it in the first release I need to know **now**, because it changes the shape of the compensation record, not just its contents. | **High.** Retrofitting variable pay into a base-only record and a base-only comparison is a rewrite of KAN-193 and KAN-200. | KAN-193 data model |
| **OQ-6** | **Currency.** Will any target tenant pay employees in more than one currency **within a single pay market**? | **No. One currency per pay market; cross-market comparison and FX are Later** (D1). | Determines whether an FX rate table is in this cycle. With one currency per market — the default, and true for both seeded tenants — it is not needed at all. | **Medium.** An FX table added later is additive; an equity engine written assuming single currency and then made multi-currency is not. | KAN-199, KAN-200 |
| **OQ-7** | **Default exposure.** Should the compensation capability default to **off** for the existing tenants, requiring him to switch it on per company? | **Yes, off by default** (D6 requirement 2, D8 safeguard). | It is his commercial control — R7 exists because he asked for it. Also a safety default (D8). | **Very low** — one seed value. | KAN-188 seed data |
| **OQ-8** | **Works councils and employee representatives.** Is any target tenant subject to co-determination on job classification or pay? The seed data spans Germany and four Nordic countries (S3). | **Assume yes for Germany and the Nordics.** Not a blocker to build; **a blocker to a real-data launch**, and it must be on the Customer-Readiness checklist. | Commercial and legal knowledge I do not have. **Flagged for legal/DPO validation — Charter §9.7.** | **Low for the build, high for the launch.** Discovering a consultation requirement during a customer rollout stops the rollout. | Customer-Readiness, not the build |
| **OQ-9** | **Segregation of duties** (backlog open item #5). Confirm the split: a **hard rule** — one person cannot decide two levels — for requests carrying money or a level change; **warn-and-audit** for placement-only. | **Confirm as stated** (D4h). | It is a governance policy, it changes behaviour for EP27 and EP38 as well as EP42, and a control decision belongs to the business rather than to me alone. | **Low.** It is a guard in `decide()` either way; the question is only which requests it binds. | KAN-198 |

### 6.1 Acknowledgements — not questions, but he should hear them

| # | What he should know | Why now |
|---|---|---|
| **A-1** | **The first real pay figure fires trigger T5 and the security phase (S5) runs before anything else** (D8). One manual entry counts. | Much better heard as a sequencing fact today than as an obstruction on the day he wants to show a prospect their own numbers. |
| **A-2** | **Under demo auth the pay visibility model is correct in code and unenforceable in practice.** Any compensation demo says so at the start. | Demo Readiness Gate rule 5. The stakeholder found DEF-001/2/3 live on 9 Aug; we do not repeat that by letting him discover this one. |
| **A-3** | **EP42 moves the S4 feature-freeze date out by the size of the epic** — roughly fifteen stories, three feature codes, five table sets, a dozen endpoints and several DOM builders, all of which enter the S5 hardening and WCAG sweep. | The price of the request. Worth paying; should be paid knowingly. |
| **A-4** | **Getting salary data in is the real adoption risk, not building the feature** (D7, R-2). 116 distinct free-text titles have to be mapped to a ladder by someone who knows the business. | The mapping screen and coverage meter are in scope because of this. The effort itself belongs to the tenant and needs naming in the customer-onboarding plan. |

---

## 7. Risks, dependencies and conflicts

### 7.1 Risks

Scored **likelihood × impact**, in the Charter severity scale. Owner named for each; the Delivery/Release Manager
holds the Risk Register (Charter §5) and should take these into it in Wave 2.

| # | Risk | L × I | Severity | Mitigation already designed in | Owner |
|---|---|---|---|---|---|
| **R-1** | **Alert fatigue kills the equity feature.** A literal 5% rule flags most of the population; HR mutes it (`notification_mutes` exists); the organisation then believes it has a control it does not have. | High × High | **Critical** | D1's two-check split, group minimums (n≥3 / n≥5), coverage gate, D2's justification validity window and re-fire delta, and the §1.5 tripwire (>40% justified → config review) | SPM |
| **R-2** | **The title→level mapping is a data project disguised as a story.** 41 + 75 distinct free-text titles for 146 people. The effort is real, belongs to the tenant, and is invisible in a story estimate. | High × High | **High** | KAN-191's mapping screen + CSV round-trip + coverage meter; named in the Customer-Readiness plan (A-4) | SPM / Delivery |
| **R-3** | **A pay amount leaks through a surface nobody listed** — a notification body, a CSV export, the search index, an analytics aggregate, the audit diff, a JSON payload filtered only in the browser. | Medium × **Critical** | **Critical** | §4.5.7's enumerated surface list; D5.6's `_MONEYISH_KEYS` guard; UAT's negative-visibility suite asserting absence from the **payload**, not the DOM | UAT / Architect |
| **R-4** | **The permission model is unenforceable under demo auth**, so nothing about D5 can be demonstrated as secure. | Certain × Medium | **High** *(accepted, disclosed)* | D8.3 disclosure; T5; feature off by default; synthetic-data banner | SPM |
| **R-5** | **One person approves a pay rise end to end** (backlog open item #5). | Medium × High | **High** | KAN-198's hard rule for money-bearing requests; overlap shown at chain-configuration time | Architect |
| **R-6** | **A partial proposal zeroes a salary** — the D-185-1 pattern, which all 4,628 tests passed through last time. | Medium × **Critical** | **Critical** | D4g's overlay rule and the named regression test across five proposal shapes | Senior SWE / UAT |
| **R-7** | **GDPR exposure widens.** Pay is not special-category, but pay × gender is the input to a gap computation, and data minimisation on *who sees amounts* becomes a live obligation rather than a design preference. Retention of pay history past exit will usually be **required** by tax/employment law — and **EP38's erasure enumeration (R3.6/R3.7) predates compensation and does not mention it**. | High × High | **High** | CFL-42-3 routes the enumeration gap to the BA; retention class on compensation records; D5's whole model | BA / DPO |
| **R-8** | **Works-council or co-determination requirement** on job classification or pay monitoring in a target tenant (Germany, Nordics — S3). | Medium × High | **High** | OQ-8; Customer-Readiness checklist item, not a build blocker | SPM / legal |
| **R-9** | **KAN-195 forks a second importer** because EP35-S2 has not landed when it starts. | Medium × Medium | **Medium** | KAN-195 is written against the EP35-S2 contract; if it ships first it is refactored onto the wizard, not left as a parallel path | Delivery |
| **R-10** | **The product is read as making a customer compliant** with a pay-transparency regime it merely measures against. | Medium × High | **High** | D1.3's framing requirement on every equity screen; §3.3 excludes statutory report generation; no compliance claim in any documentation | SPM / BA |
| **R-11** | **Scope creep into comp-review cycles.** "While we're here, could managers plan next year's increases?" is a whole product, and it will be asked. | High × Medium | **Medium** | §3.3's explicit exclusion; §3.4 names it as Later so it is parked, not lost | SPM |
| **R-12** | **The equity engine's arithmetic is wrong in a way tests do not catch**, because the fixtures were written by the person who wrote the maths. | Medium × High | **High** | KAN-168 real-DB tier; UAT writes fixture groups with **hand-computed** expected answers, including the n<3, coverage<80%, single-gender and all-equal cases | UAT |

### 7.2 Dependencies

| ID | Dependency | Needed by | Status | Note |
|---|---|---|---|---|
| **DEP-1** | **KAN-155** — `transaction()` atomic writes | KAN-189, KAN-193, KAN-195, KAN-196, KAN-197 | Planned, S2 enabler | **Hard prerequisite.** A promotion writes the assignment, the level/step, the compensation record and the audit rows. A half-applied promotion is the worst state in this epic |
| **DEP-2** | **KAN-166** — versioned migrations | KAN-188, KAN-189, KAN-190, KAN-193 | Planned, S2 enabler | Five new table sets and three feature codes. The `org_change_*` drift is precisely what this exists to stop |
| **DEP-3** | **KAN-187** — audit trail | KAN-193, KAN-202 and every mutating story | ✅ **Done** | Reused, not re-invented. Needs `ACTIONS` extended and `_MONEYISH_KEYS` added — Architect's edit (CFL-42-2) |
| **DEP-4** | **KAN-168** — real-DB integration tier | KAN-200 above all | Planned, S2 enabler | Group formation, medians and coverage gates cannot be verified against mocks |
| **DEP-5** | **KAN-185** — transfer flow | Not a dependency — **the reverse.** KAN-189 unblocks its `AC-185-07` | 🟡 In progress, blocked | State it this way round in the backlog: EP42 repays EP38 |
| **DEP-6** | **EP35-S2** — import wizard | KAN-195 (soft) | Planned, S3 | See R-9 |
| **DEP-7** | **KAN-163** — bounded background workers / any scheduler | Periodic equity re-evaluation, and any time-based progression | **Not planned** | Why D2 is event-driven + on-demand and D3 has no automatic roll-up. Do not design around a scheduler that does not exist |
| **DEP-8** | **Backlog open item #1** — the audit read-surface decision (per-employee timeline, company-wide viewer, or both) | KAN-202 | **Unresolved — SPM, Wave 3** | KAN-202 is deliberately a **compensation** surface, so it does not block on this; but the two should not be designed in ignorance of each other |
| **DEP-9** | **DPO / legal validation** — S13, retention of pay history past exit, works councils (OQ-8), the gender-gap computation's lawful basis | KAN-200, KAN-201, and the launch | **Not started** | Not a build blocker. **Is** a launch blocker. Charter §9.7 |

### 7.3 Conflict log (Charter §5 — never resolved silently)

Numbered `CFL-42-n` so they cannot collide with EP38's `CFL-1…7`.

| ID | Conflict | Severity | Evidence | Resolution required from |
|---|---|---|---|---|
| **CFL-42-1** | The documented access model says feature access is `role_feature_access` AND `company_role_feature_access`. `company_features.is_enabled` is a **third**, undocumented mechanism that the central resolver does not consult and that two blueprints enforce by hand. R7 requires it to work. | **High** | `app/auth.py:38-95` vs `app/routes/analytics.py:20-40`, `app/routes/skills_intelligence.py:21` | **Senior Architect** — ADR + KAN-188. He owns `CLAUDE.md` and the access model. **Gates the start of W1.** |
| **CFL-42-2** | `audit_service.ACTIONS` is a deliberately frozen closed enumeration and `_check_no_secrets` has no money guard, so a salary diff would be written verbatim today. EP42 needs both changed. | **High** | `app/services/audit_service.py:73-90, 95-98, 153-159` | **Senior Architect** — his file, his enumeration. Sign-off before KAN-193. |
| **CFL-42-3** | **EP38's erasure enumeration predates compensation.** `EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md` R3.6 (what erasure removes) and R3.7 (what must survive) list every table in the product and **do not mention pay**, because it did not exist. Left alone, an erasure will either destroy pay history that tax law requires retained, or retain identifying pay data that should have gone. | **High** (compliance) | EP38 §4.3 R3.6/R3.7 | **Business Analyst** (owner of that file), with DPO input. Must land before KAN-193 defines the retention class. |
| **CFL-42-4** | **Two job titles, unclear precedence.** `employees.job_title` is indexed and feeds the search trigger; EP42 makes the *level* title canonical. Directory, org tree, search, exports and the org-change summary each need to know which one they show. | **Medium** | `database/schema.sql:411, 1588, 1861` | **BA + Senior Architect.** My steer: level title canonical, working title supplementary. Needed before KAN-191. |
| **CFL-42-5** | **Segregation of duties** (backlog open item #5) is unresolved, and EP42 takes a position that changes `decide()` for EP27 and EP38 as well. | **High** | `app/services/org_change_service.py` `decide()`; backlog open item #5 | **Senior Architect** (shared engine) + **product owner ratification** (OQ-9). Gates KAN-198. |
| **CFL-42-6** | **The shared brief's baseline is wrong on tenancy.** It says "147 seeded Acme employees + Telia". Actual: Acme **46**, Telia **100**, a third tenant **"Sam Cpmapny"** with 0 employees and 3 locations, plus 1 company-less SYSTEM_ADMIN record. Anyone sizing the backfill from the brief sizes it wrong, and anyone testing tenancy will miss the empty third tenant. | **Medium** | `psql -d employee`, 2026-08-09 (S1) | **SPM — corrected here.** Every Wave 2 persona uses S1, not brief §2. |
| **CFL-42-7** | The roadmap runs to EP41 and has **no compensation epic and no BG7**; `BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` has no compensation feature; `BUSINESS_DOCUMENTATION.md` has no pay entity or retention rule for it. Three documents will be false the moment EP42 starts. | **Medium** | Roadmap §C/§D; the two business documents | **SPM** amends the roadmap and `BACKLOG.md` in **Wave 3**; **BA** amends the two business documents in the same commit as the implementation (Charter §5b rule 1). Recorded now so nobody walks past it. |

---

## 8. Wave 2 tasking

Each brief is bounded. Report in the Charter §6 format. **Do not re-derive §2 — build on it.** Where you disagree
with a decision in §4, say so explicitly under the Conflict Log convention and proceed on the stated rule; do not
quietly build something else.

### 8.1 Business Analyst

**Deliverable:** `EP42_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`, to the depth and structure of the EP38 file.

1. **Full numbered acceptance criteria** for all fifteen stories — `AC-<story>-<nn>`, individually testable, happy
   path / edge and boundary / error and failure / permissions / tenant isolation, as in EP38 §5–§8.
2. **Extend the §2 baseline** with the B-rows I have not needed: every read path that could surface a pay amount
   (the §4.5.7 list, verified in code with line numbers), how `employment_type` and the absent FTE interact with
   existing queries, and what a non-ACTIVE employee's compensation record should do.
3. **Expand D5 into a per-role, per-scope criteria set** — for every cell of §4.5.2, the expected response
   (`200` with amount / `200` with the field **absent** / `403`), for both the HTML surface and the JSON payload.
   This is the highest-value table in your document.
4. **Write D1's arithmetic as testable criteria** — group formation, the n≥3 and n≥5 minimums, the coverage gate,
   median versus midpoint selection, FTE normalisation, exclusion counting, the two thresholds, and the re-fire
   rule. Worked examples with hand-computed answers; UAT will use them.
5. **Own CFL-42-3**: extend your EP38 R3.6/R3.7 erasure enumeration to cover compensation and job-level data —
   what is anonymised, what must survive, and under which lawful basis. **This is a change to your own file and
   lands in your commit.** Flag the retention period question to the DPO alongside OQ-2's 7-year default.
6. **Traceability matrix** R1–R7 → decision → story → criteria → UX / Technical / Test pointers.
7. **Conflict log and assumption register**, starting from §7.3 and §9. Add what you find.
8. **State the DoR verdict per story.** Say which are NOT READY and exactly what is missing.

**Do not:** design schema, re-decide §4, or invent a comp-review cycle.

### 8.2 Senior Architect

**Deliverable:** your task-breakdown document, extended with EP42 — ADRs plus engineer-level tasks.

1. **ADR — the tenant feature switch (CFL-42-1, gates W1).** Where the AND is applied; the backfill migration that
   materialises `company_features` rows **with no behaviour change for any existing feature** (this is the
   acceptance criterion that matters); whether `has_feature_access()`'s signature changes; per-request caching
   against `g._feature_access`; how the two ad hoc consumers are retro-fitted; the removal path for
   `enabled_for_hr`; and the shape of the "disabled for this tenant" state.
2. **ADR — the compensation data model.** Append-only effective-dated history; amount, currency, FTE, pay basis;
   why no UPDATE and no DELETE path; the correlation to `audit_log`; the retention class; indexing for the equity
   engine's group queries at 100k employees, not 146.
3. **ADR — job architecture.** Family / level / step; immutability of ordinal position once assigned; the
   effective-dated assignment; the relationship to `employees.job_title` (CFL-42-4) including the search trigger
   and index.
4. **CFL-4 / KAN-189.** Pick the interval convention, thread `effective_date` through `create_request()` and
   `_apply_change`, and state how the existing one-day overlap is corrected without rewriting history.
   **This closes `AC-185-07` — coordinate with whoever is finishing KAN-185.**
5. **`audit_service` extension (CFL-42-2).** The new `ACTIONS`, `_MONEYISH_KEYS`, and the retention class for
   compensation events. Your file, your sign-off.
6. **The CC-2 boundary, written down.** How row-level pay scoping (manager → direct reports) is expressed so it is
   unambiguously **not** the forbidden sub-flag pattern. An engineer will get this wrong without a written rule.
7. **`decide()` and four-eyes (CFL-42-5).** How the guard is expressed, what it does to EP27 and EP38, and how the
   overlap is surfaced at chain-configuration time.
8. **The D-185-1 hazard for compensation fields** — the overlay rule, and the regression coverage you require.
9. **Feature registration**: three codes × four places, and confirm `TestFeatureRegistryHasNoDrift` catches a miss.
10. **Task breakdown to Senior SWE / Mid-Level / DevOps**, with sequencing and estimates.

**Do not:** re-open the product decisions in §4. If one is technically infeasible, say so with the reason and a
counter-proposal — that is a conflict-log entry, not a silent redesign.

### 8.3 UX / Product Designer

**Deliverable:** journeys and design specs in the relevant sections of `BUSINESS_DOCUMENTATION.md` and
`TECHNICAL_DOCUMENTATION.md` (Charter §5b). If they outgrow their host, propose `UX_DESIGN_SPECS.md` to me — do
not sprawl.

1. **The ladder configurator (KAN-190)** — the hardest screen in the epic. A tenant defining families, levels,
   titles and step counts from nothing, in an order that makes sense before they know the vocabulary. The empty
   state matters more than the populated one.
2. **The title→level mapping screen (KAN-191)** — 41 or 75 distinct free-text titles, with counts, mapped in one
   sitting. Bulk-apply, per-title override, CSV round-trip, progress. This screen decides whether the backfill
   finishes (R-2).
3. **The compensation block inside the shared move modal (KAN-196).** **Constraint: it must not make the common
   case heavier.** Most moves have no pay change. Prove that the no-change path costs one deliberate click and no
   extra scroll — and that "no change" cannot be selected by inertia, because the whole point is that it is an
   answer.
4. **"No salary recorded" and "Not applicable — contractor"** — two different empty states that must never look
   like a value or like each other (D7).
5. **The equity queue and its disposition flow (KAN-201)** — including the justification categories, the reason
   requirement, and the plain-language framing that this is a measurement and not a verdict (D1.3).
6. **The bell, against D4's blind-spot list, in writing.** Section placement, icon, badge, quick action, empty
   state, retirement, and **what four different actors see** — a recipient with an open flag, a recipient after
   somebody else dispositioned it, a user without `pay_equity`, and the subject of the flag (who is **not** a
   recipient). This is where DEF-001/2/3 lived and it is your gate item D4.
7. **"My Pay" (KAN-194)** — the most easily misread copy in the epic. Position-in-range without a raw compa-ratio,
   no comparison to anybody else, and **no forward-looking language that reads as a promise**.
8. **The promotion-eligible signal (KAN-192)** — a signal, not an entitlement. One sentence, and it has to be the
   right one.
9. **WCAG 2.2 AA as a design standard on all of it** (roadmap D-004 / Q5) — labelled controls, keyboard-operable
   confirmations, focus management, no colour-only status, and `escH()` for every new DOM builder.

### 8.4 UAT Lead

**Deliverable:** the EP42 test plan and cases, plus the regression-suite extensions you will own.

1. **Test cases per story**, happy and unhappy, in your standard format.
2. **The negative-visibility suite — your highest-value contribution.** For every role in §4.5.2 and every surface
   in §4.5.7: assert the amount is **absent from the server's JSON payload and from the rendered HTML**, not
   merely invisible. A CSS-hidden salary is a leak that passes a screenshot review, and it is a common failure.
3. **Tenant isolation for pay.** Company A must see zero of company B's amounts under every filter, every export,
   every search and every aggregate — including a SYSTEM_ADMIN with "All Companies" selected.
4. **The equity engine against hand-computed fixtures**, written by you and not by the engine's author: an
   ordinary group, a group at n=2 and n=3, coverage at 79% and 81%, a single-gender group, an all-equal group, a
   part-time employee needing FTE normalisation, a contractor who must be excluded, and a two-country group that
   must not be compared.
5. **The flag lifecycle**, asserting **content** and not just presence (Gate D7): the item appears in the right
   bell section with the right icon **and its Review action**; it retires on disposition **for every eligible
   recipient, not only the one who acted**; it does **not** retire on read; a `JUSTIFIED` flag does not re-fire
   inside its window; it does re-fire when the gap widens past the delta.
6. **The D-185-1 regression for compensation** — the five proposal shapes in D4g. Assert the final DB row, not the
   API response.
7. **Extend both regression suites** (`tests/ui/test_browser.py`, `tests/ui/test_vacation_workflow.py`) for the
   flows EP42 changes, and add compensation coverage to the browser suite. You own these files (Charter §5b).
8. **A Demo Readiness Gate pack (D2/D3/D7)** for any compensation demo — every actor, both outcomes, and the
   **A-2 disclosure in the script**: the permission model is unenforceable under demo auth. A compensation demo
   without that line in the script is **NO-GO**, and I will hold that.

---

## 9. Assumption and unknown register (new entries)

| Item | Type | Impact if wrong | Validation needed | Owner |
|---|---|---|---|---|
| The EU Pay Transparency Directive's 5% joint-pay-assessment trigger is a **gender gap within a category of workers**, not a raw dispersion (S13) | **Assumption** (Medium confidence — general knowledge, not verified against a source in this repo) | D1's Check B is the wrong shape, and any compliance framing around it is misleading | **DPO / legal** | SPM |
| Base salary alone is a sufficient comparison basis for a first release (no variable pay) | **Assumption** | In a sales-heavy tenant, base-only comparison is close to meaningless and would produce confidently wrong findings | Confirm with the first customer's pay structure; OQ-5 | SPM |
| One currency per pay market holds for target tenants | **Assumption** — true for both populated seed tenants (S3) | An FX table becomes a Must in KAN-199/200 rather than Later | OQ-6 | SPM |
| Tenants will accept that a manager sees their direct reports' pay by default | **Assumption** | Wrong default in a works-council jurisdiction is a launch incident, not a config change | OQ-2, OQ-8 | SPM / legal |
| A 12-month justification validity window is the right anti-fatigue default | **Assumption** (Low confidence — no data) | Too long hides a gap that has become unjustified; too short recreates the alert storm | Tune against the first tenant's first two runs; watch the §1.5 tripwire | SPM |
| Pay history must be **retained** past exit for tax/employment record-keeping, i.e. it is on EP38 R3.7's survive-erasure list and not R3.6's remove list | **Needs Validation** | Getting this backwards is a GDPR finding in one direction or a legal-retention failure in the other | **DPO**, per jurisdiction; CFL-42-3 | BA / DPO |
| `employees.gender` (`MALE`/`FEMALE`/`OTHER`, currently used only for vacation eligibility) is a lawful and adequate basis for a gender pay gap computation | **Needs Validation** | Check B cannot run, or runs on a basis the DPO rejects. Note EP38 §4.3 already flags this column for DPO review for a *different* purpose — the purposes are now two, which is itself a purpose-limitation question | **DPO** | BA / DPO |
| The seeded population (146 PERMANENT, 1 CONTRACTOR, 0 PART_TIME — S4) will not exercise FTE normalisation or contractor exclusion | **Known** | Real defects in both paths would ship untested | UAT builds fixtures that do (§8.4.4) | UAT |
| Coverage of 80% is the right gate for evaluating a group | **Assumption** (Medium) | Too low produces wrong findings; too high means no tenant ever gets a first result | Configurable 50–100%; review after the first tenant | SPM |
| No tenant needs pay data to reach payroll from this product in this cycle | **Assumption** | If payroll integration is expected, the compensation record's shape and identifiers change | OQ-5 conversation; EP40-S3 is the vehicle if it is wanted | SPM |

---

## 10. Definition of Ready — status per story

Assessed against Charter §4 DoR: problem understood · persona identified · business value defined · requirements
and acceptance criteria documented · UX understood · dependencies identified · data requirements known ·
security/privacy considered · technical feasibility assessed · test approach understood.

| Story | DoR after Wave 1 | What is still missing |
|---|---|---|
| KAN-188 | **NOT READY** | Architect ADR (CFL-42-1) + BA criteria. Everything else is decided. |
| KAN-189 | **NOT READY** | Architect's interval convention (CFL-4) + BA criteria. |
| KAN-190, KAN-191 | **NOT READY** | BA criteria · UX designs · CFL-42-4. |
| KAN-192 | **NOT READY** | **OQ-1** (the roll-up) — the only story in the epic gated on a product-owner answer rather than on Wave 2 work. Build against the default. |
| KAN-193, KAN-194 | **NOT READY** | BA criteria · Architect ADR · CFL-42-2 · CFL-42-3. **KAN-194 additionally needs UAT's negative-visibility approach agreed before it is built, not after.** |
| KAN-195 | **NOT READY** | BA criteria · UX mapping screen · EP35-S2 sequencing (R-9). |
| KAN-196, KAN-197 | **NOT READY** | BA criteria · UX (the modal-weight constraint) · DEP-1 (KAN-155). |
| KAN-198 | **NOT READY** | **OQ-9** ratification + CFL-42-5. |
| KAN-199, KAN-200, KAN-201 | **NOT READY** | BA criteria (D1's arithmetic) · UAT fixtures · DEP-4 (KAN-168) · OQ-3 · OQ-6. |
| KAN-202 | **NOT READY** | DEP-8 (audit read-surface decision) · BA criteria. |

**Nothing in EP42 is Ready, and nothing should be — this is Wave 1 of three, and S1 has not closed.** The epic
becomes Ready when the Wave 2 artifacts land and I have ratification on OQ-1, OQ-3, OQ-5 and OQ-9. Everything
else has a default the team builds against from today.

---

## 11. What I will do in Wave 3

Recorded so nobody duplicates it, and so it does not quietly not happen (Charter §5b):

1. **`docs/project-management/BACKLOG.md`** — add the EP42 section with all fifteen stories, the epic summary row,
   the dependency table and the build order; mark backlog open items **#3, #4 and #5 resolved** with pointers to
   D4e, D4f and D4h.
2. **`docs/product-team/deliverables/PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md`** — add **BG7**, add **EP42** with its
   waves and stage placement, and add **trigger T5** to the D-004 amendment table (D8.3).
3. **`docs/project-management/DEMO_READINESS_GATE.md`** — add the A-2 disclosure requirement for any compensation
   demo to the gate's known-defects/known-limitations rule.
4. **Reconcile the Wave 2 reports** — BA against Architect against UX against UAT — resolve every conflict
   explicitly in the Decision Log, and re-issue anything that arrives without evidence.
5. **Answer backlog open item #1** (the audit read surface), since KAN-202 sits next to it.
6. **Take OQ-1 through OQ-9 to the product owner** as one short conversation, with the defaults already being
   built against so the conversation is a confirmation and not a blocker.

*All of it in the same commits as the work it describes. Documentation lives in git; nothing goes to Jira or
Confluence (`CLAUDE.md`).*

---

# ⚖️ WAVE 3 — RECONCILIATION, RULINGS AND CONSOLIDATION — 2026-08-09

> **Added by the SPM after all four Wave 2 specialists reported.** Charter §7 (the SPM review and tasking
> contract) and §8 (the operating cycle). Everything above this line is Wave 1 and is left standing as written,
> **including the three decisions Wave 2 disproved** — §12.2 records what was wrong and why, rather than editing
> the record to look right. A decision log that quietly self-corrects is not a decision log.
>
> **Inputs reconciled:** `EP42_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md` (BA — 532 criteria) ·
> `EP42_TECHNICAL_DESIGN.md` (Architect — ADR-014…023, 14 tables, 112 tasks) · `EP42_UX_SPEC.md` (UX) ·
> `EP42_UAT_TEST_PLAN.md` (UAT — 300 cases, 21 attacks, 12 arithmetic fixtures).
>
> **Where a ruling below contradicts anything above the line, the ruling wins.**

## 12. The reconciliation

### 12.0 The five things that changed

1. **My D6 was wrong and it would have taken both tenants down on merge day.** I assumed absent
   `company_features` rows defaulting to enabled. The Architect checked: there are **18 rows and 14 are
   `is_enabled = FALSE`** — the directory, org tree, user admin, skills, vacations and company settings, in both
   populated tenants — inert only because nothing reads them. The day the resolver honours them, every
   non-SYSTEM_ADMIN user in Acme and Telia loses the entire product, with the login page still working so it
   reads as a permissions catastrophe rather than a flag. And **CI stays green the whole way**, because
   `seed_rbac.sql` carries none of those rows. Amended in §12.2.
2. **Two Critical pre-existing defects, and they are worse together than apart.** `_can_initiate_for` never
   compares the initiator to the subject; `decide()` never compares the decider to the subject. Today an
   HR_ADMIN can raise a position change for themselves and approve it, on the seeded default chain. Ruled in
   §12.5 — **fixed in W0 as KAN-203, at P0, not deferred to W3.**
3. **Two more holes in my own four-eyes rule, found independently by UAT and UX.** It binds approvers to each
   other but not the **initiator** (so `ingrid.makinen`, holding both PORTAL_ADMIN and HR_ADMIN, raises her own
   pay rise and satisfies level 1 by role, with KAN-198 fully built and green), and it is a **silent no-op on
   the default chain**, which is a single HR_ADMIN level. A control that passes its tests while doing nothing is
   the worst kind.
4. **My "PORTAL_ADMIN only" was the forbidden role check**, flagged independently by the Architect and UX with
   two different fixes. Ruled in §12.3 (CFL-42-20).
5. **KAN-155 is already Done, and KAN-168 is not started.** My dependency table had both backwards. Nothing was
   waiting on the first; the second hard-blocks the equity engine and is now the epic's real scheduling problem.

### 12.1 Review verdict on each specialist report (Charter §7)

I verify that every material claim is evidenced, that assumptions are labelled rather than smuggled in, that
charter conventions were used, and that findings reconcile across roles. I do not rubber-stamp.

| Report | Verdict | Evidence standard | What I am sending back |
|---|---|---|---|
| **Business Analyst** — requirements & acceptance criteria | **ACCEPT** | **Exceeds the bar.** 532 criteria, each individually testable; every baseline claim carries a `file:line`; assumptions labelled with confidence; ten new conflicts surfaced rather than resolved silently; a DoR verdict per story; and the GDPR resolution (§4.7) closes CFL-42-3, which I had merely routed. They also found **two Critical pre-existing defects and one live High defect** while writing criteria — that is the job done properly. | Three reworks, all caused by **my** rulings, not by their quality: (a) AC-197-* rewritten for the `LEVEL_CHANGE` rename (Ruling 8); (b) **AC-202-* must stop claiming a guarantee the mechanism cannot give** (Ruling 9) — this one matters, it is the difference between an honest control and a false one; (c) AC-199-* splits with the story (Ruling 32). |
| **Senior Architect** — technical design | **ACCEPT** | **Exceeds the bar.** Ten ADRs, each with rejected alternatives and a confidence label; every premise re-derived rather than inherited (V1–V9); no unresolved architectural unknowns; risks quantified with owners. He also caught the defect in **my** decision that would have caused the worst incident available in this epic, and flagged the SYSTEM_ADMIN narrowing for an explicit yes instead of assuming it. | Four additions: (a) **ADR-016 gains `feature_access_for(user_id, company_id)`** — the non-session resolver (Ruling 4), because that story is already rewriting the query; (b) **ADR-016's repair migration must state its reversibility explicitly** — capture the prior `is_enabled` values as a fixture, or declare the migration one-way and say so before it runs, not after; (c) **ADR-022 gains a cancel-not-approve remedy** for a genuinely stuck chain — that is a condition of my yes on the SYSTEM_ADMIN narrowing (Ruling 13); (d) ADR-021 and ADR-019's action list updated for `LEVEL_CHANGE`. |
| **UX / Product Designer** — design spec | **ACCEPT** | **Meets the bar and answers the two hardest design problems** rather than deferring them: discretion (ten rules, "absent, not hidden", applied to the surfaces that leak by accident) and the standing condition (retirement only on a recorded decision or a data change, for every recipient, with a re-fire that announces itself as a continuation). Every screen carries states, copy, validation strings and an accessibility annotation. They **verified** the shell accessibility claim in the repo instead of assuming EP38 delivered it — three of nine fixes did not land. | Four: (a) the Compensation Settings page now has **two gates** (Ruling 3) and must read coherently to a holder of one and not the other; (b) the `LEVEL_CHANGE` rename **replaces** their derived-display-label workaround, which is a simplification for them (Ruling 8); (c) the contractor-rate empty state changes (Ruling 31); (d) **design the audited salary export** they correctly predicted HR would demand (Ruling 28). |
| **UAT Lead** — test plan | **ACCEPT WITH ONE CORRECTION** | **Meets the bar.** The 21-attack confidentiality catalogue and the 12 hand-computed fixtures are precisely the answer to R-3 and R-12, and asserting **absence from the payload rather than the DOM** is the single most valuable thing anyone specified in Wave 2. Findings F-03 and F-04 are two control gaps I should have closed in Wave 1 and did not. The pre-declared sign-off position is exactly right and I endorse it. | **Correction:** F-01, F-01c and F-01e are reported as unspecified but **are specified** — BR-1.1, BR-1.5, BR-2.4 and ADR-014 answer them. Written concurrently, so this is not a rigour failure; but the plan must be **re-read against the BA and Architect files before execution** and the affected cases un-Blocked. Also: their F-01 recommendation ("ratios carried unrounded into comparisons") **contradicts BR-1.6** ("compare the value the UI shows") — nobody noticed, and I have ruled it as **CFL-42-34**. |

**Cross-role observation worth recording.** All four reports were written concurrently and they converged, not
diverged: the Architect, UX and UAT independently found the same hole in my four-eyes rule from three different
angles, and the Architect and UX independently found the same forbidden role check in my D1. Independent
convergence on a defect is strong evidence; I have treated all three as confirmed rather than as opinions to
weigh. Equally, **nobody found a problem with the epic's shape** — the wave order, the grouping key argument and
the decision to sequence the platform work first survived contact with all four specialists. That is worth
knowing before the build starts.

### 12.2 Amendments to my Wave 1 decisions

Three of my decisions were wrong or incomplete. They are amended here, not edited above.

#### A-1 — **D6 requirement 2 is replaced.** *(Ruling on CFL-42-1 / TR-15 / the Architect's blocker B-3)*

**What I wrote (Wave 1, §4.6.3):** *"Default for an absent row. **Enabled** for the eleven existing features —
KAN-188 must change nothing for any existing feature or tenant, and that is an acceptance criterion."*

**Why it was wrong.** The acceptance criterion is right; the mechanism cannot deliver it, because the rows are
not absent. 14 of the 18 `company_features` rows are present and **FALSE**, for features nothing currently
consults.

**Replacement — I ratify ADR-016 in full:**
- The default for an absent row is a **`portal_features.default_enabled` column**, not a constant in Python. A
  hardcoded set in `auth.py` would be a second feature registry one file away from the drift test that exists to
  catch exactly that.
- The migration **repairs first, then materialises**: set to TRUE every row that is FALSE for a feature nothing
  consults (excluding `reports` and `skills_intelligence`, whose values are live and must be preserved
  verbatim), then insert a row for every (company, feature) pair from `default_enabled`.
- **The 330-cell before/after matrix is a release gate, not a task.** 3 companies × 11 features × 10 roles must
  resolve identically after the migration, with the "before" captured as a fixture **before any code is
  written**. I am naming it a gate because this is precisely the class of change a reviewer skimming a green
  suite waves through.
- **Two additions of mine.** (i) The repair migration must **state its reversibility explicitly** — either the
  `_down` restores the captured prior values, or the migration is declared one-way in the runbook *before* it
  runs. A rollback that silently re-blacks-out both tenants is the same incident twice. (ii) KAN-188's
  **estimate must include the proof**, not just the change; the Architect made this point and it is right.

**Standing lesson, recorded because it will recur.** I reasoned about a data-shaped question from the schema
rather than from the data. The schema says the row may be absent; the database says it is present and false.
Any future decision that turns on "what is in the tables today" gets checked against the tables.

#### A-2 — **D5.6's audit guarantee is scoped honestly.** *(Ruling on UAT-F-03 → CFL-42-30)*

**What I wrote (§4.5.6):** *"a monetary amount is never written into an `audit_log` diff, metadata **or
reason**"*, enforced by a `_MONEYISH_KEYS` guard.

**Why it was wrong.** `_MONEYISH_KEYS` matches **keys**, exactly as `_SECRETISH_KEYS` does
(`app/services/audit_service.py:95-98`). `reason` is mandatory free text a human types. No key-matching guard
can see inside it. I specified a guarantee the mechanism cannot give, which is worse than specifying a weaker
one — UAT is right to refuse to write a pass/fail case for it.

**Replacement:**
- The **structural** guarantee **stands and is strengthened**. I adopt ADR-019's **per-action closed diff-key
  allowlist** over my denylist: a creatively-named key is refused because it is not on the list, not because we
  guessed it might be money. No amount reaches `before_state`, `after_state` or `metadata`. That part is a
  guarantee and is testable.
- The **free-text `reason` is governed by design, not by a guard.** On compensation-bearing actions, `reason`
  becomes a **mandatory category** from a seeded, company-editable list plus **optional** free text — so the
  mandatory part is structured. The optional text carries a **non-blocking warning** when it matches a numeric
  pattern ("reasons are readable by audit-log holders who may not be able to see pay"), and is included in the
  compensation redaction path at erasure.
- **No acceptance criterion may claim the guarantee covers free text.** BA amends AC-202-*.

#### A-3 — **D1's "configurable by PORTAL_ADMIN only" is replaced.** *(Ruling on CFL-42-20)*

Detailed in §12.3. Short form: it was a role check in product clothing, and I have moved it onto
`company_settings:w`.

#### A-4 — Two corrections to my dependency table

- **DEP-1 (KAN-155) is ✅ Done, not planned.** Nothing in EP42 was waiting on it. Corrected.
- **DEP-4 (KAN-168) is ⬜ not started and hard-blocks KAN-200.** This is the epic's real scheduling problem and
  it is mine to own — see Ruling 27.

#### A-5 — D7.5's coverage figure is replaced by two named figures *(Ruling on CFL-42-17)*

My example string *"Compensation data: 62% of active employees"* is ambiguous and would be quoted at a customer.
Replaced by **pay coverage** (% of ACTIVE employees with a compensation record in effect) and **level coverage**
(% with a level assignment in effect), each naming its denominator. The **equity coverage gate is a third
number** and neither of those: its denominator is *group membership* (which requires a level) and its numerator
is *comparable records*. Stated explicitly so nobody conflates the adoption instrument with the evaluation gate.

### 12.3 The authoritative conflict register

**The BA and the Architect independently allocated `CFL-42-8` through `CFL-42-13` to different conflicts.** This
table is now the single authoritative register; the *Source* column maps every prior ID so an existing reference
resolves unambiguously. **Wave 2 documents keep their internal numbering; this register governs.**

| Authoritative ID | Source | Conflict (one line) | Sev | **SPM ruling** | Home |
|---|---|---|---|---|---|
| **CFL-42-1** | SPM W1 | Tenant switch not in the central resolver. | High | **Resolved.** ADR-016 ratified with the two additions in A-1. | KAN-188 |
| **CFL-42-2** | SPM W1 | `ACTIONS` frozen; no money guard. | High | **Resolved.** ADR-019 ratified; allowlist adopted over my denylist. Also add the two codes **EP38 already needs and does not have**. | KAN-193 |
| **CFL-42-3** | SPM W1 | EP38's erasure enumeration omits pay. | High | **Resolved by the BA (§4.7).** Seven DPO items remain; DPO-2 blocks only the retention class. | KAN-193 |
| **CFL-42-4** | SPM W1 | Two job titles, unclear precedence. | Medium | **Resolved.** ADR-017(d) per-surface table; `job_title` kept and demoted; **searchability of the level title is TD-18, recorded not silently accepted.** | KAN-191 |
| **CFL-42-5** | SPM W1 | Four-eyes changes `decide()` for EP27/EP38. | High | **Resolved**, subject to OQ-9. Split: identity rules → KAN-203 (W0); chain rules → KAN-198 (W3). | KAN-198 |
| **CFL-42-6** | SPM W1 | Brief's tenancy baseline wrong. | Medium | **Closed.** S1 stands; BA re-verified independently. | — |
| **CFL-42-7** | SPM W1 | Roadmap has no BG7/EP42; two business docs have no pay. | Medium | **Roadmap and backlog: done in this wave.** The two business documents are the BA's, in the implementation commit. Note EP38 **CFL-3** (indefinite-retention falsehood in `BUSINESS_DOCUMENTATION.md:242-243`) is **still open** and now also contradicts §4.7 — chase it. | SPM / BA |
| **CFL-42-8** | BA-8 | **`@require_feature_access` denies with a 302 redirect, for JSON endpoints too.** Every "returns 403" criterion in EP42 *and EP38* describes behaviour the decorator does not have; a `fetch()` receiving a 302 to an HTML dashboard is the DEF-002 shape. | **High** | **Ruled: fix it in KAN-188**, alongside the resolver rewrite — same file, same story, one regression pass. A JSON-aware denial (content negotiation, not a second decorator). **This also silently fixes EP38's criteria**, which the BA should note. | KAN-188 |
| **CFL-42-9** | BA-9 | `_apply_change` closes `manager_relationships` with no `effective_to`; 2 such rows exist. | Medium | **Ruled: fix inside KAN-189** (DEF-42-2). Cheap now; the pattern EP42 was told to copy is broken on its closing side and would be copied into three new tables. | KAN-189 |
| **CFL-42-10** | BA-10 | One shared effective date, two different scheduler dependencies. | Medium | **Ruled: ratify BR-3.6a.** `TRANSFER`/`LEVEL_CHANGE` may not be future-dated (no scheduler); a pay-only `COMPENSATION_REVIEW` may — an inert future row is safe, a future placement is not. | KAN-189 |
| **CFL-42-11** | BA-11 | **Four-eyes is a silent no-op on the default chain**, which is a single HR_ADMIN level — i.e. every tenant today. | **High** | **Ruled: ratify AC-198-08 and AC-198-11.** Money-bearing requests require **≥2 independently satisfiable levels, refused at create**; and a **seeded two-level default chain** (HR_ADMIN → PORTAL_ADMIN) ships for money-bearing types. This also answers OQ-BA-10. Without both, the control passes its tests and does nothing. | KAN-198 |
| **CFL-42-12** | BA-12 | **D4b's create-time approver-eligibility check cannot be written** — `_load_feature_access()` resolves only the session user. | **High** | **Ruled — and both roles were right about different things.** The BA is right that the primitive does not exist; the Architect is right that it does not block KAN-194 (which is about the session user's own visibility). **It blocks KAN-196, not KAN-194.** And it is **not a gap to accept: `feature_access_for(user_id, company_id)` becomes a named deliverable of KAN-188**, which is already rewriting that exact query. Adding it there costs a fraction of adding it later. **DEP-10 closes.** | KAN-188 → KAN-196 |
| **CFL-42-13** | BA-13 | A manager without `compensation:r` can route around the mandatory pay decision — D4c and D4f read together make R3's control optional for the population that raises most moves. | **High** | **Ruled: ratify AC-196-16 verbatim.** The request records `NOT_ANSWERED_NO_PERMISSION` and **the first `compensation:r` approver must answer before approving**. Satisfies D4c and D4f simultaneously, which my Wave 1 text did not reconcile. Good catch. | KAN-196 |
| **CFL-42-14** | BA-14 | **`_can_initiate_for` never compares initiator to subject** — the admin exemption covers acting on oneself. | **Critical** | **Ruled in §12.5. Fixed in KAN-203, W0, P0.** Raised as **DEF-42-4** against EP27. `CLAUDE.md`'s headline invariant is right and the code is wrong. | KAN-203 |
| **CFL-42-15** | BA-15 | **`decide()` never compares the decider to the subject** — combined with the above, one HR_ADMIN raises and approves their own request today. | **Critical** | **Ruled in §12.5. Fixed in KAN-203, W0, P0.** Raised as **DEF-42-5** against EP27. | KAN-203 |
| **CFL-42-16** | BA-16 | "Copy the `manager_relationships` pattern" is wrong for compensation — a stored `is_current` on a future-dated row needs a scheduler. | Medium | **Ruled: ratify BR-3.2/AC-193-13.** "Current" is **computed, never stored**, for compensation and level assignments. Architect confirms in ADR-015 (his half-open + GiST design is already consistent). | KAN-193 |
| **CFL-42-17** | BA-17 | Two coverage numbers with different denominators. | Medium | **Ruled: ratify BR-4.3**, and see amendment A-5 — there are in fact **three** numbers and the third is the gate. | KAN-195 |
| **CFL-42-18** | ARCH-8 | **KAN-190 gated on `compensation` would blank the directory job title for everyone**, because the level title becomes the job title. | **High** | **Ruled: ratify ADR-017(e).** Ladder **reads** on `employee_profiles`, **writes** and the configurator on `compensation:w`. My Wave 1 story text was wrong. | KAN-190 |
| **CFL-42-19** | ARCH-9 + UX-6 | **A compa-ratio is invertible into a salary**, so `pay_equity:r` alone can reconstruct pay D5 withholds — and the Feature Access tab gives no hint of the consequence. | **High** | **Ruled: adopt both halves.** Numeric measured values render only to holders of **both** codes, otherwise a band label; **plus** a config-time advisory where the grant is made. **And I am amending D5.7: my surface list enumerated surfaces, not derivations.** *Inference* is now a named category on that list. That was a genuine gap in my decision. | KAN-201 |
| **CFL-42-20** | ARCH-10 = UX-1 | **"Thresholds configurable by PORTAL_ADMIN only" is the forbidden role check**, and D5.2's matrix contradicts it by giving HR_ADMIN threshold configuration. | **High** | **Ruled: adopt the Architect's `company_settings:w`. Reject UX's `pay_equity:d`.** Both fixes remove the role check; the tiebreaker is what the tenant admin sees at the moment of granting. `d` means *delete* everywhere else in this product, and a grant labelled "delete" that actually confers *configure* misleads at exactly the point the choice is made — and it implies findings are deletable, which they are not. `company_settings:w` is seeded PORTAL_ADMIN-only **today**, delivers my intent as a default rather than a check, and has two in-repo precedents (org-change workflow config; EP38 checklist templates). **Consequence for UX:** the Compensation Settings page now has **two gates** — thresholds/coverage/pay-markets on `company_settings:w`, bands/levels on `compensation:w` — and must read coherently to a holder of one and not the other (absent, not disabled, not broken). | KAN-199 |
| **CFL-42-21** | ARCH-11 | KAN-199 → KAN-200: my wave order implies hard, the Architect says soft. | Medium | **Ruled — and neither answer was right, because KAN-199 was two stories.** See Ruling 32: **pay markets** are part of the comparison group key and are a **hard** prerequisite (now KAN-199, moved into W2); **bands** are the comparison basis and are **soft** (now KAN-205, W4). Labelling the whole thing "soft" would have left the group key undefined at KAN-200; leaving it "hard" would have put a large band-configuration exercise on the critical path for no correctness gain. | KAN-199 / KAN-205 |
| **CFL-42-22** | ARCH-12 | The two-table access model cannot express **"read company-wide, write nothing"** — a read-only auditor or works-council representative has no clean grant. | Medium | **Ruled: accept the gap for this cycle.** No fourth feature code (permanent surface area for a hypothetical) and no `scope` column (a change to the platform's access model deserves its own decision, not a side-effect of EP42). Architect's interim stands: `r`-only means "your direct reports". **Recorded as a named product limitation** in the release notes and in `BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md`. Revisit if OQ-8 returns "yes". | Release notes |
| **CFL-42-23** | ARCH-13 | My DEP-1 says KAN-155 is planned; it is Done. | Low | **Corrected** (A-4). Nothing was waiting. | — |
| **CFL-42-24** | UX-2 | **The bell badge counts every open finding**, so with a 15-working-day disposition target it sits permanently non-zero and destroys the signal for the approvals sharing it. | Medium | **Ruled: adopt UX's proposal.** The badge counts findings **with no owner**; `[ Take ]` is a recorded, audited act (so it does not violate "never retires on read") that decrements the badge while the finding stays open and stays in the register. My D2 badge rule was wrong, and it was wrong in the direction of my own top risk — alert fatigue arriving through a door R-1 was not watching. | KAN-201 |
| **CFL-42-25** | UX-3 | **`request_type = PROMOTION` labels a demotion "Promotion"** in the inbox, bell, timeline and audit trail. | Medium | **Ruled — and I am rejecting both proposed options in favour of a third.** Not a derived display label (it cannot fix an audit action that says `PROMOTION_APPLIED` for a demotion — a lie in the durable record) and not a fourth enum value (two values meaning the same thing, chosen inconsistently). **Rename the type to `LEVEL_CHANGE` and store a `direction` of UP/DOWN/LATERAL.** Costs nothing now, when nothing is built. **"Promotion" stays the user-facing word when the direction is UP** — R4 asked for a promotion flow, not for an enum literal. Audit becomes `LEVEL_CHANGE_APPLIED` with direction in the diff. | KAN-197 |
| **CFL-42-26** | UX-4 | **Four-eyes creates a second unsatisfiable-chain case** D4b does not cover: a chain where one person is the only possible approver at two levels — created, then never decidable. | **High** | **Ruled: refuse at create, for both cases.** Consistent with D4b and with EP38's established pattern (block, name the reason, write nothing). A stalled money request is strictly worse than a refused one, and the message names the configuration fix. Covered by AC-198-08 (CFL-42-11), which I have also ratified. | KAN-198 |
| **CFL-42-27** | UX-5 | **Nothing stops a `pay_equity` holder dispositioning a finding about themselves.** | Medium | **Ruled: adopt UX's design as an explicit criterion.** The subject may **read** a finding about themselves — hiding it would be worse, and they can see their own pay anyway — but the disposition controls are **absent**, with the stated line. Same family as KAN-139 and KAN-203. **And the follow-on** (UXQ10): where this leaves a finding with no eligible dispositioner, the "no recipient" warning goes on Compensation Settings **and** the Feature Access tab **and** to SYSTEM_ADMIN via the tenant banner — SYSTEM_ADMIN is the only actor guaranteed to be able to see it. | KAN-201 |
| **CFL-42-28** | UX-7 | **The bell's one-click `✓ Approve` would approve a pay change from a line that cannot show the amount.** | **High** | **Ruled: suppress the quick action for any request carrying a pay or level change**; the line shows "Review →". UX is right, and it is the product's own precedent — reject is already a deep link *because a decision without a recorded reason is not auditable*. Approving an amount you cannot see is that failure with money attached. | KAN-196 / KAN-201 |
| **CFL-42-29** | UX-8 | **EP38's shared shell accessibility fixes never landed** — no global `:focus-visible`, no shared live regions, no `prefers-reduced-motion` — so EP42 cannot meet D-004/Q5 standing on them. | **High** | **Ruled: EP42 carries the fix, as KAN-204 in W0, tagged EP33.** D-004's entire logic is *do the cross-cutting thing once rather than twice*; ten new surfaces each inventing a private live region is the doubling D-004 exists to avoid, and it makes the S5 sweep bigger, not smaller. It is the third epic in a row to need them, which is evidence it will not arrive from the epic that owns it. **Tagged EP33 so that epic's scope shrinks honestly** rather than EP42 absorbing someone else's work invisibly. WCAG 2.2 AA on EP42's own screens is **not** renegotiated; what changes is that we stop pretending it is free. | KAN-204 |
| **CFL-42-30** | UAT-F-03 | **`_MONEYISH_KEYS` cannot enforce D5.6** — it matches keys; `reason` is mandatory free text. | **High** | **Ruled in amendment A-2.** Structural guarantee strengthened (closed allowlist); free text governed by design (category + optional text + numeric warning); **and the acceptance criteria must stop claiming what the mechanism cannot deliver.** | KAN-202 |
| **CFL-42-31** | UAT-F-04 | **Four-eyes does not bind the initiator**, so one person raises a pay rise and satisfies level 1 by role. | **High** | **Ruled: the initiator may not decide any level of a money-bearing or level-bearing request.** Added to KAN-198 and to OQ-9's ratification. **Deliberately money-scoped, not universal** — a universal initiator bar would block a legitimate tenant whose only HR_ADMIN raises and approves ordinary transfers. Subject≠initiator and subject≠decider *are* universal and are KAN-203. | KAN-198 |
| **CFL-42-32** | UAT-F-06 | **No minimum group size for displayed aggregates** — a "group average" over two people, shown to someone who knows one of them, is the other's pay exactly. | **High** | **Ruled: no aggregate of any kind rendered below n = 5**, and the configurable minimums are **floored in the database** so they cannot be set below 2. My D1 set minimums for *flags* and I did not think about *displays*. Correct and adopted. | KAN-200 |
| **CFL-42-33** | UAT-F-05 | **`403` on a cross-tenant id is an existence oracle** — it confirms a Telia employee id is real to an Acme admin. EP38 established 403. | Medium | **Ruled: `404` for every EP42 cross-tenant subject substitution**, and the inconsistency with EP38 recorded deliberately rather than discovered. Bringing EP38 into line is a **TD entry for the S5 hardening pass**, not an EP42 story — I am not reopening a shipped epic's error contract mid-build. | KAN-194 |
| **CFL-42-34** | **SPM, new** | **BR-1.6 and UAT-F-01 contradict each other and nobody noticed.** The BA says compare the **rounded** value the UI shows (with a documented effective boundary at 0.9495); UAT recommends carrying ratios **unrounded** into comparisons and rounding for display only. | Medium | **Ruled: BR-1.6 wins — compare the value the UI displays.** The alternative produces findings a user cannot reproduce from what is on their screen, and *"the screen says 0.950 but the system flagged it"* is precisely how trust in a compliance number is destroyed. The effective boundary is documented in the UI, as the BA specified. UAT's F-01 recommendation is amended. | KAN-200 |

### 12.4 Ambiguities ruled (not conflicts — questions with no answer yet)

| Source | Question | **Ruling** |
|---|---|---|
| UAT-F-01, F-01c, F-01e | Money type, rounding mode, subject-in-own-median, FTE range. | **Already answered — BR-1.1, BR-1.5, BR-2.4, BR-2.6 and ADR-014.** `NUMERIC(14,2)`, exact decimal, HALF_UP, FTE 0.01–1.00, subject included. UAT re-reads and un-Blocks the cases. |
| UAT-F-01b | Three boundary inclusivities. | **Ratify UAT's defaults:** coverage gate **inclusive** (evaluate at exactly 80%); justification window **inclusive** (no re-fire on the last day); re-fire delta **strictly greater** than +2.00pp. |
| UAT-F-01d | "Exactly one current record per date" vs "a correction is a new record". | **Ratify UAT's:** permit the same-date append, tie-break by `created_at`, mark the superseded row, "current salary" returns exactly one value. Architect confirms in ADR-015. |
| UAT-F-02 | Is a **negative** gender gap (women paid more) a finding? | **Ruled: flag on `|gap| ≥ threshold` and record the direction.** A pay-equity control that only looks one way is not a pay-equity control. |
| UAT-F-10 / T-OQ-4 | Gender `OTHER` and `NULL` in Check B. | **Ruled: excluded from the two compared medians, counted and shown as an exclusion, never folded into a binary.** That is a data-integrity and a dignity problem at once. DPO input alongside DPO-1. |
| UAT-F-11 | `pct_change_band` edges and the negative case. | **Ratify:** half-open `[0,5) [5,10) [10,20) [20,∞)` on the **absolute** percentage; `direction` carries the sign. |
| UAT-F-07 | A grant that yields nothing looks like a bug. | **Ratify:** the Feature Access tab states the scope consequence next to the grant. **This is now the third ruling of the same shape** (chain overlap at config time, `pay_equity`-without-`compensation` advisory, and this) — so I am naming it a standing rule for EP42: **consequences are shown where the choice is made, not where the surprise lands.** |
| UAT-F-08 / T-OQ-6 | A non-ACTIVE employee's compensation. | **Ruled:** history readable and retained; the record closes at `exit_date`; new records refused except a correction. |
| UAT-F-09 | Does four-eyes bind SYSTEM_ADMIN? | **Ruled: yes** — see Ruling 13, with a condition. |
| OQ-BA-1 | Exempt the **band** basis from the n≥3 minimum? | **Ruled: no — apply both minimums, and here is the better answer.** A group of one compared to a band is a **band-position fact, not an equity finding**, and it *already surfaces* as compa-ratio on the Compensation card. The information is available; it just is not a flag. That resolves the tension without widening what the engine raises. |
| OQ-BA-2 | Inserting a level mid-ladder. | **Ratify the limitation for this cycle** — with the addition that the configurator says so **at the point the ladder is being defined**, not as an error six months later. |
| OQ-BA-3 | `monthly_payments_per_year` on the company or the pay market? | **Ruled: the pay market — I am overruling the BA's own default, on their own evidence.** Acme spans Porto (Portugal, 14 statutory payments), Hamburg and Tallinn (12) **in one company**. A company-level constant is wrong for the only real example we have, by ~17%, which is more than 3× the threshold the feature is built around. A setting that manufactures a finding out of a payroll convention is not a default. Company value is the fallback until pay markets exist. |
| OQ-BA-4 | Does the subject get the promotion-eligible signal? | **Ratify: no.** The implied promise D3.4 warns about. |
| OQ-BA-5 | A "who viewed this salary" read log. | **Ruled conditionally, because the cost estimate changed.** The Architect's ADR-018 funnels every scoped read through one `Scope` resolution point — so this may be **one insert in one service function**, not "a dozen endpoints". **Architect: cost it. If it is ≤ half a day, it lands in KAN-194 as a Should. If it is genuinely a dozen endpoints, it defers and goes in the known-limitations list.** I am not guessing at a number I can have measured. |
| OQ-BA-6 | A second retention clock for pay? | **Ratify: one clock** (EP38's per-company period). DPO confirms. |
| OQ-BA-7 | CSV column `annual_base` → `amount`. | **Ratify the rename.** A column named `annual_base` holding a monthly figure is a factor-of-twelve error waiting for the first customer import. |
| OQ-BA-8 | Band context for the approver at decision time. | **Partly overruling the BA's "not this cycle": yes, but in KAN-205, not KAN-196.** An approver deciding a pay change with no sense of where it lands is a weaker version of the problem that made me suppress the bell quick-approve. It cannot be in KAN-196 because bands do not exist yet. |
| OQ-BA-11 | Is DEF-42-1 fixed inside EP42? | **Ratify: independent defect against EP21** — EP42 did not break it and absorbing it would misattribute the cause. **But P1 and scheduled in S2**, not "sometime before W2": a silent `SKIPPED` with no reason is a live data-integrity defect for anyone importing employees today, and it is the DEF-002 shape. |
| UXQ2 | Level order fixed per family or per level? | **Ratify per family** — UX designed the safe reading. Per-level locking silently renumbers an occupied level, which corrupts the historical group key. |
| UXQ3 | Are salary-change reason categories seeded? | **Ruled: yes, seed a starter list** — `Annual review`, `Promotion`, `Market adjustment`, `Role change`, `Correction`, `Other`, company-editable. A tenant that cannot record a salary on day one is a bad first run. This also supplies the structured half of amendment A-2. |
| UXQ4 | A title→level **suggestion** column? | **Ruled: out of scope this cycle.** It is an assistive inference about job classification — the territory D3.4 and Charter §1 gate. §3.3 already excludes algorithmic classification. Revisit with guardrails if the 75-row sitting proves painful. |
| UXQ5 | An export of current salaries? | **Ruled: design it deliberately, in KAN-202, as a Should.** UX is right that HR asks within a week and that the alternative is someone adding an unaudited CSV button. Row-scoped exactly as the screen is, watermarked with actor and timestamp, and every export audited as `COMPENSATION_EXPORTED` with the row count and scope. |
| UXQ6 | Tell the employee when `compensation_self` is off? | **Ratify UX's "absent".** They cannot act on it and it invites a conversation HR cannot have. Flagged to the DPO with OQ-8. |
| UXQ7 | Notify the subject when their own pay changes? | **Ruled: no notification this cycle.** It is a letter, not a bell, and half-doing it creates an expectation the product cannot meet. Recorded as Later. |
| UXQ8 | May HR record a **contractor's** rate? | **Ruled: yes.** UX's reasoning is my own north star — blocking it pushes contractor rates into a spreadsheet, which is the problem we started with. Recorded, shown, and **excluded from every comparison with the exclusion counted**. Two distinct empty states: "No rate recorded" vs "Not applicable for comparison — contractor rate recorded". |
| UXQ9 | Tenant-configurable `Hide amounts` default? | **Ruled: no per-tenant default this cycle**; UX's off default stands. Ship the usage analytics UX proposed, so the first review answers this with data rather than opinion. |
| UAT-Q9 | A third standalone regression suite? | **Ruled: yes** — `tests/ui/test_compensation_workflow.py`. UAT owns the suite; the **Architect** makes the `CLAUDE.md` amendment (his file) **in the same commit**. |

### 12.5 The two Critical pre-existing defects — ruling

**The finding.** `_can_initiate_for` (`app/routes/org_change.py:55-64`) returns `True` for any holder of
HR_ADMIN / PORTAL_ADMIN / SYSTEM_ADMIN **regardless of who the subject is**; the subject is never compared to the
initiator. `decide()` (`app/services/org_change_service.py:222-249`) compares the decider to the step and the
company **and to nothing else** — never to `req['employee_id']`, never to `req['requested_by_user_id']`.
Together: **an HR_ADMIN who is also an employee can raise a position change for themselves and approve it,
today, on the seeded default chain.** Found independently by the BA (CFL-42-14/15) and UAT (UAT-F-04), and
verified in the code by the coordinator.

**On the documentation-versus-implementation conflict.** `CLAUDE.md`'s headline invariant reads *"An individual
employee can NEVER initiate their own move."* The detailed rule beneath it grants admins a blanket exemption,
and the code matches the detailed rule. **Ruling: the headline is right and the code is wrong.** The exemption
exists so that HR can move *other people* — that is the entire purpose of `_can_initiate_for`. Nothing in KAN-139
or in EP27's history suggests anyone intended it to cover an admin acting on themselves; it is an unnoticed
consequence of expressing "who may act" as a role list without a subject comparison. The Architect (who owns
`CLAUDE.md`) tightens the wording in the same commit as the fix, to say explicitly that **nobody — including
HR_ADMIN, PORTAL_ADMIN and SYSTEM_ADMIN — may initiate or decide a request whose subject is themselves.**

**Ruling on ownership: recorded against EP27, fixed in EP42's W0.** Both halves matter.
- **Recorded against EP27, as DEF-42-4 and DEF-42-5.** That is honest attribution. EP42 did not cause this, and
  filing it as an EP42 acceptance criterion would let a future reader believe the exposure began with
  compensation. It did not; it began when the guard was written.
- **Fixed inside EP42, in W0, as KAN-203, at P0.** Three reasons. (i) The exposure is **live today** — it is a
  self-approved desk move now and a self-approved pay rise the day KAN-196 lands, and "it is only a desk move"
  is not a reason to leave a self-approval hole open for the length of an epic. (ii) My own guardrail says I do
  not recommend GO with an open P0, and I am not going to carry one through four waves. (iii) The guard has
  **no dependency on anything in EP42** and is small, so there is no reason to wait.

**Ruling on the split between KAN-203 and KAN-198.** This is the part that matters technically, and UAT's F-04
is why it has to be stated precisely:

| Rule | Scope | Story | Wave |
|---|---|---|---|
| **Subject ≠ initiator** | **Universal** — every request type, every role, including SYSTEM_ADMIN | **KAN-203** | **W0** |
| **Subject ≠ decider** | **Universal** — every request type, every level, every role | **KAN-203** | **W0** |
| **Initiator ≠ decider** | **Money-bearing or level-bearing requests only** | KAN-198 | W3 |
| **Approver ≠ approver across levels** | Money-bearing or level-bearing only | KAN-198 | W3 |
| **≥2 independently satisfiable levels, refused at create** | Money-bearing or level-bearing only | KAN-198 | W3 |

**Why initiator≠decider is deliberately *not* universal.** A tenant whose only HR_ADMIN raises and approves
ordinary transfers is a legitimate configuration, and a universal bar would break it with no in-app remedy
(TR-20). On money the calculus inverts: a blocked approval is an inconvenience, an unnoticed one-person pay
approval is a finding. Where the cost is asymmetric, take the conservative side — that is the same reasoning as
D4h and it applies the same way here.

### 12.6 The other rulings that changed the plan

**Ruling 13 — four-eyes binds SYSTEM_ADMIN. YES, with one condition.** The Architect asked for an explicit yes
rather than his inference, and he is right to. **Confirmed, and I own the consequence.** Under demo auth
SYSTEM_ADMIN is one login tile away; a control with a hole exactly where the demo identity sits is a screenshot,
not a control. The capability being removed is "one person completes a two-person control", which nobody should
have. **The condition:** a genuinely stuck chain must have a **visible, audited administrative remedy** —
SYSTEM_ADMIN may **cancel** a request (which applies nothing), the chain is reconfigured, the request is
re-raised. **Cancel is not approve.** If no cancel path exists today, KAN-198 adds it; without it, a tenant with
a misconfigured chain has a permanently undecidable request and will edit the database, which is worse than
either option. ADR-022 is amended accordingly.

**Ruling 27 — KAN-168 is the epic's scheduling problem, and it is mine.** It is ⬜ not started and it hard-blocks
KAN-200; the Architect calls it blocker B-1 and it is the same risk as my own R-12 (an engine whose fixtures were
written by its author). **Ruling: KAN-168 is promoted to P0 within the S2 enabler set and is a hard entry
condition for W4. If KAN-168 slips, W4 slips.** EP42 ships through W3 — which satisfies R1, R2, R3, R4, R6 and
R7 — and the equity engine waits. Shipping an equity engine certified against mocks is not an acceptable
alternative, and I would rather deliver six of seven asks with confidence than seven with a number I cannot
defend. **Delivery Manager: schedule KAN-168 now, not when W4 opens.**

**Ruling 32 — KAN-199 splits, which is what CFL-42-21 was really about.** Pay markets are part of the comparison
group key, so they are a **hard** prerequisite of KAN-200 and they carry the annualisation constants that
KAN-193 needs — they move **into W2** as **KAN-199 (Must · P1)**. Salary bands are the comparison *basis*, the
engine is correct without them via the group median, and they are a **soft** dependency — they become **KAN-205
(Should · P2)** in W4. Calling the whole thing "soft" would have left the group key undefined at KAN-200;
leaving it "hard" would have put a large band-configuration exercise on the critical path for no correctness
gain. Neither Wave 2 answer was wrong so much as answering about two different things.

### 12.7 The revised story list and build order

**Eighteen stories, up from fifteen.** Net new scope is two small stories (KAN-203, KAN-204), both paying debts
that are not EP42's fault; KAN-205 is a split of KAN-199, not new work. **I am naming that growth rather than
absorbing it quietly.**

| Wave | Stage | Stories, in build order |
|---|---|---|
| **W0** | **S2** | **KAN-203** (P0 · Critical defect) ∥ **KAN-204** (EP33 debt, gates the first screen) ∥ **KAN-188** (+ the non-session resolver and the JSON denial) ∥ **KAN-189** (second track — unblocks KAN-185 today) |
| **W1** | S3 | **KAN-190** → **KAN-191** |
| **W2** | S3 | **KAN-199** (pay markets) → **KAN-193** → **KAN-194** *(same release)* → **KAN-195** |
| **W3** | S3 | **KAN-196** → **KAN-197** → **KAN-198** → **KAN-192** |
| **W4** | S3 | **KAN-200** → **KAN-201** → **KAN-205** (bands) → **KAN-202** |

**What changed from Wave 1, and why:** KAN-203 and KAN-204 are new in W0 (Rulings §12.5 and CFL-42-29) ·
KAN-199 is redefined as pay markets and moves W4 → W2 (Ruling 32) · KAN-205 is the band half, new in W4 ·
KAN-192 moves to the end of W3, after KAN-197, because the promotion-eligible signal is a dead end until there
is a `LEVEL_CHANGE` request to act on it — shipping the signal first is the DEF-001/DEF-003 failure mode ·
`PROMOTION` becomes `LEVEL_CHANGE` throughout (CFL-42-25).

**Unchanged and confirmed by all four specialists:** W0 first · the ladder before the record before the equity
engine · KAN-194 in the same release as KAN-193 · W2 as the minimum shippable slice.

### 12.8 Questions still needing the product owner

**Nine, unchanged in substance from §6, three sharpened by Wave 2.** All still carry a default the team builds
against today, so none of them blocks.

| # | Sharpened by Wave 2? | Note added in this wave |
|---|---|---|
| **OQ-1** — the level roll-up | — | Still the only story a different answer would **redesign** rather than adjust (KAN-192). The BA and Architect both concur with the "signal, not automatic" default. |
| **OQ-2** — three visibility cells | — | Seed data only. One `seed_rbac.sql` edit. |
| **OQ-3** — what "5%" means | **Yes — materially** | **DEF-42-3: `employees.gender` is NULL for 100% of the seeded population and has no admin collection path.** Check B would report "insufficient gender representation" for every group in every tenant, and **cannot be demoed on seed data**. He should know he may be buying a check that has no data to run on. Put OQ-3 and **DPO-1** (may we lawfully reuse a column collected for vacation eligibility to compute a pay gap?) in **one conversation** — the BA is right that they are not two questions. |
| **OQ-4** — the example ladder | — | Seed data only. |
| **OQ-5** — total compensation | **Yes** | Still the **only** question whose late answer forces a rewrite — of KAN-193's record shape and KAN-200's comparison. The Architect has recorded the additive shape in §10.1 so a "yes" arriving *before* KAN-193 is cheap and a "yes" after it is not. **Ask this one first.** |
| **OQ-6** — multi-currency per market | — | Both populated tenants are single-currency per country, so the default holds today. |
| **OQ-7** — default exposure off | — | One seed value; also a D8 safety default. |
| **OQ-8** — works councils | **Yes** | Now also the trigger for revisiting **CFL-42-22** (the access model cannot express a read-only auditor). If a works-council representative needs company-wide read, that limitation stops being theoretical. |
| **OQ-9** — segregation of duties | **Yes — extended twice** | Now covers **three** rules, not one: approver≠approver (original), **initiator≠approver** (UAT-F-04), and **not bypassable by SYSTEM_ADMIN** (ADR-022b, my Ruling 13). Also confirm the **seeded two-level default chain** for money-bearing types (OQ-BA-10) — without it the control is a silent no-op. Note the **universal** subject≠initiator / subject≠decider rules in KAN-203 are **not** part of OQ-9: they are a defect fix, not a policy choice, and they proceed without ratification. |

### 12.9 Risk register — changes

**Newly Critical, or newly named:**

| # | Risk | Change |
|---|---|---|
| **R-13** *(new)* | **KAN-188 blacks out both populated tenants**, with CI green throughout. | **New, Critical.** The Architect's TR-15. Mitigated by ADR-016(c) and the 330-cell proof gate. This is now the highest-consequence single change in the epic and it is on day one. |
| **R-14** *(new)* | **The four-eyes control ships, passes its tests, and does nothing** — single-level default chain (CFL-42-11) and unbound initiator (CFL-42-31). | **New, High.** Closed by KAN-198's ≥2-satisfiable-levels rule and the seeded two-level chain. Recorded because "the control exists" and "the control works" were nearly two different things, and only the second is worth anything. |
| **R-15** *(new)* | **Check B ships with no data to run on** (DEF-42-3 — gender NULL for the entire seeded population, no admin collection path). | **New, Medium.** Feeds OQ-3. Not a build risk; a *value* risk. |
| **R-1** (alert fatigue) | **Widened.** CFL-42-24 found a second route to it that my own D2 created — a permanently non-zero shared bell badge. My top risk, and my own decision was feeding it. | Mitigation extended: unowned-count badge + `[ Take ]`. |
| **R-3** (a leak through an unlisted surface) | **Widened.** My §4.5.7 enumerated *surfaces* and missed **derivations** — a compa-ratio against a known band is a salary (CFL-42-19). "Inference" is now a category on that list. | Mitigation extended: both-codes rule, DB-floored group minimums, no aggregate below n=5. |
| **R-12** (equity arithmetic wrong) | **Unchanged in substance, now with a named blocker.** KAN-168. | See Ruling 27. |

## 13. Tasking — who does what next, in build order

*This is the section the product owner asked for: everybody has a task. **Nothing in W1–W4 starts until the four
gates in 13.1 clear.** Each task names its owner, its input and what "done" means.*

### 13.1 Gate 0 — four things that must clear before any EP42 code is written

| # | Gate | Owner | Done when |
|---|---|---|---|
| **G-1** | **Wave 2 reconciliation applied.** All four Wave 2 documents updated for the rulings in §12.3 and §12.4. | BA · Architect · UX · UAT | Each document carries a dated "Wave 3 amendments applied" note listing the ruling IDs it absorbed. **This is the Architect's blocker B-2.** |
| **G-2** | **SPM acknowledgement of ADR-016(c).** | **SPM — given, in §12.2 A-1.** | ✅ **Clear.** Ratified with two additions (reversibility statement; estimate includes the proof). **The Architect's blocker B-3 is closed.** |
| **G-3** | **KAN-168 scheduled** with a date, inside S2. | Delivery Manager + DevOps | A dated commitment exists. **If it cannot be committed to, W4 is descoped from this cycle now rather than discovered later.** |
| **G-4** | **OQ-5 answered** (total compensation, in or out). | SPM → product owner | Asked and answered. It is the one question whose late answer forces a rewrite; the other eight can run behind their defaults. |

### 13.2 Immediate — this week

| # | Owner | Task |
|---|---|---|
| 1 | **SPM (me)** | Take **OQ-1, OQ-3+DPO-1 (one conversation), OQ-5 and OQ-9** to the product owner. The other five ride on their defaults. Carry acknowledgements **A-1 through A-4** (§6.1) — especially **A-1: the first real pay figure fires T5 and S5 runs first.** |
| 2 | **SPM (me)** | Open the DPO/legal engagement on **DPO-1** (gender purpose limitation — blocks Check B only) and **DPO-2** (does pay history survive erasure — blocks KAN-193's retention class). The other five DPO items are launch, not build. |
| 3 | **Delivery Manager** | Schedule **KAN-168** (G-3). Add **R-13, R-14, R-15** and **T5** to the Risk Register with named owners. Re-cut the phase plan for **18 stories across W0–W4**, W0 inside S2. Own the standing "environment stays demo-grade" risk that T5 now also depends on (roadmap Q6). |
| 4 | **Senior Architect** | Apply the four report-back items in §12.1; publish **ADR-016 amended** (non-session resolver, JSON denial, reversibility) as the **first** artifact, because it gates W1. Cost **OQ-BA-5** (the read log) against ADR-018's single scope point and come back with a number, not an opinion. |
| 5 | **BA · UX · UAT** | Apply your §12.3/§12.4 rulings (G-1). UAT additionally: **re-read the plan against the BA and Architect files and un-Block the F-01/F-01c/F-01e cases** — they are answered. |
| 6 | **Engineering (any)** | **Nothing in EP42 starts.** Two things you *can* start, because they have no EP42 dependency and both are already-open debts: **KAN-203** (the P0 defect fix) and **DEF-42-1** (the importer, against EP21). |

### 13.3 W0 — stage S2 — four parallel tracks

| Track | Story | Lead | Depends on | Notes |
|---|---|---|---|---|
| **A** | **KAN-203** — subject ≠ initiator, subject ≠ decider | Senior SWE | **Nothing** | **P0. Start immediately, ahead of the gates.** Regression tests that fail without the guard. `CLAUDE.md` invariant 2 reworded in the same commit (Architect). |
| **B** | **KAN-204** — shell a11y A1/A3/A9 | Mid-Level + UX | Nothing | Three shared CSS/HTML additions. **Gates the first EP42 screen.** Tagged EP33. |
| **C** | **KAN-188** — central tenant switch + `feature_access_for()` + JSON denial | Senior SWE · design ARCH | G-1, G-2 | **The highest-consequence change in the epic.** Capture the 330-cell "before" matrix **first**. Estimate includes the proof. |
| **D** | **KAN-189** — effective dating, half-open intervals, DEF-42-2 | Senior SWE | KAN-166 | **Second track from day one.** Closes CFL-4, **unblocks `AC-185-07` on KAN-185, which is stuck today.** Coordinate with whoever is finishing KAN-185 — this is the epic's first visible win and it is somebody else's blocker. |
| — | **DEF-42-1** — the CSV importer | Mid-Level | Nothing | Against EP21. P1, in S2, before KAN-195. |

**Parallel, non-engineering:** UX designs the ladder configurator (KAN-190) and the mapping screen (KAN-191) —
the two hardest screens, and KAN-191 decides whether the backfill finishes (R-2/TR-24). UAT builds the **fixture
cohort** (part-time, contractor, intern, multi-currency, **and gender**, which the seeded data has none of) and
the **negative-visibility approach**, which must be **agreed before KAN-194 is built, not after**.

### 13.4 W1 → W4 — stage S3

| Wave | Stories | Leads | Entry condition |
|---|---|---|---|
| **W1** | KAN-190 → KAN-191 | Mid-Level, review Senior SWE | W0 tracks B and C complete; UX designs signed off |
| **W2** | KAN-199 → KAN-193 → **KAN-194 (same release)** → KAN-195 | Senior SWE (193/194), Mid-Level (199/195) | W1 complete; **CFL-42-2 signed off**; UAT's negative-visibility approach agreed; DPO-2 answered for the retention class |
| **W3** | KAN-196 → KAN-197 → KAN-198 → KAN-192 | Senior SWE (196/197/198), Mid-Level (192) | W2 complete; **OQ-9 ratified** (now three rules); **OQ-1 answered** before KAN-192 |
| **W4** | KAN-200 → KAN-201 → KAN-205 → KAN-202 | Senior SWE (200), Mid-Level (201/205/202) | **KAN-168 landed — hard gate.** UAT's F1–F12 fixtures hand-computed and independent of the engine's author. OQ-3 and DPO-1 answered, or Check B ships dark |

### 13.5 Standing rules for this epic

1. **Consequences are shown where the choice is made, not where the surprise lands.** Chain overlap at
   configuration time · the `pay_equity`-without-`compensation` advisory · the scope consequence beside a grant ·
   the mid-ladder-insertion limitation before the ladder is built. Four instances, one rule.
2. **A guarantee is only stated if the mechanism delivers it.** Amendment A-2 exists because I broke this.
3. **Absent, not hidden.** For every surface, every role: no amount in the payload, not merely none in the DOM.
4. **No story is done until `pytest` and the regression flow test pass with 0 failures**, and the documentation
   the change makes false is fixed **in the same commit** (`CLAUDE.md`; Charter §5b).
5. **A compensation demo without the A-2 disclosure in its written script is NO-GO**, and I will hold that.

*Wave 3 complete. Backlog, roadmap and this document updated together. Nothing in EP42 is Ready, and nothing
should be — S1 closes when the four gates in §13.1 clear.*

---

# 📌 AMENDMENT A1 — THE PRODUCT OWNER'S ANSWERS — 2026-08-09

> **Authoritative. Where this section contradicts anything above it, this wins** — it is the product owner
> answering the questions the earlier sections raised. Source: his reply of 2026-08-09, verbatim in
> `EP42_OWNER_ANSWERS_A1.md` §1.
>
> **D1 and D3 are re-ruled here in full. The originals in §4.1 and §4.3 are left standing and marked superseded
> rather than edited** — the reasoning trail is the point of a decision log, and a decision that quietly rewrites
> itself teaches nobody anything. §14.7 lists exactly what A1 invalidates.
>
> **OQ-1 and OQ-3 are CLOSED.** OQ-5 remains open and is now the last question that can force a rewrite.

## 14. Amendment A1

### 14.0 What the owner actually changed

**One confirmation, one reinterpretation, one authorisation — and the reinterpretation is the one that matters.**

1. **OQ-1 confirmed: progression is not automatic.** My D3.4 ruling stands. But he described a much richer model
   than we specified, and three things in it are genuinely new: **every step carries its own defined
   responsibilities and expectations**; **the manager authors the next step as a forward-looking roadmap for that
   specific employee**, explicitly *for transparency to the employee*, mutually agreed; and **step counts are
   configured per level per company**, not one global default.
2. **OQ-3 reinterpreted: the 5% is not a pay-equity threshold. It is the pay increment between consecutive
   steps.** This is the significant one. It replaces a **statistical** reference with an **absolute** one, and it
   dissolves most of the thin-data problem I measured in Wave 1.
3. **Gender data authorised** for the seeded population, so the gap check has something to run on.

**The honest note on my own Wave 1 work.** I split R5 into two checks and argued hard for it. A1 shows I split it
along the right line for the wrong reason: I split *management action* from *compliance measurement*; what
actually divides them is *absolute* from *statistical*. The split survives. The reasoning behind it does not, and
I would rather record that than let a lucky call look like a good one.

### 14.1 Do I accept the reconciliation of the 5%? **Yes — with one refinement and one caveat.**

The reconciliation offered is: *the step ladder is the legitimate explanation for pay differences within a
position; two people in the same position **should** be paid differently when they are at different steps; what
HR must be told about is the case where **pay and step do not correspond**.*

**I accept it.** It is the only reading that satisfies both of his statements without discarding one, and it is
better than what we had. Two additions:

**Refinement — the two directions are not symmetric, and the owner told us which one he cares about.** His stated
rationale is directional: *"when an employee taking additional responsibility and doing additional job the
employees pay scale should be adjusted."* The failure he is describing is **the responsibility moved and the pay
did not follow**. So:

| Finding | Meaning | Severity | Why |
|---|---|---|---|
| **`PAY_BELOW_STEP`** | Pay is materially below the step's configured pay point | **Primary** | The owner's stated concern. Someone is doing the bigger job for the old money. It also has an obvious, computable remedy |
| **`PAY_ABOVE_STEP`** | Pay is materially above, with no recorded explanation | **Secondary**, lower severity, different copy | Legitimate far more often than not — market premium, red-circled legacy pay, a retention adjustment. Treating it with the same weight as the primary case is how a queue fills with things nobody should act on |

**Caveat — this is an inference, and it should be confirmed rather than assumed forever.** The reconciliation is
a reading of two of his messages, not his words. Logged as **OQ-A1-1** with the default *"build it as reconciled"*
— so nothing waits — and put to him at the next opportunity in one sentence: *"we will tell HR when someone's pay
doesn't match the step they're on; is that what you meant by flagging a difference?"*

**And a point in the reconciliation's favour that is worth stating, because it closes R5 honestly.** The original
ask — *"flag if there is a difference of 5% for the same position"* — is **still delivered**, by construction. Two
people at the same step in the same position are measured against **the same pay point**, so if they are paid
materially apart, at least one of them deviates and is flagged. The correspondence check **subsumes** the
dispersion check. We are not quietly dropping his first request in favour of his second; we are satisfying both
with one mechanism.

### 14.2 D1 — RE-RULED. Pay equity is measured against the step, not against the group.

> **Supersedes §4.1 in full.** §4.1's group formation, group median, `n ≥ 3` minimum, 80% coverage gate and
> band-midpoint basis are **withdrawn for the primary check** and survive only where §14.2.4 says so.

#### 14.2.1 The reference value: a configured **step pay point**

Each **(job level × pay market)** carries a configured **base pay point** — the rate at entry, step `.0`. Each
step above it derives from that base by the **company-defined step increment**. The employee's pay is compared
to **their own step's pay point**. No group, no median, no peers.

**Compounding: each step's pay point is the previous step's uplifted by the increment — compound, not linear.**
Confidence Medium-High. His phrasing is *"in between 1.0 and 1.1 there could difference of some percentage"* —
a gap between **consecutive** steps, which compounds; and his rationale is an adjustment to *that person's* pay,
which is how increments are actually given. With a 5% increment on a base of 60,000:

| Step | Pay point | (linear, for contrast) |
|---|---|---|
| 1.0 | 60,000.00 | 60,000.00 |
| 1.1 | 63,000.00 | 63,000.00 |
| 1.2 | 66,150.00 | 66,000.00 |
| 1.3 | 69,457.50 | 69,000.00 |
| 1.4 | 72,930.38 | 72,000.00 |
| 1.5 | **76,576.89** | 75,000.00 |

The difference across a five-step level is ~2.1% of salary — small enough that engineering would guess either way
and never notice, large enough to be wrong. **Ruled, not left to inference.** Arithmetic follows BR-1.5 (exact
decimal, no intermediate rounding, HALF_UP once at the end).

**The increment is configured per level, with an optional per-step override.** A company may want the last step
of a level worth more than the first. Default: one increment for the whole level.

#### 14.2.2 The tolerance — and the configuration this product must refuse

Real pay will never sit exactly on a computed point. **Correspondence is checked within a company-configurable
tolerance around the step pay point, default ±2%.**

**The non-obvious rule, and the reason it is stated here rather than discovered later: the tolerance must be
strictly less than half the step increment, and the system refuses a configuration where it is not.** With a 5%
increment and a ±5% tolerance, the tolerance bands of adjacent steps **overlap** — every employee is "correctly
paid" for *some* step, and the check means nothing while appearing to work. Validation: `tolerance < increment / 2`,
enforced at configuration time with a message that explains why. This is the most likely way to render the whole
feature useless through a plausible-looking setting.

**A second configuration guard, same principle:** the configurator **warns when a level's base pay point is below
the previous level's top-step pay point** — a promotion that cuts pay. Shown at configuration time, where the
choice is made (standing rule, §13.5.1).

#### 14.2.3 Check A′ — step-pay correspondence *(replaces Check A)*

| | Check A (Wave 1 — withdrawn) | **Check A′ (A1)** |
|---|---|---|
| Question | "Is this person out of line with their peers?" | **"Does this person's pay match the step they are on?"** |
| Reference | Group median, or band midpoint | **Their own step's configured pay point** |
| Unit | One employee vs a group | **One employee, absolutely** |
| Minimum group size | **n ≥ 3** | **None. n = 1 is a valid, meaningful check.** |
| Coverage gate | **80% of the group** | **None** — replaced by per-employee preconditions and a per-company readiness gate (§14.2.5) |
| Thin-data problem | Severe — Acme has one title with n≥3 | **Dissolved** |
| Output | `OUTLIER` | **`PAY_BELOW_STEP`** (primary) · **`PAY_ABOVE_STEP`** (secondary) |

**Per-employee preconditions** (each counted and shown, never silent): a current level **and step** assignment ·
a current compensation record · a resolvable pay market · a configured pay point for that (level, step, market) ·
`employment_status = 'ACTIVE'` · not `CONTRACTOR` or `INTERN`. An employee missing any of these is **"not
evaluable"** with the reason named — not a finding, and not invisible.

#### 14.2.4 Check B — gender pay gap — **survives statistically intact**

**Do not delete the statistical machinery.** Check B is unchanged from §4.1.1 and still needs every part of it:
group formation on `(company, job_family, job_level, pay_market)`, **n ≥ 5**, **≥ 2 of each gender compared**,
median arithmetic including the even-group case, `OTHER`/`NULL` excluded-and-counted, flag on `|gap| ≥ threshold`
with the direction recorded (§12.4). **CFL-42-32 also stands unchanged** — no aggregate of any kind is rendered
below n = 5, and the group minimums stay floored in the database.

**One change:** Check B's group key now **also carries step**, as a reported dimension rather than a grouping one
— a gender gap inside a level is more informative when you can see whether the women in it are systematically at
lower steps. That is a display and drill-down requirement, not a change to the arithmetic.

#### 14.2.5 What replaces the coverage gate: a **ladder-fitted-and-reviewed** gate

The 80% coverage gate existed to stop a statistical reference being computed from half a group. With an absolute
reference that risk is gone — but a **new** one arrives with the backfill, and it is worse if unmanaged.

**The risk:** if the level/step backfill (KAN-191) drops everyone at step `.0`, then every employee whose pay is
above the entry rate — which is most of them — becomes a `PAY_ABOVE_STEP` finding on day one. That is the alert
storm of R-1 returning in a new costume, and it would arrive in the first hour of the first tenant's use.

**The ruling, in two parts:**
1. **The backfill fits the step to the pay, not the pay to the step.** Where a compensation record exists, KAN-191
   places the employee at **the step whose pay point is closest to their actual pay**, and HR overrides where it
   is wrong. This sounds circular and is exactly right for an initial load: the ladder is being fitted to reality,
   because reality came first. Everyone without a pay record defaults to `.0` and is flagged for review.
2. **Check A′ does not run for a company until its level/step backfill is explicitly marked reviewed** by a
   `job_architecture:w` holder. Until then the register shows the review progress, not findings. One gate, one
   deliberate human act, and it is far better targeted than a percentage.

#### 14.2.6 The increment is a **configuration input**, not only a detection threshold

This is the part that changes what the feature *does* rather than what it detects. Because the step pay point is
computable:

- **A step change can propose its own pay adjustment**, pre-filled at the new step's pay point (§14.4).
- **A `PAY_BELOW_STEP` finding carries its own remedy.** The register gets a **"Propose adjustment"** action that
  pre-fills a `COMPENSATION_REVIEW` at the step pay point and routes it through the existing chain. The finding
  and its fix in one place; the finding retires as `RESOLVED` when the pay lands. This is the single most useful
  thing A1 makes possible and it did not exist in any Wave 2 document.
- **HR can see the cost of a ladder before adopting it** — the configurator can total the gap between current pay
  and fitted step pay points. *(Should · P3, KAN-206; named so it is designed for, not bolted on.)*

### 14.3 D3 — RE-RULED. The step is a described job, not a number.

> **Supersedes §4.3.1, §4.3.3 and §4.3.5.** §4.3.4 (no automatic roll-up) is **CONFIRMED** by the owner and
> stands unchanged. §4.3.2 (the example ladder is illustrative) stands.

#### 14.3.1 The objects, restated

| Object | Definition | New in A1? | Authored by |
|---|---|---|---|
| **Job family** | A discipline whose roles are comparable | No | `job_architecture:w` |
| **Job level** | The **position** — Trainee SE, Junior SE, Mid SE. Carries the title, the base pay point per market, and the step increment | No | `job_architecture:w` (title/steps) + `compensation:w` (pay point) |
| **Step** | A rung **within** a level. **The employee enters at `.0`** and climbs `.1 … .N` | **Corrected** — entry at `.0`, not `.1` | — |
| **Step expectation** | **The responsibilities and expectations that define that step**, company-authored per (level, step), readable by every employee | **NEW — the biggest addition in A1** | `job_architecture:w` |
| **Step roadmap** | **The manager's forward-looking statement, for one named employee, of what the next step requires of them.** Purpose: *transparency to the employee*. Mutually agreed | **NEW** | The subject's solid-line manager, or `job_architecture:w` |
| **Working title** | `employees.job_title`, free text, demoted, never a grouping key | No | — |

**Step numbering, pinned down because this is where an off-by-one becomes a wrong salary.** A level's configured
`step_count` is **the number of increments above entry**. A level with `step_count = 5` therefore has **six
discrete step values** — `.0, .1, .2, .3, .4, .5` — and its top-step pay point is the base compounded **five**
times. This matches the owner's own example (`2.0 … 2.5`). A level with `step_count = 3` runs `.0 … .3`.

**Step counts are configured per level, per company. There is no global default of 5.** My Wave 1 "configurable
count, default 5, range 1–12" was close and not right: the count expresses *how much distance there is between
this position and the next one*, and Trainee→Junior and Junior→Mid are genuinely different distances. Range
**1–12** stands as a sanity bound; **there is no default** — the configurator requires an answer per level, the
same way D4c requires the pay question to be answered rather than defaulted.

#### 14.3.2 A fourth feature code — `job_architecture`

> **Amends §4.5.1.** There are now **four** codes, not three.

**Why, and it is not tidiness.** A1 makes **the manager the author of the roadmap**. Under the model I wrote in
Wave 1, ladder writes were gated `compensation:w`, which is seeded to HR_ADMIN and PORTAL_ADMIN only. **A manager
therefore could not do the thing the owner says is their job**, and the only way to let them would be to grant
them write access to everyone's salary. Gating an employee's development roadmap on a *pay* permission is a bad
coupling that would have surfaced as a support ticket in week one.

| Code | Governs | Seeded defaults |
|---|---|---|
| **`job_architecture`** | The ladder, step expectations, step roadmaps. **`r` for everyone** — an employee must be able to read the expectations of their step and the next one, which is the entire stated purpose. **`w`** authors the ladder and any roadmap | `EMPLOYEE` r (and every other role r) · `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w |
| `compensation` · `compensation_self` · `pay_equity` | Unchanged (§4.5.1) | Unchanged |

- **A manager authors a roadmap for their direct reports** via the same service-layer row scoping as pay
  (§4.5.3) — the flag grants the surface, the scope decides the rows. Not a sub-flag; the distinction is already
  written down and now applies to a second feature.
- **The level's base pay point and step increment stay on `compensation:w`** — they are money. The step *count*
  and the step *expectations* are `job_architecture:w` — they are job content. One screen, two gates, exactly as
  ruled for the Compensation Settings page in CFL-42-20.
- **This refines CFL-42-18 rather than reversing it.** The Architect's finding — a `compensation` gate on the
  ladder blanks the directory for everyone — stands and is honoured; the mechanism improves. **An employee's own
  level title displayed on their profile or directory row remains `employee_profiles`** (it is an attribute of
  the person, like their name); **browsing the ladder** is `job_architecture:r`. That boundary also means a
  tenant switching `job_architecture` off does not blank the directory.
- Registered in **all four places**, in **KAN-190** — the first story that needs it. Note deliberately: EP42 has
  no single "register the feature codes" story; each story registers what it needs.

#### 14.3.3 The step roadmap — the object the owner actually asked for

Distinct from the generic step expectation: the expectation says *what step 1.2 means here*; the roadmap says
*what you, specifically, need to do to get there*.

- **Authored** by the subject's solid-line manager (or a `job_architecture:w` holder), for a named employee,
  targeting a named next step.
- **Visible to the employee.** Not optional, not a manager-only note — transparency is its stated purpose. If the
  employee cannot see it, we have not built it.
- **"Mutually decided" is recorded, not enforced.** The employee **acknowledges**, with a timestamp; an
  unacknowledged roadmap is surfaced back to the manager. **I am not building an approval workflow for a
  conversation that happens in a room.** A blocking gate would mean a non-responsive employee freezes their own
  development plan — the opposite of the intent.
- **Versioned, not overwritten.** Roadmaps are re-agreed at each review; the previous one must remain readable,
  because "what did we agree in March" is the question this object exists to answer.
- **No ratings, no scores, no assessment.** It is a statement of expectations, not an evaluation. That boundary
  is what keeps this out of GDPR Art. 22 and EU AI Act territory (Charter §1) and it must not be blurred.

#### 14.3.4 The top-step signal — narrowed

**Amends §4.3.4 and KAN-192.** A1: *"it is indicative for the **reporting manager** to consider him at strong
candidature of promotion, not that it can happen already."*

- The signal goes to **the reporting manager**. My Wave 1 sent it to the manager *and* `compensation:w` holders;
  HR now sees it in the register rather than as a notification. That is a straight noise reduction and it matches
  what he said.
- **It confers nothing** — confirmed, unchanged.
- **New, and it is the more useful half:** A1 says a Junior at 2.3 or 2.4 *"is taking additional
  responsibility"*. **Step position is a live signal readable between promotions, not only a countdown to one.**
  The register and the team view show step distribution, so a manager can see who has quietly taken on scope.
  That is a reporting requirement, and it is where the "pay never followed" cases will actually be spotted.

### 14.4 Ruling — does a step change **propose** or **apply** a pay change? **Propose. Never auto-apply.**

**Confidence High**, and four independent reasons converge:

1. **Internal consistency.** A1's entire answer to OQ-1 is that progression is a human, mutually agreed decision.
   Auto-applying the money would make the pay half automatic while the step half is manual.
2. **It would drive through the four-eyes control.** KAN-198 requires two people on any money-bearing decision.
   An auto-applied pay change has **zero**.
3. **It would drive through the visibility model.** D5 lets a manager *propose* pay and never *apply* it. A step
   change authored by a manager that auto-applied pay would hand every manager a unilateral pay-change lever.
4. **`CLAUDE.md` invariant 3** — nothing is applied until the final level approves.

**The rule.** Advancing a step **pre-fills a `COMPENSATION_REVIEW`** with the new step's pay point as the proposed
amount and routes it through the existing chain. The increment's value is that the manager no longer has to work
the number out — not that nobody has to approve it. The pay decision is **mandatory to answer and may be "no
change" with a recorded reason**, exactly as D4c requires of a position change.

**And the deliberate consequence, which is a feature and not a gap:** the step change may land **before** the pay
does. That produces precisely the `PAY_BELOW_STEP` condition Check A′ exists to detect — *"they took the
responsibility, the pay never followed"*. The two halves of A1 fit together: the step change is allowed to move
first, and the correspondence check is the mechanism that makes sure the pay eventually catches up. Nothing needs
to force them into the same transaction, and forcing it would block a legitimate case (the adjustment is
budgeted for next quarter).

**Flagged for confirmation as OQ-A1-2**, default "propose". The step change itself does **not** go through the
approval chain — it is within-position job content, audited, with a mandatory review context and the employee's
acknowledgement. A **level** change (promotion) does go through the chain; that is KAN-197, unchanged. No bypass
exists: the step has no chain, the money always does.

### 14.5 Ruling — the performance-review coupling. **Record the context. Do not build performance management.**

**I agree with the recommendation, and I want the boundary in one sentence the owner can read:**

> **EP42 records that a step change happened at a review. It does not build the review.**

**Why.** Performance management is a distinct product surface in its own right (Charter §1) — cycles, goals,
ratings, forms, calibration, scheduling, reminders. It is comfortably larger than the whole of EP42. None of
`performance`, `probation`, `goal`, `review` or `objective` exists anywhere in the schema. And nothing he said
asks us to build it: *"during performance review process manager discuss about his current level"* anchors the
step conversation **to** a review that already happens, wherever it happens today. Time-to-value beats
completeness, and a step-change event that records *"agreed at the mid-term goal review on 12 March, here is the
roadmap"* delivers the transparency he asked for now, where a goals module delivers it in a year.

**What EP42 therefore does:** a step change carries a **mandatory `review_context`** — `PROBATION_REVIEW` ·
`MID_TERM_GOAL_REVIEW` · `PERFORMANCE_REVIEW` · `OFF_CYCLE` — plus a review date and an optional note.
**Mandatory to answer, with an off-cycle option**, mirroring D4c: an unanswered context means the question fell
on the floor.

**What EP42 explicitly does NOT do — stated plainly so he is not surprised later:** no review cycles, no
scheduling, no reminder that a probation review is due · no goals, objectives or key results · no ratings,
scores or calibration · no review forms or templates · no enforcement that a step change *must* occur at a
review (the context is recorded, not required) · no probation entity, no probation end date, no probation
outcome.

**Recorded in the roadmap's Later list as a candidate epic — Performance, Goals & Reviews — not numbered and not
scoped.** If he wants it, it is a conversation about a new epic, not an expansion of this one. **I would rather
tell him that now than deliver two thirds of a performance module by accident.**

### 14.6 Gender data — authorised, and it is a story

*"For the gender you can assign random gender to all employees."* `employees.gender` is NULL for 100% of the
seeded population (DEF-42-3), which is why Check B had nothing to run on.

**Ruling: accepted as a synthetic-data task, delivered as a story — KAN-208 — not as a hand edit.** The dev
database is built by hand and the CI database from `schema.sql` + the seed files; updating one and not the other
is exactly the DEF-004 trap that broke CI on 9 August. The change lands in the seed files **and** a migration.

**Three limits I am attaching, and they are not negotiable:**
1. **Synthetic only.** This authorises assigning values to seeded fictional people. It does **not** authorise
   collecting gender from real people, and T5 is unaffected.
2. **DPO-1 still stands.** Having data does not make processing it lawful. The purpose-limitation question — a
   column collected for vacation eligibility, reused as an input to an employment-related pay check — is
   untouched by this, and gender is a special category under GDPR Art. 9 on most readings. **Check B remains
   gated on DPO-1.**
3. **Distribution must be plausible, not uniform-random per row.** A coin-flip across 146 people will not
   reliably produce a group with ≥2 of each gender at n≥5, so the check would still be undemonstrable. The
   assignment is **deterministic and seeded** so it is reproducible, and shaped so at least two comparison groups
   satisfy Check B's minimums. Otherwise we have done the task and not solved the problem. `OTHER` is included in
   the population, because §12.4 requires it to be excluded-and-counted and that path needs a fixture.

### 14.7 What A1 invalidates — the explicit list

**Withdrawn or superseded:**

| # | What | Status | Where it went |
|---|---|---|---|
| 1 | **D1's group median as the primary reference** | **Superseded** | §14.2.1 — the step pay point |
| 2 | **D1's `n ≥ 3` minimum, for the primary check** | **Withdrawn** | Not needed; n=1 is valid. **Retained in full for Check B** |
| 3 | **D1's 80% coverage gate, for the primary check** | **Withdrawn** | Replaced by per-employee preconditions + the ladder-fitted-and-reviewed gate (§14.2.5). **Retained for Check B** |
| 4 | **D1's "band midpoint is the primary basis where a band exists"** | **Superseded** | The step pay point is the basis. Bands become the level's min/max **envelope** |
| 5 | **D1's compa-ratio 0.95/1.10 thresholds for Check A** | **Superseded** | Replaced by the ±2% tolerance around the step pay point |
| 6 | **The meaning of "5%"** | **Reinterpreted** | It is a **configuration input** (the increment), not a detection threshold. The detection number is now the **tolerance**, a different value with a different default |
| 7 | **D3's "steps display `<level>.<step>`, count default 5, range 1–12"** | **Amended** | Entry at `.0`; count = increments above entry; per level per company; **no default** (§14.3.1) |
| 8 | **D3.5's "bands attach to level × pay market and are the comparison basis"** | **Amended** | The **pay point** attaches there and is the basis; bands are the envelope |
| 9 | **§4.5.1's three feature codes** | **Amended to four** | `job_architecture` added (§14.3.2) |
| 10 | **CFL-42-18's resolution** (ladder reads on `employee_profiles`) | **Refined, not reversed** | Ladder reads on `job_architecture:r`; the employee's own level title stays `employee_profiles` |
| 11 | **D3.4's signal recipients** ("manager and `compensation:w` holders") | **Narrowed** | The reporting manager only |
| 12 | **OQ-BA-1** (exempt the band basis from n≥3?) | **Moot — closed** | There is no group minimum on the primary check to exempt |
| 13 | **UAT fixtures F1, F4, F5, F9, F11** (group median, group-size minimums, coverage gate, even-group median, subject-in-own-median) | **Re-scoped to Check B, or withdrawn** | They tested a statistical Check A that no longer exists. **F3, F6, F7, F8, F12 survive unchanged** |
| 14 | **UAT-F-01c / F-01b's coverage-gate boundary** | **Partly moot** | The gate boundary question dies with the gate; the justification-window and re-fire-delta inclusivities stand |

**Explicitly NOT invalidated — stated so nobody re-opens settled work:** the wave model and W0's contents ·
KAN-203, KAN-204, KAN-188, KAN-189 in every detail · **the no-automatic-roll-up ruling, which the owner
confirmed** · KAN-194 shipping with KAN-193 · every four-eyes ruling · every audit/money ruling including
amendment A-2 · the tenant switch and ADR-016 · **CFL-42-32** (no aggregate below n=5) · the pay-market concept ·
the `LEVEL_CHANGE` rename · everything else in §12.

### 14.8 Knock-on effects — stories, waves, build order

**Three new stories. Twenty-one total.** Numbering continues contiguously from KAN-205.

| Story | Why it exists | Wave | MoSCoW · P |
|---|---|---|---|
| **KAN-206** | **The step pay-point model** — base pay point per (level, pay market), the step increment with optional per-step override, the tolerance, and the two configuration guards (`tolerance < increment/2`; a level base below the previous level's top step). This is now **the reference value for the entire equity feature** and a hard prerequisite of KAN-200 and KAN-192 | **W2** | Must · P1 |
| **KAN-207** | **The step roadmap and employee transparency surface** — the manager authors the next step for a named employee, the employee reads and acknowledges it, versioned across reviews. This is the object the owner actually asked for, it has **no compensation dependency**, and it gives W1 a user-visible outcome instead of only configuration | **W1** | Must · P1 |
| **KAN-208** | **Assign synthetic gender across the seeded population** — seed files **and** a migration, deterministic, shaped so at least two groups satisfy Check B's minimums | **W0** | Must · P2 |

**Changes to existing stories:**

| Story | Change |
|---|---|
| **KAN-190** | **+** step **expectations** content per (level, step) · **+** registers the **`job_architecture`** feature code in all four places · **+** steps numbered from `.0`, count = increments above entry, **per level, no default** · ladder reads move to `job_architecture:r` · the two configuration guards live on the joint screen with KAN-206 |
| **KAN-191** | **+** assignment carries a **step**, not only a level · **+** the backfill **fits the step to the pay** (closest pay point), with HR override · **+** the **fitted-and-reviewed** gate that Check A′ waits on · employees with no pay record default to `.0` and are flagged for review |
| **KAN-192** | **+** mandatory **`review_context`** (probation / mid-term goal / performance / off-cycle) + date + note · **+** advancing a step **pre-fills a `COMPENSATION_REVIEW` at the new step's pay point and never applies it** · **+** the pay answer is mandatory and may be "no change" with a reason · the top-step signal narrows to **the reporting manager** · **+** step position as a live report of scope taken on. Now depends on **KAN-206** |
| **KAN-199** | Unchanged in scope; it is now also the container the per-market pay points in KAN-206 attach to |
| **KAN-200** | **Substantially re-specified.** Check A → **Check A′**, absolute, per employee, no group minimum, no coverage gate, tolerance-based, two finding types with **asymmetric severity**. **Check B unchanged.** **+** the ladder-fitted-and-reviewed gate. **−** group median arithmetic for the primary check |
| **KAN-201** | **+** finding **types** with distinct copy, severity and disposition categories (`PAY_BELOW_STEP` · `PAY_ABOVE_STEP` · `GENDER_GAP`) · **+** a **"Propose adjustment"** quick action on `PAY_BELOW_STEP` that pre-fills a `COMPENSATION_REVIEW` at the step pay point and retires the finding as `RESOLVED` when the pay lands |
| **KAN-205** | **Repositioned**, not resized. Bands are the level's **min/max envelope** ("is this pay sane for this level at all?"), no longer the comparison basis. Stays **Should · P2, soft** |
| **KAN-202** | **+** the step and roadmap timeline shown alongside the pay timeline — "how did this person get here" is one story, not two |

**Revised build order — 21 stories:**

```
W0  S2   KAN-203(P0) ∥ KAN-204 ∥ KAN-208 ∥ KAN-188 ∥ KAN-189
W1  S3   KAN-190 → KAN-191 → KAN-207          ← job architecture, no money in it, employee-visible
W2  S3   KAN-199 → KAN-206 → KAN-193 → KAN-194(same release) → KAN-195
W3  S3   KAN-196 → KAN-197 → KAN-198 → KAN-192
W4  S3   KAN-200 → KAN-201 → KAN-205 → KAN-202
```

**W1 is now a better wave than it was.** It ends with a complete, shippable job-architecture slice — a ladder, a
described set of expectations, everyone placed on it, and every employee able to read what their next step
requires — with **no compensation data involved at all**. That is real value the owner can see before any pay
question is settled, and it is the sequencing A1 makes possible. **W2 remains the minimum shippable slice for
the epic as a whole.**

### 14.9 Risk and question register — changes

| # | Change |
|---|---|
| **R-1** (alert fatigue) | **Reduced for the primary check** — an absolute reference produces far fewer, far more actionable findings than a 5% dispersion rule ever would. **But a new route opened and is closed in §14.2.5:** a naive `.0` backfill would flag most of the workforce in the first hour. The fitted-step backfill and the reviewed gate are the mitigation, and they are acceptance criteria, not intentions |
| **R-2** (the mapping is a data project) | **Worsened, and I am saying so.** It is no longer "map 116 titles to levels" — it is "map them to levels **and fit a step to each person**". The fitted-step default does most of it automatically, which is why it is designed that way, but HR's review is now the gate on the whole equity feature |
| **R-15** (Check B has no data) | **Closed by KAN-208**, subject to the distribution requirement in §14.6.3 |
| **R-16** *(new)* | **A plausible configuration silently disables the check** — tolerance ≥ half the increment makes adjacent bands overlap so everyone is "correct". **Medium × High.** Closed by the §14.2.2 validation |
| **R-17** *(new)* | **The step roadmap drifts into performance management** — ratings, scores, an assessment surface — through entirely reasonable-sounding increments. **Medium × High.** Closed by §14.5's exclusion list and §14.3.3's "no ratings, no scores" rule, which UX and the BA must both hold |
| **OQ-1** | **CLOSED.** Confirmed: not automatic |
| **OQ-3** | **CLOSED**, by reinterpretation. Re-ruled in §14.2 |
| **OQ-5** | **STILL OPEN, and now the last question that can force a rewrite.** Base salary only remains the default. Note it got slightly worse: the step pay point is a **base** pay point, so a later "total compensation" answer would change what the increment applies to as well as the record's shape |
| **OQ-6** | Unchanged, and less pressing — an absolute per-market reference never crosses currencies |
| **OQ-A1-1** *(new)* | Confirm the reconciliation of the 5% (§14.1): *"we will tell HR when someone's pay doesn't match the step they're on — is that what you meant?"* **Default: build it as reconciled.** |
| **OQ-A1-2** *(new)* | Confirm that advancing a step **proposes** a pay change rather than applying one (§14.4). **Default: propose.** |
| **OQ-A1-3** *(new)* | Confirm the boundary in §14.5 — **EP42 records that a step change happened at a review; it does not build the review.** **Default: as stated.** This is the one most likely to produce a surprise later, so it should be said out loud rather than filed |

## 15. Wave 4 — the amendment round

*Each brief names the sections A1 invalidates and what to change. Precise enough to act on without re-deriving A1.
Nothing here is a re-write from scratch — the Wave 2 documents are sound; A1 changes the reference value, adds
two objects and adds a feature code.*

### 15.1 Business Analyst

**Invalidated:** §4.4 (the pay-equity engine — group formation, coverage gates, Check A) in large part · §4.5
(the job ladder validity rules) · **AC-200-01…AC-200-23** (Check A) · the parts of AC-195-* and AC-191-* that
assume level-only assignment · §3.2's feature-access model (three codes).

1. **Rewrite §4.4's Check A as Check A′** — absolute, against the step pay point; no `n ≥ 3`, no coverage gate,
   no group median. **Keep §4.4's Check B arithmetic exactly as written** and add step as a reported dimension.
2. **New business rules** for: compound step-pay-point derivation (§14.2.1) · the tolerance and the
   **`tolerance < increment/2`** refusal (§14.2.2) · the two finding types and their asymmetric severity ·
   per-employee evaluability preconditions · the ladder-fitted-and-reviewed gate.
3. **Amend §4.5** for entry at `.0`, `step_count` = increments above entry, per level, **no default**, and the
   six-values-for-count-5 arithmetic.
4. **New criteria for KAN-206, KAN-207, KAN-208.** KAN-207 is the one to spend time on: authoring, the
   employee's view, acknowledgement, versioning, and the **"no ratings, no scores"** boundary as a testable rule.
5. **Amend §3.2 to four feature codes**, `job_architecture` registered in KAN-190.
6. **Amend AC-191-*** for step assignment and the **fitted-step backfill**.
7. **Amend AC-192-*** for `review_context`, propose-not-apply, and the narrowed signal recipient.
8. **Close OQ-BA-1** as moot. Re-check §21.4 — several contingencies died with Check A.

### 15.2 Senior Architect

**Invalidated:** **ADR-023** (pay-equity computation) substantially · **ADR-017** (job architecture) in its step
model · the §3.2 and §3.6 table sets · §5.2's three-code registration.

1. **Re-cut ADR-023.** The primary computation is now a **per-employee** comparison against a configured value,
   not a group aggregate. This should be **cheaper and simpler** — no `percentile_cont`, no group windowing for
   Check A. **Keep the group machinery for Check B.** Re-run the cost model; it should improve.
2. **New tables** for step expectations, step roadmaps (**versioned**), and the pay-point/increment/tolerance
   configuration. Design the roadmap for **versioning from the start** — re-agreed at each review, and the prior
   version must stay readable.
3. **Amend ADR-017** for entry at `.0` and the count semantics. **Confirm the six-discrete-values-for-count-5
   reading in the schema**, with a constraint, because this is where an off-by-one becomes a wrong salary.
4. **Rule on the pay-point derivation's storage** — computed on read, or materialised? It is read on every
   evaluation and every step-change proposal. My steer is computed, consistent with CFL-42-16's
   "current is computed, never stored", but it is your call and the cost is yours to weigh.
5. **Add `job_architecture`** as a fourth code, registered in KAN-190, all four places. Confirm the
   `job_architecture:r`-vs-`employee_profiles` split in §14.3.2 does not re-open CFL-42-18.
6. **The `tolerance < increment/2` validation** — where does it live so it cannot be bypassed by direct SQL or
   by an import? Same question for the level-base-below-previous-top-step warning.
7. **KAN-208's migration + seed** — deterministic and reproducible, per the four-place logic. This is a data
   change and DEF-004 is the precedent.
8. Confirm **propose-not-apply** composes cleanly: a step change writing a `COMPENSATION_REVIEW` request from
   `job_architecture_service` is a cross-service call, and §2.2's one-way call rule applies.

### 15.3 UX / Product Designer

**Invalidated:** §6 (the ladder configurator) needs the expectations editor · §8 (progression) needs review
context and the pay proposal · §14 (the equity register) needs new finding types and the remedy action ·
§3.1's surface map needs a fourth code.

1. **The step-expectations editor**, inside the ladder configurator. Substantial authored content per step —
   this changes §6 from a structural editor into a content editor, and the empty state matters more than ever.
2. **KAN-207, the roadmap — the most important new screen, and I want it treated that way.** Two audiences with
   different needs: the **manager** authoring for one person, and the **employee** reading it. Its purpose is
   transparency, so the employee's view is the primary one. Acknowledgement, version history, and — the hard part
   — **copy that reads as expectations, not as an assessment, and does not imply a promise.** Same discipline as
   "My Pay" and the top-step signal, applied to the most easily misread object in the epic.
3. **Progression (§8):** the `review_context` selector, and the pay proposal shown as **a proposal going to
   approval** — never as a change that has happened.
4. **The register (§14):** three finding types with distinct copy and severity, and the **"Propose adjustment"**
   action on `PAY_BELOW_STEP`. Design that as the primary path — a finding that carries its own remedy is the
   best thing A1 gives us.
5. **The configuration guards** (§14.2.2) — both are consequences shown where the choice is made, which is your
   established pattern. The tolerance one needs copy that explains *why* it is refused, not just that it is.
6. **The fitted-step backfill review screen** — HR confirming a fitted step per person, at 146 people. This gates
   the entire equity feature and it is the same adoption-cliff problem as the title mapping.
7. `job_architecture` in the §3.1 surface map, and what "no access" looks like for it.

### 15.4 UAT Lead

**Invalidated:** fixtures **F1, F4, F5, F9, F11** as Check-A fixtures · **UAT-F-01b's coverage-gate boundary** ·
the KAN-200 case set (34 cases) substantially · **UAT-F-06** stands, **F3, F6, F7, F8, F12** survive.

1. **New arithmetic fixtures** — the ones that matter most, and hand-computed as before: **compound step pay
   points across a 5-step and a 3-step level** (with the linear values alongside, so a linear implementation
   fails loudly) · **tolerance boundaries** at exactly ±2%, just inside and just outside · **the
   `tolerance ≥ increment/2` refusal**, and proof that the overlapping-bands configuration is impossible to save ·
   **the fitted-step backfill** — given a pay and a ladder, which step is chosen, including exact ties.
2. **Re-scope F1/F4/F5/F9/F11 to Check B**, or withdraw them, and say which. Check B's statistical cases must not
   be lost in the clear-out — that is the risk in this particular amendment.
3. **New cases for KAN-206, KAN-207, KAN-208.** For KAN-207 include the negative-visibility angle: an employee
   must see **their own** roadmap and **not** a colleague's, asserted at the payload.
4. **The step-change-proposes-pay path** — assert that a step change **never** writes a compensation record
   directly, and that the pre-filled request is a normal request subject to four-eyes.
5. **KAN-208's distribution** — assert that at least two comparison groups satisfy Check B's minimums after the
   seed, and that `OTHER` is present. A gender assignment that leaves Check B undemonstrable has not done its job.
6. **Add to §7.3's must-be-walked-by-a-human list:** does the roadmap read as expectations rather than as a
   performance rating? That cannot be asserted, and it is the §14.5 boundary holding or failing in practice.

*Amendment A1 applied. Backlog updated in the same pass. OQ-1 and OQ-3 closed; OQ-5 remains the open question
that can still force a rewrite, and OQ-A1-1/2/3 carry defaults so nothing waits.*

---

# ⚖️ WAVE 5 — FINAL RECONCILIATION — 2026-08-09

> All four specialists amended in place against A1. **Nobody attacked A1's shape**, and all four converged on the
> same handful of problems from different angles — which is the strongest evidence available that the model is
> right. What they collided on is IDs and mechanism, and this pass fixes both.
>
> **One ruling in §16.2 changes the mechanism of the primary check.** It is a simplification: it dissolves four
> separate Wave 4 conflicts at once and deletes work rather than adding it. Read that one first.

## 16. Wave 5 reconciliation

### 16.1 Review verdict on each amendment (Charter §7)

| Report | Verdict | What earns it | Sent back |
|---|---|---|---|
| **Business Analyst** — 736 ACs (was 532), new §0 amendment history | **ACCEPT** | Nothing deleted, everything superseded and marked. They found **the build-order defect I shipped** (CFL-42-41), **the seed that contradicts its own justification** (CFL-42-35), and — the one that matters most — they went and **looked at what `employees.gender` is actually used for** and logged their own earlier assumption as **KNOWN TO BE FALSE**. That is the assumption register doing the job it exists for, and it only worked because somebody checked rather than reasoned. | Three items, all from §16.2's ruling: BR-10.7a/b and AC-206-09/10 are **withdrawn**, not amended — the constraint they specify no longer exists. Re-scope the tolerance to a Tier-2 quality measure. |
| **Senior Architect** — 21 stories, 175 tasks, ADR-024/025, ADR-023 re-cut, critical path 71 days | **ACCEPT** | ADR-024's compounding walk-through and ADR-025's **forbidden-column table** are the right shape. **V18 is the entry I want to single out:** he found that the four-eyes control he designed *"would have shipped, passed its tests, and bound nobody"* — `org_change_workflows` returns **0 rows**, every tenant is on a single-HR_ADMIN default chain — and he led with it as the thing he got most wrong rather than burying it. **That is exactly the behaviour that makes a design review worth having.** | **CFL-42-45 dissolves — you keep the guarantee *and* the permission boundary** (§16.2). ADR-024's tolerance CHECK is withdrawn. ADR-023's Check A′ boundary becomes derived, not configured. All three are deletions. |
| **UX / Product Designer** — §22–§26, 42 new ACs | **ACCEPT** | Four conflicts raised and **complied with rather than designed around**, which is the standard. **UX-A1-C4 is the best of them:** they applied amendment A-2's own rule — *a guarantee is only stated if the mechanism delivers it* — to a **button label**, and refused to write "Accept" over a mechanism that only records "read". A-2 was written about audit diffs; they generalised it correctly to language, and I am promoting it to a standing rule (§16.6). | One: **UX-A1-C3's two-step cap becomes a one-step rule with a routed alternative** (§16.4) — principled rather than arbitrary, and it preserves the capability. |
| **UAT Lead** — 399 cases, §5.0 fixture disposition | **ACCEPT, and the strongest single contribution of the wave** | They **withdrew F-01/F-01c/F-01e**, accepting my Wave 3 correction without argument; **found two errors in their own fixtures**; caught **a contradiction between two of my own sections** (UAT-F-17 — §14.7 called the coverage-gate boundary invalidated while §14.7 item 3 retained the gate for Check B; they are right and I was inconsistent); and produced **F18**, which quantified a structural noise problem nobody else saw. | Nothing. F18's mitigation is superseded by §16.2 — which **eliminates** the problem rather than mitigating it — and that is a better outcome than the one they asked for. |

**The pattern worth recording:** every one of the four found a defect in *my* work this wave, and three of them found one in *their own*. That is a team operating properly. The things I would still be shipping wrong without them: a build order that guarantees the alert storm it was designed to prevent (BA), a four-eyes control binding nobody (Architect), a false claim on a button (UX), and a check that flags 20% of a correctly-configured workforce (UAT).

### 16.2 THE RULING THAT MATTERS — the nearest-step rule

> **Supersedes §14.2.2's tolerance-as-finding-boundary.** This dissolves **CFL-42-36, CFL-42-37, CFL-42-45,
> CFL-42-51 and UAT-F-15** in one move, and it removes work from three specialists.

**The problem UAT found (F18), and it is arithmetic, not opinion.** Because §14.2.2 required the tolerance to be
**strictly less** than half the increment, there is necessarily a band in which an employee is **correctly fitted
and still flagged**. Covered fraction of the pay space is `2t/i`; with a 5% increment and ±2% tolerance that is
80%, leaving **1 percentage point in every 5 outside every step's tolerance**. Their fixture: **4 findings from
10 perfectly-fitted employees.** Nobody did anything wrong; the geometry produced them.

**And the collision nobody spotted, which is the clearest evidence the mechanism was wrong.** The BA's fix for
CFL-42-37 was to express the default relatively as **`tolerance = increment ÷ 4`**. Substitute it: `2t/i = 0.5`,
so the dead zone **doubles from 20% to 50%**. The fix for one conflict makes the other twice as bad, and both
authors were right within their own frame. When two correct fixes fight, the thing they are both fixing is the
wrong mechanism. Logged as **CFL-42-53**.

**The ruling — two tiers, and the finding boundary is derived, not configured:**

| Tier | Rule | Raises a finding? |
|---|---|---|
| **Tier 1 — a finding** | **The employee's pay is nearer to a *different* step's pay point than to their own.** They are recorded at 2.4 and paid like 2.2 | **Yes** — bell, badge, register, per D2 and the severity split in §14.1 |
| **Tier 2 — a quality measure** | Pay is nearest to their own step but outside the configured tolerance — "close, not on the point" | **No.** Never a finding, never a notification. Shown on the **ladder-fit-quality report** and on the compensation card |

**Why this is right, not merely convenient:**

1. **The dead zone becomes exactly zero, by construction.** Every pay figure is nearest to *some* step. If it is
   nearest to its own, correspondence holds as well as this ladder's granularity allows — which is not a finding,
   it is a fact about the ladder. If it is nearest to another, that is a genuine mismatch. There is no band left
   over, at any increment, with any configuration.
2. **A fitted backfill produces zero Tier-1 findings on day one** — because fitting *means* choosing the nearest
   step. That is the right day-one experience and it is what §14.2.5 was reaching for.
3. **It still catches everything the feature exists to catch.** A single unfollowed step advance moves the
   expected point by one full increment; the resulting deviation (−4.76% at 5%) is comfortably past the half-
   increment boundary. Two people at the same step paid 10% apart: at least one crosses it. **R5 is still
   satisfied by construction.**
4. **It removes a configuration knob that could silently disable the check** — R-16, which I raised in §14.9 and
   which the `tolerance < increment/2` rule existed to police. There is now no cross-field constraint to
   validate, so there is nothing to get wrong.
5. **It is explicable to an HR user.** *"Ravi is recorded at step 2.4 but paid closer to step 2.2"* is a sentence
   somebody can act on. *"Ravi's ratio is 0.953 against a ±2% tolerance"* is not.
6. **I am correcting my own invention, not the owner's.** He specified the increment. The tolerance was mine,
   in §14.2.2, and it was the wrong instrument for the job I gave it.

**The trade-off, stated:** the Tier-1 sensitivity is no longer tunable. A company wanting finer detection
**shortens the increment** — i.e. says something true about its ladder — rather than turning a detection dial.
I regard removing that dial as a gain (R-16), and it is the one thing to revisit if a first tenant disagrees.

**What each specialist deletes:** BA — BR-10.7a/b, AC-206-09/10, the `min(increment)/2` rule. Architect —
ADR-024's tolerance CHECK, the cross-permission-domain problem in **CFL-42-45 dissolves entirely: he keeps both
the guarantee and the permission boundary**. UAT — F18's mitigation; the dead-zone cases become
assertions that Tier 1 raises **nothing** from a perfect fit. The tolerance survives only as a Tier-2 display
value, default ±2%, stored with the increment on `compensation:w`, with **no constraint against it**.

### 16.3 The single authoritative conflict register (Wave 5)

**CFL-42-35, -36 and -37 were each allocated by both the BA and the Architect to different conflicts.** This
table governs. The *Source* column maps every prior ID.

| Authoritative | Source | Conflict | Sev | **SPM ruling** |
|---|---|---|---|---|
| **CFL-42-35** | **BA-35 + ARCH-35 — merged** | Two halves of one problem: the manager cannot author the roadmap `job_architecture` exists for (BA); and ladder configuration must not ride the same grant as roadmap authoring (Architect). | **High** | **Adopt both fixes — either alone leaves the other's problem open.** Three gates: **reads** `job_architecture:r` (everyone) · **roadmap writes** `job_architecture:w`, **seeded to `SOLID_LINE_MANAGER`**, row-scoped to their DIRECT set · **ladder configuration** `org_structure:w` — seeded HR_ADMIN + PORTAL_ADMIN, **no manager**, no seed change, in-repo precedent at `org_change.py:381`. The Architect's split alone left the manager without `w`; the BA's seed alone handed managers the company's job architecture. **Consequence:** `job_architecture:w` now governs *roadmaps only*, so its **label and description on the Feature Access tab must say so** — "read the job ladder; write step roadmaps for your reports" (standing rule §13.5.1). |
| **CFL-42-36** | BA-36 | `tolerance < increment/2` under-specified against per-step overrides; should be `min(increment)/2`. | High | **DISSOLVED by §16.2.** There is no cross-step tolerance constraint. Per-step overrides are handled naturally — the Tier-1 boundary is the midpoint between adjacent pay points, well-defined whatever the increments. |
| **CFL-42-37** | BA-37 | The ±2% default is arithmetically unsatisfiable for any increment ≤ 4%. | Medium | **DISSOLVED by §16.2**, and the proposed fix (`÷4`) is itself logged as **CFL-42-53** for doubling the dead zone. |
| **CFL-42-38** | BA-38 | A1's step-distribution report breaches my own CFL-42-32 n≥5 aggregate floor. | High | **Ratify the BA's position.** Distribution rendered only at `|compared| ≥ 5`, and only to holders of **both** codes where any value is invertible. My §14.3.4 asked for a report that my own §12.3 forbids; the BA is right. |
| **CFL-42-39** | BA-39 | A1 opened a **new pay-inference channel**: `job_architecture:r` is seeded to everyone and §14.3.4 makes step position visible — base pay point + published increment + known step = that person's pay. | **High** | **Ratify BR-5.5a.** Own step always visible · **another employee's step is scoped exactly as their pay is** · level title and generic step expectations stay public. **This is CFL-42-19's class arriving through a door A1 opened, and my amended surface list should have caught it.** The seeded default is right for the object the code was created for and wrong for a second one that shares it. |
| **CFL-42-40** | BA-40 | `review_context` is mandatory, but no A1 context is true of a 146-row bulk load. | Low | **Ratify:** a fifth value **`INITIAL_LOAD`**, available only to the backfill path, never human-selectable. Requiring a human context on a bulk load would be answered dishonestly, which is worse than not asking. |
| **CFL-42-41** | BA-41 | **The build order puts the story needing pay points a wave before the story creating them.** KAN-191's fitted backfill (W1) fits against KAN-206's pay points (W2). Run as ordered, everyone lands at `.0` — the exact storm §14.2.5 exists to prevent. | **High** | **My defect. Ruled in §16.5** — split, and the fitting half moves later than either party proposed, because fitting needs **pay data** (KAN-193/195) as well as pay points. |
| **CFL-42-42** | BA-42 | KAN-208's "at least two groups satisfy Check B's minimums" is unverifiable in W0 — a group needs a family, level and pay market. | Medium | **Ratify with a correction to the BA's target wave.** Build in W0 against the planned ladder; the assertion becomes a **W2 exit gate**, not W1 — comparison groups need pay markets, which arrive with KAN-199 in W2. |
| **CFL-42-43** | BA-43 | **KAN-208 changes live behaviour in a shipped feature.** `employees.gender` has exactly one consumer — vacation-type eligibility — so 100% NULL → 100% populated changes which leave types 146 employees are offered. | **High** | **Ruled in §16.4.** Acceptable on synthetic data, **conditional on evidence**. |
| **CFL-42-44** | ARCH-36 | `reference_value` is money in a `pay_equity`-gated table; `reference_value × (1 + deviation/100)` is the subject's salary. CFL-42-19 was ruled for *computed* ratios; this is a **stored column**. | **High** | **Ratify §12.6.4 as designed.** Both codes required to see `reference_value`/`deviation_pct`, else a band label; `GENDER_GAP` findings carry no `reference_value`, enforced by CHECK. His own catch, and correct. |
| **CFL-42-45** | ARCH-37 | The tolerance CHECK spans two permission domains (`company_settings:w` vs `compensation:w`) and cannot be satisfied in one transaction; he took the guarantee over the boundary and asked me to ratify. | Medium | **DISSOLVED by §16.2 — he keeps both.** There is no CHECK to write. I note that his instinct was right: *"on the constraint that makes or breaks the feature I take the guarantee"* is the correct order of preference, and it happens not to be needed. |
| **CFL-42-46** | ARCH-38 | The performance-management boundary is held by **review discipline, not by architecture**, and three reasonable increments cross it. | Medium | **Ratify, and I am glad it is recorded rather than pretended away.** ADR-025's forbidden-column table + the standing review-checklist item are the mitigation. **Adding: it also goes on the Demo Gate's human list** (§16.4, UX-A1-C1's item (a) covers the same ground). A control nobody has named is a control nobody holds. |
| **CFL-42-47** | UX-A1-C1 | **The ladder's content quality has no owner and no criterion can test it.** A ladder reading *"does more of what 1.1 does"* passes every AC in the epic and delivers none of the transparency the owner asked for. | Medium | **Adopt (a); resolve (b) with the mechanism that already exists.** (a) *"The ladder reads as a real description of the work"* goes on the **Demo Readiness Gate's must-be-walked-by-a-human list** — that gate is mine, so I am adding it. (b) **No per-family author grant.** With CFL-42-35, ladder configuration is `org_structure:w`; **a tenant that wants engineering managers to author simply creates a role and grants it** — companies define their own roles, so the matrix already solves this and the answer is documentation, not code. Plus: the editor supports paste-friendly entry and per-step **"drafted by"** attribution, so HR can transcribe content authored elsewhere without pretending they wrote it. |
| **CFL-42-48** | UX-A1-C2 | UX specified `PAY_ABOVE_STEP` as **silent** — no bell, no badge. A1 said "lower severity", not silent. | Medium | **Ratify silent — register only.** Silent is a legitimate expression of lower severity when the alternative feeds R-1, my top risk. Their argument decides it: *a notification whose honest review outcome is "nothing to do" is how the channel gets muted*, and the channel is shared with the primary check. **§16.2 strengthens the case** — under the nearest-step rule `PAY_ABOVE_STEP` becomes rarer and means something sharper ("paid closer to a higher step"), so register-only is right for a smaller, better signal. |
| **CFL-42-49** | UX-A1-C3 | **A new control gap A1 created.** A step change is applied by one person with no approval and now has a computable pay consequence: a manager can move a report 1.0 → 1.5 alone, lift the expected pay point ~27%, and manufacture a `PAY_BELOW_STEP` that pressures the organisation to pay it. | **High** | **Adopt, modified — ruled in §16.4.** Not a two-step cap: **one step per action**, with a multi-step move **routed to a `LEVEL_CHANGE` request** (which has a chain). Principled rather than arbitrary, preserves the capability, closes the gap. |
| **CFL-42-50** | UX-A1-C4 | "Mutually decided" is unenforceable and the UI must not imply otherwise. | Low–Med | **Ratify in full, and promote the reasoning.** `Confirm we discussed this`, never *Accept*; displayed as `Discussed with Ravi on 14 March`, never "agreed". This **answers OQ-BA-13**. See §16.6 — A-2 becomes a standing rule about language, not only about audit diffs. |
| **CFL-42-51** | UAT-F-14 | **The dead zone** — a perfectly fitted ladder still flags ~20% of the workforce. | **High** | **ELIMINATED by §16.2**, not mitigated. Their recommendation (project the count at the review gate) is **still adopted** as a Tier-2 quality display — it is cheap and it is the right instrument — but it now projects a number that should be zero, which makes it a **regression detector** rather than an apology. |
| **CFL-42-52** | UAT-F-17 | **Two of my own sections contradict each other:** §14.7 item 3 retains the 80% coverage gate for Check B while §15.4 calls its boundary invalidated. | Low | **UAT is right; I was inconsistent.** The gate **stands for Check B, inclusive at exactly 80%**, and the 79.59%-displays-as-80% case is **more** important under BR-1.6, not less: the gate is the **one deliberate exception** where a rounded display value is *not* the comparison input. That exception is now documented rather than accidental. §15.4's invalidation note is corrected here. |
| **CFL-42-53** | **SPM, new** | **The BA's CFL-42-37 fix (`tolerance = increment ÷ 4`) would have doubled UAT-F-14's dead zone from 20% to 50%.** Both authors were right in their own frame; nobody held both documents. | Medium | **Both superseded by §16.2.** Recorded because it is the clearest evidence available that the tolerance-as-boundary mechanism was wrong, and because it is exactly the failure mode this reconciliation pass exists to catch. |

**ID mapping for anyone holding an older reference:** BA CFL-42-35…43 keep their numbers (35 merged with the
Architect's). **Architect CFL-42-36 → CFL-42-44 · CFL-42-37 → CFL-42-45 · CFL-42-38 → CFL-42-46.** UX
C1–C4 → **CFL-42-47…50**. UAT F-14 → **CFL-42-51**, F-17 → **CFL-42-52**.

### 16.4 The other rulings

**KAN-208's vacation side effect (CFL-42-43) — acceptable on synthetic data, conditional on evidence.**
It is acceptable: the population is fictional, the environment is demo-grade, and the change is to which leave
types a fictional person is offered. But *acceptable* is not *unmeasured*. Four conditions, all on KAN-208:
(a) **run the vacation regression suite before and after and explain every single difference** — a difference
nobody can explain is a defect, not a side effect; (b) review every gender-restricted seeded vacation type
against the new distribution; (c) the release notes and any demo script state it; (d) **if the diff produces a
failure that cannot be explained as intended eligibility change, KAN-208 does not land.** *Containment
considered and rejected:* leaving a subset NULL would preserve current behaviour but muddles Check B's exclusion
counts and leaves "insufficient gender representation" in exactly the groups you would want to demo. Change it
fully, measure it, explain it. **Process note worth keeping:** nobody had checked what that column was for until
Wave 4. The register caught it because somebody went and looked, not because anybody reasoned about it.

**CFL-42-49 — one step per action, with a routed alternative.** UX asked for a two-step cap; I am ruling
**one**, because A1's model is that a step is a *described set of expectations an employee has demonstrably met*,
and meeting two steps' worth simultaneously at one review is not progression — it is a correction or a
promotion. **A move of more than one step in a single action is refused, with a message directing the user to
raise a `LEVEL_CHANGE` request**, which has a chain and two pairs of eyes. That preserves the capability §14.3.4
explicitly permits (skip-step, with a reason), routes it through governance, and is principled rather than
arbitrary. Plus UX's other two guards: the reason is already mandatory, and the register's *"on step X since"*
line makes the pattern visible to HR, which is the real defence. **One correction to my own instinct:** I wanted
the audit row to record the resulting pay point — it must not. That is an amount, and D5.6 keeps amounts out of
`audit_log`. The row records **step before → after** (already on the allowlist) and the pay consequence is
derived on read by somebody holding `compensation:r`.

**UAT-F-12 / F-13 / F-13b — all three adopted as recommended.** Tolerance boundary **inclusive** (now a Tier-2
display question, low stakes). Tie rule: **fit down** — fitting up manufactures a *primary* finding from a tie,
fitting down at most a secondary one — **and assert determinism regardless**, which is the more important half:
a fit that flips between runs makes every downstream finding unreproducible. Distance metric: **relative
(ratio)** — the ladder is multiplicative and an absolute metric biases fitting downward at the top of every
level.

**UAT-F-15 — a 0% increment.** Permitted as an **explicit** choice; the level is marked **not evaluable by
Check A′** with the reason named. Under §16.2 this falls out naturally rather than being a special case: with no
distinct pay points there is no nearest step.

**OQ-BA-14 — notify the employee when a roadmap is written for them? I am overruling the BA's and UX's "no".**
**Yes — one in-app notification, no email, retiring on view, containing no pay information.** The roadmap's
entire stated purpose is transparency to the employee. A roadmap the employee does not know exists delivers
exactly zero of it, and "it appears on their profile" assumes they visit their profile. This is cheap and it is
the difference between the feature working and the feature existing.

**UX-A1-Q1 (ladder draft/publish) — ratify save-is-publish**, stated on screen. Do not double the model for a
screen edited twice a year; "the ladder is out of date because nobody pressed publish" is the worse failure.
**UX-A1-Q2 (roadmap deletable) — ratify supersede-only**; route the discomfort to the DPO, since it is a record
about a person. **UX-A1-Q4 — answered by CFL-42-47(b).**

**KAN-207's technical-readiness verdict — accepted, and I am naming the reviewer.** The Architect declined to
certify a story whose principal risk his tests cannot see, which is the right call and the right reason.
**KAN-207 is Ready when its copy has been reviewed by a human against the R-17 boundary, and I own that review** —
it is the same class of judgement as the Demo Gate, which is mine.

**V18 / KAN-198 — confirmed, and re-scoped in the backlog.** `org_change_workflows` returns **0 rows**; every
tenant runs the single-HR_ADMIN default. T-198-7/8 are **not an enhancement** — they are the difference between
KAN-198 existing and KAN-198 working. The backlog row now says so with the evidence attached.

### 16.5 The corrected build order

**CFL-42-41 is my defect and the fix is larger than either party proposed**, because fitting a step to pay needs
**pay data** (KAN-193 + KAN-195) as well as pay points (KAN-206). Both proposed fixes — move KAN-206 to W1, or
split KAN-191 across W1/W2 — would still have had the fitting run before any pay existed.

**Ruling: KAN-191 keeps level assignment in W1; the step-fitting half becomes KAN-209 at the end of W2.**

- **KAN-191 (W1)** — assign family and level; the title→level mapping screen; level coverage. Everyone defaults
  to step **`.0`**, which is **harmless in W1** because Check A′ requires a configured pay point and none exists,
  so nothing is evaluable and no finding can be raised.
- **KAN-209 (W2, last)** — fit steps to pay, the fitted-step review screen, and **releasing the
  ladder-fitted-and-reviewed gate**.
- **The ordering invariant, stated so it cannot be lost:** **the gate ships CLOSED with KAN-206** and is opened
  only by KAN-209's review. Between pay points existing and steps being fitted there is a window in which
  everyone is at `.0`; the closed gate is what makes that window safe. Nothing else does.

This also strengthens W2: you now leave it with pay recorded, visibility enforced, backfilled, **and the ladder
fitted and reviewed** — a coherent exit rather than a partial one.

```
W0  S2   KAN-203(P0) ∥ KAN-204 ∥ KAN-208 ∥ KAN-188 ∥ KAN-189
W1  S3   KAN-190 → KAN-191 → KAN-207                          ladder, levels, roadmap — no money in it
W2  S3   KAN-199 → KAN-206 → KAN-193 → KAN-194 → KAN-195 → KAN-209
W3  S3   KAN-196 → KAN-197 → KAN-198 → KAN-192
W4  S3   KAN-200 → KAN-201 → KAN-205 → KAN-202
```

**22 stories.** The Architect's day-24-vs-day-54 observation is resolved: KAN-206 completing early is now
correct rather than a symptom, because KAN-209 — not KAN-191 — is what consumes it.

### 16.6 Standing rules — one addition

Added to §13.5, from UX-A1-C4:

> **6. A label is a claim, and the same rule applies to it.** Amendment A-2 said a *guarantee* is only stated if
> the mechanism delivers it. It generalises: `Accept` over a mechanism that records only "read" is a false
> statement about a person, and it is worse than the weaker true one. `Confirm we discussed this`, never
> *Accept*. `Discussed with`, never *agreed*.

### 16.7 Risks

| # | Change |
|---|---|
| **R-1** (alert fatigue) | **Materially reduced.** §16.2 takes day-one Tier-1 findings from ~20% of a fitted workforce to **zero**, and CFL-42-48 keeps the secondary type out of the notification channel entirely. This is the first wave where R-1 has gone down rather than sideways. |
| **R-16** (a configuration silently disables the check) | **Closed.** There is no cross-field constraint left to misconfigure. |
| **R-17** (the roadmap drifts into performance management) | **Unchanged in likelihood, better instrumented.** CFL-42-46 states plainly that this is held by review discipline and not by the schema; ADR-025's forbidden-column table, the review-checklist item and the Demo Gate human check are the three places it is held. |
| **R-18** *(new)* | **The ladder ships with content nobody can use** — six steps that all say the same thing. **Medium × High.** No AC can test it. Held by CFL-42-47's Demo Gate item and the "drafted by" attribution. This is the adoption risk for KAN-190 the way R-2 is for KAN-191. |
| **R-19** *(new)* | **KAN-208's vacation side effect ships unexplained.** **Low × High** after §16.4's four conditions; **High × High** without them. |

## 17. For the product owner — everything still open, in one page

*He has answered OQ-1, OQ-3 and gender. Everything below has a default the team is building against today, so
**nothing here is blocking**. Ordered by what it costs to answer late.*

| # | Question | Default being built | Cost if late |
|---|---|---|---|
| **1. OQ-5** | **Is bonus, commission, equity or any variable pay in scope — or base salary only?** | **Base salary only.** | **The only one that forces a rewrite.** It changes the compensation record's shape *and*, after A1, what the step increment applies to. **Please answer this one first.** |
| **2. UX-A1-Q3** | **An employee can read what their step *requires*, but not what it is *worth*** — and the pay proposal that follows a step change is invisible to them. Your rationale was *"when an employee takes additional responsibility the pay should be adjusted"*, so the transparency is currently one-sided. Three options: **(a)** publish the pay points to everyone · **(b)** an employee sees **their own** step's pay point and their own pending proposal · **(c)** publish nothing. | **(b).** It is the honest middle, and it is the reversible one — (b)→(a) is a widening, (a)→(c) is a takeaway. | Low — a copy and permission change. But **(a)** is where EU pay-transparency law points, and in some countries **(b)** is a works-council matter (see 7). |
| **3. OQ-BA-13** | **You said the roadmap is "mutually decided". Does the employee *agree*, or *acknowledge*?** We have built **acknowledge** — the button says *"Confirm we discussed this"*, never *Accept*. | **Acknowledge.** Recording "read" honestly beats recording "agreed" falsely, and a disagreement is a conversation, not a form field. | Low — a label and a column. It is your word, so we are checking rather than assuming. |
| **4. OQ-9** | **Segregation of duties on money.** Three rules: two different approvers · the initiator may not approve · **not bypassable by SYSTEM_ADMIN**. Note: **no tenant has a configured approval chain today**, so without a seeded two-level default this control binds nobody. | **All three, plus a seeded HR_ADMIN → PORTAL_ADMIN chain for pay changes.** | Low to change, high to omit. |
| **5. OQ-2** | **Who sees a salary by default?** A manager: their direct reports only, not the whole team below them. Department and location heads: nobody. Employees: their own. | **As stated.** All three are tenant-changeable in one click. | Very low — seed data. |
| **6. OQ-7** | **Should compensation be OFF for every existing company until you switch it on?** | **Yes** — your commercial control doubling as a safety default. | Very low — one seed value. |
| **7. OQ-8** | **Are any target customers subject to works-council consultation on pay or job classification?** Your seed data spans Germany and four Nordic countries. | **Assume yes for Germany and the Nordics.** | Not a build blocker; **a launch blocker.** Discovering it during a rollout stops the rollout. |
| **8. OQ-4, OQ-6, OQ-A1-1/2/3** | Five confirmations: the example ladder was illustrative · one currency per pay market · we flag when pay does not match the step · advancing a step **proposes** a pay change rather than applying one · **EP42 records that a step change happened at a review; it does not build the review.** | **All as stated.** | Very low each. **The last one is the most likely to surprise you later** — you anchored progression to the performance review, the probation period and the mid-term goal review, and this product has none of those. A Performance, Goals & Reviews epic is parked, unscoped, if you want it. |

**Two things that are not questions, but that you should hear:**

- **The first real pay figure entered — even one, even by us, even "just to see how it looks" — triggers the
  security phase before anything else ships.** That is deliberate and it is cheaper to know now than on the day
  you want to show a prospect their own numbers.
- **Until real login exists, the pay visibility model is correct in code and unenforceable in practice** —
  anyone can pick any identity from the demo tiles. Every compensation demo will say so at the start rather than
  let somebody discover it.

*Wave 5 complete. Backlog and roadmap updated in the same pass.*
