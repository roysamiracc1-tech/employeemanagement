# EP42 — Compensation, Job Architecture & Pay Equity · UX / Product Design Spec

> **Owner:** UX / Product Designer · **Date:** 2026-08-09 · **Status:** Wave 2 deliverable — ready for BA / Architect
> reconciliation
> **Covers the eleven EP42 stories that have a user surface:** KAN-188 (the tenant-off state) · KAN-190 ladder
> configurator · KAN-191 level assignment & backfill · KAN-192 progression and the top-step signal · KAN-193/194
> the compensation record, visibility and **My Pay** · KAN-195 backfill & import · KAN-196 pay inside the shared
> position-change dialog · KAN-197 promotion · KAN-198 four-eyes on money · KAN-199 bands & compa-ratio ·
> KAN-200/201/202 the equity queue, flag delivery and the compensation timeline.
>
> **This is a build spec.** Every string below is final copy, not a placeholder. Every state listed is a state
> engineers must implement; anything not listed here is a gap I should be asked about, not guessed at.
>
> **Primary input, authoritative:** `EP42_SPM_SCOPE_AND_DECISIONS.md` (Wave 1). Where the shared brief and the SPM
> document disagree, the SPM wins and I have followed him — including S1 (three tenants: Acme 46, Telia 100,
> "Sam Cpmapny" 0) rather than the brief's "147 Acme". Decision references below are his (`D1`…`D8`, `OQ-n`).
> Where I disagree with a decision I have **complied and recorded the conflict** in §20 (Charter §9.3), never
> quietly designed something else.
>
> **Continues:** `EP38_UX_SPEC.md` — same design language, same component reuse, same state discipline. §2 of that
> document is not restated; it is extended, and §2.4 below records which of its shell fixes actually landed.
> **Related:** `docs/project-management/DEMO_READINESS_GATE.md` (D4 is mine — §15 answers it in full) ·
> `CLAUDE.md` access-control rules · roadmap D-004 / Q5 (WCAG 2.2 AA on all new work).
>
> **Out of scope for this spec** (SPM §3.3, no screens designed here): payroll, payslips, variable pay, benefits,
> total reward, comp-review cycles, budget-aware approval, FX rates, statutory gap-report generation, candidate
> or offer compensation, and any automatic pay or level change. **A1 adds a large one: performance management —
> see §25, which exists to keep it out.**

---

# 📌 WAVE 4 — AMENDMENT A1 APPLIED — 2026-08-09

> **Rulings absorbed (Gate G-1):** SPM §14 (Amendment A1, D1 and D3 re-ruled) · SPM §12.3 CFL-42-8, 13, 18, 19,
> 20, 22, 24, 25, 26, 27, 28, 29, 32, 33 · SPM §12.4 UXQ2, UXQ3, UXQ4, UXQ5, UXQ6, UXQ7, UXQ8, UXQ9, OQ-BA-2,
> OQ-BA-3, OQ-BA-4, UAT-F-07, UAT-F-08 · SPM §12.2 A-5 · SPM §12.6 Rulings 13, 27, 32 · SPM §13.5 standing rules.
>
> **The one-sentence summary of what changed for design.** The job ladder stopped being an HR configuration
> artefact and became **an instrument of transparency to the employee** — every step now carries authored
> expectations an employee can read, and a manager writes a personal roadmap to the next one. At the same time
> "5%" stopped being a detection threshold and became **the pay increment between steps**, which turns the equity
> check from a statistical comparison against colleagues into an absolute comparison against a configured number.
> Both changes make the product more honest and both land squarely on my screens.

### Change index — what is amended, superseded and new

| § | Status after A1 | What changed |
|---|---|---|
| §2.3 | **Amended** | Step vocabulary (`.0` entry), expectation vs roadmap vs pay point, and the banned-assessment-word list |
| §2.4 | **Amended** | My UX-CFL-42-8 was accepted and is now **KAN-204** in W0, tagged EP33. It gates the first EP42 screen |
| §3.1 | **Amended** | A **fourth feature code, `job_architecture`**; thresholds move to `company_settings:w` (my `pay_equity:d` was rejected — CFL-42-20); ladder reads split from ladder writes |
| §3.2 | **Amended** | Denial is a JSON-aware `403`, not a 302 (CFL-42-8); cross-tenant is **`404`**, not 403 (CFL-42-33) |
| §3.3 | **Extended** | D-R9 ratified and widened to *inference* as a category; **two new rules — D-R11 (expectations are not confidential) and D-R12 (no ratings, no scores)** |
| §4 | **Amended** | Nav and route map for `job_architecture`, the roadmap surfaces and the two-gate settings page |
| §5 | **Extended** | A fifth journey: **the employee, for whom the ladder is transparency rather than configuration** |
| §6 | **Amended + extended** | Entry at `.0`; step count **per level, no default**; the money column and its two gates; **§6.9 the step-expectations editor**, which turns this screen from a structural editor into a content editor |
| §7 | **Amended + extended** | Assignment carries a **step**; **§7.9 the fitted-step backfill review**, which now gates the entire equity feature |
| §8 | **Amended + extended** | Mandatory `review_context`; **the pay change is proposed, never applied**; §8.6 the intermediate state where the step has landed and the pay has not; the signal narrows to the reporting manager |
| §9 | **Amended** | Contractor rates now recordable (UXQ8); coverage renamed to **pay coverage** and **level coverage** (A-5); reason categories seeded (UXQ3); non-ACTIVE rule (UAT-F-08) |
| §10–§11 | **Amended** | `PROMOTION` → **`LEVEL_CHANGE` + direction** (CFL-42-25), which **deletes** my derived-display-label workaround; `NOT_ANSWERED_NO_PERMISSION` (CFL-42-13) |
| §12 | **Extended** | Four-eyes gains the initiator bar, the ≥2-satisfiable-levels rule, the seeded two-level chain, SYSTEM_ADMIN binding and the cancel remedy |
| §13 | **Amended** | Bands are the level's **envelope**, no longer the comparison basis; pay markets are their own story |
| §14.2–14.5 | **SUPERSEDED in part** | The primary check is **Check A′** — absolute, against the step pay point. No group median, no `n≥3`, no coverage gate for it. **Check B survives statistically intact.** Three finding types, asymmetric severity, and the **Propose adjustment** remedy |
| §15 | **Extended** | Six new events, three new icons, and the roadmap's acknowledgement lifecycle |
| §18 | **Extended** | Criteria 57–98 |
| §19–§20 | **Amended** | Eight of my ten open questions are answered; five of my eight conflicts are ruled; four new ones from A1 |
| **§22** | **NEW** | **KAN-207 — the step roadmap.** The manager's authoring view, the employee's view, acknowledgement, versions. *The most important new screen in the epic* |
| **§23** | **NEW** | **KAN-206 — step pay points, the increment and the tolerance**, with the two configuration guards and the copy that explains the refusal |
| **§24** | **NEW** | **The audited salary export** (UXQ5, ruled into KAN-202) |
| **§25** | **NEW** | **The line against performance management** — R-17, written as a design boundary an engineer and a future SPM can both apply |
| **§26** | **NEW** | Wave 4 change log — every superseded rule, named |

**Nothing below is deleted.** Superseded design carries a `> ⛔ **SUPERSEDED by A1**` marker and a one-line record
of what replaced it, because a spec that quietly rewrites itself teaches nobody why the first answer was wrong.

---

## 1. Scope reviewed

| Input | What I took from it |
|---|---|
| `EP42_SPM_SCOPE_AND_DECISIONS.md` | All product rules. D1 (grouping + two checks), D2 (delivery + lifecycle), D3 (ladder model + no auto roll-up), D4 (coupling, four-eyes, D-185-1 hazard), D5 (visibility matrix, audit redaction, §4.5.7 leak list), D6 (tenant switch), D7 (backfill + partial data), D8 (T5, synthetic banner) |
| `templates/base.html` | Shell, sidebar gating, bell's three sections (`:290-320`), badge maths (`:413-440`), `NOTIF_ICON` (`:608-624`), `ocSummary()` (`:630-637`), the reject-is-a-deep-link precedent (`:639-641`), `escH()` (`:661`) |
| `templates/org_change/_move_modal.html` | The shared Request Position Change dialog KAN-196 must **extend, not duplicate**: two openers, one endpoint, panel model (`mvPanel`), focus trap (`mvKeydown`), private live regions (`:105-106`), the "effective date deliberately not implemented" note (`:15-19`) that KAN-189 closes |
| `templates/employees/profile.html` | `.profile-header`/`.profile-actions` cluster, `two-col`, `.card`/`.info-list` — where the Compensation, Job Level and My Pay cards go |
| `templates/employees/directory.html` | The `⋯` row menu with correct `role="menu"` / focus restore (`:296-340`) — reused, not re-invented |
| `templates/org/tree.html` | Drag-to-move, `can_move` gate, and the legend line naming the keyboard equivalent (`:42-47`) — the pattern KAN-190's reorder must match |
| `templates/admin/org_change_workflow.html` | The repeatable-row config editor the ladder editor is built from; also the amber unconfigured-note pattern (`:16-18`) |
| `templates/admin/panel.html` | `.admin-tabs`, the Feature Access matrix (`:433-460`), the unsaved-changes chip (`:445-447`) and the **confirm-before-save diff dialog** (`:470-504`) — the model for "preview what this does before you save it" |
| `templates/admin/analytics_locked.html` | The tenant-disabled screen precedent KAN-188 must follow |
| `templates/imports/upload.html`, `templates/imports/preview.html` | The dry-run → preview → commit shape KAN-195 reuses; also the `prompt()`/`alert()` debt it must not inherit (`preview.html:94,108`) |
| `templates/org_change/inbox.html` | Approvals inbox, `diffHtml`/`diffInline`, the review modal, the stale-deep-link guard (`:188-196`) |
| `static/css/style.css` | Tokens (`:9-32`), badge pairs (`:403-408`), `.row-menu` (`:540-561`), `.sr-only` (`:565`) — and the a11y gaps in §2.4 |
| `docs/project-management/BACKLOG.md` | DEF-001/2/3 records (`:635-637`) and KAN-174/F20 (`:564`), the open keyboard-drag defect this spec must not repeat |
| **`EP42_OWNER_ANSWERS_A1.md`** *(Wave 4)* | The owner's verbatim answer. Three things drive this amendment: *"it will be job of manager to outline next level role and respossibility which will act as roadmap and trsnaparency for the trainee"*, *"each level will have it own responsibility and expectation"*, and *"5% diffence means in betwween 1.0 and 1.1"* |
| **SPM §12, §14, §15.3** *(Wave 4)* | The reconciliation rulings and the A1 re-rulings. §15.3 is my tasking; §14.7 is the invalidation list; §13.5 the standing rules |
| **`templates/employees/my_team.html`** *(Wave 4)* | The manager's existing team surface — where the roadmap's "who hasn't got one" prompt belongs, rather than a new page |

**Not available / not examined:** no running application (documentation-only task, app not started), no BA acceptance
criteria for EP42 yet (Wave 2, in parallel), no Architect ADR yet. Where a rule needs one of those I have designed
against the SPM's stated default and named the dependency.

---

## 2. Design language these screens must match

### 2.1 Tokens

`--primary #2563eb` · `--bg #f0f4f8` · `--card #fff` · `--border #e2e8f0` · `--text #1e293b` · `--muted #64748b`
(light) / `#94a3b8` (dark) · `--radius 12px` (`static/css/style.css:9-32`).
**Never hardcode a hex where a token exists.** Every EP42 surface must survive the dark-mode toggle, which
`tests/ui/test_browser.py` already asserts.

### 2.2 Components reused — EP42 introduces no new component library

| Need | Existing class / pattern | Source of truth |
|---|---|---|
| Page frame | `.page` + `<h1 style="font-size:1.25rem;font-weight:700">` + muted subtitle | `org_change/inbox.html:8-13` |
| Tabbed hub | `.admin-tabs` > `.admin-tab.active` + `.admin-panel` | `admin/panel.html:79-96` |
| Section container | `.card` > `.card-header` > `h2` + `.card-body` | `employees/profile.html:61-86` |
| Data list | `.table-card` > `.table-wrap` > `<table>`, empty via `<tr class="empty-row">` | `org_change/inbox.html:24-33` |
| Dialog | `.modal-box` > `.modal-header`(`.modal-title`,`.modal-sub`,`.modal-close`) > `.modal-body` > `.modal-footer` | `org_change/_move_modal.html:24-101` |
| Repeating config rows | The `steps-list` row (`Level N` + selects + `✕`) | `admin/org_change_workflow.html:45-63` |
| Unsaved-changes chip | `#fa-dirty-count` amber pill + a `Save changes` button that appears only when dirty | `admin/panel.html:445-453` |
| **Confirm-before-save diff dialog** | `#perm-confirm-modal` — a table of every staged change, reviewed before commit | `admin/panel.html:470-504` |
| Row overflow menu | `.row-menu` / `.row-menu-btn` / `.row-menu-list[role=menu]` with Esc + focus restore | `employees/directory.html:296-340`, `style.css:540-561` |
| Buttons | `.btn` + `.btn-primary` / `.btn-ghost` / `.btn-danger` / `.btn-success`, `.btn-sm` | `style.css` |
| Fields | `.form-group` > `label` + `.form-control` | `admin/register.html` |
| Status pills | `.badge` + `badge-green/amber/red/gray/blue/purple` | `style.css:403-408` |
| Inline amber notice | `#fffbeb` / `#fde68a` / `#b45309` box | `admin/org_change_workflow.html:16-18` |
| Tenant-off screen | Centred lock panel + one explanation + one way back | `admin/analytics_locked.html` |
| Import wizard | drop zone → preview table with per-row status → commit | `imports/upload.html`, `imports/preview.html` |
| Server flash | `.flash.flash-success` / `.flash-error` | `base.html:346-352` |

### 2.3 Copy voice — and the money vocabulary EP42 adds

Continued from EP38: sentence-case labels, `*` for required, muted helper under the field, placeholder selects
worded `— Select a level —` / `— No change —`, buttons in Title Case naming the outcome, empty states as one
factual sentence with the next action in bold, **no system codes in the UI**.

EP42's additions, fixed here so they cannot drift across eleven stories:

| Concept | The word we use | Never |
|---|---|---|
| The amount | **base salary** (`Base salary`, `annual base`) | "comp", "remuneration", "package", "CTC", "salary package" |
| The record | **salary record** / **compensation record** | "comp row", "pay line" |
| A level's title | **job title** (it is the canonical one) | "level name" in employee-facing copy |
| `employees.job_title` | **working title** | "job title" (that word now belongs to the level) |
| Family / level / step | **job family**, **level**, **step** — displayed `2.3`, spoken "level 2, step 3" | "grade", "band" (band means the pay range) |
| The pay range | **range** (employee-facing) / **band** (admin-facing) | mixing the two in one screen |
| `compa_ratio` | **position in range** in words for employees; the number only for `compensation:r` admins | showing a bare ratio to an employee |
| A finding | **finding** (a standing condition) | "alert", "violation", "breach", "issue" |
| Disposition | **record what was decided** | "dismiss", "clear", "close off", "acknowledge" |
| Absence of a record | **No salary recorded** | `—`, `0`, `N/A`, blank, `€0`, "Unknown" |
| Excluded from comparison by employment type | **Not applicable for comparison — contractor rate recorded** *(A1/UXQ8 — see §9.6 E2)* | "No salary recorded" |
| `PAY_EQUITY_FLAG_RAISED` etc. | never rendered; every code has a sentence | any enum on screen |

**A1 additions — the words that carry the new model.** These matter more than usual, because two of the three new
objects are read by employees and the third is money.

| Concept | The word we use | Never |
|---|---|---|
| Entering a level | **step `.0`** — `Level 2, step 2.0`. The employee **enters** at `.0` | starting at 2.1; "step zero" spoken as a null |
| How many steps a level has | **"steps to the next level"** — `Level 1 has 5 steps to the next level (1.0 – 1.5)` | "5 steps" alone, which reads as five values when there are six |
| What a step means | **step expectations** — *"what step 1.2 means here"*. Company-authored, generic, the same for everybody on that step | "criteria", "requirements", "competencies", "standards" (all read as an assessment rubric) |
| The manager's personal statement | **next-step roadmap** — *"what you specifically need to do"*. Per employee, forward-looking, mutually discussed | "development plan" (implies HR process), "objectives", "goals", "targets", "PIP" |
| The rate for a step | **step pay point** — the configured rate for `2.3` in this pay market | "step salary" (implies everyone on 2.3 is paid exactly it) |
| The gap allowed around it | **tolerance** | "threshold" (which now means only the gender-gap number) |
| The uplift between steps | **step increment** | "the 5%", which meant something else in Wave 1 |
| Pay that hasn't kept up | **pay below step** | "underpaid", "unfair", "discrepancy", "violation" |
| Pay above the point | **pay above step** | "overpaid" |
| The employee acknowledging a roadmap | **"Confirm we discussed this"** | "Accept", "Agree", "Sign off", "Approve" — all of which imply a contract the product is not making |

**Banned across every roadmap, step and progression surface** — the R-17 boundary made lexical, so a copy review
can fail it: *rating · score · rated · assessment · evaluation · grade (as a verb) · performance level ·
achieved · not achieved · met / unmet · complete / incomplete · % complete · on track · behind · at risk ·
exceeds · meets · below expectations · potential · calibrat\* · ranking.* If one of these words is needed to
describe a screen, the screen is out of scope (§25).

**Numbers.** Amounts render with a thousands separator and the currency code, in the tenant's locale format,
e.g. `€72,000 · EUR`. Never a bare number. Never a decimal on an annual figure. Percentages to one decimal
(`8.3%`). Compa-ratio to two (`0.96`).

### 2.4 Accessibility state of the shell — verified today, and what it means for EP42

EP38 §2.4 specified nine shell fixes as "ship with EP38". **Three of the shared ones did not land**, verified in the
repo on 2026-08-09. EP42 adds roughly ten new surfaces and cannot absorb this debt ten times.

| # | EP38 fix | Status now | Evidence | Consequence for EP42 |
|---|---|---|---|---|
| A1 | Global `:focus-visible` indicator | **Not landed.** Only `.row-menu-btn` and `.row-menu-list > *` have one | `style.css:547,561` — no global rule | Every EP42 control would ship without a visible focus ring. **2.4.7 / 2.4.11 fail.** Blocking — §20 UX-CFL-42-8 |
| A2 | Accessible dialog behaviour | **Partly landed** — `_move_modal.html` has `role="dialog"`, `aria-modal`, a trap, Esc and focus restore (`:21,159-169,330-335`). `#reject-modal` (`base.html:671`), `#review-modal` (`inbox.html:51`), `#perm-confirm-modal` and the skill/cert dialogs still have none | as cited | EP42 dialogs adopt the `_move_modal` implementation; **the disposition and record-salary dialogs must not copy `#reject-modal`** |
| A3 | Shared live regions in `base.html` | **Not landed.** The only live regions in the product are `_move_modal.html:105-106`, private to that dialog | grep for `live-status` in `templates/` returns the move modal only | Ten new async surfaces would each invent their own. Blocking — §20 UX-CFL-42-8 |
| A4/A5 | Accessible text/status colours | **Available** — the `.badge-*` pairs exist and pass | `style.css:403-408` | Use the badge pairs. `#94a3b8` is forbidden as body text on new light surfaces; `admin/org_change_workflow.html:26,29` still uses `#dc2626`/`#16a34a` and the ladder editor must **not** copy those two lines |
| A8 | No `alert()` / `confirm()` / `prompt()` | **Not landed outside EP38's own work** — `imports/preview.html:94,108`, `org_change/inbox.html:151,153,178`, `employees/profile.html:428,434,436` | as cited | KAN-195 reuses the import surface and KAN-201 lives beside the inbox. **No EP42 code path may reach a native dialog**, and where EP42 touches one of those lines it replaces it |
| A9 | `prefers-reduced-motion` | **Not landed** | no match in `style.css` | The coverage meters, progress bars and the equity-run spinner all animate. Needed |

**Rule for this epic: EP42 does not start until A1, A3 and A9 are in the shell.** They are three CSS/HTML additions,
they are shared, and they are the difference between "WCAG 2.2 AA as a design standard on new work" (D-004 / Q5)
being true and being aspirational.

> ✅ **A1/Wave 4 — accepted and scheduled.** CFL-42-29: this is now **KAN-204**, in **W0**, tagged **EP33** so
> that epic's scope shrinks honestly rather than EP42 absorbing someone else's work invisibly. It **gates the
> first EP42 screen**, and I am named as a reviewer on it (SPM §13.3 track B). The bell's missing
> `aria-expanded` / `role="region"` / Esc (§15.5) rides in the same story, because EP42 adds a section to it.

### 2.5 The two shared primitives, restated because EP42 depends on them

**(a) Accessible dialog behaviour** — the `_move_modal.html` implementation, extracted and reused by every EP42
dialog: `role="dialog" aria-modal="true"` + `aria-labelledby`/`aria-describedby`; opener stored and focus moved to
`.modal-title[tabindex="-1"]`; Tab/Shift+Tab cycle inside only; background inert; Esc closes and restores focus;
overlay click closes. **Close is refused while a mutation is in flight** — footer buttons disabled, `×` disabled,
Esc ignored — so a half-committed salary write can never be dismissed.

**(b) Shared live regions** in `base.html`, below `<main>`:

```html
<div id="live-status" class="sr-only" aria-live="polite" aria-atomic="true"></div>
<div id="live-alert"  class="sr-only" role="alert" aria-atomic="true"></div>
```

`.sr-only` already exists (`style.css:565`). Loading / progress / success → `#live-status`. Failure / blocker →
`#live-alert`. `_move_modal.html`'s private `mv-live-*` spans are folded into these.

### 2.6 Three primitives EP42 introduces — the money components

These are the only new components in the epic. Everything else is reuse.

**(a) `Money` — the amount renderer.** One function, used everywhere an amount appears, so the rules cannot be
implemented differently on ten screens.

- Renders `€72,000 · EUR` at `.9rem`, weight 600, in `--text`. **Never** at display size, never as a
  `.stat-num`, never in a `<h1>`/`<h2>`, never in `document.title`.
- Takes a **currency code**, always. There is no default currency in this product.
- If the value is absent from the payload, `Money` renders **nothing at all** and its label row is not emitted.
  It never renders a placeholder. (See D-R1.)
- Respects the **Hide amounts** state (c).
- Escapes via `escH()`; the reason/note strings beside it go through `textContent`.

**(b) `NoValue` — the two absence states, which must never look like each other or like a number.**

| State | Renders | Helper | Action |
|---|---|---|---|
| Permitted viewer, no record | `No salary recorded` in `var(--muted)`, weight 500 | `This is not a zero — the portal has no figure for Ravi yet.` | `[ Record salary… ]` for `compensation:w` |
| Excluded by employment type | `Not applicable — Contractor` in `var(--muted)` | `Contractors don't have an annual salary in this portal and aren't compared in pay equity.` | none |
| No permission | *nothing — the row, the card and the payload field are absent* | — | — |

Forbidden renderings for an absent amount, named so a code reviewer can fail them: `—`, `-`, `0`, `€0`, `0.00`,
`N/A`, `null`, `undefined`, an empty cell, a blurred number, `••••` **as a permission state**, or a currency symbol
with nothing after it.

**(c) `Hide amounts` — the shoulder-surfing control.** A toggle in the header of every surface that renders an
amount (profile Compensation card, My Pay, the Compensation hub, the equity queue, the timeline).

```
[ 👁 Hide amounts ]        ← .btn.btn-ghost.btn-sm, role=button, aria-pressed="false"
```

- Default **off** — amounts are shown. Hiding by default would put friction on the primary task and would train
  users to click through it without reading.
- When pressed: every `Money` on the page renders `•••••• · EUR` and the button becomes `[ 👁 Show amounts ]`,
  `aria-pressed="true"`. `#live-status` → `Amounts hidden.` / `Amounts shown.`
- Persisted per browser in `localStorage['comp.hideAmounts']`, so it survives navigation — a user who hides
  amounts before walking to a meeting room does not have to re-hide on every screen.
- **Auto-hide after 5 minutes of no interaction** on a compensation surface, announced politely; suppressed while
  any form field on the page has focus or a dialog is open, so it can never interrupt typing. *(Should · P2.)*
- **The critical distinction, and it must be in the code comment:** `Hide amounts` is a display preference for a
  viewer who **already has permission**. It is never the mechanism that enforces permission. Masking exists only
  where the value is authorised; **absence** is what unauthorised looks like (D-R1).
- Print: `@media print`, every compensation surface prints with a footer
  `Printed by Priya Nair · 9 August 2026 14:32 · Confidential — pay data` and `Hide amounts` has no effect on
  print (a deliberately printed page is a deliberate act).

---

## 3. Discretion by design — the permission model as the user experiences it (KAN-194, D5)

> Salary is the most sensitive data this product will ever hold. **The default in every ambiguous cell is "no",**
> and a screen must never hint at a figure the viewer may not see.

### 3.1 The feature codes and the surface map

> ⛔ **SUPERSEDED by A1.** There are now **four** codes, not three: `job_architecture` is added (SPM §14.3.2),
> because A1 makes **the manager** the author of the roadmap and a manager could not have authored one under
> `compensation:w` without being given write access to everybody's salary. The table below is the amended one;
> the two changes to my Wave 2 version are marked **(A1)** and **(CFL-42-20)**.
>
> **CFL-42-20 — my `pay_equity:d` proposal was rejected, and the reasoning is better than mine.** The SPM
> adopted the Architect's `company_settings:w` instead. His tiebreaker: `d` means *delete* everywhere else in
> this product, so a grant labelled "delete" that actually confers *configure* misleads at exactly the moment the
> tenant admin makes the choice — and it implies findings are deletable, which they are not. I accept it without
> reservation; it is the same "consequences where the choice is made" principle I argued for elsewhere, applied
> to the label on a checkbox. **The design consequence is mine to carry: the Compensation Settings page now has
> two gates and must read coherently to a holder of one and not the other — §3.7.**

Per `CLAUDE.md` and SPM D5.1: routes use `@require_feature_access('code')`, nav uses
`{% if has_feature_access('code') %}`, **no hardcoded role lists, no per-feature sub-flags**. Row scoping is a
service-layer rule and is *not* the forbidden sub-flag (SPM D5.3).

| Surface | Feature code | Action | Row scope | Story |
|---|---|---|---|---|
| **Nav item `Job Architecture`** **(A1)** | `job_architecture` | `r` | company | KAN-190 |
| **`/ladder` — browse the ladder, families, levels, step expectations** **(A1)** | `job_architecture` | `r` — **seeded to every role, including `EMPLOYEE`** | company | KAN-190 |
| **Your own level title on your profile / directory row** | `employee_profiles` | `r` | — | CFL-42-18 as refined by A1: it is an attribute of the person, like their name, so a tenant switching `job_architecture` off must not blank the directory |
| **`/ladder` → edit families, levels, titles, step counts, step expectations** **(A1)** | `job_architecture` | `w` | company | KAN-190 |
| **Base pay point + step increment (the money column of the same screen)** **(A1)** | `compensation` | `w` | company | KAN-206 |
| **Next-step roadmap — read your own** **(A1)** | `job_architecture` | `r` | **hard-scoped to `session.employee_id`, server-side** | KAN-207 |
| **Next-step roadmap — read a report's** **(A1)** | `job_architecture` | `r` | viewer's scope (solid-line reports) | KAN-207 |
| **Next-step roadmap — author / publish / supersede** **(A1)** | `job_architecture` | `w` **or** the subject's solid-line manager | subject | KAN-207 |
| **Acknowledge your own roadmap** **(A1)** | `job_architecture` | `r` + you are the subject | self | KAN-207 |
| Nav item **Compensation** | `compensation` | `r` | — | KAN-193 |
| `/compensation` → Overview (pay & level coverage, deferred list) | `compensation` | `r` | viewer's scope | KAN-195 |
| `/compensation` → Level assignment **(now level *and step*)** | `compensation` `w` **+** `job_architecture` `w` | `w` | company | KAN-191 |
| **`/compensation` → Fitted-step review** **(A1)** | `compensation` `r` **+** `job_architecture` `w` | `w` | company | KAN-191 |
| `/compensation` → Salary bands *(now the level's envelope)* | `compensation` | `w` (read-only for `r`) | company | KAN-205 |
| `/compensation` → Import | `compensation` | `w` | company | KAN-195 |
| **`/compensation` → Export current salaries** **(A1 / UXQ5)** | `compensation` | `r` | **exactly the viewer's scope** | KAN-202 |
| `/compensation` → Settings — **pay markets, tolerance, gender-gap threshold, justification categories, escalation recipients** | **`company_settings`** | **`w`** **(CFL-42-20)** | company | KAN-199/200 |
| `/compensation` → Settings — **salary-change reason categories, annualisation constants** | `compensation` | `w` | company | KAN-193/199 |
| Nav item **Pay Equity** + `/compensation/equity` register | `pay_equity` | `r` | company | KAN-201 |
| **Numeric measured values in the register (gap, pay point, compa-ratio)** | `pay_equity` `r` **AND** `compensation` `r` **(CFL-42-19)** | `r` | company | KAN-201 |
| Disposition a finding | `pay_equity` | `w` | company | KAN-201 |
| **`Propose adjustment` on a `PAY_BELOW_STEP` finding** **(A1)** | `pay_equity` `r` **+** `compensation` `r` **+** `_can_initiate_for` | — | subject | KAN-201 |
| Compensation card on **another person's** profile | `compensation` | `r` | viewer's scope | KAN-193 |
| `Record a change…` / `Record salary…` | `compensation` | `w` | viewer's scope | KAN-193 |
| Void / correct a historical record | `compensation` | `d` | company | KAN-193 |
| Compensation history timeline | `compensation` | `r` | viewer's scope | KAN-202 |
| **Job Level card on another person's profile** — level, step, expectations | **`job_architecture`** `r` **(A1)** | `r` | viewer's scope | KAN-191 |
| **The step's *pay point* on that card** | `compensation` | `r` | viewer's scope | KAN-206 |
| `Advance step…` **(A1: now `job_architecture:w` or the manager, not `compensation`)** | `job_architecture` `w` **or** solid-line manager, **+** `_can_initiate_for` | — | subject | KAN-192 |
| The **pay proposal** inside `Advance step…` | `compensation` | `r` | subject | KAN-192/196 |
| `Request a level change…` *(user-facing word: **Promotion** when the direction is up)* | `compensation` `r` **+** `_can_initiate_for` | — | subject | KAN-197 |
| Pay block inside the shared move modal | `compensation` | `r` | subject | KAN-196 |
| **My Pay** on your own profile | `compensation_self` | `r` | **hard-scoped to `session.employee_id`, server-side** | KAN-194 |

**Two notes an engineer will otherwise get wrong.**

1. **Proposing is not writing.** A solid-line manager holds `compensation:r` only by default, yet D5.2 says they
   propose the pay change at transfer and promotion. So the pay block in the move modal, `Advance step…` and
   `Request promotion…` render for **`r`**, not `w`. The write happens under the approval engine's authority on
   final approval. Gating those on `w` would silently remove the manager flow that R3 and R4 exist for.
2. **Read-without-write is a designed state, not an afterthought.** An `r`-only holder sees every compensation
   surface and **no action buttons at all** — not disabled ones. Advertising a control you cannot use is the
   EP38 §7.4 rule and it applies here without exception.
3. **(A1) `job_architecture:r` is seeded to every role, including `EMPLOYEE`, and that is the point.** It is the
   only feature code in this product whose default is "everyone", and it is deliberate: the owner's stated
   purpose for the ladder is *transparency for the trainee*. An employee who cannot read the expectations of
   their own step and the next one has not been given the feature. **A design review that "tightens" this has
   removed the requirement, not hardened it** (see D-R11).
4. **(A1) The manager authors the roadmap without any pay permission.** `job_architecture:w` **or** being the
   subject's solid-line manager is sufficient. Do not gate roadmap authoring on `compensation` — that coupling
   is the reason the fourth code exists.
5. **(A1) One screen, two gates, twice.** Both the ladder configurator (§6) and Compensation Settings (§3.7)
   present job content and money on the same page under different codes. Neither may render a broken half.

### 3.7 A screen with two gates — how it must read *(A1, CFL-42-20)*

Two pages now mix `job_architecture:w` / `compensation:w` (the ladder) and `company_settings:w` /
`compensation:w` (Settings). The rule, which is just §3.2 applied per section rather than per page:

- **Each section is present or absent on its own gate.** Never disabled, never a lock icon, never a section
  header with an empty body.
- **The page never says what is missing.** A holder of one gate sees a complete, coherent page containing only
  what they may act on. They are not told a "Pay points" section exists for somebody else — that is a disclosure
  about the tenant's configuration surface and it invites a request the person cannot make.
- **No page is empty as a result.** If a viewer's grants would leave every section absent, the page is not
  reachable at all: the nav item does not render and a direct URL takes the standard redirect. A page that
  renders as a title and nothing else reads as a defect.
- **Copy is written to survive the absence.** No sentence in the job-content half may reference a figure in the
  money half, and vice versa. Concretely: the ladder's level row reads `Level 2 · Senior Software Engineer ·
  5 steps to the next level` for a `job_architecture:w` holder, and gains `· base €72,000 · +5.0% a step` only
  for a `compensation:w` holder. The first sentence is complete on its own.
- **A11y:** the sections are `<section>` with their own `<h2>`; the page's `<h1>` and its introductory sentence
  are written to be true for either audience.

### 3.2 What "no access" looks like — for every surface

**Nothing.** Not a disabled control, not a greyed nav item, not a tooltip explaining what they are missing, not a
blurred figure, not a `••••`, not a "Hidden" chip, not an empty card with a lock on it.

- Sidebar items absent · profile cards absent · row-menu items absent (and an empty menu means no `⋯` at all,
  per `directory.html:297`) · the modal's pay block absent (SPM D4f: *absent, not disabled*).
- Direct **page** URL → the existing `require_feature_access` behaviour: flash `You do not have access to that
  page.` and redirect to the dashboard. **No bespoke 403 page for EP42.**
- **(A1 / CFL-42-8) API without access → a JSON-aware `403` with a JSON body**, not the 302-to-HTML the decorator
  does today. My Wave 2 text said "403" and described behaviour the decorator does not have; the SPM has ruled
  the fix into KAN-188. **The design consequence is mine:** a `fetch()` that receives a 302 and parses a
  dashboard as JSON fails silently, and a dialog that fails silently is the DEF-002 shape — the user is told
  nothing while the product looks like it worked. Every `P` state below assumes the JSON denial exists.
- **(A1 / CFL-42-33) A cross-tenant subject id returns `404`, not `403`** — a 403 confirms the id is real, which
  is an existence oracle across tenants. The user-facing copy is unchanged (`That employee is not in your
  company.`) because the actor is looking at their own screen, not probing.
- **The amount is absent from the JSON payload**, not filtered in the browser (SPM D5.3, R-3). A CSS-hidden
  salary is a leak that passes a screenshot review.
- `SYSTEM_ADMIN` bypasses all three codes automatically via `_load_feature_access()` — no special-casing anywhere
  in EP42 code.

### 3.3 The ten discretion rules

These are the rules I will review every EP42 screen against. They are numbered so the BA can make them criteria and
UAT can assert them.

| # | Rule | Why |
|---|---|---|
| **D-R1** | **Absent, not hidden.** No value the viewer may not see appears in the payload or the DOM. No blur, no mask, no placeholder, no "Hidden", no disabled field holding the number | A mask confirms a figure exists. Confirming existence to someone excluded from the value is itself a disclosure |
| **D-R2** | **No compensation column, sort, filter, badge or tooltip in the directory, org tree, search results, My Team or any export of those.** Pay lives on the profile, in `/compensation`, and in the move modal — nowhere else | SPM §4.5.7. Scanning surfaces are where a bystander reads a screen over a shoulder, and where a sort order silently ranks people by pay |
| **D-R3** | **Counts and meters are computed over the viewer's row scope**, and their denominator is stated. A manager sees `3 of your 4 direct reports`, never `91 of 146` | A company-wide meter shown to a row-scoped viewer is a covert company-wide read |
| **D-R4** | **A list never says how long it would have been.** No "142 more you can't see", no greyed rows, no pagination total that exceeds the scoped result | Set size is information about people outside your scope |
| **D-R5** | **No amount in a URL, a page title, a flash message, a toast, a notification body, an email, a log line or an audit diff** | URLs land in history and screenshots; titles land in window switchers and screen shares; SPM D5.6 covers the audit case with `_MONEYISH_KEYS` |
| **D-R6** | **No amount survives navigation.** Amounts are fetched per view and never cached into `localStorage`, `sessionStorage` or a global JS constant rendered into the page for a later screen | A pay figure sitting in `window.EMP` on the directory page is a leak with no visible surface |
| **D-R7** | **Three absence states, never interchangeable:** `No salary recorded` · `Not applicable — <type>` · nothing at all. Never `—`, `0` or blank | An absent value must never be able to look like a value, and "excluded" must never be counted as "missing" (SPM D7.7) |
| **D-R8** | **A zero is a real salary.** The amount field refuses `0` and negatives with a specific message, and an import row with `0` is an error, not an unknown | The D-185-1 hazard in its worst form (SPM D4g) |
| **D-R9** | **A derived number is the same data class as the number it derives from.** Compa-ratio, group median, measured gap, percentage change **and (A1) the step pay point and anything computed from it** are all money and follow `compensation:r`, not `pay_equity:r` | A gap percentage plus one known salary is another salary. **Ratified as CFL-42-19**, and the SPM has amended his own D5.7 to add *inference* as a named category on the leak list — his surface list enumerated surfaces and missed derivations. See §14.2 for what a `pay_equity`-only viewer sees instead |
| **D-R9a** | **(A1) No aggregate of any kind is rendered below n = 5**, and the configurable group minimums are floored in the database so they cannot be set below 2 | CFL-42-32. A "group average" over two people, shown to someone who knows one of them, is the other's pay exactly |
| **D-R10** | **Never derive, estimate or impute a salary** — not from the band, not from the level, not from the group median, not "typical for this role". **(A1) The step pay point is not an exception:** it is what someone *should* be paid, and it must never be rendered where an actual salary would be, or in a way that could be read as one | SPM D7.6. An imputed figure on a screen is indistinguishable from a real one — and A1 has just created a very plausible-looking one |
| **D-R11** | **(A1) Step expectations and the ladder are NOT confidential. Discretion does not apply to them, and applying it would destroy the requirement.** Job families, levels, level titles, step counts and every step's expectations are readable by **every employee** in the tenant. An employee reads their own roadmap and their own step; they may read the *generic* expectations of **every** step in **every** family, including ones they are not on | The owner's stated purpose is *transparency for the trainee*. The ten rules above exist to protect money; pointing them at job content by reflex would produce a "transparency" feature nobody can see. **The boundary is exact: the step's expectations are public within the tenant; the step's pay point is money** (D-R9) |
| **D-R12** | **(A1) No rating, score, percentage, progress indicator or comparative ranking appears on any level, step or roadmap surface, for any role** — including HR and including a "just for managers" view | R-17. This is a scope boundary enforced in the UI because it is the boundary that will be eroded by reasonable-sounding increments. §25 states it in full, with the specific next requests it refuses |

### 3.4 The tenant switch off-state (KAN-188 / R7 / D6)

Following the `admin/analytics_locked.html` precedent — a real screen, never a 403, never a redirect.

**Nav:** absent. `has_feature_access('compensation')` will AND the tenant switch after KAN-188, so the item simply
does not render. The locked screen is reached only by a direct URL or an old bookmark.

```
                              🔒
              Compensation isn't enabled for Acme Corp

   Your organisation doesn't have the Compensation module. While it is off,
   the portal doesn't show or store anyone's pay.

   Contact your Super Admin to enable it.

                      [ ← Back to Dashboard ]
```

`<h2>` is `Compensation isn't enabled for Acme Corp` and receives focus on load (`tabindex="-1"`). One route out.
Nothing actionable. The company's own name is in the heading because a SYSTEM_ADMIN switching tenants needs to know
*which* company they are looking at.

**SYSTEM_ADMIN bypass, signposted rather than silent** (SPM D6 requirement 3). A SYSTEM_ADMIN working in a company
where the feature is off sees the normal screen **with a persistent amber bar directly under the topbar**,
`role="status"`, not dismissible:

> ⚠ **Compensation is switched off for Acme Corp.** You can see this because you are a System Admin. Nobody else in
> this company can. `[ Turn it on for Acme Corp → ]`

Bypassing a commercial switch without knowing you are bypassing it is how a demo shows a customer a feature they
have not bought.

**Demo-data banner (SPM D8 safeguard 2).** While the environment is demo-grade, every compensation surface carries a
second persistent bar, grey `#f1f5f9` / `#475569`, `role="status"`, below any tenant bar:

> **Demo environment — every salary here is made up.** Don't enter a real one. *(This banner goes away when the
> portal is running on real data, and that change runs the security phase first.)*

