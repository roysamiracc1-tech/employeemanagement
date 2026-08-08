# HR Portal — Product Backlog (Epics & User Stories)

> **This is the backlog. It lives in git, not in Jira.** See
> [`README.md`](README.md) for how to update it.
>
> **`KAN-###` identifiers are local story IDs, not Jira issues.** They are kept because
> `../ARCHITECTURE_REVIEW.md` and the product-team deliverables cross-reference them. The Jira
> project they originally came from was retired on 8 Aug 2026 with zero issues remaining in it —
> the markdown below is the only surviving record of this backlog.
>
> **EP1–EP27 are completed and deployed** to `main`; **EP28–EP34** (architecture-review backlog)
> are partially delivered — see the Status column and per-story markers below.
> Legend: ✅ Done · 🟡 In progress · ⬜ Planned.

---

## Epic Summary

| ID | Epic | Stories | Status |
|----------|------|---------|--------|
| KAN-2 | EP1 — Authentication & Session Management | KAN-12 · KAN-13 · KAN-14 · KAN-15 | ✅ Done |
| KAN-3 | EP2 — Role-Based Access Control (RBAC) | KAN-16 · KAN-17 · KAN-18 · KAN-19 | ✅ Done |
| KAN-4 | EP3 — Employee Registry & Directory | KAN-20 · KAN-21 · KAN-22 · KAN-23 · KAN-24 | ✅ Done |
| KAN-5 | EP4 — Employee Profile & Self-Service | KAN-25 · KAN-26 · KAN-27 · KAN-28 · KAN-29 · KAN-30 · KAN-31 | ✅ Done |
| KAN-6 | EP5 — Organisational Structure | KAN-32 · KAN-33 · KAN-34 · KAN-35 · KAN-36 | ✅ Done |
| KAN-7 | EP6 — Manager Self-Service | KAN-37 · KAN-38 | ✅ Done |
| KAN-8 | EP7 — Vacation & Leave Management | KAN-39 · KAN-40 · KAN-41 · KAN-42 · KAN-43 · KAN-44 · KAN-45 · KAN-46 · KAN-48 · KAN-49 · KAN-50 · KAN-51 | ✅ Done |
| KAN-9 | EP8 — Company Branding & Theming | KAN-52 · KAN-53 · KAN-54 · KAN-55 · KAN-56 · KAN-57 · KAN-58 | ✅ Done |
| KAN-10 | EP9 — Dashboard & Real-Time Metrics | KAN-59 · KAN-60 · KAN-61 · KAN-62 | ✅ Done |
| KAN-11 | EP10 — Work Anniversary Recognition | KAN-63 · KAN-64 | ✅ Done |
| KAN-65 | EP11 — Two-Tier Admin System | Stories below | ✅ Done |
| KAN-66 | EP12 — Multi-Company Org CRUD | Stories below | ✅ Done |
| KAN-67 | EP13 — Feature-Level Permission Matrix | Stories below | ✅ Done |
| KAN-68 | EP14 — Test Automation & Quality Gates | Stories below | ✅ Done |
| KAN-69 | EP15 — Login Page Redesign | Stories below | ✅ Done |
| KAN-70 | EP16 — Multi-Company Seed Data (Telia) | Stories below | ✅ Done |
| EP17 | Family Tree Org Chart & Employee-Centric Navigation | KAN-81 · KAN-82 · KAN-83 · KAN-84 · KAN-85 · KAN-86 · KAN-87 | ✅ Done |
| EP18 | Email Notification System | KAN-88 · KAN-89 · KAN-90 · KAN-91 | ✅ Done |
| EP19 | Full-Text Search | KAN-92 · KAN-93 · KAN-94 · KAN-95 | ✅ Done |
| EP20 | Vacation Calendar | KAN-96 · KAN-97 · KAN-98 | ✅ Done |
| EP21 | Bulk Employee Import | KAN-99 · KAN-100 · KAN-101 · KAN-102 | ✅ Done |
| EP22 | Mobile Responsive Design | KAN-103 · KAN-104 · KAN-105 · KAN-106 | ✅ Done |
| EP23 | In-App Notification System | KAN-107 · KAN-108 · KAN-109 · KAN-110 · KAN-111 · KAN-112 · KAN-113 | ✅ Done |
| EP24 | Vacation Cancellation & Withdrawal UI | KAN-114 · KAN-115 · KAN-116 · KAN-117 · KAN-118 | ✅ Done |
| EP25 | Analytics & Reporting Dashboard | KAN-119 · KAN-120 · KAN-121 · KAN-122 · KAN-123 · KAN-124 · KAN-125 · KAN-126 · KAN-127 · KAN-128 · KAN-129 · KAN-130 · KAN-131 · KAN-132 | ✅ Done |
| EP26 | Vacation Balance Visibility | KAN-133 · KAN-134 · KAN-135 · KAN-136 | ✅ Done |
| EP27 | Employee Position Change Workflow | KAN-137 · KAN-138 · KAN-139 · KAN-140 · KAN-141 · KAN-142 · KAN-143 · KAN-144 · KAN-145 · KAN-146 · KAN-147 | ✅ Done |
| EP28 | Security Hardening (Architecture Review) | KAN-148 · KAN-149 · KAN-150 · KAN-151 · KAN-152 · KAN-153 | 🟡 In progress |
| EP29 | Data Layer & Query Performance | KAN-154 · KAN-155 · KAN-156 · KAN-157 · KAN-158 | 🟡 In progress |
| EP30 | Scalability & Runtime | KAN-159 · KAN-160 · KAN-161 · KAN-162 · KAN-163 · KAN-164 | ⬜ Planned |
| EP31 | Schema Source of Truth & Migrations | KAN-165 · KAN-166 · KAN-167 | 🟡 In progress |
| EP32 | Testing & CI Hardening | KAN-168 · KAN-169 · KAN-170 · KAN-171 | 🟡 In progress |
| EP33 | Frontend Modernization | KAN-172 · KAN-173 · KAN-174 · KAN-175 · KAN-176 · KAN-177 | ⬜ Planned |
| EP34 | Architecture & Structure | KAN-178 · KAN-179 · KAN-180 · KAN-181 · KAN-182 | ⬜ Planned |

> **EP28–EP34** are sourced from the architecture review in [`docs/ARCHITECTURE_REVIEW.md`](../ARCHITECTURE_REVIEW.md)
> (finding IDs `Fn` are referenced per story). Unlike EP1–EP27, these are **partially delivered**: ✅ KAN-152 · KAN-154 · KAN-157 · KAN-165 · KAN-169 done, 🟡 KAN-150 partial; the rest are ⬜ planned.

---

## EPIC 1 — Authentication & Session Management  —  ✅ Done
**ID:** KAN-2 · **Label:** `auth` `security`
**Description:** Secure login/logout with role-aware sessions. All portal activity requires authentication.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-12 | As an **employee**, I want to log in with my work email so I can access the portal. | Login accepts email; invalid email shows error; redirects to dashboard on success. | Must Have |
| ✅ KAN-13 | As any **logged-in user**, I want my session to persist for 8 hours so I do not need to re-login constantly. | Session cookie TTL = 8 h; logout clears session immediately. | Must Have |
| ✅ KAN-14 | As any **user**, I want to log out securely so no one else can access my account on shared devices. | `/logout` clears session and redirects to login. | Must Have |
| ✅ KAN-15 | As a **developer/demo**, I want quick-access demo user tiles on the login page so testers can log in without credentials. | Login page shows up to 6 demo user cards; clicking one pre-fills email. | Should Have |

---

## EPIC 2 — Role-Based Access Control (RBAC)  —  ✅ Done
**ID:** KAN-3 · **Label:** `rbac` `security`
**Description:** Eight distinct roles gate access to views and APIs. Roles are cumulative and checked server-side on every protected endpoint.

