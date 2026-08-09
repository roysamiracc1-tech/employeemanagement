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
> or offer compensation, and any automatic pay or level change.

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
| Excluded by employment type | **Not applicable — Contractor** | "No salary recorded" |
| `PAY_EQUITY_FLAG_RAISED` etc. | never rendered; every code has a sentence | any enum on screen |

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

### 3.1 The three feature codes and the surface map

Per `CLAUDE.md` and SPM D5.1: routes use `@require_feature_access('code')`, nav uses
`{% if has_feature_access('code') %}`, **no hardcoded role lists, no per-feature sub-flags**. Row scoping is a
service-layer rule and is *not* the forbidden sub-flag (SPM D5.3).

| Surface | Feature code | Action | Row scope | Story |
|---|---|---|---|---|
| Nav item **Compensation** | `compensation` | `r` | — | KAN-193 |
| `/compensation` → Overview (coverage meters, deferred list) | `compensation` | `r` | viewer's scope | KAN-195 |
| `/compensation` → Job ladder | `compensation` | `w` (read-only view for `r`) | company | KAN-190 |
| `/compensation` → Level assignment | `compensation` | `w` | company | KAN-191 |
| `/compensation` → Salary bands | `compensation` | `w` (read-only for `r`) | company | KAN-199 |
| `/compensation` → Import | `compensation` | `w` | company | KAN-195 |
| `/compensation` → Settings (pay markets, reason categories) | `compensation` | `w` | company | KAN-195/199 |
| Equity thresholds, gate, pay-market definition | `pay_equity` | **`d`** — see §20 UX-CFL-42-1 | company | KAN-200 |
| Nav item **Pay Equity** + `/compensation/equity` queue | `pay_equity` | `r` | company | KAN-201 |
| Disposition a finding | `pay_equity` | `w` | company | KAN-201 |
| Compensation card on **another person's** profile | `compensation` | `r` | viewer's scope | KAN-193 |
| `Record a change…` / `Record salary…` | `compensation` | `w` | viewer's scope | KAN-193 |
| Void / correct a historical record | `compensation` | `d` | company | KAN-193 |
| Compensation history timeline | `compensation` | `r` | viewer's scope | KAN-202 |
| Job Level card on another person's profile | `compensation` | `r` | viewer's scope | KAN-191 |
| `Advance step…` / `Request promotion…` | `compensation` | `r` **+** `_can_initiate_for` | subject | KAN-192/197 |
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

### 3.2 What "no access" looks like — for every surface

**Nothing.** Not a disabled control, not a greyed nav item, not a tooltip explaining what they are missing, not a
blurred figure, not a `••••`, not a "Hidden" chip, not an empty card with a lock on it.

- Sidebar items absent · profile cards absent · row-menu items absent (and an empty menu means no `⋯` at all,
  per `directory.html:297`) · the modal's pay block absent (SPM D4f: *absent, not disabled*).
- Direct URL → the existing `require_feature_access` behaviour: flash `You do not have access to that page.` and
  redirect to the dashboard. **No bespoke 403 page for EP42.**
- API without access → `403`, no state change. If a dialog is open, see the per-screen `P` states.
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
| **D-R9** | **A derived number is the same data class as the number it derives from.** Compa-ratio, group median, measured gap and percentage change are all money and follow `compensation:r`, not `pay_equity:r` | A gap percentage plus one known salary is another salary. See §14.2 for what a `pay_equity`-only viewer sees instead |
| **D-R10** | **Never derive, estimate or impute a salary** — not from the band, not from the level, not from the group median, not "typical for this role" | SPM D7.6. An imputed figure on a screen is indistinguishable from a real one |

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

```
Sidebar › Navigation
  … unchanged …

Sidebar › Administration
  Admin Panel
  Vacation Types
  Change Workflow
  Compensation          ← NEW · {% if has_feature_access('compensation') %}
  Pay Equity            ← NEW · {% if has_feature_access('pay_equity') %}   (KAN-201)
  Analytics
  Skills Intelligence

/compensation                       tabs: Overview · Job ladder · Level assignment ·
                                          Salary bands · Import · Settings
/compensation/equity                the findings register (its own nav item, its own feature code)

Employee profile gains, in the LEFT column, in this order:
  Personal Info
  Reporting Structure
  Job Level            ← NEW (KAN-191/192)   compensation:r
  Compensation         ← NEW (KAN-193)       compensation:r  · row-scoped
  Lifecycle History    (EP38)

Your own profile gains, in the RIGHT column, above Skills:
  My Pay               ← NEW (KAN-194)       compensation_self:r

templates/org_change/_move_modal.html gains one Pay block (KAN-196) and one Job level block (KAN-197).
```

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