The second sentence is deliberate: it is the only place a build-team member meets trigger T5 at the moment they are
about to trip it.

### 3.5 The shoulder-surfing case — an HR admin in an open-plan office

The threat is a **bystander**, not the user, so the answer is not more permission checks; it is layout and one
control.

1. **No hero numbers.** Salary never renders larger than body text (§2.6a). The largest thing on the profile is
   still the person's name.
2. **`Hide amounts`** (§2.6c), persisted per browser, with idle auto-hide.
3. **Amounts are never the first thing on a page.** On the profile, the Compensation card sits below Personal Info
   and Reporting Structure; on the hub, the Overview tab leads with coverage percentages, not figures.
4. **Never in the browser tab title, never in a flash that persists across a page load, never in a toast that
   outlives the dialog.** A flash renders in the chrome and survives navigation; a pay figure must not.
5. **Print and screenshot are treated as intentional** and stamped (§2.6c).
6. **The equity queue's default sort is by age of finding, not by size of gap** — so the top of the most-shared
   screen in the epic is not a ranked list of the most underpaid people in the company.

### 3.6 Partial data is the normal state, not the edge case (D7)

Per D7 the product runs for a long time at partial coverage, and **the partial state determines whether this is
trusted**. Every surface therefore has a designed partial state, tabulated per screen below, and three global
rules:

- `No salary recorded` always carries the sentence `This is not a zero — the portal has no figure for <first name>
  yet.` the first time it appears on a page. Repeating it on every row would be noise, so it is a card-level or
  table-level line, not a per-row one.
- **Every count of "compared" states what was excluded and why**: `12 compared · 3 excluded (1 contractor, 2 with
  no salary recorded)`.
- **"Nothing found" is never rendered without "what was looked at"** (§14.4). "No findings ✓" at 40% coverage is
  the most dangerous screen in this epic.

---

## 4. Information architecture

> ⛔ **AMENDED by A1.** The job ladder moves **out of the Administration section and into main Navigation**, at
> its own route, because it is now something every employee reads. Leaving it as a tab inside an admin page
> gated on a pay permission would have been the single clearest way to build the owner's transparency
> requirement and then hide it. Two profile cards change gate; two new surfaces appear.

```
Sidebar › Navigation
  Dashboard
  Employee Directory
  My Team
  Org Tree
  Position Changes
  Job Architecture      ← NEW (A1) · {% if has_feature_access('job_architecture') %}
                          Seeded r for EVERY role — this is an employee-facing item, not an admin one
  Vacation …

Sidebar › Administration
  Admin Panel
  Vacation Types
  Change Workflow
  Compensation          ← NEW · {% if has_feature_access('compensation') %}
  Pay Equity            ← NEW · {% if has_feature_access('pay_equity') %}   (KAN-201)
  Analytics
  Skills Intelligence

/ladder                             the ladder as a READING surface — families, levels, step expectations.
                                    Editing controls appear inline for job_architecture:w; the money column
                                    appears for compensation:w (§3.7, §6, §23)
/ladder/<family>/<level>/<step>     one step's expectations, deep-linkable — the URL a manager pastes into a
                                    message and an employee bookmarks

/compensation                       tabs: Overview · Level assignment · Fitted-step review (A1) ·
                                          Salary bands · Import · Export (A1) · Settings
                                    ⛔ the "Job ladder" tab is GONE — it is /ladder now
/compensation/equity                the findings register (its own nav item, its own feature code)

Employee profile gains, in the LEFT column, in this order:
  Personal Info
  Reporting Structure
  Job Level            ← NEW (KAN-191/192)   job_architecture:r   (A1: was compensation:r)
                         · the step's PAY POINT inside it stays compensation:r
  Compensation         ← NEW (KAN-193)       compensation:r  · row-scoped
  Lifecycle History    (EP38)

Your own profile gains, in the RIGHT column, above Skills:
  Your level and next step  ← NEW (A1, KAN-207)  job_architecture:r · self-scoped   §22.3
  My Pay                    ← NEW (KAN-194)      compensation_self:r

templates/employees/my_team.html gains a "next-step roadmaps" strip (A1, KAN-207) — §22.2.
templates/org_change/_move_modal.html gains one Pay block (KAN-196) and one Job level block (KAN-197).
```

**Why `/ladder` is main Navigation and not an admin tab.** Three reasons, in order of weight. (1) Its audience is
every employee — an item under "Administration" is read as "not for me" even when it is reachable. (2) Its
permission is a different code with a different default, and nav grouping that contradicts the permission model
teaches users the wrong mental model. (3) It has a deep-linkable child route that a manager will paste into a
conversation; a tab inside a six-tab admin page cannot be linked to a single step.

**Why the two new employee-facing surfaces are separate cards and not one.** `Your level and next step` is job
content (`job_architecture`); `My Pay` is money (`compensation_self`). A tenant may switch either off. Merging
them would make one card whose content and gate change shape — and would put an employee's salary and their
manager's expectations of them in the same visual object, which is exactly the association §25 exists to avoid.

**Why two nav items and not one.** `compensation` and `pay_equity` are different feature codes with different
audiences (SPM D5.1); a tenant may grant a works-council representative the findings register without granting the
pay record. One nav item gated on two codes would either over- or under-show. Two items, each gated on its own
code, is the only expression that matches the permission model.

**Why the hub is tabbed and not six nav items.** It is one administrator doing one job — standing the capability up
and keeping it current. Six sidebar entries for a feature most tenants configure twice a year is how nav sprawl
starts (the same argument that put departure reasons inside `/onboarding` in EP38 §7.1).

**Tab order is task frequency, not build order.** Overview is the weekly screen (coverage, deferred decisions); the
ladder is used twice a year. A tab a user has no permission for is **not rendered**; if only one tab remains the
strip is not rendered at all.

---

## 5. Journey maps

### 5.1 HR Administrator — standing it up from nothing (the adoption cliff, R-2)

| Stage | Goal | Today | Pain | What this design does |
|---|---|---|---|---|
| Discover | "We've been told to get pay into the portal" | Nothing exists | No idea what the first step is, or how big the job is | Overview tab opens on **two coverage meters at 0%** and a single next action, `Start with the job ladder →` |
| Start | Describe the jobs | Spreadsheet of 41 titles | A blank configurator with unfamiliar vocabulary | §6.2 first-run panel defines family/level/step in three lines and offers a **worked example** rather than an empty grid |
| Do the bulk | Get 146 people onto levels | — | 41 + 75 free-text titles, one at a time, is a week | §7 maps **by title, sorted by headcount**, with bulk apply and a CSV round-trip. The progress bar counts **people**, not titles |
| Load pay | Get salaries in | — | An importer that half-works and silently overwrites | §9.4 dry-run → diff → commit, atomic, with the zero/blank rows rejected **at preview** |
| Know when done | "Are we there?" | — | No definition of done | Overview states the equity gate: `You are 18% away (26 more people)` |
| Keep it true | Individual corrections | — | Re-uploading a file to fix one row | `Record a change…` on the profile, always available |
| Prove it later | "Why is Ravi on £X?" | — | Nothing | §14.5 timeline, joined to audit by correlation id |

**Friction I am deliberately accepting:** the mapping screen is a long sitting. The mitigation is ordering by
headcount and persisting progress, not making the job smaller — it *is* a data project (SPM R-2) and pretending
otherwise would design a screen that lies about the work.

### 5.2 Manager — pay at the moment of a move

| Stage | Goal | Pain | What this design does |
|---|---|---|---|
| Discover | Move Ravi to Ana's team | — | Unchanged: drag, profile `Transfer…`, or directory `⋯` |
| Decide | "Does his pay change?" | Today: nobody asks, so nobody answers | One three-option radio, nothing pre-selected, in the dialog they are already in |
| Common case | No pay change | Fear of a heavier flow | **One click, no scroll, no expansion** (§10.1, with the measurable constraint) |
| Understand | "Who approves this now?" | Chain changes when pay is added, invisibly | The chain sentence and the request-type line update live |
| Blocked | An approver can't see pay | Would be a stalled request | Refused at create with the fix named and a one-click escape hatch |

### 5.3 Employee — seeing their own pay

| Stage | Goal | Pain | What this design does |
|---|---|---|---|
| Discover | "What does HR have for me?" | Distrust of any portal touching pay | **My Pay** on their own profile, plain language, one card |
| Understand | "Is this right?" | A portal figure that disagrees with the payslip | Explicit: `This is not a payslip` and where to go if it looks wrong |
| Context | "Am I paid fairly?" | — | Position in range **in words**, no comparison to any colleague, ever |
| Not designed | "When do I get a rise?" | — | **No forward-looking language anywhere** (§9.2). The card answers what is, never what will be |

### 5.3a *(A1)* The employee — the ladder as transparency, not as HR configuration

**This is the journey A1 added, and it is the one that decides whether the owner got what he asked for.** The
persona is a trainee software engineer at step 1.2, six months in, with no interest whatsoever in a job
architecture. Charter §1's employee: *trust, clarity, privacy, mobile-first, plain language.*

| Stage | Their goal | Without this | What this design does |
|---|---|---|---|
| **Discover** | "What am I, here?" | The portal shows a free-text job title somebody typed once. Nothing says what it means | Their own profile card leads with **`Trainee Software Engineer · step 1.2`** and one plain sentence of what step 1.2 means — not a code, not a number they have to decode |
| **Understand** | "What does the next step actually need?" | An answer that lives entirely in one manager's head, and changes when the manager does | The same card shows **step 1.3's expectations**, authored once by the company and identical for everyone on that rung. `[ See the whole ladder → ]` for the curious |
| **Personalise** | "What do *I* need to do?" | A conversation in a room, remembered differently by two people three months later | **Their manager's next-step roadmap**, written for them, visible to them, versioned — so *"what did we agree in March"* has an answer that is not a memory |
| **Agree** | "Is this what we said?" | A plan they were told about | `Confirm we discussed this` — a recorded acknowledgement, plus a way to say **"we haven't discussed this yet"** without it being a refusal |
| **Track** | "Am I getting anywhere?" | — | **Deliberately nothing.** No progress bar, no completion, no score. The card shows where they are and what the next rung asks for. §25 explains why that emptiness is the design |
| **Trust** | "Is this a promise?" | An implied contract nobody meant to make | Every forward-looking sentence names the decision and the decider: *"Moving to step 1.3 is something you and Marcus decide together at a review."* |
| **Pay** | "Do I get more for doing more?" | The owner's actual concern: the responsibility moves and the pay does not | Not answered on this card, and that is deliberate — the step's **expectations** are theirs to read, the step's **pay point** is money (D-R9/D-R11). What they get is `My Pay`'s position-in-range sentence, and a company-side check (Check A′) that tells HR when the pay never followed |

**The friction I am accepting.** An employee sees their step's expectations and *cannot* see what that step is
worth. That is uncomfortable and I am not going to pretend otherwise — it is the direct consequence of D5, which
the SPM owns and the owner has not revisited. It is recorded as **UX-A1-Q3** rather than designed around.

### 5.4 Pay-equity responsible — working a register, not a task list

| Stage | Goal | Pain | What this design does |
|---|---|---|---|
| Discover | Something needs looking at | An alert storm that gets muted (R-1) | Capped bell section, one row per condition, no re-announcement |
| Triage | "Which of these is mine?" | A shared queue nobody owns | An **owner** column and a `Take this` action — a recorded act, not a read |
| Judge | "Is this justified?" | A number with no context | Group drill-down: who is in it, who was excluded and why, coverage, and the caveats in plain language |
| Record | Close it properly | One-click dismiss | Category + mandatory explanation + validity window shown before saving |
| Trust | "Will it come back?" | Re-firing identical findings | A re-fired finding is labelled **Re-opened** with the reason, and shows the previous justification |

---

## 6. KAN-190 — The ladder configurator *(and, after A1, the ladder as a reading surface)*

> The hardest screen in the epic. A tenant defines families, levels, titles and step counts **from nothing**, in an
> order that makes sense before they know the vocabulary. The empty state matters more than the populated one.
>
> ⛔ **AMENDED by A1, substantially.** Three changes, and the third changes what kind of screen this is.
> **(1)** Steps start at **`.0`** and `step_count` means *increments above entry*, so a level with
> `step_count = 5` has **six** values `1.0 … 1.5`. **(2)** The count is configured **per level, with no default**
> — trainee→junior and junior→mid are genuinely different distances. **(3)** Every step now carries **authored
> expectations an employee reads**, so this stopped being a structural editor and became a **content** editor
> with an audience outside HR (§6.9). It also moved: `/compensation` → **`/ladder`**, in main Navigation.

### 6.1 Purpose, entry points and audiences

**Purpose, restated after A1 — it has two now, and they pull in different directions:**
1. *(unchanged)* describe the shape of the jobs in this company, so level changes have rungs and the pay check
   has a reference; and
2. *(A1)* **publish what each rung means, to everybody who works here.**

**Nothing about any person changes here** — and the screen says so, twice.

**Entry:**
- **Read:** sidebar → **Job Architecture** (`/ladder`), for every employee. Also from the profile Job Level card's
  `See the whole ladder →`, from a roadmap's `What step 1.3 means →`, and from a deep link
  `/ladder/engineering/1/3` that a manager can paste into a conversation.
- **Edit:** the same page. Editing affordances appear inline for `job_architecture:w`; the money column appears
  for `compensation:w` (§23). There is no separate "edit mode" page — a second URL for the same content is how
  the published version and the edited version drift.
- Also from Level assignment's empty state (`You need a ladder before you can put anyone on it.
  [ Build the ladder → ]`) and from `/compensation` Overview's first-run next action.

**Gates (A1 — three, on one page, per §3.7):**

| Part of the page | Gate | Absent-not-disabled for |
|---|---|---|
| Families, levels, titles, step counts, **step expectations** — reading | `job_architecture:r` | everyone else (the nav item does not render) |
| The same — editing | `job_architecture:w` | `r`-only holders see a complete, clean, read-only ladder with **no controls at all** |
| Base pay point, step increment, computed step pay points | `compensation:r` / `:w` | **the whole money column is absent** — including its header. A `job_architecture:w` holder without `compensation:r` sees a page that reads as finished |

### 6.2 Empty state — the first-run panel

Rendered when the company has no job families. It is a panel, not a blank editor.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  Your company doesn't have a job ladder yet.                                  │
│                                                                               │
│  A job ladder describes the jobs in your company:                             │
│    • a job family — a discipline, like Engineering or Finance                 │
│    • levels inside a family — the rungs. Each level has its own job title.    │
│    • steps inside a level — smaller moves between one job and the next.       │
│      Everyone starts a level at step .0 and climbs: 2.0, 2.1, 2.2 …           │
│    • what each step means — the responsibilities it carries. You write these, │
│      and everyone in your company can read them.                              │
│                                                                               │
│  Nothing here changes anyone's job, title or pay. You're describing the        │
│  shape; you put people on it in Level assignment, and that's a separate step. │
│                                                                               │
│      [ Start from a worked example ]     [ Build it from scratch ]            │
│                                                                               │
│  Neither is permanent — you can rename, add and reorder anything until people │
│  are on it.                                                                   │
└───────────────────────────────────────────────────────────────────────────────┘
```

**(A1) The fourth bullet is the one that changes the job in front of them**, and it deliberately says *"everyone
in your company can read them"*. An HR admin who discovers at level three that they have been writing published
content will write the first two differently from one who was told before they started.

- **`Start from a worked example`** stages one family, three levels and five steps each, with real titles
  (`Engineering` · `L1 Software Engineer` · `L2 Senior Software Engineer` · `L3 Staff Engineer`), **one worked
  step expectation on 1.0 and 1.1 so the shape of the content is visible** (A1), and a dismissible
  amber banner: `This is an example. Rename or delete anything — nothing is saved until you press Save ladder.`
  A blank grid is the single biggest cause of abandoned configuration, and SPM OQ-4 explicitly wants a worked
  example rather than an opinionated shipped ladder.
- **`Build it from scratch`** stages one empty family with one empty level, focus in the family-name field
  (mirroring `admin/org_change_workflow.html:98`'s `if (!steps.length) addStep()`).
- **Neither option writes anything.** Both land in the staged editor; the Review dialog (§6.5) still runs.
- **Never another company's ladder and never a global default** — `CLAUDE.md`'s empty-state rule, at higher stakes.
  A company with no ladder shows this panel, not Acme's levels.

### 6.3 Populated layout — master/detail

```
┌ Job Architecture ────────────────────────── [ 3 unsaved changes ] [ Save ladder ] ┐
│  How jobs are organised at Acme Corp.                                             │
│                                                                                   │
│  Job families            │  Engineering                              [ Rename ]   │
│  ────────────────────    │  ─────────────────────────────────────────────────     │
│  ▸ Engineering    3 lvls │                                            │ money col │
│  ▸ Finance        2 lvls │  ⠿ Level 1  [ Trainee Software Engineer  ] │ base      │
│  ▸ Sales          0 lvls │      Steps to the next level [ 5 ▾ ]       │ [€48,000] │
│                          │      1.0 · 1.1 · 1.2 · 1.3 · 1.4 · 1.5     │ +[5.0]%   │
│  + Add job family        │      ✎ 6 of 6 steps described   12 people ⋯│ /step     │
│                          │                                            │           │
│                          │  ⠿ Level 2  [ Junior Software Engineer   ] │ [€62,000] │
│                          │      Steps to the next level [ 3 ▾ ]       │ +[4.0]%   │
│                          │      2.0 · 2.1 · 2.2 · 2.3                 │ /step     │
│                          │      ⚠ 1 of 4 steps described    8 people ⋯│           │
│                          │                                            │           │
│                          │  + Add level                                           │
│                          │                                                        │
│                          │  Levels go from the bottom up. Level 1 is the most      │
│                          │  junior. The level's title is the job title people      │
│                          │  see in the directory and the org tree. Everyone        │
│                          │  starts a level at step .0 and climbs from there.       │
└───────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Control | Rules |
|---|---|---|
| Family list | `<ul>` of buttons, one selected | Selected family is `aria-current="true"`. Count is levels, not people |
| Family name | text, required, ≤80, unique in company | `Give this job family a name.` / `You already have a job family called Engineering.` |
| Level ordinal | **derived from position, never typed** | Renumbering on reorder/delete is automatic and previewed |
| Level title | text, **required**, ≤120, unique within the family | This becomes the canonical job title (CFL-42-4) |
| **Steps to the next level** **(A1)** | `<select>` 1–12, **no default — the placeholder is `— How many? —` and it is required** | See below |
| **Step value preview** **(A1)** | static, live | `1.0 · 1.1 · 1.2 · 1.3 · 1.4 · 1.5` — **every value listed, entry step first**, so "5" can never be misread as five rungs. Each value is a link to §6.9's editor for that step |
| **Expectations progress** **(A1)** | `✎ 6 of 6 steps described` / `⚠ 1 of 4 steps described` | The `⚠` is a word-and-glyph nudge, not a blocker. Links to §6.9 |
| People count | chip, links to Level assignment filtered to that level | `job_architecture:r`. It is a headcount, not pay |
| **Money column** **(A1)** | base pay point + increment, §23 | **Absent in full, header included, without `compensation:r`** |
| Reorder | `⠿` handle **and** the `⋯` menu | See §6.6 — no pointer-only path |
| Row menu `⋯` | `Move up` · `Move down` · `Rename` · **`Describe the steps…`** · `Delete level` | `Delete level` last and in `#b91c1c`, per `directory.html`'s destructive-last ordering |

**(A1) Why there is no default step count, and how the control says so.** The SPM withdrew "default 5" because
the count expresses *how far apart two positions are*, and trainee→junior is not the same distance as
junior→mid. A default would be answered by inertia — the same reason the pay question in §10 has nothing
pre-selected. So the select opens on `— How many? —`, and until it is answered the level row carries a muted
line rather than an error (an unfinished new row is not a mistake):

> `How many steps between this level and the next one? Most companies use 3 to 5.`

Validation only bites at save: `Level 2: choose how many steps there are to the next level.`

**(A1) The six-values-for-a-count-of-five arithmetic is displayed, never explained.** The preview row lists every
value. An admin who sets `5` and sees `1.0 · 1.1 · 1.2 · 1.3 · 1.4 · 1.5` needs no sentence about off-by-one, and
an admin who expected five values sees the sixth immediately, at the point of the choice. The select's
`aria-describedby` carries `Six steps: 1.0 to 1.5.`

**(A1) The mid-ladder insertion limitation is stated here, at the point the ladder is defined** (OQ-BA-2, and
SPM standing rule §13.5.1 — consequences where the choice is made). A permanent muted line under `+ Add level`:

> `You can add a level at the top of a family at any time. Inserting one in the middle later isn't supported in
> this release — it would renumber everybody above it. Worth a minute now to leave the room you'll need.`

The explanatory paragraph under the list is permanent, not a tooltip. Three sentences that answer the three
questions every first-time configurer asks ("which way is up?", "what does the title do?" and, after A1, "where
does someone start?") are cheaper than a help page.

### 6.4 Destructive and structural cases — the part that must not be guessed

**(a) Delete a level with nobody on it.** In-page confirm dialog (never `confirm()`):

> **Delete level 3, Staff Engineer?**
> No one is on this level. Deleting it renumbers Staff Engineer's levels above it — level 4 becomes level 3, and
> level 5 becomes level 4.
> `[ Cancel ]  [ Delete level ]`

**(b) Delete a level with people on it — blocked, with the fix named.** EP38's blocker pattern: red
`#fef2f2`/`#fecaca`/`#b91c1c`, `role="alert"`.

> ⚠ **You can't delete Staff Engineer — 12 people are on this level.** Move them to another level first, then come
> back. `[ See who is on this level → ]`

**Never a cascade.** There is no "they will become unlevelled" option: silently un-levelling twelve people removes
them from every comparison group and from the coverage meter, and nobody would notice.

**(c) Reduce the step count below an occupied step — blocked, same shape.**

> ⚠ **You can't reduce Staff Engineer to 3 steps — 4 people are on step 3.4 or 3.5.** Move them to a lower step
> first. `[ See the 4 people → ]`

**(c2) *(A1)* Reduce the step count when the removed steps have expectations written but nobody on them — allowed,
and it must say what it throws away.** Expectations are authored content, sometimes a morning's work by an HR
director, and deleting them as a side-effect of changing a number would be indefensible.

> **Reduce Staff Engineer from 5 steps to 3?**
> Steps 3.4 and 3.5 go. Nobody is on them.
> **You've written expectations for 3.4 and 3.5. Those will be deleted.** `[ Read them first → ]`
> `[ Cancel ]  [ Remove 3.4 and 3.5 ]`

**(c3) *(A1)* Increase the step count — allowed, never blocked, and it creates undescribed steps.** The new steps
appear immediately with the `⚠ n of m steps described` counter updated, and a `role="status"` line:
`Steps 3.4 and 3.5 added. They have no expectations yet — anyone reading the ladder will see them as
"Not described yet". [ Describe them now → ]`

**(c4) *(A1)* Changing the step count changes what people are on.** A level's occupied steps do not move, but the
*meaning* of "top step" does — someone at 3.3 in a 5-step level is mid-ladder; in a 3-step level they are at the
top and the §8.4 signal fires. The Review dialog (§6.5) states this explicitly, because it is a consequence that
lands in somebody else's notification bell an hour later.

**(d) Reorder once assignments exist.** SPM D3 makes ordinal position immutable once assignments exist. Moving an
empty level past an occupied one changes the occupied level's ordinal too, so the lock is **per family, not per
level**: *once any level in a family has an assignment, that family's level order is fixed.* (This is a design-level
tightening of the rule; §19 UXQ2 routes it to the BA.)

The reorder handles and the `Move up`/`Move down` items are **not rendered** for a locked family — not disabled —
and the family header carries one muted line:

> `Level order is fixed — 20 people are on this ladder. You can still rename levels, change step counts and add a
> level at the top.`

**(e) Rename a level that people are on.** Allowed, and the consequence is real: it changes the job title shown for
those people in the directory, org tree and search. That is exactly what the Review dialog exists for.

**(f) Delete a family.** Blocked if any of its levels has an assignment, using the (b) copy at family scope.
Otherwise the confirm names every level that goes.

### 6.5 Review changes — previewing the effect on people before saving

The editor is **staged**. Nothing is written until `Save ladder`, which opens a Review dialog modelled on
`admin/panel.html:470-504`.

```
┌ Review ladder changes ─────────────────────────────────────────────────── × ┐
│                                                                             │
│  What changes in the ladder                                                 │
│   + Job family "Finance" — new, with 2 levels                               │
│   ~ Level 2 renamed:  "Junior Software Engineer" → "Software Engineer II"   │
│   ~ Level 3 steps:    5 → 3                                                 │
│   − Level 5 "Principal Engineer" removed (nobody is on it)                  │
│                                                                             │
│  What changes for people                                                    │
│   • 8 people on level 2 will show the job title "Software Engineer II" in   │
│     the directory, the org tree and search.                                 │
│   • Level 3 goes from 5 steps to 3. Nobody moves, but 2 people at step      │
│     3.3 are now at the top of their level — their manager will be told      │
│     they're at the top step.                    [ See the 2 people → ]      │
│   • Steps 2.4 and 2.5 are new and have no expectations yet. Anyone reading  │
│     the ladder will see them as "Not described yet".                        │
│   • Nobody moves level or step.                                             │
│   • No one's pay changes.                                                   │
│   • No employee is notified about the ladder itself.                        │
│     [ See the 8 people → ]                                                  │
│                                                                             │
│  What everyone can read                                             (A1)    │
│   • Step expectations are visible to every employee as soon as you save.    │
│     4 steps you edited become visible; 2 new steps appear as undescribed.   │
│                                                                             │
│                                        [ Cancel ]   [ Save ladder ]         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**(A1) The third section is new and it is the one an HR admin most needs.** *What everyone can read* exists
because the ladder is now published content: an admin editing a half-finished step description must be told, at
the moment of saving, that the half-finished version becomes visible to the whole company. There is no draft
state and no separate publish step in this cycle — **save is publish**, and the dialog says so rather than
letting somebody discover it. *(A draft/publish cycle is recorded as UX-A1-Q1, not designed here: it doubles the
state model for a screen HR edits twice a year, and "your ladder is out of date because nobody pressed publish"
is a worse failure than a visible typo.)*

**(A1) The top-step consequence must be in the list.** Changing a number in a configuration screen and thereby
firing a notification into three managers' bells is exactly the kind of invisible consequence the Demo Gate's D4
list exists for.

Three copy rules, all load-bearing:

1. **Structure and people are separate sections.** The admin's question is not "what did I type", it is "what will
   this do to twelve human beings".
2. **State what does *not* happen.** "No one's pay changes" and "Nobody is notified" are the two fears, and saying
   so is what makes the save feel safe to take correctly — the same reasoning as EP38's "Keep his record" line.
3. **Zero-count clauses are omitted**, never rendered as "0 people affected".

**If the impact cannot be computed, saving is blocked** (EP38 E4 precedent):

> ⚠ `We couldn't work out who these changes affect.` / `Saving is blocked until we can — nothing has been changed.`
> `[ Try again ]`

Confirming a consequence we could not measure is not confirmation.

### 6.6 Keyboard reordering — specified up front, not retro-fitted

KAN-174 / F20 is the open defect where drag is the only path to a position change in the org tree. **EP42 does not
add a second instance of that defect.**

- The `⠿` handle is a `<button>`, `aria-label="Reorder level 2, Senior Software Engineer"`, in the tab order.
- With focus on it: `↑` / `↓` move the level; `Home` / `End` move it to the top / bottom of the family.
- Each move announces to `#live-status`: `Senior Software Engineer moved to level 3 of 5.`
- The `⋯` menu carries `Move up` / `Move down` as an equally complete path, for pointer users on touch and for
  anyone who does not discover the handle.
- **Pointer drag is optional sugar.** If it is implemented it must add nothing that the keyboard path lacks, and it
  must be suppressed under `prefers-reduced-motion` for the animation only.

### 6.7 Every state — ladder configurator

| # | State | Trigger | What the user sees |
|---|---|---|---|
| L1 | Loading | Tab opened | Two skeleton family rows + three skeleton level rows; `Save ladder` hidden (nothing is dirty); `#live-status` → `Loading your job ladder…` |
| L2 | Loading — impact | `Save ladder` pressed | Review dialog opens with skeleton lines under *What changes for people*; `Save ladder` in the dialog disabled; `#live-status` → `Working out who this affects…` |
| L3 | Saving | Confirmed | Button → `Saving…`, disabled; Cancel, `×` and Esc disabled |
| E1 | **Empty — no ladder** | No families | §6.2 first-run panel |
| E2 | Empty — family with no levels | Family selected, 0 levels | `Engineering has no levels yet. A family without levels can't be used.` + `[ + Add level ]` focused |
| E3 | Empty — read-only viewer, no ladder | `r` only, 0 families | `Your company hasn't set up a job ladder yet.` — **no build action**, because they cannot build one |
| PD1 | Partial — levels exist, nobody assigned | 0 assignments | Each row shows `0 people`; a card-level line: `Nobody is on this ladder yet. [ Put people on it → ]` |
| PD2 | Partial — family locked, others not | Mixed | Locked families show §6.4(d)'s line; unlocked families keep their handles |
| V1 | Validation — family name | Empty | `Give this job family a name.` |
| V2 | Validation — duplicate family | — | `You already have a job family called Engineering.` |
| V3 | Validation — level title | Empty | `Level 2: give this level a job title. It's the title people will see.` |
| V4 | Validation — duplicate title in family | — | `Level 4 has the same title as level 2. Two levels in the same family can't share a title.` |
| V5 | Validation — no levels | Family with none, on save | `Engineering has no levels. Add at least one, or remove the family.` |
| V6 | Validation — steps out of range | — | `Steps must be between 1 and 12.` |
| B1 | **Blocked — delete an occupied level** | — | §6.4(b) |
| B2 | **Blocked — shrink past an occupied step** | — | §6.4(c) |
| B3 | Blocked — impact not computable | Impact call fails | §6.5 |
| E4 | Error — load failed | Non-2xx | `We couldn't load your job ladder.` + `[ Try again ]`; the rest of the hub still works |
| E5 | Error — save failed | Server error | `We couldn't save the ladder, so nothing has been changed. Your edits are still on this screen — try again.` Every staged change preserved |
| E6 | **Conflict — someone else saved** | `409` | `Someone else changed this ladder while you were editing. Nothing of yours has been saved.` + the list of your staged changes so they can be re-applied + `[ Reload their version ]` |
| P1 | No `compensation` at all | — | Nav item absent; direct URL → flash + dashboard |
| P2 | `r` without `w` | — | Full read-only ladder; **no** handles, no `⋯`, no `+ Add`, no Save |
| P3 | Tenant switch off | KAN-188 | §3.4 locked screen |
| P4 | SYSTEM_ADMIN, no company selected | CC-12 | `Choose a company first. A job ladder belongs to one company, so the portal needs to know which one.` + `[ Close ]` |
| D1 | Disabled — Save | Nothing staged | `Save ladder` **hidden**, not disabled — matching `admin/panel.html:448`'s dirty-only button |
| S1 | Success | Saved | `#live-status` → `Job ladder saved. 3 families, 8 levels.`; the dirty chip clears; `✓ Saved` in `#15803d` beside the button for 4 s |

### 6.8 Accessibility — ladder configurator

- **Keyboard path:** tab strip (`role="tablist"`, arrows move, one tab stop) → family list (`↑`/`↓` between
  families, `Enter` selects) → `+ Add job family` → family Rename → for each level: reorder handle → title →
  steps select → people chip → `⋯` → then `+ Add level` → `Save ladder`.
- **Focus after structural change:** adding a level moves focus to its title field and announces `Level 4 added.`;
  deleting moves focus to the next level's title (or `+ Add level`) and announces
  `Staff Engineer deleted. 2 levels left.`
- **Semantics:** the level list is a `<ul>`, each row an `<li>` with an `aria-label` naming the level and title, so
  a screen-reader user always knows which rung they are on. The `Level 3` ordinal is `aria-hidden` and duplicated in
  the row label. The `1.1 … 1.5` preview is `aria-hidden` and expressed in the steps select's
  `aria-describedby` as `5 steps, shown as 3.1 to 3.5`.
- **Dialogs** per §2.5(a). Blockers `role="alert"`; the locked-family line `role="status"`.
- **Targets:** every control ≥24×24; below 768px the panes stack (families become a collapsed `<details>` picker),
  rows become two-line cards, and every control is ≥44px.
- **Contrast:** `✓ Saved` uses `#15803d` (5.01:1), **not** `#16a34a` — do not copy
  `admin/org_change_workflow.html:29`. Blocker text `#b91c1c` on `#fef2f2` (5.91:1); locked/warning `#b45309` on
  `#fffbeb` (4.84:1).
- **Never colour alone:** locked families carry the word `fixed`; blockers lead with `⚠`; the dirty chip carries the
  count in text.
- **Reduced motion:** no row-slide animation on reorder; the position change is announced instead.
- **(A1)** The `Steps to the next level` select's `aria-describedby` reads `Six steps: 1.0 to 1.5.` and updates
  when the count changes, announced through `#live-status`. An admin using a screen reader must not have to infer
  the sixth value from a visual preview row.
- **(A1)** The money column, when present, is a `<section aria-label="Pay points for Engineering">` so its
  absence for a `job_architecture`-only holder is a missing landmark rather than a silently shorter table.

---

## 6.9 *(A1)* The step-expectations editor — the ladder becomes content

> **The single biggest addition A1 makes to an existing screen.** *"each level will have it own responsibility
> and expectation."* Every step needs a description an employee can read, and writing 6 + 4 + 4 descriptions is
> a writing task, not a configuration task. The editor has to be built for someone drafting prose, and the empty
> state matters more here than anywhere else in the epic — because an undescribed ladder is a published promise
> of transparency with nothing behind it.

### 6.9.1 Purpose, entry, gate

**Purpose:** author, for each step of each level, the responsibilities and expectations that define it — once,
generically, for everybody who is ever on that step.

**Entry:** from the ladder, three ways — the `✎ 6 of 6 steps described` counter, any step value in the preview
row (`1.3`), or the row menu's `Describe the steps…`. Also from a deep link `/ladder/engineering/1/3`.

**Gate:** read `job_architecture:r` (everyone). Write `job_architecture:w`. **No compensation permission is
involved anywhere in this editor** — that is the point of the fourth code.

### 6.9.2 Layout — a step list beside one editor, because this is a drafting session

```
┌ Engineering · Trainee Software Engineer (level 1) ─────────── [ 2 unsaved ] [ Save ] ┐
│                                                                                      │
│  Steps            │  Step 1.2                                                        │
│  ───────────      │  ──────────────────────────────────────────────────────────────  │
│  ● 1.0  entry  ✎  │  A short summary                                                 │
│  ● 1.1         ✎  │  [ Works independently on well-defined tasks.               ]    │
│  ▶ 1.2         ✎  │  One sentence. This is what shows on someone's profile and       │
│  ○ 1.3         ⚠  │  in their manager's roadmap. 120 characters.                     │
│  ○ 1.4         ⚠  │                                                                  │
│  ● 1.5  top    ✎  │  What this step means                                            │
│                   │  ⠿ [ Picks up a defined task and finishes it without daily   ] ✕ │
│  4 of 6 described │  ⠿ [ Reviews a teammate's change and gives useful comments   ] ✕ │
│                   │  ⠿ [ Writes tests for their own work as a matter of course  ] ✕ │
│  [ Copy from… ▾ ] │  + Add an expectation                                            │
│                   │                                                                  │
│                   │  Anything else worth knowing (optional)                          │
│                   │  [                                                          ]    │
│                   │                                                                  │
│                   │  Everyone at Acme Corp can read this. 3 people are on step 1.2   │
│                   │  right now.                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Control | Rules |
|---|---|---|
| Step list | `<ul>` of buttons | `●` described · `○` not described (glyph **and** the `⚠` marker **and** the `4 of 6 described` count — never colour alone). `entry` and `top` are labels on `.0` and the last step, so the shape of the level is legible while drafting |
| **Summary** | text, ≤120, **required to count as "described"** | This is the one line that appears on the profile card, in the roadmap and in the register. It carries the most weight of any string in KAN-190 |
| **Expectations** | repeatable rows, ≤240 each, 1–12 rows, reorderable | Plain sentences. **Not checkboxes** (§25) — a checkbox implies completion tracking, and completion tracking is goal management |
| Extra notes | textarea, optional | For context that is not an expectation ("this step usually takes 6–12 months, but there's no clock") |
| **`Copy from…`** | select of other steps in this company | The realistic authoring pattern is *"1.3 is 1.2 plus two things"*. Copying stages an editable duplicate and announces `Copied 5 expectations from step 1.1. Edit them for 1.2.` It never links the two |
| Readership line | static, permanent | `Everyone at Acme Corp can read this. 3 people are on step 1.2 right now.` Stated at the point of writing, every time |

**Three copy rules for the author, shown as helper text and enforced at review, not by validation:**

1. **Write what the job involves, not how well someone is doing it.** Under the expectations list:
   `Describe the work, not the person. "Reviews a teammate's change" — not "reviews changes well".`
2. **No timeframes on an individual.** `Say what the step involves. How long it takes is between a person and
   their manager.`
3. **No ratings.** The word list in §2.3 is the review checklist; §25 is the reasoning.

### 6.9.3 Every state — the expectations editor

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | Step list skeleton (6 rows) + three skeleton expectation rows |
| L2 | Saving | `Save` → `Saving…`, disabled; the step list disabled so a click cannot lose the draft |
| **E1** | **Empty — no step described in this level** | The editor opens on `.0` with one blank expectation row focused, and a panel above it: `Nobody has described the steps in Trainee Software Engineer yet. Start with step 1.0 — what does somebody do on their first day at this level? You can come back to the rest.` **One step at a time is the instruction**, because "describe six steps" is what makes people close the tab |
| E2 | Empty — this step only | `Step 1.3 isn't described yet.` + `[ Copy from step 1.2 ]` as the primary action and a blank row below it |
| E3 | Empty — no levels at all | Editor unreachable; the ladder shows §6.2 |
| **PD1** | **Partial — the normal state for months** | `4 of 6 described` and `⚠` on the undescribed steps. **Partial is never blocked and never nagged more than once per screen** — a half-described ladder is more useful than none |
| PD2 | Partial — summary written, no expectations | Counts as described (the summary is the required part); the step list shows `●` with a muted `summary only` |
| PD3 | Partial — expectations written, no summary | Counts as **not** described, with the reason at the field: `Add a one-line summary — it's the line people see everywhere else.` |
| V1 | Validation — summary too long | `Keep the summary to one line — 120 characters. You have 148.` Live counter from 100 |
| V2 | Validation — empty expectation row | Silently dropped on save; not an error. An empty row is an abandoned thought, not a mistake |
| V3 | Validation — duplicate expectation in one step | `That's the same as the second expectation. Remove one or make them different.` |
| V4 | Validation — banned word | **Not blocked.** A `role="status"` nudge under the field: `"Exceeds expectations" reads like a rating. This is a description of the work, not an assessment of the person.` A block would be a false claim of enforcement (SPM standing rule §13.5.2) and would fight a legitimate use of "meets" in a sentence |
| E4 | Error — load | `We couldn't load the step descriptions.` + `[ Try again ]` |
| E5 | Error — save | `We couldn't save. Your text is still on this screen — try again.` **Draft preserved in memory for the session**, as EP38 §5.10 does for offboarding: losing three paragraphs to a network blip is not acceptable |
| **E6** | **Conflict — somebody else edited this step** | `Priya Nair saved a change to step 1.2 while you were writing. Yours hasn't been saved.` + both versions side by side + `[ Keep mine ] [ Keep theirs ]`. Two HR people drafting a ladder in the same week is likely, and silently overwriting a colleague's prose is the worst outcome available here |
| P1 | `job_architecture:r` only | Read-only: the step list and the rendered text, no fields, no `Save`, no `Copy from…` |
| P2 | No `job_architecture` at all | Nav item and route absent |
| P3 | Tenant switch off | §3.4 locked screen, worded for Job Architecture |
| S1 | Success | `✓ Step 1.2 saved.` + `#live-status` → `Step 1.2 saved. 5 of 6 steps described. Everyone can now read it.` The step list marker flips `○ → ●` |

### 6.9.4 Accessibility — the expectations editor

- **Keyboard path:** step list (`↑`/`↓` between steps, `Enter` opens — it is a `role="tablist"`-shaped pattern
  but a real list, so `aria-current="true"` marks the open step) → summary → each expectation row's reorder
  handle → its text field → its `✕` → `+ Add an expectation` → notes → `Copy from…` → `Save`.
- **Reordering is keyboard-first**, identical to §6.6: `↑`/`↓` on the focused handle, announced
  `Expectation moved to position 2 of 3.` No pointer-only path.
- Adding a row moves focus into it and announces `Expectation 4 added.`; removing announces
  `Expectation 2 removed. 2 left.` and moves focus to the next row (or `+ Add an expectation`).
- Switching steps with unsaved text does **not** discard it: the draft is held per step for the session and the
  step list marks unsaved steps with `•` and an `aria-label` suffix `, unsaved changes`.
- The character counter is `aria-live="polite"` and announces only at 100, 120 and over.
- Each expectation field's accessible name is `Expectation 2 for step 1.2`, so a screen-reader user always knows
  which of six steps they are drafting.
- Targets ≥24×24; below 768px the two panes stack (the step list becomes a horizontally scrolling chip row with
  the described/undescribed glyph on each chip) and every control is ≥44px.

---

## 6.10 *(A1)* `/ladder` as a reading surface — what an employee sees

> The same route, the same content, no editing affordances. **This is the deliverable the owner described**, and
> it is easy to build the editor and forget that the reader is the point.

```
┌ Job Architecture ────────────────────────────────────────────────────────┐
│  How jobs are organised at Acme Corp. Anyone here can read this.         │
│                                                                          │
│  You are here → Engineering · Trainee Software Engineer · step 1.2       │
│                                                                          │
│  Engineering                                                             │
│  ├ Level 1 · Trainee Software Engineer            6 steps · 1.0 – 1.5    │
│  │    1.0  Learning the codebase with close support                      │
│  │    1.1  Completes small changes with review                           │
│  │  ▶ 1.2  Works independently on well-defined tasks       ← you         │
│  │    1.3  Not described yet                                             │
│  │    1.4  Not described yet                                             │
│  │    1.5  Takes on work that spans more than one component              │
│  ├ Level 2 · Junior Software Engineer             4 steps · 2.0 – 2.3    │
│  └ Level 3 · Mid-level Software Engineer          4 steps · 3.0 – 3.3    │
│                                                                          │
│  Finance …                                                               │
│                                                                          │
│  This describes the jobs, not the people in them. Moving between steps   │
│  is something you and your manager decide together at a review.          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Design decisions, each with its reason:**

- **`You are here` is a breadcrumb, not a highlight of achievement.** It orients; it does not congratulate or
  compare. There is no "you have completed 2 of 6 steps", no bar, no percentage (D-R12).
- **Every family and every level is readable, not just yours.** An employee may look at Finance level 3. Job
  architecture published to only the rung you are on is not transparency, it is a keyhole — and the owner's word
  was *roadmap*. **D-R11 is explicit that this content is not confidential.**
- **`Not described yet`** is the honest partial state, shown to employees as well as admins. Hiding undescribed
  steps would make a half-built ladder look complete, and an employee who cannot see that 1.3 is undescribed
  cannot ask their manager about it. For a `job_architecture:w` holder the same line reads
  `Not described yet · [ Describe it ]`.
- **No pay anywhere on this page**, for anyone — not even a `compensation:r` holder in reading mode. Pay points
  live in the editing view's money column (§23) and on the Compensation surfaces. Putting a salary next to a job
  description on a page every employee reads would make the ladder a published pay scale, which is a decision
  nobody in this project has taken. *(UX-A1-Q3 records the tension honestly.)*
- **The closing sentence is load-bearing** and appears on every variant: *"This describes the jobs, not the
  people in them. Moving between steps is something you and your manager decide together at a review."* It is
  the anti-entitlement and anti-assessment sentence in one, and it is the ladder's equivalent of My Pay's
  "this isn't a payslip".
- **Mobile:** this is the EP42 surface most likely to be opened on a phone, from a link a manager sent. Levels
  become collapsible `<details>` (the employee's own level expanded by default), steps stack, and the deep link
  `/ladder/engineering/1/3` opens with that step expanded and focused.

**States:** *Loading* — skeleton of three levels. *Empty (no ladder)* — for a non-admin:
`Your company hasn't published a job ladder yet.` with no action and no admin language. *Empty (no family
described at all)* — the tree renders with every step `Not described yet` and one line at the top:
`Your company is still writing these.` *Employee not on a level* — the `You are here` line is absent, replaced by
`You're not on a level yet. Your HR team is still setting this up.` *Error* — `We couldn't load the job ladder.`
+ `[ Try again ]`. *Tenant off* — nav absent; §3.4 screen on a direct URL.

