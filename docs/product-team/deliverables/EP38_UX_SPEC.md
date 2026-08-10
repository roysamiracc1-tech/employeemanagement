# EP38 — Employee Lifecycle Workflows · UX / Product Design Spec

> **Owner:** UX / Product Designer · **Date:** 2026-08-09 · **Status:** Ready for build review
> **Covers:** KAN-184 Offboarding (Must) · KAN-185 Transfer (Should) · KAN-183 Onboarding checklist (Should)
>
> This is a build spec. Every string below is final copy, not a placeholder. Every state listed is a state
> engineers must implement; anything not listed here is a gap I should be asked about, not guessed at.
>
> **Reconciled against `EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md` (BA)** — that document is the authority
> on business rules and I have adopted it, including where it overturned my first design (§12 records every
> change and the two places I still disagree). Rule references below are the BA's identifiers (`R…`, `AC-…`,
> `CC-…`) so a reviewer can trace any screen element back to its requirement.
> Related: `ARCHITECT_KICKOFF_AND_TASK_BREAKDOWN.md` · `PRODUCT_ROADMAP_GOALS_EPICS_STORIES.md` §BG4 · D-004.
>
> **Out of scope for this spec** (defined by the BA, no screens designed here): erasure/anonymisation,
> retention configuration, status correction (`RESIGNED ↔ TERMINATED`), rehire (EP38-S4), subject-access
> export. They need their own design pass — see §11 H1.

---

## 1. Scope reviewed

| Input | What I took from it |
|---|---|
| `templates/base.html` | Shell, sidebar gating, flash pattern, shared modal pattern, bell/live update, `escH()` |
| `templates/org/tree.html` | Drag-to-move, the "Request Position Change" modal, prefill API shape, `can_move` gate |
| `templates/org_change/inbox.html` | Approvals inbox, `admin-tabs`, `table-card`, `empty-row`, review modal, diff rendering |
| `templates/admin/org_change_workflow.html` | The repeatable-row config editor I reuse for the checklist template editor |
| `templates/employees/profile.html` | Profile layout, `two-col`, card structure, info-list, direct-reports card |
| `templates/employees/directory.html` | Row/toolbar pattern and empty-state copy for the new row action |
| `templates/admin/register.html` | Numbered `step-badge` cards, form voice, required-field convention |
| `static/css/style.css` | Design tokens, light/dark themes, component classes, and the a11y gaps in §2.4 |
| `app/routes/org_change.py`, `app/services/org_change_service.py` | Sequential engine, `_can_initiate_for`, feature gating |
| `app/auth.py` | `require_feature_access` denial behaviour (flash + redirect to dashboard) |
| `database/schema.sql`, `database/seed_rbac.sql` | `employment_status`/`exit_date`, `users.is_active`, existing feature codes |
| `EP38_REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md` (BA) | All business rules, permissions, statuses, audit content |

---

## 2. Design language these screens must match

### 2.1 Tokens

`--primary #2563eb` · `--bg #f0f4f8` · `--card #fff` · `--border #e2e8f0` · `--text #1e293b`
· `--muted #64748b` · `--radius 12px`, with `[data-theme="dark"]` overrides.
**Never hardcode a hex where a token exists** — every new surface must survive the dark-mode toggle, which
the regression suite checks.

### 2.2 Components I reuse (no new component library)

| Need | Existing class | Source of truth |
|---|---|---|
| Page frame | `.page` + `<h1 style="font-size:1.25rem;font-weight:700">` + muted subtitle | `org_change/inbox.html` |
| Section container | `.card` > `.card-header` > `h2` + `.card-body` | `employees/profile.html` |
| Data list | `.table-card` > `.table-wrap` > `<table>`, empty via `<tr class="empty-row">` | `org_change/inbox.html` |
| Dialog | `.modal-box` > `.modal-header`(`.modal-title`,`.modal-sub`,`.modal-close`) > `.modal-body` > `.modal-footer` | `org/tree.html` |
| Buttons | `.btn` + `.btn-primary` / `.btn-ghost` / `.btn-danger` / `.btn-success`, `.btn-sm` | `style.css` |
| Fields | `.form-group` > `label` + `.form-control` | `admin/register.html` |
| Status pills | `.badge` + `badge-green/amber/red/gray/blue/purple` | `style.css` |
| Tabbed sub-views | `.admin-tabs` > `.admin-tab.active` | `admin/panel.html` |
| Repeating config rows | The `steps-list` row pattern (`Level N` + selects + `✕`) | `admin/org_change_workflow.html` |
| Inline warning banner | amber `#fffbeb` / `#fde68a` box | `admin/org_change_workflow.html` |
| Server flash | `.flash.flash-success` / `.flash-error` | `base.html` |

### 2.3 Copy voice

Observed and continued: sentence-case labels, `*` for required, muted helper text under the field,
placeholder selects worded `— Select location —` / `— No change —`, buttons in Title Case naming the outcome
(`Submit for Approval`, `Save Workflow`), empty states as one factual sentence with the next action in bold.
**No system codes in the UI** — `RESIGNED` renders as **Resigned**, `SOLID_LINE` as **solid-line manager**,
`NOT_STARTED` as **To do**, `N_A` as **Not applicable**.

### 2.4 Accessibility debt in the shell that these screens must NOT inherit

D-004 defers the security sweep but keeps **a11y as a standard on new work**, and the BA restates this as
**CC-18**. These are the shell defects I found; the fixes marked **(ship with EP38)** are small, shared, and
must land with this epic or every EP38 screen re-creates the debt.

| # | Defect (evidence) | Fix | Ship with EP38? |
|---|---|---|---|
| A1 | No global focus indicator. Only `.search-input:focus` / `.form-control:focus` are styled; buttons, links, tabs, modal close have none. Fails **2.4.7 / 2.4.11**. | `:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; border-radius: 4px }`; in dark, `outline-color: #93c5fd`. | **Yes** |
| A2 | Modals (`#reject-modal`, `#move-modal`, `#review-modal`, skill/cert) are `div`s toggled by `style.display` — no `role`, no focus move, no trap, no Esc, no focus restore. Fails **4.1.2 / 2.1.2 / 2.4.3**. | Shared dialog behaviour, §2.5(a). | **Yes** for EP38 dialogs (incl. the shared `#move-modal`, which EP38 gains a second opener onto); other retro-fits stay in S5 |
| A3 | Async results announced only visually (`alert()` in `submitMove()`, silent table swaps). Fails **4.1.3**. | Shared live regions, §2.5(b). | **Yes** |
| A4 | `#94a3b8` as body/empty-state text on white = **2.56:1**. Fails **1.4.3**. (Fine on dark `#1e293b` = 5.71:1.) | Use `var(--muted) #64748b` = **4.76:1**. `#94a3b8` is forbidden for text on new light surfaces. | **Yes** (new screens) |
| A5 | Status colours used as text: `#16a34a` on white = **3.30:1**; `#f59e0b` on white = **2.15:1**; `#dc2626` on `#fef2f2` = **4.43:1** — all fail 4.5:1. | Use the badge-token pairs, which pass: `#15803d` on white = 5.01:1; `#b45309` on `#fffbeb` = 4.84:1; `#b91c1c` on `#fef2f2` = 5.91:1. | **Yes** |
| A6 | Meaning by colour alone (org-change status text, tree legend). Fails **1.4.1**. | Every EP38 status carries a glyph or word as well as colour. | **Yes** |
| A7 | Checkboxes at `15px`; `.btn-sm` computes to ~26px tall. **2.5.8** needs ≥24×24 CSS px. | EP38 checkboxes: 20px box in a ≥24px hit area. Destructive/primary actions ≥44px tall below 768px. | **Yes** |
| A8 | `window.confirm()` / `window.alert()` used for destructive confirmation and success (`cancelReq`, `deleteSkill`, `submitMove`). Native dialogs cannot carry the consequence detail this epic requires. | **No `confirm()` or `alert()` anywhere in EP38.** In-page dialogs only. | **Yes** |
| A9 | No `prefers-reduced-motion`; `.status-dot.loading` pulses indefinitely. | `@media (prefers-reduced-motion: reduce)` reducing animation/transition to ~0. | **Yes** |

### 2.5 Two shared primitives EP38 introduces

**(a) Accessible dialog behaviour** — one implementation, used by every EP38 dialog.

- `<div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="…-title" aria-describedby="…-sub">`.
- Open: store `document.activeElement` as the return target; move focus to `.modal-title` (`tabindex="-1"`)
  so the dialog is named before the first field.
- Trap: `Tab`/`Shift+Tab` cycle inside only; background `inert` (or `aria-hidden` on `#sidebar` +
  `#main-layout`); body scroll locked.
- `Esc` closes and restores focus. Overlay click closes (the established pattern).
- **Close is refused while a mutation is in flight** — footer buttons `disabled`, `×` disabled, `Esc`
  ignored — so a half-committed offboarding can never be dismissed.

**(b) Shared live regions** — added once to `base.html`, below `<main>`:

```html
<div id="live-status" class="sr-only" aria-live="polite" aria-atomic="true"></div>
<div id="live-alert"  class="sr-only" role="alert" aria-atomic="true"></div>
```

`.sr-only { position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0 }`
Loading/progress/success → `#live-status`. Failure/blocker → `#live-alert`.

---

## 3. Permission model (visibility is a permission fact, not a design choice)

Per `CLAUDE.md` and BA **CC-1/CC-2/CC-6/CC-7/CC-8**: `@require_feature_access(...)` on routes,
`has_feature_access(...)` in templates, **no hardcoded role lists, no per-feature sub-flags** — the
Skills-Intelligence `enabled_for_hr` mistake must not recur.

