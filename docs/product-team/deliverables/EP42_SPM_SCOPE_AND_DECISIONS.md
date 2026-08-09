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

---

> **§17 above is SUPERSEDED by §19 below** (Amendment A2 closed OQ-5 and added five follow-ups). Left standing
> per the rule this document has followed throughout: supersede visibly, never edit the trail.

---

# 📌 AMENDMENT A2 — THE PRODUCT OWNER'S SECOND ANSWER — 2026-08-09

> **Authoritative. Outranks A1, §14 and §16 where they conflict.** Source: his reply of 2026-08-09, verbatim in
> `EP42_OWNER_ANSWERS_A2.md` §1.
>
> **Headline: OQ-5 closes, the job-family model is confirmed unchanged, and one genuinely new capability arrives
> — an annual hike cycle. I am putting that capability in a sibling epic, EP43, and I argue it in §18.4.**

## 18. Amendment A2

### 18.1 OQ-5 — CLOSED. Base salary only.

*"base salalary only at this point"*

**Ruled: base salary only. OQ-5 comes off the open list.** No bonus, commission, equity, allowances or variable
pay in the record, and the step increment and pay point apply to **base**.

**But "at this point" is doing work, and I am converting the question into a constraint rather than deleting
it.** He is scoping this cycle, not ruling out total compensation. So OQ-5 closes as a *build* decision and
becomes a **standing extensibility rule** with three testable parts and **zero build cost**:

1. **Nothing in EP42 may make `annual_base_fte` mean "total".** The column, the API field, the UI label and the
   documentation all say **base**, so a later `annual_total_fte` sits **beside** it rather than redefining it.
2. **The pay point is a base pay point** and is named so everywhere — schema, screen, export.
3. **No code assumes a compensation record has exactly one amount.**

**Do not build `compensation_components` now.** The Architect's §10.1 already records its shape; a recorded shape
is the whole point of that register and it is sufficient. Over-building for a question he deferred would be the
scope creep I have pushed back on four times.

### 18.2 Job family — RATIFIED AS DESIGNED. Change nothing.

His worked example maps onto the existing model **exactly**, and I have checked it rather than assuming:

```
job_families:  "Full Stack Software Engineering"        (company-scoped)
  job_levels:  ordinal 1 → title "Intern Full Stack Software Engineer"
               ordinal 2 → title "Junior Software Fullstack Engineer"
```

**Two verifications, both answered here so the Architect confirms rather than investigates:**

**(a) Is a "position" a separate entity from a level's title? Ruled: NO — the title lives on the level.**
His sentence — *"there is position created Junior Software Fullstack Engineering… will belong to Job family…
with Level defined 2"* — describes the act of defining a role and mapping it to `(family, level)`. That is
precisely what the level-carries-title model does. The only case it cannot express is **two distinct positions at
the same (family, level)** — "Junior Full Stack Engineer" and "Junior Full Stack Engineer (Platform)" — and his
example does not require it.

I am refusing to generalise pre-emptively, and the reasons are not tidiness:
- Charter §9.4, problem before feature. There is one worked example and the model handles it.
- A positions table is not one table. It brings its own CRUD, its own permissions, a backfill, and — the real
  cost — **another dimension on the comparison group key**: are two positions at one level one comparison group
  or two? That question has no obviously right answer and it would have to be answered before KAN-200.
- **It is additive later.** `job_positions(family, level, title)` with the level's title as the default single
  row changes the meaning of no existing column. Recorded in the deferred-designs register alongside FX and
  total comp.

**The tell, handed to Delivery as a watch item:** if a tenant asks for two titles at one level during
onboarding, that is the trigger to build it — not a hypothesis, an observation.

**(b) Are levels family-scoped rather than company-global? Ruled: yes, as designed, unchanged.** His numbering
is family-relative (Intern = 1, Junior = 2 *within* Full Stack Software Engineering) and ADR-017 already makes a
level ordinal **within a family**. The comparison group key `(company, job_family, job_level, pay_market)`
carries family for exactly this reason — level 3 in Engineering is not level 3 in Finance. Self-consistent;
nothing to change.

**Architect's task is a one-line confirmation against the schema, not an investigation.**

### 18.3 Expectations org-wide first, then alignment — confirms W1's order

*"need to define the basic expectation for all postions and for all defined levels in organsiation then need to
align all employees for each role to it's level"*

**Ratified, no change: KAN-190 (ladder + expectations) → KAN-191 (align every employee).** Two things it adds:

- **"for all positions and for all defined levels" makes completeness a launch expectation, not a nice-to-have.**
  UX's honest `Not described yet` state stays — a blank is worse than an admission — but **KAN-209's review gate
  must report ladder-description completeness** ("28 of 34 steps described") alongside the fitted-step review.
  That is a one-line addition to a screen that already exists, and it is the only instrument anyone will have
  for R-18 (a ladder that ships with content nobody can use).
- **It confirms A1's transparency requirement a second time** — which matters enormously for §18.6, because it
  is the reason level *disclosure* is a narrow exception rather than a reversal.

### 18.4 The annual hike cycle — and my judgement on where it goes

> **Ruling: the hike cycle is a SIBLING EPIC, EP43, sequenced after EP42. But the part of it that protects
> EP42's own integrity — effective-dated pay points and ladder re-basing — stays INSIDE EP42.**

#### 18.4.1 The split, and why it is not tidiness

The instinct is to make this EP42 W5, because it shares the compensation record, the approval chain, the audit
vocabulary and the pay-point model. I considered that and rejected it, on delivery risk and coherence.

**Against W5 — three arguments, in order of weight:**

1. **EP42 is already at the outer limit of what I would run as one epic, and I would rather say that than let it
   grow by accretion.** 23 stories, 175 tasks, a 71-day critical path, ~14–16 calendar weeks — and it has been
   **amended twice in a single day**. Adding a recurring annual business process with a performance input would
   take it to ~28 stories and past the point where I could defend it as one commitment. An epic that long has no
   internal release point anyone outside the team recognises, and the longer it runs the more certain it is to be
   re-scoped mid-flight. That is the delivery risk, and this epic has already demonstrated it.
2. **It is a different shape of thing.** EP42 is a data model and a check: hold a salary, place people on a
   ladder, verify correspondence. The hike cycle is a **recurring business process** — a calendar, a budget, a
   per-employee differentiation round, a bulk approval and a bulk apply. In shape it is closer to EP38's
   lifecycle workflows than to anything in EP42. Bundling a process into a data epic makes both harder to reason
   about and makes the epic's exit criteria incoherent.
3. **The split keeps §14.5 true.** EP42's boundary — *"records that a step change happened at a review; does not
   build the review"* — stays intact. **EP43 then owns its own, explicit, narrow boundary decision** about the
   performance input (§18.5). Bolting the hike into EP42 would have forced me to reopen §14.5 and leave the
   boundary ambiguous across 28 stories, which is exactly how R-17 plays out.

**For W5 — the one real argument, and how I have answered it.** §5a is a genuine functional coupling: without
re-basing, the equity check degrades. If EP42 ships and EP43 never does, EP42 rots.

**So I have separated the capability from the process.** Two things were tangled together:

| | Goes where | Why |
|---|---|---|
| **Effective-dated pay points + a ladder re-base action** | **EP42, W2** — new story **KAN-210**, plus effective-dating built into **KAN-206** from the start | This is what protects EP42's own integrity, and it is small. A company can re-base **manually** the day they grant a hike, even with no cycle tooling at all — a workaround that genuinely works |
| **The annual cycle** — the policy, the three inputs, per-employee differentiation, the performance modifier, the budget, the approval round, the bulk apply | **EP43** | The large, process-shaped, boundary-sensitive part |

With that split, **EP42 shipping without EP43 is safe rather than degrading.** That was the only thing making W5
look necessary, and it is now handled inside EP42 for the cost of one small story.

#### 18.4.2 EP43 — Annual Compensation Review Cycle

Five stories, outline depth — it is entering **S1**, not S3, and I am not specifying it to build level in an
amendment. Under **BG7**, sequenced **after EP42 W4**.

| Story | Scope |
|---|---|
| **KAN-211** | The **cycle** itself: per company, per year, a named cycle with an effective date and a lifecycle (`DRAFT → OPEN → APPROVED → APPLIED → CLOSED`) |
| **KAN-212** | The **three inputs he named**: market movement (**per pay market** — Stockholm's market is not Tallinn's), company affordability, and the **per-employee performance modifier** (§18.5) |
| **KAN-213** | **Per-employee proposals and the manager worksheet** — differentiate within the guideline, with a running total against the budget |
| **KAN-214** | **Cycle approval and bulk apply** — one approval for the cycle, then N compensation records written atomically on the effective date |
| **KAN-215** | **Close-out, audit, and re-basing the ladder** by the market component, using **KAN-210**'s capability |

**Three invariants EP43 inherits and may not weaken**, stated now so they are not rediscovered:
- **No pay change is applied without an approval a human gave.** A cycle cannot route 500 individual requests
  through the per-request chain — that is absurd — so it needs a **cycle-level approval**. That is a legitimate
  different shape, but **KAN-198's four-eyes rule applies to the cycle as a whole**: two different people, and
  the initiator may not approve.
- **Money never reaches `audit_log`** (D5.6 / amendment A-2). A cycle writing 500 compensation records writes
  **one** correlated audit set with counts, not 500 amounts.
- **The budget is a warning, not a block.** Show the running total; require a reason to exceed. Blocking means
  the differentiation happens in a spreadsheet, which is the problem this product exists to end.

#### 18.4.3 "for each" — my reading, and the default the team builds against

His sentence is compressed: *"for each year company defines its own hike percentage for each based on market
situation and their own income and performance of the employee."*

**Ruled default:** a **company guideline percentage per cycle, per pay market** (funded by market movement and
company income), **differentiated per employee** by the performance modifier, **within the budget the guideline
implies**. Guideline 4% → budget is 4% of total base → managers distribute — one person 2%, another 7%, the total
lands near 4%. Flagged to him as **A2-1**; nothing waits.

#### 18.4.4 §5a — re-basing. **And a correction to the brief's arithmetic.**

**The brief says an un-re-based hike makes the check "silently wrong". Under the nearest-step rule I ruled in
§16.2, it is not silent — it is loud, and it fails in the first cycle rather than the third.**

Checked, not asserted. Increment 5%, pay points static, a 4% hike:

| | Distance to their own step's point | Distance to the **next** step's point | Result |
|---|---|---|---|
| After a 4% hike | **4.00%** | **0.95%** | **Nearer to the next step → every employee flags `PAY_ABOVE_STEP`** |

The threshold is **half the increment**: any hike above 2.5% (on a 5% ladder) flags the **entire workforce** in
one cycle. Below it, nothing flags and the drift accumulates until it crosses.

**Why this matters, and it cuts two ways.** It makes re-basing **more** urgent, not less — a single ordinary
hike renders the equity register unusable overnight. But it also means **we will not ship something that quietly
lies**: the failure announces itself immediately, to everybody, which is the better of the two bad outcomes and
is a point in favour of §16.2's nearest-step rule that I had not seen when I ruled it. **Risk reclassified from
"silently wrong" to "unusable until re-based".** Logged as **CFL-42-54**.

**The requirements, first-class in EP42:**
- **Pay points are effective-dated from the start** — in **KAN-206**, half-open, ADR-020's convention.
  Retrofitting effective-dating is a rewrite; adding it now is a column.
- **KAN-210: a re-base action** — raise all pay points for a family or a pay market by X%, effective D, with a
  reason, in one audited transaction.
- **A finding is always evaluated against the pay point in effect on its evaluation date**, and the evaluation
  date is stored, so **a 2026 finding is still explicable in 2028**.
- **A staleness warning:** where the newest pay point for a level is older than the company's configured cycle
  period (default 18 months), the register says so — *"these pay points have not been re-based since March 2026;
  findings may reflect market drift rather than pay decisions."* Cheap, and it is the guard against the whole
  class of problem.

### 18.5 §5b — the performance boundary, re-drawn, and I am not going to soften it

A2 makes **employee performance an input to pay**. §14.5 ruled that EP42 *"records that a step change happened at
a review; it does not build the review."* The honest position:

> **§14.5 stands unchanged for EP42. EP43 deliberately and narrowly crosses one line, and I am saying so plainly
> rather than describing a performance rating as a "modifier" and hoping nobody notices.**

**Because that is what it is.** A per-employee ordinal band, entered by a manager, that determines their pay
outcome **is a performance rating**. Calling it something else would be exactly the failure amendment A-2 and
standing rule 6 exist to prevent — *a label is a claim*. So: **EP43 introduces a performance rating as a pay
input.** That is a real widening of scope beyond anything in EP42, and the owner should be told in those words.

**The shape — ruled:** a **company-defined ordinal band** (e.g. below / meets / exceeds / outstanding), each
mapping to a **configured multiplier** on the guideline. Not a free numeric — that is a rating dressed as
arithmetic and it invites the calibration conversation immediately. A band keeps the **policy** (what "exceeds"
is worth) at company level where it belongs, and the **judgement** at manager level where it belongs, and it
makes the budget computable.

**What stays out — the line, drawn explicitly:** goals, objectives and OKRs · the review cycle itself ·
calibration and moderation · rating distributions or forced curves · scoring rubrics · 360 or peer input ·
competency assessment · a rating **history** surface — one rating per employee per cycle, and no
"performance over time" view, because that view is the drift.

**Four constraints on the rating, and they are testable:**
1. **Single-purpose.** Written in a cycle, read by that cycle, used for nothing else. Not on the profile, not in
   the directory, not in the org tree, not exported, not readable by any other feature. Enforced the way pay is
   — a scoped service, a feature gate and a negative-visibility suite.
2. **Not shown to the employee by default.** It is a manager's input to a pay proposal, not a communicated
   verdict; communicating a rating is a conversation, not a screen. Flagged as a follow-up (**A2-2**).
3. **UX's §25 ban list and its nine pre-refused requests apply to this surface first**, and I expect them to be
   tested here before anywhere else.
4. **It is EP43's boundary to hold, in EP43's own ADR** — not an appendix to ADR-025.

**And the narrative link he made, which should be explicit in the flow rather than implied:** *"The expectation
from the employee is if they satisfy in next level the compensation review based on that."* **Meeting the next
level's expectations is what justifies the compensation review.** So KAN-207's roadmap and KAN-192's step-change
pay proposal must be visibly connected — the proposal cites the roadmap it fulfils. That is a UX requirement,
and it costs nothing.

### 18.6 §6 — the job level may be hidden from the employee

*"Though role is transparent to the employee for employer but Job level may not be disclosed according to
company policy."*

**This is not a reversal — he asked for level-expectation transparency twice, in both answers.** It is a
per-company switch over one specific field, and it lands on the screens UX built in Wave 4.

**The rules, ruled:**

| Element | Visible to the employee |
|---|---|
| Their role / job title | **Always.** Never configurable |
| The ladder — families, levels, every level's expectations | **Always.** This is the transparency he asked for twice, and it is not what the switch governs |
| **Which level/step *they* currently occupy** | **Company-configurable** |
| Their roadmap | **Always visible — but rendered without level numbers when disclosure is off** (see below) |

**(a) The default is ON (disclosed) — and the tenant is *asked* during first-run setup.** Neither default alone
is right: defaulting off silently under-delivers the outcome he asked for twice; defaulting on could breach a
tenant's policy on day one. So the ladder configurator's first-run flow **asks**, making it a deliberate choice
rather than a default nobody noticed. Consistent with the standing rule — consequences shown where the choice is
made.

**(b) With disclosure off, the roadmap survives — as expectations, without numbers.** Of A2's three options I
rule **(b)**:
- **(a) hide the roadmap too** is wrong: it discards the substance to hide a label. The expectations *are* the
  transparency; the level is the name for it.
- **(c) hide the number only** is naive. Hiding *"you are at 2.3"* while showing *"your next step is 2.4"*
  discloses the level. A half-measure that leaves every reference intact will be discovered.
- **(b)** is coherent: with disclosure off, the employee's own view carries **no level or step number and no
  "you are here" position indicator anywhere**, and the roadmap reads *"to move up, here is what is expected of
  you."* Same content, no numbers. The ladder stays fully browsable.

**(c) And the honest limitation, which must be on the configuration screen and in the documentation.** An
employee who can browse the ladder and read their own roadmap can very often **infer** their level by matching
the expectations. So this setting delivers **policy compliance, not secrecy** — and it is therefore labelled
**"Do not display the employee's level"**, never *"hide"*. The configurator says so in words:
*"Employees can still read the ladder and their own expectations, so this prevents display, not inference."*
A tenant who believes they have bought secrecy will be wrong, and they should learn that from us on the
configuration screen rather than from an employee in a meeting. Standing rule 6.

**(d) Can the level be hidden from the *manager*? No.** Flatly. The manager authors the roadmap, which targets
the next step; a manager who cannot see the current step cannot do the job A1 assigns them. **The switch governs
the employee's view of their own level and nothing else** — not the manager, not HR, not the register, not
reporting, not the audit trail.

