# EP42 — Compensation, Job Architecture & Pay Equity — UAT Test Plan & Test Cases

> **Owner:** UAT Lead (`../05_UAT_LEAD.md`) · **Date:** 2026-08-09 · **Status:** Wave 2 deliverable, issued to the SPM.
> **Primary input:** `EP42_SPM_SCOPE_AND_DECISIONS.md` (Wave 1, authoritative). Where the shared team brief and the
> SPM document disagree, the SPM wins — in particular **CFL-42-6**: three companies, **Acme Corp 46 employees**,
> **Telia 100**, **"Sam Cpmapny" 0 employees / 3 locations**, plus one company-less SYSTEM_ADMIN record. Every case
> below is written against S1, not against the brief's "147 Acme employees".
>
> **What this document is.** A test plan and **300 executable test cases** for KAN-188 … KAN-202, at the level where
> a tester runs them without interpretation; the confidentiality attack catalogue; hand-computed arithmetic fixtures
> the engine's author did not write; the automation split; the impact on the two regression suites I own; and the
> Demo Readiness Gate pack for any compensation demo.
>
> **What this document is not.** It is not acceptance criteria (BA, Wave 2 — where a case cites `AC-<story>-<nn>` it
> is a placeholder until the BA's file lands, and the case is written against the SPM decision it derives from). It
> is not schema (Architect). It is not a UAT *report* — nothing has been built, so nothing has been executed, and
> **no sign-off is given or implied here** (§11).
>
> **Constraint honoured.** This wave is documentation only. **No test file was written or modified, no application
> code was touched, the app was not started and neither regression suite was run.** Every code reference below is
> from reading the repository. The suite extensions in §7 and §8 are specified here and built when the stories are
> built, by me, in the same commit as the story (Charter §5b).

---

## 0. Executive summary — the verdict, then the reasoning

**Five things the team should take from this plan.**

1. **The highest-value thing I can build for this epic is a negative-visibility suite, and it must assert absence
   from the *payload*.** EP42's failure mode is not "the feature does not work" — it is "the feature works and a
   number reached somebody who should never have seen it". A salary hidden by a Jinja `{% if %}` around a `<td>`
   while the JSON behind it still carries `annual_base` passes every screenshot review ever taken. §4 is an attack
   catalogue of **21 named attacks** against the surface list in SPM §4.5.7, and §6.7 turns them into 32 cases.
2. **The equity engine's arithmetic must be tested as arithmetic, with expected values computed by hand, in
   decimal, by somebody who is not the engine's author.** §5 gives **12 fixture groups (F1–F12) with every expected
   number written out**, including the exact-threshold trio (5.00% / 4.99% / 5.01%), compa-ratio 0.95 exactly,
   the group of 1, 2, 3 and 4, coverage at 78% / 80% / 82% **and the 79.59%-that-displays-as-80%** case, the
   all-equal group, the single-gender group, and **two cases that a float implementation fails and a decimal
   implementation passes** (F7, F11). R-12 in the SPM's register is the risk; §5 is the answer to it.
3. **Four ambiguities in the Wave 1 decisions are untestable as written**, and I cannot write a pass/fail case for
   them until they are resolved: the **rounding mode and money type** (nothing says `NUMERIC(14,2)` or names a
   rounding rule, and §5.F7 shows the answer changes the result); whether the coverage gate and the re-fire delta
   are **inclusive or exclusive** at the boundary; whether a **negative gender gap** (women paid more) is a
   finding; and whether **`_MONEYISH_KEYS` — which matches keys — is expected to stop an amount typed into the
   mandatory free-text `reason`, which it cannot.** All four are in §10 with a recommended default so cases can be
   drafted now and confirmed later.
4. **Segregation of duties has a hole D4h does not close.** KAN-198 forbids one user deciding two *levels*. It says
   nothing about the **initiator also being an approver**. In the seeded Acme configuration, `ingrid.makinen` holds
   PORTAL_ADMIN **and** HR_ADMIN, may initiate for anyone, and satisfies level 1 by role — so she can raise a pay
   rise and approve it, one person, with KAN-198 fully implemented and passing. That is the same control failure
   D4h exists to prevent, wearing a different hat. Raised as **UAT-F-04, High**, with cases written both ways.
5. **Three things in this epic cannot be proven by a green assertion and must be walked by a human in a visible
   browser** (§7.3): whether an HR user can tell **"No salary recorded" from "Not applicable — contractor"** at a
   glance (D7.1/D7.7 — two empty states that must never look like a value or like each other); whether the
   **promotion-eligible signal reads as a signal and not a promise** (D3.4); and whether the compensation block
   **fails to make the common no-change move heavier** (D4f). Each of those is a "technically passes, real HR user
   is misled" risk, which is exactly what I am here for.

**Position on sign-off, stated now so it is not a surprise later.** EP42 will not receive UAT sign-off while any
Critical or P0 defect is open, and three are pre-declared as **entry** conditions rather than findings: KAN-194
must land in the same release as KAN-193 (a pay record with no enforced visibility model is a Critical defect the
moment it exists); the `_MONEYISH_KEYS` guard must exist before the first compensation `audit_log` write; and the
tenant switch (KAN-188) must be central before the first route that renders an amount. Those are the SPM's own
sequencing decisions — I am recording that I will hold them as gates, not preferences.

---

## 1. Scope, environment and what I could not verify

### 1.1 Inputs read

| Input | Used for |
|---|---|
| `EP42_SPM_SCOPE_AND_DECISIONS.md` (Wave 1) | Authoritative source for every decision D1–D8, stories KAN-188…202, OQ-1…9, CFL-42-1…7 |
| The shared team brief (session scratchpad) | R1–R7 traceability only; its tenancy baseline is superseded by CFL-42-6 |
| `../05_UAT_LEAD.md`, `../01_TEAM_CHARTER.md` | Case template, severity/priority scales, report format, exit criteria |
| `../../docs/project-management/DEMO_READINESS_GATE.md` | D2/D3/D7 are mine; the D4 blind-spot list drives §6.14 |
| `../../docs/project-management/BACKLOG.md` lines 635–639 | DEF-001/2/3/4 verbatim records — the failure this plan exists to prevent recurring |
| `tests/ui/test_browser.py` (93 checks), `tests/ui/test_vacation_workflow.py` (39 checks) | House style, and §8's impact analysis, by line number |
| `tests/test_org_change.py`, `test_regression.py`, `test_audit_service.py`, `test_company_scoping.py`, `conftest.py` | pytest conventions, fixture names, the classes EP42 will break |
| `app/auth.py:38-95`, `app/services/org_change_service.py`, `app/services/audit_service.py`, `app/services/notification_service.py`, `templates/base.html:290-320, 608-660` | The mechanisms every case asserts against |
| Route inventory (`app/routes/*.py`) | The endpoint list the attack catalogue in §4 fires at |

### 1.2 What I did not do, and why

- **I did not run `pytest` or either regression suite.** This wave is documentation only and the instruction was
  explicit. The current recorded baseline is **browser 93/93, vacation 39/39** (`../../CLAUDE.md` §REGRESSION FLOW
  TEST). I am not restating that as a result I observed — it is the number in the repository, produced by
  `python tests/ui/test_browser.py` and `python tests/ui/test_vacation_workflow.py`. Per Charter §5b rule 3, cite
  the command, not the number.
- **I did not verify the seeded Acme approval chain against the live database.** SPM §4.4.8 records it as observed
  on 9 Aug (level 1 = `HR_ADMIN` role, level 2 = a named approver who also holds `HR_ADMIN`). I treat that as
  **Known on the SPM's evidence** and case UAT-42-198-01 re-verifies it as its own precondition.
- **Nothing has been built**, so every case below has status **Not Executed** and no actual results. A test plan
  with an "Actual result" column filled in before the code exists is a fiction.

### 1.3 Environment and tenancy

| | |
|---|---|
| **Entry criteria** | A UAT database separate from the dev database, built the way CI builds one (`schema.sql` + `seed_rbac.sql` + migrations), with the UAT fixture cohort in §1.4 loaded. Build deployed, smoke green, no open Critical. |
| **Tenants** | **Acme Corp** (46 employees; Hamburg DE, Porto PT, Tallinn EE) · **Telia** (100; Stockholm SE, Oslo NO, Copenhagen DK, Helsinki FI, Tallinn EE) · **"Sam Cpmapny"** (0 employees, 3 locations UK/US/IN) · one company-less SYSTEM_ADMIN record. |
| **Named users** | `oliver.hartmann@company.com` SYSTEM_ADMIN · `ingrid.makinen@company.com` Acme PORTAL_ADMIN + HR_ADMIN + solid-line manager · `liisa.virtanen@company.com` Acme solid-line manager of Sven · `sven.becker@company.com` Acme employee, Liisa's report · `tonis.rebane@company.com` Acme plain EMPLOYEE · `maria.andersson@telia.com` Telia admin. |
| **Concurrency (D6a)** | The dev database is shared and other actors write to it. Every case that counts rows, badges or flags is written to be **scoped to its own fixture subject**, never to "any". This is not fussiness — `tests/ui/test_browser.py:806-810` already carries a comment explaining that an unscoped bell assertion passes or fails on somebody else's data. |
| **No real PII, ever** | Charter guardrail, and SPM D8 trigger **T5**: one real compensation value in any tenant fires the S5 security phase. Every amount in this plan is synthetic and belongs to a fixture employee. |

### 1.4 The fixture cohort UAT must own — the seeded data cannot test this epic

**Known (SPM S4):** the seeded population is **146 PERMANENT, 1 CONTRACTOR, 0 PART_TIME**, and there is no FTE and
no currency anywhere in the schema. It will therefore **never** exercise FTE normalisation, part-time comparison,
intern exclusion, or a group of mixed employment types. A suite written against seed data alone would report green
across the two paths most likely to be wrong.

I own a fixture builder, `tests/fixtures/ep42_uat_seed.py` (new, mine), idempotent and re-runnable, creating in
**Acme** a `UAT Engineering` job family with levels L1–L4 and 5 steps each, one pay market per country, and this
cohort. Every employee below is prefixed `uat.` so it can never be confused with, or collide with, demo data.

| Fixture id | Employee | Type | FTE | Pay basis | Recorded amount | Purpose |
|---|---|---|---|---|---|---|
| U-01…U-05 | `uat.eng1…5@acme.test` | PERMANENT | 1.0 | annual | per §5 F1 | The ordinary group |
| U-06 | `uat.part@acme.test` | PART_TIME | 0.6 | annual | 42,000.00 | FTE normalisation (F7) |
| U-07 | `uat.contract@acme.test` | CONTRACTOR | 1.0 | hourly | 95.00 | Must be excluded and **counted** |
| U-08 | `uat.intern@acme.test` | INTERN | 1.0 | monthly | 1,200.00 | Must be excluded and counted |
| U-09 | `uat.nopay@acme.test` | PERMANENT | 1.0 | — | **no record** | "No salary recorded" empty state; coverage denominator |
| U-10 | `uat.monthly@acme.test` | PERMANENT | 1.0 | monthly | 5,833.33 | Annualisation (F8) |
| U-11 | `uat.hourly@acme.test` | PERMANENT | 1.0 | hourly | 33.6538 | Annualisation (F8) |
| U-12, U-13 | `uat.hr2@acme.test`, `uat.hr3@acme.test` | PERMANENT | 1.0 | annual | 80,000.00 | Second and third HR_ADMIN — four-eyes (§6.11) and multi-recipient retirement (§6.14) |
| U-14 | `uat.dotted@acme.test` | PERMANENT | 1.0 | annual | 70,000.00 | DOTTED_LINE_MANAGER over U-01 |
| U-15 | `uat.exmgr@acme.test` | PERMANENT | 1.0 | annual | 90,000.00 | Manager to be offboarded mid-test |
| U-16…U-20 | `uat.tal1…5@acme.test` | PERMANENT | 1.0 | annual | per §5 F6 | Tallinn (EE) pay market — must never be compared with Hamburg |
| U-21…U-26 | `uat.g1…6@acme.test` | PERMANENT | 1.0 | annual | per §5 F3/F4 | Gender-gap groups, both genders, and the single-gender group |
| U-27 | `uat.xss@acme.test` | PERMANENT | 1.0 | annual | 70,000.00 | `last_name` = `<img src=x onerror=alert('XSS')>` (payload X1, §3.6) |
| T-01…T-05 | `uat.tel1…5@telia.com` | PERMANENT | 1.0 | annual | 700,000.00 SEK | Telia comparison group — the cross-tenant target |

**Sam Cpmapny gets no employees.** It is the empty-tenant case and its value is precisely that it has none.

---

## 2. How to read a test case

### 2.1 Case ID

`UAT-42-<story>-<nn>` — e.g. `UAT-42-200-14`. **Stable for the life of the epic.** A case that is deleted leaves a
hole; the number is never reused. Cross-cutting attacks carry `UAT-42-A<nn>` (§4) and fixtures `F<n>` (§5).

### 2.2 Columns

`ID` · `Type` · `Preconditions` · `Steps (as whom)` · `Expected result` · `Sev` (severity **if this case fails**,
Charter §2) · `Auto` (where it runs).

**`Auto` legend** — **P** new or extended `pytest` under `tests/` · **R** real-DB integration tier (needs DEP-4 /
KAN-168) · **B** `tests/ui/test_browser.py` (mine) · **V** `tests/ui/test_vacation_workflow.py` (mine) ·
**C** new `tests/ui/test_compensation_workflow.py` (mine) · **H** **human-only in a visible browser — a green
assertion would not prove it** (justified individually in §7.3).

### 2.3 Type — and the rule that a type is never skipped

Every story carries all five. Where a story genuinely has no case of a type, it says so and why; it does not
silently omit the row.

`Happy` · `Edge` (boundary, empty, maximum, zero, the day itself) · `Adv` (adversarial — an internal user who is
trying, not confused: direct API, UUID substitution, injected payloads, malformed files, parameter tampering) ·
`Perm` (permission per role, including the grant that should widen and the grant that should not) ·
`Tenant` (company A's data unreachable from company B) · `Audit` (the trail where one is required) ·
`Notif` (the D4 blind-spot list) · `Math` (arithmetic with a hand-computed expected value).

### 2.4 Severity and priority

Charter §2 exactly: **Critical** core process cannot complete / release-blocking · **High** major functionality
broken or significant impact · **Medium** important with a reasonable workaround · **Low** minor or cosmetic.
Priorities on findings use **P0** blocker … **P4** future. **Every case whose failure means an unauthorised person
can obtain a pay figure is Critical, without exception** — there is no "minor leak".

---

## 3. Cross-cutting test rules — these bind every case below

**CC-T1 · Absence, not invisibility.** For any surface a viewer may reach without `compensation:r` in scope, the
test asserts the amount is **absent from the server's response body** — the JSON key is not present, or the HTML
does not contain the digit string — **not** that it is hidden. A test that asserts `not is_visible()` on a
CSS-hidden element is a test that certifies a leak. Where a case says "absent", it means: `assert 'annual_base'
not in json_keys` **and** `assert '70,000' not in response.text` **and** `assert '70000' not in response.text`.

**CC-T2 · Assert the row, not the response.** Every case that applies, voids or corrects money asserts the final
state of the **database row** (amount, currency, FTE, effective_from, is_current), not the API's 200. D-185-1 was a
data-loss defect that **all 4,628 tests passed through** because they asserted the response (SPM S15).

**CC-T3 · Decimal, not float.** Expected values in §5 are exact decimals. Assertions compare `Decimal` to `Decimal`
(or the exact string), never `pytest.approx`. `approx` on money is how a float implementation ships. Two fixtures
(F7, F11) are designed so a float implementation produces a different value and fails.

**CC-T4 · Every notification runs the D4 ten.** No EP42 notification is considered tested until all ten items of
the blind-spot list (`DEMO_READINESS_GATE.md` §D4) have an assertion: actionable area · badge count · icon/colour
semantics · retirement **for every eligible recipient** · empty state · the other approvers · the subject · the
requester · status vocabulary · deep links. §6.14 does this for the pay-equity flag and §6.5 for the
promotion-eligible signal. **Asserting that the bell opens proves nothing** — that sentence is DEF-002's epitaph.

**CC-T5 · Tenant substitution is fired at every endpoint, not sampled.** Every EP42 endpoint that takes an id gets
one case that substitutes a **Telia** UUID into an **Acme** session and one that substitutes an Acme UUID into a
Telia session. Sampling misses the one route that forgot the `company_id = %s::uuid` clause, and that route is the
whole breach.

**CC-T6 · The two named payload sets.** Reused by ID so cases stay short.

*XSS payload set* — applied to **every** free-text field EP42 adds (job family name, level title, step label, pay
market name, justification category, disposition reason, compensation reason, escalation-list label, CSV cell,
import file name), and to an **employee name** that flows into EP42 surfaces (fixture U-27):
- **X1** `<img src=x onerror=alert('XSS')>`
- **X2** `"><script>alert(1)</script>`
- **X3** `<svg/onload=alert(1)>`
- **X4** `javascript:alert(1)` (as a URL-ish value)
- **X5** `{{7*7}}` and `${7*7}` (template injection)
- **X6** 1,000 × `A` (length/overflow)
- **X7** `Müller-Łódź 日本語 🙂` (unicode, must round-trip unharmed — a sanitiser that eats this is also a defect)

*Assertion for all X payloads:* the stored value round-trips byte-identical; every rendering surface shows it as
**literal text** (`element.textContent == payload`), `page.on('dialog')` fires zero times, and no new DOM builder
inserts it without `escH()`. Surfaces to check per payload: the ladder configurator, the directory row, the org-tree
card, the equity queue, the **bell notification body**, the move-modal summary (`ocSummary()`,
`templates/base.html:630-637`), the CSV export, and the audit-trail reason display.

*Malformed CSV set* — applied to KAN-191's mapping CSV and KAN-195's compensation CSV:
- **M1** missing required header · **M2** headers in a different order · **M3** extra unknown column
- **M4** duplicate `employee_number` in one file · **M5** `employee_number` belonging to **another tenant**
- **M6** `employee_number` that does not exist · **M7** blank amount · **M8** `0` · **M9** `-1000`
- **M10** `70,000.00` (thousands separator) · **M11** `€70000` (currency symbol) · **M12** `7e4` (scientific)
- **M13** `70000.123456789` (over-precision) · **M14** FTE `1,0` (European decimal comma) · **M15** FTE `0`
- **M16** latin-1 bytes (invalid UTF-8) · **M17** UTF-8 BOM · **M18** CRLF line endings
- **M19** quoted field containing a newline and a comma · **M20** a 1 MB single cell · **M21** 100,000 rows
- **M22** formula injection: cell values `=HYPERLINK("http://evil","x")`, `+1+1`, `-1+1`, `@SUM(A1)`, `\t=cmd`
- **M23** the literal string `NULL` · **M24** `effective_from` = `2026-13-01` · **M25** `effective_from` = `01/02/2026` (ambiguous)
- **M26** a file that is not CSV at all (a PNG renamed `.csv`) · **M27** an empty file · **M28** header row only

*Assertion for all M payloads:* **row-level rejection, reported to the user with the row number and the reason,
nothing committed for the rejected row, and — for M22 — the value neutralised on any export the product produces**
(a leading `'` or the cell refused). Never a 500, never a stack trace, never a partial commit.

**CC-T7 · Re-runnable and uncontended.** Every UAT case must be runnable twice in a row with the same result. The
compensation suite gets the same treatment `tests/ui/test_vacation_workflow.py:104-137` gives leave: a narrowly
scoped, marker-based reset of **only** the rows this suite created, for **only** its own fixture employees. The
comment in that function is the standard: *"That is a defect in the suite, not in the product, and the fix is to
make the run idempotent rather than to relax the limit check."* Compensation history is **append-only** (KAN-193),
so the reset deletes fixture rows by correlation id, and **never** by relaxing an append-only constraint.

---

## 4. The confidentiality attack catalogue — A01…A21

**This is the section I would keep if I could keep only one.** Each attack is an *internal* user who is trying, not
a confused one, and each maps to cases in §6.7 and elsewhere. The surface list is SPM §4.5.7; the endpoints are
real, taken from `app/routes/*.py`.

| # | Attack | The move | What must happen | Sev if it works |
|---|---|---|---|---|
| **A01** | **Direct record fetch** | Plain EMPLOYEE (`tonis.rebane`) GETs the compensation endpoint for another Acme employee's UUID, obtained from the directory's `href="/profile/<id>"` | `403`, response body carries **no** compensation key at all | Critical |
| **A02** | **Manager reaching past their line** | `liisa.virtanen` (has `compensation:r`, scope = direct reports) GETs the record of an Acme employee who is **not** her report | `403` or `200` with an empty set — never the amount. Row scope is enforced **server-side**, not by the caller passing a scope | Critical |
| **A03** | **Skip-level reach** | A manager GETs the record of their report's report (in their subtree, not their direct line) | Refused — D5.2 grants **one level down, not the subtree** | Critical |
| **A04** | **Dotted-line reach** | `uat.dotted` (DOTTED_LINE_MANAGER over U-01), granted `compensation:r` by the tenant, GETs U-01's record | `200` with **zero rows**. The grant gives the feature; the role's defined scope is empty, so it yields nothing (D5.3). *And this is confusing — see finding UAT-F-07* | Critical |
| **A05** | **Offboarded manager** | `uat.exmgr` is offboarded (KAN-184 revokes access) while holding a session; replays the compensation request with the existing cookie | Session invalid → login redirect. If the session survives, the **row scope is re-resolved per request** and returns nothing — a cached `direct_report_ids()` is the defect | Critical |
| **A06** | **Reassigned reports** | A manager's reports are re-pointed to somebody else; the old manager replays the request for a former report | Nothing. Scope follows `manager_relationships` **as at now**, not as at login | Critical |
| **A07** | **Cross-tenant UUID substitution** | Acme HR_ADMIN (`ingrid.makinen`) substitutes a **Telia** employee UUID into every EP42 endpoint (record, timeline, history, band, flag, disposition, level assignment, import row, equity group) | Refused, nothing read, nothing written. **Recommended `404`, not `403`** — a `403` confirms the row exists and is an existence oracle across a tenant boundary. See finding UAT-F-05 (this contradicts EP38's `AC-184-45` `403` convention, deliberately) | Critical |
| **A08** | **SYSTEM_ADMIN cross-tenant aggregate** | `oliver.hartmann` with "All Companies" selected opens every dashboard, analytics and equity surface | **No cross-tenant pay figure or pay aggregate anywhere** — SPM §3.3 excludes cross-tenant pay comparison "of any kind, for any role, including SYSTEM_ADMIN aggregates". A count of employees is fine; a mean of two tenants' salaries is a defect | Critical |
| **A09** | **Search index leak** | Any user searches `/api/search?q=70000` and `q=70,000` and `q=€70000`; also the exact amount of U-01 | Zero employee hits. `trg_employee_search` must never index an amount (SPM S12). A hit is a leak that bypasses every route guard | Critical |
| **A10** | **Sort-order oracle** | A user without `compensation:r` requests `/api/employees?sort=annual_base` / `?order_by=salary` / `?sort=-compa_ratio` | The parameter is rejected or ignored; the returned order is **unchanged** from the default. Ordering is disclosure even with the column absent | High |
| **A11** | **Export leak** | `/api/analytics/export/csv` and every EP42 export (missing list, coverage, mapping round-trip, equity queue) downloaded as each role | No amount column for anyone lacking `compensation:r`; and the **missing list** never contains an amount by construction | Critical |
| **A12** | **Org-tree / directory payload** | `/api/org-tree`, `/api/org-tree/context`, `/api/employees`, `/api/my-team`, `/profile/<id>` inspected as **PORTAL_ADMIN** (who legitimately has `compensation:r`) | Compensation keys are **absent from these payloads for everyone, including PORTAL_ADMIN**. They are not compensation surfaces; a "harmless because they're allowed" leak is how the field reaches the one surface that is not gated | High |
| **A13** | **Notification-body leak** | Raise a flag with a 12.5% gap; read `/api/my-notifications` as each recipient; read the bell DOM; read any email template | No amount, **no percentage that can be inverted to one**, no band, no compa-ratio. Names the subject, the group, and that a threshold was exceeded (D2) | Critical |
| **A14** | **Audit-diff leak** | Hold `audit_log:r` and **not** `compensation:r`; read every audit row EP42 writes | Never an amount. `_MONEYISH_KEYS` refuses the write; the read shows `direction` and `pct_change_band` only (D5.6) | Critical |
| **A15** | **Audit *reason* leak** | An HR admin types `"raise to 82000 from 70000"` into the mandatory reason on a compensation change | **Today this is written verbatim to `audit_log.reason` and `_MONEYISH_KEYS` does not stop it — it matches keys, not values.** See finding UAT-F-03 | High |
| **A16** | **Small-group aggregate inversion** | View a "group average" / "group median" for a group of **2** where the viewer is one of the two, or knows one member's pay | Suppressed. An average over 2 with one known member is the other member's pay, exactly. Recommended rule: **no aggregate rendered for a group below the same minimum as Check B (n<5)** — currently unspecified, finding UAT-F-06 | Critical |
| **A17** | **Position-in-range inversion** | An employee's "My Pay" shows position in range; if that range is derived from the **group median** (no band) in a group of 2–3, the employee inverts it to a colleague's pay | Position in range is shown **only** where a real band exists, never derived from the live group median (D5.5 says "once bands exist" — make it a hard rule) | High |
| **A18** | **Count/coverage inversion** | The coverage meter says "1 of 2 recorded" for a group; combined with the group median, the single recorded amount is disclosed | Coverage counts are shown at company level and per group only where the group meets the minimum; a group of 2 shows "insufficient comparison group" and no numbers | High |
| **A19** | **Parameter-scoped self view** | POST/GET "My Pay" with `?employee_id=<somebody else>` and with a JSON body override | Ignored entirely. Scope comes from `session.employee_id` **server-side** and from nowhere else (D5.5) | Critical |
| **A20** | **Read-only holder mutating** | A holder of `compensation:r` **without** `w` calls every mutating endpoint (record, import commit, band edit, threshold change, disposition, level assign) | `403` on every one, and **zero state change** verified by re-reading the row (D5.4) | High |
| **A21** | **Tenant-switch bypass** | EP42 disabled for Telia; a Telia PORTAL_ADMIN hits every EP42 route by direct URL and every EP42 API by `fetch`, with a valid session | The **off-state screen** on HTML routes, a refusal with no payload on APIs. "Hidden from the nav" is not disabled — that is exactly the R7 failure KAN-188 exists to prevent | Critical |

---

## 5. Money arithmetic — hand-computed fixtures (F1–F12)

**Written by UAT, not by the engine's author** (SPM §8.4.4, risk R-12). Every expected value below was computed by
hand in decimal and is reproduced in full so a tester can check the engine against the paper, not the paper against
the engine. All fixtures live in Acme, family `UAT Engineering`, unless stated.

**Conventions these fixtures assume — and which are currently unspecified (finding UAT-F-01):** amounts are
`NUMERIC(14,2)`; all intermediate arithmetic is decimal, never binary float; monetary results round
**HALF_UP to 2 decimal places**; ratios are carried **unrounded** into every comparison and rounded only for
display (4 dp for compa-ratio, 2 dp for percentages); percentages are computed as a decimal fraction ×100.

### F1 — The ordinary group (odd n, no band) — Check A against the group median

Level L3, pay market **DE (Hamburg)**, all PERMANENT, FTE 1.0, annual basis.

| Employee | Amount | | |
|---|---|---|---|
| U-05 | 54,000.00 | sorted → | 54,000.00 |
| U-01 | 60,000.00 | | 60,000.00 |
| U-02 | 63,000.00 | | **63,000.00 ← median (n=5, index 3)** |
| U-03 | 66,000.00 | | 66,000.00 |
| U-04 | 72,000.00 | | 72,000.00 |

**Group median = 63,000.00.** Compa-ratio to median, unrounded, and the Check A verdict (flag below 0.95, above 1.10):

| Employee | Calculation | Ratio (4 dp) | Verdict |
|---|---|---|---|
| U-05 | 54,000 / 63,000 | **0.8571** | **FLAG — below** |
| U-01 | 60,000 / 63,000 | **0.9524** | no flag (0.95238… > 0.95 — a near-boundary pass) |
| U-02 | 63,000 / 63,000 | **1.0000** | no flag |
| U-03 | 66,000 / 63,000 | **1.0476** | no flag |
| U-04 | 72,000 / 63,000 | **1.1429** | **FLAG — above** |

**Expected: exactly 2 OPEN flags, on U-05 and U-04. Not 4, not 45.** A pairwise implementation on this group
produces 10 comparisons and would flag most of it — that assertion (`flag_count == 2`) is what catches "never
pairwise" (D1).

### F2 — Compa-ratio boundary against a **band** (the exact-threshold trio)

Band for L3/DE: min 59,500.00, **midpoint 70,000.00**, max 80,500.00.

| Case | Amount | Calculation | Ratio | Verdict | What it catches |
|---|---|---|---|---|---|
| F2-a | 66,500.00 | 66,500 / 70,000 | **0.950000** | **no flag** — the rule is *below* 0.95 | Off-by-one on the boundary |
| F2-b | 66,499.99 | 66,499.99 / 70,000 | 0.9499998… | **FLAG** | — |
| F2-c | 66,500.01 | 66,500.01 / 70,000 | 0.9500001… | no flag | — |
| F2-d | **66,465.00** | 66,465 / 70,000 | **0.949500** | **FLAG** | **Rounding before comparing.** 0.9495 rounds (2 dp) to 0.95 — an engine that rounds the compa-ratio before testing it **silently loses this flag**. This is the single most likely arithmetic defect in KAN-200 |
| F2-e | 77,000.00 | 77,000 / 70,000 | **1.100000** | **no flag** — the rule is *above* 1.10 | Upper boundary |
| F2-f | 77,000.01 | 77,000.01 / 70,000 | 1.1000001… | **FLAG** | — |

**Also assert:** where a band exists the basis **is the midpoint**, not the group median — F2's group median is
irrelevant to the verdict, and a case (UAT-42-200-11) puts a deliberately misleading median in the same group to
prove the selection.

### F3 — Gender pay gap: the exact-threshold trio (Check B, threshold ≥ 5%)

Level L2, market DE, n=6, 3 male / 3 female, all FTE 1.0 annual. Gap = **(median male − median female) / median male**.

| Variant | Male amounts | Median M | Female amounts | Median F | Gap | Verdict |
|---|---|---|---|---|---|---|
| **F3-a** | 98,000 / **100,000** / 104,000 | 100,000.00 | 93,000 / **95,000** / 96,000 | 95,000.00 | (100,000−95,000)/100,000 = **0.050000 = 5.00%** | **FLAG** (≥ 5%) |
| **F3-b** | 98,000 / **100,000** / 104,000 | 100,000.00 | 93,000 / **95,050** / 96,000 | 95,050.00 | 4,950/100,000 = **0.049500 = 4.95%** | **no flag** |
| **F3-c** | 98,000 / **100,000** / 104,000 | 100,000.00 | 93,000 / **94,950** / 96,000 | 94,950.00 | 5,050/100,000 = **0.050500 = 5.05%** | **FLAG** |
| **F3-d** | 98,000 / **100,000** / 104,000 | 100,000.00 | 99,000 / **99,990** / 101,000 | 99,990.00 | 10/100,000 = **0.000100 = 0.01%** | no flag — and the **displayed** value must be `0.01%`, not `0%` |

**F3-e — the negative gap (finding UAT-F-02).** Male median 95,000, female median 100,000 → gap = −5.26%.
As written, D1's rule (`flag at ≥ 5%`) does **not** flag it. A tester cannot mark this pass or fail until the SPM
says whether the check is directional. **Recommended default: flag on |gap| ≥ threshold and record the direction**,
because "women are paid 5% more here and we never noticed" is the same measurement failure in the other direction.
Case UAT-42-200-19 is written against that default and marked *Blocked on OQ*.

### F4 — Group-size minimums

Check A needs **n ≥ 3 comparable**; Check B needs **n ≥ 5 comparable and ≥ 2 of each gender compared**.

| Fixture | Composition | Check A | Check B | Expected text |
|---|---|---|---|---|
| F4-a | n=1 | no flag | no flag | "Insufficient comparison group" — reported in the coverage view, **never as a flag or a notification** |
| F4-b | n=2 (70,000 / 100,000 — a 42.9% spread) | **no flag** | no flag | Same. A 42.9% spread that is correctly *not* flagged is the case that proves the minimum is honoured |
| F4-c | n=3 (60,000 / 63,000 / 90,000) | **evaluated**; median 63,000; 90,000/63,000 = 1.4286 → **FLAG** | no flag (n<5) | One flag, from Check A only |
| F4-d | n=5, 5 male 0 female | evaluated | **no flag** — single gender | "Insufficient comparison group for the gender gap check" — a *different* message from "no gap found" |
| F4-e | n=5, 4 male 1 female | evaluated | **no flag** — needs ≥2 of each | Same |
| F4-f | n=6, 3+3, all identical amounts | **no flag** (all ratios 1.0000) | **gap = 0.00%, no flag** | The all-equal group must produce **exactly `0.00`**, not `0.0000000001` — see F7 |

### F5 — The coverage gate (default 80%)

Group of **50** L4 employees in market DE.

| Fixture | With a record | Coverage | Expected |
|---|---|---|---|
| F5-a | 39 | **78.00%** | **Not evaluated. Zero flags.** "Insufficient coverage — not evaluated (78% of 50)" |
| F5-b | 40 | **80.00%** | **Evaluated** (gate is inclusive — recommended default, finding UAT-F-01b) |
| F5-c | 41 | **82.00%** | Evaluated |
| **F5-d** | **39 of 49** | **79.59%** | **Not evaluated** — and this is the trap: 79.59% **displays as 80%** at 0 dp. An engine that gates on the *rounded display value* evaluates this group and produces flags it must not produce |
| F5-e | 0 of 50 | 0.00% | Not evaluated; the group appears in the coverage view with a "Record salary" route, never as "no findings" |
| F5-f | 50 of 50 | 100.00% | Evaluated |

**Also:** a company that has **never** crossed the gate shows the coverage meter and the missing list, and the
equity queue shows **no "no findings ✓" state at all** (D7.4) — asserted on text, because "no findings" at 40%
coverage is the most dangerous screen in the epic and it will pass any presence-only assertion.

### F6 — Pay markets must not be merged (the Tallinn/Hamburg case)

Same family, same level L3. Hamburg (DE) U-01…U-05 per F1. Tallinn (EE) U-16…U-20 at 30,000 / 32,000 / 34,000 /
36,000 / 38,000.

- **Expected: two groups, evaluated separately.** DE median 63,000, EE median 34,000.
- **Expected: zero cross-market flags.** If the engine keys on `(company, family, level)` and omits `pay_market`,
  the combined median of the ten is (38,000+54,000)/2 = **46,000.00** and **all five EE employees plus U-05 flag** —
  six wrong findings, and the credibility of the feature is gone on its first run (D1). `flag_count == 2` on this
  fixture is the assertion.
- **Merged-market refusal:** configure a market merging DE + EE with **no FX rate** → configuration **refused**,
  named error, nothing saved, **no silent 1:1**.

### F7 — FTE normalisation, and the float trap

U-06: PART_TIME, **FTE 0.60**, recorded annual **42,000.00**. Group otherwise all 70,000.00 at FTE 1.0, n=5.

- **Normalised = 42,000.00 / 0.60 = 70,000.00 exactly.**
- **Group median = 70,000.00. Every compa-ratio = 1.0000. Gap = 0.00%. Zero flags.**
- **The trap:** in IEEE-754 binary, `42000 / 0.6 == 70000.00000000001`. A float implementation therefore produces a
  compa-ratio of `1.0000000000000002` and a group spread of `1.42e-11` — under any threshold, so **no flag either
  way**, which is why this defect survives a presence-only test. The case asserts the **stored and returned
  normalised value equals `Decimal('70000.00')` exactly** and the reported gap equals `Decimal('0.00')` exactly.
  **A float implementation fails this case; a decimal one passes.** That is the entire point of it.
- **Also:** the *displayed* amount for U-06 is their **actual** 42,000.00 (what they are paid). The 70,000.00 is a
  comparison basis and must never be shown as their salary — an FTE-normalised figure presented as pay is a
  wrong number in front of an employee.

### F8 — Annualisation across pay bases

Company standard annual hours = **2,080** (configurable; Telia's is set to **1,720** for the cross-check).

| Fixture | Basis | Recorded | Annualised — exact | Must NOT be |
|---|---|---|---|---|
| F8-a | annual | 70,000.00 | **70,000.00** | — |
| F8-b | monthly | 5,833.33 | 5,833.33 × 12 = **69,999.96** | **not** 70,000.00 — "tidying" a monthly figure to a round annual is inventing data |
| F8-c | hourly | 33.6538 | 33.6538 × 2,080 = 69,999.904 → **69,999.90** (HALF_UP, 2 dp) | not 69,999.91, not 70,000.00 |
| F8-d | hourly, Telia | 33.6538 | 33.6538 × 1,720 = 57,884.536 → **57,884.54** | Proves annual hours is per company and not a constant |
| F8-e | monthly, 0.5 FTE | 2,916.67 | ×12 = 35,000.04, ÷0.5 = **70,000.08** | Order of operations is annualise **then** normalise; the reverse gives 70,000.08 too here, but F8-f distinguishes it |
| F8-f | hourly 33.6538, FTE 0.6 | — | annualise then normalise: 69,999.90 / 0.6 = **116,666.50** | Any other value means the two steps are in the wrong order or double-applied |

### F9 — Median on an **even**-sized group

n=4, L1/DE: 60,000.00 / 64,000.00 / 68,000.00 / 74,000.00.

- **Median = (64,000.00 + 68,000.00) / 2 = 66,000.00.**
- Ratios: 0.9091 **FLAG** · 0.9697 no · 1.0303 no · 1.1212 **FLAG**. **Expected 2 flags.**
- An implementation that takes the *lower* middle (64,000) gives 0.9375 **FLAG** / 1.0000 / 1.0625 / 1.1563 **FLAG**
  — same flag *count*, different **measured gap values**. So the case asserts the **reported gap number**, not just
  the count. A count-only assertion cannot tell these two implementations apart.

### F10 — Median rounding on an even group (which rounding mode?)

n=2 (for the median computation only; Check A does not run at n=2, so this is exercised through the **coverage/
group statistics** surface): 70,000.00 and 70,000.01.

- Exact mean = **70,000.005**.
- **HALF_UP → 70,000.01.** **HALF_EVEN (banker's) → 70,000.00.**
- The plan's stated convention is HALF_UP, so **expected 70,000.01**. **This is untestable until the rounding mode
  is ratified (UAT-F-01)** — the case is written, marked *Blocked*, and must not be run against a guess.

### F11 — Does the subject count in their own group median?

n=3: 50,000.00 / 52,000.00 / 90,000.00. Subject = the 90,000.

- **Including the subject (recommended default, and what "group median" means):** median 52,000.00 →
  ratio 90,000/52,000 = **1.7308**, gap reported as **+73.08%**.
- **Leave-one-out:** median of (50,000; 52,000) = 51,000.00 → ratio **1.7647**, gap **+76.47%**.
- Both flag, so a flag-count assertion **cannot distinguish them**. The case asserts the reported figure is
  **1.7308 / +73.08%**. Unspecified in Wave 1 — finding UAT-F-01c, recommended default *include*.

### F12 — Exclusions are counted, never silent

Group of 8 in L3/DE: 5 PERMANENT with records, 1 PART_TIME with a record, 1 CONTRACTOR (U-07), 1 INTERN (U-08),
plus U-09 PERMANENT with **no** record (group total 9).

- **Compared: 6.** **Excluded: 3** — 1 contractor, 1 intern (excluded *by design*), 1 no-record (excluded *as
  missing*). **Coverage = 6 / 7 comparable-by-type = 85.71%** — contractors and interns are **out of the
  denominator**, because D7.7 says they are "not applicable", not "missing". Conflating the two makes the coverage
  meter lie, and this fixture is the one that proves it did not.
- Displayed: `6 compared / 9 in group · 2 not applicable (contractor, intern) · 1 no record · coverage 85.71%`.
- **Assert all five numbers.** A single wrong denominator here changes whether the group passes the gate.

---

## 6. Test cases — KAN-188 … KAN-202

**300 cases.** Counts per story: 188·20 · 189·18 · 190·16 · 191·17 · 192·14 · 193·20 · 194·32 · 195·22 · 196·21 ·
197·15 · 198·14 · 199·15 · 200·34 · 201·26 · 202·16.

Status of every case is **Not Executed** — nothing is built. `Sev` is the severity **if the case fails**.

### 6.1 KAN-188 — The tenant exposure switch (R7 · D6) — 20 cases

*What this story must prove: a feature the product owner has turned off for a tenant is **unreachable**, not merely
absent from the nav; and turning the mechanism on changes nothing for any of the eleven features that exist today.*

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-188-01 | Happy | `compensation` enabled for Acme, role grant HR_ADMIN r+w | `ingrid.makinen` opens the nav | The Compensation nav item is present and opens the landing page (200) | High | B |
| UAT-42-188-02 | Happy | `compensation` **disabled** for Telia | `maria.andersson` opens the nav | No Compensation nav item | Medium | B |
| UAT-42-188-03 | **Adv** | as -02 | `maria.andersson` navigates by direct URL to `/compensation`, `/compensation/equity`, `/compensation/bands`, `/admin/job-levels` | Every one returns the **off-state screen** (a real explanatory page, `analytics_locked.html` precedent) — not a 403, not a redirect to the dashboard, not a blank page | **Critical** | P+B |
| UAT-42-188-04 | **Adv** | as -02 | `maria.andersson` calls every EP42 JSON endpoint by `fetch` with a valid session | Refused, and **the response body contains no compensation data of any kind** (CC-T1) | **Critical** | P |
| UAT-42-188-05 | Perm | Telia role matrix grants HR_ADMIN `compensation` r+w, tenant switch **off** | Telia HR_ADMIN opens `/compensation` | Off-state screen. **Effective access = tenant switch AND role grant** — a role grant cannot outvote the tenant switch | **Critical** | P |
| UAT-42-188-06 | Perm | Tenant switch **on** for Acme, role matrix grants nothing to EMPLOYEE | `tonis.rebane` opens `/compensation` | Normal permission denial (the existing `require_feature_access` behaviour), **not** the off-state screen — the two states mean different things and must not be conflated | Medium | P |
| UAT-42-188-07 | Perm | `compensation` off for Acme | `oliver.hartmann` (SYSTEM_ADMIN) in Acme context opens `/compensation` | Reaches the feature (bypass preserved) **and** sees an unmistakable "disabled for this tenant" banner. A silent bypass is how a demo shows a customer a feature they have not bought (D6.3) | High | B+H |
| UAT-42-188-08 | Edge | Sam Cpmapny (0 employees), `compensation` on | PORTAL_ADMIN of Sam Cpmapny opens every EP42 surface | Empty states throughout, no crash, coverage meter reads **"0 of 0 active employees"** and **not** `NaN%`, `0%` or a division-by-zero error | High | P |
| UAT-42-188-09 | Edge | Feature toggled off while a user is mid-session on the page | Toggle off as SYSTEM_ADMIN; the Acme user clicks any action on the open page | The **next request** is refused (`g._feature_access` is per-request) — no stale grant survives the toggle | High | P |
| UAT-42-188-10 | Edge | `company_features` row **absent** for an existing feature/tenant pair | Any user of that tenant opens that feature | **Enabled** — absent defaults to enabled for the eleven existing features (D6.2) | **Critical** | P |
| UAT-42-188-11 | Edge | `company_features` row absent for `compensation` / `compensation_self` / `pay_equity` | Any user | **Disabled** — absent defaults to disabled for the three EP42 codes (D6.2, D8 safeguard, OQ-7) | High | P |
| UAT-42-188-12 | **Regression** | Baseline captured before KAN-188 | For **each of the 11 existing feature codes × each of the 3 tenants × each role**, compare effective access before and after the change | **Byte-identical access matrix.** This is the acceptance criterion that matters (D6.2) and it is a table comparison, not a spot-check | **Critical** | P |
| UAT-42-188-13 | Regression | `reports` and `skills_intelligence` retro-fitted off their hand-rolled checks | Toggle `reports` off for Acme; open `/admin/analytics` | Same behaviour as before the retro-fit (the locked screen), now served by the **central** resolution. `app/routes/analytics.py:20-40` no longer hand-rolls it | High | P+B |
| UAT-42-188-14 | Regression | as -13 | Grep the codebase after the story | **One** implementation of the tenant check. Three implementations means the story made things worse (D6 requirement 8) | High | P |
| UAT-42-188-15 | **Adv** | — | Attempt to set `enabled_for_hr` from any EP42 surface, and grep EP42 code for reads of it | Not writable, not read. `enabled_for_hr` gains **no new consumer** (D6.9; `CLAUDE.md` forbids the pattern by name) | High | P |
| UAT-42-188-16 | **Tenant** | `compensation` on for Acme, off for Telia | `oliver.hartmann` switches company context Acme → Telia → Acme | The switch is honoured per tenant on every switch, in nav and on routes, with no bleed in either direction | **Critical** | B |
| UAT-42-188-17 | **Tenant** | — | Acme PORTAL_ADMIN attempts `POST /api/admin/company-features/<TELIA_UUID>/toggle` | `403`/`404`, nothing written. Only SYSTEM_ADMIN owns the tenant switch, and only for the tenant in context | **Critical** | P |
| UAT-42-188-18 | **Audit** | — | SYSTEM_ADMIN toggles `pay_equity` on for Acme with a reason | One `audit_log` row: `company_id`, feature code, old→new, actor, reason, correlation id. No amount (none exists yet, but the shape is asserted here) | High | P |
| UAT-42-188-19 | Edge | — | Toggle the same feature on twice in a row | Idempotent: second toggle is a no-op or an explicit "already enabled", and writes **at most one** meaningful audit row — never a duplicate pair | Low | P |
| UAT-42-188-20 | **Adv** | Feature off for Telia | A Telia user follows a **deep link** from an old notification/email into an EP42 page | Off-state screen, no data, and the link does not open a dead dialog (D4 blind-spot item 10) | High | B |

### 6.2 KAN-189 — Effective dating on the request (D4d · CFL-4 · unblocks AC-185-07) — 18 cases

*The cases that quietly rot. Every one of these asserts the **database rows**, not the API response (CC-T2).*

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-189-01 | Happy | Acme, U-01 has one current assignment | `ingrid.makinen` raises a transfer with `effective_date` = today; chain approves fully | The outgoing assignment closes and the incoming one opens on **the same boundary date**, per the Architect's chosen convention | High | P |
| UAT-42-189-02 | **Edge** | as -01, applied | `SELECT` all `employee_org_assignments` for U-01 | **Exactly one row with `is_current = TRUE`, and no two rows covering the same calendar day.** This is `AC-185-07` and the CFL-4 one-day overlap, asserted by direct query, not by the UI | **Critical** | P+R |
| UAT-42-189-03 | Happy | — | Raise a transfer with `effective_date` = today + 30 | Rejected at submission while there is no scheduler — a **future-dated placement** is not supported (EP38 R5.6), with a message that says so and offers today | High | P |
| UAT-42-189-04 | Happy | — | Raise a `COMPENSATION_REVIEW` with `effective_date` = today + 30 | **Accepted.** A future-dated compensation record is inert data until its date. The two must not be conflated (D4d) | High | P |
| UAT-42-189-05 | **Edge** | Company window = 90 back / 180 forward | Compensation effective_date = today − 90 | **Accepted** (boundary inclusive) | Medium | P |
| UAT-42-189-06 | **Edge** | as -05 | effective_date = today − 91 | **Rejected**, named error, nothing written | Medium | P |
| UAT-42-189-07 | **Edge** | as -05 | effective_date = today + 180 / today + 181 | Accepted / rejected respectively | Medium | P |
| UAT-42-189-08 | **Edge** | U-01 has records effective 2026-01-01 (60,000) and 2026-07-01 (65,000) | Query "current salary" on 2026-08-09 | **65,000.00** — the greatest `effective_from` **≤ today** | High | P |
| UAT-42-189-09 | **Edge** | as -08, plus a record effective **2026-08-09** (70,000) | Query current salary on 2026-08-09 | **70,000.00** — the boundary day is **inclusive**; a record effective today is effective today | High | P |
| UAT-42-189-10 | **Edge** | as -09 | Query current salary "as at" 2026-08-08 | **65,000.00** — the day before the boundary returns the previous record | High | P |
| UAT-42-189-11 | **Edge** | as -09, plus a record effective 2026-12-01 (80,000) | Query current salary on 2026-08-09 | **70,000.00**. The future record is **visible in the timeline marked as future** and is **never** the current value | High | P |
| UAT-42-189-12 | **Adv** | as -11 | Run the equity check | The engine compares **70,000.00**, not 80,000.00. Using a future-dated record in a present-tense comparison is a wrong finding about a real person | **Critical** | P+R |
| UAT-42-189-13 | **Adv** | U-01 has a record effective 2026-07-01 | Write a **second** record with `effective_from` = 2026-07-01 | Per the resolved rule (**UAT-F-01d — currently contradictory**: "exactly one current record per employee per date" vs "a correction is a new record"). Recommended default: **accepted, the later `created_at` supersedes, the earlier is marked superseded, and "current salary" returns exactly one value** | High | P |
| UAT-42-189-14 | **Edge** | as -13 | Query the timeline | Both rows appear, ordered, with the superseded one marked. History is the defensibility; hiding a correction defeats the point | High | P |
| UAT-42-189-15 | **Adv** | — | Retroactive record effective 2026-06-01 inserted **after** the 2026-07-01 record exists | Accepted (inside the window); current salary is **unchanged** (still the July record); the timeline shows the retroactive row in date order, not in insert order | High | P |
| UAT-42-189-16 | **Adv** | as -15 | Re-run the equity check | The engine's **present-tense** result is unchanged. EP42 does **not** claim to recompute history, and no screen implies it does | Medium | R+H |
| UAT-42-189-17 | **Adv** | — | Submit `effective_date` = `2026-13-01`, `not-a-date`, `0001-01-01`, `9999-12-31`, an empty string, and a very large integer | `400` each, named error, nothing written, no stack trace | Medium | P |
| UAT-42-189-18 | Regression | KAN-185 in flight | Re-run the KAN-185 transfer flow end to end | `AC-185-07` now passes; **no existing transfer behaviour changed** other than the date. `tests/test_org_change.py::TestApplyCarriesUnchangedFieldsForward` still green | High | P |

### 6.3 KAN-190 — The ladder configurator (R6 · D3) — 16 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-190-01 | Happy | Acme, `compensation:w` | `ingrid.makinen` creates family `UAT Engineering`, levels L1–L4 with titles, 5 steps each | Saved; levels display as `1.1 … 1.5`; each level carries **its own title** | High | P+B |
| UAT-42-190-02 | **Edge** | Acme has **no** ladder | Open the configurator | An **explicit empty state** with a route to create the first family. **Never** another company's levels, and never a global default ladder — the `CLAUDE.md` empty-state rule, applied to job levels | High | B |
| UAT-42-190-03 | **Edge** | — | Create a level with `steps_count` = **1**, **12** | Both accepted (range 1–12, D3.3) | Medium | P |
| UAT-42-190-04 | **Edge** | — | `steps_count` = **0**, **13**, **−1**, `1.5`, `"five"` | Rejected each, named error, nothing written | Medium | P |
| UAT-42-190-05 | Happy | Levels exist, **no** assignments yet | Reorder L2 above L3 | Allowed | Medium | P |
| UAT-42-190-06 | **Edge** | An employee is assigned to L2 | Reorder L2 | **Refused** — ordinal position is immutable once assignments exist. Renaming stays allowed (asserted in the same case) | High | P |
| UAT-42-190-07 | **Edge** | — | Two families in one company with the same name; two levels with the same ordinal in one family | Rejected with a named error | Medium | P |
| UAT-42-190-08 | **Edge** | — | Delete a level that has assignments | Refused, naming the count of affected employees | High | P |
| UAT-42-190-09 | **Adv** | — | Create a level whose title is payload **X1**, family **X2**, step label **X5** (§3.6) | Stored byte-identical; rendered as literal text in the configurator, the directory, the org-tree card, the equity queue and the bell; **zero dialogs**; `escH()` used by every new DOM builder | **Critical** | P+B |
| UAT-42-190-10 | **Adv** | — | Level title of 1,000 characters (**X6**) and unicode (**X7**) | Length limit enforced with a named error; unicode round-trips unharmed | Low | P |
| UAT-42-190-11 | Perm | HR_ADMIN has `compensation` **r only** | Open the configurator; attempt every mutation | Page readable; every mutating call `403` with **zero state change**, verified by re-reading (D5.4) | High | P |
| UAT-42-190-12 | Perm | EMPLOYEE | Open `/admin/job-levels` directly | Denied. Gated `@require_feature_access('compensation','w')` — **never** a hardcoded role list (`CLAUDE.md` invariant 1) | High | P |
| UAT-42-190-13 | Perm | Tenant grants `compensation:w` to SOLID_LINE_MANAGER via the Feature Access tab | That manager opens the configurator | **Access granted with no code change.** The regression that CLAUDE.md's "past mistakes" section exists to prevent | High | P |
| UAT-42-190-14 | **Tenant** | Acme has a ladder; Telia has none | Telia PORTAL_ADMIN opens the configurator | Empty state. **Acme's families and levels appear nowhere**, under no filter, in no picker, in no autocomplete | **Critical** | P+B |
| UAT-42-190-15 | **Tenant** | — | Acme HR_ADMIN `PUT`s a **Telia** level UUID | `404` (per A07), nothing read, nothing written | **Critical** | P |
| UAT-42-190-16 | **Audit** | — | Create, rename, reorder and delete a level | Four audit rows with actor, reason, before→after of the **non-monetary** fields, correlation id | Medium | P |

### 6.4 KAN-191 — Everyone on a level: assignment, mapping screen, CSV (R6 · R2 · D7) — 17 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-191-01 | Happy | Ladder exists | `ingrid.makinen` assigns U-01 to (UAT Engineering, L3, step 2) effective today | Assignment stored effective-dated; the level title becomes the canonical displayed job; `employees.job_title` **unchanged** and relabelled "Working title" (S12, CFL-42-4) | High | P+B |
| UAT-42-191-02 | Happy | Acme, 41 distinct free-text titles | Open the mapping screen | Every distinct `job_title` listed **with its headcount**, sorted by headcount descending; total across rows = the company's ACTIVE count | High | B |
| UAT-42-191-03 | Happy | as -02 | Assign a level to one title and bulk-apply | Every employee holding that title is assigned; the count applied is reported and matches the row's headcount exactly | High | P |
| UAT-42-191-04 | Happy | as -02 | Export the mapping CSV, edit, re-import | Round-trip: the re-import applies exactly the edited rows and reports the rest as unchanged | High | P |
| UAT-42-191-05 | **Edge** | 45 of 46 assigned | Open the coverage meter | "45 of 46 (97.83%)" with the remaining one **exportable**; the unassigned employee is **counted, never silently dropped** | High | P+B |
| UAT-42-191-06 | **Edge** | Sam Cpmapny | Open the mapping screen | "No employees to map" — not "100% complete". 0/0 must not read as done | Medium | P |
| UAT-42-191-07 | **Edge** | An employee holds a title used by nobody else | Map it | Works; a group of one is a valid *assignment* even though it is not a valid *comparison* (that is F4-a's job) | Low | P |
| UAT-42-191-08 | **Adv** | — | Import the mapping CSV with payloads **M1–M28** (§3.6) | Row-level rejection with the row number and reason for each; **nothing committed for a rejected row**; no 500, no stack trace, no partial commit | High | P |
| UAT-42-191-09 | **Adv** | — | **M5**: a Telia `employee_number` in an Acme import | Row rejected as "not found in this company" — **and the error must not confirm that the number exists elsewhere** (existence oracle across tenants) | **Critical** | P |
| UAT-42-191-10 | **Adv** | — | **M22** formula-injection values in the title column, then export the mapping CSV | The exported cell is neutralised (leading `'` or refused). A product that round-trips `=HYPERLINK(...)` into a customer's Excel has shipped a payload | High | P |
| UAT-42-191-11 | **Adv** | — | Import 100,000 rows (**M21**) | Either processed atomically or refused with a named row limit. **Never** a half-applied file | High | P |
| UAT-42-191-12 | **Edge** | U-01 assigned to L3 effective 2026-01-01 | Assign to L4 effective 2026-06-01; query as-at 2026-03-01 and 2026-08-09 | L3 and L4 respectively; assignment history contiguous and non-overlapping | High | P |
| UAT-42-191-13 | Perm | `compensation` r only | Attempt to assign | `403`, no state change | High | P |
| UAT-42-191-14 | Perm | Solid-line manager with `compensation:r` | Open the mapping screen | Denied (mapping is a `w` surface) — and denied **by the feature gate**, not by a role list | Medium | P |
| UAT-42-191-15 | **Tenant** | — | Acme mapping screen | Lists **only** Acme titles and headcounts. Telia's 75 titles appear nowhere; the level picker offers only Acme levels | **Critical** | P |
| UAT-42-191-16 | **Tenant** | — | Acme HR_ADMIN assigns a **Telia** employee UUID to an Acme level | `404`, nothing written, no cross-tenant assignment row created | **Critical** | P |
| UAT-42-191-17 | **Audit** | — | Assign, re-assign and un-assign | Audit rows with level/step before→after, actor, reason, correlation id, **and no amount** | Medium | P |

### 6.5 KAN-192 — Step advancement and the promotion-eligible signal (R6 · D3.4) — 14 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-192-01 | Happy | U-01 at L3 step 2 | `liisa.virtanen` (solid-line manager) advances U-01 to step 3 with a reason | Applied; audited with step before→after; **no** approval chain required because no pay change rides on it (D3.4) | High | P |
| UAT-42-192-02 | Happy | as -01 with a pay change attached | Advance step **and** propose a new salary | Routed through the approval chain as a compensation change — D4 applies. A pay change never bypasses the chain by being called a step | **Critical** | P |
| UAT-42-192-03 | **Edge** | U-01 at L3 step **5** of 5 | Advance | **Refused as an advancement**; instead a `promotion_eligible` marker is set on the assignment. **No automatic roll-up to L4** (D3.4, OQ-1) | **Critical** | P |
| UAT-42-192-04 | **Adv** | as -03 | Re-read the assignment, the level, the title and any band | **Nothing has changed** except the marker. No title change, no band change, no salary change, no comparison-group change | **Critical** | P |
| UAT-42-192-05 | **Notif** | as -03 | Check the bell of the solid-line manager and of each `compensation:w` holder | The signal appears with the correct section, a **non-outcome icon** (never ✅ and never ❌ — it is not a decision), a badge increment, and one action that leads to raising a `PROMOTION` request | High | B |
| UAT-42-192-06 | **H** | as -05 | Read the signal's wording aloud to an HR proxy and to an employee proxy | It reads as a **signal, not an entitlement**. No forward-looking language, no implied promise. *A green assertion cannot prove this; a misread sentence here is a promise the company did not make* | High | **H** |
| UAT-42-192-07 | **Notif** | The manager raises the promotion; it is decided | Re-check every recipient's bell | The eligibility signal **retires** for **every** recipient, not only the one who acted (DEF-003) | High | C |
| UAT-42-192-08 | **Notif** | Signal raised; recipient opens the bell and does nothing | Re-check | Still present. **Reading is not deciding** (D2, the DEF-003 failure in reverse) | High | C |
| UAT-42-192-09 | Happy | — | Skip-step (2 → 4), skip-level, and a **downward** move, each with a reason | All permitted; all audited with before→after and the reason; a one-way ratchet is a fiction and blocking it drives HR into the database (D3.4) | Medium | P |
| UAT-42-192-10 | **Edge** | — | Any of the above with the reason left blank | Refused. **Reason is mandatory on every transition** | Medium | P |
| UAT-42-192-11 | **Adv** | — | An employee advances **their own** step by direct API call | `403`. The KAN-139 rule generalises: you do not move yourself, in any dimension | **Critical** | P |
| UAT-42-192-12 | Perm | Manager with `compensation:r` only | Advance a report's step | `403`, no state change | High | P |
| UAT-42-192-13 | **Tenant** | — | Acme manager advances a **Telia** employee's step | `404`, nothing written | **Critical** | P |
| UAT-42-192-14 | **Audit** | Every transition above | Read the audit rows as an `audit_log:r` holder **without** `compensation:r` | Level/step before→after visible; **no amount anywhere**, including where the step carried a pay change (D5.6) | **Critical** | P |

### 6.6 KAN-193 — The compensation record (R1) — 20 cases

*Append-only, effective-dated, atomic. Every case asserts the row (CC-T2) and compares decimals (CC-T3).*

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-193-01 | Happy | Acme, `compensation:w` | Record U-01: 70,000.00 EUR, FTE 1.0, annual, effective today, reason "UAT baseline" | Row stored with amount `70000.00`, currency, FTE, basis, effective_from, actor, reason, correlation id, and `employment_type` **copied onto the record** so exclusion is stable over time | High | P |
| UAT-42-193-02 | **Math** | as -01 | Read back the amount | `Decimal('70000.00')` exactly — **not** `70000.0`, not `7.0e4`, not a float. Assert the type as well as the value (CC-T3) | High | P |
| UAT-42-193-03 | **Adv** | as -01 | Attempt `UPDATE` and `DELETE` on the record through every route and API | No path exists. A correction is a **new record**; a void is a **marked** record (`compensation:d`) | **Critical** | P |
| UAT-42-193-04 | Happy | as -01 | Void the record as PORTAL_ADMIN (`d`) with a reason | Marked voided, **still present**, excluded from "current", visible in the timeline. History is the defensibility | High | P |
| UAT-42-193-05 | Perm | HR_ADMIN (no `d`) | Attempt the void | `403`, no state change (D5.4 — `d` is PORTAL_ADMIN only) | High | P |
| UAT-42-193-06 | **Edge** | — | Amounts: `0`, `-1`, `0.001`, `99999999999999.99`, `100000000000000.00`, `""`, `null`, `"abc"`, `7e4`, `70,000.00`, `€70000` | Zero and negative **refused** with a named error; over-precision refused or rounded per the ratified rule (UAT-F-01); the too-large value refused, not silently truncated; every non-numeric refused. Nothing written in any case | High | P |
| UAT-42-193-07 | **Edge** | — | FTE: `0`, `0.009`, `0.01`, `1.00`, `1.01`, `2.00`, `-0.5`, `""` | `0` **must** be refused (it is a division by zero in every downstream comparison — F7). The rest per the ratified FTE range — **currently unspecified, UAT-F-01e**; recommended `0.01 … 1.00` | High | P |
| UAT-42-193-08 | **Edge** | — | Currency: a valid ISO code, a lowercase code, an invalid code, an empty string | Valid accepted (normalised to upper), invalid refused. **No default currency is ever assumed** — an assumed currency is a wrong number | High | P |
| UAT-42-193-09 | **Edge** | — | Pay basis `annual` / `monthly` / `hourly` / `weekly` | The first three accepted; `weekly` refused (not in the model) with a named error rather than being coerced | Medium | P |
| UAT-42-193-10 | **Edge** | Company standard annual hours unset | Record an **hourly** salary | Refused with "configure standard annual hours first" — **never** annualised against a hardcoded 2,080 (F8) | High | P |
| UAT-42-193-11 | **Edge** | — | Reason blank / whitespace only | Refused. Reason is mandatory (KAN-187 pattern) | Medium | P |
| UAT-42-193-12 | **Adv** | Simulate a failure between the compensation insert and the audit insert | Record a salary | **Both roll back.** One `transaction()` boundary (KAN-155, DEP-1); no orphan record, no orphan audit row. Assert with the `FakeTransaction` / `assert_single_atomic_unit` helpers already in `tests/conftest.py:46-64` | **Critical** | P |
| UAT-42-193-13 | **Adv** | — | Two actors record a salary for U-01 concurrently | Exactly one succeeds or both are recorded as an ordered append with a deterministic "current" — **never** a lost update and never two rows both claiming current | High | P+R |
| UAT-42-193-14 | **Edge** | U-09 has no record | Read U-09 as a `compensation:r` holder | **"No salary recorded"** with a "Record salary" action. **Never** a blank, a dash, a zero or a hyphen (D7.1) | **Critical** | P+B |
| UAT-42-193-15 | **Edge** | U-07 CONTRACTOR, U-08 INTERN | Read them as a `compensation:r` holder | **"Not applicable — Contractor" / "— Intern"**, visually and textually distinct from "No salary recorded" (D7.7) | High | P+H |
| UAT-42-193-16 | **Adv** | — | Search the whole product for any derived, estimated or imputed salary (band midpoint shown as a person's pay, group median shown in a person's row) | **None exists anywhere.** An imputed figure on a screen is indistinguishable from a real one (D7.6) | **Critical** | P+H |
| UAT-42-193-17 | **Edge** | Employee is `RESIGNED` / `TERMINATED` | Record a salary; read the existing record | Behaviour per the BA's answer to "what a non-ACTIVE employee's record does" (SPM §8.1.2 — **currently unspecified, UAT-F-08**). Recommended: existing history readable and retained; new records refused except a correction | Medium | P |
| UAT-42-193-18 | Perm | `compensation:r` without `w` | Every mutating endpoint on this story | `403`, **zero state change** re-verified by reading the row back (A20) | High | P |
| UAT-42-193-19 | **Tenant** | — | Acme HR_ADMIN records a salary against a **Telia** employee UUID | `404`, nothing written, and no row appears in either tenant | **Critical** | P |
| UAT-42-193-20 | **Audit** | -01 and -04 | Read the audit rows | `COMPENSATION_RECORDED` / `COMPENSATION_VOIDED` present in `ACTIONS`; diff carries `has_change`, `direction`, `pct_change_band`, `currency`, `effective_date` — **and no amount** (D5.6); `entity_id` is the compensation record id; the correlation id matches the compensation row's | **Critical** | P |

### 6.7 KAN-194 — Who may see a salary (D5) — 32 cases · **the negative-visibility suite**

*This is the story I will hold the release on. Every case asserts **absence from the payload** (CC-T1), and every
case that fails means somebody obtained a figure they must not have — so almost all of them are Critical.*

**6.7.1 The matrix, executed cell by cell.** For each row, the tester requests (a) the HTML profile
`/profile/<subject>`, (b) the compensation JSON endpoint for that subject, and (c) the employee list JSON, and
records which of the three carry the amount.

| ID | Type | Actor (default matrix, D5.2) | Subject | Expected (HTML · JSON · list) | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-194-01 | Perm | EMPLOYEE `tonis.rebane` | **self** | Amount shown in "My Pay" · present · absent from the list | High | P+B |
| UAT-42-194-02 | Perm | EMPLOYEE `tonis.rebane` | another employee | **absent · 403 · absent** | **Critical** | P |
| UAT-42-194-03 | Perm | SOLID_LINE_MANAGER `liisa.virtanen` | **direct report** `sven.becker` | shown · present · present for that row only | High | P+B |
| UAT-42-194-04 | Perm | `liisa.virtanen` | a **non**-report | **absent · 403 · absent** (A02) | **Critical** | P |
| UAT-42-194-05 | Perm | `liisa.virtanen` | her report's **report** (skip level) | **absent · 403 · absent** — one level down, not the subtree (A03) | **Critical** | P |
| UAT-42-194-06 | Perm | DOTTED_LINE_MANAGER `uat.dotted`, granted `compensation:r` | their dotted report U-01 | **absent · 200 with zero rows · absent** (A04) | **Critical** | P |
| UAT-42-194-07 | Perm | DEPARTMENT_HEAD (default: no) | anyone in their department | **absent · 403 · absent** | **Critical** | P |
| UAT-42-194-08 | Perm | LOCATION_HEAD (default: no) | anyone in their location | **absent · 403 · absent** | **Critical** | P |
| UAT-42-194-09 | Perm | HIRING_MANAGER | anyone | **absent · 403 · absent** | **Critical** | P |
| UAT-42-194-10 | Perm | COMPANY_ADMIN (default: **no**) | anyone | **absent · 403 · absent** — administrative reach is not a reason to see pay (D5.2.3) | **Critical** | P |
| UAT-42-194-11 | Perm | HR_ADMIN `ingrid.makinen` | anyone in Acme | shown · present · present | High | P+B |
| UAT-42-194-12 | Perm | PORTAL_ADMIN | anyone in Acme | shown · present · present, plus `d` on history | High | P |
| UAT-42-194-13 | Perm | SYSTEM_ADMIN `oliver.hartmann` | anyone, in company context | Access by automatic bypass, **with no EP42 code re-implementing the bypass** (`CLAUDE.md` invariant 4) | High | P |

**6.7.2 Grants that widen, and grants that do not.**

| ID | Type | Preconditions | Steps | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-194-14 | Perm | Tenant grants `compensation:r` to DEPARTMENT_HEAD via the Feature Access tab | That user opens the surface | **Access granted with no code change and no additional role check in the route** (CC-1/CC-2; the `_si_enabled_for_hr` mistake must not recur) | High | P |
| UAT-42-194-15 | Perm | Tenant **narrows** `compensation` to PORTAL_ADMIN only | HR_ADMIN opens the surface | Denied. **And `compensation_self` is unaffected** — every employee still sees their own pay. Narrowing who sees *others'* pay must not blind everyone to their own (D5.1) | High | P |
| UAT-42-194-16 | Perm | Tenant disables `compensation_self` | Any employee opens their profile | No "My Pay" panel, no payload, and **no effect** on `compensation` holders' view of others | Medium | P |
| UAT-42-194-17 | **Adv** | — | A grant of `compensation:r` to a role whose defined scope is empty (DOTTED, HIRING_MANAGER) | Feature reachable, **result set empty**. Scope is a service rule, not a route check (D5.3) | High | P |

**6.7.3 The attacks (§4), executed.**

| ID | Type | Attack | Steps | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-194-18 | **Adv** | A01 | `tonis.rebane` GETs another employee's compensation endpoint using a UUID scraped from `href="/profile/<id>"` in the directory | `403`; body carries no compensation key | **Critical** | P |
| UAT-42-194-19 | **Adv** | A05 | Offboard `uat.exmgr`; replay their pending compensation request with the existing session cookie | Session invalid → login. If any session survives, scope is re-resolved per request and returns nothing | **Critical** | P+C |
| UAT-42-194-20 | **Adv** | A06 | Re-point U-01 to a new manager; the **old** manager requests U-01's pay | Refused. Scope follows `manager_relationships` as at **now**, never as at login | **Critical** | P |
| UAT-42-194-21 | **Adv** | A09 | Search `70000`, `70,000`, `€70000`, and U-01's exact amount, as every role | Zero employee hits. `employee_search_index` never contains an amount | **Critical** | P+B |
| UAT-42-194-22 | **Adv** | A10 | `/api/employees?sort=annual_base`, `?order_by=salary`, `?sort=-compa_ratio` as EMPLOYEE and as a scoped manager | Parameter rejected or ignored; **the returned order is identical to the default order** (assert the id sequence). Order is disclosure | High | P |
| UAT-42-194-23 | **Adv** | A11 | Download `/api/analytics/export/csv` and every EP42 export as each of the ten roles | No amount column for anyone lacking `compensation:r` **in scope**; a scoped manager's export contains only their reports' rows | **Critical** | P |
| UAT-42-194-24 | **Adv** | A12 | Inspect `/api/org-tree`, `/api/org-tree/context`, `/api/employees`, `/api/my-team`, `/api/dashboard/stats` as **PORTAL_ADMIN** | Compensation keys **absent for everyone**, including a user who is allowed to see pay elsewhere. These are not compensation surfaces | High | P+B |
| UAT-42-194-25 | **Adv** | A19 | "My Pay" with `?employee_id=<other>`, a JSON body override, and a tampered hidden form field | All ignored; the response is **always** the caller's own record; scope from `session.employee_id` only | **Critical** | P |
| UAT-42-194-26 | **Adv** | A20 | `compensation:r`-only holder calls every mutating EP42 endpoint | `403` on each, **zero state change** verified by re-read | High | P |
| UAT-42-194-27 | **Adv** | CSS-hidden check | For every surface where a role must not see pay, dump the raw response and grep for the digit string | **The digits are not in the response at all.** A `display:none` salary passes a screenshot review and fails this case — which is the point (SPM §8.4.2) | **Critical** | P+B |
| UAT-42-194-28 | **Adv** | X-payload | Set U-27's `last_name` to **X1**; render every EP42 surface that shows a subject name | Literal text everywhere, zero dialogs, `escH()` in every new builder | High | P+B |

**6.7.4 Tenant isolation for pay.**

| ID | Type | Preconditions | Steps | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-194-29 | **Tenant** | A07 | Acme HR_ADMIN substitutes a Telia employee UUID into **every** EP42 endpoint that takes an id (record, timeline, history, band, level, flag, disposition, import row, equity group) — enumerated, not sampled (CC-T5) | `404` on every one, nothing read, nothing written, **no existence oracle** | **Critical** | P |
| UAT-42-194-30 | **Tenant** | — | Same in reverse: Telia admin against Acme UUIDs | Identical | **Critical** | P |
| UAT-42-194-31 | **Tenant** | A08 | `oliver.hartmann` with "All Companies" opens every dashboard, analytics, coverage and equity surface | **No cross-tenant pay figure and no cross-tenant pay aggregate anywhere.** Cross-tenant comparison is out of scope for every role including SYSTEM_ADMIN (§3.3) | **Critical** | P+B |
| UAT-42-194-32 | **Tenant** | — | Every EP42 picker: pay markets, levels, families, escalation recipients, approval-chain roles | Each lists **only** the current company's rows — `WHERE company_id = %s::uuid` with **no** `OR company_id IS NULL` (`CLAUDE.md`). A company with no custom roles shows an **empty** picker, never the global templates | **Critical** | P |

### 6.8 KAN-195 — Backfill: bulk CSV and manual entry (R2 · D7) — 22 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-195-01 | Happy | Acme, `compensation:w` | Upload a valid 10-row CSV (`employee_number, effective_from, currency, annual_base, fte, pay_basis, reason`) | Dry-run preview shows **create / update / error per row** before anything is written | High | P+B |
| UAT-42-195-02 | Happy | as -01 | Commit | All 10 written **atomically** in one transaction (KAN-155); coverage meter increases by exactly 10 | High | P |
| UAT-42-195-03 | **Adv** | as -01 | Abandon the preview without committing | **Nothing written.** Re-read all 10 employees: still "No salary recorded" | High | P |
| UAT-42-195-04 | **Adv** | 3 of 10 rows invalid | Commit | Per the resolved rule — recommended **all-or-nothing per batch** with the 3 errors named. Whichever is chosen, **the preview's promise and the commit's behaviour must match exactly**; a preview that says "7 will be created" and a commit that creates 10 is the defect | High | P |
| UAT-42-195-05 | **Adv** | U-01 has 70,000.00 | Import a file with a **blank** amount (M7) and one with **0** (M8) for U-01 | **Rejected at preview**, not at commit. A file that would write null or zero over an existing salary never reaches the commit step (D7, and the D-185-1 lesson in its worst form) | **Critical** | P |
| UAT-42-195-06 | **Adv** | as -05, committed anyway via direct API | Re-read the row | U-01 still has **70,000.00**. The service layer refuses independently of the UI | **Critical** | P |
| UAT-42-195-07 | **Adv** | — | Payloads **M1–M28** (§3.6) | Per CC-T6: row-level rejection with row number and reason, nothing committed for that row, no 500, no stack trace | High | P |
| UAT-42-195-08 | **Adv** | — | **M22** formula injection in the reason column, then export the coverage/missing list | Neutralised on export | High | P |
| UAT-42-195-09 | **Adv** | — | **M4** duplicate `employee_number` in one file | Rejected as a duplicate naming both row numbers — **never** last-one-wins silently | High | P |
| UAT-42-195-10 | **Tenant** | — | **M5** a Telia `employee_number` in an Acme import | Row rejected as "not found in this company"; the error does not confirm it exists elsewhere; **nothing written in either tenant** | **Critical** | P |
| UAT-42-195-11 | **Adv** | — | **M21** 100,000 rows | Processed atomically or refused with a named limit; never half-applied; the preview does not time out silently | High | P |
| UAT-42-195-12 | **Edge** | — | **M27** empty file, **M28** header only, **M26** a PNG renamed `.csv` | Named errors, nothing written, no crash | Medium | P |
| UAT-42-195-13 | Happy | — | Manual single-employee entry from the profile | Written, audited, coverage meter increments by 1 | High | P+B |
| UAT-42-195-14 | **Edge** | Acme: 91 of 146 recorded | Open the compensation landing page | **"Compensation data: 62% of active employees (91 of 146)"** — the exact numerator, denominator and percentage asserted, and the missing list exportable | High | P+B |
| UAT-42-195-15 | **Edge** | F12 composition | Open the coverage meter | Contractors and interns are **out of the denominator** ("not applicable"), not counted as missing (D7.7). Assert all five numbers per F12 | High | P |
| UAT-42-195-16 | **Edge** | Sam Cpmapny | Open the coverage meter | "0 of 0 active employees" — **not** `NaN%`, not `100%`, not a crash. 0/0 must never read as complete | High | P |
| UAT-42-195-17 | **Adv** | — | Search every screen and export for a **derived** figure (band midpoint, group median, previous year's value) presented as a person's pay | None (D7.6) | **Critical** | P+H |
| UAT-42-195-18 | Perm | `compensation:r` only | Open the import wizard and the manual entry form | Denied on both; the mutating endpoints `403` with no state change | High | P |
| UAT-42-195-19 | Perm | Solid-line manager with `compensation:r` | Attempt a bulk import | Denied (bulk is `w`); the **manual** entry for their own report follows the ratified matrix cell | Medium | P |
| UAT-42-195-20 | **Tenant** | — | Acme import committed | Telia's coverage meter, missing list and records are **unchanged** — asserted by value, before and after | **Critical** | P |
| UAT-42-195-21 | **Audit** | -02 | Read the audit rows | One row per import run with the actor, the row counts (created/updated/rejected) and the correlation id shared with every compensation row it wrote — **and no amounts** | High | P |
| UAT-42-195-22 | **H** | -14, -15, -16 | Show the three empty/partial states to an HR proxy | They can tell "no salary recorded" from "not applicable" from "0%" **without being told**. *If they hesitate, that is a finding, not a training issue* | High | **H** |

### 6.9 KAN-196 — Pay rides inside the position change (R3 · D4) — 21 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-196-01 | Happy | Acme chain configured; `ingrid.makinen` has `compensation:r` | Open the shared move modal from **all three** entry points (org-tree drop, profile, directory `⋯`) | The **same** dialog each time (`templates/org_change/_move_modal.html`), now carrying the compensation block. One modal, one endpoint, one engine (D4f) | High | B |
| UAT-42-196-02 | **Edge** | as -01 | Inspect the compensation block on open | Collapsed, with **nothing pre-selected** — "No change" is not the default. The whole point is that it is an *answer* (D4c) | High | B |
| UAT-42-196-03 | **Adv** | as -01 | Submit with the pay decision **unanswered** | Refused with a named validation error; **no request created**. "Considered" is satisfied by a recorded answer and by nothing less | **Critical** | P+C |
| UAT-42-196-04 | Happy | as -01 | Choose **No change**, submit | Request created carrying an affirmative "no change" decision, and the current salary was shown for context on the way | High | P+C |
| UAT-42-196-05 | Happy | as -01 | Choose **New salary** 75,000.00 EUR FTE 1.0, effective date shared with the placement, reason | Request created; **nothing applied yet** | High | C |
| UAT-42-196-06 | Happy | as -01 | Choose **Defer** with a reason | Request created; a **visible follow-up** exists afterwards — not a silence | High | P+C |
| UAT-42-196-07 | **Edge** | Defer chosen, reason blank | Submit | Refused | Medium | P |
| UAT-42-196-08 | Happy | -05 submitted | Full chain approves | Placement **and** the compensation record apply **atomically**, both on the KAN-189 effective date, in one `transaction()` | **Critical** | P+C |
| UAT-42-196-09 | **Adv** | -05 submitted | **Reject** at level 1 | `status = REJECTED`; **no placement change and no compensation record**. Re-read both — state proven unchanged (Gate D3) | **Critical** | P+C |
| UAT-42-196-10 | **Adv** | Chain has 2 levels | Approve level 1 only | Nothing applied; no compensation row exists yet. Nothing is applied until the final level (`CLAUDE.md` invariant 3, on money) | **Critical** | P |
| UAT-42-196-11 | **Adv** | A chain step's only possible approvers lack `compensation:r` | Submit a **money-bearing** request | **Refused at create time**, naming the step and the missing permission, **writing nothing** (D4b) — not a request that stalls for ever | High | P |
| UAT-42-196-12 | Happy | as -11 | Submit the same change as **placement only**, then a separate `COMPENSATION_REVIEW` | Both permitted. The escape hatch works and is sequential, not parallel (D4b) | High | P |
| UAT-42-196-13 | Perm | A user **without** `compensation:r` opens the modal | Inspect the DOM and the prefill payload | The compensation block is **absent** — not disabled, not blank, not hidden — and the prefill JSON carries **no** current salary (CC-T1). The request they raise is a placement-only `TRANSFER` | **Critical** | P+B |
| UAT-42-196-14 | **Adv** | as -13 | That user POSTs a salary field to `/api/org-change/request` directly | Ignored or `403`; **no pay decision recorded from an unauthorised caller** | **Critical** | P |
| UAT-42-196-15 | **Adv** · D-185-1 | U-01 has BU, FU, location, manager, level, step and a salary | Submit **pay-only** | After apply: BU, FU, location, manager, level and step **all unchanged**; only pay changed. Assert the DB row (CC-T2) | **Critical** | P |
| UAT-42-196-16 | **Adv** · D-185-1 | as -15 | Submit **placement-only** | Salary, level and step unchanged. **No NULL and no zero written over an existing salary** | **Critical** | P |
| UAT-42-196-17 | **Adv** · D-185-1 | as -15 | Submit **level-only** | Placement and salary unchanged | **Critical** | P |
| UAT-42-196-18 | **Adv** · D-185-1 | as -15 | Submit a **full** proposal | Everything the proposal named is overridden; nothing it did not name is touched | High | P |
| UAT-42-196-19 | **Adv** · D-185-1 | U-09 has **no prior compensation record** | Submit a placement-only move | Applies cleanly, creates no empty compensation row, does not crash. *(These five cases are the compensation equivalent of `tests/test_org_change.py::TestApplyCarriesUnchangedFieldsForward` — D4g requires them by name)* | **Critical** | P |
| UAT-42-196-20 | **Tenant** | — | Acme initiator names a **Telia** subject or a Telia approver | `404`, nothing written | **Critical** | P |
| UAT-42-196-21 | **Audit** | -08 | Read the audit rows | Placement and compensation events share **one correlation id**; the compensation diff carries `direction` and `pct_change_band`, **no amount**; the `pct_change_band` bucket matches the actual change (see UAT-42-202-08 for the bucket boundaries) | **Critical** | P |

### 6.10 KAN-197 — Promotion as a request type (R4 · D4e) — 15 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-197-01 | Happy | U-01 at L3.5, promotion-eligible | `ingrid.makinen` raises a promotion to L4.1 with a salary increase | `request_type = PROMOTION`; runs on the **existing** engine and chain; no second engine exists | High | P+C |
| UAT-42-197-02 | **Edge** | as -01 | Change **placement only** in the modal | Type inferred as `TRANSFER` (D4f) | Medium | P |
| UAT-42-197-03 | **Edge** | as -01 | Change **level** | Inferred `PROMOTION` | Medium | P |
| UAT-42-197-04 | **Edge** | as -01 | Change **pay only** | Inferred `COMPENSATION_REVIEW` | Medium | P |
| UAT-42-197-05 | **Adv** | Promotion with pay decision "No change" and **no reason** | Submit | **Refused.** On a promotion, "no change" requires an explicit recorded reason (D4c) — this is R4's whole purpose | High | P |
| UAT-42-197-06 | Happy | as -05 with a reason | Submit and approve fully | Applied: level/step assignment, the recorded "no change" decision, and the audit rows, **atomically** | High | P+C |
| UAT-42-197-07 | Happy | Company configures a different chain for `PROMOTION` | Raise one of each type | Each resolves its own chain | High | P |
| UAT-42-197-08 | **Edge** | **No** chain configured for `PROMOTION` | Raise a promotion | Falls back to the `TRANSFER` chain. **No request ever runs with no chain** | High | P |
| UAT-42-197-09 | **Edge** | No chain configured **at all** | Raise any type | Refused with a named error rather than auto-approving. An empty chain must never mean "approved" | **Critical** | P |
| UAT-42-197-10 | **Adv** | — | An employee raises a `PROMOTION` **for themselves**; then a `COMPENSATION_REVIEW` for themselves | `403` on both. The KAN-139 rule holds for **every** request type — `_can_initiate_for` must be extended, not bypassed | **Critical** | P |
| UAT-42-197-11 | **Adv** | HR_ADMIN raises a `COMPENSATION_REVIEW` **for themselves** | Submit | `403`. Holding HR_ADMIN is not an exemption from not paying yourself | **Critical** | P |
| UAT-42-197-12 | **Adv** | Existing `org_change_requests` rows from EP27/EP38 | After the migration | Every pre-existing row reads `request_type = 'TRANSFER'`; every existing flow behaves identically | High | P |
| UAT-42-197-13 | **Edge** | Promotion **downward** (demotion / correction) | Raise with a mandatory reason | Permitted, audited, applied through the same chain (D3.4) | Medium | P |
| UAT-42-197-14 | **Tenant** | — | Acme promotion proposing a **Telia** job level | `404`, nothing written; the level picker never offered it (UAT-42-194-32) | **Critical** | P |
| UAT-42-197-15 | **Notif** | -06 applied | Check the subject's, requester's and each approver's bell | The **subject is told what happened to them**; the requester gets progress and outcome; decided items retire for every approver. Status vocabulary identical in the list, the dialog, the notification and the timeline (D4 blind-spot items 4, 7, 8, 9) | High | C |

### 6.11 KAN-198 — Four-eyes on money (D4h · backlog open item #5) — 14 cases

*The seeded Acme overlap is the point of this story: level 1 is the **HR_ADMIN role**, level 2 is a **named
approver who also holds HR_ADMIN**, so a chain the company configured as two-level control operates as one-person
control.*

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-198-01 | **Precondition** | Acme chain | Read `org_change_workflow_steps` for Acme | Confirms level 1 = `ROLE`/`HR_ADMIN`, level 2 = `EMPLOYEE`/named, and that the named person holds `HR_ADMIN`. *If the seed has changed, the rest of this section is re-pointed, not skipped* | High | P |
| UAT-42-198-02 | **Adv** | Money-bearing request; `ingrid.makinen` holds HR_ADMIN and is the named level-2 approver | Ingrid approves level 1, then attempts level 2 | **Refused**, with a message **naming the level she already decided**. Request stays at level 2, nothing applied, no second `org_change_approvals` decision row written | **Critical** | P+C |
| UAT-42-198-03 | Happy | as -02 | `uat.hr2` (a different HR_ADMIN, also the level-2 approver) approves level 2 | Applied. Two people, two levels — the control works as configured | High | P+C |
| UAT-42-198-04 | **Adv** | as -02 | Ingrid **rejects** at level 2 after approving level 1 | Also refused. The rule binds **any** second decision, not only approvals | **Critical** | P |
| UAT-42-198-05 | **Edge** | A **level-change** request with no pay change | Same actor at both levels | **Refused** — D4h binds compensation **or level** changes | High | P |
| UAT-42-198-06 | **Edge** | **Placement-only** request | Same actor at both levels | **Allowed**, with a visible warning, and an `audit_log` row recording it as a **self-approval** (D4h option b) | Medium | P+C |
| UAT-42-198-07 | **Adv** | Money-bearing request | `oliver.hartmann` (SYSTEM_ADMIN) satisfies both levels using the bypass at `app/services/org_change_service.py:248` | **Per the ratified rule — currently unspecified, finding UAT-F-09.** Recommended: **the four-eyes rule binds SYSTEM_ADMIN too.** A control with a hole exactly where the demo user sits is not a control | High | P |
| UAT-42-198-08 | **Adv** | Money-bearing request raised by `ingrid.makinen` | Ingrid then approves **level 1** (her only decision) | **Per the ratified rule — finding UAT-F-04, High.** D4h as written permits this, and it is one-person control by another route. Recommended: **on a money-bearing request the initiator may not decide any level** | **Critical** | P |
| UAT-42-198-09 | **Adv** | Ingrid holds both PORTAL_ADMIN and HR_ADMIN and both levels are role steps she satisfies | Approve level 1, attempt level 2 | Refused. The rule is per **user**, never per **role** — satisfying two levels through two different roles is the same person twice | **Critical** | P |
| UAT-42-198-10 | Happy | Chain admin page | Configure level 1 = HR_ADMIN role, level 2 = a named HR_ADMIN | **The overlap is shown at configuration time** — "levels 1 and 2 can both be satisfied by the same person" — when it is cheap to fix (D4h) | High | B |
| UAT-42-198-11 | **Edge** | as -10 | Configure a chain with **no** overlap | No warning shown. A warning that is always on is a warning nobody reads | Low | B |
| UAT-42-198-12 | Regression | EP27 drag-and-drop and EP38 transfer | Run both end to end after KAN-198 | Placement-only behaviour unchanged except the new warning and audit row; **both regression suites extended, none relaxed** | High | B+P |
| UAT-42-198-13 | **Tenant** | — | An approver from Telia attempts to decide an Acme money request | `404`/`403`, nothing written. Approver resolution matches role **by name within the company** (`CLAUDE.md` invariant 6) | **Critical** | P |
| UAT-42-198-14 | **Audit** | -02, -06, -08 | Read the audit trail | The refused second decision is recorded as a **refused attempt** (not silently dropped); the permitted self-approval is recorded as one. An attempted control breach that leaves no trace is a gap | High | P |

### 6.12 KAN-199 — Salary bands and pay markets (D1 basis · D3.5) — 15 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-199-01 | Happy | Acme, L3 | `ingrid.makinen` creates a band for (L3, DE): min 59,500.00, mid 70,000.00, max 80,500.00 EUR, effective today | Saved; compa-ratio displayed to `compensation:r` holders | High | P+B |
| UAT-42-199-02 | **Math** | as -01 | Read the compa-ratio for the F2 amounts | Exactly the F2 table: 0.950000 / 0.9499998… / 0.9500001… / **0.949500** / 1.100000 / 1.1000001… | High | P |
| UAT-42-199-03 | **Edge** | — | min > midpoint; midpoint > max; min = max; all three equal; negative values | Each refused with a named error, nothing written | Medium | P |
| UAT-42-199-04 | **Edge** | Pay markets not configured | Create a band | Refused until a pay market exists, or defaulted to **one market per `locations.country`** — never to a single global market (D1) | High | P |
| UAT-42-199-05 | Happy | Acme has Hamburg (DE), Porto (PT), Tallinn (EE) | Open pay markets | Three markets by default, one per country (D1) | High | P |
| UAT-42-199-06 | **Adv** | — | Merge DE + EE into one market with **no FX rate** | **Refused**, named error, nothing saved. **No silent 1:1** (D1) | **Critical** | P |
| UAT-42-199-07 | Happy | An effective-dated FX rate exists for both currencies | Merge DE + EE | Permitted; the comparison currency is stated on screen | Medium | P |
| UAT-42-199-08 | **Edge** | — | Split a country into two markets | Permitted (PORTAL_ADMIN configuration) | Low | P |
| UAT-42-199-09 | Happy | Band exists | Record a salary **above** the max and **below** the min | **Allowed, flagged, reason required — never hard-blocked** (D3.5). Red-circled pay and market premiums exist, and blocking pushes the decision off-system | High | P+B |
| UAT-42-199-10 | **Edge** | Step target point (a percentile) set | Read it | Guidance only — **never enforced, never auto-applied** to a salary | Medium | P |
| UAT-42-199-11 | Perm | `compensation:r` only | Attempt to edit a band | `403`, no state change | High | P |
| UAT-42-199-12 | Perm | EMPLOYEE with `compensation_self` | Open "My Pay" where a band exists | Position in range as a **plain-language statement**, no raw compa-ratio, no comparison to anybody else, no forward-looking language (D5.5) | High | B+H |
| UAT-42-199-13 | **Adv** | A17 | No band exists; the same employee opens "My Pay" | **No position-in-range at all** — never derived from the live group median, which is invertible in a small group | High | P |
| UAT-42-199-14 | **Tenant** | — | Acme band list; then Acme HR_ADMIN `PUT`s a Telia band UUID | Only Acme bands listed; `404` on the substitution; nothing written | **Critical** | P |
| UAT-42-199-15 | **Audit** | -01, -09 | Read the audit rows | `PAY_BAND_CHANGED` present; before→after of the band's **structure**; the out-of-band flag and its reason recorded; **no employee amount in the diff** | High | P |

### 6.13 KAN-200 — The pay-equity comparison engine (R5 · D1) — 34 cases

*Every `Math` case below has its expected value written out in §5. The tester checks the engine against the paper.
All comparisons are `Decimal` to `Decimal` (CC-T3); `pytest.approx` is banned in this section.*

| ID | Type | Fixture | Steps | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-200-01 | **Math** | F1 | Run the equity check | Group median **63,000.00**; ratios 0.8571 / 0.9524 / 1.0000 / 1.0476 / 1.1429; **exactly 2 OPEN flags** (U-05, U-04) | **Critical** | P+R |
| UAT-42-200-02 | **Math** | F1 | Count the comparisons performed | Each employee compared **once against the group**, never pairwise. A pairwise engine on n=5 does 10 comparisons and produces duplicate findings about one person (D1) | High | R |
| UAT-42-200-03 | **Math** | F2-a | Compa-ratio exactly **0.950000** | **No flag.** The rule is *below* 0.95 | High | P |
| UAT-42-200-04 | **Math** | F2-b / F2-c | 0.9499998… / 0.9500001… | **Flag / no flag** | High | P |
| UAT-42-200-05 | **Math** | **F2-d** | Amount 66,465.00 against midpoint 70,000.00 (ratio **0.949500**) | **Flag.** An engine that rounds the compa-ratio to 2 dp before comparing gets 0.95 and **loses this flag silently**. This case exists to catch exactly that | **Critical** | P |
| UAT-42-200-06 | **Math** | F2-e / F2-f | 1.100000 / 1.1000001… | **No flag / flag** — the upper boundary is *above* 1.10 | High | P |
| UAT-42-200-07 | **Math** | F3-a | Gender gap exactly **5.00%** | **Flag** (threshold is ≥) | **Critical** | P |
| UAT-42-200-08 | **Math** | F3-b | **4.95%** | No flag | High | P |
| UAT-42-200-09 | **Math** | F3-c | **5.05%** | Flag | High | P |
| UAT-42-200-10 | **Math** | F3-d | **0.01%** | No flag, and the **displayed** value is `0.01%` — not rounded to `0%`, which would read as "no gap" | Medium | P |
| UAT-42-200-11 | **Math** | F2 group with a deliberately misleading group median | Run | Where a band exists the basis **is the band midpoint**, not the median. Assert the reported basis label as well as the number | High | P+R |
| UAT-42-200-12 | **Math** | F1 (no band) | Run | Basis falls back to the **group median** — and to the median, never the mean. Add one 200,000.00 salary to F1 and assert the median moves to 66,000.00 while a mean would move to 89,166.67 and hide U-05 | **Critical** | P |
| UAT-42-200-13 | **Math** | F9 (n=4) | Run | Median = **(64,000.00 + 68,000.00)/2 = 66,000.00**; 2 flags; **assert the reported gap values**, since a lower-middle implementation gives the same flag count with different numbers | High | P |
| UAT-42-200-14 | **Math** | F10 (n=2, statistics surface) | Read the group median | **70,000.01** under HALF_UP. **Blocked until UAT-F-01 (rounding mode) is ratified** — the case is written and must not be run against a guess | Medium | P |
| UAT-42-200-15 | **Math** | F4-a (n=1) | Run | **No flag.** "Insufficient comparison group", reported in the coverage view, no notification | **Critical** | P |
| UAT-42-200-16 | **Math** | F4-b (n=2, 42.9% spread) | Run | **No flag.** A large spread correctly not flagged is what proves the minimum is honoured | **Critical** | P |
| UAT-42-200-17 | **Math** | F4-c (n=3) | Run | Check A evaluated, 1 flag; Check B **not** evaluated (n<5) | High | P |
| UAT-42-200-18 | **Math** | F4-d / F4-e | Single-gender group; 4+1 group | Check B **not** run; the message is "insufficient comparison group for the gender gap check", **distinct from** "no gap found" | High | P |
| UAT-42-200-19 | **Math** | F3-e | Female median above male median by 5.26% | **Blocked on finding UAT-F-02.** Written against the recommended default: flag on `|gap| ≥ threshold` with the direction recorded | High | P |
| UAT-42-200-20 | **Edge** | Gender `OTHER` and gender `NULL` present in a group | Run Check B | **Unspecified in Wave 1 — finding UAT-F-10.** Recommended: excluded from the two compared medians, **counted and shown** as an exclusion, never silently folded into a binary | High | P |
| UAT-42-200-21 | **Math** | F5-a / F5-b / F5-c | Coverage 78% / 80% / 82% | Not evaluated / **evaluated** / evaluated. Message on the first: "insufficient coverage — not evaluated (78% of 50)" | **Critical** | P+R |
| UAT-42-200-22 | **Math** | **F5-d** | Coverage **79.59%**, which displays as 80% | **Not evaluated.** An engine that gates on the rounded display value evaluates this group and emits flags it must not emit | **Critical** | P |
| UAT-42-200-23 | **Edge** | F5-e (0%) | Run | Not evaluated; the group shows the coverage meter and a route to record salaries — **never** "no findings ✓" | **Critical** | P+B |
| UAT-42-200-24 | **Edge** | A company that has never crossed the gate | Open the equity queue | **Coverage meter and missing list only. No "no findings" state exists on this screen at all** (D7.4). Asserted on the rendered text | **Critical** | B |
| UAT-42-200-25 | **Math** | **F7** | 0.6 FTE at 42,000.00 in an otherwise-70,000.00 group | Normalised value **exactly `Decimal('70000.00')`**; every ratio exactly `1.0000`; reported gap exactly `Decimal('0.00')`; zero flags. **A float implementation returns 70000.00000000001 and fails this case** | **Critical** | P |
| UAT-42-200-26 | **Edge** | F7 | Read U-06's displayed salary | **42,000.00** — their actual pay. The 70,000.00 normalised figure is a comparison basis and must never be shown as their salary | High | P+H |
| UAT-42-200-27 | **Math** | F8-a…F8-f | Annualisation across annual / monthly / hourly, two companies' standard hours, and combined with FTE | Exactly 70,000.00 / **69,999.96** / **69,999.90** / **57,884.54** / **70,000.08** / **116,666.50**. No "tidying" to round numbers; annualise **then** normalise | **Critical** | P |
| UAT-42-200-28 | **Math** | F12 | Run | `6 compared / 9 in group · 2 not applicable · 1 no record · coverage 85.71%`. **All five numbers asserted** — contractors and interns are out of the denominator, missing records are in it | **Critical** | P |
| UAT-42-200-29 | **Adv** | F12 | Read the exclusion display | Exclusions are **counted and shown**, never silent (D1) | High | P+B |
| UAT-42-200-30 | **Math** | **F6** | Hamburg and Tallinn at the same level | **Two groups, two medians (63,000.00 / 34,000.00), exactly 2 flags total.** An engine that omits `pay_market` produces a combined median of 46,000.00 and **six wrong findings** — the first wrong finding is the one that ends the feature's credibility | **Critical** | P+R |
| UAT-42-200-31 | **Math** | F11 | n=3 with the subject at 90,000.00 | Reported ratio **1.7308** / gap **+73.08%** (subject included in their own group median). **Blocked on UAT-F-01c**; a flag-count assertion cannot distinguish the two implementations, so the case asserts the number | High | P |
| UAT-42-200-32 | Perm | — | Run "Run equity check" as: HR_ADMIN, PORTAL_ADMIN (allowed); EMPLOYEE, SOLID_LINE_MANAGER, DEPARTMENT_HEAD (denied) | Gated `@require_feature_access('pay_equity')` only. Thresholds, group minimums, the coverage gate and the pay-market definition are editable by **PORTAL_ADMIN only**; HR_ADMIN gets `403` on those | High | P |
| UAT-42-200-33 | **Tenant** | Acme and Telia both have an L3 group | Run the check in Acme | **Zero Telia employees in any Acme group**, no cross-tenant median, no cross-tenant flag, and a SYSTEM_ADMIN "All Companies" run produces **no combined group** (A08, §3.3) | **Critical** | P+R |
| UAT-42-200-34 | **Audit** | -32 | Change a threshold, the coverage gate and a pay-market definition | `PAY_EQUITY_THRESHOLD_CHANGED` rows with before→after, actor, reason, correlation id; and each change **re-opens** the affected groups for re-evaluation (D2's re-fire trigger (c)) | High | P |

### 6.14 KAN-201 — Flag delivery, the bell, and the lifecycle (R5 · D2) — 26 cases

*The D4 blind-spot list is executed here in full, with content assertions. This is the section that would have
caught DEF-001, DEF-002 and DEF-003 before a stakeholder did.*

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-201-01 | Happy | F1 run; 2 OPEN flags | `ingrid.makinen` opens `/compensation/equity` | Queue lists both flags with subject, level, pay market, group size, basis, measured gap, threshold, raised date, state, owner. Filters by state, group and age work | High | B |
| UAT-42-201-02 | **Notif** · D4-1 | as -01 | Open the bell | A **"Pay Equity" section** exists, placed after "Position Changes" and before "My Notifications" (`templates/base.html:290-320`), listing the flags **with their "Review →" action** — not read-only text | **Critical** | B |
| UAT-42-201-03 | **Notif** · D4-2 | as -01 | Read `#bell-badge` before and after the run | The badge **includes** the OPEN flags visible to this user. A badge that stays silent about work waiting is work nobody does | **Critical** | B |
| UAT-42-201-04 | **Notif** · D4-3 | as -01 | Read the icon on the flag item | **⚖️** from `NOTIF_ICON` (`templates/base.html:608-624`). **Never ❌** — a standing condition has no outcome and must not wear one (DEF-002). Assert the exact character | **Critical** | B |
| UAT-42-201-05 | **Notif** · D4-3 | — | Introduce an unknown EP42 event type | Falls back to the neutral **🔔**, never to ❌ | High | P |
| UAT-42-201-06 | **Notif** · D4-10 | as -01 | Click "Review →" | Deep-links to the queue **filtered to that flag**; the flag is visible without further searching; a stale link does not open a dead dialog | High | B |
| UAT-42-201-07 | **Notif** | as -01 | Inspect the bell for a dispose control | **There is none.** Disposition happens in the queue with a recorded reason — the same reasoning as `templates/base.html:639-641`, where reject is a deep link because a decision without a reason is not auditable | High | B |
| UAT-42-201-08 | **Adv** · A13 | as -01 | Read the notification body in the DOM **and** in `/api/my-notifications` | No amount, no currency figure, **no percentage that can be inverted to an amount**, no compa-ratio, no band. Names the subject, the group, and that a threshold was exceeded (D2) | **Critical** | P+B |
| UAT-42-201-09 | **Notif** · D4-5 | No OPEN flags for this user | Open the bell | The Pay Equity section is **hidden entirely** — never an empty "no findings ✓", which at 40% coverage reads as "we are fine" (D2, D7.4) | **Critical** | B |
| UAT-42-201-10 | **Notif** · D4-4/6 | Three eligible recipients: `ingrid.makinen`, `uat.hr2`, `uat.hr3` | Ingrid dispositions the flag `JUSTIFIED` with a reason and a category | The call to action **retires in all three bells** and the badge decrements for all three — **not only for the one who acted**. This is DEF-003's actual defect, asserted across three recipients | **Critical** | C |
| UAT-42-201-11 | **Notif** | as -10 | `uat.hr2` opens the bell and the queue and dispositions nothing | The item is **still there with its Review action**; the badge is unchanged. **Reading is not deciding** (D2) | **Critical** | C |
| UAT-42-201-12 | **Notif** · D4-7 | as -10 | Check the **subject's** bell and `/api/my-notifications` | **Nothing.** The subject of a pay-equity flag is not a recipient, and telling them would be a disclosure the model does not permit | **Critical** | P+C |
| UAT-42-201-13 | Perm | A user **without** `pay_equity` | Open the bell and `/compensation/equity` | No Pay Equity section, no badge contribution, route denied. Section gated `{% if has_feature_access('pay_equity') %}` — **feature-gated, never role-gated**; the existing role-gated "Pending Approvals" section is explicitly **not** the pattern to copy (D2, `CLAUDE.md`) | **Critical** | P+B |
| UAT-42-201-14 | Perm | Company names 2 escalation recipients who hold **no** `pay_equity` | Raise a flag | They are notified **in addition to** the matrix holders | High | P |
| UAT-42-201-15 | **Adv** | as -14 | Configure the escalation list to a subset and check the matrix holders | **The named list can never remove access from anybody the matrix grants.** A list that could deny is the `enabled_for_hr` mistake wearing a different hat (D2, `CLAUDE.md`) | **Critical** | P |
| UAT-42-201-16 | Happy | OPEN flag | Disposition `JUSTIFIED` with a category and reason | State changes; reason and category stored; audited | High | P+C |
| UAT-42-201-17 | **Adv** | OPEN flag | Disposition with a **blank** reason, and with a category but no reason | Refused both. **No one-click dismiss anywhere in the product** (D2) | High | P |
| UAT-42-201-18 | **Adv** | Several OPEN flags | Attempt bulk disposition through the UI and by API | **Not offered, and refused by the API.** Bulk disposition is one-click dismiss at scale | High | P |
| UAT-42-201-19 | Happy | `REMEDIATION_PLANNED` | Disposition without an owner or a target date | Refused; both mandatory (D2) | Medium | P |
| UAT-42-201-20 | **Edge** · the standing-condition case | Flag `JUSTIFIED`; **the underlying gap still exists**; re-run the check | **No new flag, no new notification.** The flag remains visible in the **register** as `JUSTIFIED` — it does not disappear, because the condition has not gone away. *This is the hard case the SPM flagged: dismissing the notification must not dismiss the condition* | **Critical** | P+R |
| UAT-42-201-21 | **Edge** | as -20 | Run "Run equity check" **five times in a row** with no data change | Exactly **one** flag row and **one** notification per recipient still exist. No duplicates, no re-fire, no storm. *This is the case that decides whether HR mutes the channel (risk R-1)* | **Critical** | P+R |
| UAT-42-201-22 | **Edge** | `JUSTIFIED` with a 12-month window, raised 2026-08-09 | Re-run on 2027-08-07, 2027-08-08 and 2027-08-10 (clock controlled) | Day 363 and day 364: no re-fire. Day 366: **re-fires**. The window end itself (day 365) is **Blocked on UAT-F-01b** — inclusive or exclusive is unspecified; recommended **inclusive** (no re-fire on the last day) | High | P |
| UAT-42-201-23 | **Math** | `JUSTIFIED`, threshold 5%, delta +2pp | Widen the gap to **6.99%**, **7.00%**, **7.01%** and re-run | No re-fire / **Blocked on UAT-F-01b** ("beyond threshold + 2pp" — recommended strictly greater, so 7.00% does **not** re-fire) / **re-fires** | High | P |
| UAT-42-201-24 | **Edge** | `JUSTIFIED` inside its window | Change the subject's step; separately change their salary; separately change the company threshold | **Re-fires in all three cases** (D2 triggers a, b, c) | High | P |
| UAT-42-201-25 | **Edge** | OPEN flag; a pay change closes the gap | Re-run | Auto-resolves as `RESOLVED_BY_DATA`; the notification retires for every recipient via `resolve_related()` with `related_type='pay_equity_flag'` (the DEF-003 mechanism) | High | P+C |
| UAT-42-201-26 | **Tenant** | Flags exist in both tenants | Acme HR_ADMIN opens the queue and the bell; then substitutes a **Telia** flag UUID into the disposition endpoint | Only Acme flags listed and counted in the badge; `404` on the substitution; **nothing written**; Telia's flag state unchanged | **Critical** | P+B |

### 6.15 KAN-202 — Compensation history and the audit coupling (D5.6) — 16 cases

| ID | Type | Preconditions | Steps (as whom) | Expected result | Sev | Auto |
|---|---|---|---|---|---|---|
| UAT-42-202-01 | Happy | U-01 has 3 records | `ingrid.makinen` opens the timeline | Effective date, amount, currency, FTE, level/step, actor and reason per row, in date order, with the current row marked and future rows marked as future | High | P+B |
| UAT-42-202-02 | Happy | as -01 | Join to `audit_log` by `correlation_id` | Each compensation row pairs with its audit row; the two read as one story (D5.6) | High | P |
| UAT-42-202-03 | **Adv** | Hold `audit_log:r`, **not** `compensation:r` | Read every EP42 audit row through every audit surface | **No amount anywhere.** Access control that can be routed around through a second feature is not access control (D5.6, S10) | **Critical** | P |
| UAT-42-202-04 | **Adv** | — | Call `audit_service.record()` with `after_state={'annual_base': 70000}` — and with `salary`, `pay`, `compensation`, `amount`, `wage`, `remuneration`, `base_pay`, `new_salary_eur`, `Annual_Base` | `AuditError` on **every** one, matched case-insensitively as a substring exactly like `_SECRETISH_KEYS` (`app/services/audit_service.py:95-98`). Nothing written | **Critical** | P |
| UAT-42-202-05 | **Adv** · A15 | — | Record a compensation change with the mandatory reason `"raise to 82000 from 70000"` | **Finding UAT-F-03, High.** `_MONEYISH_KEYS` matches **keys**, not values, so today this amount lands in `audit_log.reason` and is readable by `audit_log:r` holders. The case is written against the resolved rule; **as written the AC is unenforceable** | High | P |
| UAT-42-202-06 | **Adv** | — | Attempt a nested diff `{'comp': {'amount': 70000}}` | Refused — a diff is a flat `field → scalar` mapping (`audit_service._clean_diff`), which is how a whole row gets smuggled in | High | P |
| UAT-42-202-07 | Happy | — | Read the diff of a compensation change | `has_change`, `direction` (`INCREASE`/`DECREASE`/`NONE`), `pct_change_band`, `currency`, `effective_date`, `level_from`/`level_to`, `step_from`/`step_to` — and nothing else | **Critical** | P |
| UAT-42-202-08 | **Math** | Buckets `0-5`, `5-10`, `10-20`, `20+` | Changes of exactly **0.00%, 4.99%, 5.00%, 9.99%, 10.00%, 19.99%, 20.00%, 20.01%, −7.00%** | The bucket boundaries are **unspecified (inclusive at which end?) and the negative case is undefined — finding UAT-F-11**. Recommended: half-open `[0,5) [5,10) [10,20) [20,∞)` on the **absolute** percentage, with `direction` carrying the sign. **Also assert the bucket is coarse enough not to be invertible** when combined with a known previous amount | High | P |
| UAT-42-202-09 | **Adv** | Actor knows the previous amount | Combine `pct_change_band` + `direction` + `currency` with the known previous amount | The new amount can only be bounded to a range, never derived. *If the bucket were 1pp wide this control would be decorative* | High | P+H |
| UAT-42-202-10 | Happy | New actions | Read `audit_service.ACTIONS` | All eleven EP42 codes registered (`COMPENSATION_RECORDED`, `COMPENSATION_CHANGED`, `COMPENSATION_VOIDED`, `JOB_LEVEL_ASSIGNED`, `JOB_LEVEL_CHANGED`, `STEP_ADVANCED`, `PROMOTION_APPLIED`, `PAY_BAND_CHANGED`, `PAY_EQUITY_FLAG_RAISED`, `PAY_EQUITY_FLAG_DISPOSITIONED`, `PAY_EQUITY_THRESHOLD_CHANGED`); the enumeration's **shape** is unchanged (S8) | Medium | P |
| UAT-42-202-11 | **Adv** | — | Attempt to `UPDATE` an EP42 `audit_log` row | Refused by the append-only DB trigger (KAN-187) | High | P |
| UAT-42-202-12 | Perm | Manager with scoped `compensation:r` | Open the timeline of a direct report, then of a non-report | Allowed / `403`. The timeline is a **compensation** surface, row-scoped like every other | **Critical** | P |
| UAT-42-202-13 | Perm | Employee with `compensation_self` | Open their own timeline | Per the tenant setting (default: **current only, no history**) — and never anybody else's | High | P |
| UAT-42-202-14 | **Tenant** | — | Acme HR_ADMIN requests a Telia employee's timeline and a Telia `audit_log` row | `404` on both, nothing read | **Critical** | P |
| UAT-42-202-15 | **Edge** | Employee offboarded / erased under EP38 R3.6 | Read the timeline | Per **CFL-42-3** — EP38's erasure enumeration predates compensation and does not mention pay. **Blocked on the BA's resolution**; the case asserts whichever rule is chosen, and the *absence* of a rule is itself the finding | High | P |
| UAT-42-202-16 | **Audit** | — | Read the `retention_class` on every EP42 audit row | Set deliberately (`EMPLOYMENT` expected), not defaulted to `STANDARD` by omission. Retention of pay history past exit is a legal question, not a default | Medium | P |

---

## 7. Automation plan — what runs where, and what a machine cannot prove

### 7.1 New and extended `pytest`

Built by the implementing engineer with me, story by story, in the same commit as the story.

| File | New / extended | Covers | Depends on |
|---|---|---|---|
| `tests/test_company_feature_switch.py` | **new** | KAN-188 in full, including the **no-behaviour-change matrix** (UAT-42-188-12) as a parametrised table over 11 features × 3 tenants × 10 roles | — |
| `tests/test_compensation_record.py` | **new** | KAN-193: append-only, no UPDATE/DELETE path, effective dating, boundary day, window bounds, atomicity via `FakeTransaction` / `assert_single_atomic_unit` (`tests/conftest.py:46-64`) | KAN-155 |
| `tests/test_compensation_visibility.py` | **new — the negative-visibility suite** | KAN-194 §6.7 in full. Parametrised over **role × subject-relationship × surface**, asserting **absence from the response body** (CC-T1). This is the file the SPM called my highest-value contribution and it is the one I would refuse to ship without | KAN-193 |
| `tests/test_pay_equity_math.py` | **new** | §5 F1–F12 as pure-function tests with hand-computed `Decimal` expectations. No DB, no mocks of the maths, no `approx` | — |
| `tests/test_pay_equity_engine.py` | **new, real-DB tier** | Group formation, medians, coverage gates, exclusion counting, the re-fire rule, the five-runs-no-storm case. **Cannot be verified against mocks** (DEP-4 / KAN-168) | KAN-168 |
| `tests/test_org_change.py` | **extended** | `request_type`, the mandatory pay decision, the five D-185-1 proposal shapes as a compensation sibling of `TestApplyCarriesUnchangedFieldsForward` (line 302), four-eyes in `TestDecideEngine` | KAN-196/197/198 |
| `tests/test_audit_service.py` | **extended** | `_MONEYISH_KEYS` refusals (UAT-42-202-04), the eleven new `ACTIONS`, the flat-diff refusal, the retention class | CFL-42-2 |
| `tests/test_regression.py` | **extended** | `TestFeatureRegistryHasNoDrift` must fail if any of the three EP42 codes is registered in a migration but missing from `seed_rbac.sql` (the DEF-004 trap) — **verified by deliberately breaking it once before the story is accepted**, exactly as DEF-004's fix was | — |
| `tests/test_company_scoping.py` | **extended** | CC-T5: the tenant-substitution matrix over every EP42 endpoint, enumerated | — |
| `tests/fixtures/ep42_uat_seed.py` | **new (mine)** | The §1.4 cohort, idempotent and re-runnable | — |

### 7.2 Browser suites (mine)

| Suite | Change |
|---|---|
| `tests/ui/test_browser.py` | **Repairs** to §17 and §18 (see §8) plus **three new sections**: §19 *Compensation visibility in the DOM* (the CSS-hidden check, the absent block for an unprivileged user, the two empty states), §20 *Pay-equity bell content* (the full D4 ten, content-asserted), §21 *Tenant switch off-state* (direct URL, API, nav, SYSTEM_ADMIN signposting) |
| `tests/ui/test_vacation_workflow.py` | Defensive scoping only (see §8.2). No vacation behaviour changes in EP42 |
| `tests/ui/test_compensation_workflow.py` | **New suite, modelled on `test_vacation_workflow.py`.** The full round trip: record → position change with a pay decision → level-1 approve → four-eyes refusal at level 2 → second approver approves → apply → timeline → equity check → flag raised → bell across three recipients → disposition → retirement across all three. **Idempotent**, with a marker-based reset of only its own fixture rows, in the shape of `reset_test_employee_leave()` (`test_vacation_workflow.py:104-137`) — and because compensation history is append-only, the reset deletes by correlation id and **never** by relaxing the append-only constraint |

**On counts.** Test counts go stale between commits (Charter §5b rule 3), so I am not promising a number. The
current recorded baseline is browser 93 / vacation 39; after EP42 the browser suite is materially larger and there
is a third suite. The number to report is always the one the command prints.

### 7.3 What a human must walk in a visible browser — and why a green assertion would not do

These are not "hard to automate". They are cases where **the assertion I could write would pass while the user was
misled**, which is the failure mode this whole plan exists to prevent.

| # | Case | Why automation cannot prove it |
|---|---|---|
| H1 | UAT-42-193-15 / 195-22 — **"No salary recorded" vs "Not applicable — Contractor" vs "0% coverage"** | I can assert the strings differ. I cannot assert an HR admin can *tell them apart at a glance* under time pressure. The defect is indistinguishability, and it is invisible to `assert text == …` |
| H2 | UAT-42-192-06 — **the promotion-eligible wording** | A signal that reads as a promise is a promise. Only a human reader can judge that sentence, and the SPM already called it the most easily misread sentence in the epic |
| H3 | UAT-42-199-12 — **"My Pay" copy** | Same class: no jargon, no comparison, no forward-looking language. Assertable only as "these words are absent", which does not prove the words present are right |
| H4 | The **modal-weight constraint** (D4f) — the no-change path costs one deliberate click and no extra scroll | Click counts are automatable; *felt* weight and "did the common case get worse" are not. UX owns the design; UAT owns proving a real manager still completes it |
| H5 | UAT-42-200-26 — **an FTE-normalised figure never presented as pay** | An automated check can look for the number; only a person can spot a label that makes the right number mean the wrong thing |
| H6 | **WCAG 2.2 AA spot checks** — keyboard operation of the disposition dialog, focus management on the modal, screen-reader labels on the coverage meter, no colour-only status on flag state | Automatable in part; the judgement half is not |
| H7 | UAT-42-202-09 — **is `pct_change_band` coarse enough** | Arithmetic is automatable; whether the residual inference is acceptable is a privacy judgement |
| H8 | **The A-2 disclosure** — under demo auth the visibility matrix is correct in code and unenforceable in practice | Nothing in a test suite can say this out loud. It has to be in the demo script and said by a person |
| H9 | **The flow test itself** | Per `CLAUDE.md`, a flow test is a **visible browser session with spoken narration** and it is successful **only when the user explicitly approves it**. A headless suite run is not a flow test, and I never declare one successful |

---

## 8. Impact on the two regression suites I own

**This is the section that stops EP42 from being "merged, suites green, three checks quietly relaxed".** Line
numbers are against the files as they stand today.

### 8.1 `tests/ui/test_browser.py` — what EP42 changes or breaks

| Lines | Check | What EP42 does to it | My response |
|---|---|---|---|
| **748-764** | §18 raises a real position change with `POST /api/org-change/request` carrying only `{employee_id, business_unit_id, reason}` | **This will start failing the day KAN-196 lands.** The pay decision becomes **mandatory to answer**, so this payload is refused and the whole of §18 collapses with "could not raise a position change to test the bell with" | **Extend, do not relax.** Add `pay_decision: 'NO_CHANGE'` to the payload **and add a new check that the same POST *without* it is refused** — the mandatory-answer rule then has a regression test where it broke one. This is the single most likely EP42 regression-suite failure and it is a **stale assertion**, not a product defect |
| **775-780** | `badge != '0'` — the bell badge counts an approval awaiting me | Pay-equity flags also enter the badge (D2), so a non-zero badge no longer proves a position change is in it | Tighten to assert the **Position Changes section's own count**, and add a separate assertion for the Pay Equity contribution. A badge assertion that passes for the wrong reason is how DEF-001 survived |
| **785-791** | `#bell-oc-hdr` visible and the subject listed | A **fourth bell section** appears between Position Changes and My Notifications | Keep; add `#bell-pe-hdr` checks and an **ordering** assertion, because "after Position Changes, before My Notifications" is a stated requirement (D2) and nothing asserts section order today |
| **793-801** | Approve control present; Reject deep-links with `review=<id>&action=reject` | Unchanged by EP42 — but the money-bearing equivalent must **not** offer quick-approve without the amount being visible to that approver (D4b) | Add a case: an approver lacking `compensation:r` never sees a quick-approve on a money-bearing request |
| **806-817** | DEF-002 — undecided request shows ⏳, scoped to our subject | The scoping comment at 806-810 is the right pattern and EP42 must copy it for flags | Keep verbatim; reuse the pattern in §20 |
| **819-866** | Reject → retirement → outcome ❌ | Unchanged, but KAN-198 may refuse the second decision by the same actor | The suite rejects at level 1 as one actor, so it survives; **add** an explicit four-eyes case rather than relying on that |
| **646-720** | §17 Transfer… entry point; `#mv-title == "Request Position Change"` (682, 705); `#mv-chain` non-empty (707) | KAN-197 infers the request type, so the title may become type-dependent; KAN-189 adds an effective-date field; KAN-196 adds the compensation block | **Extend**: assert the title for each inferred type, assert the effective-date field exists (it is deliberately absent today and silently discarded — KAN-189), assert the compensation block's presence/absence by permission. **Do not** loosen the title assertion to a substring — that is exactly how a status-vocabulary drift gets through |
| **556-562** | Plain employee has no Transfer… entry point on their own profile | Still true, and now needs a sibling | **Add**: the same employee sees **no compensation block, no other person's pay, and no "Record salary" action** on any profile |
| **155-171** | Nav link loop | EP42 adds nav items that must be feature-gated **and** tenant-switch-gated | Add the EP42 rows for a tenant where it is on, and a negative case for a tenant where it is off |
| **419-434** | Directory content | CFL-42-4 may make the **level title** the displayed job | Re-point when CFL-42-4 is resolved; the assertion must name which title it expects and why |
| **631-641** | Unauthenticated redirect loop | New EP42 routes must be in it | Add every EP42 route to `protected` |

### 8.2 `tests/ui/test_vacation_workflow.py`

EP42 changes no vacation behaviour, but it changes the **bell the vacation suite reads**.

| Lines | Check | Risk | My response |
|---|---|---|---|
| **305-330** | Manager bell badge shows a count | If the manager also holds `pay_equity`, the badge total now includes flags, so `count > 0` can pass for the wrong reason and a genuine vacation-badge regression would hide behind it | Assert the **vacation section's own count**, not the badge total |
| **336-356** | `bell_text` contains the employee name or "request" | The dropdown text now includes a Pay Equity section; a loose substring match could be satisfied by unrelated content | Scope the assertions to `#bell-list` / `#bell-notif-list` rather than the whole `.bell-dropdown` |
| **104-137** | `reset_test_employee_leave()` | Not affected — and it is the model the new compensation suite copies | Reference it; do not touch it |

### 8.3 `pytest` files EP42 will break (engineer-owned, named here so nobody is surprised)

`tests/test_org_change.py::TestCreateRequest::test_create_inserts_and_notifies` (the `create_request()` signature
gains `effective_date` and the pay decision — KAN-189/196) · `TestApplyCarriesUnchangedFieldsForward` (line 302 —
gains a compensation sibling; the existing five must stay green **unchanged**) · `TestDecideEngine` (four-eyes) ·
`tests/test_regression.py::TestFeatureAccessEnforcement` and `TestAccessControlInvariants` (the resolver in
`app/auth.py:38-95` changes shape under KAN-188) · `tests/test_access_matrix.py` and `test_permission_matrix.py`
(three new codes) · `tests/test_transfer_entry_point.py` (`CURRENT_PLACEMENT` / `route_query` are imported by
`test_org_change.py:12`, so a placement-shape change ripples).

**The rule I will hold on all of them, from `CLAUDE.md` and my own role file: never delete a check to go green.**
A failing suite gets the specific flow driven in a browser and a decision recorded — real regression (fix the
product) or genuinely stale assertion (correct it, and **say in the commit message which one and why**).

---

## 9. Demo Readiness Gate pack for EP42

**Gate verdict for any compensation demo is CONDITIONAL on the A-2 disclosure being in the written script. Without
that line the verdict is NO-GO, and I will hold it** (SPM §8.4.8). I own D2, D3 and D7.

### 9.1 D2 — every actor walked (mine)

Not "the role that makes the demo look good". Every one of these, with a named user and a screenshot:

| Actor | Named user | What they must be shown doing |
|---|---|---|
| **Initiator** | `liisa.virtanen` (solid-line manager) | Raises a position change for `sven.becker` **with** a pay decision |
| **Approval level 1** | `ingrid.makinen` (HR_ADMIN by role) | Approves level 1 |
| **Approval level 2 — the same person** | `ingrid.makinen` | **Attempts level 2 and is refused by name** (KAN-198). This is a *demo step*, not an edge case |
| **Approval level 2 — a different person** | `uat.hr2` | Approves; the change applies |
| **The subject** | `sven.becker` | Sees "My Pay" — their own record only — and is told what happened to them |
| **A bystander who must NOT see it** | `tonis.rebane` | Opens the subject's profile: **no amount, and the payload is shown to be empty** (not merely the screen) |
| **The pay-equity responsible** | `uat.hr3` | Works the queue, dispositions with a reason |
| **A second eligible recipient** | `ingrid.makinen` | Shows the flag **leaving her bell** although she did not act (DEF-003) |
| **A tenant without the feature** | `maria.andersson` (Telia) | Direct URL → the off-state screen (R7 proven, not asserted) |
| **The product owner** | `oliver.hartmann` | Toggles the tenant switch and shows the consequence immediately |

### 9.2 D3 — both outcomes, in the same session (mine)

Every one of these is demonstrated **with the state proven unchanged afterwards** by re-reading the record:

reject a money-bearing request at level 1 → no placement change **and no compensation record** ·
the four-eyes refusal (above) · the create-time refusal when a chain step has no approver holding
`compensation:r` (D4b) · an import preview abandoned → nothing written · an import row that would zero a salary →
**rejected at preview** · a group below n≥3 → "insufficient comparison group", no flag · a group below the coverage
gate → "insufficient coverage", zero flags · a disposition attempted with a blank reason → refused · a cross-tenant
UUID substitution → nothing · the feature switched off mid-demo → the next request is refused.

### 9.3 D7 — automated evidence (mine)

`pytest` 0 failures · `python tests/ui/test_browser.py` 0 failures · `python tests/ui/test_vacation_workflow.py`
0 failures · `python tests/ui/test_compensation_workflow.py` 0 failures — **and the specific assertions covering
each demoed behaviour named in the gate record.** The second half is the one that failed on 9 Aug 2026. For this
epic the named assertions are, at minimum: UAT-42-194-27 (absence from the payload), UAT-42-198-02 (the four-eyes
refusal), UAT-42-201-02/03/04/10/11 (the bell's content, badge, icon and retirement across three recipients),
UAT-42-200-30 (pay markets not merged) and UAT-42-196-15…19 (the five D-185-1 shapes). **A passing assertion that
does not touch the demoed behaviour is not coverage.**

### 9.4 The other checks, and who owns them

D1 story truth — **BA** · D4 feedback surfaces — **UX**, against §6.14 · D5 access & tenancy — **Architect**, the
five `CLAUDE.md` checks answered with the query or route that proves each · D6 state & rehearsal — **Delivery** ·
D8 documentation truth — per Charter §5b · D9 demo script — **SPM**.

### 9.5 D6a — the concurrent-writer and demo-data problem, stated before the demo starts

The dev database is shared and other actors write to it. For a compensation demo:

1. **Use the `uat.` fixture cohort only.** Never demo on `sven.becker`'s real seeded record if anything else is
   running — and say which subjects are in use at the start.
2. **Pay-equity flags are computed from the whole group**, so another actor recording a salary mid-demo can change
   a median and a verdict **live**. The equity demo therefore uses a fixture group nobody else touches, and the
   presenter says so out loud before running the check.
3. **Compensation history is append-only**, so a demo cannot be "cleaned up" by deleting rows. Rehearse on a
   restorable snapshot, or on fixture employees created for the run.
4. **Say the known limitations out loud at the start**, per gate rule 5 and SPM A-2: *the permission model is
   correct in code and unenforceable under demo auth, because identity is self-asserted from the login tiles*; and
   *every figure shown is synthetic*.

---

## 10. Findings raised by writing this plan

Charter §2 severity and P0–P4. Each in Observation → Evidence → Impact → Recommendation → Expected Outcome form,
compressed to a table because there are eleven of them. **None of these is a defect in built code — nothing is
built.** They are acceptance criteria that cannot be turned into a pass/fail case as written, plus two control
gaps. Every one has a recommended default so Wave 3 is a confirmation, not a blocker.

| # | Finding | Sev · P | Evidence | Recommendation |
|---|---|---|---|---|
| **UAT-F-01** | **The money type and rounding mode are unspecified.** No decision names `NUMERIC(14,2)`, a rounding mode, or where rounding happens relative to comparison. §5 F7 and F10 show the answer changes the result | **High · P1** | SPM §4.1, §5 KAN-193/200; no mention of decimal, precision or rounding anywhere in Wave 1 | `NUMERIC(14,2)`; decimal arithmetic end to end; **HALF_UP**; ratios carried **unrounded** into comparisons and rounded for display only. Architect ratifies in the compensation ADR |
| **UAT-F-01b** | **Three boundaries are inclusive-or-exclusive-unspecified:** the coverage gate at exactly 80%, the justification window on its last day, and "beyond threshold + 2pp" at exactly +2.00pp | **Medium · P2** | SPM §4.1.1, §4.2.3, §4.7.2 | Gate **inclusive** (evaluate at exactly 80%); window **inclusive** (no re-fire on the last day); delta **strictly greater**. UAT-42-200-21, -201-22, -201-23 are written against these and marked Blocked |
| **UAT-F-01c** | **Whether the subject is included in their own group median is unspecified**, and a flag-count assertion cannot distinguish the two implementations — only the reported figure can | **Medium · P2** | §5 F11 | **Include** the subject. Assert the reported gap value, not the count |
| **UAT-F-01d** | **"Exactly one current record per employee per date" contradicts "a correction is a new record"** — a same-date correction produces two rows for one date | **High · P1** | SPM §5.3 KAN-193 | Permit the same-date append; break ties by `created_at`; mark the superseded row; "current salary" returns exactly one value. Architect's ADR |
| **UAT-F-01e** | **The valid FTE range is unspecified.** `0` is a division by zero in every downstream comparison | **High · P1** | SPM §4.1.1 (FTE normalisation), no range given | `0.01 … 1.00`, refused outside. `0` refused explicitly with a named error |
| **UAT-F-02** | **A negative gender gap (women paid more) is not flagged** by `gap ≥ 5%` as written | **Medium · P2** | SPM §4.1.1 Check B definition; §5 F3-e | Flag on `|gap| ≥ threshold` and record the direction. Needs the SPM's word — it changes what the number means |
| **UAT-F-03** | **`_MONEYISH_KEYS` cannot enforce D5.6.** It matches **keys**, exactly like `_SECRETISH_KEYS` (`app/services/audit_service.py:95-98`). D5.6 says an amount is never written into a diff, metadata **or reason** — but `reason` is mandatory free text typed by a human, and a key-matching guard cannot see into it | **High · P1** | `audit_service._check_no_secrets`, `_clean_diff`; SPM §4.5.6 | Either (a) accept and document that `reason` is free text and the control is partial, or (b) add a value-level numeric guard on `reason` for compensation actions. **Do not leave the AC claiming a guarantee the mechanism cannot give** — that is worse than either option |
| **UAT-F-04** | **Four-eyes does not bind the initiator.** D4h forbids one user deciding two *levels*; it says nothing about the initiator also approving. `ingrid.makinen` holds PORTAL_ADMIN **and** HR_ADMIN, may initiate for anyone, and satisfies level 1 by role — so she can raise a pay rise and approve it, with KAN-198 fully implemented and passing | **High · P1** | SPM §4.4.8; `app/services/org_change_service.py:101-105` `_user_matches_step`; the seeded Acme chain | On a money-bearing or level-bearing request, **the initiator may not decide any level**. Add to KAN-198's criteria and to OQ-9's ratification |
| **UAT-F-05** | **`403` on a cross-tenant id is an existence oracle.** EP38's `AC-184-45` establishes `403`; for compensation that confirms a Telia employee id is real to an Acme admin | **Medium · P2** | EP38 §6.7; A07 | **`404` for every EP42 cross-tenant substitution**, and the inconsistency with EP38 recorded deliberately rather than discovered. Architect's call |
| **UAT-F-06** | **No minimum group size is defined for *aggregates*.** A "group average" over two people, shown to somebody who knows one of them, is the other's pay exactly | **High · P1** | SPM §4.1.1 defines minimums for **flags**, not for displayed aggregates; A16, A18 | No aggregate rendered below the Check B minimum (n<5); a group of 2 shows "insufficient comparison group" and **no numbers at all** |
| **UAT-F-07** | **A grant that yields nothing looks like a bug.** Granting `compensation:r` to DOTTED_LINE_MANAGER gives the feature but the role's defined scope is empty, so the screen is empty. The admin who granted it will raise a support ticket, and the temptation to "fix" it by widening scope is exactly the leak | **Medium · P2** | SPM §4.5.2 matrix + §4.5.3 row scoping; A04 | The Feature Access tab states the scope consequence next to the grant ("this role sees pay for: nobody"). UX owns the wording; the case is UAT-42-194-06/17 |
| **UAT-F-08** | **A non-ACTIVE employee's compensation behaviour is unspecified** — can a record be written for a `RESIGNED` employee, and is their history readable? | **Medium · P2** | SPM §8.1.2 hands it to the BA; nothing decided | History readable and retained; new records refused except a correction. Interacts with **CFL-42-3** (EP38's erasure enumeration does not mention pay) |
| **UAT-F-09** | **Does the four-eyes rule bind SYSTEM_ADMIN?** `decide()` lets SYSTEM_ADMIN satisfy any step (`org_change_service.py:248`), and SYSTEM_ADMIN is the identity every demo runs as | **Medium · P2** | `app/services/org_change_service.py:248`; SPM §4.4.8 silent on it | **Yes, it binds.** A control with a hole exactly where the demo user sits is not a control |
| **UAT-F-10** | **Gender `OTHER` and `NULL` are undefined in Check B.** The column is `MALE`/`FEMALE`/`OTHER` (`database/schema.sql:420-423`) and nullable | **Medium · P2** | schema; SPM §4.1.1 says "≥ 2 of each gender compared" without saying which genders | Excluded from the two compared medians, **counted and shown** as an exclusion. Never silently folded into a binary — that is a data-integrity and a dignity problem at once. DPO input alongside the §9 register entry |
| **UAT-F-11** | **`pct_change_band` bucket boundaries and the negative case are undefined** | **Low · P3** | SPM §4.5.6 lists `0-5, 5-10, 10-20, 20+` with no edges | Half-open `[0,5) [5,10) [10,20) [20,∞)` on the **absolute** percentage; `direction` carries the sign |

**Two of these — UAT-F-03 and UAT-F-04 — are control gaps rather than ambiguities, and I would not sign off a
release containing KAN-198 or KAN-202 with either open.** They are P1 because they are cheap now and expensive
after the code exists.

---

## 11. Entry criteria, exit criteria and my sign-off position

### 11.1 Entry criteria (before UAT execution starts on any EP42 story)

A UAT database separate from dev, built the CI way (`schema.sql` + `seed_rbac.sql`) with migrations applied and the
§1.4 fixture cohort loaded · the BA's numbered acceptance criteria published, so every case maps to one · the
Architect's ADRs for CFL-42-1, the compensation data model and CFL-42-5 signed off · `pytest`, both existing
regression suites and the new compensation suite green on the build under test · no open Critical defect · the
three EP42 feature codes registered in **all four** places with `TestFeatureRegistryHasNoDrift` proven to fail
without them.

### 11.2 Exit criteria (Charter, role file §Exit criteria)

Critical defects **0** · High defects **0** unless explicitly accepted and logged by the SPM · core workflows pass
across every in-scope persona in §1.3 · **permissions, tenant isolation and data integrity validated** — for this
epic that means the negative-visibility suite green and the tenant-substitution matrix complete, not sampled ·
audit validated · the arithmetic fixtures F1–F12 all matching hand-computed values · the Demo Readiness Gate pack
in §9 returning GO · business stakeholders accept the results.

### 11.3 Sign-off position, stated in advance

**No sign-off is given in this document, and none is implied.** Nothing is built.

When execution happens, my position is fixed and is not a judgement call I soften under delivery pressure:

1. **Sign-off is withheld while any Critical or P0 defect is open.** Not negotiable.
2. **A leak is always Critical.** There is no "minor" disclosure of a salary, and I will not accept a severity
   downgrade on the argument that a surface is "internal only" or "behind a login".
3. **KAN-193 without KAN-194 in the same release is a Critical defect on the day it ships**, per the SPM's own
   sequencing argument (§5.6.4). If they are separated, I raise it as one.
4. **A green suite is not evidence that the demoed behaviour works** — Gate D7's second half. I will name the
   specific assertions or record the check as unmet.
5. **A headless suite run is not a flow test.** Per `CLAUDE.md`, a flow test is a visible browser session with
   spoken narration, and it is successful **only when the user explicitly approves it**. I will never declare one
   successful on my own.

---

## 12. Traceability

| Ask | Stories | Case ranges | Attacks / fixtures |
|---|---|---|---|
| **R1** hold salary | KAN-193, 194, 202 | 193-01…20 · 194-01…32 · 202-01…16 | A01–A21 · — |
| **R2** backfill existing employees | KAN-195, 191 | 195-01…22 · 191-01…17 | A11 · M1–M28 |
| **R3** position change considers pay | KAN-196, 189 | 196-01…21 · 189-01…18 | — |
| **R4** promotion triggers a salary review | KAN-197, 192 | 197-01…15 · 192-01…14 | — |
| **R5** flag a >5% difference to the HR responsible | KAN-200, 201, 199 | 200-01…34 · 201-01…26 · 199-01…15 | A13, A16, A17, A18 · F1–F12 |
| **R6** job levels, per company | KAN-190, 191, 192 | 190-01…16 · 191-01…17 · 192-01…14 | X1–X7 |
| **R7** expose/hide per company | KAN-188 | 188-01…20 | A21 |
| **Cross-cutting** | all | CC-T1…CC-T7 · §4 A01–A21 · §5 F1–F12 | — |

**Reverse check:** every story has happy, edge, adversarial, permission and tenant-isolation cases, and every story
that writes state has audit cases. The two stories with no `Math` cases (KAN-188, KAN-190) genuinely have no
arithmetic; the two with no `Notif` cases (KAN-188, KAN-199) raise no notification. Both stated rather than omitted.

---

## 13. Open questions I need answered before execution

| # | Question | To | Blocks | Default I will test against meanwhile |
|---|---|---|---|---|
| **UAT-Q1** | Ratify UAT-F-01, F-01b, F-01c, F-01d, F-01e — the money type, rounding mode and the three boundary inclusivities | Architect (with the SPM on F-01c) | KAN-193, KAN-200 case execution | The recommendations in §10 |
| **UAT-Q2** | Ratify UAT-F-02 (negative gender gap) and UAT-F-10 (gender `OTHER` / `NULL`) | SPM + DPO | KAN-200 Check B | Flag on absolute gap with direction recorded; `OTHER`/`NULL` excluded, counted and shown |
| **UAT-Q3** | Accept or close UAT-F-03 — `_MONEYISH_KEYS` cannot police the free-text `reason` | Architect | KAN-193, KAN-202 | Document the control as partial; do not claim a guarantee |
| **UAT-Q4** | Ratify UAT-F-04 and UAT-F-09 — the initiator, and SYSTEM_ADMIN, under four-eyes | SPM (extends OQ-9) + Architect | KAN-198 | Both bound by the rule |
| **UAT-Q5** | Ratify UAT-F-06 — the minimum group size for **displayed aggregates** | SPM | KAN-200, KAN-201 | No aggregate below n=5 |
| **UAT-Q6** | CFL-42-3 — does erasure remove or retain pay history? UAT-F-08 depends on it | BA + DPO | KAN-202-15 | Retain; case written both ways |
| **UAT-Q7** | Confirm the seeded Acme chain still has the level-1/level-2 HR_ADMIN overlap, or point me at the current configuration | Architect / Delivery | §6.11 preconditions | UAT-42-198-01 verifies it as its own precondition |
| **UAT-Q8** | Will KAN-168 (real-DB tier) be available before KAN-200? Eight of the 34 KAN-200 cases and four of KAN-201's cannot be verified against mocks | Delivery / Architect | KAN-200, KAN-201 execution | If not, those cases are **Blocked**, and I will report them as Blocked rather than as passed |
| **UAT-Q9** | Confirm I may add `tests/ui/test_compensation_workflow.py` as a third standalone suite (it changes what "the regression suites" means in `CLAUDE.md`, which is the Architect's file) | Architect + SPM | §7.2 | Build it; propose the `CLAUDE.md` amendment in the same commit |

---

*Prepared by the UAT Lead, Wave 2, EP42. No test file was written or modified, no application code was touched,
the app was not started and neither regression suite was run — this wave is documentation only. Nothing in this
document constitutes sign-off, and nothing in it is evidence that any behaviour works: it is a plan for producing
that evidence.*