| Surface | Feature code | Action | Notes |
|---|---|---|---|
| Offboard action + dialog (KAN-184) | `employee_lifecycle` | `w` | Page + every API (`AC-184-42`) |
| Lifecycle / audit history card on profile | `audit_log` | `r` | **Separate code** — reading the audit trail is its own permission (BA CC-6). Default PORTAL_ADMIN + HR_ADMIN |
| Non-active employee record view (status, exit date, retention) | `employee_lifecycle` | `r` | `AC-184-06` |
| Transfer entry point + dialog (KAN-185) | `org_change` | `w` | **Existing code. No new gate** (`AC-185-03`, CC-7) |
| Position-change workflow config | `org_structure` | `w` | Unchanged |
| Onboarding: day-one readiness view | `employee_lifecycle` | `r` | `AC-183-05` |
| Onboarding: checklist template editor | `employee_lifecycle` | `w` | `AC-183-01` |
| New-hire checklist card on profile | `employee_lifecycle` | `r` | Plus two business-rule paths, §7.4 |
| Update a task assigned to you | `employee_lifecycle` | — | Business rule, not a feature grant — §7.4 |

Seeded defaults (BA CC-6, not mine to set): `employee_lifecycle` → HR_ADMIN r+w · PORTAL_ADMIN r+w+d ·
SOLID_LINE_MANAGER r. `audit_log` → PORTAL_ADMIN r · HR_ADMIN r. `SYSTEM_ADMIN` needs no row.
**These are a ceiling, not a design assumption** — a tenant may widen them through the Feature Access tab and
every screen must simply work, with no extra check.

### 3.1 What "no access" looks like — for every screen

**Nothing. Not a disabled button, not a greyed nav item, not a tooltip explaining what they're missing.**

- Sidebar item absent; profile and directory-row actions absent; cards absent (never an empty card).
- Direct URL → the existing `require_feature_access` behaviour: flash `You do not have access to that page.`
  and redirect to the dashboard. **Do not build a bespoke 403 page for EP38.**
- API without access → `403`, no state change (`AC-184-43`). If a dialog is open, see §5.8 state E9.
- `SYSTEM_ADMIN` bypasses all of it automatically via `_load_feature_access()` — no special-casing in EP38 code.
- **Read-without-write** is a real, designed state, not an afterthought: an `r`-only holder sees the lifecycle
  screens and the record, and sees **no** action buttons at all.

### 3.2 Business rules layered on top of the feature gate

The flag is necessary, never sufficient — the same principle as `_can_initiate_for`.

1. **Never yourself.** No **Offboard…** on your own profile; API returns `403` (`AC-184-40`, R5.3).
2. **Company scope.** Everything filters `company_id = %s::uuid` (CC-9/CC-10). Cross-company → `403`.
3. **SYSTEM_ADMIN needs a company context** for any mutating lifecycle action (CC-12) — see §5.8 P4.
4. **Transfer keeps the org-change initiator rule** (`AC-185-02`): subject's current solid-line manager, or
   HR/Portal/System admin. An individual can never initiate their own move, through any entry point.
5. **Employees with `company_id IS NULL`** never appear on a tenant's lifecycle screens (CC-13).

---

## 4. Journey map — the HR reality this is designed for

| Stage | User goal | Today | Pain | What this design does |
|---|---|---|---|---|
| Discover | "Ravi left on Friday" | Nothing exists | Departures live in email; the portal stays wrong | One **Offboard…** action where the person is |
| Start | Record the facts once | — | Re-entering the same facts in several places | One dialog; everything else derived |
| Understand | "What will this break?" | — | **A manager's departure silently orphans their team and stalls approvals** | Step 2 shows the blast radius *and makes you resolve it* |
| Commit | Do it without fear | — | Irreversible act with no statement of consequence | Step 3 restates the consequence in plain English; the button is named after the act |
| Confirm | Know it worked | — | Silent success, no record | Success panel listing exactly what changed |
| Follow-up | Prove it months later | — | No audit trail at all | Lifecycle history card, permanently on the profile |

**Primary persona:** HR Administrator / Ops — interrupted, acting for someone else, on a laptop.
**Secondary:** Manager — transfer and their own reports' onboarding tasks, often on a phone.
**Never:** the employee themselves. EP38 has no self-service offboarding surface.

---

## 5. KAN-184 — Offboarding *(the only Must in the epic)*

### 5.0 The consequence-handling decisions

This revokes a real person's ability to sign in, removes them from the directory, org tree, search and every
picker, cancels their pending leave, and **cannot be reversed by anyone, including SYSTEM_ADMIN**
(`AC-184-26`). Seven decisions carry that weight:

1. **The action is where the person is.** You offboard from Ravi's profile or his directory row, with his
   name, employee number, manager and team in front of you. No bulk offboard (BA OQ-8).
2. **Orphaned reports are resolved in the flow, not warned about.** Each solid-line report must be given a
   successor before submit is possible (`AC-184-08`). A warning you can scroll past is not a control.
3. **The flow blocks rather than completing something broken.** If a leave approval or an approval step
   naming the leaver cannot be re-pointed, or the leaver is the last PORTAL_ADMIN, the flow stops and says
   what to fix (`AC-184-18/20/39`). It never half-completes.
4. **Nothing is cancelled silently.** Every leave request that will be cancelled is listed — type, dates,
   working days, status — before the actor confirms (`AC-184-16`).
5. **If we can't compute the impact, we don't let you commit** (§5.8 E4). Confirming a consequence we
   couldn't measure is not confirmation.
6. **The commit button is named after the act** — `Offboard Ravi Sharma` — never `Confirm`, `OK` or `Save`.
7. **The audit entry is a product surface, not a log file.** It renders on the profile, in plain language,
   naming the actor and their role at the time, because "who did this and why" is the question asked three
   months later.

**The date rule that shapes everything else (BA R5.6 / `AC-184-25`):** offboarding is **immediate**. The last
working day must be today or in the past; a future date is rejected, and scheduled offboarding is explicitly
out of scope. So there is **no pending state and no undo anywhere in this flow** — which is precisely why
steps 2 and 3 are as heavy as they are. (I argued for a scheduled, cancellable window; the BA ruled it out
for this cycle. I have recorded the residual risk in §12 D1 rather than designing against the requirement.)

### 5.1 Entry points

**(a) Employee profile header** — an action cluster in `.profile-header-info`, right-aligned ≥768px,
stacked full-width below the stats on smaller viewports. Shared with KAN-185's **Transfer…**, so there is one
place for "do something to this person's employment".

```
┌───────────────────────────────────────────────────────────────────────────┐
│  [RS]   Ravi Sharma                             [ Transfer… ] [ Offboard… ]│
│         Senior Engineer                                                    │
│         📍 Bengaluru · Technology · Platform · Permanent                    │
│         12 Skills    4 Certifications    5 Years                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Offboard…** — `.btn.btn-danger.btn-sm`, `type="button"`, `aria-haspopup="dialog"`. The ellipsis is the
established signal that a dialog follows and stops it reading as a one-click act. Rendered only when **all**
of: `has_feature_access('employee_lifecycle','w')` · `not is_own` · same company (or SYSTEM_ADMIN with a
company selected) · `employment_status == 'ACTIVE'`.

**(b) Directory row** (required by `AC-184-01`). Because the directory is a 400-row scanning surface where a
mis-click is easy, the action is **not** a bare button in the row. It is a per-row overflow menu:

- Trigger: `⋯` icon button, `aria-label="Actions for Ravi Sharma"`, `aria-haspopup="menu"`,
  `aria-expanded`, 24×24 minimum.
- Menu: `role="menu"` with `role="menuitem"` entries — `View profile` · `Transfer…` · `Offboard…`
  (the last in `#b91c1c`, and last in the order so it is never the default landing item).
- Keyboard: `Enter`/`Space`/`↓` opens and focuses the first item; `↑`/`↓` move; `Esc` closes and returns
  focus to the trigger; `Tab` closes.
- Items are filtered by the same permission + business rules as (a); a row for yourself shows only
  `View profile`. An empty menu means no `⋯` button at all.

Both entry points open the identical dialog.

### 5.2 The dialog — three steps, one dialog, 600px

Behaviour per §2.5(a). Header persists across steps:

```
┌──────────────────────────────────────────────────────────────┐
│ Offboard Ravi Sharma                                      ×  │  ← .modal-title  #ob-title
│ EMP-0142 · Senior Engineer · reports to Marcus Lee           │  ← .modal-sub    #ob-sub
├──────────────────────────────────────────────────────────────┤
│ ●───────○───────○   Exit details · What happens · Confirm    │  ← aria-hidden="true"
│                                                              │
│  <h3 tabindex="-1"> step heading </h3>                       │
│  … step body …                                               │
├──────────────────────────────────────────────────────────────┤
│ [ Cancel ]                             [ Back ]  [ Continue ]│
└──────────────────────────────────────────────────────────────┘
```

The subject's identity is in the dialog subtitle at every step (`AC-184-01`) — an interrupted user must never
have to guess who they are about to offboard. The step indicator is decorative; the authoritative
announcement is the step `<h3>` plus `Step 2 of 3, What happens` written to `#live-status`.

#### Step 1 — Exit details

| Field | Control | Label | Helper / options | Rule |
|---|---|---|---|---|
| Departure type | radios in `<fieldset>` | `Departure type *` | `Resignation — they chose to leave` (→`RESIGNED`) · `Termination — the company ended the employment` (→`TERMINATED`) | Required, **no default** (R5.2) |
| Last working day | `<input type="date">`, `max=today`, default today | `Last working day *` | `Their access is revoked as soon as you confirm. This date can't be in the future.` | Required; ≥ join date; ≤ today (`AC-184-25`) |
| Reason | `<select>` | `Reason *` | Company's configured reason categories; placeholder `— Select a reason —` | Required (`AC-184-02`, R4.1 #10) |
| Note | `<textarea rows="2">` | `Note (optional)` | `Recorded in the lifecycle history. Keep it factual — anyone who can read this employee's lifecycle history can read it.` | Optional |