**Roles:** `SYSTEM_ADMIN` · `HR_ADMIN` · `SOLID_LINE_MANAGER` · `DOTTED_LINE_MANAGER` · `DEPARTMENT_HEAD` · `LOCATION_HEAD` · `HIRING_MANAGER` · `EMPLOYEE`

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-16 | As a **SYSTEM_ADMIN**, I want to assign and revoke roles for any user so I can control access. | Role edit modal on admin panel; changes take effect immediately; own roles cannot be removed. | Must Have |
| ✅ KAN-17 | As a **SYSTEM_ADMIN**, I want to enable or disable a user account so ex-employees cannot log in. | Toggle active/inactive; inactive users are rejected at login with clear error. | Must Have |
| ✅ KAN-18 | As a **non-admin user**, I want to be redirected with an error message if I try to access a restricted page. | HTTP redirect to dashboard with flash error; no data leaked. | Must Have |
| ✅ KAN-19 | As a **SYSTEM_ADMIN**, I want the admin panel to show all users with their roles and last-login timestamp. | Admin panel loads all users; shows role badges; shows "Never" if no login recorded. | Should Have |

---

## EPIC 3 — Employee Registry & Directory  —  ✅ Done
**ID:** KAN-4 · **Label:** `employees` `directory`
**Description:** Central record of all employees with full personal, employment, and org data. Searchable, filterable directory available to authorised roles.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-20 | As an **HR_ADMIN / SYSTEM_ADMIN**, I want to register a new employee through a guided multi-step form so data is captured completely. | 6-step form: Personal Info → Employment → Organisation → Reporting → Skills → Portal Access; auto-generates EMP-XXX number; creates all records atomically. | Must Have |
| ✅ KAN-21 | As a **registrar**, I want the employee number to be auto-generated sequentially so I don't assign duplicates. | `_next_employee_number()` selects MAX and increments; zero-pads to 3 digits. | Must Have |
| ✅ KAN-22 | As an **HR_ADMIN**, I want to search and filter the employee directory by name, location, business unit, and employment type. | Filters applied server-side; results paginate at configurable rows/page. | Must Have |
| ✅ KAN-23 | As a **SYSTEM_ADMIN / HR_ADMIN**, I want to see each employee's manager, location, skills, and certifications in the directory row. | Directory table includes manager pill, location badge, skill bars, cert count. | Should Have |
| ✅ KAN-24 | As a **registrar**, I want to assign solid-line and dotted-line managers to a new employee during registration. | Step 4 lets user search and select solid/dotted manager; records written to `manager_relationships` with `is_current=true`. | Must Have |

---

## EPIC 4 — Employee Profile & Self-Service  —  ✅ Done
**ID:** KAN-5 · **Label:** `profile` `self-service`
**Description:** Every employee can view their own profile and self-maintain skills, certifications, and gender. Managers and admins see read-only profiles for others.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-25 | As any **employee**, I want to view my complete profile including employment details, org placement, manager, skills, and certifications. | `/profile` loads own profile; `/profile/<id>` loads others; `is_own` flag controls edit UI. | Must Have |
| ✅ KAN-26 | As an **employee**, I want to add skills to my profile and self-rate each on a 1–10 scale so my competencies are visible. | Skill modal with 🌱💡⚡🏆 level buttons; POST `/api/profile/skills`; list refreshes in-page. | Must Have |
| ✅ KAN-27 | As an **employee**, I want to remove a skill from my profile so outdated entries do not mislead others. | DELETE `/api/profile/skills/<id>`; list updated in-page. | Must Have |
| ✅ KAN-28 | As an **employee**, I want to add certifications with issuer, dates, and credential URL so my qualifications are recorded. | POST `/api/profile/certifications`; accepts cert name, provider, dates, URL; in-page reload. | Must Have |
| ✅ KAN-29 | As an **employee**, I want to edit and remove my certifications so I keep them current. | PUT and DELETE `/api/profile/certifications/<id>`; in-page update. | Must Have |
| ✅ KAN-30 | As an **employee**, I want to record my gender on my profile so my vacation eligibility is calculated correctly. | Gender dropdown (Male/Female/Other) with auto-save on change via POST `/api/profile/gender`. | Must Have |
| ✅ KAN-31 | As a **SYSTEM_ADMIN / HR_ADMIN**, I want to validate an employee's skill rating so the profile shows verified competencies. | POST `/api/admin/validate-skill`; status → `VALIDATED`; skill bar turns green. | Should Have |

---

## EPIC 5 — Organisational Structure  —  ✅ Done
**ID:** KAN-6 · **Label:** `org` `hierarchy`
**Description:** Multi-level org model: Companies → Business Units → Functional Units → Cost Centres → Locations.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-32 | As a **SYSTEM_ADMIN**, I want to register companies so multiple entities can share the portal. | `/admin/companies` CRUD; company has name, industry, website, HQ, description, active flag. | Must Have |
| ✅ KAN-33 | As an **employee**, I want to view my company's overview page showing headcount, locations, and business units. | `/company` shows stats, BU breakdown, location breakdown; accessible to all employees. | Should Have |
| ✅ KAN-34 | As an **HR_ADMIN**, I want to assign employees to business units, functional units, locations, and cost centres during onboarding. | Registration step 3 has cascading BU → FU selectors; `employee_org_assignments` written with `is_current=true`. | Must Have |
| ✅ KAN-35 | As a **manager or admin**, I want to view the org hierarchy as an interactive tree so I can understand reporting lines. | `/org-tree` renders recursive tree via CTE (max 10 levels); nodes clickable; expand/collapse; admin can pick any root or Full Org. | Must Have |
| ✅ KAN-36 | As a **manager**, I want to see pending vacation badges on org tree nodes so I know which reportees need action. | Orange ⏳ badge on nodes with pending requests; links to `/vacation/team`. | Should Have |

---

## EPIC 6 — Manager Self-Service  —  ✅ Done
**ID:** KAN-7 · **Label:** `manager` `team`
**Description:** Managers have a dedicated team view showing all direct reports with enriched data and can take management actions from a single screen.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-37 | As a **manager**, I want to see all my direct reports in a card layout with their role, location, skills, and manager links. | `/my-team` shows cards for all SOLID_LINE direct reports; each card has profile link and management quick-actions. | Must Have |
| ✅ KAN-38 | As a **manager**, I want to see a pending vacation count badge on each team member's card so I can act without leaving the team page. | `pendingCounts` fetched on page load; badge shows ⏳ N vacation req with link to `/vacation/team`. | Should Have |

---