### 5.4 Pay-equity responsible — working a register, not a task list

| Stage | Goal | Pain | What this design does |
|---|---|---|---|
| Discover | Something needs looking at | An alert storm that gets muted (R-1) | Capped bell section, one row per condition, no re-announcement |
| Triage | "Which of these is mine?" | A shared queue nobody owns | An **owner** column and a `Take this` action — a recorded act, not a read |
| Judge | "Is this justified?" | A number with no context | Group drill-down: who is in it, who was excluded and why, coverage, and the caveats in plain language |
| Record | Close it properly | One-click dismiss | Category + mandatory explanation + validity window shown before saving |
| Trust | "Will it come back?" | Re-firing identical findings | A re-fired finding is labelled **Re-opened** with the reason, and shows the previous justification |

---

## 6. KAN-190 — The ladder configurator

> The hardest screen in the epic. A tenant defines families, levels, titles and step counts **from nothing**, in an
> order that makes sense before they know the vocabulary. The empty state matters more than the populated one.

### 6.1 Purpose and entry points

**Purpose:** describe the shape of the jobs in this company, so that promotions have rungs and pay equity has a
grouping key. **Nothing about any person changes here** — and the screen says so, twice.

**Entry:** `/compensation` → **Job ladder** tab. Also from the Level assignment tab's empty state
(`You need a ladder before you can put anyone on it. [ Build the ladder → ]`) and from the Overview tab's first-run
next action.

**Gate:** `@require_feature_access('compensation','w')` for the editor; `r` holders get the same page **read-only,
with no controls at all** (§3.1 note 2).

### 6.2 Empty state — the first-run panel

Rendered when the company has no job families. It is a panel, not a blank editor.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  Your company doesn't have a job ladder yet.                                  │
│                                                                               │
│  A job ladder describes the jobs in your company:                             │
│    • a job family — a discipline, like Engineering or Finance                 │
│    • levels inside a family — the rungs. Each level has its own job title.    │
│    • steps inside a level — how pay moves without a promotion. Shown as 2.3.  │
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

- **`Start from a worked example`** stages one family, three levels and five steps each, with real titles
  (`Engineering` · `L1 Software Engineer` · `L2 Senior Software Engineer` · `L3 Staff Engineer`) and a dismissible
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
┌ Job ladder ──────────────────────────────── [ 3 unsaved changes ] [ Save ladder ] ┐
│                                                                                   │
│  Job families            │  Engineering                              [ Rename ]   │
│  ────────────────────    │  ─────────────────────────────────────────────────     │
│  ▸ Engineering    3 lvls │                                                        │
│  ▸ Finance        2 lvls │  ⠿  Level 1  [ Software Engineer          ]            │
│  ▸ Sales          0 lvls │            Steps [ 5 ▾ ]  1.1 … 1.5      12 people  ⋯ │
│                          │                                                        │
│  + Add job family        │  ⠿  Level 2  [ Senior Software Engineer   ]            │
│                          │            Steps [ 5 ▾ ]  2.1 … 2.5       8 people  ⋯ │
│                          │                                                        │
│                          │  ⠿  Level 3  [ Staff Engineer             ]            │
│                          │            Steps [ 3 ▾ ]  3.1 … 3.3       0 people  ⋯ │
│                          │                                                        │
│                          │  + Add level                                           │
│                          │                                                        │
│                          │  Levels go from the bottom up. Level 1 is the most      │
│                          │  junior. The level's title is the job title people      │
│                          │  see in the directory and the org tree.                 │
└───────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Control | Rules |
|---|---|---|
| Family list | `<ul>` of buttons, one selected | Selected family is `aria-current="true"`. Count is levels, not people |
| Family name | text, required, ≤80, unique in company | `Give this job family a name.` / `You already have a job family called Engineering.` |
| Level ordinal | **derived from position, never typed** | Renumbering on reorder/delete is automatic and previewed |
| Level title | text, **required**, ≤120, unique within the family | This becomes the canonical job title (CFL-42-4) |
| Steps | `<select>` 1–12, default **5** | Live preview `1.1 … 1.5` beside it, so the number becomes concrete |
| People count | chip, links to Level assignment filtered to that level | `compensation:r` only. It is a headcount, not pay |
| Reorder | `⠿` handle **and** the `⋯` menu | See §6.6 — no pointer-only path |
| Row menu `⋯` | `Move up` · `Move down` · `Rename` · `Delete level` | `Delete level` last and in `#b91c1c`, per `directory.html`'s destructive-last ordering |

