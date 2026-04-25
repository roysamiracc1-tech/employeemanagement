# HR Portal — Jira Epics & User Stories

> **Jira Project:** EmployeeManagementKanban (KAN)
> **Board URL:** https://roysamiracc1-1777144763345.atlassian.net/jira/software/projects/KAN/boards
> All 62 issues (10 Epics + 52 Stories) are live in Jira. Status: **To Do**
> All items are **completed and deployed** to `main`.

---

## Epic Summary

| Jira Key | Epic | Stories |
|----------|------|---------|
| [KAN-2](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-2) | EP1 — Authentication & Session Management | KAN-12 · KAN-13 · KAN-14 · KAN-15 |
| [KAN-3](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-3) | EP2 — Role-Based Access Control (RBAC) | KAN-16 · KAN-17 · KAN-18 · KAN-19 |
| [KAN-4](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-4) | EP3 — Employee Registry & Directory | KAN-20 · KAN-21 · KAN-22 · KAN-23 · KAN-24 |
| [KAN-5](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-5) | EP4 — Employee Profile & Self-Service | KAN-25 · KAN-26 · KAN-27 · KAN-28 · KAN-29 · KAN-30 · KAN-31 |
| [KAN-6](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-6) | EP5 — Organisational Structure | KAN-32 · KAN-33 · KAN-34 · KAN-35 · KAN-36 |
| [KAN-7](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-7) | EP6 — Manager Self-Service | KAN-37 · KAN-38 |
| [KAN-8](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-8) | EP7 — Vacation & Leave Management | KAN-39 · KAN-40 · KAN-41 · KAN-42 · KAN-43 · KAN-44 · KAN-45 · KAN-46 · KAN-48 · KAN-49 · KAN-50 · KAN-51 |
| [KAN-9](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-9) | EP8 — Company Branding & Theming | KAN-52 · KAN-53 · KAN-54 · KAN-55 · KAN-56 · KAN-57 · KAN-58 |
| [KAN-10](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-10) | EP9 — Dashboard & Real-Time Metrics | KAN-59 · KAN-60 · KAN-61 · KAN-62 |
| [KAN-11](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-11) | EP10 — Work Anniversary Recognition | KAN-63 · KAN-64 |

---

## EPIC 1 — Authentication & Session Management
**Jira:** [KAN-2](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-2) · **Label:** `auth` `security`
**Description:** Secure login/logout with role-aware sessions. All portal activity requires authentication.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-12](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-12) | As an **employee**, I want to log in with my work email so I can access the portal. | Login accepts email; invalid email shows error; redirects to dashboard on success. | Must Have |
| [KAN-13](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-13) | As any **logged-in user**, I want my session to persist for 8 hours so I do not need to re-login constantly. | Session cookie TTL = 8 h; logout clears session immediately. | Must Have |
| [KAN-14](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-14) | As any **user**, I want to log out securely so no one else can access my account on shared devices. | `/logout` clears session and redirects to login. | Must Have |
| [KAN-15](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-15) | As a **developer/demo**, I want quick-access demo user tiles on the login page so testers can log in without credentials. | Login page shows up to 6 demo user cards; clicking one pre-fills email. | Should Have |

---

## EPIC 2 — Role-Based Access Control (RBAC)
**Jira:** [KAN-3](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-3) · **Label:** `rbac` `security`
**Description:** Eight distinct roles gate access to views and APIs. Roles are cumulative and checked server-side on every protected endpoint.

**Roles:** `SYSTEM_ADMIN` · `HR_ADMIN` · `SOLID_LINE_MANAGER` · `DOTTED_LINE_MANAGER` · `DEPARTMENT_HEAD` · `LOCATION_HEAD` · `HIRING_MANAGER` · `EMPLOYEE`

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-16](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-16) | As a **SYSTEM_ADMIN**, I want to assign and revoke roles for any user so I can control access. | Role edit modal on admin panel; changes take effect immediately; own roles cannot be removed. | Must Have |
| [KAN-17](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-17) | As a **SYSTEM_ADMIN**, I want to enable or disable a user account so ex-employees cannot log in. | Toggle active/inactive; inactive users are rejected at login with clear error. | Must Have |
| [KAN-18](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-18) | As a **non-admin user**, I want to be redirected with an error message if I try to access a restricted page. | HTTP redirect to dashboard with flash error; no data leaked. | Must Have |
| [KAN-19](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-19) | As a **SYSTEM_ADMIN**, I want the admin panel to show all users with their roles and last-login timestamp. | Admin panel loads all users; shows role badges; shows "Never" if no login recorded. | Should Have |