**Accessibility:** the ladder is a nested `<ul>` with `aria-label="Job families"`; each level is a
`<details>`/`<summary>` so it is keyboard-operable natively; the employee's own step carries
`aria-current="true"` and its accessible name ends `, your current step`; `Not described yet` is real text, not a
styling state. No colour-only distinction between described and undescribed.

---

## 7. KAN-191 — Level assignment and the title backfill

> 41 distinct titles over 46 people at Acme, 75 over 100 at Telia (SPM S2). **This screen decides whether the
> backfill finishes** (risk R-2). Everything about it is optimised for one sitting.
>
> ⛔ **AMENDED by A1, and the SPM has said the risk got worse.** An assignment now carries a **step**, not only a
> level; the backfill **fits the step to the pay** rather than dropping everyone at `.0`; and HR's review of the
> fitted steps is now the **gate on the entire equity feature** (SPM §14.2.5). R-2 was "map 116 titles"; it is
> now "map 116 titles **and** fit a step to each of 146 people". The mapping screen below is unchanged in shape;
> §7.9 is the new screen that carries the second half.
>
> **Why the fitted-step default is right even though it looks circular.** Placing everyone at `.0` would make
> every employee paid above the entry rate — which is most of them — a `PAY_ABOVE_STEP` finding in the first hour
> of the first tenant's use. Fitting the step to the actual pay is the ladder being fitted to reality, because
> reality came first. The screen has to say that out loud, or HR will read it as the system marking its own
> homework (§7.9.2).

### 7.1 Purpose, entry, gate

**Purpose:** put every active employee on a (family, level, step) so promotions have rungs and pay equity has a
grouping key. **This changes what job title people see** — and the screen says so before anything is saved.

**Entry:** `/compensation` → **Level assignment**. Also from the Overview meter's `[ Put people on levels → ]`, and
from a profile Job Level card's `Not assigned` state.
**Gate:** `@require_feature_access('compensation','w')`.

### 7.2 Layout — two sub-views, `By title` first

`By title` is the default because mapping a title covers everyone who holds it; `By person` exists for the
exceptions, and an exception-first design would make the bulk job feel infinite.

```
┌ Level assignment ───────────────────────────────── [ 4 unsaved ] [ Review & apply ] ┐
│  ( By title )  ( By person )                                                        │
│                                                                                     │
│  41 working titles · 46 active employees                                            │
│  People on a level  ██████░░░░░░░░░░░░░░  28%  (13 of 46)                           │
│  Biggest titles first — mapping these covers the most people.                       │
│                                                                                     │
│  ☐  Working title                    People  Level assignment                       │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│  ☐  Software Engineer                   5    [ Engineering ▾ ][ L1 ▾ ][ 1.1 ▾ ]  ✓  │
│  ☐  Senior Software Engineer            3    [ Engineering ▾ ][ L2 ▾ ][ 2.1 ▾ ]  ✓  │
│  ☐  Payments Platform Engineer          1    [ — Select a family — ▾ ]              │
│  ☐  Head of Logistics                   1    [ — Select a family — ▾ ]              │
│  …                                                                                  │
│                                                                                     │
│  [ Download titles (CSV) ]  [ Upload mapping (CSV) ]                                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Behaviour |
|---|---|
| **Sort** | Headcount descending, fixed. This is the design decision that makes the backfill finish: the 5-person title covers 11% of Acme in one action; alphabetical order would start at "Accountant". A secondary `Sort: A–Z` is offered but never the default |
| **Progress** | Counts **people**, not titles, and says both: `28% (13 of 46)`. Twelve titles can be 60% of the workforce, and a title-based percentage would understate progress and demoralise |
| **Family select** | Company's own families only. If none: the whole tab shows §7.5 E1 |
| **Level select** | Disabled until a family is chosen: `— Select a family first —` (matching `admin/register.html`'s dependent-select convention) |
| **Step select** **(A1 — replaced)** | ⛔ *Was: "defaults to step 1".* **Now the default option is `— Fit to pay —`**, with the permanent line: `Where someone has a salary recorded, we'll put them on the step whose pay point is closest to it. Where they don't, they start at .0 and you'll be asked to check them.` Explicit steps `.0 … .N` stay selectable for a title where HR knows better. Bulk-assigning a *specific* step is a pay-adjacent judgement that must not be made five people at a time by a dropdown default nobody read — which is precisely why the default is now "fit" rather than a number |
| **Row `✓`** | Marks the row staged, not saved. Staged rows get a `#f0fdf4` background and count into the dirty chip |
| **Multi-select** | Checkboxes + a sticky bulk bar `3 titles selected · [ Assign all to… ] [ Clear ]` — for the long tail of one-person titles, which is 30+ rows at Acme |
| **Filter** | `Show: All / Not yet assigned / Assigned` — `Not yet assigned` is what you use on the second sitting |

**By person** is a searchable list: name · working title · level (`Engineering · L2 · 2.3` or `Not assigned`) ·
`[ Assign… ]`. Same staged model, same review dialog. It is also the only place a step other than 1 can be set in
bulk-free isolation.

### 7.3 The two-title precedence, made visible

CFL-42-4 is open (BA + Architect), and the SPM's steer is *level title canonical, working title supplementary*. The
UI has to render something today, so this spec adopts the steer and states it once, here, for every surface:

| Situation | Directory / org tree / search / inbox | Profile |
|---|---|---|
| Level assigned, working title differs | `Senior Software Engineer` *(Payments Platform Engineer)* — canonical first, working title in parentheses, muted | Two labelled rows: `Job title` = level title; `Working title` = free text |
| Level assigned, titles identical | `Senior Software Engineer` once | One row, `Job title`, with a muted `Also the working title` |
| **No level assigned** | The working title alone, no parentheses | `Job title` row absent; `Working title` shown; Job Level card shows `Not assigned` |
| No level **and** no working title | `No job title recorded` | same |

**Never** show a level title as though it were typed by HR, and **never** show an empty parenthesis. If the BA
overturns the steer, this table is the single place to change.

### 7.4 Review & apply — the preview

Same staged/Review pattern as §6.5, because the consequence is the same class: a title change visible to the whole
company.

```
┌ Review level assignments ───────────────────────────────────────────────── × ┐
│                                                                              │
│  You are putting 9 people on a level                                         │
│   • 5 people with the working title "Software Engineer"                      │
│     → Engineering · level 1 · step 1.1                                       │
│   • 3 people with "Senior Software Engineer"                                 │
│     → Engineering · level 2 · step 2.1                                       │
│   • 1 person: Ravi Sharma → Engineering · level 3 · step 3.2                 │
│                                                                              │
│  What people will see                                                        │
│   • 8 of these people will show a different job title in the directory,      │
│     the org tree and search. Their working title doesn't change.             │
│     [ See the 8 changes → ]                                                  │
│   • Nobody's pay changes.                                                    │
│   • Nobody is notified.                                                      │
│                                                                              │
│  Effective from  [ 09/08/2026 ]                                              │
│  This is the date the assignment starts. It doesn't backdate anyone's pay.   │
│                                                                              │
│                                     [ Cancel ]   [ Apply to 9 people ]       │
└──────────────────────────────────────────────────────────────────────────────┘
```

The commit button is named after the act and carries the count (EP38 rule 6). Applying is **atomic** — 9 of 9 or
none — and the failure copy says so.

### 7.5 CSV round-trip

Because someone will want to do this in a spreadsheet with the HR director (SPM D7.1).

- **`Download titles (CSV)`** → `working_title, people, job_family, job_level, step` with the already-assigned rows
  pre-filled, the rest blank. It contains **no pay** and no employee names — it is a title list, so it is safe to
  email round an HR team, and the download states that: `This file has job titles and headcounts. It has no pay
  and no names.`
- **`Upload mapping (CSV)`** → the same dry-run → preview → commit shape as §9.4, with row-level errors:
  - `Row 7: there's no job family called "Enginering" in your company. Check the spelling, or add the family first.`
  - `Row 12: Engineering has no level 6. It has levels 1 to 3.`
  - `Row 19: level 2 has 5 steps, so step 2.7 doesn't exist.`
  - `Row 22: no one in your company has the working title "Solutions Architect II".`
  - `Row 30: this title appears twice in the file with different levels. Fix the file and upload it again.`
- A file that maps a title to a level in a **different company** is rejected wholesale, not row-by-row:
  `This file doesn't match your company's job ladder. Nothing has been imported.`

### 7.6 Suggestions — designed, and explicitly optional

A `Suggested` column (string similarity between the working title and the level titles) would meaningfully shorten
a 75-row sitting. It is **not in KAN-191's scope** as the SPM wrote it, so I am specifying the guardrails rather
than the feature, and flagging it as UXQ4:

- Column header helper: `Suggestions come from matching words in the title. They are guesses — check every one.`
- **Never auto-applied.** `Accept all suggestions` *stages* them; the Review dialog still runs and lists them
  separately under `9 assignments came from a suggestion`.
- Every suggested row is visually marked as suggested until the human touches it, and the marker is a word
  (`Suggested`) plus an icon, never colour alone.
- Charter §1 / role rule 5: an assistive suggestion about a person's job classification must be labelled,
  explainable and overridable. It must never be silently applied to 41 titles.

### 7.7 Every state — level assignment

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | Skeleton rows; progress bar `aria-busy="true"` |
| L2 | Applying | `Apply to 9 people` → `Applying…`, disabled; dialog un-dismissable |
| E1 | **Empty — no ladder** | Whole tab replaced: `You need a job ladder before you can put anyone on it.` + `[ Build the job ladder → ]` |
| E2 | Empty — no active employees | `Your company has no active employees to assign.` (the "Sam Cpmapny" tenant — 0 employees, 3 locations — is a real case, SPM S1) |
| E3 | Empty — everyone assigned | `Everyone is on a level.` + `100% (46 of 46)` + `[ Review assignments in "By person" ]` — the tab stays reachable, because leavers and joiners re-open it |
| E4 | Empty — filter finds nothing | `No titles match "archit".` + `[ Clear search ]` |
| PD1 | **Partial — the normal state** | Progress bar + `13 of 46`. Unassigned rows show `— Select a family —`, never a blank cell |
| PD2 | Partial — a title spans people in different states | `Software Engineer · 5 people (1 already on level 2)` with a muted `Assigning this title moves that person too.` — silently re-levelling someone already placed is the surprise to avoid |
| PD3 | Partial — employee with no working title | Grouped at the end under `No working title (3 people)`, assignable by person only |
| V1 | Validation — no family | `Choose a job family for "Payments Platform Engineer".` |
| V2 | Validation — no level | `Choose a level for "Payments Platform Engineer".` |
| V3 | Validation — nothing staged | `Nothing to apply yet. Assign at least one title.` |
| V4 | Validation — effective date | `The effective date can't be in the future.` *(placement dates are constrained while there is no scheduler — EP38 R5.6)* |
| E5 | Error — load | `We couldn't load the titles in your company.` + `[ Try again ]` |
| E6 | Error — apply | `We couldn't apply these assignments, so nothing has changed. Your choices are still on this screen — try again.` |
| E7 | Conflict — ladder changed underneath | `The job ladder changed while you were working — level 3 no longer exists. Nothing has been applied.` + `[ Reload ]` |
| E8 | Error — CSV upload | Per-row list (§7.5); `Nothing has been imported.` in bold above it |
| P1 | No `compensation:w` | Tab absent |
| P2 | Tenant off / SA no company | §3.4 / §6.7 P4 |
| S1 | Success | Dialog → `✓ 9 people are now on a level.` `Coverage is now 48% (22 of 46).` `[ Keep assigning ] [ Done ]`; `#live-status` gets both sentences |

### 7.8 Accessibility — level assignment

- **Keyboard path:** sub-view tabs → filter → search → select-all checkbox → per row: checkbox → family → level →
  step (each select's accessible name includes the title, e.g. `Job family for Software Engineer`) → bulk bar when
  present → `Download titles` → `Upload mapping` → `Review & apply`.
- The table is a real `<table>` with `<th scope="col">`; the checkbox column header is
  `<th><span class="sr-only">Select title</span></th>`; the select-all is
  `aria-label="Select all 41 titles"` and announces `12 titles selected.`
- Staging a row announces `Software Engineer assigned to Engineering level 1 step 1.1. 4 changes not yet applied.`
- Progress bar: `role="progressbar"` with `aria-valuenow/min/max` and `aria-label="People on a level"`. The
  `28% (13 of 46)` text is the accessible truth; the bar supports it.
- Below 768px the table becomes stacked cards (title + count on line 1, three full-width selects below), the bulk
  bar sticks to the bottom, and every control is ≥44px.

---

## 7.9 *(A1)* The fitted-step review — the gate on the whole equity feature

> **`/compensation` → Fitted-step review.** Check A′ does not run for a company until a `job_architecture:w`
> holder has explicitly marked the fitted steps reviewed (SPM §14.2.5). One deliberate human act, replacing the
> 80% coverage gate. It is also the second half of the adoption cliff: **146 people, one at a time, unless the
> screen is designed to make the obvious cases disappear.**

### 7.9.1 Purpose, entry, gate

**Purpose:** let HR confirm, correct or override the step the system fitted to each person's pay, and then say
"we're happy" once — which is what turns the equity check on.

**Entry:** `/compensation` → **Fitted-step review** tab. Also from the Overview's Pay equity block
(`Pay equity is waiting on your step review. 118 of 146 confirmed. [ Continue → ]`) and from the equity
register's not-yet-running state (§14.4 E1).

**Gate:** `compensation:r` (the fit is derived from pay, so it is money — D-R9) **plus** `job_architecture:w`
(confirming a step is a job-content write). A holder of one without the other does not see the tab.

### 7.9.2 Layout — designed to be finished, not to be thorough

```
┌ Fitted-step review ──────────────────────────────────── [ 👁 Hide amounts ] ┐
│                                                                             │
│  We've put each person on the step whose pay point is closest to what they  │
│  are actually paid. That's deliberate: the ladder is being fitted to how    │
│  you pay people today, because that came first. Check the ones we've        │
│  flagged, correct anything that's wrong, then confirm.                      │
│                                                                             │
│  118 confirmed · 21 need a look · 7 have no pay recorded    ███████░░  81%  │
│                                                                             │
│  Show: ( Needs a look )  ( No pay recorded )  ( Confirmed )  ( Everyone )   │
│                                                                             │
│  Person              Level              Pay        Fitted   Why             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Ravi Sharma         Eng · Trainee SE   €72,000    1.5 ▾    ⚠ above the top │
│                                                             step by 4.2%    │
│                                                    [ Confirm ] [ Fits ✓ ]   │
│  Ana Costa           Eng · Junior SE    €63,100    2.1 ▾    within 0.2%     │
│  Otto Braun          Fin · Analyst      —          0.0 ▾    ⚠ no pay        │
│                                                             recorded        │
│  …                                                                          │
│                                                                             │
│  [ Confirm all 97 exact fits ]                                              │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  [ Mark the step review complete ]   Turns on the pay-equity check.         │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Design decision | Why |
|---|---|
| **The paragraph at the top is permanent and explains the circularity** | Without it, an HR admin reading "we fitted the step to the pay, now we'll check whether the pay matches the step" concludes the system is marking its own homework. The sentence that dissolves it is *"the ladder is being fitted to how you pay people today, because that came first"* — and it must be there on every visit, not in a first-run tooltip |
| **The default filter is `Needs a look`, not `Everyone`** | 97 of 146 will be an exact fit and looking at them is wasted time. Opening on 146 rows is how a 146-row review does not get done |
| **`[ Confirm all 97 exact fits ]` is a bulk action and the tolerance-exact ones are the only thing it touches** | This is the single most important control on the screen: it turns a 146-person job into a 21-person job. It is deliberately **not** "confirm all" — the flagged rows must be looked at |
| **`Why` is always populated, in words** | `within 0.2%` · `⚠ above the top step by 4.2%` · `⚠ below the entry rate by 7%` · `⚠ no pay recorded — placed at .0` · `⚠ two steps fit equally — took the lower` (the exact-tie case). A fitted step with no stated reason is a number HR cannot audit |
| **Ties resolve downward and say so** | An exact midpoint between 2.1 and 2.2 takes **2.1**. Rounding a person *up* a step manufactures a `PAY_BELOW_STEP` finding out of an arithmetic tie |
| **`No pay recorded` is a separate filter, not an error** | 7 people at `.0` because there is no salary is a *data* gap, not a fitting problem, and it is fixed on a different screen. The row offers `[ Record salary… ]` for `compensation:w` |
| **Per-row `[ Fits ✓ ]` and a step override in one control** | Confirming and correcting must both be one action from the row. Changing the step select marks the row corrected and reveals a required `Why? *` short text — an override of a computed value must carry its reason |
| **The completion button names its consequence** | `Mark the step review complete` with the muted line `Turns on the pay-equity check.` A button that switches on a compliance feature must say so |

### 7.9.3 Every state

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | Skeleton rows; the counters read `Counting…`; both bulk buttons hidden |
| L2 | Confirming in bulk | `Confirm all 97 exact fits` → `Confirming…`; a progress line; `#live-status` → `97 people confirmed.` |
| **E1** | **Empty — no ladder, or nobody assigned** | Tab replaced: `There's nobody on a level yet. [ Assign levels → ]` |
| **E2** | **Empty — no pay recorded for anybody** | `Nobody has a salary recorded, so there's nothing to fit a step to. Everyone has been placed at step .0.` + `[ Import salaries → ]` + `[ Mark the step review complete ]` **still available**, with the warning `You can turn the check on now, but with no pay recorded it won't find anything.` — honest, and it does not trap a tenant who genuinely wants levels without pay |
| E3 | Empty — filter finds nothing | `Nothing needs a look. [ Show everyone ]` |
| **E4** | **Complete — review already marked** | Header replaces the button with `✓ Step review completed by Priya Nair on 12 August 2026. Pay equity is running.` + `[ Reopen the review ]` (which requires a reason and is audited — turning the check *off* is as consequential as turning it on) |
| **PD1** | **Partial — the normal state** | The counters. Progress counts **confirmed people**, and its denominator is everyone with a level |
| PD2 | Partial — level has no pay points configured | Rows for that level read `Can't fit — no pay points set for Engineering level 1 in Germany.` + `[ Set pay points → ]` for `compensation:w`. **Never a silent `.0`** |
| PD3 | Partial — person has a level but no pay market | `Can't fit — no pay market for this person's location.` + `[ Set up pay markets → ]` |
| PD4 | Partial — new joiner after the review completed | Appears in a `3 people joined since you completed the review` strip with `[ Review them ]`; **the equity check keeps running** — a new joiner does not switch the feature off |
| V1 | Validation — override without a reason | `Say why this step is different from the fitted one.` |
| V2 | Validation — step not in the level | Not possible; the select is built from the level |
| E5 | Error — load | `We couldn't load the fitted steps.` + `[ Try again ]` |
| E6 | Error — bulk confirm | `We couldn't confirm those. Nothing has changed — try again.` Atomic |
| E7 | Conflict — ladder changed mid-review | `The job ladder changed while you were reviewing — Engineering level 1 now has 3 steps. Some fits have been recalculated.` + `[ Reload ]`; confirmations already made are kept where the step still exists and revert to `Needs a look` where it does not |
| P1 | `compensation:r` without `job_architecture:w` | Tab absent |
| P2 | `job_architecture:w` without `compensation:r` | Tab absent — the fit is derived from pay |
| S1 | Success | `✓ Step review complete. The pay-equity check is now running for Acme Corp.` + `[ Run the first check → ]`; `#live-status` gets both sentences |

### 7.9.4 Accessibility

- **Keyboard path:** filter chips (`role="radiogroup"`, arrows move) → `Confirm all exact fits` → per row: step
  select (accessible name `Fitted step for Ravi Sharma`) → `Why?` when revealed → `Fits ✓` → next row →
  `Mark the step review complete`.
- Confirming a row **does not move focus** (the user is scanning down a list); it announces
  `Ravi Sharma confirmed at step 1.5. 20 left to look at.` and the row collapses to a single confirmed line if
  the `Needs a look` filter is active — announced, so a row disappearing under the cursor is never a surprise.
- The `Why` column is real text in its own cell, never a tooltip or a `title=` attribute.
- The progress meter is `role="progressbar"` with `aria-label="People confirmed"`; the
  `118 confirmed · 21 need a look · 7 have no pay recorded` line is the accessible truth.
- `Mark the step review complete` has `aria-describedby` pointing at its consequence line.
- Below 768px each row becomes a card: name and level on line 1, pay and fitted step on line 2, the reason on
  line 3, actions full width at ≥44px.

---

## 8. KAN-192 — Progression, and the top-step signal

> A signal, not an entitlement. One sentence, and it has to be the right one.
>
> ⛔ **AMENDED by A1.** Four changes. **(1)** Steps run from `.0`. **(2)** The card now carries **what the step
> means** and a link to the next one — this is where an employee's colleague-facing view of the ladder meets a
> manager's. **(3)** A step change carries a **mandatory review context** and **proposes** a pay change; it never
> applies one (SPM §14.4) — which supersedes my Wave 2 "immediate versus approval switch". **(4)** The top-step
> signal goes to **the reporting manager only**; HR sees step position in the register instead (SPM §14.3.4).
> The card's gate also moves from `compensation:r` to **`job_architecture:r`**, with the pay point inside it
> still on `compensation:r`.

### 8.1 The Job Level card (employee profile)

Left column, above Compensation. Gate **`job_architecture:r`** + row scope *(A1 — was `compensation:r`)*.

```
┌─ Job Level ──────────────────────────────────────────────────┐
│  Job title      Trainee Software Engineer                    │
│  Family         Engineering                                  │
│  Level & step   Level 1 · step 1.5   ● ● ● ● ● ●  (1.5 of 1.5)│
│  What 1.5 means Takes on work that spans more than one       │
│                 component.                    [ Read more → ]│
│  Working title  Payments Platform Engineer                   │
│  On this step   since 4 March 2026                           │
│  On this level  since 1 March 2025                           │
│  Step pay point €76,577   (compensation:r only)              │
│                                                              │
│  ⓘ At the top step of this level.                            │
│    Reaching the top step doesn't change anyone's level,      │
│    title or pay by itself — a level change is a separate     │
│    decision someone has to make.                             │
│                                                              │
│  Next-step roadmap  Written by Marcus Lee, 12 Mar 2026       │
│                     Confirmed by Ravi, 14 Mar 2026    [ → ]  │
│                                                              │
│  [ Advance step… ] [ Write the roadmap… ] [ Request a level  │
│    change… ]                                    [ History → ]│
└──────────────────────────────────────────────────────────────┘
```

**The step indicator** `● ● ● ● ● ● (1.5 of 1.5)` is glyph **and** the step values — never dots alone, never
colour alone, and **six dots for a five-step level**, matching §6.3's arithmetic. Its accessible name is
`Step 1.5 of 1.5, the top step of this level`.

**(A1) `What 1.5 means`** is the step's authored summary (§6.9), one line, with `[ Read more → ]` to
`/ladder/engineering/1/5`. When the step has no expectations yet: `Not described yet` in `var(--muted)`, plus
`[ Describe it → ]` for `job_architecture:w` — the same honest partial state an employee sees on `/ladder`.

**(A1) `Step pay point`** is the only money on this card and it is gated `compensation:r` **and** row scope. The
row is **absent** otherwise (D-R1), not blanked. It is labelled *pay point*, never *salary* — the two sit two
cards apart and confusing them is how somebody reads a configured rate as what a person earns (D-R10).

**(A1) The roadmap row** shows author, date and acknowledgement state, and links to §22. It renders for
`job_architecture:r` + scope. States: `Written by … · Confirmed by …` · `Written by … · not confirmed yet` ·
`No roadmap yet` (with `[ Write the roadmap… ]` for the manager, and nothing for anyone else).

**The sentence.** This is the copy the SPM singled out. The rules behind it:

- The word **eligible** appears nowhere in any manager- or employee-facing string. The database marker may be
  `promotion_eligible`; the UI says **"at the top step"**. "Eligible" reads as an entitlement and it is not one.
- **No time language at all** — no "due", "ready", "overdue", "since", "waiting", no countdown, no date by which
  anything should happen. A promotion has no deadline and implying one manufactures an obligation the company never
  made.
- **The negative is stated before the positive.** "Doesn't change anything by itself" comes before any prompt to
  act, because the misreading we are guarding against is "the system has promoted them".
- It is an `ⓘ` informational block in `#f8fafc`/`#e2e8f0` — **not** amber, **not** a warning. A person at the top of
  their level is not a problem.

**Actions:** `Advance step…` and `Request promotion…` render for `compensation:r` **and** `_can_initiate_for`
(the subject's solid-line manager, or HR/Portal/System admin — SPM D4a keeps KAN-139 for every request type).
Never on your own profile, through any route.

### 8.2 The `Advance step…` dialog *(A1 — substantially rewritten)*

> ⛔ **SUPERSEDED.** My Wave 2 design made the *step* change wait for approval whenever it carried pay. **A1
> separates them:** the step change is job content and is applied immediately with an audit record; the pay
> change is **proposed** into the existing chain and never applied here (SPM §14.4). That is not a compromise —
> it is the mechanism that makes the owner's own concern detectable, because it is what allows the responsibility
> to move before the money does, which is exactly the `PAY_BELOW_STEP` case (§8.6).

**Gate:** `job_architecture:w` **or** the subject's solid-line manager, **plus** `_can_initiate_for`, plus
KAN-203's `subject ≠ initiator`. The **Pay** block inside it additionally needs `compensation:r`.

```
┌ Advance step — Ravi Sharma ───────────────────────────────── × ┐
│ EMP-0142 · Engineering · Trainee Software Engineer · step 1.3  │
├────────────────────────────────────────────────────────────────┤
│  New step *        [ 1.4 ▾ ]        (1.0 – 1.5)                │
│  → 1.4 means: Leads a small piece of work end to end.          │
│                                            [ Read more → ]     │
│                                                                │
│  What was this agreed at? *                              (A1)  │
│  ( ) Probation review  ( ) Mid-term goal review                │
│  ( ) Performance review  ( ) Not at a review                   │
│  Review date *     [ 09/08/2026 ]                              │
│  Note              [                                      ]    │
│                                                                │
│  Effective from *  [ 09/08/2026 ]                              │
│                                                                │
│  Pay *                                                (A1)     │
│  Currently €72,000 · EUR · 1.0 FTE · since 1 Mar 2026          │
│  The pay point for step 1.4 is €72,930.                        │
│  ( ) Match the step — propose €72,930  ( ) A different amount  │
│  ( ) No change   ( ) Decide separately                         │
│  Whatever you choose, Ravi's pay doesn't change today — it      │
│  goes to approval. The step change applies straight away.      │
├────────────────────────────────────────────────────────────────┤
│                          [ Cancel ]   [ Advance to step 1.4 ]  │
└────────────────────────────────────────────────────────────────┘
```

**(A1) `What was this agreed at?` — mandatory, with an off-cycle option.** Four radios in a `<fieldset>`, nothing
pre-selected, mirroring the pay question's discipline: an unanswered context means the question fell on the
floor. `Not at a review` is a legitimate answer and is worded as one — not "Other", which reads as a failure to
categorise. The review date defaults to today and may be in the past (the conversation usually happened before
somebody got to the portal); it may not be in the future.
**This is the whole of EP42's performance-review coupling. It records that a step change happened at a review.
It does not build the review** — see §25.

**(A1) The pay question has four options now, and the first one is the point of the increment.**

| Option | What it does | Copy under it |
|---|---|---|
| **Match the step — propose €72,930** | Pre-fills a `COMPENSATION_REVIEW` at the computed step pay point | `+1.3% on Ravi's current pay.` |
| **A different amount** | Reveals amount / currency / FTE, same validation and guards as §9.3 | — |
| **No change** | Records an affirmative decision, no request raised | `Recorded as a decision, not a gap. Say why below.` — **a reason is required**, because A1's whole rationale is that responsibility and pay move together, so declining to move the pay is the thing that needs explaining |
| **Decide separately** | Reason required; the subject appears on Overview → *Pay decisions deferred* | — |

**Nothing is pre-selected**, including `Match the step` — a pre-selected money option is a pay decision made by
inertia, and the fact that the system can *compute* the right number is not a reason to let it *choose*.

**The sentence under the radios is the most important string in this dialog** and is permanent, in all four
states: *"Whatever you choose, Ravi's pay doesn't change today — it goes to approval. The step change applies
straight away."* It is the honest statement of the split, at the moment of the decision, and it prevents both of
the misreadings available here ("I've given him a rise" and "nothing happened").

**Absent for a viewer without `compensation:r`:** the entire Pay block, per D-R1 and CFL-42-13. The step change
still proceeds, and the request records `NOT_ANSWERED_NO_PERMISSION` — **and the first `compensation:r` holder to
touch this person's record is asked the question**, exactly as CFL-42-13 rules for the move modal. A manager
without pay sight must not be able to make the pay question disappear.

**Skip-step** is allowed (any step in the level is selectable). Skipping more than one step reveals a muted line:
`That's a jump of 3 steps. Say why in the reason.` — a nudge, not a block.

**Downward step** is allowed and is the destructive case:

> ⚠ `This moves Ravi down from step 1.4 to step 1.2.` `Their pay doesn't change unless you change it here.`
> `☐ Yes, move Ravi down to step 1.2.`
> Commit button becomes `[ Move Ravi down to step 1.2 ]`, `.btn-danger`, disabled until ticked.

### 8.3 Every state — progression

| # | State | What the user sees |
|---|---|---|
| L1 | Loading — card | Four skeleton rows |
| L2 | Loading — chain (after picking New salary) | Notice reads `Checking who needs to approve…`; submit disabled |
| L3 | Submitting | Button → `Advancing…` / `Submitting…`; dialog un-dismissable |
| E1 | **Empty — not assigned to a level** | Card renders: `Not assigned to a level.` + `Comparisons and promotions need a level.` + `[ Assign a level… ]` for `w`. **Never** a blank card and never a hidden one — an unlevelled person is the state HR must see |
| E2 | Empty — no ladder in the company | `Your company hasn't set up a job ladder yet.` + `[ Build the job ladder → ]` for `w` |
| E3 | Empty — at the top level, top step | The top-step sentence plus `Engineering has no level above 3. A promotion here means changing the ladder or moving family.` |
| PD1 | Partial — level assigned, no working title | The `Working title` row is absent, not blank |
| PD2 | Partial — level renamed since assignment | Shows today's title; the history entry keeps the title as at the time |
| V1 | Validation | `Choose a new step.` · `The new step is the same as the current one.` · `Give a reason for this change.` · `Tick the box to confirm the move down.` |
| E4 | Error — apply | `We couldn't change Ravi's step, so nothing has changed. Try again.` |
| E5 | Conflict | `Ravi's level changed while this was open. Close and reopen to see where he is now.` + `[ Close ]` |
| E6 | Subject no longer active | `Ravi Sharma has left the company. You can't change a former employee's level.` |
| P1 | `compensation:r`, not their report, not HR | Card visible **read-only**; no action buttons |
| P2 | No `compensation` | Card absent |
| P3 | Own profile | Card visible (it is your level, not your pay) — **no action buttons**, ever |
| S1 | Success — step only, no pay change | `✓ Ravi Sharma is now on step 1.4.` `Effective 9 August 2026, agreed at the mid-term goal review on 4 August. You recorded that his pay doesn't change.` `[ Done ]` |
| **S2** | **Success — step applied, pay proposed** *(A1 — the normal case)* | `✓ Ravi Sharma is now on step 1.4.` **`A pay change to €72,930 has been sent for approval — it's with HR Admin, approval 1 of 2. His pay is unchanged until that's approved.`** `[ View in Position Changes ] [ Done ]`. Two sentences, two different verbs, deliberately: one thing happened, one thing was asked for |
| **E7** *(A1)* | **Error — the step applied but the pay proposal failed** | `Ravi is now on step 1.4, but we couldn't raise the pay change. Nothing about his pay has changed or been proposed.` + `[ Try the pay change again ]`. The two halves are separate writes by design (SPM §14.4), so a partial outcome is real and must be recoverable rather than silently lost. The subject also appears under *Pay decisions deferred* so it cannot fall off the end |
| **V2** *(A1)* | Validation — no review context | `Say what this was agreed at. If it wasn't at a review, choose "Not at a review".` |
| **V3** *(A1)* | Validation — review date in the future | `The review date can't be in the future.` |
| **V4** *(A1)* | Validation — "no change" without a reason | `Say why Ravi's pay isn't changing with this step.` |
| **PD3** *(A1)* | Partial — no pay point configured for this step | The `Match the step` option is **absent**, and a muted line reads `No pay point is set for step 1.4 in Germany, so we can't work out what it should be. [ Set pay points → ]` for `compensation:w`. The other three options still work |
| **PD4** *(A1)* | Partial — the new step has no expectations | The `→ 1.4 means:` line reads `Not described yet.` + `[ Describe it → ]` for `job_architecture:w`. Never blank, and never a blocker |

### 8.4 The top-step signal as a notification

Full D4 treatment is in §15; the design decisions specific to this signal:

- **Recipients: the subject's reporting (solid-line) manager. Only.** ⛔ *(A1 — narrowed. My Wave 2 version also
  notified `compensation:w` holders; the owner's words were "it is **indicative for the reporting manager**",
  and HR now sees step position in the register instead — §8.7. A straight noise reduction, and it matches what
  he said.)* **Not the subject.**
- **Not in My Pay, ever.** An employee reading "you are at the top step" in their own pay card would reasonably
  infer a promotion is coming. My Pay states the level and step as facts and says nothing about the top of it.
- **It has a `Not now`, and pay-equity findings do not.** The general rule, which I want on the record because it
  answers "does it ever retire" differently for the two families of EP42 event:
  > **A compliance-relevant condition needs a reasoned disposition and cannot be dismissed. A management prompt
  > needs a recorded, time-boxed dismissal and must not nag.**
  "Should we promote Ravi?" carries no compliance obligation; a manager may legitimately answer "not this year".
  So `Not now` records who dismissed it and when, suppresses re-fire for **6 months**, and does not touch the
  underlying state. A pay-equity finding gets no such control (§14.3).
- **It retires** when the person's level or step changes (any direction), when they leave, or on `Not now`. It
  never retires on read. If the subject's solid-line manager changes, it retires for the old manager and fires for
  the new one — an easy thing to miss and an easy thing to test.
- **(A1) It also fires when the ladder shrinks under someone.** Reducing a level's step count can put an existing
  employee at the top step without anybody touching that employee. §6.5's review dialog warns the admin; the
  manager gets the ordinary signal. Both halves are needed: a notification whose cause is invisible to its
  recipient is DEF-001's cousin.

---

## 8.6 *(A1)* The intermediate state — the step has landed, the pay has not

> **This is not an error. It is the expected sequence, and it is the state that later produces a
> `PAY_BELOW_STEP` finding.** SPM §14.4: *"the step change is allowed to move first, and the correspondence check
> is the mechanism that makes sure the pay eventually catches up."* Design it honestly, or three different
> screens will each invent their own way of implying something went wrong.

**The rule for all three surfaces: state both facts, in the past tense for the one that happened and the present
tense for the one that is pending, and never use an error colour.** Amber `#fffbeb`/`#b45309`, `role="status"`,
with `⏳` — the same in-flight glyph the bell uses for an undecided request (DEF-002's lesson: an item with no
outcome yet must not wear one).

**(a) Profile → Job Level card**

> `Step 1.4 since 9 August 2026.`
> ⏳ `A pay change to €72,930 is with HR Admin for approval (1 of 2). Ravi's pay is unchanged until it's
> approved.` `[ Follow it → ]`

**(b) Profile → Compensation card**

> `Base salary €72,000 · EUR · a year`
> ⏳ `A change to €72,930 is awaiting approval (1 of 2).` `[ Follow it → ]`
> — the *current* figure stays the headline. A pending proposal must never be rendered where the current salary
> goes, and never in `Money`'s primary slot (D-R10: a proposed figure that looks like a real one is the same
> defect as an imputed one).

