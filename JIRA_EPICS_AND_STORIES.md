# HR Portal — Jira Epics & User Stories

> All items listed are **completed and deployed** to `main`.
> Priority, story points, and acceptance criteria are included per story.

---

## EPIC 1 — Authentication & Session Management
**Label:** `auth` `security`
**Description:** Secure login/logout with role-aware sessions. All portal activity requires authentication.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 1.1 | As an **employee**, I want to log in with my work email so I can access the portal. | Login accepts email (no password in dev); invalid email shows error; redirects to dashboard on success. | Must Have |
| 1.2 | As any **logged-in user**, I want my session to persist for 8 hours so I do not need to re-login constantly. | Session cookie TTL = 8 h; logout clears session immediately. | Must Have |
| 1.3 | As any **user**, I want to log out securely so no one else can access my account on shared devices. | `/logout` clears session and redirects to login. | Must Have |
| 1.4 | As a **developer/demo**, I want quick-access demo user tiles on the login page so testers can log in without credentials. | Login page shows up to 6 demo user cards; clicking one pre-fills email. | Should Have |

---

## EPIC 2 — Role-Based Access Control (RBAC)
**Label:** `rbac` `security`
**Description:** Eight distinct roles gate access to views and APIs. Roles are cumulative and checked server-side on every protected endpoint.

**Roles defined:**
- `SYSTEM_ADMIN` — full portal control
- `HR_ADMIN` — employee & org management
- `SOLID_LINE_MANAGER` — direct line manager
- `DOTTED_LINE_MANAGER` — matrix/project manager
- `DEPARTMENT_HEAD` — dept visibility
- `LOCATION_HEAD` — office visibility
- `HIRING_MANAGER` — recruitment context
- `EMPLOYEE` — base role; all portal users

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 2.1 | As a **SYSTEM_ADMIN**, I want to assign and revoke roles for any user so I can control access. | Role edit modal on admin panel; changes take effect immediately; own roles cannot be removed. | Must Have |
| 2.2 | As a **SYSTEM_ADMIN**, I want to enable or disable a user account so ex-employees cannot log in. | Toggle active/inactive; inactive users are rejected at login with clear error. | Must Have |
| 2.3 | As a **non-admin user**, I want to be redirected with an error message if I try to access a restricted page. | HTTP redirect to dashboard with flash error; no data leaked. | Must Have |
| 2.4 | As a **SYSTEM_ADMIN**, I want the admin panel to show all users with their roles and last-login timestamp. | Admin panel loads all users; shows role badges; shows "Never" if no login recorded. | Should Have |

---

## EPIC 3 — Employee Registry & Directory
**Label:** `employees` `directory`
**Description:** Central record of all employees with full personal, employment, and org data. Searchable, filterable directory available to authorised roles.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 3.1 | As an **HR_ADMIN / SYSTEM_ADMIN**, I want to register a new employee through a guided multi-step form so data is captured completely. | 6-step form: Personal Info → Employment → Organisation → Reporting → Skills → Portal Access; auto-generates EMP-XXX number; creates employee record + org assignment + manager relationships + skills + user account atomically. | Must Have |
| 3.2 | As a **registrar**, I want the employee number to be auto-generated sequentially so I don't assign duplicates. | `_next_employee_number()` selects MAX and increments; zero-pads to 3 digits. | Must Have |
| 3.3 | As an **HR_ADMIN**, I want to search and filter the employee directory by name, location, business unit, and employment type. | Directory page filters are applied server-side; results paginate at configurable rows/page. | Must Have |
| 3.4 | As a **SYSTEM_ADMIN / HR_ADMIN**, I want to see each employee's manager, location, skills, and certifications in the directory row. | Directory table includes manager pill, location badge, skill bars, cert count. | Should Have |
| 3.5 | As a **registrar**, I want to assign solid-line and dotted-line managers to a new employee during registration. | Step 4 (Reporting) lets user search and select solid/dotted manager; records written to `manager_relationships` with `is_current=true`. | Must Have |

---

## EPIC 4 — Employee Profile & Self-Service
**Label:** `profile` `self-service`
**Description:** Every employee can view their own profile and self-maintain skills, certifications, and gender. Managers and admins see read-only profiles for others.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 4.1 | As any **employee**, I want to view my complete profile including employment details, org placement, manager, skills, and certifications. | `/profile` loads own profile; `/profile/<id>` loads others; `is_own` flag controls edit UI. | Must Have |
| 4.2 | As an **employee**, I want to add skills to my profile and self-rate each on a 1–10 scale so my competencies are visible. | Skill modal with 🌱💡⚡🏆 level buttons; POST `/api/profile/skills`; list refreshes in-page without full reload. | Must Have |
| 4.3 | As an **employee**, I want to remove a skill from my profile so outdated entries do not mislead others. | DELETE `/api/profile/skills/<id>`; list updated in-page. | Must Have |
| 4.4 | As an **employee**, I want to add certifications with issuer, dates, and credential URL so my qualifications are recorded. | POST `/api/profile/certifications`; accepts cert name, provider, issued/expiry date, URL; in-page reload. | Must Have |
| 4.5 | As an **employee**, I want to edit and remove my certifications so I keep them current. | PUT `/api/profile/certifications/<id>`; DELETE same path; in-page update. | Must Have |
| 4.6 | As an **employee**, I want to record my gender on my profile so my vacation eligibility is calculated correctly. | Gender dropdown (Male/Female/Other) with auto-save on change; POST `/api/profile/gender`. | Must Have |
| 4.7 | As a **SYSTEM_ADMIN / HR_ADMIN**, I want to validate an employee's skill rating so the profile shows verified competencies. | POST `/api/admin/validate-skill`; validation status changes from `SELF_ASSESSED` → `VALIDATED`; skill bar turns green. | Should Have |