---

## EPIC 3 — Employee Registry & Directory
**Jira:** [KAN-4](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-4) · **Label:** `employees` `directory`
**Description:** Central record of all employees with full personal, employment, and org data. Searchable, filterable directory available to authorised roles.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-20](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-20) | As an **HR_ADMIN / SYSTEM_ADMIN**, I want to register a new employee through a guided multi-step form so data is captured completely. | 6-step form: Personal Info → Employment → Organisation → Reporting → Skills → Portal Access; auto-generates EMP-XXX number; creates all records atomically. | Must Have |
| [KAN-21](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-21) | As a **registrar**, I want the employee number to be auto-generated sequentially so I don't assign duplicates. | `_next_employee_number()` selects MAX and increments; zero-pads to 3 digits. | Must Have |
| [KAN-22](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-22) | As an **HR_ADMIN**, I want to search and filter the employee directory by name, location, business unit, and employment type. | Filters applied server-side; results paginate at configurable rows/page. | Must Have |
| [KAN-23](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-23) | As a **SYSTEM_ADMIN / HR_ADMIN**, I want to see each employee's manager, location, skills, and certifications in the directory row. | Directory table includes manager pill, location badge, skill bars, cert count. | Should Have |
| [KAN-24](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-24) | As a **registrar**, I want to assign solid-line and dotted-line managers to a new employee during registration. | Step 4 lets user search and select solid/dotted manager; records written to `manager_relationships` with `is_current=true`. | Must Have |

---

## EPIC 4 — Employee Profile & Self-Service
**Jira:** [KAN-5](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-5) · **Label:** `profile` `self-service`
**Description:** Every employee can view their own profile and self-maintain skills, certifications, and gender. Managers and admins see read-only profiles for others.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-25](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-25) | As any **employee**, I want to view my complete profile including employment details, org placement, manager, skills, and certifications. | `/profile` loads own profile; `/profile/<id>` loads others; `is_own` flag controls edit UI. | Must Have |
| [KAN-26](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-26) | As an **employee**, I want to add skills to my profile and self-rate each on a 1–10 scale so my competencies are visible. | Skill modal with 🌱💡⚡🏆 level buttons; POST `/api/profile/skills`; list refreshes in-page. | Must Have |
| [KAN-27](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-27) | As an **employee**, I want to remove a skill from my profile so outdated entries do not mislead others. | DELETE `/api/profile/skills/<id>`; list updated in-page. | Must Have |
| [KAN-28](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-28) | As an **employee**, I want to add certifications with issuer, dates, and credential URL so my qualifications are recorded. | POST `/api/profile/certifications`; accepts cert name, provider, dates, URL; in-page reload. | Must Have |
| [KAN-29](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-29) | As an **employee**, I want to edit and remove my certifications so I keep them current. | PUT and DELETE `/api/profile/certifications/<id>`; in-page update. | Must Have |
| [KAN-30](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-30) | As an **employee**, I want to record my gender on my profile so my vacation eligibility is calculated correctly. | Gender dropdown (Male/Female/Other) with auto-save on change via POST `/api/profile/gender`. | Must Have |
| [KAN-31](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-31) | As a **SYSTEM_ADMIN / HR_ADMIN**, I want to validate an employee's skill rating so the profile shows verified competencies. | POST `/api/admin/validate-skill`; status → `VALIDATED`; skill bar turns green. | Should Have |

---