- The radio group's label is a real `<legend>`, not a floating `<div>`. No default is deliberate:
  pre-selecting "Resignation" puts words in HR's mouth on a record with legal weight.
- **Back-dated confirmation** (`AC-184-25`): if the chosen date is more than 30 days ago, an amber inline
  block appears immediately below the date field, with focus **not** stolen:
  > ⚠ `That's 47 days ago. Their access has been live since then.`
  > `☐ Yes, 12 June 2026 is their last working day.`
  `Continue` is blocked until it is ticked. The message states the *consequence* of the back-date, not just
  the arithmetic — that access was live in the interim is the fact HR needs to notice.
- The note's visibility is stated next to the field. Do not add a "private note" toggle in EP38 (§11 Q3).
- **Reason categories are company-configured** — see §7.2(c) for where they are edited.

#### Step 2 — What happens

Rendered from `GET /api/lifecycle/offboard/impact?employee_id=…`. Four zones, in this order, because the
order is the reading order of consequence: *blockers → people → work → what the system will do.*

**Zone 1 — Blockers** (shown only when present; red `#fef2f2` / `#fecaca` / text `#b91c1c`, `role="alert"`).
When any blocker is present, **`Continue` is disabled** and the zone is the first thing focus reaches.

| Blocker | Copy | Rule |
|---|---|---|
| No re-point target for leave approvals | `Offboarding is blocked. 3 leave requests are waiting for Ravi's approval and there's no one to move them to — your company has no active HR Admin. Appoint an HR Admin, then try again.` + the list of affected requests | `AC-184-18`, R2.8 |
| No re-point target for approval steps | `Offboarding is blocked. Ravi is a named approver on 2 position changes and there's no one to move them to. Appoint an HR Admin, then try again.` + the list | `AC-184-20`, R2.14 |
| Last active PORTAL_ADMIN | `Offboarding is blocked. Ravi is the only active Portal Admin in your company. Give someone else the Portal Admin role first, or your company will be locked out of its own settings.` | `AC-184-39` |

The last one states the *reason* for the rule. "You can't do this" without "here's what would break" is how
users conclude the software is broken.

**Zone 2 — Ravi's people.**

- **Solid-line reports (mandatory).** `Ravi is the solid-line manager of 4 people. Each of them needs a new
  manager before you can continue.` Then:
  - A bulk control first: `Move all 4 to  [ — Select a manager — ▾ ]  [ Apply to all ]` (R1.7).
  - Then a per-report list, one row each: avatar · name · job title · `[ manager select ]`. Rows are
    prefilled by the bulk control and individually overridable, because a departing manager's team is
    routinely split.
  - Selects list only active employees of the same company, excluding Ravi (R1.1, CC-11).
  - **`AC-184-10` case:** if the successor chosen for a report is themselves one of Ravi's reports, an inline
    muted line appears under that row: `Priya reports to Ravi too, so she'll move to Ravi's manager,
    Marcus Lee, instead of to herself.` — state the rule where the choice is made, not in a footnote.
  - **`AC-184-11` case:** if Ravi has no manager and the successor is one of his reports:
    `Ravi has no manager, so Priya will become a top-level manager in the org tree.` (amber, `role="status"`).
- **Dotted-line reports (optional, R1.5).** `Ravi is the dotted-line manager of 2 people. A new dotted-line
  manager is optional.` with the same bulk + per-row control and, when left empty, a muted line:
  `Left empty: these 2 dotted-line links will simply end. It won't change anyone's reporting line in the org tree.`
- **No reports:** one line — `Ravi has no direct reports.` Never an empty zone.

**Zone 3 — Work in flight.** Each item is a disclosure row: a one-line summary that expands to the detail.
Summaries are always visible; detail is one keystroke away (progressive disclosure), except the cancellation
list, which is expanded by default because `AC-184-16` requires it to be *seen*.

| Item | Summary copy | Detail |
|---|---|---|
| Leave that will be cancelled | `2 of Ravi's leave requests will be cancelled.` **(expanded by default)** | Table: type · dates · working days · current status (`AC-184-16`) |
| Leave that is kept | `1 approved leave request started before his last day and will be kept.` | Same table shape (R2.3) |
| Leave approvals moving | `3 leave requests waiting for Ravi's approval will move to Marcus Lee.` | Requester · dates · new approver (R2.7) |
| Position changes cancelled | `1 position change for Ravi will be cancelled. No move will be applied.` | The request summary (R2.11) |
| Approval steps moving | `Ravi is a named approver on 2 position changes. Those steps will move to Anna Weiss.` | Request · step · new approver (R2.13) |
| Onboarding tasks moving | `5 onboarding tasks assigned to Ravi will move to Marcus Lee.` | Task · new hire · new assignee (R2.18) |
| Ravi's own onboarding | `Ravi's own 3 incomplete onboarding tasks will be closed as Not applicable.` | Task list (R2.18) |
| **Warning** — last role holder | ⚠ `Ravi is the last active HR Admin in your company. 4 position changes need an HR Admin approval and will stall until someone else has that role.` **Non-blocking** (`AC-184-21`, R2.15) | — |
| Nothing in flight | `Nothing else is waiting on Ravi.` | — |

**Zone 4 — What the portal will do** (static, always last, `<ul>` with `✓` glyphs, `badge-green` styling):

> - Set Ravi's status to **Resigned**, with a last working day of **12 June 2026**
> - Revoke his portal access — he will no longer be able to sign in
> - Remove his portal roles
> - Remove him from the employee directory, org tree, search, dashboards and every picker
> - End his reporting lines
> - **Keep his record, history and past approvals** for reporting and audit

The last line is load-bearing and must not be dropped. HR's fear is that offboarding deletes the person; it
does not, and saying so is what makes the action feel safe to take correctly.

**Optional asset line** (the BA scopes asset tracking out beyond "an optional checklist line", §6.8). One
compact row at the end of zone 4:

> `Assets returned (optional)`  `☐ Laptop  ☐ Phone  ☐ Access badge  ☐ Company card  ☐ Keys`
> `Anything left unticked is recorded in the lifecycle history as outstanding. It does not block offboarding.`

Not blocking by design: HR routinely offboards before the laptop comes back, and a blocking checklist just
gets filled in dishonestly.

#### Step 3 — Confirm

No inputs but the acknowledgement. Everything is a plain-language restatement assembled from the user's own
answers — no new information appears here, so there is nothing to discover at the last second:

> **You are about to offboard Ravi Sharma (EMP-0142).**
>
> His last working day was **12 June 2026**. When you confirm, the portal will revoke his access immediately,
> remove his roles, set his status to **Resigned**, and remove him from the directory, org tree, search and
> dashboards. His record and history stay in the portal for reporting and audit.
>
> **4 solid-line reports** move to **Marcus Lee** (Priya Nair moves to Marcus Lee instead of to herself).
> **2 dotted-line links** end.
> **2 leave requests** are cancelled · **3 leave approvals** move to Marcus Lee · **1 position change** is
> cancelled · **2 approval steps** move to Anna Weiss · **5 onboarding tasks** move to Marcus Lee.
> **2 asset items** are recorded as outstanding: Laptop, Access badge.
>
> ⚠ **This cannot be undone.** Nobody can set Ravi back to active — bringing him back needs the rehire
> process, which isn't available yet.
>
> ☐ I understand this revokes Ravi Sharma's access and cannot be undone.
>
>                                    [ Cancel ]  [ Back ]  [ **Offboard Ravi Sharma** ]

Notes on the copy:
- Zero-count clauses are **omitted**, never rendered as "0 leave requests" — a wall of zeroes trains people
  to skip the paragraph that matters.
- "cannot be undone" is literal here and names the missing route honestly (`AC-184-26`), rather than implying
  a support ticket could fix it.
- **Termination** swaps the status word to **Terminated** throughout.
- The commit button is `.btn.btn-danger`, `disabled` until the acknowledgement is ticked, with
  `aria-describedby` pointing at the acknowledgement label so a screen-reader user is told *why*. This is the
  one place in EP38 where a disabled control is right: the gate is a single visible checkbox two lines above.
- **No type-to-confirm here.** Typing the employee number is reserved for erasure (`AC-184-33`), which is
  genuinely destructive of data. Using the same friction for both would flatten the difference between
  "they left" and "their data is gone".

### 5.3 Success state

The dialog body is replaced in place — it does not auto-close, because the actor needs a beat to read what
happened. Focus moves to the success heading (`tabindex="-1"`).

> ✓ **Ravi Sharma has been offboarded.**
> His access was revoked at 14:32 on 9 August 2026.
> 4 reports now report to Marcus Lee · 2 leave requests cancelled · 3 leave approvals moved to Marcus Lee ·
> 2 approval steps moved to Anna Weiss · 5 onboarding tasks moved to Marcus Lee.
> `[ View lifecycle history ]  [ Done ]`

`#live-status` receives the first two sentences. `Done` closes and reloads the underlying page, so the
profile banner and history are correct — a stale profile behind a success message is how someone offboards
the same person twice.

### 5.4 Profile after offboarding

- **Status banner** under `.profile-header`, grey `#f1f5f9` / text `#475569`, `role="status"`:
  `Left the company on 12 June 2026 · Resigned. Portal access revoked.`
  For `employee_lifecycle` read holders, a second muted line (`AC-184-31`):
  `Record kept until 12 June 2033 (retention: 7 years) · 2,498 days remaining.`