The explanatory paragraph under the list is permanent, not a tooltip. Two sentences that answer the two questions
every first-time configurer asks ("which way is up?" and "what does the title do?") are cheaper than a help page.

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
│   • Nobody moves level or step.                                             │
│   • No one's pay changes.                                                   │
│   • Nobody is notified.                                                     │
│     [ See the 8 people → ]                                                  │
│                                                                             │
│                                        [ Cancel ]   [ Save ladder ]         │
└─────────────────────────────────────────────────────────────────────────────┘
```

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

---

## 7. KAN-191 — Level assignment and the title backfill

> 41 distinct titles over 46 people at Acme, 75 over 100 at Telia (SPM S2). **This screen decides whether the
> backfill finishes** (risk R-2). Everything about it is optimised for one sitting.

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
| **Step select** | Defaults to **step 1** of the chosen level, with a permanent line above the table: `Everyone mapped by title starts at step 1. Change individuals afterwards in "By person".` Bulk-assigning a step is a pay-adjacent judgement and must not be made 5 people at a time by a dropdown default nobody read |
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

## 8. KAN-192 — Progression, and the top-step signal

> A signal, not an entitlement. One sentence, and it has to be the right one.

### 8.1 The Job Level card (employee profile)

Left column, above Compensation. Gate `compensation:r` + row scope.

```
┌─ Job Level ──────────────────────────────────────────────────┐
│  Job title      Software Engineer                            │
│  Family         Engineering                                  │
│  Level & step   Level 1 · step 1.5   ●●●●●  (5 of 5)         │
│  Working title  Payments Platform Engineer                   │
│  On this level  since 1 March 2025                           │
│                                                              │
│  ⓘ At the top step of this level.                            │
│    Reaching the top step doesn't change anyone's level,      │
│    title or pay by itself — a promotion is a separate        │
│    decision someone has to make.                             │
│                                                              │
│  [ Advance step… ]   [ Request promotion… ]   [ History → ]  │
└──────────────────────────────────────────────────────────────┘
```

**The step indicator** `●●●●● (5 of 5)` is glyph **and** number — never dots alone, and never colour alone. Its
accessible name is `Step 5 of 5`.

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

### 8.2 The `Advance step…` dialog — and the moment it becomes an approval

```
┌ Advance step — Ravi Sharma ─────────────────────────────── × ┐
│ EMP-0142 · Engineering · level 1 · step 1.3                  │
├──────────────────────────────────────────────────────────────┤
│  New step *        [ 1.4 ▾ ]        (1.1 – 1.5)              │
│  Effective from *  [ 09/08/2026 ]                            │
│  Reason *          [ ▾ ] Annual review                       │
│  Note              [                                    ]    │
│                                                              │
│  Pay *                                                       │
│  Currently €72,000 · EUR · 1.0 FTE · since 1 Mar 2026        │
│  ( ) No change   ( ) New salary   ( ) Decide separately      │
│  Say what happens to Ravi's pay. "No change" is an answer.   │
├──────────────────────────────────────────────────────────────┤
│                          [ Cancel ]   [ Advance to step 1.4 ]│
└──────────────────────────────────────────────────────────────┘
```

**The critical interaction.** Per SPM D3.4 a step advance is an immediate audited write *unless it carries a pay
change*, in which case D4 applies and it becomes a `COMPENSATION_REVIEW` on the approval chain. The user must be
told the moment that flips, not after they submit:

- Selecting **New salary** expands the amount fields **and** replaces the footer button with
  `[ Submit for Approval ]`, **and** inserts a `role="status"` notice above the footer:
  > `A pay change needs approval. This will be submitted as a compensation review, and the step change will be
  > applied together with the pay change once it's approved.`
  > `It needs 2 approvals: HR Admin, then Anna Weiss.`
- Selecting **No change** or **Decide separately** restores `[ Advance to step 1.4 ]` and removes the notice
  (announced: `This will be applied immediately.`).