## EPIC 5 — Organisational Structure
**Jira:** [KAN-6](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-6) · **Label:** `org` `hierarchy`
**Description:** Multi-level org model: Companies → Business Units → Functional Units → Cost Centres → Locations.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-32](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-32) | As a **SYSTEM_ADMIN**, I want to register companies so multiple entities can share the portal. | `/admin/companies` CRUD; company has name, industry, website, HQ, description, active flag. | Must Have |
| [KAN-33](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-33) | As an **employee**, I want to view my company's overview page showing headcount, locations, and business units. | `/company` shows stats, BU breakdown, location breakdown; accessible to all employees. | Should Have |
| [KAN-34](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-34) | As an **HR_ADMIN**, I want to assign employees to business units, functional units, locations, and cost centres during onboarding. | Registration step 3 has cascading BU → FU selectors; `employee_org_assignments` written with `is_current=true`. | Must Have |
| [KAN-35](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-35) | As a **manager or admin**, I want to view the org hierarchy as an interactive tree so I can understand reporting lines. | `/org-tree` renders recursive tree via CTE (max 10 levels); nodes clickable; expand/collapse; admin can pick any root or Full Org. | Must Have |
| [KAN-36](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-36) | As a **manager**, I want to see pending vacation badges on org tree nodes so I know which reportees need action. | Orange ⏳ badge on nodes with pending requests; links to `/vacation/team`. | Should Have |

---

## EPIC 6 — Manager Self-Service
**Jira:** [KAN-7](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-7) · **Label:** `manager` `team`
**Description:** Managers have a dedicated team view showing all direct reports with enriched data and can take management actions from a single screen.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-37](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-37) | As a **manager**, I want to see all my direct reports in a card layout with their role, location, skills, and manager links. | `/my-team` shows cards for all SOLID_LINE direct reports; each card has profile link and management quick-actions. | Must Have |
| [KAN-38](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-38) | As a **manager**, I want to see a pending vacation count badge on each team member's card so I can act without leaving the team page. | `pendingCounts` fetched on page load; badge shows ⏳ N vacation req with link to `/vacation/team`. | Should Have |

---

## EPIC 7 — Vacation & Leave Management
**Jira:** [KAN-8](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-8) · **Label:** `vacation` `leave` `hr-process`
**Description:** Company-defined leave types with location scoping and eligibility rules. Full request → approval workflow with manager review queue and upcoming schedule view.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-39](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-39) | As a **SYSTEM_ADMIN**, I want to define vacation types per company (e.g. Annual Leave, Sick Leave) with day limits and paid/unpaid flags. | `/admin/vacation-types` CRUD; name, max days/year, is_paid, colour, description stored per company. | Must Have |
| [KAN-40](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-40) | As a **SYSTEM_ADMIN**, I want to make a vacation type available only to employees in specific locations. | Multi-select locations; stored in `vacation_type_locations`; company-wide types have no location entries. | Must Have |
| [KAN-41](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-41) | As a **SYSTEM_ADMIN**, I want to add eligibility rules (gender, minimum tenure) to vacation types so the right employees see them. | Step 4 Rules builder; supports `GENDER_EQ`, `MIN_TENURE_MONTHS`, `MIN_TENURE_YEARS`; AND logic. | Must Have |
| [KAN-42](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-42) | As an **employee**, I want to see only the vacation types I am eligible for so I don't waste time applying for unavailable leave. | Location + ALL rules must pass; rule labels shown as purple badges; ineligible types hidden. | Must Have |
| [KAN-43](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-43) | As an **employee**, I want to see my used vs. remaining days for each vacation type so I know my balance. | Type cards show used/max progress bar; remaining shown in request modal; counts PENDING+APPROVED. | Must Have |
| [KAN-44](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-44) | As an **employee**, I want to submit a vacation request with start/end dates and a note so my manager is notified. | Request modal; weekday count verified server-side; manager auto-set from solid-line; annual limit enforced. | Must Have |
| [KAN-45](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-45) | As an **employee**, I want to cancel a PENDING request if my plans change. | DELETE `/api/vacation/request/<id>`; only PENDING status can be cancelled; status → CANCELLED. | Must Have |
| [KAN-46](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-46) | As an **employee**, I cannot submit a vacation request if I have no manager assigned. | Warning banner shown; request button disabled; API returns 400 with reason. | Must Have |
| [KAN-48](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-48) | As an **employee**, I want to see all my past and current requests with their status and manager note. | Request history table shows type, dates, days, status badge, manager note, cancel button for PENDING. | Must Have |
| [KAN-49](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-49) | As a **manager**, I want to see all pending vacation requests from my reportees and approve or reject them with a note. | Pending tab; review modal with optional note; POST `/api/vacation/review/<id>`; only PENDING reviewable. | Must Have |
| [KAN-50](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-50) | As a **manager**, I want to see my team's upcoming approved leave in a calendar-like schedule so I can plan coverage. | Upcoming tab groups by month; "● On leave" indicator for currently active requests. | Should Have |
| [KAN-51](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-51) | As a **manager**, I cannot approve a request that has already been reviewed. | API validates status == PENDING before update; returns 400 if already actioned. | Must Have |

