<!--
  FROZEN CONFLUENCE EXPORT — DO NOT EDIT.
  Source: https://roysamiracc1-1777144763345.atlassian.net/wiki/spaces/EmployeeMa/pages/393217
  Page ID 393217 · last edited in Confluence 26 Apr 2026 · exported 8 Aug 2026.
  SUPERSEDED BY: docs/project-management/BACKLOG.md (34 epics vs the 16 below).
  Every KAN-### link below is DEAD — the Jira project contained zero issues at export time.
-->

# HR Portal — Jira Epics & User Stories

**Jira Project:** EmployeeManagementKanban (KAN)
**Board:** https://roysamiracc1-1777144763345.atlassian.net/jira/software/projects/KAN/boards
**Total:** 16 Epics · 80 Stories · All features deployed to `main`

---

## Epic Summary

| Jira Key | Epic |
| --- | --- |
| KAN-2 | EP1 — Authentication & Session Management |
| KAN-3 | EP2 — Role-Based Access Control (RBAC) |
| KAN-4 | EP3 — Employee Registry & Directory |
| KAN-5 | EP4 — Employee Profile & Self-Service |
| KAN-6 | EP5 — Organisational Structure |
| KAN-7 | EP6 — Manager Self-Service |
| KAN-8 | EP7 — Vacation & Leave Management |
| KAN-9 | EP8 — Company Branding & Theming |
| KAN-10 | EP9 — Dashboard & Real-Time Metrics |
| KAN-11 | EP10 — Work Anniversary Recognition |
| KAN-65 | EP11 — Two-Tier Admin System (Tech Admin / Portal Admin) |
| KAN-66 | EP12 — Multi-Company Org CRUD (BU / Location / FU) |
| KAN-67 | EP13 — Feature-Level Permission Matrix |
| KAN-68 | EP14 — Test Automation & Quality Gates (238 tests) |
| KAN-69 | EP15 — Login Page Redesign (split-panel) |
| KAN-70 | EP16 — Multi-Company Seed Data (Telia, 100 employees) |

---

## EP1–EP10 (Original Epics — KAN-2 to KAN-11)

52 stories (KAN-12 to KAN-64) covering: Authentication, RBAC (8 roles), Employee Registry, Profile & Self-Service, Org Structure, Manager Self-Service, Vacation Management, Company Branding, Dashboard Metrics, Work Anniversary Recognition. All delivered and deployed.

---

## EP11 — Two-Tier Admin System (KAN-65)

**Labels:** admin · multi-tenant · security

**What was delivered:**

* PORTAL_ADMIN role in DB with full company-scoped permissions
* \_company_scope() helper — uses admin_company_id for Tech Admin, company_id for Portal Admin
* Company context bar in Admin Panel header (Tech Admin only)
* Tech Admin company_id = NULL enforced via scripts/setup_db.py
* Nav: Portal Admin sees Company Settings; Tech Admin sees Companies list
* Admin tier badge shown in panel header (purple = Tech Admin, teal = Portal Admin)

---

## EP12 — Multi-Company Org CRUD (KAN-66)

**Labels:** org-structure · admin · crud

**What was delivered:**

* 12 REST endpoints: POST/PUT/DELETE for Business Units, Locations, Functional Units
* company_id column added to all three org tables via migration and backfilled
* Portal Admin: company_id auto-injected on create; 403 on cross-company write attempt
* 409 returned when employees are currently assigned and delete is attempted
* UI: Edit/Delete buttons per row, pre-filled modals, inline error display
* \_assert_org_ownership() server-side enforcement

---

## EP13 — Feature-Level Permission Matrix (KAN-67)

**Labels:** rbac · admin · permissions

**What was delivered:**

* portal_features table: 8 feature areas (Employee Profiles, Org Structure, User Accounts, Skills, Vacations, Reports, Company Settings, System Config)
* role_feature_access table: Read/Write/Delete per role-feature pair
* GET /api/admin/roles/features and POST /api/admin/roles/feature-access
* Roles & Permissions tab in Admin Panel (Tech Admin only) with live checkbox matrix
* SYSTEM_ADMIN row locked (always full access); all other roles fully configurable
* Default permissions seeded for all 9 roles

---

## EP14 — Test Automation & Quality Gates (KAN-68)

**Labels:** testing · ci · quality

**What was delivered:**

* tests/test_routes_auth_login.py (21 tests) — login flows, session keys, Tech Admin null company, branding
* tests/test_routes_org.py (31 tests) — org CRUD company scoping, 403 cross-company, 409 employees assigned, context switch
* tests/test_ui_ux.py (48 tests) — CSS path verification, split-panel structure, CSS file integrity, template asset consistency
* .git/hooks/pre-commit — runs full 238-test suite before every commit; aborts on failure
* Total: 238 tests, all mocked, runs in under 0.5 seconds

---

## EP15 — Login Page Redesign (KAN-69)

**Labels:** ui · ux · design

**What was delivered:**

* Split-panel layout: left dark gradient hero with brand/tagline/4 feature bullets; right clean white form panel
* Demo accounts as 2-column chip grid with colour-coded role badges; clicking auto-submits form via quickLogin()
* Responsive: hero collapses on mobile (max-width 860px)
* Bug fix: CSS stylesheet path corrected from style.css to css/style.css
* Regression test permanently guards CSS path in test_ui_ux.py

---

## EP16 — Multi-Company Seed Data: Telia (KAN-70)

**Labels:** seed-data · testing · telia

**What was delivered:**

* scripts/setup_db.py — one-shot safe-to-rerun setup: migration + backfill + Tech Admin fix + portal features + Telia seed
* 100 Telia employees with Nordic names across 5 Business Units, 5 Locations (Stockholm/Helsinki/Oslo/Copenhagen/Tallinn), 12 Functional Units
* Full 4-level management hierarchy: C-suite, VP, Senior Manager, Individual Contributor
* All 100 employees get portal user accounts with correct roles
* Maria Andersson (CPO) seeded as PORTAL_ADMIN for Telia
* database/telia_seed.sql — raw SQL reference file

<!--
  ARCHIVIST'S NOTE (8 Aug 2026): body exported verbatim except that dead KAN-### hyperlinks were
  flattened to plain text (the URLs they pointed at all 404). The claim "All features deployed to
  main" and the 238-test figure were both accurate only as of 26 Apr 2026.
-->