- Header badges gain `<span class="badge badge-gray">Former employee</span>`.
- The **Offboard…** and **Transfer…** actions are gone (not disabled).
- Directory / org tree / search / dashboard exclusion needs no UI work — the existing
  `employment_status='ACTIVE'` filters deliver it (`AC-184-05`) — but the regression suites must assert it.

### 5.5 Lifecycle history card — the visible audit trail

New `.card` in the **left** profile column, below *Reporting Structure*. Renders for
`has_feature_access('audit_log')`; absent otherwise. One correlated offboarding renders as **one entry with
its detail nested**, not eleven scattered rows — the BA's correlation id (R4.1 #11) exists precisely so this
reads as one story.

```
┌─ Lifecycle History ─────────────────────────────────────────────┐
│  ●  9 Aug 2026, 14:32 · Offboarded                               │
│     by Priya Nair (HR Admin, at the time)                        │
│     Resignation · last working day 12 Jun 2026                   │
│     Reason: Moved to another company                             │
│     "Standard notice served."                                    │
│     ▸ 11 related changes                                         │
│        Status: Active → Resigned                                 │
│        Portal access: Enabled → Revoked                          │
│        Roles removed: Solid Line Manager, Employee               │
│        4 reports reassigned to Marcus Lee                        │
│        2 leave requests cancelled · 3 approvals moved            │
│        Assets outstanding: Laptop, Access badge                  │
│                                                                  │
│  ●  4 Mar 2024, 09:10 · Position change applied                  │
│     approved by Anna Weiss (final approver)                      │
│     Business unit: Operations → Technology                       │
│                                                                  │
│  ●  1 Feb 2021 · Joined                                          │
└──────────────────────────────────────────────────────────────────┘
```

- Semantics: `<ol>` newest-first; each entry an `<li>`; timestamps in `<time datetime="…">`; the "11 related
  changes" disclosure is a `<button aria-expanded>` controlling the detail list. Not a `<table>` — this is a
  narrative and must stack on mobile.