**(c) The equity register — the finding is suppressed while a proposal is live.**
A `PAY_BELOW_STEP` condition that somebody is already fixing is noise, and raising it would put a finding and its
own remedy in the queue at the same time. So:

- While a `COMPENSATION_REVIEW` for that subject is `PENDING`, **no finding is raised**, and if one is already
  open its row reads `Open · an adjustment is proposed and awaiting approval (1 of 2)` with a link. The finding
  does **not** close — it closes when the pay lands (§14.7).
- **If the proposal is rejected or cancelled, the finding raises (or re-activates) on the next evaluation**, with
  the reason on the row: `The proposed adjustment was rejected on 12 August.` This is the case that must not be
  silent: a rejected pay correction is precisely the situation the owner wants HR to know about.

**(d) What the employee sees: nothing about the proposal.** ⛔ Deliberate, and it is uncomfortable. My Pay shows
the current figure and no pending change, because a proposal can be refused and D5.5's no-forward-looking rule is
absolute — telling somebody "a rise is awaiting approval" and then refusing it is worse than telling them
nothing. What the employee *does* see is the step change itself (it is their job content, and it is on their own
Job Level card), and the position-in-range sentence on My Pay, which will read *"towards the lower end of the
range"* while the pay lags. **Recorded as UX-A1-Q3** — it is the sharpest edge of A1's transparency-versus-
discretion boundary and the SPM should see it rather than have it built quietly.

**States:** *Proposal pending* — as above. *Proposal approved* — both notices disappear; the Compensation card
shows the new figure from its effective date; a `✅` receipt goes to the requester. *Proposal rejected* —
the notice becomes `The pay change was not approved on 12 August.` in `var(--muted)` on the Job Level card, with
no colour and no glyph, and disappears after 30 days. *Proposal cancelled* — same, worded `withdrawn`.
*Multiple proposals* — not possible; the existing pending-request guard (`AC-185-08`) applies.

---

## 8.7 *(A1)* Step position as a live report — and where it stops

> A1's more useful half: *"the junior engineer who started 2.0 is already at 2.3 or 2.4, which means the junior
> software engineer is taking additional responsibility."* Step position is readable **between** promotions, and
> it is where "the pay never followed" is actually spotted. SPM §14.3.4 makes it a reporting requirement.

**Two surfaces, both deliberately thin.**

**(a) `My Team` (`templates/employees/my_team.html`) gains a step column.** Name · level · step · on this step
since · roadmap state. Nothing else.

**(b) `/compensation` Overview gains a step-distribution block** for `compensation:r` + `job_architecture:r`:

```
Where your people are on the ladder
  Engineering · Trainee Software Engineer      1.0 ▮▮      1.1 ▮▮▮▮▮   1.2 ▮▮▮
                                               1.3 ▮       1.4 —       1.5 ▮▮
  Engineering · Junior Software Engineer       2.0 ▮▮▮▮    2.1 ▮▮      …
  6 people have been on their step for more than 18 months.   [ See them ]
```

**Where it stops, and why the boundary is drawn exactly here (§25, R-17):**

| In | Out, permanently |
|---|---|
| Which step somebody is on | Any ranking of people by step |
| The date they reached it | A **rate** of progression, "steps per year", velocity, trajectory |
| A count of people per step | A comparison of one person's pace to another's, or to an average |
| "On this step for more than 18 months" — a **flag for a conversation**, phrased as a fact about elapsed time | "Slow", "stalled", "behind", "at risk", or any derived status word |
| Sorting by level, step or name | Sorting by "progress" |

The 18-month line is the one that could most easily become a performance metric, so its copy is fixed here:
**`6 people have been on their step for more than 18 months.`** — a fact about the calendar, with no adjective,
no colour, no icon and no implied fault. It exists because a person who has been on 2.3 for two years is the most
likely `PAY_BELOW_STEP` case in the company, not because anybody is judging them. The threshold is a company
setting on `company_settings:w`, defaulting to 18 months, and it may be switched off entirely.

**Accessibility:** the distribution is a real `<table>` with `<th scope="row">` per level and a caption
`People per step, by level`; the `▮` bars are `aria-hidden` and each cell's accessible name is
`Step 1.1, 5 people`. Never colour alone; never a chart without its numbers.

---

## 9. KAN-193 / 194 / 195 — The compensation record, My Pay, and the backfill

### 9.1 The Compensation card (someone else's profile)

Left column, below Job Level, above EP38's Lifecycle History. Gate `compensation:r` **and** row scope.

```
┌─ Compensation ──────────────────────────── [ 👁 Hide amounts ] ─┐
│  Base salary       €72,000 · EUR · a year                       │
│  Working pattern   Full-time · 1.0 FTE                          │
│  In effect since   1 March 2026                                 │
│  In range          Mid-range for level 2 in Germany · 0.96      │
│  Last change       Priya Nair · 1 Mar 2026 · "Annual review"    │
│                                                                 │
│  [ Record a change… ]                        [ History → ]      │
└─────────────────────────────────────────────────────────────────┘
```

- **`In range`** appears only where a band exists (KAN-199). It is **plain language plus the compa-ratio**, with the
  direction as a glyph and a word, never colour alone: `◆ Mid-range` / `▼ Below range` / `▲ Above range`.
- **`Last change`** names the actor and their reason. The note, if any, sits under it in quotes and renders via
  `textContent`.
- `Record a change…` requires `compensation:w`. `History →` requires `compensation:r` and opens §14.5.
- **Amount typography** per §2.6(a). No `.stat-num`, no heading.
- **No comparison to any colleague on this card, ever** — the band is a company-set range, not a person.

### 9.2 "My Pay" — the most easily misread copy in the epic

Right column of your **own** profile, above Skills. Gate `compensation_self:r`. Hard-scoped to
`session.employee_id` **server-side**; the scope is never taken from a request parameter.

```
┌─ My Pay ─────────────────────────────────── [ 👁 Hide amounts ] ─┐
│  Your base salary    €72,000 a year                              │
│  Your working pattern Full-time (1.0 FTE)                        │
│  In effect since     1 March 2026                                │
│  Your job level      Senior Software Engineer                    │
│                      Engineering · level 2, step 2.3             │
│  Your range          Your salary is in the middle of the range   │
│                      your company has set for level 2 in Germany.│
│                                                                  │
│  This is what the HR portal holds. It isn't a payslip, and it    │
│  doesn't include bonus, overtime, benefits or anything agreed    │
│  outside the portal. If something here looks wrong, talk to      │
│  your HR team.                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Copy rules, enforceable at review:**

1. **No forward-looking language.** These strings are banned by name: *next increase · you are due · eligible ·
   on track · expected · target salary · you will · when you reach · review date · your next review*. A sentence
   that could be read as a promise is a defect, not a wording preference.
2. **No comparison to anybody.** No median, no percentile, no "top 25%", no peer count, no "people at your level
   earn". Position in range is a comparison to a **company-set range**, which is a policy, not a colleague.
3. **Position in range in words**, per SPM D5.5. Five phrasings, and only these five:
   `towards the lower end of` · `in the middle of` · `towards the upper end of` ·
   `above the range your company has set for` · `below the range your company has set for`.
   The raw compa-ratio number is **not** shown to the employee.
4. **Out of range must not alarm.** Both out-of-range cases carry one extra sentence:
   > `Ranges are guidance. Being outside one is common and doesn't mean anything is wrong.`
   Red-circled legacy pay and genuine market premiums exist; a card that reads as an accusation about the
   employee's own salary would be a serious product mistake.
5. **No band → the `Your range` row is absent entirely.** Not "not available", not "—".
6. **No badge, no icon, no colour** on this card. Nothing that could read as a rating.
7. **History** is per-tenant, default off (SPM D5.5). When on: `[ See how your pay has changed ]` opens the same
   timeline as §14.5, self-scoped.

**Empty state — no record for me** (the state most employees will meet first, at partial coverage):

> `Your pay isn't recorded in this portal yet.`
> `Your HR team may still be adding it. Your payslip is the authority on what you're paid.`

No action, no alarm, and it points at the real source of truth — which is the sentence that prevents the support
ticket "the portal says I have no salary".

**`compensation_self` off for the tenant → the card is absent.** Not "your company has disabled this". The employee
cannot act on that sentence and it invites a conversation HR may not be able to have. *(Recorded as UXQ6 — pay
transparency law may eventually require the opposite, and that is a DPO question, not a design one.)*

**No bell notification to the subject when their pay changes.** This is a deliberate design decision, not an
omission: a pay change is communicated by a manager in a conversation, and a portal notification that arrives
before or instead of that conversation is a serious HR failure. It is the same reasoning that stopped EP38 telling
a reassigned report *why* their manager changed. My Pay simply shows the new figure from its effective date.
*(UXQ7 — some jurisdictions require written notification of a pay change; that is a letter, not a bell.)*

### 9.3 The `Record a change…` dialog

Gate `compensation:w`. Behaviour per §2.5(a).

```
┌ Record a salary change — Ravi Sharma ────────────────────── × ┐
│ EMP-0142 · Engineering · level 2 · step 2.3                   │
├───────────────────────────────────────────────────────────────┤
│  Currently  €72,000 · EUR · 1.0 FTE · since 1 March 2026      │
│                                                               │
│  New base salary *   [ €  72,000            ]  per [ year ▾ ] │
│  Currency *          [ EUR ▾ ]  Germany's pay market uses EUR │
│  Working pattern *   [ 1.0 ] FTE   Full-time                  │
│  Effective from *    [ 01/09/2026 ]                           │
│  Reason *            [ — Select a reason — ▾ ]                │
│  Note                [                                     ]  │
│                      Anyone who can see Ravi's pay can read   │
│                      this, and it stays on the record.        │
├───────────────────────────────────────────────────────────────┤
│           [ Cancel ]   [ Record €78,000 for Ravi Sharma ]     │
└───────────────────────────────────────────────────────────────┘
```

| Field | Control | Rules |
|---|---|---|
| Amount | `inputmode="decimal"`, currency prefix, thousands-formatted on blur | Required. `> 0`. Digits and separators only |
| Pay basis | select: `year` / `month` / `hour` | Required. Choosing `hour` reveals a muted line `Annualised at 1,720 hours — your company's standard.` so the comparison basis is never a mystery |
| Currency | select, **defaulted from the employee's location country**, not from a global default | Required. Mismatch with the pay market warns, never blocks |
| FTE | number 0.01–1.00, step 0.05, default 1.0 | Required. Shows the words beside it (`0.6 FTE · Part-time`) |
| Effective from | `<input type="date">`, default today | Within the company's window (default 90 back / 180 forward) |
| Reason | select from the company's categories | Required |
| Note | textarea | Optional. Its readership is stated at the field, per role rule 4 |

**Error prevention over error messages** — three guards, all designed rather than left to a server error:

1. **Order-of-magnitude guard.** If the amount is ≥5× or ≤⅕ of the current record (or, with no prior record, more
   than 2× outside the level's band), an amber block appears inline **without stealing focus**:
   > ⚠ `€720,000 is ten times Ravi's current salary. That's usually a typing slip.`
   > `☐ Yes, €720,000 is right.`
   Commit is blocked until ticked. The extra zero is the classic pay-entry defect and it is cheap to catch.
2. **Decrease acknowledgement.** Any decrease reveals:
   > `☐ This reduces Ravi's salary from €72,000 to €68,000.`
   Commit button becomes `.btn-danger` and reads `Record a reduction for Ravi Sharma`.
3. **Out-of-band, allowed and explained** (SPM D3.5 — never hard-blocked):
   > `€95,000 is above the range for level 2 in Germany (€60,000 – €84,000). That's allowed — say why in the reason.`
   The reason select gains an `Above/below range` category and free text becomes required.

**Success panel** (in-dialog, no `alert()`):

> ✓ **Salary recorded for Ravi Sharma.**
> €78,000 EUR · 1.0 FTE · effective 1 September 2026.
> This is a future date — €72,000 stays in force until then.
> `[ View history ]  [ Done ]`

`#live-status` gets the first two lines. `Done` closes and refreshes the card, so the profile behind the dialog can
never be stale (the EP38 §5.3 rule — a stale page is how the same change gets recorded twice).

### 9.4 Backfill — bulk import (KAN-195)

Reuses the existing import surface (`templates/imports/*`), not a second importer. Three phases: **upload →
preview (dry run) → commit**. Reached from `/compensation` → **Import**.

**Upload.** Drop zone identical to `imports/upload.html`, with a compensation-specific format card:

> **Columns:** `employee_number`, `effective_from` (YYYY-MM-DD), `currency`, `annual_base`, `fte`, `pay_basis`
> (annual/monthly/hourly), `reason`
> `[ Download the template ]` — *The template is empty on purpose. It never contains anyone's current pay.*

That last sentence is a discretion rule made visible (D-R5): a "download current salaries to edit" flow would put
every salary in the company into a file in someone's Downloads folder, and it is not in scope this cycle (UXQ5).

**Preview (dry run).** The `imports/preview.html` table shape, with compensation columns and a per-row action:

| # | Employee | Current | Proposed | Effective | Action | Message |
|---|---|---|---|---|---|---|
| 1 | Ravi Sharma · EMP-0142 | €72,000 | **€78,000** | 1 Sep 2026 | `Update` | +8.3% |
| 2 | Ana Costa · EMP-0157 | *No salary recorded* | **€64,000** | 1 Sep 2026 | `Create` | — |
| 3 | — · EMP-9999 | — | — | — | `Error` | No employee with that number in your company |
| 4 | Tom Rieder · EMP-0163 | €58,000 | — | — | `Error` | `annual_base` is empty |

Header summary: `118 create · 12 update · 6 errors`. Errors use `badge-red`, updates `badge-amber`, creates
`badge-green` — each with its **word**, never colour alone.

**Row-level error strings (final):**

| Situation | Message |
|---|---|
| Unknown employee number | `Row 3: no employee with number EMP-9999 in your company.` |
| Blank amount | `Row 4: annual_base is empty. A blank can't overwrite an existing salary — fix the row or take it out of the file.` |
| Zero amount | `Row 5: annual_base is 0. Zero is a real salary. If you mean "we don't know", leave this person out of the file.` |
| Negative | `Row 6: annual_base can't be negative.` |
| Bad date | `Row 7: effective_from must look like 2026-09-01.` |
| Date outside the window | `Row 8: effective_from is 400 days in the past. Your company allows 90.` |
| Unknown currency | `Row 9: "EURO" isn't a currency code. Use EUR.` |
| Currency ≠ pay market | `Row 10: Ravi is in Germany, whose pay market uses EUR, but this row says SEK.` **Warning, not an error** |
| FTE out of range | `Row 11: fte must be between 0.01 and 1.00.` |
| Duplicate | `Row 12: EMP-0142 appears twice with the same effective date.` |
| Contractor | `Row 13: Tom Rieder is a contractor. Contractors don't have an annual salary in this portal.` **Warning; the row is skipped** |
| Non-active employee | `Row 14: Ana Costa has left the company. Recording pay for a former employee needs a correction, not an import.` |
| Cross-company | Whole file rejected: `This file contains employees who aren't in your company. Nothing has been imported.` |

**Commit.** A confirm dialog, because 12 of these rows overwrite existing pay:

> **Import 130 salary records?**
> 118 people get their first salary record · **12 people's pay is being changed** · 6 rows with errors are skipped.
> `[ Review the 12 changes → ]` *(expands a from → to list)*
> ☐ I've checked the 12 changes.
> `[ Cancel ]  [ Import 130 records ]`

The acknowledgement gates only the **update** case. A first-time create needs no extra friction; overwriting
somebody's recorded pay does.

**Atomicity is stated, because it changes what a failure means:**

> `We couldn't finish the import. It failed at row 84 and nothing at all has been imported — not even the rows
> before it. Fix row 84 and upload the file again.`

**After commit:** coverage meters update in place, `#live-status` →
`130 salary records imported. Compensation coverage is now 89%.`, and the run appears in the import history with
the actor, the counts and the file name.

### 9.5 The Overview tab — coverage, and the adoption instrument

This is the screen that makes a backfill finish, and the screen that prevents "no findings ✓" at 40% coverage.

```
┌ Overview ─────────────────────────────────────── [ 👁 Hide amounts ] ┐
│                                                                      │
│  Pay coverage                                                  (A1)  │
│  ████████████░░░░░░░░  62%                                           │
│  91 of 146 active employees have a salary in effect.                 │
│  Not counted: 1 contractor, 0 interns.                               │
│  [ Export the 55 without a record (CSV) ]   [ Import salaries → ]    │
│                                                                      │
│  Level coverage                                                (A1)  │
│  ██████████████████░░  91%                                           │
│  133 of 146 active employees are on a level and step.                │
│  [ Export the 13 without a level (CSV) ]    [ Assign levels → ]      │
│                                                                      │
│  Pay equity                                                    (A1)  │
│  Not running yet — it's waiting on your step review.                 │
│  118 of 146 fitted steps confirmed.        [ Continue the review → ] │
│                                                                      │
│  Pay decisions deferred                    3                         │
│  Position changes that were applied with the pay decision put off.   │
│   • Ravi Sharma · deferred 2 Aug by Marcus Lee · "waiting on budget" │
│     [ Record salary… ]                                               │
│   • …                                                                │
└──────────────────────────────────────────────────────────────────────┘
```

**(A1 / amendment A-5) The two meters are named, because my Wave 2 label was ambiguous and would have been
quoted at a customer.** They are **pay coverage** (% of ACTIVE employees with a compensation record in effect)
and **level coverage** (% with a level *and step* assignment in effect), each naming its denominator on the
screen. **The equity gate is a third thing and is deliberately not a percentage any more** — it is the
fitted-step review (§7.9), one human act, and the block says so rather than showing a number that looks like the
other two. Conflating the adoption instrument with the evaluation gate is how a tenant concludes the check is
running when it is not.

- **Row-scoped** per D-R3. A manager with `compensation:r` over four reports sees
  `3 of your 4 direct reports have a salary recorded.` — never the company number, and never "142 more you can't
  see" (D-R4).
- **Exports contain no amounts** — they are lists of people *without* a record. Header row states it:
  `# Employees with no salary recorded — this file contains no pay data.`
- **Deferred pay decisions** is the "visible follow-up" SPM D4c requires for the *Decide separately* option. Without
  it, "defer" is indistinguishable from silence, which is the status quo we are replacing.

### 9.6 Every state — the compensation record surfaces

| # | State | What the user sees |
|---|---|---|
| L1 | Loading — card | Four skeleton rows; `aria-busy="true"` |
| L2 | Loading — import preview | `Checking 136 rows…` with a progress bar; commit hidden |
| L3 | Committing | Un-dismissable dialog; `Importing…` |
| E1 | **Empty — no salary recorded** | §2.6(b) — `No salary recorded` + `This is not a zero…` + `[ Record salary… ]` for `w` |
| **E2** | **Contractor / intern** ⛔ *(A1/UXQ8 — my "no record action" was overruled, and rightly: blocking it pushes contractor rates into a spreadsheet, which is the problem we started with)* | **Two distinct states, and they must never be conflated.** *No rate yet:* `No rate recorded` + `Contractors aren't compared in pay equity, but you can record what they're paid.` + `[ Record a rate… ]` for `w`. *Rate recorded:* the amount renders normally, plus a permanent muted line **`Not applicable for comparison — contractor rate recorded.`** and a `badge-gray` `Excluded from pay equity` on the card header. The exclusion is **counted and shown** in every coverage figure and every group (§14.2), never silent |
| E3 | Empty — no reason categories configured | ⛔ *(A1/UXQ3 — mostly moot: a starter list is now **seeded** — `Annual review`, `Promotion`, `Market adjustment`, `Role change`, `Correction`, `Other` — company-editable. The state survives for a tenant that deletes them all.)* Reason select `— No reasons configured —`, disabled, helper `Add salary-change reasons in Compensation → Settings first.` **Commit blocked**, said up front rather than failing at submit (EP38 §5.8 E1 precedent) |
| **E2a** *(A1, amendment A-2)* | Reason on a compensation-bearing action | The reason is now **a mandatory category plus optional free text**, not free text alone. The optional box carries a non-blocking `role="status"` warning when the text contains a number: `Reasons can be read by people who can see the audit log but not pay. Try not to put an amount in here.` — a warning, not a block, because the mechanism cannot enforce it and claiming otherwise would be the mistake amendment A-2 exists to correct |
| **PD6** *(A1 / UAT-F-08)* | Subject is not ACTIVE | History is readable and retained; the record **closes at `exit_date`**; the card shows `Left the company on 12 June 2026 — pay record closed.` **New records are refused** with `Ravi has left the company. You can correct a past record from the history, but you can't record a new one.`, and `Record a change…` is **absent** |
| E4 | Empty — no import history | `You haven't imported any salaries yet.` |
| E5 | Empty — Overview at 0% | Both meters at 0% with `Nobody has a salary recorded yet.` and one primary next action, `[ Start with the job ladder → ]` — because importing pay before the ladder exists produces data with no grouping key |
| PD1 | **Partial — the normal state** | Coverage meters everywhere, always with both numerator and denominator |
| PD2 | Partial — record exists, no level | Compensation card renders fully; `In range` row absent; a muted line `No level, so there's no range to compare with. [ Assign a level… ]` |
| PD3 | Partial — level exists, no band | `In range` row absent entirely, not "no band set" |
| PD4 | Partial — future-dated record exists | Card shows today's figure and a muted line: `A change to €78,000 takes effect on 1 September 2026.` |
| PD5 | Partial — employment type changed to contractor after a record exists | Card shows the historical record with `Not compared in pay equity — now a contractor.` History is never hidden by a later type change |
| E6 | Error — card load | `We couldn't load Ravi's compensation.` + `[ Try again ]`; the rest of the profile is unaffected |
| E7 | Error — save | `We couldn't record this change, so nothing has been saved. Your entries are still here — try again.` |
| E8 | Conflict — a newer record exists | `Someone recorded a change for Ravi while this was open. Reload to see it before you record another.` + `[ Reload ]` |
| E9 | Conflict — same effective date | `There's already a salary record effective 1 March 2026. Choose a different date, or correct the existing one from the history.` + `[ Open history ]` |
| E10 | Permission lost mid-flight | `Your access to compensation changed while you were working. Nothing has been saved.` + `[ Close ]` only |
| I1 | Integration failure — audit write fails | **The save is rolled back.** `We couldn't record this change because the audit trail couldn't be written. Nothing has been saved.` Pay without an audit row is not a state this product may reach (KAN-155 one transaction) |
| P1 | No `compensation` | Card absent from the profile |
| P2 | `r`, out of row scope | Card absent — and the API returns the employee **without** the field, not with it nulled |
| P3 | `r` without `w` | Card visible; no `Record a change…` |
| P4 | `w` without `d` | History visible; no `Void this record` on any entry |
| S1 | Success | §9.3 |

### 9.7 Accessibility — compensation record surfaces

- **Keyboard path (dialog):** opener → dialog title → amount → pay basis → currency → FTE → effective date →
  order-of-magnitude confirm when present → decrease acknowledgement when present → reason → note → `Cancel` →
  commit.
- Amount input: `inputmode="decimal"`, `aria-describedby` pointing at the currency helper **and** at any active
  guard; `aria-invalid="true"` on error; every inline error `role="alert"`.
- Guards are `role="status"` (amber, informational) and never steal focus; the acknowledgement checkbox is
  referenced from the commit button's `aria-describedby`, so a screen-reader user is told *why* it is disabled.
- Meters: `role="progressbar"` + `aria-valuenow/min/max` + `aria-label="Compensation coverage"`; the
  `62% · 91 of 146` text is the accessible truth.
- Import preview table: `<th scope="col">`; each row's status cell contains the **word** as well as the badge
  colour; the error column is `role="cell"` plain text, escaped.
- Targets ≥24×24; ≥44px below 768px, where the dialog becomes a full-height sheet with a sticky footer and the
  preview table scrolls inside `.table-wrap` — never the page.
- Contrast: amounts in `--text`; helper in `var(--muted)` (4.76:1); guard `#b45309` on `#fffbeb`; error `#b91c1c`
  on `#fef2f2`; success `#15803d`.

---

## 10. KAN-196 — Pay inside the shared position-change dialog

> **One modal, one endpoint, one engine, three entry points** (SPM D4f). `templates/org_change/_move_modal.html`
> is **extended**, not duplicated, and not forked. The constraint that governs the whole design: **it must not make
> the common case heavier.**

### 10.1 The weight constraint, made measurable

Most moves have no pay change. The SPM asked me to prove the no-change path costs one deliberate click and no extra
scroll. Here is the constraint an engineer must meet and UAT can assert:

1. The pay block adds **one fieldset, three lines, ≤ 80 CSS px** in its default (nothing selected) state.
2. **`No change` expands nothing.** Selecting it is the whole interaction: one click, no reveal, no scroll, no
   second step, no second dialog.
3. The modal at its current 480px width **must not scroll at 1280×720** with the pay block in its default state and
   all existing fields present. If it does, the block is too heavy and the *existing* fields get compacted, not the
   pay block trimmed — the pay answer is mandatory and cannot be the thing that shrinks.
4. Nothing pre-selected. `No change` is an **answer**, and an answer that can be given by inertia is not one
   (the same reasoning as EP38's no-default departure type).

### 10.2 The block

Placed after **Location** and before **Reason** — reason stays last because it justifies the whole request,
including the pay decision.

```
┌───────────────────────────────────────────────────────────────┐
│  Pay *                                                        │
│  Currently €72,000 · EUR · 1.0 FTE · since 1 March 2026       │
│  ( ) No change    ( ) New salary    ( ) Decide separately     │
│  Say what happens to Ravi's pay. "No change" is an answer.    │
└───────────────────────────────────────────────────────────────┘
```

`<fieldset>` with `<legend>Pay *</legend>`; three `<input type="radio">` in a row (stacked below 480px).

| Choice | What expands | Rules |
|---|---|---|
| **No change** | Nothing | Recorded as an affirmative decision. The `Currently` line stays visible so "no change" is made against a figure the user can see |
| **New salary** | Amount · Currency · FTE — three fields inline, in one row at ≥600px. **No effective-date field**: it shares the request's effective date (KAN-189), and the block says so: `Takes effect on the same date as the move.` | Same validation, same order-of-magnitude and decrease guards as §9.3 |
| **Decide separately** | One required textarea: `Why is the pay decision being put off? *` | Plus a `role="status"` line: `Ravi will appear under "Pay decisions deferred" on the Compensation page until someone records a salary.` — the follow-up is named, so deferral is not silence |

**Absent, not disabled, for a user without `compensation:r`** (SPM D4f). The fieldset does not render, the payload
carries no `current_salary`, and **no explanatory line appears** — a "you can't see pay" note would itself disclose
that a pay block exists on this dialog for other people.

### 10.3 The request type, visible before submission

The type is inferred from what changed (SPM D4f). The user must not discover it afterwards, because it determines
the approval chain and whether KAN-198's four-eyes rule binds. A `role="status"` line sits directly above the
footer and updates live:

> `This will be raised as a **Transfer**.`
> `This will be raised as a **Promotion**.` *(A1: `LEVEL_CHANGE` with direction `UP`)*
> `This will be raised as a **Compensation review**.`
> `This will be raised as a **Level change**.` *(A1: `LEVEL_CHANGE`, direction `DOWN` or `LATERAL` — §11.3)*

When the inferred type changes, the approval-chain sentence in the existing notice box (`_move_modal.html:51-54`)
re-fetches and re-renders, with an interim `Checking who needs to approve…` and a live-region announcement:

> `Now a Compensation review. It needs 3 approvals: HR Admin, Finance, then Anna Weiss.`

This is the highest-value thing the block adds. Today a requester has no idea what they have set in motion; with
pay in the request, the chain can *change under them* as they type.

### 10.4 Refused at create time — the two unsatisfiable-chain cases

SPM D4b refuses a money-bearing request at create time if any chain step has no approver holding `compensation:r`.
KAN-198 creates a **second** such case (§12.3). Both render in the existing `mv-conflict` panel
(`_move_modal.html:34-37`), `role="alert"`, with the fix named and an escape hatch that is one click:

**(a) A step nobody with pay access can satisfy**

> ⚠ **This move can't carry a pay change.**
> Approval level 2 is Anna Weiss, and she can't see pay — so nobody at that level could approve it. Nothing has
> been submitted.
> Ask your Portal Admin to give that approver Compensation access, or raise the move on its own and handle pay
> separately.
> `[ Remove the pay change and submit the move ]`  `[ Close ]`

**(b) A chain that one person satisfies twice** (KAN-198)

> ⚠ **This request can't be approved by your current approval chain.**
> Levels 1 and 2 can both only be satisfied by Priya Nair, and a change that moves pay or level needs a different
> person at each level. Nothing has been submitted.
> Ask your Portal Admin to change the approval chain.
> `[ Remove the pay change and submit the move ]`  `[ Close ]`

Refusing at create, with nothing written, follows EP38's `AC-184-18` pattern (block, name the reason, write
nothing) rather than creating a request that stalls forever. Case (b) is an extension of D4b that the SPM's text
does not explicitly cover — recorded as §20 UX-CFL-42-4.

### 10.5 What the approver sees

**In the inbox and the review modal** (`org_change/inbox.html`), `diffHtml` gains a pay row — and by D4b every
approver on a money request holds `compensation:r`, so it is safe there and only there:

> **Base salary:** €72,000 → **€78,000** (+8.3%)
> **Level:** Engineering level 1, step 1.5 → **Engineering level 2, step 2.1**
> **Job title:** Software Engineer → **Senior Software Engineer**
> Effective 1 September 2026

The percentage is shown to the approver because approving a change without knowing its size is the problem the
four-eyes rule exists to stop. It is **derived money** (D-R9) and it never leaves this surface.

**In the bell** — and this is a change to existing behaviour that must be made deliberately:

- `ocSummary()` (`base.html:630-637`) must **never** render an amount or a percentage (SPM §4.5.7 names it). A
  money-bearing request summarises as `mgr → Ana Costa · pay change` — the **word**, not the number.
- **The one-click `✓ Approve` is suppressed for any request that carries a pay or level change.** The bell item
  offers `Review →` only, deep-linking to `/org-change?review=<id>`.
  *Rationale, and it is the product's own precedent:* `base.html:639-641` already makes **Reject** a deep link
  "because a decision without a recorded reason is not auditable". Approving a pay rise from a bell line that
  **cannot show the amount** is worse — it is approving a figure you have not seen. Same reasoning, stronger case.
  Placement-only transfers keep the existing one-click Approve.

### 10.6 Every state — pay in the move modal

Existing states from EP38 §6.4 (L1, L2, E1–E12, P1–P3, PD1, PD2, S1, I1) are unchanged and not repeated. New:

| # | State | What the user sees |
|---|---|---|
| L4 | Loading — current pay | The `Currently` line reads `Loading Ravi's current pay…`; the three radios are enabled (you can answer "no change" before it arrives) |
| L5 | Loading — chain after a type change | Chain line → `Checking who needs to approve…`; submit disabled |
| E13 | **No current salary recorded** | `Currently: No salary recorded.` and the `No change` option relabels to `No change — leave it unrecorded`, with a muted line `Ravi has no salary in the portal. "No change" keeps it that way.` This is the D7 state most likely to be met in the first months and it must never look like "currently €0" |
| E14 | Subject is a contractor | `Currently: Not applicable — Contractor.` The `New salary` option is **absent**; the block reduces to `No change` / `Decide separately` |
| E15 | Pay fetch failed | `Currently: we couldn't load Ravi's current pay.` Radios stay enabled, but choosing `New salary` shows `We can't show what Ravi earns now, so a new salary can't be checked against it. Try again, or raise the move without a pay change.` and submit is blocked for that option only |
| PD3 | Partial — no band for this level/market | No out-of-band check runs; no message. Silence is correct — there is nothing to compare against |
| V7 | Validation — pay unanswered | `Say what happens to Ravi's pay. If nothing changes, choose "No change".` Focus moves to the first radio; the fieldset gets `aria-invalid` |
| V8 | Validation — new salary chosen, no amount | `Enter the new base salary.` |
| V9 | Validation — amount equals current | `That's the same as Ravi's current salary. Choose "No change" instead.` |
| V10 | Validation — defer with no reason | `Say why the pay decision is being put off.` |
| V11 | Validation — promotion with no pay change and no reason | §11.2 |
| B4 | **Blocked — chain has no pay-capable approver** | §10.4(a) |
| B5 | **Blocked — one person satisfies two levels** | §10.4(b) |
| P5 | No `compensation:r` ⛔ *(A1 / CFL-42-13 — my Wave 2 answer let the control be routed around)* | The whole fieldset is absent, as before — **but the request now records `NOT_ANSWERED_NO_PERMISSION` rather than "no pay change", and the first approver who holds `compensation:r` must answer the pay question before they can approve.** Their review dialog shows the pay block with `Nobody has answered the pay question — the person who raised this can't see pay.` and Approve is unavailable until they do. This satisfies D4c and D4f at once, which my version did not: a manager without pay sight was able to make the mandatory pay decision disappear, and managers raise most moves |
| S2 | Success — money-bearing | The existing success panel gains one line: `The pay change is part of this request. Nothing is applied — not the move and not the pay — until the last approval.` |

### 10.7 Accessibility — the pay block

- **Keyboard path:** … location → **pay radios** (arrows move within the group, `Tab` exits) → any revealed fields
  in DOM order → reason → `Cancel` → `Submit for Approval`.
- The radio group is a real `<fieldset>`/`<legend>`; the helper sentence is the fieldset's `aria-describedby`.
- Revealing fields moves **no** focus (the user is mid-decision); it announces
  `New salary selected. Three more fields added.` to `#live-status`.
- The request-type line and the chain line are `role="status"`, so a change of either is announced without
  interrupting.
- The conflict panel is `role="alert"` and receives focus, because it means nothing was submitted.
- Below 768px the radios stack full-width at ≥44px each and the three salary fields become one column.

---

## 11. KAN-197 — Promotion as a request type

### 11.1 Entry points — three, all onto the same dialog

1. **Profile → Job Level card → `Request promotion…`** (§8.1) — the main one, because you decide a promotion while
   looking at the person.
2. **The top-step signal's `Review →`** — lands on the profile Job Level card, not on a pre-filled request. The
   signal prompts a review; it does not presume the outcome.
3. **The shared modal itself** — changing the level select in a transfer turns it into a promotion (type inference,
   §10.3).

All three are gated `has_feature_access('compensation','r')` **and** `_can_initiate_for` **and**
`employment_status == 'ACTIVE'` **and** `not is_own`. No employee can initiate their own promotion, through any
route (SPM D4a keeps KAN-139 for every request type).

### 11.2 The Job level block in the shared modal

Placed **above** the Pay block — level first, because the level drives the title and the band, and the pay decision
is made in light of it.

```
┌───────────────────────────────────────────────────────────────┐
│  Job level                                                    │
│  Currently Engineering · level 1 · step 1.5 · Software Engineer│
│  New level  [ Engineering ▾ ] [ Level 2 ▾ ] [ Step 2.1 ▾ ]    │
│  → Ravi's job title becomes "Senior Software Engineer".       │
│  → The range for level 2 in Germany is €72,000 – €96,000.     │
└───────────────────────────────────────────────────────────────┘
```

The two `→` lines are a **live consequence preview**, `role="status"`. The title change is the thing that surprises
people; the range is what makes the next decision (pay) informed. The range line renders only for
`compensation:r` **and** only where a band exists.

**"No change" on a promotion requires a reason** (SPM D4c). Selecting `No change` under Pay while the level has
changed reveals a required textarea:

> `Why is there no pay change with this promotion? *`
> `A promotion with no pay movement needs a recorded reason.`

Validation: `Say why this promotion has no pay change.`

**Below the band after promotion** — a common and legitimate case worth designing rather than leaving to a generic
warning:

> `€72,000 is below the range for level 2 in Germany (€78,000 – €96,000). That's allowed — say why in the reason.`

### 11.3 Downward and sideways level moves — **resolved by the `LEVEL_CHANGE` rename**

> ⛔ **SUPERSEDED — and this is a simplification for me, not a compromise.** I raised the vocabulary defect
> (a demotion labelled "Promotion" in the inbox, bell, timeline and audit trail) and proposed a **derived display
> label** as a workaround. The SPM rejected both my option and the BA's fourth-enum-value option in favour of a
> third: **rename the type to `LEVEL_CHANGE` and store a `direction` of `UP` / `DOWN` / `LATERAL`**
> (CFL-42-25). He is right that a display label cannot fix an audit action that says `PROMOTION_APPLIED` for a
> demotion — a lie in the durable record is not a presentation problem. **My workaround table is deleted.**

**The rule now, and it is simpler:**

| `direction` | User-facing word, everywhere | Stored type | Audit |
|---|---|---|---|
| `UP` | **Promotion** | `LEVEL_CHANGE` | `LEVEL_CHANGE_APPLIED`, direction `UP` |
| `DOWN` | **Level change** | `LEVEL_CHANGE` | `LEVEL_CHANGE_APPLIED`, direction `DOWN` |
| `LATERAL` | **Level change** | `LEVEL_CHANGE` | `LEVEL_CHANGE_APPLIED`, direction `LATERAL` |

- **"Promotion" stays the user-facing word when the direction is up** — R4 asked for a promotion flow, not an
  enum literal, and telling somebody they have a "level change (up)" would be a worse product.
- The entry point on the profile is `Request a level change…` and the modal's live type line reads
  `This will be raised as a **Promotion**.` once the direction resolves upward — the word appears where it is
  true, and nowhere else.
- One word per direction, identical in the modal, the inbox, the bell, My Requests, the timeline and the audit
  trail, per the Demo Gate's status-vocabulary rule.
- **All of §10 and §11's other copy is unchanged**; only the type name and the direction-derived word move.

A downward move gets the destructive treatment:

> ⚠ `This moves Ravi down from level 3 to level 2.`
> `Their job title in the directory and org tree changes from Staff Engineer to Senior Software Engineer.`
> `Their pay doesn't change unless you change it here.`
> `☐ Yes, move Ravi down to level 2.`
> Commit: `[ Submit level change for approval ]`, `.btn-danger`, disabled until ticked.

### 11.4 Every state — promotion

| # | State | What the user sees |
|---|---|---|
| E16 | **No ladder in the company** | The Job level block is absent and `Request promotion…` does not render. The profile card shows `Your company hasn't set up a job ladder yet.` |
| E17 | Subject not on a level | Block renders with `Currently: not assigned to a level.` and `New level` required; a muted line `This will be Ravi's first level assignment.` |
| E18 | Already at the top level | `Engineering has no level above 3.` + `To promote beyond the top, add a level to the ladder or move Ravi to another family.` |
| PD4 | Family has one level | Level select shows the single level, disabled, with `Engineering has only one level.` |
| V12 | Validation — level unchanged but promotion entry used | `Choose a different level, or use "Advance step" if only the step is changing.` + a link that closes this dialog and opens §8.2 |
| V13 | Validation — step not in the new level | Not possible: the step select repopulates from the chosen level, and an out-of-range step resets to 1 with `Level 2 has 3 steps, so the step is now 2.1.` |
| S3 | Success | `✓ Promotion submitted for approval.` `Ravi's move to Senior Software Engineer and his pay change are with HR Admin (approval 1 of 2). Nothing is applied until the last approval.` `[ View in Position Changes ] [ Done ]` |
| S4 | Applied (seen by the requester later) | Bell receipt, §15. The profile's Job Level and Compensation cards both reflect the change from the effective date |

---

## 12. KAN-198 — Four eyes on money

> A two-level control that one person can satisfy twice is one-person control. On money it stops being theoretical.
>
> ⛔ **EXTENDED by Wave 3.** Four rules were added after my Wave 2 spec, three of them found independently by
> UAT, the Architect and me from different angles. All four change what a user sees, so they are designed here.
>
> | Rule | Source | What it changes on screen |
> |---|---|---|
> | **The initiator may not decide any level** of a money- or level-bearing request | CFL-42-31 | §12.2's statement panel gains a second variant |
> | **A money-bearing request needs ≥2 independently satisfiable levels, refused at create** | CFL-42-11 | §10.4(b), already designed — but it now also fires on the **default single-level chain**, i.e. every tenant today |
> | **A two-level default chain (HR_ADMIN → PORTAL_ADMIN) is seeded** for money-bearing types | CFL-42-11 | §12.1's advisory must not fire spuriously on the new default |
> | **Four-eyes binds SYSTEM_ADMIN, with a cancel-not-approve remedy** | Ruling 13 / ADR-022 | §12.3 gains the remedy |
> | *(separately)* **subject ≠ initiator and subject ≠ decider**, universally | KAN-203, P0 defect fix | §12.6 |
>
> **The one I want to underline: the control was a silent no-op.** On the seeded default chain — one HR_ADMIN
> level — KAN-198 would have shipped, passed its tests and prevented nothing. A control that passes its tests
> while doing nothing is worse than no control, because the organisation now believes it has one. That is the
> same failure shape as DEF-001 (the plumbing existed; nothing called it).

Three surfaces, and the most important one is the earliest.

### 12.1 At configuration time — the cheapest place to fix it

`templates/admin/org_change_workflow.html` gains an inline advisory under the affected rows, amber
`#fffbeb`/`#fde68a`/`#b45309`, `role="status"`, **non-blocking**:

> ⚠ **Levels 1 and 2 can both be satisfied by the same person.** Priya Nair is your only HR Admin, and she is also
> the named approver at level 2.
> For a change that moves pay or a job level, the portal requires a different person at each level — with this
> chain, those requests can't be submitted at all.
> Add a different approver at one of these levels, or give the HR Admin role to someone else.

Rendered whenever the resolved approver sets of two steps intersect and the intersection is the whole of one of
them. The page also gains a permanent explanatory line under its existing intro paragraph:

> `Changes that move pay or a job level always need two different people. Placement-only changes don't.`

### 12.2 At decision time — absent, not refused

An approver who has already decided one level of a money-bearing request:

- **does not see the request in their bell**, and
- **does not see it in `Pending My Approval`**, and
- if they arrive by a deep link, the review modal opens with the diff visible and the Approve/Reject buttons
  **absent**, replaced by a statement panel:

> **You've already decided this request.**
> You approved level 1 on 9 August 2026. A change that moves pay or a job level needs a different person at each
> level, so somebody else has to decide level 2.
> `[ Close ]`

Absent, not disabled: you cannot act, so no control is rendered. And showing work in a queue that the viewer is
forbidden to complete is DEF-001's failure in reverse — a call to action that is not actionable.

### 12.3 The stall this creates, and where it surfaces

If the only holder of the level-2 role already decided level 1, the request can never be decided. Two defences:

1. **Refuse at create time** (§10.4b) — the primary defence, and the one that means the stall usually never
   happens.
2. **When it happens anyway** (the role holder changed after submission), the **requester** sees it on their
   `My Requests` row:
   > `⚠ Waiting — nobody else can approve level 2` `[ Why? ]`
   `[ Why? ]` opens a small panel: `Priya Nair approved level 1, and she is the only person who can approve level 2.
   A change that moves pay needs a different person at each level. Ask your Portal Admin to change the approval
   chain, then cancel and raise this again.`

Naming the fix is the difference between "the software is broken" and "the configuration needs a change".

**(A1 / Ruling 13) The administrative remedy, because a permanently undecidable request makes somebody edit the
database.** A SYSTEM_ADMIN may **cancel** a stuck request — never approve it. On the request row:

> `[ Cancel this request ]` — SYSTEM_ADMIN only, with a mandatory reason.
> **Cancelling applies nothing.** `Nothing about Ravi's placement or pay changes. Reconfigure the approval chain,
> then raise the request again.`
> `Why is this being cancelled? *`

The button is `.btn-ghost` in `#b91c1c`, never `.btn-primary`, and it is never placed adjacent to Approve. The
distinction *cancel is not approve* is the whole of the ruling and the UI must not let a tired admin blur it.
Cancellation is audited and notifies the requester with the reason.

### 12.6 *(Wave 3, KAN-203)* Subject ≠ initiator, subject ≠ decider — a defect fix, not a policy

Two Critical pre-existing defects: `_can_initiate_for` never compares the initiator to the subject, and
`decide()` never compares the decider to the subject. Today an HR_ADMIN can raise a position change for
themselves and approve it. Fixed in W0 at P0. **The UX consequence is small and must be exactly right:**

- **`Transfer…`, `Advance step…`, `Request a level change…` and `Record a change…` are absent on your own
  profile and your own directory row** — for every role, including SYSTEM_ADMIN. This is already how §3.2's
  "nothing" rule works; what changes is that it now also holds for admins, who previously saw the controls.
- A request that reaches a level **you are the subject of** is absent from your bell and your pending list, and a
  deep link shows: `This request is about you. Somebody else has to decide it.` `[ Close ]`
- The messages name the rule, not the mechanism: `You can't raise a change to your own position.` /
  `You can't decide a change to your own position.`
- **No exception for SYSTEM_ADMIN**, and the copy does not offer one. The remedy is the same cancel path above.

### 12.4 Placement-only self-approval — warn, allow, record

Unchanged behaviour, made visible. In the review modal, above the buttons, amber `role="status"`:

> `You raised this request. Approving your own placement-only request is allowed, and it's recorded in the audit
> trail as a self-approval.`

No blocking, no checkbox. The SPM's split (hard rule on money, warn-and-audit on placement) is deliberate and the
copy makes the difference legible rather than mysterious.

### 12.5 Every state — four eyes

| # | State | What the user sees |
|---|---|---|
| B6 | Blocked at create | §10.4(b) — nothing written |
| B7 | Blocked at decide | §12.2 — no controls |
| W1 | Warned at configuration | §12.1 — amber, non-blocking |
| W2 | Warned at self-approval, placement only | §12.4 |
| E19 | Stalled request | §12.3 |
| PD5 | Chain resolves to a role with zero holders | Existing EP38 behaviour applies; the configuration advisory adds `No one currently holds the Finance role in your company.` |
| A11y | — | The configuration advisory is `role="status"` and referenced by `aria-describedby` from both affected level rows, so a screen-reader user meets it at the row, not only at the top of the page |

---

## 13. KAN-205 — Bands and compa-ratio *(was KAN-199)*

> ⛔ **REPOSITIONED by Wave 3 and A1.** Two changes, neither of which resizes the screen. **(1)** KAN-199 split
> (Ruling 32): **pay markets** are a hard prerequisite and moved to W2 as KAN-199; **bands** became KAN-205 in W4.
> **(2)** A1 demoted the band from *the comparison basis* to **the level's min/max envelope** — "is this pay sane
> for this level at all?" The basis is now the **step pay point** (§23). The band editor below is unchanged; what
> changes is what it is *for*, and therefore its copy.
>
> **The copy consequence, and it is the whole of the amendment for this screen:** the band footer sentence stops
> being about equity findings and becomes about sanity. Replace
> *"Bands are guidance. Pay outside a band is allowed…"* with:
>
> > `A band is the outer range for the whole level. The pay-equity check doesn't use it — that compares against
> > each step's own pay point. A band is the sanity check: pay outside it is allowed, the portal asks why, and it
> > records the answer.`
>
> **Compa-ratio survives, and its meaning narrows.** It is a **band-position fact**, shown on the Compensation
> card and in the group drill-down for `compensation:r` holders. It is **no longer a finding basis** and the
> 0.95 / 1.10 thresholds are withdrawn (SPM §14.7 item 5). OQ-BA-1's better answer applies: a group of one
> compared to a band is a band-position fact, not an equity finding, and it already surfaces on the card — the
> information is available, it simply is not a flag.
>
> **Pay markets (KAN-199, now W2)** keep §13.2 exactly as specified, including the multi-currency merge refusal —
> plus one addition from OQ-BA-3: **`monthly_payments_per_year` is a property of the pay market, not the
> company.** Acme spans Porto (14 statutory payments), Hamburg and Tallinn (12) in one company, so a
> company-level constant is wrong by ~17% for the only real example we have. The pay-market editor therefore
> carries `Payments per year [ 14 ]` with the helper `Some countries pay a 13th or 14th month. This is used to
> work out an annual figure from a monthly one.`

## 13.0 Bands and compa-ratio *(screen spec, unchanged below except where marked)*

### 13.1 The Salary bands tab

A grid: rows are levels (grouped by family), columns are pay markets. Every cell is a button.

```
┌ Salary bands ───────────────────────── [ 👁 Hide amounts ] [ Manage pay markets ] ┐
│                                                                                   │
│  Engineering            Germany (EUR)        Portugal (EUR)      Estonia (EUR)    │
│  ────────────────────────────────────────────────────────────────────────────     │
│  L3 Staff Engineer      96,000 · 114,000     Not set             Not set          │
│                         · 132,000                                                 │
│  L2 Senior SWE          72,000 · 84,000      54,000 · 63,000     Not set          │
│                         · 96,000             · 72,000                             │
│  L1 Software Engineer   58,000 · 66,000      44,000 · 50,000     Not set          │
│                         · 74,000             · 56,000                             │
│                                                                                   │
│  Bands are guidance. Pay outside a band is allowed — the portal asks why and       │
│  records the answer. It never blocks it.                                          │
└───────────────────────────────────────────────────────────────────────────────────┘
```

- Each cell reads `min · midpoint · max`, in that order, with the midpoint in weight 600 because it is the
  comparison basis (SPM D1).
- `Not set` is the empty state — **never** `—` or `0`. Its cell button reads `Set a band` on hover/focus.
- The footer sentence is permanent. It is the single most important thing to say about bands, because an HR admin's
  first assumption is that a band is a limit.

**Cell editor** (dialog): Minimum · Midpoint · Maximum · Currency (fixed to the market's, read-only with
`The pay market sets the currency.`) · Effective from · Reason.
Validation:
- `The midpoint has to sit between the minimum and the maximum.`
- `The maximum has to be more than the minimum.`
- `There's already a band for level 2 in Germany from 1 January 2026. Choose a later date.`
- Warning, not an error: `This band overlaps level 1's band (€58,000 – €74,000). Overlapping bands are normal.`

**Effect preview before save** (same discipline as §6.5):

> **What this does to people**
> 8 people are on level 2 in Germany. With this band: 6 are in range, 1 is below, 1 is above.
> `[ See who → ]`
> Nobody's pay changes. Nobody is notified. Pay equity will re-check this group.

That last line matters: changing a band changes the comparison basis and therefore can raise or close findings. An
admin who is not told that will be surprised by the bell an hour later.

### 13.2 Pay markets

Reached from `[ Manage pay markets ]`. Default: **one market per `locations.country`** (SPM D1), listed with the
locations inside each.

```
Germany (EUR)     Hamburg                         3 employees
Portugal (EUR)    Porto                          11 employees
Estonia (EUR)     Tallinn                        32 employees
                                                 [ Merge markets… ] [ Split a market… ]
```

**Merging markets with different currencies is refused** (SPM D1 — no silent 1:1, no implicit conversion):

> ⚠ **These markets can't be merged.**
> Sweden pays in SEK and Estonia pays in EUR. Comparing them needs an exchange rate for every currency in the
> market, and the portal doesn't hold exchange rates.
> Keep them separate, or ask your Portal Admin about exchange rates.

No override, no "use 1:1 for now". A silently converted comparison is a wrong finding, and the first wrong finding
costs the feature its credibility permanently.

### 13.3 Compa-ratio display

- Shown only to `compensation:r` (it is derived money — D-R9).
- Always **glyph + word + number**, never colour alone:
  `▼ Below range · 0.88` · `◆ In range · 0.96` · `▲ Above range · 1.14`
- Colours from the accessible pairs: `#b45309` on `#fffbeb` (below/above), `#475569` on `#f1f5f9` (in range).
  Below and above use the **same** amber, distinguished by glyph and word — because "above range" is not a
  worse or better state than "below range" and colouring one red would editorialise.
- **Never shown to the employee about themselves** — My Pay uses the five word-phrasings (§9.2 rule 3).
- Absent entirely where no band exists. Never `n/a`.

### 13.4 Every state — bands

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | Skeleton grid |
| E1 | Empty — no ladder | `You need a job ladder before you can set bands.` + `[ Build the job ladder → ]` |
| E2 | Empty — no locations | `Your company has no locations, so there are no pay markets yet.` + `[ Add locations in Admin Panel → ]` |
| E3 | **Empty — no bands at all** | The grid renders with every cell `Not set` plus a card-level line: `No bands set. Pay equity still works without them — it compares people against their group's median instead. Bands make it compare against what you intended.` This is the honest framing: bands are a Should, not a blocker |
| PD1 | Partial — some cells set | The normal state. Findings state which basis was used, per finding |
| PD2 | Partial — band exists, nobody on that level | Cell shows the band and a muted `0 people` |
| V1–V4 | Validation | §13.1 |
| B1 | Blocked — multi-currency merge | §13.2 |
| E4 | Error — save | `We couldn't save this band, so nothing has changed. Your figures are still here — try again.` |
| P1 | `r` without `w` | Grid visible, read-only, no cell is a button, no `Manage pay markets` |
| P2 | No `compensation` | Tab absent |
| S1 | Success | `✓ Band saved for level 2 in Germany.` + `Pay equity will re-check 8 people in this group.` |

---

## 14. KAN-200 / 201 / 202 — The pay-equity register, the flag lifecycle, and the timeline

> ⛔ **SUPERSEDED IN PART by A1 — the reference value changed, and with it most of this section's numbers.**
> The primary check is no longer statistical. It is **Check A′: does this person's pay match the step they are
> on?**, measured against **their own step's configured pay point** within a **tolerance** (default ±2%). No
> group, no median, no peers, **no `n ≥ 3` minimum, no 80% coverage gate** (SPM §14.2).
>
> | What I specified in Wave 2 | Status | What replaces it |
> |---|---|---|
> | Basis: band midpoint, else group median | **Superseded** | The step pay point (§23) |
> | Compa-ratio thresholds 0.95 / 1.10 | **Superseded** | Tolerance ±2% around the pay point |
> | `n ≥ 3` minimum on Check A | **Withdrawn** for the primary check | **n = 1 is a valid, meaningful check.** Retained in full for Check B |
> | The 80% coverage gate and its below-gate screen (§14.4 E1) | **Withdrawn** for the primary check | **The fitted-step review gate** (§7.9). Retained for Check B |
> | One finding type, `OUTLIER` | **Superseded** | **Three** — `PAY_BELOW_STEP` (primary), `PAY_ABOVE_STEP` (secondary, lower severity, different copy), `GENDER_GAP` (unchanged) |
> | *(nothing)* | **New** | **`Propose adjustment`** — the finding carries its own remedy (§14.7). The best thing A1 gives this screen |
>
> **Check B — the gender pay gap — survives statistically intact**, group formation, `n ≥ 5`, ≥2 of each gender,
> median arithmetic, `OTHER`/`NULL` excluded-and-counted, `|gap| ≥ threshold` with direction recorded, and
> CFL-42-32's no-aggregate-below-n=5. **Do not let the clear-out take it** — that is the specific risk in this
> amendment, and the SPM said so.
>
> **What this does to the screen, in one line:** the register stops being a statistics review and becomes a
> worklist of people whose pay and job have come apart, most of which can be fixed from the row.

### 14.1 The framing sentence — on every equity screen, not in a tooltip

SPM D1.3 requires plain-language framing that this is a measurement, not a compliance conclusion. One paragraph,
identical on the queue, the group drill-down and the disposition dialog, in `#f8fafc`/`#e2e8f0`, always visible,
never collapsed:

> **This is a measurement, not a verdict.** *(A1 wording.)* The portal compares what someone is paid with the pay
> point your company has set for the step they're on. It doesn't know about bonus, benefits, performance,
> experience, or anything agreed outside the portal, and it can't decide whether a difference is justified. That
> judgement is yours — the portal records it.

*(The gender-gap section of the register carries the Wave 2 wording instead, because that check **is** a
comparison between people: "The portal compares recorded base salaries inside one job level and one pay
market…". Two checks, two honest descriptions; one paragraph covering both would be true of neither.)*

Never abbreviated, never turned into an `ⓘ` icon, never behind a "learn more". A screen that produces findings about
people's pay carries its own caveat at full size.

### 14.2 The register — `/compensation/equity`

Gate `@require_feature_access('pay_equity')`. Nav item **Pay Equity**, Administration section.

```
┌ Pay Equity ────────────────────────────────────── [ 👁 Hide amounts ] [ Run check ] ┐
│  6 people are paid below their step · last checked 9 August 2026, 14:32             │
│                                                                                     │
│  [ framing paragraph — §14.1 ]                                                      │
│                                                                                     │
│  ( Pay below step · 6 )  ( Gender pay gap · 1 )  ( Pay above step · 23 )  ( Dealt   │
│                                                                    with · 14 )      │
│                                                                                     │
│  State [ Open ▾ ]   Level [ Any ▾ ]   Market [ Any ▾ ]   Owner [ Anyone ▾ ]         │
│                                                                                     │
│  Person           Level & step        Paid      Step pay pt   Difference   Owner    │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│  Ravi Sharma      Eng · Trainee 1.4   €69,000   €72,930       ▼ 5.4% below  —       │
│    on step 1.4 since 4 Mar 2026 · raised 12 days ago                                │
│    [ Propose adjustment → €72,930 ]   [ Review → ]              [ Take ]            │
│                                                                                     │
│  Ana Costa        Eng · Junior 2.2    €66,000   €70,720       ▼ 6.7% below  P. Nair │
│    Re-opened 2 days ago — the proposed adjustment was rejected on 12 Aug            │
│    [ Propose adjustment → €70,720 ]   [ Review → ]                                  │
│                                                                                     │
│  Otto Braun       Fin · Analyst 1.1   €54,000   €57,500       ▼ 6.1% below  —       │
│    Open · an adjustment is proposed and awaiting approval (1 of 2)   [ Follow → ]   │
│  …                                                                                  │
│                                                                                     │
│  11 people couldn't be checked. [ Why? ]                                            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**(A1) Three finding types, and they are not peers. The tab strip is the design.**

| Type | Tab label & order | Severity treatment | Notification | Row copy |
|---|---|---|---|---|
| **`PAY_BELOW_STEP`** | **`Pay below step`, first, and the register's default view** | `badge-amber` + `▼ below` + the word. Counted in the header line and in the bell badge | **Yes** — bell, `⚖️`, `Review →` | `Ravi is on step 1.4 but paid about 5.4% below the pay point for it.` |
| **`GENDER_GAP`** | `Gender pay gap`, second | `badge-amber` + direction word. Group-level, statistical, unchanged from Wave 2 | **Yes** — bell, `⚖️` | unchanged |
| **`PAY_ABOVE_STEP`** | **`Pay above step`, third, and explicitly framed as secondary** | `badge-gray` + `▲ above` + the word. **Not counted in the header line** | **No notification at all** — see below | `Ana is paid about 4.1% above the pay point for step 1.2. That's often deliberate.` |

**`Pay above step` gets its own tab with a permanent framing line, and no bell entry:**

> `Pay above the step's pay point is legitimate far more often than not — a market premium, a retention
> adjustment, or pay held at its old level after a change. These are here so you can see them, not as a list of
> things to fix.`

⚠ **This is a design decision the SPM should ratify, not a reading of his text — recorded as UX-A1-C2.** SPM
§14.1 gives `PAY_ABOVE_STEP` "lower severity and different copy" but does not say it is silent. I am specifying
**silent**, for three reasons: it is the alert-storm vector (before the fitted-step backfill it would have been
most of the workforce, and it will re-appear in bulk whenever a company raises a pay point); it is usually
correct; and it has no computable remedy, so a notification with a `Review →` leads to a screen where the honest
answer is "nothing to do". If he disagrees, the fallback is a bell entry that is **not** badge-counted.

**Amended design decisions for the register table:**

| Decision | Change from Wave 2 | Why |
|---|---|---|
| **Default sort** | Still oldest first, **not by size of difference** | Unchanged reason: the most-shared screen in the epic must not open as a ranked list of the most underpaid people in the company (§3.5) |
| **Columns** | `Group` and `Basis` are **gone**; `Paid`, `Step pay point` and `Difference` replace them | There is no group in the primary check any more. `Basis` was only ever needed because there were two |
| **`Paid` and `Step pay point` are money** | Absent without `compensation:r` (D-R9, CFL-42-19), replaced by a `Finding` column reading `Paid below the pay point for this step` | Ratified as CFL-42-19; a difference percentage plus one known figure is the other figure |
| **The `on step 1.4 since 4 Mar 2026` sub-line** | New | It is the evidence for the owner's actual concern — *how long has this person been doing the bigger job for the old money* — and it is the first thing a reviewer needs |
| **`11 people couldn't be checked. [ Why? ]`** | Replaces `2 of 14 groups couldn't be compared` | Per-employee preconditions, not group coverage. The panel lists each reason with a count and, where fixable, the action: `4 have no salary recorded [ Import → ]` · `3 aren't on a step [ Assign → ]` · `2 have no pay point set for their step [ Set pay points → ]` · `1 has no pay market [ Set up markets → ]` · `1 is a contractor — excluded by design` |
| **Not-evaluable is never invisible** | Reinforced | An employee the check silently skipped is the failure mode that makes a compliance number a lie |

| Design decision | Why |
|---|---|
| **Default sort: oldest finding first**, not largest gap | The most-shared screen in the epic must not open on a ranked list of the most underpaid people in the company (§3.5). Age is also the metric the SPM measures (`median days to disposition`) |
| **`Measured` and `Basis` columns are absent** for a viewer with `pay_equity:r` but **not** `compensation:r` | D-R9. Replaced by a `Finding` column: `Below the expected range for this level` / `Above the expected range` / `Gender gap above your threshold`. The workflow (read, judge, record a reason) still works; the invertible number does not leave |
| Every state is a `.badge` with a **word** | Never colour alone |
| Direction is `▼` / `▲` **plus** the word in the row's accessible name | Never colour alone (1.4.1) |
| Group-level findings (Check B) show `Whole group` as the subject | A gender-gap finding is about a group; putting a person's name on it would be wrong and would personalise a statistic |
| **`[ Take ]`** sets the owner to you | A recorded act, not a read. See §14.3 for why this matters to the badge |
| **No bulk disposition** (SPM D2) | Every disposition needs its own reason |
| The `2 of 14 groups couldn't be compared` footer is permanent | "8 findings" must never be mistaken for "8 problems in the whole company" |

**Group drill-down** (clicking the level & market cell) — the context needed to judge:

```
Engineering · Level 2 · Germany
6 compared · 3 excluded (1 contractor, 2 with no salary recorded) · coverage 75% ⚠

Basis: the band midpoint for level 2 in Germany (€84,000).

  Ravi Sharma      step 2.3   ▼ 0.88   €74,000
  Ana Costa        step 2.1   ◆ 0.97   €81,500
  …

Excluded from the comparison
  Tom Rieder       Contractor — not comparable
  Lena Fischer     No salary recorded
  Otto Braun       No salary recorded

Step is not part of the comparison — steps are meant to differ in pay. It's shown here to
help you judge.
```

- Individual amounts in the drill-down require `compensation:r` (D-R9); a `pay_equity`-only viewer sees the names,
  steps and directions without the figures.
- **Exclusions are counted and named, never silent** (SPM D1). The two "no salary recorded" rows are the most
  useful thing on this screen: they say *why* the finding might be wrong.
- The step caveat is permanent, because "why isn't step in the comparison?" is the first question every HR admin
  asks.

### 14.3 The flag lifecycle — and the answer to "does a standing condition ever retire?"

> This is the hard case the SPM handed me: **a pay-equity flag is a standing condition, not a task.** Does it ever
> retire, does it re-fire, and what does the recipient see if they dismiss it and the condition persists?

**The design separates two objects that engineers and users both tend to merge:**

| | **The finding** (the condition) | **The notification** (the delivery) |
|---|---|---|
| Lives in | the register | the bell |
| Ends when | somebody records what was decided, or the data changes so the gap is gone | the finding leaves `OPEN` |
| Can be dismissed | **No** | **No** |
| Counted | in the register's `8 open findings` | in the bell badge (see below) |

**The five rules:**

1. **There is no dismiss, anywhere.** The bell item for a finding has one action, `Review →`. No `✕`, no
   "mark as read", no swipe-away, no "not relevant". Dismissing a standing condition is a decision with no
   record — precisely what SPM D2 rules out for disposition, and DEF-003 in reverse (a call to action that
   disappears while the thing it referred to is still true). If a user could clear it, the condition would persist
   invisibly and the register would rot.

2. **Reading is not deciding, and the badge must not pretend otherwise.** The notification does not retire on read
   (SPM D2, asserted by test). It retires **only** when the finding leaves `OPEN` — on `JUSTIFIED`,
   `REMEDIATION_PLANNED`, `RESOLVED` or `RESOLVED_BY_DATA` — and it retires **for every eligible recipient**, not
   only the person who acted, via `resolve_related()` with `related_type='pay_equity_flag'` (DEF-003's actual
   defect).

3. **The bell section cannot grow into a stack.** It renders at most **five** findings, newest first, with a
   footer `+ 7 more open findings · Review all →`. It never re-announces a finding it has already delivered. A
   bell section that grows without bound is the thing HR mutes, and a muted compliance channel is worth zero
   (SPM R-1).

4. **The badge counts findings nobody has picked up — not all open findings.** *This is my one substantive
   departure from D2's wording, and §20 UX-CFL-42-2 records it with the fallback.*
   - **The problem with counting every open finding:** dispositions legitimately take days (the SPM's own target is
     a 15-working-day median), so the badge would sit permanently non-zero. A badge that never reaches zero stops
     meaning "something needs you", and the *approvals* it shares a number with get lost inside it. That is
     alert fatigue arriving through a different door than the one R-1 is watching.
   - **The design:** the badge counts open findings with **no owner**. `[ Take ]` — a recorded, audited action, not
     a read — assigns you as owner and decrements the badge. The finding stays `OPEN`, stays in the register, and
     **stays in the bell section** (now showing `Yours · in progress`). Nothing is hidden; only the "nobody has
     picked this up" signal clears.
   - **Fallback if the SPM keeps D2 as written:** count every open finding, and mitigate by decomposing the bell
     header so the number can be read — `Pending Approvals (2)` · `Position Changes (1)` ·
     `Pay Equity (8 open findings)` — and by stating on the register `Findings stay open until somebody records
     what was decided.` The decomposed headers ship either way.

5. **A re-fired finding must not look like a new one.** When the anti-fatigue window expires or one of D2's
   re-fire conditions is met, the finding returns as **`Re-opened`**, never as a fresh finding, and it says why:
   - `Re-opened — the gap has widened since it was justified.`
   - `Re-opened — Ravi's level, step or salary changed.`
   - `Re-opened — your company changed the threshold or the pay markets.`
   The register row and the disposition dialog both show the previous decision:
   > `Previously justified on 4 March 2026 by Priya Nair — Market premium: "hired against a competing offer".`

   Without this, the anti-fatigue rule produces a *worse* fatigue: every re-fire is indistinguishable from a new
   problem, and the reviewer re-types the same justification from memory. **This is a requirement, not a nicety.**

6. **A finding that closes because the data changed is announced, not silent.** `RESOLVED_BY_DATA` retires the
   call to action and sends one informational notification to the same recipients:
   > `A pay-equity finding for Ravi Sharma has closed — the gap is now below your threshold.`
   Icon `✅` (an outcome really happened), My Notifications section, **not counted** in the badge, normal
   read-and-forget lifetime. Silently removing a finding somebody was working on would look like a bug.

7. **The subject is told nothing.** The person a finding is about is not a recipient, gets no notification, sees no
   marker on their profile and nothing in My Pay.
   *Reasoning, stated because the instinct from EP38 ("tell the subject what happened to them") points the other
   way here:* a finding is an **unverified measurement**. Telling an employee the system thinks they may be
   underpaid — before any human has looked at it, and when 40%+ of findings are expected to be dispositioned as
   justified — creates an expectation the company may not be able to meet and a grievance when it cannot. The
   employee is told when something actually changes: their pay.

8. **When the audience empties.** If the last holder of `pay_equity:r` loses it, open findings have no recipient.
   The register still holds them, and the Feature Access tab and `/compensation` Settings both show:
   > ⚠ `12 open pay-equity findings have no recipient. Nobody in this company currently has Pay Equity access.`
   An unwatched compliance queue is worse than no queue, and this is the only place the condition is visible.

### 14.4 Empty and partial states — where the dangerous screen lives

| # | State | What the user sees |
|---|---|---|
| **E1** ⛔ *(A1 — replaced)* | **The fitted-step review isn't complete** | ⛔ *Was: the 80% coverage gate. Withdrawn — there is no statistical group left to be half-populated.* **The queue still does not render an empty list.** It renders the gate panel: `Pay equity isn't running yet.` + `It's waiting on your step review — we need you to confirm which step each person is on before we compare anyone's pay to it.` + the progress `118 of 146 confirmed` + `[ Continue the review → ]`. **The words "no findings" must not appear on this screen.** The reasoning is unchanged and is the most important sentence in this table: a screen that says "no findings ✓" while the check has never run is the most dangerous thing we could ship |
| **E1a** *(A1)* | **Review complete, but nothing is configured to compare against** | `Pay equity is on, but no pay points are set.` `The check compares each person's pay to the pay point for their step. Engineering has no pay points yet.` + `[ Set pay points → ]` for `compensation:w`. Zero findings, and it says why rather than implying health |
| E2 | Never run | `Pay equity hasn't been run yet.` + `[ Run check ]` + the framing paragraph |
| **E3** ⛔ *(A1 — reworded)* | **Genuinely nothing found** | `Nobody is paid below their step.` **always followed by what was looked at**: `Last checked 9 August 2026 at 14:32. 135 people were checked; 11 couldn't be. [ Why? ]` "Nothing found" may never be rendered without "here is what we looked at" — the rule survives A1 exactly, only its numbers change from groups to people |
| **E4** ⛔ *(A1 — now Check B only)* | Every group too small **for the gender-gap check** | On the `Gender pay gap` tab only: `No group is big enough to compare. The gender pay gap check needs at least 5 people on the same level in the same pay market, with at least 2 of each gender.` + `[ See your groups → ]`. **This state no longer exists for the primary check** — n = 1 is valid there |
| **E4a** *(A1)* | Check B has no gender data | `We can't run the gender pay gap check — gender isn't recorded for anyone in your company.` and **not** "no gap found". A check with no input must never report a clean result *(the DEF-42-3 state; KAN-208 fixes it for the seeded tenants)* |
| E5 | Filter finds nothing | `No findings match these filters.` + `[ Clear filters ]` |
| E6 | All findings dispositioned | `No open findings. 14 have been dealt with.` + `[ See dealt-with findings ]` |
| PD1 | Some groups uncomparable | The permanent footer `2 of 14 groups couldn't be compared. [ Why? ]` → a panel listing each with its reason (`too few people` / `coverage 63%` / `more than one currency in the pay market`) and, where fixable, the action |
| PD2 | Mixed basis | Each row states its basis (`Band mid` / `Median`); a footer explains: `Where you've set a band, the portal compares against its midpoint. Where you haven't, it compares against the group's median.` |
| PD3 | A subject left the company mid-finding | Row shows `Ravi Sharma · former employee`; the finding stays open and dispositionable, because the question "was this justified" outlives the employment |
| L1 | Loading | Skeleton rows; `#live-status` → `Loading findings…` |
| L2 | **Running a check** | `[ Run check ]` → `Running…`, disabled; a progress line `Comparing 14 groups…`; on completion `#live-status` → `Check finished. 3 new findings, 1 closed. 12 of 14 groups compared.` |
| E7 | Run failed | `We couldn't finish the check. No findings have been changed.` + `[ Try again ]` |
| E8 | **Partial run** | `12 of 14 groups were compared. 2 couldn't be — their pay market has more than one currency.` + `[ Fix pay markets → ]` |
| E9 | Register load failed | `We couldn't load the findings.` + `[ Try again ]` |
| P1 | No `pay_equity` | Nav item absent; direct URL → flash + dashboard |
| P2 | `pay_equity:r` without `w` | Register visible; **no `Review →`, no `Take`** — a read-only auditor view |
| P3 | `pay_equity:r` without `compensation:r` | §14.2 — numeric columns absent, wording instead |
| P4 | Tenant switch off | §3.4 locked screen, worded for Pay Equity |

### 14.5 The disposition dialog

```
┌ Record what was decided — Ravi Sharma ─────────────────────────────── × ┐
│ Engineering · level 2 · Germany · group of 6 · raised 12 days ago       │
├─────────────────────────────────────────────────────────────────────────┤
│  [ framing paragraph — §14.1 ]                                          │
│                                                                         │
│  Previously justified on 4 March 2026 by Priya Nair                     │  ← re-opened only
│  Market premium — "hired against a competing offer"                     │
│  Re-opened because the gap has widened.                                 │
│                                                                         │
│  What did you decide? *                                                 │
│   ( ) Justified — there's a reason for this difference                  │
│   ( ) Remediation planned — we're going to change it                    │
│   ( ) Resolved — the pay has already been changed                       │
│                                                                         │
│  ── if Justified ──                                                     │
│  Category *  [ — Select a category — ▾ ]                                │
│              seniority · time in role · performance · market premium ·  │
│              legacy pay held at its old level · other                   │
│  Explain *   [                                                     ]    │
│              Anyone with Pay Equity access can read this, and it stays  │
│              on the record.                                             │
│  This justification lasts until 9 August 2027. After that the finding   │
│  is raised again, and it comes back sooner if the gap widens or Ravi's  │
│  level, step or pay changes.                                            │
│                                                                         │
│  ── if Remediation planned ──                                           │
│  Who owns it? * [ employee ▾ ]     By when? * [ date ]                  │
│  Explain *      [                                              ]        │
│                                                                         │
│  ── if Resolved ──                                                      │
│  Explain *   [                                                     ]    │
│  Only choose this if the pay has already changed. The portal will       │
│  re-check the group.                                                    │
│                                                                         │
│  There's no one-click dismissal here. A finding leaves the queue only   │
│  when somebody records what was decided, and that record is permanent.  │
├─────────────────────────────────────────────────────────────────────────┤
│                              [ Cancel ]   [ Record this decision ]      │
└─────────────────────────────────────────────────────────────────────────┘
```

- **No default selected**, for the same reason as EP38's departure type: this is a record with weight and the
  product must not put words in the reviewer's mouth.
- **The validity window is stated before saving, not discovered later.** A reviewer who does not know their
  justification expires in twelve months will be surprised and will distrust the queue.
- **The visibility of the free text is stated at the field** (role rule 4). It is read by other people and it
  survives.
- Validation: `Choose what you decided.` · `Choose a category.` · `Explain the decision — this is the record.` ·
  `Say who owns the remediation.` · `Give a target date.` · `The target date can't be in the past.`
- Success: the dialog is replaced in place — `✓ Recorded. This finding has left the open queue.` and
  `#live-status` → `Finding for Ravi Sharma recorded as justified. It has left the open queue for everyone who
  could see it.` The register row moves to its new state without a page reload.
- **No undo.** A recorded decision can be **superseded**: a non-open finding shows `[ Change this decision ]`,
  which requires a new reason and keeps both records. History is the defensibility (SPM D5.6).

**(A1) The justification categories differ by finding type**, because a single list would be wrong for two of
the three:

| Type | Categories |
|---|---|
| **`PAY_BELOW_STEP`** | Recently changed step, adjustment already planned · Recently joined at this step · Reduced hours or a phased arrangement · Pay held while performance is being discussed *(see the caution below)* · The step is wrong, not the pay · Other |
| **`PAY_ABOVE_STEP`** | Market premium · Retention adjustment · Pay held at its old level after a change (red-circled) · Recently joined above the point · The step is wrong, not the pay · Other |
| **`GENDER_GAP`** | Wave 2's list, unchanged — seniority · time in role · performance · market premium · red-circled legacy pay · other |

⚠ **One category needs a caution and I am putting it in the UI, not in a comment.** `Pay held while performance is
being discussed` is the one place in EP42 where a performance judgement can be attached to a pay record, and it
is the crack R-17 would grow through. Selecting it reveals, before the text box:

> `Record only that a discussion is happening — not what was said, and not any assessment of the person. This
> text is read by everyone with Pay Equity access and it stays on the record permanently.`

It is a legitimate reason and removing the category would push it into "Other" with worse text. The mitigation is
the sentence, and §25 lists it as the boundary's thinnest point.

**(A1) `The step is wrong, not the pay`** is a category on both step-based types, and choosing it offers
`[ Fix the step instead → ]`, which opens §7.9 filtered to that person. A finding whose real cause is a
mis-fitted step must have a route to the fix, or HR will justify the same finding every quarter.

### 14.5a *(A1)* `Propose adjustment` — the finding that carries its own remedy

> **The best thing A1 gives this screen, and it should be designed as the primary path, not a convenience.**
> Because the step pay point is computable, a `PAY_BELOW_STEP` finding knows what the answer is. The reviewer's
> job stops being "work out what this should be and go and raise it somewhere else" and becomes "yes, do that".

**Placement.** The **first** action on a `PAY_BELOW_STEP` row, before `Review →`, labelled with the number:
`[ Propose adjustment → €72,930 ]`. On `PAY_ABOVE_STEP` and `GENDER_GAP` rows it does not appear at all — there
is no computable remedy for either, and offering one would be a lie about what the product knows.

**Gate.** `pay_equity:r` + `compensation:r` + `_can_initiate_for` + KAN-203's `subject ≠ initiator`. A reviewer
who cannot initiate for that person sees `Review →` only, and the review panel says
`You can't raise a pay change for Ravi — you're not his manager and you don't hold HR Admin. [ Who can? ]`.

**What it opens.** The **shared move modal** (`_move_modal.html`) in `COMPENSATION_REVIEW` mode — not a new
dialog, not a second endpoint, not a second engine. One modal, one endpoint, one engine, now four entry points.
Pre-filled:

```
┌ Request Position Change ────────────────────────────────────── × ┐
│ Compensation review · Ravi Sharma · EMP-0142                     │
├──────────────────────────────────────────────────────────────────┤
│ This change is not applied immediately — it is submitted for      │
│ approval. It needs 2 approvals: HR Admin, then Anna Weiss.        │
│                                                                   │
│ Pay *                                                             │
│ Currently €69,000 · EUR · 1.0 FTE · since 1 Mar 2026              │
│ (•) New salary                                                    │
│     Amount [ 72,930 ]  EUR   FTE [ 1.0 ]                          │
│     The pay point for step 1.4 in Germany. +5.7% on Ravi's pay.   │
│ ( ) A different amount   ( ) Decide separately                    │
│                                                                   │
│ Reason *  [ Step correction ▾ ]                                   │
│ [ Ravi has been on step 1.4 since 4 March 2026 and his pay      ] │
│ [ hasn't been adjusted for it.                                  ] │
│                                                                   │
│ Effective from * [ 09/08/2026 ]                                   │
├──────────────────────────────────────────────────────────────────┤
│                    [ Cancel ]   [ Submit for Approval ]           │
└──────────────────────────────────────────────────────────────────┘
```

- **The amount is pre-filled and the reason text is pre-written**, both **editable**. A pre-filled figure is the
  point of the increment; a locked one would be an automated pay decision, which §3.3 D-R12 and Charter §1 both
  forbid. The reviewer can change the number, and if they do, the helper line updates to
  `€71,000 — €1,930 below the pay point for step 1.4.` so the deviation stays visible.
- **`New salary` *is* pre-selected here**, and this is the one place in EP42 where a pay option is. The
  justification: the user did not arrive at a blank dialog, they pressed a button that names the amount. The
  question "does something change?" was answered by the click. *(Contrast §8.2 and §10.2, where the user arrived
  to do something else entirely and the pay question is genuinely open.)*
- The reason category `Step correction` is added to the seeded list (UXQ3).
- Nothing else about the modal changes: four-eyes, the create-time refusals (§10.4), the effective-date rules and
  the approval chain all apply unchanged, because it is the same request.

**The finding does NOT close when the request is raised.** It closes when the **pay lands**. Between the two:

| Finding state | Row reads | Actions |
|---|---|---|
| Open, no proposal | `Open · raised 12 days ago` | `Propose adjustment` · `Review` · `Take` |
| **Proposal pending** | `Open · an adjustment is proposed and awaiting approval (1 of 2)` | `Follow →` only. **`Propose adjustment` is absent** — the pending-request guard would refuse a second one anyway, and offering a control that will be refused is worse than not offering it |
| **Proposal approved and applied** | The next evaluation closes it as **`RESOLVED`**, and the closure notification (§15.2 `PAY_EQUITY_FLAG_CLOSED`, `✅`) says why: `Ravi Sharma's pay now matches step 1.4. The finding has closed.` | — |
| **Proposal rejected or cancelled** | `Open · the proposed adjustment was rejected on 12 August` — **and it becomes actionable again** | `Propose adjustment` · `Review` |

**Why the finding must survive the request.** Raising a request is not fixing a gap; it is asking somebody. If
the finding closed on submission, a rejected pay correction would vanish from the register — and a rejected pay
correction is *precisely* the case the owner wants HR to know about. This is the same reasoning that keeps a
finding open until a decision is recorded (§14.3 rule 1), applied one layer up.

**States:** *Loading the pre-fill* — the amount field shows `Loading…`, submit disabled. *No pay point for the
step* — the button is absent and the row's `Why?` explains. *Subject has a pending request already* — the
existing `AC-185-08` conflict panel, worded `Ravi already has a change waiting for approval. That one has to be
decided or cancelled first. [ View it ]`. *Chain unsatisfiable* — §10.4's create-time refusals, unchanged.

### 14.6 KAN-202 — the compensation timeline

Opened from `History →` on the Compensation card, and from My Pay when the tenant enables it. Gate
`compensation:r` + row scope. **A compensation surface, not an audit surface** — holding `audit_log:r` alone never
reveals an amount (SPM D5.6).

> ⛔ **EXTENDED by A1: one timeline, not two.** *"How did this person get here"* is one story, so the step and
> roadmap history interleaves with the pay history rather than living on a separate screen (SPM §14.8). Entries
> are of three kinds and each is labelled: **pay** (amount, `compensation:r`), **step / level** (`job_architecture:r`)
> and **roadmap** (`job_architecture:r` + scope). A viewer with `job_architecture:r` but not `compensation:r`
> sees a complete, coherent timeline **with the pay entries absent** — not blanked, not "hidden" — and the
> heading changes to `Level and step history`. This is §3.7's two-gate rule applied to a list rather than a page.
>
> An interleaved example, and the reason the interleaving matters:
>
> ```
> ●  4 March 2026 · moved to step 1.4
>    agreed at the mid-term goal review on 28 Feb · by Marcus Lee
>    "Taking on the payments migration."
> ●  4 March 2026 · pay change to €72,930 proposed        ⏳ rejected 12 March
> ●  12 March 2026 · next-step roadmap v3 written by Marcus Lee
>    confirmed by Ravi Sharma on 14 March
> ```
>
> Read together, those three lines are the whole of the owner's concern on one screen: the responsibility moved,
> the money was asked for, and it was refused. Split across two screens, nobody would ever put them side by side.

```
┌─ Compensation history — Ravi Sharma ─────────────────── [ 👁 Hide amounts ] ─┐
│  ●  1 September 2026 · €78,000 · EUR · 1.0 FTE                               │
│     Engineering · level 2 · step 2.1 · Senior Software Engineer              │
│     Promotion approved 12 Aug 2026 · recorded by Priya Nair (HR Admin, at    │
│     the time) · "Promotion to L2"                        ref a1b2c3d4        │
│                                                                              │
│  ●  1 March 2026 · €72,000 · EUR · 1.0 FTE            +4.3%                  │
│     Engineering · level 1 · step 1.5                                         │
│     recorded by Priya Nair (HR Admin, at the time) · "Annual review"         │
│                                                          ref 7e9f10a1        │
│                                                                              │
│  ●  1 June 2024 · €69,000 · EUR · 1.0 FTE   ⊘ Voided                         │
│     Voided by Sam Okafor on 5 Mar 2026 — "entered against the wrong person"  │
│                                                                              │
│  ●  1 February 2021 · first salary recorded during the 2026 backfill         │
│     €58,000 · EUR · 1.0 FTE · imported by Priya Nair from salaries-2026.csv  │
│                                                                              │
│  Amounts aren't written to the audit log. The audit log records that pay      │
│  changed, who changed it and why; this timeline records what it changed to.   │
│  The reference on each entry links the two.                                   │
└──────────────────────────────────────────────────────────────────────────────┘
```

- Semantics exactly as EP38 §5.5: `<ol>` newest-first, `<li>` per entry, `<time datetime="…">`, **not** a table —
  it is a narrative and must stack on mobile.
- **Actor's role as at the time** (`(HR Admin, at the time)`), because roles change and a trail that silently uses
  today's roles is misleading.
- **A voided record is struck through and kept**, never removed. `⊘ Voided` is glyph + word.
- The `ref` is the shortened correlation id, `<code>`, with a copy button (`aria-label="Copy reference a1b2c3d4"`)
  so a compliance officer can join the timeline to the audit log by hand until the audit read surface exists
  (SPM DEP-8).
- **The closing paragraph is required.** Without it, D5.6's deliberate split looks like a gap in the audit trail;
  with it, it reads as the design decision it is.
- Empty: `No salary changes recorded.` Loading: three skeleton entries. Error:
  `We couldn't load the compensation history.` + `[ Try again ]`, with the rest of the profile unaffected.
  Partial: an actor whose record is gone renders `by a removed user` plus the retained role snapshot, never blank.
- `Void this record` appears on an entry only for `compensation:d`, and is a confirmation with a mandatory reason:
  > **Void the record effective 1 June 2024?**
  > Voiding keeps the record and marks it as wrong. It doesn't delete anything, and it doesn't change what Ravi is
  > paid today. `Why is this being voided? *`
  > `[ Cancel ] [ Void this record ]`

---

## 15. The notification bell — D4's blind-spot list, filled in for every EP42 event

> This is my Demo Readiness Gate item (D4) and it is where DEF-001, DEF-002 and DEF-003 lived. **No row below is
> left blank.** An EP42 event that is not in this table does not exist.

### 15.1 The bell's shape after EP42

`templates/base.html:290-320` gains **one** section, in the position SPM D2 specifies:

```
Pending Approvals        role-gated (existing, unchanged)
Position Changes         has_feature_access('org_change')   (existing; item rendering changes — §10.5)
Pay Equity               has_feature_access('pay_equity')   ← NEW, hidden when empty
My Notifications         everyone (existing; two new event types and a new action)
```

- The Pay Equity section is **feature-gated, never role-gated** (`CLAUDE.md`; the existing "Pending Approvals"
  section is role-gated and is *not* the pattern to copy).
- It is **hidden entirely** when the viewer has no open findings. Never an empty `No findings ✓` — that reads as
  "we're fine" while coverage may be 40% (SPM D2, D7.4).
- **Section headers carry their counts** so the badge total can be decomposed at a glance:
  `Pending Approvals (2)` · `Position Changes (1)` · `Pay Equity (8 open findings)`. This ships regardless of how
  UX-CFL-42-2 is resolved.
- Capped at five items with a `+ 7 more open findings · Review all →` footer (§14.3 rule 3).

### 15.2 `NOTIF_ICON` additions

Added to the map at `base.html:608-624`. **The icon states the outcome; an item with no outcome yet must not wear
one; unknown events fall back to the neutral 🔔 and never to ❌** (DEF-002).

```js
// Standing conditions — no outcome yet, so no outcome icon
PAY_EQUITY_FLAG_RAISED:        '⚖️',
PAY_EQUITY_FLAG_REOPENED:      '⚖️',
// A management prompt — informational, no outcome
JOB_LEVEL_TOP_STEP:            '🪜',
// In flight — awaiting a decision
PROMOTION_REQUESTED:           '⏳',
COMPENSATION_REVIEW_REQUESTED: '⏳',
COMPENSATION_DECISION_DEFERRED:'⏳',
// Decided — an outcome really happened
PAY_EQUITY_FLAG_CLOSED:        '✅',
PROMOTION_APPLIED:             '✅',
PROMOTION_REJECTED:            '❌',
COMPENSATION_CHANGE_APPLIED:   '✅',
COMPENSATION_CHANGE_REJECTED:  '❌',
```

**(A1) Six more, and one rename.** `PROMOTION_*` becomes `LEVEL_CHANGE_*` throughout (CFL-42-25); the icon is
chosen by outcome, not by direction, so a demotion and a promotion share `✅` when applied — the *message* says
which, and an icon that editorialised about direction would be exactly the DEF-002 mistake in a new place.

```js
// A1 — job architecture and the roadmap
ROADMAP_SHARED:                '📋',   // your manager has written your next step — a task for you
ROADMAP_ACKNOWLEDGED:          '✅',   // to the manager: they confirmed you discussed it
ROADMAP_DISCUSS_REQUESTED:     '💬',   // to the manager: "we haven't discussed this yet"
STEP_CHANGED:                  '🪜',   // to the subject: you are on a new step
// A1 — the two step-pay finding types (both are conditions, neither is a refusal)
PAY_BELOW_STEP_RAISED:         '⚖️',
PAY_BELOW_STEP_CLOSED:         '✅',
// A1 — renamed
LEVEL_CHANGE_REQUESTED:        '⏳',
LEVEL_CHANGE_APPLIED:          '✅',
LEVEL_CHANGE_REJECTED:         '❌',
```

**Not one of the seventeen is ❌ unless something was actually refused.** A pay-equity finding is not a refusal of
anything and must never wear a cross — that is DEF-002 exactly, and pay is the worst possible place to repeat it.
**There is no icon at all for `PAY_ABOVE_STEP`, because it raises no notification** (§14.2, UX-A1-C2).

### 15.3 Every EP42 event, against the blind-spot list

| Event | Section | Icon | In badge? | Actionable in the bell? | Quick action | Recipients | Retires when | Retires for whom | Contains an amount? |
|---|---|---|---|---|---|---|---|---|---|
| **`PAY_EQUITY_FLAG_RAISED`** | Pay Equity | ⚖️ | **Yes** — while unowned (§14.3 r4) | Yes | **`Review →`** to the register filtered to this finding. **No dispose-from-the-bell** | `pay_equity:r` holders + any named escalation recipients | The finding leaves `OPEN` (any disposition, or `RESOLVED_BY_DATA`) | **Every** eligible recipient, not just the actor | **No.** Names the subject, the group and that a threshold was exceeded. No figure, no percentage |
| **`PAY_EQUITY_FLAG_REOPENED`** | Pay Equity | ⚖️ | Yes | Yes | `Review →` | same | same | same | No |
| **`PAY_EQUITY_FLAG_CLOSED`** (incl. `RESOLVED_BY_DATA`) | My Notifications | ✅ | **No** — informational | Link only | `View →` to the finding's record | same | Normal notification lifetime | n/a | No |
| **`JOB_LEVEL_TOP_STEP`** | My Notifications | 🪜 | **Yes** | Yes — **two** actions | `Review →` (profile Job Level card) · **`Not now`** (recorded, suppresses 6 months) | Subject's solid-line manager + `compensation:w` holders | Level or step changes (any direction) · subject leaves · `Not now` | Every recipient. On a manager change it retires for the old manager and fires for the new one | No |
| **`PROMOTION_REQUESTED`** | Position Changes | ⏳ | Yes | Yes | **`Review →` only — the one-click Approve is suppressed** (§10.5) | Approvers resolvable at the current level, **who hold `compensation:r`** (D4b) and have not already decided a level (KAN-198) | Decision at that level · rejection · cancellation | Every eligible approver at that level | No. `ocSummary()` renders `pay change`, never a figure |
| **`COMPENSATION_REVIEW_REQUESTED`** | Position Changes | ⏳ | Yes | Yes | `Review →` only | same | same | same | No |
| **`ORG_CHANGE_REQUESTED` carrying pay** | Position Changes | ⏳ | Yes | Yes | `Review →` only (Approve suppressed because it carries money) | same | same | same | No |
| `ORG_CHANGE_REQUESTED` placement-only | Position Changes | ⏳ | Yes | Yes | **Unchanged** — `✓ Approve` + `✗ Reject` deep link | unchanged | unchanged | unchanged | n/a |
| **`PROMOTION_APPLIED`** | My Notifications | ✅ | No | Link | `View →` profile | The requester · the subject's solid-line manager. **Not the subject** | Normal | n/a | No |
| **`COMPENSATION_CHANGE_APPLIED`** | My Notifications | ✅ | No | Link | `View →` profile | The requester only | Normal | n/a | No |
| **`COMPENSATION_CHANGE_REJECTED`** | My Notifications | ❌ | No | Link | `View →` the request | The requester | Normal | n/a | No |
| **`COMPENSATION_DECISION_DEFERRED`** | My Notifications | ⏳ | **Yes** | Yes | `Record salary →` (opens §9.3 for that person) | `compensation:w` holders | A compensation record is created for that subject with an effective date on or after the request's | Every `compensation:w` holder | No |
| A salary recorded directly (no request) | — | — | — | — | — | **Nobody.** §9.2 explains why the subject is not told by a bell | — | — | — |
| `PAY_BAND_CHANGED` · `PAY_EQUITY_THRESHOLD_CHANGED` · ladder changes | — | — | — | — | — | **Nobody.** Audit only. A configuration change does not need a bell, and notifying on one would train people to ignore the bell | — | — | — |

**(A1) The six new events, same discipline, no row blank.**

| Event | Section | Icon | In badge? | Actionable? | Quick action | Recipients | Retires when | Retires for whom | Amount? |
|---|---|---|---|---|---|---|---|---|---|
| **`ROADMAP_SHARED`** | My Notifications | 📋 | **Yes** | Yes | `Read it →` (their own profile card, §22.3). **No "acknowledge from the bell"** — confirming you discussed something you have not opened is a lie the product would be helping to tell | **The subject only.** Their manager wrote it; nobody else is notified | The subject **acknowledges** or asks to discuss — a recorded act, never on read | The subject (the only recipient) | No |
| **`ROADMAP_ACKNOWLEDGED`** | My Notifications | ✅ | No | Link | `View →` | The author | Normal lifetime | n/a | No |
| **`ROADMAP_DISCUSS_REQUESTED`** | My Notifications | 💬 | **Yes** | Yes | `Open the roadmap →` | The author | The author publishes a new version, or marks it discussed | The author | No |
| **`STEP_CHANGED`** | My Notifications | 🪜 | No | Link | `See what step 1.4 means →` (`/ladder/...`) | **The subject.** *(Unlike a pay change, which the subject is never told about by bell — §9.2. A step change is job content the employee is entitled to know, and it was just agreed with them in a room; telling them is confirming a conversation, not pre-empting one)* | Normal lifetime | n/a | **No.** The message names the step, never the pay point |
| **`PAY_BELOW_STEP_RAISED`** | Pay Equity | ⚖️ | **Yes**, while unowned | Yes | `Review →` to the register filtered to it | `pay_equity:r` holders + escalation list | The finding leaves `OPEN` | Every eligible recipient | **No.** `Ravi Sharma's pay doesn't match the step he's on.` — no figure, no percentage |
| **`PAY_BELOW_STEP_CLOSED`** | My Notifications | ✅ | No | Link | `View →` | same | Normal lifetime | n/a | No |
| `PAY_ABOVE_STEP` *(any)* | — | — | — | — | — | **Nobody** — register only (§14.2, UX-A1-C2) | — | — | — |
| Ladder or pay-point configuration changes | — | — | — | — | — | **Nobody.** Audit only — unchanged from Wave 2, and it now also covers step expectations. **Exception:** a step-count reduction that puts someone at the top step fires the ordinary `JOB_LEVEL_TOP_STEP` signal to their manager (§8.4) | — | — | — |

**Deep links, per the gate's last blind-spot item.** Every `Review →` lands on a surface that is still meaningful,
and a stale link never opens a dead dialog — reusing `inbox.html:188-196`'s guard. Specifically:
- A finding already dispositioned → the register opens with a `role="status"` line
  `That finding has already been dealt with — Priya Nair recorded it as justified on 9 August.` and the row visible
  in its new state. Not an error, not an empty page.
- A request already decided → existing EP38/EP27 behaviour.
- A subject who has left → the profile opens with EP38's former-employee banner.

### 15.4 The four actors — what each one sees (SPM §8.3.6)

| Surface | **A recipient with an open finding** | **A recipient after somebody else dispositioned it** | **A user without `pay_equity`** | **The subject of the finding** |
|---|---|---|---|---|
| Bell badge | Includes it (while unowned) | **Decremented** — for them too, not just the actor | Unchanged | Unchanged |
| Bell — Pay Equity section | Visible, the finding listed with `Review →` | **Section gone** if it was their only finding; otherwise the finding is absent from it | **Section not rendered at all** — feature-gated | Not rendered |
| `/compensation/equity` | The finding in `Open`, `[ Take ]` available | The finding under `Justified`, with who decided, when and why | Nav item absent; direct URL → flash + dashboard | Nav item absent (unless they happen to hold `pay_equity`, in which case they see the register **including the finding about themselves** — see below) |
| Their own profile | n/a | n/a | n/a | **Nothing.** No marker, no badge, no card, nothing in My Pay |
| Email | Not in scope this cycle | — | — | — |

**The one uncomfortable case, named rather than left to be discovered:** an HR administrator who holds
`pay_equity:r` and is *themselves* the subject of a finding will see it in the register. There is no self-exclusion
rule in D1 and inventing one would let a compensation administrator hide their own outlier, which is worse. The
register therefore shows it, and the disposition dialog adds one line when the actor is the subject:

> ⚠ `This finding is about you. You can read it, but someone else has to record the decision.`

with the disposition controls **absent**. This is the pay-equity equivalent of "an employee can never initiate their
own move" (KAN-139) and of KAN-198's four-eyes rule, and it belongs in the same family. *(New rule — §20
UX-CFL-42-5.)*

### 15.5 Bell accessibility

- The bell dropdown becomes a real disclosure: the button gets `aria-expanded` and `aria-controls`; the dropdown
  gets `role="region"` and `aria-label="Notifications"`; Esc closes it and returns focus to the bell button.
  *(This is an existing gap — `base.html:282-320` has neither — and EP42 adds a section to it, so it is fixed here.)*
- Each section is a `<section>` with an `<h3 class="sr-only">` matching its visible header, so a screen-reader user
  can jump between "Pending Approvals", "Position Changes", "Pay Equity" and "My Notifications".
- Each item is an `<li>`; its accessible name leads with the icon's **meaning**, not the emoji:
  `Pay equity finding. Ravi Sharma, Engineering level 2, Germany. Raised 12 days ago.` The emoji itself is
  `aria-hidden="true"`.
- `Review →`, `Take` and `Not now` are ≥24×24 (≥44px below 768px) and appear in DOM order after the item's text.
- Acting on an item announces the result **and its consequence** to `#live-status`:
  `Finding taken. It stays open and is now assigned to you.` / `Marked not now. You'll see this again if Ravi's
  level or step changes.`
- The badge is `aria-live="polite"` with an accessible name of the form `8 items need you`, not the bare number.

---

## 16. Cross-cutting requirements

| Area | Requirement |
|---|---|
| **Dark mode** | Every EP42 surface uses tokens (§2.1). The ladder editor, mapping table, coverage meters, compensation cards, My Pay, the pay block, the register, the drill-down, the disposition dialog and the timeline must all be checked in dark mode; `tests/ui/test_browser.py` already asserts dark mode and must gain these screens |
| **Mobile ≤767px** | Dialogs become full-height sheets with sticky 44px footers. The ladder's two panes stack (families collapse into a `<details>` picker). The mapping table and the register become stacked cards. Profile cards go full-width. My Pay must be fully usable at 320px — it is the one EP42 surface an employee is most likely to open on a phone |
| **Reflow / zoom** | No horizontal page scrolling at 320px or 400% zoom on any EP42 surface (1.4.10). Wide tables scroll inside `.table-wrap`, never the page. The bands grid scrolls horizontally inside its own wrapper with the level column sticky |
| **XSS posture** | D-004 defers the `innerHTML` sweep (KAN-150/173) but **EP42 must not add a new sink.** Every new DOM builder — the ladder rows, the mapping table, the register, the drill-down, the timeline, the pay block, the bell's Pay Equity section — renders user-authored strings (level titles, working titles, reasons, justifications, notes, file names) through `escH()` or `textContent`. Justification text in particular is authored by one user and read by others |
| **Company scoping** | Every list, select, meter, export and comparison filters `company_id = %s::uuid`. Company roles are never `OR company_id IS NULL`. Cross-tenant comparison does not exist for any role, including SYSTEM_ADMIN with "All Companies" selected — and the register renders `Choose a company first. Pay equity compares people inside one company.` in that state |
| **Pay in errors and logs** | User-facing errors may name the employee (the actor is looking at them) and may state an amount **only inside a `compensation:r` surface**. Logs carry employee id and employee number only (EP38 CC-17) and **never an amount** (D-R5) |
| **Print** | §2.6(c) stamp on every compensation surface |
| **Feature registration** | Three codes in all four places, per `CLAUDE.md`. UX consequence: a code registered in the migration but not `seed_rbac.sql` produces a **nav item that exists on a developer's machine and not in CI** — the DEF-004 shape. Not my file, but it is my surface, so it is on my review list |
| **(A1) The ladder is published content** | Everything on `/ladder` and in a roadmap is written by one employee and read by others: level titles, step summaries, expectations, roadmap items, notes. **Every one goes through `escH()` or `textContent`** — this is the largest new set of user-authored strings in the epic and the widest audience any of them has had. A stored XSS in a step expectation is read by the whole company |
| **(A1) The employee-facing surfaces are the mobile ones** | `/ladder`, the `Your level and next step` card and `My Pay` are what an employee opens on a phone from a bell notification. They get the mobile pass first, not last |
| **(A1) `job_architecture` in the four-place registration** | Registered in KAN-190. The UX consequence of a miss is a **nav item and an employee-facing card that exist on a developer's machine and not in CI** — the DEF-004 shape, now with the transparency requirement inside it |
| **Regression coverage** (UAT owns the files) | **(A1)** an employee reaching `/ladder` with no compensation permission and seeing no figure · an employee seeing their own roadmap and not a colleague's, asserted at the payload · the six-values-for-count-five arithmetic in every surface that renders steps · the tolerance refusal being unsaveable · a step change writing **no** compensation record · a `PAY_BELOW_STEP` finding surviving the raising of its own adjustment and re-activating on rejection · the ladder's money column being absent for a `job_architecture:w`-only holder · **and** the original list: nav visibility by feature code and by tenant switch · the locked screen · `No salary recorded` vs `Not applicable` vs absent, for three viewer types · the amount **absent from the JSON payload** for an out-of-scope viewer · the pay block absent for a viewer without `compensation:r` · the no-change path costing one click and no scroll · create-time refusal for both unsatisfiable-chain cases · the bell's Pay Equity section appearing with `Review →`, wearing ⚖️ and **not** ❌, and **leaving for a second recipient** after somebody else dispositions · a finding **not** retiring on read · a re-opened finding showing its previous justification · the ladder blockers (occupied level, occupied step) · the import's zero/blank rejection at preview |
| **Analytics** | Coverage over time per tenant (the adoption instrument) · days from tenant enablement to first equity run · drop-off in the ladder configurator by stage (abandonment at the first-run panel means the vocabulary is wrong) · titles mapped per session (if it is under ~15, the mapping screen is too slow) · share of position changes by pay answer — no change / new salary / defer (a defer rate above ~20% means the decision is being pushed off-system again) · median days a finding stays open · share dispositioned `JUSTIFIED` on first review (the SPM's >40% tripwire) · **`Hide amounts` usage** — if a large share of users turn it on and leave it on, the default is wrong and should flip |

---

## 17. What an engineer must build

1. **The three shell fixes EP42 depends on** (§2.4): global `:focus-visible`, the two shared live regions in
   `base.html`, and a `prefers-reduced-motion` block. Plus the bell's `aria-expanded`/`role="region"`/Esc (§15.5).
2. **Three money primitives** (§2.6): `Money`, `NoValue`, `Hide amounts` — one implementation each, used by every
   surface.
3. **`/compensation` hub** with six tabs, each independently gated (§4).
4. **Ladder configurator** — master/detail, staged edits, keyboard reorder, four blocked cases, Review dialog (§6).
5. **Level assignment** — by-title table sorted by headcount, bulk bar, by-person view, CSV round-trip, Review
   dialog (§7).
6. **Job Level card** on the profile + `Advance step…` dialog with its immediate-vs-approval switch (§8).
7. **Compensation card**, **My Pay**, **`Record a change…`** with three guards, **Overview** with two meters and
   the deferred list (§9).
8. **Salary import** on the existing import surface, with the compensation preview columns and the twelve row-level
   error strings (§9.4).
9. **Pay block + Job level block inside `templates/org_change/_move_modal.html`** — extended, not duplicated — plus
   the live request-type line, the re-fetching chain sentence and the two create-time refusal panels (§10, §11).
10. **Four-eyes surfaces**: the configuration advisory, the decide-time statement panel, the stalled-request line
    (§12).
11. **Bands grid + pay-market management** with the multi-currency refusal (§13).
12. **Pay-equity register**, group drill-down, disposition dialog, run-check flow, and every empty/partial state —
    especially the below-gate coverage panel that must never say "no findings" (§14).
13. **Compensation timeline** with void, correlation reference and the audit-split paragraph (§14.6).
14. **Bell**: a fourth section, `NOTIF_ICON` entries, suppression of the one-click Approve on money-bearing
    requests, `Take` and `Not now` actions, and retirement wiring for four `related_type`s (§15).

**A1 additions:**

15. **`/ladder`** — one route, three audiences: a reading view for every employee (§6.10), inline editing for
    `job_architecture:w`, and a money column for `compensation:w` (§23.1). Plus the deep-linkable child route
    `/ladder/<family>/<level>/<step>`.
16. **The step-expectations editor** (§6.9) — step list, summary, repeatable expectations, `Copy from…`, the
    conflict resolver, and draft preservation.
17. **The next-step roadmap** (§22) — the manager's authoring dialog, the employee's profile card, the
    acknowledgement and `Ask to discuss it` interactions, versioning, and the `My Team` prompt strip.
18. **The fitted-step review** (§7.9) — the fitting explanation, the `Needs a look` default filter, per-row
    confirm/override with a reason, `Confirm all exact fits`, and the completion gate.
19. **Step pay points** (§23) — the money column, the computed compound table, the **blocking** tolerance refusal
    with its explanatory copy and one-click fix, and the non-blocking level-overlap warning.
20. **`Advance step…` rebuilt** (§8.2) — the review-context fieldset, the four-option pay question with
    `Match the step`, and the permanent "the pay goes to approval, the step applies now" sentence.
21. **The register rebuilt** (§14) — three finding-type tabs, the new columns, the not-evaluable panel, and
    **`Propose adjustment`** opening the shared modal pre-filled (§14.5a).
22. **The audited salary export** (§24) — one door, row-scoped, reason required, watermarked, audited.

---

## 18. UX acceptance criteria (testable)

**Discretion (KAN-194)**
1. For a viewer without scope, no amount appears in the rendered HTML **or** in the JSON payload, on every surface
   in SPM §4.5.7 — profile, directory, org tree, search, bell, exports, the modal, the register, the timeline.
2. No surface renders a blurred, masked, greyed or placeholder value as a permission state.
3. `Hide amounts` masks only values the viewer is already permitted to see, persists across navigation, and is
   never the mechanism enforcing a permission.
4. Every count, meter and denominator is computed over the viewer's row scope, and no surface states how many rows
   were withheld.
5. No amount appears in a URL, a page title, a flash, a toast, a notification body, a log line or an audit diff.
6. The compensation CSV template download contains no existing pay data.

**Partial data (D7)**
7. An employee with no record renders `No salary recorded` with the "this is not a zero" explanation and, for `w`
   holders, a `Record salary…` action — never `—`, `0`, blank or `N/A`.
8. A contractor or intern renders `Not applicable — <type>`, distinct from "no salary recorded", and is excluded
   from coverage denominators.
9. Every coverage figure states numerator and denominator; every comparison states what was excluded and why.
10. The equity register at below-gate coverage renders the coverage panel and **never the words "no findings"**.
11. "No open findings" is never rendered without what was checked, when, and how many groups were compared.

**Ladder (KAN-190)**
12. A company with no ladder shows the first-run panel — never another company's levels or a global default.
13. Deleting a level with people on it is blocked, states the count, and offers a way to see them; the same for
    reducing steps below an occupied step.
14. Level order is fixed once any level in the family has an assignment, and the handles are absent, not disabled.
15. Every reorder is achievable by keyboard alone and is announced.
16. Saving opens a review that separates ladder changes from people consequences and states that pay does not
    change and nobody is notified; if the impact cannot be computed, saving is blocked.

**Assignment (KAN-191)**
17. Titles are listed with headcounts, sorted by headcount descending, and progress is expressed in people.
18. Bulk assignment stages rather than commits, and the review states how many people will show a different job
    title.
19. A CSV upload reports row-level errors and imports nothing when any row references another company.

**Progression (KAN-192)**
20. The top-step signal never uses the word "eligible", contains no date or deadline, and states that reaching the
    top step changes nothing by itself before it prompts any action.
21. The subject never sees the top-step signal, in the bell or in My Pay.
22. Choosing a pay change inside `Advance step…` visibly converts the action into an approval and says so before
    submission.
23. A downward step or level move requires an explicit acknowledgement naming the consequence.

**The record (KAN-193/195)**
24. The amount field refuses zero and negatives with specific messages; an import row with a zero or blank amount
    is an error at preview and cannot be committed.
25. An amount ≥5× or ≤⅕ of the current record requires an explicit confirmation.
26. Any decrease requires an acknowledgement naming both figures.
27. Out-of-band pay is allowed, flagged and requires a reason — never blocked.
28. An import is atomic, and its failure message says nothing at all was imported.
29. If the audit write fails, the compensation write is rolled back and the user is told nothing was saved.

**My Pay (KAN-194)**
30. My Pay contains none of the banned forward-looking strings, no comparison to any other person, and no raw
    compa-ratio.
31. Position in range uses one of the five permitted phrasings, and out-of-range carries the "ranges are guidance"
    sentence.
32. With no record, My Pay says the payslip is the authority and offers no action.

**Coupling (KAN-196/197/198)**
33. The pay block is mandatory to answer, has nothing pre-selected, and `No change` expands nothing — one click,
    no scroll, and the modal does not scroll at 1280×720 in the default state.
34. The pay block is **absent** for a viewer without `compensation:r`, with no explanatory text, and the request
    they raise is a placement-only transfer.
35. The inferred request type and the resolved approval chain are both visible and announced before submission, and
    both update when the type changes.
36. A money-bearing request whose chain has an unsatisfiable step is refused at create time, names the step and the
    fix, writes nothing, and offers a one-click path to submit without the pay change.
37. A promotion with no pay change requires a recorded reason.
38. A downward level move is labelled `Level change (down)` in every surface — modal, inbox, bell, My Requests,
    timeline — and never "Promotion".
39. An approver who decided one level of a money-bearing request does not see it in their bell or their pending
    list, and a deep link shows a statement panel with no decision controls.
40. The approval-chain admin page shows the overlap at configuration time.
41. The bell offers no one-click Approve on any request carrying a pay or level change, and `ocSummary()` never
    renders an amount or a percentage.

**Pay equity (KAN-200/201/202)**
42. The Pay Equity bell section is feature-gated, hidden when empty, capped at five with a "more" footer, wears ⚖️,
    and never ❌.
43. A finding is actionable in the bell with exactly one action, `Review →`; there is no dismiss anywhere.
44. A finding does not retire on read, and retires on disposition **for every eligible recipient**, asserted across
    at least three.
45. A justified finding does not re-fire inside its window; when it does re-fire it is labelled `Re-opened`, states
    why, and shows the previous justification and its author.
46. `RESOLVED_BY_DATA` sends one informational closure notification and does not silently remove the item.
47. The subject of a finding receives nothing, anywhere; a subject who is also a recipient can read the finding but
    has no disposition controls.
48. The framing paragraph appears at full size on the register, the drill-down and the disposition dialog.
49. Every disposition requires a reason; `Justified` additionally requires a category; the validity window is
    stated before saving; there is no bulk disposition and no one-click dismissal.
50. A viewer with `pay_equity:r` but not `compensation:r` sees findings without numeric columns, replaced by the
    wording variants.

**All of it**
51. Every screen renders correctly in light and dark themes at 320px, 768px and 1440px, and at 400% zoom, with no
    horizontal page scrolling.
52. No `alert()`, `confirm()` or `prompt()` on any EP42 path, including the import surface it reuses.
53. All new text meets 4.5:1 (3:1 for large text and UI boundaries) in both themes, and no meaning is carried by
    colour alone.
54. Every interactive control has a visible `:focus-visible` indicator; every dialog traps focus, closes on Esc
    except while committing, and restores focus.
55. Every async change announces through `#live-status` or `#live-alert`.
56. Every drag interaction has an equivalent keyboard path that is announced.

**A1 additions — the job ladder as transparency (KAN-190, KAN-207)**
57. Every step value is displayed, entry step first: a level with a step count of 5 shows `1.0 · 1.1 · 1.2 · 1.3 ·
    1.4 · 1.5`, six values, in the configurator, on the profile card, on `/ladder` and in every select.
58. The step-count select has **no default**; a level cannot be saved without an answer.
59. Reducing a step count is blocked when the removed steps are occupied, and when they are merely described it
    names the expectations that will be deleted before deleting them.
60. A step-count change that puts an existing employee at the top step is listed in the review dialog **and**
    fires the top-step signal to that employee's manager.
61. `/ladder` is reachable and complete for a holder of `job_architecture:r` alone, including an `EMPLOYEE`, with
    no compensation permission of any kind, and it renders **no** pay figure for anybody.
62. An employee can read the expectations of **every** step of **every** family, not only their own.
63. An undescribed step renders as `Not described yet` to every audience, including employees — never hidden and
    never omitted from the list.
64. Saving the ladder publishes it: the review dialog states that step expectations become visible to every
    employee immediately.
65. No rating, score, percentage, progress bar or ranking appears on any ladder, step, roadmap or team surface,
    for any role (§25). Asserted by an explicit negative test, not by inspection.

**A1 — the roadmap (KAN-207)**
66. An employee can see their own roadmap and **cannot** see a colleague's, asserted at the payload.
67. A manager can author a roadmap for a direct report **without holding any compensation permission**.
68. Publishing a roadmap notifies only the subject; acknowledging notifies only the author.
69. The acknowledgement is a recorded act with a timestamp; it never happens on read, and it is not required for
    anything else to proceed.
70. `Ask to discuss it` is available to the employee, records a state, notifies the author, and is not a refusal.
71. Publishing a new version preserves every earlier version, readable by both parties, with its author and date.
72. No roadmap surface contains a due date per item, a checkbox, a completion count, an outcome field, or any word
    from the §2.3 banned list.
73. Roadmap copy names the decision and the decider on every forward-looking sentence; no sentence states or
    implies that completing the roadmap results in a step change.

**A1 — step change, review context and propose-not-apply (KAN-192)**
74. A step change cannot be submitted without a review context; `Not at a review` is an available answer.
75. A step change **never writes a compensation record**. Where a pay change is chosen, a `COMPENSATION_REVIEW`
    request is created and routed through the chain; asserted at the database, not the API response.
76. The dialog states, in all four pay states, that the pay goes to approval and the step applies immediately.
77. `Match the step` pre-fills the computed pay point and remains editable; nothing is pre-selected.
78. `No change` on a step advance requires a recorded reason.
79. Where the step lands and the pay is pending, the profile states both facts, in an in-flight treatment, with no
    error colour — and the employee's My Pay says nothing about the pending proposal.
80. A pending proposal suppresses the corresponding `PAY_BELOW_STEP` finding; a rejected one re-raises it with the
    rejection named.

**A1 — pay points, increment and tolerance (KAN-206)**
81. Step pay points are shown as a computed table in the configurator, and the displayed values are **compound**,
    not linear — a linear implementation produces visibly different figures at step 3 and beyond.
82. A tolerance greater than or equal to half the step increment **cannot be saved**, and the refusal explains why
    in plain language and offers a compliant value in one click.
83. A level whose base pay point is below the previous level's top-step pay point produces a **warning**, at
    configuration time, that is dismissible and does not block.
84. The money column of the ladder is absent in full — header included — for a holder of `job_architecture:w`
    without `compensation:r`, and the page still reads as complete.
85. No pay point appears anywhere on `/ladder`'s reading view, for any role.

**A1 — the fitted-step backfill (KAN-191)**
86. The backfill places each employee with a salary at the step whose pay point is closest to it; exact ties
    resolve **downward**; employees with no salary are placed at `.0` and flagged for review.
87. Every fitted step carries a stated reason in words; a fitted step with a blank reason is a defect.
88. `Confirm all exact fits` confirms only rows inside tolerance and never a flagged row.
89. Check A′ produces **zero findings** for a company until the step review is marked complete, and the register
    says so rather than showing an empty list.
90. Reopening a completed review requires a reason and is audited.

**A1 — the register (KAN-200 / KAN-201)**
91. Three finding types render with distinct labels, severities and disposition categories; `PAY_BELOW_STEP` is
    the default view and `PAY_ABOVE_STEP` is in its own tab with its own framing.
92. `PAY_ABOVE_STEP` raises no notification and is not counted in the bell badge or the header count.
93. `Propose adjustment` appears only on `PAY_BELOW_STEP`, opens the **shared** move modal in
    `COMPENSATION_REVIEW` mode pre-filled at the step pay point, and the amount remains editable.
94. A finding does **not** close when an adjustment is proposed; it closes when the pay lands, and it re-activates
    if the proposal is rejected or cancelled.
95. `n = 1` is a valid primary finding; no group minimum and no coverage gate applies to the primary check.
96. Check B retains `n ≥ 5`, ≥2 of each gender, and no aggregate of any kind is rendered below n = 5.
97. Every employee the check could not evaluate is counted and the reason named, with a route to the fix.
98. The measured figures (`Paid`, `Step pay point`, `Difference`) are absent from the payload for a viewer holding
    `pay_equity:r` without `compensation:r`, replaced by the wording variants.

---

## 19. Open questions and design gaps

✅ **Wave 3 / A1 — eight of my ten were answered.** Recorded here rather than deleted, so this table reads as
history and the live list below it stays short.

| # | Ruling | What I built |
|---|---|---|
| **UXQ1** — erasure has no compensation screens | **Partly closed.** CFL-42-3 resolved by the BA (§4.7); seven DPO items remain and DPO-2 blocks only the retention class | **Still no screens.** Stays open below, and A1 makes it worse: roadmaps and step history are now personal data about an identified person, written by their manager, and the erasure enumeration does not mention them either |
| **UXQ2** — level order fixed per family or per level | **Ratified per family** — "UX designed the safe reading" | §6.4(d) unchanged |
| **UXQ3** — are reason categories seeded | **Yes** — `Annual review`, `Promotion`, `Market adjustment`, `Role change`, `Correction`, `Other`, company-editable | §9.6 E3 amended; A1 adds `Step correction` (§14.5a) |
| **UXQ4** — a title→level suggestion column | **Out of scope this cycle** — it is an assistive inference about job classification, the territory Charter §1 gates | §7.6 stands as a designed-but-not-built record |
| **UXQ5** — an export of current salaries | **Design it, in KAN-202, as a Should** | **§24, new** |
| **UXQ6** — tell the employee when `compensation_self` is off | **Ratified "absent"** | §9.2 unchanged |
| **UXQ7** — notify the subject when their pay changes | **No, this cycle** — "it is a letter, not a bell" | §9.2 unchanged. **A1 note:** the subject *is* now told about a **step** change (§15.3) — different object, different reasoning, stated so the two do not look inconsistent |
| **UXQ8** — may HR record a contractor's rate | **Yes** — my reasoning adopted; two distinct empty states | §9.6 E2 rewritten |
| **UXQ9** — tenant-configurable `Hide amounts` default | **No per-tenant default**; my off default stands; ship the usage analytics | §2.6(c) and §16 unchanged |
| **UXQ10** — who sees "findings have no recipient" | **Compensation Settings *and* the Feature Access tab *and* the SYSTEM_ADMIN tenant banner** — SYSTEM_ADMIN is the only actor guaranteed to be able to see it | §14.3 rule 8 amended accordingly |

**Still open, plus four that A1 created:**

| # | Question | Why it matters | Owner | Blocking? |
|---|---|---|---|---|
| **UXQ1** | **Erasure has no compensation screens.** CFL-42-3 hands the BA the erasure enumeration for pay data. Whatever it decides, somebody has to design what an HR admin sees when erasing a person who has a pay history that tax law requires retained | This is the most destructive action touching the most sensitive data, and it currently has no UI at all. EP38's H1 is still open for the same reason | UX (me), needs SPM tasking after CFL-42-3 | **Yes, before that story is built** — not before EP42 |
| **UXQ2** | Is level order fixed **per family** (my §6.4d rule) or per level? | Per-level locking lets an empty level be moved past an occupied one, silently renumbering the occupied one | BA + Architect | No — I have designed the safe reading |
| **UXQ3** | Are salary-change **reason categories** seeded for a new company, or does every tenant start empty? | §9.6 E3 blocks recording a salary when the list is empty. A tenant that cannot record pay on day one is a bad first run | BA | No, but it shapes first-run |
| **UXQ4** | Is a **title→level suggestion** column in scope for KAN-191? | It could halve a 75-row sitting; it is also an assistive inference about job classification and needs the §7.6 guardrails if built | SPM | No |
| **UXQ5** | Is there an **export of current salaries**? I have deliberately designed none, and the import template is blank | HR will ask for it within a week of go-live. Designing it deliberately (row-scoped, audited, stamped) is much better than someone adding a CSV button | SPM + DPO | No |
| **UXQ6** | When a tenant switches `compensation_self` off, should the employee be told, or should the card simply be absent? I chose absent | Transparency (role rule 4) argues for telling them; pay-transparency law may eventually require it; but the employee cannot act on it and it invites a conversation HR cannot have | BA + DPO | No |
| **UXQ7** | Should the **subject be notified when their own pay changes**? I have designed **no** notification | Some jurisdictions require written notification of a pay change — but that is a letter, not a bell. If the product must do it, it needs its own surface and its own copy | BA + DPO | No |
| **UXQ8** | Can HR record a **contractor's rate**? §9.6 E2 offers no action | Contractors are excluded from comparison either way, but blocking the record entirely will push contractor rates into a spreadsheet — the problem we started with | BA | No |
| **UXQ9** | Does the tenant get to configure the **`Hide amounts` default**? I have defaulted it off | If the analytics in §16 show most users turn it on, the default is wrong. A per-tenant default is one setting | SPM | No |
| **UX-A1-Q1** | **Does the ladder need a draft/publish cycle?** Today save is publish, and a half-written step expectation becomes visible to the whole company the moment an admin saves. §6.5 tells them so | A draft state doubles the model for a screen edited twice a year, and "the ladder is out of date because nobody pressed publish" is a worse failure than a visible typo. But an HR director drafting a sensitive rewrite may disagree | SPM | No — designed as save-is-publish, stated on screen |
| **UX-A1-Q2** | **Is a roadmap deletable, and who by?** I have designed supersede-only: a new version replaces the old and both stay readable. Nothing deletes | A manager who writes a roadmap for the wrong person, or writes something they regret, has no remedy but a superseding version that still shows the original. That is right for an audit trail and uncomfortable for a human | BA + DPO | No |
| **UX-A1-Q3** | **An employee can read what their step *requires* but not what it is *worth*.** The expectations are published; the pay point is money (D-R9/D-R11). And the pending pay proposal after a step change is invisible to them (§8.6d) | This is the sharpest edge A1 creates. The owner's stated rationale is *"when an employee taking additional responsibility the pay should be adjusted"* — an employee who can see the responsibility and not the adjustment may reasonably feel the transparency is one-sided | **SPM + product owner** | No, but it should be said out loud rather than discovered |
| **UX-A1-Q4** | **Who writes the step expectations in a real tenant?** The screen assumes HR. In most companies the content comes from engineering managers, and `job_architecture:w` is seeded to HR_ADMIN and PORTAL_ADMIN only | If the content has to be drafted by people who cannot type it into the product, it will be written in a document and pasted badly, or not at all. A per-family author grant may be needed | BA + SPM | No, but it is the adoption risk for KAN-190 the way R-2 is for KAN-191 |
| **UXQ10** ✅ | *Answered — see the block above.* Who is shown the **"findings have no recipient"** warning | — | — | Closed |

---

## 20. Conflicts with the SPM's decisions — recorded, complied with, not designed around

*Charter §9.3: surface conflicts, never resolve them silently. Each of these is built as the SPM wrote it unless he
rules otherwise; each states the cost of leaving it.*

✅ **Wave 3 — all eight of mine were ruled. Five adopted, one rejected with better reasoning, two absorbed into
stories.**

| Mine | Ruling | Outcome |
|---|---|---|
| **UX-CFL-42-1** — "PORTAL_ADMIN only" is a role check | **My fix rejected, the Architect's adopted** (CFL-42-20). `company_settings:w`, not `pay_equity:d` | §3.1 amended; §3.7 written. **The rejection is right** — a grant labelled "delete" that confers "configure" misleads where the choice is made |
| **UX-CFL-42-2** — the badge sits permanently non-zero | **Adopted** (CFL-42-24). Badge counts unowned findings; `[ Take ]` decrements it | §14.3 rule 4 becomes the specification, not the recommendation |
| **UX-CFL-42-3** — "Promotion" on a demotion | **Both options rejected for a better third** (CFL-42-25): `LEVEL_CHANGE` + `direction`. My display-label workaround is **deleted** | §11.3 rewritten. He is right that a label cannot fix a lie in the audit record |
| **UX-CFL-42-4** — the second unsatisfiable chain | **Adopted** (CFL-42-26). Refuse at create, both cases | §10.4(b) becomes the specification |
| **UX-CFL-42-5** — dispositioning a finding about yourself | **Adopted as an explicit criterion** (CFL-42-27), plus the follow-on for UXQ10 | §15.4 stands |
| **UX-CFL-42-6** — `pay_equity:r` without `compensation:r` | **Both halves adopted** (CFL-42-19), **and the SPM amended his own D5.7** to add *inference* as a category on the leak list | D-R9 ratified and widened |
| **UX-CFL-42-7** — one-click Approve on money | **Adopted** (CFL-42-28) | §10.5 becomes the specification |
| **UX-CFL-42-8** — the shell a11y fixes never landed | **Adopted as KAN-204**, W0, tagged EP33 | §2.4 amended. *"It is the third epic in a row to need them, which is evidence it will not arrive from the epic that owns it."* |

**Four new conflicts, from A1:**

| # | Conflict | Severity | Evidence | My recommendation |
|---|---|---|---|---|
| **UX-A1-C1** | **The ladder's two purposes now pull against each other, and one of them has no owner.** A1 makes `/ladder` published, employee-facing content — but nothing in EP42 says who is accountable for its **quality**, and `job_architecture:w` is seeded to HR_ADMIN and PORTAL_ADMIN only. A ladder whose six-step descriptions read *"does more of what 1.1 does"* satisfies every acceptance criterion in this epic and delivers none of the transparency the owner asked for | **Medium** | SPM §14.3.2's seeding; the owner's *"outline next level role and responsibility"*; no criterion anywhere tests content quality, and none can | Two cheap things. **(a)** Make "the ladder reads as a real description of the work" an item on the Demo Gate's must-be-walked-by-a-human list, next to UAT's roadmap item. **(b)** Consider a per-family author grant (UX-A1-Q4). Neither is a build blocker; both are the difference between shipping the feature and shipping the outcome |
| **UX-A1-C2** | **I am specifying `PAY_ABOVE_STEP` as silent — no bell entry, no badge — and A1 does not say that.** §14.1 gives it "lower severity and different copy" | **Medium** | SPM §14.1's severity table; R-1; the fact that a company raising one pay point creates dozens of them at once | Ratify silent. Fallback: a bell entry that is **not** badge-counted. A notification whose honest review outcome is "nothing to do" is how the channel gets muted, and the channel is shared with the primary check |
| **UX-A1-C3** | **A step change is applied by one person with no approval, and it now has a computable pay consequence.** KAN-203 fixes subject≠initiator and KAN-198 requires two people on money — but a *manager* may move their own report from 1.0 to 1.5 alone, in one action, which sets the expected pay point 27% higher and manufactures a `PAY_BELOW_STEP` finding that pressures the organisation to pay it | **Medium** | SPM §14.4 (the step has no chain, "the money always does"); §14.2.1's compounding table | The control is real and I am not asking for a chain on step changes — that would kill the flow. **Ask instead for two cheap guards:** a multi-step jump in one action requires the reason (already designed, §8.2) **and** a `LEVEL_CHANGE`-sized jump — more than two steps at once — is refused with `Move Ravi up two steps at a time, or raise a level change.` Plus: the register's `on step X since` line makes the pattern visible to HR, which is the real defence |
| **UX-A1-C4** | **"Mutually decided" is recorded but unenforceable, and the UI must not imply otherwise.** The SPM is right not to build an approval workflow for a conversation — but a roadmap that shows `Confirmed by Ravi` alongside content Ravi never agreed with is a stronger claim than the mechanism supports | **Low–Medium** | SPM §14.3.3; amendment A-2's own standing rule: *a guarantee is only stated if the mechanism delivers it* | Designed in: the button says **`Confirm we discussed this`**, not "I agree"; the displayed state is `Discussed with Ravi on 14 March`, never "agreed" or "accepted"; and `Ask to discuss it` exists so silence is not the only alternative to confirmation (§22.4). Recorded so nobody "improves" the label back to *Accept* |

| # | Conflict | Severity | Evidence | My recommendation |
|---|---|---|---|---|
| **UX-CFL-42-1** | **D1's "thresholds configurable by PORTAL_ADMIN only" cannot be expressed in this product's permission model.** Gating a surface on a role name is exactly what `CLAUDE.md` forbids, and it is the `enabled_for_hr` mistake in a new costume | **High** | `CLAUDE.md` access-control rules 1–3; SPM D1.1 "configurable by PORTAL_ADMIN only"; contrast with D5.4, which correctly expresses "PORTAL_ADMIN only" for voiding as `compensation:d` | Express it the same way: **thresholds, the coverage gate and pay-market definition are gated `pay_equity` `d`, seeded to PORTAL_ADMIN only**; disposition stays `w`. No role check, no sub-flag, same outcome. §3.1 is written this way |
| **UX-CFL-42-2** | **D2 counts every open finding in the shared bell badge.** Dispositions legitimately take days (his own target is a 15-day median), so the badge sits permanently non-zero and the *approvals* sharing that number lose their signal. That is alert fatigue arriving through a door R-1 is not watching | **Medium** | SPM D2.2 "Badge: counts `OPEN` flags visible to this user, added to the existing bell badge total"; §1.5's 15-working-day target | **Count open findings with no owner.** `[ Take ]` is a recorded, audited act (not a read), it decrements the badge, and the finding stays open, stays in the register and stays in the bell. Fallback if he keeps D2: ship the decomposed section headers (§15.1), which ship either way |
| **UX-CFL-42-3** | **`request_type = PROMOTION` will be displayed for downward and sideways level moves**, which D3.4 explicitly permits. "Promotion" on a demotion is wrong in the inbox, the bell, the timeline and the audit trail, and it breaks the Demo Gate's status-vocabulary rule | **Medium** | SPM D4e's three-value enum; D3.4 "downward moves are all supported through the same request type" | Either add `LEVEL_CHANGE` to the enum, or accept §11.3's derived display label. I have built the display label so nothing is blocked, but the audit trail will still say `PROMOTION_APPLIED` for a demotion, which the label cannot fix |
| **UX-CFL-42-4** | **Four-eyes creates a second unsatisfiable-chain case that D4b does not cover.** D4b refuses at create when a step has no `compensation:r` approver. KAN-198 adds: a chain where one person is the only possible approver at two levels. Left uncovered, that request is created and can never be decided | **High** | SPM D4b (create-time refusal) vs D4h (decide-time hard rule); nothing bridges them | **Refuse at create for both cases**, with the copy in §10.4(b). A stalled money request is worse than a refused one, and the fix is a configuration change the message names |
| **UX-CFL-42-5** | **Nothing stops a `pay_equity` holder dispositioning a finding about themselves.** D1 has no self-exclusion and D4h's four-eyes rule binds approvals, not dispositions | **Medium** | SPM D1, D2.3, D4h | §15.4: the subject may **read** a finding about themselves (hiding it would be worse) but the disposition controls are absent, with the stated line. This is the same family as KAN-139 and KAN-198 and should be an explicit criterion |
| **UX-CFL-42-6** | **`pay_equity:r` without `compensation:r` exposes derived money.** A measured gap plus one known salary is another salary. The seeded defaults grant both together, so this does not bite by default — but a tenant can widen `pay_equity` alone, and the Feature Access tab gives no hint of the consequence | **Medium** | SPM D5.1's separate codes; D2.2's own reasoning that a percentage "could be inverted" to an amount | D-R9 (§3.3) plus §14.2's wording variants, plus a config-time advisory in the Feature Access matrix: `Pay Equity without Compensation: this role sees findings without any figures.` Consequences shown where the choice is made — the same principle as D4h's chain overlap |
| **UX-CFL-42-7** | **The one-click `✓ Approve` in the bell would let a pay change be approved from a line that cannot show the amount.** D5 forbids the amount in the bell; D2 leaves the org-change quick action untouched | **High** | `base.html:497` (quick approve) vs SPM §4.5.7 (no amounts in the bell) and `base.html:639-641` (reject is a deep link "because a decision without a recorded reason is not auditable") | Suppress it for any request carrying pay or a level change (§10.5). This is the product's own precedent applied to a stronger case |
| **UX-CFL-42-8** | **EP38's shared shell a11y fixes did not land, and EP42 cannot ship WCAG 2.2 AA without them.** No global `:focus-visible`, no shared live regions, no `prefers-reduced-motion` | **High** | `style.css:547,561` (two selectors only); no `live-status` outside `_move_modal.html:105-106`; no reduced-motion block | Three shared additions, ahead of the first EP42 screen. Ten new surfaces each inventing a private live region is how the S5 retro-fit doubles — which is exactly what D-004 is trying to avoid paying for twice |

**One place I want to be explicit that I am *not* in conflict.** D5's "manager sees direct reports only" and
"department heads see nothing" will feel wrong to at least one customer, and OQ-2 already carries that to the owner.
Design-wise it is the right default and it costs nothing to widen: every surface is written so a tenant that widens
the matrix simply gets more rows, with no extra check anywhere.

---

## 21. Summary verdict

**RAG: Green for design readiness, Amber for the epic.**

Green because the eleven user-facing stories are specified to build level: every screen has its purpose, entry
points, layout, states, copy, validation strings, permission rule and accessibility annotation, and the two
genuinely hard design problems in this epic have answers rather than placeholders — **discretion** (ten rules, and
"absent, not hidden" applied to every surface including the ones that leak by accident) and **the standing
condition** (§14.3: no dismissal, retirement only on a recorded decision or a data change, retirement for every
recipient, and a re-fire that announces itself as a continuation rather than a new problem).

Amber for the epic, for three reasons the SPM should carry rather than inherit:

1. **UX-CFL-42-8** — EP42 cannot meet its own accessibility standard until three shared shell fixes land. They are
   small and they are shared; they are also the third epic in a row to need them.
2. **UX-CFL-42-4 and UX-CFL-42-7** — two gaps where a money-bearing request can reach a state the SPM's rules do not
   cover: a chain that can never be satisfied, and a pay approval given from a bell line that cannot show the
   amount. Both are cheap to close now and expensive to discover in a demo.
3. **UXQ1** — erasure of a person who has pay history has requirements coming (CFL-42-3) and no screens at all,
   which is the same shape as EP38's still-open H1.

**The one thing I would say out loud at the start of any compensation demo**, beyond the SPM's A-2 disclosure: this
product's visibility model is the whole feature. Demoing it as an HR admin who can see everything demonstrates
nothing. The demo has to include the manager who sees four salaries, the employee who sees one, and the person who
sees none — and the third of those is the only one that proves the design works.

> **Wave 4 addendum to the verdict.** A1 does not change the RAG. It improves the epic and it improves my part of
> it: an absolute reference is far easier to explain on a screen than a group median, a finding that carries its
> own remedy is the best interaction in the epic, and the ladder finally has a reader. Three things move:
> **(1)** the Amber reason "UX-CFL-42-8, the shell fixes" is now **scheduled as KAN-204** and stops being a risk;
> **(2)** a new Amber arrives — **UX-A1-C1**, the ladder's content quality has no owner and no criterion can test
> it; **(3)** **§25 is now the most load-bearing section in this document**, because A1 has put an
> employee-facing, manager-authored development object into a product with no performance module, and every
> reasonable-sounding next request points the same way.
>
> **And the sentence I would add to the demo script:** show the ladder to the **trainee**, not to HR. The
> configurator demos well and proves nothing; the thing the owner asked for is what a person at step 1.2 sees on
> their own profile on a Tuesday.

---

## 22. *(A1, NEW)* KAN-207 — The next-step roadmap

> *"it will be job of manager to outline next level role and respossibility which will act as roadmap and
> trsnaparency for the trainee what he needs to do next which could mutually decided"*
>
> **The object the owner actually asked for.** Two audiences with different needs — the manager authoring for one
> person, and the employee reading it — and **the employee's view is the primary one**, because transparency is
> the stated purpose. If the employee cannot see it, we have not built it.
>
> It is also **the most easily misread object in the epic**, ahead of My Pay and the top-step signal. It is a
> forward-looking statement, written by somebody with power over the reader, about what that reader should do.
> Two words wrong and it is a performance improvement plan.

### 22.1 What it is, and what it is not

| It is | It is not |
|---|---|
| A **statement of expectations** — what the next step involves, applied to this person | An assessment of how they are doing now |
| **Forward-looking** | A record of past performance |
| **One employee, one target step** | A set of objectives, goals or KRs |
| **Versioned** — re-written at each review, every version readable | Edited in place, or closed as met/unmet |
| **Acknowledged**, with a timestamp | Approved, agreed, signed or accepted |
| Written by the manager, **derived from the generic step expectations** (§6.9) | Invented from scratch each time, or a copy of the generic text with a name on it |
| Deletable by nobody; superseded by a new version | A draft the manager can quietly rewrite |

**The relationship to §6.9 in one line, because it is the thing most likely to be built as one object:** the step
expectation says *what step 1.3 means here*; the roadmap says *what you, specifically, need to do to get there*.
Same content lineage, different author, different audience, different lifetime.

### 22.2 The manager's view — authoring

**Entry points, in order of how they will actually be used:**
1. **`My Team`** (`templates/employees/my_team.html`) — a `Next step` column and, above the table, one line:
   `3 of your 6 people don't have a next-step roadmap.` `[ Show them ]`. This is where a manager preparing for a
   review week starts, and it is why the prompt belongs on an existing page rather than a new one.
2. **The report's profile** → Job Level card → `Write the roadmap…` / `Update the roadmap…`.
3. **The top-step signal's `Review →`** lands on the profile card, which carries both this and
   `Request a level change…`.

**Gate:** `job_architecture:w` **or** being the subject's solid-line manager. **No compensation permission is
involved.** Never on your own profile — a self-authored roadmap is not a mutual decision (and it is the same
family as KAN-203's subject ≠ initiator).

```
┌ Next-step roadmap — Ravi Sharma ───────────────────────────────── × ┐
│ EMP-0142 · Engineering · Trainee Software Engineer · step 1.2       │
│ Version 3 · replaces the one you wrote on 12 March 2026             │
├─────────────────────────────────────────────────────────────────────┤
│  Working towards *  [ Step 1.3 ▾ ]                                  │
│                                                                     │
│  What 1.3 means here                                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Leads a small piece of work end to end.                       │  │
│  │ • Breaks a feature into tasks and sequences them              │  │
│  │ • Handles the review conversation with a stakeholder          │  │
│  │ • Picks up production issues in their own area                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  This is the same for everyone at Acme. [ Start from these ]        │
│                                                                     │
│  What this means for Ravi *                                         │
│  ⠿ [ Take the payments migration through to release, including  ] ✕ │
│  ⠿ [ Run the design review for it yourself                      ] ✕ │
│  ⠿ [ Be the first responder for payments alerts for a rotation  ] ✕ │
│  + Add something                                                    │
│                                                                     │
│  Anything else you agreed (optional)                                │
│  [ We'll look at this again at the mid-term review.               ] │
│                                                                     │
│  When did you discuss this? *                                       │
│  ( ) Probation review ( ) Mid-term goal review ( ) Performance      │
│  ( ) Not at a review        Date * [ 12/08/2026 ]                   │
│                                                                     │
│  ⓘ Ravi will be able to read this as soon as you share it, and      │
│    he'll be asked to confirm you discussed it. Nobody else sees it   │
│    except HR.                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                  [ Cancel ]   [ Share this with Ravi ]              │
└─────────────────────────────────────────────────────────────────────┘
```

| Element | Control | Rules |
|---|---|---|
| **Working towards** | select of the steps above the current one in this level, **plus the next level's `.0`** when they are at the top step | Required. Labelled `Working towards`, never "target" or "goal" |
| **What 1.3 means here** | read-only, pulled from §6.9 | Shown so the manager writes *from* the company's definition rather than around it. `[ Start from these ]` copies them into the editable list as a starting point, then they are the manager's words |
| **What this means for Ravi** | repeatable rows, ≤240 each, 1–10, reorderable, **required (at least one)** | Plain sentences. **No checkboxes, no dates, no owners, no status** (§25) |
| Anything else | textarea, optional | Where "we'll revisit in March" lives — one shared note, not a schedule |
| **When did you discuss this** | radios + date, **required** | Same four contexts as §8.2, same reasoning. The date may be in the past, never in the future |
| Readership notice | permanent `ⓘ` | States exactly who can read it, at the point of writing — role rule 4 |
| **`Share this with Ravi`** | primary, names the act | Not `Save`. The act is *sharing*: it becomes visible immediately and notifies him |

**Authoring copy guidance, shown as helper text under the list:**
> `Write what the work will involve. Not how Ravi is doing now, and not a promise about what happens when he's
> done it — moving step is a decision you both make at a review.`

**A manager cannot write a roadmap that skips the ladder.** The `Working towards` select only offers real steps.
Where the level has no steps above the current one and no level above it, the dialog opens on a panel:
`Ravi is at the top of the Engineering ladder. There's no next step to work towards. Talk to HR about the
ladder, or raise a level change if there's another family that fits.`

### 22.3 The employee's view — the primary one

Their own profile, right column, above **My Pay**. Gate `job_architecture:r`, self-scoped server-side.
**This is the card the whole of A1 exists to produce**, so it is written for somebody who has never heard the
phrase "job architecture".

```
┌─ Your level and next step ──────────────────────────────────────┐
│  You are a Trainee Software Engineer, at step 1.2.               │
│  Step 1.2 means: works independently on well-defined tasks.      │
│                                        [ See the whole ladder → ]│
│                                                                  │
│  ── Working towards step 1.3 ──────────────────────────────────  │
│  Step 1.3 means: leads a small piece of work end to end.         │
│                                                                  │
│  What Marcus Lee wrote for you, on 12 August 2026:               │
│   • Take the payments migration through to release, including    │
│     the rollback plan                                            │
│   • Run the design review for it yourself                        │
│   • Be the first responder for payments alerts for a rotation    │
│                                                                  │
│  "We'll look at this again at the mid-term review."              │
│                                                                  │
│  Discussed at your mid-term goal review on 12 August 2026.       │
│                                                                  │
│  Moving to step 1.3 is something you and Marcus decide together  │
│  at a review. This isn't a checklist and it isn't a promise —     │
│  it's what you agreed the next step looks like.                  │
│                                                                  │
│  [ Confirm we discussed this ]   [ Ask to discuss it ]           │
│                                                                  │
│  Earlier versions (2)                                        [ ▸ ]│
└──────────────────────────────────────────────────────────────────┘
```

**Every line of that card is a decision. The ones that matter:**

1. **It opens with where they are, not with what they lack.** `You are a Trainee Software Engineer, at step 1.2.`
   A card that opens on the gap reads as a deficiency notice.
2. **The generic meaning comes before the personal list**, so the personal list reads as *an application of a
   company standard* rather than one manager's opinion about one person.
3. **The author and date are named on the personal list.** `What Marcus Lee wrote for you, on 12 August 2026.`
   Anonymous expectations are the ones people resent.
4. **The closing sentence carries three separate protections in one breath** — who decides (`you and Marcus`),
   when (`at a review`), and what this is not (`isn't a checklist and isn't a promise`). It is the roadmap's
   equivalent of My Pay's *"this isn't a payslip"* and it appears on every variant of this card.
5. **No progress of any kind.** No `1 of 3`, no bar, no ticks, no "you're nearly there" (D-R12, §25). The bullets
   are a description, and a description cannot be 40% complete.
6. **No dates on the items and no deadline anywhere.** The only date is the one that already happened — the
   review it was discussed at.
7. **`Ask to discuss it` exists because `Confirm` must not be the only exit.** A single "agree" button on an
   object the product calls *mutually decided* would be a coercive nudge, and the guardrails forbid those
   outright. It is the employee's honest alternative to clicking something untrue.
8. **Earlier versions are collapsed but present**, because *"what did we agree in March"* is the question this
   object exists to answer, and the answer belongs to the employee as much as the manager.

### 22.4 The acknowledgement interaction

**`[ Confirm we discussed this ]`** — a real button, one click, no dialog, no typing.

> Helper, under the buttons: `This records that you've read it and talked it through with Marcus. It isn't
> approval, and it doesn't commit you or the company to anything.`

After: the buttons are replaced by `✓ You confirmed you discussed this on 14 August 2026.` in `#15803d`, with
glyph and words. `#live-status` → `Confirmed. Marcus Lee has been told.` The manager gets
`ROADMAP_ACKNOWLEDGED`. **It cannot be undone** — but a new version resets it, which is the correct remedy,
because the thing to re-confirm is the new content.

**`[ Ask to discuss it ]`** — opens a small inline field, not a modal:

> `What would you like to talk about? (optional)`
> `[                                                        ]`
> `Marcus will see that you've asked. Nothing else changes.`
> `[ Cancel ] [ Send ]`

The state becomes `You asked to discuss this on 14 August 2026.` and the manager gets
`ROADMAP_DISCUSS_REQUESTED` (💬). **It is not a rejection and the UI never calls it one** — no red, no ⚠, no
"declined". It clears when the manager publishes a new version or marks it discussed.

**What is deliberately absent:** no "I disagree", no dispute state, no escalation to HR, no comment thread. Those
are conversations, and building a channel for them inside a development-plan object is the first step into a
performance module (§25). The product's job is to record that a conversation is wanted, and stop.

### 22.5 Versioning

- **Publishing a new version supersedes, never overwrites.** Every version keeps its author, its date, its review
  context and its acknowledgement state.
- The manager's dialog opens pre-filled with the current version's content and the header
  `Version 3 · replaces the one you wrote on 12 March 2026`, so re-agreeing at a review is an edit of last time's
  words rather than a blank page. **This is the single thing that decides whether roadmaps are maintained.**
- The employee's `Earlier versions (2)` disclosure lists each as
  `Version 2 · 12 March 2026 · written by Marcus Lee · confirmed 14 March`, expanding to the full content.
- **A version is never deleted** (UX-A1-Q2 records the discomfort).
- Changing the `Working towards` step does **not** create a version implicitly: it is part of the new version the
  manager is publishing, and the employee's card says so — `Working towards step 1.3 (was 1.4).`

### 22.6 Every state — the roadmap

| # | State | Manager sees | Employee sees |
|---|---|---|---|
| L1 | Loading | Skeleton form; the generic expectations panel loads first (it is static) | Three skeleton lines |
| L2 | Sharing | `Share this with Ravi` → `Sharing…`, disabled, dialog un-dismissable | — |
| **E1** | **No roadmap yet** | `Ravi doesn't have a next-step roadmap.` + `[ Write one… ]` + the muted line `Most managers write these at a review.` | `Your manager hasn't added a next-step roadmap yet.` + `It's usually written or updated at a review.` **Neutral, and it explains when to expect one** — never "your manager has not done this", which turns a card into a complaint |
| **E2** | **Target step has no expectations written** | The `What 1.3 means here` panel reads `Nobody has described step 1.3 yet.` + `[ Describe it → ]` for `job_architecture:w`, otherwise `You can still write what it means for Ravi.` | The generic line is absent; the personal list stands alone. **Never an empty quotation box** |
| E3 | Employee not on a level | `Ravi isn't on a level yet, so there's no next step to work towards.` + `[ Assign a level → ]` for the right holder | `You're not on a level yet. Your HR team is still setting this up.` |
| E4 | At the top of the ladder | §22.2's panel | `You're at the top of the Engineering ladder. Talk to Marcus about what's next.` |
| **PD1** | **Partial — shared, not acknowledged** | `Shared 12 Aug · Ravi hasn't confirmed yet` on the profile card and in `My Team`. **A muted fact, not a chase** — no red, no "overdue", no reminder notification | The two buttons, unpressed |
| PD2 | Partial — asked to discuss | `Ravi asked to discuss this on 14 Aug: "Not sure about the rotation."` + `[ Write a new version ]` `[ Mark as discussed ]` | `You asked to discuss this on 14 August 2026.` |
| PD3 | Partial — author has left the company | Version shows `written by Marcus Lee (no longer at the company)` — the content survives the author, as EP38's audit entries do | same |
| PD4 | Partial — the target step no longer exists (ladder changed) | `The step this was written for (1.4) no longer exists. Write a new version.` The old content stays readable | `The step this was written for has changed. Marcus will update it.` |
| PD5 | Employee changed manager | The new manager sees the existing roadmap and its author; **it is not reassigned, not deleted, and not hidden** | Unchanged. The card names the original author, with `(your manager at the time)` |
| V1 | Validation — no target step | `Choose the step Ravi is working towards.` |
| V2 | Validation — nothing written | `Write at least one thing. A roadmap with nothing in it isn't a roadmap.` |
| V3 | Validation — no review context | `Say when you discussed this. If it wasn't at a review, choose "Not at a review".` |
| V4 | Validation — date in the future | `The date can't be in the future — this is when you discussed it.` |
| V5 | Validation — banned word | Non-blocking `role="status"` nudge, identical to §6.9 V4: `"Exceeds expectations" reads like a rating. Describe the work, not how Ravi is doing.` |
| E5 | Error — share failed | `We couldn't share this. Nothing has been sent and your text is still here — try again.` Draft preserved for the session |
| E6 | Error — acknowledge failed | — | `We couldn't record that. Try again.` The buttons return; nothing is half-recorded |
| E7 | Conflict — a newer version exists | `Marcus published a newer version while this was open.` + `[ See it ]`; your draft is preserved for copying | Card refreshes to the newest on next load |
| **P1** | **A colleague** | — | **Nothing. No card, no link, no payload field.** An employee sees their own roadmap and nobody else's — asserted at the payload, not the DOM (D-R1) |
| P2 | HR (`job_architecture:w`, not their manager) | Can read and write it. **Deliberate:** HR runs the ladder and covers for absent managers. Every version names its author, so an HR-written roadmap is visibly HR-written | Card shows `What Priya Nair (HR) wrote for you` — never anonymised into "your manager" |
| P3 | Manager of a manager (skip-level) | **No access by default** — `job_architecture` scoping is direct reports, matching `compensation`'s D5.2 default. A tenant may widen it | — |
| P4 | Tenant switch off | Card absent; nav absent | Card absent |
| S1 | Success — shared | `✓ Shared with Ravi Sharma.` `He'll see it on his profile and be asked to confirm you discussed it.` `[ Done ]` | Bell: `📋 Marcus Lee has written your next-step roadmap.` `Read it →` |
| S2 | Success — acknowledged | Bell: `✅ Ravi Sharma confirmed you discussed his next-step roadmap.` | `✓ You confirmed you discussed this on 14 August 2026.` |

### 22.7 Accessibility — the roadmap

- **Manager's keyboard path:** opener → dialog title → `Working towards` → *(the generic panel is a
  non-focusable region; `[ Start from these ]` is a button in the tab order)* → each item's reorder handle → its
  text → its `✕` → `+ Add something` → notes → review-context radios (arrows within, Tab exits) → date →
  `Cancel` → `Share this with Ravi`.
- **Employee's keyboard path:** the card is reachable in DOM order; `Confirm we discussed this` →
  `Ask to discuss it` → `Earlier versions` disclosure (`aria-expanded`, `aria-controls`).
- **Reordering is keyboard-first** (`↑`/`↓` on the handle, announced `Moved to position 2 of 3`), identical to
  §6.6 and §6.9. No pointer-only path anywhere in EP42.
- **Semantics:** the personal list is a `<ul>`, not a series of `<div>`s and **not** a list of checkboxes — a
  screen-reader user must not be told there is something to tick. The generic panel is
  `<section aria-label="What step 1.3 means at Acme Corp">`. Versions are an `<ol>` newest-first with
  `<time datetime>`.
- **Acknowledgement:** the button's accessible name is the full sentence `Confirm we discussed this next-step
  roadmap with Marcus Lee`; its `aria-describedby` is the "isn't approval" helper, so a screen-reader user hears
  the limitation before they act. After acknowledging, focus moves to the confirmation line (`tabindex="-1"`).
- **Live regions:** `#live-status` for shared / confirmed / discussion requested / version added; `#live-alert`
  for the two failures.
- **Contrast:** the confirmation uses `#15803d` on white (5.01:1); the "not confirmed yet" state uses
  `var(--muted)` (4.76:1) and **no colour at all** — it is a neutral fact, and amber would make a manager's
  unanswered message look like the employee's fault.
- **Never colour alone:** confirmed / not confirmed / discussion requested each carry a glyph **and** the words.
- **Mobile ≤767px:** the employee card is the EP42 surface most likely to be read on a phone, from a bell
  notification. Full width, the two action buttons stacked at ≥44px, versions collapsed, no horizontal scroll at
  320px.

---

## 23. *(A1, NEW)* KAN-206 — Step pay points, the increment, and the tolerance

> The money half of the ladder, and the configuration that makes *"the pay should be adjusted"* computable.
> Two screens' worth of controls, deliberately placed on screens that already exist: **the pay points and the
> increment live in the ladder's money column** (§6.3), and **the tolerance lives on Compensation Settings**
> under a different gate (§3.7). Nothing here is a new page.

### 23.1 The money column of the ladder — `compensation:w`

```
│  ⠿ Level 1  [ Trainee Software Engineer ]  │  Germany (EUR)          ▾ │
│      Steps to the next level [ 5 ▾ ]       │  Base at 1.0 [ 48,000 ]   │
│      1.0 · 1.1 · 1.2 · 1.3 · 1.4 · 1.5     │  Each step  +[ 5.0 ]%     │
│      ✎ 6 of 6 steps described  12 people ⋯ │  [ Show the pay points ]  │
```

**`[ Show the pay points ]` expands the single most important thing on this screen** — the computed table, which
is the only defence against the compound-versus-linear confusion the SPM flagged as *"small enough that
engineering would guess either way and never notice, large enough to be wrong"*:

```
  Step   Pay point      Each step is 5.0% above the one below it.
  1.0    €48,000.00     That compounds — 1.2 is 5% above 1.1, not 10% above 1.0.
  1.1    €50,400.00
  1.2    €52,920.00     Top of this level: €61,261.51
  1.3    €55,566.00     A 5-step level has six pay points, 1.0 to 1.5.
  1.4    €58,344.30
  1.5    €61,261.51
```

The compounding sentence sits beside the table, not in a tooltip, because an HR admin who assumes linear will
read the numbers, notice `€52,920` where they expected `€52,800`, and need the explanation **there**.

| Element | Control | Rules |
|---|---|---|
| Pay market selector | `<select>` above the column | The pay points are per (level × pay market). Switching markets re-renders the column only |
| Base at `.0` | money input | Required per market before the check can run for anybody in it. Empty renders `Not set`, never `0` |
| Each step `+ %` | number, 0.1–50.0, one decimal | Required with a base. Per level, **with an optional per-step override** — `[ Override a step ]` reveals a per-step percentage list, defaulted to the level value and clearly marked where overridden |
| Currency | not an input | Inherited from the pay market, shown read-only with `The pay market sets the currency.` |
| **`[ What would this cost? ]`** *(Should · P3)* | button | Totals the gap between current pay and fitted pay points across the company. `compensation:r`, company scope, and **suppressed below n = 5** (D-R9a). Copy: `Bringing everyone up to their step's pay point would cost about €184,000 a year across 118 people. This is an estimate from what's recorded today — it isn't a budget.` |

### 23.2 Guard 1 — the tolerance the product must refuse *(the copy that has to explain itself)*

On **Compensation Settings**, gated `company_settings:w` (CFL-42-20):

```
  Pay-equity tolerance
  How far from a step's pay point someone can be paid before we flag it.
  ± [ 2.0 ] %        Your step increments range from 4.0% to 5.0%.
```

**When the entered tolerance is ≥ half the smallest increment, the save is refused** — and the refusal has to be
explicable to an HR administrator who has never thought about overlapping bands:

> ⛔ **A tolerance of ±5% can't be used with your step increments.**
>
> Your smallest step increment is 4%. With a ±5% tolerance, the "correct pay" range for one step would stretch
> past the next step's pay point — so almost everybody would count as correctly paid for **two** steps at once,
> and the check would pass everyone while looking like it was working.
>
> The tolerance has to be less than half your smallest increment. With a 4% increment, that means **under 2%**.
>
> `Suggested: ±1.5%`   `[ Use ±1.5% ]`   `[ Change the increments instead → ]`

Four things that copy does, in order: **names the refusal**, **explains the mechanism in one sentence a
non-specialist can follow**, **states the rule as arithmetic they can check**, and **offers the fix in one
click** — plus the alternative fix, because the increment may be the thing that is wrong. It is a hard block
(SPM §14.2.2, risk R-16: *"the most likely way to render the whole feature useless through a plausible-looking
setting"*), so it is the one place in EP42 where a configuration value cannot be saved at all.

**Live feedback before the refusal.** The field validates on input, not on save: the helper line under it reads
`Fine — this is well inside half your smallest increment (2.0%).` in `var(--muted)`, or turns to the amber
warning shape at ≥1.8% with `Getting close to the limit — half your smallest increment is 2.0%.` A user should
meet the boundary before they hit the wall.

**When the increments change afterwards**, the tolerance can become invalid without anybody touching it. The
ladder's save review (§6.5) therefore carries: `⛔ Lowering Engineering's increment to 3% would make your current
±2% tolerance invalid. Change the tolerance first, or use 4% or more.` — blocking, at the point of the change.

### 23.3 Guard 2 — a level that starts below the one beneath it *(warning, not a block)*

Shown inline in the money column at configuration time:

> ⚠ **Level 2 starts below the top of level 1.**
> A Junior Software Engineer at step 2.0 would be on €60,000, but a Trainee at step 1.5 is already on €61,262 —
> so somebody promoted from the top of level 1 would take a pay cut.
> Some companies overlap levels deliberately. If that's you, carry on.
> `[ I meant this ]`   `[ Change level 2's base ]`

**Non-blocking, deliberately** — overlapping levels are a real pay design — but **dismissal is per level and is
remembered**, so it does not nag, and it returns if either figure changes. Amber `#fffbeb`/`#b45309`,
`role="status"`, glyph and words.

### 23.4 Every state — pay points

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | The money column shows skeleton fields; the job-content column renders immediately (it does not depend on money) |
| **E1** | **No pay markets configured** | Column replaced by `You need pay markets before you can set pay points.` + `[ Set up pay markets → ]`. Pay markets default to one per country, so this only appears in a tenant with no locations |
| **E2** | **No pay point set for this level/market** | Every step reads `Not set`; `[ Show the pay points ]` expands to `No base pay point for Engineering level 1 in Germany, so we can't work out the step pay points.` **Never €0** |
| E3 | Base set, no increment | `Set how much each step is worth to see the pay points.` |
| **PD1** | **Partial — some markets set, some not** | The market selector marks each option `Germany (set)` / `Estonia (not set)`, so an admin can see the shape of the job without visiting each one |
| PD2 | Partial — per-step overrides in use | The computed table marks overridden rows `1.4 €58,344.30 · overridden +7.0%`, with the word, not a colour |
| PD3 | Level has no step count yet | The pay-point table is absent with `Set how many steps this level has first.` |
| V1 | Validation — base ≤ 0 | `The base pay point has to be more than zero.` |
| V2 | Validation — increment out of range | `The step increment has to be between 0.1% and 50%.` |
| V3 | Validation — increment with no base | `Set the base pay point for Germany first.` |
| **B1** | **Blocked — tolerance ≥ half the increment** | §23.2 |
| W1 | Warned — level base below the previous top step | §23.3 |
| E4 | Error — save | `We couldn't save the pay points. Nothing has changed — your figures are still here.` |
| **P1** | **`job_architecture:w` without `compensation:r`** | **The entire money column is absent, header included**, and the ladder reads as a complete page (§3.7) |
| P2 | `compensation:r` without `w` | The column renders read-only: the computed table, no inputs, no `[ Show the pay points ]` toggle needed — it is expanded |
| P3 | Tolerance section, without `company_settings:w` | Absent from Settings; the rest of the page is coherent |
| S1 | Success | `✓ Pay points saved for Engineering in Germany.` + `#live-status` → `Saved. Six pay points from €48,000 to €61,262. Pay equity will re-check 12 people.` |

### 23.5 Accessibility — pay points

- The computed pay-point table is a real `<table>` with `<caption>Pay points for Engineering level 1 in
  Germany</caption>` and `<th scope="col">`; the compounding sentence is its `aria-describedby`, so it is read
  before the numbers rather than after them.
- `[ Show the pay points ]` is `aria-expanded` + `aria-controls`.
- The tolerance refusal is `role="alert"` and takes focus (nothing was saved); the "getting close" state is
  `role="status"` and does not.
- The suggested-value button's accessible name is the full action: `Use a tolerance of 1.5 percent`.
- Money inputs are `inputmode="decimal"` with the currency in the label, not as a decorative prefix, so a screen
  reader announces `Base pay point at step 1.0, euros`.
- Below 768px the money column moves **below** the job-content column for each level rather than beside it, and
  the computed table scrolls inside `.table-wrap`.

---

## 24. *(A1 / UXQ5, NEW)* The audited salary export

> Ruled into **KAN-202 as a Should**: *"UX is right that HR asks within a week and that the alternative is
> someone adding an unaudited CSV button."* Designing it deliberately is the whole point — an export is the
> single easiest way to undo every discretion rule in §3.3.

**Entry:** `/compensation` → **Export**. Nowhere else. **No export button on the profile, the register, the
directory or any list** — one door, watched.

**Gate:** `compensation:r`. **The export is row-scoped exactly as the screen is** — a manager exports their four
reports, an HR admin exports the company. There is no "export everything" option and no scope selector: the scope
is the viewer's, always, and the screen states it.

```
┌ Export current salaries ────────────────────────────────────────┐
│  What you'll get                                                 │
│  One row per person you can see, with their current salary,      │
│  currency, FTE, effective date, level and step.                  │
│                                                                  │
│  Scope    Everyone in Acme Corp — 146 people, 91 with a salary   │
│           recorded.                                              │
│  Include  ☑ Level and step   ☐ Salary history (all records)      │
│                                                                  │
│  ⚠ This file contains pay data for 91 people.                    │
│    Your name and the time are written into the file, and the      │
│    export is recorded in the audit trail.                        │
│                                                                  │
│  Why do you need it? *                                           │
│  [ — Select a reason — ▾ ]  payroll handover · pay review ·      │
│                             audit request · data correction ·    │
│                             other                                │
│  [                                                            ]  │
│                                                                  │
│                     [ Cancel ]   [ Export 91 rows ]              │
└──────────────────────────────────────────────────────────────────┘
```

**Six rules, each of which exists because of a way exports leak:**

1. **The row count is in the button.** `Export 91 rows`, not `Download`. Somebody about to export the whole
   company should see the number before they click, not after.
2. **A reason is required**, category plus optional text, and it goes into the audit record. An export with no
   stated purpose is the one you cannot explain six months later.
3. **The file is watermarked in-band.** Row 1 of the CSV is a comment line:
   `# Acme Corp — current salaries — exported by Priya Nair (HR Admin) on 9 August 2026 14:32 — 91 rows — CONFIDENTIAL`.
   A CSV that has been forwarded twice still says who produced it.
4. **Every export is audited** as `COMPENSATION_EXPORTED` with the actor, scope, row count and reason — and
   **without any amount** (D-R5, amendment A-2's allowlist).
5. **The scope is stated, not chosen.** No "all companies" for SYSTEM_ADMIN — cross-tenant pay export does not
   exist for any role (SPM §3.3), and the screen says `You're exporting Acme Corp. Switch company to export
   another one.`
6. **Salary history is opt-in and warned:** ticking it changes the notice to
   `⚠ This file will contain 412 pay records for 91 people, including past salaries.` and the button to
   `Export 412 rows`.

**States:** *Loading the count* — `Working out what you can export…`, button disabled. *Empty (nobody in scope
has a salary)* — `Nobody you can see has a salary recorded, so there's nothing to export.` + `[ Import salaries →
]`. *Row-scoped to zero people* — `You can't see anyone's pay, so there's nothing to export.` (only reachable if
scope changed mid-session). *Validation* — `Say why you need this export.` *Error* —
`We couldn't produce the export. Nothing has been downloaded and nothing has been recorded.` *No `compensation:r`*
— tab absent. *Tenant off* — §3.4. *Success* — the file downloads and the page shows
`✓ 91 rows exported and recorded in the audit trail.`

**Accessibility:** the notice is `role="status"` and re-announced when the include-options change the counts; the
button's accessible name is the full sentence `Export 91 rows of pay data`; the download completing is announced
to `#live-status` because a file download is otherwise a silent event.

---

## 25. *(A1, NEW)* The line against performance management

> **Risk R-17: the step roadmap drifts into performance management through entirely reasonable-sounding
> increments.** The SPM asked me specifically to hold this line, and the boundary is easiest to defend if it is
> written down before anybody asks. **EP42 records that a step change happened at a review. It does not build the
> review.**
>
> This section is written so that a future request can be checked against it in one minute, by a person who was
> not in this conversation.

### 25.1 What EP42 builds

A **description** of each rung (§6.9) · a **statement** from a manager to one person about the next rung (§22) ·
a **record** that a step changed, when, and at what kind of review (§8.2) · a **fact** about where people sit on
the ladder and since when (§8.7) · and a **check** that pay corresponds to the step (§14).

Every one of those is a *description, statement, record or fact*. **None of them is a judgement about a person**,
and that is the line.

### 25.2 The nine things that are out, and the reasonable-sounding request that produces each

| # | The request, as it will actually be phrased | What it would build | Ruling |
|---|---|---|---|
| 1 | *"Could the employee tick off the roadmap items as they do them?"* | Completion tracking → task management → goals | **No.** Roadmap items are `<li>`, never checkboxes. §22.3 rule 5 |
| 2 | *"Just a little progress bar so they can see how far along they are"* | A completion percentage of a subjective list | **No.** A description cannot be 40% complete. D-R12 |
| 3 | *"A due date on each item — otherwise nothing happens"* | Deadlines on personal development → a performance improvement plan in all but name | **No.** One optional shared note ("we'll revisit in March"); no per-item dates. §22.2 |
| 4 | *"Let the manager mark the roadmap as met or not met"* | An outcome field → a rating with two values | **No.** A roadmap is superseded by a new version; it is never closed as met or unmet. §22.5 |
| 5 | *"Show me who's moving fastest through the steps"* | A ranking of people by progression rate | **No.** §8.7's table shows step and date, never a rate, a ranking or a comparison |
| 6 | *"Flag anyone who's been on a step too long"* | A red status on a person | **Partly, and carefully.** §8.7 states the *fact* — `6 people have been on their step for more than 18 months` — with no adjective, no colour, no icon, and it can be switched off. It exists to find pay that never followed, not people who are slow |
| 7 | *"Remind managers when a probation review is due"* | Review scheduling → a review cycle | **No.** EP42 records the context of a review that happened. It does not know when one is due, because it has no probation entity and no cycle. §8.2 |
| 8 | *"A rating field on the step change — it was discussed at the review anyway"* | The review itself, one field at a time | **No.** The step change carries a context, a date and a note. The note is for facts about the change, and §6.9's word list applies |
| 9 | *"Managers want to compare their team against another team's ladder position"* | Calibration | **No.** Cross-team comparison of ladder position is calibration with a different name, and calibration is the core of a performance module |

### 25.3 The three places the line is thinnest

Named, because a boundary is defended at its weak points and these are where a well-meaning change would cross it
without anybody noticing.

1. **The disposition category `Pay held while performance is being discussed`** (§14.5). It is legitimate, it is
   the only place a performance judgement can attach to a pay record, and its free text is permanent and widely
   readable. Mitigated by the sentence in §14.5; **it should be reviewed with the DPO alongside DPO-1.**
2. **The step-change `note` field** (§8.2). It is free text on an audited, retained record about a person, written
   at a performance review. Nothing stops a manager typing an appraisal into it. Mitigated by the field's helper
   (`What changed and why — not how Ravi is doing`) and by the §6.9 V4-style nudge; **not** mitigated by
   validation, because it cannot be, and claiming otherwise would break the SPM's own standing rule that a
   guarantee is only stated if the mechanism delivers it.
3. **The `18 months on a step` line** (§8.7). One adjective away from a performance metric. Fixed copy, no colour,
   no icon, switchable off, and the threshold is a company setting rather than a product opinion.

### 25.4 How to apply this line to a request that is not on the list

Three questions, in order:

1. **Is it a description of work, or a judgement about a person?** Judgements are out.
2. **Would it still make sense if the person's name were removed?** If not, it is personal assessment, not job
   architecture.
3. **Does it create a comparison between people?** Comparisons of *pay* against a configured point are the
   feature. Comparisons of *people* against each other are calibration, and calibration is a different product.

If a request passes all three and still feels like performance management, it probably is — and the honest answer
is the SPM's: *"if he wants it, it is a conversation about a new epic, not an expansion of this one."*

---

## 26. *(A1, NEW)* Wave 4 change log — every superseded rule, named

| § | What I specified in Wave 2 | Status | What replaces it, and why |
|---|---|---|---|
| §3.1 | Three feature codes | **Amended** | Four. `job_architecture`, so a manager can author a roadmap without write access to everyone's salary |
| §3.1 | Thresholds gated `pay_equity:d` | **Rejected** (CFL-42-20) | `company_settings:w`. A grant labelled "delete" that confers "configure" misleads where the choice is made |
| §3.2 | "API without access → 403" | **Amended** (CFL-42-8) | A JSON-aware 403; the decorator returns a 302 today. Cross-tenant is 404 (CFL-42-33) |
| §4 | The ladder as a tab of `/compensation` | **Moved** | `/ladder`, in main Navigation, because every employee reads it |
| §6.3 | `Steps [ 5 ▾ ]`, default 5, preview `1.1 … 1.5` | **Superseded** | No default; entry at `.0`; every value listed, six for a count of five |
| §6 | A structural editor | **Extended** | A content editor with an audience outside HR (§6.9) |
| §7.2 | Bulk assignment defaults to step 1 | **Superseded** | `— Fit to pay —`, because a `.0` backfill would flag most of the workforce on day one |
| §7 | Level assignment ends the backfill | **Extended** | §7.9's fitted-step review now gates the entire equity feature |
| §8.1 | Job Level card gated `compensation:r` | **Amended** | `job_architecture:r`; the pay point inside it stays `compensation:r` |
| §8.2 | A pay change makes the **step** wait for approval | **Superseded** (SPM §14.4) | The step applies; the pay is **proposed**. The gap between them is the thing Check A′ detects |
| §8.4 | Signal to the manager *and* `compensation:w` holders | **Narrowed** | The reporting manager only |
| §9.5 | "Compensation data: 62%" | **Amended** (A-5) | **Pay coverage** and **level coverage**, each naming its denominator; the equity gate is a third thing and is not a percentage |
| §9.6 E2 | Contractors: no record action | **Overruled** (UXQ8) | Recordable, with two distinct empty states |
| §10.6 P5 | No `compensation:r` → a placement-only transfer | **Amended** (CFL-42-13) | `NOT_ANSWERED_NO_PERMISSION`; the first pay-capable approver must answer |
| §11.3 | A derived display label for demotions | **Deleted** (CFL-42-25) | `LEVEL_CHANGE` + `direction`. A label cannot fix a lie in the audit record |
| §13 | Bands are the comparison basis | **Repositioned** | The level's min/max envelope. The basis is the step pay point |
| §14.2 | Group median / band midpoint, `n ≥ 3`, compa-ratio 0.95–1.10 | **Superseded** | Check A′: the step pay point, ±2% tolerance, n = 1 valid |
| §14.4 E1 | The 80% coverage-gate screen | **Superseded** | The fitted-step review gate. *The rule it protected — never render "no findings" when the check has not run — survives unchanged* |
| §14 | One finding type | **Superseded** | Three, with asymmetric severity, and a remedy on the primary one |
| §15.2 | Eleven icons | **Extended** | Seventeen; `PROMOTION_*` renamed `LEVEL_CHANGE_*` |
| §19 | Ten open questions | **Amended** | Eight answered; four new from A1 |
| §20 | Eight conflicts | **Amended** | All eight ruled; four new from A1 |

**What survived A1 untouched, and is worth saying:** the ten discretion rules (extended, not revised) · "absent,
not hidden" · every empty-state rule including "never render 'no findings' without what was looked at" · the
standing-condition lifecycle in §14.3 · the no-dismiss rule · the bell's blind-spot discipline · every
accessibility annotation. **The reference value changed; the design principles did not have to.** That is the
best evidence I have that Wave 2 was built on the right foundations.
</content>
</invoke>