---

## EPIC 8 — Company Branding & Theming
**Jira:** [KAN-9](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-9) · **Label:** `branding` `ui` `personalisation`
**Description:** Admins configure per-company visual identity. Employees choose their own light/dark preference. All settings persist and apply immediately on next page load.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-52](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-52) | As a **SYSTEM_ADMIN**, I want to upload a company logo so it appears in the sidebar for all employees of that company. | Drag-and-drop upload; saved to `static/uploads/logos/`; old file deleted on replacement; PNG/JPG/SVG/WebP max 2 MB. | Must Have |
| [KAN-53](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-53) | As a **SYSTEM_ADMIN**, I want to optionally provide an external logo URL instead of uploading a file. | Tab switcher between Upload File and External URL; live preview; uploaded file takes priority. | Should Have |
| [KAN-54](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-54) | As a **SYSTEM_ADMIN**, I want to set a primary theme colour for my company so the portal reflects our brand identity. | Colour picker + hex input + 8 quick presets; saved as `theme_color`; injected as `--primary` CSS variable. | Must Have |
| [KAN-55](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-55) | As a **SYSTEM_ADMIN**, I want to add a company-wide header banner (HTML) above all portal pages for announcements. | `header_html` field; rendered above all pages for company employees; inline preview button. | Should Have |
| [KAN-56](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-56) | As a **SYSTEM_ADMIN**, I want to add a company-wide footer (HTML) below all pages for legal links and support contacts. | `footer_html` field; rendered at bottom of all pages; clear button available. | Should Have |
| [KAN-57](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-57) | As any **employee**, I want to switch between light and dark mode so I can work comfortably in different environments. | Toggle button in topbar; instant CSS variable swap; POST `/api/user/theme` persists to DB; restored on next login. | Must Have |
| [KAN-58](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-58) | As an **employee**, my branding is refreshed in my session after the admin updates the company record. | `admin_company_edit` POST re-fetches and updates `session['branding']` immediately. | Should Have |

---

## EPIC 9 — Dashboard & Real-Time Metrics
**Jira:** [KAN-10](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-10) · **Label:** `dashboard` `analytics`
**Description:** Role-aware dashboard with live stat cards, drill-down filtering, and configurable auto-refresh intervals per role.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-59](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-59) | As any **logged-in user**, I want to see a dashboard with the key stats relevant to my role so I get an immediate status overview. | Stats differ by role; SYSTEM_ADMIN sees all-company counts; managers see team counts; employees see personal stats. | Must Have |
| [KAN-60](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-60) | As a **dashboard user**, I want stat cards to auto-refresh periodically so I see live data without reloading. | Refresh interval configurable per role; JS polls `/api/dashboard/stats`; changed values animate (flash green). | Should Have |
| [KAN-61](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-61) | As a **dashboard user**, I want clickable stat cards that filter the employee directory to the relevant subset. | Clicking a stat card navigates to `/directory?filter=<value>`; directory pre-applies the filter. | Should Have |
| [KAN-62](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-62) | As a **SYSTEM_ADMIN**, I want to configure per-role refresh intervals so I can balance data freshness against server load. | POST `/api/admin/refresh-settings`; persisted to `widget_refresh_settings`; applied on next page load. | Nice to Have |

---

## EPIC 10 — Work Anniversary Recognition
**Jira:** [KAN-11](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-11) · **Label:** `engagement` `hr`
**Description:** Automatic work anniversary detection with animated visual indicator on employee names throughout the portal.

| Jira Key | User Story | Acceptance Criteria | Priority |
|----------|-----------|---------------------|----------|
| [KAN-63](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-63) | As a **manager or admin**, I want to see a visual indicator next to employees whose work anniversaries are upcoming so I can acknowledge them. | 🎂 badge computed from `join_date`; urgency levels: normal (>7 days), soon (≤7 days), urgent (today/tomorrow); animated per urgency. | Should Have |
| [KAN-64](https://roysamiracc1-1777144763345.atlassian.net/browse/KAN-64) | As a **manager**, I want to hover over the badge to see the exact anniversary date and tenure. | Tooltip shows "N-year anniversary on DD MMM YYYY" on hover with smooth animation. | Should Have |