- Every entry states **when · what · who · from what to what · why**. The actor's name **and their roles as
  at the time** are shown (R4.1 #3) — "(HR Admin, at the time)" is deliberate, because roles change and an
  audit trail that silently uses today's roles is misleading.
- **A `FAILED` attempt is an entry too** (R4.1 #12): `9 Aug 2026, 14:29 · Offboarding attempted and failed`
  / `by Priya Nair (HR Admin, at the time)` / `Blocked: no active HR Admin to take over 3 leave approvals.
  Nothing was changed.` Hiding failed attempts would make the trail a success log, not an audit trail.
- Free-text (reasons, notes) renders via `textContent` / `escH()`. D-004 defers the `innerHTML` sweep, so
  **EP38 must not add a new sink** (CC-19).
- **Empty:** `No lifecycle events recorded yet.` **Loading:** three skeleton lines. **Error:**
  `We couldn't load the lifecycle history.` + `[ Try again ]`, with the rest of the profile unaffected.
  **Partial:** an actor whose record is gone renders as `by a removed user` plus the retained role snapshot,
  never a blank.

### 5.6 Notifications (`AC-184-07`)

Delivered through the existing `user_notifications` bell — no new surface. Copy:

- To the former manager: `Ravi Sharma has left the company. He no longer reports to you.`
- To each reassigned report: `Your manager has changed. You now report to Marcus Lee.`
  — deliberately does **not** say "because Ravi left"; that is the departing person's news to share, and the
  portal should not break it. The manager change is the fact the employee needs.
- To each new approver: `3 leave requests moved to you for approval because Ravi Sharma has left.`
- **To the leaver: nothing.** Their account is deactivated and unreachable, and notifying someone of their
  own offboarding through a portal bell would be a serious product mistake.

### 5.7 Small screens

<768px: the dialog becomes a full-height sheet (`inset:0; border-radius:0`) with a sticky footer and 44px
buttons. Step 2's four zones keep their order; the per-report reassignment list becomes stacked cards
(name above its select) rather than a two-column row; detail tables scroll horizontally inside
`.table-wrap` while the page itself never does.

### 5.8 Every state — offboarding

| # | State | Trigger | What the user sees |
|---|---|---|---|
| L1 | **Loading — dialog open** | Opened | Header + step 1 render at once (data is already on the page). No spinner |
| L2 | **Loading — impact** | Entering step 2 | Skeleton rows per zone; `Continue` disabled; `#live-status` → `Checking what this offboarding affects…` |
| L3 | **Loading — committing** | Commit pressed | Button → `Offboarding…`, disabled; Cancel/Back/×/Esc disabled; `#live-status` → `Offboarding Ravi Sharma…` |
| E1 | **Empty — no reason categories configured** | Company has none | Reason select shows `— No reasons configured —`, disabled, with helper `Add departure reasons in Onboarding & Offboarding settings before offboarding anyone.` + link for `w` holders. **Continue blocked** — the reason is mandatory, so proceeding is impossible, and saying so up front beats failing at submit |
| E2 | **Empty — nothing in flight** | All zeros | Zone 3 shows one line: `Nothing else is waiting on Ravi.` |
| E3 | **Partial — no join date** | `join_date IS NULL` | The ≥ join-date check is skipped; helper adds `Join date not recorded — the last working day can't be checked against it.` |
| E4 | **Error — impact fetch failed** | Non-2xx / network | Zones replaced by `⚠ We couldn't check what this offboarding affects.` / `Offboarding is blocked until we can check — nothing has been changed.` + `[ Try again ]`. **`Continue` stays disabled**; `#live-alert` gets sentence one |
| E5 | **Blocked — unresolvable re-point / last Portal Admin** | Impact returns a blocker | Zone 1 (§5.2); `Continue` disabled; the fix is named. `#live-alert` gets the blocker sentence |
| E6 | **Error — validation** | Continue/commit with invalid input | Inline under the field in `#b91c1c`, `role="alert"`, `aria-invalid="true"`, focus to the first invalid control. Strings in §5.9 |
| E7 | **Error — commit failed (rollback)** | Server error / `AC-184-36` | `We couldn't complete the offboarding, so nothing has been changed — it failed at: moving leave approvals. Try again, and if it keeps failing contact your system administrator.` Buttons re-enabled; all entered data preserved. **Naming the failing step is required** — CC-15 guarantees the rollback, and telling the user which step failed is what lets them fix the cause |
| E8 | **Conflict — already offboarded / concurrent actor** | `409` (`AC-184-37/38`) | `Ravi Sharma has already been offboarded. Refresh this page to see his current status.` + `[ Refresh ]`; commit button removed (retrying cannot help) |
| E9 | **Permission lost mid-flight** | `403` on commit | `Your access to offboarding changed while you were working. Nothing has been saved.` + `[ Close ]` only |
| E10 | **Not found / bad id** | `404`/`400` (`AC-184-41`) | `That employee no longer exists. Refresh the page.` |
| P1 | **No `employee_lifecycle:w`** | — | No entry point anywhere; direct URL → standard flash + dashboard redirect |
| P2 | **`r` without `w`** | `AC-184-43` | Record, status, retention and (with `audit_log`) history all visible; **no** action buttons |
| P3 | **Own profile / own row** | `is_own` | No **Offboard…**; API → `You can't offboard yourself.` |
| P4 | **SYSTEM_ADMIN, no company selected** | CC-12 | Entry point visible but opening the dialog shows a single panel: `Choose a company first. Offboarding changes one company's data, so the portal needs to know which one.` + `[ Close ]`. (Mirrors the existing `Select a company first.` pattern) |
| P5 | **Other company / `company_id IS NULL` subject** | CC-10/CC-13 | Not rendered; API → `That employee is not in your company.` |
| D1 | **Disabled — commit** | Acknowledgement unticked | `Offboard Ravi Sharma` disabled + `aria-describedby` → the acknowledgement |
| D2 | **Disabled — Continue** | Unassigned reports · unticked back-date confirm · blocker · failed impact | Disabled, with the reason visible on screen in every case — never a disabled button whose cause is off-screen |
| S1 | **Success** | Commit succeeds | §5.3 |
| I1 | **Integration failure — notifications** | Bell/email send fails | Offboarding still succeeds (it is committed and irreversible; rolling it back for a failed notification would be worse). Success panel adds: `We couldn't notify Marcus Lee about his new reports. The offboarding itself is complete.` and the failure is in the history |

### 5.9 Copy — validation and errors (final strings)

| Situation | Message |
|---|---|
| No departure type | `Choose whether this is a resignation or a termination.` |
| No last working day | `Choose a last working day.` |
| Date in the future | `The last working day can't be in the future — offboarding takes effect as soon as you confirm.` |
| Date before join date | `The last working day can't be before Ravi's join date (1 February 2021).` |
| Back-dated >30 days, unconfirmed | `Confirm that 12 June 2026 is their last working day.` |
| No reason selected | `Choose a reason for the departure.` |
| Report without a successor | `Choose a new manager for Priya Nair.` |
| Bulk successor not chosen | `Choose a manager to move all 4 reports to, or set them one by one.` |
| Successor is the subject | `Ravi can't be his own reports' new manager. Choose someone else.` |
| Successor is being offboarded | `Marcus Lee has already been offboarded. Choose someone else.` |
| Acknowledgement unticked | `Tick the box to confirm you understand.` |
| Impact fetch failed | `We couldn't check what this offboarding affects.` / `Offboarding is blocked until we can check — nothing has been changed.` |
| Commit failed | `We couldn't complete the offboarding, so nothing has been changed — it failed at: <step>. Try again, and if it keeps failing contact your system administrator.` |
| Already offboarded | `Ravi Sharma has already been offboarded. Refresh this page to see his current status.` |
| Permission lost | `Your access to offboarding changed while you were working. Nothing has been saved.` |
| Self-offboard | `You can't offboard yourself.` |
| Cross-company | `That employee is not in your company.` |
| No company context | `Choose a company first. Offboarding changes one company's data, so the portal needs to know which one.` |

### 5.10 Accessibility — offboarding

- **Keyboard path:** `Tab` to **Offboard…** (or `⋯` → menu → `Offboard…`) → `Enter` opens → focus on the
  dialog title → `Tab`: departure-type radios (arrows within the group, `Tab` exits) → last working day →
  back-date confirm when present → reason → note → `Cancel` → `Continue`.
  Step 2: focus to the step heading; if a blocker exists, focus goes to the blocker (`role="alert"`) instead.
  Then `Tab`: bulk successor select → `Apply to all` → each report's select in list order → dotted-line
  controls → each disclosure `<button>` (Enter/Space toggles) → asset checkboxes → `Cancel` `Back` `Continue`.
  Step 3: focus to heading → acknowledgement → `Cancel` `Back` `Offboard Ravi Sharma`.
- **Focus order** is DOM order; no positive `tabindex` anywhere.
- **Focus trap / Esc / restore** per §2.5(a); Esc ignored during L3. On close, focus returns to the opener; if
  the opener no longer exists (successful offboarding), focus goes to the new status banner
  (`tabindex="-1"`).
- **Draft preservation:** closing the dialog (Esc, ×, overlay, Cancel) keeps entered values in memory for the
  session. Reopening for the same employee restores them, with `Draft restored — you can carry on where you
  left off.` in `#live-status` and as muted helper text. HR gets interrupted; losing a twelve-row
  reassignment list to a stray Esc is not acceptable.
- **ARIA:** `role="dialog" aria-modal="true"` + `aria-labelledby`/`aria-describedby`; a `<h3 tabindex="-1">`
  per step; radio groups in `<fieldset>`/`<legend>`; the per-report list is a `<ul>` and each select's
  accessible name includes the report's name (`New manager for Priya Nair`); disclosures use
  `aria-expanded` + `aria-controls`; blockers `role="alert"`; the org-tree-root and dotted-line notes
  `role="status"`; every inline error `role="alert"` and wired via `aria-describedby` with `aria-invalid`.
- **Live regions:** `#live-status` — step changes, impact loading, draft restore, committing, success.
  `#live-alert` — blockers, impact failure, commit failure, conflict, permission loss.
- **Focus indicators:** A1. The danger button's ring uses `#b91c1c` at 2px/2px offset so it reads against its
  own pale background.
- **Targets:** all controls ≥24×24; below 768px, footer buttons, menu items and the acknowledgement row
  ≥44px.
- **Contrast:** danger `#b91c1c` on `#fef2f2` (5.91:1) · amber `#b45309` on `#fffbeb` (4.84:1) · success
  `#15803d` on white (5.01:1) · helper `var(--muted)` (4.76:1). Verified in both themes.
- **Never colour alone:** every blocker, warning and status row leads with `⚠` / `✓` plus its word.
- **Reflow:** dialog `max-width:600px; width:calc(100vw - 32px); max-height:calc(100vh - 32px)`, body
  `overflow-y:auto` — usable at 400% zoom and 320px with no horizontal page scroll.

---

## 6. KAN-185 — Transfer

### 6.0 The core decision: this is not a second system

`AC-185-01/06` require a second **entry point** to `org_change_service.create_request`, indistinguishable
downstream. The failure mode to avoid is a "Transfers" area that looks almost-but-not-quite like Position
Changes. So:

- **No new page. No new nav item. No new feature code. No new inbox. No new status vocabulary.**
- Transfer reuses the **same dialog component** as the org-tree drag-and-drop, the **same** endpoint, the
  **same** inbox, the **same** sequential engine, the **same** `diffInline`/`diffHtml` summaries.
- The word "Transfer" appears **only on the entry point** — the verb HR uses. The moment the dialog opens the
  user is in *Request Position Change*, because that is what they are creating and what they will search for
  later.

### 6.1 Entry points

1. **Employee profile** — `[ Transfer… ]`, `.btn.btn-ghost.btn-sm`, beside **Offboard…** (§5.1a).
2. **Directory row** — inside the same `⋯` menu as §5.1(b), as `Transfer…` (`AC-185-01`).
3. **Org tree drag-and-drop** — unchanged; still the fastest path for someone looking at the org's shape.

All three are gated by `has_feature_access('org_change','w')` **and** `_can_initiate_for` **and**
`employment_status == 'ACTIVE'` **and** `not is_own`.

### 6.2 The dialog

The existing `#move-modal`, with five changes:

| Element | Drag-and-drop today | Via Transfer… |
|---|---|---|
| `.modal-title` | `Request Position Change` | `Request Position Change` *(unchanged — that is the point)* |
| `.modal-sub` | `Move Ravi Sharma → under Marcus Lee` | `Transfer · Ravi Sharma · EMP-0142` |
| Prefill | Target's placement (from the drop) | **Ravi's current placement**, so every select starts at "no change" and only what moves is changed |
| "Currently" row | absent | **New** (below) |
| Effective date | absent | **New, required** (`AC-185-07`) |
| Approval-chain line | absent | **New** (below) |

**"Currently" row** — read-only `<dl>` in the established `#f8fafc`/`#e2e8f0` inset box:

> **Currently:** Marcus Lee · Technology · Platform · Bengaluru

**Effective date** — `<input type="date">`, label `Effective from *`, default today, helper:
`When the move takes effect once it's approved. It can be today or a future date.`
Validation: not before today unless the user has `HR_ADMIN`/`PORTAL_ADMIN`/`SYSTEM_ADMIN`
(back-dating an assignment is an admin correction, not a manager action — §11 Q5 confirms the boundary).

**Approval-chain line**, inside the existing notice box, fetched with the prefill:

> `This change is not applied immediately — it is submitted for approval.`
> `It needs 2 approvals: HR Admin, then Anna Weiss. Nothing changes until the last one approves.`

Variants: `It needs 1 approval: HR Admin.` (single step, and the unconfigured-workflow fallback).
This is the single most valuable addition — today a requester has no idea what they have set in motion.

Fields otherwise unchanged in order and label: *New reporting manager* · *Business unit* / *Functional unit*
(side by side, FU filtered by BU) · *Location* · *Reason \**. Non-reason selects offer `— No change —` first.
Footer: `[ Cancel ]` `[ Submit for Approval ]`.

### 6.3 Success — replacing the `alert()`

`submitMove()` currently ends in `alert('Position change submitted for approval.')`. Replaced everywhere (A8)
with an in-dialog panel:

> ✓ **Position change submitted for approval.**
> Ravi Sharma's move is with **HR Admin** (approval 1 of 2), effective 1 September 2026 once approved.
> You can follow it in Position Changes.
> `[ View in Position Changes ]  [ Done ]`

`#live-status` gets the first two sentences. The link goes to `/org-change` → *My Requests*.

### 6.4 Every state — transfer

| # | State | What the user sees |
|---|---|---|
| L1 | **Loading — prefill** | Selects show one disabled `Loading…` option; submit disabled; `#live-status` → `Loading Ravi's current position…` |
| L2 | **Loading — submitting** | `Submitting…`, disabled (existing behaviour kept) |
| E1 | **Empty — no org units** | `— None configured —`, disabled, helper `No business units have been set up for your company yet.` A manager-only move still works |
| E2 | **Empty — no eligible managers** | `— No other active employees —`, disabled |
| E3 | **Error — prefill failed** | `#mv-error`: `We couldn't load Ravi's current position. Close this and try again.` Submit disabled |
| E4 | **Error — nothing changed** | Existing string kept: `Pick at least one change (manager, unit or location).` |
| E5 | **Error — no reason** | Existing string kept: `Please give a reason for the move.` |
| E6 | **Error — no effective date** | `Choose when this move takes effect.` |
| E7 | **Error — back-dated by a manager** | `The effective date can't be in the past. Ask HR if this needs back-dating.` |
| E8 | **Error — self-manager** | Server string surfaced: `An employee cannot report to themselves.` |
| E9 | **Error — not permitted** | Server string surfaced: `You can only request moves for your own reports (or as HR/Portal admin).` |
| E10 | **Conflict — pending request exists** | `AC-185-08`: `Ravi Sharma already has a position change waiting for approval. That one has to be decided or cancelled first.` + `[ View it ]`; submit hidden |
| E11 | **Conflict — subject offboarded** | `Ravi Sharma has left the company. You can't transfer a former employee.` + `[ Close ]` |
| E12 | **Error — submit failed** | `We couldn't submit this change. Nothing has been sent for approval. Try again.` |
| P1 | **No `org_change:w`** | No entry point; drag gated by `can_move`; API → 403 |
| P2 | **Not their report** | Entry point absent for a manager outside the line; API enforces `_can_initiate_for` |
| P3 | **Own profile** | Entry point absent. An employee can never initiate their own move through any route |
| D1 | **Disabled — FU select** | `— Select a business unit first —` (matches the register form) |
| PD1 | **Partial — no current manager** | "Currently:" reads `No manager · Technology · Platform · Bengaluru` |
| PD2 | **Partial — workflow unconfigured** | Chain line falls back to `It needs 1 approval: HR Admin.` — never blank |
| S1 | **Success** | §6.3 |
| I1 | **Integration failure — approver notification** | Request still created; panel adds `We couldn't notify the approver, but the request is in their queue.` |

### 6.5 Accessibility — transfer

- **Keyboard path:** `Tab` to **Transfer…** (or via the `⋯` menu) → `Enter` → focus on the dialog title →
  `Tab`: manager → BU → FU → location → effective date → reason → `Cancel` → `Submit for Approval`.
- Focus trap, Esc, focus restore per §2.5(a) — this is the retro-fit of `#move-modal`, and it ships with
  EP38 because EP38 adds a second opener onto the same component.
- **Drag-and-drop needs a keyboard equivalent (2.1.1 / 2.5.7).** Today the only way to raise a position
  change from the tree is a mouse drag. **Transfer…** *is* that equivalent, and the org-tree legend must say
  so: `Keyboard: open a person's profile and choose Transfer… to request the same change.`
- **ARIA:** `aria-haspopup="dialog"`; the "Currently" row is a `<dl>`; the approval-chain notice is
  `role="status"` so it is announced when it arrives after the dialog opens; `#mv-error` becomes
  `role="alert"` and is referenced by the offending field's `aria-describedby`.
- **Live regions:** `#live-status` for prefill-loaded and submitted; `#live-alert` for failures.
- **Contrast:** error text moves from `#dc2626` (4.43:1 — fails) to `#b91c1c` (5.91:1).

---

## 7. KAN-183 — Onboarding checklist

Three surfaces: a **day-one readiness view** (the daily job), a **template editor** (rare configuration), and
a **checklist card** on the new hire's profile.

### 7.1 Information architecture

One page, `/onboarding`, with `.admin-tabs` — mirroring the admin-panel pattern:

| Tab | Content | Gate |
|---|---|---|
| **Day-one readiness** (default) | Incomplete mandatory tasks across all in-progress hires (`AC-183-05`) | `employee_lifecycle` `r` |
| **Checklist template** | The task template editor (`AC-183-01`) | `employee_lifecycle` `w` — tab absent without it |
| **Settings** | Departure reason categories (`AC-184-02`) | `employee_lifecycle` `w` — tab absent without it |

Nav: Administration section, after *Change Workflow*, label **Onboarding**, shown when
`has_feature_access('employee_lifecycle')`. Readiness is first because it is used weekly; the template is
used twice a year. A user with `r` only sees a single-tab page — and in that case the tab strip is not
rendered at all, because a one-tab tab strip is noise.

The departure-reason list lives here rather than on a fourth page: it is the same administrator, configuring
the same lifecycle, and a page per list is how settings sprawl starts.

### 7.2 Screens

**(a) Day-one readiness** — `.table-card`, sorted by join date ascending (`AC-183-05`):

| New hire | Joins | Task | Owner | Due | Status |
|---|---|---|---|---|---|
| Amara Osei | in 3 days · 12 Aug | Issue laptop and accessories | IT Admin | 10 Aug | ⚠ Overdue |
| Amara Osei | in 3 days · 12 Aug | Sign employment contract | Amara Osei | 12 Aug | To do |
| Tom Rieder | in 9 days · 18 Aug | Set up payroll record | Priya Nair | 16 Aug | In progress |

- Only **incomplete mandatory** tasks (`AC-183-05`). A muted line above the table says so, so nobody reads it
  as the full picture: `Mandatory tasks that aren't done yet, for everyone joining soon.`
- Filter row (reusing `.toolbar`): `All hires ▾` / `Overdue only` toggle.
- The hire's name links to their profile; the row's status cell is the same status control as §7.3 for users
  permitted to change it.
- Toolbar count: `7 tasks · 3 overdue · across 4 hires`.

**(b) Checklist template editor** — deliberately mirrors `admin/org_change_workflow.html`: same page width,
same single-card row list, same save affordances, because it is the same kind of job.

```
Onboarding Checklist Template
Tasks every new hire gets. They're created automatically when an employee is added,
and appear on the new hire's profile.
Changes apply to employees added from now on. Checklists already in progress are not changed.

┌ ⚠ No checklist configured yet — new hires are not getting an onboarding checklist. ┐  (when empty)

┌────────────────────────────────────────────────────────────────────────────────┐
│ ⠿ 1 │ [ Issue laptop and accessories       ] │ [ Role ▾ ][ IT Admin ▾ ]         │
│      │ [ description, optional             ] │ Due [ 3 ] days [ before ▾ ] joining │
│      │                                        │ ☑ Mandatory      ✕ Remove       │
│ ⠿ 2 │ [ Sign employment contract           ] │ [ The new hire ▾ ]  Due [0] …    │
│ ⠿ 3 │ [ Introduce to the team              ] │ [ Their manager ▾ ] Due [1] after │
│                                                                                  │
│  + Add task                                                                      │
│  [ Save Checklist ]   ✓ Saved                                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

| Field | Control | Notes |
|---|---|---|
| Order | drag handle `⠿` | Keyboard: `↑`/`↓` on the focused handle; announced `Moved to position 2 of 5` |
| Name | text, required, ≤150 | `AC-183-01`; duplicate names rejected (`AC-183-16`) |
| Description | text, optional | `AC-183-01` |
| Assigned to | select: `The new hire` (`NEW_HIRE`) · `Their manager` (`HIRING_MANAGER`) · `Role` · `A specific person` | Role/person reveals a second select — the same progressive pattern as the workflow editor |
| Role / person | second select | **Company's own roles only** (`company_id = %s::uuid`, never `OR company_id IS NULL`) (`AC-183-19`, CC-4) |
| Due | number + `before`/`after` + `joining` | Negative offsets are expressed as `before`, so nobody types a minus sign. `0` renders as `On their first day` |
| Mandatory | checkbox | Mandatory tasks drive the readiness view |
| Active | `Deactivate` in the row menu | Templates are **deactivated, not deleted** (`AC-183-01`); deactivated rows collapse to a muted line with `Reactivate` |

`Remove` is offered only for a template that has never been instantiated; otherwise the control is
`Deactivate`, with helper `Deactivating stops new hires getting this task. Checklists already created keep it.`

**(c) Settings — departure reasons** — the same row editor, one text field per row, plus Active/Deactivate.
Helper: `Reasons an employee can leave. Shown when someone is offboarded, and recorded in the lifecycle
history.` Empty state: `No departure reasons yet — offboarding needs at least one.` (This is a blocking
dependency for §5.8 E1, so the empty state says why it matters.)

### 7.3 New-hire checklist card (employee profile)

New `.card` in the **right** profile column, above *Skills*.

```
┌─ Onboarding ──────────────────── 3 of 7 done · 1 of 4 mandatory ─┐
│  ███████░░░░░░░░░░░░░░░  43%                                      │
│                                                                   │
│  ✓  Sign employment contract              Amara Osei              │
│     Done · 1 Aug 2026 by Amara Osei                               │
│  ✓  Issue laptop and accessories          IT Admin                │
│     Done · 2 Aug 2026 by Sam Okafor                               │
│  ⏳ Set up payroll record                 Priya Nair    [ Status ▾ ]│
│     In progress · due 10 Aug 2026                                 │
│  ○  Introduce to the team                 Marcus Lee    [ Status ▾ ]│
│     Due 12 Aug 2026                                               │
│  ⚠  Complete security training            Amara Osei    [ Status ▾ ]│
│     Overdue — was due 5 Aug 2026                      Mandatory   │
│  ⊘  Order security badge                  Unassigned    [ Status ▾ ]│
│     Not applicable — "Remote-only hire"                           │
└───────────────────────────────────────────────────────────────────┘
```

- **Statuses** (`AC-183-03`), each with a glyph and a word, never colour alone:
  `○ To do` (`NOT_STARTED`) · `⏳ In progress` (`IN_PROGRESS`) · `✓ Done` (`DONE`) ·
  `⛔ Blocked` (`BLOCKED`, reason required) · `⊘ Not applicable` (`N_A`, reason required).
- **The control is a select, not a checkbox** — five states cannot be a checkbox, and a checkbox that
  sometimes opens a reason prompt is worse than an honest select. Accessible name:
  `Status for Complete security training`.
- Choosing `Blocked` or `Not applicable` reveals a required one-line reason input inline, with
  `Save` / `Cancel`; the reason then renders in quotes under the task. Validation:
  `Say why this task is blocked.` / `Say why this task doesn't apply.`
- **Optimistic update with rollback:** the row changes at once; `#live-status` →
  `Set up payroll record marked in progress.`; on failure it reverts and `#live-alert` →
  `We couldn't update that task. It's still marked as to do.`
- **Overdue** = incomplete and past due: `⚠` + the word `Overdue` + `#b45309`.
- **`unassigned-fallback`** (`AC-183-09`): owner renders as `Portal Admin (no IT Admin found)` with helper
  `No one held the IT Admin role when this checklist was created, so it went to the Portal Admin.` — the
  fallback is stated, not silently absorbed.
- **No join date** (`AC-183-06`): due cells read `Due date pending`, with one card-level muted line:
  `Due dates need a join date on this employee's record.`
- Progress: `role="progressbar"` with `aria-valuenow/min/max` and `aria-label="Onboarding progress"`; the
  `3 of 7 done · 1 of 4 mandatory` text is the accessible truth and the bar merely supports it.

### 7.4 Who sees and does what (`AC-183-04`, §5.5 of the BA spec)

| Viewer | Sees the card | Can change status |
|---|---|---|
| `employee_lifecycle` w holder (HR/Portal admin) | Yes | Any task |
| `employee_lifecycle` r holder | Yes | Only tasks assigned to them |
| The hire's solid-line manager | Yes (own reports only) | Only tasks assigned to them |
| The new hire | **Own checklist only** | Only their own `NEW_HIRE` tasks |
| Anyone else | **No card at all** | — |

Where a viewer may see but not change a task, the status renders as a **static glyph + word** — not a
disabled select, which would advertise a control they cannot use.

### 7.5 Instantiation and the "Add New Employee" tie-in

On success at `/admin/register-user` (and after bulk import), the existing flash gains a second sentence:

- `Ravi Sharma has been added. A 7-task onboarding checklist has been created on his profile.`
- No template: `Ravi Sharma has been added. No onboarding checklist was created — no template is configured.`
  plus, for `w` holders only, ` Set one up →`.
- **Instantiation failed** (`AC-183-14`): `Ravi Sharma has been added, but his onboarding checklist couldn't
  be created.` + `[ Create it now ]`. Rendered as `flash-error` **beside a successfully created employee** —
  the hire is never lost to a checklist failure, and the retry is one click.
- Bulk import (`AC-183-12`): the import summary gains one line —
  `Onboarding checklists created for 24 of 24 new employees.` / `…for 22 of 24. 2 failed — [ Retry ]`.

Nothing about the Add New Employee form itself changes. Adding checklist configuration to a form that is
already three cards long would damage the primary flow for a decision that belongs in settings.

### 7.6 Every state — onboarding

**Template editor**

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | Three skeleton rows; `Save Checklist` disabled |
| E1 | Empty — no template | Amber `No checklist configured yet — new hires are not getting an onboarding checklist.` + one blank starter row (matching `if (!steps.length) addStep()`) |
| E2 | Empty — company has no roles | `Role` option present; its select reads `— No roles defined for your company —`, disabled, helper `Create roles in Admin Panel → Company Roles first.` **Never falls back to global template roles** (`AC-183-11`, CC-4) |
| E3 | Empty — no employees | `A specific person` select reads `— No active employees —`, disabled |
| V1–V5 | Validation | `Task 2: give the task a name.` · `Task 2: choose who this is assigned to.` · `Task 2: pick a role.` / `pick a person.` · `Task 4 has the same name as task 2. Give them different names so assignees can tell them apart.` · `Add at least one task, or the checklist does nothing.` |
| V6 | Validation — offset | `Task 3: the due offset must be a whole number of days.` |
| E4 | Error — load | `We couldn't load the checklist template.` + `[ Try again ]` |
| E5 | Error — save | `We couldn't save the checklist. Your changes are still here — try again.` (unsaved state preserved) |
| P1 | Permission | Tab absent; direct URL → flash + dashboard redirect |
| P2 | SYSTEM_ADMIN, no company | Existing pattern reused: `Select a company first.` |
| D1 | Disabled | `Saving…` while in flight |
| S1 | Success | `✓ Saved` in `#15803d`; `#live-status` → `Checklist template saved. 5 tasks.` |

**Readiness view**

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | `<tr class="empty-row"><td colspan="6">Loading…</td></tr>` (existing pattern) |
| E1 | Empty — nothing outstanding | `Nothing outstanding — every mandatory task for upcoming hires is done.` |
| E2 | Empty — no hires in progress | `No one is currently onboarding.` |
| E3 | Empty — no template configured | `No onboarding checklist configured, so there's nothing to track.` + `Set one up →` for `w` holders |
| E4 | Error | `We couldn't load the readiness list.` + `[ Try again ]` |
| PD1 | Partial — hires without join dates | Shown at the end of the list under a sub-heading `No join date yet` with `Due date pending` (`AC-183-06`) |
| P1 | Permission | Page absent |

**Checklist card**

| # | State | What the user sees |
|---|---|---|
| L1 | Loading | Four skeleton rows; `aria-busy="true"` on the progress bar |
| E1 | Empty — no checklist for this hire | **Card not rendered** — an employee predating the feature must not get a confusing empty card |
| E2 | Empty — template had no active tasks | `This hire's checklist has no tasks.` + `Edit the template →` for `w` holders |
| E3 | All done | `7 of 7 done`, bar full, `✓ Onboarding complete.` in `#15803d` |
| PD1 | Assignee has left | Owner reads `Unassigned` + `The person this was assigned to has left. Reassign it or complete it yourself.` |
| PD2 | Unassigned fallback | §7.3 |
| PD3 | No join date | §7.3 |
| E4 | Error — load | `We couldn't load the onboarding checklist.` + `[ Try again ]`; rest of the profile unaffected |
| E5 | Error — status change | Row reverts + `We couldn't update that task. It's still marked as to do.` |
| E6 | Conflict — already done | `AC-183-15`: `Someone has already marked that task done.` + `[ Refresh ]` |
| E7 | Validation — missing reason | `Say why this task is blocked.` / `Say why this task doesn't apply.` |
| P1 | Read-only viewer | Static glyph + word; no control in the tab order |
| P2 | No access | Card absent |
| S1 | Success | Row shows `Done · 9 Aug 2026 by Priya Nair`; progress and live region update |
| S2 | Hire offboarded mid-onboarding | `AC-183-13`: incomplete tasks render `⊘ Not applicable — "Employee offboarded"`, card header adds `Onboarding closed — this employee has left.` |
| I1 | Integration failure — notification | Task still changes; muted `Notification not sent.` on the affected row |

### 7.7 Accessibility — onboarding screens

- **Template editor keyboard path:** `Tab` reaches each row's drag handle (`role="button"`,
  `aria-label="Reorder task 2: Sign employment contract"`, `↑`/`↓` reorder), then name, description,
  assignee, conditional role/person, due number, before/after, Mandatory, row menu. Then `+ Add task`, then
  `Save Checklist`. Adding moves focus to the new row's name and announces `Task 6 added.`; removing
  announces `Task 3 removed. 5 tasks left.` and moves focus to the next row's name (or `+ Add task`).
- **No drag-only interaction anywhere** (2.1.1) — the handle is fully keyboard-operable.
- **Row semantics:** the editor is a `<ul>`, each row an `<li>` with an `aria-label` naming the task, so a
  screen-reader user knows which row they are in. The leading number is `aria-hidden` and duplicated in the
  row label.
- **Checklist card keyboard path:** `Tab` reaches each status select in list order; choosing Blocked/N_A
  moves focus to the revealed reason input, which is `aria-required="true"`.
- **Tabs:** `.admin-tabs` become a real tablist — `role="tablist"` / `role="tab"` with `aria-selected` and
  `aria-controls`, panels `role="tabpanel"`, arrow-key navigation, one tab stop for the strip. This fixes the
  existing pattern for the new page; retro-fitting the admin panel's tabs stays in the S5 sweep.
- **Targets:** row controls ≥24×24; below 768px, editor rows stack and every control is ≥44px.
- **Contrast:** `✓ Saved` moves from `#16a34a` (3.30:1 — fails) to `#15803d` (5.01:1); overdue uses
  `#b45309` on `#fffbeb` (4.84:1); the progress bar fill has a 3:1 boundary against its track (1.4.11).
- **Reduced motion:** progress transitions and skeleton shimmer suppressed under A9.

---

## 8. Cross-cutting requirements

| Area | Requirement |
|---|---|
| **Dark mode** | Every new surface uses tokens. The dialogs, lifecycle card, status banner, checklist card, readiness table and editor must all be checked in dark mode — `tests/ui/test_browser.py` already asserts dark mode and must gain these screens |
| **Mobile ≤767px** | Dialogs become full-height sheets with sticky 44px footers; profile actions go full-width; the reassignment list and editor rows stack; the readiness table becomes stacked cards |
| **Reflow / zoom** | No horizontal page scrolling at 320px or 400% zoom on any EP38 surface (1.4.10). Wide tables scroll inside `.table-wrap`, never the page |
| **XSS posture** | D-004 defers the `innerHTML` sweep (KAN-150/173) but **EP38 must not add new sinks** (CC-19). Reasons, notes, task names and asset names render via `textContent` or `escH()` — they are user-authored strings appearing in an audit trail |
| **Company scoping** | Every list, select and query filters `company_id = %s::uuid`. Company roles never `OR company_id IS NULL` |
| **PII in errors** | User-facing errors name the employee (the actor is looking at them); **logs** carry id and employee number only (CC-17) |
| **Regression coverage** | New checks: entry-point visibility by permission and by `r`-vs-`w` · blocked offboarding states · reassignment required · leave-cancellation list shown before confirm · offboarded employee absent from directory/org tree/search · lifecycle entry rendered · transfer entry point producing an `org_change` request in the inbox · concurrent-request 409 · template save/load · task status transitions · readiness view. Owned by the UAT Lead (Charter §5b) |
| **Analytics** | Offboardings started vs completed, with the step they were abandoned at (drop-off at step 2 signals the impact panel is frightening people for the wrong reasons) · blocked-offboarding counts by blocker type (a high "no HR Admin" rate is a tenant-configuration problem, not a UX one) · transfers by entry point · checklist completion at 30 days · overdue mandatory tasks per company |

---

## 9. Analytics-free summary of what an engineer must build

1. Two shared primitives (§2.5) + the nine shell a11y fixes marked "ship with EP38" (§2.4).
2. Profile action cluster + directory row `⋯` menu (§5.1, §6.1).
3. Offboarding dialog: 3 steps, 4 zones in step 2, impact endpoint, commit endpoint (§5.2).
4. Post-offboarding profile banner + lifecycle history card (§5.4, §5.5).
5. Transfer entry points onto the existing `#move-modal` + 5 dialog changes + success panel (§6).
6. `/onboarding` page with 3 tabs: readiness, template editor, departure reasons (§7.1, §7.2).
7. New-hire checklist card with 5-state status control (§7.3).
8. Flash/summary changes on Add New Employee and bulk import (§7.5).

---

## 10. UX acceptance criteria (testable)

**KAN-184 Offboarding**
1. Entry points render only for `employee_lifecycle:w`, never on your own record, never cross-company, never
   for a non-ACTIVE employee; an `r`-only holder sees the record and history but no action.
2. A user without the feature sees nothing and is redirected with the standard flash on direct URL access.
3. The subject's name and employee number are visible at every step of the dialog.
4. A future last working day is rejected in the UI with the §5.9 string; a date >30 days ago requires the
   explicit confirmation before `Continue` is enabled.
5. Every solid-line report is listed individually with a successor control; `Continue` and submit are
   blocked until each has one; dotted-line successors are optional and the consequence of leaving them empty
   is stated.
6. Choosing a successor who is one of the subject's own reports shows the "moves to the grandparent"
   explanation inline, at the row where the choice was made.
7. Every leave request that will be cancelled is listed with type, dates, working days and status, expanded
   by default, before confirmation.
8. Each blocker (no re-point target, last Portal Admin) disables `Continue`, states the fix, and is
   announced through `#live-alert`.
9. The last-active-role-holder warning appears and does **not** block.
10. If the impact call fails, `Continue` is blocked with the §5.8 E4 copy.
11. Step 3 states in plain English: who, the date, that access is revoked immediately, that roles are
    removed, that they leave the directory/org tree/search/dashboards, that the record is kept, where each
    group of reports goes, what leave and approvals move or cancel, what assets are outstanding, and that it
    cannot be undone.
12. The commit button reads `Offboard <First> <Last>` and is disabled until the acknowledgement is ticked.
13. A commit failure names the failing step and confirms nothing changed; entered data survives.
14. On success the profile shows the status banner, the retention line for `employee_lifecycle:r` holders,
    and a lifecycle entry with timestamp, actor name **and roles as at the time**, departure type, reason,
    field-level before/after detail, and reassignment outcomes.
15. A failed attempt also appears in the lifecycle history.
16. The dialog traps focus, closes on Esc except while committing, restores focus, and announces every step
    change, blocker, failure and success through the live regions.
17. Re-opening after an accidental close restores the entered draft.

**KAN-185 Transfer**
18. Transfer creates an `org_change` request via the existing endpoint, visible in the existing inbox, with
    no new page, nav item, feature code or status vocabulary, and is indistinguishable from a drag-initiated
    request.
19. The dialog states the employee's current placement, the effective date, and how many approvals are
    needed and who the first approver is — before submission.
20. Selects prefill to current placement and default to `— No change —`.
21. A second concurrent request for the same subject is refused with the §6.4 E10 copy and a link to the
    existing one.
22. No employee can initiate their own move through any entry point.
23. Success is an in-dialog panel with a link to Position Changes — **no `alert()`**.
24. Every path is completable by keyboard alone, and the org-tree legend names the keyboard equivalent to
    drag-and-drop.

**KAN-183 Onboarding checklist**
25. The template editor lists only the company's own roles; a company with none shows an empty state, never
    global template roles.
26. Templates are deactivated rather than deleted once instantiated, and the page states that changes do not
    affect checklists already in progress.
27. Adding an employee reports how many tasks were created; with no template it says none was created; if
    instantiation fails the employee is still created and a one-click retry is offered.
28. The readiness view lists incomplete mandatory tasks across upcoming hires, sorted by join date, and says
    that is what it is listing.
29. The checklist card shows task, assignee, due date and one of the five statuses, each with a glyph and a
    word; Blocked and Not applicable require a reason.
30. Status is changeable by `employee_lifecycle:w` holders and by a task's assignee (including the new hire
    for their own tasks); everyone else sees a static glyph, not a disabled control.