## EPIC 7 — Vacation & Leave Management  —  ✅ Done
**ID:** KAN-8 · **Label:** `vacation` `leave` `hr-process`
**Description:** Company-defined leave types with location scoping and eligibility rules. Full request → approval workflow with manager review queue and upcoming schedule view.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-39 | As a **SYSTEM_ADMIN**, I want to define vacation types per company (e.g. Annual Leave, Sick Leave) with day limits and paid/unpaid flags. | `/admin/vacation-types` CRUD; name, max days/year, is_paid, colour, description stored per company. | Must Have |
| ✅ KAN-40 | As a **SYSTEM_ADMIN**, I want to make a vacation type available only to employees in specific locations. | Multi-select locations; stored in `vacation_type_locations`; company-wide types have no location entries. | Must Have |
| ✅ KAN-41 | As a **SYSTEM_ADMIN**, I want to add eligibility rules (gender, minimum tenure) to vacation types so the right employees see them. | Step 4 Rules builder; supports `GENDER_EQ`, `MIN_TENURE_MONTHS`, `MIN_TENURE_YEARS`; AND logic. | Must Have |
| ✅ KAN-42 | As an **employee**, I want to see only the vacation types I am eligible for so I don't waste time applying for unavailable leave. | Location + ALL rules must pass; rule labels shown as purple badges; ineligible types hidden. | Must Have |
| ✅ KAN-43 | As an **employee**, I want to see my used vs. remaining days for each vacation type so I know my balance. | Type cards show used/max progress bar; remaining shown in request modal; counts PENDING+APPROVED. | Must Have |
| ✅ KAN-44 | As an **employee**, I want to submit a vacation request with start/end dates and a note so my manager is notified. | Request modal; weekday count verified server-side; manager auto-set from solid-line; annual limit enforced. | Must Have |
| ✅ KAN-45 | As an **employee**, I want to cancel a PENDING request if my plans change. | DELETE `/api/vacation/request/<id>`; only PENDING status can be cancelled; status → CANCELLED. | Must Have |
| ✅ KAN-46 | As an **employee**, I cannot submit a vacation request if I have no manager assigned. | Warning banner shown; request button disabled; API returns 400 with reason. | Must Have |
| ✅ KAN-48 | As an **employee**, I want to see all my past and current requests with their status and manager note. | Request history table shows type, dates, days, status badge, manager note, cancel button for PENDING. | Must Have |
| ✅ KAN-49 | As a **manager**, I want to see all pending vacation requests from my reportees and approve or reject them with a note. | Pending tab; review modal with optional note; POST `/api/vacation/review/<id>`; only PENDING reviewable. | Must Have |
| ✅ KAN-50 | As a **manager**, I want to see my team's upcoming approved leave in a calendar-like schedule so I can plan coverage. | Upcoming tab groups by month; "● On leave" indicator for currently active requests. | Should Have |
| ✅ KAN-51 | As a **manager**, I cannot approve a request that has already been reviewed. | API validates status == PENDING before update; returns 400 if already actioned. | Must Have |

---

## EPIC 8 — Company Branding & Theming  —  ✅ Done
**ID:** KAN-9 · **Label:** `branding` `ui` `personalisation`
**Description:** Admins configure per-company visual identity. Employees choose their own light/dark preference. All settings persist and apply immediately on next page load.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-52 | As a **SYSTEM_ADMIN**, I want to upload a company logo so it appears in the sidebar for all employees of that company. | Drag-and-drop upload; saved to `static/uploads/logos/`; old file deleted on replacement; PNG/JPG/SVG/WebP max 2 MB. | Must Have |
| ✅ KAN-53 | As a **SYSTEM_ADMIN**, I want to optionally provide an external logo URL instead of uploading a file. | Tab switcher between Upload File and External URL; live preview; uploaded file takes priority. | Should Have |
| ✅ KAN-54 | As a **SYSTEM_ADMIN**, I want to set a primary theme colour for my company so the portal reflects our brand identity. | Colour picker + hex input + 8 quick presets; saved as `theme_color`; injected as `--primary` CSS variable. | Must Have |
| ✅ KAN-55 | As a **SYSTEM_ADMIN**, I want to add a company-wide header banner (HTML) above all portal pages for announcements. | `header_html` field; rendered above all pages for company employees; inline preview button. | Should Have |
| ✅ KAN-56 | As a **SYSTEM_ADMIN**, I want to add a company-wide footer (HTML) below all pages for legal links and support contacts. | `footer_html` field; rendered at bottom of all pages; clear button available. | Should Have |
| ✅ KAN-57 | As any **employee**, I want to switch between light and dark mode so I can work comfortably in different environments. | Toggle button in topbar; instant CSS variable swap; POST `/api/user/theme` persists to DB; restored on next login. | Must Have |
| ✅ KAN-58 | As an **employee**, my branding is refreshed in my session after the admin updates the company record. | `admin_company_edit` POST re-fetches and updates `session['branding']` immediately. | Should Have |

---

## EPIC 9 — Dashboard & Real-Time Metrics  —  ✅ Done
**ID:** KAN-10 · **Label:** `dashboard` `analytics`
**Description:** Role-aware dashboard with live stat cards, drill-down filtering, and configurable auto-refresh intervals per role.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-59 | As any **logged-in user**, I want to see a dashboard with the key stats relevant to my role so I get an immediate status overview. | Stats differ by role; SYSTEM_ADMIN sees all-company counts; managers see team counts; employees see personal stats. | Must Have |
| ✅ KAN-60 | As a **dashboard user**, I want stat cards to auto-refresh periodically so I see live data without reloading. | Refresh interval configurable per role; JS polls `/api/dashboard/stats`; changed values animate (flash green). | Should Have |
| ✅ KAN-61 | As a **dashboard user**, I want clickable stat cards that filter the employee directory to the relevant subset. | Clicking a stat card navigates to `/directory?filter=<value>`; directory pre-applies the filter. | Should Have |
| ✅ KAN-62 | As a **SYSTEM_ADMIN**, I want to configure per-role refresh intervals so I can balance data freshness against server load. | POST `/api/admin/refresh-settings`; persisted to `widget_refresh_settings`; applied on next page load. | Nice to Have |

---

## EPIC 10 — Work Anniversary Recognition  —  ✅ Done
**ID:** KAN-11 · **Label:** `engagement` `hr`
**Description:** Automatic work anniversary detection with animated visual indicator on employee names throughout the portal.

| ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-63 | As a **manager or admin**, I want to see a visual indicator next to employees whose work anniversaries are upcoming so I can acknowledge them. | 🎂 badge computed from `join_date`; urgency levels: normal (>7 days), soon (≤7 days), urgent (today/tomorrow); animated per urgency. | Should Have |
| ✅ KAN-64 | As a **manager**, I want to hover over the badge to see the exact anniversary date and tenure. | Tooltip shows "N-year anniversary on DD MMM YYYY" on hover with smooth animation. | Should Have |

---

## EPIC 11 — Two-Tier Admin System  —  ✅ Done
**Label:** `admin` `multi-tenant` `security`
**Description:** Introduce two distinct admin tiers — Tech Admin (system-wide) and Portal Admin (company-scoped) — to support multi-company SaaS operations.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-65 | As a **platform owner**, I want a Tech Admin role that spans all companies so I can manage the entire portal from one account. | `SYSTEM_ADMIN` role grants full cross-company access; not affiliated with any company; `company_id = NULL` on employee record. | Must Have |
| ✅ KAN-66 | As an **HR Director**, I want a Portal Admin role scoped to my company so I can self-manage my company's data without impacting others. | `PORTAL_ADMIN` role; all admin queries auto-filter by `session['company_id']`; cannot see other companies' data. | Must Have |
| ✅ KAN-67 | As a **Tech Admin**, I want to switch company context in the Admin Panel so I can manage a specific company's data without separate logins. | Company context bar in admin header; selecting a company filters all admin sections; selecting "All Companies" removes filter; stored in `session['admin_company_id']`. | Must Have |
| ✅ KAN-68 | As a **Tech Admin**, I should not belong to any company so there is no data-isolation conflict. | `scripts/setup_db.py` sets `company_id = NULL` on all `SYSTEM_ADMIN` employee records; new Tech Admin registrations must have no company; `session['company_id']` is empty. | Must Have |

---

## EPIC 12 — Multi-Company Org CRUD  —  ✅ Done
**Label:** `org-structure` `admin` `crud`
**Description:** Full create/update/delete management of Business Units, Locations, and Functional Units from the admin panel, with per-company data isolation.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-69 | As a **Portal Admin**, I want to add, edit, and delete Business Units for my company so I can keep the org chart accurate. | POST/PUT/DELETE `/api/admin/org/business-units`; company_id auto-injected; 409 if employees assigned on delete; Edit modal pre-filled from live data. | Must Have |
| ✅ KAN-70 | As a **Portal Admin**, I want to add, edit, and delete Locations so I can track where employees are based. | POST/PUT/DELETE `/api/admin/org/locations`; office_code unique per instance; 409 on delete if employees assigned. | Must Have |
| ✅ KAN-71 | As a **Portal Admin**, I want to add, edit, and delete Functional Units, linking each to a Business Unit so the hierarchy is complete. | POST/PUT/DELETE `/api/admin/org/functional-units`; BU dropdown in FU modal populated from live BU list; cross-company write blocked with 403. | Must Have |
| ✅ KAN-72 | As a **Tech Admin**, I want to manage org structure for any company I select in the context switcher so I can assist Portal Admins. | Tech Admin in company context can CRUD org entries for that company; Tech Admin with "All Companies" selected can see all entries. | Should Have |