---

## EPIC 5 — Organisational Structure
**Label:** `org` `hierarchy`
**Description:** Multi-level org model: Companies → Business Units → Functional Units → Cost Centres → Locations. Employees are assigned to a node at any level.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 5.1 | As a **SYSTEM_ADMIN**, I want to register companies so multiple entities can share the portal. | `/admin/companies` CRUD; each company has name, industry, website, HQ, description, active flag. | Must Have |
| 5.2 | As an **employee**, I want to view my company's overview page showing headcount, locations, and business units. | `/company` shows stats, BU breakdown, location breakdown; accessible to all employees. | Should Have |
| 5.3 | As an **HR_ADMIN**, I want to assign employees to business units, functional units, locations, and cost centres during onboarding. | `employee_org_assignments` table; cascade selectors in registration form (BU → FU filtering via JS). | Must Have |
| 5.4 | As a **manager or admin**, I want to view the org hierarchy as an interactive tree so I can understand reporting lines. | `/org-tree` renders recursive tree via CTE; nodes are clickable links to profile; expand/collapse per node; admin can pick any root or "Full Org". | Must Have |
| 5.5 | As a **manager**, I want to see pending vacation badges on org tree nodes so I know which reportees need action. | `loadPendingCounts()` fetches counts before tree renders; orange ⏳ badge shown on nodes with pending requests. | Should Have |

---

## EPIC 6 — Manager Self-Service
**Label:** `manager` `team`
**Description:** Managers have a dedicated team view showing all direct reports with enriched data, and can take management actions from a single screen.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 6.1 | As a **manager**, I want to see all my direct reports in a card layout with their role, location, skills, and manager links. | `/my-team` shows cards for all SOLID_LINE direct reports; each card has profile link and management quick-actions. | Must Have |
| 6.2 | As a **manager**, I want to see a pending vacation count badge on each team member's card so I can act without leaving the team page. | `pendingCounts` fetched on page load; badge shows ⏳ N vacation req with link to `/vacation/team`. | Should Have |

---

## EPIC 7 — Vacation & Leave Management
**Label:** `vacation` `leave` `hr-process`
**Description:** Company-defined leave types with location scoping and eligibility rules. Full request → approval workflow with manager review queue and upcoming schedule view.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 7.1 | As a **SYSTEM_ADMIN**, I want to define vacation types per company (e.g. Annual Leave, Sick Leave) with day limits and paid/unpaid flags. | `/admin/vacation-types` CRUD; name, max days/year, is_paid, colour, description stored per company. | Must Have |
| 7.2 | As a **SYSTEM_ADMIN**, I want to make a vacation type available only to employees in specific locations. | Vacation type form includes multi-select locations; stored in `vacation_type_locations`; company-wide types have no location entries. | Must Have |
| 7.3 | As a **SYSTEM_ADMIN**, I want to add eligibility rules (gender, minimum tenure) to vacation types so the right employees see them. | Step 4 "Rules" in vacation type form; dynamic rule builder with rule type + value; rules stored in `vacation_type_rules`. | Must Have |
| 7.4 | As an **employee**, I want to see only the vacation types I am eligible for so I don't waste time applying for unavailable leave. | `_vacation_types_for_employee()` filters by company → location → ALL rules (AND logic); ineligible types hidden. | Must Have |
| 7.5 | As an **employee**, I want to see my used vs. remaining days for each vacation type so I know my balance. | Cards show used/max progress bar; remaining shown in request modal dropdown; checked against `vacation_requests` (PENDING + APPROVED). | Must Have |
| 7.6 | As an **employee**, I want to submit a vacation request with start/end dates and a note so my manager is notified. | Request modal; weekday count computed client-side and server-side; POST `/api/vacation/request`; manager auto-set from solid-line relationship. | Must Have |
| 7.7 | As an **employee**, I want to cancel a PENDING request if my plans change. | DELETE `/api/vacation/request/<id>`; only PENDING status can be cancelled; status → CANCELLED. | Must Have |
| 7.8 | As an **employee**, I cannot submit a vacation request if I have no manager assigned. | Warning banner shown; request button disabled; API returns 400 with reason. | Must Have |
| 7.9 | As an **employee**, I want to see all my past and current requests with their status and manager note. | Request history table on `/vacation`; shows type, dates, days, status badge, manager note, cancel button for PENDING. | Must Have |
| 7.10 | As a **manager**, I want to see all pending vacation requests from my reportees and approve or reject them with a note. | `/vacation/team` → Pending tab; review modal with optional note; POST `/api/vacation/review/<id>` with action=approve/reject; requestor's history updates. | Must Have |
| 7.11 | As a **manager**, I want to see my team's upcoming approved leave in a calendar-like schedule so I can plan coverage. | Upcoming tab groups approved/pending requests by month; "● On leave" indicator for currently active requests. | Should Have |
| 7.12 | As a **manager**, I cannot approve a request that has already been reviewed. | API validates status == PENDING before update; returns 400 if already actioned. | Must Have |