A dialog whose button changes what it does must say so on the screen, every time.

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
| S1 | Success — immediate | In-dialog panel: `✓ Ravi Sharma is now on step 1.4.` `Effective 9 August 2026. Their pay is unchanged.` `[ Done ]` |
| S2 | Success — sent for approval | `✓ Submitted for approval.` `Ravi's step change and pay change are with HR Admin (approval 1 of 2). Neither is applied until the last approval.` `[ View in Position Changes ] [ Done ]` |

### 8.4 The top-step signal as a notification

Full D4 treatment is in §15; the design decisions specific to this signal:

- **Recipients:** the subject's solid-line manager, and `compensation:w` holders. **Not the subject.**
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
│  Compensation data                                                   │
│  ████████████░░░░░░░░  62%                                           │
│  91 of 146 active employees have a salary recorded.                  │
│  Not counted: 1 contractor, 0 interns.                               │
│  [ Export the 55 without a record (CSV) ]   [ Import salaries → ]    │
│                                                                      │
│  Job levels                                                          │
│  ██████████████████░░  91%                                           │
│  133 of 146 active employees are on a level.                         │
│  [ Export the 13 without a level (CSV) ]    [ Assign levels → ]      │
│                                                                      │
│  Pay equity                                                          │
│  Not running yet. Groups are only compared once 80% of the people    │
│  in them have a salary recorded.                                     │
│  You're 18% away — about 26 more people.                             │
│                                                                      │
│  Pay decisions deferred                    3                         │
│  Position changes that were applied with the pay decision put off.   │
│   • Ravi Sharma · deferred 2 Aug by Marcus Lee · "waiting on budget" │
│     [ Record salary… ]                                               │
│   • …                                                                │
└──────────────────────────────────────────────────────────────────────┘
```

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
| E2 | **Empty — contractor / intern** | `Not applicable — Contractor` + its helper. **No record action** (UXQ8) |
| E3 | Empty — no reason categories configured | Reason select `— No reasons configured —`, disabled, helper `Add salary-change reasons in Compensation → Settings first.` **Commit blocked**, and it says so up front rather than failing at submit (EP38 §5.8 E1 precedent) |
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
> `This will be raised as a **Promotion**.`
> `This will be raised as a **Compensation review**.`
> `This will be raised as a **Level change**.` *(downward or sideways level move — see §11.3)*

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
| P5 | No `compensation:r` | The whole fieldset absent; the request created is a placement-only `TRANSFER` |
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

### 11.3 Downward and sideways level moves — a vocabulary problem I must flag

SPM D3.4 allows downward moves; SPM D4e's enum is `TRANSFER · PROMOTION · COMPENSATION_REVIEW`, with type inferred
as "level changed → PROMOTION". **A demotion labelled "Promotion" in the inbox, the bell, the timeline and the
audit trail is a defect** — and the Demo Gate's *status vocabulary* blind-spot is exactly the rule it breaks.

**Interim design rule, until the SPM/BA resolve it (§20 UX-CFL-42-3):**

| New level ordinal | Displayed everywhere | Stored `request_type` |
|---|---|---|
| Higher than current | **Promotion** | `PROMOTION` |
| Lower than current | **Level change (down)** | `PROMOTION` |
| Same level, different family | **Level change** | `PROMOTION` |

The display label must be identical in the modal, the inbox, the bell, My Requests, the timeline and the success
copy — one word, everywhere, per the gate's vocabulary rule.

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

## 13. KAN-199 — Bands and compa-ratio

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

### 14.1 The framing sentence — on every equity screen, not in a tooltip

SPM D1.3 requires plain-language framing that this is a measurement, not a compliance conclusion. One paragraph,
identical on the queue, the group drill-down and the disposition dialog, in `#f8fafc`/`#e2e8f0`, always visible,
never collapsed:

> **This is a measurement, not a verdict.** The portal compares recorded base salaries inside one job level and one
> pay market. It doesn't know about bonus, benefits, performance, experience, or anything agreed outside the
> portal, and it can't decide whether a difference is justified. That judgement is yours — the portal records it.

Never abbreviated, never turned into an `ⓘ` icon, never behind a "learn more". A screen that produces findings about
people's pay carries its own caveat at full size.

### 14.2 The register — `/compensation/equity`

Gate `@require_feature_access('pay_equity')`. Nav item **Pay Equity**, Administration section.