31. Rows are reorderable by keyboard as well as pointer, with every reorder announced.

**All three**
32. Every screen renders correctly in light and dark themes at 320px, 768px and 1440px, and at 400% zoom,
    with no horizontal page scrolling.
33. No `alert()` or `confirm()` anywhere in EP38.
34. All new text meets 4.5:1 (3:1 for large text and UI boundaries) in both themes; no meaning is carried by
    colour alone.
35. Every interactive control has a visible `:focus-visible` indicator.

---

## 11. Open questions and design gaps

The BA's spec closed my original Q1 (audit content), Q2 (feature codes), Q4 (in-flight work), Q10 (task
statuses) and Q11 (effective date). What remains:

| # | Question | Why it matters | Owner | Blocking? |
|---|---|---|---|---|
| **H1** | **Erasure, retention configuration and status correction have requirements (`AC-184-27/31/32/33/34`) but no screens.** Erasure in particular is described as "type the employee number to confirm" — that is a UI contract with no UI. | These are the most destructive actions in the product and they are currently un-designed. Building them from the AC text alone will produce an inconsistent, riskier confirmation pattern than the one in §5.2 | UX (me) — needs SPM tasking | **Yes, before those stories are built** — not before KAN-184 |
| Q1 | Are **departure reason categories** seeded with defaults for a new company, or does every tenant start empty? §5.8 E1 blocks offboarding entirely when the list is empty | A tenant that cannot offboard anyone on day one is a bad first-run experience; a sensible seeded list removes the blocker | BA | No, but affects first-run |
| Q2 | Should the **asset checklist** be company-configurable, or is the fixed five acceptable? BA §6.8 scopes asset tracking out "beyond an optional checklist line" | If configurable, §7.2(c) gains a third list; if not, the fixed list is final copy | BA | No |
| Q3 | Do **termination reasons/notes** need a restricted-visibility variant (HR-only)? I designed one level and told the user about it | Termination notes carry sensitive assertions; GDPR data-minimisation is live | BA + DPO | No — but recommend legal/DPO review |
| Q4 | The BA's `AC-183-04` gives the hire's **solid-line manager** read access to the checklist. Should the manager also see the readiness view for their own reports, or is that HR-only? | Changes whether §7.1's readiness tab is admin-only or manager-facing, which changes its default filter | BA | No |
| Q5 | Confirm that **back-dating a transfer's effective date** is HR/admin-only, as I specified in §6.2 | `AC-185-07` allows "default today, may be future" but is silent on the past; back-dating rewrites assignment history | BA | No |
| Q6 | `AC-184-25` requires "explicit confirmation" for a date >30 days ago. I designed a checkbox. Confirm that is sufficient rather than a typed date re-entry | Determines the friction level of a common correction case | BA | No |