---

## EPIC 8 — Company Branding & Theming
**Label:** `branding` `ui` `personalisation`
**Description:** Admins configure per-company visual identity. Employees choose their own light/dark preference. All settings persist and apply immediately on next page load.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 8.1 | As a **SYSTEM_ADMIN**, I want to upload a company logo so it appears in the sidebar for all employees of that company. | Logo upload panel in company edit form (file upload + drag-and-drop); file saved to `static/uploads/logos/`; served at `/static/uploads/logos/<uuid>.<ext>`; old file deleted on replacement. | Must Have |
| 8.2 | As a **SYSTEM_ADMIN**, I want to optionally provide an external logo URL instead of uploading a file. | Tab switcher between "Upload File" and "External URL"; URL tab accepts any image URL; live preview shown. | Should Have |
| 8.3 | As a **SYSTEM_ADMIN**, I want to set a primary theme colour for my company so the portal reflects our brand identity. | Colour picker + hex input + 8 quick presets; saved as `theme_color` on company record; injected as `--primary` CSS variable for all company employees. | Must Have |
| 8.4 | As a **SYSTEM_ADMIN**, I want to add a company-wide header banner (HTML) above all portal pages for announcements. | `header_html` field (textarea); stored on company; rendered via `{{ branding.header_html \| safe }}` in base template; preview button shows rendered result inline. | Should Have |
| 8.5 | As a **SYSTEM_ADMIN**, I want to add a company-wide footer (HTML) below all pages for legal links and support contacts. | `footer_html` field; same rendering as header; clear button available. | Should Have |
| 8.6 | As any **employee**, I want to switch between light and dark mode so I can work comfortably in different environments. | Theme toggle button in topbar; instant CSS variable swap via `[data-theme="dark"]`; POST `/api/user/theme` persists to DB; restored from DB on next login. | Must Have |
| 8.7 | As an **employee**, my branding (logo, colour, header, footer) is refreshed in my session after the admin updates the company record. | `admin_company_edit` POST re-fetches branding and updates `session['branding']` immediately. | Should Have |

---

## EPIC 9 — Dashboard & Real-Time Metrics
**Label:** `dashboard` `analytics`
**Description:** Role-aware dashboard with live stat cards, drill-down filtering, and configurable auto-refresh intervals per role.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 9.1 | As any **logged-in user**, I want to see a dashboard with the key stats relevant to my role so I get an immediate status overview. | Stats differ by role: SYSTEM_ADMIN sees all-company counts; managers see team counts; employees see personal stats. | Must Have |
| 9.2 | As a **dashboard user**, I want stat cards to auto-refresh periodically so I see live data without reloading. | Refresh interval configurable per role via `/api/admin/refresh-settings`; JS polls `/api/dashboard/stats`; changed values animate (flash green). | Should Have |
| 9.3 | As a **dashboard user**, I want clickable stat cards that filter the employee directory to the relevant subset. | Clicking a stat card navigates to `/directory?filter=<value>`; directory pre-applies the filter. | Should Have |
| 9.4 | As a **SYSTEM_ADMIN**, I want to configure per-role refresh intervals so I can balance data freshness against server load. | POST `/api/admin/refresh-settings`; persisted to `widget_refresh_settings`; applied on next page load. | Nice to Have |

---

## EPIC 10 — Work Anniversary Recognition
**Label:** `engagement` `hr`
**Description:** Automatic work anniversary detection with animated visual indicator on employee names throughout the portal.

| # | User Story | Acceptance Criteria | Priority |
|---|-----------|---------------------|----------|
| 10.1 | As a **manager or admin**, I want to see a visual indicator next to employees whose work anniversaries are upcoming so I can acknowledge them. | 🎂 badge computed from `join_date`; shown on name cells in directory and team cards; urgency levels: normal (>7 days), soon (≤7 days), urgent (today/tomorrow); animated differently per urgency. | Should Have |
| 10.2 | As a **manager**, I want to hover over the badge to see the exact anniversary date and tenure. | Tooltip shows "N-year anniversary on DD MMM YYYY" on hover. | Should Have |