```
┌ Pay Equity ────────────────────────────────────── [ 👁 Hide amounts ] [ Run check ] ┐
│  8 open findings · last checked 9 August 2026, 14:32                                │
│                                                                                     │
│  [ framing paragraph — §14.1 ]                                                      │
│                                                                                     │
│  State [ Open ▾ ]  Check [ Any ▾ ]  Group [ Any ▾ ]  Owner [ Anyone ▾ ]  Age [ ▾ ]  │
│                                                                                     │
│  Subject          Level & market        Group  Basis     Measured  State   Owner    │
│  ─────────────────────────────────────────────────────────────────────────────────  │
│  Ravi Sharma      Eng L2 · Germany      6      Band mid  ▼ 0.88    Open    —        │
│                   raised 12 days ago                                     [ Take ]  │
│                                                              [ Review → ]           │
│  Whole group      Eng L2 · Germany      6      Gender     ▲ 7.4%   Open    P. Nair  │
│                   raised 12 days ago                         [ Review → ]           │
│  Ana Costa        Fin L1 · Portugal     4      Median    ▲ 1.16    Re-opened  —     │
│                   re-opened 2 days ago — the gap widened     [ Review → ]           │
│  …                                                                                  │
│                                                                                     │
│  2 of 14 groups couldn't be compared. [ Why? ]                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

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
| **E1** | **Coverage below the gate** | **The queue does not render an empty list.** It renders the coverage panel: `Pay equity isn't running yet.` + the compensation coverage meter + `Groups are only compared once 80% of the people in them have a salary recorded. Right now that's true for 2 of your 14 groups.` + `[ Export who's missing (CSV) ]` + `[ Import salaries → ]`. **The words "no findings" must not appear on this screen** — "no findings ✓" at 40% coverage is the most dangerous screen we could ship (SPM D7.4) |
| E2 | Never run | `Pay equity hasn't been run yet.` + `[ Run check ]` + the framing paragraph |
| **E3** | **Coverage met, genuinely nothing found** | `No open findings.` **always followed by what was looked at**: `Last checked 9 August 2026 at 14:32. 12 of 14 groups were compared; 2 didn't have enough people. 91 of 146 employees were included.` "Nothing found" may never be rendered without "here is what we looked at" |
| E4 | Every group too small | `Nothing could be compared.` `Every group has fewer than 3 comparable people. Pay equity needs at least 3 people on the same level in the same pay market.` + `[ See your groups → ]` |
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

### 14.6 KAN-202 — the compensation timeline

Opened from `History →` on the Compensation card, and from My Pay when the tenant enables it. Gate
`compensation:r` + row scope. **A compensation surface, not an audit surface** — holding `audit_log:r` alone never
reveals an amount (SPM D5.6).

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

**Not one of the eleven is ❌ unless something was actually refused.** A pay-equity finding is not a refusal of
anything and must never wear a cross — that is DEF-002 exactly, and pay is the worst possible place to repeat it.

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
| **Regression coverage** (UAT owns the files) | Nav visibility by feature code and by tenant switch · the locked screen · `No salary recorded` vs `Not applicable` vs absent, for three viewer types · the amount **absent from the JSON payload** for an out-of-scope viewer · the pay block absent for a viewer without `compensation:r` · the no-change path costing one click and no scroll · create-time refusal for both unsatisfiable-chain cases · the bell's Pay Equity section appearing with `Review →`, wearing ⚖️ and **not** ❌, and **leaving for a second recipient** after somebody else dispositions · a finding **not** retiring on read · a re-opened finding showing its previous justification · the ladder blockers (occupied level, occupied step) · the import's zero/blank rejection at preview |
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
14. **Bell**: a fourth section, eleven `NOTIF_ICON` entries, suppression of the one-click Approve on money-bearing
    requests, `Take` and `Not now` actions, and retirement wiring for four `related_type`s (§15).

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

---

## 19. Open questions and design gaps

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
| **UXQ10** | Who is shown the **"12 open findings have no recipient"** warning (§14.3 r8), given the people who would fix it are the ones who lost access? | Today I put it on the Feature Access tab and Compensation Settings. If neither is reachable it is invisible | BA + Architect | No |

---

## 20. Conflicts with the SPM's decisions — recorded, complied with, not designed around

*Charter §9.3: surface conflicts, never resolve them silently. Each of these is built as the SPM wrote it unless he
rules otherwise; each states the cost of leaving it.*

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
</content>
</invoke>
