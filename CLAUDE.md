# CLAUDE.md — Project Rules

> **Product & engineering governance (pointer, not a rule change):** work is run by two connected persona orgs
> in `docs/product-team/` — a Product org (SPM + specialists) and an Engineering org (Senior Architect +
> engineers + DevOps). Produced artifacts live in `docs/product-team/deliverables/`: the SPM kickoff, the
> product roadmap, and the Architect's technical task breakdown. The engineering invariants below are the
> guardrails all that work must obey — they always win.

## DOCUMENTATION LIVES IN GIT — never in Jira or Confluence

**Atlassian was retired on 8 August 2026.** Jira and Confluence are not used on this project.
When the user asks to update business documentation, technical documentation, the product roadmap,
the backlog, or any project-management documentation:

1. **Edit the markdown in this repo.** Never call the Atlassian/Jira/Confluence MCP tools to create
   or update project documentation, and never link to `*.atlassian.net` — those URLs are dead.
2. **Find the right file** using the routing table in
   [`docs/project-management/README.md`](docs/project-management/README.md). The backlog is
   `docs/project-management/BACKLOG.md`; do not recreate `docs/JIRA_EPICS_AND_STORIES.md`.
3. **Commit, then push** (branch first if on `main`). Keep a doc change and the code change it
   describes in the same commit so they cannot drift.
4. `docs/archive/confluence-export/` holds frozen historical snapshots. **Read-only** — never edit
   them and never cite them as current documentation.
5. `KAN-###` are local story IDs, not Jira issues. Keep them plain text, never hyperlinked.
6. **Every persona owns documentation.** When acting as any role from `docs/product-team/`, keep that
   role's documents current as part of the work — see Team Charter §5b for the owner-per-file map.
   Documentation updates land in the same commit as the change they describe.

## DEMO READINESS GATE — run before demoing ANYTHING to the user

**Before showing the user any feature — a flow test, a walkthrough, a "here's how it works" —
run the Demo Readiness Gate in
[`docs/project-management/DEMO_READINESS_GATE.md`](docs/project-management/DEMO_READINESS_GATE.md)
and record the verdict.** It exists because on 9 Aug 2026 a demo was rehearsed only along the path
that had been built, and the stakeholder's first two questions — "where is the rejection?" and "why
does the bell not show this?" — both landed on real defects with every automated suite green.

The rules, in short:

1. **Demo the feature the way a user meets it, not the way it was built.** Start where they start.
2. **Every actor, both outcomes.** Walk it as the initiator, every approval level, the subject, and
   somebody who must NOT see it. Show the rejection/cancel/guard path, not only the happy path.
3. **Check the feedback surfaces** — notification bell (does the item appear *with its decision
   controls*?), badge count, icons, empty states, and **retirement** once decided, for **every**
   eligible approver. This is D4's blind-spot list; it is where all three 9 Aug defects lived.
4. **Green suites are not a rehearsal.** Also confirm the suites actually assert the behaviour being
   demoed — asserting that the bell *opens* proved nothing about what was inside it.
5. **Any unchecked box is NO-GO.** If a known defect is carried into a demo anyway, say so out loud
   at the start. Discovering it live in front of the user is a process failure.
6. **Name concurrent writers.** If anything else may be writing to the demo database, pick
   uncontended demo data and say so first.

The gate is owned by the SPM and delegated per persona (D1–D9) — see the table in the gate document.

## FLOW TESTS — How to run any "flow test" the user asks for

**⚠️ NON-NEGOTIABLE. This applies the moment the user's request contains the words "flow test" in
ANY form** — "flow test", "regression flow test", "do a flow test", "test the flow", "run the flow",
"show me the flow". It does NOT matter if the word "regression" or a feature name is attached. A flow
test is ALWAYS a **visible Chrome/Chromium window + spoken audio narration**, driven live in front of
the user. It is **NEVER** a headless run, NEVER a silent `pytest`/curl/API check, and NEVER just the
`tests/ui/*` headless suites. If you are about to run something headless in response to a "flow test"
request, STOP — you are making the exact mistake this rule exists to prevent.

Follow this exactly:

1. **Make sure the app is running** on `http://localhost:8000` (`python run.py`).
2. **Drive a VISIBLE Chrome/Chromium window** with Playwright (`headless=False`, a moderate `slow_mo` so it's watchable). Bring the window to the foreground (`page.bring_to_front()` + `osascript -e 'tell application "Chromium" to activate'`) so the user can actually see it. Note: Playwright launches the light-blue **Chromium** app, not the user's normal Google Chrome.
3. **Speak every step aloud** using the macOS `say` command as it happens, so the user hears what is being done and why (login, each page, each action, the outcome).
4. **Actually perform the real steps** in the UI — click the real buttons, fill the real forms, log in/out as the real users involved. Take a screenshot at each step for the record.
5. **When finished, say aloud "The flow test is complete"** (and print it), then **STOP and wait for the user to approve.** Do NOT declare the flow test successful on your own.
6. **The flow test counts as SUCCESSFUL only after the user explicitly approves** ("the flow is correct" / "approved"). Until then it is pending, no matter how clean the run looked.

**"Regression flow test" specifically** = the visible + audio browser walkthrough above, covering the
regression-critical flows (login, dashboard, directory, org tree, vacation request round-trip,
position-change approval, key admin pages). The headless `tests/ui/*` suites are a SEPARATE internal
check you may ALSO run — but they never substitute for the visible + audio session the user asked for.

Reusable drivers live under the session scratchpad (e.g. `roundtrip.py`, `flow.py`) — model new flow tests on them.


## REGRESSION FLOW TEST — run before confirming any substantial change

For any non-trivial change (feature, route, template, DB, or refactor), run the **regression flow test**
before confirming, so nothing silently breaks. This is in addition to `pytest`. Steps:

1. Ensure the app is running on `http://localhost:8000` (`python run.py`) against the seeded dev DB.
2. Run both headless browser regression suites and confirm **0 failures**:
   - `python tests/ui/test_browser.py` — 93 checks across login, admin, org tree, search, vacation
     calendar, bell, dark mode, directory, Portal-Admin scoping, restricted access, mobile, redirects,
     the Transfer… entry point (KAN-185), and **bell content** — that an approval awaiting you is
     actionable there, wears the right icon, and leaves once decided (DEF-001/2/3).
   - `python tests/ui/test_vacation_workflow.py` — 39 checks: the full submit → approve → reject →
     history → dashboard vacation workflow. It resets the leave it created on start-up, so it is
     safe to re-run — do not "fix" an `Exceeds annual limit` failure by relaxing the limit.
3. Report the pass counts (e.g. "browser 93/93, vacation 39/39") alongside the `pytest` result.
4. If a regression suite fails, **investigate whether it's a real regression or a stale assertion** —
   drive the specific flow in a browser and check console/page errors before deciding. Fix real
   regressions; correct genuinely stale assertions (and say which). Never delete a check to go green.

These suites are standalone Playwright scripts (headless), NOT part of the `pytest`/CI run — run them
directly. Keep them current: when a change alters a flow they cover, update the corresponding checks.


## BEFORE CONFIRMING ANY CHANGE TO THE USER

**Run `python -m pytest -q` and verify 0 failures, run the REGRESSION FLOW TEST above (0 failures), then manually check these 5 things:**

1. Does the UI show data ONLY scoped to the correct company / role? (No global template roles bleeding in.)
2. Does a company with NO custom roles show an empty state — not global roles like EMPLOYEE, DEPARTMENT_HEAD?
3. Does `role_feature_access` and `company_role_feature_access` only query `company_id = specific UUID` — never `OR company_id IS NULL` when showing a company's own roles?
4. Does every feature route use `@require_feature_access(...)` — never a hardcoded `@require_roles(...)` list?
5. Does SYSTEM_ADMIN bypass all feature checks automatically?

**Only confirm to the user AFTER pytest, the regression flow test, and all 5 checks pass. No exceptions.**



## Access Control — NEVER hardcode role checks for feature visibility

**Access to features is controlled entirely by two tables:**

- `role_feature_access` — global ceiling, set by SYSTEM_ADMIN via Roles & Permissions
- `company_role_feature_access` — per-company overrides, set by PORTAL_ADMIN via Feature Access tab

**The rules:**

1. Route guards use `@require_feature_access('feature_code')` — never `@require_roles(...)` for feature pages.
2. Nav links use `{% if has_feature_access('feature_code') %}` — never hardcoded `has_role(...)` for feature links.
3. Do NOT add extra per-feature role checks inside routes (e.g. `_si_enabled_for_hr`, `enabled_for_hr` checks). These bypass the permission system and block roles that have been correctly granted access.
4. SYSTEM_ADMIN always has full access — handled automatically in `_load_feature_access()`.
5. If a role has access in `role_feature_access` and is not overridden by `company_role_feature_access`, they get access. Period.

**Adding a new feature — all FOUR places, or it does not exist outside your machine:**
- Add it to `portal_features` in `setup_db.py` **and** a migration SQL under `database/migrations/`
- **Add the same row to `database/seed_rbac.sql`.** ⚠️ Non-obvious and the one that gets missed:
  a fresh database is built from `schema.sql` (structure only) + `seed_rbac.sql`, and **migrations
  are never replayed** (TECHNICAL_DOCUMENTATION §10). A feature row is DATA, so a schema-only dump
  cannot carry it — put it only in the migration and CI gets the table but not the feature, while
  every developer machine passes because the migration was run there by hand. This broke CI on
  9 Aug 2026 (`audit_log`). `TestFeatureRegistryHasNoDrift` in `tests/test_regression.py` now
  fails when a migration registers a feature the seed does not.
- Seed default `role_feature_access` rows for the roles that should have it by default —
  again in **both** the migration and `seed_rbac.sql`
- Use `@require_feature_access('your_feature_code')` on routes
- Use `{% if has_feature_access('your_feature_code') %}` in nav

**Verifying a DB change the way CI does** — the dev DB has migrations applied by hand and will hide
seed drift. Build a throwaway database the way CI builds one and run against that:
```bash
dropdb --if-exists employee_ci_local && createdb employee_ci_local
psql -q -d employee_ci_local -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
psql -q -d employee_ci_local -v ON_ERROR_STOP=1 -f database/schema.sql
psql -q -d employee_ci_local -v ON_ERROR_STOP=1 -f database/seed_rbac.sql
PGDATABASE=employee_ci_local python -m pytest -q --ignore=tests/ui
```

**Company roles are ONLY roles with `company_id = that company's UUID`.** Never query `OR company_id IS NULL` when showing a company's roles — that pulls in global template roles (EMPLOYEE, DEPARTMENT_HEAD, etc.) which the company has NOT created. Every query that lists or shows roles for a specific company must filter `WHERE company_id = %s::uuid` only.

## Position Change Workflow (org_change feature)

Drag-and-drop employee moves (BU / functional unit / location / manager) go through a company-configurable, **sequential** multi-level approval chain before anything is applied. Key invariants — do not weaken:

1. Pages/APIs are gated by `@require_feature_access('org_change', ...)`; the admin config page by `@require_feature_access('org_structure','w')`. Never hardcode role lists on these routes.
2. **An individual employee can NEVER initiate their own move.** On top of the feature gate, `create_request` requires the initiator to be the subject's current `SOLID_LINE` manager **or** hold `HR_ADMIN`/`PORTAL_ADMIN`/`SYSTEM_ADMIN`. Keep this business-rule check (`_can_initiate_for`) — the feature flag alone is not sufficient.
3. Approvals are **sequential**: level N+1 is only reached after level N approves; any single rejection sets `status=REJECTED` and applies **no** change. Nothing is applied until the final level approves.
4. All org-change queries are **company-scoped** (`company_id = %s::uuid`) — same rule as everything else. Approver resolution matches role by **name** within the company (roles are per-company).
5. The engine lives in `app/services/org_change_service.py`; reuse it — do not re-implement approval logic inline in routes.

**Past mistakes to never repeat:**
- Skills Intelligence had a legacy `enabled_for_hr` flag that blocked HR_ADMIN even after they were granted access via `role_feature_access`. This was removed. Never add sub-flags like this again.
- Skills Intelligence routes used `@require_roles('SYSTEM_ADMIN', 'PORTAL_ADMIN', 'HR_ADMIN')` hardcoded — this broke when the admin granted access to other roles (e.g. Solid Line Manager). Hardcoded role lists on feature routes are forbidden.