---

## EPIC 13 — Feature-Level Permission Matrix  —  ✅ Done
**Label:** `rbac` `admin` `permissions`
**Description:** Allow Tech Admin to define granular read/write/delete permissions per role per feature area via a visual matrix in the Admin Panel.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-73 | As a **Tech Admin**, I want to define what each role can read, write, and delete for each portal feature so access can be tuned without code changes. | Roles & Permissions tab with 8 feature rows × all roles × R/W/D checkboxes; changes saved via `POST /api/admin/roles/feature-access`; `SYSTEM_ADMIN` row locked. | Must Have |
| ✅ KAN-74 | As a **Tech Admin**, I want permission changes to take effect immediately so I do not need to restart the server. | upsert via `ON CONFLICT DO UPDATE`; no server restart required; UI reverts checkbox on API failure. | Must Have |

---

## EPIC 14 — Test Automation & Quality Gates  —  ✅ Done
**Label:** `testing` `ci` `quality`
**Description:** Establish a comprehensive automated test suite covering unit, integration, and UI/UX regression; enforce via pre-commit gate.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-75 | As a **developer**, I want a pre-commit hook that runs all tests so regressions cannot reach the repository. | `.git/hooks/pre-commit` runs `pytest tests/ -q`; aborts commit on failure; 238 tests in ≤ 1 second. | Must Have |
| ✅ KAN-76 | As a **developer**, I want UI/UX regression tests that catch broken template assets so login page breakages are caught before commit. | `test_ui_ux.py` verifies CSS path (`css/style.css`), all login page CSS classes exist in stylesheet, no old class names remain, admin tab visibility per role. | Must Have |
| ✅ KAN-77 | As a **developer**, I want integration tests for all admin CRUD endpoints including company scoping so security boundaries are continuously verified. | `test_routes_org.py` — company filter in query params for Portal Admin, 403 cross-company write, 409 on delete with employees, context switch sets session. | Must Have |

---

## EPIC 15 — Login Page Redesign  —  ✅ Done
**Label:** `ui` `ux` `design`
**Description:** Replace the single-card login with a modern split-panel layout: hero branding panel (left) + clean form panel (right) with demo account chips.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-78 | As a **new user**, I want a professional login page that communicates product value so I trust the portal. | Split-panel: left hero with gradient, tagline, 4 feature bullets; right panel with form, title, footer. Responsive (hero collapses on mobile). | Should Have |
| ✅ KAN-79 | As a **demo/tester**, I want one-click demo account chips so I can log in without typing an email. | 2-column grid of demo cards; each shows name, title, role badge; clicking auto-submits the form; `quickLogin()` JS function. | Should Have |

---

## EPIC 16 — Multi-Company Seed Data (Telia)  —  ✅ Done
**Label:** `seed-data` `testing` `telia`
**Description:** Seed a second company (Telia Company) with realistic Nordic employee data to demonstrate multi-company capabilities.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-80 | As a **Tech Admin**, I want realistic employee data for a second company (Telia) so I can demonstrate multi-company features to stakeholders. | `scripts/setup_db.py` seeds 100 Telia employees across 5 BUs, 5 locations, 12 FUs; full management hierarchy; user accounts with correct roles; Portal Admin seeded as Maria Andersson. | Should Have |

---

## EP17 — Family Tree Org Chart & Employee-Centric Navigation  —  ✅ Done
**ID:** KAN-81 · **Label:** `org-chart` `ux`

**Description:** Redesign the organisation tree from a folder/indent structure into a proper top-down family tree chart that starts from the logged-in employee, with full up/down navigation.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-81 | As an **employee**, I want the org tree to start from my own position so I immediately see my place in the hierarchy. | Tree always loads rooted at `session['employee_id']`; "you" node is highlighted in purple; route is `@login_required` (all roles). | Must Have |
| ✅ KAN-82 | As an **employee**, I want to navigate up the tree to see my manager's team so I understand the wider org context. | Blue ↑ button shows direct manager name; clicking re-focuses the tree at the manager's node; breadcrumb trail updates. | Must Have |
| ✅ KAN-83 | As a **manager**, I want to navigate down into a specific person's team so I can review their reporting structure. | Focus ↓ button visible on hover for any node with reports; clicking re-focuses tree at that person; ← My view button returns. | Must Have |
| ✅ KAN-84 | As any user, I want a breadcrumb trail showing my path through the org so I can jump to any ancestor level. | Breadcrumb renders all ancestors from CEO to current focus; each ancestor is a clickable button; current focus shown in bold. | Must Have |
| ✅ KAN-85 | As any user, I want the chart to look like a family tree with connecting lines so the hierarchy is visually clear. | Top-down layout: parent card → vertical stem → horizontal connector → child cards; T-connector lines drawn with CSS pseudo-elements; no SVG or canvas required. | Must Have |
| ✅ KAN-86 | As a **developer**, I want a `/api/org-tree/context` endpoint so the frontend can fetch ancestor chains without loading the entire tree. | Returns `{ focus: {...}, ancestors: [{...}, ...] }` ordered CEO-first; uses upward recursive CTE; no depth limit (org is finite). | Must Have |
| ✅ KAN-87 | As a **developer**, I want integration tests covering the new context endpoint and family tree page so regressions are caught pre-commit. | `TestOrgTreePage` (6 tests): accessible to all roles, contains `ftree-root` and `org-nav`. `TestApiOrgTree` (4 tests): root param, empty tree, redirect. `TestApiOrgTreeContext` (5 tests): ancestors, no ancestors at top, default to session, null focus. | Must Have |

---

## EP18 — Email Notification System  —  ✅ Done
**ID:** KAN-88 · **Label:** `notifications` `email`

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| ✅ KAN-88 | As a **Company Admin**, I want to configure which roles receive which notification events so that only relevant people are alerted. | Admin matrix UI shows events × roles; checkboxes for enabled + allow_mute; saved via POST /api/notifications/settings. | Must Have |
| ✅ KAN-89 | As a **Company Admin**, I want to propagate notification settings down the role hierarchy so I don't configure each role individually. | inherit=true on POST propagates to all sub-roles via ROLE_HIERARCHY map. | Must Have |
| ✅ KAN-90 | As an **Employee**, I want to mute non-critical notifications so I am not overwhelmed. | POST /api/notifications/mute; only works if allow_mute=true in company config. | Should Have |
| ✅ KAN-91 | As a **Developer**, I want async email sending so HTTP requests are never blocked by SMTP. | threading.Thread sends email outside request lifecycle; SMTP_HOST empty = log-only dev mode. | Must Have |

---

## EP19 — Full-Text Search  —  ✅ Done
**ID:** KAN-92 · **Label:** `search` `ux`

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| ✅ KAN-92 | As an **Employee**, I want to search for colleagues by name or job title so I can find them quickly. | GET /api/search?q= uses plainto_tsquery on GIN-indexed employee_search_index; returns ranked results. | Must Have |
| ✅ KAN-93 | As an **Employee**, I want to search for my upcoming vacations in natural language. | "my upcoming vacation", "next month" patterns parsed server-side to date-range queries. | Should Have |
| ✅ KAN-94 | As a **Manager**, I want to type "people reporting to me" and see my org tree. | Pattern matching returns focus_tree action with root_id=my employee_id. | Should Have |
| ✅ KAN-95 | As any user, I want a search bar always visible in the topbar. | .topbar-search form present on all authenticated pages; links to /search results page. | Must Have |

---