---

## 12. Reconciliation with the BA spec — what changed, and where I still disagree

**Adopted, overturning my first draft:**

| # | My original design | BA rule | Result |
|---|---|---|---|
| C1 | Future-dated, cancellable "Scheduled offboarding" with an undo window | `AC-184-25`, R5.6 — future dates rejected; scheduling out of scope | **Removed.** Offboarding is immediate; no pending state, no undo. See D1 below |
| C2 | "Leave reports without a manager" as an explicit option | `AC-184-08` — submit blocked until every solid-line report has a successor | **Removed** for solid-line; retained for **dotted-line** only, where R1.5 makes it optional |
| C3 | Bulk reassignment only | R1.7 — per-report override | **Both**: bulk-set-all plus a per-report list |
| C4 | Note optional, no reason field | `AC-184-02` — reason category mandatory, from a company-configurable list | Reason select added, plus the settings surface to configure it (§7.2c) |
| C5 | In-flight work shown as information only | §4.2 — the flow acts, lists, and blocks | Step 2 rebuilt into four zones with blockers, mandatory controls and a cancellation list |
| C6 | Lifecycle history gated by `employee_lifecycle` | CC-6 — `audit_log` is a separate feature code | Re-gated to `audit_log:r` |
| C7 | Profile as the only entry point | `AC-184-01`, `AC-185-01` — profile **or directory row** | Directory row added as a `⋯` menu rather than an inline button, to keep a mis-click expensive |
| C8 | Binary To do / Done tasks | `AC-183-03` — five states, two needing reasons | Status select with five states and inline reason capture |
| C9 | No transfer effective date | `AC-185-07` | Effective-date field added, with a back-dating rule flagged as Q5 |
| C10 | No day-one readiness screen | `AC-183-05` | Added as the default tab of `/onboarding` |