**(e) The odd case, named so UX handles it rather than discovers it.** An employee who is *also* a manager will
see their **reports'** steps and not **their own**. That is the correct output of two orthogonal rules —
CFL-42-39 (another person's step is scoped as their pay is) and this one (your own may be withheld from you) —
and it will look like a bug unless the copy explains it. **CFL-42-57.**

**(f) My Pay follows the switch.** OQ-BA-12's default — the employee sees their own step's pay point — is now
**conditional**: with disclosure off, My Pay shows the salary and **no step reference at all**, because a step
pay point names the step.

### 18.7 What A2 invalidates

| # | What | Status |
|---|---|---|
| 1 | **OQ-5** | **CLOSED** — base only; converted to the extensibility rule in §18.1 and removed from the owner's page |
| 2 | **§14.5's performance boundary** | **Stands for EP42, unchanged.** EP43 crosses it deliberately and narrowly (§18.5). Not invalidated — extended, with the extension quarantined in another epic |
| 3 | **UX Wave 4: `/ladder` in main nav, and the `Your level and next step` card** | **Not invalidated — gains a second rendering mode.** The card becomes `Your next step` with no position indicator when disclosure is off. §22–§26 need the disclosure-off variant throughout |
| 4 | **OQ-BA-12** (employee sees their own step pay point) | **Now conditional** on the disclosure switch |
| 5 | **UX-A1-Q3** (employee sees what a step requires but not what it is worth) | **Partly overtaken.** It only applies where disclosure is **on**; where it is off the question does not arise. Re-framed on the owner's page |
| 6 | **KAN-206** | **Amended** — pay points are **effective-dated from the start** |
| 7 | **A2 §5a's own premise** that un-re-based drift is *silent* | **Corrected — it is loud** (§18.4.4, CFL-42-54). Risk reclassified |
| 8 | The job-family model, the comparison group key, D3, §16.2's nearest-step rule, the build order for W0/W1/W3/W4, every ruling in §12 and §16 | **Unaffected.** A2 confirmed D3 rather than changing it |

**Conflict register — four additions:**

| ID | Conflict | Sev | Ruling |
|---|---|---|---|
| **CFL-42-54** | **A2 §5a states un-re-based hike drift is "silently wrong". Under the nearest-step rule it is loud** — any hike above half the increment flags the whole workforce in one cycle (4% hike vs 2.5% half-increment: 4.00% from own point, 0.95% from the next). | Medium | **Brief corrected.** Re-basing becomes *more* urgent; the failure mode is "unusable until re-based", not "silently wrong". **KAN-210 + effective-dated pay points in KAN-206.** A point in favour of §16.2 that I had not seen. |
| **CFL-42-55** | **A2 §6 (the level may be hidden) vs UX Wave 4**, which made `/ladder` main-nav for everyone and built a card whose premise is naming the employee's step. | **High** | **Ruled §18.6:** option (b), default ON with a first-run prompt, honest labelling ("do not display", never "hide"), manager always sees it. |
| **CFL-42-56** | **A2 §5b (performance is an input to pay) vs §14.5** (EP42 does not build the review). | **High** | **Ruled §18.5:** §14.5 stands for EP42; **EP43 crosses the line deliberately and narrowly**, and it is called a performance rating rather than dressed up as a modifier. |
| **CFL-42-57** | An employee who is also a manager sees their reports' steps but **not their own** when disclosure is off. | Low | **Correct output of two orthogonal rules.** UX owns the copy so it does not read as a bug. |

### 18.8 Stories, waves and the corrected build order

**EP42 gains one story and becomes 23. EP43 is new, with five.**

| Story | Change |
|---|---|
| **KAN-206** | **+ pay points are effective-dated from the start** (half-open, ADR-020). Retrofitting is a rewrite; adding it now is a column. **+** the staleness warning threshold is a company setting |
| **KAN-210** *(new, EP42 W2)* | **Ladder re-basing** — raise all pay points for a family or pay market by X%, effective D, reason, one audited transaction. **+** findings evaluate against the pay point in effect on the evaluation date, and store that date. **+** the staleness warning in the register. **Must · P1** — it is what makes EP42 safe to ship without EP43 |
| **KAN-207** | **+ a disclosure-off rendering** — expectations with no level or step number and no position indicator. **+** the proposal that follows a step change **cites the roadmap it fulfils** (§18.5's narrative link) |
| **KAN-190** | **+** the first-run flow **asks** whether employee level disclosure is on, and states plainly that it prevents display, not inference |
| **KAN-194** | **+** the disclosure switch in the visibility model; My Pay drops every step reference when it is off; **the switch never applies to the manager, HR, the register or reporting** |
| **KAN-209** | **+** the review gate reports **ladder-description completeness** alongside fitted steps (§18.3) |
| **KAN-200/201** | **+** findings carry their evaluation date; the register shows the staleness warning |

```
EP42 — 23 stories
W0  S2   KAN-203(P0) ∥ KAN-204 ∥ KAN-208 ∥ KAN-188 ∥ KAN-189
W1  S3   KAN-190 → KAN-191 → KAN-207
W2  S3   KAN-199 → KAN-206 → KAN-210 → KAN-193 → KAN-194 → KAN-195 → KAN-209
W3  S3   KAN-196 → KAN-197 → KAN-198 → KAN-192
W4  S3   KAN-200 → KAN-201 → KAN-205 → KAN-202

EP43 — 5 stories, after EP42 W4
         KAN-211 → KAN-212 → KAN-213 → KAN-214 → KAN-215
```

**If S3 runs long, EP43 is the natural descope** — and I want that said now rather than negotiated later. A
company can run one hike cycle manually: re-base the ladder with KAN-210, adjust salaries with KAN-195's import,
and approve through the existing chain. It is laborious and it works. **EP42 has no such fallback**, which is
why the split puts the un-descopable half inside it.

## 19. For the product owner — replaces §17

*Everything still needing your answer, one page. **All of it has a default the team is building against today, so
nothing here is blocking.** OQ-1, OQ-3, gender and OQ-5 are now closed.*

**First, one decision you should see rather than discover:**

> **The annual hike cycle you described is going into a separate epic, EP43, delivered after EP42.** EP42 is
> already 23 stories and around 14–16 weeks and has been amended twice in a day; adding a recurring annual
> process with a performance input would take it past the size I can defend as one commitment. **The part that
> protects EP42 from rotting — moving the ladder's pay rates when you grant a hike — stays inside EP42**, so
> EP42 is safe to ship whether or not EP43 follows immediately. If the schedule tightens, EP43 is the thing that
> moves; the first hike can be run with the tools EP42 gives you, laboriously.

| # | Question | Default being built | Cost if late |
|---|---|---|---|
| **1. A2-1** | **How much of the hike cycle is the system's job?** | **Store the policy, propose per employee, approve through the chain, apply on an effective date.** Not budget modelling, not forecasting, not letters. A company guideline % **per pay market** (Stockholm's market is not Tallinn's), differentiated per employee, with the budget as a **warning, not a block**. | Medium — it sizes EP43 |
| **2. A2-2** | **Where does "performance of the employee" come from?** There is no performance module, and we are not building one. **We would store a company-defined band (below / meets / exceeds / …), entered by the manager at the moment of the pay proposal.** **Said plainly: that is a performance rating, and it is the one line EP43 deliberately crosses.** Everything else stays out — no goals, no calibration, no curves, no rating history, and the value is used for the pay calculation and nothing else. | **As described**, and **not shown to the employee** by default — communicating a rating is a conversation, not a screen. | Medium |
| **3. A2-3** | **Does the annual cycle move the ladder's pay rates too?** **This is a recommendation, not a preference.** If you grant 4% and the ladder stands still, **the pay-fairness check flags your entire workforce in the first cycle** — we checked the arithmetic. | **Yes, it must.** Built into EP42 so it works even before EP43 exists. | High if omitted — the check becomes unusable |
| **4. A2-4** | **With the job level hidden, what does the employee see?** | **The ladder and every level's expectations stay fully visible** — that is the transparency you asked for twice. **Their own level number is not displayed**, and their roadmap reads as expectations without naming a step. **Honest caveat we will put on the setting itself: they can still work it out by matching the expectations. This prevents display, not inference.** Default is **disclosed**, and we **ask** you during setup rather than assuming. The level is **never** hidden from the manager — they write the roadmap. | Low |
| **5. A2-5** | **Is a "position" a separate thing from a level's title?** | **No** — the title lives on the level, which expresses your Full Stack Software Engineering example exactly. We can add it later if a company needs two job titles at one level; we are not building it on a hypothesis. | Very low |
| **6. UX-A1-Q3** | **Where the level *is* disclosed:** an employee can read what their step *requires* but not what it is *worth*, and the pay proposal after a step change is invisible to them. Your rationale was *"when an employee takes additional responsibility the pay should be adjusted"*, so the transparency is one-sided. | **They see their own step's pay point and their own pending proposal** — not the whole ladder's economics. It is the reversible middle. | Low |
| **7. OQ-BA-13** | You said the roadmap is **"mutually decided"**. Does the employee **agree** or **acknowledge**? The button says *"Confirm we discussed this"*, never *Accept*. | **Acknowledge.** Recording "read" honestly beats recording "agreed" falsely. It is your word, so we are checking. | Low |
| **8. OQ-9** | **Two different people on any pay approval**, the initiator may not approve, and **no SYSTEM_ADMIN bypass.** Note **no tenant has a configured approval chain today**, so without a seeded two-level default this control binds nobody. | **All three, plus a seeded HR_ADMIN → PORTAL_ADMIN chain.** | Low to change, high to omit |
| **9. OQ-2 · OQ-7** | **Who sees a salary by default** (manager: direct reports only; department/location heads: nobody; employees: their own) and **is compensation OFF for every company until you switch it on**. | **As stated · yes, off.** Both are seed values, changeable in one click. | Very low |
| **10. OQ-8** | **Works councils** — are any target customers subject to consultation on pay or job classification? Your seed data spans Germany and four Nordic countries. | **Assume yes for Germany and the Nordics.** | Not a build blocker; **a launch blocker** |
| **11. OQ-4 · OQ-6 · OQ-A1-1/2/3** | Five one-line confirmations: the example ladder was illustrative · one currency per pay market · we flag when pay does not match the step · advancing a step **proposes** a pay change rather than applying it · **EP42 records that a step change happened at a review; it does not build the review.** | **All as stated.** | Very low each |

**Two things that are not questions:** the first real pay figure entered — even one, even by us — triggers the
security phase before anything else ships; and until real login exists, the pay visibility model is correct in
code and **unenforceable in practice**, which every compensation demo will say at the start.

## 20. Wave 6 — the A2 amendment round

### 20.1 Business Analyst
1. **Close OQ-5** and convert it to §18.1's three-part extensibility rule as **testable criteria** — "base" in the column, the API field, the label and the docs; nothing assumes one amount.
2. **KAN-210** — new criteria: the re-base action, effective-dated pay points, findings evaluated against the point in effect on the evaluation date, the staleness warning. Amend **AC-206-*** for effective dating.
3. **The disclosure switch** — amend **AC-194-***, **AC-207-*** and **AC-190-***: default on, first-run prompt, disclosure-off rendering, **never applies to the manager/HR/register/reporting**, My Pay drops step references. Add the **CFL-42-57** manager-who-is-also-an-employee case.
4. **AC-209-*** — ladder-description completeness on the review gate (§18.3).
5. **AC-207-*** — the proposal cites the roadmap it fulfils (§18.5's narrative link).
6. **EP43 outline criteria only** — KAN-211…215 at backlog-summary depth. **Do not write 200 ACs for an epic entering S1.** Do write the three inherited invariants (§18.4.2) as criteria, because those are the ones that get lost.
7. Confirm **CFL-42-54**'s corrected arithmetic in your own words; I would rather two people had checked it.

### 20.2 Senior Architect
1. **One-line confirmation** (§18.2): the current model expresses his family/level/position example without strain, and levels are family-scoped. **Confirm; do not investigate, and do not add a positions table.** Record `job_positions` in the deferred-designs register with the "two titles at one level" trigger.
2. **KAN-206 amended: effective-dated pay points**, half-open, ADR-020's convention — **from the start**, because retrofitting is a rewrite. Then **KAN-210**'s bulk re-base as one transaction.
3. **ADR-024 amended**: `step_pay_point()` takes an **as-at date**. Every caller — the engine, the step-change proposal, My Pay — passes one. This is the change most likely to be missed by a caller.
4. **The disclosure switch**: where it resolves. It is a **display rule on one field for one audience**, not a feature gate — do not reach for a fifth feature code. Confirm it cannot leak through an API payload (the negative-visibility rule applies to it).
5. **OQ-5's extensibility rule** — confirm `annual_base_fte` and the pay point are named "base" everywhere, and that §10.1's `compensation_components` shape is still purely additive.
6. **EP43: an architecture sketch only** — where the cycle sits, how a cycle-level approval satisfies KAN-198's four-eyes, and how a 500-employee apply writes **one** correlated audit set rather than 500 amounts. **No ADRs for EP43 yet.**

### 20.3 UX / Product Designer
1. **The disclosure-off rendering, throughout §22–§26.** `Your level and next step` → `Your next step`, no position indicator, no numbers, same substance. **This is the largest single item in this round.**
2. **The first-run prompt** in the ladder configurator, with the honest sentence: *"Employees can still read the ladder and their own expectations, so this prevents display, not inference."* You have the standing rule for this; it is the same discipline as `Confirm we discussed this`.
3. **CFL-42-57's copy** — the manager who sees their reports' steps and not their own. It will look like a bug; make it not look like one.
4. **The narrative link** (§18.5): the pay proposal after a step change **cites the roadmap it fulfils**. One line, high value — it is the owner's own logic made visible.
5. **KAN-210's re-base screen** — a bulk action that moves every pay rate in a ladder. It needs a preview of what it does to existing findings, and a confirmation proportionate to its blast radius.
6. **EP43: no design yet.** But **your §25 ban list and the nine pre-refused requests will be tested on the performance-rating surface first**, so re-read them with that surface in mind and tell me if any need strengthening before EP43 starts.

### 20.4 UAT Lead
1. **The re-basing arithmetic** — hand-computed, and please **independently reproduce CFL-42-54**: with a 5% increment, show that hikes at 2.4% and 2.5% fall either side of the flag boundary, and that a 4% un-re-based hike flags **every** employee. That number is now load-bearing in an argument to the owner.
2. **As-at-date fixtures**: a finding raised in 2026 against a pay point later re-based must still explain itself in 2028. This is the regression that would otherwise be found by a customer.
3. **The disclosure switch — a negative-visibility suite of its own.** With disclosure off, no level or step number appears **in the payload**, on any employee-facing surface, including My Pay and the roadmap. And assert it is **still visible** to the manager, HR, the register and reporting — a switch that over-applies is as much a defect as one that leaks.
4. **CFL-42-57** as a named case.
5. **Ladder-description completeness** on the review gate.
6. **EP43: no cases yet**, but flag now which of your 21 attacks apply to a performance rating — I expect it to be most of them.

---

> **§19 above is SUPERSEDED by §21.7 below.** Amendment A3 closed three more questions and added two.

---

# 📌 AMENDMENT A3 — 2026-08-09 — folded into the A2 pass

> **Authoritative. Outranks A1, A2, §14, §16 and §18.** Source: `EP42_OWNER_ANSWERS_A3.md`.
>
> **The headline: he has authorised a performance module, which overturns my §14.5.** Everything else in A3
> tightens or confirms. §21.2 sizes the two readings and puts the choice back to him, because the two are a
> quarter apart in delivery time and he is entitled to choose with that visible.

## 21. Amendment A3

### 21.1 A3-1 — the hike policy is employer-configured, and nothing ships predetermined

*"This will configuarable in Admin page by the employer and cannot be predeterined."*

**Ratified, and I am extending it one step further than he asked.** The hike policy is **data, authored per
company per cycle, on an admin surface**. The product ships **no hike percentage, no band set, no multipliers and
no formula** — the same discipline already applied to `step_count` (per level, per company, **no default**), and
for a stronger reason: a shipped default is a de-facto product recommendation about somebody's pay.

**The extension: the product must not *suggest* a value either.** No "typical is 3–5%" helper text, no
market-data placeholder, no pre-filled example. A suggestion is a recommendation we have no basis for, and it is
the same principle as D7.6's *"never derive, estimate or impute a salary"*. A company that has not authored a
policy **cannot open a cycle** — the admin page requires the values rather than defaulting them.

**What A3-1 does not settle, and my ruling stands unchanged:** whether the system merely stores the policy or
runs the cycle from it. **A2's default holds — store the policy, propose per employee, approve through the
existing chain, apply on an effective date. Not budget modelling, not forecasting, not letter generation.**
A3-1 constrains where the numbers come from, not what happens next.

### 21.2 A3-2 — the performance module. **§14.5 is superseded by owner decision, and here is the sizing.**

*"Introduce performance input module with all it's requirement implement this first if required if this the
blocker."*

#### 21.2.1 §14.5 — superseded, and it did its job

**§14.5 ruled:** *"EP42 records that a step change happened at a review. It does not build the review."*
**Status: SUPERSEDED BY OWNER DECISION.** Recorded, not quietly dropped.

Worth being clear about what happened, because it is the outcome a boundary is *supposed* to produce. §14.5's
reasoning was **scope protection** — it stopped performance management arriving by accident, inside an amendment,
as a side-effect of a sentence about review timing. It did not, and should not, stop the owner choosing that
scope **on purpose, with the cost in front of him**. The boundary held until he spent it deliberately. That is
the system working, not the ruling failing.

#### 21.2.2 The two readings, sized honestly

He said *"performance **input** module"* — which leans (a) — and *"with all it's requirement"* — which leans
toward specifying whichever is chosen thoroughly. **The ambiguity is real and I am not resolving it by
assumption in either direction.**

| | **(a) Performance input — minimal** | **(b) Performance management — full** |
|---|---|---|
| **What it is** | A manager-entered band per employee per cycle, existing **only** to feed the hike calculation | Review cycles · goals and objectives · self-assessment · manager assessment · calibration and moderation · ratings history · the review workflow itself · reporting |
| **Stories** | **2** — the policy (bands and multipliers), and the per-employee entry with its scoping | **≈ 20–25** |
| **Where it lives** | **Inside EP43**, as a delineated pair of stories | **Its own epic, EP44**, with its own waves |
| **Delivery** | **≈ 2–3 weeks**, and **no delay to EP43** | **≈ 12–16 weeks**, and under his own re-sequencing instruction it goes **first**, so the hike cycle moves out by **roughly a quarter** |
| **Compliance surface** | One band per person per cycle, single-purpose | Ratings history, calibration, distributions — squarely works-council territory, and one increment away from the Charter §1 gate |
| **Does it deliver what he asked for?** | **Yes** — pay differentiated by performance | It delivers a way to *produce* the rating in-product, which is a **different problem he has not asked to solve** |

#### 21.2.3 **My recommendation: (a). Confidence High.**

Six reasons, in order of weight:

1. **His own sentence is conditional, and it is the tell.** *"implement this first **if required if this the
   blocker**."* He is not commissioning a product line; he is saying *if performance input blocks the hike, do it
   first*. Under (a) nothing is blocked for more than a fortnight. **Under (b), performance management
   *becomes* the blocker he was trying to route around.**
2. **The noun is "input".** He named it by its function — an input to something else. And the context is
   decisive: he wrote it answering *"where does the employee-performance input come from?"*, a plumbing question
   about the hike calculation.
3. **"with all it's requirement" is a quality instruction, not a scope instruction.** He has asked for thorough
   specification repeatedly, from his very first message (*"detailed requirement to the level of software
   engineer"*). It reads as *specify it properly*, not *make it big*.
4. **Nobody has asked to run a performance review in this product.** There is no user story for it, no data, no
   existing process to replace. (b) is the classic HR-suite failure: build the module, no tenant runs a cycle in
   it, the ratings are empty, and the hike differentiation happens in a spreadsheet anyway. **Adoption beats
   feature count**, and (b) has no adoption story.
5. **Time-to-value.** (b) delays every one of the seven original asks by a quarter to deliver a capability
   adjacent to the request.
6. **The compliance surface scales sharply.** (a) is one band per person per cycle. (b) brings ratings history,
   calibration and distributions — and the moment anyone adds a suggested rating or a ranking, the Charter §1
   gate engages in full.

**And (a) is shaped so (b) is an extension, not a rewrite** — the same pattern used for total compensation, FX
and the positions table. The band and multiplier tables are the natural inputs to a future review cycle.

**But he chooses.** §21.7 puts it to him in one row, with the quarter-long cost stated plainly. **The team builds
(a) meanwhile**, and if he picks (b) nothing built under (a) is wasted.

#### 21.2.4 The four consequences, worked through — they apply either way

**1. Epic structure — and yes, this is now a programme, not an epic.** Stated plainly because the coordinator
asked: **BG7 is a multi-epic programme and the roadmap should show it as one.**

| | Stories | Shape |
|---|---|---|
| **EP42** — Compensation, Job Architecture & Pay Equity | **23** | Unchanged. A data model and a check |
| **EP43** — Annual Compensation Review Cycle | **7** (5 + 2 performance-input under (a)) | A recurring business process |
| **EP44** — Performance Management | **unscoped** | **Named, not entered.** Only exists if he picks (b) |

**BG7 total under (a): 30 stories, ~5 months.** Under (b): ~52 stories, ~8–9 months. The A2 split has held up —
if the hike cycle had gone in as EP42 W5, performance input would now be arriving inside a 30-story epic, and I
would be re-cutting it under pressure instead of adding two stories to a sibling.

**2. UX's §25 boundary — rewritten, not deleted, and it matters more now.** Its intent survives and sharpens:

> **Performance is a deliberate, separately-designed surface. The ladder is still not it.**

Concretely, and these are unchanged rules: the step **expectation** stays a *description of a job*, never
criteria to be scored · the **roadmap** stays a statement of expectations, **not a checklist, not a goal list,
not an assessment** · **ADR-025's forbidden-column table stands unchanged** — no rating, score, achievement,
completion or progress column on `job_step_expectations` or `employee_step_roadmaps` · the performance input
lives in **its own tables, its own surface and its own feature code**, and never on the ladder or the roadmap ·
the **nine pre-refused requests survive and several get sharper**, because *"can we tick off roadmap items?"*
becomes far more likely to be asked once a performance surface exists next door.

**3. GDPR and works councils — OQ-8 is promoted from a launch consideration to a design input.** Performance-
related pay is squarely works-council territory in Germany and the Nordics, which is where his seed data lives.
The concrete design consequence, not a note: **the policy must be explicit, versioned, auditable, and
inspectable without exposing any individual's data** — because a works council may need to review and agree the
*bands and multipliers* before the cycle operates. That is a requirement on KAN-216, and BA routes it to the DPO
list alongside DPO-1.

**4. The Charter §1 gate — nothing here crosses it, and I am saying so explicitly so it is not crossed by
increment.** Nothing in (a) or in EP43 **scores, ranks, or automatically decides** anything about a person: a
manager enters a band, a company-configured multiplier turns it into a number, and a human approves the result.
**No automated decision-making, no profiling, no algorithmic ranking.** **The gate engages the moment anyone
proposes a suggested rating, a ranked list of employees, a forced distribution, or any model output that
influences pay** — at which point it needs the full EU AI Act high-risk treatment and GDPR Art. 22 human-in-the-
loop, and it does not enter the backlog until it has them. Standing statement, kept visible.

### 21.3 A3-3 — re-basing: a standing assumption, built against, awaiting confirmation

He did not understand the question; it has been re-put in plain terms and he has been told the recommendation is
**yes**, with work proceeding on that basis.

**Status: ASSUMPTION — build against it, do not record it as a closed decision.** Assumption register entry:

| Item | Type | Impact if wrong | Validation | Owner |
|---|---|---|---|---|
| The annual cycle re-bases the ladder's pay points by the same movement that funds the hike | **Assumption (High confidence, awaiting confirmation)** | If he says no, the equity check is unusable from the first cycle onwards and Check A′ must be re-thought entirely — **KAN-210 stays either way**, because a manual re-base is then the only remedy | A3-3 confirmation | SPM |

**Design consequences, restated because they are easy to lose, plus one refinement from A3:**
- Re-base with the hike; **pay-point history effective-dated** (KAN-206) so a 2026 finding is explicable in 2028.
- **Re-basing and the individual hikes are one cycle, not two independently reachable operations.** A cycle that
  moves salaries without moving pay points must not exist. **Refinement to KAN-210:** the standalone re-base
  action stays — EP42 must be usable without EP43 — but **inside a cycle it is driven by the cycle**, and the
  cycle cannot close having done one without the other.
- **The re-base percentage is employer-set, pre-filled from their own hike percentage, editable.** Consistent
  with A3-1: a pre-fill derived from the company's own number is not a product default.

### 21.4 A3-4 — level disclosure resolved, **and my §18.6 ruling is corrected**

*"Ok make Position tile or role, Job family and the it's job family sub levels visible"*

**The settled position — the ladder is public, the pin on the ladder is not:**

| Element | Visible to the employee |
|---|---|
| Their position title / role | **Always** |
| Their **job family** | **Always** — new in A3, previously unstated |
| **Every sub-level in that family, with each level's and step's expectations** | **Always.** This is the ladder, open by default; `/ladder` as a main-nav surface is **confirmed**, and job family is now an explicit part of what it shows |
| **Where this employee personally sits on it** | **Company-policy switch — the only thing that may be withheld** |
| Their roadmap | **Always**, written as expectations without naming a position when the switch is off |

**The correction to my own §18.6 — the switch governs the STEP, not the level.** This is a genuinely good catch
and I had it wrong. **In his own example the title already discloses the level:** *Junior Software Fullstack
Engineer* **is** level 2 of that family, and he has just said the title is always visible. A switch labelled
"hide the level" would therefore hide nothing — a false claim, and standing rule 6 forbids exactly that.

- **The switch is `Display the employee's step`, default on, per company** (not per employee).
- With it off: the employee sees their **role, their family, and every level's expectations**, but **no step
  number and no "you are here" marker within their level**.
- **The manager always sees the step** — they author the roadmap and cannot do it blind. The switch never
  applies to the manager, HR, the register, reporting or the audit trail.
- **My Pay drops every pay-point reference when the switch is off**, not just the step number: a level's base
  pay point plus a published increment plus your own salary lets you compute your step. That is CFL-42-39's
  inference class again, and the surface list must cover it.
- The honest labelling from §18.6 stands and now applies to the step: **"do not display", never "hide"** — an
  employee can still often infer their step by matching expectations, and the configuration screen says so.

### 21.5 What A3 changes

| # | What | Status |
|---|---|---|
| 1 | **§14.5** — EP42 does not build the review | **SUPERSEDED BY OWNER DECISION.** A performance module is authorised; §21.2 sizes it |
| 2 | **§18.6** — the disclosure switch governs the *level* | **CORRECTED — it governs the *step*.** The title already discloses the level |
| 3 | **UX §25** — the performance-management ban list | **REWRITTEN, not deleted.** Intent survives and sharpens (§21.2.4 item 2). ADR-025's forbidden-column table unchanged |
| 4 | **OQ-8** — works councils | **PROMOTED from launch consideration to design input.** Concrete requirement on KAN-216 |
| 5 | **A2-Q1, A2-Q2, A2-Q4** | **CLOSED** — employer-configured / performance authorised (sizing still open) / ladder open, placement policy-controlled |
| 6 | **A2-Q3 (re-basing)** | **Standing assumption**, built against, awaiting confirmation |
| 7 | **EP43** | **Gains 2 stories** (KAN-216, KAN-217) under recommendation (a). **BG7 becomes a multi-epic programme** |
| 8 | **EP44 — Performance Management** | **NAMED, unscoped, not entered.** Only exists if he picks (b) |
| 9 | Everything in §12, §16, §18.1–§18.5, the nearest-step rule, the job-family model, EP42's 23 stories and its build order | **Unaffected** |

**Conflict register — one addition:**

| ID | Conflict | Sev | Ruling |
|---|---|---|---|
| **CFL-42-58** | **A2 §6 and §18.6 built a switch to hide the job level, but the job title already discloses it** — *Junior Software Fullstack Engineer* **is** level 2, and the title is always visible. The switch as specified would have hidden nothing while claiming to. | Medium | **Corrected (§21.4): the switch governs the STEP.** Recommend and confirm with him rather than shipping a control that announces what it conceals. |

### 21.6 Story and epic changes

| Story | Change |
|---|---|
| **KAN-190** | The first-run prompt now asks about **step** display, not level display. Copy corrected. |
| **KAN-194** | The switch governs the **step**; **My Pay drops every pay-point reference** when off (not just the step number — inference, CFL-42-39). Never applies to manager / HR / register / reporting. Per company, not per employee. |
| **KAN-207** | Disclosure-off rendering: role and family **visible**, every level's expectations **visible**, **no step number and no "you are here" marker**. |
| **KAN-210** | **+** inside a cycle, re-basing is **driven by the cycle** and a cycle cannot close having moved salaries without moving pay points. The standalone action stays, because EP42 must work without EP43. |
| **KAN-212** | Re-pointed: the performance band is defined in **KAN-216** and entered in **KAN-217**, not duplicated here. |
| **KAN-216** *(new, EP43)* | **Performance-input policy** — company-defined bands and multipliers on an admin page. **Nothing predetermined and nothing suggested.** **Versioned, auditable and inspectable without exposing individuals' data**, because a works council may need to agree the bands before the cycle runs (OQ-8, now a design input). |
| **KAN-217** *(new, EP43)* | **Per-employee performance input** — a manager enters a band per employee per cycle. **Single-purpose:** written in a cycle, read by that cycle, used for nothing else; absent from the profile, the directory, the org tree and every export; **no rating-history surface**; row-scoped like pay, with its own negative-visibility suite; **not shown to the employee by default**. |

**Build order:** EP42 unchanged (23 stories, W0–W4). **EP43 becomes 7 stories** —
`KAN-216 → KAN-217 → KAN-211 → KAN-212 → KAN-213 → KAN-214 → KAN-215`, with the performance-input pair **first**,
honouring his *"implement this first if this is the blocker"*. **EP44 named, unscoped, conditional on (b).**

### 21.7 For the product owner — replaces §19

*Nothing here blocks; everything has a default being built against. **OQ-5, A2-Q1, A2-Q2 and A2-Q4 are now
closed.***

**The one decision I need from you, and it is a quarter of delivery time:**

| | Question | What I recommend |
|---|---|---|
| **★** | **You asked for a "performance input module". That reads two ways and they are very different sizes.** **(a)** the manager records a performance band for each person each cycle, which feeds the pay calculation and does nothing else — **2 stories, about 2–3 weeks, no delay to the hike cycle.** **(b)** full performance management — review cycles, goals, self-assessment, calibration, ratings history — **about 20–25 stories, 12–16 weeks, and because you said to do it first if it blocks, it would push the hike cycle out by roughly a quarter.** | **(a).** Your own words point there — *"performance **input**"*, and *"if required if this the blocker"*. Nobody has asked to *run* a performance review in this product; what you asked for is pay differentiated by performance, and (a) delivers exactly that. **(b) is a fine product and it is a different one.** We are building (a) now and it is shaped so (b) can extend it later rather than replace it. |

| # | Question | Default being built | Cost if late |
|---|---|---|---|
| **1. A3-3** | **When you set the annual hike, should the system also raise the defined salary for every level and step by the same percentage** — so a step 2.0 written as €50,000 becomes €52,000 after a 4% hike? | **Yes**, and we are building it. If not, the fairness check flags your whole workforce from the first cycle — we checked the arithmetic. Recorded as an assumption awaiting your confirmation, not as a decision made for you. | High if the answer is no |
| **2. A3-4** | **What exactly may be hidden from an employee?** Your job title already tells them their level — *Junior Software Fullstack Engineer* **is** level 2. So a switch that hides "the level" hides nothing. | **The switch hides the STEP (2.3), not the level.** Role, job family and every level's expectations stay visible always. And an honest caveat on the setting itself: they can still often work their step out by matching expectations, so it prevents display, not inference. | Low |
| **3. OQ-9** | **Two different people on any pay approval**, the initiator may not approve, no SYSTEM_ADMIN bypass. **No tenant has a configured approval chain today**, so without a seeded two-level default this control binds nobody. | All three, plus a seeded HR_ADMIN → PORTAL_ADMIN chain. | Low to change, high to omit |
| **4. OQ-8** | **Works councils** — are any target customers subject to consultation on pay or job classification? **This got more important**: performance-related pay is squarely works-council territory in Germany and the Nordics, where your seed data is. | Assume yes for Germany and the Nordics. We are designing the policy to be versioned and inspectable so a works council can review it without seeing anyone's data. | Not a build blocker; **a launch blocker** |
| **5. OQ-2 · OQ-7** | Who sees a salary by default (manager: direct reports only; department/location heads: nobody; employees: their own), and is compensation **off** for every company until you switch it on. | As stated · yes, off. Both seed values, changeable in one click. | Very low |
| **6. OQ-BA-13 · OQ-4 · OQ-6 · OQ-A1-1/2/3** | Six one-line confirmations: the roadmap is **acknowledged**, not agreed (*"Confirm we discussed this"*) · your example ladder was illustrative · one currency per pay market · we flag when pay does not match the step · advancing a step **proposes** a pay change rather than applying it · EP42 records that a step change happened at a review — **and, now, performance is a separate module rather than part of the ladder.** | All as stated. | Very low each |

**Two things that are not questions:** the first real pay figure entered — even one, even by us — triggers the
security phase before anything else ships; and until real login exists the pay visibility model is correct in
code and **unenforceable in practice**, which every compensation demo will say at the start.

### 21.8 Wave 6 tasking — deltas to §20

**All of §20 stands.** These are additions.

- **BA** — §14.5 marked **superseded by owner decision**, not deleted. Criteria for **KAN-216/217** at outline
  depth, with the **works-council inspectability** requirement on the policy and the **single-purpose**
  constraint on the input written as testable rules. Correct every "level disclosure" criterion to **step**
  disclosure (**CFL-42-58**). Route performance data to the DPO list.
- **Architect** — no ADRs for EP43 yet; **do add one paragraph** on where a performance band sits so it cannot
  be reached from the ladder or the roadmap. **ADR-025's forbidden-column table is unchanged and now more
  load-bearing.** Confirm the step-disclosure switch is a display rule on one field, not a fifth feature code.
- **UX** — **rewrite §25, do not delete it**: *"performance is a deliberate, separately-designed surface, and the
  ladder is still not it."* Expect *"can we tick off roadmap items?"* to be asked more often once a performance
  surface exists next door, and pre-refuse it there too. Redesign the disclosure-off view for **step**, not
  level: role and family visible, every level's expectations visible, **no "you are here" marker**.
- **UAT** — the negative-visibility suite extends to the performance band (it must be absent from the profile,
  directory, org tree, exports and every payload outside its cycle). Assert the step-disclosure switch hides the
  **step** and **not** the role or family, and that **My Pay drops pay-point references** when it is off.

*A3 folded in. EP42 unchanged at 23 stories; EP43 at 7; EP44 named and not entered.*

---

> **§21.7 above is SUPERSEDED by §22.13 below.** Amendments A4, A5 and A6 close four questions, overturn the
> epic's central mechanism, and replace the owner's page entirely.

---

# 📌 AMENDMENTS A4, A5 and A6 — 2026-08-09 — the owner overturns the pay/step model

> **Authoritative. A6 outranks A5, which outranks A4, which outranks A3, A2, A1, §12, §14, §16, §18, §21 and
> every specialist document.** Sources: `EP42_OWNER_ANSWERS_A4.md`, `A5.md`, `A6.md`.
>
> **A4 and A5 were never written into this document** — the session that received them was stopped. They are
> applied here for the first time, together with A6.
>
> **The headline: "pay position implies step position" was never the owner's model. It was ours.** He has
> rejected it in the strongest terms he has used — *"No you have not got correct!!"* — and with it goes the
> compa-ratio basis, the nearest-step rule, and KAN-191/KAN-209's step-fitting backfill. **§22.0 states the
> corrected model. Read it before anything else in this file, including everything above this line.**
>
> **Nothing above is edited.** Superseded rulings stay standing and marked, as this document has done
> throughout. A decision log that quietly rewrites itself teaches nobody anything — and this amendment is the
> clearest evidence yet of why the trail matters.

## 22. Amendments A4–A6

### 22.0 THE CORRECTED PAY/STEP MODEL — stated once, unambiguously

**One direction. It only runs one way.**

```
        job content & responsibility  →  STEP  →  BASE PAY
```

**and never**

```
        BASE PAY  →  STEP                        ⛔ FORBIDDEN
```

Four sentences, and every one of them is a rule:

1. **A step is an assignment about what work someone does.** It is decided by a human, at a review, from job
   content and responsibility (A1). Nothing else may set it.
2. **The step determines base pay.** A step has a defined value; an employee's base pay **is** that value,
   scaled by FTE. Base is derived, not observed.
3. **Pay never determines the step.** The system must never propose, infer, imply, suggest, pre-select or
   "fit" a step from a salary figure — not in the backfill, not in an import, not as a helper, not as a
   default, not in a tooltip. **This is a prohibition, not a preference.**
4. **Money that is not the step's value is `additional pay`** — a separately-governed, attributed amount that
   sits beside base and never moves the step (§22.3).

**The worked example, in his numbers** (A6 §6). Level 2, Full Stack Software Engineering. Global HR sets for
2027: **2.0→2.1 = 2%**, **2.1→2.2 = 2.4%**. Step 2.0 = €50,000, so 2.1 = €51,000 and 2.2 = €52,224.

| Person | Step | Base | Additional | Total cash | Correspondence check |
|---|---|---|---|---|---|
| **Maria** — assessed at her review as meeting 2.1's expectations | moves 2.0 → **2.1** | €50,000 → **€51,000** | — | €51,000 | base = step value → **no finding** |
| **Tom** — about to resign; local HR grants 5% to keep him | **stays 2.1** | **€51,000** *(unchanged)* | **€2,550** *(retention)* | €53,550 | base = step value → **no finding**; the €2,550 is visible, attributed and explainable on its own terms |

**Tom is not "a 2.2 now."** His job has not changed, so his step has not changed. The retention money does not
touch the ladder. That single sentence is the whole amendment.

**What this buys us, and it is a lot:**
- **The correspondence check becomes an equality, not an estimate.** Base either equals the step's value or it
  does not, and any difference is a real deviation rather than an artefact of somebody's counter-offer.
- **The "dead zone" problem disappears.** It existed only because pay was being mapped back onto steps.
- **The day-one alert storm largely dissolves** — see §22.4 for the part that does not, and how it is handled.
- **Two people at the same step in the same market are paid the same base, by construction.** R5's original
  ask — *"flag if there is a difference of let say 5% for the same position"* — is satisfied more strongly than
  any check we designed: the difference cannot arise from base at all, and if it arises from additional pay it
  is attributed to a named reason. **We are not quietly dropping his first request. We are making it
  structurally impossible to violate silently.**

**The cost, named honestly and paid in §22.4:** the step can no longer be derived from anything the system
already holds. Every one of the 146 seeded employees needs a **human** step assessment. That work is real, it
belongs to the tenant, and it is the price of the correction. It is the right price.

---

### 22.1 ⚠️ THE CHALLENGE PASS — which premises are the owner's, and which are ours

**This section exists because the epic's central mechanism was a team inference that nobody re-examined for
five rounds.** Before applying A6 I went back through the epic and asked one question of every load-bearing
premise: *whose is this?* I am reporting everything I found, including what I concluded is still sound —
because "I checked it and it holds" is a result, not a non-answer.

**The classification I am introducing, and it is now mandatory (see §22.15):**

| Label | Meaning |
|---|---|
| **OWNER** | Traceable to the owner's own words, quoted. |
| **EVIDENCE** | Derived from the repository, the schema or the database, with a `file:line` or a query behind it. Not the owner's, but not an opinion either. |
| **TEAM** | A team inference. Reasonable, argued, possibly right — **and not validated by either of the above.** |

#### 22.1.1 The register

| # | Premise | Origin | Verdict after A6 |
|---|---|---|---|
| 1 | **Pay position implies step position** — compa-ratio, then the nearest-step rule, then the step-fitting backfill | **TEAM** — entered at §14.1 as *"the reading that honours both"*, was flagged as an inference (OQ-A1-1), and then hardened across five documents | **⛔ FALSE. Killed by A6 §2.** This is the one. |
| 2 | **The ±2% tolerance** as the finding boundary | **TEAM** (mine, §14.2.2) | Already self-corrected in §16.2; **now dead entirely** — base is derived, so there is nothing to tolerate but rounding (§22.5.3) |
| 3 | **The nearest-step rule** | **TEAM** (mine, §16.2) | **⛔ Withdrawn in full** (§22.2) |
| 4 | **Check B — a group gender pay gap** | **TEAM. This is my biggest finding of the pass and it is not small.** It came from S13 — my own reading of the EU Pay Transparency Directive, labelled *Assumption / Medium confidence, not verified against any source in this repo*. **The owner has never mentioned gender pay, a gap, a group, or a regulator.** OQ-3 was recorded "CLOSED by reinterpretation" in A1 — but the reinterpretation closed *what "5%" means*; it never asked *does he want a gender check at all*. A question was marked closed by an answer to a different question | **Sound as a product idea, unvalidated as a requirement.** Ruled in §22.1.3 — **descoped from the critical path and put to him.** |
| 5 | **A per-employee annual "hike percentage", differentiated by performance within a budget** (A2-1's ruled default, §18.4.3) | **TEAM** — a reading of *"for each"* | **⛔ WRONG. A6 §4 says "for each" means for each step transition.** Withdrawn (§22.5) and it collapses most of EP43 (§22.11) |
| 6 | **`PAY_ABOVE_STEP` means somebody "is really at a higher step"** | **TEAM** | **⛔ Withdrawn as an interpretation.** It survives only as *"this base was set off-ladder"*, which under A6 should be rare (§22.2) |
| 7 | **Bands as a min/max envelope (KAN-205)** | **TEAM** | **Descoped to Later.** With base = step value, a band answers a question the step value already answers. Deleting a story is the right direction after A6 |
| 8 | **The "HR responsible" is the feature matrix, no new role** (D2) | **TEAM** | **Sound but stressed.** A6 §5 describes two HR authorities the matrix cannot currently tell apart. Re-ruled in §22.6 |
| 9 | **Everyone defaults to step `.0` in the backfill** | **TEAM** | **⛔ Withdrawn.** Under A6, `.0` is a *claim about job content* made by the system with no human behind it. Replaced by an explicit `STEP_NOT_ASSESSED` state (§22.4) |
| 10 | **The compensation feature's primary output is a finding queue** | **TEAM** | **Partly wrong.** At initial load the right instrument is a **reconciliation**, not a queue; findings are the exception stream afterwards (§22.4) |
| 11 | **EP42 / EP43 split** (§18.4) | **TEAM** (mine) | **Holds, contents change.** A6 shrinks EP43 substantially (§22.11) |
| 12 | **`PROMOTION` → `LEVEL_CHANGE` with a direction** | **TEAM** | **Sound, unaffected.** Downward moves are real and an audit row must not lie |
| 13 | **§14.5 — EP42 does not build the review** | **TEAM** (mine) | **SUPERSEDED BY OWNER DECISION** (A3, confirmed A4 §4, cost accepted A5 §2). §22.8 |
| 14 | **The disclosure switch governs the step, not the level** | **TEAM**, put to him and **confirmed by A5 §1** | **Now OWNER. Closed** (§22.9) |
| 15 | **Compounding, not linear** | **TEAM** | **Sound, and generalises** to per-transition rates (§22.5.2) |
| 16 | **Pay markets** as part of the grouping key and the home of annualisation constants | **EVIDENCE** — Telia spans five countries; Porto pays 14 monthly instalments and Hamburg 12 | **Sound, and reinforced.** A6's central rate schedule with per-market entry values needs exactly this object |
| 17 | **R6 is a prerequisite of R5** | **EVIDENCE** — Acme 46 employees / 41 titles / one title with n≥3; Telia 100 / 75 / six | **Sound.** Unchanged by anything in A4–A6 |
| 18 | **The two self-approval defects** (DEF-42-4/5, KAN-203) | **EVIDENCE** — `app/routes/org_change.py:55-64`, `app/services/org_change_service.py:222-249` | **Sound, and now explicitly protected** against erosion by A4-1 (§22.7) |
| 19 | **Four-eyes binds nobody today** — `org_change_workflows` returns 0 rows | **EVIDENCE** | **Sound** |
| 20 | **The tenant switch is not in the central resolver; 14 of 18 rows are FALSE** | **EVIDENCE** | **Sound** |
| 21 | **Money never reaches `audit_log`** | **EVIDENCE** — `_SECRETISH_KEYS` catches no money term; the `audit_log` read audience is a different feature code | **Sound, and extended to additional pay** (§22.3) |
| 22 | **Entry at `.0`; `step_count = 5` means six values `.0…​.5`** | **OWNER** — his own `2.0 … 2.5` | **Sound** |
| 23 | **Job family → level, title on the level, levels family-scoped** | **OWNER** — his Full Stack Software Engineering example | **Sound** |
| 24 | **No automatic roll-up on reaching the top step** | **OWNER** — A1 confirmed it explicitly | **Sound** |
| 25 | **Each step carries its own responsibilities and expectations; the manager authors a per-employee roadmap** | **OWNER** — A1, twice | **Sound, and now more important**: it is the *only* legitimate input to a step assessment (§22.4) |
| 26 | **The step increment applies to base** | **OWNER** — A2 (base only) + A6 (base tied to the step) | **Sound** |
| 27 | **Advise, do not block** | **OWNER** — A4 §2, his own words and his own reasoning | **Sound, and bounded in §22.7** |

#### 22.1.2 One inference channel that A6 makes *worse*, and nobody has spotted it

**CFL-42-59 — new, High.** CFL-42-39 established that a published step increment plus a known base pay point
plus a known step lets you compute a colleague's salary, so another person's step is scoped exactly as their
pay is. **Under A6 that inference stops being approximate and becomes exact**, because base pay **is** the step
value — no negotiation noise, no drift. It also runs in reverse: **anyone who learns a colleague's base pay
learns their step to the euro**, and vice versa.

Consequence, ruled: **the step-disclosure switch and the pay-visibility model are now two views of one
control and must be reasoned about together.** Where an employee may not see a colleague's pay, they may not
see that colleague's step; where the tenant has switched step display off, published pay points must not be
readable by an employee either (already ruled in §21.4 for My Pay — it now extends to the ladder surface).
**The `pay_policy:r` grant (§22.6) is where this is enforced.**

#### 22.1.3 The three team premises I am acting on

**(a) Check B — descoped from the critical path and put to him. Confidence High.**

*Observation.* The gender pay-gap check is the second-largest single body of work in W4 and it carries
KAN-208 (synthetic gender, which **changes live vacation-eligibility behaviour for 146 employees** —
CFL-42-43), DPO-1 (a purpose-limitation question on Art. 9 data), the entire statistical machinery, CFL-42-32
and CFL-42-38.
*Evidence.* Nothing the owner has written in six messages mentions gender, a gap, a group or a regulator. Its
sole origin is S13, my own general-knowledge reading of a directive, self-labelled *Assumption, Medium
confidence, not verified against any source in this repo*.
*Impact.* We were about to change behaviour in a shipped feature, and ask a DPO to clear special-category
processing, to feed a check nobody asked for.
*Recommendation.* **Keep it — pay-transparency measurement is a defensible product idea and compliance is a
first-class requirement — but stop carrying it as though it were his.** Concretely: **Check B, KAN-208 and
DPO-1 move off the critical path into one clearly separable slice** that can be dropped without touching
anything else, **KAN-208 comes out of W0**, and the question goes to him in plain words. Until he answers,
Check B is **⬜ conditional**.
*Expected outcome.* W0 loses its riskiest story, the DPO conversation narrows to DPO-2 (retention) which
actually blocks something, and if he says "I never asked for that" we lose nothing.

**(b) The per-employee hike percentage — withdrawn.** A6 §4 is explicit and §18.4.3's default is simply wrong.
Consequences in §22.5 and §22.11.

**(c) Bands (KAN-205) — moved to Later.** Base = step value answers "is this pay sane for this level" exactly,
where a band answered it approximately. **Removed from EP42.**

#### 22.1.4 What I checked and found sound — stated because a challenge pass that only reports breakage is a
sales pitch

The wave model · W0's contents apart from KAN-208 · **KAN-203 and every four-eyes ruling** · KAN-188 and
ADR-016 in full · KAN-189, half-open intervals and the CFL-4 resolution · the audit money-redaction rule and
amendment A-2 · the job-family model · entry at `.0` and the step-count arithmetic · no automatic roll-up ·
the step expectations and the roadmap (KAN-190, KAN-207) · pay markets and the annualisation constants ·
`LEVEL_CHANGE` and its direction · "absent, not hidden" · the six standing rules in §13.5 and §16.6 ·
R6-before-R5 · T5 and the demo-auth disclosure.

**None of that is touched by A4–A6.** The epic's shape survived; its central *arithmetic* did not.

---

### 22.2 A6 §2 — what dies, and what survives of the nearest-step rule

> *"that does not mean he will be assigned to 2.4 or 2.3 just to match the salary"*

**Withdrawn in full, as a step-assignment mechanism and as a description. Confidence High.**

A6 §2 offered the nearest-step rule a narrow survival — *"it may survive only as a way of describing a base-pay
deviation, never as a statement about which step someone occupies."* **I am taking the stronger option and
withdrawing it entirely, and here is why the weaker one is wrong:**

*"Ravi is recorded at step 2.4 but paid closer to step 2.2"* is a sentence about Ravi's **step**. It does not
matter that the system has not moved him; the sentence puts the move in the reader's head, and the reader is an
HR administrator with a keyboard. **Standing rule 6 — a label is a claim** — applies to a finding's copy
exactly as it applied to a button that said *Accept*. A description that invites the precise inference the
owner rejected is not a safe description.

**What replaces it — and it is simpler than what it replaces:**

| | Withdrawn | **Replacement** |
|---|---|---|
| The question | "Which step is this person's pay nearest to?" | **"Does this person's base equal their step's value?"** |
| The arithmetic | nearest-neighbour over every step's pay point, on relative distance, with a tie rule | **one subtraction** |
| Expressed as | "paid closer to step 2.2" | **"base is €2,430 (4.8%) below the value of step 2.4"** — a magnitude, in currency and percent, against **their own** step and no other |
| Reference to another step | central to the mechanism | **forbidden anywhere in the product** — no copy, no tooltip, no export, no notification, no API field |

**`PAY_BELOW_STEP` and `PAY_ABOVE_STEP` both survive as finding types**, with the asymmetric severity of §14.1
intact (below is primary — *"they took the responsibility, the pay never followed"*; above is secondary and
silent per CFL-42-48). What changes is what `PAY_ABOVE_STEP` **means**: it is no longer "they might really be
at a higher step". Under A6, over-payment has a legitimate home — additional pay — so a residual
`PAY_ABOVE_STEP` now means precisely **"this base was set off-ladder and nobody attributed the difference"**,
which is a governance and data-quality signal, and it should be rare. Its remedy is not a step change; it is
**"record the difference as additional pay with a reason"** (§22.3), and that becomes its quick action in the
register alongside `PAY_BELOW_STEP`'s "Propose adjustment".

**Also withdrawn with it:** the tie rule (UAT-F-13), the relative-vs-absolute distance metric (F-13b), the
half-increment boundary, and every fixture that computes a nearest step. **Deletions, not rework.**

---

### 22.3 A6 §3 — additional pay. Base and additional are two amounts, separately governed

> *"implement additional pay field which will [hold] any additional payment of such situation … so he will get
> usual hike 2.1 let say 2% but the additional pay will contain additional that employee will receive due to
> this special resignation situation"*

**Accepted as designed, as a new story — KAN-218, W2, Must · P1.**

| | **Base pay** | **Additional pay** |
|---|---|---|
| Governed by | **The step's defined value**, as at a date, × FTE | **A human decision for a named reason**, outside the ladder |
| Moves when | The step moves, or the ladder's economics move | Somebody decides it does, and records why |
| Example | Step 2.1 = €51,000 | +€2,550 retention |
| Feature gate | `compensation` r/w (unchanged) | `compensation` r/w — **the same code**; it is individual pay and local HR's job (§22.6) |

**This refines OQ-5, it does not reverse it.** He said *"base salary only at this point"* and has now added
**one** clearly-scoped supplementary component. **Architect: the record holds base and additional pay as two
distinct, separately-governed amounts. Do not open a general `compensation_components` table on the strength of
this** — §18.1's extensibility rule already records that shape, and a recorded shape is what that register is
for. One named component is not a components model.

#### 22.3.1 The open details, ruled

**A6 §3 carried recommendations. I am taking all of them, and adding three.**

| # | Question | **Ruling** | Confidence |
|---|---|---|---|
| 1 | **Reason code?** | **Mandatory, from a seeded company-editable list** — `Retention` · `Market premium` · `Red-circled legacy pay` · `Temporary responsibility` · `Location or assignment allowance` · `Transitional (ladder adoption)` · `Other (text required)`. A free-text-only reason is unreportable, and the whole value of this field is that it makes the exception *legible* | **High** |
| 2 | **Effective dated?** | **Yes, from the start**, half-open, ADR-020's convention, same as base. Retrofitting effective dating is a rewrite; adding it now is a column | **High** |
| 3 | **Time-boxed?** | **An optional end date — and where there is none, a mandatory review date, default 12 months.** A6's concern is exactly right: *a retention premium nobody ever revisits becomes invisible permanent salary*. But a hard expiry would silently cut somebody's pay on a date nobody remembers, which is worse. **So: never auto-expire; always come back and ask.** Premiums past their review date surface in the additional-pay register with the age shown | **High** |
| 4 | **Does it count toward Check B (gender gap)?** | **Yes — Check B compares base + additional.** A gap paid through premiums is still a gap, and a check that looked only at base would be trivially avoidable by paying the difference as a premium. *(Moot while Check B is conditional — §22.1.3 — but ruled now so it is not re-derived later)* | **High** |
| 5 | **Does it count toward the step-correspondence check?** | **No — that check uses base only.** Its question is *"does base match the step's value"*, and the entire point of A6 is that additional pay is **outside** the ladder. Including it would re-create the thing we just removed: money moving the step | **High** |
| 6 | *(mine)* **Is additional pay an amount for visibility, audit and export purposes?** | **Yes, in every respect.** `compensation:r` to see it; **never in an `audit_log` diff** (ADR-019's per-action allowlist extends to it — `has_additional`, `reason_code`, `direction`, `pct_change_band`, effective date; never a figure); absent from every payload for anyone without scope; included in the watermarked export; included in "My Pay" for the subject | **High** |
| 7 | *(mine)* **Does granting additional pay go through the approval chain?** | **Yes. It is a `COMPENSATION_REVIEW`**, on the existing engine, and **KAN-198's four-eyes applies** — two different people, initiator may not approve. Nothing about A6 makes this money less consequential than base; if anything the discretionary, off-ladder nature makes two pairs of eyes *more* necessary. There is no separate lightweight path | **High** |
| 8 | *(mine)* **Is a high rate of additional pay itself a signal?** | **Yes, and this is the best thing the field gives us beyond Tom's case.** The register reports, per level and market, **what fraction of total cash is additional pay**. A level where a third of the money sits outside the ladder is a level whose ladder is set wrong — and that is a far more useful management insight than any individual finding. **Should · P3 inside KAN-218.** Same instrument as the override-rate reporting in §22.7 | **Medium-High** |

**One thing additional pay is explicitly not:** a place to put anything that is not covered above. It is not
bonus, not commission, not equity, not allowances-in-general, not benefits, not total compensation. §3.3's
exclusion list stands unchanged. If someone proposes a second component, that is OQ-5 re-opening and it comes
to me.

---

### 22.4 A6 §2 — the replacement for the step-fitting backfill. **The hardest item in this pass.**

**The problem, stated precisely.** KAN-191/KAN-209 fitted each employee's step to their existing salary. That
is now forbidden. But the fitting was also the mitigation for the day-one alert storm (§14.2.5): without it,
everyone lands at `.0`, base ≠ step value for almost everybody, and the register opens with 146 findings on
the first morning. **The replacement has to solve the backfill and the storm, and it cannot use salary for
either.**

**It does, in three parts. Confidence High on the shape, Medium on the effort estimate.**

#### 22.4.1 Part 1 — where a step comes from now

**From the job, assessed by the person who knows the job: the employee's manager.**

| Input | Who | Where |
|---|---|---|
| **Family and level** | HR, via the title→level mapping screen (unchanged) | KAN-191, W1 |
| **Step** | **The subject's solid-line manager**, choosing from the step expectations authored in KAN-190, for each of their direct reports | **KAN-191, W1** *(new)* |
| **Override** | Any `job_architecture:w` holder, with a mandatory reason | KAN-191 |
| **Nothing** | — | **The default. See below** |

**Three rules on this, and they are the load-bearing ones:**

1. **Nothing is pre-selected, and nothing may be suggested.** No default step, no "based on tenure", no
   inferred value, and absolutely nothing derived from pay. This is D4c's discipline (*mandatory to answer, not
   mandatory to change, nothing pre-selected*) applied to the one field A6 exists to protect. A pre-selection
   is a system claim about somebody's job content.
2. **`STEP_NOT_ASSESSED` is a real state, distinct from step `.0`.** The old design defaulted everyone to `.0`,
   which is a *claim* — it says "this person is at entry level for their position". Under A6 the system may not
   make that claim. An employee in `STEP_NOT_ASSESSED` has **no derived base**, is **not evaluable** by the
   correspondence check, and is **listed for assessment**. It renders as *"Step not yet assessed"*, never as
   `2.0`, never as a dash, never as a blank — D7's empty-state rule, which we already apply to a missing
   salary, applied to a missing step. **This closes a hole nobody had noticed.**
3. **The assessment cites the expectations.** The manager picks a step by reading what that step means in this
   company (KAN-190's authored expectations) and confirming the person is doing it. That is the mechanism A1
   describes, used for the purpose A1 describes. **If a company's ladder is not described, its steps cannot be
   assessed** — which makes R-18 (a ladder with content nobody can use) a hard adoption dependency rather than
   a soft quality worry, and it is worth saying so out loud.

#### 22.4.2 Part 2 — what makes 146 human judgements survivable

**Distribute them.** This is the adoption question and it decides whether the epic works.

- **One HR person assessing 146 people is a project.** Forty-odd managers assessing three or four people each
  is a **ten-minute task**, and they are the only people who can do it correctly anyway.
- The surface is the manager's existing team list with the step expectations inline, one control per person,
  one submit, and a "why" field that is optional except on an override.
- **HR gets a completion meter**, can chase, and can assess directly for anyone with no manager (Acme has one
  company-less record; every tenant has orphans).
- **This is the same population, the same screen family and the same judgement as KAN-207's roadmap authoring**
  — a manager who is about to write "here is what 2.2 requires of you" has already decided the person is at
  2.1. **Sequencing consequence: assessment and roadmap authoring should be one sitting**, and UX should design
  them that way rather than as two visits.

**Effort, stated rather than hidden:** this is more human work than fitting was. Fitting was one click for HR.
This is 146 assessments plus the dispositions in Part 3. **That is the price of the owner's correction, and it
is the right price** — the alternative was a ladder built backwards from salaries, which is what he rejected.

#### 22.4.3 Part 3 — what replaces the storm mitigation: **a reconciliation, not a queue**

**KAN-209 is repurposed, not deleted.** It keeps its ID, its position at the end of W2 and its role as the W2
exit gate. Its content changes completely:

> **KAN-209 — Ladder pay reconciliation.** For every assessed employee, compare **recorded base** with **the
> step's value as at the reconciliation date**, and require **one recorded disposition each** before the
> correspondence check is allowed to run for that company.

**It opens with the totals, not with a list.** The first thing HR sees is the aggregate, because the first
question an HR director asks is *"what does adopting this ladder cost me?"*:

> *132 of 146 assessed · 89 already match · 31 below their step value by €214,000 in total · 12 above by
> €58,000 · 14 not yet assessed*

**Three dispositions, mandatory, none pre-selected:**

| # | Disposition | What it does | Available when |
|---|---|---|---|
| **1** | **Align** | Sets base to the step's value on an effective date. Creates a normal compensation record with reason `Ladder adoption` | Always |
| **2** | **Attribute the difference as additional pay** | Base becomes the step value; the surplus becomes an **attributed premium** with a reason code and a review date (§22.3). **This is precisely what A6 §3 invented additional pay for, applied to history** | base **>** step value |
| **3** | **Accept a residual deviation** | Base is left as it is, with a mandatory reason and a review date. Produces a finding that is **already dispositioned `JUSTIFIED`** on the day the gate opens | Always |

**Approval: the reconciliation is approved once, as a batch, by two people.** Routing 31 individual
`COMPENSATION_REVIEW` requests through the chain is absurd and would guarantee the work never finishes.
**KAN-198's four-eyes binds the batch** — two different people, and the person who prepared it may not approve
it. *(This sets the precedent EP43's cycle approval will inherit; better to establish it here, once, on 146
rows, than to invent it later on 500.)*

**The gate.** The **ladder-adopted-and-reconciled gate** (renamed from ladder-fitted-and-reviewed) **ships
CLOSED with KAN-206** and is opened only by KAN-209's completion. Unassessed employees do **not** block the
gate — they block only their own evaluability, and they are counted and shown.

**Day-one finding count is therefore zero by construction** — the same outcome §16.2's nearest-step rule
achieved, reached **honestly**: because a human decided every case, rather than arithmetically, because the
system quietly re-labelled everyone's step to match their salary. **That difference is the whole amendment in
one sentence.**

#### 22.4.4 What this does to the build order — a defect of mine dissolves

**CFL-42-41 is closed, not by a workaround but by A6.** The build-order defect I shipped in Wave 4 was that
step fitting sat in W1 while the pay points and pay data it fitted against arrived in W2. **Job-based step
assessment needs neither.** It needs a described ladder (KAN-190) and a manager, both of which exist in W1.

| Half | Old | **New** |
|---|---|---|
| **Step assignment** | KAN-209, W2, fitted from pay | **KAN-191, W1, assessed from the job** |
| **Pay reconciliation** | — *(did not exist; the fitting hid the problem)* | **KAN-209, W2 last, human dispositions** |

**W1 becomes stronger again:** a described ladder, everybody assessed onto a step by their own manager, every
employee able to read what their next step requires — **and still not one salary anywhere in it.**


---

### 22.5 A6 §4 — the rate is per step-transition, per year, set by Global HR

> *"Global HR department decided from 2.0 to 2.1 the hike will be 2% this year while from 2.1 to 2.2 it will
> be 2.4"*

This sharpens A2's *"for each year company defines its own hike percentage for each"*. **"For each" means for
each step transition** — not per employee, not per level, not company-wide.

#### 22.5.1 The rate schedule — a new shape, and the Architect's is wrong

**Ruled: the rate lives on the transition and is year-scoped. Confidence High.**

| | Architect's current design (ADR-024) | **Under A6** |
|---|---|---|
| Where the rate lives | `step_increment_pct` on `job_levels` — **one rate per level** | **One rate per transition**: 2.0→2.1, 2.1→2.2, 2.2→2.3 … each its own number |
| Per-transition variation | `job_step_increment_overrides`, **the exception path** | **The normal case.** There is no "the level's rate" to override |
| Time | none — the rate is a current value | **Year-scoped, with history.** *"this year"* means next year's schedule is different and last year's must still be readable |
| Authored by | `compensation:w` | **`pay_policy:w`** — Global HR (§22.6) |

**So: `step_increment_pct` on the level is withdrawn, and `job_step_increment_overrides` is withdrawn as an
override table and re-founded as the schedule itself** — every transition carries a rate for every effective
period, and there is nothing for it to be an exception to. **Architect: this is a table rename and a
re-modelling, not a new subsystem, and it is cheaper than what it replaces because the two-tier
rate/override lookup collapses into one.**

**Why year-scoping is not optional.** A finding raised in 2027 was computed against 2027's schedule. If 2028's
schedule overwrites it, that finding becomes inexplicable — the exact failure §18.4.4 already ruled against for
pay points. **Pay points are already effective-dated (KAN-206). The rate schedule must be too, on the same
half-open convention, and `step_pay_point()`'s as-at date now selects both.**

#### 22.5.2 Compounding — survives, and generalises

**The compounding ruling stands. Uniform compounding was the special case.**

```
point(step n)  =  entry_value  ×  Π (1 + r_t)        for transitions t = 1 … n
                                 t
```

His own numbers verify it: 2.0 = €50,000 · 2.1 = 50,000 × 1.02 = **€51,000** · 2.2 = 51,000 × 1.024 =
**€52,224**. A linear reading would give 2.2 = 50,000 × (1 + 0.02 + 0.024) = €52,200 — €24 apart on one
transition, and diverging with every rung. **Ruled compound, as before, and now confirmed against the owner's
own arithmetic rather than against my reasoning.** BR-1.5's exact-decimal, no-intermediate-rounding, HALF_UP-
once rule applies unchanged.

**What gets simpler:** the compound-vs-linear ambiguity that made §14.2.1 worth ruling largely evaporates —
with a rate per transition you walk the transitions, and there is no plausible way to walk them that is not
multiplicative.

#### 22.5.3 The tolerance constraint — **gone, and there is nothing left to constrain**

The `tolerance < increment / 2` rule was already dissolved in §16.2. A6 removes even the residue:

- **Base is derived from the step, not observed independently.** The check is an equality, not a
  nearest-neighbour search. There are no adjacent bands to overlap, so **R-16 stays closed and there is no
  cross-field constraint anywhere in the model.** CFL-42-36, CFL-42-37, CFL-42-45 and CFL-42-53 stay dissolved.
- **What survives is a materiality threshold, and it governs notification only.** Ruled: **company-configurable,
  default 1%, applied to `|base − step value × FTE| ÷ step value`.**
- **The critical property, and it is what stops this becoming a dial that hides the truth: the deviation is
  always computed, always shown in the register with its magnitude, and always counted in the reconciliation
  totals — whatever the threshold is set to.** The threshold decides whether a bell rings. It never decides
  whether a number exists. A tenant who sets it to 50% suppresses noise; they cannot suppress fact.
- **Per-transition rates make any half-increment rule meaningless anyway** — with 2% below and 2.4% above,
  "half the increment" is two different numbers depending which way you look. Another reason the mechanism had
  to go.

#### 22.5.4 The re-basing question — **it does NOT survive in its old form, and I am not asking it a fourth time**

**I checked, as A6 §4 instructed. Verdict: the question we have asked three times is dead. A different,
narrower question has taken its place, and it is a first asking, not a fourth.**

**Why the old question is dead.** It was: *"when the company grants an annual across-the-board hike, should the
ladder's pay points move by the same percentage?"* That question has two premises and A6 removes both.

1. It assumed **an across-the-board per-employee hike that moves salaries independently of the ladder.** Under
   A6 there is no such thing. Pay moves because the step moves (at that transition's rate) or because the
   ladder's own numbers move. **Premise 5 in §22.1.1 — withdrawn.**
2. It assumed **base pay and the step's value can drift apart and need re-synchronising.** Under A6 base pay
   **is** the step's value. They cannot drift. There is nothing to keep in sync, because they are one number.

**And the consequence that makes the old question incoherent rather than merely unnecessary: under A6, moving
the ladder and paying people are the same act.** Raise step 2.1's value from €51,000 to €52,020 and every
employee at 2.1 is, by definition, owed €52,020 — there is no second operation. That is the opposite of the old
model, where re-basing was a bookkeeping correction that had to chase a pay event. **KAN-210 therefore stops
being "a maintenance action that keeps the check honest" and becomes "the mechanism by which a company grants
an across-the-board rise."** That is a promotion in importance, and it is why KAN-210 stays firmly inside EP42.

**What survives, and it is genuinely new.** A6 §4 anticipated it precisely: *does the entry value of a level
(step x.0) also move each year, or only the transition rates above it?* This is not the same question in
smaller clothing. It is the question **"does an employee whose job has not changed get a rise?"** — and it has
a concrete, one-number answer he can give in ten seconds:

> **Anna is at step 2.1 all through 2027 and 2028. She does her job well. Her responsibilities do not change.
> What is her base pay in 2028?**

That is Q1 on the one-pager (§22.13), with three options and three numbers. **It has never been put to him, it
is not abstract, and the reason the previous three attempts failed is that they were.**

**The default being built meanwhile:** the entry value is **effective-dated and employer-authored, with no
annual expectation imposed** (A3-1 — nothing predetermined), **plus a staleness warning** where a level's entry
value has not moved within the company's configured period (default 18 months). That is option C in §22.13 and
it is buildable without his answer.

---

### 22.6 A6 §5 — Global HR and local HR. Two authorities, and the product has one role

> *"Global HR department decided…"* / *"the local HR department decides…"*

| Authority | Decides | Scope |
|---|---|---|
| **Global HR** | The ladder's economics — entry values, the per-transition rate schedule, pay markets, the materiality threshold | Company-wide, annual |
| **Local HR** | One person's pay — a base change, an additional-pay grant, a deviation disposition | Individual, ad hoc |

**Ruling: this is a permissions distinction, and I am giving it a fifth feature code — `pay_policy`.
Confidence High.**

#### 22.6.1 The ruling

| Code | Governs | Seeded defaults |
|---|---|---|
| **`pay_policy`** *(new)* | **Global HR.** Entry values, the per-transition rate schedule and its history, pay markets and their annualisation constants, the materiality threshold, the re-base action (KAN-210) | `HR_ADMIN` r+w · `PORTAL_ADMIN` r+w · everyone else none |
| `compensation` | **Local HR.** An individual's base pay, additional pay, the reconciliation dispositions, proposals through the chain | Unchanged (§4.5.1) |
| `compensation_self` · `pay_equity` · `job_architecture` | Unchanged | Unchanged |

**Why a fifth code rather than the two we have.** The distinction he describes is *not expressible* with
`compensation:w` alone: one grant would let a local HR administrator re-author the company's entire pay ladder
because they were allowed to give Tom a retention premium. That is precisely the argument that earned
`job_architecture` its fourth code in §14.3.2 — *a manager could not do the thing the owner says is their job
without being granted write access to everyone's salary* — running in the other direction. **The feature-code
matrix is the mechanism `CLAUDE.md` mandates for exactly this question, and reaching for it here is using the
model rather than working around it.**

**And it is a net simplification, not just an addition.** CFL-42-20 parked the equity thresholds, the coverage
gate and pay markets on **`company_settings:w`** because there was no better home and a role check was
forbidden. There is now a better home. **They move to `pay_policy:w`**, which:
- gives UX **one gate per screen instead of two** — the "Compensation Settings page must read coherently to a
  holder of one gate and not the other" problem in CFL-42-20 disappears;
- makes the grant honest at the point it is made (*"set the company's pay policy"* rather than
  *"company settings"* — standing rule 6);
- keeps CFL-42-20's actual ruling intact: **it is still not a role check.** `pay_policy` is seeded to
  HR_ADMIN + PORTAL_ADMIN and a tenant may widen or narrow it in one click.

**Registered in all four places in KAN-199** — the first story in W2 that needs it. Per §14.3.2's note, EP42
has no single "register the codes" story; each registers what it needs.

**Reading is gated too, and this matters more than it looks.** `pay_policy:r` is required to see entry values
and rate schedules, because **CFL-42-59 (§22.1.2) makes them exactly invertible into a colleague's salary**
under A6. The ladder's *structure* and *expectations* stay public on `job_architecture:r`; its *money* does not.

#### 22.6.2 What I am NOT building, and the question that goes to him

**Reading (b) — organisational scoping**, where HR for the Nordics can act on Nordic employees and not on
Hamburg — is **not** being built on this evidence. It would add a scoping dimension to every compensation query
and every admin surface, it changes the access model the whole product uses, and nothing he has written asks
for it: *"the local HR department"* is at least as likely to mean *"the HR people who handle individual cases"*
as *"the HR people in one country"*.

**It goes to him as Q2 on the one-pager (§22.13), with the distinguishing question stated as a fact about one
person:** *can Lars in Oslo grant additional pay to a Hamburg employee?* If the answer is no, that is reading
(b), it is a separate epic, and it is a platform change rather than a compensation feature.

**Named limitation, recorded now:** under reading (a), scope is per-company, so a `compensation:w` holder can
act on any employee in the company. This is the same class of gap as CFL-42-22 (the model cannot express
"read company-wide, write nothing"), and it is recorded in the release notes and in
`BUSINESS_OVERVIEW_FEATURES_AND_ACCESS.md` rather than papered over. **Revisit if he answers (b), or if OQ-8
comes back "yes".**

---

### 22.7 A4 §2 — **advise, do not block** — and the boundary that protects KAN-203

> *"the application will raise red flag if the hike is made beyond the set levels to manages. But local HR
> managers can always overrde the system recommedation because otherwise there might be a situation that
> employee may leave and so on but it will be sytem to raise this as flag to managers."*

**Adopted as a standing product principle for BG7. It is his, it is right, and it is more valuable than the
question that produced it.** His logic: a pay rule that blocks is a rule that loses you people; the local HR
manager has context the system does not; so the system's job is to make the exception **visible**, not to
prevent it.

**Note how well it composes with A6.** The retention counter-offer he used to justify the principle now has a
*place to live* — additional pay. So the flag fires less often and means more when it does. The two amendments
were written to solve different problems and they solve each other's.

#### 22.7.1 The rule, written down so it cannot be quoted out of shape

> **Where the system holds an opinion about *how much money is right*, it advises and records; it never
> refuses.**
> **Where the system holds a rule about *who may act*, it refuses, and the refusal is not overridable.**
> **Where the system cannot compute a true answer, or cannot record what was decided, it refuses to
> proceed — but it never refuses the decision itself.**

Three categories. Every guard in this programme belongs to exactly one, and the category decides the behaviour.

| | **Category 1 — a judgement about an amount** | **Category 2 — an integrity control** | **Category 3 — record completeness and computability** |
|---|---|---|---|
| **Behaviour** | **Advise. Allow with an override** | **Refuse. Never overridable, never configurable** | **Refuse to proceed without the input. Never refuse the outcome** |
| **Test** | Would a reasonable HR manager with more context legitimately do this anyway? | Does this put one person on both sides of a decision about themselves or their own money? | Does the refusal stop them reaching the outcome, or only reaching it without a record? |
| **Members** | base above or below the step's value · a step move whose pay does not follow the transition rate · pay outside a band · an over-budget distribution · additional pay above a configured size · a level's entry value below the previous level's top step | **KAN-203** subject ≠ initiator · **KAN-203** subject ≠ decider · **KAN-198** initiator ≠ approver on money · **KAN-198** approver ≠ approver across levels · **KAN-198** ≥2 independently satisfiable levels on a money-bearing request · **no SYSTEM_ADMIN bypass of any of these** | a mandatory reason · a mandatory reason **code** · the mandatory pay answer on a position change (D4c) · the mandatory `review_context` on a step change · a multi-currency pay market with no FX rate · a step assessment with no assessor · a cycle opened with no authored policy |

**The anti-erosion clause, and it is the point of this section:**

> **The Category 2 list above is closed and enumerated. A future amendment may add to it. Nothing may be
> removed from it by citing A4-1, because A4-1 is a statement about *amounts* and says nothing whatever about
> *actors*.** Nobody overrides *"you may not approve your own pay rise"* for retention reasons — that is the
> control existing at all. If a future reader believes an integrity control is blocking a legitimate business
> case, the answer is a **configuration fix or an administrative remedy** (KAN-198's cancel-and-reconfigure
> path, Ruling 13), **never an override.**

**And the Category 3 clarification, because this is where the principle will actually be misapplied:**
requiring a reason is **not** blocking. It does not prevent the manager giving Tom €2,550; it prevents them
doing it anonymously. If somebody argues that a mandatory reason code violates advise-don't-block, they have
confused a record with a veto. **Apply the test in the table.**

#### 22.7.2 Override mechanics — first-class, never a silent bypass

Every Category 1 override, without exception:

1. **A recorded actor** — the human being, not "the system" and not the role.
2. **A mandatory reason** — a **category** from the seeded, company-editable list, plus optional free text.
   Structured, so it is reportable; A-2's rule holds — the free text carries the non-blocking numeric-pattern
   warning and no criterion may claim a guarantee over it.
3. **An `audit_log` row** — with the money-out-of-diff rule intact (ADR-019's per-action allowlist):
   `override_of`, `reason_code`, `direction`, `pct_change_band`, effective date. **Never a figure.**
4. **Visible to the approval chain at decision time, not merely logged.** An approver deciding a request that
   carries an override sees *"this proposal is 6.3% above the value of step 2.1; reason: Retention"* on the
   decision surface. An override the approver has to go and look for is an override that was not disclosed.
   *(This is the same reasoning that suppressed the bell's one-click approve — CFL-42-28.)*
5. **Overridable ≠ invisible afterwards.** An overridden flag stays in the register as `OVERRIDDEN` with its
   reason, and is reportable. It does not vanish because somebody clicked through it.

#### 22.7.3 Override rates are data a company should see

**A4-1's last line is the most useful thing in it and it was nearly buried:** *a company whose managers override
80% of flags has a mis-set band, and the product should be able to show them that.*

**Ruled, Should · P3, in KAN-202** (which already owns history, reporting and the audited export — no new
story):

- **Override rate per company, per level, per market, per reason code.**
- **A configuration-review tripwire at 40% overridden**, matching §1.5's existing *">40% of flags dispositioned
  JUSTIFIED → review the configuration"* rule. One number, one meaning, two instruments. Above it, the register
  says so in words: *"managers have overridden 62% of pay flags at level 2 in the Nordics. This usually means
  the ladder's rates are set below the market, not that 62% of decisions were exceptional."*
- **Paired with the additional-pay share report** (§22.3.1 item 8): a high override rate and a high additional-
  pay share are the same disease seen from two angles, and both say *the ladder is wrong*, which is a far more
  actionable finding than any individual case.

**Terminology.** He says *"red flag"*; the product already has a `pay_equity` finding. **Ruled: one object, not
two.** A proposal-time warning and a post-hoc finding are the same computation at two moments, and giving them
different names would make the product speak two vocabularies about one fact. **The word in the UI is
"flag" for both, with the finding type carrying the meaning.** *(UX: red must not be the only signal — WCAG
1.4.1 — and "red" is questionable colour for a case HR is expected to override routinely and legitimately.
Your call on the palette; the vocabulary is ruled.)*

#### 22.7.4 Where the flag fires — a new moment, not a new feature

A4-1 asks for the flag *"if the hike is made beyond the set levels"* — i.e. **at the moment of proposal**, not
after the fact. **Ruled: this is the correspondence computation run inside the proposal surface. It is not a
new story.**

- **KAN-192** (step advancement) — when the pre-filled pay proposal is edited away from the transition rate,
  the deviation is shown inline with its magnitude, and submitting requires a reason category.
- **KAN-196** (pay inside the position-change request) — same, on the compensation block.
- **KAN-218** (additional pay) — same, where a premium exceeds a configured share of base.
- **KAN-209** (the reconciliation) — the "accept a residual deviation" disposition **is** this override, taken
  in bulk.

**This is standing rule §13.5.1 — consequences are shown where the choice is made, not where the surprise
lands — applied for the fifth time.** It is now the most-invoked rule in the epic, which is a sign it is a good
one.

---

### 22.8 A4 §4 and A5 §2 — full performance management. **EP44 is real.**

> **A4:** *"I want a full performance-management capability (cycles, goals, calibration) a detailed performance
> requirement impmlemation."*
> **A5:** *"OK. go ahead with full implemenation cycle as Product owneer accepting the delay."*

#### 22.8.1 The decision, and it is closed

**He chose (b). Recorded as: recommended (a), owner chose (b). It is not re-litigated here or anywhere.**

He named the three things option (b) contained — *cycles, goals, calibration* — so this is a considered choice
against a stated cost, not a misread. And in A5 he accepted the cost **in his capacity as product owner and in
those words**. Both go in the Decision Log verbatim, because this is exactly the decision somebody
re-litigates six weeks from now:

> **Decision D-006 — 2026-08-09.** *Context:* the SPM sized a performance **input** (2 stories, ~2–3 weeks, no
> delay) against full performance **management** (~20–25 stories, 12–16 weeks, sequenced first, pushing the
> hike cycle out by roughly a quarter) and recommended (a) with Confidence High.
> *Options considered:* (a) performance input inside EP43; (b) full performance management as EP44.
> *Decision:* **(b).** The owner's words: *"I want a full performance-management capability (cycles, goals,
> calibration) a detailed performance requirement impmlemation"* and *"go ahead with full implemenation cycle
> as Product owneer accepting the delay."*
> *Rationale:* his, not mine. He was shown the quarter of slip and took it.
> *Impact:* EP44 becomes a real epic of 22 stories, sequenced **between** EP42 and EP43. BG7 becomes ~50
> stories and ~8–9 months. EP43 shrinks (§22.11).

#### 22.8.2 §14.5 — SUPERSEDED BY OWNER DECISION

> **§14.5 ruled:** *"EP42 records that a step change happened at a review. It does not build the review."*
> **Status: SUPERSEDED BY OWNER DECISION.** Recorded, not deleted.

**And it did its job.** §14.5's purpose was scope protection — it stopped performance management arriving *by
accident*, inside an amendment, as a side-effect of a sentence about review timing. It did not, and should not,
stop the owner choosing that scope **on purpose, with the cost in front of him.** The boundary held until he
spent it deliberately. That is the system working, not the ruling failing.

**What still holds from §14.5, and this part is not superseded:** **EP42 itself still does not build the
review.** A step change in KAN-192 still records a `review_context` and a date, and nothing more. The review is
built in **EP44**, and the two connect through one named seam (KAN-236, §22.11.3). **UX §25's ban list and
ADR-025's forbidden-column table stand unchanged and are now *more* load-bearing**, because performance
management existing next door is precisely when somebody asks whether roadmap items can be ticked off.

#### 22.8.3 The two compliance items are now design inputs, carried — not notes

**These are the reason EP44 gets a compliance wave rather than a compliance paragraph.**

**(1) EU AI Act / GDPR Art. 22 — Charter §1. The gate is designed in from story one.**

A full performance capability **with calibration**, feeding **pay**, is on the doorstep of *"a decision with
legal or similarly significant effect"*. Nothing proposed scores, ranks or auto-decides — **but calibration is
exactly where forced distributions and ranked lists live**, and it is one plausible-sounding increment away.
So, ruled as requirements on EP44 rather than as warnings about it:

- **KAN-232 is a story, in the calibration wave, not an appendix** — human-in-the-loop attestation on every
  rating that changes in calibration, an explainability record (what changed, who changed it, why), and a hard
  product rule that **no ranking, score or distribution is ever computed by the system and applied to a
  person**.
- **Forced distribution is refused, not configurable.** Distribution is **shown** (KAN-230) so a calibration
  session can see its own shape; it is never **enforced**. A configurable forced curve is an automated decision
  with significant effect wearing a settings page.
- **Bias testing is a story (KAN-240), not a launch task** — measure the rating distribution across the
  protected characteristics the tenant lawfully holds, **report, never auto-correct**.
- **Flagged for DPO/legal validation** (Charter §9.7). Nothing in any EP44 document is legal advice.

**(2) Works councils — OQ-8 is now plausibly market-gating, and I am saying so plainly.**

Performance management with calibration, feeding pay, across Germany and four Nordic countries — which is
exactly where the seed data lives — is close to the definition of a co-determination matter. It was a launch
consideration in A2, a design input in A3; **under A4 it is plausibly a gating dependency for those markets.**

The concrete design consequence, carried as a requirement (KAN-238, and inherited from KAN-216's precedent):
**the policy — the rating scale, the review forms, the calibration rules, the rating-to-pay mapping — must be
versioned, auditable and inspectable without exposing any individual's data**, because a works council may need
to review and agree it *before* the first cycle operates. **A launch blocker, not a build blocker; and it is on
the Customer-Readiness checklist, not the sprint board.**

#### 22.8.4 The scope-growth statement — said once, factually, without editorialising

**A4 §4 asked for this and it is owed.**

> **His original request was: hold salary, put people on job levels, and flag a 5% pay difference.**
> **It is now a three-epic programme of about 50 stories and 8–9 months: EP42 (23) → EP44 (22) → EP43 (5).**
>
> He has chosen every increment with the cost shown, and each choice is defensible on its own. That is his
> right and I am not arguing with any of them. **But the cumulative shape deserves to be stated once, plainly,
> rather than discovered.** It is in the one-pager (§22.13) as a fact, not a question.

---

### 22.9 A5 §1 — the step-disclosure switch: **CLOSED**

> *"for #4: goa head with your recommendation."*

**A per-company switch governing the STEP, defaulting to visible.** The recommendation put to him in A4 §5 is
adopted. **This moves from "awaiting confirmation, built against" to a closed decision** — the design does not
change; it is settled rather than assumed.

The rationale on record, and it is the reason the switch governs the step rather than the level: **the title
already discloses the level.** *Junior Software Fullstack Engineer* **is** level 2 of that family, and he has
said the title is always visible (A3-4). A switch claiming to hide the *level* would hide nothing while
claiming to, which standing rule 6 forbids. The only thing meaningfully withholdable is the step.

**Everything already specified stands unchanged** — §21.4's rules, KAN-190's first-run prompt, KAN-194's
visibility model, KAN-207's disclosure-off rendering, the *"do not display, never hide"* labelling, the honest
sentence about inference, the manager always seeing the step, and CFL-42-57's manager-who-is-also-an-employee
case.

**One thing A6 adds to it — and it tightens the switch rather than loosening it.** Per CFL-42-59 (§22.1.2),
base pay is now **exactly** the step's value, so under A6 the step and the salary are mutually invertible with
no noise at all. Consequence, ruled: **where step display is off, the level's entry value and the rate schedule
must not be readable by that employee either** — `pay_policy:r` is not granted to `EMPLOYEE`, and My Pay's
existing rule (drop every pay-point reference when the switch is off, §21.4) extends to the `/ladder` surface.
**The ladder's structure and expectations stay public. The ladder's money does not.**

**A4 §5 housekeeping — "personal level".** He asked what the term meant; it was ours, and it was used before it
was defined. Recorded: **the ladder** is the structure, identical for everyone and always visible; **the
personal level** is the pin on the ladder — which level and step *this* employee occupies. Only the second is
policy-controlled, and after A5 only its **step** component. The term itself is retired from the vocabulary in
favour of *"the employee's own step"*, which needs no definition.

---

### 22.10 What A4–A6 invalidate, document by document

**Every row is superseded, not deleted.** Specialists mark, they do not erase — §22.15 is about why the trail
matters.

#### 22.10.1 This document (SPM)

| # | What | Status | Where it went |
|---|---|---|---|
| 1 | **§16.2 — the nearest-step rule** | **⛔ WITHDRAWN in full**, as a mechanism *and* as a description | §22.2 — base vs the step's own value, expressed as a magnitude |
| 2 | **§14.2.1's compa-ratio remnants and §14.2.2's tolerance-as-boundary** | **⛔ Dead** | §22.5.3 — a materiality threshold that governs notification only |
| 3 | **§14.2.5 — "the backfill fits the step to the pay"** | **⛔ FORBIDDEN** | §22.4 — job-based assessment by the manager, then a human reconciliation |
| 4 | **§14.2.1 — one increment per level with per-step overrides** | **Superseded** | §22.5.1 — a rate per transition, year-scoped |
| 5 | **§18.4.3 / A2-1 — "a company guideline % per pay market, differentiated per employee"** | **⛔ WRONG. Withdrawn** | §22.5.4 — "for each" means each step transition. It collapses most of EP43 |
| 6 | **§18.4.4 / A3-3 / CFL-42-54 — the re-basing question and its arithmetic** | **Moot in that form** | §22.5.4 — the drift it described cannot occur when base *is* the step's value. Replaced by the entry-value question (Q1, §22.13) |
| 7 | **§4.1 / §14.2's `PAY_ABOVE_STEP` as "really at a higher step"** | **Superseded** | §22.2 — it means "this base was set off-ladder", and its remedy is additional pay |
| 8 | **D1's Check B as a settled requirement** | **Re-classified TEAM, conditional** | §22.1.3(a) — off the critical path, put to him |
| 9 | **§4.5.1 / §14.3.2 — four feature codes** | **Amended to five** | §22.6 — `pay_policy` added |
| 10 | **CFL-42-20 — thresholds on `company_settings:w`** | **Superseded** | §22.6 — `pay_policy:w`. The ruling that it must not be a role check is **preserved**; only the home changes |
| 11 | **§14.5 — EP42 does not build the review** | **SUPERSEDED BY OWNER DECISION** | §22.8.2. *EP42 still does not build it; **EP44** does* |
| 12 | **§21.2.3 — the SPM recommends (a)** | **Closed: recommended (a), owner chose (b)** | §22.8.1, Decision D-006. Not re-litigated |
| 13 | **§21.7 — the owner's page** | **Superseded** | §22.13 |
| 14 | **A1 §5 / D3.5 / KAN-205 — bands** | **Descoped to Later** | §22.1.3(c) |
| 15 | **CFL-42-41 — the build-order defect** | **CLOSED by A6, not worked around** | §22.4.4 |
| 16 | **"everyone defaults to step `.0`" in the backfill** | **⛔ Withdrawn** | §22.4.1 — `STEP_NOT_ASSESSED` is a distinct state |
| 17 | **A5-1 / the disclosure switch as "awaiting confirmation"** | **CLOSED** | §22.9 |
| 18 | **OQ-A1-1** ("we flag when pay does not match the step — is that what you meant?") | **Answered by A6, and the answer was no to the mechanism, yes to the intent** | §22.0 |
| 19 | **OQ-A1-2** (a step change proposes rather than applies pay) | **Confirmed and strengthened** — the proposal is now pre-filled from the transition rate | Unchanged; §22.7.4 adds the inline deviation warning |
| 20 | **Everything in §12, §16 (except §16.2), §18.1–§18.3, §18.6, §21.1, §21.4** | **Unaffected** | — |

#### 22.10.2 Business Analyst — `EP42_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`

**Invalidated:** §4.4A (Check A′) in full · §4.5A's fitted-backfill rules · **AC-200-\*** for the primary check ·
**AC-206-\*** (the increment model and the tolerance) · **AC-209-\*** in full · **AC-191-\*** step-related
criteria · §3.2's four-code model · §4.4's Check B **status** (unchanged in content, now conditional) ·
BR-10.\* (the increment/tolerance rules) · §21.4A's contingency register · KAN-205's §28 in full.
**Explicitly NOT invalidated:** §4.1 money/precision · §4.2 annualisation and FTE · §4.3 effective dating ·
§4.7 GDPR · §4.8 visibility · §4.9 audit · §5, §6, §13, §14, §15 (KAN-188/189/196/197/198) · §26 (KAN-207).

#### 22.10.3 Senior Architect — `EP42_TECHNICAL_DESIGN.md`

**Invalidated:** **ADR-024** substantially — `step_increment_pct` on `job_levels` is the wrong shape and
`job_step_increment_overrides` is the wrong concept; the tolerance `CHECK` is withdrawn (again, and this time
permanently) · **ADR-023**'s Check A′ computation · §12.4.1's step model where it implies a derived-from-pay
step · §5.2's feature-code registration (four → five) · §3.3's compensation table set (base + additional) ·
§12.6's Check A′ boundary.
**Explicitly NOT invalidated:** ADR-014 money · ADR-015 the effective-dated record · ADR-016 the tenant switch
· ADR-017 family/level/step *structure* · ADR-018 row scoping · ADR-019 money out of `audit_log` (**extended**
to additional pay) · ADR-020 half-open intervals · ADR-021 · ADR-022 four-eyes · ADR-025's forbidden-column
table (**more load-bearing**, §22.8.2).

#### 22.10.4 UX — `EP42_UX_SPEC.md`

**Invalidated:** §7.9 (the fitted-step review screen) — replaced by a **manager step-assessment** screen in W1
and a **reconciliation** screen in W2 · §23 (KAN-206) for the rate schedule and the withdrawn tolerance · §14's
finding copy wherever it names another step · §13 (KAN-205) — descoped · §3.1's surface map (five codes) ·
§13.0's compa-ratio framing.
**New surfaces required:** manager step assessment (§22.4.2) · the reconciliation with totals-first (§22.4.3) ·
additional pay and its register (§22.3) · the rate-schedule authoring surface (§22.5.1) · the inline deviation
warning at proposal time (§22.7.4).
**Explicitly NOT invalidated:** §3 discretion by design · §15 the bell · §22 KAN-207 · §25 the performance line
(**rewrite again, do not delete** — §22.8.2) · every accessibility annotation.

#### 22.10.5 UAT — `EP42_UAT_TEST_PLAN.md`

**Invalidated:** **F13–F19** (the step-pay-point fixtures) in their nearest-step and tolerance parts · F-12,
F-13, F-13b (tolerance inclusivity, the tie rule, the distance metric) — **the questions no longer exist** ·
the KAN-200 Check A′ case set · the KAN-209 case set in full · KAN-205's cases · KAN-208's cases **paused**.
**Explicitly NOT invalidated:** the 21-attack confidentiality catalogue (**extend to additional pay and to
`pay_policy`**) · F1–F12's money and FTE arithmetic · Check B's statistical fixtures (**preserved, paused, not
deleted** — §22.1.3(a) is a scope question, not a quality one) · the negative-visibility approach · the
regression-suite plan · the Demo Gate pack.

---

### 22.11 Stories, waves and the corrected build order

#### 22.11.1 EP42 — still 23 stories. A6 removes as much as it adds.

**One new story (KAN-218), one removed (KAN-205 → Later), one repurposed (KAN-209), one made conditional
(KAN-208). Net zero, and I am naming that rather than presenting it as free.**

| Story | Change under A4–A6 |
|---|---|
| **KAN-190** | **+** the step expectations are now the **only** legitimate input to a step assessment, so ladder-description completeness is a hard dependency of KAN-191, not a quality nicety (R-18 escalates) |
| **KAN-191** | **+ step assessment moves here from KAN-209** — the subject's solid-line manager assesses each direct report against the authored step expectations; **nothing pre-selected, nothing suggested, and never anything derived from pay**; `STEP_NOT_ASSESSED` is a distinct state that is not step `.0`; HR completion meter and override-with-reason. **Design it in one sitting with KAN-207's roadmap authoring** — same person, same judgement, same screen family |
| **KAN-199** | **+ registers the fifth feature code `pay_policy`** in all four places; pay markets and the annualisation constants move to `pay_policy:w` |
| **KAN-206** | **Substantially re-specified.** The rate is **per transition, per year**, with history: `step_increment_pct` on `job_levels` is withdrawn and `job_step_increment_overrides` is re-founded as the schedule itself. Entry values stay effective-dated. **The tolerance is withdrawn**; a **materiality threshold (default 1%) governs notification only** and never suppresses a computed number. Gated **`pay_policy:w`**. `step_pay_point(as_at)` resolves the schedule *and* the entry value at that date |
| **KAN-210** | **Promoted in importance.** Under A6 moving the ladder **is** granting the rise — there is no second operation. Also carries the annual re-authoring of the rate schedule. Gated `pay_policy:w` |
| **KAN-218** *(new, W2)* | **Additional pay** — a second, separately-governed amount beside base: mandatory reason code, effective-dated, optional end date with a mandatory review date otherwise, routed as a `COMPENSATION_REVIEW` through the chain with four-eyes, never in an `audit_log` diff, in "My Pay" for the subject, and an **additional-pay register** with the per-level share report. **Must · P1** |
| **KAN-209** | **Repurposed. Same ID, same slot, new content: the ladder pay reconciliation** — totals first, three mandatory dispositions per employee (**align** · **attribute the surplus as additional pay** · **accept a residual deviation with a reason**), approved **once as a batch by two people**, and it opens the **ladder-adopted-and-reconciled gate** (renamed) |
| **KAN-200** | **Check A″ is an equality, not a search.** `base` vs `step value × FTE` as at the evaluation date; magnitude in currency and percent against **their own step**; **no reference to any other step anywhere**; materiality threshold governs notification only; per-employee evaluability preconditions gain `STEP_NOT_ASSESSED`. **Check B unchanged in content and ⬜ conditional in status** |
| **KAN-201** | **+** `PAY_ABOVE_STEP` gains the quick action **"Attribute as additional pay"** beside `PAY_BELOW_STEP`'s "Propose adjustment" — under A6 the over-payment case has a legitimate home and the finding should carry the route to it. `GENDER_GAP` ⬜ conditional |
| **KAN-202** | **+** the **override-rate and additional-pay-share reporting** with the 40% configuration-review tripwire (§22.7.3). **+** the timeline shows base and additional pay as two series, never summed into one line |
| **KAN-192 · KAN-196** | **+** the **inline deviation warning at proposal time** with a mandatory reason category on override (§22.7.4). KAN-192's pre-filled amount now comes from **that transition's** rate |
| **KAN-208** | **⬜ Conditional and out of W0.** Moves into the Check B slice; nothing depends on it until he confirms Check B. Side benefit: W0 loses its only story that changes live behaviour in a shipped feature (R-19 drops out of the critical path) |
| **KAN-205** | **Removed from EP42 → Later.** With base = step value, a min/max envelope answers approximately what the step value answers exactly |
| **KAN-188 · KAN-189 · KAN-193 · KAN-194 · KAN-195 · KAN-197 · KAN-198 · KAN-203 · KAN-204 · KAN-207** | **Unchanged**, except that KAN-193/194/195 must carry additional pay through the record, the visibility model and the import alongside base |

#### 22.11.2 EP43 — shrinks from 7 to 5, and A6 is why

**A6 collapsed EP43's central mechanism as well as EP42's, and it is the same collapse.** The per-employee
annual hike percentage was an artefact of the same wrong model — pay moving independently of the step. Under
A6 pay moves for exactly three reasons, and a discretionary per-person percentage is none of them:

| Reason pay moves | Where it lives |
|---|---|
| The step moved | EP42 — KAN-192, at that transition's rate |
| The ladder moved | EP42 — KAN-210, and it is the same act as granting the rise |
| An exception, attributed | EP42 — KAN-218, additional pay |

| Story | Status |
|---|---|
| **KAN-216** | **Survives, re-pointed.** The **rating → pay** mapping: company-defined multipliers against the ratings EP44 produces. Still employer-authored, nothing predetermined, nothing suggested, versioned and works-council-inspectable |
| **KAN-212** | **⛔ WITHDRAWN — merged.** Its "market movement per pay market" half is EP42's rate schedule (KAN-206/210); its policy half is KAN-216 |
| **KAN-217** | **⛔ WITHDRAWN — superseded by EP44.** A manager-entered band per cycle was option (a). The owner chose (b), so the rating is produced by the review cycle, not typed into a pay screen |
| **KAN-211 · KAN-213 · KAN-214 · KAN-215** | **Survive, re-specified.** KAN-213's worksheet becomes a **step-movement and additional-pay round**, not a percentage-distribution round |

**EP43 is now a round-management epic, not a differentiation epic** — open a cycle, run the step reviews as a
batch, approve once, apply on an effective date, close out and move the ladder. Confidence **Medium-High**; the
one thing I am inferring is whether he still wants a discretionary per-employee percentage on top, and that is
**Q3 on the one-pager**.

#### 22.11.3 EP44 — Performance Management. Twenty-two stories, KAN-219 … KAN-240.

**Real, entered, and specified to the same standard EP42 got** (*"a detailed performance requirement
implementation"*). Numbering continues from KAN-218. **The compliance wave is designed in from the start, not
bolted on** — that is A4 §4's explicit instruction and it is the difference between EP44 being buildable in
Germany and not.

| Wave | Stories |
|---|---|
| **P0 — foundations** | **KAN-219** the review-cycle object (per company, per period, `DRAFT → OPEN → IN_REVIEW → CALIBRATION → CLOSED`) and the feature codes · **KAN-220** cycle participation and eligibility (joiners, leavers, probation, part-cycle) |
| **P1 — goals** | **KAN-221** goal/objective authoring, employee and manager · **KAN-222** progress and check-ins — **narrative, never scored** · **KAN-223** company goal templates, nothing predetermined |
| **P2 — assessment** | **KAN-224** self-assessment · **KAN-225** manager assessment · **KAN-226** the rating scale — company-defined, versioned, nothing predetermined and nothing suggested · **KAN-227** the review form configurator · **KAN-228** the review conversation record and sign-off — **`Confirm we discussed this`, never `Accept`** (standing rule 6) |
| **P3 — calibration, and the compliance gate** | **KAN-229** the calibration session as a **human forum** with a group view · **KAN-230** distribution **visibility, never enforcement** — a configurable forced curve is an automated decision wearing a settings page · **KAN-231** the calibration change record — every rating change carries actor, reason and before→after · **KAN-232** the **Art. 22 / EU AI Act gate**: human-in-the-loop attestation, an explainability record, and a hard rule that nothing is ranked or scored by the system |
| **P4 — history, visibility, and the two seams** | **KAN-233** ratings history and its visibility model, with its own negative-visibility suite · **KAN-234** the employee's own view and right to comment · **KAN-235** the **pay seam**: EP43 reads a rating; single-purpose, absent from every other surface · **KAN-236** the **step seam**: a review is the `review_context` for a step change and the proposal cites the roadmap it fulfils (A2's narrative link, finally connected to a real review) · **KAN-237** reporting — completion and cycle health only, **no aggregate below n = 5** (CFL-42-32 applies here too) |
| **P5 — governance** | **KAN-238** works-council inspectability — scale, forms, calibration rules versioned and reviewable **without individual data** · **KAN-239** retention, erasure and the DPIA items for performance data · **KAN-240** bias testing across the rating distribution — **measure, report, never auto-correct** |

**Three boundaries EP44 inherits and may not weaken:** the ladder is still not a scoring instrument
(ADR-025's forbidden-column table, UX §25) · money never reaches `audit_log` · and **nothing scores, ranks or
auto-decides** — the moment anyone proposes a suggested rating, a ranked list or a forced distribution, it does
not enter the backlog until it has full EU AI Act high-risk treatment.

#### 22.11.4 The programme, and the build order

```
BG7 — 50 stories, ~8–9 months

EP42 — Compensation, Job Architecture & Pay Equity — 23 stories
  W0  S2   KAN-203(P0) ∥ KAN-204 ∥ KAN-188 ∥ KAN-189
  W1  S3   KAN-190 → KAN-191 (level + STEP ASSESSMENT) → KAN-207
  W2  S3   KAN-199 → KAN-206 → KAN-210 → KAN-193 → KAN-194 → KAN-218 → KAN-195 → KAN-209
  W3  S3   KAN-196 → KAN-197 → KAN-198 → KAN-192
  W4  S3   KAN-200 → KAN-201 → KAN-202
  ⬜ conditional on the owner confirming Check B:  KAN-208 + Check B inside KAN-200/201

EP44 — Performance Management — 22 stories, after EP42
  P0 KAN-219 → KAN-220 · P1 KAN-221 → KAN-222 → KAN-223 · P2 KAN-224 → KAN-225 → KAN-226 → KAN-227 → KAN-228
  P3 KAN-229 → KAN-230 → KAN-231 → KAN-232 · P4 KAN-233 → KAN-234 → KAN-235 → KAN-236 → KAN-237
  P5 KAN-238 → KAN-239 → KAN-240

EP43 — Annual Compensation Review Cycle — 5 stories, after EP44
  KAN-216 → KAN-211 → KAN-213 → KAN-214 → KAN-215

Later:  KAN-205 (bands) · total compensation · pay-transparency statements · statutory gap reporting
```

**Five sequencing rulings:**

1. **EP42 does not wait for EP44.** *"Implement this first if this is the blocker"* was about the **hike
   cycle**, not the compensation record. Nothing in EP42 needs a performance rating: a step assessment is a
   judgement about job content, and A1 already anchored it to a review that happens off-system today.
2. **EP44 goes ahead of EP43**, per his re-sequencing instruction. EP43's differentiation input comes from
   EP44, so the other order builds a cycle with nothing to differentiate on.
3. **EP43's KAN-211 and KAN-215 may run in parallel with EP44's later waves if capacity allows** — they have no
   performance dependency. **A4 §4 asked me to confirm this and that is the answer: partially, and it is a
   capacity call for the Delivery Manager, not a dependency.**
4. **Nothing is blocked while EP44 runs.** KAN-210 gives a company a manual annual round today: re-author the
   rates, move the entry values, and every employee's base follows. That fallback is *stronger* under A6 than
   it was under A2, because moving the ladder now moves the money.
5. **W1 is unchanged as the first shippable slice and W2 is still the minimum shippable slice for EP42.** W2
   now exits with pay recorded, visibility enforced, additional pay available, backfilled, **and the ladder
   reconciled by a human** — a better exit than before.

**The one hard gate is unchanged: KAN-168 (real-DB test tier) still blocks W4.** A6 makes the primary check
arithmetically simpler, which reduces R-12 but does not remove it — Check B, group formation, the exclusion
constraints and every effective-dated lookup are still SQL semantics that a mocked suite cannot prove.

---

### 22.12 Registers — conflicts, risks, assumptions

**Conflicts.** Continuing from CFL-42-58.

| ID | Conflict | Sev | **SPM ruling** |
|---|---|---|---|
| **CFL-42-59** | **A6 makes the step↔salary inference exact.** Base *is* the step's value, so a published entry value + rate schedule + a known step yields a colleague's salary to the euro, and the inference runs both ways. CFL-42-39 ruled this for an approximate channel; it is now exact | **High** | **Ruled §22.1.2 and §22.6.** The ladder's *money* is gated `pay_policy:r`; its *structure and expectations* stay public on `job_architecture:r`. Where step display is off, pay points are unreadable by that employee. **Extends the surface list to a second derivation class** |
| **CFL-42-60** | **The team built its central mechanism on an unvalidated inference and four specialist reviews reinforced it** — "pay position implies step position" was never in the owner's request | **High** *(process)* | **Ruled §22.15.** A Load-Bearing Premise Register, origin tagging, and a challenge instruction in every tasking brief |
| **CFL-42-61** | **Check B has no owner requirement behind it** and carries KAN-208 (which changes live vacation eligibility), DPO-1 (Art. 9 data) and the whole statistical machinery | **High** | **Ruled §22.1.3(a).** Kept, re-labelled TEAM, descoped to a separable conditional slice, KAN-208 out of W0, and put to him |
| **CFL-42-62** | **`step_increment_pct` on the level, with an override table, cannot express per-transition per-year rates** | Medium | **Ruled §22.5.1.** The rate lives on the transition and is year-scoped; the override table becomes the schedule. Architect re-cuts ADR-024 |
| **CFL-42-63** | **A4-1 (advise, do not block) can be read as licence to weaken KAN-203 and KAN-198** | **High** *(pre-emptive)* | **Ruled §22.7.1.** Three categories, a closed and enumerated Category 2 list, and an explicit anti-erosion clause: A4-1 is about amounts and says nothing about actors |
| **CFL-42-64** | **§14.5 (EP42 does not build the review) vs the owner's authorisation of full performance management** | Medium | **Ruled §22.8.2.** Superseded by owner decision. §14.5 still holds *for EP42*; EP44 builds the review |

**Risks.** Continuing from R-19.

| # | Risk | Change |
|---|---|---|
| **R-1** *(alert fatigue)* | **Reduced again, and for a better reason than last time.** §16.2 got day-one findings to zero arithmetically; §22.4.3 gets them to zero because a human dispositioned each case. The second is durable; the first was a property of a mechanism that turned out to be wrong |
| **R-2** *(the mapping is a data project)* | **Worsened, and I am saying so.** It is no longer "map 116 titles to levels" — it is that **plus 146 human step assessments plus a reconciliation disposition each**. The manager distribution (§22.4.2) is the mitigation and it is the difference between a ten-minute task and a quarter-long project. **This is now the single biggest adoption risk in the programme** |
| **R-12** *(equity arithmetic wrong)* | **Reduced.** An equality is far easier to verify than a nearest-neighbour search. KAN-168 still gates W4 |
| **R-16** *(a configuration silently disables the check)* | **Stays closed**, and is now closed twice over: no cross-field constraint exists, and the materiality threshold cannot suppress a computed number (§22.5.3) |
| **R-18** *(the ladder ships with content nobody can use)* | **Escalated to High × High.** Step expectations were a transparency feature; under A6 they are **the only legitimate input to a step assessment**. An undescribed ladder now blocks the backfill, not just the reading experience |
| **R-19** *(KAN-208's vacation side effect)* | **Off the critical path** — KAN-208 is conditional and out of W0 |
| **R-20** *(new)* | **The step assessment is done badly at speed** — forty managers clicking through a list to clear a task, producing a ladder placement nobody believes. **Medium × High.** No acceptance criterion can test it. Held by: the expectations shown inline at the point of choice, nothing pre-selected, HR's completion meter and override, and **a new Demo Gate human-check item — "a manager can explain why this person is at this step"**. Same family as R-18 |
| **R-21** *(new)* | **Additional pay becomes the dumping ground.** Every awkward number gets attributed as a premium, base drifts into fiction, and the ladder looks perfect while meaning nothing. **Medium × High.** Held by the mandatory reason **code** (not free text), the review date, and the **per-level additional-pay share report** (§22.3.1 item 8) — which is the instrument that makes the disease visible |
| **R-22** *(new)* | **EP44 crosses the Art. 22 line by increment.** Calibration is one plausible-sounding feature request away from a forced distribution. **Medium × Critical.** Held by KAN-232 as a story rather than a note, distribution-shown-never-enforced, and the standing statement in §22.8.3 |

**Assumption register — new and changed entries.**

| Item | Type | Impact if wrong | Validation | Owner |
|---|---|---|---|---|
| An employee's base pay **is** the step's value × FTE, exactly, with any difference either attributed as additional pay or recorded as a deviation | **Known** — A6 §6, his own worked example | — | — | SPM |
| The entry value of a level moves only when the employer moves it, with no annual expectation imposed | **Assumption (Medium)** — A3-1 says nothing predetermined; A6 does not say | If he expects an automatic annual lift, employees who do not move a step are silently frozen and nothing detects it | **Q1, §22.13** | SPM |
| *"Local HR"* means "HR acting on individual cases", not "HR scoped to a country" | **Assumption (Medium)** | Reading (b) is a platform change to the access model and a separate epic | **Q2, §22.13** | SPM |
| A discretionary per-employee percentage is no longer wanted, because step moves and additional pay cover the cases | **Assumption (Medium-High)** — follows from A6 §4 | EP43 grows back by ~2 stories | **Q3, §22.13** | SPM |
| Managers can and will assess their own reports against written step expectations | **Assumption (Medium)** — the population and team sizes support it (Acme: 46 people, median team 3–4) | The backfill stalls and the whole equity feature stays gated behind a closed reconciliation | First tenant; R-20 | SPM / Delivery |
| The owner wants a gender pay-gap check at all | **Needs Validation** — **downgraded from "closed"**, see §22.1.3(a) | We change live vacation behaviour and ask a DPO to clear Art. 9 processing for a check nobody requested | **Q4, §22.13**, with DPO-1 | SPM |
| A single named supplementary component is sufficient; no general components model is needed | **Assumption (High)** — A6 §3 is explicitly one field for one situation | OQ-5 re-opens and KAN-193/218's record shape changes | Watch item: a second component request | SPM / Architect |

---

### 22.13 For the product owner — one page, with the numbers *(supersedes §21.7)*

*Four questions. Each one is a worked example with real numbers, per your instruction. **Every one has a
default we are already building, so nothing here is blocking you.** If you answer only one, answer Q1.*

**First — thank you for the correction. You were right and we had it wrong.** We had built a model where the
salary decided the step. Your model is the other way round and it is better:

> **The job decides the step. The step decides the base pay. Pay never decides the step.**
> Anything extra — the retention save, the market premium — is **additional pay**, recorded with a reason,
> sitting beside the base and never touching the ladder. **Tom stays a 2.1.**

**The ladder we are working from, in your numbers.** Level 2, Full Stack Software Engineering. Global HR sets
for 2027: **2.0→2.1 = 2%**, **2.1→2.2 = 2.4%**. Step 2.0 = **€50,000**, so 2.1 = **€51,000** and 2.2 =
**€52,224**.

---

#### Q1 — Anna stays at step 2.1 all through 2027 and 2028. She does her job well. Her responsibilities do not change. **What is her base pay in 2028?**

*This is the one question with a real cost attached, and it has never been put to you — the three earlier
attempts asked something else, badly.*

| | What it means | **Anna in 2028** |
|---|---|---|
| **A — the whole ladder moves every year** | Global HR raises step 2.0 from €50,000 to €51,000 each January, so every step above it lifts too | **€52,020.** Everyone gets the market movement whether or not they move a step |
| **B — the ladder never moves** | Only the transition rates are re-authored. Your pay changes when your step changes, and only then | **€51,000** — the same as 2027, and the same in 2029 |
| **C — the ladder moves when Global HR decides, and the system asks** | No automatic rise. Global HR sets the new entry value each year if they want one, and the product warns when 18 months have gone by without one | **Whatever Global HR set** — and if they set nothing, €51,000 with a warning on the screen |

**We recommend C, and we are building C.** B silently freezes everyone who does not move a step, and nothing in
the system would notice — that is the failure mode I would least like to explain later. A takes the decision
out of the employer's hands, which contradicts your own instruction that nothing about pay may be
predetermined. **C is A's tooling with B's discipline: the employer decides every year, and the product makes
sure they know when they have not.**

---

#### Q2 — Lars is an HR administrator in Oslo. Tom in Oslo is resigning, so Lars grants him €2,550 of additional pay. **Can Lars also grant additional pay to somebody in Hamburg?**

| | What it means | **Can Lars pay a Hamburg employee?** | Cost |
|---|---|---|---|
| **A — two permissions, one HR role** | We add one permission, "set the company's pay policy". Ingrid has it, so she authors the ladder's rates for the whole company. Lars does not, so he can grant Tom his premium but **cannot change the 2.1→2.2 rate** | **Yes** — Lars can act on any individual in the company | **Nothing.** Seed values and one new permission |
| **B — HR is scoped to part of the organisation** | HR people are attached to a country or region and can only act on people in it | **No** — Hamburg is not his | **4–6 stories and a change to the access model the whole product uses.** It would delay the pay record by a month or more |

**We recommend A and we are building A.** Your sentence — *"the local HR department decides to hike salary of
one employee"* — reads at least as easily as *"the HR people who handle individual cases"* as it does *"the HR
people in Norway"*, and A gives you the important half of the distinction for nothing: **local HR can no longer
rewrite the company's pay ladder.** If you need the Hamburg answer to be **no**, tell us — that is a separate
piece of work and we would rather know now than build A twice.

---

#### Q3 — Anna performs very well in 2028. Her job has not changed and she does not move a step. **Should her manager be able to give her 3% while giving someone else 1%?**

| | What it means | **Anna's 2028 rise** |
|---|---|---|
| **A — step moves and additional pay only** *(your A6 model, taken literally)* | Pay moves when the step moves, or when the ladder moves. Anything else is additional pay with a reason. If her manager wants to reward her specifically, they either **move her to 2.2** (because she is doing 2.2's job) or **grant additional pay** (because it is an exception, and it says so) | **Nothing extra** unless the ladder moves — and then everyone at 2.1 gets the same |
| **B — plus a discretionary percentage each year** | On top of the above, managers get a per-person percentage in the annual round, differentiated by performance within a budget | **3%**, at her manager's discretion |

**We recommend A and we are building A.** B re-opens the exact door you just closed: a per-person percentage
pulls base pay away from the step's value, and within two years nobody's base matches their step again. Under A
the two legitimate cases are both still served — *she is doing more* is a **step move**, and *we need to pay
her more anyway* is **additional pay with a reason on it**.

**What this changes for you: the annual cycle gets much smaller.** It becomes "open the round, review the
steps, approve once, move the ladder" instead of a budget-and-percentages exercise. **That epic drops from 7
stories to 5.**

---

#### Q4 — We have been building a **gender pay-gap check**. **Did you ask for that?**

*We do not think you did, and we should have noticed sooner. It came from us, reading the EU Pay Transparency
Directive, and it then travelled through five rounds of documents looking like your requirement.*

| | What it means | Cost |
|---|---|---|
| **A — yes, build it** | For each job level and market with at least five people, compare the median pay of men and women and report gaps over 5%. It needs gender recorded for every employee — which today changes which leave types 146 people are offered — and a data-protection sign-off, because gender is special-category data | ~1 wave of W4, plus a DPO clearance and a change to live behaviour in a shipped feature |
| **B — no** | We drop it. **Nothing else in the epic is affected** — we have deliberately kept it separable | **Zero.** We stop |
| **C — later** | Park it. Everything else ships; this comes back when you have a customer who needs it | Zero now |

**We recommend C and we have parked it accordingly** — it is off the critical path and nothing depends on it.
**Your original ask is already satisfied without it:** two people at the same step in the same market now earn
the same base by construction, so a "5% difference for the same position" cannot arise quietly at all.

---

#### Confirmations — no action needed unless one of these is wrong

- **Additional pay** carries a **mandatory reason** (retention, market premium, red-circled legacy pay,
  transitional, other), an **effective date**, and either an **end date or a review date** — so a premium
  nobody revisits does not quietly become permanent salary. It needs **two people to approve**, like any other
  pay change.
- **Full performance management is confirmed** — cycles, goals, calibration — in your words, *"go ahead with
  full implementation cycle as Product owner accepting the delay."* It is now a real epic of 22 stories and it
  runs **after** the compensation work and **before** the annual cycle, as you instructed.
- **The step display switch is closed** — a company may choose not to display an employee's step; the job
  title, the job family and every level's expectations stay visible always. Labelled *"do not display"*, not
  *"hide"*, because an employee can still work it out from the expectations.
- **Base salary only** stands (your *"at this point"*), now with additional pay as the one supplementary
  amount. No bonus, commission or equity.

#### Three things that are not questions

1. **Where this has got to, stated once.** You asked for salary, job levels and a pay flag. It is now a
   three-epic programme of about **50 stories and 8–9 months** — compensation (23) → performance management
   (22) → the annual cycle (5). You have chosen every step of that with the cost shown, which is your call to
   make. It is worth seeing the total in one place.
2. **The first real pay figure entered — even one, even by us, even "just to see how it looks" — triggers the
   security and login phase before anything else ships.** Much better known now than on the day you want to
   show a prospect their own numbers.
3. **Until real login exists, the pay visibility rules are correct in code and unenforceable in practice** —
   anyone can pick any identity from the demo tiles. Every compensation demo will say so at the start rather
   than let somebody find out.

---

### 22.14 Wave 7 tasking — the amendment round for A4–A6

*Each brief names what A4–A6 invalidate in **your** document and what to write instead. It is precise enough to
act on without re-deriving the amendments. Report in Charter §6 format.*

#### 22.14.0 The instruction that comes first, and it goes to all four of you

**⚠️ Challenge the premises before you apply them.** The reason this round exists is that *"pay position implies
step position"* entered the epic as a **team inference**, was never in the owner's request, and survived four
specialist reviews and two of my reconciliations because everybody — including me — was tasked to **apply** the
model rather than **test** it.

So, as a **required deliverable and not an optional extra**, each of you returns a short section headed
**"Premises I challenged"** covering:

1. **Every requirement in your document that is a TEAM inference rather than something the owner said or
   something the repository proves** — tag it, and say what would falsify it. §22.1.1 is my list; **find the
   ones I missed, especially in your own file.**
2. **At least one premise you went and checked at source** — his verbatim words, the code, the database — and
   what you found. *"I checked this and it holds, here is the evidence"* is a result and I want it written
   down. The BA found the model wrong in Wave 5 only because somebody went and looked at what
   `employees.gender` is actually used for.
3. **Anything in §22 you think is wrong.** Say so under the Conflict Log convention and build to the stated
   rule meanwhile. **Agreement between four people all tasked from the same brief is not evidence** — that
   sentence is in §22.15 because I wrote the opposite in §16.1 and it was the error that let this run.

#### 22.14.1 Business Analyst

**Invalidated in your file:** §4.4A in full · §4.5A's fitted-backfill rules · AC-200-\* (primary check) ·
AC-206-\* · AC-209-\* in full · AC-191-\* step criteria · §3.2's four codes · BR-10.\* · §21.4A · §28
(KAN-205). **Not invalidated:** §4.1, §4.2, §4.3, §4.7, §4.8, §4.9, §5, §6, §13, §14, §15, §26.

1. **Rewrite §4.4A as Check A″ — an equality, not a search.** `base` vs `step value(as_at) × FTE`; the
   deviation expressed as a magnitude in currency and percent **against their own step**; a **materiality
   threshold, default 1%, that governs notification only and never suppresses a computed number**. **No
   criterion anywhere may reference another step** — that is a testable prohibition and I want it written as
   one.
2. **Withdraw, do not amend:** every nearest-step criterion, the tie rule, the distance metric, the
   half-increment boundary, the tolerance constraint, and every criterion that fits a step from pay. These are
   deletions.
3. **New business rules** for: the **per-transition, per-year rate schedule** and its history (§22.5.1) ·
   compounding across transitions with his own 2%/2.4% worked example as a fixture (§22.5.2) · **base = step
   value × FTE** as an invariant · `STEP_NOT_ASSESSED` as a state distinct from step `.0`, with its own
   rendering rule.
4. **Rewrite AC-191-\* for step assessment** (§22.4.1–2): manager-authored against the step expectations,
   **nothing pre-selected, nothing suggested, nothing derived from pay**, HR override with a reason, completion
   meter, and the `STEP_NOT_ASSESSED` rules.
5. **Rewrite AC-209-\* entirely for the reconciliation** (§22.4.3): totals first, three mandatory dispositions
   with none pre-selected, the **batch approval by two people**, and the renamed
   **ladder-adopted-and-reconciled gate**. Include the case where an employee is unassessed — it must **not**
   block the gate, only their own evaluability.
6. **New criteria for KAN-218 (additional pay)** — all eight rulings in §22.3.1, each as a testable criterion.
   The ones most likely to be lost: **additional pay is excluded from the correspondence check and included in
   Check B**; **it never appears in an `audit_log` diff**; **it goes through the chain with four-eyes**.
7. **Amend §3.2 to five feature codes** — `pay_policy` registered in KAN-199, and **CFL-42-20's thresholds move
   from `company_settings:w` to `pay_policy:w`.** Note that CFL-42-20's *ruling* (not a role check) is
   preserved; only the home changes.
8. **Write §22.7's three categories as a business rule**, with the Category 2 list enumerated and the
   anti-erosion clause stated. This is the rule that protects KAN-203 from a future reader with a good
   argument, and it belongs in your business rules where an engineer will find it.
9. **Mark Check B ⬜ conditional throughout** — content unchanged, status changed. **Do not delete a single
   Check B criterion**; §22.1.3(a) is a scope question, and if he says yes we want them intact.
10. **Withdraw AC-205-\*** and record KAN-205 as Later. **Re-check §21.4A's contingency register** — several
    contingencies died with the tolerance and the nearest-step rule.

**Do not:** design schema · re-decide §22 · re-open Check B's arithmetic · write EP44 criteria yet (that is a
separate exercise once its epic outline is agreed).

#### 22.14.2 Senior Architect

**Invalidated:** ADR-024 substantially · ADR-023's Check A′ computation · §12.4.1 where the step model implies
derivation from pay · §5.2's four-code registration · §3.3's compensation set · §12.6.
**Not invalidated:** ADR-014, 015, 016, 017 (structure), 018, 019 (**extended**), 020, 021, 022, 025.

1. **Re-cut ADR-024.** `step_increment_pct` on `job_levels` is **withdrawn**; `job_step_increment_overrides` is
   **re-founded as the schedule itself** — a rate per transition, **effective-dated**, with history, on
   ADR-020's half-open convention. There is no longer a level rate to override, so the two-tier lookup
   collapses to one. **This should be cheaper than what it replaces — say whether it is.**
2. **`step_pay_point(level, market, step, as_at)` now resolves two effective-dated things** — the entry value
   *and* the rate schedule — at the same date. **Every caller passes a date; that is the change most likely to
   be missed by a caller, and it was already true before A6, so it needs a callable-level guard, not a comment.**
3. **Withdraw the tolerance `CHECK`** — for the third and final time. There is no cross-field constraint left
   in the model. The materiality threshold is a plain configurable value with **no constraint against it**
   (§22.5.3), and its semantics are notification-only: **the deviation is always computed and stored.**
4. **Re-cut ADR-023's primary computation as an equality.** `|base − step_value × fte|` against a threshold —
   no nearest-neighbour, no windowing, no tie rule. **Re-run the cost model; it should improve markedly.**
   Check B's group machinery is unchanged and stays behind a feature switch (conditional).
5. **The compensation record gains additional pay** (§22.3) — a separate, effective-dated, reason-coded amount
   beside base, **not** a general components table. Extend **ADR-019's per-action allowlist** to it explicitly:
   `has_additional`, `reason_code`, `direction`, `pct_change_band`, `effective_date`. **Never a figure.**
6. **Add the fifth feature code `pay_policy`** — four places, registered in KAN-199. Confirm
   `TestFeatureRegistryHasNoDrift` catches a miss on it. Confirm the `pay_policy:r` / `job_architecture:r`
   split resolves CFL-42-59 cleanly, and that no payload leaks an entry value or a rate to a holder of
   `job_architecture:r` alone.
7. **Rule on where the step assessment lives.** It is job content, so it belongs in the job-architecture
   service — but it must be **structurally incapable** of reading compensation. §2.2's one-way call rule
   applies, and I want it stated as a prohibition in ADR-025's style: **no function that assigns a step may
   take, read or import a monetary value.** That is the A6 prohibition made architectural rather than
   procedural, and it is the single most valuable thing you can add this round.
8. **KAN-209's reconciliation** — a batch that writes N compensation records and M additional-pay records in
   **one** transaction with **one** correlated audit set (the EP43 pattern, established here first). Say how
   partial application is made unreachable at 146 rows.
9. **EP44 — an architecture sketch only, no ADRs.** Where the review cycle sits; how the rating reaches EP43
   without becoming readable anywhere else; and **one paragraph on how KAN-232's no-ranking rule is held
   structurally** rather than by review discipline. ADR-025's forbidden-column table is unchanged and now more
   load-bearing.

**Do not:** re-open the product decisions in §22 · build a components table · build organisational scoping for
Global/local HR.

#### 22.14.3 UX / Product Designer

**Invalidated:** §7.9 (the fitted-step review) · §23 (KAN-206) for the rate schedule and the tolerance · §14's
finding copy wherever it names another step · §13 (KAN-205, descoped) · §3.1's surface map.
**Not invalidated:** §3 discretion by design · §15 the bell · §22 (KAN-207) · every accessibility annotation.

1. **The manager step-assessment screen — the most important new surface in this round, and treat it that
   way.** Forty managers, three or four reports each, assessing against written expectations. It decides
   whether the backfill finishes (R-2) **and** whether the placements mean anything (R-20). Constraints:
   **nothing pre-selected**, the step expectations readable **at the point of choice** without leaving the
   screen, and **no number on the screen that could be mistaken for a salary or a fit**. Design it **in one
   sitting with KAN-207's roadmap authoring** — it is the same person making the same judgement, and two
   separate visits will get one of them skipped.
2. **The reconciliation screen (KAN-209) — totals first.** The HR director's first question is *"what does
   adopting this ladder cost?"*, so the aggregate opens the screen and the per-person list is second. Three
   dispositions, none pre-selected, and a batch confirmation proportionate to the blast radius.
3. **Rewrite every finding string that names another step.** *"Paid closer to step 2.2"* is forbidden — the
   copy states the magnitude against **their own** step. This is standing rule 6 applied to a finding: naming
   another step is a claim about somebody's job.
4. **Additional pay (KAN-218)** — the grant flow with its reason code and review date, its place on "My Pay"
   (the subject sees their own premium; it is their money), the **additional-pay register**, and the per-level
   share report. And the copy that keeps base and additional **visibly separate and never silently summed** —
   a single "total pay" number would undo A6 on the screen.
5. **The rate-schedule surface (§22.5.1)** — a grid of transitions × years, authored annually by Global HR,
   with history readable. And **KAN-210's re-base screen changes meaning**: under A6 moving the ladder *is*
   granting the rise, so the preview must say so in those words and show how many people's base pay moves.
6. **The inline deviation warning at proposal time** (§22.7.4) in KAN-192, KAN-196 and KAN-218 — the flag he
   asked for, at the moment he asked for it. **"Red" must not be the only signal (WCAG 1.4.1), and consider
   whether red is even right** for a case HR is expected to override routinely and legitimately. Vocabulary is
   ruled ("flag", one object); the palette is yours.
7. **The `STEP_NOT_ASSESSED` empty state** — *"Step not yet assessed"*, never `2.0`, never a dash, never blank.
   Same discipline as "No salary recorded" versus "Not applicable — contractor".
8. **§25 — rewrite for the third time, do not delete.** Performance management now exists next door as a real
   epic. The line is no longer *"the ladder is not performance management"* as a defence against drift; it is
   **which surface owns what**, and the ladder must still not become a scoring instrument. Expect *"can we tick
   off roadmap items?"* to be asked far more often once EP44 is visible, and pre-refuse it there too.
9. **Surface map: five codes.** What "no access" looks like for `pay_policy`, and — per CFL-42-59 — what an
   employee sees on `/ladder` when they hold `job_architecture:r` but not `pay_policy:r`: **structure and
   expectations, no money.**

#### 22.14.4 UAT Lead

**Invalidated:** F13–F19 in their nearest-step and tolerance parts · F-12/F-13/F-13b (the questions no longer
exist) · the KAN-200 Check A′ set · the KAN-209 set in full · KAN-205's cases · KAN-208's cases **paused, not
deleted**. **Not invalidated:** the attack catalogue · F1–F12 · Check B's fixtures (**preserved and paused**) ·
the negative-visibility approach · the regression plan · the Demo Gate pack.

1. **New arithmetic fixtures, hand-computed as before, and use his numbers**: entry €50,000, 2.0→2.1 at **2%**,
   2.1→2.2 at **2.4%** → 2.1 = **€51,000**, 2.2 = **€52,224**. **Put the linear values (€52,200) alongside so a
   linear implementation fails loudly.** Add a three-transition case with three different rates, and a case
   where the schedule changes between years so an as-at lookup that ignores its date fails.
2. **The prohibition as a test, and this is your highest-value contribution this round.** Assert that **no
   API payload, DOM node, export, notification body or audit row ever references a step other than the
   employee's own** in a correspondence context, and that **no step-assignment path accepts or reads a monetary
   input**. A6 is a prohibition; a prohibition needs a negative test or it is a comment.
3. **Tom's case, end to end, as the epic's headline fixture** (A6 §6): step 2.1, base €51,000, additional
   €2,550, total cash €53,550 → **the correspondence check raises nothing**, his step does not move, and the
   €2,550 appears attributed with its reason. **If that test fails, the amendment has not landed.**
4. **The reconciliation (KAN-209)**: all three dispositions; the batch approval binding **two different
   people**; an unassessed employee that does **not** block the gate; and — the one that matters —
   **the day-one finding count is zero after a completed reconciliation.**
5. **Additional pay**: excluded from the correspondence check, included in Check B, absent from every payload
   without `compensation:r`, absent from every `audit_log` diff, present in "My Pay" for the subject only,
   present in the watermarked export. Extend the attack catalogue to it and to `pay_policy`.
6. **CFL-42-59** — assert that a holder of `job_architecture:r` without `pay_policy:r` cannot retrieve an entry
   value or a rate in any payload, and that with step display off the employee's own payloads carry neither a
   step nor a pay point.
7. **Withdraw and say which**: for every F13–F19 fixture, state withdrawn / re-scoped / retained. **Check B's
   statistical fixtures must not be lost in the clear-out** — that is the specific risk in this amendment, and
   it is the second time I have had to say it.
8. **Two additions to the Demo Gate's must-be-walked-by-a-human list** (§7.3): *"a manager can explain why this
   person is at this step"* (R-20) and *"the ladder reads as a real description of the work"* (R-18, already
   there — it is now load-bearing rather than aspirational, because an undescribed ladder cannot be assessed
   against).

---

### 22.15 Process finding — how an unexamined team premise survived five rounds

*Charter §9 (evidence before opinion; never invent product facts). **A finding, not a blame exercise** — I
wrote the premise, I reinforced it in Wave 5, and I wrote the tasking that told four specialists to apply it.*

#### 22.15.1 What happened

"Pay position implies step position" entered the epic in **§14.1**, as my reconciliation of two of the owner's
messages. **I labelled it correctly at the time** — *"this is an inference, and it should be confirmed rather
than assumed forever"* — and logged the validating question as **OQ-A1-1** with the default *"build it as
reconciled"*.

Then four things happened, in this order:

1. **The inference acquired a decision number.** Once it was §14.2 it read like a ruling, and every document
   downstream cited it as one. **A label travels; a caveat does not.**
2. **The validating question was never chased.** OQ-A1-1 went onto a one-page list of eleven items, each with
   a default so that *"nothing blocks"*. Nothing blocked — and nothing was answered either. **The mechanism
   that stops work stalling also removes the pressure that gets questions answered.**
3. **Every tasking brief said "apply", not "test".** My Wave 4 and Wave 6 briefs are lists of *invalidated
   sections* and *what to change*. A specialist reading that is being asked to conform. The one time somebody
   went and looked at source instead — the BA checking what `employees.gender` is actually used for — they
   found a live behavioural defect and logged their own earlier assumption as **KNOWN TO BE FALSE**.
   §16.4 even says so: *"the register caught it because somebody went and looked, not because anybody reasoned
   about it."* We noticed the lesson and did not generalise it.
4. **I read agreement as confirmation, and wrote it down.** §16.1: *"Nobody attacked A1's shape... which is the
   strongest evidence available that the model is right."* **That sentence is the defect in one line, and it is
   mine.** Four specialists, tasked from one brief, told the model was authoritative, agreeing about it is not
   four pieces of evidence. It is one assumption wearing four coats. Contrast §12.1, where three roles found
   the same hole in my four-eyes rule *from three different starting points* — **that** was independent
   convergence, and the difference between the two cases is exactly the thing I failed to notice.

**Net cost:** five rounds, four specialist documents, two reconciliations and a build order all constructed on
a premise the owner had never stated, discovered only when he read a worked example and said *"No you have not
got correct!!"*. **He was the test. That is the wrong person to be the test.**

#### 22.15.2 The change — three rules, effective immediately, for every epic

**1. The Load-Bearing Premise Register.** Every epic carries one, owned by the SPM, **maximum ten rows** —
if it is longer than ten it is not a register of what the design cannot survive being wrong about. Each row:
the premise · **its origin, tagged OWNER / EVIDENCE / TEAM** (§22.1.1) · for TEAM rows, **the single question
that would falsify it** and who is chasing the answer.

> **The hard rule: a TEAM premise may not be load-bearing across more than one wave without a validating
> answer.** If a wave closes and it is still unvalidated, it goes to the **top** of the owner's page, above
> everything else, and the next tasking brief says so. Defaults keep work moving; they must not be allowed to
> keep questions comfortable.

**2. Origin tagging on requirements.** Every requirement in every deliverable carries its origin — the owner's
verbatim words, a `file:line`, or *TEAM inference*. It is a column, it costs nothing, and under it **"pay
position implies step position" would have carried `TEAM inference — SPM §14.1` in all five documents.** The
fifth reader would have seen it. Four of them read past it because it looked like his.

**3. "Premises I challenged" is a required section in every specialist report**, and it is in §22.14.0 for this
round. It must name the TEAM premises in that specialist's own file, and it must contain at least one premise
checked **at source** — his words, the code, the database — with the result stated either way. *"I checked and
it holds"* is a deliverable.

**And one line for my own review checklist** (role file, "Reviewing a specialist report"):

> **Agreement between specialists tasked from the same brief is not evidence.** Only a specialist who went to
> the source produces evidence. When four reports converge, ask what they converged *from* before treating it
> as confirmation.

#### 22.15.3 What I am not changing, and why

I am **not** adding a review stage, a sign-off or a gate. The problem was not too little process; it was that
the process had no step at which somebody was **asked to disagree**. Three cheap rules that change what a brief
asks for beat a fifth wave that asks the same question again more formally.

And I am **not** treating the defaults mechanism as the culprit. Building against a stated default is right —
it is why EP42 has 23 specified stories rather than eleven open questions. **The failure was that a default
was allowed to age into a fact.** Rule 1 is aimed precisely at that and nothing else.

*A4, A5 and A6 applied. Backlog and roadmap updated in the same pass. EP42 at 23 stories, EP44 entered at 22,
EP43 reduced to 5; four questions with the owner, all with defaults being built against, none of them blocking.*