## EP20 — Vacation Calendar  —  ✅ Done
**ID:** KAN-96 · **Label:** `calendar` `vacation`

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| ✅ KAN-96 | As an **Employee**, I want a month-grid calendar of my leave so I can see my planned absences at a glance. | /vacation/calendar renders pure CSS/JS month grid; scope=mine shows own approved+pending requests. | Must Have |
| ✅ KAN-97 | As a **Manager**, I want to see my whole team's leave in the calendar so I can plan workload. | scope=team queries manager_relationships for solid-line reports; all their approved+pending requests shown. | Must Have |
| ✅ KAN-98 | As an **Admin**, I want to see company-wide leave in the calendar. | scope=all scoped to company_id; colour legend auto-generated from vacation type colours. | Should Have |

---

## EP21 — Bulk Employee Import  —  ✅ Done
**ID:** KAN-99 · **Label:** `import` `hr-ops`

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| ✅ KAN-99  | As a **Portal Admin**, I want to import employees from a CSV so I can onboard large teams at once. | Drag-drop upload → row-level validation → preview → auto-approve (zero errors) → process. | Must Have |
| ✅ KAN-100 | As an **HR Admin**, I want to upload a CSV that goes through an approval workflow before employees are created. | HR Admin uploads → status=PENDING_REVIEW → Portal Admin approves → process. | Must Have |
| ✅ KAN-101 | As a **Portal Admin**, I want to review and reject an HR Admin's import if it contains errors. | POST /api/admin/imports/<id>/reject with reason; import marked REJECTED. | Must Have |
| ✅ KAN-102 | As a **Developer**, I want per-row validation so that a few bad rows don't block the entire import. | Each row gets validation_errors JSONB; VALID rows imported independently of INVALID rows. | Must Have |

---

## EP22 — Mobile Responsive Design  —  ✅ Done
**ID:** KAN-103 · **Label:** `mobile` `ux` `frontend`

| Story ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| ✅ KAN-103 | As a **Mobile User**, I want the sidebar to open as a drawer so I can navigate on a phone. | @media <768px: sidebar transform translateX(-100%); hamburger toggles .mob-open; overlay closes it. | Must Have |
| ✅ KAN-104 | As a **Mobile User**, I want data tables to show as labelled cards so I can read them without horizontal scroll. | .data-table td becomes display:flex with ::before content:attr(data-label). | Must Have |
| ✅ KAN-105 | As a **Mobile User**, I want the org tree to scroll horizontally with touch momentum. | .ftree-wrap: overflow-x:auto; -webkit-overflow-scrolling:touch. | Should Have |
| ✅ KAN-106 | As a **Mobile User**, I want the login page to stack vertically so it's usable on a small screen. | .login-wrap flex-direction:column at <768px; hero collapses to 180px. | Should Have |

---

## EP23 — In-App Notification System  —  ✅ Done
**ID:** KAN-107 · **Label:** `notifications` `ux` `bell`
**Description:** Every user gets a bell icon in the topbar. Managers see pending vacation approvals; employees see real-time alerts when their requests are approved, rejected, or when they cancel. Notifications persist in a `user_notifications` table and auto-mark as read.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-107 | As an **employee**, I want a bell notification when my vacation is approved so I know without checking my history. | `user_notifications` row inserted for employee on every approve/reject; bell badge count > 0 after approval; message includes type, dates. | Must Have |
| ✅ KAN-108 | As an **employee**, I want to see the approval notification in the bell dropdown so I can read the outcome without navigating away. | Bell dropdown renders "My Notifications" section; shows ✅/❌ icon, message text, timestamp, and "View →" link to `/vacation`. | Must Have |
| ✅ KAN-109 | As a **manager**, I want a bell notification when an employee cancels their vacation so I can replan team capacity. | `VACATION_CANCELLED` event creates `user_notifications` row for manager's user_id; message names the employee and dates; link `/vacation/team`. | Must Have |
| ✅ KAN-110 | As any **user**, I want the bell badge to show the total of pending approvals plus unread notifications so one badge covers everything. | `loadBellCount()` fetches `/api/vacation/pending-count` and `/api/my-notifications` in parallel; badge = sum of both. | Must Have |
| ✅ KAN-111 | As any **user**, I want notifications to auto-mark as read after I open the dropdown so the badge clears without a manual action. | `setTimeout(() => fetch('/api/my-notifications/mark-read', {method:'POST'}), 2000)` fires after dropdown opens. | Should Have |
| ✅ KAN-112 | As a **developer**, I want `/api/my-notifications` and `/api/my-notifications/mark-read` endpoints so the frontend can fetch and clear alerts. | GET returns `{count, notifications:[]}` with `event_type`, `message`, `link`, `created_at`; POST marks all read for current user. | Must Have |
| ✅ KAN-113 | As a **developer**, I want unit tests verifying notifications are created on approve, reject, and cancel so regressions are caught pre-commit. | `test_approve_sets_approved_status` asserts `create_user_notification` called with correct user_id, event, message; same for reject and cancel; no-crash test when user account missing. | Must Have |

---

## EP24 — Vacation Cancellation & Withdrawal UI  —  ✅ Done
**ID:** KAN-114 · **Label:** `vacation` `ux` `cancel`
**Description:** The cancel button was always present in the vacation history table but was completely invisible (grey text, no border). This epic makes it a visible action, extends it to allow withdrawal of future approved vacations, and ensures managers are notified on every cancellation.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-114 | As an **employee**, I want a clearly visible "✕ Cancel" button next to PENDING requests so I can cancel without hunting for a hidden control. | Button styled as `btn btn-danger btn-sm`; red background, white text; visible in request history table; confirmation dialog says "Your manager will be notified." | Must Have |
| ✅ KAN-115 | As an **employee**, I want to withdraw an approved vacation that hasn't started yet so I can change my plans. | "Withdraw" button appears on APPROVED rows where `start_date > today`; DELETE endpoint accepts APPROVED + future; confirmation warns "This cannot be undone." | Should Have |
| ✅ KAN-116 | As the **system**, I want to block withdrawal of already-started vacations so approved leave cannot be retroactively removed. | DELETE returns 400 "Cannot withdraw a request that has already started" if `start_date <= today`. | Must Have |
| ✅ KAN-117 | As a **manager**, I want a bell notification and email when an employee cancels or withdraws so I can adjust team plans. | `VACATION_CANCELLED` dispatch + `create_user_notification` called from `api_vacation_cancel`; manager's user_id resolved from vacation_requests.manager_id; link = `/vacation/team`. | Must Have |
| ✅ KAN-118 | As a **developer**, I want unit tests for all cancellation/withdrawal paths so edge cases are covered. | Tests: cancel PENDING succeeds; withdraw future APPROVED succeeds; already-started APPROVED blocked (400); REJECTED blocked (400); no-crash when manager has no user account; notification link is `/vacation/team`. | Must Have |

---