**Where I still disagree — recorded, not designed around** (Charter §9.3: surface conflicts, don't resolve
them silently):

- **D1 — No undo, no scheduling, on the most destructive action in the product.** *Observation:* offboarding
  is immediate and irreversible by anyone, and rehire (the only route back) is Could/P3 and not in this
  cycle. *Evidence:* `AC-184-25`, `AC-184-26`, BA §6.8, roadmap BG4. *Impact:* the first mis-typed offboarding
  is unrecoverable, and HR's real-world pattern is to process a resignation *before* the last day, which this
  design cannot express — so people will either offboard early (revoking access while the person is still
  working) or forget. *Recommendation:* either bring a minimal scheduled-with-cancel window into KAN-184, or
  raise rehire's priority so a recovery path exists in the same release. *Expected outcome:* the irreversible
  action stops being the only option. *Confidence: Medium-High. Evidence class: Known (the rules), Assumption
  (the behavioural consequence).* **For the SPM to decide, not me.**
- **D2 — The directory-row entry point.** I complied with `AC-184-01`, but a state-changing, irreversible
  action reachable from a 400-row scanning table is a mis-click surface. I have mitigated it with an overflow
  menu, destructive-last ordering, and the full three-step dialog. If the SPM wants the risk lower, the
  cheapest change is to drop the directory-row offboard action and keep only *Transfer…* there.
  *Confidence: Medium.*

---

## 13. Summary verdict

**RAG: Green for design readiness, Amber for the epic.** The three screens are specified to build level,
reconciled against the BA's rules, and the a11y standard is specified up front so the S5 sweep stays small
as D-004 intends. Amber for the epic because (a) **H1** — erasure, retention and status correction have
requirements but no screens, and they are more destructive than anything designed here, and (b) **D1** — an
irreversible offboarding with no scheduling and no recovery path in the same release is a product risk the
SPM should accept explicitly rather than inherit.