## EP25 — Analytics & Reporting Dashboard  —  ✅ Done
**ID:** KAN-119 · **Label:** `analytics` `admin` `reporting`
**Description:** A full analytics dashboard under `/admin/analytics` giving Company Admins, Portal Admins, and HR Admins actionable insight into feature adoption, vacation behaviour, skills coverage, org structure health, and search patterns. Every page visit and search query is logged non-blocking in Postgres, giving a rolling 1-year behavioural dataset.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-119 | As an **admin**, I want page-visit tracking so I know which features employees actually use. | `page_views` table; `@after_request` hook logs `user_id`, `company_id`, `role`, `route`, `page_label` in a background thread; skips `/api/`, `/static/`, login, unauthenticated requests. | Must Have |
| ✅ KAN-120 | As an **admin**, I want search-query logging so I can identify what employees can't find. | `search_logs` table; every `/api/search` call logs `query`, `result_count`, `role`, `company_id` in background thread. | Must Have |
| ✅ KAN-121 | As an **admin**, I want an Overview tab showing daily active users, most-visited pages, and feature adoption % so I understand portal engagement. | Chart.js line chart for DAU; horizontal bar for feature adoption (% of employees who visited each feature); top-pages table; bulk-import usage widget. | Must Have |
| ✅ KAN-122 | As an **admin**, I want a Vacation tab with KPIs (approval rate, avg decision time, pending backlog), time-series chart, status doughnut, and per-employee drilldown. | Approval/rejection/cancellation rates; avg manager decision hours; requests-over-time line chart; status doughnut; leave utilisation grouped by Company/Dept/Location/Manager; sortable employee table with used-days column. | Must Have |
| ✅ KAN-123 | As an **admin**, I want a Skills tab showing profile completeness %, validation rate, top skills, and skills-added trend so I understand the talent data quality. | KPI: employees with ≥1 skill / total; validation rate; bar chart of skills added per month; horizontal bar of top 15 skills; per-employee skill-count table. | Must Have |
| ✅ KAN-124 | As an **admin**, I want an Org Chart tab with headcount KPIs, org depth, span of control, headcount growth line chart, and org-chart page view trend so I understand structure health and feature usage. | KPIs: active headcount, manager count, avg span, max depth, org-chart views in period; headcount by department bar; headcount growth line; manager span-of-control sortable table. | Must Have |
| ✅ KAN-125 | As an **admin**, I want a Search tab showing top queries, zero-result rate, and a "zero-result terms" table so I can act on content gaps. | KPIs: total searches, unique searchers, zero-result rate; search volume over time; top-10 terms bar; full terms table; dedicated zero-result table. | Must Have |
| ✅ KAN-126 | As an **admin**, I want to filter all analytics by date preset (30d / 90d / 1yr) or a custom range so I can compare periods. | Pill buttons for presets; custom date range reveals two date inputs; filter change invalidates cache and reloads current tab data. | Must Have |
| ✅ KAN-127 | As a **Super Admin**, I want a company dropdown so I can view analytics for any onboarded company. | Company `<select>` shown only for `SYSTEM_ADMIN`; resolves to `?company_id=`; `PORTAL_ADMIN` and `HR_ADMIN` always see their own company. | Must Have |
| ✅ KAN-128 | As an **admin**, I want to download any tab's data as a CSV so I can share it in board meetings. | `/api/analytics/export/csv?section=<tab>` returns `text/csv` with correct filename; tested for vacation (employee drilldown) and search (top terms). | Must Have |
| ✅ KAN-129 | As an **admin**, I want to print any analytics view as a PDF using the browser print dialog. | Print button calls `window.print()`; `@media print` CSS hides sidebar, topbar, bell, and filter bar; all tab content visible; chart cards break-inside: avoid. | Should Have |
| ✅ KAN-130 | As an **admin**, I want filter state to be reflected in the URL so I can share a specific view with a colleague. | All filter params (`tab`, `range`, `start`, `end`, `company_id`, `group_by`) in query string via `history.replaceState`; page restores state on load. | Should Have |
| ✅ KAN-131 | As an **HR Admin**, I want read-only access to my company's analytics so I can track leave and skills without needing Company Admin rights. | `HR_ADMIN` added to `_ROLES` tuple in analytics route; sidebar "Analytics" link visible for HR_ADMIN; company always scoped to session. | Must Have |
| ✅ KAN-132 | As a **developer**, I want 24 unit tests covering all analytics endpoints so access control, data shape, CSV export, and date parsing are verified. | `TestAnalyticsPageAccess` (5), `TestAnalyticsOverview` (5), `TestAnalyticsVacation` (3), `TestAnalyticsSkills` (2), `TestAnalyticsOrg` (2), `TestAnalyticsSearch` (2), `TestAnalyticsExport` (3), `TestAnalyticsDateParsing` (2) — all passing. | Must Have |

---

## EP26 — Vacation Balance Visibility  —  ✅ Done
**ID:** KAN-133 · **Label:** `vacation` `ux` `balance`
**Description:** Surface the remaining balance for each vacation type wherever a leave decision is made — the type cards, the employee's request modal (live, as dates change), the manager's pending list, and the manager's review modal — so employees never over-request and managers can see entitlement impact before approving.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-133 | As an **employee**, I want each vacation type card to show how many days I have left so I can plan at a glance. | `/vacation` cards render **"X days left"** (in the type colour) next to "used / annual limit"; types with no cap show "No annual limit". | Must Have |
| ✅ KAN-134 | As an **employee**, I want the request modal to show my remaining balance for the selected type, updating as I pick dates, so I know the impact before submitting. | Selecting a type shows *"N of MAX days remaining this year"*; after dates it adds *"this request uses D days → R will remain"*; panel turns **red with a warning** when D > remaining. | Must Have |
| ✅ KAN-135 | As a **manager**, I want each pending request to show the employee's remaining balance for that type so I can spot over-allocation in the list. | `/api/vacation/team-pending` returns `max_days` + `used_days`; pending row shows *"used/limit left"* and flags **"⚠ over limit"** in red when exceeded. | Must Have |
| ✅ KAN-136 | As a **manager**, I want the approve/reject modal to state the balance and post-approval remainder so my decision is informed. | Review modal shows *"<name> has N of MAX <type> days left. Approving this D-day request leaves R days."*; red warning when it would exceed the limit. | Must Have |

---

## EP27 — Employee Position Change Workflow  —  ✅ Done
**ID:** KAN-137 · **Label:** `org` `workflow` `approval` `drag-drop`
**Description:** Managers, HR, and Portal Admins move an employee to a new business unit, functional unit (department), location, and/or reporting manager by **dragging a card in the Organisation Tree**. The move is a request that flows through a **company-configurable, multi-level, sequential approval chain** (each level a role or a named person) and is only applied after the final approval. Individual employees can never initiate their own move. Backed by four tables (`org_change_workflows`, `org_change_workflow_steps`, `org_change_requests`, `org_change_approvals`) and a new `org_change` portal feature.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-137 | As a **manager**, I want to drag an employee onto another person in the Org Tree to propose a move so the change starts where I already work. | `.ft-card` is `draggable` only when `has_feature_access('org_change','w')`; dropping S on T opens a "Request Position Change" modal pre-filled from T (new manager + unit/location). | Must Have |
| ✅ KAN-138 | As a **requester**, I want to adjust the proposed business unit, department, location, and manager and give a reason before submitting so the request is accurate. | Modal selects populated from `/api/org-change/prefill` (company-scoped); reason is mandatory; submit `POST /api/org-change/request`; banner states nothing changes until approved. | Must Have |
| ✅ KAN-139 | As the **system**, I want to prevent an individual employee from initiating their own move so moves are always manager-driven. | `POST /api/org-change/request` gated by `org_change` (write); requester must manage the subject (solid-line) **or** be HR/Portal/System admin, else `403`; plain `EMPLOYEE` blocked. | Must Have |
| ✅ KAN-140 | As a **Portal Admin**, I want to configure how many approval levels a move needs and who approves each so the workflow matches our governance. | `/admin/org-change-workflow` editor adds/removes ordered levels; each level is **Role** (company role) or **Person** (employee); replace-all save via `POST /api/admin/org-change-workflow`. | Must Have |
| ✅ KAN-141 | As an **approver**, I want to see only the requests waiting at a step I can decide so my queue is relevant. | `/api/org-change/pending` returns requests where the **current** step matches the caller's role or employee id; shown in "Pending My Approval" with the from→to diff and "Level X / N". | Must Have |
| ✅ KAN-142 | As an **approver**, I want to approve or reject with a note so the next level or the requester understands the decision. | `POST /api/org-change/<id>/decide` records the step decision; approve with more levels advances `current_step`; final approve applies the change; reject stops the chain. | Must Have |
| ✅ KAN-143 | As the **system**, I want approvals to be strictly sequential and any rejection to stop the chain so partial moves never occur. | Level N+1 is only notified after level N approves; a single reject sets `status=REJECTED` and applies **no** change; verified in tests and end-to-end. | Must Have |
| ✅ KAN-144 | As the **system**, I want the final approval to actually move the employee so the org data reflects the decision. | `apply_change` sets old `employee_org_assignments.is_current=FALSE`, inserts a new current row (BU/FU/location, cost centre carried), and re-points the `SOLID_LINE` manager when changed. | Must Have |
| ✅ KAN-145 | As a **requester and employee**, I want to be notified at every step so I know the status. | In-app notifications on submit, each level pass, final approve, and reject (`ORG_CHANGE_*` events, link `/org-change`) to requester; subject notified on final approve and reject. | Must Have |
| ✅ KAN-146 | As a **requester**, I want to see my requests and cancel a pending one so I stay in control. | "My Requests" tab shows status + current level; `POST /api/org-change/<id>/cancel` allowed for the requester or an admin on `PENDING` only. | Should Have |
| ✅ KAN-147 | As a **developer**, I want unit tests covering permissions and the sequential engine so regressions are caught pre-commit. | `tests/test_org_change.py` (17): initiator matrix, `decide` advance/reject/final, approver eligibility, `apply_change` SQL, `create_request` notifications, workflow save; full suite **4,511 passing**. | Must Have |

---

# Architecture Review Backlog (EP28–EP34)

> Proposed epics from the `architect-reviewer` agent's audit. Source: `docs/ARCHITECTURE_REVIEW.md`.
> Priorities are framed for a **demo/local** app today: security items are **Must Have (pre-prod)** —
> required before any real deployment, not live incidents. Each story cites its review finding (`Fn`).
>
> **Delivered so far** (branch `chore/arch-review-and-hardening`, PR #2): **KAN-152** secure runtime
> defaults · **KAN-154 / KAN-157** missing indexes (migration 07) · **KAN-150** output escaping (4 of the
> highest-traffic screens; remainder → KAN-173) · **KAN-165** authoritative `schema.sql` baseline ·
> **KAN-169** GitHub Actions CI. Status shown in the Priority column below (✅ Done · 🟡 Partial).

## EP28 — Security Hardening  —  🟡 In progress
**ID:** KAN-148 · **Label:** `security` `hardening` `pre-prod`
**Description:** Close the authentication, CSRF, and output-escaping gaps and harden session, config, and
upload handling before the portal is exposed beyond local/demo use. Sourced from review findings F1–F5, F31.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-148 | As the **product owner**, I want real authentication (password hash / SSO-OIDC / signed magic-link) so a session cannot be minted from an email address alone. (F1) | Login requires a verified factor; no session issued on email-only match; the login page no longer renders real user emails to anonymous visitors; existing tests updated. | Must Have (pre-prod) |
| ⬜ KAN-149 | As the **system**, I want CSRF protection on every state-changing endpoint so cross-site requests cannot act as a logged-in user. (F2) | Flask-WTF `CSRFProtect` (or a double-submit token for JSON) added as a real dependency; token required on all POST/PUT/DELETE (~44 routes); `api.js` sends the token; tests cover accept/reject. | Must Have (pre-prod) |
| 🟡 KAN-150 | As the **system**, I want all dynamic values escaped before insertion into the DOM so stored data cannot execute as script. (F3) | Every `innerHTML` build routes through a shared `escapeHtml`/safe-`html\`\`` helper (or `textContent`); directory, org-tree, team, my-team, admin panels covered; regression test with a `<img onerror>` name renders inert. | 🟡 Partial (directory, org-tree, team, my-team done via global `escH()`; admin/profile/search/register → KAN-173) |
| ⬜ KAN-151 | As the **system**, I want company HTML and logo uploads sanitized so a portal admin cannot inject active content to all employees. (F4) | `header_html`/`footer_html` sanitized on write (allowlist) or rendered as text (drop `| safe`); `svg` removed from allowed uploads (or rasterized); uploads served with `Content-Disposition: attachment`; content-type/magic-byte check added. | Must Have (pre-prod) |
| ✅ KAN-152 | As the **operator**, I want secure runtime defaults so a misconfigured deploy fails safe. (F5) | App raises if `SECRET_KEY` unset outside dev; `SESSION_COOKIE_SECURE/SAMESITE/HTTPONLY` set; `debug` driven by env (default off); `MAX_CONTENT_LENGTH` caps request/upload size. | ✅ Done (`app/config.py`, `run.py`) |
| ⬜ KAN-153 | As the **operator**, I want required DB configuration with no personal defaults so missing config is caught, not masked. (F31) | `app/config.py` requires `PGUSER`/`PGDATABASE` (no `'samirroy'` default); missing values raise a clear error at startup. | Should Have |

---

## EP29 — Data Layer & Query Performance  —  🟡 In progress
**ID:** KAN-154 · **Label:** `database` `performance` `sql`
**Description:** Remove the seq-scans and N+1s on hot paths, make multi-statement writes atomic, and stop
over-fetching the directory. Sourced from F6, F8, F22, F23, F24.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-154 | As a **user**, I want dashboard/directory/analytics queries to use an index on `employees.company_id` so they don't seq-scan the whole table. (F6) | Composite `(company_id, employment_status)` index added (supersedes low-value `idx_employees_status`); `EXPLAIN ANALYZE` shows index usage on the directory + dashboard queries. | ✅ Done (`database/migrations/07_perf_indexes.sql`) |
| ⬜ KAN-155 | As the **system**, I want composite writes to be atomic so a mid-loop failure cannot leave partial data. (F8) | A `transaction()` context manager (single commit/rollback) is added and used by vacation-type create/edit and org-change apply; per-row-loop commits removed; failure rolls back the whole unit; read paths no longer sit idle-in-transaction. | Must Have |
| ⬜ KAN-156 | As a **user**, I want list/analytics pages to avoid N+1 queries so they stay fast as data grows. (F22) | Analytics overview replaces the per-feature COUNT loop with one `GROUP BY route`; vacation page computes used-days for all types in one `GROUP BY`; team-pending replaces the per-row correlated subselect with a single windowed/join query. | Should Have |
| ✅ KAN-157 | As the **system**, I want indexes on the org/vacation foreign keys that are filtered/joined so those scans use an index. (F23) | `(company_id)` indexes on `business_units`/`locations`/`functional_units`; `idx` on `vacation_requests(vacation_type_id)`; confirmed via `EXPLAIN`. | ✅ Done (migration 07) |
| ⬜ KAN-158 | As a **user**, I want the employee directory paginated with a light list projection so a large company doesn't load everyone (with full skills/certs) at once. (F24) | Directory API paginates; a lightweight list query is separated from the detail query; skills/cert `JSON_AGG` only run for the detail view; serialization moved toward psycopg2 type adapters. | Should Have |

---

## EP30 — Scalability & Runtime  —  ⬜ Planned
**ID:** KAN-159 · **Label:** `scalability` `runtime` `ops`
**Description:** Make the app ready to run multi-worker / multi-instance: pool DB connections, bound
background work, share upload storage, push instead of poll, and slim the session. Sourced from F7, F16, F17, F18, F19, F25.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-159 | As the **operator**, I want a DB connection pool so requests reuse connections instead of opening one each. (F7) | `psycopg2.pool.ThreadedConnectionPool` (or PgBouncer) sits behind `get_db()`; connection open-rate under load drops sharply; background threads draw from the pool. | Must Have |
| ⬜ KAN-160 | As a **user**, I want feature-access cached across requests so it isn't re-joined on every page render. (F16) | Short-TTL process cache keyed by `(sorted(roles), company_id)`, invalidated on permission writes; per-request `g` cache retained; correctness preserved (SYSTEM_ADMIN bypass, company scoping). | Should Have |
| ⬜ KAN-161 | As the **system**, I want notification/pending counts pushed or combined rather than two polls per user every 60s. (F17) | Bell uses one endpoint returning both counts; polling is visibility-gated (or replaced with SSE/websocket); idle tabs stop querying. | Should Have |
| ⬜ KAN-162 | As the **operator**, I want uploaded logos in shared object storage so they survive across instances. (F18) | Logos stored in S3/GCS (or a shared volume) and served via signed URL/CDN; an upload on one instance is visible from another. | Should Have |
| ⬜ KAN-163 | As the **system**, I want bounded background workers so a spike or slow SMTP can't spawn unbounded threads/connections or lose work on restart. (F19) | Email + page-view logging go through a bounded worker pool / queue with backpressure and basic retry; work is not silently dropped on SIGTERM. | Should Have |
| ⬜ KAN-164 | As the **system**, I want only `company_id` in the session (not branding HTML) so the cookie can't overflow and branding can't go stale. (F25) | `session['branding']` removed; branding loaded server-side via a cached lookup (pairs with KAN-160); cookie size bounded. | Could Have |

---

## EP31 — Schema Source of Truth & Migrations  —  🟡 In progress
**ID:** KAN-165 · **Label:** `database` `migrations` `devex`
**Description:** Make the database reproducible from the repo and adopt a real migration tool so schema drift
can't happen silently (the `org_change` tables currently exist only in migration 06). Sourced from F9.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ✅ KAN-165 | As a **developer**, I want one authoritative schema so a fresh database matches production, including all currently-missing tables. (F9) | A single canonical schema (e.g. `pg_dump --schema-only` baseline or complete numbered migrations) recreates every live table — `companies`, `employees.company_id`, `vacation_*`, `page_views`, `user_notifications`, `org_change_*`, etc.; README bootstrap updated to use it. | ✅ Done (`database/schema.sql` + `seed_rbac.sql`; README updated) |
| ⬜ KAN-166 | As a **developer**, I want a migration tool with version tracking so applied migrations are recorded and ordered. (F9) | Alembic (or Flyway) adopted; existing migrations 02–06 folded into the tool; `alembic upgrade head` on a fresh DB yields the full schema. | Should Have |
| ⬜ KAN-167 | As a **developer**, I want a single owner for feature/role seeding so `setup_db.py` and `alter_table.sql` can't diverge. (F9) | `portal_features`/`role_feature_access` DDL+seed defined once; the other path references it; onboarding a company is unambiguous. | Should Have |

---

## EP32 — Testing & CI Hardening  —  🟡 In progress
**ID:** KAN-168 · **Label:** `testing` `ci` `quality`
**Description:** Add coverage the mocked suite can't provide — real-DB integration tests and a shared CI
pipeline — so SQL and schema are verified, not just string-matched. Sourced from F10, F11, F12.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-168 | As a **developer**, I want a real-DB integration test tier so SQL is executed against the actual schema. (F10) | Pytest tier spins up disposable Postgres (testcontainers or CI service container), applies schema+migrations, and exercises real routes/services; covers the org_change decide→apply flow asserting row state. | Must Have |
| ✅ KAN-169 | As a **team**, I want CI on every PR so a broken build/migration/test can't reach `main`. (F11) | GitHub Actions runs lint + full pytest + "build fresh DB from migrations then boot the app" smoke test; required status check; not bypassable like the local hook. | ✅ Done (`.github/workflows/ci.yml` — test + fresh-DB boot jobs) |
| ⬜ KAN-170 | As a **developer**, I want coverage measured with a floor so thin/untested modules are visible. (F12) | `pytest-cov` added; `--cov=app --cov-report=term-missing`; CI fails under an agreed floor; `email_service`/`page_tracker`/`skills_intelligence_service` gaps surfaced. | Should Have |
| ⬜ KAN-171 | As a **developer**, I want the mocked engine tests backed by behavior tests so they assert outcomes, not internal call order. (F10, testing #4) | The org_change (and vacation) approval flows have integration tests asserting final DB state; brittle SQL-substring/`side_effect`-ordering assertions supplemented rather than relied upon. | Should Have |

---

## EP33 — Frontend Modernization  —  ⬜ Planned
**ID:** KAN-172 · **Label:** `frontend` `refactor` `accessibility`
**Description:** Evolve the Jinja + vanilla-JS frontend without a rewrite: extract shared JS modules (making
output-escaping the default), fix accessibility, and add JS tests + asset versioning. Sourced from F3, F20, F21, F26, F27, F28. (Framework migration is explicitly deferred — see `ARCHITECTURE_REVIEW.md` Stage 3.)

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-172 | As a **developer**, I want shared JS in `static/js/` ES modules so logic isn't copy-pasted across 7+ templates. (F26) | `dom.js` (escapeHtml + safe `html\`\`` + `el`), `avatar.js`, `format.js`, `api.js` (`postJSON`/`getJSON` + CSRF header), `modal.js` created and loaded once; duplicated `avatarColor`/`initials`/`esc`/`fmt` removed from templates. | Should Have |
| ⬜ KAN-173 | As the **system**, I want escaping to be the default path in the shared modules so new code can't reintroduce XSS. (F3) | All `innerHTML` builders use the shared safe helper; a lint/check or code-review note discourages raw `innerHTML` with interpolation. | Should Have |
| ⬜ KAN-174 | As a **keyboard/screen-reader user**, I want to propose a position change without a mouse. (F20) | Org-tree cards expose a keyboard "Move…" affordance opening the same modal; `aria-grabbed`/live-region announcements; WCAG 2.1.1 satisfied for the flow. | Should Have |
| ⬜ KAN-175 | As a **screen-reader user**, I want modals with proper dialog semantics so focus and context behave. (F21) | Shared `modal.js` adds `role="dialog"`+`aria-modal`, a focus trap, Esc-to-close, and labelledby; adopted by all modals. | Should Have |
| ⬜ KAN-176 | As a **developer**, I want JS unit tests and cache-busted assets so client logic is verified and deploys don't serve stale files. (F27) | Vitest units on the pure helpers (avatar/format/escape); static assets get a build hash / `?v=`; optional esbuild minify step. | Could Have |
| ⬜ KAN-177 | As a **maintainer**, I want high-traffic inline styles moved to CSS classes and clickables made semantic so the UI is consistent and accessible. (F28) | Inline `style=` migrated to classes on the heaviest templates (start with `admin/panel.html`); non-semantic `onclick` divs replaced with `<button>`/`<a>` + `type`. | Could Have |

---

## EP34 — Architecture & Structure  —  ⬜ Planned
**ID:** KAN-178 · **Label:** `architecture` `refactor` `maintainability`
**Description:** Make the structure hold as the app grows: an application factory + Blueprints, a real service
layer, pinned dependencies, and a guard-decorator audit. Sourced from F13, F14, F15, F29, F30.

| Story ID | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| ⬜ KAN-178 | As a **developer**, I want a `create_app(config)` factory so the app can be built with test/staging/prod configs and isn't wired as an import side-effect. (F13) | `create_app` builds config, teardown, context processor, and route registration; `run.py` and tests use it; multiple app instances can coexist. | Should Have |
| ⬜ KAN-179 | As a **developer**, I want route modules as Blueprints so there's no shared-singleton import cycle and areas can carry prefixes/error handlers. (F14) | Each route module is a `Blueprint` registered in the factory; route→route imports (e.g. `company.py`→`admin.py`) removed; shared helpers moved to services. | Could Have |
| ⬜ KAN-180 | As a **developer**, I want pinned dependencies + a lockfile so builds are reproducible. (F15) | `requirements.txt` pins exact versions; a lockfile (`pip-compile`/`uv`) is committed; CI installs from the lock. | Should Have |
| ⬜ KAN-181 | As a **developer**, I want `helpers.py` split and business logic out of routes so modules are cohesive and testable. (F29) | `helpers.py` split into `services/{employees,org,vacation}` + `util/uploads`; `admin.py` split by sub-area; routes act as thin controllers. | Could Have |
| ⬜ KAN-182 | As a **maintainer**, I want a guard-decorator audit so authorization is consistent and documented. (F30) | Each `@require_roles` route reviewed; genuine feature pages converted to `@require_feature_access`; admin/config gates that stay role-based are documented (per `CLAUDE.md`, not blindly converted). | Could Have |
